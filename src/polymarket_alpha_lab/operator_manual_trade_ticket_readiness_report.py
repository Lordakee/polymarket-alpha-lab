"""Read-only Phase 1 report for human trade-ticket review readiness."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Mapping

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


__all__ = (
    "OperatorManualTradeTicketReadinessInput",
    "OperatorManualTradeTicketReadinessReport",
    "build_operator_manual_trade_ticket_readiness_report",
    "operator_manual_trade_ticket_readiness_report_payload_digest",
    "validate_operator_manual_trade_ticket_readiness_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")

READY_STATUS = "ready_for_manual_review"
BLOCKED_STATUS = "blocked_for_manual_review"
READY_REASON = "manual_trade_ticket_ready_for_human_review"
READY_NEXT_STEP = "human_review_ticket_before_any_external_action"
BLOCKED_NEXT_STEP = "do_not_prepare_ticket_until_reasons_are_resolved"

REASON_SEQUENCE = (
    "missing_market_reference",
    "missing_outcome_reference",
    "missing_side_label",
    "manual_size_not_positive",
    "net_edge_not_positive",
    "upstream_gates_not_passed",
    READY_REASON,
)
BLOCKED_REASON_SEQUENCE = REASON_SEQUENCE[:-1]

PAYLOAD_KEYS = (
    "market_ref_present",
    "outcome_ref_present",
    "side_label_present",
    "max_manual_size_probability",
    "net_edge_probability",
    "all_gates_passed",
    "ticket_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class _NoSubclassing:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _NoSubclassing and issubclass(base, _NoSubclassing):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class OperatorManualTradeTicketReadinessInput(_NoSubclassing):
    market_ref_present: bool
    outcome_ref_present: bool
    side_label_present: bool
    max_manual_size_probability: Decimal
    net_edge_probability: Decimal
    all_gates_passed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            OperatorManualTradeTicketReadinessInput,
            "readiness input",
        )
        for field_name in (
            "market_ref_present",
            "outcome_ref_present",
            "side_label_present",
            "all_gates_passed",
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "max_manual_size_probability",
            _normalize_probability(
                "max_manual_size_probability",
                self.max_manual_size_probability,
                allow_negative=False,
            ),
        )
        object.__setattr__(
            self,
            "net_edge_probability",
            _normalize_probability(
                "net_edge_probability",
                self.net_edge_probability,
                allow_negative=True,
            ),
        )


@dataclass(frozen=True)
class OperatorManualTradeTicketReadinessReport(_NoSubclassing):
    market_ref_present: bool
    outcome_ref_present: bool
    side_label_present: bool
    max_manual_size_probability: Decimal
    net_edge_probability: Decimal
    all_gates_passed: bool
    ticket_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            OperatorManualTradeTicketReadinessReport,
            "readiness report",
        )
        for field_name in (
            "market_ref_present",
            "outcome_ref_present",
            "side_label_present",
            "all_gates_passed",
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "max_manual_size_probability",
            _normalize_probability(
                "max_manual_size_probability",
                self.max_manual_size_probability,
                allow_negative=False,
            ),
        )
        object.__setattr__(
            self,
            "net_edge_probability",
            _normalize_probability(
                "net_edge_probability",
                self.net_edge_probability,
                allow_negative=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        expected_digest = _digest_payload(_payload_without_digest(self))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return _report_to_payload(self)


def build_operator_manual_trade_ticket_readiness_report(
    readiness: OperatorManualTradeTicketReadinessInput,
) -> OperatorManualTradeTicketReadinessReport:
    if type(readiness) is not OperatorManualTradeTicketReadinessInput:
        raise ValueError(
            "readiness must be an OperatorManualTradeTicketReadinessInput",
        )

    reason_codes = _derived_reason_codes(
        market_ref_present=readiness.market_ref_present,
        outcome_ref_present=readiness.outcome_ref_present,
        side_label_present=readiness.side_label_present,
        max_manual_size_probability=readiness.max_manual_size_probability,
        net_edge_probability=readiness.net_edge_probability,
        all_gates_passed=readiness.all_gates_passed,
    )
    ticket_status = _status_for_reasons(reason_codes)
    manual_next_step = _next_step_for_status(ticket_status)
    digest_source = {
        "market_ref_present": readiness.market_ref_present,
        "outcome_ref_present": readiness.outcome_ref_present,
        "side_label_present": readiness.side_label_present,
        "max_manual_size_probability": readiness.max_manual_size_probability,
        "net_edge_probability": readiness.net_edge_probability,
        "all_gates_passed": readiness.all_gates_passed,
        "ticket_status": ticket_status,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload_digest = _digest_payload(_json_object(digest_source))

    return OperatorManualTradeTicketReadinessReport(
        market_ref_present=readiness.market_ref_present,
        outcome_ref_present=readiness.outcome_ref_present,
        side_label_present=readiness.side_label_present,
        max_manual_size_probability=readiness.max_manual_size_probability,
        net_edge_probability=readiness.net_edge_probability,
        all_gates_passed=readiness.all_gates_passed,
        ticket_status=ticket_status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        payload_digest=payload_digest,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def operator_manual_trade_ticket_readiness_report_payload_digest(
    report: OperatorManualTradeTicketReadinessReport,
) -> str:
    if type(report) is not OperatorManualTradeTicketReadinessReport:
        raise ValueError(
            "report must be an OperatorManualTradeTicketReadinessReport",
        )
    _validate_report(report)
    return _digest_payload(_payload_without_digest(report))


def validate_operator_manual_trade_ticket_readiness_public_payload(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical readiness schema")

    for field_name in (
        "market_ref_present",
        "outcome_ref_present",
        "side_label_present",
        "all_gates_passed",
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")

    max_manual_size_probability = _decimal_from_payload(
        "max_manual_size_probability",
        payload["max_manual_size_probability"],
        allow_negative=False,
    )
    net_edge_probability = _decimal_from_payload(
        "net_edge_probability",
        payload["net_edge_probability"],
        allow_negative=True,
    )
    reason_codes = _normalize_payload_reason_codes(payload["reason_codes"])
    expected_reason_codes = _derived_reason_codes(
        market_ref_present=payload["market_ref_present"],  # type: ignore[arg-type]
        outcome_ref_present=payload["outcome_ref_present"],  # type: ignore[arg-type]
        side_label_present=payload["side_label_present"],  # type: ignore[arg-type]
        max_manual_size_probability=max_manual_size_probability,
        net_edge_probability=net_edge_probability,
        all_gates_passed=payload["all_gates_passed"],  # type: ignore[arg-type]
    )
    if reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match readiness fields")

    expected_status = _status_for_reasons(reason_codes)
    if payload["ticket_status"] != expected_status:
        raise ValueError("ticket_status must match reason_codes")
    expected_next_step = _next_step_for_status(expected_status)
    if payload["manual_next_step"] != expected_next_step:
        raise ValueError("manual_next_step must match ticket_status")
    if type(payload["payload_digest"]) is not str:
        raise ValueError("payload_digest must be a string")
    digest_source = dict(payload)
    digest_source.pop("payload_digest")
    if payload["payload_digest"] != _digest_payload(digest_source):
        raise ValueError("payload_digest must match public payload")
    return True


def _report_to_payload(
    report: OperatorManualTradeTicketReadinessReport,
) -> dict[str, object]:
    if type(report) is not OperatorManualTradeTicketReadinessReport:
        raise ValueError(
            "report must be an OperatorManualTradeTicketReadinessReport",
        )
    _validate_report(report)
    payload = _payload_without_digest(report)
    payload["payload_digest"] = report.payload_digest
    validate_operator_manual_trade_ticket_readiness_public_payload(payload)
    return payload


def _payload_without_digest(
    report: OperatorManualTradeTicketReadinessReport,
) -> dict[str, object]:
    return _json_object(
        {
            "market_ref_present": report.market_ref_present,
            "outcome_ref_present": report.outcome_ref_present,
            "side_label_present": report.side_label_present,
            "max_manual_size_probability": report.max_manual_size_probability,
            "net_edge_probability": report.net_edge_probability,
            "all_gates_passed": report.all_gates_passed,
            "ticket_status": report.ticket_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _validate_report(report: OperatorManualTradeTicketReadinessReport) -> None:
    expected_reason_codes = _derived_reason_codes(
        market_ref_present=report.market_ref_present,
        outcome_ref_present=report.outcome_ref_present,
        side_label_present=report.side_label_present,
        max_manual_size_probability=report.max_manual_size_probability,
        net_edge_probability=report.net_edge_probability,
        all_gates_passed=report.all_gates_passed,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match readiness fields")
    expected_status = _status_for_reasons(report.reason_codes)
    if report.ticket_status != expected_status:
        raise ValueError("ticket_status must match reason_codes")
    expected_next_step = _next_step_for_status(expected_status)
    if report.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match ticket_status")


def _derived_reason_codes(
    *,
    market_ref_present: bool,
    outcome_ref_present: bool,
    side_label_present: bool,
    max_manual_size_probability: Decimal,
    net_edge_probability: Decimal,
    all_gates_passed: bool,
) -> tuple[str, ...]:
    blocked: list[str] = []
    if market_ref_present is not True:
        blocked.append("missing_market_reference")
    if outcome_ref_present is not True:
        blocked.append("missing_outcome_reference")
    if side_label_present is not True:
        blocked.append("missing_side_label")
    if max_manual_size_probability <= ZERO:
        blocked.append("manual_size_not_positive")
    if net_edge_probability <= ZERO:
        blocked.append("net_edge_not_positive")
    if all_gates_passed is not True:
        blocked.append("upstream_gates_not_passed")
    if blocked:
        return tuple(reason for reason in BLOCKED_REASON_SEQUENCE if reason in blocked)
    return (READY_REASON,)


def _status_for_reasons(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return READY_STATUS
    return BLOCKED_STATUS


def _next_step_for_status(ticket_status: str) -> str:
    if ticket_status == READY_STATUS:
        return READY_NEXT_STEP
    if ticket_status == BLOCKED_STATUS:
        return BLOCKED_NEXT_STEP
    raise ValueError("ticket_status must be supported")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    return _normalize_reason_code_items(value)


def _normalize_payload_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(tuple(value))
    if type(value) is tuple:
        return _normalize_reason_code_items(value)
    raise ValueError("reason_codes must be a list")


def _normalize_reason_code_items(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_SEQUENCE:
            raise ValueError("reason_codes contains unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    canonical_reason_codes = tuple(reason for reason in REASON_SEQUENCE if reason in seen)
    if reason_codes != canonical_reason_codes:
        raise ValueError("reason_codes must use canonical sequence")
    if READY_REASON in seen and len(seen) != 1:
        raise ValueError("reason_codes cannot mix ready and blocked findings")
    return canonical_reason_codes


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_probability(
    field_name: str,
    value: object,
    *,
    allow_negative: bool,
) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if allow_negative:
        return normalized
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _decimal_from_payload(
    field_name: str,
    value: object,
    *,
    allow_negative: bool,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized as a string")
    return _normalize_probability(
        field_name,
        Decimal(value),
        allow_negative=allow_negative,
    )


def _json_object(value: dict[str, object]) -> dict[str, object]:
    payload = json_ready_no_floats(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _digest_payload(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
