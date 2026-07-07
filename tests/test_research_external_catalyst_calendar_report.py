from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_external_catalyst_calendar_report import (
    ResearchExternalCatalystCalendarConfig,
    ResearchExternalCatalystCalendarEvent,
    ResearchExternalCatalystCalendarPublicPayloadItem,
    ResearchExternalCatalystCalendarReport,
    ResearchExternalCatalystCalendarRow,
    build_research_external_catalyst_calendar_report,
    research_external_catalyst_calendar_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchExternalCatalystCalendarConfig:
    values = {
        "config_version": "research-external-catalyst-calendar-report-v0",
        "min_pass_source_count": d("2.000000"),
        "min_watch_source_count": d("1.000000"),
        "min_pass_source_family_count": d("2.000000"),
        "min_watch_source_family_count": d("1.000000"),
        "min_pass_confidence_score": d("0.700000"),
        "min_watch_confidence_score": d("0.450000"),
        "max_publication_lead_minutes": d("10080.000000"),
        "max_data_event_lead_minutes": d("43200.000000"),
        "max_sports_node_lead_minutes": d("43200.000000"),
        "max_policy_node_lead_minutes": d("129600.000000"),
        "max_settlement_window_lead_minutes": d("43200.000000"),
    }
    values.update(overrides)
    return ResearchExternalCatalystCalendarConfig(**values)


def event(
    index: int,
    *,
    event_type: str,
    scheduled_at: datetime | None = None,
    source_count: Decimal = d("2.000000"),
    source_family_count: Decimal = d("2.000000"),
    confidence_score: Decimal = d("0.800000"),
    settlement_window_start_at: datetime | None = None,
    settlement_window_end_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
) -> ResearchExternalCatalystCalendarEvent:
    scheduled = scheduled_at or GENERATED_AT + timedelta(hours=index)
    return ResearchExternalCatalystCalendarEvent(
        event_id=f"event-{index:03d}",
        event_type=event_type,
        event_label=f"{event_type.replace('_', '-')}-{index:03d}",
        scheduled_at=scheduled,
        source_count=source_count,
        source_family_count=source_family_count,
        confidence_score=confidence_score,
        settlement_window_start_at=settlement_window_start_at,
        settlement_window_end_at=settlement_window_end_at,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchExternalCatalystCalendarEvent, ...],
    *,
    cfg: ResearchExternalCatalystCalendarConfig | None = None,
    generated_at: datetime = GENERATED_AT,
    public_payload: tuple[ResearchExternalCatalystCalendarPublicPayloadItem, ...] = (),
) -> ResearchExternalCatalystCalendarReport:
    return build_research_external_catalyst_calendar_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
        public_payload=public_payload,
    )


def test_complete_external_catalyst_calendar_passes_and_serializes_safely() -> None:
    settlement_start = GENERATED_AT + timedelta(hours=23)
    settlement_end = GENERATED_AT + timedelta(hours=25)

    calendar_report = report(
        (
            event(4, event_type="policy_node", scheduled_at=GENERATED_AT + timedelta(days=2)),
            event(2, event_type="data_event", scheduled_at=GENERATED_AT + timedelta(hours=8)),
            event(1, event_type="publication_time", scheduled_at=GENERATED_AT + timedelta(hours=2)),
            event(
                5,
                event_type="settlement_window",
                scheduled_at=GENERATED_AT + timedelta(days=1),
                settlement_window_start_at=settlement_start,
                settlement_window_end_at=settlement_end,
            ),
            event(3, event_type="sports_node", scheduled_at=GENERATED_AT + timedelta(hours=12)),
        ),
        public_payload=(
            ResearchExternalCatalystCalendarPublicPayloadItem(
                key="calendar_scope",
                value="redacted external catalyst schedule",
            ),
        ),
    )
    payload = research_external_catalyst_calendar_report_payload(calendar_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert type(calendar_report) is ResearchExternalCatalystCalendarReport
    assert calendar_report.generated_at == GENERATED_AT
    assert calendar_report.status == "pass"
    assert calendar_report.event_count == d("5.000000")
    assert calendar_report.covered_event_type_count == d("5.000000")
    assert calendar_report.missing_event_type_count == d("0.000000")
    assert calendar_report.missing_event_types == ()
    assert calendar_report.pass_count == d("5.000000")
    assert calendar_report.watch_count == d("0.000000")
    assert calendar_report.blocked_count == d("0.000000")
    assert calendar_report.reason_codes == ("external_catalyst_calendar_pass",)
    assert tuple(row.event_type for row in calendar_report.rows) == (
        "data_event",
        "policy_node",
        "publication_time",
        "settlement_window",
        "sports_node",
    )
    assert all(type(row) is ResearchExternalCatalystCalendarRow for row in calendar_report.rows)
    assert calendar_report.rows[0].lead_time_minutes == d("480.000000")
    assert calendar_report.rows[3].settlement_window_minutes == d("120.000000")
    assert payload["event_count"] == "5.000000"
    assert payload["rows"][0]["lead_time_minutes"] == "480.000000"
    assert payload["public_payload"][0]["value"] == "redacted external catalyst schedule"
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))
    for forbidden in ("source_url", "raw_source_text", "market_question", "dsn", "table", "token"):
        assert forbidden not in encoded.lower()


