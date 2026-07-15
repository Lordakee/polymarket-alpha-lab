"""Pure paper-only probability event news catalyst timing risk report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from typing import Any, Mapping, Sequence


_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")

_NEXT_CATALYST_WATCH_HOURS = Decimal("12.000000")
_NEXT_CATALYST_IMMINENT_HOURS = Decimal("2.000000")
_FORECAST_AGE_WATCH_HOURS = Decimal("4.000000")
_FORECAST_AGE_EXPIRE_HOURS = Decimal("12.000000")
_SOURCE_REFRESH_WATCH_HOURS = Decimal("2.000000")
_SOURCE_REFRESH_EXPIRE_HOURS = Decimal("8.000000")
_MARKET_CLOSE_WATCH_HOURS = Decimal("24.000000")
_MARKET_CLOSE_IMMINENT_HOURS = Decimal("2.000000")

_CATALYST_TIMING_STATUSES = frozenset(("supported", "watch", "block"))
_MANUAL_NEXT_STEPS = frozenset(
    (
        "continue_monitoring_public_catalysts",
        "manual_review_catalyst_timing_before_reuse",
        "refresh_public_news_catalysts_before_probability_use",
    ),
)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REASON_CODE_SEQUENCE = (
    "no_public_catalyst",
    "next_catalyst_imminent",
    "forecast_age_expired",
    "source_refresh_expired",
    "market_close_imminent",
    "next_catalyst_watch_window",
    "forecast_age_watch_stale",
    "source_refresh_watch_stale",
    "market_close_watch_window",
    "catalyst_timing_supported",
)
_BLOCK_REASON_CODES = frozenset(
    (
        "no_public_catalyst",
        "next_catalyst_imminent",
        "forecast_age_expired",
        "source_refresh_expired",
        "market_close_imminent",
    ),
)


@dataclass(frozen=True)
class ProbabilityEventNewsCatalystTimingRiskReport:
    catalyst_count: Decimal
    next_catalyst_hours: Decimal
    forecast_age_hours: Decimal
    source_refresh_age_hours: Decimal
    market_close_hours: Decimal
    catalyst_timing_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "catalyst_count",
            "next_catalyst_hours",
            "forecast_age_hours",
            "source_refresh_age_hours",
            "market_close_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_catalyst_timing_status(
            "catalyst_timing_status",
            self.catalyst_timing_status,
        )
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
        payload["payload_digest"] = self.payload_digest
        return payload

    @property
    def payload_digest(self) -> str:
        canonical = json.dumps(
            _payload_without_digest(self),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_probability_event_news_catalyst_timing_risk_report(
    *,
    catalyst_count: Decimal,
    next_catalyst_hours: Decimal,
    forecast_age_hours: Decimal,
    source_refresh_age_hours: Decimal,
    market_close_hours: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventNewsCatalystTimingRiskReport:
    normalized_catalyst_count = _require_nonnegative_decimal(
        "catalyst_count",
        catalyst_count,
    )
    normalized_next_catalyst_hours = _require_nonnegative_decimal(
        "next_catalyst_hours",
        next_catalyst_hours,
    )
    normalized_forecast_age_hours = _require_nonnegative_decimal(
        "forecast_age_hours",
        forecast_age_hours,
    )
    normalized_source_refresh_age_hours = _require_nonnegative_decimal(
        "source_refresh_age_hours",
        source_refresh_age_hours,
    )
    normalized_market_close_hours = _require_nonnegative_decimal(
        "market_close_hours",
        market_close_hours,
    )
    flags = _PhaseFlags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    _require_hard_flags("builder", flags)

    reasons = _reason_codes(
        catalyst_count=normalized_catalyst_count,
        next_catalyst_hours=normalized_next_catalyst_hours,
        forecast_age_hours=normalized_forecast_age_hours,
        source_refresh_age_hours=normalized_source_refresh_age_hours,
        market_close_hours=normalized_market_close_hours,
    )
    status = _catalyst_timing_status(reasons)
    return ProbabilityEventNewsCatalystTimingRiskReport(
        catalyst_count=normalized_catalyst_count,
        next_catalyst_hours=normalized_next_catalyst_hours,
        forecast_age_hours=normalized_forecast_age_hours,
        source_refresh_age_hours=normalized_source_refresh_age_hours,
        market_close_hours=normalized_market_close_hours,
        catalyst_timing_status=status,
        reason_codes=reasons,
        manual_next_step=_manual_next_step(status),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def probability_event_news_catalyst_timing_risk_report_payload(
    report: ProbabilityEventNewsCatalystTimingRiskReport,
) -> dict[str, Any]:
    if type(report) is not ProbabilityEventNewsCatalystTimingRiskReport:
        raise ValueError(
            "report must be a ProbabilityEventNewsCatalystTimingRiskReport",
        )
    return report.public_payload


@dataclass(frozen=True)
class _PhaseFlags:
    paper_only: bool
    report_only: bool
    readonly: bool


def _reason_codes(
    *,
    catalyst_count: Decimal,
    next_catalyst_hours: Decimal,
    forecast_age_hours: Decimal,
    source_refresh_age_hours: Decimal,
    market_close_hours: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if catalyst_count == _ZERO:
        reason_codes.append("no_public_catalyst")

    if next_catalyst_hours <= _NEXT_CATALYST_IMMINENT_HOURS:
        reason_codes.append("next_catalyst_imminent")
    elif next_catalyst_hours <= _NEXT_CATALYST_WATCH_HOURS:
        reason_codes.append("next_catalyst_watch_window")

    if forecast_age_hours >= _FORECAST_AGE_EXPIRE_HOURS:
        reason_codes.append("forecast_age_expired")
    elif forecast_age_hours >= _FORECAST_AGE_WATCH_HOURS:
        reason_codes.append("forecast_age_watch_stale")

    if source_refresh_age_hours >= _SOURCE_REFRESH_EXPIRE_HOURS:
        reason_codes.append("source_refresh_expired")
    elif source_refresh_age_hours >= _SOURCE_REFRESH_WATCH_HOURS:
        reason_codes.append("source_refresh_watch_stale")

    if market_close_hours <= _MARKET_CLOSE_IMMINENT_HOURS:
        reason_codes.append("market_close_imminent")
    elif market_close_hours <= _MARKET_CLOSE_WATCH_HOURS:
        reason_codes.append("market_close_watch_window")

    if not reason_codes:
        reason_codes.append("catalyst_timing_supported")
    return _normalize_reason_codes(reason_codes)


def _catalyst_timing_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes != ("catalyst_timing_supported",):
        return "watch"
    return "supported"


def _manual_next_step(catalyst_timing_status: str) -> str:
    if catalyst_timing_status == "block":
        return "refresh_public_news_catalysts_before_probability_use"
    if catalyst_timing_status == "watch":
        return "manual_review_catalyst_timing_before_reuse"
    return "continue_monitoring_public_catalysts"


def _validate_report_consistency(
    report: ProbabilityEventNewsCatalystTimingRiskReport,
) -> None:
    expected_reasons = _reason_codes(
        catalyst_count=report.catalyst_count,
        next_catalyst_hours=report.next_catalyst_hours,
        forecast_age_hours=report.forecast_age_hours,
        source_refresh_age_hours=report.source_refresh_age_hours,
        market_close_hours=report.market_close_hours,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match report inputs")
    expected_status = _catalyst_timing_status(expected_reasons)
    if report.catalyst_timing_status != expected_status:
        raise ValueError("catalyst_timing_status must match report inputs")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match catalyst_timing_status")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_catalyst_timing_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _CATALYST_TIMING_STATUSES:
        raise ValueError(f"{field_name} must be supported, watch, or block")


def _require_manual_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MANUAL_NEXT_STEPS:
        raise ValueError(f"{field_name} must be allowed")


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


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be allowed")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _payload_without_digest(
    report: ProbabilityEventNewsCatalystTimingRiskReport,
) -> dict[str, Any]:
    _normalize_reason_codes(report.reason_codes)
    _validate_report_consistency(report)
    _require_hard_flags("report", report)
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
    "ProbabilityEventNewsCatalystTimingRiskReport",
    "build_probability_event_news_catalyst_timing_risk_report",
    "probability_event_news_catalyst_timing_risk_report_payload",
)
