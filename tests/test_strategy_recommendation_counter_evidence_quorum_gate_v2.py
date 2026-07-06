from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
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
    / "strategy_recommendation_counter_evidence_quorum_gate_v2.py"
)
CONFIG_VERSION = "strategy-recommendation-counter-evidence-quorum-gate-v2-test"
GENERATED_AT = datetime(2026, 7, 6, 15, 0, tzinfo=UTC)
RECOMMENDED_AT = datetime(2026, 7, 6, 14, 30, tzinfo=UTC)
EVIDENCE_AT = datetime(2026, 7, 6, 14, 55, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_recommendation_counter_evidence_quorum_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "min_counter_evidence_family_count": d("2.000000"),
        "min_recent_family_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_source_independence_score": d("0.700000"),
        "max_counter_evidence_age_seconds": d("3600.000000"),
        "family_quorum_gap_discount": d("0.250000"),
        "recency_gap_discount": d("0.300000"),
        "independence_gap_discount": d("0.300000"),
        "max_total_discount_before_block": d("0.650000"),
        "min_adjusted_confidence": d("0.300000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationCounterEvidenceQuorumGateV2Config(**values)


def recommendation(recommendation_id: str = "recommendation-alpha", **overrides: object):
    module = api()
    values = {
        "recommendation_id": recommendation_id,
        "market_id": "market-alpha",
        "recommendation_side": "yes",
        "base_confidence": d("0.800000"),
        "recommended_at": RECOMMENDED_AT,
    }
    values.update(overrides)
    return module.StrategyRecommendationCounterEvidenceQuorumGateV2Recommendation(
        **values,
    )


def counter_evidence(
    family_id: str = "valuation_gap",
    source_id: str = "risk_team",
    **overrides: object,
):
    module = api()
    values = {
        "recommendation_id": "recommendation-alpha",
        "family_id": family_id,
        "source_id": source_id,
        "observed_at": EVIDENCE_AT,
        "independence_score": d("0.800000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationCounterEvidenceQuorumGateV2CounterEvidence(
        **values,
    )


def build_report(*items, recommendations=None, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_recommendation_counter_evidence_quorum_gate_v2_report(
        recommendations or (recommendation(),),
        items,
        config=cfg or config(),
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


def test_quorum_met_leaves_recommendation_undiscounted_with_recent_independent_families() -> None:
    report = build_report(
        counter_evidence(
            "valuation_gap",
            "risk_team",
            independence_score=d("0.800000"),
        ),
        counter_evidence(
            "liquidity_fragility",
            "market_ops",
            observed_at=EVIDENCE_AT - timedelta(minutes=5),
            independence_score=d("0.900000"),
        ),
        generated_at=datetime(2026, 7, 6, 10, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.recommendation_count == d("1.000000")
    assert report.passed_count == d("1.000000")
    assert report.discounted_count == ZERO
    assert report.blocked_count == ZERO
    assert report.status == "passed"
    assert report.reason_codes == ("counter_evidence_quorum_met",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.recommendation_id == "recommendation-alpha"
    assert row.market_id == "market-alpha"
    assert row.recommendation_side == "yes"
    assert row.base_confidence == d("0.800000")
    assert row.adjusted_confidence == d("0.800000")
    assert row.total_discount == ZERO
    assert row.family_count == d("2.000000")
    assert row.recent_family_count == d("2.000000")
    assert row.independent_source_count == d("2.000000")
    assert row.average_independence_score == d("0.850000")
    assert row.latest_counter_evidence_at == EVIDENCE_AT
    assert row.latest_counter_evidence_age_seconds == d("300.000000")
    assert row.gate_status == "passed"
    assert row.reason_codes == ("counter_evidence_quorum_met",)


def test_recency_and_independence_gaps_discount_before_blocking_threshold() -> None:
    old_at = GENERATED_AT - timedelta(hours=3)

    report = build_report(
        counter_evidence("valuation_gap", "risk_team"),
        counter_evidence(
            "liquidity_fragility",
            "market_ops",
            observed_at=old_at,
            independence_score=d("0.900000"),
        ),
    )

    assert report.status == "discounted"
    assert report.passed_count == ZERO
    assert report.discounted_count == d("1.000000")
    assert report.blocked_count == ZERO
    assert report.reason_codes == (
        "counter_evidence_discounted",
        "counter_evidence_independence_gap",
        "counter_evidence_recency_gap",
    )

    row = report.rows[0]
    assert row.gate_status == "discounted"
    assert row.family_count == d("2.000000")
    assert row.recent_family_count == d("1.000000")
    assert row.independent_source_count == d("1.000000")
    assert row.total_discount == d("0.600000")
    assert row.adjusted_confidence == d("0.320000")
    assert row.reason_codes == (
        "counter_evidence_discounted",
        "counter_evidence_independence_gap",
        "counter_evidence_recency_gap",
    )


def test_missing_counter_evidence_blocks_recommendation_with_deterministic_reasons() -> None:
    report = build_report()

    assert report.status == "blocked"
    assert report.passed_count == ZERO
    assert report.discounted_count == ZERO
    assert report.blocked_count == d("1.000000")
    assert report.reason_codes == (
        "counter_evidence_blocked",
        "counter_evidence_confidence_floor_gap",
        "counter_evidence_family_quorum_gap",
        "counter_evidence_independence_gap",
        "counter_evidence_recency_gap",
    )

    row = report.rows[0]
    assert row.gate_status == "blocked"
    assert row.adjusted_confidence == ZERO
    assert row.total_discount == d("1.000000")
    assert row.family_count == ZERO
    assert row.recent_family_count == ZERO
    assert row.independent_source_count == ZERO
    assert row.average_independence_score == ZERO
    assert row.latest_counter_evidence_at is None
    assert row.latest_counter_evidence_age_seconds is None
    assert row.reason_codes == report.reason_codes


def test_multiple_recommendations_are_sorted_by_gate_severity_then_discount() -> None:
    discounted = recommendation("recommendation-discounted", market_id="market-beta")
    blocked = recommendation("recommendation-blocked", market_id="market-gamma")
    passed = recommendation("recommendation-passed", market_id="market-alpha")

    report = build_report(
        counter_evidence(
            "valuation_gap",
            "risk_team",
            recommendation_id="recommendation-discounted",
        ),
        counter_evidence(
            "liquidity_fragility",
            "market_ops",
            recommendation_id="recommendation-discounted",
            observed_at=GENERATED_AT - timedelta(hours=3),
            independence_score=d("0.900000"),
        ),
        counter_evidence(
            "valuation_gap",
            "risk_team",
            recommendation_id="recommendation-passed",
        ),
        counter_evidence(
            "liquidity_fragility",
            "market_ops",
            recommendation_id="recommendation-passed",
            independence_score=d("0.900000"),
        ),
        recommendations=(discounted, blocked, passed),
    )

    assert report.status == "blocked"
    assert tuple(row.recommendation_id for row in report.rows) == (
        "recommendation-blocked",
        "recommendation-discounted",
        "recommendation-passed",
    )
    assert tuple(row.gate_status for row in report.rows) == (
        "blocked",
        "discounted",
        "passed",
    )


def test_frozen_dataclasses_decimal_only_inputs_and_hard_flags() -> None:
    module = api()
    report = build_report(
        counter_evidence("valuation_gap", "risk_team"),
        counter_evidence("liquidity_fragility", "market_ops"),
    )

    assert is_dataclass(module.StrategyRecommendationCounterEvidenceQuorumGateV2Config)
    assert is_dataclass(module.StrategyRecommendationCounterEvidenceQuorumGateV2Recommendation)
    assert is_dataclass(module.StrategyRecommendationCounterEvidenceQuorumGateV2CounterEvidence)
    assert is_dataclass(module.StrategyRecommendationCounterEvidenceQuorumGateV2Row)
    assert is_dataclass(module.StrategyRecommendationCounterEvidenceQuorumGateV2Report)
    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].adjusted_confidence = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        recommendation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="base_confidence"):
        recommendation(base_confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independence_score"):
        counter_evidence(independence_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="observed_at"):
        counter_evidence(observed_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=datetime(2026, 7, 6, 15, 0))
    with pytest.raises(ValueError, match="duplicate"):
        build_report(recommendations=(recommendation(), recommendation()))
    with pytest.raises(ValueError, match="unknown recommendation"):
        build_report(counter_evidence(recommendation_id="missing-recommendation"))

    for value in (report, *report.rows):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name.endswith(("_count", "_confidence", "_discount", "_score", "_seconds")):
                assert type(item_value) is Decimal or item_value is None


def test_module_scope_has_no_stateful_io_auth_order_or_persistence_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
