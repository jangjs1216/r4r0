const TV_SCRIPT = "https://s3.tradingview.com/tv.js";
let tvScriptPromise = null;

export function mountMarket(container, props) {
  container.innerHTML = "";

  const headerRow = document.createElement("div");
  headerRow.className = "row";
  const select = document.createElement("select");
  props.symbols.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s.symbol;
    opt.textContent = `${s.symbol}`;
    if (s.symbol === props.selectedSymbol) opt.selected = true;
    select.appendChild(opt);
  });
  select.addEventListener("change", (e) => props.onSymbolChange(e.target.value));

  const status = document.createElement("span");
  status.className = "badge";
  status.textContent = props.chart?.provider === "tradingview" ? "TradingView" : "Local data";

  headerRow.appendChild(select);
  headerRow.appendChild(status);

  const chartFrame = document.createElement("div");
  chartFrame.className = "chart-frame";
  chartFrame.id = "tv-chart";

  if (props.chart?.provider === "tradingview") {
    mountTradingView(chartFrame, props.chart);
  } else {
    mountLocalChart(chartFrame, props.chart?.candles || []);
  }

  const markersCard = document.createElement("div");
  markersCard.className = "card";
  const markersTitle = document.createElement("div");
  markersTitle.className = "panel-title";
  markersTitle.textContent = "Bot execution markers (overlay target)";
  const markerList = document.createElement("div");
  markerList.className = "marker-list";
  props.botMarkers.forEach((m) => {
    const card = document.createElement("div");
    card.className = "marker";
    const row = document.createElement("div");
    row.className = "row";
    const bot = document.createElement("div");
    bot.textContent = m.bot;
    const side = document.createElement("span");
    side.className = m.side === "buy" ? "positive" : "negative";
    side.textContent = m.side.toUpperCase();
    row.appendChild(bot);
    row.appendChild(side);

    const price = document.createElement("div");
    price.className = "metric-label";
    price.textContent = `$${m.price}`;
    const time = document.createElement("div");
    time.className = "metric-label";
    time.textContent = new Date(m.timestamp).toLocaleString();

    card.appendChild(row);
    card.appendChild(price);
    card.appendChild(time);
    markerList.appendChild(card);
  });
  markersCard.appendChild(markersTitle);
  markersCard.appendChild(markerList);

  const symbolsTable = document.createElement("table");
  const head = document.createElement("thead");
  head.innerHTML = "<tr><th>Symbol</th><th>Price</th><th>24h</th><th>Vol</th></tr>";
  symbolsTable.appendChild(head);
  const body = document.createElement("tbody");
  props.symbols.forEach((s) => {
    body.appendChild(renderSymbolRow(s, props.selectedSymbol));
  });
  symbolsTable.appendChild(body);

  const bookWrap = document.createElement("div");
  bookWrap.className = "grid";

  const book = document.createElement("div");
  book.className = "card stack";
  const bidsTitle = document.createElement("div");
  bidsTitle.className = "metric-label";
  bidsTitle.textContent = "Order book";
  book.appendChild(bidsTitle);
  book.appendChild(renderBook(props.book));

  const tape = document.createElement("div");
  tape.className = "card stack";
  const tapeTitle = document.createElement("div");
  tapeTitle.className = "metric-label";
  tapeTitle.textContent = "Recent tape";
  tape.appendChild(tapeTitle);
  tape.appendChild(renderTape(props.book.tape || []));

  bookWrap.appendChild(book);
  bookWrap.appendChild(tape);

  container.appendChild(headerRow);
  container.appendChild(chartFrame);
  container.appendChild(markersCard);
  container.appendChild(symbolsTable);
  container.appendChild(bookWrap);
}

function renderSymbolRow(symbol, selectedSymbol) {
  const tr = document.createElement("tr");
  if (symbol.symbol === selectedSymbol) tr.style.background = "#132d2a";
  const px = symbol.price.toLocaleString("en-US", { maximumFractionDigits: 2 });
  tr.innerHTML = `<td>${symbol.symbol}</td><td class="number">$${px}</td><td class="${symbol.change >= 0 ? "positive" : "negative"}">${symbol.change}%</td><td class="number">${symbol.volume.toLocaleString()}</td>`;
  return tr;
}

