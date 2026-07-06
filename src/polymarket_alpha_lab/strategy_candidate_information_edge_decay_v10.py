"""Paper-only candidate information edge decay screening."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DECIMAL_CONTEXT = Context(prec=28)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")

STALE_SIGNAL_AGE_MINUTES = Decimal("1440.000000")
MATERIAL_PROBABILITY_MOVE_BPS = Decimal("300.000000")
MATERIAL_SPREAD_WIDENING_BPS = Decimal("100.000000")

DECAYING_SCORE_THRESHOLD = Decimal("0.350000")
EXPIRED_SCORE_THRESHOLD = Decimal("0.750000")
WATCH_SCORE_THRESHOLD = Decimal("0.150000")

WATCH_SIGNAL_AGE_MINUTES = Decimal("360.000000")
STALE_SIGNAL_REASON_MINUTES = Decimal("720.000000")
WATCH_PROBABILITY_MOVE_BPS = Decimal("100.000000")
WATCH_SPREAD_WIDENING_BPS = Decimal("25.000000")
LOW_SOURCE_FRESHNESS_SCORE = Decimal("0.250000")
WATCH_SOURCE_FRESHNESS_SCORE = Decimal("0.750000")
HIGH_CROWDING_PRESSURE_SCORE = Decimal("0.750000")
WATCH_CROWDING_PRESSURE_SCORE = Decimal("0.250000")

EDGE_DECAY_STATUSES = ("fresh", "watch", "decaying", "expired")
SCREENING_ACTION_BY_STATUS = {
    "fresh": "continue_screening",
    "watch": "monitor_edge_decay",
    "decaying": "refresh_edge_before_screening",
    "expired": "reject_candidate_until_fresh_signal",
}


@dataclass(frozen=True)
class StrategyCandidateInformationEdgeDecayV10Input:
    market_id: str
    signal_age_minutes: Decimal
    probability_move_bps: Decimal
    spread_widening_bps: Decimal
    source_freshness_score: Decimal
    crowding_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_id",
            _require_canonical_string("market_id", self.market_id),
        )
        for field_name in (
            "signal_age_minutes",
            "probability_move_bps",
            "spread_widening_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_freshness_score",
            "crowding_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("candidate information edge decay input", self)


@dataclass(frozen=True)
class StrategyCandidateInformationEdgeDecayV10Result:
    market_id: str
    signal_age_minutes: Decimal
    probability_move_bps: Decimal
    spread_widening_bps: Decimal
    source_freshness_score: Decimal
    crowding_pressure_score: Decimal
    decay_score: Decimal
    edge_decay_status: str
    screening_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_id",
            _require_canonical_string("market_id", self.market_id),
        )
        for field_name in (
            "signal_age_minutes",
            "probability_move_bps",
            "spread_widening_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_freshness_score",
            "crowding_pressure_score",
            "decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "edge_decay_status",
            _require_member(
                "edge_decay_status",
                self.edge_decay_status,
                EDGE_DECAY_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "screening_action",
            _require_canonical_string("screening_action", self.screening_action),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("candidate information edge decay result", self)
        _validate_result(self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_information_edge_decay_v10_payload(self)


def evaluate_strategy_candidate_information_edge_decay_v10(
    input_row: StrategyCandidateInformationEdgeDecayV10Input,
) -> StrategyCandidateInformationEdgeDecayV10Result:
    if type(input_row) is not StrategyCandidateInformationEdgeDecayV10Input:
        raise ValueError(
            "input_row must be a StrategyCandidateInformationEdgeDecayV10Input",
        )
    require_paper_only_flags("candidate information edge decay input", input_row)

    decay_score = _decay_score(input_row)
    edge_decay_status = _edge_decay_status(decay_score)

    return StrategyCandidateInformationEdgeDecayV10Result(
        market_id=input_row.market_id,
        signal_age_minutes=input_row.signal_age_minutes,
        probability_move_bps=input_row.probability_move_bps,
        spread_widening_bps=input_row.spread_widening_bps,
        source_freshness_score=input_row.source_freshness_score,
        crowding_pressure_score=input_row.crowding_pressure_score,
        decay_score=decay_score,
        edge_decay_status=edge_decay_status,
        screening_action=SCREENING_ACTION_BY_STATUS[edge_decay_status],
        reason_codes=_reason_codes(input_row, edge_decay_status),
    )


def strategy_candidate_information_edge_decay_v10_payload(
    result: StrategyCandidateInformationEdgeDecayV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateInformationEdgeDecayV10Result:
        raise ValueError(
            "result must be a StrategyCandidateInformationEdgeDecayV10Result",
        )
    require_paper_only_flags("candidate information edge decay result", result)
    return json_ready_no_floats(
        {
            "market_id": result.market_id,
            "signal_age_minutes": result.signal_age_minutes,
            "probability_move_bps": result.probability_move_bps,
            "spread_widening_bps": result.spread_widening_bps,
            "source_freshness_score": result.source_freshness_score,
            "crowding_pressure_score": result.crowding_pressure_score,
            "decay_score": result.decay_score,
            "edge_decay_status": result.edge_decay_status,
            "screening_action": result.screening_action,
            "reason_codes": result.reason_codes,
            "paper_only": result.paper_only,
            "report_only": result.report_only,
            "readonly": result.readonly,
        },
    )


def _validate_result(result: StrategyCandidateInformationEdgeDecayV10Result) -> None:
    input_row = StrategyCandidateInformationEdgeDecayV10Input(
        market_id=result.market_id,
        signal_age_minutes=result.signal_age_minutes,
        probability_move_bps=result.probability_move_bps,
        spread_widening_bps=result.spread_widening_bps,
        source_freshness_score=result.source_freshness_score,
        crowding_pressure_score=result.crowding_pressure_score,
    )
    expected_decay_score = _decay_score(input_row)
    if result.decay_score != expected_decay_score:
        raise ValueError("decay_score must match input metrics")
    expected_status = _edge_decay_status(expected_decay_score)
    if result.edge_decay_status != expected_status:
        raise ValueError("edge_decay_status must match decay_score")
    expected_screening_action = SCREENING_ACTION_BY_STATUS[expected_status]
    if result.screening_action != expected_screening_action:
        raise ValueError("screening_action must match edge_decay_status")
    expected_reason_codes = _reason_codes(input_row, expected_status)
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match input metrics and edge_decay_status")


def _decay_score(
    input_row: StrategyCandidateInformationEdgeDecayV10Input,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        source_staleness_score = ONE - input_row.source_freshness_score
        score = (
            _component_score(input_row.signal_age_minutes, STALE_SIGNAL_AGE_MINUTES)
            + _component_score(
                input_row.probability_move_bps,
                MATERIAL_PROBABILITY_MOVE_BPS,
            )
            + _component_score(
                input_row.spread_widening_bps,
                MATERIAL_SPREAD_WIDENING_BPS,
            )
            + source_staleness_score
            + input_row.crowding_pressure_score
        ) / FIVE
    return _normalize_probability("decay_score", score)


def _component_score(value: Decimal, full_decay_value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        score = value / full_decay_value
    return _cap_probability(score)


def _edge_decay_status(decay_score: Decimal) -> str:
    if decay_score >= EXPIRED_SCORE_THRESHOLD:
        return "expired"
    if decay_score >= DECAYING_SCORE_THRESHOLD:
        return "decaying"
    if decay_score >= WATCH_SCORE_THRESHOLD:
        return "watch"
    return "fresh"


def _reason_codes(
    input_row: StrategyCandidateInformationEdgeDecayV10Input,
    edge_decay_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"candidate_information_edge_{edge_decay_status}"]
    if input_row.signal_age_minutes >= STALE_SIGNAL_REASON_MINUTES:
        reason_codes.append("signal_age_stale")
    elif input_row.signal_age_minutes >= WATCH_SIGNAL_AGE_MINUTES:
        reason_codes.append("signal_age_watch")

    if input_row.probability_move_bps >= MATERIAL_PROBABILITY_MOVE_BPS:
        reason_codes.append("probability_move_material")
    elif input_row.probability_move_bps >= WATCH_PROBABILITY_MOVE_BPS:
        reason_codes.append("probability_move_watch")

    if input_row.spread_widening_bps >= MATERIAL_SPREAD_WIDENING_BPS:
        reason_codes.append("spread_widening_material")
    elif input_row.spread_widening_bps >= WATCH_SPREAD_WIDENING_BPS:
        reason_codes.append("spread_widening_watch")

    if input_row.source_freshness_score <= LOW_SOURCE_FRESHNESS_SCORE:
        reason_codes.append("source_freshness_low")
    elif input_row.source_freshness_score <= WATCH_SOURCE_FRESHNESS_SCORE:
        reason_codes.append("source_freshness_watch")

    if input_row.crowding_pressure_score >= HIGH_CROWDING_PRESSURE_SCORE:
        reason_codes.append("crowding_pressure_high")
    elif input_row.crowding_pressure_score >= WATCH_CROWDING_PRESSURE_SCORE:
        reason_codes.append("crowding_pressure_watch")

    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _cap_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _normalize_probability("probability", value)


def _normalize_nonnegative_decimal(field_name: str, value: Any) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_probability(field_name: str, value: Any) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between {ZERO} and {ONE}")
    return value


def _normalize_decimal(field_name: str, value: Any) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _normalize_reason_codes(field_name: str, value: Any) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    reason_codes = tuple(_require_canonical_string(field_name, item) for item in value)
    return _dedupe(reason_codes)


def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return tuple(result)


def _require_member(
    field_name: str,
    value: Any,
    allowed_values: tuple[str, ...],
) -> str:
    value = _require_canonical_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_canonical_string(field_name: str, value: Any) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


__all__ = (
    "StrategyCandidateInformationEdgeDecayV10Input",
    "StrategyCandidateInformationEdgeDecayV10Result",
    "evaluate_strategy_candidate_information_edge_decay_v10",
    "strategy_candidate_information_edge_decay_v10_payload",
)
