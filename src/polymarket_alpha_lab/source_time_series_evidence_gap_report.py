from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


CLEAR_REASON_CODE = "source_time_series_evidence_gap_clear"
ZERO_EXPECTED_REASON_CODE = "time_series_expected_observation_count_zero"
OFFICIAL_MISSING_REASON_CODE = "official_time_series_missing"
CAPTURE_INCOMPLETE_REASON_CODE = "time_series_capture_incomplete"
INTERVALS_MISSING_REASON_CODE = "time_series_intervals_missing"
STALE_REASON_CODE = "latest_time_series_observation_stale"

REASON_CODES = (
    CLEAR_REASON_CODE,
    ZERO_EXPECTED_REASON_CODE,
    OFFICIAL_MISSING_REASON_CODE,
    CAPTURE_INCOMPLETE_REASON_CODE,
    INTERVALS_MISSING_REASON_CODE,
    STALE_REASON_CODE,
)
EVIDENCE_GAP_STATUSES = ("clear", "watch", "blocked")
STALE_AFTER_HOURS = Decimal("2.000000")

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class SourceTimeSeriesEvidenceGapReport:
    expected_observation_count: Decimal
    captured_observation_count: Decimal
    missing_interval_count: Decimal
    latest_observation_age_hours: Decimal
    official_series_present: bool
    evidence_gap_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("SourceTimeSeriesEvidenceGapReport does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in (
            "expected_observation_count",
            "captured_observation_count",
            "missing_interval_count",
            "latest_observation_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.official_series_present) is not bool:
            raise ValueError("official_series_present must be a bool")
        _require_member(
            "evidence_gap_status",
            self.evidence_gap_status,
            EVIDENCE_GAP_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_public_string("manual_next_step", self.manual_next_step)
        _require_hard_flags(self)
        _validate_report(self)
        if self.payload_digest == "":
            object.__setattr__(self, "payload_digest", _payload_digest_for_report(self))
        else:
            object.__setattr__(
                self,
                "payload_digest",
                _require_digest("payload_digest", self.payload_digest),
            )
            if self.payload_digest != _payload_digest_for_report(self):
                raise ValueError("payload_digest must match public payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return source_time_series_evidence_gap_public_payload(self)


def build_source_time_series_evidence_gap_report(
    *,
    expected_observation_count: Decimal,
    captured_observation_count: Decimal,
    missing_interval_count: Decimal,
    latest_observation_age_hours: Decimal,
    official_series_present: bool,
) -> SourceTimeSeriesEvidenceGapReport:
    expected = _normalize_nonnegative_decimal(
        "expected_observation_count",
        expected_observation_count,
    )
    captured = _normalize_nonnegative_decimal(
        "captured_observation_count",
        captured_observation_count,
    )
    missing = _normalize_nonnegative_decimal(
        "missing_interval_count",
        missing_interval_count,
    )
    latest_age = _normalize_nonnegative_decimal(
        "latest_observation_age_hours",
        latest_observation_age_hours,
    )
    if type(official_series_present) is not bool:
        raise ValueError("official_series_present must be a bool")

    reason_codes = _reason_codes(
        expected_observation_count=expected,
        captured_observation_count=captured,
        missing_interval_count=missing,
        latest_observation_age_hours=latest_age,
        official_series_present=official_series_present,
    )
    status = _status_for_reason_codes(reason_codes)
    return SourceTimeSeriesEvidenceGapReport(
        expected_observation_count=expected,
        captured_observation_count=captured,
        missing_interval_count=missing,
        latest_observation_age_hours=latest_age,
        official_series_present=official_series_present,
        evidence_gap_status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status, reason_codes),
    )


def source_time_series_evidence_gap_public_payload(
    report: SourceTimeSeriesEvidenceGapReport,
) -> dict[str, Any]:
    if type(report) is not SourceTimeSeriesEvidenceGapReport:
        raise ValueError("report must be a SourceTimeSeriesEvidenceGapReport")
    _validate_report(report)
    payload = _public_payload_for_digest(report)
    payload["payload_digest"] = report.payload_digest
    validate_source_time_series_evidence_gap_public_payload(payload)
    return payload


def validate_source_time_series_evidence_gap_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_exact_keys(
        "payload",
        payload,
        (
            "expected_observation_count",
            "captured_observation_count",
            "missing_interval_count",
            "latest_observation_age_hours",
            "official_series_present",
            "evidence_gap_status",
            "reason_codes",
            "manual_next_step",
            "paper_only",
            "report_only",
            "readonly",
            "payload_digest",
        ),
    )
    for field_name in (
        "expected_observation_count",
        "captured_observation_count",
        "missing_interval_count",
        "latest_observation_age_hours",
    ):
        _require_decimal_payload_string(field_name, payload[field_name])
    if type(payload["official_series_present"]) is not bool:
        raise ValueError("official_series_present must be a bool")
    _require_member(
        "evidence_gap_status",
        payload["evidence_gap_status"],
        EVIDENCE_GAP_STATUSES,
    )
    _normalize_payload_reason_codes(payload["reason_codes"])
    _require_public_string("manual_next_step", payload["manual_next_step"])
    _require_public_payload_flags(payload)
    digest_value = _require_digest("payload_digest", payload["payload_digest"])
    if digest_value != _payload_digest(payload):
        raise ValueError("payload_digest must match public payload")
    _reject_public_numeric_values(payload)
    return True


def _reason_codes(
    *,
    expected_observation_count: Decimal,
    captured_observation_count: Decimal,
    missing_interval_count: Decimal,
    latest_observation_age_hours: Decimal,
    official_series_present: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not official_series_present:
        reasons.append(OFFICIAL_MISSING_REASON_CODE)
    if expected_observation_count == ZERO:
        reasons.append(ZERO_EXPECTED_REASON_CODE)
    elif captured_observation_count < expected_observation_count:
        reasons.append(CAPTURE_INCOMPLETE_REASON_CODE)
    if missing_interval_count > ZERO:
        reasons.append(INTERVALS_MISSING_REASON_CODE)
    if latest_observation_age_hours > STALE_AFTER_HOURS:
        reasons.append(STALE_REASON_CODE)
    if not reasons:
        reasons.append(CLEAR_REASON_CODE)
    return tuple(reason for reason in REASON_CODES if reason in reasons)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (CLEAR_REASON_CODE,):
        return "clear"
    if any(
        reason_code
        in (
            OFFICIAL_MISSING_REASON_CODE,
            CAPTURE_INCOMPLETE_REASON_CODE,
            INTERVALS_MISSING_REASON_CODE,
            STALE_REASON_CODE,
        )
        for reason_code in reason_codes
    ):
        return "blocked"
    return "watch"


def _manual_next_step(status: str, reason_codes: tuple[str, ...]) -> str:
    if status == "clear":
        return "continue_report_only_time_series_monitoring"
    if reason_codes == (ZERO_EXPECTED_REASON_CODE,):
        return "manual_confirm_time_series_expectation"
    return "manual_source_time_series_backfill_required"


def _public_payload_for_digest(
    report: SourceTimeSeriesEvidenceGapReport,
) -> dict[str, Any]:
    return {
        "expected_observation_count": _decimal_payload(
            report.expected_observation_count,
        ),
        "captured_observation_count": _decimal_payload(
            report.captured_observation_count,
        ),
        "missing_interval_count": _decimal_payload(report.missing_interval_count),
        "latest_observation_age_hours": _decimal_payload(
            report.latest_observation_age_hours,
        ),
        "official_series_present": report.official_series_present,
        "evidence_gap_status": report.evidence_gap_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _payload_digest_for_report(report: SourceTimeSeriesEvidenceGapReport) -> str:
    return _payload_digest(_public_payload_for_digest(report))


def _payload_digest(payload: dict[str, Any]) -> str:
    normalized = dict(payload)
    normalized.pop("payload_digest", None)
    canonical = json.dumps(
        normalized,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _require_decimal_payload_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    if parsed.is_nan() or parsed.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    if parsed < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if _decimal_payload(parsed.quantize(QUANTUM)) != value:
        raise ValueError(f"{field_name} must use six decimal places")
    return parsed


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for item in value:
        _require_member("reason_code", item, REASON_CODES)
        if item in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(item)
    return tuple(reason for reason in REASON_CODES if reason in normalized)


def _normalize_payload_reason_codes(value: object) -> list[str]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    normalized: list[str] = []
    for item in value:
        _require_member("reason_code", item, REASON_CODES)
        if item in normalized:
            raise ValueError("reason_codes must be unique")
        normalized.append(item)
    ordered = [reason for reason in REASON_CODES if reason in normalized]
    if normalized != ordered:
        raise ValueError("reason_codes sequence must match policy")
    return normalized


def _validate_report(report: SourceTimeSeriesEvidenceGapReport) -> None:
    expected_reason_codes = _reason_codes(
        expected_observation_count=report.expected_observation_count,
        captured_observation_count=report.captured_observation_count,
        missing_interval_count=report.missing_interval_count,
        latest_observation_age_hours=report.latest_observation_age_hours,
        official_series_present=report.official_series_present,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match evidence gaps")
    if report.evidence_gap_status != _status_for_reason_codes(report.reason_codes):
        raise ValueError("evidence_gap_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(
        report.evidence_gap_status,
        report.reason_codes,
    ):
        raise ValueError("manual_next_step must match evidence_gap_status")
    if (
        report.expected_observation_count == ZERO
        and report.captured_observation_count != ZERO
    ):
        raise ValueError("captured_observation_count requires expected observations")
    if report.captured_observation_count > report.expected_observation_count:
        raise ValueError("captured_observation_count must not exceed expected count")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} is not supported")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or value == "":
        raise ValueError(f"{field_name} must be public text")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_exact_keys(
    field_name: str,
    value: dict[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    if tuple(value.keys()) != expected_keys:
        raise ValueError(f"{field_name} fields must match expected public payload")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (Decimal, int, float):
        raise ValueError("public payload numeric values must be strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)
