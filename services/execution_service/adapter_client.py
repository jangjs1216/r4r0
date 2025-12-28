import httpx
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger("execution-service.adapter-client")

ADAPTER_SERVICE_URL = os.getenv("ADAPTER_SERVICE_URL", "http://exchange-adapter:8000")

class AdapterClient:
    async def get_balance(self, key_id: str) -> Dict[str, Any]:
        """
        Fetch account balance via Adapter.
        """
        async with httpx.AsyncClient() as client:
            try:
                # Assuming Adapter exposes /balance/{key_id}
                resp = await client.get(f"{ADAPTER_SERVICE_URL}/balance/{key_id}")
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.error(f"Failed to fetch balance: {e}")
                return {}

    async def get_ticker(self, key_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch current price via Adapter.
        Returns the full ticker dictionary, including 'price' and optionally 'limits'.
        """
        async with httpx.AsyncClient() as client:
            try:
                # Assuming Adapter exposes /market/ticker?key_id={key_id}&symbol={symbol}
                resp = await client.get(f"{ADAPTER_SERVICE_URL}/market/ticker", params={"key_id": key_id, "symbol": symbol})
                resp.raise_for_status()
                data = resp.json()
                # Return the whole data dict (contains "price", "limits", "symbol")
                return data
            except Exception as e:
                logger.error(f"Failed to fetch ticker: {e}")
                return None
        
    async def place_order(self, key_id: str, symbol: str, side: str, amount: float, order_type: str = 'market', price: float = None) -> Dict[str, Any]:
        """
        Place an order via Adapter.
        """
        async with httpx.AsyncClient() as client:
             try:
                payload = {
                    "key_id": key_id,
                    "symbol": symbol,
                    "side": side,
                    "amount": amount,
                    "order_type": order_type,
                    "price": price
                }
                resp = await client.post(f"{ADAPTER_SERVICE_URL}/order", json=payload)
                resp.raise_for_status()
                return resp.json()
             except Exception as e:
                 logger.error(f"Failed to place order: {e}")
                 # Return error dict or raise
                 return {"status": "error", "error": str(e)}
