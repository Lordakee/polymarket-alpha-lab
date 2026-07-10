"""Pure Phase 1 report reducer for orderbook spread stability diagnostics."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "ORDERBOOK_SPREAD_STABILITY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_ORDERBOOK_SPREAD_STABILITY_REPORT_CONFIG_VERSION",
    "ResearchMarketOrderbookSpreadStabilityConfig",
    "ResearchMarketOrderbookSpreadStabilitySnapshot",
    "ResearchMarketOrderbookSpreadStabilityReasonCodeCount",
    "ResearchMarketOrderbookSpreadStabilityReport",
    "ResearchMarketOrderbookSpreadStabilityRow",
    "build_research_market_orderbook_spread_stability_report",
    "research_market_orderbook_spread_stability_report_digest",
    "research_market_orderbook_spread_stability_report_payload",
    "validate_research_market_orderbook_spread_stability_report_payload",
)


ORDERBOOK_SPREAD_STABILITY_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_MARKET_ORDERBOOK_SPREAD_STABILITY_REPORT_CONFIG_VERSION = (
    "research-spread-stability-report-v1"
)

DECIMAL_PRECISION = 64
COUNT_QUANTUM = Decimal("1")
METRIC_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2")
BASIS_POINTS = Decimal("10000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SECONDS_PER_DAY = 86400

PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

UNSAFE_PUBLIC_FRAGMENTS = (
    "auth",
    "candidate_id",
    "condition_id",
    "credential",
    "database",
    "dsn",
    "execution",
    "live",
    "market_id",
    "market_slug",
    "network",
    "order",
    "persist",
    "position",
    "private_key",
    "question",
    "recommend",
    "secret",
    "signing",
    "sizing",
    "source_text",
    "source_url",
    "table_name",
    "token",
    "trade",
    "wallet",
    "://",
)

COMPONENT_PREFIXES = (
    "spread_bps",
    "bid_depth_change",
    "ask_depth_change",
    "snapshot_age",
    "fee_pressure",
)
ROW_BASE_REASON_CODES = tuple(
    f"{prefix}_{status}"
    for prefix in ("spread_stability", *COMPONENT_PREFIXES)
    for status in ORDERBOOK_SPREAD_STABILITY_STATUSES
)
REPORT_REASON_CODE_ORDER = (
    "spread_stability_report_block",
    "spread_stability_report_watch",
    "spread_bps_block",
    "bid_depth_change_block",
    "ask_depth_change_block",
    "snapshot_age_block",
    "fee_pressure_block",
    "spread_bps_watch",
    "bid_depth_change_watch",
    "ask_depth_change_watch",
    "snapshot_age_watch",
    "fee_pressure_watch",
    "spread_stability_report_pass",
    "no_spread_stability_snapshots",
)

CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "maximum_pass_spread_bps",
    "maximum_watch_spread_bps",
    "maximum_pass_depth_change_ratio",
    "maximum_watch_depth_change_ratio",
    "maximum_pass_snapshot_age_seconds",
    "maximum_watch_snapshot_age_seconds",
    "maximum_pass_fee_pressure_bps",
    "maximum_watch_fee_pressure_bps",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    "public_row_ref",
    "observed_at",
    "best_bid_price",
    "best_ask_price",
    "bid_depth",
    "ask_depth",
    "previous_bid_depth",
    "previous_ask_depth",
    "spread_bps",
    "bid_depth_change_ratio",
    "ask_depth_change_ratio",
    "absolute_bid_depth_change_ratio",
    "absolute_ask_depth_change_ratio",
    "snapshot_age_seconds",
    "fee_pressure_bps",
    "stability_bucket",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config",
    "snapshot_count",
    "pass_count",
    "watch_count",
    "block_count",
    "wide_spread_count",
    "bid_depth_change_count",
    "ask_depth_change_count",
    "stale_snapshot_count",
    "fee_pressure_count",
    "average_spread_bps",
    "average_abs_bid_depth_change_ratio",
    "average_abs_ask_depth_change_ratio",
    "max_spread_bps",
    "max_snapshot_age_seconds",
    "max_fee_pressure_bps",
    "status",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


class _FinalPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError(f"{cls.__bases__[0].__name__} cannot be subclassed")


@dataclass(frozen=True)
class ResearchMarketOrderbookSpreadStabilityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_ORDERBOOK_SPREAD_STABILITY_REPORT_CONFIG_VERSION
    )
    maximum_pass_spread_bps: Decimal = Decimal("100.000000")
    maximum_watch_spread_bps: Decimal = Decimal("500.000000")
    maximum_pass_depth_change_ratio: Decimal = Decimal("0.100000")
    maximum_watch_depth_change_ratio: Decimal = Decimal("0.300000")
    maximum_pass_snapshot_age_seconds: Decimal = Decimal("60.000000")
    maximum_watch_snapshot_age_seconds: Decimal = Decimal("300.000000")
    maximum_pass_fee_pressure_bps: Decimal = Decimal("50.000000")
    maximum_watch_fee_pressure_bps: Decimal = Decimal("150.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookSpreadStabilityConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_ORDERBOOK_SPREAD_STABILITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for label, pass_field_name, watch_field_name in (
            (
                "spread",
                "maximum_pass_spread_bps",
                "maximum_watch_spread_bps",
            ),
            (
                "depth change",
                "maximum_pass_depth_change_ratio",
                "maximum_watch_depth_change_ratio",
            ),
            (
                "snapshot age",
                "maximum_pass_snapshot_age_seconds",
                "maximum_watch_snapshot_age_seconds",
            ),
            (
                "fee pressure",
                "maximum_pass_fee_pressure_bps",
                "maximum_watch_fee_pressure_bps",
            ),
        ):
            _require_threshold_order(
                label,
                _require_raw_decimal(
                    pass_field_name,
                    getattr(self, pass_field_name),
                ),
                _require_raw_decimal(
                    watch_field_name,
                    getattr(self, watch_field_name),
                ),
            )
        for field_name in (
            "maximum_pass_spread_bps",
            "maximum_watch_spread_bps",
            "maximum_pass_depth_change_ratio",
            "maximum_watch_depth_change_ratio",
            "maximum_pass_snapshot_age_seconds",
            "maximum_watch_snapshot_age_seconds",
            "maximum_pass_fee_pressure_bps",
            "maximum_watch_fee_pressure_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookSpreadStabilitySnapshot(_FinalPublicDataclass):
    snapshot_label: str
    observed_at: datetime
    best_bid_price: Decimal
    best_ask_price: Decimal
    bid_depth: Decimal
    ask_depth: Decimal
    previous_bid_depth: Decimal
    previous_ask_depth: Decimal
    fee_pressure_bps: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookSpreadStabilitySnapshot,
            "snapshot",
        )
        _require_public_label("snapshot_label", self.snapshot_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("best_bid_price", "best_ask_price"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_price(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        for field_name in (
            "bid_depth",
            "ask_depth",
            "previous_bid_depth",
            "previous_ask_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fee_pressure_bps",
            _require_nonnegative_decimal("fee_pressure_bps", self.fee_pressure_bps),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookSpreadStabilityRow(_FinalPublicDataclass):
    public_row_ref: str
    observed_at: datetime
    best_bid_price: Decimal
    best_ask_price: Decimal
    bid_depth: Decimal
    ask_depth: Decimal
    previous_bid_depth: Decimal
    previous_ask_depth: Decimal
    spread_bps: Decimal
    bid_depth_change_ratio: Decimal
    ask_depth_change_ratio: Decimal
    absolute_bid_depth_change_ratio: Decimal
    absolute_ask_depth_change_ratio: Decimal
    snapshot_age_seconds: Decimal
    fee_pressure_bps: Decimal
    stability_bucket: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOrderbookSpreadStabilityRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("best_bid_price", "best_ask_price"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_price(field_name, getattr(self, field_name)),
            )
        if self.best_ask_price <= self.best_bid_price:
            raise ValueError("best_ask_price must exceed best_bid_price")
        for field_name in (
            "bid_depth",
            "ask_depth",
            "previous_bid_depth",
            "previous_ask_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_bps",
            "absolute_bid_depth_change_ratio",
            "absolute_ask_depth_change_ratio",
            "snapshot_age_seconds",
            "fee_pressure_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("bid_depth_change_ratio", "ask_depth_change_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_depth_change_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("stability_bucket", self.stability_bucket)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_internal_consistency(self)


@dataclass(frozen=True)
class ResearchMarketOrderbookSpreadStabilityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketOrderbookSpreadStabilityReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketOrderbookSpreadStabilityReport(_FinalPublicDataclass):
    generated_at: datetime
    config: ResearchMarketOrderbookSpreadStabilityConfig
    snapshot_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    wide_spread_count: Decimal
    bid_depth_change_count: Decimal
    ask_depth_change_count: Decimal
    stale_snapshot_count: Decimal
    fee_pressure_count: Decimal
    average_spread_bps: Decimal | None
    average_abs_bid_depth_change_ratio: Decimal | None
    average_abs_ask_depth_change_ratio: Decimal | None
    max_spread_bps: Decimal
    max_snapshot_age_seconds: Decimal
    max_fee_pressure_bps: Decimal
    status: str
    rows: tuple[ResearchMarketOrderbookSpreadStabilityRow, ...]
    reason_code_counts: tuple[
        ResearchMarketOrderbookSpreadStabilityReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketOrderbookSpreadStabilityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        if type(self.config) is not ResearchMarketOrderbookSpreadStabilityConfig:
            raise ValueError(
                "config must be a ResearchMarketOrderbookSpreadStabilityConfig",
            )
        _require_hard_flags("config", self.config)
        for field_name in (
            "snapshot_count",
            "pass_count",
            "watch_count",
            "block_count",
            "wide_spread_count",
            "bid_depth_change_count",
            "ask_depth_change_count",
            "stale_snapshot_count",
            "fee_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_spread_bps",
            "average_abs_bid_depth_change_ratio",
            "average_abs_ask_depth_change_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "max_spread_bps",
            "max_snapshot_age_seconds",
            "max_fee_pressure_bps",
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
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_orderbook_spread_stability_report(
    snapshots: Iterable[object],
    *,
    config: ResearchMarketOrderbookSpreadStabilityConfig,
    generated_at: datetime,
) -> ResearchMarketOrderbookSpreadStabilityReport:
    if type(config) is not ResearchMarketOrderbookSpreadStabilityConfig:
        raise ValueError(
            "config must be a ResearchMarketOrderbookSpreadStabilityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    for item in normalized_snapshots:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    ordered_snapshots = tuple(
        sorted(normalized_snapshots, key=lambda item: item.snapshot_label),
    )
    rows = tuple(
        _row_from_snapshot(
            item,
            public_row_ref=_canonical_public_row_ref(index),
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(ordered_snapshots, start=1)
    )
    return ResearchMarketOrderbookSpreadStabilityReport(
        generated_at=generated_at_utc,
        config=config,
        snapshot_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        wide_spread_count=_component_nonpass_count(rows, "spread_bps"),
        bid_depth_change_count=_component_nonpass_count(rows, "bid_depth_change"),
        ask_depth_change_count=_component_nonpass_count(rows, "ask_depth_change"),
        stale_snapshot_count=_component_nonpass_count(rows, "snapshot_age"),
        fee_pressure_count=_component_nonpass_count(rows, "fee_pressure"),
        average_spread_bps=_optional_average(rows, "spread_bps"),
        average_abs_bid_depth_change_ratio=_optional_average(
            rows,
            "absolute_bid_depth_change_ratio",
        ),
        average_abs_ask_depth_change_ratio=_optional_average(
            rows,
            "absolute_ask_depth_change_ratio",
        ),
        max_spread_bps=_maximum(rows, "spread_bps"),
        max_snapshot_age_seconds=_maximum(rows, "snapshot_age_seconds"),
        max_fee_pressure_bps=_maximum(rows, "fee_pressure_bps"),
        status=_report_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows),
    )


def research_market_orderbook_spread_stability_report_payload(
    report: ResearchMarketOrderbookSpreadStabilityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketOrderbookSpreadStabilityReport:
        raise ValueError(
            "report must be a ResearchMarketOrderbookSpreadStabilityReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_market_orderbook_spread_stability_report_payload(payload)
    return payload


def research_market_orderbook_spread_stability_report_digest(
    report: ResearchMarketOrderbookSpreadStabilityReport,
) -> str:
    if type(report) is not ResearchMarketOrderbookSpreadStabilityReport:
        raise ValueError(
            "report must be a ResearchMarketOrderbookSpreadStabilityReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def validate_research_market_orderbook_spread_stability_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_exact_keys("payload", payload, REPORT_PAYLOAD_FIELDS)
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values("payload", payload)
    provided_digest = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _public_payload_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    reconstructed = _report_from_public_payload(payload)
    canonical_payload = _payload_value(reconstructed)
    if canonical_payload != payload:
        raise ValueError("payload must use canonical public serialization")
    return True


def _row_from_snapshot(
    item: ResearchMarketOrderbookSpreadStabilitySnapshot,
    *,
    public_row_ref: str,
    config: ResearchMarketOrderbookSpreadStabilityConfig,
    generated_at: datetime,
) -> ResearchMarketOrderbookSpreadStabilityRow:
    spread_bps = _spread_bps(item.best_bid_price, item.best_ask_price)
    bid_depth_change_ratio = _depth_change_ratio(
        item.bid_depth,
        item.previous_bid_depth,
    )
    ask_depth_change_ratio = _depth_change_ratio(
        item.ask_depth,
        item.previous_ask_depth,
    )
    absolute_bid_depth_change_ratio = bid_depth_change_ratio.copy_abs()
    absolute_ask_depth_change_ratio = ask_depth_change_ratio.copy_abs()
    snapshot_age_seconds = _age_seconds(generated_at, item.observed_at)
    component_statuses = _component_statuses(
        spread_bps=spread_bps,
        absolute_bid_depth_change_ratio=absolute_bid_depth_change_ratio,
        absolute_ask_depth_change_ratio=absolute_ask_depth_change_ratio,
        snapshot_age_seconds=snapshot_age_seconds,
        fee_pressure_bps=item.fee_pressure_bps,
        config=config,
    )
    stability_bucket = _worst_status(tuple(component_statuses.values()))
    return ResearchMarketOrderbookSpreadStabilityRow(
        public_row_ref=public_row_ref,
        observed_at=item.observed_at,
        best_bid_price=item.best_bid_price,
        best_ask_price=item.best_ask_price,
        bid_depth=item.bid_depth,
        ask_depth=item.ask_depth,
        previous_bid_depth=item.previous_bid_depth,
        previous_ask_depth=item.previous_ask_depth,
        spread_bps=spread_bps,
        bid_depth_change_ratio=bid_depth_change_ratio,
        ask_depth_change_ratio=ask_depth_change_ratio,
        absolute_bid_depth_change_ratio=_quantize(
            absolute_bid_depth_change_ratio,
        ),
        absolute_ask_depth_change_ratio=_quantize(
            absolute_ask_depth_change_ratio,
        ),
        snapshot_age_seconds=snapshot_age_seconds,
        fee_pressure_bps=item.fee_pressure_bps,
        stability_bucket=stability_bucket,
        reason_codes=_row_reason_codes(
            stability_bucket=stability_bucket,
            component_statuses=component_statuses,
            input_reason_codes=item.reason_codes,
        ),
    )


def _spread_bps(best_bid_price: Decimal, best_ask_price: Decimal) -> Decimal:
    with localcontext(_decimal_context()):
        midpoint = (best_bid_price + best_ask_price) / TWO
        return _quantize((best_ask_price - best_bid_price) / midpoint * BASIS_POINTS)


def _depth_change_ratio(current_depth: Decimal, previous_depth: Decimal) -> Decimal:
    with localcontext(_decimal_context()):
        return _quantize((current_depth - previous_depth) / previous_depth)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    with localcontext(_decimal_context()):
        whole_seconds = Decimal(delta.days * SECONDS_PER_DAY + delta.seconds)
        fractional_seconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        return _quantize(whole_seconds + fractional_seconds)


def _component_statuses(
    *,
    spread_bps: Decimal,
    absolute_bid_depth_change_ratio: Decimal,
    absolute_ask_depth_change_ratio: Decimal,
    snapshot_age_seconds: Decimal,
    fee_pressure_bps: Decimal,
    config: ResearchMarketOrderbookSpreadStabilityConfig,
) -> dict[str, str]:
    return {
        "spread_bps": _status_for_maximum(
            spread_bps,
            config.maximum_pass_spread_bps,
            config.maximum_watch_spread_bps,
        ),
        "bid_depth_change": _status_for_maximum(
            absolute_bid_depth_change_ratio,
            config.maximum_pass_depth_change_ratio,
            config.maximum_watch_depth_change_ratio,
        ),
        "ask_depth_change": _status_for_maximum(
            absolute_ask_depth_change_ratio,
            config.maximum_pass_depth_change_ratio,
            config.maximum_watch_depth_change_ratio,
        ),
        "snapshot_age": _status_for_maximum(
            snapshot_age_seconds,
            config.maximum_pass_snapshot_age_seconds,
            config.maximum_watch_snapshot_age_seconds,
        ),
        "fee_pressure": _status_for_maximum(
            fee_pressure_bps,
            config.maximum_pass_fee_pressure_bps,
            config.maximum_watch_fee_pressure_bps,
        ),
    }


def _status_for_maximum(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value > watch_threshold:
        return "block"
    if value > pass_threshold:
        return "watch"
    return "pass"


def _worst_status(statuses: tuple[str, ...]) -> str:
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    stability_bucket: str,
    component_statuses: dict[str, str],
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    return (
        f"spread_stability_{stability_bucket}",
        *(f"{prefix}_{component_statuses[prefix]}" for prefix in COMPONENT_PREFIXES),
        *(f"input_{reason_code}" for reason_code in input_reason_codes),
    )


def _report_status(
    rows: tuple[ResearchMarketOrderbookSpreadStabilityRow, ...],
) -> str:
    if not rows:
        return "block"
    return _worst_status(tuple(row.stability_bucket for row in rows))


def _report_reason_codes(
    rows: tuple[ResearchMarketOrderbookSpreadStabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_spread_stability_snapshots",)
    status = _report_status(rows)
    if status == "pass":
        return ("spread_stability_report_pass",)
    present = {code for row in rows for code in row.reason_codes}
    codes = {f"spread_stability_report_{status}"}
    for prefix in COMPONENT_PREFIXES:
        for component_status in ("block", "watch"):
            code = f"{prefix}_{component_status}"
            if code in present:
                codes.add(code)
    return tuple(code for code in REPORT_REASON_CODE_ORDER if code in codes)


def _reason_code_counts(
    rows: tuple[ResearchMarketOrderbookSpreadStabilityRow, ...],
) -> tuple[ResearchMarketOrderbookSpreadStabilityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketOrderbookSpreadStabilityReasonCodeCount(
                reason_code="no_spread_stability_snapshots",
                count=Decimal("1"),
                row_ratio=ZERO,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    with localcontext(_decimal_context()):
        row_count = Decimal(len(rows))
        return tuple(
            ResearchMarketOrderbookSpreadStabilityReasonCodeCount(
                reason_code=reason_code,
                count=_count(count),
                row_ratio=_quantize(Decimal(count) / row_count),
            )
            for reason_code, count in sorted(counts.items())
        )


def _status_count(
    rows: tuple[ResearchMarketOrderbookSpreadStabilityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.stability_bucket == status))


def _component_nonpass_count(
    rows: tuple[ResearchMarketOrderbookSpreadStabilityRow, ...],
    prefix: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if f"{prefix}_watch" in row.reason_codes
            or f"{prefix}_block" in row.reason_codes
        ),
    )


def _optional_average(
    rows: tuple[ResearchMarketOrderbookSpreadStabilityRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(_decimal_context()):
        return _quantize(
            sum((getattr(row, field_name) for row in rows), ZERO)
            / Decimal(len(rows)),
        )


def _maximum(
    rows: tuple[ResearchMarketOrderbookSpreadStabilityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _normalize_snapshots(
    snapshots: Iterable[object],
) -> tuple[ResearchMarketOrderbookSpreadStabilitySnapshot, ...]:
    if isinstance(snapshots, (str, bytes)):
        raise ValueError("snapshots must be an iterable")
    try:
        values = tuple(snapshots)
    except TypeError as exc:
        raise ValueError("snapshots must be an iterable") from exc
    seen_labels: set[str] = set()
    for value in values:
        if type(value) is not ResearchMarketOrderbookSpreadStabilitySnapshot:
            raise ValueError(
                "snapshots must contain "
                "ResearchMarketOrderbookSpreadStabilitySnapshot values",
            )
        _require_hard_flags("snapshot", value)
        if value.snapshot_label in seen_labels:
            raise ValueError("snapshot_label values must be unique")
        seen_labels.add(value.snapshot_label)
    return values


def _normalize_rows(
    value: object,
) -> tuple[ResearchMarketOrderbookSpreadStabilityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchMarketOrderbookSpreadStabilityRow:
            raise ValueError(
                "rows must contain ResearchMarketOrderbookSpreadStabilityRow values",
            )
        _require_hard_flags("row", row)
        _validate_row_internal_consistency(row)
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchMarketOrderbookSpreadStabilityReasonCodeCount, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_code_counts must be a nonempty tuple")
    for item in value:
        if type(item) is not ResearchMarketOrderbookSpreadStabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketOrderbookSpreadStabilityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
    if value != tuple(sorted(value, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return value


def _normalize_input_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        if reason_code.startswith("input_") or any(
            reason_code.startswith(f"{prefix}_")
            for prefix in ("spread_stability", *COMPONENT_PREFIXES)
        ):
            raise ValueError(f"{field_name} contains a reserved reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(reason_code)
        seen.add(reason_code)
    return tuple(sorted(normalized))


def _normalize_row_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        if reason_code not in ROW_BASE_REASON_CODES:
            if not reason_code.startswith("input_"):
                raise ValueError(f"{field_name} contains an unknown reason code")
            _normalize_input_reason_codes(
                field_name,
                (reason_code.removeprefix("input_"),),
            )
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(reason_code)
        seen.add(reason_code)
    canonical_base_codes = tuple(
        code
        for prefix in ("spread_stability", *COMPONENT_PREFIXES)
        for status in ORDERBOOK_SPREAD_STABILITY_STATUSES
        if (code := f"{prefix}_{status}") in seen
    )
    canonical_input_codes = tuple(
        sorted(code for code in seen if code.startswith("input_")),
    )
    expected = canonical_base_codes + canonical_input_codes
    if tuple(normalized) != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return expected


def _normalize_report_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
        if reason_code not in REPORT_REASON_CODE_ORDER:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(code for code in REPORT_REASON_CODE_ORDER if code in seen)
    if value != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return value


def _validate_row_internal_consistency(
    row: ResearchMarketOrderbookSpreadStabilityRow,
) -> None:
    if row.spread_bps != _spread_bps(row.best_bid_price, row.best_ask_price):
        raise ValueError("spread_bps must match bid and ask prices")
    expected_bid_change = _depth_change_ratio(row.bid_depth, row.previous_bid_depth)
    if row.bid_depth_change_ratio != expected_bid_change:
        raise ValueError("bid_depth_change_ratio must match bid depths")
    expected_ask_change = _depth_change_ratio(row.ask_depth, row.previous_ask_depth)
    if row.ask_depth_change_ratio != expected_ask_change:
        raise ValueError("ask_depth_change_ratio must match ask depths")
    if row.absolute_bid_depth_change_ratio != _quantize(
        expected_bid_change.copy_abs(),
    ):
        raise ValueError(
            "absolute_bid_depth_change_ratio must match bid_depth_change_ratio",
        )
    if row.absolute_ask_depth_change_ratio != _quantize(
        expected_ask_change.copy_abs(),
    ):
        raise ValueError(
            "absolute_ask_depth_change_ratio must match ask_depth_change_ratio",
        )
    if f"spread_stability_{row.stability_bucket}" not in row.reason_codes:
        raise ValueError("stability_bucket must match reason_codes")
    for prefix in COMPONENT_PREFIXES:
        matching = tuple(
            code
            for code in row.reason_codes
            if code in tuple(
                f"{prefix}_{status}" for status in ORDERBOOK_SPREAD_STABILITY_STATUSES
            )
        )
        if len(matching) != 1:
            raise ValueError(f"reason_codes must contain one {prefix} status")


def _validate_row_semantics(
    row: ResearchMarketOrderbookSpreadStabilityRow,
    *,
    config: ResearchMarketOrderbookSpreadStabilityConfig,
    generated_at: datetime,
) -> None:
    if row.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    expected_age = _age_seconds(generated_at, row.observed_at)
    if row.snapshot_age_seconds != expected_age:
        raise ValueError("snapshot_age_seconds must match observation age")
    component_statuses = _component_statuses(
        spread_bps=row.spread_bps,
        absolute_bid_depth_change_ratio=row.absolute_bid_depth_change_ratio,
        absolute_ask_depth_change_ratio=row.absolute_ask_depth_change_ratio,
        snapshot_age_seconds=row.snapshot_age_seconds,
        fee_pressure_bps=row.fee_pressure_bps,
        config=config,
    )
    expected_bucket = _worst_status(tuple(component_statuses.values()))
    if row.stability_bucket != expected_bucket:
        raise ValueError("stability_bucket must match derived metrics")
    input_reason_codes = tuple(
        reason_code.removeprefix("input_")
        for reason_code in row.reason_codes
        if reason_code.startswith("input_")
    )
    expected_reasons = _row_reason_codes(
        stability_bucket=expected_bucket,
        component_statuses=component_statuses,
        input_reason_codes=_normalize_input_reason_codes(
            "reason_codes",
            input_reason_codes,
        ),
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match derived stability logic")


def _validate_report_consistency(
    report: ResearchMarketOrderbookSpreadStabilityReport,
) -> None:
    expected_row_refs = tuple(
        _canonical_public_row_ref(index)
        for index in range(1, len(report.rows) + 1)
    )
    if tuple(row.public_row_ref for row in report.rows) != expected_row_refs:
        raise ValueError("public_row_ref values must use canonical sequential order")
    for row in report.rows:
        _validate_row_semantics(
            row,
            config=report.config,
            generated_at=report.generated_at,
        )
    expected_pairs: dict[str, object] = {
        "snapshot_count": _count(len(report.rows)),
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "block_count": _status_count(report.rows, "block"),
        "wide_spread_count": _component_nonpass_count(report.rows, "spread_bps"),
        "bid_depth_change_count": _component_nonpass_count(
            report.rows,
            "bid_depth_change",
        ),
        "ask_depth_change_count": _component_nonpass_count(
            report.rows,
            "ask_depth_change",
        ),
        "stale_snapshot_count": _component_nonpass_count(
            report.rows,
            "snapshot_age",
        ),
        "fee_pressure_count": _component_nonpass_count(
            report.rows,
            "fee_pressure",
        ),
        "average_spread_bps": _optional_average(report.rows, "spread_bps"),
        "average_abs_bid_depth_change_ratio": _optional_average(
            report.rows,
            "absolute_bid_depth_change_ratio",
        ),
        "average_abs_ask_depth_change_ratio": _optional_average(
            report.rows,
            "absolute_ask_depth_change_ratio",
        ),
        "max_spread_bps": _maximum(report.rows, "spread_bps"),
        "max_snapshot_age_seconds": _maximum(
            report.rows,
            "snapshot_age_seconds",
        ),
        "max_fee_pressure_bps": _maximum(report.rows, "fee_pressure_bps"),
        "status": _report_status(report.rows),
        "reason_code_counts": _reason_code_counts(report.rows),
        "reason_codes": _report_reason_codes(report.rows),
    }
    for field_name, expected_value in expected_pairs.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")


def _derived_report_digest(
    report: ResearchMarketOrderbookSpreadStabilityReport,
) -> str:
    payload = _payload_value(report, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _public_payload_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _payload_value(value: object, *, include_digest: bool = True) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, Any] = {}
        for field in fields(value):
            if field.name == "derived_validation_digest" and not include_digest:
                continue
            result[field.name] = _payload_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return result
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is tuple:
        return [
            _payload_value(item, include_digest=include_digest)
            for item in value
        ]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchMarketOrderbookSpreadStabilityReport:
    config = _config_from_public_payload(_payload_required_dict(payload, "config"))
    rows_payload = _payload_required_list(payload, "rows")
    rows = tuple(
        _row_from_public_payload(item, index=index)
        for index, item in enumerate(rows_payload)
    )
    counts_payload = _payload_required_list(payload, "reason_code_counts")
    reason_code_counts = tuple(
        _reason_count_from_public_payload(item, index=index)
        for index, item in enumerate(counts_payload)
    )
    return ResearchMarketOrderbookSpreadStabilityReport(
        generated_at=_payload_datetime(payload, "generated_at"),
        config=config,
        snapshot_count=_payload_decimal(payload, "snapshot_count"),
        pass_count=_payload_decimal(payload, "pass_count"),
        watch_count=_payload_decimal(payload, "watch_count"),
        block_count=_payload_decimal(payload, "block_count"),
        wide_spread_count=_payload_decimal(payload, "wide_spread_count"),
        bid_depth_change_count=_payload_decimal(payload, "bid_depth_change_count"),
        ask_depth_change_count=_payload_decimal(payload, "ask_depth_change_count"),
        stale_snapshot_count=_payload_decimal(payload, "stale_snapshot_count"),
        fee_pressure_count=_payload_decimal(payload, "fee_pressure_count"),
        average_spread_bps=_payload_optional_decimal(
            payload,
            "average_spread_bps",
        ),
        average_abs_bid_depth_change_ratio=_payload_optional_decimal(
            payload,
            "average_abs_bid_depth_change_ratio",
        ),
        average_abs_ask_depth_change_ratio=_payload_optional_decimal(
            payload,
            "average_abs_ask_depth_change_ratio",
        ),
        max_spread_bps=_payload_decimal(payload, "max_spread_bps"),
        max_snapshot_age_seconds=_payload_decimal(
            payload,
            "max_snapshot_age_seconds",
        ),
        max_fee_pressure_bps=_payload_decimal(payload, "max_fee_pressure_bps"),
        status=_payload_required_string(payload, "status"),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_payload_string_tuple(payload, "reason_codes"),
        paper_only=_payload_bool(payload, "paper_only"),
        report_only=_payload_bool(payload, "report_only"),
        readonly=_payload_bool(payload, "readonly"),
    )


def _config_from_public_payload(
    payload: dict[str, Any],
) -> ResearchMarketOrderbookSpreadStabilityConfig:
    _require_exact_keys("config", payload, CONFIG_PAYLOAD_FIELDS)
    return ResearchMarketOrderbookSpreadStabilityConfig(
        config_version=_payload_required_string(payload, "config_version"),
        maximum_pass_spread_bps=_payload_decimal(
            payload,
            "maximum_pass_spread_bps",
        ),
        maximum_watch_spread_bps=_payload_decimal(
            payload,
            "maximum_watch_spread_bps",
        ),
        maximum_pass_depth_change_ratio=_payload_decimal(
            payload,
            "maximum_pass_depth_change_ratio",
        ),
        maximum_watch_depth_change_ratio=_payload_decimal(
            payload,
            "maximum_watch_depth_change_ratio",
        ),
        maximum_pass_snapshot_age_seconds=_payload_decimal(
            payload,
            "maximum_pass_snapshot_age_seconds",
        ),
        maximum_watch_snapshot_age_seconds=_payload_decimal(
            payload,
            "maximum_watch_snapshot_age_seconds",
        ),
        maximum_pass_fee_pressure_bps=_payload_decimal(
            payload,
            "maximum_pass_fee_pressure_bps",
        ),
        maximum_watch_fee_pressure_bps=_payload_decimal(
            payload,
            "maximum_watch_fee_pressure_bps",
        ),
        paper_only=_payload_bool(payload, "paper_only"),
        report_only=_payload_bool(payload, "report_only"),
        readonly=_payload_bool(payload, "readonly"),
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchMarketOrderbookSpreadStabilityRow:
    if type(value) is not dict:
        raise ValueError(f"rows[{index}] must be a JSON object")
    _require_exact_keys(f"rows[{index}]", value, ROW_PAYLOAD_FIELDS)
    return ResearchMarketOrderbookSpreadStabilityRow(
        public_row_ref=_payload_required_string(value, "public_row_ref"),
        observed_at=_payload_datetime(value, "observed_at"),
        best_bid_price=_payload_decimal(value, "best_bid_price"),
        best_ask_price=_payload_decimal(value, "best_ask_price"),
        bid_depth=_payload_decimal(value, "bid_depth"),
        ask_depth=_payload_decimal(value, "ask_depth"),
        previous_bid_depth=_payload_decimal(value, "previous_bid_depth"),
        previous_ask_depth=_payload_decimal(value, "previous_ask_depth"),
        spread_bps=_payload_decimal(value, "spread_bps"),
        bid_depth_change_ratio=_payload_decimal(value, "bid_depth_change_ratio"),
        ask_depth_change_ratio=_payload_decimal(value, "ask_depth_change_ratio"),
        absolute_bid_depth_change_ratio=_payload_decimal(
            value,
            "absolute_bid_depth_change_ratio",
        ),
        absolute_ask_depth_change_ratio=_payload_decimal(
            value,
            "absolute_ask_depth_change_ratio",
        ),
        snapshot_age_seconds=_payload_decimal(value, "snapshot_age_seconds"),
        fee_pressure_bps=_payload_decimal(value, "fee_pressure_bps"),
        stability_bucket=_payload_required_string(value, "stability_bucket"),
        reason_codes=_payload_string_tuple(value, "reason_codes"),
        paper_only=_payload_bool(value, "paper_only"),
        report_only=_payload_bool(value, "report_only"),
        readonly=_payload_bool(value, "readonly"),
    )


def _reason_count_from_public_payload(
    value: object,
    *,
    index: int,
) -> ResearchMarketOrderbookSpreadStabilityReasonCodeCount:
    if type(value) is not dict:
        raise ValueError(f"reason_code_counts[{index}] must be a JSON object")
    _require_exact_keys(
        f"reason_code_counts[{index}]",
        value,
        REASON_COUNT_PAYLOAD_FIELDS,
    )
    return ResearchMarketOrderbookSpreadStabilityReasonCodeCount(
        reason_code=_payload_required_string(value, "reason_code"),
        count=_payload_decimal(value, "count"),
        row_ratio=_payload_decimal(value, "row_ratio"),
        paper_only=_payload_bool(value, "paper_only"),
        report_only=_payload_bool(value, "report_only"),
        readonly=_payload_bool(value, "readonly"),
    )


def _require_exact_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(payload) != expected_keys:
        raise ValueError(f"{label} must contain exactly the canonical fields")


def _payload_required_dict(
    payload: dict[str, Any],
    field_name: str,
) -> dict[str, Any]:
    value = payload.get(field_name)
    if type(value) is not dict:
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def _payload_required_list(
    payload: dict[str, Any],
    field_name: str,
) -> list[Any]:
    value = payload.get(field_name)
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _payload_required_string(
    payload: dict[str, Any],
    field_name: str,
) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_decimal(
    payload: dict[str, Any],
    field_name: str,
) -> Decimal:
    value = _payload_required_string(payload, field_name)
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return decimal_value


def _payload_optional_decimal(
    payload: dict[str, Any],
    field_name: str,
) -> Decimal | None:
    if payload.get(field_name) is None:
        return None
    return _payload_decimal(payload, field_name)


def _payload_datetime(
    payload: dict[str, Any],
    field_name: str,
) -> datetime:
    value = _payload_required_string(payload, field_name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime") from exc
    return _as_utc(field_name, parsed)


def _payload_bool(
    payload: dict[str, Any],
    field_name: str,
) -> bool:
    value = payload.get(field_name)
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _payload_string_tuple(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    values = _payload_required_list(payload, field_name)
    if any(type(value) is not str for value in values):
        raise ValueError(f"{field_name} must contain strings")
    return tuple(values)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_threshold_order(
    label: str,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if pass_threshold > watch_threshold:
        raise ValueError(f"{label} pass threshold must not exceed watch threshold")


def _require_probability_price(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if raw > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    normalized = _quantize(raw, field_name=field_name)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize(raw, field_name=field_name)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw, field_name=field_name)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_depth_change_ratio(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < -ONE:
        raise ValueError(f"{field_name} must not be less than -1")
    return _quantize(raw, field_name=field_name)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO or raw > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(raw, field_name=field_name)


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < ZERO_COUNT or raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return _quantize_count(raw, field_name=field_name)


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count(value: int) -> Decimal:
    return _quantize_count(Decimal(value))


def _quantize(
    value: Decimal,
    *,
    field_name: str = "decimal value",
) -> Decimal:
    try:
        with localcontext(_decimal_context()):
            normalized = value.quantize(METRIC_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} exceeds supported precision") from exc
    if normalized.is_zero():
        return ZERO
    return normalized


def _quantize_count(
    value: Decimal,
    *,
    field_name: str = "count",
) -> Decimal:
    try:
        with localcontext(_decimal_context()):
            normalized = value.quantize(COUNT_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} exceeds supported precision") from exc
    if normalized.is_zero():
        return ZERO_COUNT
    return normalized


def _decimal_context() -> Context:
    return Context(prec=DECIMAL_PRECISION, rounding=ROUND_HALF_EVEN)


def _canonical_public_row_ref(index: int) -> str:
    return f"spread_stability_snapshot_{index:03d}"


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ORDERBOOK_SPREAD_STABILITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public label")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or REASON_CODE_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    _reject_unsafe_public_text(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase SHA-256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_public_numeric_values(label: str, value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{label} must serialize numeric values as strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(label, item)
    elif type(value) is list:
        for item in value:
            _reject_public_numeric_values(label, item)
