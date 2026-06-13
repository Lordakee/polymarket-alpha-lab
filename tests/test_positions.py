import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, localcontext

import pytest

from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.positions import (
    PaperNavLog,
    PaperNavSnapshot,
    PaperPortfolio,
    PaperPosition,
    PaperPositionMark,
    build_paper_portfolio,
    mark_paper_nav,
)
from polymarket_alpha_lab.research import build_research_packet


def complete_packet(**overrides):
    values = {
        "candidate": ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        "created_at": datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
        "market_url": "https://polymarket.com/event/example-market",
        "outcome_name": "Yes",
        "strategy_type": "market_quality",
        "model_probability": Decimal("0.56"),
        "bid": Decimal("0.50"),
        "ask": Decimal("0.52"),
        "midpoint": Decimal("0.51"),
        "expected_entry_price": Decimal("0.514"),
        "fair_value_estimate": Decimal("0.56"),
        "theoretical_edge": Decimal("0.046"),
        "spread": Decimal("0.02"),
        "slippage_estimate": Decimal("0.004"),
        "cost_adjusted_edge": Decimal("0.026"),
        "confidence": Decimal("0.60"),
        "max_executable_size": Decimal("100"),
        "risk_tags": ("liquidity",),
        "thesis": "Tight spread and clear rules.",
        "invalidating_conditions": "Spread widens.",
        "rule_text": "Example rule.",
        "resolution_source": "Example source",
    }
    values.update(overrides)
    return build_research_packet(**values)


def complete_fill(**overrides):
    values = {
        "token_id": "111",
        "side": "buy",
        "requested_size": Decimal("100"),
        "order_book_captured_at": datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC),
        "order_book_snapshot_sha256": "a" * 64,
        "filled_size": Decimal("100"),
        "unfilled_size": Decimal("0"),
        "average_price": Decimal("0.514"),
        "worst_price": Decimal("0.52"),
        "best_bid": Decimal("0.49"),
        "best_ask": Decimal("0.51"),
        "midpoint": Decimal("0.500"),
        "spread": Decimal("0.020"),
        "slippage_estimate": Decimal("0.004"),
    }
    values.update(overrides)
    return PaperFill(**values)


def record_from(packet=None, fill=None, **overrides):
    values = {
        "packet": packet or complete_packet(),
        "fill": fill or complete_fill(),
        "decision_timestamp": datetime(2026, 6, 13, 12, 31),
        "order_book_raw_archive_path": "data/raw/clob/book-111.json",
        "order_book_raw_payload_sha256": "b" * 64,
        "account_equity_before_trade": Decimal("10000"),
        "sizing_limiter": "max_executable_size",
        "planned_exit_rule": "Mark at executable bid on review.",
    }
    values.update(overrides)
    return PaperTradeRecord.from_packet_and_fill(**values)


def packet_at(minute: int, **overrides):
    values = {"created_at": datetime(2026, 6, 13, 12, minute, tzinfo=UTC)}
    values.update(overrides)
    return complete_packet(**values)


def test_build_paper_portfolio_opens_long_position_from_buy_record():
    record = record_from()

    portfolio = build_paper_portfolio(
        [record],
        starting_cash=Decimal("10000"),
    )

    assert portfolio.starting_cash == Decimal("10000")
    assert portfolio.cash_balance == Decimal("9948.600")
    assert portfolio.realized_pnl == Decimal("0")
    assert len(portfolio.positions) == 1
    position = portfolio.positions[0]
    assert position.source_packet_ids == (record.packet_id,)
    assert position.condition_id == "0xabc"
    assert position.token_id == "111"
    assert position.market_slug == "example-market"
    assert position.market_url == "https://polymarket.com/event/example-market"
    assert position.question == "Will the example resolve yes?"
    assert position.outcome_name == "Yes"
    assert position.strategy_type == "market_quality"
    assert position.risk_tags == ("liquidity",)
    assert position.rule_text_hash
    assert position.resolution_source == "Example source"
    assert position.market_raw_archive_path == "data/raw/gamma/markets.json"
    assert position.last_order_book_raw_archive_path == "data/raw/clob/book-111.json"
    assert position.last_order_book_raw_payload_sha256 == "b" * 64
    assert position.last_order_book_snapshot_sha256 == "a" * 64
    assert position.opened_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert position.updated_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert position.open_size == Decimal("100")
    assert position.cost_basis == Decimal("51.400")
    assert position.average_entry_price == Decimal("0.514")
    assert position.realized_pnl == Decimal("0")
    assert position.entry_trade_count == 1
    assert position.exit_trade_count == 0


