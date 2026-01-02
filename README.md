# r4r0: 24/7 자동화 크립토 트레이딩 (Web)

이 저장소는 웹 기반 완전 자동화 크립토 트레이딩 제품의 기반을 다룹니다. 아키텍처는 `bible.md`를 따릅니다: 각 View는 독립 마이크로서비스이고, 오케스트레이션은 별도 서비스이며, 모든 상호작용은 명시적 계약(DTO/이벤트/`ServiceSpec.md`)으로만 이뤄집니다. 어떤 서비스도 다른 서비스의 스토리지나 내부 구현에 직접 접근하지 않습니다.

## 서비스 토폴로지 (Service Topology)

### 1. Web View Services (Frontend Microservices)
각 뷰는 독립적인 책임과 계약을 가집니다. 상세 내용은 각 디렉토리의 `ServiceSpec.md`를 참조하세요.

- **DashboardViewService**: 전체 계정 흐름, 자산 요약, 퀵 포지션 뷰.
- **MarketViewService**: 실시간 호가(Orderbook), 차트(Candles), 봇 매커 오버레이.
- **PortfolioViewService**: 상세 자산 배분(Allocation) 및 포지션 분석.
- **BotConfigViewService**: 봇 인스턴스 목록 관리, Start/Stop 제어, 성과 요약 카드.
- **BotEditorViewService**: **(New)** 봇 상세 설정, 전략 선택 및 전략별 동적 파라미터(Dynamic Params) 편집.
- **BotTradesViewService**: 봇 실행 이력 및 성과(PnL, Latency) 통계.
- `AuthViewService`: API 키 관리 UI (Key Management Only)** 로그인 과정 없이 바로 접근. Binance, Upbit 등 다중 거래소 API Key의 등록/삭제/권한 관리 담당. 봇이 사용할 '지갑/연결'을 관리하는 곳.

### 2. Orchestrators
- **ViewOrchestrator**: `frontend/src/orchestrator/`. 
  - 앱의 네비게이션, 전역 상태(Auth, Routing) 관리.
  - 마이크로서비스(View) 간의 데이터 흐름 중개 (예: ConfigList -> Editor 전환).
  - 계약: `ServiceSpec.md` & `store.ts`.
- `TradeFlowOrchestrator`: 포트폴리오 스냅샷 → 전략 시그널 → 실행 → 알림을 순차/조건 제어

### 3. Backend Domain Services  
  - `AuthService`: **(Key Vault)** API Key의 안전한 암호화 저장소. 코드나 Config 파일이 아닌 로컬 DB(`data/*.db`)에 암호화해 저장하며, 다른 서비스에 서명 기능을 제공하거나 제한적으로 키를 불출함.
  - `ExchangeAdapterService`: 거래소(Binance 등) API 통신 전담. `AuthService`에서 키를 받아 잔고 조회, 주문 실행 등을 수행하며 Rate Limit을 관리함.
  - `BotService`: 봇 인스턴스의 설정(Config), 상태(Status), 생명주기(Lifecycle)를 관리하는 CRUD 서비스. 파이프라인(Pipeline) 구조의 설정을 저장.
  - `TradingStrategyViewService`: 사용 가능한 전략(Template) 목록과 각 전략의 파라미터 스키마(JSON Schema)를 제공하는 메타데이터 서비스.
  - `ExecutionService`: **(Core Engine)** 'RUNNING' 상태인 봇을 감지하여 실제 매매 루프(Loop)를 실행하는 워커 서비스.
    - **BotRunner**: 개별 봇의 격리된 실행 환경.
    - **LedgerAwareAdapter**: 주문 실행 전후의 상태(Pending -> Filled/Failed)를 추적하고 원장에 기록.
    - **Scheduler**: 주기적인 폴링 및 봇 상태 동기화.
  
  *(Note: `StrategyEngine` 및 `TradeExecution` 기능은 현재 `ExecutionService` 내에 통합 구현됨)*

## Contracts & Docs

- **ServiceSpec.md**: 각 마이크로서비스 폴더 내에 위치. **AI와 사람 모두를 위한 기준 진실(SSOT).**
- **Contracts**: `contracts/frontend/*.schema.json`. JSON Schema 기반의 엄격한 데이터 타이핑.

## 데이터 흐름 예시 (Bot Creation Flow)

1. **User**가 `BotConfigView`에서 `Create` 클릭.
2. **Orchestrator**가 `BotEditorView`로 전환 (`mode='create'`).
3. **BotEditorView**는 `TradingStrategyViewService`로부터 전략 템플릿 로드.
4. **User**가 파이프라인 구성 (Data Source -> Trigger -> Risk -> Action).
5. User 저장 -> `onSave` 이벤트 발생 -> **Backend(BotService)**로 설정 전송 -> **BotConfigView**로 복귀.

## 데이터 흐름 예시 (Bot Execution Flow - Mock Trading)

1. **Start Bot**: `BotService` 상태 `RUNNING` 변경.
2. **ExecutionService**: 봇 감지 및 `TestTradingStrategy` 로드 (검증용 모의 매매 전략).
3. **Loop Execution**:
   - `ExchangeAdapter`로부터 잔고 및 시세 조회.
   - `TestTradingStrategy`: 조건 충족 시(예: Loop 시작) 매수 시그널 발생.
   - `LedgerAwareAdapter`: 로컬 주문 생성(Pending) -> `ExchangeAdapter` 주문 전송 -> 결과에 따라 상태 업데이트(Filled/Failed).
4. **Result**: `BotService` 및 `Frontend`에서 실시간 상태 및 거래 로그 확인 가능.
## 🚀 Running the Project

Detailed instructions for Local Development and Docker Deployment can be found in [docs/deployment.md](./docs/deployment.md).

### Quick Start (Docker)
```bash
export MASTER_KEY="my_secret"
docker-compose up --build
```


- **Directory Structure**:
  - `frontend/src/views/*`: 각 뷰 서비스 (소스 + ServiceSpec + MockData)
  - `frontend/src/orchestrator/*`: 오케스트레이터
  - `contracts/*`: 공유 계약 스키마

75: ## 개발 원칙 (Bible 요약)
76: 
77: 1. **마이크로서비스**: 뷰 단위 격리.
78: 2. **계약 우선**: 스키마와 `ServiceSpec.md`가 코드보다 먼저다.
79: 3. **문서 동기화**: 코드가 바뀌면 스펙도 바뀐다.
80: 4. **임시 스크립트 관리**: 목적 달성 후 즉시 삭제 또는 정규화.
