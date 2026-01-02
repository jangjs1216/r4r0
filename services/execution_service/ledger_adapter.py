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
            
            # [DEBUG] Log full raw response to identify JSON structure
            import json
            try:
                # Use default=str to handle datetime objects if any
                raw_log = json.dumps(exchange_order, default=str, indent=2)
                logger.info(f"🔍 [RAW EXCHANGE RESPONSE]:\n{raw_log}")
            except Exception as log_err:
                logger.error(f"Failed to log raw response: {log_err}")

            logger.info(f"✅ [2/3] EXCHANGE EXECUTE: Order Sent (ID: {exchange_order.get('id')}, Status: {exchange_order.get('status')})")
            
        except Exception as e:
            logger.error(f"❌ Exchange Execution Failed: {e}")
            await self.bot_client.update_order_status(local_order["id"], "FAILED")
            return {"status": "failed", "reason": str(e)}

        # 3. COMMIT: Record Global Execution (Multi-Fill Support)
        if exchange_order.get("status") == "filled":
            try:
                details = exchange_order.get("details", {})
                info = details.get("info", {})
                fills = info.get("fills", [])
                
                # Standard Binance Response with Fills
                if fills:
                    for fill in fills:
                        price = float(fill.get("price", 0.0))
                        qty = float(fill.get("qty", 0.0))
                        quote_qty = price * qty
                        
                        # Use provided transactTime if available, else current UTC
                        ts_val = info.get("transactTime")
                        if ts_val:
                            # Helper to convert ms timestamp to ISO
                            ts_iso = datetime.utcfromtimestamp(int(ts_val)/1000).isoformat()
                        else:
                            ts_iso = datetime.utcnow().isoformat()

                        payload = {
                            "local_order_id": local_order["id"],
                            "exchange_trade_id": str(fill.get("tradeId")),
                            "exchange_order_id": str(exchange_order.get("id")),
                            "order_list_id": str(info.get("orderListId")),
                            "symbol": symbol,
                            "side": info.get("side", side).upper(),
                            "price": price,
                            "quantity": qty,
                            "quote_qty": quote_qty,
                            "fee": float(fill.get("commission", 0.0)),
                            "fee_asset": fill.get("commissionAsset"),
                            "timestamp": ts_iso
                        }
                        
                        await self.bot_client.record_execution(payload)
                        logger.info(f"✅ [3/3] LEDGER COMMIT: Recorded Fill {payload['exchange_trade_id']}")

                # Fallback: No Fills (e.g. Simulation or other exchange)
                else:
                    logger.warning("⚠️ No 'fills' found in response. Using aggregate execution data.")
                    payload = {
                        "local_order_id": local_order["id"],
                        "exchange_trade_id": str(exchange_order.get("id")), # Fallback ID
                        "exchange_order_id": str(exchange_order.get("id")),
                        "order_list_id": None,
                        "symbol": symbol,
                        "side": side.upper(),
                        "price": exchange_order.get("average") or exchange_order.get("price", 0.0),
                        "quantity": exchange_order.get("filled", amount),
                        "quote_qty": (exchange_order.get("cost") or 0.0),
                        "fee": exchange_order.get("fee", {}).get("cost", 0.0),
                        "fee_asset": exchange_order.get("fee", {}).get("currency"),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.bot_client.record_execution(payload)
                    logger.info(f"✅ [3/3] LEDGER COMMIT: Recorded Aggregate Execution")
                
                await self.bot_client.update_order_status(local_order["id"], "FILLED")
            
            except Exception as e:
                logger.error(f"❌ Ledger Commit Failed (Critical): {e}")
        elif exchange_order.get("status") in ["error", "failed"]:
             await self.bot_client.update_order_status(local_order["id"], "FAILED")
             logger.error(f"❌ [3/3] LEDGER UPDATE: Order Execution Failed (Status: {exchange_order.get('status')})")
        else:
             await self.bot_client.update_order_status(local_order["id"], "SENT")
             logger.warning(f"⚠️ [3/3] LEDGER UPDATE: Order not filled immediately (Status: SENT)")
        
        return exchange_order
