# strategies/test_trading.py
import logging
import asyncio
import time
from datetime import datetime

logger = logging.getLogger("execution-service.strategies.test_trading")

class TestTradingStrategy:
    """
    Test Trading Strategy:
    - Buys allocation_ratio amount
    - Holds for hold_duration
    - Sells all
    - Repeats loop_count times
    """
    def __init__(self, config):
        self.config = config
        self.state = "INIT" # INIT, HOLDING, SOLD, FINISHED
        self.loop_index = 0
        self.hold_start_time = 0
        self.bought_amount = 0.0
        
        # Parse Strategy Config
        # The frontend saves strategy params in 'config.pipeline[0]' or similar.
        # For this PoC, we assume config is flattened or we find the strategy node.
        # But 'config' passed here is likely the entire Bot object.
        # Let's extract the strategy params.
        self.params = {}
        # FIX: Access pipeline directly. Log shows it is a DICT, not a list.
        # "pipeline": {"strategy": {"id": "test_trading_v1", "params": {...}}}
        pipeline = config.get("pipeline", {})
        
        # New Schema Logic:
        strategy_node = pipeline.get("strategy", {})
        if strategy_node.get("id") == "test_trading_v1":
             self.params = strategy_node.get("params", {})
        
        # Fallback for older list-based structure if needed (Optional)
        if not self.params and isinstance(pipeline, list):
            for node in pipeline:
                if node.get("id") == "test_trading_v1":
                    self.params = node.get("params", {})
                    break
        
        # Defaults
        self.allocation = float(self.params.get("allocation_ratio", 0.1))
        self.hold_duration = int(self.params.get("hold_duration", 60))
        self.loop_count = int(self.params.get("loop_count", 5))
        self.symbol = config.get("global_settings", {}).get("symbol", "BTC/USDT")
        
        # We need the key_id to trade.
        # Frontend saves it in 'exchange' field (global_settings.exchange)
        # Some older strategy specs might assume 'account_id'
        # DEBUG: Print EVERYTHING
        print(f"DEBUG: Full Config received: {config}", flush=True)
        
        # FIX: The config object IS the bot dict, not nested under "config"
        gs = config.get("global_settings", {})
        print(f"DEBUG: Extracted global_settings: {gs}", flush=True)
        
        self.key_id = gs.get("exchange") or gs.get("account_id")
        print(f"DEBUG: Resolved key_id: {self.key_id}", flush=True)


    async def execute(self, context):
        """
        Main execution tick.
        context: Contains adapter_client, bot_config, etc.
        """
        adapter = context["adapter"]
        
        if not self.key_id:
            logger.error("Missing key_id (account_id) in bot config. Cannot trade.")
            return

        logger.info(f"[{self.config['name']}] State: {self.state} | Loop: {self.loop_index}/{self.loop_count}")

        if self.state == "FINISHED":
            return

        # 1. INIT -> BUY
        if self.state == "INIT":
            if self.loop_count > 0 and self.loop_index >= self.loop_count:
                logger.info("Loop count reached. Finishing.")
                self.state = "FINISHED"
                return

            # Get Balance (USDT)
            balance = await adapter.get_balance(self.key_id)
            usdt_balance = 0.0
            for asset in balance.get("assets", []):
                if asset["asset"] == "USDT":
                    usdt_balance = asset["free"]
                    break
            
            buy_amount_usdt = usdt_balance * self.allocation
            logger.info(f"Buying {self.symbol} with {buy_amount_usdt:.2f} USDT (Alloc: {self.allocation})")
            
            if buy_amount_usdt <= 0:
                logger.warning("Insufficient USDT balance. Waiting for funds...")
                raise ValueError("잔고 부족: USDT 잔고가 0이거나 할당량을 충족할 수 없습니다.")

            # Place Order
            ticker_data = await adapter.get_ticker(self.key_id, self.symbol)
            if not ticker_data or 'price' not in ticker_data:
                logger.error("Failed to get price. Skipping tick.")
                raise RuntimeError("가격 조회 실패: 티커 데이터를 가져올 수 없습니다.")
            
            price_val = ticker_data['price']
            limits = ticker_data.get('limits', {})
            min_notional = limits.get('min_notional')
            
            quantity = buy_amount_usdt / price_val
            # Truncate precision roughly
            quantity = float(f"{quantity:.5f}")
            
            calculated_notional = quantity * price_val
            logger.info(f"[Check] Quantity: {quantity} | Price: {price_val} | Notional: {calculated_notional} (Min: {min_notional})")
            
            if min_notional and calculated_notional < min_notional:
                logger.warning(f"⚠️ Order amount too small! {calculated_notional:.4f} < {min_notional}")
                raise ValueError(f"주문 금액 미달: 계산된 주문 금액 {calculated_notional:.4f}가 최소 주문 금액 {min_notional}보다 작습니다.")

            if quantity <= 0:
                logger.warning("Quantity too small.")
                raise ValueError("수량 부족: 계산된 주문 수량이 0 이하입니다.")

            # --- Place Order via LedgerAwareAdapter ---
            # The adapter is already wrapped, so we just pass the reason.
            order = await adapter.place_order(
                key_id=self.key_id, 
                symbol=self.symbol, 
                side="buy", 
                amount=quantity,
                reason=f"Loop {self.loop_index} Start"
            )
            
            if order.get("status") == "filled":
                 self.bought_amount = quantity
                 self.hold_start_time = time.time()
                 self.state = "HOLDING"
                 logger.info(f"Buy Filled! Holding for {self.hold_duration}s...")
            else:
                 msg = f"Buy failed: {order}"
                 logger.error(msg)
                 raise RuntimeError(f"주문 실패: {msg}")

        # 2. HOLDING -> SELL
        elif self.state == "HOLDING":
            elapsed = time.time() - self.hold_start_time
            if elapsed >= self.hold_duration:
                logger.info(f"Hold time ({elapsed:.1f}s) elapsed. Selling...")
                
                order = await adapter.place_order(
                    key_id=self.key_id,
                    symbol=self.symbol,
                    side="sell",
                    amount=self.bought_amount,
                    reason="Hold Duration Elapsed"
                )
                
                if order.get("status") == "filled":
                    logger.info("Sell Filled! Loop complete.")
                    self.state = "INIT"
                    self.loop_index += 1
                else:
                    logger.error(f"Sell failed: {order}")

            else:
                 logger.info(f"Holding... ({elapsed:.0f}/{self.hold_duration}s)")

    async def on_stop(self, context):
        """
        Called when the bot is requested to stop.
        Clean up resources or close positions.
        """
        logger.info(f"[{self.config['name']}] Stopping... Checking for open positions.")
        
        adapter = context["adapter"]
        
        # If holding a position, liquidate it
        if self.state == "HOLDING" and self.bought_amount > 0:
            logger.warning(f"[{self.config['name']}] Forced Liquidation: Selling {self.bought_amount} {self.symbol}...")
            
            try:
                order = await adapter.place_order(
                    key_id=self.key_id,
                    symbol=self.symbol,
                    side="sell",
                    amount=self.bought_amount,
                    reason="Forced Stop Liquidation"
                )
                
                if order.get("status") == "filled":
                    logger.info("Liquidation Filled! Cleanup complete.")
                    self.state = "FINISHED" # Or STOPPED
                else:
                    logger.error(f"Liquidation failed: {order}")
                    
            except Exception as e:
                logger.error(f"Error during liquidation: {e}")
        else:
            logger.info("No open positions to close.")

