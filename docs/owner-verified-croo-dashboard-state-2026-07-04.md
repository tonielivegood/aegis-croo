# Owner-Verified CROO Dashboard State — 2026-07-04

Status: Owner-verified UI evidence. This document does not claim that the provider is online, publicly discoverable, or proven through a real CAP lifecycle.

## A. PASS_VERIFIED owner-side CROO facts

The owner verified these facts directly in the CROO Dashboard on 2026-07-04:

- Agent name: `Aegis Risk Oracle`.
- The Agent is registered in the CROO Dashboard.
- The displayed source is `SDK`.
- CROO shows a platform-visible Agent Wallet. This is not evidence of wallet custody in Aegis Core.
- Service name: `Aegis Risk Check`.
- The Service exists and is configured.
- Displayed price: `0.12 USDC`.
- Displayed SLA: `5 minutes`.
- A Service ID exists. Only a truncated value was visible, so no full Service ID is recorded or inferred.
- A CROO SDK/API key has been issued. It is masked in the UI; no key value is recorded, reconstructed, rotated, or committed.

### Verified deliverable schema

| Field | Type | Required | Constraint |
| --- | --- | --- | --- |
| `decision` | string | yes | `BLOCK`, `WAIT`, or `EXECUTE` |
| `risk_score` | number | yes | 0–100 |
| `confidence` | string | yes | `low`, `medium`, or `high` |
| `safe_to_execute` | boolean | yes | — |
| `suggested_action` | string | yes | — |
| `proof_id` | string | yes | — |
| `risk_factors` | array of string | yes | — |

### Verified requirements/input schema

| Field | Type | Required |
| --- | --- | --- |
| `token` | string | yes |
| `chain` | string | yes |
| `intended_action` | string | yes |
| `size_usd` | number | yes |
| `price_change_24h` | number | no |
| `volume_change_24h` | number | no |
| `liquidity_usd` | number | no |
| `volatility_24h` | number | no |

## B. Current OFFLINE state

- The CROO Dashboard currently displays the Agent as `OFFLINE`.
- `OFFLINE` is not evidence of an active official SDK provider runtime.
- No verified WebSocket heartbeat or `ONLINE` transition is claimed.
- Public CROO Agent Store discoverability is not claimed.

## C. Real CAP lifecycle still pending

The following remain pending or unverified:

- official SDK provider `ONLINE` status;
- WebSocket heartbeat/provider runtime;
- public Store discoverability while online;
- real negotiation receipt or acceptance;
- real on-chain order creation;
- real payment lock;
- real delivery through the official CAP lifecycle;
- completion or settlement evidence;
- a controlled real order; and
- human spot-check evidence.

`CAP_MODE=mock` and `real_cap_ready=false` remain the correct repository status until separately reviewed evidence establishes otherwise.

## D. Prohibited inferences

Do not infer from the owner-verified facts that:

- the Agent is online or publicly discoverable;
- a real CAP order, payment, escrow, delivery, completion, or settlement works;
- Aegis Core holds or manages the platform-visible Agent Wallet;
- any private key or SDK/API key belongs in this repository;
- Aegis Core performs signing, transaction construction, transaction broadcast, swaps, or live trading; or
- the truncated Service ID can be reconstructed.

Aegis remains a callable pre-execution risk-check service. It checks risk before execution and does not execute trades, swaps, rebalances, or DeFi actions.

## Correction note

Previous audits that marked Agent registration, Service creation, or SDK key issuance as missing were incomplete because owner-side CROO Dashboard evidence was not available.
