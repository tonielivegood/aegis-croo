# Local CAP-Ready Order Lifecycle Design

## Goal

Add a local, in-memory CAP-shaped Order lifecycle that commissions the existing
Aegis Risk Check Service and returns its risk response as a structured
Deliverable with local Delivery Proof. This is a mock integration boundary,
not real CROO SDK, payment, escrow, settlement, reputation, or on-chain delivery.

## Scope and Safety

Step 4 adds `POST /orders`, `GET /orders/{order_id}`, and
`GET /proof/{proof_id}`. It stores local objects only for the current process.
It does not add CROO SDK dependencies, wallets, keys, signing, swaps, trade
execution, transaction construction, broadcasting, live providers, or a UI.
`EXECUTE` remains risk advice only; Aegis never executes a trade.

## Architecture

The feature has four focused modules:

- `models.py`: typed Order request, lifecycle, proof, and result models.
- `proof.py`: canonical JSON hashing and local proof construction.
- `ledger.py`: thread-safe in-memory order/proof storage and lifecycle orchestration.
- `orders.py`: thin FastAPI handlers that delegate to one process-local ledger.

`InMemoryOrderLedger.create_order` receives a validated `LocalOrderRequest`,
creates local identifiers and UTC timestamps, calls the existing `assess_risk`
exactly once, builds a proof, and stores the final order and proof atomically.
The risk engine remains the sole source of risk logic.

## Models and Validation

`LocalOrderRequest` contains non-empty requester/provider/service identifiers and
service name, non-negative `price_usdc`, positive `sla_minutes`, schema/text
requirements type, schema/text deliverable type, and the existing
`RiskCheckRequest` as `request`.

The Step 4 service fixture uses `requirements_type="schema"` and
`deliverable_type="schema"`. The returned `LocalOrderResult` contains exactly
the required Order fields plus the projected risk Deliverable and local proof.
`LocalDeliveryProof` contains exactly the seven requested proof fields.

Lifecycle status is a string enum and always advances synchronously through:

1. `NEGOTIATED_MOCK`
2. `LOCKED_MOCK`
3. `DELIVERED`
4. `CLEARED_MOCK`

The final status is always `CLEARED_MOCK` after the risk Deliverable and proof
are stored. These labels simulate shape only and do not claim payment, escrow,
settlement, or on-chain activity.

## Identifiers and Time

Orders use `order_<uuid4 hex>` and proofs use `proof_<uuid4 hex>`. They are
unique local identifiers, not blockchain or CAP SDK identifiers. `created_at`
and `completed_at` are timezone-aware UTC datetimes serialized as ISO-8601;
`completed_at` is never earlier than `created_at`.

## Hashing

Canonical JSON uses sorted keys, compact separators, ASCII-safe serialization,
and SHA-256:

- `request_hash`: the complete validated `LocalOrderRequest` JSON payload.
- `response_hash`: the complete `RiskCheckResponse` JSON Deliverable.
- `result_hash`: `{ "deliverable_type": "schema", "deliverable": <risk response> }`.

IDs and timestamps are excluded from all three hash inputs. Equivalent validated
payloads that yield the same risk response therefore produce identical hashes.
The wrapper makes `result_hash` semantically distinct from `response_hash` while
remaining deterministic.

## API Behavior

`POST /orders` returns the stored `LocalOrderResult`. `GET /orders/{order_id}`
returns that same typed object. `GET /proof/{proof_id}` returns the same
`LocalDeliveryProof`. Unknown identifiers return HTTP 404 without exposing
internal details.

The fixed disclaimer is:

`Local mock ledger only. No real CAP payment, escrow, on-chain delivery, or settlement.`

`cap_mode` is always `local_mock`.

## Testing

Tests create volatile and safe orders through FastAPI. They verify final status,
the exact lifecycle, BLOCK and EXECUTE risk decisions, persistence via both GET
routes, 404 behavior, proof fields and 64-character hashes, deterministic hashes
for equivalent payloads, CAP mode/disclaimer, timestamps, and the absence of
execution/wallet/key/signing/swap/transaction/broadcast response fields. The
existing health, risk-check, guards, and A2A tests must remain green.

## Documentation and Demo

`examples/order_flow_demo.py` uses only the Python standard library to POST a
local order and retrieve its order/proof records. README documents the three
local endpoints and repeats that storage and CAP lifecycle are mocks only.

## Self-Review

- All requested fields, endpoints, statuses, hashes, and failure cases are specified.
- Hash boundaries exclude nondeterministic IDs and timestamps.
- The ledger is process-local and intentionally non-persistent.
- Risk logic is reused without refactoring or duplication.
- No real CAP, payment, escrow, settlement, on-chain, wallet, or trading path exists.
- No Step 5 functionality or unrelated architecture is included.
