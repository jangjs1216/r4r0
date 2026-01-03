import httpx
import logging
import os

logger = logging.getLogger("execution-service.bot-client")

BOT_SERVICE_URL = os.getenv("BOT_SERVICE_URL", "http://bot-service:8000")

class BotClient:
    async def get_running_bots(self):
        async with httpx.AsyncClient() as client:
            try:
                # 모든 봇을 가져와서 로컬에서 활성 상태 필터링
                # BOOTING, RUNNING, STOPPING 상태가 필요함
                resp = await client.get(f"{BOT_SERVICE_URL}/bots")
                resp.raise_for_status()
                all_bots = resp.json()
                
                # 활성 봇 필터링
                active_states = ["BOOTING", "RUNNING", "STOPPING"]
                return [b for b in all_bots if b.get("status") in active_states]
            except httpx.RequestError as exc:
                logger.error(f"BotService 요청 중 오류 발생: {exc}")
                return []
            except httpx.HTTPStatusError as exc:
                logger.error(f"BotService 요청 중 오류 응답 {exc.response.status_code}.")
                return []
    async def update_bot_status(self, bot_id: str, status: str, message: str = None):
        """
        봇의 상태를 업데이트합니다. (READ -> MODIFY -> PUT 패턴)
        BotService가 PATCH를 지원하지 않으므로, 전체 정보를 조회 후 상태만 변경하여 업데이트합니다.
        """
        async with httpx.AsyncClient() as client:
            try:
                # 1. 현재 봇 정보 조회
                get_resp = await client.get(f"{BOT_SERVICE_URL}/bots/{bot_id}")
                get_resp.raise_for_status()
                bot_data = get_resp.json()

                # 2. 업데이트 페이로드 구성 (BotUpdate 스키마에 맞춤)
                # message가 있으면 덮어쓰고, 없으면 기존 메시지 유지 (또는 None)
                new_message = message if message is not None else bot_data.get("status_message")
                
                payload = {
                    "name": bot_data["name"],
                    "status": status,
                    "status_message": new_message,
                    "global_settings": bot_data["global_settings"],
                    "pipeline": bot_data["pipeline"]
                }

                # 3. PUT 요청 전송
                put_resp = await client.put(f"{BOT_SERVICE_URL}/bots/{bot_id}", json=payload)
                put_resp.raise_for_status()
                
                logger.info(f"봇 {bot_id} 상태 업데이트 성공: {status}")
                return put_resp.json()
                
            except Exception as e:
                logger.error(f"봇 상태 업데이트 실패 ({bot_id} -> {status}): {e}")
                return None

    async def stop_bot_session(self, bot_id: str):
        """
        [BotService] 봇의 세션을 명시적으로 종료합니다. (POST /bots/{id}/stop)
        이 호출은 Session 상태를 'ENDED'로 변경하고 Bot 상태를 'STOPPED'로 변경합니다.
        SSOT인 BotService의 상태를 업데이트하는 가장 확실한 방법입니다.
        """
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{BOT_SERVICE_URL}/bots/{bot_id}/stop")
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"세션 종료 요청 실패 ({bot_id}): {e}")
                return None

    async def create_local_order(self, bot_id, symbol, side, quantity, reason, timestamp):
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "bot_id": bot_id,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "reason": reason,
                    "timestamp": timestamp.isoformat() if timestamp else None
                }
                resp = await client.post(f"{BOT_SERVICE_URL}/orders", json=payload)
                resp.raise_for_status()
                return resp.json() # {"id": "...", "status": "..."} 반환
            except Exception as e:
                logger.error(f"Failed to create local order: {e}")
                return None

    async def update_order_status(self, local_order_id, status):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.put(f"{BOT_SERVICE_URL}/orders/{local_order_id}/status", json={"status": status})
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Failed to update order status {local_order_id}: {e}")
                return None

    async def record_execution(self, execution_data):
        async with httpx.AsyncClient() as client:
            try:
                # execution_data는 GlobalExecutionCreate 스키마와 일치해야 합니다.
                # timestamp가 datetime 객체인 경우 변환합니다.
                if "timestamp" in execution_data and not isinstance(execution_data["timestamp"], str):
                     execution_data["timestamp"] = execution_data["timestamp"].isoformat()

                resp = await client.post(f"{BOT_SERVICE_URL}/executions", json=execution_data)
                resp.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Failed to record execution: {e}")
                return False
