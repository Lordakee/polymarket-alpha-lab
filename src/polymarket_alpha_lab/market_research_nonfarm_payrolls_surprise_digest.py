from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLLS_SURPRISE_DIGEST_CONFIG_VERSION = (
    "market_research_nonfarm_payrolls_surprise_digest.v1"
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=34)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
SURPRISE_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_nonfarm_payrolls_surprise_digest",
    STATUS_WATCH: "watch_report_only_market_research_nonfarm_payrolls_surprise_digest",
    STATUS_BLOCKED: "block_report_only_market_research_nonfarm_payrolls_surprise_digest",
}

REASON_PREFIX = "market_research_nonfarm_payrolls_surprise_digest"
READY_REASON = f"{REASON_PREFIX}_ready"
NO_INPUTS_REASON = f"{REASON_PREFIX}_no_inputs"
MATERIAL_SURPRISE_REASON = f"{REASON_PREFIX}_material_surprise"
POSITIVE_SURPRISE_REASON = f"{REASON_PREFIX}_positive_surprise"
NEGATIVE_SURPRISE_REASON = f"{REASON_PREFIX}_negative_surprise"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}_probability_repricing"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}_missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}_slow_acknowledgement"
STALE_RELEASE_REASON = f"{REASON_PREFIX}_stale_release"
THIN_SOURCES_REASON = f"{REASON_PREFIX}_thin_sources"

ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_SURPRISE_REASON,
    POSITIVE_SURPRISE_REASON,
    NEGATIVE_SURPRISE_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
REASON_CODE_SEQUENCE = ROW_REASON_CODE_SEQUENCE + (NO_INPUTS_REASON,)
UNSAFE_TEXT_FRAGMENTS = (
    "".join(("au", "th")),
    "".join(("bro", "ker")),
    "".join(("can", "cel")),
    "".join(("data", "base")),
    "".join(("exec", "ute")),
    "".join(("ex", "change")),
    "".join(("li", "ve")),
    "".join(("or", "der")),
    "".join(("per", "sist")),
    "".join(("sec", "ret")),
    "".join(("st", "ore")),
    "".join(("to", "ken")),
    "".join(("tr", "ade")),
    "".join(("wal", "let")),
)


