"""Pure readonly research-team feedback loop report reducer."""

from __future__ import annotations

from dataclasses import dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any, Iterable


DEFAULT_RESEARCH_TEAM_FEEDBACK_LOOP_CONFIG_VERSION = (
    "research-team-feedback-loop-report-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COUNT_ONE = Decimal("1.000000")
STATUSES = ("pass", "watch", "block")
POSTMORTEM_READINESS_STATUSES = ("pass", "watch", "block")
CALIBRATION_WATCH_THRESHOLD = Decimal("0.100000")
CALIBRATION_BLOCK_THRESHOLD = Decimal("0.250000")
QUALITY_WATCH_FLOOR = Decimal("0.700000")
QUALITY_BLOCK_FLOOR = Decimal("0.500000")
SAFE_LABEL_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.:-",
)
SAFE_REASON_CHARACTERS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")

HARD_FLAGS = (
    "evidence_quality_below_floor",
    "learning_value_below_floor",
    "postmortem_quality_below_floor",
    "resolution_quality_below_floor",
    "severe_calibration_error",
)
OUTCOME_LEARNING_ACTIONS = (
    "capture_verified_learning",
    "hold_extreme_calibration_learning",
    "hold_low_quality_learning",
    "queue_probability_review",
    "queue_quality_review",
)
MEMORY_UPDATE_ACTIONS = (
    "quarantine_low_quality_memory",
    "quarantine_miscalibrated_memory",
    "reinforce_team_memory",
    "review_probability_memory",
    "review_quality_memory",
)
REASON_CODES = (
    "calibration_review_needed",
    "evidence_quality_below_floor",
    "evidence_quality_review_needed",
    "feedback_loop_passed",
    "learning_value_below_floor",
    "learning_value_review_needed",
    "postmortem_quality_below_floor",
    "postmortem_quality_review_needed",
    "resolution_quality_below_floor",
    "resolution_quality_review_needed",
    "severe_calibration_error",
)
PUBLIC_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "report_status",
        "fact_count",
        "pass_count",
        "watch_count",
        "block_count",
        "postmortem_readiness",
        "status_counts",
        "reason_counts",
        "hard_flag_counts",
        "outcome_learning_queue",
        "memory_update_strategy",
        "team_performance_summary",
        "improvement_suggestions",
        "average_calibration_error",
        "average_postmortem_quality_score",
        "average_evidence_quality_score",
        "average_resolution_quality_score",
        "average_learning_value_score",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
NUMERIC_PAYLOAD_FIELDS = frozenset(
    (
        "fact_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_calibration_error",
        "average_postmortem_quality_score",
        "average_evidence_quality_score",
        "average_resolution_quality_score",
        "average_learning_value_score",
        "ready_count",
        "count",
        "feedback_count",
        "supporting_feedback_count",
    ),
)
UNSAFE_FIELD_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "candidate_reference",
        "market_id",
        "marketid",
        "market_slug",
        "marketslug",
        "slug",
        "question",
        "source_ref",
        "source_reference",
        "source_url",
        "source_text",
        "sourcetext",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "account",
        "balance",
        "private",
        "secret",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ),
)
UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "candidate",
        "marketid",
        "market_id",
        "market-slug",
        "market_slug",
        "market-",
        "market_",
        "slug",
        "question",
        "source_ref",
        "source-ref",
        "source_reference",
        "source-reference",
        "source_url",
        "source-url",
        "source_text",
        "source-text",
        "sourceurl",
        "sourcetext",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "account",
        "private",
        "secret",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_FEEDBACK_LOOP_CONFIG_VERSION",
    "ResearchTeamFeedbackLoopConfig",
    "ResearchTeamFeedbackLoopFact",
    "ResearchTeamFeedbackLoopImprovementSuggestion",
    "ResearchTeamFeedbackLoopReport",
    "ResearchTeamFeedbackLoopRow",
    "ResearchTeamFeedbackLoopTeamPerformanceSummary",
    "build_research_team_feedback_loop_report",
    "research_team_feedback_loop_report_payload",
)


