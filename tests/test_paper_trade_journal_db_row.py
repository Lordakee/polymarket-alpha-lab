from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.paper_trade_journal_db_row import (
    PaperTradeJournalDbRow,
    paper_trade_record_from_db_row,
    paper_trade_record_to_db_row,
)
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet


class PaperTradeRecordSubclass(PaperTradeRecord):
    pass


def complete_packet():
    return build_research_packet(
        candidate=ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        created_at=datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        market_url="https://polymarket.com/event/example-market",
        outcome_name="Yes",
        strategy_type="market_quality",
        model_probability=Decimal("0.56"),
        bid=Decimal("0.50"),
        ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        expected_entry_price=Decimal("0.514"),
        fair_value_estimate=Decimal("0.56"),
        theoretical_edge=Decimal("0.046"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
        cost_adjusted_edge=Decimal("0.026"),
        confidence=Decimal("0.60"),
        max_executable_size=Decimal("100"),
        risk_tags=("liquidity",),
        thesis="Tight spread and clear rules.",
        invalidating_conditions="Spread widens.",
        rule_text="Example rule.",
        resolution_source="Example source",
    )


def complete_fill(
    *,
    token_id: str = "111",
    side: str = "buy",
    order_book_snapshot_sha256: str = "a" * 64,
):
    return PaperFill(
        token_id=token_id,
        side=side,
        requested_size=Decimal("100"),
        order_book_captured_at=datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC),
        order_book_snapshot_sha256=order_book_snapshot_sha256,
        filled_size=Decimal("100"),
        unfilled_size=Decimal("0"),
        average_price=Decimal("0.514"),
        worst_price=Decimal("0.52"),
        best_bid=Decimal("0.49"),
        best_ask=Decimal("0.51"),
        midpoint=Decimal("0.500"),
        spread=Decimal("0.020"),
        slippage_estimate=Decimal("0.004"),
    )


def complete_fill_equivalent_exponents() -> PaperFill:
    return PaperFill(
        token_id="111",
        side="buy",
        requested_size=Decimal("100.000000"),
        order_book_captured_at=datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC),
        order_book_snapshot_sha256="a" * 64,
        filled_size=Decimal("100.000000"),
        unfilled_size=Decimal("0.000000"),
        average_price=Decimal("0.514000"),
        worst_price=Decimal("0.520000"),
        best_bid=Decimal("0.490000"),
        best_ask=Decimal("0.510000"),
        midpoint=Decimal("0.500000"),
        spread=Decimal("0.020000"),
        slippage_estimate=Decimal("0.004000"),
    )


def record_from(packet=None, fill=None) -> PaperTradeRecord:
    return PaperTradeRecord.from_packet_and_fill(
        packet=complete_packet() if packet is None else packet,
        fill=complete_fill() if fill is None else fill,
        decision_timestamp=datetime(2026, 6, 13, 12, 31),
        order_book_raw_archive_path="data/raw/clob/book-111.json",
        order_book_raw_payload_sha256="b" * 64,
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Mark at executable bid on review.",
    )


def equivalent_exponent_record() -> PaperTradeRecord:
    return PaperTradeRecord.from_packet_and_fill(
        packet=complete_packet(),
        fill=complete_fill_equivalent_exponents(),
        decision_timestamp=datetime(2026, 6, 13, 12, 31),
        order_book_raw_archive_path="data/raw/clob/book-111.json",
        order_book_raw_payload_sha256="b" * 64,
        account_equity_before_trade=Decimal("10000.000000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Mark at executable bid on review.",
    )


def overprecision_record() -> PaperTradeRecord:
    record = record_from()
    object.__setattr__(record, "fill_average_price", Decimal("0.5140004"))
    return record


def nonfinite_decimal_record() -> PaperTradeRecord:
    record = record_from()
    object.__setattr__(record, "fill_average_price", Decimal("NaN"))
    return record


def signed_zero_record() -> PaperTradeRecord:
    record = record_from()
    object.__setattr__(record, "fill_unfilled_size", Decimal("-0.000000"))
    return record


def payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bypassed_row(
    row: PaperTradeJournalDbRow,
    **overrides: object,
) -> PaperTradeJournalDbRow:
    malformed = object.__new__(PaperTradeJournalDbRow)
    for field_name, value in row.__dict__.items():
        object.__setattr__(malformed, field_name, value)
    for field_name, value in overrides.items():
        object.__setattr__(malformed, field_name, value)
    return malformed


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_floats(item)


def test_paper_trade_journal_db_row_module_is_pure_paper_only_codec() -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_trade_journal_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "private_key",
        "wallet",
        "api_key",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
        "exchange",
    ):
        assert banned not in source.lower()


