"""Pure read-only manual preflight readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "MANUAL_TICKET_PREFLIGHT_CHECK_FIELDS",
    "ManualTradePreflightReadinessInput",
    "ManualTradePreflightReadinessReport",
    "build_manual_trade_preflight_readiness_report",
    "manual_trade_preflight_readiness_report_to_payload",
)


QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CHECK_COUNT = Decimal("5.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
MANUAL_TICKET_PREFLIGHT_CHECK_FIELDS = (
    "decision_ticket_ready",
    "cost_gate_ready",
    "source_quorum_ready",
    "team_routing_ready",
    "settlement_risk_ready",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ManualTradePreflightReadinessInput(_FinalDataclass):
    decision_ticket_ready: Decimal
    cost_gate_ready: Decimal
    source_quorum_ready: Decimal
    team_routing_ready: Decimal
    settlement_risk_ready: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ManualTradePreflightReadinessInput, "preflight input")
        for field_name in MANUAL_TICKET_PREFLIGHT_CHECK_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("preflight input", self)


@dataclass(frozen=True)
class ManualTradePreflightReadinessReport(_FinalDataclass):
    can_present_manual_ticket: bool
    blocked_check_count: Decimal
    attention_check_count: Decimal
    ready_check_ratio: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ManualTradePreflightReadinessReport, "preflight report")
        if type(self.can_present_manual_ticket) is not bool:
            raise ValueError("can_present_manual_ticket must be a bool")
        for field_name in ("blocked_check_count", "attention_check_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_check_ratio",
            _normalize_ratio("ready_check_ratio", self.ready_check_ratio),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("preflight report", self)


def build_manual_trade_preflight_readiness_report(
    readiness: ManualTradePreflightReadinessInput,
) -> ManualTradePreflightReadinessReport:
    if type(readiness) is not ManualTradePreflightReadinessInput:
        raise ValueError("readiness must be a ManualTradePreflightReadinessInput")
    _require_hard_flags("preflight input", readiness)

    blocked_codes = tuple(
        f"manual_trade_preflight_{_check_reason_name(field_name)}_blocked"
        for field_name in MANUAL_TICKET_PREFLIGHT_CHECK_FIELDS
        if getattr(readiness, field_name) == ZERO
    )
    attention_codes = tuple(
        f"manual_trade_preflight_{_check_reason_name(field_name)}_attention"
        for field_name in MANUAL_TICKET_PREFLIGHT_CHECK_FIELDS
        if ZERO < getattr(readiness, field_name) < ONE
    )
    ready_count = _count(
        sum(
            1
            for field_name in MANUAL_TICKET_PREFLIGHT_CHECK_FIELDS
            if getattr(readiness, field_name) == ONE
        ),
    )
    reason_codes = blocked_codes + attention_codes
    if not reason_codes:
        reason_codes = ("manual_trade_preflight_all_checks_ready",)

    return ManualTradePreflightReadinessReport(
        can_present_manual_ticket=not blocked_codes,
        blocked_check_count=_count(len(blocked_codes)),
        attention_check_count=_count(len(attention_codes)),
        ready_check_ratio=_ratio(ready_count, CHECK_COUNT),
        reason_codes=reason_codes,
        paper_only=readiness.paper_only,
        report_only=readiness.report_only,
        readonly=readiness.readonly,
    )


def manual_trade_preflight_readiness_report_to_payload(
    report: ManualTradePreflightReadinessReport,
) -> dict[str, object]:
    if type(report) is not ManualTradePreflightReadinessReport:
        raise ValueError("report must be a ManualTradePreflightReadinessReport")
    _require_hard_flags("preflight report", report)
    _validate_report(report)
    return {
        "can_present_manual_ticket": report.can_present_manual_ticket,
        "blocked_check_count": _decimal_text(report.blocked_check_count),
        "attention_check_count": _decimal_text(report.attention_check_count),
        "ready_check_ratio": _decimal_text(report.ready_check_ratio),
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        if type(reason_code) is not str or not reason_code:
            raise ValueError("reason_codes must contain non-empty strings")
        if reason_code != reason_code.strip():
            raise ValueError("reason_codes must be stripped")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(normalized)


def _require_hard_flags(label: str, value: Any) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must keep {field_name}=True")


def _validate_report(report: ManualTradePreflightReadinessReport) -> None:
    if report.blocked_check_count + report.attention_check_count > CHECK_COUNT:
        raise ValueError("blocked and attention check counts exceed check count")
    if report.can_present_manual_ticket != (report.blocked_check_count == ZERO):
        raise ValueError("can_present_manual_ticket must match blocked_check_count")
    if report.reason_codes == ("manual_trade_preflight_all_checks_ready",):
        if report.blocked_check_count != ZERO or report.attention_check_count != ZERO:
            raise ValueError("all-checks-ready reason requires no blocked or attention checks")
        if report.ready_check_ratio != ONE:
            raise ValueError("all-checks-ready reason requires ready_check_ratio=1.000000")
    else:
        blocked_reason_count = _count(
            sum(1 for reason_code in report.reason_codes if reason_code.endswith("_blocked")),
        )
        attention_reason_count = _count(
            sum(1 for reason_code in report.reason_codes if reason_code.endswith("_attention")),
        )
        if blocked_reason_count != report.blocked_check_count:
            raise ValueError("blocked_check_count must match blocked reason codes")
        if attention_reason_count != report.attention_check_count:
            raise ValueError("attention_check_count must match attention reason codes")


def _check_reason_name(field_name: str) -> str:
    return field_name.removesuffix("_ready")


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(QUANTUM), "f")
