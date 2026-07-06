from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.strategy_candidate_resolution_dispute_risk_v10",
    )


def dispute_input(**overrides: Any):
    values: dict[str, Any] = {
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "outcome_name": "Yes",
        "ambiguous_rule_count": d("0.000000"),
        "source_authority_score": d("1.000000"),
        "conflicting_evidence_count": d("0.000000"),
        "resolution_dependency_count": d("0.000000"),
        "time_to_resolution_minutes": d("1440.000000"),
    }
    values.update(overrides)
    return api().StrategyCandidateResolutionDisputeRiskV10Input(**values)


def build(subject: object | None = None):
    return api().build_strategy_candidate_resolution_dispute_risk_v10(
        dispute_input() if subject is None else subject,
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


def test_clear_dispute_risk_candidate_uses_readonly_report_defaults() -> None:
    module = api()

    result = build()

    assert result == module.StrategyCandidateResolutionDisputeRiskV10Result(
        candidate_id="candidate-alpha",
        market_slug="market-alpha",
        outcome_name="Yes",
        ambiguous_rule_count=d("0.000000"),
        source_authority_score=d("1.000000"),
        conflicting_evidence_count=d("0.000000"),
        resolution_dependency_count=d("0.000000"),
        time_to_resolution_minutes=d("1440.000000"),
        ambiguous_rule_pressure=d("0.000000"),
        source_authority_weakness=d("0.000000"),
        conflicting_evidence_pressure=d("0.000000"),
        resolution_dependency_pressure=d("0.000000"),
        time_pressure=d("0.000000"),
        dispute_risk_score=d("0.000000"),
        dispute_risk_status="clear",
        recommended_action="continue_monitoring",
        required_followups=(),
        reason_codes=(
            "dispute_status_clear",
            "dispute_risk_clear",
            "resolution_window_sufficient",
        ),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    for value in (
        result.ambiguous_rule_count,
        result.source_authority_score,
        result.conflicting_evidence_count,
        result.resolution_dependency_count,
        result.time_to_resolution_minutes,
        result.dispute_risk_score,
    ):
        assert type(value) is Decimal


def test_elevated_dispute_risk_scores_ambiguity_authority_conflict_dependencies_and_time() -> None:
    result = build(
        dispute_input(
            candidate_id="candidate-elevated",
            ambiguous_rule_count=d("3.000000"),
            source_authority_score=d("0.400000"),
            conflicting_evidence_count=d("2.000000"),
            resolution_dependency_count=d("3.000000"),
            time_to_resolution_minutes=d("120.000000"),
        ),
    )

    assert result.ambiguous_rule_pressure == d("0.600000")
    assert result.source_authority_weakness == d("0.600000")
    assert result.conflicting_evidence_pressure == d("0.500000")
    assert result.resolution_dependency_pressure == d("0.600000")
    assert result.time_pressure == d("0.956522")
    assert result.dispute_risk_score == d("0.610652")
    assert result.dispute_risk_status == "elevated"
    assert result.recommended_action == "escalate_manual_review"
    assert result.required_followups == (
        "clarify_ambiguous_resolution_rules",
        "refresh_authoritative_resolution_source",
        "reconcile_conflicting_resolution_evidence",
        "confirm_resolution_dependencies",
        "complete_dispute_review_before_resolution",
    )
    assert result.reason_codes == (
        "dispute_status_elevated",
        "ambiguous_resolution_rules",
        "weak_source_authority",
        "conflicting_resolution_evidence",
        "resolution_dependencies_present",
        "resolution_window_near",
    )


def test_blocked_dispute_risk_clamps_when_all_dispute_inputs_are_extreme() -> None:
    result = build(
        dispute_input(
            candidate_id="candidate-blocked",
            ambiguous_rule_count=d("8.000000"),
            source_authority_score=d("0.000000"),
            conflicting_evidence_count=d("5.000000"),
            resolution_dependency_count=d("8.000000"),
            time_to_resolution_minutes=d("30.000000"),
        ),
    )

    assert result.ambiguous_rule_pressure == d("1.000000")
    assert result.source_authority_weakness == d("1.000000")
    assert result.conflicting_evidence_pressure == d("1.000000")
    assert result.resolution_dependency_pressure == d("1.000000")
    assert result.time_pressure == d("1.000000")
    assert result.dispute_risk_score == d("1.000000")
    assert result.dispute_risk_status == "blocked"
    assert result.recommended_action == "block_candidate_until_resolved"
    assert result.reason_codes == (
        "dispute_status_blocked",
        "ambiguous_resolution_rules_heavy",
        "weak_source_authority",
        "conflicting_evidence_heavy",
        "resolution_dependencies_heavy",
        "resolution_window_imminent",
    )


def test_dispute_risk_payload_is_report_only_and_preserves_decimal_values() -> None:
    module = api()
    result = build(
        dispute_input(
            candidate_id="candidate-payload",
            ambiguous_rule_count=d("1.000000"),
            source_authority_score=d("0.700000"),
            conflicting_evidence_count=d("1.000000"),
            resolution_dependency_count=d("0.000000"),
            time_to_resolution_minutes=d("360.000000"),
        ),
    )

    payload = module.strategy_candidate_resolution_dispute_risk_v10_payload(result)

    assert payload == result.payload
    assert payload["candidate_id"] == "candidate-payload"
    assert payload["ambiguous_rule_count"] == d("1.000000")
    assert payload["source_authority_score"] == d("0.700000")
    assert payload["dispute_risk_score"] == d("0.330435")
    assert payload["required_followups"] == [
        "clarify_ambiguous_resolution_rules",
        "refresh_authoritative_resolution_source",
        "reconcile_conflicting_resolution_evidence",
    ]
    assert payload["reason_codes"] == [
        "dispute_status_watch",
        "ambiguous_resolution_rules",
        "weak_source_authority",
        "conflicting_resolution_evidence",
        "resolution_window_near",
    ]
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_tamper_evident_digest_is_derived_and_rejects_identity_tampering() -> None:
    result = build(
        dispute_input(
            candidate_id="candidate-digest",
            ambiguous_rule_count=d("2.000000"),
            source_authority_score=d("0.600000"),
            conflicting_evidence_count=d("1.000000"),
            resolution_dependency_count=d("1.000000"),
            time_to_resolution_minutes=d("240.000000"),
        ),
    )

    assert type(result.derived_validation_digest) is str
    assert len(result.derived_validation_digest) == 64
    int(result.derived_validation_digest, 16)
    assert result.payload["derived_validation_digest"] == result.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, candidate_id="candidate-tampered")
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, derived_validation_digest="0" * 64)


