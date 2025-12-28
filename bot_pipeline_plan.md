# Bot Pipeline Implementation Plan

This document outlines the step-by-step plan to implement the **Bot Pipeline Configuration** in `Bot-Editor`.
It is designed to satisfy the principles in `bible.md` (Microservices, Independent Views, Strict Contracts).

## 1. Architecture Design

### Microservices
1.  **BotService (Backend)**:
    -   **Role**: Manages the lifecycle and configuration of Bot instances.
    -   **Responsibility**: CRUD for Bot configs, persisting to SQLite/DB.
2.  **TradingStrategyViewService (Backend)**:
    -   **Role**: Provides metadata and JSON Schemas for available strategies.
    -   **Responsibility**: Returns list of strategies (e.g., Grid, RSI) and their parameter constraints.
3.  **BotEditorView (Frontend)**:
    -   **Role**: The UI for configuring the bot pipeline.
    -   **Responsibility**: Fetches schemas from `TradingStrategyViewService`, renders dynamic forms, saves config to `BotService`.

### Data Model (JSON Structure)
The `BotConfig` object will be stored in `BotService`.

```json
{
  "id": "uuid",
  "name": "My Grid Bot",
  "status": "STOPPED", // RUNNING, BACKTESTING
  "global_settings": {
    "exchange": "BINANCE_OAUTH_ID", // Link to AuthService
    "symbol": "BTC/USDT",
    "account_allocation": "1000 USDT",
    "mode": "PAPER" // REAL, BACKTEST
  },
  "pipeline": {
    "data_source": { "frame": "1h" },
    "strategy": {
      "id": "grid_v1",
      "params": { "grids": 10, "upper": 50000, "lower": 40000 }
    },
    "risk_management": {
      "stop_loss": 0.05,
      "max_drawdown": 0.1
    },
    "execution": {
      "type": "MAKER_ONLY",
      "timeout": 30
    },
    "triggers": {
      "schedule": "ALWAYS"
    }
  }
}
```

---

## 2. Implementation Phases

**Note**: Each phase should be verifiable before moving to the next.

### Phase 1: Backend Foundation (The Services)

-   [x] **Create `services/bot_service`**
    -   Setup `FastAPI`, `SQLite` (or file-based DB).
    -   Define `Bot` model and Pydantic schemas.
    -   Implement API: `GET /bots`, `POST /bots`, `GET /bots/{id}`, `PUT /bots/{id}`.
    -   Create `ServiceSpec.md`.
-   [x] **Create `services/trading_strategy_view`**
    -   Setup `FastAPI`.
    -   Define Strategy Schemas (hardcoded for now, or loaded from file).
    -   Implement API: `GET /strategies` (returns list with JSON Schema for params).
    -   Create `ServiceSpec.md`.
-   [x] **Update `docker-compose.yml`**
    -   Add both services.
    -   Ensure network connectivity.

### Phase 2: Frontend Skeleton & Integration

-   [x] **Update `contracts/frontend`**
    -   Add `bot.schema.json` and `strategy.schema.json`.
-   [x] **Create `frontend/src/views/BotEditorView`**
    -   Setup basic directory structure (ServiceSpec, api client).
    -   Implement `loadBot(id)` and `saveBot(data)`.
    -   Create a basic layout with tabs or sections for the Pipeline steps.

### Phase 3: Pipeline UI Components (The "Editor")

Implement the UI sections one by one.

-   [ ] **Section 1: General & Exchange**
    -   Input: Name.
    -   Select: Exchange (fetch from `AuthService` mock or real).
    -   Select: Symbol (hardcoded list or fetch from `ExchangeAdapter`).
    -   Select: Mode (Backtest/Paper/Live).
-   [ ] **Section 2: Strategy Configuration (Dynamic)**
    -   Select: Strategy Template (fetch from `TradingStrategyViewService`).
    -   **Dynamic Form**: specific inputs based on the selected strategy's JSON schema.
-   [ ] **Section 3: Risk & Execution**
    -   Inputs for Allocation, Stop Loss, Order Type.
-   [ ] **Section 4: Summary & Validation**
    -   JSON view of the final config.
    -   "Save" button connecting to `BotService`.

---

## 3. Verification Plan

1.  **Backend Test**:
    -   `curl POST /bots` with a sample JSON. Check persistence.
    -   `curl GET /strategies` to ensure schemas are returned.
2.  **Frontend Test**:
    -   Open `BotEditorView`.
    -   Check if Strategy list loads.
    -   Select a strategy -> Form should appear.
    -   Fill form -> Click Save -> Check Console/Network for successful POST.

---

**Next Steps**: Start with Phase 1.
