import { mountSummary } from "../views/summary/view.js";
import { mountBotTrades } from "../views/bot-trades/view.js";
import { mountServiceDetail } from "../views/service-detail/view.js";
import { mountMarket } from "../views/market/view.js";
import { mountAuth } from "../views/auth/view.js";

const state = {
  selected: "auth",
  selectedSymbol: "BTCUSDT",
  services: [
    {
      id: "dashboard",
      name: "DashboardViewService",
      domain: "overview",
      status: "healthy",
      latencyMs: 62,
      errorRate: 0.12,
      contracts: ["v1/dashboard"],
      desc: "Aggregates balances, open positions, PnL timeline.",
    },
    {
      id: "market",
      name: "MarketViewService",
      domain: "market",
      status: "healthy",
      latencyMs: 80,
      errorRate: 0.24,
      contracts: ["v1/markets", "ws:orderbook", "v1/market-chart"],
      desc: "Order book, price stream, chart + bot markers.",
    },
    {
      id: "portfolio",
      name: "PortfolioViewService",
      domain: "portfolio",
      status: "warning",
      latencyMs: 120,
      errorRate: 0.9,
      contracts: ["v1/positions"],
      desc: "Holdings, funding, withdrawal windows.",
    },
    {
      id: "bot-config",
      name: "BotConfigViewService",
      domain: "bots",
      status: "healthy",
      latencyMs: 75,
      errorRate: 0.2,
      contracts: ["v1/bots", "v1/venues"],
      desc: "Bot toggles, allocation controls, venue selection.",
    },
    {
      id: "auth",
      name: "AuthViewService",
      domain: "auth",
      status: "healthy",
      latencyMs: 55,
      errorRate: 0.05,
      contracts: ["v1/auth", "v1/keys"],
      desc: "Sign-in/up, MFA, key rotation prompts.",
    },
  ],
  authProps: {
    session: {
      status: "authenticated",
      mfa: true,
      apiKeys: ["staging: bapi_3ca2...d9bf"],
      environment: "staging",
    },
    user: {
      name: "Ops Admin",
      role: "admin",
      org: "r4r0",
    },
    controls: [
      { label: "Rotate active key", action: "rotate" },
      { label: "Lock session", action: "lock" },
      { label: "Sign out", action: "signout" },
    ],
  },
  trades: [
    {
      id: "TX-4812",
      bot: "Scalper X",
      symbol: "BTCUSDT",
      side: "long",
      size: 0.4,
      entryPx: 42320,
      exitPx: 42510,
      pnl: 76,
      result: "win",
      latencyMs: 118,
      timestamp: "2024-12-12T01:28:00Z",
    },
    {
      id: "TX-4811",
      bot: "Basis Keeper",
      symbol: "ETHUSDT",
      side: "short",
      size: 4.2,
      entryPx: 2284,
      exitPx: 2276,
      pnl: 33,
      result: "win",
      latencyMs: 102,
      timestamp: "2024-12-12T01:10:00Z",
    },
    {
      id: "TX-4810",
      bot: "Swing Theta",
      symbol: "SOLUSDT",
      side: "long",
      size: 140,
      entryPx: 83.2,
      exitPx: 82.1,
      pnl: -154,
      result: "loss",
      latencyMs: 214,
      timestamp: "2024-12-12T00:52:00Z",
    },
    {
      id: "TX-4809",
      bot: "Scalper X",
      symbol: "BTCUSDT",
      side: "short",
      size: 0.38,
      entryPx: 42110,
      exitPx: 42060,
      pnl: 19,
      result: "win",
      latencyMs: 95,
      timestamp: "2024-12-12T00:30:00Z",
    },
    {
      id: "TX-4808",
      bot: "Basis Keeper",
      symbol: "ETHUSDT",
      side: "long",
      size: 5.1,
      entryPx: 2270,
      exitPx: 2282,
      pnl: 61,
      result: "win",
      latencyMs: 110,
      timestamp: "2024-12-12T00:05:00Z",
    },
  ],
  markets: {
    symbols: [
      { symbol: "BTCUSDT", price: 42750, change: 1.3, volume: 1380 },
      { symbol: "ETHUSDT", price: 2284, change: 0.7, volume: 1022 },
      { symbol: "SOLUSDT", price: 82.7, change: -1.2, volume: 865 },
      { symbol: "XRPUSDT", price: 0.62, change: 0.4, volume: 410 },
    ],
    chart: {
      provider: "tradingview",
      symbol: "BINANCE:BTCUSDT",
      interval: "60",
      botMarkers: [
        { id: "m1", bot: "Scalper X", side: "buy", price: 42320, timestamp: "2024-12-12T01:28:00Z" },
        { id: "m2", bot: "Scalper X", side: "sell", price: 42510, timestamp: "2024-12-12T01:35:00Z" },
        { id: "m3", bot: "Swing Theta", side: "buy", price: 83.2, timestamp: "2024-12-12T00:52:00Z" },
        { id: "m4", bot: "Swing Theta", side: "sell", price: 82.1, timestamp: "2024-12-12T01:00:00Z" }
      ],
      candles: [
        { ts: 1702344000000, o: 42110, h: 42290, l: 42050, c: 42240 },
        { ts: 1702347600000, o: 42240, h: 42480, l: 42210, c: 42410 },
        { ts: 1702351200000, o: 42410, h: 42620, l: 42350, c: 42590 },
        { ts: 1702354800000, o: 42590, h: 42780, l: 42510, c: 42740 },
        { ts: 1702358400000, o: 42740, h: 42860, l: 42620, c: 42710 }
      ],
    },
    books: {
      BTCUSDT: {
        bids: [
          [42740.5, 1.2],
          [42732.4, 0.8],
          [42728.2, 0.6],
        ],
        asks: [
          [42755.2, 1.1],
          [42762.7, 0.7],
          [42771.5, 0.5],
        ],
        tape: [
          { side: "buy", px: 42751.2, qty: 0.22, ago: "12s" },
          { side: "sell", px: 42748.4, qty: 0.14, ago: "35s" },
          { side: "buy", px: 42755.1, qty: 0.32, ago: "1m" },
        ],
      },
      ETHUSDT: {
        bids: [
          [2283.4, 31],
          [2281.2, 24],
          [2278.9, 18],
        ],
        asks: [
          [2285.1, 28],
          [2286.9, 21],
          [2289.2, 16],
        ],
        tape: [
          { side: "buy", px: 2284.7, qty: 12, ago: "8s" },
          { side: "sell", px: 2283.2, qty: 8, ago: "26s" },
        ],
      },
      SOLUSDT: {
        bids: [
          [82.6, 120],
          [82.4, 84],
          [82.1, 64],
        ],
        asks: [
          [82.9, 108],
          [83.2, 72],
          [83.6, 51],
        ],
        tape: [
          { side: "sell", px: 82.8, qty: 210, ago: "15s" },
          { side: "buy", px: 82.7, qty: 180, ago: "48s" },
        ],
      },
      XRPUSDT: {
        bids: [
          [0.619, 18000],
          [0.618, 12000],
        ],
        asks: [
          [0.621, 17000],
          [0.622, 11000],
        ],
        tape: [
          { side: "buy", px: 0.621, qty: 32000, ago: "40s" },
        ],
      },
    },
  },
};

