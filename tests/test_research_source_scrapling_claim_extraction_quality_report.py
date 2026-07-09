from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_source_scrapling_claim_extraction_quality_report import (
    ResearchSourceScraplingClaimExtractionQualityConfig,
    ResearchSourceScraplingClaimExtractionQualityInput,
    ResearchSourceScraplingClaimExtractionQualityReport,
    ResearchSourceScraplingClaimExtractionQualityRow,
    build_research_source_scrapling_claim_extraction_quality_report,
    research_source_scrapling_claim_extraction_quality_report_digest,
    research_source_scrapling_claim_extraction_quality_report_payload,
    validate_research_source_scrapling_claim_extraction_quality_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scrapling_claim_extraction_quality_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
EXTRACTED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceScraplingClaimExtractionQualityConfig:
    values = {
        "fresh_extraction_max_age_seconds": d("3600.000000"),
        "stale_extraction_block_age_seconds": d("86400.000000"),
        "min_extraction_success_pass_ratio": d("0.900000"),
        "min_extraction_success_watch_ratio": d("0.650000"),
        "min_claim_acceptance_pass_ratio": d("0.800000"),
        "min_claim_acceptance_watch_ratio": d("0.500000"),
        "min_required_field_coverage_pass_ratio": d("0.900000"),
        "min_required_field_coverage_watch_ratio": d("0.700000"),
        "min_parser_confidence_pass_ratio": d("0.850000"),
        "min_parser_confidence_watch_ratio": d("0.600000"),
        "min_normalization_pass_ratio": d("0.850000"),
        "min_normalization_watch_ratio": d("0.600000"),
        "max_contradiction_watch_pressure": d("0.100000"),
        "max_contradiction_block_pressure": d("0.250000"),
        "max_duplicate_watch_pressure": d("0.200000"),
        "max_duplicate_block_pressure": d("0.500000"),
        "min_quality_pass_score": d("0.800000"),
        "min_quality_watch_score": d("0.500000"),
        "extraction_success_weight": d("0.160000"),
        "freshness_weight": d("0.140000"),
        "claim_acceptance_weight": d("0.160000"),
        "required_field_coverage_weight": d("0.150000"),
        "parser_confidence_weight": d("0.140000"),
        "normalization_weight": d("0.100000"),
        "contradiction_weight": d("0.075000"),
        "duplicate_weight": d("0.075000"),
    }
    values.update(overrides)
    return ResearchSourceScraplingClaimExtractionQualityConfig(**values)


def input_row(
    private_candidate_ref: str = "private-candidate",
    *,
    extracted_at: datetime = EXTRACTED_AT,
    extraction_attempt_count: Decimal = d("10"),
    extraction_success_count: Decimal = d("10"),
    claim_span_count: Decimal = d("10"),
    accepted_claim_span_count: Decimal = d("9"),
    required_claim_field_count: Decimal = d("5"),
    populated_claim_field_count: Decimal = d("5"),
    parser_confidence_ratio: Decimal = d("0.950000"),
    claim_normalization_ratio: Decimal = d("0.900000"),
    contradiction_flag_count: Decimal = d("0"),
    duplicate_claim_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceScraplingClaimExtractionQualityInput:
    return ResearchSourceScraplingClaimExtractionQualityInput(
        private_candidate_ref=private_candidate_ref,
        extracted_at=extracted_at,
        extraction_attempt_count=extraction_attempt_count,
        extraction_success_count=extraction_success_count,
        claim_span_count=claim_span_count,
        accepted_claim_span_count=accepted_claim_span_count,
        required_claim_field_count=required_claim_field_count,
        populated_claim_field_count=populated_claim_field_count,
        parser_confidence_ratio=parser_confidence_ratio,
        claim_normalization_ratio=claim_normalization_ratio,
        contradiction_flag_count=contradiction_flag_count,
        duplicate_claim_count=duplicate_claim_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchSourceScraplingClaimExtractionQualityInput,
    cfg: ResearchSourceScraplingClaimExtractionQualityConfig | None = None,
) -> ResearchSourceScraplingClaimExtractionQualityReport:
    return build_research_source_scrapling_claim_extraction_quality_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _walk_payload_values(value: object) -> list[object]:
    values = [value]
    if type(value) is dict:
        for key, item in value.items():
            values.extend(_walk_payload_values(key))
            values.extend(_walk_payload_values(item))
    elif type(value) is list:
        for item in value:
            values.extend(_walk_payload_values(item))
    return values


def _assert_payload_has_no_raw_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"payload leaked raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            _assert_payload_has_no_raw_numbers(item)
    elif type(value) is list:
        for item in value:
            _assert_payload_has_no_raw_numbers(item)


def _assert_payload_has_no_forbidden_surface(payload: dict[str, Any]) -> None:
    rendered_values = [str(value).casefold() for value in _walk_payload_values(payload)]
    for forbidden in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommend",
    ):
        assert all(forbidden not in value for value in rendered_values), forbidden


def _assert_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric was not Decimal: {value!r}")
    if type(value) is tuple:
        for item in value:
            _assert_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_decimal_public_numbers(getattr(value, field.name))


def _assert_no_signed_zero_decimals(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        assert not (value.is_zero() and value.is_signed())
        return
    if type(value) is tuple:
        for item in value:
            _assert_no_signed_zero_decimals(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_signed_zero_decimals(getattr(value, field.name))


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    quality_report = report()

    assert type(quality_report) is ResearchSourceScraplingClaimExtractionQualityReport
    assert is_dataclass(quality_report)
    assert quality_report.__dataclass_params__.frozen
    assert quality_report.generated_at == GENERATED_AT
    assert quality_report.status == "block"
    assert quality_report.input_count == d("0.000000")
    assert quality_report.row_count == d("0.000000")
    assert quality_report.pass_count == d("0.000000")
    assert quality_report.watch_count == d("0.000000")
    assert quality_report.block_count == d("0.000000")
    assert quality_report.attention_count == d("0.000000")
    assert quality_report.average_extraction_quality_score == d("0.000000")
    assert quality_report.max_extraction_age_seconds == d("0.000000")
    assert quality_report.rows == ()
    assert quality_report.reason_codes == (
        "scrapling_claim_extraction_no_inputs",
        "scrapling_claim_extraction_quality_block",
    )
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True
    _assert_decimal_public_numbers(quality_report)

    payload = quality_report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert research_source_scrapling_claim_extraction_quality_report_digest(
        quality_report,
    ) == payload["derived_validation_digest"]
    assert validate_research_source_scrapling_claim_extraction_quality_report_payload(
        payload,
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)


def test_report_scores_extraction_freshness_claim_quality_and_conflicts() -> None:
    quality_report = report(
        input_row("a-private-pass"),
        input_row(
            "b-private-watch",
            extracted_at=GENERATED_AT - timedelta(seconds=7200),
            extraction_success_count=d("7"),
            accepted_claim_span_count=d("7"),
            populated_claim_field_count=d("4"),
            parser_confidence_ratio=d("0.700000"),
            claim_normalization_ratio=d("0.750000"),
            contradiction_flag_count=d("1"),
            duplicate_claim_count=d("2"),
        ),
        input_row(
            "c-private-block",
            extracted_at=GENERATED_AT - timedelta(seconds=90000),
            extraction_attempt_count=d("5"),
            extraction_success_count=d("0"),
            claim_span_count=d("4"),
            accepted_claim_span_count=d("0"),
            required_claim_field_count=d("4"),
            populated_claim_field_count=d("0"),
            parser_confidence_ratio=d("0.400000"),
            claim_normalization_ratio=d("0.400000"),
            contradiction_flag_count=d("4"),
            duplicate_claim_count=d("4"),
        ),
    )

    assert quality_report.status == "block"
    assert quality_report.input_count == d("3.000000")
    assert quality_report.pass_count == d("1.000000")
    assert quality_report.watch_count == d("1.000000")
    assert quality_report.block_count == d("1.000000")
    assert quality_report.attention_count == d("2.000000")
    assert quality_report.max_extraction_age_seconds == d("90000.000000")
    assert quality_report.average_extraction_success_rate == d("0.566667")
    assert quality_report.average_extraction_freshness_score == d("0.652174")
    assert quality_report.average_claim_acceptance_rate == d("0.533333")
    assert quality_report.average_required_field_coverage_rate == d("0.600000")
    assert quality_report.average_parser_confidence_score == d("0.683333")
    assert quality_report.average_normalization_score == d("0.683333")
    assert quality_report.average_contradiction_pressure_score == d("0.366667")
    assert quality_report.average_duplicate_pressure_score == d("0.400000")
    assert quality_report.average_extraction_quality_score == d("0.613804")

    assert tuple(row.status for row in quality_report.rows) == ("block", "watch", "pass")
    assert tuple(row.row_label for row in quality_report.rows) == (
        "redacted-scrapling-claim-extraction-000003",
        "redacted-scrapling-claim-extraction-000002",
        "redacted-scrapling-claim-extraction-000001",
    )

    block_row, watch_row, pass_row = quality_report.rows
    assert type(block_row) is ResearchSourceScraplingClaimExtractionQualityRow
    assert block_row.extraction_quality_score == d("0.096000")
    assert block_row.reason_codes == (
        "extraction_success_rate_block",
        "extraction_age_block",
        "claim_acceptance_rate_block",
        "required_field_coverage_block",
        "parser_confidence_block",
        "normalization_block",
        "contradiction_pressure_block",
        "duplicate_pressure_block",
        "scrapling_claim_extraction_quality_block",
    )
    assert watch_row.extraction_success_rate == d("0.700000")
    assert watch_row.extraction_freshness_score == d("0.956522")
    assert watch_row.contradiction_pressure_score == d("0.100000")
    assert watch_row.duplicate_pressure_score == d("0.200000")
    assert watch_row.extraction_quality_score == d("0.778413")
    assert watch_row.reason_codes == (
        "extraction_success_rate_watch",
        "extraction_age_watch",
        "claim_acceptance_rate_watch",
        "required_field_coverage_watch",
        "parser_confidence_watch",
        "normalization_watch",
        "contradiction_pressure_watch",
        "duplicate_pressure_watch",
        "scrapling_claim_extraction_quality_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.extraction_quality_score == d("0.967000")
    assert pass_row.reason_codes == ("scrapling_claim_extraction_quality_pass",)


def test_payload_is_deterministic_redacted_and_digest_validated() -> None:
    rows = (
        input_row("https://example.invalid/raw_candidate/market_id/token"),
        input_row(
            "postgres://dsn/table/wallet/order/trade/live",
            extraction_success_count=d("8"),
            accepted_claim_span_count=d("8"),
            populated_claim_field_count=d("4"),
            parser_confidence_ratio=d("0.800000"),
            duplicate_claim_count=d("2"),
        ),
    )
    first = report(*rows)
    second = report(*reversed(rows))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = research_source_scrapling_claim_extraction_quality_report_payload(first)
    assert payload == research_source_scrapling_claim_extraction_quality_report_payload(first)
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert validate_research_source_scrapling_claim_extraction_quality_report_payload(
        payload,
    )
    assert all(
        row["row_label"].startswith("redacted-scrapling-claim-extraction-")
        for row in payload["rows"]
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)

    tampered_report = report(*rows)
    object.__setattr__(tampered_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_scrapling_claim_extraction_quality_report_payload(
            tampered_report,
        )

    tampered_payload = dict(payload)
    tampered_payload["status"] = "pass"
    assert not validate_research_source_scrapling_claim_extraction_quality_report_payload(
        tampered_payload,
    )


def test_payload_validation_rejects_schema_tampering_with_matching_digest() -> None:
    payload = research_source_scrapling_claim_extraction_quality_report_payload(
        report(input_row("a-private-pass")),
    )

    extra_top_level_payload = dict(payload)
    extra_top_level_payload["safe_extra"] = "redacted_extra"
    extra_top_level_payload["derived_validation_digest"] = canonical_digest(
        extra_top_level_payload,
    )

    missing_rows_payload = dict(payload)
    missing_rows_payload.pop("rows")
    missing_rows_payload["derived_validation_digest"] = canonical_digest(
        missing_rows_payload,
    )

    wrong_rows_type_payload = dict(payload)
    wrong_rows_type_payload["rows"] = "redacted_rows"
    wrong_rows_type_payload["derived_validation_digest"] = canonical_digest(
        wrong_rows_type_payload,
    )

    extra_row_field_payload = json.loads(json.dumps(payload))
    extra_row_field_payload["rows"][0]["safe_extra"] = "redacted_extra"
    extra_row_field_payload["derived_validation_digest"] = canonical_digest(
        extra_row_field_payload,
    )

    noncanonical_decimal_payload = dict(payload)
    noncanonical_decimal_payload["input_count"] = "1"
    noncanonical_decimal_payload["derived_validation_digest"] = canonical_digest(
        noncanonical_decimal_payload,
    )

    for tampered_payload in (
        extra_top_level_payload,
        missing_rows_payload,
        wrong_rows_type_payload,
        extra_row_field_payload,
        noncanonical_decimal_payload,
    ):
        assert not validate_research_source_scrapling_claim_extraction_quality_report_payload(
            tampered_payload,
        )


def test_negative_zero_inputs_are_canonicalized_in_public_decimal_surfaces() -> None:
    quality_report = report(
        input_row(
            "negative-zero-private",
            extraction_success_count=d("-0"),
            accepted_claim_span_count=d("-0"),
            populated_claim_field_count=d("-0"),
            parser_confidence_ratio=d("-0"),
            claim_normalization_ratio=d("-0"),
            contradiction_flag_count=d("-0"),
            duplicate_claim_count=d("-0"),
        ),
    )

    _assert_no_signed_zero_decimals(quality_report)
    payload = quality_report.payload
    assert "-0.000000" not in json.dumps(payload, sort_keys=True)
    assert validate_research_source_scrapling_claim_extraction_quality_report_payload(
        payload,
    )


def test_strict_validation_flags_statuses_imports_and_public_surfaces() -> None:
    quality_report = report(input_row("a-private-pass"))

    with pytest.raises(FrozenInstanceError):
        quality_report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ResearchSourceScraplingClaimExtractionQualityInput):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(input_row(report_only=True), report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(quality_report, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(quality_report, status="blocked")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(quality_report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="must be exactly Decimal"):
        input_row(extraction_success_count=_DecimalSubclass("1"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly datetime"):
        build_research_source_scrapling_claim_extraction_quality_report(
            (input_row(),),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(extracted_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        input_row(extracted_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="cannot be after generated_at"):
        report(input_row(extracted_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="extraction_success_count"):
        input_row(extraction_success_count=d("11"), extraction_attempt_count=d("10"))

    with pytest.raises(ValueError, match="accepted_claim_span_count"):
        input_row(accepted_claim_span_count=d("11"), claim_span_count=d("10"))

    with pytest.raises(ValueError, match="populated_claim_field_count"):
        input_row(populated_claim_field_count=d("6"), required_claim_field_count=d("5"))

    with pytest.raises(ValueError, match="contradiction_flag_count"):
        input_row(contradiction_flag_count=d("11"), claim_span_count=d("10"))

    with pytest.raises(ValueError, match="duplicate_claim_count"):
        input_row(duplicate_claim_count=d("11"), claim_span_count=d("10"))

    with pytest.raises(ValueError, match="weights"):
        config(extraction_success_weight=d("0.170000"))

    for public_record in (config(), quality_report, quality_report.rows[0]):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        _assert_decimal_public_numbers(public_record)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    forbidden_imports = {
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    for cls in (
        ResearchSourceScraplingClaimExtractionQualityConfig,
        ResearchSourceScraplingClaimExtractionQualityRow,
        ResearchSourceScraplingClaimExtractionQualityReport,
    ):
        for field in fields(cls):
            _assert_payload_has_no_forbidden_surface({"field": field.name})
