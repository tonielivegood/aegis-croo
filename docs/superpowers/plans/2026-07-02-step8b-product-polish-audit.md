# Step 8-B Product Polish Audit and Step 8-B-B Patch Plan

> **For agentic workers:** Use the executing-plans workflow to implement the
> Step 8-B-B patch plan task by task. Use test-driven development for every
> behavior or contract change.

**Goal:** Improve how quickly builders, CROO Store reviewers, and demo viewers
understand, trust, and integrate Aegis without changing any API behavior or
weakening its safety boundaries.

**Architecture:** Retain the FastAPI-served static HTML, CSS, and vanilla
JavaScript architecture. Step 8-B-B should refine content hierarchy, add
client-side demo presets that call the existing local endpoints, and improve
the presentation of evidence already returned by those endpoints.

**Tech Stack:** FastAPI, semantic HTML, DESIGN.md CSS tokens, vanilla
JavaScript, pytest/TestClient, and Playwright browser QA.

## Global Constraints

- DESIGN.md remains the canonical visual and product-safety contract.
- Keep every existing API route and response behavior unchanged.
- Keep CAP_MODE=mock by default.
- Keep real_cap_ready=false.
- Keep live_execution_authorized=false.
- Keep mutating_methods_called=false.
- Do not add a frontend framework or external browser dependency.
- Do not add wallet, signing, swap, transaction, broadcast, or trading logic.
- Do not add or imply real CAP payment, escrow, delivery, settlement, or
  commercial readiness.
- Do not start a live provider listener, probe, pilot, negotiation, or order.

---

## 1. Current Product Status

Step 8-A established a credible product surface rather than a hackathon
placeholder:

- GET / serves a responsive Aegis Web Console.
- The console exposes live local posture, editable risk checks, mock A2A
  requests, local order/proof helpers, CROO readiness context, and developer
  examples.
- The page follows the dark security-console design system in DESIGN.md.
- Browser interactions use only existing same-origin relative API routes.
- Proof fields are rendered as text with copy controls.
- Existing API route modules and behaviors remain unchanged.
- The merged baseline was verified with 7 focused console tests, 46 console
  plus API regression tests, and 282 full-suite tests with one existing
  warning.
- The safety scan returned zero forbidden executable capabilities.

The product is technically sound and honest. Step 8-B-B should increase
comprehension, demonstration quality, and marketplace conversion without
inventing new capability.

## 2. What Already Works Well

### Technical Execution — 30%

- FastAPI serves a dependency-light static application with no framework
  build step.
- The risk form calls the real local oracle rather than showing canned output.
- Loading, validation, bounded errors, safe text rendering, and copy helpers
  are implemented.
- The layout is responsive, accessible, and aligned with DESIGN.md tokens.
- Existing health, risk, A2A, order, proof, and CAP status routes remain
  available.

### A2A Composability — 25%

- The console exercises POST /a2a/mock-order using the editable risk request.
- The UI shows the relationship between Aegis decisions and the mock
  requester's next state.
- Developer examples expose the existing agent-facing endpoints.
- The positioning clearly says that another agent can call Aegis before acting.

### Innovation — 20%

- Aegis is positioned as a pre-trade risk oracle and A2A safety guard rather
  than another execution or signal bot.
- BLOCK, WAIT, and EXECUTE form a simple machine-readable decision contract.
- Hash-linked proof and policy-version fields make the safety decision
  inspectable and operationally credible.

### Usability and Real Adoption — 15%

- Users can edit JSON, submit a risk check, inspect factors and reasons, copy
  proof values, and exercise local integration contracts.
- Safety status is visible rather than buried in legal copy.
- The console is usable on desktop and narrow mobile layouts.

### Presentation — 10%

- The product has a cohesive security-console visual system.
- Decision colors are disciplined and accompanied by text labels.
- Honest local/mock and readiness boundaries are prominent.
- The page contains useful material for a demo video and CROO Store review.

## 3. Weaknesses That Could Hurt Top 1

1. The first viewport states what Aegis is but does not show the complete
   input-to-decision-to-proof loop quickly enough. A judge must scroll and
   infer why an agent would pay for the service.
2. The Risk Check Console has one editable sample. BLOCK, WAIT, and EXECUTE
   appear in the hero, but there is no guided way to produce and compare those
   outcomes during a short demo.
3. The A2A section emphasizes mock execution status more than the reusable
   composition contract: who calls Aegis, what they send, what they receive,
   and how the caller should branch.
4. Proof fields are credible but visually dense. Full hashes compete with each
   other, copy feedback is subtle, and provenance is explained only briefly.
5. The CROO readiness section mixes current evidence, target positioning, and
   a future observation in one block. Reviewers cannot scan a clear
   ready/gated/not-claimed capability matrix.
