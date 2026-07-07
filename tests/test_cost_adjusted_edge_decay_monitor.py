from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.cost_adjusted_edge_decay_monitor")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_COST_ADJUSTED_EDGE_DECAY_MONITOR_CONFIG_VERSION,
        "stale_observation_count": 3,
        "decay_threshold": d("0.020000"),
        "stale_cost_adjusted_edge_threshold": d("0.010000"),
    }
    values.update(overrides)
    return module.CostAdjustedEdgeDecayMonitorConfig(**values)


def observation(edge_key: str, sequence: int, edge: str, **overrides: object):
    module = api()
    values = {
        "edge_key": edge_key,
        "observation_sequence": sequence,
        "observed_at": datetime(2026, 7, 2, 9, sequence, tzinfo=UTC),
        "cost_adjusted_edge": d(edge),
        "source_count": d("1"),
    }
    values.update(overrides)
    return module.CostAdjustedEdgeObservation(**values)


def report(*rows, cfg=None):
    module = api()
    return module.build_cost_adjusted_edge_decay_monitor_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_monitor_reduces_observations_into_edge_decay_rows_and_rollup() -> None:
    monitor_report = report(
        observation("alpha", 1, "0.080000"),
        observation("alpha", 2, "0.055000"),
        observation("alpha", 3, "0.040000"),
        observation("alpha", 4, "0.020000"),
        observation("beta", 1, "0.030000"),
        observation("beta", 2, "0.029000"),
        observation("gamma", 1, "0.009000"),
        observation("gamma", 2, "0.008000"),
        observation("gamma", 3, "0.007000"),
    )

    assert is_dataclass(monitor_report)
    assert monitor_report.generated_at == GENERATED_AT
    assert monitor_report.config_version == (
        "cost-adjusted-edge-decay-monitor-v0"
    )
    assert monitor_report.observation_count == d("9")
    assert monitor_report.edge_count == d("3")
    assert monitor_report.decayed_edge_count == d("1")
    assert monitor_report.stale_edge_count == d("1")
    assert monitor_report.watch_edge_count == d("2")
    assert monitor_report.pass_edge_count == d("1")
    assert monitor_report.status == "watch"
    assert monitor_report.reason_codes == (
        "cost_adjusted_edges_decayed",
        "stale_cost_adjusted_edges_present",
    )
    assert monitor_report.paper_only is True
    assert monitor_report.report_only is True
    assert monitor_report.readonly is True

    assert tuple(row.edge_key for row in monitor_report.edge_rows) == (
        "alpha",
        "gamma",
        "beta",
    )
    decayed = monitor_report.edge_rows[0]
    assert decayed.first_cost_adjusted_edge == d("0.080000")
    assert decayed.latest_cost_adjusted_edge == d("0.020000")
    assert decayed.peak_cost_adjusted_edge == d("0.080000")
    assert decayed.edge_delta == d("-0.060000")
    assert decayed.edge_decay == d("0.060000")
    assert decayed.observation_count == d("4")
    assert decayed.decay_status == "decayed"
    assert decayed.reason_codes == ("edge_decayed",)

    stale = monitor_report.edge_rows[1]
    assert stale.edge_key == "gamma"
    assert stale.latest_cost_adjusted_edge == d("0.007000")
    assert stale.edge_decay == d("0.002000")
    assert stale.decay_status == "stale"
    assert stale.reason_codes == ("edge_stale",)

    passed = monitor_report.edge_rows[2]
    assert passed.edge_key == "beta"
    assert passed.edge_delta == d("-0.001000")
    assert passed.decay_status == "pass"
    assert passed.reason_codes == ("edge_decay_clear",)


def test_empty_monitor_report_is_report_only_and_zero_counted() -> None:
    monitor_report = report()

    assert monitor_report.observation_count == d("0")
    assert monitor_report.edge_count == d("0")
    assert monitor_report.decayed_edge_count == d("0")
    assert monitor_report.stale_edge_count == d("0")
    assert monitor_report.watch_edge_count == d("0")
    assert monitor_report.pass_edge_count == d("0")
    assert monitor_report.status == "pass"
    assert monitor_report.reason_codes == ("cost_adjusted_edge_decay_clear",)
    assert monitor_report.edge_rows == ()


