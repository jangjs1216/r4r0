# Fear / Greed Contrarian Strategies (실전 구현 가이드 + 의사코드)

이 문서는 “사람들이 **탐욕/공포로 주문을 던진 직후**, 그 **반대 방향**으로 진입(역추세/페이드)”을 실전적으로 구현하기 위한 5가지 방안을 정리한다.  
코드 구현은 `ExecutionService`의 전략(Strategy)로 들어가며, 데이터/주문은 `ExchangeAdapterService` 계약을 통해서만 접근한다.

---

## 공통 전제: 전략이 가져야 할 안전장치(필수)

> 역추세는 “맞으면 빠르게 이익, 틀리면 크게 손실” 구조가 되기 쉽다. 아래 공통 가드레일을 먼저 정의한다.

- **쿨다운(Cooldown)**: 신호 발생 후 `cooldown_seconds` 동안 재진입 금지(연속 진입 방지).
- **최대 손실 제한(Per-trade stop)**: 손절을 “가격 기반(고/저점)” + “최대 손실 USDT” 중 더 보수적으로 적용.
- **타임 스탑(Time stop)**: 일정 시간 내에 평균회귀가 안 오면 포지션 종료.
- **포지션 사이징**: `account_allocation` * `risk_fraction` 기반(예: 0.5%~2%).
- **단일 심볼/단일 포지션 정책(MVP)**: 한 심볼에 동시에 1포지션만(신호 겹침 방지).

### 공통 상태 모델(의사코드)

```pseudo
# 상태는 최소 4개로 시작한다.
STATE = FLAT | WAIT_CONFIRM | IN_POSITION | COOLDOWN

on_tick():
  if STATE == COOLDOWN and now < cooldown_until:
    return

  if STATE == IN_POSITION:
    manage_position()      # 손절/익절/시간청산/트레일링 등
    return

  if STATE in [FLAT, WAIT_CONFIRM]:
    maybe_generate_signal()
```

---

## 1) 단기 급등락(가격 충격) 페이드 (Price Shock Fade)

### 아이디어
- **탐욕**: 짧은 시간에 과도한 급등(시장가 매수 폭탄) → **매도(반대 방향)**
- **공포**: 짧은 시간에 과도한 급락(시장가 매도 폭탄) → **매수(반대 방향)**

### 필요한 데이터
- 최소: `GET /market/ticker`의 `price` + “직전 가격들”을 위한 in-memory 링버퍼
- (권장) `ohlcv`가 없더라도 1초~5초 샘플링으로 근사 가능

### 신호 정의(예시)
- `return_Ns = (price_now / price_Ns_ago) - 1`
- `z = (return_Ns - mean(return_window)) / std(return_window)`
- `z >= +Z_TH`이면 **탐욕(과열)**, `z <= -Z_TH`이면 **공포(패닉)**

### 진입 확인(“바로 역방향”을 줄이는 장치)
- 신호 직후 즉시 진입 대신, 다음 중 1개 이상 만족 시 진입:
  - `price`가 더 이상 신호 방향으로 고점을/저점을 갱신 못함(모멘텀 약화)
  - `n`틱 연속으로 되돌림(간단히 `price <= previous_price` 같은 조건)

### 의사코드

