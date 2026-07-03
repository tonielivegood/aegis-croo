# CROO Store Listing Draft: Aegis Risk Oracle

Date: 2026-07-02
Status: Draft for listing preparation; not evidence of a published listing

## Evidence rule

The official [CROO CAP site](https://cap.croo.network/) and
[CROO Agent Store](https://agent.croo.network/) were accessed on 2026-07-02.
They support the general CAP provider, service, schema, pricing, SLA, and proof
model and confirm that an Agent Store surface exists. The exact current listing
form, required fields, category taxonomy, publication process, refund rules,
and Aegis listing status were not verified from an authoritative form.

Everything below is product copy for review. Replace
`[VERIFY_OFFICIAL_CROO_LISTING_REQUIREMENTS_URL]` and
`[VERIFY_CROO_STORE_URL]` only after direct verification.

## Listing summary

| Field | Draft value |
| --- | --- |
| Agent name | Aegis Risk Oracle |
| Service name | Aegis Risk Check |
| Short tagline | Pre-trade risk oracle that returns BLOCK, WAIT, or EXECUTE with proof before a caller acts |
| Recommended categories | Data & Verification Agents; DeFi / On-chain Ops Agents |
| Requirements format | JSON schema |
| Deliverable format | JSON schema |
| Pilot price | 0.12 USDC per call; provisional positioning only |
| Draft service window | Five minutes; draft only, not a production guarantee |
| Listing URL | `[VERIFY_CROO_STORE_URL]` |
| Official listing requirements | `[VERIFY_OFFICIAL_CROO_LISTING_REQUIREMENTS_URL]` |

The category names are recommendations from the project audit, not a claim that
Product boundary: Aegis is a pre-trade risk oracle, risk-check API, DeFAI
safety agent, and A2A risk guard. Aegis checks risk before execution. Aegis
does not execute. `CAP_MODE=mock` is the default; `real_cap_ready=false`,
`live_execution_authorized=false`, and `mutating_methods_called=false`.
The 0.12 USDC pilot price is provisional. Real CAP payment, escrow, delivery,
settlement, and commercial readiness are not claimed. The owner-approved
project license is Apache-2.0; the canonical text is in the root `LICENSE`.
the current Store form exposes those exact choices.

## Long description

Aegis Risk Oracle is a callable pre-trade risk layer for agents. Before a
requester takes a separately controlled action, it sends Aegis the proposed
action, market evidence, and optional portfolio context. Aegis applies a
deterministic policy and returns `BLOCK`, `WAIT`, or `EXECUTE`, together with
a score, confidence, reasons, risk factors, suggested action, and hash-linked
proof.

The buyer problem is simple: an execution-capable agent can act faster than it
can explain whether its inputs are complete or its proposed exposure is
reasonable. Aegis gives that caller a small, inspectable checkpoint before the
caller decides what to do next.

Aegis is a risk-check API, DeFAI safety agent, and agent-to-agent risk guard.
It is intentionally separate from execution and signal generation. `EXECUTE`
means the supplied evidence passed the current risk policy; it is not
transaction authorization. Aegis never takes custody or submits an action.

The current product is available as a local API and Web Console with mock A2A
and in-memory order/proof workflows. It has a CAP-ready gated runtime, but real
CROO payment, delivery, settlement, accepting-orders status, and commercial
readiness remain unverified and are not claimed.

## Buyer problem and outcome

**Problem:** A caller needs a consistent pre-action risk decision it can inspect,
record, and branch on without delegating control of its downstream action.

**Outcome:** One structured request produces a bounded decision and proof:

- `BLOCK`: stop the proposed action.
- `WAIT`: pause for stronger evidence or manual review.
- `EXECUTE`: favorable risk advice; the caller controls any later action.

`BLOCK` and `WAIT` are successful risk-check deliverables, not provider
failures.

## Service input schema

| Field | Type | Required | Constraints and meaning |
| --- | --- | --- | --- |
| `token` | string | yes | Non-empty asset or market identifier |
| `chain` | string | yes | Non-empty chain identifier |
| `intended_action` | string | yes | Non-empty proposed action |
| `size_usd` | number | yes | Greater than or equal to zero |
| `market_signal` | object | no | Optional market evidence described below |
| `portfolio_context` | object | no | Optional exposure limits described below |

Optional `market_signal` fields:

| Field | Type | Constraint |
| --- | --- | --- |
| `price_change_24h` | number or null | None |
| `volume_change_24h` | number or null | None |
| `liquidity_usd` | number or null | Greater than or equal to zero |
| `volatility_24h` | number or null | Greater than or equal to zero |
| `slippage_bps` | number or null | Greater than or equal to zero |
| `gas_level` | string or null | `low`, `medium`, `high`, or `critical` |

If `portfolio_context` is supplied, both fields are required:

| Field | Type | Constraint |
| --- | --- | --- |
| `current_exposure_usd` | number | Greater than or equal to zero |
| `max_position_usd` | number | Greater than or equal to zero |

The requester remains responsible for the accuracy, freshness, and scope of
its inputs.

## Service output schema

| Field | Type | Meaning |
| --- | --- | --- |
| `decision` | `BLOCK`, `WAIT`, or `EXECUTE` | Risk classification |
| `risk_score` | integer, 0-100 | Deterministic policy score |
| `confidence` | `low`, `medium`, or `high` | Evidence confidence |
| `market_regime` | string | Policy classification of supplied conditions |
| `safe_to_execute` | boolean | Advice only; never authorization |
| `risk_factors` | array | Structured factor name, severity, impact, and evidence |
| `reasons` | array of strings | Human-readable policy reasons |
| `suggested_action` | string | Bounded caller guidance |
| `proof` | object | Direct risk proof fields |

## Proof fields

Direct risk proof:

| Field | Meaning |
| --- | --- |
| `request_hash` | SHA-256 link to the canonical request payload |
| `response_hash` | SHA-256 link to the policy-scoped response payload |
| `policy_version` | Policy identifier used for the decision |

Local order proof, available only through the in-memory mock order contract:

| Field | Meaning |
| --- | --- |
| `proof_id` | Local proof identifier |
| `order_id` | Local order identifier |
| `request_hash` | Canonical request hash |
| `response_hash` | Risk response hash |
| `result_hash` | Local deliverable hash |
| `policy_version` | Policy identifier |
| `deliverable_type` | Current value: `schema` |
| `created_at` | Local proof creation timestamp |

These hashes are local delivery/log attestations. They are not on-chain proof,
payment receipts, escrow records, settlement evidence, or evidence of a real
CROO delivery.

## A2A buyer workflow

1. The requester constructs a proposed action.
2. Before acting, it calls Aegis through `POST /risk-check` or the local
   `POST /a2a/mock-order` demonstration.
3. Aegis returns a decision, explanation, and proof.
4. The requester maps `BLOCK` to `REFUSED`, `WAIT` to `DELAYED`, or
   `EXECUTE` to `SIMULATED_EXECUTION_ONLY`.
5. The requester records the result and retains control of every later action.

Aegis does not perform step 5 on the requester's behalf.

## Price and service-window wording

**Pilot price:** 0.12 USDC per call.

This is provisional marketplace positioning. It does not prove that a charge
can be collected, that a buyer has paid, or that a refund mechanism exists.

**Draft service window:** five minutes.

This is a listing draft, not a production availability, latency, or completion
guarantee. Measure and approve a production service level separately before
publishing one.

## BLOCK, WAIT, no-go, failure, and refund wording

> BLOCK and WAIT are valid risk-check deliverables, not service failures.
> BLOCK advises the caller to stop; WAIT advises the caller to pause or review.
> ?No-go? may be used as plain-language shorthand for BLOCK, but `no_go` is not
> an API enum. Invalid requests return a documented API validation error and no
> risk decision. Any future charge, cancellation, dispute, or refund behavior
> must follow verified CROO rules and a separately approved paid lifecycle.

The current Aegis package makes no claim of a real charge, cancellation,
refund, escrow, settlement, or paid-order handling.

## Honest readiness boundary

| State | Current truth |
| --- | --- |
| Local risk API and Web Console | Available |
| Mock A2A and local order/proof | Available locally |
| `CAP_MODE` | `mock` |
| `real_cap_ready` | `false` |
| `live_execution_authorized` | `false` |
| `mutating_methods_called` | `false` |
| Published Aegis Store listing | Unverified; URL placeholder retained |
| Real paid CAP lifecycle | Pending and not claimed |
| Production SLA | Not established |
| Commercial readiness | Not established |

## What not to claim

Do not publish wording that says or implies:

- Aegis is a trading, execution, swap, wallet, signal, profit, or private-key agent.
- `EXECUTE` authorizes or proves a downstream action.
- Aegis provides guaranteed safety or profit.
- Aegis is online, accepting real orders, or published in the Store without
  direct listing evidence.
- A real payment, refund, escrow, delivery, settlement, reputation update, or
  paid lifecycle occurred.
- The pilot price or draft service window is a production commercial commitment.
- A local hash is an on-chain proof or payment record.

## Publication gates

Before copying this draft into a live listing:

- [ ] Verify the current official listing form and field limits.
- [ ] Verify the official category/taxonomy choices.
- [ ] Confirm anonymous public repository access.
- [x] Retain the owner-approved Apache-2.0 license in the root `LICENSE` file.
- [ ] Replace the Store URL placeholder with a visible Aegis listing.
- [ ] Verify price, cancellation, dispute, and refund rules.
- [ ] Re-run setup, schema, claim-safety, and secret checks.
- [ ] Keep real-CAP and commercial claims pending until directly evidenced.
