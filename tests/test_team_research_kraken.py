"""Public HTTP contract, no real network or provider credentials."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from email.message import Message
from io import BytesIO
from urllib.error import HTTPError

import pytest

from polymarket_alpha_lab import team_research_kraken as reader
from polymarket_alpha_lab.team_research_crypto_candles import CryptoCandleWindow
from polymarket_alpha_lab.team_research_kraken_candles import MAX_KRAKEN_BYTES, KrakenCandleSnapshot, kraken_reference


def window():
    return CryptoCandleWindow("BTC-USD", datetime(2026, 1, 1, tzinfo=UTC), datetime(2026, 1, 1, 1, tzinfo=UTC))


class Response:
    def __init__(self):
        self.url = kraken_reference(window())
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = "application/json; charset=utf-8"
        self.raw = b'{ "error": [] }\n'
        self.read_sizes = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def geturl(self):
        return self.url

    def read(self, size):
        self.read_sizes.append(size)
        return self.raw[:size]


def fake(monkeypatch, response):
    calls, handlers = [], []
    class Opener:
        def open(self, req, timeout):
            calls.append((req, timeout))
            if isinstance(response, Exception):
                raise response
            return response
    def build(*items):
        handlers.extend(items)
        return Opener()
    monkeypatch.setattr(reader, "build_opener", build)
    return calls, handlers


def test_fixed_uncredentialed_get_with_bounded_exact_body_and_actual_time(monkeypatch):
    response = Response()
    calls, handlers = fake(monkeypatch, response)
    before = datetime.now(UTC)
    snap = reader.KrakenCandleReader(True, 7).fetch(window())
    assert before <= snap.fetched_at <= datetime.now(UTC)
    req, timeout = calls[0]
    assert req.full_url == kraken_reference(window()) and req.get_method() == "GET"
    assert req.data is None and timeout == 7
    assert req.get_header("Authorization") is req.get_header("Cookie") is None
    assert snap.raw_json == response.raw and response.closed
    assert response.read_sizes == [MAX_KRAKEN_BYTES + 1]
    assert handlers[0].proxies == {}
    assert handlers[1].redirect_request(None,None,302,"redirect",{},"https://example.invalid") is None


def test_disabled_bad_window_and_unclosed_window_stop_before_opener(monkeypatch):
    def forbidden(*args):
        pytest.fail("no network")
    monkeypatch.setattr(reader, "build_opener", forbidden)
    with pytest.raises(ValueError, match="disabled"):
        reader.KrakenCandleReader().fetch(window())
    with pytest.raises(ValueError):
        reader.KrakenCandleReader(True).fetch("https://example.invalid")
    future = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    with pytest.raises(ValueError, match="not closed"):
        reader.KrakenCandleReader(True).fetch(replace(window(), start=future, end=future+timedelta(hours=1)))


@pytest.mark.parametrize("defect", ("origin", "status", "mime", "encoding", "empty", "oversize", "network"))
def test_failure_redaction_cleanup_and_no_retry(monkeypatch, defect):
    response = Response()
    if defect == "origin":
        response.url = "https://example.invalid/private"
    elif defect == "status":
        response.status = 429
    elif defect == "mime":
        response.headers.replace_header("Content-Type", "text/html")
    elif defect == "encoding":
        response.headers["Content-Encoding"] = "gzip"
    elif defect == "empty":
        response.raw = b""
    elif defect == "oversize":
        response.raw = b"x"*(MAX_KRAKEN_BYTES+1)
    elif defect == "network":
        response = RuntimeError("DO-NOT-LEAK")
    calls, _ = fake(monkeypatch, response)
    with pytest.raises(ValueError) as exc:
        reader.KrakenCandleReader(True).fetch(window())
    assert str(exc.value) == "kraken_public_fetch_failed"
    assert len(calls) == 1
    if defect != "network":
        assert response.closed
    if defect in ("origin", "status", "mime", "encoding"):
        assert response.read_sizes == []


def test_http_error_body_closed(monkeypatch):
    body = BytesIO(b"PRIVATE error body")
    error = HTTPError(kraken_reference(window()), 429, "PRIVATE", {}, body)
    fake(monkeypatch, error)
    with pytest.raises(ValueError, match="kraken_public_fetch_failed"):
        reader.KrakenCandleReader(True).fetch(window())
    assert body.closed


@pytest.mark.parametrize("kwargs", ({"allow_public_fetch":1},{"allow_public_fetch":"true"},
    {"timeout_seconds":0},{"timeout_seconds":True},{"timeout_seconds":61}))
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        reader.KrakenCandleReader(**kwargs)


@pytest.mark.parametrize("kwargs", ({"raw_json":b""},{"raw_json":"{}"},{"raw_json":b"x"*(MAX_KRAKEN_BYTES+1)},
    {"fetched_at":datetime(2026,1,1)}, {"readonly":False}))
def test_invalid_snapshot(kwargs):
    values = dict(window=window(), fetched_at=datetime(2026,1,1,tzinfo=UTC), raw_json=b'{}')
    values.update(kwargs)
    with pytest.raises(ValueError):
        KrakenCandleSnapshot(**values)
