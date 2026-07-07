from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import (
    candidate_decision_falsifiability_score as falsifiability_module,
)
from polymarket_alpha_lab.candidate_decision_falsifiability_score import (
    CandidateDecisionFalsifiabilityScoreConfig,
    CandidateDecisionFalsifiabilityScoreInput,
    CandidateDecisionFalsifiabilityScoreResult,
    candidate_decision_falsifiability_score_payload,
    score_candidate_decision_falsifiability,
)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> CandidateDecisionFalsifiabilityScoreConfig:
    values = {
        "config_version": "candidate-decision-falsifiability-test-v0",
        "minimum_pass_score": d("0.800000"),
        "minimum_watch_score": d("0.550000"),
        "minimum_observable_condition_count": d("1"),
        "minimum_measurable_threshold_count": d("1"),
        "maximum_pass_subjective_clause_count": d("0"),
        "maximum_watch_subjective_clause_count": d("2"),
        "maximum_pass_oracle_dependency_score": d("0.300000"),
        "maximum_watch_oracle_dependency_score": d("0.600000"),
        "maximum_pass_dispute_risk_score": d("0.250000"),
        "maximum_watch_dispute_risk_score": d("0.600000"),
        "minimum_pass_evidence_verifiability_score": d("0.750000"),
        "minimum_watch_evidence_verifiability_score": d("0.500000"),
        "observable_condition_weight": d("0.200000"),
        "measurable_threshold_weight": d("0.200000"),
        "subjective_clause_weight": d("0.150000"),
        "oracle_dependency_weight": d("0.150000"),
        "dispute_risk_weight": d("0.150000"),
        "evidence_verifiability_weight": d("0.150000"),
    }
    values.update(overrides)
    return CandidateDecisionFalsifiabilityScoreConfig(**values)


def candidate(**overrides: object) -> CandidateDecisionFalsifiabilityScoreInput:
    values = {
        "redacted_candidate_ref": "candidate_ref_alpha",
        "observable_condition_count": d("2"),
        "measurable_threshold_count": d("2"),
        "subjective_clause_count": d("0"),
        "oracle_dependency_score": d("0.100000"),
        "dispute_risk_score": d("0.100000"),
        "evidence_verifiability_score": d("0.950000"),
    }
    values.update(overrides)
    return CandidateDecisionFalsifiabilityScoreInput(**values)


