# Aegis Compliance and Evidence Checklist

Date: 2026-07-03
Scope: Step 9-C official source verification and submission readiness

Product boundary: Aegis is a pre-trade risk oracle, risk-check API, DeFAI
safety agent, and A2A risk guard. Aegis checks risk before execution. Aegis
does not execute. `CAP_MODE=mock` is the default; `real_cap_ready=false`,
`live_execution_authorized=false`, and `mutating_methods_called=false`.
The 0.12 USDC pilot price is provisional. Real CAP payment, escrow, delivery,
settlement, and commercial readiness are not claimed. The owner approved the
Apache License, Version 2.0 (`Apache-2.0`), and the canonical text is present
in the root `LICENSE` file.

## Evidence discipline

- External requirements use an official source URL, an access date, and a
  bounded evidence note.
- A page proving that a platform or protocol exists does not prove that Aegis
  is listed, online, paid, delivered, settled, or commercially ready.
- Public counts and page contents are point-in-time observations.
- Unavailable official forms, rules, deadlines, and taxonomies remain
  `pending` or `unknown`; third-party summaries are not final evidence.
- Internal evidence cites repository files at baseline
  `55acfb14087f08236b40ca0250579567bdecb7eb`.

## Status definitions

- `pass`: direct repository or official-source evidence supports the item.
- `missing`: the required artifact or evidence does not exist.
- `pending`: work or verification is identified but not complete.
- `unknown`: the authoritative requirement or current external state is not known.

Do not convert `missing`, `pending`, or `unknown` to `pass` without
recording evidence. A local draft is not evidence of external publication.

## Checklist

