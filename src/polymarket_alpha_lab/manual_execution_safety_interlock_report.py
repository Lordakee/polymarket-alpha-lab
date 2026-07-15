"""Pure read-only manual execution safety interlock report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


__all__ = (
    "INTERLOCK_BANDS",
    "MANUAL_EXECUTION_SAFETY_INTERLOCK_CHECK_FIELDS",
    "FrozenJsonArray",
    "FrozenJsonObject",
    "ManualExecutionSafetyInterlockInput",
    "ManualExecutionSafetyInterlockReport",
    "build_manual_execution_safety_interlock_report",
    "manual_execution_safety_interlock_report_digest",
    "manual_execution_safety_interlock_report_to_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CHECK_COUNT = Decimal("8.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
INTERLOCK_BANDS = ("ready", "attention", "blocked")
MANUAL_EXECUTION_SAFETY_INTERLOCK_CHECK_FIELDS = (
    "no_live_order_path",
    "no_wallet_or_auth_path",
    "paper_only_enforced",
    "operator_manual_only",
    "public_payload_safe",
    "supabase_persistence_ready",
    "decision_gate_ready",
    "review_packet_ready",
)

_BLOCKING_REASON_BY_FIELD = {
    "no_live_order_path": "manual_execution_interlock_live_order_path_present",
    "no_wallet_or_auth_path": "manual_execution_interlock_wallet_or_auth_path_present",
    "paper_only_enforced": "manual_execution_interlock_paper_only_not_enforced",
    "operator_manual_only": "manual_execution_interlock_operator_not_manual_only",
    "public_payload_safe": "manual_execution_interlock_public_payload_not_safe",
    "decision_gate_ready": "manual_execution_interlock_decision_gate_not_ready",
    "review_packet_ready": "manual_execution_interlock_review_packet_not_ready",
}
_ATTENTION_REASON_BY_FIELD = {
    "supabase_persistence_ready": (
        "manual_execution_interlock_supabase_persistence_not_ready"
    ),
}


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ManualExecutionSafetyInterlockInput(_FinalDataclass):
    no_live_order_path: bool
    no_wallet_or_auth_path: bool
    paper_only_enforced: bool
    operator_manual_only: bool
    public_payload_safe: bool
    supabase_persistence_ready: bool
    decision_gate_ready: bool
    review_packet_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ManualExecutionSafetyInterlockInput, "interlock input")
        for field_name in MANUAL_EXECUTION_SAFETY_INTERLOCK_CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("interlock input", self)


@dataclass(frozen=True)
class ManualExecutionSafetyInterlockReport(_FinalDataclass):
    no_live_order_path: bool
    no_wallet_or_auth_path: bool
    paper_only_enforced: bool
    operator_manual_only: bool
    public_payload_safe: bool
    supabase_persistence_ready: bool
    decision_gate_ready: bool
    review_packet_ready: bool
    execution_interlock_ready: bool
    interlock_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ManualExecutionSafetyInterlockReport, "interlock report")
        for field_name in MANUAL_EXECUTION_SAFETY_INTERLOCK_CHECK_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_bool("execution_interlock_ready", self.execution_interlock_ready)
        if self.interlock_band not in INTERLOCK_BANDS:
            raise ValueError("interlock_band must be ready, attention, or blocked")
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes("blocked_reason_codes", self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _normalize_ratio("ready_ratio", self.ready_ratio),
        )
        _require_hard_flags("interlock report", self)
        _validate_report(self)

    @property
    def public_payload(self) -> "FrozenJsonObject":
        return manual_execution_safety_interlock_report_to_public_payload(self)

    @property
    def digest(self) -> str:
        return manual_execution_safety_interlock_report_digest(self)


def build_manual_execution_safety_interlock_report(
    interlock_input: ManualExecutionSafetyInterlockInput,
) -> ManualExecutionSafetyInterlockReport:
    if type(interlock_input) is not ManualExecutionSafetyInterlockInput:
        raise ValueError(
            "interlock_input must be a ManualExecutionSafetyInterlockInput",
        )
    _require_hard_flags("interlock input", interlock_input)

    blocked_reason_codes = _blocked_reason_codes(interlock_input)
    attention_reason_codes = _attention_reason_codes(interlock_input)
    interlock_band = _interlock_band(blocked_reason_codes, attention_reason_codes)

    return ManualExecutionSafetyInterlockReport(
        no_live_order_path=interlock_input.no_live_order_path,
        no_wallet_or_auth_path=interlock_input.no_wallet_or_auth_path,
        paper_only_enforced=interlock_input.paper_only_enforced,
        operator_manual_only=interlock_input.operator_manual_only,
        public_payload_safe=interlock_input.public_payload_safe,
        supabase_persistence_ready=interlock_input.supabase_persistence_ready,
        decision_gate_ready=interlock_input.decision_gate_ready,
        review_packet_ready=interlock_input.review_packet_ready,
        execution_interlock_ready=interlock_band == "ready",
        interlock_band=interlock_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_ready_check_count(interlock_input), CHECK_COUNT),
        paper_only=interlock_input.paper_only,
        report_only=interlock_input.report_only,
        readonly=interlock_input.readonly,
    )


def manual_execution_safety_interlock_report_to_public_payload(
    report: ManualExecutionSafetyInterlockReport,
) -> "FrozenJsonObject":
    if type(report) is not ManualExecutionSafetyInterlockReport:
        raise ValueError("report must be a ManualExecutionSafetyInterlockReport")
    _require_hard_flags("interlock report", report)
    _validate_report(report)
    payload = _payload_value(report, include_digest=True)
    _validate_public_payload(payload)
    return _freeze_json_object(payload)


def manual_execution_safety_interlock_report_digest(
    report: ManualExecutionSafetyInterlockReport,
) -> str:
    if type(report) is not ManualExecutionSafetyInterlockReport:
        raise ValueError("report must be a ManualExecutionSafetyInterlockReport")
    _require_hard_flags("interlock report", report)
    _validate_report(report)
    return _digest_for_payload(_payload_value(report, include_digest=False))


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("public payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("public payload is immutable")

    def clear(self) -> None:
        raise TypeError("public payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("public payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("public payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("public payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("public payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("public payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("public payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("public payload is immutable")


def _blocked_reason_codes(
    value: ManualExecutionSafetyInterlockInput | ManualExecutionSafetyInterlockReport,
) -> tuple[str, ...]:
    return tuple(
        reason_code
        for field_name, reason_code in _BLOCKING_REASON_BY_FIELD.items()
        if getattr(value, field_name) is False
    )


def _attention_reason_codes(
    value: ManualExecutionSafetyInterlockInput | ManualExecutionSafetyInterlockReport,
) -> tuple[str, ...]:
    return tuple(
        reason_code
        for field_name, reason_code in _ATTENTION_REASON_BY_FIELD.items()
        if getattr(value, field_name) is False
    )


def _interlock_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes:
        return "attention"
    return "ready"


def _ready_check_count(
    value: ManualExecutionSafetyInterlockInput | ManualExecutionSafetyInterlockReport,
) -> Decimal:
    return _count(
        sum(
            1
            for field_name in MANUAL_EXECUTION_SAFETY_INTERLOCK_CHECK_FIELDS
            if getattr(value, field_name) is True
        ),
    )


def _validate_report(report: ManualExecutionSafetyInterlockReport) -> None:
    expected_blocked_codes = _blocked_reason_codes(report)
    expected_attention_codes = _attention_reason_codes(report)
    if report.blocked_reason_codes != expected_blocked_codes:
        raise ValueError("blocked_reason_codes must match interlock flags")
    if report.attention_reason_codes != expected_attention_codes:
        raise ValueError("attention_reason_codes must match interlock flags")
    expected_band = _interlock_band(expected_blocked_codes, expected_attention_codes)
    if report.interlock_band != expected_band:
        raise ValueError("interlock_band must match interlock reason codes")
    if report.execution_interlock_ready != (expected_band == "ready"):
        raise ValueError("execution_interlock_ready must match interlock_band")
    expected_ratio = _ratio(_ready_check_count(report), CHECK_COUNT)
    if report.ready_ratio != expected_ratio:
        raise ValueError("ready_ratio must match ready interlock checks")


def _payload_value(
    report: ManualExecutionSafetyInterlockReport,
    *,
    include_digest: bool,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "no_live_order_path": report.no_live_order_path,
        "no_wallet_or_auth_path": report.no_wallet_or_auth_path,
        "paper_only_enforced": report.paper_only_enforced,
        "operator_manual_only": report.operator_manual_only,
        "public_payload_safe": report.public_payload_safe,
        "supabase_persistence_ready": report.supabase_persistence_ready,
        "decision_gate_ready": report.decision_gate_ready,
        "review_packet_ready": report.review_packet_ready,
        "execution_interlock_ready": report.execution_interlock_ready,
        "interlock_band": report.interlock_band,
        "blocked_reason_codes": list(report.blocked_reason_codes),
        "attention_reason_codes": list(report.attention_reason_codes),
        "ready_ratio": _decimal_text(report.ready_ratio),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["digest"] = _digest_for_payload(payload)
    return payload


def _validate_public_payload(payload: dict[str, object]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("public payload must keep paper_only=True")
    if payload.get("report_only") is not True:
        raise ValueError("public payload must keep report_only=True")
    if payload.get("readonly") is not True:
        raise ValueError("public payload must keep readonly=True")
    digest = payload.get("digest")
    if type(digest) is not str or len(digest) != 64:
        raise ValueError("public payload digest must be a sha256 hex string")
    payload_without_digest = dict(payload)
    del payload_without_digest["digest"]
    if digest != _digest_for_payload(payload_without_digest):
        raise ValueError("public payload digest must match payload")
    _reject_public_numeric_values(payload)


def _digest_for_payload(payload: dict[str, object]) -> str:
    encoded = dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if reason_code != reason_code.strip():
            raise ValueError(f"{field_name} reason codes must be stripped")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _require_hard_flags(label: str, value: Any) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must keep {field_name}=True")


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(QUANTUM), "f")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (Decimal, float, int):
        raise ValueError("public payload numeric values must be decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject(
        {key: _freeze_json_value(item) for key, item in value.items()},
    )


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is list:
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value