def test_build_paper_portfolio_uses_filled_size_not_requested_size():
    partial_buy = record_from(
        fill=complete_fill(
            requested_size=Decimal("100"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("60"),
            average_price=Decimal("0.510"),
            worst_price=Decimal("0.51"),
        )
    )

    portfolio = build_paper_portfolio([partial_buy], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("9979.600")
    assert portfolio.positions[0].open_size == Decimal("40")
    assert portfolio.positions[0].cost_basis == Decimal("20.400")
    assert portfolio.positions[0].average_entry_price == Decimal("0.510")


def test_build_paper_portfolio_replays_partial_sell_and_realized_pnl():
    buy = record_from()
    sell = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("40"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.600"),
            worst_price=Decimal("0.60"),
        ),
        decision_timestamp=datetime(2026, 6, 13, 12, 32),
        order_book_raw_archive_path="data/raw/clob/book-111-sell.json",
        order_book_raw_payload_sha256="c" * 64,
    )

    portfolio = build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("9972.600")
    assert portfolio.realized_pnl == Decimal("3.440")
    assert len(portfolio.positions) == 1
    assert portfolio.positions[0].open_size == Decimal("60")
    assert portfolio.positions[0].cost_basis == Decimal("30.840")
    assert portfolio.positions[0].average_entry_price == Decimal("0.514")
    assert portfolio.positions[0].realized_pnl == Decimal("3.440")
    assert portfolio.positions[0].entry_trade_count == 1
    assert portfolio.positions[0].exit_trade_count == 1
    assert portfolio.positions[0].source_packet_ids == (buy.packet_id, sell.packet_id)
    assert portfolio.positions[0].updated_at == datetime(2026, 6, 13, 12, 32, tzinfo=UTC)
    assert (
        portfolio.positions[0].last_order_book_raw_archive_path
        == "data/raw/clob/book-111-sell.json"
    )
    assert portfolio.positions[0].last_order_book_raw_payload_sha256 == "c" * 64
    assert portfolio.positions[0].last_order_book_snapshot_sha256 == "a" * 64


def test_build_paper_portfolio_uses_sell_filled_size_not_requested_size():
    buy = record_from()
    sell = record_from(
        packet=packet_at(32, max_executable_size=Decimal("120")),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("120"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("80"),
            average_price=Decimal("0.600"),
            worst_price=Decimal("0.60"),
        ),
    )

    portfolio = build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("9972.600")
    assert portfolio.realized_pnl == Decimal("3.440")
    assert portfolio.positions[0].open_size == Decimal("60")
    assert portfolio.positions[0].cost_basis == Decimal("30.840")


def test_build_paper_portfolio_relieves_cost_basis_proportionally_not_from_display_average():
    first_buy = record_from(
        fill=complete_fill(
            requested_size=Decimal("4"),
            filled_size=Decimal("4"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.125"),
            worst_price=Decimal("0.13"),
        )
    )
    second_buy = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            requested_size=Decimal("4"),
            filled_size=Decimal("4"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.126"),
            worst_price=Decimal("0.13"),
        ),
    )
    sell = record_from(
        packet=packet_at(33),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("4"),
            filled_size=Decimal("4"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.200"),
            worst_price=Decimal("0.20"),
        ),
    )

    portfolio = build_paper_portfolio(
        [first_buy, second_buy, sell],
        starting_cash=Decimal("10000"),
    )

    assert portfolio.cash_balance == Decimal("9999.796")
    assert portfolio.realized_pnl == Decimal("0.298")
    assert portfolio.positions[0].open_size == Decimal("4")
    assert portfolio.positions[0].cost_basis == Decimal("0.502")
    assert portfolio.positions[0].average_entry_price == Decimal("0.126")


def test_build_paper_portfolio_allows_negative_realized_pnl():
    buy = record_from()
    sell = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("40"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.400"),
            worst_price=Decimal("0.40"),
        ),
    )

    portfolio = build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("9964.600")
    assert portfolio.realized_pnl == Decimal("-4.560")
    assert portfolio.positions[0].open_size == Decimal("60")
    assert portfolio.positions[0].cost_basis == Decimal("30.840")
    assert portfolio.positions[0].realized_pnl == Decimal("-4.560")


