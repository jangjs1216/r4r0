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
  - `GET /market/ticker?key_id={key_id}&symbol={symbol}`: 현재가 조회.
  - `GET /market/depth?key_id={key_id}&symbol={symbol}&limit={limit}`: 오더북 조회.
  - `GET /market/trades?key_id={key_id}&symbol={symbol}&limit={limit}`: 최근 체결 조회.
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

### 4.2 Bot Stop & Zero Position Policy (Graceful Shutdown)
1. **Stop Request**: 사용자가 봇 정지를 요청하면 `on_stop(ctx)` 훅이 호출된다.
2. **Position Check**: 전략은 `position_side` 및 `actual_balance`를 확인한다.
3. **Liquidation (If Risk On)**:
   - 만약 위험 자산(Base Asset, e.g., BTC)을 보유 중이라면(`BUY` 포지션),
   - `ExchangeAdapter`를 통해 즉시 시장가 매도(Liquidate)를 시도한다.
   - 실패 시 최대 N회(e.g., 5회) 재시도하며, 실 잔고(`min(actual, tracked)`)만큼만 매도하여 안전을 보장한다.
4. **Shutdown**: 포지션이 없거나 청산이 완료되면 봇 프로세스(`BotRunner`)를 종료한다.
   - 이를 통해 봇이 꺼진 후에도 포지션이 남는 "Zombie Position" 리스크를 원천 차단한다.

### 4.3 Supported Strategies
#### Orderflow Exhaustion V1 (`orderflow_exhaustion_v1`)
- **개요**: 호가창(Depth)과 체결(Trades) 데이터를 기반으로 단기적 탐욕/공포를 감지하고, "더 이상 못 가는(Exhaustion)" 시점에 역추세로 진입하는 전략.
- **주요 로직**:
  1. **Pressure Detection**: 최근 체결량 불균형(Buy/Sell Ratio), 스프레드 확장, 미드 가격 급변 등을 감지하여 압력 방향(BUY/SELL Pressure)을 판단.
  2. **Absorption Check**: 압력에도 불구하고 가격이 더 이상 진행되지 않거나 되돌림이 발생하면 "흡수(Absorption)"로 간주. M 틱 이상 흡수가 확인되면 진입 신호 발생.
  3. **Contrarian Entry**:
     - BUY Pressure 흡수 시 -> **SELL** (Short) 진입. (현물인 경우 Base Asset 매도)
     - SELL Pressure 흡수 시 -> **BUY** (Long) 진입. (현물인 경우 USDT 매도/Base 매수)
  4. **Exit Management**:
     - Take Profit / Stop Loss (Hard & Soft)
     - Time Stop (지정 시간 내 청산)
     - Cooldown (매매 종료 후 일정 시간 휴식)

## 5. 변경 이력 (Change Log)
- 2025-12-28: 초기 정의.
- 2026-01-03: Bot Stop 시 잔고 확인 및 강제 청산을 보장하는 Zero Position Policy 명시.