| Mandatory or review item | Status | Evidence | Source URL | Access date | Owner/action | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Official CROO CAP model | pass | Official CAP page describes provider capability listing with pricing, SLA, and acceptance schema; a verification-first Negotiate-Lock-Deliver-Clear lifecycle; and execution remaining in the provider runtime | https://cap.croo.network/ | 2026-07-03 | Submission lead: retain dated capture | Supports the protocol model, not Aegis readiness or a completed lifecycle |
| Official CROO architecture context | pass | Official docs describe CROO as infrastructure for agent identity, coordination, settlement, reputation, and provenance | https://docs.croo.network/ | 2026-07-03 | Submission lead: retain dated capture | General architecture only; not listing or submission rules |
| CROO Agent Store surface | pass | Official Store page exposes the Agent Store, agent/service discovery copy, and a Register Agent entry point | https://agent.croo.network/ | 2026-07-03 | Store operator: retain dated capture | Does not disclose the complete registration form or prove Aegis is listed |
| Exact CROO listing requirements | unknown | Public Store page did not expose authoritative field limits, category taxonomy, publication rules, or refund requirements | https://agent.croo.network/ | 2026-07-03 | Store operator: verify the current official registration form | Keep `[VERIFY_OFFICIAL_CROO_LISTING_REQUIREMENTS_URL]` unresolved |
| Published Aegis Store listing | missing | Official Store page reported zero agents at access time and displayed no Aegis listing | https://agent.croo.network/ | 2026-07-03 | Store operator: publish only after requirement review | Point-in-time observation; do not claim online or accepting-orders status |
| Official CROO SDK organization | pass | Official CAP page links to the public CROO Network GitHub organization, which exposes public Node, Go, Python, and contract repositories | https://github.com/CROO-Network | 2026-07-03 | Maintainer: use only for official SDK/protocol reference | Does not prove Aegis repository visibility or integration |
| Official DoraHacks announcement of CROO event | pass | DoraHacks-branded announcement lists the CROO Agent Hackathon and advertises a June 9-July 11, 2026 event range | https://www.linkedin.com/pulse/hackathon-newsletter-june-2026-ii-dorahacks-dorahacks-r4izc | 2026-07-03 | Submission lead: retain dated capture | Announcement evidence only; not the authoritative submission form |
| Official DoraHacks program page | unknown | No accessible authoritative CROO program/rules page was captured from the available official DoraHacks web surface | `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]` | not verified | Submission lead: open and archive the live official program page | Do not substitute third-party event summaries |
| Submission deadline and timezone | unknown | Official announcement provides an event range but no authoritative submission cutoff time or timezone | `[VERIFY_DORAHACKS_DEADLINE_AND_TIMEZONE]` | not verified | Submission lead: capture the official deadline and timezone | Do not infer a cutoff from the advertised event range |
| Mandatory DoraHacks BUIDL fields | unknown | No authoritative current BUIDL submission form was captured | `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]` | not verified | Submission lead: map the live form fields | Draft headings are not asserted as mandatory fields |
| Official judging rubric | unknown | No authoritative current CROO judging rubric was captured | `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]` | not verified | Submission lead: capture the official rubric | Current mapping remains an internal proposal |
| Official track taxonomy | unknown | No authoritative selectable track list was captured | `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]` | not verified | Submission lead: capture the live taxonomy | Current track names remain recommendations |
| Repository visibility | unknown | Local checkout is available, but no verified anonymous public Aegis repository URL was established | `[VERIFY_PUBLIC_REPO_URL]` | not verified | Repo admin: test anonymous access after a secret/history review | Search absence is not proof that a repository is private |
| License | pass | Owner explicitly approved Apache License 2.0; the root `LICENSE` contains the canonical Apache-2.0 text | https://www.apache.org/licenses/LICENSE-2.0.txt; `LICENSE` | 2026-07-03 | Maintainer: preserve the approved license artifact and identifier | SPDX identifier: `Apache-2.0`; owner decision recorded 2026-07-03 |
| Setup reproducibility | pass | Clean public clone at `38fd079e93b435fcaedda52de4b41cdb5c1b0a3f`: Windows PowerShell venv/install passed; 287 tests passed with one deprecation warning; local mock app, healthy dry-run `/health`, mock `/cap/status`, and the documented EXECUTE score-0 risk fixture with 64-character proof hashes passed | https://github.com/tonielivegood/aegis-croo; `README.md` | 2026-07-04 | Maintainer: repeat against the final release candidate | Reproducible after README public URL placeholder fix; no secrets or live application/CAP/CROO calls; only GitHub/PyPI setup traffic |
| Product-first README completeness | pass | README includes positioning, quickstart, Web Console URL, routes, examples, proof semantics, A2A flow, order/proof flow, CAP boundary, verification, safety, pricing, and license status | `README.md` | 2026-07-03 | Maintainer: recheck after documentation changes | Internal repository evidence |
| Endpoint documentation | pass | README documents the current root, health, risk, A2A mock, local order/proof, CAP status, and local/mock CAP order routes | `README.md`; `apps/api/main.py`; `apps/api/routes/` | 2026-07-03 | Maintainer: recheck after API changes | Source-mapped internal evidence |
| Request and response schemas | pass | README and Store draft document risk inputs, decisions, factors, advice, and direct/local proof fields | `README.md`; `docs/croo-store-listing-draft.md`; `src/aegis_croo/schemas/` | 2026-07-03 | Maintainer: retain source mapping | Internal evidence; proof is local, not on-chain |
| Web Console availability | pass | Static console source and route wiring exist in the repository | `apps/web/index.html`; `apps/web/app.js`; `apps/api/main.py` | 2026-07-03 | Maintainer: validate separately before public release | Local implementation evidence only; app not started in Step 9-C |
| CROO Store listing draft | pass | Versioned draft contains buyer copy, schemas, proof fields, provisional price, draft service window, A2A workflow, and publication gates | `docs/croo-store-listing-draft.md` | 2026-07-03 | Product lead: review after official form capture | Draft does not prove publication |
| CAP/CROO integration status | pass | Truth table and status documentation preserve mock/gated posture | `docs/aegis-cap-truth-table.md`; `README.md` | 2026-07-03 | Maintainer: preserve mock/gated wording | `CAP_MODE=mock`; `real_cap_ready=false`; no real lifecycle claim |
| CROO Agent registration | pass | Owner verified `Aegis Risk Oracle` as an existing registered Agent in the CROO Dashboard | `docs/owner-verified-croo-dashboard-state-2026-07-04.md` | 2026-07-04 | Owner: preserve non-secret Dashboard evidence | `PASS_VERIFIED`; current Dashboard status is `OFFLINE` |
| CROO Service configuration | pass | Owner verified the existing `Aegis Risk Check` Service, configured input and deliverable schemas, displayed 0.12 USDC price, five-minute SLA, and a truncated Service ID | `docs/owner-verified-croo-dashboard-state-2026-07-04.md` | 2026-07-04 | Owner: retain the full Service ID outside published evidence | `PASS_VERIFIED`; existence does not prove Store discoverability or a real order |
| CROO SDK/API key issuance | pass | Owner verified that a masked CROO SDK/API key has already been issued | `docs/owner-verified-croo-dashboard-state-2026-07-04.md` | 2026-07-04 | Security owner: keep the key in external secret infrastructure | `PASS_VERIFIED`; no key value is recorded, reconstructed, rotated, or committed |
| Official SDK provider ONLINE | pending | Dashboard currently shows the registered Agent as `OFFLINE` | `docs/owner-verified-croo-dashboard-state-2026-07-04.md` | 2026-07-04 | Maintainer and owner: verify through a separately approved ONLINE-readiness step | No provider heartbeat or `ONLINE` transition is claimed |
| WebSocket heartbeat | pending | No current official provider heartbeat is verified | `[VERIFY_PROVIDER_HEARTBEAT_EVIDENCE]` | not verified | Maintainer: verify connection-only behavior before any mutating CAP method | Must not infer from registration or key issuance |
| Public Store discoverability | pending | The Service exists, but public discoverability while online has not been verified | `[VERIFY_PUBLIC_STORE_LISTING_URL]` | not verified | Owner: verify anonymously after provider ONLINE status | Do not claim a published/discoverable listing yet |
| Real CAP lifecycle | pending | No verified real negotiation, on-chain order, payment lock, delivery, completion, or settlement exists | `[VERIFY_REAL_CAP_LIFECYCLE_EVIDENCE]` | not verified | Owner: require a separate controlled real-order authorization | `CAP_MODE=mock`; `real_cap_ready=false` |
| Controlled real order and human spot-check | pending | No controlled real order or human spot-check evidence exists | `[VERIFY_CONTROLLED_ORDER_AND_SPOT_CHECK]` | not verified | Owner and organizer: authorize and bound separately | Not part of ONLINE readiness |
| A2A proof/order flow | pass | README and runbook describe caller-controlled branching and in-memory order/proof retrieval | `README.md`; `docs/operations/step8c-product-operation-and-marketplace-readiness.md` | 2026-07-03 | Maintainer: retain local/mock qualifier | Local log attestation, not on-chain proof |
| Pilot price and draft service window | pass | Documentation consistently labels 0.12 USDC and five minutes as provisional draft positioning | `README.md`; `docs/croo-store-listing-draft.md` | 2026-07-03 | Product lead: approve before publication | Not payment evidence or a production SLA |
| Video walkthrough | missing | No verified public video URL exists in the package | `[VERIFY_VIDEO_URL]` | not verified | Presentation lead: record and review later | Use the bounded Step 8-C walkthrough |
| DoraHacks submission draft | pass | Draft separates reusable submission copy from unresolved official requirements and links | `docs/dorahacks-submission-draft.md` | 2026-07-03 | Submission lead: reconcile with official form | Not a submitted BUIDL |
| Claim-safety scan | pass | Contextual scan across README, compliance, Store, and DoraHacks docs | `[CLAIM_SCAN_EVIDENCE]` | 2026-07-03 | Safety reviewer: retain command output | Matches occur only in explicit negative or do-not-claim contexts |
| Formal secrets review | pass | Reviewed the current tracked tree and all reachable Git history: 61 commits and 188 unique blobs using a Git-native full-history fallback (`gitleaks` unavailable). No tracked `.env`, credential-shaped tracked files, wallet/private-key/mnemonic material, historical secret risk, deleted sensitive files, credible secret exposure, execution credential/path risk, or CAP/commercial false-claim risk was detected | Local Step 9-D-E command evidence; https://github.com/tonielivegood/aegis-croo | 2026-07-04 | Security reviewer: repeat with an approved dedicated scanner when available or after material repository changes | Secrets review passed: no credible current or historical secret exposure detected; this is not a guarantee that the repository is secret-free |
| No wallet/signing/swap/transaction/broadcast path | pass | README and runbook explicitly state the absence of these capabilities | `README.md`; `docs/operations/step8c-product-operation-and-marketplace-readiness.md` | 2026-07-03 | Safety reviewer: repeat after runtime changes | Documentation evidence; Step 9-C changes docs only |
| No live-trading path | pass | README and runbook explicitly state that no live-trading path exists | `README.md`; `docs/operations/step8c-product-operation-and-marketplace-readiness.md` | 2026-07-03 | Safety reviewer: repeat after runtime changes | No live operation claim |
| No profit or guaranteed-safety claim | pass | Contextual scan found only explicit negative safety boundaries | `[CLAIM_SCAN_EVIDENCE]` | 2026-07-03 | Safety reviewer: repeat before publication | No positive claim found |
| No fake real CAP payment/escrow/delivery/settlement claim | pass | Contextual scan found only explicit negative safety boundaries | `[CLAIM_SCAN_EVIDENCE]` | 2026-07-03 | Safety reviewer: repeat before publication | No positive real-lifecycle claim found |
| Runtime code unchanged | pass | Git diff lists only `docs/compliance-evidence-checklist.md` | `[GIT_DIFF_EVIDENCE]` | 2026-07-03 | Maintainer: retain status evidence | Runtime changes: zero |
| Tests unchanged | pass | Git diff lists only `docs/compliance-evidence-checklist.md` | `[GIT_DIFF_EVIDENCE]` | 2026-07-03 | Maintainer: retain status evidence | Test changes: zero |
| `git diff --check` | pass | Command exited zero before staging | `[DIFF_CHECK_EVIDENCE]` | 2026-07-03 | Maintainer: repeat against staged diff | Whitespace check passed |
| Step 9-C commit | pass | This checklist is included in the Step 9-C documentation commit | `[STEP_9C_COMMIT_URL]` | 2026-07-03 | Maintainer: attach a remote URL only if later pushed | Do not push |

