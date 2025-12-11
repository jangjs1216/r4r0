export function mountBotTrades(container, props) {
  container.innerHTML = "";

  const header = document.createElement("div");
  header.className = "panel-header";
  const title = document.createElement("div");
  title.className = "panel-title";
  title.textContent = "Bot trades (key view)";
  const subtitle = document.createElement("div");
  subtitle.className = "panel-subtitle";
  subtitle.textContent = "Executed trades and outcomes";
  header.appendChild(title);
  header.appendChild(subtitle);

  const statsGrid = document.createElement("div");
  statsGrid.className = "grid";
  statsGrid.appendChild(makeMetric("Total PnL", formatPnL(props.summary.totalPnl), props.summary.totalPnl >= 0));
  statsGrid.appendChild(makeMetric("Wins", props.summary.wins));
  statsGrid.appendChild(makeMetric("Losses", props.summary.losses));
  statsGrid.appendChild(makeMetric("Avg latency", `${props.summary.avgLatency} ms`));

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  thead.innerHTML = "<tr><th>ID</th><th>Bot</th><th>Symbol</th><th>Side</th><th>Size</th><th>Entry</th><th>Exit</th><th>PnL</th><th>Latency</th><th>Time</th></tr>";
  const tbody = document.createElement("tbody");
  props.trades.forEach((trade) => {
    tbody.appendChild(renderTrade(trade));
  });
  table.appendChild(thead);
  table.appendChild(tbody);

  container.appendChild(header);
  container.appendChild(statsGrid);
  container.appendChild(table);
}

function makeMetric(label, value, isPositive = true) {
  const wrap = document.createElement("div");
  wrap.className = "card metric";
  const v = document.createElement("div");
  v.className = `value ${isPositive === true ? "positive" : isPositive === false ? "negative" : ""}`;
  v.textContent = value;
  const l = document.createElement("div");
  l.className = "label";
  l.textContent = label;
  wrap.appendChild(v);
  wrap.appendChild(l);
  return wrap;
}

function renderTrade(trade) {
  const tr = document.createElement("tr");
  const pnlClass = trade.pnl >= 0 ? "positive" : "negative";
  tr.innerHTML = `
    <td>${trade.id}</td>
    <td>${trade.bot}</td>
    <td>${trade.symbol}</td>
    <td>${trade.side}</td>
    <td class="number">${trade.size}</td>
    <td class="number">$${trade.entryPx.toLocaleString()}</td>
    <td class="number">$${trade.exitPx.toLocaleString()}</td>
    <td class="number ${pnlClass}">${formatPnL(trade.pnl)}</td>
    <td class="number">${trade.latencyMs} ms</td>
    <td>${formatTime(trade.timestamp)}</td>
  `;
  return tr;
}

function formatPnL(pnl) {
  const formatted = `$${Math.abs(pnl).toLocaleString()}`;
  return pnl >= 0 ? `+${formatted}` : `-${formatted}`;
}

function formatTime(iso) {
  const date = new Date(iso);
  return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}
