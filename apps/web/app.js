"use strict";

const SAMPLE_REQUEST = {
  token: "BNB",
  chain: "bsc",
  intended_action: "buy",
  size_usd: 100,
  market_signal: {
    price_change_24h: 3.4,
    volume_change_24h: 8.1,
    liquidity_usd: 500000,
    volatility_24h: 2,
    slippage_bps: 40,
    gas_level: "medium",
  },
  portfolio_context: {
    current_exposure_usd: 250,
    max_position_usd: 1000,
  },
};

const RISK_SCENARIOS = Object.freeze({
  execute: {
    note: "Complete evidence with low volatility. Submit to ask the oracle.",
    request: SAMPLE_REQUEST,
  },
  wait: {
    note: "Volatility is elevated to 8. Submit to ask the oracle.",
    request: {
      ...SAMPLE_REQUEST,
      market_signal: { ...SAMPLE_REQUEST.market_signal, volatility_24h: 8 },
    },
  },
  block: {
    note: "Volatility is critical at 12. Submit to ask the oracle.",
    request: {
      ...SAMPLE_REQUEST,
      market_signal: { ...SAMPLE_REQUEST.market_signal, volatility_24h: 12 },
    },
  },
});

const elements = Object.fromEntries(
  [
    "refresh-status", "health-status", "health-service", "cap-mode",
    "real-cap-ready", "adapter-status", "sdk-status",
    "live-execution-authorized", "mutating-methods-called", "status-message",
    "pill-health", "pill-cap-mode",
    "risk-form", "risk-request", "risk-error", "reset-risk", "run-risk", "scenario-note",
    "risk-result", "risk-decision", "risk-score", "risk-confidence",
    "risk-regime", "risk-safe", "risk-reasons", "risk-factors",
    "risk-action", "risk-request-hash", "risk-response-hash",
    "risk-result-hash", "risk-policy-version", "run-a2a", "a2a-result",
    "a2a-status", "a2a-decision", "a2a-execution", "a2a-score", "a2a-reason",
    "create-order", "fetch-order", "fetch-proof", "order-id", "proof-id",
    "order-result", "proof-result", "order-status", "order-output",
    "proof-proof-id", "proof-order-id", "proof-request-hash",
    "proof-response-hash", "proof-result-hash", "proof-policy-version",
    "proof-created-at", "order-message",
  ].map((id) => [id, document.getElementById(id)]),
);

function setText(node, value, fallback = "Not reported") {
  if (node) node.textContent = value == null || value === "" ? fallback : String(value);
}

function setCopyValue(node, value) {
  if (!node) return;
  const fullValue = value == null || value === "" ? "Not reported" : String(value);
  node.dataset.fullValue = fullValue;
  node.title = fullValue;
  node.textContent = fullValue.length > 32
    ? fullValue.slice(0, 14) + "…" + fullValue.slice(-14)
    : fullValue;
}

function clearNode(node) {
  while (node?.firstChild) node.removeChild(node.firstChild);
}

function makeElement(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value != null) node.textContent = String(value);
  return node;
}

function boundedError(error) {
  const message = error instanceof Error ? error.message : "Request failed.";
  return message.slice(0, 240);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg).filter(Boolean).join("; ")
      : body.detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return body;
}

function parseRiskRequest() {
  try {
    const value = JSON.parse(elements["risk-request"].value);
    if (!value || Array.isArray(value) || typeof value !== "object") {
      throw new Error("Request must be a JSON object.");
    }
    setText(elements["risk-error"], "", "");
    return value;
  } catch (error) {
    setText(elements["risk-error"], boundedError(error), "");
    throw error;
  }
}

function setBusy(container, control, isBusy, busyLabel) {
  container?.setAttribute("aria-busy", String(isBusy));
  if (!control) return;
  if (!control.dataset.label) control.dataset.label = control.textContent;
  control.disabled = isBusy;
  control.textContent = isBusy ? busyLabel : control.dataset.label;
}

function setMessage(node, message, isError = false) {
  setText(node, message, "");
  node?.classList.toggle("request-state--error", isError);
}

