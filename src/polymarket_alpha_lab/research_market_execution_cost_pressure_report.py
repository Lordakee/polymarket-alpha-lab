"""Pure public execution cost pressure report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_EXECUTION_COST_PRESSURE_CONFIG_VERSION = (
    "research-market-execution-cost-pressure-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "research_market_execution_cost_pressure_"
NO_OBSERVATIONS_REASON = f"{REASON_PREFIX}no_observations"
CLEAR_REASON = f"{REASON_PREFIX}clear"
PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}pressure_block"
PRESSURE_WATCH_REASON = f"{REASON_PREFIX}pressure_watch"
TAKER_FEE_BLOCK_REASON = f"{REASON_PREFIX}taker_fee_block"
TAKER_FEE_WATCH_REASON = f"{REASON_PREFIX}taker_fee_watch"
SPREAD_BLOCK_REASON = f"{REASON_PREFIX}spread_block"
SPREAD_WATCH_REASON = f"{REASON_PREFIX}spread_watch"
DEPTH_SHORTFALL_BLOCK_REASON = f"{REASON_PREFIX}depth_shortfall_block"
DEPTH_SHORTFALL_WATCH_REASON = f"{REASON_PREFIX}depth_shortfall_watch"
LIQUIDITY_CONCENTRATION_BLOCK_REASON = f"{REASON_PREFIX}liquidity_concentration_block"
LIQUIDITY_CONCENTRATION_WATCH_REASON = f"{REASON_PREFIX}liquidity_concentration_watch"
STALE_BOOK_BLOCK_REASON = f"{REASON_PREFIX}stale_book_block"
STALE_BOOK_WATCH_REASON = f"{REASON_PREFIX}stale_book_watch"
LATENCY_HAIRCUT_BLOCK_REASON = f"{REASON_PREFIX}latency_haircut_block"
LATENCY_HAIRCUT_WATCH_REASON = f"{REASON_PREFIX}latency_haircut_watch"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

PUBLIC_LABEL_DENY_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "market-slug",
    "question",
    "source_id",
    "source_url",
    "source_text",
    "source_ref",
    "source_reference",
    "raw",
    "://",
    "?",
    "d" + "sn",
    "table",
    "tok" + "en",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "pos" + "ition",
    "b" + "uy",
    "s" + "ell",
    "reco" + "mmend",
    "siz" + "ing",
    "sub" + "mit",
    "can" + "cel",
    "li" + "ve",
)

PAYLOAD_DENY_FRAGMENTS = (
    "candidate",
    "market_id",
    "market_slug",
    "market-slug",
    "question",
    "source_id",
    "source_ref",
    "source_reference",
    "source_url",
    "source_text",
    "raw_market",
    "raw_source",
    "://",
    "?",
    "d" + "sn",
    "table",
    "tok" + "en",
    "wal" + "let",
    "au" + "th",
    "or" + "der",
    "tra" + "de",
    "pos" + "ition",
    "b" + "uy",
    "s" + "ell",
    "reco" + "mmend",
    "siz" + "ing",
    "sub" + "mit",
    "can" + "cel",
    "li" + "ve",
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_EXECUTION_COST_PRESSURE_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketExecutionCostPressureConfig",
    "ResearchMarketExecutionCostPressureObservation",
    "ResearchMarketExecutionCostPressureReasonCodeCount",
    "ResearchMarketExecutionCostPressureReport",
    "ResearchMarketExecutionCostPressureRow",
    "build_research_market_execution_cost_pressure_report",
    "research_market_execution_cost_pressure_report_digest",
    "research_market_execution_cost_pressure_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketExecutionCostPressureConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_EXECUTION_COST_PRESSURE_CONFIG_VERSION
    watch_execution_cost_pressure: Decimal = Decimal("0.350000")
    block_execution_cost_pressure: Decimal = Decimal("0.700000")
    watch_taker_fee_ratio: Decimal = Decimal("0.020000")
    block_taker_fee_ratio: Decimal = Decimal("0.050000")
    watch_spread_ratio: Decimal = Decimal("0.040000")
    block_spread_ratio: Decimal = Decimal("0.100000")
    watch_depth_shortfall_ratio: Decimal = Decimal("0.250000")
    block_depth_shortfall_ratio: Decimal = Decimal("0.600000")
    watch_liquidity_concentration_ratio: Decimal = Decimal("0.500000")
    block_liquidity_concentration_ratio: Decimal = Decimal("0.800000")
    watch_stale_book_age_seconds: Decimal = Decimal("300.000000")
    block_stale_book_age_seconds: Decimal = Decimal("900.000000")
    watch_latency_haircut_ratio: Decimal = Decimal("0.050000")
    block_latency_haircut_ratio: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExecutionCostPressureConfig, "config")
        _require_canonical_text("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_EXECUTION_COST_PRESSURE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_execution_cost_pressure",
            "block_execution_cost_pressure",
            "watch_taker_fee_ratio",
            "block_taker_fee_ratio",
            "watch_spread_ratio",
            "block_spread_ratio",
            "watch_depth_shortfall_ratio",
            "block_depth_shortfall_ratio",
            "watch_liquidity_concentration_ratio",
            "block_liquidity_concentration_ratio",
            "watch_latency_haircut_ratio",
            "block_latency_haircut_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_stale_book_age_seconds",
            "block_stale_book_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for lower_name, upper_name in (
            ("watch_execution_cost_pressure", "block_execution_cost_pressure"),
            ("watch_taker_fee_ratio", "block_taker_fee_ratio"),
            ("watch_spread_ratio", "block_spread_ratio"),
            ("watch_depth_shortfall_ratio", "block_depth_shortfall_ratio"),
            (
                "watch_liquidity_concentration_ratio",
                "block_liquidity_concentration_ratio",
            ),
            ("watch_stale_book_age_seconds", "block_stale_book_age_seconds"),
            ("watch_latency_haircut_ratio", "block_latency_haircut_ratio"),
        ):
            _require_increasing_threshold(
                lower_name,
                getattr(self, lower_name),
                upper_name,
                getattr(self, upper_name),
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketExecutionCostPressureObservation:
    public_bucket: str
    observed_at: datetime
    sample_count: Decimal
    taker_fee_ratio: Decimal
    spread_ratio: Decimal
    depth_shortfall_ratio: Decimal
    liquidity_concentration_ratio: Decimal
    stale_book_age_seconds: Decimal
    latency_haircut_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExecutionCostPressureObservation, "observation")
        object.__setattr__(
            self,
            "public_bucket",
            _require_public_label("public_bucket", self.public_bucket),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "taker_fee_ratio",
            "spread_ratio",
            "depth_shortfall_ratio",
            "liquidity_concentration_ratio",
            "latency_haircut_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_book_age_seconds",
            _require_nonnegative_decimal(
                "stale_book_age_seconds",
                self.stale_book_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketExecutionCostPressureRow:
    public_bucket: str
    observed_at: datetime
    age_seconds: Decimal
    sample_count: Decimal
    taker_fee_ratio: Decimal
    spread_ratio: Decimal
    depth_shortfall_ratio: Decimal
    liquidity_concentration_ratio: Decimal
    stale_book_age_seconds: Decimal
    latency_haircut_ratio: Decimal
    execution_cost_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExecutionCostPressureRow, "row")
        object.__setattr__(
            self,
            "public_bucket",
            _require_public_label("public_bucket", self.public_bucket),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "age_seconds",
            _require_nonnegative_decimal("age_seconds", self.age_seconds),
        )
        object.__setattr__(
            self,
            "sample_count",
            _require_positive_whole_decimal("sample_count", self.sample_count),
        )
        for field_name in (
            "taker_fee_ratio",
            "spread_ratio",
            "depth_shortfall_ratio",
            "liquidity_concentration_ratio",
            "latency_haircut_ratio",
            "execution_cost_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_book_age_seconds",
            _require_nonnegative_decimal(
                "stale_book_age_seconds",
                self.stale_book_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketExecutionCostPressureReasonCodeCount:
    reason_code: str
    count: Decimal
    sample_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketExecutionCostPressureReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "sample_ratio",
            _require_ratio_decimal("sample_ratio", self.sample_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketExecutionCostPressureReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    sample_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    taker_fee_watch_count: Decimal
    spread_watch_count: Decimal
    depth_shortfall_watch_count: Decimal
    liquidity_concentration_watch_count: Decimal
    stale_book_watch_count: Decimal
    latency_haircut_watch_count: Decimal
    max_execution_cost_pressure_score: Decimal | None
    average_execution_cost_pressure_score: Decimal | None
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketExecutionCostPressureReasonCodeCount, ...]
    rows: tuple[ResearchMarketExecutionCostPressureRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExecutionCostPressureReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_text("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "sample_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "taker_fee_watch_count",
            "spread_watch_count",
            "depth_shortfall_watch_count",
            "liquidity_concentration_watch_count",
            "stale_book_watch_count",
            "latency_haircut_watch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_execution_cost_pressure_score",
            "average_execution_cost_pressure_score",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _require_ratio_decimal(field_name, value),
                )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)


def build_research_market_execution_cost_pressure_report(
    observations: Iterable[ResearchMarketExecutionCostPressureObservation],
    *,
    config: ResearchMarketExecutionCostPressureConfig,
    generated_at: datetime,
) -> ResearchMarketExecutionCostPressureReport:
    if type(config) is not ResearchMarketExecutionCostPressureConfig:
        raise ValueError("config must be a ResearchMarketExecutionCostPressureConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized = _normalize_observations(observations, generated_at=generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    value,
                    config=config,
                    generated_at=generated_at,
                )
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketExecutionCostPressureReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        observation_count=_count_decimal(len(normalized)),
        sample_count=_sum_decimal(row.sample_count for row in rows),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        taker_fee_watch_count=_threshold_count(
            rows,
            "taker_fee_ratio",
            config.watch_taker_fee_ratio,
        ),
        spread_watch_count=_threshold_count(
            rows,
            "spread_ratio",
            config.watch_spread_ratio,
        ),
        depth_shortfall_watch_count=_threshold_count(
            rows,
            "depth_shortfall_ratio",
            config.watch_depth_shortfall_ratio,
        ),
        liquidity_concentration_watch_count=_threshold_count(
            rows,
            "liquidity_concentration_ratio",
            config.watch_liquidity_concentration_ratio,
        ),
        stale_book_watch_count=_threshold_count(
            rows,
            "stale_book_age_seconds",
            config.watch_stale_book_age_seconds,
        ),
        latency_haircut_watch_count=_threshold_count(
            rows,
            "latency_haircut_ratio",
            config.watch_latency_haircut_ratio,
        ),
        max_execution_cost_pressure_score=_max_decimal(
            row.execution_cost_pressure_score for row in rows
        ),
        average_execution_cost_pressure_score=_average_decimal(
            row.execution_cost_pressure_score for row in rows
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_market_execution_cost_pressure_report_payload(
    report: ResearchMarketExecutionCostPressureReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketExecutionCostPressureReport:
        raise ValueError("report must be a ResearchMarketExecutionCostPressureReport")
    _validate_report_consistency(report)
    value = _json_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    _reject_unsafe_payload(value)
    return value


def research_market_execution_cost_pressure_report_digest(
    report: ResearchMarketExecutionCostPressureReport,
) -> str:
    if type(report) is not ResearchMarketExecutionCostPressureReport:
        raise ValueError("report must be a ResearchMarketExecutionCostPressureReport")
    payload = research_market_execution_cost_pressure_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _row_from_observation(
    value: ResearchMarketExecutionCostPressureObservation,
    *,
    config: ResearchMarketExecutionCostPressureConfig,
    generated_at: datetime,
) -> ResearchMarketExecutionCostPressureRow:
    score = _execution_cost_pressure_score(value, config)
    status = _status_from_observation(value, config, score)
    return ResearchMarketExecutionCostPressureRow(
        public_bucket=value.public_bucket,
        observed_at=value.observed_at,
        age_seconds=_seconds_between(generated_at, value.observed_at),
        sample_count=value.sample_count,
        taker_fee_ratio=value.taker_fee_ratio,
        spread_ratio=value.spread_ratio,
        depth_shortfall_ratio=value.depth_shortfall_ratio,
        liquidity_concentration_ratio=value.liquidity_concentration_ratio,
        stale_book_age_seconds=value.stale_book_age_seconds,
        latency_haircut_ratio=value.latency_haircut_ratio,
        execution_cost_pressure_score=score,
        status=status,
        reason_codes=_row_reason_codes(
            value,
            config=config,
            score=score,
            status=status,
        ),
    )


def _status_from_observation(
    value: ResearchMarketExecutionCostPressureObservation,
    config: ResearchMarketExecutionCostPressureConfig,
    score: Decimal,
) -> str:
    if (
        score >= config.block_execution_cost_pressure
        or value.taker_fee_ratio >= config.block_taker_fee_ratio
        or value.spread_ratio >= config.block_spread_ratio
        or value.depth_shortfall_ratio >= config.block_depth_shortfall_ratio
        or value.liquidity_concentration_ratio
        >= config.block_liquidity_concentration_ratio
        or value.stale_book_age_seconds >= config.block_stale_book_age_seconds
        or value.latency_haircut_ratio >= config.block_latency_haircut_ratio
    ):
        return STATUS_BLOCK
    if (
        score >= config.watch_execution_cost_pressure
        or value.taker_fee_ratio >= config.watch_taker_fee_ratio
        or value.spread_ratio >= config.watch_spread_ratio
        or value.depth_shortfall_ratio >= config.watch_depth_shortfall_ratio
        or value.liquidity_concentration_ratio
        >= config.watch_liquidity_concentration_ratio
        or value.stale_book_age_seconds >= config.watch_stale_book_age_seconds
        or value.latency_haircut_ratio >= config.watch_latency_haircut_ratio
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    value: ResearchMarketExecutionCostPressureObservation,
    *,
    config: ResearchMarketExecutionCostPressureConfig,
    score: Decimal,
    status: str,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return (CLEAR_REASON,)
    suffix = "block" if status == STATUS_BLOCK else "watch"
    reason_codes = [f"input_{reason_code}" for reason_code in value.reason_codes]
    if value.depth_shortfall_ratio >= getattr(
        config,
        f"{suffix}_depth_shortfall_ratio",
    ):
        reason_codes.append(f"{REASON_PREFIX}depth_shortfall_{suffix}")
    if value.latency_haircut_ratio >= getattr(config, f"{suffix}_latency_haircut_ratio"):
        reason_codes.append(f"{REASON_PREFIX}latency_haircut_{suffix}")
    if value.liquidity_concentration_ratio >= getattr(
        config,
        f"{suffix}_liquidity_concentration_ratio",
    ):
        reason_codes.append(f"{REASON_PREFIX}liquidity_concentration_{suffix}")
    if value.spread_ratio >= getattr(config, f"{suffix}_spread_ratio"):
        reason_codes.append(f"{REASON_PREFIX}spread_{suffix}")
    if value.stale_book_age_seconds >= getattr(
        config,
        f"{suffix}_stale_book_age_seconds",
    ):
        reason_codes.append(f"{REASON_PREFIX}stale_book_{suffix}")
    if value.taker_fee_ratio >= getattr(config, f"{suffix}_taker_fee_ratio"):
        reason_codes.append(f"{REASON_PREFIX}taker_fee_{suffix}")
    if not any(reason_code.endswith(f"_{suffix}") for reason_code in reason_codes):
        reason_codes.append(
            PRESSURE_BLOCK_REASON if suffix == "block" else PRESSURE_WATCH_REASON,
        )
    return _normalize_reason_codes(tuple(sorted(set(reason_codes))), allow_empty=False)


def _execution_cost_pressure_score(
    value: ResearchMarketExecutionCostPressureObservation,
    config: ResearchMarketExecutionCostPressureConfig,
) -> Decimal:
    return _max_decimal(
        (
            _ratio_to_threshold(value.taker_fee_ratio, config.block_taker_fee_ratio),
            _ratio_to_threshold(value.spread_ratio, config.block_spread_ratio),
            _ratio_to_threshold(
                value.depth_shortfall_ratio,
                config.block_depth_shortfall_ratio,
            ),
            _ratio_to_threshold(
                value.liquidity_concentration_ratio,
                config.block_liquidity_concentration_ratio,
            ),
            _ratio_to_threshold(
                value.stale_book_age_seconds,
                config.block_stale_book_age_seconds,
            ),
            _ratio_to_threshold(
                value.latency_haircut_ratio,
                config.block_latency_haircut_ratio,
            ),
        ),
    ) or ZERO


def _ratio_to_threshold(value: Decimal, threshold: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(_quantize_decimal(value / threshold), ONE)


def _normalize_observations(
    observations: Iterable[ResearchMarketExecutionCostPressureObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchMarketExecutionCostPressureObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not ResearchMarketExecutionCostPressureObservation:
            raise ValueError(
                "observations must contain ResearchMarketExecutionCostPressureObservation",
            )
        _require_hard_flags(value)
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketExecutionCostPressureRow],
) -> tuple[ResearchMarketExecutionCostPressureRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketExecutionCostPressureRow:
            raise ValueError("rows must contain ResearchMarketExecutionCostPressureRow")
        _require_public_label("public_bucket", row.public_bucket)
        _require_hard_flags(row)
        _validate_row_consistency(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketExecutionCostPressureReasonCodeCount],
) -> tuple[ResearchMarketExecutionCostPressureReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for item in normalized:
        if type(item) is not ResearchMarketExecutionCostPressureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketExecutionCostPressureReasonCodeCount",
            )
        _require_hard_flags(item)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _report_status(rows: tuple[ResearchMarketExecutionCostPressureRow, ...]) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketExecutionCostPressureRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketExecutionCostPressureRow, ...],
) -> tuple[ResearchMarketExecutionCostPressureReasonCodeCount, ...]:
    denominator = _count_decimal(len(rows))
    if not rows:
        return (
            ResearchMarketExecutionCostPressureReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=_count_decimal(1),
                sample_ratio=ZERO,
            ),
        )
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        sorted(
            (
                ResearchMarketExecutionCostPressureReasonCodeCount(
                    reason_code=reason_code,
                    count=_count_decimal(counter[reason_code]),
                    sample_ratio=_safe_divide(
                        _count_decimal(counter[reason_code]),
                        denominator,
                    ),
                )
                for reason_code in reason_codes
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _validate_row_consistency(row: ResearchMarketExecutionCostPressureRow) -> None:
    if row.status == STATUS_PASS:
        if row.reason_codes != (CLEAR_REASON,):
            raise ValueError("status must match reason_codes")
        return
    if row.status == STATUS_BLOCK:
        if not any(reason_code.endswith("_block") for reason_code in row.reason_codes):
            raise ValueError("status must match reason_codes")
        return
    if not any(reason_code.endswith("_watch") for reason_code in row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: ResearchMarketExecutionCostPressureReport) -> None:
    _require_hard_flags(report)
    rows = _normalize_rows(report.rows)
    reason_code_counts = _normalize_reason_code_counts(report.reason_code_counts)
    if report.rows != rows:
        raise ValueError("rows must be sorted deterministically")
    if report.observation_count != _count_decimal(len(rows)):
        raise ValueError("observation_count must match rows")
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.sample_count != _sum_decimal(row.sample_count for row in rows):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(report.reason_codes, rows)
    if reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_code_counts != reason_code_counts:
        raise ValueError("reason_code_counts must be sorted deterministically")
    if report.max_execution_cost_pressure_score != _max_decimal(
        row.execution_cost_pressure_score for row in rows
    ):
        raise ValueError("max_execution_cost_pressure_score must match rows")
    if report.average_execution_cost_pressure_score != _average_decimal(
        row.execution_cost_pressure_score for row in rows
    ):
        raise ValueError("average_execution_cost_pressure_score must match rows")


def _row_sort_key(row: ResearchMarketExecutionCostPressureRow) -> tuple[Decimal, str]:
    priority = {
        STATUS_BLOCK: Decimal("0"),
        STATUS_WATCH: Decimal("1"),
        STATUS_PASS: Decimal("2"),
    }[row.status]
    return (priority, row.public_bucket)


def _status_count(
    rows: Iterable[ResearchMarketExecutionCostPressureRow],
    status: str,
) -> Decimal:
    return _count_decimal(sum(Decimal("1") for row in rows if row.status == status))


def _threshold_count(
    rows: Iterable[ResearchMarketExecutionCostPressureRow],
    field_name: str,
    threshold: Decimal,
) -> Decimal:
    return _count_decimal(
        sum(Decimal("1") for row in rows if getattr(row, field_name) >= threshold),
    )


def _count_decimal(value: object) -> Decimal:
    return _quantize_decimal(Decimal(str(value)))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize_decimal(total + value)
    return total


def _max_decimal(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return max(normalized)


def _average_decimal(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return _safe_divide(_sum_decimal(normalized), _count_decimal(len(normalized)))


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _seconds_between(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _safe_divide(microseconds, MICROSECONDS_PER_SECOND)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_public_label(field_name: str, value: str) -> str:
    _require_canonical_text(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_LABEL_DENY_FRAGMENTS):
        raise ValueError(f"{field_name} must not include unsafe identifiers")
    if not all(character.islower() or character.isdigit() or character == "-" for character in value):
        raise ValueError(f"{field_name} must be a canonical public label")
    return value


def _require_canonical_text(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(sorted(set(reason_codes)))
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_codes", reason_code)
    return normalized


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    _reject_unsafe_text(value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value <= ZERO or value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a positive whole Decimal")
    return value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANT)
        except InvalidOperation as exc:
            raise ValueError("Decimal value is outside supported precision") from exc


def _require_increasing_threshold(
    lower_name: str,
    lower: Decimal,
    upper_name: str,
    upper: Decimal,
) -> None:
    if lower >= upper:
        raise ValueError(f"{lower_name} must be less than {upper_name}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


def _json_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return str(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_text(str(key))
            _reject_unsafe_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
    elif isinstance(value, str):
        _reject_unsafe_text(value)


def _reject_unsafe_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in PAYLOAD_DENY_FRAGMENTS):
        raise ValueError("payload contains unsafe identifier text")
