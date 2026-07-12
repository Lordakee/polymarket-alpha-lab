"""Report-only specialist team memory backlog priority reducer.

The reducer is intentionally pure and in-memory: it accepts public aggregate
counts, derives a manual review status, and returns a JSON-safe public report.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any


SPECIALIST_TEAM_MEMORY_UPDATE_BACKLOG_STATUSES = (
    "clear",
    "monitor",
    "priority",
    "critical",
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

STATUS_CLEAR = "clear"
STATUS_MONITOR = "monitor"
STATUS_PRIORITY = "priority"
STATUS_CRITICAL = "critical"

REASON_CLEAR = "specialist_team_memory_update_backlog_clear"
REASON_MONITOR = "specialist_team_memory_update_backlog_monitor"
REASON_PRIORITY = "specialist_team_memory_update_backlog_priority"
REASON_CRITICAL = "specialist_team_memory_update_backlog_critical"
REASON_WITHIN_CAPACITY = "pending_memory_updates_within_capacity"
REASON_EXCEED_CAPACITY = "pending_memory_updates_exceed_capacity"
REASON_CALIBRATION_REVIEW = "calibration_error_probability_review"
REASON_CALIBRATION_CRITICAL = "calibration_error_probability_critical"
REASON_AGING = "oldest_memory_update_aging"
REASON_STALE = "oldest_memory_update_stale"
REASON_SETTLED_REVIEW = "settled_markets_need_memory_backlog_review"

REASON_CODE_SEQUENCE = (
    REASON_CLEAR,
    REASON_MONITOR,
    REASON_PRIORITY,
    REASON_CRITICAL,
    REASON_WITHIN_CAPACITY,
    REASON_EXCEED_CAPACITY,
    REASON_CALIBRATION_REVIEW,
    REASON_CALIBRATION_CRITICAL,
    REASON_AGING,
    REASON_STALE,
    REASON_SETTLED_REVIEW,
)

MANUAL_NEXT_STEP_ARCHIVE = "manual_archive_memory_update_backlog_report"
MANUAL_NEXT_STEP_MONITOR = "manual_review_memory_update_backlog_next_cycle"
MANUAL_NEXT_STEP_PRIORITY = "manual_prioritize_memory_updates_before_new_research"
MANUAL_NEXT_STEP_CRITICAL = "manual_clear_memory_update_backlog_before_new_research"
MANUAL_NEXT_STEP_BY_STATUS = {
    STATUS_CLEAR: MANUAL_NEXT_STEP_ARCHIVE,
    STATUS_MONITOR: MANUAL_NEXT_STEP_MONITOR,
    STATUS_PRIORITY: MANUAL_NEXT_STEP_PRIORITY,
    STATUS_CRITICAL: MANUAL_NEXT_STEP_CRITICAL,
}

PAYLOAD_FIELDS = (
    "pending_memory_update_count",
    "settled_market_count",
    "calibration_error_probability",
    "oldest_update_age_hours",
    "team_capacity_slots",
    "backlog_status",
    "reason_codes",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "@",
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "private" + "_" + "key",
    "api" + "_" + "key",
    "sig" + "nature",
    "sig" + "ning",
    "exec" + "ute",
    "exec" + "ution",
    "data" + "base",
    "per" + "sist",
    "ins" + "ert",
    "com" + "mit",
    "cur" + "sor",
)


__all__ = (
    "SPECIALIST_TEAM_MEMORY_UPDATE_BACKLOG_STATUSES",
    "SpecialistTeamMemoryUpdateBacklogPriorityInput",
    "SpecialistTeamMemoryUpdateBacklogPriorityReport",
    "build_specialist_team_memory_update_backlog_priority_report",
    "specialist_team_memory_update_backlog_priority_public_payload",
    "validate_specialist_team_memory_update_backlog_priority_public_payload",
)


@dataclass(frozen=True)
class SpecialistTeamMemoryUpdateBacklogPriorityInput:
    pending_memory_update_count: Decimal
    settled_market_count: Decimal
    calibration_error_probability: Decimal
    oldest_update_age_hours: Decimal
    team_capacity_slots: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamMemoryUpdateBacklogPriorityInput, "input")
        for field_name in (
            "pending_memory_update_count",
            "settled_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_integer_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error_probability",
            _normalize_probability_decimal(
                "calibration_error_probability",
                self.calibration_error_probability,
            ),
        )
        object.__setattr__(
            self,
            "oldest_update_age_hours",
            _normalize_nonnegative_decimal(
                "oldest_update_age_hours",
                self.oldest_update_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_slots",
            _normalize_integer_decimal("team_capacity_slots", self.team_capacity_slots),
        )
        if self.team_capacity_slots <= ZERO:
            raise ValueError("team_capacity_slots must be positive")
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class SpecialistTeamMemoryUpdateBacklogPriorityReport:
    pending_memory_update_count: Decimal
    settled_market_count: Decimal
    calibration_error_probability: Decimal
    oldest_update_age_hours: Decimal
    team_capacity_slots: Decimal
    backlog_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamMemoryUpdateBacklogPriorityReport, "report")
        for field_name in (
            "pending_memory_update_count",
            "settled_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_integer_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_error_probability",
            _normalize_probability_decimal(
                "calibration_error_probability",
                self.calibration_error_probability,
            ),
        )
        object.__setattr__(
            self,
            "oldest_update_age_hours",
            _normalize_nonnegative_decimal(
                "oldest_update_age_hours",
                self.oldest_update_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_slots",
            _normalize_integer_decimal("team_capacity_slots", self.team_capacity_slots),
        )
        if self.team_capacity_slots <= ZERO:
            raise ValueError("team_capacity_slots must be positive")
        _require_status("backlog_status", self.backlog_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.payload_digest:
            _require_sha256("payload_digest", self.payload_digest)
            if self.payload_digest != _payload_digest_for_report(self):
                raise ValueError("payload_digest must match public payload")
        else:
            object.__setattr__(self, "payload_digest", _payload_digest_for_report(self))

    @property
    def public_payload(self) -> dict[str, Any]:
        return specialist_team_memory_update_backlog_priority_public_payload(self)


def build_specialist_team_memory_update_backlog_priority_report(
    backlog_input: SpecialistTeamMemoryUpdateBacklogPriorityInput,
) -> SpecialistTeamMemoryUpdateBacklogPriorityReport:
    if type(backlog_input) is not SpecialistTeamMemoryUpdateBacklogPriorityInput:
        raise ValueError(
            "backlog_input must be a SpecialistTeamMemoryUpdateBacklogPriorityInput",
        )
    _require_hard_flags("input", backlog_input)
    status = _backlog_status(backlog_input)
    return SpecialistTeamMemoryUpdateBacklogPriorityReport(
        pending_memory_update_count=backlog_input.pending_memory_update_count,
        settled_market_count=backlog_input.settled_market_count,
        calibration_error_probability=backlog_input.calibration_error_probability,
        oldest_update_age_hours=backlog_input.oldest_update_age_hours,
        team_capacity_slots=backlog_input.team_capacity_slots,
        backlog_status=status,
        reason_codes=_reason_codes(backlog_input, status=status),
        manual_next_step=MANUAL_NEXT_STEP_BY_STATUS[status],
    )


def specialist_team_memory_update_backlog_priority_public_payload(
    report: SpecialistTeamMemoryUpdateBacklogPriorityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SpecialistTeamMemoryUpdateBacklogPriorityReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        if report.payload_digest != _payload_digest_for_report(report):
            raise ValueError("payload_digest must match public payload")
        payload = _json_ready(_public_payload_dict(report))
        if type(payload) is not dict:
            raise ValueError("public payload must be an object")
        _reject_unsafe_public_payload(payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        validate_specialist_team_memory_update_backlog_priority_public_payload(report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("public payload must be an object")
        return payload
    raise ValueError("report must be a SpecialistTeamMemoryUpdateBacklogPriorityReport")


def validate_specialist_team_memory_update_backlog_priority_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be an object")
    if tuple(payload) != PAYLOAD_FIELDS:
        raise ValueError("payload must match the canonical backlog priority schema")
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_values(payload)
    _require_hard_flags("payload", _PayloadFlags(payload))
    _normalize_integer_decimal(
        "pending_memory_update_count",
        _require_string_decimal(
            "pending_memory_update_count",
            payload["pending_memory_update_count"],
        ),
    )
    _normalize_integer_decimal(
        "settled_market_count",
        _require_string_decimal("settled_market_count", payload["settled_market_count"]),
    )
    _normalize_probability_decimal(
        "calibration_error_probability",
        _require_string_decimal(
            "calibration_error_probability",
            payload["calibration_error_probability"],
        ),
    )
    _normalize_nonnegative_decimal(
        "oldest_update_age_hours",
        _require_string_decimal("oldest_update_age_hours", payload["oldest_update_age_hours"]),
    )
    team_capacity_slots = _normalize_integer_decimal(
        "team_capacity_slots",
        _require_string_decimal("team_capacity_slots", payload["team_capacity_slots"]),
    )
    if team_capacity_slots <= ZERO:
        raise ValueError("team_capacity_slots must be positive")
    _require_status("backlog_status", payload["backlog_status"])
    _normalize_payload_reason_codes("reason_codes", payload["reason_codes"])
    _require_manual_next_step("manual_next_step", payload["manual_next_step"])
    supplied_digest = payload["payload_digest"]
    if type(supplied_digest) is not str:
        raise ValueError("payload_digest is required")
    _require_sha256("payload_digest", supplied_digest)
    if supplied_digest != _payload_digest(payload):
        raise ValueError("payload_digest must match public payload")
    return True


@dataclass(frozen=True)
class _PayloadFlags:
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


def _backlog_status(
    backlog_input: SpecialistTeamMemoryUpdateBacklogPriorityInput,
) -> str:
    if backlog_input.pending_memory_update_count == ZERO:
        return STATUS_CLEAR
    if (
        backlog_input.pending_memory_update_count > backlog_input.team_capacity_slots
        or backlog_input.calibration_error_probability >= Decimal("0.100000")
        or backlog_input.oldest_update_age_hours >= Decimal("48.000000")
    ):
        if (
            backlog_input.pending_memory_update_count
            >= backlog_input.team_capacity_slots * Decimal("3.000000")
            or backlog_input.calibration_error_probability >= Decimal("0.200000")
            or backlog_input.oldest_update_age_hours >= Decimal("72.000000")
            or backlog_input.settled_market_count >= Decimal("25.000000")
            and backlog_input.pending_memory_update_count > backlog_input.team_capacity_slots
        ):
            return STATUS_CRITICAL
        return STATUS_PRIORITY
    return STATUS_MONITOR


def _reason_codes(
    backlog_input: SpecialistTeamMemoryUpdateBacklogPriorityInput,
    *,
    status: str,
) -> tuple[str, ...]:
    status_reason = {
        STATUS_CLEAR: REASON_CLEAR,
        STATUS_MONITOR: REASON_MONITOR,
        STATUS_PRIORITY: REASON_PRIORITY,
        STATUS_CRITICAL: REASON_CRITICAL,
    }[status]
    if status == STATUS_CLEAR:
        return (status_reason,)
    codes = [status_reason]
    if backlog_input.pending_memory_update_count > backlog_input.team_capacity_slots:
        codes.append(REASON_EXCEED_CAPACITY)
    else:
        codes.append(REASON_WITHIN_CAPACITY)
    if backlog_input.calibration_error_probability >= Decimal("0.200000"):
        codes.append(REASON_CALIBRATION_CRITICAL)
    elif backlog_input.calibration_error_probability >= Decimal("0.100000"):
        codes.append(REASON_CALIBRATION_REVIEW)
    if backlog_input.oldest_update_age_hours >= Decimal("72.000000"):
        codes.append(REASON_STALE)
    elif backlog_input.oldest_update_age_hours >= Decimal("24.000000"):
        codes.append(REASON_AGING)
    if (
        backlog_input.settled_market_count >= Decimal("25.000000")
        and backlog_input.pending_memory_update_count > backlog_input.team_capacity_slots
    ):
        codes.append(REASON_SETTLED_REVIEW)
    return tuple(code for code in REASON_CODE_SEQUENCE if code in codes)


def _validate_report(report: SpecialistTeamMemoryUpdateBacklogPriorityReport) -> None:
    source = SpecialistTeamMemoryUpdateBacklogPriorityInput(
        pending_memory_update_count=report.pending_memory_update_count,
        settled_market_count=report.settled_market_count,
        calibration_error_probability=report.calibration_error_probability,
        oldest_update_age_hours=report.oldest_update_age_hours,
        team_capacity_slots=report.team_capacity_slots,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    expected_status = _backlog_status(source)
    if report.backlog_status != expected_status:
        raise ValueError("backlog_status must match backlog inputs")
    if report.reason_codes != _reason_codes(source, status=expected_status):
        raise ValueError("reason_codes must match backlog inputs")
    if report.manual_next_step != MANUAL_NEXT_STEP_BY_STATUS[expected_status]:
        raise ValueError("manual_next_step must match backlog_status")


def _payload_digest_for_report(
    report: SpecialistTeamMemoryUpdateBacklogPriorityReport,
) -> str:
    payload = _public_payload_dict(report)
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload["payload_digest"] = ""
    encoded = json.dumps(
        _json_ready(digest_payload),
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _public_payload_dict(report: SpecialistTeamMemoryUpdateBacklogPriorityReport) -> dict[str, Any]:
    return {
        "pending_memory_update_count": report.pending_memory_update_count,
        "settled_market_count": report.settled_market_count,
        "calibration_error_probability": report.calibration_error_probability,
        "oldest_update_age_hours": report.oldest_update_age_hours,
        "team_capacity_slots": report.team_capacity_slots,
        "backlog_status": report.backlog_status,
        "reason_codes": report.reason_codes,
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": report.payload_digest,
    }


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return _format_decimal(value)
    if dataclass_is_instance(value):
        return _json_ready(asdict(value))
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise TypeError("value is not public JSON serializable")


def dataclass_is_instance(value: object) -> bool:
    return hasattr(value, "__dataclass_fields__") and not isinstance(value, type)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _normalize_integer_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return value


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(field_name, value)


def _quantize(field_name: str, value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must fit the supported precision") from exc


def _format_decimal(value: Decimal) -> str:
    return format(_quantize("decimal", value), "f")


def _require_string_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be serialized as a string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return parsed


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in SPECIALIST_TEAM_MEMORY_UPDATE_BACKLOG_STATUSES:
        raise ValueError(f"{field_name} must be a supported backlog status")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value)


def _normalize_payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(field_name, tuple(value))
    if type(value) is tuple:
        return _normalize_reason_code_items(field_name, value)
    raise ValueError(f"{field_name} must be a list")


def _normalize_reason_code_items(
    field_name: str,
    value: tuple[object, ...],
) -> tuple[str, ...]:
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in REASON_CODE_SEQUENCE:
            raise ValueError(f"{field_name} contains an unsupported reason code")
        if item in normalized:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(item)
    canonical = tuple(code for code in REASON_CODE_SEQUENCE if code in normalized)
    if tuple(normalized) != canonical:
        raise ValueError(f"{field_name} must follow canonical sequence")
    return canonical


def _require_manual_next_step(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MANUAL_NEXT_STEP_BY_STATUS.values():
        raise ValueError(f"{field_name} must be a supported manual next step")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numeric values must be decimal strings")
    if isinstance(value, dict):
        for child in value.values():
            _reject_public_numeric_values(child)
    elif isinstance(value, list):
        for child in value:
            _reject_public_numeric_values(child)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, str):
        normalized = value.lower().replace("-", "_").replace(" ", "_")
        if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError("public payload contains unsafe text")
    elif isinstance(value, dict):
        for child in value.values():
            _reject_unsafe_public_payload(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            _reject_unsafe_public_payload(child)