def row_copy(row: PaperTradeJournalDbRow, **changes: object) -> PaperTradeJournalDbRow:
    values = {
        "record_sha256": row.record_sha256,
        "packet_id": row.packet_id,
        "decision_timestamp_utc": row.decision_timestamp_utc,
        "condition_id": row.condition_id,
        "token_id": row.token_id,
        "market_slug": row.market_slug,
        "outcome_name": row.outcome_name,
        "order_side": row.order_side,
        "fill_status": row.fill_status,
        "fill_filled_size": row.fill_filled_size,
        "fill_average_price": row.fill_average_price,
        "account_equity_before_trade": row.account_equity_before_trade,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
    }
    values.update(changes)
    return PaperTradeJournalDbRow(**values)


def test_paper_trade_journal_db_row_serializes_payload_and_round_trips() -> None:
    record = record_from()

    row = paper_trade_record_to_db_row(record)

    assert type(row) is PaperTradeJournalDbRow
    assert len(row.record_sha256) == 64
    assert row.record_sha256 == row.record_sha256.lower()
    assert row.packet_id == record.packet_id
    assert row.decision_timestamp_utc == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert row.condition_id == "0xabc"
    assert row.token_id == "111"
    assert row.market_slug == "example-market"
    assert row.outcome_name == "Yes"
    assert row.order_side == "buy"
    assert row.fill_status == "complete"
    assert row.fill_filled_size == Decimal("100")
    assert row.fill_average_price == Decimal("0.514")
    assert row.account_equity_before_trade == Decimal("10000")
    assert row.paper_only is True
    assert row.payload_json["packet_created_at"] == "2026-06-13T12:30:00+00:00"
    assert row.payload_json["decision_timestamp_utc"] == "2026-06-13T12:31:00+00:00"
    assert row.payload_json["order_book_captured_at"] == "2026-06-13T12:30:30+00:00"
    assert row.payload_json["model_probability"] == "0.560000"
    assert row.payload_json["confidence"] == "0.600000"
    assert row.payload_json["fill_filled_size"] == "100.000000"
    assert row.payload_json["fill_unfilled_size"] == "0.000000"
    assert row.payload_json["fill_average_price"] == "0.514000"
    assert row.payload_json["account_equity_before_trade"] == "10000.000000"
    assert row.payload_json["risk_tags"] == ["liquidity"]
    assert_no_floats(row.payload_json)

    with pytest.raises(FrozenInstanceError):
        row.packet_id = "changed"  # type: ignore[misc]

    assert paper_trade_record_from_db_row(row) == record


def test_paper_trade_journal_db_row_canonicalizes_equivalent_decimal_exponents() -> None:
    first = paper_trade_record_to_db_row(record_from())
    second = paper_trade_record_to_db_row(equivalent_exponent_record())

    assert first.record_sha256 == second.record_sha256
    assert first.payload_json == second.payload_json


def test_paper_trade_journal_db_row_rejects_overprecision_new_write_without_rounding() -> None:
    with pytest.raises(ValueError, match="six decimal places|overprecision"):
        paper_trade_record_to_db_row(overprecision_record())


def test_paper_trade_journal_db_row_rejects_nonfinite_decimal_before_persistence() -> None:
    with pytest.raises(ValueError, match="finite"):
        paper_trade_record_to_db_row(nonfinite_decimal_record())


