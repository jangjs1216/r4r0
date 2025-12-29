import asyncio
import logging
import traceback
from adapter_client import AdapterClient
from bot_client import BotClient
from ledger_adapter import LedgerAwareAdapter
# Import strategies dynamically or statically
from strategies.test_trading import TestTradingStrategy

logger = logging.getLogger("execution-service.engine")

class BotRunner:
    """
    Manages the execution loop of a single bot.
    """
    def __init__(self, bot_config: dict, adapter_client: AdapterClient, bot_client: BotClient):
        self.bot_config = bot_config
        self.adapter_client = adapter_client
        self.bot_client = bot_client
        self.strategy_instance = None
        self.task = None
        self.is_running = False

    async def start(self):
        """Starts the bot loop."""
        self.is_running = True
        self._initialize_strategy()
        self.task = asyncio.create_task(self._run_loop())
        logger.info(f"BotRunner started for {self.bot_config['name']}")

    async def stop(self):
        """Stops the bot loop."""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info(f"BotRunner stopped for {self.bot_config['name']}")

    async def stop_gracefully(self):
        """
        Stops the bot but first closes any open positions.
        """
        logger.info(f"Initiating Graceful Stop for {self.bot_config['name']}...")
        
        # 1. Stop the loop first so no new buys happen
        await self.stop()
        
        try:
            bot_id = self.bot_config['id']
            # 2. Check Net Position
            pos_data = await self.bot_client.get_bot_position(bot_id)
            if not pos_data:
                logger.error("Failed to fetch position data. Forcing STOPPED.")
            else:
                net_qty = pos_data.get("net_quantity", 0.0)
                symbol = pos_data.get("symbol")
                
                if symbol == "UNKNOWN":
                    # Try to get symbol from config if unknown
                    symbol = self.bot_config.get("global_settings", {}).get("symbol", "BTC/USDT")

                logger.info(f"Graceful Stop Phase: Net Quantity for {symbol} is {net_qty}")
                
                if abs(net_qty) > 0:
                    # Need to close
                    ledger_adapter = LedgerAwareAdapter(
                        raw_adapter=self.adapter_client,
                        bot_client=self.bot_client,
                        bot_id=bot_id
                    )
                    
                    # Determine Key ID (from config)
                    key_id = self.bot_config.get("global_settings", {}).get("exchange")
                    
                    side = "sell" if net_qty > 0 else "buy"
                    close_qty = abs(net_qty)
                    
                    logger.info(f"Placing Closing Order: {side.upper()} {close_qty} {symbol}")
                    
                    # Place Order
                    # Note: We use MARKET order for closing
                    order = await ledger_adapter.place_order(
                        key_id=key_id,
                        symbol=symbol,
                        side=side,
                        amount=close_qty,
                        reason="Graceful Stop (Close All)"
                    )
                    
                    if order.get("status") == "filled":
                        logger.info("✅ Closing successful.")
                    else:
                        logger.error(f"❌ Closing failed: {order}")
                else:
                    logger.info("No open positions to close.")

        except Exception as e:
            logger.error(f"Error during graceful stop: {e}")
            traceback.print_exc()
        
        # 3. Finally update status to STOPPED
        logger.info(f"Updating bot status to STOPPED.")
        await self.bot_client.update_bot_status(self.bot_config['id'], "STOPPED")

    def _initialize_strategy(self):
        """
        Factory method to load the correct strategy class based on config.
        """
        # Parse Strategy ID from Config
        # Config structure: { "pipeline": [ { "type": "strategy", "strategy_id": "test_trading_v1", ... } ] }
        # Simplified for now: Assume global_settings has strategy_id or check pipeline first node
        
        # In current BotService implementation, pipeline is a JSON list.
        # We need to find the strategy node.
        pipeline = self.bot_config.get("config", {}).get("pipeline", [])
        strategy_id = "unknown"
        
        # Fallback/Debug: Use test_trading directly if id matches
        # Real logic: Iterate pipeline, find node with type='strategy' (or just use dedicated field)
        # For this PoC, we map 'test_trading_v1' -> TestTradingStrategy
        
        # Let's assume the user selected 'test_trading_v1'
        # Ideally, better to pass this strategy_id clearly.
        
        self.strategy_instance = TestTradingStrategy(self.bot_config)

    async def _run_loop(self):
        """
        The main infinite loop.
        """
        logger.info("Entering execution loop...")
        
        # Initialize Ledger Wrapper
        # This Wrapper effectively acts as the "Transaction Manager" for this bot
        ledger_adapter = LedgerAwareAdapter(
            raw_adapter=self.adapter_client,
            bot_client=self.bot_client,
            bot_id=self.bot_config['id']
        )
        
        while self.is_running:
            try:
                # Build context
                # CRITICAL: We pass the 'ledger_adapter' as the 'adapter'
                # The strategy doesn't know the difference, but now all calls are intercepted.
                context = {
                    "adapter": ledger_adapter, 
                    "bot_id": self.bot_config['id'],
                    "config": self.bot_config
                }
                
                # Execute Strategy Tick
                if self.strategy_instance:
                    await self.strategy_instance.execute(context)
                
                # Sleep interval (Fixed 5s for PoC - updated from 10s to match request usage)
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in bot loop: {e}")
                traceback.print_exc()
                await asyncio.sleep(5) # Backoff on error
