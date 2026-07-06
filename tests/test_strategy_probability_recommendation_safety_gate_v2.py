from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_probability_recommendation_safety_gate_v2 import (
    DEFAULT_STRATEGY_PROBABILITY_RECOMMENDATION_SAFETY_GATE_V2_CONFIG_VERSION,
    StrategyProbabilityRecommendationSafetyGateV2Config,
    StrategyProbabilityRecommendationSafetyGateV2Input,
    StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount,
    StrategyProbabilityRecommendationSafetyGateV2Report,
    StrategyProbabilityRecommendationSafetyGateV2Row,
    build_strategy_probability_recommendation_safety_gate_v2_report,
    strategy_probability_recommendation_safety_gate_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 15, 30, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=20)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyProbabilityRecommendationSafetyGateV2Config:
    values = {
        "config_version": (
            DEFAULT_STRATEGY_PROBABILITY_RECOMMENDATION_SAFETY_GATE_V2_CONFIG_VERSION
        ),
        "min_pass_cost_adjusted_edge": d("0.030000"),
        "min_watch_cost_adjusted_edge": d("0.010000"),
        "min_evidence_quality_score": d("0.700000"),
        "max_resolution_risk_score": d("0.400000"),
        "max_liquidity_exit_risk_score": d("0.500000"),
        "min_specialist_quorum_score": d("0.666667"),
        "max_category_concentration_share": d("0.350000"),
    }
    values.update(overrides)
    return StrategyProbabilityRecommendationSafetyGateV2Config(**values)


