"""Pure paper/report/readonly candidate decision checkpoint v10."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


SCORE_QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
READY_THRESHOLD = Decimal("0.700000")
BLOCKED_READY_THRESHOLD = Decimal("0.500000")
NEAR_RESOLUTION_MINUTES = Decimal("60.000000")
BLOCKING_RESOLUTION_MINUTES = Decimal("15.000000")

CHECKPOINT_STATUSES = ("approved", "review_required", "blocked")
APPROVAL_PATHS = ("paper_approval_ready", "manual_review", "blocked")
RECOMMENDATION_STATUSES = ("recommend", "review", "watch", "blocked")
DATA_GAP_STATUSES = ("none", "minor", "material", "blocking")
RISK_REGISTER_STATUSES = ("clear", "watch", "blocking")
PORTFOLIO_FIT_STATUSES = ("fit", "watch", "blocked")
REASON_CODES = (
    "recommendation_recommend",
    "recommendation_review",
    "recommendation_watch",
    "recommendation_blocked",
    "decision_readiness_ready",
    "decision_readiness_watch",
    "decision_readiness_blocked",
    "data_gap_none",
    "data_gap_minor",
    "data_gap_material",
    "data_gap_blocking",
    "risk_register_clear",
    "risk_register_watch",
    "risk_register_blocking",
    "portfolio_fit",
    "portfolio_fit_watch",
    "portfolio_fit_blocked",
    "human_review_required",
    "human_review_not_required",
    "resolution_window_sufficient",
    "near_resolution",
    "resolution_window_blocking",
    "checkpoint_approved",
    "checkpoint_review_required",
    "checkpoint_blocked",
)


@dataclass(frozen=True)
class StrategyCandidateDecisionCheckpointV10Input:
    market_id: str
    recommendation_status: str
    decision_readiness: Decimal
    data_gap_status: str
    risk_register_status: str
    portfolio_fit_status: str
    human_review_required: bool
    time_to_resolution_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("market_id", self.market_id)
        _require_choice(
            "recommendation_status",
            self.recommendation_status,
            RECOMMENDATION_STATUSES,
        )
        object.__setattr__(
            self,
            "decision_readiness",
            _normalize_probability("decision_readiness", self.decision_readiness),
        )
        _require_choice("data_gap_status", self.data_gap_status, DATA_GAP_STATUSES)
        _require_choice(
            "risk_register_status",
            self.risk_register_status,
            RISK_REGISTER_STATUSES,
        )
        _require_choice(
            "portfolio_fit_status",
            self.portfolio_fit_status,
            PORTFOLIO_FIT_STATUSES,
        )
        _require_bool("human_review_required", self.human_review_required)
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        reject_unsafe_surface_fields("candidate decision checkpoint input", self)
        require_paper_only_flags("candidate decision checkpoint input", self)


@dataclass(frozen=True)
class StrategyCandidateDecisionCheckpointV10Result:
    market_id: str
    recommendation_status: str
    decision_readiness: Decimal
    data_gap_status: str
    risk_register_status: str
    portfolio_fit_status: str
    human_review_required: bool
    time_to_resolution_minutes: Decimal
    checkpoint_status: str
    approval_path: str
    blocking_reasons: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_identifier("market_id", self.market_id)
        _require_choice(
            "recommendation_status",
            self.recommendation_status,
            RECOMMENDATION_STATUSES,
        )
        object.__setattr__(
            self,
            "decision_readiness",
            _normalize_probability("decision_readiness", self.decision_readiness),
        )
        _require_choice("data_gap_status", self.data_gap_status, DATA_GAP_STATUSES)
        _require_choice(
            "risk_register_status",
            self.risk_register_status,
            RISK_REGISTER_STATUSES,
        )
        _require_choice(
            "portfolio_fit_status",
            self.portfolio_fit_status,
            PORTFOLIO_FIT_STATUSES,
        )
        _require_bool("human_review_required", self.human_review_required)
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_nonnegative_decimal(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        _require_choice("checkpoint_status", self.checkpoint_status, CHECKPOINT_STATUSES)
        _require_choice("approval_path", self.approval_path, APPROVAL_PATHS)
        object.__setattr__(
            self,
            "blocking_reasons",
            _normalize_string_tuple("blocking_reasons", self.blocking_reasons),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_result(self)
        reject_unsafe_surface_fields("candidate decision checkpoint result", self)
        require_paper_only_flags("candidate decision checkpoint result", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_candidate_decision_checkpoint_v10_payload(self)


def build_strategy_candidate_decision_checkpoint_v10(
    candidate: StrategyCandidateDecisionCheckpointV10Input,
) -> StrategyCandidateDecisionCheckpointV10Result:
    if type(candidate) is not StrategyCandidateDecisionCheckpointV10Input:
        raise ValueError(
            "candidate must be a StrategyCandidateDecisionCheckpointV10Input",
        )
    reject_unsafe_surface_fields("candidate decision checkpoint input", candidate)
    require_paper_only_flags("candidate decision checkpoint input", candidate)

    hard_blocked = _has_hard_blocker(candidate)
    blocking_reasons = _blocking_reasons(candidate)
    checkpoint_status = _checkpoint_status(
        hard_blocked=hard_blocked,
        blocking_reasons=blocking_reasons,
    )
    return StrategyCandidateDecisionCheckpointV10Result(
        market_id=candidate.market_id,
        recommendation_status=candidate.recommendation_status,
        decision_readiness=candidate.decision_readiness,
        data_gap_status=candidate.data_gap_status,
        risk_register_status=candidate.risk_register_status,
        portfolio_fit_status=candidate.portfolio_fit_status,
        human_review_required=candidate.human_review_required,
        time_to_resolution_minutes=candidate.time_to_resolution_minutes,
        checkpoint_status=checkpoint_status,
        approval_path=_approval_path(checkpoint_status),
        blocking_reasons=blocking_reasons,
        reason_codes=_reason_codes(candidate, checkpoint_status),
    )


def strategy_candidate_decision_checkpoint_v10_payload(
    result: StrategyCandidateDecisionCheckpointV10Result,
) -> dict[str, Any]:
    if type(result) is not StrategyCandidateDecisionCheckpointV10Result:
        raise ValueError(
            "result must be a StrategyCandidateDecisionCheckpointV10Result",
        )
    reject_unsafe_surface_fields("candidate decision checkpoint result", result)
    require_paper_only_flags("candidate decision checkpoint result", result)
    payload = json_ready_no_floats(result)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields("candidate decision checkpoint payload", payload)
    return payload


def _blocking_reasons(
    candidate: StrategyCandidateDecisionCheckpointV10Input,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.recommendation_status == "blocked":
        reasons.append("Recommendation status blocked prevents approval.")
    elif candidate.recommendation_status != "recommend":
        reasons.append(
            f"Recommendation status {candidate.recommendation_status} "
            "requires human decision.",
        )

    if candidate.decision_readiness < BLOCKED_READY_THRESHOLD:
        reasons.append(
            "Decision readiness below 0.500000 blocks checkpoint approval.",
        )
    elif candidate.decision_readiness < READY_THRESHOLD:
        reasons.append("Raise decision readiness to at least 0.700000.")

    if candidate.data_gap_status == "blocking":
        reasons.append("Blocking data gaps must be resolved.")
    elif candidate.data_gap_status == "material":
        reasons.append("Resolve material data gaps before approval.")
    elif candidate.data_gap_status == "minor":
        reasons.append("Review minor data gaps before approval.")

    if candidate.risk_register_status == "blocking":
        reasons.append("Risk register status blocking prevents approval.")
    elif candidate.risk_register_status != "clear":
        reasons.append(f"Review risk register status {candidate.risk_register_status}.")

    if candidate.portfolio_fit_status == "blocked":
        reasons.append("Portfolio fit status blocked prevents approval.")
    elif candidate.portfolio_fit_status != "fit":
        reasons.append(
            f"Portfolio fit status {candidate.portfolio_fit_status} requires review.",
        )

    if candidate.human_review_required:
        reasons.append("Human review is explicitly required.")

    if candidate.time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        reasons.append(
            f"Only {candidate.time_to_resolution_minutes} minutes remain to resolution.",
        )
    return tuple(reasons)


def _has_hard_blocker(candidate: StrategyCandidateDecisionCheckpointV10Input) -> bool:
    return (
        candidate.recommendation_status == "blocked"
        or candidate.decision_readiness < BLOCKED_READY_THRESHOLD
        or candidate.data_gap_status == "blocking"
        or candidate.risk_register_status == "blocking"
        or candidate.portfolio_fit_status == "blocked"
        or candidate.time_to_resolution_minutes <= BLOCKING_RESOLUTION_MINUTES
    )


def _checkpoint_status(*, hard_blocked: bool, blocking_reasons: tuple[str, ...]) -> str:
    if hard_blocked:
        return "blocked"
    if blocking_reasons:
        return "review_required"
    return "approved"


def _approval_path(checkpoint_status: str) -> str:
    if checkpoint_status == "approved":
        return "paper_approval_ready"
    if checkpoint_status == "review_required":
        return "manual_review"
    if checkpoint_status == "blocked":
        return "blocked"
    raise ValueError("checkpoint_status must be supported")


def _reason_codes(
    candidate: StrategyCandidateDecisionCheckpointV10Input,
    checkpoint_status: str,
) -> tuple[str, ...]:
    codes = [
        f"recommendation_{candidate.recommendation_status}",
        _decision_readiness_reason_code(candidate.decision_readiness),
        f"data_gap_{candidate.data_gap_status}",
        f"risk_register_{candidate.risk_register_status}",
        _portfolio_fit_reason_code(candidate.portfolio_fit_status),
        (
            "human_review_required"
            if candidate.human_review_required
            else "human_review_not_required"
        ),
        _resolution_window_reason_code(candidate.time_to_resolution_minutes),
        f"checkpoint_{checkpoint_status}",
    ]
    return _normalize_reason_codes(tuple(codes))


def _decision_readiness_reason_code(decision_readiness: Decimal) -> str:
    if decision_readiness < BLOCKED_READY_THRESHOLD:
        return "decision_readiness_blocked"
    if decision_readiness < READY_THRESHOLD:
        return "decision_readiness_watch"
    return "decision_readiness_ready"


def _portfolio_fit_reason_code(portfolio_fit_status: str) -> str:
    if portfolio_fit_status == "fit":
        return "portfolio_fit"
    if portfolio_fit_status == "watch":
        return "portfolio_fit_watch"
    if portfolio_fit_status == "blocked":
        return "portfolio_fit_blocked"
    raise ValueError("portfolio_fit_status must be supported")


def _resolution_window_reason_code(time_to_resolution_minutes: Decimal) -> str:
    if time_to_resolution_minutes <= BLOCKING_RESOLUTION_MINUTES:
        return "resolution_window_blocking"
    if time_to_resolution_minutes <= NEAR_RESOLUTION_MINUTES:
        return "near_resolution"
    return "resolution_window_sufficient"


def _validate_result(result: StrategyCandidateDecisionCheckpointV10Result) -> None:
    candidate = StrategyCandidateDecisionCheckpointV10Input(
        market_id=result.market_id,
        recommendation_status=result.recommendation_status,
        decision_readiness=result.decision_readiness,
        data_gap_status=result.data_gap_status,
        risk_register_status=result.risk_register_status,
        portfolio_fit_status=result.portfolio_fit_status,
        human_review_required=result.human_review_required,
        time_to_resolution_minutes=result.time_to_resolution_minutes,
    )
    blocking_reasons = _blocking_reasons(candidate)
    checkpoint_status = _checkpoint_status(
        hard_blocked=_has_hard_blocker(candidate),
        blocking_reasons=blocking_reasons,
    )
    if result.blocking_reasons != blocking_reasons:
        raise ValueError("blocking_reasons must match candidate fields")
    if result.checkpoint_status != checkpoint_status:
        raise ValueError("checkpoint_status must match candidate fields")
    if result.approval_path != _approval_path(checkpoint_status):
        raise ValueError("approval_path must match checkpoint_status")
    if result.reason_codes != _reason_codes(candidate, checkpoint_status):
        raise ValueError("reason_codes must match candidate fields")


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    normalized = _normalize_string_tuple("reason_codes", values)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in normalized:
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return normalized


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return decimal_value.quantize(SCORE_QUANT)


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
    "CHECKPOINT_STATUSES",
    "APPROVAL_PATHS",
    "RECOMMENDATION_STATUSES",
    "DATA_GAP_STATUSES",
    "RISK_REGISTER_STATUSES",
    "PORTFOLIO_FIT_STATUSES",
    "REASON_CODES",
    "StrategyCandidateDecisionCheckpointV10Input",
    "StrategyCandidateDecisionCheckpointV10Result",
    "build_strategy_candidate_decision_checkpoint_v10",
    "strategy_candidate_decision_checkpoint_v10_payload",
)
