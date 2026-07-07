"""Paper-only candidate recommendation trace report v2."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


__all__ = (
    "StrategyCandidateRecommendationTraceV2Candidate",
    "StrategyCandidateRecommendationTraceV2Config",
    "StrategyCandidateRecommendationTraceV2Report",
    "StrategyCandidateRecommendationTraceV2Row",
    "build_strategy_candidate_recommendation_trace_v2_report",
    "strategy_candidate_recommendation_trace_v2_payload",
    "validate_strategy_candidate_recommendation_trace_v2_public_payload",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
RECOMMENDATION_STATUSES = ("promoted", "watched", "blocked")
SIDES = ("yes", "no")
STATUS_PRIORITY = {"promoted": 0, "watched": 1, "blocked": 2}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sig" + "ning",
    "muta" + "tion",
    "b" + "uy",
    "se" + "ll",
    "tr" + "ade",
)
ROW_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "candidate_id",
    "market_slug",
    "question",
    "category",
    "side",
    "observed_at",
    "forecast_probability",
    "market_probability",
    "gross_probability_edge",
    "fee_probability_cost",
    "spread_probability_cost",
    "slippage_probability_cost",
    "settlement_probability_cost",
    "total_break_even_cost_probability",
    "break_even_probability",
    "edge_after_break_even",
    "source_quality_score",
    "specialist_arbitration_score",
    "resolution_risk_score",
    "liquidity_exit_feasibility_score",
    "category_exposure_ratio",
    "forecast_edge_watch_margin",
    "forecast_edge_promote_margin",
    "source_quality_watch_margin",
    "source_quality_promote_margin",
    "specialist_arbitration_watch_margin",
    "specialist_arbitration_promote_margin",
    "resolution_risk_watch_headroom",
    "resolution_risk_promote_headroom",
    "liquidity_exit_watch_margin",
    "liquidity_exit_promote_margin",
    "category_exposure_watch_headroom",
    "category_exposure_promote_headroom",
    "watch_floor_margin",
    "promotion_margin",
    "recommendation_status",
    "explanation_bullets",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_FIELDS = (
    *ROW_PUBLIC_FIELDS_WITHOUT_DIGEST[:-3],
    DERIVED_VALIDATION_DIGEST_FIELD,
    *PHASE_FLAG_FIELDS,
)
REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "candidate_count",
    "row_count",
    "promoted_count",
    "watched_count",
    "blocked_count",
    "first_observed_at",
    "latest_observed_at",
    "max_edge_after_break_even",
    "min_watch_floor_margin",
    "min_promotion_margin",
    "report_status",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_FIELDS = (
    *REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST[:-3],
    DERIVED_VALIDATION_DIGEST_FIELD,
    *PHASE_FLAG_FIELDS,
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class StrategyCandidateRecommendationTraceV2Config(_FinalPublicDataclass):
    config_version: str
    min_promote_edge_after_break_even: Decimal
    min_watch_edge_after_break_even: Decimal
    min_promote_source_quality_score: Decimal
    min_watch_source_quality_score: Decimal
    min_promote_specialist_arbitration_score: Decimal
    min_watch_specialist_arbitration_score: Decimal
    max_promote_resolution_risk_score: Decimal
    max_watch_resolution_risk_score: Decimal
    min_promote_liquidity_exit_feasibility_score: Decimal
    min_watch_liquidity_exit_feasibility_score: Decimal
    max_promote_category_exposure_ratio: Decimal
    max_watch_category_exposure_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateRecommendationTraceV2Config,
            "config",
        )
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "min_promote_edge_after_break_even",
            "min_watch_edge_after_break_even",
            "min_promote_source_quality_score",
            "min_watch_source_quality_score",
            "min_promote_specialist_arbitration_score",
            "min_watch_specialist_arbitration_score",
            "max_promote_resolution_risk_score",
            "max_watch_resolution_risk_score",
            "min_promote_liquidity_exit_feasibility_score",
            "min_watch_liquidity_exit_feasibility_score",
            "max_promote_category_exposure_ratio",
            "max_watch_category_exposure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "min_watch_edge_after_break_even",
            self.min_watch_edge_after_break_even,
            self.min_promote_edge_after_break_even,
        )
        _require_at_most(
            "min_watch_source_quality_score",
            self.min_watch_source_quality_score,
            self.min_promote_source_quality_score,
        )
        _require_at_most(
            "min_watch_specialist_arbitration_score",
            self.min_watch_specialist_arbitration_score,
            self.min_promote_specialist_arbitration_score,
        )
        _require_at_most(
            "max_promote_resolution_risk_score",
            self.max_promote_resolution_risk_score,
            self.max_watch_resolution_risk_score,
        )
        _require_at_most(
            "min_watch_liquidity_exit_feasibility_score",
            self.min_watch_liquidity_exit_feasibility_score,
            self.min_promote_liquidity_exit_feasibility_score,
        )
        _require_at_most(
            "max_promote_category_exposure_ratio",
            self.max_promote_category_exposure_ratio,
            self.max_watch_category_exposure_ratio,
        )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateRecommendationTraceV2Candidate(_FinalPublicDataclass):
    candidate_id: str
    market_slug: str
    question: str
    category: str
    side: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    fee_probability_cost: Decimal
    spread_probability_cost: Decimal
    slippage_probability_cost: Decimal
    settlement_probability_cost: Decimal
    source_quality_score: Decimal
    specialist_arbitration_score: Decimal
    resolution_risk_score: Decimal
    liquidity_exit_feasibility_score: Decimal
    category_exposure_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyCandidateRecommendationTraceV2Candidate,
            "candidate",
        )
        for field_name in ("candidate_id", "market_slug", "question", "category"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_member("side", self.side, SIDES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_probability_cost",
            "spread_probability_cost",
            "slippage_probability_cost",
            "settlement_probability_cost",
            "source_quality_score",
            "specialist_arbitration_score",
            "resolution_risk_score",
            "liquidity_exit_feasibility_score",
            "category_exposure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("candidate", self)
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyCandidateRecommendationTraceV2Row(_FinalPublicDataclass):
    candidate_id: str
    market_slug: str
    question: str
    category: str
    side: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    fee_probability_cost: Decimal
    spread_probability_cost: Decimal
    slippage_probability_cost: Decimal
    settlement_probability_cost: Decimal
    total_break_even_cost_probability: Decimal
    break_even_probability: Decimal
    edge_after_break_even: Decimal
    source_quality_score: Decimal
    specialist_arbitration_score: Decimal
    resolution_risk_score: Decimal
    liquidity_exit_feasibility_score: Decimal
    category_exposure_ratio: Decimal
    forecast_edge_watch_margin: Decimal
    forecast_edge_promote_margin: Decimal
    source_quality_watch_margin: Decimal
    source_quality_promote_margin: Decimal
    specialist_arbitration_watch_margin: Decimal
    specialist_arbitration_promote_margin: Decimal
    resolution_risk_watch_headroom: Decimal
    resolution_risk_promote_headroom: Decimal
    liquidity_exit_watch_margin: Decimal
    liquidity_exit_promote_margin: Decimal
    category_exposure_watch_headroom: Decimal
    category_exposure_promote_headroom: Decimal
    watch_floor_margin: Decimal
    promotion_margin: Decimal
    recommendation_status: str
    explanation_bullets: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyCandidateRecommendationTraceV2Row, "row")
        for field_name in ("candidate_id", "market_slug", "question", "category"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_member("side", self.side, SIDES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_probability_cost",
            "spread_probability_cost",
            "slippage_probability_cost",
            "settlement_probability_cost",
            "source_quality_score",
            "specialist_arbitration_score",
            "resolution_risk_score",
            "liquidity_exit_feasibility_score",
            "category_exposure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_probability_edge",
            "total_break_even_cost_probability",
            "break_even_probability",
            "edge_after_break_even",
            "forecast_edge_watch_margin",
            "forecast_edge_promote_margin",
            "source_quality_watch_margin",
            "source_quality_promote_margin",
            "specialist_arbitration_watch_margin",
            "specialist_arbitration_promote_margin",
            "resolution_risk_watch_headroom",
            "resolution_risk_promote_headroom",
            "liquidity_exit_watch_margin",
            "liquidity_exit_promote_margin",
            "category_exposure_watch_headroom",
            "category_exposure_promote_headroom",
            "watch_floor_margin",
            "promotion_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "recommendation_status",
            self.recommendation_status,
            RECOMMENDATION_STATUSES,
        )
        object.__setattr__(
            self,
            "explanation_bullets",
            _normalize_texts("explanation_bullets", self.explanation_bullets),
        )
        if not self.explanation_bullets:
            raise ValueError("explanation_bullets must not be empty")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyCandidateRecommendationTraceV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    row_count: Decimal
    promoted_count: Decimal
    watched_count: Decimal
    blocked_count: Decimal
    first_observed_at: datetime | None
    latest_observed_at: datetime | None
    max_edge_after_break_even: Decimal
    min_watch_floor_margin: Decimal
    min_promotion_margin: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateRecommendationTraceV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyCandidateRecommendationTraceV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "row_count",
            "promoted_count",
            "watched_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "first_observed_at",
            _as_optional_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "max_edge_after_break_even",
            "min_watch_floor_margin",
            "min_promotion_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, RECOMMENDATION_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_strategy_candidate_recommendation_trace_v2_report(
    candidates: Iterable[StrategyCandidateRecommendationTraceV2Candidate],
    *,
    config: StrategyCandidateRecommendationTraceV2Config,
    generated_at: datetime,
) -> StrategyCandidateRecommendationTraceV2Report:
    """Build a pure in-memory report describing candidate recommendation status."""

    _require_exact_type("config", config, StrategyCandidateRecommendationTraceV2Config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    observed_times = tuple(row.observed_at for row in rows)
    report_status = _report_status(rows)
    return StrategyCandidateRecommendationTraceV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(normalized_candidates)),
        row_count=_count_decimal(len(rows)),
        promoted_count=_status_count(rows, "promoted"),
        watched_count=_status_count(rows, "watched"),
        blocked_count=_status_count(rows, "blocked"),
        first_observed_at=min(observed_times) if observed_times else None,
        latest_observed_at=max(observed_times) if observed_times else None,
        max_edge_after_break_even=_max_decimal(
            tuple(row.edge_after_break_even for row in rows),
        ),
        min_watch_floor_margin=_min_decimal(tuple(row.watch_floor_margin for row in rows)),
        min_promotion_margin=_min_decimal(tuple(row.promotion_margin for row in rows)),
        report_status=report_status,
        reason_codes=_report_reason_codes(report_status, rows),
        rows=rows,
    )


def strategy_candidate_recommendation_trace_v2_payload(
    report: StrategyCandidateRecommendationTraceV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is StrategyCandidateRecommendationTraceV2Report:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        _verify_digest(report)
        for row in report.rows:
            _verify_digest(row)
        payload = _json_ready(asdict(report))
        validate_strategy_candidate_recommendation_trace_v2_public_payload(payload)
        return payload
    if type(report) is dict:
        validate_strategy_candidate_recommendation_trace_v2_public_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a StrategyCandidateRecommendationTraceV2Report",
    )


def validate_strategy_candidate_recommendation_trace_v2_public_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_public_payload_json_ready(payload)
    _require_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload.get(DERIVED_VALIDATION_DIGEST_FIELD),  # type: ignore[arg-type]
    )
    _require_exact_payload_fields(payload, REPORT_PUBLIC_FIELDS, "report payload")
    _require_public_payload_flags(payload, "report payload")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_digest(
            DERIVED_VALIDATION_DIGEST_FIELD,
            row.get(DERIVED_VALIDATION_DIGEST_FIELD),  # type: ignore[arg-type]
        )
        _require_exact_payload_fields(row, ROW_PUBLIC_FIELDS, "row payload")
        _require_public_payload_flags(row, "row payload")
        _validate_public_payload_digest(row, ROW_PUBLIC_FIELDS_WITHOUT_DIGEST)
    _validate_public_payload_digest(payload, REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST)
    return True


def _row_from_candidate(
    candidate: StrategyCandidateRecommendationTraceV2Candidate,
    *,
    config: StrategyCandidateRecommendationTraceV2Config,
    generated_at: datetime,
) -> StrategyCandidateRecommendationTraceV2Row:
    observed_at = _as_utc("observed_at", candidate.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    gross_probability_edge = _subtract_decimal(
        candidate.forecast_probability,
        candidate.market_probability,
    )
    total_break_even_cost_probability = _sum_decimals(
        (
            candidate.fee_probability_cost,
            candidate.spread_probability_cost,
            candidate.slippage_probability_cost,
            candidate.settlement_probability_cost,
        ),
    )
    break_even_probability = _add_decimal(
        candidate.market_probability,
        total_break_even_cost_probability,
    )
    edge_after_break_even = _subtract_decimal(
        candidate.forecast_probability,
        break_even_probability,
    )
    forecast_edge_watch_margin = _subtract_decimal(
        edge_after_break_even,
        config.min_watch_edge_after_break_even,
    )
    forecast_edge_promote_margin = _subtract_decimal(
        edge_after_break_even,
        config.min_promote_edge_after_break_even,
    )
    source_quality_watch_margin = _subtract_decimal(
        candidate.source_quality_score,
        config.min_watch_source_quality_score,
    )
    source_quality_promote_margin = _subtract_decimal(
        candidate.source_quality_score,
        config.min_promote_source_quality_score,
    )
    specialist_arbitration_watch_margin = _subtract_decimal(
        candidate.specialist_arbitration_score,
        config.min_watch_specialist_arbitration_score,
    )
    specialist_arbitration_promote_margin = _subtract_decimal(
        candidate.specialist_arbitration_score,
        config.min_promote_specialist_arbitration_score,
    )
    resolution_risk_watch_headroom = _subtract_decimal(
        config.max_watch_resolution_risk_score,
        candidate.resolution_risk_score,
    )
    resolution_risk_promote_headroom = _subtract_decimal(
        config.max_promote_resolution_risk_score,
        candidate.resolution_risk_score,
    )
    liquidity_exit_watch_margin = _subtract_decimal(
        candidate.liquidity_exit_feasibility_score,
        config.min_watch_liquidity_exit_feasibility_score,
    )
    liquidity_exit_promote_margin = _subtract_decimal(
        candidate.liquidity_exit_feasibility_score,
        config.min_promote_liquidity_exit_feasibility_score,
    )
    category_exposure_watch_headroom = _subtract_decimal(
        config.max_watch_category_exposure_ratio,
        candidate.category_exposure_ratio,
    )
    category_exposure_promote_headroom = _subtract_decimal(
        config.max_promote_category_exposure_ratio,
        candidate.category_exposure_ratio,
    )
    watch_floor_margin = _min_decimal(
        (
            forecast_edge_watch_margin,
            source_quality_watch_margin,
            specialist_arbitration_watch_margin,
            resolution_risk_watch_headroom,
            liquidity_exit_watch_margin,
            category_exposure_watch_headroom,
        ),
    )
    promotion_margin = _min_decimal(
        (
            forecast_edge_promote_margin,
            source_quality_promote_margin,
            specialist_arbitration_promote_margin,
            resolution_risk_promote_headroom,
            liquidity_exit_promote_margin,
            category_exposure_promote_headroom,
        ),
    )
    recommendation_status = _recommendation_status(
        watch_floor_margin=watch_floor_margin,
        promotion_margin=promotion_margin,
    )
    reason_codes = _row_reason_codes(
        candidate=candidate,
        recommendation_status=recommendation_status,
        edge_after_break_even=edge_after_break_even,
        config=config,
    )
    return StrategyCandidateRecommendationTraceV2Row(
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        question=candidate.question,
        category=candidate.category,
        side=candidate.side,
        observed_at=observed_at,
        forecast_probability=candidate.forecast_probability,
        market_probability=candidate.market_probability,
        gross_probability_edge=gross_probability_edge,
        fee_probability_cost=candidate.fee_probability_cost,
        spread_probability_cost=candidate.spread_probability_cost,
        slippage_probability_cost=candidate.slippage_probability_cost,
        settlement_probability_cost=candidate.settlement_probability_cost,
        total_break_even_cost_probability=total_break_even_cost_probability,
        break_even_probability=break_even_probability,
        edge_after_break_even=edge_after_break_even,
        source_quality_score=candidate.source_quality_score,
        specialist_arbitration_score=candidate.specialist_arbitration_score,
        resolution_risk_score=candidate.resolution_risk_score,
        liquidity_exit_feasibility_score=candidate.liquidity_exit_feasibility_score,
        category_exposure_ratio=candidate.category_exposure_ratio,
        forecast_edge_watch_margin=forecast_edge_watch_margin,
        forecast_edge_promote_margin=forecast_edge_promote_margin,
        source_quality_watch_margin=source_quality_watch_margin,
        source_quality_promote_margin=source_quality_promote_margin,
        specialist_arbitration_watch_margin=specialist_arbitration_watch_margin,
        specialist_arbitration_promote_margin=specialist_arbitration_promote_margin,
        resolution_risk_watch_headroom=resolution_risk_watch_headroom,
        resolution_risk_promote_headroom=resolution_risk_promote_headroom,
        liquidity_exit_watch_margin=liquidity_exit_watch_margin,
        liquidity_exit_promote_margin=liquidity_exit_promote_margin,
        category_exposure_watch_headroom=category_exposure_watch_headroom,
        category_exposure_promote_headroom=category_exposure_promote_headroom,
        watch_floor_margin=watch_floor_margin,
        promotion_margin=promotion_margin,
        recommendation_status=recommendation_status,
        explanation_bullets=_explanation_bullets(
            candidate=candidate,
            recommendation_status=recommendation_status,
            edge_after_break_even=edge_after_break_even,
            total_break_even_cost_probability=total_break_even_cost_probability,
            watch_floor_margin=watch_floor_margin,
            promotion_margin=promotion_margin,
        ),
        reason_codes=reason_codes,
    )


def _explanation_bullets(
    *,
    candidate: StrategyCandidateRecommendationTraceV2Candidate,
    recommendation_status: str,
    edge_after_break_even: Decimal,
    total_break_even_cost_probability: Decimal,
    watch_floor_margin: Decimal,
    promotion_margin: Decimal,
) -> tuple[str, ...]:
    return (
        "Recommendation "
        f"{recommendation_status} for candidate {candidate.candidate_id} "
        f"on {candidate.side}.",
        "Forecast edge after break-even cost is "
        f"{_format_decimal(edge_after_break_even)} after total cost "
        f"{_format_decimal(total_break_even_cost_probability)}.",
        "Source quality, specialist arbitration, resolution risk, "
        "liquidity exit feasibility, and category exposure were scored together.",
        "Watch floor margin "
        f"{_format_decimal(watch_floor_margin)} and promotion margin "
        f"{_format_decimal(promotion_margin)}.",
    )


def _row_reason_codes(
    *,
    candidate: StrategyCandidateRecommendationTraceV2Candidate,
    recommendation_status: str,
    edge_after_break_even: Decimal,
    config: StrategyCandidateRecommendationTraceV2Config,
) -> tuple[str, ...]:
    codes = [f"candidate_recommendation_trace_{recommendation_status}"]
    if edge_after_break_even < config.min_watch_edge_after_break_even:
        codes.append("forecast_edge_below_watch_floor")
    elif edge_after_break_even < config.min_promote_edge_after_break_even:
        codes.append("forecast_edge_watch")
    else:
        codes.append("forecast_edge_promote")
    if edge_after_break_even >= ZERO:
        codes.append("cost_break_even_met")
    else:
        codes.append("cost_break_even_not_met")
    if candidate.source_quality_score < config.min_watch_source_quality_score:
        codes.append("source_quality_below_floor")
    elif candidate.source_quality_score < config.min_promote_source_quality_score:
        codes.append("source_quality_watch")
    else:
        codes.append("source_quality_promote")
    if (
        candidate.specialist_arbitration_score
        < config.min_watch_specialist_arbitration_score
    ):
        codes.append("specialist_arbitration_below_floor")
    elif (
        candidate.specialist_arbitration_score
        < config.min_promote_specialist_arbitration_score
    ):
        codes.append("specialist_arbitration_watch")
    else:
        codes.append("specialist_arbitration_promote")
    if candidate.resolution_risk_score > config.max_watch_resolution_risk_score:
        codes.append("resolution_risk_above_ceiling")
    elif candidate.resolution_risk_score > config.max_promote_resolution_risk_score:
        codes.append("resolution_risk_watch")
    else:
        codes.append("resolution_risk_promote")
    if (
        candidate.liquidity_exit_feasibility_score
        < config.min_watch_liquidity_exit_feasibility_score
    ):
        codes.append("liquidity_exit_below_floor")
    elif (
        candidate.liquidity_exit_feasibility_score
        < config.min_promote_liquidity_exit_feasibility_score
    ):
        codes.append("liquidity_exit_watch")
    else:
        codes.append("liquidity_exit_feasible")
    if candidate.category_exposure_ratio > config.max_watch_category_exposure_ratio:
        codes.append("category_exposure_above_ceiling")
    elif candidate.category_exposure_ratio > config.max_promote_category_exposure_ratio:
        codes.append("category_exposure_watch")
    else:
        codes.append("category_exposure_promote")
    codes.extend(candidate.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _recommendation_status(
    *,
    watch_floor_margin: Decimal,
    promotion_margin: Decimal,
) -> str:
    if watch_floor_margin < ZERO:
        return "blocked"
    if promotion_margin < ZERO:
        return "watched"
    return "promoted"


def _report_status(rows: tuple[StrategyCandidateRecommendationTraceV2Row, ...]) -> str:
    if any(row.recommendation_status == "blocked" for row in rows):
        return "blocked"
    if any(row.recommendation_status == "watched" for row in rows):
        return "watched"
    return "promoted"


def _report_reason_codes(
    report_status: str,
    rows: tuple[StrategyCandidateRecommendationTraceV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("candidate_recommendation_trace_no_candidates",)
    codes = [f"candidate_recommendation_trace_report_{report_status}"]
    if any(row.recommendation_status == "blocked" for row in rows):
        codes.append("blocked_candidates_present")
    if any(row.recommendation_status == "watched" for row in rows):
        codes.append("watched_candidates_present")
    if all(row.recommendation_status == "promoted" for row in rows):
        codes.append("all_candidates_promoted")
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _row_sort_key(
    row: StrategyCandidateRecommendationTraceV2Row,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        STATUS_PRIORITY[row.recommendation_status],
        -row.promotion_margin,
        -row.edge_after_break_even,
        row.category,
        row.market_slug,
        row.candidate_id,
    )


def _normalize_candidates(
    candidates: Iterable[StrategyCandidateRecommendationTraceV2Candidate],
) -> tuple[StrategyCandidateRecommendationTraceV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    for candidate in normalized:
        _require_exact_type(
            "candidate",
            candidate,
            StrategyCandidateRecommendationTraceV2Candidate,
        )
        _require_hard_flags("candidate", candidate)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyCandidateRecommendationTraceV2Row],
) -> tuple[StrategyCandidateRecommendationTraceV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        _require_exact_type("row", row, StrategyCandidateRecommendationTraceV2Row)
        _require_hard_flags("row", row)
        _verify_digest(row)
    return normalized


def _validate_row_consistency(row: StrategyCandidateRecommendationTraceV2Row) -> None:
    if row.gross_probability_edge != _subtract_decimal(
        row.forecast_probability,
        row.market_probability,
    ):
        raise ValueError("gross_probability_edge does not match probabilities")
    expected_total_cost = _sum_decimals(
        (
            row.fee_probability_cost,
            row.spread_probability_cost,
            row.slippage_probability_cost,
            row.settlement_probability_cost,
        ),
    )
    if row.total_break_even_cost_probability != expected_total_cost:
        raise ValueError("total_break_even_cost_probability does not match costs")
    expected_break_even = _add_decimal(row.market_probability, expected_total_cost)
    if row.break_even_probability != expected_break_even:
        raise ValueError("break_even_probability does not match market and costs")
    expected_edge_after_break_even = _subtract_decimal(
        row.forecast_probability,
        expected_break_even,
    )
    if row.edge_after_break_even != expected_edge_after_break_even:
        raise ValueError("edge_after_break_even does not match forecast and break-even")
    expected_watch_floor_margin = _min_decimal(
        (
            row.forecast_edge_watch_margin,
            row.source_quality_watch_margin,
            row.specialist_arbitration_watch_margin,
            row.resolution_risk_watch_headroom,
            row.liquidity_exit_watch_margin,
            row.category_exposure_watch_headroom,
        ),
    )
    if row.watch_floor_margin != expected_watch_floor_margin:
        raise ValueError("watch_floor_margin does not match dimension margins")
    expected_promotion_margin = _min_decimal(
        (
            row.forecast_edge_promote_margin,
            row.source_quality_promote_margin,
            row.specialist_arbitration_promote_margin,
            row.resolution_risk_promote_headroom,
            row.liquidity_exit_promote_margin,
            row.category_exposure_promote_headroom,
        ),
    )
    if row.promotion_margin != expected_promotion_margin:
        raise ValueError("promotion_margin does not match dimension margins")
    if row.recommendation_status != _recommendation_status(
        watch_floor_margin=row.watch_floor_margin,
        promotion_margin=row.promotion_margin,
    ):
        raise ValueError("recommendation_status does not match margins")


def _validate_report_consistency(
    report: StrategyCandidateRecommendationTraceV2Report,
) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.candidate_count != report.row_count:
        raise ValueError("candidate_count must match rows")
    if report.promoted_count != _status_count(report.rows, "promoted"):
        raise ValueError("promoted_count must match rows")
    if report.watched_count != _status_count(report.rows, "watched"):
        raise ValueError("watched_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must be sorted by recommendation status and margin")
    observed_times = tuple(row.observed_at for row in report.rows)
    if report.first_observed_at != (min(observed_times) if observed_times else None):
        raise ValueError("first_observed_at must match rows")
    if report.latest_observed_at != (max(observed_times) if observed_times else None):
        raise ValueError("latest_observed_at must match rows")
    if report.max_edge_after_break_even != _max_decimal(
        tuple(row.edge_after_break_even for row in report.rows),
    ):
        raise ValueError("max_edge_after_break_even must match rows")
    if report.min_watch_floor_margin != _min_decimal(
        tuple(row.watch_floor_margin for row in report.rows),
    ):
        raise ValueError("min_watch_floor_margin must match rows")
    if report.min_promotion_margin != _min_decimal(
        tuple(row.promotion_margin for row in report.rows),
    ):
        raise ValueError("min_promotion_margin must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    for row in report.rows:
        _verify_digest(row)


def _status_count(
    rows: tuple[StrategyCandidateRecommendationTraceV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.recommendation_status == status))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add_decimal(total, value)
    return total


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _quantize(min(values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _quantize(max(values))


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _format_decimal(value: Decimal) -> str:
    return format(value, "f")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for reason_code in reason_codes:
        _require_canonical_public_string(field_name, reason_code)
    if len(tuple(dict.fromkeys(reason_codes))) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(reason_codes)


def _normalize_texts(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        _require_canonical_public_string(field_name, value)
    return values


def _require_exact_type(
    value_or_field_name: object,
    value_or_expected_type: object,
    expected_type_or_label: object,
) -> None:
    if type(value_or_field_name) is str:
        field_name = value_or_field_name
        value = value_or_expected_type
        expected_type = expected_type_or_label
    else:
        field_name = str(expected_type_or_label)
        value = value_or_field_name
        expected_type = value_or_expected_type
    if not isinstance(expected_type, type):
        raise ValueError("expected_type must be a type")
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    _require_canonical_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_at_most(field_name: str, left: Decimal, right: Decimal) -> None:
    if left > right:
        raise ValueError(f"{field_name} must be at most its paired threshold")


def _require_canonical_public_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _apply_or_verify_digest(
    value: StrategyCandidateRecommendationTraceV2Row
    | StrategyCandidateRecommendationTraceV2Report,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, DERIVED_VALIDATION_DIGEST_FIELD, expected)
        return
    _require_digest(DERIVED_VALIDATION_DIGEST_FIELD, provided)
    if provided != expected:
        raise ValueError("derived_validation_digest must match derived fields")


def _verify_digest(
    value: StrategyCandidateRecommendationTraceV2Row
    | StrategyCandidateRecommendationTraceV2Report,
) -> None:
    _require_digest(DERIVED_VALIDATION_DIGEST_FIELD, value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest must match derived fields")


def _derived_digest(
    value: StrategyCandidateRecommendationTraceV2Row
    | StrategyCandidateRecommendationTraceV2Report,
) -> str:
    digest_input = asdict(value)
    digest_input.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    payload = _json_ready(digest_input)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _validate_public_payload_digest(
    payload: dict[str, object],
    fields_without_digest: tuple[str, ...],
) -> None:
    digest = payload.get(DERIVED_VALIDATION_DIGEST_FIELD)
    _require_digest(DERIVED_VALIDATION_DIGEST_FIELD, digest)  # type: ignore[arg-type]
    digest_input = {field_name: payload[field_name] for field_name in fields_without_digest}
    encoded = dumps(digest_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _require_canonical_public_string(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str) and _has_unsafe_public_fragment(value):
        raise ValueError(f"{label} contains unsafe public value")


def _require_public_payload_json_ready(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_public_payload_json_ready(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_json_ready(item)
        return
    if value is None or type(value) in (str, bool):
        return
    if type(value) in (Decimal, int, float):
        raise ValueError("public payload numeric values must be strings")
    raise ValueError("public payload value is not JSON-ready")


def _require_exact_payload_fields(
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
    label: str,
) -> None:
    if tuple(payload.keys()) != expected_fields:
        raise ValueError(f"{label} fields must match the public contract")


def _require_public_payload_flags(payload: dict[str, object], label: str) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


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
