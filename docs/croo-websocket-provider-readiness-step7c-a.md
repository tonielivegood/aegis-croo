# CROO WebSocket Provider Readiness Audit - Step 7C-A

Date: 2026-06-30

## Scope

Step 7C-A is a local source audit and plan only. No CROO SDK runtime module was
imported, no credential was used, no WebSocket was opened, and no provider
example or CAP lifecycle method was run.

Sources inspected:

- Installed package metadata for `croo-sdk 0.2.1`
- Installed local source: `croo/agent_client.py`, `croo/ws.py`,
  `croo/types.py`, `croo/errors.py`, and `croo/__init__.py`
- Installed package `METADATA`, which contains the official README examples
- Existing Aegis Step 6A, Step 6C, Step 7A, and Step 7B materials

## Current Status After Step 7B

- `CAP_MODE=mock` and `CAP_REAL_PROVIDER_ENABLED=false` are defaults.
- The Step 7A guard and Step 7B planner are pure local logic.
- Neither component listens for events or performs a CAP action.
- Every `/cap/status` path keeps `real_cap_ready=false`.
- Aegis is not verified online, visible, or accepting orders on CROO.

## Verified SDK WebSocket Contract

The exact connection call is asynchronous:

```python
stream = await client.connect_websocket()
```

It requires `Config.ws_url`, creates an `EventStream`, immediately awaits
`stream.connect()`, and opens a real network connection. It is not a local
readiness check.

The callback model is:

```python
stream.on(event_type, handler)
stream.on_any(handler)
await stream.close()
error = stream.err()
```

Handlers are synchronous `Callable[[Event], None]` callbacks. The dispatcher calls
them directly and does not await coroutine handlers. Official examples schedule
asynchronous work from synchronous callbacks.

Event types are `NEGOTIATION_CREATED`, `NEGOTIATION_REJECTED`,
`NEGOTIATION_EXPIRED`, `ORDER_CREATED`, `ORDER_PAID`,
`ORDER_COMPLETED`, `ORDER_REJECTED`, and `ORDER_EXPIRED`.

The stream starts read and ping loops after connection. It uses a 30-second ping
interval, a 60-second pong timeout, and automatic reconnect with exponential
backoff capped at 30 seconds. Duplicate-key close code 1008 stops reconnect and
is exposed through `stream.err()`; other disconnects trigger reconnect.

## Credential And Logging Risk

The SDK places the raw SDK key in the WebSocket URL as the `key` query
parameter. The source logs that complete URL at INFO level. Reconnect exceptions
and parse failures may also include backend or raw event data.

An unwrapped online test is unsafe. A future wrapper must prove with
sentinel-only tests that the key and raw event payload cannot appear in console,
file, test, or captured logs. Suppressing INFO alone is insufficient unless
warning and error paths are sanitized too.

## Official Provider Example Risk

The official provider example is mutating:

- `NEGOTIATION_CREATED` schedules `accept_negotiation`.
- `ORDER_PAID` schedules `deliver_order`.

The requester example calls `negotiate_order` and `pay_order`. These
examples must not be copied, imported, or run as readiness probes.

## Methods That Remain Blocked

The readiness path must not call or dynamically dispatch:

- `negotiate_order`
- `accept_negotiation`
- `accept_negotiation_with_fund_address`
- `reject_negotiation`
- `pay_order`
- `deliver_order`
- `reject_order`
- `upload_file`
- `get_download_url`
- Any settle, clear, create, mutate, wallet, private-key, signing, swap,
  transaction-construction, broadcast, or live-trading method

## What A Future Online Test May Prove

After all prerequisites pass and separate approval is given, a bounded
observe-only test may prove only:

- WebSocket authentication and initial connection succeeded.
- The connection stayed open for the approved interval.
- The stream closed when the kill timer fired.
- No business-event handler and no mutating method ran.
- Sanitized Dashboard evidence showed the expected Agent online during the
  same interval, if the Dashboard exposes that state.

SDK 0.2.1 exposes no successful-pong callback or public heartbeat counter. A
short connection alone is not direct heartbeat proof.

## What It Must Not Claim

A bounded connection must not claim real order acceptance, provider/Service
identity verification by socket alone, payment, escrow, delivery, clear,
settlement, reputation, on-chain proof, a complete lifecycle, or any wallet,
signing, swap, transaction, broadcast, or trading capability.
`real_cap_ready` must remain false.

