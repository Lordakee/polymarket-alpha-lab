from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, ROUND_UP, getcontext, setcontext

import pytest

from polymarket_alpha_lab.team_evidence_aggregation_temporal import (
    assess_team_evidence_temporal,
)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceRequirement,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
    TeamEvidenceTemporalAssessment,
)


FRESHNESS_ANCHOR_AT = datetime(
    2026, 7, 13, 10, 0, 0, 125000, tzinfo=UTC
)
CAPTURED_AT = datetime(2026, 7, 13, 10, 4, 30, 375000, tzinfo=UTC)
RECORDED_AT = datetime(2026, 7, 13, 10, 5, 0, 125000, tzinfo=UTC)
ASSESSED_AT = datetime(2026, 7, 13, 10, 6, 0, 125000, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 13, 11, 0, 0, 625000, tzinfo=UTC)
HARD_FLAGS = ("paper_only", "report_only", "readonly")


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(character: str) -> str:
    return character * 64


def config(**changes: object) -> TeamEvidenceAggregationConfig:
    values: dict[str, object] = {
        "config_version": "agg-test-v1",
        "max_evidence_age_seconds": d("7200.000000"),
        "max_capture_lag_seconds": d("300.000000"),
        "independence_group_weight_cap": d("0.730000"),
        "correlation_group_weight_cap": d("0.610000"),
        "max_requirement_assignments_per_evidence": 3,
        "contradiction_no_probability_max": d("0.210000"),
        "contradiction_yes_probability_min": d("0.790000"),
        "contradiction_watch_score": d("0.310000"),
        "contradiction_block_score": d("0.670000"),
        "publish_probability_floor": d("0.110000"),
        "publish_probability_ceiling": d("0.890000"),
        "maximum_records": 8,
        "maximum_requirements": 4,
        "maximum_requirement_memberships": 16,
        "maximum_witness_edges": 12,
        "requirements": (
            TeamEvidenceRequirement(
                requirement_id="macro.release",
                minimum_witness_count=1,
                minimum_effective_weight=d("0.120000"),
                unmet_status="blocked",
            ),
        ),
    }
    values.update(changes)
    return TeamEvidenceAggregationConfig(**values)


def record(
    *,
    freshness_anchor_at: datetime = FRESHNESS_ANCHOR_AT,
    captured_at: datetime = CAPTURED_AT,
    recorded_at: datetime = RECORDED_AT,
    assessed_at: datetime = ASSESSED_AT,
) -> TeamEvidenceAggregationRecord:
    lineage = TeamEvidenceSourceLineage(
        source_lineage_id="lineage.alpha",
        source_lineage_digest=digest("a"),
    )
    capture = TeamEvidenceCapture(
        capture_id="capture.alpha.1",
        capture_digest=digest("b"),
        source_lineage_id=lineage.source_lineage_id,
        source_lineage_digest=lineage.source_lineage_digest,
        content_digest=digest("c"),
        captured_at=captured_at,
    )
    evidence_revision = TeamEvidenceRevision(
        evidence_revision_id="evidence.alpha.1",
        evidence_revision_digest=digest("d"),
        previous_evidence_revision_id=None,
        previous_evidence_revision_digest=None,
        source_lineage_id=lineage.source_lineage_id,
        source_lineage_digest=lineage.source_lineage_digest,
        content_digest=capture.content_digest,
        requirement_ids=("macro.release",),
        freshness_anchor_at=freshness_anchor_at,
        recorded_at=recorded_at,
    )
    assessment_revision = TeamEvidenceAssessmentRevision(
        assessment_revision_id="assessment.alpha.1",
        assessment_revision_digest=digest("e"),
        previous_assessment_revision_id=None,
        previous_assessment_revision_digest=None,
        evidence_revision_id=evidence_revision.evidence_revision_id,
        evidence_revision_digest=evidence_revision.evidence_revision_digest,
        assessed_at=assessed_at,
        probability_yes=d("0.640000"),
        requested_weight=d("0.400000"),
        rationale_digest=digest("f"),
        independence_key="desk.alpha",
        correlation_key="macro.shared",
    )
    return TeamEvidenceAggregationRecord(
        source_lineage=lineage,
        capture=capture,
        evidence_revision=evidence_revision,
        assessment_revision=assessment_revision,
    )


def assess(
    value: TeamEvidenceAggregationRecord,
    *,
    evaluated_at: datetime = EVALUATED_AT,
    cfg: TeamEvidenceAggregationConfig | None = None,
) -> TeamEvidenceTemporalAssessment:
    return assess_team_evidence_temporal(
        value,
        evaluated_at=evaluated_at,
        config=config() if cfg is None else cfg,
    )


def bypass(value: object, **changes: object) -> object:
    copied = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(
            copied,
            field.name,
            changes.get(field.name, getattr(value, field.name)),
        )
    return copied