```pseudo
params:
  sample_interval_ms = 1000
  shock_window_sec = 30
  stats_window_sec = 300
  z_threshold = 3.0
  confirm_ticks = 3
  risk_fraction = 0.01
  stop_pct = 0.004
  take_profit_pct = 0.003
  time_stop_sec = 180
  cooldown_sec = 60

state:
  price_buffer = RingBuffer(maxlen=stats_window_sec / sample_interval_sec)
  shock_direction = NONE | UP | DOWN
  confirm_count = 0
  entry_price = null
  entry_time = null

on_tick():
  price = adapter.get_ticker(key_id, symbol).price
  price_buffer.push({t: now, price})

  if not price_buffer.has(price_Ns_ago(shock_window_sec)):
    return

  r = price / price_buffer.price_at(now - shock_window_sec) - 1
  z = zscore(r, returns_over_last(stats_window_sec))

  if STATE == FLAT:
    if z >= z_threshold:
      shock_direction = UP           # 탐욕(급등)
      STATE = WAIT_CONFIRM
      confirm_count = 0
    else if z <= -z_threshold:
      shock_direction = DOWN         # 공포(급락)
      STATE = WAIT_CONFIRM
      confirm_count = 0

  if STATE == WAIT_CONFIRM:
    # 확인 조건: 더 못 가는지(모멘텀 둔화) 체크
    if shock_direction == UP:
      if price <= previous_price:
        confirm_count += 1
      else:
        confirm_count = max(confirm_count - 1, 0)

      if confirm_count >= confirm_ticks:
        qty = position_size_from_balance(risk_fraction)
        adapter.place_order(key_id, symbol, side="sell", amount=qty, reason="Greed Shock Fade")
        set_position(entry_price=price, entry_time=now, direction="short_or_reduce")
        STATE = IN_POSITION

    if shock_direction == DOWN:
      if price >= previous_price:
        confirm_count += 1
      else:
        confirm_count = max(confirm_count - 1, 0)

      if confirm_count >= confirm_ticks:
        qty = position_size_from_balance(risk_fraction)
        adapter.place_order(key_id, symbol, side="buy", amount=qty, reason="Fear Shock Fade")
        set_position(entry_price=price, entry_time=now, direction="long")
        STATE = IN_POSITION

  if STATE == IN_POSITION:
    if unrealized_pnl_pct() <= -stop_pct:
      exit_market("Stop Loss")
      STATE = COOLDOWN
      cooldown_until = now + cooldown_sec
    else if unrealized_pnl_pct() >= take_profit_pct:
      exit_market("Take Profit")
      STATE = COOLDOWN
      cooldown_until = now + cooldown_sec
    else if now - entry_time >= time_stop_sec:
      exit_market("Time Stop")
      STATE = COOLDOWN
      cooldown_until = now + cooldown_sec
```

---

## 2) RSI/볼린저 기반 과열·패닉 역추세 (Mean Reversion with Indicators)

### 아이디어
- **탐욕**: RSI 과매수 + 볼린저 상단 이탈 → (재진입 시) **매도**
- **공포**: RSI 과매도 + 볼린저 하단 이탈 → (재진입 시) **매수**
- 핵심은 “이탈 순간 추격”이 아니라 **재진입(re-entry)** 을 트리거로 삼는 것.

### 필요한 데이터
- `ohlcv`(캔들) 필요: 최소 `close` 배열
- 현재 `ExchangeAdapterService`에는 `ohlcv` 엔드포인트가 없으므로 실전 구현 시 아래 중 하나가 필요:
  - `ExchangeAdapterService`: `GET /market/ohlcv?key_id&symbol&timeframe&limit`
  - 또는 별도 MarketData 서비스로 분리(장기적으로 권장)

### 의사코드

```pseudo
params:
  timeframe = "1m"
  limit = 200
  rsi_period = 14
  bb_period = 20
  bb_k = 2.0
  rsi_overbought = 70
  rsi_oversold = 30
  stop_pct = 0.006
  cooldown_sec = 120

state:
  last_band_state = INSIDE | ABOVE | BELOW
  entry_price = null

on_tick():
  candles = adapter.get_ohlcv(key_id, symbol, timeframe, limit)
  closes = candles.close
  price = closes[-1]

  rsi = RSI(closes, rsi_period)
  mid, upper, lower = BollingerBands(closes, bb_period, bb_k)

  band_state =
    if price > upper: ABOVE
    else if price < lower: BELOW
    else: INSIDE

  if STATE == FLAT:
    # 탐욕: 위로 과열 -> 재진입 시 역방향 진입
    if rsi >= rsi_overbought and last_band_state == ABOVE and band_state == INSIDE:
      qty = position_size_from_balance(risk_fraction)
      adapter.place_order(key_id, symbol, side="sell", amount=qty, reason="Greed: RSI+BB reentry")
      entry_price = price
      STATE = IN_POSITION

    # 공포: 아래로 과매도 -> 재진입 시 매수
    if rsi <= rsi_oversold and last_band_state == BELOW and band_state == INSIDE:
      qty = position_size_from_balance(risk_fraction)
      adapter.place_order(key_id, symbol, side="buy", amount=qty, reason="Fear: RSI+BB reentry")
      entry_price = price
      STATE = IN_POSITION

  if STATE == IN_POSITION:
    # 1차 목표: 미들밴드(mid) 회귀를 목표로 잡으면 “평균회귀형” 청산이 된다.
    if (position_is_long() and price >= mid) or (position_is_short() and price <= mid):
      exit_market("Mean Reversion to Mid")
      STATE = COOLDOWN
      cooldown_until = now + cooldown_sec

    # 손절: 엔트리 대비 퍼센트 (MVP)
    if moved_against_entry(price, entry_price, stop_pct):
      exit_market("Stop Loss")
      STATE = COOLDOWN
      cooldown_until = now + cooldown_sec

  last_band_state = band_state
```

