"""Functional tests for ``polymarket_alpha_lab.paper_portfolio_nav``.

These compose the already-tested primitives (journal read, build_paper_portfolio,
normalize_order_book, mark_paper_nav) behind the new orchestrator and a fake
``MarketNavClient``. ``marked_at`` is caller-supplied so every assertion is
deterministic.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.paper_portfolio_nav import (
    _mark_paper_portfolio_nav_from_records,
    mark_paper_portfolio_nav,
)
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet

MARKED_AT = datetime(2026, 6, 14, 0, 0, tzinfo=UTC)


def _packet(*, token_id: str, condition_id: str, created_minute: int = 30):
    return build_research_packet(
        candidate=ScoredCandidate(
            condition_id=condition_id,
            token_id=token_id,
            market_slug=f"market-{token_id}",
            question=f"Will {token_id} resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        created_at=datetime(2026, 6, 13, 12, created_minute, tzinfo=UTC),
        market_url=f"https://polymarket.com/event/market-{token_id}",
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


def _buy_record(*, token_id: str, condition_id: str, created_minute: int = 30):
    return PaperTradeRecord.from_packet_and_fill(
        packet=_packet(
            token_id=token_id,
            condition_id=condition_id,
            created_minute=created_minute,
        ),
        fill=PaperFill(
            token_id=token_id,
            side="buy",
            requested_size=Decimal("100"),
            order_book_captured_at=datetime(2026, 6, 13, 12, created_minute, 30, tzinfo=UTC),
            order_book_snapshot_sha256="a" * 64,
            filled_size=Decimal("100"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.514"),
            worst_price=Decimal("0.52"),
            best_bid=Decimal("0.49"),
            best_ask=Decimal("0.51"),
            midpoint=Decimal("0.500"),
            spread=Decimal("0.020"),
            slippage_estimate=Decimal("0.004"),
        ),
        decision_timestamp=datetime(2026, 6, 13, 12, created_minute, 31, tzinfo=UTC),
        order_book_raw_archive_path=f"data/raw/clob/book-{token_id}.json",
        order_book_raw_payload_sha256="b" * 64,
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Mark at executable bid on review.",
    )


def _book_payload(token_id: str) -> dict:
    # 100 @ 0.514 -> exit_value 49.600 (60*0.50 + 40*0.49); cost_basis 51.400.
    return {
        "asset_id": token_id,
        "bids": [
            {"price": "0.50", "size": "60"},
            {"price": "0.49", "size": "40"},
        ],
        "asks": [{"price": "0.52", "size": "100"}],
    }


class FakeNavClient:
    def __init__(self, books: dict[str, dict]):
        self._books = books
        self.fetched: list[str] = []

    def get_order_book(self, *, token_id: str) -> dict:
        self.fetched.append(token_id)
        return self._books[token_id]


def test_empty_journal_yields_starting_cash_nav_with_no_fetch(tmp_path):
    journal_path = tmp_path / "empty.jsonl"
    journal_path.write_text("", encoding="utf-8")
    client = FakeNavClient({})  # would KeyError if any fetch happened

    snapshot = mark_paper_portfolio_nav(
        journal_path,
        starting_cash=Decimal("10000"),
        client=client,
        marked_at=MARKED_AT,
    )

    # Empty journal -> empty portfolio -> dict-comp over zero positions
    # performs no fetches; NAV collapses to starting_cash.
    assert client.fetched == []
    assert snapshot.paper_only is True
    assert len(snapshot.marks) == 0
    assert snapshot.starting_cash == Decimal("10000")
    assert snapshot.cash_balance == Decimal("10000")
    assert snapshot.realized_pnl == Decimal("0")
    assert snapshot.exit_nav == Decimal("10000")
    assert snapshot.unrealized_exit_pnl == Decimal("0")
    assert snapshot.marked_at == MARKED_AT


def test_marks_single_position_with_one_live_fetch(tmp_path):
    journal_path = tmp_path / "paper-trades.jsonl"
    PaperTradeJournal(path=journal_path).append(_buy_record(token_id="111", condition_id="0xabc"))
    client = FakeNavClient({"111": _book_payload("111")})

    snapshot = mark_paper_portfolio_nav(
        journal_path,
        starting_cash=Decimal("10000"),
        client=client,
        marked_at=MARKED_AT,
    )

    assert client.fetched == ["111"]
    assert len(snapshot.marks) == 1
    # buy 100 @ 0.514 -> cost 51.400; cash_balance 9948.600; exit_value 49.600.
    assert snapshot.cash_balance == Decimal("9948.600")
    assert snapshot.exit_nav == Decimal("9998.200")
    assert snapshot.total_cost_basis == Decimal("51.400")
    assert snapshot.unrealized_exit_pnl == Decimal("-1.800")
    assert snapshot.marks[0].mark_status == "fully_executable"


def test_marks_supplied_trade_records_without_jsonl():
    record = _buy_record(token_id="111", condition_id="0xabc")
    client = FakeNavClient({"111": _book_payload("111")})

    snapshot = _mark_paper_portfolio_nav_from_records(
        (record,),
        starting_cash=Decimal("10000"),
        client=client,
        marked_at=MARKED_AT,
    )

    assert client.fetched == ["111"]
    assert len(snapshot.marks) == 1
    assert snapshot.exit_nav == Decimal("9998.200")
    assert snapshot.marks[0].token_id == "111"


def test_supplied_trade_records_validate_before_fetch():
    invalid_record = object()
    client = FakeNavClient({"111": _book_payload("111")})

    with pytest.raises(ValueError, match="record must be a PaperTradeRecord"):
        _mark_paper_portfolio_nav_from_records(
            (invalid_record,),
            starting_cash=Decimal("10000"),
            client=client,
            marked_at=MARKED_AT,
        )

    assert client.fetched == []


def test_fans_out_one_fetch_per_held_token(tmp_path):
    journal_path = tmp_path / "paper-trades.jsonl"
    journal = PaperTradeJournal(path=journal_path)
    journal.append(_buy_record(token_id="111", condition_id="0xabc", created_minute=30))
    journal.append(_buy_record(token_id="222", condition_id="0xdef", created_minute=31))
    client = FakeNavClient(
        {
            "111": _book_payload("111"),
            "222": _book_payload("222"),
        }
    )

    snapshot = mark_paper_portfolio_nav(
        journal_path,
        starting_cash=Decimal("100000"),
        client=client,
        marked_at=MARKED_AT,
    )

    assert sorted(client.fetched) == ["111", "222"]
    assert len(snapshot.marks) == 2
    mark_tokens = sorted(mark.token_id for mark in snapshot.marks)
    assert mark_tokens == ["111", "222"]
    # Two identical 100 @ 0.514 longs: total exit_value 99.200, cost 102.800.
    assert snapshot.total_cost_basis == Decimal("102.800")
    assert snapshot.exit_nav == Decimal("100000") - Decimal("102.800") + Decimal("99.200")


def test_appends_nav_log_when_path_supplied(tmp_path):
    journal_path = tmp_path / "paper-trades.jsonl"
    PaperTradeJournal(path=journal_path).append(_buy_record(token_id="111", condition_id="0xabc"))
    nav_log_path = tmp_path / "nav.jsonl"
    client = FakeNavClient({"111": _book_payload("111")})

    snapshot = mark_paper_portfolio_nav(
        journal_path,
        starting_cash=Decimal("10000"),
        client=client,
        marked_at=MARKED_AT,
        nav_log_path=nav_log_path,
    )

    assert nav_log_path.exists()
    lines = nav_log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert Decimal(stored["exit_nav"]) == snapshot.exit_nav
    assert Decimal(stored["starting_cash"]) == snapshot.starting_cash
    assert stored["paper_only"] is True


def test_injected_nav_snapshot_sink_receives_returned_snapshot(tmp_path):
    journal_path = tmp_path / "paper-trades.jsonl"
    PaperTradeJournal(path=journal_path).append(_buy_record(token_id="111", condition_id="0xabc"))
    client = FakeNavClient({"111": _book_payload("111")})
    received = []

    def sink(snapshot):
        received.append(snapshot)

    snapshot = mark_paper_portfolio_nav(
        journal_path,
        starting_cash=Decimal("10000"),
        client=client,
        marked_at=MARKED_AT,
        nav_snapshot_sink=sink,
    )

    assert received == [snapshot]
    assert received[0] is snapshot


def test_nav_snapshot_sink_runs_after_nav_log_append_even_when_sink_raises(tmp_path):
    journal_path = tmp_path / "paper-trades.jsonl"
    PaperTradeJournal(path=journal_path).append(_buy_record(token_id="111", condition_id="0xabc"))
    nav_log_path = tmp_path / "nav.jsonl"
    client = FakeNavClient({"111": _book_payload("111")})
    sink_observations = []

    def sink(snapshot):
        lines = nav_log_path.read_text(encoding="utf-8").splitlines()
        sink_observations.append((snapshot, nav_log_path.exists(), len(lines)))
        raise RuntimeError("sink failed")

    with pytest.raises(RuntimeError, match="sink failed"):
        mark_paper_portfolio_nav(
            journal_path,
            starting_cash=Decimal("10000"),
            client=client,
            marked_at=MARKED_AT,
            nav_log_path=nav_log_path,
            nav_snapshot_sink=sink,
        )

    assert len(sink_observations) == 1
    assert sink_observations[0][1:] == (True, 1)
    assert nav_log_path.exists()
    assert len(nav_log_path.read_text(encoding="utf-8").splitlines()) == 1


def test_omits_nav_log_when_path_absent(tmp_path):
    journal_path = tmp_path / "paper-trades.jsonl"
    PaperTradeJournal(path=journal_path).append(_buy_record(token_id="111", condition_id="0xabc"))
    nav_log_path = tmp_path / "nav.jsonl"
    client = FakeNavClient({"111": _book_payload("111")})

    mark_paper_portfolio_nav(
        journal_path,
        starting_cash=Decimal("10000"),
        client=client,
        marked_at=MARKED_AT,
    )

    assert not nav_log_path.exists()


def test_rejects_invalid_nav_snapshot_sink_before_any_client_fetch(tmp_path):
    journal_path = tmp_path / "paper-trades.jsonl"
    PaperTradeJournal(path=journal_path).append(_buy_record(token_id="111", condition_id="0xabc"))
    client = FakeNavClient({"111": _book_payload("111")})

    with pytest.raises(ValueError, match="nav_snapshot_sink"):
        mark_paper_portfolio_nav(
            journal_path,
            starting_cash=Decimal("10000"),
            client=client,
            marked_at=MARKED_AT,
            nav_snapshot_sink=object(),
        )

    assert client.fetched == []


def test_nav_snapshot_sink_failure_propagates(tmp_path):
    journal_path = tmp_path / "paper-trades.jsonl"
    PaperTradeJournal(path=journal_path).append(_buy_record(token_id="111", condition_id="0xabc"))
    client = FakeNavClient({"111": _book_payload("111")})

    def sink(snapshot):
        raise RuntimeError("sink failed")

    with pytest.raises(RuntimeError, match="sink failed"):
        mark_paper_portfolio_nav(
            journal_path,
            starting_cash=Decimal("10000"),
            client=client,
            marked_at=MARKED_AT,
            nav_snapshot_sink=sink,
        )


def test_rejects_non_positive_starting_cash(tmp_path):
    journal_path = tmp_path / "empty.jsonl"
    journal_path.write_text("", encoding="utf-8")
    client = FakeNavClient({})

    with pytest.raises(ValueError, match="starting_cash must be positive"):
        mark_paper_portfolio_nav(
            journal_path,
            starting_cash=Decimal("0"),
            client=client,
            marked_at=MARKED_AT,
        )

    with pytest.raises(ValueError, match="starting_cash must be positive"):
        mark_paper_portfolio_nav(
            journal_path,
            starting_cash=Decimal("-1"),
            client=client,
            marked_at=MARKED_AT,
        )


def test_rejects_non_decimal_starting_cash(tmp_path):
    journal_path = tmp_path / "empty.jsonl"
    journal_path.write_text("", encoding="utf-8")
    client = FakeNavClient({})

    with pytest.raises(ValueError, match="starting_cash must be a Decimal"):
        mark_paper_portfolio_nav(
            journal_path,
            starting_cash=10000,  # int, not Decimal
            client=client,
            marked_at=MARKED_AT,
        )


def test_rejects_non_protocol_client(tmp_path):
    journal_path = tmp_path / "empty.jsonl"
    journal_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="client must be a MarketNavClient"):
        mark_paper_portfolio_nav(
            journal_path,
            starting_cash=Decimal("10000"),
            client=object(),  # no get_order_book method
            marked_at=MARKED_AT,
        )


def test_round_trips_journal_read_through_full_pipeline(tmp_path):
    # End-to-end: the orchestrator must consume records produced by the very
    # same PaperTradeJournal.append path (type-keyed read coercion feeds
    # build_paper_portfolio's _validate_trade_record re-validation).
    journal_path = tmp_path / "paper-trades.jsonl"
    record = _buy_record(token_id="111", condition_id="0xabc")
    PaperTradeJournal(path=journal_path).append(record)
    client = FakeNavClient({"111": _book_payload("111")})

    snapshot = mark_paper_portfolio_nav(
        journal_path,
        starting_cash=Decimal("10000"),
        client=client,
        marked_at=MARKED_AT,
    )

    assert snapshot.exit_nav == Decimal("9998.200")
    assert snapshot.marks[0].token_id == "111"
