"""Pure readonly reducer for strategy team learning feedback v3."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_TEAM_LEARNING_FEEDBACK_V3_CONFIG_VERSION = (
    "strategy-team-learning-feedback-v3-v0"
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)

STATUSES = ("pass", "watch", "blocked")
STATUS_SORT_PRIORITY = {"blocked": 0, "watch": 1, "pass": 2}
EMPTY_REASON_CODE = "strategy_team_learning_feedback_v3_empty"
REASON_CODES = (
    "strategy_team_learning_feedback_v3_calibration_blocked",
    "strategy_team_learning_feedback_v3_calibration_watch",
    "strategy_team_learning_feedback_v3_source_reliability_below_min",
    "strategy_team_learning_feedback_v3_source_failure_tags_observed",
    "strategy_team_learning_feedback_v3_playbook_updates_suggested",
    "strategy_team_learning_feedback_v3_passed",
)
REPORT_REASON_CODES = (EMPTY_REASON_CODE, *REASON_CODES)

__all__ = (
    "DEFAULT_STRATEGY_TEAM_LEARNING_FEEDBACK_V3_CONFIG_VERSION",
    "StrategyTeamLearningFeedbackV3Config",
    "StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion",
    "StrategyTeamLearningFeedbackV3Report",
    "StrategyTeamLearningFeedbackV3ResolvedRecommendation",
    "StrategyTeamLearningFeedbackV3SourceFailureTagCount",
    "StrategyTeamLearningFeedbackV3TeamLesson",
    "build_strategy_team_learning_feedback_v3_report",
    "strategy_team_learning_feedback_v3_payload",
)


@dataclass(frozen=True)
class StrategyTeamLearningFeedbackV3Config:
    config_version: str = DEFAULT_STRATEGY_TEAM_LEARNING_FEEDBACK_V3_CONFIG_VERSION
    calibration_watch_delta_threshold: Decimal = Decimal("0.100000")
    calibration_blocked_delta_threshold: Decimal = Decimal("0.250000")
    min_source_reliability_score: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "calibration_watch_delta_threshold",
            "calibration_blocked_delta_threshold",
            "min_source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.calibration_blocked_delta_threshold < self.calibration_watch_delta_threshold:
            raise ValueError("calibration_blocked_delta_threshold must not be below watch")
        require_paper_only_flags("StrategyTeamLearningFeedbackV3Config", self)


@dataclass(frozen=True)
class StrategyTeamLearningFeedbackV3ResolvedRecommendation:
    team_id: str
    category_id: str
    recommendation_id: str
    playbook_section: str
    resolved_at: datetime
    recommended_probability: Decimal
    resolved_outcome: Decimal
    source_reliability_score: Decimal
    source_failure_tags: tuple[str, ...] = ()
    playbook_update_suggestions: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "team_id",
            "category_id",
            "recommendation_id",
            "playbook_section",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for field_name in (
            "recommended_probability",
            "resolved_outcome",
            "source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_failure_tags",
            _normalize_string_tuple("source_failure_tags", self.source_failure_tags),
        )
        object.__setattr__(
            self,
            "playbook_update_suggestions",
            _normalize_string_tuple(
                "playbook_update_suggestions",
                self.playbook_update_suggestions,
            ),
        )
        reject_unsafe_surface_fields("learning feedback v3 resolved recommendation", self)
        require_paper_only_flags(
            "StrategyTeamLearningFeedbackV3ResolvedRecommendation",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamLearningFeedbackV3TeamLesson:
    team_id: str
    category_id: str
    playbook_section: str
    team_lesson: str
    lesson_status: str
    resolved_recommendation_count: Decimal
    average_recommended_probability: Decimal
    average_resolved_outcome: Decimal
    calibration_delta: Decimal
    average_source_reliability_score: Decimal
    source_failure_tags: tuple[str, ...]
    playbook_update_suggestions: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("team_id", "category_id", "playbook_section", "team_lesson"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("lesson_status", self.lesson_status, STATUSES)
        object.__setattr__(
            self,
            "resolved_recommendation_count",
            _normalize_positive_count(
                "resolved_recommendation_count",
                self.resolved_recommendation_count,
            ),
        )
        for field_name in (
            "average_recommended_probability",
            "average_resolved_outcome",
            "average_source_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_delta",
            _normalize_delta("calibration_delta", self.calibration_delta),
        )
        object.__setattr__(
            self,
            "source_failure_tags",
            _normalize_string_tuple("source_failure_tags", self.source_failure_tags),
        )
        object.__setattr__(
            self,
            "playbook_update_suggestions",
            _normalize_string_tuple(
                "playbook_update_suggestions",
                self.playbook_update_suggestions,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REASON_CODES),
        )
        _validate_lesson(self)
        reject_unsafe_surface_fields("learning feedback v3 team lesson", self)
        require_paper_only_flags("StrategyTeamLearningFeedbackV3TeamLesson", self)


@dataclass(frozen=True)
class StrategyTeamLearningFeedbackV3SourceFailureTagCount:
    source_failure_tag: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("source_failure_tag", self.source_failure_tag)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        require_paper_only_flags(
            "StrategyTeamLearningFeedbackV3SourceFailureTagCount",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion:
    playbook_section: str
    suggestion: str
    supporting_lesson_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("playbook_section", self.playbook_section)
        _require_canonical_string("suggestion", self.suggestion)
        object.__setattr__(
            self,
            "supporting_lesson_count",
            _normalize_positive_count(
                "supporting_lesson_count",
                self.supporting_lesson_count,
            ),
        )
        require_paper_only_flags(
            "StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion",
            self,
        )


@dataclass(frozen=True)
class StrategyTeamLearningFeedbackV3Report:
    generated_at: datetime
    config_version: str
    source_recommendation_count: Decimal
    team_lesson_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_calibration_delta: Decimal
    average_source_reliability_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    team_lessons: tuple[StrategyTeamLearningFeedbackV3TeamLesson, ...]
    source_failure_tag_counts: tuple[StrategyTeamLearningFeedbackV3SourceFailureTagCount, ...]
    playbook_update_suggestions: tuple[
        StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_recommendation_count",
            "team_lesson_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_calibration_delta",
            _normalize_delta("average_calibration_delta", self.average_calibration_delta),
        )
        object.__setattr__(
            self,
            "average_source_reliability_score",
            _normalize_probability(
                "average_source_reliability_score",
                self.average_source_reliability_score,
            ),
        )
        _require_member("report_status", self.report_status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "team_lessons", _normalize_lessons(self.team_lessons))
        object.__setattr__(
            self,
            "source_failure_tag_counts",
            _normalize_tag_counts(self.source_failure_tag_counts),
        )
        object.__setattr__(
            self,
            "playbook_update_suggestions",
            _normalize_suggestions(self.playbook_update_suggestions),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("learning feedback v3 report", self)
        require_paper_only_flags("StrategyTeamLearningFeedbackV3Report", self)


def build_strategy_team_learning_feedback_v3_report(
    recommendations: Iterable[object],
    *,
    config: StrategyTeamLearningFeedbackV3Config,
    generated_at: datetime,
) -> StrategyTeamLearningFeedbackV3Report:
    if type(config) is not StrategyTeamLearningFeedbackV3Config:
        raise ValueError("config must be a StrategyTeamLearningFeedbackV3Config")
    require_paper_only_flags("StrategyTeamLearningFeedbackV3Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_recommendations = _normalize_recommendations(recommendations)
    for recommendation in source_recommendations:
        if recommendation.resolved_at > generated_at_utc:
            raise ValueError("resolved_at must not be after generated_at")

    lessons = _build_lessons(source_recommendations, config=config)
    return StrategyTeamLearningFeedbackV3Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_recommendation_count=_count(len(source_recommendations)),
        team_lesson_count=_count(len(lessons)),
        pass_count=_status_count(lessons, "pass"),
        watch_count=_status_count(lessons, "watch"),
        blocked_count=_status_count(lessons, "blocked"),
        average_calibration_delta=_recommendation_average_delta(source_recommendations),
        average_source_reliability_score=_recommendation_average_source_score(
            source_recommendations,
        ),
        report_status=_report_status(lessons),
        reason_codes=_report_reason_codes(lessons),
        team_lessons=lessons,
        source_failure_tag_counts=_source_failure_tag_counts_from_recommendations(
            source_recommendations,
        ),
        playbook_update_suggestions=_playbook_update_suggestions(lessons),
    )


def strategy_team_learning_feedback_v3_payload(
    report: StrategyTeamLearningFeedbackV3Report,
) -> dict[str, Any]:
    if type(report) is not StrategyTeamLearningFeedbackV3Report:
        raise ValueError("report must be a StrategyTeamLearningFeedbackV3Report")
    require_paper_only_flags("StrategyTeamLearningFeedbackV3Report", report)
    reject_unsafe_surface_fields("learning feedback v3 report", report)
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    reject_unsafe_surface_fields("learning feedback v3 payload", payload)
    return payload


def _normalize_recommendations(
    recommendations: Iterable[object],
) -> tuple[StrategyTeamLearningFeedbackV3ResolvedRecommendation, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        normalized = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen_ids: set[str] = set()
    for recommendation in normalized:
        if type(recommendation) is not StrategyTeamLearningFeedbackV3ResolvedRecommendation:
            raise ValueError(
                "recommendations must contain StrategyTeamLearningFeedbackV3ResolvedRecommendation values",
            )
        require_paper_only_flags(
            "StrategyTeamLearningFeedbackV3ResolvedRecommendation",
            recommendation,
        )
        if recommendation.recommendation_id in seen_ids:
            raise ValueError("recommendation_id values must be unique")
        seen_ids.add(recommendation.recommendation_id)
    return normalized


def _build_lessons(
    recommendations: tuple[StrategyTeamLearningFeedbackV3ResolvedRecommendation, ...],
    *,
    config: StrategyTeamLearningFeedbackV3Config,
) -> tuple[StrategyTeamLearningFeedbackV3TeamLesson, ...]:
    grouped: dict[tuple[str, str, str], list[StrategyTeamLearningFeedbackV3ResolvedRecommendation]]
    grouped = {}
    for recommendation in recommendations:
        key = (
            recommendation.team_id,
            recommendation.category_id,
            recommendation.playbook_section,
        )
        grouped.setdefault(key, []).append(recommendation)
    lessons = tuple(
        _build_lesson(
            team_id=team_id,
            category_id=category_id,
            playbook_section=playbook_section,
            recommendations=tuple(group),
            config=config,
        )
        for (team_id, category_id, playbook_section), group in grouped.items()
    )
    return tuple(sorted(lessons, key=_lesson_sort_key))


def _build_lesson(
    *,
    team_id: str,
    category_id: str,
    playbook_section: str,
    recommendations: tuple[StrategyTeamLearningFeedbackV3ResolvedRecommendation, ...],
    config: StrategyTeamLearningFeedbackV3Config,
) -> StrategyTeamLearningFeedbackV3TeamLesson:
    count = _count(len(recommendations))
    average_recommended_probability = _average(
        tuple(recommendation.recommended_probability for recommendation in recommendations),
    )
    average_resolved_outcome = _average(
        tuple(recommendation.resolved_outcome for recommendation in recommendations),
    )
    calibration_delta = _quantize_ratio(
        average_resolved_outcome - average_recommended_probability,
    )
    average_source_reliability_score = _average(
        tuple(recommendation.source_reliability_score for recommendation in recommendations),
    )
    source_failure_tags = tuple(
        sorted(
            {
                tag
                for recommendation in recommendations
                for tag in recommendation.source_failure_tags
            },
        ),
    )
    playbook_update_suggestions = tuple(
        sorted(
            {
                suggestion
                for recommendation in recommendations
                for suggestion in recommendation.playbook_update_suggestions
            },
        ),
    )
    reason_codes = _lesson_reason_codes(
        calibration_delta=calibration_delta,
        average_source_reliability_score=average_source_reliability_score,
        source_failure_tags=source_failure_tags,
        playbook_update_suggestions=playbook_update_suggestions,
        config=config,
    )
    lesson_status = _lesson_status(
        calibration_delta=calibration_delta,
        reason_codes=reason_codes,
        config=config,
    )
    return StrategyTeamLearningFeedbackV3TeamLesson(
        team_id=team_id,
        category_id=category_id,
        playbook_section=playbook_section,
        team_lesson=_team_lesson_text(
            team_id=team_id,
            category_id=category_id,
            lesson_status=lesson_status,
        ),
        lesson_status=lesson_status,
        resolved_recommendation_count=count,
        average_recommended_probability=average_recommended_probability,
        average_resolved_outcome=average_resolved_outcome,
        calibration_delta=calibration_delta,
        average_source_reliability_score=average_source_reliability_score,
        source_failure_tags=source_failure_tags,
        playbook_update_suggestions=playbook_update_suggestions,
        reason_codes=reason_codes,
    )


def _lesson_reason_codes(
    *,
    calibration_delta: Decimal,
    average_source_reliability_score: Decimal,
    source_failure_tags: tuple[str, ...],
    playbook_update_suggestions: tuple[str, ...],
    config: StrategyTeamLearningFeedbackV3Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    absolute_delta = abs(calibration_delta)
    if absolute_delta >= config.calibration_blocked_delta_threshold:
        codes.append("strategy_team_learning_feedback_v3_calibration_blocked")
    elif absolute_delta >= config.calibration_watch_delta_threshold:
        codes.append("strategy_team_learning_feedback_v3_calibration_watch")
    if average_source_reliability_score < config.min_source_reliability_score:
        codes.append("strategy_team_learning_feedback_v3_source_reliability_below_min")
    if source_failure_tags:
        codes.append("strategy_team_learning_feedback_v3_source_failure_tags_observed")
    if playbook_update_suggestions:
        codes.append("strategy_team_learning_feedback_v3_playbook_updates_suggested")
    if not codes:
        codes.append("strategy_team_learning_feedback_v3_passed")
    return _normalize_reason_codes("reason_codes", tuple(codes), REASON_CODES)


def _lesson_status(
    *,
    calibration_delta: Decimal,
    reason_codes: tuple[str, ...],
    config: StrategyTeamLearningFeedbackV3Config,
) -> str:
    if calibration_delta <= -config.calibration_blocked_delta_threshold:
        return "blocked"
    if reason_codes != ("strategy_team_learning_feedback_v3_passed",):
        return "watch"
    return "pass"


def _team_lesson_text(*, team_id: str, category_id: str, lesson_status: str) -> str:
    if lesson_status == "blocked":
        return f"reduce_{team_id}_{category_id}_playbook_confidence"
    if lesson_status == "watch":
        return f"review_{team_id}_{category_id}_playbook_calibration"
    return f"reuse_{team_id}_{category_id}_playbook"


def _report_status(lessons: tuple[StrategyTeamLearningFeedbackV3TeamLesson, ...]) -> str:
    if any(lesson.lesson_status == "blocked" for lesson in lessons):
        return "blocked"
    if any(lesson.lesson_status == "watch" for lesson in lessons) or not lessons:
        return "watch"
    return "pass"


def _report_reason_codes(
    lessons: tuple[StrategyTeamLearningFeedbackV3TeamLesson, ...],
) -> tuple[str, ...]:
    if not lessons:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for lesson in lessons:
        observed.update(lesson.reason_codes)
    if any(lesson.lesson_status == "watch" for lesson in lessons):
        observed.add("strategy_team_learning_feedback_v3_calibration_watch")
    if any(code != "strategy_team_learning_feedback_v3_passed" for code in observed):
        observed.discard("strategy_team_learning_feedback_v3_passed")
    return tuple(code for code in REPORT_REASON_CODES[1:] if code in observed)


def _source_failure_tag_counts(
    lessons: tuple[StrategyTeamLearningFeedbackV3TeamLesson, ...],
) -> tuple[StrategyTeamLearningFeedbackV3SourceFailureTagCount, ...]:
    counts: Counter[str] = Counter()
    for lesson in lessons:
        counts.update(lesson.source_failure_tags)
    return tuple(
        sorted(
            (
                StrategyTeamLearningFeedbackV3SourceFailureTagCount(
                    source_failure_tag=tag,
                    count=_count(count),
                )
                for tag, count in counts.items()
            ),
            key=lambda item: (-item.count, item.source_failure_tag),
        ),
    )


def _source_failure_tag_counts_from_recommendations(
    recommendations: tuple[StrategyTeamLearningFeedbackV3ResolvedRecommendation, ...],
) -> tuple[StrategyTeamLearningFeedbackV3SourceFailureTagCount, ...]:
    counts: Counter[str] = Counter()
    for recommendation in recommendations:
        counts.update(recommendation.source_failure_tags)
    return tuple(
        sorted(
            (
                StrategyTeamLearningFeedbackV3SourceFailureTagCount(
                    source_failure_tag=tag,
                    count=_count(count),
                )
                for tag, count in counts.items()
            ),
            key=lambda item: (-item.count, item.source_failure_tag),
        ),
    )


def _playbook_update_suggestions(
    lessons: tuple[StrategyTeamLearningFeedbackV3TeamLesson, ...],
) -> tuple[StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion, ...]:
    counts: Counter[tuple[str, str]] = Counter()
    for lesson in lessons:
        for suggestion in lesson.playbook_update_suggestions:
            counts[(lesson.playbook_section, suggestion)] += 1
    return tuple(
        StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion(
            playbook_section=playbook_section,
            suggestion=suggestion,
            supporting_lesson_count=_count(count),
        )
        for (playbook_section, suggestion), count in sorted(counts.items())
    )


def _recommendation_average_delta(
    recommendations: tuple[StrategyTeamLearningFeedbackV3ResolvedRecommendation, ...],
) -> Decimal:
    if not recommendations:
        return ZERO_RATIO
    return _average(
        tuple(
            recommendation.resolved_outcome - recommendation.recommended_probability
            for recommendation in recommendations
        ),
    )


def _recommendation_average_source_score(
    recommendations: tuple[StrategyTeamLearningFeedbackV3ResolvedRecommendation, ...],
) -> Decimal:
    if not recommendations:
        return ZERO_RATIO
    return _average(
        tuple(recommendation.source_reliability_score for recommendation in recommendations),
    )


def _status_count(
    lessons: tuple[StrategyTeamLearningFeedbackV3TeamLesson, ...],
    status: str,
) -> Decimal:
    return _count(sum(lesson.lesson_status == status for lesson in lessons))


def _lesson_sort_key(lesson: StrategyTeamLearningFeedbackV3TeamLesson) -> tuple[int, str, str]:
    return (
        STATUS_SORT_PRIORITY[lesson.lesson_status],
        lesson.team_id,
        lesson.category_id,
    )


def _validate_lesson(lesson: StrategyTeamLearningFeedbackV3TeamLesson) -> None:
    expected_delta = _quantize_ratio(
        lesson.average_resolved_outcome - lesson.average_recommended_probability,
    )
    if lesson.calibration_delta != expected_delta:
        raise ValueError("calibration_delta must match averages")
    if lesson.lesson_status not in STATUSES:
        raise ValueError("lesson_status must be valid")
    if lesson.reason_codes == ("strategy_team_learning_feedback_v3_passed",) and (
        lesson.source_failure_tags or lesson.playbook_update_suggestions
    ):
        raise ValueError("passed lessons must not carry failure tags or suggestions")


def _validate_report(report: StrategyTeamLearningFeedbackV3Report) -> None:
    if report.source_recommendation_count != sum(
        (lesson.resolved_recommendation_count for lesson in report.team_lessons),
        ZERO_COUNT,
    ):
        raise ValueError("source_recommendation_count must match team_lessons")
    if report.team_lesson_count != _count(len(report.team_lessons)):
        raise ValueError("team_lesson_count must match team_lessons")
    if report.pass_count != _status_count(report.team_lessons, "pass"):
        raise ValueError("pass_count must match team_lessons")
    if report.watch_count != _status_count(report.team_lessons, "watch"):
        raise ValueError("watch_count must match team_lessons")
    if report.blocked_count != _status_count(report.team_lessons, "blocked"):
        raise ValueError("blocked_count must match team_lessons")
    if report.report_status != _report_status(report.team_lessons):
        raise ValueError("report_status must match team_lessons")
    if report.reason_codes != _report_reason_codes(report.team_lessons):
        raise ValueError("reason_codes must match team_lessons")
    _validate_source_failure_tag_counts(report)
    if report.playbook_update_suggestions != _playbook_update_suggestions(
        report.team_lessons,
    ):
        raise ValueError("playbook_update_suggestions must match team_lessons")


def _validate_source_failure_tag_counts(
    report: StrategyTeamLearningFeedbackV3Report,
) -> None:
    lesson_tags = {
        tag for lesson in report.team_lessons for tag in lesson.source_failure_tags
    }
    count_tags = {item.source_failure_tag for item in report.source_failure_tag_counts}
    if lesson_tags != count_tags:
        raise ValueError("source_failure_tag_counts must match team_lessons")
    for item in report.source_failure_tag_counts:
        if item.count > report.source_recommendation_count:
            raise ValueError("source_failure_tag_counts cannot exceed source recommendations")


def _normalize_lessons(
    value: object,
) -> tuple[StrategyTeamLearningFeedbackV3TeamLesson, ...]:
    if type(value) is not tuple:
        raise ValueError("team_lessons must be a tuple")
    lessons = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for lesson in lessons:
        if type(lesson) is not StrategyTeamLearningFeedbackV3TeamLesson:
            raise ValueError(
                "team_lessons must contain StrategyTeamLearningFeedbackV3TeamLesson values",
            )
        require_paper_only_flags("StrategyTeamLearningFeedbackV3TeamLesson", lesson)
        key = (lesson.team_id, lesson.category_id, lesson.playbook_section)
        if key in seen_keys:
            raise ValueError("team_lessons values must be unique")
        seen_keys.add(key)
    if lessons != tuple(sorted(lessons, key=_lesson_sort_key)):
        raise ValueError("team_lessons must be deterministically sorted")
    return lessons


def _normalize_tag_counts(
    value: object,
) -> tuple[StrategyTeamLearningFeedbackV3SourceFailureTagCount, ...]:
    if type(value) is not tuple:
        raise ValueError("source_failure_tag_counts must be a tuple")
    items = tuple(value)
    seen_tags: set[str] = set()
    for item in items:
        if type(item) is not StrategyTeamLearningFeedbackV3SourceFailureTagCount:
            raise ValueError(
                "source_failure_tag_counts must contain StrategyTeamLearningFeedbackV3SourceFailureTagCount values",
            )
        require_paper_only_flags("StrategyTeamLearningFeedbackV3SourceFailureTagCount", item)
        if item.source_failure_tag in seen_tags:
            raise ValueError("source_failure_tag_counts values must be unique")
        seen_tags.add(item.source_failure_tag)
    if items != tuple(sorted(items, key=lambda item: (-item.count, item.source_failure_tag))):
        raise ValueError("source_failure_tag_counts must be deterministically sorted")
    return items


def _normalize_suggestions(
    value: object,
) -> tuple[StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion, ...]:
    if type(value) is not tuple:
        raise ValueError("playbook_update_suggestions must be a tuple")
    items = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion:
            raise ValueError(
                "playbook_update_suggestions must contain StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion values",
            )
        require_paper_only_flags("StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion", item)
        key = (item.playbook_section, item.suggestion)
        if key in seen_keys:
            raise ValueError("playbook_update_suggestions values must be unique")
        seen_keys.add(key)
    if items != tuple(sorted(items, key=lambda item: (item.playbook_section, item.suggestion))):
        raise ValueError("playbook_update_suggestions must be deterministically sorted")
    return items


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed_codes)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} values must be unique")
    expected = tuple(code for code in allowed_codes if code in codes)
    if codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return codes


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    items = tuple(value)
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} values must be unique")
    return tuple(sorted(items))


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be a known value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < -ONE_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, ZERO_RATIO) / _count(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)
