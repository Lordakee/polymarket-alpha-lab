from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_source_scraping_coverage_completeness_report as api
from polymarket_alpha_lab.research_source_scraping_coverage_completeness_report import (
    ResearchSourceScrapingCoverageCompletenessConfig,
    ResearchSourceScrapingCoverageCompletenessInput,
    ResearchSourceScrapingCoverageCompletenessReport,
    build_research_source_scraping_coverage_completeness_report,
    validate_research_source_scraping_coverage_completeness_report_payload,
)


NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _input(
    *,
    private_collection_ref: str = (
        "raw_candidate_id=secret-market-7|market_slug=private-election|"
        "question=private question text|https://example.invalid/path?token=hidden"
    ),
    tool_family: str = "primary_channel",
    collected_at: datetime = NOW - timedelta(minutes=15),
    target_source_count: Decimal = Decimal("10.000000"),
    covered_source_count: Decimal = Decimal("10.000000"),
    parse_confidence_ratio: Decimal = Decimal("0.920000"),
    critical_field_count: Decimal = Decimal("5.000000"),
    missing_critical_field_count: Decimal = Decimal("0.000000"),
    duplicate_corroboration_count: Decimal = Decimal("3.000000"),
    required_duplicate_corroboration_count: Decimal = Decimal("3.000000"),
    authority_score: Decimal = Decimal("0.900000"),
) -> ResearchSourceScrapingCoverageCompletenessInput:
    return ResearchSourceScrapingCoverageCompletenessInput(
        private_collection_ref=private_collection_ref,
        tool_family=tool_family,
        collected_at=collected_at,
        target_source_count=target_source_count,
        covered_source_count=covered_source_count,
        parse_confidence_ratio=parse_confidence_ratio,
        critical_field_count=critical_field_count,
        missing_critical_field_count=missing_critical_field_count,
        duplicate_corroboration_count=duplicate_corroboration_count,
        required_duplicate_corroboration_count=required_duplicate_corroboration_count,
        authority_score=authority_score,
    )


def _report(
    inputs: tuple[ResearchSourceScrapingCoverageCompletenessInput, ...],
    *,
    config: ResearchSourceScrapingCoverageCompletenessConfig | None = None,
) -> ResearchSourceScrapingCoverageCompletenessReport:
    return build_research_source_scraping_coverage_completeness_report(
        inputs,
        config=config or ResearchSourceScrapingCoverageCompletenessConfig(),
        generated_at=NOW,
    )


def test_pass_report_uses_decimal_payload_stable_digest_and_redacts_private_refs() -> None:
    report = _report(
        (
            _input(tool_family="primary_channel"),
            _input(
                private_collection_ref=(
                    "raw_candidate_id=secret-market-8|market_id=private-8|"
                    "url=https://example.invalid/other?wallet=hidden"
                ),
                tool_family="secondary_channel",
                covered_source_count=Decimal("9.000000"),
                parse_confidence_ratio=Decimal("0.880000"),
                duplicate_corroboration_count=Decimal("2.000000"),
                authority_score=Decimal("0.850000"),
            ),
        ),
    )
    same_report = _report(
        (
            _input(
                tool_family="secondary_channel",
                private_collection_ref="b",
                covered_source_count=Decimal("9.000000"),
                parse_confidence_ratio=Decimal("0.880000"),
                duplicate_corroboration_count=Decimal("2.000000"),
                authority_score=Decimal("0.850000"),
            ),
            _input(tool_family="primary_channel", private_collection_ref="a"),
        ),
    )
    changed_report = _report((_input(covered_source_count=Decimal("8.000000")),))

    assert report.status == "pass"
    assert report.reason_codes == ("scraping_coverage_completeness_pass",)
    assert report.input_count == Decimal("2.000000")
    assert report.row_count == Decimal("2.000000")
    assert report.target_source_count == Decimal("20.000000")
    assert report.covered_source_count == Decimal("19.000000")
    assert report.aggregate_coverage_ratio == Decimal("0.950000")
    assert report.average_parse_confidence_ratio == Decimal("0.900000")
    assert report.average_authority_score == Decimal("0.875000")
    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert report.derived_validation_digest != changed_report.derived_validation_digest

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert validate_research_source_scraping_coverage_completeness_report_payload(payload)
    assert payload["input_count"] == "2.000000"
    assert payload["aggregate_coverage_ratio"] == "0.950000"
    assert payload["rows"][0]["row_index"] == "1.000000"
    assert payload["rows"][0]["tool_family"] == "primary_channel"
    assert payload["derived_validation_digest"] == report.derived_validation_digest

    rendered = json.dumps(payload, sort_keys=True)
    for forbidden_fragment in (
        "secret-market",
        "private-election",
        "private question text",
        "https://",
        "example.invalid",
        "wallet=hidden",
        "token=hidden",
    ):
        assert forbidden_fragment not in rendered
    _assert_no_decimal_objects(payload)
    _assert_no_public_numbers(report)


