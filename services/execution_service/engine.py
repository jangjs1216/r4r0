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