@dataclass(frozen=True)
class MarketResearchNonfarmPayrollsSurpriseDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLLS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    fresh_release_max_age_seconds: Decimal = Decimal("7200.000000")
    material_surprise_threshold_jobs: Decimal = Decimal("50000.000000")
    min_source_count: Decimal = Decimal("2.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    probability_repricing_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNonfarmPayrollsSurpriseDigestConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollsSurpriseDigestConfig:
            raise TypeError(
                "config must be exactly "
                "MarketResearchNonfarmPayrollsSurpriseDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLLS_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_release_max_age_seconds",
            "material_surprise_threshold_jobs",
            "max_acknowledgement_lag_seconds",
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
        object.__setattr__(
            self,
            "probability_repricing_threshold",
            _require_ratio_decimal(
                "probability_repricing_threshold",
                self.probability_repricing_threshold,
            ),
        )
        if self.probability_repricing_threshold <= ZERO:
            raise ValueError("probability_repricing_threshold must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchNonfarmPayrollsSurpriseDigestInputRow:
    research_key: str
    condition_id: str
    payroll_series_key: str
    release_reference: str
    released_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    actual_payroll_jobs: Decimal
    consensus_payroll_jobs: Decimal
    previous_payroll_jobs: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNonfarmPayrollsSurpriseDigestInputRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollsSurpriseDigestInputRow:
            raise TypeError(
                "input row must be exactly "
                "MarketResearchNonfarmPayrollsSurpriseDigestInputRow",
            )
        for field_name in ("research_key", "condition_id", "payroll_series_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("release_reference", self.release_reference)
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        if self.acknowledged_at is not None and self.acknowledged_at < self.released_at:
            raise ValueError("acknowledged_at must not precede released_at")
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "actual_payroll_jobs",
            "consensus_payroll_jobs",
            "previous_payroll_jobs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchNonfarmPayrollsSurpriseDigestRow:
    research_key: str
    condition_id: str
    payroll_series_key: str
    surprise_status: str
    released_at: datetime
    acknowledged_at: datetime | None
    release_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    actual_payroll_jobs: Decimal
    consensus_payroll_jobs: Decimal
    previous_payroll_jobs: Decimal
    payroll_surprise_jobs: Decimal
    payroll_surprise_abs_jobs: Decimal
    payroll_surprise_ratio: Decimal
    previous_payroll_delta_jobs: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_delta: Decimal
    redacted_release_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNonfarmPayrollsSurpriseDigestRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollsSurpriseDigestRow:
            raise TypeError(
                "row must be exactly MarketResearchNonfarmPayrollsSurpriseDigestRow",
            )
        for field_name in ("research_key", "condition_id", "payroll_series_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_surprise_status("surprise_status", self.surprise_status)
        object.__setattr__(self, "released_at", _as_utc("released_at", self.released_at))
        object.__setattr__(
            self,
            "acknowledged_at",
            _as_optional_utc("acknowledged_at", self.acknowledged_at),
        )
        object.__setattr__(
            self,
            "release_age_seconds",
            _require_nonnegative_decimal("release_age_seconds", self.release_age_seconds),
        )
        object.__setattr__(
            self,
            "acknowledgement_lag_seconds",
            _require_optional_nonnegative_decimal(
                "acknowledgement_lag_seconds",
                self.acknowledgement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_nonnegative_count_decimal("source_count", self.source_count),
        )
        for field_name in (
            "actual_payroll_jobs",
            "consensus_payroll_jobs",
            "previous_payroll_jobs",
            "payroll_surprise_jobs",
            "payroll_surprise_abs_jobs",
            "payroll_surprise_ratio",
            "previous_payroll_delta_jobs",
            "probability_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("market_probability_before", "market_probability_after"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "redacted_release_reference",
            _require_redacted_reference(
                "redacted_release_reference",
                self.redacted_release_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    release_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount:
            raise TypeError(
                "reason count must be exactly "
                "MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount",
            )
        _require_known_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "release_ratio",
            _require_ratio_decimal("release_ratio", self.release_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class MarketResearchNonfarmPayrollsSurpriseDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    release_count: Decimal
    ready_release_count: Decimal
    watch_release_count: Decimal
    blocked_release_count: Decimal
    positive_surprise_count: Decimal
    negative_surprise_count: Decimal
    material_surprise_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    probability_repricing_count: Decimal
    positive_surprise_ratio: Decimal
    negative_surprise_ratio: Decimal
    material_surprise_ratio: Decimal
    average_abs_surprise_jobs: Decimal
    max_release_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchNonfarmPayrollsSurpriseDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketResearchNonfarmPayrollsSurpriseDigestReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollsSurpriseDigestReport:
            raise TypeError(
                "report must be exactly "
                "MarketResearchNonfarmPayrollsSurpriseDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLLS_SURPRISE_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_surprise_status("digest_status", self.digest_status)
        if self.recommended_next_step != NEXT_STEPS[self.digest_status]:
            raise ValueError("recommended_next_step must match digest_status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, REASON_CODE_SEQUENCE),
        )
        for field_name in (
            "release_count",
            "ready_release_count",
            "watch_release_count",
            "blocked_release_count",
            "positive_surprise_count",
            "negative_surprise_count",
            "material_surprise_count",
            "stale_release_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "probability_repricing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "positive_surprise_ratio",
            "negative_surprise_ratio",
            "material_surprise_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_abs_surprise_jobs",
            "max_release_age_seconds",
            "average_source_count",
        ):
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
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_nonfarm_payrolls_surprise_digest(
    rows: tuple[object, ...],
    *,
    config: MarketResearchNonfarmPayrollsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchNonfarmPayrollsSurpriseDigestReport:
    if type(config) is not MarketResearchNonfarmPayrollsSurpriseDigestConfig:
        raise ValueError(
            "config must be exactly "
            "MarketResearchNonfarmPayrollsSurpriseDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(rows, generated_at_utc)
    built_rows = tuple(
        _build_row(source, config=config, generated_at=generated_at_utc)
        for source in source_rows
    )
    canonical_rows = _canonical_rows(built_rows)
    reason_code_counts = _build_reason_code_counts(canonical_rows)
    release_count = _count(len(canonical_rows))
    ready_count = _status_count(canonical_rows, STATUS_READY)
    watch_count = _status_count(canonical_rows, STATUS_WATCH)
    blocked_count = _status_count(canonical_rows, STATUS_BLOCKED)
    digest_status = _report_status(canonical_rows)

    return MarketResearchNonfarmPayrollsSurpriseDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        reason_codes=tuple(item.reason_code for item in reason_code_counts),
        release_count=release_count,
        ready_release_count=ready_count,
        watch_release_count=watch_count,
        blocked_release_count=blocked_count,
        positive_surprise_count=_direction_count(canonical_rows, positive=True),
        negative_surprise_count=_direction_count(canonical_rows, positive=False),
        material_surprise_count=_reason_count(canonical_rows, MATERIAL_SURPRISE_REASON),
        stale_release_count=_reason_count(canonical_rows, STALE_RELEASE_REASON),
        thin_source_count=_reason_count(canonical_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_reason_count(
            canonical_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_count(
            canonical_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        probability_repricing_count=_reason_count(
            canonical_rows,
            PROBABILITY_REPRICING_REASON,
        ),
        positive_surprise_ratio=_ratio(
            _direction_count(canonical_rows, positive=True),
            release_count,
        ),
        negative_surprise_ratio=_ratio(
            _direction_count(canonical_rows, positive=False),
            release_count,
        ),
        material_surprise_ratio=_ratio(
            _reason_count(canonical_rows, MATERIAL_SURPRISE_REASON),
            release_count,
        ),
        average_abs_surprise_jobs=_average(
            tuple(row.payroll_surprise_abs_jobs for row in canonical_rows),
        ),
        max_release_age_seconds=max(
            (row.release_age_seconds for row in canonical_rows),
            default=ZERO,
        ),
        average_source_count=_ratio(
            _sum_decimal(row.source_count for row in canonical_rows),
            release_count,
        ),
        rows=canonical_rows,
        reason_code_counts=reason_code_counts,
    )


def market_research_nonfarm_payrolls_surprise_digest_payload(
    report: MarketResearchNonfarmPayrollsSurpriseDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchNonfarmPayrollsSurpriseDigestReport:
        raise ValueError(
            "report must be exactly "
            "MarketResearchNonfarmPayrollsSurpriseDigestReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _build_row(
    source: MarketResearchNonfarmPayrollsSurpriseDigestInputRow,
    *,
    config: MarketResearchNonfarmPayrollsSurpriseDigestConfig,
    generated_at: datetime,
) -> MarketResearchNonfarmPayrollsSurpriseDigestRow:
    release_age_seconds = _seconds_between(source.released_at, generated_at)
    acknowledgement_lag_seconds = None
    if source.acknowledged_at is not None:
        acknowledgement_lag_seconds = _seconds_between(
            source.released_at,
            source.acknowledged_at,
        )
    payroll_surprise_jobs = _finite_decimal(
        source.actual_payroll_jobs - source.consensus_payroll_jobs,
    )
    payroll_surprise_abs_jobs = _finite_decimal(abs(payroll_surprise_jobs))
    previous_payroll_delta_jobs = _finite_decimal(
        source.actual_payroll_jobs - source.previous_payroll_jobs,
    )
    probability_delta = _finite_decimal(
        source.market_probability_after - source.market_probability_before,
    )
    reason_codes = _row_reason_codes(
        source_count=source.source_count,
        payroll_surprise_jobs=payroll_surprise_jobs,
        probability_delta=probability_delta,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        config=config,
    )
    return MarketResearchNonfarmPayrollsSurpriseDigestRow(
        research_key=source.research_key,
        condition_id=source.condition_id,
        payroll_series_key=source.payroll_series_key,
        surprise_status=_row_status(reason_codes),
        released_at=source.released_at,
        acknowledged_at=source.acknowledged_at,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=source.source_count,
        actual_payroll_jobs=source.actual_payroll_jobs,
        consensus_payroll_jobs=source.consensus_payroll_jobs,
        previous_payroll_jobs=source.previous_payroll_jobs,
        payroll_surprise_jobs=payroll_surprise_jobs,
        payroll_surprise_abs_jobs=payroll_surprise_abs_jobs,
        payroll_surprise_ratio=_ratio(
            payroll_surprise_abs_jobs,
            abs(source.consensus_payroll_jobs),
        ),
        previous_payroll_delta_jobs=previous_payroll_delta_jobs,
        market_probability_before=source.market_probability_before,
        market_probability_after=source.market_probability_after,
        probability_delta=probability_delta,
        redacted_release_reference=_redact_reference(source.release_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: Decimal,
    payroll_surprise_jobs: Decimal,
    probability_delta: Decimal,
    release_age_seconds: Decimal,
    acknowledgement_lag_seconds: Decimal | None,
    config: MarketResearchNonfarmPayrollsSurpriseDigestConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if abs(payroll_surprise_jobs) >= config.material_surprise_threshold_jobs:
        codes.append(MATERIAL_SURPRISE_REASON)
        if payroll_surprise_jobs > ZERO:
            codes.append(POSITIVE_SURPRISE_REASON)
        elif payroll_surprise_jobs < ZERO:
            codes.append(NEGATIVE_SURPRISE_REASON)
    if abs(probability_delta) >= config.probability_repricing_threshold:
        codes.append(PROBABILITY_REPRICING_REASON)
    if acknowledgement_lag_seconds is None:
        codes.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        codes.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if release_age_seconds > config.fresh_release_max_age_seconds:
        codes.append(STALE_RELEASE_REASON)
    if source_count < config.min_source_count:
        codes.append(THIN_SOURCES_REASON)
    if not codes:
        codes.append(READY_REASON)
    return _normalize_reason_codes(tuple(codes), ROW_REASON_CODE_SEQUENCE)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchNonfarmPayrollsSurpriseDigestRow, ...],
) -> str:
    if not rows or any(row.surprise_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.surprise_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _status_count(
    rows: tuple[MarketResearchNonfarmPayrollsSurpriseDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.surprise_status == status))


def _direction_count(
    rows: tuple[MarketResearchNonfarmPayrollsSurpriseDigestRow, ...],
    *,
    positive: bool,
) -> Decimal:
    if positive:
        return _count(sum(1 for row in rows if row.payroll_surprise_jobs > ZERO))
    return _count(sum(1 for row in rows if row.payroll_surprise_jobs < ZERO))


def _reason_count(
    rows: tuple[MarketResearchNonfarmPayrollsSurpriseDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_sort_key(
    row: MarketResearchNonfarmPayrollsSurpriseDigestRow,
) -> tuple[int, Decimal, str, str]:
    return (
        {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}[row.surprise_status],
        -row.payroll_surprise_abs_jobs,
        row.payroll_series_key,
        row.research_key,
    )


def _canonical_rows(
    rows: tuple[MarketResearchNonfarmPayrollsSurpriseDigestRow, ...],
) -> tuple[MarketResearchNonfarmPayrollsSurpriseDigestRow, ...]:
    return tuple(sorted(rows, key=_row_sort_key))


def _build_reason_code_counts(
    rows: tuple[MarketResearchNonfarmPayrollsSurpriseDigestRow, ...],
) -> tuple[MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount, ...]:
    total = _count(len(rows))
    if total == ZERO:
        return (
            MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                release_ratio=ZERO,
            ),
        )
    counts: list[MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount] = []
    for reason_code in ROW_REASON_CODE_SEQUENCE:
        count = _reason_count(rows, reason_code)
        if count == ZERO:
            continue
        counts.append(
            MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount(
                reason_code=reason_code,
                count=count,
                release_ratio=_ratio(count, total),
            ),
        )
    return tuple(counts)


def _normalize_input_rows(
    rows: object,
    generated_at: datetime,
) -> tuple[MarketResearchNonfarmPayrollsSurpriseDigestInputRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchNonfarmPayrollsSurpriseDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchNonfarmPayrollsSurpriseDigestInputRow",
            )
        _require_hard_flags("input row", row)
        key = (row.research_key, row.condition_id, row.payroll_series_key)
        if key in seen:
            raise ValueError("rows must use unique research condition series values")
        seen.add(key)
        if row.released_at > generated_at:
            raise ValueError("released_at must not be after generated_at")
        if row.acknowledged_at is not None and row.acknowledged_at > generated_at:
            raise ValueError("acknowledged_at must not be after generated_at")
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchNonfarmPayrollsSurpriseDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not MarketResearchNonfarmPayrollsSurpriseDigestRow:
            raise ValueError(
                "row must be exactly "
                "MarketResearchNonfarmPayrollsSurpriseDigestRow",
            )
        _require_hard_flags("row", row)
        key = (row.research_key, row.condition_id, row.payroll_series_key)
        if key in seen:
            raise ValueError("rows must use unique research condition series values")
        seen.add(key)
    if normalized != _canonical_rows(normalized):
        raise ValueError("rows must be canonical")
    return normalized


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(counts)
    seen: set[str] = set()
    for count in normalized:
        if type(count) is not MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount",
            )
        _require_hard_flags("reason count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must use unique reason codes")
        seen.add(count.reason_code)
    canonical = tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in seen)
    if tuple(count.reason_code for count in normalized) != canonical:
        raise ValueError("reason_code_counts must be canonical")
    return normalized


def _normalize_reason_codes(
    reason_codes: object,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    seen: set[str] = set()
    for reason_code in normalized:
        _require_known_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must use unique reason codes")
        if reason_code not in sequence:
            raise ValueError("reason_code is not valid for this scope")
        seen.add(reason_code)
    canonical = tuple(reason_code for reason_code in sequence if reason_code in seen)
    if normalized != canonical:
        raise ValueError("reason_codes must be canonical")
    if sequence == ROW_REASON_CODE_SEQUENCE and READY_REASON in seen and len(seen) != 1:
        raise ValueError("reason_codes ready must be exclusive")
    if NO_INPUTS_REASON in seen and len(seen) != 1:
        raise ValueError("reason_codes no_inputs must be exclusive")
    return normalized


def _validate_row(row: MarketResearchNonfarmPayrollsSurpriseDigestRow) -> None:
    if row.acknowledged_at is None:
        if row.acknowledgement_lag_seconds is not None:
            raise ValueError("acknowledgement_lag_seconds must be absent")
    elif row.acknowledgement_lag_seconds is None:
        raise ValueError("acknowledgement_lag_seconds must be present")
    elif row.acknowledged_at < row.released_at:
        raise ValueError("acknowledgement_lag_seconds must match timestamps")
    elif row.acknowledgement_lag_seconds != _seconds_between(
        row.released_at,
        row.acknowledged_at,
    ):
        raise ValueError("acknowledgement_lag_seconds must match timestamps")
    if row.payroll_surprise_jobs != _finite_decimal(
        row.actual_payroll_jobs - row.consensus_payroll_jobs,
    ):
        raise ValueError("payroll_surprise_jobs must match actual less consensus")
    if row.payroll_surprise_abs_jobs != _finite_decimal(abs(row.payroll_surprise_jobs)):
        raise ValueError("payroll_surprise_abs_jobs must match payroll_surprise_jobs")
    if row.payroll_surprise_ratio != _ratio(
        row.payroll_surprise_abs_jobs,
        abs(row.consensus_payroll_jobs),
    ):
        raise ValueError("payroll_surprise_ratio must match payroll values")
    if row.previous_payroll_delta_jobs != _finite_decimal(
        row.actual_payroll_jobs - row.previous_payroll_jobs,
    ):
        raise ValueError("previous_payroll_delta_jobs must match actual less previous")
    if row.probability_delta != _finite_decimal(
        row.market_probability_after - row.market_probability_before,
    ):
        raise ValueError("probability_delta must match market probabilities")
    if row.surprise_status != _row_status(row.reason_codes):
        raise ValueError("surprise_status must match reason_codes")


def _validate_report(report: MarketResearchNonfarmPayrollsSurpriseDigestReport) -> None:
    if (
        report.ready_release_count
        + report.watch_release_count
        + report.blocked_release_count
        != report.release_count
    ):
        raise ValueError("ready_release_count fields must sum to release_count")
    if report.release_count != _count(len(report.rows)):
        raise ValueError("release_count must match rows")
    for status, field_name in (
        (STATUS_READY, "ready_release_count"),
        (STATUS_WATCH, "watch_release_count"),
        (STATUS_BLOCKED, "blocked_release_count"),
    ):
        expected = _status_count(report.rows, status)
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_reason_counts = _build_reason_code_counts(report.rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(
        count.reason_code for count in report.reason_code_counts
    ):
        raise ValueError("reason_codes must match reason_code_counts")
    for reason_code, field_name in (
        (MATERIAL_SURPRISE_REASON, "material_surprise_count"),
        (STALE_RELEASE_REASON, "stale_release_count"),
        (THIN_SOURCES_REASON, "thin_source_count"),
        (MISSING_ACKNOWLEDGEMENT_REASON, "missing_acknowledgement_count"),
        (SLOW_ACKNOWLEDGEMENT_REASON, "slow_acknowledgement_count"),
        (PROBABILITY_REPRICING_REASON, "probability_repricing_count"),
    ):
        expected = _reason_count(report.rows, reason_code)
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    positive_count = _direction_count(report.rows, positive=True)
    negative_count = _direction_count(report.rows, positive=False)
    if report.positive_surprise_count != positive_count:
        raise ValueError("positive_surprise_count must match rows")
    if report.negative_surprise_count != negative_count:
        raise ValueError("negative_surprise_count must match rows")
    if report.positive_surprise_ratio != _ratio(positive_count, report.release_count):
        raise ValueError("positive_surprise_ratio must match rows")
    if report.negative_surprise_ratio != _ratio(negative_count, report.release_count):
        raise ValueError("negative_surprise_ratio must match rows")
    if report.material_surprise_ratio != _ratio(
        report.material_surprise_count,
        report.release_count,
    ):
        raise ValueError("material_surprise_ratio must match rows")
    if report.average_abs_surprise_jobs != _average(
        tuple(row.payroll_surprise_abs_jobs for row in report.rows),
    ):
        raise ValueError("average_abs_surprise_jobs must match rows")
    if report.max_release_age_seconds != max(
        (row.release_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_release_age_seconds must match rows")
    if report.average_source_count != _ratio(
        _sum_decimal(row.source_count for row in report.rows),
        report.release_count,
    ):
        raise ValueError("average_source_count must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("datetime interval must be nonnegative")
    delta = end - start
    total_microseconds = Decimal(
        delta.days * 86_400_000_000
        + delta.seconds * 1_000_000
        + delta.microseconds,
    )
    return _finite_decimal(total_microseconds / MICROSECONDS_PER_SECOND)


def _redact_reference(value: str) -> str:
    if _is_safe_public_reference(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _require_redacted_reference(field_name: str, value: object) -> str:
    _require_reference(field_name, value)
    if _is_safe_public_reference(value):
        return value
    if value.startswith("sha256:") and len(value) == 19:
        return value
    raise ValueError(f"{field_name} must be redacted")


def _is_safe_public_reference(value: str) -> bool:
    if not value.startswith("public-"):
        return False
    lowered = value.lower()
    return not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _require_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not be padded")
    lowered = value.lower()
    if "".join(("wal", "let")) in lowered:
        raise ValueError(f"{field_name} contains forbidden text")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must not be padded")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain restricted text")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    return _require_public_string(field_name, value)


def _require_surprise_status(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in SURPRISE_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")
    return value


def _require_known_reason_code(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _finite_decimal(value)


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _finite_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT) as context:
        try:
            return value.quantize(QUANT, context=context)
        except InvalidOperation as exc:
            raise ValueError("Decimal value must be quantizable") from exc


def _count(value: int) -> Decimal:
    return _finite_decimal(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _finite_decimal(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _finite_decimal(numerator / denominator)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total = _finite_decimal(total + value)
    return total


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) in (float, int):
        raise ValueError("payload must not contain public float or int values")
    return value


__all__ = (
    "DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLLS_SURPRISE_DIGEST_CONFIG_VERSION",
    "MarketResearchNonfarmPayrollsSurpriseDigestConfig",
    "MarketResearchNonfarmPayrollsSurpriseDigestInputRow",
    "MarketResearchNonfarmPayrollsSurpriseDigestReasonCodeCount",
    "MarketResearchNonfarmPayrollsSurpriseDigestReport",
    "MarketResearchNonfarmPayrollsSurpriseDigestRow",
    "build_market_research_nonfarm_payrolls_surprise_digest",
    "market_research_nonfarm_payrolls_surprise_digest_payload",
)
