from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

app = FastAPI(title="TradingStrategyViewService", version="1.0.0")

class StrategyDefinition(BaseModel):
    id: str
    name: str
    description: str
    version: str
    schema: Dict[str, Any]  # Field name matches JSON key exactly (No aliases)

# In-memory strategy definitions (Mock Data)
STRATEGIES = [
    {
        "id": "grid_v1",
        "name": "Classic Grid",
        "description": "Places buy and sell orders at fixed intervals.",
        "version": "1.0.0",
        "schema": {
            "type": "object",
            "properties": {
                "upper_price": {"type": "number", "title": "Upper Price"},
                "lower_price": {"type": "number", "title": "Lower Price"},
                "grid_count": {"type": "integer", "minimum": 2, "maximum": 100, "title": "Grid Count", "default": 10}
            },
            "required": ["upper_price", "lower_price", "grid_count"]
        }
    },
    {
        "id": "rsi_basic",
        "name": "RSI Reversal",
        "description": "Buys when oversold, sells when overbought based on RSI.",
        "version": "0.5.0",
        "schema": {
            "type": "object",
            "properties": {
                "period": {"type": "integer", "default": 14, "title": "RSI Period"},
                "buy_threshold": {"type": "number", "default": 30, "title": "Buy Threshold"},
                "sell_threshold": {"type": "number", "default": 70, "title": "Sell Threshold"}
            },
            "required": ["period", "buy_threshold", "sell_threshold"]
        }
    },
    {
        "id": "test_trading_v1",
        "name": "Test Trading (Buy & Sell Loop)",
        "description": "Educational Strategy: Buys specified allocation, holds for duration, then sells. Repeats.",
        "version": "1.0.0",
        "schema": {
            "type": "object",
            "properties": {
                "allocation_ratio": {"type": "number", "minimum": 0.1, "maximum": 1.0, "title": "Buy Allocation Ratio (0.1-1.0)"},
                "hold_duration": {"type": "integer", "minimum": 10, "title": "Hold Duration (Seconds)", "default": 60},
                "loop_count": {"type": "integer", "default": 5, "title": "Loop Count (0=Infinite)"}
            },
            "required": ["allocation_ratio", "hold_duration"]
        }
    }
]

@app.get("/strategies", response_model=List[StrategyDefinition])
def get_strategies():
    # Transform keys if necessary, here we just return the list
    return STRATEGIES

@app.get("/strategies/{strategy_id}", response_model=StrategyDefinition)
def get_strategy(strategy_id: str):
    for s in STRATEGIES:
        if s["id"] == strategy_id:
            return s
    raise HTTPException(status_code=404, detail="Strategy not found")
