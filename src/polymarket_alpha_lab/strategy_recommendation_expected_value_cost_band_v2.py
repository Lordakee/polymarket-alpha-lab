"""Pure Phase 1 expected-value cost band reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_EXPECTED_VALUE_COST_BAND_V2_CONFIG_VERSION",
    "StrategyRecommendationExpectedValueCostBandV2Config",
    "StrategyRecommendationExpectedValueCostBandV2Input",
    "StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount",
    "StrategyRecommendationExpectedValueCostBandV2Report",
    "StrategyRecommendationExpectedValueCostBandV2Row",
    "build_strategy_recommendation_expected_value_cost_band_v2_report",
    "strategy_recommendation_expected_value_cost_band_v2_payload",
)


DEFAULT_STRATEGY_RECOMMENDATION_EXPECTED_VALUE_COST_BAND_V2_CONFIG_VERSION = (
    "strategy-recommendation-expected-value-cost-band-v2"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "blocked")
COST_BANDS = ("positive", "thin", "negative")
STATUS_SORT_PRIORITY = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
REPORT_GUARD_REASON_CODES = (
    "cost_band_confidence_watch",
    "cost_band_cost_ratio_blocked",
    "cost_band_cost_ratio_watch",
    "cost_band_net_expected_value_blocked",
    "cost_band_net_expected_value_watch",
    "cost_band_probability_edge_blocked",
)


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueCostBandV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_EXPECTED_VALUE_COST_BAND_V2_CONFIG_VERSION
    )
    minimum_pass_net_expected_value: Decimal = Decimal("0.020000")
    minimum_watch_net_expected_value: Decimal = Decimal("0.000000")
    minimum_confidence: Decimal = Decimal("0.500000")
    maximum_pass_cost_to_edge_ratio: Decimal = Decimal("0.500000")
    maximum_watch_cost_to_edge_ratio: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyRecommendationExpectedValueCostBandV2Config "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            StrategyRecommendationExpectedValueCostBandV2Config,
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RECOMMENDATION_EXPECTED_VALUE_COST_BAND_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "minimum_pass_net_expected_value",
            "minimum_watch_net_expected_value",
            "maximum_pass_cost_to_edge_ratio",
            "maximum_watch_cost_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_confidence",
            _normalize_ratio("minimum_confidence", self.minimum_confidence),
        )
        if self.minimum_watch_net_expected_value > self.minimum_pass_net_expected_value:
            raise ValueError(
                "minimum_watch_net_expected_value must be at most "
                "minimum_pass_net_expected_value",
            )
        if self.maximum_pass_cost_to_edge_ratio > self.maximum_watch_cost_to_edge_ratio:
            raise ValueError(
                "maximum_pass_cost_to_edge_ratio must be at most "
                "maximum_watch_cost_to_edge_ratio",
            )
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueCostBandV2Config",
            self,
        )
        reject_unsafe_surface_fields("cost band config", self)


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueCostBandV2Input:
    recommendation_id: str
    observed_at: datetime
    probability_edge: Decimal
    confidence: Decimal
    taker_fee: Decimal
    spread: Decimal
    slippage: Decimal
    settlement_lag: Decimal
    liquidity_haircut: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyRecommendationExpectedValueCostBandV2Input "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "input",
            self,
            StrategyRecommendationExpectedValueCostBandV2Input,
        )
        _require_canonical_string("recommendation_id", self.recommendation_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability_edge",
            _normalize_decimal("probability_edge", self.probability_edge),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_ratio("confidence", self.confidence),
        )
        for field_name in (
            "taker_fee",
            "spread",
            "slippage",
            "settlement_lag",
            "liquidity_haircut",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueCostBandV2Input",
            self,
        )
        reject_unsafe_surface_fields("cost band input", self)


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueCostBandV2Row:
    recommendation_id: str
    observed_at: datetime
    probability_edge: Decimal
    confidence: Decimal
    taker_fee: Decimal
    spread: Decimal
    slippage: Decimal
    settlement_lag: Decimal
    liquidity_haircut: Decimal
    confidence_adjusted_edge: Decimal
    total_cost: Decimal
    net_expected_value: Decimal
    cost_to_edge_ratio: Decimal
    edge_shortfall: Decimal
    recommendation_status: str
    cost_band: str
    reason_codes: tuple[str, ...]
    driver_explanations: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyRecommendationExpectedValueCostBandV2Row "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            StrategyRecommendationExpectedValueCostBandV2Row,
        )
        _require_canonical_string("recommendation_id", self.recommendation_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "probability_edge",
            "confidence_adjusted_edge",
            "net_expected_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "confidence", _normalize_ratio("confidence", self.confidence))
        for field_name in (
            "taker_fee",
            "spread",
            "slippage",
            "settlement_lag",
            "liquidity_haircut",
            "total_cost",
            "cost_to_edge_ratio",
            "edge_shortfall",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("recommendation_status", self.recommendation_status, STATUSES)
        _require_member("cost_band", self.cost_band, COST_BANDS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "driver_explanations",
            _normalize_driver_explanations(self.driver_explanations),
        )
        _require_hex_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueCostBandV2Row",
            self,
        )
        reject_unsafe_surface_fields("cost band row", self)


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason code count",
            self,
            StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount,
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount",
            self,
        )
        reject_unsafe_surface_fields("cost band reason code count", self)


@dataclass(frozen=True)
class StrategyRecommendationExpectedValueCostBandV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_total_cost: Decimal
    max_total_cost: Decimal
    min_net_expected_value: Decimal
    max_cost_to_edge_ratio: Decimal
    max_edge_shortfall: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount,
        ...,
    ]
    recommendation_rows: tuple[StrategyRecommendationExpectedValueCostBandV2Row, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyRecommendationExpectedValueCostBandV2Report "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            StrategyRecommendationExpectedValueCostBandV2Report,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_RECOMMENDATION_EXPECTED_VALUE_COST_BAND_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_total_cost",
            "max_total_cost",
            "min_net_expected_value",
            "max_cost_to_edge_ratio",
            "max_edge_shortfall",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "recommendation_rows",
            _normalize_rows(self.recommendation_rows),
        )
        _require_hex_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        require_paper_only_flags(
            "StrategyRecommendationExpectedValueCostBandV2Report",
            self,
        )
        reject_unsafe_surface_fields("cost band report", self)


def build_strategy_recommendation_expected_value_cost_band_v2_report(
    recommendations: Iterable[StrategyRecommendationExpectedValueCostBandV2Input],
    *,
    config: StrategyRecommendationExpectedValueCostBandV2Config,
    generated_at: datetime,
) -> StrategyRecommendationExpectedValueCostBandV2Report:
    if type(config) is not StrategyRecommendationExpectedValueCostBandV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationExpectedValueCostBandV2Config",
        )
    require_paper_only_flags("config", config)
    reject_unsafe_surface_fields("cost band config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(recommendations)
    for recommendation in inputs:
        if recommendation.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_input(recommendation, config=config) for recommendation in inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = _report_reason_codes(rows)
    report = _report_from_parts(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
    )
    return report


def strategy_recommendation_expected_value_cost_band_v2_payload(
    report: StrategyRecommendationExpectedValueCostBandV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationExpectedValueCostBandV2Report:
        raise ValueError("report must be a StrategyRecommendationExpectedValueCostBandV2Report")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("cost band report", report)
    return json_ready_no_floats(report)


def _row_from_input(
    recommendation: StrategyRecommendationExpectedValueCostBandV2Input,
    *,
    config: StrategyRecommendationExpectedValueCostBandV2Config,
) -> StrategyRecommendationExpectedValueCostBandV2Row:
    confidence_adjusted_edge = _multiply_decimal(
        recommendation.probability_edge,
        recommendation.confidence,
    )
    total_cost = _add_decimal(
        recommendation.taker_fee,
        recommendation.spread,
        recommendation.slippage,
        recommendation.settlement_lag,
        recommendation.liquidity_haircut,
    )
    net_expected_value = _subtract_decimal(confidence_adjusted_edge, total_cost)
    cost_to_edge_ratio = _ratio_or_zero(total_cost, confidence_adjusted_edge)
    edge_shortfall = _max_two(_subtract_decimal(ZERO, net_expected_value), ZERO)
    reason_codes = _row_reason_codes(
        recommendation,
        net_expected_value=net_expected_value,
        cost_to_edge_ratio=cost_to_edge_ratio,
        config=config,
    )
    status = _row_status(reason_codes)
    cost_band = _cost_band(status)
    driver_explanations = _driver_explanations_from_values(
        probability_edge=recommendation.probability_edge,
        confidence=recommendation.confidence,
        confidence_adjusted_edge=confidence_adjusted_edge,
        liquidity_haircut=recommendation.liquidity_haircut,
        total_cost=total_cost,
        net_expected_value=net_expected_value,
        cost_to_edge_ratio=cost_to_edge_ratio,
        reason_codes=reason_codes,
    )
    validation_digest = _row_validation_digest_from_parts(
        recommendation_id=recommendation.recommendation_id,
        observed_at=recommendation.observed_at,
        probability_edge=recommendation.probability_edge,
        confidence=recommendation.confidence,
        taker_fee=recommendation.taker_fee,
        spread=recommendation.spread,
        slippage=recommendation.slippage,
        settlement_lag=recommendation.settlement_lag,
        liquidity_haircut=recommendation.liquidity_haircut,
        confidence_adjusted_edge=confidence_adjusted_edge,
        total_cost=total_cost,
        net_expected_value=net_expected_value,
        cost_to_edge_ratio=cost_to_edge_ratio,
        edge_shortfall=edge_shortfall,
        recommendation_status=status,
        cost_band=cost_band,
        reason_codes=reason_codes,
        driver_explanations=driver_explanations,
    )
    return StrategyRecommendationExpectedValueCostBandV2Row(
        recommendation_id=recommendation.recommendation_id,
        observed_at=recommendation.observed_at,
        probability_edge=recommendation.probability_edge,
        confidence=recommendation.confidence,
        taker_fee=recommendation.taker_fee,
        spread=recommendation.spread,
        slippage=recommendation.slippage,
        settlement_lag=recommendation.settlement_lag,
        liquidity_haircut=recommendation.liquidity_haircut,
        confidence_adjusted_edge=confidence_adjusted_edge,
        total_cost=total_cost,
        net_expected_value=net_expected_value,
        cost_to_edge_ratio=cost_to_edge_ratio,
        edge_shortfall=edge_shortfall,
        recommendation_status=status,
        cost_band=cost_band,
        reason_codes=reason_codes,
        driver_explanations=driver_explanations,
        validation_digest=validation_digest,
    )


def _report_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[StrategyRecommendationExpectedValueCostBandV2Row, ...],
    reason_codes: tuple[str, ...],
    reason_code_counts: tuple[
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount,
        ...,
    ],
) -> StrategyRecommendationExpectedValueCostBandV2Report:
    candidate_count = _count(len(rows))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    blocked_count = _status_count(rows, "blocked")
    average_total_cost = _average_decimal(tuple(row.total_cost for row in rows))
    max_total_cost = _max_decimal(tuple(row.total_cost for row in rows))
    min_net_expected_value = _min_decimal(tuple(row.net_expected_value for row in rows))
    max_cost_to_edge_ratio = _max_decimal(tuple(row.cost_to_edge_ratio for row in rows))
    max_edge_shortfall = _max_decimal(tuple(row.edge_shortfall for row in rows))
    status = _report_status(rows)
    validation_digest = _report_validation_digest_from_parts(
        generated_at=generated_at,
        config_version=config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_total_cost=average_total_cost,
        max_total_cost=max_total_cost,
        min_net_expected_value=min_net_expected_value,
        max_cost_to_edge_ratio=max_cost_to_edge_ratio,
        max_edge_shortfall=max_edge_shortfall,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        rows=rows,
    )
    return StrategyRecommendationExpectedValueCostBandV2Report(
        generated_at=generated_at,
        config_version=config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_total_cost=average_total_cost,
        max_total_cost=max_total_cost,
        min_net_expected_value=min_net_expected_value,
        max_cost_to_edge_ratio=max_cost_to_edge_ratio,
        max_edge_shortfall=max_edge_shortfall,
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=reason_code_counts,
        recommendation_rows=rows,
        validation_digest=validation_digest,
    )


def _row_reason_codes(
    recommendation: StrategyRecommendationExpectedValueCostBandV2Input,
    *,
    net_expected_value: Decimal,
    cost_to_edge_ratio: Decimal,
    config: StrategyRecommendationExpectedValueCostBandV2Config,
) -> tuple[str, ...]:
    reason_codes = list(recommendation.reason_codes)
    if recommendation.probability_edge <= ZERO:
        reason_codes.append("cost_band_probability_edge_blocked")
    elif net_expected_value < config.minimum_watch_net_expected_value:
        reason_codes.append("cost_band_net_expected_value_blocked")
    elif cost_to_edge_ratio > config.maximum_watch_cost_to_edge_ratio:
        reason_codes.append("cost_band_cost_ratio_blocked")
    else:
        if net_expected_value < config.minimum_pass_net_expected_value:
            reason_codes.append("cost_band_net_expected_value_watch")
        if cost_to_edge_ratio > config.maximum_pass_cost_to_edge_ratio:
            reason_codes.append("cost_band_cost_ratio_watch")
        if recommendation.confidence < config.minimum_confidence:
            reason_codes.append("cost_band_confidence_watch")
    reason_codes.extend(_cost_component_reason_codes(recommendation))
    if not _has_cost_band_guard(reason_codes):
        reason_codes.append("cost_band_clear")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _cost_component_reason_codes(
    recommendation: StrategyRecommendationExpectedValueCostBandV2Input,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if recommendation.taker_fee > ZERO:
        reason_codes.append("cost_band_taker_fee_present")
    if recommendation.spread > ZERO:
        reason_codes.append("cost_band_spread_present")
    if recommendation.slippage > ZERO:
        reason_codes.append("cost_band_slippage_present")
    if recommendation.settlement_lag > ZERO:
        reason_codes.append("cost_band_settlement_lag_present")
    if recommendation.liquidity_haircut > ZERO:
        reason_codes.append("cost_band_liquidity_haircut_present")
    return tuple(reason_codes)


def _has_cost_band_guard(reason_codes: list[str]) -> bool:
    return any(reason_code in REPORT_GUARD_REASON_CODES for reason_code in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _cost_band(status: str) -> str:
    if status == "blocked":
        return "negative"
    if status == "watch":
        return "thin"
    return "positive"


def _driver_explanations(
    row: StrategyRecommendationExpectedValueCostBandV2Row,
) -> tuple[str, ...]:
    return _driver_explanations_from_values(
        probability_edge=row.probability_edge,
        confidence=row.confidence,
        confidence_adjusted_edge=row.confidence_adjusted_edge,
        liquidity_haircut=row.liquidity_haircut,
        total_cost=row.total_cost,
        net_expected_value=row.net_expected_value,
        cost_to_edge_ratio=row.cost_to_edge_ratio,
        reason_codes=row.reason_codes,
    )


def _driver_explanations_from_values(
    *,
    probability_edge: Decimal,
    confidence: Decimal,
    confidence_adjusted_edge: Decimal,
    liquidity_haircut: Decimal,
    total_cost: Decimal,
    net_expected_value: Decimal,
    cost_to_edge_ratio: Decimal,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    edge_explanation = (
        f"Probability edge {probability_edge} is positive."
        if probability_edge > ZERO
        else f"Probability edge {probability_edge} is not positive."
    )
    return (
        edge_explanation,
        (
            f"Confidence {confidence} applies to edge {probability_edge}, leaving "
            f"confidence-adjusted edge {confidence_adjusted_edge}."
        ),
        (
            f"Liquidity haircut {liquidity_haircut} is included in total cost "
            f"{total_cost}."
        ),
        (
            f"Costs total {total_cost} versus confidence-adjusted edge "
            f"{confidence_adjusted_edge}, leaving net expected value "
            f"{net_expected_value}."
        ),
        _status_explanation(
            probability_edge=probability_edge,
            confidence=confidence,
            net_expected_value=net_expected_value,
            cost_to_edge_ratio=cost_to_edge_ratio,
            reason_codes=reason_codes,
        ),
    )


def _status_explanation(
    *,
    probability_edge: Decimal,
    confidence: Decimal,
    net_expected_value: Decimal,
    cost_to_edge_ratio: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    if "cost_band_probability_edge_blocked" in reason_codes:
        return f"Blocked because probability edge {probability_edge} is not positive."
    if "cost_band_net_expected_value_blocked" in reason_codes:
        return (
            f"Blocked because net expected value {net_expected_value} is below "
            "the watch floor."
        )
    if "cost_band_cost_ratio_blocked" in reason_codes:
        return (
            f"Blocked because cost-to-edge ratio {cost_to_edge_ratio} is above "
            "the block limit."
        )
    if "cost_band_net_expected_value_watch" in reason_codes:
        return (
            f"Watch because net expected value {net_expected_value} is below "
            "the pass floor."
        )
    if "cost_band_cost_ratio_watch" in reason_codes:
        return (
            f"Watch because cost-to-edge ratio {cost_to_edge_ratio} is above "
            "the pass limit."
        )
    if "cost_band_confidence_watch" in reason_codes:
        return (
            f"Watch because confidence {confidence} is below the minimum confidence "
            "requirement."
        )
    return (
        f"Pass because net expected value {net_expected_value} meets the pass floor "
        f"and cost-to-edge ratio {cost_to_edge_ratio} is within limits."
    )


def _report_status(
    rows: tuple[StrategyRecommendationExpectedValueCostBandV2Row, ...],
) -> str:
    if any(row.recommendation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.recommendation_status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyRecommendationExpectedValueCostBandV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cost_band_report_empty",)
    status = _report_status(rows)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in REPORT_GUARD_REASON_CODES
    }
    if not observed:
        return ("cost_band_report_clear",)
    return (
        f"cost_band_report_{'clear' if status == 'pass' else status}",
        *tuple(
            reason_code
            for reason_code in REPORT_GUARD_REASON_CODES
            if reason_code in observed
        ),
    )


def _reason_code_counts(
    rows: tuple[StrategyRecommendationExpectedValueCostBandV2Row, ...],
) -> tuple[StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_inputs(
    recommendations: Iterable[StrategyRecommendationExpectedValueCostBandV2Input],
) -> tuple[StrategyRecommendationExpectedValueCostBandV2Input, ...]:
    if isinstance(recommendations, (str, bytes)):
        raise ValueError("recommendations must be an iterable")
    try:
        rows = tuple(recommendations)
    except TypeError as exc:
        raise ValueError("recommendations must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not StrategyRecommendationExpectedValueCostBandV2Input:
            raise ValueError(
                "recommendations must contain "
                "StrategyRecommendationExpectedValueCostBandV2Input values",
            )
        require_paper_only_flags("recommendation", row)
        reject_unsafe_surface_fields("cost band input", row)
        if row.recommendation_id in seen_ids:
            raise ValueError("recommendations must not contain duplicate ids")
        seen_ids.add(row.recommendation_id)
    return rows


def _normalize_rows(
    rows: Iterable[StrategyRecommendationExpectedValueCostBandV2Row],
) -> tuple[StrategyRecommendationExpectedValueCostBandV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("recommendation_rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("recommendation_rows must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in values:
        if type(row) is not StrategyRecommendationExpectedValueCostBandV2Row:
            raise ValueError(
                "recommendation_rows must contain "
                "StrategyRecommendationExpectedValueCostBandV2Row values",
            )
        require_paper_only_flags("recommendation_row", row)
        reject_unsafe_surface_fields("cost band row", row)
        if row.recommendation_id in seen_ids:
            raise ValueError("recommendation_rows must not contain duplicate ids")
        seen_ids.add(row.recommendation_id)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("recommendation_rows must use stable sequence")
    return values


def _normalize_reason_code_counts(
    value: Iterable[StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount],
) -> tuple[StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in rows:
        if type(row) is not StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        require_paper_only_flags("reason_code_count", row)
        reject_unsafe_surface_fields("cost band reason code count", row)
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate values")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use stable sequence")
        previous_key = key
        seen_codes.add(row.reason_code)
    return rows


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return reason_codes


def _normalize_driver_explanations(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("driver_explanations must be a list or tuple")
    explanations = tuple(value)
    if not explanations:
        raise ValueError("driver_explanations must not be empty")
    for explanation in explanations:
        if type(explanation) is not str:
            raise ValueError("driver_explanations must contain strings")
        if explanation.strip() != explanation or not explanation:
            raise ValueError("driver_explanations must contain public text")
        _reject_unsafe_text("driver_explanations", explanation)
    if len(explanations) != len(set(explanations)):
        raise ValueError("driver_explanations must not contain duplicate values")
    return explanations


def _validate_row(row: StrategyRecommendationExpectedValueCostBandV2Row) -> None:
    if row.confidence_adjusted_edge != _multiply_decimal(
        row.probability_edge,
        row.confidence,
    ):
        raise ValueError("confidence_adjusted_edge must match probability_edge")
    if row.total_cost != _add_decimal(
        row.taker_fee,
        row.spread,
        row.slippage,
        row.settlement_lag,
        row.liquidity_haircut,
    ):
        raise ValueError("total_cost must match component costs")
    if row.net_expected_value != _subtract_decimal(
        row.confidence_adjusted_edge,
        row.total_cost,
    ):
        raise ValueError("net_expected_value must match edge less total_cost")
    if row.cost_to_edge_ratio != _ratio_or_zero(
        row.total_cost,
        row.confidence_adjusted_edge,
    ):
        raise ValueError("cost_to_edge_ratio must match total_cost and edge")
    expected_shortfall = _max_two(_subtract_decimal(ZERO, row.net_expected_value), ZERO)
    if row.edge_shortfall != expected_shortfall:
        raise ValueError("edge_shortfall must match net_expected_value")
    if row.recommendation_status != _row_status(row.reason_codes):
        raise ValueError("recommendation_status must match reason_codes")
    if row.cost_band != _cost_band(row.recommendation_status):
        raise ValueError("cost_band must match recommendation_status")
    if row.driver_explanations != _driver_explanations(row):
        raise ValueError("driver_explanations must match row drivers")
    if row.validation_digest != _row_validation_digest(row):
        raise ValueError("validation_digest must match row")


def _validate_report(report: StrategyRecommendationExpectedValueCostBandV2Report) -> None:
    rows = report.recommendation_rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match recommendation_rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match recommendation_rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match recommendation_rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match recommendation_rows")
    if report.average_total_cost != _average_decimal(tuple(row.total_cost for row in rows)):
        raise ValueError("average_total_cost must match recommendation_rows")
    if report.max_total_cost != _max_decimal(tuple(row.total_cost for row in rows)):
        raise ValueError("max_total_cost must match recommendation_rows")
    if report.min_net_expected_value != _min_decimal(
        tuple(row.net_expected_value for row in rows),
    ):
        raise ValueError("min_net_expected_value must match recommendation_rows")
    if report.max_cost_to_edge_ratio != _max_decimal(
        tuple(row.cost_to_edge_ratio for row in rows),
    ):
        raise ValueError("max_cost_to_edge_ratio must match recommendation_rows")
    if report.max_edge_shortfall != _max_decimal(
        tuple(row.edge_shortfall for row in rows),
    ):
        raise ValueError("max_edge_shortfall must match recommendation_rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match recommendation_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match recommendation_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match recommendation_rows")
    if report.validation_digest != _report_validation_digest(report):
        raise ValueError("validation_digest must match report")


def _row_sort_key(
    row: StrategyRecommendationExpectedValueCostBandV2Row,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        STATUS_SORT_PRIORITY[row.recommendation_status],
        -row.edge_shortfall,
        -row.cost_to_edge_ratio,
        row.recommendation_id,
    )


def _status_count(
    rows: tuple[StrategyRecommendationExpectedValueCostBandV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.recommendation_status == status))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("max_decimal", max(values))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _normalize_decimal("min_decimal", min(values))


def _max_two(left: Decimal, right: Decimal) -> Decimal:
    return left if left >= right else right


def _add_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be {expected_type.__name__}")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_text(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")
    _reject_unsafe_text(field_name, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("reason_codes must not contain duplicate values")
    return tuple(sorted(reason_codes))


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be less than or equal to one")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
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
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _row_validation_digest(
    row: StrategyRecommendationExpectedValueCostBandV2Row,
) -> str:
    return _row_validation_digest_from_parts(
        recommendation_id=row.recommendation_id,
        observed_at=row.observed_at,
        probability_edge=row.probability_edge,
        confidence=row.confidence,
        taker_fee=row.taker_fee,
        spread=row.spread,
        slippage=row.slippage,
        settlement_lag=row.settlement_lag,
        liquidity_haircut=row.liquidity_haircut,
        confidence_adjusted_edge=row.confidence_adjusted_edge,
        total_cost=row.total_cost,
        net_expected_value=row.net_expected_value,
        cost_to_edge_ratio=row.cost_to_edge_ratio,
        edge_shortfall=row.edge_shortfall,
        recommendation_status=row.recommendation_status,
        cost_band=row.cost_band,
        reason_codes=row.reason_codes,
        driver_explanations=row.driver_explanations,
    )


def _row_validation_digest_from_parts(
    *,
    recommendation_id: str,
    observed_at: datetime,
    probability_edge: Decimal,
    confidence: Decimal,
    taker_fee: Decimal,
    spread: Decimal,
    slippage: Decimal,
    settlement_lag: Decimal,
    liquidity_haircut: Decimal,
    confidence_adjusted_edge: Decimal,
    total_cost: Decimal,
    net_expected_value: Decimal,
    cost_to_edge_ratio: Decimal,
    edge_shortfall: Decimal,
    recommendation_status: str,
    cost_band: str,
    reason_codes: tuple[str, ...],
    driver_explanations: tuple[str, ...],
) -> str:
    return _digest_pairs(
        (
            ("schema", "row-v2"),
            ("recommendation_id", recommendation_id),
            ("observed_at", _digest_value(_as_utc("observed_at", observed_at))),
            ("probability_edge", _digest_value(probability_edge)),
            ("confidence", _digest_value(confidence)),
            ("taker_fee", _digest_value(taker_fee)),
            ("spread", _digest_value(spread)),
            ("slippage", _digest_value(slippage)),
            ("settlement_lag", _digest_value(settlement_lag)),
            ("liquidity_haircut", _digest_value(liquidity_haircut)),
            ("confidence_adjusted_edge", _digest_value(confidence_adjusted_edge)),
            ("total_cost", _digest_value(total_cost)),
            ("net_expected_value", _digest_value(net_expected_value)),
            ("cost_to_edge_ratio", _digest_value(cost_to_edge_ratio)),
            ("edge_shortfall", _digest_value(edge_shortfall)),
            ("recommendation_status", recommendation_status),
            ("cost_band", cost_band),
            ("reason_codes", _digest_value(reason_codes)),
            ("driver_explanations", _digest_value(driver_explanations)),
            ("paper_only", "true"),
            ("report_only", "true"),
            ("readonly", "true"),
        ),
    )


def _report_validation_digest(
    report: StrategyRecommendationExpectedValueCostBandV2Report,
) -> str:
    return _report_validation_digest_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        average_total_cost=report.average_total_cost,
        max_total_cost=report.max_total_cost,
        min_net_expected_value=report.min_net_expected_value,
        max_cost_to_edge_ratio=report.max_cost_to_edge_ratio,
        max_edge_shortfall=report.max_edge_shortfall,
        status=report.status,
        reason_codes=report.reason_codes,
        reason_code_counts=report.reason_code_counts,
        rows=report.recommendation_rows,
    )


def _report_validation_digest_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    average_total_cost: Decimal,
    max_total_cost: Decimal,
    min_net_expected_value: Decimal,
    max_cost_to_edge_ratio: Decimal,
    max_edge_shortfall: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    reason_code_counts: tuple[
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount,
        ...,
    ],
    rows: tuple[StrategyRecommendationExpectedValueCostBandV2Row, ...],
) -> str:
    return _digest_pairs(
        (
            ("schema", "report-v2"),
            ("generated_at", _digest_value(_as_utc("generated_at", generated_at))),
            ("config_version", config_version),
            ("candidate_count", _digest_value(candidate_count)),
            ("pass_count", _digest_value(pass_count)),
            ("watch_count", _digest_value(watch_count)),
            ("blocked_count", _digest_value(blocked_count)),
            ("average_total_cost", _digest_value(average_total_cost)),
            ("max_total_cost", _digest_value(max_total_cost)),
            ("min_net_expected_value", _digest_value(min_net_expected_value)),
            ("max_cost_to_edge_ratio", _digest_value(max_cost_to_edge_ratio)),
            ("max_edge_shortfall", _digest_value(max_edge_shortfall)),
            ("status", status),
            ("reason_codes", _digest_value(reason_codes)),
            ("reason_code_counts", _digest_reason_counts(reason_code_counts)),
            ("row_digests", _digest_value(tuple(row.validation_digest for row in rows))),
            ("paper_only", "true"),
            ("report_only", "true"),
            ("readonly", "true"),
        ),
    )


def _digest_reason_counts(
    reason_code_counts: tuple[
        StrategyRecommendationExpectedValueCostBandV2ReasonCodeCount,
        ...,
    ],
) -> str:
    return ",".join(
        f"{row.reason_code}:{_digest_value(row.count)}" for row in reason_code_counts
    )


def _digest_value(value: object) -> str:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is str:
        return value
    if type(value) is tuple:
        return ",".join(_digest_value(item) for item in value)
    raise ValueError("validation digest value has unsupported type")


def _digest_pairs(pairs: tuple[tuple[str, str], ...]) -> str:
    payload = "\n".join(f"{key}={value}" for key, value in pairs)
    return sha256(payload.encode("utf-8")).hexdigest()
