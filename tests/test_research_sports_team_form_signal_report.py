from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_sports_team_form_signal_report import (
    ResearchSportsTeamFormSignalConfig,
    ResearchSportsTeamFormSignalInputRow,
    ResearchSportsTeamFormSignalReasonCodeCount,
    ResearchSportsTeamFormSignalReport,
    ResearchSportsTeamFormSignalRow,
    build_research_sports_team_form_signal_report,
    research_sports_team_form_signal_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSportsTeamFormSignalConfig:
    values = {
        "config_version": "research-sports-team-form-signal-report-v0",
        "min_recent_games": d("3"),
        "recent_form_pass_score": d("0.600000"),
        "recent_form_block_score": d("0.300000"),
        "availability_watch_threshold": d("0.700000"),
        "availability_block_threshold": d("0.400000"),
        "key_absence_watch_count": d("1"),
        "key_absence_block_count": d("3"),
        "schedule_watch_games_last_7_days": d("3"),
        "schedule_block_games_last_7_days": d("4"),
        "rest_days_watch_threshold": d("2"),
        "rest_days_block_threshold": d("1"),
        "venue_watch_threshold": d("0.450000"),
        "venue_block_threshold": d("0.250000"),
        "fresh_information_max_age_seconds": d("3600"),
        "stale_information_block_age_seconds": d("21600"),
        "contradiction_watch_ratio": d("0.250000"),
        "contradiction_block_ratio": d("0.500000"),
        "overall_pass_score": d("0.700000"),
        "overall_watch_score": d("0.450000"),
    }
    values.update(overrides)
    return ResearchSportsTeamFormSignalConfig(**values)


def input_row(
    index: int,
    *,
    research_key: str | None = None,
    participant_label: str | None = None,
    participant_kind: str = "team",
    side: str = "home",
    latest_information_observed_at: datetime | None = None,
    recent_games_played: Decimal = d("5"),
    recent_win_count: Decimal = d("4"),
    recent_draw_count: Decimal = d("0"),
    recent_loss_count: Decimal = d("1"),
    recent_point_differential: Decimal = d("35"),
    availability_score: Decimal = d("0.900000"),
    key_absence_count: Decimal = d("0"),
    schedule_games_last_7_days: Decimal = d("2"),
    rest_days: Decimal = d("3"),
    venue_support_score: Decimal = d("0.800000"),
    corroborating_signal_count: Decimal = d("3"),
    contradiction_signal_count: Decimal = d("0"),
    public_context_note: str | None = "Beat report says rotation is intact",
) -> ResearchSportsTeamFormSignalInputRow:
    return ResearchSportsTeamFormSignalInputRow(
        research_key=research_key or f"sports-signal-{index:03d}",
        participant_label=participant_label or f"Participant {index}",
        participant_kind=participant_kind,
        side=side,
        latest_information_observed_at=(
            latest_information_observed_at
            or GENERATED_AT - timedelta(minutes=30)
        ),
        recent_games_played=recent_games_played,
        recent_win_count=recent_win_count,
        recent_draw_count=recent_draw_count,
        recent_loss_count=recent_loss_count,
        recent_point_differential=recent_point_differential,
        availability_score=availability_score,
        key_absence_count=key_absence_count,
        schedule_games_last_7_days=schedule_games_last_7_days,
        rest_days=rest_days,
        venue_support_score=venue_support_score,
        corroborating_signal_count=corroborating_signal_count,
        contradiction_signal_count=contradiction_signal_count,
        public_context_note=public_context_note,
    )


def report(
    rows: tuple[ResearchSportsTeamFormSignalInputRow, ...],
    *,
    cfg: ResearchSportsTeamFormSignalConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSportsTeamFormSignalReport:
    return build_research_sports_team_form_signal_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_with_zero_counts() -> None:
    form_report = report(())

    assert type(form_report) is ResearchSportsTeamFormSignalReport
    assert form_report.generated_at == GENERATED_AT
    assert form_report.config_version == "research-sports-team-form-signal-report-v0"
    assert form_report.status == "block"
    assert form_report.subject_count == d("0")
    assert form_report.pass_count == d("0")
    assert form_report.watch_count == d("0")
    assert form_report.block_count == d("0")
    assert form_report.stale_information_count == d("0")
    assert form_report.injury_concern_count == d("0")
    assert form_report.dense_schedule_count == d("0")
    assert form_report.contradiction_count == d("0")
    assert form_report.average_signal_score == d("0")
    assert form_report.average_information_age_seconds == d("0")
    assert form_report.min_rest_days == d("0")
    assert form_report.reason_codes == ("no_sports_subjects",)
    assert form_report.reason_code_counts == (
        ResearchSportsTeamFormSignalReasonCodeCount(
            reason_code="no_sports_subjects",
            count=d("1"),
            subject_ratio=d("1.000000"),
        ),
    )
    assert form_report.rows == ()
    assert form_report.paper_only is True
    assert form_report.report_only is True
    assert form_report.readonly is True


def test_clear_team_form_signal_passes_with_safe_public_payload() -> None:
    form_report = report((input_row(1),))
    payload = research_sports_team_form_signal_report_payload(form_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert form_report.status == "pass"
    assert form_report.subject_count == d("1")
    assert form_report.pass_count == d("1")
    assert form_report.watch_count == d("0")
    assert form_report.block_count == d("0")
    assert form_report.average_signal_score == d("0.862000")
    assert form_report.average_information_age_seconds == d("1800")
    assert form_report.min_rest_days == d("3")

    row = form_report.rows[0]
    assert type(row) is ResearchSportsTeamFormSignalRow
    assert row.research_key == "sports-signal-001"
    assert row.participant_label == "Participant 1"
    assert row.participant_kind == "team"
    assert row.side == "home"
    assert row.information_age_seconds == d("1800")
    assert row.recent_form_score == d("0.815000")
    assert row.availability_score == d("0.900000")
    assert row.schedule_density_score == d("0.750000")
    assert row.venue_support_score == d("0.800000")
    assert row.freshness_score == d("1.000000")
    assert row.contradiction_ratio == d("0.000000")
    assert row.contradiction_score == d("1.000000")
    assert row.team_form_signal_score == d("0.862000")
    assert row.team_form_signal_status == "pass"
    assert row.redacted_context_note == "note_provided"
    assert row.reason_codes == (
        "availability_clear",
        "contradiction_clear",
        "fresh_information",
        "recent_form_clear",
        "schedule_density_clear",
        "sports_form_signal_pass",
        "venue_support_clear",
    )

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["team_form_signal_score"] == "0.862000"
    assert payload["rows"][0]["redacted_context_note"] == "note_provided"
    assert "Beat report says rotation is intact" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not _payload_contains_identifier_surface(payload)


def test_fatigued_injured_stale_and_contradicted_subject_blocks() -> None:
    form_report = report(
        (
            input_row(
                1,
                side="away",
                latest_information_observed_at=GENERATED_AT - timedelta(hours=8),
                recent_games_played=d("4"),
                recent_win_count=d("0"),
                recent_draw_count=d("0"),
                recent_loss_count=d("4"),
                recent_point_differential=d("-48"),
                availability_score=d("0.250000"),
                key_absence_count=d("4"),
                schedule_games_last_7_days=d("5"),
                rest_days=d("0"),
                venue_support_score=d("0.150000"),
                corroborating_signal_count=d("1"),
                contradiction_signal_count=d("2"),
                public_context_note=None,
            ),
        ),
    )

    row = form_report.rows[0]
    assert form_report.status == "block"
    assert form_report.block_count == d("1")
    assert form_report.stale_information_count == d("1")
    assert form_report.injury_concern_count == d("1")
    assert form_report.dense_schedule_count == d("1")
    assert form_report.contradiction_count == d("1")
    assert form_report.average_signal_score == d("0.121250")
    assert row.information_age_seconds == d("28800")
    assert row.recent_form_score == d("0.000000")
    assert row.schedule_density_score == d("0.000000")
    assert row.contradiction_ratio == d("0.666667")
    assert row.team_form_signal_status == "block"
    assert row.redacted_context_note is None
    assert row.reason_codes == (
        "availability_block",
        "contradiction_block",
        "information_stale_block",
        "key_absence_block",
        "low_rest_block",
        "recent_form_block",
        "schedule_density_block",
        "sports_form_signal_block",
        "venue_support_block",
    )


def test_watch_signal_sorts_rows_and_summarizes_reason_counts() -> None:
    form_report = report(
        (
            input_row(
                2,
                research_key="z-watch",
                participant_kind="player",
                side="away",
                latest_information_observed_at=GENERATED_AT - timedelta(hours=3),
                recent_win_count=d("2"),
                recent_draw_count=d("1"),
                recent_loss_count=d("2"),
                recent_point_differential=d("0"),
                availability_score=d("0.650000"),
                key_absence_count=d("1"),
                schedule_games_last_7_days=d("3"),
                rest_days=d("2"),
                venue_support_score=d("0.350000"),
                corroborating_signal_count=d("3"),
                contradiction_signal_count=d("1"),
            ),
            input_row(1, research_key="a-pass"),
        ),
    )

    assert tuple(row.research_key for row in form_report.rows) == ("a-pass", "z-watch")
    assert form_report.status == "watch"
    assert form_report.pass_count == d("1")
    assert form_report.watch_count == d("1")
    assert form_report.block_count == d("0")
    assert form_report.reason_codes == (
        "availability_watch",
        "contradiction_watch",
        "information_stale_watch",
        "key_absence_watch",
        "low_rest_watch",
        "recent_form_watch",
        "schedule_density_watch",
        "sports_form_signal_watch",
        "venue_support_watch",
    )
    assert tuple(
        (count.reason_code, count.count, count.subject_ratio)
        for count in form_report.reason_code_counts
        if count.reason_code.endswith("_watch")
    ) == (
        ("availability_watch", d("1"), d("0.500000")),
        ("contradiction_watch", d("1"), d("0.500000")),
        ("information_stale_watch", d("1"), d("0.500000")),
        ("key_absence_watch", d("1"), d("0.500000")),
        ("low_rest_watch", d("1"), d("0.500000")),
        ("recent_form_watch", d("1"), d("0.500000")),
        ("schedule_density_watch", d("1"), d("0.500000")),
        ("sports_form_signal_watch", d("1"), d("0.500000")),
        ("venue_support_watch", d("1"), d("0.500000")),
    )


def test_validation_rejects_bad_types_future_times_bad_counts_and_flags() -> None:
    with pytest.raises(ValueError, match="recent_form_pass_score"):
        config(recent_form_pass_score=d("0.200000"))
    with pytest.raises(ValueError, match="availability_score"):
        input_row(1, availability_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="availability_score"):
        input_row(1, availability_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((input_row(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (input_row(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_key"):
        input_row(1, research_key=" sports-signal-001")
    with pytest.raises(ValueError, match="participant_kind"):
        input_row(1, participant_kind="coach")
    with pytest.raises(ValueError, match="side"):
        input_row(1, side="road")
    with pytest.raises(ValueError, match="recent game counts"):
        input_row(1, recent_win_count=d("3"))
    with pytest.raises(ValueError, match="latest_information_observed_at"):
        report(
            (
                input_row(
                    1,
                    latest_information_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="public_context_note"):
        input_row(1, public_context_note="raw market id leaked")
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_reports_validate_consistency() -> None:
    form_report = report((input_row(1),))

    with pytest.raises(FrozenInstanceError):
        form_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        form_report.rows[0].availability_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="team_form_signal_status"):
        replace(form_report.rows[0], team_form_signal_status="watch")
    with pytest.raises(ValueError, match="status"):
        replace(form_report, status="watch")


def test_owned_module_has_no_network_db_file_mutation_or_action_language_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_sports_team_form_signal_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "pymongo",
        "open(",
        ".write(",
        "execute(",
        "connect(",
        "buy",
        "sell",
        "position",
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


def _payload_contains_identifier_surface(value: object) -> bool:
    unsafe_key_tokens = (
        "raw_source",
        "raw_sources",
        "raw_market",
        "raw_markets",
        "raw_event",
        "raw_events",
        "raw_condition",
        "raw_conditions",
        "source_id",
        "source_label",
        "market_id",
        "market_slug",
        "event_id",
        "event_slug",
        "condition_id",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in unsafe_key_tokens:
                return True
            if _payload_contains_identifier_surface(item):
                return True
        return False
    if isinstance(value, list):
        return any(_payload_contains_identifier_surface(item) for item in value)
    if isinstance(value, str):
        return any(token in value.lower() for token in unsafe_key_tokens)
    return False
