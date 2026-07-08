from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_market_resolution_liquidity_cost_frontier_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_COST_FRONTIER_REPORT_CONFIG_VERSION
        ),
        "max_pass_spread_ratio": d("0.020000"),
        "max_watch_spread_ratio": d("0.080000"),
        "min_pass_near_band_depth": d("1000.000000"),
        "min_watch_near_band_depth": d("300.000000"),
        "min_pass_mid_band_depth": d("600.000000"),
        "min_watch_mid_band_depth": d("150.000000"),
        "min_pass_far_band_depth": d("300.000000"),
        "min_watch_far_band_depth": d("50.000000"),
        "max_pass_fee_drag_ratio": d("0.015000"),
        "max_watch_fee_drag_ratio": d("0.050000"),
        "min_pass_slippage_cushion_ratio": d("0.040000"),
        "min_watch_slippage_cushion_ratio": d("0.010000"),
        "max_pass_book_age_seconds": d("300.000000"),
        "max_watch_book_age_seconds": d("1200.000000"),
        "max_pass_volatility_ratio": d("0.200000"),
        "max_watch_volatility_ratio": d("0.500000"),
        "max_pass_settlement_friction_ratio": d("0.150000"),
        "max_watch_settlement_friction_ratio": d("0.400000"),
        "min_pass_resolution_window_seconds": d("3600.000000"),
        "min_watch_resolution_window_seconds": d("900.000000"),
        "pass_frontier_score": d("0.750000"),
        "watch_frontier_score": d("0.450000"),
        "spread_weight": d("0.150000"),
        "depth_band_weight": d("0.200000"),
        "fee_drag_weight": d("0.150000"),
        "slippage_cushion_weight": d("0.150000"),
        "book_age_weight": d("0.100000"),
        "volatility_weight": d("0.100000"),
        "settlement_friction_weight": d("0.100000"),
        "resolution_window_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchMarketResolutionLiquidityCostFrontierConfig(**values)


