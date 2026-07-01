---
name: "Aegis Risk Oracle"
version: "1.0.0"
description: "Security-first design contract for the Aegis pre-trade risk oracle and agent-to-agent risk guard."
colors:
  primary: "#57E6A5"
  on-primary: "#07100C"
  primary-container: "#17392D"
  primary-strong: "#9AF4C9"
  secondary: "#A9B8C2"
  tertiary: "#F2B84B"
  neutral: "#070A0D"
  surface: "#0C1218"
  surface-raised: "#111A22"
  surface-inset: "#0A0F14"
  surface-interactive: "#15212B"
  on-surface: "#F2F7F5"
  on-surface-secondary: "#A9B8C2"
  on-surface-muted: "#73838E"
  outline: "#293A47"
  outline-subtle: "#1B2833"
  outline-strong: "#3A5262"
  error: "#FF5D6C"
  error-container: "#3A171D"
  warning: "#F2B84B"
  warning-container: "#372A13"
  safe: "#57E6A5"
  safe-container: "#17392D"
  status-neutral: "#8FA4B2"
  status-neutral-container: "#17222A"
typography:
  headline-display:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "5.5rem"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.035em"
  headline-lg:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "3.25rem"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  headline-md:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.625rem"
    fontWeight: 600
    lineHeight: 1.18
    letterSpacing: "-0.015em"
  body-lg:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.6
  body-md:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.6
  body-sm:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.55
  label-lg:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.2
  label-sm:
    fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.08em"
  code-md:
    fontFamily: "IBM Plex Mono, SFMono-Regular, Consolas, monospace"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.55
  code-sm:
    fontFamily: "IBM Plex Mono, SFMono-Regular, Consolas, monospace"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.5
spacing:
  0: "0px"
  1: "0.25rem"
  2: "0.5rem"
  3: "0.75rem"
  4: "1rem"
  5: "1.25rem"
  6: "1.5rem"
  8: "2rem"
  10: "2.5rem"
  12: "3rem"
  16: "4rem"
  20: "5rem"
  24: "6rem"
rounded:
  none: "0px"
  sm: "0.375rem"
  md: "0.625rem"
  lg: "0.875rem"
  xl: "1.25rem"
  full: "999px"
radius:
  none: "0px"
  sm: "0.375rem"
  md: "0.625rem"
  lg: "0.875rem"
  xl: "1.25rem"
  full: "999px"
shadows:
  none: "none"
  inset: "inset 0 1px 0 rgba(255, 255, 255, 0.035)"
  low: "0 8px 24px rgba(0, 0, 0, 0.22)"
  medium: "0 18px 48px rgba(0, 0, 0, 0.32)"
  focus: "0 0 0 3px rgba(87, 230, 165, 0.28)"
elevation:
  base: 0
  raised: 1
  sticky: 10
  dialog: 30
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.md}"
    padding: "{spacing.3}"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.primary-strong}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.md}"
    padding: "{spacing.3}"
    height: "44px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.md}"
    padding: "{spacing.3}"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.surface-interactive}"
    textColor: "{colors.on-surface}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.md}"
    padding: "{spacing.3}"
    height: "44px"
  status-badge:
    backgroundColor: "{colors.status-neutral-container}"
    textColor: "{colors.status-neutral}"
    typography: "{typography.code-sm}"
    rounded: "{rounded.full}"
    padding: "{spacing.2}"
  status-badge-verified:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.primary-strong}"
    typography: "{typography.code-sm}"
    rounded: "{rounded.full}"
    padding: "{spacing.2}"
  risk-card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"
    padding: "{spacing.6}"
  proof-panel:
    backgroundColor: "{colors.surface-inset}"
    textColor: "{colors.on-surface}"
    typography: "{typography.code-md}"
    rounded: "{rounded.md}"
    padding: "{spacing.5}"
  code-block:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.on-surface-secondary}"
    typography: "{typography.code-md}"
    rounded: "{rounded.md}"
    padding: "{spacing.5}"
  input-textarea:
    backgroundColor: "{colors.surface-inset}"
    textColor: "{colors.on-surface}"
    typography: "{typography.code-md}"
    rounded: "{rounded.md}"
    padding: "{spacing.5}"
    height: "18rem"
  decision-badge:
    backgroundColor: "{colors.status-neutral-container}"
    textColor: "{colors.on-surface-secondary}"
    typography: "{typography.code-sm}"
    rounded: "{rounded.sm}"
    padding: "{spacing.2}"
  decision-badge-block:
    backgroundColor: "{colors.error-container}"
    textColor: "{colors.error}"
    typography: "{typography.code-sm}"
    rounded: "{rounded.sm}"
    padding: "{spacing.2}"
  decision-badge-wait:
    backgroundColor: "{colors.warning-container}"
    textColor: "{colors.warning}"
    typography: "{typography.code-sm}"
    rounded: "{rounded.sm}"
    padding: "{spacing.2}"
  decision-badge-execute:
    backgroundColor: "{colors.safe-container}"
    textColor: "{colors.safe}"
    typography: "{typography.code-sm}"
    rounded: "{rounded.sm}"
    padding: "{spacing.2}"
  status-grid:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.on-surface-secondary}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.lg}"
    padding: "{spacing.4}"
  console-panel:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.xl}"
    padding: "{spacing.6}"
