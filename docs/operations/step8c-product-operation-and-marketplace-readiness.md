# Aegis Product Operation and Marketplace-Readiness Runbook

Date: 2026-07-02
Baseline commit: `a8eb75d7711c3598b31779f07f800de9cb5e3b0b`
Operating posture: local, dry-run, and mock only

## 1. Product Purpose

> Other agents can hire Aegis before they execute.

> Aegis returns BLOCK, WAIT, or EXECUTE with proof.

Aegis Risk Oracle is a chain-agnostic pre-trade risk oracle, risk-check API,
DeFAI safety agent, and agent-to-agent risk guard. A requester or execution
agent submits a proposed action before taking that action. Aegis returns a
decision, risk score, reasons, suggested action, and deterministic hash-linked
evidence.

Aegis checks risk before execution; Aegis does not execute. It is not a
trading bot, execution bot, swap bot, wallet manager, signal seller, profit
generator, or private-key agent. `EXECUTE` is a favorable risk classification,
not transaction authorization and not evidence that any transaction occurred.

## 2. Safe Local Operation

### Preconditions

- Use the repository checkout intended for local validation.
- Keep secrets and `.env` files outside the repository.
- Keep `CAP_MODE=mock`; do not set real-provider or lifecycle-action flags.
- Confirm `git status --short --branch` is clean.
- Install dependencies once, if needed:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### One-command local start

From the repository root, run exactly:

```powershell
$env:CAP_MODE = "mock"; .\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

Expected Web Console URL:

`http://127.0.0.1:8000/`

This starts the FastAPI application only. It does not start a CROO provider
listener, WebSocket probe, negotiation, payment, or paid-order workflow.

### Health and posture checks

In a second PowerShell window:

```powershell
$baseUrl = "http://127.0.0.1:8000"
$health = Invoke-RestMethod -Uri "$baseUrl/health"
$cap = Invoke-RestMethod -Uri "$baseUrl/cap/status"
$health | Format-List
$cap | Format-List
```

Expected local baseline:

| Check | Expected value |
| --- | --- |
| `GET /health` HTTP status | `200` |
| `status` | `healthy` |
| `service` | `aegis-risk-oracle` |
| `mode` | `dry-run` |
| `GET /cap/status` HTTP status | `200` |
| `cap_mode` | `mock` |
| `real_cap_ready` | `false` |
| `adapter_status` | `MOCK_ONLY` |

Stop if the service is not healthy, `cap_mode` is not `mock`, or
`real_cap_ready` is not `false`. Do not troubleshoot by enabling real CAP
settings.

## 3. Customer Validation Path

1. Open `http://127.0.0.1:8000/`.
2. In **Runtime posture**, confirm health is reported directly by `/health`.
3. Confirm `/cap/status` reports `CAP_MODE=mock` and
   `real_cap_ready=false`. Confirm the console also displays
   `live_execution_authorized=false` and `mutating_methods_called=false`.
4. Open **Risk Check Console** and select one of the deterministic scenarios.
5. Choose **Run risk check**.
6. Inspect the text decision, `risk_score`, `safe_to_execute`, confidence,
   market regime, reasons, risk factors, and suggested action.
7. Inspect and copy the full proof hashes and `policy_version`. A displayed
   shortened hash must copy its complete value.
8. Treat the output as risk advice for a separately controlled caller. Do not
   interpret any result as execution, payment, delivery, or settlement.

## 4. Deterministic Service Validation Scenarios

The Web Console scenarios use the same complete request except for
`market_signal.volatility_24h`. These outcomes were verified before the Step
8-B merge:

| Scenario | Volatility | Expected score | Expected decision | Downstream meaning |
| --- | ---: | ---: | --- | --- |
| Safest available low-risk | `2` | `0` | `EXECUTE` | Favorable risk advice; simulated action only |
| Elevated volatility | `8` | `35` | `WAIT` | Pause the simulated action |
| Critical volatility | `12` | `70` | `BLOCK` | Refuse the simulated action |

Base request:

```json
{
  "token": "BNB",
  "chain": "bsc",
  "intended_action": "buy",
  "size_usd": 100,
  "market_signal": {
    "price_change_24h": 3.4,
    "volume_change_24h": 8.1,
    "liquidity_usd": 500000,
    "volatility_24h": 2,
    "slippage_bps": 40,
    "gas_level": "medium"
  },
  "portfolio_context": {
    "current_exposure_usd": 250,
    "max_position_usd": 1000
  }
}
```

PowerShell validation:

```powershell
$baseUrl = "http://127.0.0.1:8000"
$request = @{
  token = "BNB"
  chain = "bsc"
  intended_action = "buy"
  size_usd = 100
  market_signal = @{
    price_change_24h = 3.4
    volume_change_24h = 8.1
    liquidity_usd = 500000
    volatility_24h = 2
    slippage_bps = 40
    gas_level = "medium"
  }
  portfolio_context = @{
    current_exposure_usd = 250
    max_position_usd = 1000
  }
}

foreach ($scenario in @(
  @{ Name = "EXECUTE"; Volatility = 2; ExpectedScore = 0 },
  @{ Name = "WAIT"; Volatility = 8; ExpectedScore = 35 },
  @{ Name = "BLOCK"; Volatility = 12; ExpectedScore = 70 }
)) {
  $request.market_signal.volatility_24h = $scenario.Volatility
  $body = $request | ConvertTo-Json -Depth 5
  $result = Invoke-RestMethod -Method Post -Uri "$baseUrl/risk-check" `
    -ContentType "application/json" -Body $body
  [pscustomobject]@{
    Scenario = $scenario.Name
    Decision = $result.decision
    RiskScore = $result.risk_score
    ExpectedScore = $scenario.ExpectedScore
    SafeToExecute = $result.safe_to_execute
  }
}
```

If policy or fixtures change later, validate actual behavior before presenting
an `EXECUTE` scenario. WAIT and BLOCK are the safer default validation paths
when a deterministic low-risk result is not established.

## 5. A2A Integration Workflow

The integration contract is deliberately caller-controlled:

1. A requester or execution agent constructs a proposed action.
2. Before any simulated action, it calls `POST /a2a/mock-order` or
   `POST /risk-check`.
3. It branches on Aegis output:
   - `BLOCK` maps to `REFUSED` and the simulated action stops.
   - `WAIT` maps to `DELAYED` and the simulated action pauses.
   - `EXECUTE` maps to `SIMULATED_EXECUTION_ONLY`.
4. The caller records the decision and proof. No transaction is submitted.

Example:

```powershell
$a2aBody = @{
  buyer_agent_id = "builder-agent"
  requested_action = $request
} | ConvertTo-Json -Depth 6

Invoke-RestMethod -Method Post -Uri "$baseUrl/a2a/mock-order" `
  -ContentType "application/json" -Body $a2aBody
```

Expected response fields include `buyer_agent_id`, `aegis_decision`,
`risk_score`, `safe_to_execute`, `mock_execution_status`, `reason`,
`risk_factors`, and `proof`.

This workflow contains no real trade, wallet, private key, signing, swap,
transaction construction, or broadcast.

## 6. Local Order and Proof Workflow

The local order API is an in-memory CAP-shaped contract test. Data disappears
when the app restarts. Its mock lifecycle labels do not prove a real CAP
lifecycle.

### `POST /orders` — Create a local order

```powershell
$orderBody = @{
  requester_agent_id = "builder-agent"
  provider_agent_id = "aegis-risk-oracle"
  service_id = "aegis-risk-check"
  service_name = "Aegis Risk Check"
  sla_minutes = 5
  price_usdc = 0.12
  requirements_type = "schema"
  deliverable_type = "schema"
  request = $request
} | ConvertTo-Json -Depth 7

$order = Invoke-RestMethod -Method Post -Uri "$baseUrl/orders" `
  -ContentType "application/json" -Body $orderBody
