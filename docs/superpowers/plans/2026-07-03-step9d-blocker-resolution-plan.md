# Step 9-D Blocker Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve, or explicitly retain as unresolved, every remaining Aegis submission and marketplace-readiness blocker using direct evidence and owner-controlled decisions.

**Architecture:** Treat each blocker as an independent evidence gate with a named owner, a safe verification action, an acceptance condition, and a stop condition. Update the compliance checklist only after direct evidence exists; keep external publication, license selection, and real CAP lifecycle actions behind explicit owner approval.

**Tech Stack:** Git, Markdown, PowerShell, official CROO/CAP and DoraHacks web sources, repository-local evidence, and separately approved local/mock validation commands.

## Global Constraints

- Aegis checks risk before execution; Aegis does not execute.
- Do not modify runtime code or tests under this plan unless separately approved.
- Do not select or change a license without an explicit owner decision.
- Do not push or change repository visibility without explicit owner authorization.
- Do not start the app during planning. Any later setup or video run requires separate approval and must use `CAP_MODE=mock`.
- Do not call live CAP/CROO APIs, start a provider listener, negotiate, place a paid order, or perform a real lifecycle action.
- Do not read, print, copy, or commit secret values. Secret-scan evidence may contain only file paths, rule identifiers, counts, and redacted findings.
- Do not claim real CAP payment, escrow, delivery, settlement, accepting-orders status, or commercial readiness unless separately verified with authoritative evidence.
- External requirements require an official source URL, access date, bounded evidence note, owner/action, and `pass`, `missing`, `pending`, or `unknown` status.
- The provisional `0.12 USDC` pilot price and five-minute service window remain positioning only.

---

## File and Evidence Map

The execution phase may change only the files justified by verified evidence:

- Modify: `docs/compliance-evidence-checklist.md` — authoritative readiness status, evidence, source, date, owner, limitation, and next action.
- Modify: `docs/dorahacks-submission-draft.md` — verified program fields, deadline, rubric, tracks, repository URL, video URL, and submission link only after evidence exists.
- Modify: `docs/croo-store-listing-draft.md` — verified listing fields, limits, categories, policies, and public listing URL only after evidence exists.
- Modify: `README.md` — public repository, license, or release wording only when the corresponding owner decision and evidence are complete.
- Create after owner approval: `LICENSE` — exact owner-approved license text; Codex must not choose or infer it.
- Create during separately approved setup validation: `docs/evidence/step9d-setup-reproducibility.md` — redacted clean-environment commands, expected/actual results, commit, OS, and timestamp.
- Create during separately approved security review: `docs/evidence/step9d-secrets-review.md` — scan scope, tool/version, command class, redacted result summary, reviewer, and timestamp; never secret values.
- Create during video preparation: `docs/evidence/step9d-video-walkthrough-review.md` — script checklist, safety-claim review, final public URL, access result, and date.

Every execution task must begin with `git status --short --branch` and end with
`git diff --check` plus a changed-file review. Do not combine unrelated blocker
resolutions into one commit when an owner or reviewer could approve them
independently.

## Blocker Summary and Recommended Order