6. Developer curl examples reference external JSON files that are not shown.
   They are not immediately copy-pasteable, and the agent integration sequence
   is not demonstrated end to end.
7. The page is comprehensive but long. It lacks a deliberate judge/demo path
   that connects value proposition, one decision, proof, A2A composition, and
   honest marketplace status in under two minutes.

## 4. Prioritized Improvement List

The list is intentionally capped at seven items.

| Priority | Improvement | Judging category impacted | Expected Top 1 value | Implementation risk | Changes API behavior | Fake CAP/commercial claim risk |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Add deterministic BLOCK, WAIT, and EXECUTE scenario presets beside the editable request, with clear input differences and one-click use of POST /risk-check. | Technical Execution, Innovation, Usability, Presentation | Very high: makes the core decision system demonstrable in seconds and proves all three branches are meaningful. | Medium: preset payloads must stay valid and deterministic against current policy. | No | Low if every result is labeled as a local risk decision, not execution. |
| 2 | Rewrite the hero and core-workflow copy around the buyer outcome: call Aegis before acting, receive a decision plus reasons and proof, then branch safely. | Usability and Real Adoption, Presentation, Innovation | High: clarifies why another agent would hire Aegis and improves conversion without hype. | Low | No | Low; retain all canonical boundary claims verbatim. |
| 3 | Turn the A2A section into a compact composability contract showing caller, request, Aegis response, and caller branch for BLOCK, WAIT, and EXECUTE. | A2A Composability, Technical Execution | Very high: directly addresses the second-largest judging category and makes integration architecture obvious. | Low | No | Low if the downstream branch remains simulated and caller-controlled. |
| 4 | Improve proof and hash presentation with stable field grouping, readable shortening, full-value copy, stronger copied feedback, and explicit local-attestation provenance. | Technical Execution, Usability and Real Adoption, Presentation | High: makes evidence feel operational rather than decorative and strengthens trust. | Medium: visual shortening must never alter the copied value or imply on-chain proof. | No | Low with explicit local-log and not-on-chain labels. |
| 5 | Replace the readiness block with an honest capability matrix: available now, gated/manual, and not claimed. Keep price and target tracks clearly labeled as pilot positioning. | Usability and Real Adoption, Presentation | High: lets CROO reviewers assess readiness quickly while preserving credibility. | Low | No | Medium: wording must not turn gated or planned capability into verified readiness. |
| 6 | Make developer examples self-contained and show the A2A decision-branch sequence, response fields, and proof retrieval using existing routes. | A2A Composability, Technical Execution, Usability and Real Adoption | High: reduces integration friction and demonstrates real adoption value. | Low | No | Low; examples must remain local/mock and must not include CAP mutation methods. |
| 7 | Tighten page rhythm into a two-minute demo path with stronger section transitions and a visible progression from risk input to proof to A2A use to readiness. | Presentation, Usability and Real Adoption | Medium-high: improves reviewer recall and demo-video pacing without adding features. | Low | No | Low; preserve visible boundary language at every relevant step. |

## 5. Required Step 8-B-B Implementation Scope

Step 8-B-B must:

- Improve Web Console copy and conversion.
- Make BLOCK, WAIT, and EXECUTE demo scenarios clearer.
- Improve proof and hash readability and copyability.
- Improve the CROO Store readiness section.
- Improve developer integration examples.
- Improve the A2A composability explanation.
- Keep all API behavior unchanged.

The implementation should modify only the existing static Web Console and its
focused tests unless a separately reviewed documentation update is necessary.
It must not add a new endpoint, request field, response field, persistence
layer, external dependency, or CAP runtime behavior.

## 6. Cut List

Do not include:

- A new frontend framework.
- Charts unless a later review demonstrates a necessary relationship that
  cannot be communicated more clearly with text or a compact comparison.
- A wallet or connect button.
- Live trading visuals.
- A fake payment, escrow, delivery, settlement, or commercial-readiness claim.
- Overengineered dashboard features.
- Authentication, accounts, analytics, remote assets, external scripts, or
  browser storage.
- New CAP/CROO listener, probe, provider, negotiation, payment, or order logic.

## 7. Recommended Step 8-B-B Patch Plan

### Task 1: Lock the Product and Safety Copy Contract

**Files:**

- Modify tests/test_web_console.py
- Modify apps/web/index.html

**Plan:**

1. Add failing assertions for the revised buyer-oriented value proposition,
   three scenario labels, A2A composition steps, proof provenance, readiness
   states, and self-contained integration examples.
2. Retain the existing canonical claims and forbidden-claim assertions.
3. Update only semantic HTML and copy until the content tests pass.
4. Confirm no existing endpoint reference is removed or renamed.

