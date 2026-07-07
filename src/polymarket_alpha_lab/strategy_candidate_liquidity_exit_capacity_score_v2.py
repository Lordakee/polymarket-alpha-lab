"""Pure paper/report score for candidate liquidity exit capacity v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_LIQUIDITY_EXIT_CAPACITY_SCORE_V2_CONFIG_VERSION = (
    "strategy-candidate-liquidity-exit-capacity-score-v2"
)
EXIT_CAPACITY_STATUSES = ("pass", "watch", "blocked")
CAPACITY_DECISIONS = ("paper_candidate", "manual_review", "reject")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HUNDRED = Decimal("100.000000")
DEPTH_SCORE_WEIGHT = Decimal("0.550000")
SPREAD_SCORE_WEIGHT = Decimal("0.200000")
URGENCY_SCORE_WEIGHT = Decimal("0.100000")
CLOSE_SCORE_WEIGHT = Decimal("0.100000")
SETTLEMENT_SCORE_WEIGHT = Decimal("0.050000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_UNSAFE_TERM_PARTS = (
    ("li", "ve"),
    ("au", "th"),
    ("wal", "let"),
    ("or", "der"),
    ("net", "work"),
    ("data", "base"),
    ("per", "sist"),
    ("sig", "ning"),
    ("muta", "tion"),
    ("b", "uy"),
    ("se", "ll"),
    ("tra", "de"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "candidate_id",
    "market_slug",
    "observed_at",
    "config_version",
    "expected_position_notional",
    "book_depth_notional",
    "spread_ratio",
    "urgency_ratio",
    "seconds_until_market_close",
    "settlement_lag_seconds",
    "watch_min_exit_depth_to_required_capacity_ratio",
    "block_min_exit_depth_to_required_capacity_ratio",
    "watch_max_spread_ratio",
    "block_max_spread_ratio",
    "watch_min_seconds_until_market_close",
    "block_min_seconds_until_market_close",
    "watch_max_settlement_lag_seconds",
    "block_max_settlement_lag_seconds",
    "urgency_capacity_buffer_ratio",
    "close_proximity_capacity_buffer_ratio",
    "settlement_lag_capacity_buffer_ratio",
    "minimum_pass_score",
    "blocked_max_score",
    "urgency_capacity_buffer_notional",
    "close_proximity_pressure_ratio",
    "close_proximity_capacity_buffer_notional",
    "settlement_lag_pressure_ratio",
    "settlement_lag_capacity_buffer_notional",
    "required_exit_capacity_notional",
    "exit_depth_to_required_capacity_ratio",
    "capacity_shortfall_notional",
    "depth_capacity_score",
    "spread_score",
    "urgency_score",
    "close_proximity_score",
    "settlement_lag_score",
    "exit_capacity_score",
    "exit_capacity_status",
    "capacity_decision",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class StrategyCandidateLiquidityExitCapacityScoreV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_LIQUIDITY_EXIT_CAPACITY_SCORE_V2_CONFIG_VERSION
    )
    watch_min_exit_depth_to_required_capacity_ratio: Decimal = Decimal("1.250000")
    block_min_exit_depth_to_required_capacity_ratio: Decimal = Decimal("1.000000")
    watch_max_spread_ratio: Decimal = Decimal("0.030000")
    block_max_spread_ratio: Decimal = Decimal("0.060000")
    watch_min_seconds_until_market_close: Decimal = Decimal("172800.000000")
    block_min_seconds_until_market_close: Decimal = Decimal("21600.000000")
    watch_max_settlement_lag_seconds: Decimal = Decimal("86400.000000")
    block_max_settlement_lag_seconds: Decimal = Decimal("259200.000000")
    urgency_capacity_buffer_ratio: Decimal = Decimal("0.500000")
    close_proximity_capacity_buffer_ratio: Decimal = Decimal("0.500000")
    settlement_lag_capacity_buffer_ratio: Decimal = Decimal("0.250000")
    minimum_pass_score: Decimal = Decimal("75.000000")
    blocked_max_score: Decimal = Decimal("25.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateLiquidityExitCapacityScoreV2Config:
            raise ValueError(
                "config must be a StrategyCandidateLiquidityExitCapacityScoreV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_min_exit_depth_to_required_capacity_ratio",
            "block_min_exit_depth_to_required_capacity_ratio",
            "watch_max_spread_ratio",
            "block_max_spread_ratio",
            "urgency_capacity_buffer_ratio",
            "close_proximity_capacity_buffer_ratio",
            "settlement_lag_capacity_buffer_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_min_seconds_until_market_close",
            "block_min_seconds_until_market_close",
            "watch_max_settlement_lag_seconds",
            "block_max_settlement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in ("minimum_pass_score", "blocked_max_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateLiquidityExitCapacityScoreV2Input:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    expected_position_notional: Decimal
    book_depth_notional: Decimal
    spread_ratio: Decimal
    urgency_ratio: Decimal
    seconds_until_market_close: Decimal
    settlement_lag_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateLiquidityExitCapacityScoreV2Input:
            raise ValueError(
                "input must be a StrategyCandidateLiquidityExitCapacityScoreV2Input",
            )
        for field_name in ("candidate_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "expected_position_notional",
            _normalize_positive_money(
                "expected_position_notional",
                self.expected_position_notional,
            ),
        )
        object.__setattr__(
            self,
            "book_depth_notional",
            _normalize_money("book_depth_notional", self.book_depth_notional),
        )
        object.__setattr__(
            self,
            "spread_ratio",
            _normalize_ratio("spread_ratio", self.spread_ratio),
        )
        object.__setattr__(
            self,
            "urgency_ratio",
            _normalize_unit_ratio("urgency_ratio", self.urgency_ratio),
        )
        for field_name in ("seconds_until_market_close", "settlement_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("input", self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyCandidateLiquidityExitCapacityScoreV2Result:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    config_version: str
    expected_position_notional: Decimal
    book_depth_notional: Decimal
    spread_ratio: Decimal
    urgency_ratio: Decimal
    seconds_until_market_close: Decimal
    settlement_lag_seconds: Decimal
    watch_min_exit_depth_to_required_capacity_ratio: Decimal
    block_min_exit_depth_to_required_capacity_ratio: Decimal
    watch_max_spread_ratio: Decimal
    block_max_spread_ratio: Decimal
    watch_min_seconds_until_market_close: Decimal
    block_min_seconds_until_market_close: Decimal
    watch_max_settlement_lag_seconds: Decimal
    block_max_settlement_lag_seconds: Decimal
    urgency_capacity_buffer_ratio: Decimal
    close_proximity_capacity_buffer_ratio: Decimal
    settlement_lag_capacity_buffer_ratio: Decimal
    minimum_pass_score: Decimal
    blocked_max_score: Decimal
    urgency_capacity_buffer_notional: Decimal
    close_proximity_pressure_ratio: Decimal
    close_proximity_capacity_buffer_notional: Decimal
    settlement_lag_pressure_ratio: Decimal
    settlement_lag_capacity_buffer_notional: Decimal
    required_exit_capacity_notional: Decimal
    exit_depth_to_required_capacity_ratio: Decimal
    capacity_shortfall_notional: Decimal
    depth_capacity_score: Decimal
    spread_score: Decimal
    urgency_score: Decimal
    close_proximity_score: Decimal
    settlement_lag_score: Decimal
    exit_capacity_score: Decimal
    exit_capacity_status: str
    capacity_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateLiquidityExitCapacityScoreV2Result:
            raise ValueError(
                "result must be a StrategyCandidateLiquidityExitCapacityScoreV2Result",
            )
        for field_name in ("candidate_id", "market_slug", "config_version"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "expected_position_notional",
            _normalize_positive_money(
                "expected_position_notional",
                self.expected_position_notional,
            ),
        )
        for field_name in (
            "book_depth_notional",
            "urgency_capacity_buffer_notional",
            "close_proximity_capacity_buffer_notional",
            "settlement_lag_capacity_buffer_notional",
            "required_exit_capacity_notional",
            "capacity_shortfall_notional",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_money(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_ratio",
            "urgency_ratio",
            "watch_min_exit_depth_to_required_capacity_ratio",
            "block_min_exit_depth_to_required_capacity_ratio",
            "watch_max_spread_ratio",
            "block_max_spread_ratio",
            "urgency_capacity_buffer_ratio",
            "close_proximity_capacity_buffer_ratio",
            "settlement_lag_capacity_buffer_ratio",
            "close_proximity_pressure_ratio",
            "settlement_lag_pressure_ratio",
            "exit_depth_to_required_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "seconds_until_market_close",
            "settlement_lag_seconds",
            "watch_min_seconds_until_market_close",
            "block_min_seconds_until_market_close",
            "watch_max_settlement_lag_seconds",
            "block_max_settlement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_score",
            "blocked_max_score",
            "depth_capacity_score",
            "spread_score",
            "urgency_score",
            "close_proximity_score",
            "settlement_lag_score",
            "exit_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _require_member(
            "exit_capacity_status",
            self.exit_capacity_status,
            EXIT_CAPACITY_STATUSES,
        )
        _require_member("capacity_decision", self.capacity_decision, CAPACITY_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_config_fields(self)
        _validate_result_consistency(self)
        _reject_unsafe_public_payload("result", self)
        _require_hard_flags("result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_liquidity_exit_capacity_score_v2_payload(self)


def score_strategy_candidate_liquidity_exit_capacity_v2(
    capacity_input: StrategyCandidateLiquidityExitCapacityScoreV2Input,
    *,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config | None = None,
) -> StrategyCandidateLiquidityExitCapacityScoreV2Result:
    if type(capacity_input) is not StrategyCandidateLiquidityExitCapacityScoreV2Input:
        raise ValueError(
            "input must be a StrategyCandidateLiquidityExitCapacityScoreV2Input",
        )
    if config is None:
        config = StrategyCandidateLiquidityExitCapacityScoreV2Config()
    if type(config) is not StrategyCandidateLiquidityExitCapacityScoreV2Config:
        raise ValueError(
            "config must be a StrategyCandidateLiquidityExitCapacityScoreV2Config",
        )
    _reject_unsafe_public_payload("input", capacity_input)
    _reject_unsafe_public_payload("config", config)
    _require_hard_flags("input", capacity_input)
    _require_hard_flags("config", config)

    close_pressure = _close_proximity_pressure(capacity_input, config)
    settlement_pressure = _settlement_lag_pressure(capacity_input, config)
    urgency_buffer = _money_product(
        capacity_input.expected_position_notional,
        capacity_input.urgency_ratio,
        config.urgency_capacity_buffer_ratio,
    )
    close_buffer = _money_product(
        capacity_input.expected_position_notional,
        close_pressure,
        config.close_proximity_capacity_buffer_ratio,
    )
    settlement_buffer = _money_product(
        capacity_input.expected_position_notional,
        settlement_pressure,
        config.settlement_lag_capacity_buffer_ratio,
    )
    required_capacity = _add_money(
        capacity_input.expected_position_notional,
        urgency_buffer,
        close_buffer,
        settlement_buffer,
    )
    depth_ratio = _ratio(capacity_input.book_depth_notional, required_capacity)
    capacity_shortfall = max(
        required_capacity - capacity_input.book_depth_notional,
        ZERO,
    ).quantize(QUANTUM)
    depth_score = _depth_capacity_score(depth_ratio, config)
    spread_score = _spread_score(capacity_input.spread_ratio, config)
    urgency_score = _unit_inverse_score(capacity_input.urgency_ratio)
    close_score = _unit_inverse_score(close_pressure)
    settlement_score = _settlement_lag_score(capacity_input, config)
    score_value = _weighted_score(
        depth_score=depth_score,
        spread_score=spread_score,
        urgency_score=urgency_score,
        close_score=close_score,
        settlement_score=settlement_score,
    )
    status = _status(
        capacity_input,
        config,
        depth_ratio=depth_ratio,
        score_value=score_value,
    )

    return StrategyCandidateLiquidityExitCapacityScoreV2Result(
        candidate_id=capacity_input.candidate_id,
        market_slug=capacity_input.market_slug,
        observed_at=capacity_input.observed_at,
        config_version=config.config_version,
        expected_position_notional=capacity_input.expected_position_notional,
        book_depth_notional=capacity_input.book_depth_notional,
        spread_ratio=capacity_input.spread_ratio,
        urgency_ratio=capacity_input.urgency_ratio,
        seconds_until_market_close=capacity_input.seconds_until_market_close,
        settlement_lag_seconds=capacity_input.settlement_lag_seconds,
        watch_min_exit_depth_to_required_capacity_ratio=(
            config.watch_min_exit_depth_to_required_capacity_ratio
        ),
        block_min_exit_depth_to_required_capacity_ratio=(
            config.block_min_exit_depth_to_required_capacity_ratio
        ),
        watch_max_spread_ratio=config.watch_max_spread_ratio,
        block_max_spread_ratio=config.block_max_spread_ratio,
        watch_min_seconds_until_market_close=config.watch_min_seconds_until_market_close,
        block_min_seconds_until_market_close=config.block_min_seconds_until_market_close,
        watch_max_settlement_lag_seconds=config.watch_max_settlement_lag_seconds,
        block_max_settlement_lag_seconds=config.block_max_settlement_lag_seconds,
        urgency_capacity_buffer_ratio=config.urgency_capacity_buffer_ratio,
        close_proximity_capacity_buffer_ratio=(
            config.close_proximity_capacity_buffer_ratio
        ),
        settlement_lag_capacity_buffer_ratio=(
            config.settlement_lag_capacity_buffer_ratio
        ),
        minimum_pass_score=config.minimum_pass_score,
        blocked_max_score=config.blocked_max_score,
        urgency_capacity_buffer_notional=urgency_buffer,
        close_proximity_pressure_ratio=close_pressure,
        close_proximity_capacity_buffer_notional=close_buffer,
        settlement_lag_pressure_ratio=settlement_pressure,
        settlement_lag_capacity_buffer_notional=settlement_buffer,
        required_exit_capacity_notional=required_capacity,
        exit_depth_to_required_capacity_ratio=depth_ratio,
        capacity_shortfall_notional=capacity_shortfall,
        depth_capacity_score=depth_score,
        spread_score=spread_score,
        urgency_score=urgency_score,
        close_proximity_score=close_score,
        settlement_lag_score=settlement_score,
        exit_capacity_score=score_value,
        exit_capacity_status=status,
        capacity_decision=_capacity_decision(status),
        reason_codes=_reason_codes(
            capacity_input.reason_codes,
            status=status,
            capacity_input=capacity_input,
            config=config,
            depth_ratio=depth_ratio,
            capacity_shortfall=capacity_shortfall,
            score_value=score_value,
        ),
    )


def strategy_candidate_liquidity_exit_capacity_score_v2_payload(
    result: StrategyCandidateLiquidityExitCapacityScoreV2Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateLiquidityExitCapacityScoreV2Result:
        raise ValueError(
            "result must be a StrategyCandidateLiquidityExitCapacityScoreV2Result",
        )
    _require_hard_flags("result", result)
    _validate_result_consistency(result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    _reject_unsafe_public_payload("result", result)
    return _json_ready(asdict(result))


def reject_strategy_candidate_liquidity_exit_capacity_score_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    _reject_unsafe_public_payload(label, payload)


def _validate_config(config: StrategyCandidateLiquidityExitCapacityScoreV2Config) -> None:
    if (
        config.block_min_exit_depth_to_required_capacity_ratio
        > config.watch_min_exit_depth_to_required_capacity_ratio
    ):
        raise ValueError(
            "block_min_exit_depth_to_required_capacity_ratio must be <= watch threshold",
        )
    if config.block_min_exit_depth_to_required_capacity_ratio <= ZERO:
        raise ValueError(
            "block_min_exit_depth_to_required_capacity_ratio must be positive",
        )
    if config.watch_max_spread_ratio > config.block_max_spread_ratio:
        raise ValueError(
            "watch_max_spread_ratio must be <= block_max_spread_ratio",
        )
    if config.block_max_spread_ratio <= ZERO:
        raise ValueError("block_max_spread_ratio must be positive")
    if (
        config.block_min_seconds_until_market_close
        > config.watch_min_seconds_until_market_close
    ):
        raise ValueError(
            "block_min_seconds_until_market_close must be <= watch threshold",
        )
    if config.watch_min_seconds_until_market_close <= ZERO:
        raise ValueError("watch_min_seconds_until_market_close must be positive")
    if config.watch_max_settlement_lag_seconds > config.block_max_settlement_lag_seconds:
        raise ValueError(
            "watch_max_settlement_lag_seconds must be <= block threshold",
        )
    if config.block_max_settlement_lag_seconds <= ZERO:
        raise ValueError("block_max_settlement_lag_seconds must be positive")
    if config.blocked_max_score > config.minimum_pass_score:
        raise ValueError("blocked_max_score must be <= minimum_pass_score")


def _validate_result_config_fields(
    result: StrategyCandidateLiquidityExitCapacityScoreV2Result,
) -> None:
    config = StrategyCandidateLiquidityExitCapacityScoreV2Config(
        config_version=result.config_version,
        watch_min_exit_depth_to_required_capacity_ratio=(
            result.watch_min_exit_depth_to_required_capacity_ratio
        ),
        block_min_exit_depth_to_required_capacity_ratio=(
            result.block_min_exit_depth_to_required_capacity_ratio
        ),
        watch_max_spread_ratio=result.watch_max_spread_ratio,
        block_max_spread_ratio=result.block_max_spread_ratio,
        watch_min_seconds_until_market_close=result.watch_min_seconds_until_market_close,
        block_min_seconds_until_market_close=result.block_min_seconds_until_market_close,
        watch_max_settlement_lag_seconds=result.watch_max_settlement_lag_seconds,
        block_max_settlement_lag_seconds=result.block_max_settlement_lag_seconds,
        urgency_capacity_buffer_ratio=result.urgency_capacity_buffer_ratio,
        close_proximity_capacity_buffer_ratio=(
            result.close_proximity_capacity_buffer_ratio
        ),
        settlement_lag_capacity_buffer_ratio=(
            result.settlement_lag_capacity_buffer_ratio
        ),
        minimum_pass_score=result.minimum_pass_score,
        blocked_max_score=result.blocked_max_score,
    )
    _validate_config(config)


def _validate_result_consistency(
    result: StrategyCandidateLiquidityExitCapacityScoreV2Result,
) -> None:
    close_pressure = _close_pressure_from_values(
        result.seconds_until_market_close,
        result.watch_min_seconds_until_market_close,
    )
    settlement_pressure = _settlement_pressure_from_values(
        result.settlement_lag_seconds,
        result.block_max_settlement_lag_seconds,
    )
    if result.close_proximity_pressure_ratio != close_pressure:
        raise ValueError("close_proximity_pressure_ratio must match input fields")
    if result.settlement_lag_pressure_ratio != settlement_pressure:
        raise ValueError("settlement_lag_pressure_ratio must match input fields")
    urgency_buffer = _money_product(
        result.expected_position_notional,
        result.urgency_ratio,
        result.urgency_capacity_buffer_ratio,
    )
    close_buffer = _money_product(
        result.expected_position_notional,
        close_pressure,
        result.close_proximity_capacity_buffer_ratio,
    )
    settlement_buffer = _money_product(
        result.expected_position_notional,
        settlement_pressure,
        result.settlement_lag_capacity_buffer_ratio,
    )
    if result.urgency_capacity_buffer_notional != urgency_buffer:
        raise ValueError("urgency_capacity_buffer_notional must match input fields")
    if result.close_proximity_capacity_buffer_notional != close_buffer:
        raise ValueError(
            "close_proximity_capacity_buffer_notional must match input fields",
        )
    if result.settlement_lag_capacity_buffer_notional != settlement_buffer:
        raise ValueError(
            "settlement_lag_capacity_buffer_notional must match input fields",
        )
    required_capacity = _add_money(
        result.expected_position_notional,
        urgency_buffer,
        close_buffer,
        settlement_buffer,
    )
    if result.required_exit_capacity_notional != required_capacity:
        raise ValueError("required_exit_capacity_notional must match input fields")
    depth_ratio = _ratio(result.book_depth_notional, result.required_exit_capacity_notional)
    if result.exit_depth_to_required_capacity_ratio != depth_ratio:
        raise ValueError("exit_depth_to_required_capacity_ratio must match input fields")
    shortfall = max(
        result.required_exit_capacity_notional - result.book_depth_notional,
        ZERO,
    ).quantize(QUANTUM)
    if result.capacity_shortfall_notional != shortfall:
        raise ValueError("capacity_shortfall_notional must match input fields")
    if result.depth_capacity_score != _depth_score_from_values(
        result.exit_depth_to_required_capacity_ratio,
        result.watch_min_exit_depth_to_required_capacity_ratio,
    ):
        raise ValueError("depth_capacity_score must match input fields")
    if result.spread_score != _spread_score_from_values(
        result.spread_ratio,
        result.block_max_spread_ratio,
    ):
        raise ValueError("spread_score must match input fields")
    if result.urgency_score != _unit_inverse_score(result.urgency_ratio):
        raise ValueError("urgency_score must match input fields")
    if result.close_proximity_score != _unit_inverse_score(
        result.close_proximity_pressure_ratio,
    ):
        raise ValueError("close_proximity_score must match input fields")
    if result.settlement_lag_score != _settlement_score_from_values(
        result.settlement_lag_seconds,
        result.block_max_settlement_lag_seconds,
    ):
        raise ValueError("settlement_lag_score must match input fields")
    expected_score = _weighted_score(
        depth_score=result.depth_capacity_score,
        spread_score=result.spread_score,
        urgency_score=result.urgency_score,
        close_score=result.close_proximity_score,
        settlement_score=result.settlement_lag_score,
    )
    if result.exit_capacity_score != expected_score:
        raise ValueError("exit_capacity_score must match component scores")
    expected_status = _status_from_values(
        depth_ratio=result.exit_depth_to_required_capacity_ratio,
        spread_ratio=result.spread_ratio,
        seconds_until_market_close=result.seconds_until_market_close,
        settlement_lag_seconds=result.settlement_lag_seconds,
        score_value=result.exit_capacity_score,
        block_min_exit_depth_to_required_capacity_ratio=(
            result.block_min_exit_depth_to_required_capacity_ratio
        ),
        watch_min_exit_depth_to_required_capacity_ratio=(
            result.watch_min_exit_depth_to_required_capacity_ratio
        ),
        block_max_spread_ratio=result.block_max_spread_ratio,
        watch_max_spread_ratio=result.watch_max_spread_ratio,
        block_min_seconds_until_market_close=(
            result.block_min_seconds_until_market_close
        ),
        watch_min_seconds_until_market_close=(
            result.watch_min_seconds_until_market_close
        ),
        block_max_settlement_lag_seconds=result.block_max_settlement_lag_seconds,
        watch_max_settlement_lag_seconds=result.watch_max_settlement_lag_seconds,
        blocked_max_score=result.blocked_max_score,
        minimum_pass_score=result.minimum_pass_score,
    )
    if result.exit_capacity_status != expected_status:
        raise ValueError("exit_capacity_status must match input fields")
    if result.capacity_decision != _capacity_decision(result.exit_capacity_status):
        raise ValueError("capacity_decision must match exit_capacity_status")


def _close_proximity_pressure(
    capacity_input: StrategyCandidateLiquidityExitCapacityScoreV2Input,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> Decimal:
    return _close_pressure_from_values(
        capacity_input.seconds_until_market_close,
        config.watch_min_seconds_until_market_close,
    )


def _close_pressure_from_values(
    seconds_until_market_close: Decimal,
    watch_min_seconds_until_market_close: Decimal,
) -> Decimal:
    if seconds_until_market_close >= watch_min_seconds_until_market_close:
        return ZERO
    return _bounded_unit_ratio(
        (watch_min_seconds_until_market_close - seconds_until_market_close)
        / watch_min_seconds_until_market_close,
    )


def _settlement_lag_pressure(
    capacity_input: StrategyCandidateLiquidityExitCapacityScoreV2Input,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> Decimal:
    return _settlement_pressure_from_values(
        capacity_input.settlement_lag_seconds,
        config.block_max_settlement_lag_seconds,
    )


def _settlement_pressure_from_values(
    settlement_lag_seconds: Decimal,
    block_max_settlement_lag_seconds: Decimal,
) -> Decimal:
    return _bounded_unit_ratio(settlement_lag_seconds / block_max_settlement_lag_seconds)


def _depth_capacity_score(
    depth_ratio: Decimal,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> Decimal:
    return _depth_score_from_values(
        depth_ratio,
        config.watch_min_exit_depth_to_required_capacity_ratio,
    )


def _depth_score_from_values(
    depth_ratio: Decimal,
    watch_min_exit_depth_to_required_capacity_ratio: Decimal,
) -> Decimal:
    if depth_ratio >= watch_min_exit_depth_to_required_capacity_ratio:
        return HUNDRED
    return _normalize_score(
        "depth_capacity_score",
        depth_ratio / watch_min_exit_depth_to_required_capacity_ratio * HUNDRED,
    )


def _spread_score(
    spread_ratio: Decimal,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> Decimal:
    return _spread_score_from_values(spread_ratio, config.block_max_spread_ratio)


def _spread_score_from_values(
    spread_ratio: Decimal,
    block_max_spread_ratio: Decimal,
) -> Decimal:
    if spread_ratio >= block_max_spread_ratio:
        return ZERO
    return _normalize_score(
        "spread_score",
        HUNDRED - spread_ratio / block_max_spread_ratio * HUNDRED,
    )


def _settlement_lag_score(
    capacity_input: StrategyCandidateLiquidityExitCapacityScoreV2Input,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> Decimal:
    return _settlement_score_from_values(
        capacity_input.settlement_lag_seconds,
        config.block_max_settlement_lag_seconds,
    )


def _settlement_score_from_values(
    settlement_lag_seconds: Decimal,
    block_max_settlement_lag_seconds: Decimal,
) -> Decimal:
    if settlement_lag_seconds >= block_max_settlement_lag_seconds:
        return ZERO
    return _normalize_score(
        "settlement_lag_score",
        HUNDRED - settlement_lag_seconds / block_max_settlement_lag_seconds * HUNDRED,
    )


def _unit_inverse_score(value: Decimal) -> Decimal:
    return _normalize_score("unit_inverse_score", (ONE - value) * HUNDRED)


def _weighted_score(
    *,
    depth_score: Decimal,
    spread_score: Decimal,
    urgency_score: Decimal,
    close_score: Decimal,
    settlement_score: Decimal,
) -> Decimal:
    return _normalize_score(
        "exit_capacity_score",
        depth_score * DEPTH_SCORE_WEIGHT
        + spread_score * SPREAD_SCORE_WEIGHT
        + urgency_score * URGENCY_SCORE_WEIGHT
        + close_score * CLOSE_SCORE_WEIGHT
        + settlement_score * SETTLEMENT_SCORE_WEIGHT,
    )


def _status(
    capacity_input: StrategyCandidateLiquidityExitCapacityScoreV2Input,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
    *,
    depth_ratio: Decimal,
    score_value: Decimal,
) -> str:
    return _status_from_values(
        depth_ratio=depth_ratio,
        spread_ratio=capacity_input.spread_ratio,
        seconds_until_market_close=capacity_input.seconds_until_market_close,
        settlement_lag_seconds=capacity_input.settlement_lag_seconds,
        score_value=score_value,
        block_min_exit_depth_to_required_capacity_ratio=(
            config.block_min_exit_depth_to_required_capacity_ratio
        ),
        watch_min_exit_depth_to_required_capacity_ratio=(
            config.watch_min_exit_depth_to_required_capacity_ratio
        ),
        block_max_spread_ratio=config.block_max_spread_ratio,
        watch_max_spread_ratio=config.watch_max_spread_ratio,
        block_min_seconds_until_market_close=(
            config.block_min_seconds_until_market_close
        ),
        watch_min_seconds_until_market_close=(
            config.watch_min_seconds_until_market_close
        ),
        block_max_settlement_lag_seconds=config.block_max_settlement_lag_seconds,
        watch_max_settlement_lag_seconds=config.watch_max_settlement_lag_seconds,
        blocked_max_score=config.blocked_max_score,
        minimum_pass_score=config.minimum_pass_score,
    )


def _status_from_values(
    *,
    depth_ratio: Decimal,
    spread_ratio: Decimal,
    seconds_until_market_close: Decimal,
    settlement_lag_seconds: Decimal,
    score_value: Decimal,
    block_min_exit_depth_to_required_capacity_ratio: Decimal,
    watch_min_exit_depth_to_required_capacity_ratio: Decimal,
    block_max_spread_ratio: Decimal,
    watch_max_spread_ratio: Decimal,
    block_min_seconds_until_market_close: Decimal,
    watch_min_seconds_until_market_close: Decimal,
    block_max_settlement_lag_seconds: Decimal,
    watch_max_settlement_lag_seconds: Decimal,
    blocked_max_score: Decimal,
    minimum_pass_score: Decimal,
) -> str:
    if (
        depth_ratio < block_min_exit_depth_to_required_capacity_ratio
        or spread_ratio > block_max_spread_ratio
        or seconds_until_market_close < block_min_seconds_until_market_close
        or settlement_lag_seconds > block_max_settlement_lag_seconds
        or score_value <= blocked_max_score
    ):
        return "blocked"
    if (
        depth_ratio < watch_min_exit_depth_to_required_capacity_ratio
        or spread_ratio > watch_max_spread_ratio
        or seconds_until_market_close < watch_min_seconds_until_market_close
        or settlement_lag_seconds > watch_max_settlement_lag_seconds
        or score_value < minimum_pass_score
    ):
        return "watch"
    return "pass"


def _capacity_decision(status: str) -> str:
    if status == "pass":
        return "paper_candidate"
    if status == "watch":
        return "manual_review"
    if status == "blocked":
        return "reject"
    raise ValueError("exit_capacity_status must be supported")


def _reason_codes(
    existing: tuple[str, ...],
    *,
    status: str,
    capacity_input: StrategyCandidateLiquidityExitCapacityScoreV2Input,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
    depth_ratio: Decimal,
    capacity_shortfall: Decimal,
    score_value: Decimal,
) -> tuple[str, ...]:
    additions = [
        "strategy_candidate_liquidity_exit_capacity_score_v2",
        f"exit_capacity_{status}",
        _depth_reason_code(depth_ratio, config),
        _spread_reason_code(capacity_input.spread_ratio, config),
        _urgency_reason_code(capacity_input.urgency_ratio),
        _close_reason_code(capacity_input.seconds_until_market_close, config),
        _settlement_reason_code(capacity_input.settlement_lag_seconds, config),
    ]
    if capacity_shortfall > ZERO:
        additions.append("capacity_shortfall")
    additions.append(_score_reason_code(score_value, config))
    return _append_reason_codes(existing, tuple(additions))


def _depth_reason_code(
    depth_ratio: Decimal,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> str:
    if depth_ratio < config.block_min_exit_depth_to_required_capacity_ratio:
        return "depth_capacity_below_block"
    if depth_ratio < config.watch_min_exit_depth_to_required_capacity_ratio:
        return "depth_capacity_below_watch"
    return "depth_capacity_sufficient"


def _spread_reason_code(
    spread_ratio: Decimal,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> str:
    if spread_ratio > config.block_max_spread_ratio:
        return "spread_block"
    if spread_ratio > config.watch_max_spread_ratio:
        return "spread_watch"
    if spread_ratio == ZERO:
        return "spread_zero"
    return "spread_inside_limit"


def _urgency_reason_code(urgency_ratio: Decimal) -> str:
    if urgency_ratio == ZERO:
        return "urgency_clear"
    return "urgency_pressure_applied"


def _close_reason_code(
    seconds_until_market_close: Decimal,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> str:
    if seconds_until_market_close < config.block_min_seconds_until_market_close:
        return "close_proximity_block"
    if seconds_until_market_close < config.watch_min_seconds_until_market_close:
        return "close_proximity_watch"
    return "close_proximity_clear"


def _settlement_reason_code(
    settlement_lag_seconds: Decimal,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> str:
    if settlement_lag_seconds > config.block_max_settlement_lag_seconds:
        return "settlement_lag_block"
    if settlement_lag_seconds > config.watch_max_settlement_lag_seconds:
        return "settlement_lag_watch"
    return "settlement_lag_clear"


def _score_reason_code(
    score_value: Decimal,
    config: StrategyCandidateLiquidityExitCapacityScoreV2Config,
) -> str:
    if score_value <= config.blocked_max_score:
        return "score_below_block"
    if score_value < config.minimum_pass_score:
        return "score_below_pass"
    return "score_pass"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = list(existing)
    for addition in additions:
        if addition not in reason_codes:
            reason_codes.append(addition)
    return tuple(reason_codes)


def _money_product(
    value: Decimal,
    first_ratio: Decimal,
    second_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (value * first_ratio * second_ratio).quantize(QUANTUM)


def _add_money(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _bounded_unit_ratio(value: Decimal) -> Decimal:
    normalized = _normalize_ratio("bounded_unit_ratio", value)
    if normalized > ONE:
        return ONE
    return normalized


def _derived_validation_digest(
    result: StrategyCandidateLiquidityExitCapacityScoreV2Result,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _normalize_positive_money(field_name: str, value: object) -> Decimal:
    normalized = _normalize_money(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_money(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_unit_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_ratio(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return normalized


def _normalize_seconds(field_name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > HUNDRED:
        raise ValueError(f"{field_name} must be <= 100")
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
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_LIQUIDITY_EXIT_CAPACITY_SCORE_V2_CONFIG_VERSION",
    "EXIT_CAPACITY_STATUSES",
    "CAPACITY_DECISIONS",
    "StrategyCandidateLiquidityExitCapacityScoreV2Config",
    "StrategyCandidateLiquidityExitCapacityScoreV2Input",
    "StrategyCandidateLiquidityExitCapacityScoreV2Result",
    "score_strategy_candidate_liquidity_exit_capacity_v2",
    "strategy_candidate_liquidity_exit_capacity_score_v2_payload",
    "reject_strategy_candidate_liquidity_exit_capacity_score_v2_unsafe_payload",
)
