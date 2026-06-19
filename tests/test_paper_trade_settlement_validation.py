from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    PaperForecastEvidenceReport,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.journal import PaperTradeRecord
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport
from polymarket_alpha_lab.paper_trade_settlement_validation import (
    PaperTradeSettlementValidationConfig,
    PaperTradeSettlementValidationReport,
    PaperTradeSettlementValidationRow,
    build_paper_trade_settlement_validation_report,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
CONFIG = PaperTradeSettlementValidationConfig(
    config_version="paper-trade-settlement-validation-v0",
    min_resolved_trades=1,
    forecast_evidence_config=PaperForecastEvidenceConfig(
        config_version="paper-trade-settlement-validation-v0",
        min_probability_observations=1,
        min_edge_observations=1,
        max_mean_probability_loss=Decimal("1.0000"),
        max_bucket_error=Decimal("1.0000"),
        max_mean_edge_gap_ratio=Decimal("1.0000"),
        min_positive_edge_hit_rate=Decimal("0"),
        max_residual_exposure_ratio=Decimal("1.0000"),
    ),
)
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
    packet_id: str | None = None,
    token_id: str | None = None,
    market_slug: str | None = None,
    outcome_name: str = "YES",
    strategy_type: str = "market_quality",
    filled_size: Decimal = Decimal("10"),
    unfilled_size: Decimal = Decimal("0"),
    average_price: Decimal = Decimal("0.4000"),
    fair_value: Decimal = Decimal("0.7000"),
    theoretical_edge: Decimal = Decimal("0.120000"),
    cost_adjusted_edge: Decimal = Decimal("0.100000"),
    order_side: str = "buy",
    decision_timestamp: datetime | None = None,
) -> PaperTradeRecord:
    requested_size = filled_size + unfilled_size
    minute = index % 60
    return PaperTradeRecord(
        packet_id=packet_id or f"pkt-{index}",
        packet_created_at=datetime(2026, 6, 18, 9, minute, tzinfo=UTC),
        condition_id=f"0x{index:04x}",
        token_id=token_id or f"token-{index}",
        market_slug=market_slug or f"market-{index}",
        market_url=f"https://polymarket.com/event/market-{index}",
        question=f"Will market {index} resolve yes?",
        outcome_name=outcome_name,
        strategy_type=strategy_type,
        source_score="80.000",
        market_raw_archive_path=f"data/raw/gamma/market-{index}.json",
        order_book_raw_archive_path=f"data/raw/clob/book-{index}.json",
        order_book_raw_payload_sha256=HEX,
        order_book_snapshot_sha256=HEX,
        risk_tags=("liquidity",),
        rule_text_hash=HEX,
        resolution_source="Official source",
        decision_timestamp_utc=decision_timestamp
        or datetime(2026, 6, 18, 9, minute, 30, tzinfo=UTC),
        model_probability=fair_value,
        confidence=Decimal("0.8000"),
        research_bid=Decimal("0.3000"),
        research_ask=average_price,
        research_midpoint=(Decimal("0.3000") + average_price) / Decimal("2"),
        research_expected_entry_price=average_price,
        research_fair_value_estimate=fair_value,
        research_theoretical_edge=theoretical_edge,
        research_spread=Decimal("0.0400"),
        research_slippage_estimate=Decimal("0.004000"),
        research_cost_adjusted_edge=cost_adjusted_edge,
        max_executable_size=Decimal("1000"),
        order_side=order_side,
        order_requested_size=requested_size,
        fill_filled_size=filled_size,
        fill_unfilled_size=unfilled_size,
        fill_status="complete" if unfilled_size == 0 else "partial",
        fill_average_price=average_price,
        fill_worst_price=average_price,
        fill_best_bid=Decimal("0.3000"),
        fill_best_ask=average_price,
        fill_midpoint=(Decimal("0.3000") + average_price) / Decimal("2"),
        fill_spread=Decimal("0.0400"),
        fill_slippage_estimate=Decimal("0.006000"),
        order_book_captured_at=datetime(2026, 6, 18, 9, minute, 20, tzinfo=UTC),
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
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
            config=PaperForecastEvidenceConfig(
                config_version="paper-trade-settlement-validation-test",
                min_probability_observations=0,
                min_edge_observations=0,
                max_mean_probability_loss=Decimal("1.0000"),
                max_bucket_error=Decimal("1.0000"),
                max_mean_edge_gap_ratio=Decimal("1.0000"),
                min_positive_edge_hit_rate=Decimal("0"),
                max_residual_exposure_ratio=Decimal("1.0000"),
            ),
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
    config: PaperTradeSettlementValidationConfig = CONFIG,
    generated_at: datetime = GENERATED_AT,
) -> PaperTradeSettlementValidationReport:
    return build_paper_trade_settlement_validation_report(
        records,
        outcome_report=outcome_report,
        config=config,
        generated_at=generated_at,
    )


