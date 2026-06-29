# Aegis CAP Truth Table

Date: 2026-06-30

## Purpose

This note is the submission-safe truth model for Aegis CROO/CAP readiness. Aegis is a pre-trade risk oracle and risk-check API. It is not a trading bot, wallet manager, execution agent, swap agent, or private-key agent.

## Current Truth

Aegis has local SDK runtime initialization evidence and a CAP-ready adapter posture. Aegis is not yet verified as an online CROO provider, is not accepting real CAP orders, and has not completed a real CAP payment, escrow, delivery, clear, settlement, reputation, or on-chain proof flow.

`real_cap_ready=false` is the correct current status.

## CAP Readiness Truth Table

| Layer | Meaning | Current Aegis status | Can claim? |
|---|---|---|---|
| Dashboard configured | Agent, Service, API key, schemas, price, SLA, and tags are configured in CROO Dashboard. | Needs sanitized dashboard evidence before being claimed beyond local env presence. | Partial only |
| SDK client initialized | `croo-sdk` imports and `AgentClient` initializes with runtime config. | Verified in Step 6C. | Yes |
| Agent online | WebSocket connected, heartbeat active, Agent visible and accepting orders. | Not verified. | No |
| Controlled provider behavior | Aegis provider guard validates service ID/name, schema, fund-transfer settings, and forbidden execution requests before any future accept path. | Step 7A guard and Step 7B adapter skeleton are pure local planning logic; both are disabled and disconnected from CROO/CAP runtime. | Local skeletons only |
| Real order lifecycle | Negotiation -> lock/pay/escrow -> deliver -> clear/settlement. | Not verified. | No |
| On-chain delivery proof | Real CAP delivery records the deliverable hash on-chain. | Not verified. | No |
| Reputation/settlement | CAP Clear and any reputation update occur after delivery. | Not verified. | No |

## Dashboard vs SDK Responsibility Split

Dashboard is the setup layer. It is where Agent registration, Service registration, API key issuance/rotation, requirements schema, deliverable schema, price, SLA, tags, and Agent status monitoring belong.

The SDK is the runtime/order lifecycle layer. It handles runtime order APIs and WebSocket connectivity. SDK import and `AgentClient` initialization prove only that the package and local runtime configuration can initialize. They do not prove Agent Store visibility, online heartbeat, Service activation, payment, escrow, delivery, settlement, or reputation.

WebSocket heartbeat is the online layer. Aegis must not claim the Agent is online, visible, or accepting orders until a deliberately controlled WebSocket provider path is built and verified.

## Provider Example Risk Warning

Official provider examples are not safe readiness probes for Aegis. They may connect a WebSocket, accept negotiations, and deliver sample results automatically. Aegis must not copy or run those examples directly because Aegis needs a controlled provider guard before any real order can be accepted.

Aegis must reject or refuse any request that asks it to execute trades, hold keys, sign transactions, perform swaps, broadcast transactions, enable fund-transfer service behavior, or deliver dummy payloads as if they were risk results.

## Forbidden CAP Methods For Current Readiness

Current readiness checks must not call:

- `negotiateOrder` / `negotiate_order`
- `acceptNegotiation` / `accept_negotiation`
- `acceptNegotiationWithFundAddress` / `accept_negotiation_with_fund_address`
- `payOrder` / `pay_order`
- `deliverOrder` / `deliver_order`
- `rejectOrder` / `reject_order`
- `uploadFile` / `upload_file`

They must also not settle, clear, create or mutate a real CAP order, call smart contracts directly, add wallet/private-key/signing/swap/transaction-broadcast logic, or expose secrets.

## Step 7A Local Provider Guard Scaffold

Step 7A adds a pure local classifier for hypothetical CAP negotiation/order payloads. It returns `accept_candidate`, `reject`, or `manual_review` after checking the Aegis Risk Check service identity, requirements schema, fund-transfer metadata, prompt-injection language, and prohibited execution requests.

The scaffold is disabled by disconnection: no listener calls it, no CROO SDK or WebSocket is imported, and no real order can be accepted. `accept_candidate` means only that a local payload passed the prefilter; it is not negotiation acceptance, provider readiness, Agent online status, or permission to call a CAP lifecycle method.

`CAP_MODE=mock` remains the default. `real_cap_ready=false` remains mandatory because online heartbeat, controlled provider integration, and the real negotiation -> lock/pay/escrow -> deliver -> clear/settlement lifecycle are unverified.

## Step 7B Disabled Provider Adapter Skeleton

Step 7B adds a local provider action planner gated by `CAP_REAL_PROVIDER_ENABLED=false` by default. Construction through environment configuration is refused unless the flag is explicitly enabled. Enabling it unlocks only local test planning; it does not start a listener, import the CROO SDK provider runtime, connect WebSocket, or call a CAP method.

The planner always runs the Step 7A guard first. A valid risk-check payload can produce only the hypothetical actions `would_accept` and `would_deliver_after_paid`; unsafe and ambiguous payloads produce `would_reject` or `would_manual_review`. These labels are plans, not real order actions. Every plan records `local_only=true`, `real_action_performed=false`, and `real_cap_ready=false`.

## Safe Next Step

Review and commit Step 7B while keeping the skeleton disconnected. Do not add a listener, WebSocket connection, provider example, SDK runtime import, or real CAP lifecycle call without a separate reviewed and explicitly approved step.
