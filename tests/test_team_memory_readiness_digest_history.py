from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from polymarket_alpha_lab.team_memory_readiness_digest import (
    TeamMemoryReadinessDigestReasonCodeCount,
    TeamMemoryReadinessDigestReport,
    TeamMemoryReadinessDigestSourceStatus,
)
from polymarket_alpha_lab.team_memory_readiness_digest_history import (
    TeamMemoryReadinessDigestHistoryConfig,
    TeamMemoryReadinessDigestHistoryStatusRow,
    build_team_memory_readiness_digest_history_report,
)
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def test_empty_history_is_blocked_with_zeroed_report_only_summary() -> None:
    report = build_team_memory_readiness_digest_history_report(
        (),
        config=TeamMemoryReadinessDigestHistoryConfig(min_report_count=2),
        generated_at=GENERATED_AT,
    )

    assert report.history_status == "blocked"
    assert report.reason_codes == ("insufficient_history",)
    assert report.report_count == 0
    assert report.required_report_count == 2
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.latest_digest_status is None
    assert report.latest_team_count == 0
    assert report.latest_pass_count == 0
    assert report.latest_watch_count == 0
    assert report.latest_blocked_count == 0
    assert report.team_count_delta == 0
    assert report.pass_count_delta == 0
    assert report.watch_count_delta == 0
    assert report.blocked_count_delta == 0
    assert report.duplicate_latest_generated_at is False
    assert report.status_rows == (
        TeamMemoryReadinessDigestHistoryStatusRow(
            digest_status="pass",
            report_count=0,
        ),
        TeamMemoryReadinessDigestHistoryStatusRow(
            digest_status="watch",
            report_count=0,
        ),
        TeamMemoryReadinessDigestHistoryStatusRow(
            digest_status="blocked",
            report_count=0,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_fewer_than_min_report_count_is_blocked_but_includes_latest_counts() -> None:
    source_report = _digest_report(
        generated_at=GENERATED_AT,
        pass_count=2,
    )

    report = build_team_memory_readiness_digest_history_report(
        [source_report],
        config=TeamMemoryReadinessDigestHistoryConfig(min_report_count=2),
        generated_at=GENERATED_AT + timedelta(minutes=5),
    )

    assert report.history_status == "blocked"
    assert report.reason_codes == ("insufficient_history",)
    assert report.report_count == 1
    assert report.latest_digest_status == "pass"
    assert report.latest_team_count == 2
    assert report.latest_pass_count == 2
    assert report.latest_watch_count == 0
    assert report.latest_blocked_count == 0


def test_duplicate_latest_generated_at_blocks_history() -> None:
    latest_generated_at = GENERATED_AT + timedelta(minutes=2)
    report = build_team_memory_readiness_digest_history_report(
        (
            _digest_report(generated_at=GENERATED_AT, pass_count=1),
            _digest_report(generated_at=latest_generated_at, pass_count=2),
            _digest_report(
                generated_at=latest_generated_at,
                pass_count=1,
                watch_count=1,
            ),
        ),
        config=TeamMemoryReadinessDigestHistoryConfig(min_report_count=2),
        generated_at=latest_generated_at + timedelta(minutes=5),
    )

    assert report.history_status == "blocked"
    assert report.reason_codes == ("duplicate_latest_generated_at",)
    assert report.duplicate_latest_generated_at is True
    assert report.latest_report_generated_at == latest_generated_at
    assert report.latest_pass_count == 2
    assert report.latest_watch_count == 0

    with pytest.raises(ValueError, match="duplicate_latest_generated_at reason"):
        replace(report, duplicate_latest_generated_at=False)


def test_enough_reports_yield_observed_summary_with_status_rows_and_deltas() -> None:
    first_generated_at = GENERATED_AT
    middle_generated_at = GENERATED_AT + timedelta(minutes=1)
    latest_generated_at = GENERATED_AT + timedelta(minutes=2)
    reports = (
        _digest_report(
            generated_at=middle_generated_at,
            pass_count=1,
            watch_count=1,
        ),
        _digest_report(
            generated_at=latest_generated_at,
            pass_count=3,
        ),
        _digest_report(
            generated_at=first_generated_at,
            pass_count=1,
            blocked_count=1,
        ),
    )

    report = build_team_memory_readiness_digest_history_report(
        reports,
        config=TeamMemoryReadinessDigestHistoryConfig(min_report_count=3),
        generated_at=latest_generated_at + timedelta(minutes=5),
    )

    assert report.history_status == "observed"
    assert report.reason_codes == ()
    assert report.report_count == 3
    assert report.required_report_count == 3
    assert report.first_report_generated_at == first_generated_at
    assert report.latest_report_generated_at == latest_generated_at
    assert report.status_rows == (
        TeamMemoryReadinessDigestHistoryStatusRow(
            digest_status="pass",
            report_count=1,
        ),
        TeamMemoryReadinessDigestHistoryStatusRow(
            digest_status="watch",
            report_count=1,
        ),
        TeamMemoryReadinessDigestHistoryStatusRow(
            digest_status="blocked",
            report_count=1,
        ),
    )
    assert report.latest_digest_status == "pass"
    assert report.latest_team_count == 3
    assert report.latest_pass_count == 3
    assert report.latest_watch_count == 0
    assert report.latest_blocked_count == 0
    assert report.team_count_delta == 1
    assert report.pass_count_delta == 2
    assert report.watch_count_delta == 0
    assert report.blocked_count_delta == -1
    assert report.duplicate_latest_generated_at is False
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_history_rejects_wrong_inputs_and_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="TeamMemoryReadinessDigestHistoryConfig"):
        build_team_memory_readiness_digest_history_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="TeamMemoryReadinessDigestReport"):
        build_team_memory_readiness_digest_history_report(
            (object(),),
            config=TeamMemoryReadinessDigestHistoryConfig(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="paper_only"):
        TeamMemoryReadinessDigestHistoryConfig(paper_only=False)
    with pytest.raises(ValueError, match="not a bool"):
        TeamMemoryReadinessDigestHistoryConfig(min_report_count=True)


def _digest_report(
    *,
    generated_at: datetime,
    pass_count: int = 0,
    watch_count: int = 0,
    blocked_count: int = 0,
) -> TeamMemoryReadinessDigestReport:
    team_count = pass_count + watch_count + blocked_count
    digest_status = _digest_status(
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
    )
    source_statuses = tuple(
        [
            *_source_statuses("pass", pass_count, start_index=0),
            *_source_statuses("watch", watch_count, start_index=pass_count),
            *_source_statuses(
                "blocked",
                blocked_count,
                start_index=pass_count + watch_count,
            ),
        ],
    )
    return TeamMemoryReadinessDigestReport(
        generated_at=generated_at,
        config_version="team-memory-readiness-digest-test-v0",
        digest_status=digest_status,
        recommended_next_step={
            "pass": "allow_team_memory_readiness_use",
            "watch": "throttle_team_memory_readiness_use",
            "blocked": "block_team_memory_readiness_use",
        }[digest_status],
        team_count=team_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        source_statuses=source_statuses,
        source_config_versions=tuple(
            sorted(
                (
                    status.team_id,
                    status.source_config_version,
                )
                for status in source_statuses
            ),
        ),
        reason_code_counts=(
            TeamMemoryReadinessDigestReasonCodeCount(
                reason_code=_reason_code(digest_status, team_count),
                count=1,
            ),
        ),
        reason_codes=(_reason_code(digest_status, team_count),),
    )


def _source_statuses(
    gate_status: str,
    count: int,
    *,
    start_index: int,
) -> tuple[TeamMemoryReadinessDigestSourceStatus, ...]:
    return tuple(
        TeamMemoryReadinessDigestSourceStatus(
            team_id=TEAM_IDS[start_index + index],
            gate_status=gate_status,
            recommended_next_step={
                "pass": "allow_team_diagnostics_snapshot_history_memory_use",
                "watch": "throttle_team_diagnostics_snapshot_history_memory_use",
                "blocked": "block_team_diagnostics_snapshot_history_memory_use",
            }[gate_status],
            source_config_version="team-diagnostics-snapshot-history-gate-test-v0",
            latest_snapshot_age_seconds=60,
            source_snapshot_count=3,
            source_required_snapshot_count=3,
            source_status="ready",
        )
        for index in range(count)
    )


def _digest_status(
    *,
    pass_count: int,
    watch_count: int,
    blocked_count: int,
) -> str:
    if blocked_count:
        return "blocked"
    if watch_count:
        return "watch"
    if pass_count:
        return "pass"
    return "blocked"


def _reason_code(digest_status: str, team_count: int) -> str:
    if team_count == 0:
        return "team_memory_readiness_digest_empty_sources"
    return {
        "pass": "team_memory_readiness_digest_passed",
        "watch": "team_memory_readiness_digest_watch_sources_present",
        "blocked": "team_memory_readiness_digest_blocked_sources_present",
    }[digest_status]
