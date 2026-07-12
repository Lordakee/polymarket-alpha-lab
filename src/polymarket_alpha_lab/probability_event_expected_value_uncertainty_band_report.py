"""Pure read-only probability expected value uncertainty band report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Mapping


__all__ = (
    "ProbabilityEventExpectedValueUncertaintyBandInput",
    "ProbabilityEventExpectedValueUncertaintyBandPublicPayload",
    "ProbabilityEventExpectedValueUncertaintyBandReport",
    "build_probability_event_expected_value_uncertainty_band_report",
    "probability_event_expected_value_uncertainty_band_report_digest",
    "probability_event_expected_value_uncertainty_band_report_payload",
)


CONFIG_VERSION = "probability-event-expected-value-uncertainty-band-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
PASS_LOW_EDGE = Decimal("0.050000")
RATIO_QUANTUM = Decimal("0.000001")
PROBABILITY_FIELDS = (
    "forecast_probability",
    "market_probability",
    "probability_uncertainty",
    "fee_probability",
    "slippage_probability",
)
NEXT_STEP_BY_STATUS = {
    "pass": (
        "Record the public probability band in the local Supabase/Postgres "
        "paper evidence design notes; keep Phase 1 read-only."
    ),
    "watch": (
        "Manually review whether the public probability edge survives fees, "
        "slippage, and uncertainty before any later-stage decision."
    ),
    "block": (
        "Block this event from Phase 1 expected-value consideration and "
        "capture only the read-only report rationale."
    ),
}


class ProbabilityEventExpectedValueUncertaintyBandPublicPayload(dict[str, object]):
    """Immutable public payload for the read-only report."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("public_payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


