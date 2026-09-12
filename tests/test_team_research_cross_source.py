"""Real parsers and model loop with synthetic, independently shaped venue rows."""
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext
from hashlib import sha256
import json

import pytest

from polymarket_alpha_lab import team_research_cross_source as cross
from polymarket_alpha_lab.team_research_agent import run_team_research_agent
from polymarket_alpha_lab.team_research_agent_types import ResearchAgentLimits, ResearchModelReply, ResearchToolCall
from polymarket_alpha_lab.team_research_crypto_candles import CoinbaseCandleSnapshot, CryptoCandleWindow, EPOCH
from polymarket_alpha_lab.team_research_cross_source_pipeline import run_cross_source_crypto_research
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, evidence_content_sha256
from polymarket_alpha_lab.team_research_kraken_candles import (
    PAIRS, SHARED_GRANULARITIES, KrakenCandleSnapshot, kraken_reference,
)

NOW = datetime(2026, 9, 12, tzinfo=UTC)
CAPTURE = NOW + timedelta(seconds=10)


def window(product="ETH-USD", granularity=3600):
    return CryptoCandleWindow(product, NOW - timedelta(seconds=granularity * 2), NOW, granularity)


def kraken_row(stamp, close="100"):
    return [stamp, "100", "1000", "1", close, "100", "2", 3]


def fixtures(w=None):
    w = w or window()
    start = (w.start - EPOCH) // timedelta(seconds=1)
    stamps = [start + n * w.granularity_seconds for n in range(w.expected_count)]
    cb = CoinbaseCandleSnapshot(w, CAPTURE, json.dumps([[s, 1, 1000, 100, 100, 2] for s in stamps]).encode())
    payload = {"error": [], "result": {PAIRS[w.product_id][1]: [
        *(kraken_row(s) for s in stamps), kraken_row(stamps[-1] + w.granularity_seconds)],
        "last": stamps[-1]}}
    kr = KrakenCandleSnapshot(w, CAPTURE, json.dumps(payload).encode())
    return cb, kr


def alter(kr, mutate):
    p = json.loads(kr.raw_json)
    mutate(p, p["result"][PAIRS[kr.window.product_id][1]])
    return replace(kr, raw_json=json.dumps(p).encode())


def check(cb=None, kr=None, **kwargs):
    first, second = fixtures()
    args = dict(team_id="crypto_eth", condition_id="fixture", as_of=CAPTURE)
    args.update(kwargs)
    return cross.check_crypto_cross_source(first if cb is None else cb, second if kr is None else kr, **args)


def market(**kwargs):
    p = dict(slug="fixture-market", conditionId="fixture", question="Synthetic YES/NO event?",
             description="Synthetic rules, not a source-matching assertion.", active=True, closed=False,
             outcomes='["Yes","No"]', endDate="2026-09-13T00:00:00Z")
    p.update(kwargs)
    return GammaMarketSnapshot("fixture-market", CAPTURE, json.dumps(p).encode())


class Model:
    def __init__(self, finish_one=False):
        self.calls = 0
        self.messages = []
        self.ids = []
        self.finish_one = finish_one

    def complete(self, *, messages_json, max_output_tokens):
        self.calls += 1
        messages = json.loads(messages_json)
        self.messages.append(messages)
        if self.calls == 1:
            assert len(json.loads(messages[1]["content"])["required_source_ids"]) == 2
            calls = (ResearchToolCall("search", "search_evidence", '{"query":"*"}'),)
        elif self.calls == 2:
            self.ids = [item["source_id"] for item in json.loads(messages[-1]["content"])["sources"]]
            calls = tuple(ResearchToolCall(f"read-{n}", "read_evidence", json.dumps({"source_id": source}))
                          for n, source in enumerate(self.ids))
        else:
            args = dict(probability_yes="0.4", confidence="0.2", summary="Synthetic, uncalibrated result.",
                        source_ids=self.ids[:1] if self.finish_one else self.ids)
            calls = (ResearchToolCall("finish", "finish_research", json.dumps(args)),)
        return ResearchModelReply(calls, 10)


def run(cb=None, kr=None, **kwargs):
    first, second = fixtures()
    args = dict(task_id="t", team_id="crypto_eth", condition_id="fixture", as_of=CAPTURE,
                model_factory=lambda _: Model())
    args.update(kwargs)
    return run_cross_source_crypto_research(market(), first if cb is None else cb,
                                           second if kr is None else kr, **args)


