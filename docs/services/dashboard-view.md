# DashboardViewService

- **책임**: 잔고, 오픈 포지션, 포커스 포지션 스냅샷, 상위 PnL 메트릭을 표시.
- **계약(입력 DTO)**: `contracts/frontend/dashboard.schema.json` (balances, positions[], focusPosition?, timestamp).
- **경계**: 오케스트레이션/크로스 서비스 호출 없음; DTO 소비만 수행하며 포지션을 변경하지 않음.
- **상호작용**: View Orchestrator로부터 심볼 포커스 이벤트를 받을 수 있으며, 명령은 발행하지 않음.
- **테스트**: 계약 검증; 포지션 리스트/포커스 카드 스냅샷; PnL 부호/포맷 확인.