def test_missing_required_event_types_blocks_report_even_with_good_rows() -> None:
    calendar_report = report(
        (
            event(1, event_type="publication_time"),
            event(2, event_type="data_event"),
        ),
    )

    assert calendar_report.status == "block"
    assert calendar_report.event_count == d("2.000000")
    assert calendar_report.covered_event_type_count == d("2.000000")
    assert calendar_report.missing_event_type_count == d("3.000000")
    assert calendar_report.missing_event_types == (
        "policy_node",
        "settlement_window",
        "sports_node",
    )
    assert calendar_report.reason_codes == (
        "external_catalyst_calendar_missing_required_types",
        "missing_policy_node",
        "missing_settlement_window",
        "missing_sports_node",
    )


def test_low_confirmation_and_late_calendar_items_are_watch_or_block() -> None:
    calendar_report = report(
        (
            event(
                1,
                event_type="publication_time",
                source_count=d("1.000000"),
                source_family_count=d("1.000000"),
                confidence_score=d("0.500000"),
            ),
            event(2, event_type="data_event"),
            event(3, event_type="sports_node"),
            event(4, event_type="policy_node"),
            event(
                5,
                event_type="settlement_window",
                scheduled_at=GENERATED_AT + timedelta(days=45),
                settlement_window_start_at=GENERATED_AT + timedelta(days=45),
                settlement_window_end_at=GENERATED_AT + timedelta(days=45, hours=2),
            ),
        ),
    )

    publication_row = next(
        row for row in calendar_report.rows if row.event_type == "publication_time"
    )
    settlement_row = next(
        row for row in calendar_report.rows if row.event_type == "settlement_window"
    )

    assert calendar_report.status == "block"
    assert publication_row.status == "watch"
    assert publication_row.reason_codes == (
        "low_source_confirmation",
        "single_source_family_confirmation",
    )
    assert settlement_row.status == "block"
    assert "settlement_window_lead_time_too_long" in settlement_row.reason_codes
    assert "external_catalyst_calendar_blocked_rows" in calendar_report.reason_codes


def test_validation_rejects_bad_types_settlement_shape_and_unsafe_payload() -> None:
    with pytest.raises(ValueError, match="min_pass_source_count"):
        config(min_pass_source_count=d("1.25"))
    with pytest.raises(ValueError, match="min_pass_confidence_score"):
        config(min_pass_confidence_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(1, event_type="publication_time"),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (event(1, event_type="publication_time"),),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="event_type"):
        event(1, event_type="earnings_call")
    with pytest.raises(ValueError, match="confidence_score"):
        event(1, event_type="data_event", confidence_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="event_label"):
        event(1, event_type="policy_node").__class__(
            **{
                **event(1, event_type="policy_node").__dict__,
                "event_label": "Will this market resolve yes?",
            },
        )
    with pytest.raises(ValueError, match="settlement_window_start_at"):
        event(1, event_type="settlement_window")
    with pytest.raises(ValueError, match="settlement_window_end_at"):
        event(
            1,
            event_type="settlement_window",
            settlement_window_start_at=GENERATED_AT + timedelta(hours=2),
            settlement_window_end_at=GENERATED_AT + timedelta(hours=1),
        )
    with pytest.raises(ValueError, match="settlement_window_start_at"):
        event(
            1,
            event_type="data_event",
            settlement_window_start_at=GENERATED_AT + timedelta(hours=1),
        )
    with pytest.raises(ValueError, match="public_payload"):
        report(
            (event(1, event_type="publication_time"),),
            public_payload=(ResearchExternalCatalystCalendarPublicPayloadItem("source_url", "redacted"),),
        )
    with pytest.raises(ValueError, match="value"):
        ResearchExternalCatalystCalendarPublicPayloadItem(
            key="calendar_scope",
            value="https://example.invalid/raw-source",
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(event(1, event_type="publication_time"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_report_rows_validate_consistency() -> None:
    calendar_report = report(
        (
            event(1, event_type="publication_time"),
            event(2, event_type="data_event"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        calendar_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        calendar_report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(calendar_report.rows[0], status="watch")
    with pytest.raises(ValueError, match="missing_event_type_count"):
        replace(calendar_report, missing_event_type_count=d("0.000000"))


def test_owned_module_has_no_network_filesystem_db_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_external_catalyst_calendar_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "create_engine",
        "psycopg",
        "clobclient",
        "web3",
        "private_key",
        "wallet",
        "place_order",
        "cancel_order",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
