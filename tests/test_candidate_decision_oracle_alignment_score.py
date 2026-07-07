from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_oracle_alignment_score"
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def facts(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "redacted_candidate_ref": "redacted-candidate-alpha",
        "public_evidence_alignment_score": d("0.950000"),
        "resolution_rule_alignment_score": d("0.900000"),
        "official_evidence_coverage_score": d("0.850000"),
        "resolver_consistency_score": d("0.900000"),
        "contradiction_risk_score": d("0.100000"),
        "ambiguity_risk_score": d("0.150000"),
        "evidence_observation_count": d("5"),
        "min_pass_oracle_alignment_score": d("0.750000"),
        "min_watch_oracle_alignment_score": d("0.500000"),
        "max_watch_contradiction_risk_score": d("0.400000"),
        "max_block_contradiction_risk_score": d("0.750000"),
        "max_watch_ambiguity_risk_score": d("0.450000"),
        "max_block_ambiguity_risk_score": d("0.800000"),
        "fact_set_version": "facts-v1",
        "reason_codes": ("redacted_public_evidence_reviewed",),
    }
    values.update(overrides)
    return module.CandidateDecisionOracleAlignmentFacts(**values)


def score(subject: object | None = None):
    module = api()
    return module.score_candidate_decision_oracle_alignment(
        facts() if subject is None else subject,
    )


def report(*items: object):
    module = api()
    return module.build_candidate_decision_oracle_alignment_report(items or (facts(),))


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


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


def test_scores_pass_watch_block_and_sorts_weakest_first() -> None:
    module = api()
    passed = facts(redacted_candidate_ref="redacted-candidate-c")
    watched = facts(
        redacted_candidate_ref="redacted-candidate-b",
        public_evidence_alignment_score=d("0.700000"),
        resolution_rule_alignment_score=d("0.700000"),
        official_evidence_coverage_score=d("0.650000"),
        resolver_consistency_score=d("0.650000"),
        reason_codes=(),
    )
    blocked = facts(
        redacted_candidate_ref="redacted-candidate-a",
        public_evidence_alignment_score=d("0.400000"),
        resolution_rule_alignment_score=d("0.450000"),
        official_evidence_coverage_score=d("0.400000"),
        resolver_consistency_score=d("0.450000"),
        contradiction_risk_score=d("0.850000"),
        reason_codes=(),
    )

    aggregate = report(passed, watched, blocked)

    assert aggregate == module.CandidateDecisionOracleAlignmentReport(
        result_count=d("3"),
        pass_count=d("1"),
        watch_count=d("1"),
        blocked_count=d("1"),
        min_oracle_alignment_score=d("0.422500"),
        average_oracle_alignment_score=d("0.670833"),
        max_contradiction_risk_score=d("0.850000"),
        max_ambiguity_risk_score=d("0.150000"),
        results=aggregate.results,
        fact_set_versions=(
            ("redacted-candidate-a", "facts-v1"),
            ("redacted-candidate-b", "facts-v1"),
            ("redacted-candidate-c", "facts-v1"),
        ),
        reason_codes=aggregate.reason_codes,
        derived_validation_digest=aggregate.derived_validation_digest,
    )
    assert tuple(row.redacted_candidate_ref for row in aggregate.results) == (
        "redacted-candidate-a",
        "redacted-candidate-b",
        "redacted-candidate-c",
    )
    assert tuple(row.support_status for row in aggregate.results) == (
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.oracle_alignment_score for row in aggregate.results) == (
        d("0.422500"),
        d("0.682500"),
        d("0.907500"),
    )
    assert aggregate.reason_codes == (
        "oracle_alignment_report_block",
        "contradiction_risk_block",
        "oracle_alignment_score_below_watch",
        "oracle_alignment_score_between_watch_and_pass",
        "oracle_alignment_pass",
    )
    assert aggregate.paper_only is True
    assert aggregate.report_only is True
    assert aggregate.readonly is True
    assert_sha256(aggregate.derived_validation_digest)


