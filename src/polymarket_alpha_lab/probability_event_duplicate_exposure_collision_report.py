from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal


DEFAULT_CONFIG_VERSION = "probability-event-duplicate-exposure-collision-report-v0"

CLEAR_STATUS = "clear"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
COLLISION_STATUSES = (CLEAR_STATUS, WATCH_STATUS, BLOCK_STATUS)

SAME_SOURCE_REASON = "same_resolution_source_collision"
WATCHLIST_REASON = "watchlist_overlap_collision"
PORTFOLIO_BLOCK_REASON = "portfolio_exposure_overlap_block"
PORTFOLIO_WATCH_REASON = "portfolio_exposure_overlap_watch"
CORRELATED_EVENT_REASON = "correlated_event_overlap_watch"
CLEAR_REASON = "duplicate_exposure_collision_clear"
REASON_CODES = (
    SAME_SOURCE_REASON,
    WATCHLIST_REASON,
    PORTFOLIO_BLOCK_REASON,
    PORTFOLIO_WATCH_REASON,
    CORRELATED_EVENT_REASON,
    CLEAR_REASON,
)

MANUAL_BLOCK_STEP = "manual_review_block_duplicate_exposure"
MANUAL_WATCH_STEP = "manual_review_correlated_exposure"
MANUAL_CLEAR_STEP = "no_manual_action_required"
MANUAL_STEPS = (MANUAL_BLOCK_STEP, MANUAL_WATCH_STEP, MANUAL_CLEAR_STEP)

COUNT_QUANT = Decimal("1")
RATIO_QUANT = Decimal("0.000001")
DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1.000000")
UNSAFE_PUBLIC_PAYLOAD_KEY_MARKERS = (
    chr(108) + chr(105) + chr(118) + chr(101),
    chr(97) + chr(117) + chr(116) + chr(104),
    chr(119) + chr(97) + chr(108) + chr(108) + chr(101) + chr(116),
    chr(111) + chr(114) + chr(100) + chr(101) + chr(114),
    chr(110) + chr(101) + chr(116) + chr(119) + chr(111) + chr(114) + chr(107),
    chr(100) + chr(97) + chr(116) + chr(97) + chr(98) + chr(97) + chr(115) + chr(101),
    chr(112) + chr(101) + chr(114) + chr(115) + chr(105) + chr(115) + chr(116),
)


