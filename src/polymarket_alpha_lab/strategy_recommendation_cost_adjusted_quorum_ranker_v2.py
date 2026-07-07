"""Pure Phase 1 cost-adjusted quorum recommendation ranker v2."""

from __future__ import annotations

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


DEFAULT_STRATEGY_RECOMMENDATION_COST_ADJUSTED_QUORUM_RANKER_V2_CONFIG_VERSION = (
    "strategy-recommendation-cost-adjusted-quorum-ranker-v2"
)

BPS_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
USD_QUANTUM = Decimal("0.000001")
ZERO_BPS = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ZERO_USD = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SIDES = ("yes", "no")
RECOMMENDATION_STATUSES = ("recommend", "review", "watch", "blocked", "empty")
REASON_CODES = (
    "positive_cost_adjusted_ev",
    "nonpositive_cost_adjusted_ev",
    "edge_margin_met",
    "edge_margin_short",
    "specialist_quorum_met",
    "specialist_quorum_short",
    "source_family_quorum_met",
    "source_family_quorum_short",
    "official_source_present",
    "official_source_missing",
    "liquidity_depth_met",
    "liquidity_depth_short",
    "costs_applied",
    "status_recommend",
    "status_review",
    "status_watch",
    "status_blocked",
    "top_candidate_recommended",
    "top_candidate_review",
    "top_candidate_watch",
    "top_candidate_blocked",
    "candidates_ranked",
    "no_candidates",
)


