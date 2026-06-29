import json
from urllib.request import Request, urlopen


MOCK_ORDER_URL = "http://127.0.0.1:8000/a2a/mock-order"

MOCK_ORDER = {
    "buyer_agent_id": "mock-execution-agent",
    "requested_action": {
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


def main() -> None:
    request = Request(
        MOCK_ORDER_URL,
        data=json.dumps(MOCK_ORDER).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        result = json.load(response)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
