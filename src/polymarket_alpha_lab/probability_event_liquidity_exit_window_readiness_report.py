"""Readonly exit-window readiness report for probability event liquidity."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "ProbabilityEventLiquidityExitWindowReadinessReport",
    "build_probability_event_liquidity_exit_window_readiness_report",
    "probability_event_liquidity_exit_window_readiness_report_payload",
    "validate_probability_event_liquidity_exit_window_readiness_public_payload",
)


DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
EXIT_WINDOW_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

READY_REASON = "exit_window_ready"
TIME_WINDOW_REASON = "insufficient_time_to_resolution_exit_window"
ENTRY_DEPTH_REASON = "entry_depth_probability_watch"
EXIT_DEPTH_REASON = "exit_depth_probability_watch"
SPREAD_REASON = "spread_probability_watch"
REASON_CODES = (
    READY_REASON,
    TIME_WINDOW_REASON,
    ENTRY_DEPTH_REASON,
    EXIT_DEPTH_REASON,
    SPREAD_REASON,
)

READY_NEXT_STEP = "monitor_exit_window"
WATCH_NEXT_STEP = "manual_review_exit_liquidity"
BLOCKED_NEXT_STEP = "do_not_enter_without_manual_exit_plan"

MIN_READY_DEPTH_PROBABILITY = Decimal("0.800000")
MAX_READY_SPREAD_PROBABILITY = Decimal("0.020000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    _join_parts("candidate", "_", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("market", "_", "question"),
    _join_parts("ques", "tion"),
    _join_parts("source", "_", "id"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "ref"),
    _join_parts("source", "_", "reference"),
    _join_parts("d", "s", "n"),
    _join_parts("table", "_", "name"),
    _join_parts("to", "ken"),
)


class _NoPublicSubclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if _NoPublicSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventLiquidityExitWindowReadinessReport(_NoPublicSubclass):
    entry_depth_probability: Decimal
    exit_depth_probability: Decimal
    time_to_resolution_hours: Decimal
    spread_probability: Decimal
    expected_exit_window_hours: Decimal
    exit_window_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventLiquidityExitWindowReadinessReport,
            "report",
        )
        for field_name in (
            "entry_depth_probability",
            "exit_depth_probability",
            "spread_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_hours",
            _require_nonnegative_decimal(
                "time_to_resolution_hours",
                self.time_to_resolution_hours,
            ),
        )
        object.__setattr__(
            self,
            "expected_exit_window_hours",
            _require_positive_decimal(
                "expected_exit_window_hours",
                self.expected_exit_window_hours,
            ),
        )
        _require_choice("exit_window_status", self.exit_window_status, EXIT_WINDOW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_choice(
            "manual_next_step",
            self.manual_next_step,
            (READY_NEXT_STEP, WATCH_NEXT_STEP, BLOCKED_NEXT_STEP),
        )
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def digest(self) -> str:
        return _canonical_digest(_base_public_payload(self))

    @property
    def public_payload(self) -> dict[str, Any]:
        return _public_payload(self)


def build_probability_event_liquidity_exit_window_readiness_report(
    *,
    entry_depth_probability: Decimal,
    exit_depth_probability: Decimal,
    time_to_resolution_hours: Decimal,
    spread_probability: Decimal,
    expected_exit_window_hours: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventLiquidityExitWindowReadinessReport:
    entry_depth = _require_ratio(
        "entry_depth_probability",
        entry_depth_probability,
    )
    exit_depth = _require_ratio("exit_depth_probability", exit_depth_probability)
    time_to_resolution = _require_nonnegative_decimal(
        "time_to_resolution_hours",
        time_to_resolution_hours,
    )
    spread = _require_ratio("spread_probability", spread_probability)
    expected_exit_window = _require_positive_decimal(
        "expected_exit_window_hours",
        expected_exit_window_hours,
    )
    evaluated = _evaluate(
        entry_depth_probability=entry_depth,
        exit_depth_probability=exit_depth,
        time_to_resolution_hours=time_to_resolution,
        spread_probability=spread,
        expected_exit_window_hours=expected_exit_window,
    )
    return ProbabilityEventLiquidityExitWindowReadinessReport(
        entry_depth_probability=entry_depth,
        exit_depth_probability=exit_depth,
        time_to_resolution_hours=time_to_resolution,
        spread_probability=spread,
        expected_exit_window_hours=expected_exit_window,
        exit_window_status=evaluated["exit_window_status"],
        reason_codes=evaluated["reason_codes"],
        manual_next_step=evaluated["manual_next_step"],
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_liquidity_exit_window_readiness_report_payload(
    report: ProbabilityEventLiquidityExitWindowReadinessReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventLiquidityExitWindowReadinessReport:
        raise ValueError(
            "report must be a ProbabilityEventLiquidityExitWindowReadinessReport",
        )
    return _public_payload(report)


def validate_probability_event_liquidity_exit_window_readiness_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _reject_public_numeric_values(payload)
    _require_payload_hard_flags(payload)
    digest = payload.get("digest")
    if type(digest) is not str:
        raise ValueError("digest must be a string")
    if len(digest) != 64:
        raise ValueError("digest must be a sha256 hex string")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError("digest must be a sha256 hex string") from exc
    unsigned = dict(payload)
    unsigned.pop("digest")
    if digest != _canonical_digest(unsigned):
        raise ValueError("digest does not match public payload")
    return True


def _evaluate(
    *,
    entry_depth_probability: Decimal,
    exit_depth_probability: Decimal,
    time_to_resolution_hours: Decimal,
    spread_probability: Decimal,
    expected_exit_window_hours: Decimal,
) -> dict[str, Any]:
    if time_to_resolution_hours < expected_exit_window_hours:
        return {
            "exit_window_status": STATUS_BLOCKED,
            "reason_codes": (TIME_WINDOW_REASON,),
            "manual_next_step": BLOCKED_NEXT_STEP,
        }

    reason_codes: list[str] = []
    if entry_depth_probability < MIN_READY_DEPTH_PROBABILITY:
        reason_codes.append(ENTRY_DEPTH_REASON)
    if exit_depth_probability < MIN_READY_DEPTH_PROBABILITY:
        reason_codes.append(EXIT_DEPTH_REASON)
    if spread_probability > MAX_READY_SPREAD_PROBABILITY:
        reason_codes.append(SPREAD_REASON)

    if reason_codes:
        return {
            "exit_window_status": STATUS_WATCH,
            "reason_codes": tuple(reason_codes),
            "manual_next_step": WATCH_NEXT_STEP,
        }
    return {
        "exit_window_status": STATUS_READY,
        "reason_codes": (READY_REASON,),
        "manual_next_step": READY_NEXT_STEP,
    }


def _validate_report(
    report: ProbabilityEventLiquidityExitWindowReadinessReport,
) -> None:
    expected = _evaluate(
        entry_depth_probability=report.entry_depth_probability,
        exit_depth_probability=report.exit_depth_probability,
        time_to_resolution_hours=report.time_to_resolution_hours,
        spread_probability=report.spread_probability,
        expected_exit_window_hours=report.expected_exit_window_hours,
    )
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match exit window readiness checks")


def _base_public_payload(
    report: ProbabilityEventLiquidityExitWindowReadinessReport,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        ProbabilityEventLiquidityExitWindowReadinessReport,
        "report",
    )
    _require_hard_flags("report", report)
    _validate_report(report)
    return {
        "entry_depth_probability": _public_decimal(report.entry_depth_probability),
        "exit_depth_probability": _public_decimal(report.exit_depth_probability),
        "time_to_resolution_hours": _public_decimal(report.time_to_resolution_hours),
        "spread_probability": _public_decimal(report.spread_probability),
        "expected_exit_window_hours": _public_decimal(
            report.expected_exit_window_hours,
        ),
        "exit_window_status": report.exit_window_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _public_payload(
    report: ProbabilityEventLiquidityExitWindowReadinessReport,
) -> dict[str, Any]:
    payload = _base_public_payload(report)
    payload["digest"] = _canonical_digest(payload)
    validate_probability_event_liquidity_exit_window_readiness_public_payload(payload)
    return payload


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _public_decimal(value: Decimal) -> str:
    return format(_require_nonnegative_decimal("public decimal", value), "f")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return ratio


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _require_choice(
    field_name: str,
    value: object,
    choices: tuple[str, ...],
) -> None:
    _require_canonical_string(field_name, value)
    if value not in choices:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_exact_type(
    value: object,
    expected_type: type[object],
    label: str,
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be an exact {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must have {field_name}=True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload must have {field_name}=True")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError("payload contains unsafe public key")
            _reject_unsafe_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)
    elif type(value) in (Decimal, float, int):
        raise ValueError("public payload numeric values must be strings")