function render() {
  const app = document.getElementById("app");
  app.innerHTML = "";

  const shell = document.createElement("div");
  shell.className = "app";

  const sidebar = buildSidebar();
  const content = document.createElement("div");
  content.className = "content";

  content.appendChild(buildHero());

  const mainPanel = document.createElement("section");
  mainPanel.className = "panel";
  mainPanel.style.minHeight = "320px";
  mountSelected(mainPanel);
  content.appendChild(mainPanel);

  shell.appendChild(sidebar);
  shell.appendChild(content);
  app.appendChild(shell);
}

function buildSidebar() {
  const navItems = [{ id: "summary", label: "Summary" }, { id: "bot-trades", label: "Bot Trades" }, ...state.services.map((s) => ({ id: s.id, label: s.name }))];
  const sidebar = document.createElement("aside");
  sidebar.className = "sidebar";

  const header = document.createElement("header");
  const title = document.createElement("h3");
  title.textContent = "View Orchestrator";
  const sub = document.createElement("div");
  sub.className = "muted";
  sub.textContent = "Select a microservice to inspect";
  header.appendChild(title);
  header.appendChild(sub);

  const nav = document.createElement("div");
  nav.className = "nav";

  navItems.forEach((item) => {
    const btn = document.createElement("button");
    btn.className = state.selected === item.id ? "active" : "";
    btn.textContent = item.label;
    if (item.id === "bot-trades") {
      const pill = document.createElement("span");
      pill.className = "pill";
      pill.textContent = "key";
      btn.appendChild(pill);
    }
    btn.addEventListener("click", () => {
      state.selected = item.id;
      render();
    });
    nav.appendChild(btn);
  });

  sidebar.appendChild(header);
  sidebar.appendChild(nav);
  return sidebar;
}

