"""Pure probability selection summary history trend reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.paper_probability_selection_summary_history import (
    PaperProbabilitySelectionSummaryHistoryReport,
)


DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_CONFIG_VERSION = (
    "paper-probability-selection-summary-history-trend-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
HISTORY_STATUSES = ("ready", "watch", "blocked")
TREND_STATUSES = (
    "insufficient_history",
    "stale",
    "deteriorating",
    "watch",
    "stable",
)
NEXT_STEP_BY_TREND_STATUS = {
    "insufficient_history": "collect_more_history",
    "stale": "refresh_source_history",
    "deteriorating": "review_probability_selection",
    "watch": "continue_monitoring",
    "stable": "continue_monitoring",
}
STABLE_SOURCE_REASON_CODE = "selection_summary_history_stable"
TREND_REASON_CODES = (
    "insufficient_history_count",
    "latest_history_stale",
    "stale_history_reports_present",
    "thin_history_reports_present",
    "selected_share_deteriorated",
    "average_selected_share_below_minimum",
    "latest_history_watch",
    "latest_history_blocked",
    "recurring_history_reason_codes",
    "history_trend_stable",
)
TREND_REASON_CODE_SET = frozenset(TREND_REASON_CODES)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryTrendConfig:
    config_version: str = (
        DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_CONFIG_VERSION
    )
    min_history_count: int = 3
    stale_age_seconds: int = 3_600
    min_average_selected_share: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperProbabilitySelectionSummaryHistoryTrendConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperProbabilitySelectionSummaryHistoryTrendConfig:
            raise ValueError(
                "config must be exactly "
                "PaperProbabilitySelectionSummaryHistoryTrendConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_history_count", self.min_history_count)
        _require_nonnegative_int("stale_age_seconds", self.stale_age_seconds)
        object.__setattr__(
            self,
            "min_average_selected_share",
            _normalize_probability(
                "min_average_selected_share",
                self.min_average_selected_share,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryTrendReport:
    generated_at: datetime
    config_version: str
    source_history_count: int
    first_generated_at: datetime
    latest_generated_at: datetime
    history_span_seconds: int
    latest_history_status: str
    latest_status_streak: int
    latest_selected_share: Decimal
    average_selected_share: Decimal
    selected_share_delta: Decimal
    stale_history_count: int
    thin_history_count: int
    recurring_reason_code_counts: tuple[tuple[str, int], ...]
    trend_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperProbabilitySelectionSummaryHistoryTrendReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperProbabilitySelectionSummaryHistoryTrendReport:
            raise ValueError(
                "trend report must be exactly "
                "PaperProbabilitySelectionSummaryHistoryTrendReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "first_generated_at",
            _as_utc("first_generated_at", self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_utc("latest_generated_at", self.latest_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("source_history_count", self.source_history_count)
        _require_nonnegative_int("history_span_seconds", self.history_span_seconds)
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
            "recurring_reason_code_counts",
            _normalize_reason_code_counts(self.recurring_reason_code_counts),
        )
        _require_trend_status("trend_status", self.trend_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("trend report", self)
        _validate_trend_report(self)


def build_paper_probability_selection_summary_history_trend_report(
    history_reports: object,
    *,
    config: PaperProbabilitySelectionSummaryHistoryTrendConfig,
    generated_at: datetime,
) -> PaperProbabilitySelectionSummaryHistoryTrendReport:
    if type(config) is not PaperProbabilitySelectionSummaryHistoryTrendConfig:
        raise ValueError(
            "config must be exactly "
            "PaperProbabilitySelectionSummaryHistoryTrendConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    reports = _normalize_history_reports(history_reports)
    _require_chronological_reports(reports)

    first_report = reports[0]
    latest_report = reports[-1]
    latest_selected_share = _normalize_probability(
        "latest_selected_share",
        latest_report.latest_selected_share,
    )
    average_selected_share = _average_latest_selected_share(reports)
    selected_share_delta = _quantize(
        latest_selected_share
        - _normalize_probability(
            "first latest_selected_share",
            first_report.latest_selected_share,
        ),
    )
    stale_history_count = _stale_history_count(
        reports,
        generated_at=generated_at_utc,
        stale_age_seconds=config.stale_age_seconds,
    )
    thin_history_count = sum(
        1 for report in reports if report.source_report_count < config.min_history_count
    )
    recurring_reason_code_counts = _recurring_reason_code_counts(reports)
    reason_codes = _trend_reason_codes(
        reports=reports,
        config=config,
        generated_at=generated_at_utc,
        stale_history_count=stale_history_count,
        thin_history_count=thin_history_count,
        average_selected_share=average_selected_share,
        selected_share_delta=selected_share_delta,
        recurring_reason_code_counts=recurring_reason_code_counts,
    )
    trend_status = _trend_status(reason_codes)

    return PaperProbabilitySelectionSummaryHistoryTrendReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_history_count=len(reports),
        first_generated_at=first_report.generated_at,
        latest_generated_at=latest_report.generated_at,
        history_span_seconds=_seconds_between(
            latest_report.generated_at,
            first_report.generated_at,
            "history_span_seconds",
        ),
        latest_history_status=latest_report.history_status,
        latest_status_streak=_latest_status_streak(reports),
        latest_selected_share=latest_selected_share,
        average_selected_share=average_selected_share,
        selected_share_delta=selected_share_delta,
        stale_history_count=stale_history_count,
        thin_history_count=thin_history_count,
        recurring_reason_code_counts=recurring_reason_code_counts,
        trend_status=trend_status,
        recommended_next_step=NEXT_STEP_BY_TREND_STATUS[trend_status],
        reason_codes=reason_codes,
    )


def _normalize_history_reports(
    value: object,
) -> tuple[PaperProbabilitySelectionSummaryHistoryReport, ...]:
    if type(value) is not tuple:
        raise ValueError("history_reports must be a tuple")
    if not value:
        raise ValueError("history_reports must be nonempty")
    reports = tuple(value)
    for index, report in enumerate(reports):
        if type(report) is not PaperProbabilitySelectionSummaryHistoryReport:
            raise ValueError(
                "history_reports must contain "
                "PaperProbabilitySelectionSummaryHistoryReport values",
            )
        _validate_source_history_report(index, report)
    return reports


def _validate_source_history_report(
    index: int,
    report: PaperProbabilitySelectionSummaryHistoryReport,
) -> None:
    label = f"source history_reports.{index}"
    _require_hard_flags(label, report)
    _as_utc(f"{label}.generated_at", report.generated_at)
    _require_nonnegative_int(f"{label}.source_report_count", report.source_report_count)
    _require_history_status(f"{label}.history_status", report.history_status)
    _normalize_probability(
        f"{label}.latest_selected_share",
        report.latest_selected_share,
    )
    _normalize_probability(
        f"{label}.average_selected_share",
        report.average_selected_share,
    )
    _require_reason_codes(f"{label}.reason_codes", report.reason_codes)


def _require_chronological_reports(
    reports: tuple[PaperProbabilitySelectionSummaryHistoryReport, ...],
) -> None:
    previous_generated_at: datetime | None = None
    for report in reports:
        generated_at = _as_utc("source history generated_at", report.generated_at)
        if previous_generated_at is not None and generated_at < previous_generated_at:
            raise ValueError("history_reports must be chronological by generated_at")
        previous_generated_at = generated_at


def _average_latest_selected_share(
    reports: tuple[PaperProbabilitySelectionSummaryHistoryReport, ...],
) -> Decimal:
    total = sum(
        _normalize_probability("latest_selected_share", report.latest_selected_share)
        for report in reports
    )
    return _quantize(total / Decimal(len(reports)))


def _stale_history_count(
    reports: tuple[PaperProbabilitySelectionSummaryHistoryReport, ...],
    *,
    generated_at: datetime,
    stale_age_seconds: int,
) -> int:
    return sum(
        1
        for report in reports
        if _seconds_between(
            generated_at,
            report.generated_at,
            "source history generated_at",
        )
        > stale_age_seconds
    )


def _recurring_reason_code_counts(
    reports: tuple[PaperProbabilitySelectionSummaryHistoryReport, ...],
) -> tuple[tuple[str, int], ...]:
    counts: Counter[str] = Counter()
    for report in reports:
        counts.update(
            reason_code
            for reason_code in set(report.reason_codes)
            if reason_code != STABLE_SOURCE_REASON_CODE
        )
    return tuple(
        (reason_code, count)
        for reason_code, count in sorted(counts.items())
        if count > 1
    )


def _trend_reason_codes(
    *,
    reports: tuple[PaperProbabilitySelectionSummaryHistoryReport, ...],
    config: PaperProbabilitySelectionSummaryHistoryTrendConfig,
    generated_at: datetime,
    stale_history_count: int,
    thin_history_count: int,
    average_selected_share: Decimal,
    selected_share_delta: Decimal,
    recurring_reason_code_counts: tuple[tuple[str, int], ...],
) -> tuple[str, ...]:
    latest_report = reports[-1]
    reason_codes: list[str] = []
    if len(reports) < config.min_history_count:
        reason_codes.append("insufficient_history_count")
    if _is_stale(
        latest_report,
        generated_at=generated_at,
        stale_age_seconds=config.stale_age_seconds,
    ):
        reason_codes.append("latest_history_stale")
    elif stale_history_count > 0:
        reason_codes.append("stale_history_reports_present")
    if thin_history_count > 0:
        reason_codes.append("thin_history_reports_present")
    if selected_share_delta < ZERO:
        reason_codes.append("selected_share_deteriorated")
    if average_selected_share < config.min_average_selected_share:
        reason_codes.append("average_selected_share_below_minimum")
    if latest_report.history_status == "watch":
        reason_codes.append("latest_history_watch")
    if latest_report.history_status == "blocked":
        reason_codes.append("latest_history_blocked")
    if recurring_reason_code_counts:
        reason_codes.append("recurring_history_reason_codes")
    if not reason_codes:
        reason_codes.append("history_trend_stable")
    return tuple(reason_codes)


def _is_stale(
    report: PaperProbabilitySelectionSummaryHistoryReport,
    *,
    generated_at: datetime,
    stale_age_seconds: int,
) -> bool:
    return (
        _seconds_between(generated_at, report.generated_at, "source history generated_at")
        > stale_age_seconds
    )


def _trend_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("history_trend_stable",):
        return "stable"
    if "insufficient_history_count" in reason_codes:
        return "insufficient_history"
    if "latest_history_stale" in reason_codes:
        return "stale"
    if (
        "selected_share_deteriorated" in reason_codes
        or "average_selected_share_below_minimum" in reason_codes
    ):
        return "deteriorating"
    return "watch"


def _latest_status_streak(
    reports: tuple[PaperProbabilitySelectionSummaryHistoryReport, ...],
) -> int:
    latest_status = reports[-1].history_status
    count = 0
    for report in reversed(reports):
        if report.history_status != latest_status:
            break
        count += 1
    return count


def _validate_trend_report(
    report: PaperProbabilitySelectionSummaryHistoryTrendReport,
) -> None:
    if report.recommended_next_step != NEXT_STEP_BY_TREND_STATUS[report.trend_status]:
        raise ValueError("recommended_next_step must match trend_status")
    if report.latest_status_streak > report.source_history_count:
        raise ValueError("latest_status_streak must not exceed source_history_count")
    if report.stale_history_count > report.source_history_count:
        raise ValueError("stale_history_count must not exceed source_history_count")
    if report.thin_history_count > report.source_history_count:
        raise ValueError("thin_history_count must not exceed source_history_count")
    if report.history_span_seconds != _seconds_between(
        report.latest_generated_at,
        report.first_generated_at,
        "history_span_seconds",
    ):
        raise ValueError("history_span_seconds must match first/latest generated_at")
    if report.generated_at < report.latest_generated_at:
        raise ValueError("latest_generated_at must not be after generated_at")
    if not report.reason_codes:
        raise ValueError("reason_codes must be nonempty")
    for reason_code in report.reason_codes:
        if reason_code not in TREND_REASON_CODE_SET:
            raise ValueError("reason_codes must be known trend reasons")
    if report.trend_status != _trend_status(report.reason_codes):
        raise ValueError("trend_status must match reason_codes")
    if report.reason_codes == ("history_trend_stable",):
        if report.trend_status != "stable":
            raise ValueError("history_trend_stable requires stable trend_status")
        if (
            report.average_selected_share == report.latest_selected_share
            and report.selected_share_delta != ZERO
        ):
            raise ValueError("selected_share_delta must match stable selected shares")
        if report.stale_history_count != 0:
            raise ValueError("stale_history_count must be zero for stable trends")
        if report.thin_history_count != 0:
            raise ValueError("thin_history_count must be zero for stable trends")
        if report.recurring_reason_code_counts:
            raise ValueError("recurring_reason_code_counts must be empty for stable trends")
    elif "history_trend_stable" in report.reason_codes:
        raise ValueError("reason_codes must not mix stable and non-stable reasons")
    if report.selected_share_delta < ZERO and (
        "selected_share_deteriorated" not in report.reason_codes
    ):
        raise ValueError("selected_share_delta requires a deterioration reason")
    if (
        "selected_share_deteriorated" in report.reason_codes
        and report.selected_share_delta >= ZERO
    ):
        raise ValueError("selected_share_delta must be negative when deteriorated")
    if report.stale_history_count > 0 and (
        "latest_history_stale" not in report.reason_codes
        and "stale_history_reports_present" not in report.reason_codes
    ):
        raise ValueError("stale_history_count requires a stale history reason")
    if "latest_history_stale" in report.reason_codes and report.stale_history_count == 0:
        raise ValueError("stale_history_count must support latest stale reason")
    if (
        "stale_history_reports_present" in report.reason_codes
        and report.stale_history_count == 0
    ):
        raise ValueError("stale_history_count must support stale history reason")
    if (
        report.thin_history_count > 0
        and "thin_history_reports_present" not in report.reason_codes
    ):
        raise ValueError("thin_history_count requires thin history reason")
    if (
        "thin_history_reports_present" in report.reason_codes
        and report.thin_history_count == 0
    ):
        raise ValueError("thin_history_count must support thin history reason")
    for _, count in report.recurring_reason_code_counts:
        if count <= 1:
            raise ValueError("recurring_reason_code_counts must exceed one")
        if count > report.source_history_count:
            raise ValueError(
                "recurring_reason_code_counts must not exceed source_history_count",
            )
    if (
        report.recurring_reason_code_counts
        and "recurring_history_reason_codes" not in report.reason_codes
    ):
        raise ValueError(
            "recurring_reason_code_counts require recurring reason code",
        )
    if (
        "recurring_history_reason_codes" in report.reason_codes
        and not report.recurring_reason_code_counts
    ):
        raise ValueError(
            "recurring_reason_code_counts must support recurring reason code",
        )
    if (
        report.latest_history_status == "watch"
        and "latest_history_watch" not in report.reason_codes
    ):
        raise ValueError("latest_history_status requires watch reason")
    if (
        "latest_history_watch" in report.reason_codes
        and report.latest_history_status != "watch"
    ):
        raise ValueError("latest_history_status must support watch reason")
    if (
        report.latest_history_status == "blocked"
        and "latest_history_blocked" not in report.reason_codes
    ):
        raise ValueError("latest_history_status requires blocked reason")
    if (
        "latest_history_blocked" in report.reason_codes
        and report.latest_history_status != "blocked"
    ):
        raise ValueError("latest_history_status must support blocked reason")


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, int], ...]:
    if type(value) is not tuple:
        raise ValueError("recurring_reason_code_counts must be a tuple")
    rows: list[tuple[str, int]] = []
    previous_reason_code: str | None = None
    seen: set[str] = set()
    for row in value:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(
                "recurring_reason_code_counts must contain reason/count tuples",
            )
        reason_code, count = row
        _require_canonical_string("recurring_reason_code_counts", reason_code)
        _require_positive_int("recurring_reason_code_counts", count)
        if reason_code in seen:
            raise ValueError("recurring_reason_code_counts must be unique")
        if previous_reason_code is not None and previous_reason_code > reason_code:
            raise ValueError("recurring_reason_code_counts must be sorted")
        previous_reason_code = reason_code
        seen.add(reason_code)
        rows.append((reason_code, count))
    return tuple(rows)


def _require_reason_codes(field_name: str, value: object) -> None:
    _normalize_reason_codes(field_name, value)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
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


def _seconds_between(later: datetime, earlier: datetime, field_name: str) -> int:
    later_utc = _as_utc(field_name, later)
    earlier_utc = _as_utc(field_name, earlier)
    seconds = (later_utc - earlier_utc) // timedelta(seconds=1)
    if seconds < 0:
        raise ValueError(f"{field_name} must not be future dated")
    return seconds


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_history_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_trend_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TREND_STATUSES:
        raise ValueError(f"{field_name} must be a known trend status")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be a nonnegative int")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or value < 1:
        raise ValueError(f"{field_name} must be a positive int")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_CONFIG_VERSION",
    "PaperProbabilitySelectionSummaryHistoryTrendConfig",
    "PaperProbabilitySelectionSummaryHistoryTrendReport",
    "build_paper_probability_selection_summary_history_trend_report",
)
