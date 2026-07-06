"""Paper-only portfolio impact reducer for strategy recommendations."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any


DECIMAL_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIDES = ("yes", "no")
REPORT_STATUSES = ("paper_recommendable", "paper_watch", "paper_reject")
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
EDGE_STATUSES = ("edge_pass", "edge_reject")
CONFIDENCE_STATUSES = ("confidence_pass", "confidence_watch")
EXIT_FEASIBILITY_STATUSES = ("exit_liquidity_pass", "exit_liquidity_watch")
CATEGORY_CONCENTRATION_STATUSES = (
    "category_concentration_pass",
    "category_concentration_watch",
)
CORRELATED_OUTCOME_STATUSES = ("correlated_outcome_pass", "correlated_outcome_watch")
SETTLEMENT_DATE_CLUSTER_STATUSES = (
    "settlement_date_cluster_pass",
    "settlement_date_cluster_watch",
)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
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


@dataclass(frozen=True)
class StrategyRecommendationPortfolioImpactV2Config:
    config_version: str
    fee_rate: Decimal
    slippage_rate: Decimal
    min_confidence: Decimal
    min_cost_adjusted_edge: Decimal
    max_exit_liquidity_ratio: Decimal
    max_category_post_share: Decimal
    max_correlated_outcome_post_share: Decimal
    max_settlement_date_post_share: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "fee_rate",
            "slippage_rate",
            "min_confidence",
            "max_exit_liquidity_ratio",
            "max_category_post_share",
            "max_correlated_outcome_post_share",
            "max_settlement_date_post_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_cost_adjusted_edge",
            _normalize_decimal("min_cost_adjusted_edge", self.min_cost_adjusted_edge),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class CandidateStrategyRecommendationV2:
    candidate_id: str
    market_slug: str
    category_id: str
    outcome_group_id: str
    side: str
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence: Decimal
    target_notional: Decimal
    exit_liquidity: Decimal
    spread: Decimal
    settlement_date: date
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
            "category_id",
            "outcome_group_id",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_side(self.side)
        for field_name in ("forecast_probability", "implied_probability", "confidence", "spread"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "target_notional",
            _normalize_positive_decimal("target_notional", self.target_notional),
        )
        object.__setattr__(
            self,
            "exit_liquidity",
            _normalize_positive_decimal("exit_liquidity", self.exit_liquidity),
        )
        object.__setattr__(
            self,
            "settlement_date",
            _require_date("settlement_date", self.settlement_date),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ExistingPortfolioPositionV2:
    position_id: str
    market_slug: str
    category_id: str
    outcome_group_id: str
    notional: Decimal
    settlement_date: date
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "position_id",
            "market_slug",
            "category_id",
            "outcome_group_id",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "notional",
            _normalize_nonnegative_decimal("notional", self.notional),
        )
        object.__setattr__(
            self,
            "settlement_date",
            _require_date("settlement_date", self.settlement_date),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyRecommendationPortfolioImpactV2Report:
    generated_at: datetime
    config_version: str
    candidate_id: str
    market_slug: str
    category_id: str
    outcome_group_id: str
    side: str
    settlement_date: date
    existing_position_count: Decimal
    forecast_probability: Decimal
    implied_probability: Decimal
    confidence: Decimal
    target_notional: Decimal
    exit_liquidity: Decimal
    spread: Decimal
    fee_rate: Decimal
    slippage_rate: Decimal
    min_confidence: Decimal
    min_cost_adjusted_edge: Decimal
    max_exit_liquidity_ratio: Decimal
    max_category_post_share: Decimal
    max_correlated_outcome_post_share: Decimal
    max_settlement_date_post_share: Decimal
    total_existing_notional: Decimal
    total_post_notional: Decimal
    raw_edge: Decimal
    cost_drag: Decimal
    cost_adjusted_edge: Decimal
    confidence_haircut_rate: Decimal
    confidence_haircut_edge: Decimal
    exit_liquidity_ratio: Decimal
    category_existing_notional: Decimal
    category_post_notional: Decimal
    category_post_share: Decimal
    correlated_outcome_existing_notional: Decimal
    correlated_outcome_post_notional: Decimal
    correlated_outcome_post_share: Decimal
    settlement_date_existing_notional: Decimal
    settlement_date_post_notional: Decimal
    settlement_date_post_share: Decimal
    edge_status: str
    confidence_status: str
    exit_feasibility_status: str
    category_concentration_status: str
    correlated_outcome_status: str
    settlement_date_cluster_status: str
    report_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "config_version",
            "candidate_id",
            "market_slug",
            "category_id",
            "outcome_group_id",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_side(self.side)
        object.__setattr__(
            self,
            "settlement_date",
            _require_date("settlement_date", self.settlement_date),
        )
        object.__setattr__(
            self,
            "existing_position_count",
            _normalize_whole_decimal("existing_position_count", self.existing_position_count),
        )
        for field_name in (
            "forecast_probability",
            "implied_probability",
            "confidence",
            "spread",
            "fee_rate",
            "slippage_rate",
            "min_confidence",
            "max_exit_liquidity_ratio",
            "max_category_post_share",
            "max_correlated_outcome_post_share",
            "max_settlement_date_post_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_cost_adjusted_edge",
            "total_existing_notional",
            "total_post_notional",
            "raw_edge",
            "cost_drag",
            "cost_adjusted_edge",
            "confidence_haircut_rate",
            "confidence_haircut_edge",
            "exit_liquidity_ratio",
            "category_existing_notional",
            "category_post_notional",
            "category_post_share",
            "correlated_outcome_existing_notional",
            "correlated_outcome_post_notional",
            "correlated_outcome_post_share",
            "settlement_date_existing_notional",
            "settlement_date_post_notional",
            "settlement_date_post_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("target_notional", "exit_liquidity"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name, choices in (
            ("edge_status", EDGE_STATUSES),
            ("confidence_status", CONFIDENCE_STATUSES),
            ("exit_feasibility_status", EXIT_FEASIBILITY_STATUSES),
            ("category_concentration_status", CATEGORY_CONCENTRATION_STATUSES),
            ("correlated_outcome_status", CORRELATED_OUTCOME_STATUSES),
            ("settlement_date_cluster_status", SETTLEMENT_DATE_CLUSTER_STATUSES),
            ("report_status", REPORT_STATUSES),
        ):
            _require_choice(field_name, getattr(self, field_name), choices)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags(self)
        _validate_report_consistency(self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_strategy_recommendation_portfolio_impact_v2_report(
    candidate: CandidateStrategyRecommendationV2,
    *,
    existing_positions: Iterable[ExistingPortfolioPositionV2],
    config: StrategyRecommendationPortfolioImpactV2Config,
    generated_at: datetime,
) -> StrategyRecommendationPortfolioImpactV2Report:
    if type(candidate) is not CandidateStrategyRecommendationV2:
        raise ValueError("candidate must be a CandidateStrategyRecommendationV2")
    if type(config) is not StrategyRecommendationPortfolioImpactV2Config:
        raise ValueError("config must be a StrategyRecommendationPortfolioImpactV2Config")
    _require_hard_flags(candidate)
    _require_hard_flags(config)
    positions = _normalize_positions(existing_positions)
    normalized_generated_at = _as_utc("generated_at", generated_at)

    total_existing_notional = _sum_decimals(tuple(position.notional for position in positions))
    total_post_notional = _normalize_decimal(
        "total_post_notional",
        total_existing_notional + candidate.target_notional,
    )
    category_existing_notional = _sum_decimals(
        tuple(
            position.notional
            for position in positions
            if position.category_id == candidate.category_id
        ),
    )
    correlated_outcome_existing_notional = _sum_decimals(
        tuple(
            position.notional
            for position in positions
            if position.outcome_group_id == candidate.outcome_group_id
        ),
    )
    settlement_date_existing_notional = _sum_decimals(
        tuple(
            position.notional
            for position in positions
            if position.settlement_date == candidate.settlement_date
        ),
    )
    category_post_notional = _normalize_decimal(
        "category_post_notional",
        category_existing_notional + candidate.target_notional,
    )
    correlated_outcome_post_notional = _normalize_decimal(
        "correlated_outcome_post_notional",
        correlated_outcome_existing_notional + candidate.target_notional,
    )
    settlement_date_post_notional = _normalize_decimal(
        "settlement_date_post_notional",
        settlement_date_existing_notional + candidate.target_notional,
    )
    raw_edge = _normalize_decimal(
        "raw_edge",
        candidate.forecast_probability - candidate.implied_probability,
    )
    cost_drag = _normalize_decimal(
        "cost_drag",
        config.fee_rate + config.slippage_rate + candidate.spread,
    )
    cost_adjusted_edge = _normalize_decimal(
        "cost_adjusted_edge",
        raw_edge - cost_drag,
    )
    confidence_haircut_rate = _normalize_decimal(
        "confidence_haircut_rate",
        ONE - candidate.confidence,
    )
    confidence_haircut_edge = _normalize_decimal(
        "confidence_haircut_edge",
        cost_adjusted_edge * candidate.confidence,
    )
    exit_liquidity_ratio = _ratio(candidate.target_notional, candidate.exit_liquidity)
    category_post_share = _ratio(category_post_notional, total_post_notional)
    correlated_outcome_post_share = _ratio(correlated_outcome_post_notional, total_post_notional)
    settlement_date_post_share = _ratio(settlement_date_post_notional, total_post_notional)

    edge_status = (
        "edge_pass"
        if cost_adjusted_edge >= config.min_cost_adjusted_edge
        else "edge_reject"
    )
    confidence_status = (
        "confidence_pass" if candidate.confidence >= config.min_confidence else "confidence_watch"
    )
    exit_feasibility_status = (
        "exit_liquidity_pass"
        if exit_liquidity_ratio <= config.max_exit_liquidity_ratio
        else "exit_liquidity_watch"
    )
    category_concentration_status = (
        "category_concentration_pass"
        if category_post_share <= config.max_category_post_share
        else "category_concentration_watch"
    )
    correlated_outcome_status = (
        "correlated_outcome_pass"
        if correlated_outcome_post_share <= config.max_correlated_outcome_post_share
        else "correlated_outcome_watch"
    )
    settlement_date_cluster_status = (
        "settlement_date_cluster_pass"
        if settlement_date_post_share <= config.max_settlement_date_post_share
        else "settlement_date_cluster_watch"
    )
    report_status = _report_status(
        edge_status=edge_status,
        confidence_status=confidence_status,
        exit_feasibility_status=exit_feasibility_status,
        category_concentration_status=category_concentration_status,
        correlated_outcome_status=correlated_outcome_status,
        settlement_date_cluster_status=settlement_date_cluster_status,
    )

    return StrategyRecommendationPortfolioImpactV2Report(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        category_id=candidate.category_id,
        outcome_group_id=candidate.outcome_group_id,
        side=candidate.side,
        settlement_date=candidate.settlement_date,
        existing_position_count=Decimal(len(positions)),
        forecast_probability=candidate.forecast_probability,
        implied_probability=candidate.implied_probability,
        confidence=candidate.confidence,
        target_notional=candidate.target_notional,
        exit_liquidity=candidate.exit_liquidity,
        spread=candidate.spread,
        fee_rate=config.fee_rate,
        slippage_rate=config.slippage_rate,
        min_confidence=config.min_confidence,
        min_cost_adjusted_edge=config.min_cost_adjusted_edge,
        max_exit_liquidity_ratio=config.max_exit_liquidity_ratio,
        max_category_post_share=config.max_category_post_share,
        max_correlated_outcome_post_share=config.max_correlated_outcome_post_share,
        max_settlement_date_post_share=config.max_settlement_date_post_share,
        total_existing_notional=total_existing_notional,
        total_post_notional=total_post_notional,
        raw_edge=raw_edge,
        cost_drag=cost_drag,
        cost_adjusted_edge=cost_adjusted_edge,
        confidence_haircut_rate=confidence_haircut_rate,
        confidence_haircut_edge=confidence_haircut_edge,
        exit_liquidity_ratio=exit_liquidity_ratio,
        category_existing_notional=category_existing_notional,
        category_post_notional=category_post_notional,
        category_post_share=category_post_share,
        correlated_outcome_existing_notional=correlated_outcome_existing_notional,
        correlated_outcome_post_notional=correlated_outcome_post_notional,
        correlated_outcome_post_share=correlated_outcome_post_share,
        settlement_date_existing_notional=settlement_date_existing_notional,
        settlement_date_post_notional=settlement_date_post_notional,
        settlement_date_post_share=settlement_date_post_share,
        edge_status=edge_status,
        confidence_status=confidence_status,
        exit_feasibility_status=exit_feasibility_status,
        category_concentration_status=category_concentration_status,
        correlated_outcome_status=correlated_outcome_status,
        settlement_date_cluster_status=settlement_date_cluster_status,
        report_status=report_status,
        reason_codes=_reason_codes(
            edge_status=edge_status,
            confidence_status=confidence_status,
            exit_feasibility_status=exit_feasibility_status,
            category_concentration_status=category_concentration_status,
            correlated_outcome_status=correlated_outcome_status,
            settlement_date_cluster_status=settlement_date_cluster_status,
        ),
    )


def strategy_recommendation_portfolio_impact_v2_payload(
    report: StrategyRecommendationPortfolioImpactV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationPortfolioImpactV2Report:
        raise ValueError("report must be a StrategyRecommendationPortfolioImpactV2Report")
    _require_hard_flags(report)
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")
    payload = _report_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return validate_strategy_recommendation_portfolio_impact_v2_public_payload(payload)


def validate_strategy_recommendation_portfolio_impact_v2_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or isinstance(payload, (str, bytes)):
        raise ValueError("public payload must be a mapping")
    ready = _validate_public_payload_value(payload)
    if not isinstance(ready, dict):
        raise ValueError("public payload must be a JSON object")
    digest = ready.get("derived_validation_digest")
    if digest is not None:
        if type(digest) is not str:
            raise ValueError("derived_validation_digest must be a string")
        _require_sha256("derived_validation_digest", digest)
        digest_source = dict(ready)
        digest_source.pop("derived_validation_digest")
        if digest != _public_payload_digest(digest_source):
            raise ValueError("derived_validation_digest mismatch")
    return ready


def _normalize_positions(
    positions: Iterable[ExistingPortfolioPositionV2],
) -> tuple[ExistingPortfolioPositionV2, ...]:
    if isinstance(positions, (str, bytes)):
        raise ValueError("existing_positions must be an iterable")
    try:
        items = tuple(positions)
    except TypeError as exc:
        raise ValueError("existing_positions must be an iterable") from exc
    for position in items:
        if type(position) is not ExistingPortfolioPositionV2:
            raise ValueError(
                "existing_positions must contain only ExistingPortfolioPositionV2 values",
            )
        _require_hard_flags(position)
    return tuple(sorted(items, key=lambda item: (item.settlement_date, item.position_id)))


def _report_status(
    *,
    edge_status: str,
    confidence_status: str,
    exit_feasibility_status: str,
    category_concentration_status: str,
    correlated_outcome_status: str,
    settlement_date_cluster_status: str,
) -> str:
    if edge_status == "edge_reject":
        return "paper_reject"
    watch_statuses = (
        confidence_status,
        exit_feasibility_status,
        category_concentration_status,
        correlated_outcome_status,
        settlement_date_cluster_status,
    )
    if any(status.endswith(f"_{WATCH_STATUS}") for status in watch_statuses):
        return "paper_watch"
    return "paper_recommendable"


def _reason_codes(
    *,
    edge_status: str,
    confidence_status: str,
    exit_feasibility_status: str,
    category_concentration_status: str,
    correlated_outcome_status: str,
    settlement_date_cluster_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if edge_status == "edge_pass":
        reason_codes.append("cost_adjusted_edge_passed")
    else:
        reason_codes.append("cost_adjusted_edge_below_minimum")
    if confidence_status == "confidence_pass":
        reason_codes.append("confidence_passed")
    else:
        reason_codes.append("confidence_below_minimum")
    if exit_feasibility_status == "exit_liquidity_pass":
        reason_codes.append("exit_liquidity_ratio_passed")
    else:
        reason_codes.append("exit_liquidity_ratio_above_limit")
    if category_concentration_status == "category_concentration_pass":
        reason_codes.append("category_concentration_passed")
    else:
        reason_codes.append("category_concentration_above_limit")
    if correlated_outcome_status == "correlated_outcome_pass":
        reason_codes.append("correlated_outcome_exposure_passed")
    else:
        reason_codes.append("correlated_outcome_exposure_above_limit")
    if settlement_date_cluster_status == "settlement_date_cluster_pass":
        reason_codes.append("settlement_date_cluster_passed")
    else:
        reason_codes.append("settlement_date_cluster_above_limit")
    return tuple(reason_codes)


def _validate_report_consistency(report: StrategyRecommendationPortfolioImpactV2Report) -> None:
    if report.total_post_notional != _normalize_decimal(
        "total_post_notional",
        report.total_existing_notional + report.target_notional,
    ):
        raise ValueError("total_post_notional must reconcile")
    if report.raw_edge != _normalize_decimal(
        "raw_edge",
        report.forecast_probability - report.implied_probability,
    ):
        raise ValueError("raw_edge must match probabilities")
    if report.cost_drag != _normalize_decimal(
        "cost_drag",
        report.fee_rate + report.slippage_rate + report.spread,
    ):
        raise ValueError("cost_drag must match cost inputs")
    if report.cost_adjusted_edge != _normalize_decimal(
        "cost_adjusted_edge",
        report.raw_edge - report.cost_drag,
    ):
        raise ValueError("cost_adjusted_edge must match raw_edge minus cost_drag")
    if report.confidence_haircut_rate != _normalize_decimal(
        "confidence_haircut_rate",
        ONE - report.confidence,
    ):
        raise ValueError("confidence_haircut_rate must match confidence")
    if report.confidence_haircut_edge != _normalize_decimal(
        "confidence_haircut_edge",
        report.cost_adjusted_edge * report.confidence,
    ):
        raise ValueError("confidence_haircut_edge must match confidence")
    if report.exit_liquidity_ratio != _ratio(report.target_notional, report.exit_liquidity):
        raise ValueError("exit_liquidity_ratio must match target_notional and exit_liquidity")
    if report.category_post_notional != _normalize_decimal(
        "category_post_notional",
        report.category_existing_notional + report.target_notional,
    ):
        raise ValueError("category_post_notional must reconcile")
    if report.category_post_share != _ratio(report.category_post_notional, report.total_post_notional):
        raise ValueError("category_post_share must reconcile")
    if report.correlated_outcome_post_notional != _normalize_decimal(
        "correlated_outcome_post_notional",
        report.correlated_outcome_existing_notional + report.target_notional,
    ):
        raise ValueError("correlated_outcome_post_notional must reconcile")
    if report.correlated_outcome_post_share != _ratio(
        report.correlated_outcome_post_notional,
        report.total_post_notional,
    ):
        raise ValueError("correlated_outcome_post_share must reconcile")
    if report.settlement_date_post_notional != _normalize_decimal(
        "settlement_date_post_notional",
        report.settlement_date_existing_notional + report.target_notional,
    ):
        raise ValueError("settlement_date_post_notional must reconcile")
    if report.settlement_date_post_share != _ratio(
        report.settlement_date_post_notional,
        report.total_post_notional,
    ):
        raise ValueError("settlement_date_post_share must reconcile")

    expected_edge_status = (
        "edge_pass"
        if report.cost_adjusted_edge >= report.min_cost_adjusted_edge
        else "edge_reject"
    )
    expected_confidence_status = (
        "confidence_pass" if report.confidence >= report.min_confidence else "confidence_watch"
    )
    expected_exit_feasibility_status = (
        "exit_liquidity_pass"
        if report.exit_liquidity_ratio <= report.max_exit_liquidity_ratio
        else "exit_liquidity_watch"
    )
    expected_category_concentration_status = (
        "category_concentration_pass"
        if report.category_post_share <= report.max_category_post_share
        else "category_concentration_watch"
    )
    expected_correlated_outcome_status = (
        "correlated_outcome_pass"
        if report.correlated_outcome_post_share <= report.max_correlated_outcome_post_share
        else "correlated_outcome_watch"
    )
    expected_settlement_date_cluster_status = (
        "settlement_date_cluster_pass"
        if report.settlement_date_post_share <= report.max_settlement_date_post_share
        else "settlement_date_cluster_watch"
    )
    if report.edge_status != expected_edge_status:
        raise ValueError("edge_status must match thresholds")
    if report.confidence_status != expected_confidence_status:
        raise ValueError("confidence_status must match thresholds")
    if report.exit_feasibility_status != expected_exit_feasibility_status:
        raise ValueError("exit_feasibility_status must match thresholds")
    if report.category_concentration_status != expected_category_concentration_status:
        raise ValueError("category_concentration_status must match thresholds")
    if report.correlated_outcome_status != expected_correlated_outcome_status:
        raise ValueError("correlated_outcome_status must match thresholds")
    if report.settlement_date_cluster_status != expected_settlement_date_cluster_status:
        raise ValueError("settlement_date_cluster_status must match thresholds")
    expected_report_status = _report_status(
        edge_status=report.edge_status,
        confidence_status=report.confidence_status,
        exit_feasibility_status=report.exit_feasibility_status,
        category_concentration_status=report.category_concentration_status,
        correlated_outcome_status=report.correlated_outcome_status,
        settlement_date_cluster_status=report.settlement_date_cluster_status,
    )
    if report.report_status != expected_report_status:
        raise ValueError("report_status must match component statuses")
    expected_reason_codes = _reason_codes(
        edge_status=report.edge_status,
        confidence_status=report.confidence_status,
        exit_feasibility_status=report.exit_feasibility_status,
        category_concentration_status=report.category_concentration_status,
        correlated_outcome_status=report.correlated_outcome_status,
        settlement_date_cluster_status=report.settlement_date_cluster_status,
    )
    if report.reason_codes != _normalize_reason_codes("reason_codes", expected_reason_codes):
        raise ValueError("reason_codes must match component statuses")


def _report_payload_without_digest(report: StrategyRecommendationPortfolioImpactV2Report) -> dict[str, Any]:
    return {
        "generated_at": _payload_value(report.generated_at),
        "config_version": report.config_version,
        "candidate_id": report.candidate_id,
        "market_slug": report.market_slug,
        "category_id": report.category_id,
        "outcome_group_id": report.outcome_group_id,
        "side": report.side,
        "settlement_date": _payload_value(report.settlement_date),
        "existing_position_count": _payload_value(report.existing_position_count),
        "forecast_probability": _payload_value(report.forecast_probability),
        "implied_probability": _payload_value(report.implied_probability),
        "confidence": _payload_value(report.confidence),
        "target_notional": _payload_value(report.target_notional),
        "exit_liquidity": _payload_value(report.exit_liquidity),
        "spread": _payload_value(report.spread),
        "fee_rate": _payload_value(report.fee_rate),
        "slippage_rate": _payload_value(report.slippage_rate),
        "min_confidence": _payload_value(report.min_confidence),
        "min_cost_adjusted_edge": _payload_value(report.min_cost_adjusted_edge),
        "max_exit_liquidity_ratio": _payload_value(report.max_exit_liquidity_ratio),
        "max_category_post_share": _payload_value(report.max_category_post_share),
        "max_correlated_outcome_post_share": _payload_value(
            report.max_correlated_outcome_post_share,
        ),
        "max_settlement_date_post_share": _payload_value(report.max_settlement_date_post_share),
        "total_existing_notional": _payload_value(report.total_existing_notional),
        "total_post_notional": _payload_value(report.total_post_notional),
        "raw_edge": _payload_value(report.raw_edge),
        "cost_drag": _payload_value(report.cost_drag),
        "cost_adjusted_edge": _payload_value(report.cost_adjusted_edge),
        "confidence_haircut_rate": _payload_value(report.confidence_haircut_rate),
        "confidence_haircut_edge": _payload_value(report.confidence_haircut_edge),
        "exit_liquidity_ratio": _payload_value(report.exit_liquidity_ratio),
        "category_existing_notional": _payload_value(report.category_existing_notional),
        "category_post_notional": _payload_value(report.category_post_notional),
        "category_post_share": _payload_value(report.category_post_share),
        "correlated_outcome_existing_notional": _payload_value(
            report.correlated_outcome_existing_notional,
        ),
        "correlated_outcome_post_notional": _payload_value(
            report.correlated_outcome_post_notional,
        ),
        "correlated_outcome_post_share": _payload_value(report.correlated_outcome_post_share),
        "settlement_date_existing_notional": _payload_value(
            report.settlement_date_existing_notional,
        ),
        "settlement_date_post_notional": _payload_value(report.settlement_date_post_notional),
        "settlement_date_post_share": _payload_value(report.settlement_date_post_share),
        "edge_status": report.edge_status,
        "confidence_status": report.confidence_status,
        "exit_feasibility_status": report.exit_feasibility_status,
        "category_concentration_status": report.category_concentration_status,
        "correlated_outcome_status": report.correlated_outcome_status,
        "settlement_date_cluster_status": report.settlement_date_cluster_status,
        "report_status": report.report_status,
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_validation_digest(report: StrategyRecommendationPortfolioImpactV2Report) -> str:
    return _public_payload_digest(_report_payload_without_digest(report))


def _public_payload_digest(payload_without_digest: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _payload_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return format(_normalize_decimal("payload decimal", value), "f")
    if isinstance(value, datetime):
        return _payload_datetime(value)
    if type(value) is date:
        return value.isoformat()
    if type(value) is str:
        _require_canonical_public_string("public payload value", value)
        return value
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("public payload value must use Decimal strings")
    if type(value) is float:
        raise ValueError("public payload value must not be a float")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    raise ValueError("public payload value is not JSON serializable")


def _validate_public_payload_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload key must be a string")
            _require_canonical_public_string("public payload key", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            ready[key] = _validate_public_payload_value(item)
        return ready
    if isinstance(value, tuple):
        return [_validate_public_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_validate_public_payload_value(item) for item in value]
    if type(value) is str:
        _require_canonical_public_string("public payload value", value)
        return value
    if type(value) is bool:
        return value
    if value is None:
        return None
    if isinstance(value, Decimal):
        return _payload_value(value)
    if type(value) in (int, float):
        raise ValueError("public payload value must not use native numeric types")
    raise ValueError("public payload value is not JSON serializable")


def _payload_datetime(value: datetime) -> str:
    text = _as_utc("payload datetime", value).isoformat()
    if text.endswith("+00:00"):
        return f"{text[:-6]}Z"
    return text


def _normalize_reason_codes(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_public_string("reason_code", item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(items))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    return _normalize_decimal("sum", sum(values, Decimal("0")))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _normalize_nonnegative_decimal("ratio numerator", numerator)
    denominator = _normalize_positive_decimal("ratio denominator", denominator)
    with localcontext() as context:
        context.prec = 28
        return _normalize_decimal("ratio", numerator / denominator)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        context.prec = 28
        return value.quantize(DECIMAL_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_date(field_name: str, value: date) -> date:
    if type(value) is not date:
        raise ValueError(f"{field_name} must be a date")
    return value


def _require_side(value: str) -> None:
    _require_canonical_public_string("side", value)
    if value not in SIDES:
        raise ValueError("side must be yes or no")


def _require_choice(field_name: str, value: str, choices: tuple[str, ...]) -> None:
    _require_canonical_public_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_sha256(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_canonical_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe value")


__all__ = (
    "CandidateStrategyRecommendationV2",
    "ExistingPortfolioPositionV2",
    "StrategyRecommendationPortfolioImpactV2Config",
    "StrategyRecommendationPortfolioImpactV2Report",
    "build_strategy_recommendation_portfolio_impact_v2_report",
    "strategy_recommendation_portfolio_impact_v2_payload",
    "validate_strategy_recommendation_portfolio_impact_v2_public_payload",
)
