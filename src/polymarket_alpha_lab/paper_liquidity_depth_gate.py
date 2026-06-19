"""Paper-only liquidity/depth gate for recommendation rows.

This module is a pure reducer over supplied paper-side depth fields.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
ACTIONS = ("recommend", "watch", "reject")
SIDES = ("yes", "no")
LIQUIDITY_STATUSES = ("pass", "watch", "blocked")
STATUS_PRIORITY = {
    "pass": 0,
    "watch": 1,
    "blocked": 2,
}


@dataclass(frozen=True)
class PaperLiquidityDepthGateInput:
    market_slug: str
    side: str
    action: str
    requested_paper_shares: Decimal
    executable_paper_shares: Decimal
    max_executable_shares: Decimal
    side_price: Decimal
    spread_cost_per_share: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        if self.side not in SIDES:
            raise ValueError("side must be yes or no")
        if self.action not in ACTIONS:
            raise ValueError("action must be recommend, watch, or reject")
        for field_name in (
            "requested_paper_shares",
            "executable_paper_shares",
            "max_executable_shares",
            "spread_cost_per_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "side_price",
            _normalize_probability("side_price", self.side_price),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_input_share_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperLiquidityDepthGateConfig:
    config_version: str
    min_depth_fill_ratio: Decimal
    max_spread_cost_per_share: Decimal
    shallow_depth_penalty_per_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_depth_fill_ratio",
            _normalize_probability("min_depth_fill_ratio", self.min_depth_fill_ratio),
        )
        for field_name in (
            "max_spread_cost_per_share",
            "shallow_depth_penalty_per_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperLiquidityDepthGateRow:
    market_slug: str
    side: str
    action: str
    requested_paper_shares: Decimal
    executable_paper_shares: Decimal
    max_executable_shares: Decimal
    side_price: Decimal
    spread_cost_per_share: Decimal
    fill_ratio: Decimal
    liquidity_status: str
    liquidity_cost_per_share: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        if self.side not in SIDES:
            raise ValueError("side must be yes or no")
        if self.action not in ACTIONS:
            raise ValueError("action must be recommend, watch, or reject")
        for field_name in (
            "requested_paper_shares",
            "executable_paper_shares",
            "max_executable_shares",
            "spread_cost_per_share",
            "liquidity_cost_per_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "side_price",
            _normalize_probability("side_price", self.side_price),
        )
        object.__setattr__(
            self,
            "fill_ratio",
            _normalize_probability("fill_ratio", self.fill_ratio),
        )
        if self.liquidity_status not in LIQUIDITY_STATUSES:
            raise ValueError("liquidity_status must be pass, watch, or blocked")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperLiquidityDepthGateReport:
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    rows: tuple[PaperLiquidityDepthGateRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_paper_liquidity_depth_gate_report(
    inputs: Iterable[PaperLiquidityDepthGateInput],
    *,
    config: PaperLiquidityDepthGateConfig,
    generated_at: datetime,
) -> PaperLiquidityDepthGateReport:
    if type(config) is not PaperLiquidityDepthGateConfig:
        raise ValueError("config must be a PaperLiquidityDepthGateConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_safety_flags(config)

    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(value, config=config) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    return PaperLiquidityDepthGateReport(
        generated_at=_as_utc(generated_at),
        config_version=config.config_version,
        input_count=len(normalized_inputs),
        row_count=len(rows),
        pass_count=_liquidity_status_count(rows, "pass"),
        watch_count=_liquidity_status_count(rows, "watch"),
        blocked_count=_liquidity_status_count(rows, "blocked"),
        rows=rows,
    )


def _row_from_input(
    value: PaperLiquidityDepthGateInput,
    *,
    config: PaperLiquidityDepthGateConfig,
) -> PaperLiquidityDepthGateRow:
    fill_ratio = _fill_ratio(
        value.requested_paper_shares,
        value.executable_paper_shares,
    )
    liquidity_cost_per_share = _liquidity_cost_per_share(
        spread_cost_per_share=value.spread_cost_per_share,
        fill_ratio=fill_ratio,
        shallow_depth_penalty_per_share=config.shallow_depth_penalty_per_share,
    )
    liquidity_status = _liquidity_status(
        action=value.action,
        executable_paper_shares=value.executable_paper_shares,
        fill_ratio=fill_ratio,
        spread_cost_per_share=value.spread_cost_per_share,
        config=config,
    )
    reason_codes = _reason_codes_for(
        source_reason_codes=value.reason_codes,
        action=value.action,
        executable_paper_shares=value.executable_paper_shares,
        fill_ratio=fill_ratio,
        spread_cost_per_share=value.spread_cost_per_share,
        config=config,
    )

    return PaperLiquidityDepthGateRow(
        market_slug=value.market_slug,
        side=value.side,
        action=value.action,
        requested_paper_shares=value.requested_paper_shares,
        executable_paper_shares=value.executable_paper_shares,
        max_executable_shares=value.max_executable_shares,
        side_price=value.side_price,
        spread_cost_per_share=value.spread_cost_per_share,
        fill_ratio=fill_ratio,
        liquidity_status=liquidity_status,
        liquidity_cost_per_share=liquidity_cost_per_share,
        reason_codes=reason_codes,
    )


def _fill_ratio(
    requested_paper_shares: Decimal,
    executable_paper_shares: Decimal,
) -> Decimal:
    if requested_paper_shares <= ZERO:
        return _quantize(ZERO)
    if executable_paper_shares <= ZERO:
        return _quantize(ZERO)
    with localcontext(DECIMAL_CONTEXT):
        ratio = executable_paper_shares / requested_paper_shares
    if ratio > ONE:
        return _quantize(ONE)
    return _quantize(ratio)


def _liquidity_cost_per_share(
    *,
    spread_cost_per_share: Decimal,
    fill_ratio: Decimal,
    shallow_depth_penalty_per_share: Decimal,
) -> Decimal:
    if fill_ratio >= ONE:
        return spread_cost_per_share
    return _add_decimal(spread_cost_per_share, shallow_depth_penalty_per_share)


def _liquidity_status(
    *,
    action: str,
    executable_paper_shares: Decimal,
    fill_ratio: Decimal,
    spread_cost_per_share: Decimal,
    config: PaperLiquidityDepthGateConfig,
) -> str:
    if action == "reject":
        return "blocked"
    if executable_paper_shares <= ZERO:
        return "blocked"
    if fill_ratio < config.min_depth_fill_ratio:
        return "watch"
    if spread_cost_per_share > config.max_spread_cost_per_share:
        return "watch"
    return "pass"


def _reason_codes_for(
    *,
    source_reason_codes: tuple[str, ...],
    action: str,
    executable_paper_shares: Decimal,
    fill_ratio: Decimal,
    spread_cost_per_share: Decimal,
    config: PaperLiquidityDepthGateConfig,
) -> tuple[str, ...]:
    spread_codes = (
        ("spread_cost_above_limit",)
        if spread_cost_per_share > config.max_spread_cost_per_share
        else ()
    )
    depth_codes = _depth_reason_codes(
        executable_paper_shares=executable_paper_shares,
        fill_ratio=fill_ratio,
        min_depth_fill_ratio=config.min_depth_fill_ratio,
        include_pass_code=not spread_codes,
    )
    action_codes = ("upstream_reject_action",) if action == "reject" else ()
    return _normalize_reason_codes(
        (
            *source_reason_codes,
            *depth_codes,
            *spread_codes,
            *action_codes,
        ),
    )


def _depth_reason_codes(
    *,
    executable_paper_shares: Decimal,
    fill_ratio: Decimal,
    min_depth_fill_ratio: Decimal,
    include_pass_code: bool,
) -> tuple[str, ...]:
    if executable_paper_shares <= ZERO:
        return ("no_executable_depth",)
    if fill_ratio < min_depth_fill_ratio:
        return ("below_min_depth_fill_ratio",)
    if not include_pass_code:
        return ()
    return ("liquidity_depth_pass",)


def _row_sort_key(
    row: PaperLiquidityDepthGateRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_PRIORITY[row.liquidity_status],
        -row.fill_ratio,
        row.liquidity_cost_per_share,
        -row.executable_paper_shares,
        row.market_slug,
        row.side,
    )


def _liquidity_status_count(
    rows: tuple[PaperLiquidityDepthGateRow, ...],
    liquidity_status: str,
) -> int:
    return sum(1 for row in rows if row.liquidity_status == liquidity_status)


def _normalize_inputs(
    values: Iterable[PaperLiquidityDepthGateInput],
) -> tuple[PaperLiquidityDepthGateInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable of PaperLiquidityDepthGateInput values")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of PaperLiquidityDepthGateInput values",
        ) from exc
    for value in normalized:
        if type(value) is not PaperLiquidityDepthGateInput:
            raise ValueError(
                "inputs must contain only PaperLiquidityDepthGateInput values",
            )
        _require_safety_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[PaperLiquidityDepthGateRow],
) -> tuple[PaperLiquidityDepthGateRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperLiquidityDepthGateRow:
            raise ValueError("rows must contain PaperLiquidityDepthGateRow values")
        _require_safety_flags(row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _validate_input_share_consistency(value: PaperLiquidityDepthGateInput) -> None:
    if value.executable_paper_shares > value.requested_paper_shares:
        raise ValueError("executable_paper_shares must not exceed requested_paper_shares")
    if value.executable_paper_shares > value.max_executable_shares:
        raise ValueError("max_executable_shares must cover executable_paper_shares")


def _validate_row_consistency(row: PaperLiquidityDepthGateRow) -> None:
    _validate_row_share_consistency(row)
    expected_fill_ratio = _fill_ratio(
        row.requested_paper_shares,
        row.executable_paper_shares,
    )
    if row.fill_ratio != expected_fill_ratio:
        raise ValueError("fill_ratio must match requested and executable shares")
    expected_liquidity_cost_per_share = _expected_row_liquidity_cost_per_share(row)
    if row.liquidity_cost_per_share != expected_liquidity_cost_per_share:
        raise ValueError("liquidity_cost_per_share must match spread and depth penalty")


def _validate_row_share_consistency(row: PaperLiquidityDepthGateRow) -> None:
    if row.executable_paper_shares > row.requested_paper_shares:
        raise ValueError("executable_paper_shares must not exceed requested_paper_shares")
    if row.executable_paper_shares > row.max_executable_shares:
        raise ValueError("max_executable_shares must cover executable_paper_shares")


def _expected_row_liquidity_cost_per_share(
    row: PaperLiquidityDepthGateRow,
) -> Decimal:
    if row.fill_ratio >= ONE:
        return row.spread_cost_per_share
    if row.liquidity_cost_per_share < row.spread_cost_per_share:
        raise ValueError("liquidity_cost_per_share must include spread cost")
    return row.liquidity_cost_per_share


def _validate_report_consistency(report: PaperLiquidityDepthGateReport) -> None:
    if report.input_count != len(report.rows):
        raise ValueError("input_count must equal rows length")
    if report.row_count != len(report.rows):
        raise ValueError("row_count must equal rows length")
    if report.pass_count != _liquidity_status_count(report.rows, "pass"):
        raise ValueError("pass_count must equal rows")
    if report.watch_count != _liquidity_status_count(report.rows, "watch"):
        raise ValueError("watch_count must equal rows")
    if report.blocked_count != _liquidity_status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must equal rows")
    if report.row_count != (
        report.pass_count + report.watch_count + report.blocked_count
    ):
        raise ValueError("row_count must equal liquidity status counts")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted")


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_codes", reason_code)
    return tuple(sorted(set(normalized)))


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_safety_flags(value: Any) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


__all__ = (
    "PaperLiquidityDepthGateInput",
    "PaperLiquidityDepthGateConfig",
    "PaperLiquidityDepthGateRow",
    "PaperLiquidityDepthGateReport",
    "build_paper_liquidity_depth_gate_report",
)
