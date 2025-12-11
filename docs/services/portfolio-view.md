# PortfolioViewService

- **책임**: 보유자산(진입/마크/PnL), 배분, 출금 윈도우 표시.
- **계약(입력 DTO)**: `contracts/frontend/portfolio.schema.json` (holdings[], allocations[], transfers[], selectedSymbol).
- **경계**: 읽기 전용; 잔고 변경/출금 없음; 포트폴리오 서비스 직접 호출 없음.
- **상호작용**: 오케스트레이터로부터 심볼 포커스를 받을 수 있으며, 외부로 명령을 내보내지 않음.
- **테스트**: 계약 검증; 테이블/카드 스냅샷; PnL 부호/포맷 확인.
