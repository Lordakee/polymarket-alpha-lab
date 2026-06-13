import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.domain import OrderBookLevel, OrderBookSnapshot
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.paper import (
    PaperFill,
    PaperOrder,
    simulate_order_book_fill,
)
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet


def complete_packet(
    max_executable_size: Decimal = Decimal("100"),
    *,
    created_at: datetime = datetime(2026, 6, 13, 12, 30, tzinfo=UTC),
):
    return build_research_packet(
        candidate=ScoredCandidate(
            condition_id="0xabc",
            token_id="111",
            market_slug="example-market",
            question="Will the example resolve yes?",
            total_score="78.500",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        created_at=created_at,
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
        max_executable_size=max_executable_size,
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
    requested_size: Decimal = Decimal("100"),
    order_book_captured_at: datetime = datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC),
    order_book_snapshot_sha256: str = "a" * 64,
    filled_size: Decimal = Decimal("100"),
    unfilled_size: Decimal = Decimal("0"),
    average_price: Decimal | None = Decimal("0.514"),
    worst_price: Decimal | None = Decimal("0.52"),
    best_bid: Decimal | None = Decimal("0.49"),
    best_ask: Decimal | None = Decimal("0.51"),
    midpoint: Decimal | None = Decimal("0.500"),
    spread: Decimal | None = Decimal("0.020"),
    slippage_estimate: Decimal | None = Decimal("0.004"),
):
    return PaperFill(
        token_id=token_id,
        side=side,
        requested_size=requested_size,
        order_book_captured_at=order_book_captured_at,
        order_book_snapshot_sha256=order_book_snapshot_sha256,
        filled_size=filled_size,
        unfilled_size=unfilled_size,
        average_price=average_price,
        worst_price=worst_price,
        best_bid=best_bid,
        best_ask=best_ask,
        midpoint=midpoint,
        spread=spread,
        slippage_estimate=slippage_estimate,
    )


def record_from(packet, fill):
    return PaperTradeRecord.from_packet_and_fill(
        packet=packet,
        fill=fill,
        decision_timestamp=datetime(2026, 6, 13, 12, 31),
        order_book_raw_archive_path="data/raw/clob/book-111.json",
        order_book_raw_payload_sha256="b" * 64,
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Mark at executable bid on review.",
    )


