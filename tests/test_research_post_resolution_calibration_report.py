from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_post_resolution_calibration_report import (
    DEFAULT_RESEARCH_POST_RESOLUTION_CALIBRATION_REPORT_CONFIG_VERSION,
    ResearchPostResolutionCalibrationMemoryWritePlan,
    ResearchPostResolutionCalibrationReasonCodeCount,
    ResearchPostResolutionCalibrationReport,
    ResearchPostResolutionCalibrationReportConfig,
    ResearchPostResolutionCalibrationResolvedEvent,
    ResearchPostResolutionCalibrationRow,
    build_research_post_resolution_calibration_report,
    research_post_resolution_calibration_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_post_resolution_calibration_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchPostResolutionCalibrationReportConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_POST_RESOLUTION_CALIBRATION_REPORT_CONFIG_VERSION
        ),
        "min_resolved_event_count": d("3"),
        "absolute_bias_watch_threshold": d("0.080000"),
        "absolute_bias_block_threshold": d("0.500000"),
        "mean_bias_watch_threshold": d("0.050000"),
        "mean_bias_block_threshold": d("0.100000"),
        "brier_watch_threshold": d("0.220000"),
        "brier_block_threshold": d("0.300000"),
        "local_memory_write_planning_enabled": True,
    }
    values.update(overrides)
    return ResearchPostResolutionCalibrationReportConfig(**values)


