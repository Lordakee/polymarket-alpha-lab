from polymarket_alpha_lab.api import PolymarketPublicClient


class FakeTransport:
    def __init__(self):
        self.calls = []

    def get_json(self, url, *, timeout):
        self.calls.append((url, timeout))
        return [{"id": "1"}]


def test_list_markets_uses_gamma_endpoint_and_query_parameters():
    transport = FakeTransport()
    client = PolymarketPublicClient(transport=transport, timeout_seconds=7)

    payload = client.list_markets(active=True, closed=False, limit=25)

    assert payload == [{"id": "1"}]
    assert transport.calls == [
        (
            "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=25",
            7,
        )
    ]


def test_get_order_book_uses_clob_book_endpoint():
    transport = FakeTransport()
    client = PolymarketPublicClient(transport=transport)

    client.get_order_book(token_id="123")

    assert transport.calls[0][0] == "https://clob.polymarket.com/book?token_id=123"
