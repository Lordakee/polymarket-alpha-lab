"""Readonly Decimal gate for recommendation signal stability."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_RECOMMENDATION_SIGNAL_STABILITY_GATE_V2_CONFIG_VERSION = (
    "strategy-recommendation-signal-stability-gate-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

VALIDATION_STATUSES = ("pass", "watch", "blocked")
ROW_STATUS_RANK = {
    "blocked": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

OBSERVATION_RATIO_FIELDS = (
    "source_verified_edge_start",
    "source_verified_edge_current",
    "market_probability_start",
    "market_probability_current",
    "uncertainty_band_start",
    "uncertainty_band_current",
    "specialist_confidence_start",
    "specialist_confidence_current",
    "liquidity_exit_risk_start",
    "liquidity_exit_risk_current",
    "resolution_ambiguity_start",
    "resolution_ambiguity_current",
    "portfolio_impact_start",
    "portfolio_impact_current",
)

ROW_REASON_CODES = (
    "signal_stability_row_pass",
    "signal_stability_row_watch",
    "signal_stability_row_blocked",
    "source_verified_edge_trend_stable",
    "source_verified_edge_trend_watch",
    "source_verified_edge_trend_weak",
    "market_probability_movement_stable",
    "market_probability_movement_watch",
    "market_probability_movement_high",
    "uncertainty_band_movement_stable",
    "uncertainty_band_movement_watch",
    "uncertainty_band_movement_wide",
    "specialist_confidence_drift_stable",
    "specialist_confidence_drift_watch",
    "specialist_confidence_drift_weak",
    "liquidity_exit_risk_drift_stable",
    "liquidity_exit_risk_drift_watch",
    "liquidity_exit_risk_drift_high",
    "resolution_ambiguity_drift_stable",
    "resolution_ambiguity_drift_watch",
    "resolution_ambiguity_drift_high",
    "portfolio_impact_drift_stable",
    "portfolio_impact_drift_watch",
    "portfolio_impact_drift_high",
)
REPORT_REASON_CODES = (
    "signal_stability_gate_passed",
    "signal_stability_gate_watch_rows",
    "signal_stability_gate_blocked_rows",
    "signal_stability_gate_empty",
)
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)

__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_SIGNAL_STABILITY_GATE_V2_CONFIG_VERSION",
    "StrategyRecommendationSignalStabilityGateV2Config",
    "StrategyRecommendationSignalStabilityGateV2Observation",
    "StrategyRecommendationSignalStabilityGateV2Row",
    "StrategyRecommendationSignalStabilityGateV2Report",
    "build_strategy_recommendation_signal_stability_gate_v2",
    "strategy_recommendation_signal_stability_gate_v2_payload",
)


@dataclass(frozen=True)
class StrategyRecommendationSignalStabilityGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_SIGNAL_STABILITY_GATE_V2_CONFIG_VERSION
    )
    pass_stability_floor: Decimal = Decimal("0.950000")
    watch_stability_floor: Decimal = Decimal("0.850000")
    source_verified_edge_trend_weight: Decimal = Decimal("0.200000")
    market_probability_movement_weight: Decimal = Decimal("0.200000")
    uncertainty_band_movement_weight: Decimal = Decimal("0.120000")
    specialist_confidence_drift_weight: Decimal = Decimal("0.160000")
    liquidity_exit_risk_drift_weight: Decimal = Decimal("0.120000")
    resolution_ambiguity_drift_weight: Decimal = Decimal("0.100000")
    portfolio_impact_drift_weight: Decimal = Decimal("0.100000")
    max_pass_source_verified_edge_decline: Decimal = Decimal("0.000000")
    max_watch_source_verified_edge_decline: Decimal = Decimal("0.030000")
    max_source_verified_edge_decline: Decimal = Decimal("0.070000")
    max_pass_market_probability_movement: Decimal = Decimal("0.030000")
    max_watch_market_probability_movement: Decimal = Decimal("0.100000")
    max_market_probability_movement: Decimal = Decimal("0.200000")
    max_pass_uncertainty_band_widening: Decimal = Decimal("0.000000")
    max_watch_uncertainty_band_widening: Decimal = Decimal("0.050000")
    max_uncertainty_band_widening: Decimal = Decimal("0.100000")
    max_pass_specialist_confidence_decline: Decimal = Decimal("0.000000")
    max_watch_specialist_confidence_decline: Decimal = Decimal("0.050000")
    max_specialist_confidence_decline: Decimal = Decimal("0.100000")
    max_pass_liquidity_exit_risk_increase: Decimal = Decimal("0.000000")
    max_watch_liquidity_exit_risk_increase: Decimal = Decimal("0.050000")
    max_liquidity_exit_risk_increase: Decimal = Decimal("0.100000")
    max_pass_resolution_ambiguity_increase: Decimal = Decimal("0.000000")
    max_watch_resolution_ambiguity_increase: Decimal = Decimal("0.050000")
    max_resolution_ambiguity_increase: Decimal = Decimal("0.100000")
    max_pass_portfolio_impact_increase: Decimal = Decimal("0.000000")
    max_watch_portfolio_impact_increase: Decimal = Decimal("0.050000")
    max_portfolio_impact_increase: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationSignalStabilityGateV2Config:
            raise ValueError(
                "config must be exactly StrategyRecommendationSignalStabilityGateV2Config",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        for field_name in (
            "pass_stability_floor",
            "watch_stability_floor",
            "source_verified_edge_trend_weight",
            "market_probability_movement_weight",
            "uncertainty_band_movement_weight",
            "specialist_confidence_drift_weight",
            "liquidity_exit_risk_drift_weight",
            "resolution_ambiguity_drift_weight",
            "portfolio_impact_drift_weight",
            "max_pass_source_verified_edge_decline",
            "max_watch_source_verified_edge_decline",
            "max_source_verified_edge_decline",
            "max_pass_market_probability_movement",
            "max_watch_market_probability_movement",
            "max_market_probability_movement",
            "max_pass_uncertainty_band_widening",
            "max_watch_uncertainty_band_widening",
            "max_uncertainty_band_widening",
            "max_pass_specialist_confidence_decline",
            "max_watch_specialist_confidence_decline",
            "max_specialist_confidence_decline",
            "max_pass_liquidity_exit_risk_increase",
            "max_watch_liquidity_exit_risk_increase",
            "max_liquidity_exit_risk_increase",
            "max_pass_resolution_ambiguity_increase",
            "max_watch_resolution_ambiguity_increase",
            "max_resolution_ambiguity_increase",
            "max_pass_portfolio_impact_increase",
            "max_watch_portfolio_impact_increase",
            "max_portfolio_impact_increase",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(asdict(self)))


@dataclass(frozen=True)
class StrategyRecommendationSignalStabilityGateV2Observation:
    recommendation_id: str
    market_slug: str
    outcome_name: str
    source_verified_edge_start: Decimal
    source_verified_edge_current: Decimal
    market_probability_start: Decimal
    market_probability_current: Decimal
    uncertainty_band_start: Decimal
    uncertainty_band_current: Decimal
    specialist_confidence_start: Decimal
    specialist_confidence_current: Decimal
    liquidity_exit_risk_start: Decimal
    liquidity_exit_risk_current: Decimal
    resolution_ambiguity_start: Decimal
    resolution_ambiguity_current: Decimal
    portfolio_impact_start: Decimal
    portfolio_impact_current: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationSignalStabilityGateV2Observation:
            raise ValueError(
                "observation must be exactly "
                "StrategyRecommendationSignalStabilityGateV2Observation",
            )
        for field_name in ("recommendation_id", "market_slug", "outcome_name"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in OBSERVATION_RATIO_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", _payload_value(asdict(self)))


@dataclass(frozen=True)
class StrategyRecommendationSignalStabilityGateV2Row:
    recommendation_id: str
    market_slug: str
    outcome_name: str
    source_verified_edge_start: Decimal
    source_verified_edge_current: Decimal
    source_verified_edge_trend: Decimal
    source_verified_edge_trend_score: Decimal
    market_probability_start: Decimal
    market_probability_current: Decimal
    market_probability_movement: Decimal
    market_probability_movement_score: Decimal
    uncertainty_band_start: Decimal
    uncertainty_band_current: Decimal
    uncertainty_band_movement: Decimal
    uncertainty_band_movement_score: Decimal
    specialist_confidence_start: Decimal
    specialist_confidence_current: Decimal
    specialist_confidence_drift: Decimal
    specialist_confidence_drift_score: Decimal
    liquidity_exit_risk_start: Decimal
    liquidity_exit_risk_current: Decimal
    liquidity_exit_risk_drift: Decimal
    liquidity_exit_risk_drift_score: Decimal
    resolution_ambiguity_start: Decimal
    resolution_ambiguity_current: Decimal
    resolution_ambiguity_drift: Decimal
    resolution_ambiguity_drift_score: Decimal
    portfolio_impact_start: Decimal
    portfolio_impact_current: Decimal
    portfolio_impact_drift: Decimal
    portfolio_impact_drift_score: Decimal
    stability_score: Decimal
    validation_status: str
    final_recommendation_blocked: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationSignalStabilityGateV2Row:
            raise ValueError("row must be exactly StrategyRecommendationSignalStabilityGateV2Row")
        for field_name in ("recommendation_id", "market_slug", "outcome_name"):
            object.__setattr__(
                self,
                field_name,
                _require_non_empty_string(field_name, getattr(self, field_name)),
            )
        for field_name in OBSERVATION_RATIO_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_verified_edge_trend",
            "market_probability_movement",
            "uncertainty_band_movement",
            "specialist_confidence_drift",
            "liquidity_exit_risk_drift",
            "resolution_ambiguity_drift",
            "portfolio_impact_drift",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_verified_edge_trend_score",
            "market_probability_movement_score",
            "uncertainty_band_movement_score",
            "specialist_confidence_drift_score",
            "liquidity_exit_risk_drift_score",
            "resolution_ambiguity_drift_score",
            "portfolio_impact_drift_score",
            "stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("validation_status", self.validation_status)
        _require_bool("final_recommendation_blocked", self.final_recommendation_blocked)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(asdict(self)))
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyRecommendationSignalStabilityGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    final_recommendation_blocked: bool
    recommendation_count: Decimal
    pass_recommendation_count: Decimal
    watch_recommendation_count: Decimal
    blocked_recommendation_count: Decimal
    average_stability_score: Decimal
    top_stability_score: Decimal
    bottom_stability_score: Decimal
    rows: tuple[StrategyRecommendationSignalStabilityGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationSignalStabilityGateV2Report:
            raise ValueError(
                "report must be exactly StrategyRecommendationSignalStabilityGateV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        _require_status("gate_status", self.gate_status)
        _require_bool("final_recommendation_blocked", self.final_recommendation_blocked)
        for field_name in (
            "recommendation_count",
            "pass_recommendation_count",
            "watch_recommendation_count",
            "blocked_recommendation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_stability_score",
            "top_stability_score",
            "bottom_stability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(asdict(self)))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(_report_digest_fields(self)),
            )
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            _validate_report_digest(self)
        _validate_report_shape(self)
        _validate_report_summary(self)

    @property
    def payload(self) -> dict[str, object]:
        payload = _payload_value(asdict(self))
        _reject_unsafe_public_payload("payload", payload)
        if type(payload) is not dict:
            raise ValueError("payload must be an object")
        return payload

    @classmethod
    def from_payload(
        cls,
        payload: object,
    ) -> StrategyRecommendationSignalStabilityGateV2Report:
        _reject_unsafe_public_payload("payload", payload)
        payload_dict = _payload_dict("payload", payload)
        _require_payload_fields(payload_dict, REPORT_PAYLOAD_FIELDS)
        values = _report_values_from_payload(payload_dict)
        supplied_digest = _string_from_payload(
            "derived_validation_digest",
            payload_dict["derived_validation_digest"],
        )
        _require_sha256_digest("derived_validation_digest", supplied_digest)
        expected_digest = _derived_validation_digest(values)
        if supplied_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        return cls(**values, derived_validation_digest=supplied_digest)


REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "gate_status",
    "final_recommendation_blocked",
    "recommendation_count",
    "pass_recommendation_count",
    "watch_recommendation_count",
    "blocked_recommendation_count",
    "average_stability_score",
    "top_stability_score",
    "bottom_stability_score",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    "recommendation_id",
    "market_slug",
    "outcome_name",
    "source_verified_edge_start",
    "source_verified_edge_current",
    "source_verified_edge_trend",
    "source_verified_edge_trend_score",
    "market_probability_start",
    "market_probability_current",
    "market_probability_movement",
    "market_probability_movement_score",
    "uncertainty_band_start",
    "uncertainty_band_current",
    "uncertainty_band_movement",
    "uncertainty_band_movement_score",
    "specialist_confidence_start",
    "specialist_confidence_current",
    "specialist_confidence_drift",
    "specialist_confidence_drift_score",
    "liquidity_exit_risk_start",
    "liquidity_exit_risk_current",
    "liquidity_exit_risk_drift",
    "liquidity_exit_risk_drift_score",
    "resolution_ambiguity_start",
    "resolution_ambiguity_current",
    "resolution_ambiguity_drift",
    "resolution_ambiguity_drift_score",
    "portfolio_impact_start",
    "portfolio_impact_current",
    "portfolio_impact_drift",
    "portfolio_impact_drift_score",
    "stability_score",
    "validation_status",
    "final_recommendation_blocked",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


def build_strategy_recommendation_signal_stability_gate_v2(
    observations: object,
    *,
    config: StrategyRecommendationSignalStabilityGateV2Config | None = None,
    generated_at: datetime,
) -> StrategyRecommendationSignalStabilityGateV2Report:
    if config is None:
        config = StrategyRecommendationSignalStabilityGateV2Config()
    if type(config) is not StrategyRecommendationSignalStabilityGateV2Config:
        raise ValueError("config must be a StrategyRecommendationSignalStabilityGateV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (_row_for_observation(item, config) for item in normalized_observations),
            key=_row_sort_key,
        ),
    )
    status = _gate_status(rows)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "gate_status": status,
        "final_recommendation_blocked": status != "pass",
        "recommendation_count": _count_decimal(len(rows)),
        "pass_recommendation_count": _status_count(rows, "pass"),
        "watch_recommendation_count": _status_count(rows, "watch"),
        "blocked_recommendation_count": _status_count(rows, "blocked"),
        "average_stability_score": _average_score(rows),
        "top_stability_score": _top_score(rows),
        "bottom_stability_score": _bottom_score(rows),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyRecommendationSignalStabilityGateV2Report(**values)


def strategy_recommendation_signal_stability_gate_v2_payload(
    report: StrategyRecommendationSignalStabilityGateV2Report,
) -> dict[str, object]:
    if type(report) is not StrategyRecommendationSignalStabilityGateV2Report:
        raise ValueError("report must be a StrategyRecommendationSignalStabilityGateV2Report")
    _require_hard_flags("report", report)
    _validate_report_digest(report)
    return report.payload


def _row_for_observation(
    observation: StrategyRecommendationSignalStabilityGateV2Observation,
    config: StrategyRecommendationSignalStabilityGateV2Config,
) -> StrategyRecommendationSignalStabilityGateV2Row:
    source_verified_edge_trend = _q(
        observation.source_verified_edge_current - observation.source_verified_edge_start,
    )
    market_probability_movement = _absolute_decimal(
        observation.market_probability_current - observation.market_probability_start,
    )
    uncertainty_band_movement = _q(
        observation.uncertainty_band_current - observation.uncertainty_band_start,
    )
    specialist_confidence_drift = _q(
        observation.specialist_confidence_current - observation.specialist_confidence_start,
    )
    liquidity_exit_risk_drift = _q(
        observation.liquidity_exit_risk_current - observation.liquidity_exit_risk_start,
    )
    resolution_ambiguity_drift = _q(
        observation.resolution_ambiguity_current - observation.resolution_ambiguity_start,
    )
    portfolio_impact_drift = _q(
        observation.portfolio_impact_current - observation.portfolio_impact_start,
    )

    source_verified_edge_trend_score = _adverse_score(
        _decline_amount(source_verified_edge_trend),
        config.max_source_verified_edge_decline,
    )
    market_probability_movement_score = _adverse_score(
        market_probability_movement,
        config.max_market_probability_movement,
    )
    uncertainty_band_movement_score = _adverse_score(
        _increase_amount(uncertainty_band_movement),
        config.max_uncertainty_band_widening,
    )
    specialist_confidence_drift_score = _adverse_score(
        _decline_amount(specialist_confidence_drift),
        config.max_specialist_confidence_decline,
    )
    liquidity_exit_risk_drift_score = _adverse_score(
        _increase_amount(liquidity_exit_risk_drift),
        config.max_liquidity_exit_risk_increase,
    )
    resolution_ambiguity_drift_score = _adverse_score(
        _increase_amount(resolution_ambiguity_drift),
        config.max_resolution_ambiguity_increase,
    )
    portfolio_impact_drift_score = _adverse_score(
        _increase_amount(portfolio_impact_drift),
        config.max_portfolio_impact_increase,
    )
    stability_score = _stability_score(
        source_verified_edge_trend_score=source_verified_edge_trend_score,
        market_probability_movement_score=market_probability_movement_score,
        uncertainty_band_movement_score=uncertainty_band_movement_score,
        specialist_confidence_drift_score=specialist_confidence_drift_score,
        liquidity_exit_risk_drift_score=liquidity_exit_risk_drift_score,
        resolution_ambiguity_drift_score=resolution_ambiguity_drift_score,
        portfolio_impact_drift_score=portfolio_impact_drift_score,
        config=config,
    )
    status = _validation_status(
        source_verified_edge_trend=source_verified_edge_trend,
        market_probability_movement=market_probability_movement,
        uncertainty_band_movement=uncertainty_band_movement,
        specialist_confidence_drift=specialist_confidence_drift,
        liquidity_exit_risk_drift=liquidity_exit_risk_drift,
        resolution_ambiguity_drift=resolution_ambiguity_drift,
        portfolio_impact_drift=portfolio_impact_drift,
        stability_score=stability_score,
        config=config,
    )
    return StrategyRecommendationSignalStabilityGateV2Row(
        recommendation_id=observation.recommendation_id,
        market_slug=observation.market_slug,
        outcome_name=observation.outcome_name,
        source_verified_edge_start=observation.source_verified_edge_start,
        source_verified_edge_current=observation.source_verified_edge_current,
        source_verified_edge_trend=source_verified_edge_trend,
        source_verified_edge_trend_score=source_verified_edge_trend_score,
        market_probability_start=observation.market_probability_start,
        market_probability_current=observation.market_probability_current,
        market_probability_movement=market_probability_movement,
        market_probability_movement_score=market_probability_movement_score,
        uncertainty_band_start=observation.uncertainty_band_start,
        uncertainty_band_current=observation.uncertainty_band_current,
        uncertainty_band_movement=uncertainty_band_movement,
        uncertainty_band_movement_score=uncertainty_band_movement_score,
        specialist_confidence_start=observation.specialist_confidence_start,
        specialist_confidence_current=observation.specialist_confidence_current,
        specialist_confidence_drift=specialist_confidence_drift,
        specialist_confidence_drift_score=specialist_confidence_drift_score,
        liquidity_exit_risk_start=observation.liquidity_exit_risk_start,
        liquidity_exit_risk_current=observation.liquidity_exit_risk_current,
        liquidity_exit_risk_drift=liquidity_exit_risk_drift,
        liquidity_exit_risk_drift_score=liquidity_exit_risk_drift_score,
        resolution_ambiguity_start=observation.resolution_ambiguity_start,
        resolution_ambiguity_current=observation.resolution_ambiguity_current,
        resolution_ambiguity_drift=resolution_ambiguity_drift,
        resolution_ambiguity_drift_score=resolution_ambiguity_drift_score,
        portfolio_impact_start=observation.portfolio_impact_start,
        portfolio_impact_current=observation.portfolio_impact_current,
        portfolio_impact_drift=portfolio_impact_drift,
        portfolio_impact_drift_score=portfolio_impact_drift_score,
        stability_score=stability_score,
        validation_status=status,
        final_recommendation_blocked=status != "pass",
        reason_codes=_row_reason_codes(
            source_verified_edge_trend=source_verified_edge_trend,
            market_probability_movement=market_probability_movement,
            uncertainty_band_movement=uncertainty_band_movement,
            specialist_confidence_drift=specialist_confidence_drift,
            liquidity_exit_risk_drift=liquidity_exit_risk_drift,
            resolution_ambiguity_drift=resolution_ambiguity_drift,
            portfolio_impact_drift=portfolio_impact_drift,
            validation_status=status,
            config=config,
        ),
    )


def _stability_score(
    *,
    source_verified_edge_trend_score: Decimal,
    market_probability_movement_score: Decimal,
    uncertainty_band_movement_score: Decimal,
    specialist_confidence_drift_score: Decimal,
    liquidity_exit_risk_drift_score: Decimal,
    resolution_ambiguity_drift_score: Decimal,
    portfolio_impact_drift_score: Decimal,
    config: StrategyRecommendationSignalStabilityGateV2Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            source_verified_edge_trend_score * config.source_verified_edge_trend_weight
            + market_probability_movement_score * config.market_probability_movement_weight
            + uncertainty_band_movement_score * config.uncertainty_band_movement_weight
            + specialist_confidence_drift_score * config.specialist_confidence_drift_weight
            + liquidity_exit_risk_drift_score * config.liquidity_exit_risk_drift_weight
            + resolution_ambiguity_drift_score * config.resolution_ambiguity_drift_weight
            + portfolio_impact_drift_score * config.portfolio_impact_drift_weight,
        )


def _validation_status(
    *,
    source_verified_edge_trend: Decimal,
    market_probability_movement: Decimal,
    uncertainty_band_movement: Decimal,
    specialist_confidence_drift: Decimal,
    liquidity_exit_risk_drift: Decimal,
    resolution_ambiguity_drift: Decimal,
    portfolio_impact_drift: Decimal,
    stability_score: Decimal,
    config: StrategyRecommendationSignalStabilityGateV2Config,
) -> str:
    if _has_blocking_drift(
        source_verified_edge_trend=source_verified_edge_trend,
        market_probability_movement=market_probability_movement,
        uncertainty_band_movement=uncertainty_band_movement,
        specialist_confidence_drift=specialist_confidence_drift,
        liquidity_exit_risk_drift=liquidity_exit_risk_drift,
        resolution_ambiguity_drift=resolution_ambiguity_drift,
        portfolio_impact_drift=portfolio_impact_drift,
        config=config,
    ):
        return "blocked"
    if (
        stability_score >= config.pass_stability_floor
        and _decline_amount(source_verified_edge_trend)
        <= config.max_pass_source_verified_edge_decline
        and market_probability_movement <= config.max_pass_market_probability_movement
        and _increase_amount(uncertainty_band_movement)
        <= config.max_pass_uncertainty_band_widening
        and _decline_amount(specialist_confidence_drift)
        <= config.max_pass_specialist_confidence_decline
        and _increase_amount(liquidity_exit_risk_drift)
        <= config.max_pass_liquidity_exit_risk_increase
        and _increase_amount(resolution_ambiguity_drift)
        <= config.max_pass_resolution_ambiguity_increase
        and _increase_amount(portfolio_impact_drift)
        <= config.max_pass_portfolio_impact_increase
    ):
        return "pass"
    if stability_score >= config.watch_stability_floor:
        return "watch"
    return "blocked"


def _has_blocking_drift(
    *,
    source_verified_edge_trend: Decimal,
    market_probability_movement: Decimal,
    uncertainty_band_movement: Decimal,
    specialist_confidence_drift: Decimal,
    liquidity_exit_risk_drift: Decimal,
    resolution_ambiguity_drift: Decimal,
    portfolio_impact_drift: Decimal,
    config: StrategyRecommendationSignalStabilityGateV2Config,
) -> bool:
    return (
        _decline_amount(source_verified_edge_trend)
        > config.max_watch_source_verified_edge_decline
        or market_probability_movement > config.max_watch_market_probability_movement
        or _increase_amount(uncertainty_band_movement)
        > config.max_watch_uncertainty_band_widening
        or _decline_amount(specialist_confidence_drift)
        > config.max_watch_specialist_confidence_decline
        or _increase_amount(liquidity_exit_risk_drift)
        > config.max_watch_liquidity_exit_risk_increase
        or _increase_amount(resolution_ambiguity_drift)
        > config.max_watch_resolution_ambiguity_increase
        or _increase_amount(portfolio_impact_drift)
        > config.max_watch_portfolio_impact_increase
    )


def _row_reason_codes(
    *,
    source_verified_edge_trend: Decimal,
    market_probability_movement: Decimal,
    uncertainty_band_movement: Decimal,
    specialist_confidence_drift: Decimal,
    liquidity_exit_risk_drift: Decimal,
    resolution_ambiguity_drift: Decimal,
    portfolio_impact_drift: Decimal,
    validation_status: str,
    config: StrategyRecommendationSignalStabilityGateV2Config,
) -> tuple[str, ...]:
    return (
        f"signal_stability_row_{validation_status}",
        _adverse_reason(
            _decline_amount(source_verified_edge_trend),
            pass_ceiling=config.max_pass_source_verified_edge_decline,
            watch_ceiling=config.max_watch_source_verified_edge_decline,
            stable_reason="source_verified_edge_trend_stable",
            watch_reason="source_verified_edge_trend_watch",
            high_reason="source_verified_edge_trend_weak",
        ),
        _adverse_reason(
            market_probability_movement,
            pass_ceiling=config.max_pass_market_probability_movement,
            watch_ceiling=config.max_watch_market_probability_movement,
            stable_reason="market_probability_movement_stable",
            watch_reason="market_probability_movement_watch",
            high_reason="market_probability_movement_high",
        ),
        _adverse_reason(
            _increase_amount(uncertainty_band_movement),
            pass_ceiling=config.max_pass_uncertainty_band_widening,
            watch_ceiling=config.max_watch_uncertainty_band_widening,
            stable_reason="uncertainty_band_movement_stable",
            watch_reason="uncertainty_band_movement_watch",
            high_reason="uncertainty_band_movement_wide",
        ),
        _adverse_reason(
            _decline_amount(specialist_confidence_drift),
            pass_ceiling=config.max_pass_specialist_confidence_decline,
            watch_ceiling=config.max_watch_specialist_confidence_decline,
            stable_reason="specialist_confidence_drift_stable",
            watch_reason="specialist_confidence_drift_watch",
            high_reason="specialist_confidence_drift_weak",
        ),
        _adverse_reason(
            _increase_amount(liquidity_exit_risk_drift),
            pass_ceiling=config.max_pass_liquidity_exit_risk_increase,
            watch_ceiling=config.max_watch_liquidity_exit_risk_increase,
            stable_reason="liquidity_exit_risk_drift_stable",
            watch_reason="liquidity_exit_risk_drift_watch",
            high_reason="liquidity_exit_risk_drift_high",
        ),
        _adverse_reason(
            _increase_amount(resolution_ambiguity_drift),
            pass_ceiling=config.max_pass_resolution_ambiguity_increase,
            watch_ceiling=config.max_watch_resolution_ambiguity_increase,
            stable_reason="resolution_ambiguity_drift_stable",
            watch_reason="resolution_ambiguity_drift_watch",
            high_reason="resolution_ambiguity_drift_high",
        ),
        _adverse_reason(
            _increase_amount(portfolio_impact_drift),
            pass_ceiling=config.max_pass_portfolio_impact_increase,
            watch_ceiling=config.max_watch_portfolio_impact_increase,
            stable_reason="portfolio_impact_drift_stable",
            watch_reason="portfolio_impact_drift_watch",
            high_reason="portfolio_impact_drift_high",
        ),
    )


def _adverse_reason(
    adverse_value: Decimal,
    *,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
    stable_reason: str,
    watch_reason: str,
    high_reason: str,
) -> str:
    if adverse_value <= pass_ceiling:
        return stable_reason
    if adverse_value <= watch_ceiling:
        return watch_reason
    return high_reason


def _gate_status(rows: tuple[StrategyRecommendationSignalStabilityGateV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.validation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.validation_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationSignalStabilityGateV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("signal_stability_gate_empty",)
    if status == "pass":
        return ("signal_stability_gate_passed",)
    reasons: list[str] = []
    if any(row.validation_status == "watch" for row in rows):
        reasons.append("signal_stability_gate_watch_rows")
    if any(row.validation_status == "blocked" for row in rows):
        reasons.append("signal_stability_gate_blocked_rows")
    return tuple(reasons)


def _status_count(
    rows: tuple[StrategyRecommendationSignalStabilityGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.validation_status == status))


def _average_score(rows: tuple[StrategyRecommendationSignalStabilityGateV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum((row.stability_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _top_score(rows: tuple[StrategyRecommendationSignalStabilityGateV2Row, ...]) -> Decimal:
    return max((row.stability_score for row in rows), default=ZERO)


def _bottom_score(rows: tuple[StrategyRecommendationSignalStabilityGateV2Row, ...]) -> Decimal:
    return min((row.stability_score for row in rows), default=ZERO)


def _row_sort_key(
    row: StrategyRecommendationSignalStabilityGateV2Row,
) -> tuple[Decimal, str, str, str]:
    return (
        ROW_STATUS_RANK[row.validation_status],
        row.recommendation_id,
        row.market_slug,
        row.outcome_name,
    )


def _normalize_observations(
    observations: object,
) -> tuple[StrategyRecommendationSignalStabilityGateV2Observation, ...]:
    if isinstance(observations, (str, bytes)) or not hasattr(observations, "__iter__"):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not StrategyRecommendationSignalStabilityGateV2Observation:
            raise ValueError(
                "observation items must be "
                "StrategyRecommendationSignalStabilityGateV2Observation",
            )
        _require_hard_flags("observation", item)
        key = (item.recommendation_id, item.market_slug)
        if key in seen:
            raise ValueError("duplicate recommendation_id and market_slug")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[StrategyRecommendationSignalStabilityGateV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and recommendation_id")
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not StrategyRecommendationSignalStabilityGateV2Row:
            raise ValueError("rows must contain StrategyRecommendationSignalStabilityGateV2Row")
        _require_hard_flags("row", row)
        key = (row.recommendation_id, row.market_slug)
        if key in seen:
            raise ValueError("rows must not contain duplicate recommendation_id and market_slug")
        seen.add(key)
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not hasattr(values, "__iter__"):
        raise ValueError(f"{field_name} must be an iterable")
    normalized = tuple(values)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    _reject_unsafe_public_payload(field_name, normalized)
    for value in normalized:
        _require_non_empty_string(field_name, value)
        if value not in allowed:
            raise ValueError(f"{field_name} contains an unsupported reason code")
    return normalized


def _validate_config(config: StrategyRecommendationSignalStabilityGateV2Config) -> None:
    if config.watch_stability_floor > config.pass_stability_floor:
        raise ValueError("watch_stability_floor must not exceed pass_stability_floor")
    _require_ordered_thresholds(
        "source_verified_edge_decline",
        config.max_pass_source_verified_edge_decline,
        config.max_watch_source_verified_edge_decline,
        config.max_source_verified_edge_decline,
    )
    _require_ordered_thresholds(
        "market_probability_movement",
        config.max_pass_market_probability_movement,
        config.max_watch_market_probability_movement,
        config.max_market_probability_movement,
    )
    _require_ordered_thresholds(
        "uncertainty_band_widening",
        config.max_pass_uncertainty_band_widening,
        config.max_watch_uncertainty_band_widening,
        config.max_uncertainty_band_widening,
    )
    _require_ordered_thresholds(
        "specialist_confidence_decline",
        config.max_pass_specialist_confidence_decline,
        config.max_watch_specialist_confidence_decline,
        config.max_specialist_confidence_decline,
    )
    _require_ordered_thresholds(
        "liquidity_exit_risk_increase",
        config.max_pass_liquidity_exit_risk_increase,
        config.max_watch_liquidity_exit_risk_increase,
        config.max_liquidity_exit_risk_increase,
    )
    _require_ordered_thresholds(
        "resolution_ambiguity_increase",
        config.max_pass_resolution_ambiguity_increase,
        config.max_watch_resolution_ambiguity_increase,
        config.max_resolution_ambiguity_increase,
    )
    _require_ordered_thresholds(
        "portfolio_impact_increase",
        config.max_pass_portfolio_impact_increase,
        config.max_watch_portfolio_impact_increase,
        config.max_portfolio_impact_increase,
    )
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.source_verified_edge_trend_weight
            + config.market_probability_movement_weight
            + config.uncertainty_band_movement_weight
            + config.specialist_confidence_drift_weight
            + config.liquidity_exit_risk_drift_weight
            + config.resolution_ambiguity_drift_weight
            + config.portfolio_impact_drift_weight
        ).quantize(SCORE_QUANT)
    if weight_total != ONE:
        raise ValueError("stability weights must sum to 1.000000")


def _require_ordered_thresholds(
    label: str,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
    score_ceiling: Decimal,
) -> None:
    if pass_ceiling > watch_ceiling:
        raise ValueError(f"{label} pass ceiling must not exceed watch ceiling")
    if watch_ceiling > score_ceiling:
        raise ValueError(f"{label} watch ceiling must not exceed score ceiling")
    if score_ceiling == ZERO:
        raise ValueError(f"{label} score ceiling must be positive")


def _validate_row_consistency(
    row: StrategyRecommendationSignalStabilityGateV2Row,
) -> None:
    if row.source_verified_edge_trend != _q(
        row.source_verified_edge_current - row.source_verified_edge_start,
    ):
        raise ValueError("source_verified_edge_trend must match source fields")
    if row.market_probability_movement != _absolute_decimal(
        row.market_probability_current - row.market_probability_start,
    ):
        raise ValueError("market_probability_movement must match market fields")
    if row.uncertainty_band_movement != _q(
        row.uncertainty_band_current - row.uncertainty_band_start,
    ):
        raise ValueError("uncertainty_band_movement must match uncertainty fields")
    if row.specialist_confidence_drift != _q(
        row.specialist_confidence_current - row.specialist_confidence_start,
    ):
        raise ValueError("specialist_confidence_drift must match confidence fields")
    if row.liquidity_exit_risk_drift != _q(
        row.liquidity_exit_risk_current - row.liquidity_exit_risk_start,
    ):
        raise ValueError("liquidity_exit_risk_drift must match liquidity fields")
    if row.resolution_ambiguity_drift != _q(
        row.resolution_ambiguity_current - row.resolution_ambiguity_start,
    ):
        raise ValueError("resolution_ambiguity_drift must match resolution fields")
    if row.portfolio_impact_drift != _q(
        row.portfolio_impact_current - row.portfolio_impact_start,
    ):
        raise ValueError("portfolio_impact_drift must match portfolio fields")
    if row.final_recommendation_blocked is not (row.validation_status != "pass"):
        raise ValueError("final_recommendation_blocked must match validation_status")
    if row.reason_codes[0] != f"signal_stability_row_{row.validation_status}":
        raise ValueError("reason_codes must match validation_status")


def _validate_report_shape(report: StrategyRecommendationSignalStabilityGateV2Report) -> None:
    if report.recommendation_count != _count_decimal(len(report.rows)):
        raise ValueError("recommendation_count must match rows")
    if (
        report.pass_recommendation_count != _status_count(report.rows, "pass")
        or report.watch_recommendation_count != _status_count(report.rows, "watch")
        or report.blocked_recommendation_count != _status_count(report.rows, "blocked")
    ):
        raise ValueError("status counts must match rows")
    expected_status = _gate_status(report.rows)
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match rows")
    if report.final_recommendation_blocked is not (report.gate_status != "pass"):
        raise ValueError("final_recommendation_blocked must match gate_status")
    if report.reason_codes != _report_reason_codes(report.rows, report.gate_status):
        raise ValueError("reason_codes must match gate_status")


def _validate_report_summary(report: StrategyRecommendationSignalStabilityGateV2Report) -> None:
    if report.average_stability_score != _average_score(report.rows):
        raise ValueError("average_stability_score must match rows")
    if report.top_stability_score != _top_score(report.rows):
        raise ValueError("top_stability_score must match rows")
    if report.bottom_stability_score != _bottom_score(report.rows):
        raise ValueError("bottom_stability_score must match rows")


def _validate_report_digest(report: StrategyRecommendationSignalStabilityGateV2Report) -> None:
    if report.derived_validation_digest != _derived_validation_digest(
        _report_digest_fields(report),
    ):
        raise ValueError("derived_validation_digest must match report fields")


def _report_digest_fields(
    report: StrategyRecommendationSignalStabilityGateV2Report,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "gate_status": report.gate_status,
        "final_recommendation_blocked": report.final_recommendation_blocked,
        "recommendation_count": report.recommendation_count,
        "pass_recommendation_count": report.pass_recommendation_count,
        "watch_recommendation_count": report.watch_recommendation_count,
        "blocked_recommendation_count": report.blocked_recommendation_count,
        "average_stability_score": report.average_stability_score,
        "top_stability_score": report.top_stability_score,
        "bottom_stability_score": report.bottom_stability_score,
        "rows": report.rows,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _derived_validation_digest(values: dict[str, object]) -> str:
    digest_values = dict(values)
    digest_values.pop("derived_validation_digest", None)
    ready = _payload_value(digest_values)
    _reject_unsafe_public_payload("derived validation digest fields", ready)
    encoded = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_values_from_payload(payload: dict[str, object]) -> dict[str, object]:
    return {
        "generated_at": _datetime_from_payload("generated_at", payload["generated_at"]),
        "config_version": _string_from_payload("config_version", payload["config_version"]),
        "gate_status": _string_from_payload("gate_status", payload["gate_status"]),
        "final_recommendation_blocked": _bool_from_payload(
            "final_recommendation_blocked",
            payload["final_recommendation_blocked"],
        ),
        "recommendation_count": _count_from_payload(
            "recommendation_count",
            payload["recommendation_count"],
        ),
        "pass_recommendation_count": _count_from_payload(
            "pass_recommendation_count",
            payload["pass_recommendation_count"],
        ),
        "watch_recommendation_count": _count_from_payload(
            "watch_recommendation_count",
            payload["watch_recommendation_count"],
        ),
        "blocked_recommendation_count": _count_from_payload(
            "blocked_recommendation_count",
            payload["blocked_recommendation_count"],
        ),
        "average_stability_score": _decimal_from_payload(
            "average_stability_score",
            payload["average_stability_score"],
        ),
        "top_stability_score": _decimal_from_payload(
            "top_stability_score",
            payload["top_stability_score"],
        ),
        "bottom_stability_score": _decimal_from_payload(
            "bottom_stability_score",
            payload["bottom_stability_score"],
        ),
        "rows": tuple(
            _row_from_payload(item) for item in _payload_list("rows", payload["rows"])
        ),
        "reason_codes": tuple(
            _string_from_payload("reason_codes", item)
            for item in _payload_list("reason_codes", payload["reason_codes"])
        ),
        "paper_only": _bool_from_payload("paper_only", payload["paper_only"]),
        "report_only": _bool_from_payload("report_only", payload["report_only"]),
        "readonly": _bool_from_payload("readonly", payload["readonly"]),
    }


def _row_from_payload(payload: object) -> StrategyRecommendationSignalStabilityGateV2Row:
    payload_dict = _payload_dict("row payload", payload)
    _require_payload_fields(payload_dict, ROW_PAYLOAD_FIELDS)
    return StrategyRecommendationSignalStabilityGateV2Row(
        recommendation_id=_string_from_payload(
            "recommendation_id",
            payload_dict["recommendation_id"],
        ),
        market_slug=_string_from_payload("market_slug", payload_dict["market_slug"]),
        outcome_name=_string_from_payload("outcome_name", payload_dict["outcome_name"]),
        source_verified_edge_start=_decimal_from_payload(
            "source_verified_edge_start",
            payload_dict["source_verified_edge_start"],
        ),
        source_verified_edge_current=_decimal_from_payload(
            "source_verified_edge_current",
            payload_dict["source_verified_edge_current"],
        ),
        source_verified_edge_trend=_decimal_from_payload(
            "source_verified_edge_trend",
            payload_dict["source_verified_edge_trend"],
        ),
        source_verified_edge_trend_score=_decimal_from_payload(
            "source_verified_edge_trend_score",
            payload_dict["source_verified_edge_trend_score"],
        ),
        market_probability_start=_decimal_from_payload(
            "market_probability_start",
            payload_dict["market_probability_start"],
        ),
        market_probability_current=_decimal_from_payload(
            "market_probability_current",
            payload_dict["market_probability_current"],
        ),
        market_probability_movement=_decimal_from_payload(
            "market_probability_movement",
            payload_dict["market_probability_movement"],
        ),
        market_probability_movement_score=_decimal_from_payload(
            "market_probability_movement_score",
            payload_dict["market_probability_movement_score"],
        ),
        uncertainty_band_start=_decimal_from_payload(
            "uncertainty_band_start",
            payload_dict["uncertainty_band_start"],
        ),
        uncertainty_band_current=_decimal_from_payload(
            "uncertainty_band_current",
            payload_dict["uncertainty_band_current"],
        ),
        uncertainty_band_movement=_decimal_from_payload(
            "uncertainty_band_movement",
            payload_dict["uncertainty_band_movement"],
        ),
        uncertainty_band_movement_score=_decimal_from_payload(
            "uncertainty_band_movement_score",
            payload_dict["uncertainty_band_movement_score"],
        ),
        specialist_confidence_start=_decimal_from_payload(
            "specialist_confidence_start",
            payload_dict["specialist_confidence_start"],
        ),
        specialist_confidence_current=_decimal_from_payload(
            "specialist_confidence_current",
            payload_dict["specialist_confidence_current"],
        ),
        specialist_confidence_drift=_decimal_from_payload(
            "specialist_confidence_drift",
            payload_dict["specialist_confidence_drift"],
        ),
        specialist_confidence_drift_score=_decimal_from_payload(
            "specialist_confidence_drift_score",
            payload_dict["specialist_confidence_drift_score"],
        ),
        liquidity_exit_risk_start=_decimal_from_payload(
            "liquidity_exit_risk_start",
            payload_dict["liquidity_exit_risk_start"],
        ),
        liquidity_exit_risk_current=_decimal_from_payload(
            "liquidity_exit_risk_current",
            payload_dict["liquidity_exit_risk_current"],
        ),
        liquidity_exit_risk_drift=_decimal_from_payload(
            "liquidity_exit_risk_drift",
            payload_dict["liquidity_exit_risk_drift"],
        ),
        liquidity_exit_risk_drift_score=_decimal_from_payload(
            "liquidity_exit_risk_drift_score",
            payload_dict["liquidity_exit_risk_drift_score"],
        ),
        resolution_ambiguity_start=_decimal_from_payload(
            "resolution_ambiguity_start",
            payload_dict["resolution_ambiguity_start"],
        ),
        resolution_ambiguity_current=_decimal_from_payload(
            "resolution_ambiguity_current",
            payload_dict["resolution_ambiguity_current"],
        ),
        resolution_ambiguity_drift=_decimal_from_payload(
            "resolution_ambiguity_drift",
            payload_dict["resolution_ambiguity_drift"],
        ),
        resolution_ambiguity_drift_score=_decimal_from_payload(
            "resolution_ambiguity_drift_score",
            payload_dict["resolution_ambiguity_drift_score"],
        ),
        portfolio_impact_start=_decimal_from_payload(
            "portfolio_impact_start",
            payload_dict["portfolio_impact_start"],
        ),
        portfolio_impact_current=_decimal_from_payload(
            "portfolio_impact_current",
            payload_dict["portfolio_impact_current"],
        ),
        portfolio_impact_drift=_decimal_from_payload(
            "portfolio_impact_drift",
            payload_dict["portfolio_impact_drift"],
        ),
        portfolio_impact_drift_score=_decimal_from_payload(
            "portfolio_impact_drift_score",
            payload_dict["portfolio_impact_drift_score"],
        ),
        stability_score=_decimal_from_payload(
            "stability_score",
            payload_dict["stability_score"],
        ),
        validation_status=_string_from_payload(
            "validation_status",
            payload_dict["validation_status"],
        ),
        final_recommendation_blocked=_bool_from_payload(
            "final_recommendation_blocked",
            payload_dict["final_recommendation_blocked"],
        ),
        reason_codes=tuple(
            _string_from_payload("reason_codes", item)
            for item in _payload_list("reason_codes", payload_dict["reason_codes"])
        ),
        paper_only=_bool_from_payload("paper_only", payload_dict["paper_only"]),
        report_only=_bool_from_payload("report_only", payload_dict["report_only"]),
        readonly=_bool_from_payload("readonly", payload_dict["readonly"]),
    )


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be Decimal strings")
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    if type(value) in (list, tuple):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _payload_dict(label: str, value: object) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an object")
    for key in value:
        if type(key) is not str:
            raise ValueError(f"{label} keys must be strings")
    return value


def _payload_list(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_payload_fields(
    payload: dict[str, object],
    fields: tuple[str, ...],
) -> None:
    if set(payload) != set(fields):
        raise ValueError("payload fields must match public schema")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_unsafe_public_payload(label, asdict(payload))
        return
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _mentions_unsafe_public_term(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) in (list, tuple):
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str and _mentions_unsafe_public_term(payload):
        raise ValueError(f"unsafe public payload value in {label}: {payload}")


def _mentions_unsafe_public_term(value: str) -> bool:
    tokens = _public_tokens(value.lower())
    return any(term in tokens for term in UNSAFE_PUBLIC_TERMS)


def _public_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in value:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _q_exact(field_name, value)


def _normalize_signed_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < -ONE:
        raise ValueError(f"{field_name} must be >= -1.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return _q_exact(field_name, value)


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(COUNT_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must be an integral Decimal")
    return quantized


def _q_exact(field_name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value < ZERO:
            value = ZERO
        if value > ONE:
            value = ONE
        return value.quantize(SCORE_QUANT)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _q(-value)
    return _q(value)


def _decline_amount(value: Decimal) -> Decimal:
    if value < ZERO:
        return _q(-value)
    return ZERO


def _increase_amount(value: Decimal) -> Decimal:
    if value > ZERO:
        return _q(value)
    return ZERO


def _adverse_score(adverse_value: Decimal, ceiling: Decimal) -> Decimal:
    if ceiling <= ZERO:
        raise ValueError("adverse score ceiling must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - adverse_value / ceiling)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_signed_decimal(field_name, parsed)


def _count_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_nonnegative_integral_decimal(field_name, parsed)


def _bool_from_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _string_from_payload(field_name: str, value: object) -> str:
    return _require_non_empty_string(field_name, value)


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in VALIDATION_STATUSES:
        raise ValueError(f"{field_name} must be one of {VALIDATION_STATUSES!r}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be boolean")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    _reject_unsafe_public_payload(label, _payload_value(asdict(value)))


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc
