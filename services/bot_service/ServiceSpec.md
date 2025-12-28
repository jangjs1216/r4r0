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