## Required Sanitized Dashboard Evidence

Before requesting approval, record sanitized evidence that:

- The expected Agent ID and display name are configured.
- The expected Service ID and `Aegis Risk Check` belong to that Agent.
- Requirements and deliverable schemas match the reviewed risk-check contract.
- `require_fund_transfer` is false.
- Price, SLA, and tags match the intended listing.
- An SDK key is associated with the Agent, showing presence or a masked
  identifier only.
- The pre-test online/offline state is recorded.
- No unrelated process uses the same SDK key.
- No pending negotiations or paid orders could be affected.

## Required Kill Switches

The implemented local harness defaults to:

```text
CAP_MODE=mock
CAP_REAL_PROVIDER_ENABLED=false
CAP_WS_OBSERVE_ONLY_ENABLED=false
CAP_WS_OBSERVE_TIMEOUT_SECONDS=5.0
```

Every observed event aborts unconditionally; there is no permissive event mode.
These settings are fake-only in Step 7C-B. Enabling the observe-only gate must
not enable the Step 7B planner or change `real_cap_ready`. Dashboard evidence
and a separate real-SDK adapter remain prerequisites for any approved
connection attempt.

The wrapper must use one process without reload, install log redaction before
client construction, register no mutating callback, enforce a wall-clock
timeout, call `stream.close()` in `finally`, and terminate if graceful close
does not finish.

## Exact Abort Conditions

Abort before connection if Dashboard evidence is missing or mismatched, fund
transfer is enabled, schemas differ, secret-safe logging tests fail, kill-switch
defaults are permissive, another process may use the key, or pending
negotiations/paid orders exist.

Close and stop immediately if:

- Any negotiation or order event arrives.
- Any handler schedules work.
- Any blocked method is resolved for dispatch or called.
- A key, credential-bearing URL, raw event payload, or sensitive ID is logged.
- `stream.err()` becomes non-null.
- Close code 1008, authentication, or policy error occurs.
- Automatic reconnect begins.
- Dashboard Agent/Service identity mismatches.
- Timeout or graceful-close deadline is exceeded.
- `real_cap_ready` becomes true.

## Safe Step 7C Implementation Plan

1. Add the proposed readiness settings with safe defaults.
2. Build a local observe-only controller against a fake stream interface; do
   not import `croo` at module import time.
3. Add sentinel tests for connection, reconnect, parse, and exception log
   redaction.
4. Add fake-stream tests for timeout, event abort, stream errors, graceful
   close, and forced-stop signaling.
5. Add AST and call-recorder tests proving blocked methods are unreachable.
6. Review sanitized Dashboard evidence and confirm no pending work or duplicate
   SDK-key session.
7. Request separate approval for one bounded connection-only probe.
8. Record only sanitized timing and Dashboard online evidence.
9. Keep `real_cap_ready=false` and document unverified lifecycle layers.

## Audit Conclusion

A real Step 7C online test is **not safe to attempt next**. First implement and
fake-test the observe-only controller, log redaction, and kill switches, then
review Dashboard evidence. A real connection requires separate explicit
approval after those prerequisites pass.

## Step 7C-B Local Harness Status

Step 7C-B implements the first prerequisite as a fake-only, dependency-injected
local harness. It adds:

- `CAP_WS_OBSERVE_ONLY_ENABLED=false` by default.
- `CAP_WS_OBSERVE_TIMEOUT_SECONDS=5.0` with bounded parsing.
- SDK-key, credential-query, sensitive-header, and credential-bearing
  WebSocket URL redaction.
- Sanitized event summaries containing event type and ID-presence booleans
  only.
- Immediate abort planning for every observed event.
- Hard timeout, connector cancellation, and bounded close in all enabled runs.
- Fake-stream and AST tests proving no SDK, network, WebSocket, or CAP
  mutating call is present.

The harness accepts an injected stream and connect coroutine. It does not import
`croo`, create an SDK client, open a socket, or provide a real provider
listener. Enabling it only permits a caller-supplied local test dependency to
run. It does not enable `CAP_REAL_PROVIDER_ENABLED`, change `CAP_MODE`, or
set `real_cap_ready=true`.

Step 7C-B does not make a real connection safe by itself. Sanitized Dashboard
evidence, duplicate-session and pending-order checks, a reviewed real-SDK
adapter boundary, and separate explicit approval are still required before a
bounded online probe.