---

## 3) 오더북 스윕·체결 불균형(시장가 폭탄) 페이드 (Orderflow Exhaustion)

### 아이디어
사람들이 공포/탐욕으로 던지는 주문은 대개 **시장가(taker)** 로 나타나며, 다음 현상으로 관측된다.
- 오더북 여러 레벨이 순식간에 소진(“스윕”)
- 스프레드 급확대 후 빠른 정상화
- 체결 델타(매수-매도 체결량)가 한쪽으로 급증

“그런데 가격이 더 못 가고 막히면(흡수/고갈)” 반대 방향으로 짧게 먹는 전략이다.

### 필요한 데이터
- `orderbook depth` + `recent trades`(체결 스트림)
- 현재 `ExchangeAdapterService`에는 해당 엔드포인트가 없으므로 실전 구현 시:
  - `GET /market/depth?symbol&limit`
  - `GET /market/trades?symbol&limit` 또는 websocket 스트림이 필요

### 의사코드

```pseudo
params:
  depth_limit = 50
  trades_lookback_sec = 10
  delta_threshold = 3.0
  sweep_levels_threshold = 5
  spread_expand_threshold = 2.0
  confirm_absorption_ticks = 2
  stop_buffer_pct = 0.001
  cooldown_sec = 120

state:
  last_mid = null
  last_spread = null
  sweep_high = null
  sweep_low = null
  absorption_count = 0
  last_signal_side = NONE | BUY_PRESSURE | SELL_PRESSURE

on_tick():
  ob = adapter.get_depth(symbol, depth_limit)
  trades = adapter.get_trades(symbol, since=now - trades_lookback_sec)

  mid = (ob.best_bid + ob.best_ask) / 2
  spread = ob.best_ask - ob.best_bid

  buy_vol = sum(t.qty for t in trades if t.side == "buy")
  sell_vol = sum(t.qty for t in trades if t.side == "sell")
  delta = buy_vol - sell_vol

  swept_levels = count_price_levels_consumed(ob_snapshot_history, direction=sign(delta))
  spread_expand = spread / avg_spread_last_1m()

  if STATE == FLAT:
    if delta_is_extreme(delta, delta_threshold) and swept_levels >= sweep_levels_threshold and spread_expand >= spread_expand_threshold:
      if delta > 0:
        last_signal_side = BUY_PRESSURE     # 탐욕성 매수 폭탄
        sweep_high = recent_high_price_during_event()
      else:
        last_signal_side = SELL_PRESSURE    # 공포성 매도 폭탄
        sweep_low = recent_low_price_during_event()

      STATE = WAIT_CONFIRM
      absorption_count = 0

  if STATE == WAIT_CONFIRM:
    # “흡수” 확인: 델타는 계속 한쪽인데 가격이 더 못 감 + 스프레드 정상화
    if last_signal_side == BUY_PRESSURE:
      if mid <= last_mid and spread_is_normalizing():
        absorption_count += 1
      if absorption_count >= confirm_absorption_ticks:
        qty = position_size_from_balance(risk_fraction)
        adapter.place_order(key_id, symbol, side="sell", amount=qty, reason="Greed: orderflow exhaustion")
        set_stop(price = sweep_high * (1 + stop_buffer_pct))
        STATE = IN_POSITION

    if last_signal_side == SELL_PRESSURE:
      if mid >= last_mid and spread_is_normalizing():
        absorption_count += 1
      if absorption_count >= confirm_absorption_ticks:
        qty = position_size_from_balance(risk_fraction)
        adapter.place_order(key_id, symbol, side="buy", amount=qty, reason="Fear: orderflow exhaustion")
        set_stop(price = sweep_low * (1 - stop_buffer_pct))
        STATE = IN_POSITION

  if STATE == IN_POSITION:
    manage_position_mean_revert()  # VWAP/중심가/미들밴드 회귀 목표
    if stopped_or_tp_or_time_stop():
      STATE = COOLDOWN
      cooldown_until = now + cooldown_sec

  last_mid = mid
  last_spread = spread
```

