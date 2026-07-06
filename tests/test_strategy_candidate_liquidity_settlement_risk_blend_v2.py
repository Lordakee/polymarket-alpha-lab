from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_liquidity_settlement_risk_blend_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def blend_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "candidate_id": "candidate-liquidity-risk-v2",
        "available_liquidity_usd": d("2500.000000"),
        "target_notional_usd": d("5000.000000"),
        "spread_bps": d("40.000000"),
        "maximum_spread_bps": d("100.000000"),
        "depth_usd": d("3000.000000"),
        "minimum_depth_usd": d("6000.000000"),
        "settlement_lag_hours": d("36.000000"),
        "maximum_settlement_lag_hours": d("72.000000"),
        "resolution_ambiguity_score": d("0.250000"),
        "exit_difficulty_score": d("0.300000"),
        "minimum_actionable_score": d("65.000000"),
        "reason_codes": ("research_signal_present",),
    }
    values.update(overrides)
    return module.StrategyCandidateLiquiditySettlementRiskBlendV2Input(**values)


def blend(subject: object | None = None):
    module = api()
    return module.estimate_strategy_candidate_liquidity_settlement_risk_blend_v2(
        blend_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_blend_scores_capacity_spread_depth_settlement_resolution_and_exit() -> None:
    module = api()

    result = blend()

    assert result == module.StrategyCandidateLiquiditySettlementRiskBlendV2Result(
        candidate_id="candidate-liquidity-risk-v2",
        available_liquidity_usd=d("2500.000000"),
        target_notional_usd=d("5000.000000"),
        liquidity_capacity_score=d("50.000000"),
        spread_bps=d("40.000000"),
        maximum_spread_bps=d("100.000000"),
        spread_score=d("60.000000"),
        depth_usd=d("3000.000000"),
        minimum_depth_usd=d("6000.000000"),
        depth_score=d("50.000000"),
        settlement_lag_hours=d("36.000000"),
        maximum_settlement_lag_hours=d("72.000000"),
        settlement_lag_score=d("50.000000"),
        resolution_ambiguity_score=d("0.250000"),
        resolution_clarity_score=d("75.000000"),
        exit_difficulty_score=d("0.300000"),
        exit_ease_score=d("70.000000"),
        paper_blend_score=d("57.250000"),
        risk_score=d("42.750000"),
        minimum_actionable_score=d("65.000000"),
        blend_status="watch",
        blend_decision="manual_review",
        reason_codes=(
            "research_signal_present",
            "strategy_candidate_liquidity_settlement_risk_blend_v2",
            "blend_watch",
            "liquidity_capacity_shortfall",
            "spread_penalty_applied",
            "depth_shortfall",
            "settlement_lag_penalty_applied",
            "resolution_ambiguity_present",
            "exit_difficulty_present",
            "blend_positive_below_minimum",
        ),
        derived_validation_digest=(
            "6b67e79237b645b142207485ace3e8251e66deeeb63568ba8f1424c5b8b4e119"
        ),
    )
    assert type(result.paper_blend_score) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_candidate_when_liquidity_and_resolution_clear_thresholds() -> None:
    result = blend(
        blend_input(
            available_liquidity_usd=d("10000.000000"),
            target_notional_usd=d("5000.000000"),
            spread_bps=d("5.000000"),
            depth_usd=d("9000.000000"),
            minimum_depth_usd=d("6000.000000"),
            settlement_lag_hours=d("12.000000"),
            resolution_ambiguity_score=d("0.000000"),
            exit_difficulty_score=d("0.050000"),
            minimum_actionable_score=d("80.000000"),
            reason_codes=(),
        ),
    )

    assert result.liquidity_capacity_score == d("100.000000")
    assert result.spread_score == d("95.000000")
    assert result.depth_score == d("100.000000")
    assert result.settlement_lag_score == d("83.333333")
    assert result.resolution_clarity_score == d("100.000000")
    assert result.exit_ease_score == d("95.000000")
    assert result.paper_blend_score == d("96.250000")
    assert result.risk_score == d("3.750000")
    assert result.blend_status == "candidate"
    assert result.blend_decision == "paper_candidate"
    assert result.reason_codes == (
        "strategy_candidate_liquidity_settlement_risk_blend_v2",
        "blend_candidate",
        "liquidity_capacity_sufficient",
        "spread_inside_limit",
        "depth_sufficient",
        "settlement_lag_inside_limit",
        "resolution_clear",
        "exit_easy",
        "minimum_actionable_score_met",
    )


def test_blocked_when_all_blend_components_are_exhausted() -> None:
    result = blend(
        blend_input(
            available_liquidity_usd=d("0.000000"),
            spread_bps=d("100.000000"),
            depth_usd=d("0.000000"),
            settlement_lag_hours=d("72.000000"),
            resolution_ambiguity_score=d("1.000000"),
            exit_difficulty_score=d("1.000000"),
            minimum_actionable_score=d("1.000000"),
            reason_codes=(),
        ),
    )

    assert result.paper_blend_score == d("0.000000")
    assert result.risk_score == d("100.000000")
    assert result.blend_status == "blocked"
    assert result.blend_decision == "reject"
    assert "blend_below_or_equal_zero" in result.reason_codes


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = blend()
    payload = result.payload

    assert payload == module.strategy_candidate_liquidity_settlement_risk_blend_v2_payload(
        result,
    )
    assert payload["paper_blend_score"] == "57.250000"
    assert payload["resolution_ambiguity_score"] == "0.250000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_liquidity_settlement_risk_blend_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = blend_input()
    result = blend(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.StrategyCandidateLiquiditySettlementRiskBlendV2Input.__dataclass_params__.frozen
    assert module.StrategyCandidateLiquiditySettlementRiskBlendV2Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.candidate_id = "other-candidate"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.blend_status = "candidate"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="available_liquidity_usd must be a Decimal"):
        blend_input(available_liquidity_usd=2500)
    with pytest.raises(ValueError, match="candidate_id must be a canonical"):
        blend_input(candidate_id=" candidate-liquidity-risk-v2")
    with pytest.raises(ValueError, match="target_notional_usd must be positive"):
        blend_input(target_notional_usd=d("0.000000"))
    with pytest.raises(ValueError, match="maximum_spread_bps must be positive"):
        blend_input(maximum_spread_bps=d("0.000000"))
    with pytest.raises(ValueError, match="resolution_ambiguity_score must be <= 1"):
        blend_input(resolution_ambiguity_score=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        blend_input(reason_codes=["research_signal_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        blend_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="blend_input"):
        blend(object())

    rebuilt = module.StrategyCandidateLiquiditySettlementRiskBlendV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = blend()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyCandidateLiquiditySettlementRiskBlendV2Result(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            blend_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_liquidity_settlement_risk_blend_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_liquidity_settlement_risk_blend_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_liquidity_settlement_risk_blend_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "BLEND_STATUSES",
        "BLEND_DECISIONS",
        "StrategyCandidateLiquiditySettlementRiskBlendV2Input",
        "StrategyCandidateLiquiditySettlementRiskBlendV2Result",
        "estimate_strategy_candidate_liquidity_settlement_risk_blend_v2",
        "strategy_candidate_liquidity_settlement_risk_blend_v2_payload",
        "reject_strategy_candidate_liquidity_settlement_risk_blend_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "strategy_candidate_liquidity_settlement_risk_blend_v2" not in getattr(
        root,
        "__all__",
        (),
    )