def test_paper_trade_journal_db_row_canonicalizes_signed_zero_decimal() -> None:
    row = paper_trade_record_to_db_row(signed_zero_record())

    assert row.payload_json["fill_unfilled_size"] == "0.000000"


def test_paper_trade_journal_db_row_hash_is_deterministic_for_equivalent_records() -> None:
    record = record_from()
    same_record = PaperTradeRecord(**record.__dict__)

    first = paper_trade_record_to_db_row(record)
    second = paper_trade_record_to_db_row(same_record)

    assert first.record_sha256 == second.record_sha256
    assert first.payload_json == second.payload_json


def test_paper_trade_journal_db_row_rejects_wrong_record_type_and_subclasses() -> None:
    with pytest.raises(ValueError, match="PaperTradeRecord"):
        paper_trade_record_to_db_row(object())

    record = record_from()
    subclass = PaperTradeRecordSubclass(**record.__dict__)
    with pytest.raises(ValueError, match="PaperTradeRecord"):
        paper_trade_record_to_db_row(subclass)


def test_paper_trade_journal_db_row_rejects_false_paper_only_flag() -> None:
    row = paper_trade_record_to_db_row(record_from())

    with pytest.raises(ValueError, match="paper_only"):
        row_copy(row, paper_only=False)


def test_paper_trade_journal_db_row_rejects_payload_floats() -> None:
    row = paper_trade_record_to_db_row(record_from())

    with pytest.raises(ValueError, match="payload_json"):
        row_copy(row, payload_json={**row.payload_json, "bad_float": 0.1})


def test_paper_trade_journal_db_row_rejects_raw_decimal_payload_before_normalization() -> None:
    row = paper_trade_record_to_db_row(record_from())
    payload_json = deepcopy(row.payload_json)
    payload_json["fill_average_price"] = Decimal("0.514000")

    with pytest.raises(ValueError, match="Decimal|JSON"):
        row_copy(row, payload_json=payload_json)

    with pytest.raises(ValueError, match="Decimal|JSON"):
        paper_trade_record_from_db_row(bypassed_row(row, payload_json=payload_json))


def test_paper_trade_journal_db_row_rejects_raw_datetime_payload_before_normalization() -> None:
    row = paper_trade_record_to_db_row(record_from())
    payload_json = deepcopy(row.payload_json)
    payload_json["decision_timestamp_utc"] = datetime(2026, 6, 13, 12, 31, tzinfo=UTC)

    with pytest.raises(ValueError, match="datetime|JSON"):
        row_copy(row, payload_json=payload_json)

    with pytest.raises(ValueError, match="datetime|JSON"):
        paper_trade_record_from_db_row(bypassed_row(row, payload_json=payload_json))


def test_paper_trade_journal_db_row_rejects_record_floats_before_persistence() -> None:
    record = record_from()
    object.__setattr__(record, "fill_average_price", 0.514)

    with pytest.raises(ValueError, match="float|Decimal"):
        paper_trade_record_to_db_row(record)


def test_paper_trade_journal_from_db_row_accepts_self_hashed_allowed_legacy_decimals() -> None:
    row = paper_trade_record_to_db_row(record_from())
    payload_json = deepcopy(row.payload_json)
    payload_json["model_probability"] = "0.56"
    payload_json["confidence"] = "0.60"
    payload_json["research_bid"] = "0.5"
    payload_json["fill_worst_price"] = "0.52"
    payload_json["fill_best_bid"] = "0.49"
    payload_json["fill_filled_size"] = "100"
    payload_json["fill_average_price"] = "0.514"
    payload_json["account_equity_before_trade"] = "10000"

    legacy_row = PaperTradeJournalDbRow(
        record_sha256=payload_sha256(payload_json),
        packet_id=row.packet_id,
        decision_timestamp_utc=row.decision_timestamp_utc,
        condition_id=row.condition_id,
        token_id=row.token_id,
        market_slug=row.market_slug,
        outcome_name=row.outcome_name,
        order_side=row.order_side,
        fill_status=row.fill_status,
        fill_filled_size=Decimal("100"),
        fill_average_price=Decimal("0.514"),
        account_equity_before_trade=Decimal("10000"),
        payload_json=payload_json,
    )

    assert paper_trade_record_from_db_row(legacy_row) == record_from()