@dataclass(frozen=True)
class ProbabilityEventExpectedValueUncertaintyBandInput:
    forecast_probability: Decimal
    market_probability: Decimal
    probability_uncertainty: Decimal
    fee_probability: Decimal
    slippage_probability: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventExpectedValueUncertaintyBandInput:
            raise TypeError(
                "ProbabilityEventExpectedValueUncertaintyBandInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventExpectedValueUncertaintyBandInput:
            raise ValueError(
                "input must be exactly ProbabilityEventExpectedValueUncertaintyBandInput",
            )
        for field_name in PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ProbabilityEventExpectedValueUncertaintyBandReport:
    config_version: str
    forecast_probability: Decimal
    market_probability: Decimal
    probability_uncertainty: Decimal
    fee_probability: Decimal
    slippage_probability: Decimal
    expected_value_low: Decimal
    expected_value_high: Decimal
    ev_band_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ProbabilityEventExpectedValueUncertaintyBandReport:
            raise TypeError(
                "ProbabilityEventExpectedValueUncertaintyBandReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ProbabilityEventExpectedValueUncertaintyBandReport:
            raise ValueError(
                "report must be exactly "
                "ProbabilityEventExpectedValueUncertaintyBandReport",
            )
        _require_config_version(self.config_version)
        for field_name in PROBABILITY_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("expected_value_low", "expected_value_high"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)).quantize(
                    RATIO_QUANTUM,
                ),
            )
        _require_status("ev_band_status", self.ev_band_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_manual_next_step(self.ev_band_status, self.manual_next_step)
        _require_sha256_hex("payload_digest", self.payload_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.payload_digest != _payload_digest(_payload_items(self, payload_digest="")):
            raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> ProbabilityEventExpectedValueUncertaintyBandPublicPayload:
        payload = ProbabilityEventExpectedValueUncertaintyBandPublicPayload(
            _payload_items(self, payload_digest=self.payload_digest),
        )
        _validate_public_payload(payload)
        return payload


def build_probability_event_expected_value_uncertainty_band_report(
    inputs: ProbabilityEventExpectedValueUncertaintyBandInput,
) -> ProbabilityEventExpectedValueUncertaintyBandReport:
    """Build a deterministic Phase 1 probability edge band report."""

    if type(inputs) is not ProbabilityEventExpectedValueUncertaintyBandInput:
        raise ValueError(
            "inputs must be a ProbabilityEventExpectedValueUncertaintyBandInput",
        )
    _require_hard_flags("input", inputs)
    expected_value_low = _expected_value_low(inputs)
    expected_value_high = _expected_value_high(inputs)
    status = _ev_band_status(expected_value_low)
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "forecast_probability": inputs.forecast_probability,
        "market_probability": inputs.market_probability,
        "probability_uncertainty": inputs.probability_uncertainty,
        "fee_probability": inputs.fee_probability,
        "slippage_probability": inputs.slippage_probability,
        "expected_value_low": expected_value_low,
        "expected_value_high": expected_value_high,
        "ev_band_status": status,
        "reason_codes": _reason_codes(status, inputs.reason_codes),
        "manual_next_step": NEXT_STEP_BY_STATUS[status],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ProbabilityEventExpectedValueUncertaintyBandReport(
        **values,
        payload_digest=_payload_digest(_payload_values(values, payload_digest="")),
    )


def probability_event_expected_value_uncertainty_band_report_payload(
    report: (
        ProbabilityEventExpectedValueUncertaintyBandReport
        | Mapping[str, object]
    ),
) -> ProbabilityEventExpectedValueUncertaintyBandPublicPayload:
    if type(report) is ProbabilityEventExpectedValueUncertaintyBandReport:
        _require_hard_flags("report", report)
        return report.public_payload
    if isinstance(report, Mapping):
        payload = ProbabilityEventExpectedValueUncertaintyBandPublicPayload(report)
        _validate_public_payload(payload)
        return payload
    raise ValueError(
        "report must be a ProbabilityEventExpectedValueUncertaintyBandReport "
        "or public payload",
    )


def probability_event_expected_value_uncertainty_band_report_digest(
    report: (
        ProbabilityEventExpectedValueUncertaintyBandReport
        | Mapping[str, object]
    ),
) -> str:
    payload = probability_event_expected_value_uncertainty_band_report_payload(report)
    return _payload_digest(dict(payload, payload_digest=""))


def _expected_value_low(
    inputs: ProbabilityEventExpectedValueUncertaintyBandInput,
) -> Decimal:
    return _quantize(
        inputs.forecast_probability
        - inputs.probability_uncertainty
        - inputs.market_probability
        - inputs.fee_probability
        - inputs.slippage_probability,
    )


def _expected_value_high(
    inputs: ProbabilityEventExpectedValueUncertaintyBandInput,
) -> Decimal:
    return _quantize(
        inputs.forecast_probability
        + inputs.probability_uncertainty
        - inputs.market_probability
        - inputs.fee_probability
        - inputs.slippage_probability,
    )


def _ev_band_status(expected_value_low: Decimal) -> str:
    if expected_value_low <= ZERO:
        return "block"
    if expected_value_low < PASS_LOW_EDGE:
        return "watch"
    return "pass"


def _reason_codes(
    status: str,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = {
        f"expected_value_uncertainty_band_{status}",
        f"manual_review_expected_value_band_{status}",
    }
    if status == "block":
        reason_codes.add("expected_value_low_not_positive")
    else:
        reason_codes.add("positive_expected_value_low")
    if status == "watch":
        reason_codes.add("expected_value_low_below_pass_threshold")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _validate_report(report: ProbabilityEventExpectedValueUncertaintyBandReport) -> None:
    expected_low = _quantize(
        report.forecast_probability
        - report.probability_uncertainty
        - report.market_probability
        - report.fee_probability
        - report.slippage_probability,
    )
    if report.expected_value_low != expected_low:
        raise ValueError("expected_value_low must match probability inputs")
    expected_high = _quantize(
        report.forecast_probability
        + report.probability_uncertainty
        - report.market_probability
        - report.fee_probability
        - report.slippage_probability,
    )
    if report.expected_value_high != expected_high:
        raise ValueError("expected_value_high must match probability inputs")
    expected_status = _ev_band_status(report.expected_value_low)
    if report.ev_band_status != expected_status:
        raise ValueError("ev_band_status must match expected_value_low")
    expected_reason_codes = _reason_codes(report.ev_band_status, _input_codes(report))
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match expected value status")


def _input_codes(
    report: ProbabilityEventExpectedValueUncertaintyBandReport,
) -> tuple[str, ...]:
    input_prefix = "input_"
    return tuple(
        reason_code.removeprefix(input_prefix)
        for reason_code in report.reason_codes
        if reason_code.startswith(input_prefix)
    )


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"public_payload.{field_name} must be True")
    digest = payload.get("payload_digest")
    _require_sha256_hex("payload_digest", digest)
    values = dict(payload, payload_digest="")
    if digest != _payload_digest(values):
        raise ValueError("public_payload.payload_digest must match payload values")
    for path, value in _iter_payload_values(payload):
        if type(value) in (int, float, Decimal):
            raise ValueError(f"public numeric values must be Decimal strings: {path}")
        if value is not None and type(value) not in (dict, list, str, bool):
            raise ValueError(f"public payload values must be JSON-safe: {path}")


def _iter_payload_values(
    value: object,
    path: str = "payload",
) -> tuple[tuple[str, object], ...]:
    values: list[tuple[str, object]] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            item_path = f"{path}.{key}"
            values.append((item_path, item))
            values.extend(_iter_payload_values(item, item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"
            values.append((item_path, item))
            values.extend(_iter_payload_values(item, item_path))
    return tuple(values)


def _payload_items(
    report: ProbabilityEventExpectedValueUncertaintyBandReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return _payload_values(
        {
            field.name: getattr(report, field.name)
            for field in fields(report)
            if field.name != "payload_digest"
        },
        payload_digest=payload_digest,
    )


def _payload_values(
    values: Mapping[str, object],
    *,
    payload_digest: str,
) -> dict[str, object]:
    payload = {str(key): _payload_value(value) for key, value in values.items()}
    payload["payload_digest"] = payload_digest
    return payload


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _payload_value(payload),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or not value or value.strip() != value:
            raise ValueError(f"{field_name} must contain canonical reason codes")
        if value.lower() != value or " " in value:
            raise ValueError(f"{field_name} must contain canonical reason codes")
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_manual_next_step(status: str, value: object) -> None:
    if type(value) is not str or value != NEXT_STEP_BY_STATUS[status]:
        raise ValueError("manual_next_step must match ev_band_status")


def _require_config_version(value: object) -> None:
    if type(value) is not str or value != CONFIG_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_sha256_hex(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
