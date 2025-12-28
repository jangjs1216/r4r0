import logging
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
                # Parse details
                details = exchange_order.get("details", {})
                exchange_trade_id = str(exchange_order.get("id")) # Default to Order ID
                
                position_id = None
                if "info" in details and isinstance(details["info"], dict):
                    position_id = details["info"].get("positionId")

                await self.bot_client.record_execution({
                    "local_order_id": local_order["id"],
                    "exchange_trade_id": exchange_trade_id,
                    "exchange_order_id": str(exchange_order.get("id")),
                    "position_id": position_id,
                    "symbol": symbol,
                    "price": exchange_order.get("average") or exchange_order.get("price", 0.0),
                    "quantity": exchange_order.get("filled", amount),
                    "fee": exchange_order.get("fee", {}).get("cost", 0.0),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                await self.bot_client.update_order_status(local_order["id"], "FILLED")
                logger.info(f"✅ [3/3] LEDGER COMMIT: Global Execution Recorded (Trade: {exchange_trade_id}, Pos: {position_id})")
            
            except Exception as e:
                logger.error(f"❌ Ledger Commit Failed (Critical): {e}")
        elif exchange_order.get("status") in ["error", "failed"]:
             await self.bot_client.update_order_status(local_order["id"], "FAILED")
             logger.error(f"❌ [3/3] LEDGER UPDATE: Order Execution Failed (Status: {exchange_order.get('status')})")
        else:
             await self.bot_client.update_order_status(local_order["id"], "SENT")
             logger.warning(f"⚠️ [3/3] LEDGER UPDATE: Order not filled immediately (Status: SENT)")
        
        return exchange_order
