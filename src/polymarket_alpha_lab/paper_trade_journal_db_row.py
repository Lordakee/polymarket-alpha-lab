"""Pure row codec for persisted paper trade journal records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.json_recovery import from_jsonable


__all__ = (
    "PaperTradeJournalDbRow",
    "paper_trade_record_from_db_row",
    "paper_trade_record_to_db_row",
)

_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_ORDER_SIDES = ("buy", "sell")
_FILL_STATUSES = ("complete", "partial")
_DECIMAL_QUANTUM = Decimal("0.000001")
_MISSING = object()
_MATERIALIZED_DECIMAL_PAYLOAD_PATHS = frozenset(
    {
        ("fill_filled_size",),
        ("fill_average_price",),
        ("account_equity_before_trade",),
    },
)
_DECIMAL_PAYLOAD_PATHS = frozenset(
    {
        ("model_probability",),
        ("confidence",),
        ("research_bid",),
        ("research_ask",),
        ("research_midpoint",),
        ("research_expected_entry_price",),
        ("research_fair_value_estimate",),
        ("research_theoretical_edge",),
        ("research_spread",),
        ("research_slippage_estimate",),
        ("research_cost_adjusted_edge",),
        ("max_executable_size",),
        ("order_requested_size",),
        ("fill_filled_size",),
        ("fill_unfilled_size",),
        ("fill_average_price",),
        ("fill_worst_price",),
        ("fill_best_bid",),
        ("fill_best_ask",),
        ("fill_midpoint",),
        ("fill_spread",),
        ("fill_slippage_estimate",),
        ("account_equity_before_trade",),
    },
)


@dataclass(frozen=True)
class PaperTradeJournalDbRow:
    record_sha256: str
    packet_id: str
    decision_timestamp_utc: datetime
    condition_id: str
    token_id: str
    market_slug: str
    outcome_name: str
    order_side: str
    fill_status: str
    fill_filled_size: Decimal
    fill_average_price: Decimal
    account_equity_before_trade: Decimal
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("record_sha256", self.record_sha256)
        _require_canonical_string("packet_id", self.packet_id)
        object.__setattr__(
            self,
            "decision_timestamp_utc",
            _as_utc("decision_timestamp_utc", self.decision_timestamp_utc),
        )
        _require_canonical_string("condition_id", self.condition_id)
        _require_canonical_string("token_id", self.token_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("outcome_name", self.outcome_name)
        _require_choice("order_side", self.order_side, _ORDER_SIDES)
        _require_choice("fill_status", self.fill_status, _FILL_STATUSES)
        _require_positive_decimal("fill_filled_size", self.fill_filled_size)
        _require_price_decimal("fill_average_price", self.fill_average_price)
        _require_positive_decimal(
            "account_equity_before_trade",
            self.account_equity_before_trade,
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")
        _validate_materialized_fields_match_payload(self)
        _validate_payload_recovers_to_compatible_record(self.payload_json)


def paper_trade_record_to_db_row(record: PaperTradeRecord) -> PaperTradeJournalDbRow:
    if type(record) is not PaperTradeRecord:
        raise ValueError("record must be a PaperTradeRecord")
    payload_json = _json_ready(asdict(record))
    return PaperTradeJournalDbRow(
        record_sha256=_record_sha256(payload_json),
        packet_id=record.packet_id,
        decision_timestamp_utc=record.decision_timestamp_utc,
        condition_id=record.condition_id,
        token_id=record.token_id,
        market_slug=record.market_slug,
        outcome_name=record.outcome_name,
        order_side=record.order_side,
        fill_status=record.fill_status,
        fill_filled_size=record.fill_filled_size,
        fill_average_price=record.fill_average_price,
        account_equity_before_trade=record.account_equity_before_trade,
        payload_json=payload_json,
    )


def paper_trade_record_from_db_row(row: PaperTradeJournalDbRow) -> PaperTradeRecord:
    if type(row) is not PaperTradeJournalDbRow:
        raise ValueError("row must be a PaperTradeJournalDbRow")
    _validate_row_core_fields(row)
    payload_json = _normalize_json_object("payload_json", row.payload_json)
    _validate_materialized_fields_match_payload(row, payload_json)
    record = _validate_payload_recovers_to_compatible_record(payload_json)
    return record


def _validate_row_core_fields(row: PaperTradeJournalDbRow) -> None:
    _require_sha256("record_sha256", row.record_sha256)
    _require_canonical_string("packet_id", row.packet_id)
    _as_utc("decision_timestamp_utc", row.decision_timestamp_utc)
    _require_canonical_string("condition_id", row.condition_id)
    _require_canonical_string("token_id", row.token_id)
    _require_canonical_string("market_slug", row.market_slug)
    _require_canonical_string("outcome_name", row.outcome_name)
    _require_choice("order_side", row.order_side, _ORDER_SIDES)
    _require_choice("fill_status", row.fill_status, _FILL_STATUSES)
    _require_positive_decimal("fill_filled_size", row.fill_filled_size)
    _require_price_decimal("fill_average_price", row.fill_average_price)
    _require_positive_decimal(
        "account_equity_before_trade",
        row.account_equity_before_trade,
    )
    if row.paper_only is not True:
        raise ValueError("paper_only must be True")
    if row.report_only is not True:
        raise ValueError("report_only must be True")
    if row.readonly is not True:
        raise ValueError("readonly must be True")


def _validate_payload_recovers_to_compatible_record(
    payload_json: dict[str, Any],
) -> PaperTradeRecord:
    try:
        record = from_jsonable(PaperTradeRecord, payload_json)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid paper trade record: {exc}",
        ) from exc
    if type(record) is not PaperTradeRecord:
        raise ValueError("payload_json must recover a PaperTradeRecord")
    expected_payload_json = _json_ready(asdict(record))
    _validate_payload_compatible_with_canonical_payload(
        payload_json,
        expected_payload_json,
    )
    return record


def _validate_materialized_fields_match_payload(
    row: PaperTradeJournalDbRow,
    payload_json: dict[str, Any] | None = None,
) -> None:
    if payload_json is None:
        payload_json = row.payload_json
    expected_values = {
        "record_sha256": _record_sha256(payload_json),
        "packet_id": payload_json.get("packet_id", _MISSING),
        "decision_timestamp_utc": payload_json.get(
            "decision_timestamp_utc",
            _MISSING,
        ),
        "condition_id": payload_json.get("condition_id", _MISSING),
        "token_id": payload_json.get("token_id", _MISSING),
        "market_slug": payload_json.get("market_slug", _MISSING),
        "outcome_name": payload_json.get("outcome_name", _MISSING),
        "order_side": payload_json.get("order_side", _MISSING),
        "fill_status": payload_json.get("fill_status", _MISSING),
        "fill_filled_size": payload_json.get("fill_filled_size", _MISSING),
        "fill_average_price": payload_json.get("fill_average_price", _MISSING),
        "account_equity_before_trade": payload_json.get(
            "account_equity_before_trade",
            _MISSING,
        ),
    }
    actual_values = {
        "record_sha256": row.record_sha256,
        "packet_id": row.packet_id,
        "decision_timestamp_utc": _as_utc(
            "decision_timestamp_utc",
            row.decision_timestamp_utc,
        ).isoformat(),
        "condition_id": row.condition_id,
        "token_id": row.token_id,
        "market_slug": row.market_slug,
        "outcome_name": row.outcome_name,
        "order_side": row.order_side,
        "fill_status": row.fill_status,
    }
    for field_name, actual_value in actual_values.items():
        _require_json_exact_match(
            field_name,
            actual_value,
            expected_values[field_name],
        )
    for field_path in _MATERIALIZED_DECIMAL_PAYLOAD_PATHS:
        field_name = field_path[0]
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
    row_value: Decimal,
    payload_value: object,
) -> None:
    if type(payload_value) is not str:
        raise ValueError(f"{field_name} must match payload_json")
    try:
        payload_decimal = Decimal(payload_value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must match payload_json") from exc
    if not payload_decimal.is_finite() or payload_decimal != row_value:
        raise ValueError(f"{field_name} must match payload_json")


def _record_sha256(payload_json: dict[str, Any]) -> str:
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
    raise ValueError("paper trade journal DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        normalized = _copy_json_payload(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
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
        raise ValueError(
            f"payload_json must match canonical paper trade record: {exc}",
        ) from exc


def _validate_json_compatible(
    path: tuple[str, ...],
    actual: object,
    expected: object,
) -> None:
    if path in _DECIMAL_PAYLOAD_PATHS:
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


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        rendered = ", ".join(choices)
        raise ValueError(f"{field_name} must be one of: {rendered}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a finite Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    return value


def _require_positive_decimal(field_name: str, value: object) -> None:
    decimal = _require_decimal(field_name, value)
    if decimal <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_price_decimal(field_name: str, value: object) -> None:
    decimal = _require_decimal(field_name, value)
    if decimal < 0 or decimal > 1:
        raise ValueError(f"{field_name} must be in [0, 1]")
