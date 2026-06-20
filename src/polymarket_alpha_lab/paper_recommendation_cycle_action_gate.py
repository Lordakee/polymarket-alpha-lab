"""Pure paper-only reducer from cycle review status to next action."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from polymarket_alpha_lab.paper_recommendation_cycle_review import (
    PaperRecommendationCycleReviewReasonCodeCount,
    PaperRecommendationCycleReviewReport,
)


REVIEW_STATUSES = ("pass", "watch", "blocked")
ACTION_STATUSES = ("research_ready", "watch", "blocked")
RECOMMENDED_NEXT_STEPS = (
    "build_candidate_research_queue",
    "await_fresh_cycle_evidence",
    "repair_cycle_evidence",
)
BLOCKED_REASON_CODES = frozenset(
    (
        "cycle_review_blocked",
        "missing_required_artifacts",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "cycle_review_watch",
        "cycle_history_stale",
    ),
)


@dataclass(frozen=True)
class PaperRecommendationCycleActionGateConfig:
    config_version: str

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)


@dataclass(frozen=True)
class PaperRecommendationCycleActionGateReasonCodeCount:
    reason_code: str
    count: int

    def __post_init__(self) -> None:
        _require_canonical_token("reason_code", self.reason_code)
        _require_positive_int("count", self.count)


@dataclass(frozen=True)
class PaperRecommendationCycleActionGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    review_status: str
    latest_final_status: str | None
    action_status: str
    recommended_next_step: str
    missing_required_artifact_count: int
    blocked_reason_count: int
    watch_reason_count: int
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_review_status("review_status", self.review_status)
        _require_optional_review_status("latest_final_status", self.latest_final_status)
        _require_action_status("action_status", self.action_status)
        _require_recommended_next_step(
            "recommended_next_step",
            self.recommended_next_step,
        )
        for field_name in (
            "missing_required_artifact_count",
            "blocked_reason_count",
            "watch_reason_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("cycle action gate report", self)


def build_paper_recommendation_cycle_action_gate_report(
    review: PaperRecommendationCycleReviewReport,
    *,
    config: PaperRecommendationCycleActionGateConfig,
    generated_at: datetime,
) -> PaperRecommendationCycleActionGateReport:
    """Reduce a cycle review report into a paper-only action gate report."""

    if type(config) is not PaperRecommendationCycleActionGateConfig:
        raise ValueError("config must be a PaperRecommendationCycleActionGateConfig")
    if type(review) is not PaperRecommendationCycleReviewReport:
        raise ValueError("review must be a PaperRecommendationCycleReviewReport")
    _require_hard_flags("cycle review report", review)

    action_status = _action_status(review)
    reason_code_counts = _derived_reason_code_counts(review)

    return PaperRecommendationCycleActionGateReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_config_version=review.config_version,
        review_status=review.review_status,
        latest_final_status=review.latest_final_status,
        action_status=action_status,
        recommended_next_step=_recommended_next_step(action_status),
        missing_required_artifact_count=len(review.missing_required_artifact_names),
        blocked_reason_count=_blocked_reason_count(reason_code_counts),
        watch_reason_count=_watch_reason_count(reason_code_counts),
        reason_code_counts=reason_code_counts,
    )


def _action_status(review: PaperRecommendationCycleReviewReport) -> str:
    if review.review_status == "pass" and (
        not review.missing_required_artifact_names
        and review.stale_history is False
    ):
        return "research_ready"
    if review.review_status == "blocked" or review.missing_required_artifact_names:
        return "blocked"
    return "watch"


def _recommended_next_step(action_status: str) -> str:
    if action_status == "research_ready":
        return "build_candidate_research_queue"
    if action_status == "blocked":
        return "repair_cycle_evidence"
    return "await_fresh_cycle_evidence"


def _derived_reason_code_counts(
    review: PaperRecommendationCycleReviewReport,
) -> tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for reason_count in review.reason_code_counts:
        if type(reason_count) is not PaperRecommendationCycleReviewReasonCodeCount:
            raise ValueError(
                "review reason_code_counts must contain "
                "PaperRecommendationCycleReviewReasonCodeCount",
            )
        counts[reason_count.reason_code] += reason_count.count
    counts[f"cycle_review_{review.review_status}"] += 1
    if review.missing_required_artifact_names:
        counts["missing_required_artifacts"] += len(
            review.missing_required_artifact_names,
        )
    if review.stale_history is True:
        counts["cycle_history_stale"] += 1
    return tuple(
        PaperRecommendationCycleActionGateReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in sorted(counts)
    )


def _blocked_reason_count(
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...],
) -> int:
    return sum(
        reason_count.count
        for reason_count in reason_code_counts
        if reason_count.reason_code in BLOCKED_REASON_CODES
        or reason_count.reason_code.endswith("_blocked")
    )


def _watch_reason_count(
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...],
) -> int:
    return sum(
        reason_count.count
        for reason_count in reason_code_counts
        if reason_count.reason_code in WATCH_REASON_CODES
        or reason_count.reason_code.endswith("_watch")
    )


def _validate_report_consistency(
    report: PaperRecommendationCycleActionGateReport,
) -> None:
    if report.recommended_next_step != _recommended_next_step(report.action_status):
        raise ValueError("recommended_next_step must match action_status")
    expected_missing_artifact_count = _reason_count(
        report.reason_code_counts,
        "missing_required_artifacts",
    )
    if report.missing_required_artifact_count != expected_missing_artifact_count:
        raise ValueError(
            "missing_required_artifact_count must match reason_code_counts",
        )
    if report.action_status != _status_from_review_fields(
        review_status=report.review_status,
        missing_required_artifact_count=report.missing_required_artifact_count,
        stale_history=_has_reason_code(report.reason_code_counts, "cycle_history_stale"),
    ):
        raise ValueError("action_status must match review fields")
    expected_blocked_reason_count = _blocked_reason_count(report.reason_code_counts)
    if report.blocked_reason_count != expected_blocked_reason_count:
        raise ValueError("blocked reason counts must match reason_code_counts")
    expected_watch_reason_count = _watch_reason_count(report.reason_code_counts)
    if report.watch_reason_count != expected_watch_reason_count:
        raise ValueError("watch reason counts must match reason_code_counts")


def _status_from_review_fields(
    *,
    review_status: str,
    missing_required_artifact_count: int,
    stale_history: bool,
) -> str:
    if (
        review_status == "pass"
        and missing_required_artifact_count == 0
        and stale_history is False
    ):
        return "research_ready"
    if review_status == "blocked" or missing_required_artifact_count > 0:
        return "blocked"
    return "watch"


def _has_reason_code(
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...],
    reason_code: str,
) -> bool:
    return any(reason_count.reason_code == reason_code for reason_count in reason_code_counts)


def _reason_count(
    reason_code_counts: tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...],
    reason_code: str,
) -> int:
    for reason_count in reason_code_counts:
        if reason_count.reason_code == reason_code:
            return reason_count.count
    return 0


def _normalize_reason_code_counts(
    values: Iterable[PaperRecommendationCycleActionGateReasonCodeCount],
) -> tuple[PaperRecommendationCycleActionGateReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    previous_reason_code: str | None = None
    for value in normalized:
        if type(value) is not PaperRecommendationCycleActionGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "PaperRecommendationCycleActionGateReasonCodeCount",
            )
        if previous_reason_code is not None and value.reason_code <= previous_reason_code:
            raise ValueError("reason_code_counts must be sorted by reason_code")
        previous_reason_code = value.reason_code
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_optional_review_status(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_review_status(field_name, value)


def _require_review_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REVIEW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_action_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ACTION_STATUSES:
        raise ValueError(f"{field_name} must be research_ready, watch, or blocked")


def _require_recommended_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RECOMMENDED_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known recommended next step")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_canonical_token(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.lower() != value or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be a canonical token")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "PaperRecommendationCycleActionGateConfig",
    "PaperRecommendationCycleActionGateReasonCodeCount",
    "PaperRecommendationCycleActionGateReport",
    "build_paper_recommendation_cycle_action_gate_report",
)
