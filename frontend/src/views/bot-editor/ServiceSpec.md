# BotEditorViewService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**:
  - 트레이딩 봇의 로직을 **시각적 파이프라인(Visual Pipeline)** 형태로 구성.
  - 마이크로서비스 기반 전략 컴포넌트(Trigger, Filter, Risk, Action)들을 노드로 제공.
  - 노드 간의 데이터 흐름 및 논리적 연결(Edge) 관리.
  - 생성된 파이프라인(Execution Plan)을 JSON 형태로 검증 및 출력.

- **하지 않는 일**:
  - 봇 목록 관리 (BotConfigView 담당).
  - 개별 전략 알고리즘의 실제 실행 (Backend Microservices 담당).

## 2. 외부 계약 (Contract)

### 2.1 Inputs (Props/Store)

- **availableNodes**: 백엔드에서 제공되는 사용 가능한 전략 모듈 메타데이터.
  - `id`: 모듈 식별자 (예: `rsi-trigger`, `ema-filter`)
  - `type`: 노드 타입 (`TRIGGER`, `FILTER`, `RISK`, `ACTION`)
  - `inputSchema`: 이 노드가 받는 데이터 타입.
  - `paramSchema`: 사용자 설정 파라미터 스키마 (JSON Schema).
- **initialPipeline**: (Edit 모드 시) 기존 파이프라인 데이터.

### 2.2 Outputs (Events/Actions)

- **onSave(pipelineConfig)**:
  - `pipelineConfig`:
    ```json
    {
      "nodes": [
        { "id": "n1", "moduleId": "rsi-trigger", "params": { "period": 14, "threshold": 30 } },
        { "id": "n2", "moduleId": "market-buy", "params": {} }
      ],
      "edges": [
        { "source": "n1", "target": "n2" }
      ]
    }
    ```

## 3. 내부 개념 모델 (Domain Model)

- **Pipeline Node**: 전략의 최소 구성 단위. 하나의 독립된 마이크로서비스 기능에 대응됨.
- **Pipeline Edge**: 데이터 또는 제어 흐름의 이동 통로.
- **Micro-Kernel Strategy**: 전략은 더 이상 거대한 클래스가 아니라, 작은 파이프라인 노드들의 조합으로 정의됨.

## 4. 주요 플로우 요약

### 4.1 파이프라인 구성 플로우
1. 사용자가 Editor에 진입하면 사용 가능한 **노드 팔레트(Node Palette)** 로딩.
2. 'RSI Trigger' 노드를 캔버스에 드롭 -> `TriggerService` 마이크로서비스 사용 정의.
3. 'Stop Loss' 노드를 연결 -> `RiskService` 마이크로서비스 사용 정의.
4. 노드를 클릭하여 상세 파라미터(기간, 퍼센트 등) 설정.
5. 'Save' 클릭 시 노드 연결성(Connectivity) 검증 후 **파이프라인 JSON** 생성.
6. 오케스트레이터를 통해 백엔드로 전송.

## 5. 변경 이력 (Change Log)
- 2025-12-28: Pipeline Architecture 도입. 단순 폼 방식에서 **노드 기반 파이프라인 편집기**로 전환.
