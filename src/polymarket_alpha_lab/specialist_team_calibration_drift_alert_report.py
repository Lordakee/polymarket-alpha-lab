"""Public-safe specialist team calibration drift alert report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


DEFAULT_SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION = (
    "specialist-team-calibration-drift-alert-report-v0"
)

SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_STATUSES = ("pass", "watch", "block")

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
HEX_CHARS = frozenset("0123456789abcdef")

THRESHOLD_BREACHED_REASON = "calibration_drift_threshold_breached"
RECENT_ERROR_ABOVE_HISTORY_REASON = "recent_error_above_historical_probability"
NO_RECENT_PREDICTIONS_REASON = "no_recent_predictions"
CLEAR_REASON = "calibration_drift_clear"
REASON_CODE_SEQUENCE = (
    THRESHOLD_BREACHED_REASON,
    RECENT_ERROR_ABOVE_HISTORY_REASON,
    NO_RECENT_PREDICTIONS_REASON,
    CLEAR_REASON,
)

MANUAL_NEXT_STEP_BY_STATUS = {
    "pass": "manual_no_action",
    "watch": "manual_review_calibration_drift_evidence",
    "block": "manual_escalate_calibration_drift_alert",
}


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        _join("li", "ve"),
        _join("au", "th"),
        _join("wal", "let"),
        _join("or", "der"),
        _join("tra", "de"),
        _join("k", "ey"),
        _join("key", "s"),
        _join("private", "_", "key"),
        _join("api", "_", "key"),
        _join("secret", "_", "key"),
        "signed",
        "mutation",
        "network",
        "connect",
        "persist",
        "durable",
        "jsonl",
    ),
)

__all__ = (
    "DEFAULT_SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION",
    "SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_STATUSES",
    "SpecialistTeamCalibrationDriftAlertReport",
    "build_specialist_team_calibration_drift_alert_report",
    "specialist_team_calibration_drift_alert_report_digest",
    "specialist_team_calibration_drift_alert_report_payload",
    "validate_specialist_team_calibration_drift_alert_public_payload",
)


@dataclass(frozen=True)
class SpecialistTeamCalibrationDriftAlertReport:
    config_version: str
    team_id: str
    recent_prediction_count: Decimal
    recent_error_probability: Decimal
    historical_error_probability: Decimal
    drift_threshold_probability: Decimal
    drift_probability: Decimal
    calibration_drift_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    public_payload: dict[str, Any]
    payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamCalibrationDriftAlertReport, "report")
        object.__setattr__(
            self,
            "config_version",
            _require_config_version(self.config_version),
        )
        object.__setattr__(self, "team_id", _require_public_code("team_id", self.team_id))
        object.__setattr__(
            self,
            "recent_prediction_count",
            _normalize_integer_decimal(
                "recent_prediction_count",
                self.recent_prediction_count,
            ),
        )
        for field_name in (
            "recent_error_probability",
            "historical_error_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "drift_threshold_probability",
            _normalize_positive_probability_decimal(
                "drift_threshold_probability",
                self.drift_threshold_probability,
            ),
        )
        object.__setattr__(
            self,
            "drift_probability",
            _normalize_drift_decimal("drift_probability", self.drift_probability),
        )
        if self.drift_probability != _quantize(
            self.recent_error_probability - self.historical_error_probability,
        ):
            raise ValueError("drift_probability must match recent minus historical")
        object.__setattr__(
            self,
            "calibration_drift_status",
            _require_status("calibration_drift_status", self.calibration_drift_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.calibration_drift_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("calibration_drift_status must match reason_codes")
        object.__setattr__(
            self,
            "manual_next_step",
            _require_public_code("manual_next_step", self.manual_next_step),
        )
        if self.manual_next_step != MANUAL_NEXT_STEP_BY_STATUS[self.calibration_drift_status]:
            raise ValueError("manual_next_step must match calibration_drift_status")
        _require_hard_flags("report", self)
        _require_sha256("payload_digest", self.payload_digest)
        if type(self.public_payload) is not dict:
            raise ValueError("public_payload must be a dict")
        _reject_unsafe_public_payload(self.public_payload)
        _require_public_payload_schema(self.public_payload)
        if self.payload_digest != _digest_public_payload(self.public_payload):
            raise ValueError("payload_digest must match public_payload")
        if self.public_payload.get("payload_digest") != self.payload_digest:
            raise ValueError("public_payload payload_digest must match payload_digest")


def build_specialist_team_calibration_drift_alert_report(
    *,
    team_id: str,
    recent_prediction_count: Decimal,
    recent_error_probability: Decimal,
    historical_error_probability: Decimal,
    drift_threshold_probability: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SpecialistTeamCalibrationDriftAlertReport:
    normalized_team_id = _require_public_code("team_id", team_id)
    normalized_recent_prediction_count = _normalize_integer_decimal(
        "recent_prediction_count",
        recent_prediction_count,
    )
    normalized_recent_error_probability = _normalize_probability_decimal(
        "recent_error_probability",
        recent_error_probability,
    )
    normalized_historical_error_probability = _normalize_probability_decimal(
        "historical_error_probability",
        historical_error_probability,
    )
    normalized_drift_threshold_probability = _normalize_positive_probability_decimal(
        "drift_threshold_probability",
        drift_threshold_probability,
    )
    _require_flags(paper_only=paper_only, report_only=report_only, readonly=readonly)
    drift_probability = _quantize(
        normalized_recent_error_probability - normalized_historical_error_probability,
    )
    reason_codes = _reason_codes(
        recent_prediction_count=normalized_recent_prediction_count,
        recent_error_probability=normalized_recent_error_probability,
        historical_error_probability=normalized_historical_error_probability,
        drift_probability=drift_probability,
        drift_threshold_probability=normalized_drift_threshold_probability,
    )
    status = _status_from_reason_codes(reason_codes)
    values = {
        "config_version": DEFAULT_SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION,
        "team_id": normalized_team_id,
        "recent_prediction_count": normalized_recent_prediction_count,
        "recent_error_probability": normalized_recent_error_probability,
        "historical_error_probability": normalized_historical_error_probability,
        "drift_threshold_probability": normalized_drift_threshold_probability,
        "drift_probability": drift_probability,
        "calibration_drift_status": status,
        "reason_codes": reason_codes,
        "manual_next_step": MANUAL_NEXT_STEP_BY_STATUS[status],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload_without_digest = _payload_from_values(values)
    payload_digest = _digest_public_payload(payload_without_digest)
    public_payload = dict(payload_without_digest)
    public_payload["payload_digest"] = payload_digest
    return SpecialistTeamCalibrationDriftAlertReport(
        **values,
        public_payload=public_payload,
        payload_digest=payload_digest,
    )


def specialist_team_calibration_drift_alert_report_payload(
    report: SpecialistTeamCalibrationDriftAlertReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SpecialistTeamCalibrationDriftAlertReport:
        _require_hard_flags("report", report)
        if report.payload_digest != _digest_public_payload(report.public_payload):
            raise ValueError("payload_digest must match public_payload")
        _reject_unsafe_public_payload(report.public_payload)
        _require_public_payload_schema(report.public_payload)
        return dict(report.public_payload)
    if type(report) is dict:
        validate_specialist_team_calibration_drift_alert_public_payload(report)
        return report
    raise ValueError("report must be a SpecialistTeamCalibrationDriftAlertReport")


def specialist_team_calibration_drift_alert_report_digest(
    report: SpecialistTeamCalibrationDriftAlertReport | dict[str, Any],
) -> str:
    payload = specialist_team_calibration_drift_alert_report_payload(report)
    payload_digest = payload["payload_digest"]
    if type(payload_digest) is not str:
        raise ValueError("payload_digest must be a string")
    return payload_digest


def validate_specialist_team_calibration_drift_alert_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public_payload must be a dict")
    _reject_unsafe_public_payload(payload)
    supplied_digest = payload.get("payload_digest")
    if type(supplied_digest) is not str:
        raise ValueError("payload_digest must be a string")
    _require_sha256("payload_digest", supplied_digest)
    if supplied_digest != _digest_public_payload(payload):
        raise ValueError("payload_digest must match public_payload")
    _require_public_payload_schema(payload)
    return True


def _reason_codes(
    *,
    recent_prediction_count: Decimal,
    recent_error_probability: Decimal,
    historical_error_probability: Decimal,
    drift_probability: Decimal,
    drift_threshold_probability: Decimal,
) -> tuple[str, ...]:
    if recent_prediction_count == ZERO:
        return (NO_RECENT_PREDICTIONS_REASON,)
    reasons: list[str] = []
    if drift_probability >= drift_threshold_probability:
        reasons.append(THRESHOLD_BREACHED_REASON)
    if recent_error_probability > historical_error_probability:
        reasons.append(RECENT_ERROR_ABOVE_HISTORY_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if THRESHOLD_BREACHED_REASON in reason_codes:
        return "block"
    if (
        NO_RECENT_PREDICTIONS_REASON in reason_codes
        or RECENT_ERROR_ABOVE_HISTORY_REASON in reason_codes
    ):
        return "watch"
    return "pass"


def _payload_from_values(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "config_version": values["config_version"],
        "team_id": values["team_id"],
        "recent_prediction_count": _decimal_to_string(values["recent_prediction_count"]),
        "recent_error_probability": _decimal_to_string(values["recent_error_probability"]),
        "historical_error_probability": _decimal_to_string(
            values["historical_error_probability"],
        ),
        "drift_threshold_probability": _decimal_to_string(
            values["drift_threshold_probability"],
        ),
        "drift_probability": _decimal_to_string(values["drift_probability"]),
        "calibration_drift_status": values["calibration_drift_status"],
        "reason_codes": list(values["reason_codes"]),
        "manual_next_step": values["manual_next_step"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _require_public_payload_schema(payload: dict[str, Any]) -> None:
    expected_fields = {
        "config_version",
        "team_id",
        "recent_prediction_count",
        "recent_error_probability",
        "historical_error_probability",
        "drift_threshold_probability",
        "drift_probability",
        "calibration_drift_status",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
        "payload_digest",
    }
    if set(payload) != expected_fields:
        raise ValueError("public_payload fields are invalid")
    _require_config_version(_require_string("config_version", payload["config_version"]))
    _require_public_code("team_id", payload["team_id"])
    for field_name in (
        "recent_prediction_count",
        "recent_error_probability",
        "historical_error_probability",
        "drift_threshold_probability",
        "drift_probability",
    ):
        if type(payload[field_name]) is not str:
            raise ValueError("numeric public payload values must be strings")
    _normalize_integer_decimal(
        "recent_prediction_count",
        Decimal(payload["recent_prediction_count"]),
    )
    for field_name in (
        "recent_error_probability",
        "historical_error_probability",
    ):
        _normalize_probability_decimal(field_name, Decimal(payload[field_name]))
    _normalize_positive_probability_decimal(
        "drift_threshold_probability",
        Decimal(payload["drift_threshold_probability"]),
    )
    _normalize_drift_decimal("drift_probability", Decimal(payload["drift_probability"]))
    _require_status("calibration_drift_status", payload["calibration_drift_status"])
    reason_codes_value = payload["reason_codes"]
    if type(reason_codes_value) is not list:
        raise ValueError("reason_codes must be a list")
    reason_codes = _normalize_reason_codes(tuple(reason_codes_value))
    if payload["calibration_drift_status"] != _status_from_reason_codes(reason_codes):
        raise ValueError("calibration_drift_status must match reason_codes")
    _require_public_code("manual_next_step", payload["manual_next_step"])
    if (
        payload["manual_next_step"]
        != MANUAL_NEXT_STEP_BY_STATUS[payload["calibration_drift_status"]]
    ):
        raise ValueError("manual_next_step must match calibration_drift_status")
    _require_flags(
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _digest_public_payload(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("payload_digest", None)
    encoded = json.dumps(
        unsigned,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return sha256(encoded).hexdigest()


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_code("reason_code", reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(reason_code)
    sequenced = tuple(reason for reason in REASON_CODE_SEQUENCE if reason in normalized)
    if sequenced != reason_codes:
        raise ValueError("reason_codes must use supported sequence")
    if CLEAR_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("calibration_drift_clear must be the only clear reason")
    return reason_codes


def _require_config_version(value: str) -> str:
    value = _require_string("config_version", value)
    if value != DEFAULT_SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported version")
    return value


def _require_status(field_name: str, value: str) -> str:
    value = _require_string(field_name, value)
    if value not in SPECIALIST_TEAM_CALIBRATION_DRIFT_ALERT_STATUSES:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_public_code(field_name: str, value: object) -> str:
    value = _require_string(field_name, value)
    if not value or any(char not in PUBLIC_CODE_CHARS for char in value):
        raise ValueError(f"{field_name} must be a public code")
    normalized = value.casefold()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public")
    return value


def _require_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _normalize_integer_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must use 6 decimal places")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _normalize_probability_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return _quantize(value)


def _normalize_positive_probability_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_probability_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_drift_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < -ONE or value > ONE:
        raise ValueError(f"{field_name} must be between -1.000000 and 1.000000")
    return _quantize(value)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value could not be normalized") from exc


def _decimal_to_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_flags(*, paper_only: object, report_only: object, readonly: object) -> None:
    if paper_only is not True:
        raise ValueError("paper_only must be True")
    if report_only is not True:
        raise ValueError("report_only must be True")
    if readonly is not True:
        raise ValueError("readonly must be True")


def _require_sha256(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload key")
            lowered_key = key.casefold()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(child)
    elif isinstance(value, list):
        for child in value:
            _reject_unsafe_public_payload(child)
    elif type(value) is str:
        lowered_value = value.casefold()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError("unsafe public payload")
    elif type(value) in (int, float, Decimal):
        raise ValueError("numeric public payload values must be strings")
    elif type(value) is not bool and value is not None:
        raise ValueError("public payload value type is unsupported")
