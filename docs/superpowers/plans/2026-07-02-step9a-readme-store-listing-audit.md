# Step 9-A: README and Store Listing Package Audit

Date: 2026-07-02

Baseline: `d349ece54b6ece75de0681077f14c73044a3e42a`

Status: Audit complete; implementation deferred to Step 9-B

## Evidence Rule

Official CROO and DoraHacks requirements are time-sensitive. Step 9-B must
verify current official sources and replace placeholders with dated evidence.
Nothing in this audit should be treated as an official rule from AI memory.

## 1. Current Documentation Status

Already strong:

- README positions Aegis as a callable pre-trade risk oracle, explains
  BLOCK/WAIT/EXECUTE, includes a PowerShell quickstart, and states that Aegis
  never executes.
- The Web Console provides deterministic scenarios, mock A2A interaction,
  local order/proof retrieval, copyable hashes, and honest CAP status.
- The Step 8-C operations runbook provides a one-command local start,
  validation path, schemas, Store positioning, and video walkthrough sequence.
- `DESIGN.md` preserves canonical claims and safety language.
- Tests cover API contracts, decision thresholds, proof fields, A2A mappings,
  Web Console claims, and static assets.

Material gaps:

1. **P0 — LICENSE is missing.** The owner must choose it; agents must not.
2. **P0 — README price is stale.** It says 0.25 USDC; the current pilot draft
   is 0.12 USDC.
3. **P0 — Official CROO/DoraHacks rules and deadlines are not evidenced.**
4. **P0 — Public repository and Agent Store listing status are unverified.**
5. **P1 — README follows old implementation steps instead of the buyer path.**
6. **P1 — No consolidated endpoint, response, or proof-schema reference.**
7. **P1 — A2A explanation is correct but too brief for integrators.**
8. **P1 — No standalone Store listing, DoraHacks draft, or compliance file.**
9. **P2 — Web Console URL and reproducibility checks are not prominent.**
10. **P2 — Video, screenshots, and submission links remain placeholders.**

## 2. Missing or Weak Items for Top 1

| Gap | Judging impact | Required correction |
| --- | --- | --- |
| Missing license | Technical Execution, Adoption | Add only an owner-approved license |
| 0.25/0.12 price conflict | Usability, Presentation | Use 0.12 USDC as explicit pilot positioning |
| Unverified official rules | Technical Execution | Record official URLs, access dates, and evidence |
| Step-history README | Usability, Presentation | Lead with product, run, call, proof, integrate, verify |
| Weak schema/proof reference | Technical Execution, A2A | Add compact exact field tables and examples |
| Weak A2A walkthrough | A2A Composability | Show caller → Aegis → decision/proof → caller branch |
| No Store/submission evidence | Adoption, Presentation | Create drafts, then replace links only when verified |

## 3. README Requirements

Step 9-B should restructure README, not append another long section.

1. **Product one-liner:** “Pre-trade risk oracle that returns BLOCK, WAIT, or
   EXECUTE with proof before a caller acts.”
2. **Positioning:** risk-check API, DeFAI safety agent, A2A risk guard, paid
   callable-service candidate. Aegis checks risk; it does not execute.
3. **Quickstart:** prerequisites, clone/change-directory, virtual environment,
   install, verify, and run commands.
4. **Local run command:** use the explicit virtual-environment Python path and
   `CAP_MODE=mock` from the Step 8-C runbook.
5. **Web Console URL:** `http://127.0.0.1:8000/`.
6. **Endpoint table:** method, path, purpose, and posture for:
   - `GET /`
   - `GET /health`
   - `POST /risk-check`
   - `POST /a2a/mock-order`
   - `POST /orders`
   - `GET /orders/{order_id}`
   - `GET /proof/{proof_id}`
   - `GET /cap/status`
   - `POST /cap/order` labeled local/mock only.
7. **Examples:** one complete deterministic request and representative response.
8. **Proof schema:** distinguish direct risk proof from local order proof; state
   that both are local log attestations, not on-chain proof.
