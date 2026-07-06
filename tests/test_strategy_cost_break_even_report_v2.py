from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_cost_break_even_report_v2 import (
    DEFAULT_STRATEGY_COST_BREAK_EVEN_REPORT_V2_CONFIG_VERSION,
    StrategyCostBreakEvenReportV2Config,
    StrategyCostBreakEvenReportV2Input,
    StrategyCostBreakEvenReportV2Report,
    StrategyCostBreakEvenReportV2Row,
    build_strategy_cost_break_even_report_v2,
    strategy_cost_break_even_report_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyCostBreakEvenReportV2Config:
    values = {
        "config_version": DEFAULT_STRATEGY_COST_BREAK_EVEN_REPORT_V2_CONFIG_VERSION,
        "watch_net_edge_threshold_probability": d("0.010000"),
        "max_observation_age_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return StrategyCostBreakEvenReportV2Config(**values)


def candidate(**overrides: object) -> StrategyCostBreakEvenReportV2Input:
    values = {
        "candidate_ref": "candidate_alpha",
        "market_ref": "probability_alpha",
        "observed_at": datetime(2026, 7, 6, 11, 55, tzinfo=UTC),
        "forecast_probability": d("0.620000"),
        "displayed_probability": d("0.550000"),
        "taker_fee_rate": d("0.020000"),
        "bid_ask_spread_probability": d("0.012000"),
        "expected_slippage_probability": d("0.004000"),
        "settlement_delay_days": d("7.000000"),
        "annualized_capital_lockup_rate": d("0.100000"),
        "confidence_haircut_rate": d("0.150000"),
    }
    values.update(overrides)
    return StrategyCostBreakEvenReportV2Input(**values)


def report(
    *candidates: StrategyCostBreakEvenReportV2Input,
    cfg: StrategyCostBreakEvenReportV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyCostBreakEvenReportV2Report:
    return build_strategy_cost_break_even_report_v2(
        candidates,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_computes_decimal_break_even_probability_costs() -> None:
    summary = report(
        candidate(),
        candidate(
            candidate_ref="candidate_shortfall",
            market_ref="probability_beta",
            forecast_probability=d("0.570000"),
            displayed_probability=d("0.550000"),
            bid_ask_spread_probability=d("0.015000"),
            expected_slippage_probability=d("0.006000"),
            confidence_haircut_rate=d("0.200000"),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == DEFAULT_STRATEGY_COST_BREAK_EVEN_REPORT_V2_CONFIG_VERSION
    assert summary.candidate_count == 2
    assert summary.row_count == 2
    assert summary.clear_count == 1
    assert summary.watch_count == 0
    assert summary.blocked_count == 1
    assert summary.highest_minimum_forecast_edge_probability == d("0.041319")
    assert summary.average_minimum_forecast_edge_probability == d("0.037162")
    assert tuple(row.candidate_ref for row in summary.rows) == (
        "candidate_shortfall",
        "candidate_alpha",
    )

    shortfall = summary.rows[0]
    assert isinstance(shortfall, StrategyCostBreakEvenReportV2Row)
    assert shortfall.gross_forecast_edge_probability == d("0.020000")
    assert shortfall.taker_fee_cost_probability == d("0.011000")
    assert shortfall.bid_ask_spread_cost_probability == d("0.015000")
    assert shortfall.expected_slippage_probability == d("0.006000")
    assert shortfall.settlement_delay_capital_lockup_probability == d("0.001055")
    assert shortfall.direct_cost_probability == d("0.033055")
    assert shortfall.confidence_haircut_cost_probability == d("0.008264")
    assert shortfall.minimum_forecast_edge_probability == d("0.041319")
    assert shortfall.net_forecast_edge_probability == d("-0.021319")
    assert shortfall.age_seconds == d("300.000000")
    assert shortfall.status == "blocked"
    assert shortfall.reason_codes == (
        "below_minimum_forecast_edge",
        "confidence_haircut_applied",
        "settlement_delay_capital_lockup",
    )

    cleared = summary.rows[1]
    assert cleared.gross_forecast_edge_probability == d("0.070000")
    assert cleared.taker_fee_cost_probability == d("0.011000")
    assert cleared.direct_cost_probability == d("0.028055")
    assert cleared.confidence_haircut_cost_probability == d("0.004951")
    assert cleared.minimum_forecast_edge_probability == d("0.033006")
    assert cleared.net_forecast_edge_probability == d("0.036994")
    assert cleared.status == "clear"
    assert cleared.reason_codes == (
        "break_even_edge_cleared",
        "confidence_haircut_applied",
        "settlement_delay_capital_lockup",
    )
    assert cleared.paper_only is True
    assert cleared.report_only is True
    assert cleared.readonly is True
    assert len(cleared.derived_validation_digest) == 64


def test_empty_report_is_paper_only_and_digest_protected() -> None:
    summary = report()

    assert summary.candidate_count == 0
    assert summary.row_count == 0
    assert summary.clear_count == 0
    assert summary.watch_count == 0
    assert summary.blocked_count == 0
    assert summary.highest_minimum_forecast_edge_probability is None
    assert summary.average_minimum_forecast_edge_probability is None
    assert summary.rows == ()
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64


def test_payload_serializes_decimals_as_strings_and_rejects_unsafe_surfaces() -> None:
    generated_at = datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    payload = strategy_cost_break_even_report_v2_payload(
        report(candidate(), generated_at=generated_at),
    )
    payload_text = repr(payload).lower()

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["highest_minimum_forecast_edge_probability"] == "0.033006"
    assert payload["rows"][0]["forecast_probability"] == "0.620000"
    assert payload["rows"][0]["minimum_forecast_edge_probability"] == "0.033006"
    assert payload["rows"][0]["net_forecast_edge_probability"] == "0.036994"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "live" not in payload_text
    assert "auth" not in payload_text
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert "network" not in payload_text
    assert "database" not in payload_text
    assert "persist" not in payload_text
    assert "signing" not in payload_text
    assert "mutation" not in payload_text
    assert "buy" not in payload_text
    assert "sell" not in payload_text
    assert "trade" not in payload_text

    with pytest.raises(ValueError, match="unsafe"):
        strategy_cost_break_even_report_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "sell_path": "not used",
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        strategy_cost_break_even_report_v2_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "note": "connect wallet",
            },
        )

    tampered_payload = strategy_cost_break_even_report_v2_payload(report(candidate()))
    tampered_payload["rows"][0]["minimum_forecast_edge_probability"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_cost_break_even_report_v2_payload(tampered_payload)


def test_rejects_non_decimal_arithmetic_unsafe_text_and_bad_datetimes() -> None:
    with pytest.raises(ValueError, match="forecast_probability"):
        candidate(forecast_probability=0.62)
    with pytest.raises(ValueError, match="candidate_ref"):
        candidate(candidate_ref="wallet_reference")
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="live-cost-report")
    with pytest.raises(ValueError, match="confidence_haircut_rate"):
        candidate(confidence_haircut_rate=d("1.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=datetime(2026, 7, 6, 11, 55))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate(), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(candidate(observed_at=datetime(2026, 7, 6, 12, 1, tzinfo=UTC)))


def test_dataclasses_are_frozen_and_reject_digest_tampering() -> None:
    summary = report(candidate())
    row = summary.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.row_count = 0  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            gross_forecast_edge_probability=d("0.080000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            row_count=0,
            derived_validation_digest=summary.derived_validation_digest,
        )


def test_rejects_inconsistent_rows_and_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        report(
            candidate(candidate_ref="same_ref"),
            candidate(candidate_ref="same_ref", market_ref="probability_beta"),
        )
    with pytest.raises(ValueError, match="inputs must be an iterable"):
        build_strategy_cost_break_even_report_v2(
            "not-an-input",
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="StrategyCostBreakEvenReportV2Input"):
        build_strategy_cost_break_even_report_v2(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="minimum_forecast_edge_probability"):
        StrategyCostBreakEvenReportV2Row(
            candidate_ref="candidate_alpha",
            market_ref="probability_alpha",
            observed_at=datetime(2026, 7, 6, 11, 55, tzinfo=UTC),
            forecast_probability=d("0.620000"),
            displayed_probability=d("0.550000"),
            gross_forecast_edge_probability=d("0.070000"),
            taker_fee_rate=d("0.020000"),
            taker_fee_cost_probability=d("0.011000"),
            bid_ask_spread_cost_probability=d("0.012000"),
            expected_slippage_probability=d("0.004000"),
            settlement_delay_days=d("7.000000"),
            annualized_capital_lockup_rate=d("0.100000"),
            settlement_delay_capital_lockup_probability=d("0.001055"),
            direct_cost_probability=d("0.028055"),
            confidence_haircut_rate=d("0.150000"),
            confidence_haircut_cost_probability=d("0.004951"),
            minimum_forecast_edge_probability=d("0.040000"),
            net_forecast_edge_probability=d("0.030000"),
            age_seconds=d("300.000000"),
            status="clear",
            reason_codes=(
                "break_even_edge_cleared",
                "confidence_haircut_applied",
                "settlement_delay_capital_lockup",
            ),
        )
