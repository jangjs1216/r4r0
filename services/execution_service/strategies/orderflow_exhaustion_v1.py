import logging
import time
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("execution-service.strategies.orderflow_exhaustion_v1")


@dataclass
class _Params:
    depth_limit: int = 50
    trades_limit: int = 200
    trades_lookback_sec: int = 10

    delta_ratio_threshold: float = 2.5
    min_total_quote_volume: float = 50.0

    spread_expand_ratio_threshold: float = 1.5
    sweep_move_pct_threshold: float = 0.001
    confirm_absorption_ticks: int = 2

    buy_allocation_ratio: float = 0.10
    sell_allocation_ratio: float = 0.10
    quantity_precision: int = 5

    take_profit_pct: float = 0.003
    stop_loss_pct: float = 0.004
    stop_buffer_pct: float = 0.001
    time_stop_sec: int = 180
    cooldown_sec: int = 120

    spread_ema_alpha: float = 0.2
    spread_normalized_max_ratio: float = 1.2


class OrderflowExhaustionV1Strategy:
    """
    Orderflow Exhaustion (Contrarian Fade) - v1

    - 탐욕(매수 폭탄) / 공포(매도 폭탄)를 최근 체결(trades)과 스프레드/미드 변화로 근사한다.
    - 스윕 이후 더 못 가는 "흡수/고갈"이 확인되면 반대 방향으로 진입한다.
    - 현물(spot) 기반이므로, SELL 진입은 '보유한 base 자산을 일부 매도'하는 inventory-based 페이드로 동작한다.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        pipeline = config.get("pipeline", {})
        strategy_node = pipeline.get("strategy", {}) if isinstance(pipeline, dict) else {}
        params = strategy_node.get("params", {}) if strategy_node.get("id") == "orderflow_exhaustion_v1" else {}

        self.params = _Params(
            depth_limit=int(params.get("depth_limit", _Params.depth_limit)),
            trades_limit=int(params.get("trades_limit", _Params.trades_limit)),
            trades_lookback_sec=int(params.get("trades_lookback_sec", _Params.trades_lookback_sec)),
            delta_ratio_threshold=float(params.get("delta_ratio_threshold", _Params.delta_ratio_threshold)),
            min_total_quote_volume=float(params.get("min_total_quote_volume", _Params.min_total_quote_volume)),
            spread_expand_ratio_threshold=float(
                params.get("spread_expand_ratio_threshold", _Params.spread_expand_ratio_threshold)
            ),
            sweep_move_pct_threshold=float(params.get("sweep_move_pct_threshold", _Params.sweep_move_pct_threshold)),
            confirm_absorption_ticks=int(params.get("confirm_absorption_ticks", _Params.confirm_absorption_ticks)),
            buy_allocation_ratio=float(params.get("buy_allocation_ratio", _Params.buy_allocation_ratio)),
            sell_allocation_ratio=float(params.get("sell_allocation_ratio", _Params.sell_allocation_ratio)),
            quantity_precision=int(params.get("quantity_precision", _Params.quantity_precision)),
            take_profit_pct=float(params.get("take_profit_pct", _Params.take_profit_pct)),
            stop_loss_pct=float(params.get("stop_loss_pct", _Params.stop_loss_pct)),
            stop_buffer_pct=float(params.get("stop_buffer_pct", _Params.stop_buffer_pct)),
            time_stop_sec=int(params.get("time_stop_sec", _Params.time_stop_sec)),
            cooldown_sec=int(params.get("cooldown_sec", _Params.cooldown_sec)),
            spread_ema_alpha=float(params.get("spread_ema_alpha", _Params.spread_ema_alpha)),
            spread_normalized_max_ratio=float(params.get("spread_normalized_max_ratio", _Params.spread_normalized_max_ratio)),
        )

        gs = config.get("global_settings", {})
        self.symbol = gs.get("symbol", "BTC/USDT")
        self.key_id = gs.get("exchange") or gs.get("account_id")

        self.state = "FLAT"  # FLAT | WAIT_CONFIRM | IN_POSITION | COOLDOWN
        self.cooldown_until = 0.0

        self.last_mid: Optional[float] = None
        self.spread_ema: Optional[float] = None

        self.last_signal_side: Optional[str] = None  # BUY_PRESSURE | SELL_PRESSURE
        self.absorption_count = 0
        self.sweep_high: Optional[float] = None
        self.sweep_low: Optional[float] = None

        self.position_side: Optional[str] = None  # BUY or SELL (spot inventory sell)
        self.position_qty: float = 0.0
        self.entry_price: Optional[float] = None
        self.entry_time: float = 0.0
        self.stop_price: Optional[float] = None

    async def execute(self, context: Dict[str, Any]):
        adapter = context["adapter"]

        if not self.key_id:
            logger.error("Missing key_id (global_settings.exchange/account_id). Cannot trade.")
            return

        now = time.time()

        if self.state == "COOLDOWN":
            if now < self.cooldown_until:
                return
            self.state = "FLAT"

        ticker = await adapter.get_ticker(self.key_id, self.symbol)
        if not ticker or "price" not in ticker:
            logger.warning("Ticker unavailable; skipping tick.")
            return

        price = float(ticker["price"])
        limits = ticker.get("limits") or {}

        if self.state == "IN_POSITION":
            await self._manage_position(adapter, price, now)
            return

        depth = await adapter.get_depth(self.key_id, self.symbol, self.params.depth_limit)
        trades_resp = await adapter.get_trades(self.key_id, self.symbol, self.params.trades_limit)
        if not depth or not trades_resp:
            logger.warning("Depth/Trades unavailable; skipping tick.")
            return

        best_bid, best_ask = depth.get("best_bid"), depth.get("best_ask")
        if best_bid is None or best_ask is None:
            logger.warning("Depth missing best_bid/best_ask; skipping tick.")
            return

        best_bid = float(best_bid)
        best_ask = float(best_ask)
        mid = (best_bid + best_ask) / 2.0
        spread = best_ask - best_bid

        if self.spread_ema is None:
            self.spread_ema = spread
        else:
            a = self.params.spread_ema_alpha
            self.spread_ema = (a * spread) + ((1 - a) * self.spread_ema)

        spread_expand_ratio = spread / self.spread_ema if self.spread_ema and self.spread_ema > 0 else 1.0

        sweep_move_pct = 0.0
        if self.last_mid is not None and self.last_mid > 0:
            sweep_move_pct = abs(mid / self.last_mid - 1.0)

        buy_q, sell_q = self._calc_trade_pressure(trades_resp, now)
        total_q = buy_q + sell_q
        if total_q < self.params.min_total_quote_volume:
            self.last_mid = mid
            return

        buy_sell_ratio = (buy_q + 1e-9) / (sell_q + 1e-9)
        sell_buy_ratio = (sell_q + 1e-9) / (buy_q + 1e-9)

        is_spread_extreme = spread_expand_ratio >= self.params.spread_expand_ratio_threshold
        is_sweep_move = sweep_move_pct >= self.params.sweep_move_pct_threshold

        if self.state == "FLAT":
            if buy_sell_ratio >= self.params.delta_ratio_threshold and is_spread_extreme and is_sweep_move:
                self.last_signal_side = "BUY_PRESSURE"
                self.state = "WAIT_CONFIRM"
                self.absorption_count = 0
                self.sweep_high = max(self.sweep_high or 0.0, best_ask, mid, price)
                logger.info(
                    f"[{self.config.get('name')}] BUY_PRESSURE detected (ratio={buy_sell_ratio:.2f}, spreadX={spread_expand_ratio:.2f}, move={sweep_move_pct:.4f})"
                )
            elif sell_buy_ratio >= self.params.delta_ratio_threshold and is_spread_extreme and is_sweep_move:
                self.last_signal_side = "SELL_PRESSURE"
                self.state = "WAIT_CONFIRM"
                self.absorption_count = 0
                self.sweep_low = min(self.sweep_low or mid, best_bid, mid, price)
                logger.info(
                    f"[{self.config.get('name')}] SELL_PRESSURE detected (ratio={sell_buy_ratio:.2f}, spreadX={spread_expand_ratio:.2f}, move={sweep_move_pct:.4f})"
                )
            self.last_mid = mid
            return

        if self.state == "WAIT_CONFIRM":
            normalized = spread <= (self.spread_ema * self.params.spread_normalized_max_ratio)

            if self.last_signal_side == "BUY_PRESSURE":
                self.sweep_high = max(self.sweep_high or 0.0, best_ask, mid, price)
                if normalized and self.last_mid is not None and mid <= self.last_mid and buy_sell_ratio >= 1.0:
                    self.absorption_count += 1
                else:
                    self.absorption_count = max(self.absorption_count - 1, 0)

                if self.absorption_count >= self.params.confirm_absorption_ticks:
                    await self._enter_contrarian(
                        adapter=adapter,
                        entry_side="SELL",
                        price=price,
                        now=now,
                        limits=limits,
                        reason="Greed: orderflow exhaustion (buy pressure absorbed)",
                    )

            elif self.last_signal_side == "SELL_PRESSURE":
                self.sweep_low = min(self.sweep_low or mid, best_bid, mid, price)
                if normalized and self.last_mid is not None and mid >= self.last_mid and sell_buy_ratio >= 1.0:
                    self.absorption_count += 1
                else:
                    self.absorption_count = max(self.absorption_count - 1, 0)

                if self.absorption_count >= self.params.confirm_absorption_ticks:
                    await self._enter_contrarian(
                        adapter=adapter,
                        entry_side="BUY",
                        price=price,
                        now=now,
                        limits=limits,
                        reason="Fear: orderflow exhaustion (sell pressure absorbed)",
                    )

        self.last_mid = mid

    def _calc_trade_pressure(self, trades_resp: Dict[str, Any], now_sec: float) -> Tuple[float, float]:
        trades = trades_resp.get("trades") or []
        cutoff_ms = int((now_sec - self.params.trades_lookback_sec) * 1000)

        buy_quote = 0.0
        sell_quote = 0.0

        for t in trades:
            ts = t.get("timestamp")
            if ts is None or ts < cutoff_ms:
                continue
            side = (t.get("side") or "").lower()
            price = t.get("price")
            amount = t.get("amount")
            if price is None or amount is None:
                continue
            q = float(price) * float(amount)
            if side == "buy":
                buy_quote += q
            elif side == "sell":
                sell_quote += q

        return buy_quote, sell_quote

    async def _enter_contrarian(
        self,
        adapter,
        entry_side: str,
        price: float,
        now: float,
        limits: Dict[str, Any],
        reason: str,
    ):
        qty = await self._calc_order_qty(adapter, entry_side, price, limits)
        if qty <= 0:
            logger.warning(f"Entry blocked: qty=0 ({entry_side}). Going cooldown to avoid spam.")
            self.state = "COOLDOWN"
            self.cooldown_until = now + self.params.cooldown_sec
            return

        order = await adapter.place_order(
            key_id=self.key_id,
            symbol=self.symbol,
            side=entry_side.lower(),
            amount=qty,
            reason=reason,
        )

        if order.get("status") != "filled":
            logger.error(f"Entry order not filled: {order}")
            self.state = "COOLDOWN"
            self.cooldown_until = now + self.params.cooldown_sec
            return

        self.position_side = entry_side
        self.position_qty = qty
        self.entry_price = price
        self.entry_time = now

        if entry_side == "BUY":
            hard_stop = price * (1 - self.params.stop_loss_pct)
            if self.sweep_low is not None:
                hard_stop = min(hard_stop, self.sweep_low * (1 - self.params.stop_buffer_pct))
            self.stop_price = hard_stop
        else:  # SELL
            hard_stop = price * (1 + self.params.stop_loss_pct)
            if self.sweep_high is not None:
                hard_stop = max(hard_stop, self.sweep_high * (1 + self.params.stop_buffer_pct))
            self.stop_price = hard_stop

        self.state = "IN_POSITION"
        logger.info(
            f"[{self.config.get('name')}] Entered {entry_side} qty={qty} entry={price} stop={self.stop_price}"
        )

    async def _calc_order_qty(self, adapter, side: str, price: float, limits: Dict[str, Any]) -> float:
        balance = await adapter.get_balance(self.key_id)
        assets = balance.get("assets") or []
        base, quote = self._parse_symbol(self.symbol)

        min_notional = limits.get("min_notional")
        min_amount = limits.get("min_amount")

        if side == "BUY":
            quote_free = 0.0
            for a in assets:
                if a.get("asset") == quote:
                    quote_free = float(a.get("free") or 0.0)
                    break

            spend_quote = quote_free * self.params.buy_allocation_ratio
            if spend_quote <= 0:
                return 0.0

            qty = spend_quote / price
        else:  # SELL
            base_free = 0.0
            for a in assets:
                if a.get("asset") == base:
                    base_free = float(a.get("free") or 0.0)
                    break
            qty = base_free * self.params.sell_allocation_ratio

        qty = float(f"{qty:.{self.params.quantity_precision}f}")
        if qty <= 0:
            return 0.0

        if min_amount and qty < float(min_amount):
            return 0.0

        if min_notional and (qty * price) < float(min_notional):
            return 0.0

        return qty

    async def _manage_position(self, adapter, price: float, now: float):
        if self.entry_price is None or self.position_side is None:
            self._reset_to_flat(now)
            return

        if self.stop_price is not None:
            if self.position_side == "BUY" and price <= self.stop_price:
                await self._exit(adapter, "Stop Loss (hard)")
                return
            if self.position_side == "SELL" and price >= self.stop_price:
                await self._exit(adapter, "Stop Loss (hard)")
                return

        if self.position_side == "BUY":
            if price >= self.entry_price * (1 + self.params.take_profit_pct):
                await self._exit(adapter, "Take Profit")
                return
        else:  # SELL
            if price <= self.entry_price * (1 - self.params.take_profit_pct):
                await self._exit(adapter, "Take Profit")
                return

        if now - self.entry_time >= self.params.time_stop_sec:
            await self._exit(adapter, "Time Stop")
            return

    async def _exit(self, adapter, reason: str):
        exit_side = "SELL" if self.position_side == "BUY" else "BUY"
        qty = self.position_qty

        order = await adapter.place_order(
            key_id=self.key_id,
            symbol=self.symbol,
            side=exit_side.lower(),
            amount=qty,
            reason=f"{reason} (exit {exit_side})",
        )

        if order.get("status") != "filled":
            logger.error(f"Exit order not filled: {order}")
            return

        self._reset_to_flat(time.time())

    async def on_stop(self, context: Dict[str, Any]):
        """
        Called when the bot is requested to stop.
        Clean up resources or close positions.
        Ensures NO risk asset position is left behind (Zero Position Policy).
        """
        logger.info(f"[{self.config.get('name')}] Stopping... Checking for open positions.")
        adapter = context["adapter"]

        # If we are not in a position (FLAT or COOLDOWN), we are good.
        # But we double-check the 'position_side' just in case.
        if self.position_side is None or self.state not in ["IN_POSITION"]:
            logger.info("State is not IN_POSITION. No active trade to close.")
            self._reset_to_flat(time.time())
            return

        # Case 1: We are LONG (Bought Base, waiting to Sell)
        # We must SELL to liquidate to USDT (Safe Asset).
        if self.position_side == "BUY":
            logger.warning(f"[{self.config.get('name')}] Closing LONG position (Liquidating to USDT)...")
            
            # Check actual balance to be safe
            try:
                base, quote = self._parse_symbol(self.symbol)
                balance_data = await adapter.get_balance(self.key_id)
                actual_qty = 0.0
                for asset in balance_data.get("assets", []):
                    if asset["asset"] == base:
                        actual_qty = float(asset["free"])
                        break
                
                # Determine sell qty: min(actual, tracked)
                if actual_qty <= 0.00001:
                    logger.info("Actual balance is near zero. Nothing to sell.")
                    return

                sell_qty = min(actual_qty, self.position_qty) if self.position_qty > 0 else actual_qty
                
                # Retry loop for liquidation
                max_retries = 5
                for i in range(max_retries):
                    logger.info(f"Liquidation Attempt {i+1}/{max_retries}: Selling {sell_qty} {base}...")
                    order = await adapter.place_order(
                        key_id=self.key_id,
                        symbol=self.symbol,
                        side="sell",
                        amount=sell_qty,
                        reason="Forced Stop Liquidation (Long Exit)",
                    )
                    
                    if order.get("status") == "filled":
                        logger.info("Liquidation Filled! Cleanup complete.")
                        break
                    else:
                        logger.error(f"Liquidation failed: {order}. Retrying...")
                        await asyncio.sleep(1)
                else:
                    logger.error("CRITICAL: Failed to liquidate LONG position after retries.")

            except Exception as e:
                logger.error(f"Error during LONG liquidation: {e}")

        # Case 2: We are SHORT (Sold Base, waiting to Buy back)
        # In Spot context, this means we hold USDT.
        # Stopping here is 'Safe' as we are in stablecoin.
        # We generally do NOT force buy-back because that would expose us to volatility again.
        elif self.position_side == "SELL":
            logger.info(
                f"[{self.config.get('name')}] Current position is SHORT (Spot Sell). "
                "We hold USDT, which is safe. Skipping forced buy-back."
            )

        self._reset_to_flat(time.time())

    def _reset_to_flat(self, now: float):
        self.state = "COOLDOWN"
        self.cooldown_until = now + self.params.cooldown_sec

        self.last_signal_side = None
        self.absorption_count = 0
        self.sweep_high = None
        self.sweep_low = None

        self.position_side = None
        self.position_qty = 0.0
        self.entry_price = None
        self.entry_time = 0.0
        self.stop_price = None

    @staticmethod
    def _parse_symbol(symbol: str) -> Tuple[str, str]:
        if "/" in symbol:
            base, quote = symbol.split("/", 1)
            return base, quote
        return symbol, "USDT"

