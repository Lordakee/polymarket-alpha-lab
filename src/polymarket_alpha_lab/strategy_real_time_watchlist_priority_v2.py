"""Decimal-only paper report for real-time watchlist priority candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
import hashlib
from typing import Any


__all__ = (
    "StrategyRealTimeWatchlistPriorityV2Candidate",
    "StrategyRealTimeWatchlistPriorityV2Config",
    "StrategyRealTimeWatchlistPriorityV2Report",
    "StrategyRealTimeWatchlistPriorityV2Row",
    "build_strategy_real_time_watchlist_priority_v2_report",
    "strategy_real_time_watchlist_priority_v2_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-real-time-watchlist-priority-v2-v0"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PRIORITY_STATUSES = ("priority_review", "watch", "defer", "blocked")
REPORT_STATUSES = ("empty_watchlist", *PRIORITY_STATUSES)
STATUS_REASON_PREFIX = "strategy_real_time_watchlist_priority_v2_"
PUBLIC_ROW_FIELDS = (
    "priority_rank",
    "candidate_id",
    "market_slug",
    "outcome_name",
    "priority_status",
    "priority_score",
    "cost_adjusted_edge",
    "probability_movement",
    "absolute_probability_movement",
    "information_staleness_score",
    "source_contradiction_score",
    "exit_liquidity_feasibility",
    "resolution_horizon_score",
    "specialist_uncertainty_score",
    "model_probability",
    "market_probability",
    "previous_market_probability",
    "estimated_cost",
    "information_age_seconds",
    "exit_liquidity_notional",
    "candidate_notional",
    "hours_to_resolution",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "report_status",
    "candidate_count",
    "priority_review_count",
    "watch_count",
    "defer_count",
    "blocked_count",
    "top_priority_score",
    "top_cost_adjusted_edge",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_PAYLOAD_FIELDS = (
    *PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
UNSAFE_PUBLIC_TEXT_TOKENS = (
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
class StrategyRealTimeWatchlistPriorityV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    minimum_priority_score: Decimal = Decimal("0.100000")
    minimum_cost_adjusted_edge: Decimal = Decimal("0.010000")
    minimum_exit_liquidity_feasibility: Decimal = Decimal("0.500000")
    maximum_specialist_uncertainty: Decimal = Decimal("0.700000")
    maximum_information_age_seconds: Decimal = Decimal("3600.000000")
    near_resolution_horizon_hours: Decimal = Decimal("24.000000")
    probability_movement_weight: Decimal = Decimal("0.500000")
    information_staleness_weight: Decimal = Decimal("0.100000")
    source_contradiction_weight: Decimal = Decimal("0.200000")
    liquidity_exit_feasibility_weight: Decimal = Decimal("0.300000")
    resolution_horizon_weight: Decimal = Decimal("0.100000")
    specialist_uncertainty_weight: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRealTimeWatchlistPriorityV2Config:
            raise TypeError(
                "StrategyRealTimeWatchlistPriorityV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRealTimeWatchlistPriorityV2Config:
            raise ValueError(
                "config must be exactly StrategyRealTimeWatchlistPriorityV2Config",
            )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_priority_score",
            "minimum_cost_adjusted_edge",
            "minimum_exit_liquidity_feasibility",
            "maximum_specialist_uncertainty",
            "probability_movement_weight",
            "information_staleness_weight",
            "source_contradiction_weight",
            "liquidity_exit_feasibility_weight",
            "resolution_horizon_weight",
            "specialist_uncertainty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_exit_liquidity_feasibility",
            "maximum_specialist_uncertainty",
        ):
            if getattr(self, field_name) > ONE:
                raise ValueError(f"{field_name} must be a probability")
        for field_name in (
            "maximum_information_age_seconds",
            "near_resolution_horizon_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyRealTimeWatchlistPriorityV2Candidate:
    candidate_id: str
    market_slug: str
    outcome_name: str
    model_probability: Decimal
    market_probability: Decimal
    previous_market_probability: Decimal
    estimated_cost: Decimal
    information_age_seconds: Decimal
    source_contradiction_score: Decimal
    exit_liquidity_notional: Decimal
    candidate_notional: Decimal
    hours_to_resolution: Decimal
    specialist_uncertainty_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRealTimeWatchlistPriorityV2Candidate:
            raise TypeError(
                "StrategyRealTimeWatchlistPriorityV2Candidate "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRealTimeWatchlistPriorityV2Candidate:
            raise ValueError(
                "candidate must be exactly StrategyRealTimeWatchlistPriorityV2Candidate",
            )
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "model_probability",
            "market_probability",
            "previous_market_probability",
            "source_contradiction_score",
            "specialist_uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "estimated_cost",
            "information_age_seconds",
            "exit_liquidity_notional",
            "hours_to_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "candidate_notional",
            _normalize_positive_decimal("candidate_notional", self.candidate_notional),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("candidate", self)
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyRealTimeWatchlistPriorityV2Row:
    priority_rank: Decimal
    candidate_id: str
    market_slug: str
    outcome_name: str
    priority_status: str
    priority_score: Decimal
    cost_adjusted_edge: Decimal
    probability_movement: Decimal
    absolute_probability_movement: Decimal
    information_staleness_score: Decimal
    source_contradiction_score: Decimal
    exit_liquidity_feasibility: Decimal
    resolution_horizon_score: Decimal
    specialist_uncertainty_score: Decimal
    model_probability: Decimal
    market_probability: Decimal
    previous_market_probability: Decimal
    estimated_cost: Decimal
    information_age_seconds: Decimal
    exit_liquidity_notional: Decimal
    candidate_notional: Decimal
    hours_to_resolution: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyRealTimeWatchlistPriorityV2Row:
            raise ValueError("row must be exactly StrategyRealTimeWatchlistPriorityV2Row")
        object.__setattr__(
            self,
            "priority_rank",
            _normalize_positive_whole_decimal("priority_rank", self.priority_rank),
        )
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("priority_status", self.priority_status, PRIORITY_STATUSES)
        for field_name in (
            "priority_score",
            "cost_adjusted_edge",
            "probability_movement",
        ):
            object.__setattr__(
                self,
                field_name,
                _quantize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "absolute_probability_movement",
            "information_staleness_score",
            "source_contradiction_score",
            "exit_liquidity_feasibility",
            "resolution_horizon_score",
            "specialist_uncertainty_score",
            "model_probability",
            "market_probability",
            "previous_market_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "estimated_cost",
            "information_age_seconds",
            "exit_liquidity_notional",
            "hours_to_resolution",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "candidate_notional",
            _normalize_positive_decimal("candidate_notional", self.candidate_notional),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyRealTimeWatchlistPriorityV2Report:
    config_version: str
    report_status: str
    candidate_count: Decimal
    priority_review_count: Decimal
    watch_count: Decimal
    defer_count: Decimal
    blocked_count: Decimal
    top_priority_score: Decimal
    top_cost_adjusted_edge: Decimal
    rows: tuple[StrategyRealTimeWatchlistPriorityV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyRealTimeWatchlistPriorityV2Report:
            raise TypeError(
                "StrategyRealTimeWatchlistPriorityV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyRealTimeWatchlistPriorityV2Report:
            raise ValueError(
                "report must be exactly StrategyRealTimeWatchlistPriorityV2Report",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "candidate_count",
            "priority_review_count",
            "watch_count",
            "defer_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("top_priority_score", "top_cost_adjusted_edge"):
            object.__setattr__(
                self,
                field_name,
                _quantize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows("rows", self.rows))
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _normalize_sha256(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)
        _validate_report_consistency(self)


def build_strategy_real_time_watchlist_priority_v2_report(
    candidates: object,
    *,
    config: StrategyRealTimeWatchlistPriorityV2Config,
) -> StrategyRealTimeWatchlistPriorityV2Report:
    """Build a pure report-only priority view for candidate review."""

    _require_exact_type("config", config, StrategyRealTimeWatchlistPriorityV2Config)
    candidate_inputs = _normalize_candidates(candidates)
    rows_without_rank = tuple(_row_for_candidate(candidate, config) for candidate in candidate_inputs)
    sorted_rows = sorted(
        rows_without_rank,
        key=lambda row: (
            row.priority_score,
            row.cost_adjusted_edge,
            row.absolute_probability_movement,
            row.exit_liquidity_feasibility,
            row.resolution_horizon_score,
            row.candidate_id,
        ),
        reverse=True,
    )
    rows = tuple(
        _ranked_row(row, Decimal(index + 1).quantize(QUANTUM))
        for index, row in enumerate(sorted_rows)
    )
    status_counts = _status_counts(rows)
    return StrategyRealTimeWatchlistPriorityV2Report(
        config_version=config.config_version,
        report_status=_report_status(rows),
        candidate_count=_whole_decimal(len(rows)),
        priority_review_count=_whole_decimal(status_counts["priority_review"]),
        watch_count=_whole_decimal(status_counts["watch"]),
        defer_count=_whole_decimal(status_counts["defer"]),
        blocked_count=_whole_decimal(status_counts["blocked"]),
        top_priority_score=rows[0].priority_score if rows else ZERO,
        top_cost_adjusted_edge=rows[0].cost_adjusted_edge if rows else ZERO,
        rows=rows,
    )


def strategy_real_time_watchlist_priority_v2_payload(
    report: StrategyRealTimeWatchlistPriorityV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is StrategyRealTimeWatchlistPriorityV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_public_payload_fields(report)
        _validate_public_payload(report)
        return dict(report)
    raise ValueError("report must be a StrategyRealTimeWatchlistPriorityV2Report")


def _normalize_candidates(candidates: object) -> tuple[StrategyRealTimeWatchlistPriorityV2Candidate, ...]:
    if isinstance(candidates, (str, bytes)) or not hasattr(candidates, "__iter__"):
        raise ValueError("candidates must be an iterable")
    normalized: list[StrategyRealTimeWatchlistPriorityV2Candidate] = []
    for candidate in candidates:
        _require_exact_type(
            "candidate",
            candidate,
            StrategyRealTimeWatchlistPriorityV2Candidate,
        )
        normalized.append(candidate)
    return tuple(normalized)


def _row_for_candidate(
    candidate: StrategyRealTimeWatchlistPriorityV2Candidate,
    config: StrategyRealTimeWatchlistPriorityV2Config,
) -> StrategyRealTimeWatchlistPriorityV2Row:
    cost_adjusted_edge = _quantize_decimal(
        "cost_adjusted_edge",
        candidate.model_probability - candidate.market_probability - candidate.estimated_cost,
    )
    probability_movement = _quantize_decimal(
        "probability_movement",
        candidate.market_probability - candidate.previous_market_probability,
    )
    absolute_probability_movement = abs(probability_movement).quantize(QUANTUM)
    information_staleness_score = _capped_ratio(
        candidate.information_age_seconds,
        config.maximum_information_age_seconds,
    )
    exit_liquidity_feasibility = _capped_ratio(
        candidate.exit_liquidity_notional,
        candidate.candidate_notional,
    )
    resolution_horizon_score = _resolution_horizon_score(
        candidate.hours_to_resolution,
        config.near_resolution_horizon_hours,
    )
    priority_score = _priority_score(
        cost_adjusted_edge=cost_adjusted_edge,
        absolute_probability_movement=absolute_probability_movement,
        information_staleness_score=information_staleness_score,
        source_contradiction_score=candidate.source_contradiction_score,
        exit_liquidity_feasibility=exit_liquidity_feasibility,
        resolution_horizon_score=resolution_horizon_score,
        specialist_uncertainty_score=candidate.specialist_uncertainty_score,
        config=config,
    )
    priority_status = _priority_status(
        cost_adjusted_edge=cost_adjusted_edge,
        priority_score=priority_score,
        information_age_seconds=candidate.information_age_seconds,
        exit_liquidity_feasibility=exit_liquidity_feasibility,
        specialist_uncertainty_score=candidate.specialist_uncertainty_score,
        config=config,
    )
    return StrategyRealTimeWatchlistPriorityV2Row(
        priority_rank=ONE,
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        outcome_name=candidate.outcome_name,
        priority_status=priority_status,
        priority_score=priority_score,
        cost_adjusted_edge=cost_adjusted_edge,
        probability_movement=probability_movement,
        absolute_probability_movement=absolute_probability_movement,
        information_staleness_score=information_staleness_score,
        source_contradiction_score=candidate.source_contradiction_score,
        exit_liquidity_feasibility=exit_liquidity_feasibility,
        resolution_horizon_score=resolution_horizon_score,
        specialist_uncertainty_score=candidate.specialist_uncertainty_score,
        model_probability=candidate.model_probability,
        market_probability=candidate.market_probability,
        previous_market_probability=candidate.previous_market_probability,
        estimated_cost=candidate.estimated_cost,
        information_age_seconds=candidate.information_age_seconds,
        exit_liquidity_notional=candidate.exit_liquidity_notional,
        candidate_notional=candidate.candidate_notional,
        hours_to_resolution=candidate.hours_to_resolution,
        reason_codes=_row_reason_codes(
            priority_status,
            cost_adjusted_edge=cost_adjusted_edge,
            absolute_probability_movement=absolute_probability_movement,
            information_staleness_score=information_staleness_score,
            source_contradiction_score=candidate.source_contradiction_score,
            exit_liquidity_feasibility=exit_liquidity_feasibility,
            resolution_horizon_score=resolution_horizon_score,
            specialist_uncertainty_score=candidate.specialist_uncertainty_score,
            config=config,
            upstream_reason_codes=candidate.reason_codes,
        ),
    )


def _ranked_row(
    row: StrategyRealTimeWatchlistPriorityV2Row,
    priority_rank: Decimal,
) -> StrategyRealTimeWatchlistPriorityV2Row:
    return StrategyRealTimeWatchlistPriorityV2Row(
        priority_rank=priority_rank,
        candidate_id=row.candidate_id,
        market_slug=row.market_slug,
        outcome_name=row.outcome_name,
        priority_status=row.priority_status,
        priority_score=row.priority_score,
        cost_adjusted_edge=row.cost_adjusted_edge,
        probability_movement=row.probability_movement,
        absolute_probability_movement=row.absolute_probability_movement,
        information_staleness_score=row.information_staleness_score,
        source_contradiction_score=row.source_contradiction_score,
        exit_liquidity_feasibility=row.exit_liquidity_feasibility,
        resolution_horizon_score=row.resolution_horizon_score,
        specialist_uncertainty_score=row.specialist_uncertainty_score,
        model_probability=row.model_probability,
        market_probability=row.market_probability,
        previous_market_probability=row.previous_market_probability,
        estimated_cost=row.estimated_cost,
        information_age_seconds=row.information_age_seconds,
        exit_liquidity_notional=row.exit_liquidity_notional,
        candidate_notional=row.candidate_notional,
        hours_to_resolution=row.hours_to_resolution,
        reason_codes=row.reason_codes,
    )


def _priority_score(
    *,
    cost_adjusted_edge: Decimal,
    absolute_probability_movement: Decimal,
    information_staleness_score: Decimal,
    source_contradiction_score: Decimal,
    exit_liquidity_feasibility: Decimal,
    resolution_horizon_score: Decimal,
    specialist_uncertainty_score: Decimal,
    config: StrategyRealTimeWatchlistPriorityV2Config,
) -> Decimal:
    score = (
        cost_adjusted_edge
        + (absolute_probability_movement * config.probability_movement_weight)
        + (information_staleness_score * config.information_staleness_weight)
        + (source_contradiction_score * config.source_contradiction_weight)
        + (exit_liquidity_feasibility * config.liquidity_exit_feasibility_weight)
        + (resolution_horizon_score * config.resolution_horizon_weight)
        - (specialist_uncertainty_score * config.specialist_uncertainty_weight)
    )
    return score.quantize(QUANTUM)


def _priority_status(
    *,
    cost_adjusted_edge: Decimal,
    priority_score: Decimal,
    information_age_seconds: Decimal,
    exit_liquidity_feasibility: Decimal,
    specialist_uncertainty_score: Decimal,
    config: StrategyRealTimeWatchlistPriorityV2Config,
) -> str:
    if cost_adjusted_edge < config.minimum_cost_adjusted_edge:
        return "blocked"
    if exit_liquidity_feasibility < config.minimum_exit_liquidity_feasibility:
        return "blocked"
    if specialist_uncertainty_score > config.maximum_specialist_uncertainty:
        return "blocked"
    if information_age_seconds > config.maximum_information_age_seconds:
        return "defer"
    if priority_score >= config.minimum_priority_score:
        return "priority_review"
    return "watch"


def _row_reason_codes(
    priority_status: str,
    *,
    cost_adjusted_edge: Decimal,
    absolute_probability_movement: Decimal,
    information_staleness_score: Decimal,
    source_contradiction_score: Decimal,
    exit_liquidity_feasibility: Decimal,
    resolution_horizon_score: Decimal,
    specialist_uncertainty_score: Decimal,
    config: StrategyRealTimeWatchlistPriorityV2Config,
    upstream_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = [
        f"{STATUS_REASON_PREFIX}{priority_status}",
        (
            "cost_adjusted_edge_positive"
            if cost_adjusted_edge > ZERO
            else "cost_adjusted_edge_nonpositive"
        ),
        (
            "probability_movement_observed"
            if absolute_probability_movement > ZERO
            else "probability_movement_flat"
        ),
        (
            "information_staleness_observed"
            if information_staleness_score > ZERO
            else "information_fresh"
        ),
        (
            "source_contradiction_observed"
            if source_contradiction_score > ZERO
            else "source_contradiction_absent"
        ),
        (
            "exit_feasibility_ready"
            if exit_liquidity_feasibility >= config.minimum_exit_liquidity_feasibility
            else "exit_feasibility_insufficient"
        ),
        (
            "resolution_horizon_near"
            if resolution_horizon_score > ZERO
            else "resolution_horizon_distant"
        ),
        (
            "specialist_uncertainty_observed"
            if specialist_uncertainty_score > ZERO
            else "specialist_uncertainty_absent"
        ),
        *upstream_reason_codes,
    ]
    return tuple(dict.fromkeys(reason_codes))


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    ratio = numerator / denominator
    if ratio > ONE:
        return ONE
    return ratio.quantize(QUANTUM)


def _resolution_horizon_score(hours_to_resolution: Decimal, near_horizon: Decimal) -> Decimal:
    if hours_to_resolution >= near_horizon:
        return ZERO
    return ((near_horizon - hours_to_resolution) / near_horizon).quantize(QUANTUM)


def _status_counts(rows: tuple[StrategyRealTimeWatchlistPriorityV2Row, ...]) -> dict[str, int]:
    counts = {status: 0 for status in PRIORITY_STATUSES}
    for row in rows:
        counts[row.priority_status] += 1
    return counts


def _report_status(rows: tuple[StrategyRealTimeWatchlistPriorityV2Row, ...]) -> str:
    if not rows:
        return "empty_watchlist"
    for status in PRIORITY_STATUSES:
        if any(row.priority_status == status for row in rows):
            return status
    raise ValueError("rows must contain a known priority status")


def _report_public_payload_values(
    report: StrategyRealTimeWatchlistPriorityV2Report,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "report_status": report.report_status,
        "candidate_count": _decimal_payload(report.candidate_count),
        "priority_review_count": _decimal_payload(report.priority_review_count),
        "watch_count": _decimal_payload(report.watch_count),
        "defer_count": _decimal_payload(report.defer_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "top_priority_score": _decimal_payload(report.top_priority_score),
        "top_cost_adjusted_edge": _decimal_payload(report.top_cost_adjusted_edge),
        "rows": [_row_public_payload_values(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload_values(row: StrategyRealTimeWatchlistPriorityV2Row) -> dict[str, object]:
    return {
        "priority_rank": _decimal_payload(row.priority_rank),
        "candidate_id": row.candidate_id,
        "market_slug": row.market_slug,
        "outcome_name": row.outcome_name,
        "priority_status": row.priority_status,
        "priority_score": _decimal_payload(row.priority_score),
        "cost_adjusted_edge": _decimal_payload(row.cost_adjusted_edge),
        "probability_movement": _decimal_payload(row.probability_movement),
        "absolute_probability_movement": _decimal_payload(
            row.absolute_probability_movement,
        ),
        "information_staleness_score": _decimal_payload(row.information_staleness_score),
        "source_contradiction_score": _decimal_payload(row.source_contradiction_score),
        "exit_liquidity_feasibility": _decimal_payload(row.exit_liquidity_feasibility),
        "resolution_horizon_score": _decimal_payload(row.resolution_horizon_score),
        "specialist_uncertainty_score": _decimal_payload(
            row.specialist_uncertainty_score,
        ),
        "model_probability": _decimal_payload(row.model_probability),
        "market_probability": _decimal_payload(row.market_probability),
        "previous_market_probability": _decimal_payload(row.previous_market_probability),
        "estimated_cost": _decimal_payload(row.estimated_cost),
        "information_age_seconds": _decimal_payload(row.information_age_seconds),
        "exit_liquidity_notional": _decimal_payload(row.exit_liquidity_notional),
        "candidate_notional": _decimal_payload(row.candidate_notional),
        "hours_to_resolution": _decimal_payload(row.hours_to_resolution),
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_derived_validation_digest(
    report: StrategyRealTimeWatchlistPriorityV2Report,
) -> str:
    return _derived_validation_digest(_report_public_payload_values(report))


def _validate_report_derived_validation_digest(
    report: StrategyRealTimeWatchlistPriorityV2Report,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(payload: dict[str, object]) -> str:
    values = tuple(
        f"{field_name}={_digest_payload_value(payload[field_name])}"
        for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
    )
    return _sha256("strategy_real_time_watchlist_priority_v2_derived", values)


def _digest_payload_value(value: object) -> str:
    if isinstance(value, dict):
        return "{" + ",".join(
            f"{key}:{_digest_payload_value(value[key])}" for key in sorted(value)
        ) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_digest_payload_value(item) for item in value) + "]"
    return str(value)


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _require_public_payload_fields(payload: dict[str, object]) -> None:
    for field_name in PUBLIC_PAYLOAD_FIELDS:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    extra_fields = sorted(set(payload) - set(PUBLIC_PAYLOAD_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _validate_public_payload(payload: dict[str, object]) -> None:
    _require_canonical_string("config_version", payload["config_version"])
    _require_member("report_status", payload["report_status"], REPORT_STATUSES)
    for field_name in (
        "candidate_count",
        "priority_review_count",
        "watch_count",
        "defer_count",
        "blocked_count",
    ):
        _require_decimal_payload_string(field_name, payload[field_name], whole=True)
    for field_name in ("top_priority_score", "top_cost_adjusted_edge"):
        _require_decimal_payload_string(field_name, payload[field_name], signed=True)
    rows = _validate_public_rows(payload["rows"])
    _require_hard_flags("payload", _DictFlags(payload))
    provided_digest = _normalize_sha256(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    if provided_digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload fields")
    if payload["report_status"] == "empty_watchlist" and rows:
        raise ValueError("empty_watchlist report must not include rows")


def _validate_public_rows(value: object) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[dict[str, object]] = []
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_public_row_fields(row)
        _validate_public_row(row)
        rows.append(row)
    return tuple(rows)


def _require_public_row_fields(row: dict[str, object]) -> None:
    for field_name in PUBLIC_ROW_FIELDS:
        if field_name not in row:
            raise ValueError(f"rows.{field_name} is required")
    extra_fields = sorted(set(row) - set(PUBLIC_ROW_FIELDS))
    if extra_fields:
        raise ValueError(f"unexpected public row field: {extra_fields[0]}")


def _validate_public_row(row: dict[str, object]) -> None:
    for field_name in ("candidate_id", "market_slug", "outcome_name"):
        _require_canonical_string(field_name, row[field_name])
    _require_member("priority_status", row["priority_status"], PRIORITY_STATUSES)
    _require_decimal_payload_string("priority_rank", row["priority_rank"], whole=True)
    for field_name in (
        "priority_score",
        "cost_adjusted_edge",
        "probability_movement",
    ):
        _require_decimal_payload_string(field_name, row[field_name], signed=True)
    for field_name in (
        "absolute_probability_movement",
        "information_staleness_score",
        "source_contradiction_score",
        "exit_liquidity_feasibility",
        "resolution_horizon_score",
        "specialist_uncertainty_score",
        "model_probability",
        "market_probability",
        "previous_market_probability",
    ):
        _require_decimal_payload_string(field_name, row[field_name], probability=True)
    for field_name in (
        "estimated_cost",
        "information_age_seconds",
        "exit_liquidity_notional",
        "candidate_notional",
        "hours_to_resolution",
    ):
        _require_decimal_payload_string(field_name, row[field_name])
    reason_codes = _normalize_public_reason_codes("reason_codes", row["reason_codes"])
    _require_hard_flags("row", _DictFlags(row))
    expected_reason_code = f"{STATUS_REASON_PREFIX}{row['priority_status']}"
    if not reason_codes or reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with priority_status reason code")


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    reason_codes: list[str] = []
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
        reason_codes.append(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return tuple(reason_codes)


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    probability: bool = False,
    whole: bool = False,
    signed: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = decimal_value.quantize(QUANTUM)
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    if not signed and normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if probability and (normalized < ZERO or normalized > ONE):
        raise ValueError(f"{field_name} must be a probability")
    if whole and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal-derived string")
    return normalized


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _validate_row_consistency(row: StrategyRealTimeWatchlistPriorityV2Row) -> None:
    expected_reason_code = f"{STATUS_REASON_PREFIX}{row.priority_status}"
    if not row.reason_codes or row.reason_codes[0] != expected_reason_code:
        raise ValueError("reason_codes must start with priority_status reason code")


def _validate_report_consistency(report: StrategyRealTimeWatchlistPriorityV2Report) -> None:
    status_counts = _status_counts(report.rows)
    if report.candidate_count != _whole_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.priority_review_count != _whole_decimal(status_counts["priority_review"]):
        raise ValueError("priority_review_count must match rows")
    if report.watch_count != _whole_decimal(status_counts["watch"]):
        raise ValueError("watch_count must match rows")
    if report.defer_count != _whole_decimal(status_counts["defer"]):
        raise ValueError("defer_count must match rows")
    if report.blocked_count != _whole_decimal(status_counts["blocked"]):
        raise ValueError("blocked_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    top_priority_score = report.rows[0].priority_score if report.rows else ZERO
    top_cost_adjusted_edge = report.rows[0].cost_adjusted_edge if report.rows else ZERO
    if report.top_priority_score != top_priority_score:
        raise ValueError("top_priority_score must match rows")
    if report.top_cost_adjusted_edge != top_cost_adjusted_edge:
        raise ValueError("top_cost_adjusted_edge must match rows")


def _normalize_rows(
    field_name: str,
    value: object,
) -> tuple[StrategyRealTimeWatchlistPriorityV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for row in value:
        _require_exact_type("row", row, StrategyRealTimeWatchlistPriorityV2Row)
    return value


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_hard_flags(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        expected = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _whole_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 string")
    return value


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _is_unsafe_public_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _is_unsafe_public_text(key):
                raise ValueError(f"unsafe field in {label}: {item_path}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)


def _is_unsafe_public_text(value: str) -> bool:
    tokens = _surface_text_tokens(value.lower())
    return any(token in UNSAFE_PUBLIC_TEXT_TOKENS for token in tokens)


def _surface_text_tokens(value: str) -> tuple[str, ...]:
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
