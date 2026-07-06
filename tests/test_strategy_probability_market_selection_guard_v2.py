from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_probability_market_selection_guard_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_probability_market_selection_guard_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
CAPTURED_AT = datetime(2026, 7, 6, 11, 45, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing market-selection guard module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "minimum_research_readiness_score": d("0.700000"),
        "minimum_cost_adjusted_edge": d("0.030000"),
        "maximum_resolution_ambiguity_score": d("0.250000"),
        "minimum_liquidity_exit_feasibility_score": d("0.600000"),
        "maximum_portfolio_concentration_ratio": d("0.150000"),
        "minimum_specialist_quorum_count": d("3"),
    }
    values.update(overrides)
    return module.StrategyProbabilityMarketSelectionGuardV2Config(**values)


def candidate(
    candidate_id: str = "candidate-pass",
    *,
    market_slug: str = "fed-cuts-by-september",
    event_id: str = "macro-rates-2026",
    research_source_id: str = "source-macro",
    research_readiness_score: Decimal = d("0.920000"),
    gross_probability_edge: Decimal = d("0.085000"),
    estimated_fee_ratio: Decimal = d("0.010000"),
    estimated_slippage_ratio: Decimal = d("0.015000"),
    resolution_ambiguity_score: Decimal = d("0.100000"),
    liquidity_exit_feasibility_score: Decimal = d("0.850000"),
    projected_portfolio_concentration_ratio: Decimal = d("0.050000"),
    specialist_quorum_count: Decimal = d("4"),
    captured_at: datetime = CAPTURED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.StrategyProbabilityMarketSelectionCandidate(
        candidate_id=candidate_id,
        market_slug=market_slug,
        event_id=event_id,
        research_source_id=research_source_id,
        research_readiness_score=research_readiness_score,
        gross_probability_edge=gross_probability_edge,
        estimated_fee_ratio=estimated_fee_ratio,
        estimated_slippage_ratio=estimated_slippage_ratio,
        resolution_ambiguity_score=resolution_ambiguity_score,
        liquidity_exit_feasibility_score=liquidity_exit_feasibility_score,
        projected_portfolio_concentration_ratio=projected_portfolio_concentration_ratio,
        specialist_quorum_count=specialist_quorum_count,
        captured_at=captured_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    selected_config = overrides.pop("config", None)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_strategy_probability_market_selection_guard_v2(
        items,
        config=selected_config or config(),
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


def test_blocks_market_candidates_on_all_phase_1_readiness_guards() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        candidate("candidate-pass"),
        candidate(
            "candidate-blocked",
            market_slug="election-resolution-procedure",
            event_id="election-rules-2026",
            research_source_id="source-civic",
            research_readiness_score=d("0.600000"),
            gross_probability_edge=d("0.035000"),
            estimated_fee_ratio=d("0.010000"),
            estimated_slippage_ratio=d("0.010000"),
            resolution_ambiguity_score=d("0.350000"),
            liquidity_exit_feasibility_score=d("0.400000"),
            projected_portfolio_concentration_ratio=d("0.200000"),
            specialist_quorum_count=d("2"),
            captured_at=datetime(2026, 7, 6, 7, 30, tzinfo=eastern),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-probability-market-selection-guard-v2"
    assert report.candidate_count == d("2")
    assert report.pass_candidate_count == d("1")
    assert report.blocked_candidate_count == d("1")
    assert report.average_cost_adjusted_edge == d("0.037500")
    assert report.minimum_cost_adjusted_edge_seen == d("0.015000")
    assert report.maximum_resolution_ambiguity_seen == d("0.350000")
    assert report.maximum_portfolio_concentration_seen == d("0.200000")
    assert report.decision_status == "blocked"
    assert report.reason_codes == (
        "market_selection_guard_candidates_blocked",
        "weak_research_readiness_block",
        "thin_cost_adjusted_edge_block",
        "high_resolution_ambiguity_block",
        "low_liquidity_exit_feasibility_block",
        "portfolio_concentration_block",
        "insufficient_specialist_quorum_block",
    )

    assert tuple(row.candidate_id for row in report.decisions) == (
        "candidate-blocked",
        "candidate-pass",
    )
    blocked = report.decisions[0]
    assert blocked.decision_status == "blocked"
    assert blocked.cost_adjusted_edge == d("0.015000")
    assert blocked.captured_at == datetime(2026, 7, 6, 11, 30, tzinfo=UTC)
    assert blocked.reason_codes == (
        "weak_research_readiness_block",
        "thin_cost_adjusted_edge_block",
        "high_resolution_ambiguity_block",
        "low_liquidity_exit_feasibility_block",
        "portfolio_concentration_block",
        "insufficient_specialist_quorum_block",
    )

    passing = report.decisions[1]
    assert passing.decision_status == "pass"
    assert passing.cost_adjusted_edge == d("0.060000")
    assert passing.reason_codes == ("market_selection_guard_candidate_pass",)

    payload = report.payload
    assert payload["candidate_count"] == "2"
    assert payload["average_cost_adjusted_edge"] == "0.037500"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["decisions"][0]["cost_adjusted_edge"] == "0.015000"
    assert payload["decisions"][0]["specialist_quorum_count"] == "2"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_empty_input_is_blocked_report_only_and_digest_backed() -> None:
    report = build_report()

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.candidate_count == d("0")
    assert report.pass_candidate_count == d("0")
    assert report.blocked_candidate_count == d("0")
    assert report.average_cost_adjusted_edge == d("0.000000")
    assert report.minimum_cost_adjusted_edge_seen == d("0.000000")
    assert report.maximum_resolution_ambiguity_seen == d("0.000000")
    assert report.maximum_portfolio_concentration_seen == d("0.000000")
    assert report.decision_status == "blocked"
    assert report.reason_codes == ("market_selection_guard_no_candidates_block",)
    assert report.decisions == ()
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    sample_config = config()
    sample_candidate = candidate()
    report = build_report(sample_candidate)
    decision = report.decisions[0]

    decimal_fields = {
        "minimum_research_readiness_score",
        "minimum_cost_adjusted_edge",
        "maximum_resolution_ambiguity_score",
        "minimum_liquidity_exit_feasibility_score",
        "maximum_portfolio_concentration_ratio",
        "minimum_specialist_quorum_count",
        "research_readiness_score",
        "gross_probability_edge",
        "estimated_fee_ratio",
        "estimated_slippage_ratio",
        "resolution_ambiguity_score",
        "liquidity_exit_feasibility_score",
        "projected_portfolio_concentration_ratio",
        "specialist_quorum_count",
        "cost_adjusted_edge",
        "candidate_count",
        "pass_candidate_count",
        "blocked_candidate_count",
        "average_cost_adjusted_edge",
        "minimum_cost_adjusted_edge_seen",
        "maximum_resolution_ambiguity_seen",
        "maximum_portfolio_concentration_seen",
    }

    for item in (sample_config, sample_candidate, decision, report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in decimal_fields:
                assert type(getattr(item, field.name)) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(sample_config, paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.StrategyProbabilityMarketSelectionCandidate(
            **{
                **sample_candidate.payload,
                "captured_at": sample_candidate.captured_at,
                "readonly": False,
            },
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "research_readiness_score",
            _DecimalSubclass("0.900000"),
            "research_readiness_score must be exactly Decimal",
        ),
        (
            "gross_probability_edge",
            0.09,
            "gross_probability_edge must be exactly Decimal",
        ),
        (
            "resolution_ambiguity_score",
            d("1.000001"),
            "resolution_ambiguity_score must be <= 1.000000",
        ),
        (
            "liquidity_exit_feasibility_score",
            d("-0.000001"),
            "liquidity_exit_feasibility_score must be >= 0.000000",
        ),
        (
            "specialist_quorum_count",
            d("2.5"),
            "specialist_quorum_count must be an integral Decimal",
        ),
    ),
)
def test_candidate_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        candidate(**{field_name: bad_value})


def test_config_validation_rejects_bad_thresholds_datetime_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="minimum_cost_adjusted_edge must be exactly Decimal"):
        config(minimum_cost_adjusted_edge="0.030000")
    with pytest.raises(ValueError, match="minimum_specialist_quorum_count must be an integral Decimal"):
        config(minimum_specialist_quorum_count=d("2.5"))
    with pytest.raises(ValueError, match="captured_at must be exactly datetime"):
        candidate(captured_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))
    with pytest.raises(ValueError, match="report_only must be True"):
        module.StrategyProbabilityMarketSelectionGuardV2Config(report_only=False)


def test_derived_validation_digest_rejects_tampered_reports() -> None:
    report = build_report(candidate())

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(report, pass_candidate_count=d("9"))


def test_public_payload_rejects_unsafe_keys_and_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public key"):
        module._reject_unsafe_public_payload("payload", {"wallet_hint": "safe"})
    with pytest.raises(ValueError, match="unsafe public value"):
        module._reject_unsafe_public_payload("payload", {"candidate_id": "live-feed"})
    with pytest.raises(ValueError, match="unsafe public value"):
        candidate(market_slug="wallet-risk")


def test_payload_helper_accepts_only_guard_reports_and_preserves_digest() -> None:
    module = api()
    report = build_report(candidate())

    payload = module.strategy_probability_market_selection_guard_v2_payload(report)

    assert payload == report.payload
    with pytest.raises(ValueError, match="report must be StrategyProbabilityMarketSelectionGuardV2Report"):
        module.strategy_probability_market_selection_guard_v2_payload({"report": "dict"})


def test_module_exposes_no_network_persistence_or_execution_surface() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    banned_import_roots = {
        "boto3",
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "urllib",
    }
    banned_call_names = {
        "Request",
        "commit",
        "connect",
        "execute",
        "executemany",
        "open",
        "rollback",
        "urlopen",
    }
    unsafe_public_tokens = {
        "auth",
        "buy",
        "database",
        "live",
        "mutation",
        "network",
        "order",
        "persist",
        "sell",
        "signing",
        "trade",
        "wallet",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names

    public_names = [name for name in dir(module) if not name.startswith("_")]
    for name in public_names:
        folded = name.lower()
        for token in unsafe_public_tokens:
            assert token not in folded
