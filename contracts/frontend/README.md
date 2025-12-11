# 프런트엔드 View 계약

각 View 서비스는 JSON Schema로 정의된 타입이 있는 props DTO를 소비합니다. 스키마는 고정 계약이며 브레이킹 체인지는 새 버전 파일(예: `summary.v2.schema.json`)과 오케스트레이션 업데이트가 필요합니다.

- `summary.schema.json` — 마이크로서비스 요약(상태/지연/에러율/계약) + 히어로 영역 트레이드 KPI  
- `overview.schema.json` — 호환성을 위한 기존 요약 스키마  
- `bot-trades.schema.json` — 실행된 봇 트레이드와 집계 통계(승/패/PnL/지연)  
- `dashboard.schema.json` — 잔고, 포지션, 포커스 포지션 스냅샷  
- `market.schema.json` — 심볼 목록, 선택 심볼, 오더북/테이프; 선택적 차트 설정(TradingView/로컬)과 봇 마커 오버레이  
- `portfolio.schema.json` — 보유자산, 배분, 출금 윈도우  
- `bot-config.schema.json` — 봇 정의와 거래소(venue)  
- `auth.schema.json` — 세션 상태, MFA/키 플래그, 사용자 정보, UI 컨트롤 목록  

직렬화되지 않는 핸들러(콜백)는 View Orchestrator가 주입합니다:

- `market`: `onSymbolChange(symbol)`로 포커스 심볼 변경 전달
- `bot-config`: `onToggle(botId)`, `onVenueChange(botId, venue)`

크로스-뷰 플로우는 오케스트레이터 이벤트로만 제한됩니다: 마켓 심볼 변경은 Dashboard/Portfolio로 전달되고, 봇 액션은 bot-config 서비스 내부에 머물며, 필요 시 오케스트레이터가 실행 서비스로 브리징합니다. `BotTradesViewService`는 읽기 전용(결과 리포트)이며 실행 상태를 변경하지 않습니다.
