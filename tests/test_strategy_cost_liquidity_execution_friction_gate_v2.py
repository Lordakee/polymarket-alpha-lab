from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 59, 30, tzinfo=UTC)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wal", "let")),
    "".join(("or", "der")),
    "".join(("net", "work")),
    "".join(("data", "base")),
    "".join(("per", "sist")),
    "".join(("sig", "ning")),
    "".join(("muta", "tion")),
    "".join(("b", "uy")),
    "".join(("se", "ll")),
    "".join(("tr", "ade")),
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_cost_liquidity_execution_friction_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-cost-liquidity-execution-friction-gate-v2",
        "min_cost_adjusted_edge": d("0.030000"),
        "max_total_execution_friction_drag": d("0.060000"),
        "max_spread_drag": d("0.040000"),
        "min_depth_coverage_ratio": d("1.500000"),
        "max_age_seconds": d("120.000000"),
    }
    values.update(overrides)
    return module.StrategyCostLiquidityExecutionFrictionGateV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "question": "Will alpha resolve yes?",
        "side": "yes",
        "observed_at": OBSERVED_AT,
        "gross_edge": d("0.120000"),
        "entry_probability": d("0.600000"),
        "fee_rate": d("0.020000"),
        "best_bid_probability": d("0.590000"),
        "best_ask_probability": d("0.610000"),
        "target_size_shares": d("100.000000"),
        "available_depth_shares": d("200.000000"),
        "expected_slippage_probability": d("0.005000"),
        "reason_codes": ("seed",),
    }
    values.update(overrides)
    return module.StrategyCostLiquidityExecutionFrictionGateV2Candidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_cost_liquidity_execution_friction_gate_v2_report(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def test_scores_fee_spread_depth_drag_and_cost_adjusted_edge() -> None:
    result = report(candidate(candidate_id="ready", market_slug="market-ready"))

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-cost-liquidity-execution-friction-gate-v2"
    assert result.candidate_count == d("1")
    assert result.ready_count == d("1")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.max_total_execution_friction_drag == d("0.037000")
    assert result.min_cost_adjusted_edge == d("0.083000")
    assert result.average_execution_friction_drag_score == d("0.037000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    row = result.rows[0]
    assert row.candidate_id == "ready"
    assert row.fee_drag == d("0.012000")
    assert row.spread_drag == d("0.020000")
    assert row.depth_coverage_ratio == d("2.000000")
    assert row.depth_drag == d("0.000000")
    assert row.expected_slippage_probability == d("0.005000")
    assert row.total_execution_friction_drag == d("0.037000")
    assert row.execution_friction_drag_score == d("0.037000")
    assert row.cost_adjusted_edge == d("0.083000")
    assert row.age_seconds == d("30.000000")
    assert row.gate_status == "ready"
    assert row.reason_codes == ("cost_adjusted_edge_ready", "seed")
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert len(row.derived_validation_digest) == 64


def test_blocks_poor_cost_adjusted_edge_and_execution_friction_thresholds() -> None:
    result = report(
        candidate(
            candidate_id="poor-edge",
            market_slug="market-poor-edge",
            gross_edge=d("0.025000"),
        ),
        candidate(
            candidate_id="thin-depth",
            market_slug="market-thin-depth",
            available_depth_shares=d("60.000000"),
        ),
        candidate(
            candidate_id="wide-spread",
            market_slug="market-wide-spread",
            best_bid_probability=d("0.560000"),
            best_ask_probability=d("0.630000"),
        ),
        candidate(
            candidate_id="stale",
            market_slug="market-stale",
            observed_at=datetime(2026, 7, 6, 11, 56, tzinfo=UTC),
        ),
    )

    assert result.ready_count == d("0")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("3")

    poor_edge = next(row for row in result.rows if row.candidate_id == "poor-edge")
    assert poor_edge.cost_adjusted_edge == d("-0.012000")
    assert poor_edge.gate_status == "blocked"
    assert "cost_adjusted_edge_not_positive" in poor_edge.reason_codes

    thin_depth = next(row for row in result.rows if row.candidate_id == "thin-depth")
    assert thin_depth.depth_coverage_ratio == d("0.600000")
    assert thin_depth.depth_drag == d("0.400000")
    assert thin_depth.gate_status == "blocked"
    assert "depth_coverage_below_minimum" in thin_depth.reason_codes

    wide_spread = next(row for row in result.rows if row.candidate_id == "wide-spread")
    assert wide_spread.spread_drag == d("0.070000")
    assert wide_spread.gate_status == "blocked"
    assert "spread_drag_above_limit" in wide_spread.reason_codes

    stale = next(row for row in result.rows if row.candidate_id == "stale")
    assert stale.age_seconds == d("240.000000")
    assert stale.gate_status == "watch"
    assert "candidate_stale" in stale.reason_codes


def test_payload_serializes_decimals_as_strings_and_exposes_hard_flags() -> None:
    payload = api().strategy_cost_liquidity_execution_friction_gate_v2_payload(
        report(candidate(candidate_id="payload")),
    )

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["max_total_execution_friction_drag"] == "0.037000"
    assert payload["min_cost_adjusted_edge"] == "0.083000"
    assert payload["rows"][0]["candidate_id"] == "payload"
    assert payload["rows"][0]["cost_adjusted_edge"] == "0.083000"
    assert payload["rows"][0]["age_seconds"] == "30.000000"
    assert payload["rows"][0]["derived_validation_digest"]
    assert payload["derived_validation_digest"]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert type(key) is str
                assert not any(fragment in key.lower() for fragment in FORBIDDEN_PUBLIC_FRAGMENTS)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        else:
            assert not isinstance(value, float)
            assert not isinstance(value, Decimal)
            assert type(value) is not int
            if isinstance(value, str):
                lowered_value = value.lower()
                assert not any(
                    fragment in lowered_value
                    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS
                )

    walk(payload)


def test_dataclasses_are_frozen_flags_are_hard_and_digest_tampering_is_rejected() -> None:
    result = report(candidate())
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.gate_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        config().min_cost_adjusted_edge = d("0.020000")

    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, gate_status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, ready_count=d("0"))


def test_unsafe_public_keys_values_and_invalid_decimal_surfaces_are_rejected() -> None:
    module = api()

    for field_name, bad_value in (
        ("candidate_id", "candidate-" + "".join(("wal", "let"))),
        ("market_slug", "market-" + "".join(("net", "work"))),
        ("question", "Will alpha " + "".join(("b", "uy")) + "?"),
        ("reason_codes", ("needs-" + "".join(("au", "th")),)),
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            candidate(**{field_name: bad_value})

    with pytest.raises(ValueError, match="unsafe public"):
        config(config_version="phase-" + "".join(("li", "ve")))
    with pytest.raises(ValueError, match="gross_edge"):
        candidate(gross_edge=_DecimalSubclass("0.120000"))
    with pytest.raises(ValueError, match="entry_probability"):
        candidate(entry_probability=0.6)
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(candidate_id=_StringSubclass("candidate-alpha"))
    with pytest.raises(ValueError, match="public_payload_key"):
        module._reject_unsafe_public_payload(
            {"safe": {"risk-" + "".join(("or", "der")): "ok"}},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module._reject_unsafe_public_payload(
            {"safe": "uses-" + "".join(("sig", "ning"))},
        )


def test_decimal_only_public_values_and_report_consistency_validation() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    result = report(
        candidate(observed_at=datetime(2026, 7, 6, 7, 59, 30, tzinfo=eastern)),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=eastern),
    )
    assert result.generated_at == GENERATED_AT
    assert result.rows[0].observed_at == OBSERVED_AT

    for instance in (config(), candidate(), result, result.rows[0]):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) in (bool, str, datetime, tuple) or value is None:
                continue
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_cost_liquidity_execution_friction_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_cost_liquidity_execution_friction_gate_v2_report(
            "not-candidates",
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidate values"):
        module.build_strategy_cost_liquidity_execution_friction_gate_v2_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 6, 11, 59, 30))
    with pytest.raises(ValueError, match="must not be after generated_at"):
        report(candidate(observed_at=datetime(2026, 7, 6, 12, 0, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="rows must be sorted"):
        module.StrategyCostLiquidityExecutionFrictionGateV2Report(
            generated_at=GENERATED_AT,
            config_version="strategy-cost-liquidity-execution-friction-gate-v2",
            candidate_count=d("2"),
            ready_count=d("1"),
            watch_count=d("1"),
            blocked_count=d("0"),
            max_total_execution_friction_drag=d("0.037000"),
            min_cost_adjusted_edge=d("0.027000"),
            average_execution_friction_drag_score=d("0.037000"),
            rows=(
                report(candidate(candidate_id="watch", gross_edge=d("0.064000"))).rows[0],
                report(candidate(candidate_id="ready")).rows[0],
            ),
        )


def test_module_scope_has_no_unsafe_surfaces() -> None:
    module = api()
    exported_names = set(module.__all__)
    assert exported_names == {
        "StrategyCostLiquidityExecutionFrictionGateV2Candidate",
        "StrategyCostLiquidityExecutionFrictionGateV2Config",
        "StrategyCostLiquidityExecutionFrictionGateV2Report",
        "StrategyCostLiquidityExecutionFrictionGateV2Row",
        "build_strategy_cost_liquidity_execution_friction_gate_v2_report",
        "strategy_cost_liquidity_execution_friction_gate_v2_payload",
    }
    for name in exported_names:
        lowered_name = name.lower()
        assert not any(fragment in lowered_name for fragment in FORBIDDEN_PUBLIC_FRAGMENTS)

    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "clob",
        "private_key",
        "secret",
        "account",
        "broker",
        "submit",
        "cancel",
        "open(",
        "Path(",
    ):
        assert forbidden not in lowered_source
    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment not in lowered_source

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
