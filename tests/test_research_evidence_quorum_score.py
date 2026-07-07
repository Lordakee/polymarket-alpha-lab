from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from json import dumps
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_evidence_quorum_score"


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def aggregate(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "candidate_public_ref": "candidate-public-ref-001",
        "official_source_count": d("1"),
        "independent_source_count": d("4"),
        "contradiction_count": d("0"),
        "stale_source_count": d("0"),
        "source_family_concentration": d("0.250000"),
        "evidence_freshness_score": d("0.900000"),
        "resolution_rule_coverage_score": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchEvidenceQuorumPacketAggregate(**values)


def score(*items: object):
    module = api()
    return module.score_research_evidence_quorum(
        tuple(items) if items else (aggregate(),),
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


def test_scores_pass_watch_and_block_rows_with_deterministic_sorting() -> None:
    report = score(
        aggregate(
            candidate_public_ref="candidate-public-ref-003",
            official_source_count=d("0"),
            independent_source_count=d("1"),
            contradiction_count=d("1"),
            source_family_concentration=d("0.800000"),
            evidence_freshness_score=d("0.400000"),
            resolution_rule_coverage_score=d("0.450000"),
        ),
        aggregate(
            candidate_public_ref="candidate-public-ref-001",
            official_source_count=d("1"),
            independent_source_count=d("4"),
            contradiction_count=d("0"),
            stale_source_count=d("0"),
            source_family_concentration=d("0.250000"),
            evidence_freshness_score=d("0.900000"),
            resolution_rule_coverage_score=d("0.900000"),
        ),
        aggregate(
            candidate_public_ref="candidate-public-ref-002",
            official_source_count=d("1"),
            independent_source_count=d("2"),
            contradiction_count=d("0"),
            stale_source_count=d("1"),
            source_family_concentration=d("0.600000"),
            evidence_freshness_score=d("0.700000"),
            resolution_rule_coverage_score=d("0.700000"),
        ),
    )

    assert tuple(row.candidate_public_ref for row in report.rows) == (
        "candidate-public-ref-001",
        "candidate-public-ref-002",
        "candidate-public-ref-003",
    )
    assert report.candidate_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.reason_codes == (
        "research_evidence_quorum_passed",
        "missing_official_source",
        "insufficient_independent_sources",
        "source_contradictions_present",
        "stale_sources_present",
        "source_family_concentration_high",
        "evidence_freshness_low",
        "resolution_rule_coverage_low",
        "quorum_support_watch_score",
        "quorum_support_block_score",
    )

    passed, watched, blocked = report.rows
    assert passed.quorum_support_score == d("0.915000")
    assert passed.quorum_support == "pass"
    assert passed.reason_codes == ("research_evidence_quorum_passed",)

    assert watched.quorum_support_score == d("0.641667")
    assert watched.quorum_support == "watch"
    assert watched.reason_codes == (
        "insufficient_independent_sources",
        "stale_sources_present",
        "source_family_concentration_high",
        "evidence_freshness_low",
        "resolution_rule_coverage_low",
        "quorum_support_watch_score",
    )

    assert blocked.quorum_support_score == d("0.000000")
    assert blocked.quorum_support == "block"
    assert blocked.reason_codes == (
        "missing_official_source",
        "insufficient_independent_sources",
        "source_contradictions_present",
        "source_family_concentration_high",
        "evidence_freshness_low",
        "resolution_rule_coverage_low",
        "quorum_support_block_score",
    )


def test_payloads_are_public_safe_json_ready_and_digest_checked() -> None:
    module = api()
    report = score()
    row = report.rows[0]

    payload = report.payload
    dumps(payload, sort_keys=True)
    assert payload == module.research_evidence_quorum_score_payload(report)
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["candidate_public_ref"] == "candidate-public-ref-001"
    assert payload["rows"][0]["official_source_count"] == "1"
    assert payload["rows"][0]["quorum_support_score"] == "0.915000"
    assert payload["rows"][0]["reason_codes"] == ["research_evidence_quorum_passed"]
    assert payload["rows"][0]["derived_validation_digest"] == row.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    object.__setattr__(row, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_evidence_quorum_score_row_payload(row)

    with pytest.raises(ValueError, match="unsafe"):
        module.reject_research_evidence_quorum_score_unsafe_payload(
            "unsafe public value",
            {"candidate_public_ref": "https://example.invalid/path"},
        )


def test_report_payload_rejects_stale_nested_row_digest() -> None:
    module = api()
    report = score()
    row = report.rows[0]

    object.__setattr__(row, "quorum_support_score", d("0.000000"))

    with pytest.raises(ValueError, match="row derived_validation_digest"):
        module.research_evidence_quorum_score_payload(report)


def test_payloads_reject_digest_current_but_inconsistent_row_fields() -> None:
    module = api()
    report = score()
    row = report.rows[0]

    object.__setattr__(row, "quorum_support_score", d("0.000000"))
    object.__setattr__(row, "derived_validation_digest", module._row_digest(row))
    object.__setattr__(report, "derived_validation_digest", module._report_digest(report))

    with pytest.raises(ValueError, match="quorum_support_score"):
        module.research_evidence_quorum_score_row_payload(row)
    with pytest.raises(ValueError, match="quorum_support_score"):
        module.research_evidence_quorum_score_payload(report)


def test_public_payload_rejects_sensitive_research_and_execution_terms() -> None:
    module = api()

    for unsafe_value in (
        "api_key=secret-token",
        "postgres_dsn=alpha_lab",
        "research_source_table",
        "recommendation=hold",
        "position_size=0.250000",
    ):
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            module.reject_research_evidence_quorum_score_unsafe_payload(
                "public payload",
                {"aggregate_note": unsafe_value},
            )


def test_public_payload_rejects_raw_numeric_values() -> None:
    module = api()

    for raw_numeric in (0.5, 1):
        with pytest.raises(ValueError, match="public payload numeric values"):
            module.reject_research_evidence_quorum_score_unsafe_payload(
                "public payload",
                {"score": raw_numeric},
            )


def test_dataclasses_are_frozen_decimal_only_and_validate_public_inputs() -> None:
    module = api()
    subject = aggregate()
    report = score(subject)
    row = report.rows[0]

    for instance in (subject, row, report):
        assert is_dataclass(instance)
        assert instance.__dataclass_params__.frozen
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(FrozenInstanceError):
        subject.official_source_count = d("2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.quorum_support = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="official_source_count must be a Decimal"):
        aggregate(official_source_count=1)
    with pytest.raises(ValueError, match="evidence_freshness_score must be a Decimal"):
        aggregate(evidence_freshness_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="independent_source_count must be integral"):
        aggregate(independent_source_count=d("2.500000"))
    with pytest.raises(ValueError, match="source_family_concentration must be between"):
        aggregate(source_family_concentration=d("1.000001"))
    with pytest.raises(ValueError, match="evidence_freshness_score must use"):
        aggregate(evidence_freshness_score=d("0.9000001"))
    with pytest.raises(ValueError, match="candidate_public_ref must be public-safe"):
        aggregate(candidate_public_ref="https://example.invalid/raw-question")
    with pytest.raises(ValueError, match="candidate_public_ref must be public-safe"):
        aggregate(candidate_public_ref="candidate-market-slug-question-001")
    with pytest.raises(ValueError, match="paper_only must be True"):
        aggregate(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="aggregates must be a tuple"):
        module.score_research_evidence_quorum([subject])
    with pytest.raises(ValueError, match="aggregate must be"):
        module.score_research_evidence_quorum((object(),))

    rebuilt_row = module.ResearchEvidenceQuorumScoreRow(**public_field_values(row))
    rebuilt_report = module.ResearchEvidenceQuorumScoreReport(
        **public_field_values(report),
    )
    assert rebuilt_row == row
    assert rebuilt_report == report


def test_module_exports_and_runtime_surface_stay_phase_one_pure() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "boto3",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "getenv",
        "open",
        "request",
        "urlopen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float

    lowered = source.lower()
    for token in (
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "wallet",
    ):
        assert token not in lowered

    assert module.__all__ == (
        "QUORUM_SUPPORT_LEVELS",
        "RESEARCH_EVIDENCE_QUORUM_REASON_CODES",
        "ResearchEvidenceQuorumPacketAggregate",
        "ResearchEvidenceQuorumScoreRow",
        "ResearchEvidenceQuorumScoreReport",
        "score_research_evidence_quorum",
        "research_evidence_quorum_score_row_payload",
        "research_evidence_quorum_score_payload",
        "reject_research_evidence_quorum_score_unsafe_payload",
    )
