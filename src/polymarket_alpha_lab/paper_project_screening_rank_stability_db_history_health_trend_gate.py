"""Pure gate reducer for project screening rank stability health trends."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket_alpha_lab.paper_project_screening_rank_stability_db_history_health_trend import (
    PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport,
)


DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION = (
    "paper-project-screening-rank-stability-db-history-health-trend-gate-v0"
)
HEALTH_STATUSES = ("pass", "watch", "blocked")
SOURCE_HEALTH_PASS_REASON_CODE = (
    "paper_project_screening_rank_stability_db_history_health_passed"
)
NEXT_STEP_BY_STATUS = {
    "pass": (
        "allow_paper_project_screening_rank_stability_db_history_health_trend_review"
    ),
    "watch": (
        "throttle_paper_project_screening_rank_stability_db_history_health_trend_review"
    ),
    "blocked": (
        "block_paper_project_screening_rank_stability_db_history_health_trend_review"
    ),
}
PASS_REASON_CODE = (
    "paper_project_screening_rank_stability_db_history_health_trend_gate_passed"
)
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_paper_project_screening_rank_stability_db_history_health_trend_samples",
        "latest_paper_project_screening_rank_stability_db_history_health_trend_blocked",
        "consecutive_paper_project_screening_rank_stability_db_history_health_trend_blocked_threshold_exceeded",
        "missing_latest_paper_project_screening_rank_stability_db_history_health_trend_timestamp",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "latest_paper_project_screening_rank_stability_db_history_health_trend_watch",
        "consecutive_paper_project_screening_rank_stability_db_history_health_trend_watch_threshold_exceeded",
        "duplicate_paper_project_screening_rank_stability_db_history_health_trend_timestamp_threshold_exceeded",
        "unstable_paper_project_screening_rank_stability_db_history_health_trend_ready_candidates_present",
        "worsening_paper_project_screening_rank_stability_db_history_health_trend_unstable_ready_count",
        "worsening_paper_project_screening_rank_stability_db_history_health_trend_watch_count",
        "worsening_paper_project_screening_rank_stability_db_history_health_trend_blocked_count",
        "repeated_paper_project_screening_rank_stability_db_history_health_trend_reason_threshold_exceeded",
        "stale_paper_project_screening_rank_stability_db_history_health_trend",
    ),
)
GATE_REASON_CODES = BLOCKED_REASON_CODES | WATCH_REASON_CODES | frozenset(
    (PASS_REASON_CODE,),
)

__all__ = (
    "DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION",
    "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig",
    "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount",
    "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReport",
    "build_paper_project_screening_rank_stability_db_history_health_trend_gate_report",
)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig:
    config_version: str = (
        DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_TREND_GATE_CONFIG_VERSION
    )
    min_source_health_report_count: int = 3
    max_consecutive_latest_watch_count: int = 0
    max_consecutive_latest_blocked_count: int = 0
    max_duplicate_generated_at_count: int = 0
    max_latest_source_age_seconds: int = 86_400
    max_latest_unstable_ready_count: int = 0
    max_unstable_ready_count_delta: int = 0
    max_watch_rank_stability_report_count_delta: int = 0
    max_blocked_rank_stability_report_count_delta: int = 0
    max_repeated_reason_code_count: int = 0
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig:
            raise ValueError(
                "config must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_source_health_report_count",
            "max_consecutive_latest_watch_count",
            "max_consecutive_latest_blocked_count",
            "max_duplicate_generated_at_count",
            "max_latest_source_age_seconds",
            "max_latest_unstable_ready_count",
            "max_unstable_ready_count_delta",
            "max_watch_rank_stability_report_count_delta",
            "max_blocked_rank_stability_report_count_delta",
            "max_repeated_reason_code_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if (
            type(self)
            is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount
        ):
            raise ValueError(
                "reason code count must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount,
        ...,
    ]
    source_health_report_count: int
    latest_health_status: str | None
    latest_health_generated_at: datetime | None
    latest_source_age_seconds: int | None
    duplicate_generated_at_count: int
    consecutive_latest_watch_count: int
    consecutive_latest_blocked_count: int
    latest_stable_ready_count: int | None
    latest_unstable_ready_count: int | None
    latest_unstable_ready_count_delta: int | None
    watch_rank_stability_report_count_delta: int | None
    blocked_rank_stability_report_count_delta: int | None
    latest_reason_code_counts: tuple[tuple[str, int], ...]
    repeated_reason_code_counts: tuple[tuple[str, int], ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReport:
            raise TypeError(
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReport:
            raise ValueError(
                "gate report must be exactly "
                "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        object.__setattr__(
            self,
            "latest_health_generated_at",
            _as_optional_utc(
                "latest_health_generated_at",
                self.latest_health_generated_at,
            ),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_health_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_nonnegative_int(
            "source_health_report_count",
            self.source_health_report_count,
        )
        if self.latest_health_status is not None:
            _require_health_status("latest_health_status", self.latest_health_status)
        for field_name in (
            "latest_source_age_seconds",
            "latest_stable_ready_count",
            "latest_unstable_ready_count",
        ):
            _require_optional_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "duplicate_generated_at_count",
            "consecutive_latest_watch_count",
            "consecutive_latest_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "latest_unstable_ready_count_delta",
            "watch_rank_stability_report_count_delta",
            "blocked_rank_stability_report_count_delta",
        ):
            _require_optional_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "latest_reason_code_counts",
            _normalize_count_pairs(
                "latest_reason_code_counts",
                self.latest_reason_code_counts,
            ),
        )
        object.__setattr__(
            self,
            "repeated_reason_code_counts",
            _normalize_count_pairs(
                "repeated_reason_code_counts",
                self.repeated_reason_code_counts,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_gate_report(self)
        _validate_hard_flags("gate report", self)


def build_paper_project_screening_rank_stability_db_history_health_trend_gate_report(
    trend_report: object,
    *,
    config: PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig,
    generated_at: datetime,
) -> PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReport:
    if type(trend_report) is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport:
        raise ValueError(
            "trend_report must be a "
            "PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport",
        )
    if type(config) is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig:
        raise ValueError(
            "config must be a "
            "PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_hard_flags("config", config)
    _validate_hard_flags("trend report", trend_report)

    reason_codes = _gate_reason_codes(trend_report=trend_report, config=config)
    gate_status = _gate_status(reason_codes)
    reason_code_counts = tuple(
        PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount(
            reason_code=reason_code,
            report_count=1,
        )
        for reason_code in reason_codes
    )

    return PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_config_version=trend_report.config_version,
        source_generated_at=trend_report.generated_at,
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[gate_status],
        reason_code_counts=reason_code_counts,
        source_health_report_count=trend_report.source_health_report_count,
        latest_health_status=trend_report.latest_health_status,
        latest_health_generated_at=trend_report.latest_generated_at,
        latest_source_age_seconds=trend_report.latest_source_age_seconds_latest,
        duplicate_generated_at_count=trend_report.duplicate_generated_at_count,
        consecutive_latest_watch_count=trend_report.consecutive_latest_watch_count,
        consecutive_latest_blocked_count=trend_report.consecutive_latest_blocked_count,
        latest_stable_ready_count=trend_report.latest_stable_ready_count_latest,
        latest_unstable_ready_count=trend_report.latest_unstable_ready_count_latest,
        latest_unstable_ready_count_delta=(
            trend_report.latest_unstable_ready_count_delta
        ),
        watch_rank_stability_report_count_delta=(
            trend_report.watch_rank_stability_report_count_delta
        ),
        blocked_rank_stability_report_count_delta=(
            trend_report.blocked_rank_stability_report_count_delta
        ),
        latest_reason_code_counts=trend_report.latest_reason_code_counts,
        repeated_reason_code_counts=trend_report.repeated_reason_code_counts,
        reason_codes=reason_codes,
    )


def _gate_reason_codes(
    *,
    trend_report: PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport,
    config: PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if trend_report.source_health_report_count < config.min_source_health_report_count:
        reason_codes.append(
            "insufficient_paper_project_screening_rank_stability_db_history_health_trend_samples",
        )
    if trend_report.latest_generated_at is None:
        reason_codes.append(
            "missing_latest_paper_project_screening_rank_stability_db_history_health_trend_timestamp",
        )
    if trend_report.latest_health_status == "blocked":
        reason_codes.append(
            "latest_paper_project_screening_rank_stability_db_history_health_trend_blocked",
        )
    if (
        trend_report.consecutive_latest_blocked_count
        > config.max_consecutive_latest_blocked_count
    ):
        reason_codes.append(
            "consecutive_paper_project_screening_rank_stability_db_history_health_trend_blocked_threshold_exceeded",
        )
    if trend_report.latest_health_status == "watch":
        reason_codes.append(
            "latest_paper_project_screening_rank_stability_db_history_health_trend_watch",
        )
    if (
        trend_report.consecutive_latest_watch_count
        > config.max_consecutive_latest_watch_count
    ):
        reason_codes.append(
            "consecutive_paper_project_screening_rank_stability_db_history_health_trend_watch_threshold_exceeded",
        )
    if trend_report.duplicate_generated_at_count > config.max_duplicate_generated_at_count:
        reason_codes.append(
            "duplicate_paper_project_screening_rank_stability_db_history_health_trend_timestamp_threshold_exceeded",
        )
    if (
        trend_report.latest_source_age_seconds_latest is not None
        and trend_report.latest_source_age_seconds_latest
        > config.max_latest_source_age_seconds
    ):
        reason_codes.append(
            "stale_paper_project_screening_rank_stability_db_history_health_trend",
        )
    if (
        trend_report.latest_unstable_ready_count_latest is not None
        and trend_report.latest_unstable_ready_count_latest
        > config.max_latest_unstable_ready_count
    ):
        reason_codes.append(
            "unstable_paper_project_screening_rank_stability_db_history_health_trend_ready_candidates_present",
        )
    if (
        trend_report.latest_unstable_ready_count_delta is not None
        and trend_report.latest_unstable_ready_count_delta
        > config.max_unstable_ready_count_delta
    ):
        reason_codes.append(
            "worsening_paper_project_screening_rank_stability_db_history_health_trend_unstable_ready_count",
        )
    if (
        trend_report.watch_rank_stability_report_count_delta is not None
        and trend_report.watch_rank_stability_report_count_delta
        > config.max_watch_rank_stability_report_count_delta
    ):
        reason_codes.append(
            "worsening_paper_project_screening_rank_stability_db_history_health_trend_watch_count",
        )
    if (
        trend_report.blocked_rank_stability_report_count_delta is not None
        and trend_report.blocked_rank_stability_report_count_delta
        > config.max_blocked_rank_stability_report_count_delta
    ):
        reason_codes.append(
            "worsening_paper_project_screening_rank_stability_db_history_health_trend_blocked_count",
        )
    if any(
        count > config.max_repeated_reason_code_count
        for reason_code, count in trend_report.repeated_reason_code_counts
        if reason_code != SOURCE_HEALTH_PASS_REASON_CODE
    ):
        reason_codes.append(
            "repeated_paper_project_screening_rank_stability_db_history_health_trend_reason_threshold_exceeded",
        )
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(sorted(set(reason_codes)))


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    unknown_reason_codes = tuple(
        reason_code for reason_code in reason_codes if reason_code not in GATE_REASON_CODES
    )
    if unknown_reason_codes:
        raise ValueError("reason_codes must contain known gate reason codes")
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_gate_report(
    report: PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.gate_status]:
        raise ValueError("recommended_next_step must match gate_status")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    if any(row.report_count != 1 for row in report.reason_code_counts):
        raise ValueError("reason_code_counts must be presence counts")
    if report.gate_status != _gate_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    has_pass_reason = PASS_REASON_CODE in report.reason_codes
    has_other_reason = any(
        reason_code in BLOCKED_REASON_CODES or reason_code in WATCH_REASON_CODES
        for reason_code in report.reason_codes
    )
    if has_pass_reason and has_other_reason:
        raise ValueError("pass reason must not be mixed with watch or blocked reasons")
    if report.source_health_report_count == 0:
        if report.latest_health_status is not None:
            raise ValueError("latest_health_status must be absent without source reports")
        if report.latest_health_generated_at is not None:
            raise ValueError(
                "latest_health_generated_at must be absent without source reports",
            )


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    if not rows:
        raise ValueError("reason_code_counts is required")
    seen: set[str] = set()
    previous_key: tuple[int, str] | None = None
    for row in rows:
        if (
            type(row)
            is not PaperProjectScreeningRankStabilityDbHistoryHealthTrendGateReasonCodeCount
        ):
            raise ValueError("reason_code_counts must contain exact reason rows")
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.report_count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministic")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _normalize_count_pairs(
    field_name: str,
    value: object,
) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    rows: list[tuple[str, int]] = []
    seen: set[str] = set()
    previous_key: tuple[int, str] | None = None
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError(f"{field_name} must contain reason/count pairs")
        reason_code, count = item
        _require_canonical_string(field_name, reason_code)
        _require_positive_int(field_name, count)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        key = (-count, reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError(f"{field_name} must be deterministic")
        previous_key = key
        seen.add(reason_code)
        rows.append((reason_code, count))
    return tuple(rows)


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} is required")
    seen: set[str] = set()
    previous: str | None = None
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in GATE_REASON_CODES:
            raise ValueError(f"{field_name} must contain known gate reason codes")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > reason_code:
            raise ValueError(f"{field_name} must be sorted")
        previous = reason_code
        seen.add(reason_code)
    return reason_codes


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _require_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")


def _require_optional_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_int(field_name, value)


def _validate_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")
