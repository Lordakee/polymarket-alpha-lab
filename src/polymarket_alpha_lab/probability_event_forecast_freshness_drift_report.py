"""Pure paper-only probability event forecast freshness drift report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")

_FORECAST_AGE_WATCH_HOURS = Decimal("4.000000")
_FORECAST_AGE_EXPIRE_HOURS = Decimal("12.000000")
_MARKET_MOVE_WATCH_PROBABILITY = Decimal("0.050000")
_MARKET_MOVE_HIGH_PROBABILITY = Decimal("0.150000")
_SOURCE_REFRESH_WATCH_HOURS = Decimal("2.000000")
_SOURCE_REFRESH_EXPIRE_HOURS = Decimal("8.000000")
_EVENT_CLOSE_WATCH_HOURS = Decimal("6.000000")
_EVENT_CLOSE_IMMINENT_HOURS = Decimal("2.000000")
_MODEL_CONFIDENCE_DRIFT_WATCH = Decimal("0.100000")
_MODEL_CONFIDENCE_DRIFT_HIGH = Decimal("0.200000")

_FRESHNESS_STATUSES = frozenset(("fresh", "stale", "expired"))
_DRIFT_LEVELS = frozenset(("low", "medium", "high"))
_MANUAL_NEXT_STEPS = frozenset(
    (
        "continue_monitoring",
        "manual_review_forecast_before_reuse",
        "refresh_inputs_and_rebuild_forecast_before_reuse",
    ),
)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REASON_CODE_SEQUENCE = (
    "forecast_age_expired",
    "market_price_move_high",
    "source_refresh_expired",
    "event_close_imminent",
    "model_confidence_drift_high",
    "forecast_age_watch_stale",
    "market_price_move_watch",
    "source_refresh_watch_stale",
    "event_close_watch_window",
    "model_confidence_drift_watch",
    "forecast_fresh",
)
_HIGH_REASON_CODES = frozenset(
    (
        "forecast_age_expired",
        "market_price_move_high",
        "source_refresh_expired",
        "event_close_imminent",
        "model_confidence_drift_high",
    ),
)


@dataclass(frozen=True)
class ProbabilityEventForecastFreshnessDriftReport:
    forecast_age_hours: Decimal
    market_price_move_probability: Decimal
    source_refresh_age_hours: Decimal
    event_time_to_close_hours: Decimal
    model_confidence_drift: Decimal
    freshness_status: str
    drift_level: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "forecast_age_hours",
            "source_refresh_age_hours",
            "event_time_to_close_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "market_price_move_probability",
            "model_confidence_drift",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_freshness_status("freshness_status", self.freshness_status)
        _require_drift_level("drift_level", self.drift_level)
        _require_manual_next_step("manual_next_step", self.manual_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        payload = _payload_without_digest(self)
        payload["digest"] = self.digest
        return payload

    @property
    def digest(self) -> str:
        canonical = json.dumps(
            _payload_without_digest(self),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_probability_event_forecast_freshness_drift_report(
    *,
    forecast_age_hours: Decimal,
    market_price_move_probability: Decimal,
    source_refresh_age_hours: Decimal,
    event_time_to_close_hours: Decimal,
    model_confidence_drift: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventForecastFreshnessDriftReport:
    forecast_age = _require_nonnegative_decimal(
        "forecast_age_hours",
        forecast_age_hours,
    )
    market_move = _require_ratio_decimal(
        "market_price_move_probability",
        market_price_move_probability,
    )
    source_age = _require_nonnegative_decimal(
        "source_refresh_age_hours",
        source_refresh_age_hours,
    )
    time_to_close = _require_nonnegative_decimal(
        "event_time_to_close_hours",
        event_time_to_close_hours,
    )
    confidence_drift = _require_ratio_decimal(
        "model_confidence_drift",
        model_confidence_drift,
    )
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)

    reasons = _reason_codes(
        forecast_age_hours=forecast_age,
        market_price_move_probability=market_move,
        source_refresh_age_hours=source_age,
        event_time_to_close_hours=time_to_close,
        model_confidence_drift=confidence_drift,
    )
    freshness_status = _freshness_status(reasons)
    drift_level = _drift_level(reasons)
    return ProbabilityEventForecastFreshnessDriftReport(
        forecast_age_hours=forecast_age,
        market_price_move_probability=market_move,
        source_refresh_age_hours=source_age,
        event_time_to_close_hours=time_to_close,
        model_confidence_drift=confidence_drift,
        freshness_status=freshness_status,
        drift_level=drift_level,
        reason_codes=reasons,
        manual_next_step=_manual_next_step(freshness_status),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_forecast_freshness_drift_report_payload(
    report: ProbabilityEventForecastFreshnessDriftReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventForecastFreshnessDriftReport:
        raise ValueError(
            "report must be a ProbabilityEventForecastFreshnessDriftReport",
        )
    return report.public_payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _reason_codes(
    *,
    forecast_age_hours: Decimal,
    market_price_move_probability: Decimal,
    source_refresh_age_hours: Decimal,
    event_time_to_close_hours: Decimal,
    model_confidence_drift: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if forecast_age_hours >= _FORECAST_AGE_EXPIRE_HOURS:
        reason_codes.append("forecast_age_expired")
    elif forecast_age_hours >= _FORECAST_AGE_WATCH_HOURS:
        reason_codes.append("forecast_age_watch_stale")

    if market_price_move_probability >= _MARKET_MOVE_HIGH_PROBABILITY:
        reason_codes.append("market_price_move_high")
    elif market_price_move_probability >= _MARKET_MOVE_WATCH_PROBABILITY:
        reason_codes.append("market_price_move_watch")

    if source_refresh_age_hours >= _SOURCE_REFRESH_EXPIRE_HOURS:
        reason_codes.append("source_refresh_expired")
    elif source_refresh_age_hours >= _SOURCE_REFRESH_WATCH_HOURS:
        reason_codes.append("source_refresh_watch_stale")

    if event_time_to_close_hours <= _EVENT_CLOSE_IMMINENT_HOURS:
        reason_codes.append("event_close_imminent")
    elif event_time_to_close_hours <= _EVENT_CLOSE_WATCH_HOURS:
        reason_codes.append("event_close_watch_window")

    if model_confidence_drift >= _MODEL_CONFIDENCE_DRIFT_HIGH:
        reason_codes.append("model_confidence_drift_high")
    elif model_confidence_drift >= _MODEL_CONFIDENCE_DRIFT_WATCH:
        reason_codes.append("model_confidence_drift_watch")

    if not reason_codes:
        reason_codes.append("forecast_fresh")
    return _normalize_reason_codes(reason_codes)


def _freshness_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _HIGH_REASON_CODES for reason_code in reason_codes):
        return "expired"
    if reason_codes != ("forecast_fresh",):
        return "stale"
    return "fresh"


def _drift_level(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _HIGH_REASON_CODES for reason_code in reason_codes):
        return "high"
    if reason_codes != ("forecast_fresh",):
        return "medium"
    return "low"


def _manual_next_step(freshness_status: str) -> str:
    if freshness_status == "expired":
        return "refresh_inputs_and_rebuild_forecast_before_reuse"
    if freshness_status == "stale":
        return "manual_review_forecast_before_reuse"
    return "continue_monitoring"


def _validate_report_consistency(
    report: ProbabilityEventForecastFreshnessDriftReport,
) -> None:
    expected_reasons = _reason_codes(
        forecast_age_hours=report.forecast_age_hours,
        market_price_move_probability=report.market_price_move_probability,
        source_refresh_age_hours=report.source_refresh_age_hours,
        event_time_to_close_hours=report.event_time_to_close_hours,
        model_confidence_drift=report.model_confidence_drift,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report inputs")
    expected_status = _freshness_status(expected_reasons)
    if report.freshness_status != expected_status:
        raise ValueError("freshness_status must match report inputs")
    if report.drift_level != _drift_level(expected_reasons):
        raise ValueError("drift_level must match report inputs")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match freshness_status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_freshness_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _FRESHNESS_STATUSES:
        raise ValueError(f"{field_name} must be fresh, stale, or expired")


def _require_drift_level(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _DRIFT_LEVELS:
        raise ValueError(f"{field_name} must be low, medium, or high")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be supported")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _payload_without_digest(
    report: ProbabilityEventForecastFreshnessDriftReport,
) -> dict[str, Any]:
    _normalize_reason_codes(report.reason_codes)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    return payload


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


__all__ = (
    "ProbabilityEventForecastFreshnessDriftReport",
    "build_probability_event_forecast_freshness_drift_report",
    "probability_event_forecast_freshness_drift_report_payload",
)
