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
    개별 봇의 실행 루프를 관리하는 클래스입니다.
    """
    def __init__(self, bot_config: dict, adapter_client: AdapterClient, bot_client: BotClient):
        self.bot_config = bot_config
        self.adapter_client = adapter_client
        self.bot_client = bot_client
        self.strategy_instance = None
        self.task = None
        self.is_running = False
        self.stop_requested = False

    async def start(self):
        """봇 실행 루프를 시작합니다. 반드시 BOOTING 단계를 거칩니다."""
        # 1. BOOTING 상태로 전이 (SSOT: BotService)
        if self.bot_config.get('status') != 'BOOTING':
             logger.info(f"{self.bot_config['name']} 상태를 BOOTING으로 변경 중")
             await self.bot_client.update_bot_status(self.bot_config['id'], "BOOTING")

        self.is_running = True
        self._initialize_strategy()
        
        # 2. BOOTING 단계에서 초기 사이클 실행
        # 첫 번째 트레이딩 틱(예: 그리드 오픈)이 원장 기록([3/3] COMMIT)까지 
        # 완전히 완료되어야만 RUNNING 상태로 변경되도록 보장합니다.
        logger.info(f"{self.bot_config['name']}의 초기 부팅 사이클(동기화/매매 체크) 수행 중...")
        
        ledger_adapter = LedgerAwareAdapter(
            raw_adapter=self.adapter_client,
            bot_client=self.bot_client,
            bot_id=self.bot_config['id']
        )
        
        context = {
            "adapter": ledger_adapter, 
            "bot_id": self.bot_config['id'],
            "config": self.bot_config
        }
        
        try:
            if self.strategy_instance:
                # 이 호출은 LedgerAwareAdapter.place_order가 [3/3] Commit을 마칠 때까지 블로킹됩니다.
                await self.strategy_instance.execute(context)
            
            # 부팅 시뮬레이션을 위한 추가 지연 (필요 시)
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"{self.bot_config['name']} 부팅 사이클 중 치명적 오류 발생: {e}")
            await self.bot_client.update_bot_status(self.bot_config['id'], "STOPPED")
            self.is_running = False
            return

        # 3. RUNNING 상태로 최종 전이
        # execute()가 예외 없이 종료되었다는 것은 첫 번째 틱의 모든 원장 기록이 완료되었음을 의미합니다.
        logger.info(f"부팅 완료. {self.bot_config['name']} 상태를 RUNNING으로 변경합니다.")
        await self.bot_client.update_bot_status(self.bot_config['id'], "RUNNING")
        
        # 4. 백그라운드 루프로 전환
        self.task = asyncio.create_task(self._run_loop())
        logger.info(f"{self.bot_config['name']}의 BotRunner 루프가 시작되었습니다.")

    async def stop(self):
        """봇 루프를 안전하게 종료(Graceful Stop)합니다."""
        # 1. 상태를 STOPPING으로 변경
        logger.info(f"{self.bot_config['name']} 상태를 STOPPING으로 변경 중")
        await self.bot_client.update_bot_status(self.bot_config['id'], "STOPPING")
        
        # 2. 루프 종료 요청 (플래그 설정)
        self.stop_requested = True
        
        # 3. 루프가 종료될 때까지 대기
        if self.task:
            try:
                # 전략의 on_stop 실행 시간을 고려하여 타임아웃을 넉넉히 설정
                await asyncio.wait_for(self.task, timeout=15.0) 
            except (asyncio.CancelledError, asyncio.TimeoutError):
                logger.warning("종료 대기 중 타임아웃 또는 취소 발생. 강제 종료합니다.")
                self.task.cancel()
        
        # 4. 최종적으로 STOPPED 상태로 전이
        logger.info(f"{self.bot_config['name']} 상태를 STOPPED로 변경합니다.")
        await self.bot_client.update_bot_status(self.bot_config['id'], "STOPPED")
        
        logger.info(f"{self.bot_config['name']}의 BotRunner가 정지되었습니다.")

    def _initialize_strategy(self):
        """
        Factory method to load the correct strategy class based on config.
        """
        self.strategy_instance = TestTradingStrategy(self.bot_config)

    async def _run_loop(self):
        """
        The main infinite loop.
        """
        logger.info("Entering execution loop...")
        
        ledger_adapter = LedgerAwareAdapter(
            raw_adapter=self.adapter_client,
            bot_client=self.bot_client,
            bot_id=self.bot_config['id']
        )
        
        # Context 재사용
        context = {
            "adapter": ledger_adapter, 
            "bot_id": self.bot_config['id'],
            "config": self.bot_config
        }
        
        while self.is_running:
            try:
                # 종료 요청 확인
                if self.stop_requested:
                    logger.info("종료 요청 감지. 전략 정리 작업을 수행합니다.")
                    if self.strategy_instance:
                        # Graceful Stop 로직 실행 (청산 등)
                        if hasattr(self.strategy_instance, 'on_stop'):
                            await self.strategy_instance.on_stop(context)
                    
                    self.is_running = False
                    break

                # Execute Strategy Tick
                if self.strategy_instance:
                    await self.strategy_instance.execute(context)
                
                # Sleep interval (Check every 1s to respond to stop quickly)
                for _ in range(5):
                    if self.stop_requested: break
                    await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in bot loop: {e}")
                traceback.print_exc()
                await asyncio.sleep(5) # Backoff on error