---

# Aegis Design Contract

## 1. Overview

Aegis is a pre-trade risk oracle, risk-check API, DeFAI safety agent, and
agent-to-agent risk guard. It is a paid callable service candidate for CROO
Agent Commerce. The product evaluates a proposed action before any separately
controlled execution and returns an evidence-backed risk decision.

Aegis is not a trading bot, swap bot, execution bot, wallet manager, signal
seller, profit generator, or private-key agent. Every interface must preserve
that boundary in structure, interaction, and copy.

The canonical product claims are:

> “Other agents can hire Aegis before they execute.”

> “Aegis returns BLOCK, WAIT, or EXECUTE with proof.”

> “CAP-ready gated runtime; real payment, delivery, settlement, and commercial readiness are not claimed yet.”

> “No wallet, signing, swap, transaction, or broadcast path.”

## 2. Brand Feel

Aegis should feel trustworthy, technical, security-first, and premium without
being flashy. The visual character is serious DeFi infrastructure: deliberate,
quiet, legible, and inspectable. Builders should feel that the system exposes
its reasoning. CROO reviewers should immediately understand what is real,
local/mock, gated, unavailable, or unverified.

The product should resemble a mature security operations console more than a
consumer trading terminal. Confidence comes from clear boundaries, stable
layout, honest status language, deterministic proof fields, and disciplined
color—not from spectacle.

## 3. Visual Principles

1. **Evidence before decoration.** Risk decisions, reasons, factors, hashes,
   policy version, and system posture receive visual priority.
2. **Quiet by default.** Use dark neutral surfaces, restrained borders, and
   generous spacing. Neon green is an accent, never an ambient glow theme.
3. **State is explicit.** Never communicate BLOCK, WAIT, or EXECUTE through
   color alone. Pair color with a label and, where useful, a concise icon.
4. **Honesty is visible.** Local/mock and gated states must be present near the
   affected control or result, not hidden in a footer.
5. **Actions are bounded.** Primary buttons submit risk checks or local/mock
   workflows only. No control may resemble wallet connection or trade execution.
6. **Data remains readable.** Dense evidence uses consistent rows, alignment,
   and monospace values rather than decorative dashboards or fake charts.

## 4. Color Usage

The base is near-black with cool slate surfaces. Text contrast must remain high
without using pure white across large areas.

- Neon green is reserved for verified state, safe posture, CROO-ready gated
  cues, and the EXECUTE risk decision. It does not mean a trade was executed.
- Red is reserved for BLOCK, danger, or a failed safety prerequisite.
- Amber is reserved for WAIT, manual review, incomplete information, or gated
  caution.
- Neutral slate communicates unavailable, not reported, local/mock, or idle.
- Do not use semantic colors as large decorative backgrounds. Prefer a narrow
  rail, badge, border, or compact status treatment.
- Never use green to imply profit, price appreciation, payment success, or
  commercial readiness.

## 5. Typography Rules

Use the display/body family for narrative product copy, headings, labels, and
controls. Use the monospace family for JSON, code examples, request and response
payloads, proof IDs, order IDs, hashes, policy versions, status values, and
machine-readable evidence.

The following fields must always render in monospace when visible:

- `request_hash`
- `response_hash`
- `proof_hash`
- `result_hash`
- `proof_id`
- `order_id`
- `policy_version`

Headings should be compact and confident. Body copy should use comfortable line
lengths of approximately 55–75 characters. Utility labels may use uppercase
only when short, and must not mimic speculative trading-terminal jargon.

## 6. Layout Rules

- Use a maximum content width near `1440px` with responsive page gutters.
- Favor open vertical sections and a small number of strong console panels over
  nested cards or a default bento grid.
- Keep the first viewport focused on positioning, safety posture, and the main
  risk-check action. Do not fill it with fake metrics.
- Use a two-column workbench only when input and output benefit from direct
  comparison. Collapse to one column below tablet widths.
- Keep status information in a scannable grid with consistent label/value
  alignment.
- Make JSON editors, response evidence, and code examples horizontally safe:
  wrap descriptive text, but allow code surfaces to scroll without breaking the
  page.
- Preserve at least `44px` interactive target height on touch devices.
- Avoid modal-first flows. Critical safety context should remain visible in the
  page where the action occurs.

## 7. Component Guidance

### Buttons