9. **A2A workflow:** BLOCK → REFUSED, WAIT → DELAYED, EXECUTE →
   SIMULATED_EXECUTION_ONLY; caller controls any later action.
10. **CAP-ready boundary:** `CAP_MODE=mock`, `real_cap_ready=false`,
    `live_execution_authorized=false`, `mutating_methods_called=false`.
11. **Verification:** focused and full test commands plus current evidence link;
    avoid permanently hard-coding stale pass counts.
12. **Safety limits:** no wallet, signing, swap, transaction, broadcast, live
    trading, profit, guaranteed-safety, or real paid-lifecycle claim.
13. **License:** link the owner-approved root license or show it as a blocker.

Keep the core README readable in under five minutes. Link the Step 8-C runbook
for operational detail instead of duplicating it.

## 4. CROO Store Listing Package

These are draft product fields until verified against the current official
CROO source.

| Field | Draft |
| --- | --- |
| Agent name | Aegis Risk Oracle |
| Service name | Aegis Risk Check |
| Short tagline | Pre-trade risk oracle that returns BLOCK, WAIT, or EXECUTE with proof before a caller acts |
| Categories/tracks | Data & Verification Agents; DeFi / On-chain Ops Agents |
| Pilot price | 0.12 USDC per call; positioning only until real payment is verified |
| SLA draft | Five-minute service window; not a production guarantee |

Long description must cover the buyer problem, structured decision and proof,
A2A pre-execution integration, differentiation from execution/signal bots, and
the current mock/gated status.

### Buyer/requester input schema

| Field | Type | Required |
| --- | --- | --- |
| `token` | string | yes |
| `chain` | string | yes |
| `intended_action` | string | yes |
| `size_usd` | non-negative number | yes |
| `market_signal` | object | no |
| `portfolio_context` | object | no |

### Deliverable/output schema

- `decision`, `risk_score`, `confidence`, `market_regime`
- `safe_to_execute` as advice, never authorization
- `risk_factors`, `reasons`, `suggested_action`
- `proof`

### Proof fields

- Direct risk proof: `request_hash`, `response_hash`, `policy_version`.
- Local order proof: `proof_id`, `order_id`, `request_hash`, `response_hash`,
  `result_hash`, `policy_version`, `deliverable_type`, `created_at`.

### WAIT, BLOCK, no-go, failure, and refund wording

> BLOCK and WAIT are valid risk-check deliverables, not service failures.
> BLOCK advises stop; WAIT advises pause or review. Invalid requests should
> return a documented API error and no risk decision. Any charge, refund, or
> cancellation behavior must follow verified CROO rules and a separately
> approved paid lifecycle. Aegis currently claims no real charge, refund,
> escrow, settlement, or paid-order handling.

### Exact honest boundaries

Allowed:

- “Other agents can hire Aegis before they execute.”
- “Aegis returns BLOCK, WAIT, or EXECUTE with proof.”
- “CAP-ready gated runtime; real payment, delivery, settlement, and commercial
  readiness are not claimed yet.”
- “No wallet, signing, swap, transaction, or broadcast path.”

Not allowed until verified: real payment/refund/escrow/delivery/settlement,
online or accepting-orders status, commercial readiness, production SLA,
guaranteed safety, profit, or live execution.

## 5. DoraHacks Submission Package

Verify the official current form before treating these as mandatory fields.

| Item | Draft or placeholder |
| --- | --- |
| Project summary | Proof-backed pre-trade risk oracle for agents |
| Repository link | `[VERIFY_PUBLIC_REPO_URL]` |
| Store listing link | `[VERIFY_CROO_STORE_URL]` |
| Video walkthrough link | `[VERIFY_VIDEO_URL]` |
| Setup instructions | Product-first README plus Step 8-C runbook |
| Tracks | Data & Verification Agents; DeFi / On-chain Ops Agents |

Judging mapping:

- **Technical Execution:** reproducible API, deterministic policy, proofs,
  tests, and fail-closed boundaries.