def test_unsafe_payload_surface_rejection_blocks_live_execution_keys() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe live surface field"):
        module._payload_value({"safe": [{"wallet_address": "0xabc"}]})
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module._reject_unsafe_surface_fields("payload", {"submit_order_id": "order-1"})
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module._reject_unsafe_surface_fields("payload", {"api_key": "not-allowed"})


def test_validation_rejects_wrong_types_subclasses_bad_flags_and_mismatched_results() -> None:
    module = api()
    subject = dispute_input()
    result = build(subject)

    class InputSubclass(module.StrategyCandidateResolutionDisputeRiskV10Input):
        pass

    class ResultSubclass(module.StrategyCandidateResolutionDisputeRiskV10Result):
        pass

    with pytest.raises(FrozenInstanceError):
        subject.candidate_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.dispute_risk_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="candidate_id must"):
        dispute_input(candidate_id=" candidate-alpha ")
    with pytest.raises(ValueError, match="ambiguous_rule_count must be a Decimal"):
        dispute_input(ambiguous_rule_count=1)
    with pytest.raises(ValueError, match="ambiguous_rule_count must be nonnegative"):
        dispute_input(ambiguous_rule_count=d("-1.000000"))
    with pytest.raises(ValueError, match="ambiguous_rule_count must be a whole Decimal"):
        dispute_input(ambiguous_rule_count=d("1.500000"))
    with pytest.raises(ValueError, match="source_authority_score must be between"):
        dispute_input(source_authority_score=d("1.000001"))
    with pytest.raises(ValueError, match="conflicting_evidence_count must be a whole"):
        dispute_input(conflicting_evidence_count=d("0.500000"))
    with pytest.raises(ValueError, match="resolution_dependency_count must be nonnegative"):
        dispute_input(resolution_dependency_count=d("-0.000001"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be a Decimal"):
        dispute_input(time_to_resolution_minutes="1440.000000")
    with pytest.raises(ValueError, match="paper_only must be True"):
        dispute_input(paper_only=False)
    with pytest.raises(ValueError, match="candidate must be"):
        build(object())
    with pytest.raises(ValueError, match="candidate must be"):
        build(InputSubclass(**subject.__dict__))
    with pytest.raises(ValueError, match="result must be"):
        module.strategy_candidate_resolution_dispute_risk_v10_payload(object())
    with pytest.raises(ValueError, match="result must be"):
        ResultSubclass(**result.__dict__)
    with pytest.raises(ValueError, match="dispute_risk_score must match"):
        replace(result, dispute_risk_score=d("0.010000"))
    with pytest.raises(ValueError, match="recommended_action must match"):
        replace(result, recommended_action="refresh_resolution_evidence")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(result, reason_codes=("dispute_risk_clear",))
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, derived_validation_digest="f" * 64)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_module_is_pure_readonly_decimal_only_and_unwired_from_execution_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    lowered = source.lower()

    assert module.StrategyCandidateResolutionDisputeRiskV10Input.__dataclass_params__.frozen
    assert module.StrategyCandidateResolutionDisputeRiskV10Result.__dataclass_params__.frozen
    assert module.__all__ == (
        "DISPUTE_RISK_STATUSES",
        "RECOMMENDED_ACTIONS",
        "REASON_CODES",
        "REQUIRED_FOLLOWUPS",
        "StrategyCandidateResolutionDisputeRiskV10Input",
        "StrategyCandidateResolutionDisputeRiskV10Result",
        "build_strategy_candidate_resolution_dispute_risk_v10",
        "strategy_candidate_resolution_dispute_risk_v10_payload",
    )

    forbidden_import_roots = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    )
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "create_order",
        "open",
        "place_order",
        "read_text",
        "submit_order",
        "write_text",
    }
    assert "unsafe live surface field" in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert {name.split(".", 1)[0] for name in imported_modules}.isdisjoint(
        forbidden_import_roots,
    )
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
