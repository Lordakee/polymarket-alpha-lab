from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_scraping_quality_gate_report as api
from polymarket_alpha_lab.research_source_scraping_quality_gate_report import (
    ResearchSourceScrapingQualityGateConfig,
    ResearchSourceScrapingQualityGateReport,
    ResearchSourceScrapingQualityGateSnapshot,
    build_research_source_scraping_quality_gate_report,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _snapshot(
    *,
    candidate_count: Decimal = Decimal("3.000000"),
    covered_candidate_count: Decimal = Decimal("3.000000"),
    fresh_candidate_count: Decimal = Decimal("3.000000"),
    parsed_candidate_count: Decimal = Decimal("3.000000"),
    parse_confidence_sum: Decimal = Decimal("2.700000"),
    retrieval_attempt_count: Decimal = Decimal("6.000000"),
    retrieval_retry_count: Decimal = Decimal("0.000000"),
    evidence_complete_candidate_count: Decimal = Decimal("3.000000"),
) -> ResearchSourceScrapingQualityGateSnapshot:
    return ResearchSourceScrapingQualityGateSnapshot(
        candidate_count=candidate_count,
        covered_candidate_count=covered_candidate_count,
        fresh_candidate_count=fresh_candidate_count,
        parsed_candidate_count=parsed_candidate_count,
        parse_confidence_sum=parse_confidence_sum,
        retrieval_attempt_count=retrieval_attempt_count,
        retrieval_retry_count=retrieval_retry_count,
        evidence_complete_candidate_count=evidence_complete_candidate_count,
    )


def _report(
    snapshot: ResearchSourceScrapingQualityGateSnapshot,
    *,
    config: ResearchSourceScrapingQualityGateConfig | None = None,
) -> ResearchSourceScrapingQualityGateReport:
    return build_research_source_scraping_quality_gate_report(
        snapshot,
        config=config or ResearchSourceScrapingQualityGateConfig(),
        generated_at=NOW,
    )


def test_pass_report_uses_decimal_metrics_payload_and_stable_digest() -> None:
    report = _report(_snapshot())
    same_report = _report(_snapshot())
    retry_pressure_report = _report(
        _snapshot(retrieval_retry_count=Decimal("1.000000")),
    )

    assert report.gate_status == "pass"
    assert report.gate_next_step == "continue_candidate_research_scraping_review"
    assert report.reason_codes == ("scraping_quality_gate_pass",)
    assert report.candidate_count == Decimal("3.000000")
    assert report.coverage_ratio == Decimal("1.000000")
    assert report.freshness_ratio == Decimal("1.000000")
    assert report.parse_confidence_ratio == Decimal("0.900000")
    assert report.retry_pressure_ratio == Decimal("0.000000")
    assert report.evidence_completeness_ratio == Decimal("1.000000")
    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert report.derived_validation_digest != retry_pressure_report.derived_validation_digest

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["candidate_count"] == "3.000000"
    assert payload["parse_confidence_ratio"] == "0.900000"
    assert payload["retry_pressure_ratio"] == "0.000000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_watch_and_block_statuses_use_fixed_reason_order() -> None:
    watch_report = _report(
        _snapshot(
            candidate_count=Decimal("10.000000"),
            covered_candidate_count=Decimal("9.000000"),
            fresh_candidate_count=Decimal("6.000000"),
            parsed_candidate_count=Decimal("9.000000"),
            parse_confidence_sum=Decimal("7.500000"),
            retrieval_attempt_count=Decimal("10.000000"),
            retrieval_retry_count=Decimal("2.000000"),
            evidence_complete_candidate_count=Decimal("8.000000"),
        ),
    )

    block_report = _report(
        _snapshot(
            candidate_count=Decimal("10.000000"),
            covered_candidate_count=Decimal("4.000000"),
            fresh_candidate_count=Decimal("2.000000"),
            parsed_candidate_count=Decimal("5.000000"),
            parse_confidence_sum=Decimal("2.500000"),
            retrieval_attempt_count=Decimal("10.000000"),
            retrieval_retry_count=Decimal("7.000000"),
            evidence_complete_candidate_count=Decimal("3.000000"),
        ),
    )

    assert watch_report.gate_status == "watch"
    assert watch_report.reason_codes == (
        "freshness_below_pass_threshold",
        "retry_pressure_above_pass_threshold",
    )
    assert block_report.gate_status == "block"
    assert block_report.reason_codes == (
        "coverage_below_block_threshold",
        "parse_confidence_below_block_threshold",
        "retry_pressure_above_block_threshold",
        "evidence_completeness_below_block_threshold",
    )


def test_empty_snapshot_blocks_without_ratio_numbers() -> None:
    report = _report(
        _snapshot(
            candidate_count=Decimal("0.000000"),
            covered_candidate_count=Decimal("0.000000"),
            fresh_candidate_count=Decimal("0.000000"),
            parsed_candidate_count=Decimal("0.000000"),
            parse_confidence_sum=Decimal("0.000000"),
            retrieval_attempt_count=Decimal("0.000000"),
            retrieval_retry_count=Decimal("0.000000"),
            evidence_complete_candidate_count=Decimal("0.000000"),
        ),
    )

    assert report.gate_status == "block"
    assert report.reason_codes == ("empty_candidate_research_snapshot",)
    assert report.coverage_ratio is None
    assert report.freshness_ratio is None
    assert report.parse_confidence_ratio is None
    assert report.retry_pressure_ratio is None
    assert report.evidence_completeness_ratio is None


def test_dataclasses_flags_decimal_only_and_safe_public_surface() -> None:
    report = _report(_snapshot())

    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceScrapingQualityGateConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceScrapingQualityGateConfig(paper_only=False)

    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceScrapingQualityGateSnapshot(
            candidate_count=1,  # type: ignore[arg-type]
            covered_candidate_count=Decimal("1.000000"),
            fresh_candidate_count=Decimal("1.000000"),
            parsed_candidate_count=Decimal("1.000000"),
            parse_confidence_sum=Decimal("1.000000"),
            retrieval_attempt_count=Decimal("1.000000"),
            retrieval_retry_count=Decimal("0.000000"),
            evidence_complete_candidate_count=Decimal("1.000000"),
        )

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    forbidden_terms = (
        "raw_url",
        "source_text",
        "market_id",
        "question",
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
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        ResearchSourceScrapingQualityGateConfig,
        ResearchSourceScrapingQualityGateSnapshot,
        ResearchSourceScrapingQualityGateReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