def test_paper_trade_journal_appends_jsonl_record(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")
    packet = complete_packet()
    fill = complete_fill()
    record = record_from(packet, fill)

    assert record.fill_midpoint == Decimal("0.500")
    assert record.fill_spread == Decimal("0.020")

    journal.append(record)

    lines = journal.path.read_text().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith('{"account_equity_before_trade"')
    stored = json.loads(lines[0])
    assert stored["packet_id"] == packet.packet_id
    assert stored["packet_created_at"] == "2026-06-13T12:30:00+00:00"
    assert stored["decision_timestamp_utc"] == "2026-06-13T12:31:00+00:00"
    assert stored["condition_id"] == "0xabc"
    assert stored["token_id"] == "111"
    assert stored["market_slug"] == "example-market"
    assert stored["market_url"] == "https://polymarket.com/event/example-market"
    assert stored["question"] == "Will the example resolve yes?"
    assert stored["outcome_name"] == "Yes"
    assert stored["strategy_type"] == "market_quality"
    assert stored["source_score"] == "78.500"
    assert stored["market_raw_archive_path"] == "data/raw/gamma/markets.json"
    assert stored["order_book_raw_archive_path"] == "data/raw/clob/book-111.json"
    assert stored["order_book_raw_payload_sha256"] == "b" * 64
    assert stored["order_book_snapshot_sha256"] == "a" * 64
    assert stored["risk_tags"] == ["liquidity"]
    assert stored["rule_text_hash"] == packet.rule_text_hash
    assert stored["resolution_source"] == "Example source"
    assert stored["model_probability"] == "0.56"
    assert stored["confidence"] == "0.60"
    assert stored["research_bid"] == "0.50"
    assert stored["research_ask"] == "0.52"
    assert stored["research_midpoint"] == "0.51"
    assert stored["research_expected_entry_price"] == "0.514"
    assert stored["research_fair_value_estimate"] == "0.56"
    assert stored["research_theoretical_edge"] == "0.046"
    assert stored["research_spread"] == "0.02"
    assert stored["research_slippage_estimate"] == "0.004"
    assert stored["research_cost_adjusted_edge"] == "0.026"
    assert stored["max_executable_size"] == "100"
    assert stored["order_side"] == "buy"
    assert stored["order_requested_size"] == "100"
    assert stored["fill_filled_size"] == "100"
    assert stored["fill_unfilled_size"] == "0"
    assert stored["fill_status"] == "complete"
    assert stored["fill_average_price"] == "0.514"
    assert stored["fill_worst_price"] == "0.52"
    assert stored["fill_best_bid"] == "0.49"
    assert stored["fill_best_ask"] == "0.51"
    assert stored["fill_midpoint"] == "0.500"
    assert stored["fill_spread"] == "0.020"
    assert stored["fill_slippage_estimate"] == "0.004"
    assert stored["order_book_captured_at"] == "2026-06-13T12:30:30+00:00"
    assert stored["account_equity_before_trade"] == "10000"
    assert stored["sizing_limiter"] == "max_executable_size"
    assert stored["planned_exit_rule"] == "Mark at executable bid on review."
    assert stored["thesis"] == "Tight spread and clear rules."
    assert stored["invalidating_conditions"] == "Spread widens."


def test_paper_trade_journal_appends_without_overwriting(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")
    first = record_from(complete_packet(), complete_fill(order_book_snapshot_sha256="a" * 64))
    second = record_from(complete_packet(), complete_fill(order_book_snapshot_sha256="b" * 64))

    journal.append(first)
    journal.append(second)

    lines = journal.path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["order_book_snapshot_sha256"] == "a" * 64
    assert json.loads(lines[1])["order_book_snapshot_sha256"] == "b" * 64


def test_paper_trade_journal_creates_parent_directories(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "nested" / "run" / "paper-trades.jsonl")
    record = record_from(complete_packet(), complete_fill())

    journal.append(record)

    assert journal.path.exists()
    assert len(journal.path.read_text().splitlines()) == 1


def test_paper_trade_record_normalizes_decision_and_order_book_timestamps():
    eastern = timezone(timedelta(hours=-4))
    fill = complete_fill(
        order_book_captured_at=datetime(2026, 6, 13, 8, 30, 30, tzinfo=eastern)
    )

    record = PaperTradeRecord.from_packet_and_fill(
        packet=complete_packet(
            created_at=datetime(2026, 6, 13, 8, 30, tzinfo=eastern)
        ),
        fill=fill,
        decision_timestamp=datetime(2026, 6, 13, 8, 31, tzinfo=eastern),
        order_book_raw_archive_path="data/raw/clob/book-111.json",
        order_book_raw_payload_sha256="b" * 64,
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Mark at executable bid on review.",
    )

    assert record.packet_created_at == datetime(2026, 6, 13, 12, 30, tzinfo=UTC)
    assert record.decision_timestamp_utc == datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
    assert record.order_book_captured_at == datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC)


def test_paper_trade_record_treats_naive_order_book_timestamp_as_utc():
    record = record_from(
        complete_packet(),
        complete_fill(order_book_captured_at=datetime(2026, 6, 13, 12, 30, 30)),
    )

    assert record.order_book_captured_at == datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC)


