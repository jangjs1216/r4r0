# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

웹 기반 24/7 자동화 크립토 트레이딩 시스템. **`bible.md`가 이 레포의 절대 규칙이며, 모든 변경 전에 해당 서비스의 `ServiceSpec.md`를 먼저 읽어야 한다.** 아키텍처 요약은 `docs/architecture-overview.md` 참조.

## 명령어

### 전체 스택 (Docker)
```bash
export MASTER_KEY="dev_master_key_1234567890"
docker-compose up --build        # 또는 ./start_dev.sh
```
- Web UI: http://localhost (Nginx가 `/api/*`를 백엔드로 라우팅)
- 노출 포트: bot-service :8001, trading-strategy-view :8002, backtest-service :8003

### 프론트엔드 (frontend/)
```bash
npm run dev      # Vite dev server (:5173) — CORS 직접 호출 모드
npm run lint     # ESLint
npm run build    # tsc -b && vite build
```

### 백엔드 서비스 개별 실행
각 서비스는 독립 FastAPI 앱. 해당 디렉토리에서:
```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# auth는 MASTER_KEY 환경변수 필요
```

### 테스트 (pytest)
테스트 import 경로가 서비스마다 다르므로 실행 위치에 주의:
```bash
# bot_service: sys.path 조작으로 main을 직접 import → 서비스 디렉토리에서 실행
cd services/bot_service && pytest tests/

# execution_service: 패키지 경로(services.execution_service.*)로 import → 레포 루트에서 실행
pytest services/execution_service/tests/

# 단일 테스트
pytest services/bot_service/tests/test_session.py -k "test_name"
```

## 아키텍처 핵심

### 마이크로서비스 경계 (bible.md의 절대 원칙)
- **각 View = 독립 마이크로서비스** (`frontend/src/views/*`), View 간 조합은 `frontend/src/orchestrator/`만 담당.
- 서비스 간 통신은 **계약(API/이벤트)으로만**. 다른 서비스의 DB(`data/*.db`)·내부 구현 직접 접근 금지.
- 백엔드: `services/auth` (API Key 암호화 저장소) → `services/exchange_adapter` (거래소 통신 전담) → `services/bot_service` (봇 Config/Status/Session SSOT) → `services/execution_service` (RUNNING 봇 감지 후 매매 루프 워커) / `services/backtest_service` (과거 데이터 시뮬레이션) / `services/trading_strategy_view` (전략 메타데이터·파라미터 JSON Schema).
- 계약 스키마: `contracts/frontend/*.schema.json`, `contracts/backend/*.yaml`.

### 전략 코드는 3곳에 분산되어 있다 (수정 시 동기화 필수)
1. `services/trading_strategy_view/main.py` — 전략 ID·파라미터 JSON Schema (인메모리 목록)
2. `services/execution_service/strategies/` — 라이브 실행 로직 (`execute(context)` duck-typing, `engine.py`의 `_initialize_strategy()`에서 ID로 분기)
3. `services/backtest_service/domain/strategy.py` — 백테스트 벡터화 로직 (`generate_signals(df)` → 1/-1/0 시리즈, `StrategyFactory`에서 분기)

전략을 추가/수정하면 세 곳의 ID·파라미터 키가 정확히 일치해야 한다.

### 봇 실행 상태 머신 (ExecutionService)
`BOOTING → RUNNING → STOPPING → STOPPED`. BOOTING에서 첫 틱이 원장 커밋까지 완료되어야 RUNNING 전이. 상태의 SSOT는 BotService이며, `LedgerAwareAdapter`가 주문을 Pending → Filled/Failed로 추적해 원장에 기록한다.

## 작업 규칙 (bible.md / .cursorrules 요약)

1. **ServiceSpec 우선**: 수정 전 해당 서비스 `ServiceSpec.md`를 읽고, 계약/플로우 변경 시 Spec을 먼저 갱신한 뒤 코드를 맞춘다. 코드 변경 후 Spec 동기화 필수.
2. **한 번에 하나의 서비스만** 크게 변경한다. 변경 범위(파일/라인)는 최소화하고, 리팩터링은 기능 추가와 분리한다.
3. **Naming Golden Rule — No Aliases**: Pydantic `Field(alias=...)` 금지. 내부 변수명 = DB 컬럼명 = JSON Key = Frontend 인터페이스 필드명을 철자까지 일치시킨다.
4. **레이어 구조**: API → Application → Domain → Infra (backtest_service가 표준 예시). `*Manager`/`*Helper`/`*Util` 남발 금지.
5. **주석·Docstring은 한국어**로 작성한다.
6. **임시 스크립트는 즉시 정리**: 마이그레이션 스크립트는 완료 후 삭제/아카이브, 검증 스크립트는 정식 `tests/`로 승격.
7. **의존성 버전 고정**: `requirements.txt`/`package.json`에 명시적 버전, 서비스 간 동일 라이브러리는 동일 버전.
