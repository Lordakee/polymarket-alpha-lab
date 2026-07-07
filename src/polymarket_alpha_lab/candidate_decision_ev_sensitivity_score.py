"""Pure Phase 1 EV sensitivity score for probability-event decisions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from hashlib import sha256
from typing import Any


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BPS_PER_ONE = Decimal("10000.000000")
DECISION_SUPPORT_STATUSES = ("pass", "watch", "block")
EVALUATED_SIDES = ("yes", "no")
_UNSAFE_TERM_PARTS = (
    ("candidate", "_id"),
    ("market", "_id"),
    ("market", "_slug"),
    ("market", "_que", "stion"),
    ("que", "stion"),
    ("source", "_ref"),
    ("source", "_url"),
    ("d", "sn"),
    ("table", "_name"),
    ("wal", "let"),
    ("au", "th"),
    ("or", "der"),
    ("tra", "de"),
    ("b", "uy"),
    ("se", "ll"),
    ("rec", "ommend"),
    ("private", "_token"),
    ("private", "_key"),
    ("position", "_size"),
)
_UNSAFE_TERMS = tuple("".join(parts) for parts in _UNSAFE_TERM_PARTS)
_DIGEST_FIELDS = (
    "forecast_yes_probability",
    "executable_yes_price",
    "executable_no_price",
    "evaluated_side",
    "side_forecast_probability",
    "executable_side_price",
    "apparent_edge_bps",
    "fee_drag_bps",
    "spread_drag_bps",
    "cash_lock_settlement_drag_bps",
    "forecast_uncertainty_band_bps",
    "total_drag_bps",
    "risk_adjusted_edge_bps",
    "minimum_pass_edge_bps",
    "margin_to_pass_bps",
    "decision_support_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class CandidateDecisionEvSensitivityScoreInput:
    forecast_yes_probability: Decimal
    executable_yes_price: Decimal
    executable_no_price: Decimal
    evaluated_side: str
    fee_drag_bps: Decimal
    spread_drag_bps: Decimal
    cash_lock_settlement_drag_bps: Decimal
    forecast_uncertainty_band_bps: Decimal
    minimum_pass_edge_bps: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "forecast_yes_probability",
            "executable_yes_price",
            "executable_no_price",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("evaluated_side", self.evaluated_side, EVALUATED_SIDES)
        for field_name in (
            "fee_drag_bps",
            "spread_drag_bps",
            "cash_lock_settlement_drag_bps",
            "forecast_uncertainty_band_bps",
            "minimum_pass_edge_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        reject_candidate_decision_ev_sensitivity_score_unsafe_payload(
            "EV sensitivity input",
            self,
        )
        _require_paper_flags("EV sensitivity input", self)


@dataclass(frozen=True)
class CandidateDecisionEvSensitivityScoreResult:
    forecast_yes_probability: Decimal
    executable_yes_price: Decimal
    executable_no_price: Decimal
    evaluated_side: str
    side_forecast_probability: Decimal
    executable_side_price: Decimal
    apparent_edge_bps: Decimal
    fee_drag_bps: Decimal
    spread_drag_bps: Decimal
    cash_lock_settlement_drag_bps: Decimal
    forecast_uncertainty_band_bps: Decimal
    total_drag_bps: Decimal
    risk_adjusted_edge_bps: Decimal
    minimum_pass_edge_bps: Decimal
    margin_to_pass_bps: Decimal
    decision_support_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "forecast_yes_probability",
            "executable_yes_price",
            "executable_no_price",
            "side_forecast_probability",
            "executable_side_price",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice("evaluated_side", self.evaluated_side, EVALUATED_SIDES)
        for field_name in (
            "fee_drag_bps",
            "spread_drag_bps",
            "cash_lock_settlement_drag_bps",
            "forecast_uncertainty_band_bps",
            "total_drag_bps",
            "minimum_pass_edge_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "apparent_edge_bps",
            "risk_adjusted_edge_bps",
            "margin_to_pass_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_choice(
            "decision_support_status",
            self.decision_support_status,
            DECISION_SUPPORT_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_result_consistency(self)
        reject_candidate_decision_ev_sensitivity_score_unsafe_payload(
            "EV sensitivity result",
            self,
        )
        _require_paper_flags("EV sensitivity result", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match result fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_ev_sensitivity_score_payload(self)


def estimate_candidate_decision_ev_sensitivity_score(
    score_input: CandidateDecisionEvSensitivityScoreInput,
) -> CandidateDecisionEvSensitivityScoreResult:
    if type(score_input) is not CandidateDecisionEvSensitivityScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionEvSensitivityScoreInput",
        )
    reject_candidate_decision_ev_sensitivity_score_unsafe_payload(
        "EV sensitivity input",
        score_input,
    )
    _require_paper_flags("EV sensitivity input", score_input)

    side_forecast_probability = _side_forecast_probability(
        score_input.forecast_yes_probability,
        score_input.evaluated_side,
    )
    executable_side_price = _executable_side_price(
        score_input.executable_yes_price,
        score_input.executable_no_price,
        score_input.evaluated_side,
    )
    apparent_edge_bps = _apparent_edge_bps(
        side_forecast_probability,
        executable_side_price,
    )
    total_drag_bps = _total_drag_bps(
        score_input.fee_drag_bps,
        score_input.spread_drag_bps,
        score_input.cash_lock_settlement_drag_bps,
        score_input.forecast_uncertainty_band_bps,
    )
    risk_adjusted_edge_bps = _normalize_decimal(
        "risk_adjusted_edge_bps",
        apparent_edge_bps - total_drag_bps,
    )
    margin_to_pass_bps = _normalize_decimal(
        "margin_to_pass_bps",
        risk_adjusted_edge_bps - score_input.minimum_pass_edge_bps,
    )
    decision_support_status = _decision_support_status(
        risk_adjusted_edge_bps,
        score_input.minimum_pass_edge_bps,
    )

    return CandidateDecisionEvSensitivityScoreResult(
        forecast_yes_probability=score_input.forecast_yes_probability,
        executable_yes_price=score_input.executable_yes_price,
        executable_no_price=score_input.executable_no_price,
        evaluated_side=score_input.evaluated_side,
        side_forecast_probability=side_forecast_probability,
        executable_side_price=executable_side_price,
        apparent_edge_bps=apparent_edge_bps,
        fee_drag_bps=score_input.fee_drag_bps,
        spread_drag_bps=score_input.spread_drag_bps,
        cash_lock_settlement_drag_bps=score_input.cash_lock_settlement_drag_bps,
        forecast_uncertainty_band_bps=score_input.forecast_uncertainty_band_bps,
        total_drag_bps=total_drag_bps,
        risk_adjusted_edge_bps=risk_adjusted_edge_bps,
        minimum_pass_edge_bps=score_input.minimum_pass_edge_bps,
        margin_to_pass_bps=margin_to_pass_bps,
        decision_support_status=decision_support_status,
        reason_codes=_reason_codes(
            score_input.reason_codes,
            evaluated_side=score_input.evaluated_side,
            apparent_edge_bps=apparent_edge_bps,
            fee_drag_bps=score_input.fee_drag_bps,
            spread_drag_bps=score_input.spread_drag_bps,
            cash_lock_settlement_drag_bps=score_input.cash_lock_settlement_drag_bps,
            forecast_uncertainty_band_bps=score_input.forecast_uncertainty_band_bps,
            risk_adjusted_edge_bps=risk_adjusted_edge_bps,
            minimum_pass_edge_bps=score_input.minimum_pass_edge_bps,
            decision_support_status=decision_support_status,
        ),
    )


def candidate_decision_ev_sensitivity_score_payload(
    result: CandidateDecisionEvSensitivityScoreResult,
) -> dict[str, Any]:
    if type(result) is not CandidateDecisionEvSensitivityScoreResult:
        raise ValueError(
            "result must be a CandidateDecisionEvSensitivityScoreResult",
        )
    _require_paper_flags("EV sensitivity result", result)
    if result.derived_validation_digest != _derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")
    reject_candidate_decision_ev_sensitivity_score_unsafe_payload(
        "EV sensitivity result",
        result,
    )
    payload = _json_ready(asdict(result))
    if type(payload) is not dict:
        raise ValueError("result payload must be a dict")
    reject_candidate_decision_ev_sensitivity_score_unsafe_payload(
        "EV sensitivity payload",
        payload,
    )
    return payload


def reject_candidate_decision_ev_sensitivity_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _side_forecast_probability(
    forecast_yes_probability: Decimal,
    evaluated_side: str,
) -> Decimal:
    if evaluated_side == "yes":
        return _normalize_unit_decimal(
            "side_forecast_probability",
            forecast_yes_probability,
        )
    if evaluated_side == "no":
        return _normalize_unit_decimal(
            "side_forecast_probability",
            ONE - forecast_yes_probability,
        )
    raise ValueError("evaluated_side must be one of supported values")


def _executable_side_price(
    executable_yes_price: Decimal,
    executable_no_price: Decimal,
    evaluated_side: str,
) -> Decimal:
    if evaluated_side == "yes":
        return _normalize_unit_decimal("executable_side_price", executable_yes_price)
    if evaluated_side == "no":
        return _normalize_unit_decimal("executable_side_price", executable_no_price)
    raise ValueError("evaluated_side must be one of supported values")


def _apparent_edge_bps(
    side_forecast_probability: Decimal,
    executable_side_price: Decimal,
) -> Decimal:
    return _normalize_decimal(
        "apparent_edge_bps",
        (side_forecast_probability - executable_side_price) * BPS_PER_ONE,
    )


def _total_drag_bps(
    fee_drag_bps: Decimal,
    spread_drag_bps: Decimal,
    cash_lock_settlement_drag_bps: Decimal,
    forecast_uncertainty_band_bps: Decimal,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        "total_drag_bps",
        fee_drag_bps
        + spread_drag_bps
        + cash_lock_settlement_drag_bps
        + forecast_uncertainty_band_bps,
    )


def _decision_support_status(
    risk_adjusted_edge_bps: Decimal,
    minimum_pass_edge_bps: Decimal,
) -> str:
    if risk_adjusted_edge_bps <= ZERO:
        return "block"
    if risk_adjusted_edge_bps < minimum_pass_edge_bps:
        return "watch"
    return "pass"


def _reason_codes(
    existing: tuple[str, ...],
    *,
    evaluated_side: str,
    apparent_edge_bps: Decimal,
    fee_drag_bps: Decimal,
    spread_drag_bps: Decimal,
    cash_lock_settlement_drag_bps: Decimal,
    forecast_uncertainty_band_bps: Decimal,
    risk_adjusted_edge_bps: Decimal,
    minimum_pass_edge_bps: Decimal,
    decision_support_status: str,
) -> tuple[str, ...]:
    additions = [
        "candidate_decision_ev_sensitivity_score",
        f"status_{decision_support_status}",
        f"side_{evaluated_side}",
        _apparent_edge_reason_code(apparent_edge_bps),
    ]
    if fee_drag_bps > ZERO:
        additions.append("fee_drag_applied")
    if spread_drag_bps > ZERO:
        additions.append("spread_drag_applied")
    if cash_lock_settlement_drag_bps > ZERO:
        additions.append("cash_lock_settlement_drag_applied")
    if forecast_uncertainty_band_bps > ZERO:
        additions.append("forecast_uncertainty_band_applied")
    if risk_adjusted_edge_bps <= ZERO:
        additions.append("adjusted_edge_nonpositive")
    elif risk_adjusted_edge_bps < minimum_pass_edge_bps:
        additions.append("positive_below_pass_threshold")
    else:
        additions.append("minimum_pass_edge_met")
    return _append_reason_codes(existing, tuple(additions))


def _apparent_edge_reason_code(apparent_edge_bps: Decimal) -> str:
    if apparent_edge_bps > ZERO:
        return "apparent_edge_positive"
    if apparent_edge_bps == ZERO:
        return "apparent_edge_flat"
    return "apparent_edge_negative"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_result_consistency(
    result: CandidateDecisionEvSensitivityScoreResult,
) -> None:
    if result.side_forecast_probability != _side_forecast_probability(
        result.forecast_yes_probability,
        result.evaluated_side,
    ):
        raise ValueError("side_forecast_probability must match forecast and side")
    if result.executable_side_price != _executable_side_price(
        result.executable_yes_price,
        result.executable_no_price,
        result.evaluated_side,
    ):
        raise ValueError("executable_side_price must match executable side input")
    if result.apparent_edge_bps != _apparent_edge_bps(
        result.side_forecast_probability,
        result.executable_side_price,
    ):
        raise ValueError("apparent_edge_bps must match forecast minus price")
    if result.total_drag_bps != _total_drag_bps(
        result.fee_drag_bps,
        result.spread_drag_bps,
        result.cash_lock_settlement_drag_bps,
        result.forecast_uncertainty_band_bps,
    ):
        raise ValueError("total_drag_bps must match drag inputs")
    if result.risk_adjusted_edge_bps != _normalize_decimal(
        "risk_adjusted_edge_bps",
        result.apparent_edge_bps - result.total_drag_bps,
    ):
        raise ValueError("risk_adjusted_edge_bps must match edge minus drag")
    if result.decision_support_status != _decision_support_status(
        result.risk_adjusted_edge_bps,
        result.minimum_pass_edge_bps,
    ):
        raise ValueError("decision_support_status must match adjusted edge")
    if result.margin_to_pass_bps != _normalize_decimal(
        "margin_to_pass_bps",
        result.risk_adjusted_edge_bps - result.minimum_pass_edge_bps,
    ):
        raise ValueError("margin_to_pass_bps must match pass threshold")


def _derived_validation_digest(
    result: CandidateDecisionEvSensitivityScoreResult,
) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(result, field_name))}"
        for field_name in _DIGEST_FIELDS
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        _require_safe_reason_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    return value


def _require_safe_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain strings")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical nonblank strings")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain lowercase values")
    first_character = value[0]
    if first_character < "a" or first_character > "z":
        raise ValueError(f"{field_name} must contain safe public taxonomy values")
    for character in value:
        if not (
            "a" <= character <= "z"
            or "0" <= character <= "9"
            or character == "_"
        ):
            raise ValueError(f"{field_name} must contain safe public taxonomy values")


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than 1")
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
    return value.quantize(QUANTUM)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_canonical_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    return ()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


__all__ = (
    "DECISION_SUPPORT_STATUSES",
    "EVALUATED_SIDES",
    "CandidateDecisionEvSensitivityScoreInput",
    "CandidateDecisionEvSensitivityScoreResult",
    "estimate_candidate_decision_ev_sensitivity_score",
    "candidate_decision_ev_sensitivity_score_payload",
    "reject_candidate_decision_ev_sensitivity_score_unsafe_payload",
)