def snapshot(
    frontier_snapshot_key: str = "frontier-case-pass",
    *,
    observed_at: datetime | None = None,
    resolution_window_seconds: Decimal = d("7200.000000"),
    best_bid_price: Decimal = d("0.490000"),
    best_ask_price: Decimal = d("0.500000"),
    near_band_depth: Decimal = d("1200.000000"),
    mid_band_depth: Decimal = d("800.000000"),
    far_band_depth: Decimal = d("400.000000"),
    fee_drag_ratio: Decimal = d("0.010000"),
    slippage_cushion_ratio: Decimal = d("0.050000"),
    volatility_ratio: Decimal = d("0.150000"),
    settlement_friction_ratio: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketResolutionLiquidityCostFrontierSnapshot(
        frontier_snapshot_key=frontier_snapshot_key,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=120),
        resolution_window_seconds=resolution_window_seconds,
        best_bid_price=best_bid_price,
        best_ask_price=best_ask_price,
        near_band_depth=near_band_depth,
        mid_band_depth=mid_band_depth,
        far_band_depth=far_band_depth,
        fee_drag_ratio=fee_drag_ratio,
        slippage_cushion_ratio=slippage_cushion_ratio,
        volatility_ratio=volatility_ratio,
        settlement_friction_ratio=settlement_friction_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_resolution_liquidity_cost_frontier_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_resolution_liquidity_cost_frontier_review() -> None:
    module = api()
    frontier_report = report()

    assert module.RESOLUTION_LIQUIDITY_COST_FRONTIER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "RESOLUTION_LIQUIDITY_COST_FRONTIER_STATUSES",
        "DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_COST_FRONTIER_REPORT_CONFIG_VERSION",
        "ResearchMarketResolutionLiquidityCostFrontierConfig",
        "ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount",
        "ResearchMarketResolutionLiquidityCostFrontierReport",
        "ResearchMarketResolutionLiquidityCostFrontierRow",
        "ResearchMarketResolutionLiquidityCostFrontierSnapshot",
        "build_research_market_resolution_liquidity_cost_frontier_report",
        "research_market_resolution_liquidity_cost_frontier_report_digest",
        "research_market_resolution_liquidity_cost_frontier_report_payload",
    )
    assert type(frontier_report) is module.ResearchMarketResolutionLiquidityCostFrontierReport
    assert is_dataclass(frontier_report)
    assert frontier_report.generated_at == GENERATED_AT
    assert frontier_report.config_version == (
        "research-market-resolution-liquidity-cost-frontier-report-v0"
    )
    assert frontier_report.input_count == ZERO
    assert frontier_report.pass_count == ZERO
    assert frontier_report.watch_count == ZERO
    assert frontier_report.block_count == ZERO
    assert frontier_report.average_frontier_score is None
    assert frontier_report.max_spread_ratio == ZERO
    assert frontier_report.min_near_band_depth == ZERO
    assert frontier_report.min_mid_band_depth == ZERO
    assert frontier_report.min_far_band_depth == ZERO
    assert frontier_report.max_fee_drag_ratio == ZERO
    assert frontier_report.max_slippage_cushion_gap == ZERO
    assert frontier_report.max_book_age_seconds == ZERO
    assert frontier_report.max_volatility_ratio == ZERO
    assert frontier_report.max_settlement_friction_ratio == ZERO
    assert frontier_report.min_resolution_window_seconds == ZERO
    assert frontier_report.status == "block"
    assert frontier_report.reason_codes == (
        "no_resolution_liquidity_cost_frontier_snapshots",
    )
    assert frontier_report.reason_code_counts == (
        module.ResearchMarketResolutionLiquidityCostFrontierReasonCodeCount(
            reason_code="no_resolution_liquidity_cost_frontier_snapshots",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert frontier_report.rows == ()
    assert frontier_report.paper_only is True
    assert frontier_report.report_only is True
    assert frontier_report.readonly is True


def test_scores_pass_watch_and_block_resolution_window_frontiers() -> None:
    frontier_report = report(
        snapshot(
            "frontier-case-watch",
            observed_at=GENERATED_AT - timedelta(seconds=600),
            resolution_window_seconds=d("1800.000000"),
            best_bid_price=d("0.455000"),
            best_ask_price=d("0.500000"),
            near_band_depth=d("650.000000"),
            mid_band_depth=d("320.000000"),
            far_band_depth=d("160.000000"),
            fee_drag_ratio=d("0.030000"),
            slippage_cushion_ratio=d("0.025000"),
            volatility_ratio=d("0.300000"),
            settlement_friction_ratio=d("0.250000"),
        ),
        snapshot(
            "frontier-case-block",
            observed_at=GENERATED_AT - timedelta(seconds=1800),
            resolution_window_seconds=d("600.000000"),
            best_bid_price=d("0.400000"),
            best_ask_price=d("0.500000"),
            near_band_depth=d("250.000000"),
            mid_band_depth=d("80.000000"),
            far_band_depth=d("20.000000"),
            fee_drag_ratio=d("0.080000"),
            slippage_cushion_ratio=d("0.005000"),
            volatility_ratio=d("0.750000"),
            settlement_friction_ratio=d("0.600000"),
            reason_codes=("manual_review",),
        ),
        snapshot("frontier-case-pass"),
    )

    assert frontier_report.input_count == d("3.000000")
    assert frontier_report.pass_count == d("1.000000")
    assert frontier_report.watch_count == d("1.000000")
    assert frontier_report.block_count == d("1.000000")
    assert frontier_report.average_frontier_score == d("0.468403")
    assert frontier_report.max_spread_ratio == d("0.100000")
    assert frontier_report.min_near_band_depth == d("250.000000")
    assert frontier_report.min_mid_band_depth == d("80.000000")
    assert frontier_report.min_far_band_depth == d("20.000000")
    assert frontier_report.max_fee_drag_ratio == d("0.080000")
    assert frontier_report.max_slippage_cushion_gap == d("0.035000")
    assert frontier_report.max_book_age_seconds == d("1800.000000")
    assert frontier_report.max_volatility_ratio == d("0.750000")
    assert frontier_report.max_settlement_friction_ratio == d("0.600000")
    assert frontier_report.min_resolution_window_seconds == d("600.000000")
    assert frontier_report.status == "block"

    block_row, pass_row, watch_row = frontier_report.rows
    assert tuple(row.public_frontier_ref for row in frontier_report.rows) == (
        "resolution_frontier_group_001",
        "resolution_frontier_group_002",
        "resolution_frontier_group_003",
    )
    assert tuple(row.status for row in frontier_report.rows) == (
        "block",
        "pass",
        "watch",
    )
    assert block_row.spread_ratio == d("0.100000")
    assert block_row.depth_band_coverage_ratio == d("0.080000")
    assert block_row.depth_band_score == d("0.066667")
    assert block_row.fee_drag_ratio == d("0.080000")
    assert block_row.slippage_cushion_gap == d("0.035000")
    assert block_row.book_age_pressure == d("1.000000")
    assert block_row.cost_pressure == d("0.966146")
    assert block_row.frontier_score == d("0.040416")
    assert block_row.reason_codes == (
        "book_age_block",
        "depth_band_block",
        "fee_drag_block",
        "frontier_score_block",
        "input_manual_review",
        "resolution_window_block",
        "settlement_friction_block",
        "slippage_cushion_block",
        "spread_block",
        "volatility_block",
    )
    assert pass_row.depth_band_coverage_ratio == d("0.333333")
    assert pass_row.depth_band_score == d("1.000000")
    assert pass_row.spread_score == d("0.875000")
    assert pass_row.fee_drag_score == d("0.800000")
    assert pass_row.slippage_cushion_score == d("1.000000")
    assert pass_row.book_age_score == d("0.900000")
    assert pass_row.volatility_score == d("0.700000")
    assert pass_row.settlement_friction_score == d("0.750000")
    assert pass_row.resolution_window_score == d("1.000000")
    assert pass_row.cost_pressure == d("0.142188")
    assert pass_row.frontier_score == d("0.886250")
    assert pass_row.reason_codes == (
        "book_age_pass",
        "depth_band_pass",
        "fee_drag_pass",
        "frontier_score_pass",
        "resolution_window_pass",
        "settlement_friction_pass",
        "slippage_cushion_pass",
        "spread_pass",
        "volatility_pass",
    )
    assert watch_row.slippage_cushion_gap == d("0.015000")
    assert watch_row.depth_band_score == d("0.533333")
    assert watch_row.cost_pressure == d("0.535156")
    assert watch_row.frontier_score == d("0.478542")
    assert watch_row.reason_codes == (
        "book_age_watch",
        "depth_band_watch",
        "fee_drag_watch",
        "frontier_score_watch",
        "resolution_window_watch",
        "settlement_friction_watch",
        "slippage_cushion_watch",
        "spread_watch",
        "volatility_watch",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        snapshot("frontier-case-z", reason_codes=("zeta", "alpha")),
        snapshot("frontier-case-a"),
    )
    second = report(
        snapshot("frontier-case-a"),
        snapshot("frontier-case-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = (
        module.research_market_resolution_liquidity_cost_frontier_report_payload(first)
    )
    second_payload = (
        module.research_market_resolution_liquidity_cost_frontier_report_payload(second)
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert (
        module.research_market_resolution_liquidity_cost_frontier_report_digest(first)
        == module.research_market_resolution_liquidity_cost_frontier_report_digest(second)
        == first.derived_validation_digest
    )
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["public_frontier_ref"] == (
        "resolution_frontier_group_001"
    )
    assert first_payload["rows"][0]["frontier_score"] == "0.886250"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "frontier-case-a" not in encoded
    assert "frontier-case-z" not in encoded
    assert not any(
        _has_forbidden_public_surface(str(value))
        for value in _walk_payload_strings(first_payload)
    )
    assert not any(
        _has_forbidden_public_surface(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(snapshot())

    for value in (
        config(),
        snapshot(),
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].frontier_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="best_bid_price"):
        snapshot(best_bid_price=0.49)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        snapshot(fee_drag_ratio=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="near_band_depth"):
        snapshot(near_band_depth=DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="slippage_cushion_ratio"):
        snapshot(slippage_cushion_ratio=d("1.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(snapshot(), generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="best_ask_price"):
        snapshot(best_bid_price=d("0.500000"), best_ask_price=d("0.490000"))
    with pytest.raises(ValueError, match="mid_band_depth"):
        snapshot(near_band_depth=d("100.000000"), mid_band_depth=d("101.000000"))
    with pytest.raises(ValueError, match="far_band_depth"):
        snapshot(mid_band_depth=d("100.000000"), far_band_depth=d("101.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        snapshot(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="unsafe public"):
        snapshot(reason_codes=("market_id",))
    with pytest.raises(ValueError, match="paper_only"):
        snapshot(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchMarketResolutionLiquidityCostFrontierConfig,), {})


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


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _walk_payload_strings(value: object) -> tuple[str, ...]:
    strings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(_walk_payload_strings(item))
    elif isinstance(value, str):
        strings.append(value)
    return tuple(strings)


def _has_forbidden_public_surface(value: str) -> bool:
    normalized = value.lower()
    forbidden_fragments = (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "position",
        "sizing",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)
