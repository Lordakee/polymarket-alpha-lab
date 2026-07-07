"""Pure Phase 1 final decision matrix for strategy recommendations."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RECOMMENDATION_FINAL_DECISION_MATRIX_V2_CONFIG_VERSION = (
    "strategy-recommendation-final-decision-matrix-v2"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

SIDES = ("yes", "no")
FINAL_DECISIONS = ("pass", "manual-review", "watch", "abstain")
KNOWN_REASON_CODE_SEQUENCE = (
    "final_decision_pass",
    "final_decision_manual_review",
    "final_decision_watch",
    "final_decision_abstain",
    "cost_adjusted_edge_pass",
    "cost_adjusted_edge_watch",
    "cost_adjusted_edge_abstain",
    "evidence_quorum_pass",
    "evidence_quorum_review",
    "evidence_quorum_abstain",
    "source_confidence_pass",
    "source_confidence_review",
    "source_confidence_abstain",
    "resolution_risk_pass",
    "resolution_risk_review",
    "resolution_risk_abstain",
    "liquidity_capacity_pass",
    "liquidity_capacity_watch",
    "liquidity_capacity_abstain",
    "category_budget_pass",
    "category_budget_watch",
    "category_budget_abstain",
    "team_consensus_pass",
    "team_consensus_review",
    "team_consensus_abstain",
    "candidates_ranked",
    "no_candidates",
)
REASON_CODE_RANK = {
    reason_code: Decimal(index)
    for index, reason_code in enumerate(KNOWN_REASON_CODE_SEQUENCE)
}
ALLOWED_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


EXTRA_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("li", "ve"),
        _surface_term("net", "work"),
        _surface_term("data", "base"),
        _surface_term("d", "b"),
        _surface_term("per", "sist"),
        _surface_term("sig", "ning"),
        _surface_term("muta", "tion"),
        _surface_term("tra", "de"),
        _surface_term("b", "uy"),
        _surface_term("se", "ll"),
        _surface_term("sec", "ret"),
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = UNSAFE_SURFACE_FIELD_FRAGMENTS | EXTRA_UNSAFE_PUBLIC_FRAGMENTS


@dataclass(frozen=True)
class StrategyRecommendationFinalDecisionMatrixV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_RECOMMENDATION_FINAL_DECISION_MATRIX_V2_CONFIG_VERSION
    )
    minimum_pass_cost_adjusted_edge_bps: Decimal = Decimal("50.000000")
    minimum_watch_cost_adjusted_edge_bps: Decimal = Decimal("0.000000")
    minimum_pass_evidence_quorum_score: Decimal = Decimal("0.800000")
    minimum_watch_evidence_quorum_score: Decimal = Decimal("0.500000")
    minimum_pass_source_confidence_score: Decimal = Decimal("0.750000")
    minimum_watch_source_confidence_score: Decimal = Decimal("0.500000")
    maximum_pass_resolution_risk_score: Decimal = Decimal("0.250000")
    maximum_watch_resolution_risk_score: Decimal = Decimal("0.600000")
    minimum_pass_liquidity_capacity_ratio: Decimal = Decimal("1.500000")
    minimum_watch_liquidity_capacity_ratio: Decimal = Decimal("1.000000")
    minimum_pass_category_budget_remaining_ratio: Decimal = Decimal("0.200000")
    minimum_watch_category_budget_remaining_ratio: Decimal = Decimal("0.050000")
    minimum_pass_team_consensus_score: Decimal = Decimal("0.800000")
    minimum_watch_team_consensus_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "minimum_pass_cost_adjusted_edge_bps",
            "minimum_watch_cost_adjusted_edge_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_evidence_quorum_score",
            "minimum_watch_evidence_quorum_score",
            "minimum_pass_source_confidence_score",
            "minimum_watch_source_confidence_score",
            "maximum_pass_resolution_risk_score",
            "maximum_watch_resolution_risk_score",
            "minimum_pass_category_budget_remaining_ratio",
            "minimum_watch_category_budget_remaining_ratio",
            "minimum_pass_team_consensus_score",
            "minimum_watch_team_consensus_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_pass_liquidity_capacity_ratio",
            "minimum_watch_liquidity_capacity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_positive(
            "minimum_pass_cost_adjusted_edge_bps",
            self.minimum_pass_cost_adjusted_edge_bps,
        )
        _require_positive(
            "minimum_pass_liquidity_capacity_ratio",
            self.minimum_pass_liquidity_capacity_ratio,
        )
        _require_positive(
            "minimum_pass_category_budget_remaining_ratio",
            self.minimum_pass_category_budget_remaining_ratio,
        )
        _require_not_below(
            "minimum_pass_cost_adjusted_edge_bps",
            self.minimum_pass_cost_adjusted_edge_bps,
            "minimum_watch_cost_adjusted_edge_bps",
            self.minimum_watch_cost_adjusted_edge_bps,
        )
        _require_not_below(
            "minimum_pass_evidence_quorum_score",
            self.minimum_pass_evidence_quorum_score,
            "minimum_watch_evidence_quorum_score",
            self.minimum_watch_evidence_quorum_score,
        )
        _require_not_below(
            "minimum_pass_source_confidence_score",
            self.minimum_pass_source_confidence_score,
            "minimum_watch_source_confidence_score",
            self.minimum_watch_source_confidence_score,
        )
        _require_not_above(
            "maximum_pass_resolution_risk_score",
            self.maximum_pass_resolution_risk_score,
            "maximum_watch_resolution_risk_score",
            self.maximum_watch_resolution_risk_score,
        )
        _require_not_below(
            "minimum_pass_liquidity_capacity_ratio",
            self.minimum_pass_liquidity_capacity_ratio,
            "minimum_watch_liquidity_capacity_ratio",
            self.minimum_watch_liquidity_capacity_ratio,
        )
        _require_not_below(
            "minimum_pass_category_budget_remaining_ratio",
            self.minimum_pass_category_budget_remaining_ratio,
            "minimum_watch_category_budget_remaining_ratio",
            self.minimum_watch_category_budget_remaining_ratio,
        )
        _require_not_below(
            "minimum_pass_team_consensus_score",
            self.minimum_pass_team_consensus_score,
            "minimum_watch_team_consensus_score",
            self.minimum_watch_team_consensus_score,
        )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyRecommendationFinalDecisionMatrixV2Candidate:
    candidate_id: str
    market_slug: str
    side: str
    category: str
    gross_edge_bps: Decimal
    taker_fee_bps: Decimal
    spread_cost_bps: Decimal
    slippage_cost_bps: Decimal
    evidence_quorum_score: Decimal
    source_confidence_score: Decimal
    resolution_risk_score: Decimal
    liquidity_capacity_ratio: Decimal
    category_budget_remaining_ratio: Decimal
    team_consensus_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "category"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_choice("side", self.side, SIDES)
        object.__setattr__(
            self,
            "gross_edge_bps",
            _normalize_decimal("gross_edge_bps", self.gross_edge_bps),
        )
        for field_name in ("taker_fee_bps", "spread_cost_bps", "slippage_cost_bps"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_quorum_score",
            "source_confidence_score",
            "resolution_risk_score",
            "category_budget_remaining_ratio",
            "team_consensus_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_capacity_ratio",
            _normalize_nonnegative_decimal(
                "liquidity_capacity_ratio",
                self.liquidity_capacity_ratio,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        require_paper_only_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRecommendationFinalDecisionMatrixV2Row:
    rank: Decimal
    candidate_id: str
    market_slug: str
    side: str
    category: str
    gross_edge_bps: Decimal
    taker_fee_bps: Decimal
    spread_cost_bps: Decimal
    slippage_cost_bps: Decimal
    total_cost_bps: Decimal
    cost_adjusted_edge_bps: Decimal
    cost_adjusted_edge_score: Decimal
    evidence_quorum_score: Decimal
    source_confidence_score: Decimal
    resolution_risk_score: Decimal
    resolution_safety_score: Decimal
    liquidity_capacity_ratio: Decimal
    liquidity_capacity_score: Decimal
    category_budget_remaining_ratio: Decimal
    category_budget_score: Decimal
    team_consensus_score: Decimal
    decision_score: Decimal
    final_decision: str
    reason_codes: tuple[str, ...]
    decision_digest: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        for field_name in ("candidate_id", "market_slug", "category"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_choice("side", self.side, SIDES)
        object.__setattr__(
            self,
            "gross_edge_bps",
            _normalize_decimal("gross_edge_bps", self.gross_edge_bps),
        )
        for field_name in (
            "taker_fee_bps",
            "spread_cost_bps",
            "slippage_cost_bps",
            "total_cost_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_decimal("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        for field_name in (
            "cost_adjusted_edge_score",
            "evidence_quorum_score",
            "source_confidence_score",
            "resolution_risk_score",
            "resolution_safety_score",
            "liquidity_capacity_score",
            "category_budget_remaining_ratio",
            "category_budget_score",
            "team_consensus_score",
            "decision_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "liquidity_capacity_ratio",
            _normalize_nonnegative_decimal(
                "liquidity_capacity_ratio",
                self.liquidity_capacity_ratio,
            ),
        )
        _require_choice("final_decision", self.final_decision, FINAL_DECISIONS)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)
        expected_digest = _row_digest(self)
        if self.decision_digest is None:
            object.__setattr__(self, "decision_digest", expected_digest)
        else:
            _require_digest("decision_digest", self.decision_digest)
            if self.decision_digest != expected_digest:
                raise ValueError("decision_digest must match row")


@dataclass(frozen=True)
class StrategyRecommendationFinalDecisionMatrixV2Report:
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    abstain_count: Decimal
    manual_review_count: Decimal
    top_candidate_id: str | None
    final_decision: str
    average_decision_score: Decimal
    max_decision_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyRecommendationFinalDecisionMatrixV2Row, ...]
    report_digest: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "abstain_count",
            "manual_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.top_candidate_id is not None:
            _require_public_identifier("top_candidate_id", self.top_candidate_id)
        _require_choice("final_decision", self.final_decision, FINAL_DECISIONS)
        for field_name in ("average_decision_score", "max_decision_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        require_paper_only_flags("report", self)
        expected_digest = _report_digest(self)
        if self.report_digest is None:
            object.__setattr__(self, "report_digest", expected_digest)
        else:
            _require_digest("report_digest", self.report_digest)
            if self.report_digest != expected_digest:
                raise ValueError("report_digest must match report")

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_recommendation_final_decision_matrix_v2_payload(self)


def build_strategy_recommendation_final_decision_matrix_v2_report(
    candidates: Iterable[StrategyRecommendationFinalDecisionMatrixV2Candidate],
    *,
    config: StrategyRecommendationFinalDecisionMatrixV2Config | None = None,
) -> StrategyRecommendationFinalDecisionMatrixV2Report:
    active_config = config or StrategyRecommendationFinalDecisionMatrixV2Config()
    if type(active_config) is not StrategyRecommendationFinalDecisionMatrixV2Config:
        raise ValueError(
            "config must be a StrategyRecommendationFinalDecisionMatrixV2Config",
        )
    require_paper_only_flags("config", active_config)
    normalized_candidates = _normalize_candidates(candidates)
    rows = _rank_rows(
        tuple(
            _row_from_candidate(candidate, rank=Decimal("1"), config=active_config)
            for candidate in normalized_candidates
        ),
    )
    top_row = rows[0] if rows else None

    return StrategyRecommendationFinalDecisionMatrixV2Report(
        config_version=active_config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        abstain_count=_status_count(rows, "abstain"),
        manual_review_count=_status_count(rows, "manual-review"),
        top_candidate_id=None if top_row is None else top_row.candidate_id,
        final_decision="abstain" if top_row is None else top_row.final_decision,
        average_decision_score=_average_score(rows),
        max_decision_score=_max_score(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_recommendation_final_decision_matrix_v2_payload(
    report: StrategyRecommendationFinalDecisionMatrixV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyRecommendationFinalDecisionMatrixV2Report:
        raise ValueError(
            "report must be a StrategyRecommendationFinalDecisionMatrixV2Report",
        )
    require_paper_only_flags("report", report)
    _validate_report(report)
    for row in report.rows:
        _verify_row_digest(row)
    _verify_report_digest(report)
    payload = _report_payload(report)
    reject_unsafe_surface_fields(
        "strategy recommendation final decision matrix v2",
        payload,
    )
    ready = json_ready_no_floats(payload)
    _reject_unsafe_public_values(ready)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _row_from_candidate(
    candidate: StrategyRecommendationFinalDecisionMatrixV2Candidate,
    *,
    rank: Decimal,
    config: StrategyRecommendationFinalDecisionMatrixV2Config,
) -> StrategyRecommendationFinalDecisionMatrixV2Row:
    total_cost_bps = _sum_decimals(
        candidate.taker_fee_bps,
        candidate.spread_cost_bps,
        candidate.slippage_cost_bps,
    )
    cost_adjusted_edge_bps = _subtract_decimal(candidate.gross_edge_bps, total_cost_bps)
    cost_adjusted_edge_score = _bounded_ratio(
        max(cost_adjusted_edge_bps, ZERO),
        config.minimum_pass_cost_adjusted_edge_bps,
    )
    resolution_safety_score = _subtract_decimal(ONE, candidate.resolution_risk_score)
    liquidity_capacity_score = _bounded_ratio(
        candidate.liquidity_capacity_ratio,
        config.minimum_pass_liquidity_capacity_ratio,
    )
    category_budget_score = _bounded_ratio(
        candidate.category_budget_remaining_ratio,
        config.minimum_pass_category_budget_remaining_ratio,
    )
    final_decision = _final_decision(
        cost_adjusted_edge_bps=cost_adjusted_edge_bps,
        evidence_quorum_score=candidate.evidence_quorum_score,
        source_confidence_score=candidate.source_confidence_score,
        resolution_risk_score=candidate.resolution_risk_score,
        liquidity_capacity_ratio=candidate.liquidity_capacity_ratio,
        category_budget_remaining_ratio=candidate.category_budget_remaining_ratio,
        team_consensus_score=candidate.team_consensus_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        source_reason_codes=candidate.reason_codes,
        final_decision=final_decision,
        cost_adjusted_edge_bps=cost_adjusted_edge_bps,
        evidence_quorum_score=candidate.evidence_quorum_score,
        source_confidence_score=candidate.source_confidence_score,
        resolution_risk_score=candidate.resolution_risk_score,
        liquidity_capacity_ratio=candidate.liquidity_capacity_ratio,
        category_budget_remaining_ratio=candidate.category_budget_remaining_ratio,
        team_consensus_score=candidate.team_consensus_score,
        config=config,
    )

    return StrategyRecommendationFinalDecisionMatrixV2Row(
        rank=rank,
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        side=candidate.side,
        category=candidate.category,
        gross_edge_bps=candidate.gross_edge_bps,
        taker_fee_bps=candidate.taker_fee_bps,
        spread_cost_bps=candidate.spread_cost_bps,
        slippage_cost_bps=candidate.slippage_cost_bps,
        total_cost_bps=total_cost_bps,
        cost_adjusted_edge_bps=cost_adjusted_edge_bps,
        cost_adjusted_edge_score=cost_adjusted_edge_score,
        evidence_quorum_score=candidate.evidence_quorum_score,
        source_confidence_score=candidate.source_confidence_score,
        resolution_risk_score=candidate.resolution_risk_score,
        resolution_safety_score=resolution_safety_score,
        liquidity_capacity_ratio=candidate.liquidity_capacity_ratio,
        liquidity_capacity_score=liquidity_capacity_score,
        category_budget_remaining_ratio=candidate.category_budget_remaining_ratio,
        category_budget_score=category_budget_score,
        team_consensus_score=candidate.team_consensus_score,
        decision_score=_decision_score(
            cost_adjusted_edge_score=cost_adjusted_edge_score,
            evidence_quorum_score=candidate.evidence_quorum_score,
            source_confidence_score=candidate.source_confidence_score,
            resolution_safety_score=resolution_safety_score,
            liquidity_capacity_score=liquidity_capacity_score,
            category_budget_score=category_budget_score,
            team_consensus_score=candidate.team_consensus_score,
        ),
        final_decision=final_decision,
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[StrategyRecommendationFinalDecisionMatrixV2Row, ...],
) -> tuple[StrategyRecommendationFinalDecisionMatrixV2Row, ...]:
    return tuple(
        StrategyRecommendationFinalDecisionMatrixV2Row(
            rank=_count(index),
            candidate_id=row.candidate_id,
            market_slug=row.market_slug,
            side=row.side,
            category=row.category,
            gross_edge_bps=row.gross_edge_bps,
            taker_fee_bps=row.taker_fee_bps,
            spread_cost_bps=row.spread_cost_bps,
            slippage_cost_bps=row.slippage_cost_bps,
            total_cost_bps=row.total_cost_bps,
            cost_adjusted_edge_bps=row.cost_adjusted_edge_bps,
            cost_adjusted_edge_score=row.cost_adjusted_edge_score,
            evidence_quorum_score=row.evidence_quorum_score,
            source_confidence_score=row.source_confidence_score,
            resolution_risk_score=row.resolution_risk_score,
            resolution_safety_score=row.resolution_safety_score,
            liquidity_capacity_ratio=row.liquidity_capacity_ratio,
            liquidity_capacity_score=row.liquidity_capacity_score,
            category_budget_remaining_ratio=row.category_budget_remaining_ratio,
            category_budget_score=row.category_budget_score,
            team_consensus_score=row.team_consensus_score,
            decision_score=row.decision_score,
            final_decision=row.final_decision,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _final_decision(
    *,
    cost_adjusted_edge_bps: Decimal,
    evidence_quorum_score: Decimal,
    source_confidence_score: Decimal,
    resolution_risk_score: Decimal,
    liquidity_capacity_ratio: Decimal,
    category_budget_remaining_ratio: Decimal,
    team_consensus_score: Decimal,
    config: StrategyRecommendationFinalDecisionMatrixV2Config,
) -> str:
    if (
        cost_adjusted_edge_bps < config.minimum_watch_cost_adjusted_edge_bps
        or evidence_quorum_score < config.minimum_watch_evidence_quorum_score
        or source_confidence_score < config.minimum_watch_source_confidence_score
        or resolution_risk_score > config.maximum_watch_resolution_risk_score
        or liquidity_capacity_ratio < config.minimum_watch_liquidity_capacity_ratio
        or category_budget_remaining_ratio
        < config.minimum_watch_category_budget_remaining_ratio
        or team_consensus_score < config.minimum_watch_team_consensus_score
    ):
        return "abstain"
    if (
        evidence_quorum_score < config.minimum_pass_evidence_quorum_score
        or source_confidence_score < config.minimum_pass_source_confidence_score
        or resolution_risk_score > config.maximum_pass_resolution_risk_score
        or team_consensus_score < config.minimum_pass_team_consensus_score
    ):
        return "manual-review"
    if (
        cost_adjusted_edge_bps < config.minimum_pass_cost_adjusted_edge_bps
        or liquidity_capacity_ratio < config.minimum_pass_liquidity_capacity_ratio
        or category_budget_remaining_ratio
        < config.minimum_pass_category_budget_remaining_ratio
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    source_reason_codes: tuple[str, ...],
    final_decision: str,
    cost_adjusted_edge_bps: Decimal,
    evidence_quorum_score: Decimal,
    source_confidence_score: Decimal,
    resolution_risk_score: Decimal,
    liquidity_capacity_ratio: Decimal,
    category_budget_remaining_ratio: Decimal,
    team_consensus_score: Decimal,
    config: StrategyRecommendationFinalDecisionMatrixV2Config,
) -> tuple[str, ...]:
    reason_codes = [
        _final_decision_reason_code(final_decision),
        _minimum_reason_code(
            "cost_adjusted_edge",
            cost_adjusted_edge_bps,
            pass_value=config.minimum_pass_cost_adjusted_edge_bps,
            watch_value=config.minimum_watch_cost_adjusted_edge_bps,
            review_label="watch",
        ),
        _minimum_reason_code(
            "evidence_quorum",
            evidence_quorum_score,
            pass_value=config.minimum_pass_evidence_quorum_score,
            watch_value=config.minimum_watch_evidence_quorum_score,
            review_label="review",
        ),
        _minimum_reason_code(
            "source_confidence",
            source_confidence_score,
            pass_value=config.minimum_pass_source_confidence_score,
            watch_value=config.minimum_watch_source_confidence_score,
            review_label="review",
        ),
        _maximum_reason_code(
            "resolution_risk",
            resolution_risk_score,
            pass_value=config.maximum_pass_resolution_risk_score,
            watch_value=config.maximum_watch_resolution_risk_score,
        ),
        _minimum_reason_code(
            "liquidity_capacity",
            liquidity_capacity_ratio,
            pass_value=config.minimum_pass_liquidity_capacity_ratio,
            watch_value=config.minimum_watch_liquidity_capacity_ratio,
            review_label="watch",
        ),
        _minimum_reason_code(
            "category_budget",
            category_budget_remaining_ratio,
            pass_value=config.minimum_pass_category_budget_remaining_ratio,
            watch_value=config.minimum_watch_category_budget_remaining_ratio,
            review_label="watch",
        ),
        _minimum_reason_code(
            "team_consensus",
            team_consensus_score,
            pass_value=config.minimum_pass_team_consensus_score,
            watch_value=config.minimum_watch_team_consensus_score,
            review_label="review",
        ),
    ]
    reason_codes.extend(source_reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _final_decision_reason_code(final_decision: str) -> str:
    if final_decision == "manual-review":
        return "final_decision_manual_review"
    return f"final_decision_{final_decision}"


def _minimum_reason_code(
    prefix: str,
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
    review_label: str,
) -> str:
    if value >= pass_value:
        return f"{prefix}_pass"
    if value >= watch_value:
        return f"{prefix}_{review_label}"
    return f"{prefix}_abstain"


def _maximum_reason_code(
    prefix: str,
    value: Decimal,
    *,
    pass_value: Decimal,
    watch_value: Decimal,
) -> str:
    if value <= pass_value:
        return f"{prefix}_pass"
    if value <= watch_value:
        return f"{prefix}_review"
    return f"{prefix}_abstain"


def _decision_score(
    *,
    cost_adjusted_edge_score: Decimal,
    evidence_quorum_score: Decimal,
    source_confidence_score: Decimal,
    resolution_safety_score: Decimal,
    liquidity_capacity_score: Decimal,
    category_budget_score: Decimal,
    team_consensus_score: Decimal,
) -> Decimal:
    return _divide_decimal(
        _sum_decimals(
            cost_adjusted_edge_score,
            evidence_quorum_score,
            source_confidence_score,
            resolution_safety_score,
            liquidity_capacity_score,
            category_budget_score,
            team_consensus_score,
        ),
        Decimal("7"),
    )


def _row_payload(row: StrategyRecommendationFinalDecisionMatrixV2Row) -> dict[str, Any]:
    return {
        "rank": row.rank,
        "candidate_id": row.candidate_id,
        "market_slug": row.market_slug,
        "side": row.side,
        "category": row.category,
        "gross_edge_bps": row.gross_edge_bps,
        "taker_fee_bps": row.taker_fee_bps,
        "spread_cost_bps": row.spread_cost_bps,
        "slippage_cost_bps": row.slippage_cost_bps,
        "total_cost_bps": row.total_cost_bps,
        "cost_adjusted_edge_bps": row.cost_adjusted_edge_bps,
        "cost_adjusted_edge_score": row.cost_adjusted_edge_score,
        "evidence_quorum_score": row.evidence_quorum_score,
        "source_confidence_score": row.source_confidence_score,
        "resolution_risk_score": row.resolution_risk_score,
        "resolution_safety_score": row.resolution_safety_score,
        "liquidity_capacity_ratio": row.liquidity_capacity_ratio,
        "liquidity_capacity_score": row.liquidity_capacity_score,
        "category_budget_remaining_ratio": row.category_budget_remaining_ratio,
        "category_budget_score": row.category_budget_score,
        "team_consensus_score": row.team_consensus_score,
        "decision_score": row.decision_score,
        "final_decision": row.final_decision,
        "reason_codes": row.reason_codes,
        "decision_digest": row.decision_digest,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_digest_payload(
    row: StrategyRecommendationFinalDecisionMatrixV2Row,
) -> dict[str, Any]:
    payload = _row_payload(row)
    return {key: value for key, value in payload.items() if key != "decision_digest"}


def _report_payload(
    report: StrategyRecommendationFinalDecisionMatrixV2Report,
) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "abstain_count": report.abstain_count,
        "manual_review_count": report.manual_review_count,
        "top_candidate_id": report.top_candidate_id,
        "final_decision": report.final_decision,
        "average_decision_score": report.average_decision_score,
        "max_decision_score": report.max_decision_score,
        "reason_codes": report.reason_codes,
        "rows": tuple(_row_payload(row) for row in report.rows),
        "report_digest": report.report_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_digest_payload(
    report: StrategyRecommendationFinalDecisionMatrixV2Report,
) -> dict[str, Any]:
    payload = _report_payload(report)
    return {key: value for key, value in payload.items() if key != "report_digest"}


def _row_digest(row: StrategyRecommendationFinalDecisionMatrixV2Row) -> str:
    return _digest(_row_digest_payload(row))


def _report_digest(report: StrategyRecommendationFinalDecisionMatrixV2Report) -> str:
    return _digest(_report_digest_payload(report))


def _digest(payload: dict[str, Any]) -> str:
    ready = json_ready_no_floats(payload)
    text = json.dumps(ready, allow_nan=False, separators=(",", ":"), sort_keys=True)
    return f"sha256:{sha256(text.encode('utf-8')).hexdigest()}"


def _validate_row(row: StrategyRecommendationFinalDecisionMatrixV2Row) -> None:
    if row.total_cost_bps != _sum_decimals(
        row.taker_fee_bps,
        row.spread_cost_bps,
        row.slippage_cost_bps,
    ):
        raise ValueError("total_cost_bps must match explicit costs")
    if row.cost_adjusted_edge_bps != _subtract_decimal(
        row.gross_edge_bps,
        row.total_cost_bps,
    ):
        raise ValueError("cost_adjusted_edge_bps must match gross edge less costs")
    if row.resolution_safety_score != _subtract_decimal(ONE, row.resolution_risk_score):
        raise ValueError("resolution_safety_score must match resolution risk")
    if row.decision_score != _decision_score(
        cost_adjusted_edge_score=row.cost_adjusted_edge_score,
        evidence_quorum_score=row.evidence_quorum_score,
        source_confidence_score=row.source_confidence_score,
        resolution_safety_score=row.resolution_safety_score,
        liquidity_capacity_score=row.liquidity_capacity_score,
        category_budget_score=row.category_budget_score,
        team_consensus_score=row.team_consensus_score,
    ):
        raise ValueError("decision_score must match component scores")
    expected_decision_reason = _final_decision_reason_code(row.final_decision)
    if expected_decision_reason not in row.reason_codes:
        raise ValueError("reason_codes must include final decision")


def _validate_report(report: StrategyRecommendationFinalDecisionMatrixV2Report) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.abstain_count != _status_count(report.rows, "abstain"):
        raise ValueError("abstain_count must match rows")
    if report.manual_review_count != _status_count(report.rows, "manual-review"):
        raise ValueError("manual_review_count must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    expected_ranks = tuple(_count(index) for index in range(1, len(report.rows) + 1))
    if tuple(row.rank for row in report.rows) != expected_ranks:
        raise ValueError("rows must use consecutive ranks")
    top_row = report.rows[0] if report.rows else None
    if (None if top_row is None else top_row.candidate_id) != report.top_candidate_id:
        raise ValueError("top_candidate_id must match rows")
    expected_final_decision = "abstain" if top_row is None else top_row.final_decision
    if report.final_decision != expected_final_decision:
        raise ValueError("final_decision must match rows")
    if report.average_decision_score != _average_score(report.rows):
        raise ValueError("average_decision_score must match rows")
    if report.max_decision_score != _max_score(report.rows):
        raise ValueError("max_decision_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_candidates(
    candidates: Iterable[StrategyRecommendationFinalDecisionMatrixV2Candidate],
) -> tuple[StrategyRecommendationFinalDecisionMatrixV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyRecommendationFinalDecisionMatrixV2Candidate:
            raise ValueError(
                "candidates must contain StrategyRecommendationFinalDecisionMatrixV2Candidate",
            )
        require_paper_only_flags("candidate", candidate)
        if candidate.candidate_id in seen:
            raise ValueError("candidates must not contain duplicate candidate_id values")
        seen.add(candidate.candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyRecommendationFinalDecisionMatrixV2Row],
) -> tuple[StrategyRecommendationFinalDecisionMatrixV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyRecommendationFinalDecisionMatrixV2Row:
            raise ValueError("rows must contain StrategyRecommendationFinalDecisionMatrixV2Row")
        require_paper_only_flags("row", row)
        _verify_row_digest(row)
    return normalized


def _status_count(
    rows: tuple[StrategyRecommendationFinalDecisionMatrixV2Row, ...],
    final_decision: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.final_decision == final_decision))


def _average_score(rows: tuple[StrategyRecommendationFinalDecisionMatrixV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return _divide_decimal(
        _sum_decimals(*(row.decision_score for row in rows)),
        _count(len(rows)),
    )


def _max_score(rows: tuple[StrategyRecommendationFinalDecisionMatrixV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.decision_score for row in rows)


def _report_reason_codes(
    rows: tuple[StrategyRecommendationFinalDecisionMatrixV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_candidates",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    reason_codes.append("candidates_ranked")
    return _normalize_reason_codes(tuple(dict.fromkeys(reason_codes)), require_nonempty=True)


def _row_sort_key(row: StrategyRecommendationFinalDecisionMatrixV2Row) -> tuple[object, ...]:
    return (
        _decision_rank(row.final_decision),
        -row.decision_score,
        -row.cost_adjusted_edge_bps,
        -row.evidence_quorum_score,
        -row.source_confidence_score,
        row.resolution_risk_score,
        -row.liquidity_capacity_ratio,
        -row.category_budget_remaining_ratio,
        -row.team_consensus_score,
        row.candidate_id,
        row.market_slug,
        row.side,
    )


def _decision_rank(final_decision: str) -> Decimal:
    if final_decision == "pass":
        return Decimal("0")
    if final_decision == "manual-review":
        return Decimal("1")
    if final_decision == "watch":
        return Decimal("2")
    if final_decision == "abstain":
        return Decimal("3")
    raise ValueError("final_decision must be known")


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for item in value:
        _require_public_identifier("reason_codes", item)
        if item in seen:
            raise ValueError("reason_codes must not contain duplicate values")
        seen.add(item)
    return tuple(sorted(seen, key=_reason_key))


def _reason_key(reason_code: str) -> tuple[Decimal, str]:
    return (REASON_CODE_RANK.get(reason_code, Decimal(len(KNOWN_REASON_CODE_SEQUENCE))), reason_code)


def _verify_row_digest(row: StrategyRecommendationFinalDecisionMatrixV2Row) -> None:
    if row.decision_digest != _row_digest(row):
        raise ValueError("decision_digest must match row")


def _verify_report_digest(report: StrategyRecommendationFinalDecisionMatrixV2Report) -> None:
    if report.report_digest != _report_digest(report):
        raise ValueError("report_digest must match report")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    prefix = "sha256:"
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be a sha256 digest")
    digest = value[len(prefix) :]
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if any(char not in ALLOWED_IDENTIFIER_CHARS for char in value):
        raise ValueError(f"{field_name} contains unsupported characters")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in choices:
        raise ValueError(f"{field_name} must be a known value")


def _require_positive(field_name: str, value: Decimal) -> None:
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_not_below(
    upper_field_name: str,
    upper_value: Decimal,
    lower_field_name: str,
    lower_value: Decimal,
) -> None:
    if lower_value > upper_value:
        raise ValueError(f"{lower_field_name} must not exceed {upper_field_name}")


def _require_not_above(
    lower_field_name: str,
    lower_value: Decimal,
    upper_field_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value > upper_value:
        raise ValueError(f"{lower_field_name} must not exceed {upper_field_name}")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be whole")
    return value.quantize(COUNT_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
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
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _sum_decimals(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
    return _quantize(total)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = left - right
    return _quantize(value)


def _divide_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    return _quantize(value)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    if numerator <= ZERO:
        return ZERO
    if numerator >= denominator:
        return ONE
    return _divide_decimal(numerator, denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_values(value: object) -> None:
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError("payload has unsafe public value")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_unsafe_public_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_values(item)


__all__ = (
    "DEFAULT_STRATEGY_RECOMMENDATION_FINAL_DECISION_MATRIX_V2_CONFIG_VERSION",
    "StrategyRecommendationFinalDecisionMatrixV2Candidate",
    "StrategyRecommendationFinalDecisionMatrixV2Config",
    "StrategyRecommendationFinalDecisionMatrixV2Report",
    "StrategyRecommendationFinalDecisionMatrixV2Row",
    "build_strategy_recommendation_final_decision_matrix_v2_report",
    "strategy_recommendation_final_decision_matrix_v2_payload",
)
