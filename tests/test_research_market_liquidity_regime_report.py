from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_liquidity_regime_report import (
    MarketLiquidityRegimeConfig,
    MarketLiquidityRegimeInputRow,
    MarketLiquidityRegimeReasonCodeCount,
    MarketLiquidityRegimeReport,
    MarketLiquidityRegimeReportRow,
    build_research_market_liquidity_regime_report,
    research_market_liquidity_regime_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=5)
_DEFAULT_SOURCE_ID = object()


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketLiquidityRegimeConfig:
    values = {
        "config_version": "research-market-liquidity-regime-report-v0",
        "min_pass_depth_usdc": d("2500.00"),
        "min_watch_depth_usdc": d("500.00"),
        "max_pass_spread_rate": d("0.020000"),
        "max_watch_spread_rate": d("0.070000"),
        "min_pass_activity_usdc": d("1000.00"),
        "min_watch_activity_usdc": d("100.00"),
        "min_pass_activity_count": d("10"),
        "min_watch_activity_count": d("2"),
        "near_settlement_window_hours": d("6.000000"),
        "max_pass_near_settlement_change_rate": d("0.030000"),
        "max_watch_near_settlement_change_rate": d("0.120000"),
        "max_pass_fee_friction_rate": d("0.010000"),
        "max_watch_fee_friction_rate": d("0.030000"),
    }
    values.update(overrides)
    return MarketLiquidityRegimeConfig(**values)


