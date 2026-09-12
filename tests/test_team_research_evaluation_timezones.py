"""Repeated local hours must never alter evaluation time eligibility or selection."""
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, TeamResearchTask, TeamResearchResult
from polymarket_alpha_lab.team_research_intake import TeamResearchIntake, ResearchSourceReceipt, evidence_content_sha256
from polymarket_alpha_lab.team_research_market_pipeline import MarketTeamResearchRun
from polymarket_alpha_lab.team_research_evaluation import (
    ResearchEvaluationRecord as Record, ResearchEvaluationOutcome as Outcome,
    ResearchEvaluationReport as Report,
)


def record(record_id="r1", *, recorded_at):
    now = datetime(2026, 9, 12, tzinfo=UTC)
    source = ResearchEvidence("s", "crypto_eth", "c", "Synthetic source", "Synthetic text", "synthetic:source", now)
    task = TeamResearchTask(record_id, "crypto_eth", "c", "tz-market", "Synthetic?", "Synthetic rules", now, (source,))
    receipt = ResearchSourceReceipt("s", evidence_content_sha256(source), source.reference, now)
    intake = TeamResearchIntake(record_id, "crypto_eth", "c", "tz-market", now, now, "a" * 64,
        "prepared", "research_intake_prepared", task, (receipt,))
    result = TeamResearchResult(record_id, "crypto_eth", "c", "tz-market", now,
        "completed", "research_completed", Decimal("0.7"), Decimal("0.2"), "Synthetic.", ("s",))
    return Record(record_id, "synthetic-model", "synthetic-v1", recorded_at, MarketTeamResearchRun(intake, result))


def outcome(*, forecast_cutoff_at, resolved_at, recorded_at):
    return Outcome("c", "tz-market", forecast_cutoff_at, resolved_at, recorded_at,
                   True, "synthetic:confirmed", "b" * 64)


def reasons(report):
    return {row.record_id: row.reason_code for row in report.decisions}


def fold_time(hour, minute, fold=0):
    from zoneinfo import ZoneInfo
    return datetime(2026, 11, 1, hour, minute, tzinfo=ZoneInfo("America/New_York"), fold=fold)


def test_repeated_local_hour_contains_distinct_attempt_instants():
    early = record("early-fold", recorded_at=fold_time(1, 30, 0))
    late = record("late-fold", recorded_at=fold_time(1, 30, 1))
    actual = outcome(forecast_cutoff_at=fold_time(2, 0), resolved_at=fold_time(3, 0), recorded_at=fold_time(4, 0))
    report = Report((late, early), (actual,), fold_time(5, 0))
    assert reasons(report) == {"early-fold": "scored", "late-fold": "later_attempt"}


def test_dst_fold_cannot_make_post_cutoff_capture_score():
    item = record(recorded_at=fold_time(1, 15, 1))  # 06:15 UTC
    actual = outcome(forecast_cutoff_at=fold_time(1, 45, 0),  # 05:45 UTC
                     resolved_at=fold_time(2, 0), recorded_at=fold_time(3, 0))
    assert reasons(Report((item,), (actual,), fold_time(4, 0)))["r1"] == "not_pre_outcome"


def test_dst_fold_future_capture_not_visible_in_earlier_report():
    item = record(recorded_at=fold_time(1, 15, 1))
    report = Report((item,), (), fold_time(1, 50, 0))
    assert reasons(report)["r1"] == "not_yet_recorded"
    assert report.groups == ()


def test_dst_fold_outcome_chronology_uses_instants_not_wall_clock():
    actual = outcome(forecast_cutoff_at=fold_time(1, 45, 0),
        resolved_at=fold_time(1, 15, 1), recorded_at=fold_time(1, 20, 1))
    assert actual.forecast_cutoff_at.astimezone(UTC) < actual.resolved_at.astimezone(UTC)


def test_dst_fold_reversed_real_chronology_rejected():
    with pytest.raises(ValueError, match="chronological"):
        outcome(forecast_cutoff_at=fold_time(1, 15, 1), resolved_at=fold_time(1, 45, 0),
                recorded_at=fold_time(1, 50, 0))
