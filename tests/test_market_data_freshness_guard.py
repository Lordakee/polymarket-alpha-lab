from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.domain import MarketSnapshot, OrderBookLevel, OrderBookSnapshot
from polymarket_alpha_lab.market_data_freshness_guard import (
    PaperMarketDataFreshnessGuardBookRow,
    PaperMarketDataFreshnessGuardConfig,
    PaperMarketDataFreshnessGuardSummary,
    build_paper_market_data_freshness_guard_summary,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def _config(**overrides) -> PaperMarketDataFreshnessGuardConfig:
    values = {
        "config_version": "market-data-freshness-guard-v0",
        "max_market_snapshot_age_seconds": 120,
        "max_book_snapshot_age_seconds": 60,
        "min_book_count": 2,
        "max_spread": Decimal("0.0500"),
        "min_side_depth": Decimal("10.0000"),
    }
    values.update(overrides)
    return PaperMarketDataFreshnessGuardConfig(**values)


def _market(**overrides) -> MarketSnapshot:
    values = {
        "condition_id": "condition-alpha",
        "market_slug": "private-alpha-market",
        "question": "Private alpha market question?",
        "active": True,
        "closed": False,
        "accepting_orders": True,
        "end_time": None,
        "volume_24h": Decimal("100.0000"),
        "liquidity": Decimal("250.0000"),
        "captured_at": GENERATED_AT - timedelta(seconds=30),
    }
    values.update(overrides)
    return MarketSnapshot(**values)


def _book(
    token_id: str,
    *,
    captured_at: datetime | None = None,
    bid_price: Decimal = Decimal("0.4900"),
    bid_size: Decimal = Decimal("25.0000"),
    ask_price: Decimal = Decimal("0.5100"),
    ask_size: Decimal = Decimal("30.0000"),
) -> OrderBookSnapshot:
    return OrderBookSnapshot(
        token_id=token_id,
        bids=(OrderBookLevel(price=bid_price, size=bid_size),),
        asks=(OrderBookLevel(price=ask_price, size=ask_size),),
        captured_at=(
            captured_at
            if captured_at is not None
            else GENERATED_AT - timedelta(seconds=15)
        ),
    )


def test_market_data_freshness_guard_reports_fresh_snapshot_as_pass():
    summary = build_paper_market_data_freshness_guard_summary(
        _market(),
        (
            _book("token-beta"),
            _book("token-alpha", captured_at=GENERATED_AT - timedelta(seconds=20)),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(summary, PaperMarketDataFreshnessGuardSummary)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == "market-data-freshness-guard-v0"
    assert summary.condition_id == "condition-alpha"
    assert summary.market_age_seconds == Decimal("30")
    assert summary.book_count == 2
    assert summary.missing_book_count == 0
    assert summary.status == "pass"
    assert summary.reason_codes == ("market_data_fresh",)
    assert tuple(row.token_id for row in summary.book_rows) == (
        "token-alpha",
        "token-beta",
    )
    assert tuple(row.status for row in summary.book_rows) == ("pass", "pass")
    assert summary.book_rows[0] == PaperMarketDataFreshnessGuardBookRow(
        token_id="token-alpha",
        captured_at=GENERATED_AT - timedelta(seconds=20),
        age_seconds=Decimal("20"),
        best_bid=Decimal("0.4900"),
        best_ask=Decimal("0.5100"),
        spread=Decimal("0.0200"),
        bid_depth=Decimal("25.0000"),
        ask_depth=Decimal("30.0000"),
        status="pass",
        reason_codes=("fresh_book_snapshot",),
    )


def test_market_data_freshness_guard_blocks_stale_market_and_missing_book_without_slug_or_question():
    summary = build_paper_market_data_freshness_guard_summary(
        _market(captured_at=GENERATED_AT - timedelta(seconds=121)),
        (_book("token-alpha"),),
        config=_config(max_market_snapshot_age_seconds=120, min_book_count=2),
        generated_at=GENERATED_AT,
    )

    assert summary.status == "blocked"
    assert summary.reason_codes == ("stale_market_snapshot", "missing_book")
    assert summary.market_age_seconds == Decimal("121")
    assert summary.book_count == 1
    assert summary.missing_book_count == 1
    assert not hasattr(summary, "market_slug")
    assert not hasattr(summary, "question")
    summary_payload = asdict(summary)
    assert "market_slug" not in summary_payload
    assert "question" not in summary_payload
    assert "private-alpha-market" not in repr(summary)
    assert "Private alpha market question?" not in repr(summary)


def test_market_data_freshness_guard_marks_stale_book_wide_spread_and_thin_depth():
    summary = build_paper_market_data_freshness_guard_summary(
        _market(),
        (
            _book(
                "token-stale",
                captured_at=GENERATED_AT - timedelta(seconds=61),
            ),
            _book(
                "token-wide",
                bid_price=Decimal("0.4100"),
                ask_price=Decimal("0.5001"),
            ),
            _book(
                "token-thin",
                bid_size=Decimal("9.9999"),
                ask_size=Decimal("10.0000"),
            ),
        ),
        config=_config(max_book_snapshot_age_seconds=60, min_book_count=3),
        generated_at=GENERATED_AT,
    )

    assert summary.status == "blocked"
    assert summary.reason_codes == (
        "stale_book_snapshot",
        "wide_spread",
        "thin_depth",
    )
    assert tuple(row.token_id for row in summary.book_rows) == (
        "token-stale",
        "token-thin",
        "token-wide",
    )
    assert tuple(row.status for row in summary.book_rows) == (
        "blocked",
        "watch",
        "watch",
    )
    assert summary.book_rows[0].reason_codes == ("stale_book_snapshot",)
    assert summary.book_rows[1].reason_codes == ("thin_depth",)
    assert summary.book_rows[2].spread == Decimal("0.0901")
    assert summary.book_rows[2].reason_codes == ("wide_spread",)


def test_market_data_freshness_guard_normalizes_datetimes_to_utc_and_preserves_subseconds():
    generated_at = datetime(
        2026,
        6,
        18,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    market_captured_at = datetime(
        2026,
        6,
        18,
        13,
        59,
        59,
        999999,
        tzinfo=timezone(timedelta(hours=2)),
    )

    summary = build_paper_market_data_freshness_guard_summary(
        _market(captured_at=market_captured_at),
        (_book("token-alpha"), _book("token-beta")),
        config=_config(max_market_snapshot_age_seconds=2),
        generated_at=generated_at,
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.market_captured_at == datetime(2026, 6, 18, 11, 59, 59, 999999, tzinfo=UTC)
    assert summary.market_age_seconds == Decimal("0.000001")


def test_market_data_freshness_guard_rejects_future_snapshot_times():
    with pytest.raises(ValueError, match="future"):
        build_paper_market_data_freshness_guard_summary(
            _market(captured_at=GENERATED_AT + timedelta(seconds=1)),
            (_book("token-alpha"), _book("token-beta")),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        build_paper_market_data_freshness_guard_summary(
            _market(),
            (
                _book("token-alpha", captured_at=GENERATED_AT + timedelta(seconds=1)),
                _book("token-beta"),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_market_data_freshness_guard_validates_exact_scalar_types_and_decimal_only_inputs():
    with pytest.raises(ValueError, match="config_version"):
        PaperMarketDataFreshnessGuardConfig(
            config_version=_StringSubclass("market-data-freshness-guard-v0"),
            max_market_snapshot_age_seconds=120,
            max_book_snapshot_age_seconds=60,
            min_book_count=2,
            max_spread=Decimal("0.0500"),
            min_side_depth=Decimal("10.0000"),
        )
    with pytest.raises(ValueError, match="max_market_snapshot_age_seconds"):
        PaperMarketDataFreshnessGuardConfig(
            config_version="market-data-freshness-guard-v0",
            max_market_snapshot_age_seconds=_IntSubclass(120),
            max_book_snapshot_age_seconds=60,
            min_book_count=2,
            max_spread=Decimal("0.0500"),
            min_side_depth=Decimal("10.0000"),
        )
    with pytest.raises(ValueError, match="max_spread"):
        PaperMarketDataFreshnessGuardConfig(
            config_version="market-data-freshness-guard-v0",
            max_market_snapshot_age_seconds=120,
            max_book_snapshot_age_seconds=60,
            min_book_count=2,
            max_spread=_DecimalSubclass("0.0500"),
            min_side_depth=Decimal("10.0000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_market_data_freshness_guard_summary(
            _market(),
            (_book("token-alpha"), _book("token-beta")),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 6, 18, 12, 0, tzinfo=UTC),
        )
    bad_level_book = _book("token-alpha")
    object.__setattr__(
        bad_level_book,
        "bids",
        (OrderBookLevel(price=_DecimalSubclass("0.4900"), size=Decimal("25.0000")),),
    )
    with pytest.raises(ValueError, match="price"):
        build_paper_market_data_freshness_guard_summary(
            _market(),
            (bad_level_book, _book("token-beta")),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_market_data_freshness_guard_rejects_direct_summary_inconsistency():
    stale_row_claiming_pass = PaperMarketDataFreshnessGuardBookRow(
        token_id="token-alpha",
        captured_at=GENERATED_AT - timedelta(seconds=999),
        age_seconds=Decimal("999"),
        best_bid=Decimal("0.4900"),
        best_ask=Decimal("0.5100"),
        spread=Decimal("0.0200"),
        bid_depth=Decimal("25.0000"),
        ask_depth=Decimal("30.0000"),
        status="pass",
        reason_codes=("fresh_book_snapshot",),
    )

    with pytest.raises(ValueError, match="book row status"):
        PaperMarketDataFreshnessGuardSummary(
            generated_at=GENERATED_AT,
            config_version="market-data-freshness-guard-v0",
            condition_id="condition-alpha",
            market_captured_at=GENERATED_AT - timedelta(seconds=1),
            market_age_seconds=Decimal("1"),
            max_market_snapshot_age_seconds=120,
            max_book_snapshot_age_seconds=60,
            min_book_count=1,
            max_spread=Decimal("0.0500"),
            min_side_depth=Decimal("10.0000"),
            book_count=1,
            missing_book_count=0,
            status="pass",
            reason_codes=("market_data_fresh",),
            book_rows=(stale_row_claiming_pass,),
        )


def test_market_data_freshness_guard_dataclasses_are_frozen_and_hard_flags_are_true():
    cfg = _config()
    summary = build_paper_market_data_freshness_guard_summary(
        _market(),
        (_book("token-alpha"), _book("token-beta")),
        config=cfg,
        generated_at=GENERATED_AT,
    )

    assert cfg.paper_only is True
    assert cfg.report_only is True
    assert cfg.readonly is True
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"
    with pytest.raises(FrozenInstanceError):
        summary.book_rows[0].status = "watch"
    with pytest.raises(ValueError, match="paper_only"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(cfg, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(cfg, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.book_rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.book_rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.book_rows[0], readonly=False)
