import json
from datetime import UTC, datetime

from polymarket_alpha_lab.pipeline import MarketScanConfig, run_market_scan


class FakeClient:
    def __init__(self):
        self.book_calls = []

    def list_markets(self, *, active, closed, limit):
        assert active is True
        assert closed is False
        assert limit == 2
        return [
            {
                "conditionId": "0xabc",
                "slug": "example-market",
                "question": "Will the example resolve yes?",
                "active": True,
                "closed": False,
                "acceptingOrders": True,
                "enableOrderBook": True,
                "volume24hr": "10000",
                "liquidity": "20000",
                "outcomes": '["Yes","No"]',
                "clobTokenIds": '["111","222"]',
                "description": "Clear rules",
                "resolutionSource": "https://example.com",
            }
        ]

    def get_order_book(self, *, token_id):
        self.book_calls.append(token_id)
        if token_id == "222":
            raise RuntimeError("book temporarily unavailable")
        return {
            "asset_id": token_id,
            "bids": [{"price": "0.49", "size": "500"}],
            "asks": [{"price": "0.51", "size": "500"}],
        }


def test_run_market_scan_archives_raw_data_and_writes_ranked_candidates(tmp_path):
    captured_at = datetime(2026, 6, 13, 12, 30, tzinfo=UTC)
    output_path = tmp_path / "artifacts" / "scores.json"
    client = FakeClient()

    candidates = run_market_scan(
        client=client,
        config=MarketScanConfig(
            limit=2,
            archive_root=tmp_path / "raw",
            output_path=output_path,
            fetch_books=True,
        ),
        captured_at=captured_at,
    )

    assert client.book_calls == ["111", "222"]
    assert [candidate.token_id for candidate in candidates] == ["111", "222"]
    assert candidates[0].market_slug == "example-market"
    assert candidates[1].token_id == "222"
    assert candidates[0].raw_archive_path.endswith("20260613T123000Z-markets.json")

    raw_markets = tmp_path / "raw" / "gamma" / "20260613T123000Z-markets.json"
    raw_book = tmp_path / "raw" / "clob" / "20260613T123000Z-book-111.json"
    assert raw_markets.exists()
    assert raw_book.exists()

    written = json.loads(output_path.read_text())
    assert written[0]["condition_id"] == "0xabc"
    assert written[0]["token_id"] == "111"
    assert written[0]["market_slug"] == "example-market"
    assert written[0]["question"] == "Will the example resolve yes?"
    assert written[0]["raw_archive_path"].endswith("20260613T123000Z-markets.json")


def test_run_market_scan_fails_fast_when_primary_market_fetch_fails(tmp_path):
    class BrokenClient:
        def list_markets(self, *, active, closed, limit):
            raise RuntimeError("primary market fetch failed")

    try:
        run_market_scan(
            client=BrokenClient(),
            config=MarketScanConfig(
                limit=1,
                archive_root=tmp_path / "raw",
                output_path=tmp_path / "scores.json",
            ),
            captured_at=datetime(2026, 6, 13, tzinfo=UTC),
        )
    except RuntimeError as exc:
        assert str(exc) == "primary market fetch failed"
    else:
        raise AssertionError("expected primary market fetch failure to propagate")
