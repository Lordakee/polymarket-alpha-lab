"""Readonly resolution oracle latency watch report reducer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
SEVERE_THRESHOLD_MULTIPLE = Decimal("2.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

PASS_REASON = "resolution_oracle_latency_within_threshold"
MISSING_REASON = "resolution_oracle_source_missing"
AGE_EXCEEDS_REASON = "oracle_update_age_exceeds_threshold"
AGE_SEVERE_REASON = "oracle_update_age_severely_exceeds_threshold"
WINDOW_COMPRESSED_REASON = "expected_resolution_window_compressed"
DEPENDENCY_REASON = "resolution_dependency_chain_present"
REASON_CODES = (
    MISSING_REASON,
    AGE_SEVERE_REASON,
    AGE_EXCEEDS_REASON,
    WINDOW_COMPRESSED_REASON,
    DEPENDENCY_REASON,
    PASS_REASON,
)

STEP_CONTINUE = "continue_resolution_oracle_monitoring"
STEP_RECHECK = "manually_recheck_resolution_oracle"
STEP_PAUSE = "pause_for_manual_resolution_oracle_review"
MANUAL_STEPS = (STEP_CONTINUE, STEP_RECHECK, STEP_PAUSE)

__all__ = (
    "SourceResolutionOracleLatencyWatchReport",
    "build_source_resolution_oracle_latency_watch_report",
    "source_resolution_oracle_latency_watch_report_digest",
    "source_resolution_oracle_latency_watch_report_to_public_payload",
    "validate_source_resolution_oracle_latency_watch_report_payload",
)


@dataclass(frozen=True)
class SourceResolutionOracleLatencyWatchReport:
    oracle_source_present: bool
    oracle_update_age_hours: Decimal
    expected_resolution_hours: Decimal
    dependency_count: Decimal
    latency_threshold_hours: Decimal
    oracle_latency_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SourceResolutionOracleLatencyWatchReport:
            raise TypeError(
                "SourceResolutionOracleLatencyWatchReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, SourceResolutionOracleLatencyWatchReport, "report")
        _require_bool("oracle_source_present", self.oracle_source_present)
        for name in (
            "oracle_update_age_hours",
            "expected_resolution_hours",
            "dependency_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "latency_threshold_hours",
            _require_positive_decimal(
                "latency_threshold_hours",
                self.latency_threshold_hours,
            ),
        )
        _require_integer_decimal("dependency_count", self.dependency_count)
        _require_status("oracle_latency_status", self.oracle_latency_status)
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
        return source_resolution_oracle_latency_watch_report_to_public_payload(self)


def build_source_resolution_oracle_latency_watch_report(
    *,
    oracle_source_present: bool,
    oracle_update_age_hours: Decimal,
    expected_resolution_hours: Decimal,
    dependency_count: Decimal,
    latency_threshold_hours: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SourceResolutionOracleLatencyWatchReport:
    values = {
        "oracle_source_present": _require_bool(
            "oracle_source_present",
            oracle_source_present,
        ),
        "oracle_update_age_hours": _require_nonnegative_decimal(
            "oracle_update_age_hours",
            oracle_update_age_hours,
        ),
        "expected_resolution_hours": _require_nonnegative_decimal(
            "expected_resolution_hours",
            expected_resolution_hours,
        ),
        "dependency_count": _require_nonnegative_decimal(
            "dependency_count",
            dependency_count,
        ),
        "latency_threshold_hours": _require_positive_decimal(
            "latency_threshold_hours",
            latency_threshold_hours,
        ),
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    _require_integer_decimal("dependency_count", values["dependency_count"])
    _require_hard_flags("input", _FlagView(paper_only, report_only, readonly))
    reasons = _reason_codes(
        oracle_source_present=values["oracle_source_present"],
        oracle_update_age_hours=values["oracle_update_age_hours"],
        expected_resolution_hours=values["expected_resolution_hours"],
        dependency_count=values["dependency_count"],
        latency_threshold_hours=values["latency_threshold_hours"],
    )
    status = _oracle_latency_status(reasons)
    return SourceResolutionOracleLatencyWatchReport(
        **values,
        oracle_latency_status=status,
        reason_codes=reasons,
        manual_next_step=_manual_next_step(status),
        payload_digest="",
    )


def source_resolution_oracle_latency_watch_report_digest(
    report: SourceResolutionOracleLatencyWatchReport,
) -> str:
    _require_exact_type(report, SourceResolutionOracleLatencyWatchReport, "report")
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_digest=True)
    _require_matching_digest(payload)
    return report.payload_digest


def source_resolution_oracle_latency_watch_report_to_public_payload(
    report: SourceResolutionOracleLatencyWatchReport,
) -> dict[str, Any]:
    _require_exact_type(report, SourceResolutionOracleLatencyWatchReport, "report")
    _require_hard_flags("report", report)
    payload = _payload_value(report, include_digest=True)
    _require_matching_digest(payload)
    return payload


def validate_source_resolution_oracle_latency_watch_report_payload(
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
    oracle_source_present: bool,
    oracle_update_age_hours: Decimal,
    expected_resolution_hours: Decimal,
    dependency_count: Decimal,
    latency_threshold_hours: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not oracle_source_present:
        reasons.append(MISSING_REASON)
    if oracle_update_age_hours >= latency_threshold_hours * SEVERE_THRESHOLD_MULTIPLE:
        reasons.append(AGE_SEVERE_REASON)
    elif oracle_update_age_hours > latency_threshold_hours:
        reasons.append(AGE_EXCEEDS_REASON)
    if expected_resolution_hours < latency_threshold_hours:
        reasons.append(WINDOW_COMPRESSED_REASON)
    if dependency_count > ZERO:
        reasons.append(DEPENDENCY_REASON)
    if not reasons:
        return (PASS_REASON,)
    return tuple(reasons)


def _oracle_latency_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    if MISSING_REASON in reason_codes or AGE_SEVERE_REASON in reason_codes:
        return STATUS_BLOCK
    return STATUS_WATCH


def _manual_next_step(status: str) -> str:
    if status == STATUS_PASS:
        return STEP_CONTINUE
    if status == STATUS_WATCH:
        return STEP_RECHECK
    if status == STATUS_BLOCK:
        return STEP_PAUSE
    raise ValueError("oracle_latency_status must be supported")


def _validate_report(report: SourceResolutionOracleLatencyWatchReport) -> None:
    expected_reasons = _reason_codes(
        oracle_source_present=report.oracle_source_present,
        oracle_update_age_hours=report.oracle_update_age_hours,
        expected_resolution_hours=report.expected_resolution_hours,
        dependency_count=report.dependency_count,
        latency_threshold_hours=report.latency_threshold_hours,
    )
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match oracle latency inputs")
    expected_status = _oracle_latency_status(expected_reasons)
    if report.oracle_latency_status != expected_status:
        raise ValueError("oracle_latency_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match oracle_latency_status")


def _payload_value(
    report: SourceResolutionOracleLatencyWatchReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    if not is_dataclass(report):
        raise ValueError("report must be a dataclass")
    payload: dict[str, Any] = {}
    for field in fields(report):
        if field.name == "payload_digest" and not include_digest:
            continue
        payload[field.name] = _json_ready(getattr(report, field.name))
    _require_payload_report_shape(payload, require_digest=include_digest)
    return payload


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return format(value.quantize(SIX), "f")
    if type(value) in (str, bool) or value is None:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    raise ValueError(f"unsupported public payload value {value!r}")


def _payload_digest(payload: dict[str, Any]) -> str:
    material = {
        name: value
        for name, value in payload.items()
        if name != "payload_digest"
    }
    return sha256(
        _canonical_payload_bytes(material),
    ).hexdigest()


def _canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    ordered = {name: payload[name] for name in sorted(payload)}
    return json.dumps(ordered, separators=(",", ":")).encode("utf-8")


def _require_matching_digest(payload: dict[str, Any]) -> None:
    if "payload_digest" not in payload:
        raise ValueError("payload_digest must be present")
    _require_sha256("payload_digest", payload["payload_digest"])
    if payload["payload_digest"] != _payload_digest(payload):
        raise ValueError("payload_digest must match public payload")


def _require_payload_report_shape(
    payload: dict[str, Any],
    *,
    require_digest: bool = True,
) -> None:
    expected_names = {
        "oracle_source_present",
        "oracle_update_age_hours",
        "expected_resolution_hours",
        "dependency_count",
        "latency_threshold_hours",
        "oracle_latency_status",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
    }
    if require_digest:
        expected_names = expected_names | {"payload_digest"}
    if set(payload) != expected_names:
        raise ValueError("public payload fields must match oracle latency report")
    if type(payload["oracle_source_present"]) is not bool:
        raise ValueError("payload oracle_source_present must be a bool")
    for name in (
        "oracle_update_age_hours",
        "expected_resolution_hours",
        "dependency_count",
        "latency_threshold_hours",
    ):
        if type(payload[name]) is not str:
            raise ValueError("public payload decimal values must be strings")
    _require_status("payload oracle_latency_status", payload["oracle_latency_status"])
    reason_codes = payload["reason_codes"]
    if type(reason_codes) is not list:
        raise ValueError("payload reason_codes must be a list")
    _require_reason_codes("payload reason_codes", tuple(reason_codes))
    _require_manual_step("payload manual_next_step", payload["manual_next_step"])
    _require_payload_hard_flags(payload)


def _reject_payload_numeric_objects(value: object) -> None:
    if type(value) in (Decimal, int, float):
        raise ValueError("public payload must not contain numeric objects")
    if isinstance(value, dict):
        for item in value.values():
            _reject_payload_numeric_objects(item)
    if isinstance(value, list):
        for item in value:
            _reject_payload_numeric_objects(item)


def _require_exact_type(value: object, expected_type: type, name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be a {expected_type.__name__}")


def _require_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")
    return value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    return value.quantize(SIX)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be non-negative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_integer_decimal(name: str, value: Decimal) -> None:
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be an integer count")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be supported")


def _require_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if len(value) == 0:
        raise ValueError(f"{name} must not be empty")
    for item in value:
        if type(item) is not str or item not in REASON_CODES:
            raise ValueError(f"{name} contains unsupported reason code")
    if PASS_REASON in value and value != (PASS_REASON,):
        raise ValueError(f"{name} pass reason must stand alone")
    return value


def _require_manual_step(name: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_STEPS:
        raise ValueError(f"{name} must be supported")


def _require_sha256(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a sha256 hex digest") from exc


def _require_hard_flags(name: str, value: Any) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if payload.get(name) is not True:
            raise ValueError(f"payload {name} must be True")
