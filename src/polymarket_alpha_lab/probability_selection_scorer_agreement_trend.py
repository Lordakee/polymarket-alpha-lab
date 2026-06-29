"""Pure probability selection/scorer agreement trend reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polymarket_alpha_lab.probability_selection_scorer_agreement import (
    ProbabilitySelectionScorerAgreementReport,
)


DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_CONFIG_VERSION = (
    "probability-selection-scorer-agreement-trend-v0"
)
ZERO = Decimal("0.000000")
QUANTUM = Decimal("0.000001")
AGREEMENT_STATUSES = (
    "aligned",
    "gate_blocked",
    "insufficient_identifiers",
    "low_overlap",
    "missing_inputs",
)
TREND_STATUSES = (
    "insufficient_history",
    "blocked",
    "watch",
    "stable",
)
NEXT_STEP_BY_TREND_STATUS = {
    "insufficient_history": "collect_more_history",
    "blocked": "review_scorer_gate",
    "watch": "continue_monitoring",
    "stable": "continue_monitoring",
}
NEXT_STEP_BY_LATEST_AGREEMENT_STATUS = {
    "aligned": "continue_monitoring",
    "gate_blocked": "review_scorer_gate",
    "insufficient_identifiers": "enrich_inputs",
    "low_overlap": "review_selection_scorer_disagreement",
    "missing_inputs": "enrich_inputs",
}
STABLE_SOURCE_REASON_CODE = "selection_scorer_aligned"
TREND_REASON_CODES = (
    "agreement_trend_stable",
    "insufficient_history_count",
    "latest_agreement_gate_blocked",
    "latest_agreement_insufficient_identifiers",
    "latest_agreement_low_overlap",
    "latest_agreement_missing_inputs",
    "recurring_agreement_reason_codes",
    "repeated_latest_agreement_blocker",
)
TREND_REASON_CODE_SET = frozenset(TREND_REASON_CODES)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementTrendConfig:
    config_version: str = (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_CONFIG_VERSION
    )
    min_history_count: int = 3
    blocking_status_streak_threshold: int = 2
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilitySelectionScorerAgreementTrendConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilitySelectionScorerAgreementTrendConfig:
            raise ValueError(
                "config must be exactly "
                "ProbabilitySelectionScorerAgreementTrendConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_positive_int("min_history_count", self.min_history_count)
        _require_positive_int(
            "blocking_status_streak_threshold",
            self.blocking_status_streak_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementTrendReport:
    generated_at: datetime
    config_version: str
    source_report_count: int
    first_generated_at: datetime
    latest_generated_at: datetime
    history_span_seconds: int
    latest_agreement_status: str
    latest_status_streak: int
    aligned_report_count: int
    low_overlap_report_count: int
    gate_blocked_report_count: int
    missing_inputs_report_count: int
    insufficient_identifiers_report_count: int
    average_selected_count: Decimal
    average_scorer_candidate_count: Decimal
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
            "ProbabilitySelectionScorerAgreementTrendReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilitySelectionScorerAgreementTrendReport:
            raise ValueError(
                "trend report must be exactly "
                "ProbabilitySelectionScorerAgreementTrendReport",
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
        _require_positive_int("source_report_count", self.source_report_count)
        _require_nonnegative_int("history_span_seconds", self.history_span_seconds)
        _require_agreement_status("latest_agreement_status", self.latest_agreement_status)
        _require_positive_int("latest_status_streak", self.latest_status_streak)
        for field_name in (
            "aligned_report_count",
            "low_overlap_report_count",
            "gate_blocked_report_count",
            "missing_inputs_report_count",
            "insufficient_identifiers_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "average_selected_count",
            _normalize_nonnegative_decimal(
                "average_selected_count",
                self.average_selected_count,
            ),
        )
        object.__setattr__(
            self,
            "average_scorer_candidate_count",
            _normalize_nonnegative_decimal(
                "average_scorer_candidate_count",
                self.average_scorer_candidate_count,
            ),
        )
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


def build_probability_selection_scorer_agreement_trend_report(
    agreement_reports: object,
    *,
    config: ProbabilitySelectionScorerAgreementTrendConfig,
    generated_at: datetime,
) -> ProbabilitySelectionScorerAgreementTrendReport:
    if type(config) is not ProbabilitySelectionScorerAgreementTrendConfig:
        raise ValueError(
            "config must be exactly ProbabilitySelectionScorerAgreementTrendConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    reports = _normalize_agreement_reports(agreement_reports)
    _require_chronological_reports(reports)

    latest_report = reports[-1]
    latest_agreement_status = latest_report.agreement_status
    recurring_reason_code_counts = _recurring_reason_code_counts(reports)
    latest_status_streak = _latest_status_streak(reports)
    reason_codes = _trend_reason_codes(
        reports=reports,
        config=config,
        latest_status_streak=latest_status_streak,
        recurring_reason_code_counts=recurring_reason_code_counts,
    )
    trend_status = _trend_status(reason_codes)

    return ProbabilitySelectionScorerAgreementTrendReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_report_count=len(reports),
        first_generated_at=reports[0].generated_at,
        latest_generated_at=latest_report.generated_at,
        history_span_seconds=_seconds_between(
            latest_report.generated_at,
            reports[0].generated_at,
            "history_span_seconds",
        ),
        latest_agreement_status=latest_agreement_status,
        latest_status_streak=latest_status_streak,
        aligned_report_count=_status_count(reports, "aligned"),
        low_overlap_report_count=_status_count(reports, "low_overlap"),
        gate_blocked_report_count=_status_count(reports, "gate_blocked"),
        missing_inputs_report_count=_status_count(reports, "missing_inputs"),
        insufficient_identifiers_report_count=_status_count(
            reports,
            "insufficient_identifiers",
        ),
        average_selected_count=_average_count(reports, "selected_count"),
        average_scorer_candidate_count=_average_count(
            reports,
            "scorer_candidate_count",
        ),
        recurring_reason_code_counts=recurring_reason_code_counts,
        trend_status=trend_status,
        recommended_next_step=_recommended_next_step(
            trend_status=trend_status,
            latest_agreement_status=latest_agreement_status,
        ),
        reason_codes=reason_codes,
    )


def _normalize_agreement_reports(
    value: object,
) -> tuple[ProbabilitySelectionScorerAgreementReport, ...]:
    if type(value) is not tuple:
        raise ValueError("agreement_reports must be a tuple")
    if not value:
        raise ValueError("agreement_reports must be nonempty")
    reports = tuple(value)
    for index, report in enumerate(reports):
        if type(report) is not ProbabilitySelectionScorerAgreementReport:
            raise ValueError(
                "agreement_reports must contain exactly "
                "ProbabilitySelectionScorerAgreementReport values",
            )
        _validate_source_agreement_report(index, report)
    return reports


def _validate_source_agreement_report(
    index: int,
    report: ProbabilitySelectionScorerAgreementReport,
) -> None:
    label = f"source agreement_reports.{index}"
    _require_hard_flags(label, report)
    _as_utc(f"{label}.generated_at", report.generated_at)
    _require_agreement_status(f"{label}.agreement_status", report.agreement_status)
    for field_name in (
        "selected_count",
        "scorer_candidate_count",
        "selected_market_overlap_count",
        "selected_condition_overlap_count",
        "rejected_but_scored_count",
        "scored_but_unselected_count",
    ):
        _require_nonnegative_int(f"{label}.{field_name}", getattr(report, field_name))
    _normalize_reason_codes(f"{label}.reason_codes", report.reason_codes)


def _require_chronological_reports(
    reports: tuple[ProbabilitySelectionScorerAgreementReport, ...],
) -> None:
    previous_generated_at: datetime | None = None
    for report in reports:
        generated_at = _as_utc("source agreement generated_at", report.generated_at)
        if previous_generated_at is not None and generated_at < previous_generated_at:
            raise ValueError("agreement_reports must be chronological by generated_at")
        previous_generated_at = generated_at


def _status_count(
    reports: tuple[ProbabilitySelectionScorerAgreementReport, ...],
    status: str,
) -> int:
    return sum(1 for report in reports if report.agreement_status == status)


def _average_count(
    reports: tuple[ProbabilitySelectionScorerAgreementReport, ...],
    field_name: str,
) -> Decimal:
    total = sum(getattr(report, field_name) for report in reports)
    return _quantize(Decimal(total) / Decimal(len(reports)))


def _recurring_reason_code_counts(
    reports: tuple[ProbabilitySelectionScorerAgreementReport, ...],
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


def _latest_status_streak(
    reports: tuple[ProbabilitySelectionScorerAgreementReport, ...],
) -> int:
    latest_status = reports[-1].agreement_status
    count = 0
    for report in reversed(reports):
        if report.agreement_status != latest_status:
            break
        count += 1
    return count


def _trend_reason_codes(
    *,
    reports: tuple[ProbabilitySelectionScorerAgreementReport, ...],
    config: ProbabilitySelectionScorerAgreementTrendConfig,
    latest_status_streak: int,
    recurring_reason_code_counts: tuple[tuple[str, int], ...],
) -> tuple[str, ...]:
    latest_status = reports[-1].agreement_status
    reason_codes: list[str] = []
    if len(reports) < config.min_history_count:
        reason_codes.append("insufficient_history_count")
    if latest_status == "gate_blocked":
        reason_codes.append("latest_agreement_gate_blocked")
    elif latest_status == "insufficient_identifiers":
        reason_codes.append("latest_agreement_insufficient_identifiers")
    elif latest_status == "low_overlap":
        reason_codes.append("latest_agreement_low_overlap")
    elif latest_status == "missing_inputs":
        reason_codes.append("latest_agreement_missing_inputs")
    if _is_repeated_blocker(
        latest_status,
        latest_status_streak=latest_status_streak,
        threshold=config.blocking_status_streak_threshold,
    ):
        reason_codes.append("repeated_latest_agreement_blocker")
    if recurring_reason_code_counts:
        reason_codes.append("recurring_agreement_reason_codes")
    if not reason_codes:
        reason_codes.append("agreement_trend_stable")
    return tuple(reason_codes)


def _is_repeated_blocker(
    latest_status: str,
    *,
    latest_status_streak: int,
    threshold: int,
) -> bool:
    return latest_status == "gate_blocked" and latest_status_streak >= threshold


def _trend_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("agreement_trend_stable",):
        return "stable"
    if "insufficient_history_count" in reason_codes:
        return "insufficient_history"
    if "repeated_latest_agreement_blocker" in reason_codes:
        return "blocked"
    return "watch"


def _recommended_next_step(
    *,
    trend_status: str,
    latest_agreement_status: str,
) -> str:
    if trend_status == "insufficient_history":
        return NEXT_STEP_BY_TREND_STATUS[trend_status]
    if trend_status == "blocked":
        return "review_scorer_gate"
    return NEXT_STEP_BY_LATEST_AGREEMENT_STATUS[latest_agreement_status]


def _validate_trend_report(
    report: ProbabilitySelectionScorerAgreementTrendReport,
) -> None:
    if report.latest_status_streak > report.source_report_count:
        raise ValueError("latest_status_streak must not exceed source_report_count")
    aggregate_status_count = (
        report.aligned_report_count
        + report.low_overlap_report_count
        + report.gate_blocked_report_count
        + report.missing_inputs_report_count
        + report.insufficient_identifiers_report_count
    )
    if aggregate_status_count != report.source_report_count:
        raise ValueError("agreement status counts must equal source_report_count")
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
            raise ValueError("reason_codes must be known agreement trend reasons")
    if report.trend_status != _trend_status(report.reason_codes):
        raise ValueError("trend_status must match reason_codes")
    if report.recommended_next_step != _recommended_next_step(
        trend_status=report.trend_status,
        latest_agreement_status=report.latest_agreement_status,
    ):
        raise ValueError("recommended_next_step must match trend_status")
    if report.reason_codes == ("agreement_trend_stable",):
        if report.trend_status != "stable":
            raise ValueError("agreement_trend_stable requires stable trend_status")
        if report.latest_agreement_status != "aligned":
            raise ValueError("agreement_trend_stable requires aligned latest status")
        if report.recurring_reason_code_counts:
            raise ValueError("recurring_reason_code_counts must be empty for stable trends")
    elif "agreement_trend_stable" in report.reason_codes:
        raise ValueError("reason_codes must not mix stable and non-stable reasons")
    _validate_latest_status_reason(report)
    _validate_recurring_reason_codes(report)


def _validate_latest_status_reason(
    report: ProbabilitySelectionScorerAgreementTrendReport,
) -> None:
    reason_by_status = {
        "gate_blocked": "latest_agreement_gate_blocked",
        "insufficient_identifiers": "latest_agreement_insufficient_identifiers",
        "low_overlap": "latest_agreement_low_overlap",
        "missing_inputs": "latest_agreement_missing_inputs",
    }
    expected_reason = reason_by_status.get(report.latest_agreement_status)
    if expected_reason is not None and expected_reason not in report.reason_codes:
        raise ValueError("latest_agreement_status requires matching reason")
    for status, reason_code in reason_by_status.items():
        if reason_code in report.reason_codes and report.latest_agreement_status != status:
            raise ValueError("latest_agreement_status must support matching reason")
    if "repeated_latest_agreement_blocker" in report.reason_codes:
        if report.latest_agreement_status != "gate_blocked":
            raise ValueError("repeated_latest_agreement_blocker requires gate_blocked")
        if report.trend_status != "blocked":
            raise ValueError("repeated_latest_agreement_blocker requires blocked status")


def _validate_recurring_reason_codes(
    report: ProbabilitySelectionScorerAgreementTrendReport,
) -> None:
    for _, count in report.recurring_reason_code_counts:
        if count <= 1:
            raise ValueError("recurring_reason_code_counts must exceed one")
        if count > report.source_report_count:
            raise ValueError(
                "recurring_reason_code_counts must not exceed source_report_count",
            )
    if (
        report.recurring_reason_code_counts
        and "recurring_agreement_reason_codes" not in report.reason_codes
    ):
        raise ValueError(
            "recurring_reason_code_counts require recurring reason code",
        )
    if (
        "recurring_agreement_reason_codes" in report.reason_codes
        and not report.recurring_reason_code_counts
    ):
        raise ValueError(
            "recurring_reason_code_counts must support recurring reason code",
        )


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


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


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


def _require_agreement_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in AGREEMENT_STATUSES:
        raise ValueError(f"{field_name} must be a known agreement status")


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
    "DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_CONFIG_VERSION",
    "ProbabilitySelectionScorerAgreementTrendConfig",
    "ProbabilitySelectionScorerAgreementTrendReport",
    "build_probability_selection_scorer_agreement_trend_report",
)