### Task 2: Add Three Client-Side Risk Scenario Presets

**Files:**

- Modify tests/test_web_console.py
- Modify apps/web/index.html
- Modify apps/web/app.js

**Plan:**

1. Add static tests requiring BLOCK, WAIT, and EXECUTE preset controls and
   forbidding new endpoint strings.
2. Define three immutable local JSON payloads that are valid under the current
   RiskCheckRequest schema and deterministically exercise the existing policy.
3. Make preset controls populate the existing editable textarea; submission
   must continue through POST /risk-check.
4. Display the selected scenario as an input explanation, never as a promised
   result.
5. Verify each preset through the existing local API in focused tests or
   browser QA without changing oracle policy.

### Task 3: Clarify Decision and A2A Composition

**Files:**

- Modify tests/test_web_console.py
- Modify apps/web/index.html
- Modify apps/web/app.js
- Modify apps/web/styles.css

**Plan:**

1. Present the flow as Caller Agent → Aegis Risk Check → Decision and Proof →
   Caller-Controlled Branch.
2. Keep BLOCK mapped to refuse, WAIT to pause/review, and EXECUTE to favorable
   risk posture without transaction authorization.
3. Reuse the currently selected risk request for POST /a2a/mock-order.
4. Improve result labels so simulated status cannot be confused with live
   execution.
5. Add no lifecycle mutation control or CAP endpoint.

### Task 4: Make Proof Operationally Readable

**Files:**

- Modify tests/test_web_console.py
- Modify apps/web/index.html
- Modify apps/web/app.js
- Modify apps/web/styles.css

**Plan:**

1. Group request_hash, response_hash, result_hash or proof_hash, proof_id, and
   policy_version in a stable order.
2. Render a readable visual form while preserving the exact full value in
   memory and in the copy action.
3. Add accessible copied and copy-failed feedback.
4. Keep the explicit local-log-attestation and not-on-chain-proof language.
5. Ensure mobile layouts do not clip hashes or copy controls.

### Task 5: Reframe CROO Readiness Honestly

**Files:**

- Modify tests/test_web_console.py
- Modify apps/web/index.html
- Modify apps/web/styles.css

**Plan:**

1. Add a three-state matrix: available now, gated/manual, and not claimed.
2. Place CAP_MODE=mock, real_cap_ready=false,
   live_execution_authorized=false, and mutating_methods_called=false in the
   relevant state.
3. Keep 0.12 USDC labeled as pilot price positioning, not verified payment.
4. Keep the target tracks visible: Data and Verification Agents and DeFi /
   On-chain Ops Agents.
5. Repeat that real payment, delivery, settlement, and commercial readiness
   are not claimed.

### Task 6: Make Integration Examples Copy-Pasteable

**Files:**

- Modify tests/test_web_console.py
- Modify apps/web/index.html
- Modify apps/web/styles.css

**Plan:**

1. Replace references to unseen JSON files with complete inline local request
   examples.
2. Show the minimal risk-check call first.
3. Show the A2A wrapper request and decision-branch pseudocode second.
4. Show local order and proof retrieval only after the core agent integration.
5. Keep examples limited to existing relative or loopback routes and exclude
   credentials, CAP mutation calls, wallets, and trading actions.

### Task 7: Verify Product Quality and Safety

**Files:**

- Modify tests/test_web_console.py only if a discovered regression requires a
  test-first correction.

**Plan:**

1. Run the focused Web Console tests.
2. Run the console plus existing API regression set.
3. Run the full pytest suite.
4. Run git diff --check and designmd lint DESIGN.md.
5. Run the forbidden product-claim and executable-capability scans.
6. Use browser QA for the two-minute demo path at desktop and 390px mobile
   widths.
7. Exercise all three risk presets, A2A composition, proof copying, and the
   readiness matrix.
8. Confirm no API route module or behavior changed before committing.

## 8. Step 8-B-B Acceptance Criteria

- A first-time reviewer can explain Aegis, its buyer, its output, and its
  safety boundary from the first viewport.
- BLOCK, WAIT, and EXECUTE can each be demonstrated through the existing
  risk-check endpoint without editing JSON manually.
- The A2A caller contract and downstream branching are explicit.
- Proof fields remain exact, copyable, accessible, and honestly described.
- CROO readiness is scannable without implying real commerce.
- Developer examples are self-contained and use only existing routes.
- Desktop and mobile browser QA pass without console errors or overflow.
- Focused, regression, and full tests pass.
- All forbidden capability and product-claim scan categories remain zero.
- Git shows no runtime change outside the approved Step 8-B-B Web Console
  files.
