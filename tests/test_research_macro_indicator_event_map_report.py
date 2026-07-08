from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_macro_indicator_event_map_report import (
    DEFAULT_RESEARCH_MACRO_INDICATOR_EVENT_MAP_CONFIG_VERSION,
    ResearchMacroIndicatorEventMapConfig,
    ResearchMacroIndicatorEventMapInputRow,
    ResearchMacroIndicatorEventMapReasonCodeCount,
    ResearchMacroIndicatorEventMapReport,
    ResearchMacroIndicatorEventMapRow,
    build_research_macro_indicator_event_map_report,
    research_macro_indicator_event_map_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_macro_indicator_event_map_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMacroIndicatorEventMapConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_MACRO_INDICATOR_EVENT_MAP_CONFIG_VERSION,
        "min_public_source_count": d("2"),
        "min_release_time_confidence": d("0.650000"),
        "block_release_time_confidence": d("0.400000"),
        "min_event_indicator_alignment": d("0.600000"),
        "historical_sensitivity_watch_threshold": d("0.500000"),
        "historical_sensitivity_block_threshold": d("0.800000"),
        "review_need_watch_threshold": d("0.400000"),
        "review_need_block_threshold": d("0.750000"),
        "max_review_lag_seconds": d("86400.000000"),
        "release_proximity_watch_seconds": d("10800.000000"),
    }
    values.update(overrides)
    return ResearchMacroIndicatorEventMapConfig(**values)


