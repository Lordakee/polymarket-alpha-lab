from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest

import polymarket_alpha_lab.team_specialist_research_queue_learning_value_v2 as api
from polymarket_alpha_lab.team_specialist_research_queue_learning_value_v2 import (
    TeamSpecialistResearchQueueLearningValueConfigV2,
    TeamSpecialistResearchQueueLearningValueInputV2,
    TeamSpecialistResearchQueueLearningValueReportV2,
    build_team_specialist_research_queue_learning_value_v2,
    team_specialist_research_queue_learning_value_v2_payload,
)


NOW = datetime(2026, 1, 20, 12, tzinfo=UTC)


def _input(
    queue_item_id: str,
    *,
    lesson_age_days: int = 2,
    learning_signal_score: Decimal = Decimal("0.800000"),
    feedback_impact_score: Decimal = Decimal("0.900000"),
    evidence_gap_score: Decimal = Decimal("0.700000"),
    queue_priority_score: Decimal = Decimal("0.600000"),
) -> TeamSpecialistResearchQueueLearningValueInputV2:
    return TeamSpecialistResearchQueueLearningValueInputV2(
        team_id="team-alpha",
        specialist_id="specialist-research",
        queue_item_id=queue_item_id,
        observed_at=NOW - timedelta(hours=1),
        lesson_last_applied_at=NOW - timedelta(days=lesson_age_days),
        queue_age_seconds=Decimal("3600"),
        learning_signal_score=learning_signal_score,
        feedback_impact_score=feedback_impact_score,
        evidence_gap_score=evidence_gap_score,
        queue_priority_score=queue_priority_score,
        public_research_refs=(f"public:{queue_item_id}",),
    )


