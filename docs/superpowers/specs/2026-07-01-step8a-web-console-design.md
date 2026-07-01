# Step 8-A Aegis Web Console Design

## Goal

Build a reusable, product-grade Web Console at `/` for real users, agent
builders, CROO Agent Store reviewers, and the demo video. The console uses the
existing local FastAPI endpoints and preserves every API contract and CAP
safety boundary.

## Architecture

FastAPI serves `apps/web/index.html` at `/` and mounts `apps/web/static` at
`/static`. The HTML defines semantic product sections, `styles.css` owns the
responsive visual system, and `app.js` owns safe same-origin API calls and UI
rendering. No frontend framework, template engine, external script, analytics,
or new runtime dependency is introduced.

Existing API routes remain unchanged:

- `GET /health`
- `POST /risk-check`
- `POST /a2a/mock-order`
- `POST /orders`
- `GET /orders/{order_id}`
- `GET /proof/{proof_id}`
- `GET /cap/status`

## Product Surface

The page is a dark, precise operations console with cool off-white typography,
sparing neon-green verified accents, amber caution states, and red BLOCK states. It
uses restrained borders, generous spacing, monospace data surfaces, and a
responsive two-column grid that collapses cleanly on narrow screens.

Sections:

1. Hero and positioning: Aegis is a pre-trade risk oracle that returns BLOCK,
   WAIT, or EXECUTE with proof and never executes.
2. Live posture: fetch `/health` and `/cap/status`; show CAP mode, readiness,
   and immutable execution/mutation flags with explicit safe defaults.
3. Risk Check: editable valid JSON, submit to `/risk-check`, and render the
   actual decision, score, confidence, regime, reasons, factors, action, and
   proof fields.
4. A2A mock flow: submit the same risk request inside a mock requester envelope
   to `/a2a/mock-order`; explain REFUSED, DELAYED, and simulated-only execution.
5. Local order/proof: create a local mock order, retain returned IDs in memory,
   and fetch the stored order or proof with visible local-only disclaimers.
6. CROO readiness: price, target tracks, honest current status, and the next
   separately approved one-event manual-review observation boundary.
7. Developer integration: copyable curl examples and compact response-shape
   documentation for all supported endpoints.

## Data and Error Flow

JavaScript uses relative URLs and `fetch` only. Requests are parsed from the
textarea before submission. The UI never uses `innerHTML` for response data;
all untrusted values are rendered through text nodes. Errors show a bounded,
readable message derived from HTTP status and structured API detail without
displaying request headers, environment variables, credentials, or stack
traces. Controls expose loading and disabled states.

The live posture panel treats missing optional status fields as "not reported"
and never infers readiness. `real_cap_ready`, `live_execution_authorized`, and
`mutating_methods_called` remain false in product copy and status rendering.

## Safety and Claim Boundary

The console does not add wallet connection, key handling, signing, swap,
transaction construction, broadcast, trading, a provider listener, a probe, or
any real CROO/CAP action. It does not call `/cap/order` or the manual real pilot
runner. All interactive order flows are explicitly local/mock.

Required honest claim:

> CAP-ready gated runtime; real payment, delivery, settlement, and commercial
> readiness are not claimed yet.

`EXECUTE` is presented as a risk decision for simulated/local flow only, never
as transaction authorization.

## Testing

Focused FastAPI tests verify `/` serves HTML, static assets are available,
required product/safety claims and endpoint references are present, and no
forbidden capability language or external tracking scripts appear. Existing
route tests plus the full suite verify API behavior remains unchanged. Static
scans cover forbidden runtime capabilities, real CAP mutations, generic
lifecycle calls, provider-example references, auto-start paths, and secret
access.
