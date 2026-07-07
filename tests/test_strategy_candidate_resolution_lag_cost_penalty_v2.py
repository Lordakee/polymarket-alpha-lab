from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_resolution_lag_cost_penalty_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_resolution_lag_cost_penalty_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-candidate-resolution-lag-cost-penalty-v2-phase1",
        "resolution_delay_penalty_per_day": d("0.001000"),
        "capital_lockup_apr": d("0.120000"),
        "stale_evidence_penalty_per_day": d("0.002000"),
        "settlement_ambiguity_penalty_weight": d("0.050000"),
        "exit_friction_penalty_weight": d("1.000000"),
        "watch_net_probability_edge": d("0.020000"),
        "max_pass_penalty_to_edge_ratio": d("0.500000"),
        "max_watch_penalty_to_edge_ratio": d("0.800000"),
    }
    values.update(overrides)
    return module.StrategyCandidateResolutionLagCostPenaltyV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "alpha-market",
        "observed_at": OBSERVED_AT,
        "expected_probability_edge": d("0.100000"),
        "entry_probability": d("0.400000"),
        "resolution_delay_hours": d("24.000000"),
        "capital_lockup_days": d("2.000000"),
        "stale_evidence_hours": d("12.000000"),
        "settlement_ambiguity_score": d("0.100000"),
        "exit_friction_score": d("0.010000"),
        "reason_codes": ("candidate_positive_edge",),
    }
    values.update(overrides)
    return module.StrategyCandidateResolutionLagCostPenaltyV2Candidate(**values)


