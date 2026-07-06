"""Paper report reducer for probability signal freshness decay curves."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_SIGNAL_FRESHNESS_DECAY_CURVE_V10_CONFIG_VERSION = (
    "strategy-signal-freshness-decay-curve-v10"
)

DECIMAL_PRECISION = 64
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
FOUR = Decimal("4.000000")
HALF = Decimal("0.500000")
FRESH_WEIGHT_THRESHOLD = Decimal("0.750000")
STALE_WEIGHT_THRESHOLD = Decimal("0.250000")
EXPIRED_WEIGHT_THRESHOLD = Decimal("0.100000")
HIGH_SIGNAL_THRESHOLD = Decimal("0.750000")
MEDIUM_SIGNAL_THRESHOLD = Decimal("0.500000")

DECAY_STATUSES = ("fresh", "decaying", "stale", "expired")
REASON_CODES = (
    "source_reliability_high",
    "source_reliability_medium",
    "source_reliability_low",
    "time_sensitivity_high",
    "time_sensitivity_normal",
    "resolution_urgency_high",
    "resolution_urgency_normal",
    "confirmed_update_recent",
    "confirmed_update_stale",
    "signal_fresh",
    "signal_decaying",
    "signal_stale",
    "decay_status_fresh",
    "decay_status_decaying",
    "decay_status_stale",
    "decay_status_expired",
    "refresh_required",
    "refresh_not_required",
)
PAYLOAD_FIELDS = (
    "config_version",
    "signal_age_minutes",
    "half_life_minutes",
    "source_reliability",
    "market_time_sensitivity",
    "resolution_urgency",
    "last_confirmed_update_minutes",
    "freshness_weight",
    "decay_status",
    "refresh_required",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class SignalFreshnessDecayCurveV10Input:
    signal_age_minutes: Decimal
    half_life_minutes: Decimal
    source_reliability: Decimal
    market_time_sensitivity: Decimal
    resolution_urgency: Decimal
    last_confirmed_update_minutes: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "signal_age_minutes",
            _normalize_nonnegative_decimal(
                "signal_age_minutes",
                self.signal_age_minutes,
            ),
        )
        object.__setattr__(
            self,
            "half_life_minutes",
            _normalize_positive_decimal("half_life_minutes", self.half_life_minutes),
        )
        object.__setattr__(
            self,
            "source_reliability",
            _normalize_unit_decimal("source_reliability", self.source_reliability),
        )
        object.__setattr__(
            self,
            "market_time_sensitivity",
            _normalize_unit_decimal(
                "market_time_sensitivity",
                self.market_time_sensitivity,
            ),
        )
        object.__setattr__(
            self,
            "resolution_urgency",
            _normalize_unit_decimal("resolution_urgency", self.resolution_urgency),
        )
        object.__setattr__(
            self,
            "last_confirmed_update_minutes",
            _normalize_nonnegative_decimal(
                "last_confirmed_update_minutes",
                self.last_confirmed_update_minutes,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class SignalFreshnessDecayCurveV10Result:
    signal_age_minutes: Decimal
    half_life_minutes: Decimal
    source_reliability: Decimal
    market_time_sensitivity: Decimal
    resolution_urgency: Decimal
    last_confirmed_update_minutes: Decimal
    freshness_weight: Decimal
    decay_status: str
    refresh_required: bool
    reason_codes: tuple[str, ...]
    config_version: str = DEFAULT_STRATEGY_SIGNAL_FRESHNESS_DECAY_CURVE_V10_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_config_version(self.config_version)
        object.__setattr__(
            self,
            "signal_age_minutes",
            _normalize_nonnegative_decimal(
                "signal_age_minutes",
                self.signal_age_minutes,
            ),
        )
        object.__setattr__(
            self,
            "half_life_minutes",
            _normalize_positive_decimal("half_life_minutes", self.half_life_minutes),
        )
        object.__setattr__(
            self,
            "source_reliability",
            _normalize_unit_decimal("source_reliability", self.source_reliability),
        )
        object.__setattr__(
            self,
            "market_time_sensitivity",
            _normalize_unit_decimal(
                "market_time_sensitivity",
                self.market_time_sensitivity,
            ),
        )
        object.__setattr__(
            self,
            "resolution_urgency",
            _normalize_unit_decimal("resolution_urgency", self.resolution_urgency),
        )
        object.__setattr__(
            self,
            "last_confirmed_update_minutes",
            _normalize_nonnegative_decimal(
                "last_confirmed_update_minutes",
                self.last_confirmed_update_minutes,
            ),
        )
        object.__setattr__(
            self,
            "freshness_weight",
            _normalize_unit_decimal("freshness_weight", self.freshness_weight),
        )
        _require_member("decay_status", self.decay_status, DECAY_STATUSES)
        _require_bool("refresh_required", self.refresh_required)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("result", self)
        _validate_result(self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_signal_freshness_decay_curve_v10_payload(self)


def strategy_signal_freshness_decay_curve_v10(
    signal: SignalFreshnessDecayCurveV10Input,
) -> SignalFreshnessDecayCurveV10Result:
    if type(signal) is not SignalFreshnessDecayCurveV10Input:
        raise ValueError("signal must be a SignalFreshnessDecayCurveV10Input")
    _require_hard_flags("input", signal)
    freshness_weight = _freshness_weight(signal)
    decay_status = _decay_status(freshness_weight)
    refresh_required = _refresh_required(signal, decay_status)
    return SignalFreshnessDecayCurveV10Result(
        signal_age_minutes=signal.signal_age_minutes,
        half_life_minutes=signal.half_life_minutes,
        source_reliability=signal.source_reliability,
        market_time_sensitivity=signal.market_time_sensitivity,
        resolution_urgency=signal.resolution_urgency,
        last_confirmed_update_minutes=signal.last_confirmed_update_minutes,
        freshness_weight=freshness_weight,
        decay_status=decay_status,
        refresh_required=refresh_required,
        reason_codes=_reason_codes(signal, decay_status, refresh_required),
    )


def strategy_signal_freshness_decay_curve_v10_payload(
    report: SignalFreshnessDecayCurveV10Result | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SignalFreshnessDecayCurveV10Result:
        _require_hard_flags("result", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsupported_payload_fields(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a SignalFreshnessDecayCurveV10Result")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsupported_payload_fields(payload)
    _require_hard_flags("payload", _DictFlags(payload))
    return payload


@dataclass(frozen=True)
class _DictFlags:
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


def _freshness_weight(signal: SignalFreshnessDecayCurveV10Input) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PRECISION
        age_ratio = signal.signal_age_minutes / signal.half_life_minutes
        decay_curve = ctx.power(HALF, age_ratio)
        pressure_discount = ONE - (
            (signal.market_time_sensitivity + signal.resolution_urgency) / FOUR
        )
        raw_weight = signal.source_reliability * decay_curve * pressure_discount
    return _clamp_unit(_quantize(raw_weight))


def _decay_status(freshness_weight: Decimal) -> str:
    if freshness_weight >= FRESH_WEIGHT_THRESHOLD:
        return "fresh"
    if freshness_weight >= STALE_WEIGHT_THRESHOLD:
        return "decaying"
    if freshness_weight >= EXPIRED_WEIGHT_THRESHOLD:
        return "stale"
    return "expired"


def _refresh_required(
    signal: SignalFreshnessDecayCurveV10Input,
    decay_status: str,
) -> bool:
    if decay_status in ("stale", "expired"):
        return True
    pressure_high = (
        signal.market_time_sensitivity >= HIGH_SIGNAL_THRESHOLD
        or signal.resolution_urgency >= HIGH_SIGNAL_THRESHOLD
    )
    return _confirmed_update_is_stale(signal) and pressure_high


def _reason_codes(
    signal: SignalFreshnessDecayCurveV10Input,
    decay_status: str,
    refresh_required: bool,
) -> tuple[str, ...]:
    codes = [
        _source_reliability_code(signal.source_reliability),
        _time_sensitivity_code(signal.market_time_sensitivity),
        _resolution_urgency_code(signal.resolution_urgency),
        _confirmed_update_code(signal),
        _signal_age_code(signal),
        f"decay_status_{decay_status}",
        "refresh_required" if refresh_required else "refresh_not_required",
    ]
    return tuple(codes)


def _source_reliability_code(value: Decimal) -> str:
    if value >= HIGH_SIGNAL_THRESHOLD:
        return "source_reliability_high"
    if value >= MEDIUM_SIGNAL_THRESHOLD:
        return "source_reliability_medium"
    return "source_reliability_low"


def _time_sensitivity_code(value: Decimal) -> str:
    if value >= HIGH_SIGNAL_THRESHOLD:
        return "time_sensitivity_high"
    return "time_sensitivity_normal"


def _resolution_urgency_code(value: Decimal) -> str:
    if value >= HIGH_SIGNAL_THRESHOLD:
        return "resolution_urgency_high"
    return "resolution_urgency_normal"


def _confirmed_update_code(signal: SignalFreshnessDecayCurveV10Input) -> str:
    if _confirmed_update_is_stale(signal):
        return "confirmed_update_stale"
    return "confirmed_update_recent"


def _confirmed_update_is_stale(signal: SignalFreshnessDecayCurveV10Input) -> bool:
    return signal.last_confirmed_update_minutes >= signal.half_life_minutes


def _signal_age_code(signal: SignalFreshnessDecayCurveV10Input) -> str:
    if signal.signal_age_minutes == ZERO:
        return "signal_fresh"
    if signal.signal_age_minutes > signal.half_life_minutes * TWO:
        return "signal_stale"
    return "signal_decaying"


def _validate_result(result: SignalFreshnessDecayCurveV10Result) -> None:
    signal = SignalFreshnessDecayCurveV10Input(
        signal_age_minutes=result.signal_age_minutes,
        half_life_minutes=result.half_life_minutes,
        source_reliability=result.source_reliability,
        market_time_sensitivity=result.market_time_sensitivity,
        resolution_urgency=result.resolution_urgency,
        last_confirmed_update_minutes=result.last_confirmed_update_minutes,
    )
    if result.freshness_weight != _freshness_weight(signal):
        raise ValueError("freshness_weight must match decay curve")
    if result.decay_status != _decay_status(result.freshness_weight):
        raise ValueError("decay_status must match freshness_weight")
    if result.refresh_required != _refresh_required(signal, result.decay_status):
        raise ValueError("refresh_required must match decay status")
    expected_reason_codes = _reason_codes(
        signal,
        result.decay_status,
        result.refresh_required,
    )
    if result.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match decay inputs")


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsupported_payload_fields(value: dict[str, object]) -> None:
    for key in value:
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        if key not in PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for code in codes:
        _require_member(field_name, code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return codes


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_STRATEGY_SIGNAL_FRESHNESS_DECAY_CURVE_V10_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        return value.quantize(RATIO_QUANTUM)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


__all__ = (
    "DEFAULT_STRATEGY_SIGNAL_FRESHNESS_DECAY_CURVE_V10_CONFIG_VERSION",
    "SignalFreshnessDecayCurveV10Input",
    "SignalFreshnessDecayCurveV10Result",
    "strategy_signal_freshness_decay_curve_v10",
    "strategy_signal_freshness_decay_curve_v10_payload",
)
