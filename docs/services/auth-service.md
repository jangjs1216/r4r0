# AuthService (Backend for AuthViewService) — Requirements

이 문서는 `bible.md`의 서비스 경계/계약 우선 원칙과 `README.md`의 서비스 토폴로지를 바탕으로, **AuthViewService를 지원하는 AuthService 백엔드 구현 요구사항**을 정리합니다.

## 1) 범위 (Scope)

- AuthViewService에 필요한 **세션 상태/사용자 정보/컨트롤 목록**을 제공한다.
- Binance API Key를 **안전하게 등록/조회/회전/폐기**할 수 있는 백엔드 API를 제공한다.
- 키 메타데이터/감사 로그는 `DatabaseService`의 계약을 통해 저장한다(직접 DB 접근 금지).
- 비밀값(API Secret)은 **디스크에 쓰지 않고** 시크릿 매니저(예: Vault/ASM/KMS)로만 보관한다.

## 2) 비범위 (Non-goals)

- 트레이딩 실행/주문 라우팅(Execution/ExchangeAdapter) 구현.
- 포트폴리오/마켓 데이터 등 다른 도메인 기능 구현.
- 프런트엔드(View) 렌더링 로직 변경(이 문서의 목적은 백엔드 요구사항 정리).

## 3) 서비스 경계/의존성 (Bible 준수)

- AuthService는 **Auth 도메인(유저/세션/MFA/키 관리)**만 책임진다.
- View/Orchestrator는 AuthService의 **공개 계약(API)**만 호출한다.
- 키 메타데이터/감사 로그 저장은 `DatabaseService` 계약을 통해 수행한다(`docs/services/database-service.md` 참조).
- Binance 검증/상태 확인이 필요하면, AuthService는 외부 API(Binance) 호출을 **Infrastructure 레이어**에서 수행한다.

## 4) View 계약(Props)과 백엔드 제공 값

AuthViewService 입력 DTO(고정 계약):
- `contracts/frontend/auth.schema.json`

AuthService는 아래 값을 채워 View Orchestrator가 그대로 주입할 수 있어야 한다:
- `session.status`: `authenticated | locked | unauthenticated`
- `session.mfa`: boolean
- `session.apiKeys`: 문자열 배열(마스킹된 레이블/식별자; 비밀값 금지)
- `session.environment`: 예) `staging`, `production`
- `user.{name, role, org}`
- `controls[]`: `{ label, action }` (예: `rotate`, `lock`, `signout`)

## 5) 공개 API 계약 (초안; v1)

`README.md`에 명시된 계약 토큰(`v1/auth`, `v1/keys`)을 만족하는 형태로, 최소 엔드포인트를 정의한다.
계약은 브레이킹 체인지 없이 확장(필드 추가/새 엔드포인트)하고, 필요 시 `v2`로 버전업한다.

### 5.1 Session / View props

- `GET /v1/auth/view-props`
  - 목적: AuthViewService에 필요한 props 한 번에 제공(오케스트레이터 단순화)
  - 응답: `contracts/frontend/auth.schema.json`과 호환되는 JSON

선택(분리형을 선호할 경우):
- `GET /v1/auth/session` (세션)
- `GET /v1/auth/user` (유저)
- `GET /v1/keys` (키 목록)

### 5.2 Binance API Key 관리

- `POST /v1/keys`
  - 목적: API Key/Secret 등록(“vault-only”)
  - 요청(최소): `{ apiKey, apiSecret, environment }`
  - 동작:
    - 입력 검증(빈 값/형식)
    - 시크릿 매니저에 `apiSecret` 저장(평문 로그/디스크 기록 금지)
    - `DatabaseService`를 통해 `api_keys` 메타데이터 저장(예: `venue=binance`, `label`, `key_hash`, `status`, `created_at`)
    - 가능하면 Binance에 최소 검증 호출을 수행하고(예: 계정 조회), 성공/실패를 상태로 반영
  - 응답(권장): View에 노출 가능한 “마스킹/레퍼런스”만 반환(예: `staging: bapi_****...****`)

- `POST /v1/keys/rotate` (또는 `POST /v1/keys/:id/rotate`)
  - 목적: 키 회전 워크플로(새 키 등록 → 기존 키 폐기/비활성)
  - 동작: 감사 로그 기록 + 상태 전이(예: `active` → `rotated`)

- `POST /v1/keys/revoke` (또는 `DELETE /v1/keys/:id`)
  - 목적: 키 폐기/비활성화 + 시크릿 매니저에서 제거(가능한 경우)

## 6) 데이터/스토리지 요구사항

- 평문 비밀값(`apiSecret`)은 DB에 저장하지 않는다.
- `DatabaseService`에 저장하는 값은 **메타데이터**로 제한한다:
  - `venue`: `"binance"` 고정(초기)
  - `label`: 사람이 구분 가능한 값(환경 포함 권장)
  - `key_hash`: API Key 해시(원문 저장 지양)
  - `status`: `active|revoked|rotated|invalid` 등(내부 상태; View에는 마스킹 문자열로만 노출)
  - `created_at`, `last_rotated_at`, `last_used_at`(가능한 경우)
- 감사 로그(`audit_trails`)는 `DatabaseService` 계약으로만 기록한다(누가/무엇을/언제/어떤 리소스).

## 7) 보안 요구사항

- **절대 금지**: 시크릿을 로그/에러/트레이스/클라이언트 응답에 포함.
- 전송 구간 TLS(프로덕션 기준), CORS/CSRF 정책 명확화(웹 콘솔 시나리오).
- 인증/인가:
  - 최소: 인증된 세션에서만 키 CRUD 가능
  - 권장: 역할 기반 접근(RBAC) + 조직/테넌트 분리
- 레이트리밋/브루트포스 방지(키 등록/세션 엔드포인트 포함).
- 환경 분리:
  - `staging`/`production` 키를 논리적으로 분리 저장(네임스페이스/경로 분리)

## 8) 오류 응답/관측성

- 오류 응답은 일관된 포맷(예: `{ code, message, details? }`)을 사용하되, 계약으로 고정한다.
- 시크릿 관련 실패는 내부 코드로만 식별하고, 외부 메시지는 최소 정보만 제공한다.
- 메트릭/로그:
  - `POST /v1/keys` 성공/실패/검증 실패 카운트
  - Binance 검증 호출 지연/실패율
  - 감사 로그 누락 방지(필수 이벤트)

## 9) 테스트 요구사항

- 계약 테스트:
  - `GET /v1/auth/view-props` 응답이 `contracts/frontend/auth.schema.json`을 만족
- 보안 테스트(최소):
  - 로그/응답에 `apiSecret`이 포함되지 않음을 검증
- 통합 테스트(선택):
  - `DatabaseService` 계약 호출(메타데이터/감사 로그) 모킹 또는 테스트 더블
  - Binance 검증 클라이언트 성공/실패 케이스