def recommendation(
    recommendation_id: str = "rec-alpha",
    *,
    category: str = "macro",
    estimated_probability: Decimal = d("0.640000"),
    market_price: Decimal = d("0.550000"),
    fee_probability_cost: Decimal = d("0.010000"),
    slippage_probability_cost: Decimal = d("0.015000"),
    evidence_quality_score: Decimal = d("0.850000"),
    resolution_risk_score: Decimal = d("0.200000"),
    liquidity_exit_risk_score: Decimal = d("0.250000"),
    specialist_quorum_score: Decimal = d("0.900000"),
    category_concentration_share: Decimal = d("0.200000"),
    observed_at: datetime = OBSERVED_AT,
    source_config_version: str = "phase1-local-snapshot-v0",
    reason_codes: tuple[str, ...] = ("probability_input_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyProbabilityRecommendationSafetyGateV2Input:
    return StrategyProbabilityRecommendationSafetyGateV2Input(
        recommendation_id=recommendation_id,
        category=category,
        estimated_probability=estimated_probability,
        market_price=market_price,
        fee_probability_cost=fee_probability_cost,
        slippage_probability_cost=slippage_probability_cost,
        evidence_quality_score=evidence_quality_score,
        resolution_risk_score=resolution_risk_score,
        liquidity_exit_risk_score=liquidity_exit_risk_score,
        specialist_quorum_score=specialist_quorum_score,
        category_concentration_share=category_concentration_share,
        observed_at=observed_at,
        source_config_version=source_config_version,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: StrategyProbabilityRecommendationSafetyGateV2Input,
    cfg: StrategyProbabilityRecommendationSafetyGateV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyProbabilityRecommendationSafetyGateV2Report:
    return build_strategy_probability_recommendation_safety_gate_v2_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_gate_scores_pass_watch_and_block_recommendations() -> None:
    digest = report(
        recommendation(
            "rec-pass",
            category="macro",
            estimated_probability=d("0.670000"),
            market_price=d("0.550000"),
            fee_probability_cost=d("0.010000"),
            slippage_probability_cost=d("0.015000"),
            evidence_quality_score=d("0.900000"),
            resolution_risk_score=d("0.200000"),
            liquidity_exit_risk_score=d("0.250000"),
            specialist_quorum_score=d("0.900000"),
            category_concentration_share=d("0.200000"),
            reason_codes=("model_edge_positive",),
        ),
        recommendation(
            "rec-watch",
            category="policy",
            estimated_probability=d("0.585000"),
            market_price=d("0.550000"),
            fee_probability_cost=d("0.010000"),
            slippage_probability_cost=d("0.015000"),
            evidence_quality_score=d("0.650000"),
            resolution_risk_score=d("0.400000"),
            liquidity_exit_risk_score=d("0.450000"),
            specialist_quorum_score=d("0.600000"),
            category_concentration_share=d("0.340000"),
        ),
        recommendation(
            "rec-block",
            category="sports",
            estimated_probability=d("0.570000"),
            market_price=d("0.550000"),
            fee_probability_cost=d("0.010000"),
            slippage_probability_cost=d("0.015000"),
            evidence_quality_score=d("0.500000"),
            resolution_risk_score=d("0.700000"),
            liquidity_exit_risk_score=d("0.800000"),
            specialist_quorum_score=d("0.400000"),
            category_concentration_share=d("0.600000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == "strategy-probability-recommendation-safety-gate-v2"
    assert digest.recommendation_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.min_cost_adjusted_edge == d("-0.005000")
    assert digest.min_evidence_quality_score == d("0.500000")
    assert digest.max_resolution_risk_score == d("0.700000")
    assert digest.max_liquidity_exit_risk_score == d("0.800000")
    assert digest.min_specialist_quorum_score == d("0.400000")
    assert digest.max_category_concentration_share == d("0.600000")
    assert digest.status == "blocked"
    assert digest.recommended_next_step == "block_recommendation"
    assert digest.reason_codes == (
        "strategy_probability_safety_gate_blocked",
        "safety_category_concentration_excessive_blocked",
        "safety_cost_adjusted_edge_thin_watch",
        "safety_evidence_quality_low_blocked",
        "safety_liquidity_exit_risk_high_blocked",
        "safety_quorum_weak_watch",
        "safety_resolution_risk_high_blocked",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert len(digest.derived_validation_digest) == 64

    blocked, watched, passed = digest.rows
    assert tuple(row.gate_status for row in digest.rows) == ("blocked", "watch", "pass")
    assert blocked.recommendation_id == "rec-block"
    assert blocked.raw_probability_edge == d("0.020000")
    assert blocked.total_probability_cost == d("0.025000")
    assert blocked.cost_adjusted_edge == d("-0.005000")
    assert blocked.reason_codes == (
        "probability_input_ready",
        "safety_category_concentration_excessive_blocked",
        "safety_cost_adjusted_edge_negative_blocked",
        "safety_evidence_quality_low_blocked",
        "safety_liquidity_exit_risk_high_blocked",
        "safety_quorum_weak_watch",
        "safety_resolution_risk_high_blocked",
    )
    assert watched.gate_status == "watch"
    assert watched.cost_adjusted_edge == d("0.010000")
    assert watched.reason_codes == (
        "probability_input_ready",
        "safety_cost_adjusted_edge_thin_watch",
        "safety_evidence_quality_thin_watch",
        "safety_quorum_weak_watch",
    )
    assert passed.gate_status == "pass"
    assert passed.reason_codes == ("model_edge_positive", "safety_gate_clear")

    assert digest.reason_code_counts[:2] == (
        StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount(
            reason_code="probability_input_ready",
            count=d("2.000000"),
            recommendation_ratio=d("0.666667"),
        ),
        StrategyProbabilityRecommendationSafetyGateV2ReasonCodeCount(
            reason_code="safety_quorum_weak_watch",
            count=d("2.000000"),
            recommendation_ratio=d("0.666667"),
        ),
    )


def test_empty_gate_is_pass_with_decimal_counts_and_flags() -> None:
    digest = report()

    assert digest.recommendation_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.min_cost_adjusted_edge == ZERO
    assert digest.status == "pass"
    assert digest.recommended_next_step == "paper_monitor_only"
    assert digest.reason_codes == ("strategy_probability_safety_gate_empty",)
    assert digest.reason_code_counts == ()
    assert digest.rows == ()

    populated = report(recommendation())
    for value in (digest, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_score", "_cost", "_edge", "_ratio", "_share")):
                assert type(item_value) is Decimal


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    digest = report(
        recommendation(
            observed_at=datetime(
                2026,
                7,
                6,
                8,
                10,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            6,
            8,
            30,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = strategy_probability_recommendation_safety_gate_v2_payload(digest)

    assert payload["generated_at"] == "2026-07-06T15:30:00+00:00"
    assert payload["recommendation_count"] == "1.000000"
    assert payload["rows"][0]["cost_adjusted_edge"] == "0.065000"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T15:10:00+00:00"
    assert payload["derived_validation_digest"] == digest.derived_validation_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["pass_count"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_probability_recommendation_safety_gate_v2_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest, pass_count=d("2.000000"))


def test_public_payload_rejects_unsafe_keys_values_flags_and_numbers() -> None:
    digest = report(recommendation())
    payload = strategy_probability_recommendation_safety_gate_v2_payload(digest)

    for key in (
        "live_mode",
        "auth_header",
        "wallet_address",
        "order_id",
        "network_url",
        "database_table",
        "persist_path",
        "signing_key",
        "mutation_name",
        "buy_instruction",
        "sell_instruction",
        "trade_route",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            strategy_probability_recommendation_safety_gate_v2_payload(unsafe)

    for value in ("live quote", "auth token", "wallet signer", "buy now", "sell now"):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            strategy_probability_recommendation_safety_gate_v2_payload(unsafe)

    numeric = dict(payload)
    numeric["recommendation_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        strategy_probability_recommendation_safety_gate_v2_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        strategy_probability_recommendation_safety_gate_v2_payload(downgraded)


def test_validation_rejects_non_decimal_values_duplicate_ids_and_bad_time_boundaries() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        recommendation(estimated_probability=0.6)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        recommendation(estimated_probability=_DecimalSubclass("0.600000"))

    with pytest.raises(ValueError, match="generated_at"):
        report(recommendation("aware"), generated_at=datetime(2026, 7, 6, 15, 30))

    with pytest.raises(ValueError, match="observed_at"):
        recommendation(observed_at=datetime(2026, 7, 6, 15, 10))

    with pytest.raises(ValueError, match="future"):
        report(recommendation(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unique"):
        report(recommendation("duplicate"), recommendation("duplicate"))

    with pytest.raises(ValueError, match="paper_only"):
        recommendation(paper_only=False)

    with pytest.raises(ValueError, match="subclass"):
        StrategyProbabilityRecommendationSafetyGateV2Config.__new__(
            type(
                "ConfigSubclass",
                (StrategyProbabilityRecommendationSafetyGateV2Config,),
                {},
            ),
        )

    frozen = recommendation()
    with pytest.raises(FrozenInstanceError):
        frozen.recommendation_id = "changed"  # type: ignore[misc]


def test_report_constructors_reject_inconsistent_materialized_fields() -> None:
    digest = report(recommendation())
    row = digest.rows[0]

    with pytest.raises(ValueError, match="cost_adjusted_edge"):
        StrategyProbabilityRecommendationSafetyGateV2Row(
            **{
                **row.__dict__,
                "cost_adjusted_edge": d("0.010000"),
            },
        )

    with pytest.raises(ValueError, match="status"):
        StrategyProbabilityRecommendationSafetyGateV2Report(
            **{
                **digest.__dict__,
                "status": "blocked",
            },
        )


def test_module_exposes_no_network_order_wallet_db_or_persistence_surface() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_probability_recommendation_safety_gate_v2.py"
    )
    tree = ast.parse(module_path.read_text())
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