| Order | Blocker | Current status/evidence | Top 1 value | Resolver | Exact safe next action | Risk if skipped |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | Owner-approved license | `missing`; no root `LICENSE*` or `COPYING*` at the Step 9-C baseline | Removes reuse ambiguity and a common submission/repository completeness failure | Owner decision required; Codex may implement the exact approved choice | Owner supplies the approved license identity and exact text or authoritative template; Codex creates root `LICENSE` and updates license wording only after that approval | Reviewers cannot determine reuse rights; submission may be ineligible or look incomplete |
| 2 | Public repository visibility | `unknown`; local checkout exists but no anonymous public Aegis URL is verified | Lets judges inspect source and reproduce the product | Repo owner/admin controls visibility; Codex can verify anonymously after receiving the canonical URL | Record the canonical repository URL and test it without authenticated credentials; if private, report `missing` and do not change visibility until the owner authorizes publication and the secrets gate passes | Judges may be unable to inspect source; a premature visibility change could expose sensitive history |
| 3 | Setup reproducibility | `pending`; README and Step 8-C commands exist but no clean-environment transcript exists | Demonstrates technical execution and reduces judge setup friction | Codex can perform after separate approval to install dependencies and start the local app | From a clean checkout at the release commit, run the documented PowerShell setup with `CAP_MODE=mock`, validate health and the bounded local flows, stop the app, and record redacted evidence | A polished README may hide broken or incomplete setup; judges may abandon evaluation |
| 4 | Secrets review | `pending`; no secret was intentionally read in Step 9-C, but no repository/history scan is recorded | Protects users and makes public-repository/submission actions defensible | Security reviewer or Codex with explicit scan approval | Scan tracked files and reachable Git history using a non-printing/redacted workflow; record only paths, rule IDs, counts, and remediation status; stop before any public visibility change if a finding exists | Public release could expose credentials or private material; evidence artifacts could themselves leak secrets if mishandled |
| 5 | Official DoraHacks requirements | `unknown`; event announcement is verified, but program page, cutoff/timezone, BUIDL fields, rubric, and tracks are not | Prevents administrative disqualification and aligns the narrative with actual judging | Codex can research official public sources; owner may need authenticated form access | Capture the official program/rules/form URL, access date, exact deadline and timezone, required fields, rubric, and selectable tracks; retain `unknown` for anything not visible from an authoritative source | Wrong deadline, missing fields, or invented tracks/rubric can invalidate or weaken the submission |
| 6 | Exact CROO Store listing requirements | `unknown`; Store and Register Agent surface exist, but field limits, taxonomy, publication rules, and refund requirements are not verified | Converts the listing draft into form-ready, policy-aligned copy | Codex can inspect official public material; Store operator may need authenticated registration access | Capture the official registration form or documentation, record every required field and limit, then reconcile only verified differences in the Store draft | Listing may be rejected, truncated, miscategorized, or make unsupported commercial promises |
| 7 | Video walkthrough link | `missing`; Step 8-C contains a bounded under-five-minute sequence, but no verified public video exists | Gives judges a fast proof of product value, A2A flow, and honest boundaries | Codex can prepare/review the script; owner/presentation lead records and publishes | Review the Step 8-C sequence against the final release, record locally in mock mode under separate approval, run the claim-safety review, publish through an owner-approved channel, and verify anonymous playback | Judges lose the fastest evaluation path; an unreviewed video may overclaim live or commercial readiness |
| 8 | Published Aegis Store listing | `missing`; official Store showed no Aegis listing at the 2026-07-03 access | Demonstrates marketplace discoverability and a credible adoption path | Store operator/owner must authorize and publish; Codex can verify the resulting public page | After requirements, license, secrets, and final copy review pass, submit the listing through the official surface; verify the public URL anonymously before marking `pass` | Claiming a draft as published damages credibility; publishing too early may expose incomplete or noncompliant copy |
| 9 | Real CAP lifecycle evidence | `pending`/unverified; mock and gated contracts exist, but no real payment, escrow, delivery, or settlement is proven | Honest status is more valuable than a risky demo; real evidence matters only if the submission truly requires it | Owner authorization and a separately reviewed operational plan are mandatory | Keep the item `pending` and keep all real-lifecycle claims absent unless an owner separately approves a narrowly scoped, fail-closed verification plan | Fabricated or inferred evidence creates severe trust, financial, and safety risk; an unnecessary live test expands scope and exposure |

---

### Task 1: Obtain and Apply the Owner-Approved License Decision

**Files:**
- Create after approval: `LICENSE`
- Modify after approval: `README.md`
- Modify after approval: `docs/compliance-evidence-checklist.md`
- Modify if the form requires it: `docs/dorahacks-submission-draft.md`

**Interfaces:**
- Consumes: a written owner decision naming the license and approving its exact text.
- Produces: a root license artifact and evidence-backed license status.

- [ ] **Step 1: Ask the owner for a written license decision**

Require the owner to provide the license name/SPDX identifier and approve the
exact canonical text. Present options only if the owner asks for analysis; do
not recommend, select, or infer a license as part of execution.

- [ ] **Step 2: Stop if approval is absent or ambiguous**

Keep checklist status `missing` and README wording `Pending owner approval`.
Record no inferred reuse permission.

- [ ] **Step 3: Apply the exact approved artifact**

Create `LICENSE` from the approved canonical text. Update README and checklist
with the approved name, root path, decision date, and owner evidence reference.

- [ ] **Step 4: Verify scope and consistency**

Run:

```powershell
git diff --check
git diff --name-only
rg -n "license|LICENSE|COPYING" README.md docs/compliance-evidence-checklist.md docs/dorahacks-submission-draft.md
```

Expected: no whitespace errors; only approved documentation plus `LICENSE`
changed; every license statement agrees with the owner decision.

