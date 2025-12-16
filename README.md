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

### 3. Backend Domain Services (개념적)
- **StrategyEngine**: 플러그인 방식의 전략 실행기. `BotEditor`에 전략 스키마(Schema)를 제공.
- **TradeExecution**: 거래소 주문 집행 및 관리.
- **MarketData**: 실시간 데이터 스트리밍.
- **Persistence**: 봇 설정 및 이력 저장 (DB).

## Contracts & Docs

- **ServiceSpec.md**: 각 마이크로서비스 폴더 내에 위치. **AI와 사람 모두를 위한 기준 진실(SSOT).**
- **Contracts**: `contracts/frontend/*.schema.json`. JSON Schema 기반의 엄격한 데이터 타이핑.

## 데이터 흐름 예시 (Bot Creation Flow)

1. **User**가 `BotConfigView`에서 `Create` 클릭.
2. **Orchestrator**가 `BotEditorView`로 전환 (`mode='create'`).
3. **BotEditorView**는 사용 가능한 전략(`Grid`, `RSI`, `Vwap` 등) 목록과 각 전략의 파라미터 스키마를 로드.
4. User가 `Grid Strategy` 선택 -> **BotEditorView**가 격자 간격, 상/하단 가격 입력 폼을 동적으로 렌더링.
5. User 저장 -> `onSave` 이벤트 발생 -> **Backend**로 설정 전송 -> **BotConfigView**로 복귀.

## 시작하기

- **Frontend**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
- **Directory Structure**:
  - `frontend/src/views/*`: 각 뷰 서비스 (소스 + ServiceSpec + MockData)
  - `frontend/src/orchestrator/*`: 오케스트레이터
  - `contracts/*`: 공유 계약 스키마

## 개발 원칙 (Bible 요약)

1. **마이크로서비스**: 뷰 단위 격리.
2. **계약 우선**: 스키마와 `ServiceSpec.md`가 코드보다 먼저다.
3. **문서 동기화**: 코드가 바뀌면 스펙도 바뀐다.