- **A2A Composability:** caller agent requests a decision before its action.
- **Innovation:** proof-backed risk layer, not an execution or signal bot.
- **Usability & Adoption:** Web Console, schemas, Store copy, price/SLA draft.
- **Presentation:** concise README, verified links, walkthrough, honest status.

## 6. Compliance Checklist

Status values: `pass`, `missing`, `pending`, `unknown`.

| Mandatory/review item | Evidence placeholder | Status | Source link placeholder | Owner/action |
| --- | --- | --- | --- | --- |
| Official CROO requirements | Dated rule capture | unknown | `[OFFICIAL_CROO_RULES_URL]` | Submission lead: verify current source |
| Official DoraHacks requirements/deadline | Dated form and deadline capture | unknown | `[OFFICIAL_DORAHACKS_URL]` | Submission lead: verify source and timezone |
| Repository visibility | Anonymous public access capture | unknown | `[PUBLIC_REPO_URL]` | Repo admin: verify without exposing secrets |
| License | Root file and README link | missing | `[APPROVED_LICENSE_URL]` | Owner: choose license |
| CAP/CROO integration status | Status/truth-table evidence | pass | `[CAP_STATUS_EVIDENCE]` | Maintainer: preserve mock/gated wording |
| Agent Store listing status | Visible listing capture | missing | `[STORE_LISTING_URL]` | Store operator: create after rule check |
| Setup reproducibility | Clean-environment transcript | pending | `[SETUP_EVIDENCE]` | Maintainer: verify Step 9-B docs |
| API/proof schemas | Source-linked tables/sample | pending | `[SCHEMA_EVIDENCE]` | Maintainer: verify against code |
| A2A workflow | Mock-order transcript | pass | `[A2A_EVIDENCE]` | Maintainer: surface in README |
| Video walkthrough | Public checked link | missing | `[VIDEO_URL]` | Presentation lead: record later |
| DoraHacks BUIDL fields | Reviewed draft | missing | `[BUIDL_DRAFT]` | Submission lead: create draft |
| Store copy, price, SLA | Versioned draft | pending | `[STORE_DRAFT]` | Product lead: create draft |
| No fake CAP/commercial claims | Scan and review sign-off | pass | `[CLAIM_SCAN]` | Safety reviewer: rerun before release |
| No secrets in artifacts | Secret scan and manual review | pending | `[SECRET_SCAN]` | Security reviewer: verify before push |

Do not convert `unknown`, `missing`, or `pending` to `pass` without evidence.

## 7. Risks That Could Hurt Top 1

1. Fake CAP or paid-lifecycle wording destroys trust.
2. Unclear setup prevents judge verification.
3. Weak A2A explanation makes Aegis look like a standalone dashboard.
4. A long, step-history README buries the product; a vague README hides proof.
5. Missing hash semantics makes evidence look decorative.
6. A listing draft is not evidence of a visible Store listing.
7. No compliance checklist invites last-minute submission failure.
8. Conflicting 0.25/0.12 pricing looks commercially careless.
9. Missing license blocks clear open-source reuse terms.

## 8. Recommended Step 9-B Scope

Documentation/package files only:

1. Rewrite README into the product-first structure above.
2. Create a CROO Store listing draft.
3. Create a DoraHacks submission draft.
4. Create a standalone evidence-based compliance checklist.
5. Add a license only after explicit owner selection.

Do not change runtime code, tests, API behavior, safety gates, or CAP posture
unless separately approved.

## Recommended Step 9-B Prompt

> Implement Step 9-B from the committed Step 9-A audit. Update README and
> create concise CROO Store, DoraHacks, and compliance drafts. Verify current
> official CROO/DoraHacks sources before asserting requirements. Keep 0.12
> USDC and the five-minute SLA explicitly pilot/draft positioning. Preserve
> `CAP_MODE=mock`, `real_cap_ready=false`,
> `live_execution_authorized=false`, and `mutating_methods_called=false`.
> Do not change runtime code, tests, or API behavior. Do not choose a license
> without explicit owner approval. Do not claim real payment, escrow,
> delivery, settlement, commercial readiness, wallet execution, profit, or
> guaranteed safety.
