"""Pure row codec for persisted strategy risk audit reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.strategy_risk_audit import (
    REPORT_STATUSES,
    PaperStrategyRiskAuditReport,
)


__all__ = (
    "PaperStrategyRiskAuditReportDbRow",
    "strategy_risk_audit_report_from_db_row",
    "strategy_risk_audit_report_to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperStrategyRiskAuditReportDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    status: str
    gate_count: int
    pass_count: int
    fail_count: int
    incomplete_count: int
    gate_results_json: list[Any]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_member("status", self.status, REPORT_STATUSES)
        for field_name in (
            "gate_count",
            "pass_count",
            "fail_count",
            "incomplete_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.gate_count != self.pass_count + self.fail_count + self.incomplete_count:
            raise ValueError(
                "gate_count must equal pass_count + fail_count + incomplete_count",
            )
        if self.status != _status_from_counts(self.fail_count, self.incomplete_count):
            raise ValueError("status must match gate counts")
        object.__setattr__(
            self,
            "gate_results_json",
            _normalize_json_array("gate_results_json", self.gate_results_json),
        )
        if self.gate_count != len(self.gate_results_json):
            raise ValueError("gate_count must match gate_results_json")
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _validate_payload_hard_flags(self.payload_json, "payload_json")
        if self.gate_results_json != self.payload_json.get("gate_results"):
            raise ValueError("gate_results_json must match payload_json")
        _validate_row_scalars_match_payload(self)
        _require_hard_flags("DB row", self)
        if self.report_sha256 != _report_sha256(self.payload_json):
            raise ValueError("report_sha256 must match payload_json")


def strategy_risk_audit_report_to_db_row(
    report: PaperStrategyRiskAuditReport,
) -> PaperStrategyRiskAuditReportDbRow:
    if type(report) is not PaperStrategyRiskAuditReport:
        raise ValueError("report must be a PaperStrategyRiskAuditReport")
    _validate_report(report)
    payload_json = _json_ready(asdict(report))
    gate_results_json = payload_json.get("gate_results")
    if not isinstance(gate_results_json, list):
        raise ValueError("payload_json gate_results must be a JSON array")
    return PaperStrategyRiskAuditReportDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        gate_count=report.gate_count,
        pass_count=report.pass_count,
        fail_count=report.fail_count,
        incomplete_count=report.incomplete_count,
        gate_results_json=gate_results_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=True,
    )


def strategy_risk_audit_report_from_db_row(
    row: PaperStrategyRiskAuditReportDbRow,
) -> PaperStrategyRiskAuditReport:
    if type(row) is not PaperStrategyRiskAuditReportDbRow:
        raise ValueError("row must be a PaperStrategyRiskAuditReportDbRow")
    _reject_json_floats(row.gate_results_json)
    _reject_json_floats(row.payload_json)
    _validate_payload_hard_flags(row.payload_json, "payload_json")
    if row.gate_results_json != row.payload_json.get("gate_results"):
        raise ValueError("gate_results_json must match payload_json")
    try:
        report = from_jsonable(PaperStrategyRiskAuditReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid strategy risk audit report: {exc}",
        ) from exc
    if type(report) is not PaperStrategyRiskAuditReport:
        raise ValueError("payload_json must recover a PaperStrategyRiskAuditReport")
    _validate_report(report)
    expected_row = strategy_risk_audit_report_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def _validate_report(report: PaperStrategyRiskAuditReport) -> None:
    if report.paper_only is not True:
        raise ValueError("report paper_only must be True")
    if report.report_only is not True:
        raise ValueError("report report_only must be True")


def _validate_row_matches_payload(
    row: PaperStrategyRiskAuditReportDbRow,
    expected: PaperStrategyRiskAuditReportDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "status",
        "gate_count",
        "pass_count",
        "fail_count",
        "incomplete_count",
        "gate_results_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_scalars_match_payload(
    row: PaperStrategyRiskAuditReportDbRow,
) -> None:
    for field_name in (
        "generated_at",
        "config_version",
        "status",
        "gate_count",
        "pass_count",
        "fail_count",
        "incomplete_count",
    ):
        if row.payload_json.get(field_name) != _json_ready(getattr(row, field_name)):
            raise ValueError(f"{field_name} must match payload_json")


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
    raise ValueError("strategy risk audit DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    return _json_ready(value)


def _normalize_json_array(field_name: str, value: object) -> list[Any]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return normalized


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_floats(item)


def _validate_payload_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if value.get("paper_only") is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if value.get("report_only") is not True:
        raise ValueError(f"{field_name} report_only must be True")
    for key, item in value.items():
        if isinstance(item, dict):
            _validate_optional_payload_hard_flags(item, f"{field_name}.{key}")
        elif isinstance(item, (list, tuple)):
            for index, element in enumerate(item):
                _validate_optional_payload_hard_flags(
                    element,
                    f"{field_name}.{key}.{index}",
                )


def _validate_optional_payload_hard_flags(value: Any, field_name: str) -> None:
    if isinstance(value, dict):
        if "paper_only" in value and value["paper_only"] is not True:
            raise ValueError(f"{field_name} paper_only must be True")
        if "report_only" in value and value["report_only"] is not True:
            raise ValueError(f"{field_name} report_only must be True")
        for key, item in value.items():
            if isinstance(item, dict):
                _validate_optional_payload_hard_flags(item, f"{field_name}.{key}")
            elif isinstance(item, (list, tuple)):
                for index, element in enumerate(item):
                    _validate_optional_payload_hard_flags(
                        element,
                        f"{field_name}.{key}.{index}",
                    )
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_optional_payload_hard_flags(item, f"{field_name}.{index}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256")


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


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(field_name: str, value: Any) -> None:
    if value.paper_only is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if value.report_only is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if value.readonly is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _status_from_counts(fail_count: int, incomplete_count: int) -> str:
    if fail_count > 0:
        return "blocked_by_risk"
    if incomplete_count > 0:
        return "insufficient_evidence"
    return "audit_ready"
