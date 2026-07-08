"""Public report-only cost-curve input sufficiency report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Mapping, Sequence


DEFAULT_MARKET_COST_CURVE_SUFFICIENCY_CONFIG_VERSION = (
    "research-market-cost-curve-sufficiency-report-v1"
)
STATUSES = ("pass", "watch", "block")

_STATUSES = frozenset(STATUSES)
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_TERMS = (
    "auth",
    "condition_id",
    "database",
    "execution",
    "live",
    "market_id",
    "market_slug",
    "network",
    "order",
    "private",
    "private_key",
    "secret",
    "signature",
    "signed",
    "source_id",
    "token_id",
    "trade",
    "wallet",
)
_REASON_CODE_SEQUENCE = (
    "spread_watch",
    "spread_block",
    "taker_fee_watch",
    "taker_fee_block",
    "depth_slope_watch",
    "depth_slope_block",
    "deposit_friction_watch",
    "deposit_friction_block",
    "settlement_friction_watch",
    "settlement_friction_block",
    "gas_friction_watch",
    "gas_friction_block",
    "liquidity_concentration_watch",
    "liquidity_concentration_block",
    "cost_curve_sufficiency_pass",
    "cost_curve_sufficiency_empty",
)


@dataclass(frozen=True)
class MarketCostCurveSufficiencyConfig:
    config_version: str = DEFAULT_MARKET_COST_CURVE_SUFFICIENCY_CONFIG_VERSION
    spread_watch_pct: Decimal = Decimal("0.050000")
    spread_block_pct: Decimal = Decimal("0.100000")
    taker_fee_watch_pct: Decimal = Decimal("0.030000")
    taker_fee_block_pct: Decimal = Decimal("0.060000")
    depth_slope_watch_pct_per_100: Decimal = Decimal("0.080000")
    depth_slope_block_pct_per_100: Decimal = Decimal("0.150000")
    deposit_friction_watch_pct: Decimal = Decimal("0.015000")
    deposit_friction_block_pct: Decimal = Decimal("0.030000")
    settlement_friction_watch_pct: Decimal = Decimal("0.015000")
    settlement_friction_block_pct: Decimal = Decimal("0.030000")
    gas_friction_watch_pct: Decimal = Decimal("0.015000")
    gas_friction_block_pct: Decimal = Decimal("0.030000")
    liquidity_concentration_watch_share: Decimal = Decimal("0.650000")
    liquidity_concentration_block_share: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("MarketCostCurveSufficiencyConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketCostCurveSufficiencyConfig:
            raise ValueError("config must be exactly MarketCostCurveSufficiencyConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_COST_CURVE_SUFFICIENCY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "spread_watch_pct",
            "spread_block_pct",
            "taker_fee_watch_pct",
            "taker_fee_block_pct",
            "depth_slope_watch_pct_per_100",
            "depth_slope_block_pct_per_100",
            "deposit_friction_watch_pct",
            "deposit_friction_block_pct",
            "settlement_friction_watch_pct",
            "settlement_friction_block_pct",
            "gas_friction_watch_pct",
            "gas_friction_block_pct",
            "liquidity_concentration_watch_share",
            "liquidity_concentration_block_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.spread_block_pct <= self.spread_watch_pct:
            raise ValueError("spread_block_pct must exceed spread_watch_pct")
        if self.taker_fee_block_pct <= self.taker_fee_watch_pct:
            raise ValueError("taker_fee_block_pct must exceed taker_fee_watch_pct")
        if self.depth_slope_block_pct_per_100 <= self.depth_slope_watch_pct_per_100:
            raise ValueError(
                "depth_slope_block_pct_per_100 must exceed "
                "depth_slope_watch_pct_per_100",
            )
        if self.deposit_friction_block_pct <= self.deposit_friction_watch_pct:
            raise ValueError(
                "deposit_friction_block_pct must exceed deposit_friction_watch_pct",
            )
        if self.settlement_friction_block_pct <= self.settlement_friction_watch_pct:
            raise ValueError(
                "settlement_friction_block_pct must exceed "
                "settlement_friction_watch_pct",
            )
        if self.gas_friction_block_pct <= self.gas_friction_watch_pct:
            raise ValueError("gas_friction_block_pct must exceed gas_friction_watch_pct")
        if (
            self.liquidity_concentration_block_share
            <= self.liquidity_concentration_watch_share
        ):
            raise ValueError(
                "liquidity_concentration_block_share must exceed "
                "liquidity_concentration_watch_share",
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class MarketCostCurveSufficiencyInput:
    research_case_key: str
    observed_at: datetime
    spread_pct: Decimal
    taker_fee_pct: Decimal
    depth_slope_pct_per_100: Decimal
    deposit_friction_pct: Decimal
    settlement_friction_pct: Decimal
    gas_friction_pct: Decimal
    top_liquidity_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("MarketCostCurveSufficiencyInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketCostCurveSufficiencyInput:
            raise ValueError("input must be exactly MarketCostCurveSufficiencyInput")
        _require_public_identifier("research_case_key", self.research_case_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_pct",
            "taker_fee_pct",
            "depth_slope_pct_per_100",
            "deposit_friction_pct",
            "settlement_friction_pct",
            "gas_friction_pct",
            "top_liquidity_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class MarketCostCurveSufficiencyRow:
    research_case_key: str
    observed_at: datetime
    spread_pct: Decimal
    taker_fee_pct: Decimal
    depth_slope_pct_per_100: Decimal
    deposit_friction_pct: Decimal
    settlement_friction_pct: Decimal
    gas_friction_pct: Decimal
    top_liquidity_share: Decimal
    total_friction_pct: Decimal
    sufficiency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("MarketCostCurveSufficiencyRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketCostCurveSufficiencyRow:
            raise ValueError("row must be exactly MarketCostCurveSufficiencyRow")
        _require_public_identifier("research_case_key", self.research_case_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "spread_pct",
            "taker_fee_pct",
            "depth_slope_pct_per_100",
            "deposit_friction_pct",
            "settlement_friction_pct",
            "gas_friction_pct",
            "top_liquidity_share",
            "total_friction_pct",
            "sufficiency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class MarketCostCurveSufficiencyReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketCostCurveSufficiencyReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class MarketCostCurveSufficiencyReport:
    generated_at: datetime
    config_version: str
    report_status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_sufficiency_score: Decimal
    max_spread_pct: Decimal
    max_taker_fee_pct: Decimal
    max_depth_slope_pct_per_100: Decimal
    max_deposit_friction_pct: Decimal
    max_settlement_friction_pct: Decimal
    max_gas_friction_pct: Decimal
    max_total_friction_pct: Decimal
    max_top_liquidity_share: Decimal
    rows: tuple[MarketCostCurveSufficiencyRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketCostCurveSufficiencyReasonCodeCount, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("MarketCostCurveSufficiencyReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not MarketCostCurveSufficiencyReport:
            raise ValueError("report must be exactly MarketCostCurveSufficiencyReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_MARKET_COST_CURVE_SUFFICIENCY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_sufficiency_score",
            "max_spread_pct",
            "max_taker_fee_pct",
            "max_depth_slope_pct_per_100",
            "max_deposit_friction_pct",
            "max_settlement_friction_pct",
            "max_gas_friction_pct",
            "max_total_friction_pct",
            "max_top_liquidity_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return market_cost_curve_sufficiency_report_payload(self)


def build_market_cost_curve_sufficiency_report(
    rows: Sequence[MarketCostCurveSufficiencyInput],
    *,
    generated_at: datetime,
    config: MarketCostCurveSufficiencyConfig | None = None,
) -> MarketCostCurveSufficiencyReport:
    """Build a deterministic paper-review sufficiency report."""

    if config is None:
        config = MarketCostCurveSufficiencyConfig()
    if type(config) is not MarketCostCurveSufficiencyConfig:
        raise ValueError("config must be a MarketCostCurveSufficiencyConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(rows)
    for item in normalized_inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    report_rows = tuple(_row_for_input(item, config) for item in normalized_inputs)
    reason_codes = _report_reason_codes(report_rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(report_rows),
        "input_count": _decimal_count(len(report_rows)),
        "pass_count": _decimal_count(_status_count(report_rows, "pass")),
        "watch_count": _decimal_count(_status_count(report_rows, "watch")),
        "block_count": _decimal_count(_status_count(report_rows, "block")),
        "average_sufficiency_score": _average(
            tuple(row.sufficiency_score for row in report_rows),
        ),
        "max_spread_pct": max((row.spread_pct for row in report_rows), default=_ZERO),
        "max_taker_fee_pct": max(
            (row.taker_fee_pct for row in report_rows),
            default=_ZERO,
        ),
        "max_depth_slope_pct_per_100": max(
            (row.depth_slope_pct_per_100 for row in report_rows),
            default=_ZERO,
        ),
        "max_deposit_friction_pct": max(
            (row.deposit_friction_pct for row in report_rows),
            default=_ZERO,
        ),
        "max_settlement_friction_pct": max(
            (row.settlement_friction_pct for row in report_rows),
            default=_ZERO,
        ),
        "max_gas_friction_pct": max(
            (row.gas_friction_pct for row in report_rows),
            default=_ZERO,
        ),
        "max_total_friction_pct": max(
            (row.total_friction_pct for row in report_rows),
            default=_ZERO,
        ),
        "max_top_liquidity_share": max(
            (row.top_liquidity_share for row in report_rows),
            default=_ZERO,
        ),
        "rows": report_rows,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(reason_codes, report_rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return MarketCostCurveSufficiencyReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def market_cost_curve_sufficiency_report_payload(
    report: MarketCostCurveSufficiencyReport,
) -> dict[str, object]:
    if type(report) is not MarketCostCurveSufficiencyReport:
        raise ValueError("report must be a MarketCostCurveSufficiencyReport")
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_payload("payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_for_input(
    item: MarketCostCurveSufficiencyInput,
    config: MarketCostCurveSufficiencyConfig,
) -> MarketCostCurveSufficiencyRow:
    reason_codes = _row_reason_codes(item, config)
    return MarketCostCurveSufficiencyRow(
        research_case_key=item.research_case_key,
        observed_at=item.observed_at,
        spread_pct=item.spread_pct,
        taker_fee_pct=item.taker_fee_pct,
        depth_slope_pct_per_100=item.depth_slope_pct_per_100,
        deposit_friction_pct=item.deposit_friction_pct,
        settlement_friction_pct=item.settlement_friction_pct,
        gas_friction_pct=item.gas_friction_pct,
        top_liquidity_share=item.top_liquidity_share,
        total_friction_pct=_total_friction_pct(item),
        sufficiency_score=_sufficiency_score(reason_codes),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: MarketCostCurveSufficiencyInput,
    config: MarketCostCurveSufficiencyConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_high_reason(
        reason_codes,
        "spread",
        item.spread_pct,
        config.spread_watch_pct,
        config.spread_block_pct,
    )
    _append_high_reason(
        reason_codes,
        "taker_fee",
        item.taker_fee_pct,
        config.taker_fee_watch_pct,
        config.taker_fee_block_pct,
    )
    _append_high_reason(
        reason_codes,
        "depth_slope",
        item.depth_slope_pct_per_100,
        config.depth_slope_watch_pct_per_100,
        config.depth_slope_block_pct_per_100,
    )
    _append_high_reason(
        reason_codes,
        "deposit_friction",
        item.deposit_friction_pct,
        config.deposit_friction_watch_pct,
        config.deposit_friction_block_pct,
    )
    _append_high_reason(
        reason_codes,
        "settlement_friction",
        item.settlement_friction_pct,
        config.settlement_friction_watch_pct,
        config.settlement_friction_block_pct,
    )
    _append_high_reason(
        reason_codes,
        "gas_friction",
        item.gas_friction_pct,
        config.gas_friction_watch_pct,
        config.gas_friction_block_pct,
    )
    _append_high_reason(
        reason_codes,
        "liquidity_concentration",
        item.top_liquidity_share,
        config.liquidity_concentration_watch_share,
        config.liquidity_concentration_block_share,
    )
    if not reason_codes:
        reason_codes.append("cost_curve_sufficiency_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_high_reason(
    reason_codes: list[str],
    metric_name: str,
    value: Decimal,
    watch: Decimal,
    block: Decimal,
) -> None:
    if value >= block:
        reason_codes.append(f"{metric_name}_block")
    elif value >= watch:
        reason_codes.append(f"{metric_name}_watch")


def _total_friction_pct(value: object) -> Decimal:
    return _quantize(
        getattr(value, "spread_pct")
        + getattr(value, "taker_fee_pct")
        + getattr(value, "deposit_friction_pct")
        + getattr(value, "settlement_friction_pct")
        + getattr(value, "gas_friction_pct"),
    )


def _sufficiency_score(reason_codes: tuple[str, ...]) -> Decimal:
    block_count = sum(1 for reason_code in reason_codes if reason_code.endswith("_block"))
    watch_count = sum(1 for reason_code in reason_codes if reason_code.endswith("_watch"))
    score = _ONE
    score -= Decimal(block_count) * Decimal("0.150000")
    score -= Decimal(watch_count) * Decimal("0.050000")
    if score < _ZERO:
        return _ZERO
    return _quantize(score)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[MarketCostCurveSufficiencyRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketCostCurveSufficiencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cost_curve_sufficiency_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MarketCostCurveSufficiencyRow, ...],
) -> tuple[MarketCostCurveSufficiencyReasonCodeCount, ...]:
    denominator = _decimal_count(len(rows))
    counts: list[MarketCostCurveSufficiencyReasonCodeCount] = []
    for reason_code in reason_codes:
        if rows:
            count = _decimal_count(
                sum(1 for row in rows if reason_code in row.reason_codes),
            )
            row_ratio = _ZERO if denominator == _ZERO else _quantize(count / denominator)
        else:
            count = _decimal_count(1)
            row_ratio = _ZERO
        counts.append(
            MarketCostCurveSufficiencyReasonCodeCount(
                reason_code=reason_code,
                count=count,
                row_ratio=row_ratio,
            ),
        )
    return tuple(counts)


def _status_count(rows: tuple[MarketCostCurveSufficiencyRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_inputs(
    rows: Sequence[MarketCostCurveSufficiencyInput],
) -> tuple[MarketCostCurveSufficiencyInput, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[MarketCostCurveSufficiencyInput] = []
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketCostCurveSufficiencyInput:
            raise ValueError("rows must contain MarketCostCurveSufficiencyInput")
        if row.research_case_key in seen_keys:
            raise ValueError("duplicate research_case_key")
        seen_keys.add(row.research_case_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.research_case_key))


def _normalize_rows(
    rows: Sequence[MarketCostCurveSufficiencyRow],
) -> tuple[MarketCostCurveSufficiencyRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[MarketCostCurveSufficiencyRow] = []
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not MarketCostCurveSufficiencyRow:
            raise ValueError("rows must contain MarketCostCurveSufficiencyRow")
        if row.research_case_key in seen_keys:
            raise ValueError("duplicate research_case_key")
        seen_keys.add(row.research_case_key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.research_case_key))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _normalize_reason_code_counts(
    items: Sequence[MarketCostCurveSufficiencyReasonCodeCount],
) -> tuple[MarketCostCurveSufficiencyReasonCodeCount, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[MarketCostCurveSufficiencyReasonCodeCount] = []
    seen_codes: set[str] = set()
    for item in items:
        if type(item) is not MarketCostCurveSufficiencyReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketCostCurveSufficiencyReasonCodeCount",
            )
        if item.reason_code in seen_codes:
            raise ValueError("reason_code_counts must have unique reason_code values")
        seen_codes.add(item.reason_code)
        normalized.append(item)
    if not normalized:
        raise ValueError("reason_code_counts must not be empty")
    return tuple(
        item
        for reason_code in _REASON_CODE_SEQUENCE
        for item in normalized
        if item.reason_code == reason_code
    )


def _validate_row_consistency(row: MarketCostCurveSufficiencyRow) -> None:
    if row.total_friction_pct != _total_friction_pct(row):
        raise ValueError("total_friction_pct must match input fields")
    if row.sufficiency_score != _sufficiency_score(row.reason_codes):
        raise ValueError("sufficiency_score must match reason_codes")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(report: MarketCostCurveSufficiencyReport) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_sufficiency_score != _average(
        tuple(row.sufficiency_score for row in rows),
    ):
        raise ValueError("average_sufficiency_score must match rows")
    if report.max_spread_pct != max((row.spread_pct for row in rows), default=_ZERO):
        raise ValueError("max_spread_pct must match rows")
    if report.max_taker_fee_pct != max((row.taker_fee_pct for row in rows), default=_ZERO):
        raise ValueError("max_taker_fee_pct must match rows")
    if report.max_depth_slope_pct_per_100 != max(
        (row.depth_slope_pct_per_100 for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_depth_slope_pct_per_100 must match rows")
    if report.max_deposit_friction_pct != max(
        (row.deposit_friction_pct for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_deposit_friction_pct must match rows")
    if report.max_settlement_friction_pct != max(
        (row.settlement_friction_pct for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_settlement_friction_pct must match rows")
    if report.max_gas_friction_pct != max(
        (row.gas_friction_pct for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_gas_friction_pct must match rows")
    if report.max_total_friction_pct != max(
        (row.total_friction_pct for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_total_friction_pct must match rows")
    if report.max_top_liquidity_share != max(
        (row.top_liquidity_share for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_top_liquidity_share must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, rows):
        raise ValueError("reason_code_counts must match rows")


def _report_values_without_digest(
    report: MarketCostCurveSufficiencyReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    canonical_payload = _json_ready(values)
    serialized = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return _json_ready(asdict(value))
    return value


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _format_decimal(value: Decimal) -> str:
    return f"{_quantize(value):.6f}"


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a plain str")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a str")
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains an unsafe public term")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, str):
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_public_text(label, str(key))
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, tuple | list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _reject_unsafe_public_text(label, field.name)
            _reject_unsafe_public_payload(label, getattr(value, field.name))


__all__ = (
    "DEFAULT_MARKET_COST_CURVE_SUFFICIENCY_CONFIG_VERSION",
    "STATUSES",
    "MarketCostCurveSufficiencyConfig",
    "MarketCostCurveSufficiencyInput",
    "MarketCostCurveSufficiencyRow",
    "MarketCostCurveSufficiencyReasonCodeCount",
    "MarketCostCurveSufficiencyReport",
    "build_market_cost_curve_sufficiency_report",
    "market_cost_curve_sufficiency_report_payload",
)