def event(
    research_key: str = "research.calibration.base",
    *,
    condition_id: str = "condition_calibration_base",
    forecast_probability: Decimal = d("0.700000"),
    resolved_probability: Decimal = d("1.000000"),
    resolved_at: datetime | None = None,
    public_resolution_reference: str = "public-resolution-note",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchPostResolutionCalibrationResolvedEvent:
    return ResearchPostResolutionCalibrationResolvedEvent(
        research_key=research_key,
        condition_id=condition_id,
        forecast_probability=forecast_probability,
        resolved_probability=resolved_probability,
        resolved_at=resolved_at or GENERATED_AT - timedelta(hours=1),
        public_resolution_reference=public_resolution_reference,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchPostResolutionCalibrationReportConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchPostResolutionCalibrationReport:
    return build_research_post_resolution_calibration_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {
            "paper_only",
            "report_only",
            "readonly",
            "validation_config",
            "local_memory_write_planning_enabled",
            "requires_operator_review",
            "execute_write",
        }:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if (
            field.name.endswith(("_bias", "_count", "_error", "_score", "_threshold"))
            or "probability" in field.name
        ):
            assert type(item) is Decimal


def test_post_resolution_calibration_report_scores_bias_and_redacts_refs() -> None:
    summary = report(
        (
            event(
                "research.calibration.a",
                condition_id="condition_calibration_a",
                forecast_probability=d("0.900000"),
                resolved_probability=d("0.000000"),
                public_resolution_reference="https://vendor.example/resolution?credential=hidden",
            ),
            event(
                "research.calibration.b",
                condition_id="condition_calibration_b",
                forecast_probability=d("0.400000"),
                resolved_probability=d("0.000000"),
                public_resolution_reference="confidential-resolution-note",
                resolved_at=GENERATED_AT - timedelta(hours=2),
            ),
            event(
                "research.calibration.c",
                condition_id="condition_calibration_c",
                forecast_probability=d("0.980000"),
                resolved_probability=d("1.000000"),
                public_resolution_reference="public-resolution-note-c",
                resolved_at=GENERATED_AT - timedelta(hours=3),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_POST_RESOLUTION_CALIBRATION_REPORT_CONFIG_VERSION
    )
    assert summary.status == "block"
    assert summary.next_step == (
        "block_report_only_post_resolution_calibration_review_until_bias_reviewed"
    )
    assert summary.event_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_signed_bias == d("0.426667")
    assert summary.mean_absolute_bias == d("0.440000")
    assert summary.max_absolute_bias == d("0.900000")
    assert summary.brier_score == d("0.323467")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.status, row.condition_id) for row in summary.rows) == (
        ("block", "condition_calibration_a"),
        ("pass", "condition_calibration_c"),
        ("watch", "condition_calibration_b"),
    )

    blocked = summary.rows[0]
    assert blocked.signed_bias == d("0.900000")
    assert blocked.absolute_bias == d("0.900000")
    assert blocked.squared_error == d("0.810000")
    assert blocked.redacted_resolution_reference == "sha256:63d3e5245be7"
    assert blocked.improvement_items == (
        "review_probability_bin_with_large_absolute_bias_using_public_resolution_notes",
        "compare_forecast_confidence_to_realized_outcomes_before_reusing_template",
    )
    assert blocked.reason_codes == (
        "research_post_resolution_calibration_absolute_bias_block",
        "research_post_resolution_calibration_brier_block",
    )

    ready = summary.rows[1]
    assert ready.signed_bias == d("-0.020000")
    assert ready.absolute_bias == d("0.020000")
    assert ready.squared_error == d("0.000400")
    assert ready.redacted_resolution_reference == "public-resolution-note-c"
    assert ready.reason_codes == ("research_post_resolution_calibration_pass",)

    watched = summary.rows[2]
    assert watched.signed_bias == d("0.400000")
    assert watched.absolute_bias == d("0.400000")
    assert watched.squared_error == d("0.160000")
    assert watched.redacted_resolution_reference == "sha256:cd716e2a983b"
    assert watched.reason_codes == (
        "research_post_resolution_calibration_absolute_bias_watch",
    )

    assert summary.reason_code_counts == (
        ResearchPostResolutionCalibrationReasonCodeCount(
            reason_code="research_post_resolution_calibration_absolute_bias_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchPostResolutionCalibrationReasonCodeCount(
            reason_code="research_post_resolution_calibration_mean_bias_block",
            count=d("3.000000"),
            event_ratio=d("1.000000"),
        ),
        ResearchPostResolutionCalibrationReasonCodeCount(
            reason_code="research_post_resolution_calibration_brier_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchPostResolutionCalibrationReasonCodeCount(
            reason_code="research_post_resolution_calibration_absolute_bias_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchPostResolutionCalibrationReasonCodeCount(
            reason_code="research_post_resolution_calibration_local_memory_plan",
            count=d("3.000000"),
            event_ratio=d("1.000000"),
        ),
        ResearchPostResolutionCalibrationReasonCodeCount(
            reason_code="research_post_resolution_calibration_pass",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )
    assert summary.improvement_items == (
        "review_probability_bin_with_large_absolute_bias_using_public_resolution_notes",
        "review_directional_probability_bias_before_updating_future_research_checklists",
        "compare_forecast_confidence_to_realized_outcomes_before_reusing_template",
        "add_calibration_note_for_probability_bin_before_next_research_cycle",
        "plan_local_supabase_postgres_memory_write_after_operator_review_only",
        "keep_current_research_calibration_notes_and_continue_passive_review",
    )
    assert summary.memory_write_plan == ResearchPostResolutionCalibrationMemoryWritePlan(
        target="local_supabase_postgres_research_memory",
        planned_operation="insert_review_rows",
        payload_family="post_resolution_calibration_review",
        row_count=d("3.000000"),
    )
    assert summary.memory_write_plan.execute_write is False

    public = repr(asdict(summary)).lower()
    for value in (
        "hidden",
        "vendor.example",
        "https://",
        "confidential-resolution-note",
        "credential",
    ):
        assert value not in public


def test_empty_post_resolution_calibration_report_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.status == "block"
    assert summary.next_step == (
        "block_report_only_post_resolution_calibration_review_until_bias_reviewed"
    )
    assert summary.event_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.mean_signed_bias == ZERO
    assert summary.mean_absolute_bias == ZERO
    assert summary.max_absolute_bias == ZERO
    assert summary.brier_score == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchPostResolutionCalibrationReasonCodeCount(
            reason_code="research_post_resolution_calibration_no_inputs",
            count=d("1.000000"),
            event_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == ("research_post_resolution_calibration_no_inputs",)
    assert summary.improvement_items == (
        "collect_resolved_public_events_before_calibration_review",
    )
    assert summary.memory_write_plan == ResearchPostResolutionCalibrationMemoryWritePlan(
        target="local_supabase_postgres_research_memory",
        planned_operation="insert_review_rows",
        payload_family="post_resolution_calibration_review",
        row_count=ZERO,
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_post_resolution_calibration_report_honors_custom_threshold_config() -> None:
    summary = report(
        (
            event(
                forecast_probability=d("0.880000"),
                resolved_probability=d("1.000000"),
            ),
        ),
        cfg=config(
            min_resolved_event_count=d("1"),
            absolute_bias_watch_threshold=d("0.200000"),
            absolute_bias_block_threshold=d("0.400000"),
            mean_bias_watch_threshold=d("0.200000"),
            mean_bias_block_threshold=d("0.400000"),
            brier_watch_threshold=d("0.200000"),
            brier_block_threshold=d("0.400000"),
            local_memory_write_planning_enabled=False,
        ),
    )

    assert summary.status == "pass"
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.rows[0].reason_codes == (
        "research_post_resolution_calibration_pass",
    )
    assert summary.reason_codes == ("research_post_resolution_calibration_pass",)
    assert summary.memory_write_plan is None


def test_post_resolution_calibration_payload_uses_decimal_strings_and_safe_plan() -> None:
    summary = report((event(),))
    payload = research_post_resolution_calibration_report_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["event_count"] == "1.000000"
    assert payload["mean_absolute_bias"] == "0.300000"
    assert payload["rows"][0]["squared_error"] == "0.090000"
    assert payload["memory_write_plan"]["row_count"] == "1.000000"
    assert payload["memory_write_plan"]["execute_write"] is False
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "public_resolution_reference" not in repr(payload)
    assert "confidential" not in repr(payload).lower()


def test_post_resolution_calibration_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(ResearchPostResolutionCalibrationReportConfig)
    assert is_dataclass(ResearchPostResolutionCalibrationResolvedEvent)
    assert is_dataclass(ResearchPostResolutionCalibrationRow)
    assert is_dataclass(ResearchPostResolutionCalibrationReasonCodeCount)
    assert is_dataclass(ResearchPostResolutionCalibrationMemoryWritePlan)
    assert is_dataclass(ResearchPostResolutionCalibrationReport)

    cfg = config()
    source_event = event()
    summary = report((source_event,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_event.forecast_probability = d("0.2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].absolute_bias = d("0.4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.event_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("research-post-resolution-calibration-v0"))
    with pytest.raises(ValueError, match="min_resolved_event_count"):
        config(min_resolved_event_count=d("1.5"))
    with pytest.raises(ValueError, match="absolute_bias_watch_threshold"):
        config(absolute_bias_watch_threshold=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="absolute_bias_block_threshold"):
        config(
            absolute_bias_watch_threshold=d("0.500000"),
            absolute_bias_block_threshold=d("0.400000"),
        )
    with pytest.raises(ValueError, match="mean_bias_block_threshold"):
        config(
            mean_bias_watch_threshold=d("0.500000"),
            mean_bias_block_threshold=d("0.400000"),
        )
    with pytest.raises(ValueError, match="brier_block_threshold"):
        config(
            brier_watch_threshold=d("0.500000"),
            brier_block_threshold=d("0.400000"),
        )
    with pytest.raises(ValueError, match="local_memory_write_planning_enabled"):
        config(local_memory_write_planning_enabled=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="research_key"):
        event(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        event(condition_id="condition_wallet_probe")
    with pytest.raises(ValueError, match="forecast_probability"):
        event(forecast_probability=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="forecast_probability"):
        event(forecast_probability=Decimal("NaN"))
    with pytest.raises(ValueError, match="forecast_probability"):
        event(forecast_probability=d("1.000001"))
    with pytest.raises(ValueError, match="resolved_probability"):
        event(resolved_probability=d("0.500000"))
    with pytest.raises(ValueError, match="resolved_at"):
        event(resolved_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="resolved_at"):
        event(resolved_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="paper_only"):
        event(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        event(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        event(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_post_resolution_calibration_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_post_resolution_calibration_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="resolved_events"):
        report((object(),))
    with pytest.raises(ValueError, match="condition_id"):
        report((event(), event()))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready = report(
        (
            event(
                forecast_probability=d("1.000000"),
                resolved_probability=d("1.000000"),
            ),
        ),
        cfg=config(min_resolved_event_count=d("1"), local_memory_write_planning_enabled=False),
    ).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "research_post_resolution_calibration_absolute_bias_watch",
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(ready, status="block")
    with pytest.raises(ValueError, match="signed_bias"):
        replace(ready, signed_bias=d("0.500000"))
    with pytest.raises(ValueError, match="absolute_bias"):
        replace(ready, absolute_bias=d("0.500000"))
    with pytest.raises(ValueError, match="squared_error"):
        replace(ready, squared_error=d("0.250000"))
    with pytest.raises(ValueError, match="redacted_resolution_reference"):
        replace(ready, redacted_resolution_reference="https://host?credential=hidden")
    with pytest.raises(ValueError, match="improvement_items"):
        replace(ready, improvement_items=("buy_more_yes",))

    clean_report = report(
        (
            event(
                forecast_probability=d("1.000000"),
                resolved_probability=d("1.000000"),
            ),
        ),
        cfg=config(min_resolved_event_count=d("1"), local_memory_write_planning_enabled=False),
    )
    with pytest.raises(ValueError, match="pass_count"):
        replace(clean_report, pass_count=ZERO)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            clean_report,
            reason_codes=(
                "research_post_resolution_calibration_local_memory_plan",
                "research_post_resolution_calibration_pass",
            ),
        )
    with pytest.raises(ValueError, match="memory_write_plan"):
        replace(
            clean_report,
            memory_write_plan=ResearchPostResolutionCalibrationMemoryWritePlan(
                target="local_supabase_postgres_research_memory",
                planned_operation="insert_review_rows",
                payload_family="post_resolution_calibration_review",
                row_count=d("2.000000"),
            ),
        )
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                event("research.calibration.z", condition_id="condition_calibration_z"),
                event(
                    "research.calibration.a",
                    condition_id="condition_calibration_a",
                    forecast_probability=d("1.000000"),
                    resolved_probability=d("1.000000"),
                ),
            ),
            cfg=config(min_resolved_event_count=d("1")),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    source_event = event()
    summary = report((source_event,))

    assert_decimal_numeric_fields(config())
    assert_decimal_numeric_fields(source_event)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])
    assert_decimal_numeric_fields(summary.memory_write_plan)


def test_module_has_no_io_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "advice",
        "market_slug",
        "question",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
        "durable",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
