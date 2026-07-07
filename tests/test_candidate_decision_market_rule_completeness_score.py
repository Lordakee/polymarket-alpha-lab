from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import (
    candidate_decision_market_rule_completeness_score as completeness_module,
)
from polymarket_alpha_lab.candidate_decision_market_rule_completeness_score import (
    CandidateDecisionMarketRuleCompletenessScoreConfig,
    CandidateDecisionMarketRuleCompletenessScoreInput,
    CandidateDecisionMarketRuleCompletenessScoreResult,
    candidate_decision_market_rule_completeness_score_payload,
    score_candidate_decision_market_rule_completeness,
)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> CandidateDecisionMarketRuleCompletenessScoreConfig:
    values = {
        "config_version": "candidate-decision-market-rule-completeness-test-v0",
        "minimum_pass_score": d("0.900000"),
        "minimum_watch_score": d("0.650000"),
        "minimum_rule_clause_count": d("2"),
        "minimum_boundary_condition_count": d("1"),
        "minimum_disqualifier_clause_count": d("1"),
        "minimum_settlement_source_count": d("1"),
        "maximum_contradiction_count": d("0"),
        "minimum_rule_specificity_score": d("0.700000"),
        "maximum_ambiguity_score": d("0.300000"),
        "rule_clause_weight": d("0.150000"),
        "boundary_condition_weight": d("0.150000"),
        "disqualifier_clause_weight": d("0.100000"),
        "settlement_source_weight": d("0.200000"),
        "contradiction_weight": d("0.150000"),
        "rule_specificity_weight": d("0.150000"),
        "ambiguity_weight": d("0.100000"),
    }
    values.update(overrides)
    return CandidateDecisionMarketRuleCompletenessScoreConfig(**values)


def candidate(**overrides: object) -> CandidateDecisionMarketRuleCompletenessScoreInput:
    values = {
        "redacted_candidate_ref": "candidate_ref_alpha",
        "rule_clause_count": d("4"),
        "boundary_condition_count": d("2"),
        "disqualifier_clause_count": d("1"),
        "settlement_source_count": d("1"),
        "contradiction_count": d("0"),
        "rule_specificity_score": d("0.900000"),
        "ambiguity_score": d("0.100000"),
    }
    values.update(overrides)
    return CandidateDecisionMarketRuleCompletenessScoreInput(**values)


def score(
    candidate_state: CandidateDecisionMarketRuleCompletenessScoreInput | object | None = None,
    score_config: CandidateDecisionMarketRuleCompletenessScoreConfig | object | None = None,
) -> CandidateDecisionMarketRuleCompletenessScoreResult:
    return score_candidate_decision_market_rule_completeness(
        candidate() if candidate_state is None else candidate_state,
        config() if score_config is None else score_config,
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


def test_complete_candidate_scores_pass_for_rule_completeness() -> None:
    result = score()

    assert result.config_version == "candidate-decision-market-rule-completeness-test-v0"
    assert result.redacted_candidate_ref == "candidate_ref_alpha"
    assert result.status == "pass"
    assert result.rule_clause_score == d("1.000000")
    assert result.boundary_condition_score == d("1.000000")
    assert result.disqualifier_clause_score == d("1.000000")
    assert result.settlement_source_score == d("1.000000")
    assert result.contradiction_score == d("1.000000")
    assert result.ambiguity_component_score == d("0.900000")
    assert result.market_rule_completeness_score == d("0.975000")
    assert result.reason_codes == (
        "candidate_decision_market_rule_completeness_pass",
        "market_rule_completeness_sufficient",
    )
    assert len(result.validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_contradiction_and_missing_settlement_source_block() -> None:
    result = score(
        candidate(
            settlement_source_count=d("0"),
            contradiction_count=d("1"),
            ambiguity_score=d("0.200000"),
        ),
    )

    assert result.status == "block"
    assert result.settlement_source_score == d("0.000000")
    assert result.contradiction_score == d("0.000000")
    assert result.market_rule_completeness_score == d("0.615000")
    assert result.reason_codes == (
        "candidate_decision_market_rule_completeness_block",
        "settlement_source_count_below_minimum",
        "contradiction_count_above_limit",
    )


def test_low_specificity_candidate_is_watch() -> None:
    result = score(
        candidate(
            rule_specificity_score=d("0.300000"),
            ambiguity_score=d("0.800000"),
        ),
    )

    assert result.status == "watch"
    assert result.market_rule_completeness_score == d("0.815000")
    assert result.reason_codes == (
        "candidate_decision_market_rule_completeness_watch",
        "rule_specificity_score_below_minimum",
        "ambiguity_score_above_limit",
    )


def test_decimal_exact_type_rejection_and_frozen_outputs() -> None:
    result = score()

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="rule_clause_count must be a Decimal"):
        candidate(rule_clause_count=1)
    with pytest.raises(ValueError, match="boundary_condition_count must be a Decimal"):
        candidate(boundary_condition_count=DecimalSubclass("1"))
    with pytest.raises(ValueError, match="disqualifier_clause_count must be a whole Decimal"):
        candidate(disqualifier_clause_count=d("1.5"))
    with pytest.raises(ValueError, match="rule_specificity_score must be a Decimal"):
        candidate(rule_specificity_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="ambiguity_score must be a Decimal"):
        candidate(ambiguity_score=0.1)
    with pytest.raises(ValueError, match="minimum_watch_score must be a Decimal"):
        config(minimum_watch_score=0.65)
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(ambiguity_weight=d("0.050000"))
    with pytest.raises(ValueError, match="candidate_state"):
        score(object())
    with pytest.raises(ValueError, match="config"):
        score(score_config=object())


def test_leak_rejection_for_redacted_reference_and_payload_surface() -> None:
    with pytest.raises(ValueError, match="unsafe public payload value"):
        candidate(redacted_candidate_ref="candidate_ref_secret_token")
    with pytest.raises(ValueError, match="redacted"):
        candidate(redacted_candidate_ref="raw-alpha")

    result = score()
    payload = candidate_decision_market_rule_completeness_score_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_slug",
        "question=",
        "http",
        "wallet",
        "token",
        "secret",
        "trade",
        "order",
        "buy",
        "sell",
        "recommendation",
        "position-size",
        "dsn",
        "table:",
    ):
        assert forbidden not in rendered

    with pytest.raises(ValueError, match="unsafe public payload"):
        completeness_module._reject_unsafe_public_payload(  # noqa: SLF001
            "test",
            {"candidate_id": "candidate_ref_alpha"},
        )


