import logging
import json
from datetime import datetime

logger = logging.getLogger("execution-service.ledger-adapter")

class LedgerAwareAdapter:
    """
    Wraps the ExchangeAdapterClient to automatically handle Ledger (BotService) transactions.
    Strategies should use this adapter instead of the raw client.
    """
    def __init__(self, raw_adapter, bot_client, bot_id):
        self.adapter = raw_adapter
        self.bot_client = bot_client
        self.bot_id = bot_id

    # Passthrough methods for read-only operations
    async def get_balance(self, key_id):
        return await self.adapter.get_balance(key_id)

    async def get_ticker(self, key_id, symbol):
        return await self.adapter.get_ticker(key_id, symbol)

    # Transactional methods
    async def place_order(self, key_id, symbol, side, amount, order_type='market', price=None, reason="Strategy Signal"):
        """
        Executes a trade with full Double-Entry Ledger recording.
        """
        logger.info(f"Preparing Ledger Transaction: {side} {amount} {symbol} ({reason})")

        # 1. PREPARE: Record Local Order (Intent)
        try:
            local_order = await self.bot_client.create_local_order(
                bot_id=self.bot_id,
                symbol=symbol,
                side=side.upper(),
                quantity=amount,
                reason=reason,
                timestamp=datetime.utcnow()
            )
            
            if not local_order:
                raise Exception("Failed to create LocalOrder record.")
            
            logger.info(f"✅ [1/3] LEDGER PREPARE: Local Order Created (ID: {local_order['id']}, Status: {local_order['status']})")
            
        except Exception as e:
            logger.error(f"❌ Ledger Prepare Failed: {e}")
            return {"status": "failed", "reason": "Ledger Prepare Failed"}

        # 2. EXECUTE: Call Exchange Adapter
        try:
            exchange_order = await self.adapter.place_order(
                key_id=key_id,
                symbol=symbol,
                side=side,
                amount=amount,
                order_type=order_type,
                price=price
            )
            logger.info(f"✅ [2/3] EXCHANGE EXECUTE: Order Sent (ID: {exchange_order.get('id')}, Status: {exchange_order.get('status')})")
            
        except Exception as e:
            logger.error(f"❌ Exchange Execution Failed: {e}")
            await self.bot_client.update_order_status(local_order["id"], "FAILED")
            return {"status": "failed", "reason": str(e)}

        # 3. COMMIT: Record Global Execution
        if exchange_order.get("status") == "filled":
            try:
                # Parse CCXT Unified fields
                exchange_trade_id = str(exchange_order.get("id"))
                
                # Get 'info' (raw exchange response) for additional fields
                info = exchange_order.get("info", {})
                
                # Position ID (Futures)
                position_id = info.get("positionId") if isinstance(info, dict) else None
                
                # Fee details from CCXT unified structure
                fee_obj = exchange_order.get("fee", {})
                fee_cost = fee_obj.get("cost", 0.0) if fee_obj else 0.0
                fee_currency = fee_obj.get("currency") if fee_obj else None
                
                # Realized PnL (Futures only - from raw info)
                realized_pnl = None
                if isinstance(info, dict):
                    pnl_val = info.get("realizedPnl") or info.get("realizedProfit")
                    if pnl_val is not None:
                        try:
                            realized_pnl = float(pnl_val)
                        except (ValueError, TypeError):
                            pass
                
                # Position Side (Futures Hedge Mode)
                position_side = info.get("positionSide") if isinstance(info, dict) else None
                
                # Raw response for audit (serialize info dict)
                raw_response = None
                try:
                    raw_response = json.dumps(info) if info else None
                except (TypeError, ValueError):
                    pass

                await self.bot_client.record_execution({
                    "local_order_id": local_order["id"],
                    "exchange_trade_id": exchange_trade_id,
                    "exchange_order_id": str(exchange_order.get("id")),
                    "position_id": position_id,
                    "symbol": symbol,
                    "side": side.upper(),
                    "price": exchange_order.get("average") or exchange_order.get("price", 0.0),
                    "quantity": exchange_order.get("filled", amount),
                    "fee": fee_cost,
                    "fee_currency": fee_currency,
                    "realized_pnl": realized_pnl,
                    "position_side": position_side,
                    "raw_response": raw_response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                await self.bot_client.update_order_status(local_order["id"], "FILLED")
                logger.info(f"✅ [3/3] LEDGER COMMIT: Global Execution Recorded (Trade: {exchange_trade_id}, PnL: {realized_pnl})")
            
            except Exception as e:
                logger.error(f"❌ Ledger Commit Failed (Critical): {e}")
        elif exchange_order.get("status") in ["error", "failed"]:
             await self.bot_client.update_order_status(local_order["id"], "FAILED")
             logger.error(f"❌ [3/3] LEDGER UPDATE: Order Execution Failed (Status: {exchange_order.get('status')})")
        else:
             await self.bot_client.update_order_status(local_order["id"], "SENT")
             logger.warning(f"⚠️ [3/3] LEDGER UPDATE: Order not filled immediately (Status: SENT)")
        
        return exchange_order
