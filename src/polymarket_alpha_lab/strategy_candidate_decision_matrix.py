"""Paper-only strategy candidate decision matrix reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Iterable


__all__ = (
    "PaperStrategyCandidateDecisionInput",
    "PaperStrategyCandidateDecisionMatrixConfig",
    "PaperStrategyCandidateDecisionMatrixReport",
    "PaperStrategyCandidateDecisionRow",
    "build_paper_strategy_candidate_decision_matrix_report",
)


ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_ONE = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT_PRECISION = 28
BASE_SCORE_PENALTY = Decimal("0.012500")

DECISION_STATUSES = ("candidate", "research", "watch", "blocked")
ACTIONS = (
    "select_for_manual_review",
    "refresh_information",
    "escalate_specialist_review",
    "watch",
    "reject",
)
STATUS_RANK = {"candidate": 0, "research": 1, "watch": 2, "blocked": 3}


@dataclass(frozen=True)
class PaperStrategyCandidateDecisionMatrixConfig:
    config_version: str
    min_candidate_score: Decimal = Decimal("0.700000")
    min_research_score: Decimal = Decimal("0.450000")
    min_net_edge_per_share: Decimal = Decimal("0.030000")
    min_information_quality_score: Decimal = Decimal("0.650000")
    min_liquidity_score: Decimal = Decimal("0.500000")
    max_total_cost_per_share: Decimal = Decimal("0.040000")
    max_resolution_risk_score: Decimal = Decimal("0.350000")
    min_team_memory_score: Decimal = Decimal("0.400000")
    min_calibration_score: Decimal = Decimal("0.400000")
    min_source_count: Decimal = Decimal("2")
    max_freshness_minutes: Decimal = Decimal("120")
    edge_weight: Decimal = Decimal("0.300000")
    information_quality_weight: Decimal = Decimal("0.250000")
    cost_weight: Decimal = Decimal("0.150000")
    liquidity_weight: Decimal = Decimal("0.120000")
    resolution_risk_weight: Decimal = Decimal("0.100000")
    team_memory_weight: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_candidate_score",
            "min_research_score",
            "min_information_quality_score",
            "min_liquidity_score",
            "max_resolution_risk_score",
            "min_team_memory_score",
            "min_calibration_score",
            "edge_weight",
            "information_quality_weight",
            "cost_weight",
            "liquidity_weight",
            "resolution_risk_weight",
            "team_memory_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_net_edge_per_share",
            "max_total_cost_per_share",
            "min_source_count",
            "max_freshness_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_research_score > self.min_candidate_score:
            raise ValueError("min_research_score must not exceed min_candidate_score")
        if self.min_source_count <= ZERO:
            raise ValueError("min_source_count must be positive")
        if self.max_freshness_minutes <= ZERO:
            raise ValueError("max_freshness_minutes must be positive")
        if self.min_net_edge_per_share <= ZERO:
            raise ValueError("min_net_edge_per_share must be positive")
        _validate_weight_total(self)
        _validate_hard_flags(self)


@dataclass(frozen=True)
class PaperStrategyCandidateDecisionInput:
    market_slug: str
    question: str
    team_id: str
    category: str
    forecast_probability: Decimal
    market_probability: Decimal
    net_edge_per_share: Decimal
    total_cost_per_share: Decimal
    liquidity_score: Decimal
    information_quality_score: Decimal
    source_count: Decimal
    freshness_minutes: Decimal
    resolution_risk_score: Decimal
    team_memory_score: Decimal
    calibration_score: Decimal
    reason_codes: tuple[str, ...] = ()
    evidence_gap_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("market_slug", "question", "team_id", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "liquidity_score",
            "information_quality_score",
            "resolution_risk_score",
            "team_memory_score",
            "calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "net_edge_per_share",
            "total_cost_per_share",
            "source_count",
            "freshness_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_string_tuple("evidence_gap_codes", self.evidence_gap_codes),
        )
        _validate_hard_flags(self)


@dataclass(frozen=True)
class PaperStrategyCandidateDecisionRow:
    rank: Decimal
    market_slug: str
    question: str
    team_id: str
    category: str
    decision_status: str
    action: str
    forecast_probability: Decimal
    market_probability: Decimal
    net_edge_per_share: Decimal
    total_cost_per_share: Decimal
    cost_adjusted_edge: Decimal
    liquidity_score: Decimal
    information_quality_score: Decimal
    source_count: Decimal
    freshness_minutes: Decimal
    resolution_risk_score: Decimal
    team_memory_score: Decimal
    calibration_score: Decimal
    composite_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_nonnegative_decimal("rank", self.rank))
        if self.rank <= ZERO:
            raise ValueError("rank must be positive")
        for field_name in ("market_slug", "question", "team_id", "category"):
            _require_canonical_string(field_name, getattr(self, field_name))
        if type(self.decision_status) is not str or self.decision_status not in DECISION_STATUSES:
            raise ValueError("decision_status must be candidate, research, watch, or blocked")
        if type(self.action) is not str or self.action not in ACTIONS:
            raise ValueError("action must be a known decision action")
        for field_name in (
            "forecast_probability",
            "market_probability",
            "liquidity_score",
            "information_quality_score",
            "resolution_risk_score",
            "team_memory_score",
            "calibration_score",
            "composite_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "net_edge_per_share",
            "total_cost_per_share",
            "source_count",
            "freshness_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_decimal("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        _validate_row_action_semantics(self)
        _validate_hard_flags(self)


@dataclass(frozen=True)
class PaperStrategyCandidateDecisionMatrixReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    select_count: Decimal
    research_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    decision_rows: tuple[PaperStrategyCandidateDecisionRow, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "select_count",
            "research_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "decision_rows", _normalize_rows(self.decision_rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _validate_hard_flags(self)


def build_paper_strategy_candidate_decision_matrix_report(
    candidates: Iterable[PaperStrategyCandidateDecisionInput],
    *,
    config: PaperStrategyCandidateDecisionMatrixConfig,
    generated_at: datetime,
) -> PaperStrategyCandidateDecisionMatrixReport:
    """Rank paper candidates for operator review; never creates live orders."""

    if type(config) is not PaperStrategyCandidateDecisionMatrixConfig:
        raise ValueError("config must be a PaperStrategyCandidateDecisionMatrixConfig")
    _validate_hard_flags(config)
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    normalized_candidates = _normalize_inputs(candidates)
    unranked_rows = tuple(
        _decision_row(candidate=candidate, config=config, rank=COUNT_ONE)
        for candidate in normalized_candidates
    )
    ordered_rows = tuple(
        PaperStrategyCandidateDecisionRow(
            **{
                **row.__dict__,
                "rank": _count(index),
            },
        )
        for index, row in enumerate(_order_rows(unranked_rows), start=1)
    )
    return PaperStrategyCandidateDecisionMatrixReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count(len(ordered_rows)),
        select_count=_status_count(ordered_rows, "candidate"),
        research_count=_status_count(ordered_rows, "research"),
        watch_count=_status_count(ordered_rows, "watch"),
        blocked_count=_status_count(ordered_rows, "blocked"),
        decision_rows=ordered_rows,
        reason_code_counts=_reason_code_counts(ordered_rows),
    )


def _decision_row(
    *,
    candidate: PaperStrategyCandidateDecisionInput,
    config: PaperStrategyCandidateDecisionMatrixConfig,
    rank: Decimal,
) -> PaperStrategyCandidateDecisionRow:
    reasons = list(candidate.reason_codes)
    reasons.extend(candidate.evidence_gap_codes)
    cost_adjusted_edge = _quantize_score(
        candidate.net_edge_per_share - candidate.total_cost_per_share,
    )
    _append_rule_reasons(reasons, candidate=candidate, config=config, cost_adjusted_edge=cost_adjusted_edge)
    decision_status = _decision_status(
        candidate=candidate,
        config=config,
        cost_adjusted_edge=cost_adjusted_edge,
        reason_codes=tuple(reasons),
    )
    action = _decision_action(decision_status, tuple(reasons))
    _append_unique(reasons, f"decision_{decision_status}")
    return PaperStrategyCandidateDecisionRow(
        rank=rank,
        market_slug=candidate.market_slug,
        question=candidate.question,
        team_id=candidate.team_id,
        category=candidate.category,
        decision_status=decision_status,
        action=action,
        forecast_probability=candidate.forecast_probability,
        market_probability=candidate.market_probability,
        net_edge_per_share=candidate.net_edge_per_share,
        total_cost_per_share=candidate.total_cost_per_share,
        cost_adjusted_edge=cost_adjusted_edge,
        liquidity_score=candidate.liquidity_score,
        information_quality_score=candidate.information_quality_score,
        source_count=candidate.source_count,
        freshness_minutes=candidate.freshness_minutes,
        resolution_risk_score=candidate.resolution_risk_score,
        team_memory_score=candidate.team_memory_score,
        calibration_score=candidate.calibration_score,
        composite_score=_composite_score(candidate, config),
        reason_codes=tuple(reasons),
    )


def _append_rule_reasons(
    reasons: list[str],
    *,
    candidate: PaperStrategyCandidateDecisionInput,
    config: PaperStrategyCandidateDecisionMatrixConfig,
    cost_adjusted_edge: Decimal,
) -> None:
    if candidate.net_edge_per_share < config.min_net_edge_per_share:
        _append_unique(reasons, "edge_below_minimum")
    if candidate.total_cost_per_share > config.max_total_cost_per_share:
        _append_unique(reasons, "cost_exceeds_limit")
    if cost_adjusted_edge <= ZERO:
        _append_unique(reasons, "costs_erase_edge")
    if candidate.source_count < config.min_source_count:
        _append_unique(reasons, "source_count_below_minimum")
    if candidate.freshness_minutes > config.max_freshness_minutes:
        _append_unique(reasons, "stale_information")
    if (
        candidate.information_quality_score < config.min_information_quality_score
        and candidate.source_count >= config.min_source_count
        and candidate.freshness_minutes <= config.max_freshness_minutes
    ):
        _append_unique(reasons, "information_quality_below_candidate_threshold")
    if candidate.liquidity_score < config.min_liquidity_score:
        _append_unique(reasons, "liquidity_below_minimum")
    if candidate.resolution_risk_score > config.max_resolution_risk_score:
        _append_unique(reasons, "resolution_risk_above_limit")
    elif candidate.resolution_risk_score >= _quantize_score(config.max_resolution_risk_score * Decimal("0.900000")):
        _append_unique(reasons, "resolution_risk_watch")
    if candidate.team_memory_score < config.min_team_memory_score:
        _append_unique(reasons, "team_memory_below_minimum")
    if candidate.calibration_score < config.min_calibration_score:
        _append_unique(reasons, "calibration_below_minimum")


def _decision_status(
    *,
    candidate: PaperStrategyCandidateDecisionInput,
    config: PaperStrategyCandidateDecisionMatrixConfig,
    cost_adjusted_edge: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    hard_blockers = {
        "cost_exceeds_limit",
        "costs_erase_edge",
        "edge_below_minimum",
        "liquidity_below_minimum",
        "resolution_risk_above_limit",
        "source_count_below_minimum",
        "stale_information",
    }
    if any(reason_code in hard_blockers for reason_code in reason_codes):
        return "blocked"
    if (
        cost_adjusted_edge > ZERO
        and candidate.information_quality_score >= config.min_information_quality_score
        and candidate.team_memory_score >= config.min_team_memory_score
        and candidate.calibration_score >= config.min_calibration_score
        and _composite_score(candidate, config) >= config.min_candidate_score
    ):
        return "candidate"
    if _composite_score(candidate, config) >= config.min_research_score:
        return "research"
    return "watch"


def _decision_action(decision_status: str, reason_codes: tuple[str, ...]) -> str:
    if decision_status == "candidate":
        return "select_for_manual_review"
    if decision_status == "blocked":
        return "reject"
    if any(
        reason_code in reason_codes
        for reason_code in (
            "calibration_below_minimum",
            "resolution_risk_watch",
            "team_memory_below_minimum",
        )
    ):
        return "escalate_specialist_review"
    if any(
        reason_code in reason_codes
        for reason_code in (
            "information_quality_below_candidate_threshold",
            "missing_primary_source",
            "source_count_below_minimum",
            "stale_information",
        )
    ):
        return "refresh_information"
    return "watch"


def _composite_score(
    candidate: PaperStrategyCandidateDecisionInput,
    config: PaperStrategyCandidateDecisionMatrixConfig,
) -> Decimal:
    edge_score = _unit_ratio(candidate.net_edge_per_share, config.min_net_edge_per_share)
    cost_score = ONE - _unit_ratio(candidate.total_cost_per_share, config.max_total_cost_per_share)
    resolution_score = ONE - candidate.resolution_risk_score
    raw_score = (
        edge_score * config.edge_weight
        + candidate.information_quality_score * config.information_quality_weight
        + cost_score * config.cost_weight
        + candidate.liquidity_score * config.liquidity_weight
        + resolution_score * config.resolution_risk_weight
        + candidate.team_memory_score * config.team_memory_weight
    )
    evidence_penalty = _evidence_penalty(candidate, config)
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _normalize_unit_decimal(
            "composite_score",
            max(ZERO, raw_score - BASE_SCORE_PENALTY - evidence_penalty),
        )


def _evidence_penalty(
    candidate: PaperStrategyCandidateDecisionInput,
    config: PaperStrategyCandidateDecisionMatrixConfig,
) -> Decimal:
    penalty = ZERO
    if candidate.source_count < config.min_source_count:
        penalty += Decimal("0.025000")
    if candidate.freshness_minutes > config.max_freshness_minutes:
        penalty += Decimal("0.030500")
    return penalty


def _unit_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _normalize_unit_decimal("ratio", min(max(numerator / denominator, ZERO), ONE))


def _order_rows(
    rows: tuple[PaperStrategyCandidateDecisionRow, ...],
) -> tuple[PaperStrategyCandidateDecisionRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.decision_status],
                -row.composite_score,
                row.market_slug,
                row.team_id,
                row.category,
            ),
        ),
    )


def _normalize_inputs(
    candidates: Iterable[PaperStrategyCandidateDecisionInput],
) -> tuple[PaperStrategyCandidateDecisionInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of PaperStrategyCandidateDecisionInput values")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of PaperStrategyCandidateDecisionInput values") from exc
    for item in items:
        if type(item) is not PaperStrategyCandidateDecisionInput:
            raise ValueError("candidates must contain only PaperStrategyCandidateDecisionInput values")
        _validate_hard_flags(item)
    return items


def _normalize_rows(
    rows: Iterable[PaperStrategyCandidateDecisionRow],
) -> tuple[PaperStrategyCandidateDecisionRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("decision_rows must be an iterable of PaperStrategyCandidateDecisionRow values")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("decision_rows must be an iterable of PaperStrategyCandidateDecisionRow values") from exc
    for item in items:
        if type(item) is not PaperStrategyCandidateDecisionRow:
            raise ValueError("decision_rows must contain only PaperStrategyCandidateDecisionRow values")
        _validate_hard_flags(item)
    return items


def _normalize_reason_code_counts(
    reason_code_counts: Iterable[tuple[str, Decimal]],
) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(reason_code_counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable of tuples")
    try:
        items = tuple(reason_code_counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable of tuples") from exc
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count tuples")
        reason_code, count = item
        _require_canonical_string("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason codes")
        seen.add(reason_code)
        normalized.append((reason_code, _normalize_nonnegative_decimal("count", count)))
    return tuple(sorted(normalized, key=lambda item: item[0]))


def _reason_code_counts(
    rows: tuple[PaperStrategyCandidateDecisionRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + COUNT_ONE
    return tuple(sorted(counts.items(), key=lambda item: item[0]))


def _status_count(rows: tuple[PaperStrategyCandidateDecisionRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.decision_status == status))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _validate_report_consistency(report: PaperStrategyCandidateDecisionMatrixReport) -> None:
    if report.candidate_count != _count(len(report.decision_rows)):
        raise ValueError("candidate_count must match decision_rows length")
    if report.select_count != _status_count(report.decision_rows, "candidate"):
        raise ValueError("select_count must match decision rows")
    if report.research_count != _status_count(report.decision_rows, "research"):
        raise ValueError("research_count must match decision rows")
    if report.watch_count != _status_count(report.decision_rows, "watch"):
        raise ValueError("watch_count must match decision rows")
    if report.blocked_count != _status_count(report.decision_rows, "blocked"):
        raise ValueError("blocked_count must match decision rows")
    if report.reason_code_counts != _reason_code_counts(report.decision_rows):
        raise ValueError("reason_code_counts must match decision rows")


def _validate_row_action_semantics(row: PaperStrategyCandidateDecisionRow) -> None:
    if row.decision_status == "candidate" and row.action != "select_for_manual_review":
        raise ValueError("candidate rows must select for manual review")
    if row.decision_status == "blocked" and row.action != "reject":
        raise ValueError("blocked rows must reject")


def _validate_weight_total(config: PaperStrategyCandidateDecisionMatrixConfig) -> None:
    total = (
        config.edge_weight
        + config.information_quality_weight
        + config.cost_weight
        + config.liquidity_weight
        + config.resolution_risk_weight
        + config.team_memory_weight
    )
    if total != ONE:
        raise ValueError("decision matrix weights must sum to 1.000000")


def _normalize_string_tuple(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of canonical strings")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of canonical strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return tuple(sorted(set(items)))


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _normalize_unit_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_score(value)


def _quantize_score(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return value.quantize(SCORE_QUANTUM)


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")
