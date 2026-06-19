from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable

try:
    from .strategy_candidate_recommendation import (
        PaperStrategyCandidateRecommendationReport,
    )
except ModuleNotFoundError as exc:
    if exc.name != "polymarket_alpha_lab.strategy_candidate_recommendation":
        raise
    PaperStrategyCandidateRecommendationReport = None


ACTIONS = ("recommend", "watch", "reject")
SIDES = ("yes", "no", "none")
NO_REASON_CODE = "no_reason_code"
ZERO = Decimal("0")


@dataclass(frozen=True)
class PaperStrategyRecommendationExplanationRow:
    market_slug: str
    action: str
    selected_side: str
    recommendation_score: Decimal
    primary_reason_code: str
    reason_codes: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_action(self.action)
        _require_side("selected_side", self.selected_side)
        _require_nonnegative_decimal("recommendation_score", self.recommendation_score)
        _require_canonical_string("primary_reason_code", self.primary_reason_code)
        reason_codes = _normalize_reason_codes(self.reason_codes)
        object.__setattr__(self, "reason_codes", reason_codes)
        expected_primary_reason_code = _primary_reason_code(reason_codes)
        if self.primary_reason_code != expected_primary_reason_code:
            raise ValueError("primary_reason_code must match reason_codes")
        expected_explanation = _canonical_explanation(
            action=self.action,
            selected_side=self.selected_side,
            recommendation_score=self.recommendation_score,
            primary_reason_code=self.primary_reason_code,
        )
        if self.explanation != expected_explanation:
            raise ValueError("explanation must be canonical")


@dataclass(frozen=True)
class PaperStrategyRecommendationExplanationReport:
    generated_at: datetime
    source_config_version: str
    recommendation_count: int
    recommend_count: int
    watch_count: int
    reject_count: int
    explanation_rows: tuple[PaperStrategyRecommendationExplanationRow, ...]
    primary_reason_code_counts: tuple[tuple[str, int], ...] | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_nonnegative_int("recommendation_count", self.recommendation_count)
        _require_nonnegative_int("recommend_count", self.recommend_count)
        _require_nonnegative_int("watch_count", self.watch_count)
        _require_nonnegative_int("reject_count", self.reject_count)
        explanation_rows = _normalize_explanation_rows(self.explanation_rows)
        object.__setattr__(self, "explanation_rows", explanation_rows)
        primary_reason_code_counts = _normalize_primary_reason_code_counts(
            self.primary_reason_code_counts,
            explanation_rows,
        )
        object.__setattr__(
            self,
            "primary_reason_code_counts",
            primary_reason_code_counts,
        )
        if self.recommendation_count != len(explanation_rows):
            raise ValueError("recommendation_count must match explanation_rows")
        if self.recommend_count != _action_count(explanation_rows, "recommend"):
            raise ValueError("recommend_count must match explanation_rows")
        if self.watch_count != _action_count(explanation_rows, "watch"):
            raise ValueError("watch_count must match explanation_rows")
        if self.reject_count != _action_count(explanation_rows, "reject"):
            raise ValueError("reject_count must match explanation_rows")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_strategy_recommendation_explanation_report(
    recommendation_report,
    *,
    generated_at: datetime,
) -> PaperStrategyRecommendationExplanationReport:
    _validate_recommendation_report(recommendation_report)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    explanation_rows = tuple(
        _build_explanation_row(row)
        for row in recommendation_report.recommendation_rows
    )
    return PaperStrategyRecommendationExplanationReport(
        generated_at=generated_at,
        source_config_version=recommendation_report.config_version,
        recommendation_count=len(explanation_rows),
        recommend_count=_action_count(explanation_rows, "recommend"),
        watch_count=_action_count(explanation_rows, "watch"),
        reject_count=_action_count(explanation_rows, "reject"),
        explanation_rows=explanation_rows,
        primary_reason_code_counts=_primary_reason_code_counts(explanation_rows),
    )


