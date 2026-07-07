from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_team_specialization_feedback_loop import (
    ResearchTeamSpecializationFeedbackLoopConfig,
    ResearchTeamSpecializationFeedbackLoopReport,
    ResearchTeamSpecializationFeedbackLoopRow,
    TeamSpecializationFeedbackInput,
    TeamSpecializationMemoryUpdateSuggestion,
    build_research_team_specialization_feedback_loop_report,
    research_team_specialization_feedback_loop_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedFeedbackShape:
    team_id: str
    category_id: str
    evaluated_case_count: Decimal
    hit_count: Decimal
    mean_calibration_error: Decimal
    unresolved_information_gap_count: Decimal
    postmortem_feedback_count: Decimal
    stale_memory_item_count: Decimal
    updated_at: datetime
    gap_tags: tuple[str, ...] = ()
    feedback_tags: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchTeamSpecializationFeedbackLoopConfig:
    values = {
        "config_version": "research-team-specialization-feedback-loop-v0",
        "pass_hit_rate": d("0.600000"),
        "watch_hit_rate": d("0.450000"),
        "pass_calibration_error": d("0.120000"),
        "watch_calibration_error": d("0.220000"),
        "max_watch_gap_ratio": d("0.300000"),
        "max_watch_stale_memory_ratio": d("0.300000"),
    }
    values.update(overrides)
    return ResearchTeamSpecializationFeedbackLoopConfig(**values)


def feedback(
    *,
    team_id: str = "politics",
    category_id: str = "politics",
    evaluated_case_count: Decimal = d("10"),
    hit_count: Decimal = d("7"),
    mean_calibration_error: Decimal = d("0.090000"),
    unresolved_information_gap_count: Decimal = d("1"),
    postmortem_feedback_count: Decimal = d("3"),
    stale_memory_item_count: Decimal = d("0"),
    updated_at: datetime = GENERATED_AT,
    gap_tags: tuple[str, ...] = ("calendar_gap",),
    feedback_tags: tuple[str, ...] = ("postmortem_digest",),
) -> TeamSpecializationFeedbackInput:
    return TeamSpecializationFeedbackInput(
        team_id=team_id,
        category_id=category_id,
        evaluated_case_count=evaluated_case_count,
        hit_count=hit_count,
        mean_calibration_error=mean_calibration_error,
        unresolved_information_gap_count=unresolved_information_gap_count,
        postmortem_feedback_count=postmortem_feedback_count,
        stale_memory_item_count=stale_memory_item_count,
        updated_at=updated_at,
        gap_tags=gap_tags,
        feedback_tags=feedback_tags,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchTeamSpecializationFeedbackLoopConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamSpecializationFeedbackLoopReport:
    return build_research_team_specialization_feedback_loop_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_pure_report() -> None:
    feedback_report = report(())

    assert type(feedback_report) is ResearchTeamSpecializationFeedbackLoopReport
    assert feedback_report.generated_at == GENERATED_AT
    assert feedback_report.config_version == "research-team-specialization-feedback-loop-v0"
    assert feedback_report.team_count == d("0")
    assert feedback_report.pass_count == d("0")
    assert feedback_report.watch_count == d("0")
    assert feedback_report.block_count == d("0")
    assert feedback_report.average_hit_rate is None
    assert feedback_report.average_calibration_error is None
    assert feedback_report.status == "block"
    assert feedback_report.reason_codes == ("no_team_feedback",)
    assert feedback_report.rows == ()
    assert feedback_report.memory_update_suggestions == ()
    assert feedback_report.paper_only is True
    assert feedback_report.report_only is True
    assert feedback_report.readonly is True


def test_politics_finance_and_sports_rows_generate_pass_watch_block() -> None:
    feedback_report = report(
        (
            feedback(
                team_id="sports_soccer",
                category_id="sports.soccer",
                evaluated_case_count=d("8"),
                hit_count=d("2"),
                mean_calibration_error=d("0.310000"),
                unresolved_information_gap_count=d("4"),
                postmortem_feedback_count=d("0"),
                stale_memory_item_count=d("3"),
                gap_tags=("lineup_gap", "injury_gap"),
                feedback_tags=(),
            ),
            feedback(
                team_id="politics",
                category_id="politics",
                evaluated_case_count=d("10"),
                hit_count=d("8"),
                mean_calibration_error=d("0.080000"),
                unresolved_information_gap_count=d("1"),
                postmortem_feedback_count=d("4"),
                stale_memory_item_count=d("0"),
                gap_tags=("calendar_gap",),
                feedback_tags=("debate_review",),
            ),
            feedback(
                team_id="macro_rates",
                category_id="finance.macro.rates",
                evaluated_case_count=d("10"),
                hit_count=d("5"),
                mean_calibration_error=d("0.180000"),
                unresolved_information_gap_count=d("3"),
                postmortem_feedback_count=d("1"),
                stale_memory_item_count=d("2"),
                gap_tags=("econ_release_gap",),
                feedback_tags=("fomc_review",),
            ),
        ),
    )

    assert feedback_report.status == "block"
    assert feedback_report.team_count == d("3")
    assert feedback_report.pass_count == d("1")
    assert feedback_report.watch_count == d("1")
    assert feedback_report.block_count == d("1")
    assert feedback_report.average_hit_rate == d("0.516667")
    assert feedback_report.average_calibration_error == d("0.190000")
    assert tuple(row.team_id for row in feedback_report.rows) == (
        "macro_rates",
        "politics",
        "sports_soccer",
    )

    macro_row, politics_row, sports_row = feedback_report.rows
    assert type(politics_row) is ResearchTeamSpecializationFeedbackLoopRow
    assert politics_row.status == "pass"
    assert politics_row.hit_rate == d("0.800000")
    assert politics_row.information_gap_ratio == d("0.100000")
    assert politics_row.memory_stale_ratio == d("0.000000")
    assert politics_row.reason_codes == (
        "calibration_error_pass",
        "feedback_present",
        "historical_hit_rate_pass",
        "information_gap_controlled",
        "memory_current",
        "team_specialization_pass",
    )
    assert macro_row.status == "watch"
    assert macro_row.reason_codes == (
        "calibration_error_watch",
        "feedback_present",
        "historical_hit_rate_watch",
        "information_gap_watch",
        "memory_update_needed",
        "team_specialization_watch",
    )
    assert sports_row.status == "block"
    assert sports_row.reason_codes == (
        "calibration_error_block",
        "feedback_missing",
        "historical_hit_rate_block",
        "information_gap_block",
        "memory_update_needed",
        "team_specialization_block",
    )

    assert feedback_report.memory_update_suggestions == (
        TeamSpecializationMemoryUpdateSuggestion(
            team_id="macro_rates",
            category_id="finance.macro.rates",
            status="watch",
            suggestion_codes=(
                "refresh_team_memory",
                "tighten_calibration_review",
                "triage_information_gaps",
            ),
            reason_codes=(
                "memory_update_needed",
                "specialization_watch",
            ),
        ),
        TeamSpecializationMemoryUpdateSuggestion(
            team_id="politics",
            category_id="politics",
            status="pass",
            suggestion_codes=("keep_current_specialization_memory",),
            reason_codes=("specialization_pass",),
        ),
        TeamSpecializationMemoryUpdateSuggestion(
            team_id="sports_soccer",
            category_id="sports.soccer",
            status="block",
            suggestion_codes=(
                "capture_postmortem_feedback",
                "rebuild_team_memory",
                "resolve_information_gaps_before_research_reuse",
                "tighten_calibration_review",
            ),
            reason_codes=(
                "memory_update_required",
                "specialization_block",
            ),
        ),
    )


def test_payload_is_deterministic_decimal_only_and_public_safe() -> None:
    feedback_report = report(
        (
            SuppliedFeedbackShape(
                team_id="sports_basketball",
                category_id="sports.basketball",
                evaluated_case_count=d("4"),
                hit_count=d("2"),
                mean_calibration_error=d("0.180000"),
                unresolved_information_gap_count=d("1"),
                postmortem_feedback_count=d("1"),
                stale_memory_item_count=d("1"),
                updated_at=GENERATED_AT,
                gap_tags=("rotation_gap", "schedule_gap"),
                feedback_tags=("injury_review",),
            ),
            SuppliedFeedbackShape(
                team_id="equity_indices",
                category_id="finance.equity.indices",
                evaluated_case_count=d("5"),
                hit_count=d("4"),
                mean_calibration_error=d("0.060000"),
                unresolved_information_gap_count=d("0"),
                postmortem_feedback_count=d("2"),
                stale_memory_item_count=d("0"),
                updated_at=GENERATED_AT,
                gap_tags=(),
                feedback_tags=("earnings_review",),
            ),
        ),
    )

    payload = research_team_specialization_feedback_loop_payload(feedback_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["team_id"] == "equity_indices"
    assert payload["rows"][0]["hit_rate"] == "0.800000"
    assert payload["rows"][1]["information_gap_ratio"] == "0.250000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    forbidden_fragments = (
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "buy",
        "sell",
        "position",
        "recommend",
        "wallet",
        "order",
    )
    assert not any(fragment in encoded.lower() for fragment in forbidden_fragments)


def test_validation_rejects_bad_types_unknown_teams_pair_mismatch_and_flags() -> None:
    with pytest.raises(ValueError, match="pass_hit_rate"):
        config(pass_hit_rate=0.6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_hit_rate"):
        config(watch_hit_rate=_DecimalSubclass("0.450000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((feedback(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((feedback(),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="team_id"):
        feedback(team_id="politics ")
    with pytest.raises(ValueError, match="category_id"):
        feedback(team_id="politics", category_id="sports.soccer")
    with pytest.raises(ValueError, match="evaluated_case_count"):
        feedback(evaluated_case_count=d("1.5"))
    with pytest.raises(ValueError, match="hit_count"):
        feedback(evaluated_case_count=d("2"), hit_count=d("3"))
    with pytest.raises(ValueError, match="mean_calibration_error"):
        feedback(mean_calibration_error=d("1.100000"))
    with pytest.raises(ValueError, match="gap_tags"):
        feedback(gap_tags=("Raw Text",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(feedback(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_report_consistency_is_strict() -> None:
    feedback_report = report((feedback(),))

    with pytest.raises(FrozenInstanceError):
        feedback_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        feedback_report.rows[0].hit_rate = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="hit_rate"):
        replace(feedback_report.rows[0], hit_rate=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(feedback_report, status="watch")


def test_owned_module_has_no_network_filesystem_db_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_specialization_feedback_loop.py"
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
        "commit(",
        "rollback(",
        "execute(",
        "wallet",
        "order",
        "auth",
        "private_key",
        "buy",
        "sell",
        "position",
        "recommend",
        "candidate",
        "market",
        "source",
        "url",
        "dsn",
        "table",
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
