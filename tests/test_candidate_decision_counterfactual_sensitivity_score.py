from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.candidate_decision_counterfactual_sensitivity_score"
)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_COUNTERFACTUAL_SENSITIVITY_SCORE_CONFIG_VERSION
        ),
        "max_pass_dominant_assumption_weight": d("0.450000"),
        "max_watch_dominant_assumption_weight": d("0.650000"),
        "max_pass_scenario_dispersion_score": d("0.350000"),
        "max_watch_scenario_dispersion_score": d("0.650000"),
        "max_pass_downside_sensitivity_score": d("0.350000"),
        "max_watch_downside_sensitivity_score": d("0.650000"),
        "min_pass_independent_driver_count": d("3"),
        "min_watch_independent_driver_count": d("2"),
        "min_pass_evidence_support_score": d("0.750000"),
        "min_watch_evidence_support_score": d("0.450000"),
        "dominant_assumption_weight_weight": d("0.350000"),
        "scenario_dispersion_weight": d("0.250000"),
        "downside_sensitivity_weight": d("0.250000"),
        "driver_concentration_weight": d("0.100000"),
        "evidence_gap_weight": d("0.050000"),
        "min_pass_counterfactual_resilience_score": d("0.700000"),
        "min_watch_counterfactual_resilience_score": d("0.400000"),
    }
    values.update(overrides)
    return module.CandidateDecisionCounterfactualSensitivityScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values = {
        "redacted_candidate_ref": "redacted-cf-alpha-001",
        "assumption_count": d("5"),
        "dominant_assumption_weight": d("0.300000"),
        "scenario_dispersion_score": d("0.200000"),
        "downside_sensitivity_score": d("0.250000"),
        "independent_driver_count": d("4"),
        "evidence_support_score": d("0.850000"),
    }
    values.update(overrides)
    return module.CandidateDecisionCounterfactualSensitivityScoreInput(**values)