def observation(
    index: int,
    *,
    raw_market_id: str | None = None,
    raw_source_id: str | None | object = _DEFAULT_SOURCE_ID,
    observed_at: datetime = OBSERVED_AT,
    settlement_at: datetime = OBSERVED_AT + timedelta(hours=3),
    depth_usdc: Decimal = d("5000.00"),
    spread_rate: Decimal = d("0.015000"),
    activity_usdc: Decimal = d("2500.00"),
    activity_count: Decimal = d("25"),
    near_settlement_change_rate: Decimal = d("0.020000"),
    fee_friction_rate: Decimal = d("0.005000"),
    reason_codes: tuple[str, ...] = (),
) -> MarketLiquidityRegimeInputRow:
    return MarketLiquidityRegimeInputRow(
        raw_market_id=raw_market_id or f"market-{index:03d}",
        raw_source_id=(
            f"source-{index:03d}" if raw_source_id is _DEFAULT_SOURCE_ID else raw_source_id
        ),
        observed_at=observed_at,
        settlement_at=settlement_at,
        depth_usdc=depth_usdc,
        spread_rate=spread_rate,
        activity_usdc=activity_usdc,
        activity_count=activity_count,
        near_settlement_change_rate=near_settlement_change_rate,
        fee_friction_rate=fee_friction_rate,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketLiquidityRegimeConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketLiquidityRegimeReport:
    return build_research_market_liquidity_regime_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_summary() -> None:
    liquidity_report = report(())

    assert type(liquidity_report) is MarketLiquidityRegimeReport
    assert liquidity_report.generated_at == GENERATED_AT
    assert liquidity_report.config_version == "research-market-liquidity-regime-report-v0"
    assert liquidity_report.observation_count == d("0")
    assert liquidity_report.pass_count == d("0")
    assert liquidity_report.watch_count == d("0")
    assert liquidity_report.blocked_count == d("0")
    assert liquidity_report.minimum_depth_usdc is None
    assert liquidity_report.maximum_spread_rate is None
    assert liquidity_report.total_activity_usdc == d("0.00")
    assert liquidity_report.maximum_fee_friction_rate is None
    assert liquidity_report.minimum_hours_to_settlement is None
    assert liquidity_report.status == "blocked"
    assert liquidity_report.reason_codes == ("no_liquidity_regime_observations",)
    assert liquidity_report.reason_code_counts == (
        MarketLiquidityRegimeReasonCodeCount(
            reason_code="no_liquidity_regime_observations",
            count=d("1"),
        ),
    )
    assert liquidity_report.rows == ()
    assert liquidity_report.paper_only is True
    assert liquidity_report.report_only is True
    assert liquidity_report.readonly is True


def test_deep_tight_active_stable_low_fee_observation_passes() -> None:
    liquidity_report = report((observation(1),))

    assert liquidity_report.status == "pass"
    assert liquidity_report.observation_count == d("1")
    assert liquidity_report.pass_count == d("1")
    assert liquidity_report.watch_count == d("0")
    assert liquidity_report.blocked_count == d("0")
    assert liquidity_report.minimum_depth_usdc == d("5000.00")
    assert liquidity_report.maximum_spread_rate == d("0.015000")
    assert liquidity_report.total_activity_usdc == d("2500.00")
    assert liquidity_report.maximum_fee_friction_rate == d("0.005000")
    assert liquidity_report.minimum_hours_to_settlement == d("3.000000")
    assert liquidity_report.reason_codes == ("liquidity_regime_pass",)

    row = liquidity_report.rows[0]
    assert type(row) is MarketLiquidityRegimeReportRow
    assert row.row_number == d("1")
    assert row.observed_at == OBSERVED_AT
    assert row.settlement_at == OBSERVED_AT + timedelta(hours=3)
    assert row.hours_to_settlement == d("3.000000")
    assert row.depth_status == "pass"
    assert row.spread_status == "pass"
    assert row.activity_status == "pass"
    assert row.near_settlement_status == "pass"
    assert row.fee_friction_status == "pass"
    assert row.status == "pass"
    assert row.reason_codes == (
        "active_activity",
        "deep_depth",
        "liquidity_regime_pass",
        "low_fee_friction",
        "stable_near_settlement",
        "tight_spread",
    )


def test_watch_and_block_outputs_cover_all_regime_dimensions() -> None:
    liquidity_report = report(
        (
            observation(
                2,
                raw_market_id="z-watch",
                depth_usdc=d("1000.00"),
                spread_rate=d("0.050000"),
                activity_usdc=d("300.00"),
                activity_count=d("4"),
                near_settlement_change_rate=d("0.090000"),
                fee_friction_rate=d("0.020000"),
                reason_codes=("manual_liquidity_review",),
            ),
            observation(
                1,
                raw_market_id="a-block",
                depth_usdc=d("100.00"),
                spread_rate=d("0.090000"),
                activity_usdc=d("10.00"),
                activity_count=d("0"),
                near_settlement_change_rate=d("0.200000"),
                fee_friction_rate=d("0.050000"),
            ),
        ),
    )

    assert liquidity_report.status == "blocked"
    assert liquidity_report.pass_count == d("0")
    assert liquidity_report.watch_count == d("1")
    assert liquidity_report.blocked_count == d("1")
    assert liquidity_report.minimum_depth_usdc == d("100.00")
    assert liquidity_report.maximum_spread_rate == d("0.090000")
    assert liquidity_report.total_activity_usdc == d("310.00")
    assert liquidity_report.maximum_fee_friction_rate == d("0.050000")

    blocked, watch = liquidity_report.rows
    assert blocked.row_number == d("1")
    assert blocked.depth_status == "blocked"
    assert blocked.spread_status == "blocked"
    assert blocked.activity_status == "blocked"
    assert blocked.near_settlement_status == "blocked"
    assert blocked.fee_friction_status == "blocked"
    assert blocked.status == "blocked"
    assert blocked.reason_codes == (
        "high_fee_friction",
        "inactive_activity",
        "liquidity_regime_blocked",
        "near_settlement_liquidity_shift",
        "thin_depth",
        "wide_spread",
    )

    assert watch.row_number == d("2")
    assert watch.depth_status == "watch"
    assert watch.spread_status == "watch"
    assert watch.activity_status == "watch"
    assert watch.near_settlement_status == "watch"
    assert watch.fee_friction_status == "watch"
    assert watch.status == "watch"
    assert watch.reason_codes == (
        "input_manual_liquidity_review",
        "liquidity_regime_watch",
        "moderate_activity",
        "moderate_depth",
        "moderate_fee_friction",
        "near_settlement_liquidity_watch",
        "wide_spread",
    )


def test_payload_uses_decimal_strings_and_redacts_raw_market_source_identifiers() -> None:
    liquidity_report = report(
        (
            observation(
                1,
                raw_market_id="secret-market-alpha",
                raw_source_id="secret-source-feed",
            ),
        ),
    )

    payload = research_market_liquidity_regime_report_payload(liquidity_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["rows"][0]["depth_usdc"] == "5000.00"
    assert payload["rows"][0]["spread_rate"] == "0.015000"
    assert payload["rows"][0]["activity_count"] == "25"
    assert "secret-market-alpha" not in encoded
    assert "secret-source-feed" not in encoded
    assert "raw_market_id" not in encoded
    assert "raw_source_id" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_validation_rejects_bad_types_thresholds_times_reason_codes_and_flags() -> None:
    with pytest.raises(ValueError, match="max_pass_spread_rate"):
        config(max_pass_spread_rate=0.02)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_watch_spread_rate"):
        config(max_pass_spread_rate=d("0.080000"), max_watch_spread_rate=d("0.020000"))
    with pytest.raises(ValueError, match="min_watch_depth_usdc"):
        config(min_pass_depth_usdc=d("500.00"), min_watch_depth_usdc=d("2500.00"))
    with pytest.raises(ValueError, match="min_pass_activity_count"):
        config(min_pass_activity_count=_DecimalSubclass("10"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="raw_market_id"):
        observation(1, raw_market_id=" market")
    with pytest.raises(ValueError, match="raw_source_id"):
        observation(1, raw_source_id=" source")
    with pytest.raises(ValueError, match="spread_rate"):
        observation(1, spread_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_usdc"):
        observation(1, depth_usdc=_DecimalSubclass("1.00"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="settlement_at"):
        observation(1, settlement_at=OBSERVED_AT - timedelta(seconds=1))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="readonly"):
        replace(observation(1), readonly=False)
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    liquidity_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        liquidity_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        liquidity_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="hours_to_settlement"):
        replace(liquidity_report.rows[0], hours_to_settlement=d("1.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(liquidity_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="pass_count"):
        replace(liquidity_report, pass_count=d("0"))


def test_owned_module_has_no_io_mutation_or_advice_language_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_regime_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite",
        "wallet",
        "auth",
        "order",
        "buy",
        "sell",
        "long",
        "short",
        "position",
        "recommend",
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
