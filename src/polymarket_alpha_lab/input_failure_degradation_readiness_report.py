import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Iterable


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")

_READY_STATUS = "ready_readonly"
_WATCH_STATUS = "watch_readonly_degraded"
_BLOCKED_STATUS = "blocked_readonly_degraded"

_READY_REASON = "all_required_inputs_available"
_MISSING_SIGNALS_REASON = "input_failure_signals_missing"
_REQUIRED_FAILED_REASON = "required_input_failed"
_OPTIONAL_FAILED_REASON = "optional_input_failed"
_MANUAL_REVIEW_REASON = "manual_review_required"
_RECOMMENDATION_PROHIBITED_REASON = "recommendation_prohibited"

__all__ = (
    "InputFailureDegradationReadinessReport",
    "InputFailureSignal",
    "build_input_failure_degradation_readiness_report",
)


class _FrozenJsonObject(dict[str, Any]):
    def __new__(cls, values: dict[str, Any]) -> "_FrozenJsonObject":
        instance = super().__new__(cls)
        dict.update(instance, values)
        return instance

    def __init__(self, values: dict[str, Any]) -> None:
        pass

    def _readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public payload is immutable")

    __setitem__ = _readonly
    __delitem__ = _readonly
    clear = _readonly
    pop = _readonly
    popitem = _readonly
    setdefault = _readonly
    update = _readonly
    __ior__ = _readonly


class _FrozenJsonArray(list[Any]):
    def __new__(cls, values: Iterable[Any]) -> "_FrozenJsonArray":
        instance = super().__new__(cls)
        list.extend(instance, values)
        return instance

    def __init__(self, values: Iterable[Any]) -> None:
        pass

    def _readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public payload is immutable")

    __setitem__ = _readonly
    __delitem__ = _readonly
    append = _readonly
    clear = _readonly
    extend = _readonly
    insert = _readonly
    pop = _readonly
    remove = _readonly
    reverse = _readonly
    sort = _readonly
    __iadd__ = _readonly
    __imul__ = _readonly


@dataclass(frozen=True)
class InputFailureSignal:
    source_name: str
    failed: bool
    required: bool
    blocking_reason: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not InputFailureSignal:
            raise TypeError("InputFailureSignal does not support subclassing")

    def __post_init__(self) -> None:
        _validate_signal(self)


