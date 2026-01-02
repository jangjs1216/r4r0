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
    주기적으로 실행 중인 봇 목록을 동기화하는 작업입니다.
    """
    try:
        runners_list = await bot_client.get_running_bots()
        active_ids = {bot['id'] for bot in runners_list}
        
        # 1. 새로운 봇 시작 (BOOTING 상태 포함)
        # RUNNING 또는 BOOTING 상태라면 '활성(Active)'으로 간주합니다.
        # 주의: get_running_bots()는 클라이언트 내부 필터링을 통해 RUNNING, BOOTING, STOPPING을 모두 반환합니다.
        
        for bot in runners_list:
            bid = bot['id']
            status = bot.get('status')
            
            # 봇이 STOPPING 상태라면, 종료 프로세스를 완료할 러너가 필요합니다.
            # 봇이 BOOTING 상태라면, 부팅 프로세스를 완료할 러너를 시작해야 합니다.
            
            if bid not in active_runners:
                if status in ['RUNNING', 'BOOTING']:
                    logger.info(f"새로운 봇 러너 시작: {bot['name']} ({bid}) [상태: {status}]")
                    runner = BotRunner(bot, adapter_client, bot_client)
                    await runner.start() # start() 내부에서 BOOTING -> RUNNING 처리
                    active_runners[bid] = runner
                elif status == 'STOPPING':
                     # 러너가 없는데 상태가 STOPPING인 경우 -> 고아(Zombie) 상태
                     # 서비스 재시작 등으로 인해 발생할 수 있음. 강제로 STOPPED로 리셋.
                     logger.warning(f"고아(Orphan) STOPPING 봇 발견: {bid}. STOPPED로 강제 리셋합니다.")
                     await bot_client.update_bot_status(bid, "STOPPED", message="서비스 재시작으로 인한 상태 초기화")
            else:
                # 이미 실행 중인 러너가 있는 경우. 중지가 필요한지 확인합니다.
                # DB 상태가 STOPPING이면 러너의 stop()을 호출합니다.
                if status == 'STOPPING':
                     runner = active_runners[bid]
                     if runner.is_running:
                         logger.info(f"{bid}의 STOPPING 상태 감지. 안전한 종료(Graceful Stop)를 시작합니다.")
                         # 폴링 루프를 차단하지 않도록 별도 태스크로 stop() 실행
                         asyncio.create_task(_stop_and_cleanup(bid, runner))

        # 2. 제거된 봇 정리 (고아 프로세스 방지)
        # 목록에서 완전히 사라진 봇(삭제되었거나 STOPPED로 변한 경우)은 로컬 러너도 정지해야 합니다.
        current_ids = list(active_runners.keys())
        for bid in current_ids:
            if bid not in active_ids:
                 # 고아(Orphan) 봇입니다. 정지시킵니다.
                 logger.info(f"목록에서 사라진 봇(고아) 정지: {bid}")
                 runner = active_runners[bid]
                 asyncio.create_task(_stop_and_cleanup(bid, runner))
                 
    except Exception as e:
        logger.error(f"폴링 루프 중 오류 발생: {e}")

async def _stop_and_cleanup(bid, runner):
    """러너를 정지하고 관리 딕셔너리에서 제거하는 헬퍼 함수입니다."""
    await runner.stop() # 여기서 RUNNING -> STOPPING -> STOPPED 전환을 처리함
    if bid in active_runners:
        del active_runners[bid]

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
