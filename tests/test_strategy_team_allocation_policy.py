from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_allocation_policy.py"
)
GENERATED_AT = datetime(2026, 7, 6, 9, 30, tzinfo=timezone(timedelta(hours=-4)))
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_allocation_policy",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-team-allocation-policy-test-v0",
        "base_paper_notional_cap": d("1000.000000"),
        "edge_full_score": d("0.100000"),
        "min_allocation_score": d("0.250000"),
        "strong_team_memory_score": d("0.750000"),
        "strong_source_quality": d("0.700000"),
    }
    values.update(overrides)
    return module.StrategyTeamAllocationPolicyConfig(**values)


def team(**overrides: object):
    module = api()
    values = {
        "team_id": "macro_team",
        "category": "rates",
        "team_memory_score": d("0.900000"),
        "category_capacity": d("1000.000000"),
        "current_exposure": d("100.000000"),
        "source_quality": d("0.800000"),
        "cost_adjusted_edge": d("0.120000"),
        "reason_codes": ("team_allocation_input",),
    }
    values.update(overrides)
    return module.StrategyTeamAllocationPolicyTeam(**values)


def allocate(*, teams=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.allocate_strategy_team_allocation_policy(
        teams,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_allocates_paper_notional_caps_from_team_signals_and_capacity() -> None:
    result = allocate(
        teams=(
            team(
                team_id="macro_team",
                category="rates",
                team_memory_score=d("0.900000"),
                category_capacity=d("1000.000000"),
                current_exposure=d("100.000000"),
                source_quality=d("0.800000"),
                cost_adjusted_edge=d("0.120000"),
            ),
            team(
                team_id="policy_team",
                category="elections",
                team_memory_score=d("0.500000"),
                category_capacity=d("500.000000"),
                current_exposure=d("100.000000"),
                source_quality=d("0.600000"),
                cost_adjusted_edge=d("0.040000"),
            ),
            team(
                team_id="sports_team",
                category="soccer",
                team_memory_score=d("0.300000"),
                category_capacity=d("300.000000"),
                current_exposure=d("300.000000"),
                source_quality=d("0.900000"),
                cost_adjusted_edge=d("0.100000"),
            ),
        ),
    )

    assert result.generated_at == datetime(2026, 7, 6, 13, 30, tzinfo=UTC)
    assert result.config_version == "strategy-team-allocation-policy-test-v0"
    assert result.team_count == d("3")
    assert result.allocated_team_count == d("2")
    assert result.watch_team_count == ZERO
    assert result.blocked_team_count == d("1")
    assert result.total_available_capacity == d("1300.000000")
    assert result.total_paper_notional_cap == d("1300.000000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "team_allocation_selected",
        "team_allocation_blocked",
        "notional_cap_limited_by_capacity",
        "category_capacity_exhausted",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.team_id for row in result.rows) == (
        "macro_team",
        "policy_team",
        "sports_team",
    )
    assert tuple(row.allocation_status for row in result.rows) == (
        "allocate",
        "allocate",
        "blocked",
    )

    macro, policy, sports = result.rows
    assert macro.available_capacity == d("900.000000")
    assert macro.capacity_headroom_ratio == d("0.900000")
    assert macro.allocation_score == d("0.900000")
    assert macro.paper_notional_cap == d("900.000000")
    assert macro.reason_codes == (
        "team_allocation_input",
        "team_allocation_selected",
        "team_memory_strong",
        "source_quality_strong",
        "cost_adjusted_edge_positive",
        "category_capacity_available",
    )

    assert policy.available_capacity == d("400.000000")
    assert policy.capacity_headroom_ratio == d("0.800000")
    assert policy.allocation_score == d("0.530000")
    assert policy.paper_notional_cap == d("400.000000")
    assert policy.reason_codes == (
        "team_allocation_input",
        "team_allocation_selected",
        "team_memory_watch",
        "source_quality_watch",
        "cost_adjusted_edge_positive",
        "category_capacity_available",
        "notional_cap_limited_by_capacity",
    )

    assert sports.available_capacity == ZERO
    assert sports.capacity_headroom_ratio == ZERO
    assert sports.allocation_score == d("0.595000")
    assert sports.paper_notional_cap == ZERO
    assert sports.reason_codes == (
        "team_allocation_input",
        "team_allocation_blocked",
        "team_memory_watch",
        "source_quality_strong",
        "cost_adjusted_edge_positive",
        "category_capacity_exhausted",
    )


def test_low_score_or_nonpositive_edge_keeps_team_on_watch_with_zero_cap() -> None:
    result = allocate(
        teams=(
            team(
                team_id="crypto_team",
                category="crypto",
                team_memory_score=d("0.200000"),
                category_capacity=d("1000.000000"),
                current_exposure=d("100.000000"),
                source_quality=d("0.300000"),
                cost_adjusted_edge=d("-0.010000"),
            ),
        ),
    )

    assert result.status == "watch"
    assert result.allocated_team_count == ZERO
    assert result.watch_team_count == d("1")
    assert result.blocked_team_count == ZERO
    assert result.total_paper_notional_cap == ZERO

    row = result.rows[0]
    assert row.allocation_status == "watch"
    assert row.allocation_score == d("0.245000")
    assert row.paper_notional_cap == ZERO
    assert row.reason_codes == (
        "team_allocation_input",
        "team_allocation_watch",
        "team_memory_watch",
        "source_quality_watch",
        "cost_adjusted_edge_nonpositive",
        "category_capacity_available",
        "allocation_score_below_minimum",
    )


def test_empty_policy_report_is_zeroed_paper_only_and_readonly() -> None:
    empty = allocate()

    assert empty.generated_at == datetime(2026, 7, 6, 13, 30, tzinfo=UTC)
    assert empty.team_count == ZERO
    assert empty.allocated_team_count == ZERO
    assert empty.watch_team_count == ZERO
    assert empty.blocked_team_count == ZERO
    assert empty.total_available_capacity == ZERO
    assert empty.total_paper_notional_cap == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("team_allocation_no_inputs",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_policy_dataclasses_are_frozen_and_flags_cannot_be_downgraded() -> None:
    module = api()
    cfg = config()
    sample_team = team()
    result = allocate(teams=(sample_team,), cfg=cfg)
    row = result.rows[0]

    for item in (cfg, sample_team, row, result):
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert getattr(item, field.name) is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(sample_team, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyTeamAllocationPolicyReport(
            generated_at=GENERATED_AT,
            config_version="strategy-team-allocation-policy-test-v0",
            team_count=ZERO,
            allocated_team_count=ZERO,
            watch_team_count=ZERO,
            blocked_team_count=ZERO,
            total_available_capacity=ZERO,
            total_paper_notional_cap=ZERO,
            status="watch",
            reason_codes=("team_allocation_no_inputs",),
            rows=(),
            paper_only=False,
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("team_memory_score", 1),
        ("category_capacity", 1000),
        ("current_exposure", 0.1),
        ("source_quality", _DecimalSubclass("0.800000")),
        ("cost_adjusted_edge", 0),
    ),
)
def test_team_inputs_reject_non_decimal_numeric_values(
    field_name: str,
    bad_value: object,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be exactly Decimal"):
        team(**{field_name: bad_value})


def test_policy_rejects_invalid_capacity_and_probability_ranges() -> None:
    with pytest.raises(ValueError, match="current_exposure must not exceed category_capacity"):
        team(category_capacity=d("100.000000"), current_exposure=d("101.000000"))
    with pytest.raises(ValueError, match="team_memory_score must be <= 1.000000"):
        team(team_memory_score=d("1.000001"))
    with pytest.raises(ValueError, match="source_quality must be >= 0.000000"):
        team(source_quality=d("-0.000001"))
    with pytest.raises(ValueError, match="edge_full_score must be positive"):
        config(edge_full_score=ZERO)


def test_policy_payload_is_json_ready_without_float_values() -> None:
    module = api()
    result = allocate(teams=(team(),))

    payload = module.strategy_team_allocation_policy_payload(result)

    assert payload["generated_at"] == "2026-07-06T13:30:00+00:00"
    assert payload["team_count"] == "1.000000"
    assert payload["total_paper_notional_cap"] == "900.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_notional_cap"] == "900.000000"
    assert_no_float_values(payload)


def test_module_has_no_unsafe_execution_surface_or_float_constants() -> None:
    source = MODULE_PATH.read_text()
    lowered = source.lower()
    forbidden_fragments = (
        "api_key",
        "private_key",
        "wallet",
        "signing",
        "submit_order",
        "cancel_order",
        "replace_order",
        "clob_client",
        "live_trading",
    )
    assert not any(fragment in lowered for fragment in forbidden_fragments)

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
