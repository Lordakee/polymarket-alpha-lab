from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 7, 16, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def gate():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_portfolio_liquidity_stress_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def position(
    market_slug: str = "calm-event-yes",
    *,
    condition_id: str | None = None,
    observed_at: datetime = datetime(2026, 7, 7, 15, 30, tzinfo=UTC),
    open_exposure_notional: str | Decimal = "5000.000000",
    target_exit_shares: str | Decimal = "10000.000000",
    bid_probability: str | Decimal = "0.480000",
    ask_probability: str | Decimal = "0.490000",
    bid_depth_shares: str | Decimal = "100000.000000",
    ask_depth_shares: str | Decimal = "100000.000000",
    market_close_seconds: str | Decimal = "172800.000000",
    source_config_version: str | None = None,
):
    module = gate()
    return module.StrategyPortfolioLiquidityStressGateV2Position(
        market_slug=market_slug,
        condition_id=condition_id or f"{market_slug}-condition",
        observed_at=observed_at,
        open_exposure_notional=(
            open_exposure_notional
            if isinstance(open_exposure_notional, Decimal)
            else d(open_exposure_notional)
        ),
        target_exit_shares=(
            target_exit_shares
            if isinstance(target_exit_shares, Decimal)
            else d(target_exit_shares)
        ),
        bid_probability=(
            bid_probability
            if isinstance(bid_probability, Decimal)
            else d(bid_probability)
        ),
        ask_probability=(
            ask_probability
            if isinstance(ask_probability, Decimal)
            else d(ask_probability)
        ),
        bid_depth_shares=(
            bid_depth_shares
            if isinstance(bid_depth_shares, Decimal)
            else d(bid_depth_shares)
        ),
        ask_depth_shares=(
            ask_depth_shares
            if isinstance(ask_depth_shares, Decimal)
            else d(ask_depth_shares)
        ),
        market_close_seconds=(
            market_close_seconds
            if isinstance(market_close_seconds, Decimal)
            else d(market_close_seconds)
        ),
        source_config_version=(
            source_config_version
            or module.DEFAULT_STRATEGY_PORTFOLIO_LIQUIDITY_STRESS_GATE_V2_CONFIG_VERSION
        ),
    )


def stressed_config():
    module = gate()
    return module.StrategyPortfolioLiquidityStressGateV2Config(
        max_clear_portfolio_open_exposure_notional=d("50000.000000"),
        max_watch_portfolio_open_exposure_notional=d("70000.000000"),
    )