def test_watch_and_block_reports_use_fixed_reason_order() -> None:
    watch_report = _report(
        (
            _input(
                target_source_count=Decimal("10.000000"),
                covered_source_count=Decimal("8.000000"),
                parse_confidence_ratio=Decimal("0.700000"),
                critical_field_count=Decimal("10.000000"),
                missing_critical_field_count=Decimal("2.000000"),
                duplicate_corroboration_count=Decimal("1.000000"),
                required_duplicate_corroboration_count=Decimal("2.000000"),
                authority_score=Decimal("0.700000"),
            ),
        ),
    )
    block_report = _report(
        (
            _input(
                collected_at=NOW - timedelta(days=2),
                target_source_count=Decimal("10.000000"),
                covered_source_count=Decimal("2.000000"),
                parse_confidence_ratio=Decimal("0.500000"),
                critical_field_count=Decimal("10.000000"),
                missing_critical_field_count=Decimal("7.000000"),
                duplicate_corroboration_count=Decimal("0.000000"),
                required_duplicate_corroboration_count=Decimal("2.000000"),
                authority_score=Decimal("0.400000"),
            ),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.rows[0].reason_codes == (
        "coverage_below_target",
        "parse_confidence_below_pass_threshold",
        "critical_field_completeness_below_pass_threshold",
        "duplicate_corroboration_below_pass_threshold",
        "authority_below_pass_threshold",
        "completeness_score_below_pass_threshold",
    )
    assert block_report.status == "block"
    assert block_report.rows[0].reason_codes == (
        "coverage_below_watch_threshold",
        "parse_confidence_below_watch_threshold",
        "critical_field_completeness_below_watch_threshold",
        "duplicate_corroboration_below_watch_threshold",
        "freshness_below_watch_threshold",
        "authority_below_watch_threshold",
        "completeness_score_below_watch_threshold",
    )


def test_empty_input_blocks_with_zero_decimal_scores() -> None:
    report = _report(())

    assert report.status == "block"
    assert report.reason_codes == ("scraping_coverage_completeness_no_inputs",)
    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.aggregate_coverage_ratio == Decimal("0.000000")
    assert report.average_completeness_score == Decimal("0.000000")
    assert report.reason_code_counts[0].count == Decimal("1.000000")
    assert report.rows == ()


def test_dataclasses_flags_digest_decimal_only_safe_surface_and_no_io_imports() -> None:
    report = _report((_input(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchSourceScrapingCoverageCompletenessConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        ResearchSourceScrapingCoverageCompletenessConfig(paper_only=False)

    with pytest.raises(ValueError, match="Decimal"):
        _input(target_source_count=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = report.payload
    broken_payload = dict(payload)
    broken_payload["aggregate_coverage_ratio"] = "0.100000"
    assert not validate_research_source_scraping_coverage_completeness_report_payload(
        broken_payload,
    )

    for hard_flag in ("paper_only", "report_only", "readonly"):
        tampered_flag_payload = dict(payload)
        tampered_flag_payload[hard_flag] = False
        tampered_flag_payload = _payload_with_matching_digest(tampered_flag_payload)
        assert not validate_research_source_scraping_coverage_completeness_report_payload(
            tampered_flag_payload,
        )

    tampered_status_payload = dict(payload)
    tampered_status_payload["status"] = "alert"
    tampered_status_payload = _payload_with_matching_digest(tampered_status_payload)
    assert not validate_research_source_scraping_coverage_completeness_report_payload(
        tampered_status_payload,
    )

    tampered_row_status_payload = json.loads(json.dumps(payload, sort_keys=True))
    tampered_row_status_payload["rows"][0]["status"] = "alert"
    tampered_row_status_payload = _payload_with_matching_digest(tampered_row_status_payload)
    assert not validate_research_source_scraping_coverage_completeness_report_payload(
        tampered_row_status_payload,
    )

    for leaked_key in (
        "candidateId",
        "market-id",
        "sourceUrl",
        "rawText",
        "walletAddress",
        "orderBook",
    ):
        leaked_payload = dict(payload)
        leaked_payload[leaked_key] = "redacted"
        leaked_payload = _payload_with_matching_digest(leaked_payload)
        assert not validate_research_source_scraping_coverage_completeness_report_payload(
            leaked_payload,
        )

    for leaked_value in (
        "candidateId=secret",
        "market-id=secret",
        "sourceUrl=secret",
        "rawText=secret",
        "walletAddress=secret",
        "orderBook=secret",
        "".join(("scr", "apling")),
        "".join(("agent", "_reach")),
    ):
        leaked_payload = dict(payload)
        leaked_payload["config_version"] = leaked_value
        leaked_payload = _payload_with_matching_digest(leaked_payload)
        assert not validate_research_source_scraping_coverage_completeness_report_payload(
            leaked_payload,
        )

    forbidden_terms = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        ResearchSourceScrapingCoverageCompletenessConfig,
        ResearchSourceScrapingCoverageCompletenessInput,
        ResearchSourceScrapingCoverageCompletenessReport,
    ):
        for field in fields(cls):
            if field.name == "private_collection_ref":
                continue
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_terms)

    source_path = Path(api.__file__)
    tree = ast.parse(source_path.read_text())
    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "ccxt",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _payload_with_matching_digest(payload: dict[str, object]) -> dict[str, object]:
    resigned_payload = dict(payload)
    unsigned_payload = dict(resigned_payload)
    unsigned_payload.pop("derived_validation_digest", None)
    resigned_payload["derived_validation_digest"] = sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    return resigned_payload


def _assert_no_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_public_numbers(getattr(value, field.name))
