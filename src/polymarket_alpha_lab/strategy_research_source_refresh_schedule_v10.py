"""Pure paper-only research source refresh schedule strategy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any


CONFIG_VERSION = "strategy-research-source-refresh-schedule-v10"
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
LOW_RELIABILITY_FLOOR = Decimal("0.600000")
HIGH_RELIABILITY_FLOOR = Decimal("0.800000")
MEDIUM_SENSITIVITY_FLOOR = Decimal("0.600000")
HIGH_SENSITIVITY_FLOOR = Decimal("0.800000")
HEALTHY_CAPACITY_FLOOR = Decimal("0.800000")
USABLE_CAPACITY_FLOOR = Decimal("0.500000")
CRITICAL_RESOLUTION_MINUTES = Decimal("60.000000")
COMPRESSED_RESOLUTION_MINUTES = Decimal("360.000000")
IMMEDIATE_CADENCE_MINUTES = Decimal("15.000000")
ACTIVE_CADENCE_MINUTES = Decimal("30.000000")
LOW_PRESSURE_CADENCE_MINUTES = Decimal("240.000000")

FRESHNESS_STATUSES = ("fresh", "aging", "stale")
REFRESH_SCHEDULE_STATUSES = (
    "refresh_now",
    "scheduled",
    "deferred",
    "capacity_limited",
)
HARD_FLAGS = ("paper_only", "report_only", "readonly")
PAYLOAD_FIELDS = frozenset(
    (
        "config_version",
        "market_id",
        "source_family",
        "freshness_status",
        "source_reliability_score",
        "market_time_sensitivity",
        "time_to_resolution_minutes",
        "team_capacity_score",
        "refresh_schedule_status",
        "next_refresh_minutes",
        "refresh_cadence_minutes",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchSourceRefreshScheduleV10Input:
    market_id: str
    source_family: str
    freshness_status: str
    source_reliability_score: Decimal
    market_time_sensitivity: Decimal
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_id",
            _require_canonical_string("market_id", self.market_id),
        )
        object.__setattr__(
            self,
            "source_family",
            _require_canonical_string("source_family", self.source_family),
        )
        object.__setattr__(
            self,
            "freshness_status",
            _require_member("freshness_status", self.freshness_status, FRESHNESS_STATUSES),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _normalize_score("source_reliability_score", self.source_reliability_score),
        )
        object.__setattr__(
            self,
            "market_time_sensitivity",
            _normalize_score("market_time_sensitivity", self.market_time_sensitivity),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_whole_minutes(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_score("team_capacity_score", self.team_capacity_score),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceRefreshScheduleV10Report:
    market_id: str
    source_family: str
    freshness_status: str
    source_reliability_score: Decimal
    market_time_sensitivity: Decimal
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    refresh_schedule_status: str
    next_refresh_minutes: Decimal
    refresh_cadence_minutes: Decimal
    reason_codes: tuple[str, ...]
    payload: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "market_id",
            _require_canonical_string("market_id", self.market_id),
        )
        object.__setattr__(
            self,
            "source_family",
            _require_canonical_string("source_family", self.source_family),
        )
        object.__setattr__(
            self,
            "freshness_status",
            _require_member("freshness_status", self.freshness_status, FRESHNESS_STATUSES),
        )
        for field_name in (
            "source_reliability_score",
            "market_time_sensitivity",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_whole_minutes(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "refresh_schedule_status",
            _require_member(
                "refresh_schedule_status",
                self.refresh_schedule_status,
                REFRESH_SCHEDULE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "next_refresh_minutes",
            _normalize_whole_minutes("next_refresh_minutes", self.next_refresh_minutes),
        )
        object.__setattr__(
            self,
            "refresh_cadence_minutes",
            _normalize_positive_whole_minutes(
                "refresh_cadence_minutes",
                self.refresh_cadence_minutes,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        if self.payload != _json_ready(_report_payload(self)):
            raise ValueError("payload must match report fields")


def strategy_research_source_refresh_schedule_v10(
    inputs: ResearchSourceRefreshScheduleV10Input,
) -> ResearchSourceRefreshScheduleV10Report:
    if type(inputs) is not ResearchSourceRefreshScheduleV10Input:
        raise ValueError("inputs must be a ResearchSourceRefreshScheduleV10Input")
    _require_hard_flags("inputs", inputs)

    refresh_cadence_minutes = _refresh_cadence_minutes(inputs)
    refresh_schedule_status = _refresh_schedule_status(inputs, refresh_cadence_minutes)
    next_refresh_minutes = _next_refresh_minutes(
        refresh_schedule_status,
        refresh_cadence_minutes,
    )
    reason_codes = _reason_codes(inputs, refresh_schedule_status)
    report_values = {
        "market_id": inputs.market_id,
        "source_family": inputs.source_family,
        "freshness_status": inputs.freshness_status,
        "source_reliability_score": inputs.source_reliability_score,
        "market_time_sensitivity": inputs.market_time_sensitivity,
        "time_to_resolution_minutes": inputs.time_to_resolution_minutes,
        "team_capacity_score": inputs.team_capacity_score,
        "refresh_schedule_status": refresh_schedule_status,
        "next_refresh_minutes": next_refresh_minutes,
        "refresh_cadence_minutes": refresh_cadence_minutes,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceRefreshScheduleV10Report(
        **report_values,
        payload=_json_ready({"config_version": CONFIG_VERSION, **report_values}),
    )


def strategy_research_source_refresh_schedule_v10_payload(
    report: ResearchSourceRefreshScheduleV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceRefreshScheduleV10Report:
        _require_hard_flags("report", report)
        payload = _json_ready(_report_payload(report))
    elif type(report) is dict:
        _validate_payload_fields(report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchSourceRefreshScheduleV10Report")

    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_payload_fields(payload)
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


def _validate_report(report: ResearchSourceRefreshScheduleV10Report) -> None:
    expected_cadence = _refresh_cadence_minutes(report)
    expected_status = _refresh_schedule_status(report, expected_cadence)
    expected_next_refresh = _next_refresh_minutes(expected_status, expected_cadence)
    if report.refresh_schedule_status != expected_status:
        raise ValueError("refresh_schedule_status must match inputs")
    if report.refresh_cadence_minutes != expected_cadence:
        raise ValueError("refresh_cadence_minutes must match inputs")
    if report.next_refresh_minutes != expected_next_refresh:
        raise ValueError("next_refresh_minutes must match inputs")
    if report.reason_codes != _reason_codes(report, expected_status):
        raise ValueError("reason_codes must match refresh schedule")


def _refresh_cadence_minutes(value: object) -> Decimal:
    if (
        getattr(value, "freshness_status") == "stale"
        or _reliability_bucket(value) == "low"
        or _time_sensitivity_bucket(value) == "high"
        or _resolution_window_bucket(value) == "critical"
    ):
        return IMMEDIATE_CADENCE_MINUTES
    if (
        getattr(value, "freshness_status") == "aging"
        or _reliability_bucket(value) == "medium"
        or _time_sensitivity_bucket(value) == "medium"
        or _resolution_window_bucket(value) == "compressed"
    ):
        return ACTIVE_CADENCE_MINUTES
    return LOW_PRESSURE_CADENCE_MINUTES


def _refresh_schedule_status(value: object, refresh_cadence_minutes: Decimal) -> str:
    if _capacity_bucket(value) == "constrained":
        return "capacity_limited"
    if (
        getattr(value, "freshness_status") == "stale"
        or _reliability_bucket(value) == "low"
        or _resolution_window_bucket(value) == "critical"
    ):
        return "refresh_now"
    if refresh_cadence_minutes == LOW_PRESSURE_CADENCE_MINUTES:
        return "deferred"
    return "scheduled"


def _next_refresh_minutes(
    refresh_schedule_status: str,
    refresh_cadence_minutes: Decimal,
) -> Decimal:
    if refresh_schedule_status == "refresh_now":
        return ZERO
    if refresh_schedule_status == "capacity_limited":
        return (refresh_cadence_minutes * TWO).quantize(DECIMAL_QUANTUM)
    return refresh_cadence_minutes


def _reason_codes(value: object, refresh_schedule_status: str) -> tuple[str, ...]:
    if refresh_schedule_status == "capacity_limited":
        status_code = "refresh_capacity_limited"
    elif refresh_schedule_status == "deferred":
        status_code = "refresh_deferred"
    elif refresh_schedule_status == "scheduled":
        status_code = "refresh_scheduled"
    else:
        status_code = refresh_schedule_status
    return (
        f"freshness_{getattr(value, 'freshness_status')}",
        f"reliability_{_reliability_bucket(value)}",
        f"time_sensitivity_{_time_sensitivity_bucket(value)}",
        f"resolution_window_{_resolution_window_bucket(value)}",
        f"capacity_{_capacity_bucket(value)}",
        status_code,
    )


def _reliability_bucket(value: object) -> str:
    score = getattr(value, "source_reliability_score")
    if score >= HIGH_RELIABILITY_FLOOR:
        return "high"
    if score >= LOW_RELIABILITY_FLOOR:
        return "medium"
    return "low"


def _time_sensitivity_bucket(value: object) -> str:
    score = getattr(value, "market_time_sensitivity")
    if score >= HIGH_SENSITIVITY_FLOOR:
        return "high"
    if score >= MEDIUM_SENSITIVITY_FLOOR:
        return "medium"
    return "low"


def _resolution_window_bucket(value: object) -> str:
    minutes = getattr(value, "time_to_resolution_minutes")
    if minutes <= CRITICAL_RESOLUTION_MINUTES:
        return "critical"
    if minutes <= COMPRESSED_RESOLUTION_MINUTES:
        return "compressed"
    return "open"


def _capacity_bucket(value: object) -> str:
    score = getattr(value, "team_capacity_score")
    if score >= HEALTHY_CAPACITY_FLOOR:
        return "healthy"
    if score >= USABLE_CAPACITY_FLOOR:
        return "usable"
    return "constrained"


def _report_payload(report: ResearchSourceRefreshScheduleV10Report) -> dict[str, Any]:
    return {
        "config_version": CONFIG_VERSION,
        "market_id": report.market_id,
        "source_family": report.source_family,
        "freshness_status": report.freshness_status,
        "source_reliability_score": report.source_reliability_score,
        "market_time_sensitivity": report.market_time_sensitivity,
        "time_to_resolution_minutes": report.time_to_resolution_minutes,
        "team_capacity_score": report.team_capacity_score,
        "refresh_schedule_status": report.refresh_schedule_status,
        "next_refresh_minutes": report.next_refresh_minutes,
        "refresh_cadence_minutes": report.refresh_cadence_minutes,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(DECIMAL_QUANTUM))
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool or value is None:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_score(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(DECIMAL_QUANTUM)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_whole_minutes(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    normalized = value.quantize(DECIMAL_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_whole_minutes(field_name: str, value: object) -> Decimal:
    normalized = _normalize_whole_minutes(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be greater than zero")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return reason_codes


def _validate_payload_fields(payload: dict[str, Any]) -> None:
    for key in payload:
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        if key not in PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        if label == "payload":
            raise ValueError("payload paper_only must be True")
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        if label == "payload":
            raise ValueError("payload report_only must be True")
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        if label == "payload":
            raise ValueError("payload readonly must be True")
        raise ValueError(f"{label} must be readonly")


__all__ = (
    "ResearchSourceRefreshScheduleV10Input",
    "ResearchSourceRefreshScheduleV10Report",
    "strategy_research_source_refresh_schedule_v10",
    "strategy_research_source_refresh_schedule_v10_payload",
)
