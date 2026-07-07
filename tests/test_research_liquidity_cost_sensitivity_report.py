from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_liquidity_cost_sensitivity_report import (
    LiquidityCostSensitivityConfig,
    LiquidityCostSensitivityReasonCodeCount,
    LiquidityCostSensitivityReport,
    LiquidityCostSensitivityRow,
    LiquidityCostSensitivityScenario,
    build_research_liquidity_cost_sensitivity_report,
    research_liquidity_cost_sensitivity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedScenarioShape:
    scenario_id: str
    market_slug: str
    outcome_name: str
    bid_ask_spread_rate: Decimal
    available_depth: Decimal
    research_notional: Decimal
    taker_fee_rate: Decimal
    settlement_friction_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> LiquidityCostSensitivityConfig:
    values = {
        "config_version": "research-liquidity-cost-sensitivity-report-v0",
        "pass_max_total_cost_rate": d("0.030000"),
        "watch_max_total_cost_rate": d("0.060000"),
        "pass_min_depth_coverage_ratio": d("1.000000"),
        "watch_min_depth_coverage_ratio": d("0.500000"),
        "depth_shortfall_cost_weight": d("0.100000"),
    }
    values.update(overrides)
    return LiquidityCostSensitivityConfig(**values)


def scenario(
    scenario_id: str,
    *,
    market_slug: str = "market-alpha",
    outcome_name: str = "yes",
    bid_ask_spread_rate: Decimal = d("0.010000"),
    available_depth: Decimal = d("100"),
    research_notional: Decimal = d("50"),
    taker_fee_rate: Decimal = d("0.002000"),
    settlement_friction_rate: Decimal = d("0.003000"),
    reason_codes: tuple[str, ...] = (),
) -> LiquidityCostSensitivityScenario:
    return LiquidityCostSensitivityScenario(
        scenario_id=scenario_id,
        market_slug=market_slug,
        outcome_name=outcome_name,
        bid_ask_spread_rate=bid_ask_spread_rate,
        available_depth=available_depth,
        research_notional=research_notional,
        taker_fee_rate=taker_fee_rate,
        settlement_friction_rate=settlement_friction_rate,
        reason_codes=reason_codes,
    )


def report(
    scenarios: tuple[object, ...],
    *,
    cfg: LiquidityCostSensitivityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> LiquidityCostSensitivityReport:
    return build_research_liquidity_cost_sensitivity_report(
        scenarios,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_research_only_report() -> None:
    liquidity_report = report(())

    assert type(liquidity_report) is LiquidityCostSensitivityReport
    assert liquidity_report.generated_at == GENERATED_AT
    assert liquidity_report.config_version == "research-liquidity-cost-sensitivity-report-v0"
    assert liquidity_report.scenario_count == d("0")
    assert liquidity_report.pass_count == d("0")
    assert liquidity_report.watch_count == d("0")
    assert liquidity_report.block_count == d("0")
    assert liquidity_report.average_total_cost_rate is None
    assert liquidity_report.max_total_cost_rate is None
    assert liquidity_report.status == "block"
    assert liquidity_report.reason_codes == ("no_liquidity_cost_scenarios",)
    assert liquidity_report.reason_code_counts == (
        LiquidityCostSensitivityReasonCodeCount(
            reason_code="no_liquidity_cost_scenarios",
            count=d("1"),
        ),
    )
    assert liquidity_report.rows == ()
    assert liquidity_report.paper_only is True
    assert liquidity_report.report_only is True
    assert liquidity_report.readonly is True
    assert "Research-only" in liquidity_report.research_note


def test_spread_depth_fee_and_settlement_friction_drive_pass_watch_block() -> None:
    liquidity_report = report(
        (
            SuppliedScenarioShape(
                scenario_id="c-block",
                market_slug="gamma",
                outcome_name="yes",
                bid_ask_spread_rate=d("0.035000"),
                available_depth=d("20"),
                research_notional=d("100"),
                taker_fee_rate=d("0.010000"),
                settlement_friction_rate=d("0.010000"),
                reason_codes=("manual_review",),
            ),
            scenario(
                "a-pass",
                market_slug="alpha",
                bid_ask_spread_rate=d("0.010000"),
                available_depth=d("100"),
                research_notional=d("50"),
                taker_fee_rate=d("0.002000"),
                settlement_friction_rate=d("0.003000"),
            ),
            scenario(
                "b-watch",
                market_slug="beta",
                bid_ask_spread_rate=d("0.020000"),
                available_depth=d("75"),
                research_notional=d("100"),
                taker_fee_rate=d("0.005000"),
                settlement_friction_rate=d("0.003000"),
            ),
        ),
    )

    assert liquidity_report.status == "block"
    assert liquidity_report.scenario_count == d("3")
    assert liquidity_report.pass_count == d("1")
    assert liquidity_report.watch_count == d("1")
    assert liquidity_report.block_count == d("1")
    assert liquidity_report.average_total_cost_rate == d("0.067667")
    assert liquidity_report.max_total_cost_rate == d("0.135000")
    assert tuple(row.scenario_id for row in liquidity_report.rows) == (
        "a-pass",
        "b-watch",
        "c-block",
    )

    pass_row, watch_row, block_row = liquidity_report.rows
    assert type(pass_row) is LiquidityCostSensitivityRow
    assert pass_row.depth_coverage_ratio == d("1.000000")
    assert pass_row.depth_shortfall == d("0")
    assert pass_row.explicit_cost_rate == d("0.015000")
    assert pass_row.depth_shortfall_cost_rate == d("0.000000")
    assert pass_row.total_cost_rate == d("0.015000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "adequate_depth",
        "liquidity_cost_pass",
        "low_cost_friction",
        "spread_cost_present",
        "taker_fee_present",
        "settlement_friction_present",
    )

    assert watch_row.depth_coverage_ratio == d("0.750000")
    assert watch_row.depth_shortfall == d("25")
    assert watch_row.depth_shortfall_ratio == d("0.250000")
    assert watch_row.explicit_cost_rate == d("0.028000")
    assert watch_row.depth_shortfall_cost_rate == d("0.025000")
    assert watch_row.total_cost_rate == d("0.053000")
    assert watch_row.status == "watch"
    assert "limited_depth" in watch_row.reason_codes
    assert "elevated_cost_friction" in watch_row.reason_codes

    assert block_row.depth_coverage_ratio == d("0.200000")
    assert block_row.depth_shortfall == d("80")
    assert block_row.depth_shortfall_ratio == d("0.800000")
    assert block_row.explicit_cost_rate == d("0.055000")
    assert block_row.depth_shortfall_cost_rate == d("0.080000")
    assert block_row.total_cost_rate == d("0.135000")
    assert block_row.status == "block"
    assert "insufficient_depth" in block_row.reason_codes
    assert "excessive_cost_friction" in block_row.reason_codes
    assert "input_manual_review" in block_row.reason_codes


def test_payload_is_json_safe_decimal_only_and_has_no_directional_terms() -> None:
    liquidity_report = report((scenario("a-pass"),))

    payload = research_liquidity_cost_sensitivity_report_payload(liquidity_report)
    encoded = json.dumps(payload, sort_keys=True)
    row_payload = payload["rows"][0]

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert row_payload["total_cost_rate"] == "0.015000"
    assert row_payload["available_depth"] == "100"
    assert "scenario_id" not in row_payload
    assert "market_slug" not in row_payload
    assert "outcome_name" not in row_payload
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    lowered = encoded.lower()
    assert "buy" not in lowered
    assert "sell" not in lowered
    assert "position" not in lowered
    assert "recommend" not in lowered


def test_payload_rejects_sensitive_identity_fields() -> None:
    liquidity_report = report((scenario("a-pass"),))
    payload = research_liquidity_cost_sensitivity_report_payload(liquidity_report)
    tampered = {
        **payload,
        "rows": (
            {
                **payload["rows"][0],
                "scenario_id": "a-pass",
                "market_slug": "market-alpha",
                "outcome_name": "yes",
            },
        ),
    }

    with pytest.raises(ValueError, match="scenario_id|market_slug|outcome_name"):
        research_liquidity_cost_sensitivity_report_payload(tampered)  # type: ignore[arg-type]


def test_validation_rejects_bad_types_thresholds_terms_and_flags() -> None:
    with pytest.raises(ValueError, match="pass_max_total_cost_rate"):
        config(pass_max_total_cost_rate=0.03)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="taker_fee_rate"):
        scenario("bad-fee", taker_fee_rate=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="watch_max_total_cost_rate"):
        config(watch_max_total_cost_rate=d("0.020000"))
    with pytest.raises(ValueError, match="depth coverage"):
        config(watch_min_depth_coverage_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((scenario("a-pass"),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (scenario("a-pass"),),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="scenario_id"):
        scenario(" a-pass")
    with pytest.raises(ValueError, match="market_slug"):
        scenario("bad-term", market_slug="buy-token")
    with pytest.raises(ValueError, match="available_depth"):
        scenario("negative-depth", available_depth=d("-1"))
    with pytest.raises(ValueError, match="research_notional"):
        scenario("zero-notional", research_notional=d("0"))
    with pytest.raises(ValueError, match="reason_codes"):
        scenario("bad-reason", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(scenario("bad-flag"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    liquidity_report = report((scenario("a-pass"),))

    with pytest.raises(FrozenInstanceError):
        liquidity_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        liquidity_report.rows[0].total_cost_rate = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="total_cost_rate"):
        replace(liquidity_report.rows[0], total_cost_rate=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(liquidity_report, status="watch")


def test_owned_module_has_no_network_persistence_or_mutation_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_liquidity_cost_sensitivity_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "pathlib",
        "open(",
        ".write(",
        "connect(",
        "place_order",
        "cancel_order",
        "wallet",
        "private_key",
        "auth",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
