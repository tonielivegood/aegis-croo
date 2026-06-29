# CROO Observe-Only WebSocket Probe Evidence - Step 7C-C

Date: 2026-06-30

## Scope

Step 7C-C ran one bounded real WebSocket connection-only probe through the
Step 7C-B observe-only safety harness. It did not run an official provider
example and did not create, negotiate, accept, reject, pay, deliver, upload,
settle, clear, or mutate any CAP order.

## Sanitized Preconditions

Before the connection:

- The working tree was clean at commit `72e62d1`.
- Both approved secret files existed; their contents were not printed.
- The user confirmed the Dashboard profile and `Aegis Risk Check` Service
  configuration, including Schema requirements, Schema deliverable,
  `require_fund_transfer=false`, and price `0.12 USDC`.
- No external local provider or probe process was found.
- `CAP_MODE=mock`.
- `CAP_REAL_PROVIDER_ENABLED=false`.
- `CAP_WS_OBSERVE_ONLY_ENABLED` was enabled only in the probe process.
- The timeout was exactly five seconds.
- The full fake-only test suite passed: `101 passed, 1 warning`.
- Static checks found no forbidden CAP lifecycle call.

## Sanitized Result

```json
{
  "probe_status": "verified_observe_only",
  "websocket_connection_status": "verified_observe_only",
  "agent_online_status": "observed_connection_only",
  "real_cap_ready": false,
  "closed": true,
  "mutating_methods_called": false,
  "event": null,
  "failure_reason": null
}
```

The process output was compared with both approved secret literals before it
was emitted. Neither literal appeared.

## What This Proves

- WebSocket authentication and initial connection succeeded once.
- The connection remained event-free for the bounded observation interval.
- The harness closed the stream after the timeout.
- No negotiation or order event was observed.
- No CAP mutating method was called.
- The connection-only status can be recorded as
  `agent_online_status=observed_connection_only` for this probe evidence.

## What This Does Not Prove

- Persistent WebSocket heartbeat or long-running availability.
- Agent Store visibility or accepting-orders status over time.
- Provider/Service identity through the socket alone.
- Controlled real negotiation acceptance or delivery behavior.
- Payment, escrow, settlement, clear, reputation, or on-chain proof.
- A complete commercial CAP order lifecycle.
- `real_cap_ready=true`.

## Approved PowerShell Shape

This command shape reads only the two approved files and does not echo their
contents. It must not be rerun without separate approval:

```powershell
cd E:\Aegis-CROO

$env:CAP_MODE = "mock"
$env:CAP_REAL_PROVIDER_ENABLED = "false"
$env:CAP_WS_OBSERVE_ONLY_ENABLED = "true"
$env:CAP_WS_OBSERVE_TIMEOUT_SECONDS = "5"
$env:CROO_WS_URL = "wss://api.croo.network/ws"
$env:CROO_SDK_KEY = (
    Get-Content -Raw "E:\Aegis-Secrets\croo-provider-key.txt"
).Trim()
$env:CROO_SERVICE_ID = (
    Get-Content -Raw "E:\Aegis-Secrets\croo-service-id.txt"
).Trim()

try {
    .\.venv\Scripts\python.exe scripts\croo_ws_observe_probe.py
}
finally {
    Remove-Item Env:CROO_SDK_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:CROO_SERVICE_ID -ErrorAction SilentlyContinue
    Remove-Item Env:CAP_WS_OBSERVE_ONLY_ENABLED -ErrorAction SilentlyContinue
}
```

## Current Readiness

`real_cap_ready=false` remains mandatory. The next step must remain
controlled and separately approved; it must not jump directly to a paid order
or copy the official auto-accept/auto-deliver provider example.