def test_build_paper_portfolio_omits_fully_closed_positions():
    buy = record_from()
    sell = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("100"),
            filled_size=Decimal("100"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.600"),
            worst_price=Decimal("0.60"),
        ),
    )

    portfolio = build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))

    assert portfolio.cash_balance == Decimal("10008.600")
    assert portfolio.realized_pnl == Decimal("8.600")
    assert portfolio.positions == ()


def test_build_paper_portfolio_rejects_sell_before_buy():
    sell = record_from(fill=complete_fill(side="sell"))

    with pytest.raises(ValueError, match="sell.*open position"):
        build_paper_portfolio([sell], starting_cash=Decimal("10000"))


def test_build_paper_portfolio_rejects_oversell():
    buy = record_from(
        fill=complete_fill(
            requested_size=Decimal("40"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.510"),
            worst_price=Decimal("0.51"),
        )
    )
    sell = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("50"),
            filled_size=Decimal("50"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.600"),
            worst_price=Decimal("0.60"),
        ),
    )

    with pytest.raises(ValueError, match="sell.*open_size"):
        build_paper_portfolio([buy, sell], starting_cash=Decimal("10000"))


def test_build_paper_portfolio_rejects_insufficient_cash_for_buy():
    with pytest.raises(ValueError, match="cash"):
        build_paper_portfolio([record_from()], starting_cash=Decimal("10"))


def test_build_paper_portfolio_unions_risk_tags_for_same_token_records():
    first = record_from()
    second = record_from(
        packet=packet_at(32, risk_tags=("event-risk",)),
        fill=complete_fill(
            requested_size=Decimal("10"),
            filled_size=Decimal("10"),
            unfilled_size=Decimal("0"),
        ),
    )

    portfolio = build_paper_portfolio([first, second], starting_cash=Decimal("10000"))

    assert portfolio.positions[0].risk_tags == ("liquidity", "event-risk")


def test_build_paper_portfolio_returns_empty_portfolio_for_no_records():
    portfolio = build_paper_portfolio([], starting_cash=Decimal("10000"))

    assert portfolio.starting_cash == Decimal("10000")
    assert portfolio.cash_balance == Decimal("10000")
    assert portfolio.realized_pnl == Decimal("0")
    assert portfolio.positions == ()


def test_build_paper_portfolio_rejects_duplicate_packet_id():
    record = record_from()

    with pytest.raises(ValueError, match="duplicate.*packet_id"):
        build_paper_portfolio([record, record], starting_cash=Decimal("10000"))


def test_mark_paper_nav_uses_bid_side_exit_depth_for_longs():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("0.50"), Decimal("60")),
            OrderBookLevel(Decimal("0.49"), Decimal("40")),
        ),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, 0, 0),
    )

    assert snapshot.marked_at == datetime(2026, 6, 14, tzinfo=UTC)
    assert snapshot.cash_balance == Decimal("9948.600")
    assert snapshot.realized_pnl == Decimal("0")
    assert snapshot.total_cost_basis == Decimal("51.400")
    assert snapshot.exit_nav == Decimal("9998.200")
    assert snapshot.midpoint_nav == Decimal("9999.600")
    assert snapshot.unrealized_exit_pnl == Decimal("-1.800")
    assert snapshot.paper_only is True
    assert len(snapshot.marks) == 1
    mark = snapshot.marks[0]
    assert mark.token_id == "111"
    assert mark.open_size == Decimal("100")
    assert mark.cost_basis == Decimal("51.400")
    assert mark.average_entry_price == Decimal("0.514")
    assert mark.order_book_captured_at == datetime(2026, 6, 14, tzinfo=UTC)
    assert len(mark.order_book_snapshot_sha256) == 64
    assert mark.exit_filled_size == Decimal("100")
    assert mark.exit_unfilled_size == Decimal("0")
    assert mark.exit_average_price == Decimal("0.496")
    assert mark.exit_worst_price == Decimal("0.49")
    assert mark.exit_value == Decimal("49.600")
    assert mark.midpoint_price == Decimal("0.510")
    assert mark.midpoint_value == Decimal("51.000")
    assert mark.best_bid == Decimal("0.50")
    assert mark.best_ask == Decimal("0.52")
    assert mark.spread == Decimal("0.020")
    assert mark.slippage_estimate == Decimal("0.004")
    assert mark.mark_status == "fully_executable"