function setFlowState(container, state) {
  container?.setAttribute("data-flow-state", state);
}

function setPill(node, text, tone) {
  if (!node) return;
  const dot = node.querySelector(".pill__dot");
  node.textContent = "";
  if (dot) node.appendChild(dot);
  else node.appendChild(makeElement("span", "pill__dot"));
  node.appendChild(document.createTextNode(text));
  node.dataset.tone = tone;
}

function renderList(node, values, emptyMessage) {
  clearNode(node);
  const items = Array.isArray(values) && values.length ? values : [emptyMessage];
  for (const value of items) node.appendChild(makeElement("li", "", value));
}

function renderFactors(node, factors) {
  clearNode(node);
  if (!Array.isArray(factors) || factors.length === 0) {
    node.appendChild(makeElement("p", "muted", "No risk factors reported."));
    return;
  }
  for (const factor of factors) {
    const item = makeElement("article", "factor");
    const heading = makeElement("div", "factor__heading");
    heading.appendChild(makeElement("strong", "", factor.name));
    heading.appendChild(makeElement("span", `severity severity--${factor.severity}`, factor.severity));
    item.appendChild(heading);
    item.appendChild(makeElement("p", "", factor.evidence));
    item.appendChild(makeElement("small", "", `Score impact +${factor.score_impact}`));
    node.appendChild(item);
  }
}

function setDecision(value) {
  const decision = String(value || "READY").toUpperCase();
  setText(elements["risk-decision"], decision);
  elements["risk-result"].dataset.decision = decision;
  elements["risk-decision"].className = "decision-badge";
  if (["BLOCK", "WAIT", "EXECUTE"].includes(decision)) {
    elements["risk-decision"].classList.add(`decision-badge--${decision.toLowerCase()}`);
  }
}

function renderRiskResult(result) {
  setDecision(result.decision);
  setText(elements["risk-score"], result.risk_score);
  setText(elements["risk-confidence"], result.confidence);
  setText(elements["risk-regime"], result.market_regime);
  setText(elements["risk-safe"], result.safe_to_execute);
  renderList(elements["risk-reasons"], result.reasons, "No reasons reported.");
  renderFactors(elements["risk-factors"], result.risk_factors);
  setText(elements["risk-action"], result.suggested_action);
  setCopyValue(elements["risk-request-hash"], result.proof?.request_hash);
  setCopyValue(elements["risk-response-hash"], result.proof?.response_hash);
  setCopyValue(elements["risk-result-hash"], result.proof?.result_hash || result.proof?.proof_hash);
  setText(elements["risk-policy-version"], result.proof?.policy_version);
}

function renderProof(proof) {
  setText(elements["proof-proof-id"], proof?.proof_id);
  setText(elements["proof-order-id"], proof?.order_id);
  setCopyValue(elements["proof-request-hash"], proof?.request_hash);
  setCopyValue(elements["proof-response-hash"], proof?.response_hash);
  setCopyValue(elements["proof-result-hash"], proof?.result_hash);
  setText(elements["proof-policy-version"], proof?.policy_version);
  setText(elements["proof-created-at"], proof?.created_at);
}

