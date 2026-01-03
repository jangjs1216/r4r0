# ExchangeAdapterService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할 (Role)**:
  - **Proxy to Exchange**: Binance 등 외부 거래소 API와의 직접적인 통신을 담당.
  - **Protocol Normalization**: 거래소마다 다른 API 응답(Balance, Order 등)을 내부 표준 포맷으로 변환.
  - **Rate Limit Management**: 거래소 API 호출 제한을 준수하도록 요청 속도 조절.

- **책임 (Responsibility)**:
  - `AuthService`로부터 (내부 채널을 통해) 복호화된 API Key/Secret을 획득하여 서명 생성.
  - 잔고(Balance) 조회 요청 수행 및 결과 반환.
  - **Current Price & Limits**: 실시간 현재가 및 주문 제약조건(Min Notional 등) 조회.
  - **Order Execution**: 봇 또는 사용자의 요청에 따라 실제 매수/매도 주문 실행.

- **하지 않는 일 (Non-Goals)**:
  - **Key Storage**: 키를 직접 저장하지 않으며, `AuthService`에 의존한다.
  - **Trading Strategy**: 언제 사고 팔지 결정하지 않는다. (순수 Executor)

## 2. 외부 계약 (Contract)

### 2.1 제공 API (`contracts/backend/exchange-adapter-api.yaml`)

- **GET /balance/{keyId}**
  - 입력: `keyId` (AuthService에 등록된 키 ID)
  - 출력: `AccountBalance` (총 자산 가치 및 코인별 보유량)
  - 동작:
    1. `AuthService`에 `keyId`에 해당하는 Secret 요청.
    2. Binance API (`GET /api/v3/account`) 호출.
    3. 결과를 표준 포맷으로 변환하여 반환.

- **GET /market/ticker**
  - 입력: `key_id`, `symbol` (예: BTC/USDT)
  - 출력: 현재가(`price`) 및 주문 제약 정보(`limits`: min_notional, min_amount)
  - 목적: 전략 실행 전 최소 주문 금액 준수 여부 확인용

- **POST /order**
  - 입력: `key_id`, `symbol`, `side` (buy/sell), `amount`, `order_type`, `price` (limit인 경우)
  - 출력: `order_id` (거래소 주문 ID), `status`, `details`
  - 동작: `AuthService`에서 키를 받아 거래소에 주문을 전송하고 결과를 반환.

### 2.2 의존 계약 (Dependencies)

- **AuthService**:
  - `GET /internal/keys/{id}/secret` (예정): API 호출을 위한 Secret Key 불출.
  - 보안을 위해 `ExchangeAdapter`와 `AuthService`는 동일한 사설 네트워크(Docker Network) 내에서만 통신해야 함.

## 3. 내부 개념 모델 (Domain Model)

- **ExchangeClient (Interface)**:
  - `fetch_balance()`
  - 구현체: `BinanceClient`, `UpbitClient` 등.

## 4. 데이터 흐름

1. **Dashboard** (Frontend) -> **ExchangeAdapter**: `GET /balance/key-123` 호출.
2. **ExchangeAdapter** -> **AuthService**: `key-123`의 API Key/Secret 요청.
3. **ExchangeAdapter** -> **Binance**: 서명된 요청 전송 (`/api/v3/account`).
4. **Binance** -> **ExchangeAdapter**: 응답 수신.
5. **ExchangeAdapter** -> **Dashboard**: `AccountBalance` JSON 반환.

## 5. 변경 이력

- 2025-12-17: 초기 설계. 잔고 조회 기능 중심.
