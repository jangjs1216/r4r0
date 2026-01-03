import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from services.execution_service.strategies.orderflow_exhaustion_v1 import OrderflowExhaustionV1Strategy

class TestOrderflowExhaustionV1Strategy(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = {
            "name": "test_bot",
            "global_settings": {
                "symbol": "BTC/USDT",
                "exchange": "test_key"
            },
            "pipeline": {
                "strategy": {
                    "id": "orderflow_exhaustion_v1",
                    "params": {
                        "buy_allocation_ratio": 0.5,
                        "cooldown_sec": 0
                    }
                }
            }
        }
        self.strategy = OrderflowExhaustionV1Strategy(self.config)
        self.mock_adapter = AsyncMock()
        self.context = {"adapter": self.mock_adapter}

    async def test_initial_state(self):
        self.assertEqual(self.strategy.state, "FLAT")

    async def test_execute_no_data(self):
        # Setup mocks to return None
        self.mock_adapter.get_ticker.return_value = None
        
        await self.strategy.execute(self.context)
        
        # Should remain FLAT
        self.assertEqual(self.strategy.state, "FLAT")

    async def test_on_stop_liquidation(self):
        # Simulate being IN_POSITION (LONG)
        self.strategy.state = "IN_POSITION"
        self.strategy.position_side = "BUY"
        self.strategy.position_qty = 0.1
        self.strategy.symbol = "BTC/USDT"
        
        # Mock Balance: 0.1 BTC available
        self.mock_adapter.get_balance.return_value = {
            "assets": [{"asset": "BTC", "free": "0.1"}]
        }
        
        # Mock Place Order
        self.mock_adapter.place_order.return_value = {"status": "filled"}

        await self.strategy.on_stop(self.context)

        # Check if sell order was placed
        self.mock_adapter.place_order.assert_called_with(
            key_id="test_key",
            symbol="BTC/USDT",
            side="sell",
            amount=0.1,
            reason="Forced Stop Liquidation (Long Exit)"
        )
        
        # State should be reset
        self.assertEqual(self.strategy.state, "COOLDOWN")
        self.assertIsNone(self.strategy.position_side)

    async def test_on_stop_no_position(self):
        self.strategy.state = "FLAT"
        self.strategy.position_side = None
        
        await self.strategy.on_stop(self.context)
        
        # Should not place any order
        self.mock_adapter.place_order.assert_not_called()

if __name__ == '__main__':
    unittest.main()
