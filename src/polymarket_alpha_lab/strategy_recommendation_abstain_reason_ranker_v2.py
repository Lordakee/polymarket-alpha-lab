"""Pure Phase 1 abstain/manual-review reason ranker v2."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RECOMMENDATION_ABSTAIN_REASON_RANKER_V2_CONFIG_VERSION = (
    "strategy-recommendation-abstain-reason-ranker-v2"
)

COUNT_QUANTUM = Decimal("1")
BPS_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_BPS = Decimal("0.000000")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SELECTED_SIDES = ("yes", "no")
DECISION_STATUSES = ("abstain", "manual_review")
ROW_REASON_CODES = (
    "insufficient_edge_after_cost",
    "stale_sources",
    "weak_evidence_quorum",
    "contradiction_severity",
    "resolution_ambiguity",
    "liquidity_risk",
    "category_budget_pressure",
    "no_rankable_abstain_reason",
)
REPORT_REASON_CODES = ROW_REASON_CODES + ("no_abstain_decisions",)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_ABSTAIN_REASON_RANKER_V2_CONFIG_VERSION",
    "StrategyRecommendationAbstainReasonRankerV2Config",
    "StrategyRecommendationAbstainReasonRankerV2Input",
    "StrategyRecommendationAbstainReasonRankerV2RankedReason",
    "StrategyRecommendationAbstainReasonRankerV2Report",
    "rank_strategy_recommendation_abstain_reasons_v2",
    "strategy_recommendation_abstain_reason_ranker_v2_payload",
)


@dataclass(frozen=True)
class StrategyRecommendationAbstainReasonRankerV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_ABSTAIN_REASON_RANKER_V2_CONFIG_VERSION
    )
    minimum_edge_after_cost_bps: Decimal = Decimal("25.000000")
    edge_shortfall_weight_bps: Decimal = Decimal("1.000000")
    stale_source_weight_bps: Decimal = Decimal("100.000000")
    weak_evidence_quorum_weight_bps: Decimal = Decimal("100.000000")
    contradiction_severity_weight_bps: Decimal = Decimal("100.000000")
    resolution_ambiguity_weight_bps: Decimal = Decimal("100.000000")
    liquidity_risk_weight_bps: Decimal = Decimal("100.000000")
    category_budget_pressure_weight_bps: Decimal = Decimal("100.000000")
    stale_source_reason_threshold: Decimal = Decimal("0.250000")
    evidence_quorum_floor: Decimal = Decimal("0.700000")
    contradiction_severity_reason_threshold: Decimal = Decimal("0.250000")
    resolution_ambiguity_reason_threshold: Decimal = Decimal("0.250000")
    liquidity_risk_reason_threshold: Decimal = Decimal("0.250000")
    category_budget_pressure_reason_threshold: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationAbstainReasonRankerV2Config:
            raise TypeError(
                "StrategyRecommendationAbstainReasonRankerV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationAbstainReasonRankerV2Config:
            raise ValueError(
                "config must be exactly StrategyRecommendationAbstainReasonRankerV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "minimum_edge_after_cost_bps",
            _normalize_nonnegative_bps(
                "minimum_edge_after_cost_bps",
                self.minimum_edge_after_cost_bps,
            ),
        )
        for field_name in (
            "edge_shortfall_weight_bps",
            "stale_source_weight_bps",
            "weak_evidence_quorum_weight_bps",
            "contradiction_severity_weight_bps",
            "resolution_ambiguity_weight_bps",
            "liquidity_risk_weight_bps",
            "category_budget_pressure_weight_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_source_reason_threshold",
            "evidence_quorum_floor",
            "contradiction_severity_reason_threshold",
            "resolution_ambiguity_reason_threshold",
            "liquidity_risk_reason_threshold",
            "category_budget_pressure_reason_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags(
            "StrategyRecommendationAbstainReasonRankerV2Config",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationAbstainReasonRankerV2Input:
    recommendation_id: str
    market_slug: str
    selected_side: str
    decision_status: str
    edge_after_cost_bps: Decimal
    source_staleness_score: Decimal
    evidence_quorum_score: Decimal
    contradiction_severity_score: Decimal
    resolution_ambiguity_score: Decimal
    liquidity_risk_score: Decimal
    category_budget_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationAbstainReasonRankerV2Input:
            raise TypeError(
                "StrategyRecommendationAbstainReasonRankerV2Input does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationAbstainReasonRankerV2Input:
            raise ValueError(
                "decision must be exactly StrategyRecommendationAbstainReasonRankerV2Input",
            )
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_choice("selected_side", self.selected_side, SELECTED_SIDES)
        _require_choice("decision_status", self.decision_status, DECISION_STATUSES)
        object.__setattr__(
            self,
            "edge_after_cost_bps",
            _normalize_bps("edge_after_cost_bps", self.edge_after_cost_bps),
        )
        for field_name in (
            "source_staleness_score",
            "evidence_quorum_score",
            "contradiction_severity_score",
            "resolution_ambiguity_score",
            "liquidity_risk_score",
            "category_budget_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags(
            "StrategyRecommendationAbstainReasonRankerV2Input",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationAbstainReasonRankerV2RankedReason:
    reason_rank: Decimal
    recommendation_id: str
    market_slug: str
    selected_side: str
    decision_status: str
    reason_code: str
    reason_score_bps: Decimal
    factor_value: Decimal
    threshold_value: Decimal
    edge_after_cost_bps: Decimal
    source_staleness_score: Decimal
    evidence_quorum_score: Decimal
    contradiction_severity_score: Decimal
    resolution_ambiguity_score: Decimal
    liquidity_risk_score: Decimal
    category_budget_pressure_score: Decimal
    reason_digest: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationAbstainReasonRankerV2RankedReason:
            raise TypeError(
                "StrategyRecommendationAbstainReasonRankerV2RankedReason does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationAbstainReasonRankerV2RankedReason:
            raise ValueError(
                "ranked reason must be exactly StrategyRecommendationAbstainReasonRankerV2RankedReason",
            )
        object.__setattr__(
            self,
            "reason_rank",
            _normalize_positive_count("reason_rank", self.reason_rank),
        )
        _require_canonical_string("recommendation_id", self.recommendation_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_choice("selected_side", self.selected_side, SELECTED_SIDES)
        _require_choice("decision_status", self.decision_status, DECISION_STATUSES)
        _require_choice("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "reason_score_bps",
            _normalize_nonnegative_bps("reason_score_bps", self.reason_score_bps),
        )
        for field_name in ("factor_value", "threshold_value"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_after_cost_bps",
            _normalize_bps("edge_after_cost_bps", self.edge_after_cost_bps),
        )
        for field_name in (
            "source_staleness_score",
            "evidence_quorum_score",
            "contradiction_severity_score",
            "resolution_ambiguity_score",
            "liquidity_risk_score",
            "category_budget_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_ranked_reason(self)
        require_paper_only_flags(
            "StrategyRecommendationAbstainReasonRankerV2RankedReason",
            self,
        )
        expected_digest = _ranked_reason_digest(self)
        if self.reason_digest is None:
            object.__setattr__(self, "reason_digest", expected_digest)
        else:
            _require_digest("reason_digest", self.reason_digest)
            if self.reason_digest != expected_digest:
                raise ValueError("reason_digest must match ranked reason")


@dataclass(frozen=True)
class StrategyRecommendationAbstainReasonRankerV2Report:
    config_version: str
    decision_count: Decimal
    ranked_reason_count: Decimal
    top_reason_code: str | None
    reason_codes: tuple[str, ...]
    ranked_reasons: tuple[StrategyRecommendationAbstainReasonRankerV2RankedReason, ...]
    report_digest: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRecommendationAbstainReasonRankerV2Report:
            raise TypeError(
                "StrategyRecommendationAbstainReasonRankerV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRecommendationAbstainReasonRankerV2Report:
            raise ValueError(
                "report must be exactly StrategyRecommendationAbstainReasonRankerV2Report",
            )
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "decision_count",
            _normalize_nonnegative_count("decision_count", self.decision_count),
        )
        object.__setattr__(
            self,
            "ranked_reason_count",
            _normalize_nonnegative_count(
                "ranked_reason_count",
                self.ranked_reason_count,
            ),
        )
        if self.top_reason_code is not None:
            _require_choice("top_reason_code", self.top_reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "ranked_reasons",
            _normalize_ranked_reasons(self.ranked_reasons),
        )
        _validate_report(self)
        require_paper_only_flags(
            "StrategyRecommendationAbstainReasonRankerV2Report",
            self,
        )
        expected_digest = _report_digest(self)
        if self.report_digest is None:
            object.__setattr__(self, "report_digest", expected_digest)
        else:
            _require_digest("report_digest", self.report_digest)
            if self.report_digest != expected_digest:
                raise ValueError("report_digest must match report")

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_recommendation_abstain_reason_ranker_v2_payload(self)


def rank_strategy_recommendation_abstain_reasons_v2(
    decisions: Iterable[StrategyRecommendationAbstainReasonRankerV2Input],
    *,
    config: StrategyRecommendationAbstainReasonRankerV2Config | None = None,
) -> StrategyRecommendationAbstainReasonRankerV2Report:
    """Rank paper-only reasons for abstain and manual-review decisions."""

    active_config = config or StrategyRecommendationAbstainReasonRankerV2Config()
    if type(active_config) is not StrategyRecommendationAbstainReasonRankerV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationAbstainReasonRankerV2Config",
        )
    require_paper_only_flags("config", active_config)
    normalized_decisions = _normalize_inputs(decisions)
    _validate_unique_decisions(normalized_decisions)

    unranked_reasons: list[StrategyRecommendationAbstainReasonRankerV2RankedReason] = []
    for decision in normalized_decisions:
        unranked_reasons.extend(
            _ranked_reasons_for_decision(
                decision,
                reason_rank=Decimal("1"),
                config=active_config,
            ),
        )

    sorted_reasons = tuple(sorted(unranked_reasons, key=_rank_sort_key))
    ranked_reasons = tuple(
        _replace_reason_rank(reason, Decimal(index))
        for index, reason in enumerate(sorted_reasons, start=1)
    )
    top_reason = ranked_reasons[0] if ranked_reasons else None

    return StrategyRecommendationAbstainReasonRankerV2Report(
        config_version=active_config.config_version,
        decision_count=Decimal(len(normalized_decisions)),
        ranked_reason_count=Decimal(len(ranked_reasons)),
        top_reason_code=None if top_reason is None else top_reason.reason_code,
        reason_codes=_report_reason_codes(ranked_reasons),
        ranked_reasons=ranked_reasons,
    )


def strategy_recommendation_abstain_reason_ranker_v2_payload(
    report: StrategyRecommendationAbstainReasonRankerV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationAbstainReasonRankerV2Report:
        raise ValueError(
            "report must be a StrategyRecommendationAbstainReasonRankerV2Report",
        )
    require_paper_only_flags("report", report)
    payload = {
        "config_version": report.config_version,
        "decision_count": report.decision_count,
        "ranked_reason_count": report.ranked_reason_count,
        "top_reason_code": report.top_reason_code,
        "reason_codes": report.reason_codes,
        "ranked_reasons": tuple(_ranked_reason_payload(row) for row in report.ranked_reasons),
        "report_digest": report.report_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    reject_unsafe_surface_fields(
        "strategy abstain reason ranker v2",
        payload,
    )
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _ranked_reasons_for_decision(
    decision: StrategyRecommendationAbstainReasonRankerV2Input,
    *,
    reason_rank: Decimal,
    config: StrategyRecommendationAbstainReasonRankerV2Config,
) -> tuple[StrategyRecommendationAbstainReasonRankerV2RankedReason, ...]:
    reasons: list[StrategyRecommendationAbstainReasonRankerV2RankedReason] = []

    edge_shortfall_bps = _nonnegative_bps_delta(
        config.minimum_edge_after_cost_bps,
        decision.edge_after_cost_bps,
    )
    if edge_shortfall_bps > ZERO_BPS:
        reasons.append(
            _reason_row(
                decision,
                reason_rank=reason_rank,
                reason_code="insufficient_edge_after_cost",
                reason_score_bps=_score_bps(
                    edge_shortfall_bps,
                    config.edge_shortfall_weight_bps,
                ),
                factor_value=edge_shortfall_bps,
                threshold_value=config.minimum_edge_after_cost_bps,
            ),
        )

    if decision.source_staleness_score >= config.stale_source_reason_threshold:
        reasons.append(
            _reason_row(
                decision,
                reason_rank=reason_rank,
                reason_code="stale_sources",
                reason_score_bps=_score_bps(
                    decision.source_staleness_score,
                    config.stale_source_weight_bps,
                ),
                factor_value=decision.source_staleness_score,
                threshold_value=config.stale_source_reason_threshold,
            ),
        )

    evidence_quorum_gap = _nonnegative_ratio_delta(
        config.evidence_quorum_floor,
        decision.evidence_quorum_score,
    )
    if evidence_quorum_gap > ZERO_RATIO:
        reasons.append(
            _reason_row(
                decision,
                reason_rank=reason_rank,
                reason_code="weak_evidence_quorum",
                reason_score_bps=_score_bps(
                    evidence_quorum_gap,
                    config.weak_evidence_quorum_weight_bps,
                ),
                factor_value=evidence_quorum_gap,
                threshold_value=config.evidence_quorum_floor,
            ),
        )

    if (
        decision.contradiction_severity_score
        >= config.contradiction_severity_reason_threshold
    ):
        reasons.append(
            _reason_row(
                decision,
                reason_rank=reason_rank,
                reason_code="contradiction_severity",
                reason_score_bps=_score_bps(
                    decision.contradiction_severity_score,
                    config.contradiction_severity_weight_bps,
                ),
                factor_value=decision.contradiction_severity_score,
                threshold_value=config.contradiction_severity_reason_threshold,
            ),
        )

    if decision.resolution_ambiguity_score >= config.resolution_ambiguity_reason_threshold:
        reasons.append(
            _reason_row(
                decision,
                reason_rank=reason_rank,
                reason_code="resolution_ambiguity",
                reason_score_bps=_score_bps(
                    decision.resolution_ambiguity_score,
                    config.resolution_ambiguity_weight_bps,
                ),
                factor_value=decision.resolution_ambiguity_score,
                threshold_value=config.resolution_ambiguity_reason_threshold,
            ),
        )

    if decision.liquidity_risk_score >= config.liquidity_risk_reason_threshold:
        reasons.append(
            _reason_row(
                decision,
                reason_rank=reason_rank,
                reason_code="liquidity_risk",
                reason_score_bps=_score_bps(
                    decision.liquidity_risk_score,
                    config.liquidity_risk_weight_bps,
                ),
                factor_value=decision.liquidity_risk_score,
                threshold_value=config.liquidity_risk_reason_threshold,
            ),
        )

    if (
        decision.category_budget_pressure_score
        >= config.category_budget_pressure_reason_threshold
    ):
        reasons.append(
            _reason_row(
                decision,
                reason_rank=reason_rank,
                reason_code="category_budget_pressure",
                reason_score_bps=_score_bps(
                    decision.category_budget_pressure_score,
                    config.category_budget_pressure_weight_bps,
                ),
                factor_value=decision.category_budget_pressure_score,
                threshold_value=config.category_budget_pressure_reason_threshold,
            ),
        )

    if reasons:
        return tuple(reasons)
    return (
        _reason_row(
            decision,
            reason_rank=reason_rank,
            reason_code="no_rankable_abstain_reason",
            reason_score_bps=ZERO_BPS,
            factor_value=ZERO_RATIO,
            threshold_value=ZERO_RATIO,
        ),
    )


def _reason_row(
    decision: StrategyRecommendationAbstainReasonRankerV2Input,
    *,
    reason_rank: Decimal,
    reason_code: str,
    reason_score_bps: Decimal,
    factor_value: Decimal,
    threshold_value: Decimal,
) -> StrategyRecommendationAbstainReasonRankerV2RankedReason:
    return StrategyRecommendationAbstainReasonRankerV2RankedReason(
        reason_rank=reason_rank,
        recommendation_id=decision.recommendation_id,
        market_slug=decision.market_slug,
        selected_side=decision.selected_side,
        decision_status=decision.decision_status,
        reason_code=reason_code,
        reason_score_bps=reason_score_bps,
        factor_value=factor_value,
        threshold_value=threshold_value,
        edge_after_cost_bps=decision.edge_after_cost_bps,
        source_staleness_score=decision.source_staleness_score,
        evidence_quorum_score=decision.evidence_quorum_score,
        contradiction_severity_score=decision.contradiction_severity_score,
        resolution_ambiguity_score=decision.resolution_ambiguity_score,
        liquidity_risk_score=decision.liquidity_risk_score,
        category_budget_pressure_score=decision.category_budget_pressure_score,
    )


def _replace_reason_rank(
    row: StrategyRecommendationAbstainReasonRankerV2RankedReason,
    reason_rank: Decimal,
) -> StrategyRecommendationAbstainReasonRankerV2RankedReason:
    return StrategyRecommendationAbstainReasonRankerV2RankedReason(
        reason_rank=reason_rank,
        recommendation_id=row.recommendation_id,
        market_slug=row.market_slug,
        selected_side=row.selected_side,
        decision_status=row.decision_status,
        reason_code=row.reason_code,
        reason_score_bps=row.reason_score_bps,
        factor_value=row.factor_value,
        threshold_value=row.threshold_value,
        edge_after_cost_bps=row.edge_after_cost_bps,
        source_staleness_score=row.source_staleness_score,
        evidence_quorum_score=row.evidence_quorum_score,
        contradiction_severity_score=row.contradiction_severity_score,
        resolution_ambiguity_score=row.resolution_ambiguity_score,
        liquidity_risk_score=row.liquidity_risk_score,
        category_budget_pressure_score=row.category_budget_pressure_score,
        reason_digest=row.reason_digest,
    )


def _rank_sort_key(
    row: StrategyRecommendationAbstainReasonRankerV2RankedReason,
) -> tuple[object, ...]:
    return (
        -row.reason_score_bps,
        _reason_code_rank(row.reason_code),
        row.recommendation_id,
        row.market_slug,
        row.selected_side,
        row.decision_status,
    )


def _reason_code_rank(reason_code: str) -> int:
    return ROW_REASON_CODES.index(reason_code)


def _normalize_inputs(
    decisions: Iterable[StrategyRecommendationAbstainReasonRankerV2Input],
) -> tuple[StrategyRecommendationAbstainReasonRankerV2Input, ...]:
    if isinstance(decisions, (str, bytes)):
        raise ValueError("decisions must be an iterable")
    try:
        normalized = tuple(decisions)
    except TypeError as exc:
        raise ValueError("decisions must be an iterable") from exc
    for decision in normalized:
        if type(decision) is not StrategyRecommendationAbstainReasonRankerV2Input:
            raise ValueError(
                "decisions must contain StrategyRecommendationAbstainReasonRankerV2Input",
            )
        require_paper_only_flags("decision", decision)
    return normalized


def _normalize_ranked_reasons(
    rows: Iterable[StrategyRecommendationAbstainReasonRankerV2RankedReason],
) -> tuple[StrategyRecommendationAbstainReasonRankerV2RankedReason, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("ranked_reasons must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("ranked_reasons must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyRecommendationAbstainReasonRankerV2RankedReason:
            raise ValueError(
                "ranked_reasons must contain StrategyRecommendationAbstainReasonRankerV2RankedReason",
            )
        require_paper_only_flags("ranked reason", row)
    return normalized


def _validate_unique_decisions(
    decisions: tuple[StrategyRecommendationAbstainReasonRankerV2Input, ...],
) -> None:
    recommendation_ids = tuple(decision.recommendation_id for decision in decisions)
    if len(recommendation_ids) != len(set(recommendation_ids)):
        raise ValueError("decisions must not contain duplicate recommendation_id values")


def _validate_ranked_reason(
    row: StrategyRecommendationAbstainReasonRankerV2RankedReason,
) -> None:
    if row.reason_code == "no_rankable_abstain_reason":
        if (
            row.reason_score_bps != ZERO_BPS
            or row.factor_value != ZERO_RATIO
            or row.threshold_value != ZERO_RATIO
        ):
            raise ValueError("no_rankable_abstain_reason rows must be zero scored")
    elif row.reason_score_bps <= ZERO_BPS:
        raise ValueError("ranked reason rows must have positive reason_score_bps")


def _validate_report(report: StrategyRecommendationAbstainReasonRankerV2Report) -> None:
    if report.ranked_reason_count != Decimal(len(report.ranked_reasons)):
        raise ValueError("ranked_reason_count must match ranked_reasons")
    if report.ranked_reasons:
        decision_count = Decimal(
            len({row.recommendation_id for row in report.ranked_reasons}),
        )
    else:
        decision_count = ZERO_COUNT
    if report.decision_count != decision_count:
        raise ValueError("decision_count must match ranked_reasons")
    expected_top_reason_code = (
        None if not report.ranked_reasons else report.ranked_reasons[0].reason_code
    )
    if report.top_reason_code != expected_top_reason_code:
        raise ValueError("top_reason_code must match ranked_reasons")
    expected_ranks = tuple(
        Decimal(index) for index in range(1, len(report.ranked_reasons) + 1)
    )
    if tuple(row.reason_rank for row in report.ranked_reasons) != expected_ranks:
        raise ValueError("ranked_reasons must use contiguous Decimal ranks")
    if report.ranked_reasons != _expected_reason_order(report.ranked_reasons):
        raise ValueError("ranked_reasons must use deterministic ranking")
    if report.reason_codes != _report_reason_codes(report.ranked_reasons):
        raise ValueError("reason_codes must match ranked_reasons")


def _expected_reason_order(
    rows: tuple[StrategyRecommendationAbstainReasonRankerV2RankedReason, ...],
) -> tuple[StrategyRecommendationAbstainReasonRankerV2RankedReason, ...]:
    return tuple(
        _replace_reason_rank(row, Decimal(index))
        for index, row in enumerate(sorted(rows, key=_rank_sort_key), start=1)
    )


def _report_reason_codes(
    rows: tuple[StrategyRecommendationAbstainReasonRankerV2RankedReason, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_abstain_decisions",)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(row.reason_code for row in rows),
        REPORT_REASON_CODES,
    )


def _ranked_reason_payload(
    row: StrategyRecommendationAbstainReasonRankerV2RankedReason,
) -> dict[str, Any]:
    return {
        "reason_rank": row.reason_rank,
        "recommendation_id": row.recommendation_id,
        "market_slug": row.market_slug,
        "selected_side": row.selected_side,
        "decision_status": row.decision_status,
        "reason_code": row.reason_code,
        "reason_score_bps": row.reason_score_bps,
        "factor_value": row.factor_value,
        "threshold_value": row.threshold_value,
        "edge_after_cost_bps": row.edge_after_cost_bps,
        "source_staleness_score": row.source_staleness_score,
        "evidence_quorum_score": row.evidence_quorum_score,
        "contradiction_severity_score": row.contradiction_severity_score,
        "resolution_ambiguity_score": row.resolution_ambiguity_score,
        "liquidity_risk_score": row.liquidity_risk_score,
        "category_budget_pressure_score": row.category_budget_pressure_score,
        "reason_digest": row.reason_digest,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _ranked_reason_digest_payload(
    row: StrategyRecommendationAbstainReasonRankerV2RankedReason,
) -> dict[str, Any]:
    return {
        "recommendation_id": row.recommendation_id,
        "market_slug": row.market_slug,
        "selected_side": row.selected_side,
        "decision_status": row.decision_status,
        "reason_code": row.reason_code,
        "reason_score_bps": row.reason_score_bps,
        "factor_value": row.factor_value,
        "threshold_value": row.threshold_value,
        "edge_after_cost_bps": row.edge_after_cost_bps,
        "source_staleness_score": row.source_staleness_score,
        "evidence_quorum_score": row.evidence_quorum_score,
        "contradiction_severity_score": row.contradiction_severity_score,
        "resolution_ambiguity_score": row.resolution_ambiguity_score,
        "liquidity_risk_score": row.liquidity_risk_score,
        "category_budget_pressure_score": row.category_budget_pressure_score,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_payload(
    report: StrategyRecommendationAbstainReasonRankerV2Report,
) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "decision_count": report.decision_count,
        "ranked_reason_count": report.ranked_reason_count,
        "top_reason_code": report.top_reason_code,
        "reason_codes": report.reason_codes,
        "ranked_reasons": tuple(_ranked_reason_payload(row) for row in report.ranked_reasons),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _ranked_reason_digest(
    row: StrategyRecommendationAbstainReasonRankerV2RankedReason,
) -> str:
    return _digest(_ranked_reason_digest_payload(row))


def _report_digest(report: StrategyRecommendationAbstainReasonRankerV2Report) -> str:
    return _digest(_report_digest_payload(report))


def _digest(payload: dict[str, Any]) -> str:
    ready = json_ready_no_floats(payload)
    text = json.dumps(ready, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return f"sha256:{sha256(text.encode('utf-8')).hexdigest()}"


def _score_bps(value: Decimal, weight_bps: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = value * weight_bps
    return _normalize_nonnegative_bps("reason_score_bps", score)


def _nonnegative_bps_delta(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        delta = left - right
    if delta <= ZERO_BPS:
        return ZERO_BPS
    return _normalize_nonnegative_bps("bps_delta", delta)


def _nonnegative_ratio_delta(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        delta = left - right
    if delta <= ZERO_RATIO:
        return ZERO_RATIO
    return _normalize_ratio("ratio_delta", delta)


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_choice(field_name, value, allowed)
        seen.add(value)
    return tuple(value for value in allowed if value in seen)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_bps(field_name: str, value: object) -> Decimal:
    return _normalize_decimal(field_name, value, BPS_QUANTUM)


def _normalize_nonnegative_bps(field_name: str, value: object) -> Decimal:
    normalized = _normalize_bps(field_name, value)
    if normalized < ZERO_BPS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, BPS_QUANTUM)
    if normalized < ZERO_BPS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(quantum)
    if quantized != value:
        raise ValueError(f"{field_name} must use the configured decimal scale")
    return quantized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a digest string")
    prefix = "sha256:"
    hexdigest = value.removeprefix(prefix)
    if (
        not value.startswith(prefix)
        or len(hexdigest) != 64
        or any(character not in "0123456789abcdef" for character in hexdigest)
    ):
        raise ValueError(f"{field_name} must be a sha256 digest")
