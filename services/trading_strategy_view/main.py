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

# 인메모리 전략 정의 (Mock 데이터)
STRATEGIES = [
    {
        "id": "grid_v1",
        "name": "클래식 그리드 (Classic Grid)",
        "description": "설정된 구간 내에서 일정 간격으로 매수/매도 주문을 배치합니다.",
        "version": "1.0.0",
        "schema": {
            "type": "object",
            "properties": {
                "upper_price": {"type": "number", "title": "상단 가격"},
                "lower_price": {"type": "number", "title": "하단 가격"},
                "grid_count": {"type": "integer", "minimum": 2, "maximum": 100, "title": "그리드 개수", "default": 10}
            },
            "required": ["upper_price", "lower_price", "grid_count"]
        }
    },
    {
        "id": "rsi_basic",
        "name": "RSI 역추세 (RSI Reversal)",
        "description": "RSI 지표를 기반으로 과매도 시 매수, 과매수 시 매도합니다.",
        "version": "0.5.0",
        "schema": {
            "type": "object",
            "properties": {
                "period": {"type": "integer", "default": 14, "title": "RSI 기간"},
                "buy_threshold": {"type": "number", "default": 30, "title": "매수 임계값"},
                "sell_threshold": {"type": "number", "default": 70, "title": "매도 임계값"}
            },
            "required": ["period", "buy_threshold", "sell_threshold"]
        }
    },
    {
        "id": "test_trading_v1",
        "name": "테스트 트레이딩 (매수 & 매도 루프)",
        "description": "교육용 전략: 지정된 비율만큼 매수 후 일정 시간 보유하다가 전량 매도합니다. 이를 반복합니다.",
        "version": "1.0.0",
        "schema": {
            "type": "object",
            "properties": {
                "allocation_ratio": {"type": "number", "minimum": 0.1, "maximum": 1.0, "title": "매수 할당 비율 (0.1-1.0)"},
                "hold_duration": {"type": "integer", "minimum": 10, "title": "보유 기간 (초)", "default": 60},
                "loop_count": {"type": "integer", "default": 5, "title": "반복 횟수 (0=무한)"}
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
