"""Pure row codec for persisted paper research packet operator-flow reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_research_packet_operator_flow import (
    PaperResearchPacketOperatorFlowReport,
)


__all__ = (
    "PaperResearchPacketOperatorFlowDbRow",
    "paper_research_packet_operator_flow_report_from_db_row",
    "paper_research_packet_operator_flow_report_to_db_row",
    "from_db_row",
    "to_db_row",
)


FLOW_STATUSES = ("pass", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperResearchPacketOperatorFlowDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    flow_status: str
    packet_generated_at: datetime
    packet_config_version: str
    packet_persisted: bool
    packet_row_count: int
    included_count: int
    skipped_count: int
    quality_generated_at: datetime
    quality_config_version: str
    quality_status: str
    quality_persisted: bool
    quality_check_count: int
    quality_pass_count: int
    quality_watch_count: int
    quality_blocked_count: int
    history_generated_at: datetime
    history_config_version: str
    history_status: str
    history_source_report_count: int
    history_latest_quality_status: str
    reason_codes_json: list[str]
    reason_code_count: int
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
        _require_status("flow_status", self.flow_status)
        object.__setattr__(
            self,
            "packet_generated_at",
            _as_utc("packet_generated_at", self.packet_generated_at),
        )
        _require_canonical_string("packet_config_version", self.packet_config_version)
        _require_bool("packet_persisted", self.packet_persisted)
        for field_name in ("packet_row_count", "included_count", "skipped_count"):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "quality_generated_at",
            _as_utc("quality_generated_at", self.quality_generated_at),
        )
        _require_canonical_string("quality_config_version", self.quality_config_version)
        _require_status("quality_status", self.quality_status)
        _require_bool("quality_persisted", self.quality_persisted)
        for field_name in (
            "quality_check_count",
            "quality_pass_count",
            "quality_watch_count",
            "quality_blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "history_generated_at",
            _as_utc("history_generated_at", self.history_generated_at),
        )
        _require_canonical_string("history_config_version", self.history_config_version)
        _require_status("history_status", self.history_status)
        _require_nonnegative_int(
            "history_source_report_count",
            self.history_source_report_count,
        )
        _require_status(
            "history_latest_quality_status",
            self.history_latest_quality_status,
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_reason_codes_json("reason_codes_json", self.reason_codes_json),
        )
        _require_nonnegative_int("reason_code_count", self.reason_code_count)
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _validate_timeline(self)
        _require_hard_flags("DB row", self)
        _validate_row_payload_consistency(self)


def paper_research_packet_operator_flow_report_to_db_row(
    report: PaperResearchPacketOperatorFlowReport,
) -> PaperResearchPacketOperatorFlowDbRow:
    if type(report) is not PaperResearchPacketOperatorFlowReport:
        raise ValueError("report must be a PaperResearchPacketOperatorFlowReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperResearchPacketOperatorFlowDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        flow_status=report.flow_status,
        packet_generated_at=report.packet_generated_at,
        packet_config_version=report.packet_config_version,
        packet_persisted=report.packet_persisted,
        packet_row_count=report.packet_row_count,
        included_count=report.included_count,
        skipped_count=report.skipped_count,
        quality_generated_at=report.quality_generated_at,
        quality_config_version=report.quality_config_version,
        quality_status=report.quality_status,
        quality_persisted=report.quality_persisted,
        quality_check_count=report.quality_check_count,
        quality_pass_count=report.quality_pass_count,
        quality_watch_count=report.quality_watch_count,
        quality_blocked_count=report.quality_blocked_count,
        history_generated_at=report.history_generated_at,
        history_config_version=report.history_config_version,
        history_status=report.history_status,
        history_source_report_count=report.history_source_report_count,
        history_latest_quality_status=report.history_latest_quality_status,
        reason_codes_json=list(report.reason_codes),
        reason_code_count=len(report.reason_codes),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_research_packet_operator_flow_report_from_db_row(
    row: PaperResearchPacketOperatorFlowDbRow,
) -> PaperResearchPacketOperatorFlowReport:
    if type(row) is not PaperResearchPacketOperatorFlowDbRow:
        raise ValueError("row must be a PaperResearchPacketOperatorFlowDbRow")
    _reject_json_floats(row.reason_codes_json)
    _reject_json_floats(row.payload_json)
    report = _report_from_payload_json(row.payload_json)
    _validate_row_matches_payload(row, _expected_row_values_from_report(report))
    return report


def to_db_row(
    report: PaperResearchPacketOperatorFlowReport,
) -> PaperResearchPacketOperatorFlowDbRow:
    return paper_research_packet_operator_flow_report_to_db_row(report)


def from_db_row(
    row: PaperResearchPacketOperatorFlowDbRow,
) -> PaperResearchPacketOperatorFlowReport:
    return paper_research_packet_operator_flow_report_from_db_row(row)


def _validate_report_tree(value: Any, field_name: str = "report") -> None:
    if isinstance(value, PaperResearchPacketOperatorFlowReport):
        if type(value) is not PaperResearchPacketOperatorFlowReport:
            raise ValueError(f"{field_name} must be a PaperResearchPacketOperatorFlowReport")
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
    row: PaperResearchPacketOperatorFlowDbRow,
    expected: dict[str, Any],
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "flow_status",
        "packet_generated_at",
        "packet_config_version",
        "packet_persisted",
        "packet_row_count",
        "included_count",
        "skipped_count",
        "quality_generated_at",
        "quality_config_version",
        "quality_status",
        "quality_persisted",
        "quality_check_count",
        "quality_pass_count",
        "quality_watch_count",
        "quality_blocked_count",
        "history_generated_at",
        "history_config_version",
        "history_status",
        "history_source_report_count",
        "history_latest_quality_status",
        "reason_codes_json",
        "reason_code_count",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if getattr(row, field_name) != expected[field_name]:
            raise ValueError(f"{field_name} must match payload_json")


def _validate_row_payload_consistency(row: PaperResearchPacketOperatorFlowDbRow) -> None:
    report = _report_from_payload_json(row.payload_json)
    _validate_row_matches_payload(row, _expected_row_values_from_report(report))


def _report_from_payload_json(
    payload_json: dict[str, Any],
) -> PaperResearchPacketOperatorFlowReport:
    _reject_json_floats(payload_json)
    _require_json_hard_flags(payload_json, "payload_json")
    _validate_json_hard_flags(payload_json, "payload_json")
    try:
        report = from_jsonable(PaperResearchPacketOperatorFlowReport, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid paper research packet operator-flow report: {exc}",
        ) from exc
    if type(report) is not PaperResearchPacketOperatorFlowReport:
        raise ValueError(
            "payload_json must recover a PaperResearchPacketOperatorFlowReport",
        )
    _validate_report_tree(report)
    return report


def _expected_row_values_from_report(
    report: PaperResearchPacketOperatorFlowReport,
) -> dict[str, Any]:
    payload_json = _json_ready(asdict(report))
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must be a JSON object")
    return {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": _as_utc("generated_at", report.generated_at),
        "config_version": report.config_version,
        "flow_status": report.flow_status,
        "packet_generated_at": _as_utc(
            "packet_generated_at",
            report.packet_generated_at,
        ),
        "packet_config_version": report.packet_config_version,
        "packet_persisted": report.packet_persisted,
        "packet_row_count": report.packet_row_count,
        "included_count": report.included_count,
        "skipped_count": report.skipped_count,
        "quality_generated_at": _as_utc(
            "quality_generated_at",
            report.quality_generated_at,
        ),
        "quality_config_version": report.quality_config_version,
        "quality_status": report.quality_status,
        "quality_persisted": report.quality_persisted,
        "quality_check_count": report.quality_check_count,
        "quality_pass_count": report.quality_pass_count,
        "quality_watch_count": report.quality_watch_count,
        "quality_blocked_count": report.quality_blocked_count,
        "history_generated_at": _as_utc(
            "history_generated_at",
            report.history_generated_at,
        ),
        "history_config_version": report.history_config_version,
        "history_status": report.history_status,
        "history_source_report_count": report.history_source_report_count,
        "history_latest_quality_status": report.history_latest_quality_status,
        "reason_codes_json": list(report.reason_codes),
        "reason_code_count": len(report.reason_codes),
        "payload_json": payload_json,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _validate_timeline(row: PaperResearchPacketOperatorFlowDbRow) -> None:
    if row.packet_generated_at > row.quality_generated_at:
        raise ValueError("packet_generated_at must not be after quality_generated_at")
    if row.quality_generated_at > row.history_generated_at:
        raise ValueError("quality_generated_at must not be after history_generated_at")
    if row.history_generated_at > row.generated_at:
        raise ValueError("history_generated_at must not be after generated_at")


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
    raise ValueError("paper research packet operator-flow DB row values must be JSON serializable")


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


def _normalize_reason_codes_json(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON list")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(item)
        normalized.append(item)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if normalized != sorted(normalized):
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(flag_name in value for flag_name in ("paper_only", "report_only", "readonly")):
        _require_json_hard_flags(value, field_name)
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _require_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    for flag_name in ("paper_only", "report_only", "readonly"):
        if value.get(flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be present and true")


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
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
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in FLOW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
