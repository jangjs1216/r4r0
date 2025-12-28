# TradingStrategyViewService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**: 사용 가능한 매매 전략(Trading Strategy)의 메타데이터와 파라미터 스키마를 제공하는 서비스.
- **책임**:
  - 지원하는 전략 목록 제공 (예: Grid, RSI, VWAP).
  - 각 전략의 파라미터(Parameter)에 대한 JSON Schema 제공 (Frontend가 동적 폼을 그리기 위함).
- **하지 않는 일**:
  - 실제 전략 실행 (StrategyEngine 담당).
  - 봇 설정 저장 (BotService 담당).

## 2. 외부 계약 (Contract)

### 2.1 REST API

- **Base URL**: `/strategies`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | 가용한 모든 전략의 목록과 스키마 조회 |
| `GET` | `/{strategy_id}` | 특정 전략의 상세 스키마 조회 |

### 2.2 응답 구조 (StrategyMetadata)

```json
[
  {
    "id": "grid_v1",
    "name": "Grid Trading Strategy",
    "description": "Buy low, sell high within a specific price range.",
    "version": "1.0.0",
    "schema": {
      "type": "object",
      "properties": {
        "upper_price": { "type": "number", "description": "Upper bound of the grid" },
        "lower_price": { "type": "number", "description": "Lower bound of the grid" },
        "grid_count": { "type": "integer", "minimum": 2, "maximum": 100 }
      },
      "required": ["upper_price", "lower_price", "grid_count"]
    }
  },
  {
    "id": "test_trading_v1",
    "name": "Test Trading (Buy & Sell Loop)",
    "description": "Educational Strategy: Buys specified allocation, holds for duration, then sells. Repeats.",
    "version": "1.0.0",
    "schema": {
      "type": "object",
      "properties": {
        "allocation_ratio": { "type": "number", "minimum": 0.1, "maximum": 1.0, "title": "Buy Allocation Ratio (0.1-1.0)" },
        "hold_duration": { "type": "integer", "minimum": 10, "title": "Hold Duration (Seconds)", "default": 60 },
        "loop_count": { "type": "integer", "default": 5, "title": "Loop Count (0=Infinite)" }
      },
      "required": ["allocation_ratio", "hold_duration"]
    }
  }
]
```

## 3. 내부 개념 모델

- **StrategyDefinition**: 전략의 ID, 이름, 설명, 파라미터 스키마를 담은 불변 객체.
  - 현재는 코드 내에 하드코딩되거나 정적 파일(JSON/YAML)로 관리됨.

## 4. 주요 플로우 요약

1. **봇 생성/수정 진입**: 
   - `BotEditorView`가 로드될 때 `GET /strategies` 호출.
2. **동적 폼 렌더링**:
   - Frontend는 사용자가 선택한 전략(`id`)의 `schema`를 참조하여 입력 필드를 생성.

## 5. 변경 이력

- 2025-12-28: 초기 정의 (Bot Pipeline Plan 기반)
