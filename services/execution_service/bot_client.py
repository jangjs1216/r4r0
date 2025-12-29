import httpx
import logging
import os

logger = logging.getLogger("execution-service.bot-client")

BOT_SERVICE_URL = os.getenv("BOT_SERVICE_URL", "http://bot-service:8000")

class BotClient:
    async def get_running_bots(self):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{BOT_SERVICE_URL}/bots", params={"status": "RUNNING,STOPPING"})
                resp.raise_for_status()
                return resp.json()
            except httpx.RequestError as exc:
                logger.error(f"An error occurred while requesting BotService: {exc}")
                return []
            except httpx.HTTPStatusError as exc:
                logger.error(f"Error response {exc.response.status_code} while requesting BotService.")
                return []

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
                return resp.json() # Returns {"id": "...", "status": "..."}
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
                # execution_data should match GlobalExecutionCreate schema
                # Convert timestamp if it's a datetime object
                if "timestamp" in execution_data and not isinstance(execution_data["timestamp"], str):
                     execution_data["timestamp"] = execution_data["timestamp"].isoformat()

                resp = await client.post(f"{BOT_SERVICE_URL}/executions", json=execution_data)
                resp.raise_for_status()
                return True
            except Exception as e:
                logger.error(f"Failed to record execution: {e}")
                return False

    async def get_bot_position(self, bot_id):
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{BOT_SERVICE_URL}/bots/{bot_id}/position")
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Failed to get bot position: {e}")
                return None

    async def update_bot_status(self, bot_id, status):
        """
        Updates bot status by fetching current config and PUTting it back with new status.
        Uses GET -> PUT pattern since PATCH is not available.
        """
        async with httpx.AsyncClient() as client:
            try:
                # 1. Get current bot info
                get_resp = await client.get(f"{BOT_SERVICE_URL}/bots/{bot_id}")
                get_resp.raise_for_status()
                bot_data = get_resp.json()
                
                # 2. Update status in payload
                # BotUpdate schema expects name, status, global_settings, pipeline
                payload = {
                    "name": bot_data["name"],
                    "status": status,
                    "global_settings": bot_data["global_settings"],
                    "pipeline": bot_data["pipeline"]
                }
                
                # 3. PUT update
                put_resp = await client.put(f"{BOT_SERVICE_URL}/bots/{bot_id}", json=payload)
                put_resp.raise_for_status()
                return True
                
            except Exception as e:
                logger.error(f"Failed to update bot status {bot_id} to {status}: {e}")
                return False
