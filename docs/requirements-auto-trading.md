# 자동매매 실현을 위한 리팩토링 요구사항

> 작성일: 2026-06-11 · 기준 브랜치: `impl-backtest`
> 배경: 현재 시스템은 거래소 연동(잔고/시세 조회, 주문 전송)과 봇 실행 파이프라인(봇 생성 → 시작 → 루프 → 주문 → 원장 기록)이 코드상 존재하나, 실제 자동매매를 신뢰성 있게 수행할 수 없는 상태다.
> 원인은 기능 부재가 아니라 **(1) 전략 검증 불가, (2) 무인(24/7) 운영 불가, (3) 리스크 통제 부재** 세 가지다.
> 아키텍처 배경은 [`architecture-overview.md`](./architecture-overview.md) 참조.

---

## R1. 전략 검증 체계 — 백테스트↔라이브 단절 해소 (최우선)

**현황**: 라이브 전략(`orderflow_exhaustion_v1`)은 백테스트가 불가능하고, 백테스트 전략(SMA/RSI)은 라이브 구현이 없다. 즉 **검증되지 않은 전략만 실계좌에 올릴 수 있는 구조**다.

| ID | 요구사항 | 근거 (현재 코드) |
|---|---|---|
| R1.1 | **전략 인터페이스 단일화.** 전략 1개 = (메타데이터 + 파라미터 스키마 + 시그널 로직)을 한 모듈로 통합한다. 데이터 접근을 `MarketDataProvider` 인터페이스로 추상화해, 라이브(실시간 adapter)와 백테스트(historical replay)가 동일한 전략 코드를 실행한다. | 전략이 3곳에 분산: `services/trading_strategy_view/main.py`(스키마), `services/execution_service/strategies/`(라이브), `services/backtest_service/domain/strategy.py`(백테스트) |
| R1.2 | **레지스트리 패턴 도입.** 전략 자동 등록으로 if-else 분기와 하드코딩 목록을 제거한다. `trading_strategy_view`는 레지스트리에서 스키마를 동적으로 서빙한다. | `engine.py:109` `_initialize_strategy()`의 if-else 분기, `trading_strategy_view/main.py:15`의 인메모리 `STRATEGIES` 목록 |
| R1.3 | **백테스트 엔진 표현력 확장.** 현재 1/-1/0 시그널 모델(Long-only, 전량 매수/매도)을 포지션 사이징·TP/SL·부분 청산·시간 정지를 표현할 수 있는 모델로 확장한다. orderflow 계열(틱/체결/스프레드 기반) 전략도 백테스트 가능해야 한다. | `backtest_service/domain/strategy.py`의 `generate_signals(df) → 1/-1/0` |
| R1.4 | **`SimulationEngine` 단위 테스트 추가.** 체결/수수료/슬리피지/펀딩비 계산을 검증한다. 수치 버그가 곧 잘못된 전략 채택으로 이어진다. | 현재 백테스트 엔진 테스트 0개 |

## R2. 무인 운영(24/7) — 상태 영속성과 복구

**현황**: 포지션 상태(`position_side`, `entry_price`, `stop_price` 등)가 전략 인스턴스의 **메모리에만** 존재한다. 프로세스가 죽으면 포지션이 고아가 된다.

| ID | 요구사항 | 근거 (현재 코드) |
|---|---|---|
| R2.1 | **전략 포지션 상태 영속화.** ExecutionService 재시작 시에도 포지션·스탑·진입가를 잃지 않도록 상태를 저장한다 (원장 또는 별도 상태 저장소). | `orderflow_exhaustion_v1.py:80-95` — 모든 상태가 인스턴스 변수 |
| R2.2 | **재시작 시 포지션 복구.** 현재 poll이 RUNNING 봇에 `start()`를 재호출하면 전략이 FLAT 상태로 부팅되어 기존 포지션을 무시하고 이중 진입할 수 있다. 원장/실잔고 기준으로 포지션을 재구성한 뒤 루프를 재개해야 한다. | `execution_service/main.py:39-44` poll → `BotRunner.start()` |
| R2.3 | **주문 reconciliation 루프.** 즉시 체결되지 않은 주문이 `SENT` 상태로 방치된다. 미체결 주문을 주기적으로 조회해 Filled/Canceled를 원장에 반영하는 루프가 필요하다. limit 주문을 도입하는 순간 필수가 된다. | `ledger_adapter.py:157` — SENT 이후 추적 없음 |
| R2.4 | **원장 커밋 실패 처리.** 체결은 됐는데 원장 기록이 실패하면 현재 로그만 남기고 넘어간다. 재시도 큐 또는 알람으로 누락을 방지한다. | `ledger_adapter.py:152` — 예외를 로그만 하고 통과 |

