# Execution Service - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**: 'RUNNING' 상태인 봇을 감지하고, 실제 매매 전략(Loop)을 실행하는 **Worker Service**.
- **책임**:
  - BotService로부터 실행할 봇 목록 조회 (Polling/Event).
  - ExchangeAdapterService와 통신하여 시세/잔고 조회 및 주문 실행.
  - 전략 로직(`Strategy Engine`) 구동 및 상태 관리.
  - 실행 로그(Execution Log) 생성.
- **하지 않는 일**:
  - 봇 설정(Config)의 원본 데이터 관리 (BotService 책임).
  - API Key의 직접 관리 및 복호화 (AuthService 책임).
  - 전략 메타데이터 정의 (TradingStrategyViewService 책임).

## 2. 외부 계약 (Contract)

### 2.1 API Endpoints (Control Plane)
ExecutionService는 주로 **Background Worker**로 동작하지만, 상태 모니터링을 위한 최소한의 API를 제공한다.

- `GET /health`: 서비스 상태 확인.
- `GET /status`: 현재 실행 중인 봇 목록 및 상태 요약 (Debug용).

### 2.2 Dependencies (Outbound Calls)
- **BotService**: `GET /bots?status=RUNNING` (실행 대상 조회).
- **ExchangeAdapterService**:
  - `GET /balance/{key_id}`: 잔고 조회.
  - `GET /market/ticker?symbol={symbol}`: 현재가 조회.
  - `POST /order`: 주문 실행.

## 3. 내부 개념 모델 (Domain Model)

- **BotRunner**: 하나의 봇 인스턴스를 실행하는 논리적 단위 (Thread or Task).
- **StrategyContext**: 전략 실행에 필요한 문맥 정보 (Ticker, Balance, Config).
- **ControlLoop**: 주기적으로(e.g. 1초, 1분) 전략 로직을 수행하는 루프.

## 4. 주요 플로우 요약

### 4.1 Bot Running Flow
1. **Poller Loop**: 주기적으로 `BotService`에서 `RUNNING` 봇 목록을 가져온다.
2. **Diff & Sync**:
   - 새로 추가된 봇 -> `BotRunner` 생성 및 시작.
   - 사라지거나 STOPPED된 봇 -> `BotRunner` 중지 및 정리.
3. **BotRunner Loop**:
   - 설정된 전략(Ex: `test_trading`)의 `execute(ctx)` 메서드 호출.
   - 전략 내부에서 Adapter 호출 -> 주문 실행.

## 5. 변경 이력 (Change Log)
- 2025-12-28: 초기 정의.
