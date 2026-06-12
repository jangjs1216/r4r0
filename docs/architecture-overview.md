# r4r0 아키텍처 개요 (Architecture Overview)

> 작성일: 2026-06-11 · 기준 브랜치: `impl-backtest`
> 상세 원칙은 [`bible.md`](../bible.md), 서비스별 계약은 각 디렉토리의 `ServiceSpec.md` 참조.

## 1. 한 줄 요약

웹 기반 24/7 자동화 크립토 트레이딩 시스템. **View 단위 프론트엔드 마이크로서비스 + 도메인별 백엔드 마이크로서비스** 구조이며, 모든 서비스 간 상호작용은 명시적 계약(JSON Schema / `ServiceSpec.md`)으로만 이뤄진다.

## 2. 서비스 토폴로지

```
┌─────────────────────────── Frontend (React, :80) ───────────────────────────┐
│  views/: dashboard · market · portfolio · bot-config · bot-editor           │
│          bot-trades · backtest · auth      (각 View = 독립 마이크로서비스)   │
│  orchestrator/: 네비게이션, 전역 상태, View 간 데이터 흐름 중개              │
└──────────┬───────────────────────────────────────────────────────────────────┘
           │ REST (contracts/frontend/*.schema.json)
┌──────────▼───────────────── Backend Services ────────────────────────────────┐
│                                                                              │
│  AuthService (:8000 내부)        API Key 암호화 저장소(Key Vault, SQLite)    │
│  ExchangeAdapter                 거래소(Binance) 통신 전담, Rate Limit 관리  │
│  BotService (:8001)              봇 Config/Status/Session CRUD (SSOT)        │
│  TradingStrategyView (:8002)     전략 템플릿 + 파라미터 JSON Schema 메타데이터│
│  ExecutionService                RUNNING 봇 감지 → 실매매 루프 워커          │
│    ├─ BotRunner                  봇별 격리 실행 (BOOTING→RUNNING→STOPPING)   │
│    ├─ strategies/                라이브 전략 (orderflow_exhaustion_v1 등)    │
│    └─ LedgerAwareAdapter         주문 Pending→Filled/Failed 추적 + 원장 기록 │
│  BacktestService (:8003)         과거 데이터 시뮬레이션                      │
│    ├─ domain/engine.py           SimulationEngine (체결/비용/펀딩비 시뮬)    │
│    ├─ domain/strategy.py         벡터화 전략 (SMA, RSI) + StrategyFactory    │
│    ├─ domain/analyzer.py         Sharpe/승률/Profit Factor 계산              │
│    └─ infra/data_loader.py       CCXT 기반 OHLCV 페이지네이션 수집           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
   스토리지: data/*.db (SQLite, 서비스별 분리) · 배포: docker-compose
```

## 3. 핵심 데이터 흐름

### 봇 생성
`BotConfigView` → (Orchestrator) → `BotEditorView` → `TradingStrategyView`에서 전략 스키마 로드 → 파이프라인 구성 → `BotService`에 저장.

### 라이브 실행
`BotService` 상태가 `RUNNING`으로 변경 → `ExecutionService`의 Scheduler가 감지 → `BotRunner.start()`:
1. **BOOTING**: 전략 로드 후 초기 틱을 원장 커밋([3/3] COMMIT)까지 완료해야 RUNNING 전이.
2. **루프**: 매 틱 `strategy.execute(context)` 호출. context = `{adapter(LedgerAware), bot_id, config}`. 전략이 직접 시세 조회·주문 실행.
3. **정지**: STOPPING → `on_stop()`(청산) → 세션 종료 → STOPPED.

### 백테스트
`fetch_historical_data`(CCXT OHLCV) → `StrategyFactory`가 bot_config에서 전략 생성 → `generate_signals(df)`로 시그널 시리즈(1/-1/0) 생성 → `SimulationEngine.run()`이 체결 시뮬(수수료 0.05%, 슬리피지 모델, 8시간 펀딩비) → Metrics(PnL, CAGR, MDD, Sharpe, 승률, Alpha/Cost 분리) 반환.

## 4. 전략(Strategy) 관련 현재 구조 — 리팩토링의 핵심 지점

전략 하나가 **세 곳에 분산**되어 있고 서로 계약이 느슨하다:

| 위치 | 역할 | 인터페이스 |
|---|---|---|
| `services/trading_strategy_view/main.py` | 전략 메타데이터·파라미터 JSON Schema (인메모리 하드코딩) | REST `/strategies` |
| `services/execution_service/strategies/` | 라이브 실행 로직 (이벤트 루프 기반, `execute(context)`) | 암묵적 duck-typing |
| `services/backtest_service/domain/strategy.py` | 백테스트 로직 (벡터화, `generate_signals(df)`) | `Strategy` ABC |

