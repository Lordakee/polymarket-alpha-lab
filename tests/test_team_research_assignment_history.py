from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_research_assignment import (
    TeamResearchAssignmentReport,
    TeamResearchAssignmentRow,
    TeamResearchAssignmentTeamSummary,
)
from polymarket_alpha_lab.team_research_assignment_history import (
    TeamResearchAssignmentHistoryConfig,
    TeamResearchAssignmentHistoryStatusRow,
    build_team_research_assignment_history_report,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def test_empty_history_is_blocked_with_zeroed_report_only_summary() -> None:
    report = build_team_research_assignment_history_report(
        (),
        config=TeamResearchAssignmentHistoryConfig(min_report_count=2),
        generated_at=GENERATED_AT,
    )

    assert report.history_status == "blocked"
    assert report.reason_codes == ("insufficient_history",)
    assert report.report_count == 0
    assert report.required_report_count == 2
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.latest_assignment_status is None
    assert report.latest_assignment_count == 0
    assert report.latest_assigned_count == 0
    assert report.latest_watch_count == 0
    assert report.latest_blocked_count == 0
    assert report.assignment_count_delta == 0
    assert report.assigned_count_delta == 0
    assert report.watch_count_delta == 0
    assert report.blocked_count_delta == 0
    assert report.duplicate_latest_generated_at is False
    assert report.status_rows == (
        TeamResearchAssignmentHistoryStatusRow(
            assignment_status="ready",
            report_count=0,
        ),
        TeamResearchAssignmentHistoryStatusRow(
            assignment_status="watch",
            report_count=0,
        ),
        TeamResearchAssignmentHistoryStatusRow(
            assignment_status="blocked",
            report_count=0,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_fewer_than_min_report_count_is_blocked_but_includes_latest_counts() -> None:
    source_report = _assignment_report(
        generated_at=GENERATED_AT,
        assigned_count=2,
    )

    report = build_team_research_assignment_history_report(
        [source_report],
        config=TeamResearchAssignmentHistoryConfig(min_report_count=2),
        generated_at=GENERATED_AT + timedelta(minutes=5),
    )

    assert report.history_status == "blocked"
    assert report.reason_codes == ("insufficient_history",)
    assert report.report_count == 1
    assert report.latest_assignment_status == "ready"
    assert report.latest_assignment_count == 2
    assert report.latest_assigned_count == 2
    assert report.latest_watch_count == 0
    assert report.latest_blocked_count == 0


def test_duplicate_latest_generated_at_blocks_history() -> None:
    latest_generated_at = GENERATED_AT + timedelta(minutes=2)
    report = build_team_research_assignment_history_report(
        (
            _assignment_report(generated_at=GENERATED_AT, assigned_count=1),
            _assignment_report(generated_at=latest_generated_at, assigned_count=2),
            _assignment_report(
                generated_at=latest_generated_at,
                assigned_count=1,
                watch_count=1,
            ),
        ),
        config=TeamResearchAssignmentHistoryConfig(min_report_count=2),
        generated_at=latest_generated_at + timedelta(minutes=5),
    )

    assert report.history_status == "blocked"
    assert report.reason_codes == ("duplicate_latest_generated_at",)
    assert report.duplicate_latest_generated_at is True
    assert report.latest_report_generated_at == latest_generated_at


def test_enough_reports_with_latest_ready_status_yields_observed_summary() -> None:
    first_generated_at = GENERATED_AT
    middle_generated_at = GENERATED_AT + timedelta(minutes=1)
    latest_generated_at = GENERATED_AT + timedelta(minutes=2)
    reports = (
        _assignment_report(
            generated_at=middle_generated_at,
            assigned_count=1,
            watch_count=1,
        ),
        _assignment_report(
            generated_at=latest_generated_at,
            assigned_count=3,
        ),
        _assignment_report(
            generated_at=first_generated_at,
            assigned_count=1,
            blocked_count=1,
        ),
    )

    report = build_team_research_assignment_history_report(
        reports,
        config=TeamResearchAssignmentHistoryConfig(min_report_count=3),
        generated_at=latest_generated_at + timedelta(minutes=5),
    )

    assert report.history_status == "observed"
    assert report.reason_codes == ()
    assert report.report_count == 3
    assert report.required_report_count == 3
    assert report.first_report_generated_at == first_generated_at
    assert report.latest_report_generated_at == latest_generated_at
    assert report.status_rows == (
        TeamResearchAssignmentHistoryStatusRow(
            assignment_status="ready",
            report_count=1,
        ),
        TeamResearchAssignmentHistoryStatusRow(
            assignment_status="watch",
            report_count=1,
        ),
        TeamResearchAssignmentHistoryStatusRow(
            assignment_status="blocked",
            report_count=1,
        ),
    )
    assert report.latest_assignment_status == "ready"
    assert report.latest_assignment_count == 3
    assert report.latest_assigned_count == 3
    assert report.latest_watch_count == 0
    assert report.latest_blocked_count == 0
    assert report.assignment_count_delta == 1
    assert report.assigned_count_delta == 2
    assert report.watch_count_delta == 0
    assert report.blocked_count_delta == -1
    assert report.duplicate_latest_generated_at is False
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_history_rejects_wrong_inputs_and_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="TeamResearchAssignmentHistoryConfig"):
        build_team_research_assignment_history_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="TeamResearchAssignmentReport"):
        build_team_research_assignment_history_report(
            (object(),),
            config=TeamResearchAssignmentHistoryConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="paper_only"):
        TeamResearchAssignmentHistoryConfig(paper_only=False)


def _assignment_report(
    *,
    generated_at: datetime,
    assigned_count: int,
    watch_count: int = 0,
    blocked_count: int = 0,
) -> TeamResearchAssignmentReport:
    rows = tuple(
        [
            *_assignment_rows(
                generated_at=generated_at,
                start_rank=1,
                assignment_status="assigned",
                count=assigned_count,
            ),
            *_assignment_rows(
                generated_at=generated_at,
                start_rank=1 + assigned_count,
                assignment_status="watch",
                count=watch_count,
            ),
            *_assignment_rows(
                generated_at=generated_at,
                start_rank=1 + assigned_count + watch_count,
                assignment_status="blocked",
                count=blocked_count,
            ),
        ],
    )
    assignment_count = assigned_count + watch_count + blocked_count
    assignment_status = _report_status(
        assigned_count=assigned_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
    )
    return TeamResearchAssignmentReport(
        generated_at=generated_at,
        config_version="team-research-assignment-test-v0",
        source_queue_config_version="candidate-research-queue-test-v0",
        source_route_config_version="team-market-route-test-v0",
        source_memory_config_version="team-memory-readiness-test-v0",
        assignment_status=assignment_status,
        recommended_next_step={
            "ready": "assign_team_research_work",
            "watch": "review_team_research_assignments",
            "blocked": "block_team_research_assignment",
        }[assignment_status],
        assignment_count=assignment_count,
        assigned_count=assigned_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        team_summaries=(
            TeamResearchAssignmentTeamSummary(
                team_id="crypto_btc",
                assignment_count=assignment_count,
                assigned_count=assigned_count,
                watch_count=watch_count,
                blocked_count=blocked_count,
                memory_readiness_status="pass",
                memory_use_policy="allow",
            ),
        )
        if assignment_count
        else (),
        rows=rows,
        reason_codes=(_report_reason_code(assignment_status, assignment_count),),
    )


def _assignment_rows(
    *,
    generated_at: datetime,
    start_rank: int,
    assignment_status: str,
    count: int,
) -> tuple[TeamResearchAssignmentRow, ...]:
    return tuple(
        _assignment_row(
            generated_at=generated_at,
            research_rank=start_rank + offset,
            assignment_status=assignment_status,
        )
        for offset in range(count)
    )


def _assignment_row(
    *,
    generated_at: datetime,
    research_rank: int,
    assignment_status: str,
) -> TeamResearchAssignmentRow:
    market_slug = f"secret-market-{generated_at.minute}-{research_rank}"
    queue_research_status = {
        "assigned": "ready",
        "watch": "watch",
        "blocked": "blocked",
    }[assignment_status]
    return TeamResearchAssignmentRow(
        research_rank=research_rank,
        market_slug=market_slug,
        question=f"Will {market_slug} reveal a private question?",
        selected_side="yes",
        scoring_side="yes",
        team_id="crypto_btc",
        category_id="finance.crypto.btc",
        routing_confidence=Decimal("0.900000"),
        secondary_team_ids=(),
        queue_research_status=queue_research_status,
        queue_research_bucket="ready_bucket",
        queue_readiness_status="pass",
        memory_readiness_status="pass",
        memory_use_policy="allow",
        assignment_status=assignment_status,
        assignment_reason_codes=(
            {
                "assigned": "team_research_assignment_assigned",
                "watch": "source_queue_research_status_watch",
                "blocked": "source_queue_research_status_blocked",
            }[assignment_status],
        ),
        evidence_gap_codes=(),
        source_reason_codes=("candidate_research_ready",),
    )


def _report_status(
    *,
    assigned_count: int,
    watch_count: int,
    blocked_count: int,
) -> str:
    if blocked_count:
        return "blocked"
    if watch_count:
        return "watch"
    if assigned_count:
        return "ready"
    return "blocked"


def _report_reason_code(assignment_status: str, assignment_count: int) -> str:
    if assignment_count == 0:
        return "team_research_assignment_empty_queue"
    return {
        "ready": "team_research_assignment_ready",
        "watch": "team_research_assignment_watch",
        "blocked": "team_research_assignment_blocked",
    }[assignment_status]