def test_mark_paper_nav_uses_exact_bid_walk_notional_not_quantized_average_product():
    buy = record_from(
        fill=complete_fill(
            requested_size=Decimal("3"),
            filled_size=Decimal("3"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.100"),
            worst_price=Decimal("0.10"),
        )
    )
    portfolio = build_paper_portfolio([buy], starting_cash=Decimal("100"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(
            OrderBookLevel(Decimal("0.20"), Decimal("2")),
            OrderBookLevel(Decimal("0.10"), Decimal("1")),
        ),
        asks=(OrderBookLevel(Decimal("0.30"), Decimal("3")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    mark = snapshot.marks[0]
    assert mark.exit_filled_size == Decimal("3")
    assert mark.exit_average_price == Decimal("0.167")
    assert mark.exit_filled_size * mark.exit_average_price == Decimal("0.501")
    assert mark.exit_value == Decimal("0.500")
    assert snapshot.exit_nav == Decimal("100.200")


def test_mark_paper_nav_values_unfilled_exit_depth_at_zero():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.50"), Decimal("25")),),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("9961.100")
    assert snapshot.unrealized_exit_pnl == Decimal("-38.900")
    assert snapshot.marks[0].exit_filled_size == Decimal("25")
    assert snapshot.marks[0].exit_unfilled_size == Decimal("75")
    assert snapshot.marks[0].exit_average_price == Decimal("0.500")
    assert snapshot.marks[0].exit_value == Decimal("12.500")
    assert snapshot.marks[0].mark_status == "partially_executable"


def test_mark_paper_nav_reports_no_exit_depth_without_midpoint_nav():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("9948.600")
    assert snapshot.midpoint_nav is None
    assert snapshot.unrealized_exit_pnl == Decimal("-51.400")
    assert snapshot.marks[0].exit_filled_size == Decimal("0")
    assert snapshot.marks[0].exit_unfilled_size == Decimal("100")
    assert snapshot.marks[0].exit_average_price is None
    assert snapshot.marks[0].exit_worst_price is None
    assert snapshot.marks[0].exit_value == Decimal("0")
    assert snapshot.marks[0].midpoint_price is None
    assert snapshot.marks[0].midpoint_value is None
    assert snapshot.marks[0].mark_status == "no_exit_depth"


def test_mark_paper_nav_rejects_missing_book_for_open_position():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))

    with pytest.raises(ValueError, match="missing.*111"):
        mark_paper_nav(
            portfolio,
            {},
            marked_at=datetime(2026, 6, 14, tzinfo=UTC),
        )


def test_mark_paper_nav_rejects_token_mismatch_book():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="222",
        bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="token_id"):
        mark_paper_nav(
            portfolio,
            {"111": book},
            marked_at=datetime(2026, 6, 14, tzinfo=UTC),
        )


def test_mark_paper_nav_rejects_invalid_public_inputs():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match="portfolio"):
        mark_paper_nav(object(), {"111": book}, marked_at=datetime(2026, 6, 14, tzinfo=UTC))
    with pytest.raises(ValueError, match="mapping"):
        mark_paper_nav(portfolio, "not-books", marked_at=datetime(2026, 6, 14, tzinfo=UTC))
    with pytest.raises(ValueError, match="token id"):
        mark_paper_nav(portfolio, {" ": book}, marked_at=datetime(2026, 6, 14, tzinfo=UTC))
    with pytest.raises(ValueError, match="OrderBookSnapshot"):
        mark_paper_nav(portfolio, {"111": object()}, marked_at=datetime(2026, 6, 14, tzinfo=UTC))


def test_mark_paper_nav_preserves_crossed_book_executable_mark():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.55"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.53"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    snapshot = mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert snapshot.exit_nav == Decimal("10003.600")
    assert snapshot.midpoint_nav == Decimal("10002.600")
    assert snapshot.marks[0].exit_average_price == Decimal("0.550")
    assert snapshot.marks[0].midpoint_price == Decimal("0.540")
    assert snapshot.marks[0].spread == Decimal("-0.020")
    assert snapshot.marks[0].mark_status == "fully_executable"


def test_mark_paper_nav_sorts_multiple_positions_and_requires_all_midpoints_for_midpoint_nav():
    later_sort_record = record_from()
    earlier_sort_packet = packet_at(
        32,
        candidate=ScoredCandidate(
            condition_id="0xaaa",
            token_id="222",
            market_slug="another-market",
            question="Will another market resolve yes?",
            total_score="80.000",
            raw_archive_path="data/raw/gamma/markets-2.json",
        ),
        market_url="https://polymarket.com/event/another-market",
        outcome_name="Yes",
    )
    earlier_sort_record = record_from(
        packet=earlier_sort_packet,
        fill=complete_fill(
            token_id="222",
            requested_size=Decimal("100"),
            filled_size=Decimal("100"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.200"),
            worst_price=Decimal("0.20"),
        ),
        order_book_raw_archive_path="data/raw/clob/book-222.json",
        order_book_raw_payload_sha256="c" * 64,
    )

    portfolio = build_paper_portfolio(
        [later_sort_record, earlier_sort_record],
        starting_cash=Decimal("10000"),
    )
    assert [position.token_id for position in portfolio.positions] == ["222", "111"]

    snapshot = mark_paper_nav(
        portfolio,
        {
            "111": OrderBookSnapshot(
                token_id="111",
                bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
                asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            ),
            "222": OrderBookSnapshot(
                token_id="222",
                bids=(),
                asks=(OrderBookLevel(Decimal("0.22"), Decimal("100")),),
                captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            ),
        },
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    assert [mark.token_id for mark in snapshot.marks] == ["222", "111"]
    assert snapshot.exit_nav == Decimal("9978.600")
    assert snapshot.midpoint_nav is None
    assert snapshot.total_cost_basis == Decimal("71.400")
    assert snapshot.unrealized_exit_pnl == Decimal("-21.400")


def executable_snapshot():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.50"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.52"), Decimal("100")),),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )
    return mark_paper_nav(
        portfolio,
        {"111": book},
        marked_at=datetime(2026, 6, 14, tzinfo=UTC),
    )


