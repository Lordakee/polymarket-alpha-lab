"""Pure gate reducer for probability selection/scorer agreement trends."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.probability_selection_scorer_agreement_trend import (
    AGREEMENT_STATUSES,
    ProbabilitySelectionScorerAgreementTrendReport,
    TREND_STATUSES,
)


DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_CONFIG_VERSION = (
    "probability-selection-scorer-agreement-trend-gate-v0"
)
GATE_STATUSES = ("pass", "watch", "blocked")
NEXT_STEP_BY_GATE_STATUS = {
    "pass": "allow_probability_selection_scorer_agreement_trend_review",
    "watch": "throttle_probability_selection_scorer_agreement_trend_review",
    "blocked": "block_probability_selection_scorer_agreement_trend_review",
}
PASS_REASON_CODE = "probability_selection_scorer_agreement_trend_gate_passed"
BLOCKED_REASON_CODES = frozenset(
    (
        "insufficient_probability_selection_scorer_agreement_trend_samples",
        "latest_probability_selection_scorer_agreement_trend_blocked",
        "repeated_probability_selection_scorer_agreement_trend_blocker",
    ),
)
WATCH_REASON_CODES = frozenset(
    (
        "latest_probability_selection_scorer_agreement_trend_watch",
        "repeated_probability_selection_scorer_agreement_trend_watch_threshold_exceeded",
        "repeated_probability_selection_scorer_agreement_trend_reason_threshold_exceeded",
        "stale_probability_selection_scorer_agreement_trend",
    ),
)
GATE_REASON_CODES = (
    frozenset((PASS_REASON_CODE,)) | BLOCKED_REASON_CODES | WATCH_REASON_CODES
)

__all__ = (
    "DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_CONFIG_VERSION",
    "ProbabilitySelectionScorerAgreementTrendGateConfig",
    "ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount",
    "ProbabilitySelectionScorerAgreementTrendGateReport",
    "build_probability_selection_scorer_agreement_trend_gate_report",
)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementTrendGateConfig:
    config_version: str = (
        DEFAULT_PROBABILITY_SELECTION_SCORER_AGREEMENT_TREND_GATE_CONFIG_VERSION
    )
    min_source_report_count: int = 3
    max_latest_status_streak_for_watch: int = 1
    max_latest_status_streak_for_block: int = 2
    max_trend_report_age_seconds: int = 86_400
    max_recurring_reason_code_count: int = 2
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilitySelectionScorerAgreementTrendGateConfig:
            raise TypeError(
                "ProbabilitySelectionScorerAgreementTrendGateConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilitySelectionScorerAgreementTrendGateConfig:
            raise ValueError(
                "config must be exactly "
                "ProbabilitySelectionScorerAgreementTrendGateConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_source_report_count",
            "max_latest_status_streak_for_watch",
            "max_latest_status_streak_for_block",
            "max_trend_report_age_seconds",
            "max_recurring_reason_code_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _validate_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount:
            raise TypeError(
                "ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount",
            )
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("report_count", self.report_count)
        _validate_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ProbabilitySelectionScorerAgreementTrendGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    trend_report_age_seconds: int
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount,
        ...,
    ]
    source_report_count: int
    source_trend_status: str
    source_recommended_next_step: str
    latest_agreement_status: str
    latest_agreement_status_streak: int
    aligned_report_count: int
    low_overlap_report_count: int
    gate_blocked_report_count: int
    missing_inputs_report_count: int
    insufficient_identifiers_report_count: int
    average_selected_count: Decimal
    average_scorer_candidate_count: Decimal
    latest_source_reason_codes: tuple[str, ...]
    recurring_source_reason_code_counts: tuple[tuple[str, int], ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilitySelectionScorerAgreementTrendGateReport:
            raise TypeError(
                "ProbabilitySelectionScorerAgreementTrendGateReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilitySelectionScorerAgreementTrendGateReport:
            raise ValueError(
                "gate report must be exactly "
                "ProbabilitySelectionScorerAgreementTrendGateReport",
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
        for field_name in (
            "source_report_count",
            "latest_agreement_status_streak",
            "aligned_report_count",
            "low_overlap_report_count",
            "gate_blocked_report_count",
            "missing_inputs_report_count",
            "insufficient_identifiers_report_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_trend_status("source_trend_status", self.source_trend_status)
        _require_canonical_string(
            "source_recommended_next_step",
            self.source_recommended_next_step,
        )
        _require_agreement_status(
            "latest_agreement_status",
            self.latest_agreement_status,
        )
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


def build_probability_selection_scorer_agreement_trend_gate_report(
    source_report: object,
    *,
    config: ProbabilitySelectionScorerAgreementTrendGateConfig,
    generated_at: datetime,
) -> ProbabilitySelectionScorerAgreementTrendGateReport:
    if type(source_report) is not ProbabilitySelectionScorerAgreementTrendReport:
        raise ValueError(
            "source_report must be exactly ProbabilitySelectionScorerAgreementTrendReport",
        )
    if type(config) is not ProbabilitySelectionScorerAgreementTrendGateConfig:
        raise ValueError(
            "config must be exactly ProbabilitySelectionScorerAgreementTrendGateConfig",
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
    return ProbabilitySelectionScorerAgreementTrendGateReport(
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
        source_report_count=source_report.source_report_count,
        source_trend_status=source_report.trend_status,
        source_recommended_next_step=source_report.recommended_next_step,
        latest_agreement_status=source_report.latest_agreement_status,
        latest_agreement_status_streak=source_report.latest_status_streak,
        aligned_report_count=source_report.aligned_report_count,
        low_overlap_report_count=source_report.low_overlap_report_count,
        gate_blocked_report_count=source_report.gate_blocked_report_count,
        missing_inputs_report_count=source_report.missing_inputs_report_count,
        insufficient_identifiers_report_count=(
            source_report.insufficient_identifiers_report_count
        ),
        average_selected_count=source_report.average_selected_count,
        average_scorer_candidate_count=source_report.average_scorer_candidate_count,
        latest_source_reason_codes=source_report.reason_codes,
        recurring_source_reason_code_counts=source_report.recurring_reason_code_counts,
        reason_codes=reason_codes,
    )


def _gate_reason_codes(
    source_report: ProbabilitySelectionScorerAgreementTrendReport,
    *,
    config: ProbabilitySelectionScorerAgreementTrendGateConfig,
    generated_at: datetime,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_report.source_report_count < config.min_source_report_count:
        reason_codes.append(
            "insufficient_probability_selection_scorer_agreement_trend_samples",
        )
    if source_report.latest_agreement_status == "gate_blocked":
        reason_codes.append(
            "latest_probability_selection_scorer_agreement_trend_blocked",
        )
    elif source_report.latest_agreement_status != "aligned":
        reason_codes.append("latest_probability_selection_scorer_agreement_trend_watch")
    if (
        source_report.latest_agreement_status == "gate_blocked"
        and source_report.latest_status_streak
        >= config.max_latest_status_streak_for_block
    ):
        reason_codes.append(
            "repeated_probability_selection_scorer_agreement_trend_blocker",
        )
    elif (
        source_report.latest_agreement_status != "aligned"
        and source_report.latest_status_streak
        > config.max_latest_status_streak_for_watch
    ):
        reason_codes.append(
            "repeated_probability_selection_scorer_agreement_trend_watch_threshold_exceeded",
        )
    if (
        _seconds_between(
            generated_at,
            source_report.generated_at,
            "trend_report_age_seconds",
        )
        > config.max_trend_report_age_seconds
    ):
        reason_codes.append("stale_probability_selection_scorer_agreement_trend")
    if any(
        count > config.max_recurring_reason_code_count
        for _, count in source_report.recurring_reason_code_counts
    ):
        reason_codes.append(
            "repeated_probability_selection_scorer_agreement_trend_reason_threshold_exceeded",
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
) -> tuple[ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount, ...]:
    return tuple(
        ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(reason_code, 1)
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
    report: ProbabilitySelectionScorerAgreementTrendGateReport,
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


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    if not value:
        raise ValueError("reason_code_counts must be nonempty")
    counts = tuple(value)
    for count in counts:
        if type(count) is not ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain exactly "
                "ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount values",
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


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite() or value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(Decimal("0.000001"))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(later: datetime, earlier: datetime, field_name: str) -> int:
    seconds = int((later - earlier).total_seconds())
    if seconds < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    return seconds


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_trend_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TREND_STATUSES:
        raise ValueError(f"{field_name} must be a known trend status")


def _require_agreement_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in AGREEMENT_STATUSES:
        raise ValueError(f"{field_name} must be a known agreement status")


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
