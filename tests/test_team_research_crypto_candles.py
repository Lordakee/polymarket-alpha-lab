"""Synthetic, no-network candle intake and actual research-loop integration."""
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, localcontext
from hashlib import sha256
import json

import pytest

from polymarket_alpha_lab import team_research_crypto_candles as c
from polymarket_alpha_lab.team_research_agent_types import ResearchAgentLimits, ResearchModelReply, ResearchToolCall
from polymarket_alpha_lab.team_research_crypto_pipeline import CryptoMarketResearchRun, run_crypto_research_from_snapshots
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, evidence_content_sha256

NOW = datetime(2026, 9, 12, 0, 0, tzinfo=UTC)
START = NOW - timedelta(hours=2)



def window(product="ETH-USD", **changes):
    return replace(c.CryptoCandleWindow(product, START, NOW), **changes)


def payload(w=None):
    w = w or window()
    start = (w.start - c.EPOCH) // timedelta(seconds=1)
    return [[start + n * w.granularity_seconds, 95, 110, 100, 105, 2] for n in range(w.expected_count)]


def snapshot(rows=None, **changes):
    return replace(c.CoinbaseCandleSnapshot(window(), NOW, json.dumps(payload() if rows is None else rows).encode()), **changes)


def prepare(s=None, **changes):
    args = dict(team_id="crypto_eth", condition_id="fixture", as_of=NOW)
    args.update(changes)
    return c.prepare_crypto_candle_evidence(snapshot() if s is None else s, **args)


def market(**changes):
    p = dict(slug="fixture-market", conditionId="fixture", question="Synthetic future event?",
             description="Synthetic rules; Coinbase is not necessarily the resolution oracle.",
             active=True, closed=False, outcomes='["Yes","No"]', endDate="2026-09-13T00:00:00Z")
    p.update(changes)
    return GammaMarketSnapshot("fixture-market", NOW, json.dumps(p).encode())


class Model:
    def __init__(self):
        self.messages = []

    def complete(self, *, messages_json, max_output_tokens):
        messages = json.loads(messages_json)
        self.messages.append(messages)
        step = len(self.messages)
        if step == 1:
            name, args = "search_evidence", {"query": "*"}
        elif step == 2:
            source = json.loads(messages[-1]["content"])["sources"][0]["source_id"]
            name, args = "read_evidence", {"source_id": source}
        else:
            source = json.loads(messages[-1]["content"])["source_id"]
            name, args = "finish_research", dict(probability_yes="0.4", confidence="0.2",
                                                summary="Synthetic, uncalibrated result.", source_ids=[source])
        return ResearchModelReply((ResearchToolCall(f"call-{step}", name, json.dumps(args)),), 5)


def run(s=None, **changes):
    args = dict(task_id="t", team_id="crypto_eth", condition_id="fixture", as_of=NOW,
                model_factory=lambda _: Model())
    args.update(changes)
    return run_crypto_research_from_snapshots(market(), snapshot() if s is None else s, **args)


@pytest.mark.parametrize(("team", "product"), tuple(c.PRODUCTS.items()))
def test_btc_eth_real_intake_to_agent_with_scripted_model(team, product):
    w = window(product)
    snap = snapshot(window=w)
    model = Model()
    result = run(snap, team_id=team, model_factory=lambda _: model)
    assert result.candles.status == "prepared"
    assert result.market_run.research.status == "completed"
    assert result.market_run.research.probability_yes == Decimal("0.4")
    assert result.market_run.intake.source_receipts == (result.candles.receipt,)
    assert result.market_run.research.source_ids == (result.candles.evidence.source_id,)
    assert result.market_run.research.tool_trace == ("search_evidence", "read_evidence", "finish_research")
    assert len(model.messages) == 3
    assert product in model.messages[2][-1]["content"]
    for value in (snap, result, result.candles, result.candles.evidence, result.candles.receipt, result.market_run.research):
        assert value.paper_only is value.report_only is value.readonly is True


def test_exact_six_column_order_decimal_precision_and_return():
    rows = payload()
    raw = ('[[%s,95.125,110.125,100.125,105.125,2.123456789012],'
           '[%s,96,112,102,110,0]]' % (rows[0][0], rows[1][0])).encode()
    result = prepare(snapshot(raw_json=raw))
    body = json.loads(result.evidence.text)
    assert body["columns"] == ["bucket_start_unix", "low", "high", "open", "close", "volume"]
    assert body["candles"][0] == [rows[0][0], "95.125", "110.125", "100.125", "105.125", "2.123456789012"]
    assert body["candles"][1][-1] == "0"
    assert body["window_return_fraction"] == "0.098627"
    assert body["price_currency"] == "USD" and body["volume_currency"] == "ETH"
    assert result.evidence.observed_at == NOW
    assert result.raw_content_sha256 == sha256(raw).hexdigest()
    assert result.receipt.content_sha256 == evidence_content_sha256(result.evidence)
    assert result.accepted_count == 2 and result.missing_count == 0


