# AuthViewService - Service Spec (Key Management Hub)

## 1. 역할과 책임 (Responsibility)

- **역할**:
  - **Multi-Exchange API Key Management**: Binance, Upbit 등 여러 거래소의 API Key 등록/관리.
  - **거래소 연결 허브**: 봇이 사용할 수 있는 거래소 연결(Connetion)들의 저장소 역할.

- **하지 않는 일**:
  - **User Authentication**: 로그인/로그아웃 프로세스는 제거됨 (항상 접속 상태).
  - API Key를 이용한 트레이딩 실행 (ExecutionService 담당).

## 2. 외부 계약 (Contract)

### 2.1 Props

참조: `contracts/frontend/auth.schema.json`
(기존 `session` 필드는 유지하되, `status`는 항상 `authenticated`로 간주)

- **exchangeKeys**: 등록된 거래소 키 목록.

### 2.2 Events

- **onAddKey(payload)**: 키 등록 요청.
- **onDeleteKey(id)**: 키 삭제 요청.

## 3. 내부 개념 모델 (Domain Model)

- **ExchangeConnection**: { ExchangeID, Label, MaskedKey, Permissions }

## 4. 주요 플로우

1. 사용자가 Sidebar에서 'Auth'(또는 Key Manager) 클릭.
2. 현재 등록된 API Key 목록 조회.
3. 'Add Connection'으로 새 키 등록 -> 백엔드 전송 -> 목록 갱신.

## 5. 변경 이력

- 2025-12-16: 로그인/로그아웃 기능 제거. 순수 **API Key Manager**로 역할 축소 및 집중.
