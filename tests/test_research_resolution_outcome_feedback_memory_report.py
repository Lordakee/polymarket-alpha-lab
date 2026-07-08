from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_resolution_outcome_feedback_memory_report import (
    CALIBRATION_BUCKETS,
    DEFAULT_RESEARCH_RESOLUTION_OUTCOME_FEEDBACK_MEMORY_REPORT_CONFIG_VERSION,
    ERROR_CATEGORIES,
    STATUSES,
    ResearchResolutionOutcomeFeedbackMemoryBucketRow,
    ResearchResolutionOutcomeFeedbackMemoryConfig,
    ResearchResolutionOutcomeFeedbackMemoryInput,
    ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount,
    ResearchResolutionOutcomeFeedbackMemoryReport,
    ResearchResolutionOutcomeFeedbackMemoryRow,
    build_research_resolution_outcome_feedback_memory_report,
    research_resolution_outcome_feedback_memory_report_payload,
    validate_research_resolution_outcome_feedback_memory_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
RESOLVED_AT = GENERATED_AT - timedelta(hours=1)
ZERO = Decimal("0.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_resolution_outcome_feedback_memory_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionOutcomeFeedbackMemoryConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_RESOLUTION_OUTCOME_FEEDBACK_MEMORY_REPORT_CONFIG_VERSION
        ),
        "watch_abs_calibration_error": d("0.100000"),
        "block_abs_calibration_error": d("0.250000"),
        "watch_stale_thesis_ratio": d("0.300000"),
        "block_stale_thesis_ratio": d("0.600000"),
        "watch_thesis_age_seconds": d("604800.000000"),
        "block_thesis_age_seconds": d("1209600.000000"),
        "min_pass_sample_count": d("10.000000"),
        "min_watch_sample_count": d("3.000000"),
    }
    values.update(overrides)
    return ResearchResolutionOutcomeFeedbackMemoryConfig(**values)


