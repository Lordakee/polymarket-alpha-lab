from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import (
    Context,
    Decimal,
    DecimalException,
    ROUND_HALF_EVEN,
    localcontext,
)
from typing import Final

from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAssessmentRevision,
    TeamEvidenceCapture,
    TeamEvidenceRevision,
    TeamEvidenceSourceLineage,
    TeamEvidenceTemporalAssessment,
)


__all__ = ("assess_team_evidence_temporal",)


_HARD_FLAGS: Final = ("paper_only", "report_only", "readonly")
_ZERO: Final = Decimal("0.000000")


def _require_exact_type(
    path: str,
    value: object,
    expected: type[object],
) -> None:
    if type(value) is not expected:
        raise ValueError(f"{path} must be exactly {expected.__name__}")


def _require_hard_flags(path: str, value: object) -> None:
    for flag in _HARD_FLAGS:
        if getattr(value, flag, None) is not True:
            raise ValueError(f"{path}.{flag} must be exact True")


def _utc_datetime(path: str, value: object) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(f"{path} must be an exact aware datetime")
    return value.astimezone(UTC)


def _timedelta_seconds(path: str, delta: timedelta) -> Decimal:
    try:
        with localcontext(Context(prec=64, rounding=ROUND_HALF_EVEN)):
            seconds = (
                Decimal(delta.days) * Decimal(86400)
                + Decimal(delta.seconds)
                + Decimal(delta.microseconds) / Decimal(1000000)
            )
            normalized = seconds.quantize(Decimal("0.000001"))
    except DecimalException as error:
        raise ValueError(f"{path} must normalize to fixed-six Decimal") from error
    return _ZERO if normalized == _ZERO else normalized


def assess_team_evidence_temporal(
    record: TeamEvidenceAggregationRecord,
    *,
    evaluated_at: datetime,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceTemporalAssessment:
    _require_exact_type("record", record, TeamEvidenceAggregationRecord)
    record_layers = (
        ("record", record, TeamEvidenceAggregationRecord),
        (
            "record.source_lineage",
            record.source_lineage,
            TeamEvidenceSourceLineage,
        ),
        ("record.capture", record.capture, TeamEvidenceCapture),
        (
            "record.evidence_revision",
            record.evidence_revision,
            TeamEvidenceRevision,
        ),
        (
            "record.assessment_revision",
            record.assessment_revision,
            TeamEvidenceAssessmentRevision,
        ),
    )
    for path, layer, expected in record_layers:
        _require_exact_type(path, layer, expected)
        _require_hard_flags(path, layer)

    _require_exact_type("config", config, TeamEvidenceAggregationConfig)
    _require_hard_flags("config", config)
    normalized_evaluated_at = _utc_datetime("evaluated_at", evaluated_at)
    freshness_anchor_at = _utc_datetime(
        "record.evidence_revision.freshness_anchor_at",
        record.evidence_revision.freshness_anchor_at,
    )
    captured_at = _utc_datetime(
        "record.capture.captured_at",
        record.capture.captured_at,
    )
    recorded_at = _utc_datetime(
        "record.evidence_revision.recorded_at",
        record.evidence_revision.recorded_at,
    )
    assessed_at = _utc_datetime(
        "record.assessment_revision.assessed_at",
        record.assessment_revision.assessed_at,
    )

    evidence_age_seconds = _timedelta_seconds(
        "evidence_age_seconds",
        normalized_evaluated_at - freshness_anchor_at,
    )
    capture_lag_seconds = _timedelta_seconds(
        "capture_lag_seconds",
        captured_at - freshness_anchor_at,
    )
    effective_at_evaluation = freshness_anchor_at <= normalized_evaluated_at
    captured_at_evaluation = captured_at <= normalized_evaluated_at
    evidence_revision_available_at_evaluation = (
        recorded_at <= normalized_evaluated_at
    )
    assessment_revision_available_at_evaluation = (
        assessed_at <= normalized_evaluated_at
    )
    fresh = (
        effective_at_evaluation
        and evidence_age_seconds <= config.max_evidence_age_seconds
    )
    timely = (
        capture_lag_seconds >= _ZERO
        and capture_lag_seconds <= config.max_capture_lag_seconds
    )

    return TeamEvidenceTemporalAssessment(
        capture_id=record.capture.capture_id,
        evidence_revision_id=record.evidence_revision.evidence_revision_id,
        assessment_revision_id=(
            record.assessment_revision.assessment_revision_id
        ),
        evidence_age_seconds=evidence_age_seconds,
        capture_lag_seconds=capture_lag_seconds,
        effective_at_evaluation=effective_at_evaluation,
        captured_at_evaluation=captured_at_evaluation,
        evidence_revision_available_at_evaluation=(
            evidence_revision_available_at_evaluation
        ),
        assessment_revision_available_at_evaluation=(
            assessment_revision_available_at_evaluation
        ),
        fresh=fresh,
        timely=timely,
    )
