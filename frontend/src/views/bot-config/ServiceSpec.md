# BotConfigViewService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**:
  - 트레이딩 봇의 목록 조회 및 상태 모니터링
  - 봇의 실행 상태(Running/Paused) 토글 제어
  - 새로운 봇 생성/수정 화면으로의 진입점 제공

- **하지 않는 일**:
  - 봇의 상세 전략 파라미터 편집 (BotEditorViewService로 분리됨)
  - 봇의 실제 매매 로직 실행 (백엔드 엔진 담당)
  - 실시간 매매 로그의 상세 모니터링 (BotTradesView 담당)

## 2. 외부 계약 (Contract)

### 2.1 Props (입력)

참조: `contracts/frontend/bot-config.schema.json`

- **bots**: 봇 설정 객체 배열
  - `id`, `name`, `strategy`
  - `status`: "running" | "paused"
  - `allocation`, `risk`, `schedule`
  - `venue`: 연결된 거래소 어댑터 ID
- **onToggle**: 봇 상태 변경 핸들러
- **onEdit**: 봇 수정 화면 진입 핸들러
- **onCreate**: 봇 생성 화면 진입 핸들러
- **onVenueChange**: 거래소 변경 핸들러

## 3. 내부 개념 모델 (Domain Model)

- **BotConfiguration**: 하나의 독립된 트레이딩 봇 인스턴스 설정. 전략과 리스크 파라미터를 포함.
- **StrategyParams**: 전략별로 상이한 세부 파라미터.

## 4. 주요 플로우 요약

### 4.1 봇 관리
1. 등록된 봇 목록 카드/리스트 조회.
2. 특정 봇의 'Start/Stop' 토글 스위치 조작 -> `onToggle` 호출.
3. 'Create' 또는 'Edit' 버튼 클릭 -> `onCreate`/`onEdit` 호출 -> Orchestrator가 **BotEditorView**로 화면 전환.

## 5. 변경 이력 (Change Log)

- 2025-12-16: 초기 정의 (`contracts/frontend/bot-config.schema.json` 기반)