$order | ConvertTo-Json -Depth 8
```

### `GET /orders/{order_id}` and `GET /proof/{proof_id}` — Retrieve evidence

```powershell
$savedOrder = Invoke-RestMethod -Uri "$baseUrl/orders/$($order.order_id)"
$savedProof = Invoke-RestMethod -Uri "$baseUrl/proof/$($order.proof_id)"
$savedOrder | ConvertTo-Json -Depth 8
$savedProof | ConvertTo-Json -Depth 5
```

Verify these proof fields:

- `proof_id`
- `order_id`
- `request_hash`
- `response_hash`
- `result_hash` (also described generically as the proof/result hash)
- `policy_version`
- `created_at`

The local proof is a deterministic delivery log attestation, not an on-chain
proof. `NEGOTIATED_MOCK`, `LOCKED_MOCK`, and `CLEARED_MOCK` are simulation
labels. No funds are charged, locked, escrowed, cleared, or settled.

## 7. CROO Store Readiness Checklist

### Listing draft

| Item | Current marketplace-ready wording |
| --- | --- |
| Service name | Aegis Risk Check |
| One-liner | Pre-trade risk oracle that returns BLOCK, WAIT, or EXECUTE with proof before a caller acts. |
| Pilot price | 0.12 USDC per call; positioning only until real payment is separately verified |
| Target track | Data & Verification Agents |
| Target track | DeFi / On-chain Ops Agents |
| Requirements format | Schema |
| Deliverable format | Schema |
| Draft SLA | 5-minute service window; draft only, not a production availability guarantee |

### Input schema summary

- Required: `token`, `chain`, `intended_action`, and non-negative `size_usd`.
- Optional market evidence: price change, volume change, liquidity,
  volatility, slippage, and gas level.
- Optional portfolio evidence: current exposure and maximum position.
- The caller is responsible for truthful, current, correctly scoped inputs.

### Output schema summary

- `decision`: BLOCK, WAIT, or EXECUTE.
- `risk_score`: integer from 0 to 100.
- `confidence`, `market_regime`, and `safe_to_execute`.
- Structured `risk_factors`, human-readable `reasons`, and
  `suggested_action`.
- Deterministic proof metadata for audit and correlation.

### Proof schema

The direct risk response includes `request_hash`, `response_hash`, and
`policy_version`. The local order proof additionally includes `proof_id`,
`order_id`, `result_hash`, and `created_at`. Hashes are evidence links, not
payment receipts, escrow records, settlement evidence, or on-chain proofs.

### Buyer/requester expectations

- Call Aegis before a separately controlled action.
- Treat BLOCK as stop, WAIT as pause/review, and EXECUTE as favorable risk
  advice only.
- Retain the request, response, proof identifiers, hashes, and policy version.
- Do not delegate wallet custody, signing, or execution to Aegis.
- Do not treat the pilot price or draft SLA as proof of a completed commercial
  transaction or production service level.

## 8. Honest CAP Boundary

Aegis has a **CAP-ready gated runtime**. The current truthful state is:

- `CAP_MODE=mock` by default.
- `real_cap_ready=false`.
- `live_execution_authorized=false`.
- `mutating_methods_called=false`.
- Real payment is not claimed.
- Real escrow is not claimed.
- Real delivery is not claimed.
- Real settlement is not claimed.
- Commercial readiness is not claimed until it is separately verified.

CAP-ready means local contracts and guarded boundaries exist. It does not mean
Aegis is online in the CROO Store, accepting real orders, or verified across a
paid lifecycle.

## 9. Deployment-Readiness Checklist

### Allowed local configuration

- Set `CAP_MODE=mock` explicitly or rely on its mock default.
- Bind only to the intended host and port; use `127.0.0.1:8000` for this local
  runbook.
- Keep non-secret deployment settings in the deployment environment.
- Keep every real-provider, listener, accept/reject, paid-order, and delivery
  gate unset or false.

### Secrets and real-mode configuration

- Never commit secrets, API keys, private keys, `.env` files, or secret-bearing
  logs.
- Future CROO credentials, if separately approved, must be injected from an
  external secret store or environment and must never be printed.
- The presence of credentials or `CAP_MODE=real` alone is not authorization to
  start a provider listener or perform a CAP action.

### Deployment gate

- [ ] Git working tree is clean and the intended commit is recorded.
- [ ] Full tests and capability scans pass in the deployment candidate review.
- [ ] `GET /health` is healthy.
- [ ] `GET /cap/status` reports mock mode and `real_cap_ready=false`.
- [ ] Dry-run/read-only posture is documented for operators and users.
- [ ] No wallet, signing, swap, transaction, broadcast, or live-trading path
      exists.
- [ ] No real CAP activity is enabled without a separate, explicit approval.
- [ ] Logs and captured evidence contain no secrets.
- [ ] Rollback and process-stop procedures are available for the target host.

This checklist supports deploy readiness of the local/mock callable service.
It does not authorize or certify real CAP operation.

## 10. Submission and Video Walkthrough

### Under-five-minute sequence

1. **0:00–0:30 — Positioning:** Show the hero and state that other agents can
   hire Aegis before they execute. State that Aegis checks risk but never
   executes.
2. **0:30–1:00 — Runtime posture:** Show live `/health` and `/cap/status`.
   Point out mock mode and the three false safety/readiness flags.
3. **1:00–2:15 — Decisions:** Run EXECUTE, WAIT, and BLOCK presets. Show the
   deterministic 0/35/70 scores and explain each caller-controlled branch.
4. **2:15–2:50 — Evidence:** Show reasons, factors, policy version, and copy a
   complete 64-character hash.
5. **2:50–3:30 — A2A composability:** Run the mock A2A request and show
   REFUSED, DELAYED, or SIMULATED_EXECUTION_ONLY behavior.
6. **3:30–4:15 — Local order/proof:** Create an in-memory local order, then
   retrieve its order and proof IDs. Call out every `_MOCK` state.
7. **4:15–4:50 — Marketplace fit:** Show the 0.12 USDC pilot positioning,
   target tracks, schema contract, and readiness matrix.
8. **4:50–5:00 — Honest close:** State the CAP and commercial boundaries.

### Do not claim in the video walkthrough

- A real payment, escrow, delivery, settlement, reputation update, or paid
  order.
- Commercial readiness or a production SLA.
- Guaranteed safety, profit, trading signals, or live execution.
- Wallet custody, signing, swaps, transaction construction, or broadcasting.
- CROO Store online/accepting-orders status unless separately verified later.

## 11. Known Limitations and Next Steps

- Real CROO/CAP credentials and production connectivity remain pending and must
  stay outside the repository.
- A real paid-order lifecycle has not been verified or claimed.
- The order ledger is process-local and in-memory.
- The proof is a local log attestation, not on-chain proof.
- The 0.12 USDC price and five-minute SLA are marketplace positioning drafts,
  not evidence of payment or production service performance.
- Any future one-event real negotiation observation requires separate explicit
  approval and the existing fail-closed gates. This runbook does not grant that
  approval.

Recommended follow-on work is a separately reviewed deploy-target checklist
and recording script that continue to use only local/mock endpoints. Do not
start a real provider listener, probe, negotiation, or paid order as part of
that work.
