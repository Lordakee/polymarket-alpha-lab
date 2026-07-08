"""Deterministic, report-only watch reports for abstract cost input drift."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_COST_INPUT_DRIFT_WATCH_CONFIG_VERSION = (
    "research-market-cost-input-drift-watch-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "question",
    "source_id",
    "source_ref",
    "source-url",
    "source_url",
    "source-text",
    "source_text",
    "http://",
    "https://",
    "dsn",
    "database",
    "table",
    "token",
    "secret",
    "auth",
    "credential",
    "private_key",
    "private key",
    "wallet",
    "order",
    "trade",
    "trading",
)
_ROW_REASON_SEQUENCE = (
    "spread_drift_block",
    "spread_drift_watch",
    "taker_fee_drift_block",
    "taker_fee_drift_watch",
    "depth_slope_drift_block",
    "depth_slope_drift_watch",
    "gas_friction_drift_block",
    "gas_friction_drift_watch",
    "deposit_friction_drift_block",
    "deposit_friction_drift_watch",
    "settlement_friction_drift_block",
    "settlement_friction_drift_watch",
    "total_friction_drift_block",
    "total_friction_drift_watch",
    "quote_staleness_block",
    "quote_staleness_watch",
    "cost_input_drift_block",
    "cost_input_drift_watch",
    "cost_input_drift_pass",
)
_REPORT_REASON_SEQUENCE = (
    "no_cost_input_drift_observations",
    "cost_input_drift_report_block_rows",
    "cost_input_drift_report_watch_rows",
    "cost_input_drift_report_pass",
)

_ROW_RECORD: type[Any]
_DIGEST_RECORD: type[Any]
_REPORT_RECORD: type[Any]

__all__ = (
    "DEFAULT_RESEARCH_MARKET_COST_INPUT_DRIFT_WATCH_CONFIG_VERSION",
    "ResearchMarketCostInputDriftWatchConfig",
    "ResearchMarketCostInputObservation",
    "ResearchMarketCostInputDriftWatchRow",
    "ResearchMarketCostInputDriftWatchDigest",
    "ResearchMarketCostInputDriftWatchReport",
    "build_research_market_cost_input_drift_watch_report",
    "research_market_cost_input_drift_watch_report_payload",
    "research_market_cost_input_drift_watch_digest_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketCostInputDriftWatchConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_COST_INPUT_DRIFT_WATCH_CONFIG_VERSION
    watch_spread_drift_bps: Decimal = Decimal("10.000000")
    block_spread_drift_bps: Decimal = Decimal("50.000000")
    watch_taker_fee_drift_bps: Decimal = Decimal("5.000000")
    block_taker_fee_drift_bps: Decimal = Decimal("20.000000")
    watch_depth_slope_drift_bps: Decimal = Decimal("20.000000")
    block_depth_slope_drift_bps: Decimal = Decimal("80.000000")
    watch_friction_drift_bps: Decimal = Decimal("10.000000")
    block_friction_drift_bps: Decimal = Decimal("40.000000")
    watch_total_friction_drift_bps: Decimal = Decimal("20.000000")
    block_total_friction_drift_bps: Decimal = Decimal("80.000000")
    watch_quote_age_seconds: Decimal = Decimal("300.000000")
    block_quote_age_seconds: Decimal = Decimal("900.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostInputDriftWatchConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for name in (
            "watch_spread_drift_bps",
            "block_spread_drift_bps",
            "watch_taker_fee_drift_bps",
            "block_taker_fee_drift_bps",
            "watch_depth_slope_drift_bps",
            "block_depth_slope_drift_bps",
            "watch_friction_drift_bps",
            "block_friction_drift_bps",
            "watch_total_friction_drift_bps",
            "block_total_friction_drift_bps",
            "watch_quote_age_seconds",
            "block_quote_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_ordered_threshold(
            "watch_spread_drift_bps",
            self.watch_spread_drift_bps,
            "block_spread_drift_bps",
            self.block_spread_drift_bps,
        )
        _require_ordered_threshold(
            "watch_taker_fee_drift_bps",
            self.watch_taker_fee_drift_bps,
            "block_taker_fee_drift_bps",
            self.block_taker_fee_drift_bps,
        )
        _require_ordered_threshold(
            "watch_depth_slope_drift_bps",
            self.watch_depth_slope_drift_bps,
            "block_depth_slope_drift_bps",
            self.block_depth_slope_drift_bps,
        )
        _require_ordered_threshold(
            "watch_friction_drift_bps",
            self.watch_friction_drift_bps,
            "block_friction_drift_bps",
            self.block_friction_drift_bps,
        )
        _require_ordered_threshold(
            "watch_total_friction_drift_bps",
            self.watch_total_friction_drift_bps,
            "block_total_friction_drift_bps",
            self.block_total_friction_drift_bps,
        )
        _require_ordered_threshold(
            "watch_quote_age_seconds",
            self.watch_quote_age_seconds,
            "block_quote_age_seconds",
            self.block_quote_age_seconds,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketCostInputObservation(_FinalPublicDataclass):
    cost_input_bucket: str
    cost_surface_bucket: str
    observed_at: datetime
    baseline_spread_bps: Decimal
    current_spread_bps: Decimal
    baseline_taker_fee_bps: Decimal
    current_taker_fee_bps: Decimal
    baseline_depth_slope_bps: Decimal
    current_depth_slope_bps: Decimal
    baseline_gas_friction_bps: Decimal
    current_gas_friction_bps: Decimal
    baseline_deposit_friction_bps: Decimal
    current_deposit_friction_bps: Decimal
    baseline_settlement_friction_bps: Decimal
    current_settlement_friction_bps: Decimal
    quote_age_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostInputObservation, "observation")
        object.__setattr__(
            self,
            "cost_input_bucket",
            _require_public_identifier("cost_input_bucket", self.cost_input_bucket),
        )
        object.__setattr__(
            self,
            "cost_surface_bucket",
            _require_public_identifier("cost_surface_bucket", self.cost_surface_bucket),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in (
            "baseline_spread_bps",
            "current_spread_bps",
            "baseline_taker_fee_bps",
            "current_taker_fee_bps",
            "baseline_depth_slope_bps",
            "current_depth_slope_bps",
            "baseline_gas_friction_bps",
            "current_gas_friction_bps",
            "baseline_deposit_friction_bps",
            "current_deposit_friction_bps",
            "baseline_settlement_friction_bps",
            "current_settlement_friction_bps",
            "quote_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_SEQUENCE),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketCostInputDriftWatchRow(_FinalPublicDataclass):
    cost_input_bucket: str
    cost_surface_bucket: str
    observed_at: datetime
    baseline_spread_bps: Decimal
    current_spread_bps: Decimal
    spread_drift_bps: Decimal
    absolute_spread_drift_bps: Decimal
    baseline_taker_fee_bps: Decimal
    current_taker_fee_bps: Decimal
    taker_fee_drift_bps: Decimal
    absolute_taker_fee_drift_bps: Decimal
    baseline_depth_slope_bps: Decimal
    current_depth_slope_bps: Decimal
    depth_slope_drift_bps: Decimal
    absolute_depth_slope_drift_bps: Decimal
    baseline_gas_friction_bps: Decimal
    current_gas_friction_bps: Decimal
    gas_friction_drift_bps: Decimal
    absolute_gas_friction_drift_bps: Decimal
    baseline_deposit_friction_bps: Decimal
    current_deposit_friction_bps: Decimal
    deposit_friction_drift_bps: Decimal
    absolute_deposit_friction_drift_bps: Decimal
    baseline_settlement_friction_bps: Decimal
    current_settlement_friction_bps: Decimal
    settlement_friction_drift_bps: Decimal
    absolute_settlement_friction_drift_bps: Decimal
    baseline_total_friction_bps: Decimal
    current_total_friction_bps: Decimal
    total_friction_drift_bps: Decimal
    absolute_total_friction_drift_bps: Decimal
    baseline_total_cost_bps: Decimal
    current_total_cost_bps: Decimal
    total_cost_drift_bps: Decimal
    absolute_total_cost_drift_bps: Decimal
    quote_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostInputDriftWatchRow, "row")
        object.__setattr__(
            self,
            "cost_input_bucket",
            _require_public_identifier("cost_input_bucket", self.cost_input_bucket),
        )
        object.__setattr__(
            self,
            "cost_surface_bucket",
            _require_public_identifier("cost_surface_bucket", self.cost_surface_bucket),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in (
            "baseline_spread_bps",
            "current_spread_bps",
            "absolute_spread_drift_bps",
            "baseline_taker_fee_bps",
            "current_taker_fee_bps",
            "absolute_taker_fee_drift_bps",
            "baseline_depth_slope_bps",
            "current_depth_slope_bps",
            "absolute_depth_slope_drift_bps",
            "baseline_gas_friction_bps",
            "current_gas_friction_bps",
            "absolute_gas_friction_drift_bps",
            "baseline_deposit_friction_bps",
            "current_deposit_friction_bps",
            "absolute_deposit_friction_drift_bps",
            "baseline_settlement_friction_bps",
            "current_settlement_friction_bps",
            "absolute_settlement_friction_drift_bps",
            "baseline_total_friction_bps",
            "current_total_friction_bps",
            "absolute_total_friction_drift_bps",
            "baseline_total_cost_bps",
            "current_total_cost_bps",
            "absolute_total_cost_drift_bps",
            "quote_age_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        for name in (
            "spread_drift_bps",
            "taker_fee_drift_bps",
            "depth_slope_drift_bps",
            "gas_friction_drift_bps",
            "deposit_friction_drift_bps",
            "settlement_friction_drift_bps",
            "total_friction_drift_bps",
            "total_cost_drift_bps",
        ):
            object.__setattr__(self, name, _require_decimal(name, getattr(self, name)))
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketCostInputDriftWatchDigest(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_absolute_total_cost_drift_bps: Decimal
    max_absolute_total_cost_drift_bps: Decimal
    average_absolute_total_friction_drift_bps: Decimal
    max_absolute_total_friction_drift_bps: Decimal
    max_quote_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostInputDriftWatchDigest, "digest")
        _normalize_summary_fields(self)
        _validate_summary_counts(self)
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_SEQUENCE),
        )
        if self.status != _summary_status_from_counts(
            block_count=self.block_count,
            watch_count=self.watch_count,
            input_count=self.input_count,
        ):
            raise ValueError("status must match summary counts")
        if self.reason_codes != _report_reason_codes(
            block_count=self.block_count,
            watch_count=self.watch_count,
            input_count=self.input_count,
        ):
            raise ValueError("reason_codes must match status")
        _require_hard_flags("digest", self)
        _reject_unsafe_public_payload("digest", self)
        _finalize_digest_payload(self)


@dataclass(frozen=True)
class ResearchMarketCostInputDriftWatchReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_absolute_total_cost_drift_bps: Decimal
    max_absolute_total_cost_drift_bps: Decimal
    average_absolute_total_friction_drift_bps: Decimal
    max_absolute_total_friction_drift_bps: Decimal
    max_quote_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    digest: ResearchMarketCostInputDriftWatchDigest
    rows: tuple[ResearchMarketCostInputDriftWatchRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostInputDriftWatchReport, "report")
        _normalize_summary_fields(self)
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_SEQUENCE),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if type(self.digest) is not ResearchMarketCostInputDriftWatchDigest:
            raise ValueError("digest must be a ResearchMarketCostInputDriftWatchDigest")
        _validate_report(self)
        _validate_summary_counts(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _finalize_report_payload(self)


_ROW_RECORD = ResearchMarketCostInputDriftWatchRow
_DIGEST_RECORD = ResearchMarketCostInputDriftWatchDigest
_REPORT_RECORD = ResearchMarketCostInputDriftWatchReport


def build_research_market_cost_input_drift_watch_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketCostInputDriftWatchConfig,
    generated_at: datetime,
) -> ResearchMarketCostInputDriftWatchReport:
    if type(config) is not ResearchMarketCostInputDriftWatchConfig:
        raise ValueError("config must be a ResearchMarketCostInputDriftWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_observation(item, config) for item in items),
            key=_row_key,
        ),
    )
    summary = _summary_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    digest = _DIGEST_RECORD(**summary)
    return _REPORT_RECORD(
        **summary,
        digest=digest,
        rows=rows,
    )


def research_market_cost_input_drift_watch_report_payload(
    report: ResearchMarketCostInputDriftWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketCostInputDriftWatchReport:
        _require_hard_flags("report", report)
        _validate_payload_digest("report", report.payload)
        return report.payload
    if type(report) is dict:
        _validate_payload_digest("report", report)
        digest_payload = report.get("digest")
        if type(digest_payload) is not dict:
            raise ValueError("digest must be a payload object")
        _validate_payload_digest("digest", digest_payload)
        return report
    raise ValueError("report must be a ResearchMarketCostInputDriftWatchReport")


def research_market_cost_input_drift_watch_digest_payload(
    digest: ResearchMarketCostInputDriftWatchDigest | dict[str, Any],
) -> dict[str, Any]:
    if type(digest) is ResearchMarketCostInputDriftWatchDigest:
        _require_hard_flags("digest", digest)
        _validate_payload_digest("digest", digest.payload)
        return digest.payload
    if type(digest) is dict:
        _validate_payload_digest("digest", digest)
        return digest
    raise ValueError("digest must be a ResearchMarketCostInputDriftWatchDigest")


def _row_from_observation(
    item: ResearchMarketCostInputObservation,
    config: ResearchMarketCostInputDriftWatchConfig,
) -> ResearchMarketCostInputDriftWatchRow:
    spread_drift = _quantize(item.current_spread_bps - item.baseline_spread_bps)
    taker_fee_drift = _quantize(
        item.current_taker_fee_bps - item.baseline_taker_fee_bps,
    )
    depth_slope_drift = _quantize(
        item.current_depth_slope_bps - item.baseline_depth_slope_bps,
    )
    gas_drift = _quantize(
        item.current_gas_friction_bps - item.baseline_gas_friction_bps,
    )
    deposit_drift = _quantize(
        item.current_deposit_friction_bps - item.baseline_deposit_friction_bps,
    )
    settlement_drift = _quantize(
        item.current_settlement_friction_bps
        - item.baseline_settlement_friction_bps,
    )
    baseline_total_friction = _total_friction(
        gas=item.baseline_gas_friction_bps,
        deposit=item.baseline_deposit_friction_bps,
        settlement=item.baseline_settlement_friction_bps,
    )
    current_total_friction = _total_friction(
        gas=item.current_gas_friction_bps,
        deposit=item.current_deposit_friction_bps,
        settlement=item.current_settlement_friction_bps,
    )
    total_friction_drift = _quantize(
        current_total_friction - baseline_total_friction,
    )
    baseline_total_cost = _total_cost(
        spread=item.baseline_spread_bps,
        taker_fee=item.baseline_taker_fee_bps,
        depth_slope=item.baseline_depth_slope_bps,
        total_friction=baseline_total_friction,
    )
    current_total_cost = _total_cost(
        spread=item.current_spread_bps,
        taker_fee=item.current_taker_fee_bps,
        depth_slope=item.current_depth_slope_bps,
        total_friction=current_total_friction,
    )
    total_cost_drift = _quantize(current_total_cost - baseline_total_cost)
    status, reason_codes = _row_status_and_reasons(
        spread_drift=_absolute_decimal(spread_drift),
        taker_fee_drift=_absolute_decimal(taker_fee_drift),
        depth_slope_drift=_absolute_decimal(depth_slope_drift),
        gas_friction_drift=_absolute_decimal(gas_drift),
        deposit_friction_drift=_absolute_decimal(deposit_drift),
        settlement_friction_drift=_absolute_decimal(settlement_drift),
        total_friction_drift=_absolute_decimal(total_friction_drift),
        quote_age_seconds=item.quote_age_seconds,
        config=config,
    )
    return _ROW_RECORD(
        cost_input_bucket=item.cost_input_bucket,
        cost_surface_bucket=item.cost_surface_bucket,
        observed_at=item.observed_at,
        baseline_spread_bps=item.baseline_spread_bps,
        current_spread_bps=item.current_spread_bps,
        spread_drift_bps=spread_drift,
        absolute_spread_drift_bps=_absolute_decimal(spread_drift),
        baseline_taker_fee_bps=item.baseline_taker_fee_bps,
        current_taker_fee_bps=item.current_taker_fee_bps,
        taker_fee_drift_bps=taker_fee_drift,
        absolute_taker_fee_drift_bps=_absolute_decimal(taker_fee_drift),
        baseline_depth_slope_bps=item.baseline_depth_slope_bps,
        current_depth_slope_bps=item.current_depth_slope_bps,
        depth_slope_drift_bps=depth_slope_drift,
        absolute_depth_slope_drift_bps=_absolute_decimal(depth_slope_drift),
        baseline_gas_friction_bps=item.baseline_gas_friction_bps,
        current_gas_friction_bps=item.current_gas_friction_bps,
        gas_friction_drift_bps=gas_drift,
        absolute_gas_friction_drift_bps=_absolute_decimal(gas_drift),
        baseline_deposit_friction_bps=item.baseline_deposit_friction_bps,
        current_deposit_friction_bps=item.current_deposit_friction_bps,
        deposit_friction_drift_bps=deposit_drift,
        absolute_deposit_friction_drift_bps=_absolute_decimal(deposit_drift),
        baseline_settlement_friction_bps=item.baseline_settlement_friction_bps,
        current_settlement_friction_bps=item.current_settlement_friction_bps,
        settlement_friction_drift_bps=settlement_drift,
        absolute_settlement_friction_drift_bps=_absolute_decimal(settlement_drift),
        baseline_total_friction_bps=baseline_total_friction,
        current_total_friction_bps=current_total_friction,
        total_friction_drift_bps=total_friction_drift,
        absolute_total_friction_drift_bps=_absolute_decimal(total_friction_drift),
        baseline_total_cost_bps=baseline_total_cost,
        current_total_cost_bps=current_total_cost,
        total_cost_drift_bps=total_cost_drift,
        absolute_total_cost_drift_bps=_absolute_decimal(total_cost_drift),
        quote_age_seconds=item.quote_age_seconds,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    *,
    spread_drift: Decimal,
    taker_fee_drift: Decimal,
    depth_slope_drift: Decimal,
    gas_friction_drift: Decimal,
    deposit_friction_drift: Decimal,
    settlement_friction_drift: Decimal,
    total_friction_drift: Decimal,
    quote_age_seconds: Decimal,
    config: ResearchMarketCostInputDriftWatchConfig,
) -> tuple[str, tuple[str, ...]]:
    status = "pass"
    reasons: list[str] = []

    status = _append_threshold_reason(
        status,
        reasons,
        value=spread_drift,
        watch_value=config.watch_spread_drift_bps,
        block_value=config.block_spread_drift_bps,
        watch_reason="spread_drift_watch",
        block_reason="spread_drift_block",
    )
    status = _append_threshold_reason(
        status,
        reasons,
        value=taker_fee_drift,
        watch_value=config.watch_taker_fee_drift_bps,
        block_value=config.block_taker_fee_drift_bps,
        watch_reason="taker_fee_drift_watch",
        block_reason="taker_fee_drift_block",
    )
    status = _append_threshold_reason(
        status,
        reasons,
        value=depth_slope_drift,
        watch_value=config.watch_depth_slope_drift_bps,
        block_value=config.block_depth_slope_drift_bps,
        watch_reason="depth_slope_drift_watch",
        block_reason="depth_slope_drift_block",
    )
    for value, watch_reason, block_reason in (
        (gas_friction_drift, "gas_friction_drift_watch", "gas_friction_drift_block"),
        (
            deposit_friction_drift,
            "deposit_friction_drift_watch",
            "deposit_friction_drift_block",
        ),
        (
            settlement_friction_drift,
            "settlement_friction_drift_watch",
            "settlement_friction_drift_block",
        ),
    ):
        status = _append_threshold_reason(
            status,
            reasons,
            value=value,
            watch_value=config.watch_friction_drift_bps,
            block_value=config.block_friction_drift_bps,
            watch_reason=watch_reason,
            block_reason=block_reason,
        )
    status = _append_threshold_reason(
        status,
        reasons,
        value=total_friction_drift,
        watch_value=config.watch_total_friction_drift_bps,
        block_value=config.block_total_friction_drift_bps,
        watch_reason="total_friction_drift_watch",
        block_reason="total_friction_drift_block",
    )
    status = _append_threshold_reason(
        status,
        reasons,
        value=quote_age_seconds,
        watch_value=config.watch_quote_age_seconds,
        block_value=config.block_quote_age_seconds,
        watch_reason="quote_staleness_watch",
        block_reason="quote_staleness_block",
    )

    if status == "block":
        reasons.append("cost_input_drift_block")
    elif status == "watch":
        reasons.append("cost_input_drift_watch")
    else:
        reasons.append("cost_input_drift_pass")
    return status, _normalize_reason_codes(tuple(reasons), _ROW_REASON_SEQUENCE)


def _append_threshold_reason(
    status: str,
    reasons: list[str],
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= block_value:
        reasons.append(block_reason)
        return "block"
    if value >= watch_value:
        reasons.append(watch_reason)
        if status != "block":
            return "watch"
    return status


def _summary_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchMarketCostInputDriftWatchRow, ...],
) -> dict[str, Any]:
    block_count = _decimal_count(sum(1 for row in rows if row.status == "block"))
    watch_count = _decimal_count(sum(1 for row in rows if row.status == "watch"))
    input_count = _decimal_count(len(rows))
    status = _summary_status_from_counts(
        block_count=block_count,
        watch_count=watch_count,
        input_count=input_count,
    )
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "input_count": input_count,
        "pass_count": _decimal_count(sum(1 for row in rows if row.status == "pass")),
        "watch_count": watch_count,
        "block_count": block_count,
        "average_absolute_total_cost_drift_bps": _mean(
            tuple(row.absolute_total_cost_drift_bps for row in rows),
        ),
        "max_absolute_total_cost_drift_bps": _max_decimal(
            tuple(row.absolute_total_cost_drift_bps for row in rows),
        ),
        "average_absolute_total_friction_drift_bps": _mean(
            tuple(row.absolute_total_friction_drift_bps for row in rows),
        ),
        "max_absolute_total_friction_drift_bps": _max_decimal(
            tuple(row.absolute_total_friction_drift_bps for row in rows),
        ),
        "max_quote_age_seconds": _max_decimal(
            tuple(row.quote_age_seconds for row in rows),
        ),
        "status": status,
        "reason_codes": _report_reason_codes(
            block_count=block_count,
            watch_count=watch_count,
            input_count=input_count,
        ),
    }


def _normalize_summary_fields(
    value: ResearchMarketCostInputDriftWatchDigest | ResearchMarketCostInputDriftWatchReport,
) -> None:
    object.__setattr__(value, "generated_at", _as_utc("generated_at", value.generated_at))
    object.__setattr__(
        value,
        "config_version",
        _require_public_identifier("config_version", value.config_version),
    )
    for name in (
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_absolute_total_cost_drift_bps",
        "max_absolute_total_cost_drift_bps",
        "average_absolute_total_friction_drift_bps",
        "max_absolute_total_friction_drift_bps",
        "max_quote_age_seconds",
    ):
        object.__setattr__(
            value,
            name,
            _require_nonnegative_decimal(name, getattr(value, name)),
        )


def _validate_summary_counts(
    value: ResearchMarketCostInputDriftWatchDigest | ResearchMarketCostInputDriftWatchReport,
) -> None:
    if value.pass_count + value.watch_count + value.block_count != value.input_count:
        raise ValueError("status counts must match input_count")
    if value.max_absolute_total_cost_drift_bps < (
        value.average_absolute_total_cost_drift_bps
    ):
        raise ValueError("max_absolute_total_cost_drift_bps must be at least average")
    if value.max_absolute_total_friction_drift_bps < (
        value.average_absolute_total_friction_drift_bps
    ):
        raise ValueError("max_absolute_total_friction_drift_bps must be at least average")


def _validate_report(report: ResearchMarketCostInputDriftWatchReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_key)):
        raise ValueError("rows must be sorted by cost input and surface bucket")
    if len({(row.cost_input_bucket, row.cost_surface_bucket) for row in report.rows}) != len(
        report.rows,
    ):
        raise ValueError("rows must contain unique cost input and surface bucket pairs")
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.average_absolute_total_cost_drift_bps != _mean(
        tuple(row.absolute_total_cost_drift_bps for row in report.rows),
    ):
        raise ValueError("average_absolute_total_cost_drift_bps must match rows")
    if report.max_absolute_total_cost_drift_bps != _max_decimal(
        tuple(row.absolute_total_cost_drift_bps for row in report.rows),
    ):
        raise ValueError("max_absolute_total_cost_drift_bps must match rows")
    if report.average_absolute_total_friction_drift_bps != _mean(
        tuple(row.absolute_total_friction_drift_bps for row in report.rows),
    ):
        raise ValueError("average_absolute_total_friction_drift_bps must match rows")
    if report.max_absolute_total_friction_drift_bps != _max_decimal(
        tuple(row.absolute_total_friction_drift_bps for row in report.rows),
    ):
        raise ValueError("max_absolute_total_friction_drift_bps must match rows")
    if report.max_quote_age_seconds != _max_decimal(
        tuple(row.quote_age_seconds for row in report.rows),
    ):
        raise ValueError("max_quote_age_seconds must match rows")
    if report.status != _summary_status_from_counts(
        block_count=report.block_count,
        watch_count=report.watch_count,
        input_count=report.input_count,
    ):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(
        block_count=report.block_count,
        watch_count=report.watch_count,
        input_count=report.input_count,
    ):
        raise ValueError("reason_codes must match rows")
    if not _digest_matches_report(report.digest, report):
        raise ValueError("digest must match report summary")


def _validate_row(row: ResearchMarketCostInputDriftWatchRow) -> None:
    expected_total_friction = _total_friction(
        gas=row.baseline_gas_friction_bps,
        deposit=row.baseline_deposit_friction_bps,
        settlement=row.baseline_settlement_friction_bps,
    )
    if row.baseline_total_friction_bps != expected_total_friction:
        raise ValueError("baseline_total_friction_bps must match friction inputs")
    expected_current_friction = _total_friction(
        gas=row.current_gas_friction_bps,
        deposit=row.current_deposit_friction_bps,
        settlement=row.current_settlement_friction_bps,
    )
    if row.current_total_friction_bps != expected_current_friction:
        raise ValueError("current_total_friction_bps must match friction inputs")
    expected_baseline_cost = _total_cost(
        spread=row.baseline_spread_bps,
        taker_fee=row.baseline_taker_fee_bps,
        depth_slope=row.baseline_depth_slope_bps,
        total_friction=row.baseline_total_friction_bps,
    )
    if row.baseline_total_cost_bps != expected_baseline_cost:
        raise ValueError("baseline_total_cost_bps must match cost inputs")
    expected_current_cost = _total_cost(
        spread=row.current_spread_bps,
        taker_fee=row.current_taker_fee_bps,
        depth_slope=row.current_depth_slope_bps,
        total_friction=row.current_total_friction_bps,
    )
    if row.current_total_cost_bps != expected_current_cost:
        raise ValueError("current_total_cost_bps must match cost inputs")
    for name, current_name, baseline_name in (
        ("spread_drift_bps", "current_spread_bps", "baseline_spread_bps"),
        ("taker_fee_drift_bps", "current_taker_fee_bps", "baseline_taker_fee_bps"),
        ("depth_slope_drift_bps", "current_depth_slope_bps", "baseline_depth_slope_bps"),
        (
            "gas_friction_drift_bps",
            "current_gas_friction_bps",
            "baseline_gas_friction_bps",
        ),
        (
            "deposit_friction_drift_bps",
            "current_deposit_friction_bps",
            "baseline_deposit_friction_bps",
        ),
        (
            "settlement_friction_drift_bps",
            "current_settlement_friction_bps",
            "baseline_settlement_friction_bps",
        ),
        (
            "total_friction_drift_bps",
            "current_total_friction_bps",
            "baseline_total_friction_bps",
        ),
        ("total_cost_drift_bps", "current_total_cost_bps", "baseline_total_cost_bps"),
    ):
        expected_delta = _quantize(getattr(row, current_name) - getattr(row, baseline_name))
        actual_delta = getattr(row, name)
        if actual_delta != expected_delta:
            raise ValueError(f"{name} must match cost inputs")
        absolute_name = f"absolute_{name}"
        if getattr(row, absolute_name) != _absolute_decimal(actual_delta):
            raise ValueError(f"{absolute_name} must match {name}")
    if row.status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _digest_matches_report(
    digest: ResearchMarketCostInputDriftWatchDigest,
    report: ResearchMarketCostInputDriftWatchReport,
) -> bool:
    names = (
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_absolute_total_cost_drift_bps",
        "max_absolute_total_cost_drift_bps",
        "average_absolute_total_friction_drift_bps",
        "max_absolute_total_friction_drift_bps",
        "max_quote_age_seconds",
        "status",
        "reason_codes",
    )
    return all(getattr(digest, name) == getattr(report, name) for name in names)


def _finalize_digest_payload(digest: ResearchMarketCostInputDriftWatchDigest) -> None:
    base_payload = _digest_payload_base(digest)
    expected_digest = _payload_digest(base_payload)
    supplied = digest.derived_validation_digest
    if supplied == "":
        object.__setattr__(digest, "derived_validation_digest", expected_digest)
    elif supplied != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = dict(base_payload)
    payload["derived_validation_digest"] = digest.derived_validation_digest
    _reject_unsafe_public_payload("digest.payload", payload)
    object.__setattr__(digest, "payload", payload)


def _finalize_report_payload(report: ResearchMarketCostInputDriftWatchReport) -> None:
    base_payload = _report_payload_base(report)
    expected_digest = _payload_digest(base_payload)
    supplied = report.derived_validation_digest
    if supplied == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
    elif supplied != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = dict(base_payload)
    payload["derived_validation_digest"] = report.derived_validation_digest
    _reject_unsafe_public_payload("report.payload", payload)
    object.__setattr__(report, "payload", payload)


def _digest_payload_base(digest: ResearchMarketCostInputDriftWatchDigest) -> dict[str, Any]:
    return {
        "generated_at": digest.generated_at.isoformat(),
        "config_version": digest.config_version,
        "input_count": _decimal_string(digest.input_count),
        "pass_count": _decimal_string(digest.pass_count),
        "watch_count": _decimal_string(digest.watch_count),
        "block_count": _decimal_string(digest.block_count),
        "average_absolute_total_cost_drift_bps": _decimal_string(
            digest.average_absolute_total_cost_drift_bps,
        ),
        "max_absolute_total_cost_drift_bps": _decimal_string(
            digest.max_absolute_total_cost_drift_bps,
        ),
        "average_absolute_total_friction_drift_bps": _decimal_string(
            digest.average_absolute_total_friction_drift_bps,
        ),
        "max_absolute_total_friction_drift_bps": _decimal_string(
            digest.max_absolute_total_friction_drift_bps,
        ),
        "max_quote_age_seconds": _decimal_string(digest.max_quote_age_seconds),
        "status": digest.status,
        "reason_codes": list(digest.reason_codes),
        "paper_only": digest.paper_only,
        "report_only": digest.report_only,
        "readonly": digest.readonly,
    }


def _report_payload_base(report: ResearchMarketCostInputDriftWatchReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "input_count": _decimal_string(report.input_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "average_absolute_total_cost_drift_bps": _decimal_string(
            report.average_absolute_total_cost_drift_bps,
        ),
        "max_absolute_total_cost_drift_bps": _decimal_string(
            report.max_absolute_total_cost_drift_bps,
        ),
        "average_absolute_total_friction_drift_bps": _decimal_string(
            report.average_absolute_total_friction_drift_bps,
        ),
        "max_absolute_total_friction_drift_bps": _decimal_string(
            report.max_absolute_total_friction_drift_bps,
        ),
        "max_quote_age_seconds": _decimal_string(report.max_quote_age_seconds),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "digest": report.digest.payload,
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchMarketCostInputDriftWatchRow) -> dict[str, Any]:
    return {
        "input_bucket_digest": _public_digest(row.cost_input_bucket),
        "surface_bucket_digest": _public_digest(row.cost_surface_bucket),
        "observed_at": row.observed_at.isoformat(),
        "baseline_spread_bps": _decimal_string(row.baseline_spread_bps),
        "current_spread_bps": _decimal_string(row.current_spread_bps),
        "spread_drift_bps": _decimal_string(row.spread_drift_bps),
        "absolute_spread_drift_bps": _decimal_string(row.absolute_spread_drift_bps),
        "baseline_taker_fee_bps": _decimal_string(row.baseline_taker_fee_bps),
        "current_taker_fee_bps": _decimal_string(row.current_taker_fee_bps),
        "taker_fee_drift_bps": _decimal_string(row.taker_fee_drift_bps),
        "absolute_taker_fee_drift_bps": _decimal_string(
            row.absolute_taker_fee_drift_bps,
        ),
        "baseline_depth_slope_bps": _decimal_string(row.baseline_depth_slope_bps),
        "current_depth_slope_bps": _decimal_string(row.current_depth_slope_bps),
        "depth_slope_drift_bps": _decimal_string(row.depth_slope_drift_bps),
        "absolute_depth_slope_drift_bps": _decimal_string(
            row.absolute_depth_slope_drift_bps,
        ),
        "baseline_gas_friction_bps": _decimal_string(row.baseline_gas_friction_bps),
        "current_gas_friction_bps": _decimal_string(row.current_gas_friction_bps),
        "gas_friction_drift_bps": _decimal_string(row.gas_friction_drift_bps),
        "absolute_gas_friction_drift_bps": _decimal_string(
            row.absolute_gas_friction_drift_bps,
        ),
        "baseline_deposit_friction_bps": _decimal_string(
            row.baseline_deposit_friction_bps,
        ),
        "current_deposit_friction_bps": _decimal_string(
            row.current_deposit_friction_bps,
        ),
        "deposit_friction_drift_bps": _decimal_string(row.deposit_friction_drift_bps),
        "absolute_deposit_friction_drift_bps": _decimal_string(
            row.absolute_deposit_friction_drift_bps,
        ),
        "baseline_settlement_friction_bps": _decimal_string(
            row.baseline_settlement_friction_bps,
        ),
        "current_settlement_friction_bps": _decimal_string(
            row.current_settlement_friction_bps,
        ),
        "settlement_friction_drift_bps": _decimal_string(
            row.settlement_friction_drift_bps,
        ),
        "absolute_settlement_friction_drift_bps": _decimal_string(
            row.absolute_settlement_friction_drift_bps,
        ),
        "baseline_total_friction_bps": _decimal_string(row.baseline_total_friction_bps),
        "current_total_friction_bps": _decimal_string(row.current_total_friction_bps),
        "total_friction_drift_bps": _decimal_string(row.total_friction_drift_bps),
        "absolute_total_friction_drift_bps": _decimal_string(
            row.absolute_total_friction_drift_bps,
        ),
        "baseline_total_cost_bps": _decimal_string(row.baseline_total_cost_bps),
        "current_total_cost_bps": _decimal_string(row.current_total_cost_bps),
        "total_cost_drift_bps": _decimal_string(row.total_cost_drift_bps),
        "absolute_total_cost_drift_bps": _decimal_string(
            row.absolute_total_cost_drift_bps,
        ),
        "quote_age_seconds": _decimal_string(row.quote_age_seconds),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketCostInputObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    items = tuple(observations)
    for item in items:
        if type(item) is not ResearchMarketCostInputObservation:
            raise ValueError(
                "observations must contain ResearchMarketCostInputObservation values",
            )
        _require_hard_flags("observation", item)
    if len({(item.cost_input_bucket, item.cost_surface_bucket) for item in items}) != len(
        items,
    ):
        raise ValueError("observations must contain unique cost input and surface pairs")
    return items


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketCostInputDriftWatchRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    clean = tuple(rows)
    for row in clean:
        if type(row) is not ResearchMarketCostInputDriftWatchRow:
            raise ValueError("rows must contain ResearchMarketCostInputDriftWatchRow values")
        _require_hard_flags("row", row)
    return clean


def _normalize_reason_codes(
    value: object,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    clean: list[str] = []
    allowed = frozenset(allowed_sequence)
    for item in value:
        if type(item) is not str:
            raise ValueError("reason_codes must contain strings")
        code = _require_public_identifier("reason_codes", item)
        if code not in allowed:
            raise ValueError("reason_codes contains an unknown reason code")
        if code not in clean:
            clean.append(code)
    return tuple(code for code in allowed_sequence if code in clean)


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "cost_input_drift_block" in reason_codes:
        return "block"
    if "cost_input_drift_watch" in reason_codes:
        return "watch"
    return "pass"


def _summary_status_from_counts(
    *,
    block_count: Decimal,
    watch_count: Decimal,
    input_count: Decimal,
) -> str:
    if input_count == _ZERO or block_count > _ZERO:
        return "block"
    if watch_count > _ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    block_count: Decimal,
    watch_count: Decimal,
    input_count: Decimal,
) -> tuple[str, ...]:
    if input_count == _ZERO:
        return ("no_cost_input_drift_observations",)
    reasons: list[str] = []
    if block_count > _ZERO:
        reasons.append("cost_input_drift_report_block_rows")
    if watch_count > _ZERO:
        reasons.append("cost_input_drift_report_watch_rows")
    if not reasons:
        reasons.append("cost_input_drift_report_pass")
    return tuple(reasons)


def _row_key(row: ResearchMarketCostInputDriftWatchRow) -> tuple[str, str]:
    return (row.cost_input_bucket, row.cost_surface_bucket)


def _total_friction(*, gas: Decimal, deposit: Decimal, settlement: Decimal) -> Decimal:
    return _quantize(gas + deposit + settlement)


def _total_cost(
    *,
    spread: Decimal,
    taker_fee: Decimal,
    depth_slope: Decimal,
    total_friction: Decimal,
) -> Decimal:
    return _quantize(spread + taker_fee + depth_slope + total_friction)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _quantize(-value)
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return clean


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(value)


def _require_ordered_threshold(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{watch_name} must not exceed {block_name}")


def _decimal_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{item.name}",
                getattr(value, item.name),
            )
        return
    if type(value) is str:
        lower_value = value.lower()
        if any(term in lower_value for term in _UNSAFE_PUBLIC_TERMS):
            raise ValueError("unsafe public payload")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("unsafe public payload")
        if not value.is_finite():
            raise ValueError("unsafe public payload")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("unsafe public payload")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("unsafe public payload")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError("unsafe public payload")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("unsafe public payload")


def _public_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(label: str, payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} payload must be a JSON object")
    _reject_unsafe_public_payload(label, payload)
    supplied = payload.get("derived_validation_digest")
    if type(supplied) is not str or _DIGEST_RE.fullmatch(supplied) is None:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    base_payload = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    if _payload_digest(base_payload) != supplied:
        raise ValueError("derived_validation_digest must match payload fields")