---

## 4) 돌파 실패(스탑런) 페이드 (Breakout Failure / Stop-run Fade)

### 아이디어
군중 심리는 주요 고점/저점에서 주문이 몰리고, 돌파 순간 “추격(탐욕/공포)”이 발생한다.  
하지만 종종 돌파는 “스탑(손절) 털기”로 끝나고, 가격이 레벨 안으로 복귀하며 반대 방향으로 크게 되돌린다.

- **탐욕 케이스**: 저항 돌파(고점 갱신) 직후 **종가가 다시 레벨 아래로 복귀** → 매도
- **공포 케이스**: 지지 붕괴(저점 이탈) 직후 **종가가 다시 레벨 위로 복귀** → 매수

### 필요한 데이터
- `ohlcv`(캔들): 최소 `high/low/close`

### 의사코드

```pseudo
params:
  timeframe = "5m"
  lookback_bars = 50
  breakout_buffer_pct = 0.0005      # 레벨 판정 여유
  stop_buffer_pct = 0.0008
  require_volume_spike = true
  volume_spike_ratio = 2.0
  cooldown_sec = 180

state:
  key_level_high = null
  key_level_low = null
  last_breakout = NONE | UP | DOWN
  breakout_extreme = null            # 스윕 고/저점(손절 기준)

on_tick():
  candles = adapter.get_ohlcv(key_id, symbol, timeframe, limit=lookback_bars + 2)
  highs = candles.high
  lows = candles.low
  closes = candles.close
  vols = candles.volume

  level_high = max(highs[-(lookback_bars+1):-1])   # 직전 lookback 구간 고점
  level_low  = min(lows[-(lookback_bars+1):-1])    # 직전 lookback 구간 저점
  close_now  = closes[-1]
  high_now   = highs[-1]
  low_now    = lows[-1]

  vol_ok = true
  if require_volume_spike:
    vol_ok = vols[-1] >= avg(vols[-(lookback_bars+1):-1]) * volume_spike_ratio

  if STATE == FLAT and vol_ok:
    # 1) 돌파 이벤트 탐지
    if high_now >= level_high * (1 + breakout_buffer_pct):
      last_breakout = UP
      breakout_extreme = high_now
    if low_now <= level_low * (1 - breakout_buffer_pct):
      last_breakout = DOWN
      breakout_extreme = low_now

    # 2) "실패" 확인: 종가가 레벨 안으로 복귀하면 역방향 진입
    if last_breakout == UP and close_now < level_high:
      qty = position_size_from_balance(risk_fraction)
      adapter.place_order(key_id, symbol, side="sell", amount=qty, reason="Greed: breakout failure fade")
      set_stop(price = breakout_extreme * (1 + stop_buffer_pct))
      STATE = IN_POSITION

    if last_breakout == DOWN and close_now > level_low:
      qty = position_size_from_balance(risk_fraction)
      adapter.place_order(key_id, symbol, side="buy", amount=qty, reason="Fear: breakdown failure fade")
      set_stop(price = breakout_extreme * (1 - stop_buffer_pct))
      STATE = IN_POSITION

  if STATE == IN_POSITION:
    # 목표: 레인지 중앙/반대편 레벨로 회귀
    target = (level_high + level_low) / 2
    if reached_target(target) or stopped_or_time_stop():
      exit_market("Range mean/stop")
      STATE = COOLDOWN
      cooldown_until = now + cooldown_sec
```

