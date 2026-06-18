from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport
from polymarket_alpha_lab.paper_trade_attribution import (
    PaperTradeAttributionConfig,
    PaperTradeAttributionReport,
    PaperTradeAttributionRow,
    build_paper_trade_attribution_report,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
CONFIG = PaperTradeAttributionConfig(config_version="paper-trade-attribution-v0")
HEX = "a" * 64


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


def _record(
    index: int,
    *,
    market_slug: str | None = None,
    outcome_name: str = "YES",
    fill_status: str = "complete",
    requested_size: Decimal = Decimal("100"),
    filled_size: Decimal = Decimal("100"),
    unfilled_size: Decimal = Decimal("0"),
    average_price: Decimal = Decimal("0.5400"),
    decision_timestamp: datetime | None = None,
    sizing_limiter: str = "max_executable_size",
) -> PaperTradeRecord:
    return PaperTradeRecord(
        packet_id=f"pkt-{index}",
        packet_created_at=datetime(2026, 6, 18, 9, index, tzinfo=UTC),
        condition_id=f"0x{index:04x}",
        token_id=f"token-{index}",
        market_slug=market_slug or f"market-{index}",
        market_url=f"https://polymarket.com/event/market-{index}",
        question=f"Will market {index} resolve yes?",
        outcome_name=outcome_name,
        strategy_type="market_quality",
        source_score="80.000",
        market_raw_archive_path=f"data/raw/gamma/market-{index}.json",
        order_book_raw_archive_path=f"data/raw/clob/book-{index}.json",
        order_book_raw_payload_sha256=HEX,
        order_book_snapshot_sha256=HEX,
        risk_tags=("liquidity",),
        rule_text_hash=HEX,
        resolution_source="Official source",
        decision_timestamp_utc=decision_timestamp
        or datetime(2026, 6, 18, 9, index, 30, tzinfo=UTC),
        model_probability=Decimal("0.6000"),
        confidence=Decimal("0.8000"),
        research_bid=Decimal("0.5000"),
        research_ask=Decimal("0.5400"),
        research_midpoint=Decimal("0.5200"),
        research_expected_entry_price=Decimal("0.5400"),
        research_fair_value_estimate=Decimal("0.6000"),
        research_theoretical_edge=Decimal("0.060000"),
        research_spread=Decimal("0.0400"),
        research_slippage_estimate=Decimal("0.004000"),
        research_cost_adjusted_edge=Decimal("0.040000"),
        max_executable_size=Decimal("1000"),
        order_side="buy",
        order_requested_size=requested_size,
        fill_filled_size=filled_size,
        fill_unfilled_size=unfilled_size,
        fill_status=fill_status,
        fill_average_price=average_price,
        fill_worst_price=average_price,
        fill_best_bid=Decimal("0.5000"),
        fill_best_ask=Decimal("0.5400"),
        fill_midpoint=Decimal("0.5200"),
        fill_spread=Decimal("0.0400"),
        fill_slippage_estimate=Decimal("0.006000"),
        order_book_captured_at=datetime(2026, 6, 18, 9, index, 20, tzinfo=UTC),
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter=sizing_limiter,
        planned_exit_rule="Hold to resolution.",
        thesis="Paper test thesis.",
        invalidating_conditions="Resolution source changes.",
    )


def _observation(
    record: PaperTradeRecord,
    actual_outcome_value: Decimal,
    *,
    observed_at: datetime = GENERATED_AT,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=observed_at,
        source_packet_id=record.packet_id,
        condition_id=record.condition_id,
        token_id=record.token_id,
        market_slug=record.market_slug,
        strategy_type=record.strategy_type,
        risk_tags=record.risk_tags,
        predicted_probability=record.research_fair_value_estimate,
        actual_outcome_value=actual_outcome_value,
    )


def _outcome_report(
    *observations: PaperForecastEvidenceObservation,
    pending_count: int = 0,
) -> OutcomeTrackingReport:
    evidence_report = (
        build_paper_forecast_evidence_report(
            observations,
            config=PaperForecastEvidenceConfig(config_version="paper-trade-attribution-test"),
            generated_at=GENERATED_AT,
        )
        if observations
        else None
    )
    return OutcomeTrackingReport(
        generated_at=GENERATED_AT,
        config_version="outcome-tracker-v1",
        total_markets_checked=len(observations) + pending_count,
        resolved_count=len(observations),
        pending_count=pending_count,
        observations=observations,
        forecast_evidence_report=evidence_report,
    )


def _report(
    *records: PaperTradeRecord,
    outcome_report: OutcomeTrackingReport | None = None,
) -> PaperTradeAttributionReport:
    return build_paper_trade_attribution_report(
        records,
        config=CONFIG,
        generated_at=GENERATED_AT,
        outcome_report=outcome_report,
    )


def _row(**overrides) -> PaperTradeAttributionRow:
    values = {
        "market_slug": "market-a",
        "side": "yes",
        "status": "complete",
        "trade_count": 1,
        "filled_count": 1,
        "complete_fill_count": 1,
        "partial_fill_count": 0,
        "resolved_count": None,
        "pending_count": None,
        "realized_win_count": None,
        "realized_loss_count": None,
        "total_requested_size": Decimal("10"),
        "total_filled_size": Decimal("10"),
        "total_unfilled_size": Decimal("0"),
        "total_notional": Decimal("5.4000"),
        "reason_codes": ("fill_complete",),
    }
    values.update(overrides)
    return PaperTradeAttributionRow(**values)


def test_attribution_empty_data_is_readonly_paper_report_with_zero_trade_counts():
    report = _report()

    assert isinstance(report, PaperTradeAttributionReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-trade-attribution-v0"
    assert report.trade_count == 0
    assert report.row_count == 0
    assert report.market_count == 0
    assert report.filled_count == 0
    assert report.complete_fill_count == 0
    assert report.partial_fill_count == 0
    assert report.resolved_count is None
    assert report.pending_count is None
    assert report.realized_win_count is None
    assert report.realized_loss_count is None
    assert report.total_requested_size == Decimal("0")
    assert report.total_filled_size == Decimal("0")
    assert report.total_unfilled_size == Decimal("0")
    assert report.total_notional == Decimal("0")
    assert report.first_trade_decision_at is None
    assert report.latest_trade_decision_at is None
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_attribution_groups_market_side_status_and_sorts_by_count_market_side_status():
    trades = (
        _record(
            1,
            market_slug="market-b",
            outcome_name="NO",
            fill_status="partial",
            requested_size=Decimal("100"),
            filled_size=Decimal("40"),
            unfilled_size=Decimal("60"),
            average_price=Decimal("0.2500"),
            sizing_limiter="book_depth",
        ),
        _record(
            2,
            market_slug="market-a",
            outcome_name="YES",
            requested_size=Decimal("100"),
            filled_size=Decimal("100"),
            average_price=Decimal("0.5400"),
        ),
        _record(
            3,
            market_slug="market-b",
            outcome_name="NO",
            fill_status="partial",
            requested_size=Decimal("100"),
            filled_size=Decimal("30"),
            unfilled_size=Decimal("70"),
            average_price=Decimal("0.3000"),
            sizing_limiter="book_depth",
        ),
        _record(
            4,
            market_slug="market-a",
            outcome_name="YES",
            requested_size=Decimal("50"),
            filled_size=Decimal("50"),
            average_price=Decimal("0.5000"),
        ),
        _record(
            5,
            market_slug="market-c",
            outcome_name="YES",
            requested_size=Decimal("10"),
            filled_size=Decimal("10"),
            average_price=Decimal("0.6000"),
        ),
    )

    report = _report(*trades)

    assert [(row.market_slug, row.side, row.status) for row in report.rows] == [
        ("market-a", "yes", "complete"),
        ("market-b", "no", "partial"),
        ("market-c", "yes", "complete"),
    ]
    assert report.trade_count == 5
    assert report.row_count == 3
    assert report.market_count == 3
    assert report.filled_count == 5
    assert report.complete_fill_count == 3
    assert report.partial_fill_count == 2
    assert report.total_requested_size == Decimal("360")
    assert report.total_filled_size == Decimal("230")
    assert report.total_unfilled_size == Decimal("130")
    assert report.total_notional == Decimal("104.0000")

    market_a = report.rows[0]
    assert market_a.trade_count == 2
    assert market_a.filled_count == 2
    assert market_a.complete_fill_count == 2
    assert market_a.partial_fill_count == 0
    assert market_a.total_requested_size == Decimal("150")
    assert market_a.total_filled_size == Decimal("150")
    assert market_a.total_unfilled_size == Decimal("0")
    assert market_a.total_notional == Decimal("79.0000")
    assert market_a.reason_codes == ("fill_complete", "sizing_limiter:max_executable_size")

    market_b = report.rows[1]
    assert market_b.trade_count == 2
    assert market_b.filled_count == 2
    assert market_b.complete_fill_count == 0
    assert market_b.partial_fill_count == 2
    assert market_b.total_requested_size == Decimal("200")
    assert market_b.total_filled_size == Decimal("70")
    assert market_b.total_unfilled_size == Decimal("130")
    assert market_b.total_notional == Decimal("19.0000")
    assert market_b.reason_codes == ("fill_partial", "sizing_limiter:book_depth")


def test_attribution_applies_outcome_report_to_resolved_pending_and_realized_counts():
    resolved_win = _record(1, market_slug="market-a", outcome_name="YES")
    resolved_loss = _record(
        2,
        market_slug="market-a",
        outcome_name="YES",
        fill_status="partial",
        requested_size=Decimal("50"),
        filled_size=Decimal("25"),
        unfilled_size=Decimal("25"),
    )
    pending = _record(3, market_slug="market-b", outcome_name="NO")
    outcome_report = _outcome_report(
        _observation(resolved_win, Decimal("1")),
        _observation(resolved_loss, Decimal("0")),
        pending_count=1,
    )

    report = _report(
        resolved_win,
        resolved_loss,
        pending,
        outcome_report=outcome_report,
    )
    rows_by_key = {
        (row.market_slug, row.side, row.status): row
        for row in report.rows
    }

    assert report.resolved_count == 2
    assert report.pending_count == 1
    assert report.realized_win_count == 1
    assert report.realized_loss_count == 1
    assert rows_by_key[("market-a", "yes", "complete")].resolved_count == 1
    assert rows_by_key[("market-a", "yes", "complete")].pending_count == 0
    assert rows_by_key[("market-a", "yes", "complete")].realized_win_count == 1
    assert rows_by_key[("market-a", "yes", "complete")].realized_loss_count == 0
    assert rows_by_key[("market-a", "yes", "partial")].resolved_count == 1
    assert rows_by_key[("market-a", "yes", "partial")].pending_count == 0
    assert rows_by_key[("market-a", "yes", "partial")].realized_win_count == 0
    assert rows_by_key[("market-a", "yes", "partial")].realized_loss_count == 1
    assert rows_by_key[("market-b", "no", "complete")].resolved_count == 0
    assert rows_by_key[("market-b", "no", "complete")].pending_count == 1
    assert rows_by_key[("market-b", "no", "complete")].realized_win_count == 0
    assert rows_by_key[("market-b", "no", "complete")].realized_loss_count == 0


def test_attribution_normalizes_datetimes_to_utc():
    eastern = timezone(timedelta(hours=-4))
    trade = _record(
        1,
        decision_timestamp=datetime(2026, 6, 18, 8, 30, tzinfo=eastern),
    )

    report = build_paper_trade_attribution_report(
        (trade,),
        config=CONFIG,
        generated_at=datetime(2026, 6, 18, 8, 0, tzinfo=eastern),
    )

    assert report.generated_at == datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    assert report.first_trade_decision_at == datetime(2026, 6, 18, 12, 30, tzinfo=UTC)
    assert report.latest_trade_decision_at == datetime(2026, 6, 18, 12, 30, tzinfo=UTC)


def test_attribution_rejects_invalid_inputs_and_non_exact_scalar_types():
    with pytest.raises(ValueError, match="config must be"):
        build_paper_trade_attribution_report((), config=object(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_trade_attribution_report((), config=CONFIG, generated_at="now")
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_trade_attribution_report(
            (),
            config=CONFIG,
            generated_at=_DatetimeSubclass(2026, 6, 18, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="trade_records"):
        build_paper_trade_attribution_report("not records", config=CONFIG, generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="PaperTradeRecord"):
        build_paper_trade_attribution_report((object(),), config=CONFIG, generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="outcome_report"):
        build_paper_trade_attribution_report(
            (),
            config=CONFIG,
            generated_at=GENERATED_AT,
            outcome_report=object(),
        )
    for flag_name in ("paper_only", "report_only", "readonly"):
        outcome_report = _outcome_report()
        object.__setattr__(outcome_report, flag_name, False)
        with pytest.raises(ValueError, match=flag_name):
            build_paper_trade_attribution_report(
                (),
                config=CONFIG,
                generated_at=GENERATED_AT,
                outcome_report=outcome_report,
            )
    with pytest.raises(ValueError, match="config_version"):
        PaperTradeAttributionConfig(
            config_version=_StringSubclass("paper-trade-attribution-v0"),
        )
    with pytest.raises(ValueError, match="trade_count"):
        _row(trade_count=_IntSubclass(1))
    with pytest.raises(ValueError, match="trade_count"):
        _row(trade_count=True)
    with pytest.raises(ValueError, match="total_requested_size"):
        _row(total_requested_size=_DecimalSubclass("10"))
    with pytest.raises(ValueError, match="market_slug"):
        _row(market_slug=_StringSubclass("market-a"))


def test_attribution_dataclasses_are_frozen_and_revalidate_hard_flags():
    report = _report(_record(1))

    with pytest.raises(FrozenInstanceError):
        report.trade_count = 2
    with pytest.raises(FrozenInstanceError):
        report.rows[0].trade_count = 2
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
