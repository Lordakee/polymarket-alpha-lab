"""Pure in-memory Phase 1 market liquidity exit gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_MARKET_LIQUIDITY_EXIT_GATE_V2_CONFIG_VERSION = (
    "strategy-market-liquidity-exit-gate-v2"
)

GATE_STATUSES = ("clear", "watch", "blocked")
CLEAR_REASON_CODE = "liquidity_exit_gate_clear"
EMPTY_REASON_CODE = "liquidity_exit_gate_empty"

ROW_REASON_CODE_SEQUENCE = (
    "liquidity_exit_ask_depth_below_minimum",
    "liquidity_exit_ask_depth_below_clear",
    "liquidity_exit_bid_depth_below_clear",
    "liquidity_exit_bid_depth_below_minimum",
    "liquidity_exit_book_imbalance_above_max",
    "liquidity_exit_book_imbalance_above_clear",
    "liquidity_exit_depth_ratio_below_clear",
    "liquidity_exit_depth_ratio_below_minimum",
    "liquidity_exit_settlement_horizon_blocked",
    "liquidity_exit_settlement_horizon_pressure",
    "liquidity_exit_spread_above_max",
    "liquidity_exit_spread_above_clear",
    "liquidity_exit_volume_decay_above_max",
    "liquidity_exit_volume_decay_above_clear",
)
REPORT_REASON_CODE_SEQUENCE = (EMPTY_REASON_CODE, CLEAR_REASON_CODE) + ROW_REASON_CODE_SEQUENCE
BLOCKING_REASON_CODES = frozenset(
    (
        "liquidity_exit_ask_depth_below_minimum",
        "liquidity_exit_bid_depth_below_minimum",
        "liquidity_exit_book_imbalance_above_max",
        "liquidity_exit_depth_ratio_below_minimum",
        "liquidity_exit_settlement_horizon_blocked",
        "liquidity_exit_spread_above_max",
        "liquidity_exit_volume_decay_above_max",
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
class StrategyMarketLiquidityExitGateV2Config:
    config_version: str = DEFAULT_STRATEGY_MARKET_LIQUIDITY_EXIT_GATE_V2_CONFIG_VERSION
    min_clear_bid_depth_shares: Decimal = Decimal("1000.000000")
    min_watch_bid_depth_shares: Decimal = Decimal("500.000000")
    min_clear_ask_depth_shares: Decimal = Decimal("1000.000000")
    min_watch_ask_depth_shares: Decimal = Decimal("500.000000")
    min_clear_exit_depth_to_target_ratio: Decimal = Decimal("2.000000")
    min_watch_exit_depth_to_target_ratio: Decimal = Decimal("1.000000")
    max_clear_spread_probability: Decimal = Decimal("0.020000")
    max_watch_spread_probability: Decimal = Decimal("0.050000")
    max_clear_volume_decay_ratio: Decimal = Decimal("0.250000")
    max_watch_volume_decay_ratio: Decimal = Decimal("0.500000")
    max_clear_book_imbalance_ratio: Decimal = Decimal("0.400000")
    max_watch_book_imbalance_ratio: Decimal = Decimal("0.700000")
    max_clear_settlement_horizon_seconds: Decimal = Decimal("86400.000000")
    max_watch_settlement_horizon_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketLiquidityExitGateV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketLiquidityExitGateV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_MARKET_LIQUIDITY_EXIT_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_clear_bid_depth_shares",
            "min_watch_bid_depth_shares",
            "min_clear_ask_depth_shares",
            "min_watch_ask_depth_shares",
            "min_clear_exit_depth_to_target_ratio",
            "min_watch_exit_depth_to_target_ratio",
            "max_clear_settlement_horizon_seconds",
            "max_watch_settlement_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_clear_spread_probability",
            "max_watch_spread_probability",
            "max_clear_volume_decay_ratio",
            "max_watch_volume_decay_ratio",
            "max_clear_book_imbalance_ratio",
            "max_watch_book_imbalance_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyMarketLiquidityExitGateV2Snapshot:
    market_slug: str
    condition_id: str
    observed_at: datetime
    target_exit_shares: Decimal
    bid_probability: Decimal
    ask_probability: Decimal
    bid_depth_shares: Decimal
    ask_depth_shares: Decimal
    current_volume_shares_24h: Decimal
    previous_volume_shares_24h: Decimal
    settlement_horizon_seconds: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketLiquidityExitGateV2Snapshot does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "condition_id", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "target_exit_shares",
            _normalize_positive_decimal("target_exit_shares", self.target_exit_shares),
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
            "current_volume_shares_24h",
            "previous_volume_shares_24h",
            "settlement_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_snapshot(self)
        _require_hard_flags("snapshot", self)


@dataclass(frozen=True)
class StrategyMarketLiquidityExitGateV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    market_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketLiquidityExitGateV2ReasonCodeCount does not support subclassing",
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
class StrategyMarketLiquidityExitGateV2Row:
    market_slug: str
    condition_id: str
    observed_at: datetime
    target_exit_shares: Decimal
    bid_probability: Decimal
    ask_probability: Decimal
    spread_probability: Decimal
    bid_depth_shares: Decimal
    ask_depth_shares: Decimal
    exit_depth_shares: Decimal
    exit_depth_to_target_ratio: Decimal
    current_volume_shares_24h: Decimal
    previous_volume_shares_24h: Decimal
    volume_decay_ratio: Decimal
    book_imbalance_ratio: Decimal
    settlement_horizon_seconds: Decimal
    feasibility_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyMarketLiquidityExitGateV2Row does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "condition_id", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "target_exit_shares",
            _normalize_positive_decimal("target_exit_shares", self.target_exit_shares),
        )
        for field_name in (
            "bid_probability",
            "ask_probability",
            "spread_probability",
            "volume_decay_ratio",
            "book_imbalance_ratio",
            "feasibility_score",
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
            "current_volume_shares_24h",
            "previous_volume_shares_24h",
            "settlement_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "exit_depth_to_target_ratio",
            _normalize_nonnegative_decimal(
                "exit_depth_to_target_ratio",
                self.exit_depth_to_target_ratio,
            ),
        )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
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
class StrategyMarketLiquidityExitGateV2Report:
    generated_at: datetime
    config_version: str
    market_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    min_exit_depth_to_target_ratio: Decimal
    max_spread_probability: Decimal
    max_volume_decay_ratio: Decimal
    max_book_imbalance_ratio: Decimal
    max_settlement_horizon_seconds: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyMarketLiquidityExitGateV2ReasonCodeCount, ...]
    rows: tuple[StrategyMarketLiquidityExitGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketLiquidityExitGateV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketLiquidityExitGateV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("market_count", "clear_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_exit_depth_to_target_ratio",
            "max_settlement_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_spread_probability",
            "max_volume_decay_ratio",
            "max_book_imbalance_ratio",
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


def build_strategy_market_liquidity_exit_gate_v2_report(
    snapshots: list[StrategyMarketLiquidityExitGateV2Snapshot]
    | tuple[StrategyMarketLiquidityExitGateV2Snapshot, ...],
    *,
    config: StrategyMarketLiquidityExitGateV2Config,
    generated_at: datetime,
) -> StrategyMarketLiquidityExitGateV2Report:
    if type(config) is not StrategyMarketLiquidityExitGateV2Config:
        raise ValueError("config must be a StrategyMarketLiquidityExitGateV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_snapshots = _normalize_snapshots(snapshots)
    _validate_unique_snapshots(normalized_snapshots)
    _validate_not_after_generated_at(normalized_snapshots, generated_at=generated_at_utc)

    rows = tuple(
        sorted(
            (_row_for_snapshot(snapshot, config=config) for snapshot in normalized_snapshots),
            key=_row_sort_key,
        ),
    )
    return StrategyMarketLiquidityExitGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        market_count=_count(len(rows)),
        clear_count=_status_count(rows, "clear"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        min_exit_depth_to_target_ratio=min(
            (row.exit_depth_to_target_ratio for row in rows),
            default=ZERO,
        ),
        max_spread_probability=max((row.spread_probability for row in rows), default=ZERO),
        max_volume_decay_ratio=max((row.volume_decay_ratio for row in rows), default=ZERO),
        max_book_imbalance_ratio=max(
            (row.book_imbalance_ratio for row in rows),
            default=ZERO,
        ),
        max_settlement_horizon_seconds=max(
            (row.settlement_horizon_seconds for row in rows),
            default=ZERO,
        ),
        gate_status=_report_status(rows),
        recommended_next_step=_recommended_next_step(_report_status(rows)),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_market_liquidity_exit_gate_v2_public_payload(
    report: StrategyMarketLiquidityExitGateV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMarketLiquidityExitGateV2Report:
        raise ValueError("report must be a StrategyMarketLiquidityExitGateV2Report")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_strategy_market_liquidity_exit_gate_v2_public_payload(payload)
    return payload


def validate_strategy_market_liquidity_exit_gate_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("strategy market liquidity exit gate payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_snapshot(
    snapshot: StrategyMarketLiquidityExitGateV2Snapshot,
    *,
    config: StrategyMarketLiquidityExitGateV2Config,
) -> StrategyMarketLiquidityExitGateV2Row:
    spread_probability = _subtract_decimal(snapshot.ask_probability, snapshot.bid_probability)
    exit_depth_shares = min(snapshot.bid_depth_shares, snapshot.ask_depth_shares)
    exit_depth_to_target_ratio = _ratio(exit_depth_shares, snapshot.target_exit_shares)
    volume_decay_ratio = _volume_decay_ratio(
        snapshot.current_volume_shares_24h,
        snapshot.previous_volume_shares_24h,
    )
    book_imbalance_ratio = _book_imbalance_ratio(
        snapshot.bid_depth_shares,
        snapshot.ask_depth_shares,
    )
    reason_codes = _row_reason_codes(
        bid_depth_shares=snapshot.bid_depth_shares,
        ask_depth_shares=snapshot.ask_depth_shares,
        exit_depth_to_target_ratio=exit_depth_to_target_ratio,
        spread_probability=spread_probability,
        volume_decay_ratio=volume_decay_ratio,
        book_imbalance_ratio=book_imbalance_ratio,
        settlement_horizon_seconds=snapshot.settlement_horizon_seconds,
        config=config,
    )
    gate_status = _row_status(reason_codes)
    return StrategyMarketLiquidityExitGateV2Row(
        market_slug=snapshot.market_slug,
        condition_id=snapshot.condition_id,
        observed_at=snapshot.observed_at,
        target_exit_shares=snapshot.target_exit_shares,
        bid_probability=snapshot.bid_probability,
        ask_probability=snapshot.ask_probability,
        spread_probability=spread_probability,
        bid_depth_shares=snapshot.bid_depth_shares,
        ask_depth_shares=snapshot.ask_depth_shares,
        exit_depth_shares=exit_depth_shares,
        exit_depth_to_target_ratio=exit_depth_to_target_ratio,
        current_volume_shares_24h=snapshot.current_volume_shares_24h,
        previous_volume_shares_24h=snapshot.previous_volume_shares_24h,
        volume_decay_ratio=volume_decay_ratio,
        book_imbalance_ratio=book_imbalance_ratio,
        settlement_horizon_seconds=snapshot.settlement_horizon_seconds,
        feasibility_score=_feasibility_score(
            gate_status,
            snapshot=snapshot,
            exit_depth_to_target_ratio=exit_depth_to_target_ratio,
            config=config,
        ),
        gate_status=gate_status,
        reason_codes=reason_codes,
        source_config_version=snapshot.source_config_version,
    )


def _row_reason_codes(
    *,
    bid_depth_shares: Decimal,
    ask_depth_shares: Decimal,
    exit_depth_to_target_ratio: Decimal,
    spread_probability: Decimal,
    volume_decay_ratio: Decimal,
    book_imbalance_ratio: Decimal,
    settlement_horizon_seconds: Decimal,
    config: StrategyMarketLiquidityExitGateV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if ask_depth_shares < config.min_watch_ask_depth_shares:
        reason_codes.append("liquidity_exit_ask_depth_below_minimum")
    elif ask_depth_shares < config.min_clear_ask_depth_shares:
        reason_codes.append("liquidity_exit_ask_depth_below_clear")
    if bid_depth_shares < config.min_watch_bid_depth_shares:
        reason_codes.append("liquidity_exit_bid_depth_below_minimum")
    elif bid_depth_shares < config.min_clear_bid_depth_shares:
        reason_codes.append("liquidity_exit_bid_depth_below_clear")
    if book_imbalance_ratio > config.max_watch_book_imbalance_ratio:
        reason_codes.append("liquidity_exit_book_imbalance_above_max")
    elif book_imbalance_ratio > config.max_clear_book_imbalance_ratio:
        reason_codes.append("liquidity_exit_book_imbalance_above_clear")
    if exit_depth_to_target_ratio < config.min_watch_exit_depth_to_target_ratio:
        reason_codes.append("liquidity_exit_depth_ratio_below_minimum")
    elif exit_depth_to_target_ratio < config.min_clear_exit_depth_to_target_ratio:
        reason_codes.append("liquidity_exit_depth_ratio_below_clear")
    if settlement_horizon_seconds > config.max_watch_settlement_horizon_seconds:
        reason_codes.append("liquidity_exit_settlement_horizon_blocked")
    elif settlement_horizon_seconds > config.max_clear_settlement_horizon_seconds:
        reason_codes.append("liquidity_exit_settlement_horizon_pressure")
    if spread_probability > config.max_watch_spread_probability:
        reason_codes.append("liquidity_exit_spread_above_max")
    elif spread_probability > config.max_clear_spread_probability:
        reason_codes.append("liquidity_exit_spread_above_clear")
    if volume_decay_ratio > config.max_watch_volume_decay_ratio:
        reason_codes.append("liquidity_exit_volume_decay_above_max")
    elif volume_decay_ratio > config.max_clear_volume_decay_ratio:
        reason_codes.append("liquidity_exit_volume_decay_above_clear")
    if not reason_codes:
        return (CLEAR_REASON_CODE,)
    return tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _feasibility_score(
    gate_status: str,
    *,
    snapshot: StrategyMarketLiquidityExitGateV2Snapshot,
    exit_depth_to_target_ratio: Decimal,
    config: StrategyMarketLiquidityExitGateV2Config,
) -> Decimal:
    if gate_status == "blocked":
        return ZERO
    if gate_status == "clear":
        return _ratio(exit_depth_to_target_ratio, exit_depth_to_target_ratio + Decimal("0.500000"))
    excess_bid_depth = max(snapshot.bid_depth_shares - config.min_watch_bid_depth_shares, ZERO)
    return _ratio(excess_bid_depth, snapshot.bid_depth_shares)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (CLEAR_REASON_CODE,):
        return "clear"
    return "watch"


def _report_status(rows: tuple[StrategyMarketLiquidityExitGateV2Row, ...]) -> str:
    statuses = tuple(row.gate_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "clear"


def _recommended_next_step(gate_status: str) -> str:
    if gate_status == "blocked":
        return "block_report_only_liquidity_exit"
    if gate_status == "watch":
        return "review_report_only_liquidity_exit"
    return "continue_report_only_liquidity_exit"


def _report_reason_codes(
    rows: tuple[StrategyMarketLiquidityExitGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    present = set(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON_CODE
    )
    if not present:
        return (CLEAR_REASON_CODE,)
    implied_reason_pairs = (
        (
            "liquidity_exit_ask_depth_below_minimum",
            "liquidity_exit_ask_depth_below_clear",
        ),
        (
            "liquidity_exit_bid_depth_below_minimum",
            "liquidity_exit_bid_depth_below_clear",
        ),
        (
            "liquidity_exit_book_imbalance_above_max",
            "liquidity_exit_book_imbalance_above_clear",
        ),
        (
            "liquidity_exit_depth_ratio_below_minimum",
            "liquidity_exit_depth_ratio_below_clear",
        ),
        (
            "liquidity_exit_settlement_horizon_blocked",
            "liquidity_exit_settlement_horizon_pressure",
        ),
        (
            "liquidity_exit_spread_above_max",
            "liquidity_exit_spread_above_clear",
        ),
        (
            "liquidity_exit_volume_decay_above_max",
            "liquidity_exit_volume_decay_above_clear",
        ),
    )
    for severe_reason, threshold_reason in implied_reason_pairs:
        if severe_reason in present:
            present.add(threshold_reason)
    return tuple(reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in present)


def _reason_code_counts(
    rows: tuple[StrategyMarketLiquidityExitGateV2Row, ...],
) -> tuple[StrategyMarketLiquidityExitGateV2ReasonCodeCount, ...]:
    market_count = _count(len(rows))
    return tuple(
        StrategyMarketLiquidityExitGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            market_ratio=_ratio(_reason_count(rows, reason_code), market_count),
        )
        for reason_code in ROW_REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_snapshots(
    value: object,
) -> tuple[StrategyMarketLiquidityExitGateV2Snapshot, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("snapshots must be a list or tuple")
    snapshots = tuple(value)
    for item in snapshots:
        if type(item) is not StrategyMarketLiquidityExitGateV2Snapshot:
            raise ValueError(
                "snapshots must contain StrategyMarketLiquidityExitGateV2Snapshot values",
            )
        _require_hard_flags("snapshot", item)
    return snapshots


def _normalize_rows(value: object) -> tuple[StrategyMarketLiquidityExitGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyMarketLiquidityExitGateV2Row:
            raise ValueError("rows must contain StrategyMarketLiquidityExitGateV2Row values")
        _require_hard_flags("row", row)
        key = _market_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate market liquidity snapshot")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyMarketLiquidityExitGateV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for item in counts:
        if type(item) is not StrategyMarketLiquidityExitGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyMarketLiquidityExitGateV2ReasonCodeCount values",
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


def _validate_config(config: StrategyMarketLiquidityExitGateV2Config) -> None:
    _require_less_or_equal(
        "min_watch_bid_depth_shares",
        config.min_watch_bid_depth_shares,
        config.min_clear_bid_depth_shares,
    )
    _require_less_or_equal(
        "min_watch_ask_depth_shares",
        config.min_watch_ask_depth_shares,
        config.min_clear_ask_depth_shares,
    )
    _require_less_or_equal(
        "min_watch_exit_depth_to_target_ratio",
        config.min_watch_exit_depth_to_target_ratio,
        config.min_clear_exit_depth_to_target_ratio,
    )
    _require_less_or_equal(
        "max_clear_spread_probability",
        config.max_clear_spread_probability,
        config.max_watch_spread_probability,
    )
    _require_less_or_equal(
        "max_clear_volume_decay_ratio",
        config.max_clear_volume_decay_ratio,
        config.max_watch_volume_decay_ratio,
    )
    _require_less_or_equal(
        "max_clear_book_imbalance_ratio",
        config.max_clear_book_imbalance_ratio,
        config.max_watch_book_imbalance_ratio,
    )
    _require_less_or_equal(
        "max_clear_settlement_horizon_seconds",
        config.max_clear_settlement_horizon_seconds,
        config.max_watch_settlement_horizon_seconds,
    )


def _validate_snapshot(snapshot: StrategyMarketLiquidityExitGateV2Snapshot) -> None:
    if snapshot.bid_probability > snapshot.ask_probability:
        raise ValueError("bid_probability must not exceed ask_probability")


def _validate_unique_snapshots(
    snapshots: tuple[StrategyMarketLiquidityExitGateV2Snapshot, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for snapshot in snapshots:
        key = _market_key(snapshot)
        if key in seen:
            raise ValueError("snapshots contain duplicate market liquidity snapshot")
        seen.add(key)


def _validate_not_after_generated_at(
    snapshots: tuple[StrategyMarketLiquidityExitGateV2Snapshot, ...],
    *,
    generated_at: datetime,
) -> None:
    for snapshot in snapshots:
        if snapshot.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _validate_row(row: StrategyMarketLiquidityExitGateV2Row) -> None:
    if row.bid_probability > row.ask_probability:
        raise ValueError("bid_probability must not exceed ask_probability")
    if row.spread_probability != _subtract_decimal(row.ask_probability, row.bid_probability):
        raise ValueError("spread_probability must match probability quotes")
    if row.exit_depth_shares != min(row.bid_depth_shares, row.ask_depth_shares):
        raise ValueError("exit_depth_shares must match displayed depth")
    if row.exit_depth_to_target_ratio != _ratio(row.exit_depth_shares, row.target_exit_shares):
        raise ValueError("exit_depth_to_target_ratio must match exit depth and target")
    if row.volume_decay_ratio != _volume_decay_ratio(
        row.current_volume_shares_24h,
        row.previous_volume_shares_24h,
    ):
        raise ValueError("volume_decay_ratio must match volume values")
    if row.book_imbalance_ratio != _book_imbalance_ratio(
        row.bid_depth_shares,
        row.ask_depth_shares,
    ):
        raise ValueError("book_imbalance_ratio must match book depths")
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyMarketLiquidityExitGateV2Report) -> None:
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
    if report.clear_count + report.watch_count + report.blocked_count != report.market_count:
        raise ValueError("status counts must match market_count")
    if report.min_exit_depth_to_target_ratio != min(
        (row.exit_depth_to_target_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_exit_depth_to_target_ratio must match rows")
    if report.max_spread_probability != max(
        (row.spread_probability for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_spread_probability must match rows")
    if report.max_volume_decay_ratio != max(
        (row.volume_decay_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_volume_decay_ratio must match rows")
    if report.max_book_imbalance_ratio != max(
        (row.book_imbalance_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_book_imbalance_ratio must match rows")
    if report.max_settlement_horizon_seconds != max(
        (row.settlement_horizon_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_settlement_horizon_seconds must match rows")
    if report.gate_status != _report_status(rows):
        raise ValueError("gate_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.gate_status):
        raise ValueError("recommended_next_step must match gate_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _market_key(
    value: StrategyMarketLiquidityExitGateV2Snapshot | StrategyMarketLiquidityExitGateV2Row,
) -> tuple[str, str]:
    return (value.market_slug, value.condition_id)


def _row_sort_key(
    row: StrategyMarketLiquidityExitGateV2Row,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.gate_status],
        row.feasibility_score,
        -_row_pressure_value(row),
        -row.settlement_horizon_seconds,
        row.market_slug,
        row.condition_id,
    )


def _row_pressure_value(row: StrategyMarketLiquidityExitGateV2Row) -> Decimal:
    return max(
        row.spread_probability,
        row.volume_decay_ratio,
        row.book_imbalance_ratio,
    )


def _status_count(
    rows: tuple[StrategyMarketLiquidityExitGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _reason_count(
    rows: tuple[StrategyMarketLiquidityExitGateV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _volume_decay_ratio(current_value: Decimal, previous_value: Decimal) -> Decimal:
    if previous_value == ZERO:
        return ZERO
    decay = max(previous_value - current_value, ZERO)
    return _ratio(decay, previous_value)


def _book_imbalance_ratio(bid_depth: Decimal, ask_depth: Decimal) -> Decimal:
    total_depth = bid_depth + ask_depth
    if total_depth == ZERO:
        return ZERO
    return _ratio(abs(ask_depth - bid_depth), total_depth)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


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


def _row_derived_validation_digest(row: StrategyMarketLiquidityExitGateV2Row) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(report: StrategyMarketLiquidityExitGateV2Report) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _row_public_payload_for_digest(row: StrategyMarketLiquidityExitGateV2Row) -> dict[str, Any]:
    payload = _payload_value(row)
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: StrategyMarketLiquidityExitGateV2Report,
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
    "DEFAULT_STRATEGY_MARKET_LIQUIDITY_EXIT_GATE_V2_CONFIG_VERSION",
    "StrategyMarketLiquidityExitGateV2Config",
    "StrategyMarketLiquidityExitGateV2ReasonCodeCount",
    "StrategyMarketLiquidityExitGateV2Report",
    "StrategyMarketLiquidityExitGateV2Row",
    "StrategyMarketLiquidityExitGateV2Snapshot",
    "build_strategy_market_liquidity_exit_gate_v2_report",
    "strategy_market_liquidity_exit_gate_v2_public_payload",
    "validate_strategy_market_liquidity_exit_gate_v2_public_payload",
)
