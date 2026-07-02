# Aegis Compliance and Evidence Checklist

Date: 2026-07-02
Scope: Step 9-B documentation and marketplace/submission readiness
Product boundary: Aegis is a pre-trade risk oracle, risk-check API, DeFAI
safety agent, and A2A risk guard. Aegis checks risk before execution. Aegis
does not execute. `CAP_MODE=mock` is the default; `real_cap_ready=false`,
`live_execution_authorized=false`, and `mutating_methods_called=false`.
The 0.12 USDC pilot price is provisional. Real CAP payment, escrow, delivery,
settlement, and commercial readiness are not claimed. No owner-approved root
license exists, so license selection remains pending owner approval.


## Status definitions

- `pass`: direct repository or official-source evidence supports the item.
- `missing`: the required artifact or evidence does not exist.
- `pending`: work or verification is identified but not complete.
- `unknown`: the authoritative requirement or current external state is not known.

Do not convert `missing`, `pending`, or `unknown` to `pass` without
recording evidence. A local draft is not evidence of external publication.

## Checklist

| Mandatory or review item | Status | Evidence | Official source URL placeholder | Access date | Owner/action | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Official CROO protocol model | pass | CAP page describes provider capability, pricing, SLA, schema, proof, and lifecycle | https://cap.croo.network/ | 2026-07-02 | Submission lead: retain dated capture | Does not prove Aegis integration or listing |
| Exact CROO listing requirements | unknown | No authoritative current form captured | `[VERIFY_OFFICIAL_CROO_LISTING_REQUIREMENTS_URL]` | ? | Store operator: inspect live form | Do not infer required fields from this draft |
| Official DoraHacks program and deadline | unknown | No authoritative program page or deadline capture | `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]` | ? | Submission lead: verify deadline and timezone | Third-party summaries are not accepted evidence |
| Repository visibility | unknown | Local Git checkout only | `[VERIFY_PUBLIC_REPO_URL]` | ? | Repo admin: test anonymous access | Review history and artifacts for secrets first |
| License | missing | No owner-approved root license | `[APPROVED_LICENSE_URL]` | ? | Owner: select license explicitly | No agent should choose it |
| Setup reproducibility | pending | README and Step 8-C commands documented | `[SETUP_EVIDENCE]` | ? | Maintainer: run clean-environment setup later | Current pass does not start the app |
| Product-first README | pass | `README.md` rewritten and checked in Step 9-B | `[README_COMMIT_URL]` | 2026-07-03 | Maintainer: retain commit evidence | Product positioning and boundaries reviewed |
| Endpoint documentation | pass | README table mapped to `apps/api/main.py` and route modules | `[SCHEMA_EVIDENCE]` | 2026-07-02 | Maintainer: recheck after API changes | Covers all current public routes |
| Request and response schemas | pass | README and Store draft mapped to Pydantic models | `[SCHEMA_EVIDENCE]` | 2026-07-02 | Maintainer: retain source mapping | Optional nested-field constraints documented |
| Web Console | pass | `apps/web/index.html`, `apps/web/app.js`, and existing console tests | `[WEB_CONSOLE_EVIDENCE]` | 2026-07-02 | Maintainer: run cheap console test | Local URL only; not a public deployment |
| CROO Store listing draft | pass | `docs/croo-store-listing-draft.md` | `[STORE_DRAFT_COMMIT_URL]` | 2026-07-02 | Product lead: review copy | Draft does not prove publication |
| Published CROO Store listing | missing | No visible Aegis listing captured | `[VERIFY_CROO_STORE_URL]` | ? | Store operator: publish after rule review | Do not claim online or accepting orders |
| CAP/CROO integration status | pass | `docs/aegis-cap-truth-table.md`, `GET /cap/status`, guarded runtime | `[CAP_STATUS_EVIDENCE]` | 2026-07-02 | Maintainer: preserve mock/gated wording | `CAP_MODE=mock`; `real_cap_ready=false`; `live_execution_authorized=false`; `mutating_methods_called=false` |
| A2A proof/order flow | pass | Local routes, schemas, Web Console, and existing tests | `[A2A_EVIDENCE]` | 2026-07-02 | Maintainer: retain local/mock qualifier | In-memory evidence, not on-chain proof |
| Pilot price and draft service window | pass | 0.12 USDC and five-minute draft consistently documented | `[STORE_DRAFT_COMMIT_URL]` | 2026-07-02 | Product lead: approve before publication | Not payment evidence or production SLA |
| Video walkthrough | missing | No verified public video URL | `[VERIFY_VIDEO_URL]` | ? | Presentation lead: record and review | Use the Step 8-C under-five-minute sequence |
| DoraHacks BUIDL fields | unknown | Draft content exists; official form not captured | `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]` | ? | Submission lead: map live form fields | Do not call draft headings mandatory |
| DoraHacks submission draft | pass | `docs/dorahacks-submission-draft.md` | `[DORAHACKS_DRAFT_COMMIT_URL]` | 2026-07-02 | Submission lead: review after official-source capture | Not a submitted BUIDL |
| Claim-safety scan | pass | Contextual text scan across the four Step 9-B docs | `[CLAIM_SCAN_EVIDENCE]` | 2026-07-03 | Safety reviewer: retain command output | Matches occur only in explicit negative boundaries |
| Secrets check | pending | No secret values intentionally added | `[SECRET_SCAN_EVIDENCE]` | ? | Security reviewer: scan changed artifacts | Never print real credentials during review |
| No wallet/signing/swap/transaction/broadcast path | pass | Runtime and UI source review; documentation states absence | `[CAPABILITY_SCAN_EVIDENCE]` | 2026-07-02 | Safety reviewer: confirm runtime diff is zero | Words may appear only in explicit boundaries |
| No live-trading path | pass | Runtime source review and zero-runtime-change requirement | `[CAPABILITY_SCAN_EVIDENCE]` | 2026-07-02 | Safety reviewer: confirm runtime diff is zero | No claim of live operation |
| No profit or guaranteed-safety claim | pass | Contextual scan found only explicit negative boundaries | `[CLAIM_SCAN_EVIDENCE]` | 2026-07-03 | Safety reviewer: repeat before publication | No positive claim found |
| No fake real CAP payment/escrow/delivery/settlement claim | pass | Drafts distinguish local/mock from pending real lifecycle | `[CLAIM_SCAN_EVIDENCE]` | 2026-07-03 | Safety reviewer: repeat before publication | Negative disclaimers are expected |
| Runtime code unchanged | pass | Git status lists only the four intended docs | `[GIT_DIFF_EVIDENCE]` | 2026-07-03 | Maintainer: retain status evidence | Runtime changes: zero |
| Tests unchanged unless documentation checks require it | pass | Git status lists only the four intended docs | `[GIT_DIFF_EVIDENCE]` | 2026-07-03 | Maintainer: retain status evidence | Test changes: zero; no pytest run required |
| `git diff --check` | pass | Command exited zero before staging | `[DIFF_CHECK_EVIDENCE]` | 2026-07-03 | Maintainer: repeat against staged diff | Whitespace check passed |
| Final commit | pass | This checklist is included in the Step 9-B documentation commit | `[STEP_9B_COMMIT_URL]` | 2026-07-03 | Maintainer: attach remote URL if later published | Branch retained locally; do not push |

## Official-source record

| Source | What it supports | What it does not support |
| --- | --- | --- |
| https://cap.croo.network/ | General CAP positioning, provider capability listing, pricing/SLA/schema language, proof, and lifecycle | Aegis readiness, a completed Aegis lifecycle, exact Store form requirements |
| https://agent.croo.network/ | Existence of the official Agent Store surface | Aegis publication, category choices, accepting-orders status |
| https://docs.croo.network/ | General CROO architecture context | Exact Aegis submission or listing state |
| `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]` | Pending | Until verified, no deadline, field, track, or rubric assertion |

## Release claim gate

Before a public submission or listing, all of the following must be true:

- Official requirements and deadlines have dated source evidence.
- Repository visibility and license status are resolved.
- Public links work without privileged access.
- Setup is reproduced from a clean environment.
- Schema and endpoint copy matches the release commit.
- Claim and secret scans are recorded.
- The Store listing and BUIDL are distinguished from their local drafts.
- Any real-CAP or commercial claim has separate direct evidence.