- [ ] **Step 5: Commit the independently reviewable result**

```powershell
git add -- LICENSE README.md docs/compliance-evidence-checklist.md docs/dorahacks-submission-draft.md
git commit -m "docs: add owner-approved project license"
```

Include only files actually changed.

### Task 2: Confirm Public Repository Visibility Without Changing It

**Files:**
- Modify: `docs/compliance-evidence-checklist.md`
- Modify after verification: `docs/dorahacks-submission-draft.md`
- Modify after verification if useful: `README.md`

**Interfaces:**
- Consumes: owner-confirmed canonical repository URL and current release commit.
- Produces: anonymous-access evidence or an honest `missing` result.

- [ ] **Step 1: Obtain the canonical repository URL from the repo owner**

Do not derive publication authority from a local remote. Record the URL only
after the owner confirms it is the intended submission repository.

- [ ] **Step 2: Test anonymous read access**

Use an unauthenticated browser session to open the repository landing page and
the raw `README.md` at the intended commit. Do not push, fork, change settings,
or expose a private URL in public copy.

- [ ] **Step 3: Classify the result**

- `pass`: anonymous landing-page and source access work at the intended commit.
- `missing`: the canonical repository is private or inaccessible.
- `unknown`: the owner has not supplied the canonical URL.

If visibility must change, stop and require owner authorization plus a passed
secrets review before changing any external setting.

- [ ] **Step 4: Record bounded evidence and commit**

Record URL, access date, tested paths, commit hash, result, owner/action, and
the limitation that public visibility does not prove setup reproducibility.
Update submission copy only on `pass`.

### Task 3: Capture Clean-Environment Setup Reproducibility

**Files:**
- Create: `docs/evidence/step9d-setup-reproducibility.md`
- Modify: `docs/compliance-evidence-checklist.md`
- Modify only if observed commands differ: `README.md`
- Modify only if observed commands differ: `docs/operations/step8c-product-operation-and-marketplace-readiness.md`

**Interfaces:**
- Consumes: a clean checkout at the intended release commit and separate permission to install dependencies/start the local app.
- Produces: a redacted setup transcript and verified or failed reproducibility status.

- [ ] **Step 1: Record the isolated test conditions**

Record OS, PowerShell version, Python version, commit hash, clean status, and
start time. Do not record environment-variable values except the literal safe
setting `CAP_MODE=mock`.

- [ ] **Step 2: Execute the documented clean setup under separate approval**

Use the README commands to create `.venv`, install `requirements.txt`, set
`CAP_MODE=mock`, and start FastAPI on `127.0.0.1:8000`. Do not enable any real
provider or lifecycle flag.

- [ ] **Step 3: Run only the bounded validation path**

Verify `/health`, `/cap/status`, deterministic risk decisions, mock A2A, and
local order/proof retrieval. Required posture remains:

```text
CAP_MODE=mock
real_cap_ready=false
live_execution_authorized=false
mutating_methods_called=false
```

- [ ] **Step 4: Stop the local process and record results**

Record commands, exit/results, failures, and deviations without cookies,
tokens, credentials, or full environment dumps. A failure keeps status
`pending`; do not edit runtime code under this plan.

- [ ] **Step 5: Reconcile docs and commit the evidence**

Change README/runbook only when the observed safe setup disproves their current
instructions. Mark checklist `pass` only when a clean run completes.

### Task 4: Perform a Redacted Repository and History Secrets Review

**Files:**
- Create: `docs/evidence/step9d-secrets-review.md`
- Modify: `docs/compliance-evidence-checklist.md`

**Interfaces:**
- Consumes: explicit approval for a repository/history scan and a tool configured to redact values.
- Produces: a non-sensitive scan summary and release gate decision.

- [ ] **Step 1: Define scan scope without opening secret-bearing files**

Cover tracked content and reachable Git history. Exclude generated worktrees,
virtual environments, caches, and dependency directories. Do not print file
contents or matched values.

- [ ] **Step 2: Run a redacted scanner under separate approval**

Configure output to include only scanner/tool version, rule identifier, file
path, commit identifier when applicable, and finding count. Redirect detailed
secret-bearing output away from logs and documentation.

- [ ] **Step 3: Apply the stop condition**

If any credible finding exists, keep checklist status `pending`, block public
visibility/publication, and hand remediation to the owner/security reviewer.
Do not paste the value into issues, chat, commits, or the evidence file.

- [ ] **Step 4: Record the safe result**

