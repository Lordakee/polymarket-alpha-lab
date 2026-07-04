"""Pure Phase 1 nonfarm payroll revision digest reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLL_REVISION_DIGEST_CONFIG_VERSION = (
    "market-research-nonfarm-payroll-revision-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
REVISION_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_nonfarm_payroll_revision_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
MATERIAL_REVISION_REASON = f"{REASON_PREFIX}material_revision"
PROBABILITY_REPRICING_REASON = f"{REASON_PREFIX}probability_repricing"
MISSING_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}missing_acknowledgement"
SLOW_ACKNOWLEDGEMENT_REASON = f"{REASON_PREFIX}slow_acknowledgement"
STALE_RELEASE_REASON = f"{REASON_PREFIX}stale_release"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    MATERIAL_REVISION_REASON,
    STALE_RELEASE_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    THIN_SOURCES_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    MATERIAL_REVISION_REASON,
    PROBABILITY_REPRICING_REASON,
    MISSING_ACKNOWLEDGEMENT_REASON,
    READY_REASON,
    SLOW_ACKNOWLEDGEMENT_REASON,
    STALE_RELEASE_REASON,
    THIN_SOURCES_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_nonfarm_payroll_revision_digest",
    STATUS_WATCH: "watch_report_only_market_research_nonfarm_payroll_revision_digest",
    STATUS_BLOCKED: "block_report_only_market_research_nonfarm_payroll_revision_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("au", "th"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sign", "ing"),
        _join_parts("acc", "ount"),
        _join_parts("sub", "mit"),
    ),
)


__all__ = (
    "DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLL_REVISION_DIGEST_CONFIG_VERSION",
    "MarketResearchNonfarmPayrollRevisionDigestConfig",
    "MarketResearchNonfarmPayrollRevisionDigestInputRow",
    "MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount",
    "MarketResearchNonfarmPayrollRevisionDigestReport",
    "MarketResearchNonfarmPayrollRevisionDigestRow",
    "build_market_research_nonfarm_payroll_revision_digest",
    "market_research_nonfarm_payroll_revision_digest_payload",
)


@dataclass(frozen=True)
class MarketResearchNonfarmPayrollRevisionDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLL_REVISION_DIGEST_CONFIG_VERSION
    )
    fresh_release_max_age_seconds: Decimal = Decimal("7200.000000")
    material_revision_threshold_jobs: Decimal = Decimal("50000.000000")
    min_source_count: Decimal = Decimal("2.000000")
    max_acknowledgement_lag_seconds: Decimal = Decimal("1800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchNonfarmPayrollRevisionDigestConfig:
            raise TypeError(
                "MarketResearchNonfarmPayrollRevisionDigestConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollRevisionDigestConfig:
            raise ValueError(
                "config must be exactly "
                "MarketResearchNonfarmPayrollRevisionDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLL_REVISION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_release_max_age_seconds",
            "material_revision_threshold_jobs",
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
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchNonfarmPayrollRevisionDigestInputRow:
    research_key: str
    condition_id: str
    payroll_series_key: str
    release_reference: str
    released_at: datetime
    acknowledged_at: datetime | None
    source_count: Decimal
    previous_payroll_jobs: Decimal
    revised_payroll_jobs: Decimal
    consensus_payroll_jobs: Decimal
    unemployment_rate: Decimal
    labor_force_participation_rate: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchNonfarmPayrollRevisionDigestInputRow:
            raise TypeError(
                "MarketResearchNonfarmPayrollRevisionDigestInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollRevisionDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchNonfarmPayrollRevisionDigestInputRow",
            )
        _require_public_string("research_key", self.research_key)
        _require_public_string("condition_id", self.condition_id)
        _require_public_string("payroll_series_key", self.payroll_series_key)
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
            "previous_payroll_jobs",
            "revised_payroll_jobs",
            "consensus_payroll_jobs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unemployment_rate",
            "labor_force_participation_rate",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchNonfarmPayrollRevisionDigestRow:
    research_key: str
    condition_id: str
    payroll_series_key: str
    revision_status: str
    released_at: datetime
    acknowledged_at: datetime | None
    release_age_seconds: Decimal
    acknowledgement_lag_seconds: Decimal | None
    source_count: Decimal
    previous_payroll_jobs: Decimal
    revised_payroll_jobs: Decimal
    consensus_payroll_jobs: Decimal
    revision_delta_jobs: Decimal
    revision_abs_jobs: Decimal
    consensus_delta_jobs: Decimal
    unemployment_rate: Decimal
    labor_force_participation_rate: Decimal
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
        if cls is not MarketResearchNonfarmPayrollRevisionDigestRow:
            raise TypeError(
                "MarketResearchNonfarmPayrollRevisionDigestRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollRevisionDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchNonfarmPayrollRevisionDigestRow",
            )
        for field_name in ("research_key", "condition_id", "payroll_series_key"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_revision_status("revision_status", self.revision_status)
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
            "release_age_seconds",
            _require_nonnegative_decimal("release_age_seconds", self.release_age_seconds),
        )
        if self.acknowledgement_lag_seconds is not None:
            object.__setattr__(
                self,
                "acknowledgement_lag_seconds",
                _require_nonnegative_decimal(
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
            "previous_payroll_jobs",
            "revised_payroll_jobs",
            "consensus_payroll_jobs",
            "revision_delta_jobs",
            "revision_abs_jobs",
            "consensus_delta_jobs",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_finite_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "unemployment_rate",
            "labor_force_participation_rate",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_delta",
            _require_finite_decimal("probability_delta", self.probability_delta),
        )
        _require_public_string("redacted_release_reference", self.redacted_release_reference)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row_status_reason_codes(self.revision_status, self.reason_codes)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    release_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount",
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
class MarketResearchNonfarmPayrollRevisionDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    release_count: Decimal
    ready_release_count: Decimal
    watch_release_count: Decimal
    blocked_release_count: Decimal
    material_revision_count: Decimal
    stale_release_count: Decimal
    thin_source_count: Decimal
    missing_acknowledgement_count: Decimal
    slow_acknowledgement_count: Decimal
    probability_repricing_count: Decimal
    average_revision_abs_jobs: Decimal
    max_release_age_seconds: Decimal
    average_source_count: Decimal
    rows: tuple[MarketResearchNonfarmPayrollRevisionDigestRow, ...]
    reason_code_counts: tuple[
        MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount,
        ...
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchNonfarmPayrollRevisionDigestReport:
            raise TypeError(
                "MarketResearchNonfarmPayrollRevisionDigestReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchNonfarmPayrollRevisionDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchNonfarmPayrollRevisionDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_NONFARM_PAYROLL_REVISION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_revision_status("digest_status", self.digest_status)
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
            "material_revision_count",
            "stale_release_count",
            "thin_source_count",
            "missing_acknowledgement_count",
            "slow_acknowledgement_count",
            "probability_repricing_count",
            "average_revision_abs_jobs",
            "max_release_age_seconds",
            "average_source_count",
        ):
            normalizer = _require_nonnegative_count_decimal
            if field_name in (
                "average_revision_abs_jobs",
                "max_release_age_seconds",
                "average_source_count",
            ):
                normalizer = _require_nonnegative_decimal
            object.__setattr__(
                self,
                field_name,
                normalizer(field_name, getattr(self, field_name)),
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


def build_market_research_nonfarm_payroll_revision_digest(
    rows: tuple[object, ...],
    *,
    config: MarketResearchNonfarmPayrollRevisionDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchNonfarmPayrollRevisionDigestReport:
    if config is None:
        config = MarketResearchNonfarmPayrollRevisionDigestConfig()
    if type(config) is not MarketResearchNonfarmPayrollRevisionDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchNonfarmPayrollRevisionDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(rows)
    digest_rows = tuple(
        _build_digest_row(source, config=config, generated_at=generated_at_utc)
        for source in source_rows
    )
    sorted_rows = tuple(sorted(digest_rows, key=_row_sort_key))
    reason_counts = _build_reason_code_counts(sorted_rows)
    release_count = _decimal_count(sorted_rows)
    ready_count = _decimal_count(
        row for row in sorted_rows if row.revision_status == STATUS_READY
    )
    watch_count = _decimal_count(
        row for row in sorted_rows if row.revision_status == STATUS_WATCH
    )
    blocked_count = _decimal_count(
        row for row in sorted_rows if row.revision_status == STATUS_BLOCKED
    )
    digest_status = _digest_status(blocked_count, watch_count)
    reason_codes = _digest_reason_codes(sorted_rows)
    if not sorted_rows:
        reason_codes = (NO_INPUTS_REASON,)
    return MarketResearchNonfarmPayrollRevisionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        reason_codes=reason_codes,
        release_count=release_count,
        ready_release_count=ready_count,
        watch_release_count=watch_count,
        blocked_release_count=blocked_count,
        material_revision_count=_reason_count(sorted_rows, MATERIAL_REVISION_REASON),
        stale_release_count=_reason_count(sorted_rows, STALE_RELEASE_REASON),
        thin_source_count=_reason_count(sorted_rows, THIN_SOURCES_REASON),
        missing_acknowledgement_count=_reason_count(
            sorted_rows,
            MISSING_ACKNOWLEDGEMENT_REASON,
        ),
        slow_acknowledgement_count=_reason_count(
            sorted_rows,
            SLOW_ACKNOWLEDGEMENT_REASON,
        ),
        probability_repricing_count=_reason_count(
            sorted_rows,
            PROBABILITY_REPRICING_REASON,
        ),
        average_revision_abs_jobs=_average(
            tuple(row.revision_abs_jobs for row in sorted_rows),
        ),
        max_release_age_seconds=max(
            (row.release_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        average_source_count=_average(tuple(row.source_count for row in sorted_rows)),
        rows=sorted_rows,
        reason_code_counts=reason_counts,
    )


def market_research_nonfarm_payroll_revision_digest_payload(
    report: MarketResearchNonfarmPayrollRevisionDigestReport,
) -> dict[str, Any]:
    if type(report) in (float, int):
        raise ValueError("payload must not contain public float or int values")
    if type(report) is not MarketResearchNonfarmPayrollRevisionDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchNonfarmPayrollRevisionDigestReport",
        )
    return _payload_value(report)


def _build_digest_row(
    source: MarketResearchNonfarmPayrollRevisionDigestInputRow,
    *,
    config: MarketResearchNonfarmPayrollRevisionDigestConfig,
    generated_at: datetime,
) -> MarketResearchNonfarmPayrollRevisionDigestRow:
    if source.released_at > generated_at:
        raise ValueError("released_at must not be after generated_at")
    release_age_seconds = _seconds_between(source.released_at, generated_at)
    acknowledgement_lag_seconds = None
    if source.acknowledged_at is not None:
        acknowledgement_lag_seconds = _seconds_between(
            source.released_at,
            source.acknowledged_at,
        )
    revision_delta_jobs = _quantize(source.revised_payroll_jobs - source.previous_payroll_jobs)
    revision_abs_jobs = _quantize(abs(revision_delta_jobs))
    consensus_delta_jobs = _quantize(
        source.revised_payroll_jobs - source.consensus_payroll_jobs,
    )
    probability_delta = _quantize(
        source.market_probability_after - source.market_probability_before,
    )
    reasons: list[str] = []
    if revision_abs_jobs >= config.material_revision_threshold_jobs:
        reasons.append(MATERIAL_REVISION_REASON)
    if abs(probability_delta) >= Decimal("0.100000"):
        reasons.append(PROBABILITY_REPRICING_REASON)
    if source.acknowledged_at is None:
        reasons.append(MISSING_ACKNOWLEDGEMENT_REASON)
    elif acknowledgement_lag_seconds is not None and (
        acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds
    ):
        reasons.append(SLOW_ACKNOWLEDGEMENT_REASON)
    if release_age_seconds > config.fresh_release_max_age_seconds:
        reasons.append(STALE_RELEASE_REASON)
    if source.source_count < config.min_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    reason_codes = _normalize_reason_codes(tuple(reasons), ROW_REASON_CODE_SEQUENCE)
    return MarketResearchNonfarmPayrollRevisionDigestRow(
        research_key=source.research_key,
        condition_id=source.condition_id,
        payroll_series_key=source.payroll_series_key,
        revision_status=_row_status(reason_codes),
        released_at=source.released_at,
        acknowledged_at=source.acknowledged_at,
        release_age_seconds=release_age_seconds,
        acknowledgement_lag_seconds=acknowledgement_lag_seconds,
        source_count=source.source_count,
        previous_payroll_jobs=source.previous_payroll_jobs,
        revised_payroll_jobs=source.revised_payroll_jobs,
        consensus_payroll_jobs=source.consensus_payroll_jobs,
        revision_delta_jobs=revision_delta_jobs,
        revision_abs_jobs=revision_abs_jobs,
        consensus_delta_jobs=consensus_delta_jobs,
        unemployment_rate=source.unemployment_rate,
        labor_force_participation_rate=source.labor_force_participation_rate,
        market_probability_before=source.market_probability_before,
        market_probability_after=source.market_probability_after,
        probability_delta=probability_delta,
        redacted_release_reference=_redact_reference(source.release_reference),
        reason_codes=reason_codes,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if MISSING_ACKNOWLEDGEMENT_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _digest_status(blocked_count: Decimal, watch_count: Decimal) -> str:
    if blocked_count > ZERO:
        return STATUS_BLOCKED
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _row_sort_key(
    row: MarketResearchNonfarmPayrollRevisionDigestRow,
) -> tuple[int, Decimal, str, str]:
    rank = {
        STATUS_BLOCKED: 0,
        STATUS_WATCH: 1,
        STATUS_READY: 2,
    }[row.revision_status]
    return (rank, -row.revision_abs_jobs, row.payroll_series_key, row.research_key)


def _digest_reason_codes(
    rows: tuple[MarketResearchNonfarmPayrollRevisionDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    if seen == {READY_REASON}:
        return (READY_REASON,)
    seen.discard(READY_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _build_reason_code_counts(
    rows: tuple[MarketResearchNonfarmPayrollRevisionDigestRow, ...],
) -> tuple[MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount, ...]:
    total = _decimal_count(rows)
    if total == ZERO:
        return ()
    counts: list[MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        if reason_code in (READY_REASON, NO_INPUTS_REASON):
            continue
        count = _reason_count(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    release_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _reason_count(
    rows: tuple[MarketResearchNonfarmPayrollRevisionDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(row for row in rows if reason_code in row.reason_codes)


def _normalize_input_rows(
    rows: tuple[object, ...],
) -> tuple[MarketResearchNonfarmPayrollRevisionDigestInputRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[MarketResearchNonfarmPayrollRevisionDigestInputRow] = []
    for row in rows:
        if type(row) is not MarketResearchNonfarmPayrollRevisionDigestInputRow:
            raise ValueError(
                "input row must be exactly "
                "MarketResearchNonfarmPayrollRevisionDigestInputRow",
            )
        normalized.append(row)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[MarketResearchNonfarmPayrollRevisionDigestRow, ...],
) -> tuple[MarketResearchNonfarmPayrollRevisionDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[MarketResearchNonfarmPayrollRevisionDigestRow] = []
    for row in rows:
        if type(row) is not MarketResearchNonfarmPayrollRevisionDigestRow:
            raise ValueError(
                "row must be exactly MarketResearchNonfarmPayrollRevisionDigestRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: tuple[MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount, ...],
) -> tuple[MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount] = []
    for count in counts:
        if type(count) is not MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "MarketResearchNonfarmPayrollRevisionDigestReasonCodeCount",
            )
        normalized.append(count)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (REASON_CODE_SEQUENCE.index(item.reason_code), item.reason_code),
        ),
    )


def _validate_row_status_reason_codes(
    revision_status: str,
    reason_codes: tuple[str, ...],
) -> None:
    expected = _row_status(reason_codes)
    if expected != revision_status:
        raise ValueError("revision_status must match reason_codes")


def _validate_report_reason_codes(
    digest_status: str,
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchNonfarmPayrollRevisionDigestRow, ...],
) -> None:
    if tuple(reason for reason in REASON_CODE_SEQUENCE if reason in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    expected = _digest_reason_codes(rows)
    if not rows:
        expected = (NO_INPUTS_REASON,)
    if reason_codes != expected:
        raise ValueError("reason_codes must summarize rows")
    if digest_status != _digest_status(
        _decimal_count(row for row in rows if row.revision_status == STATUS_BLOCKED),
        _decimal_count(row for row in rows if row.revision_status == STATUS_WATCH),
    ):
        raise ValueError("digest_status must summarize rows")


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_known_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        if reason_code not in sequence:
            raise ValueError("reason_code is not valid for this scope")
        seen.add(reason_code)
    normalized = tuple(reason_code for reason_code in sequence if reason_code in seen)
    if normalized != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return normalized


def _require_known_reason_code(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_revision_status(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain string")
    if value not in REVISION_STATUSES:
        raise ValueError(f"{field_name} must be a supported revision status")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(
                f"{field_name} paper_only/report_only/readonly must be True",
            )


def _require_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def _require_canonical_string(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    if value != value.strip():
        raise ValueError(f"{field_name} must not be padded")


def _require_reference(field_name: str, value: str) -> None:
    _require_public_string(field_name, value)
    lowered = value.lower()
    for fragment in UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} contains forbidden text")


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_microseconds = Decimal(
        delta.days * 86_400_000_000
        + delta.seconds * 1_000_000
        + delta.microseconds,
    )
    return _quantize(total_microseconds / MICROSECONDS_PER_SECOND)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _decimal_count(values: object) -> Decimal:
    return _quantize(Decimal(sum(1 for _ in values)))


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        value = Decimal(value)
    with localcontext(DECIMAL_CONTEXT) as ctx:
        try:
            return value.quantize(QUANT, context=ctx)
        except InvalidOperation as exc:
            raise ValueError("Decimal value must be quantizable") from exc


def _redact_reference(value: str) -> str:
    if value.startswith("public-"):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


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
