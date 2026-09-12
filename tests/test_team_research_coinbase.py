"""No-network public Coinbase reader contracts, with real candle intake."""
from datetime import UTC, datetime, timedelta
from email.message import Message
from io import BytesIO
import json
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

from polymarket_alpha_lab import team_research_coinbase as reader
from polymarket_alpha_lab.team_research_crypto_candles import (
    MAX_CANDLE_BYTES, CryptoCandleWindow, prepare_crypto_candle_evidence,
)

END = datetime(2020, 1, 2, tzinfo=UTC)
WINDOW = CryptoCandleWindow("BTC-USD", END - timedelta(hours=1), END)


class Response:
    status = 200
    def __init__(self, raw=b'[]'):
        self.raw, self.url = raw, WINDOW.source_reference
        self.headers = Message()
        self.headers["Content-Type"] = "application/json; charset=utf-8"
        self.sizes, self.closed = [], False
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.closed = True
    def geturl(self):
        return self.url
    def read(self, size):
        self.sizes.append(size)
        return self.raw[:size]


def fake(monkeypatch, response):
    calls, handlers = [], []
    class Opener:
        def open(self, request, timeout):
            calls.append((request, timeout))
            if isinstance(response, Exception):
                raise response
            return response
    def build(*values):
        handlers.extend(values)
        return Opener()
    monkeypatch.setattr(reader, "build_opener", build)
    return calls, handlers


def test_single_public_request_fixed_product_and_times_without_credentials(monkeypatch):
    response = Response(b' [ [1577919600, 1, 2, 1, 2, 3] ]\n')
    calls, handlers = fake(monkeypatch, response)
    before = datetime.now(UTC)
    snap = reader.CoinbaseCandleReader(True, 7).fetch(WINDOW)
    assert before <= snap.fetched_at <= datetime.now(UTC)
    assert snap.raw_json == response.raw and snap.window == WINDOW and snap.window is not WINDOW
    request, timeout = calls[0]
    assert len(calls) == 1 and timeout == 7
    assert request.full_url == WINDOW.source_reference and request.get_method() == "GET"
    assert request.data is None and request.get_header("Authorization") is None and request.get_header("Cookie") is None
    assert parse_qs(urlsplit(request.full_url).query) == {
        "start": [WINDOW.start.isoformat()], "end": [WINDOW.end.isoformat()], "granularity": ["3600"]}
    assert handlers[0].proxies == {}
    assert handlers[1].redirect_request(None, None, 302, "redirect", {}, "https://example.invalid") is None
    assert response.sizes == [MAX_CANDLE_BYTES + 1] and response.closed
    # Historical response fetched now is not valid historical as-of evidence.
    assert prepare_crypto_candle_evidence(snap, team_id="crypto_btc", condition_id="c", as_of=END).reason_code == "candle_snapshot_from_future"


@pytest.mark.parametrize("enabled", (False, True))
def test_disabled_or_unclosed_window_cannot_open_network(monkeypatch, enabled):
    def forbidden(*args):
        pytest.fail("no opener expected")
    monkeypatch.setattr(reader, "build_opener", forbidden)
    end = datetime(2099, 1, 2, tzinfo=UTC)
    w = CryptoCandleWindow("ETH-USD", end - timedelta(hours=1), end)
    with pytest.raises(ValueError):
        reader.CoinbaseCandleReader(enabled).fetch(w)


@pytest.mark.parametrize("defect", ("origin", "status", "mime", "encoding", "empty", "oversize", "network"))
def test_reader_failures_redacted_closed_and_not_retried(monkeypatch, defect):
    response = Response()
    if defect == "origin": response.url = "https://example.invalid/private"
    elif defect == "status": response.status = 503
    elif defect == "mime": response.headers.replace_header("Content-Type", "text/html")
    elif defect == "encoding": response.headers["Content-Encoding"] = "gzip"
    elif defect == "empty": response.raw = b""
    elif defect == "oversize": response.raw = b"x" * (MAX_CANDLE_BYTES + 1)
    elif defect == "network": response = RuntimeError("synthetic-sensitive-error")
    calls, _ = fake(monkeypatch, response)
    with pytest.raises(ValueError) as error:
        reader.CoinbaseCandleReader(True).fetch(WINDOW)
    assert str(error.value) == "coinbase_public_fetch_failed" and len(calls) == 1
    assert error.value.__suppress_context__ is True
    if defect != "network": assert response.closed
    if defect in ("origin", "status", "mime", "encoding"): assert response.sizes == []


def test_http_error_body_is_closed(monkeypatch):
    body = BytesIO(b"synthetic-sensitive-error")
    error = HTTPError(WINDOW.source_reference, 429, "fixture", {}, body)
    calls, _ = fake(monkeypatch, error)
    with pytest.raises(ValueError, match="coinbase_public_fetch_failed"):
        reader.CoinbaseCandleReader(True).fetch(WINDOW)
    assert body.closed and len(calls) == 1


@pytest.mark.parametrize("changes", ({"allow_public_fetch": 1}, {"timeout_seconds": True}, {"timeout_seconds": 0}, {"timeout_seconds": 61}))
def test_reader_configuration_validation(changes):
    with pytest.raises(ValueError):
        reader.CoinbaseCandleReader(**changes)


def test_live_shaped_response_through_real_intake(monkeypatch):
    now = datetime.now(UTC)
    end = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    w = CryptoCandleWindow("BTC-USD", end - timedelta(hours=1), end)
    stamp = (w.start - datetime(1970, 1, 1, tzinfo=UTC)) // timedelta(seconds=1)
    response = Response(json.dumps([[stamp, 100, 110, 101, 109, 2.5]]).encode())
    response.url = w.source_reference
    fake(monkeypatch, response)
    snap = reader.CoinbaseCandleReader(True).fetch(w)
    result = prepare_crypto_candle_evidence(snap, team_id="crypto_btc", condition_id="fixture", as_of=snap.fetched_at)
    assert result.status == "prepared" and result.evidence.observed_at == end
