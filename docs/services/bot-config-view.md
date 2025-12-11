# BotConfigViewService

- **책임**: 봇 정의, 상태, 배분, 거래소 선택, 토글 제공.
- **계약(입력 DTO)**: `contracts/frontend/bot-config.schema.json` (bots[]; `onToggle`/`onVenueChange`는 오케스트레이터가 주입).
- **경계**: 트레이드 실행/설정 쓰기를 직접 수행하지 않음; 모든 변경은 오케스트레이터/계약된 백엔드 엔드포인트를 통해 처리.
- **상호작용**: `onToggle(botId)`, `onVenueChange(botId, venue)`를 오케스트레이터로 전달; 그 외 크로스 서비스 접근 없음.
- **테스트**: 계약 검증; 토글/거래소 변경 핸들러 호출 확인; 봇 카드 스냅샷.
