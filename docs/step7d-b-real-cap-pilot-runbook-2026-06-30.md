# Step 7D-B Real CAP Pilot Approval Runbook

Date: 2026-06-30
Baseline main commit: `fc4b181d8df7d464d9e87d970820b14cec6e6c36`
Status: **PLAN ONLY — NO-GO FOR LIVE EXECUTION**

## Approval Boundary

This runbook does not authorize a WebSocket connection, provider listener, negotiation, rejection, acceptance, payment, delivery, upload, clear, settlement, or any other live CROO/CAP action.

Step 7D-A deliberately has no real SDK connector, live start path, real action adapter, or controlled requester/payment harness. No existing environment-variable combination can execute this pilot. Before any option can run, the missing boundaries named here must be implemented, fake-tested, reviewed, and approved in a separate change and a separate explicit go/no-go decision.

`real_cap_ready=false` remains mandatory before, during, and after every option in this runbook.

## 1. Goal

Verify one tightly controlled real CAP provider lifecycle step without violating Aegis safety boundaries, while preserving the product claim:

> Other agents hire Aegis before they execute. Aegis returns BLOCK, WAIT, or EXECUTE with proof.

The pilot must be bounded to one allowlisted Service request, one unique run ID, one requester, and one terminal outcome. It must never add wallet, private-key, signing, swap, transaction-construction, broadcast, or live-trading behavior to Aegis.

## 2. Candidate Pilot Options

### Option A — Receive, Guard, and Reject One Real Negotiation

**Flow:** A controlled requester creates one deliberately unsafe or wrong-service negotiation. Aegis receives it, runs the Step 7A guard and Step 7B planner, and calls `reject_negotiation` exactly once only when the expected guard result is `reject`.

**Benefits**

- Proves real inbound negotiation routing, guard execution, and one bounded provider mutation.
- Demonstrates that Aegis refuses unsafe commerce rather than blindly accepting work.
- Adds useful Technical Execution and trust evidence.

**Risks**

- Requires a real requester mutation and a real provider rejection mutation.
- Deliberately creates unsafe payload evidence, which must be carefully allowlisted and sanitized.
- Does not prove payment, escrow, delivery, adoption, or the core paid-risk-check story.
- A mismatch between expected and received payload must abort without rejection.

**Required gates**

- Controlled requester, live connector, and real rejection adapter implemented and fake-tested.
- `CAP_PROVIDER_REJECT_ENABLED=true`; accept, paid handling, and delivery remain false.
- Exactly one expected negotiation and one provider rejection; no retry.

**Can claim after a successful run**

- One real negotiation was received, guard-checked, and rejected by Aegis.
- The rejection was bounded to the approved unsafe fixture.

**Cannot claim**

- Aegis accepted work, handled payment/escrow, delivered a result, settled, stayed persistently online, or is commercially ready.

### Option B — Receive, Guard, and Manual-Review One Real Negotiation

**Flow:** A controlled requester creates one valid Aegis Risk Check negotiation. Aegis receives it, runs the guard and planner, records `accept_candidate` plus `would_manual_review` because all provider mutation gates remain off, then closes without accept or reject.

**Benefits**

- Safest real inbound canary: proves real negotiation routing and guard/planner compatibility with zero provider mutation.
- Validates Dashboard Service identity and schema against a real event.
- Provides a clean checkpoint before any acceptance or paid-order attempt.

**Risks**

- The requester still creates one real negotiation.
- The negotiation may remain pending or expire; Dashboard cleanup behavior must be understood first.
- Scoring uplift is modest because there is no real acceptance, payment, or delivery.

**Required gates**

- Controlled requester and live connector implemented and fake-tested.
- Every provider action gate remains false.
- Exactly one event is processed, evidence is captured, and the stream closes.

**Can claim after a successful run**

- One real Aegis Risk Check negotiation was received and guard/planner-checked.
- Aegis intentionally performed no provider mutation and routed the request to manual review.

**Cannot claim**

- Acceptance, rejection, payment, escrow, delivery, settlement, persistent availability, or commercial readiness.

### Option C — Complete One Real Paid Aegis Risk Check Order at 0.12 USDC

**Flow:** A controlled requester creates one allowlisted valid negotiation. Aegis guard-checks and accepts it. The requester pays exactly `0.12 USDC`. Aegis correlates `ORDER_PAID`, re-runs the guard, calls `assess_risk` exactly once, validates the Schema deliverable, and calls `deliver_order` exactly once.

