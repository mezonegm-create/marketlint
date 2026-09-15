import httpx
import pytest

from marketlint.adapters.polymarket import fetch_market, fetch_markets


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_event_fetches_all_child_markets_and_inherits_event_metadata():
    def handler(request):
        assert request.url.path == "/events/slug/x"
        return httpx.Response(200, json={
            "description": "Event-level resolution rules",
            "resolutionSource": "Official Source",
            "endDate": "2026-12-31T23:59:00Z",
            "markets": [
                {
                    "id": "1",
                    "question": "Will X be above 10?",
                    "outcomes": '["Yes","No"]',
                    "outcomePrices": '["0.6","0.4"]',
                },
                {
                    "id": "2",
                    "question": "Will X be above 20?",
                    "outcomes": '["Yes","No"]',
                    "outcomePrices": '["0.2","0.8"]',
                },
            ],
        })

    client = _client(handler)
    try:
        markets = fetch_markets("https://polymarket.com/event/x", client=client)
    finally:
        client.close()
    assert [market.market_id for market in markets] == ["1", "2"]
    assert markets[1].prices == [0.2, 0.8]
    assert markets[0].resolution_source == "Official Source"
    assert markets[0].description == "Event-level resolution rules"


def test_single_market_uses_market_slug_endpoint():
    def handler(request):
        assert request.url.path == "/markets/slug/y"
        return httpx.Response(200, json={
            "id": "9",
            "question": "Will Y happen?",
            "outcomes": '["Yes","No"]',
        })

    client = _client(handler)
    try:
        market = fetch_market("https://polymarket.com/market/y", client=client)
    finally:
        client.close()
    assert market.market_id == "9"


def test_rejects_non_polymarket_hosts_before_network_access():
    with pytest.raises(ValueError, match="polymarket.com"):
        fetch_markets("https://example.com/event/x")


def test_rejects_malformed_polymarket_paths():
    with pytest.raises(ValueError, match="must contain"):
        fetch_markets("https://polymarket.com/x")
