"""Pure row codec for persisted paper probability recommendation queue reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.paper_probability_recommendation_queue import (
    PaperProbabilityRecommendationQueueReport,
)


__all__ = (
    "PaperProbabilityRecommendationQueueDbRow",
    "from_db_row",
    "paper_probability_recommendation_queue_report_from_db_row",
    "paper_probability_recommendation_queue_report_to_db_row",
    "to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_QUEUE_DECIMAL_PAYLOAD_FIELDS = frozenset(
    (
        "recommendation_score",
        "net_probability_edge",
        "total_cost_per_share",
        "executable_paper_shares",
    ),
)


@dataclass(frozen=True)
class PaperProbabilityRecommendationQueueDbRow:
    report_sha256: str
    generated_at: datetime
    source_config_version: str
    input_count: int
    queue_count: int
    research_review_count: int
    await_fresh_context_count: int
    skip_count: int
    excluded_count: int
    reason_code_counts_json: dict[str, int]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("source_config_version", self.source_config_version)
        for field_name in (
            "input_count",
            "queue_count",
            "research_review_count",
            "await_fresh_context_count",
            "skip_count",
            "excluded_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
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
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_json_hard_flags(self.payload_json, "payload_json")
        _validate_materialized_fields_match_payload(self)


def to_db_row(
    report: PaperProbabilityRecommendationQueueReport,
) -> PaperProbabilityRecommendationQueueDbRow:
    if type(report) is not PaperProbabilityRecommendationQueueReport:
        raise ValueError("report must be a PaperProbabilityRecommendationQueueReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperProbabilityRecommendationQueueDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        source_config_version=report.source_config_version,
        input_count=report.input_count,
        queue_count=report.queue_count,
        research_review_count=report.research_review_count,
        await_fresh_context_count=report.await_fresh_context_count,
        skip_count=report.skip_count,
        excluded_count=report.excluded_count,
        reason_code_counts_json=_reason_code_counts_json(report),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def from_db_row(
    row: PaperProbabilityRecommendationQueueDbRow,
) -> PaperProbabilityRecommendationQueueReport:
    if type(row) is not PaperProbabilityRecommendationQueueDbRow:
        raise ValueError("row must be a PaperProbabilityRecommendationQueueDbRow")
    _reject_raw_payload_values(row.payload_json, "payload_json")
    _validate_json_hard_flags(row.payload_json, "payload_json")
    _validate_raw_payload_hash(row)
    payload_json = _normalize_legacy_decimal_payload(row.payload_json)
    try:
        report = from_jsonable(PaperProbabilityRecommendationQueueReport, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid probability queue report: {exc}",
        ) from exc
    if type(report) is not PaperProbabilityRecommendationQueueReport:
        raise ValueError(
            "payload_json must recover a PaperProbabilityRecommendationQueueReport",
        )
    _validate_report_tree(report)
    expected_row = to_db_row(report)
    _validate_row_matches_payload(row, expected_row, compare_report_sha256=False)
    return report


def paper_probability_recommendation_queue_report_to_db_row(
    report: PaperProbabilityRecommendationQueueReport,
) -> PaperProbabilityRecommendationQueueDbRow:
    return to_db_row(report)


def paper_probability_recommendation_queue_report_from_db_row(
    row: PaperProbabilityRecommendationQueueDbRow,
) -> PaperProbabilityRecommendationQueueReport:
    return from_db_row(row)


def _validate_report_tree(report: PaperProbabilityRecommendationQueueReport) -> None:
    _validate_hard_flags_tree(report, "report")


def _validate_hard_flags_tree(value: Any, field_name: str) -> None:
    if _has_hard_flag(value):
        _require_hard_flags(field_name, value)
    if is_dataclass(value) and not isinstance(value, type):
        for item_field in fields(value):
            _validate_hard_flags_tree(
                getattr(value, item_field.name),
                f"{field_name}.{item_field.name}",
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_hard_flags_tree(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_hard_flags_tree(item, f"{field_name}.{index}")


def _has_hard_flag(value: Any) -> bool:
    return any(
        hasattr(value, flag_name)
        for flag_name in ("paper_only", "report_only", "readonly")
    )


def _validate_row_matches_payload(
    row: PaperProbabilityRecommendationQueueDbRow,
    expected: PaperProbabilityRecommendationQueueDbRow,
    *,
    compare_report_sha256: bool = True,
) -> None:
    field_names = (
        "report_sha256",
        "generated_at",
        "source_config_version",
        "input_count",
        "queue_count",
        "research_review_count",
        "await_fresh_context_count",
        "skip_count",
        "excluded_count",
        "reason_code_counts_json",
        "paper_only",
        "report_only",
        "readonly",
    )
    for field_name in field_names:
        if field_name == "report_sha256" and not compare_report_sha256:
            continue
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _validate_materialized_fields_match_payload(
    row: PaperProbabilityRecommendationQueueDbRow,
) -> None:
    payload_json = row.payload_json
    expected_values = {
        "report_sha256": _report_sha256(payload_json),
        "generated_at": payload_json.get("generated_at"),
        "source_config_version": payload_json.get("source_config_version"),
        "input_count": payload_json.get("input_count"),
        "queue_count": payload_json.get("queue_count"),
        "research_review_count": payload_json.get("research_review_count"),
        "await_fresh_context_count": payload_json.get("await_fresh_context_count"),
        "skip_count": payload_json.get("skip_count"),
        "excluded_count": payload_json.get("excluded_count"),
        "reason_code_counts_json": _reason_code_counts_json_from_payload(payload_json),
        "paper_only": payload_json.get("paper_only"),
        "report_only": payload_json.get("report_only"),
        "readonly": payload_json.get("readonly"),
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at.isoformat(),
        "source_config_version": row.source_config_version,
        "input_count": row.input_count,
        "queue_count": row.queue_count,
        "research_review_count": row.research_review_count,
        "await_fresh_context_count": row.await_fresh_context_count,
        "skip_count": row.skip_count,
        "excluded_count": row.excluded_count,
        "reason_code_counts_json": row.reason_code_counts_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name in actual_values:
        actual_value = actual_values[field_name]
        expected_value = expected_values[field_name]
        if (
            type(actual_value) is not type(expected_value)
            or actual_value != expected_value
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _reason_code_counts_json(
    report: PaperProbabilityRecommendationQueueReport,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for queue_row in report.queue_rows:
        for reason_code in queue_row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _reason_code_counts_json_from_payload(
    payload_json: dict[str, Any],
) -> dict[str, int] | None:
    queue_rows = payload_json.get("queue_rows")
    if not isinstance(queue_rows, list):
        return None
    counts: dict[str, int] = {}
    for queue_row in queue_rows:
        if not isinstance(queue_row, dict):
            return None
        reason_codes = queue_row.get("reason_codes")
        if not isinstance(reason_codes, list):
            return None
        for reason_code in reason_codes:
            if not isinstance(reason_code, str):
                return None
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_raw_payload_hash(row: PaperProbabilityRecommendationQueueDbRow) -> None:
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")


def _json_ready(value: Any, field_path: tuple[str | int, ...] = ()) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), field_path)
    if isinstance(value, Decimal):
        if not _is_queue_decimal_payload_path(field_path):
            raise ValueError(
                f"{_format_payload_path(field_path)} is not an allowed Decimal path",
            )
        return _fixed_six_decimal_string(_format_payload_path(field_path), value)
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
        return {
            key: _json_ready(item, (*field_path, key))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, (*field_path, index))
            for index, item in enumerate(value)
        ]
    raise ValueError("probability queue DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_raw_payload_values(value, field_name)
    except ValueError as exc:
        raise ValueError(f"{field_name} must contain only JSON-safe values") from exc
    return {key: _json_ready(item) for key, item in value.items()}


def _normalize_legacy_decimal_payload(
    value: Any,
    field_path: tuple[str | int, ...] = (),
) -> Any:
    if _is_queue_decimal_payload_path(field_path):
        field_name = _format_payload_path(field_path)
        if type(value) is not str:
            raise ValueError(f"{field_name} must be a Decimal string")
        return _fixed_six_decimal_string(
            field_name,
            _decimal_from_string(field_name, value),
        )
    if isinstance(value, dict):
        return {
            key: _normalize_legacy_decimal_payload(item, (*field_path, key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _normalize_legacy_decimal_payload(item, (*field_path, index))
            for index, item in enumerate(value)
        ]
    return value


def _is_queue_decimal_payload_path(field_path: tuple[str | int, ...]) -> bool:
    return (
        len(field_path) == 3
        and field_path[0] == "queue_rows"
        and isinstance(field_path[1], int)
        and field_path[2] in _QUEUE_DECIMAL_PAYLOAD_FIELDS
    )


def _fixed_six_decimal_string(field_name: str, value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    value_tuple = value.as_tuple()
    excess_decimal_places = -value_tuple.exponent - 6
    if excess_decimal_places > 0 and any(
        digit != 0 for digit in value_tuple.digits[-excess_decimal_places:]
    ):
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return f"{value:.6f}"


def _decimal_from_string(field_name: str, value: str) -> Decimal:
    try:
        decimal = Decimal(value)
    except ArithmeticError as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal


def _format_payload_path(field_path: tuple[str | int, ...]) -> str:
    if not field_path:
        return "payload_json"
    formatted = "payload_json"
    for item in field_path:
        if isinstance(item, int):
            formatted = f"{formatted}[{item}]"
        else:
            formatted = f"{formatted}.{item}"
    return formatted


def _normalize_reason_code_counts_json(
    field_name: str,
    value: object,
) -> dict[str, int]:
    normalized = _normalize_json_object(field_name, value)
    for key, item in normalized.items():
        _require_canonical_string(f"{field_name} key", key)
        if type(item) is not int or item <= 0:
            raise ValueError(f"{field_name} {key} must be a positive int")
    return {key: normalized[key] for key in sorted(normalized)}


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
        elif isinstance(item, (list, tuple)):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _reject_raw_payload_values(value: Any, field_name: str) -> None:
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must not be a raw Decimal")
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must not be a raw datetime")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_raw_payload_values(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_raw_payload_values(item, f"{field_name}[{index}]")


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


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")
