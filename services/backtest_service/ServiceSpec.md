# Backtest Service Specification

## 1. 개요 (Overview)
`BacktestService`는 봇 설정과 과거 시장 데이터를 기반으로 시뮬레이션을 수행하고, 성과 지표(CAGR, MDD, Sharpe)와 비용 분석(Alpha vs Cost) 결과를 반환합니다.

## 2. API 명세 (API Specification)

### 2.1 실행 (Run Simulation)
**Endpoint**: `POST /run`

**Request Body (`RunBacktestRequest`)**
```json
{
  "bot_config": {
    "name": "Grid Bot Test",
    "global_settings": { ... },
    "pipeline": { ... }
  },
  "time_range": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-02-01T00:00:00Z"
  },
  "initial_capital": 10000.0,
  "slippage_model": "MEDIUM"  // NONE, LOW(0.05%), MEDIUM(0.1%), HIGH(0.2%)
}
```

**Response Body (`BacktestResponse`)**
```json
{
  "job_id": "uuid-...",
  "status": "COMPLETED",
  "metrics": {
    "total_pnl": 1500.0,
    "cagr": 25.5,
    "mdd": -12.4,
    "sharpe_ratio": 1.8,
    "win_rate": 0.65,
    "profit_factor": 1.5,
    "alpha_gross": 2000.0,    // 순수 매매 이익 (비용 제외)
    "total_cost": 500.0       // 총 비용 (스프레드+슬리피지+수수료+펀딩)
  },
  "cost_breakdown": {
    "spread_cost": 100.0,
    "slippage_cost": 200.0,
    "commission": 150.0,
    "funding_fee": 50.0
  },
  "equity_curve": [
    { "timestamp": 1704067200000, "balance": 10000.0, "buy_hold_price": 42000.0 },
    ...
  ],
  "trades": [
    { "timestamp": ..., "side": "BUY", "price": 42100, "size": 0.1, "cost": 4.2 }
  ]
}
```

## 3. 데이터 모델 (Data Models)

### 3.1 Slippage Model
- **NONE**: 0% (이상적 상황)
- **LOW**: 0.05% (유동성 풍부)
- **MEDIUM**: 0.1% (평균)
- **HIGH**: 0.2% (변동성 심함)

### 3.2 Constants
- **Commission Rate**: 0.05% (Binance VIP 0 기준)
- **Funding Interval**: 8시간 (시장 평균)
