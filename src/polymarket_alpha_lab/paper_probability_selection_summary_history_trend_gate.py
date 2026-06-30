"""Pure gate reducer for paper probability selection summary history trends."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.paper_probability_selection_summary_history_trend import (
    HISTORY_STATUSES,
    PaperProbabilitySelectionSummaryHistoryTrendReport,
    TREND_STATUSES,
)


DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_GATE_CONFIG_VERSION = (
    "paper-probability-selection-summary-history-trend-gate-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
GATE_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_GATE_STATUS = {
    "pass": "allow_probability_selection_summary_history_trend_review",
    "watch": "throttle_probability_selection_summary_history_trend_review",
    "blocked": "block_probability_selection_summary_history_trend_review",
}
PASS_REASON_CODE = "paper_probability_selection_summary_history_trend_gate_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_paper_probability_selection_summary_history_trend_samples",
        "stale_paper_probability_selection_summary_history_trend",
        "deteriorating_paper_probability_selection_summary_history_trend",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "latest_paper_probability_selection_summary_history_trend_watch",
        "repeated_paper_probability_selection_summary_history_trend_watch_threshold_exceeded",
        "thin_paper_probability_selection_summary_history_trend_reports",
        "recurring_paper_probability_selection_summary_history_trend_reason_codes",
        "aged_paper_probability_selection_summary_history_trend_report",
    ),
)
GATE_REASON_CODES = frozenset((PASS_REASON_CODE,)) | BLOCKED_REASON_CODES | WATCH_REASON_CODES

__all__ = (
    "DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_GATE_CONFIG_VERSION",
    "PaperProbabilitySelectionSummaryHistoryTrendGateConfig",
    "PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount",
    "PaperProbabilitySelectionSummaryHistoryTrendGateReport",
    "build_paper_probability_selection_summary_history_trend_gate_report",
)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryTrendGateConfig:
    config_version: str = (
        DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_GATE_CONFIG_VERSION
    )
    min_source_history_count: int = 3
    max_latest_status_streak_for_watch: int = 1
    max_trend_report_age_seconds: int = 86_400
    max_recurring_reason_code_count: int = 2
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProbabilitySelectionSummaryHistoryTrendGateConfig:
            raise TypeError(
                "PaperProbabilitySelectionSummaryHistoryTrendGateConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProbabilitySelectionSummaryHistoryTrendGateConfig:
            raise ValueError(
                "config must be exactly "
                "PaperProbabilitySelectionSummaryHistoryTrendGateConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_source_history_count",
            "max_latest_status_streak_for_watch",
            "max_trend_report_age_seconds",
            "max_recurring_reason_code_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount:
            raise TypeError(
                "PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryTrendGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    trend_report_age_seconds: int
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount,
        ...,
    ]
    source_history_count: int
    source_trend_status: str
    source_recommended_next_step: str
    latest_history_status: str
    latest_status_streak: int
    latest_selected_share: Decimal
    average_selected_share: Decimal
    selected_share_delta: Decimal
    stale_history_count: int
    thin_history_count: int
    latest_source_reason_codes: tuple[str, ...]
    recurring_source_reason_code_counts: tuple[tuple[str, int], ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PaperProbabilitySelectionSummaryHistoryTrendGateReport:
            raise TypeError(
                "PaperProbabilitySelectionSummaryHistoryTrendGateReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not PaperProbabilitySelectionSummaryHistoryTrendGateReport:
            raise ValueError(
                "gate report must be exactly "
                "PaperProbabilitySelectionSummaryHistoryTrendGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_nonnegative_int(
            "trend_report_age_seconds",
            self.trend_report_age_seconds,
        )
        _require_gate_status("gate_status", self.gate_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_nonnegative_int("source_history_count", self.source_history_count)
        _require_trend_status("source_trend_status", self.source_trend_status)
        _require_canonical_string(
            "source_recommended_next_step",
            self.source_recommended_next_step,
        )
        _require_history_status("latest_history_status", self.latest_history_status)
        _require_positive_int("latest_status_streak", self.latest_status_streak)
        object.__setattr__(
            self,
            "latest_selected_share",
            _normalize_probability("latest_selected_share", self.latest_selected_share),
        )
        object.__setattr__(
            self,
            "average_selected_share",
            _normalize_probability("average_selected_share", self.average_selected_share),
        )
        object.__setattr__(
            self,
            "selected_share_delta",
            _normalize_delta("selected_share_delta", self.selected_share_delta),
        )
        _require_nonnegative_int("stale_history_count", self.stale_history_count)
        _require_nonnegative_int("thin_history_count", self.thin_history_count)
        object.__setattr__(
            self,
            "latest_source_reason_codes",
            _normalize_source_reason_codes(
                "latest_source_reason_codes",
                self.latest_source_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "recurring_source_reason_code_counts",
            _normalize_count_pairs(
                "recurring_source_reason_code_counts",
                self.recurring_source_reason_code_counts,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_gate_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_gate_report(self)
        _validate_hard_flags("gate report", self)


def build_paper_probability_selection_summary_history_trend_gate_report(
    source_report: object,
    *,
    config: PaperProbabilitySelectionSummaryHistoryTrendGateConfig,
    generated_at: datetime,
) -> PaperProbabilitySelectionSummaryHistoryTrendGateReport:
    if type(source_report) is not PaperProbabilitySelectionSummaryHistoryTrendReport:
        raise ValueError(
            "source_report must be exactly "
            "PaperProbabilitySelectionSummaryHistoryTrendReport",
        )
    if type(config) is not PaperProbabilitySelectionSummaryHistoryTrendGateConfig:
        raise ValueError(
            "config must be exactly "
            "PaperProbabilitySelectionSummaryHistoryTrendGateConfig",
        )
    _validate_hard_flags("source_report", source_report)
    _validate_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_generated_at = _as_utc("source_generated_at", source_report.generated_at)
    if source_generated_at > generated_at_utc:
        raise ValueError("source_generated_at must not be after generated_at")
    reason_codes = _gate_reason_codes(
        source_report,
        config=config,
        generated_at=generated_at_utc,
    )
    gate_status = _gate_status(reason_codes)
    return PaperProbabilitySelectionSummaryHistoryTrendGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_config_version=source_report.config_version,
        source_generated_at=source_generated_at,
        trend_report_age_seconds=_seconds_between(
            generated_at_utc,
            source_generated_at,
            "trend_report_age_seconds",
        ),
        gate_status=gate_status,
        recommended_next_step=NEXT_STEP_BY_GATE_STATUS[gate_status],
        reason_code_counts=_reason_code_counts(reason_codes),
        source_history_count=source_report.source_history_count,
        source_trend_status=source_report.trend_status,
        source_recommended_next_step=source_report.recommended_next_step,
        latest_history_status=source_report.latest_history_status,
        latest_status_streak=source_report.latest_status_streak,
        latest_selected_share=source_report.latest_selected_share,
        average_selected_share=source_report.average_selected_share,
        selected_share_delta=source_report.selected_share_delta,
        stale_history_count=source_report.stale_history_count,
        thin_history_count=source_report.thin_history_count,
        latest_source_reason_codes=source_report.reason_codes,
        recurring_source_reason_code_counts=source_report.recurring_reason_code_counts,
        reason_codes=reason_codes,
    )


def _gate_reason_codes(
    source_report: PaperProbabilitySelectionSummaryHistoryTrendReport,
    *,
    config: PaperProbabilitySelectionSummaryHistoryTrendGateConfig,
    generated_at: datetime,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if (
        source_report.source_history_count < config.min_source_history_count
        or source_report.trend_status == "insufficient_history"
    ):
        reason_codes.append(
            "insufficient_paper_probability_selection_summary_history_trend_samples",
        )
    if source_report.trend_status == "stale":
        reason_codes.append("stale_paper_probability_selection_summary_history_trend")
    if source_report.trend_status == "deteriorating":
        reason_codes.append(
            "deteriorating_paper_probability_selection_summary_history_trend",
        )
    if source_report.trend_status == "watch":
        reason_codes.append("latest_paper_probability_selection_summary_history_trend_watch")
        if (
            source_report.latest_status_streak
            > config.max_latest_status_streak_for_watch
        ):
            reason_codes.append(
                "repeated_paper_probability_selection_summary_history_trend_watch_threshold_exceeded",
            )
    if source_report.thin_history_count > 0:
        reason_codes.append(
            "thin_paper_probability_selection_summary_history_trend_reports",
        )
    if any(
        count > config.max_recurring_reason_code_count
        for _, count in source_report.recurring_reason_code_counts
    ):
        reason_codes.append(
            "recurring_paper_probability_selection_summary_history_trend_reason_codes",
        )
    if (
        _seconds_between(
            generated_at,
            source_report.generated_at,
            "trend_report_age_seconds",
        )
        > config.max_trend_report_age_seconds
    ):
        reason_codes.append(
            "aged_paper_probability_selection_summary_history_trend_report",
        )
    if not reason_codes:
        reason_codes.append(PASS_REASON_CODE)
    return tuple(_dedupe_sequence(reason_codes))


def _gate_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount, ...]:
    return tuple(
        PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount(reason_code, 1)
        for reason_code in reason_codes
    )


def _dedupe_sequence(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)


def _validate_gate_report(
    report: PaperProbabilitySelectionSummaryHistoryTrendGateReport,
) -> None:
    if report.generated_at < report.source_generated_at:
        raise ValueError("source_generated_at must not be after generated_at")
    if report.trend_report_age_seconds != _seconds_between(
        report.generated_at,
        report.source_generated_at,
        "trend_report_age_seconds",
    ):
        raise ValueError("trend_report_age_seconds must match generated_at/source")
    if report.recommended_next_step != NEXT_STEP_BY_GATE_STATUS[report.gate_status]:
        raise ValueError("recommended_next_step must match gate_status")
    if not report.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")
    if report.gate_status != _gate_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if PASS_REASON_CODE in report.reason_codes and len(report.reason_codes) != 1:
        raise ValueError("pass reason code must not be mixed with other reasons")
    if report.latest_status_streak > report.source_history_count:
        raise ValueError("latest_status_streak must not exceed source_history_count")
    if report.stale_history_count > report.source_history_count:
        raise ValueError("stale_history_count must not exceed source_history_count")
    if report.thin_history_count > report.source_history_count:
        raise ValueError("thin_history_count must not exceed source_history_count")

    thin_reason = "thin_paper_probability_selection_summary_history_trend_reports"
    recurring_reason = (
        "recurring_paper_probability_selection_summary_history_trend_reason_codes"
    )
    if report.thin_history_count > 0 and thin_reason not in report.reason_codes:
        raise ValueError("thin_history_count requires thin history gate reason")
    if thin_reason in report.reason_codes and report.thin_history_count == 0:
        raise ValueError("thin_history_count must support thin history gate reason")
    if (
        recurring_reason in report.reason_codes
        and not report.recurring_source_reason_code_counts
    ):
        raise ValueError(
            "recurring_source_reason_code_counts must support recurring gate reason",
        )

    insufficient_reason = (
        "insufficient_paper_probability_selection_summary_history_trend_samples"
    )
    stale_reason = "stale_paper_probability_selection_summary_history_trend"
    deteriorating_reason = (
        "deteriorating_paper_probability_selection_summary_history_trend"
    )
    watch_reason = "latest_paper_probability_selection_summary_history_trend_watch"
    if (
        report.source_trend_status == "insufficient_history"
        and insufficient_reason not in report.reason_codes
    ):
        raise ValueError("source_trend_status requires insufficient gate reason")
    if report.source_trend_status == "stale" and stale_reason not in report.reason_codes:
        raise ValueError("source_trend_status requires stale gate reason")
    if stale_reason in report.reason_codes and report.source_trend_status != "stale":
        raise ValueError("source_trend_status must support stale gate reason")
    if (
        report.source_trend_status == "deteriorating"
        and deteriorating_reason not in report.reason_codes
    ):
        raise ValueError("source_trend_status requires deteriorating gate reason")
    if (
        deteriorating_reason in report.reason_codes
        and report.source_trend_status != "deteriorating"
    ):
        raise ValueError("source_trend_status must support deteriorating gate reason")
    if report.source_trend_status == "watch" and watch_reason not in report.reason_codes:
        raise ValueError("source_trend_status requires watch gate reason")
    if watch_reason in report.reason_codes and report.source_trend_status != "watch":
        raise ValueError("source_trend_status must support watch gate reason")
    if report.reason_codes == (PASS_REASON_CODE,) and report.source_trend_status != "stable":
        raise ValueError("source_trend_status must support pass gate reason")


def _normalize_reason_code_counts(
    value: object,
) -> tuple[PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    if not value:
        raise ValueError("reason_code_counts must be nonempty")
    counts = tuple(value)
    for count in counts:
        if type(count) is not PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount values",
            )
    return counts


def _normalize_count_pairs(label: str, value: object) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    normalized = []
    previous_reason_code: str | None = None
    seen: set[str] = set()
    for row in value:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f"{label} rows must be reason/count pairs")
        reason_code, count = row
        _require_canonical_string(f"{label} reason_code", reason_code)
        _require_positive_int(f"{label} count", count)
        if reason_code in seen:
            raise ValueError(f"{label} must be unique")
        if previous_reason_code is not None and previous_reason_code > reason_code:
            raise ValueError(f"{label} must be sorted")
        previous_reason_code = reason_code
        seen.add(reason_code)
        normalized.append((reason_code, count))
    return tuple(normalized)


def _normalize_source_reason_codes(label: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    if not value:
        raise ValueError(f"{label} must be nonempty")
    values = tuple(value)
    seen: set[str] = set()
    for reason_code in values:
        _require_canonical_string(label, reason_code)
        if reason_code in seen:
            raise ValueError(f"{label} must be unique")
        seen.add(reason_code)
    return values


def _normalize_gate_reason_codes(label: str, value: object) -> tuple[str, ...]:
    reason_codes = _normalize_source_reason_codes(label, value)
    for reason_code in reason_codes:
        if reason_code not in GATE_REASON_CODES:
            raise ValueError(f"{label} must contain known gate reason codes")
    return reason_codes


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_delta(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE:
        raise ValueError(f"{field_name} must be at least negative one")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(later: datetime, earlier: datetime, field_name: str) -> int:
    later_utc = _as_utc(field_name, later)
    earlier_utc = _as_utc(field_name, earlier)
    seconds = (later_utc - earlier_utc) // timedelta(seconds=1)
    if seconds < 0:
        raise ValueError(f"{field_name} must not be future dated")
    return seconds


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_history_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_trend_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TREND_STATUSES:
        raise ValueError(f"{field_name} must be a known trend status")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    if value != value.strip() or value.lower() != value:
        raise ValueError(f"{field_name} must be canonical")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _validate_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")
