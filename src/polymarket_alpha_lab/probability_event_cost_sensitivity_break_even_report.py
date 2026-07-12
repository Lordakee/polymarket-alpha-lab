from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_PROBABILITY_EVENT_COST_SENSITIVITY_BREAK_EVEN_REPORT_VERSION",
    "ProbabilityEventCostSensitivityBreakEvenReport",
    "build_probability_event_cost_sensitivity_break_even_report",
    "probability_event_cost_sensitivity_break_even_report_payload",
)


DEFAULT_PROBABILITY_EVENT_COST_SENSITIVITY_BREAK_EVEN_REPORT_VERSION = (
    "probability-event-cost-sensitivity-break-even-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
BREAK_EVEN_STATUSES = frozenset(
    (
        "above_break_even",
        "at_break_even",
        "below_break_even",
    ),
)
REASON_CODES_BY_STATUS = {
    "above_break_even": (
        "probability_event_cost_sensitivity_headroom_positive",
    ),
    "at_break_even": (
        "probability_event_cost_sensitivity_headroom_zero",
    ),
    "below_break_even": (
        "probability_event_cost_sensitivity_headroom_negative",
    ),
}
MANUAL_NEXT_STEP_BY_STATUS = {
    "above_break_even": "manual_review_cost_headroom_before_paper_decision",
    "at_break_even": "manual_review_zero_headroom_before_paper_decision",
    "below_break_even": "manual_reprice_cost_assumptions_before_paper_decision",
}


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ProbabilityEventCostSensitivityBreakEvenReport(_FinalDataclass):
    config_version: str
    raw_edge_probability: Decimal
    base_cost_probability: Decimal
    stressed_cost_probability: Decimal
    slippage_shock_probability: Decimal
    uncertainty_buffer_probability: Decimal
    total_cost_probability: Decimal
    cost_headroom_probability: Decimal
    break_even_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventCostSensitivityBreakEvenReport,
            "report",
        )
        if (
            self.config_version
            != DEFAULT_PROBABILITY_EVENT_COST_SENSITIVITY_BREAK_EVEN_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported report version")
        for field_name in (
            "raw_edge_probability",
            "base_cost_probability",
            "stressed_cost_probability",
            "slippage_shock_probability",
            "uncertainty_buffer_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        expected_total_cost = _quantize_probability(
            self.base_cost_probability
            + self.stressed_cost_probability
            + self.slippage_shock_probability
            + self.uncertainty_buffer_probability,
        )
        object.__setattr__(
            self,
            "total_cost_probability",
            _require_probability_decimal(
                "total_cost_probability",
                self.total_cost_probability,
            ),
        )
        if self.total_cost_probability != expected_total_cost:
            raise ValueError("total_cost_probability must match cost component sum")
        expected_headroom = _quantize_delta_probability(
            self.raw_edge_probability - self.total_cost_probability,
        )
        object.__setattr__(
            self,
            "cost_headroom_probability",
            _require_delta_probability_decimal(
                "cost_headroom_probability",
                self.cost_headroom_probability,
            ),
        )
        if self.cost_headroom_probability != expected_headroom:
            raise ValueError("cost_headroom_probability must match raw edge less costs")
        if self.break_even_status not in BREAK_EVEN_STATUSES:
            raise ValueError("break_even_status must be supported")
        expected_status = _status_for_headroom(self.cost_headroom_probability)
        if self.break_even_status != expected_status:
            raise ValueError("break_even_status must match cost headroom")
        expected_reason_codes = REASON_CODES_BY_STATUS[expected_status]
        if self.reason_codes != expected_reason_codes:
            raise ValueError("reason_codes must match break_even_status")
        expected_next_step = MANUAL_NEXT_STEP_BY_STATUS[expected_status]
        if self.manual_next_step != expected_next_step:
            raise ValueError("manual_next_step must match break_even_status")
        _require_hard_flags("report", self)
        expected_digest = _payload_digest(_payload_without_digest(self))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return probability_event_cost_sensitivity_break_even_report_payload(self)


def build_probability_event_cost_sensitivity_break_even_report(
    *,
    raw_edge_probability: Decimal,
    base_cost_probability: Decimal,
    stressed_cost_probability: Decimal,
    slippage_shock_probability: Decimal,
    uncertainty_buffer_probability: Decimal,
) -> ProbabilityEventCostSensitivityBreakEvenReport:
    raw_edge = _require_probability_decimal(
        "raw_edge_probability",
        raw_edge_probability,
    )
    base_cost = _require_probability_decimal(
        "base_cost_probability",
        base_cost_probability,
    )
    stressed_cost = _require_probability_decimal(
        "stressed_cost_probability",
        stressed_cost_probability,
    )
    slippage_shock = _require_probability_decimal(
        "slippage_shock_probability",
        slippage_shock_probability,
    )
    uncertainty_buffer = _require_probability_decimal(
        "uncertainty_buffer_probability",
        uncertainty_buffer_probability,
    )
    total_cost = _quantize_probability(
        base_cost + stressed_cost + slippage_shock + uncertainty_buffer,
    )
    headroom = _quantize_delta_probability(raw_edge - total_cost)
    status = _status_for_headroom(headroom)
    report_values: dict[str, Any] = {
        "config_version": (
            DEFAULT_PROBABILITY_EVENT_COST_SENSITIVITY_BREAK_EVEN_REPORT_VERSION
        ),
        "raw_edge_probability": raw_edge,
        "base_cost_probability": base_cost,
        "stressed_cost_probability": stressed_cost,
        "slippage_shock_probability": slippage_shock,
        "uncertainty_buffer_probability": uncertainty_buffer,
        "total_cost_probability": total_cost,
        "cost_headroom_probability": headroom,
        "break_even_status": status,
        "reason_codes": REASON_CODES_BY_STATUS[status],
        "manual_next_step": MANUAL_NEXT_STEP_BY_STATUS[status],
    }
    payload = _payload_from_values(report_values)
    return ProbabilityEventCostSensitivityBreakEvenReport(
        **report_values,
        payload_digest=_payload_digest(payload),
    )


def probability_event_cost_sensitivity_break_even_report_payload(
    report: ProbabilityEventCostSensitivityBreakEvenReport,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        ProbabilityEventCostSensitivityBreakEvenReport,
        "report",
    )
    payload = _payload_without_digest(report)
    payload["payload_digest"] = report.payload_digest
    if payload["payload_digest"] != _payload_digest(_payload_without_digest(report)):
        raise ValueError("payload_digest must match report payload")
    return payload


def _payload_without_digest(
    report: ProbabilityEventCostSensitivityBreakEvenReport,
) -> dict[str, Any]:
    _require_hard_flags("report", report)
    return _payload_from_values(
        {
            "config_version": report.config_version,
            "raw_edge_probability": report.raw_edge_probability,
            "base_cost_probability": report.base_cost_probability,
            "stressed_cost_probability": report.stressed_cost_probability,
            "slippage_shock_probability": report.slippage_shock_probability,
            "uncertainty_buffer_probability": report.uncertainty_buffer_probability,
            "total_cost_probability": report.total_cost_probability,
            "cost_headroom_probability": report.cost_headroom_probability,
            "break_even_status": report.break_even_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
        },
    )


def _payload_from_values(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "config_version": values["config_version"],
        "raw_edge_probability": _decimal_text(values["raw_edge_probability"]),
        "base_cost_probability": _decimal_text(values["base_cost_probability"]),
        "stressed_cost_probability": _decimal_text(values["stressed_cost_probability"]),
        "slippage_shock_probability": _decimal_text(
            values["slippage_shock_probability"],
        ),
        "uncertainty_buffer_probability": _decimal_text(
            values["uncertainty_buffer_probability"],
        ),
        "total_cost_probability": _decimal_text(values["total_cost_probability"]),
        "cost_headroom_probability": _decimal_text(
            values["cost_headroom_probability"],
        ),
        "break_even_status": values["break_even_status"],
        "reason_codes": values["reason_codes"],
        "manual_next_step": values["manual_next_step"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_delta_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_delta_probability(value)


def _quantize_probability(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized == Decimal("-0.000000"):
        return ZERO
    return normalized


def _quantize_delta_probability(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized == Decimal("-0.000000"):
        return ZERO
    return normalized


def _status_for_headroom(headroom: Decimal) -> str:
    if headroom > ZERO:
        return "above_break_even"
    if headroom == ZERO:
        return "at_break_even"
    return "below_break_even"


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
