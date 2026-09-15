import httpx

from marketlint.adapters.polymarket import fetch_market, fetch_markets


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_event_fetches_all_child_markets():
    def handler(request):
        assert request.url.path == "/events"
        return httpx.Response(200, json=[{"markets": [
            {"id": "1", "question": "Will X be above 10?", "outcomes": '["Yes","No"]', "outcomePrices": '["0.6","0.4"]'},
            {"id": "2", "question": "Will X be above 20?", "outcomes": '["Yes","No"]', "outcomePrices": '["0.2","0.8"]'},
        ]}])

    client = _client(handler)
    try:
        markets = fetch_markets("https://polymarket.com/event/x", client=client)
    finally:
        client.close()
    assert [market.market_id for market in markets] == ["1", "2"]
    assert markets[1].prices == [0.2, 0.8]


def test_single_market_fetch_remains_backward_compatible():
    def handler(request):
        assert request.url.path == "/markets"
        return httpx.Response(200, json=[{"id": "9", "question": "Will Y happen?", "outcomes": '["Yes","No"]'}])

    client = _client(handler)
    try:
        market = fetch_market("https://polymarket.com/market/y", client=client)
    finally:
        client.close()
    assert market.market_id == "9"
