import json
from urllib.request import Request, urlopen


API_BASE_URL = "http://127.0.0.1:8000"

LOCAL_ORDER = {
    "requester_agent_id": "mock-requester-agent",
    "provider_agent_id": "aegis-risk-oracle",
    "service_id": "aegis-risk-check-schema-v1",
    "service_name": "Aegis Risk Check",
    "sla_minutes": 5,
    "price_usdc": 0.25,
    "requirements_type": "schema",
    "deliverable_type": "schema",
    "request": {
        "token": "BNB",
        "chain": "bsc",
        "intended_action": "buy",
        "size_usd": 100,
        "market_signal": {
            "price_change_24h": -8,
            "volume_change_24h": -10,
            "liquidity_usd": 50_000,
            "volatility_24h": 9,
        },
    },
}


def request_json(method: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{API_BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def main() -> None:
    created = request_json("POST", "/orders", LOCAL_ORDER)
    stored_order = request_json("GET", f"/orders/{created['order_id']}")
    stored_proof = request_json("GET", f"/proof/{created['proof_id']}")
    print(json.dumps({
        "created_order": created,
        "stored_order": stored_order,
        "stored_proof": stored_proof,
    }, indent=2))


if __name__ == "__main__":
    main()