def test_paper_nav_log_appends_jsonl_snapshot(tmp_path):
    snapshot = executable_snapshot()
    log = PaperNavLog(path=tmp_path / "nav.jsonl")

    log.append(snapshot)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"cash_balance"')
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["marked_at"] == "2026-06-14T00:00:00+00:00"
    assert stored["starting_cash"] == "10000"
    assert stored["cash_balance"] == "9948.600"
    assert stored["exit_nav"] == "9998.600"
    assert stored["midpoint_nav"] == "9999.600"
    assert stored["total_cost_basis"] == "51.400"
    assert stored["unrealized_exit_pnl"] == "-1.400"
    assert stored["marks"][0]["token_id"] == "111"
    assert stored["marks"][0]["order_book_captured_at"] == "2026-06-14T00:00:00+00:00"
    assert stored["marks"][0]["exit_average_price"] == "0.500"
    assert stored["marks"][0]["order_book_snapshot_sha256"]


def test_paper_nav_log_appends_without_overwriting(tmp_path):
    log = PaperNavLog(path=str(tmp_path / "nested" / "nav.jsonl"))
    first = executable_snapshot()
    second = replace(
        executable_snapshot(),
        marked_at=datetime(2026, 6, 15, tzinfo=UTC),
    )

    log.append(first)
    log.append(second)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["marked_at"] == "2026-06-14T00:00:00+00:00"
    assert json.loads(lines[1])["marked_at"] == "2026-06-15T00:00:00+00:00"


def test_paper_nav_log_rejects_invalid_paths(tmp_path):
    with pytest.raises(ValueError, match="path"):
        PaperNavLog(path=object())
    with pytest.raises(ValueError, match="path"):
        PaperNavLog(path="")
    with pytest.raises(ValueError, match="path"):
        PaperNavLog(path=tmp_path)
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("already a file", encoding="utf-8")
    with pytest.raises(ValueError, match="path"):
        PaperNavLog(path=parent_file / "nav.jsonl")