Mark `pass` only after the reviewer confirms no unresolved finding remains.
Record scope, tool/version, date, reviewer, counts, and limitations.

### Task 5: Verify Official DoraHacks Requirements

**Files:**
- Modify: `docs/compliance-evidence-checklist.md`
- Modify: `docs/dorahacks-submission-draft.md`

**Interfaces:**
- Consumes: official DoraHacks program, rules, and submission-form sources.
- Produces: dated authoritative evidence for program URL, cutoff/timezone, fields, rubric, and tracks.

- [ ] **Step 1: Locate the official program surface**

Use only DoraHacks-controlled pages or the official current hackathon page.
The verified LinkedIn event announcement remains event-existence evidence,
not submission-form evidence.

- [ ] **Step 2: Capture each requirement independently**

For the program URL, deadline/timezone, mandatory BUIDL fields, judging rubric,
and selectable tracks, record the exact official URL, access date, concise
evidence note, and limitation. If authenticated fields are inaccessible,
request an owner-provided capture from the live form.

- [ ] **Step 3: Preserve unknowns**

Do not infer a cutoff from the June 9–July 11 event range. Do not present the
current proposed judging map or recommended tracks as official. Keep each
unverified row `unknown` independently.

- [ ] **Step 4: Reconcile the submission draft**

Replace only claims supported by the captured source. Retain explicit
placeholders for unavailable links and keep draft copy distinct from a
submitted BUIDL.

- [ ] **Step 5: Run a source and claim review**

```powershell
git diff --check
rg -n "unknown|not verified|VERIFY_|deadline|timezone|rubric|track|mandatory" docs/compliance-evidence-checklist.md docs/dorahacks-submission-draft.md
```

Expected: every external claim has a source/date or remains explicitly
unverified.

### Task 6: Verify Exact CROO Store Listing Requirements

**Files:**
- Modify: `docs/compliance-evidence-checklist.md`
- Modify: `docs/croo-store-listing-draft.md`

**Interfaces:**
- Consumes: official CROO registration form or official listing documentation.
- Produces: a source-backed mapping from required Store fields to Aegis draft copy.

- [ ] **Step 1: Inspect the official registration surface read-only**

Capture required/optional fields, character limits, categories/taxonomy,
schema expectations, pricing/SLA fields, publication rules, refund language,
and required links. If authentication is required, ask the Store operator for
a dated capture; do not register or submit during verification.

- [ ] **Step 2: Build the field mapping in the Store draft**

For every verified field, map the official label and limit to the existing
Aegis copy. Keep provisional price and service-window qualifiers. Do not add
payment, escrow, delivery, settlement, production SLA, or accepting-orders
claims.

- [ ] **Step 3: Preserve unresolved requirements**

Keep checklist status `unknown` if the complete official form cannot be
captured. Store existence and a Register Agent link are insufficient evidence.

- [ ] **Step 4: Validate and commit**

Run `git diff --check`, review only the two documentation files, and confirm
every new requirement has an official URL and access date.

### Task 7: Prepare, Record, and Verify the Video Walkthrough

**Files:**
- Create: `docs/evidence/step9d-video-walkthrough-review.md`
- Modify after public verification: `docs/compliance-evidence-checklist.md`
- Modify after public verification: `docs/dorahacks-submission-draft.md`

**Interfaces:**
- Consumes: Step 8-C under-five-minute sequence, final mock-mode release commit, and owner-approved publishing channel.
- Produces: reviewed script evidence and an anonymously playable public URL.

- [ ] **Step 1: Freeze the script against the release commit**

Use the Step 8-C 0:00–5:00 sequence. Require spoken and visible statements
that Aegis checks risk before execution, does not execute, and is in mock mode.

- [ ] **Step 2: Record locally under separate app-start approval**

Show `/health`, `/cap/status`, EXECUTE/WAIT/BLOCK, proof hashes, mock A2A, and
local order/proof retrieval. Keep all `_MOCK` labels visible. Do not call a
live provider or display secrets.

- [ ] **Step 3: Perform the claim-safety review before publication**

Reject the recording if it claims or implies real payment, escrow, delivery,
settlement, accepting orders, commercial readiness, guaranteed safety,
profit, wallet custody, signing, swaps, transactions, broadcast, or live
trading.

- [ ] **Step 4: Publish and test anonymously**

The owner/presentation lead publishes through an approved channel. Verify
anonymous playback, title/description accuracy, duration, and final URL before
replacing `[VERIFY_VIDEO_URL]` or marking checklist `pass`.

