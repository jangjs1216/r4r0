export function mountServiceDetail(container, props) {
  container.innerHTML = "";

  const header = document.createElement("div");
  header.className = "panel-header";
  const title = document.createElement("div");
  title.className = "panel-title";
  title.textContent = props.service.name;
  const subtitle = document.createElement("div");
  subtitle.className = "panel-subtitle";
  subtitle.textContent = props.responsibilities;
  header.appendChild(title);
  header.appendChild(subtitle);

  const grid = document.createElement("div");
  grid.className = "grid";
  grid.appendChild(makeMetric("Status", props.health.status, tone(props.health.status)));
  grid.appendChild(makeMetric("Latency p50", `${props.health.latencyMs} ms`));
  grid.appendChild(makeMetric("Error rate", `${props.health.errorRate}%`));
  grid.appendChild(makeMetric("Last deploy", formatTime(props.health.lastDeployed)));

  const contracts = document.createElement("div");
  contracts.className = "card";
  const cTitle = document.createElement("div");
  cTitle.className = "panel-title";
  cTitle.textContent = "Contracts";
  const cList = document.createElement("div");
  cList.className = "chips";
  props.contracts.forEach((c) => {
    const chip = document.createElement("div");
    chip.className = "chip";
    chip.textContent = c;
    cList.appendChild(chip);
  });
  contracts.appendChild(cTitle);
  contracts.appendChild(cList);

  const dependencies = document.createElement("div");
  dependencies.className = "card";
  const dTitle = document.createElement("div");
  dTitle.className = "panel-title";
  dTitle.textContent = "Dependencies (read-only)";
  const dList = document.createElement("div");
  dList.className = "panel-subtitle";
  dList.textContent = props.dependencies.join(", ");
  dependencies.appendChild(dTitle);
  dependencies.appendChild(dList);

  container.appendChild(header);
  container.appendChild(grid);
  container.appendChild(contracts);
  container.appendChild(dependencies);
}

function makeMetric(label, value, toneClass) {
  const card = document.createElement("div");
  card.className = "card metric";
  const v = document.createElement("div");
  v.className = `value ${toneClass || ""}`;
  v.textContent = value;
  const l = document.createElement("div");
  l.className = "label";
  l.textContent = label;
  card.appendChild(v);
  card.appendChild(l);
  return card;
}

function tone(status) {
  if (status === "healthy") return "positive";
  if (status === "warning") return "warn";
  return "negative";
}

function formatTime(iso) {
  const date = new Date(iso);
  return date.toLocaleString();
}