**Benefits**

- Highest Top 1 impact: demonstrates real agent commerce around Aegis's differentiated risk-gate product.
- Can materially improve Technical Execution, A2A Composability, Usability/Adoption, and Presentation.
- Produces the strongest evidence for “another agent hired Aegis before execution.”

**Risks**

- Requires real requester negotiation/payment and real provider acceptance/delivery mutations.
- SDK logging, reconnect, event-order, duplicate-session, and correlation failures can expose secrets or cause unintended actions.
- The audited SDK may emit `ORDER_CREATED` before `ORDER_PAID`; Step 7D-A currently treats unexpected events as manual review. Option C is therefore NO-GO until the exact event sequence is supported and fake-tested.
- Payment does not automatically prove escrow, settlement, or commercial readiness; those require explicit platform evidence.

**Required gates**

- Option B has passed and been reviewed.
- Live connector, controlled requester/payment harness, real accept/deliver adapter, spend cap, idempotency record, and expected intermediary-event handling are implemented and fake-tested.
- Exactly one order, `0.12 USDC` maximum service price, no retry, and exact method-call counts.

**Can claim after a successful run**

- Only the lifecycle states supported by captured evidence: one real negotiation accepted, one real `0.12 USDC` payment observed, and one real Schema risk-check delivery confirmed.
- Escrow or settlement only if CROO explicitly reports and the evidence captures that state.

**Cannot claim**

- Persistent provider availability, repeat adoption, generalized commercial readiness, arbitrary payment/escrow guarantees, or any wallet/trading capability.

## 3. Recommended Path

**Recommend Option B for the next approval.** It is the safest meaningful step beyond the connection-only probe and validates the real inbound payload against the guard/planner without provider mutation.

After Option B passes, perform a separate evidence review. If every Option C prerequisite then passes, request a new explicit approval for Option C. Option A is useful for proving real rejection behavior but is not the best next step for the Top 1 story and should not be combined with Option B or C in the same session.

## 4. Required Prerequisites

All items are mandatory for every option unless explicitly marked Option C only.

### Dashboard and account state

- The expected Agent ID/display name owns the expected Service ID and `Aegis Risk Check` Service.
- Price is exactly `0.12 USDC`.
- Require Fund Transfer is OFF.
- Requirements type is Schema and matches `RiskCheckRequest` exactly.
- Deliverable type is Schema and matches `RiskCheckResponse` exactly.
- Pre-run Agent online/offline state is recorded with sanitized evidence.
- No pending negotiation, paid order, delivery, or unrelated test exists.
- No other process or session uses the provider SDK key.

### Repository and verification state

- Git is clean on an explicitly recorded commit.
- Full pytest, compile, and `git diff --check` pass immediately before approval.
- Forbidden import, CAP mutation, generic mutation, wallet/signing/swap/transaction/trading, provider-example, and secret-pattern scans pass.
- Step 7D-A disabled defaults and `real_cap_ready=false` are unchanged.
- The exact SDK version, event types, and method signatures are re-audited locally.

### Secret handling

- Required secret files may be present locally but are confirmed ignored/untracked by metadata only.
- Secret file contents are never read, printed, copied into evidence, or passed on a command line.
- Redaction is active before SDK client construction and covers URL query parameters, headers, raw events, identifiers, and exceptions.
- The key is scoped/rotatable, and a rotation path is ready if leakage is suspected.

### Missing implementation prerequisites

These do not exist in Step 7D-A and make all options **NO-GO today**:

- A reviewed real SDK connector that disables automatic reconnect or detects and aborts it.
- A reviewed real action adapter exposing only the methods authorized for the selected option.
- A controlled requester harness with hard order/spend/idempotency limits.
- Persistent one-run idempotency evidence that prevents accidental reruns across processes.
- Option C only: expected `ORDER_CREATED` handling, payment correlation, exact price verification, and real Schema delivery integration.

## 5. Required Environment Gates

### Common real-pilot settings

These values apply only after the missing implementation prerequisites pass review:

```text
CAP_MODE=real
CAP_REAL_PROVIDER_ENABLED=true
CAP_CONTROLLED_PROVIDER_RUNTIME_ENABLED=true
CAP_WS_OBSERVE_ONLY_ENABLED=false
CAP_PROVIDER_RUNTIME_TIMEOUT_SECONDS=5.0
CAP_PROVIDER_RUNTIME_CLOSE_TIMEOUT_SECONDS=1.0
```

