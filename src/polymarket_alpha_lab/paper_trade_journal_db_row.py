"""Pure row codec for persisted paper trade journal records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
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
_MISSING = object()


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
        _validate_materialized_fields_match_payload(self)


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
    _reject_json_floats(row.payload_json)
    try:
        record = from_jsonable(PaperTradeRecord, row.payload_json)
    except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid paper trade record: {exc}",
        ) from exc
    if type(record) is not PaperTradeRecord:
        raise ValueError("payload_json must recover a PaperTradeRecord")

    expected = paper_trade_record_to_db_row(record)
    if row.record_sha256 != expected.record_sha256:
        raise ValueError("record_sha256 must match payload_json")
    for field_name in (
        "packet_id",
        "decision_timestamp_utc",
        "condition_id",
        "token_id",
        "market_slug",
        "outcome_name",
        "order_side",
        "fill_status",
        "fill_filled_size",
        "fill_average_price",
        "account_equity_before_trade",
        "paper_only",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")
    return record


def _validate_materialized_fields_match_payload(row: PaperTradeJournalDbRow) -> None:
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
        "decision_timestamp_utc": row.decision_timestamp_utc.isoformat(),
        "condition_id": row.condition_id,
        "token_id": row.token_id,
        "market_slug": row.market_slug,
        "outcome_name": row.outcome_name,
        "order_side": row.order_side,
        "fill_status": row.fill_status,
        "fill_filled_size": _json_ready(row.fill_filled_size),
        "fill_average_price": _json_ready(row.fill_average_price),
        "account_equity_before_trade": _json_ready(
            row.account_equity_before_trade,
        ),
    }
    for field_name, actual_value in actual_values.items():
        if actual_value != expected_values[field_name]:
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
    raise ValueError("paper trade journal DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must not contain floats") from exc
    return {key: _json_ready(item) for key, item in value.items()}


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
