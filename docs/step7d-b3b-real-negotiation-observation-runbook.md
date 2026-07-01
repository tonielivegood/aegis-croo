# Step 7D-B3-B Real Negotiation Observation Go/No-Go Runbook

Date: 2026-07-01
Project: Aegis Risk Oracle CROO

## 1. Purpose and Authorization Boundary

This runbook governs a future, separately approved observation of at most one
real `negotiation-created` event. The observation is manual-review only. It is
not authorization to accept, reject, pay, deliver, upload, settle, clear, or
otherwise mutate a negotiation or order.

The observation must not handle a paid order, initiate or verify a payment,
escrow, delivery, or settlement flow, or support a commercial-readiness claim.
It must not introduce wallet, private-key, signing, swap, transaction,
broadcast, or live-trading behavior.

Committing this runbook does not authorize a real observation. A future run
requires separate, explicit operator approval issued specifically for one
bounded observation.

## 2. Current Safe Baseline

The verified Step 7D-B3-A baseline before this docs-only runbook commit is:

- `main` HEAD: `a9b75d1d9d18ae8608e46e87063eaa224c9f1650`.
- Full pytest after the B3-A merge: `275 passed, 1 existing warning`.
- Post-merge focused B3-A tests: `27 passed`.
- Forbidden-capability scan categories: all `0`.
- `CAP_MODE=mock` by default.
- `CAP_MODE=real` alone cannot start the manual runner.
- `cap_pilot_enabled=false` by default.
- `connector_start_authorized=false` by default.
- `sdk_load_authorized=false` by default.
- `option_b_negotiation_pilot_authorized=false` by default.
- `manual_operator_approval=false` by default.
- `max_events=0` by default and must equal `1` for an approved observation.
- `require_fund_transfer=false` is required.
- `real_cap_ready=false`.
- `live_execution_authorized=false`.
- `mutating_methods_called=false`.

The B3-A fake-only timing matrix verifies that queued, adjacent, timer-zero,
and delayed second events return `no_go`. Only one valid
`negotiation-created` event may return `manual_review`; adjacent/deferred
bypasses are `0`.

## 3. Strict Go/No-Go Checklist

Every GO item is mandatory. Any unmet, ambiguous, or unverifiable item is
NO-GO. Approval expires after one observation attempt, including an attempt
that fails, times out, or closes without an event.

### GO only if

- [ ] The Dashboard profile remains complete.
- [ ] The service price remains exactly `0.12 USDC`, or a changed price is
      explicitly documented and separately approved before observation.
- [ ] Require Fund Transfer remains OFF.
- [ ] Requirements type is Schema and the expected schema is verified.
- [ ] Deliverable type is Schema and the expected schema is verified.
- [ ] The API key and service ID exist only outside the repository.
- [ ] Secret values will not be printed, logged, copied into evidence, or
      passed in command-line arguments.
- [ ] `git status` is clean on an explicitly recorded commit.
- [ ] Full pytest passes immediately before approval.
- [ ] Every forbidden-capability scan category returns `0`.
- [ ] The operator explicitly approves exactly one observation.
- [ ] `CAP_MODE=real` is accompanied by every separately required gate.
- [ ] `cap_pilot_enabled=true`.
- [ ] `connector_start_authorized=true`.
- [ ] `sdk_load_authorized=true`.
- [ ] `option_b_negotiation_pilot_authorized=true`.
- [ ] `manual_operator_approval=true`.
- [ ] `max_events=1` at every applicable gate and request boundary.
- [ ] `require_fund_transfer=false`.
- [ ] No paid-order flow is enabled or reachable.
- [ ] No lifecycle mutation method is enabled or reachable.
- [ ] Accept, reject, pay, deliver, upload, settle, and clear gates remain OFF.
- [ ] No wallet, private-key, signing, swap, transaction, broadcast, or
      live-trading path exists.
- [ ] The runtime timeout and bounded close timeout are explicitly recorded.
- [ ] The evidence sink accepts sanitized fields only.

### NO-GO if

- Any required secret is missing, printed, logged, or stored inside the
  repository.
- Dashboard identity, price, fund-transfer, requirements, or deliverable
  settings differ from the approved snapshot.
