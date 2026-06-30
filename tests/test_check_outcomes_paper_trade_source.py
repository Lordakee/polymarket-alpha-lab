from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
import re
from typing import Any

import pytest

from polymarket_alpha_lab.check_outcomes_paper_trade_source import (
    load_check_outcomes_paper_trade_records,
)
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.supabase_paper_trade_journal_config import (
    SupabasePaperTradeJournalConfig,
)


LOCAL_DSN = "postgresql://localhost/postgres"


def _record(
    *,
    packet_id: str,
    condition_id: str,
    token_id: str,
    decision_at: datetime,
    fair_value: Decimal = Decimal("0.600000"),
) -> PaperTradeRecord:
    return PaperTradeRecord(
        packet_id=packet_id,
        packet_created_at=datetime(2026, 6, 29, 12, 0, tzinfo=UTC),
        condition_id=condition_id,
        token_id=token_id,
        market_slug=f"market-{packet_id}",
        market_url=f"https://polymarket.com/event/market-{packet_id}",
        question=f"Will market {packet_id} resolve yes?",
        outcome_name="YES",
        strategy_type="market_quality",
        source_score="80.000",
        market_raw_archive_path="data/raw/gamma/markets.json",
        order_book_raw_archive_path="data/raw/clob/book.json",
        order_book_raw_payload_sha256="a" * 64,
        order_book_snapshot_sha256="b" * 64,
        risk_tags=("liquidity",),
        rule_text_hash="c" * 64,
        resolution_source="Example resolution source",
        decision_timestamp_utc=decision_at,
        model_probability=fair_value,
        confidence=Decimal("0.700000"),
        research_bid=Decimal("0.500000"),
        research_ask=Decimal("0.520000"),
        research_midpoint=Decimal("0.510000"),
        research_expected_entry_price=Decimal("0.520000"),
        research_fair_value_estimate=fair_value,
        research_theoretical_edge=Decimal("0.080000"),
        research_spread=Decimal("0.020000"),
        research_slippage_estimate=Decimal("0.004000"),
        research_cost_adjusted_edge=Decimal("0.060000"),
        max_executable_size=Decimal("100.000000"),
        order_side="buy",
        order_requested_size=Decimal("10.000000"),
        fill_filled_size=Decimal("10.000000"),
        fill_unfilled_size=Decimal("0.000000"),
        fill_status="complete",
        fill_average_price=Decimal("0.520000"),
        fill_worst_price=Decimal("0.520000"),
        fill_best_bid=Decimal("0.500000"),
        fill_best_ask=Decimal("0.520000"),
        fill_midpoint=Decimal("0.510000"),
        fill_spread=Decimal("0.020000"),
        fill_slippage_estimate=Decimal("0.004000"),
        order_book_captured_at=datetime(2026, 6, 29, 12, 1, tzinfo=UTC),
        account_equity_before_trade=Decimal("10000.000000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Mark at executable bid on review.",
        thesis="Tight spread and clear rules.",
        invalidating_conditions="Spread widens.",
    )


def _write_journal(tmp_path: Path, records: tuple[PaperTradeRecord, ...]) -> Path:
    journal_path = tmp_path / "paper-trades.jsonl"
    journal = PaperTradeJournal(journal_path)
    for record in records:
        journal.append(record)
    return journal_path


def test_disabled_db_reads_legacy_jsonl_in_append_order(tmp_path: Path) -> None:
    older = _record(
        packet_id="packet-older",
        condition_id="0xolder",
        token_id="111",
        decision_at=datetime(2026, 6, 29, 12, 0, tzinfo=UTC),
    )
    newer = _record(
        packet_id="packet-newer",
        condition_id="0xnewer",
        token_id="222",
        decision_at=datetime(2026, 6, 29, 13, 0, tzinfo=UTC),
    )
    journal_path = _write_journal(tmp_path, (older, newer))
    db_config = SupabasePaperTradeJournalConfig(enabled=False, dsn=None)

    def forbidden_loader(**_: Any) -> tuple[object, ...]:
        raise AssertionError("DB loader should not run when DB source is disabled")

    records = load_check_outcomes_paper_trade_records(
        journal_path=journal_path,
        db_config=db_config,
        db_loader=forbidden_loader,
    )

    assert records == (older, newer)
    assert records[0].research_fair_value_estimate == Decimal("0.600000")


def test_disabled_db_missing_legacy_jsonl_returns_empty_tuple(tmp_path: Path) -> None:
    records = load_check_outcomes_paper_trade_records(
        journal_path=tmp_path / "missing-paper-trades.jsonl",
        db_config=SupabasePaperTradeJournalConfig(enabled=False, dsn=None),
        db_loader=None,
    )

    assert records == ()


def test_enabled_db_loads_records_reverses_to_append_order_and_ignores_jsonl(
    tmp_path: Path,
) -> None:
    older = _record(
        packet_id="packet-older",
        condition_id="0xolder",
        token_id="111",
        decision_at=datetime(2026, 6, 29, 12, 0, tzinfo=UTC),
        fair_value=Decimal("0.610000"),
    )
    newer = _record(
        packet_id="packet-newer",
        condition_id="0xnewer",
        token_id="222",
        decision_at=datetime(2026, 6, 29, 13, 0, tzinfo=UTC),
        fair_value=Decimal("0.620000"),
    )
    db_config = SupabasePaperTradeJournalConfig(
        enabled=True,
        dsn=LOCAL_DSN,
        table_name="paper_trade_archive",
    )
    load_calls: list[tuple[str, str]] = []

    def fake_loader(*, dsn: str, table_name: str) -> tuple[object, ...]:
        load_calls.append((dsn, table_name))
        return (newer, older)

    records = load_check_outcomes_paper_trade_records(
        journal_path=tmp_path / "missing-legacy-jsonl.jsonl",
        db_config=db_config,
        db_loader=fake_loader,
    )

    assert records == (older, newer)
    assert load_calls == [(LOCAL_DSN, "paper_trade_archive")]
    assert records[0].research_fair_value_estimate == Decimal("0.610000")
    with pytest.raises(FrozenInstanceError):
        records[0].packet_id = "mutated"  # type: ignore[misc]


def test_enabled_db_requires_loader(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match="db_loader is required when paper trade DB source is enabled",
    ):
        load_check_outcomes_paper_trade_records(
            journal_path=tmp_path / "paper-trades.jsonl",
            db_config=SupabasePaperTradeJournalConfig(enabled=True, dsn=LOCAL_DSN),
            db_loader=None,
        )


@pytest.mark.parametrize(
    "loader_result",
    (
        "not-records",
        (object(),),
    ),
)
def test_enabled_db_rejects_non_paper_trade_record_loader_output(
    tmp_path: Path,
    loader_result: object,
) -> None:
    def fake_loader(*, dsn: str, table_name: str) -> object:
        return loader_result

    with pytest.raises(
        ValueError,
        match="paper trade DB source must return",
    ):
        load_check_outcomes_paper_trade_records(
            journal_path=tmp_path / "paper-trades.jsonl",
            db_config=SupabasePaperTradeJournalConfig(enabled=True, dsn=LOCAL_DSN),
            db_loader=fake_loader,  # type: ignore[arg-type]
        )


def test_rejects_non_supabase_paper_trade_journal_config(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError,
        match="db_config must be a SupabasePaperTradeJournalConfig",
    ):
        load_check_outcomes_paper_trade_records(
            journal_path=tmp_path / "paper-trades.jsonl",
            db_config=object(),  # type: ignore[arg-type]
            db_loader=None,
        )


def test_public_exports_are_explicit() -> None:
    import polymarket_alpha_lab.check_outcomes_paper_trade_source as source

    assert source.__all__ == (
        "CheckOutcomesPaperTradeDbLoader",
        "load_check_outcomes_paper_trade_records",
    )


def test_helper_scope_excludes_live_and_psycopg_surfaces() -> None:
    import polymarket_alpha_lab.check_outcomes_paper_trade_source as source

    module_source = Path(source.__file__).read_text(encoding="utf-8")
    forbidden_patterns = (
        r"\bpsycopg\b",
        r"\bconnect_local_supabase\b",
        r"\bPolymarketPublicClient\b",
        r"\blive\s+trading\b",
        r"\bauth\b",
        r"\bwallet\b",
        r"\bprivate[_ -]?key\b",
        r"\bsubmit(?:s|ted|ting|tal)?\b",
        r"\bsign(?:s|ed|ing)?\b",
        r"\bcancel(?:s|ed|ing|lation)?\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, module_source), pattern
