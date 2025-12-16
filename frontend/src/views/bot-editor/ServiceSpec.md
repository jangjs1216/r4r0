# BotEditorViewService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**:
  - 단일 트레이딩 봇의 상세 설정(Configuration) 편집.
  - 전략 알고리즘 선택 및 **동적 파라미터 폼(Dynamic Form)** 제공.
  - 적용 대상 심볼(종목) 및 자산 배분(Allocation) 설정.
  - 새 봇 생성(`create`) 및 기존 봇 수정(`edit`) 모드 지원.

- **하지 않는 일**:
  - 봇 목록 조회 및 상태 토글 (BotConfigViewService 담당).
  - 봇의 실행/중지 실제 처리 (백엔드 요청은 Orchestrator나 Handler를 통해 전달).

## 2. 외부 계약 (Contract)

### 2.1 Props (입력)

참조: `contracts/frontend/bot-editor.schema.json`

- **mode**: 'create' | 'edit'
- **targetBot**: (Edit 모드 시) 수정할 봇의 기존 설정 데이터.
  - `parameters`: 전략별 특화된 설정값 (JSON).
- **strategies**: 선택 가능한 전략 메타데이터 목록.
  - `parameterSchema`: 각 전략이 요구하는 파라미터의 JSON Schema (동적 폼 생성용).
- **symbols**: 거래 가능한 심볼 목록.

### 2.2 Events (출력)

- **onSave(botConfig)**: 설정 저장 요청.
- **onCancel()**: 편집 취소 및 목록으로 복귀 요청.

## 3. 내부 개념 모델 (Domain Model)

- **StrategyDefinition**: 전략의 ID, 이름, 그리고 **파라미터 스펙(Schema)**을 포함하는 메타데이터.
- **BotParameterForm**: 선택된 전략의 Schema에 따라 동적으로 렌더링되는 입력 폼 상태.

## 4. 주요 플로우 요약

### 4.1 봇 생성/수정
1. 사용자가 BotConfigView에서 'Create' 또는 'Edit' 버튼 클릭.
2. Orchestrator가 `BotEditorView`로 화면 전환 및 필요 데이터(전략 목록, 타겟 봇 등) 주입.
3. 사용자가 **전략(Strategy)**을 선택.
4. View는 선택된 전략의 `parameterSchema`를 읽어 해당 전략에 맞는 **입력 폼(Input Fields)**을 동적으로 렌더링.
   - 예: 'Grid Strategy' 선택 시 -> Grid Level, Upper/Lower Price 입력창 표시.
   - 예: 'RSI Strategy' 선택 시 -> Period, Overbought/Oversold Threshold 입력창 표시.
5. 사용자가 종목(Symbol) 및 자산 배분 설정.
6. 'Save' 클릭 시 `onSave` 이벤트 발생 -> Orchestrator가 저장 로직 수행 후 `BotConfigView`로 복귀.

## 5. 변경 이력 (Change Log)

- 2025-12-16: 초기 정의. 봇 설정의 복잡성을 고려하여 `BotConfigView`에서 분리(**독립 마이크로서비스화**).