function renderBook(book) {
  const wrap = document.createElement("div");
  wrap.className = "stack";

  const bids = document.createElement("div");
  bids.className = "stack";
  const bidsLabel = document.createElement("div");
  bidsLabel.className = "metric-label";
  bidsLabel.textContent = "Bids";
  bids.appendChild(bidsLabel);
  (book.bids || []).forEach(([px, qty]) => bids.appendChild(renderBookRow(px, qty, true)));

  const asks = document.createElement("div");
  asks.className = "stack";
  const asksLabel = document.createElement("div");
  asksLabel.className = "metric-label";
  asksLabel.textContent = "Asks";
  asks.appendChild(asksLabel);
  (book.asks || []).forEach(([px, qty]) => asks.appendChild(renderBookRow(px, qty, false)));

  wrap.appendChild(bids);
  wrap.appendChild(asks);
  return wrap;
}

function renderBookRow(px, qty, bid) {
  const row = document.createElement("div");
  row.className = "row";
  const price = document.createElement("div");
  price.className = bid ? "positive" : "negative";
  price.textContent = `$${px.toLocaleString()}`;
  const size = document.createElement("div");
  size.className = "metric-label";
  size.textContent = `${qty} ${bid ? "bid" : "ask"}`;
  row.appendChild(price);
  row.appendChild(size);
  return row;
}

function renderTape(tape) {
  const list = document.createElement("div");
  list.className = "list";
  tape.forEach((t) => {
    const row = document.createElement("div");
    row.className = "row";
    const side = document.createElement("span");
    side.className = `tag ${t.side === "buy" ? "" : "warn"}`;
    side.textContent = t.side.toUpperCase();
    const px = document.createElement("div");
    px.textContent = `$${t.px.toLocaleString()}`;
    const qty = document.createElement("div");
    qty.className = "metric-label";
    qty.textContent = `${t.qty} · ${t.ago} ago`;
    row.appendChild(side);
    row.appendChild(px);
    row.appendChild(qty);
    list.appendChild(row);
  });
  return list;
}

function mountTradingView(target, chart) {
  ensureTradingView()
    .then(() => {
      target.innerHTML = "";
      /* global TradingView */
      new TradingView.widget({
        autosize: true,
        symbol: chart.symbol,
        interval: chart.interval || "60",
        container_id: target.id,
        theme: "dark",
        style: "1",
        locale: "en",
        hide_side_toolbar: false,
        hide_top_toolbar: false,
      });
    })
    .catch(() => {
      mountLocalChart(target, chart.candles || []);
    });
}

function ensureTradingView() {
  if (window.TradingView) return Promise.resolve();
  if (tvScriptPromise) return tvScriptPromise;
  tvScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = TV_SCRIPT;
    script.onload = () => resolve();
    script.onerror = (err) => reject(err);
    document.head.appendChild(script);
  });
  return tvScriptPromise;
}

function mountLocalChart(target, candles) {
  target.innerHTML = "";
  const canvas = document.createElement("canvas");
  canvas.width = target.clientWidth || 640;
  canvas.height = target.clientHeight || 360;
  const ctx = canvas.getContext("2d");
  target.appendChild(canvas);

  if (!candles.length) {
    const fallback = document.createElement("div");
    fallback.className = "chart-fallback";
    fallback.textContent = "No chart data";
    target.appendChild(fallback);
    return;
  }

  const closes = candles.map((c) => c.c);
  const max = Math.max(...closes);
  const min = Math.min(...closes);
  const pad = (max - min) * 0.1 || 1;
  const scaleY = (val) => {
    const h = canvas.height - 20;
    return h - ((val - (min - pad)) / (max - min + pad * 2)) * h + 10;
  };
  const stepX = canvas.width / Math.max(1, closes.length - 1);

  ctx.strokeStyle = "#4da1ff";
  ctx.lineWidth = 2;
  ctx.beginPath();
  closes.forEach((c, idx) => {
    const x = idx * stepX;
    const y = scaleY(c);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}
