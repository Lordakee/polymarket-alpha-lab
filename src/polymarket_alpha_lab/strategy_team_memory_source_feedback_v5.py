"""Pure readonly source-family feedback report for settled paper recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_TEAM_MEMORY_SOURCE_FEEDBACK_V5_CONFIG_VERSION = (
    "strategy-team-memory-source-feedback-v5"
)

PASS_REASON = "strategy_team_memory_source_feedback_v5_passed"
EMPTY_REASON = "strategy_team_memory_source_feedback_v5_empty"
LOW_ACCURACY_REASON = "strategy_team_memory_source_feedback_v5_low_accuracy"
STALE_SOURCES_REASON = "strategy_team_memory_source_feedback_v5_stale_sources"
CONFLICTED_SOURCES_REASON = "strategy_team_memory_source_feedback_v5_conflicted_sources"
RESOLUTION_LAG_REASON = "strategy_team_memory_source_feedback_v5_resolution_lag"

REASON_CODES = (
    PASS_REASON,
    EMPTY_REASON,
    LOW_ACCURACY_REASON,
    STALE_SOURCES_REASON,
    CONFLICTED_SOURCES_REASON,
    RESOLUTION_LAG_REASON,
)
SOURCE_FEEDBACK_STATUSES = ("pass", "watch", "blocked")
QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ZERO_QUANT = Decimal("0.000000")
ONE_QUANT = Decimal("1.000000")
STATUS_WEIGHT = {
    "pass": Decimal("0"),
    "watch": Decimal("1"),
    "blocked": Decimal("2"),
}

__all__ = (
    "DEFAULT_STRATEGY_TEAM_MEMORY_SOURCE_FEEDBACK_V5_CONFIG_VERSION",
    "StrategyTeamMemorySourceFamilyScore",
    "StrategyTeamMemorySourceFeedbackV5Config",
    "StrategyTeamMemorySourceFeedbackV5Report",
    "StrategyTeamMemorySourceFeedbackV5SettledRecommendation",
    "build_strategy_team_memory_source_feedback_v5_report",
    "strategy_team_memory_source_feedback_v5_report_payload",
)


@dataclass(frozen=True)
class StrategyTeamMemorySourceFeedbackV5Config:
    config_version: str = DEFAULT_STRATEGY_TEAM_MEMORY_SOURCE_FEEDBACK_V5_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("86400")
    max_resolution_lag_seconds: Decimal = Decimal("86400")
    min_pass_accuracy_rate: Decimal = Decimal("0.700000")
    min_watch_accuracy_rate: Decimal = Decimal("0.500000")
    max_pass_staleness_rate: Decimal = Decimal("0.250000")
    max_watch_staleness_rate: Decimal = Decimal("0.500000")
    max_pass_conflict_rate: Decimal = Decimal("0.250000")
    max_watch_conflict_rate: Decimal = Decimal("0.500000")
    max_pass_resolution_lag_rate: Decimal = Decimal("0.250000")
    max_watch_resolution_lag_rate: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("max_source_age_seconds", "max_resolution_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_accuracy_rate",
            "min_watch_accuracy_rate",
            "max_pass_staleness_rate",
            "max_watch_staleness_rate",
            "max_pass_conflict_rate",
            "max_watch_conflict_rate",
            "max_pass_resolution_lag_rate",
            "max_watch_resolution_lag_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_accuracy_rate < self.min_watch_accuracy_rate:
            raise ValueError("min_pass_accuracy_rate must not be below watch")
        for pass_field, watch_field in (
            ("max_pass_staleness_rate", "max_watch_staleness_rate"),
            ("max_pass_conflict_rate", "max_watch_conflict_rate"),
            ("max_pass_resolution_lag_rate", "max_watch_resolution_lag_rate"),
        ):
            if getattr(self, pass_field) > getattr(self, watch_field):
                raise ValueError(f"{pass_field} must not exceed {watch_field}")
        require_paper_only_flags("StrategyTeamMemorySourceFeedbackV5Config", self)


@dataclass(frozen=True)
class StrategyTeamMemorySourceFeedbackV5SettledRecommendation:
    team_id: str
    source_family: str
    recommendation_id: str
    recommendation_recorded_at: datetime
    source_observed_at: datetime
    settled_at: datetime
    resolution_recorded_at: datetime | None
    predicted_outcome: bool
    resolved_outcome: bool
    source_conflict_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "source_family", "recommendation_id"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "recommendation_recorded_at",
            "source_observed_at",
            "settled_at",
        ):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "resolution_recorded_at",
            _as_optional_utc("resolution_recorded_at", self.resolution_recorded_at),
        )
        _require_bool("predicted_outcome", self.predicted_outcome)
        _require_bool("resolved_outcome", self.resolved_outcome)
        object.__setattr__(
            self,
            "source_conflict_count",
            _require_nonnegative_integral_decimal(
                "source_conflict_count",
                self.source_conflict_count,
            ),
        )
        require_paper_only_flags(
            "StrategyTeamMemorySourceFeedbackV5SettledRecommendation",
            self,
        )
        _validate_settled_recommendation_chronology(self)
        reject_unsafe_surface_fields(
            "strategy team memory source feedback v5 settled recommendation",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamMemorySourceFamilyScore:
    team_id: str
    source_family: str
    recommendation_count: Decimal
    correct_recommendation_count: Decimal
    stale_source_count: Decimal
    conflicted_recommendation_count: Decimal
    resolution_lag_breach_count: Decimal
    source_conflict_count: Decimal
    accuracy_rate: Decimal
    staleness_rate: Decimal
    conflict_rate: Decimal
    resolution_lag_breach_rate: Decimal
    average_resolution_lag_seconds: Decimal
    source_family_score: Decimal
    source_feedback_status: str
    reason_codes: tuple[str, ...]
    recommendation_ids: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "source_family"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "recommendation_count",
            "correct_recommendation_count",
            "stale_source_count",
            "conflicted_recommendation_count",
            "resolution_lag_breach_count",
            "source_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "accuracy_rate",
            "staleness_rate",
            "conflict_rate",
            "resolution_lag_breach_rate",
            "source_family_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_resolution_lag_seconds",
            _require_nonnegative_decimal(
                "average_resolution_lag_seconds",
                self.average_resolution_lag_seconds,
            ),
        )
        _require_member("source_feedback_status", self.source_feedback_status, SOURCE_FEEDBACK_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "recommendation_ids",
            _normalize_string_tuple("recommendation_ids", self.recommendation_ids),
        )
        _validate_family_score(self)
        require_paper_only_flags("StrategyTeamMemorySourceFamilyScore", self)
        reject_unsafe_surface_fields(
            "strategy team memory source feedback v5 source family score",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamMemorySourceFeedbackV5Report:
    generated_at: datetime
    config_version: str
    source_feedback_status: str
    recommendation_count: Decimal
    source_family_count: Decimal
    pass_family_count: Decimal
    watch_family_count: Decimal
    blocked_family_count: Decimal
    correct_recommendation_count: Decimal
    stale_source_count: Decimal
    conflicted_recommendation_count: Decimal
    resolution_lag_breach_count: Decimal
    source_conflict_count: Decimal
    accuracy_rate: Decimal | None
    staleness_rate: Decimal | None
    conflict_rate: Decimal | None
    resolution_lag_breach_rate: Decimal | None
    average_resolution_lag_seconds: Decimal | None
    average_source_family_score: Decimal | None
    source_family_scores: tuple[StrategyTeamMemorySourceFamilyScore, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("source_feedback_status", self.source_feedback_status, SOURCE_FEEDBACK_STATUSES)
        for field_name in (
            "recommendation_count",
            "source_family_count",
            "pass_family_count",
            "watch_family_count",
            "blocked_family_count",
            "correct_recommendation_count",
            "stale_source_count",
            "conflicted_recommendation_count",
            "resolution_lag_breach_count",
            "source_conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "accuracy_rate",
            "staleness_rate",
            "conflict_rate",
            "resolution_lag_breach_rate",
            "average_source_family_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_resolution_lag_seconds",
            _normalize_optional_nonnegative_decimal(
                "average_resolution_lag_seconds",
                self.average_resolution_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_family_scores",
            _normalize_source_family_scores(self.source_family_scores),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report(self)
        require_paper_only_flags("StrategyTeamMemorySourceFeedbackV5Report", self)
        reject_unsafe_surface_fields(
            "strategy team memory source feedback v5 report",
            self,
        )


def build_strategy_team_memory_source_feedback_v5_report(
    settled_recommendations: list[StrategyTeamMemorySourceFeedbackV5SettledRecommendation]
    | tuple[StrategyTeamMemorySourceFeedbackV5SettledRecommendation, ...],
    *,
    config: StrategyTeamMemorySourceFeedbackV5Config,
    generated_at: datetime,
) -> StrategyTeamMemorySourceFeedbackV5Report:
    if type(config) is not StrategyTeamMemorySourceFeedbackV5Config:
        raise ValueError("config must be a StrategyTeamMemorySourceFeedbackV5Config")
    require_paper_only_flags("StrategyTeamMemorySourceFeedbackV5Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_settled_recommendations(
        settled_recommendations,
        generated_at=generated_at_utc,
    )
    family_scores = _source_family_scores(rows, config=config)
    recommendation_count = _count_decimal(len(rows))
    correct_count = _sum_counts(
        tuple(score.correct_recommendation_count for score in family_scores),
    )
    stale_count = _sum_counts(tuple(score.stale_source_count for score in family_scores))
    conflicted_count = _sum_counts(
        tuple(score.conflicted_recommendation_count for score in family_scores),
    )
    resolution_lag_breach_count = _sum_counts(
        tuple(score.resolution_lag_breach_count for score in family_scores),
    )
    reason_codes = _report_reason_codes(rows, family_scores)
    status = _report_status(reason_codes, family_scores)

    return StrategyTeamMemorySourceFeedbackV5Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_feedback_status=status,
        recommendation_count=recommendation_count,
        source_family_count=_count_decimal(len(family_scores)),
        pass_family_count=_family_status_count(family_scores, "pass"),
        watch_family_count=_family_status_count(family_scores, "watch"),
        blocked_family_count=_family_status_count(family_scores, "blocked"),
        correct_recommendation_count=correct_count,
        stale_source_count=stale_count,
        conflicted_recommendation_count=conflicted_count,
        resolution_lag_breach_count=resolution_lag_breach_count,
        source_conflict_count=_sum_counts(tuple(score.source_conflict_count for score in family_scores)),
        accuracy_rate=_optional_ratio(correct_count, recommendation_count),
        staleness_rate=_optional_ratio(stale_count, recommendation_count),
        conflict_rate=_optional_ratio(conflicted_count, recommendation_count),
        resolution_lag_breach_rate=_optional_ratio(
            resolution_lag_breach_count,
            recommendation_count,
        ),
        average_resolution_lag_seconds=_average(
            tuple(_resolution_lag_seconds(row) for row in rows),
        ),
        average_source_family_score=_average(
            tuple(score.source_family_score for score in family_scores),
        ),
        source_family_scores=family_scores,
        reason_codes=reason_codes,
    )


def strategy_team_memory_source_feedback_v5_report_payload(
    report: StrategyTeamMemorySourceFeedbackV5Report,
) -> dict[str, Any]:
    if type(report) is not StrategyTeamMemorySourceFeedbackV5Report:
        raise ValueError("report must be a StrategyTeamMemorySourceFeedbackV5Report")
    require_paper_only_flags("StrategyTeamMemorySourceFeedbackV5Report", report)
    reject_unsafe_surface_fields(
        "strategy team memory source feedback v5 report",
        report,
    )
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _normalize_settled_recommendations(
    settled_recommendations: list[StrategyTeamMemorySourceFeedbackV5SettledRecommendation]
    | tuple[StrategyTeamMemorySourceFeedbackV5SettledRecommendation, ...],
    *,
    generated_at: datetime,
) -> tuple[StrategyTeamMemorySourceFeedbackV5SettledRecommendation, ...]:
    if type(settled_recommendations) not in (list, tuple):
        raise ValueError("settled_recommendations must be a list or tuple")
    rows = tuple(settled_recommendations)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyTeamMemorySourceFeedbackV5SettledRecommendation:
            raise ValueError(
                "settled_recommendations must contain StrategyTeamMemorySourceFeedbackV5SettledRecommendation values",
            )
        require_paper_only_flags(
            "StrategyTeamMemorySourceFeedbackV5SettledRecommendation",
            row,
        )
        if row.recommendation_recorded_at > generated_at:
            raise ValueError("recommendation_recorded_at must not be in the future")
        if row.source_observed_at > generated_at:
            raise ValueError("source_observed_at must not be in the future")
        if row.settled_at > generated_at:
            raise ValueError("settled_at must not be in the future")
        if row.resolution_recorded_at is not None and row.resolution_recorded_at > generated_at:
            raise ValueError("resolution_recorded_at must not be in the future")
        key = (row.team_id, row.recommendation_id)
        if key in seen:
            raise ValueError("recommendation_id values must be unique per team")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.team_id, row.source_family, row.recommendation_id)))


def _source_family_scores(
    rows: tuple[StrategyTeamMemorySourceFeedbackV5SettledRecommendation, ...],
    *,
    config: StrategyTeamMemorySourceFeedbackV5Config,
) -> tuple[StrategyTeamMemorySourceFamilyScore, ...]:
    keys = tuple(sorted({(row.team_id, row.source_family) for row in rows}))
    return tuple(_source_family_score(key, rows, config=config) for key in keys)


def _source_family_score(
    key: tuple[str, str],
    rows: tuple[StrategyTeamMemorySourceFeedbackV5SettledRecommendation, ...],
    *,
    config: StrategyTeamMemorySourceFeedbackV5Config,
) -> StrategyTeamMemorySourceFamilyScore:
    team_id, source_family = key
    scoped_rows = tuple(
        row for row in rows if row.team_id == team_id and row.source_family == source_family
    )
    recommendation_count = _count_decimal(len(scoped_rows))
    correct_count = _count_decimal(
        sum(1 for row in scoped_rows if row.predicted_outcome is row.resolved_outcome),
    )
    stale_count = _count_decimal(
        sum(1 for row in scoped_rows if _is_stale(row, config.max_source_age_seconds)),
    )
    conflicted_count = _count_decimal(sum(1 for row in scoped_rows if row.source_conflict_count > ZERO))
    lag_breach_count = _count_decimal(
        sum(
            1
            for row in scoped_rows
            if _resolution_lag_seconds(row) > config.max_resolution_lag_seconds
        ),
    )
    accuracy_rate = _ratio(correct_count, recommendation_count)
    staleness_rate = _ratio(stale_count, recommendation_count)
    conflict_rate = _ratio(conflicted_count, recommendation_count)
    resolution_lag_breach_rate = _ratio(lag_breach_count, recommendation_count)
    source_family_score = _source_family_score_value(
        accuracy_rate=accuracy_rate,
        staleness_rate=staleness_rate,
        conflict_rate=conflict_rate,
        resolution_lag_breach_rate=resolution_lag_breach_rate,
    )
    reason_codes = _family_reason_codes(
        accuracy_rate=accuracy_rate,
        staleness_rate=staleness_rate,
        conflict_rate=conflict_rate,
        resolution_lag_breach_rate=resolution_lag_breach_rate,
        config=config,
    )

    return StrategyTeamMemorySourceFamilyScore(
        team_id=team_id,
        source_family=source_family,
        recommendation_count=recommendation_count,
        correct_recommendation_count=correct_count,
        stale_source_count=stale_count,
        conflicted_recommendation_count=conflicted_count,
        resolution_lag_breach_count=lag_breach_count,
        source_conflict_count=_sum_counts(tuple(row.source_conflict_count for row in scoped_rows)),
        accuracy_rate=accuracy_rate,
        staleness_rate=staleness_rate,
        conflict_rate=conflict_rate,
        resolution_lag_breach_rate=resolution_lag_breach_rate,
        average_resolution_lag_seconds=_average_or_zero(
            tuple(_resolution_lag_seconds(row) for row in scoped_rows),
        ),
        source_family_score=source_family_score,
        source_feedback_status=_family_status(
            accuracy_rate=accuracy_rate,
            staleness_rate=staleness_rate,
            conflict_rate=conflict_rate,
            resolution_lag_breach_rate=resolution_lag_breach_rate,
            config=config,
        ),
        reason_codes=reason_codes,
        recommendation_ids=tuple(sorted(row.recommendation_id for row in scoped_rows)),
    )


def _family_reason_codes(
    *,
    accuracy_rate: Decimal,
    staleness_rate: Decimal,
    conflict_rate: Decimal,
    resolution_lag_breach_rate: Decimal,
    config: StrategyTeamMemorySourceFeedbackV5Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if accuracy_rate < config.min_pass_accuracy_rate:
        reason_codes.append(LOW_ACCURACY_REASON)
    if staleness_rate > config.max_pass_staleness_rate:
        reason_codes.append(STALE_SOURCES_REASON)
    if conflict_rate > config.max_pass_conflict_rate:
        reason_codes.append(CONFLICTED_SOURCES_REASON)
    if resolution_lag_breach_rate > config.max_pass_resolution_lag_rate:
        reason_codes.append(RESOLUTION_LAG_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _family_status(
    *,
    accuracy_rate: Decimal,
    staleness_rate: Decimal,
    conflict_rate: Decimal,
    resolution_lag_breach_rate: Decimal,
    config: StrategyTeamMemorySourceFeedbackV5Config,
) -> str:
    blocked = (
        accuracy_rate < config.min_watch_accuracy_rate
        or staleness_rate > config.max_watch_staleness_rate
        or conflict_rate > config.max_watch_conflict_rate
        or resolution_lag_breach_rate > config.max_watch_resolution_lag_rate
    )
    if blocked:
        return "blocked"
    watch = (
        accuracy_rate < config.min_pass_accuracy_rate
        or staleness_rate > config.max_pass_staleness_rate
        or conflict_rate > config.max_pass_conflict_rate
        or resolution_lag_breach_rate > config.max_pass_resolution_lag_rate
    )
    if watch:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyTeamMemorySourceFeedbackV5SettledRecommendation, ...],
    family_scores: tuple[StrategyTeamMemorySourceFamilyScore, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    for reason_code in (
        LOW_ACCURACY_REASON,
        STALE_SOURCES_REASON,
        CONFLICTED_SOURCES_REASON,
        RESOLUTION_LAG_REASON,
    ):
        if any(reason_code in family_score.reason_codes for family_score in family_scores):
            reason_codes.append(reason_code)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _report_status(
    reason_codes: tuple[str, ...],
    family_scores: tuple[StrategyTeamMemorySourceFamilyScore, ...],
) -> str:
    if reason_codes == (EMPTY_REASON,):
        return "watch"
    if reason_codes == (PASS_REASON,):
        return "pass"
    if any(score.source_feedback_status == "blocked" for score in family_scores):
        return "blocked"
    return "watch"


def _source_family_score_value(
    *,
    accuracy_rate: Decimal,
    staleness_rate: Decimal,
    conflict_rate: Decimal,
    resolution_lag_breach_rate: Decimal,
) -> Decimal:
    penalty_average = _ratio(
        staleness_rate + conflict_rate + resolution_lag_breach_rate,
        Decimal("3"),
    )
    return _clamp_probability(_q((accuracy_rate + (ONE_QUANT - penalty_average)) / Decimal("2")))


def _is_stale(
    row: StrategyTeamMemorySourceFeedbackV5SettledRecommendation,
    max_source_age_seconds: Decimal,
) -> bool:
    return _elapsed_seconds(row.recommendation_recorded_at, row.source_observed_at) > max_source_age_seconds


def _resolution_lag_seconds(
    row: StrategyTeamMemorySourceFeedbackV5SettledRecommendation,
) -> Decimal:
    end = row.resolution_recorded_at if row.resolution_recorded_at is not None else row.settled_at
    return _elapsed_seconds(end, row.settled_at)


def _elapsed_seconds(later: datetime, earlier: datetime) -> Decimal:
    if later < earlier:
        raise ValueError("later datetime must not be earlier than earlier datetime")
    delta = later - earlier
    return _q(
        Decimal(delta.days * 86400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000")),
    )


def _validate_settled_recommendation_chronology(
    row: StrategyTeamMemorySourceFeedbackV5SettledRecommendation,
) -> None:
    if row.source_observed_at > row.recommendation_recorded_at:
        raise ValueError("source_observed_at must not be after recommendation_recorded_at")
    if row.recommendation_recorded_at > row.settled_at:
        raise ValueError("recommendation_recorded_at must not be after settled_at")
    if row.resolution_recorded_at is not None and row.resolution_recorded_at < row.settled_at:
        raise ValueError("resolution_recorded_at must not be before settled_at")


def _validate_family_score(score: StrategyTeamMemorySourceFamilyScore) -> None:
    if score.correct_recommendation_count > score.recommendation_count:
        raise ValueError("correct_recommendation_count must not exceed recommendation_count")
    if score.stale_source_count > score.recommendation_count:
        raise ValueError("stale_source_count must not exceed recommendation_count")
    if score.conflicted_recommendation_count > score.recommendation_count:
        raise ValueError("conflicted_recommendation_count must not exceed recommendation_count")
    if score.resolution_lag_breach_count > score.recommendation_count:
        raise ValueError("resolution_lag_breach_count must not exceed recommendation_count")
    if _count_decimal(len(score.recommendation_ids)) != score.recommendation_count:
        raise ValueError("recommendation_ids must match recommendation_count")


def _validate_report(report: StrategyTeamMemorySourceFeedbackV5Report) -> None:
    if report.source_family_count != _count_decimal(len(report.source_family_scores)):
        raise ValueError("source_family_count must match source_family_scores")
    if (
        report.pass_family_count + report.watch_family_count + report.blocked_family_count
        != report.source_family_count
    ):
        raise ValueError("family status counts must match source_family_count")
    if report.correct_recommendation_count > report.recommendation_count:
        raise ValueError("correct_recommendation_count must not exceed recommendation_count")
    if report.stale_source_count > report.recommendation_count:
        raise ValueError("stale_source_count must not exceed recommendation_count")
    if report.conflicted_recommendation_count > report.recommendation_count:
        raise ValueError("conflicted_recommendation_count must not exceed recommendation_count")
    if report.resolution_lag_breach_count > report.recommendation_count:
        raise ValueError("resolution_lag_breach_count must not exceed recommendation_count")


def _normalize_source_family_scores(
    scores: tuple[StrategyTeamMemorySourceFamilyScore, ...],
) -> tuple[StrategyTeamMemorySourceFamilyScore, ...]:
    if type(scores) is not tuple:
        raise ValueError("source_family_scores must be a tuple")
    for score in scores:
        if type(score) is not StrategyTeamMemorySourceFamilyScore:
            raise ValueError(
                "source_family_scores must contain StrategyTeamMemorySourceFamilyScore values",
            )
    return tuple(sorted(scores, key=lambda score: (score.team_id, score.source_family)))


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, REASON_CODES)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _normalize_string_tuple(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        _require_canonical_string(field_name, value)
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must be unique")
    return values


def _family_status_count(
    family_scores: tuple[StrategyTeamMemorySourceFamilyScore, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for score in family_scores if score.source_feedback_status == status))


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total


def _average(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _ratio(_sum_counts(values), _count_decimal(len(values)))


def _average_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    average = _average(values)
    return ZERO_QUANT if average is None else average


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    return _ratio(numerator, denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    return _q(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical string")


def _require_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _q(normalized)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _q(normalized)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_integral_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative integral Decimal")
    return normalized


def _require_probability_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > Decimal("1"):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _q(normalized)


def _normalize_optional_probability_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO_QUANT:
        return ZERO_QUANT
    if value > ONE_QUANT:
        return ONE_QUANT
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _q(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_EVEN)
