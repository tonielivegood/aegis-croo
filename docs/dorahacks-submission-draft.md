# DoraHacks Submission Draft: Aegis Risk Oracle

Date: 2026-07-02
Status: Draft for submission preparation; not a submitted BUIDL

## Source and verification rule

No authoritative DoraHacks page for the current CROO program, its deadline,
mandatory BUIDL fields, track taxonomy, or judging rubric was verified during
this documentation pass. Third-party event summaries are not accepted as
submission evidence.

Keep `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]`,
`[VERIFY_DORAHACKS_DEADLINE_AND_TIMEZONE]`, and all public artifact
placeholders unresolved until a submission lead checks the live official form.
The sections below are strong draft content, not a claim that each heading is a
mandatory form field.

## Project summary

Aegis Risk Oracle is a proof-backed pre-trade risk-check service for agents.
Before a caller takes a separately controlled action, it asks Aegis for a
deterministic `BLOCK`, `WAIT`, or `EXECUTE` decision. Aegis returns the
score, confidence, reasons, structured risk factors, suggested action, and
hash-linked local proof the caller can inspect and retain.

Aegis checks risk before execution. Aegis does not execute.

## Problem

Execution-capable agents can move faster than their safety review. Their
proposed actions may rely on incomplete market data, elevated volatility,
unacceptable slippage, weak liquidity, or portfolio overexposure. A caller
needs a consistent risk checkpoint it can compose before its own action without
delegating custody or control.

Most demos collapse analysis, signaling, and execution into one agent. That
makes it difficult to audit where a decision came from and who controlled the
later action.

## Solution

Aegis separates risk classification from execution:

1. The caller submits a proposed action and evidence.
2. A deterministic policy evaluates guard conditions.
3. Aegis returns `BLOCK`, `WAIT`, or `EXECUTE`.
4. The response includes reasons, structured factors, and request/response hashes.
5. The caller decides whether to stop, pause, or continue its own workflow.

This contract makes Aegis useful as a callable risk-check API, DeFAI safety
agent, agent-to-agent risk guard, and future paid service candidate while
preserving a strict non-execution boundary.

## Technical architecture

| Component | Responsibility |
| --- | --- |
| FastAPI service | Exposes health, risk, A2A mock, local order/proof, and CAP status routes |
| Deterministic risk oracle | Applies versioned guards and maps score thresholds to decisions |
| Risk schemas | Validate required action fields and optional market/portfolio evidence |
| Proof generation | Hashes canonical local request and response payloads |
| Mock A2A requester | Maps decisions to `REFUSED`, `DELAYED`, or `SIMULATED_EXECUTION_ONLY` |
| In-memory order ledger | Exercises a CAP-shaped local order and proof contract |
| Gated CAP adapter | Defaults to mock and fails closed for unapproved real behavior |
| Provider presence runtime | Real, non-mutating `croo-sdk` WebSocket connection; live-verified to flip the registered Agent's CROO Dashboard status OFFLINE to ONLINE |
| Provider lifecycle wiring | Real `croo-sdk` accept/deliver calls, gated and allowlisted; implemented and fake-SDK tested, not yet run against a live paid order |
| Web Console | Runs deterministic scenarios and displays posture, reasons, and proof |

The local API routes are documented in the product-first README. The runtime
defaults to `CAP_MODE=mock`, reports `real_cap_ready=false`, and preserves
`live_execution_authorized=false` and `mutating_methods_called=false`.

## A2A composability

A caller composes Aegis immediately before its own controlled action:

```text
caller proposal
    -> Aegis risk check
        -> decision + reasons + proof
            -> caller-controlled branch
```

- `BLOCK -> REFUSED`
- `WAIT -> DELAYED`
- `EXECUTE -> SIMULATED_EXECUTION_ONLY`

The caller retains the request, response, hashes, and policy version. Aegis
never submits the caller's downstream action.

## Innovation

Aegis treats risk review as a separately callable, proof-backed agent service
rather than bundling it into a signal or execution product. Its useful output
is not a prediction or trade; it is an inspectable decision contract another
agent can compose, record, and challenge.

The distinction matters:

- deterministic policy instead of opaque action selection;
- structured risk evidence instead of a bare score;
- versioned hash-linked proof instead of decorative status copy;
- caller-controlled branching instead of delegated execution;
- fail-closed CAP gates instead of simulated production claims.

## Usability and real adoption path

Available locally today:

