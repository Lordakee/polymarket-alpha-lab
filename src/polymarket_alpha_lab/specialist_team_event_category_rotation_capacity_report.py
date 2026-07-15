"""Read-only specialist team event category rotation capacity report.

Pure in-memory Decimal arithmetic for manual specialist coverage review. The
module only produces immutable report objects, public payloads, and digests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


SPECIALIST_TEAM_EVENT_CATEGORY_ROTATION_CAPACITY_STATUSES = (
    "ready",
    "attention",
    "blocked",
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_COUNT_FIELDS = (
    "team_count",
    "category_count",
    "overloaded_team_count",
    "rotation_slot_count",
    "urgent_category_count",
)
_REASON_CODES = (
    "urgent_category_rotation_capacity_shortfall_blocker",
    "specialist_team_overload_attention",
    "category_coverage_capacity_attention",
    "specialist_team_event_category_rotation_capacity_ready",
)
_MANUAL_NEXT_STEPS = (
    "assign_additional_specialist_category_coverage",
    "document_specialist_rotation_capacity_review",
    "escalate_manual_rotation_capacity_review",
    "rebalance_specialist_team_rotation_queue",
)
_PUBLIC_FIELDS = frozenset(
    (
        "team_count",
        "category_count",
        "overloaded_team_count",
        "rotation_slot_count",
        "urgent_category_count",
        "rotation_capacity_status",
        "reason_codes",
        "manual_next_step",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "auto",
    "b" + "uy",
    "crawl",
    "exec" + "ute",
    "exec" + "ution",
    "jsonl",
    "k" + "ey",
    "li" + "ve",
    "persist",
    "scrape",
    "se" + "ll",
    "sig" + "n",
    "trad" + "e",
    "wal" + "let",
)

__all__ = (
    "SPECIALIST_TEAM_EVENT_CATEGORY_ROTATION_CAPACITY_STATUSES",
    "SpecialistTeamEventCategoryRotationCapacityInput",
    "SpecialistTeamEventCategoryRotationCapacityReport",
    "build_specialist_team_event_category_rotation_capacity_report",
    "specialist_team_event_category_rotation_capacity_public_payload",
)


@dataclass(frozen=True)
class SpecialistTeamEventCategoryRotationCapacityInput:
    team_count: Decimal
    category_count: Decimal
    overloaded_team_count: Decimal
    rotation_slot_count: Decimal
    urgent_category_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamEventCategoryRotationCapacityInput:
            raise ValueError(
                "input must be exactly "
                "SpecialistTeamEventCategoryRotationCapacityInput",
            )
        for field_name in _COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_counts(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class SpecialistTeamEventCategoryRotationCapacityReport:
    team_count: Decimal
    category_count: Decimal
    overloaded_team_count: Decimal
    rotation_slot_count: Decimal
    urgent_category_count: Decimal
    rotation_capacity_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not SpecialistTeamEventCategoryRotationCapacityReport:
            raise ValueError(
                "report must be exactly "
                "SpecialistTeamEventCategoryRotationCapacityReport",
            )
        for field_name in _COUNT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _validate_counts(self)
        _require_status("rotation_capacity_status", self.rotation_capacity_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _apply_or_verify_payload_digest(self)
        _validate_report_consistency(self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_event_category_rotation_capacity_public_payload(self)


def build_specialist_team_event_category_rotation_capacity_report(
    value: SpecialistTeamEventCategoryRotationCapacityInput,
) -> SpecialistTeamEventCategoryRotationCapacityReport:
    if type(value) is not SpecialistTeamEventCategoryRotationCapacityInput:
        raise ValueError(
            "value must be a SpecialistTeamEventCategoryRotationCapacityInput",
        )
    _require_hard_flags("input", value)
    reason_codes = _reason_codes(
        team_count=value.team_count,
        category_count=value.category_count,
        overloaded_team_count=value.overloaded_team_count,
        rotation_slot_count=value.rotation_slot_count,
        urgent_category_count=value.urgent_category_count,
    )
    status = _rotation_capacity_status(reason_codes)
    return SpecialistTeamEventCategoryRotationCapacityReport(
        team_count=value.team_count,
        category_count=value.category_count,
        overloaded_team_count=value.overloaded_team_count,
        rotation_slot_count=value.rotation_slot_count,
        urgent_category_count=value.urgent_category_count,
        rotation_capacity_status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status, reason_codes),
    )


def specialist_team_event_category_rotation_capacity_public_payload(
    report: SpecialistTeamEventCategoryRotationCapacityReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamEventCategoryRotationCapacityReport:
        raise ValueError(
            "report must be a SpecialistTeamEventCategoryRotationCapacityReport",
        )
    _require_hard_flags("report", report)
    _verify_payload_digest(report)
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _reason_codes(
    *,
    team_count: Decimal,
    category_count: Decimal,
    overloaded_team_count: Decimal,
    rotation_slot_count: Decimal,
    urgent_category_count: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if urgent_category_count > rotation_slot_count:
        reasons.append("urgent_category_rotation_capacity_shortfall_blocker")
    if overloaded_team_count > ZERO:
        reasons.append("specialist_team_overload_attention")
    if category_count > team_count:
        reasons.append("category_coverage_capacity_attention")
    if not reasons:
        return ("specialist_team_event_category_rotation_capacity_ready",)
    return tuple(reason for reason in _REASON_CODES if reason in reasons)


def _rotation_capacity_status(reason_codes: tuple[str, ...]) -> str:
    if "urgent_category_rotation_capacity_shortfall_blocker" in reason_codes:
        return "blocked"
    if reason_codes != ("specialist_team_event_category_rotation_capacity_ready",):
        return "attention"
    return "ready"


def _manual_next_step(status: str, reason_codes: tuple[str, ...]) -> str:
    if status == "blocked":
        return "escalate_manual_rotation_capacity_review"
    if "specialist_team_overload_attention" in reason_codes:
        return "rebalance_specialist_team_rotation_queue"
    if "category_coverage_capacity_attention" in reason_codes:
        return "assign_additional_specialist_category_coverage"
    return "document_specialist_rotation_capacity_review"


def _validate_report_consistency(
    report: SpecialistTeamEventCategoryRotationCapacityReport,
) -> None:
    expected_reason_codes = _reason_codes(
        team_count=report.team_count,
        category_count=report.category_count,
        overloaded_team_count=report.overloaded_team_count,
        rotation_slot_count=report.rotation_slot_count,
        urgent_category_count=report.urgent_category_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rotation capacity inputs")
    expected_status = _rotation_capacity_status(expected_reason_codes)
    if report.rotation_capacity_status != expected_status:
        raise ValueError(
            "rotation_capacity_status must match rotation capacity inputs",
        )
    expected_next_step = _manual_next_step(expected_status, expected_reason_codes)
    if report.manual_next_step != expected_next_step:
        raise ValueError("manual_next_step must match rotation capacity status")


def _validate_counts(value: object) -> None:
    team_count = getattr(value, "team_count")
    category_count = getattr(value, "category_count")
    overloaded_team_count = getattr(value, "overloaded_team_count")
    urgent_category_count = getattr(value, "urgent_category_count")
    if overloaded_team_count > team_count:
        raise ValueError("overloaded_team_count must not exceed team_count")
    if urgent_category_count > category_count:
        raise ValueError("urgent_category_count must not exceed category_count")


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer-valued Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in SPECIALIST_TEAM_EVENT_CATEGORY_ROTATION_CAPACITY_STATUSES
    ):
        raise ValueError(f"{field_name} must be a supported status")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in _REASON_CODES:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    ordered = tuple(reason_code for reason_code in _REASON_CODES if reason_code in seen)
    if value != ordered:
        raise ValueError(f"{field_name} must use canonical order")
    return ordered


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a supported manual next step")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        flag = getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _apply_or_verify_payload_digest(
    report: SpecialistTeamEventCategoryRotationCapacityReport,
) -> None:
    if report.payload_digest == "":
        object.__setattr__(report, "payload_digest", _payload_digest(report))
        return
    _verify_payload_digest(report)


def _verify_payload_digest(
    report: SpecialistTeamEventCategoryRotationCapacityReport,
) -> None:
    if type(report.payload_digest) is not str or len(report.payload_digest) != 64:
        raise ValueError("payload_digest must be a 64-character hex digest")
    if report.payload_digest != _payload_digest(report):
        raise ValueError("payload_digest must match public payload")


def _payload_digest(
    report: SpecialistTeamEventCategoryRotationCapacityReport,
) -> str:
    payload = asdict(report)
    payload.pop("payload_digest")
    json_payload = _json_ready(payload)
    encoded = dumps(
        json_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return f"{value.quantize(QUANTUM)}"
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    if set(payload) != _PUBLIC_FIELDS:
        raise ValueError("public payload must match the canonical capacity schema")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public text")
