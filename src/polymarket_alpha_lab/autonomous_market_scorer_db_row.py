"""Pure row codec for persisted autonomous market scorer reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.autonomous_market_scorer import (
    AutonomousMarketScorerReport,
)
from polymarket_alpha_lab.json_recovery import from_jsonable


__all__ = (
    "AutonomousMarketScorerDbRow",
    "autonomous_market_scorer_from_db_row",
    "autonomous_market_scorer_report_from_db_row",
    "autonomous_market_scorer_report_to_db_row",
    "autonomous_market_scorer_to_db_row",
    "from_db_row",
    "to_db_row",
)


ZERO = Decimal("0")
QUANTUM = Decimal("0.000001")
GATE_STATUSES = ("pass", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_LIKE_STRING_PATTERN = re.compile(
    r"^[+-]?(?:(?:\d+\.\d*)|(?:\.\d+)|(?:\d+[eE][+-]?\d+))$",
)
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_REPORT_DECIMAL_FIELDS = (
    "top_total_score",
    "average_total_score",
    "total_recommended_notional",
)
_SCORE_ROW_DECIMAL_FIELDS = (
    "confidence_score",
    "liquidity_score",
    "spread_score",
    "edge_score",
    "cost_score",
    "risk_score",
    "total_score",
    "recommended_notional",
    "estimated_edge",
)
_MATERIALIZED_FIELDS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "gate_status",
    "markets_scored",
    "markets_skipped",
    "markets_blocked",
    "top_total_score",
    "average_total_score",
    "total_recommended_notional",
    "reason_codes_json",
    "score_rows_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class AutonomousMarketScorerDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    gate_status: str
    markets_scored: int
    markets_skipped: int
    markets_blocked: int
    top_total_score: Decimal
    average_total_score: Decimal
    total_recommended_notional: Decimal
    reason_codes_json: list[str]
    score_rows_json: list[dict[str, Any]]
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
        _require_gate_status("gate_status", self.gate_status)
        _require_nonnegative_int("markets_scored", self.markets_scored)
        _require_nonnegative_int("markets_skipped", self.markets_skipped)
        _require_nonnegative_int("markets_blocked", self.markets_blocked)
        _require_nonnegative_decimal("top_total_score", self.top_total_score)
        _require_nonnegative_decimal(
            "average_total_score",
            self.average_total_score,
        )
        _require_nonnegative_decimal(
            "total_recommended_notional",
            self.total_recommended_notional,
        )
        object.__setattr__(
            self,
            "reason_codes_json",
            _normalize_string_list("reason_codes_json", self.reason_codes_json),
        )
        object.__setattr__(
            self,
            "score_rows_json",
            _normalize_json_object_array("score_rows_json", self.score_rows_json),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)
        _validate_row_payload_consistency(self)


def autonomous_market_scorer_to_db_row(
    report: AutonomousMarketScorerReport,
) -> AutonomousMarketScorerDbRow:
    if type(report) is not AutonomousMarketScorerReport:
        raise ValueError("report must be an AutonomousMarketScorerReport")
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    reason_codes_json = payload_json.get("reason_codes")
    if not isinstance(reason_codes_json, list):
        raise ValueError("payload_json reason_codes must be a JSON array")
    score_rows_json = payload_json.get("score_rows")
    if not isinstance(score_rows_json, list):
        raise ValueError("payload_json score_rows must be a JSON array")
    return AutonomousMarketScorerDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        gate_status=report.gate_status,
        markets_scored=report.markets_scored,
        markets_skipped=report.markets_skipped,
        markets_blocked=report.markets_blocked,
        top_total_score=report.top_total_score,
        average_total_score=report.average_total_score,
        total_recommended_notional=report.total_recommended_notional,
        reason_codes_json=reason_codes_json,
        score_rows_json=score_rows_json,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def autonomous_market_scorer_from_db_row(
    row: AutonomousMarketScorerDbRow,
) -> AutonomousMarketScorerReport:
    if type(row) is not AutonomousMarketScorerDbRow:
        raise ValueError("row must be an AutonomousMarketScorerDbRow")
    return _validate_row_payload_consistency(row)


def _validate_row_payload_consistency(
    row: AutonomousMarketScorerDbRow,
) -> AutonomousMarketScorerReport:
    _validate_row_shape(row)
    reason_codes_json = _normalize_string_list(
        "reason_codes_json",
        row.reason_codes_json,
    )
    raw_score_rows_json = _normalize_json_object_array(
        "score_rows_json",
        row.score_rows_json,
    )
    raw_payload_json = _normalize_json_object("payload_json", row.payload_json)
    if row.report_sha256 != _report_sha256(raw_payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(raw_payload_json, "payload_json")
    payload_json = _normalize_legacy_decimal_payload(raw_payload_json)
    if not isinstance(payload_json, dict):
        raise ValueError("payload_json must be a JSON object")
    score_rows_json = _normalize_legacy_decimal_payload(
        raw_score_rows_json,
        ("score_rows",),
    )
    if not isinstance(score_rows_json, list):
        raise ValueError("score_rows_json must be a JSON array")
    _validate_json_hard_flags(payload_json, "payload_json")
    _validate_payload_decimal_strings(payload_json)
    _require_payload_flags_match_row(payload_json, "payload_json", row)
    if reason_codes_json != payload_json.get("reason_codes"):
        raise ValueError("reason_codes_json must match payload_json")
    if score_rows_json != payload_json.get("score_rows"):
        raise ValueError("score_rows_json must match payload_json")
    try:
        report = from_jsonable(AutonomousMarketScorerReport, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid autonomous market scorer report: {exc}",
        ) from exc
    if type(report) is not AutonomousMarketScorerReport:
        raise ValueError("payload_json must recover an AutonomousMarketScorerReport")
    _validate_report_tree(report)
    _validate_row_matches_payload(
        row,
        report,
        payload_json=payload_json,
        score_rows_json=score_rows_json,
    )
    return report


def _validate_row_shape(row: AutonomousMarketScorerDbRow) -> None:
    _require_sha256("report_sha256", row.report_sha256)
    _as_utc("generated_at", row.generated_at)
    _require_canonical_string("config_version", row.config_version)
    _require_gate_status("gate_status", row.gate_status)
    _require_nonnegative_int("markets_scored", row.markets_scored)
    _require_nonnegative_int("markets_skipped", row.markets_skipped)
    _require_nonnegative_int("markets_blocked", row.markets_blocked)
    _require_nonnegative_decimal("top_total_score", row.top_total_score)
    _require_nonnegative_decimal("average_total_score", row.average_total_score)
    _require_nonnegative_decimal(
        "total_recommended_notional",
        row.total_recommended_notional,
    )
    _normalize_string_list("reason_codes_json", row.reason_codes_json)
    _normalize_json_object_array("score_rows_json", row.score_rows_json)
    _normalize_json_object("payload_json", row.payload_json)
    _require_hard_flags("DB row", row)


def _require_payload_flags_match_row(
    payload_json: dict[str, Any],
    field_name: str,
    row: AutonomousMarketScorerDbRow,
) -> None:
    for flag_name in _HARD_FLAG_NAMES:
        if flag_name not in payload_json:
            raise ValueError(f"{field_name} {flag_name} must match DB row")
        if payload_json[flag_name] is not getattr(row, flag_name):
            raise ValueError(f"{field_name} {flag_name} must match DB row")


def to_db_row(report: AutonomousMarketScorerReport) -> AutonomousMarketScorerDbRow:
    return autonomous_market_scorer_to_db_row(report)


def from_db_row(row: AutonomousMarketScorerDbRow) -> AutonomousMarketScorerReport:
    return autonomous_market_scorer_from_db_row(row)


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
    row: AutonomousMarketScorerDbRow,
    report: AutonomousMarketScorerReport,
    *,
    payload_json: dict[str, Any],
    score_rows_json: list[dict[str, Any]],
) -> None:
    canonical_payload_json = _json_ready(asdict(report))
    expected_values = {
        "report_sha256": row.report_sha256,
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "gate_status": report.gate_status,
        "markets_scored": report.markets_scored,
        "markets_skipped": report.markets_skipped,
        "markets_blocked": report.markets_blocked,
        "top_total_score": report.top_total_score,
        "average_total_score": report.average_total_score,
        "total_recommended_notional": report.total_recommended_notional,
        "reason_codes_json": report.reason_codes,
        "score_rows_json": canonical_payload_json.get("score_rows"),
        "payload_json": canonical_payload_json,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    actual_values = {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "gate_status": row.gate_status,
        "markets_scored": row.markets_scored,
        "markets_skipped": row.markets_skipped,
        "markets_blocked": row.markets_blocked,
        "top_total_score": row.top_total_score,
        "average_total_score": row.average_total_score,
        "total_recommended_notional": row.total_recommended_notional,
        "reason_codes_json": row.reason_codes_json,
        "score_rows_json": score_rows_json,
        "payload_json": payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    for field_name in _MATERIALIZED_FIELDS:
        if not _json_equal_strict(
            _json_ready_materialized_field(field_name, actual_values[field_name]),
            _json_ready_materialized_field(field_name, expected_values[field_name]),
        ):
            raise ValueError(f"{field_name} must match payload_json")


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: Any, field_path: tuple[str | int, ...] = ()) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), field_path)
    if isinstance(value, Decimal):
        if not _is_decimal_payload_path(field_path):
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
            if type(key) is not str:
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
    raise ValueError("scorer DB row values must be JSON serializable")


def _json_ready_materialized_field(field_name: str, value: Any) -> Any:
    if field_name in _REPORT_DECIMAL_FIELDS:
        return _json_ready(value, (field_name,))
    if field_name == "score_rows_json":
        return _json_ready(value, ("score_rows",))
    return _json_ready(value)


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


def _normalize_json_object_array(
    field_name: str,
    value: object,
) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON array")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    try:
        _reject_json_floats(value)
        normalized = _json_ready(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, list):
        raise ValueError(f"{field_name} must be a JSON array")
    for item in normalized:
        if not isinstance(item, dict):
            raise ValueError(f"{field_name} must contain JSON objects")
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
        _require_canonical_string(field_name, item)
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        if previous is not None and previous > item:
            raise ValueError(f"{field_name} must be sorted")
        normalized.append(item)
        seen.add(item)
        previous = item
    return normalized


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(flag_name in value for flag_name in _HARD_FLAG_NAMES):
        for flag_name in _HARD_FLAG_NAMES:
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _validate_payload_decimal_strings(payload_json: dict[str, Any]) -> None:
    for field_name in _REPORT_DECIMAL_FIELDS:
        _require_json_decimal_string(
            f"payload_json {field_name}",
            payload_json.get(field_name),
        )
    score_rows_json = payload_json.get("score_rows")
    if not isinstance(score_rows_json, list):
        raise ValueError("payload_json score_rows must be a JSON array")
    for index, score_row in enumerate(score_rows_json):
        if not isinstance(score_row, dict):
            raise ValueError(f"payload_json score_rows {index} must be a JSON object")
        for field_name in _SCORE_ROW_DECIMAL_FIELDS:
            _require_json_decimal_string(
                f"payload_json score_rows {index} {field_name}",
                score_row.get(field_name),
            )


def _normalize_legacy_decimal_payload(
    value: Any,
    field_path: tuple[str | int, ...] = (),
) -> Any:
    if _is_decimal_payload_path(field_path):
        field_name = _format_payload_path(field_path)
        if type(value) is not str:
            raise ValueError(f"{field_name} must be a Decimal string")
        return _fixed_six_decimal_string(
            field_name,
            _decimal_from_string(field_name, value),
        )
    if type(value) is str and _DECIMAL_LIKE_STRING_PATTERN.fullmatch(value) is not None:
        raise ValueError(
            f"{_format_payload_path(field_path)} is not an allowed Decimal path",
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


def _is_decimal_payload_path(field_path: tuple[str | int, ...]) -> bool:
    return (
        len(field_path) == 1
        and field_path[0] in _REPORT_DECIMAL_FIELDS
    ) or (
        len(field_path) == 3
        and field_path[0] == "score_rows"
        and isinstance(field_path[1], int)
        and field_path[2] in _SCORE_ROW_DECIMAL_FIELDS
    )


def _fixed_six_decimal_string(field_name: str, value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    value_tuple = value.as_tuple()
    excess_decimal_places = -value_tuple.exponent - 6
    if excess_decimal_places > 0 and any(
        digit != 0 for digit in value_tuple.digits[-excess_decimal_places:]
    ):
        raise ValueError(f"{field_name} must not exceed six decimal places")
    if value == ZERO:
        return "0.000000"
    return f"{value:.6f}"


def _decimal_from_string(field_name: str, value: str) -> Decimal:
    try:
        decimal = Decimal(value)
    except InvalidOperation as exc:
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


def _require_json_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    try:
        decimal = Decimal(value)
        canonical = decimal.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical decimal string") from exc
    if not decimal.is_finite() or decimal < ZERO:
        raise ValueError(f"{field_name} must be a nonnegative finite decimal string")
    if decimal == ZERO:
        canonical = ZERO.quantize(QUANTUM)
    if value != str(canonical):
        raise ValueError(f"{field_name} must be a canonical decimal string")


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not be a Decimal")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not be a datetime")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_json_floats(item)


def _json_equal_strict(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return False
        return all(_json_equal_strict(left[key], right[key]) for key in left)
    if isinstance(left, list):
        if len(left) != len(right):
            return False
        return all(
            _json_equal_strict(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def _has_hard_flag(value: Any) -> bool:
    return any(hasattr(value, flag_name) for flag_name in _HARD_FLAG_NAMES)


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in _HARD_FLAG_NAMES:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


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


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_finite_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value != value.quantize(QUANTUM):
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


autonomous_market_scorer_report_to_db_row = autonomous_market_scorer_to_db_row
autonomous_market_scorer_report_from_db_row = autonomous_market_scorer_from_db_row
