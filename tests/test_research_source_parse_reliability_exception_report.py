from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_parse_reliability_exception_report import (
    DEFAULT_RESEARCH_SOURCE_PARSE_RELIABILITY_EXCEPTION_REPORT_CONFIG_VERSION,
    ResearchSourceParseReliabilityExceptionConfig,
    ResearchSourceParseReliabilityExceptionInput,
    ResearchSourceParseReliabilityExceptionReasonCodeCount,
    ResearchSourceParseReliabilityExceptionReport,
    ResearchSourceParseReliabilityExceptionRow,
    build_research_source_parse_reliability_exception_report,
    research_source_parse_reliability_exception_report_payload,
    validate_research_source_parse_reliability_exception_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_parse_reliability_exception_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedParseReliabilityShape:
    parser_family: str
    parsed_count: Decimal
    failed_count: Decimal
    required_field_count: Decimal
    missing_required_field_count: Decimal
    parser_output_generated_at: datetime
    corroborating_source_count: Decimal
    required_corroborating_source_count: Decimal
    retry_backlog_count: Decimal
    manual_review_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchSourceParseReliabilityExceptionConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_SOURCE_PARSE_RELIABILITY_EXCEPTION_REPORT_CONFIG_VERSION
        ),
        "parse_success_ratio_watch_threshold": d("0.900000"),
        "parse_success_ratio_block_threshold": d("0.750000"),
        "missing_required_field_ratio_watch_threshold": d("0.100000"),
        "missing_required_field_ratio_block_threshold": d("0.300000"),
        "parser_output_age_watch_seconds": d("1800.000000"),
        "parser_output_age_block_seconds": d("7200.000000"),
        "corroboration_ready_ratio_watch_threshold": d("0.800000"),
        "corroboration_ready_ratio_block_threshold": d("0.500000"),
        "retry_backlog_watch_threshold": d("5.000000"),
        "retry_backlog_block_threshold": d("20.000000"),
        "manual_review_urgency_watch_threshold": d("0.400000"),
        "manual_review_urgency_block_threshold": d("0.750000"),
    }
    values.update(overrides)
    return ResearchSourceParseReliabilityExceptionConfig(**values)