def report(*, candidates=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_candidate_resolution_lag_cost_penalty_v2(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_penalty_model_scores_candidates_and_orders_by_eroded_edge() -> None:
    result = report(
        candidates=(
            candidate(
                candidate_id="pass-alpha",
                market_slug="gamma-pass",
                expected_probability_edge=d("0.100000"),
                entry_probability=d("0.400000"),
                resolution_delay_hours=d("24.000000"),
                capital_lockup_days=d("2.000000"),
                stale_evidence_hours=d("12.000000"),
                settlement_ambiguity_score=d("0.100000"),
                exit_friction_score=d("0.010000"),
            ),
            candidate(
                candidate_id="watch-alpha",
                market_slug="beta-watch",
                expected_probability_edge=d("0.070000"),
                entry_probability=d("0.600000"),
                resolution_delay_hours=d("96.000000"),
                capital_lockup_days=d("10.000000"),
                stale_evidence_hours=d("48.000000"),
                settlement_ambiguity_score=d("0.200000"),
                exit_friction_score=d("0.020000"),
            ),
            candidate(
                candidate_id="blocked-alpha",
                market_slug="alpha-blocked",
                expected_probability_edge=d("0.050000"),
                entry_probability=d("0.800000"),
                resolution_delay_hours=d("240.000000"),
                capital_lockup_days=d("20.000000"),
                stale_evidence_hours=d("72.000000"),
                settlement_ambiguity_score=d("0.400000"),
                exit_friction_score=d("0.020000"),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-candidate-resolution-lag-cost-penalty-v2-phase1"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.total_lag_probability_penalty == d("0.118496")
    assert result.max_total_lag_probability_penalty == d("0.061260")
    assert result.min_penalty_adjusted_probability_edge == d("-0.011260")
    assert result.max_penalty_to_edge_ratio == d("1.225200")
    assert result.max_edge_shortfall == d("0.011260")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "resolution_lag_cost_penalty_blocked",
        "resolution_lag_cost_penalty_passed",
        "resolution_lag_cost_penalty_watch",
        "resolution_delay_penalty_present",
        "capital_lockup_penalty_present",
        "stale_evidence_penalty_present",
        "settlement_ambiguity_penalty_present",
        "exit_friction_penalty_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.penalty_status for row in result.rows) == (
        "blocked",
        "watch",
        "pass",
    )
    blocked, watched, passed = result.rows

    assert blocked.candidate_id == "blocked-alpha"
    assert blocked.resolution_delay_probability_cost == d("0.010000")
    assert blocked.capital_lockup_probability_cost == d("0.005260")
    assert blocked.stale_evidence_probability_cost == d("0.006000")
    assert blocked.settlement_ambiguity_probability_cost == d("0.020000")
    assert blocked.exit_friction_probability_cost == d("0.020000")
    assert blocked.total_lag_probability_penalty == d("0.061260")
    assert blocked.penalty_adjusted_probability_edge == d("-0.011260")
    assert blocked.penalty_to_edge_ratio == d("1.225200")
    assert blocked.edge_shortfall == d("0.011260")
    assert blocked.reason_codes == (
        "candidate_positive_edge",
        "resolution_lag_cost_penalty_blocked",
        "resolution_delay_penalty_present",
        "capital_lockup_penalty_present",
        "stale_evidence_penalty_present",
        "settlement_ambiguity_penalty_present",
        "exit_friction_penalty_present",
    )

    assert watched.candidate_id == "watch-alpha"
    assert watched.total_lag_probability_penalty == d("0.039973")
    assert watched.penalty_adjusted_probability_edge == d("0.030027")
    assert watched.penalty_to_edge_ratio == d("0.571043")
    assert watched.edge_shortfall == ZERO
    assert "resolution_lag_cost_penalty_watch" in watched.reason_codes

    assert passed.candidate_id == "pass-alpha"
    assert passed.total_lag_probability_penalty == d("0.017263")
    assert passed.penalty_adjusted_probability_edge == d("0.082737")
    assert passed.penalty_to_edge_ratio == d("0.172630")
    assert passed.edge_shortfall == ZERO
    assert passed.reason_codes == (
        "candidate_positive_edge",
        "resolution_lag_cost_penalty_passed",
        "resolution_delay_penalty_present",
        "capital_lockup_penalty_present",
        "stale_evidence_penalty_present",
        "settlement_ambiguity_penalty_present",
        "exit_friction_penalty_present",
    )


def test_empty_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.total_lag_probability_penalty == ZERO
    assert empty.max_total_lag_probability_penalty == ZERO
    assert empty.min_penalty_adjusted_probability_edge == ZERO
    assert empty.max_penalty_to_edge_ratio == ZERO
    assert empty.max_edge_shortfall == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("resolution_lag_cost_penalty_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidates=(candidate(),))
    for value in (empty, *populated.rows, populated):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_cost",
                    "_edge",
                    "_ratio",
                    "_shortfall",
                    "_penalty",
                    "_probability",
                    "_score",
                    "_hours",
                    "_days",
                    "_apr",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_and_digest_are_deterministic_decimal_strings_without_floats() -> None:
    module = api()
    first = report(
        candidates=(
            candidate(candidate_id="second-alpha", market_slug="second-market"),
            candidate(candidate_id="first-alpha", market_slug="first-market"),
        ),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = report(
        candidates=tuple(reversed(first.rows)),
        generated_at=first.generated_at,
    )

    first_payload = module.strategy_candidate_resolution_lag_cost_penalty_v2_payload(first)
    second_payload = module.strategy_candidate_resolution_lag_cost_penalty_v2_payload(second)
    first_digest = module.strategy_candidate_resolution_lag_cost_penalty_v2_digest(first)
    second_digest = module.strategy_candidate_resolution_lag_cost_penalty_v2_digest(second)

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert first_payload["candidate_count"] == "2"
    assert first_payload["total_lag_probability_penalty"] == "0.034526"
    assert first_payload["rows"][0]["total_lag_probability_penalty"] == "0.017263"
    assert first_digest == second_digest
    assert len(first_digest) == 64
    assert first_digest == module.strategy_candidate_resolution_lag_cost_penalty_v2_digest(first)
    assert json.dumps(first_payload, allow_nan=False, sort_keys=True)
    assert_no_float_values(first_payload)


def test_validation_rejects_bad_types_precision_duplicates_dates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_resolution_lag_cost_penalty_v2(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="Decimal"):
        candidate(expected_probability_edge=0.1)
    with pytest.raises(ValueError, match="six decimal"):
        candidate(exit_friction_score=d("0.0000001"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        candidate(settlement_ambiguity_score=d("1.000001"))
    with pytest.raises(ValueError, match="datetime"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 6, 11, 30))
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 6, 11, 30, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate(report_only=False)
    with pytest.raises(ValueError, match="max_pass_penalty_to_edge_ratio"):
        config(
            max_pass_penalty_to_edge_ratio=d("0.900000"),
            max_watch_penalty_to_edge_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        report(candidates=(candidate(), candidate()))
    with pytest.raises(ValueError, match="observed_at"):
        report(
            candidates=(
                candidate(observed_at=datetime(2026, 7, 6, 12, 1, tzinfo=UTC)),
            ),
        )

    result = report(candidates=(candidate(),))
    with pytest.raises(FrozenInstanceError):
        result.rows[0].penalty_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)


def test_static_phase1_surface_has_no_io_or_execution_behavior() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    exported_names = set(module.__all__)

    forbidden_import_roots = {
        "httpx",
        "psycopg",
        "requests",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "execute",
        "open",
        "request",
        "send",
        "submit",
    }
    forbidden_public_fragments = (
        "auth",
        "broker",
        "cancel",
        "exchange_mutation",
        "live",
        "order",
        "private_key",
        "sign",
        "trade",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            assert name not in forbidden_calls

    for name in exported_names:
        lowered = name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    for unsafe_key in (
        "auth_token",
        "wallet_address",
        "live_order_id",
        "trade_request",
        "cancel_request",
        "replace_request",
    ):
        with pytest.raises(ValueError, match="unsafe surface field"):
            module._reject_unsafe_fields("phase1 boundary probe", {unsafe_key: "x"})