def score(subject: object | None = None, *, cfg: object | None = None):
    module = api()
    return module.score_candidate_decision_counterfactual_sensitivity(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_public_json_scalars(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected raw Decimal value {value!r}")
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_public_json_scalars(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_json_scalars(item)


def test_diversified_counterfactual_thesis_passes() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionCounterfactualSensitivityScoreReport(
        config_version=(
            "candidate-decision-counterfactual-sensitivity-score-v0"
        ),
        redacted_candidate_ref="redacted-cf-alpha-001",
        assumption_count=d("5.000000"),
        dominant_assumption_weight=d("0.300000"),
        scenario_dispersion_score=d("0.200000"),
        downside_sensitivity_score=d("0.250000"),
        independent_driver_count=d("4.000000"),
        evidence_support_score=d("0.850000"),
        driver_diversification_score=d("0.800000"),
        driver_concentration_score=d("0.200000"),
        evidence_gap_score=d("0.150000"),
        counterfactual_fragility_score=d("0.245000"),
        counterfactual_resilience_score=d("0.755000"),
        status="pass",
        hard_flag_codes=(),
        reason_codes=(
            "candidate_decision_counterfactual_sensitivity_score",
            "status_pass",
            "dominant_assumption_weight_pass",
            "scenario_dispersion_score_pass",
            "downside_sensitivity_score_pass",
            "independent_driver_count_pass",
            "evidence_support_score_pass",
            "counterfactual_resilience_score_pass",
            "hard_flags_absent",
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64
    assert result.payload == (
        module.candidate_decision_counterfactual_sensitivity_score_payload(result)
    )


def test_dominant_assumption_blocks_with_hard_flag() -> None:
    result = score(
        score_input(
            dominant_assumption_weight=d("0.750000"),
            scenario_dispersion_score=d("0.250000"),
            downside_sensitivity_score=d("0.250000"),
            evidence_support_score=d("0.800000"),
        ),
    )

    assert result.counterfactual_fragility_score == d("0.417500")
    assert result.counterfactual_resilience_score == d("0.582500")
    assert result.status == "block"
    assert result.hard_flag_codes == ("dominant_assumption_weight_hard_flag",)
    assert "dominant_assumption_weight_block" in result.reason_codes
    assert "hard_flags_present" in result.reason_codes


def test_high_scenario_dispersion_watches_without_hard_flag() -> None:
    result = score(score_input(scenario_dispersion_score=d("0.500000")))

    assert result.counterfactual_fragility_score == d("0.320000")
    assert result.counterfactual_resilience_score == d("0.680000")
    assert result.status == "watch"
    assert result.hard_flag_codes == ()
    assert "scenario_dispersion_score_watch" in result.reason_codes
    assert "counterfactual_resilience_score_watch" in result.reason_codes


def test_decimal_exact_type_rejection() -> None:
    with pytest.raises(ValueError, match="assumption_count must be a Decimal"):
        score_input(assumption_count=5)
    with pytest.raises(ValueError, match="dominant_assumption_weight must be a Decimal"):
        score_input(dominant_assumption_weight=0.3)
    with pytest.raises(ValueError, match="evidence_support_score must be an exact Decimal"):
        score_input(evidence_support_score=DecimalSubclass("0.850000"))
    with pytest.raises(ValueError, match="assumption_count must be a whole Decimal"):
        score_input(assumption_count=d("5.500000"))
    with pytest.raises(ValueError, match="independent_driver_count must not exceed"):
        score_input(independent_driver_count=d("6"))
    with pytest.raises(ValueError, match="scenario_dispersion_weight must be an exact Decimal"):
        config(scenario_dispersion_weight=DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="config weights must sum to 1"):
        config(evidence_gap_weight=d("0.060000"))


def test_leak_rejection_for_public_identifiers_sources_and_execution_terms() -> None:
    module = api()
    payload = score().payload

    with pytest.raises(ValueError, match="unsafe"):
        score_input(redacted_candidate_ref="candidate_id-alpha")
    with pytest.raises(ValueError, match="unsafe"):
        score_input(redacted_candidate_ref="https://example.invalid/raw")

    unsafe_payloads = (
        {"candidate_id": "candidate-123"},
        {"market_id": "market-123"},
        {"market_slug": "will-event-resolve"},
        {"market_question": "Will this event resolve?"},
        {"source_ref": "source-123"},
        {"source_url": "https://example.invalid/source"},
        {"source_text": "raw source text"},
        {"dsn": "postgresql://example.invalid/db"},
        {"table_name": "candidate_scores"},
        {"secret_token": "redacted"},
        {"status_note": "wallet"},
        {"status_note": "auth"},
        {"status_note": "order"},
        {"status_note": "trade"},
        {"status_note": "buy"},
        {"status_note": "sell"},
        {"status_note": "recommendation"},
        {"status_note": "position-sizing"},
        {"diagnostic_count": 1},
    )
    for extra_payload in unsafe_payloads:
        with pytest.raises(ValueError):
            module.validate_candidate_decision_counterfactual_sensitivity_public_payload(
                {**payload, **extra_payload},
            )


def test_hard_flags_and_safety_flags_are_enforced() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    result = score(subject, cfg=cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.CandidateDecisionCounterfactualSensitivityScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionCounterfactualSensitivityScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionCounterfactualSensitivityScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.assumption_count = d("6")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    multi_flag = score(
        score_input(
            scenario_dispersion_score=d("0.800000"),
            downside_sensitivity_score=d("0.900000"),
            independent_driver_count=d("1"),
            evidence_support_score=d("0.300000"),
        ),
    )
    assert multi_flag.status == "block"
    assert multi_flag.hard_flag_codes == (
        "scenario_dispersion_score_hard_flag",
        "downside_sensitivity_score_hard_flag",
        "independent_driver_count_hard_flag",
        "evidence_support_score_hard_flag",
    )

    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.CandidateDecisionCounterfactualSensitivityScoreConfig(
            **{**public_values(cfg), "readonly": False},
        )
    with pytest.raises(ValueError, match="input_value"):
        score(object())
    with pytest.raises(ValueError, match="config"):
        score(subject, cfg=object())


def test_deterministic_payload_has_only_safe_status_words_and_json_scalars() -> None:
    first = score()
    second = score()

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.payload == second.payload
    assert json.dumps(first.payload, allow_nan=False, sort_keys=True) == json.dumps(
        second.payload,
        allow_nan=False,
        sort_keys=True,
    )

    payload = first.payload
    assert payload["assumption_count"] == "5.000000"
    assert payload["dominant_assumption_weight"] == "0.300000"
    assert payload["counterfactual_fragility_score"] == "0.245000"
    assert payload["counterfactual_resilience_score"] == "0.755000"
    assert payload["status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_public_json_scalars(payload)

    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "secret",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position-sizing",
        "position_size",
        "ready",
        "blocked",
        "matched",
        "supported",
    ):
        assert forbidden not in rendered


def test_report_consistency_is_validated() -> None:
    module = api()
    result = score()

    rebuilt = module.CandidateDecisionCounterfactualSensitivityScoreReport(
        **public_values(result),
    )
    assert rebuilt == result

    with pytest.raises(ValueError, match="counterfactual_fragility_score"):
        replace(result, counterfactual_fragility_score=d("0.250000"))
    with pytest.raises(ValueError, match="counterfactual_resilience_score"):
        replace(result, counterfactual_resilience_score=d("0.700000"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("candidate_decision_counterfactual_sensitivity_score",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionCounterfactualSensitivityScoreReport(
            **{**public_values(result), "derived_validation_digest": "0" * 64},
        )
    with pytest.raises(ValueError, match="max_pass_dominant_assumption_weight"):
        config(max_pass_dominant_assumption_weight=d("0.700000"))
    with pytest.raises(ValueError, match="min_watch_independent_driver_count"):
        config(min_watch_independent_driver_count=d("4"))
    with pytest.raises(ValueError, match="min_watch_evidence_support_score"):
        config(min_watch_evidence_support_score=d("0.800000"))


def test_module_has_report_only_boundary_no_io_or_live_surface_and_no_float_literals() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered = source.lower()
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
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "private_key",
        "secret_token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "dsn",
        "table_name",
        "position_size",
        "position-sizing",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "open(",
        "path(",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "exchange",
        "ready",
        "blocked",
        "matched",
        "supported",
    ):
        assert forbidden not in lowered

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_COUNTERFACTUAL_SENSITIVITY_SCORE_CONFIG_VERSION",
        "COUNTERFACTUAL_SENSITIVITY_STATUSES",
        "CandidateDecisionCounterfactualSensitivityScoreConfig",
        "CandidateDecisionCounterfactualSensitivityScoreInput",
        "CandidateDecisionCounterfactualSensitivityScoreReport",
        "score_candidate_decision_counterfactual_sensitivity",
        "candidate_decision_counterfactual_sensitivity_score_payload",
        "validate_candidate_decision_counterfactual_sensitivity_public_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "candidate_decision_counterfactual_sensitivity_score" not in getattr(
        root,
        "__all__",
        (),
    )