@dataclass(frozen=True)
class StrategyRecommendationCostAdjustedQuorumRankerV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_COST_ADJUSTED_QUORUM_RANKER_V2_CONFIG_VERSION
    )
    minimum_specialist_agreement_count: Decimal = Decimal("2")
    minimum_source_family_count: Decimal = Decimal("2")
    minimum_liquidity_depth_usd: Decimal = Decimal("1000.000000")
    minimum_cost_adjusted_ev_bps: Decimal = Decimal("25.000000")
    minimum_recommendation_score_bps: Decimal = Decimal("100.000000")
    specialist_quorum_weight_bps: Decimal = Decimal("20.000000")
    source_family_weight_bps: Decimal = Decimal("20.000000")
    official_source_weight_bps: Decimal = Decimal("10.000000")
    liquidity_depth_weight_bps: Decimal = Decimal("15.000000")
    require_official_source: bool = True
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_specialist_agreement_count",
            "minimum_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_liquidity_depth_usd",
            _normalize_positive_usd(
                "minimum_liquidity_depth_usd",
                self.minimum_liquidity_depth_usd,
            ),
        )
        for field_name in (
            "minimum_cost_adjusted_ev_bps",
            "minimum_recommendation_score_bps",
            "specialist_quorum_weight_bps",
            "source_family_weight_bps",
            "official_source_weight_bps",
            "liquidity_depth_weight_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        _require_bool("require_official_source", self.require_official_source)
        require_paper_only_flags(
            "StrategyRecommendationCostAdjustedQuorumRankerV2Config",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationCostAdjustedQuorumRankerV2Input:
    candidate_id: str
    market_slug: str
    side: str
    gross_edge_bps: Decimal
    taker_fee_bps: Decimal
    spread_cost_bps: Decimal
    slippage_cost_bps: Decimal
    liquidity_depth_usd: Decimal
    specialist_agreement_count: Decimal
    source_family_count: Decimal
    has_official_source: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("candidate_id", self.candidate_id)
        _require_identifier("market_slug", self.market_slug)
        _require_choice("side", self.side, SIDES)
        object.__setattr__(
            self,
            "gross_edge_bps",
            _normalize_bps("gross_edge_bps", self.gross_edge_bps),
        )
        for field_name in (
            "taker_fee_bps",
            "spread_cost_bps",
            "slippage_cost_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_depth_usd",
            _normalize_nonnegative_usd("liquidity_depth_usd", self.liquidity_depth_usd),
        )
        for field_name in (
            "specialist_agreement_count",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_bool("has_official_source", self.has_official_source)
        require_paper_only_flags(
            "StrategyRecommendationCostAdjustedQuorumRankerV2Input",
            self,
        )


@dataclass(frozen=True)
class StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow:
    rank: Decimal
    candidate_id: str
    market_slug: str
    side: str
    gross_edge_bps: Decimal
    taker_fee_bps: Decimal
    spread_cost_bps: Decimal
    slippage_cost_bps: Decimal
    total_cost_bps: Decimal
    cost_adjusted_ev_bps: Decimal
    edge_margin_bps: Decimal
    liquidity_depth_usd: Decimal
    specialist_agreement_count: Decimal
    source_family_count: Decimal
    has_official_source: bool
    quorum_score_bps: Decimal
    liquidity_depth_score_bps: Decimal
    recommendation_score_bps: Decimal
    recommendation_status: str
    reason_codes: tuple[str, ...]
    decision_digest: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_identifier("candidate_id", self.candidate_id)
        _require_identifier("market_slug", self.market_slug)
        _require_choice("side", self.side, SIDES)
        object.__setattr__(
            self,
            "gross_edge_bps",
            _normalize_bps("gross_edge_bps", self.gross_edge_bps),
        )
        for field_name in (
            "taker_fee_bps",
            "spread_cost_bps",
            "slippage_cost_bps",
            "total_cost_bps",
            "quorum_score_bps",
            "liquidity_depth_score_bps",
            "recommendation_score_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cost_adjusted_ev_bps",
            "edge_margin_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_bps(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_depth_usd",
            _normalize_nonnegative_usd("liquidity_depth_usd", self.liquidity_depth_usd),
        )
        for field_name in (
            "specialist_agreement_count",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_bool("has_official_source", self.has_official_source)
        _require_choice(
            "recommendation_status",
            self.recommendation_status,
            RECOMMENDATION_STATUSES[:-1],
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_ranked_row(self)
        require_paper_only_flags(
            "StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow",
            self,
        )
        expected_digest = _ranked_row_digest(self)
        if self.decision_digest is None:
            object.__setattr__(self, "decision_digest", expected_digest)
        else:
            _require_digest("decision_digest", self.decision_digest)
            if self.decision_digest != expected_digest:
                raise ValueError("decision_digest must match ranked row")


@dataclass(frozen=True)
class StrategyRecommendationCostAdjustedQuorumRankerV2Report:
    config_version: str
    candidate_count: Decimal
    ranked_rows: tuple[StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow, ...]
    top_candidate_id: str | None
    recommendation_status: str
    reason_codes: tuple[str, ...]
    report_digest: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "candidate_count",
            _normalize_nonnegative_count("candidate_count", self.candidate_count),
        )
        object.__setattr__(self, "ranked_rows", _normalize_ranked_rows(self.ranked_rows))
        if self.top_candidate_id is not None:
            _require_identifier("top_candidate_id", self.top_candidate_id)
        _require_choice(
            "recommendation_status",
            self.recommendation_status,
            RECOMMENDATION_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        require_paper_only_flags(
            "StrategyRecommendationCostAdjustedQuorumRankerV2Report",
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
        return strategy_recommendation_cost_adjusted_quorum_ranker_v2_payload(self)


def rank_strategy_recommendation_cost_adjusted_quorum_v2(
    candidates: tuple[StrategyRecommendationCostAdjustedQuorumRankerV2Input, ...],
    *,
    config: StrategyRecommendationCostAdjustedQuorumRankerV2Config | None = None,
) -> StrategyRecommendationCostAdjustedQuorumRankerV2Report:
    active_config = config or StrategyRecommendationCostAdjustedQuorumRankerV2Config()
    if type(active_config) is not StrategyRecommendationCostAdjustedQuorumRankerV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationCostAdjustedQuorumRankerV2Config",
        )
    require_paper_only_flags("config", active_config)
    normalized_candidates = _normalize_inputs(candidates)
    _validate_unique_candidates(normalized_candidates)

    unranked_rows = tuple(
        _ranked_row(candidate, rank=Decimal("1"), config=active_config)
        for candidate in normalized_candidates
    )
    sorted_rows = tuple(sorted(unranked_rows, key=_rank_sort_key))
    ranked_rows = tuple(
        _replace_rank(row, Decimal(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    top_row = ranked_rows[0] if ranked_rows else None

    return StrategyRecommendationCostAdjustedQuorumRankerV2Report(
        config_version=active_config.config_version,
        candidate_count=Decimal(len(ranked_rows)),
        ranked_rows=ranked_rows,
        top_candidate_id=None if top_row is None else top_row.candidate_id,
        recommendation_status="empty" if top_row is None else top_row.recommendation_status,
        reason_codes=_report_reason_codes(top_row),
    )


def strategy_recommendation_cost_adjusted_quorum_ranker_v2_payload(
    report: StrategyRecommendationCostAdjustedQuorumRankerV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationCostAdjustedQuorumRankerV2Report:
        raise ValueError(
            "report must be a StrategyRecommendationCostAdjustedQuorumRankerV2Report",
        )
    require_paper_only_flags("report", report)
    payload = {
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "ranked_rows": tuple(_row_payload(row) for row in report.ranked_rows),
        "top_candidate_id": report.top_candidate_id,
        "recommendation_status": report.recommendation_status,
        "reason_codes": report.reason_codes,
        "report_digest": report.report_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    reject_unsafe_surface_fields(
        "strategy recommendation cost adjusted quorum ranker v2",
        payload,
    )
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _ranked_row(
    candidate: StrategyRecommendationCostAdjustedQuorumRankerV2Input,
    *,
    rank: Decimal,
    config: StrategyRecommendationCostAdjustedQuorumRankerV2Config,
) -> StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow:
    total_cost_bps = _sum_bps(
        candidate.taker_fee_bps,
        candidate.spread_cost_bps,
        candidate.slippage_cost_bps,
    )
    cost_adjusted_ev_bps = _subtract_bps(candidate.gross_edge_bps, total_cost_bps)
    edge_margin_bps = _subtract_bps(
        cost_adjusted_ev_bps,
        config.minimum_cost_adjusted_ev_bps,
    )
    quorum_score_bps = _quorum_score_bps(candidate, config)
    liquidity_depth_score_bps = _liquidity_depth_score_bps(candidate, config)
    status = _recommendation_status(
        candidate,
        cost_adjusted_ev_bps=cost_adjusted_ev_bps,
        edge_margin_bps=edge_margin_bps,
        liquidity_depth_usd=candidate.liquidity_depth_usd,
        config=config,
    )
    recommendation_score_bps = (
        ZERO_BPS
        if status == "blocked"
        else _recommendation_score_bps(
            cost_adjusted_ev_bps=cost_adjusted_ev_bps,
            edge_margin_bps=edge_margin_bps,
            quorum_score_bps=quorum_score_bps,
            liquidity_depth_score_bps=liquidity_depth_score_bps,
        )
    )

    return StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow(
        rank=rank,
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        side=candidate.side,
        gross_edge_bps=candidate.gross_edge_bps,
        taker_fee_bps=candidate.taker_fee_bps,
        spread_cost_bps=candidate.spread_cost_bps,
        slippage_cost_bps=candidate.slippage_cost_bps,
        total_cost_bps=total_cost_bps,
        cost_adjusted_ev_bps=cost_adjusted_ev_bps,
        edge_margin_bps=edge_margin_bps,
        liquidity_depth_usd=candidate.liquidity_depth_usd,
        specialist_agreement_count=candidate.specialist_agreement_count,
        source_family_count=candidate.source_family_count,
        has_official_source=candidate.has_official_source,
        quorum_score_bps=quorum_score_bps,
        liquidity_depth_score_bps=liquidity_depth_score_bps,
        recommendation_score_bps=recommendation_score_bps,
        recommendation_status=status,
        reason_codes=_row_reason_codes(
            candidate,
            total_cost_bps=total_cost_bps,
            cost_adjusted_ev_bps=cost_adjusted_ev_bps,
            edge_margin_bps=edge_margin_bps,
            liquidity_depth_usd=candidate.liquidity_depth_usd,
            status=status,
            config=config,
        ),
    )


def _replace_rank(
    row: StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow,
    rank: Decimal,
) -> StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow:
    return StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow(
        rank=rank,
        candidate_id=row.candidate_id,
        market_slug=row.market_slug,
        side=row.side,
        gross_edge_bps=row.gross_edge_bps,
        taker_fee_bps=row.taker_fee_bps,
        spread_cost_bps=row.spread_cost_bps,
        slippage_cost_bps=row.slippage_cost_bps,
        total_cost_bps=row.total_cost_bps,
        cost_adjusted_ev_bps=row.cost_adjusted_ev_bps,
        edge_margin_bps=row.edge_margin_bps,
        liquidity_depth_usd=row.liquidity_depth_usd,
        specialist_agreement_count=row.specialist_agreement_count,
        source_family_count=row.source_family_count,
        has_official_source=row.has_official_source,
        quorum_score_bps=row.quorum_score_bps,
        liquidity_depth_score_bps=row.liquidity_depth_score_bps,
        recommendation_score_bps=row.recommendation_score_bps,
        recommendation_status=row.recommendation_status,
        reason_codes=row.reason_codes,
        decision_digest=row.decision_digest,
    )


def _recommendation_status(
    candidate: StrategyRecommendationCostAdjustedQuorumRankerV2Input,
    *,
    cost_adjusted_ev_bps: Decimal,
    edge_margin_bps: Decimal,
    liquidity_depth_usd: Decimal,
    config: StrategyRecommendationCostAdjustedQuorumRankerV2Config,
) -> str:
    if _is_blocked_by_quorum(candidate, config):
        return "blocked"
    if cost_adjusted_ev_bps <= ZERO_BPS:
        return "watch"
    recommendation_score_bps = _recommendation_score_bps(
        cost_adjusted_ev_bps=cost_adjusted_ev_bps,
        edge_margin_bps=edge_margin_bps,
        quorum_score_bps=_quorum_score_bps(candidate, config),
        liquidity_depth_score_bps=_liquidity_depth_score_bps(candidate, config),
    )
    if (
        edge_margin_bps >= config.minimum_cost_adjusted_ev_bps
        and liquidity_depth_usd >= config.minimum_liquidity_depth_usd
        and recommendation_score_bps >= config.minimum_recommendation_score_bps
    ):
        return "recommend"
    if recommendation_score_bps > ZERO_BPS:
        return "review"
    return "watch"


def _recommendation_score_bps(
    *,
    cost_adjusted_ev_bps: Decimal,
    edge_margin_bps: Decimal,
    quorum_score_bps: Decimal,
    liquidity_depth_score_bps: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            cost_adjusted_ev_bps
            + edge_margin_bps
            + quorum_score_bps
            + liquidity_depth_score_bps
        )
    if raw_score <= ZERO_BPS:
        return ZERO_BPS
    return _normalize_nonnegative_bps("recommendation_score_bps", raw_score)


def _quorum_score_bps(
    candidate: StrategyRecommendationCostAdjustedQuorumRankerV2Input,
    config: StrategyRecommendationCostAdjustedQuorumRankerV2Config,
) -> Decimal:
    specialist_ratio = _bounded_ratio(
        candidate.specialist_agreement_count,
        config.minimum_specialist_agreement_count,
    )
    source_family_ratio = _bounded_ratio(
        candidate.source_family_count,
        config.minimum_source_family_count,
    )
    official_source_score = (
        config.official_source_weight_bps
        if candidate.has_official_source
        else ZERO_BPS
    )
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            specialist_ratio * config.specialist_quorum_weight_bps
            + source_family_ratio * config.source_family_weight_bps
            + official_source_score
        )
    return _normalize_nonnegative_bps("quorum_score_bps", raw_score)


def _liquidity_depth_score_bps(
    candidate: StrategyRecommendationCostAdjustedQuorumRankerV2Input,
    config: StrategyRecommendationCostAdjustedQuorumRankerV2Config,
) -> Decimal:
    depth_ratio = _bounded_ratio(
        candidate.liquidity_depth_usd,
        config.minimum_liquidity_depth_usd,
    )
    with localcontext(DECIMAL_CONTEXT):
        raw_score = depth_ratio * config.liquidity_depth_weight_bps
    return _normalize_nonnegative_bps("liquidity_depth_score_bps", raw_score)


def _row_reason_codes(
    candidate: StrategyRecommendationCostAdjustedQuorumRankerV2Input,
    *,
    total_cost_bps: Decimal,
    cost_adjusted_ev_bps: Decimal,
    edge_margin_bps: Decimal,
    liquidity_depth_usd: Decimal,
    status: str,
    config: StrategyRecommendationCostAdjustedQuorumRankerV2Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    codes.append(
        "positive_cost_adjusted_ev"
        if cost_adjusted_ev_bps > ZERO_BPS
        else "nonpositive_cost_adjusted_ev",
    )
    codes.append(
        "edge_margin_met"
        if edge_margin_bps >= config.minimum_cost_adjusted_ev_bps
        else "edge_margin_short",
    )
    codes.append(
        "specialist_quorum_met"
        if candidate.specialist_agreement_count >= config.minimum_specialist_agreement_count
        else "specialist_quorum_short",
    )
    codes.append(
        "source_family_quorum_met"
        if candidate.source_family_count >= config.minimum_source_family_count
        else "source_family_quorum_short",
    )
    codes.append(
        "official_source_present"
        if candidate.has_official_source
        else "official_source_missing",
    )
    codes.append(
        "liquidity_depth_met"
        if liquidity_depth_usd >= config.minimum_liquidity_depth_usd
        else "liquidity_depth_short",
    )
    if total_cost_bps > ZERO_BPS:
        codes.append("costs_applied")
    codes.append(f"status_{status}")
    return _normalize_reason_codes(tuple(codes))


def _report_reason_codes(
    top_row: StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow | None,
) -> tuple[str, ...]:
    if top_row is None:
        return ("no_candidates",)
    if top_row.recommendation_status == "recommend":
        return ("top_candidate_recommended", "candidates_ranked")
    if top_row.recommendation_status == "review":
        return ("top_candidate_review", "candidates_ranked")
    if top_row.recommendation_status == "watch":
        return ("top_candidate_watch", "candidates_ranked")
    return ("top_candidate_blocked", "candidates_ranked")


def _row_payload(row: StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow) -> dict[str, Any]:
    return {
        "rank": row.rank,
        "candidate_id": row.candidate_id,
        "market_slug": row.market_slug,
        "side": row.side,
        "gross_edge_bps": row.gross_edge_bps,
        "taker_fee_bps": row.taker_fee_bps,
        "spread_cost_bps": row.spread_cost_bps,
        "slippage_cost_bps": row.slippage_cost_bps,
        "total_cost_bps": row.total_cost_bps,
        "cost_adjusted_ev_bps": row.cost_adjusted_ev_bps,
        "edge_margin_bps": row.edge_margin_bps,
        "liquidity_depth_usd": row.liquidity_depth_usd,
        "specialist_agreement_count": row.specialist_agreement_count,
        "source_family_count": row.source_family_count,
        "has_official_source": row.has_official_source,
        "quorum_score_bps": row.quorum_score_bps,
        "liquidity_depth_score_bps": row.liquidity_depth_score_bps,
        "recommendation_score_bps": row.recommendation_score_bps,
        "recommendation_status": row.recommendation_status,
        "reason_codes": row.reason_codes,
        "decision_digest": row.decision_digest,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_digest_payload(
    row: StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow,
) -> dict[str, Any]:
    return {
        "candidate_id": row.candidate_id,
        "market_slug": row.market_slug,
        "side": row.side,
        "gross_edge_bps": row.gross_edge_bps,
        "taker_fee_bps": row.taker_fee_bps,
        "spread_cost_bps": row.spread_cost_bps,
        "slippage_cost_bps": row.slippage_cost_bps,
        "total_cost_bps": row.total_cost_bps,
        "cost_adjusted_ev_bps": row.cost_adjusted_ev_bps,
        "edge_margin_bps": row.edge_margin_bps,
        "liquidity_depth_usd": row.liquidity_depth_usd,
        "specialist_agreement_count": row.specialist_agreement_count,
        "source_family_count": row.source_family_count,
        "has_official_source": row.has_official_source,
        "quorum_score_bps": row.quorum_score_bps,
        "liquidity_depth_score_bps": row.liquidity_depth_score_bps,
        "recommendation_score_bps": row.recommendation_score_bps,
        "recommendation_status": row.recommendation_status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_payload(
    report: StrategyRecommendationCostAdjustedQuorumRankerV2Report,
) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "ranked_rows": tuple(_row_payload(row) for row in report.ranked_rows),
        "top_candidate_id": report.top_candidate_id,
        "recommendation_status": report.recommendation_status,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _ranked_row_digest(row: StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow) -> str:
    return _digest(_row_digest_payload(row))


def _report_digest(report: StrategyRecommendationCostAdjustedQuorumRankerV2Report) -> str:
    return _digest(_report_digest_payload(report))


def _digest(payload: dict[str, Any]) -> str:
    ready = json_ready_no_floats(payload)
    text = json.dumps(ready, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return f"sha256:{sha256(text.encode('utf-8')).hexdigest()}"


def _validate_ranked_row(
    row: StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow,
) -> None:
    expected_total_cost_bps = _sum_bps(
        row.taker_fee_bps,
        row.spread_cost_bps,
        row.slippage_cost_bps,
    )
    if row.total_cost_bps != expected_total_cost_bps:
        raise ValueError("total_cost_bps must match explicit costs")
    if row.cost_adjusted_ev_bps != _subtract_bps(row.gross_edge_bps, row.total_cost_bps):
        raise ValueError("cost_adjusted_ev_bps must match gross edge less costs")
    if row.recommendation_status == "blocked" and row.recommendation_score_bps != ZERO_BPS:
        raise ValueError("blocked rows must have zero recommendation_score_bps")
    if row.recommendation_status == "recommend":
        if row.cost_adjusted_ev_bps <= ZERO_BPS:
            raise ValueError("recommended rows must have positive cost_adjusted_ev_bps")
        if row.edge_margin_bps < ZERO_BPS:
            raise ValueError("recommended rows must have nonnegative edge_margin_bps")
    if (
        row.total_cost_bps > ZERO_BPS
        and "costs_applied" not in row.reason_codes
    ):
        raise ValueError("costed rows must include costs_applied")
    if (
        row.total_cost_bps == ZERO_BPS
        and "costs_applied" in row.reason_codes
    ):
        raise ValueError("uncosted rows must not include costs_applied")
    expected_status_reason = f"status_{row.recommendation_status}"
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include recommendation status")


def _validate_report(report: StrategyRecommendationCostAdjustedQuorumRankerV2Report) -> None:
    if report.candidate_count != Decimal(len(report.ranked_rows)):
        raise ValueError("candidate_count must match ranked_rows")
    candidate_ids = tuple(row.candidate_id for row in report.ranked_rows)
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("ranked_rows must contain unique candidate_id values")
    expected_ranks = tuple(Decimal(index) for index in range(1, len(report.ranked_rows) + 1))
    if tuple(row.rank for row in report.ranked_rows) != expected_ranks:
        raise ValueError("ranked_rows must use contiguous Decimal ranks")
    if report.ranked_rows != _expected_row_order(report.ranked_rows):
        raise ValueError("ranked_rows must use deterministic ranking")
    top_row = report.ranked_rows[0] if report.ranked_rows else None
    if (None if top_row is None else top_row.candidate_id) != report.top_candidate_id:
        raise ValueError("top_candidate_id must match ranked_rows")
    if ("empty" if top_row is None else top_row.recommendation_status) != (
        report.recommendation_status
    ):
        raise ValueError("recommendation_status must match ranked_rows")
    if report.reason_codes != _report_reason_codes(top_row):
        raise ValueError("reason_codes must match ranked_rows")


def _expected_row_order(
    rows: tuple[StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow, ...],
) -> tuple[StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow, ...]:
    return tuple(
        _replace_rank(row, Decimal(index))
        for index, row in enumerate(sorted(rows, key=_rank_sort_key), start=1)
    )


def _rank_sort_key(
    row: StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.recommendation_status),
        -row.recommendation_score_bps,
        -row.cost_adjusted_ev_bps,
        -row.edge_margin_bps,
        -row.quorum_score_bps,
        -row.liquidity_depth_score_bps,
        row.candidate_id,
        row.market_slug,
        row.side,
    )


def _status_rank(status: str) -> int:
    if status == "recommend":
        return 0
    if status == "review":
        return 1
    if status == "watch":
        return 2
    if status == "blocked":
        return 3
    raise ValueError("recommendation_status must be supported")


def _normalize_inputs(
    candidates: tuple[StrategyRecommendationCostAdjustedQuorumRankerV2Input, ...],
) -> tuple[StrategyRecommendationCostAdjustedQuorumRankerV2Input, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    for candidate in normalized:
        if type(candidate) is not StrategyRecommendationCostAdjustedQuorumRankerV2Input:
            raise ValueError(
                "candidates must contain "
                "StrategyRecommendationCostAdjustedQuorumRankerV2Input",
            )
        require_paper_only_flags("candidate", candidate)
    return normalized


def _normalize_ranked_rows(
    rows: tuple[StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow, ...],
) -> tuple[StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("ranked_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("ranked_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow:
            raise ValueError(
                "ranked_rows must contain "
                "StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow",
            )
        require_paper_only_flags("ranked row", row)
    return normalized


def _validate_unique_candidates(
    candidates: tuple[StrategyRecommendationCostAdjustedQuorumRankerV2Input, ...],
) -> None:
    candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidates must not contain duplicate candidate_id values")


def _is_blocked_by_quorum(
    candidate: StrategyRecommendationCostAdjustedQuorumRankerV2Input,
    config: StrategyRecommendationCostAdjustedQuorumRankerV2Config,
) -> bool:
    if candidate.specialist_agreement_count < config.minimum_specialist_agreement_count:
        return True
    if candidate.source_family_count < config.minimum_source_family_count:
        return True
    if config.require_official_source and not candidate.has_official_source:
        return True
    return False


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_identifier("reason_codes", value)
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes must not contain duplicate values")
        seen.add(value)
    return tuple(value for value in REASON_CODES if value in seen)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    if ratio >= ONE_RATIO:
        return ONE_RATIO
    if ratio <= ZERO_BPS:
        return ZERO_BPS
    return _normalize_nonnegative_bps("bounded_ratio", ratio)


def _sum_bps(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO_BPS)
    return _normalize_nonnegative_bps("total_cost_bps", total)


def _subtract_bps(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = left - right
    return _normalize_bps("bps_delta", value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        normalized = decimal_value.quantize(COUNT_QUANTUM)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_usd(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_usd(field_name, value)
    if normalized <= ZERO_USD:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_usd(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        normalized = decimal_value.quantize(USD_QUANTUM)
    if normalized < ZERO_USD:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_bps(field_name: str, value: object) -> Decimal:
    normalized = _normalize_bps(field_name, value)
    if normalized < ZERO_BPS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_bps(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(BPS_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_digest(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    prefix = "sha256:"
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be a sha256 digest")
    digest = value[len(prefix) :]
    if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_COST_ADJUSTED_QUORUM_RANKER_V2_CONFIG_VERSION",
    "SIDES",
    "RECOMMENDATION_STATUSES",
    "REASON_CODES",
    "StrategyRecommendationCostAdjustedQuorumRankerV2Config",
    "StrategyRecommendationCostAdjustedQuorumRankerV2Input",
    "StrategyRecommendationCostAdjustedQuorumRankerV2RankedRow",
    "StrategyRecommendationCostAdjustedQuorumRankerV2Report",
    "rank_strategy_recommendation_cost_adjusted_quorum_v2",
    "strategy_recommendation_cost_adjusted_quorum_ranker_v2_payload",
)
