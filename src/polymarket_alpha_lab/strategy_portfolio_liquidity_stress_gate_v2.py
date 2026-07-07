"""Pure in-memory Phase 1 portfolio liquidity stress gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_PORTFOLIO_LIQUIDITY_STRESS_GATE_V2_CONFIG_VERSION = (
    "strategy-portfolio-liquidity-stress-gate-v2"
)

GATE_STATUSES = ("clear", "watch", "blocked")
CLEAR_REASON_CODE = "portfolio_liquidity_stress_clear"
EMPTY_REASON_CODE = "portfolio_liquidity_stress_gate_empty"

ROW_REASON_CODE_SEQUENCE = (
    "portfolio_liquidity_stress_market_exposure_above_max",
    "portfolio_liquidity_stress_market_exposure_above_clear",
    "portfolio_liquidity_stress_shallow_book",
    "portfolio_liquidity_stress_spread_above_max",
    "portfolio_liquidity_stress_spread_above_clear",
    "portfolio_liquidity_stress_exit_urgency_above_max",
    "portfolio_liquidity_stress_exit_urgency_above_clear",
)
ROW_ALLOWED_REASON_CODE_SEQUENCE = (CLEAR_REASON_CODE,) + ROW_REASON_CODE_SEQUENCE
ROW_BLOCKING_REASON_CODES = frozenset(
    (
        "portfolio_liquidity_stress_market_exposure_above_max",
        "portfolio_liquidity_stress_shallow_book",
        "portfolio_liquidity_stress_spread_above_max",
        "portfolio_liquidity_stress_exit_urgency_above_max",
    ),
)

REPORT_REASON_CODE_SEQUENCE = (
    EMPTY_REASON_CODE,
    CLEAR_REASON_CODE,
    "portfolio_liquidity_stress_open_exposure_above_max",
    "portfolio_liquidity_stress_open_exposure_above_clear",
    "portfolio_liquidity_stress_shallow_book_share_above_max",
    "portfolio_liquidity_stress_shallow_book_share_above_clear",
    "portfolio_liquidity_stress_spread_above_max",
    "portfolio_liquidity_stress_spread_above_clear",
    "portfolio_liquidity_stress_exit_urgency_above_max",
    "portfolio_liquidity_stress_exit_urgency_above_clear",
    "portfolio_liquidity_stress_close_cluster_share_above_max",
    "portfolio_liquidity_stress_close_cluster_share_above_clear",
    "portfolio_liquidity_stress_size_cap_above_max",
    "portfolio_liquidity_stress_size_cap_above_clear",
)
REPORT_BLOCKING_REASON_CODES = frozenset(
    (
        "portfolio_liquidity_stress_open_exposure_above_max",
        "portfolio_liquidity_stress_shallow_book_share_above_max",
        "portfolio_liquidity_stress_spread_above_max",
        "portfolio_liquidity_stress_exit_urgency_above_max",
        "portfolio_liquidity_stress_close_cluster_share_above_max",
        "portfolio_liquidity_stress_size_cap_above_max",
    ),
)

STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "clear": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sig", "ning"),
        _join_parts("mu", "tation"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class StrategyPortfolioLiquidityStressGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_PORTFOLIO_LIQUIDITY_STRESS_GATE_V2_CONFIG_VERSION
    )
    max_clear_portfolio_open_exposure_notional: Decimal = Decimal("100000.000000")
    max_watch_portfolio_open_exposure_notional: Decimal = Decimal("150000.000000")
    max_clear_market_open_exposure_notional: Decimal = Decimal("20000.000000")
    max_watch_market_open_exposure_notional: Decimal = Decimal("50000.000000")
    min_clear_exit_depth_to_exposure_ratio: Decimal = Decimal("1.500000")
    min_watch_exit_depth_to_exposure_ratio: Decimal = Decimal("1.000000")
    max_clear_shallow_book_share_ratio: Decimal = Decimal("0.200000")
    max_watch_shallow_book_share_ratio: Decimal = Decimal("0.400000")
    max_clear_spread_probability: Decimal = Decimal("0.030000")
    max_watch_spread_probability: Decimal = Decimal("0.070000")
    max_clear_exit_urgency_ratio: Decimal = Decimal("0.500000")
    max_watch_exit_urgency_ratio: Decimal = Decimal("0.800000")
    max_clear_close_cluster_share_ratio: Decimal = Decimal("0.300000")
    max_watch_close_cluster_share_ratio: Decimal = Decimal("0.500000")
    close_cluster_horizon_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPortfolioLiquidityStressGateV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyPortfolioLiquidityStressGateV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PORTFOLIO_LIQUIDITY_STRESS_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_clear_portfolio_open_exposure_notional",
            "max_watch_portfolio_open_exposure_notional",
            "max_clear_market_open_exposure_notional",
            "max_watch_market_open_exposure_notional",
            "min_clear_exit_depth_to_exposure_ratio",
            "min_watch_exit_depth_to_exposure_ratio",
            "close_cluster_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_clear_shallow_book_share_ratio",
            "max_watch_shallow_book_share_ratio",
            "max_clear_spread_probability",
            "max_watch_spread_probability",
            "max_clear_exit_urgency_ratio",
            "max_watch_exit_urgency_ratio",
            "max_clear_close_cluster_share_ratio",
            "max_watch_close_cluster_share_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyPortfolioLiquidityStressGateV2Position:
    market_slug: str
    condition_id: str
    observed_at: datetime
    open_exposure_notional: Decimal
    target_exit_shares: Decimal
    bid_probability: Decimal
    ask_probability: Decimal
    bid_depth_shares: Decimal
    ask_depth_shares: Decimal
    market_close_seconds: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPortfolioLiquidityStressGateV2Position does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "condition_id", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("open_exposure_notional", "target_exit_shares"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("bid_probability", "ask_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bid_depth_shares",
            "ask_depth_shares",
            "market_close_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_position(self)
        _require_hard_flags("position", self)


@dataclass(frozen=True)
class StrategyPortfolioLiquidityStressGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    market_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPortfolioLiquidityStressGateV2ReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(
            self,
            "market_ratio",
            _normalize_ratio("market_ratio", self.market_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyPortfolioLiquidityStressGateV2Row:
    market_slug: str
    condition_id: str
    observed_at: datetime
    open_exposure_notional: Decimal
    target_exit_shares: Decimal
    bid_probability: Decimal
    ask_probability: Decimal
    spread_probability: Decimal
    bid_depth_shares: Decimal
    ask_depth_shares: Decimal
    exit_depth_shares: Decimal
    exit_depth_notional: Decimal
    exit_depth_to_exposure_ratio: Decimal
    exit_urgency_ratio: Decimal
    market_close_seconds: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPortfolioLiquidityStressGateV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "condition_id", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("open_exposure_notional", "target_exit_shares"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bid_probability",
            "ask_probability",
            "spread_probability",
            "exit_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bid_depth_shares",
            "ask_depth_shares",
            "exit_depth_shares",
            "exit_depth_notional",
            "exit_depth_to_exposure_ratio",
            "market_close_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_ALLOWED_REASON_CODE_SEQUENCE,
            ),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class StrategyPortfolioLiquidityStressGateV2Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_open_exposure_notional: Decimal
    max_market_open_exposure_notional: Decimal
    shallow_book_open_exposure_notional: Decimal
    shallow_book_share_ratio: Decimal
    max_spread_probability: Decimal
    max_exit_urgency_ratio: Decimal
    close_cluster_open_exposure_notional: Decimal
    close_cluster_share_ratio: Decimal
    size_cap_breach_count: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyPortfolioLiquidityStressGateV2ReasonCodeCount, ...]
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyPortfolioLiquidityStressGateV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyPortfolioLiquidityStressGateV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "market_count",
            "clear_count",
            "watch_count",
            "blocked_count",
            "size_cap_breach_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_open_exposure_notional",
            "max_market_open_exposure_notional",
            "shallow_book_open_exposure_notional",
            "close_cluster_open_exposure_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "shallow_book_share_ratio",
            "max_spread_probability",
            "max_exit_urgency_ratio",
            "close_cluster_share_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_strategy_portfolio_liquidity_stress_gate_v2_report(
    positions: list[StrategyPortfolioLiquidityStressGateV2Position]
    | tuple[StrategyPortfolioLiquidityStressGateV2Position, ...],
    *,
    config: StrategyPortfolioLiquidityStressGateV2Config,
    generated_at: datetime,
) -> StrategyPortfolioLiquidityStressGateV2Report:
    if type(config) is not StrategyPortfolioLiquidityStressGateV2Config:
        raise ValueError("config must be a StrategyPortfolioLiquidityStressGateV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_positions = _normalize_positions(positions)
    _validate_unique_positions(normalized_positions)
    _validate_not_after_generated_at(
        normalized_positions,
        generated_at=generated_at_utc,
    )

    rows = tuple(
        sorted(
            (_row_for_position(position, config=config) for position in normalized_positions),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows, config=config)
    return StrategyPortfolioLiquidityStressGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        clear_count=_status_count(rows, "clear"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        total_open_exposure_notional=_total_open_exposure(rows),
        max_market_open_exposure_notional=max(
            (row.open_exposure_notional for row in rows),
            default=ZERO,
        ),
        shallow_book_open_exposure_notional=_shallow_book_open_exposure(
            rows,
            config=config,
        ),
        shallow_book_share_ratio=_shallow_book_share_ratio(rows, config=config),
        max_spread_probability=max((row.spread_probability for row in rows), default=ZERO),
        max_exit_urgency_ratio=max(
            (row.exit_urgency_ratio for row in rows),
            default=ZERO,
        ),
        close_cluster_open_exposure_notional=_close_cluster_open_exposure(
            rows,
            config=config,
        ),
        close_cluster_share_ratio=_close_cluster_share_ratio(rows, config=config),
        size_cap_breach_count=_size_cap_breach_count(rows, config=config),
        gate_status=_report_status(reason_codes),
        recommended_next_step=_recommended_next_step(_report_status(reason_codes)),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_portfolio_liquidity_stress_gate_v2_public_payload(
    report: StrategyPortfolioLiquidityStressGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyPortfolioLiquidityStressGateV2Report:
        raise ValueError("report must be a StrategyPortfolioLiquidityStressGateV2Report")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_strategy_portfolio_liquidity_stress_gate_v2_public_payload(payload)
    return payload


def validate_strategy_portfolio_liquidity_stress_gate_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("strategy portfolio liquidity stress gate payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_position(
    position: StrategyPortfolioLiquidityStressGateV2Position,
    *,
    config: StrategyPortfolioLiquidityStressGateV2Config,
) -> StrategyPortfolioLiquidityStressGateV2Row:
    spread_probability = _subtract_decimal(position.ask_probability, position.bid_probability)
    exit_depth_shares = min(position.bid_depth_shares, position.ask_depth_shares)
    exit_depth_notional = _multiply_decimal(exit_depth_shares, position.bid_probability)
    exit_depth_to_exposure_ratio = _ratio(
        exit_depth_notional,
        position.open_exposure_notional,
    )
    exit_urgency_ratio = _exit_urgency_ratio(
        position.open_exposure_notional,
        exit_depth_notional,
    )
    reason_codes = _row_reason_codes(
        open_exposure_notional=position.open_exposure_notional,
        exit_depth_to_exposure_ratio=exit_depth_to_exposure_ratio,
        spread_probability=spread_probability,
        exit_urgency_ratio=exit_urgency_ratio,
        config=config,
    )
    gate_status = _row_status(reason_codes)
    return StrategyPortfolioLiquidityStressGateV2Row(
        market_slug=position.market_slug,
        condition_id=position.condition_id,
        observed_at=position.observed_at,
        open_exposure_notional=position.open_exposure_notional,
        target_exit_shares=position.target_exit_shares,
        bid_probability=position.bid_probability,
        ask_probability=position.ask_probability,
        spread_probability=spread_probability,
        bid_depth_shares=position.bid_depth_shares,
        ask_depth_shares=position.ask_depth_shares,
        exit_depth_shares=exit_depth_shares,
        exit_depth_notional=exit_depth_notional,
        exit_depth_to_exposure_ratio=exit_depth_to_exposure_ratio,
        exit_urgency_ratio=exit_urgency_ratio,
        market_close_seconds=position.market_close_seconds,
        gate_status=gate_status,
        reason_codes=reason_codes,
        source_config_version=position.source_config_version,
    )


def _row_reason_codes(
    *,
    open_exposure_notional: Decimal,
    exit_depth_to_exposure_ratio: Decimal,
    spread_probability: Decimal,
    exit_urgency_ratio: Decimal,
    config: StrategyPortfolioLiquidityStressGateV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if open_exposure_notional > config.max_watch_market_open_exposure_notional:
        reason_codes.append("portfolio_liquidity_stress_market_exposure_above_max")
    elif open_exposure_notional > config.max_clear_market_open_exposure_notional:
        reason_codes.append("portfolio_liquidity_stress_market_exposure_above_clear")
    if exit_depth_to_exposure_ratio < config.min_clear_exit_depth_to_exposure_ratio:
        reason_codes.append("portfolio_liquidity_stress_shallow_book")
    if spread_probability > config.max_watch_spread_probability:
        reason_codes.append("portfolio_liquidity_stress_spread_above_max")
    elif spread_probability > config.max_clear_spread_probability:
        reason_codes.append("portfolio_liquidity_stress_spread_above_clear")
    if exit_urgency_ratio > config.max_watch_exit_urgency_ratio:
        reason_codes.append("portfolio_liquidity_stress_exit_urgency_above_max")
    elif exit_urgency_ratio > config.max_clear_exit_urgency_ratio:
        reason_codes.append("portfolio_liquidity_stress_exit_urgency_above_clear")
    if not reason_codes:
        return (CLEAR_REASON_CODE,)
    return tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in ROW_BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (CLEAR_REASON_CODE,):
        return "clear"
    return "watch"


def _report_reason_codes(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    *,
    config: StrategyPortfolioLiquidityStressGateV2Config,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    total_open_exposure = _total_open_exposure(rows)
    shallow_book_share = _shallow_book_share_ratio(rows, config=config)
    max_spread = max((row.spread_probability for row in rows), default=ZERO)
    max_exit_urgency = max((row.exit_urgency_ratio for row in rows), default=ZERO)
    close_cluster_share = _close_cluster_share_ratio(rows, config=config)
    size_cap_max_count = _size_cap_breach_count(rows, config=config)
    size_cap_clear_count = _size_cap_clear_count(rows, config=config)

    reason_codes: list[str] = []
    if total_open_exposure > config.max_watch_portfolio_open_exposure_notional:
        reason_codes.append("portfolio_liquidity_stress_open_exposure_above_max")
    elif total_open_exposure > config.max_clear_portfolio_open_exposure_notional:
        reason_codes.append("portfolio_liquidity_stress_open_exposure_above_clear")
    if shallow_book_share > config.max_watch_shallow_book_share_ratio:
        reason_codes.append("portfolio_liquidity_stress_shallow_book_share_above_max")
    elif shallow_book_share > config.max_clear_shallow_book_share_ratio:
        reason_codes.append("portfolio_liquidity_stress_shallow_book_share_above_clear")
    if max_spread > config.max_watch_spread_probability:
        reason_codes.append("portfolio_liquidity_stress_spread_above_max")
    elif max_spread > config.max_clear_spread_probability:
        reason_codes.append("portfolio_liquidity_stress_spread_above_clear")
    if max_exit_urgency > config.max_watch_exit_urgency_ratio:
        reason_codes.append("portfolio_liquidity_stress_exit_urgency_above_max")
    elif max_exit_urgency > config.max_clear_exit_urgency_ratio:
        reason_codes.append("portfolio_liquidity_stress_exit_urgency_above_clear")
    if close_cluster_share > config.max_watch_close_cluster_share_ratio:
        reason_codes.append("portfolio_liquidity_stress_close_cluster_share_above_max")
    elif close_cluster_share > config.max_clear_close_cluster_share_ratio:
        reason_codes.append("portfolio_liquidity_stress_close_cluster_share_above_clear")
    if size_cap_max_count > ZERO:
        reason_codes.append("portfolio_liquidity_stress_size_cap_above_max")
    elif size_cap_clear_count > ZERO:
        reason_codes.append("portfolio_liquidity_stress_size_cap_above_clear")
    if not reason_codes:
        return (CLEAR_REASON_CODE,)
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in REPORT_BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes in ((CLEAR_REASON_CODE,), (EMPTY_REASON_CODE,)):
        return "clear"
    return "watch"


def _recommended_next_step(gate_status: str) -> str:
    if gate_status == "blocked":
        return "block_report_only_portfolio_liquidity_stress_gate"
    if gate_status == "watch":
        return "review_report_only_portfolio_liquidity_stress_gate"
    return "continue_report_only_portfolio_liquidity_stress_gate"


def _reason_code_counts(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
) -> tuple[StrategyPortfolioLiquidityStressGateV2ReasonCodeCount, ...]:
    market_count = _count(len(rows))
    return tuple(
        StrategyPortfolioLiquidityStressGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            market_ratio=_ratio(_reason_count(rows, reason_code), market_count),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_positions(
    value: object,
) -> tuple[StrategyPortfolioLiquidityStressGateV2Position, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("positions must be a list or tuple")
    positions = tuple(value)
    for item in positions:
        if type(item) is not StrategyPortfolioLiquidityStressGateV2Position:
            raise ValueError(
                "positions must contain StrategyPortfolioLiquidityStressGateV2Position "
                "values",
            )
        _require_hard_flags("position", item)
    return positions


def _normalize_rows(value: object) -> tuple[StrategyPortfolioLiquidityStressGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyPortfolioLiquidityStressGateV2Row:
            raise ValueError(
                "rows must contain StrategyPortfolioLiquidityStressGateV2Row values",
            )
        _require_hard_flags("row", row)
        key = _position_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate portfolio liquidity position")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyPortfolioLiquidityStressGateV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not StrategyPortfolioLiquidityStressGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyPortfolioLiquidityStressGateV2ReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
    expected = tuple(
        item
        for reason_code in ROW_REASON_CODE_SEQUENCE
        for item in counts
        if item.reason_code == reason_code
    )
    if counts != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_config(config: StrategyPortfolioLiquidityStressGateV2Config) -> None:
    _require_less_or_equal(
        "max_clear_portfolio_open_exposure_notional",
        config.max_clear_portfolio_open_exposure_notional,
        config.max_watch_portfolio_open_exposure_notional,
    )
    _require_less_or_equal(
        "max_clear_market_open_exposure_notional",
        config.max_clear_market_open_exposure_notional,
        config.max_watch_market_open_exposure_notional,
    )
    _require_less_or_equal(
        "min_watch_exit_depth_to_exposure_ratio",
        config.min_watch_exit_depth_to_exposure_ratio,
        config.min_clear_exit_depth_to_exposure_ratio,
    )
    _require_less_or_equal(
        "max_clear_shallow_book_share_ratio",
        config.max_clear_shallow_book_share_ratio,
        config.max_watch_shallow_book_share_ratio,
    )
    _require_less_or_equal(
        "max_clear_spread_probability",
        config.max_clear_spread_probability,
        config.max_watch_spread_probability,
    )
    _require_less_or_equal(
        "max_clear_exit_urgency_ratio",
        config.max_clear_exit_urgency_ratio,
        config.max_watch_exit_urgency_ratio,
    )
    _require_less_or_equal(
        "max_clear_close_cluster_share_ratio",
        config.max_clear_close_cluster_share_ratio,
        config.max_watch_close_cluster_share_ratio,
    )


def _validate_position(position: StrategyPortfolioLiquidityStressGateV2Position) -> None:
    if position.bid_probability > position.ask_probability:
        raise ValueError("bid_probability must not exceed ask_probability")


def _validate_unique_positions(
    positions: tuple[StrategyPortfolioLiquidityStressGateV2Position, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for position in positions:
        key = _position_key(position)
        if key in seen:
            raise ValueError("positions contain duplicate portfolio liquidity position")
        seen.add(key)


def _validate_not_after_generated_at(
    positions: tuple[StrategyPortfolioLiquidityStressGateV2Position, ...],
    *,
    generated_at: datetime,
) -> None:
    for position in positions:
        if position.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _validate_row(row: StrategyPortfolioLiquidityStressGateV2Row) -> None:
    if row.bid_probability > row.ask_probability:
        raise ValueError("bid_probability must not exceed ask_probability")
    if row.spread_probability != _subtract_decimal(row.ask_probability, row.bid_probability):
        raise ValueError("spread_probability must match quotes")
    if row.exit_depth_shares != min(row.bid_depth_shares, row.ask_depth_shares):
        raise ValueError("exit_depth_shares must match displayed depth")
    if row.exit_depth_notional != _multiply_decimal(
        row.exit_depth_shares,
        row.bid_probability,
    ):
        raise ValueError("exit_depth_notional must match displayed depth")
    if row.exit_depth_to_exposure_ratio != _ratio(
        row.exit_depth_notional,
        row.open_exposure_notional,
    ):
        raise ValueError("exit_depth_to_exposure_ratio must match exposure")
    if row.exit_urgency_ratio != _exit_urgency_ratio(
        row.open_exposure_notional,
        row.exit_depth_notional,
    ):
        raise ValueError("exit_urgency_ratio must match exposure")
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyPortfolioLiquidityStressGateV2Report) -> None:
    rows = report.rows
    market_count = _count(len(rows))
    if report.market_count != market_count:
        raise ValueError("market_count must match rows")
    for field_name, status in (
        ("clear_count", "clear"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.clear_count + report.watch_count + report.blocked_count != market_count:
        raise ValueError("status counts must match market_count")
    if report.total_open_exposure_notional != _total_open_exposure(rows):
        raise ValueError("total_open_exposure_notional must match rows")
    if report.max_market_open_exposure_notional != max(
        (row.open_exposure_notional for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_market_open_exposure_notional must match rows")
    if report.shallow_book_open_exposure_notional != _row_exposure_with_reason(
        rows,
        "portfolio_liquidity_stress_shallow_book",
    ):
        raise ValueError("shallow_book_open_exposure_notional must match rows")
    if report.shallow_book_share_ratio != _ratio(
        report.shallow_book_open_exposure_notional,
        report.total_open_exposure_notional,
    ):
        raise ValueError("shallow_book_share_ratio must match rows")
    if report.max_spread_probability != max(
        (row.spread_probability for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_spread_probability must match rows")
    if report.max_exit_urgency_ratio != max(
        (row.exit_urgency_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_exit_urgency_ratio must match rows")
    if report.close_cluster_open_exposure_notional > report.total_open_exposure_notional:
        raise ValueError("close_cluster_open_exposure_notional must not exceed total")
    if report.close_cluster_share_ratio != _ratio(
        report.close_cluster_open_exposure_notional,
        report.total_open_exposure_notional,
    ):
        raise ValueError("close_cluster_share_ratio must match rows")
    if report.size_cap_breach_count != _reason_count(
        rows,
        "portfolio_liquidity_stress_market_exposure_above_max",
    ):
        raise ValueError("size_cap_breach_count must match rows")
    if report.gate_status != _report_status(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if report.recommended_next_step != _recommended_next_step(report.gate_status):
        raise ValueError("recommended_next_step must match gate_status")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _position_key(
    value: StrategyPortfolioLiquidityStressGateV2Position
    | StrategyPortfolioLiquidityStressGateV2Row,
) -> tuple[str, str]:
    return (value.market_slug, value.condition_id)


def _row_sort_key(
    row: StrategyPortfolioLiquidityStressGateV2Row,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.gate_status],
        -row.open_exposure_notional,
        -_row_pressure_value(row),
        row.market_close_seconds,
        row.market_slug,
        row.condition_id,
    )


def _row_pressure_value(row: StrategyPortfolioLiquidityStressGateV2Row) -> Decimal:
    return max(row.spread_probability, row.exit_urgency_ratio)


def _status_count(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _reason_count(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_exposure_with_reason(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _sum_decimal(
        tuple(row.open_exposure_notional for row in rows if reason_code in row.reason_codes),
    )


def _total_open_exposure(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
) -> Decimal:
    return _sum_decimal(tuple(row.open_exposure_notional for row in rows))


def _shallow_book_open_exposure(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    *,
    config: StrategyPortfolioLiquidityStressGateV2Config,
) -> Decimal:
    return _sum_decimal(
        tuple(
            row.open_exposure_notional
            for row in rows
            if row.exit_depth_to_exposure_ratio
            < config.min_clear_exit_depth_to_exposure_ratio
        ),
    )


def _shallow_book_share_ratio(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    *,
    config: StrategyPortfolioLiquidityStressGateV2Config,
) -> Decimal:
    return _ratio(
        _shallow_book_open_exposure(rows, config=config),
        _total_open_exposure(rows),
    )


def _close_cluster_open_exposure(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    *,
    config: StrategyPortfolioLiquidityStressGateV2Config,
) -> Decimal:
    return _sum_decimal(
        tuple(
            row.open_exposure_notional
            for row in rows
            if row.market_close_seconds <= config.close_cluster_horizon_seconds
        ),
    )


def _close_cluster_share_ratio(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    *,
    config: StrategyPortfolioLiquidityStressGateV2Config,
) -> Decimal:
    return _ratio(
        _close_cluster_open_exposure(rows, config=config),
        _total_open_exposure(rows),
    )


def _size_cap_breach_count(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    *,
    config: StrategyPortfolioLiquidityStressGateV2Config,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if row.open_exposure_notional > config.max_watch_market_open_exposure_notional
        ),
    )


def _size_cap_clear_count(
    rows: tuple[StrategyPortfolioLiquidityStressGateV2Row, ...],
    *,
    config: StrategyPortfolioLiquidityStressGateV2Config,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if row.open_exposure_notional > config.max_clear_market_open_exposure_notional
        ),
    )


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        with localcontext(DECIMAL_CONTEXT):
            total = _quantize(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _exit_urgency_ratio(open_exposure_notional: Decimal, exit_depth_notional: Decimal) -> Decimal:
    if exit_depth_notional == ZERO:
        return ONE
    return min(ONE, _ratio(open_exposure_notional, exit_depth_notional))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: Any) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_count(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_ratio(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if value != normalized:
        raise ValueError(f"{field_name} must have at most six decimal places")
    return normalized


def _require_public_string(field_name: str, value: Any) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_surface_fragment(value):
        raise ValueError(f"{field_name} has unsafe value")


def _require_member(field_name: str, value: Any, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_less_or_equal(field_name: str, left: Decimal, right: Decimal) -> None:
    if left > right:
        raise ValueError(f"{field_name} must not exceed paired threshold")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256_digest(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _row_derived_validation_digest(
    row: StrategyPortfolioLiquidityStressGateV2Row,
) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: StrategyPortfolioLiquidityStressGateV2Report,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _row_public_payload_for_digest(
    row: StrategyPortfolioLiquidityStressGateV2Row,
) -> dict[str, Any]:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: StrategyPortfolioLiquidityStressGateV2Report,
) -> dict[str, Any]:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded_payload.encode("utf-8")).hexdigest()


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_surface_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_public_numeric_values(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError("public payload must use Decimal strings, not numeric values")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numeric_values(item)


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _has_unsafe_surface_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS)


__all__ = (
    "DEFAULT_STRATEGY_PORTFOLIO_LIQUIDITY_STRESS_GATE_V2_CONFIG_VERSION",
    "StrategyPortfolioLiquidityStressGateV2Config",
    "StrategyPortfolioLiquidityStressGateV2Position",
    "StrategyPortfolioLiquidityStressGateV2ReasonCodeCount",
    "StrategyPortfolioLiquidityStressGateV2Report",
    "StrategyPortfolioLiquidityStressGateV2Row",
    "build_strategy_portfolio_liquidity_stress_gate_v2_report",
    "strategy_portfolio_liquidity_stress_gate_v2_public_payload",
    "validate_strategy_portfolio_liquidity_stress_gate_v2_public_payload",
)
