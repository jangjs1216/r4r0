from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

class TimeRange(BaseModel):
    start_date: datetime
    end_date: datetime

class BacktestMetrics(BaseModel):
    total_pnl: float
    cagr: float
    mdd: float
    sharpe_ratio: float
    win_rate: float
    profit_factor: float
    alpha_gross: float = Field(..., description="Gross profit before costs")
    total_cost: float = Field(..., description="Total accumulated costs")

class CostBreakdown(BaseModel):
    spread_cost: float
    slippage_cost: float
    commission: float
    funding_fee: float

class EquityPoint(BaseModel):
    timestamp: int  # Unix ms
    balance: float
    buy_hold_price: Optional[float] = None

class TradeRecord(BaseModel):
    timestamp: int
    side: Literal["BUY", "SELL"]
    price: float
    size: float
    cost: float  # Total cost for this trade

class RunBacktestRequest(BaseModel):
    bot_config: Dict[str, Any]  # Full JSON config from BotService
    time_range: TimeRange
    initial_capital: float = 10000.0
    slippage_model: Literal["NONE", "LOW", "MEDIUM", "HIGH"] = "MEDIUM"

class BacktestResponse(BaseModel):
    job_id: str
    status: Literal["COMPLETED", "FAILED"]
    metrics: BacktestMetrics
    cost_breakdown: CostBreakdown
    equity_curve: List[EquityPoint]
    trades: List[TradeRecord]