`button-primary` is for running a risk check or an explicitly labeled
local/mock request. `button-secondary` is for refresh, copy, fetch, reset, or
navigation. Button labels must describe the bounded action: “Run risk check” is
valid; “Execute trade” is forbidden.

### Status and decision badges

`status-badge` communicates system posture such as healthy, mock, gated, or not
reported. `decision-badge` is reserved for BLOCK, WAIT, and EXECUTE. Do not use
decision colors for unrelated statuses.

### Risk and console panels

`risk-card` highlights the decision first, followed by score, confidence,
regime, reasons, risk factors, suggested action, and proof. `console-panel`
frames a complete workflow, not every small content group.

### Proof, code, and input surfaces

`proof-panel` uses stable rows with copyable values. `code-block` presents curl
and response examples. `input-textarea` is a real editable JSON surface with a
visible label, validation feedback, and strong focus state.

### Status grids

`status-grid` shows real endpoint posture without inferring missing values.
Boolean safety invariants should render as explicit true/false values plus
human-readable meaning.

## 8. Risk Decision Display Rules

Risk decisions must be identifiable within one glance:

- **BLOCK:** red label and rail; action language states that simulated or
  downstream execution should be refused.
- **WAIT:** amber label and rail; action language states that execution should
  pause pending data or manual review.
- **EXECUTE:** green label and rail; language states that the risk decision is
  favorable, while reiterating that Aegis does not execute or authorize a
  transaction.

Always show the text label, risk score, `safe_to_execute`, confidence, and
suggested action together. Never animate EXECUTE like a win state. Never use
confetti, profit language, directional price arrows, or celebratory motion.

## 9. Proof and Hash Display Rules

Proof fields should look credible, deterministic, and operationally useful.

- Render proof fields in monospace with preserved character accuracy.
- Provide an explicit copy control when a full value is available.
- A visually truncated hash must expose the full value through copy and an
  accessible label; never alter the underlying value.
- Group `request_hash`, `response_hash`, `result_hash` or `proof_hash`, and
  `policy_version` in a consistent order.
- Distinguish local delivery proof/log attestation from on-chain proof.
- Never imply that a hash proves payment, escrow, settlement, delivery, or
  commercial readiness.
- Never display raw credentials, authorization values, secret-bearing URLs, or
  unsanitized exceptions near evidence.

## 10. Accessibility Rules

- Meet WCAG 2.2 AA contrast for text and interactive states.
- Never rely on color alone; every status includes text.
- Provide visible keyboard focus using the verified-green focus token.
- Use semantic headings, landmarks, labels, buttons, and live regions.
- Associate validation and error text with the relevant input.
- Use `aria-live="polite"` for completed request status and `role="alert"` for
  actionable errors.
- Respect `prefers-reduced-motion`; no essential information may depend on
  animation.
- Keep touch targets at least `44px` and preserve logical tab order.
- Code and hash surfaces must support zoom, wrapping or controlled scrolling,
  selection, and copy without obscuring adjacent content.

## 11. Forbidden Design Directions

Do not introduce:

- casino, gambling, meme, moonshot, trading-profit, or speculative visuals;
- candlestick charts, token-price charts, portfolio P&L, buy/sell controls, or
  directional trade signals;
- wallet connection, account balance, private-key, seed phrase, signing, swap,
  transaction, broadcast, or live-trading controls;
- guaranteed-safety, guaranteed-profit, payment-verified, escrow-verified,
  delivery-verified, settlement-verified, or commercially-ready claims;
- fake metrics, fake marketplace activity, fake agent demand, or fake revenue;
- excessive neon, rainbow gradients, glassmorphism, glowing orbs, cyberpunk
  grids, humanoid AI art, generic robot imagery, or other AI-slop motifs;
- external tracking scripts or design elements that conceal local/mock status;
- controls that call or imply real CAP mutation methods.

## 12. How Coding Agents Should Use This File

1. Read `DESIGN.md` before proposing, generating, or modifying Aegis UI.
2. Treat YAML values as canonical tokens. Reuse them through CSS custom
   properties or the project’s token mechanism instead of inventing one-off
   colors, spacing, radii, or shadows.
3. Treat the Markdown rules and product claims as a design and safety contract,
   not optional guidance.
4. Map every new component to an existing component token. If no token fits,
   document the need before adding one.
5. Preserve semantic decision colors and never reuse them decoratively.
6. Keep all API response data code-native and render untrusted values as text.
7. Verify desktop and mobile layouts, keyboard focus, contrast, reduced motion,
   copy accuracy, and honest local/mock/gated language.
8. Run `git diff --check` and `designmd lint DESIGN.md` when the CLI is usable.
9. Reject any UI request that conflicts with the forbidden directions or Aegis
   safety positioning unless the governing product specification is explicitly
   revised and separately approved.
10. Do not interpret this file as authorization for a real CAP/CROO listener,
    probe, API call, negotiation, paid order, payment, delivery, or settlement.