def _row(**overrides) -> PaperTradeSettlementValidationRow:
    values = {
        "packet_id": "pkt-1",
        "source_packet_id": "pkt-1",
        "condition_id": "0x0001",
        "token_id": "token-1",
        "market_slug": "market-1",
        "outcome_name": "YES",
        "strategy_type": "market_quality",
        "status": "observed",
        "entry_notional": Decimal("4.0000"),
        "settlement_payout": Decimal("10"),
        "realized_pnl": Decimal("6.0000"),
        "return_ratio": Decimal("1.500000"),
        "predicted_probability": Decimal("0.7000"),
        "actual_outcome_value": Decimal("1"),
        "probability_loss": Decimal("0.090000"),
        "cost_adjusted_edge": Decimal("0.100000"),
        "reason_codes": ("settlement_observed",),
    }
    values.update(overrides)
    return PaperTradeSettlementValidationRow(**values)


def test_settlement_validation_empty_inputs_are_readonly_empty_report():
    report = _report()

    assert isinstance(report, PaperTradeSettlementValidationReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-trade-settlement-validation-v0"
    assert report.trade_count == 0
    assert report.outcome_observation_count == 0
    assert report.row_count == 0
    assert report.resolved_count == 0
    assert report.pending_count == 0
    assert report.quality_flag_count == 0
    assert report.duplicate_outcome_count == 0
    assert report.unmatched_outcome_count == 0
    assert report.total_entry_notional == Decimal("0")
    assert report.total_settlement_payout == Decimal("0")
    assert report.total_realized_pnl == Decimal("0")
    assert report.win_rate is None
    assert report.positive_return_rate is None
    assert report.mean_probability_loss is None
    assert report.mean_return_ratio is None
    assert report.mean_cost_adjusted_edge is None
    assert report.positive_edge_hit_rate is None
    assert report.status == "empty"
    assert report.rows == ()
    assert report.forecast_evidence_report is None
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_settlement_validation_marks_trades_pending_without_matching_outcomes():
    pending = _record(1, filled_size=Decimal("25"), average_price=Decimal("0.5200"))
    outcome_report = _outcome_report(pending_count=1)

    report = _report(pending, outcome_report=outcome_report)

    assert report.status == "pending"
    assert report.trade_count == 1
    assert report.resolved_count == 0
    assert report.pending_count == 1
    assert report.quality_flag_count == 0
    assert report.total_entry_notional == Decimal("13.0000")
    assert report.total_settlement_payout == Decimal("0")
    assert report.total_realized_pnl == Decimal("0")
    assert report.forecast_evidence_report is None
    assert len(report.rows) == 1
    row = report.rows[0]
    assert row.status == "pending"
    assert row.entry_notional == Decimal("13.0000")
    assert row.settlement_payout is None
    assert row.realized_pnl is None
    assert row.return_ratio is None
    assert row.probability_loss is None
    assert row.reason_codes == ("outcome_pending",)


def test_settlement_validation_flags_empty_outcome_report_as_trade_set_mismatch_for_trades():
    trade = _record(1)

    report = _report(trade, outcome_report=_outcome_report())

    assert report.status == "quality_flags"
    assert report.trade_count == 1
    assert report.resolved_count == 0
    assert report.pending_count == 0
    assert report.quality_flag_count == 1
    assert report.forecast_evidence_report is None
    row = report.rows[0]
    assert row.status == "quality_flags"
    assert row.source_packet_id is None
    assert row.reason_codes == ("outcome_report_trade_set_mismatch",)


def test_settlement_validation_flags_outcome_report_trade_count_mismatch():
    trade = _record(1)

    report = _report(trade, outcome_report=_outcome_report(pending_count=2))

    assert report.status == "quality_flags"
    assert report.trade_count == 1
    assert report.resolved_count == 0
    assert report.pending_count == 0
    assert report.quality_flag_count == 1
    assert report.forecast_evidence_report is None
    row = report.rows[0]
    assert row.status == "quality_flags"
    assert row.reason_codes == ("outcome_report_trade_set_mismatch",)


def test_settlement_validation_computes_win_loss_rows_and_nested_evidence_report():
    winner = _record(
        1,
        filled_size=Decimal("10"),
        average_price=Decimal("0.4000"),
        fair_value=Decimal("0.7000"),
        cost_adjusted_edge=Decimal("0.100000"),
    )
    loser = _record(
        2,
        filled_size=Decimal("10"),
        average_price=Decimal("0.6000"),
        fair_value=Decimal("0.3000"),
        cost_adjusted_edge=Decimal("0.050000"),
    )
    outcome_report = _outcome_report(
        _observation(winner, Decimal("1")),
        _observation(loser, Decimal("0")),
    )

    report = _report(winner, loser, outcome_report=outcome_report)

    assert report.status == "observed"
    assert report.resolved_count == 2
    assert report.pending_count == 0
    assert report.total_entry_notional == Decimal("10.0000")
    assert report.total_settlement_payout == Decimal("10")
    assert report.total_realized_pnl == Decimal("0.0000")
    assert report.win_rate == Decimal("0.500000")
    assert report.positive_return_rate == Decimal("0.500000")
    rows = {row.packet_id: row for row in report.rows}
    assert rows[winner.packet_id].entry_notional == Decimal("4.0000")
    assert rows[winner.packet_id].settlement_payout == Decimal("10")
    assert rows[winner.packet_id].realized_pnl == Decimal("6.0000")
    assert rows[winner.packet_id].return_ratio == Decimal("1.500000")
    assert rows[winner.packet_id].probability_loss == Decimal("0.090000")
    assert rows[winner.packet_id].reason_codes == ("settlement_observed",)
    assert rows[loser.packet_id].entry_notional == Decimal("6.0000")
    assert rows[loser.packet_id].settlement_payout == Decimal("0")
    assert rows[loser.packet_id].realized_pnl == Decimal("-6.0000")
    assert rows[loser.packet_id].return_ratio == Decimal("-1.000000")
    assert rows[loser.packet_id].probability_loss == Decimal("0.090000")
    assert isinstance(report.forecast_evidence_report, PaperForecastEvidenceReport)
    assert report.forecast_evidence_report.observation_count == 2
    assert report.forecast_evidence_report.edge_observation_count == 2


def test_settlement_validation_flags_sell_side_trades_as_unsupported_without_position_context():
    sell = _record(
        1,
        filled_size=Decimal("10"),
        average_price=Decimal("0.4000"),
        fair_value=Decimal("0.7000"),
        order_side="sell",
    )
    outcome_report = _outcome_report(_observation(sell, Decimal("1")))

    report = _report(sell, outcome_report=outcome_report)

    assert report.status == "quality_flags"
    assert report.resolved_count == 0
    assert report.quality_flag_count == 1
    assert report.total_entry_notional == Decimal("4.0000")
    assert report.total_settlement_payout == Decimal("0")
    assert report.total_realized_pnl == Decimal("0")
    assert report.win_rate is None
    assert report.forecast_evidence_report is None
    row = report.rows[0]
    assert row.status == "quality_flags"
    assert row.reason_codes == ("sell_side_settlement_requires_position_context",)
    assert row.realized_pnl is None
    assert row.return_ratio is None


def test_settlement_validation_aggregates_realized_metrics_and_positive_edge_hits():
    winner = _record(
        1,
        filled_size=Decimal("10"),
        average_price=Decimal("0.4000"),
        fair_value=Decimal("0.7000"),
        cost_adjusted_edge=Decimal("0.100000"),
    )
    loser = _record(
        2,
        filled_size=Decimal("10"),
        average_price=Decimal("0.6000"),
        fair_value=Decimal("0.3000"),
        cost_adjusted_edge=Decimal("0.050000"),
    )
    negative_edge_winner = _record(
        3,
        filled_size=Decimal("5"),
        average_price=Decimal("0.2500"),
        fair_value=Decimal("0.2000"),
        cost_adjusted_edge=Decimal("-0.020000"),
    )
    outcome_report = _outcome_report(
        _observation(winner, Decimal("1")),
        _observation(loser, Decimal("0")),
        _observation(negative_edge_winner, Decimal("1")),
    )

    report = _report(winner, loser, negative_edge_winner, outcome_report=outcome_report)

    assert report.status == "observed"
    assert report.total_entry_notional == Decimal("11.2500")
    assert report.total_settlement_payout == Decimal("15")
    assert report.total_realized_pnl == Decimal("3.7500")
    assert report.win_rate == Decimal("0.666667")
    assert report.positive_return_rate == Decimal("0.666667")
    assert report.mean_probability_loss == Decimal("0.273333")
    assert report.mean_return_ratio == Decimal("1.166667")
    assert report.mean_cost_adjusted_edge == Decimal("0.043333")
    assert report.positive_edge_hit_rate == Decimal("0.500000")


def test_settlement_validation_marks_insufficient_sample_below_config_threshold():
    trade = _record(1)
    outcome_report = _outcome_report(_observation(trade, Decimal("1")))
    config = replace(CONFIG, min_resolved_trades=2)

    report = _report(trade, outcome_report=outcome_report, config=config)

    assert report.status == "insufficient_sample"
    assert report.resolved_count == 1
    assert report.forecast_evidence_report is not None


def test_settlement_validation_flags_duplicate_outcomes_for_same_trade_key():
    trade = _record(1)
    outcome_report = _outcome_report(
        _observation(trade, Decimal("1"), observed_at=GENERATED_AT),
        _observation(
            trade,
            Decimal("0"),
            observed_at=GENERATED_AT + timedelta(seconds=1),
        ),
    )

    report = _report(trade, outcome_report=outcome_report)

    assert report.status == "quality_flags"
    assert report.resolved_count == 0
    assert report.pending_count == 0
    assert report.quality_flag_count == 1
    assert report.duplicate_outcome_count == 2
    assert report.unmatched_outcome_count == 0
    assert report.forecast_evidence_report is None
    assert report.rows[0].status == "quality_flags"
    assert report.rows[0].settlement_payout is None
    assert report.rows[0].reason_codes == ("duplicate_outcomes",)


def test_settlement_validation_counts_unmatched_outcomes_as_quality_flags():
    trade = _record(1)
    unmatched_trade = _record(
        99,
        packet_id="pkt-unmatched",
        token_id="token-unmatched",
        market_slug="market-unmatched",
    )
    outcome_report = _outcome_report(_observation(unmatched_trade, Decimal("1")))

    report = _report(trade, outcome_report=outcome_report)

    assert report.status == "quality_flags"
    assert report.resolved_count == 0
    assert report.pending_count == 0
    assert report.quality_flag_count == 1
    assert report.duplicate_outcome_count == 0
    assert report.unmatched_outcome_count == 1
    assert report.rows[0].status == "quality_flags"
    assert report.rows[0].reason_codes == ("outcome_report_trade_set_mismatch",)


def test_settlement_validation_preserves_matched_rows_when_report_has_unmatched_outcome():
    trade = _record(1)
    unmatched_trade = _record(
        99,
        packet_id="pkt-unmatched",
        token_id="token-unmatched",
        market_slug="market-unmatched",
    )
    outcome_report = _outcome_report(
        _observation(trade, Decimal("1")),
        _observation(unmatched_trade, Decimal("0")),
    )

    report = _report(trade, outcome_report=outcome_report)

    assert report.status == "quality_flags"
    assert report.resolved_count == 1
    assert report.pending_count == 0
    assert report.quality_flag_count == 0
    assert report.duplicate_outcome_count == 0
    assert report.unmatched_outcome_count == 1
    row = report.rows[0]
    assert row.status == "observed"
    assert row.reason_codes == ("settlement_observed",)
    assert row.source_packet_id == trade.packet_id


def test_settlement_validation_flags_duplicate_trade_join_keys_without_raising():
    first = _record(1, filled_size=Decimal("10"), average_price=Decimal("0.4000"))
    repeated_run = replace(
        first,
        decision_timestamp_utc=first.decision_timestamp_utc + timedelta(minutes=1),
        fill_filled_size=Decimal("12"),
        order_requested_size=Decimal("12"),
        fill_average_price=Decimal("0.4200"),
        fill_worst_price=Decimal("0.4200"),
        fill_best_ask=Decimal("0.4200"),
        fill_midpoint=Decimal("0.3600"),
        research_ask=Decimal("0.4200"),
        research_midpoint=Decimal("0.3600"),
        research_expected_entry_price=Decimal("0.4200"),
    )

    report = _report(first, repeated_run, outcome_report=_outcome_report(pending_count=2))

    assert report.status == "quality_flags"
    assert report.trade_count == 2
    assert report.resolved_count == 0
    assert report.pending_count == 0
    assert report.quality_flag_count == 2
    assert [row.packet_id for row in report.rows] == [first.packet_id, repeated_run.packet_id]
    assert [row.entry_notional for row in report.rows] == [
        Decimal("4.0000"),
        Decimal("5.0400"),
    ]
    assert {row.reason_codes for row in report.rows} == {("duplicate_trade_join_key",)}


def test_settlement_validation_flags_matched_outcome_identity_mismatch():
    trade = _record(1)
    mismatched = PaperForecastEvidenceObservation(
        observed_at=GENERATED_AT,
        source_packet_id=trade.packet_id,
        condition_id="0xother",
        token_id=trade.token_id,
        market_slug=trade.market_slug,
        strategy_type=trade.strategy_type,
        risk_tags=trade.risk_tags,
        predicted_probability=trade.research_fair_value_estimate,
        actual_outcome_value=Decimal("1"),
    )
    outcome_report = _outcome_report(mismatched)

    report = _report(trade, outcome_report=outcome_report)

    assert report.status == "quality_flags"
    assert report.resolved_count == 0
    assert report.quality_flag_count == 1
    assert report.forecast_evidence_report is None
    assert report.rows[0].status == "quality_flags"
    assert report.rows[0].reason_codes == ("outcome_identity_mismatch",)


def test_settlement_validation_flags_matched_forecast_probability_mismatch():
    trade = _record(1, fair_value=Decimal("0.7000"))
    mismatched = PaperForecastEvidenceObservation(
        observed_at=GENERATED_AT,
        source_packet_id=trade.packet_id,
        condition_id=trade.condition_id,
        token_id=trade.token_id,
        market_slug=trade.market_slug,
        strategy_type=trade.strategy_type,
        risk_tags=trade.risk_tags,
        predicted_probability=Decimal("0.6000"),
        actual_outcome_value=Decimal("1"),
    )

    report = _report(trade, outcome_report=_outcome_report(mismatched))

    assert report.status == "quality_flags"
    assert report.resolved_count == 0
    assert report.quality_flag_count == 1
    assert report.total_settlement_payout == Decimal("0")
    assert report.total_realized_pnl == Decimal("0")
    assert report.mean_probability_loss is None
    assert report.forecast_evidence_report is None
    row = report.rows[0]
    assert row.status == "quality_flags"
    assert row.source_packet_id == trade.packet_id
    assert row.predicted_probability is None
    assert row.actual_outcome_value is None
    assert row.probability_loss is None
    assert row.reason_codes == ("outcome_identity_mismatch",)


def test_settlement_validation_normalizes_datetimes_to_utc():
    eastern = timezone(timedelta(hours=-4))
    trade = _record(
        1,
        decision_timestamp=datetime(2026, 6, 18, 8, 30, tzinfo=eastern),
    )
    outcome_report = _outcome_report(
        _observation(
            trade,
            Decimal("1"),
            observed_at=datetime(2026, 6, 18, 8, 0, tzinfo=eastern),
        ),
    )

    report = _report(
        trade,
        outcome_report=outcome_report,
        generated_at=datetime(2026, 6, 18, 8, 0, tzinfo=eastern),
    )

    assert report.generated_at == GENERATED_AT
    assert report.first_trade_decision_at == datetime(2026, 6, 18, 12, 30, tzinfo=UTC)
    assert report.latest_trade_decision_at == datetime(2026, 6, 18, 12, 30, tzinfo=UTC)
    assert report.first_observed_at == GENERATED_AT
    assert report.latest_observed_at == GENERATED_AT


def test_settlement_validation_rejects_invalid_inputs_and_non_exact_scalar_types():
    with pytest.raises(ValueError, match="config must be"):
        build_paper_trade_settlement_validation_report(
            (),
            outcome_report=None,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_trade_settlement_validation_report(
            (),
            outcome_report=None,
            config=CONFIG,
            generated_at="now",
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_trade_settlement_validation_report(
            (),
            outcome_report=None,
            config=CONFIG,
            generated_at=_DatetimeSubclass(2026, 6, 18, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="trade_records"):
        build_paper_trade_settlement_validation_report(
            "not records",
            outcome_report=None,
            config=CONFIG,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperTradeRecord"):
        build_paper_trade_settlement_validation_report(
            (object(),),
            outcome_report=None,
            config=CONFIG,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="outcome_report"):
        build_paper_trade_settlement_validation_report(
            (),
            outcome_report=object(),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )
    for flag_name in ("paper_only", "report_only", "readonly"):
        outcome_report = _outcome_report()
        object.__setattr__(outcome_report, flag_name, False)
        with pytest.raises(ValueError, match=flag_name):
            build_paper_trade_settlement_validation_report(
                (),
                outcome_report=outcome_report,
                config=CONFIG,
                generated_at=GENERATED_AT,
            )
    with pytest.raises(ValueError, match="config_version"):
        PaperTradeSettlementValidationConfig(
            config_version=_StringSubclass("paper-trade-settlement-validation-v0"),
        )
    with pytest.raises(ValueError, match="min_resolved_trades"):
        PaperTradeSettlementValidationConfig(
            config_version="paper-trade-settlement-validation-v0",
            min_resolved_trades=_IntSubclass(1),
        )
    with pytest.raises(ValueError, match="status"):
        _row(status="unknown")
    with pytest.raises(ValueError, match="entry_notional"):
        _row(entry_notional=_DecimalSubclass("4"))
    with pytest.raises(ValueError, match="entry_notional"):
        _row(entry_notional=4)
    with pytest.raises(ValueError, match="packet_id"):
        _row(packet_id=_StringSubclass("pkt-1"))


def test_settlement_validation_dataclasses_are_frozen_and_revalidate_hard_flags():
    trade = _record(1)
    report = _report(trade, outcome_report=_outcome_report(_observation(trade, Decimal("1"))))

    with pytest.raises(FrozenInstanceError):
        report.trade_count = 2
    with pytest.raises(FrozenInstanceError):
        report.rows[0].entry_notional = Decimal("0")
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


def test_settlement_validation_report_rejects_status_inconsistent_with_counts():
    trade = _record(1)
    report = _report(trade, outcome_report=_outcome_report(_observation(trade, Decimal("1"))))

    with pytest.raises(ValueError, match="status must match"):
        replace(report, status="pending")
