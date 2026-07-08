"""Pure public fee friction watch report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_FEE_FRICTION_WATCH_CONFIG_VERSION = (
    "research-market-fee-friction-watch-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REASON_PREFIX = "research_market_fee_friction_watch_"
NO_OBSERVATIONS_REASON = f"{REASON_PREFIX}no_observations"
CLEAR_REASON = f"{REASON_PREFIX}clear"
AGGREGATE_FEE_FRICTION_BLOCK_REASON = f"{REASON_PREFIX}aggregate_fee_friction_block"
AGGREGATE_FEE_FRICTION_WATCH_REASON = f"{REASON_PREFIX}aggregate_fee_friction_watch"
CATALYST_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}catalyst_pressure_block"
CATALYST_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}catalyst_pressure_watch"
DEPTH_FADE_BLOCK_REASON = f"{REASON_PREFIX}depth_fade_block"
DEPTH_FADE_WATCH_REASON = f"{REASON_PREFIX}depth_fade_watch"
FEE_FRICTION_BLOCK_REASON = f"{REASON_PREFIX}fee_friction_block"
FEE_FRICTION_WATCH_REASON = f"{REASON_PREFIX}fee_friction_watch"
QUOTE_STALENESS_BLOCK_REASON = f"{REASON_PREFIX}quote_staleness_block"
QUOTE_STALENESS_WATCH_REASON = f"{REASON_PREFIX}quote_staleness_watch"
SPREAD_BLOCK_REASON = f"{REASON_PREFIX}spread_block"
SPREAD_WATCH_REASON = f"{REASON_PREFIX}spread_watch"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

PUBLIC_LABEL_DENY_FRAGMENTS = (
    "market_id",
    "market_slug",
    "source_id",
    "source_url",
    "raw",
    "://",
    "?",
)

PAYLOAD_DENY_FRAGMENTS = (
    "market_id",
    "market_slug",
    "source_id",
    "source_url",
    "raw_market",
    "raw_source",
    "://",
    "?",
)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_FEE_FRICTION_WATCH_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketFeeFrictionWatchConfig",
    "ResearchMarketFeeFrictionWatchObservation",
    "ResearchMarketFeeFrictionWatchReasonCodeCount",
    "ResearchMarketFeeFrictionWatchReport",
    "ResearchMarketFeeFrictionWatchRow",
    "build_research_market_fee_friction_watch_report",
    "research_market_fee_friction_watch_report_digest",
    "research_market_fee_friction_watch_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketFeeFrictionWatchConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_FEE_FRICTION_WATCH_CONFIG_VERSION
    watch_fee_friction_ratio: Decimal = Decimal("0.015000")
    block_fee_friction_ratio: Decimal = Decimal("0.040000")
    watch_spread_ratio: Decimal = Decimal("0.050000")
    block_spread_ratio: Decimal = Decimal("0.120000")
    watch_depth_fade_ratio: Decimal = Decimal("0.250000")
    block_depth_fade_ratio: Decimal = Decimal("0.600000")
    watch_quote_staleness_seconds: Decimal = Decimal("300.000000")
    block_quote_staleness_seconds: Decimal = Decimal("900.000000")
    watch_catalyst_pressure: Decimal = Decimal("0.600000")
    block_catalyst_pressure: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeFrictionWatchConfig:
            raise TypeError("config must be exactly ResearchMarketFeeFrictionWatchConfig")
        _require_canonical_text("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_FEE_FRICTION_WATCH_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_fee_friction_ratio",
            "block_fee_friction_ratio",
            "watch_spread_ratio",
            "block_spread_ratio",
            "watch_depth_fade_ratio",
            "block_depth_fade_ratio",
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
            "watch_fee_friction_ratio",
            self.watch_fee_friction_ratio,
            "block_fee_friction_ratio",
            self.block_fee_friction_ratio,
        )
        _require_increasing_threshold(
            "watch_spread_ratio",
            self.watch_spread_ratio,
            "block_spread_ratio",
            self.block_spread_ratio,
        )
        _require_increasing_threshold(
            "watch_depth_fade_ratio",
            self.watch_depth_fade_ratio,
            "block_depth_fade_ratio",
            self.block_depth_fade_ratio,
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
class ResearchMarketFeeFrictionWatchObservation:
    public_bucket: str
    observed_at: datetime
    sample_count: Decimal
    aggregate_fee_friction_ratio: Decimal
    bid_ask_spread_ratio: Decimal
    depth_fade_ratio: Decimal
    quote_staleness_seconds: Decimal
    catalyst_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
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
            "aggregate_fee_friction_ratio",
            "bid_ask_spread_ratio",
            "depth_fade_ratio",
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
class ResearchMarketFeeFrictionWatchRow:
    public_bucket: str
    observed_at: datetime
    age_seconds: Decimal
    sample_count: Decimal
    aggregate_fee_friction_ratio: Decimal
    bid_ask_spread_ratio: Decimal
    depth_fade_ratio: Decimal
    quote_staleness_seconds: Decimal
    catalyst_pressure: Decimal
    fee_friction_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
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
            "aggregate_fee_friction_ratio",
            "bid_ask_spread_ratio",
            "depth_fade_ratio",
            "catalyst_pressure",
            "fee_friction_score",
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
class ResearchMarketFeeFrictionWatchReasonCodeCount:
    reason_code: str
    count: Decimal
    sample_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
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
class ResearchMarketFeeFrictionWatchReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    sample_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    fee_friction_watch_count: Decimal
    spread_watch_count: Decimal
    depth_fade_watch_count: Decimal
    quote_stale_count: Decimal
    catalyst_pressure_count: Decimal
    max_fee_friction_score: Decimal | None
    average_fee_friction_score: Decimal | None
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketFeeFrictionWatchReasonCodeCount, ...]
    rows: tuple[ResearchMarketFeeFrictionWatchRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
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
            "fee_friction_watch_count",
            "spread_watch_count",
            "depth_fade_watch_count",
            "quote_stale_count",
            "catalyst_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_fee_friction_score", "average_fee_friction_score"):
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


def build_research_market_fee_friction_watch_report(
    observations: Iterable[ResearchMarketFeeFrictionWatchObservation],
    *,
    config: ResearchMarketFeeFrictionWatchConfig,
    generated_at: datetime,
) -> ResearchMarketFeeFrictionWatchReport:
    if type(config) is not ResearchMarketFeeFrictionWatchConfig:
        raise ValueError("config must be a ResearchMarketFeeFrictionWatchConfig")
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
    return ResearchMarketFeeFrictionWatchReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        observation_count=_count_decimal(len(normalized)),
        sample_count=_sum_decimal(row.sample_count for row in rows),
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        fee_friction_watch_count=_threshold_count(
            rows,
            "aggregate_fee_friction_ratio",
            config.watch_fee_friction_ratio,
        ),
        spread_watch_count=_threshold_count(
            rows,
            "bid_ask_spread_ratio",
            config.watch_spread_ratio,
        ),
        depth_fade_watch_count=_threshold_count(
            rows,
            "depth_fade_ratio",
            config.watch_depth_fade_ratio,
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
        max_fee_friction_score=_max_decimal(row.fee_friction_score for row in rows),
        average_fee_friction_score=_average_decimal(
            (row.fee_friction_score for row in rows),
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_market_fee_friction_watch_report_payload(
    report: ResearchMarketFeeFrictionWatchReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFeeFrictionWatchReport:
        raise ValueError("report must be a ResearchMarketFeeFrictionWatchReport")
    _validate_report_consistency(report)
    value = _json_value(report)
    if type(value) is not dict:
        raise ValueError("report must serialize to a JSON object")
    _reject_unsafe_payload(value)
    return value


def research_market_fee_friction_watch_report_digest(
    report: ResearchMarketFeeFrictionWatchReport,
) -> str:
    if type(report) is not ResearchMarketFeeFrictionWatchReport:
        raise ValueError("report must be a ResearchMarketFeeFrictionWatchReport")
    payload = research_market_fee_friction_watch_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _row_from_observation(
    value: ResearchMarketFeeFrictionWatchObservation,
    *,
    config: ResearchMarketFeeFrictionWatchConfig,
    generated_at: datetime,
) -> ResearchMarketFeeFrictionWatchRow:
    status = _status_from_observation(value, config)
    return ResearchMarketFeeFrictionWatchRow(
        public_bucket=value.public_bucket,
        observed_at=value.observed_at,
        age_seconds=_seconds_between(generated_at, value.observed_at),
        sample_count=value.sample_count,
        aggregate_fee_friction_ratio=value.aggregate_fee_friction_ratio,
        bid_ask_spread_ratio=value.bid_ask_spread_ratio,
        depth_fade_ratio=value.depth_fade_ratio,
        quote_staleness_seconds=value.quote_staleness_seconds,
        catalyst_pressure=value.catalyst_pressure,
        fee_friction_score=_fee_friction_score(value, config),
        status=status,
        reason_codes=_row_reason_codes(value, config=config, status=status),
    )


def _status_from_observation(
    value: ResearchMarketFeeFrictionWatchObservation,
    config: ResearchMarketFeeFrictionWatchConfig,
) -> str:
    if (
        value.aggregate_fee_friction_ratio >= config.block_fee_friction_ratio
        or value.bid_ask_spread_ratio >= config.block_spread_ratio
        or value.depth_fade_ratio >= config.block_depth_fade_ratio
        or value.quote_staleness_seconds >= config.block_quote_staleness_seconds
        or value.catalyst_pressure >= config.block_catalyst_pressure
    ):
        return STATUS_BLOCK
    if (
        value.aggregate_fee_friction_ratio >= config.watch_fee_friction_ratio
        or value.bid_ask_spread_ratio >= config.watch_spread_ratio
        or value.depth_fade_ratio >= config.watch_depth_fade_ratio
        or value.quote_staleness_seconds >= config.watch_quote_staleness_seconds
        or value.catalyst_pressure >= config.watch_catalyst_pressure
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    value: ResearchMarketFeeFrictionWatchObservation,
    *,
    config: ResearchMarketFeeFrictionWatchConfig,
    status: str,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return (CLEAR_REASON,)
    suffix = "block" if status == STATUS_BLOCK else "watch"
    reason_codes = [f"input_{reason_code}" for reason_code in value.reason_codes]
    if value.aggregate_fee_friction_ratio >= getattr(
        config,
        f"{suffix}_fee_friction_ratio",
    ):
        reason_codes.append(f"{REASON_PREFIX}aggregate_fee_friction_{suffix}")
        reason_codes.append(f"{REASON_PREFIX}fee_friction_{suffix}")
    if value.catalyst_pressure >= getattr(config, f"{suffix}_catalyst_pressure"):
        reason_codes.append(f"{REASON_PREFIX}catalyst_pressure_{suffix}")
    if value.depth_fade_ratio >= getattr(config, f"{suffix}_depth_fade_ratio"):
        reason_codes.append(f"{REASON_PREFIX}depth_fade_{suffix}")
    if value.quote_staleness_seconds >= getattr(
        config,
        f"{suffix}_quote_staleness_seconds",
    ):
        reason_codes.append(f"{REASON_PREFIX}quote_staleness_{suffix}")
    if value.bid_ask_spread_ratio >= getattr(config, f"{suffix}_spread_ratio"):
        reason_codes.append(f"{REASON_PREFIX}spread_{suffix}")
    return _normalize_reason_codes(tuple(sorted(set(reason_codes))), allow_empty=False)


def _fee_friction_score(
    value: ResearchMarketFeeFrictionWatchObservation,
    config: ResearchMarketFeeFrictionWatchConfig,
) -> Decimal:
    return _max_decimal(
        (
            _ratio_to_threshold(
                value.aggregate_fee_friction_ratio,
                config.block_fee_friction_ratio,
            ),
            _ratio_to_threshold(value.bid_ask_spread_ratio, config.block_spread_ratio),
            _ratio_to_threshold(value.depth_fade_ratio, config.block_depth_fade_ratio),
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
    observations: Iterable[ResearchMarketFeeFrictionWatchObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchMarketFeeFrictionWatchObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not ResearchMarketFeeFrictionWatchObservation:
            raise ValueError(
                "observations must contain ResearchMarketFeeFrictionWatchObservation",
            )
        _require_hard_flags(value)
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketFeeFrictionWatchRow],
) -> tuple[ResearchMarketFeeFrictionWatchRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchMarketFeeFrictionWatchRow:
            raise ValueError("rows must contain ResearchMarketFeeFrictionWatchRow")
        _require_public_label("public_bucket", row.public_bucket)
        _require_hard_flags(row)
        _validate_row_consistency(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Iterable[ResearchMarketFeeFrictionWatchReasonCodeCount],
) -> tuple[ResearchMarketFeeFrictionWatchReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    for item in normalized:
        if type(item) is not ResearchMarketFeeFrictionWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchMarketFeeFrictionWatchReasonCodeCount",
            )
        _require_hard_flags(item)
    return tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))


def _report_status(rows: tuple[ResearchMarketFeeFrictionWatchRow, ...]) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeFrictionWatchRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_OBSERVATIONS_REASON,)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketFeeFrictionWatchRow, ...],
) -> tuple[ResearchMarketFeeFrictionWatchReasonCodeCount, ...]:
    denominator = _count_decimal(len(rows))
    if not rows:
        return (
            ResearchMarketFeeFrictionWatchReasonCodeCount(
                reason_code=NO_OBSERVATIONS_REASON,
                count=_count_decimal(1),
                sample_ratio=ZERO,
            ),
        )
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        sorted(
            (
                ResearchMarketFeeFrictionWatchReasonCodeCount(
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


def _validate_row_consistency(row: ResearchMarketFeeFrictionWatchRow) -> None:
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


def _validate_report_consistency(report: ResearchMarketFeeFrictionWatchReport) -> None:
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
    if report.max_fee_friction_score != _max_decimal(row.fee_friction_score for row in rows):
        raise ValueError("max_fee_friction_score must match rows")
    if report.average_fee_friction_score != _average_decimal(
        (row.fee_friction_score for row in rows),
    ):
        raise ValueError("average_fee_friction_score must match rows")


def _row_sort_key(row: ResearchMarketFeeFrictionWatchRow) -> tuple[Decimal, str]:
    priority = {
        STATUS_BLOCK: Decimal("0"),
        STATUS_WATCH: Decimal("1"),
        STATUS_PASS: Decimal("2"),
    }[row.status]
    return (priority, row.public_bucket)


def _status_count(rows: Iterable[ResearchMarketFeeFrictionWatchRow], status: str) -> Decimal:
    return _count_decimal(sum(Decimal("1") for row in rows if row.status == status))


def _threshold_count(
    rows: Iterable[ResearchMarketFeeFrictionWatchRow],
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
