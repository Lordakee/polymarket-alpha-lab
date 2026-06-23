"""Pure row codec for persisted paper research packet reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_research_packet import (
    PaperResearchPacketReport,
    PaperResearchPacketRow,
)


__all__ = (
    "PaperResearchPacketDbRow",
    "paper_research_packet_from_db_row",
    "paper_research_packet_report_from_db_row",
    "paper_research_packet_report_to_db_row",
    "paper_research_packet_to_db_row",
    "from_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperResearchPacketDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    input_row_count: int
    packet_row_count: int
    included_count: int
    skipped_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    packet_rows_json: list[dict[str, Any]]
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
        for field_name in (
            "input_row_count",
            "packet_row_count",
            "included_count",
            "skipped_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "packet_rows_json",
            _normalize_packet_rows_json(
                "packet_rows_json",
                self.packet_rows_json,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)


def paper_research_packet_to_db_row(
    report: PaperResearchPacketReport,
) -> PaperResearchPacketDbRow:
    if type(report) is not PaperResearchPacketReport:
        raise ValueError("report must be a PaperResearchPacketReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperResearchPacketDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        input_row_count=report.input_row_count,
        packet_row_count=report.packet_row_count,
        included_count=report.included_count,
        skipped_count=report.skipped_count,
        high_priority_count=report.high_priority_count,
        medium_priority_count=report.medium_priority_count,
        low_priority_count=report.low_priority_count,
        packet_rows_json=list(payload_json["packet_rows"]),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_research_packet_from_db_row(
    row: PaperResearchPacketDbRow,
) -> PaperResearchPacketReport:
    if type(row) is not PaperResearchPacketDbRow:
        raise ValueError("row must be a PaperResearchPacketDbRow")
    _reject_json_floats(row.payload_json)
    _validate_payload_json_hard_flags(row.payload_json)
    _validate_packet_rows_json_hard_flags(row.packet_rows_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperResearchPacketReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid paper research packet report: {exc}",
        ) from exc
    if type(report) is not PaperResearchPacketReport:
        raise ValueError("payload_json must recover a PaperResearchPacketReport")
    _validate_report_tree(report)
    expected_row = paper_research_packet_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(report: PaperResearchPacketReport) -> PaperResearchPacketDbRow:
    return paper_research_packet_to_db_row(report)


def from_db_row(row: PaperResearchPacketDbRow) -> PaperResearchPacketReport:
    return paper_research_packet_from_db_row(row)


def _validate_report_tree(value: Any, field_name: str = "report") -> None:
    if isinstance(value, PaperResearchPacketReport):
        if type(value) is not PaperResearchPacketReport:
            raise ValueError(f"{field_name} must be a PaperResearchPacketReport")
    elif isinstance(value, PaperResearchPacketRow):
        if type(value) is not PaperResearchPacketRow:
            raise ValueError(f"{field_name} must be a PaperResearchPacketRow")
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
    row: PaperResearchPacketDbRow,
    expected: PaperResearchPacketDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "input_row_count",
        "packet_row_count",
        "included_count",
        "skipped_count",
        "high_priority_count",
        "medium_priority_count",
        "low_priority_count",
        "packet_rows_json",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
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
    raise ValueError("paper research packet DB row values must be JSON serializable")


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


def _normalize_json_object_list(field_name: str, value: object) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON list")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
        normalized.append(_normalize_json_object(field_name, item))
    return normalized


def _normalize_packet_rows_json(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    rows = _normalize_json_object_list(field_name, value)
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(rows):
        _require_json_hard_flags(item, f"{field_name} {index}")
        _validate_json_hard_flags(item, f"{field_name} {index}")
        try:
            packet_row = from_jsonable(PaperResearchPacketRow, item)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} contains invalid packet rows: {exc}") from exc
        if type(packet_row) is not PaperResearchPacketRow:
            raise ValueError(f"{field_name} must contain paper research packet rows")
        normalized_item = _json_ready(asdict(packet_row))
        if not isinstance(normalized_item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
        normalized.append(normalized_item)
    return normalized


def _validate_payload_json_hard_flags(value: Any) -> None:
    _require_json_hard_flags(value, "payload_json")
    packet_rows = value.get("packet_rows")
    if not isinstance(packet_rows, list):
        raise ValueError("payload_json packet_rows must be a JSON list")
    for index, item in enumerate(packet_rows):
        _require_json_hard_flags(item, f"payload_json packet_rows {index}")


def _validate_packet_rows_json_hard_flags(value: Any) -> None:
    if not isinstance(value, list):
        raise ValueError("packet_rows_json must be a JSON list")
    for index, item in enumerate(value):
        _require_json_hard_flags(item, f"packet_rows_json {index}")


def _require_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    for flag_name in ("paper_only", "report_only", "readonly"):
        if value.get(flag_name) is not True:
            raise ValueError(f"{field_name} {flag_name} must be present and true")


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


paper_research_packet_report_to_db_row = paper_research_packet_to_db_row
paper_research_packet_report_from_db_row = paper_research_packet_from_db_row
