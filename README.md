# Aegis Risk Oracle

> Pre-trade risk oracle that returns `BLOCK`, `WAIT`, or `EXECUTE` with proof
> before a caller acts.

Aegis is a chain-agnostic risk-check API, DeFAI safety agent, agent-to-agent
risk guard, and paid callable-service candidate for CROO Agent Commerce. A
requester submits a proposed action and supporting evidence. Aegis applies a
deterministic policy and returns a decision, score, reasons, suggested action,
and hash-linked proof.

**Aegis checks risk before execution. Aegis does not execute.** `EXECUTE` is a
favorable risk classification, not transaction authorization and not evidence
that an action occurred.

## What Aegis does

- Evaluates a proposed action before a separately controlled caller acts.
- Returns `BLOCK`, `WAIT`, or `EXECUTE` with structured reasons and risk factors.
- Gives agents a small JSON contract for pre-action risk checks.
- Produces deterministic request and response hashes for correlation and audit.
- Supports a local mock A2A flow and an in-memory order/proof contract.

## What Aegis does not do

Aegis is not a trading bot, execution bot, swap bot, wallet manager, signal
seller, profit generator, or private-key agent. It has no wallet custody,
private-key handling, signing, swap, transaction construction, broadcast, or
live-trading path. It does not promise profit or guaranteed safety.

## Architecture and CROO/CAP integration

```text
Requester agent                Aegis Core (this repo)              CROO backend
────────────────                ─────────────────────              ─────────────
                                 apps/api (FastAPI)
                                   risk-check, health, Web Console
                                 src/aegis_croo/oracle + guards
                                   deterministic BLOCK/WAIT/EXECUTE
                                 src/aegis_croo/orders
                                   local ledger + SHA-256 proof

  scripts/croo_requester_canary.py        scripts/croo_provider_presence.py -----> WebSocket (real, live-verified)
  (separate SDK key, gated,                 always-on, non-mutating, ONLINE
   never run live in this repo)             reproduced live

                                          scripts/croo_provider_lifecycle.py ---> negotiate/accept/pay/deliver
                                          src/aegis_croo/cap/provider_lifecycle_   (real SDK calls, offline-tested,
                                            runtime.py + delivery_mapping.py       never run live in this repo)
```

Aegis Core (the oracle, guards, and local order/proof ledger) is fully
local, deterministic, and unaffected by whether any CROO connection exists.
CROO integration is layered strictly on top of it, split into two
independently gated pieces:

1. **Provider presence** (`src/aegis_croo/cap/provider_presence_runtime.py`,
   `scripts/croo_provider_presence.py`) — a non-mutating WebSocket connection
   that registers no event handler. This is the only piece that has been run
   against the real CROO backend, and it reproduced the Agent's Dashboard
   ONLINE status for as long as the connection stayed open.
2. **Lifecycle wiring** (`src/aegis_croo/cap/provider_lifecycle_runtime.py`,
   `src/aegis_croo/cap/delivery_mapping.py`, `scripts/croo_provider_lifecycle.py`,
   `scripts/croo_requester_canary.py`) — narrow, explicitly gated code that can
   accept one negotiation and deliver one result via the real `croo-sdk`
   (`accept_negotiation`, `deliver_order`), correlated against a Service ID
   and requester Agent ID allowlist with in-memory, single-order idempotency.
   This is fully implemented and covered by fake-SDK tests, but it has never
   been run against the real CROO backend: no funded, separately-keyed
   requester Agent exists yet to negotiate and pay for a real order.

## Current product status

Real means a live call against the actual CROO backend occurred and was
observed. Offline-tested means the code path is implemented and proven
against fake SDK clients only, with zero live network calls.

| Capability | Status | Meaning |
| --- | --- | --- |
| Risk-check API and Web Console | Real, local | Calls the deterministic local oracle, always live |
| Provider WebSocket presence (ONLINE) | **Real, live-verified** | A real `connect_websocket()` session against the CROO backend reproduced the Agent's Dashboard status flipping OFFLINE → ONLINE for the duration of the connection, and back to OFFLINE on close |
| Real CAP lifecycle wiring (negotiate/accept/pay/deliver) | **Implemented, offline-tested only** | Gated code exists to accept a negotiation and deliver a result via the official `croo-sdk`; proven only against fake SDK clients in the test suite, never run against the live CROO backend |
| Real paid CAP order | **Not completed** | No funded requester Agent exists yet; no negotiation, payment, or delivery has ever been exchanged with the real CROO backend |
| A2A requester flow | Local mock | Caller branches on advice; no external action occurs |
| Local order and proof flow | In-memory mock | CAP-shaped contract test; records disappear on restart |
| CAP adapter (`/cap/order`, `/cap/status`) | Gated local mock | `CAP_MODE=mock` by default; real mode only probes SDK client construction, never mutates |

The required safety posture remains, unless a separately owner-approved
canary is explicitly and narrowly enabled for a bounded test:

```text
CAP_MODE=mock
real_cap_ready=false
live_execution_authorized=false
mutating_methods_called=false
```

Aegis does not claim real payment, escrow, settlement, or production
readiness anywhere in this document.

## Quickstart for Windows PowerShell

Prerequisites: Python 3.11 or newer, Git, and PowerShell.

```powershell
git clone https://github.com/tonielivegood/aegis-croo
Set-Location Aegis-CROO
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:CAP_MODE = "mock"
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

The public repository URL above has been verified for anonymous access. If the
repository is already checked out, start at `Set-Location` with its local path.

Open the local Web Console at <http://127.0.0.1:8000/>. This starts only the
FastAPI application. It does not start a CROO provider listener, negotiation,
payment, delivery, or settlement flow.

## API surface

| Method | Path | Purpose | Current posture |
| --- | --- | --- | --- |
| `GET` | `/` | Serve the Web Console | Local |
| `GET` | `/health` | Report service health and dry-run mode | Local |
| `POST` | `/risk-check` | Evaluate a proposed action | Local core API |
| `POST` | `/a2a/mock-order` | Demonstrate caller-to-Aegis composition | Local mock only |
| `POST` | `/orders` | Create an in-memory CAP-shaped order record | Local mock only |
| `GET` | `/orders/{order_id}` | Retrieve an in-memory order record | Local mock only |
| `GET` | `/proof/{proof_id}` | Retrieve a local delivery log attestation | Local mock only |
| `GET` | `/cap/status` | Report mock/real readiness gates | Read-only posture |
| `POST` | `/cap/order` | Adapt a CAP-shaped request into the local order flow | Local mock only; real mode fails closed |

Invalid request bodies return the normal FastAPI/Pydantic validation response
and no risk decision.

## Risk-check request and response

This complete low-risk fixture deterministically returns `EXECUTE` with score
`0` under policy `aegis-risk-oracle-v0.1`:

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

Call it from a second PowerShell window:

```powershell
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
$body = $request | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/risk-check `
  -ContentType application/json -Body $body
```

Representative response shape:

```json
{
  "decision": "EXECUTE",
  "risk_score": 0,
  "confidence": "high",
  "market_regime": "safe_small_buy",
  "safe_to_execute": true,
  "risk_factors": [],
  "reasons": [
    "No guard identified elevated risk in the supplied evidence."
  ],
  "suggested_action": "EXECUTE means the risk decision is acceptable; Aegis performs no transaction or execution.",
  "proof": {
    "request_hash": "<64-character SHA-256>",
    "response_hash": "<64-character SHA-256>",
    "policy_version": "aegis-risk-oracle-v0.1"
  }
}
```

The hash placeholders above represent deterministic 64-character values
returned by the running service; they are not fabricated evidence.
`safe_to_execute` is advice for the caller, never authorization.

### All three decisions, from the same running service

`BLOCK` — negative 24h volume change combined with high volatility:

```json
{
  "decision": "BLOCK",
  "risk_score": 70,
  "confidence": "high",
  "market_regime": "volatile_buy",
  "safe_to_execute": false,
  "risk_factors": [
    {"name": "high_volatility", "severity": "medium", "score_impact": 35,
     "evidence": "24h volatility is 9.0, at or above 7.0."},
    {"name": "negative_volume_confirmation", "severity": "medium", "score_impact": 35,
     "evidence": "Buy signal has negative 24h volume change of -10.0%."}
  ],
  "suggested_action": "BLOCK this proposed action and reassess the flagged risk evidence."
}
```

`WAIT` — missing an important market-signal field (`liquidity_usd`):

```json
{
  "decision": "WAIT",
  "risk_score": 35,
  "confidence": "low",
  "market_regime": "missing_data",
  "safe_to_execute": false,
  "risk_factors": [
    {"name": "missing_liquidity", "severity": "medium", "score_impact": 35,
     "evidence": "Liquidity data is missing from the market signal."}
  ],
  "suggested_action": "WAIT for stronger or more complete evidence before proceeding."
}
```

All three responses above were captured from a locally running instance of
this exact repository state; none are hypothetical.

## Proof and hash semantics

Aegis exposes two related local proof shapes:

| Proof | Fields | Meaning |
| --- | --- | --- |
| Direct risk proof | `request_hash`, `response_hash`, `policy_version` | Links the canonical request to the policy-scoped response |
| Local order proof | `proof_id`, `order_id`, `request_hash`, `response_hash`, `result_hash`, `policy_version`, `deliverable_type`, `created_at` | Links an in-memory order record to its local deliverable |

All hashes are SHA-256 evidence links over canonical local payloads. They are
local delivery/log attestations, not on-chain proofs, payment receipts, escrow
records, settlement evidence, or proof of commercial readiness. Store the
original request and response with their hashes; a hash alone does not explain
the decision.

## Agent-to-agent workflow

The composition contract keeps the caller in control:

1. A requester or execution-capable agent constructs a proposed action.
2. Before acting, it calls `POST /risk-check` or `POST /a2a/mock-order`.
3. Aegis returns a decision, reasons, risk factors, and proof.
4. The caller branches on the result:

| Aegis decision | Mock A2A status | Caller meaning |
| --- | --- | --- |
| `BLOCK` | `REFUSED` | Stop the proposed action |
| `WAIT` | `DELAYED` | Pause for stronger evidence or review |
| `EXECUTE` | `SIMULATED_EXECUTION_ONLY` | Favorable risk advice; caller controls any later action |

5. The caller records the decision and proof. Aegis submits nothing.

Run the existing local requester demonstration while the API is running:

```powershell
.\.venv\Scripts\python.exe examples\mock_buyer_agent_demo.py
```

## Local order and proof workflow

`POST /orders` accepts requester/provider IDs, service metadata, provisional
price and SLA fields, schema types, and a nested risk request. It applies the
same oracle, creates an in-memory order, and returns `order_id`, `proof_id`, the
risk deliverable, and local lifecycle labels.

Retrieve the result with `GET /orders/{order_id}` and its proof with
`GET /proof/{proof_id}`. The mock lifecycle labels
`NEGOTIATED_MOCK`, `LOCKED_MOCK`, `DELIVERED`, and `CLEARED_MOCK` describe a
local contract simulation only. No funds or external deliverables move, and
records disappear when the process restarts.

The current marketplace positioning is **0.12 USDC per call for a pilot** with
a **draft five-minute service window**. Both are provisional listing copy, not
evidence of a charge, refund policy, production service level, or completed
commercial transaction.

## CAP-ready boundary

The default runtime posture is still `CAP_MODE=mock`, and `real_cap_ready`
remains `false`. Beyond local schemas and adapter contracts, two real-SDK
capabilities now exist and are independently gated behind explicit,
default-`false` environment flags (`CAP_PROVIDER_PRESENCE_ENABLED`,
`CAP_REAL_LIFECYCLE_ENABLED`, `CAP_ACCEPT_NEGOTIATION_ENABLED`,
`CAP_DELIVER_ORDER_ENABLED`, `CAP_REQUESTER_CANARY_ENABLED`,
`CAP_REQUESTER_PAY_ENABLED`):

- **Provider presence is live-verified.** A real, non-mutating WebSocket
  connection to the CROO backend reproduced the registered Agent's Dashboard
  status transitioning OFFLINE → ONLINE for the duration of the connection.
- **Lifecycle wiring exists and is offline-tested, not live-run.** The
  provider side can accept exactly one negotiation and deliver exactly one
  result through the real `croo-sdk`, gated by a Service ID and requester
  Agent ID allowlist with single-order idempotency — proven only against
  fake SDK clients. No funded, separately-keyed requester Agent has been set
  up, so no real negotiation, payment, or delivery has occurred.

Aegis does not claim a real CROO listing, accepting-orders status, payment,
escrow, delivery, settlement, reputation update, paid lifecycle, production
SLA, or commercial readiness. Real-provider credentials remain outside this
repository in an external secret mechanism and are never printed or
committed.

See the [CAP readiness truth table](docs/aegis-cap-truth-table.md) for the
guarded runtime state.

## Verification

Run focused API and Web Console checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_risk_check.py tests\test_a2a_mock_order.py tests\test_orders.py tests\test_cap_adapter.py tests\test_web_console.py -q
```

Run focused checks for the CAP presence and lifecycle wiring (fake SDK
clients only, no network):

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_cap_provider_presence_runtime.py tests\test_cap_provider_lifecycle_runtime.py tests\test_cap_delivery_mapping.py tests\test_croo_requester_canary.py -q
```

Run the full suite:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Do not permanently infer correctness from an old pass count. Record fresh
evidence for a release or submission candidate.

## Safety boundaries

- Risk advice is not execution authorization.
- `BLOCK` and `WAIT` are valid deliverables, not service failures.
- No wallet, private-key, signing, swap, transaction, broadcast, or
  live-trading path exists.
- No profit or guaranteed-safety claim is made.
- No real CAP payment, escrow, delivery, settlement, or commercial-readiness
  claim is made.
- Secrets and real-provider credentials must remain outside the repository and
  must never be printed.

## Documentation package

- [Product operation and marketplace-readiness runbook](docs/operations/step8c-product-operation-and-marketplace-readiness.md)
- [CROO Store listing draft](docs/croo-store-listing-draft.md)
- [DoraHacks submission draft](docs/dorahacks-submission-draft.md)
- [Compliance and evidence checklist](docs/compliance-evidence-checklist.md)
- [Owner-verified CROO Dashboard state](docs/owner-verified-croo-dashboard-state-2026-07-04.md)
- [CAP readiness truth table](docs/aegis-cap-truth-table.md)

## License

Aegis CROO is licensed under the Apache License, Version 2.0
(`Apache-2.0`). See [LICENSE](LICENSE) for the complete terms.