def test_monitor_payload_is_json_ready_redacted_and_no_float() -> None:
    monitor_report = report(
        observation("alpha", 1, "0.050000"),
        observation("alpha", 2, "0.010000"),
    )
    payload = api().cost_adjusted_edge_decay_monitor_payload(monitor_report)

    payload_text = repr(payload).lower()
    assert "market_slug" not in payload_text
    assert "question" not in payload_text
    assert "payload" not in payload_text
    assert "recommend" not in payload_text
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert payload["observation_count"] == "2"
    assert payload["edge_rows"][0]["edge_key"] == "alpha"
    assert payload["edge_rows"][0]["edge_decay"] == "0.040000"
    assert payload["derived_validation_digest"] == (
        monitor_report.derived_validation_digest
    )


def test_monitor_derived_validation_digest_is_deterministic_and_tamper_evident() -> None:
    observations = (
        observation("alpha", 1, "0.050000"),
        observation("alpha", 2, "0.030000"),
        observation("beta", 1, "0.020000"),
    )
    first = report(*observations)
    reordered = report(*tuple(reversed(observations)))

    assert first.derived_validation_digest == reordered.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in first.derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    object.__setattr__(first, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api().cost_adjusted_edge_decay_monitor_payload(first)


def test_monitor_rejects_invalid_inputs_and_duplicates() -> None:
    module = api()

    with pytest.raises(ValueError, match="observations must be a list or tuple"):
        module.build_cost_adjusted_edge_decay_monitor_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report(object())
    with pytest.raises(ValueError, match="config must be"):
        module.build_cost_adjusted_edge_decay_monitor_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_cost_adjusted_edge_decay_monitor_report(
            (),
            config=config(),
            generated_at=object(),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(
            observation("alpha", 1, "0.050000"),
            observation("alpha", 1, "0.040000"),
        )


def test_monitor_rejects_non_decimal_and_scalar_subclasses() -> None:
    module = api()

    with pytest.raises(ValueError, match="cost_adjusted_edge must be a Decimal"):
        observation("alpha", 1, "0.020000").__class__(
            edge_key="alpha",
            observation_sequence=1,
            observed_at=datetime(2026, 7, 2, 9, 1, tzinfo=UTC),
            cost_adjusted_edge=0.02,
            source_count=d("1"),
        )
    with pytest.raises(ValueError, match="cost_adjusted_edge"):
        observation("alpha", 1, "0.020000").__class__(
            edge_key="alpha",
            observation_sequence=1,
            observed_at=datetime(2026, 7, 2, 9, 1, tzinfo=UTC),
            cost_adjusted_edge=_DecimalSubclass("0.020000"),
            source_count=d("1"),
        )
    with pytest.raises(ValueError, match="edge_key"):
        observation(_StringSubclass("alpha"), 1, "0.020000")
    with pytest.raises(ValueError, match="generated_at"):
        module.build_cost_adjusted_edge_decay_monitor_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )


def test_monitor_dataclasses_are_frozen_and_revalidate_flags_and_counts() -> None:
    module = api()
    monitor_report = report(
        observation("alpha", 1, "0.050000"),
        observation("alpha", 2, "0.010000"),
    )

    with pytest.raises(FrozenInstanceError):
        monitor_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(monitor_report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(monitor_report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(monitor_report, readonly=False)
    with pytest.raises(ValueError, match="observation_count"):
        replace(monitor_report, observation_count=d("9"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(monitor_report, reason_codes=("cost_adjusted_edge_decay_clear",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(monitor_report.edge_rows[0], paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.CostAdjustedEdgeDecayMonitorConfig(
            config_version="cost-adjusted-edge-decay-monitor-v0",
            paper_only=False,
        )


def test_module_scope_has_no_live_mutation_advice_or_float_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/cost_adjusted_edge_decay_monitor.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "market_slug",
        "question",
        "payload_json",
        "investment_recommendation",
        "durable",
        "open(",
        "fast",
        "rank",
        "advice",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def test_module_exports_are_local_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_COST_ADJUSTED_EDGE_DECAY_MONITOR_CONFIG_VERSION",
        "CostAdjustedEdgeDecayMonitorConfig",
        "CostAdjustedEdgeObservation",
        "CostAdjustedEdgeDecayRow",
        "CostAdjustedEdgeDecayMonitorReport",
        "build_cost_adjusted_edge_decay_monitor_report",
        "cost_adjusted_edge_decay_monitor_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "cost_adjusted_edge_decay_monitor" not in getattr(root, "__all__", ())
