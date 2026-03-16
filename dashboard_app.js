const statusLabel = document.getElementById("status-label");
const refreshButton = document.getElementById("refresh-btn");
const summaryGrid = document.getElementById("summary-grid");
const performanceTables = document.getElementById("performance-tables");
const intelligenceGrid = document.getElementById("intelligence-grid");
const reportsList = document.getElementById("reports-list");
const reportSearchInput = document.getElementById("report-search");
const probabilityBlocks = document.getElementById("probability-blocks");
const openPositionsContainer = document.getElementById("open-positions");
const decisionOutput = document.getElementById("decision-output");

const REFRESH_INTERVAL = 5000;
let refreshTimer;

const summaryFields = [
  { label: "Market Open", getter: (s) => (s.market_open ? "Yes" : "No") },
  { label: "Entry Allowed", getter: (s) => (s.entry_allowed ? "Yes" : "No") },
  { label: "Best Index", getter: (s) => s.best_index || "N/A" },
  { label: "Rotation Reason", getter: (s) => s.rotation_reason || "N/A" },
  { label: "Min Confidence", getter: (s) => s.min_confidence ?? "N/A" },
  { label: "Runtime Profile", getter: (s) => s.active_runtime_profile || "BASE" },
  { label: "Threshold Min", getter: (s) => s.auto_tune_min_confidence ?? "N/A" },
];

const performanceSections = [
  { title: "Regime Performance", key: "regime_stats" },
  { title: "IV Performance", key: "iv_stats" },
  { title: "Time Performance", key: "time_stats" },
  { title: "Risk Efficiency", key: "risk_efficiency" },
  { title: "Duration Stats", key: "duration_stats" },
];

const intelligenceFields = [
  { label: "Total Trades", key: "total_trades" },
  { label: "Win Rate", key: "win_rate", suffix: "%" },
  { label: "Expectancy", key: "expectancy" },
  { label: "Growth Rate", key: "growth_rate", suffix: "%" },
  { label: "Best Confidence", key: "best_confidence_zone" },
];

refreshButton.addEventListener("click", () => {
  runUpdate(true);
});

function clearTimer() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }
}

function setTimer() {
  clearTimer();
  refreshTimer = setInterval(() => runUpdate(false), REFRESH_INTERVAL);
}

function humanValue(value) {
  if (value === undefined || value === null || value === "") {
    return "N/A";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? value : value.toFixed(2);
  }
  return String(value);
}

function renderEvolution(evalData, configData) {
  const evolutionGrid = document.getElementById("evolution-grid");
  if (!evolutionGrid) return;
  evolutionGrid.innerHTML = "";

  const live = evalData.live || {};
  const replay = evalData.replay || {};

  const fields = [
    { label: "Active Config Version", value: configData.version || "N/A" },
    { label: "Live Win Rate", value: live.win_rate !== undefined ? live.win_rate + "%" : "N/A" },
    { label: "Live Trades", value: live.total_trades || 0 },
    { label: "Live Expectancy", value: live.expectancy !== undefined ? live.expectancy : "N/A" },
    { label: "Replay Win Rate", value: replay.win_rate !== undefined ? replay.win_rate + "%" : "N/A" },
    { label: "Replay Trades", value: replay.total_trades || 0 },
    { label: "Target Multiplier", value: configData.target_multiplier || "N/A" },
    { label: "Min Confidence", value: configData.min_confidence || "N/A" }
  ];

  fields.forEach(({ label, value }) => {
    const cell = document.createElement("div");
    cell.className = "kv";
    const prefix = document.createElement("span");
    prefix.textContent = label;
    const strong = document.createElement("strong");
    strong.textContent = value;
    cell.appendChild(prefix);
    cell.appendChild(strong);
    evolutionGrid.appendChild(cell);
  });
}

function renderSummary(state) {
  summaryGrid.innerHTML = "";
  summaryFields.forEach(({ label, getter }) => {
    const cell = document.createElement("div");
    cell.className = "kv";
    const prefix = document.createElement("span");
    prefix.textContent = label;
    const value = document.createElement("strong");
    value.textContent = humanValue(getter(state));
    cell.appendChild(prefix);
    cell.appendChild(value);
    summaryGrid.appendChild(cell);
  });
}

