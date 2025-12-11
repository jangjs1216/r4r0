# DatabaseService

- **책임**: 봇 설정, 거래소 API 키 메타데이터, 실행/감사 로그, 뷰용 집계 데이터를 보관. 도메인 서비스에 CRUD/조회 계약을 제공하며, View가 테이블에 직접 접근하는 일은 없습니다.
- **계약**: 버전된 API 제공(예: `POST /v1/bot-config`, `GET /v1/bot-config/:id`, `POST /v1/execution-log`, `GET /v1/execution-log?botId=...`, `GET /v1/api-keys/:venue`). 모든 접근은 계약을 통해서만 이뤄지며 공유 DB 핸들은 없습니다.
- **스키마(베이스라인)**:
  - `bot_configs(id, bot_id, name, strategy, params_json, venue, status, allocation_pct, created_at, updated_at)`
  - `execution_logs(id, bot_id, venue, symbol, side, size, entry_px, exit_px, pnl, latency_ms, tx_id, filled_at, raw_response_json)`
  - `api_keys(id, venue, label, key_hash, created_at, last_rotated_at, status)`
  - `audit_trails(id, actor, action, resource, metadata_json, created_at)`
- **경계**: 준비된 DTO/쿼리만 제공하며 트레이딩 로직은 포함하지 않습니다. BotConfigService, TradeExecutionService 등 도메인 서비스만 호출할 수 있으며, View는 각자의 서비스 경유로만 간접 접근합니다.
- **테스트**: 마이그레이션/스키마 테스트, 엔드포인트별 계약 테스트, 로그 보존/PII 마스킹 검증.***