@dataclass(frozen=True)
class InputFailureDegradationReadinessReport:
    generated_at: datetime
    degradation_status: str
    manual_review_required: bool
    recommendation_allowed: bool
    reason_codes: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    prohibited_recommendation_conditions: tuple[str, ...]
    input_count: Decimal
    failed_input_count: Decimal
    required_failed_input_count: Decimal
    signals: tuple[InputFailureSignal, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload_digest: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not InputFailureDegradationReadinessReport:
            raise TypeError(
                "InputFailureDegradationReadinessReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not InputFailureDegradationReadinessReport:
            raise ValueError(
                "report must be exactly InputFailureDegradationReadinessReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(self, "signals", _normalize_signals(self.signals))
        _validate_report_values(self)
        expected_digest = _payload_digest(self)
        if type(self.payload_digest) is str and self.payload_digest == "":
            object.__setattr__(self, "payload_digest", expected_digest)
        else:
            _require_digest("payload_digest", self.payload_digest)
            if self.payload_digest != expected_digest:
                raise ValueError("payload_digest must match report payload")

    @property
    def public_payload(self) -> _FrozenJsonObject:
        _validate_report(self)
        payload = _payload_without_digest(self)
        payload["payload_digest"] = self.payload_digest
        return _freeze_json_object(payload)


def build_input_failure_degradation_readiness_report(
    signals: Iterable[InputFailureSignal],
    *,
    generated_at: datetime,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> InputFailureDegradationReadinessReport:
    normalized_signals = _normalize_signals(signals)
    generated_at_utc = _as_utc("generated_at", generated_at)
    status = _degradation_status(normalized_signals)
    return InputFailureDegradationReadinessReport(
        generated_at=generated_at_utc,
        degradation_status=status,
        manual_review_required=status != _READY_STATUS,
        recommendation_allowed=status == _READY_STATUS,
        reason_codes=_reason_codes(normalized_signals),
        blocking_reasons=_blocking_reasons(normalized_signals),
        prohibited_recommendation_conditions=_prohibited_conditions(status),
        input_count=_decimal_count(len(normalized_signals)),
        failed_input_count=_decimal_count(
            len(tuple(signal for signal in normalized_signals if signal.failed)),
        ),
        required_failed_input_count=_decimal_count(
            len(
                tuple(
                    signal
                    for signal in normalized_signals
                    if signal.failed and signal.required
                ),
            ),
        ),
        signals=normalized_signals,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _payload_without_digest(
    report: InputFailureDegradationReadinessReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "degradation_status": report.degradation_status,
        "manual_review_required": report.manual_review_required,
        "recommendation_allowed": report.recommendation_allowed,
        "reason_codes": list(report.reason_codes),
        "blocking_reasons": list(report.blocking_reasons),
        "prohibited_recommendation_conditions": list(
            report.prohibited_recommendation_conditions,
        ),
        "input_count": _decimal_text(report.input_count),
        "failed_input_count": _decimal_text(report.failed_input_count),
        "required_failed_input_count": _decimal_text(
            report.required_failed_input_count,
        ),
        "signals": [
            {
                "source_name": signal.source_name,
                "failed": signal.failed,
                "required": signal.required,
                "blocking_reason": signal.blocking_reason,
                "paper_only": signal.paper_only,
                "report_only": signal.report_only,
                "readonly": signal.readonly,
            }
            for signal in report.signals
        ],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _degradation_status(signals: tuple[InputFailureSignal, ...]) -> str:
    if not signals:
        return _BLOCKED_STATUS
    if any(signal.failed and signal.required for signal in signals):
        return _BLOCKED_STATUS
    if any(signal.failed for signal in signals):
        return _WATCH_STATUS
    return _READY_STATUS


def _reason_codes(signals: tuple[InputFailureSignal, ...]) -> tuple[str, ...]:
    if not signals:
        return (
            _MISSING_SIGNALS_REASON,
            _MANUAL_REVIEW_REASON,
            _RECOMMENDATION_PROHIBITED_REASON,
        )
    if any(signal.failed and signal.required for signal in signals):
        return (
            _REQUIRED_FAILED_REASON,
            _MANUAL_REVIEW_REASON,
            _RECOMMENDATION_PROHIBITED_REASON,
        )
    if any(signal.failed for signal in signals):
        return (
            _OPTIONAL_FAILED_REASON,
            _MANUAL_REVIEW_REASON,
            _RECOMMENDATION_PROHIBITED_REASON,
        )
    return (_READY_REASON,)


def _blocking_reasons(signals: tuple[InputFailureSignal, ...]) -> tuple[str, ...]:
    if not signals:
        return (_MISSING_SIGNALS_REASON,)
    return tuple(signal.blocking_reason for signal in signals if signal.failed)


def _prohibited_conditions(status: str) -> tuple[str, ...]:
    if status == _READY_STATUS:
        return (
            "phase_one_paper_only",
            "phase_one_report_only",
            "phase_one_readonly",
        )
    if status == _WATCH_STATUS:
        return ("manual_review_pending", "readonly_degraded_state")
    return (
        "missing_required_input",
        "manual_review_pending",
        "readonly_degraded_state",
    )


def _normalize_signals(
    signals: Iterable[InputFailureSignal],
) -> tuple[InputFailureSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        normalized = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen_source_names: set[str] = set()
    for signal in normalized:
        if type(signal) is not InputFailureSignal:
            raise ValueError("signals must contain InputFailureSignal values")
        _validate_signal(signal)
        if signal.source_name in seen_source_names:
            raise ValueError("signals must contain unique source_name values")
        seen_source_names.add(signal.source_name)
    return tuple(sorted(normalized, key=lambda signal: signal.source_name))


def _require_identifier(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    if value != value.strip() or value.lower() != value:
        raise ValueError(f"{name} must be a canonical lowercase string")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-.")
    if any(character not in allowed for character in value):
        raise ValueError(f"{name} must be a canonical lowercase string")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a timezone-aware datetime") from exc
    if offset is None:
        raise ValueError(f"{name} must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_flags(value: object) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if getattr(value, name) is not True:
            raise ValueError(f"{name} must be True")


def _require_status(value: str) -> None:
    if type(value) is not str or value not in (
        _READY_STATUS,
        _WATCH_STATUS,
        _BLOCKED_STATUS,
    ):
        raise ValueError("degradation_status is not supported")


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _decimal_text(value: Decimal) -> str:
    _require_count_decimal("count field", value)
    return f"{value:f}"


def _validate_signal(signal: InputFailureSignal) -> None:
    if type(signal) is not InputFailureSignal:
        raise ValueError("signal must be exactly InputFailureSignal")
    _require_identifier("source_name", signal.source_name)
    _require_bool("failed", signal.failed)
    _require_bool("required", signal.required)
    _require_identifier("blocking_reason", signal.blocking_reason)
    _require_flags(signal)


def _require_count_decimal(name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must use positive zero")
    if value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    if value.as_tuple().exponent != _QUANT.as_tuple().exponent:
        raise ValueError(f"{name} must use six decimal places")


def _require_digest(name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be a lowercase sha256 digest")


def _validate_report_values(
    report: InputFailureDegradationReadinessReport,
) -> None:
    if type(report) is not InputFailureDegradationReadinessReport:
        raise ValueError(
            "report must be exactly InputFailureDegradationReadinessReport",
        )
    normalized_generated_at = _as_utc("generated_at", report.generated_at)
    if (
        report.generated_at.tzinfo is not UTC
        or report.generated_at != normalized_generated_at
    ):
        raise ValueError("generated_at must be normalized to UTC")
    normalized_signals = _normalize_signals(report.signals)
    if type(report.signals) is not tuple or report.signals != normalized_signals:
        raise ValueError("signals must be a canonical tuple")
    for field_name in (
        "reason_codes",
        "blocking_reasons",
        "prohibited_recommendation_conditions",
    ):
        _require_exact_string_tuple(field_name, getattr(report, field_name))
    _require_flags(report)

    expected_status = _degradation_status(report.signals)
    expected_manual_review = expected_status != _READY_STATUS
    expected_recommendation_allowed = expected_status == _READY_STATUS
    expected_reason_codes = _reason_codes(report.signals)
    expected_blocking_reasons = _blocking_reasons(report.signals)
    expected_prohibited_conditions = _prohibited_conditions(expected_status)
    expected_input_count = _decimal_count(len(report.signals))
    expected_failed_count = _decimal_count(
        sum(1 for signal in report.signals if signal.failed),
    )
    expected_required_failed_count = _decimal_count(
        sum(1 for signal in report.signals if signal.failed and signal.required),
    )

    _require_status(report.degradation_status)
    if report.degradation_status != expected_status:
        raise ValueError("degradation_status must match input failures")
    _require_bool("manual_review_required", report.manual_review_required)
    if report.manual_review_required is not expected_manual_review:
        raise ValueError("manual_review_required must match input failures")
    _require_bool("recommendation_allowed", report.recommendation_allowed)
    if report.recommendation_allowed is not expected_recommendation_allowed:
        raise ValueError("recommendation_allowed must match input failures")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match input failures")
    if report.blocking_reasons != expected_blocking_reasons:
        raise ValueError("blocking_reasons must match input failures")
    if report.prohibited_recommendation_conditions != expected_prohibited_conditions:
        raise ValueError(
            "prohibited_recommendation_conditions must match input failures",
        )

    expected_counts = {
        "input_count": expected_input_count,
        "failed_input_count": expected_failed_count,
        "required_failed_input_count": expected_required_failed_count,
    }
    for name, expected_value in expected_counts.items():
        value = getattr(report, name)
        _require_count_decimal(name, value)
        if value != expected_value:
            raise ValueError(f"{name} must match signals")


def _require_exact_string_tuple(name: str, value: object) -> None:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be exactly a tuple")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{name} must contain exact string values")


def _payload_digest(report: InputFailureDegradationReadinessReport) -> str:
    encoded = json.dumps(
        _payload_without_digest(report),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_report(report: InputFailureDegradationReadinessReport) -> None:
    _validate_report_values(report)
    _require_digest("payload_digest", report.payload_digest)
    if report.payload_digest != _payload_digest(report):
        raise ValueError("payload_digest must match report payload")


def _freeze_json_object(value: dict[str, Any]) -> _FrozenJsonObject:
    return _FrozenJsonObject(
        {key: _freeze_json_value(item) for key, item in value.items()},
    )


def _freeze_json_value(value: Any) -> Any:
    if type(value) is dict:
        return _freeze_json_object(value)
    if type(value) is list:
        return _FrozenJsonArray(_freeze_json_value(item) for item in value)
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("public payload must contain only JSON values")
