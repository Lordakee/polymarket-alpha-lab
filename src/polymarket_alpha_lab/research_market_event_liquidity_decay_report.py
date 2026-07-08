"""Pure event-domain liquidity decay report for caller-supplied research inputs.

The module is deterministic and side-effect free. Callers provide aggregate
event-domain liquidity observations; the builder returns report-only decay
scores, statuses, and public reason codes for research filtering.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_EVENT_LIQUIDITY_DECAY_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketEventLiquidityDecayConfig",
    "ResearchMarketEventLiquidityDecayInput",
    "ResearchMarketEventLiquidityDecayReasonCodeCount",
    "ResearchMarketEventLiquidityDecayReport",
    "ResearchMarketEventLiquidityDecayRow",
    "build_research_market_event_liquidity_decay_report",
    "research_market_event_liquidity_decay_report_payload",
)


DEFAULT_RESEARCH_MARKET_EVENT_LIQUIDITY_DECAY_CONFIG_VERSION = (
    "research-market-event-liquidity-decay-report-v0"
)
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_MAX_WATCH_LIQUIDITY_DECAY_SCORE = Decimal("0.350000")
DEFAULT_MAX_BLOCK_LIQUIDITY_DECAY_SCORE = Decimal("0.700000")

_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_market",
    "raw_source",
    "market_id",
    "source_id",
    "condition_id",
    "token_id",
    "source_url",
    "wallet",
    "auth",
    "order",
    "trade",
    "execution",
    "network_url",
    "database",
    "db_",
    "persist",
    "mutation",
    "signing",
    "private" "_key",
    "secret",
    "live trading",
    "live_mode",
    "buy",
    "sell",
    "position",
    "recommendation",
    "sizing",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketEventLiquidityDecayConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_EVENT_LIQUIDITY_DECAY_CONFIG_VERSION
    max_watch_liquidity_decay_score: Decimal = DEFAULT_MAX_WATCH_LIQUIDITY_DECAY_SCORE
    max_block_liquidity_decay_score: Decimal = DEFAULT_MAX_BLOCK_LIQUIDITY_DECAY_SCORE
    max_watch_depth_decay_ratio: Decimal = Decimal("0.250000")
    max_block_depth_decay_ratio: Decimal = Decimal("0.600000")
    max_watch_spread_widening_ratio: Decimal = Decimal("0.500000")
    max_block_spread_widening_ratio: Decimal = Decimal("1.500000")
    max_watch_quote_age_seconds: Decimal = Decimal("300.000000")
    max_block_quote_age_seconds: Decimal = Decimal("1800.000000")
    max_watch_volume_fade_ratio: Decimal = Decimal("0.300000")
    max_block_volume_fade_ratio: Decimal = Decimal("0.700000")
    max_watch_fee_rate_bps: Decimal = Decimal("50.000000")
    max_block_fee_rate_bps: Decimal = Decimal("100.000000")
    depth_weight: Decimal = Decimal("0.250000")
    spread_weight: Decimal = Decimal("0.200000")
    quote_staleness_weight: Decimal = Decimal("0.200000")
    volume_weight: Decimal = Decimal("0.200000")
    fee_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "max_watch_liquidity_decay_score",
            "max_block_liquidity_decay_score",
            "max_watch_depth_decay_ratio",
            "max_block_depth_decay_ratio",
            "max_watch_volume_fade_ratio",
            "max_block_volume_fade_ratio",
            "depth_weight",
            "spread_weight",
            "quote_staleness_weight",
            "volume_weight",
            "fee_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_watch_spread_widening_ratio",
            "max_block_spread_widening_ratio",
            "max_watch_quote_age_seconds",
            "max_block_quote_age_seconds",
            "max_watch_fee_rate_bps",
            "max_block_fee_rate_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_block_liquidity_decay_score <= self.max_watch_liquidity_decay_score:
            raise ValueError(
                "max_block_liquidity_decay_score must exceed "
                "max_watch_liquidity_decay_score",
            )
        if self.max_block_depth_decay_ratio <= self.max_watch_depth_decay_ratio:
            raise ValueError(
                "max_block_depth_decay_ratio must exceed max_watch_depth_decay_ratio",
            )
        if self.max_block_spread_widening_ratio <= self.max_watch_spread_widening_ratio:
            raise ValueError(
                "max_block_spread_widening_ratio must exceed "
                "max_watch_spread_widening_ratio",
            )
        if self.max_block_quote_age_seconds <= self.max_watch_quote_age_seconds:
            raise ValueError(
                "max_block_quote_age_seconds must exceed max_watch_quote_age_seconds",
            )
        if self.max_block_volume_fade_ratio <= self.max_watch_volume_fade_ratio:
            raise ValueError(
                "max_block_volume_fade_ratio must exceed max_watch_volume_fade_ratio",
            )
        if self.max_block_fee_rate_bps <= self.max_watch_fee_rate_bps:
            raise ValueError(
                "max_block_fee_rate_bps must exceed max_watch_fee_rate_bps",
            )
        weight_sum = _quantize(
            self.depth_weight
            + self.spread_weight
            + self.quote_staleness_weight
            + self.volume_weight
            + self.fee_weight,
        )
        if weight_sum != ONE:
            raise ValueError("component weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchMarketEventLiquidityDecayInput:
    event_domain: str
    domain_label: str
    baseline_depth_usd: Decimal
    current_depth_usd: Decimal
    baseline_spread_bps: Decimal
    current_spread_bps: Decimal
    quote_age_seconds: Decimal
    baseline_volume_usd: Decimal
    current_volume_usd: Decimal
    fee_rate_bps: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("event_domain", "domain_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "baseline_depth_usd",
            "baseline_spread_bps",
            "baseline_volume_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "current_depth_usd",
            "current_spread_bps",
            "quote_age_seconds",
            "current_volume_usd",
            "fee_rate_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("domain_input", self)
        _reject_unsafe_public_payload("domain_input", _payload_value(self))


@dataclass(frozen=True)
class ResearchMarketEventLiquidityDecayRow:
    event_domain: str
    domain_label: str
    baseline_depth_usd: Decimal
    current_depth_usd: Decimal
    depth_decay_ratio: Decimal
    baseline_spread_bps: Decimal
    current_spread_bps: Decimal
    spread_widening_ratio: Decimal
    quote_age_seconds: Decimal
    quote_staleness_score: Decimal
    baseline_volume_usd: Decimal
    current_volume_usd: Decimal
    volume_fade_ratio: Decimal
    fee_rate_bps: Decimal
    fee_friction_score: Decimal
    observed_at: datetime
    liquidity_decay_score: Decimal
    decay_status: str
    reason_codes: tuple[str, ...]
    config: InitVar[ResearchMarketEventLiquidityDecayConfig | None] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(
        self,
        config: ResearchMarketEventLiquidityDecayConfig | None,
    ) -> None:
        for field_name in ("event_domain", "domain_label"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "baseline_depth_usd",
            "baseline_spread_bps",
            "baseline_volume_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "current_depth_usd",
            "current_spread_bps",
            "quote_age_seconds",
            "current_volume_usd",
            "fee_rate_bps",
            "spread_widening_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_decay_ratio",
            "quote_staleness_score",
            "volume_fade_ratio",
            "fee_friction_score",
            "liquidity_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("decay_status", self.decay_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self, config=config)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchMarketEventLiquidityDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    event_domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_domain_ratio",
            _require_probability_decimal("event_domain_ratio", self.event_domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", _payload_value(self))


@dataclass(frozen=True)
class ResearchMarketEventLiquidityDecayReport:
    generated_at: datetime
    config_version: str
    event_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_liquidity_decay_score: Decimal | None
    max_depth_decay_ratio: Decimal
    max_spread_widening_ratio: Decimal
    max_quote_age_seconds: Decimal
    max_volume_fade_ratio: Decimal
    max_fee_rate_bps: Decimal
    status: str
    rows: tuple[ResearchMarketEventLiquidityDecayRow, ...]
    reason_code_counts: tuple[ResearchMarketEventLiquidityDecayReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "event_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_liquidity_decay_score",
            _require_optional_probability_decimal(
                "average_liquidity_decay_score",
                self.average_liquidity_decay_score,
            ),
        )
        for field_name in ("max_depth_decay_ratio", "max_volume_fade_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_spread_widening_ratio",
            "max_quote_age_seconds",
            "max_fee_rate_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_status_consistency(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", _report_payload(self, include_digest=True))


def build_research_market_event_liquidity_decay_report(
    domain_inputs: Iterable[object],
    *,
    config: ResearchMarketEventLiquidityDecayConfig,
    generated_at: datetime,
) -> ResearchMarketEventLiquidityDecayReport:
    if type(config) is not ResearchMarketEventLiquidityDecayConfig:
        raise ValueError("config must be a ResearchMarketEventLiquidityDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_domain_inputs(domain_inputs)
    for item in input_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be in the future")
    domains = tuple(item.event_domain for item in input_items)
    if len(set(domains)) != len(domains):
        raise ValueError("event_domain values must be unique")

    rows = tuple(
        _build_row(item, config=config)
        for item in sorted(input_items, key=lambda value: value.event_domain)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketEventLiquidityDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_domain_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_liquidity_decay_score=_average_decay_score(rows),
        max_depth_decay_ratio=_max_decimal(
            tuple(row.depth_decay_ratio for row in rows),
            default=ZERO,
        ),
        max_spread_widening_ratio=_max_decimal(
            tuple(row.spread_widening_ratio for row in rows),
            default=ZERO,
        ),
        max_quote_age_seconds=_max_decimal(
            tuple(row.quote_age_seconds for row in rows),
            default=ZERO,
        ),
        max_volume_fade_ratio=_max_decimal(
            tuple(row.volume_fade_ratio for row in rows),
            default=ZERO,
        ),
        max_fee_rate_bps=_max_decimal(tuple(row.fee_rate_bps for row in rows), default=ZERO),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_event_liquidity_decay_report_payload(
    report: ResearchMarketEventLiquidityDecayReport | dict[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchMarketEventLiquidityDecayReport:
        _require_hard_flags("report", report)
        payload = _report_payload(report, include_digest=True)
        _reject_unsafe_public_payload("report", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("report", report)
        _reject_numeric_payload_values(report)
        _require_payload_hard_flags(report)
        _validate_payload_digest(report)
        return dict(report)
    raise ValueError("report must be a ResearchMarketEventLiquidityDecayReport")


def _build_row(
    item: ResearchMarketEventLiquidityDecayInput,
    *,
    config: ResearchMarketEventLiquidityDecayConfig,
) -> ResearchMarketEventLiquidityDecayRow:
    depth_decay_ratio = _bounded_ratio(
        item.baseline_depth_usd - item.current_depth_usd,
        item.baseline_depth_usd,
    )
    spread_widening_ratio = _nonnegative_ratio(
        item.current_spread_bps - item.baseline_spread_bps,
        item.baseline_spread_bps,
    )
    quote_staleness_score = _capped_ratio(
        item.quote_age_seconds,
        config.max_block_quote_age_seconds,
    )
    volume_fade_ratio = _bounded_ratio(
        item.baseline_volume_usd - item.current_volume_usd,
        item.baseline_volume_usd,
    )
    fee_friction_score = _capped_ratio(
        item.fee_rate_bps,
        config.max_block_fee_rate_bps,
    )
    liquidity_decay_score = _liquidity_decay_score(
        depth_decay_ratio=depth_decay_ratio,
        spread_widening_ratio=spread_widening_ratio,
        quote_staleness_score=quote_staleness_score,
        volume_fade_ratio=volume_fade_ratio,
        fee_friction_score=fee_friction_score,
        config=config,
    )
    decay_status = _row_status(
        depth_decay_ratio=depth_decay_ratio,
        spread_widening_ratio=spread_widening_ratio,
        quote_age_seconds=item.quote_age_seconds,
        volume_fade_ratio=volume_fade_ratio,
        fee_rate_bps=item.fee_rate_bps,
        liquidity_decay_score=liquidity_decay_score,
        config=config,
    )
    return ResearchMarketEventLiquidityDecayRow(
        event_domain=item.event_domain,
        domain_label=item.domain_label,
        baseline_depth_usd=item.baseline_depth_usd,
        current_depth_usd=item.current_depth_usd,
        depth_decay_ratio=depth_decay_ratio,
        baseline_spread_bps=item.baseline_spread_bps,
        current_spread_bps=item.current_spread_bps,
        spread_widening_ratio=spread_widening_ratio,
        quote_age_seconds=item.quote_age_seconds,
        quote_staleness_score=quote_staleness_score,
        baseline_volume_usd=item.baseline_volume_usd,
        current_volume_usd=item.current_volume_usd,
        volume_fade_ratio=volume_fade_ratio,
        fee_rate_bps=item.fee_rate_bps,
        fee_friction_score=fee_friction_score,
        observed_at=item.observed_at,
        liquidity_decay_score=liquidity_decay_score,
        decay_status=decay_status,
        reason_codes=_row_reason_codes(
            depth_decay_ratio=depth_decay_ratio,
            spread_widening_ratio=spread_widening_ratio,
            quote_age_seconds=item.quote_age_seconds,
            volume_fade_ratio=volume_fade_ratio,
            fee_rate_bps=item.fee_rate_bps,
            liquidity_decay_score=liquidity_decay_score,
            decay_status=decay_status,
            input_reason_codes=item.reason_codes,
            config=config,
        ),
        config=config,
    )


def _normalize_domain_inputs(
    domain_inputs: Iterable[object],
) -> tuple[ResearchMarketEventLiquidityDecayInput, ...]:
    if isinstance(domain_inputs, (str, bytes)):
        raise ValueError("domain_inputs must be an iterable")
    try:
        values = tuple(domain_inputs)
    except TypeError as exc:
        raise ValueError("domain_inputs must be an iterable") from exc
    return tuple(_coerce_domain_input(value) for value in values)


def _coerce_domain_input(value: object) -> ResearchMarketEventLiquidityDecayInput:
    if type(value) is ResearchMarketEventLiquidityDecayInput:
        _require_hard_flags("domain_input", value)
        return value
    _require_hard_flags("domain_input", value)
    return ResearchMarketEventLiquidityDecayInput(
        event_domain=_field_value(value, "event_domain"),
        domain_label=_field_value(value, "domain_label"),
        baseline_depth_usd=_field_value(value, "baseline_depth_usd"),
        current_depth_usd=_field_value(value, "current_depth_usd"),
        baseline_spread_bps=_field_value(value, "baseline_spread_bps"),
        current_spread_bps=_field_value(value, "current_spread_bps"),
        quote_age_seconds=_field_value(value, "quote_age_seconds"),
        baseline_volume_usd=_field_value(value, "baseline_volume_usd"),
        current_volume_usd=_field_value(value, "current_volume_usd"),
        fee_rate_bps=_field_value(value, "fee_rate_bps"),
        observed_at=_field_value(value, "observed_at"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if numerator <= ZERO:
        return ZERO
    return _quantize(min(ONE, numerator / denominator))


def _nonnegative_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if numerator <= ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if numerator <= ZERO:
        return ZERO
    return _quantize(min(ONE, numerator / denominator))


def _liquidity_decay_score(
    *,
    depth_decay_ratio: Decimal,
    spread_widening_ratio: Decimal,
    quote_staleness_score: Decimal,
    volume_fade_ratio: Decimal,
    fee_friction_score: Decimal,
    config: ResearchMarketEventLiquidityDecayConfig,
) -> Decimal:
    raw_score = (
        (depth_decay_ratio * config.depth_weight)
        + (min(ONE, spread_widening_ratio) * config.spread_weight)
        + (quote_staleness_score * config.quote_staleness_weight)
        + (volume_fade_ratio * config.volume_weight)
        + (fee_friction_score * config.fee_weight)
    )
    return _quantize(max(ZERO, min(ONE, raw_score)))


def _row_status(
    *,
    depth_decay_ratio: Decimal,
    spread_widening_ratio: Decimal,
    quote_age_seconds: Decimal,
    volume_fade_ratio: Decimal,
    fee_rate_bps: Decimal,
    liquidity_decay_score: Decimal,
    config: ResearchMarketEventLiquidityDecayConfig,
) -> str:
    if (
        liquidity_decay_score >= config.max_block_liquidity_decay_score
        or depth_decay_ratio >= config.max_block_depth_decay_ratio
        or spread_widening_ratio >= config.max_block_spread_widening_ratio
        or quote_age_seconds >= config.max_block_quote_age_seconds
        or volume_fade_ratio >= config.max_block_volume_fade_ratio
        or fee_rate_bps >= config.max_block_fee_rate_bps
    ):
        return "block"
    if (
        liquidity_decay_score >= config.max_watch_liquidity_decay_score
        or depth_decay_ratio > config.max_watch_depth_decay_ratio
        or spread_widening_ratio > config.max_watch_spread_widening_ratio
        or quote_age_seconds > config.max_watch_quote_age_seconds
        or volume_fade_ratio > config.max_watch_volume_fade_ratio
        or fee_rate_bps > config.max_watch_fee_rate_bps
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    depth_decay_ratio: Decimal,
    spread_widening_ratio: Decimal,
    quote_age_seconds: Decimal,
    volume_fade_ratio: Decimal,
    fee_rate_bps: Decimal,
    liquidity_decay_score: Decimal,
    decay_status: str,
    input_reason_codes: tuple[str, ...],
    config: ResearchMarketEventLiquidityDecayConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    if depth_decay_ratio >= config.max_block_depth_decay_ratio:
        reason_codes.add("depth_decay_block")
    elif depth_decay_ratio > config.max_watch_depth_decay_ratio:
        reason_codes.add("depth_decay_watch")
    if spread_widening_ratio >= config.max_block_spread_widening_ratio:
        reason_codes.add("spread_widening_block")
    elif spread_widening_ratio > config.max_watch_spread_widening_ratio:
        reason_codes.add("spread_widening_watch")
    if quote_age_seconds >= config.max_block_quote_age_seconds:
        reason_codes.add("quote_staleness_block")
    elif quote_age_seconds > config.max_watch_quote_age_seconds:
        reason_codes.add("quote_staleness_watch")
    if volume_fade_ratio >= config.max_block_volume_fade_ratio:
        reason_codes.add("volume_fade_block")
    elif volume_fade_ratio > config.max_watch_volume_fade_ratio:
        reason_codes.add("volume_fade_watch")
    if fee_rate_bps >= config.max_block_fee_rate_bps:
        reason_codes.add("fee_friction_block")
    elif fee_rate_bps > config.max_watch_fee_rate_bps:
        reason_codes.add("fee_friction_watch")
    if liquidity_decay_score >= config.max_block_liquidity_decay_score:
        reason_codes.add("liquidity_decay_score_block")
    elif liquidity_decay_score >= config.max_watch_liquidity_decay_score:
        reason_codes.add("liquidity_decay_score_watch")
    if decay_status == "pass":
        reason_codes.add("liquidity_decay_clear")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchMarketEventLiquidityDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("liquidity_decay_no_event_domains",)
    if all(row.decay_status == "pass" for row in rows):
        return ("liquidity_decay_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchMarketEventLiquidityDecayRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.decay_status == "block" for row in rows):
        return "block"
    if any(row.decay_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketEventLiquidityDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketEventLiquidityDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketEventLiquidityDecayReasonCodeCount(
                reason_code=reason_codes[0],
                count=_decimal_count(1),
                event_domain_ratio=ZERO,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    total = _decimal_count(len(rows))
    return tuple(
        ResearchMarketEventLiquidityDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            event_domain_ratio=_quantize(_decimal_count(count) / total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_decay_score(
    rows: tuple[ResearchMarketEventLiquidityDecayRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(
        sum((row.liquidity_decay_score for row in rows), ZERO) / _decimal_count(len(rows)),
    )


def _status_count(
    rows: tuple[ResearchMarketEventLiquidityDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.decay_status == status)


def _max_decimal(values: tuple[Decimal, ...], *, default: Decimal) -> Decimal:
    if not values:
        return default
    return max(values)


def _normalize_rows(
    rows: tuple[ResearchMarketEventLiquidityDecayRow, ...],
) -> tuple[ResearchMarketEventLiquidityDecayRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketEventLiquidityDecayRow:
            raise ValueError("rows must contain ResearchMarketEventLiquidityDecayRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.event_domain))
    if rows != sorted_rows:
        raise ValueError("rows must use deterministic event_domain order")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketEventLiquidityDecayReasonCodeCount, ...],
) -> tuple[ResearchMarketEventLiquidityDecayReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketEventLiquidityDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketEventLiquidityDecayReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must use deterministic reason_code order")
    return counts


def _validate_row_consistency(
    row: ResearchMarketEventLiquidityDecayRow,
    *,
    config: ResearchMarketEventLiquidityDecayConfig | None,
) -> None:
    cfg = config or ResearchMarketEventLiquidityDecayConfig()
    expected_depth = _bounded_ratio(row.baseline_depth_usd - row.current_depth_usd, row.baseline_depth_usd)
    expected_spread = _nonnegative_ratio(
        row.current_spread_bps - row.baseline_spread_bps,
        row.baseline_spread_bps,
    )
    expected_quote = _capped_ratio(row.quote_age_seconds, cfg.max_block_quote_age_seconds)
    expected_volume = _bounded_ratio(
        row.baseline_volume_usd - row.current_volume_usd,
        row.baseline_volume_usd,
    )
    expected_fee = _capped_ratio(row.fee_rate_bps, cfg.max_block_fee_rate_bps)
    if row.depth_decay_ratio != expected_depth:
        raise ValueError("depth_decay_ratio must match depth values")
    if row.spread_widening_ratio != expected_spread:
        raise ValueError("spread_widening_ratio must match spread values")
    if row.quote_staleness_score != expected_quote:
        raise ValueError("quote_staleness_score must match quote_age_seconds")
    if row.volume_fade_ratio != expected_volume:
        raise ValueError("volume_fade_ratio must match volume values")
    if row.fee_friction_score != expected_fee:
        raise ValueError("fee_friction_score must match fee_rate_bps")
    expected_score = _liquidity_decay_score(
        depth_decay_ratio=row.depth_decay_ratio,
        spread_widening_ratio=row.spread_widening_ratio,
        quote_staleness_score=row.quote_staleness_score,
        volume_fade_ratio=row.volume_fade_ratio,
        fee_friction_score=row.fee_friction_score,
        config=cfg,
    )
    if row.liquidity_decay_score != expected_score:
        raise ValueError("liquidity_decay_score must match component values")
    expected_status = _row_status(
        depth_decay_ratio=row.depth_decay_ratio,
        spread_widening_ratio=row.spread_widening_ratio,
        quote_age_seconds=row.quote_age_seconds,
        volume_fade_ratio=row.volume_fade_ratio,
        fee_rate_bps=row.fee_rate_bps,
        liquidity_decay_score=row.liquidity_decay_score,
        config=cfg,
    )
    if row.decay_status != expected_status:
        raise ValueError("decay_status must match component values")


def _validate_report_status_consistency(
    report: ResearchMarketEventLiquidityDecayReport,
) -> None:
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_report_consistency(report: ResearchMarketEventLiquidityDecayReport) -> None:
    if report.event_domain_count != _decimal_count(len(report.rows)):
        raise ValueError("event_domain_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_liquidity_decay_score != _average_decay_score(report.rows):
        raise ValueError("average_liquidity_decay_score must match rows")
    if report.max_depth_decay_ratio != _max_decimal(
        tuple(row.depth_decay_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_depth_decay_ratio must match rows")
    if report.max_spread_widening_ratio != _max_decimal(
        tuple(row.spread_widening_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_spread_widening_ratio must match rows")
    if report.max_quote_age_seconds != _max_decimal(
        tuple(row.quote_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_quote_age_seconds must match rows")
    if report.max_volume_fade_ratio != _max_decimal(
        tuple(row.volume_fade_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_volume_fade_ratio must match rows")
    if report.max_fee_rate_bps != _max_decimal(
        tuple(row.fee_rate_bps for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_fee_rate_bps must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _report_payload(
    report: ResearchMarketEventLiquidityDecayReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    if not include_digest:
        payload.pop("derived_validation_digest", None)
    return payload


def _derived_validation_digest(report: ResearchMarketEventLiquidityDecayReport) -> str:
    return _payload_validation_digest(_report_payload(report, include_digest=False))


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest is required")
    _require_digest("derived_validation_digest", digest)
    if digest != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _payload_validation_digest(payload: dict[str, object]) -> str:
    public_payload = dict(payload)
    public_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        public_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(+value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if _contains_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _require_payload_hard_flags(value: object) -> None:
    if isinstance(value, dict):
        if all(flag in value for flag in ("paper_only", "report_only", "readonly")):
            for flag in ("paper_only", "report_only", "readonly"):
                if value[flag] is not True:
                    raise ValueError(f"{flag} must be True")
        for item in value.values():
            _require_payload_hard_flags(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _require_payload_hard_flags(item)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _reject_numeric_payload_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload must not contain raw numeric values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_payload_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_numeric_payload_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_unsafe_public_fragment(str(key)):
                raise ValueError(f"{label} contains unsafe public content")
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, str) and _contains_unsafe_public_fragment(value):
        raise ValueError(f"{label} contains unsafe public content")


def _contains_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)