def _assert_no_decimal_or_float(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_or_float(item)
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_no_decimal_or_float(item)
        return
    assert not isinstance(value, (Decimal, float))


def test_research_queue_learning_value_scores_and_sorts_rows() -> None:
    report = build_team_specialist_research_queue_learning_value_v2(
        (
            _input(
                "queue-beta",
                lesson_age_days=28,
                learning_signal_score=Decimal("0.300000"),
                feedback_impact_score=Decimal("0.100000"),
                evidence_gap_score=Decimal("0.200000"),
                queue_priority_score=Decimal("0.300000"),
            ),
            _input("queue-alpha"),
        ),
        config=TeamSpecialistResearchQueueLearningValueConfigV2(),
        generated_at=NOW,
    )

    assert report.queue_item_count == Decimal("2")
    assert report.high_value_count == Decimal("1")
    assert report.stale_learning_count == Decimal("1")
    assert report.average_learning_value_score == Decimal("0.377500")
    assert report.status == "high_value"
    assert report.reason_codes == (
        "high_value_learning_opportunity",
        "stale_learning_penalty",
        "high_impact_feedback_boost",
    )
    assert tuple(row.queue_item_id for row in report.learning_value_rows) == (
        "queue-alpha",
        "queue-beta",
    )
    assert report.learning_value_rows[0].learning_value_score == Decimal("0.700000")
    assert report.learning_value_rows[0].row_status == "high_value"
    assert report.learning_value_rows[1].learning_value_score == Decimal("0.055000")
    assert report.learning_value_rows[1].row_status == "low_value"


def test_stale_learning_penalty_reduces_learning_value() -> None:
    fresh = build_team_specialist_research_queue_learning_value_v2(
        (_input("queue-fresh", lesson_age_days=2),),
        config=TeamSpecialistResearchQueueLearningValueConfigV2(),
        generated_at=NOW,
    ).learning_value_rows[0]
    stale = build_team_specialist_research_queue_learning_value_v2(
        (_input("queue-stale", lesson_age_days=28),),
        config=TeamSpecialistResearchQueueLearningValueConfigV2(),
        generated_at=NOW,
    ).learning_value_rows[0]

    assert fresh.stale_learning_penalty == Decimal("0.000000")
    assert stale.stale_learning_penalty == Decimal("1.000000")
    assert stale.learning_value_score == fresh.learning_value_score - Decimal("0.150000")
    assert "stale_learning_penalty" in stale.reason_codes


def test_high_impact_feedback_boost_increases_learning_value() -> None:
    config = TeamSpecialistResearchQueueLearningValueConfigV2()
    ordinary = build_team_specialist_research_queue_learning_value_v2(
        (_input("queue-ordinary", feedback_impact_score=Decimal("0.740000")),),
        config=config,
        generated_at=NOW,
    ).learning_value_rows[0]
    high_impact = build_team_specialist_research_queue_learning_value_v2(
        (_input("queue-impact", feedback_impact_score=Decimal("0.800000")),),
        config=config,
        generated_at=NOW,
    ).learning_value_rows[0]

    assert ordinary.high_impact_feedback_boost == Decimal("0.000000")
    assert high_impact.high_impact_feedback_boost == Decimal("0.800000")
    assert high_impact.learning_value_score == ordinary.learning_value_score + Decimal("0.160000")
    assert "high_impact_feedback_boost" in high_impact.reason_codes


def test_payload_serializes_decimal_values_as_strings() -> None:
    report = build_team_specialist_research_queue_learning_value_v2(
        (_input("queue-alpha"),),
        config=TeamSpecialistResearchQueueLearningValueConfigV2(),
        generated_at=NOW,
    )

    payload = team_specialist_research_queue_learning_value_v2_payload(report)

    assert payload["queue_item_count"] == "1"
    assert payload["average_learning_value_score"] == "0.700000"
    assert payload["learning_value_rows"][0]["learning_value_score"] == "0.700000"
    assert payload["learning_value_rows"][0]["queue_age_seconds"] == "3600.000000"
    assert isinstance(payload["derived_validation_digest"], str)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_decimal_or_float(payload)


def test_dataclasses_are_frozen() -> None:
    report = build_team_specialist_research_queue_learning_value_v2(
        (_input("queue-alpha"),),
        config=TeamSpecialistResearchQueueLearningValueConfigV2(),
        generated_at=NOW,
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.learning_value_rows[0].learning_value_score = Decimal("0.1")  # type: ignore[misc]


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        TeamSpecialistResearchQueueLearningValueConfigV2(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(_input("queue-alpha"), report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        TeamSpecialistResearchQueueLearningValueReportV2(
            generated_at=NOW,
            config_version="team-specialist-research-queue-learning-value-v2-phase-1",
            queue_item_count=Decimal("0"),
            high_value_count=Decimal("0"),
            watch_count=Decimal("0"),
            low_value_count=Decimal("0"),
            stale_learning_count=Decimal("0"),
            average_learning_value_score=Decimal("0.000000"),
            status="empty",
            reason_codes=("empty_research_queue",),
            learning_value_rows=(),
            derived_validation_digest="0" * 64,
            readonly=False,
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_team_specialist_research_queue_learning_value_v2(
        (_input("queue-alpha"),),
        config=TeamSpecialistResearchQueueLearningValueConfigV2(),
        generated_at=NOW,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report.learning_value_rows[0], derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


@pytest.mark.parametrize(
    "term",
    (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ),
)
def test_unsafe_public_keys_and_values_are_rejected(term: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        team_specialist_research_queue_learning_value_v2_payload({term: "safe"})

    with pytest.raises(ValueError, match="unsafe public"):
        team_specialist_research_queue_learning_value_v2_payload({"safe": f"alpha-{term}"})

    with pytest.raises(ValueError, match="unsafe public"):
        TeamSpecialistResearchQueueLearningValueInputV2(
            team_id=f"team-{term}",
            specialist_id="specialist-research",
            queue_item_id="queue-alpha",
            observed_at=NOW,
            lesson_last_applied_at=NOW,
            queue_age_seconds=Decimal("0"),
            learning_signal_score=Decimal("0.500000"),
            feedback_impact_score=Decimal("0.500000"),
            evidence_gap_score=Decimal("0.500000"),
            queue_priority_score=Decimal("0.500000"),
            public_research_refs=("public:queue-alpha",),
        )


def test_public_api_exposes_no_unsafe_surface_names() -> None:
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    names: set[str] = set(api.__all__)
    for name in api.__all__:
        value = getattr(api, name)
        if inspect.isclass(value) and is_dataclass(value):
            names.update(field.name for field in fields(value))

    assert not {
        name
        for name in names
        if any(term in name.lower() for term in unsafe_terms)
    }
