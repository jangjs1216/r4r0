# r4r0: 24/7 자동화 크립토 트레이딩 (Web)

이 저장소는 웹 기반 완전 자동화 크립토 트레이딩 제품의 기반을 다룹니다. 아키텍처는 `bible.md`를 따릅니다: 각 View는 독립 마이크로서비스이고, 오케스트레이션은 별도 서비스이며, 모든 상호작용은 명시적 계약(DTO/이벤트)으로만 이뤄집니다. 어떤 서비스도 다른 서비스의 스토리지나 내부 구현에 직접 접근하지 않습니다.

## 서비스 토폴로지 (초안)
- **Web View Services (프런트엔드)**  
  - `DashboardViewService`: 잔고, 오픈 포지션, PnL 타임라인  
  - `BotConfigViewService`: 봇 설정 생성/수정, 스케줄, 리스크 토글, 전략 선택(플러그형 전략 마이크로서비스와 계약으로 연결)  
  - `MarketViewService`: 호가/프라이스 스트림 슬라이스, 심볼 선택  
  - `PortfolioViewService`: 보유자산, 배분, 펀딩, 출금  
  - `AuthViewService`: 로그인/가입, MFA, 키 관리 UI  
  각 View는 타입이 있는 props/DTO만 노출하며 백엔드 서비스의 공개 API만 호출합니다.
- **Orchestrators**  
  - `TradeFlowOrchestrator`: auth → 포트폴리오 스냅샷 → 전략 시그널 → 실행 → 알림을 순차/조건 제어하며 플로우 외 도메인 규칙은 소유하지 않음  
  - `ViewOrchestrator`: 계약만으로 뷰 간 데이터 연결(예: 마켓 심볼 선택 → 대시보드/포트폴리오로 전달)
- **Backend Domain Services**  
  - `AuthService`(유저, API 키, MFA), `PortfolioService`(잔고, 포지션, PnL), `StrategyEngineService`(플러그형 전략 계약; 각 전략은 신호/백테스트 엔드포인트를 가진 독립 마이크로서비스 가능), `TradeExecutionService`(주문 라우팅, 슬리피지/수수료 계산) + **ExchangeAdapterService**(Binance 우선, 인터페이스로 거래소 교체/추가 가능), `MarketDataIngestService`(틱/캔들/WS 인입), `NotificationService`(이메일/푸시/웹훅).
- **Data & Persistence Services**  
  - `DatabaseService`: 봇 설정, 실행 로그, API 키 메타, 감사 로그 스키마를 소유. 모든 View/Domain 서비스에 읽기/쓰기 계약을 제공하며 직접 스토리지 접근은 불가.  
  - `BotConfigService`: 설정과 로컬 실행 기록을 `DatabaseService`에 저장/조회. Binance 주문은 반드시 `TradeExecutionService` + `ExchangeAdapterService`를 거치며 View에서 직접 호출하지 않음.

## Contracts & Data Flows
- REST/JSON으로 명령/조회, WebSocket으로 가격/포지션 업데이트 스트림.  
- 예시 DTO: `POST /strategy/signals` `{ symbol, side, size, confidence, ts }`; `GET /portfolio/positions` → `[ { symbol, qty, entryPx, liqPx, pnl, ts } ]`  
- 브레이킹 체인지는 새 버전 필요(예: `/v2/positions`); 기존 스키마 변형 지양.  
- 거래소 어댑터 계약: `POST /exchange/place-order` `{ venue, symbol, side, type, qty, price?, clientId }` (거래소 독립 응답). 어댑터가 Binance 인증/레이트리밋 처리하며 다른 거래소(`venue=okx` 등)로 교체/추가 가능.

## Repo Layout (제안)
- `frontend/` (뷰별 마이크로 프런트엔드; 디자인 토큰만 공유)  
- `orchestrators/` (TradeFlow, View orchestrators)  
- `services/` (`auth`, `portfolio`, `strategy` + 전략별 마이크로서비스 옵션, `exchange-adapter` Binance 우선 멀티베뉴, `execution`, `market-data`, `notification`)  
- `contracts/` (OpenAPI/JSON Schema, 이벤트 스펙), `infra/` (IaC, DB 마이그레이션), `tests/` (계약 + 통합)

## 프런트엔드 UI (현재 스켈레톤)
- 랜딩 영역: 전용 **SummaryViewService**(마이크로서비스 요약/지연/계약 + 봇 트레이드 KPI).  
- **좌측 사이드바 탭**으로 각 마이크로서비스 또는 핵심 `Bot Trades` 뷰 이동; 탭 선택 시 오른쪽에 해당 뷰만 렌더.  
- **Bot trade history**: 트레이드 테이블(봇, 방향, 진입/청산, PnL, 지연, 시간) + 승/패/PnL 집계.  
- View 서비스는 격리되며, **View Orchestrator**(`frontend/orchestrator/main.js`)가 계약에 정의된 props/핸들러만 주입.

## 시작하기 (프런트엔드 스켈레톤)
- 뷰 계약: `contracts/frontend/*.schema.json`, 설명은 `contracts/frontend/README.md`에 정리(`summary.schema.json`, `bot-trades.schema.json`, 기존 뷰 스키마 포함).  
- UI 마이크로서비스: `frontend/views/*`; 오케스트레이터: `frontend/orchestrator/main.js`; 스타일 토큰: `frontend/styles/main.css`.  
- 로컬 실행: `cd frontend && python -m http.server 4173` → `http://localhost:4173` 접속.  
- 한 변경 = 한 서비스; 계약 우선/단일 서비스 수정 원칙(`bible.md`) 준수.

## Dev & Ops Notes
- 계약 우선: JSON Schema/OpenAPI + 이벤트 토픽을 먼저 정의.  
- 한 번에 하나의 서비스만 수정; 서비스 경계 넘는 PR 금지.  
- 테스트: 서비스별 계약 테스트; 오케스트레이터 통합/스냅샷; 뷰별 UI 스냅샷/E2E.  
- 시크릿(API 키 등)은 커밋 금지, 환경/시크릿 매니저 사용.  
- 거래소 샌드박스 키/레이트리밋 고려; 실행 멱등/재시도는 Execution 서비스에서 처리하고 오케스트레이터는 직접 재시도하지 않음.  
- DB 접근은 반드시 `DatabaseService` 계약 경유; View/Domain 서비스는 스토리지에 직접 접근 불가. BotConfig 기록(설정/주문 로그)은 `BotConfigService` → `DatabaseService`로 흐름을 강제.
