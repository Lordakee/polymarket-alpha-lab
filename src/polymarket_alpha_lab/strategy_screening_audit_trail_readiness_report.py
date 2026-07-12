"""Pure paper-only audit readiness reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


READY_REASON = "strategy_screening_audit_trail_readiness_ready"
SCREEN_CONTRACT_MISSING_REASON = (
    "strategy_screening_audit_trail_screen_contract_digest_missing"
)
RESEARCH_PACKET_MISSING_REASON = (
    "strategy_screening_audit_trail_research_packet_digest_missing"
)
COST_GATE_MISSING_REASON = "strategy_screening_audit_trail_cost_gate_digest_missing"
TEAM_ROUTE_MISSING_REASON = "strategy_screening_audit_trail_team_route_digest_missing"
MEMORY_CONTEXT_MISSING_REASON = (
    "strategy_screening_audit_trail_memory_context_digest_missing"
)
OPERATOR_SAFETY_MISSING_REASON = (
    "strategy_screening_audit_trail_operator_safety_digest_missing"
)
SUPABASE_PERSISTENCE_ATTENTION_REASON = (
    "strategy_screening_audit_trail_supabase_persistence_not_ready"
)
EPHEMERAL_LOG_ATTENTION_REASON = (
    "strategy_screening_audit_trail_ephemeral_log_not_excluded"
)

BLOCKED_REASON_BY_DIGEST_FIELD = {
    "screen_contract_digest_present": SCREEN_CONTRACT_MISSING_REASON,
    "research_packet_digest_present": RESEARCH_PACKET_MISSING_REASON,
    "cost_gate_digest_present": COST_GATE_MISSING_REASON,
    "team_route_digest_present": TEAM_ROUTE_MISSING_REASON,
    "memory_context_digest_present": MEMORY_CONTEXT_MISSING_REASON,
    "operator_safety_digest_present": OPERATOR_SAFETY_MISSING_REASON,
}
INPUT_FIELDS = (
    "screen_contract_digest_present",
    "research_packet_digest_present",
    "cost_gate_digest_present",
    "team_route_digest_present",
    "memory_context_digest_present",
    "operator_safety_digest_present",
    "supabase_persistence_ready",
    "ephemeral_log_excluded",
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

__all__ = (
    "StrategyScreeningAuditTrailReadinessReport",
    "build_strategy_screening_audit_trail_readiness_report",
    "strategy_screening_audit_trail_readiness_digest",
    "strategy_screening_audit_trail_readiness_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class StrategyScreeningAuditTrailReadinessReport(_FinalDataclass):
    screen_contract_digest_present: bool
    research_packet_digest_present: bool
    cost_gate_digest_present: bool
    team_route_digest_present: bool
    memory_context_digest_present: bool
    operator_safety_digest_present: bool
    supabase_persistence_ready: bool
    ephemeral_log_excluded: bool
    audit_trail_ready: bool
    missing_digest_count: Decimal
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyScreeningAuditTrailReadinessReport, "report")
        for field_name in INPUT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_bool("audit_trail_ready", self.audit_trail_ready)
        object.__setattr__(
            self,
            "missing_digest_count",
            _require_nonnegative_decimal("missing_digest_count", self.missing_digest_count),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(self.blocked_reason_codes),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(self.attention_reason_codes),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_flags(self)
        _validate_report(self)
        expected_digest = _digest_for_report(self)
        if self.digest == "":
            object.__setattr__(self, "digest", expected_digest)
        elif self.digest != expected_digest:
            raise ValueError("digest must match public payload")
        _require_digest("digest", self.digest)

    @property
    def public_payload(self) -> dict[str, object]:
        return strategy_screening_audit_trail_readiness_payload(self)


def build_strategy_screening_audit_trail_readiness_report(
    *,
    screen_contract_digest_present: bool,
    research_packet_digest_present: bool,
    cost_gate_digest_present: bool,
    team_route_digest_present: bool,
    memory_context_digest_present: bool,
    operator_safety_digest_present: bool,
    supabase_persistence_ready: bool,
    ephemeral_log_excluded: bool,
) -> StrategyScreeningAuditTrailReadinessReport:
    inputs = {
        "screen_contract_digest_present": _require_bool(
            "screen_contract_digest_present",
            screen_contract_digest_present,
        ),
        "research_packet_digest_present": _require_bool(
            "research_packet_digest_present",
            research_packet_digest_present,
        ),
        "cost_gate_digest_present": _require_bool(
            "cost_gate_digest_present",
            cost_gate_digest_present,
        ),
        "team_route_digest_present": _require_bool(
            "team_route_digest_present",
            team_route_digest_present,
        ),
        "memory_context_digest_present": _require_bool(
            "memory_context_digest_present",
            memory_context_digest_present,
        ),
        "operator_safety_digest_present": _require_bool(
            "operator_safety_digest_present",
            operator_safety_digest_present,
        ),
        "supabase_persistence_ready": _require_bool(
            "supabase_persistence_ready",
            supabase_persistence_ready,
        ),
        "ephemeral_log_excluded": _require_bool(
            "ephemeral_log_excluded",
            ephemeral_log_excluded,
        ),
    }
    blocked_reason_codes = tuple(
        reason
        for field_name, reason in BLOCKED_REASON_BY_DIGEST_FIELD.items()
        if not inputs[field_name]
    )
    attention_reason_codes = _attention_reasons(
        supabase_persistence_ready=inputs["supabase_persistence_ready"],
        ephemeral_log_excluded=inputs["ephemeral_log_excluded"],
        blocked_reason_codes=blocked_reason_codes,
    )
    present_count = _decimal_count(
        sum(ONE for field_name in INPUT_FIELDS if inputs[field_name]),
    )
    total_count = _decimal_count(len(INPUT_FIELDS))
    return StrategyScreeningAuditTrailReadinessReport(
        **inputs,
        audit_trail_ready=not blocked_reason_codes
        and inputs["supabase_persistence_ready"]
        and inputs["ephemeral_log_excluded"],
        missing_digest_count=_decimal_count(len(blocked_reason_codes)),
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(present_count, total_count),
    )


def strategy_screening_audit_trail_readiness_payload(
    report: StrategyScreeningAuditTrailReadinessReport,
) -> dict[str, object]:
    if type(report) is not StrategyScreeningAuditTrailReadinessReport:
        raise ValueError("report must be a StrategyScreeningAuditTrailReadinessReport")
    _require_flags(report)
    _validate_report(report)
    if report.digest != _digest_for_report(report):
        raise ValueError("digest must match public payload")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    return payload


def strategy_screening_audit_trail_readiness_digest(
    report: StrategyScreeningAuditTrailReadinessReport,
) -> str:
    if type(report) is not StrategyScreeningAuditTrailReadinessReport:
        raise ValueError("report must be a StrategyScreeningAuditTrailReadinessReport")
    _require_flags(report)
    _validate_report(report)
    return _digest_for_report(report)


def _attention_reasons(
    *,
    supabase_persistence_ready: bool,
    ephemeral_log_excluded: bool,
    blocked_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not supabase_persistence_ready:
        reasons.append(SUPABASE_PERSISTENCE_ATTENTION_REASON)
    if not ephemeral_log_excluded:
        reasons.append(EPHEMERAL_LOG_ATTENTION_REASON)
    if not reasons and not blocked_reason_codes:
        reasons.append(READY_REASON)
    return tuple(reasons)


def _validate_report(report: StrategyScreeningAuditTrailReadinessReport) -> None:
    expected_blocked = tuple(
        reason
        for field_name, reason in BLOCKED_REASON_BY_DIGEST_FIELD.items()
        if not getattr(report, field_name)
    )
    if report.blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match missing digest inputs")
    expected_missing = _decimal_count(len(expected_blocked))
    if report.missing_digest_count != expected_missing:
        raise ValueError("missing_digest_count must match missing digest inputs")
    expected_attention = _attention_reasons(
        supabase_persistence_ready=report.supabase_persistence_ready,
        ephemeral_log_excluded=report.ephemeral_log_excluded,
        blocked_reason_codes=expected_blocked,
    )
    if report.attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match guard inputs")
    expected_ready = (
        not expected_blocked
        and report.supabase_persistence_ready
        and report.ephemeral_log_excluded
    )
    if report.audit_trail_ready is not expected_ready:
        raise ValueError("audit_trail_ready must match readiness inputs")
    present_count = _decimal_count(
        sum(ONE for field_name in INPUT_FIELDS if getattr(report, field_name)),
    )
    expected_ratio = _ratio(present_count, _decimal_count(len(INPUT_FIELDS)))
    if report.ready_ratio != expected_ratio:
        raise ValueError("ready_ratio must match digest inputs")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    raise ValueError(f"unsupported public value type: {type(value).__name__}")


def _digest_payload(report: StrategyScreeningAuditTrailReadinessReport) -> dict[str, object]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    payload = dict(payload)
    payload["digest"] = ""
    return payload


def _digest_for_report(report: StrategyScreeningAuditTrailReadinessReport) -> str:
    encoded = json.dumps(
        _digest_payload(report),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _decimal_count(value: object) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _format_decimal(value: Decimal) -> str:
    return f"{_quantize(value):.6f}"


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        quantized = _quantize(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be six-decimal") from exc
    if value != quantized:
        raise ValueError(f"{field_name} must be six-decimal")
    return quantized


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value or value.strip() != value:
            raise ValueError("reason code must be a non-empty canonical string")
        if not value.replace("_", "").isalnum() or not value.islower():
            raise ValueError("reason code must be a non-empty canonical string")
        normalized.append(value)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(normalized)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be true")
