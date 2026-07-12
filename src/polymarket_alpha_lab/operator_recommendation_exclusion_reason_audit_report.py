"""Read-only Phase 1 report for candidate exclusion reason coverage."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Mapping

from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats


__all__ = (
    "OperatorRecommendationExclusionReasonAuditReport",
    "build_operator_recommendation_exclusion_reason_audit_report",
    "operator_recommendation_exclusion_reason_audit_report_payload_digest",
    "validate_operator_recommendation_exclusion_reason_audit_public_payload",
)


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
WHOLE = Decimal("1.000000")

COMPLETE_STATUS = "exclusion_reasons_complete"
ATTENTION_STATUS = "exclusion_reasons_need_manual_attention"
COMPLETE_NEXT_STEP = "manual_review_excluded_candidates_before_queue_changes"
ATTENTION_NEXT_STEP = "fill_missing_exclusion_reasons_before_any_queue_change"

REASON_SEQUENCE = (
    "no_excluded_candidates_to_audit",
    "excluded_candidates_missing_reasons",
    "no_cost_block_exclusions_recorded",
    "cost_block_reasons_present",
    "no_source_block_exclusions_recorded",
    "source_block_reasons_present",
    "no_risk_block_exclusions_recorded",
    "risk_block_reasons_present",
)
READY_REASONS = (
    "cost_block_reasons_present",
    "source_block_reasons_present",
    "risk_block_reasons_present",
)
PAYLOAD_KEYS = (
    "excluded_candidate_count",
    "missing_reason_count",
    "cost_block_count",
    "source_block_count",
    "risk_block_count",
    "exclusion_audit_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class OperatorRecommendationExclusionReasonAuditReport(_FinalDataclass):
    excluded_candidate_count: Decimal
    missing_reason_count: Decimal
    cost_block_count: Decimal
    source_block_count: Decimal
    risk_block_count: Decimal
    exclusion_audit_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            OperatorRecommendationExclusionReasonAuditReport,
            "report",
        )
        for field_name in (
            "excluded_candidate_count",
            "missing_reason_count",
            "cost_block_count",
            "source_block_count",
            "risk_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags(self)
        _validate_report(self)
        expected_digest = _digest_payload(_payload_without_digest(self))
        if self.payload_digest != expected_digest:
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return _report_to_payload(self)


def build_operator_recommendation_exclusion_reason_audit_report(
    *,
    excluded_candidate_count: Decimal,
    missing_reason_count: Decimal,
    cost_block_count: Decimal,
    source_block_count: Decimal,
    risk_block_count: Decimal,
) -> OperatorRecommendationExclusionReasonAuditReport:
    values = {
        "excluded_candidate_count": _require_count_decimal(
            "excluded_candidate_count",
            excluded_candidate_count,
        ),
        "missing_reason_count": _require_count_decimal(
            "missing_reason_count",
            missing_reason_count,
        ),
        "cost_block_count": _require_count_decimal("cost_block_count", cost_block_count),
        "source_block_count": _require_count_decimal(
            "source_block_count",
            source_block_count,
        ),
        "risk_block_count": _require_count_decimal("risk_block_count", risk_block_count),
    }
    reason_codes = _derived_reason_codes(**values)
    status = _status_for_reasons(reason_codes)
    manual_next_step = _next_step_for_status(status)
    digest_source = _json_object(
        {
            **values,
            "exclusion_audit_status": status,
            "reason_codes": reason_codes,
            "manual_next_step": manual_next_step,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    return OperatorRecommendationExclusionReasonAuditReport(
        **values,
        exclusion_audit_status=status,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        payload_digest=_digest_payload(digest_source),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def operator_recommendation_exclusion_reason_audit_report_payload_digest(
    report: OperatorRecommendationExclusionReasonAuditReport,
) -> str:
    if type(report) is not OperatorRecommendationExclusionReasonAuditReport:
        raise ValueError(
            "report must be an OperatorRecommendationExclusionReasonAuditReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    return _digest_payload(_payload_without_digest(report))


def validate_operator_recommendation_exclusion_reason_audit_public_payload(
    payload: Mapping[str, object],
) -> bool:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical exclusion audit schema")

    for field_name in ("paper_only", "report_only", "readonly"):
        _require_bool(field_name, payload[field_name])
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")

    counts = {
        "excluded_candidate_count": _decimal_from_payload(
            "excluded_candidate_count",
            payload["excluded_candidate_count"],
        ),
        "missing_reason_count": _decimal_from_payload(
            "missing_reason_count",
            payload["missing_reason_count"],
        ),
        "cost_block_count": _decimal_from_payload(
            "cost_block_count",
            payload["cost_block_count"],
        ),
        "source_block_count": _decimal_from_payload(
            "source_block_count",
            payload["source_block_count"],
        ),
        "risk_block_count": _decimal_from_payload(
            "risk_block_count",
            payload["risk_block_count"],
        ),
    }
    reason_codes = _normalize_payload_reason_codes(payload["reason_codes"])
    expected_reason_codes = _derived_reason_codes(**counts)
    if reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match exclusion audit counts")

    expected_status = _status_for_reasons(reason_codes)
    if payload["exclusion_audit_status"] != expected_status:
        raise ValueError("exclusion_audit_status must match reason_codes")
    expected_next_step = _next_step_for_status(expected_status)
    if payload["manual_next_step"] != expected_next_step:
        raise ValueError("manual_next_step must match exclusion_audit_status")
    if type(payload["payload_digest"]) is not str:
        raise ValueError("payload_digest must be a string")
    digest_source = dict(payload)
    digest_source.pop("payload_digest")
    if payload["payload_digest"] != _digest_payload(digest_source):
        raise ValueError("payload_digest must match public payload")
    return True


def _report_to_payload(
    report: OperatorRecommendationExclusionReasonAuditReport,
) -> dict[str, object]:
    if type(report) is not OperatorRecommendationExclusionReasonAuditReport:
        raise ValueError(
            "report must be an OperatorRecommendationExclusionReasonAuditReport",
        )
    _require_hard_flags(report)
    _validate_report(report)
    if report.payload_digest != _digest_payload(_payload_without_digest(report)):
        raise ValueError("payload_digest must match public payload")
    payload = _payload_without_digest(report)
    payload["payload_digest"] = report.payload_digest
    validate_operator_recommendation_exclusion_reason_audit_public_payload(payload)
    return payload


def _payload_without_digest(
    report: OperatorRecommendationExclusionReasonAuditReport,
) -> dict[str, object]:
    return _json_object(
        {
            "excluded_candidate_count": report.excluded_candidate_count,
            "missing_reason_count": report.missing_reason_count,
            "cost_block_count": report.cost_block_count,
            "source_block_count": report.source_block_count,
            "risk_block_count": report.risk_block_count,
            "exclusion_audit_status": report.exclusion_audit_status,
            "reason_codes": report.reason_codes,
            "manual_next_step": report.manual_next_step,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _validate_report(
    report: OperatorRecommendationExclusionReasonAuditReport,
) -> None:
    expected_reason_codes = _derived_reason_codes(
        excluded_candidate_count=report.excluded_candidate_count,
        missing_reason_count=report.missing_reason_count,
        cost_block_count=report.cost_block_count,
        source_block_count=report.source_block_count,
        risk_block_count=report.risk_block_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match exclusion audit counts")
    expected_status = _status_for_reasons(report.reason_codes)
    if report.exclusion_audit_status != expected_status:
        raise ValueError("exclusion_audit_status must match reason_codes")
    expected_next_step = _next_step_for_status(expected_status)
    if report.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match exclusion_audit_status")


def _derived_reason_codes(
    *,
    excluded_candidate_count: Decimal,
    missing_reason_count: Decimal,
    cost_block_count: Decimal,
    source_block_count: Decimal,
    risk_block_count: Decimal,
) -> tuple[str, ...]:
    findings: list[str] = []
    if excluded_candidate_count == ZERO:
        findings.append("no_excluded_candidates_to_audit")
    if missing_reason_count > ZERO:
        findings.append("excluded_candidates_missing_reasons")
    if cost_block_count == ZERO:
        findings.append("no_cost_block_exclusions_recorded")
    elif excluded_candidate_count > ZERO:
        findings.append("cost_block_reasons_present")
    if source_block_count == ZERO:
        findings.append("no_source_block_exclusions_recorded")
    elif excluded_candidate_count > ZERO:
        findings.append("source_block_reasons_present")
    if risk_block_count == ZERO:
        findings.append("no_risk_block_exclusions_recorded")
    elif excluded_candidate_count > ZERO:
        findings.append("risk_block_reasons_present")
    return tuple(reason for reason in REASON_SEQUENCE if reason in findings)


def _status_for_reasons(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == READY_REASONS:
        return COMPLETE_STATUS
    return ATTENTION_STATUS


def _next_step_for_status(status: str) -> str:
    if status == COMPLETE_STATUS:
        return COMPLETE_NEXT_STEP
    if status == ATTENTION_STATUS:
        return ATTENTION_NEXT_STEP
    raise ValueError("exclusion_audit_status must be supported")


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


def _normalize_reason_code_items(value: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_SEQUENCE:
            raise ValueError("reason_codes contains unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(reason_code)
    canonical = tuple(reason for reason in REASON_SEQUENCE if reason in seen)
    if value != canonical:
        raise ValueError("reason_codes must use canonical sequence")
    return canonical


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            quantized = value.quantize(QUANT)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be six-decimal") from exc
    if value != quantized:
        raise ValueError(f"{field_name} must be six-decimal")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if quantized % WHOLE != ZERO:
        raise ValueError(f"{field_name} must be a whole count")
    return quantized


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized as a string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _require_count_decimal(field_name, decimal_value)


def _json_object(value: dict[str, object]) -> dict[str, object]:
    payload = json_ready_no_floats(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    return payload


def _digest_payload(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