def codec_ready_values(value: TeamEvidenceTemporalAssessment) -> tuple[object, ...]:
    return (
        value.capture_id,
        value.evidence_revision_id,
        value.assessment_revision_id,
        format(value.evidence_age_seconds, ".6f"),
        format(value.capture_lag_seconds, ".6f"),
        value.effective_at_evaluation,
        value.captured_at_evaluation,
        value.evidence_revision_available_at_evaluation,
        value.assessment_revision_available_at_evaluation,
        value.fresh,
        value.timely,
        value.paper_only,
        value.report_only,
        value.readonly,
    )


def test_temporal_assessment_uses_exact_anchor_age_and_capture_lag_formulas() -> None:
    result = assess(record())

    assert result.capture_id == "capture.alpha.1"
    assert result.evidence_revision_id == "evidence.alpha.1"
    assert result.assessment_revision_id == "assessment.alpha.1"
    assert result.evidence_age_seconds == d("3600.500000")
    assert result.capture_lag_seconds == d("270.250000")
    assert result.effective_at_evaluation is True
    assert result.captured_at_evaluation is True
    assert result.evidence_revision_available_at_evaluation is True
    assert result.assessment_revision_available_at_evaluation is True
    assert result.fresh is True
    assert result.timely is True
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert not hasattr(result, "eligible")


def test_temporal_age_and_lag_limits_are_inclusive() -> None:
    limits = config(
        max_evidence_age_seconds=d("3600.500000"),
        max_capture_lag_seconds=d("270.250000"),
    )
    at_limits = assess(record(), cfg=limits)
    age_over = assess(
        record(),
        evaluated_at=EVALUATED_AT + timedelta(microseconds=1),
        cfg=limits,
    )
    lag_over = assess(
        record(captured_at=CAPTURED_AT + timedelta(microseconds=1)),
        cfg=limits,
    )

    assert at_limits.fresh is True
    assert at_limits.timely is True
    assert age_over.evidence_age_seconds == d("3600.500001")
    assert age_over.fresh is False
    assert age_over.timely is True
    assert lag_over.capture_lag_seconds == d("270.250001")
    assert lag_over.fresh is True
    assert lag_over.timely is False


def test_future_anchor_retains_negative_age_and_is_not_fresh() -> None:
    result = assess(
        record(
            freshness_anchor_at=EVALUATED_AT + timedelta(microseconds=1),
        )
    )

    assert result.evidence_age_seconds == d("-0.000001")
    assert result.evidence_age_seconds.is_signed() is True
    assert result.effective_at_evaluation is False
    assert result.fresh is False


def test_future_capture_is_independently_unavailable() -> None:
    result = assess(
        record(captured_at=EVALUATED_AT + timedelta(microseconds=1)),
        cfg=config(max_capture_lag_seconds=d("7200.000000")),
    )

    assert result.capture_lag_seconds == d("3600.500001")
    assert result.captured_at_evaluation is False
    assert result.effective_at_evaluation is True
    assert result.fresh is True
    assert result.timely is True
    assert result.evidence_revision_available_at_evaluation is True
    assert result.assessment_revision_available_at_evaluation is True


def test_capture_before_anchor_and_excessive_lag_are_not_timely() -> None:
    limits = config(max_capture_lag_seconds=d("300.000000"))
    before = assess(
        record(
            captured_at=FRESHNESS_ANCHOR_AT - timedelta(microseconds=1),
        ),
        cfg=limits,
    )
    excessive = assess(
        record(
            captured_at=FRESHNESS_ANCHOR_AT
            + timedelta(seconds=300, microseconds=1),
        ),
        cfg=limits,
    )

    assert before.capture_lag_seconds == d("-0.000001")
    assert before.timely is False
    assert excessive.capture_lag_seconds == d("300.000001")
    assert excessive.timely is False
    assert before.evidence_age_seconds == d("3600.500000")
    assert excessive.evidence_age_seconds == d("3600.500000")
    assert before.fresh is True
    assert excessive.fresh is True


def test_stale_evidence_uses_anchor_not_capture_or_recording_time() -> None:
    stale_config = config(
        max_evidence_age_seconds=d("3600.499999"),
        max_capture_lag_seconds=d("7200.000000"),
    )
    original = assess(record(), cfg=stale_config)
    recent_recapture = assess(
        record(
            captured_at=EVALUATED_AT,
            recorded_at=EVALUATED_AT,
            assessed_at=EVALUATED_AT,
        ),
        cfg=stale_config,
    )

    assert original.evidence_age_seconds == d("3600.500000")
    assert recent_recapture.evidence_age_seconds == original.evidence_age_seconds
    assert original.fresh is False
    assert recent_recapture.fresh is False
    assert recent_recapture.captured_at_evaluation is True
    assert recent_recapture.evidence_revision_available_at_evaluation is True
    assert recent_recapture.assessment_revision_available_at_evaluation is True


