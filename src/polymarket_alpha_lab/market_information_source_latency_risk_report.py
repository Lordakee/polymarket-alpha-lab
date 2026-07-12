"""Readonly market information source latency risk report reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
CAPTURE_AGE_WATCH_HOURS = Decimal("2.000000")
CAPTURE_AGE_BLOCK_HOURS = Decimal("4.000000")
MOVE_WATCH_PROBABILITY = Decimal("0.500000")
MOVE_BLOCK_PROBABILITY = Decimal("0.750000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

PASS_REASON = "information_source_latency_within_limit"
OFFICIAL_ABOVE_LIMIT_REASON = "official_source_latency_above_limit"
ALTERNATIVE_ABOVE_LIMIT_REASON = "alternative_source_latency_above_limit"
CAPTURE_AGE_HIGH_REASON = "capture_age_high"
MOVE_PROBABILITY_HIGH_REASON = "market_move_probability_high"
REASON_CODES = (
    OFFICIAL_ABOVE_LIMIT_REASON,
    ALTERNATIVE_ABOVE_LIMIT_REASON,
    CAPTURE_AGE_HIGH_REASON,
    MOVE_PROBABILITY_HIGH_REASON,
    PASS_REASON,
)

STEP_CONTINUE = "continue_manual_review"
STEP_RECHECK = "manually_recheck_public_sources"
STEP_PAUSE_REFRESH = "pause_and_refresh_information_manually"
MANUAL_STEPS = (STEP_CONTINUE, STEP_RECHECK, STEP_PAUSE_REFRESH)

__all__ = (
    "MarketInformationSourceLatencyRiskReport",
    "build_market_information_source_latency_risk_report",
    "market_information_source_latency_risk_report_digest",
    "market_information_source_latency_risk_report_to_public_payload",
    "validate_market_information_source_latency_risk_report_payload",
)


@dataclass(frozen=True)
class MarketInformationSourceLatencyRiskReport:
    official_source_latency_ms: Decimal
    alternative_source_latency_ms: Decimal
    capture_age_hours: Decimal
    market_move_probability: Decimal
    max_latency_ms: Decimal
    latency_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not MarketInformationSourceLatencyRiskReport:
            raise TypeError(
                "MarketInformationSourceLatencyRiskReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketInformationSourceLatencyRiskReport, "report")
        for name in (
            "official_source_latency_ms",
            "alternative_source_latency_ms",
            "capture_age_hours",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "market_move_probability",
            _require_ratio_decimal(
                "market_move_probability",
                self.market_move_probability,
            ),
        )
        object.__setattr__(
            self,
            "max_latency_ms",
            _require_positive_decimal("max_latency_ms", self.max_latency_ms),
        )
        _require_status("latency_status", self.latency_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes),
        )
        _require_manual_step("manual_next_step", self.manual_next_step)
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.payload_digest == "":
            object.__setattr__(
                self,
                "payload_digest",
                _payload_digest(_payload_value(self, include_digest=False)),
            )
        else:
            _require_sha256("payload_digest", self.payload_digest)
            _require_matching_digest(_payload_value(self, include_digest=True))

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_information_source_latency_risk_report_to_public_payload(self)


def build_market_information_source_latency_risk_report(
    *,
    official_source_latency_ms: Decimal,
    alternative_source_latency_ms: Decimal,
    capture_age_hours: Decimal,
    market_move_probability: Decimal,
    max_latency_ms: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketInformationSourceLatencyRiskReport:
    values = {
        "official_source_latency_ms": _require_nonnegative_decimal(
            "official_source_latency_ms",
            official_source_latency_ms,
        ),
        "alternative_source_latency_ms": _require_nonnegative_decimal(
            "alternative_source_latency_ms",
            alternative_source_latency_ms,
        ),
        "capture_age_hours": _require_nonnegative_decimal(
            "capture_age_hours",
            capture_age_hours,
        ),
        "market_move_probability": _require_ratio_decimal(
            "market_move_probability",
            market_move_probability,
        ),
        "max_latency_ms": _require_positive_decimal("max_latency_ms", max_latency_ms),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    _require_hard_flags("input", _FlagView(paper_only, report_only, readonly))
    reasons = _reason_codes(
        official_source_latency_ms=values["official_source_latency_ms"],
        alternative_source_latency_ms=values["alternative_source_latency_ms"],
        capture_age_hours=values["capture_age_hours"],
        market_move_probability=values["market_move_probability"],
        max_latency_ms=values["max_latency_ms"],
    )
    status = _latency_status(reasons)
    report_values = {
        **values,
        "latency_status": status,
        "reason_codes": reasons,
        "manual_next_step": _manual_next_step(status),
        "payload_digest": "",
    }
    return MarketInformationSourceLatencyRiskReport(**report_values)


def market_information_source_latency_risk_report_digest(
    report: MarketInformationSourceLatencyRiskReport,
) -> str:
    _require_exact_type(report, MarketInformationSourceLatencyRiskReport, "report")
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_digest=True)
    _require_matching_digest(payload)
    return report.payload_digest


def market_information_source_latency_risk_report_to_public_payload(
    report: MarketInformationSourceLatencyRiskReport,
) -> dict[str, Any]:
    _require_exact_type(report, MarketInformationSourceLatencyRiskReport, "report")
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_digest=True)
    _require_matching_digest(payload)
    return payload


def validate_market_information_source_latency_risk_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_payload_numeric_objects(payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    _require_payload_report_shape(payload)
    return True


@dataclass(frozen=True)
class _FlagView:
    paper_only: bool
    report_only: bool
    readonly: bool


def _reason_codes(
    *,
    official_source_latency_ms: Decimal,
    alternative_source_latency_ms: Decimal,
    capture_age_hours: Decimal,
    market_move_probability: Decimal,
    max_latency_ms: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if official_source_latency_ms > max_latency_ms:
        reasons.append(OFFICIAL_ABOVE_LIMIT_REASON)
    if alternative_source_latency_ms > max_latency_ms:
        reasons.append(ALTERNATIVE_ABOVE_LIMIT_REASON)
    if capture_age_hours >= CAPTURE_AGE_BLOCK_HOURS:
        reasons.append(CAPTURE_AGE_HIGH_REASON)
    if market_move_probability >= MOVE_BLOCK_PROBABILITY:
        reasons.append(MOVE_PROBABILITY_HIGH_REASON)
    if not reasons:
        return (PASS_REASON,)
    return tuple(reasons)


def _latency_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    if (
        ALTERNATIVE_ABOVE_LIMIT_REASON in reason_codes
        or CAPTURE_AGE_HIGH_REASON in reason_codes
        or MOVE_PROBABILITY_HIGH_REASON in reason_codes
    ):
        return STATUS_BLOCK
    return STATUS_WATCH


def _manual_next_step(status: str) -> str:
    if status == STATUS_PASS:
        return STEP_CONTINUE
    if status == STATUS_WATCH:
        return STEP_RECHECK
    if status == STATUS_BLOCK:
        return STEP_PAUSE_REFRESH
    raise ValueError("latency_status must be supported")


def _validate_report(report: MarketInformationSourceLatencyRiskReport) -> None:
    expected_reasons = _reason_codes(
        official_source_latency_ms=report.official_source_latency_ms,
        alternative_source_latency_ms=report.alternative_source_latency_ms,
        capture_age_hours=report.capture_age_hours,
        market_move_probability=report.market_move_probability,
        max_latency_ms=report.max_latency_ms,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report inputs")
    expected_status = _latency_status(expected_reasons)
    if report.latency_status != expected_status:
        raise ValueError("latency_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match latency_status")


def _payload_value(
    value: Any,
    *,
    include_digest: bool,
) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(
            {
                field.name: getattr(value, field.name)
                for field in fields(value)
                if include_digest or field.name != "payload_digest"
            },
            include_digest=include_digest,
        )
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is str:
        if not value:
            raise ValueError("public payload strings must be non-empty")
        return value
    if type(value) is bool or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for name, item in value.items():
            if type(name) is not str:
                raise ValueError("public payload names must be strings")
            payload[name] = _payload_value(item, include_digest=include_digest)
        return payload
    raise ValueError("public payload contains unsupported value")


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(_canonical_payload(payload), separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _canonical_payload(value: Any) -> Any:
    if type(value) is dict:
        return {name: _canonical_payload(value[name]) for name in sorted(value)}
    if type(value) is list:
        return [_canonical_payload(item) for item in value]
    return value


def _require_matching_digest(payload: Any) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    if "payload_digest" not in payload:
        raise ValueError("payload_digest is required")
    _require_sha256("payload_digest", payload["payload_digest"])
    material = {name: item for name, item in payload.items() if name != "payload_digest"}
    if payload["payload_digest"] != _payload_digest(material):
        raise ValueError("payload_digest does not match public payload")


def _require_payload_report_shape(payload: dict[str, Any]) -> None:
    required_names = (
        "official_source_latency_ms",
        "alternative_source_latency_ms",
        "capture_age_hours",
        "market_move_probability",
        "max_latency_ms",
        "latency_status",
        "reason_codes",
        "manual_next_step",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    for name in required_names:
        if name not in payload:
            raise ValueError(f"public payload missing {name}")
    _require_status("latency_status", payload["latency_status"])
    _require_reason_code_list("reason_codes", payload["reason_codes"])
    _require_manual_step("manual_next_step", payload["manual_next_step"])


def _reject_payload_numeric_objects(value: Any) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_payload_numeric_objects(item)
        return
    if type(value) is list:
        for item in value:
            _reject_payload_numeric_objects(item)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if payload.get(name) is not True:
            raise ValueError(f"payload {name} must be True")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of {STATUSES}")


def _require_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must be nonempty")
    for value in values:
        if type(value) is not str or value not in REASON_CODES:
            raise ValueError(f"{name} contains an unknown reason code")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicates")
    return values


def _require_reason_code_list(name: str, values: object) -> None:
    if type(values) is not list:
        raise ValueError(f"{name} must be a list")
    _require_reason_codes(name, tuple(values))


def _require_manual_step(name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_STEPS:
        raise ValueError(f"{name} must be supported")


def _require_sha256(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 digest string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a sha256 digest string") from exc


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{name} {flag_name} must be True")


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX)