### Task 8: Publish and Verify the Aegis Store Listing

**Files:**
- Modify after publication: `docs/compliance-evidence-checklist.md`
- Modify after publication: `docs/croo-store-listing-draft.md`
- Modify after publication: `docs/dorahacks-submission-draft.md`

**Interfaces:**
- Consumes: verified listing requirements, owner-approved license, passed secrets gate, final reviewed listing copy, and Store operator authorization.
- Produces: an anonymously accessible official Aegis Store URL or an honest retained `missing` status.

- [ ] **Step 1: Check publication prerequisites**

Require completed requirement mapping, approved license, reviewed public
repository posture, passed secrets review, and owner-approved final copy.

- [ ] **Step 2: Require explicit external-write authorization**

The Store operator must explicitly authorize submitting the listing. If not,
keep `missing`; do not treat the local draft as publication evidence.

- [ ] **Step 3: Publish through the official Store surface**

Submit only the reviewed fields. Do not claim accepting-orders status or real
commercial operation unless those states are separately verified.

- [ ] **Step 4: Verify the public result**

Open the final URL anonymously. Record service identity, visible copy, URL,
access date, and any moderation/pending state. Mark `pass` only when the Aegis
listing is publicly visible; otherwise use `pending` or `missing` accurately.

### Task 9: Retain the Real CAP Lifecycle Gate Unless Separately Authorized

**Files:**
- Modify only to record current status: `docs/compliance-evidence-checklist.md`
- Review for consistency: `README.md`
- Review for consistency: `docs/croo-store-listing-draft.md`
- Review for consistency: `docs/dorahacks-submission-draft.md`

**Interfaces:**
- Consumes: current mock/gated posture and any future separate owner authorization.
- Produces: an honest pending status and absence of unsupported lifecycle claims.

- [ ] **Step 1: Confirm the default disposition**

Keep real CAP lifecycle evidence `pending` and keep:

```text
CAP_MODE=mock
real_cap_ready=false
live_execution_authorized=false
mutating_methods_called=false
```

- [ ] **Step 2: Do not initiate real verification from this plan**

No provider listener, live API call, negotiation, paid order, payment, escrow,
delivery, settlement, or reputation update is authorized.

- [ ] **Step 3: Require a separate operational plan if the owner later asks**

That plan must define necessity, credentials handling, spending ceiling,
counterparty, environment, read/write gates, stop conditions, rollback,
evidence retention, and explicit approvals. Its existence alone would not
prove a completed lifecycle.

- [ ] **Step 4: Run the final claim-safety scan**

```powershell
rg -ni -C 2 "guaranteed safety|profit generator|live trading bot|execution bot|wallet manager|private-key agent|real payment|real escrow|real delivery|real settlement|commercial readiness" README.md docs/compliance-evidence-checklist.md docs/croo-store-listing-draft.md docs/dorahacks-submission-draft.md
```

Expected: matches occur only in explicit negative, prohibited-claim, or
pending-verification contexts.

---

## Cross-Gate Release Decision

Before submission or marketplace publication, conduct one final evidence
review:

- [ ] Owner-approved license is present and consistently named.
- [ ] Canonical repository URL works anonymously at the release commit.
- [ ] Setup reproducibility has a clean, redacted transcript.
- [ ] Secrets review has no unresolved finding and contains no secret values.
- [ ] Official DoraHacks program URL, deadline/timezone, fields, rubric, and
      tracks are sourced or remain explicitly `unknown`.
- [ ] Exact CROO listing requirements are sourced or publication remains
      blocked.
- [ ] Public video URL works anonymously and passes claim-safety review.
- [ ] Published Store status matches the actual public state.
- [ ] Real CAP lifecycle remains unclaimed unless separately verified.
- [ ] `git diff --check` passes and changed files are documentation/evidence
      artifacts plus an owner-approved root `LICENSE`, if applicable.

The submission can proceed with real CAP lifecycle evidence still `pending` if
the official rules do not require it and all copy remains explicit about the
mock/gated state. The submission must not proceed with invented evidence,
ambiguous licensing, exposed secrets, or claims that a draft link is public.

## Plan Completion Criteria

This plan is complete when each blocker has either:

1. direct evidence and a justified `pass` status; or
2. an honest `missing`, `pending`, or `unknown` status with a named owner,
   exact next action, and release impact.

Completion does not require a real CAP lifecycle. It does require that no one
claims real CAP payment, escrow, delivery, settlement, or commercial readiness
without authoritative verification.
