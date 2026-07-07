"""Pure Phase 1 candidate edge buffer scorer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_CONFIDENCE_EDGE_BUFFER_V2_CONFIG_VERSION = (
    "strategy-candidate-resolution-confidence-edge-buffer-v2"
)
EDGE_BUFFER_STATUSES = ("pass", "watch", "blocked")
EDGE_BUFFER_DECISIONS = ("paper_candidate", "manual_review", "reject")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HUNDRED = Decimal("100.000000")
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


@dataclass(frozen=True)
class StrategyCandidateResolutionConfidenceEdgeBufferV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_CONFIDENCE_EDGE_BUFFER_V2_CONFIG_VERSION
    )
    pass_min_edge_buffer: Decimal = Decimal("0.020000")
    watch_min_edge_buffer: Decimal = Decimal("0.000000")
    watch_min_resolution_confidence_score: Decimal = Decimal("0.750000")
    block_min_resolution_confidence_score: Decimal = Decimal("0.500000")
    watch_min_source_hierarchy_score: Decimal = Decimal("0.750000")
    block_min_source_hierarchy_score: Decimal = Decimal("0.500000")
    watch_max_contradiction_severity: Decimal = Decimal("0.300000")
    block_max_contradiction_severity: Decimal = Decimal("0.700000")
    watch_max_settlement_lag_seconds: Decimal = Decimal("86400.000000")
    block_max_settlement_lag_seconds: Decimal = Decimal("259200.000000")
    watch_max_liquidity_exit_risk: Decimal = Decimal("0.300000")
    block_max_liquidity_exit_risk: Decimal = Decimal("0.700000")
    resolution_confidence_buffer_weight: Decimal = Decimal("0.050000")
    source_hierarchy_buffer_weight: Decimal = Decimal("0.030000")
    contradiction_buffer_weight: Decimal = Decimal("0.040000")
    settlement_lag_buffer_weight: Decimal = Decimal("0.020000")
    liquidity_exit_risk_buffer_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionConfidenceEdgeBufferV2Config:
            raise ValueError(
                "config must be a StrategyCandidateResolutionConfidenceEdgeBufferV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_min_edge_buffer",
            "watch_min_edge_buffer",
            "watch_max_settlement_lag_seconds",
            "block_max_settlement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_min_resolution_confidence_score",
            "block_min_resolution_confidence_score",
            "watch_min_source_hierarchy_score",
            "block_min_source_hierarchy_score",
            "watch_max_contradiction_severity",
            "block_max_contradiction_severity",
            "watch_max_liquidity_exit_risk",
            "block_max_liquidity_exit_risk",
            "resolution_confidence_buffer_weight",
            "source_hierarchy_buffer_weight",
            "contradiction_buffer_weight",
            "settlement_lag_buffer_weight",
            "liquidity_exit_risk_buffer_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionConfidenceEdgeBufferV2Input:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    candidate_edge: Decimal
    resolution_confidence_score: Decimal
    source_hierarchy_score: Decimal
    contradiction_severity: Decimal
    settlement_lag_seconds: Decimal
    taker_edge_cost: Decimal
    spread_edge_cost: Decimal
    slippage_edge_cost: Decimal
    liquidity_exit_risk: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionConfidenceEdgeBufferV2Input:
            raise ValueError(
                "input must be a StrategyCandidateResolutionConfidenceEdgeBufferV2Input",
            )
        for field_name in ("candidate_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "candidate_edge",
            _normalize_decimal("candidate_edge", self.candidate_edge),
        )
        for field_name in (
            "resolution_confidence_score",
            "source_hierarchy_score",
            "contradiction_severity",
            "liquidity_exit_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "settlement_lag_seconds",
            "taker_edge_cost",
            "spread_edge_cost",
            "slippage_edge_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("input", self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionConfidenceEdgeBufferV2Result:
    candidate_id: str
    market_slug: str
    observed_at: datetime
    config_version: str
    candidate_edge: Decimal
    resolution_confidence_score: Decimal
    source_hierarchy_score: Decimal
    contradiction_severity: Decimal
    settlement_lag_seconds: Decimal
    taker_edge_cost: Decimal
    spread_edge_cost: Decimal
    slippage_edge_cost: Decimal
    liquidity_exit_risk: Decimal
    pass_min_edge_buffer: Decimal
    watch_min_edge_buffer: Decimal
    watch_min_resolution_confidence_score: Decimal
    block_min_resolution_confidence_score: Decimal
    watch_min_source_hierarchy_score: Decimal
    block_min_source_hierarchy_score: Decimal
    watch_max_contradiction_severity: Decimal
    block_max_contradiction_severity: Decimal
    watch_max_settlement_lag_seconds: Decimal
    block_max_settlement_lag_seconds: Decimal
    watch_max_liquidity_exit_risk: Decimal
    block_max_liquidity_exit_risk: Decimal
    resolution_confidence_buffer_weight: Decimal
    source_hierarchy_buffer_weight: Decimal
    contradiction_buffer_weight: Decimal
    settlement_lag_buffer_weight: Decimal
    liquidity_exit_risk_buffer_weight: Decimal
    resolution_confidence_buffer: Decimal
    source_hierarchy_buffer: Decimal
    contradiction_buffer: Decimal
    settlement_lag_pressure_ratio: Decimal
    settlement_lag_buffer: Decimal
    liquidity_exit_buffer: Decimal
    total_risk_buffer: Decimal
    total_cost_buffer: Decimal
    required_edge_buffer: Decimal
    edge_buffer: Decimal
    edge_buffer_shortfall: Decimal
    edge_buffer_score: Decimal
    edge_buffer_status: str
    candidate_decision: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionConfidenceEdgeBufferV2Result:
            raise ValueError(
                "result must be a StrategyCandidateResolutionConfidenceEdgeBufferV2Result",
            )
        for field_name in ("candidate_id", "market_slug", "config_version"):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "candidate_edge",
            "edge_buffer",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolution_confidence_score",
            "source_hierarchy_score",
            "contradiction_severity",
            "liquidity_exit_risk",
            "watch_min_resolution_confidence_score",
            "block_min_resolution_confidence_score",
            "watch_min_source_hierarchy_score",
            "block_min_source_hierarchy_score",
            "watch_max_contradiction_severity",
            "block_max_contradiction_severity",
            "watch_max_liquidity_exit_risk",
            "block_max_liquidity_exit_risk",
            "resolution_confidence_buffer_weight",
            "source_hierarchy_buffer_weight",
            "contradiction_buffer_weight",
            "settlement_lag_buffer_weight",
            "liquidity_exit_risk_buffer_weight",
            "settlement_lag_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "settlement_lag_seconds",
            "taker_edge_cost",
            "spread_edge_cost",
            "slippage_edge_cost",
            "pass_min_edge_buffer",
            "watch_min_edge_buffer",
            "watch_max_settlement_lag_seconds",
            "block_max_settlement_lag_seconds",
            "resolution_confidence_buffer",
            "source_hierarchy_buffer",
            "contradiction_buffer",
            "settlement_lag_buffer",
            "liquidity_exit_buffer",
            "total_risk_buffer",
            "total_cost_buffer",
            "required_edge_buffer",
            "edge_buffer_shortfall",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_buffer_score",
            _normalize_score("edge_buffer_score", self.edge_buffer_score),
        )
        _require_member("edge_buffer_status", self.edge_buffer_status, EDGE_BUFFER_STATUSES)
        _require_member("candidate_decision", self.candidate_decision, EDGE_BUFFER_DECISIONS)
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
        return strategy_candidate_resolution_confidence_edge_buffer_v2_payload(self)


def score_strategy_candidate_resolution_confidence_edge_buffer_v2(
    edge_input: StrategyCandidateResolutionConfidenceEdgeBufferV2Input,
    *,
    config: StrategyCandidateResolutionConfidenceEdgeBufferV2Config | None = None,
) -> StrategyCandidateResolutionConfidenceEdgeBufferV2Result:
    if type(edge_input) is not StrategyCandidateResolutionConfidenceEdgeBufferV2Input:
        raise ValueError(
            "input must be a StrategyCandidateResolutionConfidenceEdgeBufferV2Input",
        )
    if config is None:
        config = StrategyCandidateResolutionConfidenceEdgeBufferV2Config()
    if type(config) is not StrategyCandidateResolutionConfidenceEdgeBufferV2Config:
        raise ValueError(
            "config must be a StrategyCandidateResolutionConfidenceEdgeBufferV2Config",
        )
    _reject_unsafe_public_payload("input", edge_input)
    _reject_unsafe_public_payload("config", config)
    _require_hard_flags("input", edge_input)
    _require_hard_flags("config", config)

    resolution_buffer = _product(
        ONE - edge_input.resolution_confidence_score,
        config.resolution_confidence_buffer_weight,
    )
    source_buffer = _product(
        ONE - edge_input.source_hierarchy_score,
        config.source_hierarchy_buffer_weight,
    )
    contradiction_buffer = _product(
        edge_input.contradiction_severity,
        config.contradiction_buffer_weight,
    )
    settlement_pressure = _settlement_lag_pressure(
        edge_input.settlement_lag_seconds,
        config.block_max_settlement_lag_seconds,
    )
    settlement_buffer = _product(
        settlement_pressure,
        config.settlement_lag_buffer_weight,
    )
    liquidity_buffer = _product(
        edge_input.liquidity_exit_risk,
        config.liquidity_exit_risk_buffer_weight,
    )
    total_risk_buffer = _add_decimals(
        resolution_buffer,
        source_buffer,
        contradiction_buffer,
        settlement_buffer,
        liquidity_buffer,
    )
    total_cost_buffer = _add_decimals(
        edge_input.taker_edge_cost,
        edge_input.spread_edge_cost,
        edge_input.slippage_edge_cost,
    )
    required_edge_buffer = _add_decimals(total_risk_buffer, total_cost_buffer)
    edge_buffer = _subtract_decimal(edge_input.candidate_edge, required_edge_buffer)
    edge_buffer_shortfall = _edge_buffer_shortfall(
        edge_buffer,
        config.watch_min_edge_buffer,
    )
    edge_buffer_score = _edge_buffer_score(edge_buffer, config.pass_min_edge_buffer)
    status = _edge_buffer_status(
        resolution_confidence_score=edge_input.resolution_confidence_score,
        source_hierarchy_score=edge_input.source_hierarchy_score,
        contradiction_severity=edge_input.contradiction_severity,
        settlement_lag_seconds=edge_input.settlement_lag_seconds,
        liquidity_exit_risk=edge_input.liquidity_exit_risk,
        edge_buffer=edge_buffer,
        config=config,
    )

    return StrategyCandidateResolutionConfidenceEdgeBufferV2Result(
        candidate_id=edge_input.candidate_id,
        market_slug=edge_input.market_slug,
        observed_at=edge_input.observed_at,
        config_version=config.config_version,
        candidate_edge=edge_input.candidate_edge,
        resolution_confidence_score=edge_input.resolution_confidence_score,
        source_hierarchy_score=edge_input.source_hierarchy_score,
        contradiction_severity=edge_input.contradiction_severity,
        settlement_lag_seconds=edge_input.settlement_lag_seconds,
        taker_edge_cost=edge_input.taker_edge_cost,
        spread_edge_cost=edge_input.spread_edge_cost,
        slippage_edge_cost=edge_input.slippage_edge_cost,
        liquidity_exit_risk=edge_input.liquidity_exit_risk,
        pass_min_edge_buffer=config.pass_min_edge_buffer,
        watch_min_edge_buffer=config.watch_min_edge_buffer,
        watch_min_resolution_confidence_score=(
            config.watch_min_resolution_confidence_score
        ),
        block_min_resolution_confidence_score=(
            config.block_min_resolution_confidence_score
        ),
        watch_min_source_hierarchy_score=config.watch_min_source_hierarchy_score,
        block_min_source_hierarchy_score=config.block_min_source_hierarchy_score,
        watch_max_contradiction_severity=config.watch_max_contradiction_severity,
        block_max_contradiction_severity=config.block_max_contradiction_severity,
        watch_max_settlement_lag_seconds=config.watch_max_settlement_lag_seconds,
        block_max_settlement_lag_seconds=config.block_max_settlement_lag_seconds,
        watch_max_liquidity_exit_risk=config.watch_max_liquidity_exit_risk,
        block_max_liquidity_exit_risk=config.block_max_liquidity_exit_risk,
        resolution_confidence_buffer_weight=(
            config.resolution_confidence_buffer_weight
        ),
        source_hierarchy_buffer_weight=config.source_hierarchy_buffer_weight,
        contradiction_buffer_weight=config.contradiction_buffer_weight,
        settlement_lag_buffer_weight=config.settlement_lag_buffer_weight,
        liquidity_exit_risk_buffer_weight=config.liquidity_exit_risk_buffer_weight,
        resolution_confidence_buffer=resolution_buffer,
        source_hierarchy_buffer=source_buffer,
        contradiction_buffer=contradiction_buffer,
        settlement_lag_pressure_ratio=settlement_pressure,
        settlement_lag_buffer=settlement_buffer,
        liquidity_exit_buffer=liquidity_buffer,
        total_risk_buffer=total_risk_buffer,
        total_cost_buffer=total_cost_buffer,
        required_edge_buffer=required_edge_buffer,
        edge_buffer=edge_buffer,
        edge_buffer_shortfall=edge_buffer_shortfall,
        edge_buffer_score=edge_buffer_score,
        edge_buffer_status=status,
        candidate_decision=_candidate_decision(status),
        reason_codes=_reason_codes(
            edge_input.reason_codes,
            status=status,
            resolution_confidence_score=edge_input.resolution_confidence_score,
            source_hierarchy_score=edge_input.source_hierarchy_score,
            contradiction_severity=edge_input.contradiction_severity,
            settlement_lag_seconds=edge_input.settlement_lag_seconds,
            liquidity_exit_risk=edge_input.liquidity_exit_risk,
            total_cost_buffer=total_cost_buffer,
            edge_buffer=edge_buffer,
            config=config,
        ),
    )


def strategy_candidate_resolution_confidence_edge_buffer_v2_payload(
    result: StrategyCandidateResolutionConfidenceEdgeBufferV2Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateResolutionConfidenceEdgeBufferV2Result:
        raise ValueError(
            "result must be a StrategyCandidateResolutionConfidenceEdgeBufferV2Result",
        )
    _require_hard_flags("result", result)
    _validate_result_consistency(result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    _reject_unsafe_public_payload("result", result)
    return _json_ready(asdict(result))


def reject_strategy_candidate_resolution_confidence_edge_buffer_v2_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    _reject_unsafe_public_payload(label, payload)


def _validate_config(
    config: StrategyCandidateResolutionConfidenceEdgeBufferV2Config,
) -> None:
    if config.watch_min_edge_buffer > config.pass_min_edge_buffer:
        raise ValueError("watch_min_edge_buffer must be <= pass_min_edge_buffer")
    if (
        config.block_min_resolution_confidence_score
        > config.watch_min_resolution_confidence_score
    ):
        raise ValueError(
            "block_min_resolution_confidence_score must be <= watch threshold",
        )
    if config.block_min_source_hierarchy_score > config.watch_min_source_hierarchy_score:
        raise ValueError("block_min_source_hierarchy_score must be <= watch threshold")
    if (
        config.watch_max_contradiction_severity
        > config.block_max_contradiction_severity
    ):
        raise ValueError(
            "watch_max_contradiction_severity must be <= block threshold",
        )
    if config.watch_max_settlement_lag_seconds > config.block_max_settlement_lag_seconds:
        raise ValueError(
            "watch_max_settlement_lag_seconds must be <= block threshold",
        )
    if config.block_max_settlement_lag_seconds <= ZERO:
        raise ValueError("block_max_settlement_lag_seconds must be positive")
    if config.watch_max_liquidity_exit_risk > config.block_max_liquidity_exit_risk:
        raise ValueError("watch_max_liquidity_exit_risk must be <= block threshold")


def _validate_result_config_fields(
    result: StrategyCandidateResolutionConfidenceEdgeBufferV2Result,
) -> None:
    config = StrategyCandidateResolutionConfidenceEdgeBufferV2Config(
        config_version=result.config_version,
        pass_min_edge_buffer=result.pass_min_edge_buffer,
        watch_min_edge_buffer=result.watch_min_edge_buffer,
        watch_min_resolution_confidence_score=(
            result.watch_min_resolution_confidence_score
        ),
        block_min_resolution_confidence_score=(
            result.block_min_resolution_confidence_score
        ),
        watch_min_source_hierarchy_score=result.watch_min_source_hierarchy_score,
        block_min_source_hierarchy_score=result.block_min_source_hierarchy_score,
        watch_max_contradiction_severity=result.watch_max_contradiction_severity,
        block_max_contradiction_severity=result.block_max_contradiction_severity,
        watch_max_settlement_lag_seconds=result.watch_max_settlement_lag_seconds,
        block_max_settlement_lag_seconds=result.block_max_settlement_lag_seconds,
        watch_max_liquidity_exit_risk=result.watch_max_liquidity_exit_risk,
        block_max_liquidity_exit_risk=result.block_max_liquidity_exit_risk,
        resolution_confidence_buffer_weight=(
            result.resolution_confidence_buffer_weight
        ),
        source_hierarchy_buffer_weight=result.source_hierarchy_buffer_weight,
        contradiction_buffer_weight=result.contradiction_buffer_weight,
        settlement_lag_buffer_weight=result.settlement_lag_buffer_weight,
        liquidity_exit_risk_buffer_weight=result.liquidity_exit_risk_buffer_weight,
    )
    _validate_config(config)


def _validate_result_consistency(
    result: StrategyCandidateResolutionConfidenceEdgeBufferV2Result,
) -> None:
    resolution_buffer = _product(
        ONE - result.resolution_confidence_score,
        result.resolution_confidence_buffer_weight,
    )
    if result.resolution_confidence_buffer != resolution_buffer:
        raise ValueError("resolution_confidence_buffer must match input fields")
    source_buffer = _product(
        ONE - result.source_hierarchy_score,
        result.source_hierarchy_buffer_weight,
    )
    if result.source_hierarchy_buffer != source_buffer:
        raise ValueError("source_hierarchy_buffer must match input fields")
    contradiction_buffer = _product(
        result.contradiction_severity,
        result.contradiction_buffer_weight,
    )
    if result.contradiction_buffer != contradiction_buffer:
        raise ValueError("contradiction_buffer must match input fields")
    settlement_pressure = _settlement_lag_pressure(
        result.settlement_lag_seconds,
        result.block_max_settlement_lag_seconds,
    )
    if result.settlement_lag_pressure_ratio != settlement_pressure:
        raise ValueError("settlement_lag_pressure_ratio must match input fields")
    settlement_buffer = _product(
        settlement_pressure,
        result.settlement_lag_buffer_weight,
    )
    if result.settlement_lag_buffer != settlement_buffer:
        raise ValueError("settlement_lag_buffer must match input fields")
    liquidity_buffer = _product(
        result.liquidity_exit_risk,
        result.liquidity_exit_risk_buffer_weight,
    )
    if result.liquidity_exit_buffer != liquidity_buffer:
        raise ValueError("liquidity_exit_buffer must match input fields")
    total_risk_buffer = _add_decimals(
        resolution_buffer,
        source_buffer,
        contradiction_buffer,
        settlement_buffer,
        liquidity_buffer,
    )
    if result.total_risk_buffer != total_risk_buffer:
        raise ValueError("total_risk_buffer must match input fields")
    total_cost_buffer = _add_decimals(
        result.taker_edge_cost,
        result.spread_edge_cost,
        result.slippage_edge_cost,
    )
    if result.total_cost_buffer != total_cost_buffer:
        raise ValueError("total_cost_buffer must match input fields")
    required_edge_buffer = _add_decimals(total_risk_buffer, total_cost_buffer)
    if result.required_edge_buffer != required_edge_buffer:
        raise ValueError("required_edge_buffer must match input fields")
    edge_buffer = _subtract_decimal(result.candidate_edge, result.required_edge_buffer)
    if result.edge_buffer != edge_buffer:
        raise ValueError("edge_buffer must match candidate edge and requirements")
    shortfall = _edge_buffer_shortfall(edge_buffer, result.watch_min_edge_buffer)
    if result.edge_buffer_shortfall != shortfall:
        raise ValueError("edge_buffer_shortfall must match edge_buffer")
    score_value = _edge_buffer_score(edge_buffer, result.pass_min_edge_buffer)
    if result.edge_buffer_score != score_value:
        raise ValueError("edge_buffer_score must match edge_buffer")

    config = StrategyCandidateResolutionConfidenceEdgeBufferV2Config(
        config_version=result.config_version,
        pass_min_edge_buffer=result.pass_min_edge_buffer,
        watch_min_edge_buffer=result.watch_min_edge_buffer,
        watch_min_resolution_confidence_score=(
            result.watch_min_resolution_confidence_score
        ),
        block_min_resolution_confidence_score=(
            result.block_min_resolution_confidence_score
        ),
        watch_min_source_hierarchy_score=result.watch_min_source_hierarchy_score,
        block_min_source_hierarchy_score=result.block_min_source_hierarchy_score,
        watch_max_contradiction_severity=result.watch_max_contradiction_severity,
        block_max_contradiction_severity=result.block_max_contradiction_severity,
        watch_max_settlement_lag_seconds=result.watch_max_settlement_lag_seconds,
        block_max_settlement_lag_seconds=result.block_max_settlement_lag_seconds,
        watch_max_liquidity_exit_risk=result.watch_max_liquidity_exit_risk,
        block_max_liquidity_exit_risk=result.block_max_liquidity_exit_risk,
        resolution_confidence_buffer_weight=(
            result.resolution_confidence_buffer_weight
        ),
        source_hierarchy_buffer_weight=result.source_hierarchy_buffer_weight,
        contradiction_buffer_weight=result.contradiction_buffer_weight,
        settlement_lag_buffer_weight=result.settlement_lag_buffer_weight,
        liquidity_exit_risk_buffer_weight=result.liquidity_exit_risk_buffer_weight,
    )
    status = _edge_buffer_status(
        resolution_confidence_score=result.resolution_confidence_score,
        source_hierarchy_score=result.source_hierarchy_score,
        contradiction_severity=result.contradiction_severity,
        settlement_lag_seconds=result.settlement_lag_seconds,
        liquidity_exit_risk=result.liquidity_exit_risk,
        edge_buffer=result.edge_buffer,
        config=config,
    )
    if result.edge_buffer_status != status:
        raise ValueError("edge_buffer_status must match input fields")
    if result.candidate_decision != _candidate_decision(result.edge_buffer_status):
        raise ValueError("candidate_decision must match edge_buffer_status")
    expected_reasons = _reason_codes(
        _source_reason_codes(result.reason_codes),
        status=result.edge_buffer_status,
        resolution_confidence_score=result.resolution_confidence_score,
        source_hierarchy_score=result.source_hierarchy_score,
        contradiction_severity=result.contradiction_severity,
        settlement_lag_seconds=result.settlement_lag_seconds,
        liquidity_exit_risk=result.liquidity_exit_risk,
        total_cost_buffer=result.total_cost_buffer,
        edge_buffer=result.edge_buffer,
        config=config,
    )
    if result.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match input fields")


def _edge_buffer_status(
    *,
    resolution_confidence_score: Decimal,
    source_hierarchy_score: Decimal,
    contradiction_severity: Decimal,
    settlement_lag_seconds: Decimal,
    liquidity_exit_risk: Decimal,
    edge_buffer: Decimal,
    config: StrategyCandidateResolutionConfidenceEdgeBufferV2Config,
) -> str:
    if (
        resolution_confidence_score < config.block_min_resolution_confidence_score
        or source_hierarchy_score < config.block_min_source_hierarchy_score
        or contradiction_severity >= config.block_max_contradiction_severity
        or settlement_lag_seconds >= config.block_max_settlement_lag_seconds
        or liquidity_exit_risk >= config.block_max_liquidity_exit_risk
        or edge_buffer < config.watch_min_edge_buffer
    ):
        return "blocked"
    if (
        resolution_confidence_score < config.watch_min_resolution_confidence_score
        or source_hierarchy_score < config.watch_min_source_hierarchy_score
        or contradiction_severity >= config.watch_max_contradiction_severity
        or settlement_lag_seconds >= config.watch_max_settlement_lag_seconds
        or liquidity_exit_risk >= config.watch_max_liquidity_exit_risk
        or edge_buffer < config.pass_min_edge_buffer
    ):
        return "watch"
    return "pass"


def _candidate_decision(status: str) -> str:
    if status == "pass":
        return "paper_candidate"
    if status == "watch":
        return "manual_review"
    return "reject"


def _reason_codes(
    source_reason_codes: tuple[str, ...],
    *,
    status: str,
    resolution_confidence_score: Decimal,
    source_hierarchy_score: Decimal,
    contradiction_severity: Decimal,
    settlement_lag_seconds: Decimal,
    liquidity_exit_risk: Decimal,
    total_cost_buffer: Decimal,
    edge_buffer: Decimal,
    config: StrategyCandidateResolutionConfidenceEdgeBufferV2Config,
) -> tuple[str, ...]:
    codes = list(source_reason_codes)
    codes.append("strategy_candidate_resolution_confidence_edge_buffer_v2")
    codes.append(f"edge_buffer_{status}")
    codes.append(
        _low_threshold_reason(
            "resolution_confidence",
            resolution_confidence_score,
            config.watch_min_resolution_confidence_score,
            config.block_min_resolution_confidence_score,
        ),
    )
    codes.append(
        _low_threshold_reason(
            "source_hierarchy",
            source_hierarchy_score,
            config.watch_min_source_hierarchy_score,
            config.block_min_source_hierarchy_score,
        ),
    )
    codes.append(
        _high_threshold_reason(
            "contradiction",
            contradiction_severity,
            config.watch_max_contradiction_severity,
            config.block_max_contradiction_severity,
        ),
    )
    codes.append(
        _high_threshold_reason(
            "settlement_lag",
            settlement_lag_seconds,
            config.watch_max_settlement_lag_seconds,
            config.block_max_settlement_lag_seconds,
        ),
    )
    codes.append("cost_stack_applied" if total_cost_buffer > ZERO else "cost_stack_clear")
    codes.append(
        _high_threshold_reason(
            "liquidity_exit",
            liquidity_exit_risk,
            config.watch_max_liquidity_exit_risk,
            config.block_max_liquidity_exit_risk,
        ),
    )
    codes.append(_edge_buffer_reason(edge_buffer, config))
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _source_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    marker = "strategy_candidate_resolution_confidence_edge_buffer_v2"
    if marker not in reason_codes:
        return reason_codes
    return reason_codes[: reason_codes.index(marker)]


def _low_threshold_reason(
    label: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value < block_threshold:
        return f"{label}_block"
    if value < watch_threshold:
        return f"{label}_watch"
    return f"{label}_clear"


def _high_threshold_reason(
    label: str,
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value >= block_threshold:
        return f"{label}_block"
    if value >= watch_threshold:
        return f"{label}_watch"
    return f"{label}_clear"


def _edge_buffer_reason(
    edge_buffer: Decimal,
    config: StrategyCandidateResolutionConfidenceEdgeBufferV2Config,
) -> str:
    if edge_buffer < ZERO:
        return "edge_buffer_negative"
    if edge_buffer < config.watch_min_edge_buffer:
        return "edge_buffer_below_watch"
    if edge_buffer < config.pass_min_edge_buffer:
        return "edge_buffer_below_pass"
    return "edge_buffer_cleared"


def _edge_buffer_shortfall(edge_buffer: Decimal, watch_min_edge_buffer: Decimal) -> Decimal:
    return max(watch_min_edge_buffer - edge_buffer, ZERO).quantize(QUANTUM)


def _edge_buffer_score(edge_buffer: Decimal, pass_min_edge_buffer: Decimal) -> Decimal:
    if edge_buffer <= ZERO:
        return ZERO
    if pass_min_edge_buffer <= ZERO:
        return HUNDRED
    return _normalize_score(
        "edge_buffer_score",
        min(edge_buffer / pass_min_edge_buffer * HUNDRED, HUNDRED),
    )


def _settlement_lag_pressure(
    settlement_lag_seconds: Decimal,
    block_max_settlement_lag_seconds: Decimal,
) -> Decimal:
    return _bounded_unit_ratio(settlement_lag_seconds / block_max_settlement_lag_seconds)


def _product(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _add_decimals(first: Decimal, second: Decimal, *rest: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = first + second
        for value in rest:
            total += value
        return total.quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _bounded_unit_ratio(value: Decimal) -> Decimal:
    normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _normalize_score(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > HUNDRED:
        raise ValueError(f"{field_name} must be <= 100.000000")
    return normalized


def _normalize_unit_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in normalized:
        _require_canonical_string(field_name, reason_code)
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _require_canonical_string("public_payload_key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public content in {label}")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_TERMS)


def _derived_validation_digest(
    result: StrategyCandidateResolutionConfidenceEdgeBufferV2Result,
) -> str:
    digest_input = asdict(result)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_canonical_digest(value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError("derived_validation_digest must be a sha256 hex digest")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_CONFIDENCE_EDGE_BUFFER_V2_CONFIG_VERSION",
    "EDGE_BUFFER_STATUSES",
    "EDGE_BUFFER_DECISIONS",
    "StrategyCandidateResolutionConfidenceEdgeBufferV2Config",
    "StrategyCandidateResolutionConfidenceEdgeBufferV2Input",
    "StrategyCandidateResolutionConfidenceEdgeBufferV2Result",
    "score_strategy_candidate_resolution_confidence_edge_buffer_v2",
    "strategy_candidate_resolution_confidence_edge_buffer_v2_payload",
    "reject_strategy_candidate_resolution_confidence_edge_buffer_v2_unsafe_payload",
)
