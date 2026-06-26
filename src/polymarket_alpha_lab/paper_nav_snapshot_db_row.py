"""Pure row codec for persisted paper NAV snapshots."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.positions import PaperNavSnapshot


__all__ = (
    "PaperNavSnapshotDbRow",
    "paper_nav_snapshot_from_db_row",
    "paper_nav_snapshot_to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_MISSING = object()


@dataclass(frozen=True)
class PaperNavSnapshotDbRow:
    snapshot_sha256: str
    marked_at: datetime
    starting_cash: Decimal
    cash_balance: Decimal
    exit_nav: Decimal
    midpoint_nav: Decimal | None
    total_cost_basis: Decimal
    unrealized_exit_pnl: Decimal
    mark_count: int
    payload_json: dict[str, Any]
    paper_only: bool = True

    def __post_init__(self) -> None:
        _require_sha256("snapshot_sha256", self.snapshot_sha256)
        object.__setattr__(self, "marked_at", _as_utc("marked_at", self.marked_at))
        _require_positive_decimal("starting_cash", self.starting_cash)
        _require_nonnegative_decimal("cash_balance", self.cash_balance)
        _require_nonnegative_decimal("exit_nav", self.exit_nav)
        _require_optional_nonnegative_decimal("midpoint_nav", self.midpoint_nav)
        _require_nonnegative_decimal("total_cost_basis", self.total_cost_basis)
        _require_finite_decimal("unrealized_exit_pnl", self.unrealized_exit_pnl)
        _require_nonnegative_int("mark_count", self.mark_count)
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_paper_only("DB row", self)
        _validate_materialized_fields_match_payload(self)


def paper_nav_snapshot_to_db_row(snapshot: PaperNavSnapshot) -> PaperNavSnapshotDbRow:
    if type(snapshot) is not PaperNavSnapshot:
        raise ValueError("snapshot must be a PaperNavSnapshot")
    _require_paper_only("snapshot", snapshot)
    payload_json = _json_ready(asdict(snapshot))
    snapshot_sha256 = _snapshot_sha256(payload_json)
    return PaperNavSnapshotDbRow(
        snapshot_sha256=snapshot_sha256,
        marked_at=snapshot.marked_at,
        starting_cash=snapshot.starting_cash,
        cash_balance=snapshot.cash_balance,
        exit_nav=snapshot.exit_nav,
        midpoint_nav=snapshot.midpoint_nav,
        total_cost_basis=snapshot.total_cost_basis,
        unrealized_exit_pnl=snapshot.unrealized_exit_pnl,
        mark_count=len(snapshot.marks),
        payload_json=payload_json,
        paper_only=snapshot.paper_only,
    )


def paper_nav_snapshot_from_db_row(row: PaperNavSnapshotDbRow) -> PaperNavSnapshot:
    if type(row) is not PaperNavSnapshotDbRow:
        raise ValueError("row must be a PaperNavSnapshotDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_paper_only(row.payload_json, "payload_json")
    try:
        snapshot = from_jsonable(PaperNavSnapshot, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"payload_json is not a valid NAV snapshot: {exc}") from exc
    if type(snapshot) is not PaperNavSnapshot:
        raise ValueError("payload_json must recover a PaperNavSnapshot")
    _require_paper_only("snapshot", snapshot)
    expected_row = paper_nav_snapshot_to_db_row(snapshot)
    if row.snapshot_sha256 != expected_row.snapshot_sha256:
        raise ValueError("snapshot_sha256 must match payload_json")
    if _summary_values(row) != _summary_values(expected_row):
        raise ValueError("summary columns must match payload_json")
    return snapshot


def _summary_values(row: PaperNavSnapshotDbRow) -> tuple[Any, ...]:
    return (
        row.marked_at,
        row.starting_cash,
        row.cash_balance,
        row.exit_nav,
        row.midpoint_nav,
        row.total_cost_basis,
        row.unrealized_exit_pnl,
        row.mark_count,
        row.paper_only,
    )


def _validate_materialized_fields_match_payload(row: PaperNavSnapshotDbRow) -> None:
    payload_json = row.payload_json
    expected_values = {
        "snapshot_sha256": _snapshot_sha256(payload_json),
        "marked_at": payload_json.get("marked_at", _MISSING),
        "starting_cash": payload_json.get("starting_cash", _MISSING),
        "cash_balance": payload_json.get("cash_balance", _MISSING),
        "exit_nav": payload_json.get("exit_nav", _MISSING),
        "midpoint_nav": payload_json.get("midpoint_nav", _MISSING),
        "total_cost_basis": payload_json.get("total_cost_basis", _MISSING),
        "unrealized_exit_pnl": payload_json.get("unrealized_exit_pnl", _MISSING),
        "mark_count": len(payload_json.get("marks", ()))
        if isinstance(payload_json.get("marks", _MISSING), list)
        else _MISSING,
        "paper_only": payload_json.get("paper_only", _MISSING),
    }
    actual_values = {
        "snapshot_sha256": row.snapshot_sha256,
        "marked_at": row.marked_at.isoformat(),
        "starting_cash": _json_ready(row.starting_cash),
        "cash_balance": _json_ready(row.cash_balance),
        "exit_nav": _json_ready(row.exit_nav),
        "midpoint_nav": _json_ready(row.midpoint_nav),
        "total_cost_basis": _json_ready(row.total_cost_basis),
        "unrealized_exit_pnl": _json_ready(row.unrealized_exit_pnl),
        "mark_count": row.mark_count,
        "paper_only": row.paper_only,
    }
    for field_name, actual_value in actual_values.items():
        if actual_value != expected_values[field_name]:
            raise ValueError(f"{field_name} must match payload_json")


def _snapshot_sha256(payload_json: dict[str, Any]) -> str:
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
    raise ValueError("NAV snapshot DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = {key: _json_ready(item) for key, item in value.items()}
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    _reject_json_floats(normalized)
    _validate_json_paper_only(normalized, field_name)
    return normalized


def _validate_json_paper_only(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if "paper_only" in value and value.get("paper_only") is not True:
        raise ValueError(f"{field_name} paper_only must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_paper_only(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_paper_only(element, f"{child_name} {index}")


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_json_floats(item)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_finite_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_positive_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_finite_decimal(field_name, value)
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_nonnegative_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_paper_only(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