def test_result_payload_is_deterministic_redacted_and_decimal_stringed() -> None:
    module = api()
    first = score()
    second = score()

    assert first == second
    assert first.support_status == "pass"
    assert first.oracle_alignment_score == d("0.907500")
    assert first.reason_codes == (
        "redacted_public_evidence_reviewed",
        "candidate_decision_oracle_alignment_score",
        "support_pass",
        "public_evidence_alignment_pass",
        "resolution_rule_alignment_pass",
        "official_evidence_coverage_pass",
        "resolver_consistency_pass",
        "contradiction_risk_pass",
        "ambiguity_risk_pass",
        "oracle_alignment_pass",
    )
    assert first.blocker_codes == ()
    assert_sha256(first.derived_validation_digest)

    payload = first.payload
    assert payload == module.candidate_decision_oracle_alignment_payload(first)
    assert payload == second.payload
    assert payload["redacted_candidate_ref"] == "redacted-candidate-alpha"
    assert payload["oracle_alignment_score"] == "0.907500"
    assert payload["support_status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in rendered


def test_decimal_only_exact_type_frozen_and_hard_flags() -> None:
    module = api()
    subject = facts()
    result = score(subject)
    aggregate = report(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert is_dataclass(aggregate)
    assert module.CandidateDecisionOracleAlignmentFacts.__dataclass_params__.frozen
    assert module.CandidateDecisionOracleAlignmentResult.__dataclass_params__.frozen
    assert module.CandidateDecisionOracleAlignmentReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.redacted_candidate_ref = "redacted-candidate-other"  # type: ignore[misc]
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

    with pytest.raises(ValueError, match="public_evidence_alignment_score must be a Decimal"):
        facts(public_evidence_alignment_score=1)
    with pytest.raises(ValueError, match="resolution_rule_alignment_score must be a Decimal"):
        facts(resolution_rule_alignment_score=1.0)
    with pytest.raises(ValueError, match="official_evidence_coverage_score must be a Decimal"):
        facts(official_evidence_coverage_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="evidence_observation_count must be integral"):
        facts(evidence_observation_count=d("1.500000"))
    with pytest.raises(ValueError, match="min_watch_oracle_alignment_score must not exceed"):
        facts(
            min_pass_oracle_alignment_score=d("0.400000"),
            min_watch_oracle_alignment_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="max_watch_contradiction_risk_score must not exceed"):
        facts(
            max_watch_contradiction_risk_score=d("0.800000"),
            max_block_contradiction_risk_score=d("0.750000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        facts(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(aggregate, readonly=False)


def test_rejects_unsafe_public_payload_keys_values_and_refs() -> None:
    module = api()

    with pytest.raises(ValueError, match="redacted candidate"):
        facts(redacted_candidate_ref="raw-candidate-123")
    with pytest.raises(ValueError, match="safe redacted"):
        facts(redacted_candidate_ref="redacted-candidate-market_id-alpha")

    unsafe_terms = (
        "raw_candidate_id",
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
            facts(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe|redacted"):
            module.reject_candidate_decision_oracle_alignment_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe|redacted"):
            module.reject_candidate_decision_oracle_alignment_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_report_and_digest_consistency_rejects_tampering() -> None:
    module = api()
    result = score()
    aggregate = report(facts())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionOracleAlignmentResult(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionOracleAlignmentReport(
            **{
                **public_field_values(aggregate),
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="support_status"):
        module.CandidateDecisionOracleAlignmentResult(
            **{
                **public_field_values(result),
                "support_status": "watch",
                "derived_validation_digest": "",
            },
        )
    with pytest.raises(ValueError, match="average_oracle_alignment_score"):
        replace(aggregate, average_oracle_alignment_score=d("0.100000"))

    payload = aggregate.payload
    assert payload == module.candidate_decision_oracle_alignment_payload(aggregate)
    assert payload == report(facts()).payload
    assert payload["result_count"] == "1"
    assert payload["support_status"] == "pass"
    assert payload["results"][0]["support_status"] == "pass"
    assert_no_float_or_int_values(payload)

    object.__setattr__(aggregate, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_oracle_alignment_payload(aggregate)


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_oracle_alignment_score.py",
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
    assert module.SUPPORT_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "SUPPORT_STATUSES",
        "CandidateDecisionOracleAlignmentFacts",
        "CandidateDecisionOracleAlignmentResult",
        "CandidateDecisionOracleAlignmentReport",
        "score_candidate_decision_oracle_alignment",
        "build_candidate_decision_oracle_alignment_report",
        "candidate_decision_oracle_alignment_payload",
        "reject_candidate_decision_oracle_alignment_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "candidate_decision_oracle_alignment_score" not in getattr(root, "__all__", ())
