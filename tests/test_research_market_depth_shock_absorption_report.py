from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_depth_shock_absorption_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_DEPTH_SHOCK_ABSORPTION_REPORT_CONFIG_VERSION
        ),
        "max_pass_shock_shortfall_ratio": d("0.050000"),
        "max_watch_shock_shortfall_ratio": d("0.250000"),
        "max_pass_spread_widening": d("0.020000"),
        "max_watch_spread_widening": d("0.060000"),
        "max_pass_imbalance_volatility": d("0.200000"),
        "max_watch_imbalance_volatility": d("0.500000"),
        "max_pass_stale_book_age_seconds": d("120.000000"),
        "max_watch_stale_book_age_seconds": d("600.000000"),
        "min_pass_fee_slippage_cushion_ratio": d("0.150000"),
        "min_watch_fee_slippage_cushion_ratio": d("0.050000"),
        "pass_absorption_score": d("0.750000"),
        "watch_absorption_score": d("0.450000"),
        "depth_absorption_weight": d("0.350000"),
        "spread_resilience_weight": d("0.200000"),
        "imbalance_stability_weight": d("0.150000"),
        "freshness_weight": d("0.150000"),
        "fee_slippage_cushion_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchMarketDepthShockAbsorptionConfig(**values)


def observation(
    book_snapshot_key: str = "shock-case-pass",
    *,
    observed_at: datetime | None = None,
    last_book_update_at: datetime | None = None,
    target_shock_probability: Decimal = d("0.100000"),
    near_band_depth: Decimal = d("0.060000"),
    mid_band_depth: Decimal = d("0.030000"),
    far_band_depth: Decimal = d("0.010000"),
    spread_widening: Decimal = d("0.010000"),
    imbalance_volatility: Decimal = d("0.100000"),
    fee_cushion: Decimal = d("0.010000"),
    slippage_cushion: Decimal = d("0.010000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketDepthShockAbsorptionObservation(
        book_snapshot_key=book_snapshot_key,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=45),
        last_book_update_at=last_book_update_at or GENERATED_AT - timedelta(seconds=45),
        target_shock_probability=target_shock_probability,
        near_band_depth=near_band_depth,
        mid_band_depth=mid_band_depth,
        far_band_depth=far_band_depth,
        spread_widening=spread_widening,
        imbalance_volatility=imbalance_volatility,
        fee_cushion=fee_cushion,
        slippage_cushion=slippage_cushion,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_depth_shock_absorption_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_depth_shock_absorption_review() -> None:
    module = api()
    absorption_report = report()

    assert module.DEPTH_SHOCK_ABSORPTION_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEPTH_SHOCK_ABSORPTION_STATUSES",
        "DEFAULT_RESEARCH_MARKET_DEPTH_SHOCK_ABSORPTION_REPORT_CONFIG_VERSION",
        "ResearchMarketDepthShockAbsorptionConfig",
        "ResearchMarketDepthShockAbsorptionObservation",
        "ResearchMarketDepthShockAbsorptionReasonCodeCount",
        "ResearchMarketDepthShockAbsorptionReport",
        "ResearchMarketDepthShockAbsorptionRow",
        "build_research_market_depth_shock_absorption_report",
        "research_market_depth_shock_absorption_report_digest",
        "research_market_depth_shock_absorption_report_payload",
    )
    assert type(absorption_report) is module.ResearchMarketDepthShockAbsorptionReport
    assert is_dataclass(absorption_report)
    assert absorption_report.generated_at == GENERATED_AT
    assert (
        absorption_report.config_version
        == "research-market-depth-shock-absorption-report-v0"
    )
    assert absorption_report.input_count == ZERO
    assert absorption_report.pass_count == ZERO
    assert absorption_report.watch_count == ZERO
    assert absorption_report.block_count == ZERO
    assert absorption_report.average_depth_shock_absorption_score is None
    assert absorption_report.min_net_depth_coverage_ratio == ZERO
    assert absorption_report.max_shock_shortfall_ratio == ZERO
    assert absorption_report.max_spread_widening == ZERO
    assert absorption_report.max_imbalance_volatility == ZERO
    assert absorption_report.max_stale_book_age_seconds == ZERO
    assert absorption_report.min_fee_slippage_cushion_ratio == ZERO
    assert absorption_report.status == "block"
    assert absorption_report.reason_codes == ("no_depth_shock_absorption_observations",)
    assert absorption_report.reason_code_counts == (
        module.ResearchMarketDepthShockAbsorptionReasonCodeCount(
            reason_code="no_depth_shock_absorption_observations",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert absorption_report.rows == ()
    assert absorption_report.paper_only is True
    assert absorption_report.report_only is True
    assert absorption_report.readonly is True


def test_scores_pass_watch_and_block_depth_shock_observations() -> None:
    absorption_report = report(
        observation(
            "shock-case-watch",
            last_book_update_at=GENERATED_AT - timedelta(seconds=180),
            target_shock_probability=d("0.100000"),
            near_band_depth=d("0.035000"),
            mid_band_depth=d("0.025000"),
            far_band_depth=d("0.025000"),
            spread_widening=d("0.030000"),
            imbalance_volatility=d("0.300000"),
            fee_cushion=d("0.005000"),
            slippage_cushion=d("0.005000"),
        ),
        observation(
            "shock-case-block",
            last_book_update_at=GENERATED_AT - timedelta(seconds=700),
            target_shock_probability=d("0.100000"),
            near_band_depth=d("0.020000"),
            mid_band_depth=d("0.015000"),
            far_band_depth=d("0.015000"),
            spread_widening=d("0.080000"),
            imbalance_volatility=d("0.600000"),
            fee_cushion=d("0.002000"),
            slippage_cushion=d("0.002000"),
            reason_codes=("manual_depth_review",),
        ),
        observation("shock-case-pass"),
    )

    assert absorption_report.input_count == d("3.000000")
    assert absorption_report.pass_count == d("1.000000")
    assert absorption_report.watch_count == d("1.000000")
    assert absorption_report.block_count == d("1.000000")
    assert absorption_report.average_depth_shock_absorption_score == d("0.617306")
    assert absorption_report.min_net_depth_coverage_ratio == d("0.540000")
    assert absorption_report.max_shock_shortfall_ratio == d("0.460000")
    assert absorption_report.max_spread_widening == d("0.080000")
    assert absorption_report.max_imbalance_volatility == d("0.600000")
    assert absorption_report.max_stale_book_age_seconds == d("700.000000")
    assert absorption_report.min_fee_slippage_cushion_ratio == d("0.040000")
    assert absorption_report.status == "block"

    block_row, pass_row, watch_row = absorption_report.rows
    assert tuple(row.absorption_group_ref for row in absorption_report.rows) == (
        "depth_shock_group_001",
        "depth_shock_group_002",
        "depth_shock_group_003",
    )
    assert tuple(row.status for row in absorption_report.rows) == (
        "block",
        "pass",
        "watch",
    )
    assert block_row.total_band_depth == d("0.050000")
    assert block_row.fee_slippage_cushion == d("0.004000")
    assert block_row.net_absorbable_probability == d("0.054000")
    assert block_row.net_depth_coverage_ratio == d("0.540000")
    assert block_row.shock_shortfall_ratio == d("0.460000")
    assert block_row.stale_book_pressure == d("1.000000")
    assert block_row.depth_shock_absorption_score == d("0.229000")
    assert block_row.reason_codes == (
        "depth_band_shortfall_block",
        "depth_shock_absorption_block",
        "fee_slippage_cushion_block",
        "imbalance_volatility_block",
        "input_manual_depth_review",
        "spread_widening_block",
        "stale_book_age_block",
    )
    assert pass_row.total_band_depth == d("0.100000")
    assert pass_row.fee_slippage_cushion_ratio == d("0.200000")
    assert pass_row.net_depth_coverage_ratio == d("1.000000")
    assert pass_row.shock_shortfall_ratio == ZERO
    assert pass_row.stale_book_age_seconds == d("45.000000")
    assert pass_row.stale_book_pressure == d("0.075000")
    assert pass_row.depth_absorption_score == d("1.000000")
    assert pass_row.spread_resilience_score == d("0.833333")
    assert pass_row.imbalance_stability_score == d("0.800000")
    assert pass_row.freshness_score == d("0.925000")
    assert pass_row.fee_slippage_cushion_score == d("1.000000")
    assert pass_row.depth_shock_absorption_score == d("0.925417")
    assert pass_row.reason_codes == (
        "depth_band_shortfall_pass",
        "depth_shock_absorption_pass",
        "fee_slippage_cushion_pass",
        "imbalance_volatility_pass",
        "spread_widening_pass",
        "stale_book_age_pass",
    )
    assert watch_row.net_depth_coverage_ratio == d("0.950000")
    assert watch_row.shock_shortfall_ratio == d("0.050000")
    assert watch_row.fee_slippage_cushion_ratio == d("0.100000")
    assert watch_row.stale_book_pressure == d("0.300000")
    assert watch_row.depth_shock_absorption_score == d("0.697500")
    assert watch_row.reason_codes == (
        "depth_band_shortfall_watch",
        "depth_shock_absorption_watch",
        "fee_slippage_cushion_watch",
        "imbalance_volatility_watch",
        "spread_widening_watch",
        "stale_book_age_watch",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        observation("shock-case-z", reason_codes=("zeta", "alpha")),
        observation("shock-case-a"),
    )
    second = report(
        observation("shock-case-a"),
        observation("shock-case-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_depth_shock_absorption_report_payload(first)
    second_payload = module.research_market_depth_shock_absorption_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert module.research_market_depth_shock_absorption_report_digest(first) == (
        module.research_market_depth_shock_absorption_report_digest(second)
    )
    assert len(module.research_market_depth_shock_absorption_report_digest(first)) == 64
    int(module.research_market_depth_shock_absorption_report_digest(first), 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["absorption_group_ref"] == "depth_shock_group_001"
    assert first_payload["rows"][0]["target_shock_probability"] == "0.100000"
    assert first_payload["rows"][0]["net_depth_coverage_ratio"] == "1.000000"
    assert first_payload["rows"][0]["depth_shock_absorption_score"] == "0.925417"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "shock-case-a" not in encoded
    assert "shock-case-z" not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(observation())

    for value in (config(), observation(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].depth_shock_absorption_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="target_shock_probability"):
        observation(target_shock_probability=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_widening"):
        observation(spread_widening=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="depth bands"):
        observation(
            near_band_depth=ZERO,
            mid_band_depth=ZERO,
            far_band_depth=ZERO,
        )
    with pytest.raises(ValueError, match="imbalance_volatility"):
        observation(imbalance_volatility=d("1.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="unsafe public"):
        observation(reason_codes=("market_id",))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="book_snapshot_key"):
        report(observation("duplicate"), observation("duplicate"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchMarketDepthShockAbsorptionConfig,), {})


def test_owned_module_has_no_db_network_wallet_execution_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_depth_shock_absorption_report.py"
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
        "postgres",
        "private_key",
        "place_order",
        "cancel_order",
        "order_size",
        "live_trading",
        "trade_recommendation",
        "connect(",
        "open(",
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


def _has_forbidden_public_surface_key(key: str) -> bool:
    normalized = key.lower()
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
        "buy",
        "sell",
        "size",
        "sizing",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)