def test_paper_nav_log_rejects_invalid_public_input(tmp_path):
    log = PaperNavLog(path=tmp_path / "nav.jsonl")

    with pytest.raises(ValueError, match="snapshot"):
        log.append(object())

    assert not log.path.exists()


def test_paper_nav_log_rejects_non_finite_decimal_before_open(tmp_path):
    snapshot = executable_snapshot()
    object.__setattr__(snapshot, "cash_balance", Decimal("NaN"))
    log = PaperNavLog(path=tmp_path / "nav.jsonl")

    with pytest.raises(ValueError, match="finite"):
        log.append(snapshot)

    assert not log.path.exists()


def test_paper_nav_log_preserves_existing_file_when_serialization_fails(tmp_path):
    snapshot = executable_snapshot()
    object.__setattr__(snapshot, "cash_balance", Decimal("NaN"))
    path = tmp_path / "nav.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")
    log = PaperNavLog(path=path)

    with pytest.raises(ValueError, match="finite"):
        log.append(snapshot)

    assert path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_positions_dataclasses_are_frozen():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))
    snapshot = executable_snapshot()

    with pytest.raises(FrozenInstanceError):
        portfolio.cash_balance = Decimal("1")
    with pytest.raises(FrozenInstanceError):
        portfolio.positions[0].open_size = Decimal("1")
    with pytest.raises(FrozenInstanceError):
        snapshot.exit_nav = Decimal("1")
    with pytest.raises(FrozenInstanceError):
        snapshot.marks[0].exit_value = Decimal("1")