function renderDecision(state) {
  const decision = state.decision_output || {};
  const targets = decision.targets || {};
  const optionPlan = decision.option_plan || {};
  const reasons = Array.isArray(decision.reasons) ? decision.reasons : [];
  const rationale = Array.isArray(decision.rationale) ? decision.rationale : [];
  const diagnostics = decision.diagnostics || {};

  decisionOutput.innerHTML = `
    <div class="decision-hero">
      <div>
        <span class="tag">${decision.action || "NO-TRADE"}</span>
        <h3>${decision.headline || "No trade"}</h3>
        <p class="decision-summary">${decision.summary || "Market scan in progress."}</p>
      </div>
      <div class="decision-metrics">
        <div class="kv"><span>Symbol</span><strong>${humanValue(decision.symbol)}</strong></div>
        <div class="kv"><span>Bias</span><strong>${humanValue(decision.bias)}</strong></div>
        <div class="kv"><span>Regime</span><strong>${humanValue(decision.regime)}</strong></div>
        <div class="kv"><span>Confidence</span><strong>${humanValue(decision.confidence)}%</strong></div>
        <div class="kv"><span>Grade</span><strong>${humanValue(decision.grade)}</strong></div>
        <div class="kv"><span>Risk</span><strong>${humanValue(decision.risk_status)}</strong></div>
      </div>
    </div>
    <div class="decision-grid">
      <div class="table-wrap">
        <h3>Trade Plan</h3>
        <div class="kv-grid">
          <div class="kv"><span>Spot</span><strong>${humanValue(decision.spot)}</strong></div>
          <div class="kv"><span>Entry</span><strong>${humanValue(targets.entry)}</strong></div>
          <div class="kv"><span>Stop</span><strong>${humanValue(targets.stop)}</strong></div>
          <div class="kv"><span>Target</span><strong>${humanValue(targets.target)}</strong></div>
          <div class="kv"><span>Strike</span><strong>${humanValue(optionPlan.strike)}</strong></div>
          <div class="kv"><span>Option Type</span><strong>${humanValue(optionPlan.option_type)}</strong></div>
        </div>
      </div>
      <div class="table-wrap">
        <h3>Blockers / Reasons</h3>
        <ul class="reason-list">
          ${reasons.length ? reasons.map((reason) => `<li>${reason}</li>`).join("") : "<li>No active blockers.</li>"}
        </ul>
      </div>
      <div class="table-wrap">
        <h3>Rationale</h3>
        <ul class="reason-list">
          ${rationale.length ? rationale.map((item) => `<li>${item}</li>`).join("") : "<li>Rationale not available.</li>"}
        </ul>
      </div>
      <div class="table-wrap">
        <h3>Diagnostics</h3>
        <div class="kv-grid">
          <div class="kv"><span>ML Win%</span><strong>${humanValue(diagnostics.ml_win_probability)}</strong></div>
          <div class="kv"><span>IV Regime</span><strong>${humanValue(diagnostics.iv_regime)}</strong></div>
          <div class="kv"><span>Current IV</span><strong>${humanValue(diagnostics.current_iv)}</strong></div>
          <div class="kv"><span>OI Bias</span><strong>${humanValue(diagnostics.oi_bias)}</strong></div>
          <div class="kv"><span>Order Flow</span><strong>${humanValue(diagnostics.order_flow_bias)}</strong></div>
          <div class="kv"><span>Risk %</span><strong>${humanValue(diagnostics.risk_pct)}</strong></div>
        </div>
      </div>
    </div>
  `;
}

function renderTables(state) {
  performanceTables.innerHTML = "";
  performanceSections.forEach(({ title, key }) => {
    const data = state.intelligence_stats?.[key] || {};
    if (!data || Object.keys(data).length === 0) {
      const empty = document.createElement("p");
      empty.textContent = `${title} (no data yet)`;
      empty.className = "muted";
      const wrapper = document.createElement("div");
      wrapper.appendChild(empty);
      performanceTables.appendChild(wrapper);
      return;
    }
    const tableWrap = document.createElement("div");
    const heading = document.createElement("h3");
    heading.textContent = title;
    tableWrap.appendChild(heading);
    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headerRow.innerHTML = "<th>Key</th><th>Value</th>";
    thead.appendChild(headerRow);
    const tbody = document.createElement("tbody");
    Object.entries(data)
      .sort((a, b) => {
        const aVal = typeof a[1] === "number" ? a[1] : parseFloat(a[1]) || 0;
        const bVal = typeof b[1] === "number" ? b[1] : parseFloat(b[1]) || 0;
        return bVal - aVal;
      })
      .forEach(([key, value]) => {
        const row = document.createElement("tr");
        const keyCell = document.createElement("td");
        keyCell.textContent = key;
        const valueCell = document.createElement("td");
        valueCell.textContent = humanValue(value);
        row.appendChild(keyCell);
        row.appendChild(valueCell);
        tbody.appendChild(row);
      });
    table.appendChild(thead);
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    performanceTables.appendChild(tableWrap);
  });
}