def test_outside_range_rows_are_excluded_not_cited_or_silently_used():
    rows = payload()
    outside = [[rows[0][0] - 3600, 1, 999, 1, 999, 1], [rows[-1][0] + 3600, 1, 999, 1, 999, 1]]
    result = prepare(snapshot([outside[1], rows[1], outside[0], rows[0]]))
    assert result.status == "prepared" and result.excluded_count == 2
    body = json.loads(result.evidence.text)
    assert [row[0] for row in body["candles"]] == [row[0] for row in rows]
    assert "999" not in json.dumps(body["candles"])
    assert result.evidence.source_id == result.receipt.source_id


@pytest.mark.parametrize("rows", ([], payload()[:1], payload()[1:]))
def test_missing_buckets_never_filled_and_stop_model(rows):
    calls = []
    result = run(snapshot(rows), model_factory=lambda _: calls.append(1))
    assert result.candles.reason_code == "candle_window_incomplete"
    assert result.candles.missing_count == 2 - len(rows)
    assert result.candles.evidence is result.candles.receipt is result.market_run is None
    assert calls == []


@pytest.mark.parametrize("outside", (False, True))
def test_duplicates_even_outside_range_fail_closed(outside):
    rows = payload()
    duplicate = list(rows[0])
    if outside:
        duplicate[0] -= 3600
    rows.extend((duplicate, duplicate))
    assert prepare(snapshot(rows)).reason_code == "duplicate_candle_bucket"


@pytest.mark.parametrize("raw", (b'{}', b'null', b'"x"', b'[[true,1,2,1,2,1]]', b'\xff', b'{"a":1,"a":2}',
    b'[[0,NaN,2,1,2,1]]', b'[[0,Infinity,2,1,2,1]]', b'[[0,1e9999999999999999999999,2,1,2,1]]',
    b'[[0,1e-9999999999999999999999,2,1,2,1]]', b'['*1100+b']'*1100))
def test_untrusted_json_errors_return_fixed_blocker(raw):
    assert prepare(snapshot(raw_json=raw)).reason_code == "invalid_candle_payload"


@pytest.mark.parametrize(("index", "value"), (
    (0, True), (0, -1), (0, 1), (0, 1.0), (0, "1789164000"), (0, 999999999999999999),
    (1, "95"), (1, False), (1, 0), (1, -1), (1, 111), (2, 99), (3, 200), (4, 1),
    (5, -1), (5, "1"), (5, True), (5, 1e30), (5, 1e-20),
))
def test_malformed_candle_values_block(index, value):
    rows = payload()
    rows[0][index] = value
    assert prepare(snapshot(rows)).reason_code == "invalid_candle_payload"


@pytest.mark.parametrize("rows", ([{}], [[0, 1]], [payload()[0] + [1]], payload() * 151))
def test_row_shape_and_response_count_limits(rows):
    assert prepare(snapshot(rows)).reason_code == "invalid_candle_payload"


@pytest.mark.parametrize(("fetched", "asof", "reason"), (
    (NOW + timedelta(microseconds=1), NOW, "candle_snapshot_from_future"),
    (NOW, NOW + timedelta(seconds=301), "candle_snapshot_stale"),
    (NOW - timedelta(microseconds=1), NOW, "candle_window_unclosed"),
))
def test_time_guards(fetched, asof, reason):
    assert prepare(snapshot(fetched_at=fetched), as_of=asof).reason_code == reason


def test_inclusive_freshness_limits_and_actual_bucket_end_time():
    assert prepare(as_of=NOW + timedelta(seconds=300)).status == "prepared"
    assert prepare(snapshot(fetched_at=NOW + timedelta(days=1)), as_of=NOW + timedelta(days=1)).status == "prepared"
    result = prepare(snapshot(fetched_at=NOW + timedelta(days=1, microseconds=1)), as_of=NOW + timedelta(days=1, microseconds=1))
    assert result.reason_code == "candle_window_stale"  # Fresh retrieval cannot revive old observations.
    calls = []
    assert run(as_of=NOW + timedelta(seconds=2), limits=ResearchAgentLimits(max_evidence_age_seconds=1),
               model_factory=lambda _: calls.append(1)).market_run is None
    assert calls == []


@pytest.mark.parametrize("granularity", c.GRANULARITIES)
def test_all_supported_granularities(granularity):
    w = c.CryptoCandleWindow("BTC-USD", NOW - timedelta(seconds=2 * granularity), NOW, granularity)
    result = prepare(snapshot(payload(w), window=w), team_id="crypto_btc")
    assert result.status == "prepared"


@pytest.mark.parametrize("changes", (
    {"product_id": "BTC-USDT"}, {"product_id": "../../private"}, {"product_id": True},
    {"start": NOW}, {"start": NOW + timedelta(hours=1)}, {"end": NOW + timedelta(seconds=1)},
    {"start": NOW - timedelta(hours=49)}, {"granularity_seconds": True}, {"granularity_seconds": 30},
    {"start": START.replace(tzinfo=None)}, {"end": NOW.replace(microsecond=1)},
    {"start": datetime(1969, 1, 1, tzinfo=UTC)},
))
def test_invalid_window_before_io(changes):
    with pytest.raises(ValueError):
        window(**changes)


