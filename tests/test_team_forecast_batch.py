"""Real ten-team smoke tests and deterministic parallel-batch contracts."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier, Event, Lock
from types import MappingProxyType

import pytest

from polymarket_alpha_lab import team_forecast_batch as batch
from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS


NOW = datetime(2026, 9, 12, 0, 0, tzinfo=UTC)


def request(team_id="crypto_eth", request_id="fixture-1"):
    config_type, evidence_type, _ = batch._TEAMS[team_id]
    item = evidence_type(
        source_id="fixture-source", source_type="supplied", evidence_text="Synthetic evidence",
        data_timestamp=NOW - timedelta(seconds=60), data_freshness_seconds=60,
        evidence_type="supplied_probability_delta", weight=Decimal("0.8"),
        probability_impact=Decimal("0.05"), reason_codes=("synthetic_fixture",),
    )
    return batch.TeamForecastBatchRequest(
        request_id=request_id, team_id=team_id, condition_id=f"condition-{request_id}",
        market_slug=f"market-{request_id}", question="Synthetic YES/NO question?",
        event_template="supplied_fixture", base_probability=Decimal("0.50"),
        config=config_type(config_version="batch-test-v0"), evidence=(item,), generated_at=NOW,
    )


def set_builder(monkeypatch, team_id, builder):
    registry = dict(batch._TEAMS)
    config_type, evidence_type, _ = registry[team_id]
    registry[team_id] = (config_type, evidence_type, builder)
    monkeypatch.setattr(batch, "_TEAMS", MappingProxyType(registry))


def test_registry_covers_current_taxonomy_and_is_readonly():
    assert batch.SUPPORTED_TEAM_IDS == TEAM_IDS
    with pytest.raises(TypeError):
        batch._TEAMS["fixture"] = ()


@pytest.mark.parametrize("team_id", TEAM_IDS)
def test_real_builder_for_every_team(team_id):
    item = request(team_id)
    result, = batch.run_team_forecast_batch((item,))
    assert result.status == "built"
    assert result.reason_code == "team_forecast_built"
    assert result.forecast.forecast_probability == Decimal("0.550000")
    assert result.forecast.team_id == team_id
    assert result.forecast.generated_at == NOW
    assert result.evidence[0].source_id == "fixture-source"
    for value in (result, result.forecast, *result.evidence):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
    encoded = json_ready_no_floats(result)
    assert encoded["forecast"]["forecast_probability"] == "0.550000"


def test_serial_and_parallel_ten_team_results_are_identical():
    items = tuple(request(team, f"fixture-{index}") for index, team in enumerate(TEAM_IDS))
    serial = batch.run_team_forecast_batch(items, max_workers=1)
    parallel = batch.run_team_forecast_batch(items, max_workers=3)
    assert serial == parallel
    assert tuple(row.request_id for row in parallel) == tuple(row.request_id for row in items)


def test_no_side_probability_reorientation():
    item = request()
    item = replace(item, evidence=(replace(item.evidence[0], probability_impact=Decimal("-0.1")),))
    outcome, = batch.run_team_forecast_batch((item,))
    assert outcome.status == "built"
    assert outcome.forecast.selected_side == "no"
    assert outcome.forecast.forecast_probability == Decimal("0.400000")


def test_workers_overlap_are_bounded_and_preserve_result_order(monkeypatch):
    original = batch._TEAMS["crypto_eth"][2]
    rendezvous = Barrier(2, timeout=10)
    lock = Lock()
    active = 0
    peak = 0
    threads = set()

    def concurrent_builder(**kwargs):
        nonlocal active, peak
        from threading import current_thread
        with lock:
            active += 1
            peak = max(peak, active)
            threads.add(current_thread().ident)
        try:
            rendezvous.wait()
            return original(**kwargs)
        finally:
            with lock:
                active -= 1

    set_builder(monkeypatch, "crypto_eth", concurrent_builder)
    items = tuple(request(request_id=f"fixture-{index}") for index in range(6))
    results = batch.run_team_forecast_batch(items, max_workers=2)
    assert all(row.status == "built" for row in results)
    assert peak == 2
    assert len(threads) == 2
    assert active == 0
    assert tuple(row.request_id for row in results) == tuple(row.request_id for row in items)


def test_faster_second_task_does_not_reorder_results(monkeypatch):
    original = batch._TEAMS["crypto_eth"][2]
    second_finished = Event()

    def out_of_order(**kwargs):
        if kwargs["condition_id"].endswith("first"):
            assert second_finished.wait(10)
        else:
            second_finished.set()
        return original(**kwargs)

    set_builder(monkeypatch, "crypto_eth", out_of_order)
    rows = batch.run_team_forecast_batch((request(request_id="first"), request(request_id="second")), max_workers=2)
    assert [row.request_id for row in rows] == ["first", "second"]
    assert all(row.status == "built" for row in rows)


def test_worker_failure_is_redacted_and_does_not_stop_other_teams(monkeypatch, capsys):
    def broken(**kwargs):
        raise RuntimeError("synthetic-do-not-log-credential")

    set_builder(monkeypatch, "crypto_eth", broken)
    rows = batch.run_team_forecast_batch((request(), request("macro_rates", "macro")), max_workers=2)
    assert rows[0].status == "failed"
    assert rows[0].forecast is None
    assert rows[0].evidence == ()
    assert rows[0].reason_code == "team_forecast_build_failed"
    assert rows[1].status == "built"
    assert "synthetic-do-not-log-credential" not in repr(rows)
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


@pytest.mark.parametrize("defect", ("team", "market", "condition", "time", "source", "count", "flags", "probability"))
def test_invalid_builder_output_is_suppressed(monkeypatch, defect):
    original = batch._TEAMS["crypto_eth"][2]

    def invalid(**kwargs):
        forecast, evidence = original(**kwargs)
        if defect == "team":
            forecast = replace(forecast, team_id="crypto_btc", category_id="finance.crypto.btc")
        elif defect == "market":
            forecast = replace(forecast, market_slug="different-market")
        elif defect == "condition":
            forecast = replace(forecast, condition_id="different-condition")
        elif defect == "time":
            forecast = replace(forecast, generated_at=NOW + timedelta(seconds=1))
        elif defect == "source":
            evidence = (replace(evidence[0], source_id="different-source"),)
        elif defect == "count":
            evidence = ()
        elif defect == "flags":
            object.__setattr__(forecast, "readonly", False)
        elif defect == "probability":
            object.__setattr__(forecast, "forecast_probability", Decimal("NaN"))
        return forecast, evidence

    set_builder(monkeypatch, "crypto_eth", invalid)
    result, = batch.run_team_forecast_batch((request(),))
    assert result.status == "failed"
    assert result.forecast is None
    assert result.evidence == ()


@pytest.mark.parametrize("max_workers", (0, -1, True, 1.5, "2", None))
def test_invalid_worker_limit(max_workers):
    with pytest.raises(ValueError, match="max_workers"):
        batch.run_team_forecast_batch((), max_workers=max_workers)


def test_empty_batch_does_not_create_executor(monkeypatch):
    def forbidden(**kwargs):
        pytest.fail("no executor for empty batch")
    monkeypatch.setattr(batch, "ThreadPoolExecutor", forbidden)
    assert batch.run_team_forecast_batch(()) == ()


def test_invalid_request_and_duplicate_ids_fail_before_any_builder(monkeypatch):
    calls = []
    set_builder(monkeypatch, "crypto_eth", lambda **kwargs: calls.append(kwargs))
    item = request()
    with pytest.raises(ValueError, match="request_id"):
        batch.run_team_forecast_batch((item, item), max_workers=2)
    invalid = request(request_id="invalid")
    object.__setattr__(invalid.config, "market_implied_probability_hint", Decimal("NaN"))
    with pytest.raises(ValueError, match="invalid supplied-input"):
        batch.run_team_forecast_batch((item, invalid), max_workers=2)
    assert calls == []


@pytest.mark.parametrize("field", ("paper_only", "report_only", "readonly"))
def test_hard_flags_rechecked_before_workers(field):
    item = request()
    object.__setattr__(item, field, False)
    with pytest.raises(ValueError):
        batch.run_team_forecast_batch((item,))


@pytest.mark.parametrize("change", (
    {"team_id": "unknown"}, {"request_id": " "}, {"base_probability": 0.5},
    {"base_probability": Decimal("NaN")}, {"base_probability": Decimal("1.1")},
    {"generated_at": NOW.replace(tzinfo=None)}, {"evidence": ()}, {"evidence": []},
))
def test_invalid_request_construction(change):
    with pytest.raises(ValueError):
        replace(request(), **change)


def test_cross_team_evidence_config_and_duplicate_sources_rejected():
    eth = request()
    btc = request("crypto_btc", "btc")
    with pytest.raises(ValueError, match="config"):
        replace(eth, config=btc.config)
    with pytest.raises(ValueError, match="evidence"):
        replace(eth, evidence=btc.evidence)
    with pytest.raises(ValueError, match="source_id"):
        replace(eth, evidence=eth.evidence * 2)


def test_inputs_are_snapshotted_without_mutating_caller(monkeypatch):
    item = request()
    original = batch._TEAMS["crypto_eth"][2]
    observed = []
    def inspecting(**kwargs):
        observed.append(kwargs)
        return original(**kwargs)
    set_builder(monkeypatch, "crypto_eth", inspecting)
    outcome, = batch.run_team_forecast_batch((item,))
    assert outcome.status == "built"
    assert observed[0]["config"] == item.config
    assert observed[0]["config"] is not item.config
    assert observed[0]["evidence"][0] is not item.evidence[0]
    with pytest.raises(FrozenInstanceError):
        outcome.status = "ready"


def test_container_and_subclass_contract():
    with pytest.raises(ValueError, match="tuple"):
        batch.run_team_forecast_batch([request()])
    with pytest.raises(ValueError, match="exact"):
        batch.run_team_forecast_batch((object(),))


def test_outcome_cannot_claim_failed_with_packets_or_ready():
    outcome, = batch.run_team_forecast_batch((request(),))
    with pytest.raises(ValueError):
        replace(outcome, status="failed")
    with pytest.raises(ValueError):
        replace(outcome, status="ready")
    with pytest.raises(ValueError):
        replace(outcome, paper_only=False)
