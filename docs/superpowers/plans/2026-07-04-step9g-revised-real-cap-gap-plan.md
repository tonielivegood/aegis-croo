# Step 9-G Revised Real-CAP Gap Plan

**Goal:** Move Aegis from an owner-verified but `OFFLINE` CROO state toward verified provider `ONLINE` readiness without changing Aegis Core's non-custodial, non-executing boundary.

**Architecture:** Keep Aegis Core unchanged as the callable risk-check API. First verify whether the repository already contains a suitable official-SDK provider process. If separation is necessary, keep the provider process outside Aegis Core and supply its masked credential only through owner-controlled external secret infrastructure.

**Safe operational deadline:** `2026-07-09 23:59 UTC+8` unless written organizer clarification supersedes it.

## Non-negotiable boundary

Step 9-G-C must not add any of the following to Aegis Core or this repository:

- private keys or SDK/API key values;
- wallet custody;
- local signing;
- transaction construction or broadcast;
- requester payment logic;
- swap, trading, rebalance, or DeFi execution logic; or
- fake real-CAP, Store-discoverability, payment, escrow, delivery, settlement, or commercial-readiness claims.

## Corrected evidence baseline

### PASS_VERIFIED

- registered CROO Agent: `Aegis Risk Oracle`;
- existing CROO Service: `Aegis Risk Check`;
- issued CROO SDK/API key, masked and not recorded;
- configured requirements/input schema;
- configured deliverable schema;
- displayed `0.12 USDC` price and five-minute SLA;
- public repository and Apache-2.0 license;
- reproducible setup and 287 passing tests in the clean-environment verification;
- formal repository and reachable-history secrets review passed;
- callable Aegis risk API;
- local proof ledger and hashes; and
- non-custodial, non-executing Aegis Core.

### PARTIAL

- CAP adapter boundary;
- local `/cap/order` behavior;
- local A2A flow; and
- proof structures that may be usable in a CAP delivery payload.

These are local/mock capabilities, not evidence of an official CAP lifecycle.

### MISSING_OR_UNVERIFIED

- official SDK provider `ONLINE` status;
- WebSocket heartbeat;
- public Store discoverability;
- real negotiation receipt or acceptance;
- real on-chain order creation and payment lock;
- real CAP delivery;
- completion or settlement evidence;
- controlled real order; and
- controlled human spot-check evidence.

## Next technical blocker

The next technical blocker is an official SDK provider runtime reaching a verified `ONLINE` state through the documented provider connection and WebSocket heartbeat path. Starting local Aegis endpoints, importing an SDK, or possessing an SDK/API key does not satisfy this gate.

## Step 9-G-C — official SDK provider ONLINE readiness

Step 9-G-C is verification-first. It must stop before negotiation, order, payment, delivery, settlement, or another mutating CAP method unless the owner separately authorizes a controlled real-order phase.

### Gate 1: verify the official SDK contract

Before implementation, verify from current official documentation and code:

1. the exact intended SDK package and pinned version;
2. the exact provider connection method and event-stream type;
3. the exact heartbeat and Dashboard `OFFLINE` → `ONLINE` transition behavior;
4. the exact required environment-variable names;
5. whether connection alone invokes any mutating CAP method;
6. whether the SDK performs signing, transaction construction, or broadcast during connection; and
7. disconnect, retry, timeout, and failure behavior.

Do not rely on AI memory for method names, configuration, or lifecycle behavior.

### Gate 2: audit existing repository capability

Inspect the repository read-only and determine:

- whether an official SDK provider process already exists;
- whether current code only initializes a client;
- whether existing observe-only tooling is reusable;
- whether current code invokes negotiation, acceptance, payment, delivery, or settlement methods;
- whether a provider can call the existing Aegis risk API without modifying Aegis Core; and
- whether a separate external provider process is necessary.

Prefer reuse over new code. Do not duplicate an existing bounded provider harness.

### Gate 3: choose the smallest boundary-safe process

Choose one verified option:

1. reuse an existing non-mutating official-SDK provider connection harness; or
2. operate a minimal separate provider process outside Aegis Core.

The process may receive the SDK/API key only through external secret infrastructure. It must never log, print, persist, place in a test fixture, or commit the key.

### Gate 4: implement and test ONLINE-only readiness

Repository implementation work is limited to the smallest connection path and tests proving it fails closed before mutating CAP methods. Tests must demonstrate that provider connection and heartbeat do not invoke negotiation acceptance, order creation, payment, delivery, completion, or settlement.

### Gate 5: bounded owner-approved validation

After review and separate owner approval, validate only:

- official SDK initialization;
- authenticated provider connection;
- WebSocket heartbeat;
- Dashboard `ONLINE` status; and
- public Store discoverability, if CROO exposes it after heartbeat.

Record non-secret evidence with `mutating_methods_called=false`, `live_execution_authorized=false`, and `real_cap_ready=false`. Stop after ONLINE readiness.

## Responsibility split

### Repository implementation work

- verify and reuse existing provider/observe-only code where possible;
- add only the smallest connection harness if none exists;
- preserve fail-closed guards;
- add tests proving no mutating CAP method runs during ONLINE readiness; and
- document evidence without credentials.

### Owner action

- confirm the intended Agent and Service;
- approve the SDK package/version after evidence review;
- authorize the bounded ONLINE-only probe;
- observe the Dashboard result; and
- separately authorize any future controlled real order.

### External secret infrastructure

- inject the masked CROO SDK/API key at runtime;
- prevent logging and persistence;
- restrict access to the provider process; and
- support revocation without committing or rotating credentials through this repository.

### CROO platform dependency

- SDK authentication;
- WebSocket endpoint and heartbeat;
- Dashboard status transition;
- Agent Store visibility behavior; and
- platform-managed wallet/executor behavior.

### Controlled real-order authorization

Not included in Step 9-G-C. Negotiation acceptance, order creation, payment lock, delivery, completion, settlement, and human spot-check require a later explicit authorization with bounded value, counterparty, evidence, and stop conditions.

## Ordered critical path

1. Verify official SDK package/version, connection method, environment variables, and online-transition semantics.
2. Audit existing provider and observe-only code for reuse.
3. Decide whether a separate external provider process is necessary.
4. Add or configure only the non-mutating ONLINE-readiness path.
5. Prove with tests that connection does not invoke mutating CAP methods.
6. Obtain owner approval for a bounded ONLINE-only probe.
7. Verify heartbeat, Dashboard `ONLINE`, and Store discoverability.
8. Record evidence and stop with `real_cap_ready=false`.
9. Request separate controlled real-order authorization only after the ONLINE gate passes.

## Completion criteria

Step 9-G-C is complete only when the official provider heartbeat and resulting Dashboard state are verified without exposing credentials or invoking mutating CAP methods. Store discoverability remains pending if it cannot be observed independently. Real CAP lifecycle readiness remains pending until a separately authorized order completes.
