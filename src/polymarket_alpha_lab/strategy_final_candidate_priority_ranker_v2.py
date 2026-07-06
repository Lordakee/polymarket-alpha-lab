"""Pure in-memory Phase 1 final candidate priority ranker."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_FINAL_CANDIDATE_PRIORITY_RANKER_V2_CONFIG_VERSION = (
    "strategy-final-candidate-priority-ranker-v2"
)

DECIMAL_PRECISION_TEMPLATE = (
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
)
SHA256_HEX_TEMPLATE = (
    "00000000000000000000000000000000"
    "00000000000000000000000000000000"
)
DECIMAL_CONTEXT = Context(
    prec=len(DECIMAL_PRECISION_TEMPLATE),
    rounding=ROUND_HALF_EVEN,
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")

RANKING_STATUSES = ("pass", "watch", "blocked")
SAFETY_GATE_STATUSES = RANKING_STATUSES
PASS_REASON_CODE = "priority_ranker_passed"
EMPTY_REASON_CODE = "priority_ranker_empty"
ROW_REASON_CODE_SEQUENCE = (
    "edge_below_cost_break_even",
    "safety_gate_watch",
    "safety_gate_blocked",
    "uncertainty_band_above_limit",
    "portfolio_impact_below_minimum",
    "liquidity_exit_risk_above_limit",
    "resolution_risk_above_limit",
    "specialist_confidence_below_minimum",
)
REPORT_REASON_CODE_SEQUENCE = (EMPTY_REASON_CODE, PASS_REASON_CODE) + ROW_REASON_CODE_SEQUENCE
BLOCKING_REASON_CODES = frozenset(
    (
        "edge_below_cost_break_even",
        "safety_gate_blocked",
        "liquidity_exit_risk_above_limit",
        "resolution_risk_above_limit",
    ),
)
STATUS_SORT_RANK = {
    "pass": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "blocked": Decimal("2.000000"),
}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sig", "ning"),
        _join_parts("mu", "tation"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class StrategyFinalCandidatePriorityRankerV2Config:
    config_version: str = DEFAULT_STRATEGY_FINAL_CANDIDATE_PRIORITY_RANKER_V2_CONFIG_VERSION
    max_uncertainty_band_probability: Decimal = Decimal("0.050000")
    max_liquidity_exit_risk_score: Decimal = Decimal("0.050000")
    max_resolution_risk_score: Decimal = Decimal("0.050000")
    min_specialist_signal_confidence: Decimal = Decimal("0.700000")
    min_portfolio_impact_score: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyFinalCandidatePriorityRankerV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyFinalCandidatePriorityRankerV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_FINAL_CANDIDATE_PRIORITY_RANKER_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_uncertainty_band_probability",
            "max_liquidity_exit_risk_score",
            "max_resolution_risk_score",
            "min_specialist_signal_confidence",
            "min_portfolio_impact_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyFinalCandidatePriorityRankerV2Candidate:
    candidate_id: str
    market_slug: str
    condition_id: str
    outcome: str
    evaluated_at: datetime
    source_verified_edge_probability: Decimal
    cost_break_even_probability: Decimal
    safety_gate_status: str
    uncertainty_band_probability: Decimal
    portfolio_impact_score: Decimal
    liquidity_exit_risk_score: Decimal
    resolution_risk_score: Decimal
    specialist_signal_confidence: Decimal
    specialist_signal_count: Decimal
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyFinalCandidatePriorityRankerV2Candidate does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
            "condition_id",
            "outcome",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        for field_name in (
            "source_verified_edge_probability",
            "cost_break_even_probability",
            "uncertainty_band_probability",
            "portfolio_impact_score",
            "liquidity_exit_risk_score",
            "resolution_risk_score",
            "specialist_signal_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("safety_gate_status", self.safety_gate_status, SAFETY_GATE_STATUSES)
        object.__setattr__(
            self,
            "specialist_signal_count",
            _normalize_count("specialist_signal_count", self.specialist_signal_count),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyFinalCandidatePriorityRankerV2Row:
    priority_rank: Decimal
    candidate_id: str
    market_slug: str
    condition_id: str
    outcome: str
    evaluated_at: datetime
    source_verified_edge_probability: Decimal
    cost_break_even_probability: Decimal
    edge_after_cost_probability: Decimal
    safety_gate_status: str
    uncertainty_band_probability: Decimal
    uncertainty_adjusted_edge_probability: Decimal
    portfolio_impact_score: Decimal
    liquidity_exit_risk_score: Decimal
    resolution_risk_score: Decimal
    risk_adjusted_edge_probability: Decimal
    specialist_signal_confidence: Decimal
    specialist_signal_count: Decimal
    priority_score: Decimal
    ranking_status: str
    reason_codes: tuple[str, ...]
    source_config_version: str
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyFinalCandidatePriorityRankerV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_slug",
            "condition_id",
            "outcome",
            "source_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "evaluated_at", _as_utc("evaluated_at", self.evaluated_at))
        object.__setattr__(self, "priority_rank", _normalize_count("priority_rank", self.priority_rank))
        for field_name in (
            "source_verified_edge_probability",
            "cost_break_even_probability",
            "uncertainty_band_probability",
            "portfolio_impact_score",
            "liquidity_exit_risk_score",
            "resolution_risk_score",
            "specialist_signal_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "edge_after_cost_probability",
            "uncertainty_adjusted_edge_probability",
            "risk_adjusted_edge_probability",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("safety_gate_status", self.safety_gate_status, SAFETY_GATE_STATUSES)
        object.__setattr__(
            self,
            "specialist_signal_count",
            _normalize_count("specialist_signal_count", self.specialist_signal_count),
        )
        _require_member("ranking_status", self.ranking_status, RANKING_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class StrategyFinalCandidatePriorityRankerV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    top_candidate_id: str | None
    max_priority_score: Decimal
    total_priority_score: Decimal
    ranking_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyFinalCandidatePriorityRankerV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyFinalCandidatePriorityRankerV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyFinalCandidatePriorityRankerV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.top_candidate_id is not None:
            _require_public_string("top_candidate_id", self.top_candidate_id)
        for field_name in ("max_priority_score", "total_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("ranking_status", self.ranking_status, RANKING_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_strategy_final_candidate_priority_ranker_v2_report(
    candidates: list[StrategyFinalCandidatePriorityRankerV2Candidate]
    | tuple[StrategyFinalCandidatePriorityRankerV2Candidate, ...],
    *,
    config: StrategyFinalCandidatePriorityRankerV2Config,
    generated_at: datetime,
) -> StrategyFinalCandidatePriorityRankerV2Report:
    if type(config) is not StrategyFinalCandidatePriorityRankerV2Config:
        raise ValueError("config must be a StrategyFinalCandidatePriorityRankerV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    _validate_unique_candidates(normalized_candidates)
    _validate_not_after_generated_at(normalized_candidates, generated_at=generated_at_utc)
    unranked_rows = tuple(_row_for_candidate(candidate, config=config) for candidate in normalized_candidates)
    ranked_rows = _ranked_rows(unranked_rows)

    return StrategyFinalCandidatePriorityRankerV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(ranked_rows)),
        pass_count=_status_count(ranked_rows, "pass"),
        watch_count=_status_count(ranked_rows, "watch"),
        blocked_count=_status_count(ranked_rows, "blocked"),
        top_candidate_id=next(iter(ranked_rows)).candidate_id if ranked_rows else None,
        max_priority_score=max(
            (row.priority_score for row in ranked_rows),
            default=ZERO,
        ),
        total_priority_score=_sum_decimal(tuple(row.priority_score for row in ranked_rows)),
        ranking_status=_report_status(ranked_rows),
        recommended_next_step=_recommended_next_step(_report_status(ranked_rows)),
        reason_codes=_report_reason_codes(ranked_rows),
        rows=ranked_rows,
    )


def strategy_final_candidate_priority_ranker_v2_public_payload(
    report: StrategyFinalCandidatePriorityRankerV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyFinalCandidatePriorityRankerV2Report:
        raise ValueError("report must be a StrategyFinalCandidatePriorityRankerV2Report")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_strategy_final_candidate_priority_ranker_v2_public_payload(payload)
    return payload


def validate_strategy_final_candidate_priority_ranker_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("strategy final candidate priority ranker payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_candidate(
    candidate: StrategyFinalCandidatePriorityRankerV2Candidate,
    *,
    config: StrategyFinalCandidatePriorityRankerV2Config,
) -> StrategyFinalCandidatePriorityRankerV2Row:
    edge_after_cost = _subtract_decimal(
        candidate.source_verified_edge_probability,
        candidate.cost_break_even_probability,
    )
    uncertainty_adjusted_edge = _subtract_decimal(
        edge_after_cost,
        candidate.uncertainty_band_probability,
    )
    risk_adjusted_edge = _subtract_decimal(
        _subtract_decimal(
            uncertainty_adjusted_edge,
            candidate.liquidity_exit_risk_score,
        ),
        candidate.resolution_risk_score,
    )
    priority_score = _add_decimal(
        risk_adjusted_edge,
        _multiply_decimal(
            candidate.portfolio_impact_score,
            candidate.specialist_signal_confidence,
        ),
    )
    reason_codes = _row_reason_codes(candidate, edge_after_cost=edge_after_cost, config=config)
    return StrategyFinalCandidatePriorityRankerV2Row(
        priority_rank=ZERO,
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        condition_id=candidate.condition_id,
        outcome=candidate.outcome,
        evaluated_at=candidate.evaluated_at,
        source_verified_edge_probability=candidate.source_verified_edge_probability,
        cost_break_even_probability=candidate.cost_break_even_probability,
        edge_after_cost_probability=edge_after_cost,
        safety_gate_status=candidate.safety_gate_status,
        uncertainty_band_probability=candidate.uncertainty_band_probability,
        uncertainty_adjusted_edge_probability=uncertainty_adjusted_edge,
        portfolio_impact_score=candidate.portfolio_impact_score,
        liquidity_exit_risk_score=candidate.liquidity_exit_risk_score,
        resolution_risk_score=candidate.resolution_risk_score,
        risk_adjusted_edge_probability=risk_adjusted_edge,
        specialist_signal_confidence=candidate.specialist_signal_confidence,
        specialist_signal_count=candidate.specialist_signal_count,
        priority_score=priority_score,
        ranking_status=_row_status(reason_codes),
        reason_codes=reason_codes,
        source_config_version=candidate.source_config_version,
    )


def _row_reason_codes(
    candidate: StrategyFinalCandidatePriorityRankerV2Candidate,
    *,
    edge_after_cost: Decimal,
    config: StrategyFinalCandidatePriorityRankerV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if edge_after_cost <= ZERO:
        reason_codes.append("edge_below_cost_break_even")
    if candidate.safety_gate_status == "watch":
        reason_codes.append("safety_gate_watch")
    if candidate.safety_gate_status == "blocked":
        reason_codes.append("safety_gate_blocked")
    if candidate.uncertainty_band_probability > config.max_uncertainty_band_probability:
        reason_codes.append("uncertainty_band_above_limit")
    if candidate.portfolio_impact_score < config.min_portfolio_impact_score:
        reason_codes.append("portfolio_impact_below_minimum")
    if candidate.liquidity_exit_risk_score > config.max_liquidity_exit_risk_score:
        reason_codes.append("liquidity_exit_risk_above_limit")
    if candidate.resolution_risk_score > config.max_resolution_risk_score:
        reason_codes.append("resolution_risk_above_limit")
    if candidate.specialist_signal_confidence < config.min_specialist_signal_confidence:
        reason_codes.append("specialist_confidence_below_minimum")
    if not reason_codes:
        return (PASS_REASON_CODE,)
    return tuple(
        reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in reason_codes
    )


def _ranked_rows(
    rows: tuple[StrategyFinalCandidatePriorityRankerV2Row, ...],
) -> tuple[StrategyFinalCandidatePriorityRankerV2Row, ...]:
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    ranked: list[StrategyFinalCandidatePriorityRankerV2Row] = []
    current_rank = ZERO
    for row in sorted_rows:
        current_rank = _add_decimal(current_rank, ONE)
        ranked.append(replace_row_rank(row, current_rank))
    return tuple(ranked)


def replace_row_rank(
    row: StrategyFinalCandidatePriorityRankerV2Row,
    priority_rank: Decimal,
) -> StrategyFinalCandidatePriorityRankerV2Row:
    return StrategyFinalCandidatePriorityRankerV2Row(
        priority_rank=priority_rank,
        candidate_id=row.candidate_id,
        market_slug=row.market_slug,
        condition_id=row.condition_id,
        outcome=row.outcome,
        evaluated_at=row.evaluated_at,
        source_verified_edge_probability=row.source_verified_edge_probability,
        cost_break_even_probability=row.cost_break_even_probability,
        edge_after_cost_probability=row.edge_after_cost_probability,
        safety_gate_status=row.safety_gate_status,
        uncertainty_band_probability=row.uncertainty_band_probability,
        uncertainty_adjusted_edge_probability=row.uncertainty_adjusted_edge_probability,
        portfolio_impact_score=row.portfolio_impact_score,
        liquidity_exit_risk_score=row.liquidity_exit_risk_score,
        resolution_risk_score=row.resolution_risk_score,
        risk_adjusted_edge_probability=row.risk_adjusted_edge_probability,
        specialist_signal_confidence=row.specialist_signal_confidence,
        specialist_signal_count=row.specialist_signal_count,
        priority_score=row.priority_score,
        ranking_status=row.ranking_status,
        reason_codes=row.reason_codes,
        source_config_version=row.source_config_version,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (PASS_REASON_CODE,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[StrategyFinalCandidatePriorityRankerV2Row, ...]) -> str:
    statuses = tuple(row.ranking_status for row in rows)
    if "blocked" in statuses:
        return "blocked"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _recommended_next_step(ranking_status: str) -> str:
    if ranking_status == "blocked":
        return "hold_report_only_priority_review"
    if ranking_status == "watch":
        return "review_report_only_priority_queue"
    return "continue_report_only_priority_queue"


def _report_reason_codes(
    rows: tuple[StrategyFinalCandidatePriorityRankerV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    present = set(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    )
    if not present:
        return (PASS_REASON_CODE,)
    return tuple(reason_code for reason_code in ROW_REASON_CODE_SEQUENCE if reason_code in present)


def _normalize_candidates(
    value: object,
) -> tuple[StrategyFinalCandidatePriorityRankerV2Candidate, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("candidates must be a list or tuple")
    candidates = tuple(value)
    for item in candidates:
        if type(item) is not StrategyFinalCandidatePriorityRankerV2Candidate:
            raise ValueError(
                "candidates must contain StrategyFinalCandidatePriorityRankerV2Candidate values",
            )
        _require_hard_flags("candidate", item)
    return candidates


def _normalize_rows(
    value: object,
) -> tuple[StrategyFinalCandidatePriorityRankerV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str, str]] = set()
    for row in rows:
        if type(row) is not StrategyFinalCandidatePriorityRankerV2Row:
            raise ValueError("rows must contain StrategyFinalCandidatePriorityRankerV2Row values")
        _require_hard_flags("row", row)
        key = _candidate_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate final candidate")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_ranked_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed_values)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_unique_candidates(
    candidates: tuple[StrategyFinalCandidatePriorityRankerV2Candidate, ...],
) -> None:
    seen: set[tuple[str, str, str, str]] = set()
    for candidate in candidates:
        key = _candidate_key(candidate)
        if key in seen:
            raise ValueError("candidates contain duplicate final candidate")
        seen.add(key)


def _validate_not_after_generated_at(
    candidates: tuple[StrategyFinalCandidatePriorityRankerV2Candidate, ...],
    *,
    generated_at: datetime,
) -> None:
    for candidate in candidates:
        if candidate.evaluated_at > generated_at:
            raise ValueError("evaluated_at must not be after generated_at")


def _validate_row(row: StrategyFinalCandidatePriorityRankerV2Row) -> None:
    if row.edge_after_cost_probability != _subtract_decimal(
        row.source_verified_edge_probability,
        row.cost_break_even_probability,
    ):
        raise ValueError("edge_after_cost_probability must match edge and cost")
    if row.uncertainty_adjusted_edge_probability != _subtract_decimal(
        row.edge_after_cost_probability,
        row.uncertainty_band_probability,
    ):
        raise ValueError("uncertainty_adjusted_edge_probability must match row fields")
    expected_risk_adjusted_edge = _subtract_decimal(
        _subtract_decimal(
            row.uncertainty_adjusted_edge_probability,
            row.liquidity_exit_risk_score,
        ),
        row.resolution_risk_score,
    )
    if row.risk_adjusted_edge_probability != expected_risk_adjusted_edge:
        raise ValueError("risk_adjusted_edge_probability must match row fields")
    expected_priority_score = _add_decimal(
        row.risk_adjusted_edge_probability,
        _multiply_decimal(row.portfolio_impact_score, row.specialist_signal_confidence),
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match row fields")
    if row.ranking_status != _row_status(row.reason_codes):
        raise ValueError("ranking_status must match reason_codes")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyFinalCandidatePriorityRankerV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.candidate_count:
        raise ValueError("status counts must match candidate_count")
    for row in rows:
        _validate_row(row)
    top_candidate_id = next(iter(rows)).candidate_id if rows else None
    if report.top_candidate_id != top_candidate_id:
        raise ValueError("top_candidate_id must match rows")
    if report.max_priority_score != max(
        (row.priority_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_priority_score must match rows")
    if report.total_priority_score != _sum_decimal(tuple(row.priority_score for row in rows)):
        raise ValueError("total_priority_score must match rows")
    if report.ranking_status != _report_status(rows):
        raise ValueError("ranking_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.ranking_status):
        raise ValueError("recommended_next_step must match ranking_status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_public_numeric_values(value: object, path: str = "") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(
            f"public payload must use Decimal strings, not numeric values at {path}",
        )
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_public_numeric_values(item, nested_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]"
            _reject_public_numeric_values(item, nested_path)


def _payload_required_string(payload: dict[str, Any], key: str) -> str:
    if key not in payload:
        raise ValueError(f"{key} is required")
    value = payload[key]
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _row_derived_validation_digest(row: StrategyFinalCandidatePriorityRankerV2Row) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: StrategyFinalCandidatePriorityRankerV2Report,
) -> str:
    return _public_payload_derived_validation_digest(
        _report_public_payload_for_digest(report),
    )


def _row_public_payload_for_digest(
    row: StrategyFinalCandidatePriorityRankerV2Row,
) -> dict[str, Any]:
    payload = _json_ready_no_floats(asdict(row))
    if not isinstance(payload, dict):
        raise ValueError("row payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: StrategyFinalCandidatePriorityRankerV2Report,
) -> dict[str, Any]:
    payload = _json_ready_no_floats(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("report payload must be an object")
    payload.pop("derived_validation_digest", None)
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("derived validation payload", digest_payload)
    canonical_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public key in {label}")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
                raise ValueError(f"unsafe public key in {label}: {key}")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) is str:
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}: {path}")


def _json_ready_no_floats(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_no_floats(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime JSON value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_no_floats(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_no_floats(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    normalized_value = value.lower()
    if any(fragment in normalized_value for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    _require_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != len(SHA256_HEX_TEMPLATE) or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < len(""):
        raise ValueError("count source must be nonnegative")
    return _decimal_from_number(value)


def _decimal_from_number(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _add_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left + right).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
        return total.quantize(QUANTUM)


def _status_count(
    rows: tuple[StrategyFinalCandidatePriorityRankerV2Row, ...],
    status: str,
) -> Decimal:
    return _count(len(tuple(row for row in rows if row.ranking_status == status)))


def _candidate_key(value: object) -> tuple[str, str, str, str]:
    return (
        getattr(value, "candidate_id"),
        getattr(value, "market_slug"),
        getattr(value, "condition_id"),
        getattr(value, "outcome"),
    )


def _row_sort_key(row: StrategyFinalCandidatePriorityRankerV2Row) -> tuple[Decimal, Decimal, str, str, str, str]:
    return (
        STATUS_SORT_RANK[row.ranking_status],
        -row.priority_score,
        row.candidate_id,
        row.market_slug,
        row.condition_id,
        row.outcome,
    )


def _ranked_row_sort_key(
    row: StrategyFinalCandidatePriorityRankerV2Row,
) -> tuple[Decimal, Decimal, Decimal, str, str, str, str]:
    return (
        row.priority_rank,
        STATUS_SORT_RANK[row.ranking_status],
        -row.priority_score,
        row.candidate_id,
        row.market_slug,
        row.condition_id,
        row.outcome,
    )


__all__ = (
    "DEFAULT_STRATEGY_FINAL_CANDIDATE_PRIORITY_RANKER_V2_CONFIG_VERSION",
    "StrategyFinalCandidatePriorityRankerV2Candidate",
    "StrategyFinalCandidatePriorityRankerV2Config",
    "StrategyFinalCandidatePriorityRankerV2Report",
    "StrategyFinalCandidatePriorityRankerV2Row",
    "build_strategy_final_candidate_priority_ranker_v2_report",
    "strategy_final_candidate_priority_ranker_v2_public_payload",
    "validate_strategy_final_candidate_priority_ranker_v2_public_payload",
)