The following configuration variables must be present but their values must never be printed:

```text
CROO_API_URL
CROO_WS_URL
CROO_SDK_KEY
CROO_SERVICE_ID
CROO_PROVIDER_AGENT_ID
```

### Required new pilot kill switches

These variables are defined by this runbook but are **not implemented today**. Their absence is a hard NO-GO:

```text
CAP_PILOT_ENABLED=true
CAP_PILOT_RUN_ID=<unique nonsecret identifier>
CAP_PILOT_MAX_ORDERS=1
CAP_PILOT_MAX_SPEND_USDC=0.12
CAP_PILOT_NO_RETRY=true
CAP_PILOT_REQUESTER_ENABLED=true
CAP_PILOT_NEGOTIATE_ENABLED=true
CAP_PILOT_PAY_ENABLED=<option-specific>
CAP_PILOT_EXPECTED_SERVICE_ID=<exact reviewed CROO Dashboard Service ID>
```

The local guard currently uses `aegis-risk-check-schema-v1` as its logical Service contract ID. If the CROO Dashboard Service ID differs, the mapping must be explicitly documented and fake-tested before approval; an unexplained mismatch is a hard NO-GO.

### Option-specific provider gates

| Gate | Option A | Option B | Option C |
|---|---:|---:|---:|
| `CAP_PROVIDER_ACCEPT_ENABLED` | `false` | `false` | `true` |
| `CAP_PROVIDER_REJECT_ENABLED` | `true` | `false` | `false` |
| `CAP_PROVIDER_PAID_ORDER_HANDLING_ENABLED` | `false` | `false` | `true` |
| `CAP_PROVIDER_DELIVER_ENABLED` | `false` | `false` | `true` |
| `CAP_PROVIDER_RUNTIME_MAX_EVENTS` | `1` | `1` | `3` |
| `CAP_PILOT_PAY_ENABLED` | `false` | `false` | `true` |

Option C uses a maximum of three business events to allow the audited `NEGOTIATION_CREATED -> ORDER_CREATED -> ORDER_PAID` sequence. If the installed SDK/backend emits a different sequence, the run is NO-GO until the sequence and limit are updated in tests and reapproved.

### Variables that must remain off for every option

```text
CAP_WS_OBSERVE_ONLY_ENABLED=false
```

No fund-address, upload, settlement, clear, wallet, signing, swap, broadcast, or trading gate may exist or be enabled. Any undocumented permissive environment variable is an abort condition.

## 6. Event Handling Rules

### `NEGOTIATION_CREATED`

1. Confirm this is the first event, event count is within limit, and the internal ID has not been seen.
2. Match requester, provider, Service ID/name, `0.12 USDC` price, Require Fund Transfer OFF, requirements type, and deliverable type.
3. Run `evaluate_cap_provider_guard` exactly once before any provider mutation.
4. Pass that exact result to `plan_from_guard_result`; do not re-evaluate for planning.
5. Option A: call `reject_negotiation` once only for the allowlisted fixture and an exact `reject` decision. Any other decision aborts without mutation.
6. Option B: record `would_manual_review`, make no provider call, and close.
7. Option C: call `accept_negotiation` once only for `accept_candidate`, exact schema/identity/price match, and all gates enabled. Store the payload internally for later correlation.

### `ORDER_CREATED`

- Options A/B: unexpected; abort and close.
- Option C: allow only as the second event for the accepted negotiation/order correlation. Record a sanitized summary, make no additional mutation, and continue waiting for `ORDER_PAID` within the same timeout.

### `ORDER_PAID`

- Options A/B: unexpected; abort and close without mutation.
- Option C only:
  1. Require the third event and exact correlation to the approved negotiation/order.
  2. Verify the observed service price/payment is exactly `0.12 USDC`; any fund-transfer request or extra amount aborts.
  3. Re-run the guard on the stored negotiation payload and require `accept_candidate`.
  4. Validate `RiskCheckRequest`, call `assess_risk` exactly once, and validate `RiskCheckResponse`.
  5. Produce deterministic request/response/result proof hashes.
  6. Call `deliver_order` exactly once with the inline Schema deliverable; never upload a file.
  7. Close immediately after delivery confirmation or the first terminal error.

### Unknown, duplicate, or out-of-order events