@pytest.mark.parametrize("changes", ({"team_id": "politics"}, {"team_id": "crypto_btc"}, {"condition_id": ""},
    {"as_of": NOW.replace(tzinfo=None)}, {"max_snapshot_age_seconds": True}, {"max_evidence_age_seconds": -1}))
def test_scope_and_limit_contracts(changes):
    with pytest.raises(ValueError):
        prepare(**changes)


def test_timezone_equivalence_and_decimal_context_independence():
    offset = timezone(timedelta(hours=8))
    w = window(start=START.astimezone(offset), end=NOW.astimezone(offset))
    assert w == window() and w.source_reference == window().source_reference
    first = prepare()
    with localcontext() as ctx:
        ctx.prec = 4
        second = prepare(snapshot(window=w, fetched_at=NOW.astimezone(offset)))
    assert first == second


def test_raw_and_request_binding_changes_identity():
    first = prepare()
    second = prepare(snapshot(raw_json=json.dumps(payload(), indent=2).encode()))
    third = prepare(snapshot(fetched_at=NOW + timedelta(seconds=1)), as_of=NOW + timedelta(seconds=1))
    assert first.evidence.source_id != second.evidence.source_id != third.evidence.source_id
    assert first.receipt.content_sha256 != second.receipt.content_sha256


@pytest.mark.parametrize("flag", ("paper_only", "report_only", "readonly"))
def test_mutated_flags_are_revalidated(flag):
    snap = snapshot()
    object.__setattr__(snap, flag, False)
    with pytest.raises(ValueError):
        prepare(snap)


def test_bound_receipts_and_run_cannot_be_substituted():
    result = run()
    with pytest.raises(FrozenInstanceError):
        result.readonly = False
    for changes in ({"status": "ready"}, {"status": "blocked"}, {"accepted_count": 1},
                    {"receipt": replace(result.candles.receipt, content_sha256="0" * 64)},
                    {"evidence": replace(result.candles.evidence, observed_at=START)}):
        with pytest.raises(ValueError):
            replace(result.candles, **changes)
    with pytest.raises(ValueError):
        CryptoMarketResearchRun(prepare(snapshot([])), result.market_run)
    other = run(snapshot(raw_json=json.dumps(payload(), indent=2).encode()))
    with pytest.raises(ValueError):
        replace(result, market_run=other.market_run)


def test_closed_market_still_blocks_after_valid_candles():
    calls = []
    result = run_crypto_research_from_snapshots(market(closed=True), snapshot(), task_id="t",
        team_id="crypto_eth", condition_id="fixture", as_of=NOW, model_factory=lambda _: calls.append(1))
    assert result.candles.status == "prepared"
    assert result.market_run.intake.reason_code == "market_not_open"
    assert result.market_run.research is None and calls == []


def test_snapshot_contract_and_input_copies():
    for changes in ({"raw_json": b""}, {"raw_json": "[]"}, {"raw_json": b"x" * 131073}, {"window": object()}):
        with pytest.raises(ValueError):
            snapshot(**changes)
    snap = snapshot()
    def factory(_):
        object.__setattr__(snap.window, "product_id", "BTC-USD")
        object.__setattr__(snap, "raw_json", b"[]")
        return Model()
    result = run(snap, model_factory=factory)
    assert result.candles.window.product_id == "ETH-USD"
    assert result.market_run.research.status == "completed"


@pytest.mark.parametrize("team", ("crypto_btc", "crypto_eth"))
def test_demo_and_imports_with_network_guard(team):
    import os
    from pathlib import Path
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[1]
    program = """
import sys, runpy
from pathlib import Path

def guard(event, args):
    if event.startswith(('socket.', 'urllib.', 'subprocess.')):
        raise RuntimeError('forbidden demo I/O')
sys.addaudithook(guard)
sys.path.insert(0, str(Path('scripts').resolve()))
sys.argv = ['run_crypto_research_demo.py', '--team', sys.argv[1]]
runpy.run_path('scripts/run_crypto_research_demo.py', run_name='__main__')
"""
    env = dict(os.environ, PYTHONPATH=str(root / 'src'))
    result = subprocess.run([sys.executable, '-c', program, team], cwd=root, env=env,
                            capture_output=True, text=True, check=False, timeout=30)
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value['synthetic_demo'] is True
    assert value['public_network_called'] is value['live_model_called'] is False
    assert value['source_count'] == 1 and value['candle_count'] == 2
    assert value['research_status'] == 'completed'


def test_public_probe_default_has_no_network(monkeypatch, capsys):
    import runpy
    from pathlib import Path
    probe = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/probe_crypto_candles.py'))
    from polymarket_alpha_lab import team_research_coinbase as module
    def forbidden(*args, **kwargs):
        pytest.fail('default probe must not contact a provider')
    monkeypatch.setattr(module, 'build_opener', forbidden)
    assert probe['main']([]) == 0
    assert json.loads(capsys.readouterr().out)['public_fetch_enabled'] is False
