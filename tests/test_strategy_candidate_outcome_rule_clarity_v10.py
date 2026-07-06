from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import (
    strategy_candidate_outcome_rule_clarity_v10 as clarity_module,
)
from polymarket_alpha_lab.strategy_candidate_outcome_rule_clarity_v10 import (
    StrategyCandidateOutcomeRuleClarityConfig,
    StrategyCandidateOutcomeRuleClarityInput,
    StrategyCandidateOutcomeRuleClarityScore,
    score_strategy_candidate_outcome_rule_clarity_v10,
    strategy_candidate_outcome_rule_clarity_v10_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyCandidateOutcomeRuleClarityConfig:
    values = {
        "config_version": "strategy-candidate-outcome-rule-clarity-test-v10",
        "minimum_clear_score": d("0.750000"),
        "minimum_watch_score": d("0.500000"),
        "minimum_source_authority_score": d("0.700000"),
        "minimum_adjudication_dependency_score": d("0.700000"),
        "maximum_ambiguity_count": d("4"),
        "maximum_days_to_resolution": d("84.000000"),
        "measurable_criteria_weight": d("0.300000"),
        "source_authority_weight": d("0.250000"),
        "ambiguity_weight": d("0.200000"),
        "adjudication_dependency_weight": d("0.150000"),
        "time_to_resolution_weight": d("0.100000"),
    }
    values.update(overrides)
    return StrategyCandidateOutcomeRuleClarityConfig(**values)


def candidate(**overrides: object) -> StrategyCandidateOutcomeRuleClarityInput:
    values = {
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "measurable_criteria_count": d("4"),
        "required_measurable_criteria_count": d("4"),
        "source_authority_score": d("0.900000"),
        "ambiguity_count": d("1"),
        "adjudication_dependency_score": d("0.800000"),
        "days_to_resolution": d("21.000000"),
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return StrategyCandidateOutcomeRuleClarityInput(**values)


def score(
    candidate_state: StrategyCandidateOutcomeRuleClarityInput | object | None = None,
    strategy_config: StrategyCandidateOutcomeRuleClarityConfig | object | None = None,
) -> StrategyCandidateOutcomeRuleClarityScore:
    return score_strategy_candidate_outcome_rule_clarity_v10(
        candidate_state or candidate(),
        strategy_config or config(),
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


def test_clear_candidate_scores_rule_clarity_components() -> None:
    result = score()

    assert result.config_version == "strategy-candidate-outcome-rule-clarity-test-v10"
    assert result.candidate_id == "candidate-001"
    assert result.market_slug == "fed-cuts-by-september"
    assert result.outcome_name == "Yes"
    assert result.clarity_status == "clear"
    assert result.measurable_criteria_score == d("1.000000")
    assert result.source_authority_score == d("0.900000")
    assert result.ambiguity_score == d("0.750000")
    assert result.adjudication_dependency_score == d("0.800000")
    assert result.time_to_resolution_score == d("0.750000")
    assert result.outcome_rule_clarity_score == d("0.870000")
    assert result.reason_codes == (
        "strategy_candidate_outcome_rule_clarity_clear",
        "candidate_screened",
        "outcome_rule_clarity_sufficient",
    )
    assert len(result.validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_unclear_candidate_reports_each_rule_clarity_blocker() -> None:
    result = score(
        candidate(
            measurable_criteria_count=d("1"),
            source_authority_score=d("0.400000"),
            ambiguity_count=d("5"),
            adjudication_dependency_score=d("0.500000"),
            days_to_resolution=d("100.000000"),
        ),
    )

    assert result.clarity_status == "unclear"
    assert result.measurable_criteria_score == d("0.250000")
    assert result.ambiguity_score == d("0.000000")
    assert result.time_to_resolution_score == d("0.000000")
    assert result.outcome_rule_clarity_score == d("0.250000")
    assert result.reason_codes == (
        "strategy_candidate_outcome_rule_clarity_unclear",
        "candidate_screened",
        "measurable_criteria_below_required",
        "source_authority_below_minimum",
        "ambiguity_count_above_limit",
        "adjudication_dependency_below_minimum",
        "time_to_resolution_above_limit",
    )


def test_watch_candidate_when_composite_is_mid_quality() -> None:
    result = score(
        candidate(
            measurable_criteria_count=d("3"),
            source_authority_score=d("0.700000"),
            ambiguity_count=d("2"),
            adjudication_dependency_score=d("0.700000"),
            days_to_resolution=d("42.000000"),
        ),
    )

    assert result.clarity_status == "watch"
    assert result.outcome_rule_clarity_score == d("0.655000")
    assert result.reason_codes == (
        "strategy_candidate_outcome_rule_clarity_watch",
        "candidate_screened",
        "measurable_criteria_below_required",
    )


def test_outputs_are_frozen_typed_decimal_quantized_tuple_only_and_readonly() -> None:
    candidate_state = candidate(source_authority_score=d("0.9000001"))
    result = score(candidate_state)

    assert candidate_state.source_authority_score == d("0.900000")
    assert type(result.outcome_rule_clarity_score) is Decimal
    assert type(result.reason_codes) is tuple
    with pytest.raises(FrozenInstanceError):
        result.clarity_status = "unclear"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        replace(candidate_state, source_authority_score=0.9)
    with pytest.raises(ValueError, match="measurable_criteria_count must be a Decimal"):
        replace(candidate_state, measurable_criteria_count=1)
    with pytest.raises(ValueError, match="required_measurable_criteria_count must be positive"):
        replace(candidate_state, required_measurable_criteria_count=d("0"))
    with pytest.raises(ValueError, match="ambiguity_count must be nonnegative"):
        replace(candidate_state, ambiguity_count=d("-1"))
    with pytest.raises(ValueError, match="days_to_resolution must be nonnegative"):
        replace(candidate_state, days_to_resolution=d("-1.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(candidate_state, reason_codes=["candidate_screened"])
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(candidate_state, reason_codes=("candidate_screened", "candidate_screened"))
    with pytest.raises(ValueError, match="clarity_status"):
        replace(result, clarity_status="ready")
    with pytest.raises(ValueError, match="measurable_criteria_score must match criteria counts"):
        replace(result, measurable_criteria_score=d("0.500000"))
    with pytest.raises(ValueError, match="validation_digest must match score_result"):
        replace(result, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_rejects_wrong_public_types_subclasses_and_bad_config() -> None:
    class CandidateSubclass(StrategyCandidateOutcomeRuleClarityInput):
        pass

    with pytest.raises(ValueError, match="candidate_state"):
        score(object())
    with pytest.raises(ValueError, match="candidate_state"):
        score(CandidateSubclass(**candidate().__dict__))
    with pytest.raises(ValueError, match="config"):
        score(strategy_config=object())
    with pytest.raises(ValueError, match="minimum_watch_score"):
        config(minimum_watch_score=d("0.760000"))
    with pytest.raises(ValueError, match="maximum_ambiguity_count must be positive"):
        config(maximum_ambiguity_count=d("0"))
    with pytest.raises(ValueError, match="maximum_days_to_resolution must be positive"):
        config(maximum_days_to_resolution=d("0.000000"))
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(time_to_resolution_weight=d("0.050000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)


def test_payload_uses_decimal_strings_flags_and_no_floats() -> None:
    result = score()

    payload = strategy_candidate_outcome_rule_clarity_v10_payload(result)

    assert payload == {
        "config_version": "strategy-candidate-outcome-rule-clarity-test-v10",
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "clarity_status": "clear",
        "measurable_criteria_count": "4",
        "required_measurable_criteria_count": "4",
        "measurable_criteria_score": "1.000000",
        "source_authority_score": "0.900000",
        "ambiguity_count": "1",
        "ambiguity_score": "0.750000",
        "adjudication_dependency_score": "0.800000",
        "days_to_resolution": "21.000000",
        "time_to_resolution_score": "0.750000",
        "outcome_rule_clarity_score": "0.870000",
        "validation_digest": result.validation_digest,
        "reason_codes": [
            "strategy_candidate_outcome_rule_clarity_clear",
            "candidate_screened",
            "outcome_rule_clarity_sufficient",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="score_result must be"):
        strategy_candidate_outcome_rule_clarity_v10_payload(object())


def test_payload_revalidates_digest_and_rejects_unsafe_public_payload() -> None:
    result = score()

    with pytest.raises(ValueError, match="validation_digest must match score_result"):
        strategy_candidate_outcome_rule_clarity_v10_payload(
            replace(result, validation_digest="0" * 64),
        )

    unsafe_result = score(candidate(candidate_id="candidate-wallet-surface"))
    with pytest.raises(ValueError, match="unsafe payload"):
        strategy_candidate_outcome_rule_clarity_v10_payload(unsafe_result)


def test_module_is_pure_and_has_no_network_db_order_or_io_surface() -> None:
    source = inspect.getsource(clarity_module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "order",
        "trade",
    }
    forbidden_attr_fragments = (
        "api_key",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "token",
        "trade",
        "wallet",
        "write",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
