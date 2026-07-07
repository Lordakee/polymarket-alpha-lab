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
        "polymarket_alpha_lab.strategy_candidate_resolution_rule_sensitivity_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "candidate_id": "candidate-resolution-rule-v2",
        "rule_specificity_ratio": d("0.300000"),
        "official_source_hierarchy_ratio": d("0.250000"),
        "settlement_ambiguity_ratio": d("0.800000"),
        "seconds_until_resolution_deadline": d("3600"),
        "deadline_proximity_window_seconds": d("14400"),
        "prior_dispute_count": d("3"),
        "historical_resolution_count": d("6"),
        "watch_sensitivity_bps": d("300.000000"),
        "block_sensitivity_bps": d("700.000000"),
        "reason_codes": ("resolution_rule_review_requested",),
    }
    values.update(overrides)
    return module.StrategyCandidateResolutionRuleSensitivityScoreV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_strategy_candidate_resolution_rule_sensitivity_score_v2(
        score_input() if subject is None else subject,
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


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_resolution_rule_sensitivity_scores_high_risk_rule_fragility() -> None:
    module = api()

    result = score()

    assert result == module.StrategyCandidateResolutionRuleSensitivityScoreV2Result(
        candidate_id="candidate-resolution-rule-v2",
        rule_specificity_ratio=d("0.300000"),
        official_source_hierarchy_ratio=d("0.250000"),
        settlement_ambiguity_ratio=d("0.800000"),
        seconds_until_resolution_deadline=d("3600"),
        deadline_proximity_window_seconds=d("14400"),
        prior_dispute_count=d("3"),
        historical_resolution_count=d("6"),
        rule_specificity_penalty_bps=d("210.000000"),
        official_source_hierarchy_penalty_bps=d("150.000000"),
        settlement_ambiguity_penalty_bps=d("200.000000"),
        deadline_proximity_ratio=d("0.750000"),
        deadline_proximity_penalty_bps=d("112.500000"),
        dispute_history_ratio=d("0.500000"),
        dispute_history_penalty_bps=d("50.000000"),
        paper_score_bps=d("722.500000"),
        watch_sensitivity_bps=d("300.000000"),
        block_sensitivity_bps=d("700.000000"),
        sensitivity_rank="high",
        score_status="blocked",
        score_decision="reject",
        reason_codes=(
            "resolution_rule_review_requested",
            "strategy_candidate_resolution_rule_sensitivity_score_v2",
            "score_blocked",
            "sensitivity_high",
            "rule_specificity_penalty_applied",
            "official_source_hierarchy_penalty_applied",
            "settlement_ambiguity_penalty_applied",
            "deadline_proximity_penalty_applied",
            "dispute_history_penalty_applied",
            "sensitivity_exceeds_block_threshold",
        ),
        derived_validation_digest=(
            "d565b5e62472a7d74e81c2777b793eccb5d248b6b6514b561367766475e7fe17"
        ),
    )
    assert type(result.paper_score_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_candidate_when_resolution_rules_are_specific_official_and_uncontested() -> None:
    result = score(
        score_input(
            rule_specificity_ratio=d("1.000000"),
            official_source_hierarchy_ratio=d("1.000000"),
            settlement_ambiguity_ratio=d("0.000000"),
            seconds_until_resolution_deadline=d("28800"),
            deadline_proximity_window_seconds=d("7200"),
            prior_dispute_count=d("0"),
            historical_resolution_count=d("8"),
            watch_sensitivity_bps=d("250.000000"),
            block_sensitivity_bps=d("600.000000"),
            reason_codes=(),
        ),
    )

    assert result.rule_specificity_penalty_bps == d("0.000000")
    assert result.official_source_hierarchy_penalty_bps == d("0.000000")
    assert result.settlement_ambiguity_penalty_bps == d("0.000000")
    assert result.deadline_proximity_ratio == d("0.000000")
    assert result.dispute_history_ratio == d("0.000000")
    assert result.paper_score_bps == d("0.000000")
    assert result.sensitivity_rank == "low"
    assert result.score_status == "candidate"
    assert result.score_decision == "paper_candidate"
    assert result.reason_codes == (
        "strategy_candidate_resolution_rule_sensitivity_score_v2",
        "score_candidate",
        "sensitivity_low",
        "rule_specificity_clear",
        "official_source_hierarchy_clear",
        "settlement_ambiguity_clear",
        "deadline_not_near",
        "no_dispute_history",
        "sensitivity_below_watch_threshold",
    )


def test_watch_when_resolution_rule_sensitivity_is_moderate() -> None:
    result = score(
        score_input(
            rule_specificity_ratio=d("0.600000"),
            official_source_hierarchy_ratio=d("0.500000"),
            settlement_ambiguity_ratio=d("0.400000"),
            seconds_until_resolution_deadline=d("7200"),
            deadline_proximity_window_seconds=d("14400"),
            prior_dispute_count=d("0"),
            historical_resolution_count=d("10"),
            watch_sensitivity_bps=d("300.000000"),
            block_sensitivity_bps=d("700.000000"),
            reason_codes=(),
        ),
    )

    assert result.rule_specificity_penalty_bps == d("120.000000")
    assert result.official_source_hierarchy_penalty_bps == d("100.000000")
    assert result.settlement_ambiguity_penalty_bps == d("100.000000")
    assert result.deadline_proximity_ratio == d("0.500000")
    assert result.deadline_proximity_penalty_bps == d("75.000000")
    assert result.dispute_history_penalty_bps == d("0.000000")
    assert result.paper_score_bps == d("395.000000")
    assert result.sensitivity_rank == "moderate"
    assert result.score_status == "watch"
    assert result.score_decision == "manual_review"
    assert "sensitivity_requires_manual_review" in result.reason_codes


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.strategy_candidate_resolution_rule_sensitivity_score_v2_payload(
        result,
    )
    assert payload["paper_score_bps"] == "722.500000"
    assert payload["deadline_proximity_ratio"] == "0.750000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_resolution_rule_sensitivity_score_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert (
        module.StrategyCandidateResolutionRuleSensitivityScoreV2Input.__dataclass_params__.frozen
    )
    assert (
        module.StrategyCandidateResolutionRuleSensitivityScoreV2Result.__dataclass_params__.frozen
    )

    with pytest.raises(FrozenInstanceError):
        subject.candidate_id = "other-candidate"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.score_status = "candidate"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="rule_specificity_ratio must be a Decimal"):
        score_input(rule_specificity_ratio=1)
    with pytest.raises(ValueError, match="settlement_ambiguity_ratio must be between"):
        score_input(settlement_ambiguity_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="candidate_id must be a canonical"):
        score_input(candidate_id=" candidate-resolution-rule-v2")
    with pytest.raises(ValueError, match="seconds_until_resolution_deadline must be integral"):
        score_input(seconds_until_resolution_deadline=d("1.500000"))
    with pytest.raises(ValueError, match="historical_resolution_count must be positive"):
        score_input(historical_resolution_count=d("0"))
    with pytest.raises(ValueError, match="prior_dispute_count must not exceed"):
        score_input(prior_dispute_count=d("7"))
    with pytest.raises(ValueError, match="block_sensitivity_bps must be at least"):
        score_input(block_sensitivity_bps=d("299.999999"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["resolution_rule_review_requested"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.StrategyCandidateResolutionRuleSensitivityScoreV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyCandidateResolutionRuleSensitivityScoreV2Result(
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
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_resolution_rule_sensitivity_score_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_resolution_rule_sensitivity_score_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/strategy_candidate_resolution_rule_sensitivity_score_v2.py",
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
        "SCORE_STATUSES",
        "SCORE_DECISIONS",
        "SENSITIVITY_RANKS",
        "StrategyCandidateResolutionRuleSensitivityScoreV2Input",
        "StrategyCandidateResolutionRuleSensitivityScoreV2Result",
        "estimate_strategy_candidate_resolution_rule_sensitivity_score_v2",
        "strategy_candidate_resolution_rule_sensitivity_score_v2_payload",
        "reject_strategy_candidate_resolution_rule_sensitivity_score_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "strategy_candidate_resolution_rule_sensitivity_score_v2" not in getattr(
        root,
        "__all__",
        (),
    )