@pytest.mark.parametrize(
    "starting_cash",
    [Decimal("0"), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")],
)
def test_build_paper_portfolio_rejects_invalid_starting_cash(starting_cash):
    with pytest.raises(ValueError, match="starting_cash"):
        build_paper_portfolio([record_from()], starting_cash=starting_cash)


def test_build_paper_portfolio_rejects_invalid_public_inputs():
    with pytest.raises(ValueError, match="records"):
        build_paper_portfolio("not-records", starting_cash=Decimal("10000"))
    with pytest.raises(ValueError, match="record"):
        build_paper_portfolio([object()], starting_cash=Decimal("10000"))
    with pytest.raises(ValueError, match="starting_cash"):
        build_paper_portfolio([record_from()], starting_cash="10000")


@pytest.mark.parametrize("field_name", ["fill_average_price", "fill_worst_price"])
def test_build_paper_portfolio_rejects_direct_records_missing_fill_prices(field_name):
    record = replace(record_from(), **{field_name: None})

    with pytest.raises(ValueError, match=field_name):
        build_paper_portfolio([record], starting_cash=Decimal("10000"))


def test_build_paper_portfolio_rejects_inconsistent_fill_status():
    with pytest.raises(ValueError, match="fill_status"):
        build_paper_portfolio(
            [replace(record_from(), fill_status="filled")],
            starting_cash=Decimal("10000"),
        )

    partial_record = record_from(
        fill=complete_fill(
            requested_size=Decimal("100"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("60"),
            average_price=Decimal("0.510"),
            worst_price=Decimal("0.51"),
        )
    )
    with pytest.raises(ValueError, match="fill_status"):
        build_paper_portfolio(
            [replace(partial_record, fill_status="complete")],
            starting_cash=Decimal("10000"),
        )


def test_build_paper_portfolio_rejects_blank_market_url_from_direct_record():
    record = replace(record_from(), market_url="   ")

    with pytest.raises(ValueError, match="market_url"):
        build_paper_portfolio([record], starting_cash=Decimal("10000"))


def test_build_paper_portfolio_rejects_noncanonical_risk_tags():
    record = record_from(packet=complete_packet(risk_tags=("liquidity ",)))

    with pytest.raises(ValueError, match="risk_tags"):
        build_paper_portfolio([record], starting_cash=Decimal("10000"))


def test_build_paper_portfolio_rejects_inconsistent_token_metadata():
    first = record_from()
    changed_packet = packet_at(32, market_url="https://polymarket.com/event/changed")
    second = record_from(packet=changed_packet)

    with pytest.raises(ValueError, match="metadata"):
        build_paper_portfolio([first, second], starting_cash=Decimal("10000"))


def test_build_paper_portfolio_rejects_metadata_change_after_full_close_and_reopen():
    buy = record_from()
    close = record_from(
        packet=packet_at(32),
        fill=complete_fill(
            side="sell",
            requested_size=Decimal("100"),
            filled_size=Decimal("100"),
            unfilled_size=Decimal("0"),
            average_price=Decimal("0.600"),
            worst_price=Decimal("0.60"),
        ),
    )
    reopen = record_from(
        packet=packet_at(33, market_url="https://polymarket.com/event/changed"),
        fill=complete_fill(),
    )

    with pytest.raises(ValueError, match="metadata"):
        build_paper_portfolio([buy, close, reopen], starting_cash=Decimal("10000"))


def test_position_timestamps_normalize_to_utc():
    eastern = timezone(timedelta(hours=-4))
    record = record_from(
        decision_timestamp=datetime(2026, 6, 13, 8, 31, tzinfo=eastern),
    )

    portfolio = build_paper_portfolio([record], starting_cash=Decimal("10000"))

    assert portfolio.positions[0].opened_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert portfolio.positions[0].updated_at == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)


def test_direct_position_construction_rejects_invalid_state():
    position = build_paper_portfolio([record_from()], starting_cash=Decimal("10000")).positions[0]

    with pytest.raises(ValueError, match="open_size"):
        replace(position, open_size=Decimal("0"))
    with pytest.raises(ValueError, match="market_url"):
        replace(position, market_url=" ")
    with pytest.raises(ValueError, match="cost_basis"):
        replace(position, cost_basis=Decimal("100.001"))
    with pytest.raises(ValueError, match="risk_tags"):
        replace(position, risk_tags=("liquidity", " "))
    with pytest.raises(ValueError, match="average_entry_price"):
        replace(position, average_entry_price=Decimal("NaN"))
    with pytest.raises(ValueError, match="average_entry_price"):
        replace(position, average_entry_price=None)
    with pytest.raises(ValueError, match="SHA-256|sha256"):
        replace(position, last_order_book_raw_payload_sha256="A" * 64)
    with pytest.raises(ValueError, match="SHA-256|sha256"):
        replace(position, last_order_book_snapshot_sha256="not-hex")


def test_direct_nav_snapshot_rejects_invalid_state():
    snapshot = executable_snapshot()

    with pytest.raises(ValueError, match="paper_only"):
        replace(snapshot, paper_only=False)
    with pytest.raises(ValueError, match="marks"):
        replace(snapshot, marks=(object(),))
    with pytest.raises(ValueError, match="exit_nav"):
        replace(snapshot, exit_nav=Decimal("1"))
    with pytest.raises(ValueError, match="total_cost_basis"):
        replace(snapshot, total_cost_basis=Decimal("1"))
    with pytest.raises(ValueError, match="unrealized_exit_pnl"):
        replace(snapshot, unrealized_exit_pnl=Decimal("1"))
    with pytest.raises(ValueError, match="accounting"):
        replace(snapshot, starting_cash=Decimal("9999"))


def test_direct_portfolio_construction_rejects_accounting_identity_break():
    portfolio = build_paper_portfolio([record_from()], starting_cash=Decimal("10000"))

    with pytest.raises(ValueError, match="accounting"):
        replace(portfolio, cash_balance=Decimal("9990"))


def test_direct_nav_snapshot_normalizes_marked_at_to_utc():
    eastern = timezone(timedelta(hours=-4))
    snapshot = replace(
        executable_snapshot(),
        marked_at=datetime(2026, 6, 13, 20, 0, tzinfo=eastern),
    )

    assert snapshot.marked_at == datetime(2026, 6, 14, 0, 0, tzinfo=UTC)


def test_direct_position_mark_rejects_invalid_status():
    mark = executable_snapshot().marks[0]

    with pytest.raises(ValueError, match="mark_status"):
        replace(mark, mark_status="midpoint_only")
    with pytest.raises(ValueError, match="exit_filled_size"):
        replace(mark, exit_filled_size=Decimal("0"), mark_status="fully_executable")
    with pytest.raises(ValueError, match="SHA-256|sha256"):
        replace(mark, order_book_snapshot_sha256="a" * 63)


def test_direct_position_mark_rejects_impossible_binary_values():
    mark = executable_snapshot().marks[0]

    with pytest.raises(ValueError, match="cost_basis"):
        replace(mark, cost_basis=Decimal("100.001"))
    with pytest.raises(ValueError, match="average_entry_price"):
        replace(mark, average_entry_price=None)
    with pytest.raises(ValueError, match="exit_value"):
        replace(
            mark,
            exit_filled_size=Decimal("1"),
            exit_unfilled_size=Decimal("99"),
            exit_value=Decimal("2"),
            exit_average_price=Decimal("0.500"),
            exit_worst_price=Decimal("0.500"),
            mark_status="partially_executable",
        )
    with pytest.raises(ValueError, match="exit_value"):
        replace(
            mark,
            exit_filled_size=Decimal("0"),
            exit_unfilled_size=Decimal("100"),
            exit_average_price=None,
            exit_worst_price=None,
            exit_value=Decimal("1"),
            mark_status="no_exit_depth",
        )
    with pytest.raises(ValueError, match="midpoint_value"):
        replace(mark, midpoint_value=Decimal("100.001"))


def test_direct_position_mark_normalizes_order_book_timestamp_to_utc():
    eastern = timezone(timedelta(hours=-4))
    mark = replace(
        executable_snapshot().marks[0],
        order_book_captured_at=datetime(2026, 6, 13, 20, 0, tzinfo=eastern),
    )

    assert mark.order_book_captured_at == datetime(2026, 6, 14, 0, 0, tzinfo=UTC)


def test_position_mark_validation_uses_exact_decimal_math_under_low_ambient_precision():
    with localcontext(Context(prec=10)):
        mark = PaperPositionMark(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            outcome_name="Yes",
            open_size=Decimal("100000000000000000001"),
            cost_basis=Decimal("0.1"),
            average_entry_price=Decimal("0"),
            order_book_captured_at=datetime(2026, 6, 14, tzinfo=UTC),
            order_book_snapshot_sha256="c" * 64,
            exit_filled_size=Decimal("100000000000000000000"),
            exit_unfilled_size=Decimal("1"),
            exit_average_price=Decimal("1"),
            exit_worst_price=Decimal("1"),
            exit_value=Decimal("100000000000000000000"),
            midpoint_price=None,
            midpoint_value=None,
            best_bid=Decimal("1"),
            best_ask=None,
            spread=None,
            slippage_estimate=Decimal("0"),
            mark_status="partially_executable",
        )

    assert mark.exit_filled_size + mark.exit_unfilled_size == mark.open_size


def test_mark_paper_nav_uses_exact_decimal_math_under_low_ambient_precision():
    open_size = Decimal("123456789012345678901")
    cost_basis = Decimal("0.1")
    position = PaperPosition(
        source_packet_ids=("packet-1",),
        condition_id="0xabc",
        token_id="111",
        market_slug="example-market",
        market_url="https://polymarket.com/event/example-market",
        question="Will the example resolve yes?",
        outcome_name="Yes",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        rule_text_hash="d" * 64,
        resolution_source="Example source",
        market_raw_archive_path="data/raw/gamma/markets.json",
        last_order_book_raw_archive_path="data/raw/clob/book-111.json",
        last_order_book_raw_payload_sha256="e" * 64,
        last_order_book_snapshot_sha256="f" * 64,
        opened_at=datetime(2026, 6, 13, tzinfo=UTC),
        updated_at=datetime(2026, 6, 13, tzinfo=UTC),
        open_size=open_size,
        cost_basis=cost_basis,
        average_entry_price=Decimal("0"),
        realized_pnl=Decimal("0"),
        entry_trade_count=1,
        exit_trade_count=0,
    )
    portfolio = PaperPortfolio(
        starting_cash=cost_basis,
        cash_balance=Decimal("0"),
        realized_pnl=Decimal("0"),
        positions=(position,),
    )
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("1"), open_size),),
        asks=(),
        captured_at=datetime(2026, 6, 14, tzinfo=UTC),
    )

    with localcontext(Context(prec=10)):
        snapshot = mark_paper_nav(
            portfolio,
            {"111": book},
            marked_at=datetime(2026, 6, 14, tzinfo=UTC),
        )

    assert snapshot.exit_nav == open_size
    assert snapshot.unrealized_exit_pnl == Decimal("123456789012345678900.9")