**문제점:**
- 같은 전략이라도 라이브 버전과 백테스트 버전을 따로 구현해야 함 → `orderflow_exhaustion_v1`은 라이브만 존재, SMA/RSI는 백테스트만 존재. **백테스트로 검증한 전략을 그대로 라이브에 올릴 수 없음.**
- 전략 파라미터 스키마(`trading_strategy_view`)와 실제 구현(`_Params` dataclass, `StrategyFactory`)이 수동 동기화 — 스키마 불일치 시 런타임에야 발견.
- `BotRunner._initialize_strategy()`가 if-else 하드코딩 → 전략 추가 시 엔진 코드 수정 필요.
- 백테스트 시그널 모델(1/-1/0, Long-only, 전량 매수/매도)이 단순해서 orderflow 같은 마이크로스트럭처 전략·부분 청산·TP/SL을 표현 못 함.

**리팩토링 방향 제안:**
1. **전략 패키지 단일화**: 전략 1개 = `(메타데이터 + 파라미터 스키마 + 시그널 로직)` 한 모듈. 데이터 접근을 `MarketDataProvider` 인터페이스로 추상화해 라이브(실시간 adapter)와 백테스트(historical replay)가 동일 전략 코드를 공유.
2. **레지스트리 패턴**: if-else/하드코딩 목록 대신 전략 자동 등록 → `trading_strategy_view`는 레지스트리에서 스키마를 동적 서빙.
3. **백테스트 엔진 확장**: 포지션 사이징, 부분 청산, TP/SL, 틱/오더북 레벨 시뮬레이션 지원 → orderflow 계열 전략도 백테스트 가능하게.

## 5. 기타 관찰 사항

- `data/temp_pnl_repo/`는 외부 PnL 계산 레포 임시 사본 — bible의 "임시 스크립트 관리" 원칙상 정리 대상.
- 루트의 `daily_aggTrades_head.csv`, `historical_aggTrades_head.csv`(빈 파일), `migrate_status_message.py`(bot_service 내 사본과 중복)도 정리 대상.
- 테스트는 `bot_service/tests`, `execution_service/tests` 일부만 존재. 백테스트 엔진(`SimulationEngine`)은 테스트 없음 — 수익 계산 검증이 안 된 상태로 전략 평가에 사용 중.

## 6. 리팩토링에 활용할 Claude Code 스킬

"유용한 전략 만들기"를 목표로 한 리팩토링 단계별 권장 스킬:

### 단계 1 — 컨텍스트 정비
| 스킬 | 용도 |
|---|---|
| `/init` | `CLAUDE.md` 생성. bible.md의 핵심 원칙(서비스 경계, 계약 우선, ServiceSpec 동기화)을 요약해 두면 이후 모든 AI 작업이 아키텍처 원칙을 자동으로 따름. |

### 단계 2 — 설계 및 구현
| 도구 | 용도 |
|---|---|
| **Plan 모드** (`Shift+Tab`) | 전략 인터페이스 통합(4절의 리팩토링 방향) 같은 구조 변경은 코드 수정 전 계획을 먼저 검토. 서비스 경계를 건드리는 작업에 특히 중요. |
| **Explore / Plan 서브에이전트** | 전략 코드가 3개 서비스에 분산되어 있어, 영향 범위 조사(예: "시그널 타입을 바꾸면 어디가 깨지나")를 위임하면 메인 컨텍스트를 아낄 수 있음. |

### 단계 3 — 품질 게이트 (수정 직후 매번)
| 스킬 | 용도 |
|---|---|
| `/code-review` | 커밋 전 정확성 버그 리뷰. **백테스트 엔진의 체결/비용 계산은 수치 버그가 곧 잘못된 전략 채택으로 이어지므로** `high` 이상 effort 권장. PR 단위 심층 리뷰는 `/code-review ultra <PR#>`. |
| `/simplify` | 리팩토링 후 중복·과잉 추상화 정리. 특히 전략 파라미터 파싱(`_Params` 수동 매핑 등) 같은 보일러플레이트 제거에 유효. |
| `/verify`, `/run` | docker-compose 스택을 실제로 띄워 봇 생성→실행→백테스트 플로우가 동작하는지 확인. 테스트 커버리지가 낮은 현재 상태에서 회귀 방지의 주 수단. |
| `/security-review` | API Key Vault(AuthService), 주문 실행 경로를 건드릴 때. 실제 자금이 걸린 코드이므로 머지 전 필수. |

### 단계 4 — 전략 개발 루프 자동화
| 스킬 | 용도 |
|---|---|
| **커스텀 스킬** (`.claude/skills/`) | "전략 추가" 워크플로(메타데이터 등록 → 라이브 구현 → 백테스트 구현 → 스키마 동기화 → 테스트)는 반복 절차이므로 프로젝트 스킬(예: `/new-strategy`)로 정의해 두면 누락 없이 일관되게 수행 가능. 백테스트 실행→리포트 해석도 `/backtest` 스킬 후보. |
| `/loop`, `/schedule` | 파라미터 스윕 백테스트를 반복 실행하거나, 야간 정기 백테스트 리포트 생성 같은 장기 실험 자동화. |

### 권장 작업 순서
1. `/init`으로 CLAUDE.md 생성 (bible 원칙 내장)
2. Plan 모드로 전략 인터페이스 통합 설계 → 구현
3. `SimulationEngine` 단위 테스트 추가 후 `/code-review high`
4. `/verify`로 전체 플로우 동작 확인
5. `/new-strategy` 커스텀 스킬 정의 → 전략 양산 체계 확립
