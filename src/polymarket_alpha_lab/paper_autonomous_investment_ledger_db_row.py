"""Pure row codec for paper autonomous investment ledger reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_autonomous_investment_ledger import (
    PaperAutonomousInvestmentLedgerEntry,
    PaperAutonomousInvestmentLedgerReasonCodeCount,
    PaperAutonomousInvestmentLedgerReport,
)


__all__ = (
    "PaperAutonomousInvestmentLedgerDbRow",
    "from_db_row",
    "paper_autonomous_investment_ledger_from_db_row",
    "paper_autonomous_investment_ledger_report_from_db_row",
    "paper_autonomous_investment_ledger_report_to_db_row",
    "paper_autonomous_investment_ledger_to_db_row",
    "to_db_row",
)


_LEDGER_STATUSES = ("pass", "watch", "blocked")
_SHA256_PATTERN = r"^[a-f0-9]{64}$"


@dataclass(frozen=True)
class PaperAutonomousInvestmentLedgerDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    ledger_status: str
    recommended_next_step: str
    source_record_count: int
    submitted_count: int
    held_count: int
    blocked_count: int
    total_submitted_notional: Decimal
    held_zero_notional_count: int
    blocked_zero_notional_count: int
    latest_generated_at: datetime | None
    latest_age_seconds: int | None
    reason_code_counts_json: list[dict[str, Any]]
    entries_json: list[dict[str, Any]]
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_ledger_status("ledger_status", self.ledger_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "source_record_count",
            "submitted_count",
            "held_count",
            "blocked_count",
            "held_zero_notional_count",
            "blocked_zero_notional_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "total_submitted_notional",
            _require_nonnegative_decimal(
                "total_submitted_notional",
                self.total_submitted_notional,
            ),
        )
        _require_optional_nonnegative_int("latest_age_seconds", self.latest_age_seconds)
        object.__setattr__(
            self,
            "reason_code_counts_json",
            _normalize_reason_code_counts_json(
                "reason_code_counts_json",
                self.reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "entries_json",
            _normalize_entries_json("entries_json", self.entries_json),
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
        _require_hard_flags("DB row", self)


def paper_autonomous_investment_ledger_to_db_row(
    report: PaperAutonomousInvestmentLedgerReport,
) -> PaperAutonomousInvestmentLedgerDbRow:
    if type(report) is not PaperAutonomousInvestmentLedgerReport:
        raise ValueError("report must be a PaperAutonomousInvestmentLedgerReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    reason_code_counts_json = payload_json.get("reason_code_counts")
    entries_json = payload_json.get("entries")
    reason_codes_json = payload_json.get("reason_codes")
    if not isinstance(reason_code_counts_json, list):
        raise ValueError("payload_json reason_code_counts must be a JSON array")
    if not isinstance(entries_json, list):
        raise ValueError("payload_json entries must be a JSON array")
    if not isinstance(reason_codes_json, list):
        raise ValueError("payload_json reason_codes must be a JSON array")
    return PaperAutonomousInvestmentLedgerDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        ledger_status=report.ledger_status,
        recommended_next_step=report.recommended_next_step,
        source_record_count=report.source_record_count,
        submitted_count=report.submitted_count,
        held_count=report.held_count,
        blocked_count=report.blocked_count,
        total_submitted_notional=report.total_submitted_notional,
        held_zero_notional_count=report.held_zero_notional_count,
        blocked_zero_notional_count=report.blocked_zero_notional_count,
        latest_generated_at=report.latest_generated_at,
        latest_age_seconds=report.latest_age_seconds,
        reason_code_counts_json=reason_code_counts_json,
        entries_json=entries_json,
        reason_codes_json=reason_codes_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_autonomous_investment_ledger_from_db_row(
    row: PaperAutonomousInvestmentLedgerDbRow,
) -> PaperAutonomousInvestmentLedgerReport:
    if type(row) is not PaperAutonomousInvestmentLedgerDbRow:
        raise ValueError("row must be a PaperAutonomousInvestmentLedgerDbRow")
    _reject_json_floats(row.reason_code_counts_json)
    _reject_json_floats(row.entries_json)
    _reject_json_floats(row.reason_codes_json)
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperAutonomousInvestmentLedgerReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid investment ledger report: {exc}",
        ) from exc
    if type(report) is not PaperAutonomousInvestmentLedgerReport:
        raise ValueError(
            "payload_json must recover a PaperAutonomousInvestmentLedgerReport",
        )
    _validate_report_tree(report)
    expected_row = paper_autonomous_investment_ledger_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperAutonomousInvestmentLedgerReport,
) -> PaperAutonomousInvestmentLedgerDbRow:
    return paper_autonomous_investment_ledger_to_db_row(report)


def from_db_row(
    row: PaperAutonomousInvestmentLedgerDbRow,
) -> PaperAutonomousInvestmentLedgerReport:
    return paper_autonomous_investment_ledger_from_db_row(row)


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
    row: PaperAutonomousInvestmentLedgerDbRow,
    expected: PaperAutonomousInvestmentLedgerDbRow,
) -> None:
    for field_name in _MATERIALIZED_FIELDS:
        if getattr(row, field_name) != getattr(expected, field_name):
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
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("investment ledger DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
        normalized = _json_ready(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_reason_code_counts_json(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    return _normalize_dataclass_json_objects(
        field_name,
        value,
        PaperAutonomousInvestmentLedgerReasonCodeCount,
        "ledger reason code count rows",
    )


def _normalize_entries_json(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    return _normalize_dataclass_json_objects(
        field_name,
        value,
        PaperAutonomousInvestmentLedgerEntry,
        "ledger entries",
    )


def _normalize_dataclass_json_objects(
    field_name: str,
    value: object,
    row_type: type,
    label: str,
) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
        _validate_json_hard_flags(item, field_name)
        try:
            recovered = from_jsonable(row_type, item)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} {exc}") from exc
        if type(recovered) is not row_type:
            raise ValueError(f"{field_name} must contain {label}")
        normalized_item = _json_ready(asdict(recovered))
        if not isinstance(normalized_item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
        normalized.append(normalized_item)
    return normalized


def _normalize_string_list(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    normalized: list[str] = []
    previous: str | None = None
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(f"{field_name} entry", item)
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
        raise ValueError("JSON value must not be a float")
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


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or re.fullmatch(_SHA256_PATTERN, value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_ledger_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _LEDGER_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if isinstance(value, bool) or type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return value


_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "ledger_status",
    "recommended_next_step",
    "source_record_count",
    "submitted_count",
    "held_count",
    "blocked_count",
    "total_submitted_notional",
    "held_zero_notional_count",
    "blocked_zero_notional_count",
    "latest_generated_at",
    "latest_age_seconds",
    "reason_code_counts_json",
    "entries_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


paper_autonomous_investment_ledger_report_to_db_row = (
    paper_autonomous_investment_ledger_to_db_row
)
paper_autonomous_investment_ledger_report_from_db_row = (
    paper_autonomous_investment_ledger_from_db_row
)
