from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_liquidity_stress_scenario_report import (
    DEFAULT_RESEARCH_MARKET_LIQUIDITY_STRESS_SCENARIO_CONFIG_VERSION,
    ResearchMarketLiquidityStressScenarioConfig,
    ResearchMarketLiquidityStressScenarioInput,
    ResearchMarketLiquidityStressScenarioReasonCodeCount,
    ResearchMarketLiquidityStressScenarioReport,
    ResearchMarketLiquidityStressScenarioRow,
    build_research_market_liquidity_stress_scenario_report,
    research_market_liquidity_stress_scenario_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketLiquidityStressScenarioConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_MARKET_LIQUIDITY_STRESS_SCENARIO_CONFIG_VERSION,
        "min_pass_liquidity_score": d("0.750000"),
        "min_watch_liquidity_score": d("0.400000"),
        "max_watch_depth_decline_ratio": d("0.250000"),
        "max_block_depth_decline_ratio": d("0.600000"),
        "max_watch_spread_widening_ratio": d("0.500000"),
        "max_block_spread_widening_ratio": d("1.500000"),
        "max_watch_fee_rate_bps": d("50.000000"),
        "max_block_fee_rate_bps": d("100.000000"),
        "watch_settlement_window_seconds": d("86400.000000"),
        "block_settlement_window_seconds": d("3600.000000"),
        "max_watch_information_shock_probability_move": d("0.080000"),
        "max_block_information_shock_probability_move": d("0.180000"),
        "depth_weight": d("0.300000"),
        "spread_weight": d("0.250000"),
        "fee_weight": d("0.150000"),
        "settlement_weight": d("0.150000"),
        "information_shock_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchMarketLiquidityStressScenarioConfig(**values)


def scenario(
    scenario_key: str,
    *,
    scenario_label: str = "public liquidity stress scenario",
    baseline_depth_usd: Decimal = d("100000.000000"),
    stressed_depth_usd: Decimal = d("85000.000000"),
    baseline_spread_bps: Decimal = d("50.000000"),
    stressed_spread_bps: Decimal = d("60.000000"),
    fee_rate_bps: Decimal = d("20.000000"),
    seconds_to_settlement: Decimal = d("604800.000000"),
    information_shock_probability_move: Decimal = d("0.030000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("depth_snapshot_reviewed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketLiquidityStressScenarioInput:
    return ResearchMarketLiquidityStressScenarioInput(
        scenario_key=scenario_key,
        scenario_label=scenario_label,
        baseline_depth_usd=baseline_depth_usd,
        stressed_depth_usd=stressed_depth_usd,
        baseline_spread_bps=baseline_spread_bps,
        stressed_spread_bps=stressed_spread_bps,
        fee_rate_bps=fee_rate_bps,
        seconds_to_settlement=seconds_to_settlement,
        information_shock_probability_move=information_shock_probability_move,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchMarketLiquidityStressScenarioInput,
    cfg: ResearchMarketLiquidityStressScenarioConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketLiquidityStressScenarioReport:
    return build_research_market_liquidity_stress_scenario_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_report_scores_pass_watch_and_block_liquidity_stress_scenarios() -> None:
    liquidity_report = report(
        scenario("scenario-pass"),
        scenario(
            "scenario-watch",
            baseline_depth_usd=d("100000.000000"),
            stressed_depth_usd=d("65000.000000"),
            baseline_spread_bps=d("40.000000"),
            stressed_spread_bps=d("70.000000"),
            fee_rate_bps=d("60.000000"),
            seconds_to_settlement=d("43200.000000"),
            information_shock_probability_move=d("0.100000"),
            reason_codes=("manual_liquidity_review",),
        ),
        scenario(
            "scenario-block",
            baseline_depth_usd=d("100000.000000"),
            stressed_depth_usd=d("25000.000000"),
            baseline_spread_bps=d("40.000000"),
            stressed_spread_bps=d("110.000000"),
            fee_rate_bps=d("125.000000"),
            seconds_to_settlement=d("1800.000000"),
            information_shock_probability_move=d("0.200000"),
            reason_codes=("information_event_active",),
        ),
    )

    assert is_dataclass(liquidity_report)
    assert liquidity_report.config_version == (
        "research-market-liquidity-stress-scenario-report-v0"
    )
    assert liquidity_report.scenario_count == d("3.000000")
    assert liquidity_report.pass_count == d("1.000000")
    assert liquidity_report.watch_count == d("1.000000")
    assert liquidity_report.block_count == d("1.000000")
    assert liquidity_report.min_liquidity_score == d("0.075000")
    assert liquidity_report.max_depth_decline_ratio == d("0.750000")
    assert liquidity_report.max_spread_widening_ratio == d("1.750000")
    assert liquidity_report.max_fee_rate_bps == d("125.000000")
    assert liquidity_report.min_seconds_to_settlement == d("1800.000000")
    assert liquidity_report.max_information_shock_probability_move == d("0.200000")
    assert liquidity_report.status == "block"
    assert len(liquidity_report.derived_validation_digest) == 64
    assert liquidity_report.paper_only is True
    assert liquidity_report.report_only is True
    assert liquidity_report.readonly is True

    block_row, passed, watched = liquidity_report.rows
    assert tuple(row.stress_status for row in liquidity_report.rows) == (
        "block",
        "pass",
        "watch",
    )
    assert block_row.scenario_key == "scenario-block"
    assert block_row.depth_decline_ratio == d("0.750000")
    assert block_row.spread_widening_ratio == d("1.750000")
    assert block_row.fee_friction_score == d("1.000000")
    assert block_row.settlement_proximity_score == d("1.000000")
    assert block_row.information_shock_score == d("1.000000")
    assert block_row.liquidity_score == d("0.075000")
    assert block_row.reason_codes == (
        "fee_friction_severe_block",
        "information_shock_severe_block",
        "input_information_event_active",
        "liquidity_depth_decline_severe_block",
        "liquidity_spread_widening_severe_block",
        "liquidity_stress_score_low_block",
        "settlement_window_imminent_block",
    )

    assert passed.scenario_key == "scenario-pass"
    assert passed.depth_decline_ratio == d("0.150000")
    assert passed.spread_widening_ratio == d("0.200000")
    assert passed.fee_friction_score == d("0.200000")
    assert passed.settlement_proximity_score == ZERO
    assert passed.information_shock_score == d("0.166667")
    assert passed.liquidity_score == d("0.850000")
    assert passed.reason_codes == (
        "input_depth_snapshot_reviewed",
        "liquidity_stress_scenario_clear",
    )

    assert watched.scenario_key == "scenario-watch"
    assert watched.depth_decline_ratio == d("0.350000")
    assert watched.spread_widening_ratio == d("0.750000")
    assert watched.fee_friction_score == d("0.600000")
    assert watched.settlement_proximity_score == d("0.521739")
    assert watched.information_shock_score == d("0.555556")
    assert watched.liquidity_score == d("0.455906")
    assert watched.reason_codes == (
        "fee_friction_elevated_watch",
        "information_shock_elevated_watch",
        "input_manual_liquidity_review",
        "liquidity_depth_decline_elevated_watch",
        "liquidity_spread_widening_elevated_watch",
        "liquidity_stress_score_thin_watch",
        "settlement_window_near_watch",
    )


def test_empty_report_is_watch_with_decimal_counts_and_hard_flags() -> None:
    liquidity_report = report()

    assert liquidity_report.scenario_count == ZERO
    assert liquidity_report.pass_count == ZERO
    assert liquidity_report.watch_count == ZERO
    assert liquidity_report.block_count == ZERO
    assert liquidity_report.min_liquidity_score == ZERO
    assert liquidity_report.status == "watch"
    assert liquidity_report.reason_codes == ("liquidity_stress_scenario_empty",)
    assert liquidity_report.reason_code_counts == (
        ResearchMarketLiquidityStressScenarioReasonCodeCount(
            reason_code="liquidity_stress_scenario_empty",
            count=d("1.000000"),
            scenario_ratio=d("0.000000"),
        ),
    )
    assert liquidity_report.rows == ()

    populated = report(scenario("scenario-pass"))
    for value in (liquidity_report, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_ratio",
                    "_score",
                    "_bps",
                    "_usd",
                    "_seconds",
                    "_move",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_serializes_public_values_without_raw_identifiers_or_numeric_leaks() -> None:
    liquidity_report = report(
        scenario(
            "scenario-pass",
            observed_at=datetime(
                2026,
                7,
                6,
                8,
                45,
                tzinfo=UTC,
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            6,
            9,
            0,
            tzinfo=UTC,
        ),
    )

    payload = research_market_liquidity_stress_scenario_report_payload(liquidity_report)

    assert payload["generated_at"] == "2026-07-06T09:00:00+00:00"
    assert payload["scenario_count"] == "1.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T08:45:00+00:00"
    assert payload["rows"][0]["liquidity_score"] == "0.850000"
    assert payload["derived_validation_digest"] == liquidity_report.derived_validation_digest
    assert "raw_market_id" not in json.dumps(payload, sort_keys=True)
    assert "raw_source_id" not in json.dumps(payload, sort_keys=True)
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    tampered = dict(payload)
    tampered["pass_count"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_market_liquidity_stress_scenario_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(liquidity_report, pass_count=d("2.000000"))


def test_public_payload_rejects_raw_market_source_and_action_language() -> None:
    payload = research_market_liquidity_stress_scenario_report_payload(
        report(scenario("scenario-pass")),
    )

    for key in (
        "raw_market_id",
        "raw_source_id",
        "condition_id",
        "token_id",
        "source_url",
        "wallet_address",
        "auth_header",
        "order_id",
        "mutation_name",
        "network_url",
        "database_table",
        "buy_instruction",
        "sell_instruction",
        "position_size",
        "recommendation_text",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            research_market_liquidity_stress_scenario_report_payload(unsafe)

    for value in (
        "raw_market_id:abc",
        "source_url:https://example.invalid",
        "buy this outcome",
        "sell this outcome",
        "increase position",
        "recommendation pending",
        "wallet signer",
        "live trading",
        "database write",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            research_market_liquidity_stress_scenario_report_payload(unsafe)

    numeric = dict(payload)
    numeric["scenario_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        research_market_liquidity_stress_scenario_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_market_liquidity_stress_scenario_report_payload(downgraded)


def test_validation_rejects_non_decimal_values_duplicate_keys_bad_times_and_flags() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        scenario("bad-decimal", baseline_depth_usd=100000)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        scenario(
            "bad-subclass",
            baseline_depth_usd=_DecimalSubclass("100000.000000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(scenario("aware"), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        scenario("naive-time", observed_at=datetime(2026, 7, 6, 11, 45))
    with pytest.raises(ValueError, match="observed_at"):
        scenario(
            "time-subclass",
            observed_at=_DatetimeSubclass(2026, 7, 6, 11, 45, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report(scenario("future", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        report(scenario("duplicate"), scenario("duplicate"))
    with pytest.raises(ValueError, match="paper_only"):
        scenario("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_research_market_liquidity_stress_scenario_report(
            (),
            config=ResearchMarketLiquidityStressScenarioConfig.__new__(
                type(
                    "ConfigSubclass",
                    (ResearchMarketLiquidityStressScenarioConfig,),
                    {},
                ),
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="weight"):
        config(depth_weight=d("0.400000"))
    with pytest.raises(ValueError, match="settlement"):
        config(block_settlement_window_seconds=d("90000.000000"))

    frozen = scenario("scenario-pass")
    with pytest.raises(FrozenInstanceError):
        frozen.scenario_key = "changed"  # type: ignore[misc]


def test_manual_materialized_rows_and_reports_validate_consistency() -> None:
    liquidity_report = report(scenario("scenario-pass"))
    row = liquidity_report.rows[0]

    with pytest.raises(ValueError, match="liquidity_score"):
        ResearchMarketLiquidityStressScenarioRow(
            **{
                **row.__dict__,
                "liquidity_score": d("0.100000"),
            },
        )

    with pytest.raises(ValueError, match="status"):
        ResearchMarketLiquidityStressScenarioReport(
            **{
                **liquidity_report.__dict__,
                "status": "block",
            },
        )


def test_non_default_score_thresholds_are_used_for_row_consistency() -> None:
    custom_config = config(
        min_pass_liquidity_score=d("0.700000"),
        min_watch_liquidity_score=d("0.300000"),
        max_watch_depth_decline_ratio=d("0.350000"),
        max_block_depth_decline_ratio=d("0.700000"),
    )

    liquidity_report = report(
        scenario(
            "custom-pass",
            stressed_depth_usd=d("70000.000000"),
            baseline_spread_bps=d("40.000000"),
            stressed_spread_bps=d("60.000000"),
        ),
        cfg=custom_config,
    )

    row = liquidity_report.rows[0]
    assert liquidity_report.status == "pass"
    assert liquidity_report.pass_count == d("1.000000")
    assert liquidity_report.watch_count == ZERO
    assert liquidity_report.block_count == ZERO
    assert row.stress_status == "pass"
    assert row.liquidity_score == d("0.730000")
    assert row.reason_codes == (
        "input_depth_snapshot_reviewed",
        "liquidity_stress_scenario_clear",
    )


def test_single_threshold_watch_and_block_rows_validate_against_full_criteria() -> None:
    liquidity_report = report(
        scenario(
            "fee-only-block",
            stressed_depth_usd=d("95000.000000"),
            stressed_spread_bps=d("51.000000"),
            fee_rate_bps=d("101.000000"),
            information_shock_probability_move=ZERO,
        ),
        scenario(
            "settlement-only-watch",
            stressed_depth_usd=d("95000.000000"),
            stressed_spread_bps=d("51.000000"),
            fee_rate_bps=ZERO,
            seconds_to_settlement=d("50000.000000"),
            information_shock_probability_move=ZERO,
        ),
    )

    block_row, watch_row = liquidity_report.rows
    assert block_row.scenario_key == "fee-only-block"
    assert block_row.stress_status == "block"
    assert block_row.liquidity_score == d("0.830000")
    assert block_row.reason_codes == (
        "fee_friction_severe_block",
        "input_depth_snapshot_reviewed",
    )
    assert watch_row.scenario_key == "settlement-only-watch"
    assert watch_row.stress_status == "watch"
    assert watch_row.liquidity_score == d("0.914058")
    assert watch_row.reason_codes == (
        "input_depth_snapshot_reviewed",
        "settlement_window_near_watch",
    )
    assert liquidity_report.status == "block"
    assert liquidity_report.block_count == d("1.000000")
    assert liquidity_report.watch_count == d("1.000000")


def test_module_exposes_no_live_trading_network_wallet_order_or_persistence_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_stress_scenario_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_runtime_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "open(",
        "connect(",
        "commit(",
        "send_order",
        "place_order",
    )

    assert all(term not in source for term in forbidden_runtime_terms)
