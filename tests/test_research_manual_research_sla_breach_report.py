from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_manual_research_sla_breach_report import (
    ResearchManualResearchSlaBreachConfig,
    ResearchManualResearchSlaBreachObservation,
    ResearchManualResearchSlaBreachReasonCodeCount,
    ResearchManualResearchSlaBreachReport,
    ResearchManualResearchSlaBreachRow,
    build_research_manual_research_sla_breach_report,
    research_manual_research_sla_breach_report_digest,
    research_manual_research_sla_breach_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedObservationShape:
    team: str
    event_category: str
    assigned_at: datetime
    due_at: datetime
    source_age_seconds: Decimal
    completed_at: datetime | None = None
    missing_owner_flag: bool = False
    evidence_gap_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class UnsafeSuppliedObservationShape:
    team: str
    event_category: str
    assigned_at: datetime
    due_at: datetime
    source_age_seconds: Decimal
    raw_candidate_id: str
    market_slug: str
    source_url: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchManualResearchSlaBreachConfig:
    values = {
        "config_version": "manual-research-sla-breach-report-v0",
        "fresh_source_age_seconds": d("3600"),
        "stale_source_age_seconds": d("21600"),
        "watch_window_seconds": d("1800"),
    }
    values.update(overrides)
    return ResearchManualResearchSlaBreachConfig(**values)


def observation(
    index: int,
    *,
    team: str = "macro-team",
    event_category: str = "economic-release",
    assigned_at: datetime | None = None,
    due_at: datetime | None = None,
    source_age_seconds: Decimal = d("900"),
    completed_at: datetime | None = None,
    missing_owner_flag: bool = False,
    evidence_gap_flag: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchManualResearchSlaBreachObservation:
    return ResearchManualResearchSlaBreachObservation(
        team=team,
        event_category=event_category,
        assigned_at=(
            assigned_at if assigned_at is not None else GENERATED_AT - timedelta(hours=2)
        ),
        due_at=due_at if due_at is not None else GENERATED_AT + timedelta(hours=2),
        source_age_seconds=source_age_seconds,
        completed_at=completed_at,
        missing_owner_flag=missing_owner_flag,
        evidence_gap_flag=evidence_gap_flag,
        reason_codes=reason_codes or (f"manual_check_{index:03d}",),
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchManualResearchSlaBreachConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchManualResearchSlaBreachReport:
    return build_research_manual_research_sla_breach_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_fresh_open_manual_research_groups_pass_with_public_status_only() -> None:
    sla_report = report(
        (
            observation(2, team="sports-team", event_category="player-news"),
            observation(
                1,
                team="macro-team",
                event_category="economic-release",
                reason_codes=("analyst_acknowledged",),
            ),
        ),
    )

    assert type(sla_report) is ResearchManualResearchSlaBreachReport
    assert sla_report.generated_at == GENERATED_AT
    assert sla_report.config_version == "manual-research-sla-breach-report-v0"
    assert sla_report.group_count == d("2")
    assert sla_report.assignment_count == d("2")
    assert sla_report.pass_count == d("2")
    assert sla_report.watch_count == d("0")
    assert sla_report.block_count == d("0")
    assert sla_report.status == "pass"
    assert sla_report.reason_codes == ("manual_research_sla_pass",)
    assert tuple((row.team, row.event_category) for row in sla_report.rows) == (
        ("macro-team", "economic-release"),
        ("sports-team", "player-news"),
    )

    row = sla_report.rows[0]
    assert type(row) is ResearchManualResearchSlaBreachRow
    assert row.source_freshness_status == "pass"
    assert row.assignment_count == d("1")
    assert row.open_count == d("1")
    assert row.completed_count == d("0")
    assert row.due_soon_count == d("0")
    assert row.active_breach_count == d("0")
    assert row.completed_late_count == d("0")
    assert row.missing_owner_count == d("0")
    assert row.evidence_gap_count == d("0")
    assert row.max_source_age_seconds == d("900")
    assert row.max_overdue_seconds == d("0")
    assert row.status == "pass"
    assert row.reason_codes == (
        "fresh_sources",
        "input_analyst_acknowledged",
        "manual_research_sla_pass",
        "no_manual_research_sla_breach",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert _status_values_are_public(
        research_manual_research_sla_breach_report_payload(sla_report),
    )


def test_due_soon_or_aging_source_groups_watch_without_blocking() -> None:
    sla_report = report(
        (
            observation(
                1,
                due_at=GENERATED_AT + timedelta(minutes=20),
                source_age_seconds=d("7200"),
            ),
        ),
    )

    row = sla_report.rows[0]
    assert sla_report.status == "watch"
    assert sla_report.pass_count == d("0")
    assert sla_report.watch_count == d("1")
    assert sla_report.block_count == d("0")
    assert row.source_freshness_status == "watch"
    assert row.due_soon_count == d("1")
    assert row.status == "watch"
    assert row.reason_codes == (
        "aging_sources",
        "input_manual_check_001",
        "manual_research_due_soon",
        "manual_research_sla_watch",
    )


def test_overdue_missing_owner_and_stale_source_groups_block() -> None:
    sla_report = report(
        (
            observation(
                1,
                team="weather-team",
                event_category="storm-resolution",
                due_at=GENERATED_AT - timedelta(minutes=15),
                source_age_seconds=d("28800"),
                missing_owner_flag=True,
                evidence_gap_flag=True,
                reason_codes=("needs_human_followup",),
            ),
        ),
    )

    row = sla_report.rows[0]
    assert sla_report.status == "block"
    assert sla_report.block_count == d("1")
    assert row.source_freshness_status == "block"
    assert row.active_breach_count == d("1")
    assert row.missing_owner_count == d("1")
    assert row.evidence_gap_count == d("1")
    assert row.max_source_age_seconds == d("28800")
    assert row.max_overdue_seconds == d("900")
    assert row.status == "block"
    assert row.reason_codes == (
        "evidence_gap_present",
        "input_needs_human_followup",
        "manual_research_sla_block",
        "manual_research_sla_overdue",
        "missing_owner_present",
        "stale_sources",
    )


def test_decimal_datetime_enum_and_bool_type_rejections_are_strict() -> None:
    with pytest.raises(ValueError, match="fresh_source_age_seconds"):
        config(fresh_source_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_source_age_seconds"):
        config(stale_source_age_seconds=_DecimalSubclass("21600"))
    with pytest.raises(ValueError, match="watch_window_seconds"):
        config(watch_window_seconds=d("-1"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(1),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_age_seconds"):
        observation(1, source_age_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="team"):
        observation(1, team=" macro-team")
    with pytest.raises(ValueError, match="event_category"):
        observation(1, event_category="market question")
    with pytest.raises(ValueError, match="assigned_at"):
        observation(1, assigned_at=datetime(2026, 7, 8, 10, 0))
    with pytest.raises(ValueError, match="due_at"):
        observation(1, due_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="completed_at"):
        observation(1, completed_at=datetime(2026, 7, 8, 13, 0))
    with pytest.raises(ValueError, match="missing_owner_flag"):
        replace(observation(1), missing_owner_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_gap_flag"):
        replace(observation(1), evidence_gap_flag=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="completed_at"):
        observation(1, completed_at=GENERATED_AT - timedelta(hours=3))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(1, reason_codes=("Needs Review",))


def test_public_payload_and_digest_reject_and_omit_sensitive_identifiers() -> None:
    with pytest.raises(ValueError, match="raw_candidate_id"):
        report(
            (
                UnsafeSuppliedObservationShape(
                    team="macro-team",
                    event_category="economic-release",
                    assigned_at=GENERATED_AT - timedelta(hours=1),
                    due_at=GENERATED_AT + timedelta(hours=1),
                    source_age_seconds=d("900"),
                    raw_candidate_id="candidate-raw-123",
                    market_slug="will-fed-cut-rates",
                    source_url="https://example.test/source",
                ),
            ),
        )
    with pytest.raises(ValueError, match="team"):
        observation(1, team="https://example.test/team")

    public_report = report(
        (
            SuppliedObservationShape(
                team="macro-team",
                event_category="economic-release",
                assigned_at=GENERATED_AT - timedelta(hours=1),
                due_at=GENERATED_AT + timedelta(hours=1),
                source_age_seconds=d("900"),
            ),
        ),
    )
    encoded_report = json.dumps(
        research_manual_research_sla_breach_report_payload(public_report),
        sort_keys=True,
    ).lower()
    encoded_digest = json.dumps(
        research_manual_research_sla_breach_report_digest(public_report),
        sort_keys=True,
    ).lower()

    forbidden_terms = (
        "candidate",
        "market_slug",
        "market_id",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    assert all(term not in encoded_report for term in forbidden_terms)
    assert all(term not in encoded_digest for term in forbidden_terms)


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    item = observation(1)
    sla_report = report((item,))

    with pytest.raises(FrozenInstanceError):
        item.team = "other-team"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        sla_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sla_report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(sla_report, readonly=False)


def test_payload_is_deterministic_decimal_only_and_digest_matches_report() -> None:
    sla_report = report(
        (
            observation(
                3,
                team="z-team",
                event_category="sports-news",
                due_at=GENERATED_AT - timedelta(seconds=30),
                source_age_seconds=d("28800"),
                missing_owner_flag=True,
            ),
            observation(
                1,
                team="a-team",
                event_category="macro-release",
                due_at=GENERATED_AT + timedelta(minutes=15),
                source_age_seconds=d("7200"),
            ),
            observation(
                2,
                team="z-team",
                event_category="sports-news",
                due_at=GENERATED_AT + timedelta(hours=2),
                source_age_seconds=d("900"),
                completed_at=GENERATED_AT - timedelta(minutes=10),
            ),
        ),
    )
    payload = research_manual_research_sla_breach_report_payload(sla_report)
    digest = research_manual_research_sla_breach_report_digest(sla_report)
    encoded_once = json.dumps(payload, sort_keys=True)
    encoded_twice = json.dumps(
        research_manual_research_sla_breach_report_payload(sla_report),
        sort_keys=True,
    )

    assert encoded_once == encoded_twice
    assert tuple(
        (row.team, row.event_category, row.source_freshness_status)
        for row in sla_report.rows
    ) == (
        ("a-team", "macro-release", "watch"),
        ("z-team", "sports-news", "block"),
        ("z-team", "sports-news", "pass"),
    )
    assert sla_report.reason_code_counts == (
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="aging_sources",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="fresh_sources",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="input_manual_check_001",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="input_manual_check_002",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="input_manual_check_003",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="manual_research_due_soon",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="manual_research_sla_block",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="manual_research_sla_overdue",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="manual_research_sla_pass",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="manual_research_sla_watch",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="missing_owner_present",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="no_manual_research_sla_breach",
            count=d("1"),
        ),
        ResearchManualResearchSlaBreachReasonCodeCount(
            reason_code="stale_sources",
            count=d("1"),
        ),
    )
    assert payload["status"] == digest["status"] == "block"
    assert payload["group_count"] == digest["group_count"] == "3"
    assert payload["assignment_count"] == digest["assignment_count"] == "3"
    assert payload["pass_count"] == digest["pass_count"] == "1"
    assert payload["watch_count"] == digest["watch_count"] == "1"
    assert payload["block_count"] == digest["block_count"] == "1"
    assert digest["team_statuses"] == [
        {"assignment_count": "1", "status": "watch", "team": "a-team"},
        {"assignment_count": "2", "status": "block", "team": "z-team"},
    ]
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(isinstance(value, int) for value in _walk_payload_values(payload))
    assert _status_values_are_public(payload)
    assert _status_values_are_public(digest)


def test_owned_module_has_no_network_filesystem_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_manual_research_sla_breach_report.py"
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
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
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


def _status_values_are_public(value: object) -> bool:
    allowed = {"pass", "watch", "block"}
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("status") and item not in allowed:
                return False
            if not _status_values_are_public(item):
                return False
    elif isinstance(value, list):
        return all(_status_values_are_public(item) for item in value)
    return True
