# CROO Real Readiness Probe Evidence - Step 6C

Date: 2026-06-29

## Scope

Step 6C was a controlled local readiness probe of `GET /cap/status` only.

This was not a real CAP order test. It did not create, negotiate, pay, deliver, reject, upload, settle, clear, or mutate any real CAP order. It did not add or exercise wallet, private key, signing, swap, transaction construction, broadcast, or live trading logic.

## Preconditions

- `croo-sdk` version `0.2.1` was installed in the local project virtual environment.
- The full local test suite passed before the real-mode status probe.
- Secret values were loaded into process environment variables only.
- Secret values were not printed, pasted, logged, committed, or serialized in the reported response.
- No `.env` file was created.

## Recovery From Stale Local API State

An earlier probe attempt reached a stale local Aegis-CROO uvicorn reload-chain process on port `8000`, which returned mock-mode status. The stale Aegis-CROO API processes were identified and stopped.

The successful recovery probe avoided port `8000` and launched a fresh single-process API on port `8010` without `--reload`, so the API process inherited the approved real-mode environment directly.

## Sanitized Probe Response

The successful probe called only:

```text
GET http://127.0.0.1:8010/cap/status
```

The response was checked against the literal secret values before being reported. No secret value appeared in the response.

Sanitized response:

```json
{
  "cap_mode": "real",
  "real_cap_ready": false,
  "adapter_status": "REAL_CAP_CLIENT_INITIALIZED_READINESS_UNVERIFIED",
  "sdk_import_status": "ok",
  "service_id_status": "present_unverified",
  "credential_status": "present",
  "provider_agent_id": "aegis-risk-oracle",
  "disclaimer": "Real CAP configuration is present, but Step 6 provider verification has not run. No real CAP action was performed.",
  "client_init_status": "ok",
  "readiness_reason": "SDK client initialized, but provider/service readiness requires official read-only verification or dashboard confirmation.",
  "missing": []
}
```

## Evidence Interpretation

- `cap_mode="real"` means the fresh API process inherited `CAP_MODE=real`.
- `sdk_import_status="ok"` means the installed CROO SDK package imported.
- `client_init_status="ok"` means `AgentClient` initialized with the configured API/WS URLs and SDK key.
- `service_id_status="present_unverified"` means service configuration was present, but the service identity was not verified through an official safe read-only CROO/CAP method.
- `credential_status="present"` means a credential was present in the process environment. It does not expose or validate the secret value in this status.
- `real_cap_ready=false` is the honest expected result because Step 6C did not prove provider/service readiness.

## What Step 6C Did Not Prove

Step 6C did not verify:

- Provider/service ownership or readiness through an official safe read-only CROO/CAP method.
- Real CAP payment.
- Escrow locking.
- Settlement or clearing.
- Reputation updates.
- Upload or delivery.
- On-chain delivery or transaction submission.

## Verification After Probe

After the probe, the local API process on port `8010` was stopped.

The full local test suite passed:

```text
58 passed, 1 warning
```

Known warning:

```text
StarletteDeprecationWarning from fastapi.testclient / httpx
```

Git status was clean after the probe before this documentation step.

## Next Step

Step 6D should be plan-only unless explicitly approved otherwise:

- Identify an official safe read-only provider/service verification path, or
- Define what CROO Dashboard evidence is acceptable before allowing `real_cap_ready=true`.

Until that evidence exists, `real_cap_ready=false` remains the correct and safe status.
