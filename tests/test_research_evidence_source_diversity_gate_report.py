from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_evidence_source_diversity_gate_report as api
from polymarket_alpha_lab.research_evidence_source_diversity_gate_report import (
    ResearchEvidenceSourceDiversityGateConfig,
    ResearchEvidenceSourceDiversityGateInput,
    ResearchEvidenceSourceDiversityGateReport,
    build_research_evidence_source_diversity_gate_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _inputs(
    *,
    aggregate_source_count: Decimal = d("8.000000"),
    independent_source_class_count: Decimal = d("4.000000"),
    stale_source_count: Decimal = d("1.000000"),
    contradiction_count: Decimal = d("2.000000"),
    covered_contradiction_count: Decimal = d("2.000000"),
) -> ResearchEvidenceSourceDiversityGateInput:
    return ResearchEvidenceSourceDiversityGateInput(
        aggregate_source_count=aggregate_source_count,
        independent_source_class_count=independent_source_class_count,
        stale_source_count=stale_source_count,
        contradiction_count=contradiction_count,
        covered_contradiction_count=covered_contradiction_count,
    )


def _report(
    inputs: ResearchEvidenceSourceDiversityGateInput | None = None,
    *,
    config: ResearchEvidenceSourceDiversityGateConfig | None = None,
) -> ResearchEvidenceSourceDiversityGateReport:
    return build_research_evidence_source_diversity_gate_report(
        inputs or _inputs(),
        generated_at=NOW,
        config=config,
    )


def test_status_vocabulary_is_exact() -> None:
    assert api.RESEARCH_EVIDENCE_SOURCE_DIVERSITY_GATE_STATUSES == (
        "pass",
        "watch",
        "block",
    )


def test_diverse_fresh_contradiction_covered_research_passes() -> None:
    report = _report()

    assert report.gate_status == "pass"
    assert report.check_count == d("3.000000")
    assert report.passed_check_count == d("3.000000")
    assert report.watch_check_count == d("0.000000")
    assert report.blocked_check_count == d("0.000000")
    assert report.aggregate_source_count == d("8.000000")
    assert report.independent_source_class_count == d("4.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.stale_source_concentration_ratio == d("0.125000")
    assert report.contradiction_count == d("2.000000")
    assert report.covered_contradiction_count == d("2.000000")
    assert report.contradiction_coverage_ratio == d("1.000000")
    assert report.reason_codes == (
        "independent_source_classes_pass",
        "stale_source_concentration_pass",
        "contradiction_coverage_pass",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_near_miss_research_watches_without_blocking() -> None:
    report = _report(
        _inputs(
            aggregate_source_count=d("6.000000"),
            independent_source_class_count=d("2.000000"),
            stale_source_count=d("3.000000"),
            contradiction_count=d("2.000000"),
            covered_contradiction_count=d("1.000000"),
        ),
    )

    assert report.gate_status == "watch"
    assert report.passed_check_count == d("0.000000")
    assert report.watch_check_count == d("3.000000")
    assert report.blocked_check_count == d("0.000000")
    assert report.stale_source_concentration_ratio == d("0.500000")
    assert report.contradiction_coverage_ratio == d("0.500000")
    assert report.reason_codes == (
        "independent_source_classes_watch",
        "stale_source_concentration_watch",
        "contradiction_coverage_watch",
    )


def test_insufficient_aggregate_diversity_blocks_safe_gate_status() -> None:
    report = _report(
        _inputs(
            aggregate_source_count=d("4.000000"),
            independent_source_class_count=d("1.000000"),
            stale_source_count=d("3.000000"),
            contradiction_count=d("2.000000"),
            covered_contradiction_count=d("0.000000"),
        ),
    )

    assert report.gate_status == "block"
    assert report.passed_check_count == d("0.000000")
    assert report.watch_check_count == d("0.000000")
    assert report.blocked_check_count == d("3.000000")
    assert report.stale_source_concentration_ratio == d("0.750000")
    assert report.contradiction_coverage_ratio == d("0.000000")
    assert report.reason_codes == (
        "independent_source_classes_block",
        "stale_source_concentration_block",
        "contradiction_coverage_block",
    )


def test_zero_contradictions_are_fully_covered_for_gate_math() -> None:
    report = _report(_inputs(contradiction_count=d("0.000000")))

    assert report.contradiction_count == d("0.000000")
    assert report.covered_contradiction_count == d("0.000000")
    assert report.contradiction_coverage_ratio == d("1.000000")
    assert "contradiction_coverage_pass" in report.reason_codes


def test_payload_is_deterministic_json_ready_decimal_only_and_tamper_evident() -> None:
    first = _report()
    second = _report()

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    json.dumps(first.payload, sort_keys=True)
    assert first.payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert first.payload["aggregate_source_count"] == "8.000000"
    assert first.payload["stale_source_concentration_ratio"] == "0.125000"
    assert first.payload["contradiction_coverage_ratio"] == "1.000000"
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    assert isinstance(first.derived_validation_digest, str)
    assert len(first.derived_validation_digest) == 64
    _assert_no_non_decimal_public_numbers(first)
    _assert_no_decimal_objects(first.payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, independent_source_class_count=d("5.000000"))


def test_dataclasses_are_frozen_decimal_only_and_validate_aggregate_relationships() -> None:
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchEvidenceSourceDiversityGateConfig):
            pass

    with pytest.raises(TypeError):

        class BadInput(ResearchEvidenceSourceDiversityGateInput):
            pass

    with pytest.raises(ValueError, match="aggregate_source_count must be a Decimal"):
        _inputs(aggregate_source_count=8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="independent_source_class_count cannot exceed"):
        _inputs(independent_source_class_count=d("9.000000"))

    with pytest.raises(ValueError, match="stale_source_count cannot exceed"):
        _inputs(stale_source_count=d("9.000000"))

    with pytest.raises(ValueError, match="covered_contradiction_count cannot exceed"):
        _inputs(covered_contradiction_count=d("3.000000"))

    with pytest.raises(ValueError, match="paper_only"):
        ResearchEvidenceSourceDiversityGateConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        ResearchEvidenceSourceDiversityGateInput(
            aggregate_source_count=d("8.000000"),
            independent_source_class_count=d("4.000000"),
            stale_source_count=d("1.000000"),
            contradiction_count=d("2.000000"),
            covered_contradiction_count=d("2.000000"),
            readonly=False,
        )


def test_no_raw_candidate_market_source_content_or_action_surfaces_are_exposed() -> None:
    forbidden_public_fragments = (
        "url",
        "uri",
        "text",
        "market_id",
        "market_slug",
        "question",
        "candidate_id",
        "candidate_slug",
        "source_id",
        "source_ref",
        "source_reference",
        "source_locator",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    for cls in (
        ResearchEvidenceSourceDiversityGateConfig,
        ResearchEvidenceSourceDiversityGateInput,
        ResearchEvidenceSourceDiversityGateReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    payload = _report().payload
    _assert_payload_has_no_forbidden_public_surface(payload)

    source = Path(
        "src/polymarket_alpha_lab/research_evidence_source_diversity_gate_report.py",
    ).read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "private_key",
        "live_trading",
        "submit",
        "cancel",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _assert_no_non_decimal_public_numbers(value: Any) -> None:
    if isinstance(value, Decimal):
        return
    if isinstance(value, float) or type(value) is int:
        raise AssertionError("public numerics must be Decimal values")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_non_decimal_public_numbers(item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _assert_no_decimal_objects(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload must expose Decimal values as strings")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_payload_has_no_forbidden_public_surface(value: Any) -> None:
    forbidden = (
        "url",
        "uri",
        "text",
        "market_id",
        "market_slug",
        "question",
        "candidate_id",
        "candidate_slug",
        "source_id",
        "source_ref",
        "source_reference",
        "source_locator",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(fragment in lowered for fragment in forbidden)
            _assert_payload_has_no_forbidden_public_surface(item)
    elif isinstance(value, list):
        for item in value:
            _assert_payload_has_no_forbidden_public_surface(item)