def report(*positions: object, cfg: object | None = None):
    module = gate()
    return module.build_strategy_portfolio_liquidity_stress_gate_v2_report(
        positions,
        config=cfg or module.StrategyPortfolioLiquidityStressGateV2Config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def large_stressed_position():
    return position(
        "large-event-yes",
        open_exposure_notional="60000.000000",
        target_exit_shares="10000.000000",
        bid_probability="0.400000",
        ask_probability="0.500000",
        bid_depth_shares="100.000000",
        ask_depth_shares="120.000000",
        market_close_seconds="3600.000000",
    )


def soon_watch_position():
    return position(
        "soon-event-yes",
        open_exposure_notional="15000.000000",
        bid_probability="0.490000",
        ask_probability="0.530000",
        bid_depth_shares="60000.000000",
        ask_depth_shares="60000.000000",
        market_close_seconds="7200.000000",
    )


def calm_position():
    return position("calm-event-yes")


def test_empty_input_returns_report_only_clear_zero_digest() -> None:
    module = gate()

    stress_report = report()

    assert isinstance(stress_report, module.StrategyPortfolioLiquidityStressGateV2Report)
    assert is_dataclass(stress_report)
    assert stress_report.__dataclass_params__.frozen
    assert stress_report.generated_at == GENERATED_AT
    assert stress_report.generated_at.tzinfo is UTC
    assert stress_report.config_version == (
        "strategy-portfolio-liquidity-stress-gate-v2"
    )
    assert stress_report.gate_status == "clear"
    assert stress_report.recommended_next_step == (
        "continue_report_only_portfolio_liquidity_stress_gate"
    )
    assert stress_report.market_count == d("0.000000")
    assert stress_report.clear_count == d("0.000000")
    assert stress_report.watch_count == d("0.000000")
    assert stress_report.blocked_count == d("0.000000")
    assert stress_report.total_open_exposure_notional == d("0.000000")
    assert stress_report.max_market_open_exposure_notional == d("0.000000")
    assert stress_report.shallow_book_open_exposure_notional == d("0.000000")
    assert stress_report.shallow_book_share_ratio == d("0.000000")
    assert stress_report.max_spread_probability == d("0.000000")
    assert stress_report.max_exit_urgency_ratio == d("0.000000")
    assert stress_report.close_cluster_open_exposure_notional == d("0.000000")
    assert stress_report.close_cluster_share_ratio == d("0.000000")
    assert stress_report.size_cap_breach_count == d("0.000000")
    assert stress_report.rows == ()
    assert stress_report.reason_codes == ("portfolio_liquidity_stress_gate_empty",)
    assert stress_report.reason_code_counts == ()
    assert len(stress_report.derived_validation_digest) == 64
    assert stress_report.paper_only is True
    assert stress_report.report_only is True
    assert stress_report.readonly is True


def test_blocked_aggregate_stress_captures_all_phase_1_signals() -> None:
    stress_report = report(
        calm_position(),
        large_stressed_position(),
        soon_watch_position(),
        cfg=stressed_config(),
    )

    assert stress_report.gate_status == "blocked"
    assert stress_report.recommended_next_step == (
        "block_report_only_portfolio_liquidity_stress_gate"
    )
    assert stress_report.market_count == d("3.000000")
    assert stress_report.blocked_count == d("1.000000")
    assert stress_report.watch_count == d("1.000000")
    assert stress_report.clear_count == d("1.000000")
    assert stress_report.total_open_exposure_notional == d("80000.000000")
    assert stress_report.max_market_open_exposure_notional == d("60000.000000")
    assert stress_report.shallow_book_open_exposure_notional == d("60000.000000")
    assert stress_report.shallow_book_share_ratio == d("0.750000")
    assert stress_report.max_spread_probability == d("0.100000")
    assert stress_report.max_exit_urgency_ratio == d("1.000000")
    assert stress_report.close_cluster_open_exposure_notional == d("75000.000000")
    assert stress_report.close_cluster_share_ratio == d("0.937500")
    assert stress_report.size_cap_breach_count == d("1.000000")
    assert stress_report.reason_codes == (
        "portfolio_liquidity_stress_open_exposure_above_max",
        "portfolio_liquidity_stress_shallow_book_share_above_max",
        "portfolio_liquidity_stress_spread_above_max",
        "portfolio_liquidity_stress_exit_urgency_above_max",
        "portfolio_liquidity_stress_close_cluster_share_above_max",
        "portfolio_liquidity_stress_size_cap_above_max",
    )
    assert tuple(row.market_slug for row in stress_report.rows) == (
        "large-event-yes",
        "soon-event-yes",
        "calm-event-yes",
    )

    blocked, watched, passed = stress_report.rows
    assert blocked.gate_status == "blocked"
    assert blocked.spread_probability == d("0.100000")
    assert blocked.exit_depth_shares == d("100.000000")
    assert blocked.exit_depth_notional == d("40.000000")
    assert blocked.exit_depth_to_exposure_ratio == d("0.000667")
    assert blocked.exit_urgency_ratio == d("1.000000")
    assert blocked.reason_codes == (
        "portfolio_liquidity_stress_market_exposure_above_max",
        "portfolio_liquidity_stress_shallow_book",
        "portfolio_liquidity_stress_spread_above_max",
        "portfolio_liquidity_stress_exit_urgency_above_max",
    )
    assert watched.gate_status == "watch"
    assert watched.reason_codes == (
        "portfolio_liquidity_stress_spread_above_clear",
        "portfolio_liquidity_stress_exit_urgency_above_clear",
    )
    assert passed.gate_status == "clear"
    assert passed.reason_codes == ("portfolio_liquidity_stress_clear",)
    assert tuple(item.reason_code for item in stress_report.reason_code_counts) == (
        "portfolio_liquidity_stress_market_exposure_above_max",
        "portfolio_liquidity_stress_shallow_book",
        "portfolio_liquidity_stress_spread_above_max",
        "portfolio_liquidity_stress_spread_above_clear",
        "portfolio_liquidity_stress_exit_urgency_above_max",
        "portfolio_liquidity_stress_exit_urgency_above_clear",
    )
    assert stress_report.reason_code_counts[0].count == d("1.000000")
    assert stress_report.reason_code_counts[0].market_ratio == d("0.333333")


def test_rows_payloads_and_digests_are_deterministic() -> None:
    module = gate()
    cfg = stressed_config()
    first = soon_watch_position()
    second = large_stressed_position()
    third = calm_position()

    forward = report(first, second, third, cfg=cfg)
    reverse = report(third, second, first, cfg=cfg)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "large-event-yes",
        "soon-event-yes",
        "calm-event-yes",
    )
    assert all(len(row.derived_validation_digest) == 64 for row in forward.rows)
    assert forward.derived_validation_digest == reverse.derived_validation_digest

    payload = module.strategy_portfolio_liquidity_stress_gate_v2_public_payload(
        forward,
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["total_open_exposure_notional"] == "80000.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-07T15:30:00+00:00"
    assert payload["rows"][0]["exit_depth_notional"] == "40.000000"
    assert (
        payload["derived_validation_digest"]
        == forward.derived_validation_digest
    )
    assert module.validate_strategy_portfolio_liquidity_stress_gate_v2_public_payload(
        payload,
    )

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "order" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        elif type(value) is bool:
            return
        else:
            assert not isinstance(value, (Decimal, datetime, float, int))

    walk_payload(payload)


def test_validation_rejects_bad_inputs_and_inconsistent_records() -> None:
    module = gate()

    with pytest.raises(ValueError, match="open_exposure_notional must be a Decimal"):
        position(open_exposure_notional=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_strategy_portfolio_liquidity_stress_gate_v2_report(
            (),
            config=module.StrategyPortfolioLiquidityStressGateV2Config(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="bid_probability must not exceed ask_probability"):
        position(bid_probability="0.700000", ask_probability="0.600000")
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.build_strategy_portfolio_liquidity_stress_gate_v2_report(
            (position(observed_at=datetime(2026, 7, 7, 16, 1, tzinfo=UTC)),),
            config=module.StrategyPortfolioLiquidityStressGateV2Config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="positions contain duplicate portfolio liquidity position",
    ):
        report(
            position("duplicate-market", condition_id="duplicate-condition"),
            position("duplicate-market", condition_id="duplicate-condition"),
        )
    with pytest.raises(
        ValueError,
        match="max_clear_portfolio_open_exposure_notional",
    ):
        module.StrategyPortfolioLiquidityStressGateV2Config(
            max_clear_portfolio_open_exposure_notional=d("2.000000"),
            max_watch_portfolio_open_exposure_notional=d("1.000000"),
        )

    valid_row = report(calm_position()).rows[0]
    with pytest.raises(ValueError, match="spread_probability must match quotes"):
        replace(valid_row, spread_probability=d("0.999999"))
    with pytest.raises(ValueError, match="gate_status must match reason_codes"):
        replace(
            valid_row,
            reason_codes=("portfolio_liquidity_stress_spread_above_clear",),
        )

    frozen_position = position("frozen-position")
    with pytest.raises(FrozenInstanceError):
        frozen_position.market_slug = "changed"  # type: ignore[misc]


def test_hard_flags_decimal_only_and_no_durable_or_active_surfaces() -> None:
    module = gate()
    stress_report = report(calm_position())

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.StrategyPortfolioLiquidityStressGateV2Config(paper_only=False)
    with pytest.raises(ValueError, match="position report_only must be True"):
        replace(calm_position(), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(stress_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(stress_report, paper_only=False)

    for public_record in (
        module.StrategyPortfolioLiquidityStressGateV2Config(),
        calm_position(),
        stress_report.rows[0],
        stress_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/strategy_portfolio_liquidity_stress_gate_v2.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "auth",
        "order",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source.lower()
