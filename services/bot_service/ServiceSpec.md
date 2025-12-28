# BotService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**: 봇 인스턴스의 설정(Config), 상태(Status), 생명주기(Lifecycle)를 관리하는 서비스.
- **책임**:
  - 봇 생성, 수정, 삭제, 조회 (CRUD).
  - 봇 설정(JSON)의 영속화 (SQLite).
- **하지 않는 일**:
  - 실제 매매 로직 실행 (StrategyEngine이 담당).
  - 실시간 데이터 수집 (ExchangeAdapter/MarketService가 담당).
  - 전략 메타데이터 제공 (TradingStrategyViewService가 담당).

## 2. 외부 계약 (Contract)

### 2.1 REST API

- **Base URL**: `/bots`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | 모든 봇 목록 조회 (요약 정보) |
| `POST` | `/` | 새로운 봇 생성 |
| `GET` | `/{bot_id}` | 특정 봇의 상세 설정 조회 |
| `PUT` | `/{bot_id}` | 봇 설정 수정 |
| `DELETE` | `/{bot_id}` | 봇 삭제 |

### 2.2 입력 파라미터 (DTO)

**CreateBotRequest / UpdateBotRequest**
```json
{
  "name": "My Bitcoin Grid Bot",
  "status": "STOPPED",
  "global_settings": {
    "exchange": "binance_01",
    "symbol": "BTC/USDT",
    "account_allocation": "1000",
    "mode": "PAPER"
  },
  "pipeline": {
    "data_source": { "frame": "1h" },
    "strategy": {
      "id": "grid_v1",
      "params": { "grids": 10, "upper": 50000, "lower": 40000 }
    },
    "risk_management": { "stop_loss": 0.05 },
    "execution": { "type": "MAKER_ONLY" },
    "triggers": { "schedule": "ALWAYS" }
  }
}
```

### 2.3 응답 구조

**BotResponse**
- 위 Request 구조에 `id` (UUID), `created_at`, `updated_at` 필드가 추가됨.

## 3. 내부 개념 모델 (Domain Model)

- **Bot**: 봇 엔티티.
  - `id`: UUID (Primary Key)
  - `name`: String
  - `status`: Enum (STOPPED, RUNNING, PAUSED, ERROR)
  - `config`: JSON (전체 파이프라인 설정 저장)
  - `created_at`: Datetime
  - `updated_at`: Datetime

## 4. 주요 플로우 요약

1. **봇 생성**: 
   - 사용자가 Editor에서 설정 완료 -> `POST /bots` 호출 -> DB 저장 -> 생성된 ID 반환.
2. **봇 목록 조회**:
   - `BotConfigView` 진입 시 `GET /bots` 호출 -> 이름, 상태, 수익률(별도 집계 시) 등 요약 리스트 반환.
3. **봇 수정**:
   - `BotEditorView` 진입 시 `GET /bots/{id}` -> 설정 로드 -> 수정 후 `PUT /bots/{id}`.

## 5. 변경 이력 (Change Log)

- 2025-12-28: 초기 정의 (Bot Pipeline Plan 기반)
- 2025-12-28: 이중 원장(Double-Entry Ledger) 시스템을 위한 `LocalOrder`, `GlobalExecution` 모델 및 API 추가

---

## 6. 추가 모델: 원장 시스템 (Ledger System)

### 6.1 개념 모델
- **LocalOrder (로컬 주문)**: 봇이 매매를 결심한 '의도'와 '시점'을 기록.
  - `id`: UUID (Primary Key)
  - `bot_id`: UUID (Foreign Key)
  - `symbol`: String
  - `side`: Enum (BUY, SELL)
  - `quantity`: Float
  - `timestamp`: DateTime (정확한 의사결정 시각)
  - `status`: Enum (PENDING, SENT, FILLED, FAILED)
  - `reason`: String (매매 근거 - 시각화용)

- **GlobalExecution (글로벌 체결)**: 거래소에서 실제로 체결된 결과.
  - `id`: String (Exchange Trade ID, Primary Key)
  - `local_order_id`: UUID (Foreign Key)
  - `exchange_order_id`: String (Exchange Order ID)
  - `position_id`: String (Optional)
  - `symbol`: String
  - `price`: Float
  - `quantity`: Float
  - `fee`: Float
  - `timestamp`: DateTime (거래소 체결 시각)

### 6.2 Ledger API

**POST /orders** (로컬 주문 기록)
```json
{
  "bot_id": "uuid...",
  "symbol": "BTC/USDT",
  "side": "BUY",
  "quantity": 1.5,
  "reason": "RSI < 30",
  "timestamp": "2025-..."
}
```
Response: `{"id": "local_order_uuid"}`

**PUT /orders/{id}/status** (상태 업데이트)
```json
{
  "status": "SENT" or "FAILED"
}
```

**POST /executions** (체결 기록)
```json
{
  "local_order_id": "local_order_uuid",
  "exchange_trade_id": "12345",
  "exchange_order_id": "987654",
  "symbol": "BTC/USDT",
  "price": 50000.0,
  "quantity": 1.5,
  "fee": 0.001,
  "timestamp": "2025-..."
}
```
