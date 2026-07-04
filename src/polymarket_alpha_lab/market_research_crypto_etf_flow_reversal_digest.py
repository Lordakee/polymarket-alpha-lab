"""Pure Phase 1 report-only crypto ETF flow reversal digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_REVERSAL_DIGEST_CONFIG_VERSION",
    "MarketResearchCryptoEtfFlowReversalDigestConfig",
    "MarketResearchCryptoEtfFlowReversalObservation",
    "MarketResearchCryptoEtfFlowReversalRow",
    "MarketResearchCryptoEtfFlowReversalReasonCodeCount",
    "MarketResearchCryptoEtfFlowReversalReport",
    "build_market_research_crypto_etf_flow_reversal_digest",
    "market_research_crypto_etf_flow_reversal_digest_payload",
)


DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_REVERSAL_DIGEST_CONFIG_VERSION = (
    "market-research-crypto-etf-flow-reversal-digest-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

OUTFLOW_REVERSAL = "outflow_reversal"
INFLOW_REVERSAL = "inflow_reversal"
NO_REVERSAL = "no_reversal"
REVERSAL_DIRECTIONS = (OUTFLOW_REVERSAL, INFLOW_REVERSAL, NO_REVERSAL)

BLOCKED_STATUS = "blocked"
WATCH_STATUS = "watch"
PASS_STATUS = "pass"
REVERSAL_STATUSES = (BLOCKED_STATUS, WATCH_STATUS, PASS_STATUS)
STATUS_RANK = {
    BLOCKED_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

RECOMMENDED_NEXT_STEPS = {
    BLOCKED_STATUS: "block_report_only_market_research_crypto_etf_flow_reversal_digest",
    WATCH_STATUS: "monitor_report_only_market_research_crypto_etf_flow_reversal_digest",
    PASS_STATUS: "allow_report_only_market_research_crypto_etf_flow_reversal_digest",
}

EMPTY_REASON = "crypto_etf_flow_reversal_digest_empty"
ABSENT_REVERSAL_REASON = "crypto_etf_flow_reversal_absent"
INFLOW_REVERSAL_REASON = "crypto_etf_flow_reversal_inflow"
OUTFLOW_REVERSAL_REASON = "crypto_etf_flow_reversal_outflow"
MATERIAL_REVERSAL_REASON = "crypto_etf_flow_reversal_material"
LARGE_REVERSAL_REASON = "crypto_etf_flow_reversal_large"
SOURCE_FRESH_REASON = "source_fresh"
SOURCE_STALE_REASON = "source_stale"
THIN_SOURCE_REASON = "thin_sources"
MISSING_CONFIRMATION_REASON = "missing_confirmation"
LOW_CONFIDENCE_REASON = "low_flow_confidence"


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowReversalDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_REVERSAL_DIGEST_CONFIG_VERSION
    )
    watch_reversal_abs_usd: Decimal = Decimal("50000000.000000")
    blocked_reversal_abs_usd: Decimal = Decimal("250000000.000000")
    max_source_age_seconds: Decimal = Decimal("7200.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_confirmation_count: Decimal = Decimal("1.000000")
    min_flow_confidence: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchCryptoEtfFlowReversalDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_REVERSAL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_reversal_abs_usd",
            "blocked_reversal_abs_usd",
            "max_source_age_seconds",
            "min_source_count",
            "min_confirmation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_flow_confidence",
            _normalize_probability("min_flow_confidence", self.min_flow_confidence),
        )
        if self.watch_reversal_abs_usd > self.blocked_reversal_abs_usd:
            raise ValueError(
                "watch_reversal_abs_usd must not exceed blocked_reversal_abs_usd",
            )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowReversalObservation:
    source_id: str
    research_key: str
    market_slug: str
    asset_symbol: str
    etf_ticker: str
    current_net_flow_usd: Decimal
    previous_net_flow_usd: Decimal
    source_count: Decimal
    confirmation_count: Decimal
    flow_confidence: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoEtfFlowReversalObservation,
            "observation",
        )
        for field_name in (
            "source_id",
            "research_key",
            "market_slug",
            "asset_symbol",
            "etf_ticker",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("current_net_flow_usd", "previous_net_flow_usd"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "confirmation_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "flow_confidence",
            _normalize_probability("flow_confidence", self.flow_confidence),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowReversalRow:
    source_id: str
    research_key: str
    market_slug: str
    asset_symbol: str
    etf_ticker: str
    observed_at: datetime
    source_age_seconds: Decimal
    current_net_flow_usd: Decimal
    previous_net_flow_usd: Decimal
    flow_change_usd: Decimal
    flow_change_abs_usd: Decimal
    reversal_magnitude_usd: Decimal
    source_count: Decimal
    confirmation_count: Decimal
    flow_confidence: Decimal
    reversal_direction: str
    reversal_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchCryptoEtfFlowReversalRow, "row")
        for field_name in (
            "source_id",
            "research_key",
            "market_slug",
            "asset_symbol",
            "etf_ticker",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "current_net_flow_usd",
            "previous_net_flow_usd",
            "flow_change_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_age_seconds",
            "flow_change_abs_usd",
            "reversal_magnitude_usd",
            "source_count",
            "confirmation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "flow_confidence",
            _normalize_probability("flow_confidence", self.flow_confidence),
        )
        _require_member("reversal_direction", self.reversal_direction, REVERSAL_DIRECTIONS)
        _require_member("reversal_status", self.reversal_status, REVERSAL_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowReversalReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketResearchCryptoEtfFlowReversalReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketResearchCryptoEtfFlowReversalReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_reversal_count: Decimal
    watch_reversal_count: Decimal
    routine_count: Decimal
    outflow_reversal_count: Decimal
    inflow_reversal_count: Decimal
    no_reversal_count: Decimal
    stale_source_count: Decimal
    thin_source_count: Decimal
    low_confirmation_count: Decimal
    low_confidence_count: Decimal
    max_reversal_magnitude_usd: Decimal
    net_current_flow_usd: Decimal
    net_previous_flow_usd: Decimal
    aggregate_flow_change_usd: Decimal
    average_flow_confidence: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MarketResearchCryptoEtfFlowReversalRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketResearchCryptoEtfFlowReversalReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketResearchCryptoEtfFlowReversalReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_REVERSAL_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_reversal_count",
            "watch_reversal_count",
            "routine_count",
            "outflow_reversal_count",
            "inflow_reversal_count",
            "no_reversal_count",
            "stale_source_count",
            "thin_source_count",
            "low_confirmation_count",
            "low_confidence_count",
            "max_reversal_magnitude_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "net_current_flow_usd",
            "net_previous_flow_usd",
            "aggregate_flow_change_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_flow_confidence",
            _normalize_probability("average_flow_confidence", self.average_flow_confidence),
        )
        _require_member("digest_status", self.digest_status, REVERSAL_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags(self)


def build_market_research_crypto_etf_flow_reversal_digest(
    inputs: Iterable[MarketResearchCryptoEtfFlowReversalObservation],
    *,
    config: MarketResearchCryptoEtfFlowReversalDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoEtfFlowReversalReport:
    if type(config) is not MarketResearchCryptoEtfFlowReversalDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchCryptoEtfFlowReversalDigestConfig",
        )
    _require_hard_flags(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_observation(value, config=config, generated_at=generated_at)
                for value in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)
    return MarketResearchCryptoEtfFlowReversalReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_reversal_count=_status_count(rows, BLOCKED_STATUS),
        watch_reversal_count=_status_count(rows, WATCH_STATUS),
        routine_count=_status_count(rows, PASS_STATUS),
        outflow_reversal_count=_direction_count(rows, OUTFLOW_REVERSAL),
        inflow_reversal_count=_direction_count(rows, INFLOW_REVERSAL),
        no_reversal_count=_direction_count(rows, NO_REVERSAL),
        stale_source_count=_reason_count(rows, SOURCE_STALE_REASON),
        thin_source_count=_reason_count(rows, THIN_SOURCE_REASON),
        low_confirmation_count=_reason_count(rows, MISSING_CONFIRMATION_REASON),
        low_confidence_count=_reason_count(rows, LOW_CONFIDENCE_REASON),
        max_reversal_magnitude_usd=_max_row_decimal(rows, "reversal_magnitude_usd"),
        net_current_flow_usd=_sum_decimal(row.current_net_flow_usd for row in rows),
        net_previous_flow_usd=_sum_decimal(row.previous_net_flow_usd for row in rows),
        aggregate_flow_change_usd=_sum_decimal(row.flow_change_usd for row in rows),
        average_flow_confidence=_ratio(
            _sum_decimal(row.flow_confidence for row in rows),
            row_count,
        ),
        digest_status=digest_status,
        recommended_next_step=RECOMMENDED_NEXT_STEPS[digest_status],
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def market_research_crypto_etf_flow_reversal_digest_payload(
    report: MarketResearchCryptoEtfFlowReversalReport,
) -> dict[str, Any]:
    if type(report) is not MarketResearchCryptoEtfFlowReversalReport:
        raise ValueError(
            "report must be exactly MarketResearchCryptoEtfFlowReversalReport",
        )
    _require_hard_flags(report)
    return _payload_value(report)


def _row_from_observation(
    value: MarketResearchCryptoEtfFlowReversalObservation,
    *,
    config: MarketResearchCryptoEtfFlowReversalDigestConfig,
    generated_at: datetime,
) -> MarketResearchCryptoEtfFlowReversalRow:
    source_age_seconds = _seconds_between(generated_at, value.observed_at)
    source_fresh = source_age_seconds <= config.max_source_age_seconds
    flow_change_usd = _quantize_decimal(
        value.current_net_flow_usd - value.previous_net_flow_usd,
    )
    flow_change_abs_usd = _quantize_decimal(abs(flow_change_usd))
    direction = _reversal_direction(
        previous_net_flow_usd=value.previous_net_flow_usd,
        current_net_flow_usd=value.current_net_flow_usd,
    )
    reversal_magnitude_usd = flow_change_abs_usd if direction != NO_REVERSAL else ZERO
    reason_codes = _row_reason_codes(
        value.upstream_reason_codes,
        value=value,
        config=config,
        direction=direction,
        reversal_magnitude_usd=reversal_magnitude_usd,
        source_fresh=source_fresh,
    )
    return MarketResearchCryptoEtfFlowReversalRow(
        source_id=value.source_id,
        research_key=value.research_key,
        market_slug=value.market_slug,
        asset_symbol=value.asset_symbol,
        etf_ticker=value.etf_ticker,
        observed_at=value.observed_at,
        source_age_seconds=source_age_seconds,
        current_net_flow_usd=value.current_net_flow_usd,
        previous_net_flow_usd=value.previous_net_flow_usd,
        flow_change_usd=flow_change_usd,
        flow_change_abs_usd=flow_change_abs_usd,
        reversal_magnitude_usd=reversal_magnitude_usd,
        source_count=value.source_count,
        confirmation_count=value.confirmation_count,
        flow_confidence=value.flow_confidence,
        reversal_direction=direction,
        reversal_status=_row_status(
            direction=direction,
            reversal_magnitude_usd=reversal_magnitude_usd,
            reason_codes=reason_codes,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    value: MarketResearchCryptoEtfFlowReversalObservation,
    config: MarketResearchCryptoEtfFlowReversalDigestConfig,
    direction: str,
    reversal_magnitude_usd: Decimal,
    source_fresh: bool,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if direction == OUTFLOW_REVERSAL:
        reason_codes.append(OUTFLOW_REVERSAL_REASON)
    elif direction == INFLOW_REVERSAL:
        reason_codes.append(INFLOW_REVERSAL_REASON)
    else:
        reason_codes.append(ABSENT_REVERSAL_REASON)
    if direction != NO_REVERSAL and reversal_magnitude_usd >= config.watch_reversal_abs_usd:
        reason_codes.append(MATERIAL_REVERSAL_REASON)
    if (
        direction != NO_REVERSAL
        and reversal_magnitude_usd >= config.blocked_reversal_abs_usd
    ):
        reason_codes.append(LARGE_REVERSAL_REASON)
    reason_codes.append(SOURCE_FRESH_REASON if source_fresh else SOURCE_STALE_REASON)
    if value.source_count < config.min_source_count:
        reason_codes.append(THIN_SOURCE_REASON)
    if value.confirmation_count < config.min_confirmation_count:
        reason_codes.append(MISSING_CONFIRMATION_REASON)
    if value.flow_confidence < config.min_flow_confidence:
        reason_codes.append(LOW_CONFIDENCE_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    *,
    direction: str,
    reversal_magnitude_usd: Decimal,
    reason_codes: tuple[str, ...],
    config: MarketResearchCryptoEtfFlowReversalDigestConfig,
) -> str:
    if _has_blocking_quality_reason(reason_codes):
        return BLOCKED_STATUS
    if direction == NO_REVERSAL:
        return PASS_STATUS
    if reversal_magnitude_usd >= config.blocked_reversal_abs_usd:
        return BLOCKED_STATUS
    if reversal_magnitude_usd >= config.watch_reversal_abs_usd:
        return WATCH_STATUS
    return PASS_STATUS


def _has_blocking_quality_reason(reason_codes: tuple[str, ...]) -> bool:
    return any(
        reason_code in reason_codes
        for reason_code in (
            SOURCE_STALE_REASON,
            THIN_SOURCE_REASON,
            MISSING_CONFIRMATION_REASON,
            LOW_CONFIDENCE_REASON,
        )
    )


def _reversal_direction(
    *,
    previous_net_flow_usd: Decimal,
    current_net_flow_usd: Decimal,
) -> str:
    if previous_net_flow_usd > ZERO and current_net_flow_usd < ZERO:
        return OUTFLOW_REVERSAL
    if previous_net_flow_usd < ZERO and current_net_flow_usd > ZERO:
        return INFLOW_REVERSAL
    return NO_REVERSAL


def _report_reason_codes(
    rows: tuple[MarketResearchCryptoEtfFlowReversalRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketResearchCryptoEtfFlowReversalRow, ...],
) -> tuple[MarketResearchCryptoEtfFlowReversalReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == (EMPTY_REASON,):
        return (
            MarketResearchCryptoEtfFlowReversalReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MarketResearchCryptoEtfFlowReversalReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            row_ratio=_ratio(_reason_count(rows, reason_code), row_count),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    inputs: Iterable[MarketResearchCryptoEtfFlowReversalObservation],
) -> tuple[MarketResearchCryptoEtfFlowReversalObservation, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not MarketResearchCryptoEtfFlowReversalObservation:
            raise ValueError(
                "inputs must contain MarketResearchCryptoEtfFlowReversalObservation",
            )
        _require_hard_flags(value)
        if value.source_id in seen:
            raise ValueError("inputs must not contain duplicate source_id")
        seen.add(value.source_id)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketResearchCryptoEtfFlowReversalRow],
) -> tuple[MarketResearchCryptoEtfFlowReversalRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketResearchCryptoEtfFlowReversalRow:
            raise ValueError("rows must contain MarketResearchCryptoEtfFlowReversalRow")
        _require_hard_flags(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[MarketResearchCryptoEtfFlowReversalReasonCodeCount],
) -> tuple[MarketResearchCryptoEtfFlowReversalReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not MarketResearchCryptoEtfFlowReversalReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchCryptoEtfFlowReversalReasonCodeCount",
            )
        _require_hard_flags(value)
    return tuple(sorted(normalized, key=lambda value: value.reason_code))


def _validate_row(row: MarketResearchCryptoEtfFlowReversalRow) -> None:
    if row.flow_change_usd != _quantize_decimal(
        row.current_net_flow_usd - row.previous_net_flow_usd,
    ):
        raise ValueError("flow_change_usd must match current minus previous flow")
    if row.flow_change_abs_usd != _quantize_decimal(abs(row.flow_change_usd)):
        raise ValueError("flow_change_abs_usd must match flow_change_usd magnitude")
    expected_direction = _reversal_direction(
        previous_net_flow_usd=row.previous_net_flow_usd,
        current_net_flow_usd=row.current_net_flow_usd,
    )
    if row.reversal_direction != expected_direction:
        raise ValueError("reversal_direction must match flow signs")
    expected_magnitude = row.flow_change_abs_usd if row.reversal_direction != NO_REVERSAL else ZERO
    if row.reversal_magnitude_usd != expected_magnitude:
        raise ValueError("reversal_magnitude_usd must match reversal direction")


def _validate_report(report: MarketResearchCryptoEtfFlowReversalReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if (
        report.blocked_reversal_count
        + report.watch_reversal_count
        + report.routine_count
        != report.row_count
    ):
        raise ValueError("status counts must match row_count")
    if (
        report.outflow_reversal_count
        + report.inflow_reversal_count
        + report.no_reversal_count
        != report.row_count
    ):
        raise ValueError("direction counts must match row_count")
    if report.stale_source_count != _reason_count(report.rows, SOURCE_STALE_REASON):
        raise ValueError("stale_source_count must match rows")
    if report.thin_source_count != _reason_count(report.rows, THIN_SOURCE_REASON):
        raise ValueError("thin_source_count must match rows")
    if report.low_confirmation_count != _reason_count(
        report.rows,
        MISSING_CONFIRMATION_REASON,
    ):
        raise ValueError("low_confirmation_count must match rows")
    if report.low_confidence_count != _reason_count(report.rows, LOW_CONFIDENCE_REASON):
        raise ValueError("low_confidence_count must match rows")
    if report.max_reversal_magnitude_usd != _max_row_decimal(
        report.rows,
        "reversal_magnitude_usd",
    ):
        raise ValueError("max_reversal_magnitude_usd must match rows")
    if report.net_current_flow_usd != _sum_decimal(
        row.current_net_flow_usd for row in report.rows
    ):
        raise ValueError("net_current_flow_usd must match rows")
    if report.net_previous_flow_usd != _sum_decimal(
        row.previous_net_flow_usd for row in report.rows
    ):
        raise ValueError("net_previous_flow_usd must match rows")
    if report.aggregate_flow_change_usd != _sum_decimal(
        row.flow_change_usd for row in report.rows
    ):
        raise ValueError("aggregate_flow_change_usd must match rows")
    if report.average_flow_confidence != _ratio(
        _sum_decimal(row.flow_confidence for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_flow_confidence must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != RECOMMENDED_NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.reason_codes,
        report.rows,
    ):
        raise ValueError("reason_code_counts must match rows")


def _digest_status(rows: tuple[MarketResearchCryptoEtfFlowReversalRow, ...]) -> str:
    if not rows:
        return BLOCKED_STATUS
    if any(row.reversal_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if any(row.reversal_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(
    rows: tuple[MarketResearchCryptoEtfFlowReversalRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.reversal_status == status))


def _direction_count(
    rows: tuple[MarketResearchCryptoEtfFlowReversalRow, ...],
    direction: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.reversal_direction == direction))


def _reason_count(
    rows: tuple[MarketResearchCryptoEtfFlowReversalRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MarketResearchCryptoEtfFlowReversalRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize_decimal(numerator / denominator)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    whole_seconds = Decimal(delta.days * 86400 + delta.seconds)
    fractional_seconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize_decimal(whole_seconds + fractional_seconds)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")


def _row_sort_key(
    row: MarketResearchCryptoEtfFlowReversalRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.reversal_status],
        -row.reversal_magnitude_usd,
        row.asset_symbol,
        row.research_key,
        row.source_id,
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    return value
