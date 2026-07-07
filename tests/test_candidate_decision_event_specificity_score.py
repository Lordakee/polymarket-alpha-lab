from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_event_specificity_score"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "event_definition_specificity_score": d("0.700000"),
        "resolution_criteria_clarity_score": d("0.600000"),
        "measurable_outcome_score": d("0.700000"),
        "timeframe_specificity_score": d("0.500000"),
        "researchability_score": d("0.800000"),
        "threshold_precision_score": d("0.600000"),
        "ambiguity_risk_score": d("0.400000"),
        "reason_codes": ("event_scope_review_requested",),
    }
    values.update(overrides)
    return module.CandidateDecisionEventSpecificityScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.score_candidate_decision_event_specificity(
        score_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)


def test_pass_when_event_is_specific_decidable_and_researchable() -> None:
    result = score(
        score_input(
            event_definition_specificity_score=d("1.000000"),
            resolution_criteria_clarity_score=d("1.000000"),
            measurable_outcome_score=d("1.000000"),
            timeframe_specificity_score=d("1.000000"),
            researchability_score=d("1.000000"),
            threshold_precision_score=d("1.000000"),
            ambiguity_risk_score=d("0.000000"),
            reason_codes=(),
        ),
    )

    assert result.event_specificity_score == d("1.000000")
    assert result.score_status == "pass"
    assert result.component_gaps == ()
    assert result.reason_codes == (
        "event_specificity_score",
        "status_pass",
        "definition_specific",
        "criteria_decidable",
        "outcome_measurable",
        "timeframe_specific",
        "research_context_available",
        "threshold_precise",
        "ambiguity_low",
    )
    assert type(result.event_specificity_score) is Decimal


def test_watch_when_event_has_researchable_but_incomplete_definition() -> None:
    result = score()

    assert result.event_specificity_score == d("0.650000")
    assert result.score_status == "watch"
    assert result.component_gaps == (
        "resolution_criteria_clarity",
        "timeframe_specificity",
        "threshold_precision",
        "ambiguity_risk",
    )
    assert result.reason_codes == (
        "event_scope_review_requested",
        "event_specificity_score",
        "status_watch",
        "definition_specific",
        "criteria_unclear",
        "outcome_measurable",
        "timeframe_incomplete",
        "research_context_available",
        "threshold_imprecise",
        "ambiguity_elevated",
    )


def test_block_when_event_definition_is_not_actionably_researchable() -> None:
    result = score(
        score_input(
            event_definition_specificity_score=d("0.200000"),
            resolution_criteria_clarity_score=d("0.300000"),
            measurable_outcome_score=d("0.400000"),
            timeframe_specificity_score=d("0.200000"),
            researchability_score=d("0.300000"),
            threshold_precision_score=d("0.200000"),
            ambiguity_risk_score=d("0.900000"),
            reason_codes=(),
        ),
    )

    assert result.event_specificity_score == d("0.260000")
    assert result.score_status == "block"
    assert result.component_gaps == (
        "event_definition_specificity",
        "resolution_criteria_clarity",
        "measurable_outcome",
        "timeframe_specificity",
        "researchability",
        "threshold_precision",
        "ambiguity_risk",
    )
    assert "status_block" in result.reason_codes


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.CandidateDecisionEventSpecificityScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionEventSpecificityScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.reason_codes = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.score_status = "pass"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "event_specificity_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(
        ValueError,
        match="event_definition_specificity_score must be a Decimal",
    ):
        score_input(event_definition_specificity_score=1)
    with pytest.raises(ValueError, match="researchability_score must be a Decimal"):
        score_input(researchability_score=1.0)
    with pytest.raises(ValueError, match="ambiguity_risk_score must be a Decimal"):
        score_input(ambiguity_risk_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="threshold_precision_score must be between"):
        score_input(threshold_precision_score=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["event_scope_review_requested"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())


def test_public_payload_rejects_identifier_source_runtime_and_action_language() -> None:
    module = api()
    payload = score().payload
    serialized_strings = list(payload.keys())
    serialized_strings.extend(
        item
        for value in payload.values()
        for item in (value if isinstance(value, list) else [value])
        if isinstance(item, str)
    )

    forbidden_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "recommend",
    )
    for public_string in serialized_strings:
        lowered = public_string.lower()
        assert all(term not in lowered for term in forbidden_terms)

    for term in forbidden_terms:
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_candidate_decision_event_specificity_score_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_candidate_decision_event_specificity_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_payload_is_deterministic_json_ready_and_hard_flagged() -> None:
    module = api()
    first = score()
    second = score()

    assert first == second
    assert first.payload == second.payload
    assert first.event_specificity_digest == second.event_specificity_digest
    assert first.payload == module.candidate_decision_event_specificity_score_payload(
        first,
    )
    assert first.payload["score_status"] == "watch"
    assert first.payload["event_specificity_score"] == "0.650000"
    assert first.payload["component_gaps"] == [
        "resolution_criteria_clarity",
        "timeframe_specificity",
        "threshold_precision",
        "ambiguity_risk",
    ]
    assert first.payload["event_specificity_digest"] == first.event_specificity_digest
    assert first.payload["paper_only"] is True
    assert first.payload["report_only"] is True
    assert first.payload["readonly"] is True
    assert_no_float_or_int(first.payload)


def test_report_and_digest_consistency_are_enforced() -> None:
    module = api()
    result = score()

    rebuilt = module.CandidateDecisionEventSpecificityScoreReport(
        **public_field_values(result),
    )
    assert rebuilt == result

    with pytest.raises(ValueError, match="event_specificity_score must match"):
        replace(result, event_specificity_score=d("0.660000"))
    with pytest.raises(ValueError, match="score_status must match"):
        replace(result, score_status="pass")
    with pytest.raises(ValueError, match="component_gaps must match"):
        replace(result, component_gaps=())
    with pytest.raises(ValueError, match="event_specificity_digest"):
        module.CandidateDecisionEventSpecificityScoreReport(
            **{
                **public_field_values(result),
                "event_specificity_digest": "0" * 64,
            },
        )

    object.__setattr__(result, "event_specificity_digest", "0" * 64)
    with pytest.raises(ValueError, match="event_specificity_digest"):
        module.candidate_decision_event_specificity_score_payload(result)


def test_module_has_no_io_network_or_persistence_surface() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_event_specificity_score.py",
    ).read_text(encoding="utf-8")
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
    assert module.SCORE_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "SCORE_STATUSES",
        "CandidateDecisionEventSpecificityScoreInput",
        "CandidateDecisionEventSpecificityScoreReport",
        "score_candidate_decision_event_specificity",
        "candidate_decision_event_specificity_score_payload",
        "reject_candidate_decision_event_specificity_score_unsafe_payload",
    )