@pytest.mark.parametrize("product,team", (("BTC-USD", "crypto_btc"), ("ETH-USD", "crypto_eth")))
@pytest.mark.parametrize("granularity", SHARED_GRANULARITIES)
def test_both_products_and_all_shared_intervals(product, team, granularity):
    cb, kr = fixtures(window(product, granularity))
    row = check(cb, kr, team_id=team)
    assert row.status == "matched"
    assert row.close_divergences_bps == (Decimal("0.000000"),) * 2
    assert len(row.evidence) == len(row.source_receipts) == 2
    assert row.kraken_excluded_count == 1
    assert [json.loads(item.text)["provider"] for item in row.evidence] == ["coinbase_exchange", "kraken"]
    for item, receipt in zip(row.evidence, row.source_receipts, strict=True):
        assert item.observed_at == NOW
        assert receipt.content_sha256 == evidence_content_sha256(item)
        assert item.paper_only is item.report_only is item.readonly is True
    assert row.coinbase_raw_sha256 == sha256(cb.raw_json).hexdigest()
    assert row.kraken_raw_sha256 == sha256(kr.raw_json).hexdigest()


@pytest.mark.parametrize("team,product", (("crypto_btc", "BTC-USD"), ("crypto_eth", "ETH-USD")))
def test_real_cross_source_intake_and_agent_cites_two_read_sources(team, product):
    cb, kr = fixtures(window(product))
    model = Model()
    row = run(cb, kr, team_id=team, model_factory=lambda _: model)
    assert row.check.status == "matched"
    assert row.market_run.intake.source_receipts == row.check.source_receipts
    result = row.market_run.research
    assert result.status == "completed"
    assert result.probability_yes == Decimal("0.4")
    assert result.tool_trace == ("search_evidence", "read_evidence", "read_evidence", "finish_research")
    assert set(result.source_ids) == set(model.ids)
    assert result.total_tokens == 30


def test_reading_both_but_citing_one_cannot_complete():
    result = run(model_factory=lambda _: Model(finish_one=True)).market_run.research
    assert result.reason_code == "invalid_citations"
    assert result.status == "blocked"
    assert result.source_ids == () and result.probability_yes is result.confidence is None
    assert result.summary == ""


@pytest.mark.parametrize("mutate,reason", (
    (lambda p,r: p.update(error=["SENSITIVE provider message"]), "kraken_api_error"),
    (lambda p,r: p.update(error=""), "invalid_kraken_payload"),
    (lambda p,r: p["result"].update(OTHER=[]), "kraken_pair_mismatch"),
    (lambda p,r: p["result"].update(last=True), "invalid_kraken_payload"),
    (lambda p,r: r.pop(0), "kraken_window_incomplete"),
    (lambda p,r: r.append(r[-1]), "duplicate_kraken_bucket"),
    (lambda p,r: r.reverse(), "invalid_kraken_payload"),
    (lambda p,r: r[0].append("extra"), "invalid_kraken_payload"),
    (lambda p,r: r[0].__setitem__(0, r[0][0] + 1), "invalid_kraken_payload"),
    (lambda p,r: r[0].__setitem__(0, True), "invalid_kraken_payload"),
    (lambda p,r: r[0].__setitem__(4, "1001"), "invalid_kraken_payload"),
    (lambda p,r: r[0].__setitem__(7, True), "invalid_kraken_payload"),
    (lambda p,r: r[0].__setitem__(slice(5,8), ["0", "0", 0]), "kraken_empty_bucket"),
    (lambda p,r: r[0].__setitem__(7, 0), "invalid_kraken_payload"),
    (lambda p,r: r[0].__setitem__(6, "0"), "invalid_kraken_payload"),
))
def test_bad_kraken_stops_before_model_factory(mutate, reason):
    cb, kr = fixtures()
    calls = []
    row = run(cb, alter(kr, mutate), model_factory=lambda _: calls.append(1))
    assert row.check.reason_code == "kraken:" + reason
    assert row.check.status == "blocked" and row.market_run is None
    assert row.check.evidence == row.check.source_receipts == ()
    assert calls == [] and "SENSITIVE" not in repr(row)


