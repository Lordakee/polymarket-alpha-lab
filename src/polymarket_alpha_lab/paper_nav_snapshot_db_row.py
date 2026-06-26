"""Pure row codec for persisted paper NAV snapshots."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
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
_DECIMAL_QUANTUM = Decimal("0.000001")
_MISSING = object()
_MATERIALIZED_DECIMAL_PAYLOAD_PATHS = frozenset(
    {
        ("starting_cash",),
        ("cash_balance",),
        ("exit_nav",),
        ("midpoint_nav",),
        ("total_cost_basis",),
        ("unrealized_exit_pnl",),
    },
)


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
        _validate_payload_recovers_to_compatible_snapshot(self.payload_json)


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
    _validate_row_core_fields(row)
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    _validate_materialized_fields_match_payload(row, payload_json)
    snapshot = _validate_payload_recovers_to_compatible_snapshot(payload_json)
    return snapshot


def _validate_row_core_fields(row: PaperNavSnapshotDbRow) -> None:
    _require_sha256("snapshot_sha256", row.snapshot_sha256)
    _as_utc("marked_at", row.marked_at)
    _require_positive_decimal("starting_cash", row.starting_cash)
    _require_nonnegative_decimal("cash_balance", row.cash_balance)
    _require_nonnegative_decimal("exit_nav", row.exit_nav)
    _require_optional_nonnegative_decimal("midpoint_nav", row.midpoint_nav)
    _require_nonnegative_decimal("total_cost_basis", row.total_cost_basis)
    _require_finite_decimal("unrealized_exit_pnl", row.unrealized_exit_pnl)
    _require_nonnegative_int("mark_count", row.mark_count)
    _require_paper_only("DB row", row)


def _validate_payload_recovers_to_compatible_snapshot(
    payload_json: dict[str, Any],
) -> PaperNavSnapshot:
    try:
        snapshot = from_jsonable(PaperNavSnapshot, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"payload_json is not a valid NAV snapshot: {exc}") from exc
    if type(snapshot) is not PaperNavSnapshot:
        raise ValueError("payload_json must recover a PaperNavSnapshot")
    _require_paper_only("snapshot", snapshot)
    expected_payload_json = _json_ready(asdict(snapshot))
    _validate_payload_compatible_with_canonical_payload(
        payload_json,
        expected_payload_json,
    )
    return snapshot


def _validate_materialized_fields_match_payload(
    row: PaperNavSnapshotDbRow,
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
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
        "marked_at": _as_utc("marked_at", row.marked_at).isoformat(),
        "mark_count": row.mark_count,
        "paper_only": row.paper_only,
    }
    for field_name, actual_value in actual_values.items():
        _require_json_exact_match(
            field_name,
            actual_value,
            expected_values[field_name],
        )
    for field_name in (
        "starting_cash",
        "cash_balance",
        "exit_nav",
        "midpoint_nav",
        "total_cost_basis",
        "unrealized_exit_pnl",
    ):
        _require_materialized_decimal_match(
            field_name,
            getattr(row, field_name),
            expected_values[field_name],
        )


def _require_json_exact_match(
    field_name: str,
    actual_value: object,
    expected_value: object,
) -> None:
    if type(actual_value) is not type(expected_value) or actual_value != expected_value:
        raise ValueError(f"{field_name} must match payload_json")


def _require_materialized_decimal_match(
    field_name: str,
    row_value: Decimal | None,
    payload_value: object,
) -> None:
    if row_value is None:
        if payload_value is not None:
            raise ValueError(f"{field_name} must match payload_json")
        return
    if type(payload_value) is not str:
        raise ValueError(f"{field_name} must match payload_json")
    try:
        payload_decimal = Decimal(payload_value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must match payload_json") from exc
    if not payload_decimal.is_finite() or payload_decimal != row_value:
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
        return _decimal_to_json(value)
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
        normalized = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    _validate_json_paper_only(normalized, field_name)
    return normalized


def _copy_json_payload(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        raise ValueError("JSON value must not contain Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, datetime):
        raise ValueError("JSON value must not contain datetime")
    if type(value) in (str, int, bool):
        return value
    if isinstance(value, dict):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            copied[key] = _copy_json_payload(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_payload(item) for item in value]
    raise ValueError("JSON value must be a dict, list, string, int, bool, or null")


def _decimal_to_json(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("JSON Decimal value must be finite")
    with localcontext() as context:
        context.prec = max(
            28,
            len(value.as_tuple().digits) + abs(value.as_tuple().exponent) + 6,
        )
        quantized = value.quantize(_DECIMAL_QUANTUM)
    if value != quantized:
        raise ValueError("JSON Decimal value must have at most six decimal places")
    if quantized.is_zero():
        quantized = Decimal("0.000000")
    return format(quantized, "f")


def _validate_payload_compatible_with_canonical_payload(
    payload_json: dict[str, Any],
    expected_payload_json: dict[str, Any],
) -> None:
    try:
        _validate_json_compatible((), payload_json, expected_payload_json)
    except ValueError as exc:
        raise ValueError(f"payload_json must match canonical NAV snapshot: {exc}") from exc


def _validate_json_compatible(
    path: tuple[str, ...],
    actual: object,
    expected: object,
) -> None:
    if path in _MATERIALIZED_DECIMAL_PAYLOAD_PATHS:
        _validate_compatible_decimal_path(".".join(path), actual, expected)
        return
    if type(actual) is not type(expected):
        raise ValueError(f"{'.'.join(path) or 'payload_json'} has wrong JSON type")
    if isinstance(actual, dict):
        if actual.keys() != expected.keys():  # type: ignore[union-attr]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} keys differ")
        for key in actual:
            _validate_json_compatible(
                (*path, key),
                actual[key],
                expected[key],  # type: ignore[index]
            )
        return
    if isinstance(actual, list):
        if len(actual) != len(expected):  # type: ignore[arg-type]
            raise ValueError(f"{'.'.join(path) or 'payload_json'} length differs")
        for index, item in enumerate(actual):
            _validate_json_compatible(
                (*path, str(index)),
                item,
                expected[index],  # type: ignore[index]
            )
        return
    if actual != expected:
        raise ValueError(f"{'.'.join(path) or 'payload_json'} differs")


def _validate_compatible_decimal_path(
    field_name: str,
    actual: object,
    expected: object,
) -> None:
    if actual is None or expected is None:
        if actual is not expected:
            raise ValueError(f"{field_name} differs")
        return
    if type(actual) is not str or type(expected) is not str:
        raise ValueError(f"{field_name} has wrong JSON type")
    try:
        actual_decimal = Decimal(actual)
        expected_decimal = Decimal(expected)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} is not a Decimal string") from exc
    if (
        not actual_decimal.is_finite()
        or not expected_decimal.is_finite()
        or actual_decimal != expected_decimal
    ):
        raise ValueError(f"{field_name} differs")


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
    if type(value) is not Decimal:
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
