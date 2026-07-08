from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_source_scrapling_extraction_quality_gate_report as api
from polymarket_alpha_lab.research_source_scrapling_extraction_quality_gate_report import (
    ResearchSourceScraplingExtractionOutput,
    ResearchSourceScraplingExtractionQualityGateConfig,
    ResearchSourceScraplingExtractionQualityGateReport,
    build_research_source_scrapling_extraction_quality_gate_report,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _output(
    extraction_scope: str = "macro-calendar",
    *,
    extracted_at: datetime | None = None,
    required_field_count: Decimal = d("10.000000"),
    extracted_field_count: Decimal = d("10.000000"),
    selector_expected_count: Decimal = d("4.000000"),
    selector_match_count: Decimal = d("4.000000"),
    conflict_count: Decimal = d("0.000000"),
    fallback_attempt_count: Decimal = d("4.000000"),
    fallback_success_count: Decimal = d("4.000000"),
) -> ResearchSourceScraplingExtractionOutput:
    return ResearchSourceScraplingExtractionOutput(
        extraction_scope=extraction_scope,
        extracted_at=extracted_at or GENERATED_AT - timedelta(minutes=30),
        required_field_count=required_field_count,
        extracted_field_count=extracted_field_count,
        selector_expected_count=selector_expected_count,
        selector_match_count=selector_match_count,
        conflict_count=conflict_count,
        fallback_attempt_count=fallback_attempt_count,
        fallback_success_count=fallback_success_count,
    )


def _report(
    outputs: tuple[ResearchSourceScraplingExtractionOutput, ...],
    *,
    config: ResearchSourceScraplingExtractionQualityGateConfig | None = None,
) -> ResearchSourceScraplingExtractionQualityGateReport:
    return build_research_source_scrapling_extraction_quality_gate_report(
        outputs,
        config=config or ResearchSourceScraplingExtractionQualityGateConfig(),
        generated_at=GENERATED_AT,
    )


def test_extraction_quality_scoring_builds_pass_watch_and_block_rows() -> None:
    report = _report(
        (
            _output(
                "macro-calendar-pass",
                extracted_field_count=d("9.000000"),
            ),
            _output(
                "macro-calendar-watch",
                extracted_field_count=d("8.000000"),
                conflict_count=d("2.000000"),
                fallback_success_count=d("2.000000"),
            ),
            _output(
                "macro-calendar-block",
                extracted_at=GENERATED_AT - timedelta(hours=8),
                extracted_field_count=d("4.000000"),
                selector_match_count=d("1.000000"),
                conflict_count=d("2.000000"),
                fallback_success_count=d("1.000000"),
            ),
        ),
    )

    assert report.status == "block"
    assert report.extraction_scope_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_extraction_quality_score == d("0.673333")
    assert report.lowest_extraction_quality_score == d("0.280000")
    assert report.highest_conflict_risk_ratio == d("0.500000")
    assert report.max_freshness_age_seconds == d("28800.000000")

    pass_row, watch_row, block_row = report.rows
    assert pass_row.extraction_scope == "macro-calendar-block"
    assert pass_row.status == "block"
    assert pass_row.extraction_completeness_ratio == d("0.400000")
    assert pass_row.source_freshness_score == d("0.000000")
    assert pass_row.selector_stability_ratio == d("0.250000")
    assert pass_row.conflict_risk_ratio == d("0.500000")
    assert pass_row.fallback_coverage_ratio == d("0.250000")
    assert pass_row.extraction_quality_score == d("0.280000")
    assert pass_row.reason_codes == (
        "scrapling_extraction_quality_gate_block",
        "extraction_completeness_below_block_threshold",
        "source_freshness_below_block_threshold",
        "selector_stability_below_block_threshold",
        "conflict_risk_above_block_threshold",
        "fallback_coverage_below_block_threshold",
    )

    assert watch_row.extraction_scope == "macro-calendar-pass"
    assert watch_row.status == "pass"
    assert watch_row.extraction_quality_score == d("0.980000")
    assert watch_row.reason_codes == ("scrapling_extraction_quality_gate_pass",)

    assert block_row.extraction_scope == "macro-calendar-watch"
    assert block_row.status == "watch"
    assert block_row.extraction_quality_score == d("0.760000")
    assert block_row.reason_codes == (
        "scrapling_extraction_quality_gate_watch",
        "extraction_completeness_below_pass_threshold",
        "conflict_risk_above_pass_threshold",
        "fallback_coverage_below_pass_threshold",
    )


def test_fallback_status_boundaries_are_pass_watch_then_block() -> None:
    config = ResearchSourceScraplingExtractionQualityGateConfig(
        min_fallback_coverage_pass_ratio=d("0.750000"),
        min_fallback_coverage_block_ratio=d("0.500000"),
    )

    pass_report = _report(
        (
            _output(
                fallback_success_count=d("3.000000"),
                fallback_attempt_count=d("4.000000"),
            ),
        ),
        config=config,
    )
    watch_report = _report(
        (
            _output(
                fallback_success_count=d("2.000000"),
                fallback_attempt_count=d("4.000000"),
            ),
        ),
        config=config,
    )
    block_report = _report(
        (
            _output(
                fallback_success_count=d("1.000000"),
                fallback_attempt_count=d("4.000000"),
            ),
        ),
        config=config,
    )

    assert pass_report.rows[0].fallback_coverage_ratio == d("0.750000")
    assert pass_report.rows[0].status == "pass"
    assert watch_report.rows[0].fallback_coverage_ratio == d("0.500000")
    assert watch_report.rows[0].status == "watch"
    assert watch_report.rows[0].reason_codes == (
        "scrapling_extraction_quality_gate_watch",
        "fallback_coverage_below_pass_threshold",
    )
    assert block_report.rows[0].fallback_coverage_ratio == d("0.250000")
    assert block_report.rows[0].status == "block"
    assert block_report.rows[0].reason_codes == (
        "scrapling_extraction_quality_gate_block",
        "fallback_coverage_below_block_threshold",
    )


def test_deterministic_payload_digest_and_tamper_validation() -> None:
    report = _report((_output(),))
    same_report = _report((_output(),))
    changed_report = _report((_output(extracted_field_count=d("9.000000")),))

    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert report.derived_validation_digest != changed_report.derived_validation_digest

    payload = api.research_source_scrapling_extraction_quality_gate_report_payload(report)
    assert payload == report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["extraction_scope_count"] == "1.000000"
    assert payload["average_extraction_quality_score"] == "1.000000"
    assert payload["rows"][0]["fallback_coverage_ratio"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    tampered_payload = dict(payload)
    tampered_payload["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.research_source_scrapling_extraction_quality_gate_report_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_payload_prevents_sensitive_surface_leaks() -> None:
    report = _report((_output(),))
    payload = api.research_source_scrapling_extraction_quality_gate_report_payload(report)
    forbidden_fragments = (
        "candidate_id",
        "candidate-id",
        "market_id",
        "market-id",
        "market_slug",
        "market-slug",
        "source_url",
        "source-url",
        "source_text",
        "source-text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "http://",
        "https://",
        "www.",
    )

    for public_name in (*api.__all__, *_walk_strings(payload)):
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ResearchSourceScraplingExtractionQualityGateConfig,
        ResearchSourceScraplingExtractionOutput,
        api.ResearchSourceScraplingExtractionQualityGateRow,
        ResearchSourceScraplingExtractionQualityGateReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    with pytest.raises(ValueError, match="unsafe public"):
        _output(extraction_scope="market_slug_123")
    with pytest.raises(ValueError, match="unsafe public"):
        _output(extraction_scope="https://example.test/research")

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["source_url"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public field"):
        api.research_source_scrapling_extraction_quality_gate_report_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["review_note"] = "wallet order trade"
    with pytest.raises(ValueError, match="unsafe public value"):
        api.research_source_scrapling_extraction_quality_gate_report_payload(
            unsafe_value_payload,
        )

    source_text = Path(api.__file__).read_text(encoding="utf-8")
    for forbidden_import in (
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
        assert forbidden_import not in source_text
        assert not hasattr(api, forbidden_import)


def test_custom_config_validation_flags_and_decimal_only_contract() -> None:
    config = ResearchSourceScraplingExtractionQualityGateConfig()
    output = _output()

    with pytest.raises(FrozenInstanceError):
        config.min_extraction_completeness_pass_ratio = d("0.800000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        output.extracted_field_count = d("9.000000")  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceScraplingExtractionQualityGateConfig):
            pass

    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceScraplingExtractionQualityGateConfig(
            min_extraction_completeness_pass_ratio=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceScraplingExtractionQualityGateConfig(paper_only=False)
    with pytest.raises(ValueError, match="must not exceed pass threshold"):
        ResearchSourceScraplingExtractionQualityGateConfig(
            min_fallback_coverage_pass_ratio=d("0.600000"),
            min_fallback_coverage_block_ratio=d("0.700000"),
        )
    with pytest.raises(ValueError, match="must not exceed block threshold"):
        ResearchSourceScraplingExtractionQualityGateConfig(
            max_conflict_risk_pass_ratio=d("0.700000"),
            max_conflict_risk_block_ratio=d("0.600000"),
        )
    with pytest.raises(ValueError, match="must be less than block threshold"):
        ResearchSourceScraplingExtractionQualityGateConfig(
            max_freshness_age_pass_seconds=d("3600.000000"),
            max_freshness_age_block_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="must not exceed required_field_count"):
        _output(extracted_field_count=d("11.000000"))
    with pytest.raises(ValueError, match="must not be after generated_at"):
        _report((_output(extracted_at=GENERATED_AT + timedelta(seconds=1)),))


def _walk_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, nested in value.items():
            strings.append(key)
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for nested in value:
            strings.extend(_walk_strings(nested))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


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
        assert type(value) is Decimal
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
