# Orchestrator - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**: 
  - 사용자의 인터페이스 탐색(Navigation) 관리
  - 애플리케이션의 최상위 레이아웃(Sidebar, Header) 렌더링
  - 현재 활성화된 View Service(마이크로서비스)를 마운트 및 전환
  - 전역 상태(인증 여부, 현재 뷰 식별자)의 단일 진실 공급원(SSOT)

- **하지 않는 일**:
  - 개별 View 내부의 도메인 로직 처리 (예: 주문 입력 검증)
  - 개별 View의 데이터(호가창, 차트 등)를 직접 페칭하거나 가공
  - 복잡한 비즈니스 로직 수정

## 2. 외부 계약 (Contract)

### 2.1 State & Actions (Store)

- **State**:
  - `currentView`: `ViewId` ('dashboard' | 'market' | 'portfolio' | 'bot-config' | 'bot-editor' | 'bot-trades' | 'auth')
  - `isAuthenticated`: `boolean`
  - `editingBotId`: `string | null` (BotEditorView 진입 시 전달할 컨텍스트)

- **Actions**:
  - `setView(view: ViewId)`: 화면 전환
  - `setAuthenticated(auth: boolean)`: 인증 상태 변경

### 2.2 하위 View에 대한 Props 계약

Orchestrator는 각 View Service가 요구하는 **초기 Props**나 **이벤트 핸들러**를 주입하는 역할을 담당한다.
(현재는 정적 라우팅 위주이나, 추후 데이터 하이드레이션 역할이 추가될 수 있음)

- 공통: 특별한 공통 Props 없음. 각 View의 스키마에 따름.
- 예외: `BotConfigView`의 `onToggle` 등 오케스트레이션이 필요한 핸들러 주입.

## 3. 내부 개념 모델 (Domain Model)

- **ViewId**: 애플리케이션 내의 유효한 페이지 식별자 목록.

## 4. 주요 플로우 요약

### 4.1 뷰 전환 플로우
1. 사용자가 Sidebar의 메뉴 아이콘 클릭.
2. `setView(ViewId)` 액션 호출.
3. `store.currentView` 상태 업데이트.
4. `App.tsx`가 변경된 `currentView`를 감지하여 메인 영역의 컴포넌트 교체.
5. (Drill-down 예시) `BotConfig`에서 Edit 클릭 -> `setView('bot-editor')` 및 `editingBotId` 설정 -> 상세 편집 화면 렌더링.

### 4.2 인증 가드 플로우 (예정)
1. 앱 진입 시 `isAuthenticated` 확인.
2. `false`인 경우 강제로 `currentView`를 'auth'로 고정하거나 리다이렉트.

## 5. 변경 이력 (Change Log)

- 2025-12-16: 초기 정의 (Client-side Routing & Layout)
