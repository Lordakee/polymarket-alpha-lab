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
        "polymarket_alpha_lab.research_market_liquidity_depth_decay_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_DECAY_REPORT_CONFIG_VERSION
        ),
        "max_pass_book_age_seconds": d("300.000000"),
        "max_watch_book_age_seconds": d("900.000000"),
        "max_pass_spread": d("0.020000"),
        "max_watch_spread": d("0.050000"),
        "max_pass_depth_decay_ratio": d("0.250000"),
        "max_watch_depth_decay_ratio": d("0.600000"),
        "max_pass_unchanged_book_seconds": d("180.000000"),
        "max_watch_unchanged_book_seconds": d("600.000000"),
        "pass_liquidity_depth_decay_score": d("0.750000"),
        "watch_liquidity_depth_decay_score": d("0.450000"),
        "depth_freshness_weight": d("0.300000"),
        "spread_pressure_weight": d("0.300000"),
        "depth_decay_weight": d("0.250000"),
        "stale_book_risk_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchMarketLiquidityDepthDecayConfig(**values)


def snapshot(
    book_snapshot_key: str = "depth-case-pass",
    *,
    observed_at: datetime | None = None,
    last_depth_change_at: datetime | None = None,
    best_bid_price: Decimal = d("0.490000"),
    best_ask_price: Decimal = d("0.500000"),
    near_band_depth: Decimal = d("1000.000000"),
    far_band_depth: Decimal = d("850.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketLiquidityDepthDecaySnapshot(
        book_snapshot_key=book_snapshot_key,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=120),
        last_depth_change_at=last_depth_change_at or GENERATED_AT - timedelta(seconds=60),
        best_bid_price=best_bid_price,
        best_ask_price=best_ask_price,
        near_band_depth=near_band_depth,
        far_band_depth=far_band_depth,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_liquidity_depth_decay_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_liquidity_depth_decay_review() -> None:
    module = api()
    depth_report = report()

    assert module.LIQUIDITY_DEPTH_DECAY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "LIQUIDITY_DEPTH_DECAY_STATUSES",
        "DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_DECAY_REPORT_CONFIG_VERSION",
        "ResearchMarketLiquidityDepthDecayConfig",
        "ResearchMarketLiquidityDepthDecayReasonCodeCount",
        "ResearchMarketLiquidityDepthDecayReport",
        "ResearchMarketLiquidityDepthDecayRow",
        "ResearchMarketLiquidityDepthDecaySnapshot",
        "build_research_market_liquidity_depth_decay_report",
        "research_market_liquidity_depth_decay_report_digest",
        "research_market_liquidity_depth_decay_report_payload",
    )
    assert type(depth_report) is module.ResearchMarketLiquidityDepthDecayReport
    assert is_dataclass(depth_report)
    assert depth_report.generated_at == GENERATED_AT
    assert depth_report.config_version == "research-market-liquidity-depth-decay-report-v0"
    assert depth_report.input_count == ZERO
    assert depth_report.pass_count == ZERO
    assert depth_report.watch_count == ZERO
    assert depth_report.block_count == ZERO
    assert depth_report.average_liquidity_depth_decay_score is None
    assert depth_report.max_book_age_seconds == ZERO
    assert depth_report.max_spread_pressure == ZERO
    assert depth_report.max_depth_decay_ratio == ZERO
    assert depth_report.max_unchanged_book_seconds == ZERO
    assert depth_report.status == "block"
    assert depth_report.reason_codes == ("no_liquidity_depth_decay_snapshots",)
    assert depth_report.reason_code_counts == (
        module.ResearchMarketLiquidityDepthDecayReasonCodeCount(
            reason_code="no_liquidity_depth_decay_snapshots",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert depth_report.rows == ()
    assert depth_report.paper_only is True
    assert depth_report.report_only is True
    assert depth_report.readonly is True


def test_scores_pass_watch_and_block_depth_decay_snapshots() -> None:
    depth_report = report(
        snapshot(
            "depth-case-watch",
            observed_at=GENERATED_AT - timedelta(seconds=420),
            last_depth_change_at=GENERATED_AT - timedelta(seconds=300),
            best_bid_price=d("0.470000"),
            best_ask_price=d("0.500000"),
            near_band_depth=d("600.000000"),
            far_band_depth=d("390.000000"),
        ),
        snapshot(
            "depth-case-block",
            observed_at=GENERATED_AT - timedelta(seconds=1200),
            last_depth_change_at=GENERATED_AT - timedelta(seconds=900),
            best_bid_price=d("0.420000"),
            best_ask_price=d("0.500000"),
            near_band_depth=d("100.000000"),
            far_band_depth=d("20.000000"),
            reason_codes=("manual_depth_review",),
        ),
        snapshot("depth-case-pass"),
    )

    assert depth_report.input_count == d("3.000000")
    assert depth_report.pass_count == d("1.000000")
    assert depth_report.watch_count == d("1.000000")
    assert depth_report.block_count == d("1.000000")
    assert depth_report.average_liquidity_depth_decay_score == d("0.427222")
    assert depth_report.max_book_age_seconds == d("1200.000000")
    assert depth_report.max_spread_pressure == d("0.080000")
    assert depth_report.max_depth_decay_ratio == d("0.800000")
    assert depth_report.max_unchanged_book_seconds == d("900.000000")
    assert depth_report.status == "block"

    block_row, pass_row, watch_row = depth_report.rows
    assert tuple(row.liquidity_group_ref for row in depth_report.rows) == (
        "liquidity_depth_group_001",
        "liquidity_depth_group_002",
        "liquidity_depth_group_003",
    )
    assert tuple(row.status for row in depth_report.rows) == ("block", "pass", "watch")
    assert block_row.book_age_seconds == d("1200.000000")
    assert block_row.spread_pressure == d("0.080000")
    assert block_row.depth_decay_ratio == d("0.800000")
    assert block_row.liquidity_depth_decay_score == ZERO
    assert block_row.reason_codes == (
        "depth_decay_block",
        "depth_freshness_block",
        "input_manual_depth_review",
        "liquidity_depth_decay_block",
        "spread_pressure_block",
        "stale_book_risk_block",
    )
    assert pass_row.depth_freshness_score == d("0.866667")
    assert pass_row.spread_pressure_score == d("0.800000")
    assert pass_row.depth_decay_score == d("0.750000")
    assert pass_row.stale_book_risk_score == d("0.900000")
    assert pass_row.liquidity_depth_decay_score == d("0.822500")
    assert pass_row.reason_codes == (
        "depth_decay_pass",
        "depth_freshness_pass",
        "liquidity_depth_decay_pass",
        "spread_pressure_pass",
        "stale_book_risk_pass",
    )
    assert watch_row.depth_decay_ratio == d("0.350000")
    assert watch_row.liquidity_depth_decay_score == d("0.459167")
    assert watch_row.reason_codes == (
        "depth_decay_watch",
        "depth_freshness_watch",
        "liquidity_depth_decay_watch",
        "spread_pressure_watch",
        "stale_book_risk_watch",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        snapshot("depth-case-z", reason_codes=("zeta", "alpha")),
        snapshot("depth-case-a"),
    )
    second = report(
        snapshot("depth-case-a"),
        snapshot("depth-case-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_liquidity_depth_decay_report_payload(first)
    second_payload = module.research_market_liquidity_depth_decay_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert module.research_market_liquidity_depth_decay_report_digest(first) == (
        module.research_market_liquidity_depth_decay_report_digest(second)
    )
    assert len(module.research_market_liquidity_depth_decay_report_digest(first)) == 64
    int(module.research_market_liquidity_depth_decay_report_digest(first), 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["liquidity_group_ref"] == "liquidity_depth_group_001"
    assert first_payload["rows"][0]["liquidity_depth_decay_score"] == "0.822500"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "depth-case-a" not in encoded
    assert "depth-case-z" not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(snapshot())

    for value in (config(), snapshot(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].liquidity_depth_decay_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="best_bid_price"):
        snapshot(best_bid_price=0.49)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="near_band_depth"):
        snapshot(near_band_depth=DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(snapshot(), generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report(snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="best_ask_price"):
        snapshot(best_bid_price=d("0.500000"), best_ask_price=d("0.490000"))
    with pytest.raises(ValueError, match="far_band_depth"):
        snapshot(near_band_depth=d("100.000000"), far_band_depth=d("101.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        snapshot(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        snapshot(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchMarketLiquidityDepthDecayConfig,), {})


def test_owned_module_has_no_db_network_wallet_execution_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_depth_decay_report.py"
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
        "wallet",
        "private_key",
        "auth",
        "place_order",
        "cancel_order",
        "order_size",
        "live_trading",
        "trade_recommendation",
        "sizing",
        "buy_",
        "sell_",
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