def test_paper_trade_journal_from_db_row_rejects_stale_legacy_payload_hash() -> None:
    row = paper_trade_record_to_db_row(record_from())
    payload_json = deepcopy(row.payload_json)
    payload_json["fill_filled_size"] = "100"

    with pytest.raises(ValueError, match="record_sha256"):
        row_copy(row, payload_json=payload_json)

    with pytest.raises(ValueError, match="record_sha256"):
        paper_trade_record_from_db_row(bypassed_row(row, payload_json=payload_json))


def test_paper_trade_journal_from_db_row_rejects_value_changing_legacy_payload() -> None:
    row = paper_trade_record_to_db_row(record_from())
    payload_json = deepcopy(row.payload_json)
    payload_json["fill_average_price"] = "0.514001"

    with pytest.raises(ValueError, match="fill_average_price"):
        PaperTradeJournalDbRow(
            **{
                **row.__dict__,
                "record_sha256": payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_paper_trade_journal_from_db_row_rejects_bypassed_overprecision_payload() -> None:
    row = paper_trade_record_to_db_row(record_from())
    payload_json = deepcopy(row.payload_json)
    payload_json["fill_average_price"] = "0.5140004"

    with pytest.raises(ValueError, match="six decimal places|payload_json"):
        paper_trade_record_from_db_row(
            bypassed_row(
                row,
                record_sha256=payload_sha256(payload_json),
                fill_average_price=Decimal("0.5140004"),
                payload_json=payload_json,
            ),
        )


def test_paper_trade_journal_from_db_row_rejects_noncanonical_datetime_payload() -> None:
    row = paper_trade_record_to_db_row(record_from())
    payload_json = deepcopy(row.payload_json)
    payload_json["packet_created_at"] = "2026-06-13T07:30:00-05:00"

    with pytest.raises(ValueError, match="packet_created_at|canonical|payload_json"):
        PaperTradeJournalDbRow(
            **{
                **row.__dict__,
                "record_sha256": payload_sha256(payload_json),
                "payload_json": payload_json,
            },
        )


def test_paper_trade_journal_from_db_row_rejects_bool_int_confusion_in_bypassed_row() -> None:
    row = paper_trade_record_to_db_row(record_from())

    with pytest.raises(ValueError, match="paper_only"):
        paper_trade_record_from_db_row(bypassed_row(row, paper_only=1))

    payload_json = deepcopy(row.payload_json)
    payload_json["paper_only"] = 1
    with pytest.raises(ValueError, match="paper_only"):
        paper_trade_record_from_db_row(
            bypassed_row(
                row,
                record_sha256=payload_sha256(payload_json),
                payload_json=payload_json,
            ),
        )


def test_paper_trade_journal_db_row_rejects_malformed_stored_payload() -> None:
    row = paper_trade_record_to_db_row(record_from())

    with pytest.raises(ValueError, match="packet_id|payload_json"):
        row_copy(
            row,
            payload_json={
                key: value
                for key, value in row.payload_json.items()
                if key != "packet_id"
            },
        )


def test_paper_trade_journal_db_row_rejects_hash_mismatch() -> None:
    row = paper_trade_record_to_db_row(record_from())

    with pytest.raises(ValueError, match="record_sha256"):
        row_copy(
            row,
            payload_json={**row.payload_json, "token_id": "222"},
        )


def test_paper_trade_journal_from_db_row_defends_against_bypassed_hash_mismatch() -> None:
    row = paper_trade_record_to_db_row(record_from())
    malformed = object.__new__(PaperTradeJournalDbRow)
    for field_name, value in row.__dict__.items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(
        malformed,
        "payload_json",
        {**row.payload_json, "token_id": "222"},
    )

    with pytest.raises(ValueError, match="record_sha256|token_id"):
        paper_trade_record_from_db_row(malformed)