def memory_input(
    team_id: str = "macro-research",
    category_id: str = "rates",
    *,
    calibration_bucket: str = "p80_100",
    forecast_probability: Decimal = d("0.820000"),
    realized_outcome_rate: Decimal = d("0.800000"),
    sample_count: Decimal = d("20.000000"),
    error_category: str = "none",
    stale_thesis_ratio: Decimal = d("0.050000"),
    thesis_age_seconds: Decimal = d("86400.000000"),
    resolved_at: datetime = RESOLVED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchResolutionOutcomeFeedbackMemoryInput:
    return ResearchResolutionOutcomeFeedbackMemoryInput(
        team_id=team_id,
        category_id=category_id,
        calibration_bucket=calibration_bucket,
        forecast_probability=forecast_probability,
        realized_outcome_rate=realized_outcome_rate,
        sample_count=sample_count,
        error_category=error_category,
        stale_thesis_ratio=stale_thesis_ratio,
        thesis_age_seconds=thesis_age_seconds,
        resolved_at=resolved_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *items: ResearchResolutionOutcomeFeedbackMemoryInput,
    cfg: ResearchResolutionOutcomeFeedbackMemoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionOutcomeFeedbackMemoryReport:
    return build_research_resolution_outcome_feedback_memory_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_report_builds_aggregate_outcome_learning_memory_with_safe_feedback_queue() -> None:
    report = build_report(
        memory_input(),
        memory_input(
            "policy-research",
            "courts",
            calibration_bucket="p60_80",
            forecast_probability=d("0.650000"),
            realized_outcome_rate=d("0.500000"),
            sample_count=d("5.000000"),
            error_category="evidence_gap",
            stale_thesis_ratio=d("0.350000"),
            thesis_age_seconds=d("700000.000000"),
        ),
        memory_input(
            "crypto-research",
            "protocol",
            calibration_bucket="p20_40",
            forecast_probability=d("0.300000"),
            realized_outcome_rate=d("0.800000"),
            sample_count=d("2.000000"),
            error_category="resolution_rule_misread",
            stale_thesis_ratio=d("0.750000"),
            thesis_age_seconds=d("1300000.000000"),
        ),
    )

    assert is_dataclass(report)
    assert STATUSES == ("pass", "watch", "block")
    assert CALIBRATION_BUCKETS == ("p00_20", "p20_40", "p40_60", "p60_80", "p80_100")
    assert ERROR_CATEGORIES == (
        "none",
        "calibration_miss",
        "evidence_gap",
        "resolution_rule_misread",
        "stale_thesis",
        "contradiction_missed",
        "other",
    )
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.feedback_queue_count == d("2.000000")
    assert report.feedback_queue_ratio == d("0.666667")
    assert report.calibration_bucket_count == d("3.000000")
    assert report.stale_thesis_indicator_count == d("2.000000")
    assert report.max_abs_calibration_error == d("0.500000")
    assert report.average_abs_calibration_error == d("0.223333")
    assert report.max_stale_thesis_ratio == d("0.750000")
    assert report.max_thesis_age_seconds == d("1300000.000000")
    assert report.reason_codes == (
        "outcome_feedback_memory_block",
        "calibration_error_block",
        "stale_thesis_block",
        "thesis_age_block",
        "error_category_block",
        "sample_size_low_block",
        "calibration_error_watch",
        "stale_thesis_watch",
        "thesis_age_watch",
        "error_category_watch",
        "sample_size_low_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.team_id == "crypto-research"
    assert block_row.category_id == "protocol"
    assert block_row.abs_calibration_error == d("0.500000")
    assert block_row.reason_codes == (
        "calibration_error_block",
        "stale_thesis_block",
        "thesis_age_block",
        "error_category_block",
        "sample_size_low_block",
    )
    assert watch_row.reason_codes == (
        "calibration_error_watch",
        "stale_thesis_watch",
        "thesis_age_watch",
        "error_category_watch",
        "sample_size_low_watch",
    )
    assert pass_row.reason_codes == ("outcome_feedback_memory_pass",)
    assert ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount(
        reason_code="calibration_error_block",
        count=d("1.000000"),
        row_ratio=d("0.333333"),
    ) in report.reason_code_counts
    assert tuple(bucket.calibration_bucket for bucket in report.calibration_buckets) == (
        "p20_40",
        "p60_80",
        "p80_100",
    )
    assert tuple(bucket.status for bucket in report.calibration_buckets) == (
        "block",
        "watch",
        "pass",
    )

    payload = research_resolution_outcome_feedback_memory_report_payload(report)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "block"
    assert payload["feedback_queue_count"] == "2.000000"
    assert payload["rows"][0]["derived_validation_digest"] == block_row.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert validate_research_resolution_outcome_feedback_memory_public_payload(payload)
    assert_no_public_numeric_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    forbidden_payload_fragments = (
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_text",
        "raw_text",
        "source_url",
    )
    lowered_keys = tuple(key.lower() for key in payload_keys(payload))
    assert not any(
        fragment in key
        for key in lowered_keys
        for fragment in forbidden_payload_fragments
    )


def test_public_contract_is_frozen_decimal_digest_bound_and_surface_safe() -> None:
    module_classes = (
        ResearchResolutionOutcomeFeedbackMemoryConfig,
        ResearchResolutionOutcomeFeedbackMemoryInput,
        ResearchResolutionOutcomeFeedbackMemoryReasonCodeCount,
        ResearchResolutionOutcomeFeedbackMemoryBucketRow,
        ResearchResolutionOutcomeFeedbackMemoryRow,
        ResearchResolutionOutcomeFeedbackMemoryReport,
    )
    for klass in module_classes:
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    report = build_report(memory_input())
    for value in (config(), memory_input(), report, *report.reason_code_counts, *report.calibration_buckets, *report.rows):
        for field in fields(value):
            field_value = getattr(value, field.name)
            assert type(field_value) is not float
            if field.name.endswith(("_count", "_ratio", "_seconds", "_rate", "_error", "_probability")):
                assert field_value is None or type(field_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        memory_input(paper_only=False)
    with pytest.raises(TypeError, match="subclass"):
        type("DerivedConfig", (ResearchResolutionOutcomeFeedbackMemoryConfig,), {})
    with pytest.raises(TypeError, match="subclass"):
        type("DerivedRow", (ResearchResolutionOutcomeFeedbackMemoryRow,), {})
    with pytest.raises(ValueError, match="forecast_probability"):
        memory_input(forecast_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_abs_calibration_error"):
        config(watch_abs_calibration_error=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="resolved_at must be a datetime"):
        memory_input(resolved_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="resolved_at must be timezone-aware"):
        memory_input(resolved_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="calibration_bucket"):
        memory_input(calibration_bucket="p00_20", forecast_probability=d("0.820000"))
    with pytest.raises(ValueError, match="duplicate aggregate feedback"):
        build_report(memory_input(), memory_input())
    with pytest.raises(ValueError, match="after generated_at"):
        build_report(memory_input(resolved_at=GENERATED_AT + timedelta(seconds=1)))

    eastern = timezone(timedelta(hours=-4))
    tz_report = build_report(
        memory_input(resolved_at=datetime(2026, 7, 8, 7, 0, tzinfo=eastern)),
    )
    assert tz_report.rows[0].resolved_at == datetime(2026, 7, 8, 11, 0, tzinfo=UTC)

    payload = research_resolution_outcome_feedback_memory_report_payload(report)
    with pytest.raises(ValueError, match="numeric"):
        validate_research_resolution_outcome_feedback_memory_public_payload(
            {**payload, "row_count": 1},
        )
    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_resolution_outcome_feedback_memory_public_payload(missing_digest)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_resolution_outcome_feedback_memory_public_payload(
            {**payload, "block_count": "9.000000"},
        )
    for forbidden_key in (
        "market_id",
        "market_slug",
        "question_text",
        "source_text",
        "wallet_address",
        "order_id",
        "network_url",
        "database_dsn",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            validate_research_resolution_outcome_feedback_memory_public_payload(
                {**payload, forbidden_key: "not allowed"},
            )
    for forbidden_value in (
        "raw source text leaked",
        "wallet configured",
        "order configured",
        "live trading configured",
        "database configured",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            validate_research_resolution_outcome_feedback_memory_public_payload(
                {**payload, "operator_note": forbidden_value},
            )

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden_import_modules = {
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
        "py_clob_client",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_modules
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_modules

    lowered_source = source.lower()
    forbidden_source_fragments = (
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_text",
        "raw_text",
        "source_url",
        "private_key",
        "wallet",
        "auth_token",
        "network_client",
        "database_url",
        "place_order",
        "create_order",
        "cancel_order",
        "live_trading",
        "open(",
        "requests.",
        "httpx.",
        "socket.",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source