@pytest.mark.parametrize("value", (100, 100.0, True, None, "NaN", "Infinity", "1e2", "-1", " 100", "1_00", "1"*65, "0.0000000000001", "1000000000000000001"))
def test_kraken_decimal_wire_strings_are_strict(value):
    _, kr = fixtures()
    kr = alter(kr, lambda p,r: r[0].__setitem__(4, value))
    assert check(kr=kr).reason_code == "kraken:invalid_kraken_payload"


@pytest.mark.parametrize("raw", (b'{}', b'[]', b'null', b'not-json', b'\xff',
    b'{"error":[],"error":[]}', b'{"x":NaN}', b'{"x":1e999999999999999999999999}'))
def test_bad_json_is_redacted(raw):
    _, kr = fixtures()
    assert check(kr=replace(kr, raw_json=raw)).reason_code.startswith("kraken:")


def test_last_row_is_never_accepted_even_if_it_looks_closed():
    cb, kr = fixtures()
    kr = alter(kr, lambda p,r: r.pop())
    # The remaining final row is within our window, but uncommitted by protocol.
    row = check(cb, kr)
    assert row.reason_code == "kraken:kraken_window_incomplete"


def test_extra_closed_and_uncommitted_rows_excluded_from_evidence():
    cb, kr = fixtures()
    def mutate(p, rows):
        rows.insert(0, kraken_row(rows[0][0] - 3600, "999"))
        rows[-1][4] = "888"
    row = check(cb, alter(kr, mutate))
    assert row.status == "matched" and row.kraken_excluded_count == 2
    assert "999" not in row.evidence[1].text and "888" not in row.evidence[1].text
    assert len(json.loads(row.evidence[1].text)["candles"]) == 2


def test_same_venue_or_incorrect_runtime_type_rejected():
    cb, kr = fixtures()
    with pytest.raises(ValueError):
        check(cb, cb)
    with pytest.raises(ValueError):
        cross.check_crypto_cross_source(kr, cb, team_id="crypto_eth", condition_id="c", as_of=CAPTURE)


@pytest.mark.parametrize("change", ("product", "window", "granularity"))
def test_mismatched_windows_cannot_be_compared(change):
    cb, kr = fixtures()
    w = window("BTC-USD") if change == "product" else (
        replace(kr.window, start=kr.window.start - timedelta(hours=1)) if change == "window"
        else replace(kr.window, granularity_seconds=900))
    row = check(cb, replace(kr, window=w))
    assert row.reason_code == "source_window_mismatch"
    assert row.close_divergences_bps == ()


@pytest.mark.parametrize("delta,reason", ((1,"kraken_snapshot_from_future"),(-301,"kraken_snapshot_stale"),(-11,"kraken_window_unclosed")))
def test_kraken_capture_time_checks(delta, reason):
    cb, kr = fixtures()
    assert check(cb, replace(kr, fetched_at=CAPTURE+timedelta(seconds=delta))).reason_code == reason


def test_capture_skew_at_boundary_and_beyond():
    cb, kr = fixtures()
    as_of = CAPTURE + timedelta(seconds=61)
    assert check(cb, replace(kr, fetched_at=CAPTURE+timedelta(seconds=60)), as_of=as_of).status == "matched"
    assert check(cb, replace(kr, fetched_at=as_of), as_of=as_of).reason_code == "capture_skew_exceeded"


def test_old_window_not_revived_by_new_download():
    cb, kr = fixtures()
    future = CAPTURE + timedelta(days=2)
    result = check(replace(cb, fetched_at=future), replace(kr, fetched_at=future), as_of=future)
    assert result.reason_code == "coinbase:candle_window_stale"


def test_coinbase_missing_data_blocks_without_fallback():
    cb, kr = fixtures()
    cb = replace(cb, raw_json=b'[]')
    calls = []
    row = run(cb, kr, model_factory=lambda _: calls.append(1))
    assert row.check.reason_code == "coinbase:candle_window_incomplete"
    assert row.market_run is None and calls == []


def test_any_earlier_bucket_disagreement_blocks_even_when_latest_matches():
    cb, kr = fixtures()
    kr = alter(kr, lambda p,r: r[0].__setitem__(4, "110"))
    calls = []
    row = run(cb, kr, model_factory=lambda _: calls.append(1))
    assert row.check.reason_code == "close_price_divergence"
    assert row.check.close_divergences_bps[-1] == 0
    assert row.check.max_observed_divergence_bps > 100
    assert calls == [] and row.check.evidence == ()


