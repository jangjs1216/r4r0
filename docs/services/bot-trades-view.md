# BotTradesViewService

- **책임**: 실행된 봇 트레이드(봇, 방향, 진입/청산, PnL, 지연, 시간)와 집계 KPI(승/패/총 PnL/평균 지연) 표시.
- **계약(입력 DTO)**: `contracts/frontend/bot-trades.schema.json` (trades[], summary).
- **경계**: 읽기 전용 리포팅; 트레이드 실행/변경 없음; 전략/실행 서비스를 직접 접근하지 않음.
- **상호작용**: 탭 선택은 View Orchestrator가 처리; 추후 추가 시 필터/정렬 의도를 오케스트레이터로 전달 가능.
- **테스트**: 계약 검증; 테이블 렌더 스냅샷; PnL 부호/포맷 확인.
