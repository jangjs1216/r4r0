# AuthService (Key Manager) - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**:
  - **Secure Key Storage**: 거래소 API Key/Secret을 AES-256 등 강력한 알고리즘으로 암호화하여 저장.
  - **Key Lifecycle Management**: 키 등록, 조회(마스킹), 삭제.
  - **Signer Provider**: (추후) `TradeExecutionService` 등 다른 서비스가 주문을 나갈 때, 요청을 받아 서명(Sign) 값을 반환하거나, 복호화된 키를 안전한 채널로 제공(Role에 따라).

- **보안 요구사항 (Critical)**:
  - **Transport Security**: 클라이언트와 서버 간의 모든 통신(특히 키 등록)은 반드시 **HTTPS (TLS 1.2+)**를 통해 이루어져야 한다. (HTTP 사용 시 Secret Key 유출 위험).
  - 로컬 개발 환경에서는 HTTP를 허용하되, 브라우저 경고가 발생할 수 있음을 인지한다.

- **하지 않는 일**:
  - **User Authentication**: 로그인/세션 관리 (프로젝트 정책상 제거됨).
  - **Order Execution**: 실제 거래소 API 호출은 `ExchangeAdapter`가 수행.

## 2. 외부 계약 (Contract)

### 2.1 REST API

참조: `contracts/backend/auth-api.yaml`

- **GET /keys**
  - 저장된 모든 키의 목록 반환.
  - **Secret Key는 절대 반환하지 않음.** (Public Key도 마스킹 처리 권장)
- **POST /keys**
  - 신규 키 등록.
  - 입력: `exchange`, `label`, `publicKey`, `secretKey`
  - 처리: `secretKey`를 암호화하여 DB 저장.
- **DELETE /keys/{id}**
  - 키 영구 삭제.

## 3. 내부 개념 모델 (Domain Model)

- **StoredCredential**:
  - `id` (UUID)
  - `exchange` (enum)
  - `label` (string)
  - `access_key_enc` (encrypted bytes)
  - `secret_key_enc` (encrypted bytes)
  - `created_at`

## 4. 주요 플로우 요약

### 4.1 키 등록 및 보존
1. Frontend `AuthView`에서 `POST /keys` 요청.
2. `AuthService`는 환경변수(`MASTER_KEY`)를 이용해 Secret Key를 암호화.
3. 로컬 SQLite DB (`data/auth.db`)에 저장.
4. 응답으로 마스킹된 정보 반환.

### 4.2 시스템 재시작 시
1. 서비스 재시작 되어도 `data/auth.db`는 유지됨 (프로젝트 코드 외부에 존재해야 함, `.gitignore` 필수).
2. `GET /keys` 요청 시 DB에서 로드하여 반환 -> "계속해서 서비스에 연동" 조건 만족.

## 5. 변경 이력 (Change Log)

- 2025-12-17: 초기 생성. 보안을 고려한 로컬 암호화 저장소로 설계.