- Record only a sanitized event summary.
- Make no provider/requester mutation.
- Set the outcome to manual review/error, close once, and mark the pilot failed.
- Never skip or reorder events to force a success narrative.

### Unsafe payloads

- Option A: reject only the exact approved unsafe fixture and only with the rejection gate enabled.
- Options B/C: manual review/abort with no accept, reject, pay, or delivery.

### Ambiguous payloads

- Every option routes ambiguity to manual review and closes without mutation.
- Missing identity, schema, price, fund-transfer metadata, IDs, or correlation is ambiguity.

## 7. Forbidden Actions

- No Aegis wallet, private-key, seed phrase, signing, swap, transaction construction, transaction broadcast, or live-trading behavior.
- No fund-transfer negotiation and no `accept_negotiation_with_fund_address`.
- No official provider/requester example or copied auto-action callback.
- No unbounded listener, background daemon, reload process, automatic retry, or automatic reconnect.
- No raw SDK key, credential-bearing URL, authorization header, raw event, negotiation/order ID, or secret-bearing exception in logs or evidence.
- No `upload_file`, `get_download_url`, settle, or clear call.
- No method outside the option's exact allowlist:
  - Option A: requester `negotiate_order` once; provider `reject_negotiation` once.
  - Option B: requester `negotiate_order` once; no provider mutation.
  - Option C: requester `negotiate_order` once and `pay_order` once; provider `accept_negotiation` once and `deliver_order` once.
- No second attempt in the same approval, even after a transient failure.

## 8. Evidence to Capture

Capture one sanitized JSON report and no raw SDK/backend logs:

```text
pilot_option
pilot_run_id
git_commit
sdk_version
started_at_utc
duration_seconds
dashboard_snapshot_status
event_summaries[]:
  event_type
  has_negotiation_id
  has_order_id
guard_decision
guard_reason_codes
planner_directives
risk_check_decision            # Option C only
risk_score                     # Option C only
proof_request_hash             # Option C only
proof_response_hash            # Option C only
proof_result_hash              # Option C only
payment_status                 # Option C, only if explicitly observed
escrow_status                  # only if explicitly reported by CROO
delivery_status                # Option C, only if explicitly confirmed
settlement_status              # only if explicitly reported by CROO
closed
close_attempted
mutating_methods_called[]
mutating_method_call_counts
real_cap_ready
failure_reason
```

Required terminal invariants:

- `closed=true`; otherwise the pilot fails and forced process termination is recorded.
- Method calls exactly match the selected option; any extra call is a failure.
- `real_cap_ready=false` for every option.
- No raw IDs, event payloads, URLs, headers, or secrets appear in the report.

## 9. Truth Table Update Rules

### After successful Option A

May upgrade:

- Real negotiation received: `verified_once`.
- Guard against a real payload: `verified_once`.
- Real provider rejection: `verified_once_for_allowlisted_fixture`.

Must remain `not_verified`:

- Acceptance, payment, escrow, delivery, clear, settlement, reputation, persistent online status, commercial readiness, and `real_cap_ready`.

### After successful Option B

May upgrade:

- Real negotiation received: `verified_once`.
- Guard/planner compatibility with a real Aegis payload: `verified_once`.
- Real manual-review/no-mutation behavior: `verified_once`.

Must remain `not_verified`:

- Rejection, acceptance, payment, escrow, delivery, clear, settlement, reputation, persistent online status, commercial readiness, and `real_cap_ready`.

### After successful Option C

May upgrade only when evidence supports each field:

- Real negotiation received/accepted: `verified_once`.
- Real requester payment: `verified_once_at_0.12_usdc`.
- Real Schema risk-check delivery: `verified_once`.
- Escrow: `verified_once` only if CROO explicitly reports escrow/lock evidence.
- Clear/settlement/reputation: `verified_once` only if the platform explicitly reports the corresponding terminal state.

Must remain `not_verified`:

- Persistent provider availability, generalized accepting-orders status, repeat adoption, generalized payment/escrow guarantees, commercial readiness, wallet/trading capability, and `real_cap_ready`.

A failed or partial pilot never upgrades a truth-table status. It records only the last safely observed fact and the failure reason.

## 10. Go/No-Go Checklist

Every row must be PASS before a live approval can be requested.