function renderIntelligence(state) {
  intelligenceGrid.innerHTML = "";
  intelligenceFields.forEach(({ label, key, suffix = "" }) => {
    const cell = document.createElement("div");
    cell.className = "kv";
    const prefix = document.createElement("span");
    prefix.textContent = label;
    const value = document.createElement("strong");
    value.textContent = `${humanValue(state.intelligence_stats?.[key])}${suffix}`;
    cell.appendChild(prefix);
    cell.appendChild(value);
    intelligenceGrid.appendChild(cell);
  });

  if (state.live_setup_probability) {
    const setup = state.live_setup_probability;
    const extra = document.createElement("div");
    extra.className = "kv";
    extra.innerHTML = `
      <span>Live Setup</span>
      <strong>${humanValue(setup.win_probability)}% win (${humanValue(setup.expectancy_r)}R)</strong>
      <span class="muted">${humanValue(setup.sample_size)} samples · ${setup.source || "unknown source"}</span>
    `;
    intelligenceGrid.appendChild(extra);
  }
}

function buildProbabilityBlock(title, data) {
  const block = document.createElement("div");
  block.className = "table-wrap";
  const heading = document.createElement("h3");
  heading.textContent = title;
  block.appendChild(heading);
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  thead.innerHTML = "<tr><th>Key</th><th>Samples</th><th>Win%</th><th>Exp R</th></tr>";
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  Object.entries(data || {}).forEach(([key, stats]) => {
    const row = document.createElement("tr");
    const label = document.createElement("td");
    label.textContent = key;
    const samples = document.createElement("td");
    samples.textContent = humanValue(stats.sample_size);
    const winProb = document.createElement("td");
    winProb.textContent = `${humanValue(stats.win_probability)}%`;
    const expectancy = document.createElement("td");
    expectancy.textContent = humanValue(stats.expectancy_r);
    row.append(label, samples, winProb, expectancy);
    tbody.appendChild(row);
  });
  table.appendChild(tbody);
  block.appendChild(table);
  return block;
}

function renderProbability(state) {
  probabilityBlocks.innerHTML = "";
  if (state.live_ml_probability?.available) {
    const mlBlock = document.createElement("div");
    mlBlock.className = "kv";
    mlBlock.innerHTML = `
      <span>ML Win Chance</span>
      <strong>${humanValue(state.live_ml_probability.win_probability)}%</strong>
      <span class="muted">${state.live_ml_probability.samples_total || "0"} samples · ${state.live_ml_probability.model_version || "v?"}</span>
    `;
    probabilityBlocks.appendChild(mlBlock);
  }
  if (state.live_meta_label?.available) {
    const metaBlock = document.createElement("div");
    metaBlock.className = "kv";
    metaBlock.innerHTML = `
      <span>Meta Recommendation</span>
      <strong>${state.live_meta_label.recommendation || "N/A"}</strong>
      <span class="muted">${humanValue(state.live_meta_label.take_quality_probability)}% chance</span>
    `;
    probabilityBlocks.appendChild(metaBlock);
  }

  const probabilityModel = state.intelligence_stats?.probability_model || {};
  const global = probabilityModel.global || {};
  if (global && Object.keys(global).length) {
    const globalBlock = document.createElement("div");
    globalBlock.className = "kv";
    globalBlock.innerHTML = `
      <span>Probability Model</span>
      <strong>${humanValue(global.win_probability)}% win (${humanValue(global.expectancy_r)}R)</strong>
      <span class="muted">${humanValue(global.sample_size)} samples</span>
    `;
    probabilityBlocks.appendChild(globalBlock);
  }
  if (probabilityModel.by_confidence) {
    probabilityBlocks.appendChild(buildProbabilityBlock("By Confidence", probabilityModel.by_confidence));
  }
  if (probabilityModel.by_regime) {
    probabilityBlocks.appendChild(buildProbabilityBlock("By Regime", probabilityModel.by_regime));
  }
  if (probabilityModel.by_iv_regime) {
    probabilityBlocks.appendChild(buildProbabilityBlock("By IV Regime", probabilityModel.by_iv_regime));
  }
}