@pytest.mark.parametrize("close,status", (("201","matched"),("201.000000000001","blocked"),("200.999999999999","matched")))
def test_exact_threshold_and_sub_display_precision_breach(close, status):
    cb, kr = fixtures()
    cb = replace(cb, raw_json=cb.raw_json.replace(b', 100, 2]', b', 199, 2]'))
    kr = alter(kr, lambda p,r: [row.__setitem__(4, close) for row in r])
    row = check(cb, kr)
    assert row.status == status
    if status == "blocked":
        assert row.max_observed_divergence_bps == Decimal("100.000001")


def test_symmetric_metric_and_ambient_decimal_context_independence():
    cb, kr = fixtures()
    kr = alter(kr, lambda p,r: r[0].__setitem__(4, "100.3"))
    normal = check(cb, kr)
    with localcontext() as ctx:
        ctx.prec = 2
        assert check(cb, kr) == normal
    assert cross._divergence(Decimal("199"),Decimal("201")) == cross._divergence(Decimal("201"),Decimal("199"))


@pytest.mark.parametrize("policy", ({"max_close_divergence_bps": 100}, {"max_close_divergence_bps": Decimal("NaN")},
    {"max_close_divergence_bps": Decimal("-1")}, {"max_close_divergence_bps": Decimal("10001")},
    {"max_close_divergence_bps": Decimal("0.0000001")}, {"max_capture_skew_seconds": True}, {"max_capture_skew_seconds": -1}))
def test_invalid_policy(policy):
    with pytest.raises(ValueError):
        cross.CrossSourcePolicy(**policy)


def test_zero_tolerance_and_metrics_cannot_be_forged():
    row = check(policy=cross.CrossSourcePolicy(Decimal("0")))
    assert row.status == "matched"
    for changes in ({"close_divergences_bps": (Decimal("1"),Decimal("0"))}, {"evidence": row.evidence[:1]},
                    {"source_receipts": row.source_receipts[::-1]}, {"kraken_raw_sha256": "0"*64},
                    {"readonly": False}, {"status": "ready"}, {"status": "blocked"}):
        with pytest.raises(ValueError):
            replace(row, **changes)
    with pytest.raises(FrozenInstanceError):
        row.status = "ready"


def test_gamma_rejection_stops_factory_after_matched_sources():
    cb, kr = fixtures()
    calls = []
    row = run_cross_source_crypto_research(market(closed=True), cb, kr, task_id="t", team_id="crypto_eth",
        condition_id="fixture", as_of=CAPTURE, model_factory=lambda _: calls.append(1))
    assert row.check.status == "matched"
    assert row.market_run.intake.reason_code == "market_not_open"
    assert row.market_run.research is None and calls == []


def test_factory_failure_is_redacted(capsys):
    def bad(_):
        raise RuntimeError("DO-NOT-LEAK")
    row = run(model_factory=bad)
    assert row.market_run.research.reason_code == "model_factory_failed"
    assert "DO-NOT-LEAK" not in repr(row)
    assert capsys.readouterr() == ("", "")


def test_run_binding_cannot_swap_sources_or_claim_one_source_completion():
    row = run()
    research = row.market_run.research
    with pytest.raises(ValueError):
        replace(row, market_run=replace(row.market_run, research=replace(research, source_ids=research.source_ids[:1])))
    with pytest.raises(ValueError):
        replace(row, check=replace(row.check, condition_id="other"))


@pytest.mark.parametrize("value", (["x"], ("missing",), (1,), ("x","x")))
def test_required_source_contract_rejects_before_model(value):
    row = run()
    class Forbidden:
        def complete(self, **kwargs):
            pytest.fail("must not call model")
    with pytest.raises(ValueError):
        run_team_research_agent(row.market_run.intake.task, model=Forbidden(), required_source_ids=value)


def test_unsupported_six_hour_interval_rejected():
    with pytest.raises(ValueError):
        KrakenCandleSnapshot(window(granularity=21600), CAPTURE, b'{}')


def test_reference_fixed_pair_minutes_and_since_overlap():
    cb, kr = fixtures()
    from urllib.parse import parse_qs, urlsplit
    parts = urlsplit(kraken_reference(kr.window))
    assert parts.netloc == "api.kraken.com" and parts.path == "/0/public/OHLC"
    assert parse_qs(parts.query) == {"pair":["ETHUSD"], "interval":["60"],
                                   "since":[str((kr.window.start-EPOCH)//timedelta(seconds=1)-3600)]}
