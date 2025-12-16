# DashboardViewService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**:
  - 사용자의 자산 현황 요약 (Total Equity, PnL)
  - 현재 활성 포지션의 간략한 리스트 제공
  - 시스템/계정 상태의 '한 눈에 보기' 대시보드 제공

- **하지 않는 일**:
  - 개별 포지션의 상세 청산/수정 조작 (PortfolioView 또는 MarketView 위임)
  - 차트 상세 분석

## 2. 외부 계약 (Contract)

### 2.1 Props (입력)

참조: `contracts/frontend/dashboard.schema.json`

- **user**: 사용자 기본 정보
- **balances**:
  - `totalEquity`: 총 자산 가치
  - `dayPnl`, `weekPnl`: 기간별 손익
  - `cash`: 현금 잔고
- **positions**: `Position` 객체의 배열 (요약본)
- **focusPosition**: 현재 포커스된(가장 중요한) 포지션 또는 null
- **timestamp**: 데이터 기준 시간

### 2.2 Events (출력)

- 포지션 클릭 시 상세 화면 이동 요청 (Orchestrator 경유)

## 3. 내부 개념 모델 (Domain Model)

- **AccountSummary**: 자산, PnL 등을 포함한 계정 요약 객체.
- **PositionSummary**: 심볼, 사이즈, 수익률 등 핵심 정보만 담은 포지션 객체.

## 4. 주요 플로우 요약

### 4.1 대시보드 로드
1. View 마운트 시 최신 `balances` 및 `positions` 데이터 수신.
2. 총 자산 및 일일 등락폭 강조 표시.
3. 활성 포지션 리스트 렌더링.

## 5. 변경 이력 (Change Log)

- 2025-12-16: 초기 정의 (`contracts/frontend/dashboard.schema.json` 기반)