---

## 5) 레버리지 군중 지표(펀딩·OI·청산) 역추세 (Crowded Leverage Reversal)

### 아이디어
“탐욕/공포 주문 투척”은 선물 시장에서 더 강하게 관측된다.
- **탐욕(롱 과열)**: 펀딩비 급등 + OI 급증 + (상승 중) 청산(숏 청산) 스파이크 → 이후 되돌림 구간을 역방향 공략
- **공포(숏 과열)**: 펀딩비 급락(음수) + OI 급증 + (하락 중) 청산(롱 청산) 스파이크 → 이후 되돌림 구간을 역방향 공략

### 필요한 데이터
거래소마다 제공 방식이 달라서 ExchangeAdapter에 “표준화된 파생 지표 엔드포인트”를 추가하는 게 현실적이다.
- 예시(새 계약): `GET /derivatives/metrics?symbol=BTC/USDT`
  - `funding_rate`, `open_interest`, `liquidations_1m`, `mark_price`, `index_price` 등

### 의사코드

```pseudo
params:
  funding_z_th = 3.0
  oi_change_th = 0.15                 # N분 대비 15%+
  liquidation_spike_th = 3.0
  require_price_exhaustion = true
  cooldown_sec = 300

state:
  metrics_history = RingBuffer(maxlen=200)

on_tick():
  m = adapter.get_derivatives_metrics(symbol)
  metrics_history.push(m)

  if not enough_history(metrics_history):
    return

  funding_z = zscore(m.funding_rate, metrics_history.funding_rate)
  oi_change = m.open_interest / metrics_history.open_interest_at(now - 10m) - 1
  liq_z = zscore(m.liquidations_1m, metrics_history.liquidations_1m)

  # (선택) 가격 고갈 확인: 상승/하락이 둔화되거나 레인지 복귀 신호
  price_ok = true
  if require_price_exhaustion:
    price_ok = price_momentum_is_fading()

  if STATE == FLAT and price_ok:
    # 탐욕(롱 과열) -> 반대(매도)
    if funding_z >= funding_z_th and oi_change >= oi_change_th and liq_z >= liquidation_spike_th:
      qty = position_size_from_balance(risk_fraction)
      adapter.place_order(key_id, symbol, side="sell", amount=qty, reason="Greed: crowded long reversal")
      STATE = IN_POSITION

    # 공포(숏 과열) -> 반대(매수)
    if funding_z <= -funding_z_th and oi_change >= oi_change_th and liq_z >= liquidation_spike_th:
      qty = position_size_from_balance(risk_fraction)
      adapter.place_order(key_id, symbol, side="buy", amount=qty, reason="Fear: crowded short reversal")
      STATE = IN_POSITION

  if STATE == IN_POSITION:
    # 목표: 펀딩 정상화 / OI 감소 / 평균회귀 레벨 도달 중 하나를 익절 트리거로 사용
    if funding_z_back_to_normal() or reached_mean_reversion_level() or stopped_or_time_stop():
      exit_market("Crowding unwind / stop")
      STATE = COOLDOWN
      cooldown_until = now + cooldown_sec
```

---

## 구현 메모(이 레포 구조 기준)

- 전략 코드는 `services/execution_service/strategies/*`에 추가하고, `ExecutionService`에서 config의 `pipeline.strategy.id`로 로딩한다.
- 실전형 데이터(`ohlcv`, `depth`, `trades`, `derivatives metrics`)는 **반드시** `ExchangeAdapterService`의 계약(API)로 노출되어야 하며, `ExecutionService`가 거래소 SDK/DB에 직접 접근하지 않는다.
- 주문은 `LedgerAwareAdapter.place_order(...)`를 통해 나가야 원장(LocalOrder/GlobalExecution)이 누락 없이 기록된다(시각화/감사/분석에 중요).

