from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


ZERO = Decimal("0")
ONE = Decimal("1")
VALUE_QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

PASS_REASON = "operator_decision_threshold_policy_pass"
WATCH_REASON = "operator_decision_threshold_policy_watch"
BLOCK_REASON = "operator_decision_threshold_policy_block"

MANUAL_NEXT_STEP_PASS = "Proceed with paper-only operator review."
MANUAL_NEXT_STEP_WATCH = "Review watch reason codes before any paper-only operator decision."
MANUAL_NEXT_STEP_BLOCK = (
    "Manual override review required; keep the decision in paper-only mode."
)

MIN_NET_EDGE_PASS = Decimal("0.050000")
MIN_NET_EDGE_WATCH = Decimal("0.030000")
MIN_CONFIDENCE_PASS = Decimal("0.700000")
MIN_CONFIDENCE_WATCH = Decimal("0.600000")
MAX_COST_PASS = Decimal("0.050000")
MAX_COST_WATCH = Decimal("0.100000")
MAX_UNCERTAINTY_PASS = Decimal("0.200000")
MAX_UNCERTAINTY_WATCH = Decimal("0.250000")

REASON_CODE_SEQUENCE = (
    "net_edge_probability_ready",
    "net_edge_probability_watch",
    "net_edge_probability_below_minimum",
    "confidence_probability_ready",
    "confidence_probability_watch",
    "confidence_probability_below_minimum",
    "cost_probability_ready",
    "cost_probability_watch",
    "cost_probability_above_limit",
    "uncertainty_probability_ready",
    "uncertainty_probability_watch",
    "uncertainty_probability_above_limit",
    "manual_override_not_required",
    "manual_override_required",
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
)


