# BacktestView - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**: 봇 백테스팅 설정, 실행 트리거, 그리고 결과 리포트(차트 및 지표)를 시각화하는 뷰.
- **책임**:
  - 백테스트 기간, 초기 자본 등 파라미터 입력 폼 제공.
  - 백엔드(`BacktestService`)에 실행 요청.
  - 결과 데이터(Equity Curve, KPI, Cost Breakdown)를 시각화.
  - 3가지 Bento Grid 디자인 옵션 제공 (사용자 선택 가능).

## 2. 외부 계약 (Contract)

### 2.1 View Props (Inputs)
- **`botId`** (Optional): 특정 봇의 컨텍스트에서 진입 시 해당 봇 ID. 없으면 빈 폼.
- **`initialConfig`** (Optional): 봇 에디터에서 넘어온 임시 설정값 (아직 저장 안 된 상태).

### 2.2 View Events (Outputs)
- **`onClose`**: 뷰 닫기 또는 에디터로 복귀.

## 3. 내부 개념 모델 (Domain Model)

### 3.1 BacktestResult (백테스트 결과)
```typescript
interface BacktestResult {
  jobId: string;
  metrics: {
    totalPnl: number;      // 누적 손익
    cagr: number;          // 연평균 성장률
    mdd: number;           // 최대 낙폭
    sharpeRatio: number;   // 샤프 지수
    winRate: number;       // 승률
    profitFactor: number;  // 수익 팩터
    alpha: number;         // 순수 알파 (Gross Alpha)
    totalCost: number;     // 총 비용 (Cost Drag)
  };
  equityCurve: {
    time: string;
    value: number;
    buyHoldValue?: number; // 벤치마크
  }[];
  costBreakdown: {
    spread: number;
    slippage: number;
    fees: number;
    funding: number;
  };
  trades: TradeHistory[];  // 매매 상세 내역
}
```

## 4. 주요 플로우 (Key Flows)

1. **설정 및 실행**:
   - 사용자가 기간(Start/End), 자본금 입력.
   - [Run Backtest] 클릭 -> `BacktestService.run(config)` 호출.
   - 로딩 상태(Loading Spinner) 표시.

2. **결과 표시**:
   - 백엔드에서 `BacktestResult` 수신.
   - 선택된 Layout Option (V1/V2/V3)에 따라 결과 렌더링.

3. **디자인 스위칭**:
   - 상단 툴바에서 [V1:Chart] / [V2:KPI] / [V3:Balanced] 버튼으로 레이아웃 즉시 변경.
