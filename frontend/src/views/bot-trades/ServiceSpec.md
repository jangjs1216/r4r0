# BotTradesViewService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**:
  - 봇이 실행한 과거 매매 이력(History) 조회
  - 승률, 손익비, 평균 지연시간(Latency) 등 성과 지표 요약
  - 각 트레이드의 진입/청산 상세 정보 제공

- **하지 않는 일**:
  - 실시간 호가/차트 모니터링 (MarketView 담당)
  - 봇 설정 변경 (BotConfigView 담당)

## 2. 외부 계약 (Contract)

### 2.1 Props (입력)

참조: `contracts/frontend/bot-trades.schema.json`

- **trades**: 매매 이력 리스트 (`entryPx`, `exitPx`, `pnl`, `result`, `latencyMs` 등)
- **summary**: 성과 요약 통계
  - `wins`, `losses`: 승패 횟수
  - `totalPnl`: 누적 손익
  - `avgLatency`: 평균 주문 처리 지연 시간

## 3. 내부 개념 모델 (Domain Model)

- **TradeExecution**: 하나의 완성된 매매 사이클(진입+청산).
- **PerformanceMetrics**: 봇의 효율성을 판단하기 위한 통계 지표.

## 4. 주요 플로우 요약

### 4.1 성과 분석
1. 상단 요약 패널에서 누적 PnL 및 승률 확인.
2. 하단 리스트에서 개별 트레이드 클릭.
3. 상세 정보(슬리피지, 수수료, 지연시간 등) 확인.

## 5. 변경 이력 (Change Log)

- 2025-12-16: 초기 정의 (`contracts/frontend/bot-trades.schema.json` 기반)
