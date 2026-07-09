# Step 9-G-C Gate 1 — Official SDK Provider ONLINE Readiness Verification

Date recorded: 2026-07-09 (plan filename retains the 2026-07-04 Step 9-G series numbering for continuity with the revised gap plan).

## Scope

This document is verification-only. It records the current official SDK contract, audits existing repository capability, and defines the smallest boundary-safe next step. **No runtime code was written or modified to produce this document.** No CROO/CAP API was called, no WebSocket was opened, and no CAP lifecycle method was run while preparing it.

## Gate 1 — Official SDK contract (verified against primary sources)

Checked directly against the CROO-Network GitHub organization and PyPI on 2026-07-09:

| SDK | Repository | Package | Status |
| --- | --- | --- | --- |
| Python | `github.com/CROO-Network/python-sdk` | `croo-sdk` (PyPI, latest `0.2.1`, released 2026-05-22; import name `croo`) | **Fully verified**, including at local installed-source level (`croo/agent_client.py`, `croo/ws.py`, `croo/types.py`, `croo/errors.py`) — see `docs/croo-python-sdk-contract-step6a.md` and `docs/croo-websocket-provider-readiness-step7c-a.md`. |
| Go | `github.com/CROO-Network/go-sdk` | Go module `croo` | Verified only at README-summary level via this session's fetch; not verified at source-line level like Python. |
| Node/TypeScript | `github.com/CROO-Network/node-sdk` | `@croo-network/sdk` (npm) | Verified only at README-summary level via this session's fetch; not verified at source-line level. |

**Chosen SDK candidate: Python (`croo-sdk` 0.2.1), import package `croo`.** It is the only SDK with source-level primary verification already on record in this repository, and the repository is Python-only (FastAPI + pytest); introducing Go or Node would add a second toolchain and an unverified contract simultaneously, which is not the smallest safe path.

### Exact verified connection contract (Python)

```python
from croo import AgentClient, Config

client = AgentClient(
    Config(base_url=os.environ["CROO_API_URL"], ws_url=os.environ["CROO_WS_URL"]),
    os.environ["CROO_SDK_KEY"],
)
stream = await client.connect_websocket()   # returns an EventStream; opens a real network connection
stream.on_any(handler)                       # handler: Callable[[Event], None], called synchronously
await stream.close()
error = stream.err()
```

