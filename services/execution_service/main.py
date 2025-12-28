from fastapi import FastAPI
import logging
from contextlib import asynccontextmanager
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot_client import BotClient
from adapter_client import AdapterClient
from engine import BotRunner

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("execution-service")

# Global Scheduler
scheduler = AsyncIOScheduler()
bot_client = BotClient()
adapter_client = AdapterClient()
active_runners = {} # bot_id -> BotRunner instance

async def poll_running_bots():
    """
    Periodic task to sync running bots.
    """
    try:
        runners_list = await bot_client.get_running_bots()
        active_ids = {bot['id'] for bot in runners_list}
        
        # 1. Start new bots
        for bot in runners_list:
            bid = bot['id']
            if bid not in active_runners:
                logger.info(f"Starting new bot runner: {bot['name']} ({bid})")
                runner = BotRunner(bot, adapter_client, bot_client)
                await runner.start()
                active_runners[bid] = runner

        # 2. Stop removed/stopped bots
        current_ids = list(active_runners.keys())
        for bid in current_ids:
            if bid not in active_ids:
                 logger.info(f"Stopping bot (not in running list): {bid}")
                 runner = active_runners[bid]
                 await runner.stop()
                 del active_runners[bid]

                 
    except Exception as e:
        logger.error(f"Error in poll loop: {e}")

# --- Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Starting Execution Service...")
    
    # Start Scheduler
    scheduler.add_job(poll_running_bots, 'interval', seconds=5)
    scheduler.start()
    
    yield
    
    # Shutdown logic
    logger.info("Shutting down Execution Service...")
    scheduler.shutdown()

app = FastAPI(title="Execution Service", version="1.0.0", lifespan=lifespan)

# --- Routes ---
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "execution-service"}

@app.get("/status")
def get_status():
    # Placeholder for bot runner status
    return {"running_bots": 0, "active_runners": []}
