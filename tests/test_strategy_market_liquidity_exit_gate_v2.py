from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 55, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_NAME = "polymarket_alpha_lab.strategy_market_liquidity_exit_gate_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_market_liquidity_exit_gate_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_STRATEGY_MARKET_LIQUIDITY_EXIT_GATE_V2_CONFIG_VERSION,
        "min_clear_bid_depth_shares": d("1000.000000"),
        "min_watch_bid_depth_shares": d("500.000000"),
        "min_clear_ask_depth_shares": d("1000.000000"),
        "min_watch_ask_depth_shares": d("500.000000"),
        "min_clear_exit_depth_to_target_ratio": d("2.000000"),
        "min_watch_exit_depth_to_target_ratio": d("1.000000"),
        "max_clear_spread_probability": d("0.020000"),
        "max_watch_spread_probability": d("0.050000"),
        "max_clear_volume_decay_ratio": d("0.250000"),
        "max_watch_volume_decay_ratio": d("0.500000"),
        "max_clear_book_imbalance_ratio": d("0.400000"),
        "max_watch_book_imbalance_ratio": d("0.700000"),
        "max_clear_settlement_horizon_seconds": d("86400.000000"),
        "max_watch_settlement_horizon_seconds": d("604800.000000"),
    }
    values.update(overrides)
    return module.StrategyMarketLiquidityExitGateV2Config(**values)


def snapshot(**overrides: object) -> Any:
    module = api()
    values = {
        "market_slug": "liquidity-clear-market",
        "condition_id": "condition-clear",
        "observed_at": OBSERVED_AT,
        "target_exit_shares": d("400.000000"),
        "bid_probability": d("0.490000"),
        "ask_probability": d("0.510000"),
        "bid_depth_shares": d("1200.000000"),
        "ask_depth_shares": d("1100.000000"),
        "current_volume_shares_24h": d("9000.000000"),
        "previous_volume_shares_24h": d("10000.000000"),
        "settlement_horizon_seconds": d("3600.000000"),
        "source_config_version": "paper-depth-snapshot-v0",
    }
    values.update(overrides)
    return module.StrategyMarketLiquidityExitGateV2Snapshot(**values)