async function refreshStatus() {
  setBusy(null, elements["refresh-status"], true, "Refreshing…");
  setMessage(elements["status-message"], "Reading local API posture…");
  setPill(elements["pill-health"], "API …", "neutral");
  setPill(elements["pill-cap-mode"], "CAP MODE …", "neutral");
  try {
    const [health, cap] = await Promise.all([
      apiRequest("/health"),
      apiRequest("/cap/status"),
    ]);
    setText(elements["health-status"], health.status || "healthy");
    setText(elements["health-service"], health.service || "/health");
    setText(elements["cap-mode"], cap.cap_mode);
    setText(elements["real-cap-ready"], cap.real_cap_ready);
    setText(elements["adapter-status"], cap.adapter_status);
    setText(elements["sdk-status"], cap.sdk_import_status);
    setText(elements["live-execution-authorized"], false);
    setText(elements["mutating-methods-called"], false);
    const healthy = (health.status || "").toLowerCase() === "healthy";
    setPill(elements["pill-health"], healthy ? "API HEALTHY" : "API " + (health.status || "UNKNOWN").toUpperCase(), healthy ? "safe" : "warning");
    setPill(elements["pill-cap-mode"], "CAP MODE " + String(cap.cap_mode || "unknown").toUpperCase(), cap.cap_mode === "mock" ? "neutral" : "warning");
    setMessage(elements["status-message"], "Local posture refreshed. Missing values remain unverified.");
  } catch (error) {
    setText(elements["health-status"], "unavailable");
    setText(elements["adapter-status"], "unavailable");
    setPill(elements["pill-health"], "API DOWN", "error");
    setPill(elements["pill-cap-mode"], "CAP MODE UNKNOWN", "error");
    setMessage(elements["status-message"], boundedError(error), true);
  } finally {
    setBusy(null, elements["refresh-status"], false, "Refreshing…");
  }
}

async function runRiskCheck(event) {
  event.preventDefault();
  let request;
  try {
    request = parseRiskRequest();
  } catch (_error) {
    return;
  }
  setBusy(elements["risk-result"], elements["run-risk"], true, "Checking risk…");
  setFlowState(elements["risk-result"], "loading");
  try {
    renderRiskResult(await apiRequest("/risk-check", {
      method: "POST",
      body: JSON.stringify(request),
    }));
    setFlowState(elements["risk-result"], "success");
  } catch (error) {
    setText(elements["risk-error"], boundedError(error), "");
    setFlowState(elements["risk-result"], "error");
  } finally {
    setBusy(elements["risk-result"], elements["run-risk"], false, "Checking risk…");
  }
}

async function runMockA2A() {
  let request;
  try {
    request = parseRiskRequest();
  } catch (_error) {
    return;
  }
  setBusy(elements["a2a-result"], elements["run-a2a"], true, "Running mock…");
  setText(elements["a2a-status"], "RUNNING");
  setFlowState(elements["a2a-result"], "loading");
  try {
    const result = await apiRequest("/a2a/mock-order", {
      method: "POST",
      body: JSON.stringify({ buyer_agent_id: "web-console-agent", requested_action: request }),
    });
    setText(elements["a2a-status"], "COMPLETE");
    setText(elements["a2a-decision"], result.aegis_decision);
    setText(elements["a2a-execution"], result.mock_execution_status);
    setText(elements["a2a-score"], result.risk_score);
    setText(elements["a2a-reason"], result.reason);
    setFlowState(elements["a2a-result"], "success");
  } catch (error) {
    setText(elements["a2a-status"], "ERROR");
    setText(elements["a2a-reason"], boundedError(error));
    setFlowState(elements["a2a-result"], "error");
  } finally {
    setBusy(elements["a2a-result"], elements["run-a2a"], false, "Running mock…");
  }
}

function localOrderRequest() {
  return {
    requester_agent_id: "web-console-agent",
    provider_agent_id: "aegis-risk-oracle",
    service_id: "aegis-risk-check",
    service_name: "Aegis Risk Check",
    sla_minutes: 5,
    price_usdc: 0.12,
    requirements_type: "schema",
    deliverable_type: "schema",
    request: parseRiskRequest(),
  };
}

function renderOrder(order) {
  setText(elements["order-status"], order.status || "COMPLETE");
  setText(elements["order-output"], JSON.stringify(order, null, 2));
  setText(elements["order-id"], order.order_id, "");
  setText(elements["proof-id"], order.proof_id, "");
  renderProof(order.proof);
}