- a Windows PowerShell quickstart;
- a Web Console at `http://127.0.0.1:8000/`;
- complete JSON request and response documentation;
- deterministic EXECUTE, WAIT, and BLOCK scenarios;
- mock A2A composition;
- local order and proof retrieval;
- explicit CAP readiness status.

Adoption path:

1. Verify clean-environment setup and public repository access.
2. Retain the owner-approved Apache-2.0 license in the root `LICENSE` file.
3. Verify the current CROO listing form and publish reviewed service copy.
4. Measure the draft price and service window in a controlled pilot.
5. Complete separately approved real-CAP readiness work.
6. Claim paid operation only after direct lifecycle evidence exists.

The 0.12 USDC pilot price and five-minute service window are provisional
positioning, not proof of payment or a production service level.

## Proposed judging-criteria mapping

This is an internal review map pending confirmation of the official rubric.

| Proposed criterion | Aegis evidence |
| --- | --- |
| Technical execution | Reproducible API, typed schemas, deterministic policy, tests, proofs, and fail-closed boundaries |
| A2A composability | Caller requests a decision and proof before its own controlled action |
| Innovation | Proof-backed pre-action risk layer separated from signals and execution |
| Usability and adoption | Web Console, PowerShell setup, schemas, listing copy, and bounded pilot path |
| Presentation | Product-first README, concise walkthrough path, verified/pending evidence table |

## Setup instructions

Use the product-first [README](../README.md) for the shortest path and the
[Step 8-C operations runbook](operations/step8c-product-operation-and-marketplace-readiness.md)
for detailed local validation.

The safe local start is:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:CAP_MODE = "mock"
.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

No CROO provider listener or real lifecycle action is part of setup.

## Submission links

| Artifact | Draft value | Verification needed |
| --- | --- | --- |
| Official program page | `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]` | Confirm host, program, rules, and form |
| Deadline | `[VERIFY_DORAHACKS_DEADLINE_AND_TIMEZONE]` | Confirm date, time, and timezone |
| Public repository | `[VERIFY_PUBLIC_REPO_URL]` | Confirm anonymous access and no exposed secrets |
| CROO Store listing | `[VERIFY_CROO_STORE_URL]` | Confirm visible Aegis listing |
| Video walkthrough | `[VERIFY_VIDEO_URL]` | Confirm public playback and final claims |
| Live demo | `[VERIFY_DEMO_URL_OR_NOT_APPLICABLE]` | Do not substitute the local URL as a public deployment |

## Track recommendation

Recommended, pending the official taxonomy:

1. Data & Verification Agents.
2. DeFi / On-chain Ops Agents.

These recommendations describe Aegis's product fit. They are not verified names
of selectable DoraHacks tracks.

## Verified versus pending requirements

| Item | Status | Evidence or action |
| --- | --- | --- |
| CROO CAP describes provider capabilities, schema, pricing, SLA, and proof | verified | Official CAP page accessed 2026-07-02: https://cap.croo.network/ |
| CROO exposes an Agent Store surface | verified | Official Store accessed 2026-07-02: https://agent.croo.network/ |
| Official DoraHacks CROO program URL | unknown | Verify the live DoraHacks page directly |
| Submission deadline and timezone | unknown | Record official form evidence |
| Mandatory BUIDL fields | unknown | Capture the current official form |
| Official judging rubric | unknown | Capture current criteria before final mapping |
| Official track names | unknown | Confirm selectable tracks |
| Public repository access | unknown | Test anonymously |
| Aegis Store listing | missing | Publish only after official requirement review |
| Public video | missing | Record and verify later |
| Owner-approved license | verified | Apache-2.0; canonical text is present in the root `LICENSE` file |
| Provider Agent reproducibly ONLINE | verified | Real WebSocket connection reproduced Dashboard OFFLINE→ONLINE transition; see [owner-verified CROO Dashboard state](owner-verified-croo-dashboard-state-2026-07-04.md) |
| Real CAP lifecycle wiring implemented | verified (offline) | `accept_negotiation`/`deliver_order` wired, gated, and fake-SDK tested; never run live |
| Real paid lifecycle evidence | missing | No funded requester Agent exists yet; not invented, keep claim absent |

## Submission safety statement

Aegis is not a trading bot, execution bot, swap bot, wallet manager, signal
seller, profit generator, or private-key agent. It has no wallet custody,
signing, transaction construction, broadcast, or live-trading path. It does not
claim guaranteed safety, a real payment, escrow, delivery, settlement,
accepting-orders status, production SLA, or commercial readiness.

Before submission, compare every external claim with the
[compliance and evidence checklist](compliance-evidence-checklist.md).
