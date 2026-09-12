"""Bounded public GET wire contract and intake integration using a fake opener."""
from datetime import UTC, datetime, timedelta
from email.message import Message
from io import BytesIO
import json
from urllib.error import HTTPError

import pytest

from polymarket_alpha_lab import team_research_gamma as gamma
from polymarket_alpha_lab.team_research_intake import (
    GAMMA_MARKET_PREFIX, MAX_GAMMA_RESPONSE_BYTES, prepare_team_research_from_gamma,
)
from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence


class Response:
    def __init__(self, raw=b'{}'):
        self.raw = raw
        self.status = 200
        self.url = GAMMA_MARKET_PREFIX + "fixture-market"
        self.headers = Message()
        self.headers["Content-Type"] = "application/json; charset=utf-8"
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
        def open(self, request, timeout):
            calls.append((request, timeout))
            if isinstance(response, Exception):
                raise response
            return response
    def build(*items):
        handlers.extend(items)
        return Opener()
    monkeypatch.setattr(gamma, "build_opener", build)
    return calls, handlers


def test_public_wire_keeps_exact_raw_bytes_and_uses_fixed_get_without_credentials(monkeypatch):
    raw = b'{ "slug" : "fixture-market", "unknown" : 0.125 }\n'
    response = Response(raw)
    calls, handlers = fake(monkeypatch, response)
    before = datetime.now(UTC)
    snap = gamma.GammaResearchReader(True, 7).fetch(market_slug="fixture-market")
    after = datetime.now(UTC)
    assert snap.raw_json == raw
    assert before <= snap.fetched_at <= after
    request, timeout = calls[0]
    assert timeout == 7 and request.full_url == response.url
    assert request.get_method() == "GET" and request.data is None
    assert request.get_header("Authorization") is None
    assert request.get_header("Cookie") is None
    assert response.read_sizes == [MAX_GAMMA_RESPONSE_BYTES + 1] and response.closed
    assert snap.source_reference == response.url
    assert handlers[0].proxies == {}
    assert handlers[1].redirect_request(None, None, 302, "redirect", {}, "https://example.invalid") is None


def test_disabled_fetch_and_bad_slug_stop_before_any_network(monkeypatch):
    def forbidden(*args):
        pytest.fail("must not create opener")
    monkeypatch.setattr(gamma, "build_opener", forbidden)
    with pytest.raises(ValueError, match="disabled"):
        gamma.GammaResearchReader().fetch(market_slug="fixture-market")
    for slug in ("../x", "x?token=value", "https://example.invalid", "x/y"):
        with pytest.raises(ValueError):
            gamma.GammaResearchReader(True).fetch(market_slug=slug)


@pytest.mark.parametrize("defect", ("origin", "status", "type", "oversize", "empty", "network"))
def test_failed_or_unbounded_response_redacted_and_not_retried(monkeypatch, defect):
    response = Response()
    if defect == "origin":
        response.url = "https://example.invalid/sensitive"
    elif defect == "status":
        response.status = 503
    elif defect == "type":
        response.headers.replace_header("Content-Type", "text/html")
    elif defect == "oversize":
        response.raw = b"x" * (MAX_GAMMA_RESPONSE_BYTES + 2)
    elif defect == "empty":
        response.raw = b""
    elif defect == "network":
        response = RuntimeError("synthetic-sensitive-error")
    calls, _ = fake(monkeypatch, response)
    with pytest.raises(ValueError) as error:
        gamma.GammaResearchReader(True).fetch(market_slug="fixture-market")
    assert str(error.value) == "gamma_public_fetch_failed"
    assert len(calls) == 1
    if defect in ("origin", "status", "type"):
        assert response.read_sizes == [] and response.closed


def test_http_error_response_is_closed(monkeypatch):
    body = BytesIO(b"synthetic-private-response")
    error = HTTPError(GAMMA_MARKET_PREFIX + "fixture-market", 429, "sensitive", {}, body)
    calls, _ = fake(monkeypatch, error)
    with pytest.raises(ValueError, match="gamma_public_fetch_failed"):
        gamma.GammaResearchReader(True).fetch(market_slug="fixture-market")
    assert body.closed and len(calls) == 1


@pytest.mark.parametrize("changes", ({"allow_public_fetch": 1}, {"allow_public_fetch": "true"},
                                    {"timeout_seconds": 0}, {"timeout_seconds": True}, {"timeout_seconds": 61}))
def test_invalid_reader_configuration(changes):
    with pytest.raises(ValueError):
        gamma.GammaResearchReader(**changes)


def test_malformed_json_is_retained_but_never_prepared(monkeypatch):
    calls, _ = fake(monkeypatch, Response(b'{"x":1,"x":2}'))
    snap = gamma.GammaResearchReader(True).fetch(market_slug="fixture-market")
    result = prepare_team_research_from_gamma(snap, task_id="t", team_id="crypto_eth",
        condition_id="c", as_of=snap.fetched_at, evidence=())
    assert result.reason_code == "invalid_market_payload"
    assert len(calls) == 1


def test_fake_public_response_to_real_intake(monkeypatch):
    now = datetime.now(UTC)
    payload = dict(slug="fixture-market", conditionId="c", question="Synthetic?",
                   description="Synthetic resolution criterion.", outcomes='["Yes","No"]',
                   active=True, closed=False, endDate=(now + timedelta(days=1)).isoformat())
    fake(monkeypatch, Response(json.dumps(payload).encode()))
    snap = gamma.GammaResearchReader(True).fetch(market_slug="fixture-market")
    source = ResearchEvidence("s", "crypto_eth", "c", "Synthetic title", "Synthetic observation",
                              "synthetic:source", now)
    result = prepare_team_research_from_gamma(snap, task_id="t", team_id="crypto_eth", condition_id="c",
                                            as_of=snap.fetched_at, evidence=(source,))
    assert result.status == "prepared"
    assert result.task.resolution_criteria == payload["description"]
    assert result.task.evidence == (source,)
