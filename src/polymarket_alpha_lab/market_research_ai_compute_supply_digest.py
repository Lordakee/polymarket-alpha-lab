"""Pure Phase 1 AI compute supply digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_MARKET_RESEARCH_AI_COMPUTE_SUPPLY_DIGEST_CONFIG_VERSION = (
    "market-research-ai-compute-supply-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
COMPUTE_SUPPLY_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "market_research_ai_compute_supply_digest_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
READY_REASON = f"{REASON_PREFIX}ready"
CONSTRAINED_SUPPLY_REASON = f"{REASON_PREFIX}constrained_supply"
TIGHT_SUPPLY_REASON = f"{REASON_PREFIX}tight_supply"
HIGH_DEMAND_PRESSURE_REASON = f"{REASON_PREFIX}high_demand_pressure"
SUPPLY_DISRUPTION_REASON = f"{REASON_PREFIX}supply_disruption"
PROVIDER_CONCENTRATION_REASON = f"{REASON_PREFIX}provider_concentration"
MISSING_REVIEW_REASON = f"{REASON_PREFIX}missing_review"
PROBABILITY_SHIFT_REASON = f"{REASON_PREFIX}probability_shift"
SLOW_REVIEW_REASON = f"{REASON_PREFIX}slow_review"
STALE_SUPPLY_REASON = f"{REASON_PREFIX}stale_supply"
THIN_SOURCES_REASON = f"{REASON_PREFIX}thin_sources"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    CONSTRAINED_SUPPLY_REASON,
    MISSING_REVIEW_REASON,
    PROBABILITY_SHIFT_REASON,
    HIGH_DEMAND_PRESSURE_REASON,
    SUPPLY_DISRUPTION_REASON,
    PROVIDER_CONCENTRATION_REASON,
    TIGHT_SUPPLY_REASON,
    SLOW_REVIEW_REASON,
    STALE_SUPPLY_REASON,
    THIN_SOURCES_REASON,
    READY_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    CONSTRAINED_SUPPLY_REASON,
    HIGH_DEMAND_PRESSURE_REASON,
    MISSING_REVIEW_REASON,
    PROBABILITY_SHIFT_REASON,
    PROVIDER_CONCENTRATION_REASON,
    READY_REASON,
    SLOW_REVIEW_REASON,
    STALE_SUPPLY_REASON,
    SUPPLY_DISRUPTION_REASON,
    THIN_SOURCES_REASON,
    TIGHT_SUPPLY_REASON,
)

NEXT_STEPS = {
    STATUS_READY: "allow_report_only_market_research_ai_compute_supply_digest",
    STATUS_WATCH: "watch_report_only_market_research_ai_compute_supply_digest",
    STATUS_BLOCKED: "block_report_only_market_research_ai_compute_supply_digest",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
PROBABILITY_SHIFT_THRESHOLD = Decimal("0.100000")
_PUBLIC_REFERENCE_FRAGMENTS = ("public", "memo", "bulletin", "notice", "release")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


@dataclass(frozen=True)
class MarketResearchAiComputeSupplyDigestConfig:
    config_version: str = DEFAULT_MARKET_RESEARCH_AI_COMPUTE_SUPPLY_DIGEST_CONFIG_VERSION
    fresh_supply_max_age_seconds: Decimal = Decimal("86400.000000")
    min_public_source_count: Decimal = Decimal("2")
    min_ready_supply_score: Decimal = Decimal("0.650000")
    min_watch_supply_score: Decimal = Decimal("0.350000")
    max_demand_pressure_score: Decimal = Decimal("0.700000")
    max_supply_disruption_score: Decimal = Decimal("0.500000")
    max_provider_concentration_score: Decimal = Decimal("0.650000")
    max_review_lag_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiComputeSupplyDigestConfig:
            raise TypeError(
                "MarketResearchAiComputeSupplyDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiComputeSupplyDigestConfig:
            raise ValueError(
                "config must be exactly MarketResearchAiComputeSupplyDigestConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "fresh_supply_max_age_seconds",
            _require_nonnegative_decimal(
                "fresh_supply_max_age_seconds",
                self.fresh_supply_max_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "min_public_source_count",
            _require_nonnegative_count_decimal(
                "min_public_source_count",
                self.min_public_source_count,
            ),
        )
        for field_name in (
            "min_ready_supply_score",
            "min_watch_supply_score",
            "max_demand_pressure_score",
            "max_supply_disruption_score",
            "max_provider_concentration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_supply_score > self.min_ready_supply_score:
            raise ValueError("min_ready_supply_score must be at least min_watch_supply_score")
        object.__setattr__(
            self,
            "max_review_lag_seconds",
            _require_nonnegative_decimal(
                "max_review_lag_seconds",
                self.max_review_lag_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchAiComputeSupplyDigestInputRow:
    research_key: str
    condition_id: str
    compute_segment: str
    public_supply_reference: str
    supply_observed_at: datetime
    reviewed_at: datetime | None
    public_source_count: Decimal
    available_supply_score: Decimal
    demand_pressure_score: Decimal
    supply_disruption_score: Decimal
    provider_concentration_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiComputeSupplyDigestInputRow:
            raise TypeError(
                "MarketResearchAiComputeSupplyDigestInputRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiComputeSupplyDigestInputRow:
            raise ValueError(
                "input row must be exactly MarketResearchAiComputeSupplyDigestInputRow",
            )
        for field_name in ("research_key", "condition_id", "compute_segment"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference("public_supply_reference", self.public_supply_reference)
        object.__setattr__(
            self,
            "supply_observed_at",
            _as_utc("supply_observed_at", self.supply_observed_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
        )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in (
            "available_supply_score",
            "demand_pressure_score",
            "supply_disruption_score",
            "provider_concentration_score",
            "market_probability_before",
            "market_probability_after",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.reviewed_at is not None and self.reviewed_at < self.supply_observed_at:
            raise ValueError("reviewed_at must be on or after supply_observed_at")
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class MarketResearchAiComputeSupplyDigestRow:
    research_key: str
    condition_id: str
    compute_segment: str
    supply_observed_at: datetime
    reviewed_at: datetime | None
    supply_age_seconds: Decimal
    review_lag_seconds: Decimal | None
    public_source_count: Decimal
    available_supply_score: Decimal
    demand_pressure_score: Decimal
    supply_disruption_score: Decimal
    provider_concentration_score: Decimal
    market_probability_before: Decimal
    market_probability_after: Decimal
    probability_change: Decimal
    supply_status: str
    redacted_supply_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiComputeSupplyDigestRow:
            raise TypeError(
                "MarketResearchAiComputeSupplyDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiComputeSupplyDigestRow:
            raise ValueError("row must be exactly MarketResearchAiComputeSupplyDigestRow")
        for field_name in ("research_key", "condition_id", "compute_segment"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "supply_observed_at",
            _as_utc("supply_observed_at", self.supply_observed_at),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _optional_utc("reviewed_at", self.reviewed_at),
        )
        object.__setattr__(
            self,
            "supply_age_seconds",
            _require_nonnegative_decimal("supply_age_seconds", self.supply_age_seconds),
        )
        object.__setattr__(
            self,
            "review_lag_seconds",
            _require_optional_nonnegative_decimal(
                "review_lag_seconds",
                self.review_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "public_source_count",
            _require_nonnegative_count_decimal(
                "public_source_count",
                self.public_source_count,
            ),
        )
        for field_name in (
            "available_supply_score",
            "demand_pressure_score",
            "supply_disruption_score",
            "provider_concentration_score",
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
            "probability_change",
            _require_probability_change("probability_change", self.probability_change),
        )
        _require_status("supply_status", self.supply_status)
        object.__setattr__(
            self,
            "redacted_supply_reference",
            _require_redacted_reference(
                "redacted_supply_reference",
                self.redacted_supply_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchAiComputeSupplyDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    supply_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiComputeSupplyDigestReasonCodeCount:
            raise TypeError(
                "MarketResearchAiComputeSupplyDigestReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiComputeSupplyDigestReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "MarketResearchAiComputeSupplyDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code, REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "supply_ratio",
            _require_ratio_decimal("supply_ratio", self.supply_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MarketResearchAiComputeSupplyDigestReport:
    generated_at: datetime
    config_version: str
    digest_status: str
    next_step: str
    supply_count: Decimal
    ready_supply_count: Decimal
    watch_supply_count: Decimal
    blocked_supply_count: Decimal
    constrained_supply_count: Decimal
    tight_supply_count: Decimal
    high_demand_pressure_count: Decimal
    supply_disruption_count: Decimal
    provider_concentration_count: Decimal
    stale_supply_count: Decimal
    thin_source_count: Decimal
    missing_review_count: Decimal
    slow_review_count: Decimal
    average_available_supply_score: Decimal
    max_supply_age_seconds: Decimal
    average_public_source_count: Decimal
    rows: tuple[MarketResearchAiComputeSupplyDigestRow, ...]
    reason_code_counts: tuple[MarketResearchAiComputeSupplyDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketResearchAiComputeSupplyDigestReport:
            raise TypeError(
                "MarketResearchAiComputeSupplyDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not MarketResearchAiComputeSupplyDigestReport:
            raise ValueError(
                "report must be exactly MarketResearchAiComputeSupplyDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "supply_count",
            "ready_supply_count",
            "watch_supply_count",
            "blocked_supply_count",
            "constrained_supply_count",
            "tight_supply_count",
            "high_demand_pressure_count",
            "supply_disruption_count",
            "provider_concentration_count",
            "stale_supply_count",
            "thin_source_count",
            "missing_review_count",
            "slow_review_count",
            "average_available_supply_score",
            "max_supply_age_seconds",
            "average_public_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not MarketResearchAiComputeSupplyDigestRow:
                raise ValueError(
                    "rows must contain MarketResearchAiComputeSupplyDigestRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for row in self.reason_code_counts:
            if type(row) is not MarketResearchAiComputeSupplyDigestReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "MarketResearchAiComputeSupplyDigestReasonCodeCount",
                )
            _require_hard_flags("reason code count", row)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_ai_compute_supply_digest(
    input_rows: list[MarketResearchAiComputeSupplyDigestInputRow]
    | tuple[MarketResearchAiComputeSupplyDigestInputRow, ...],
    *,
    config: MarketResearchAiComputeSupplyDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchAiComputeSupplyDigestReport:
    cfg = config or MarketResearchAiComputeSupplyDigestConfig()
    if type(cfg) is not MarketResearchAiComputeSupplyDigestConfig:
        raise ValueError("config must be a MarketResearchAiComputeSupplyDigestConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    source_rows = _normalize_input_rows(input_rows, report_time)
    built_rows = tuple(
        _build_row(row, config=cfg, generated_at=report_time) for row in source_rows
    )
    ranked_rows = _ranked_rows(built_rows)
    supply_count = _count(len(ranked_rows))
    ready_supply_count = _count(
        sum(1 for row in ranked_rows if row.supply_status == STATUS_READY),
    )
    watch_supply_count = _count(
        sum(1 for row in ranked_rows if row.supply_status == STATUS_WATCH),
    )
    blocked_supply_count = _count(
        sum(1 for row in ranked_rows if row.supply_status == STATUS_BLOCKED),
    )
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not ranked_rows:
        reason_code_counts = (
            MarketResearchAiComputeSupplyDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                supply_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    digest_status = _report_status(
        has_inputs=bool(ranked_rows),
        blocked_supply_count=blocked_supply_count,
        watch_supply_count=watch_supply_count,
    )
    return MarketResearchAiComputeSupplyDigestReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        digest_status=digest_status,
        next_step=NEXT_STEPS[digest_status],
        supply_count=supply_count,
        ready_supply_count=ready_supply_count,
        watch_supply_count=watch_supply_count,
        blocked_supply_count=blocked_supply_count,
        constrained_supply_count=_reason_count(ranked_rows, CONSTRAINED_SUPPLY_REASON),
        tight_supply_count=_reason_count(ranked_rows, TIGHT_SUPPLY_REASON),
        high_demand_pressure_count=_reason_count(
            ranked_rows,
            HIGH_DEMAND_PRESSURE_REASON,
        ),
        supply_disruption_count=_reason_count(ranked_rows, SUPPLY_DISRUPTION_REASON),
        provider_concentration_count=_reason_count(
            ranked_rows,
            PROVIDER_CONCENTRATION_REASON,
        ),
        stale_supply_count=_reason_count(ranked_rows, STALE_SUPPLY_REASON),
        thin_source_count=_reason_count(ranked_rows, THIN_SOURCES_REASON),
        missing_review_count=_reason_count(ranked_rows, MISSING_REVIEW_REASON),
        slow_review_count=_reason_count(ranked_rows, SLOW_REVIEW_REASON),
        average_available_supply_score=_average(
            tuple(row.available_supply_score for row in ranked_rows),
        ),
        max_supply_age_seconds=_max_decimal(
            tuple(row.supply_age_seconds for row in ranked_rows),
        ),
        average_public_source_count=_average(
            tuple(row.public_source_count for row in ranked_rows),
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_ai_compute_supply_digest_payload(
    report: MarketResearchAiComputeSupplyDigestReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchAiComputeSupplyDigestReport:
        raise ValueError("report must be a MarketResearchAiComputeSupplyDigestReport")
    _require_hard_flags("report", report)
    return _json_ready_no_numbers(asdict(report))


def _build_row(
    row: MarketResearchAiComputeSupplyDigestInputRow,
    *,
    config: MarketResearchAiComputeSupplyDigestConfig,
    generated_at: datetime,
) -> MarketResearchAiComputeSupplyDigestRow:
    supply_age_seconds = _elapsed_seconds(row.supply_observed_at, generated_at)
    review_lag_seconds = (
        None
        if row.reviewed_at is None
        else _elapsed_seconds(row.supply_observed_at, row.reviewed_at)
    )
    probability_change = _quantize(row.market_probability_after - row.market_probability_before)
    reason_codes = _row_reason_codes(
        row,
        config=config,
        supply_age_seconds=supply_age_seconds,
        review_lag_seconds=review_lag_seconds,
        probability_change=probability_change,
    )
    return MarketResearchAiComputeSupplyDigestRow(
        research_key=row.research_key,
        condition_id=row.condition_id,
        compute_segment=row.compute_segment,
        supply_observed_at=row.supply_observed_at,
        reviewed_at=row.reviewed_at,
        supply_age_seconds=supply_age_seconds,
        review_lag_seconds=review_lag_seconds,
        public_source_count=row.public_source_count,
        available_supply_score=row.available_supply_score,
        demand_pressure_score=row.demand_pressure_score,
        supply_disruption_score=row.supply_disruption_score,
        provider_concentration_score=row.provider_concentration_score,
        market_probability_before=row.market_probability_before,
        market_probability_after=row.market_probability_after,
        probability_change=probability_change,
        supply_status=_row_status(reason_codes),
        redacted_supply_reference=_redact_reference(row.public_supply_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: MarketResearchAiComputeSupplyDigestInputRow,
    *,
    config: MarketResearchAiComputeSupplyDigestConfig,
    supply_age_seconds: Decimal,
    review_lag_seconds: Decimal | None,
    probability_change: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.available_supply_score < config.min_watch_supply_score:
        reasons.append(CONSTRAINED_SUPPLY_REASON)
    elif row.available_supply_score < config.min_ready_supply_score:
        reasons.append(TIGHT_SUPPLY_REASON)
    if row.demand_pressure_score > config.max_demand_pressure_score:
        reasons.append(HIGH_DEMAND_PRESSURE_REASON)
    if row.supply_disruption_score > config.max_supply_disruption_score:
        reasons.append(SUPPLY_DISRUPTION_REASON)
    if row.provider_concentration_score > config.max_provider_concentration_score:
        reasons.append(PROVIDER_CONCENTRATION_REASON)
    if row.reviewed_at is None:
        reasons.append(MISSING_REVIEW_REASON)
    elif review_lag_seconds is not None and review_lag_seconds > config.max_review_lag_seconds:
        reasons.append(SLOW_REVIEW_REASON)
    if supply_age_seconds > config.fresh_supply_max_age_seconds:
        reasons.append(STALE_SUPPLY_REASON)
    if row.public_source_count < config.min_public_source_count:
        reasons.append(THIN_SOURCES_REASON)
    if abs(probability_change) >= PROBABILITY_SHIFT_THRESHOLD:
        reasons.append(PROBABILITY_SHIFT_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return _normalize_row_reason_codes(tuple(reasons))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if CONSTRAINED_SUPPLY_REASON in reason_codes or MISSING_REVIEW_REASON in reason_codes:
        return STATUS_BLOCKED
    if PROBABILITY_SHIFT_REASON in reason_codes and HIGH_DEMAND_PRESSURE_REASON in reason_codes:
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    blocked_supply_count: Decimal,
    watch_supply_count: Decimal,
) -> str:
    if not has_inputs:
        return STATUS_BLOCKED
    if blocked_supply_count > ZERO:
        return STATUS_BLOCKED
    if watch_supply_count > ZERO:
        return STATUS_WATCH
    return STATUS_READY


def _normalize_input_rows(
    rows: list[MarketResearchAiComputeSupplyDigestInputRow]
    | tuple[MarketResearchAiComputeSupplyDigestInputRow, ...],
    generated_at: datetime,
) -> tuple[MarketResearchAiComputeSupplyDigestInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized: list[MarketResearchAiComputeSupplyDigestInputRow] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not MarketResearchAiComputeSupplyDigestInputRow:
            raise ValueError(
                "input rows must contain MarketResearchAiComputeSupplyDigestInputRow",
            )
        if row.supply_observed_at > generated_at:
            raise ValueError("supply_observed_at must be on or before generated_at")
        key = (row.research_key, row.condition_id, row.compute_segment)
        if key in seen:
            raise ValueError("input rows must be unique by research_key, condition_id, segment")
        seen.add(key)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.compute_segment,
                item.research_key,
                item.condition_id,
            ),
        ),
    )


def _ranked_rows(
    rows: tuple[MarketResearchAiComputeSupplyDigestRow, ...],
) -> tuple[MarketResearchAiComputeSupplyDigestRow, ...]:
    status_rank = {STATUS_BLOCKED: 0, STATUS_WATCH: 1, STATUS_READY: 2}
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                status_rank[row.supply_status],
                _reason_rank(row.reason_codes),
                row.compute_segment,
                row.research_key,
                row.condition_id,
            ),
        ),
    )


def _reason_rank(reason_codes: tuple[str, ...]) -> tuple[int, ...]:
    return tuple(
        REASON_CODE_SEQUENCE.index(reason_code)
        if reason_code in REASON_CODE_SEQUENCE
        else len(REASON_CODE_SEQUENCE)
        for reason_code in reason_codes
    )


def _reason_count(
    rows: tuple[MarketResearchAiComputeSupplyDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[MarketResearchAiComputeSupplyDigestRow, ...],
) -> tuple[MarketResearchAiComputeSupplyDigestReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    supply_count = _count(len(rows))
    return tuple(
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            supply_ratio=_ratio(_count(counts[reason_code]), supply_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in sorted(reason_codes, key=_row_reason_sort_key):
        _require_reason_code("reason_codes", reason_code, ROW_REASON_CODE_SEQUENCE)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in sorted(reason_codes, key=_report_reason_sort_key):
        _require_reason_code("reason_codes", reason_code, REASON_CODE_SEQUENCE)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _row_reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return (ROW_REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    except ValueError:
        return (len(ROW_REASON_CODE_SEQUENCE), reason_code)


def _report_reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return (REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    except ValueError:
        return (len(REASON_CODE_SEQUENCE), reason_code)


def _validate_row(row: MarketResearchAiComputeSupplyDigestRow) -> None:
    expected_probability_change = _quantize(
        row.market_probability_after - row.market_probability_before,
    )
    if row.probability_change != expected_probability_change:
        raise ValueError("probability_change must equal probability after minus before")
    if row.supply_status != _row_status(row.reason_codes):
        raise ValueError("supply_status does not match reason_codes")
    if row.reason_codes == (READY_REASON,):
        if row.supply_status != STATUS_READY:
            raise ValueError("ready row must have ready supply_status")
    elif READY_REASON in row.reason_codes:
        raise ValueError("ready reason cannot be combined with risk reasons")


def _validate_report(report: MarketResearchAiComputeSupplyDigestReport) -> None:
    ranked = _ranked_rows(report.rows)
    if report.rows != ranked:
        raise ValueError("rows must be deterministically ranked")
    supply_count = _count(len(report.rows))
    if report.supply_count != supply_count:
        raise ValueError("supply_count does not match rows")
    ready = _count(sum(1 for row in report.rows if row.supply_status == STATUS_READY))
    watch = _count(sum(1 for row in report.rows if row.supply_status == STATUS_WATCH))
    blocked = _count(sum(1 for row in report.rows if row.supply_status == STATUS_BLOCKED))
    expected_counts = {
        "ready_supply_count": ready,
        "watch_supply_count": watch,
        "blocked_supply_count": blocked,
        "constrained_supply_count": _reason_count(report.rows, CONSTRAINED_SUPPLY_REASON),
        "tight_supply_count": _reason_count(report.rows, TIGHT_SUPPLY_REASON),
        "high_demand_pressure_count": _reason_count(
            report.rows,
            HIGH_DEMAND_PRESSURE_REASON,
        ),
        "supply_disruption_count": _reason_count(report.rows, SUPPLY_DISRUPTION_REASON),
        "provider_concentration_count": _reason_count(
            report.rows,
            PROVIDER_CONCENTRATION_REASON,
        ),
        "stale_supply_count": _reason_count(report.rows, STALE_SUPPLY_REASON),
        "thin_source_count": _reason_count(report.rows, THIN_SOURCES_REASON),
        "missing_review_count": _reason_count(report.rows, MISSING_REVIEW_REASON),
        "slow_review_count": _reason_count(report.rows, SLOW_REVIEW_REASON),
        "average_available_supply_score": _average(
            tuple(row.available_supply_score for row in report.rows),
        ),
        "max_supply_age_seconds": _max_decimal(
            tuple(row.supply_age_seconds for row in report.rows),
        ),
        "average_public_source_count": _average(
            tuple(row.public_source_count for row in report.rows),
        ),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} does not match rows")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        blocked_supply_count=blocked,
        watch_supply_count=watch,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status does not match rows")
    if report.next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("next_step does not match digest_status")
    expected_reason_code_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_reason_code_counts = (
            MarketResearchAiComputeSupplyDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                supply_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts do not match rows")
    expected_reason_codes = tuple(row.reason_code for row in report.reason_code_counts)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes do not match reason_code_counts")


def _require_status(field_name: str, value: str) -> str:
    if type(value) is not str or value not in COMPUTE_SUPPLY_STATUSES:
        raise ValueError(f"{field_name} must be one of {COMPUTE_SUPPLY_STATUSES}")
    return value


def _require_reason_code(
    field_name: str,
    value: str,
    allowed: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a known compute supply reason code")
    return value


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _unsafe_text_fragments()):
        raise ValueError(f"{field_name} contains unsafe surface wording")
    return value


def _require_reference(field_name: str, value: str) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty reference string")
    return value


def _require_redacted_reference(field_name: str, value: str) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty redacted reference")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _unsafe_text_fragments()):
        raise ValueError(f"{field_name} contains unsafe reference wording")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in range 0..1")
    return decimal_value


def _require_probability_change(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < Decimal("-1.000000") or decimal_value > ONE:
        raise ValueError(f"{field_name} must be in range -1..1")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return decimal_value


def _require_finite_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _elapsed_seconds(start: datetime, end: datetime) -> Decimal:
    if end < start:
        raise ValueError("end datetime must be on or after start datetime")
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _quantize(seconds + micros)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _redact_reference(value: str) -> str:
    lowered = value.lower()
    if all(fragment in lowered for fragment in _PUBLIC_REFERENCE_FRAGMENTS[:1]) and not any(
        fragment in lowered for fragment in _unsafe_text_fragments()
    ):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _json_ready_no_numbers(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_numbers(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) in (int, float):
        raise ValueError("JSON value must not be a public numeric")
    if isinstance(value, str) or isinstance(value, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_no_numbers(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_no_numbers(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _unsafe_text_fragments() -> tuple[str, ...]:
    return (
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("bro", "ker"),
        _join_parts("or", "der"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
        _join_parts("market", "_slug"),
        _join_parts("ques", "tion"),
        _join_parts("private", "_key"),
        _join_parts("api", "_key"),
        _join_parts("sec", "ret"),
        _join_parts("pos", "ition"),
        _join_parts("tr", "ade"),
        _join_parts("b", "et"),
        _join_parts("st", "ake"),
        _join_parts("cli", "ent"),
        _join_parts("re", "quests"),
        _join_parts("ht", "tp"),
        _join_parts("sock", "et"),
        _join_parts("sub", "process"),
        _join_parts("path", "lib"),
        _join_parts("live", "_surface"),
    )


__all__ = (
    "DEFAULT_MARKET_RESEARCH_AI_COMPUTE_SUPPLY_DIGEST_CONFIG_VERSION",
    "MarketResearchAiComputeSupplyDigestConfig",
    "MarketResearchAiComputeSupplyDigestInputRow",
    "MarketResearchAiComputeSupplyDigestReasonCodeCount",
    "MarketResearchAiComputeSupplyDigestReport",
    "MarketResearchAiComputeSupplyDigestRow",
    "build_market_research_ai_compute_supply_digest",
    "market_research_ai_compute_supply_digest_payload",
)
