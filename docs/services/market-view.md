# MarketViewService

- **책임**: 심볼 목록과 현재 선택, 오더북(매수/매도), 최근 테이프, 실시간 차트를 렌더링.
- **계약(입력 DTO)**: `contracts/frontend/market.schema.json` (symbols[], selectedSymbol, book{bids,asks,tape}, 선택적 차트 설정 + 봇 마커).
- **경계**: 읽기 전용; 주문 생성/취소 없음; 마켓 인입/DB에 직접 접근하지 않음.
- **상호작용**: `onSymbolChange(symbol)`을 View Orchestrator로 전달; 다른 크로스 서비스 호출 없음. 봇 마커는 렌더 전용(실행 이벤트 오버레이 대상).
- **테스트**: 계약 검증; 오더북/테이프 렌더 스냅샷; 선택 변경 콜백 호출 확인.
