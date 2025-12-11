# ViewOrchestrator

- **책임**: View 서비스에 props를 전달하고 탭 상태를 관리하며, 뷰 간 이벤트(심볼 포커스, 봇 토글 등)를 중재.
- **계약**: `contracts/frontend/*.schema.json`에 정의된 DTO만 소비/생산; 서비스 계약에 따라 콜백(`onSymbolChange`, `onToggle`, `onVenueChange`)을 주입.
- **경계**: 비즈니스 규칙 없음; 계약된 백엔드 엔드포인트 호출 외 DB/API 직접 조작 금지; View 내부에 접근하지 않음.
- **상호작용**: View 서비스의 사용자 의도를 수신해 적절한 백엔드/오케스트레이터 계층으로 전달하고, 로컬 상태를 업데이트 후 재렌더링.
- **테스트**: 서비스별 props 배선 통합/스냅샷 테스트; 콜백 이벤트 디스패치 테스트.