- Auth: SDK key sent as the `key` query parameter on the WebSocket URL, and as the `X-SDK-Key` HTTP header for REST calls. No bearer prefix.
- Heartbeat: 30-second ping interval, 60-second pong timeout, auto-reconnect with exponential backoff capped at 30 seconds. Close code 1008 (duplicate key session) stops reconnect.
- Event types: `NEGOTIATION_CREATED`, `NEGOTIATION_REJECTED`, `NEGOTIATION_EXPIRED`, `ORDER_CREATED`, `ORDER_PAID`, `ORDER_COMPLETED`, `ORDER_REJECTED`, `ORDER_EXPIRED`.
- **Known credential-logging risk (already documented, still unresolved):** the SDK source logs the full WebSocket URL — including the `key` query parameter — at INFO level. Any persistent-connection process **must** install log redaction (the repo's `src/aegis_croo/cap/ws_safety.py` already provides `redact_sensitive_text`) before constructing the client, at WARNING level or stricter, matching the pattern already used in `scripts/croo_ws_observe_probe.py`.

### Required environment variables

`CROO_API_URL`, `CROO_WS_URL`, `CROO_SDK_KEY`, and optionally `BASE_RPC_URL` (defaults to Base mainnet JSON-RPC, unrelated to Aegis Core). `CROO_SERVICE_ID` and `CROO_PROVIDER_AGENT_ID` are Aegis-repo-level config, not SDK-required.

### Private key / signing / mutation at connection time

Cross-checked against all three official SDKs (Node README makes this most explicit): **account setup — agent creation, service registration, SDK-Key issuance — is handled entirely in the Dashboard and is not part of any SDK.** No SDK requires a private key, local signing, or wallet access merely to construct a client or open the WebSocket. The wallet referenced in the CROO Dashboard is a platform-managed Account Abstraction wallet, not something the SDK or Aegis Core touches.

## Gate 2 — Existing repository capability (read-only audit)

The repository already contains real, working provider-readiness scaffolding. It does **not** yet contain a persistent provider runtime.

| Component | File | What it does | Reusable for ONLINE readiness? |
| --- | --- | --- | --- |
| CAP config/env loader | `src/aegis_croo/cap/config.py` | Reads `CAP_MODE`, `CROO_API_URL/WS_URL/SDK_KEY/SERVICE_ID`, all provider-runtime feature flags (default `false`) | Yes, reuse as-is |
| Credential/log redaction | `src/aegis_croo/cap/ws_safety.py` | Redacts SDK keys, credential-bearing WS URLs, sensitive headers from any text/logs | Yes, reuse as-is |
| Observe-only WS harness | `src/aegis_croo/cap/ws_observe_harness.py` | Generic bounded-timeout harness: connects an injected stream, waits for first event OR timeout, always closes, never routes to a mutating handler | Yes — this is the correct base for a longer-lived (not just 5-second) ONLINE probe |
| Real SDK status probe | `src/aegis_croo/cap/adapter.py` (`_probe_real_cap_sdk_readiness`) | Lazily imports `croo`, constructs `Config`/`AgentClient` only, **never calls `connect_websocket`** | Yes — proves client construction is already safe and already wired into `/cap/status` |
| Gated real SDK adapter | `src/aegis_croo/cap/gated_real_sdk_adapter.py` | Wraps `AgentClient.connect_websocket()` behind five independent authorization gates (pilot, connector-start, sdk-load, negotiation-pilot, no mutation flags); real connection only reachable if all pass | Partially — built for the Option-B *negotiation* pilot, not a plain ONLINE heartbeat; heavier than needed for Gate 1's narrower goal |
| Standalone observe-only probe script | `scripts/croo_ws_observe_probe.py` | External process (does **not** import or start `apps/api`), validates `CAP_MODE=mock`, `CAP_REAL_PROVIDER_ENABLED=false`, `CAP_WS_OBSERVE_ONLY_ENABLED=true`, a credential-free `wss://` URL, then opens one real bounded connection via the harness above and closes it | **Yes — this is the closest existing precedent to reuse and extend** |
| Negotiation pilot runners | `option_b_pilot_runner.py`, `manual_negotiation_pilot_runner.py`, `quarantined_sdk_connector.py`, `live_connector_wrapper.py` | Built for a later, separately-authorized negotiation-observation pilot, not ONLINE readiness | Not needed for Gate 1/ONLINE-only scope; leave untouched |

**No official `croo-sdk` dependency is declared in `requirements.txt`.** The package is imported lazily via `importlib.import_module("croo")` everywhere, and is not installed in the tracked dev environment. This is correct for keeping `CAP_MODE=mock` fully import-free, but means a real ONLINE attempt requires `pip install croo-sdk` into whatever environment runs the provider process (not necessarily the Aegis Core venv).

### Prior real-world evidence already on record (important — this is not a cold start)

`docs/croo-websocket-observe-probe-step7c-c.md` records that **a real, bounded (5-second), observe-only WebSocket connection to the actual CROO backend already succeeded once, on 2026-06-30**, using exactly `scripts/croo_ws_observe_probe.py`:

```json
{"probe_status": "verified_observe_only", "websocket_connection_status": "verified_observe_only",
 "agent_online_status": "observed_connection_only", "real_cap_ready": false, "closed": true,
 "mutating_methods_called": false, "event": null, "failure_reason": null}
```

This proves the SDK-key auth and WebSocket connection mechanism itself already works end-to-end and safely (no mutation, no leaked secret in output). It explicitly does **not** prove persistent heartbeat, Store discoverability, or a sustained Dashboard ONLINE transition — the connection was intentionally closed after 5 seconds, which is consistent with the owner verifying the Dashboard still showed `OFFLINE` on 2026-07-04 (four days later). **The remaining gap is duration/persistence, not connection feasibility.**

The two external credential files referenced by that probe (`E:\Aegis-Secrets\croo-provider-key.txt`, `E:\Aegis-Secrets\croo-service-id.txt`) still exist outside the repository as of 2026-07-09 (existence confirmed by directory listing only; contents were not read). External secret infrastructure for a future approved run is therefore already in place.

### A discrepancy worth naming (resolved, not a blocker)

At first read, `scripts/croo_ws_observe_probe.py`'s `_create_sdk_stream` constructs `croo_sdk.EventStream(sdk_key, ws_url)` directly, which looks inconsistent with the documented contract (`AgentClient(...).connect_websocket()` is what returns an `EventStream`). This is **not** an open bug: Step 7C-C already exercised this exact code path against the real backend and got a successful, sanitized result, so the direct-construction call is empirically confirmed to work against installed `croo-sdk` 0.2.1. Recorded here only so a future reader doesn't mistake it for an untested assumption.

## Gate 3 — Smallest boundary-safe next step

Two options were available per the revised gap plan (`docs/superpowers/plans/2026-07-04-step9g-revised-real-cap-gap-plan.md`):

1. **Reuse the existing non-mutating observe-only harness**, extended from a 5-second bounded probe to a longer-lived (but still time-bounded and kill-switched) connection, run as the same kind of standalone script under `scripts/`, outside `apps/api`.
2. Operate a wholly new separate provider process.

**Selected: Option 1.** `scripts/croo_ws_observe_probe.py` plus `ObserveOnlyWebSocketHarness` already are a separate external process with no coupling to Aegis Core (`apps/api`, `src/aegis_croo/oracle`, `src/aegis_croo/guards` are untouched by any CAP-readiness code path). Building a second, unrelated separate process would duplicate this instead of reusing it, which the revised gap plan's Gate 2 explicitly says to avoid ("prefer reuse over new code... do not duplicate an existing bounded provider harness").

## Gate 1 classification table (per task instructions)

| Question | Classification | Basis |
| --- | --- | --- |
| Is SDK-key auth sufficient to initialize the runtime client? | **YES_VERIFIED** | Step 6A source read: `AgentClient(config, sdk_key)` takes only `base_url`, `ws_url`, and the key string. |
| Is SDK-key auth sufficient to open the WebSocket? | **YES_VERIFIED** | Step 7C-A source read + Step 7C-C real successful connection; key travels as a WS query parameter, nothing else required. |
| Does merely opening the WebSocket create negotiation/order/payment/delivery/settlement/on-chain tx? | **NO_VERIFIED** | Step 7C-A: connecting only starts read/ping loops and dispatches to `on_any`/`on` handlers; mutation only happens if a handler explicitly calls a mutating method, which the harness never registers. Step 7C-C's real run observed zero events and zero mutation. |
| Is a private key required merely for client init / WS connect / heartbeat / passive listening? | **NO_VERIFIED** (Python, Node); **UNCLEAR_NEEDS_VERIFICATION** (Go) | Python confirmed at source level; Node README explicitly states account/wallet setup is Dashboard-only and not part of the SDK; Go was only checked via README summary in this session, not source. |
| Is a mutating CAP method required merely to become ONLINE? | **NO_VERIFIED** | Same Step 7C-A/7C-C evidence: connection and Dashboard `OFFLINE`→`ONLINE` transition are a function of an open, authenticated WebSocket, not of calling `accept_negotiation`/`pay_order`/`deliver_order`. |

## Zero-mutating-method rule (binding for any future run)

The following must never be called, imported for use, or reachable from any dispatch path during ONLINE-readiness work:

- `negotiate_order`
- `accept_negotiation` / `accept_negotiation_with_fund_address`
- `reject_negotiation`
- `pay_order`
- `deliver_order`
- `reject_order`
- `upload_file`
- `get_download_url`
- any settle, clear, create-order, wallet, private-key, signing, swap, transaction-construction, or broadcast method

This matches `docs/croo-websocket-provider-readiness-step7c-a.md`'s "Methods That Remain Blocked" list and the existing AST/call-recorder test pattern in `tests/test_cap_ws_observe_harness.py` / `tests/test_croo_ws_observe_probe.py`.

## Expected ONLINE-transition and heartbeat evidence (for a future approved run)

A future bounded test may record, and only record:

- WebSocket authentication and connection succeeded.
- The connection stayed open for the approved interval (longer than 5 seconds — long enough to plausibly register as a heartbeat cycle, i.e. at least one 30-second ping interval, ideally several).
- The stream closed cleanly when the kill timer fired, or on explicit operator stop.
- No business event was routed to a mutating handler (none is registered).
- Sanitized Dashboard evidence, captured separately by the owner, showing the Agent transitioning from `OFFLINE` to `ONLINE` during the same interval, if the Dashboard exposes that transition.
- `real_cap_ready` remains `false` throughout and after.

It must **not** claim: Store discoverability, negotiation, order creation, payment, delivery, settlement, or any commercial-readiness fact beyond the connection/heartbeat observation itself.

## Rollback / stop conditions

Stop and do not proceed to a real connection attempt if, at execution time:

- `CAP_MODE` is anything other than `mock` outside the single approved probe invocation.
- The credential-free-URL check on `CROO_WS_URL` fails (any query string, userinfo, or embedded fragment).
- Static/AST tests proving the blocked-method list is unreachable do not pass.
- The external secret files are missing, or a second process might already hold the same SDK-Key session (duplicate-key close code 1008 risk).
- Any pending negotiation or unpaid/unsettled order might exist for this Agent (would make an accidental event non-hypothetical).
- Sanitized Dashboard evidence cannot be captured before or after the run.

## Commands / tests reserved for later implementation (not run in this task)

These are named for Step 9-G-C Gate 4 implementation planning only — none were executed while producing this document:

```powershell
# Environment (values sourced only from E:\Aegis-Secrets, never printed)
$env:CAP_MODE = "mock"
$env:CAP_REAL_PROVIDER_ENABLED = "false"
$env:CAP_WS_OBSERVE_ONLY_ENABLED = "true"
$env:CAP_WS_OBSERVE_TIMEOUT_SECONDS = "<owner-approved bounded value, longer than 5s>"

# Test command reserved for Gate 4 (already exists; rerun only, no new authoring needed for Gate 1):
.\.venv\Scripts\python.exe -m pytest tests\test_cap_ws_observe_harness.py tests\test_croo_ws_observe_probe.py tests\test_cap_ws_safety.py -q
```

Any change to `CAP_WS_OBSERVE_TIMEOUT_SECONDS` beyond the current 60-second bound enforced in `config.py` (`_configured_bounded_float`) requires a corresponding, separately reviewed code change — not just an environment variable — since the bound is presently hardcoded in the harness at 5.0 seconds default and clamps at `(0, 60]`.

## Prohibited during any ONLINE canary (explicit, per task instruction)

- `AcceptNegotiation` / `accept_negotiation`
- `NegotiateOrder` / `negotiate_order`
- `PayOrder` / `pay_order`
- `DeliverOrder` / `deliver_order`
- real order creation
- payment
- settlement
- any transaction mutation

## Conclusion

Gate 1 is complete. The official SDK contract is verified (Python, source-level). The repository already contains reusable, boundary-safe scaffolding for exactly this purpose, and a real bounded connection has already succeeded once (2026-06-30) without any mutation. The only remaining engineering gap before requesting an owner-approved ONLINE canary is extending the existing bounded probe from a short fixed timeout to an owner-approved longer interval with the same zero-mutating-method guarantees — not building anything new from scratch, and not touching Aegis Core.

No implementation is authorized by this document. Gate 4 (implementation) and Gate 5 (bounded owner-approved validation) remain separate, future, explicitly-approved steps.
