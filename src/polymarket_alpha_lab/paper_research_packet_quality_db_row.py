"""Pure row codec for persisted paper research packet quality reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_research_packet_quality import (
    PaperResearchPacketQualityCheckRow,
    PaperResearchPacketQualityReasonCodeCount,
    PaperResearchPacketQualityReport,
)


__all__ = (
    "PaperResearchPacketQualityDbRow",
    "paper_research_packet_quality_from_db_row",
    "paper_research_packet_quality_report_from_db_row",
    "paper_research_packet_quality_report_to_db_row",
    "paper_research_packet_quality_to_db_row",
    "from_db_row",
    "to_db_row",
)


ZERO = Decimal("0")
ONE = Decimal("1")
QUANTUM = Decimal("0.000001")
CHECK_NAMES = ("source_freshness", "packet_population", "skip_pressure")
QUALITY_STATUSES = ("pass", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperResearchPacketQualityDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_generated_at: datetime
    source_config_version: str
    input_row_count: int
    packet_row_count: int
    included_count: int
    skipped_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    source_age_seconds: int
    included_share: Decimal | None
    skipped_share: Decimal | None
    check_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    quality_status: str
    check_rows_json: list[dict[str, Any]]
    reason_code_counts_json: list[dict[str, Any]]
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
        object.__setattr__(
            self,
            "source_generated_at",
            _as_utc("source_generated_at", self.source_generated_at),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        if self.source_generated_at > self.generated_at:
            raise ValueError("source_generated_at must not be after generated_at")
        for field_name in (
            "input_row_count",
            "packet_row_count",
            "included_count",
            "skipped_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
            "source_age_seconds",
            "check_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "reason_code_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "included_share",
            _normalize_ratio("included_share", self.included_share),
        )
        object.__setattr__(
            self,
            "skipped_share",
            _normalize_ratio("skipped_share", self.skipped_share),
        )
        _require_quality_status("quality_status", self.quality_status)
        object.__setattr__(
            self,
            "check_rows_json",
            _normalize_check_rows_json("check_rows_json", self.check_rows_json),
        )
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
            "reason_codes_json",
            _normalize_reason_codes_json("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)


def paper_research_packet_quality_to_db_row(
    report: PaperResearchPacketQualityReport,
) -> PaperResearchPacketQualityDbRow:
    if type(report) is not PaperResearchPacketQualityReport:
        raise ValueError("report must be a PaperResearchPacketQualityReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    check_rows_json = list(payload_json["check_rows"])
    reason_code_counts_json = list(payload_json["reason_code_counts"])
    reason_codes_json = [
        item["reason_code"] for item in reason_code_counts_json if isinstance(item, dict)
    ]
    return PaperResearchPacketQualityDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_generated_at=report.source_generated_at,
        source_config_version=report.source_config_version,
        input_row_count=report.input_row_count,
        packet_row_count=report.packet_row_count,
        included_count=report.included_count,
        skipped_count=report.skipped_count,
        high_priority_count=report.high_priority_count,
        medium_priority_count=report.medium_priority_count,
        low_priority_count=report.low_priority_count,
        source_age_seconds=report.source_age_seconds,
        included_share=report.included_share,
        skipped_share=report.skipped_share,
        check_count=report.check_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        quality_status=report.quality_status,
        check_rows_json=check_rows_json,
        reason_code_counts_json=reason_code_counts_json,
        reason_codes_json=reason_codes_json,
        reason_code_count=len(reason_codes_json),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_research_packet_quality_from_db_row(
    row: PaperResearchPacketQualityDbRow,
) -> PaperResearchPacketQualityReport:
    if type(row) is not PaperResearchPacketQualityDbRow:
        raise ValueError("row must be a PaperResearchPacketQualityDbRow")
    _reject_json_floats(row.check_rows_json)
    _reject_json_floats(row.reason_code_counts_json)
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.check_rows_json, "check_rows_json")
    _validate_json_hard_flags(row.reason_code_counts_json, "reason_code_counts_json")
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(
            PaperResearchPacketQualityReport,
            _recover_report_payload_json_values(row.payload_json),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid paper research packet quality report: {exc}",
        ) from exc
    if type(report) is not PaperResearchPacketQualityReport:
        raise ValueError(
            "payload_json must recover a PaperResearchPacketQualityReport",
        )
    _validate_report_tree(report)
    expected_row = paper_research_packet_quality_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperResearchPacketQualityReport,
) -> PaperResearchPacketQualityDbRow:
    return paper_research_packet_quality_to_db_row(report)


def from_db_row(
    row: PaperResearchPacketQualityDbRow,
) -> PaperResearchPacketQualityReport:
    return paper_research_packet_quality_from_db_row(row)


def _validate_report_tree(value: Any, field_name: str = "report") -> None:
    if isinstance(value, PaperResearchPacketQualityReport):
        if type(value) is not PaperResearchPacketQualityReport:
            raise ValueError(f"{field_name} must be a PaperResearchPacketQualityReport")
    elif isinstance(value, PaperResearchPacketQualityCheckRow):
        if type(value) is not PaperResearchPacketQualityCheckRow:
            raise ValueError(f"{field_name} must be a PaperResearchPacketQualityCheckRow")
    elif isinstance(value, PaperResearchPacketQualityReasonCodeCount):
        if type(value) is not PaperResearchPacketQualityReasonCodeCount:
            raise ValueError(
                f"{field_name} must be a PaperResearchPacketQualityReasonCodeCount",
            )
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
    row: PaperResearchPacketQualityDbRow,
    expected: PaperResearchPacketQualityDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "source_generated_at",
        "source_config_version",
        "input_row_count",
        "packet_row_count",
        "included_count",
        "skipped_count",
        "high_priority_count",
        "medium_priority_count",
        "low_priority_count",
        "source_age_seconds",
        "included_share",
        "skipped_share",
        "check_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "quality_status",
        "check_rows_json",
        "reason_code_counts_json",
        "reason_codes_json",
        "reason_code_count",
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
    raise ValueError("paper research packet quality DB row values must be JSON serializable")


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


def _normalize_check_rows_json(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    rows = _normalize_json_object_list(field_name, value)
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(rows):
        _require_json_hard_flags(item, f"{field_name} {index}")
        _validate_json_hard_flags(item, f"{field_name} {index}")
        try:
            row = PaperResearchPacketQualityCheckRow(
                **_recover_check_row_json_values(item),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} contains invalid check rows: {exc}") from exc
        if type(row) is not PaperResearchPacketQualityCheckRow:
            raise ValueError(f"{field_name} must contain quality check rows")
        normalized_item = _json_ready(asdict(row))
        if not isinstance(normalized_item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
        normalized.append(normalized_item)
    if normalized and tuple(item["check_name"] for item in normalized) != CHECK_NAMES:
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _normalize_reason_code_counts_json(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    rows = _normalize_json_object_list(field_name, value)
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(rows):
        _require_json_hard_flags(item, f"{field_name} {index}")
        _validate_json_hard_flags(item, f"{field_name} {index}")
        try:
            row = from_jsonable(PaperResearchPacketQualityReasonCodeCount, item)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{field_name} contains invalid reason count rows: {exc}") from exc
        if type(row) is not PaperResearchPacketQualityReasonCodeCount:
            raise ValueError(f"{field_name} must contain quality reason count rows")
        normalized_item = _json_ready(asdict(row))
        if not isinstance(normalized_item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
        reason_code = normalized_item.get("reason_code")
        if type(reason_code) is not str or reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(reason_code)
        normalized.append(normalized_item)
    return normalized


def _recover_report_payload_json_values(value: dict[str, Any]) -> dict[str, Any]:
    recovered = dict(value)
    for field_name in ("included_share", "skipped_share"):
        if field_name in recovered:
            recovered[field_name] = _recover_optional_decimal_json_value(
                field_name,
                recovered[field_name],
            )
    check_rows = recovered.get("check_rows")
    if isinstance(check_rows, list):
        recovered["check_rows"] = [
            _recover_check_row_json_values(item) if isinstance(item, dict) else item
            for item in check_rows
        ]
    return recovered


def _recover_check_row_json_values(value: dict[str, Any]) -> dict[str, Any]:
    recovered = dict(value)
    for field_name in ("observed_value", "threshold"):
        if field_name in recovered:
            recovered[field_name] = _recover_measure_json_value(
                field_name,
                recovered[field_name],
            )
    return recovered


def _recover_measure_json_value(field_name: str, value: object) -> int | Decimal | None:
    if value is None:
        return None
    if type(value) is int:
        return value
    if type(value) is Decimal:
        return value
    if type(value) is str:
        return _decimal_from_json_string(field_name, value)
    raise ValueError(f"{field_name} must be an int, Decimal, or None")


def _recover_optional_decimal_json_value(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    if type(value) is Decimal:
        return value
    if type(value) is str:
        return _decimal_from_json_string(field_name, value)
    raise ValueError(f"{field_name} must be a Decimal or None")


def _decimal_from_json_string(field_name: str, value: str) -> Decimal:
    try:
        decimal = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal


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


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_quality_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _normalize_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal or None")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(QUANTUM)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if quantized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return quantized


paper_research_packet_quality_report_to_db_row = paper_research_packet_quality_to_db_row
paper_research_packet_quality_report_from_db_row = paper_research_packet_quality_from_db_row
