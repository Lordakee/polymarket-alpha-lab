from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_evidence_traceability_score"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "redacted_candidate_ref": "redacted-candidate-alpha",
        "evidence_claim_count": d("5"),
        "traceable_claim_count": d("5"),
        "replayable_step_count": d("2"),
        "independent_review_count": d("2"),
        "unresolved_gap_count": d("0"),
        "cross_reference_ratio": d("1.000000"),
        "timestamp_coverage_ratio": d("1.000000"),
        "reason_codes": ("redacted_traceability_inputs_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionEvidenceTraceabilityScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.score_candidate_decision_evidence_traceability(
        score_input() if subject is None else subject,
    )


def report(*subjects: object):
    module = api()
    return module.build_candidate_decision_evidence_traceability_score_report(
        subjects or (score_input(),),
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_pass_status_for_fully_traceable_reviewable_evidence_chain() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionEvidenceTraceabilityScoreRow(
        config_version=module.DEFAULT_CONFIG_VERSION,
        redacted_candidate_ref="redacted-candidate-alpha",
        evidence_claim_count=d("5"),
        traceable_claim_count=d("5"),
        traceable_claim_ratio=d("1.000000"),
        replayable_step_count=d("2"),
        independent_review_count=d("2"),
        unresolved_gap_count=d("0"),
        cross_reference_ratio=d("1.000000"),
        timestamp_coverage_ratio=d("1.000000"),
        evidence_traceability_score=d("1.000000"),
        status="pass",
        safety_flags=module.SAFETY_FLAGS,
        reason_codes=(
            "redacted_traceability_inputs_present",
            "candidate_decision_evidence_traceability_score",
            "evidence_traceability_pass",
            "traceable_claim_ratio_pass",
            "replayable_step_count_pass",
            "independent_review_count_pass",
            "cross_reference_ratio_strong",
            "timestamp_coverage_ratio_strong",
            "traceability_score_pass_threshold_met",
        ),
        hard_flag_codes=(),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert type(result.evidence_traceability_score) is Decimal
    assert result.status in module.STATUS_VALUES
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_watch_status_for_partial_but_reviewable_traceability() -> None:
    result = score(
        score_input(
            redacted_candidate_ref="redacted-candidate-watch",
            evidence_claim_count=d("4"),
            traceable_claim_count=d("2"),
            replayable_step_count=d("1"),
            independent_review_count=d("1"),
            unresolved_gap_count=d("1"),
            cross_reference_ratio=d("0.600000"),
            timestamp_coverage_ratio=d("0.700000"),
            reason_codes=(),
        ),
    )

    assert result.traceable_claim_ratio == d("0.500000")
    assert result.evidence_traceability_score == d("0.535000")
    assert result.status == "watch"
    assert result.hard_flag_codes == ()
    assert result.reason_codes == (
        "candidate_decision_evidence_traceability_score",
        "evidence_traceability_watch",
        "traceable_claim_ratio_watch",
        "replayable_step_count_watch",
        "independent_review_count_watch",
        "cross_reference_ratio_moderate",
        "timestamp_coverage_ratio_strong",
        "traceability_score_between_watch_and_pass",
    )


def test_block_status_for_untraceable_or_unreviewable_chain() -> None:
    result = score(
        score_input(
            redacted_candidate_ref="redacted-candidate-block",
            evidence_claim_count=d("3"),
            traceable_claim_count=d("0"),
            replayable_step_count=d("0"),
            independent_review_count=d("0"),
            unresolved_gap_count=d("3"),
            cross_reference_ratio=d("0.200000"),
            timestamp_coverage_ratio=d("0.200000"),
            reason_codes=(),
        ),
    )

    assert result.traceable_claim_ratio == d("0.000000")
    assert result.evidence_traceability_score == d("0.000000")
    assert result.status == "block"
    assert result.hard_flag_codes == (
        "traceable_claim_count_block",
        "traceable_claim_ratio_block",
        "replayable_step_count_block",
        "independent_review_count_block",
        "unresolved_gap_count_block",
    )
    assert "hard_flag_present" in result.reason_codes


def test_decimal_type_rejection_and_frozen_hard_flags() -> None:
    module = api()
    subject = score_input()
    result = score(subject)
    aggregate = report(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert is_dataclass(aggregate)
    assert module.CandidateDecisionEvidenceTraceabilityScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionEvidenceTraceabilityScoreRow.__dataclass_params__.frozen
    assert module.CandidateDecisionEvidenceTraceabilityScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.redacted_candidate_ref = "redacted-candidate-other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        aggregate.block_count = d("9")  # type: ignore[misc]

    for instance in (subject, result, aggregate):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="evidence_claim_count must be a Decimal"):
        score_input(evidence_claim_count=5)
    with pytest.raises(ValueError, match="cross_reference_ratio must be a Decimal"):
        score_input(cross_reference_ratio=1.0)
    with pytest.raises(ValueError, match="timestamp_coverage_ratio must be an exact Decimal"):
        score_input(timestamp_coverage_ratio=DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="traceable_claim_count must not exceed"):
        score_input(traceable_claim_count=d("6"))
    with pytest.raises(ValueError, match="replayable_step_count must be integral"):
        score_input(replayable_step_count=d("1.500000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(aggregate, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())
    with pytest.raises(ValueError, match="candidates"):
        report(object())


def test_public_payload_leak_rejection() -> None:
    module = api()
    unsafe_terms = (
        "candidate_id",
        "raw_candidate",
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
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe|redacted"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe|redacted"):
            module.reject_candidate_decision_evidence_traceability_score_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe|redacted"):
            module.reject_candidate_decision_evidence_traceability_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )

    with pytest.raises(ValueError, match="redacted candidate ref"):
        score_input(redacted_candidate_ref="candidate-123")
    with pytest.raises(ValueError, match="safe redacted candidate ref"):
        score_input(redacted_candidate_ref="redacted-candidate-market_id-alpha")


def test_payload_digest_determinism_and_report_consistency() -> None:
    module = api()
    pass_input = score_input(redacted_candidate_ref="redacted-candidate-c")
    watch_input = score_input(
        redacted_candidate_ref="redacted-candidate-b",
        evidence_claim_count=d("4"),
        traceable_claim_count=d("2"),
        replayable_step_count=d("1"),
        independent_review_count=d("1"),
        unresolved_gap_count=d("1"),
        cross_reference_ratio=d("0.600000"),
        timestamp_coverage_ratio=d("0.700000"),
        reason_codes=(),
    )
    block_input = score_input(
        redacted_candidate_ref="redacted-candidate-a",
        evidence_claim_count=d("3"),
        traceable_claim_count=d("0"),
        replayable_step_count=d("0"),
        independent_review_count=d("0"),
        unresolved_gap_count=d("3"),
        cross_reference_ratio=d("0.200000"),
        timestamp_coverage_ratio=d("0.200000"),
        reason_codes=(),
    )

    first = score(pass_input)
    second = score(pass_input)
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.candidate_decision_evidence_traceability_score_payload(first) == first.payload
    assert first.payload["evidence_traceability_score"] == "1.000000"
    assert first.payload["status"] == "pass"
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    assert first.payload["paper_only"] is True
    assert first.payload["report_only"] is True
    assert first.payload["readonly"] is True
    assert_no_float_or_int_values(first.payload)

    aggregate = report(pass_input, watch_input, block_input)
    assert aggregate == module.CandidateDecisionEvidenceTraceabilityScoreReport(
        config_version=module.DEFAULT_CONFIG_VERSION,
        candidate_count=d("3"),
        pass_count=d("1"),
        watch_count=d("1"),
        block_count=d("1"),
        max_evidence_traceability_score=d("1.000000"),
        min_evidence_traceability_score=d("0.000000"),
        average_evidence_traceability_score=d("0.511667"),
        report_status="block",
        safety_flags=module.SAFETY_FLAGS,
        reason_codes=(
            "candidate_decision_evidence_traceability_score_report",
            "block_status_present",
            "watch_status_present",
            "pass_status_present",
        ),
        rows=aggregate.rows,
        derived_validation_digest=aggregate.derived_validation_digest,
    )
    assert tuple(row.redacted_candidate_ref for row in aggregate.rows) == (
        "redacted-candidate-a",
        "redacted-candidate-b",
        "redacted-candidate-c",
    )
    assert aggregate.payload == module.candidate_decision_evidence_traceability_score_payload(
        aggregate,
    )
    assert_no_float_or_int_values(aggregate.payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionEvidenceTraceabilityScoreRow(
            **{
                **public_field_values(first),
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionEvidenceTraceabilityScoreReport(
            **{
                **public_field_values(aggregate),
                "derived_validation_digest": "0" * 64,
            },
        )

    object.__setattr__(first, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_evidence_traceability_score_payload(first)


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_evidence_traceability_score.py",
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
        "candidate_id",
        "market_id",
        "market_slug",
        "source_ref",
        "source_url",
        "source_text",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "live",
        "network",
        "database",
        "persist",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
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
    assert module.STATUS_VALUES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_CONFIG_VERSION",
        "STATUS_VALUES",
        "SAFETY_FLAGS",
        "CandidateDecisionEvidenceTraceabilityScoreConfig",
        "CandidateDecisionEvidenceTraceabilityScoreInput",
        "CandidateDecisionEvidenceTraceabilityScoreRow",
        "CandidateDecisionEvidenceTraceabilityScoreReport",
        "score_candidate_decision_evidence_traceability",
        "build_candidate_decision_evidence_traceability_score_report",
        "candidate_decision_evidence_traceability_score_payload",
        "reject_candidate_decision_evidence_traceability_score_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "candidate_decision_evidence_traceability_score" not in getattr(root, "__all__", ())
