# BotEditorView - Service Spec

## 1. 역할과 책임
- **역할**: 봇 파이프라인(설정)을 시각적으로 편집하고 저장하는 UI 뷰.
- **책임**:
  - `TradingStrategyViewService`에서 전략 목록(Schema)을 로드.
  - JSON Schema Form을 통해 전략별 동적 파라미터 입력 UI 렌더링.
  - `BotService`의 API를 호출하여 봇 설정을 저장/수정.
  - Pipeline의 각 단계(Exchange -> Strategy -> Risk -> Execution)를 탭이나 스텝으로 구성.

## 2. 외부 계약 (Frontend API Clients)

### 2.1 BotService Client
- `GET /bots/{id}`: 봇 로드 (수정 모드 시)
- `POST /bots`: 신규 봇 저장
- `PUT /bots/{id}`: 봇 수정

### 2.2 StrategyService Client
- `GET /strategies`: 가용 전략 및 스키마 목록 로드

## 3. 내부 상태 모델 (React State)

```typescript
interface BotEditorState {
  isLoading: boolean;
  mode: 'create' | 'edit';
  strategies: StrategyDefinition[]; // Loaded from backend
  formData: BotConfig; // The full config object being edited
}
```

## 4. 주요 플로우
1. 뷰 진입 (`/bots/new` or `/bots/:id/edit`)
2. `useEffect` -> `StrategyService.getStrategies()` 호출 -> 전략 목록 State 저장.
3. (Edit 모드라면) `BotService.getBot(id)` 호출 -> `formData` 초기화.
4. 사용자가 전략 템플릿 선택 -> `strategies`에서 해당 `schema` 조회 -> 동적 폼 생성.
5. Save 버튼 클릭 -> 유효성 검사 -> `BotService.saveBot(formData)` 호출.
