export function mountSummary(container, props) {
  container.innerHTML = "";

  const header = document.createElement("div");
  header.className = "panel-header";
  const title = document.createElement("div");
  title.className = "panel-title";
  title.textContent = "Summary";
  const subtitle = document.createElement("div");
  subtitle.className = "panel-subtitle";
  subtitle.textContent = "Service health + bot trade KPIs";
  header.appendChild(title);
  header.appendChild(subtitle);

  const serviceGrid = document.createElement("div");
  serviceGrid.className = "grid";

  props.services.forEach((service) => {
    serviceGrid.appendChild(renderServiceCard(service));
  });

  const tradesCard = document.createElement("div");
  tradesCard.className = "card";
  const tradesTitle = document.createElement("div");
  tradesTitle.className = "panel-title";
  tradesTitle.textContent = "Bot trade KPIs";
  const stats = props.tradesSummary;
  const rows = document.createElement("div");
  rows.className = "grid";
  rows.style.gridTemplateColumns = "repeat(auto-fit, minmax(160px, 1fr))";
  rows.appendChild(makeMetric("Total PnL", formatPnL(stats.totalPnl)));
  rows.appendChild(makeMetric("Wins", stats.wins));
  rows.appendChild(makeMetric("Losses", stats.losses));
  rows.appendChild(makeMetric("Avg latency", `${stats.avgLatency} ms`));
  tradesCard.appendChild(tradesTitle);
  tradesCard.appendChild(rows);

  container.appendChild(header);
  container.appendChild(serviceGrid);
  container.appendChild(tradesCard);
}

function renderServiceCard(service) {
  const card = document.createElement("div");
  card.className = "card";

  const top = document.createElement("div");
  top.className = "row";
  const title = document.createElement("div");
  title.textContent = service.name;
  const status = document.createElement("span");
  status.className = `status ${statusTone(service.status)}`;
  status.textContent = service.status;
  top.appendChild(title);
  top.appendChild(status);

  const desc = document.createElement("div");
  desc.className = "panel-subtitle";
  desc.textContent = service.desc;

  const metrics = document.createElement("div");
  metrics.className = "grid";
  metrics.style.gridTemplateColumns = "repeat(auto-fit, minmax(140px, 1fr))";
  metrics.appendChild(makeMetric("Latency p50", `${service.latencyMs} ms`));
  metrics.appendChild(makeMetric("Error rate", `${service.errorRate}%`));
  metrics.appendChild(makeMetric("Contracts", service.contracts.join(", ")));

  card.appendChild(top);
  card.appendChild(desc);
  card.appendChild(metrics);
  return card;
}

function makeMetric(label, value) {
  const wrap = document.createElement("div");
  wrap.className = "metric";
  const v = document.createElement("div");
  v.className = "value";
  v.textContent = value;
  const l = document.createElement("div");
  l.className = "label";
  l.textContent = label;
  wrap.appendChild(v);
  wrap.appendChild(l);
  return wrap;
}

function statusTone(status) {
  if (status === "healthy") return "ok";
  if (status === "warning") return "warn";
  return "bad";
}

function formatPnL(pnl) {
  const formatted = `$${Math.round(Math.abs(pnl)).toLocaleString()}`;
  return pnl >= 0 ? `+${formatted}` : `-${formatted}`;
}
