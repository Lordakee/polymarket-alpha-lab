from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_liquidity_slippage_watchlist_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_SLIPPAGE_WATCHLIST_REPORT_CONFIG_VERSION
        ),
        "min_pass_available_liquidity": d("500.000000"),
        "min_watch_available_liquidity": d("100.000000"),
        "max_pass_spread_width": d("0.020000"),
        "max_watch_spread_width": d("0.060000"),
        "max_pass_depth_concentration": d("0.350000"),
        "max_watch_depth_concentration": d("0.700000"),
        "max_pass_book_age_seconds": d("120.000000"),
        "max_watch_book_age_seconds": d("600.000000"),
        "max_pass_unchanged_book_seconds": d("180.000000"),
        "max_watch_unchanged_book_seconds": d("900.000000"),
        "liquidity_weight": d("0.250000"),
        "spread_weight": d("0.250000"),
        "depth_concentration_weight": d("0.200000"),
        "book_freshness_weight": d("0.150000"),
        "stale_book_weight": d("0.150000"),
        "pass_execution_quality_score": d("0.700000"),
        "watch_execution_quality_score": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchStrategyLiquiditySlippageWatchlistConfig(**values)


def watch_input(
    input_key: str = "entry-pass",
    *,
    apparent_edge: Decimal = d("0.050000"),
    best_bid_price: Decimal = d("0.490000"),
    best_ask_price: Decimal = d("0.500000"),
    available_liquidity: Decimal = d("1000.000000"),
    largest_level_liquidity: Decimal = d("100.000000"),
    book_observed_at: datetime | None = None,
    last_book_change_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyLiquiditySlippageWatchlistInput(
        input_key=input_key,
        apparent_edge=apparent_edge,
        best_bid_price=best_bid_price,
        best_ask_price=best_ask_price,
        available_liquidity=available_liquidity,
        largest_level_liquidity=largest_level_liquidity,
        book_observed_at=(
            book_observed_at
            if book_observed_at is not None
            else GENERATED_AT - timedelta(seconds=60)
        ),
        last_book_change_at=(
            last_book_change_at
            if last_book_change_at is not None
            else GENERATED_AT - timedelta(seconds=30)
        ),
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_liquidity_slippage_watchlist_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_watchlist_review() -> None:
    module = api()
    watchlist = report()

    assert module.LIQUIDITY_SLIPPAGE_WATCHLIST_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "LIQUIDITY_SLIPPAGE_WATCHLIST_STATUSES",
        "DEFAULT_RESEARCH_STRATEGY_LIQUIDITY_SLIPPAGE_WATCHLIST_REPORT_CONFIG_VERSION",
        "ResearchStrategyLiquiditySlippageWatchlistConfig",
        "ResearchStrategyLiquiditySlippageWatchlistInput",
        "ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount",
        "ResearchStrategyLiquiditySlippageWatchlistReport",
        "ResearchStrategyLiquiditySlippageWatchlistRow",
        "build_research_strategy_liquidity_slippage_watchlist_report",
        "research_strategy_liquidity_slippage_watchlist_report_digest",
        "research_strategy_liquidity_slippage_watchlist_report_payload",
    )
    assert type(watchlist) is module.ResearchStrategyLiquiditySlippageWatchlistReport
    assert is_dataclass(watchlist)
    assert watchlist.generated_at == GENERATED_AT
    assert watchlist.config_version == (
        "research-strategy-liquidity-slippage-watchlist-report-v0"
    )
    assert watchlist.input_count == ZERO
    assert watchlist.pass_count == ZERO
    assert watchlist.watch_count == ZERO
    assert watchlist.block_count == ZERO
    assert watchlist.average_execution_quality_score is None
    assert watchlist.max_edge_fragility_score == ZERO
    assert watchlist.min_available_liquidity == ZERO
    assert watchlist.max_spread_width == ZERO
    assert watchlist.max_depth_concentration_ratio == ZERO
    assert watchlist.max_book_age_seconds == ZERO
    assert watchlist.max_unchanged_book_seconds == ZERO
    assert watchlist.status == "block"
    assert watchlist.reason_codes == ("no_liquidity_slippage_watchlist_inputs",)
    assert watchlist.reason_code_counts == (
        module.ResearchStrategyLiquiditySlippageWatchlistReasonCodeCount(
            reason_code="no_liquidity_slippage_watchlist_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert watchlist.rows == ()
    assert len(watchlist.derived_validation_digest) == 64
    assert watchlist.paper_only is True
    assert watchlist.report_only is True
    assert watchlist.readonly is True


def test_scores_pass_watch_and_block_liquidity_slippage_inputs() -> None:
    watchlist = report(
        watch_input(
            "entry-watch",
            apparent_edge=d("0.080000"),
            best_bid_price=d("0.460000"),
            best_ask_price=d("0.500000"),
            available_liquidity=d("300.000000"),
            largest_level_liquidity=d("150.000000"),
            book_observed_at=GENERATED_AT - timedelta(seconds=300),
            last_book_change_at=GENERATED_AT - timedelta(seconds=400),
        ),
        watch_input(
            "entry-block",
            apparent_edge=d("0.100000"),
            best_bid_price=d("0.400000"),
            best_ask_price=d("0.490000"),
            available_liquidity=d("50.000000"),
            largest_level_liquidity=d("45.000000"),
            book_observed_at=GENERATED_AT - timedelta(seconds=900),
            last_book_change_at=GENERATED_AT - timedelta(seconds=1000),
            reason_codes=("manual_liquidity_review",),
        ),
        watch_input("entry-pass"),
    )

    assert watchlist.input_count == d("3.000000")
    assert watchlist.pass_count == d("1.000000")
    assert watchlist.watch_count == d("1.000000")
    assert watchlist.block_count == d("1.000000")
    assert watchlist.average_execution_quality_score == d("0.461190")
    assert watchlist.max_edge_fragility_score == d("0.097500")
    assert watchlist.min_available_liquidity == d("50.000000")
    assert watchlist.max_spread_width == d("0.090000")
    assert watchlist.max_depth_concentration_ratio == d("0.900000")
    assert watchlist.max_book_age_seconds == d("900.000000")
    assert watchlist.max_unchanged_book_seconds == d("1000.000000")
    assert watchlist.status == "block"
    assert watchlist.reason_codes == (
        "liquidity_slippage_watchlist_block",
        "liquidity_floor_block",
        "spread_width_block",
        "depth_concentration_block",
        "book_freshness_block",
        "stale_book_observation_block",
        "liquidity_floor_watch",
        "spread_width_watch",
        "depth_concentration_watch",
        "book_freshness_watch",
        "stale_book_observation_watch",
    )

    block_row, pass_row, watch_row = watchlist.rows
    assert tuple(row.watchlist_ref for row in watchlist.rows) == (
        "liquidity_slippage_watchlist_001",
        "liquidity_slippage_watchlist_002",
        "liquidity_slippage_watchlist_003",
    )
    assert tuple(row.status for row in watchlist.rows) == ("block", "pass", "watch")
    assert block_row.apparent_edge == d("0.100000")
    assert block_row.spread_width == d("0.090000")
    assert block_row.depth_concentration_ratio == d("0.900000")
    assert block_row.execution_quality_score == d("0.025000")
    assert block_row.edge_fragility_score == d("0.097500")
    assert block_row.reason_codes == (
        "book_freshness_block",
        "depth_concentration_block",
        "input_manual_liquidity_review",
        "liquidity_floor_block",
        "liquidity_slippage_watchlist_block",
        "spread_width_block",
        "stale_book_observation_block",
    )
    assert pass_row.execution_quality_score == d("0.909762")
    assert pass_row.edge_fragility_score == d("0.004512")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "book_freshness_pass",
        "depth_concentration_pass",
        "liquidity_floor_pass",
        "liquidity_slippage_watchlist_pass",
        "spread_width_pass",
        "stale_book_observation_pass",
    )
    assert watch_row.execution_quality_score == d("0.448809")
    assert watch_row.edge_fragility_score == d("0.044095")
    assert watch_row.status == "watch"
    assert "liquidity_floor_watch" in watch_row.reason_codes
    assert "spread_width_watch" in watch_row.reason_codes
    assert "depth_concentration_watch" in watch_row.reason_codes
    assert "book_freshness_watch" in watch_row.reason_codes
    assert "stale_book_observation_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        watch_input("entry-z", reason_codes=("zeta", "alpha")),
        watch_input("entry-a"),
    )
    second = report(
        watch_input("entry-a"),
        watch_input("entry-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_strategy_liquidity_slippage_watchlist_report_payload(
        first,
    )
    second_payload = module.research_strategy_liquidity_slippage_watchlist_report_payload(
        second,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert module.research_strategy_liquidity_slippage_watchlist_report_digest(first) == (
        module.research_strategy_liquidity_slippage_watchlist_report_digest(second)
    )
    assert len(module.research_strategy_liquidity_slippage_watchlist_report_digest(first)) == 64
    int(module.research_strategy_liquidity_slippage_watchlist_report_digest(first), 16)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["rows"][0]["watchlist_ref"] == (
        "liquidity_slippage_watchlist_001"
    )
    assert first_payload["rows"][0]["execution_quality_score"] == "0.909762"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert "entry-a" not in encoded
    assert "entry-z" not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )
    assert not any(
        _has_forbidden_public_surface_value(value)
        for value in _walk_payload_values(first_payload)
        if isinstance(value, str)
    )


def test_validation_rejects_bad_types_flags_future_times_and_digest_tampering() -> None:
    module = api()
    populated = report(watch_input())

    for value in (config(), watch_input(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].execution_quality_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="apparent_edge"):
        watch_input(apparent_edge=0.05)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="available_liquidity"):
        watch_input(available_liquidity=DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="book_observed_at"):
        watch_input(book_observed_at=datetime(2026, 7, 8, 15, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(watch_input(), generated_at=DatetimeSubclass(2026, 7, 8, 15, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="book_observed_at"):
        report(watch_input(book_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="last_book_change_at"):
        report(watch_input(last_book_change_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="best_ask_price"):
        watch_input(best_bid_price=d("0.500000"), best_ask_price=d("0.490000"))
    with pytest.raises(ValueError, match="largest_level_liquidity"):
        watch_input(
            available_liquidity=d("100.000000"),
            largest_level_liquidity=d("101.000000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        watch_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        watch_input(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchStrategyLiquiditySlippageWatchlistConfig,), {})


def test_owned_module_has_no_db_network_wallet_execution_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_liquidity_slippage_watchlist_report.py"
    )
    if not module_path.exists():
        pytest.skip("module not implemented yet")
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "postgres",
        "wall" + "et",
        "private" + "_" + "key",
        "auth",
        "place" + "_" + "order",
        "cancel" + "_" + "order",
        "order" + "_" + "amount",
        "live" + "_" + "trading",
        "trade" + "_" + "recommendation",
        "position" + "_" + "amount",
        "buy" + "_",
        "sell" + "_",
        "connect(",
        "open(",
    )

    assert all(term not in text for term in forbidden_terms)


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
        "raw",
        "candidate" + "_" + "id",
        "condition" + "_" + "id",
        "market" + "_" + "id",
        "market" + "_" + "slug",
        "slug",
        "ques" + "tion",
        "url",
        "source" + "_" + "text",
        "dsn",
        "table",
        "token",
        "wall" + "et",
        "order",
        "trade",
        "buy",
        "sell",
        "position" + "_" + "amount",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)


def _has_forbidden_public_surface_value(value: str) -> bool:
    normalized = value.lower()
    forbidden_fragments = (
        "entry-a",
        "entry-z",
        "candidate" + "_" + "id",
        "market" + "_" + "id",
        "market" + "_" + "slug",
        "ques" + "tion",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
        "wall" + "et",
        "order",
        "trade",
        "buy",
        "sell",
        "position" + "_" + "amount",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)
