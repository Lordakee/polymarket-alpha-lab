from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_evidence_gap_score"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def fact(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "candidate_ref": "redacted-candidate-alpha",
        "official_resolution_source_count": d("2"),
        "required_official_resolution_source_count": d("2"),
        "market_terms_rule_count": d("3"),
        "required_market_terms_rule_count": d("3"),
        "fresh_data_point_count": d("4"),
        "required_fresh_data_point_count": d("4"),
        "contradiction_check_count": d("2"),
        "required_contradiction_check_count": d("2"),
        "base_rate_context_count": d("2"),
        "required_base_rate_context_count": d("2"),
        "specialist_review_count": d("2"),
        "required_specialist_review_count": d("2"),
        "minimum_pass_score_bps": d("550.000000"),
        "minimum_watch_score_bps": d("375.000000"),
        "reason_codes": ("redacted_candidate_facts_present",),
    }
    values.update(overrides)
    return module.CandidateDecisionEvidenceGapFacts(**values)


def score(subject: object | None = None):
    module = api()
    return module.score_candidate_decision_evidence_gap(
        fact() if subject is None else subject,
    )


def report(*facts: object):
    module = api()
    return module.build_candidate_decision_evidence_gap_report(
        facts or (fact(),),
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


def test_complete_redacted_evidence_supports_continued_research() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionEvidenceGapResult(
        candidate_ref="redacted-candidate-alpha",
        official_resolution_source_count=d("2"),
        required_official_resolution_source_count=d("2"),
        market_terms_rule_count=d("3"),
        required_market_terms_rule_count=d("3"),
        fresh_data_point_count=d("4"),
        required_fresh_data_point_count=d("4"),
        contradiction_check_count=d("2"),
        required_contradiction_check_count=d("2"),
        base_rate_context_count=d("2"),
        required_base_rate_context_count=d("2"),
        specialist_review_count=d("2"),
        required_specialist_review_count=d("2"),
        official_resolution_source_coverage_ratio=d("1.000000"),
        market_terms_rule_coverage_ratio=d("1.000000"),
        fresh_data_coverage_ratio=d("1.000000"),
        contradiction_check_coverage_ratio=d("1.000000"),
        base_rate_context_coverage_ratio=d("1.000000"),
        specialist_review_coverage_ratio=d("1.000000"),
        evidence_gap_count=d("0"),
        aggregate_evidence_score_bps=d("600.000000"),
        minimum_pass_score_bps=d("550.000000"),
        minimum_watch_score_bps=d("375.000000"),
        support_status="pass",
        support_decision="research_next",
        reason_codes=(
            "redacted_candidate_facts_present",
            "candidate_decision_evidence_gap_score",
            "support_pass",
            "official_resolution_source_coverage_met",
            "market_terms_rule_coverage_met",
            "fresh_data_coverage_met",
            "contradiction_check_coverage_met",
            "base_rate_context_coverage_met",
            "specialist_review_coverage_met",
            "minimum_pass_score_met",
        ),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert type(result.aggregate_evidence_score_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_partial_evidence_gap_is_watch_support() -> None:
    result = score(
        fact(
            official_resolution_source_count=d("1"),
            fresh_data_point_count=d("2"),
            contradiction_check_count=d("1"),
            base_rate_context_count=d("1"),
            specialist_review_count=d("1"),
            minimum_pass_score_bps=d("550.000000"),
            minimum_watch_score_bps=d("300.000000"),
            reason_codes=(),
        ),
    )

    assert result.official_resolution_source_coverage_ratio == d("0.500000")
    assert result.market_terms_rule_coverage_ratio == d("1.000000")
    assert result.fresh_data_coverage_ratio == d("0.500000")
    assert result.evidence_gap_count == d("6")
    assert result.aggregate_evidence_score_bps == d("350.000000")
    assert result.support_status == "watch"
    assert result.support_decision == "watch"
    assert result.reason_codes == (
        "candidate_decision_evidence_gap_score",
        "support_watch",
        "official_resolution_source_gap",
        "market_terms_rule_coverage_met",
        "fresh_data_gap",
        "contradiction_check_gap",
        "base_rate_context_gap",
        "specialist_review_gap",
        "score_between_watch_and_pass",
    )


def test_missing_official_resolution_and_terms_block_support() -> None:
    result = score(
        fact(
            official_resolution_source_count=d("0"),
            market_terms_rule_count=d("0"),
            fresh_data_point_count=d("1"),
            contradiction_check_count=d("0"),
            base_rate_context_count=d("0"),
            specialist_review_count=d("0"),
            minimum_pass_score_bps=d("550.000000"),
            minimum_watch_score_bps=d("200.000000"),
            reason_codes=(),
        ),
    )

    assert result.evidence_gap_count == d("14")
    assert result.aggregate_evidence_score_bps == d("25.000000")
    assert result.support_status == "block"
    assert result.support_decision == "block"
    assert result.blocker_codes == (
        "official_resolution_source_missing",
        "market_terms_rule_missing",
    )
    assert "support_block" in result.reason_codes
    assert "score_below_watch_threshold" in result.reason_codes


def test_report_sorts_results_by_status_severity_score_and_candidate_ref() -> None:
    module = api()
    pass_fact = fact(candidate_ref="redacted-candidate-c")
    watch_fact = fact(
        candidate_ref="redacted-candidate-b",
        official_resolution_source_count=d("1"),
        fresh_data_point_count=d("2"),
        contradiction_check_count=d("1"),
        base_rate_context_count=d("1"),
        specialist_review_count=d("1"),
        minimum_watch_score_bps=d("300.000000"),
        reason_codes=(),
    )
    block_fact = fact(
        candidate_ref="redacted-candidate-a",
        official_resolution_source_count=d("0"),
        market_terms_rule_count=d("0"),
        fresh_data_point_count=d("0"),
        contradiction_check_count=d("0"),
        base_rate_context_count=d("0"),
        specialist_review_count=d("0"),
        reason_codes=(),
    )

    aggregate = report(pass_fact, watch_fact, block_fact)

    assert aggregate == module.CandidateDecisionEvidenceGapReport(
        result_count=d("3"),
        pass_count=d("1"),
        watch_count=d("1"),
        blocked_count=d("1"),
        average_evidence_score_bps=d("316.666667"),
        max_evidence_gap_count=d("15"),
        results=aggregate.results,
        reason_codes=(
            "candidate_decision_evidence_gap_report",
            "blocked_support_present",
            "watch_support_present",
            "pass_support_present",
        ),
        derived_validation_digest=aggregate.derived_validation_digest,
    )
    assert tuple(row.candidate_ref for row in aggregate.results) == (
        "redacted-candidate-a",
        "redacted-candidate-b",
        "redacted-candidate-c",
    )
    assert tuple(row.support_status for row in aggregate.results) == (
        "block",
        "watch",
        "pass",
    )
    assert aggregate.paper_only is True
    assert aggregate.report_only is True
    assert aggregate.readonly is True


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.candidate_decision_evidence_gap_payload(result)
    assert payload["candidate_ref"] == "redacted-candidate-alpha"
    assert payload["aggregate_evidence_score_bps"] == "600.000000"
    assert payload["evidence_gap_count"] == "0"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    aggregate_payload = report(fact()).payload
    assert aggregate_payload["result_count"] == "1"
    assert aggregate_payload["results"][0]["candidate_ref"] == "redacted-candidate-alpha"
    assert_no_float_or_int_values(aggregate_payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_evidence_gap_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = fact()
    result = score(subject)
    aggregate = report(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert is_dataclass(aggregate)
    assert module.CandidateDecisionEvidenceGapFacts.__dataclass_params__.frozen
    assert module.CandidateDecisionEvidenceGapResult.__dataclass_params__.frozen
    assert module.CandidateDecisionEvidenceGapReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.candidate_ref = "other-ref"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.support_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        aggregate.blocked_count = d("9")  # type: ignore[misc]

    for instance in (subject, result, aggregate):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="official_resolution_source_count must be a Decimal"):
        fact(official_resolution_source_count=2)
    with pytest.raises(ValueError, match="candidate_ref must be a redacted"):
        fact(candidate_ref="https://example.invalid/market")
    with pytest.raises(ValueError, match="candidate_ref must be a redacted candidate"):
        fact(candidate_ref="redacted-public-alpha")
    with pytest.raises(ValueError, match="candidate_ref must be a safe redacted"):
        fact(candidate_ref="redacted-candidate-market_id-alpha")
    with pytest.raises(ValueError, match="fresh_data_point_count must be integral"):
        fact(fresh_data_point_count=d("1.500000"))
    with pytest.raises(ValueError, match="required_market_terms_rule_count must be positive"):
        fact(required_market_terms_rule_count=d("0"))
    with pytest.raises(ValueError, match="minimum_watch_score_bps must not exceed"):
        fact(minimum_pass_score_bps=d("100.000000"), minimum_watch_score_bps=d("101.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        fact(reason_codes=["redacted_candidate_facts_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        fact(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(aggregate, readonly=False)
    with pytest.raises(ValueError, match="facts"):
        score(object())
    with pytest.raises(ValueError, match="facts_list"):
        report(object())

    block_result = score(
        fact(
            official_resolution_source_count=d("0"),
            market_terms_rule_count=d("0"),
            fresh_data_point_count=d("1"),
            contradiction_check_count=d("0"),
            base_rate_context_count=d("0"),
            specialist_review_count=d("0"),
            minimum_watch_score_bps=d("200.000000"),
            reason_codes=(),
        ),
    )
    with pytest.raises(ValueError, match="support_status"):
        module.CandidateDecisionEvidenceGapResult(
            **{
                **public_field_values(block_result),
                "support_status": "blocked",
                "support_decision": "block",
                "derived_validation_digest": "",
            },
        )

    rebuilt_result = module.CandidateDecisionEvidenceGapResult(
        **public_field_values(result),
    )
    assert rebuilt_result == result
    rebuilt_report = module.CandidateDecisionEvidenceGapReport(
        **public_field_values(aggregate),
    )
    assert rebuilt_report == aggregate


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()
    aggregate = report(fact())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionEvidenceGapResult(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionEvidenceGapReport(
            **{
                **public_field_values(aggregate),
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
        "http",
        "slug",
        "question",
        "market_id",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe|redacted"):
            fact(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe|redacted"):
            module.reject_candidate_decision_evidence_gap_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe|redacted"):
            module.reject_candidate_decision_evidence_gap_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_evidence_gap_score.py",
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
    assert module.SUPPORT_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "SUPPORT_STATUSES",
        "SUPPORT_DECISIONS",
        "CandidateDecisionEvidenceGapFacts",
        "CandidateDecisionEvidenceGapResult",
        "CandidateDecisionEvidenceGapReport",
        "score_candidate_decision_evidence_gap",
        "build_candidate_decision_evidence_gap_report",
        "candidate_decision_evidence_gap_payload",
        "reject_candidate_decision_evidence_gap_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "candidate_decision_evidence_gap_score" not in getattr(root, "__all__", ())
