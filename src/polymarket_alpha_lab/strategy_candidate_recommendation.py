"""Paper-only strategy candidate recommendation reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.candidate_assessment import (
    PaperCandidateAssessmentReport,
    PaperCandidateAssessmentRow,
)
from polymarket_alpha_lab.strategy_readiness_state import (
    PaperStrategyReadinessStateReport,
)


__all__ = (
    "PaperStrategyCandidateRecommendationConfig",
    "PaperStrategyCandidateRecommendationRow",
    "PaperStrategyCandidateRecommendationReport",
    "build_paper_strategy_candidate_recommendation_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")

RECOMMENDATION_ACTIONS = ("recommend", "watch", "reject")
ACTION_RANK = {"recommend": 0, "watch": 1, "reject": 2}
ASSESSMENT_STATUSES = ("ready", "watch", "blocked")
READINESS_STATUSES = ("blocked", "watch", "pass")
SIDES = ("yes", "no", "none")


@dataclass(frozen=True)
class PaperStrategyCandidateRecommendationConfig:
    config_version: str
    min_recommendation_score: Decimal = Decimal("0.010000")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_decimal(
            "min_recommendation_score",
            self.min_recommendation_score,
        )
        if self.min_recommendation_score > ONE:
            raise ValueError("min_recommendation_score must be at most 1")


@dataclass(frozen=True)
class PaperStrategyCandidateRecommendationRow:
    market_slug: str
    question: str
    action: str
    assessment_status: str
    readiness_status: str
    selected_side: str
    scoring_side: str
    recommendation_score: Decimal
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("question", self.question)
        if type(self.action) is not str or self.action not in RECOMMENDATION_ACTIONS:
            raise ValueError("action must be recommend, watch, or reject")
        if (
            type(self.assessment_status) is not str
            or self.assessment_status not in ASSESSMENT_STATUSES
        ):
            raise ValueError("assessment_status must be a known assessment status")
        if (
            type(self.readiness_status) is not str
            or self.readiness_status not in READINESS_STATUSES
        ):
            raise ValueError("readiness_status must be a known readiness status")
        if type(self.selected_side) is not str or self.selected_side not in SIDES:
            raise ValueError("selected_side must be yes, no, or none")
        if type(self.scoring_side) is not str or self.scoring_side not in SIDES:
            raise ValueError("scoring_side must be yes, no, or none")
        if self.action == "recommend" and self.selected_side == "none":
            raise ValueError("recommended rows must have a selected side")
        _require_nonnegative_decimal("recommendation_score", self.recommendation_score)
        if self.recommendation_score > ONE:
            raise ValueError("recommendation_score must be at most 1")
        if self.recommendation_score != _quantize_score(self.recommendation_score):
            raise ValueError("recommendation_score must use 0.000001 precision")
        _validate_row_action_semantics(self)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )


@dataclass(frozen=True)
class PaperStrategyCandidateRecommendationReport:
    generated_at: datetime
    config_version: str
    readiness_overall_status: str
    candidate_count: int
    recommend_count: int
    watch_count: int
    reject_count: int
    recommendation_rows: tuple[PaperStrategyCandidateRecommendationRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            type(self.readiness_overall_status) is not str
            or self.readiness_overall_status not in READINESS_STATUSES
        ):
            raise ValueError("readiness_overall_status must be a known readiness status")
        for field_name in (
            "candidate_count",
            "recommend_count",
            "watch_count",
            "reject_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "recommendation_rows",
            _normalize_recommendation_rows(self.recommendation_rows),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_strategy_candidate_recommendation_report(
    assessment_report: PaperCandidateAssessmentReport,
    readiness_report: PaperStrategyReadinessStateReport,
    *,
    config: PaperStrategyCandidateRecommendationConfig,
    generated_at: datetime,
) -> PaperStrategyCandidateRecommendationReport:
    """Rank paper assessment candidates against the readonly strategy readiness gate."""

    _validate_assessment_report(assessment_report)
    _validate_readiness_report(readiness_report)
    if type(config) is not PaperStrategyCandidateRecommendationConfig:
        raise ValueError(
            "config must be a PaperStrategyCandidateRecommendationConfig",
        )
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    rows = tuple(
        _recommendation_row_from_assessment(
            assessment_row=row,
            readiness_status=readiness_report.overall_status,
            config=config,
        )
        for row in assessment_report.assessment_rows
    )
    ordered_rows = _order_rows(rows)

    return PaperStrategyCandidateRecommendationReport(
        generated_at=generated_at,
        config_version=config.config_version,
        readiness_overall_status=readiness_report.overall_status,
        candidate_count=assessment_report.candidate_count,
        recommend_count=_action_count(ordered_rows, "recommend"),
        watch_count=_action_count(ordered_rows, "watch"),
        reject_count=_action_count(ordered_rows, "reject"),
        recommendation_rows=ordered_rows,
    )


def _recommendation_row_from_assessment(
    *,
    assessment_row: PaperCandidateAssessmentRow,
    readiness_status: str,
    config: PaperStrategyCandidateRecommendationConfig,
) -> PaperStrategyCandidateRecommendationRow:
    recommendation_score = _quantize_score(assessment_row.readiness_score)
    action = _recommendation_action(
        assessment_status=assessment_row.assessment_status,
        readiness_status=readiness_status,
        recommendation_score=recommendation_score,
        config=config,
    )
    reason_codes = _recommendation_reason_codes(
        assessment_row=assessment_row,
        readiness_status=readiness_status,
        recommendation_score=recommendation_score,
        config=config,
    )

    return PaperStrategyCandidateRecommendationRow(
        market_slug=assessment_row.market_slug,
        question=assessment_row.question,
        action=action,
        assessment_status=assessment_row.assessment_status,
        readiness_status=readiness_status,
        selected_side=assessment_row.selected_side,
        scoring_side=assessment_row.scoring_side,
        recommendation_score=recommendation_score,
        reason_codes=reason_codes,
    )


def _recommendation_action(
    *,
    assessment_status: str,
    readiness_status: str,
    recommendation_score: Decimal,
    config: PaperStrategyCandidateRecommendationConfig,
) -> str:
    if assessment_status == "blocked":
        return "reject"
    if readiness_status == "blocked":
        return "watch"
    if (
        assessment_status == "ready"
        and readiness_status == "pass"
        and recommendation_score >= config.min_recommendation_score
    ):
        return "recommend"
    return "watch"


def _recommendation_reason_codes(
    *,
    assessment_row: PaperCandidateAssessmentRow,
    readiness_status: str,
    recommendation_score: Decimal,
    config: PaperStrategyCandidateRecommendationConfig,
) -> tuple[str, ...]:
    reason_codes = list(assessment_row.reason_codes)
    _append_unique(reason_codes, _readiness_reason_code(readiness_status))
    _append_unique(
        reason_codes,
        f"candidate_{assessment_row.assessment_status}",
    )
    if recommendation_score < config.min_recommendation_score:
        _append_unique(reason_codes, "below_recommendation_threshold")
    return tuple(reason_codes)


def _readiness_reason_code(readiness_status: str) -> str:
    if readiness_status == "pass":
        return "readiness_passed"
    if readiness_status == "watch":
        return "readiness_watch"
    return "readiness_blocked"


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _validate_row_action_semantics(row: PaperStrategyCandidateRecommendationRow) -> None:
    if row.assessment_status == "blocked" and row.action != "reject":
        raise ValueError("blocked assessment rows must be rejected")
    if row.action == "recommend":
        if row.assessment_status != "ready":
            raise ValueError("recommended rows must be assessment ready")
        if row.readiness_status != "pass":
            raise ValueError("recommended rows must have passing readiness")
        if row.recommendation_score <= ZERO:
            raise ValueError("recommended rows must have positive recommendation_score")
    if row.readiness_status == "blocked" and row.action == "recommend":
        raise ValueError("blocked readiness rows cannot be recommended")


def _validate_assessment_report(report: Any) -> None:
    if type(report) is not PaperCandidateAssessmentReport:
        raise ValueError("assessment_report must be a PaperCandidateAssessmentReport")
    _validate_hard_flags("assessment_report", report)


def _validate_readiness_report(report: Any) -> None:
    if type(report) is not PaperStrategyReadinessStateReport:
        raise ValueError(
            "readiness_report must be a PaperStrategyReadinessStateReport",
        )
    _validate_hard_flags("readiness_report", report)


def _validate_hard_flags(field_name: str, report: Any) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if hasattr(report, flag_name) and getattr(report, flag_name) is not True:
            raise ValueError(f"{field_name} must be {flag_name}")


def _validate_report_consistency(
    report: PaperStrategyCandidateRecommendationReport,
) -> None:
    if report.candidate_count != len(report.recommendation_rows):
        raise ValueError("candidate_count must match recommendation_rows")
    if report.recommend_count != _action_count(
        report.recommendation_rows,
        "recommend",
    ):
        raise ValueError("recommend_count must match recommendation_rows")
    if report.watch_count != _action_count(report.recommendation_rows, "watch"):
        raise ValueError("watch_count must match recommendation_rows")
    if report.reject_count != _action_count(report.recommendation_rows, "reject"):
        raise ValueError("reject_count must match recommendation_rows")
    slugs = tuple(row.market_slug for row in report.recommendation_rows)
    if len(set(slugs)) != len(slugs):
        raise ValueError("recommendation_rows must contain unique market_slug values")
    if any(
        row.readiness_status != report.readiness_overall_status
        for row in report.recommendation_rows
    ):
        raise ValueError("readiness_overall_status must match recommendation_rows")
    if report.recommendation_rows != _order_rows(report.recommendation_rows):
        raise ValueError("recommendation_rows must use deterministic ordering")


def _normalize_recommendation_rows(
    rows: tuple[PaperStrategyCandidateRecommendationRow, ...],
) -> tuple[PaperStrategyCandidateRecommendationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("recommendation_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("recommendation_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperStrategyCandidateRecommendationRow:
            raise ValueError(
                "recommendation_rows must contain "
                "PaperStrategyCandidateRecommendationRow values",
            )
    return normalized


def _order_rows(
    rows: tuple[PaperStrategyCandidateRecommendationRow, ...],
) -> tuple[PaperStrategyCandidateRecommendationRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                ACTION_RANK[row.action],
                -row.recommendation_score,
                row.market_slug,
            ),
        ),
    )


def _action_count(
    rows: tuple[PaperStrategyCandidateRecommendationRow, ...],
    action: str,
) -> int:
    return sum(1 for row in rows if row.action == action)


def _as_utc(value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_decimal(field_name: str, value: Any) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")


def _require_finite_decimal(field_name: str, value: Any) -> None:
    _require_decimal(field_name, value)
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: Any) -> None:
    _require_finite_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_string_tuple(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _quantize_score(value: Decimal) -> Decimal:
    _require_finite_decimal("score", value)
    return value.quantize(SCORE_QUANTUM)