@dataclass(frozen=True)
class OperatorDecisionThresholdPolicyReadinessReport:
    min_net_edge_probability: Decimal
    min_confidence_probability: Decimal
    max_cost_probability: Decimal
    max_uncertainty_probability: Decimal
    manual_override_required: bool
    policy_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: dict[str, Any]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorDecisionThresholdPolicyReadinessReport:
            raise TypeError(
                "OperatorDecisionThresholdPolicyReadinessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not OperatorDecisionThresholdPolicyReadinessReport:
            raise ValueError(
                "report must be exactly OperatorDecisionThresholdPolicyReadinessReport",
            )
        for field_name in (
            "min_net_edge_probability",
            "min_confidence_probability",
            "max_cost_probability",
            "max_uncertainty_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "manual_override_required",
            _require_bool("manual_override_required", self.manual_override_required),
        )
        _require_status("policy_status", self.policy_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_public_string("manual_next_step", self.manual_next_step)
        expected_status = _status_from_reason_codes(self.reason_codes)
        if self.policy_status != expected_status:
            raise ValueError("policy_status must match reason_codes")
        expected_next_step = _manual_next_step(self.policy_status)
        if self.manual_next_step != expected_next_step:
            raise ValueError("manual_next_step must match policy_status")
        require_paper_only_flags("report", self)
        expected_payload = _public_payload(
            min_net_edge_probability=self.min_net_edge_probability,
            min_confidence_probability=self.min_confidence_probability,
            max_cost_probability=self.max_cost_probability,
            max_uncertainty_probability=self.max_uncertainty_probability,
            manual_override_required=self.manual_override_required,
            policy_status=self.policy_status,
            reason_codes=self.reason_codes,
            manual_next_step=self.manual_next_step,
            paper_only=self.paper_only,
            report_only=self.report_only,
            readonly=self.readonly,
        )
        if self.public_payload != expected_payload:
            raise ValueError("public_payload must match report fields")
        reject_unsafe_surface_fields("public_payload", self.public_payload)
        expected_digest = _payload_digest(self.public_payload)
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public_payload")
        reject_unsafe_surface_fields("report", self)


def build_operator_decision_threshold_policy_readiness_report(
    *,
    min_net_edge_probability: Decimal,
    min_confidence_probability: Decimal,
    max_cost_probability: Decimal,
    max_uncertainty_probability: Decimal,
    manual_override_required: bool,
) -> OperatorDecisionThresholdPolicyReadinessReport:
    net_edge = _require_ratio_decimal(
        "min_net_edge_probability",
        min_net_edge_probability,
    )
    confidence = _require_ratio_decimal(
        "min_confidence_probability",
        min_confidence_probability,
    )
    cost = _require_ratio_decimal("max_cost_probability", max_cost_probability)
    uncertainty = _require_ratio_decimal(
        "max_uncertainty_probability",
        max_uncertainty_probability,
    )
    override_required = _require_bool(
        "manual_override_required",
        manual_override_required,
    )
    reason_codes = _reason_codes(
        min_net_edge_probability=net_edge,
        min_confidence_probability=confidence,
        max_cost_probability=cost,
        max_uncertainty_probability=uncertainty,
        manual_override_required=override_required,
    )
    policy_status = _status_from_reason_codes(reason_codes)
    manual_next_step = _manual_next_step(policy_status)
    public_payload = _public_payload(
        min_net_edge_probability=net_edge,
        min_confidence_probability=confidence,
        max_cost_probability=cost,
        max_uncertainty_probability=uncertainty,
        manual_override_required=override_required,
        policy_status=policy_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    return OperatorDecisionThresholdPolicyReadinessReport(
        min_net_edge_probability=net_edge,
        min_confidence_probability=confidence,
        max_cost_probability=cost,
        max_uncertainty_probability=uncertainty,
        manual_override_required=override_required,
        policy_status=policy_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        public_payload=public_payload,
        payload_digest=_payload_digest(public_payload),
    )


def _reason_codes(
    *,
    min_net_edge_probability: Decimal,
    min_confidence_probability: Decimal,
    max_cost_probability: Decimal,
    max_uncertainty_probability: Decimal,
    manual_override_required: bool,
) -> tuple[str, ...]:
    reason_codes = [
        _minimum_threshold_reason(
            value=min_net_edge_probability,
            pass_threshold=MIN_NET_EDGE_PASS,
            watch_threshold=MIN_NET_EDGE_WATCH,
            ready_reason="net_edge_probability_ready",
            watch_reason="net_edge_probability_watch",
            block_reason="net_edge_probability_below_minimum",
        ),
        _minimum_threshold_reason(
            value=min_confidence_probability,
            pass_threshold=MIN_CONFIDENCE_PASS,
            watch_threshold=MIN_CONFIDENCE_WATCH,
            ready_reason="confidence_probability_ready",
            watch_reason="confidence_probability_watch",
            block_reason="confidence_probability_below_minimum",
        ),
        _maximum_threshold_reason(
            value=max_cost_probability,
            pass_threshold=MAX_COST_PASS,
            watch_threshold=MAX_COST_WATCH,
            ready_reason="cost_probability_ready",
            watch_reason="cost_probability_watch",
            block_reason="cost_probability_above_limit",
        ),
        _maximum_threshold_reason(
            value=max_uncertainty_probability,
            pass_threshold=MAX_UNCERTAINTY_PASS,
            watch_threshold=MAX_UNCERTAINTY_WATCH,
            ready_reason="uncertainty_probability_ready",
            watch_reason="uncertainty_probability_watch",
            block_reason="uncertainty_probability_above_limit",
        ),
        (
            "manual_override_required"
            if manual_override_required
            else "manual_override_not_required"
        ),
    ]
    if (
        any(reason_code.endswith("_below_minimum") for reason_code in reason_codes)
        or any(reason_code.endswith("_above_limit") for reason_code in reason_codes)
        or manual_override_required
    ):
        reason_codes.append(BLOCK_REASON)
    elif any(reason_code.endswith("_watch") for reason_code in reason_codes):
        reason_codes.append(WATCH_REASON)
    else:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _minimum_threshold_reason(
    *,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    ready_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= pass_threshold:
        return ready_reason
    if value >= watch_threshold:
        return watch_reason
    return block_reason


def _maximum_threshold_reason(
    *,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    ready_reason: str,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value <= pass_threshold:
        return ready_reason
    if value <= watch_threshold:
        return watch_reason
    return block_reason


def _public_payload(
    *,
    min_net_edge_probability: Decimal,
    min_confidence_probability: Decimal,
    max_cost_probability: Decimal,
    max_uncertainty_probability: Decimal,
    manual_override_required: bool,
    policy_status: str,
    reason_codes: tuple[str, ...],
    manual_next_step: str,
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, Any]:
    payload = {
        "manual_next_step": manual_next_step,
        "manual_override_required": manual_override_required,
        "max_cost_probability": str(max_cost_probability),
        "max_uncertainty_probability": str(max_uncertainty_probability),
        "min_confidence_probability": str(min_confidence_probability),
        "min_net_edge_probability": str(min_net_edge_probability),
        "paper_only": paper_only,
        "policy_status": policy_status,
        "readonly": readonly,
        "reason_codes": list(reason_codes),
        "report_only": report_only,
    }
    reject_unsafe_surface_fields("payload", payload)
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _manual_next_step(policy_status: str) -> str:
    if policy_status == STATUS_PASS:
        return MANUAL_NEXT_STEP_PASS
    if policy_status == STATUS_WATCH:
        return MANUAL_NEXT_STEP_WATCH
    if policy_status == STATUS_BLOCK:
        return MANUAL_NEXT_STEP_BLOCK
    raise ValueError("policy_status must be pass, watch, or block")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return STATUS_BLOCK
    if WATCH_REASON in reason_codes:
        return STATUS_WATCH
    if PASS_REASON in reason_codes:
        return STATUS_PASS
    raise ValueError("reason_codes must include a terminal policy reason")


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        normalized.append(reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return tuple(normalized)


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} is not an allowed reason code")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be a single-line string")
    return value


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


__all__ = (
    "OperatorDecisionThresholdPolicyReadinessReport",
    "build_operator_decision_threshold_policy_readiness_report",
)