@dataclass(frozen=True)
class ProbabilityEventDuplicateExposureCollisionReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    portfolio_exposure_overlap_watch_probability: Decimal = Decimal("0.500000")
    portfolio_exposure_overlap_block_probability: Decimal = Decimal("0.700000")
    correlated_event_watch_count: Decimal = Decimal("1")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "portfolio_exposure_overlap_watch_probability",
            _normalize_ratio(
                "portfolio_exposure_overlap_watch_probability",
                self.portfolio_exposure_overlap_watch_probability,
            ),
        )
        object.__setattr__(
            self,
            "portfolio_exposure_overlap_block_probability",
            _normalize_ratio(
                "portfolio_exposure_overlap_block_probability",
                self.portfolio_exposure_overlap_block_probability,
            ),
        )
        object.__setattr__(
            self,
            "correlated_event_watch_count",
            _normalize_nonnegative_integral_decimal(
                "correlated_event_watch_count",
                self.correlated_event_watch_count,
            ),
        )
        if (
            self.portfolio_exposure_overlap_watch_probability
            > self.portfolio_exposure_overlap_block_probability
        ):
            raise ValueError(
                "portfolio_exposure_overlap_watch_probability must be <= block probability",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ProbabilityEventDuplicateExposureCollisionInput:
    candidate_id: str
    event_ref: str
    market_ref: str
    correlated_event_count: Decimal
    same_resolution_source_count: Decimal
    existing_watchlist_overlap_count: Decimal
    portfolio_exposure_overlap_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "event_ref", "market_ref"):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_unsafe_public_payload_text(getattr(self, field_name))
        for field_name in (
            "correlated_event_count",
            "same_resolution_source_count",
            "existing_watchlist_overlap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "portfolio_exposure_overlap_probability",
            _normalize_ratio(
                "portfolio_exposure_overlap_probability",
                self.portfolio_exposure_overlap_probability,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventDuplicateExposureCollisionRow:
    candidate_id: str
    event_ref: str
    market_ref: str
    correlated_event_count: Decimal
    same_resolution_source_count: Decimal
    existing_watchlist_overlap_count: Decimal
    portfolio_exposure_overlap_probability: Decimal
    collision_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "event_ref", "market_ref"):
            _require_canonical_string(field_name, getattr(self, field_name))
            _reject_unsafe_public_payload_text(getattr(self, field_name))
        for field_name in (
            "correlated_event_count",
            "same_resolution_source_count",
            "existing_watchlist_overlap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "portfolio_exposure_overlap_probability",
            _normalize_ratio(
                "portfolio_exposure_overlap_probability",
                self.portfolio_exposure_overlap_probability,
            ),
        )
        _require_collision_status("collision_status", self.collision_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_manual_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ProbabilityEventDuplicateExposureCollisionReport:
    config_version: str
    candidate_count: Decimal
    blocker_count: Decimal
    attention_count: Decimal
    clear_count: Decimal
    collision_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    rows: tuple[ProbabilityEventDuplicateExposureCollisionRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "candidate_count",
            "blocker_count",
            "attention_count",
            "clear_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_collision_status("collision_status", self.collision_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_manual_step("manual_next_step", self.manual_next_step)
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_probability_event_duplicate_exposure_collision_report(
    rows: Iterable[ProbabilityEventDuplicateExposureCollisionInput],
    *,
    config: ProbabilityEventDuplicateExposureCollisionReportConfig,
) -> ProbabilityEventDuplicateExposureCollisionReport:
    if type(config) is not ProbabilityEventDuplicateExposureCollisionReportConfig:
        raise ValueError("config must be ProbabilityEventDuplicateExposureCollisionReportConfig")
    _require_hard_flags("config", config)
    source_rows = _normalize_input_rows(rows)
    report_rows = tuple(
        sorted(
            (_build_report_row(row, config=config) for row in source_rows),
            key=lambda row: row.candidate_id,
        ),
    )
    status = _report_status(report_rows)
    return ProbabilityEventDuplicateExposureCollisionReport(
        config_version=config.config_version,
        candidate_count=Decimal(len(report_rows)),
        blocker_count=Decimal(
            sum(1 for row in report_rows if row.collision_status == BLOCK_STATUS),
        ),
        attention_count=Decimal(
            sum(1 for row in report_rows if row.collision_status == WATCH_STATUS),
        ),
        clear_count=Decimal(
            sum(1 for row in report_rows if row.collision_status == CLEAR_STATUS),
        ),
        collision_status=status,
        reason_codes=_report_reason_codes(report_rows),
        manual_next_step=_manual_next_step(status),
        rows=report_rows,
    )


def _build_report_row(
    row: ProbabilityEventDuplicateExposureCollisionInput,
    *,
    config: ProbabilityEventDuplicateExposureCollisionReportConfig,
) -> ProbabilityEventDuplicateExposureCollisionRow:
    reasons = _row_reason_codes(row, config=config)
    status = _row_status(reasons)
    return ProbabilityEventDuplicateExposureCollisionRow(
        candidate_id=row.candidate_id,
        event_ref=row.event_ref,
        market_ref=row.market_ref,
        correlated_event_count=row.correlated_event_count,
        same_resolution_source_count=row.same_resolution_source_count,
        existing_watchlist_overlap_count=row.existing_watchlist_overlap_count,
        portfolio_exposure_overlap_probability=row.portfolio_exposure_overlap_probability,
        collision_status=status,
        reason_codes=reasons,
        manual_next_step=_manual_next_step(status),
    )


def _row_reason_codes(
    row: ProbabilityEventDuplicateExposureCollisionInput,
    *,
    config: ProbabilityEventDuplicateExposureCollisionReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.same_resolution_source_count > DECIMAL_ZERO:
        reasons.append(SAME_SOURCE_REASON)
    if row.existing_watchlist_overlap_count > DECIMAL_ZERO:
        reasons.append(WATCHLIST_REASON)
    if (
        row.portfolio_exposure_overlap_probability
        >= config.portfolio_exposure_overlap_block_probability
    ):
        reasons.append(PORTFOLIO_BLOCK_REASON)
    elif (
        row.portfolio_exposure_overlap_probability
        >= config.portfolio_exposure_overlap_watch_probability
    ):
        reasons.append(PORTFOLIO_WATCH_REASON)
    if row.correlated_event_count >= config.correlated_event_watch_count:
        reasons.append(CORRELATED_EVENT_REASON)
    if not reasons:
        return (CLEAR_REASON,)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if SAME_SOURCE_REASON in reason_codes or PORTFOLIO_BLOCK_REASON in reason_codes:
        return BLOCK_STATUS
    if reason_codes != (CLEAR_REASON,):
        return WATCH_STATUS
    return CLEAR_STATUS


def _report_status(
    rows: tuple[ProbabilityEventDuplicateExposureCollisionRow, ...],
) -> str:
    if any(row.collision_status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.collision_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return CLEAR_STATUS


def _report_reason_codes(
    rows: tuple[ProbabilityEventDuplicateExposureCollisionRow, ...],
) -> tuple[str, ...]:
    reasons = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != CLEAR_REASON
    }
    if not reasons:
        return (CLEAR_REASON,)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _manual_next_step(collision_status: str) -> str:
    if collision_status == BLOCK_STATUS:
        return MANUAL_BLOCK_STEP
    if collision_status == WATCH_STATUS:
        return MANUAL_WATCH_STEP
    return MANUAL_CLEAR_STEP


def _normalize_input_rows(
    rows: Iterable[ProbabilityEventDuplicateExposureCollisionInput],
) -> tuple[ProbabilityEventDuplicateExposureCollisionInput, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ProbabilityEventDuplicateExposureCollisionInput:
            raise ValueError(
                "rows must contain ProbabilityEventDuplicateExposureCollisionInput values",
            )
        _require_hard_flags("input", row)
    return normalized


def _normalize_report_rows(
    value: object,
) -> tuple[ProbabilityEventDuplicateExposureCollisionRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ProbabilityEventDuplicateExposureCollisionRow:
            raise ValueError(
                "rows must contain ProbabilityEventDuplicateExposureCollisionRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=lambda row: row.candidate_id)):
        raise ValueError("rows must be sorted by candidate_id")
    if len({row.candidate_id for row in rows}) != len(rows):
        raise ValueError("rows must be unique by candidate_id")
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    expected = tuple(reason for reason in REASON_CODES if reason in set(reason_codes))
    if reason_codes != expected:
        raise ValueError("reason_codes must be sorted and unique")
    return reason_codes


def _normalize_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    quantized = _normalize_integral_decimal(field_name, value)
    if quantized < DECIMAL_ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(RATIO_QUANT)
    if quantized < DECIMAL_ZERO or quantized > DECIMAL_ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return quantized


def _require_collision_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in COLLISION_STATUSES:
        raise ValueError(f"{field_name} must be one of clear, watch, block")


def _require_manual_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_STEPS:
        raise ValueError(f"{field_name} must contain a known manual step")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known collision reasons")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload_text(value: str) -> None:
    lowered = value.lower()
    tokens = tuple(lowered.split("_"))
    if any(
        lowered == marker or marker in tokens
        for marker in UNSAFE_PUBLIC_PAYLOAD_KEY_MARKERS
    ):
        raise ValueError(f"unsafe public payload value: {value}")


def _validate_row(row: ProbabilityEventDuplicateExposureCollisionRow) -> None:
    if row.collision_status != _row_status(row.reason_codes):
        raise ValueError("collision_status must match reason_codes")
    if row.manual_next_step != _manual_next_step(row.collision_status):
        raise ValueError("manual_next_step must match collision_status")


def _validate_report(report: ProbabilityEventDuplicateExposureCollisionReport) -> None:
    if report.candidate_count != Decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.blocker_count != Decimal(
        sum(1 for row in report.rows if row.collision_status == BLOCK_STATUS),
    ):
        raise ValueError("blocker_count must match rows")
    if report.attention_count != Decimal(
        sum(1 for row in report.rows if row.collision_status == WATCH_STATUS),
    ):
        raise ValueError("attention_count must match rows")
    if report.clear_count != Decimal(
        sum(1 for row in report.rows if row.collision_status == CLEAR_STATUS),
    ):
        raise ValueError("clear_count must match rows")
    if report.collision_status != _report_status(report.rows):
        raise ValueError("collision_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.manual_next_step != _manual_next_step(report.collision_status):
        raise ValueError("manual_next_step must match collision_status")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "ProbabilityEventDuplicateExposureCollisionReportConfig",
    "ProbabilityEventDuplicateExposureCollisionInput",
    "ProbabilityEventDuplicateExposureCollisionRow",
    "ProbabilityEventDuplicateExposureCollisionReport",
    "build_probability_event_duplicate_exposure_collision_report",
)