function renderOpenPositions(state) {
  openPositionsContainer.innerHTML = "";
  const positions = state.open_positions || [];
  if (!positions.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No open trades detected.";
    openPositionsContainer.appendChild(empty);
    return;
  }

  const table = document.createElement("table");
  const thead = document.createElement("thead");
  thead.innerHTML =
    "<tr><th>Symbol</th><th>Option</th><th>Dir</th><th>Entry</th><th>Current</th><th>Stop</th><th>Target</th><th>Floating PnL</th><th>Lots</th></tr>";
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  const livePrice = state.live_price;
  const fallbackPrice = state.selected_option_meta?.last_price;
  positions.forEach((pos) => {
    const strikeLabel = `${humanValue(pos.strike)} ${pos.option_type || ""}`.trim();
    const currentLabel = humanValue(pos.current_price ?? livePrice ?? fallbackPrice);
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${pos.index || pos.symbol || "N/A"}</td>
      <td>${strikeLabel}</td>
      <td>${pos.direction || "N/A"}</td>
      <td>${humanValue(pos.entry)}</td>
      <td>${currentLabel}</td>
      <td>${humanValue(pos.stop)}</td>
      <td>${humanValue(pos.target)}</td>
      <td>${humanValue(pos.floating_pnl)}</td>
      <td>${humanValue(pos.lots)}</td>
    `;
    tbody.appendChild(row);
  });
  table.appendChild(tbody);
  const wrapper = document.createElement("div");
  wrapper.className = "table-wrap";
  wrapper.appendChild(table);
  openPositionsContainer.appendChild(wrapper);
}

let allReports = [];

function renderReports(reports) {
  if (!reportsList) return;
  reportsList.innerHTML = "";
  if (!reports || reports.length === 0) {
    const empty = document.createElement("div");
    empty.className = "no-reports";
    empty.textContent = "No reports found.";
    reportsList.appendChild(empty);
    return;
  }

  reports.forEach((report) => {
    const item = document.createElement("div");
    item.className = "report-item";
    item.innerHTML = `
      <h3>${report.title}</h3>
      <p>${report.content}</p>
      <div class="report-meta">
        <span class="report-category tag">${report.category}</span>
      </div>
    `;
    reportsList.appendChild(item);
  });
}

function handleSearch() {
  const query = reportSearchInput.value.toLowerCase().trim();
  if (!query) {
    renderReports(allReports);
    return;
  }

  const filtered = allReports.filter((r) => {
    return (
      (r.title && r.title.toLowerCase().includes(query)) ||
      (r.content && r.content.toLowerCase().includes(query)) ||
      (r.category && r.category.toLowerCase().includes(query))
    );
  });
  renderReports(filtered);
}

if (reportSearchInput) {
  reportSearchInput.addEventListener("input", handleSearch);
}

async function runUpdate(userInitiated) {
  try {
    const response = await fetch("/api/runtime-state");
    if (!response.ok) {
      throw new Error("Runtime data not ready yet.");
    }
    const state = await response.json();
    statusLabel.textContent = `Updated ${new Date(state.served_at_utc).toLocaleTimeString("en-IN", {
      timeZone: "Asia/Kolkata",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    })}`;
    renderSummary(state);
    renderDecision(state);
    renderTables(state);
    renderIntelligence(state);

    // Fetch new endpoints
    try {
      const evalRes = await fetch("/api/evaluation-stats");
      const configRes = await fetch("/api/config-status");
      if(evalRes.ok && configRes.ok) {
        const evalData = await evalRes.json();
        const configData = await configRes.json();
        renderEvolution(evalData, configData);
      }
    } catch(e) {
      console.warn("Could not fetch evolution data", e);
    }

    allReports = state.intelligence_reports || [];
    // Only update list if user isn't currently searching to avoid resetting view
    if (reportSearchInput && !reportSearchInput.value.trim()) {
      renderReports(allReports);
    }

    renderProbability(state);
    renderOpenPositions(state);
  } catch (error) {
    statusLabel.textContent = error.message;
  }
}

// Chat UI Logic
const chatHistory = document.getElementById("chat-history");
const chatInput = document.getElementById("chat-input");
const chatSendBtn = document.getElementById("chat-send-btn");

function addMessage(text, isUser = false) {
  const msg = document.createElement("p");
  msg.className = isUser ? "user-msg" : "bot-msg";
  msg.textContent = text;
  chatHistory.appendChild(msg);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

async function sendChat() {
  const query = chatInput.value.trim();
  if (!query) return;

  addMessage(query, true);
  chatInput.value = "";

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query }),
    });
    const data = await response.json();
    addMessage(data.response, false);
  } catch (err) {
    addMessage("Error: Could not connect to AI Agent. Is the server running?", false);
  }
}

chatSendBtn.addEventListener("click", sendChat);
chatInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") sendChat();
});

runUpdate(false);
setTimer();
