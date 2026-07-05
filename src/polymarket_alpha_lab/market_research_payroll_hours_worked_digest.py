"""Pure Phase 1 payroll hours worked digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_MARKET_RESEARCH_PAYROLL_HOURS_WORKED_DIGEST_CONFIG_VERSION = (
    "market-research-payroll-hours-worked-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_payroll_hours_worked_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_HOURS_SURPRISE_REASON = f"{REASON_PREFIX}material_hours_surprise"
NEGATIVE_HOURS_SURPRISE_REASON = f"{REASON_PREFIX}negative_hours_surprise"
POSITIVE_HOURS_SURPRISE_REASON = f"{REASON_PREFIX}positive_hours_surprise"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REPORT_REASON_CODE_SEQUENCE = (
    MATERIAL_HOURS_SURPRISE_REASON,
    NEGATIVE_HOURS_SURPRISE_REASON,
    POSITIVE_HOURS_SURPRISE_REASON,
    PROBABILITY_REPRICING_REASON,
    READY_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_HOURS_SURPRISE_REASON,
    NEGATIVE_HOURS_SURPRISE_REASON,
    POSITIVE_HOURS_SURPRISE_REASON,
    PROBABILITY_REPRICING_REASON,
    READY_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
)
REASON_COUNT_SORT_SEQUENCE = (
    MATERIAL_HOURS_SURPRISE_REASON,
    STALE_RELEASE_REASON,
    PROBABILITY_REPRICING_REASON,
    NEGATIVE_HOURS_SURPRISE_REASON,
    POSITIVE_HOURS_SURPRISE_REASON,
    THIN_SOURCES_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_payroll_hours_worked_digest",
    STATUS_WATCH: "review_report_only_market_research_payroll_hours_worked_digest",
    STATUS_BLOCKED: "block_report_only_market_research_payroll_hours_worked_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
STATUS_SORT_WEIGHT = {
    STATUS_BLOCKED: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_READY: Decimal("2.000000"),
}

__all__ = (
    "DEFAULT_MARKET_RESEARCH_PAYROLL_HOURS_WORKED_DIGEST_CONFIG_VERSION",
    "MarketResearchPayrollHoursWorkedDigestConfig",
    "MarketResearchPayrollHoursWorkedDigestInputRow",
    "MarketResearchPayrollHoursWorkedDigestRow",
    "MarketResearchPayrollHoursWorkedDigestReasonCodeCount",
    "MarketResearchPayrollHoursWorkedDigestReport",
    "build_market_research_payroll_hours_worked_digest",
    "market_research_payroll_hours_worked_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchPayrollHoursWorkedDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_PAYROLL_HOURS_WORKED_DIGEST_CONFIG_VERSION
    )
    fresh_release_max_age_seconds: Decimal = Decimal("7200.000000")
    material_hours_delta_threshold: Decimal = Decimal("0.100000")
    min_source_count: Decimal = Decimal("2.000000")
    probability_repricing_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPayrollHoursWorkedDigestConfig:
            raise TypeError(
                "MarketResearchPayrollHoursWorkedDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollHoursWorkedDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchPayrollHoursWorkedDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_PAYROLL_HOURS_WORKED_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_release_max_age_seconds",
            "material_hours_delta_threshold",
            "probability_repricing_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchPayrollHoursWorkedDigestInputRow:
    research_key: str
    condition_id: str
    payroll_series_key: str
    released_at: datetime
    source_count: Decimal
    actual_hours_worked: Decimal
    consensus_hours_worked: Decimal
    previous_hours_worked: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPayrollHoursWorkedDigestInputRow:
            raise TypeError(
                "MarketResearchPayrollHoursWorkedDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollHoursWorkedDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchPayrollHoursWorkedDigestInputRow",
            )
        for field_name in ("research_key", "condition_id", "payroll_series_key"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "actual_hours_worked",
            "consensus_hours_worked",
            "previous_hours_worked",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchPayrollHoursWorkedDigestRow:
    research_key: str
    condition_id: str
    payroll_series_key: str
    digest_status: str
    released_at: datetime
    release_age_seconds: Decimal
    source_count: Decimal
    actual_hours_worked: Decimal
    consensus_hours_worked: Decimal
    previous_hours_worked: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    hours_surprise: Decimal
    hours_surprise_abs: Decimal
    hours_surprise_ratio: Decimal
    previous_hours_delta: Decimal
    probability_delta: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPayrollHoursWorkedDigestRow:
            raise TypeError(
                "MarketResearchPayrollHoursWorkedDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollHoursWorkedDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchPayrollHoursWorkedDigestRow",
            )
        for field_name in ("research_key", "condition_id", "payroll_series_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_digest_status("digest_status", self.digest_status)
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "release_age_seconds",
            _require_nonnegative_decimal("release_age_seconds", self.release_age_seconds),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "actual_hours_worked",
            "consensus_hours_worked",
            "previous_hours_worked",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "hours_surprise",
            "hours_surprise_abs",
            "hours_surprise_ratio",
            "previous_hours_delta",
            "probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row_status_reason_codes(self.digest_status, self.reason_codes)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchPayrollHoursWorkedDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    release_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPayrollHoursWorkedDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchPayrollHoursWorkedDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollHoursWorkedDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchPayrollHoursWorkedDigestReasonCodeCount",
            )
        _require_known_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "release_ratio",
            _require_ratio_decimal("release_ratio", self.release_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchPayrollHoursWorkedDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    release_count: Decimal
    ready_release_count: Decimal
    watch_release_count: Decimal
    blocked_release_count: Decimal
    positive_hours_surprise_count: Decimal
    negative_hours_surprise_count: Decimal
    material_hours_surprise_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    probability_repricing_count: Decimal
    positive_hours_surprise_ratio: Decimal
    negative_hours_surprise_ratio: Decimal
    material_hours_surprise_ratio: Decimal
    average_abs_hours_surprise: Decimal
    max_release_age_seconds: Decimal
    rows: tuple[MarketResearchPayrollHoursWorkedDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchPayrollHoursWorkedDigestReasonCodeCount,
        ...
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchPayrollHoursWorkedDigestReport:
            raise TypeError(
                "MarketResearchPayrollHoursWorkedDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchPayrollHoursWorkedDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchPayrollHoursWorkedDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_PAYROLL_HOURS_WORKED_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_digest_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODE_SEQUENCE),
        )
        for field_name in (
            "release_count",
            "ready_release_count",
            "watch_release_count",
            "blocked_release_count",
            "positive_hours_surprise_count",
            "negative_hours_surprise_count",
            "material_hours_surprise_count",
            "stale_release_count",
            "thin_source_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "positive_hours_surprise_ratio",
            "negative_hours_surprise_ratio",
            "material_hours_surprise_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_abs_hours_surprise", "max_release_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        if (
            self.ready_release_count
            + self.watch_release_count
            + self.blocked_release_count
            != self.release_count
        ):
            raise ValueError("ready count fields must sum to release_count")
        if self.release_count != _decimal_count(self.rows):
            raise ValueError("release_count must equal row count")
        _validate_report_reason_codes(self.digest_status, self.reason_codes, self.rows)
        _require_hard_flags("report", self)


def build_market_research_payroll_hours_worked_digest(
    inputs: list[MarketResearchPayrollHoursWorkedDigestInputRow]
    | tuple[MarketResearchPayrollHoursWorkedDigestInputRow, ...],
    *,
    config: MarketResearchPayrollHoursWorkedDigestConfig,
    generated_at: datetime,
) -> MarketResearchPayrollHoursWorkedDigestReport:
    if type(config) is not MarketResearchPayrollHoursWorkedDigestConfig:
        raise ValueError(
            "config must be a MarketResearchPayrollHoursWorkedDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(inputs)
    digest_rows = tuple(
        _build_digest_row(source, config=config, generated_at=generated_at_utc)
        for source in source_rows
    )
    sorted_rows = tuple(sorted(digest_rows, key=_row_sort_key))
    release_count = _decimal_count(sorted_rows)
    ready_count = _decimal_count(
        row for row in sorted_rows if row.digest_status == STATUS_READY
    )
    watch_count = _decimal_count(
        row for row in sorted_rows if row.digest_status == STATUS_WATCH
    )
    blocked_count = _decimal_count(
        row for row in sorted_rows if row.digest_status == STATUS_BLOCKED
    )
    if not sorted_rows:
        digest_status = STATUS_BLOCKED
        reason_codes = (NO_INPUTS_REASON,)
    else:
        digest_status = _digest_status(blocked_count, watch_count)
        reason_codes = _digest_reason_codes(sorted_rows)
    return MarketResearchPayrollHoursWorkedDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        reason_codes=reason_codes,
        release_count=release_count,
        ready_release_count=ready_count,
        watch_release_count=watch_count,
        blocked_release_count=blocked_count,
        positive_hours_surprise_count=_direction_count(sorted_rows, "positive"),
        negative_hours_surprise_count=_direction_count(sorted_rows, "negative"),
        material_hours_surprise_count=_reason_count(
            sorted_rows,
            MATERIAL_HOURS_SURPRISE_REASON,
        ),
        stale_release_count=_reason_count(sorted_rows, STALE_RELEASE_REASON),
        thin_source_count=_reason_count(sorted_rows, THIN_SOURCES_REASON),
        probability_repricing_count=_reason_count(
            sorted_rows,
            PROBABILITY_REPRICING_REASON,
        ),
        positive_hours_surprise_ratio=_ratio(
            _direction_count(sorted_rows, "positive"),
            release_count,
        ),
        negative_hours_surprise_ratio=_ratio(
            _direction_count(sorted_rows, "negative"),
            release_count,
        ),
        material_hours_surprise_ratio=_ratio(
            _reason_count(sorted_rows, MATERIAL_HOURS_SURPRISE_REASON),
            release_count,
        ),
        average_abs_hours_surprise=_average(
            tuple(row.hours_surprise_abs for row in sorted_rows),
        ),
        max_release_age_seconds=_max_decimal(
            tuple(row.release_age_seconds for row in sorted_rows),
        ),
        rows=sorted_rows,
        reason_code_counts=_build_reason_code_counts(sorted_rows),
    )


def market_research_payroll_hours_worked_digest_payload(
    report: MarketResearchPayrollHoursWorkedDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchPayrollHoursWorkedDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchPayrollHoursWorkedDigestReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _build_digest_row(
    source: MarketResearchPayrollHoursWorkedDigestInputRow,
    *,
    config: MarketResearchPayrollHoursWorkedDigestConfig,
    generated_at: datetime,
) -> MarketResearchPayrollHoursWorkedDigestRow:
    if source.released_at > generated_at:
        raise ValueError("released_at must not be in the future")
    release_age_seconds = _age_seconds(generated_at, source.released_at)
    hours_surprise = _quantize(source.actual_hours_worked - source.consensus_hours_worked)
    hours_surprise_abs = _quantize(abs(hours_surprise))
    previous_hours_delta = _quantize(
        source.actual_hours_worked - source.previous_hours_worked,
    )
    probability_delta = _quantize(
        source.market_probability_after - source.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        source,
        release_age_seconds=release_age_seconds,
        hours_surprise=hours_surprise,
        probability_delta=probability_delta,
        config=config,
    )
    return MarketResearchPayrollHoursWorkedDigestRow(
        research_key=source.research_key,
        condition_id=source.condition_id,
        payroll_series_key=source.payroll_series_key,
        digest_status=_row_status(reason_codes),
        released_at=source.released_at,
        release_age_seconds=release_age_seconds,
        source_count=source.source_count,
        actual_hours_worked=source.actual_hours_worked,
        consensus_hours_worked=source.consensus_hours_worked,
        previous_hours_worked=source.previous_hours_worked,
        market_probability_before=source.market_probability_before,
        market_probability_after=source.market_probability_after,
        hours_surprise=hours_surprise,
        hours_surprise_abs=hours_surprise_abs,
        hours_surprise_ratio=_ratio(hours_surprise_abs, source.consensus_hours_worked),
        previous_hours_delta=previous_hours_delta,
        probability_delta=probability_delta,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    source: MarketResearchPayrollHoursWorkedDigestInputRow,
    *,
    release_age_seconds: Decimal,
    hours_surprise: Decimal,
    probability_delta: Decimal,
    config: MarketResearchPayrollHoursWorkedDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if abs(hours_surprise) >= config.material_hours_delta_threshold:
        reason_codes.append(MATERIAL_HOURS_SURPRISE_REASON)
        if hours_surprise < ZERO:
            reason_codes.append(NEGATIVE_HOURS_SURPRISE_REASON)
        elif hours_surprise > ZERO:
            reason_codes.append(POSITIVE_HOURS_SURPRISE_REASON)
    if abs(probability_delta) >= config.probability_repricing_threshold:
        reason_codes.append(PROBABILITY_REPRICING_REASON)
    if release_age_seconds > config.fresh_release_max_age_seconds:
        reason_codes.append(STALE_RELEASE_REASON)
    if source.source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCES_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(tuple(reason_codes), ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    if THIN_SOURCES_REASON in reason_codes and MATERIAL_HOURS_SURPRISE_REASON not in reason_codes:
        return STATUS_BLOCKED
    return STATUS_WATCH


def _digest_status(blocked_count: Decimal, watch_count: Decimal) -> str:
    if blocked_count > ZERO:
        return STATUS_BLOCKED
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _digest_reason_codes(
    rows: tuple[MarketResearchPayrollHoursWorkedDigestRow, ...],
) -> tuple[str, ...]:
    codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != READY_REASON
    }
    if not codes and rows:
        codes.add(READY_REASON)
    return tuple(code for code in REPORT_REASON_CODE_SEQUENCE if code in codes)


def _build_reason_code_counts(
    rows: tuple[MarketResearchPayrollHoursWorkedDigestRow, ...],
) -> tuple[MarketResearchPayrollHoursWorkedDigestReasonCodeCount, ...]:
    release_count = _decimal_count(rows)
    if not rows:
        return (
            MarketResearchPayrollHoursWorkedDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                release_ratio=ZERO,
            ),
        )
    counts: list[MarketResearchPayrollHoursWorkedDigestReasonCodeCount] = []
    for reason_code in REPORT_REASON_CODE_SEQUENCE:
        if reason_code in (READY_REASON, NO_INPUTS_REASON):
            continue
        count = _reason_count(rows, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchPayrollHoursWorkedDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                release_ratio=_ratio(count, release_count),
            ),
        )
    return tuple(
        sorted(
            counts,
            key=lambda item: (
                -item.count,
                REASON_COUNT_SORT_SEQUENCE.index(item.reason_code),
            ),
        ),
    )


def _normalize_input_rows(
    value: list[MarketResearchPayrollHoursWorkedDigestInputRow]
    | tuple[MarketResearchPayrollHoursWorkedDigestInputRow, ...],
) -> tuple[MarketResearchPayrollHoursWorkedDigestInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchPayrollHoursWorkedDigestInputRow:
            raise ValueError(
                "inputs must contain "
                "MarketResearchPayrollHoursWorkedDigestInputRow values",
            )
        _require_hard_flags("input row", row)
        key = (row.condition_id, row.payroll_series_key)
        if key in seen_keys:
            raise ValueError("payroll_series_key values must be unique per condition_id")
        seen_keys.add(key)
    return rows


def _normalize_rows(
    value: tuple[MarketResearchPayrollHoursWorkedDigestRow, ...],
) -> tuple[MarketResearchPayrollHoursWorkedDigestRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not MarketResearchPayrollHoursWorkedDigestRow:
            raise ValueError(
                "rows must contain MarketResearchPayrollHoursWorkedDigestRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    return rows


def _normalize_reason_code_counts(
    value: tuple[MarketResearchPayrollHoursWorkedDigestReasonCodeCount, ...],
) -> tuple[MarketResearchPayrollHoursWorkedDigestReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    for item in counts:
        if type(item) is not MarketResearchPayrollHoursWorkedDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchPayrollHoursWorkedDigestReasonCodeCount values",
            )
        _require_hard_flags("reason count", item)
    if counts != tuple(
        sorted(
            counts,
            key=lambda item: (
                -item.count,
                REASON_COUNT_SORT_SEQUENCE.index(item.reason_code),
            ),
        ),
    ):
        raise ValueError("reason_code_counts must use deterministic ordering")
    return counts


def _normalize_reason_codes(
    value: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_known_reason_code("reason_codes", reason_code)
    canonical = tuple(code for code in sequence if code in set(reason_codes))
    if reason_codes != canonical:
        raise ValueError("reason_codes must use deterministic ordering")
    return reason_codes


def _validate_row_status_reason_codes(
    status: str,
    reason_codes: tuple[str, ...],
) -> None:
    if status == STATUS_READY and reason_codes != (READY_REASON,):
        raise ValueError("ready rows require the ready reason")
    if status != STATUS_READY and reason_codes == (READY_REASON,):
        raise ValueError("non-ready rows require blocking or watch reasons")


def _validate_report_reason_codes(
    status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchPayrollHoursWorkedDigestRow, ...],
) -> None:
    expected = _digest_reason_codes(rows) if rows else (NO_INPUTS_REASON,)
    if reason_codes != expected:
        raise ValueError("reason_codes must match rows")
    expected_status = STATUS_BLOCKED if not rows else _digest_status(
        _decimal_count(row for row in rows if row.digest_status == STATUS_BLOCKED),
        _decimal_count(row for row in rows if row.digest_status == STATUS_WATCH),
    )
    if status != expected_status:
        raise ValueError("digest_status must match rows")


def _direction_count(
    rows: tuple[MarketResearchPayrollHoursWorkedDigestRow, ...],
    direction: str,
) -> Decimal:
    if direction == "positive":
        return _decimal_count(row for row in rows if row.hours_surprise > ZERO)
    if direction == "negative":
        return _decimal_count(row for row in rows if row.hours_surprise < ZERO)
    raise ValueError("direction must be positive or negative")


def _reason_count(
    rows: tuple[MarketResearchPayrollHoursWorkedDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(row for row in rows if reason_code in row.reason_codes)


def _row_sort_key(
    row: MarketResearchPayrollHoursWorkedDigestRow,
) -> tuple[Decimal, str, str]:
    return (STATUS_SORT_WEIGHT[row.digest_status], row.payroll_series_key, row.research_key)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = (
        Decimal(delta.days * 86400 + delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    return _quantize(seconds)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_count(values: object) -> Decimal:
    return _quantize(Decimal(sum(1 for _ in values)))  # type: ignore[arg-type]


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_finite_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_finite_decimal(field_name, value)
    if decimal <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_decimal(field_name, value)
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_positive_decimal(field_name, value)
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_finite_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _require_digest_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_known_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
