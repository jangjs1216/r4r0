# SummaryViewService

- **책임**: 각 View 서비스의 헬스/지연/에러/계약 정보를 요약하고, 봇 트레이드 KPI를 표시.
- **계약(입력 DTO)**: `contracts/frontend/summary.schema.json` (services[], tradesSummary).
- **경계**: 읽기 전용; 타 서비스 상태를 변경하지 않으며 오케스트레이터가 전달한 DTO만 사용.
- **상호작용**: 탭 선택 의도를 View Orchestrator에 전달; 다른 서비스를 직접 호출하지 않음.
- **테스트**: 요약 레이아웃 스냅샷; `summary.schema.json` 계약 검증.
