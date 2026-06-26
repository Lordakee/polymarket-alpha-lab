"""Pure row codec for paper autonomous allocation proposal DB-history health reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    HEALTH_STATUSES,
    NEXT_STEP_BY_STATUS,
    PaperAutonomousAllocationProposalDbHistoryHealthReport,
)


__all__ = (
    "PaperAutonomousAllocationProposalDbHistoryHealthDbRow",
    "from_db_row",
    "paper_autonomous_allocation_proposal_db_history_health_report_from_db_row",
    "paper_autonomous_allocation_proposal_db_history_health_report_to_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_MISSING = object()


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalDbHistoryHealthDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    health_status: str
    recommended_next_step: str
    history_report_count: int
    pass_report_count: int
    watch_report_count: int
    blocked_report_count: int
    latest_history_status: str | None
    latest_proposal_status: str | None
    latest_allocated_count: int | None
    latest_total_allocated_paper_notional: Decimal | None
    max_source_age_seconds: int | None
    latest_source_age_seconds: int | None
    duplicate_latest_report_generated_at_count: int
    reason_code_counts_json: list[dict[str, Any]]
    reason_codes_json: list[str]
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
        _require_health_status("health_status", self.health_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        _require_status_next_step(self.health_status, self.recommended_next_step)
        for field_name in (
            "history_report_count",
            "pass_report_count",
            "watch_report_count",
            "blocked_report_count",
            "duplicate_latest_report_generated_at_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        if self.history_report_count != (
            self.pass_report_count + self.watch_report_count + self.blocked_report_count
        ):
            raise ValueError("history_report_count must equal status counts")
        if self.latest_history_status is not None:
            _require_health_status("latest_history_status", self.latest_history_status)
        if self.latest_proposal_status is not None:
            _require_health_status("latest_proposal_status", self.latest_proposal_status)
        _require_optional_nonnegative_int(
            "latest_allocated_count",
            self.latest_allocated_count,
        )
        object.__setattr__(
            self,
            "latest_total_allocated_paper_notional",
            _require_optional_nonnegative_decimal(
                "latest_total_allocated_paper_notional",
                self.latest_total_allocated_paper_notional,
            ),
        )
        _require_optional_nonnegative_int(
            "max_source_age_seconds",
            self.max_source_age_seconds,
        )
        _require_optional_nonnegative_int(
            "latest_source_age_seconds",
            self.latest_source_age_seconds,
        )
        object.__setattr__(
            self,
            "reason_code_counts_json",
            _normalize_json_object_array(
                "reason_code_counts_json",
                self.reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_list("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB-history health DB row", self)
        _validate_row_payload_consistency(self)
        _validate_payload_recovers_to_canonical_report(self.payload_json)


def paper_autonomous_allocation_proposal_db_history_health_report_to_db_row(
    report: Any,
) -> PaperAutonomousAllocationProposalDbHistoryHealthDbRow:
    if type(report) is not PaperAutonomousAllocationProposalDbHistoryHealthReport:
        raise ValueError(
            "report must be a "
            "PaperAutonomousAllocationProposalDbHistoryHealthReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    reason_codes_json = payload_json.get("reason_codes")
    reason_code_counts_json = payload_json.get("reason_code_counts")
    if not isinstance(reason_codes_json, list):
        raise ValueError("payload_json reason_codes must be a JSON array")
    if not isinstance(reason_code_counts_json, list):
        raise ValueError("payload_json reason_code_counts must be a JSON array")
    return PaperAutonomousAllocationProposalDbHistoryHealthDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        health_status=report.health_status,
        recommended_next_step=report.recommended_next_step,
        history_report_count=report.history_report_count,
        pass_report_count=report.pass_report_count,
        watch_report_count=report.watch_report_count,
        blocked_report_count=report.blocked_report_count,
        latest_history_status=report.latest_history_status,
        latest_proposal_status=report.latest_proposal_status,
        latest_allocated_count=report.latest_allocated_count,
        latest_total_allocated_paper_notional=(
            report.latest_total_allocated_paper_notional
        ),
        max_source_age_seconds=report.max_source_age_seconds,
        latest_source_age_seconds=report.latest_source_age_seconds,
        duplicate_latest_report_generated_at_count=(
            report.duplicate_latest_report_generated_at_count
        ),
        reason_code_counts_json=reason_code_counts_json,
        reason_codes_json=reason_codes_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_allocation_proposal_db_history_health_report_from_db_row(
    row: PaperAutonomousAllocationProposalDbHistoryHealthDbRow,
) -> PaperAutonomousAllocationProposalDbHistoryHealthReport:
    if type(row) is not PaperAutonomousAllocationProposalDbHistoryHealthDbRow:
        raise ValueError(
            "row must be a PaperAutonomousAllocationProposalDbHistoryHealthDbRow",
        )
    _validate_row_payload_consistency(row)
    try:
        report = from_jsonable(
            PaperAutonomousAllocationProposalDbHistoryHealthReport,
            row.payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid DB-history health report: " f"{exc}",
        ) from exc
    if type(report) is not PaperAutonomousAllocationProposalDbHistoryHealthReport:
        raise ValueError(
            "payload_json must recover a "
            "PaperAutonomousAllocationProposalDbHistoryHealthReport",
        )
    _validate_report_tree(report)
    _validate_payload_recovers_to_canonical_report(row.payload_json)
    expected_row = (
        paper_autonomous_allocation_proposal_db_history_health_report_to_db_row(
            report,
        )
    )
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(report: Any) -> PaperAutonomousAllocationProposalDbHistoryHealthDbRow:
    return paper_autonomous_allocation_proposal_db_history_health_report_to_db_row(
        report,
    )


def from_db_row(
    row: PaperAutonomousAllocationProposalDbHistoryHealthDbRow,
) -> PaperAutonomousAllocationProposalDbHistoryHealthReport:
    return paper_autonomous_allocation_proposal_db_history_health_report_from_db_row(
        row,
    )


def _validate_report_tree(value: Any, field_name: str = "report") -> None:
    if _has_hard_flag(value):
        _require_hard_flags(field_name, value)
    if is_dataclass(value) and not isinstance(value, type):
        for item_field in fields(value):
            _validate_report_tree(
                getattr(value, item_field.name),
                f"{field_name}.{item_field.name}",
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_report_tree(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_report_tree(item, f"{field_name}.{index}")


def _validate_row_matches_payload(
    row: PaperAutonomousAllocationProposalDbHistoryHealthDbRow,
    expected: PaperAutonomousAllocationProposalDbHistoryHealthDbRow,
) -> None:
    for field_name in _MATERIALIZED_FIELDS:
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_payload_consistency(
    row: PaperAutonomousAllocationProposalDbHistoryHealthDbRow,
) -> None:
    _reject_json_floats(row.reason_code_counts_json)
    _reject_json_floats(row.reason_codes_json)
    _reject_json_floats(row.payload_json)
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_required_json_hard_flags_array(
        "reason_code_counts_json",
        row.reason_code_counts_json,
    )
    for field_name in _ROOT_PAYLOAD_FIELDS:
        _validate_row_field_matches_payload(
            field_name,
            getattr(row, field_name),
            row.payload_json[field_name]
            if field_name in row.payload_json
            else _MISSING,
        )
    _validate_row_field_matches_payload(
        "reason_codes_json",
        row.reason_codes_json,
        row.payload_json.get("reason_codes"),
    )
    _validate_row_field_matches_payload(
        "reason_code_counts_json",
        row.reason_code_counts_json,
        row.payload_json.get("reason_code_counts"),
    )
    for field_name in ("paper_only", "report_only", "readonly"):
        _validate_row_field_matches_payload(
            field_name,
            getattr(row, field_name),
            row.payload_json.get(field_name),
        )


def _validate_row_field_matches_payload(
    field_name: str,
    row_value: Any,
    payload_value: Any,
) -> None:
    if _json_ready(row_value) != payload_value:
        raise ValueError(f"{field_name} must match payload_json")


def _validate_required_json_hard_flags_array(
    field_name: str,
    value: object,
) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    for index, item in enumerate(value):
        _require_json_hard_flags(f"{field_name} {index}", item)


def _require_json_hard_flags(field_name: str, value: object) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    for flag_name in ("paper_only", "report_only", "readonly"):
        if value.get(flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be present and true")


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
        return format(value.quantize(_DECIMAL_QUANTUM), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("DB-history health DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_json_object_array(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    normalized = _json_ready(value)
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON array")
    for item in normalized:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
    return normalized


def _normalize_string_list(field_name: str, value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    previous: str | None = None
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > item:
            raise ValueError(f"{field_name} must be sorted")
        normalized.append(item)
        seen.add(item)
        previous = item
    if not normalized:
        raise ValueError(f"{field_name} must contain at least one value")
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(flag_name in value for flag_name in ("paper_only", "report_only", "readonly")):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_floats(item)


def _has_hard_flag(value: Any) -> bool:
    return any(
        hasattr(value, flag_name)
        for flag_name in ("paper_only", "report_only", "readonly")
    )


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_health_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HEALTH_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_status_next_step(status: str, next_step: str) -> None:
    expected = NEXT_STEP_BY_STATUS[status]
    if next_step != expected:
        raise ValueError("recommended_next_step must match health_status")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _validate_payload_recovers_to_canonical_report(
    payload_json: dict[str, Any],
) -> None:
    try:
        report = from_jsonable(
            PaperAutonomousAllocationProposalDbHistoryHealthReport,
            payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid DB-history health report: " f"{exc}",
        ) from exc
    if type(report) is not PaperAutonomousAllocationProposalDbHistoryHealthReport:
        raise ValueError(
            "payload_json must recover a "
            "PaperAutonomousAllocationProposalDbHistoryHealthReport",
        )
    _validate_report_tree(report)
    if payload_json != _json_ready(asdict(report)):
        raise ValueError("payload_json must match canonical recovered report payload")


_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "health_status",
    "recommended_next_step",
    "history_report_count",
    "pass_report_count",
    "watch_report_count",
    "blocked_report_count",
    "latest_history_status",
    "latest_proposal_status",
    "latest_allocated_count",
    "latest_total_allocated_paper_notional",
    "max_source_age_seconds",
    "latest_source_age_seconds",
    "duplicate_latest_report_generated_at_count",
    "reason_code_counts_json",
    "reason_codes_json",
    "paper_only",
    "report_only",
    "readonly",
)


_ROOT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "health_status",
    "recommended_next_step",
    "history_report_count",
    "pass_report_count",
    "watch_report_count",
    "blocked_report_count",
    "latest_history_status",
    "latest_proposal_status",
    "latest_allocated_count",
    "latest_total_allocated_paper_notional",
    "max_source_age_seconds",
    "latest_source_age_seconds",
    "duplicate_latest_report_generated_at_count",
)
