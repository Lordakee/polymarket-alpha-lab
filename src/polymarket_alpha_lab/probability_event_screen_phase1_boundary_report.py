"""Read-only Phase 1 boundary readiness report for probability event screens."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
)


__all__ = (
    "PHASE1_BOUNDARY_BANDS",
    "ProbabilityEventScreenPhase1BoundaryInput",
    "ProbabilityEventScreenPhase1BoundaryReport",
    "build_probability_event_screen_phase1_boundary_report",
    "probability_event_screen_phase1_boundary_report_digest",
    "probability_event_screen_phase1_boundary_report_to_payload",
    "validate_probability_event_screen_phase1_boundary_public_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CONTROL_COUNT = Decimal("8.000000")

PHASE1_BOUNDARY_BANDS = ("ready", "attention", "blocked")
READY_REASON_CODE = "probability_event_screen_phase1_boundary_ready"

BLOCKED_REASON_SEQUENCE = (
    "phase1_boundary_paper_only_not_enforced",
    "phase1_boundary_report_only_not_enforced",
    "phase1_boundary_readonly_not_enforced",
    "phase1_boundary_wallet_or_auth_path_available",
    "phase1_boundary_live_order_path_available",
    "phase1_boundary_manual_only_execution_not_ready",
    "phase1_boundary_public_payload_safety_not_ready",
    "phase1_boundary_supabase_persistence_not_ready",
)
ATTENTION_REASON_SEQUENCE = (
    "phase1_boundary_paper_only_flag_not_set",
    "phase1_boundary_report_only_flag_not_set",
    "phase1_boundary_readonly_flag_not_set",
    READY_REASON_CODE,
)
FLAG_ATTENTION_REASON_CODES = ATTENTION_REASON_SEQUENCE[:-1]

PAYLOAD_KEYS = (
    "paper_only_enforced",
    "report_only_enforced",
    "readonly_enforced",
    "no_wallet_or_auth_path",
    "no_live_order_path",
    "manual_only_execution_ready",
    "public_payload_safety_ready",
    "supabase_persistence_ready",
    "phase1_boundary_ready",
    "boundary_band",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
)

UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "postgres://",
    "postgresql://",
    "service_role",
    "bearer ",
)

_BOOL_INPUT_FIELDS = (
    "paper_only_enforced",
    "report_only_enforced",
    "readonly_enforced",
    "no_wallet_or_auth_path",
    "no_live_order_path",
    "manual_only_execution_ready",
    "public_payload_safety_ready",
    "supabase_persistence_ready",
)

_BLOCKING_CHECKS = (
    ("paper_only_enforced", "phase1_boundary_paper_only_not_enforced"),
    ("report_only_enforced", "phase1_boundary_report_only_not_enforced"),
    ("readonly_enforced", "phase1_boundary_readonly_not_enforced"),
    ("no_wallet_or_auth_path", "phase1_boundary_wallet_or_auth_path_available"),
    ("no_live_order_path", "phase1_boundary_live_order_path_available"),
    (
        "manual_only_execution_ready",
        "phase1_boundary_manual_only_execution_not_ready",
    ),
    (
        "public_payload_safety_ready",
        "phase1_boundary_public_payload_safety_not_ready",
    ),
    (
        "supabase_persistence_ready",
        "phase1_boundary_supabase_persistence_not_ready",
    ),
)


class _Phase1BoundaryPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _Phase1BoundaryPublicDataclass and issubclass(
                base,
                _Phase1BoundaryPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventScreenPhase1BoundaryInput(_Phase1BoundaryPublicDataclass):
    paper_only_enforced: bool
    report_only_enforced: bool
    readonly_enforced: bool
    no_wallet_or_auth_path: bool
    no_live_order_path: bool
    manual_only_execution_ready: bool
    public_payload_safety_ready: bool
    supabase_persistence_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenPhase1BoundaryInput,
            "Phase 1 boundary input",
        )
        for field_name in _BOOL_INPUT_FIELDS + (
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))


@dataclass(frozen=True)
class ProbabilityEventScreenPhase1BoundaryReport(_Phase1BoundaryPublicDataclass):
    paper_only_enforced: bool
    report_only_enforced: bool
    readonly_enforced: bool
    no_wallet_or_auth_path: bool
    no_live_order_path: bool
    manual_only_execution_ready: bool
    public_payload_safety_ready: bool
    supabase_persistence_ready: bool
    phase1_boundary_ready: bool
    boundary_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenPhase1BoundaryReport,
            "Phase 1 boundary report",
        )
        for field_name in _BOOL_INPUT_FIELDS + (
            "phase1_boundary_ready",
            "paper_only",
            "report_only",
            "readonly",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "boundary_band",
            _normalize_member("boundary_band", self.boundary_band),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _normalize_ratio("ready_ratio", self.ready_ratio),
        )
        _validate_report(self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_phase1_boundary_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_phase1_boundary_report_digest(self)


def build_probability_event_screen_phase1_boundary_report(
    readiness: ProbabilityEventScreenPhase1BoundaryInput,
) -> ProbabilityEventScreenPhase1BoundaryReport:
    if type(readiness) is not ProbabilityEventScreenPhase1BoundaryInput:
        raise ValueError(
            "readiness must be a ProbabilityEventScreenPhase1BoundaryInput",
        )

    blocked_reason_codes, attention_reason_codes, ready_control_count = (
        _boundary_findings(readiness)
    )
    boundary_band = _boundary_band(blocked_reason_codes, attention_reason_codes)

    return ProbabilityEventScreenPhase1BoundaryReport(
        paper_only_enforced=readiness.paper_only_enforced,
        report_only_enforced=readiness.report_only_enforced,
        readonly_enforced=readiness.readonly_enforced,
        no_wallet_or_auth_path=readiness.no_wallet_or_auth_path,
        no_live_order_path=readiness.no_live_order_path,
        manual_only_execution_ready=readiness.manual_only_execution_ready,
        public_payload_safety_ready=readiness.public_payload_safety_ready,
        supabase_persistence_ready=readiness.supabase_persistence_ready,
        phase1_boundary_ready=boundary_band == "ready",
        boundary_band=boundary_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_control_count), CONTROL_COUNT),
        paper_only=readiness.paper_only,
        report_only=readiness.report_only,
        readonly=readiness.readonly,
    )


def probability_event_screen_phase1_boundary_report_to_payload(
    report: ProbabilityEventScreenPhase1BoundaryReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenPhase1BoundaryReport:
        raise ValueError(
            "report must be a ProbabilityEventScreenPhase1BoundaryReport",
        )
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "paper_only_enforced": report.paper_only_enforced,
            "report_only_enforced": report.report_only_enforced,
            "readonly_enforced": report.readonly_enforced,
            "no_wallet_or_auth_path": report.no_wallet_or_auth_path,
            "no_live_order_path": report.no_live_order_path,
            "manual_only_execution_ready": report.manual_only_execution_ready,
            "public_payload_safety_ready": report.public_payload_safety_ready,
            "supabase_persistence_ready": report.supabase_persistence_ready,
            "phase1_boundary_ready": report.phase1_boundary_ready,
            "boundary_band": report.boundary_band,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_probability_event_screen_phase1_boundary_public_payload(payload)
    return payload


def probability_event_screen_phase1_boundary_report_digest(
    report: ProbabilityEventScreenPhase1BoundaryReport,
) -> str:
    payload = probability_event_screen_phase1_boundary_report_to_payload(report)
    return _digest_payload(payload)


def validate_probability_event_screen_phase1_boundary_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical Phase 1 boundary schema")
    _reject_unsafe_public_values(payload)
    for field_name in (
        *_BOOL_INPUT_FIELDS,
        "phase1_boundary_ready",
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_member("boundary_band", payload["boundary_band"])
    blocked_reason_codes = _normalize_payload_reason_codes(
        "blocked_reason_codes",
        payload["blocked_reason_codes"],
        BLOCKED_REASON_SEQUENCE,
    )
    attention_reason_codes = _normalize_payload_reason_codes(
        "attention_reason_codes",
        payload["attention_reason_codes"],
        ATTENTION_REASON_SEQUENCE,
    )
    ready_ratio_value = payload["ready_ratio"]
    if type(ready_ratio_value) is not str:
        raise ValueError("ready_ratio must be serialized as a string")
    ready_ratio = _normalize_ratio("ready_ratio", Decimal(ready_ratio_value))
    expected_blocked, _expected_attention, ready_control_count = _payload_findings(
        payload,
    )
    if blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match boundary fields")
    if not _payload_attention_codes_are_valid(
        blocked_reason_codes,
        attention_reason_codes,
    ):
        raise ValueError("attention_reason_codes must match boundary fields")
    expected_band = _boundary_band(blocked_reason_codes, attention_reason_codes)
    if payload["boundary_band"] != expected_band:
        raise ValueError("boundary_band must match reason codes")
    if payload["phase1_boundary_ready"] is not (expected_band == "ready"):
        raise ValueError("phase1_boundary_ready must match boundary_band")
    if ready_ratio != _ratio(_count(ready_control_count), CONTROL_COUNT):
        raise ValueError("ready_ratio must match boundary fields")
    return payload


def _payload_attention_codes_are_valid(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> bool:
    if blocked_reason_codes:
        return attention_reason_codes == ()
    if attention_reason_codes == (READY_REASON_CODE,):
        return True
    return bool(attention_reason_codes) and all(
        reason_code in FLAG_ATTENTION_REASON_CODES
        for reason_code in attention_reason_codes
    )


def _boundary_findings(
    readiness: ProbabilityEventScreenPhase1BoundaryInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocked: list[str] = []
    ready_control_count = 0
    for field_name, reason_code in _BLOCKING_CHECKS:
        if getattr(readiness, field_name) is True:
            ready_control_count += 1
        else:
            blocked.append(reason_code)

    attention: list[str] = []
    if readiness.paper_only is not True:
        attention.append("phase1_boundary_paper_only_flag_not_set")
    if readiness.report_only is not True:
        attention.append("phase1_boundary_report_only_flag_not_set")
    if readiness.readonly is not True:
        attention.append("phase1_boundary_readonly_flag_not_set")

    blocked_reason_codes = tuple(
        reason for reason in BLOCKED_REASON_SEQUENCE if reason in blocked
    )
    if blocked_reason_codes:
        return blocked_reason_codes, (), ready_control_count
    attention_reason_codes = tuple(
        reason for reason in ATTENTION_REASON_SEQUENCE if reason in attention
    )
    if not attention_reason_codes:
        attention_reason_codes = (READY_REASON_CODE,)
    return blocked_reason_codes, attention_reason_codes, ready_control_count


def _payload_findings(
    payload: Mapping[str, object],
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenPhase1BoundaryInput(
        paper_only_enforced=payload["paper_only_enforced"],  # type: ignore[arg-type]
        report_only_enforced=payload["report_only_enforced"],  # type: ignore[arg-type]
        readonly_enforced=payload["readonly_enforced"],  # type: ignore[arg-type]
        no_wallet_or_auth_path=payload["no_wallet_or_auth_path"],  # type: ignore[arg-type]
        no_live_order_path=payload["no_live_order_path"],  # type: ignore[arg-type]
        manual_only_execution_ready=payload["manual_only_execution_ready"],  # type: ignore[arg-type]
        public_payload_safety_ready=payload["public_payload_safety_ready"],  # type: ignore[arg-type]
        supabase_persistence_ready=payload["supabase_persistence_ready"],  # type: ignore[arg-type]
        paper_only=payload["paper_only"],  # type: ignore[arg-type]
        report_only=payload["report_only"],  # type: ignore[arg-type]
        readonly=payload["readonly"],  # type: ignore[arg-type]
    )
    return _boundary_findings(source)


def _validate_report(report: ProbabilityEventScreenPhase1BoundaryReport) -> None:
    blocked_reason_codes, attention_reason_codes, ready_control_count = (
        _report_findings(report)
    )
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match boundary fields")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match boundary fields")
    expected_band = _boundary_band(blocked_reason_codes, attention_reason_codes)
    if report.boundary_band != expected_band:
        raise ValueError("boundary_band must match reason codes")
    if report.phase1_boundary_ready is not (expected_band == "ready"):
        raise ValueError("phase1_boundary_ready must match boundary_band")
    if report.ready_ratio != _ratio(_count(ready_control_count), CONTROL_COUNT):
        raise ValueError("ready_ratio must match boundary fields")


def _report_findings(
    report: ProbabilityEventScreenPhase1BoundaryReport,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenPhase1BoundaryInput(
        paper_only_enforced=report.paper_only_enforced,
        report_only_enforced=report.report_only_enforced,
        readonly_enforced=report.readonly_enforced,
        no_wallet_or_auth_path=report.no_wallet_or_auth_path,
        no_live_order_path=report.no_live_order_path,
        manual_only_execution_ready=report.manual_only_execution_ready,
        public_payload_safety_ready=report.public_payload_safety_ready,
        supabase_persistence_ready=report.supabase_persistence_ready,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    return _boundary_findings(source)


def _boundary_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes != (READY_REASON_CODE,):
        return "attention"
    return "ready"


def _normalize_member(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PHASE1_BOUNDARY_BANDS:
        raise ValueError(f"{field_name} must be a supported Phase 1 boundary band")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value, supported_reason_codes)


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(
            field_name,
            tuple(value),
            supported_reason_codes,
        )
    if type(value) is tuple:
        return _normalize_reason_code_items(field_name, value, supported_reason_codes)
    raise ValueError(f"{field_name} must be a list")


def _normalize_reason_code_items(
    field_name: str,
    reason_codes: tuple[str, ...],
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in supported_reason_codes:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    ordered = tuple(
        reason_code for reason_code in supported_reason_codes if reason_code in seen
    )
    if reason_codes != ordered:
        raise ValueError(f"{field_name} must use canonical order")
    return ordered


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _reject_unsafe_public_values(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_unsafe_public_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_values(item)
        return
    if type(value) is str:
        normalized = value.lower()
        if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains unsafe private value")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_ratio("ready_ratio", numerator / denominator)


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