def input_row(
    event_key: str = "macro.cpi.monthly",
    *,
    condition_id: str = "condition_macro_cpi_monthly",
    event_family: str = "macro",
    macro_indicator: str = "consumer_price_index",
    public_release_reference: str = "official-bls-release-calendar",
    scheduled_release_at: datetime | None = None,
    reviewed_at: object = _UNSET,
    public_source_count: Decimal = d("3"),
    release_time_confidence: Decimal = d("0.900000"),
    historical_sensitivity_score: Decimal = d("0.200000"),
    event_indicator_alignment_score: Decimal = d("0.900000"),
    review_need_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMacroIndicatorEventMapInputRow:
    return ResearchMacroIndicatorEventMapInputRow(
        event_key=event_key,
        condition_id=condition_id,
        event_family=event_family,
        macro_indicator=macro_indicator,
        public_release_reference=public_release_reference,
        scheduled_release_at=scheduled_release_at or GENERATED_AT + timedelta(days=3),
        reviewed_at=(
            GENERATED_AT - timedelta(hours=2)
            if reviewed_at is _UNSET
            else reviewed_at
        ),
        public_source_count=public_source_count,
        release_time_confidence=release_time_confidence,
        historical_sensitivity_score=historical_sensitivity_score,
        event_indicator_alignment_score=event_indicator_alignment_score,
        review_need_score=review_need_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchMacroIndicatorEventMapConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMacroIndicatorEventMapReport:
    return build_research_macro_indicator_event_map_report(
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
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if (
            field.name.endswith(
                (
                    "_confidence",
                    "_count",
                    "_ratio",
                    "_score",
                    "_seconds",
                ),
            )
            or field.name
            in {
                "average_historical_sensitivity_score",
                "average_release_time_confidence",
            }
        ):
            assert type(item) is Decimal


def test_macro_indicator_event_map_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "gold.real_yield.weekly",
                condition_id="condition_gold_real_yield_weekly",
                event_family="gold",
                macro_indicator="real_yield_change",
                public_release_reference="https://vendor.example/path?credential=hidden",
                scheduled_release_at=GENERATED_AT + timedelta(hours=1),
                reviewed_at=GENERATED_AT - timedelta(days=5),
                public_source_count=d("1"),
                release_time_confidence=d("0.600000"),
                historical_sensitivity_score=d("0.650000"),
                event_indicator_alignment_score=d("0.550000"),
                review_need_score=d("0.500000"),
            ),
            input_row(
                "spx.nfp.monthly",
                condition_id="condition_spx_nfp_monthly",
                event_family="equity_index",
                macro_indicator="nonfarm_payrolls",
                public_release_reference="confidential-release-brief",
                scheduled_release_at=GENERATED_AT + timedelta(hours=2),
                reviewed_at=None,
                public_source_count=d("2"),
                release_time_confidence=d("0.300000"),
                historical_sensitivity_score=d("0.850000"),
                event_indicator_alignment_score=d("0.750000"),
                review_need_score=d("0.800000"),
            ),
            input_row(
                "macro.cpi.monthly",
                condition_id="condition_macro_cpi_monthly",
                event_family="macro",
                macro_indicator="consumer_price_index",
                public_release_reference="official-bls-release-calendar",
                scheduled_release_at=GENERATED_AT + timedelta(days=3),
                reviewed_at=GENERATED_AT - timedelta(hours=2),
                public_source_count=d("3"),
                release_time_confidence=d("0.900000"),
                historical_sensitivity_score=d("0.200000"),
                event_indicator_alignment_score=d("0.900000"),
                review_need_score=d("0.100000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_RESEARCH_MACRO_INDICATOR_EVENT_MAP_CONFIG_VERSION
    assert summary.report_status == "block"
    assert summary.next_step == "block_report_only_research_macro_indicator_event_map"
    assert summary.event_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.review_required_count == d("2.000000")
    assert summary.high_sensitivity_count == d("2.000000")
    assert summary.close_release_count == d("2.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.average_historical_sensitivity_score == d("0.566667")
    assert summary.average_release_time_confidence == d("0.600000")
    assert summary.max_review_need_score == d("0.800000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.event_status, row.event_key) for row in summary.rows) == (
        ("block", "spx.nfp.monthly"),
        ("watch", "gold.real_yield.weekly"),
        ("pass", "macro.cpi.monthly"),
    )

    blocked = summary.rows[0]
    assert blocked.release_proximity_seconds == d("7200.000000")
    assert blocked.review_lag_seconds is None
    assert blocked.review_required is True
    assert blocked.redacted_release_reference == "sha256:582d3102956c"
    assert blocked.reason_codes == (
        "research_macro_indicator_event_map_release_time_untrusted",
        "research_macro_indicator_event_map_historical_sensitivity_block",
        "research_macro_indicator_event_map_review_need_block",
        "research_macro_indicator_event_map_missing_review",
        "research_macro_indicator_event_map_release_window_close",
    )

    watch = summary.rows[1]
    assert watch.release_proximity_seconds == d("3600.000000")
    assert watch.review_lag_seconds == d("432000.000000")
    assert watch.review_required is True
    assert watch.redacted_release_reference == "sha256:351a0c54ff74"
    assert watch.reason_codes == (
        "research_macro_indicator_event_map_release_time_uncertain",
        "research_macro_indicator_event_map_low_indicator_alignment",
        "research_macro_indicator_event_map_historical_sensitivity_watch",
        "research_macro_indicator_event_map_review_need_watch",
        "research_macro_indicator_event_map_stale_review",
        "research_macro_indicator_event_map_release_window_close",
        "research_macro_indicator_event_map_thin_sources",
    )

    ready = summary.rows[2]
    assert ready.event_status == "pass"
    assert ready.review_lag_seconds == d("7200.000000")
    assert ready.redacted_release_reference == "official-bls-release-calendar"
    assert ready.reason_codes == ("research_macro_indicator_event_map_pass",)

    assert summary.reason_code_counts == (
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_release_time_untrusted",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_historical_sensitivity_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_review_need_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_missing_review",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_release_time_uncertain",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_low_indicator_alignment",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_historical_sensitivity_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_review_need_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_stale_review",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_release_window_close",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_thin_sources",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_pass",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "hidden",
        "vendor.example",
        "https://",
        "confidential-release-brief",
        "credential",
    ):
        assert value not in public


def test_empty_macro_indicator_event_map_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.report_status == "block"
    assert summary.next_step == "block_report_only_research_macro_indicator_event_map"
    assert summary.event_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_historical_sensitivity_score == ZERO
    assert summary.average_release_time_confidence == ZERO
    assert summary.max_review_need_score == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchMacroIndicatorEventMapReasonCodeCount(
            reason_code="research_macro_indicator_event_map_no_inputs",
            count=d("1.000000"),
            event_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == ("research_macro_indicator_event_map_no_inputs",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_macro_indicator_event_map_honors_custom_threshold_config() -> None:
    summary = report(
        (input_row(historical_sensitivity_score=d("0.450000")),),
        cfg=config(
            min_public_source_count=d("1"),
            min_release_time_confidence=d("0.100000"),
            block_release_time_confidence=d("0.050000"),
            min_event_indicator_alignment=d("0.100000"),
            historical_sensitivity_watch_threshold=d("0.400000"),
            historical_sensitivity_block_threshold=d("0.900000"),
            review_need_watch_threshold=d("0.900000"),
            review_need_block_threshold=d("1.000000"),
            max_review_lag_seconds=d("172800.000000"),
            release_proximity_watch_seconds=d("1.000000"),
        ),
    )

    assert summary.report_status == "watch"
    assert summary.watch_count == d("1.000000")
    assert summary.rows[0].event_status == "watch"
    assert summary.rows[0].reason_codes == (
        "research_macro_indicator_event_map_historical_sensitivity_watch",
    )


def test_macro_indicator_event_map_payload_uses_decimal_strings_and_redacts() -> None:
    summary = report((input_row(),))
    payload = research_macro_indicator_event_map_report_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["event_count"] == "1.000000"
    assert payload["average_historical_sensitivity_score"] == "0.200000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_release_reference':" not in repr(payload)
    assert "confidential" not in repr(payload).lower()


def test_macro_indicator_event_map_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(ResearchMacroIndicatorEventMapConfig)
    assert is_dataclass(ResearchMacroIndicatorEventMapInputRow)
    assert is_dataclass(ResearchMacroIndicatorEventMapRow)
    assert is_dataclass(ResearchMacroIndicatorEventMapReasonCodeCount)
    assert is_dataclass(ResearchMacroIndicatorEventMapReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.public_source_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].public_source_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.event_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("macro-map-v0"))
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=d("1.5"))
    with pytest.raises(ValueError, match="min_release_time_confidence"):
        config(min_release_time_confidence=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_release_time_confidence"):
        config(block_release_time_confidence=d("0.800000"))
    with pytest.raises(ValueError, match="historical_sensitivity_score"):
        input_row(historical_sensitivity_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="review_need_block_threshold"):
        config(
            review_need_watch_threshold=d("0.900000"),
            review_need_block_threshold=d("0.800000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="event_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="private_condition")
    with pytest.raises(ValueError, match="event_family"):
        input_row(event_family="sports")
    with pytest.raises(ValueError, match="scheduled_release_at"):
        input_row(scheduled_release_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="reviewed_at"):
        input_row(reviewed_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="public_source_count"):
        input_row(public_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="release_time_confidence"):
        input_row(release_time_confidence=Decimal("NaN"))
    with pytest.raises(ValueError, match="event_indicator_alignment_score"):
        input_row(event_indicator_alignment_score=d("1.000001"))
    with pytest.raises(ValueError, match="review_need_score"):
        input_row(review_need_score=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_macro_indicator_event_map_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_macro_indicator_event_map_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))
    with pytest.raises(ValueError, match="reviewed_at"):
        report((input_row(reviewed_at=GENERATED_AT + timedelta(seconds=1)),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    passing = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passing,
            reason_codes=(
                "research_macro_indicator_event_map_pass",
                "research_macro_indicator_event_map_release_time_uncertain",
            ),
        )
    with pytest.raises(ValueError, match="event_status"):
        replace(passing, event_status="block")
    with pytest.raises(ValueError, match="review_required"):
        replace(passing, review_required=True)
    with pytest.raises(ValueError, match="redacted_release_reference"):
        replace(passing, redacted_release_reference="https://host?credential=hidden")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report((input_row(),)), pass_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report((input_row(),)), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report((input_row(),)), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report((input_row(),)), readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("macro.z", macro_indicator="z_indicator"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_or_execution_surfaces() -> None:
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
        "database",
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
