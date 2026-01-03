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
    },
    {
        "id": "orderflow_exhaustion_v1",
        "name": "오더플로우 고갈 역추세 (Orderflow Exhaustion Fade)",
        "description": "탐욕/공포성 시장가 주문(체결 불균형) 이후, 더 못 가는 '흡수/고갈'이 확인되면 반대 방향으로 진입합니다. (현물 기반: SELL은 보유 base 자산 일부 매도 후 되돌림에서 재매수)",
        "version": "1.0.0",
        "schema": {
            "type": "object",
            "properties": {
                "depth_limit": {"type": "integer", "minimum": 5, "maximum": 200, "default": 50, "title": "오더북 Depth Limit"},
                "trades_limit": {"type": "integer", "minimum": 20, "maximum": 1000, "default": 200, "title": "최근 체결 조회 개수"},
                "trades_lookback_sec": {"type": "integer", "minimum": 3, "maximum": 60, "default": 10, "title": "체결 집계 구간(초)"},

                "delta_ratio_threshold": {"type": "number", "minimum": 1.2, "maximum": 10.0, "default": 2.5, "title": "체결 불균형 비율 임계값"},
                "min_total_quote_volume": {"type": "number", "minimum": 0, "default": 50.0, "title": "최소 체결대금(Quote)"},

                "spread_expand_ratio_threshold": {"type": "number", "minimum": 1.0, "maximum": 10.0, "default": 1.5, "title": "스프레드 확장 비율 임계값"},
                "sweep_move_pct_threshold": {"type": "number", "minimum": 0.0, "maximum": 0.05, "default": 0.001, "title": "미드 가격 급변(%) 임계값"},
                "confirm_absorption_ticks": {"type": "integer", "minimum": 1, "maximum": 10, "default": 2, "title": "흡수 확인 틱 수"},

                "buy_allocation_ratio": {"type": "number", "minimum": 0.01, "maximum": 1.0, "default": 0.1, "title": "BUY 할당 비율(Quote 기준)"},
                "sell_allocation_ratio": {"type": "number", "minimum": 0.01, "maximum": 1.0, "default": 0.1, "title": "SELL 할당 비율(Base 기준)"},
                "quantity_precision": {"type": "integer", "minimum": 0, "maximum": 12, "default": 5, "title": "수량 반올림 자릿수"},

                "take_profit_pct": {"type": "number", "minimum": 0.0, "maximum": 0.1, "default": 0.003, "title": "익절(%)"},
                "stop_loss_pct": {"type": "number", "minimum": 0.0, "maximum": 0.1, "default": 0.004, "title": "손절(%)"},
                "stop_buffer_pct": {"type": "number", "minimum": 0.0, "maximum": 0.05, "default": 0.001, "title": "스윕 고/저점 버퍼(%)"},
                "time_stop_sec": {"type": "integer", "minimum": 10, "maximum": 3600, "default": 180, "title": "시간 청산(초)"},
                "cooldown_sec": {"type": "integer", "minimum": 0, "maximum": 3600, "default": 120, "title": "쿨다운(초)"},

                "spread_ema_alpha": {"type": "number", "minimum": 0.01, "maximum": 1.0, "default": 0.2, "title": "스프레드 EMA 알파"},
                "spread_normalized_max_ratio": {"type": "number", "minimum": 1.0, "maximum": 5.0, "default": 1.2, "title": "스프레드 정상화 최대비율"}
            },
            "required": []
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