- Require Fund Transfer is ON.
- Any test fails or the expected suite cannot run.
- `git status` is dirty or the reviewed commit does not match the run commit.
- Any forbidden-capability scan category is nonzero.
- More than one event might be processed, queued, retained, or retried.
- Accept, reject, pay, deliver, upload, settle, or clear is enabled or
  reachable.
- A paid-order, escrow, payment, delivery, or settlement flow is enabled.
- Wallet, private-key, signing, swap, transaction, broadcast, or live-trading
  behavior exists.
- Evidence could contain a key, authorization value, credential-bearing URL,
  raw identifier, raw event, or secret-bearing exception.
- Anyone claims or requires paid-order handling, verified escrow/payment,
  verified delivery/settlement, commercial readiness, or live trading.
- The observation is not covered by a fresh, explicit, one-attempt approval.

## 4. Claim Boundary

### Allowed after a separately approved future observation

Use only this claim, and only when supported by sanitized evidence:

> One real negotiation-created event was observed and classified as
> manual_review/no_go with sanitized evidence.

If no event was observed, the claim must instead state that the bounded
observation ended without a qualifying event and report only its sanitized
status.

### Not allowed

- "real CAP ready"
- "paid order handled"
- "payment verified"
- "escrow verified"
- "delivery verified"
- "settlement verified"
- "commercially ready"
- "live trading"

The invariant `real_cap_ready=false` remains true after an observation.

## 5. Operator Procedure Outline

This outline is not approval to run. The operator must stop at the approval
gate unless separate approval has been recorded.

1. Record the intended observation ID, reviewed commit, operator, scope, and
   expiration of the one-attempt approval.
2. Complete every GO item and record a sanitized Dashboard snapshot, clean Git
   status, passing full-suite result, and zero-count safety scan.
3. Confirm that all mutation, paid-order, wallet, signing, transaction, and
   trading paths remain absent or disabled.
4. Load the API key, service ID, and any required connection values from an
   approved external path only. Do not read them into evidence or print them.
5. Reconfirm `max_events=1`, bounded runtime/close timeouts, no retry, and the
   complete required gate snapshot without secret values.
6. Obtain and record explicit operator approval for one bounded observation.
7. Run one bounded observation through the reviewed manual runner only.
8. Accept only one `negotiation-created` event for classification. Any
   malformed, non-negotiation, duplicate, multiple, queued, adjacent,
   timer-zero, or delayed second event must fail closed.
9. Capture sanitized evidence only, verify redaction, close the connection,
   and stop immediately.
10. Do not rerun after success, failure, timeout, close failure, or no event.
    A new attempt requires separate approval and a new preflight.

## 6. Evidence Fields

Capture only the following sanitized fields:

```text
observation_id
created_at
request_hash                 # if available; never the raw request
sanitized_event_type
decision_status              # manual_review or no_go
close_status
gates_snapshot               # booleans/limits only; no secrets
real_cap_ready               # always false
mutating_methods_called      # always false
live_execution_authorized    # always false
redaction_check_result
```

Do not capture raw API keys, authorization headers, connection URLs, service
credentials, negotiation/order identifiers, raw events, raw requests, or
secret-bearing exceptions.

## 7. Abort and Post-Observation Rules

- Abort immediately on any NO-GO condition or invariant mismatch.
- A second event fails closed and ends the observation.
- A close failure must be reported with sanitized evidence and must not cause
  a retry.
- Do not enable a mutation or paid-order gate to recover from an error.
- Preserve `real_cap_ready=false`, `mutating_methods_called=false`, and
  `live_execution_authorized=false` in the final evidence.
- Treat the approval as consumed after the first attempt.

## 8. Step 8 Transition

After this runbook is committed, proceed to Step 8 Web Playground / demo
polish. Do not run a real negotiation observation before or during Step 8
unless it receives separate, explicit approval under this runbook.

Step 8 must preserve Aegis positioning as a pre-trade DeFAI risk-check agent,
risk oracle, and A2A safety guard. It must not imply trade execution, wallet
management, transaction signing/broadcast, profit, payment verification, or
commercial readiness.
