from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any

app = FastAPI(title="TradingStrategyViewService", version="1.0.0")

class StrategyDefinition(BaseModel):
    id: str
    name: str
    description: str
    version: str
    schema_def: Dict[str, Any] = Field(..., alias="schema")  # Map internal 'schema_def' to JSON 'schema'

# In-memory strategy definitions (Mock Data)
STRATEGIES = [
    {
        "id": "grid_v1",
        "name": "Classic Grid",
        "description": "Places buy and sell orders at fixed intervals.",
        "version": "1.0.0",
        "schema_def": {
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
        "schema_def": {
            "type": "object",
            "properties": {
                "period": {"type": "integer", "default": 14, "title": "RSI Period"},
                "buy_threshold": {"type": "number", "default": 30, "title": "Buy Threshold"},
                "sell_threshold": {"type": "number", "default": 70, "title": "Sell Threshold"}
            },
            "required": ["period", "buy_threshold", "sell_threshold"]
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
