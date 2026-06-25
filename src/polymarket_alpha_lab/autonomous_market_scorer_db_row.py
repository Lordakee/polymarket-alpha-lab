"""Pure row codec for persisted autonomous market scorer reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
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
_HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
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
    _reject_json_floats(row.reason_codes_json)
    _reject_json_floats(row.score_rows_json)
    _reject_json_floats(row.payload_json)
    if row.report_sha256 != _report_sha256(row.payload_json):
        raise ValueError("report_sha256 must match payload_json")
    _validate_json_hard_flags(row.payload_json, "payload_json")
    if row.reason_codes_json != row.payload_json.get("reason_codes"):
        raise ValueError("reason_codes_json must match payload_json")
    if row.score_rows_json != row.payload_json.get("score_rows"):
        raise ValueError("score_rows_json must match payload_json")
    try:
        report = from_jsonable(AutonomousMarketScorerReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid autonomous market scorer report: {exc}",
        ) from exc
    if type(report) is not AutonomousMarketScorerReport:
        raise ValueError("payload_json must recover an AutonomousMarketScorerReport")
    _validate_report_tree(report)
    expected_row = autonomous_market_scorer_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


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
    expected: AutonomousMarketScorerDbRow,
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
    raise ValueError("scorer DB row values must be JSON serializable")


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
