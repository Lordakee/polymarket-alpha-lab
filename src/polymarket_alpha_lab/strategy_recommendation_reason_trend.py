"""Pure paper recommendation reason-code trend reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any

from polymarket_alpha_lab.strategy_recommendation_bundle import (
    PaperStrategyRecommendationBundleReport,
)
from polymarket_alpha_lab.strategy_recommendation_explain import (
    NO_REASON_CODE,
    PaperStrategyRecommendationExplanationReport,
)
from polymarket_alpha_lab.strategy_recommendation_history import (
    PaperStrategyRecommendationHistoryReport,
)


RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DEFAULT_BLOCKED_REASON_CODES = (
    "blocked_forecast_quality",
    "blocked_risk_drawdown",
    "incomplete_data",
    "missing_cost_report",
)
REASON_TREND_STATUSES = ("stable", "watch", "blocked")


@dataclass(frozen=True)
class PaperStrategyRecommendationReasonTrendConfig:
    config_version: str
    max_blocked_reason_share: Decimal = Decimal("0.500000")
    max_no_reason_code_share: Decimal = Decimal("0.500000")
    top_reason_code_limit: int = 5
    blocked_reason_codes: tuple[str, ...] = DEFAULT_BLOCKED_REASON_CODES

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_blocked_reason_share",
            _normalize_probability_decimal(
                "max_blocked_reason_share",
                self.max_blocked_reason_share,
            ),
        )
        object.__setattr__(
            self,
            "max_no_reason_code_share",
            _normalize_probability_decimal(
                "max_no_reason_code_share",
                self.max_no_reason_code_share,
            ),
        )
        _require_positive_int("top_reason_code_limit", self.top_reason_code_limit)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
            ),
        )


@dataclass(frozen=True)
class PaperStrategyRecommendationReasonTrendSourceSummary:
    generated_at: datetime
    config_version: str
    primary_reason_code_counts: tuple[tuple[str, int], ...]
    reason_code_count: int
    no_reason_code_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "primary_reason_code_counts",
            _normalize_reason_code_counts(self.primary_reason_code_counts),
        )
        for field_name in (
            "reason_code_count",
            "no_reason_code_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.reason_code_count != _count_total(self.primary_reason_code_counts):
            raise ValueError("reason_code_count must match primary_reason_code_counts")
        if self.no_reason_code_count != _count_reason_code(
            self.primary_reason_code_counts,
            NO_REASON_CODE,
        ):
            raise ValueError(
                "no_reason_code_count must match primary_reason_code_counts",
            )


@dataclass(frozen=True)
class PaperStrategyRecommendationReasonTrendReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    latest_primary_reason_code_counts: tuple[tuple[str, int], ...]
    total_primary_reason_code_counts: tuple[tuple[str, int], ...]
    top_new_reason_codes: tuple[tuple[str, int], ...]
    persistent_reason_codes: tuple[str, ...]
    latest_reason_code_count: int
    latest_no_reason_code_count: int
    latest_blocked_reason_count: int
    latest_no_reason_code_share: Decimal | None
    latest_blocked_reason_share: Decimal | None
    max_blocked_reason_share: Decimal
    max_no_reason_code_share: Decimal
    top_reason_code_limit: int
    blocked_reason_codes: tuple[str, ...]
    status: str
    source_summaries: tuple[PaperStrategyRecommendationReasonTrendSourceSummary, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        object.__setattr__(
            self,
            "first_generated_at",
            _as_optional_utc(self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc(self.latest_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        object.__setattr__(
            self,
            "latest_primary_reason_code_counts",
            _normalize_reason_code_counts(self.latest_primary_reason_code_counts),
        )
        object.__setattr__(
            self,
            "total_primary_reason_code_counts",
            _normalize_reason_code_counts(self.total_primary_reason_code_counts),
        )
        object.__setattr__(
            self,
            "top_new_reason_codes",
            _normalize_reason_code_counts(self.top_new_reason_codes),
        )
        object.__setattr__(
            self,
            "persistent_reason_codes",
            _normalize_reason_codes(
                "persistent_reason_codes",
                self.persistent_reason_codes,
            ),
        )
        for field_name in (
            "latest_reason_code_count",
            "latest_no_reason_code_count",
            "latest_blocked_reason_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_no_reason_code_share",
            _normalize_optional_probability_decimal(
                "latest_no_reason_code_share",
                self.latest_no_reason_code_share,
            ),
        )
        object.__setattr__(
            self,
            "latest_blocked_reason_share",
            _normalize_optional_probability_decimal(
                "latest_blocked_reason_share",
                self.latest_blocked_reason_share,
            ),
        )
        object.__setattr__(
            self,
            "max_blocked_reason_share",
            _normalize_probability_decimal(
                "max_blocked_reason_share",
                self.max_blocked_reason_share,
            ),
        )
        object.__setattr__(
            self,
            "max_no_reason_code_share",
            _normalize_probability_decimal(
                "max_no_reason_code_share",
                self.max_no_reason_code_share,
            ),
        )
        _require_positive_int("top_reason_code_limit", self.top_reason_code_limit)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
            ),
        )
        if self.status not in REASON_TREND_STATUSES:
            raise ValueError("status must be a known reason trend status")
        object.__setattr__(
            self,
            "source_summaries",
            _normalize_source_summaries(self.source_summaries),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def build_paper_strategy_recommendation_reason_trend_report(
    reports: list[
        PaperStrategyRecommendationBundleReport
        | PaperStrategyRecommendationExplanationReport
        | PaperStrategyRecommendationHistoryReport
    ]
    | tuple[
        PaperStrategyRecommendationBundleReport
        | PaperStrategyRecommendationExplanationReport
        | PaperStrategyRecommendationHistoryReport,
        ...,
    ],
    *,
    config: PaperStrategyRecommendationReasonTrendConfig,
    generated_at: datetime,
) -> PaperStrategyRecommendationReasonTrendReport:
    if type(config) is not PaperStrategyRecommendationReasonTrendConfig:
        raise ValueError("config must be a PaperStrategyRecommendationReasonTrendConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    normalized_reports = _normalize_reports(reports)
    source_summaries = tuple(
        _source_summary_from_report(report)
        for report in normalized_reports
    )
    latest_summary = source_summaries[-1] if source_summaries else None
    latest_counts = (
        latest_summary.primary_reason_code_counts
        if latest_summary is not None
        else ()
    )
    latest_reason_count = _count_total(latest_counts)
    latest_no_reason_count = _count_reason_code(latest_counts, NO_REASON_CODE)
    latest_blocked_reason_count = _blocked_reason_count(
        latest_counts,
        config.blocked_reason_codes,
    )
    top_new_reason_codes = _top_new_reason_codes(
        source_summaries,
        config.top_reason_code_limit,
    )
    latest_no_reason_share = _ratio(latest_no_reason_count, latest_reason_count)
    latest_blocked_reason_share = _ratio(
        latest_blocked_reason_count,
        latest_reason_count,
    )

    return PaperStrategyRecommendationReasonTrendReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_count=len(source_summaries),
        first_generated_at=(
            source_summaries[0].generated_at
            if source_summaries
            else None
        ),
        latest_generated_at=(
            latest_summary.generated_at
            if latest_summary is not None
            else None
        ),
        latest_primary_reason_code_counts=latest_counts,
        total_primary_reason_code_counts=_total_reason_code_counts(source_summaries),
        top_new_reason_codes=top_new_reason_codes,
        persistent_reason_codes=_persistent_reason_codes(source_summaries),
        latest_reason_code_count=latest_reason_count,
        latest_no_reason_code_count=latest_no_reason_count,
        latest_blocked_reason_count=latest_blocked_reason_count,
        latest_no_reason_code_share=latest_no_reason_share,
        latest_blocked_reason_share=latest_blocked_reason_share,
        max_blocked_reason_share=config.max_blocked_reason_share,
        max_no_reason_code_share=config.max_no_reason_code_share,
        top_reason_code_limit=config.top_reason_code_limit,
        blocked_reason_codes=config.blocked_reason_codes,
        status=_status(
            latest_blocked_reason_share=latest_blocked_reason_share,
            latest_no_reason_code_share=latest_no_reason_share,
            max_blocked_reason_share=config.max_blocked_reason_share,
            max_no_reason_code_share=config.max_no_reason_code_share,
            top_new_reason_codes=top_new_reason_codes,
        ),
        source_summaries=source_summaries,
    )


def _normalize_reports(
    reports: list[
        PaperStrategyRecommendationBundleReport
        | PaperStrategyRecommendationExplanationReport
        | PaperStrategyRecommendationHistoryReport
    ]
    | tuple[
        PaperStrategyRecommendationBundleReport
        | PaperStrategyRecommendationExplanationReport
        | PaperStrategyRecommendationHistoryReport,
        ...,
    ],
) -> tuple[
    PaperStrategyRecommendationBundleReport
    | PaperStrategyRecommendationExplanationReport
    | PaperStrategyRecommendationHistoryReport,
    ...,
]:
    if type(reports) not in (list, tuple):
        raise ValueError("reports must be a list or tuple of recommendation reports")
    normalized = tuple(reports)
    for report in normalized:
        if type(report) not in (
            PaperStrategyRecommendationBundleReport,
            PaperStrategyRecommendationExplanationReport,
            PaperStrategyRecommendationHistoryReport,
        ):
            raise ValueError(
                "reports must contain only recommendation report values",
            )
        _validate_report_flags(report)
    return normalized


def _validate_report_flags(report: Any) -> None:
    if report.paper_only is not True:
        raise ValueError("reports must contain paper_only recommendation reports")
    if report.report_only is not True:
        raise ValueError("reports must contain report_only recommendation reports")
    if report.readonly is not True:
        raise ValueError("reports must contain readonly recommendation reports")


def _source_summary_from_report(
    report: PaperStrategyRecommendationBundleReport
    | PaperStrategyRecommendationExplanationReport
    | PaperStrategyRecommendationHistoryReport,
) -> PaperStrategyRecommendationReasonTrendSourceSummary:
    if type(report) is PaperStrategyRecommendationBundleReport:
        counts = _normalize_reason_code_counts(report.primary_reason_code_counts or ())
        config_version = report.config_version
    elif type(report) is PaperStrategyRecommendationExplanationReport:
        counts = _normalize_reason_code_counts(report.primary_reason_code_counts or ())
        config_version = report.source_config_version
    else:
        counts = ()
        config_version = report.config_version
    return PaperStrategyRecommendationReasonTrendSourceSummary(
        generated_at=report.generated_at,
        config_version=config_version,
        primary_reason_code_counts=counts,
        reason_code_count=_count_total(counts),
        no_reason_code_count=_count_reason_code(counts, NO_REASON_CODE),
    )


def _total_reason_code_counts(
    source_summaries: tuple[PaperStrategyRecommendationReasonTrendSourceSummary, ...],
) -> tuple[tuple[str, int], ...]:
    totals: dict[str, int] = {}
    for summary in source_summaries:
        for reason_code, count in summary.primary_reason_code_counts:
            totals[reason_code] = totals.get(reason_code, 0) + count
    return _sorted_counts(totals)


def _top_new_reason_codes(
    source_summaries: tuple[PaperStrategyRecommendationReasonTrendSourceSummary, ...],
    limit: int,
) -> tuple[tuple[str, int], ...]:
    if len(source_summaries) < 2:
        return ()
    prior_reason_codes = set()
    for summary in source_summaries[:-1]:
        prior_reason_codes.update(
            reason_code
            for reason_code, count in summary.primary_reason_code_counts
            if count > 0
        )
    latest_new_counts = {
        reason_code: count
        for reason_code, count in source_summaries[-1].primary_reason_code_counts
        if count > 0 and reason_code not in prior_reason_codes
    }
    return _sorted_counts(latest_new_counts)[:limit]


def _persistent_reason_codes(
    source_summaries: tuple[PaperStrategyRecommendationReasonTrendSourceSummary, ...],
) -> tuple[str, ...]:
    nonempty_reason_sets = tuple(
        frozenset(
            reason_code
            for reason_code, count in summary.primary_reason_code_counts
            if count > 0
        )
        for summary in source_summaries
        if summary.reason_code_count > 0
    )
    if not nonempty_reason_sets:
        return ()
    persistent = set(nonempty_reason_sets[0])
    for reason_codes in nonempty_reason_sets[1:]:
        persistent &= reason_codes
    return tuple(sorted(persistent))


def _status(
    *,
    latest_blocked_reason_share: Decimal | None,
    latest_no_reason_code_share: Decimal | None,
    max_blocked_reason_share: Decimal,
    max_no_reason_code_share: Decimal,
    top_new_reason_codes: tuple[tuple[str, int], ...],
) -> str:
    if (
        latest_blocked_reason_share is not None
        and latest_blocked_reason_share > max_blocked_reason_share
    ):
        return "blocked"
    if (
        latest_no_reason_code_share is not None
        and latest_no_reason_code_share > max_no_reason_code_share
    ):
        return "blocked"
    if top_new_reason_codes:
        return "watch"
    return "stable"


def _validate_report_consistency(
    report: PaperStrategyRecommendationReasonTrendReport,
) -> None:
    if report.source_report_count != len(report.source_summaries):
        raise ValueError("source_report_count must match source_summaries")
    if report.source_report_count == 0:
        _validate_empty_report(report)
        return

    first = report.source_summaries[0]
    latest = report.source_summaries[-1]
    expected_latest_counts = latest.primary_reason_code_counts
    expected_latest_reason_count = _count_total(expected_latest_counts)
    expected_latest_no_reason_count = _count_reason_code(
        expected_latest_counts,
        NO_REASON_CODE,
    )
    expected_latest_blocked_reason_count = _blocked_reason_count(
        expected_latest_counts,
        report.blocked_reason_codes,
    )
    expected_latest_no_reason_share = _ratio(
        expected_latest_no_reason_count,
        expected_latest_reason_count,
    )
    expected_latest_blocked_reason_share = _ratio(
        expected_latest_blocked_reason_count,
        expected_latest_reason_count,
    )
    expected_top_new_reason_codes = _top_new_reason_codes(
        report.source_summaries,
        report.top_reason_code_limit,
    )

    if report.first_generated_at != first.generated_at:
        raise ValueError("first_generated_at must match source_summaries")
    if report.latest_generated_at != latest.generated_at:
        raise ValueError("latest_generated_at must match source_summaries")
    if report.latest_primary_reason_code_counts != expected_latest_counts:
        raise ValueError(
            "latest_primary_reason_code_counts must match source_summaries",
        )
    if report.total_primary_reason_code_counts != _total_reason_code_counts(
        report.source_summaries,
    ):
        raise ValueError(
            "total_primary_reason_code_counts must match source_summaries",
        )
    if report.top_new_reason_codes != expected_top_new_reason_codes:
        raise ValueError("top_new_reason_codes must match source_summaries")
    if report.persistent_reason_codes != _persistent_reason_codes(
        report.source_summaries,
    ):
        raise ValueError("persistent_reason_codes must match source_summaries")
    if report.latest_reason_code_count != expected_latest_reason_count:
        raise ValueError("latest_reason_code_count must match source_summaries")
    if report.latest_no_reason_code_count != expected_latest_no_reason_count:
        raise ValueError(
            "latest_no_reason_code_count must match source_summaries",
        )
    if report.latest_blocked_reason_count != expected_latest_blocked_reason_count:
        raise ValueError(
            "latest_blocked_reason_count must match source_summaries",
        )
    if report.latest_no_reason_code_share != expected_latest_no_reason_share:
        raise ValueError(
            "latest_no_reason_code_share must match source_summaries",
        )
    if report.latest_blocked_reason_share != expected_latest_blocked_reason_share:
        raise ValueError(
            "latest_blocked_reason_share must match source_summaries",
        )
    if report.status != _status(
        latest_blocked_reason_share=expected_latest_blocked_reason_share,
        latest_no_reason_code_share=expected_latest_no_reason_share,
        max_blocked_reason_share=report.max_blocked_reason_share,
        max_no_reason_code_share=report.max_no_reason_code_share,
        top_new_reason_codes=expected_top_new_reason_codes,
    ):
        raise ValueError("status must match reason trend thresholds")


def _validate_empty_report(
    report: PaperStrategyRecommendationReasonTrendReport,
) -> None:
    if report.first_generated_at is not None or report.latest_generated_at is not None:
        raise ValueError("generated_at bounds must be absent without reports")
    if report.latest_primary_reason_code_counts:
        raise ValueError(
            "latest_primary_reason_code_counts must be empty without reports",
        )
    if report.total_primary_reason_code_counts:
        raise ValueError(
            "total_primary_reason_code_counts must be empty without reports",
        )
    if report.top_new_reason_codes:
        raise ValueError("top_new_reason_codes must be empty without reports")
    if report.persistent_reason_codes:
        raise ValueError("persistent_reason_codes must be empty without reports")
    for field_name in (
        "latest_reason_code_count",
        "latest_no_reason_code_count",
        "latest_blocked_reason_count",
    ):
        if getattr(report, field_name) != 0:
            raise ValueError(f"{field_name} must be zero without reports")
    if (
        report.latest_no_reason_code_share is not None
        or report.latest_blocked_reason_share is not None
    ):
        raise ValueError("latest shares must be absent without reports")
    if report.status != "stable":
        raise ValueError("status must be stable without reports")


def _normalize_source_summaries(
    source_summaries: tuple[
        PaperStrategyRecommendationReasonTrendSourceSummary,
        ...,
    ],
) -> tuple[PaperStrategyRecommendationReasonTrendSourceSummary, ...]:
    if isinstance(source_summaries, (str, bytes)):
        raise ValueError("source_summaries must be an iterable")
    try:
        summaries = tuple(source_summaries)
    except TypeError as exc:
        raise ValueError("source_summaries must be an iterable") from exc
    for summary in summaries:
        if type(summary) is not PaperStrategyRecommendationReasonTrendSourceSummary:
            raise ValueError(
                "source_summaries must contain "
                "PaperStrategyRecommendationReasonTrendSourceSummary values",
            )
    return tuple(
        PaperStrategyRecommendationReasonTrendSourceSummary(
            generated_at=summary.generated_at,
            config_version=summary.config_version,
            primary_reason_code_counts=summary.primary_reason_code_counts,
            reason_code_count=summary.reason_code_count,
            no_reason_code_count=summary.no_reason_code_count,
        )
        for summary in summaries
    )


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return tuple(sorted(set(reason_codes)))


def _normalize_reason_code_counts(
    values: tuple[tuple[str, int], ...],
) -> tuple[tuple[str, int], ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("primary_reason_code_counts must be an iterable")
    try:
        counts = tuple(values)
    except TypeError as exc:
        raise ValueError("primary_reason_code_counts must be an iterable") from exc
    total_by_reason_code: dict[str, int] = {}
    for item in counts:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError(
                "primary_reason_code_counts entries must be reason/count pairs",
            )
        reason_code, count = item
        _require_canonical_string("primary_reason_code", reason_code)
        _require_nonnegative_int("primary_reason_code count", count)
        if count == 0:
            continue
        total_by_reason_code[reason_code] = (
            total_by_reason_code.get(reason_code, 0) + count
        )
    return _sorted_counts(total_by_reason_code)


def _sorted_counts(counts: dict[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(
        sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        ),
    )


def _blocked_reason_count(
    counts: tuple[tuple[str, int], ...],
    blocked_reason_codes: tuple[str, ...],
) -> int:
    blocked = frozenset(blocked_reason_codes)
    return sum(count for reason_code, count in counts if reason_code in blocked)


def _count_total(counts: tuple[tuple[str, int], ...]) -> int:
    return sum(count for _, count in counts)


def _count_reason_code(
    counts: tuple[tuple[str, int], ...],
    target_reason_code: str,
) -> int:
    return sum(count for reason_code, count in counts if reason_code == target_reason_code)


def _ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        RATIO_QUANTUM,
        rounding=ROUND_HALF_EVEN,
    )


def _as_utc(value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(value: datetime | None) -> datetime | None:
    return None if value is None else _as_utc(value)


def _normalize_probability_decimal(
    field_name: str,
    value: Any,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value.quantize(RATIO_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_optional_probability_decimal(
    field_name: str,
    value: Any,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability_decimal(field_name, value)


def _require_canonical_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: Any) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


__all__ = (
    "PaperStrategyRecommendationReasonTrendConfig",
    "PaperStrategyRecommendationReasonTrendReport",
    "PaperStrategyRecommendationReasonTrendSourceSummary",
    "build_paper_strategy_recommendation_reason_trend_report",
)
