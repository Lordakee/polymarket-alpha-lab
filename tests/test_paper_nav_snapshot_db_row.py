from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_nav_snapshot_db_row import (
    PaperNavSnapshotDbRow,
    paper_nav_snapshot_from_db_row,
    paper_nav_snapshot_to_db_row,
)
from polymarket_alpha_lab.positions import PaperNavSnapshot, PaperPositionMark


MARKED_AT = datetime(2026, 6, 19, 18, 15, tzinfo=UTC)
BOOK_CAPTURED_AT = datetime(2026, 6, 19, 18, 14, tzinfo=UTC)


class NavSnapshotSubclass(PaperNavSnapshot):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _mark(*, token_id: str = "token-1") -> PaperPositionMark:
    return PaperPositionMark(
        condition_id=f"condition-{token_id}",
        token_id=token_id,
        market_slug=f"market-{token_id}",
        outcome_name="Yes",
        open_size=d("10"),
        cost_basis=d("4.00"),
        average_entry_price=d("0.400"),
        order_book_captured_at=BOOK_CAPTURED_AT,
        order_book_snapshot_sha256="b" * 64,
        exit_filled_size=d("10"),
        exit_unfilled_size=d("0"),
        exit_average_price=d("0.550"),
        exit_worst_price=d("0.540"),
        exit_value=d("5.50"),
        midpoint_price=d("0.555"),
        midpoint_value=d("5.55"),
        best_bid=d("0.550"),
        best_ask=d("0.560"),
        spread=d("0.010"),
        slippage_estimate=d("0.000"),
        mark_status="fully_executable",
    )


def _snapshot(
    *,
    marked_at: datetime = MARKED_AT,
    paper_only: bool = True,
) -> PaperNavSnapshot:
    return PaperNavSnapshot(
        marked_at=marked_at,
        starting_cash=d("100.00"),
        cash_balance=d("96.00"),
        realized_pnl=d("0"),
        exit_nav=d("101.50"),
        midpoint_nav=d("101.55"),
        total_cost_basis=d("4.00"),
        unrealized_exit_pnl=d("1.50"),
        marks=(_mark(),),
        paper_only=paper_only,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_nav_snapshot_db_row_module_is_pure_paper_only_codec() -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_nav_snapshot_db_row.py",
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


def test_nav_snapshot_db_row_serializes_canonical_payload_and_round_trips() -> None:
    snapshot = _snapshot(
        marked_at=datetime(2026, 6, 19, 14, 15, tzinfo=timezone(timedelta(hours=-4))),
    )

    row = paper_nav_snapshot_to_db_row(snapshot)

    assert type(row) is PaperNavSnapshotDbRow
    assert len(row.snapshot_sha256) == 64
    assert row.snapshot_sha256 == row.snapshot_sha256.lower()
    assert row.marked_at == MARKED_AT
    assert row.starting_cash == d("100.00")
    assert row.cash_balance == d("96.00")
    assert row.exit_nav == d("101.50")
    assert row.midpoint_nav == d("101.55")
    assert row.total_cost_basis == d("4.00")
    assert row.unrealized_exit_pnl == d("1.50")
    assert row.mark_count == 1
    assert row.paper_only is True
    assert row.payload_json["marked_at"] == "2026-06-19T18:15:00+00:00"
    assert row.payload_json["starting_cash"] == "100.00"
    assert row.payload_json["cash_balance"] == "96.00"
    assert row.payload_json["exit_nav"] == "101.50"
    assert row.payload_json["midpoint_nav"] == "101.55"
    assert row.payload_json["marks"][0]["cost_basis"] == "4.00"
    assert row.payload_json["marks"][0]["order_book_captured_at"] == (
        "2026-06-19T18:14:00+00:00"
    )
    assert row.payload_json["paper_only"] is True
    _assert_no_floats(row.payload_json)

    assert paper_nav_snapshot_from_db_row(row) == snapshot


def test_nav_snapshot_db_row_hash_is_deterministic_for_equivalent_snapshots() -> None:
    snapshot = _snapshot()
    same_snapshot = PaperNavSnapshot(**snapshot.__dict__)

    first = paper_nav_snapshot_to_db_row(snapshot)
    second = paper_nav_snapshot_to_db_row(same_snapshot)

    assert first.snapshot_sha256 == second.snapshot_sha256
    assert first.payload_json == second.payload_json


def test_nav_snapshot_db_row_rejects_wrong_snapshot_type_and_subclasses() -> None:
    with pytest.raises(ValueError, match="PaperNavSnapshot"):
        paper_nav_snapshot_to_db_row(object())

    snapshot = _snapshot()
    subclass = NavSnapshotSubclass(**snapshot.__dict__)
    with pytest.raises(ValueError, match="PaperNavSnapshot"):
        paper_nav_snapshot_to_db_row(subclass)


def test_nav_snapshot_db_row_rejects_false_paper_only_snapshot_flag() -> None:
    snapshot = _snapshot()
    object.__setattr__(snapshot, "paper_only", False)

    with pytest.raises(ValueError, match="paper_only"):
        paper_nav_snapshot_to_db_row(snapshot)


def test_nav_snapshot_db_row_rejects_malformed_stored_payload_flags() -> None:
    row = paper_nav_snapshot_to_db_row(_snapshot())

    with pytest.raises(ValueError, match="paper_only"):
        PaperNavSnapshotDbRow(
            snapshot_sha256="a" * 64,
            marked_at=row.marked_at,
            starting_cash=row.starting_cash,
            cash_balance=row.cash_balance,
            exit_nav=row.exit_nav,
            midpoint_nav=row.midpoint_nav,
            total_cost_basis=row.total_cost_basis,
            unrealized_exit_pnl=row.unrealized_exit_pnl,
            mark_count=row.mark_count,
            payload_json={**row.payload_json, "paper_only": False},
        )


def test_nav_snapshot_db_row_wraps_payload_recovery_errors_as_value_error() -> None:
    row = paper_nav_snapshot_to_db_row(_snapshot())

    with pytest.raises(ValueError, match="mark_count|payload_json"):
        replace(
            row,
            snapshot_sha256="a" * 64,
            payload_json={
                key: value for key, value in row.payload_json.items() if key != "marks"
            },
        )


def test_nav_snapshot_db_row_validates_row_shape_and_summary_matches_payload() -> None:
    row = paper_nav_snapshot_to_db_row(_snapshot())

    with pytest.raises(ValueError, match="snapshot_sha256"):
        replace(row, snapshot_sha256="bad")

    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})

    with pytest.raises(ValueError, match="mark_count"):
        replace(row, mark_count=2)

    with pytest.raises(FrozenInstanceError):
        row.mark_count = 2  # type: ignore[misc]


def test_nav_snapshot_from_db_row_defends_against_bypassed_summary_mismatch() -> None:
    row = paper_nav_snapshot_to_db_row(_snapshot())
    malformed = object.__new__(PaperNavSnapshotDbRow)
    for field_name, value in row.__dict__.items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(malformed, "mark_count", 2)

    with pytest.raises(ValueError, match="summary|mark_count"):
        paper_nav_snapshot_from_db_row(malformed)


def test_nav_snapshot_db_row_does_not_require_report_only_or_readonly_flags() -> None:
    row = paper_nav_snapshot_to_db_row(_snapshot())
    payload_without_extra_flags = {
        key: value
        for key, value in row.payload_json.items()
        if key not in {"report_only", "readonly"}
    }
    relaxed_row = replace(row, payload_json=payload_without_extra_flags)

    assert paper_nav_snapshot_from_db_row(relaxed_row) == _snapshot()
