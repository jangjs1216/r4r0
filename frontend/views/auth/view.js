export function mountAuth(container, props) {
  container.innerHTML = "";

  const header = document.createElement("div");
  header.className = "panel-header";
  const title = document.createElement("div");
  title.className = "panel-title";
  title.textContent = "Auth & Binance API Keys";
  const subtitle = document.createElement("div");
  subtitle.className = "panel-subtitle";
  subtitle.textContent = "MFA status, environment, and a safe path to inject exchange keys without persisting to disk.";
  header.appendChild(title);
  header.appendChild(subtitle);

  const layout = document.createElement("div");
  layout.className = "grid";
  layout.style.gridTemplateColumns = "2fr 3fr";

  layout.appendChild(renderSessionCard(props.session, props.user));
  layout.appendChild(renderKeyForm(props.session.environment, props.onCreateKey));

  const guideRow = document.createElement("div");
  guideRow.className = "grid";
  guideRow.appendChild(renderGuidelines());
  guideRow.appendChild(renderControls(props.controls));

  container.appendChild(header);
  container.appendChild(layout);
  container.appendChild(guideRow);
}

function renderSessionCard(session, user) {
  const card = document.createElement("div");
  card.className = "card";

  const top = document.createElement("div");
  top.className = "row";
  const left = document.createElement("div");
  const title = document.createElement("div");
  title.className = "panel-title";
  title.textContent = user.name || "Authenticated user";
  const subtitle = document.createElement("div");
  subtitle.className = "panel-subtitle";
  subtitle.textContent = `${user.role || "member"} @ ${user.org || "—"}`;
  left.appendChild(title);
  left.appendChild(subtitle);

  const badge = document.createElement("div");
  badge.className = `status ${statusTone(session.status)}`;
  badge.textContent = session.status;

  top.appendChild(left);
  top.appendChild(badge);

  const grid = document.createElement("div");
  grid.className = "grid";
  grid.style.gridTemplateColumns = "repeat(auto-fit, minmax(160px, 1fr))";
  grid.appendChild(makeMetric("Environment", session.environment));
  grid.appendChild(makeMetric("MFA", session.mfa ? "Enabled" : "Disabled"));
  grid.appendChild(makeMetric("API keys", session.apiKeys.length));

  const keys = document.createElement("div");
  keys.className = "list";
  const keysTitle = document.createElement("div");
  keysTitle.className = "panel-subtitle";
  keysTitle.textContent = "Existing keys (masked, stored in backend vault)";
  keys.appendChild(keysTitle);
  if (!session.apiKeys.length) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "No exchange keys linked yet.";
    keys.appendChild(empty);
  } else {
    session.apiKeys.forEach((k) => {
      const row = document.createElement("div");
      row.className = "row";
      const label = document.createElement("div");
      label.textContent = k;
      const tag = document.createElement("span");
      tag.className = "pill subtle";
      tag.textContent = "vaulted";
      row.appendChild(label);
      row.appendChild(tag);
      keys.appendChild(row);
    });
  }

  card.appendChild(top);
  card.appendChild(grid);
  card.appendChild(keys);
  return card;
}

function renderKeyForm(environment, onCreateKey) {
  const card = document.createElement("div");
  card.className = "card";

  const title = document.createElement("div");
  title.className = "panel-title";
  title.textContent = "Add Binance API key (vault-only)";
  const subtitle = document.createElement("div");
  subtitle.className = "panel-subtitle";
  subtitle.textContent = "Secret is kept in-memory for this request only, sent to Auth service → secrets manager, never written to disk.";

  const form = document.createElement("form");
  form.className = "form";

  const apiKey = buildField("API Key", "text", "BINANCE_API_KEY");
  const apiSecret = buildField("Secret", "password", "BINANCE_API_SECRET");
  const envSelect = buildSelect(environment);

  const controls = document.createElement("div");
  controls.className = "row";
  controls.style.justifyContent = "flex-start";
  controls.style.gap = "10px";

  const submit = document.createElement("button");
  submit.type = "submit";
  submit.className = "btn primary";
  submit.textContent = "Send to Auth service";

  const reset = document.createElement("button");
  reset.type = "reset";
  reset.className = "btn ghost";
  reset.textContent = "Clear";

  controls.appendChild(submit);
  controls.appendChild(reset);

  const note = document.createElement("div");
  note.className = "note";
  note.textContent = "On submit, secret is discarded after posting to backend contract (e.g., POST /v1/keys).";

  form.appendChild(apiKey.field);
  form.appendChild(apiSecret.field);
  form.appendChild(envSelect.field);
  form.appendChild(controls);
  form.appendChild(note);

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const payload = {
      apiKey: apiKey.input.value.trim(),
      apiSecret: apiSecret.input.value.trim(),
      environment: envSelect.select.value,
    };

    if (!payload.apiKey || !payload.apiSecret) {
      note.textContent = "API key and secret are required.";
      note.classList.add("warn");
      return;
    }

    if (typeof onCreateKey === "function") {
      onCreateKey(payload);
    }

    note.classList.remove("warn");
    note.textContent = "Submitted to Auth service; secret not retained in the view.";
    form.reset();
    envSelect.select.value = environment || "staging";
  });

  card.appendChild(title);
  card.appendChild(subtitle);
  card.appendChild(form);
  return card;
}

function renderGuidelines() {
  const card = document.createElement("div");
  card.className = "card";
  const title = document.createElement("div");
  title.className = "panel-title";
  title.textContent = "Key handling playbook";
  const list = document.createElement("ul");
  list.className = "bullet-list";
  [
    "Use MFA + least-privilege exchange keys; rotate on schedule.",
    "Send secrets to Auth service → secrets manager (Vault/ASM), never commit to repo or disk.",
    "Keep per-environment keys separate; prefer IP-allowlisting and withdrawal locks.",
    "Emit audit events on create/rotate/revoke; surface last used time in UI.",
  ].forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  });

  card.appendChild(title);
  card.appendChild(list);
  return card;
}

function renderControls(controls) {
  const card = document.createElement("div");
  card.className = "card";
  const title = document.createElement("div");
  title.className = "panel-title";
  title.textContent = "Auth controls";

  const wrap = document.createElement("div");
  wrap.className = "chips";
  (controls || []).forEach((control) => {
    const chip = document.createElement("button");
    chip.className = "chip ghost";
    chip.type = "button";
    chip.textContent = control.label;
    chip.addEventListener("click", () => {
      // In a real impl this would emit an orchestrator event.
    });
    wrap.appendChild(chip);
  });

  if (!controls || !controls.length) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "No controls configured.";
    wrap.appendChild(empty);
  }

  card.appendChild(title);
  card.appendChild(wrap);
  return card;
}

function buildField(label, type, placeholder) {
  const field = document.createElement("label");
  field.className = "field";
  const span = document.createElement("span");
  span.textContent = label;
  const input = document.createElement("input");
  input.type = type;
  input.placeholder = placeholder;
  field.appendChild(span);
  field.appendChild(input);
  return { field, input };
}

function buildSelect(environment) {
  const field = document.createElement("label");
  field.className = "field";
  const span = document.createElement("span");
  span.textContent = "Environment";
  const select = document.createElement("select");
  ["staging", "production"].forEach((env) => {
    const opt = document.createElement("option");
    opt.value = env;
    opt.textContent = env;
    if (environment === env) opt.selected = true;
    select.appendChild(opt);
  });
  field.appendChild(span);
  field.appendChild(select);
  return { field, select };
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
  if (status === "authenticated") return "ok";
  if (status === "locked") return "warn";
  return "bad";
}
