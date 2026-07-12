from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from typing import Any


__all__ = (
    "OperatorCandidateReviewBudgetAllocationReport",
    "build_operator_candidate_review_budget_allocation_report",
    "operator_candidate_review_budget_allocation_report_payload",
)


ZERO = Decimal("0")

STATUS_IDLE = "idle"
STATUS_SUFFICIENT = "sufficient"
STATUS_LIMITED = "limited"
STATUS_BLOCKED = "blocked"

NO_CANDIDATES_REASON_CODE = (
    "operator_candidate_review_budget_allocation_no_candidates"
)
CAPACITY_SUFFICIENT_REASON_CODE = (
    "operator_candidate_review_budget_allocation_capacity_sufficient"
)
CAPACITY_LIMITED_REASON_CODE = (
    "operator_candidate_review_budget_allocation_capacity_limited"
)
HIGH_PRIORITY_OVER_CAPACITY_REASON_CODE = (
    "operator_candidate_review_budget_allocation_high_priority_over_capacity"
)
BLOCKED_CANDIDATES_PRESENT_REASON_CODE = (
    "operator_candidate_review_budget_allocation_blocked_candidates_present"
)

NO_ALLOCATION_STEP = "no_manual_review_allocation_required"
SUFFICIENT_STEP = (
    "review_all_candidates_in_priority_"
    + "or"
    + "der_without_budget_reallocation"
)
LIMITED_STEP = "review_high_priority_candidates_then_defer_remaining_candidates"
BLOCKED_STEP = "escalate_manual_review_budget_before_candidate_decisions"


