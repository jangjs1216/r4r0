# MarketViewService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**:
  - 특정 마켓(심볼)의 실시간 시세 조회
  - 오더북(호가창) 및 체결 내역(Tape) 시각화
  - 기술적 분석을 위한 차트(Candlestick) 렌더링
  - 봇 마커(매매 시점) 오버레이 표시

- **하지 않는 일**:
  - 사용자의 전체 잔고 관리
  - 봇 전략 설정 수정

## 2. 외부 계약 (Contract)

### 2.1 Props (입력)

참조: `contracts/frontend/market.schema.json`

- **symbols**: 마켓 목록 (`price`, `change`, `volume` 포함)
- **selectedSymbol**: 현재 보고 있는 심볼 (예: "BTC/USDT")
- **book**:
  - `bids`: [[price, qty], ...]
  - `asks`: [[price, qty], ...]
  - `tape`: 최근 체결 내역 리스트
- **chart**: 차트 설정 및 캔들 데이터 (`provider`, `candles` 등)
- **botMarkers**: 차트 위에 표시할 봇 매매 시점 마커
- **onSymbolChange**: 심볼 변경 요청 핸들러

## 3. 내부 개념 모델 (Domain Model)

- **OrderBook**: 매수/매도 호가 리스트. 시각화를 위해 정렬 및 집계됨.
- **Candle**: 시가/고가/저가/종가/거래량 데이터.
- **TradeTape**: 실시간 체결 내역 스트림.

## 4. 주요 플로우 요약

### 4.1 마켓 모니터링
1. 좌측/상단 심볼 리스트에서 심볼 선택.
2. `onSymbolChange` 이벤트 발생 -> Orchestrator가 데이터 갱신 유도.
3. 해당 심볼의 차트, 오더북, 체결 내역 렌더링.
4. 봇 매매 내역이 있을 경우 차트에 마커 표시.

## 5. 변경 이력 (Change Log)

- 2025-12-16: 초기 정의 (`contracts/frontend/market.schema.json` 기반)