def test_paper_trade_record_accepts_partial_fills_with_positive_filled_size():
    record = record_from(
        complete_packet(),
        complete_fill(
            requested_size=Decimal("100"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("60"),
        ),
    )

    assert record.fill_filled_size == Decimal("40")
    assert record.fill_unfilled_size == Decimal("60")
    assert record.fill_status == "partial"


def test_paper_trade_journal_persists_partial_fill_jsonl(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")
    record = record_from(
        complete_packet(),
        complete_fill(
            requested_size=Decimal("100"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("60"),
        ),
    )

    journal.append(record)

    stored = json.loads(journal.path.read_text())
    assert stored["order_requested_size"] == "100"
    assert stored["fill_filled_size"] == "40"
    assert stored["fill_unfilled_size"] == "60"
    assert stored["fill_status"] == "partial"


def test_paper_trade_journal_serializes_optional_fill_quotes_as_null(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")
    record = record_from(
        complete_packet(),
        complete_fill(
            best_bid=None,
            best_ask=None,
            midpoint=None,
            spread=None,
            slippage_estimate=None,
        ),
    )

    journal.append(record)

    stored = json.loads(journal.path.read_text())
    assert stored["fill_best_bid"] is None
    assert stored["fill_best_ask"] is None
    assert stored["fill_midpoint"] is None
    assert stored["fill_spread"] is None
    assert stored["fill_slippage_estimate"] is None


def test_paper_trade_journal_rejects_direct_record_with_non_finite_decimal(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")
    record = replace(
        record_from(complete_packet(), complete_fill()),
        account_equity_before_trade=Decimal("NaN"),
    )

    with pytest.raises(ValueError, match="finite"):
        journal.append(record)

    assert not journal.path.exists()


def test_paper_trade_journal_accepts_sell_fill(tmp_path):
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")
    record = record_from(complete_packet(), complete_fill(side="sell"))

    journal.append(record)

    stored = json.loads(journal.path.read_text())
    assert stored["order_side"] == "sell"
    assert stored["fill_filled_size"] == "100"


def test_paper_trade_journal_persists_crossed_book_fill_metadata(tmp_path):
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.55"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.53"), Decimal("100")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    fill = simulate_order_book_fill(
        PaperOrder(token_id="111", side="buy", size=Decimal("25")),
        book,
    )
    record = record_from(complete_packet(), fill)
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")

    journal.append(record)

    stored = json.loads(journal.path.read_text())
    assert stored["research_spread"] == "0.02"
    assert stored["research_midpoint"] == "0.51"
    assert stored["fill_spread"] == "-0.020"
    assert stored["fill_midpoint"] == "0.540"
    assert stored["fill_average_price"] == "0.530"


def test_paper_trade_journal_persists_simulated_partial_fill_status(tmp_path):
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("100")),),
        asks=(OrderBookLevel(Decimal("0.51"), Decimal("40")),),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    fill = simulate_order_book_fill(
        PaperOrder(token_id="111", side="buy", size=Decimal("100")),
        book,
    )
    record = record_from(complete_packet(), fill)
    journal = PaperTradeJournal(path=tmp_path / "paper-trades.jsonl")

    journal.append(record)

    stored = json.loads(journal.path.read_text())
    assert stored["fill_filled_size"] == "40"
    assert stored["fill_unfilled_size"] == "60"
    assert stored["fill_status"] == "partial"
    assert stored["fill_average_price"] == "0.510"
    assert stored["fill_worst_price"] == "0.51"


def test_paper_trade_record_rejects_simulated_zero_fill():
    book = OrderBookSnapshot(
        token_id="111",
        bids=(OrderBookLevel(Decimal("0.49"), Decimal("100")),),
        asks=(),
        captured_at=datetime(2026, 6, 13, tzinfo=UTC),
    )
    fill = simulate_order_book_fill(
        PaperOrder(token_id="111", side="buy", size=Decimal("100")),
        book,
    )

    with pytest.raises(ValueError, match="positive filled_size"):
        record_from(complete_packet(), fill)


def test_paper_trade_record_rejects_incomplete_packet():
    packet = complete_packet()
    incomplete_packet = build_research_packet(
        candidate=ScoredCandidate(
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            question=packet.question,
            total_score=packet.source_score,
            raw_archive_path="",
        ),
        created_at=packet.created_at,
        market_url=packet.market_url,
        outcome_name=packet.outcome_name,
        strategy_type=packet.strategy_type,
        model_probability=packet.model_probability,
        bid=packet.bid,
        ask=packet.ask,
        midpoint=packet.midpoint,
        expected_entry_price=None,
        fair_value_estimate=packet.fair_value_estimate,
        theoretical_edge=packet.theoretical_edge,
        spread=packet.spread,
        slippage_estimate=packet.slippage_estimate,
        cost_adjusted_edge=packet.cost_adjusted_edge,
        confidence=None,
        max_executable_size=packet.max_executable_size,
        risk_tags=(),
        thesis=packet.thesis,
        invalidating_conditions=packet.invalidating_conditions,
        rule_text=packet.rule_text,
        resolution_source=packet.resolution_source,
    )

    with pytest.raises(ValueError, match="incomplete research packet") as exc:
        record_from(incomplete_packet, complete_fill())
    assert "expected_entry_price" in str(exc.value)
    assert "confidence" in str(exc.value)
    assert "raw_archive_path" in str(exc.value)
    assert "risk_tags" in str(exc.value)


def test_paper_trade_record_rejects_blank_risk_tag():
    packet = complete_packet()
    blank_tag_packet = build_research_packet(
        candidate=ScoredCandidate(
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            question=packet.question,
            total_score=packet.source_score,
            raw_archive_path=packet.raw_archive_path,
        ),
        created_at=packet.created_at,
        market_url=packet.market_url,
        outcome_name=packet.outcome_name,
        strategy_type=packet.strategy_type,
        model_probability=packet.model_probability,
        bid=packet.bid,
        ask=packet.ask,
        midpoint=packet.midpoint,
        expected_entry_price=packet.expected_entry_price,
        fair_value_estimate=packet.fair_value_estimate,
        theoretical_edge=packet.theoretical_edge,
        spread=packet.spread,
        slippage_estimate=packet.slippage_estimate,
        cost_adjusted_edge=packet.cost_adjusted_edge,
        confidence=packet.confidence,
        max_executable_size=packet.max_executable_size,
        risk_tags=("liquidity", "   "),
        thesis=packet.thesis,
        invalidating_conditions=packet.invalidating_conditions,
        rule_text=packet.rule_text,
        resolution_source=packet.resolution_source,
    )

    with pytest.raises(ValueError, match="risk_tags"):
        record_from(blank_tag_packet, complete_fill())


def test_paper_trade_record_rejects_blank_market_raw_archive_path():
    packet = complete_packet()
    blank_archive_packet = build_research_packet(
        candidate=ScoredCandidate(
            condition_id=packet.condition_id,
            token_id=packet.token_id,
            market_slug=packet.market_slug,
            question=packet.question,
            total_score=packet.source_score,
            raw_archive_path="   ",
        ),
        created_at=packet.created_at,
        market_url=packet.market_url,
        outcome_name=packet.outcome_name,
        strategy_type=packet.strategy_type,
        model_probability=packet.model_probability,
        bid=packet.bid,
        ask=packet.ask,
        midpoint=packet.midpoint,
        expected_entry_price=packet.expected_entry_price,
        fair_value_estimate=packet.fair_value_estimate,
        theoretical_edge=packet.theoretical_edge,
        spread=packet.spread,
        slippage_estimate=packet.slippage_estimate,
        cost_adjusted_edge=packet.cost_adjusted_edge,
        confidence=packet.confidence,
        max_executable_size=packet.max_executable_size,
        risk_tags=packet.risk_tags,
        thesis=packet.thesis,
        invalidating_conditions=packet.invalidating_conditions,
        rule_text=packet.rule_text,
        resolution_source=packet.resolution_source,
    )

    with pytest.raises(ValueError, match="raw_archive_path"):
        record_from(blank_archive_packet, complete_fill())


@pytest.mark.parametrize(
    ("fill", "account_equity_before_trade", "match"),
    [
        (
            complete_fill(filled_size=Decimal("0"), unfilled_size=Decimal("100")),
            Decimal("10000"),
            "positive filled_size",
        ),
        (
            complete_fill(
                requested_size=Decimal("101"),
                filled_size=Decimal("101"),
                unfilled_size=Decimal("0"),
            ),
            Decimal("10000"),
            "max_executable_size",
        ),
        (
            complete_fill(
                requested_size=Decimal("101"),
                filled_size=Decimal("40"),
                unfilled_size=Decimal("61"),
            ),
            Decimal("10000"),
            "requested_size",
        ),
        (complete_fill(), Decimal("0"), "account_equity_before_trade"),
        (complete_fill(), Decimal("-1"), "account_equity_before_trade"),
    ],
)
def test_paper_trade_record_rejects_invalid_trade_inputs(
    fill, account_equity_before_trade, match
):
    with pytest.raises(ValueError, match=match):
        PaperTradeRecord.from_packet_and_fill(
            packet=complete_packet(),
            fill=fill,
            decision_timestamp=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            order_book_raw_archive_path="data/raw/clob/book-111.json",
            order_book_raw_payload_sha256="b" * 64,
            account_equity_before_trade=account_equity_before_trade,
            sizing_limiter="max_executable_size",
            planned_exit_rule="Mark at executable bid on review.",
        )


@pytest.mark.parametrize(
    ("packet", "fill", "account_equity_before_trade", "match"),
    [
        (
            complete_packet(max_executable_size=Decimal("Infinity")),
            complete_fill(),
            Decimal("10000"),
            "max_executable_size",
        ),
        (
            complete_packet(max_executable_size=Decimal("NaN")),
            complete_fill(),
            Decimal("10000"),
            "max_executable_size",
        ),
        (
            complete_packet(max_executable_size=Decimal("-Infinity")),
            complete_fill(),
            Decimal("10000"),
            "max_executable_size",
        ),
        (
            replace(complete_packet(), model_probability=Decimal("NaN")),
            complete_fill(),
            Decimal("10000"),
            "model_probability",
        ),
        (
            replace(complete_packet(), confidence=Decimal("Infinity")),
            complete_fill(),
            Decimal("10000"),
            "confidence",
        ),
        (
            replace(complete_packet(), bid=Decimal("-Infinity")),
            complete_fill(),
            Decimal("10000"),
            "bid",
        ),
        (
            replace(complete_packet(), ask=Decimal("NaN")),
            complete_fill(),
            Decimal("10000"),
            "ask",
        ),
        (
            replace(complete_packet(), midpoint=Decimal("Infinity")),
            complete_fill(),
            Decimal("10000"),
            "midpoint",
        ),
        (
            replace(complete_packet(), expected_entry_price=Decimal("NaN")),
            complete_fill(),
            Decimal("10000"),
            "expected_entry_price",
        ),
        (
            replace(complete_packet(), fair_value_estimate=Decimal("Infinity")),
            complete_fill(),
            Decimal("10000"),
            "fair_value_estimate",
        ),
        (
            replace(complete_packet(), theoretical_edge=Decimal("NaN")),
            complete_fill(),
            Decimal("10000"),
            "theoretical_edge",
        ),
        (
            replace(complete_packet(), slippage_estimate=Decimal("Infinity")),
            complete_fill(),
            Decimal("10000"),
            "slippage_estimate",
        ),
        (
            replace(complete_packet(), cost_adjusted_edge=Decimal("NaN")),
            complete_fill(),
            Decimal("10000"),
            "cost_adjusted_edge",
        ),
        (
            complete_packet(),
            complete_fill(requested_size=Decimal("NaN")),
            Decimal("10000"),
            "requested_size",
        ),
        (
            complete_packet(),
            complete_fill(filled_size=Decimal("Infinity")),
            Decimal("10000"),
            "filled_size",
        ),
        (
            complete_packet(),
            complete_fill(unfilled_size=Decimal("NaN")),
            Decimal("10000"),
            "unfilled_size",
        ),
        (
            complete_packet(),
            complete_fill(average_price=Decimal("NaN")),
            Decimal("10000"),
            "fill_average_price",
        ),
        (
            complete_packet(),
            complete_fill(worst_price=Decimal("NaN")),
            Decimal("10000"),
            "fill_worst_price",
        ),
        (
            complete_packet(),
            complete_fill(best_bid=Decimal("NaN")),
            Decimal("10000"),
            "fill_best_bid",
        ),
        (
            complete_packet(),
            complete_fill(best_ask=Decimal("Infinity")),
            Decimal("10000"),
            "fill_best_ask",
        ),
        (
            complete_packet(),
            complete_fill(midpoint=Decimal("-Infinity")),
            Decimal("10000"),
            "fill_midpoint",
        ),
        (
            complete_packet(),
            complete_fill(spread=Decimal("Infinity")),
            Decimal("10000"),
            "fill_spread",
        ),
        (
            complete_packet(),
            complete_fill(slippage_estimate=Decimal("NaN")),
            Decimal("10000"),
            "fill_slippage_estimate",
        ),
        (
            complete_packet(),
            complete_fill(),
            Decimal("Infinity"),
            "account_equity_before_trade",
        ),
        (
            complete_packet(),
            complete_fill(),
            Decimal("NaN"),
            "account_equity_before_trade",
        ),
    ],
)
def test_paper_trade_record_rejects_non_finite_decimals(
    packet, fill, account_equity_before_trade, match
):
    with pytest.raises(ValueError, match=match):
        PaperTradeRecord.from_packet_and_fill(
            packet=packet,
            fill=fill,
            decision_timestamp=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            order_book_raw_archive_path="data/raw/clob/book-111.json",
            order_book_raw_payload_sha256="b" * 64,
            account_equity_before_trade=account_equity_before_trade,
            sizing_limiter="max_executable_size",
            planned_exit_rule="Mark at executable bid on review.",
        )


@pytest.mark.parametrize(
    (
        "fill",
        "order_book_raw_archive_path",
        "order_book_raw_payload_sha256",
        "sizing_limiter",
        "planned_exit_rule",
        "match",
    ),
    [
        (
            replace(complete_fill(), token_id="222"),
            "data/raw/clob/book-111.json",
            "b" * 64,
            "max_executable_size",
            "Exit rule.",
            "token_id",
        ),
        (
            complete_fill(),
            "",
            "b" * 64,
            "max_executable_size",
            "Exit rule.",
            "order_book_raw_archive_path",
        ),
        (
            complete_fill(),
            "   ",
            "b" * 64,
            "max_executable_size",
            "Exit rule.",
            "order_book_raw_archive_path",
        ),
        (
            complete_fill(),
            "data/raw/clob/book-111.json",
            "not-hex",
            "max_executable_size",
            "Exit rule.",
            "order_book_raw_payload_sha256",
        ),
        (
            complete_fill(),
            "data/raw/clob/book-111.json",
            "b" * 63,
            "max_executable_size",
            "Exit rule.",
            "order_book_raw_payload_sha256",
        ),
        (
            complete_fill(),
            "data/raw/clob/book-111.json",
            "B" * 64,
            "max_executable_size",
            "Exit rule.",
            "order_book_raw_payload_sha256",
        ),
        (
            complete_fill(order_book_snapshot_sha256=""),
            "data/raw/clob/book-111.json",
            "b" * 64,
            "max_executable_size",
            "Exit rule.",
            "order_book_snapshot_sha256",
        ),
        (
            complete_fill(order_book_snapshot_sha256="not-hex"),
            "data/raw/clob/book-111.json",
            "b" * 64,
            "max_executable_size",
            "Exit rule.",
            "order_book_snapshot_sha256",
        ),
        (
            complete_fill(order_book_snapshot_sha256="a" * 63),
            "data/raw/clob/book-111.json",
            "b" * 64,
            "max_executable_size",
            "Exit rule.",
            "order_book_snapshot_sha256",
        ),
        (
            complete_fill(order_book_snapshot_sha256="A" * 64),
            "data/raw/clob/book-111.json",
            "b" * 64,
            "max_executable_size",
            "Exit rule.",
            "order_book_snapshot_sha256",
        ),
        (
            complete_fill(),
            "data/raw/clob/book-111.json",
            "b" * 64,
            "",
            "Exit rule.",
            "sizing_limiter",
        ),
        (
            complete_fill(),
            "data/raw/clob/book-111.json",
            "b" * 64,
            "   ",
            "Exit rule.",
            "sizing_limiter",
        ),
        (
            complete_fill(),
            "data/raw/clob/book-111.json",
            "b" * 64,
            "max_executable_size",
            "",
            "planned_exit_rule",
        ),
        (
            complete_fill(),
            "data/raw/clob/book-111.json",
            "b" * 64,
            "max_executable_size",
            "   ",
            "planned_exit_rule",
        ),
    ],
)
def test_paper_trade_record_rejects_invalid_journal_boundaries(
    fill,
    order_book_raw_archive_path,
    order_book_raw_payload_sha256,
    sizing_limiter,
    planned_exit_rule,
    match,
):
    with pytest.raises(ValueError, match=match):
        PaperTradeRecord.from_packet_and_fill(
            packet=complete_packet(),
            fill=fill,
            decision_timestamp=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            order_book_raw_archive_path=order_book_raw_archive_path,
            order_book_raw_payload_sha256=order_book_raw_payload_sha256,
            account_equity_before_trade=Decimal("10000"),
            sizing_limiter=sizing_limiter,
            planned_exit_rule=planned_exit_rule,
        )


@pytest.mark.parametrize(
    ("fill", "match"),
    [
        (complete_fill(side="hold"), "side"),
        (complete_fill(requested_size=Decimal("0")), "requested_size"),
        (complete_fill(filled_size=Decimal("-1")), "filled_size"),
        (complete_fill(unfilled_size=Decimal("-1")), "unfilled_size"),
        (
            complete_fill(filled_size=Decimal("40"), unfilled_size=Decimal("50")),
            "fill accounting",
        ),
        (complete_fill(average_price=None), "average_price"),
        (complete_fill(worst_price=None), "worst_price"),
    ],
)
def test_paper_trade_record_rejects_impossible_fill_inputs(fill, match):
    with pytest.raises(ValueError, match=match):
        PaperTradeRecord.from_packet_and_fill(
            packet=complete_packet(),
            fill=fill,
            decision_timestamp=datetime(2026, 6, 13, 12, 31, tzinfo=UTC),
            order_book_raw_archive_path="data/raw/clob/book-111.json",
            order_book_raw_payload_sha256="b" * 64,
            account_equity_before_trade=Decimal("10000"),
            sizing_limiter="max_executable_size",
            planned_exit_rule="Mark at executable bid on review.",
        )