## Official-source record

| Source | Verified evidence | Explicit limitation | Access date |
| --- | --- | --- | --- |
| https://cap.croo.network/ | CAP standardizes agent commerce; provider capabilities include pricing, SLA, and acceptance schema; delivery uses proof; the lifecycle is Negotiate-Lock-Deliver-Clear; execution remains in the provider runtime | Does not prove Aegis listing, connectivity, payment, delivery, settlement, or commercial readiness | 2026-07-03 |
| https://docs.croo.network/ | Official CROO architecture context covers agent identity, coordination, settlement, reputation, and provenance | Landing documentation does not define the Aegis listing or DoraHacks submission requirements | 2026-07-03 |
| https://agent.croo.network/ | Official Agent Store surface and Register Agent entry point exist; the public page reported zero agents at access time | Does not expose complete listing rules and does not prove Aegis is registered or accepting orders | 2026-07-03 |
| https://github.com/CROO-Network | Official organization exposes public SDK and protocol repositories | Does not prove Aegis repository visibility or completed CAP integration | 2026-07-03 |
| https://www.linkedin.com/pulse/hackathon-newsletter-june-2026-ii-dorahacks-dorahacks-r4izc | DoraHacks-branded announcement includes the CROO Agent Hackathon and an advertised June 9-July 11, 2026 event range | Does not provide an authoritative submission deadline/timezone, BUIDL form, rubric, or track taxonomy | 2026-07-03 |
| `[VERIFY_OFFICIAL_DORAHACKS_PROGRAM_URL]` | Pending | Until captured, no exact deadline, field, track, or rubric assertion is permitted | not verified |

## Release claim gate

Before a public submission or listing, all of the following must be true:

- Official requirements and deadline/timezone have dated source evidence.
- Repository visibility and license status are resolved.
- Public Store, repository, video, and submission links work without privileged access.
- Setup is reproduced from a clean environment.
- Schema and endpoint copy matches the release commit.
- Claim and secret scans are recorded.
- The Store listing and BUIDL are distinguished from their local drafts.
- Any real-CAP or commercial claim has separate direct evidence.

## Step 9-C source-verification note

No app was started. No live CAP/CROO API was called. No provider listener,
negotiation, paid order, payment, escrow, delivery, or settlement was
performed. Official public pages were reviewed as documentation evidence only.