async function createLocalOrder() {
  let request;
  try {
    request = localOrderRequest();
  } catch (_error) {
    return;
  }
  setBusy(elements["order-result"], elements["create-order"], true, "Creating local order…");
  setMessage(elements["order-message"], "Creating an in-memory mock order…");
  setFlowState(elements["order-result"], "loading");
  setFlowState(elements["proof-result"], "loading");
  try {
    const order = await apiRequest("/orders", { method: "POST", body: JSON.stringify(request) });
    renderOrder(order);
    setMessage(elements["order-message"], "Local mock order and delivery proof created. No external action occurred.");
    setFlowState(elements["order-result"], "success");
    setFlowState(elements["proof-result"], "success");
  } catch (error) {
    setText(elements["order-status"], "ERROR");
    setMessage(elements["order-message"], boundedError(error), true);
    setFlowState(elements["order-result"], "error");
    setFlowState(elements["proof-result"], "error");
  } finally {
    setBusy(elements["order-result"], elements["create-order"], false, "Creating local order…");
  }
}

async function fetchOrder() {
  const orderId = elements["order-id"].value.trim();
  if (!orderId) return setMessage(elements["order-message"], "Enter an order ID.", true);
  setBusy(elements["order-result"], elements["fetch-order"], true, "Fetching…");
  setFlowState(elements["order-result"], "loading");
  try {
    renderOrder(await apiRequest(`/orders/${encodeURIComponent(orderId)}`));
    setMessage(elements["order-message"], "Local order retrieved.");
    setFlowState(elements["order-result"], "success");
  } catch (error) {
    setMessage(elements["order-message"], boundedError(error), true);
    setFlowState(elements["order-result"], "error");
  } finally {
    setBusy(elements["order-result"], elements["fetch-order"], false, "Fetching…");
  }
}

async function fetchProof() {
  const proofId = elements["proof-id"].value.trim();
  if (!proofId) return setMessage(elements["order-message"], "Enter a proof ID.", true);
  setBusy(elements["proof-result"], elements["fetch-proof"], true, "Fetching…");
  setFlowState(elements["proof-result"], "loading");
  try {
    renderProof(await apiRequest(`/proof/${encodeURIComponent(proofId)}`));
    setMessage(elements["order-message"], "Local delivery proof retrieved.");
    setFlowState(elements["proof-result"], "success");
  } catch (error) {
    setMessage(elements["order-message"], boundedError(error), true);
    setFlowState(elements["proof-result"], "error");
  } finally {
    setBusy(elements["proof-result"], elements["fetch-proof"], false, "Fetching…");
  }
}

function selectScenario(button) {
  const scenario = RISK_SCENARIOS[button?.dataset.scenario];
  if (!scenario) return;
  elements["risk-request"].value = JSON.stringify(scenario.request, null, 2);
  setText(elements["scenario-note"], scenario.note);
  setText(elements["risk-error"], "", "");
  for (const option of document.querySelectorAll("[data-scenario]")) {
    option.setAttribute("aria-pressed", String(option === button));
  }
}

async function copyValue(button) {
  const source = document.getElementById(button.dataset.copy);
  if (!source) return;
  const original = button.textContent;
  try {
    await navigator.clipboard.writeText(source.dataset.fullValue || source.textContent);
    button.textContent = "Copied";
    button.setAttribute("aria-label", "Copied " + source.id);
  } catch (_error) {
    button.textContent = "Copy unavailable";
    button.setAttribute("aria-label", "Copy unavailable for " + source.id);
  }
  window.setTimeout(() => {
    button.textContent = original;
    button.setAttribute("aria-label", "Copy " + source.id);
  }, 1400);
}

selectScenario(document.querySelector('[data-scenario="execute"]'));
elements["risk-form"].addEventListener("submit", runRiskCheck);
elements["reset-risk"].addEventListener("click", () => {
  selectScenario(document.querySelector('[data-scenario="execute"]'));
});
for (const button of document.querySelectorAll("[data-scenario]")) {
  button.addEventListener("click", () => selectScenario(button));
}
elements["refresh-status"].addEventListener("click", refreshStatus);
elements["run-a2a"].addEventListener("click", runMockA2A);
elements["create-order"].addEventListener("click", createLocalOrder);
elements["fetch-order"].addEventListener("click", fetchOrder);
elements["fetch-proof"].addEventListener("click", fetchProof);
for (const button of document.querySelectorAll("[data-copy]")) {
  button.addEventListener("click", () => copyValue(button));
}

refreshStatus();
