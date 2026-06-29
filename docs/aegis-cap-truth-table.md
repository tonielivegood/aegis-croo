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
| Controlled provider behavior | Aegis provider guard validates service ID/name, schema, fund-transfer settings, and forbidden execution requests before accept/deliver. | Not built. | No |
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

## Safe Next Step

Before any real provider test, design a controlled provider guard with `CAP_MODE=mock` as the default and an explicit disabled-by-default real-provider gate. The design should define validation for the target Service, schema, no fund transfer, no execution/wallet/signing/swap/broadcast requests, and safe delivery of Aegis risk-check schema output only.

Do not run a real WebSocket provider or official provider example until that guard design is reviewed and explicitly approved.