| Check | PASS evidence | FAIL/NO-GO condition |
|---|---|---|
| Explicit approval | Selected option, time window, method allowlist, and spend cap approved | General or ambiguous approval |
| Clean repository | Clean status and recorded commit | Any unreviewed change |
| Verification | Full tests, compile, diff, and scans pass | Any failure or new warning requiring review |
| Dashboard identity | Agent/Service/schema/price/fund-transfer snapshot matches | Any mismatch or stale evidence |
| Pending work | No pending negotiations/orders and no duplicate key session | Any pending or uncertain state |
| Secrets | Ignored/untracked presence only; redaction sentinel tests pass | Secret printed/read, suspicious log, or unscoped key |
| Live connector | Reviewed, fake-tested, bounded, reconnect-aborting | Missing connector or automatic reconnect possible |
| Real action adapter | Only selected methods are reachable; AST/call-recorder tests pass | Dynamic dispatch or extra method reachable |
| Requester harness | One run ID, one order, no retry, exact spend cap | Missing idempotency or spend bound |
| Event contract | Exact expected sequence is fake-tested | Unknown intermediary event or uncertain sequence |
| Close behavior | Graceful close and forced-stop deadline tested | Close can hang or duplicate |
| Evidence plan | Sanitized report schema and output location reviewed | Raw logs/IDs/secrets required |

### Current go/no-go result

**NO-GO for Options A, B, and C today.** The live connector, real action adapter, requester kill switches, cross-process idempotency, and fresh Dashboard/pending-order evidence are absent. Option C additionally lacks tested `ORDER_CREATED` handling and real payment/delivery integration.

## 11. Rollback and Abort Plan

1. On any abort condition, stop scheduling work and cancel pending tasks.
2. Attempt bounded stream close for `1.0` second exactly once.
3. If close fails or reconnect begins, terminate the single pilot process; do not restart it.
4. Immediately set/unset all pilot and provider gates back to their safe defaults:

```text
CAP_MODE=mock
CAP_REAL_PROVIDER_ENABLED=false
CAP_CONTROLLED_PROVIDER_RUNTIME_ENABLED=false
CAP_PROVIDER_ACCEPT_ENABLED=false
CAP_PROVIDER_REJECT_ENABLED=false
CAP_PROVIDER_PAID_ORDER_HANDLING_ENABLED=false
CAP_PROVIDER_DELIVER_ENABLED=false
CAP_PILOT_ENABLED=false
CAP_PILOT_REQUESTER_ENABLED=false
CAP_PILOT_NEGOTIATE_ENABLED=false
CAP_PILOT_PAY_ENABLED=false
```

5. Preserve only the sanitized pilot report and process exit code. Do not preserve raw logs or event payloads.
6. Write the unique run ID to the reviewed idempotency record before connection; a present run ID prevents every rerun.
7. Inspect Dashboard state manually for a pending negotiation/order using masked identifiers only. Do not mutate it without a new approval.
8. If any credential may have leaked, rotate/revoke it before any future work and mark the pilot failed.
9. A failed run consumes the approval. A retry requires a new root-cause review, fresh tests/scans, and new explicit approval.

## 12. Submission Impact

| Pilot | Technical Execution | A2A Composability | Usability/Adoption | Presentation |
|---|---|---|---|---|
| Option A | Moderate: proves one real guarded mutation | Low-Moderate: real inbound and rejection | Low: no paid use or deliverable | Moderate trust story, weak commerce story |
| Option B | Moderate: proves real inbound guard/planner behavior | Moderate: real agent request reaches Aegis | Low-Moderate: one real interaction, no purchase | Strong safety canary and honest progression |
| Option C | High: proves guarded real accept/pay/deliver flow | High: another agent hires Aegis through CAP | High if payment/delivery evidence is clean | Highest-impact demo of the core product promise |

Option B is the recommended next approval because it reduces integration uncertainty without provider mutation. Option C is the recommended eventual Top 1 pilot, but only after Option B and every additional prerequisite pass.

## Approval Record Template

This section must be completed in a later review. Blank fields mean NO-GO.

```text
approved_option:
approved_git_commit:
approved_sdk_version:
approved_run_id:
approved_time_window_utc:
approved_requester_agent:
approved_provider_agent:
approved_service_id:
approved_method_allowlist:
approved_max_orders: 1
approved_max_spend_usdc:
approved_event_limit:
approved_runtime_timeout_seconds: 5.0
approved_close_timeout_seconds: 1.0
approver:
```

No person or automation may infer approval from this runbook's existence.