function buildHero() {
  const hero = document.createElement("section");
  hero.className = "hero";
  const row = document.createElement("div");
  row.className = "row";

  const left = document.createElement("div");
  const title = document.createElement("h2");
  title.textContent = "r4r0 Frontend Mesh";
  const sub = document.createElement("div");
  sub.className = "muted";
  sub.textContent = "Microservice summaries + bot trade outcomes";
  left.appendChild(title);
  left.appendChild(sub);

  const tags = document.createElement("div");
  tags.className = "chips";
  tags.appendChild(makeChip("Contract-first"));
  tags.appendChild(makeChip("View-isolated"));
  tags.appendChild(makeChip("Bot trades prioritized"));

  row.appendChild(left);
  row.appendChild(tags);
  hero.appendChild(row);
  return hero;
}

function makeChip(label) {
  const chip = document.createElement("div");
  chip.className = "chip";
  chip.textContent = label;
  return chip;
}

function mountSelected(container) {
  if (state.selected === "summary") {
    mountSummary(container, {
      services: state.services,
      tradesSummary: summarizeTrades(state.trades),
    });
    return;
  }

  if (state.selected === "bot-trades") {
    mountBotTrades(container, {
      trades: state.trades,
      summary: summarizeTrades(state.trades),
    });
    return;
  }

  if (state.selected === "market") {
    mountMarket(container, composeMarketProps(state.markets, state.selectedSymbol, updateSelectedSymbol));
    return;
  }

  if (state.selected === "auth") {
    mountAuth(container, {
      ...state.authProps,
      onCreateKey: handleApiKeyCreate,
    });
    return;
  }

  const service = state.services.find((s) => s.id === state.selected);
  if (service) {
    mountServiceDetail(container, {
      service,
      health: {
        status: service.status,
        latencyMs: service.latencyMs,
        errorRate: service.errorRate,
        lastDeployed: "2024-12-11T23:50:00Z",
      },
      contracts: service.contracts,
      responsibilities: service.desc,
      dependencies: ["contracts/frontend/*.schema.json", "orchestrator events"],
    });
  }
}

function composeMarketProps(markets, selectedSymbol, onSymbolChange) {
  const book = markets.books[selectedSymbol] || { bids: [], asks: [], tape: [] };
  return {
    symbols: markets.symbols,
    selectedSymbol,
    book,
    chart: markets.chart,
    botMarkers: markets.chart?.botMarkers || [],
    onSymbolChange,
  };
}

function updateSelectedSymbol(symbol) {
  state.selectedSymbol = symbol;
  state.markets.chart = { ...state.markets.chart, symbol: `BINANCE:${symbol}` };
  render();
}

function handleApiKeyCreate(payload) {
  const env = payload.environment || state.authProps.session.environment;
  const masked = maskKey(payload.apiKey);
  const nextKeys = [formatKey(masked, env), ...state.authProps.session.apiKeys].slice(0, 5);
  state.authProps = {
    ...state.authProps,
    session: {
      ...state.authProps.session,
      apiKeys: nextKeys,
      environment: env,
    },
  };
  render();
}

function maskKey(key) {
  const val = (key || "").trim();
  if (val.length <= 8) return `${val.slice(0, 2)}***`;
  return `${val.slice(0, 4)}...${val.slice(-4)}`;
}

function formatKey(masked, env) {
  return `${env}: ${masked}`;
}

function summarizeTrades(trades) {
  const wins = trades.filter((t) => t.result === "win").length;
  const losses = trades.filter((t) => t.result === "loss").length;
  const totalPnl = trades.reduce((acc, t) => acc + t.pnl, 0);
  const avgLatency = trades.length ? Math.round(trades.reduce((acc, t) => acc + t.latencyMs, 0) / trades.length) : 0;
  return { wins, losses, totalPnl, avgLatency };
}

document.addEventListener("DOMContentLoaded", render);
