"""Real stdlib HTTP framing over in-memory wire bytes; no network or database."""
from datetime import UTC, datetime, timedelta
from http.client import HTTPResponse, IncompleteRead
from io import BytesIO

import pytest

from polymarket_alpha_lab import team_research_gamma as gamma


class Socket:
    def __init__(self, wire):
        self.wire = wire
    def makefile(self, *args):
        return BytesIO(self.wire)


def response(body=b'{}', headers=b'Content-Length: 2\r\n'):
    r = HTTPResponse(Socket(b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n' + headers + b'\r\n' + body))
    r.begin()
    r.url = 'https://gamma-api.polymarket.com/markets/slug/fixture-market'
    return r


def test_gamma_must_reject_valid_json_in_a_short_http_body(monkeypatch):
    r = response(b'{}', b'Content-Length: 20\r\n')
    class Opener:
        def open(self, *args, **kwargs):
            return r
    monkeypatch.setattr(gamma, 'build_opener', lambda *a: Opener())
    with pytest.raises(ValueError, match='gamma_public_fetch_failed'):
        gamma.GammaResearchReader(True).fetch(market_slug='fixture-market')
    assert r.isclosed()

from polymarket_alpha_lab.public_http import read_public_body, PublicBodyError


@pytest.mark.parametrize('body,headers', [
    (b'{}', b'Content-Length: 2\r\n'),
    (b'{}', b''),
    (b'2\r\n{}\r\n0\r\n\r\n', b'Transfer-Encoding: chunked\r\n'),
])
def test_real_http_complete_framing_preserves_exact_bytes(body, headers):
    with response(body, headers) as r:
        assert read_public_body(r, 100) == b'{}'


@pytest.mark.parametrize('body,headers,code', [
    (b'{}', b'Content-Length: 30\r\n', 'incomplete'),
    (b'{}', b'Content-Length: 999\r\n', 'too_large'),
    (b'{}', b'Content-Length: -1\r\n', 'framing_invalid'),
    (b'{}', b'Content-Length: x\r\n', 'framing_invalid'),
    (b'{}', b'Content-Length: 2\r\nContent-Length: 2\r\n', 'framing_invalid'),
    (b'{}', b'Content-Length: 2\r\nTransfer-Encoding: chunked\r\n', 'framing_invalid'),
    (b'{}', b'Transfer-Encoding: gzip\r\n', 'framing_invalid'),
    (b'{}', b'Content-Encoding: gzip\r\n', 'framing_invalid'),
    (b'{}', b'Content-Encoding: identity\r\nContent-Encoding: identity\r\n', 'framing_invalid'),
    (b'', b'Content-Length: 0\r\n', 'empty'),
    (b'x'*101, b'', 'too_large'),
])
def test_bounded_wire_errors(body, headers, code):
    with response(body, headers) as r:
        with pytest.raises(PublicBodyError, match='public_response_'+code):
            read_public_body(r, 100)


def test_real_chunked_truncation_never_returns_partial_json():
    with response(b'2\r\n{}\r\n', b'Transfer-Encoding: chunked\r\n') as r:
        with pytest.raises(IncompleteRead):
            read_public_body(r, 100)


@pytest.mark.parametrize('limit', [0, True, -1, 4194305, '100'])
def test_invalid_limits_before_any_read(limit):
    with pytest.raises(ValueError, match='limit_invalid'):
        read_public_body(None, limit)
