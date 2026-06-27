"""Pure row codec for persisted paper probability selection summary history reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_probability_selection_summary_history import (
    HISTORY_STATUSES,
    RECOMMENDED_NEXT_STEPS,
    PaperProbabilitySelectionSummaryHistoryReport,
)


__all__ = (
    "PaperProbabilitySelectionSummaryHistoryDbRow",
    "paper_probability_selection_summary_history_from_db_row",
    "paper_probability_selection_summary_history_report_from_db_row",
    "paper_probability_selection_summary_history_report_to_db_row",
    "paper_probability_selection_summary_history_to_db_row",
    "from_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_SHARE_PAYLOAD_PATHS = frozenset(
    {
        ("latest_selected_share",),
        ("average_selected_share",),
    },
)


@dataclass(frozen=True)
class PaperProbabilitySelectionSummaryHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_report_count: int
    latest_generated_at: datetime | None
    latest_age_seconds: int | None
    latest_queue_count: int
    latest_selected_count: int
    latest_selected_share: Decimal
    average_selected_share: Decimal
    history_status: str
    recommended_next_step: str
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
        for field_name in (
            "source_report_count",
            "latest_queue_count",
            "latest_selected_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_generated_at",
            _normalize_optional_datetime("latest_generated_at", self.latest_generated_at),
        )
        _require_optional_nonnegative_int("latest_age_seconds", self.latest_age_seconds)
        object.__setattr__(
            self,
            "latest_selected_share",
            _normalize_probability("latest_selected_share", self.latest_selected_share),
        )
        object.__setattr__(
            self,
            "average_selected_share",
            _normalize_probability("average_selected_share", self.average_selected_share),
        )
        _require_history_status("history_status", self.history_status)
        _require_recommended_next_step(
            "recommended_next_step",
            self.recommended_next_step,
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
        _validate_constructor_payload_consistency(self)


def paper_probability_selection_summary_history_to_db_row(
    report: PaperProbabilitySelectionSummaryHistoryReport,
) -> PaperProbabilitySelectionSummaryHistoryDbRow:
    if type(report) is not PaperProbabilitySelectionSummaryHistoryReport:
        raise ValueError("report must be a PaperProbabilitySelectionSummaryHistoryReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperProbabilitySelectionSummaryHistoryDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_report_count=report.source_report_count,
        latest_generated_at=report.latest_generated_at,
        latest_age_seconds=report.latest_age_seconds,
        latest_queue_count=report.latest_queue_count,
        latest_selected_count=report.latest_selected_count,
        latest_selected_share=report.latest_selected_share,
        average_selected_share=report.average_selected_share,
        history_status=report.history_status,
        recommended_next_step=report.recommended_next_step,
        reason_codes_json=list(payload_json["reason_codes"]),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def paper_probability_selection_summary_history_from_db_row(
    row: PaperProbabilitySelectionSummaryHistoryDbRow,
) -> PaperProbabilitySelectionSummaryHistoryReport:
    if type(row) is not PaperProbabilitySelectionSummaryHistoryDbRow:
        raise ValueError("row must be a PaperProbabilitySelectionSummaryHistoryDbRow")
    _validate_row_core_fields(row)
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    if row.report_sha256 != _report_sha256(payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(payload_json, "payload_json")
    normalized_payload_json = _normalize_legacy_share_payload(payload_json)
    try:
        report = from_jsonable(
            PaperProbabilitySelectionSummaryHistoryReport,
            normalized_payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid selection summary history report: {exc}",
        ) from exc
    if type(report) is not PaperProbabilitySelectionSummaryHistoryReport:
        raise ValueError(
            "payload_json must recover a PaperProbabilitySelectionSummaryHistoryReport",
        )
    _validate_report_tree(report)
    expected_row = paper_probability_selection_summary_history_to_db_row(report)
    _validate_row_matches_payload(row, expected_row, normalized_payload_json)
    return report


def to_db_row(
    report: PaperProbabilitySelectionSummaryHistoryReport,
) -> PaperProbabilitySelectionSummaryHistoryDbRow:
    return paper_probability_selection_summary_history_to_db_row(report)


def from_db_row(
    row: PaperProbabilitySelectionSummaryHistoryDbRow,
) -> PaperProbabilitySelectionSummaryHistoryReport:
    return paper_probability_selection_summary_history_from_db_row(row)


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
    row: PaperProbabilitySelectionSummaryHistoryDbRow,
    expected: PaperProbabilitySelectionSummaryHistoryDbRow,
    normalized_payload_json: dict[str, Any] | None = None,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "source_report_count",
        "latest_generated_at",
        "latest_age_seconds",
        "latest_queue_count",
        "latest_selected_count",
        "latest_selected_share",
        "average_selected_share",
        "history_status",
        "recommended_next_step",
        "reason_codes_json",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        actual_value = getattr(row, field_name)
        expected_value = getattr(expected, field_name)
        if field_name == "report_sha256" and normalized_payload_json is not None:
            continue
        if field_name == "payload_json" and normalized_payload_json is not None:
            actual_value = normalized_payload_json
        if type(actual_value) is not type(expected_value) or actual_value != expected_value:
            raise ValueError(f"{field_name} must match payload_json")


def _validate_constructor_payload_consistency(
    row: PaperProbabilitySelectionSummaryHistoryDbRow,
) -> None:
    _validate_json_hard_flags(row.payload_json, "payload_json")
    for flag_name in ("paper_only", "report_only", "readonly"):
        _require_payload_value(row.payload_json, flag_name, getattr(row, flag_name))
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    for field_name in (
        "generated_at",
        "config_version",
        "source_report_count",
        "latest_generated_at",
        "latest_age_seconds",
        "latest_queue_count",
        "latest_selected_count",
        "latest_selected_share",
        "average_selected_share",
        "history_status",
        "recommended_next_step",
    ):
        _require_payload_value(row.payload_json, field_name, getattr(row, field_name))
    _require_payload_value(
        row.payload_json,
        "reason_codes",
        row.reason_codes_json,
        row_field_name="reason_codes_json",
    )
    _validate_payload_recovers_to_compatible_report(row.payload_json)


def _validate_row_core_fields(
    row: PaperProbabilitySelectionSummaryHistoryDbRow,
) -> None:
    _require_sha256("report_sha256", row.report_sha256)
    _as_utc("generated_at", row.generated_at)
    _require_canonical_string("config_version", row.config_version)
    for field_name in (
        "source_report_count",
        "latest_queue_count",
        "latest_selected_count",
    ):
        _require_nonnegative_int(field_name, getattr(row, field_name))
    _normalize_optional_datetime("latest_generated_at", row.latest_generated_at)
    _require_optional_nonnegative_int("latest_age_seconds", row.latest_age_seconds)
    _normalize_probability("latest_selected_share", row.latest_selected_share)
    _normalize_probability("average_selected_share", row.average_selected_share)
    _require_history_status("history_status", row.history_status)
    _require_recommended_next_step(
        "recommended_next_step",
        row.recommended_next_step,
    )
    _normalize_string_list("reason_codes_json", row.reason_codes_json)
    _require_hard_flags("DB row", row)


def _validate_payload_recovers_to_compatible_report(
    payload_json: dict[str, Any],
) -> PaperProbabilitySelectionSummaryHistoryReport:
    normalized_payload_json = _normalize_legacy_share_payload(payload_json)
    try:
        report = from_jsonable(
            PaperProbabilitySelectionSummaryHistoryReport,
            normalized_payload_json,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid selection summary history report: {exc}",
        ) from exc
    if type(report) is not PaperProbabilitySelectionSummaryHistoryReport:
        raise ValueError(
            "payload_json must recover a PaperProbabilitySelectionSummaryHistoryReport",
        )
    _validate_report_tree(report)
    _validate_payload_compatible_with_canonical_payload(
        payload_json,
        _canonical_report_payload(report),
    )
    return report


def _canonical_report_payload(
    report: PaperProbabilitySelectionSummaryHistoryReport,
) -> dict[str, Any]:
    payload_json = _json_ready(asdict(report))
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must recover a JSON object")
    return payload_json


def _require_payload_value(
    payload_json: dict[str, Any],
    payload_field_name: str,
    value: Any,
    *,
    row_field_name: str | None = None,
) -> None:
    field_name = row_field_name or payload_field_name
    if payload_field_name not in payload_json:
        raise ValueError(f"{field_name} must match payload_json")
    payload_value = payload_json[payload_field_name]
    if (payload_field_name,) in _SHARE_PAYLOAD_PATHS:
        _require_payload_share_value(field_name, payload_value, value)
        return
    if payload_value != _json_ready(value, (payload_field_name,)):
        raise ValueError(f"{field_name} must match payload_json")


def _require_payload_share_value(
    field_name: str,
    payload_value: object,
    row_value: object,
) -> None:
    if type(row_value) is not Decimal or type(payload_value) is not str:
        raise ValueError(f"{field_name} must match payload_json")
    try:
        payload_decimal = Decimal(payload_value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must match payload_json") from exc
    if not payload_decimal.is_finite() or payload_decimal != row_value:
        raise ValueError(f"{field_name} must match payload_json")
    _decimal_to_six_place_string(field_name, payload_decimal)


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any, path: tuple[object, ...] = ()) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), path)
    if isinstance(value, Decimal):
        if path not in _SHARE_PAYLOAD_PATHS:
            raise ValueError(f"{_payload_path_name(path)} is not a Decimal payload path")
        return _decimal_to_six_place_string(_payload_path_name(path), value)
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
        return {key: _json_ready(item, (*path, key)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item, (*path, index)) for index, item in enumerate(value)]
    raise ValueError("selection summary history DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _validate_json_payload_value(field_name, value)
        normalized = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _validate_json_payload_value(field_name: str, value: object) -> None:
    if value is None:
        return
    if type(value) in (str, int, bool):
        return
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not contain floats")
    if isinstance(value, (Decimal, datetime)):
        raise ValueError(f"{field_name} must contain only raw JSON values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} object keys must be strings")
            _validate_json_payload_value(f"{field_name} {key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_payload_value(f"{field_name} {index}", item)
        return
    raise ValueError(f"{field_name} must contain only raw JSON values")


def _copy_json_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _copy_json_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_json_payload(item) for item in value]
    return value


def _normalize_legacy_share_payload(
    value: Any,
    path: tuple[object, ...] = (),
) -> Any:
    if path in _SHARE_PAYLOAD_PATHS:
        if type(value) is not str:
            raise ValueError(f"{_payload_path_name(path)} must be a Decimal string")
        return _decimal_string_to_six_place(_payload_path_name(path), value)
    if isinstance(value, dict):
        return {
            key: _normalize_legacy_share_payload(item, (*path, key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _normalize_legacy_share_payload(item, (*path, index))
            for index, item in enumerate(value)
        ]
    return value


def _decimal_string_to_six_place(field_name: str, value: str) -> str:
    _require_canonical_string(field_name, value)
    try:
        decimal = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _decimal_to_six_place_string(field_name, decimal)


def _decimal_to_six_place_string(field_name: str, value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError(f"{field_name} Decimal value must be finite")
    try:
        with localcontext() as context:
            integer_digits = max(value.adjusted() + 1, 1)
            context.prec = max(28, integer_digits + 6)
            quantized = value.quantize(_DECIMAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must have at most six decimal places") from exc
    if quantized != value:
        raise ValueError(f"{field_name} must have at most six decimal places")
    return format(quantized, "f")


def _validate_payload_compatible_with_canonical_payload(
    payload_json: dict[str, Any],
    expected_payload_json: dict[str, Any],
) -> None:
    try:
        _validate_json_compatible((), payload_json, expected_payload_json)
    except ValueError as exc:
        raise ValueError(
            "payload_json must match canonical selection summary history report: "
            f"{exc}",
        ) from exc


def _validate_json_compatible(
    path: tuple[object, ...],
    actual: object,
    expected: object,
) -> None:
    if path in _SHARE_PAYLOAD_PATHS:
        _validate_compatible_share_path(_payload_path_name(path), actual, expected)
        return
    if type(actual) is not type(expected):
        raise ValueError(f"{_payload_path_name(path)} has wrong JSON type")
    if isinstance(actual, dict):
        if actual.keys() != expected.keys():  # type: ignore[union-attr]
            raise ValueError(f"{_payload_path_name(path)} keys differ")
        for key in actual:
            _validate_json_compatible(
                (*path, key),
                actual[key],
                expected[key],  # type: ignore[index]
            )
        return
    if isinstance(actual, list):
        if len(actual) != len(expected):  # type: ignore[arg-type]
            raise ValueError(f"{_payload_path_name(path)} length differs")
        for index, item in enumerate(actual):
            _validate_json_compatible(
                (*path, index),
                item,
                expected[index],  # type: ignore[index]
            )
        return
    if actual != expected:
        raise ValueError(f"{_payload_path_name(path)} differs")


def _validate_compatible_share_path(
    field_name: str,
    actual: object,
    expected: object,
) -> None:
    if type(actual) is not str or type(expected) is not str:
        raise ValueError(f"{field_name} has wrong JSON type")
    actual_normalized = _decimal_string_to_six_place(field_name, actual)
    expected_normalized = _decimal_string_to_six_place(field_name, expected)
    if actual_normalized != expected_normalized:
        raise ValueError(f"{field_name} differs")


def _payload_path_name(path: tuple[object, ...]) -> str:
    if not path:
        return "payload_json"
    return "payload_json " + " ".join(str(item) for item in path)


def _normalize_string_list(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON list")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
    normalized: list[str] = []
    for item in value:
        _require_canonical_string(field_name, item)
        normalized.append(item)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
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


def _normalize_optional_datetime(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal > Decimal("1"):
        raise ValueError(f"{field_name} must be at most one")
    return decimal


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_history_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in HISTORY_STATUSES:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_recommended_next_step(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RECOMMENDED_NEXT_STEPS:
        raise ValueError(f"{field_name} must be a known next step")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_int(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_int(field_name, value)


paper_probability_selection_summary_history_report_to_db_row = (
    paper_probability_selection_summary_history_to_db_row
)
paper_probability_selection_summary_history_report_from_db_row = (
    paper_probability_selection_summary_history_from_db_row
)
