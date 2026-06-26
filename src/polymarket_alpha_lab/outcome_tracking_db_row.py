"""Pure row codec for persisted outcome tracking reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.forecast_evidence import (
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.outcome_tracker import (
    OutcomeTrackingReport,
    _recover_forecast_evidence_config,
)


__all__ = (
    "OutcomeTrackingReportDbRow",
    "outcome_tracking_report_from_db_row",
    "outcome_tracking_report_to_db_row",
)


FORECAST_EVIDENCE_STATUSES = (
    "incomplete_data",
    "insufficient_evidence",
    "blocked_by_quality",
    "paper_review_ready",
)
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_MISSING = object()


@dataclass(frozen=True)
class OutcomeTrackingReportDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    total_markets_checked: int
    resolved_count: int
    pending_count: int
    observation_count: int
    forecast_evidence_status: str | None
    payload_json: dict[str, Any]
    paper_only: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "total_markets_checked",
            "resolved_count",
            "pending_count",
            "observation_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        _require_optional_forecast_evidence_status(
            "forecast_evidence_status",
            self.forecast_evidence_status,
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _validate_json_hard_flags(self.payload_json, "payload_json")
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.resolved_count + self.pending_count != self.total_markets_checked:
            raise ValueError(
                "resolved_count + pending_count must equal total_markets_checked",
            )
        if self.observation_count != self.resolved_count:
            raise ValueError("observation_count must equal resolved_count")
        _validate_materialized_fields_match_payload(self)


def outcome_tracking_report_to_db_row(
    report: OutcomeTrackingReport,
) -> OutcomeTrackingReportDbRow:
    if type(report) is not OutcomeTrackingReport:
        raise ValueError("report must be an OutcomeTrackingReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return OutcomeTrackingReportDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        total_markets_checked=report.total_markets_checked,
        resolved_count=report.resolved_count,
        pending_count=report.pending_count,
        observation_count=len(report.observations),
        forecast_evidence_status=(
            None
            if report.forecast_evidence_report is None
            else report.forecast_evidence_report.status
        ),
        payload_json=payload_json,
        paper_only=report.paper_only,
    )


def outcome_tracking_report_from_db_row(
    row: OutcomeTrackingReportDbRow,
) -> OutcomeTrackingReport:
    if type(row) is not OutcomeTrackingReportDbRow:
        raise ValueError("row must be an OutcomeTrackingReportDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(OutcomeTrackingReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"payload_json is not a valid outcome tracking report: {exc}") from exc
    if type(report) is not OutcomeTrackingReport:
        raise ValueError("payload_json must recover an OutcomeTrackingReport")
    report = _canonicalize_forecast_evidence_report(report)
    _validate_report_tree(report)
    expected_row = outcome_tracking_report_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def _canonicalize_forecast_evidence_report(
    report: OutcomeTrackingReport,
) -> OutcomeTrackingReport:
    if report.forecast_evidence_report is None:
        return report
    config = _recover_forecast_evidence_config(report.forecast_evidence_report)
    forecast_evidence_report = build_paper_forecast_evidence_report(
        report.observations,
        config=config,
        generated_at=report.generated_at,
    )
    return OutcomeTrackingReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        total_markets_checked=report.total_markets_checked,
        resolved_count=report.resolved_count,
        pending_count=report.pending_count,
        observations=report.observations,
        forecast_evidence_report=forecast_evidence_report,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _validate_row_matches_payload(
    row: OutcomeTrackingReportDbRow,
    expected: OutcomeTrackingReportDbRow,
) -> None:
    if row.report_sha256 != expected.report_sha256:
        raise ValueError("report_sha256 must match payload_json")
    for field_name in (
        "generated_at",
        "config_version",
        "total_markets_checked",
        "resolved_count",
        "pending_count",
        "observation_count",
        "forecast_evidence_status",
        "paper_only",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_materialized_fields_match_payload(
    row: OutcomeTrackingReportDbRow,
) -> None:
    payload_json = row.payload_json
    forecast_evidence_report = payload_json.get("forecast_evidence_report", _MISSING)
    expected_forecast_evidence_status = _MISSING
    if forecast_evidence_report is None:
        expected_forecast_evidence_status = None
    elif isinstance(forecast_evidence_report, dict):
        expected_forecast_evidence_status = forecast_evidence_report.get(
            "status",
            _MISSING,
        )
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at", _MISSING),
        "config_version": payload_json.get("config_version", _MISSING),
        "total_markets_checked": payload_json.get("total_markets_checked", _MISSING),
        "resolved_count": payload_json.get("resolved_count", _MISSING),
        "pending_count": payload_json.get("pending_count", _MISSING),
        "observation_count": len(payload_json.get("observations", ()))
        if isinstance(payload_json.get("observations", _MISSING), list)
        else _MISSING,
        "forecast_evidence_status": expected_forecast_evidence_status,
        "paper_only": payload_json.get("paper_only", _MISSING),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "config_version": row.config_version,
        "total_markets_checked": row.total_markets_checked,
        "resolved_count": row.resolved_count,
        "pending_count": row.pending_count,
        "observation_count": row.observation_count,
        "forecast_evidence_status": row.forecast_evidence_status,
        "paper_only": row.paper_only,
    }
    for field_name, actual_value in actual_values.items():
        if actual_value != expected_values[field_name]:
            raise ValueError(f"{field_name} must match payload_json")


def _validate_report_tree(report: OutcomeTrackingReport) -> None:
    _require_hard_flags_if_present("report", report)
    for index, observation in enumerate(report.observations):
        _require_hard_flags_if_present(f"observations {index}", observation)
    if report.forecast_evidence_report is not None:
        _require_hard_flags_if_present(
            "forecast_evidence_report",
            report.forecast_evidence_report,
        )
        for index, gate_result in enumerate(report.forecast_evidence_report.gate_results):
            _require_hard_flags_if_present(
                f"forecast_evidence_report gate_results {index}",
                gate_result,
            )
        for index, bucket in enumerate(report.forecast_evidence_report.buckets):
            _require_hard_flags_if_present(
                f"forecast_evidence_report buckets {index}",
                bucket,
            )


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("outcome tracking DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    return {key: _json_ready(item) for key, item in value.items()}


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    for flag_name in ("paper_only", "report_only", "readonly"):
        if flag_name in value and value[flag_name] is not True:
            raise ValueError(f"{field_name} {flag_name} must be true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_json_floats(item)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_forecast_evidence_status(
    field_name: str,
    value: object,
) -> None:
    if value is None:
        return
    if type(value) is not str or value not in FORECAST_EVIDENCE_STATUSES:
        raise ValueError(f"{field_name} must be a known forecast evidence status")


def _require_hard_flags_if_present(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if hasattr(value, flag_name) and getattr(value, flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")