def _build_explanation_row(row: object) -> PaperStrategyRecommendationExplanationRow:
    reason_codes = _normalize_reason_codes(getattr(row, "reason_codes"))
    primary_reason_code = _primary_reason_code(reason_codes)
    action = getattr(row, "action")
    selected_side = getattr(row, "selected_side")
    recommendation_score = getattr(row, "recommendation_score")
    return PaperStrategyRecommendationExplanationRow(
        market_slug=getattr(row, "market_slug"),
        action=action,
        selected_side=selected_side,
        recommendation_score=recommendation_score,
        primary_reason_code=primary_reason_code,
        reason_codes=reason_codes,
        explanation=_canonical_explanation(
            action=action,
            selected_side=selected_side,
            recommendation_score=recommendation_score,
            primary_reason_code=primary_reason_code,
        ),
    )


def _validate_recommendation_report(recommendation_report: object) -> None:
    source_type = PaperStrategyCandidateRecommendationReport
    if source_type is None:
        raise ValueError(
            "recommendation_report must be a PaperStrategyCandidateRecommendationReport",
        )
    if type(recommendation_report) is not source_type:
        raise ValueError(
            "recommendation_report must be a PaperStrategyCandidateRecommendationReport",
        )
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(recommendation_report, flag_name, None) is not True:
            raise ValueError(f"recommendation_report {flag_name} must be True")
    _require_canonical_string(
        "recommendation_report config_version",
        getattr(recommendation_report, "config_version", None),
    )


def _primary_reason_code(reason_codes: tuple[str, ...]) -> str:
    return reason_codes[0] if reason_codes else NO_REASON_CODE


def _canonical_explanation(
    *,
    action: str,
    selected_side: str,
    recommendation_score: Decimal,
    primary_reason_code: str,
) -> str:
    return (
        f"{action} {selected_side} because {primary_reason_code} "
        f"(score {recommendation_score})"
    )


def _action_count(
    rows: tuple[PaperStrategyRecommendationExplanationRow, ...],
    action: str,
) -> int:
    return sum(1 for row in rows if row.action == action)


def _primary_reason_code_counts(
    rows: tuple[PaperStrategyRecommendationExplanationRow, ...],
) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.primary_reason_code] = counts.get(row.primary_reason_code, 0) + 1
    return tuple(
        sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        ),
    )


def _normalize_primary_reason_code_counts(
    value: Iterable[tuple[str, int]] | None,
    rows: tuple[PaperStrategyRecommendationExplanationRow, ...],
) -> tuple[tuple[str, int], ...]:
    expected = _primary_reason_code_counts(rows)
    if value is None:
        return expected
    if isinstance(value, (str, bytes)):
        raise ValueError("primary_reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("primary_reason_code_counts must be an iterable") from exc
    for row in counts:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("primary_reason_code_counts must contain tuple rows")
        reason_code, count = row
        _require_canonical_string("primary_reason_code_counts reason_code", reason_code)
        _require_nonnegative_int("primary_reason_code_counts count", count)
    if counts != expected:
        raise ValueError("primary_reason_code_counts must match explanation_rows")
    return counts


def _normalize_explanation_rows(
    value: Iterable[PaperStrategyRecommendationExplanationRow],
) -> tuple[PaperStrategyRecommendationExplanationRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("explanation_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("explanation_rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperStrategyRecommendationExplanationRow:
            raise ValueError(
                "explanation_rows must contain "
                "PaperStrategyRecommendationExplanationRow values",
            )
    return rows


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    return reason_codes


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_action(value: object) -> None:
    _require_canonical_string("action", value)
    if value not in ACTIONS:
        raise ValueError("action must be recommend, watch, or reject")


def _require_side(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in SIDES:
        raise ValueError(f"{field_name} must be yes, no, or none")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


__all__ = (
    "PaperStrategyRecommendationExplanationRow",
    "PaperStrategyRecommendationExplanationReport",
    "build_paper_strategy_recommendation_explanation_report",
)