## R3. 실행 품질 — 현재 구조로는 전략이 신호를 잡지 못함

| ID | 요구사항 | 근거 (현재 코드) |
|---|---|---|
| R3.1 | **시세 레이턴시 개선.** ExchangeAdapter가 요청마다 CCXT 클라이언트를 새로 생성하고 `load_markets()`를 호출해 호출당 수 초가 걸린다. 여기에 5초 폴링 틱 + REST `fetch_trades` 조합이라, 10초 lookback 마이크로스트럭처 신호를 쓰는 orderflow 전략은 사실상 트리거되지 않는다. 거래소 클라이언트 재사용(커넥션 풀) + WebSocket 스트림(체결/오더북) 도입이 필요하다. | `exchange_adapter/main.py` 전 엔드포인트, `engine.py:151-153` 폴링 간격 |
| R3.2 | **거래소 정밀도 규칙 준수.** 수량을 고정 소수점(`quantity_precision` 파라미터)으로 자르고 있어 거래소별 step size 위반으로 주문이 거절될 수 있다. CCXT `amount_to_precision`/`price_to_precision`을 사용한다. | `orderflow_exhaustion_v1.py:325` |
| R3.3 | **마켓 타입 결정.** 현재 `defaultType: 'spot'` 고정이라 숏 진입이 불가능하고, SELL 진입이 "보유분 일부 매도"라는 우회로 동작한다. futures 지원 여부를 결정하고 포지션 모델을 그에 맞춘다. | `exchange_adapter/main.py:35`, `orderflow_exhaustion_v1.py:43` |

## R4. 리스크 통제 — 실거래 전 필수 안전망

| ID | 요구사항 | 근거 (현재 코드) |
|---|---|---|
| R4.1 | **Paper/Testnet 모드.** 현재 실계좌로만 실행 가능해 검증 단계가 곧 실손실이다. 거래소 testnet 연결 또는 가상 체결(paper) 모드를 봇 단위로 선택할 수 있어야 한다. | ExchangeAdapter에 모드 분기 없음 |
| R4.2 | **글로벌 리스크 가드.** 킬스위치(전 봇 즉시 정지), 일일 손실 한도, 봇당 최대 할당액, 주문 전 최소 잔고 검증. 현재 전무하다. | — |
| R4.3 | **운영 알림.** 청산 실패(`on_stop` 5회 재시도 실패 시 로그만 남김), 원장 불일치, 봇 크래시를 무인 상태에서 알 수 있는 채널(텔레그램 등)이 필요하다. | `orderflow_exhaustion_v1.py:438`, `engine.py:158` |

## R5. 정리 항목 (소규모, 즉시 가능)

| ID | 요구사항 | 근거 (현재 코드) |
|---|---|---|
| R5.1 | `key_id`가 `global_settings.exchange` 필드에 저장되어 이름과 의미가 불일치한다 (Naming Golden Rule 위반). 필드명을 `key_id`로 통일하고 프론트/계약 스키마를 동기화한다. | `orderflow_exhaustion_v1.py:78`, `test_trading.py` |
| R5.2 | ExecutionService `/status`가 플레이스홀더로 항상 0을 반환한다. `active_runners` 실상태를 노출한다. | `execution_service/main.py:103-105` |
| R5.3 | 디버그 출력 제거: 봇 config 전체 print, API publicKey 로깅. | `test_trading.py`(DEBUG print), `exchange_adapter/main.py:51` |
| R5.4 | 임시 산출물 정리: `data/temp_pnl_repo/`, 루트의 `*_head.csv`, 중복 마이그레이션 스크립트. | bible.md 임시 스크립트 관리 원칙 |

---

## 권장 작업 순서

1. **R4.1 Paper/Testnet 모드** — 이후 모든 검증의 안전망. 가장 먼저.
2. **R1 전략 통합 + 백테스트 신뢰성** — 올릴 가치가 있는 전략을 만들 수 있는 기반.
3. **R2 상태 영속성·복구** — 24/7 무인 운영의 전제 조건.
4. **R3 WebSocket·정밀도** — 전략이 실제로 신호를 잡고 주문이 거절되지 않게.
5. **R4.2–R4.3 리스크 가드·알림** — 실자금 투입 직전 단계.
6. **R5** — 각 단계 진행 중 해당 파일을 건드릴 때 함께 처리.

각 단계는 bible.md 원칙대로 **한 번에 하나의 서비스**씩, 해당 서비스 `ServiceSpec.md` 갱신 → 코드 순으로 진행한다.
