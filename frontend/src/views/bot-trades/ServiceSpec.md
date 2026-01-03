- **역할**:
  - **Session-based Analysis**: 봇 실행 주기(Session)별 성과(PnL, 승률)를 카드 형태로 요약 제공.
  - **Trade History Drill-down**: 특정 세션을 클릭하면 해당 세션의 상세 매매 이력 조회.
  - **Live PnL**: 실행 중인 세션의 실시간 손익 모니터링.

- **하지 않는 일**:
  - 실시간 호가/차트 모니터링 (MarketView 담당)
  - 봇 설정 변경 (BotConfigView 담당)

## 2. 외부 계약 (Contract)

### 2.1 Backend APIs

- `GET /bots/{bot_id}/sessions`: 세션 목록 조회 (Master View)
- `GET /sessions/{session_id}`: 특정 세션의 매매 내역 조회 (Detail View)

## 3. 내부 개념 모델 (Domain Model)

- **BotSession**: Start -> Stop 사이의 실행 단위.
  - `status`: ACTIVE | ENDED
  - `summary`: { totalPnl, winRate, ... }
- **TradeExecution**: 매매 체결 건.

## 4. 주요 플로우 요약

### 4.1 Master-Detail 탐색
1. **세션 목록**: 사용자가 봇을 선택하면, 최근 실행 세션 리스트가 카드 형태로 표시됨. (Active 세션은 최상단 강조)
2. **세션 상세**: 카드를 클릭하면 우측(또는 하단) 패널에 해당 세션의 매매 로그 테이블이 로드됨.
3. **실시간 업데이트**: Active 세션의 PnL 숫자는 주기적으로(또는 이벤트 수신으로) 갱신됨.

## 5. 변경 이력 (Change Log)

- 2025-12-16: 초기 정의 (`contracts/frontend/bot-trades.schema.json` 기반)
