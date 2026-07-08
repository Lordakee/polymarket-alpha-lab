from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_trigger_calendar_readiness_report import (
    DEFAULT_RESEARCH_EVENT_TRIGGER_CALENDAR_READINESS_CONFIG_VERSION,
    ResearchEventTriggerCalendarReadinessConfig,
    ResearchEventTriggerCalendarReadinessInput,
    ResearchEventTriggerCalendarReadinessReasonCodeCount,
    ResearchEventTriggerCalendarReadinessReport,
    ResearchEventTriggerCalendarReadinessRow,
    build_research_event_trigger_calendar_readiness_report,
    research_event_trigger_calendar_readiness_report_digest,
    research_event_trigger_calendar_readiness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
_DEFAULT = object()


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchEventTriggerCalendarReadinessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_TRIGGER_CALENDAR_READINESS_CONFIG_VERSION
        ),
        "watch_trigger_window_seconds": d("86400.000000"),
        "max_evidence_age_seconds": d("86400.000000"),
        "min_watch_team_capacity_ratio": d("0.500000"),
    }
    values.update(overrides)
    return ResearchEventTriggerCalendarReadinessConfig(**values)


def readiness_input(
    research_event_key: str = "event.alpha",
    *,
    event_family: str = "economic_calendar",
    trigger_at: datetime | None = None,
    latest_source_refresh_at: datetime | None | object = _DEFAULT,
    source_refresh_window_seconds: Decimal = d("14400.000000"),
    latest_evidence_at: datetime | None | object = _DEFAULT,
    evidence_item_count: Decimal = d("3.000000"),
    available_researcher_count: Decimal = d("2.000000"),
    team_available_hours: Decimal = d("6.000000"),
    required_research_hours: Decimal = d("4.000000"),
    hard_calendar_conflict: bool = False,
    hard_evidence_gap: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventTriggerCalendarReadinessInput:
    return ResearchEventTriggerCalendarReadinessInput(
        research_event_key=research_event_key,
        event_family=event_family,
        trigger_at=trigger_at or GENERATED_AT + timedelta(days=2),
        latest_source_refresh_at=latest_source_refresh_at
        if latest_source_refresh_at is not _DEFAULT
        else GENERATED_AT - timedelta(hours=1),
        source_refresh_window_seconds=source_refresh_window_seconds,
        latest_evidence_at=latest_evidence_at
        if latest_evidence_at is not _DEFAULT
        else GENERATED_AT - timedelta(hours=3),
        evidence_item_count=evidence_item_count,
        available_researcher_count=available_researcher_count,
        team_available_hours=team_available_hours,
        required_research_hours=required_research_hours,
        hard_calendar_conflict=hard_calendar_conflict,
        hard_evidence_gap=hard_evidence_gap,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchEventTriggerCalendarReadinessInput, ...],
    *,
    cfg: ResearchEventTriggerCalendarReadinessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventTriggerCalendarReadinessReport:
    return build_research_event_trigger_calendar_readiness_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_event_trigger_calendar_readiness_reduces_pass_watch_and_block() -> None:
    summary = report(
        (
            readiness_input(
                "event.pass",
                trigger_at=GENERATED_AT + timedelta(days=3),
                latest_source_refresh_at=GENERATED_AT - timedelta(hours=1),
                latest_evidence_at=GENERATED_AT - timedelta(hours=2),
                team_available_hours=d("8.000000"),
                required_research_hours=d("4.000000"),
            ),
            readiness_input(
                "event.watch",
                trigger_at=GENERATED_AT + timedelta(hours=6),
                latest_source_refresh_at=GENERATED_AT - timedelta(hours=8),
                source_refresh_window_seconds=d("14400.000000"),
                latest_evidence_at=GENERATED_AT - timedelta(hours=30),
                team_available_hours=d("3.000000"),
                required_research_hours=d("4.000000"),
            ),
            readiness_input(
                "event.block",
                trigger_at=GENERATED_AT - timedelta(hours=1),
                latest_source_refresh_at=None,
                latest_evidence_at=None,
                evidence_item_count=d("0.000000"),
                available_researcher_count=d("0.000000"),
                team_available_hours=d("0.000000"),
                required_research_hours=d("4.000000"),
                hard_calendar_conflict=True,
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, ResearchEventTriggerCalendarReadinessReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_EVENT_TRIGGER_CALENDAR_READINESS_CONFIG_VERSION
    )
    assert summary.readiness_status == "block"
    assert summary.public_next_step == "pause_report_only_research_readiness"
    assert summary.event_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.source_refresh_due_count == d("1.000000")
    assert summary.source_refresh_missing_count == d("1.000000")
    assert summary.evidence_stale_count == d("1.000000")
    assert summary.evidence_missing_count == d("1.000000")
    assert summary.team_capacity_thin_count == d("1.000000")
    assert summary.team_unavailable_count == d("1.000000")
    assert summary.hard_flag_count == d("1.000000")
    assert summary.average_team_capacity_ratio == d("0.916667")
    assert summary.average_latest_evidence_age_seconds == d("57600.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.research_event_key for row in summary.rows) == (
        "event.block",
        "event.watch",
        "event.pass",
    )

    blocked = summary.rows[0]
    assert blocked.readiness_status == "block"
    assert blocked.public_next_step == "pause_report_only_research_readiness"
    assert blocked.event_trigger_seconds == d("-3600.000000")
    assert blocked.latest_source_age_seconds is None
    assert blocked.latest_evidence_age_seconds is None
    assert blocked.team_capacity_ratio == d("0.000000")
    assert blocked.reason_codes == (
        "event_trigger_calendar_readiness_event_elapsed",
        "event_trigger_calendar_readiness_source_refresh_missing",
        "event_trigger_calendar_readiness_team_unavailable",
        "event_trigger_calendar_readiness_evidence_missing",
        "event_trigger_calendar_readiness_hard_calendar_conflict",
    )

    watched = summary.rows[1]
    assert watched.readiness_status == "watch"
    assert watched.public_next_step == "watch_report_only_research_readiness"
    assert watched.event_trigger_seconds == d("21600.000000")
    assert watched.latest_source_age_seconds == d("28800.000000")
    assert watched.latest_evidence_age_seconds == d("108000.000000")
    assert watched.team_capacity_ratio == d("0.750000")
    assert watched.reason_codes == (
        "event_trigger_calendar_readiness_event_near",
        "event_trigger_calendar_readiness_source_refresh_due",
        "event_trigger_calendar_readiness_team_capacity_thin",
        "event_trigger_calendar_readiness_evidence_stale",
    )

    passed = summary.rows[2]
    assert passed.readiness_status == "pass"
    assert passed.public_next_step == "continue_report_only_research_readiness"
    assert passed.event_trigger_seconds == d("259200.000000")
    assert passed.latest_source_age_seconds == d("3600.000000")
    assert passed.latest_evidence_age_seconds == d("7200.000000")
    assert passed.team_capacity_ratio == d("2.000000")
    assert passed.reason_codes == (
        "event_trigger_calendar_readiness_pass",
        "event_trigger_calendar_readiness_source_refresh_current",
        "event_trigger_calendar_readiness_team_capacity_ready",
        "event_trigger_calendar_readiness_evidence_fresh",
    )

    assert summary.reason_code_counts == (
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_event_elapsed",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_event_near",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_source_refresh_current",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_source_refresh_due",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_source_refresh_missing",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_team_capacity_ready",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_team_capacity_thin",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_team_unavailable",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_evidence_fresh",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_evidence_stale",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_evidence_missing",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_hard_calendar_conflict",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_pass",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )


def test_event_trigger_calendar_readiness_empty_inputs_blocks_report_only() -> None:
    summary = report(())

    assert summary.readiness_status == "block"
    assert summary.public_next_step == "pause_report_only_research_readiness"
    assert summary.event_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == (
        "event_trigger_calendar_readiness_no_inputs",
    )
    assert summary.reason_code_counts == (
        ResearchEventTriggerCalendarReadinessReasonCodeCount(
            reason_code="event_trigger_calendar_readiness_no_inputs",
            count=d("1.000000"),
            event_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_event_trigger_calendar_readiness_validates_decimal_datetime_and_types() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        readiness_input(evidence_item_count=1)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="datetime"):
        readiness_input(trigger_at="2026-07-08T12:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="timezone"):
        readiness_input(trigger_at=datetime(2026, 7, 8, 13, 0))

    with pytest.raises(ValueError, match="whole second"):
        readiness_input(trigger_at=datetime(2026, 7, 8, 13, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(TypeError, match="exactly str"):
        readiness_input(research_event_key=_StringSubclass("event.alpha"))

    with pytest.raises(TypeError, match="exactly datetime"):
        readiness_input(trigger_at=_DateTimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))

    with pytest.raises(TypeError, match="exactly Decimal"):
        readiness_input(evidence_item_count=_DecimalSubclass("1.000000"))

    with pytest.raises(TypeError, match="bool"):
        readiness_input(hard_evidence_gap="false")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="whole count"):
        readiness_input(evidence_item_count=d("1.500000"))

    with pytest.raises(ValueError, match="positive"):
        readiness_input(required_research_hours=d("0.000000"))

    with pytest.raises(ValueError, match="future"):
        report(
            (
                readiness_input(
                    latest_source_refresh_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )

    frozen = readiness_input()
    with pytest.raises(FrozenInstanceError):
        frozen.team_available_hours = d("99.000000")  # type: ignore[misc]

    assert replace(frozen, team_available_hours=d("7.000000")).team_available_hours == d(
        "7.000000",
    )


def test_event_trigger_calendar_readiness_rejects_public_leaks_and_status_values() -> None:
    unsafe_values = (
        "candidate-raw-123",
        "market_id-123",
        "market_slug-foo",
        "market_question-text",
        "source_ref-private",
        "source_url-private",
        "source_text-private",
        "postgres-dsn",
        "table-private",
        "secret-token",
        "wallet-secret",
        "auth-secret",
        "order-ticket",
        "trade-ticket",
        "position-ticket",
        "buy-signal",
        "sell-signal",
        "recommendation-signal",
    )
    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            readiness_input(research_event_key=value)

    summary = report((readiness_input(),))
    with pytest.raises(ValueError, match="public status"):
        replace(summary.rows[0], readiness_status="ready")

    with pytest.raises(ValueError, match="public status"):
        replace(summary, readiness_status="blocked")

    public = repr(asdict(summary)).lower() + repr(summary.payload).lower()
    for token in (
        "candidate-raw",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "postgres-dsn",
        "table-private",
        "secret-token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert token not in public


def test_event_trigger_calendar_readiness_enforces_hard_flags() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        readiness_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        readiness_input(readonly=False)

    hard = report((readiness_input(hard_evidence_gap=True),))
    assert hard.readiness_status == "block"
    assert hard.rows[0].readiness_status == "block"
    assert hard.hard_flag_count == d("1.000000")
    assert "event_trigger_calendar_readiness_hard_evidence_gap" in hard.reason_codes

    with pytest.raises(ValueError, match="paper_only"):
        replace(hard, paper_only=False)


def test_event_trigger_calendar_readiness_payload_and_digest_are_deterministic() -> None:
    first = report(
        (
            readiness_input("event.zeta"),
            readiness_input("event.alpha"),
            readiness_input(
                "event.mid",
                latest_source_refresh_at=GENERATED_AT - timedelta(hours=9),
            ),
        ),
    )
    second = report(
        (
            readiness_input(
                "event.mid",
                latest_source_refresh_at=GENERATED_AT - timedelta(hours=9),
            ),
            readiness_input("event.alpha"),
            readiness_input("event.zeta"),
        ),
    )

    assert tuple(row.research_event_key for row in first.rows) == (
        "event.mid",
        "event.alpha",
        "event.zeta",
    )
    assert research_event_trigger_calendar_readiness_report_payload(first) == (
        research_event_trigger_calendar_readiness_report_payload(second)
    )
    assert research_event_trigger_calendar_readiness_report_digest(first) == (
        research_event_trigger_calendar_readiness_report_digest(second)
    )
    assert first.payload == research_event_trigger_calendar_readiness_report_payload(first)
    assert first.digest == research_event_trigger_calendar_readiness_report_digest(first)
    assert first.payload["event_count"] == "3.000000"
    assert first.payload["rows"][0]["latest_source_age_seconds"] == "32400.000000"
    assert first.payload["generated_at"] == "2026-07-08T12:00:00+00:00"

    encoded = json.dumps(first.payload, sort_keys=True, separators=(",", ":"))
    assert first.digest == sha256(encoded.encode()).hexdigest()


def test_event_trigger_calendar_readiness_report_is_read_only_and_frozen() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_trigger_calendar_readiness_report.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "delete",
        "cursor",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    forbidden_source_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert not any(term in source.lower() for term in forbidden_source_terms)

    for cls in (
        ResearchEventTriggerCalendarReadinessConfig,
        ResearchEventTriggerCalendarReadinessInput,
        ResearchEventTriggerCalendarReadinessRow,
        ResearchEventTriggerCalendarReadinessReasonCodeCount,
        ResearchEventTriggerCalendarReadinessReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