@dataclass(frozen=True)
class ResearchTeamFeedbackLoopConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_FEEDBACK_LOOP_CONFIG_VERSION
    calibration_watch_threshold: Decimal = CALIBRATION_WATCH_THRESHOLD
    calibration_block_threshold: Decimal = CALIBRATION_BLOCK_THRESHOLD
    quality_watch_floor: Decimal = QUALITY_WATCH_FLOOR
    quality_block_floor: Decimal = QUALITY_BLOCK_FLOOR
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamFeedbackLoopConfig:
            raise TypeError("ResearchTeamFeedbackLoopConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchTeamFeedbackLoopConfig)
        object.__setattr__(
            self,
            "config_version",
            _safe_label("config_version", self.config_version),
        )
        for field_name in (
            "calibration_watch_threshold",
            "calibration_block_threshold",
            "quality_watch_floor",
            "quality_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        if self.calibration_block_threshold < self.calibration_watch_threshold:
            raise ValueError("calibration_block_threshold must not be below watch")
        if self.quality_block_floor > self.quality_watch_floor:
            raise ValueError("quality_block_floor must not exceed watch")
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamFeedbackLoopFact:
    team_id: str
    feedback_reference: str
    resolved_at: datetime
    forecast_probability: Decimal
    resolved_outcome_probability: Decimal
    postmortem_quality_score: Decimal
    evidence_quality_score: Decimal
    resolution_quality_score: Decimal
    learning_value_score: Decimal
    improvement_themes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamFeedbackLoopFact:
            raise TypeError("ResearchTeamFeedbackLoopFact does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("fact", self, ResearchTeamFeedbackLoopFact)
        object.__setattr__(self, "team_id", _safe_label("team_id", self.team_id))
        object.__setattr__(
            self,
            "feedback_reference",
            _safe_redacted_reference("feedback_reference", self.feedback_reference),
        )
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for field_name in (
            "forecast_probability",
            "resolved_outcome_probability",
            "postmortem_quality_score",
            "evidence_quality_score",
            "resolution_quality_score",
            "learning_value_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "improvement_themes",
            _safe_reason_tuple("improvement_themes", self.improvement_themes),
        )
        _require_flags("fact", self)
        _reject_unsafe_surface("fact", self)


@dataclass(frozen=True)
class ResearchTeamFeedbackLoopRow:
    team_id: str
    feedback_reference: str
    resolved_at: datetime
    forecast_probability: Decimal
    resolved_outcome_probability: Decimal
    postmortem_quality_score: Decimal
    evidence_quality_score: Decimal
    resolution_quality_score: Decimal
    learning_value_score: Decimal
    calibration_error: Decimal
    status: str
    postmortem_readiness_status: str
    outcome_learning_action: str
    memory_update_action: str
    improvement_themes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    hard_flags: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamFeedbackLoopRow:
            raise TypeError("ResearchTeamFeedbackLoopRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchTeamFeedbackLoopRow)
        object.__setattr__(self, "team_id", _safe_label("team_id", self.team_id))
        object.__setattr__(
            self,
            "feedback_reference",
            _safe_redacted_reference("feedback_reference", self.feedback_reference),
        )
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for field_name in (
            "forecast_probability",
            "resolved_outcome_probability",
            "postmortem_quality_score",
            "evidence_quality_score",
            "resolution_quality_score",
            "learning_value_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error",
            _decimal_between_zero_and_one("calibration_error", self.calibration_error),
        )
        object.__setattr__(self, "status", _require_member("status", self.status, STATUSES))
        object.__setattr__(
            self,
            "postmortem_readiness_status",
            _require_member(
                "postmortem_readiness_status",
                self.postmortem_readiness_status,
                POSTMORTEM_READINESS_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "outcome_learning_action",
            _require_member(
                "outcome_learning_action",
                self.outcome_learning_action,
                OUTCOME_LEARNING_ACTIONS,
            ),
        )
        object.__setattr__(
            self,
            "memory_update_action",
            _require_member(
                "memory_update_action",
                self.memory_update_action,
                MEMORY_UPDATE_ACTIONS,
            ),
        )
        object.__setattr__(
            self,
            "improvement_themes",
            _safe_reason_tuple("improvement_themes", self.improvement_themes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _safe_member_tuple("reason_codes", self.reason_codes, REASON_CODES),
        )
        object.__setattr__(
            self,
            "hard_flags",
            _safe_member_tuple("hard_flags", self.hard_flags, HARD_FLAGS),
        )
        _require_flags("row", self)
        _validate_row(self)
        _reject_unsafe_surface("row", self)


@dataclass(frozen=True)
class ResearchTeamFeedbackLoopTeamPerformanceSummary:
    team_id: str
    feedback_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_calibration_error: Decimal
    average_postmortem_quality_score: Decimal
    average_evidence_quality_score: Decimal
    average_resolution_quality_score: Decimal
    team_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", _safe_label("team_id", self.team_id))
        for field_name in ("feedback_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_error",
            "average_postmortem_quality_score",
            "average_evidence_quality_score",
            "average_resolution_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal_between_zero_and_one(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_status",
            _require_member("team_status", self.team_status, STATUSES),
        )
        _require_flags("team_performance_summary", self)
        _reject_unsafe_surface("team_performance_summary", self)


@dataclass(frozen=True)
class ResearchTeamFeedbackLoopImprovementSuggestion:
    improvement_theme: str
    suggestion: str
    supporting_feedback_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "improvement_theme",
            _safe_reason("improvement_theme", self.improvement_theme),
        )
        object.__setattr__(self, "suggestion", _safe_reason("suggestion", self.suggestion))
        object.__setattr__(
            self,
            "supporting_feedback_count",
            _nonnegative_integral_decimal(
                "supporting_feedback_count",
                self.supporting_feedback_count,
            ),
        )
        if self.supporting_feedback_count <= ZERO:
            raise ValueError("supporting_feedback_count must be positive")
        _require_flags("improvement_suggestion", self)
        _reject_unsafe_surface("improvement_suggestion", self)


@dataclass(frozen=True)
class ResearchTeamFeedbackLoopReport:
    generated_at: datetime
    config_version: str
    rows: tuple[ResearchTeamFeedbackLoopRow, ...]
    fact_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    postmortem_ready_count: Decimal
    learning_queue_count: Decimal
    report_status: str
    reason_counts: tuple[tuple[str, Decimal], ...]
    team_performance_summary: tuple[ResearchTeamFeedbackLoopTeamPerformanceSummary, ...]
    improvement_suggestions: tuple[ResearchTeamFeedbackLoopImprovementSuggestion, ...]
    payload: dict[str, Any] = field(compare=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamFeedbackLoopReport:
            raise TypeError("ResearchTeamFeedbackLoopReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchTeamFeedbackLoopReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _safe_label("config_version", self.config_version),
        )
        object.__setattr__(self, "rows", _row_tuple("rows", self.rows))
        for field_name in (
            "fact_count",
            "pass_count",
            "watch_count",
            "block_count",
            "postmortem_ready_count",
            "learning_queue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "report_status",
            _require_member("report_status", self.report_status, STATUSES),
        )
        object.__setattr__(
            self,
            "reason_counts",
            _reason_count_tuple("reason_counts", self.reason_counts),
        )
        object.__setattr__(
            self,
            "team_performance_summary",
            _team_summary_tuple("team_performance_summary", self.team_performance_summary),
        )
        object.__setattr__(
            self,
            "improvement_suggestions",
            _suggestion_tuple("improvement_suggestions", self.improvement_suggestions),
        )
        _require_flags("report", self)
        _validate_report(self)
        if self.payload != _report_payload(self):
            raise ValueError("payload must match report fields")
        _validate_public_payload("payload", self.payload)


def build_research_team_feedback_loop_report(
    facts: Iterable[ResearchTeamFeedbackLoopFact],
    *,
    config: ResearchTeamFeedbackLoopConfig,
    generated_at: datetime,
) -> ResearchTeamFeedbackLoopReport:
    if type(config) is not ResearchTeamFeedbackLoopConfig:
        raise ValueError("config must be a ResearchTeamFeedbackLoopConfig")
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = []
    for fact in facts:
        _require_exact_type("facts", fact, ResearchTeamFeedbackLoopFact)
        _require_flags("fact", fact)
        if fact.resolved_at > generated_at_utc:
            raise ValueError("resolved_at must not be after generated_at")
        rows.append(_row_from_fact(fact, config=config))
    sorted_rows = tuple(
        sorted(rows, key=lambda row: (row.team_id, row.feedback_reference, row.resolved_at)),
    )
    report_status = _report_status(sorted_rows)
    reason_counts = _reason_counts(sorted_rows)
    team_summary = _team_performance_summary(sorted_rows)
    suggestions = _improvement_suggestions(sorted_rows)
    payload = _report_payload_from_parts(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=sorted_rows,
        report_status=report_status,
        reason_counts=reason_counts,
        team_performance_summary=team_summary,
        improvement_suggestions=suggestions,
    )
    return ResearchTeamFeedbackLoopReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=sorted_rows,
        fact_count=_decimal_count(len(sorted_rows)),
        pass_count=_status_count(sorted_rows, "pass"),
        watch_count=_status_count(sorted_rows, "watch"),
        block_count=_status_count(sorted_rows, "block"),
        postmortem_ready_count=_postmortem_readiness_count(sorted_rows, "pass"),
        learning_queue_count=_learning_queue_count(sorted_rows),
        report_status=report_status,
        reason_counts=reason_counts,
        team_performance_summary=team_summary,
        improvement_suggestions=suggestions,
        payload=payload,
    )


def research_team_feedback_loop_report_payload(
    report: ResearchTeamFeedbackLoopReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamFeedbackLoopReport:
        _require_flags("report", report)
        _reject_unsafe_surface("report", report)
        payload = report.payload
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a ResearchTeamFeedbackLoopReport")
    _require_flags("payload", _DictFlags(payload))
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload("payload", ready)
    return ready


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_fact(
    fact: ResearchTeamFeedbackLoopFact,
    *,
    config: ResearchTeamFeedbackLoopConfig,
) -> ResearchTeamFeedbackLoopRow:
    calibration_error = _q(abs(fact.forecast_probability - fact.resolved_outcome_probability))
    hard_flags = _hard_flags(fact=fact, calibration_error=calibration_error, config=config)
    status = _row_status(fact=fact, calibration_error=calibration_error, hard_flags=hard_flags, config=config)
    reason_codes = _row_reason_codes(fact=fact, calibration_error=calibration_error, hard_flags=hard_flags, config=config)
    postmortem_status = _postmortem_readiness_status(fact=fact, hard_flags=hard_flags, config=config)
    return ResearchTeamFeedbackLoopRow(
        team_id=fact.team_id,
        feedback_reference=fact.feedback_reference,
        resolved_at=fact.resolved_at,
        forecast_probability=fact.forecast_probability,
        resolved_outcome_probability=fact.resolved_outcome_probability,
        postmortem_quality_score=fact.postmortem_quality_score,
        evidence_quality_score=fact.evidence_quality_score,
        resolution_quality_score=fact.resolution_quality_score,
        learning_value_score=fact.learning_value_score,
        calibration_error=calibration_error,
        status=status,
        postmortem_readiness_status=postmortem_status,
        outcome_learning_action=_outcome_learning_action(status=status, hard_flags=hard_flags),
        memory_update_action=_memory_update_action(status=status, hard_flags=hard_flags),
        improvement_themes=fact.improvement_themes,
        reason_codes=reason_codes,
        hard_flags=hard_flags,
    )


def _hard_flags(
    *,
    fact: ResearchTeamFeedbackLoopFact,
    calibration_error: Decimal,
    config: ResearchTeamFeedbackLoopConfig,
) -> tuple[str, ...]:
    flags = []
    if calibration_error > config.calibration_block_threshold:
        flags.append("severe_calibration_error")
    if fact.evidence_quality_score < config.quality_block_floor:
        flags.append("evidence_quality_below_floor")
    if fact.learning_value_score < config.quality_block_floor:
        flags.append("learning_value_below_floor")
    if fact.postmortem_quality_score < config.quality_block_floor:
        flags.append("postmortem_quality_below_floor")
    if fact.resolution_quality_score < config.quality_block_floor:
        flags.append("resolution_quality_below_floor")
    return tuple(flag for flag in HARD_FLAGS if flag in flags)


def _row_status(
    *,
    fact: ResearchTeamFeedbackLoopFact,
    calibration_error: Decimal,
    hard_flags: tuple[str, ...],
    config: ResearchTeamFeedbackLoopConfig,
) -> str:
    if hard_flags:
        return "block"
    if calibration_error > config.calibration_watch_threshold:
        return "watch"
    if fact.postmortem_quality_score < config.quality_watch_floor:
        return "watch"
    if fact.evidence_quality_score < config.quality_watch_floor:
        return "watch"
    if fact.resolution_quality_score < config.quality_watch_floor:
        return "watch"
    if fact.learning_value_score < config.quality_watch_floor:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    fact: ResearchTeamFeedbackLoopFact,
    calibration_error: Decimal,
    hard_flags: tuple[str, ...],
    config: ResearchTeamFeedbackLoopConfig,
) -> tuple[str, ...]:
    codes = list(hard_flags)
    if "severe_calibration_error" not in hard_flags and calibration_error > config.calibration_watch_threshold:
        codes.append("calibration_review_needed")
    if (
        "postmortem_quality_below_floor" not in hard_flags
        and fact.postmortem_quality_score < config.quality_watch_floor
    ):
        codes.append("postmortem_quality_review_needed")
    if (
        "evidence_quality_below_floor" not in hard_flags
        and fact.evidence_quality_score < config.quality_watch_floor
    ):
        codes.append("evidence_quality_review_needed")
    if (
        "resolution_quality_below_floor" not in hard_flags
        and fact.resolution_quality_score < config.quality_watch_floor
    ):
        codes.append("resolution_quality_review_needed")
    if (
        "learning_value_below_floor" not in hard_flags
        and fact.learning_value_score < config.quality_watch_floor
    ):
        codes.append("learning_value_review_needed")
    if not codes:
        codes.append("feedback_loop_passed")
    return tuple(code for code in REASON_CODES if code in codes)


def _postmortem_readiness_status(
    *,
    fact: ResearchTeamFeedbackLoopFact,
    hard_flags: tuple[str, ...],
    config: ResearchTeamFeedbackLoopConfig,
) -> str:
    if hard_flags:
        return "block"
    if fact.postmortem_quality_score < config.quality_watch_floor:
        return "watch"
    if fact.evidence_quality_score < config.quality_watch_floor:
        return "watch"
    if fact.resolution_quality_score < config.quality_watch_floor:
        return "watch"
    if fact.learning_value_score < config.quality_watch_floor:
        return "watch"
    return "pass"


def _outcome_learning_action(*, status: str, hard_flags: tuple[str, ...]) -> str:
    if status == "pass":
        return "capture_verified_learning"
    if _has_quality_hard_flag(hard_flags):
        return "hold_low_quality_learning"
    if "severe_calibration_error" in hard_flags:
        return "hold_extreme_calibration_learning"
    if status == "watch":
        return "queue_probability_review"
    return "queue_quality_review"


def _memory_update_action(*, status: str, hard_flags: tuple[str, ...]) -> str:
    if _has_quality_hard_flag(hard_flags):
        return "quarantine_low_quality_memory"
    if "severe_calibration_error" in hard_flags:
        return "quarantine_miscalibrated_memory"
    if status == "watch":
        return "review_probability_memory"
    return "reinforce_team_memory"


def _has_quality_hard_flag(hard_flags: tuple[str, ...]) -> bool:
    return any(flag.endswith("_quality_below_floor") for flag in hard_flags) or (
        "learning_value_below_floor" in hard_flags
    )


def _report_status(rows: tuple[ResearchTeamFeedbackLoopRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_counts(rows: tuple[ResearchTeamFeedbackLoopRow, ...]) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + COUNT_ONE
    return tuple((reason_code, counts[reason_code]) for reason_code in sorted(counts))


def _status_count(rows: tuple[ResearchTeamFeedbackLoopRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(row.status == status for row in rows))


def _postmortem_readiness_count(rows: tuple[ResearchTeamFeedbackLoopRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(row.postmortem_readiness_status == status for row in rows))


def _learning_queue_count(rows: tuple[ResearchTeamFeedbackLoopRow, ...]) -> Decimal:
    return _decimal_count(sum(row.outcome_learning_action != "hold_low_quality_learning" for row in rows))


def _team_performance_summary(
    rows: tuple[ResearchTeamFeedbackLoopRow, ...],
) -> tuple[ResearchTeamFeedbackLoopTeamPerformanceSummary, ...]:
    team_ids = tuple(sorted({row.team_id for row in rows}))
    summaries = []
    for team_id in team_ids:
        scoped_rows = tuple(row for row in rows if row.team_id == team_id)
        summaries.append(
            ResearchTeamFeedbackLoopTeamPerformanceSummary(
                team_id=team_id,
                feedback_count=_decimal_count(len(scoped_rows)),
                pass_count=_status_count(scoped_rows, "pass"),
                watch_count=_status_count(scoped_rows, "watch"),
                block_count=_status_count(scoped_rows, "block"),
                average_calibration_error=_average(
                    tuple(row.calibration_error for row in scoped_rows),
                ),
                average_postmortem_quality_score=_average(
                    tuple(row.postmortem_quality_score for row in scoped_rows),
                ),
                average_evidence_quality_score=_average(
                    tuple(row.evidence_quality_score for row in scoped_rows),
                ),
                average_resolution_quality_score=_average(
                    tuple(row.resolution_quality_score for row in scoped_rows),
                ),
                team_status=_report_status(scoped_rows),
            ),
        )
    return tuple(summaries)


def _improvement_suggestions(
    rows: tuple[ResearchTeamFeedbackLoopRow, ...],
) -> tuple[ResearchTeamFeedbackLoopImprovementSuggestion, ...]:
    counts: dict[str, Decimal] = {}
    statuses: dict[str, set[str]] = {}
    for row in rows:
        for theme in row.improvement_themes:
            counts[theme] = counts.get(theme, ZERO) + COUNT_ONE
            statuses.setdefault(theme, set()).add(row.status)
    return tuple(
        ResearchTeamFeedbackLoopImprovementSuggestion(
            improvement_theme=theme,
            suggestion=_suggestion_for_theme(theme=theme, statuses=statuses[theme]),
            supporting_feedback_count=counts[theme],
        )
        for theme in sorted(counts)
    )


def _suggestion_for_theme(*, theme: str, statuses: set[str]) -> str:
    if "block" in statuses:
        prefix = "rebuild"
    elif "watch" in statuses:
        prefix = "tighten"
    else:
        prefix = "preserve_high_quality"
    return _safe_reason("suggestion", f"{prefix}_{theme}_loop")


def _report_payload(report: ResearchTeamFeedbackLoopReport) -> dict[str, Any]:
    return _report_payload_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        rows=report.rows,
        report_status=report.report_status,
        reason_counts=report.reason_counts,
        team_performance_summary=report.team_performance_summary,
        improvement_suggestions=report.improvement_suggestions,
    )


def _report_payload_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchTeamFeedbackLoopRow, ...],
    report_status: str,
    reason_counts: tuple[tuple[str, Decimal], ...],
    team_performance_summary: tuple[ResearchTeamFeedbackLoopTeamPerformanceSummary, ...],
    improvement_suggestions: tuple[ResearchTeamFeedbackLoopImprovementSuggestion, ...],
) -> dict[str, Any]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "report_status": report_status,
        "fact_count": _json_ready(_decimal_count(len(rows))),
        "pass_count": _json_ready(_status_count(rows, "pass")),
        "watch_count": _json_ready(_status_count(rows, "watch")),
        "block_count": _json_ready(_status_count(rows, "block")),
        "postmortem_readiness": {
            "ready_count": _json_ready(_postmortem_readiness_count(rows, "pass")),
            "watch_count": _json_ready(_postmortem_readiness_count(rows, "watch")),
            "block_count": _json_ready(_postmortem_readiness_count(rows, "block")),
        },
        "status_counts": [
            {"status": status, "count": _json_ready(count)}
            for status, count in _status_counts(rows)
        ],
        "reason_counts": [
            {"reason_code": reason_code, "count": _json_ready(count)}
            for reason_code, count in reason_counts
        ],
        "hard_flag_counts": [
            {"hard_flag": hard_flag, "count": _json_ready(count)}
            for hard_flag, count in _hard_flag_counts(rows)
        ],
        "outcome_learning_queue": [
            {"outcome_learning_action": action, "count": _json_ready(count)}
            for action, count in _action_counts(
                tuple(row.outcome_learning_action for row in rows),
            )
        ],
        "memory_update_strategy": [
            {"memory_update_action": action, "count": _json_ready(count)}
            for action, count in _action_counts(tuple(row.memory_update_action for row in rows))
        ],
        "team_performance_summary": [
            _team_summary_payload(summary) for summary in team_performance_summary
        ],
        "improvement_suggestions": [
            _suggestion_payload(suggestion) for suggestion in improvement_suggestions
        ],
        "average_calibration_error": _json_ready(
            _average(tuple(row.calibration_error for row in rows)),
        ),
        "average_postmortem_quality_score": _json_ready(
            _average(tuple(row.postmortem_quality_score for row in rows)),
        ),
        "average_evidence_quality_score": _json_ready(
            _average(tuple(row.evidence_quality_score for row in rows)),
        ),
        "average_resolution_quality_score": _json_ready(
            _average(tuple(row.resolution_quality_score for row in rows)),
        ),
        "average_learning_value_score": _json_ready(
            _average(tuple(row.learning_value_score for row in rows)),
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _team_summary_payload(
    summary: ResearchTeamFeedbackLoopTeamPerformanceSummary,
) -> dict[str, Any]:
    return {
        "team_id": summary.team_id,
        "feedback_count": _json_ready(summary.feedback_count),
        "pass_count": _json_ready(summary.pass_count),
        "watch_count": _json_ready(summary.watch_count),
        "block_count": _json_ready(summary.block_count),
        "average_calibration_error": _json_ready(summary.average_calibration_error),
        "average_postmortem_quality_score": _json_ready(
            summary.average_postmortem_quality_score,
        ),
        "average_evidence_quality_score": _json_ready(summary.average_evidence_quality_score),
        "average_resolution_quality_score": _json_ready(
            summary.average_resolution_quality_score,
        ),
        "team_status": summary.team_status,
    }


def _suggestion_payload(
    suggestion: ResearchTeamFeedbackLoopImprovementSuggestion,
) -> dict[str, Any]:
    return {
        "improvement_theme": suggestion.improvement_theme,
        "suggestion": suggestion.suggestion,
        "supporting_feedback_count": _json_ready(suggestion.supporting_feedback_count),
    }


def _status_counts(rows: tuple[ResearchTeamFeedbackLoopRow, ...]) -> tuple[tuple[str, Decimal], ...]:
    counts = []
    for status in STATUSES:
        count = _status_count(rows, status)
        if count > ZERO:
            counts.append((status, count))
    return tuple(counts)


def _hard_flag_counts(rows: tuple[ResearchTeamFeedbackLoopRow, ...]) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for hard_flag in row.hard_flags:
            counts[hard_flag] = counts.get(hard_flag, ZERO) + COUNT_ONE
    return tuple((hard_flag, counts[hard_flag]) for hard_flag in sorted(counts))


def _action_counts(values: tuple[str, ...]) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for value in values:
        counts[value] = counts.get(value, ZERO) + COUNT_ONE
    return tuple((value, counts[value]) for value in sorted(counts))


def _validate_row(row: ResearchTeamFeedbackLoopRow) -> None:
    expected_error = _q(abs(row.forecast_probability - row.resolved_outcome_probability))
    if row.calibration_error != expected_error:
        raise ValueError("calibration_error must match forecast and outcome")
    if row.hard_flags and row.status != "block":
        raise ValueError("hard_flags require block status")
    if row.status == "pass" and row.reason_codes != ("feedback_loop_passed",):
        raise ValueError("pass rows must use passed reason")
    if row.status != "pass" and row.reason_codes == ("feedback_loop_passed",):
        raise ValueError("non-pass rows must not use passed reason")


def _validate_report(report: ResearchTeamFeedbackLoopReport) -> None:
    if report.rows != tuple(
        sorted(report.rows, key=lambda row: (row.team_id, row.feedback_reference, row.resolved_at)),
    ):
        raise ValueError("rows must be deterministically sorted")
    if report.fact_count != _decimal_count(len(report.rows)):
        raise ValueError("fact_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.postmortem_ready_count != _postmortem_readiness_count(report.rows, "pass"):
        raise ValueError("postmortem_ready_count must match rows")
    if report.learning_queue_count != _learning_queue_count(report.rows):
        raise ValueError("learning_queue_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_counts != _reason_counts(report.rows):
        raise ValueError("reason_counts must match rows")
    if report.team_performance_summary != _team_performance_summary(report.rows):
        raise ValueError("team_performance_summary must match rows")
    if report.improvement_suggestions != _improvement_suggestions(report.rows):
        raise ValueError("improvement_suggestions must match rows")


def _validate_public_payload(label: str, payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a public payload")
    _require_flags(label, _DictFlags(payload))
    _reject_unsafe_surface(label, payload)
    if frozenset(payload) != PUBLIC_PAYLOAD_FIELDS:
        raise ValueError(f"{label} fields must match public aggregate schema")
    _validate_public_payload_values(label, payload)


def _validate_public_payload_values(label: str, payload: dict[str, Any]) -> None:
    _require_member(f"{label}.report_status", payload["report_status"], STATUSES)
    for field_name in (
        "fact_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_calibration_error",
        "average_postmortem_quality_score",
        "average_evidence_quality_score",
        "average_resolution_quality_score",
        "average_learning_value_score",
    ):
        _payload_decimal(field_name, payload[field_name])
    for readiness_field in ("ready_count", "watch_count", "block_count"):
        _payload_decimal(readiness_field, payload["postmortem_readiness"][readiness_field])
    _validate_count_items(label, payload["status_counts"], "status", STATUSES)
    _validate_count_items(label, payload["reason_counts"], "reason_code", REASON_CODES)
    _validate_count_items(label, payload["hard_flag_counts"], "hard_flag", HARD_FLAGS)
    _validate_count_items(
        label,
        payload["outcome_learning_queue"],
        "outcome_learning_action",
        OUTCOME_LEARNING_ACTIONS,
    )
    _validate_count_items(
        label,
        payload["memory_update_strategy"],
        "memory_update_action",
        MEMORY_UPDATE_ACTIONS,
    )
    if type(payload["team_performance_summary"]) is not list:
        raise ValueError(f"{label}.team_performance_summary must be a list")
    for summary in payload["team_performance_summary"]:
        _validate_public_team_summary(label, summary)
    if type(payload["improvement_suggestions"]) is not list:
        raise ValueError(f"{label}.improvement_suggestions must be a list")
    for suggestion in payload["improvement_suggestions"]:
        _validate_public_suggestion(label, suggestion)


def _validate_count_items(
    label: str,
    value: object,
    key_field: str,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{label}.{key_field} counts must be a list")
    previous_key = ""
    for item in value:
        if type(item) is not dict or frozenset(item) != frozenset((key_field, "count")):
            raise ValueError(f"{label}.{key_field} counts must use public schema")
        key = _require_member(key_field, item[key_field], allowed_values)
        if key <= previous_key:
            raise ValueError(f"{label}.{key_field} counts must be deterministically sorted")
        previous_key = key
        _payload_decimal("count", item["count"])


def _validate_public_team_summary(label: str, value: object) -> None:
    fields = frozenset(
        (
            "team_id",
            "feedback_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_calibration_error",
            "average_postmortem_quality_score",
            "average_evidence_quality_score",
            "average_resolution_quality_score",
            "team_status",
        ),
    )
    if type(value) is not dict or frozenset(value) != fields:
        raise ValueError(f"{label}.team_performance_summary must use public schema")
    _safe_label("team_id", value["team_id"])
    _require_member("team_status", value["team_status"], STATUSES)
    for field_name in fields - frozenset(("team_id", "team_status")):
        _payload_decimal(field_name, value[field_name])
    _reject_unsafe_surface(label, value)


def _validate_public_suggestion(label: str, value: object) -> None:
    fields = frozenset(("improvement_theme", "suggestion", "supporting_feedback_count"))
    if type(value) is not dict or frozenset(value) != fields:
        raise ValueError(f"{label}.improvement_suggestions must use public schema")
    _safe_reason("improvement_theme", value["improvement_theme"])
    _safe_reason("suggestion", value["suggestion"])
    _payload_decimal("supporting_feedback_count", value["supporting_feedback_count"])
    _reject_unsafe_surface(label, value)


def _row_tuple(field_name: str, value: object) -> tuple[ResearchTeamFeedbackLoopRow, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    rows = tuple(value)
    for row in rows:
        _require_exact_type(field_name, row, ResearchTeamFeedbackLoopRow)
        _require_flags("row", row)
    return rows


def _team_summary_tuple(
    field_name: str,
    value: object,
) -> tuple[ResearchTeamFeedbackLoopTeamPerformanceSummary, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    summaries = tuple(value)
    for summary in summaries:
        _require_exact_type(
            field_name,
            summary,
            ResearchTeamFeedbackLoopTeamPerformanceSummary,
        )
        _require_flags("team_performance_summary", summary)
    if summaries != tuple(sorted(summaries, key=lambda summary: summary.team_id)):
        raise ValueError(f"{field_name} must be deterministically sorted")
    return summaries


def _suggestion_tuple(
    field_name: str,
    value: object,
) -> tuple[ResearchTeamFeedbackLoopImprovementSuggestion, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    suggestions = tuple(value)
    for suggestion in suggestions:
        _require_exact_type(
            field_name,
            suggestion,
            ResearchTeamFeedbackLoopImprovementSuggestion,
        )
        _require_flags("improvement_suggestion", suggestion)
    if suggestions != tuple(sorted(suggestions, key=lambda item: item.improvement_theme)):
        raise ValueError(f"{field_name} must be deterministically sorted")
    return suggestions


def _reason_count_tuple(field_name: str, value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    previous_key = ""
    normalized = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError(f"{field_name} items must be key/count tuples")
        key = _require_member(field_name, item[0], REASON_CODES)
        if key <= previous_key:
            raise ValueError(f"{field_name} must be deterministically sorted")
        previous_key = key
        normalized.append((key, _nonnegative_integral_decimal(field_name, item[1])))
    return tuple(normalized)


def _safe_member_tuple(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_member(field_name, item, allowed_values)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} values must be unique")
    expected = tuple(item for item in allowed_values if item in value)
    if value != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return value


def _safe_reason_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    values = tuple(_safe_reason(field_name, item) for item in value)
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} values must be unique")
    return tuple(sorted(values))


def _safe_reason(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if any(character not in SAFE_REASON_CHARACTERS for character in value):
        raise ValueError(f"{field_name} must use safe public characters")
    _reject_unsafe_text(field_name, value)
    return value


def _safe_label(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if any(character not in SAFE_LABEL_CHARACTERS for character in value):
        raise ValueError(f"{field_name} must use safe label characters")
    _reject_unsafe_text(field_name, value)
    return value


def _safe_redacted_reference(field_name: str, value: object) -> str:
    safe_value = _safe_label(field_name, value)
    if not safe_value.endswith("-redacted"):
        raise ValueError(f"{field_name} must be redacted")
    return safe_value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    safe_value = _safe_reason(field_name, value)
    if safe_value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")
    return safe_value


def _require_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _decimal_between_zero_and_one(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _q(decimal_value)


def _nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative integral Decimal")
    return _q(decimal_value)


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, bool) or isinstance(value, int):
        raise ValueError(f"{field_name} must be a Decimal string")
    if type(value) is Decimal:
        return _q(value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(decimal_value)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _q(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    total = ZERO
    for value in values:
        total += value
    return _q(total / _decimal_count(len(values)))


def _q(value: Decimal) -> Decimal:
    return value.quantize(COUNT_ONE, rounding=ROUND_HALF_EVEN)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        raise ValueError("public payload must not expose dataclass internals")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_q(value))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, bool) or type(value) is str:
        return value
    if isinstance(value, int):
        raise ValueError("JSON numeric value must be Decimal")
    if type(value) is dict:
        return _json_dict(value)
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _json_dict(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


def _reject_unsafe_surface(label: str, value: object) -> None:
    for key, item in _iter_items(value):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe public field in {label}: {key}")
        if type(item) is str:
            _reject_unsafe_text(label, item)


def _reject_unsafe_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public text in {label}")


def _iter_items(value: object) -> tuple[tuple[str, object], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        items: list[tuple[str, object]] = []
        for key in getattr(value, "__dataclass_fields__"):
            item = getattr(value, key)
            items.append((key, item))
            items.extend(_iter_items(item))
        return tuple(items)
    if type(value) is dict:
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append((key, item))
            items.extend(_iter_items(item))
        return tuple(items)
    if type(value) in (list, tuple):
        items = []
        for item in value:
            items.extend(_iter_items(item))
        return tuple(items)
    return ()