def test_hard_flags_are_enforced_on_public_dataclasses() -> None:
    result = score()

    for item in (
        config(paper_only=True),
        candidate(report_only=True),
        result,
    ):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        candidate(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_payload_is_deterministic_decimal_string_only_and_status_vocabulary() -> None:
    first = score()
    second = score()

    first_payload = candidate_decision_market_rule_completeness_score_payload(first)
    second_payload = candidate_decision_market_rule_completeness_score_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["status"] == "pass"
    assert first_payload["minimum_pass_score"] == "0.900000"
    assert first_payload["minimum_watch_score"] == "0.650000"
    assert first_payload["rule_clause_count"] == "4"
    assert first_payload["market_rule_completeness_score"] == "0.975000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert json.dumps(first_payload, allow_nan=False, sort_keys=True)
    assert_no_float_values(first_payload)
    assert first_payload["status"] in {"pass", "watch", "block"}
    assert first_payload["status"] not in {"ready", "blocked", "matched", "supported"}

    with pytest.raises(ValueError, match="score_result must be"):
        candidate_decision_market_rule_completeness_score_payload(object())


def test_report_consistency_rejects_tampering() -> None:
    result = score()

    with pytest.raises(ValueError, match="status"):
        replace(result, status="ready")
    with pytest.raises(ValueError, match="rule_clause_score must match"):
        replace(result, rule_clause_score=d("0.500000"))
    with pytest.raises(ValueError, match="ambiguity_component_score must match"):
        replace(result, ambiguity_component_score=d("0.500000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(result, reason_codes=("candidate_decision_market_rule_completeness_pass",))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def test_public_api_and_static_surface_are_report_only() -> None:
    assert completeness_module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_MARKET_RULE_COMPLETENESS_SCORE_CONFIG_VERSION",
        "CandidateDecisionMarketRuleCompletenessScoreConfig",
        "CandidateDecisionMarketRuleCompletenessScoreInput",
        "CandidateDecisionMarketRuleCompletenessScoreResult",
        "score_candidate_decision_market_rule_completeness",
        "candidate_decision_market_rule_completeness_score_payload",
    )
    for exported_name in completeness_module.__all__:
        exported = getattr(completeness_module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    source = completeness_module.__loader__.get_source(  # type: ignore[union-attr]
        completeness_module.__name__,
    )
    assert source is not None
    tree = ast.parse(source)

    forbidden_import_roots = {
        "boto3",
        "http",
        "httpx",
        "io",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "cancel",
        "commit",
        "connect",
        "execute",
        "executemany",
        "fetch",
        "input",
        "open",
        "order",
        "patch",
        "post",
        "print",
        "put",
        "read",
        "request",
        "submit",
        "trade",
        "urlopen",
        "write",
    }
    forbidden_public_field_fragments = {
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "raw",
        "table",
        "url",
        "wallet",
    }

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
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    for class_name in (
        "CandidateDecisionMarketRuleCompletenessScoreConfig",
        "CandidateDecisionMarketRuleCompletenessScoreInput",
        "CandidateDecisionMarketRuleCompletenessScoreResult",
    ):
        exported = getattr(completeness_module, class_name)
        for field in fields(exported):
            if field.name == "redacted_candidate_ref":
                continue
            assert not any(
                fragment in field.name.lower()
                for fragment in forbidden_public_field_fragments
            )
