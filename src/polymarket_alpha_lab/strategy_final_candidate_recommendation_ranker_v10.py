"""Pure paper-only final candidate recommendation ranker v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_FINAL_CANDIDATE_RECOMMENDATION_RANKER_V10_CONFIG_VERSION = (
    "final-candidate-recommendation-ranker-v10"
)

BPS_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_BPS = Decimal("0.000000")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DATA_GAP_STATUSES = ("none", "minor", "material", "blocking")
RECOMMENDATION_STATUSES = ("recommend", "review", "watch", "blocked", "empty")
REASON_CODES = (
    "positive_net_edge",
    "nonpositive_net_edge",
    "liquidity_supported",
    "liquidity_watch",
    "team_fit_supported",
    "team_fit_watch",
    "data_gap_none",
    "data_gap_minor",
    "data_gap_material",
    "data_gap_blocking",
    "human_review_required",
    "manual_research_ready",
    "manual_research_watch",
    "score_review_band",
    "score_watch_band",
    "top_candidate_recommended",
    "top_candidate_needs_human_review",
    "top_candidate_review",
    "top_candidate_watch",
    "top_candidate_blocked",
    "candidates_ranked",
    "no_candidates",
)


@dataclass(frozen=True)
class FinalCandidateRecommendationRankerV10Config:
    config_version: str = DEFAULT_FINAL_CANDIDATE_RECOMMENDATION_RANKER_V10_CONFIG_VERSION
    minimum_recommendation_score_bps: Decimal = Decimal("50.000000")
    minimum_review_score_bps: Decimal = Decimal("0.000000")
    liquidity_weight_bps: Decimal = Decimal("20.000000")
    team_fit_weight_bps: Decimal = Decimal("15.000000")
    minor_data_gap_penalty_bps: Decimal = Decimal("10.000000")
    material_data_gap_penalty_bps: Decimal = Decimal("35.000000")
    human_review_penalty_bps: Decimal = Decimal("25.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_recommendation_score_bps",
            "minimum_review_score_bps",
            "liquidity_weight_bps",
            "team_fit_weight_bps",
            "minor_data_gap_penalty_bps",
            "material_data_gap_penalty_bps",
            "human_review_penalty_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        if self.minimum_review_score_bps > self.minimum_recommendation_score_bps:
            raise ValueError(
                "minimum_review_score_bps must be <= "
                "minimum_recommendation_score_bps",
            )
        if self.minor_data_gap_penalty_bps > self.material_data_gap_penalty_bps:
            raise ValueError(
                "minor_data_gap_penalty_bps must be <= "
                "material_data_gap_penalty_bps",
            )
        require_paper_only_flags("FinalCandidateRecommendationRankerV10Config", self)


@dataclass(frozen=True)
class FinalCandidateRecommendationRankerV10Input:
    market_id: str
    cost_adjusted_edge_bps: Decimal
    confidence_penalty_bps: Decimal
    liquidity_score: Decimal
    resolution_risk_premium_bps: Decimal
    team_fit_score: Decimal
    data_gap_status: str
    human_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("market_id", self.market_id)
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_bps("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        for field_name in (
            "confidence_penalty_bps",
            "resolution_risk_premium_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        for field_name in ("liquidity_score", "team_fit_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_choice("data_gap_status", self.data_gap_status, DATA_GAP_STATUSES)
        _require_bool("human_review_required", self.human_review_required)
        require_paper_only_flags("FinalCandidateRecommendationRankerV10Input", self)


@dataclass(frozen=True)
class FinalCandidateRecommendationRankerV10RankedRow:
    rank: Decimal
    market_id: str
    cost_adjusted_edge_bps: Decimal
    confidence_penalty_bps: Decimal
    liquidity_score: Decimal
    resolution_risk_premium_bps: Decimal
    team_fit_score: Decimal
    data_gap_status: str
    human_review_required: bool
    data_gap_penalty_bps: Decimal
    human_review_penalty_bps: Decimal
    recommendation_score_bps: Decimal
    recommendation_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_identifier("market_id", self.market_id)
        object.__setattr__(
            self,
            "cost_adjusted_edge_bps",
            _normalize_bps("cost_adjusted_edge_bps", self.cost_adjusted_edge_bps),
        )
        for field_name in (
            "confidence_penalty_bps",
            "resolution_risk_premium_bps",
            "data_gap_penalty_bps",
            "human_review_penalty_bps",
            "recommendation_score_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_bps(field_name, getattr(self, field_name)),
            )
        for field_name in ("liquidity_score", "team_fit_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_choice("data_gap_status", self.data_gap_status, DATA_GAP_STATUSES)
        _require_bool("human_review_required", self.human_review_required)
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
        require_paper_only_flags("FinalCandidateRecommendationRankerV10RankedRow", self)


@dataclass(frozen=True)
class FinalCandidateRecommendationRankerV10Report:
    config_version: str
    candidate_count: Decimal
    ranked_rows: tuple[FinalCandidateRecommendationRankerV10RankedRow, ...]
    top_market_id: str | None
    recommendation_status: str
    reason_codes: tuple[str, ...]
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
        if self.top_market_id is not None:
            _require_identifier("top_market_id", self.top_market_id)
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
        require_paper_only_flags("FinalCandidateRecommendationRankerV10Report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return final_candidate_recommendation_ranker_v10_payload(self)


def rank_final_candidate_recommendations_v10(
    candidates: tuple[FinalCandidateRecommendationRankerV10Input, ...],
    *,
    config: FinalCandidateRecommendationRankerV10Config | None = None,
) -> FinalCandidateRecommendationRankerV10Report:
    active_config = config or FinalCandidateRecommendationRankerV10Config()
    if type(active_config) is not FinalCandidateRecommendationRankerV10Config:
        raise ValueError("config must be a FinalCandidateRecommendationRankerV10Config")
    require_paper_only_flags("config", active_config)
    normalized_candidates = _normalize_inputs(candidates)
    _validate_unique_candidates(normalized_candidates)

    unranked_rows = tuple(
        _ranked_row(candidate, rank=ZERO_COUNT, config=active_config)
        for candidate in normalized_candidates
    )
    sorted_rows = tuple(
        sorted(
            unranked_rows,
            key=lambda row: (
                _status_rank(row.recommendation_status),
                -row.recommendation_score_bps,
                row.market_id,
            ),
        ),
    )
    ranked_rows = tuple(
        _replace_rank(row, Decimal(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    top_row = ranked_rows[0] if ranked_rows else None

    return FinalCandidateRecommendationRankerV10Report(
        config_version=active_config.config_version,
        candidate_count=Decimal(len(ranked_rows)),
        ranked_rows=ranked_rows,
        top_market_id=None if top_row is None else top_row.market_id,
        recommendation_status="empty" if top_row is None else top_row.recommendation_status,
        reason_codes=_report_reason_codes(top_row),
    )


def final_candidate_recommendation_ranker_v10_payload(
    report: FinalCandidateRecommendationRankerV10Report,
) -> dict[str, Any]:
    if type(report) is not FinalCandidateRecommendationRankerV10Report:
        raise ValueError(
            "report must be a FinalCandidateRecommendationRankerV10Report",
        )
    require_paper_only_flags("report", report)
    payload = {
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "ranked_rows": tuple(_row_payload(row) for row in report.ranked_rows),
        "top_market_id": report.top_market_id,
        "recommendation_status": report.recommendation_status,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    reject_unsafe_surface_fields("final candidate recommendation ranker v10", payload)
    ready = json_ready_no_floats(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _ranked_row(
    candidate: FinalCandidateRecommendationRankerV10Input,
    *,
    rank: Decimal,
    config: FinalCandidateRecommendationRankerV10Config,
) -> FinalCandidateRecommendationRankerV10RankedRow:
    if candidate.data_gap_status == "blocking":
        return FinalCandidateRecommendationRankerV10RankedRow(
            rank=rank if rank > ZERO_COUNT else Decimal("1"),
            market_id=candidate.market_id,
            cost_adjusted_edge_bps=candidate.cost_adjusted_edge_bps,
            confidence_penalty_bps=candidate.confidence_penalty_bps,
            liquidity_score=candidate.liquidity_score,
            resolution_risk_premium_bps=candidate.resolution_risk_premium_bps,
            team_fit_score=candidate.team_fit_score,
            data_gap_status=candidate.data_gap_status,
            human_review_required=candidate.human_review_required,
            data_gap_penalty_bps=ZERO_BPS,
            human_review_penalty_bps=ZERO_BPS,
            recommendation_score_bps=ZERO_BPS,
            recommendation_status="blocked",
            reason_codes=("data_gap_blocking",),
        )

    data_gap_penalty_bps = _data_gap_penalty(candidate.data_gap_status, config)
    human_review_penalty_bps = (
        config.human_review_penalty_bps
        if candidate.human_review_required
        else ZERO_BPS
    )
    recommendation_score_bps = _recommendation_score_bps(
        candidate,
        data_gap_penalty_bps=data_gap_penalty_bps,
        human_review_penalty_bps=human_review_penalty_bps,
        config=config,
    )
    status = _recommendation_status(
        recommendation_score_bps,
        human_review_required=candidate.human_review_required,
        config=config,
    )

    return FinalCandidateRecommendationRankerV10RankedRow(
        rank=rank if rank > ZERO_COUNT else Decimal("1"),
        market_id=candidate.market_id,
        cost_adjusted_edge_bps=candidate.cost_adjusted_edge_bps,
        confidence_penalty_bps=candidate.confidence_penalty_bps,
        liquidity_score=candidate.liquidity_score,
        resolution_risk_premium_bps=candidate.resolution_risk_premium_bps,
        team_fit_score=candidate.team_fit_score,
        data_gap_status=candidate.data_gap_status,
        human_review_required=candidate.human_review_required,
        data_gap_penalty_bps=data_gap_penalty_bps,
        human_review_penalty_bps=human_review_penalty_bps,
        recommendation_score_bps=recommendation_score_bps,
        recommendation_status=status,
        reason_codes=_row_reason_codes(candidate, status, recommendation_score_bps),
    )


def _replace_rank(
    row: FinalCandidateRecommendationRankerV10RankedRow,
    rank: Decimal,
) -> FinalCandidateRecommendationRankerV10RankedRow:
    return FinalCandidateRecommendationRankerV10RankedRow(
        rank=rank,
        market_id=row.market_id,
        cost_adjusted_edge_bps=row.cost_adjusted_edge_bps,
        confidence_penalty_bps=row.confidence_penalty_bps,
        liquidity_score=row.liquidity_score,
        resolution_risk_premium_bps=row.resolution_risk_premium_bps,
        team_fit_score=row.team_fit_score,
        data_gap_status=row.data_gap_status,
        human_review_required=row.human_review_required,
        data_gap_penalty_bps=row.data_gap_penalty_bps,
        human_review_penalty_bps=row.human_review_penalty_bps,
        recommendation_score_bps=row.recommendation_score_bps,
        recommendation_status=row.recommendation_status,
        reason_codes=row.reason_codes,
    )


def _recommendation_score_bps(
    candidate: FinalCandidateRecommendationRankerV10Input,
    *,
    data_gap_penalty_bps: Decimal,
    human_review_penalty_bps: Decimal,
    config: FinalCandidateRecommendationRankerV10Config,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            candidate.cost_adjusted_edge_bps
            - candidate.confidence_penalty_bps
            - candidate.resolution_risk_premium_bps
            + candidate.liquidity_score * config.liquidity_weight_bps
            + candidate.team_fit_score * config.team_fit_weight_bps
            - data_gap_penalty_bps
            - human_review_penalty_bps
        )
    if raw_score <= ZERO_BPS:
        return ZERO_BPS
    return _normalize_bps("recommendation_score_bps", raw_score)


def _recommendation_status(
    recommendation_score_bps: Decimal,
    *,
    human_review_required: bool,
    config: FinalCandidateRecommendationRankerV10Config,
) -> str:
    if human_review_required:
        return "review"
    if recommendation_score_bps >= config.minimum_recommendation_score_bps:
        return "recommend"
    if recommendation_score_bps >= config.minimum_review_score_bps:
        return "review"
    return "watch"


def _data_gap_penalty(
    data_gap_status: str,
    config: FinalCandidateRecommendationRankerV10Config,
) -> Decimal:
    if data_gap_status == "none":
        return ZERO_BPS
    if data_gap_status == "minor":
        return config.minor_data_gap_penalty_bps
    if data_gap_status == "material":
        return config.material_data_gap_penalty_bps
    if data_gap_status == "blocking":
        return ZERO_BPS
    raise ValueError("data_gap_status must be supported")


def _row_reason_codes(
    candidate: FinalCandidateRecommendationRankerV10Input,
    status: str,
    recommendation_score_bps: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    codes.append(
        "positive_net_edge"
        if recommendation_score_bps > ZERO_BPS
        else "nonpositive_net_edge",
    )
    codes.append(
        "liquidity_supported"
        if candidate.liquidity_score >= Decimal("0.500000")
        else "liquidity_watch",
    )
    codes.append(
        "team_fit_supported"
        if candidate.team_fit_score >= Decimal("0.500000")
        else "team_fit_watch",
    )
    codes.append(f"data_gap_{candidate.data_gap_status}")
    if candidate.human_review_required:
        codes.append("human_review_required")
    elif status == "recommend":
        codes.append("manual_research_ready")
    elif status == "review":
        codes.append("score_review_band")
    else:
        codes.append("score_watch_band")
    if status != "recommend" and not candidate.human_review_required:
        codes.append("manual_research_watch")
    return _normalize_reason_codes(tuple(codes))


def _report_reason_codes(
    top_row: FinalCandidateRecommendationRankerV10RankedRow | None,
) -> tuple[str, ...]:
    if top_row is None:
        return ("no_candidates",)
    if top_row.recommendation_status == "recommend":
        return ("top_candidate_recommended", "candidates_ranked")
    if top_row.recommendation_status == "review" and top_row.human_review_required:
        return ("top_candidate_needs_human_review", "candidates_ranked")
    if top_row.recommendation_status == "review":
        return ("top_candidate_review", "candidates_ranked")
    if top_row.recommendation_status == "watch":
        return ("top_candidate_watch", "candidates_ranked")
    return ("top_candidate_blocked", "candidates_ranked")


def _row_payload(row: FinalCandidateRecommendationRankerV10RankedRow) -> dict[str, Any]:
    return {
        "rank": row.rank,
        "market_id": row.market_id,
        "cost_adjusted_edge_bps": row.cost_adjusted_edge_bps,
        "confidence_penalty_bps": row.confidence_penalty_bps,
        "liquidity_score": row.liquidity_score,
        "resolution_risk_premium_bps": row.resolution_risk_premium_bps,
        "team_fit_score": row.team_fit_score,
        "data_gap_status": row.data_gap_status,
        "human_review_required": row.human_review_required,
        "data_gap_penalty_bps": row.data_gap_penalty_bps,
        "human_review_penalty_bps": row.human_review_penalty_bps,
        "recommendation_score_bps": row.recommendation_score_bps,
        "recommendation_status": row.recommendation_status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_ranked_row(row: FinalCandidateRecommendationRankerV10RankedRow) -> None:
    if row.data_gap_status == "blocking":
        if row.recommendation_status != "blocked":
            raise ValueError("blocking data gaps must be blocked")
        if row.recommendation_score_bps != ZERO_BPS:
            raise ValueError("blocking data gaps must have zero recommendation_score_bps")
        if row.reason_codes != ("data_gap_blocking",):
            raise ValueError("blocking rows must use data_gap_blocking reason code")
    if row.human_review_required and row.recommendation_status == "recommend":
        raise ValueError("human_review_required rows cannot be direct recommendations")


def _validate_report(report: FinalCandidateRecommendationRankerV10Report) -> None:
    if report.candidate_count != Decimal(len(report.ranked_rows)):
        raise ValueError("candidate_count must match ranked_rows")
    ids = tuple(row.market_id for row in report.ranked_rows)
    if len(ids) != len(set(ids)):
        raise ValueError("ranked_rows must contain unique market_id values")
    expected_ranks = tuple(Decimal(index) for index in range(1, len(report.ranked_rows) + 1))
    if tuple(row.rank for row in report.ranked_rows) != expected_ranks:
        raise ValueError("ranked_rows must use contiguous Decimal ranks")
    if report.ranked_rows != _expected_row_order(report.ranked_rows):
        raise ValueError("ranked_rows must use deterministic ranking")
    top_row = report.ranked_rows[0] if report.ranked_rows else None
    if (None if top_row is None else top_row.market_id) != report.top_market_id:
        raise ValueError("top_market_id must match ranked_rows")
    if ("empty" if top_row is None else top_row.recommendation_status) != (
        report.recommendation_status
    ):
        raise ValueError("recommendation_status must match ranked_rows")
    if report.reason_codes != _report_reason_codes(top_row):
        raise ValueError("reason_codes must match ranked_rows")


def _expected_row_order(
    rows: tuple[FinalCandidateRecommendationRankerV10RankedRow, ...],
) -> tuple[FinalCandidateRecommendationRankerV10RankedRow, ...]:
    reranked = tuple(
        _replace_rank(row, Decimal(index))
        for index, row in enumerate(
            sorted(
                rows,
                key=lambda row: (
                    _status_rank(row.recommendation_status),
                    -row.recommendation_score_bps,
                    row.market_id,
                ),
            ),
            start=1,
        )
    )
    return reranked


def _normalize_inputs(
    candidates: tuple[FinalCandidateRecommendationRankerV10Input, ...],
) -> tuple[FinalCandidateRecommendationRankerV10Input, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    for candidate in normalized:
        if type(candidate) is not FinalCandidateRecommendationRankerV10Input:
            raise ValueError(
                "candidates must contain FinalCandidateRecommendationRankerV10Input",
            )
        require_paper_only_flags("candidate", candidate)
    return normalized


def _normalize_ranked_rows(
    rows: tuple[FinalCandidateRecommendationRankerV10RankedRow, ...],
) -> tuple[FinalCandidateRecommendationRankerV10RankedRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("ranked_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("ranked_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not FinalCandidateRecommendationRankerV10RankedRow:
            raise ValueError(
                "ranked_rows must contain FinalCandidateRecommendationRankerV10RankedRow",
            )
        require_paper_only_flags("ranked row", row)
    return normalized


def _validate_unique_candidates(
    candidates: tuple[FinalCandidateRecommendationRankerV10Input, ...],
) -> None:
    market_ids = tuple(candidate.market_id for candidate in candidates)
    if len(market_ids) != len(set(market_ids)):
        raise ValueError("candidates must not contain duplicate market_id values")


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


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_bps(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be less than or equal to one")
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


__all__ = (
    "DEFAULT_FINAL_CANDIDATE_RECOMMENDATION_RANKER_V10_CONFIG_VERSION",
    "DATA_GAP_STATUSES",
    "RECOMMENDATION_STATUSES",
    "REASON_CODES",
    "FinalCandidateRecommendationRankerV10Config",
    "FinalCandidateRecommendationRankerV10Input",
    "FinalCandidateRecommendationRankerV10RankedRow",
    "FinalCandidateRecommendationRankerV10Report",
    "rank_final_candidate_recommendations_v10",
    "final_candidate_recommendation_ranker_v10_payload",
)
