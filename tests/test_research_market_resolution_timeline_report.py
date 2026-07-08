from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_resolution_timeline_report import (
    MarketResolutionTimelineConfig,
    MarketResolutionTimelineEventInput,
    MarketResolutionTimelineReasonCodeCount,
    MarketResolutionTimelineReport,
    MarketResolutionTimelineRow,
    build_market_resolution_timeline_report,
    market_resolution_timeline_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedEventShape:
    event_id: str
    market_id: str
    event_type: str
    due_at: datetime
    completed_at: datetime | None = None
    evidence_count: Decimal = Decimal("0")
    dispute_open: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResolutionTimelineConfig:
    values = {
        "config_version": "market-resolution-timeline-report-v0",
        "info_refresh_grace_seconds": d("3600.000000"),
        "settlement_evidence_grace_seconds": d("7200.000000"),
        "dispute_window_grace_seconds": d("86400.000000"),
        "postmortem_grace_seconds": d("172800.000000"),
        "min_settlement_evidence_count": d("2"),
    }
    values.update(overrides)
    return MarketResolutionTimelineConfig(**values)


def event(
    index: int,
    *,
    market_id: str = "market-alpha",
    event_type: str = "info_refresh",
    due_at: datetime | None = None,
    completed_at: datetime | None = None,
    evidence_count: Decimal = Decimal("0"),
    dispute_open: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> MarketResolutionTimelineEventInput:
    return MarketResolutionTimelineEventInput(
        event_id=f"event-{index:03d}",
        market_id=market_id,
        event_type=event_type,
        due_at=due_at if due_at is not None else GENERATED_AT + timedelta(hours=1),
        completed_at=completed_at,
        evidence_count=evidence_count,
        dispute_open=dispute_open,
        reason_codes=reason_codes,
    )


def report(
    events: tuple[object, ...],
    *,
    cfg: MarketResolutionTimelineConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResolutionTimelineReport:
    return build_market_resolution_timeline_report(
        events,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_with_no_resolution_timeline() -> None:
    timeline = report(())

    assert type(timeline) is MarketResolutionTimelineReport
    assert timeline.generated_at == GENERATED_AT
    assert timeline.config_version == "market-resolution-timeline-report-v0"
    assert timeline.market_count == d("0")
    assert timeline.event_count == d("0")
    assert timeline.pass_count == d("0")
    assert timeline.watch_count == d("0")
    assert timeline.blocked_count == d("0")
    assert timeline.open_dispute_count == d("0")
    assert timeline.overdue_event_count == d("0")
    assert timeline.next_due_at is None
    assert timeline.status == "block"
    assert timeline.reason_codes == ("no_resolution_timeline_events",)
    assert timeline.reason_code_counts == (
        MarketResolutionTimelineReasonCodeCount(
            reason_code="no_resolution_timeline_events",
            count=d("1"),
        ),
    )
    assert timeline.rows == ()
    assert timeline.paper_only is True
    assert timeline.report_only is True
    assert timeline.readonly is True


def test_complete_resolution_timeline_passes_with_decimal_durations() -> None:
    timeline = report(
        (
            event(
                3,
                event_type="dispute_window",
                due_at=GENERATED_AT + timedelta(days=1),
            ),
            event(
                4,
                event_type="postmortem",
                due_at=GENERATED_AT + timedelta(days=2),
            ),
            event(
                2,
                event_type="settlement_evidence",
                due_at=GENERATED_AT - timedelta(hours=1),
                completed_at=GENERATED_AT - timedelta(minutes=30),
                evidence_count=d("2"),
                reason_codes=("official_resolution_seen",),
            ),
            event(
                1,
                event_type="info_refresh",
                due_at=GENERATED_AT - timedelta(hours=3),
                completed_at=GENERATED_AT - timedelta(hours=2),
            ),
        ),
    )

    assert timeline.status == "pass"
    assert timeline.market_count == d("1")
    assert timeline.event_count == d("4")
    assert timeline.pass_count == d("4")
    assert timeline.watch_count == d("0")
    assert timeline.blocked_count == d("0")
    assert timeline.open_dispute_count == d("0")
    assert timeline.overdue_event_count == d("0")
    assert timeline.next_due_at == GENERATED_AT + timedelta(days=1)
    assert timeline.reason_codes == ("resolution_timeline_pass",)

    assert tuple(row.event_type for row in timeline.rows) == (
        "info_refresh",
        "settlement_evidence",
        "dispute_window",
        "postmortem",
    )
    settlement = timeline.rows[1]
    assert type(settlement) is MarketResolutionTimelineRow
    assert settlement.evidence_count == d("2")
    assert settlement.seconds_until_due == d("-3600.000000")
    assert settlement.completion_lag_seconds == d("1800.000000")
    assert settlement.status == "pass"
    assert settlement.reason_codes == (
        "input_official_resolution_seen",
        "resolution_timeline_pass",
    )


def test_overdue_refresh_missing_settlement_evidence_and_open_dispute_watch() -> None:
    timeline = report(
        (
            event(
                1,
                event_type="info_refresh",
                due_at=GENERATED_AT - timedelta(minutes=90),
            ),
            event(
                2,
                event_type="settlement_evidence",
                due_at=GENERATED_AT - timedelta(minutes=30),
                evidence_count=d("1"),
            ),
            event(
                3,
                event_type="dispute_window",
                due_at=GENERATED_AT + timedelta(hours=6),
                dispute_open=True,
            ),
            event(
                4,
                event_type="postmortem",
                due_at=GENERATED_AT + timedelta(days=2),
            ),
        ),
    )

    assert timeline.status == "watch"
    assert timeline.watch_count == d("3")
    assert timeline.blocked_count == d("0")
    assert timeline.open_dispute_count == d("1")
    assert timeline.overdue_event_count == d("2")
    assert timeline.next_due_at == GENERATED_AT + timedelta(hours=6)
    assert timeline.reason_codes == (
        "dispute_window_open",
        "info_refresh_overdue_watch",
        "settlement_evidence_incomplete_watch",
    )
    assert tuple((row.event_type, row.status) for row in timeline.rows) == (
        ("info_refresh", "watch"),
        ("settlement_evidence", "watch"),
        ("dispute_window", "watch"),
        ("postmortem", "pass"),
    )


def test_expired_dispute_and_stale_postmortem_block_timeline() -> None:
    timeline = report(
        (
            event(
                1,
                event_type="dispute_window",
                due_at=GENERATED_AT - timedelta(days=2),
                dispute_open=True,
            ),
            event(
                2,
                event_type="postmortem",
                due_at=GENERATED_AT - timedelta(days=3),
            ),
        ),
    )

    assert timeline.status == "block"
    assert timeline.blocked_count == d("2")
    assert timeline.overdue_event_count == d("2")
    assert timeline.reason_codes == (
        "dispute_window_expired_block",
        "postmortem_overdue_block",
    )
    assert tuple(row.status for row in timeline.rows) == ("block", "block")


def test_payload_is_public_json_safe_and_does_not_expose_raw_market_surfaces() -> None:
    timeline = report(
        (
            event(
                1,
                market_id="market-alpha",
                event_type="settlement_evidence",
                due_at=GENERATED_AT - timedelta(minutes=10),
                completed_at=GENERATED_AT - timedelta(minutes=5),
                evidence_count=d("2"),
            ),
        ),
    )

    payload = market_resolution_timeline_report_payload(timeline)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["rows"][0]["evidence_count"] == "2"
    assert payload["rows"][0]["seconds_until_due"] == "-600.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    forbidden_fragments = (
        "raw_question",
        "question",
        "slug",
        "source_url",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "market-alpha",
        "http",
    )
    assert not any(fragment in encoded.lower() for fragment in forbidden_fragments)


def test_validation_rejects_bad_types_future_times_bad_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="info_refresh_grace_seconds"):
        config(info_refresh_grace_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="settlement_evidence_grace_seconds"):
        config(settlement_evidence_grace_seconds=_DecimalSubclass("7200"))
    with pytest.raises(ValueError, match="min_settlement_evidence_count"):
        config(min_settlement_evidence_count=d("1.5"))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="event_type"):
        event(1, event_type="trade")
    with pytest.raises(ValueError, match="market_id"):
        event(1, market_id=" market-alpha")
    with pytest.raises(ValueError, match="market_id"):
        event(1, market_id="market-token")
    with pytest.raises(ValueError, match="due_at"):
        event(1, due_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="completed_at"):
        report(
            (
                event(
                    1,
                    due_at=GENERATED_AT,
                    completed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="evidence_count"):
        event(1, evidence_count=d("-1"))
    with pytest.raises(ValueError, match="dispute_open"):
        replace(event(1), dispute_open=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(event(1), paper_only=False)


def test_strict_input_shape_frozen_dataclasses_and_consistency_checks() -> None:
    supplied = SuppliedEventShape(
        event_id="event-001",
        market_id="market-alpha",
        event_type="info_refresh",
        due_at=GENERATED_AT + timedelta(hours=1),
    )
    timeline = report((supplied,))

    assert type(timeline.rows[0]) is MarketResolutionTimelineRow
    with pytest.raises(FrozenInstanceError):
        timeline.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        timeline.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="pass_count"):
        replace(timeline, pass_count=d("0"))
    with pytest.raises(ValueError, match="status"):
        replace(timeline.rows[0], status="block")
    with pytest.raises(ValueError, match="event rows must be an iterable"):
        report(("not-a-row",))  # type: ignore[arg-type]


def test_owned_module_has_no_trading_db_network_or_filesystem_write_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_resolution_timeline_report.py"
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
        "execute(",
        "insert ",
        "update ",
        "delete ",
        "commit(",
        "trade",
        "order",
        "wallet",
        "token",
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