@dataclass(frozen=True)
class OperatorCandidateReviewBudgetAllocationReport:
    candidate_count: Decimal
    high_priority_count: Decimal
    manual_review_minutes_available: Decimal
    average_review_minutes_required: Decimal
    blocked_candidate_count: Decimal
    budget_status: str
    review_capacity_count: Decimal
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: dict[str, Any]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not OperatorCandidateReviewBudgetAllocationReport:
            raise TypeError(
                "OperatorCandidateReviewBudgetAllocationReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not OperatorCandidateReviewBudgetAllocationReport:
            raise ValueError(
                "report must be exactly OperatorCandidateReviewBudgetAllocationReport",
            )
        for field_name in (
            "candidate_count",
            "high_priority_count",
            "manual_review_minutes_available",
            "blocked_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "average_review_minutes_required",
            _require_positive_decimal(
                "average_review_minutes_required",
                self.average_review_minutes_required,
            ),
        )
        object.__setattr__(
            self,
            "review_capacity_count",
            _require_nonnegative_whole_decimal(
                "review_capacity_count",
                self.review_capacity_count,
            ),
        )
        object.__setattr__(
            self,
            "budget_status",
            _require_status("budget_status", self.budget_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_step("manual_next_step", self.manual_next_step),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        object.__setattr__(
            self,
            "payload_digest",
            _require_digest("payload_digest", self.payload_digest),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_operator_candidate_review_budget_allocation_report(
    *,
    candidate_count: Decimal,
    high_priority_count: Decimal,
    manual_review_minutes_available: Decimal,
    average_review_minutes_required: Decimal,
    blocked_candidate_count: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> OperatorCandidateReviewBudgetAllocationReport:
    candidate_count = _require_nonnegative_whole_decimal(
        "candidate_count",
        candidate_count,
    )
    high_priority_count = _require_nonnegative_whole_decimal(
        "high_priority_count",
        high_priority_count,
    )
    manual_review_minutes_available = _require_nonnegative_whole_decimal(
        "manual_review_minutes_available",
        manual_review_minutes_available,
    )
    average_review_minutes_required = _require_positive_decimal(
        "average_review_minutes_required",
        average_review_minutes_required,
    )
    blocked_candidate_count = _require_nonnegative_whole_decimal(
        "blocked_candidate_count",
        blocked_candidate_count,
    )
    _require_hard_flags(
        "builder",
        _FlagValues(
            paper_only=paper_only,
            report_only=report_only,
            readonly=readonly,
        ),
    )
    _validate_input_counts(
        candidate_count,
        high_priority_count,
        blocked_candidate_count,
    )

    raw_capacity = (
        manual_review_minutes_available / average_review_minutes_required
    ).to_integral_value(rounding=ROUND_FLOOR)
    review_capacity_count = min(candidate_count, raw_capacity)
    budget_status = _budget_status(
        candidate_count,
        high_priority_count,
        review_capacity_count,
    )
    reason_codes = _reason_codes(
        budget_status,
        blocked_candidate_count,
    )
    manual_next_step = _manual_next_step(budget_status)
    public_payload = {
        "candidate_count": candidate_count,
        "high_priority_count": high_priority_count,
        "manual_review_minutes_available": manual_review_minutes_available,
        "average_review_minutes_required": average_review_minutes_required,
        "blocked_candidate_count": blocked_candidate_count,
        "budget_status": budget_status,
        "review_capacity_count": review_capacity_count,
        "reason_codes": reason_codes,
        "manual_next_step": manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload_digest = _payload_digest(public_payload)

    return OperatorCandidateReviewBudgetAllocationReport(
        candidate_count=candidate_count,
        high_priority_count=high_priority_count,
        manual_review_minutes_available=manual_review_minutes_available,
        average_review_minutes_required=average_review_minutes_required,
        blocked_candidate_count=blocked_candidate_count,
        budget_status=budget_status,
        review_capacity_count=review_capacity_count,
        reason_codes=reason_codes,
        manual_next_step=manual_next_step,
        public_payload=public_payload,
        payload_digest=payload_digest,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def operator_candidate_review_budget_allocation_report_payload(
    report: OperatorCandidateReviewBudgetAllocationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is OperatorCandidateReviewBudgetAllocationReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_public_numerics(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be an OperatorCandidateReviewBudgetAllocationReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_numerics(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_public_report_payload(payload)
    return payload


@dataclass(frozen=True)
class _FlagValues:
    paper_only: object
    report_only: object
    readonly: object


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _budget_status(
    candidate_count: Decimal,
    high_priority_count: Decimal,
    review_capacity_count: Decimal,
) -> str:
    if candidate_count == ZERO:
        return STATUS_IDLE
    if high_priority_count > review_capacity_count:
        return STATUS_BLOCKED
    if review_capacity_count < candidate_count:
        return STATUS_LIMITED
    return STATUS_SUFFICIENT


def _reason_codes(
    budget_status: str,
    blocked_candidate_count: Decimal,
) -> tuple[str, ...]:
    if budget_status == STATUS_IDLE:
        values = [NO_CANDIDATES_REASON_CODE]
    elif budget_status == STATUS_BLOCKED:
        values = [HIGH_PRIORITY_OVER_CAPACITY_REASON_CODE]
    elif budget_status == STATUS_LIMITED:
        values = [CAPACITY_LIMITED_REASON_CODE]
    else:
        values = [CAPACITY_SUFFICIENT_REASON_CODE]
    if blocked_candidate_count > ZERO and budget_status != STATUS_IDLE:
        values.append(BLOCKED_CANDIDATES_PRESENT_REASON_CODE)
    return tuple(values)


def _manual_next_step(budget_status: str) -> str:
    if budget_status == STATUS_IDLE:
        return NO_ALLOCATION_STEP
    if budget_status == STATUS_BLOCKED:
        return BLOCKED_STEP
    if budget_status == STATUS_LIMITED:
        return LIMITED_STEP
    return SUFFICIENT_STEP


def _validate_input_counts(
    candidate_count: Decimal,
    high_priority_count: Decimal,
    blocked_candidate_count: Decimal,
) -> None:
    if high_priority_count > candidate_count:
        raise ValueError("high_priority_count must not exceed candidate_count")
    if blocked_candidate_count > candidate_count:
        raise ValueError("blocked_candidate_count must not exceed candidate_count")


def _validate_report(report: OperatorCandidateReviewBudgetAllocationReport) -> None:
    _validate_input_counts(
        report.candidate_count,
        report.high_priority_count,
        report.blocked_candidate_count,
    )
    expected_capacity = min(
        report.candidate_count,
        (
            report.manual_review_minutes_available
            / report.average_review_minutes_required
        ).to_integral_value(rounding=ROUND_FLOOR),
    )
    if report.review_capacity_count != expected_capacity:
        raise ValueError("review_capacity_count must match review minutes")
    expected_status = _budget_status(
        report.candidate_count,
        report.high_priority_count,
        report.review_capacity_count,
    )
    if report.budget_status != expected_status:
        raise ValueError("budget_status must match review capacity")
    if report.reason_codes != _reason_codes(
        report.budget_status,
        report.blocked_candidate_count,
    ):
        raise ValueError("reason_codes must match budget status")
    if report.manual_next_step != _manual_next_step(report.budget_status):
        raise ValueError("manual_next_step must match budget status")
    expected_public_payload = _expected_public_payload(report)
    if report.public_payload != expected_public_payload:
        raise ValueError("public_payload must match report fields")
    if report.payload_digest != _payload_digest(report.public_payload):
        raise ValueError("payload_digest must match report fields")


def _expected_public_payload(
    report: OperatorCandidateReviewBudgetAllocationReport,
) -> dict[str, Any]:
    return {
        "candidate_count": report.candidate_count,
        "high_priority_count": report.high_priority_count,
        "manual_review_minutes_available": report.manual_review_minutes_available,
        "average_review_minutes_required": report.average_review_minutes_required,
        "blocked_candidate_count": report.blocked_candidate_count,
        "budget_status": report.budget_status,
        "review_capacity_count": report.review_capacity_count,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_public_report_payload(payload: dict[str, Any]) -> None:
    required_names = {
        "candidate_count",
        "high_priority_count",
        "manual_review_minutes_available",
        "average_review_minutes_required",
        "blocked_candidate_count",
        "budget_status",
        "review_capacity_count",
        "reason_codes",
        "manual_next_step",
        "public_payload",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    if set(payload) != required_names:
        raise ValueError("report payload must use the supported public schema")
    nested = payload["public_payload"]
    if type(nested) is not dict:
        raise ValueError("public_payload must be a JSON object")
    nested_names = set(required_names)
    nested_names.remove("public_payload")
    nested_names.remove("payload_digest")
    if set(nested) != nested_names:
        raise ValueError("public_payload must use the supported public schema")
    for name in nested_names:
        if payload[name] != nested[name]:
            raise ValueError("payload_digest must match report fields")
    if payload["payload_digest"] != _payload_digest(payload["public_payload"]):
        raise ValueError("payload_digest must match report fields")


def _normalize_public_payload(value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError("public_payload must be a dict")
    normalized: dict[str, Any] = {}
    for name, item in value.items():
        if type(name) is not str:
            raise ValueError("public_payload names must be strings")
        normalized[name] = item
    return normalized


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        converted: dict[str, object] = {}
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("JSON object names must be strings")
            converted[name] = _json_ready(item)
        return converted
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or isinstance(value, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(item)
    if type(value) is list:
        for item in value:
            _reject_public_numerics(item)


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        normalized.append(_require_reason_code("reason_codes", value))
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(normalized)


def _require_reason_code(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if text.lower() != text or " " in text:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    return text


def _require_step(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if text.lower() != text or " " in text:
        raise ValueError(f"{field_name} must contain canonical text")
    return text


def _require_status(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if text not in {STATUS_IDLE, STATUS_SUFFICIENT, STATUS_LIMITED, STATUS_BLOCKED}:
        raise ValueError(f"{field_name} must be a supported budget status")
    return text


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _payload_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        _stable_json_ready(value),
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _stable_json_ready(value: object) -> object:
    if type(value) is dict:
        return {
            name: _stable_json_ready(value[name])
            for name in sorted(value)
        }
    if type(value) is list:
        return [_stable_json_ready(item) for item in value]
    return _json_ready(value)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")