def score(
    candidate_state: CandidateDecisionFalsifiabilityScoreInput | object | None = None,
    score_config: CandidateDecisionFalsifiabilityScoreConfig | object | None = None,
) -> CandidateDecisionFalsifiabilityScoreResult:
    return score_candidate_decision_falsifiability(
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


def test_objective_candidate_scores_pass_for_falsifiability() -> None:
    result = score()

    assert result.config_version == "candidate-decision-falsifiability-test-v0"
    assert result.redacted_candidate_ref == "candidate_ref_alpha"
    assert result.status == "pass"
    assert result.observable_condition_score == d("1.000000")
    assert result.measurable_threshold_score == d("1.000000")
    assert result.subjective_clause_score == d("1.000000")
    assert result.oracle_dependency_component_score == d("0.900000")
    assert result.dispute_risk_component_score == d("0.900000")
    assert result.falsifiability_score == d("0.962500")
    assert result.reason_codes == (
        "candidate_decision_falsifiability_pass",
        "falsifiability_sufficient",
    )
    assert len(result.validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_subjective_clause_and_dispute_risk_block() -> None:
    result = score(
        candidate(
            subjective_clause_count=d("3"),
            dispute_risk_score=d("0.800000"),
        ),
    )

    assert result.status == "block"
    assert result.subjective_clause_score == d("0.000000")
    assert result.dispute_risk_component_score == d("0.200000")
    assert result.falsifiability_score == d("0.707500")
    assert result.reason_codes == (
        "candidate_decision_falsifiability_block",
        "subjective_clause_count_above_watch_limit",
        "dispute_risk_score_above_watch_limit",
    )


def test_oracle_dependency_watch() -> None:
    result = score(candidate(oracle_dependency_score=d("0.500000")))

    assert result.status == "watch"
    assert result.oracle_dependency_component_score == d("0.500000")
    assert result.falsifiability_score == d("0.902500")
    assert result.reason_codes == (
        "candidate_decision_falsifiability_watch",
        "oracle_dependency_score_above_pass_limit",
    )


def test_decimal_exact_type_rejection_and_frozen_outputs() -> None:
    result = score()

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="observable_condition_count must be a Decimal"):
        candidate(observable_condition_count=1)
    with pytest.raises(ValueError, match="measurable_threshold_count must be a Decimal"):
        candidate(measurable_threshold_count=DecimalSubclass("1"))
    with pytest.raises(ValueError, match="subjective_clause_count must be a whole Decimal"):
        candidate(subjective_clause_count=d("1.5"))
    with pytest.raises(ValueError, match="oracle_dependency_score must be a Decimal"):
        candidate(oracle_dependency_score=DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="dispute_risk_score must be a Decimal"):
        candidate(dispute_risk_score=0.1)
    with pytest.raises(ValueError, match="minimum_pass_score must be a Decimal"):
        config(minimum_pass_score=0.8)
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(evidence_verifiability_weight=d("0.100000"))
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
    payload = candidate_decision_falsifiability_score_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
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
        "position_sizing",
        "dsn",
        "table:",
        "source_ref",
        "source_text",
        "source_url",
    ):
        assert forbidden not in rendered

    with pytest.raises(ValueError, match="unsafe public payload"):
        falsifiability_module._reject_unsafe_public_payload(  # noqa: SLF001
            "test",
            {"market_slug": "candidate_ref_alpha"},
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

    first_payload = candidate_decision_falsifiability_score_payload(first)
    second_payload = candidate_decision_falsifiability_score_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["status"] == "pass"
    assert first_payload["minimum_pass_score"] == "0.800000"
    assert first_payload["minimum_watch_score"] == "0.550000"
    assert first_payload["observable_condition_count"] == "2"
    assert first_payload["oracle_dependency_weight"] == "0.150000"
    assert first_payload["falsifiability_score"] == "0.962500"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert json.dumps(first_payload, allow_nan=False, sort_keys=True)
    assert_no_float_values(first_payload)
    assert first_payload["status"] in {"pass", "watch", "block"}
    assert first_payload["status"] not in {"ready", "blocked", "matched", "supported"}

    with pytest.raises(ValueError, match="score_result must be"):
        candidate_decision_falsifiability_score_payload(object())


def test_report_consistency_rejects_tampering() -> None:
    result = score()

    with pytest.raises(ValueError, match="status"):
        replace(result, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(result, status="blocked")
    with pytest.raises(ValueError, match="observable_condition_score must match"):
        replace(result, observable_condition_score=d("0.500000"))
    with pytest.raises(ValueError, match="subjective_clause_score must match"):
        replace(result, subjective_clause_score=d("0.500000"))
    with pytest.raises(ValueError, match="oracle_dependency_component_score must match"):
        replace(result, oracle_dependency_component_score=d("0.500000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(result, reason_codes=("candidate_decision_falsifiability_pass",))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def test_public_api_and_static_surface_are_report_only() -> None:
    assert falsifiability_module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_FALSIFIABILITY_SCORE_CONFIG_VERSION",
        "CandidateDecisionFalsifiabilityScoreConfig",
        "CandidateDecisionFalsifiabilityScoreInput",
        "CandidateDecisionFalsifiabilityScoreResult",
        "score_candidate_decision_falsifiability",
        "candidate_decision_falsifiability_score_payload",
    )
    for exported_name in falsifiability_module.__all__:
        exported = getattr(falsifiability_module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    source = falsifiability_module.__loader__.get_source(  # type: ignore[union-attr]
        falsifiability_module.__name__,
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
        "source_ref",
        "source_text",
        "source_url",
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
        "CandidateDecisionFalsifiabilityScoreConfig",
        "CandidateDecisionFalsifiabilityScoreInput",
        "CandidateDecisionFalsifiabilityScoreResult",
    ):
        exported = getattr(falsifiability_module, class_name)
        for field in fields(exported):
            if field.name == "redacted_candidate_ref":
                continue
            assert not any(
                fragment in field.name.lower()
                for fragment in forbidden_public_field_fragments
            )