def test_evidence_and_assessment_revision_availability_are_independent() -> None:
    equality = record(
        captured_at=EVALUATED_AT,
        recorded_at=EVALUATED_AT,
        assessed_at=EVALUATED_AT,
    )
    at_equality = assess(
        equality,
        cfg=config(max_capture_lag_seconds=d("7200.000000")),
    )
    evidence_future = assess(
        record(
            captured_at=EVALUATED_AT,
            recorded_at=EVALUATED_AT + timedelta(microseconds=1),
            assessed_at=EVALUATED_AT,
        ),
        cfg=config(max_capture_lag_seconds=d("7200.000000")),
    )
    assessment_future = assess(
        record(
            captured_at=EVALUATED_AT,
            recorded_at=EVALUATED_AT,
            assessed_at=EVALUATED_AT + timedelta(microseconds=1),
        ),
        cfg=config(max_capture_lag_seconds=d("7200.000000")),
    )

    assert at_equality.captured_at_evaluation is True
    assert at_equality.evidence_revision_available_at_evaluation is True
    assert at_equality.assessment_revision_available_at_evaluation is True
    assert evidence_future.captured_at_evaluation is True
    assert evidence_future.evidence_revision_available_at_evaluation is False
    assert evidence_future.assessment_revision_available_at_evaluation is True
    assert assessment_future.captured_at_evaluation is True
    assert assessment_future.evidence_revision_available_at_evaluation is True
    assert assessment_future.assessment_revision_available_at_evaluation is False


def test_timezone_offsets_are_equivalent_and_microseconds_are_preserved() -> None:
    offset = timezone(timedelta(hours=5, minutes=30))
    utc_result = assess(record())
    offset_result = assess(
        record(
            freshness_anchor_at=FRESHNESS_ANCHOR_AT.astimezone(offset),
            captured_at=CAPTURED_AT.astimezone(offset),
            recorded_at=RECORDED_AT.astimezone(offset),
            assessed_at=ASSESSED_AT.astimezone(offset),
        ),
        evaluated_at=EVALUATED_AT.astimezone(offset),
    )

    assert offset_result == utc_result
    assert offset_result.evidence_age_seconds == d("3600.500000")
    assert offset_result.capture_lag_seconds == d("270.250000")
    assert offset_result.evidence_age_seconds.as_tuple().exponent == -6
    assert offset_result.capture_lag_seconds.as_tuple().exponent == -6


def test_temporal_assessment_rejects_wrong_exact_types_naive_time_and_false_flags() -> None:
    value = record()
    cfg = config()

    with pytest.raises(ValueError, match="record"):
        assess_team_evidence_temporal(
            cfg, evaluated_at=EVALUATED_AT, config=cfg  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="config"):
        assess_team_evidence_temporal(
            value, evaluated_at=EVALUATED_AT, config=value  # type: ignore[arg-type]
        )

    class DatetimeSubclass(datetime):
        pass

    invalid_evaluated_times = (
        datetime(2026, 7, 13, 11, 0, 0, 625000),
        DatetimeSubclass(2026, 7, 13, 11, 0, 0, 625000, tzinfo=UTC),
    )
    for invalid in invalid_evaluated_times:
        with pytest.raises(ValueError, match="evaluated_at"):
            assess(value, evaluated_at=invalid)

    layers = (
        ("record", None),
        ("record.source_lineage", "source_lineage"),
        ("record.capture", "capture"),
        ("record.evidence_revision", "evidence_revision"),
        ("record.assessment_revision", "assessment_revision"),
    )
    for path, attribute in layers:
        for flag in HARD_FLAGS:
            if attribute is None:
                invalid_record = bypass(value, **{flag: False})
            else:
                nested = bypass(getattr(value, attribute), **{flag: False})
                invalid_record = bypass(value, **{attribute: nested})
            with pytest.raises(ValueError, match=rf"{path}\.{flag}"):
                assess(invalid_record)  # type: ignore[arg-type]

    for flag in HARD_FLAGS:
        invalid_config = bypass(cfg, **{flag: False})
        with pytest.raises(ValueError, match=rf"config\.{flag}"):
            assess(value, cfg=invalid_config)  # type: ignore[arg-type]


def test_temporal_assessment_is_invariant_to_hostile_ambient_decimal_context() -> None:
    baseline = assess(record())
    baseline_values = codec_ready_values(baseline)
    saved = getcontext().copy()
    try:
        setcontext(Context(prec=2, rounding=ROUND_UP))
        hostile_result = assess(record())
        hostile_values = codec_ready_values(hostile_result)
        assert type(hostile_result) is TeamEvidenceTemporalAssessment
        assert hostile_result == baseline
        assert hostile_values == baseline_values
    finally:
        setcontext(saved)

    assert getcontext() == saved
