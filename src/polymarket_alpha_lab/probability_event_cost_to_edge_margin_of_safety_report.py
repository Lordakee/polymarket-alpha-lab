"""Pure cost-to-edge margin of safety report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json


STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
MARGIN_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

REASON_PREFIX = "probability_event_cost_to_edge_margin_of_safety_"
PASS_REASON = REASON_PREFIX + STATUS_PASS
COSTS_EXCEED_RAW_EDGE_REASON = REASON_PREFIX + "costs_exceed_raw_edge"
NO_POSITIVE_MARGIN_REASON = REASON_PREFIX + "no_positive_margin"

PASS_MANUAL_NEXT_STEP = "document_cost_adjusted_edge_for_manual_phase1_review"
WATCH_MANUAL_NEXT_STEP = "tighten_cost_inputs_before_manual_review"
BLOCKED_MANUAL_NEXT_STEP = "block_manual_review_until_edge_exceeds_costs"
MANUAL_NEXT_STEPS = (
    PASS_MANUAL_NEXT_STEP,
    WATCH_MANUAL_NEXT_STEP,
    BLOCKED_MANUAL_NEXT_STEP,
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

INPUT_PROBABILITY_FIELDS = (
    "raw_edge_probability",
    "taker_fee_probability",
    "estimated_slippage_probability",
    "settlement_cost_probability",
    "uncertainty_buffer_probability",
)
REPORT_PROBABILITY_FIELDS = (
    *INPUT_PROBABILITY_FIELDS,
    "net_edge_probability",
    "margin_of_safety_probability",
)
PAYLOAD_KEYS = (
    *REPORT_PROBABILITY_FIELDS,
    "margin_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "MARGIN_STATUSES",
    "ProbabilityEventCostToEdgeMarginOfSafetyInput",
    "ProbabilityEventCostToEdgeMarginOfSafetyReport",
    "build_probability_event_cost_to_edge_margin_of_safety_report",
    "probability_event_cost_to_edge_margin_of_safety_report_digest",
    "probability_event_cost_to_edge_margin_of_safety_report_to_payload",
    "validate_probability_event_cost_to_edge_margin_of_safety_public_payload",
)


@dataclass(frozen=True)
class ProbabilityEventCostToEdgeMarginOfSafetyInput:
    raw_edge_probability: Decimal
    taker_fee_probability: Decimal
    estimated_slippage_probability: Decimal
    settlement_cost_probability: Decimal
    uncertainty_buffer_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventCostToEdgeMarginOfSafetyInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventCostToEdgeMarginOfSafetyInput,
            "input",
        )
        for field_name in INPUT_PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventCostToEdgeMarginOfSafetyReport:
    raw_edge_probability: Decimal
    taker_fee_probability: Decimal
    estimated_slippage_probability: Decimal
    settlement_cost_probability: Decimal
    uncertainty_buffer_probability: Decimal
    net_edge_probability: Decimal
    margin_of_safety_probability: Decimal
    margin_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventCostToEdgeMarginOfSafetyReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventCostToEdgeMarginOfSafetyReport,
            "report",
        )
        for field_name in REPORT_PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "margin_status",
            _require_margin_status("margin_status", self.margin_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step("manual_next_step", self.manual_next_step),
        )
        _require_sha256_digest("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _digest_payload(_payload_from_report(self))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_cost_to_edge_margin_of_safety_report_to_payload(self)


def build_probability_event_cost_to_edge_margin_of_safety_report(
    source: ProbabilityEventCostToEdgeMarginOfSafetyInput,
) -> ProbabilityEventCostToEdgeMarginOfSafetyReport:
    if type(source) is not ProbabilityEventCostToEdgeMarginOfSafetyInput:
        raise ValueError(
            "source must be a ProbabilityEventCostToEdgeMarginOfSafetyInput",
        )
    _require_hard_flags("source", source)
    derived = _derived_values(
        raw_edge_probability=source.raw_edge_probability,
        taker_fee_probability=source.taker_fee_probability,
        estimated_slippage_probability=source.estimated_slippage_probability,
        settlement_cost_probability=source.settlement_cost_probability,
        uncertainty_buffer_probability=source.uncertainty_buffer_probability,
    )
    values: dict[str, object] = {
        "raw_edge_probability": source.raw_edge_probability,
        "taker_fee_probability": source.taker_fee_probability,
        "estimated_slippage_probability": source.estimated_slippage_probability,
        "settlement_cost_probability": source.settlement_cost_probability,
        "uncertainty_buffer_probability": source.uncertainty_buffer_probability,
        **derived,
    }
    digest = _digest_payload(_payload_from_values(values))
    return ProbabilityEventCostToEdgeMarginOfSafetyReport(
        **values,
        payload_digest=digest,
    )


def probability_event_cost_to_edge_margin_of_safety_report_to_payload(
    report: ProbabilityEventCostToEdgeMarginOfSafetyReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventCostToEdgeMarginOfSafetyReport:
        raise ValueError(
            "report must be a ProbabilityEventCostToEdgeMarginOfSafetyReport",
        )
    _validate_report(report)
    _require_hard_flags("report", report)
    expected_digest = _digest_payload(_payload_from_report(report))
    if report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match public payload")
    payload = _payload_from_report(report)
    validate_probability_event_cost_to_edge_margin_of_safety_public_payload(payload)
    return payload


def probability_event_cost_to_edge_margin_of_safety_report_digest(
    report: ProbabilityEventCostToEdgeMarginOfSafetyReport,
) -> str:
    payload = probability_event_cost_to_edge_margin_of_safety_report_to_payload(report)
    return _digest_payload(payload)


def validate_probability_event_cost_to_edge_margin_of_safety_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical schema")
    inputs = {
        field_name: _require_payload_decimal(field_name, payload[field_name])
        for field_name in INPUT_PROBABILITY_FIELDS
    }
    expected = _derived_values(**inputs)
    for field_name in ("net_edge_probability", "margin_of_safety_probability"):
        parsed = _require_payload_decimal(field_name, payload[field_name])
        if parsed != expected[field_name]:
            raise ValueError(f"{field_name} must match cost-to-edge inputs")
    if payload["margin_status"] != expected["margin_status"]:
        raise ValueError("margin_status must match cost-to-edge inputs")
    reason_codes = _normalize_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
    )
    if reason_codes != expected["reason_codes"]:
        raise ValueError("reason_codes must match cost-to-edge inputs")
    if payload["manual_next_step"] != expected["manual_next_step"]:
        raise ValueError("manual_next_step must match cost-to-edge inputs")
    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, payload[field_name])
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    return payload


def _derived_values(
    *,
    raw_edge_probability: Decimal,
    taker_fee_probability: Decimal,
    estimated_slippage_probability: Decimal,
    settlement_cost_probability: Decimal,
    uncertainty_buffer_probability: Decimal,
) -> dict[str, object]:
    net_edge_probability = _require_decimal(
        "net_edge_probability",
        raw_edge_probability
        - taker_fee_probability
        - estimated_slippage_probability
        - settlement_cost_probability,
    )
    margin_of_safety_probability = _require_decimal(
        "margin_of_safety_probability",
        net_edge_probability - uncertainty_buffer_probability,
    )
    if net_edge_probability < ZERO:
        return {
            "net_edge_probability": net_edge_probability,
            "margin_of_safety_probability": margin_of_safety_probability,
            "margin_status": STATUS_BLOCKED,
            "reason_codes": (
                COSTS_EXCEED_RAW_EDGE_REASON,
                NO_POSITIVE_MARGIN_REASON,
            ),
            "manual_next_step": BLOCKED_MANUAL_NEXT_STEP,
        }
    if margin_of_safety_probability <= ZERO:
        return {
            "net_edge_probability": net_edge_probability,
            "margin_of_safety_probability": margin_of_safety_probability,
            "margin_status": STATUS_WATCH,
            "reason_codes": (NO_POSITIVE_MARGIN_REASON,),
            "manual_next_step": WATCH_MANUAL_NEXT_STEP,
        }
    return {
        "net_edge_probability": net_edge_probability,
        "margin_of_safety_probability": margin_of_safety_probability,
        "margin_status": STATUS_PASS,
        "reason_codes": (PASS_REASON,),
        "manual_next_step": PASS_MANUAL_NEXT_STEP,
    }


def _validate_report(
    report: ProbabilityEventCostToEdgeMarginOfSafetyReport,
) -> None:
    expected = _derived_values(
        raw_edge_probability=report.raw_edge_probability,
        taker_fee_probability=report.taker_fee_probability,
        estimated_slippage_probability=report.estimated_slippage_probability,
        settlement_cost_probability=report.settlement_cost_probability,
        uncertainty_buffer_probability=report.uncertainty_buffer_probability,
    )
    for field_name in (
        "net_edge_probability",
        "margin_of_safety_probability",
        "margin_status",
        "reason_codes",
        "manual_next_step",
    ):
        if getattr(report, field_name) != expected[field_name]:
            raise ValueError(f"{field_name} must match cost-to-edge inputs")


def _payload_from_report(
    report: ProbabilityEventCostToEdgeMarginOfSafetyReport,
) -> dict[str, object]:
    return _payload_from_values(
        {
            field_name: getattr(report, field_name)
            for field_name in PAYLOAD_KEYS
            if field_name not in ("paper_only", "report_only", "readonly")
        },
    )


def _payload_from_values(values: Mapping[str, object]) -> dict[str, object]:
    return {
        "raw_edge_probability": _decimal_text(values["raw_edge_probability"]),
        "taker_fee_probability": _decimal_text(values["taker_fee_probability"]),
        "estimated_slippage_probability": _decimal_text(
            values["estimated_slippage_probability"],
        ),
        "settlement_cost_probability": _decimal_text(
            values["settlement_cost_probability"],
        ),
        "uncertainty_buffer_probability": _decimal_text(
            values["uncertainty_buffer_probability"],
        ),
        "net_edge_probability": _decimal_text(values["net_edge_probability"]),
        "margin_of_safety_probability": _decimal_text(
            values["margin_of_safety_probability"],
        ),
        "margin_status": values["margin_status"],
        "reason_codes": list(values["reason_codes"]),  # type: ignore[arg-type]
        "manual_next_step": values["manual_next_step"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value)


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_code_items(field_name, tuple(value))


def _normalize_reason_code_items(
    field_name: str,
    value: tuple[object, ...],
) -> tuple[str, ...]:
    allowed = (
        PASS_REASON,
        COSTS_EXCEED_RAW_EDGE_REASON,
        NO_POSITIVE_MARGIN_REASON,
    )
    seen: set[str] = set()
    for item in value:
        if type(item) is not str or item not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
    canonical = tuple(item for item in allowed if item in seen)
    if value != canonical:
        raise ValueError(f"{field_name} must use canonical sequence")
    return canonical


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _require_margin_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MARGIN_STATUSES:
        raise ValueError(f"{field_name} must be a supported margin status")
    return value


def _require_manual_next_step(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a supported manual next step")
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized as a string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if parsed != _require_decimal(field_name, parsed):
        raise ValueError(f"{field_name} must be quantized to six places")
    if field_name in INPUT_PROBABILITY_FIELDS and (parsed < ZERO or parsed > ONE):
        raise ValueError(f"{field_name} must be between 0 and 1")
    return parsed


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    allowed = set("0123456789abcdef")
    if any(item not in allowed for item in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _decimal_text(value: object) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload Decimal value must be a Decimal")
    return format(_require_decimal("payload Decimal value", value), "f")


def _digest_payload(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
