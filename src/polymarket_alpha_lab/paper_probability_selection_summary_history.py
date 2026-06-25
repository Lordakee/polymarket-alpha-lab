"""Pure paper-only probability selection summary history reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.paper_probability_selection_summary import (
    PaperProbabilitySelectionSummaryReport,
    PaperProbabilitySelectionSummaryRow,
)


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
HISTORY_STATUSES = ("ready", "watch", "blocked")
RECOMMENDED_NEXT_STEPS = (
    "collect_more_history",
    "refresh_selection_summary",
    "review_probability_selection",
    "proceed_to_paper_allocation",
)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryConfig:
    config_version: str
    min_source_report_count: int = 3
    max_latest_age_seconds: int = 3600
    min_latest_selected_share: Decimal = ZERO
    min_average_selected_share: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperProbabilitySelectionSummaryHistoryConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperProbabilitySelectionSummaryHistoryConfig:
            raise ValueError(
                "config must be exactly PaperProbabilitySelectionSummaryHistoryConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_source_report_count", self.min_source_report_count)
        _require_nonnegative_int("max_latest_age_seconds", self.max_latest_age_seconds)
        object.__setattr__(
            self,
            "min_latest_selected_share",
            _normalize_probability(
                "min_latest_selected_share",
                self.min_latest_selected_share,
            ),
        )
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
class PaperProbabilitySelectionSummaryHistoryReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    history_span_seconds: int | None
    latest_age_seconds: int | None
    latest_queue_count: int
    latest_selected_count: int
    latest_pending_count: int
    latest_rejected_count: int
    latest_skipped_count: int
    aggregate_queue_count: int
    aggregate_selected_count: int
    aggregate_pending_count: int
    aggregate_rejected_count: int
    aggregate_skipped_count: int
    latest_selected_share: Decimal
    average_selected_share: Decimal
    distinct_config_versions: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, int], ...]
    history_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "PaperProbabilitySelectionSummaryHistoryReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not PaperProbabilitySelectionSummaryHistoryReport:
            raise ValueError(
                "history report must be exactly "
                "PaperProbabilitySelectionSummaryHistoryReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        object.__setattr__(
            self,
            "first_generated_at",
            _normalize_optional_datetime("first_generated_at", self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _normalize_optional_datetime("latest_generated_at", self.latest_generated_at),
        )
        _require_optional_int("history_span_seconds", self.history_span_seconds)
        _require_optional_int("latest_age_seconds", self.latest_age_seconds)
        for field_name in (
            "latest_queue_count",
            "latest_selected_count",
            "latest_pending_count",
            "latest_rejected_count",
            "latest_skipped_count",
            "aggregate_queue_count",
            "aggregate_selected_count",
            "aggregate_pending_count",
            "aggregate_rejected_count",
            "aggregate_skipped_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
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
            "distinct_config_versions",
            _normalize_config_versions(self.distinct_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_history_status("history_status", self.history_status)
        _require_recommended_next_step(
            "recommended_next_step",
            self.recommended_next_step,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("history report", self)
        _validate_report_consistency(self)


def build_paper_probability_selection_summary_history_report(
    reports: tuple[PaperProbabilitySelectionSummaryReport, ...],
    *,
    config: PaperProbabilitySelectionSummaryHistoryConfig,
    generated_at: datetime,
) -> PaperProbabilitySelectionSummaryHistoryReport:
    if type(config) is not PaperProbabilitySelectionSummaryHistoryConfig:
        raise ValueError(
            "config must be a PaperProbabilitySelectionSummaryHistoryConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    source_reports = _normalize_reports(reports)

    if not source_reports:
        reason_codes = _history_reason_codes(
            config=config,
            source_report_count=0,
            latest_age_seconds=None,
            latest_selected_share=ZERO,
            average_selected_share=ZERO,
            latest_pending_count=0,
            latest_rejected_count=0,
            distinct_config_versions=(),
        )
        return PaperProbabilitySelectionSummaryHistoryReport(
            generated_at=generated_at,
            config_version=config.config_version,
            source_report_count=0,
            first_generated_at=None,
            latest_generated_at=None,
            history_span_seconds=None,
            latest_age_seconds=None,
            latest_queue_count=0,
            latest_selected_count=0,
            latest_pending_count=0,
            latest_rejected_count=0,
            latest_skipped_count=0,
            aggregate_queue_count=0,
            aggregate_selected_count=0,
            aggregate_pending_count=0,
            aggregate_rejected_count=0,
            aggregate_skipped_count=0,
            latest_selected_share=ZERO,
            average_selected_share=ZERO,
            distinct_config_versions=(),
            reason_code_counts=(),
            history_status=_history_status(reason_codes),
            recommended_next_step=_recommended_next_step(reason_codes),
            reason_codes=reason_codes,
        )

    first_report = source_reports[0]
    latest_report = source_reports[-1]
    latest_selected_count = latest_report.ready_count
    latest_pending_count = latest_report.watch_count
    latest_rejected_count = latest_report.blocked_count
    latest_skipped_count = _skipped_count(latest_report)
    aggregate_queue_count = sum(report.queue_count for report in source_reports)
    aggregate_selected_count = sum(report.ready_count for report in source_reports)
    aggregate_pending_count = sum(report.watch_count for report in source_reports)
    aggregate_rejected_count = sum(report.blocked_count for report in source_reports)
    aggregate_skipped_count = sum(_skipped_count(report) for report in source_reports)
    latest_selected_share = _ratio(latest_selected_count, latest_report.queue_count)
    average_selected_share = _ratio(aggregate_selected_count, aggregate_queue_count)
    latest_age_seconds = _seconds_between(generated_at, latest_report.generated_at)
    reason_codes = _history_reason_codes(
        config=config,
        source_report_count=len(source_reports),
        latest_age_seconds=latest_age_seconds,
        latest_selected_share=latest_selected_share,
        average_selected_share=average_selected_share,
        latest_pending_count=latest_pending_count,
        latest_rejected_count=latest_rejected_count,
        distinct_config_versions=_distinct_config_versions(source_reports),
    )

    return PaperProbabilitySelectionSummaryHistoryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_count=len(source_reports),
        first_generated_at=first_report.generated_at,
        latest_generated_at=latest_report.generated_at,
        history_span_seconds=_seconds_between(
            latest_report.generated_at,
            first_report.generated_at,
        ),
        latest_age_seconds=latest_age_seconds,
        latest_queue_count=latest_report.queue_count,
        latest_selected_count=latest_selected_count,
        latest_pending_count=latest_pending_count,
        latest_rejected_count=latest_rejected_count,
        latest_skipped_count=latest_skipped_count,
        aggregate_queue_count=aggregate_queue_count,
        aggregate_selected_count=aggregate_selected_count,
        aggregate_pending_count=aggregate_pending_count,
        aggregate_rejected_count=aggregate_rejected_count,
        aggregate_skipped_count=aggregate_skipped_count,
        latest_selected_share=latest_selected_share,
        average_selected_share=average_selected_share,
        distinct_config_versions=_distinct_config_versions(source_reports),
        reason_code_counts=_reason_code_counts(source_reports),
        history_status=_history_status(reason_codes),
        recommended_next_step=_recommended_next_step(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_reports(
    reports: tuple[PaperProbabilitySelectionSummaryReport, ...],
) -> tuple[PaperProbabilitySelectionSummaryReport, ...]:
    if type(reports) is not tuple:
        raise ValueError("reports must be a tuple of PaperProbabilitySelectionSummaryReport values")
    for report in reports:
        if type(report) is not PaperProbabilitySelectionSummaryReport:
            raise ValueError(
                "reports must contain only PaperProbabilitySelectionSummaryReport values",
            )
        _validate_source_report(report)
    _require_chronological_reports(reports)
    return reports


def _require_chronological_reports(
    reports: tuple[PaperProbabilitySelectionSummaryReport, ...],
) -> None:
    previous_generated_at: datetime | None = None
    for report in reports:
        generated_at = _as_utc("source report generated_at", report.generated_at)
        if previous_generated_at is not None and generated_at < previous_generated_at:
            raise ValueError("reports must be in chronological generated_at order")
        previous_generated_at = generated_at


def _validate_source_report(report: PaperProbabilitySelectionSummaryReport) -> None:
    _require_hard_flags("source report", report)
    _as_utc("source report generated_at", report.generated_at)
    for row in report.rows:
        if type(row) is not PaperProbabilitySelectionSummaryRow:
            raise ValueError("source report rows must contain selection summary row values")
        _require_hard_flags("source report row", row)
    if report.queue_count != len(report.rows):
        raise ValueError("source report queue_count must match rows")
    if report.ready_count != sum(1 for row in report.rows if row.selection_status == "ready"):
        raise ValueError("source report ready_count must match rows")
    if report.watch_count != sum(1 for row in report.rows if row.selection_status == "watch"):
        raise ValueError("source report watch_count must match rows")
    if report.blocked_count != sum(1 for row in report.rows if row.selection_status == "blocked"):
        raise ValueError("source report blocked_count must match rows")


def _skipped_count(report: PaperProbabilitySelectionSummaryReport) -> int:
    return sum(1 for row in report.rows if row.recommended_next_step == "skip")


def _distinct_config_versions(
    reports: tuple[PaperProbabilitySelectionSummaryReport, ...],
) -> tuple[str, ...]:
    return tuple(sorted({report.config_version for report in reports}))


def _reason_code_counts(
    reports: tuple[PaperProbabilitySelectionSummaryReport, ...],
) -> tuple[tuple[str, int], ...]:
    counts: Counter[str] = Counter()
    for report in reports:
        counts.update(report.reason_codes)
        for row in report.rows:
            counts.update(row.reason_codes)
    return tuple((reason_code, counts[reason_code]) for reason_code in sorted(counts))


def _history_reason_codes(
    *,
    config: PaperProbabilitySelectionSummaryHistoryConfig,
    source_report_count: int,
    latest_age_seconds: int | None,
    latest_selected_share: Decimal,
    average_selected_share: Decimal,
    latest_pending_count: int,
    latest_rejected_count: int,
    distinct_config_versions: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_report_count == 0:
        reason_codes.append("no_selection_summary_history")
    if source_report_count < config.min_source_report_count:
        reason_codes.append("insufficient_selection_summary_history")
    if (
        latest_age_seconds is not None
        and latest_age_seconds > config.max_latest_age_seconds
    ):
        reason_codes.append("latest_selection_summary_stale")
    if latest_rejected_count > 0:
        reason_codes.append("latest_selection_has_blocked_rows")
    if latest_pending_count > 0:
        reason_codes.append("latest_selection_has_watch_rows")
    if source_report_count > 0 and latest_selected_share < config.min_latest_selected_share:
        reason_codes.append("latest_selected_share_below_minimum")
    if source_report_count > 0 and average_selected_share < config.min_average_selected_share:
        reason_codes.append("average_selected_share_below_minimum")
    if len(distinct_config_versions) > 1:
        reason_codes.append("selection_summary_config_version_changed")
    if not reason_codes:
        reason_codes.append("selection_summary_history_stable")
    return tuple(reason_codes)


def _history_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("selection_summary_history_stable",):
        return "ready"
    blocked_reasons = {
        "no_selection_summary_history",
        "insufficient_selection_summary_history",
        "latest_selection_summary_stale",
        "latest_selected_share_below_minimum",
        "average_selected_share_below_minimum",
    }
    if any(reason_code in blocked_reasons for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _recommended_next_step(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("selection_summary_history_stable",):
        return "proceed_to_paper_allocation"
    if (
        "no_selection_summary_history" in reason_codes
        or "insufficient_selection_summary_history" in reason_codes
    ):
        return "collect_more_history"
    if "latest_selection_summary_stale" in reason_codes:
        return "refresh_selection_summary"
    return "review_probability_selection"


def _validate_report_consistency(
    report: PaperProbabilitySelectionSummaryHistoryReport,
) -> None:
    if report.history_status != _history_status(report.reason_codes):
        raise ValueError("history_status must match reason_codes")
    if report.recommended_next_step != _recommended_next_step(report.reason_codes):
        raise ValueError("recommended_next_step must match reason_codes")
    if report.history_status == "ready" and report.reason_codes != (
        "selection_summary_history_stable",
    ):
        raise ValueError("reason_codes must contain only the stable reason when ready")
    if report.history_status != "ready" and (
        "selection_summary_history_stable" in report.reason_codes
    ):
        raise ValueError("reason_codes must not contain stable reason unless ready")
    if report.source_report_count == 0:
        if report.first_generated_at is not None:
            raise ValueError("first_generated_at must be absent without source reports")
        if report.latest_generated_at is not None:
            raise ValueError("latest_generated_at must be absent without source reports")
        if report.history_span_seconds is not None:
            raise ValueError("history_span_seconds must be absent without source reports")
        if report.latest_age_seconds is not None:
            raise ValueError("latest_age_seconds must be absent without source reports")
    else:
        if report.first_generated_at is None:
            raise ValueError("first_generated_at is required with source reports")
        if report.latest_generated_at is None:
            raise ValueError("latest_generated_at is required with source reports")
        if report.history_span_seconds is None:
            raise ValueError("history_span_seconds is required with source reports")
        if report.latest_age_seconds is None:
            raise ValueError("latest_age_seconds is required with source reports")
        expected_span = _seconds_between(
            report.latest_generated_at,
            report.first_generated_at,
        )
        if report.history_span_seconds != expected_span:
            raise ValueError("history_span_seconds must match first/latest generated_at")
        expected_age = _seconds_between(report.generated_at, report.latest_generated_at)
        if report.latest_age_seconds != expected_age:
            raise ValueError("latest_age_seconds must match latest_generated_at")

    if (
        report.latest_selected_count
        + report.latest_pending_count
        + report.latest_rejected_count
        != report.latest_queue_count
    ):
        raise ValueError("latest counts must sum to latest_queue_count")
    if report.latest_skipped_count > report.latest_rejected_count:
        raise ValueError("latest_skipped_count must not exceed latest_rejected_count")
    if (
        report.aggregate_selected_count
        + report.aggregate_pending_count
        + report.aggregate_rejected_count
        != report.aggregate_queue_count
    ):
        raise ValueError("aggregate counts must sum to aggregate_queue_count")
    if report.aggregate_skipped_count > report.aggregate_rejected_count:
        raise ValueError("aggregate_skipped_count must not exceed aggregate_rejected_count")
    if report.latest_selected_share != _ratio(
        report.latest_selected_count,
        report.latest_queue_count,
    ):
        raise ValueError("latest_selected_share must match latest counts")
    if report.average_selected_share != _ratio(
        report.aggregate_selected_count,
        report.aggregate_queue_count,
    ):
        raise ValueError("average_selected_share must match aggregate counts")
    reason_code_total = sum(count for _reason_code, count in report.reason_code_counts)
    if reason_code_total < report.aggregate_queue_count:
        raise ValueError("reason_code_counts must cover aggregate rows")


def _normalize_config_versions(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("distinct_config_versions must be an iterable of strings")
    try:
        versions = tuple(value)
    except TypeError as exc:
        raise ValueError("distinct_config_versions must be an iterable of strings") from exc
    for version in versions:
        _require_canonical_string("distinct_config_versions", version)
    normalized = tuple(sorted(set(versions)))
    if versions != normalized:
        raise ValueError("distinct_config_versions must be sorted and unique")
    return versions


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, int], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc

    normalized_rows: list[tuple[str, int]] = []
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("reason_code_counts must contain reason/count tuples")
        reason_code, count = row
        _require_canonical_string("reason_code_counts", reason_code)
        _require_positive_int("reason_code_counts", count)
        normalized_rows.append((reason_code, count))
    normalized = tuple(normalized_rows)
    if normalized != tuple(sorted(normalized, key=lambda item: item[0])):
        raise ValueError("reason_code_counts must use deterministic ordering")
    if len({reason_code for reason_code, _count in normalized}) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO
    return _quantize(Decimal(numerator) / Decimal(denominator))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _seconds_between(later: datetime, earlier: datetime) -> int:
    seconds = (later - earlier) // timedelta(seconds=1)
    if seconds < 0:
        raise ValueError("source report generated_at must not be future dated")
    return seconds


def _normalize_optional_datetime(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_history_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_recommended_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RECOMMENDED_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known next step")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value == 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_int(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) is not int or value < 0:
        raise ValueError(f"{field_name} must be an int")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


__all__ = (
    "PaperProbabilitySelectionSummaryHistoryConfig",
    "PaperProbabilitySelectionSummaryHistoryReport",
    "build_paper_probability_selection_summary_history_report",
)
