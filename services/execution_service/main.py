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
    Handles RUNNING, STOPPING, and cleanup.
    """
    try:
        # Fetch bots (RUNNING & STOPPING)
        bots_data = await bot_client.get_running_bots()
        bots_map = {b['id']: b for b in bots_data} # ID -> Bot Data
        
        # 1. Check Existing Runners
        current_runner_ids = list(active_runners.keys())
        for bid in current_runner_ids:
            if bid not in bots_map:
                # Bot no longer in allowed list (e.g. STOPPED manually or Deleted)
                logger.info(f"Stopping bot (removed/stopped): {bid}")
                await active_runners[bid].stop()
                del active_runners[bid]
            else:
                # Bot exists, check status
                bot = bots_map[bid]
                if bot['status'] == 'STOPPING':
                    # Needs Graceful Stop
                    logger.info(f"Executing Graceful Stop for {bid}")
                    await active_runners[bid].stop_gracefully()
                    del active_runners[bid]
                
                # If RUNNING, do nothing (keep running)

        # 2. Start New Bots / Handle Orphans
        for bid, bot in bots_map.items():
            if bot['status'] == 'RUNNING' and bid not in active_runners:
                 logger.info(f"Starting new runner: {bot['name']} ({bid})")
                 runner = BotRunner(bot, adapter_client, bot_client)
                 await runner.start()
                 active_runners[bid] = runner
            elif bot['status'] == 'STOPPING' and bid not in active_runners:
                 # It was STOPPING but we don't have a runner.
                 # This implies it crashed or never started. 
                 # Just force status to STOPPED to clean up.
                 logger.info(f"Bot {bid} found in STOPPING but not running. Forcing STOPPED.")
                 await bot_client.update_bot_status(bid, "STOPPED")

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
