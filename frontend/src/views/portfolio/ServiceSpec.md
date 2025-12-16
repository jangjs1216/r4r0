# PortfolioViewService - Service Spec

## 1. 역할과 책임 (Responsibility)

- **역할**:
  - 보유 중인 모든 암호화폐 자산 및 포지션 상세 조회
  - 자산 배분 비중(Allocation) 시각화 (예: 파이 차트)
  - 입출금(Transfer) 내역 표시

- **하지 않는 일**:
  - 신규 매매 주문 실행 (TradedExecutionService가 담당, 여기서는 조회 위주)
  - 시장 데이터 분석 (MarketView 담당)

## 2. 외부 계약 (Contract)

### 2.1 Props (입력)

참조: `contracts/frontend/portfolio.schema.json`

- **holdings**: 보유 포지션/자산 목록 (`symbol`, `size`, `entry`, `mark`, `pnl`)
- **allocations**: 자산별 비중 (`pct`) 및 펀딩비 정보
- **transfers**: 최근 입출금 내역
- **selectedSymbol**: (선택적) 강조할 심볼

## 3. 내부 개념 모델 (Domain Model)

- **Holding**: 현재 보유 중인 자산 또는 파생상품 포지션. 미실현 손익을 포함.
- **AllocationStats**: 포트폴리오 리스크 관리를 위한 자산별 비중 데이터.

## 4. 주요 플로우 요약

### 4.1 포트폴리오 점검
1. 전체 보유 자산 목록 테이블 렌더링.
2. 각 자산의 미실현 손익(PnL) 및 현재가(Mark Price) 확인.
3. 자산 배분 차트를 통해 특정 자산 쏠림 현상 확인.

## 5. 변경 이력 (Change Log)

- 2025-12-16: 초기 정의 (`contracts/frontend/portfolio.schema.json` 기반)
