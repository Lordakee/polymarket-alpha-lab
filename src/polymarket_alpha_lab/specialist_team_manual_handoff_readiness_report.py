"""Public-safe specialist team manual handoff readiness report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "SpecialistTeamManualHandoffReadinessInput",
    "SpecialistTeamManualHandoffReadinessReport",
    "build_specialist_team_manual_handoff_readiness_report",
    "specialist_team_manual_handoff_readiness_report_payload",
)


ZERO = Decimal("0.000000")
COUNT_QUANT = Decimal("1.000000")
MEMORY_POLICY_STATUSES = ("pass", "watch", "block")
HANDOFF_STATUSES = ("ready", "not_ready")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "trade",
    "persist",
    "write",
    "mutation",
    "account",
    "private_key",
    "signing",
)
READY_REASON_CODE = "manual_handoff_ready"
REASON_PRIORITY = (
    "operator_owner_missing",
    "research_packet_missing",
    "source_gaps_open",
    "memory_policy_watch",
    "memory_policy_block",
    "handoff_note_missing",
    READY_REASON_CODE,
)
NEXT_STEP_BY_REASON_CODE = {
    "operator_owner_missing": "assign_operator_owner_before_manual_handoff",
    "research_packet_missing": "attach_research_packet_before_manual_handoff",
    "source_gaps_open": "close_source_gaps_before_manual_handoff",
    "memory_policy_watch": "resolve_memory_policy_watch_before_manual_handoff",
    "memory_policy_block": "resolve_memory_policy_block_before_manual_handoff",
    "handoff_note_missing": "add_handoff_note_before_manual_handoff",
    READY_REASON_CODE: "operator_manual_review",
}


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class SpecialistTeamManualHandoffReadinessInput(_FinalPublicDataclass):
    primary_team_id: str
    operator_owner_present: bool
    research_packet_present: bool
    source_gaps_count: Decimal
    memory_policy_status: str
    handoff_note_present: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamManualHandoffReadinessInput, "input")
        object.__setattr__(
            self,
            "primary_team_id",
            _require_public_string("primary_team_id", self.primary_team_id),
        )
        for field_name in (
            "operator_owner_present",
            "research_packet_present",
            "handoff_note_present",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_gaps_count",
            _require_count_decimal("source_gaps_count", self.source_gaps_count),
        )
        object.__setattr__(
            self,
            "memory_policy_status",
            _require_member(
                "memory_policy_status",
                self.memory_policy_status,
                MEMORY_POLICY_STATUSES,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class SpecialistTeamManualHandoffReadinessReport(_FinalPublicDataclass):
    primary_team_id: str
    operator_owner_present: bool
    research_packet_present: bool
    source_gaps_count: Decimal
    memory_policy_status: str
    handoff_note_present: bool
    handoff_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamManualHandoffReadinessReport, "report")
        object.__setattr__(
            self,
            "primary_team_id",
            _require_public_string("primary_team_id", self.primary_team_id),
        )
        for field_name in (
            "operator_owner_present",
            "research_packet_present",
            "handoff_note_present",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_gaps_count",
            _require_count_decimal("source_gaps_count", self.source_gaps_count),
        )
        object.__setattr__(
            self,
            "memory_policy_status",
            _require_member(
                "memory_policy_status",
                self.memory_policy_status,
                MEMORY_POLICY_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "handoff_status",
            _require_member("handoff_status", self.handoff_status, HANDOFF_STATUSES),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_public_string("manual_next_step", self.manual_next_step),
        )
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_specialist_team_manual_handoff_readiness_report(
    input_value: SpecialistTeamManualHandoffReadinessInput,
) -> SpecialistTeamManualHandoffReadinessReport:
    if type(input_value) is not SpecialistTeamManualHandoffReadinessInput:
        raise ValueError(
            "input_value must be a SpecialistTeamManualHandoffReadinessInput",
        )
    _require_hard_flags("input_value", input_value)
    reason_codes = _reason_codes_for_input(input_value)
    return SpecialistTeamManualHandoffReadinessReport(
        primary_team_id=input_value.primary_team_id,
        operator_owner_present=input_value.operator_owner_present,
        research_packet_present=input_value.research_packet_present,
        source_gaps_count=input_value.source_gaps_count,
        memory_policy_status=input_value.memory_policy_status,
        handoff_note_present=input_value.handoff_note_present,
        handoff_status=_handoff_status(reason_codes),
        reason_codes=reason_codes,
        manual_next_step=NEXT_STEP_BY_REASON_CODE[reason_codes[0]],
    )


def specialist_team_manual_handoff_readiness_report_payload(
    report: SpecialistTeamManualHandoffReadinessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SpecialistTeamManualHandoffReadinessReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        return payload
    if type(report) is dict:
        _reject_public_numeric_values(report)
        _reject_unsafe_public_payload(
            "payload",
            report,
            allow_json_containers=True,
        )
        _require_hard_flags("payload", _PayloadFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be an object")
        _validate_payload_shape(payload)
        return payload
    raise ValueError(
        "report must be a SpecialistTeamManualHandoffReadinessReport",
    )


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


def _reason_codes_for_input(
    input_value: SpecialistTeamManualHandoffReadinessInput,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not input_value.operator_owner_present:
        reason_codes.append("operator_owner_missing")
    if not input_value.research_packet_present:
        reason_codes.append("research_packet_missing")
    if input_value.source_gaps_count > ZERO:
        reason_codes.append("source_gaps_open")
    if input_value.memory_policy_status == "watch":
        reason_codes.append("memory_policy_watch")
    if input_value.memory_policy_status == "block":
        reason_codes.append("memory_policy_block")
    if not input_value.handoff_note_present:
        reason_codes.append("handoff_note_missing")
    if not reason_codes:
        reason_codes.append(READY_REASON_CODE)
    return tuple(reason_codes)


def _handoff_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON_CODE,):
        return "ready"
    return "not_ready"


def _validate_report_consistency(
    report: SpecialistTeamManualHandoffReadinessReport,
) -> None:
    expected_reason_codes = _reason_codes_for_input(
        SpecialistTeamManualHandoffReadinessInput(
            primary_team_id=report.primary_team_id,
            operator_owner_present=report.operator_owner_present,
            research_packet_present=report.research_packet_present,
            source_gaps_count=report.source_gaps_count,
            memory_policy_status=report.memory_policy_status,
            handoff_note_present=report.handoff_note_present,
        ),
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match manual handoff readiness inputs")
    if report.handoff_status != _handoff_status(report.reason_codes):
        raise ValueError("handoff_status must match reason_codes")
    if report.manual_next_step != NEXT_STEP_BY_REASON_CODE[report.reason_codes[0]]:
        raise ValueError("manual_next_step must match first reason_code")


def _validate_payload_shape(payload: dict[str, Any]) -> None:
    expected_keys = (
        "primary_team_id",
        "operator_owner_present",
        "research_packet_present",
        "source_gaps_count",
        "memory_policy_status",
        "handoff_note_present",
        "handoff_status",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
    )
    if tuple(payload) != expected_keys:
        raise ValueError("payload schema must match manual handoff readiness report")
    report = SpecialistTeamManualHandoffReadinessReport(
        primary_team_id=payload["primary_team_id"],
        operator_owner_present=payload["operator_owner_present"],
        research_packet_present=payload["research_packet_present"],
        source_gaps_count=_decimal_from_public_string(
            "source_gaps_count",
            payload["source_gaps_count"],
        ),
        memory_policy_status=payload["memory_policy_status"],
        handoff_note_present=payload["handoff_note_present"],
        handoff_status=payload["handoff_status"],
        reason_codes=tuple(payload["reason_codes"]),
        manual_next_step=payload["manual_next_step"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    _validate_report_consistency(report)


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} has unsafe public value")
    if len(value) > 96:
        raise ValueError(f"{field_name} is too long")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise ValueError(f"{field_name} must be printable ASCII")
    if _has_unsafe_public_fragment(field_name):
        raise ValueError(f"{field_name} has unsafe public field")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    value = _require_public_string(field_name, value)
    if value not in allowed_values:
        joined = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {joined}")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        decimal_value = value.quantize(COUNT_QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc
    if decimal_value != value:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _decimal_from_public_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use a Decimal string") from exc
    return _require_count_decimal(field_name, decimal_value)


def _require_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    reason_codes: list[str] = []
    for reason_code in value:
        reason_code = _require_public_string("reason_code", reason_code)
        if reason_code not in REASON_PRIORITY:
            raise ValueError("reason_code is not supported")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        reason_codes.append(reason_code)
    sorted_codes = tuple(
        reason_code for reason_code in REASON_PRIORITY if reason_code in seen
    )
    if tuple(reason_codes) != sorted_codes:
        raise ValueError("reason_codes must follow priority order")
    if READY_REASON_CODE in seen and len(seen) > 1:
        raise ValueError("manual_handoff_ready cannot be combined with gaps")
    return tuple(reason_codes)


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _reject_public_numeric_values(value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) in (Decimal, int, float):
        raise ValueError(
            f"public payload must use Decimal strings, not numeric values at {path}",
        )
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_public_numeric_values(item, nested_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]"
            _reject_public_numeric_values(item, nested_path)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            SpecialistTeamManualHandoffReadinessInput,
            SpecialistTeamManualHandoffReadinessReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return format(value, ".6f")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is int:
        raise ValueError("JSON value must use Decimal strings")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    raise ValueError(f"unsupported JSON value: {type(value).__name__}")