def report(*values: object, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_market_liquidity_exit_gate_v2_report(
        values,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_public_numeric(value: object) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, int, float)):
        raise AssertionError(f"unexpected public numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)


def unsafe_text(*parts: str) -> str:
    return "".join(parts)


def test_gate_scores_clear_watch_and_blocked_exit_feasibility() -> None:
    result = report(
        snapshot(
            market_slug="z-clear",
            condition_id="condition-clear",
            target_exit_shares=d("400.000000"),
            bid_depth_shares=d("1200.000000"),
            ask_depth_shares=d("1100.000000"),
            bid_probability=d("0.490000"),
            ask_probability=d("0.510000"),
            current_volume_shares_24h=d("9000.000000"),
            previous_volume_shares_24h=d("10000.000000"),
            settlement_horizon_seconds=d("3600.000000"),
        ),
        snapshot(
            market_slug="m-watch",
            condition_id="condition-watch",
            target_exit_shares=d("400.000000"),
            bid_depth_shares=d("700.000000"),
            ask_depth_shares=d("900.000000"),
            bid_probability=d("0.470000"),
            ask_probability=d("0.505000"),
            current_volume_shares_24h=d("6500.000000"),
            previous_volume_shares_24h=d("10000.000000"),
            settlement_horizon_seconds=d("172800.000000"),
        ),
        snapshot(
            market_slug="a-blocked",
            condition_id="condition-blocked",
            target_exit_shares=d("600.000000"),
            bid_depth_shares=d("300.000000"),
            ask_depth_shares=d("2400.000000"),
            bid_probability=d("0.430000"),
            ask_probability=d("0.510000"),
            current_volume_shares_24h=d("4000.000000"),
            previous_volume_shares_24h=d("10000.000000"),
            settlement_horizon_seconds=d("1209600.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-market-liquidity-exit-gate-v2"
    assert result.market_count == d("3.000000")
    assert result.clear_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.min_exit_depth_to_target_ratio == d("0.500000")
    assert result.max_spread_probability == d("0.080000")
    assert result.max_volume_decay_ratio == d("0.600000")
    assert result.max_book_imbalance_ratio == d("0.777778")
    assert result.max_settlement_horizon_seconds == d("1209600.000000")
    assert result.gate_status == "blocked"
    assert result.recommended_next_step == "block_report_only_liquidity_exit"
    assert result.reason_codes == (
        "liquidity_exit_ask_depth_below_clear",
        "liquidity_exit_bid_depth_below_clear",
        "liquidity_exit_bid_depth_below_minimum",
        "liquidity_exit_book_imbalance_above_max",
        "liquidity_exit_book_imbalance_above_clear",
        "liquidity_exit_depth_ratio_below_clear",
        "liquidity_exit_depth_ratio_below_minimum",
        "liquidity_exit_settlement_horizon_blocked",
        "liquidity_exit_settlement_horizon_pressure",
        "liquidity_exit_spread_above_max",
        "liquidity_exit_spread_above_clear",
        "liquidity_exit_volume_decay_above_max",
        "liquidity_exit_volume_decay_above_clear",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.market_slug for row in result.rows) == (
        "a-blocked",
        "m-watch",
        "z-clear",
    )
    blocked, watched, cleared = result.rows

    assert blocked.gate_status == "blocked"
    assert blocked.spread_probability == d("0.080000")
    assert blocked.exit_depth_shares == d("300.000000")
    assert blocked.exit_depth_to_target_ratio == d("0.500000")
    assert blocked.volume_decay_ratio == d("0.600000")
    assert blocked.book_imbalance_ratio == d("0.777778")
    assert blocked.feasibility_score == d("0.000000")
    assert blocked.reason_codes == (
        "liquidity_exit_bid_depth_below_minimum",
        "liquidity_exit_book_imbalance_above_max",
        "liquidity_exit_depth_ratio_below_minimum",
        "liquidity_exit_settlement_horizon_blocked",
        "liquidity_exit_spread_above_max",
        "liquidity_exit_volume_decay_above_max",
    )

    assert watched.gate_status == "watch"
    assert watched.spread_probability == d("0.035000")
    assert watched.exit_depth_to_target_ratio == d("1.750000")
    assert watched.volume_decay_ratio == d("0.350000")
    assert watched.book_imbalance_ratio == d("0.125000")
    assert watched.feasibility_score == d("0.285714")
    assert watched.reason_codes == (
        "liquidity_exit_ask_depth_below_clear",
        "liquidity_exit_bid_depth_below_clear",
        "liquidity_exit_depth_ratio_below_clear",
        "liquidity_exit_settlement_horizon_pressure",
        "liquidity_exit_spread_above_clear",
        "liquidity_exit_volume_decay_above_clear",
    )

    assert cleared.gate_status == "clear"
    assert cleared.exit_depth_to_target_ratio == d("2.750000")
    assert cleared.feasibility_score == d("0.846154")
    assert cleared.reason_codes == ("liquidity_exit_gate_clear",)
    assert len({row.derived_validation_digest for row in result.rows}) == 3


def test_empty_report_is_readonly_zeroed_and_digest_bound() -> None:
    module = api()
    empty = report()

    assert type(empty) is module.StrategyMarketLiquidityExitGateV2Report
    assert empty.market_count == ZERO
    assert empty.clear_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.blocked_count == ZERO
    assert empty.min_exit_depth_to_target_ratio == ZERO
    assert empty.max_spread_probability == ZERO
    assert empty.max_volume_decay_ratio == ZERO
    assert empty.max_book_imbalance_ratio == ZERO
    assert empty.max_settlement_horizon_seconds == ZERO
    assert empty.gate_status == "clear"
    assert empty.recommended_next_step == "continue_report_only_liquidity_exit"
    assert empty.reason_codes == ("liquidity_exit_gate_empty",)
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in empty.derived_validation_digest)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    for public_value in (config(), snapshot(), empty):
        assert is_dataclass(public_value)
        assert public_value.__dataclass_params__.frozen is True


def test_public_payload_uses_decimal_strings_and_rejects_tampering() -> None:
    module = api()
    result = report(
        snapshot(
            market_slug="payload-market",
            condition_id="condition-payload",
            bid_probability=d("0.430000"),
            ask_probability=d("0.510000"),
            bid_depth_shares=d("300.000000"),
            ask_depth_shares=d("2400.000000"),
            target_exit_shares=d("600.000000"),
            current_volume_shares_24h=d("4000.000000"),
            previous_volume_shares_24h=d("10000.000000"),
            settlement_horizon_seconds=d("1209600.000000"),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_market_liquidity_exit_gate_v2_public_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["max_spread_probability"] == "0.080000"
    assert payload["max_book_imbalance_ratio"] == "0.777778"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-06T11:55:00+00:00"
    assert payload["rows"][0]["bid_depth_shares"] == "300.000000"
    assert payload["rows"][0]["book_imbalance_ratio"] == "0.777778"
    assert payload["rows"][0]["paper_only"] is True
    assert module.validate_strategy_market_liquidity_exit_gate_v2_public_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    numeric_payload = {**payload, "market_count": 1}
    with pytest.raises(ValueError, match="Decimal strings|numeric"):
        module.validate_strategy_market_liquidity_exit_gate_v2_public_payload(
            numeric_payload,
        )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_market_liquidity_exit_gate_v2_public_payload(
            missing_digest,
        )

    tampered = {**payload, "blocked_count": "0.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_market_liquidity_exit_gate_v2_public_payload(tampered)

    tampered_report = replace(result)
    object.__setattr__(tampered_report, "blocked_count", d("99.000000"))
    with pytest.raises(ValueError, match="blocked_count|derived_validation_digest"):
        module.strategy_market_liquidity_exit_gate_v2_public_payload(tampered_report)


@pytest.mark.parametrize(
    ("key", "value"),
    (
        (unsafe_text("li", "ve", "_enabled"), "not allowed"),
        (unsafe_text("au", "th", "_token"), "not allowed"),
        (unsafe_text("wal", "let", "_address"), "not allowed"),
        (unsafe_text("ord", "er", "_id"), "not allowed"),
        (unsafe_text("net", "work", "_url"), "not allowed"),
        (unsafe_text("data", "base", "_dsn"), "not allowed"),
        (unsafe_text("per", "sist", "_path"), "not allowed"),
        (unsafe_text("sig", "ning", "_key"), "not allowed"),
        (unsafe_text("mu", "tation", "_path"), "not allowed"),
        (unsafe_text("bu", "y", "_flag"), "not allowed"),
        (unsafe_text("sel", "l", "_flag"), "not allowed"),
        (unsafe_text("tra", "de", "_id"), "not allowed"),
        ("operator_note", unsafe_text("configured ", "li", "ve", " surface")),
        ("operator_note", unsafe_text("configured ", "au", "th", " surface")),
        ("operator_note", unsafe_text("configured ", "wal", "let", " surface")),
        ("operator_note", unsafe_text("configured ", "ord", "er", " surface")),
        ("operator_note", unsafe_text("configured ", "net", "work", " surface")),
        ("operator_note", unsafe_text("configured ", "data", "base", " surface")),
        ("operator_note", unsafe_text("configured ", "per", "sist", " surface")),
        ("operator_note", unsafe_text("configured ", "sig", "ning", " surface")),
        ("operator_note", unsafe_text("configured ", "mu", "tation", " surface")),
        ("operator_note", unsafe_text("configured ", "bu", "y", " surface")),
        ("operator_note", unsafe_text("configured ", "sel", "l", " surface")),
        ("operator_note", unsafe_text("configured ", "tra", "de", " surface")),
    ),
)
def test_public_payload_rejects_unsafe_public_keys_and_values(
    key: str,
    value: str,
) -> None:
    module = api()
    payload = module.strategy_market_liquidity_exit_gate_v2_public_payload(
        report(snapshot(market_slug="unsafe-check", condition_id="condition-unsafe")),
    )

    unsafe_payload = {**payload, key: value}
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_strategy_market_liquidity_exit_gate_v2_public_payload(
            unsafe_payload,
        )


def test_validation_rejects_bad_types_flags_duplicates_time_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_market_liquidity_exit_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 6, 11, 55))
    with pytest.raises(ValueError, match="observed_at"):
        snapshot(observed_at=datetime(2026, 7, 6, 11, 55, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="after generated_at"):
        report(snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate market liquidity snapshot"):
        report(
            snapshot(market_slug="dup", condition_id="condition-dup"),
            snapshot(market_slug="dup", condition_id="condition-dup"),
        )
    with pytest.raises(ValueError, match="target_exit_shares"):
        snapshot(target_exit_shares=400)
    with pytest.raises(ValueError, match="bid_depth_shares"):
        snapshot(bid_depth_shares=_DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="bid_probability"):
        snapshot(bid_probability=d("0.510000"), ask_probability=d("0.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        snapshot(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)

    clear_report = report(snapshot(market_slug="consistency", condition_id="condition-consistency"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(clear_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="clear_count"):
        replace(clear_report, clear_count=d("2.000000"))

    with pytest.raises(FrozenInstanceError):
        clear_report.gate_status = "blocked"  # type: ignore[misc]


def test_export_contract_and_static_no_external_surfaces() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_STRATEGY_MARKET_LIQUIDITY_EXIT_GATE_V2_CONFIG_VERSION",
        "StrategyMarketLiquidityExitGateV2Config",
        "StrategyMarketLiquidityExitGateV2ReasonCodeCount",
        "StrategyMarketLiquidityExitGateV2Report",
        "StrategyMarketLiquidityExitGateV2Row",
        "StrategyMarketLiquidityExitGateV2Snapshot",
        "build_strategy_market_liquidity_exit_gate_v2_report",
        "strategy_market_liquidity_exit_gate_v2_public_payload",
        "validate_strategy_market_liquidity_exit_gate_v2_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for instance in (
        config(),
        snapshot(),
        *report(snapshot()).rows,
        report(snapshot()),
    ):
        for field in fields(instance):
            value = getattr(instance, field.name)
            assert type(value) is not float
            if field.name.endswith(
                (
                    "_count",
                    "_probability",
                    "_ratio",
                    "_shares",
                    "_seconds",
                    "_score",
                ),
            ):
                assert value is None or type(value) is Decimal

    source = MODULE_PATH.read_text()
    lowered_source = source.lower()
    forbidden_source_fragments = (
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "py_clob_client",
        "private_key",
        "api_key",
        "auth_token",
        "wallet",
        "network_client",
        "database_url",
        "persist_path",
        "place_order",
        "create_order",
        "cancel_order",
        "submit_order",
        "live_trading",
        "trade_executor",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in lowered_source

    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "read",
        "write",
    }
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_source_fragments
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_source_fragments
        elif isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in forbidden_call_names
