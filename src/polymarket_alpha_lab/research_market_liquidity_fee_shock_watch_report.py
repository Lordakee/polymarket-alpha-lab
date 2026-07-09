"""Pure public liquidity-fee shock watch report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_SHOCK_WATCH_CONFIG_VERSION = (
    "research-market-liquidity-fee-shock-watch-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "research_market_liquidity_fee_shock_watch_"
NO_OBSERVATIONS_REASON = f"{REASON_PREFIX}no_observations"
CLEAR_REASON = f"{REASON_PREFIX}clear"
LIQUIDITY_SHOCK_BLOCK_REASON = f"{REASON_PREFIX}liquidity_shock_block"
LIQUIDITY_SHOCK_WATCH_REASON = f"{REASON_PREFIX}liquidity_shock_watch"
FEE_SHOCK_BLOCK_REASON = f"{REASON_PREFIX}fee_shock_block"
FEE_SHOCK_WATCH_REASON = f"{REASON_PREFIX}fee_shock_watch"
SPREAD_BLOCK_REASON = f"{REASON_PREFIX}spread_block"
SPREAD_WATCH_REASON = f"{REASON_PREFIX}spread_watch"
QUOTE_STALENESS_BLOCK_REASON = f"{REASON_PREFIX}quote_staleness_block"
QUOTE_STALENESS_WATCH_REASON = f"{REASON_PREFIX}quote_staleness_watch"
CATALYST_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}catalyst_pressure_block"
CATALYST_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}catalyst_pressure_watch"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "raw",
    "://",
    "?",
    _join_parts("au", "th"),
    _join_parts("li", "ve"),
    _join_parts("trad", "ing"),
    _join_parts("siz", "ing"),
    _join_parts("recommen", "dation"),
    _join_parts("execu", "tion"),
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_SHOCK_WATCH_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketLiquidityFeeShockWatchConfig",
    "ResearchMarketLiquidityFeeShockWatchObservation",
    "ResearchMarketLiquidityFeeShockWatchReasonCodeCount",
    "ResearchMarketLiquidityFeeShockWatchReport",
    "ResearchMarketLiquidityFeeShockWatchRow",
    "build_research_market_liquidity_fee_shock_watch_report",
    "research_market_liquidity_fee_shock_watch_report_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchMarketLiquidityFeeShockWatchConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_SHOCK_WATCH_CONFIG_VERSION
    watch_liquidity_shock_ratio: Decimal = Decimal("0.200000")
    block_liquidity_shock_ratio: Decimal = Decimal("0.500000")
    watch_fee_shock_ratio: Decimal = Decimal("0.030000")
    block_fee_shock_ratio: Decimal = Decimal("0.100000")
    watch_spread_ratio: Decimal = Decimal("0.050000")
    block_spread_ratio: Decimal = Decimal("0.120000")
    watch_quote_staleness_seconds: Decimal = Decimal("300.000000")
    block_quote_staleness_seconds: Decimal = Decimal("900.000000")
    watch_catalyst_pressure: Decimal = Decimal("0.600000")
    block_catalyst_pressure: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquidityFeeShockWatchConfig:
            raise TypeError(
                "config must be exactly ResearchMarketLiquidityFeeShockWatchConfig",
            )
        _require_canonical_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_SHOCK_WATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_liquidity_shock_ratio",
            "block_liquidity_shock_ratio",
            "watch_fee_shock_ratio",
            "block_fee_shock_ratio",
            "watch_spread_ratio",
            "block_spread_ratio",
            "watch_catalyst_pressure",
            "block_catalyst_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_quote_staleness_seconds",
            "block_quote_staleness_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_increasing_threshold(
            "watch_liquidity_shock_ratio",
            self.watch_liquidity_shock_ratio,
            "block_liquidity_shock_ratio",
            self.block_liquidity_shock_ratio,
        )
        _require_increasing_threshold(
            "watch_fee_shock_ratio",
            self.watch_fee_shock_ratio,
            "block_fee_shock_ratio",
            self.block_fee_shock_ratio,
        )
        _require_increasing_threshold(
            "watch_spread_ratio",
            self.watch_spread_ratio,
            "block_spread_ratio",
            self.block_spread_ratio,
        )
        _require_increasing_threshold(
            "watch_quote_staleness_seconds",
            self.watch_quote_staleness_seconds,
            "block_quote_staleness_seconds",
            self.block_quote_staleness_seconds,
        )
        _require_increasing_threshold(
            "watch_catalyst_pressure",
            self.watch_catalyst_pressure,
            "block_catalyst_pressure",
            self.block_catalyst_pressure,
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketLiquidityFeeShockWatchObservation(_FinalPublicDataclass):
    public_bucket: str
    observed_at: datetime
    sample_count: Decimal
    liquidity_shock_ratio: Decimal
    fee_shock_ratio: Decimal
    bid_ask_spread_ratio: Decimal
    quote_staleness_seconds: Decimal
    catalyst_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquidityFeeShockWatchObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketLiquidityFeeShockWatchObservation",
            )
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
            "liquidity_shock_ratio",
            "fee_shock_ratio",
            "bid_ask_spread_ratio",
            "catalyst_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_staleness_seconds",
            _require_nonnegative_decimal(
                "quote_staleness_seconds",
                self.quote_staleness_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketLiquidityFeeShockWatchRow(_FinalPublicDataclass):
    public_bucket: str
    observed_at: datetime
    age_seconds: Decimal
    sample_count: Decimal
    liquidity_shock_ratio: Decimal
    fee_shock_ratio: Decimal
    bid_ask_spread_ratio: Decimal
    quote_staleness_seconds: Decimal
    catalyst_pressure: Decimal
    shock_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquidityFeeShockWatchRow:
            raise ValueError("row must be exactly ResearchMarketLiquidityFeeShockWatchRow")
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
            "liquidity_shock_ratio",
            "fee_shock_ratio",
            "bid_ask_spread_ratio",
            "catalyst_pressure",
            "shock_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "quote_staleness_seconds",
            _require_nonnegative_decimal(
                "quote_staleness_seconds",
                self.quote_staleness_seconds,
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
class ResearchMarketLiquidityFeeShockWatchReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    sample_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquidityFeeShockWatchReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchMarketLiquidityFeeShockWatchReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "sample_ratio",
            _require_ratio_decimal("sample_ratio", self.sample_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchMarketLiquidityFeeShockWatchReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    sample_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    liquidity_shock_watch_count: Decimal
    fee_shock_watch_count: Decimal
    spread_watch_count: Decimal
    quote_stale_count: Decimal
    catalyst_pressure_count: Decimal
    max_shock_score: Decimal | None
    average_shock_score: Decimal | None
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketLiquidityFeeShockWatchReasonCodeCount, ...]
    rows: tuple[ResearchMarketLiquidityFeeShockWatchRow, ...]
    derived_validation_digest: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketLiquidityFeeShockWatchReport:
            raise ValueError(
                "report must be exactly ResearchMarketLiquidityFeeShockWatchReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_FEE_SHOCK_WATCH_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "sample_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "liquidity_shock_watch_count",
            "fee_shock_watch_count",
            "spread_watch_count",
            "quote_stale_count",
            "catalyst_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("max_shock_score", "average_shock_score"):
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
        _validate_report_counts(self)
        _require_hard_flags(self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest is None:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report contents")
        _reject_unsafe_payload(_report_payload_without_digest(self))


def build_research_market_liquidity_fee_shock_watch_report(
    observations: Iterable[ResearchMarketLiquidityFeeShockWatchObservation],
    *,
    config: ResearchMarketLiquidityFeeShockWatchConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityFeeShockWatchReport:
    if type(config) is not ResearchMarketLiquidityFeeShockWatchConfig:
        raise ValueError("config must be a ResearchMarketLiquidityFeeShockWatchConfig")
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
    return ResearchMarketLiquidityFeeShockWatchReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        observation_count=_count_decimal(len(normalized)),
        sample_count=_sum_decimal(row.sample_count for row in rows),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        liquidity_shock_watch_count=_threshold_count(
            rows,
            "liquidity_shock_ratio",
            config.watch_liquidity_shock_ratio,
        ),
        fee_shock_watch_count=_threshold_count(
            rows,
            "fee_shock_ratio",
            config.watch_fee_shock_ratio,
        ),
        spread_watch_count=_threshold_count(
            rows,
            "bid_ask_spread_ratio",
            config.watch_spread_ratio,
        ),
        quote_stale_count=_threshold_count(
            rows,
            "quote_staleness_seconds",
            config.watch_quote_staleness_seconds,
        ),
        catalyst_pressure_count=_threshold_count(
            rows,
            "catalyst_pressure",
            config.watch_catalyst_pressure,
        ),
        max_shock_score=_max_decimal(row.shock_score for row in rows),
        average_shock_score=_average_decimal(row.shock_score for row in rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_market_liquidity_fee_shock_watch_report_payload(
    report: ResearchMarketLiquidityFeeShockWatchReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketLiquidityFeeShockWatchReport:
        raise ValueError("report must be a ResearchMarketLiquidityFeeShockWatchReport")
    _validate_report_counts(report)
    _validate_report_digest(report)
    value = _json_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    _reject_unsafe_payload(value)
    _require_hard_flags(_DictFlags(value))
    return value


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_observation(
    value: ResearchMarketLiquidityFeeShockWatchObservation,
    *,
    config: ResearchMarketLiquidityFeeShockWatchConfig,
    generated_at: datetime,
) -> ResearchMarketLiquidityFeeShockWatchRow:
    status = _status_from_observation(value, config)
    return ResearchMarketLiquidityFeeShockWatchRow(
        public_bucket=value.public_bucket,
        observed_at=value.observed_at,
        age_seconds=_seconds_between(generated_at, value.observed_at),
        sample_count=value.sample_count,
        liquidity_shock_ratio=value.liquidity_shock_ratio,
        fee_shock_ratio=value.fee_shock_ratio,
        bid_ask_spread_ratio=value.bid_ask_spread_ratio,
        quote_staleness_seconds=value.quote_staleness_seconds,
        catalyst_pressure=value.catalyst_pressure,
        shock_score=_shock_score(value, config),
        status=status,
        reason_codes=_row_reason_codes(value, config=config, status=status),
    )


def _status_from_observation(
    value: ResearchMarketLiquidityFeeShockWatchObservation,
    config: ResearchMarketLiquidityFeeShockWatchConfig,
) -> str:
    if (
        value.liquidity_shock_ratio >= config.block_liquidity_shock_ratio
        or value.fee_shock_ratio >= config.block_fee_shock_ratio
        or value.bid_ask_spread_ratio >= config.block_spread_ratio
        or value.quote_staleness_seconds >= config.block_quote_staleness_seconds
        or value.catalyst_pressure >= config.block_catalyst_pressure
    ):
        return STATUS_BLOCK
    if (
        value.liquidity_shock_ratio >= config.watch_liquidity_shock_ratio
        or value.fee_shock_ratio >= config.watch_fee_shock_ratio
        or value.bid_ask_spread_ratio >= config.watch_spread_ratio
        or value.quote_staleness_seconds >= config.watch_quote_staleness_seconds
        or value.catalyst_pressure >= config.watch_catalyst_pressure
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    value: ResearchMarketLiquidityFeeShockWatchObservation,
    *,
    config: ResearchMarketLiquidityFeeShockWatchConfig,
    status: str,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return (CLEAR_REASON,)
    suffix = "block" if status == STATUS_BLOCK else "watch"
    reason_codes = [f"input_{reason_code}" for reason_code in value.reason_codes]
    if value.catalyst_pressure >= getattr(config, f"{suffix}_catalyst_pressure"):
        reason_codes.append(f"{REASON_PREFIX}catalyst_pressure_{suffix}")
    if value.fee_shock_ratio >= getattr(config, f"{suffix}_fee_shock_ratio"):
        reason_codes.append(f"{REASON_PREFIX}fee_shock_{suffix}")
    if value.liquidity_shock_ratio >= getattr(
        config,
        f"{suffix}_liquidity_shock_ratio",
    ):
        reason_codes.append(f"{REASON_PREFIX}liquidity_shock_{suffix}")
    if value.quote_staleness_seconds >= getattr(
        config,
        f"{suffix}_quote_staleness_seconds",
    ):
        reason_codes.append(f"{REASON_PREFIX}quote_staleness_{suffix}")
    if value.bid_ask_spread_ratio >= getattr(config, f"{suffix}_spread_ratio"):
        reason_codes.append(f"{REASON_PREFIX}spread_{suffix}")
    return _normalize_reason_codes(tuple(sorted(set(reason_codes))), allow_empty=False)


def _shock_score(
    value: ResearchMarketLiquidityFeeShockWatchObservation,
    config: ResearchMarketLiquidityFeeShockWatchConfig,
) -> Decimal:
    return _max_decimal(
        (
            _ratio_to_threshold(
                value.liquidity_shock_ratio,
                config.block_liquidity_shock_ratio,
            ),
            _ratio_to_threshold(value.fee_shock_ratio, config.block_fee_shock_ratio),
            _ratio_to_threshold(value.bid_ask_spread_ratio, config.block_spread_ratio),
            _ratio_to_threshold(
                value.quote_staleness_seconds,
                config.block_quote_staleness_seconds,
            ),
            _ratio_to_threshold(value.catalyst_pressure, config.block_catalyst_pressure),
        ),
    ) or ZERO


def _ratio_to_threshold(value: Decimal, threshold: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(_quantize_decimal(value / threshold), ONE)


def _normalize_observations(
    observations: Iterable[ResearchMarketLiquidityFeeShockWatchObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchMarketLiquidityFeeShockWatchObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not ResearchMarketLiquidityFeeShockWatchObservation:
            raise ValueError(
                "observations must contain ResearchMarketLiquidityFeeShockWatchObservation",
            )
        _require_hard_flags(value)
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketLiquidityFeeShockWatchRow],
) -> tuple[ResearchMarketLiquidityFeeShockWatchRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketLiquidityFeeShockWatchRow:
            raise ValueError("rows must contain ResearchMarketLiquidityFeeShockWatchRow")
        _require_public_label("public_bucket", row.public_bucket)
        _require_hard_flags(row)
        _validate_row_consistency(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketLiquidityFeeShockWatchReasonCodeCount],
) -> tuple[ResearchMarketLiquidityFeeShockWatchReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for item in normalized:
        if type(item) is not ResearchMarketLiquidityFeeShockWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketLiquidityFeeShockWatchReasonCodeCount",
            )
        _require_hard_flags(item)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _report_status(rows: tuple[ResearchMarketLiquidityFeeShockWatchRow, ...]) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityFeeShockWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketLiquidityFeeShockWatchRow, ...],
) -> tuple[ResearchMarketLiquidityFeeShockWatchReasonCodeCount, ...]:
    denominator = _count_decimal(len(rows))
    if not rows:
        return (
            ResearchMarketLiquidityFeeShockWatchReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=_count_decimal(1),
                sample_ratio=ZERO,
            ),
        )
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        sorted(
            (
                ResearchMarketLiquidityFeeShockWatchReasonCodeCount(
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


def _validate_row_consistency(row: ResearchMarketLiquidityFeeShockWatchRow) -> None:
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


def _validate_report_counts(report: ResearchMarketLiquidityFeeShockWatchReport) -> None:
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
    if report.max_shock_score != _max_decimal(row.shock_score for row in rows):
        raise ValueError("max_shock_score must match rows")
    if report.average_shock_score != _average_decimal(row.shock_score for row in rows):
        raise ValueError("average_shock_score must match rows")


def _validate_report_digest(report: ResearchMarketLiquidityFeeShockWatchReport) -> None:
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report contents")


def _report_validation_digest(report: ResearchMarketLiquidityFeeShockWatchReport) -> str:
    payload = _report_payload_without_digest(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_payload_without_digest(
    report: ResearchMarketLiquidityFeeShockWatchReport,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for field in fields(report):
        if field.name == "derived_validation_digest":
            continue
        payload[field.name] = _json_value(getattr(report, field.name))
    return payload


def _row_sort_key(row: ResearchMarketLiquidityFeeShockWatchRow) -> tuple[object, ...]:
    priority = {
        STATUS_BLOCK: Decimal("0"),
        STATUS_WATCH: Decimal("1"),
        STATUS_PASS: Decimal("2"),
    }[row.status]
    return (
        priority,
        row.public_bucket,
        row.observed_at.isoformat(),
        row.age_seconds,
        row.sample_count,
        row.liquidity_shock_ratio,
        row.fee_shock_ratio,
        row.bid_ask_spread_ratio,
        row.quote_staleness_seconds,
        row.catalyst_pressure,
        row.shock_score,
        row.reason_codes,
    )


def _status_count(
    rows: Iterable[ResearchMarketLiquidityFeeShockWatchRow],
    status: str,
) -> Decimal:
    total = ZERO
    for row in rows:
        if row.status == status:
            total = _quantize_decimal(total + ONE)
    return total


def _threshold_count(
    rows: Iterable[ResearchMarketLiquidityFeeShockWatchRow],
    field_name: str,
    threshold: Decimal,
) -> Decimal:
    total = ZERO
    for row in rows:
        if getattr(row, field_name) >= threshold:
            total = _quantize_decimal(total + ONE)
    return total


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


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_public_label(field_name: str, value: str) -> str:
    _require_canonical_text(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
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
    if any(fragment in value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain unsafe identifiers")
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")


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


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return value


def _require_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_whole_decimal(field_name, value)
    if value == ZERO:
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


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


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
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("payload contains unsafe identifier text")