def parse_item(
    parser_family: str = "official-feed",
    *,
    parsed_count: Decimal = d("95.000000"),
    failed_count: Decimal = d("5.000000"),
    required_field_count: Decimal = d("100.000000"),
    missing_required_field_count: Decimal = d("0.000000"),
    parser_output_generated_at: datetime = GENERATED_AT - timedelta(minutes=10),
    corroborating_source_count: Decimal = d("3.000000"),
    required_corroborating_source_count: Decimal = d("3.000000"),
    retry_backlog_count: Decimal = d("0.000000"),
    manual_review_urgency: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceParseReliabilityExceptionInput:
    return ResearchSourceParseReliabilityExceptionInput(
        parser_family=parser_family,
        parsed_count=parsed_count,
        failed_count=failed_count,
        required_field_count=required_field_count,
        missing_required_field_count=missing_required_field_count,
        parser_output_generated_at=parser_output_generated_at,
        corroborating_source_count=corroborating_source_count,
        required_corroborating_source_count=required_corroborating_source_count,
        retry_backlog_count=retry_backlog_count,
        manual_review_urgency=manual_review_urgency,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceParseReliabilityExceptionConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceParseReliabilityExceptionReport:
    return build_research_source_parse_reliability_exception_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_pass_report_with_digest() -> None:
    exception_report = report(())

    assert type(exception_report) is ResearchSourceParseReliabilityExceptionReport
    assert exception_report.__dataclass_params__.frozen is True
    assert exception_report.generated_at == GENERATED_AT
    assert exception_report.config_version == (
        DEFAULT_RESEARCH_SOURCE_PARSE_RELIABILITY_EXCEPTION_REPORT_CONFIG_VERSION
    )
    assert exception_report.parser_family_count == ZERO
    assert exception_report.input_count == ZERO
    assert exception_report.parse_success_ratio == ONE
    assert exception_report.missing_required_field_count == ZERO
    assert exception_report.missing_required_field_ratio == ZERO
    assert exception_report.stale_parser_output_count == ZERO
    assert exception_report.max_parser_output_age_seconds == ZERO
    assert exception_report.corroboration_ready_count == ZERO
    assert exception_report.corroboration_ready_ratio == ONE
    assert exception_report.retry_backlog_count == ZERO
    assert exception_report.manual_review_urgency_peak == ZERO
    assert exception_report.pass_count == ZERO
    assert exception_report.watch_count == ZERO
    assert exception_report.block_count == ZERO
    assert exception_report.status == "pass"
    assert exception_report.reason_codes == ("no_parse_reliability_exceptions",)
    assert exception_report.reason_code_counts == (
        ResearchSourceParseReliabilityExceptionReasonCodeCount(
            reason_code="no_parse_reliability_exceptions",
            count=ONE,
        ),
    )
    assert exception_report.rows == ()
    assert len(exception_report.derived_validation_digest) == 64
    assert exception_report.paper_only is True
    assert exception_report.report_only is True
    assert exception_report.readonly is True


def test_parse_reliability_exceptions_aggregate_success_fields_age_readiness_backlog_and_review() -> None:
    exception_report = report(
        (
            parse_item(
                "parser-pass",
                parsed_count=d("95.000000"),
                failed_count=d("5.000000"),
                missing_required_field_count=d("0.000000"),
                parser_output_generated_at=GENERATED_AT - timedelta(minutes=10),
                corroborating_source_count=d("3.000000"),
                required_corroborating_source_count=d("3.000000"),
                retry_backlog_count=d("0.000000"),
                manual_review_urgency=d("0.100000"),
            ),
            parse_item(
                "parser-watch",
                parsed_count=d("85.000000"),
                failed_count=d("15.000000"),
                missing_required_field_count=d("12.000000"),
                parser_output_generated_at=GENERATED_AT - timedelta(minutes=45),
                corroborating_source_count=d("2.000000"),
                required_corroborating_source_count=d("3.000000"),
                retry_backlog_count=d("7.000000"),
                manual_review_urgency=d("0.450000"),
            ),
            parse_item(
                "parser-block",
                parsed_count=d("60.000000"),
                failed_count=d("40.000000"),
                missing_required_field_count=d("35.000000"),
                parser_output_generated_at=GENERATED_AT - timedelta(hours=3),
                corroborating_source_count=d("1.000000"),
                required_corroborating_source_count=d("3.000000"),
                retry_backlog_count=d("25.000000"),
                manual_review_urgency=d("0.850000"),
                reason_codes=("requires_schema_owner_review",),
            ),
        ),
    )

    assert tuple(row.parser_family for row in exception_report.rows) == (
        "parser-block",
        "parser-pass",
        "parser-watch",
    )
    assert exception_report.status == "block"
    assert exception_report.parser_family_count == d("3.000000")
    assert exception_report.input_count == d("300.000000")
    assert exception_report.parse_success_ratio == d("0.800000")
    assert exception_report.missing_required_field_count == d("47.000000")
    assert exception_report.missing_required_field_ratio == d("0.156667")
    assert exception_report.stale_parser_output_count == d("2.000000")
    assert exception_report.max_parser_output_age_seconds == d("10800.000000")
    assert exception_report.corroboration_ready_count == d("1.000000")
    assert exception_report.corroboration_ready_ratio == d("0.333333")
    assert exception_report.retry_backlog_count == d("32.000000")
    assert exception_report.manual_review_urgency_peak == d("0.850000")
    assert exception_report.pass_count == d("1.000000")
    assert exception_report.watch_count == d("1.000000")
    assert exception_report.block_count == d("1.000000")

    block_row, pass_row, watch_row = exception_report.rows
    assert type(block_row) is ResearchSourceParseReliabilityExceptionRow
    assert pass_row.status == "pass"
    assert pass_row.parse_success_ratio == d("0.950000")
    assert pass_row.reason_codes == ("source_parse_reliability_exception_pass",)
    assert watch_row.status == "watch"
    assert watch_row.parse_success_ratio == d("0.850000")
    assert watch_row.missing_required_field_ratio == d("0.120000")
    assert watch_row.parser_output_age_seconds == d("2700.000000")
    assert watch_row.corroboration_ready_ratio == d("0.666667")
    assert "parse_success_ratio_watch" in watch_row.reason_codes
    assert "missing_required_fields_watch" in watch_row.reason_codes
    assert "stale_parser_output_watch" in watch_row.reason_codes
    assert "corroboration_not_ready_watch" in watch_row.reason_codes
    assert "retry_backlog_watch" in watch_row.reason_codes
    assert "manual_review_urgency_watch" in watch_row.reason_codes
    assert block_row.status == "block"
    assert block_row.parse_success_ratio == d("0.600000")
    assert block_row.missing_required_field_ratio == d("0.350000")
    assert block_row.parser_output_age_seconds == d("10800.000000")
    assert block_row.corroboration_ready_ratio == d("0.333333")
    assert "parse_success_ratio_block" in block_row.reason_codes
    assert "missing_required_fields_block" in block_row.reason_codes
    assert "stale_parser_output_block" in block_row.reason_codes
    assert "corroboration_not_ready_block" in block_row.reason_codes
    assert "retry_backlog_block" in block_row.reason_codes
    assert "manual_review_urgency_block" in block_row.reason_codes
    assert "input_requires_schema_owner_review" in block_row.reason_codes
    assert exception_report.reason_code_counts == tuple(
        sorted(exception_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_digest_is_deterministic_public_safe_and_decimal_string_only() -> None:
    rows = (
        SuppliedParseReliabilityShape(
            parser_family="parser-watch",
            parsed_count=d("85.000000"),
            failed_count=d("15.000000"),
            required_field_count=d("100.000000"),
            missing_required_field_count=d("12.000000"),
            parser_output_generated_at=GENERATED_AT - timedelta(minutes=45),
            corroborating_source_count=d("2.000000"),
            required_corroborating_source_count=d("3.000000"),
            retry_backlog_count=d("7.000000"),
            manual_review_urgency=d("0.450000"),
            reason_codes=("schema_review_pending",),
        ),
        parse_item("parser-pass"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_source_parse_reliability_exception_report_payload(first_report)
    second_payload = research_source_parse_reliability_exception_report_payload(
        second_report,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["parse_success_ratio"] == "0.950000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert validate_research_source_parse_reliability_exception_report_payload(
        first_payload,
    )
    assert not any(type(value) in (float, int) for value in _walk_payload_values(first_payload))
    assert all(row["status"] in {"pass", "watch", "block"} for row in first_payload["rows"])
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "http",
            "url",
            "raw",
            "text",
            "market",
            "condition",
            "candidate",
            "dsn",
            "table",
            "token",
            "private",
            "wallet",
            "auth",
            "order",
            "trade",
            "sizing",
            "recommendation",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_time_and_public_leaks() -> None:
    with pytest.raises(ValueError, match="parse_success_ratio_watch_threshold"):
        config(parse_success_ratio_watch_threshold=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="parse_success_ratio_block_threshold"):
        config(parse_success_ratio_block_threshold=d("0.950000"))
    with pytest.raises(ValueError, match="missing_required_field_ratio_block_threshold"):
        config(missing_required_field_ratio_block_threshold=d("0.050000"))
    with pytest.raises(ValueError, match="parser_output_age_block_seconds"):
        config(parser_output_age_block_seconds=d("1000.000000"))
    with pytest.raises(ValueError, match="parsed_count"):
        parse_item(parsed_count=95)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="failed_count"):
        parse_item(failed_count=_DecimalSubclass("5.000000"))
    with pytest.raises(ValueError, match="missing_required_field_count"):
        parse_item(missing_required_field_count=d("1.500000"))
    with pytest.raises(ValueError, match="parser_family"):
        parse_item("market-0xabc")
    with pytest.raises(ValueError, match="parser_family"):
        parse_item("raw-source-parser")
    with pytest.raises(ValueError, match="paper_only"):
        replace(parse_item(), paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report((parse_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (parse_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="parser_output_generated_at"):
        report(
            (
                parse_item(
                    parser_output_generated_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )

    exception_report = report((parse_item(),))
    with pytest.raises(FrozenInstanceError):
        exception_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(exception_report, paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(exception_report, retry_backlog_count=d("99.000000"))

    payload = research_source_parse_reliability_exception_report_payload(exception_report)
    tampered_payload = dict(payload)
    tampered_payload["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_source_parse_reliability_exception_report_payload(
            tampered_payload,
        )
    leaky_payload = dict(payload)
    leaky_payload["rows"] = tuple(payload["rows"]) + (
        {"parser_family": "https://example.invalid/raw-source"},
    )
    with pytest.raises(ValueError, match="unsafe public"):
        validate_research_source_parse_reliability_exception_report_payload(
            leaky_payload,
        )

    for cls in (
        ResearchSourceParseReliabilityExceptionConfig,
        ResearchSourceParseReliabilityExceptionInput,
        ResearchSourceParseReliabilityExceptionRow,
        ResearchSourceParseReliabilityExceptionReport,
    ):
        public_field_names = {field.name for field in fields(cls)}
        for forbidden in ("url", "raw", "text", "market", "candidate", "dsn", "table"):
            assert not any(forbidden in field_name.lower() for field_name in public_field_names)


def test_module_is_pure_readonly_report_scope_without_forbidden_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.AsyncFunctionDef):
            assert False, f"unexpected async surface: {node.name}"
    assert not (imports & forbidden_import_roots)

    lowered = source.lower()
    for forbidden in (
        "private_key",
        "wallet",
        "auth",
        "order",
        "trade",
        "live_trading",
        "sizing",
        "recommendation",
        "database",
        "network",
    ):
        assert forbidden not in lowered


def _walk_payload_values(value: object) -> list[object]:
    if isinstance(value, dict):
        items: list[object] = []
        for key, item in value.items():
            items.append(key)
            items.extend(_walk_payload_values(item))
        return items
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_walk_payload_values(item))
        return items
    return [value]
