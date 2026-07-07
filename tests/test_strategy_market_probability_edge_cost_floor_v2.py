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
ZERO = Decimal("0.000000")
MODULE_NAME = "polymarket_alpha_lab.strategy_market_probability_edge_cost_floor_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_market_probability_edge_cost_floor_v2.py"
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
        "config_version": (
            module.DEFAULT_STRATEGY_MARKET_PROBABILITY_EDGE_COST_FLOOR_V2_CONFIG_VERSION
        ),
        "min_required_net_edge": d("0.030000"),
        "watch_net_edge_floor": d("0.000000"),
    }
    values.update(overrides)
    return module.StrategyMarketProbabilityEdgeCostFloorV2Config(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values = {
        "market_id": "market-alpha",
        "event_slug": "event-alpha",
        "category": "macro",
        "model_probability": d("0.720000"),
        "market_probability": d("0.620000"),
        "taker_fee_rate": d("0.010000"),
        "settlement_slippage_rate": d("0.020000"),
        "reason_codes": ("model_research_complete",),
    }
    values.update(overrides)
    return module.StrategyMarketProbabilityEdgeCostFloorV2Candidate(**values)


def report(
    *values: object,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_strategy_market_probability_edge_cost_floor_v2_report(
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


def assert_decimal_only_public_dataclass(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name.endswith(("_count", "_probability", "_edge", "_rate", "_floor")):
            assert type(item) is Decimal
        elif field.name == "candidate_ratio":
            assert type(item) is Decimal
        elif hasattr(item, "__dataclass_fields__"):
            assert_decimal_only_public_dataclass(item)
        elif isinstance(item, tuple):
            for nested in item:
                if hasattr(nested, "__dataclass_fields__"):
                    assert_decimal_only_public_dataclass(nested)


def unsafe_text(*parts: str) -> str:
    return "".join(parts)


def test_report_scores_pass_watch_and_block_after_cost_floor() -> None:
    result = report(
        candidate(
            market_id="z-pass",
            event_slug="z-election-pass",
            category="politics",
            model_probability=d("0.720000"),
            market_probability=d("0.620000"),
            taker_fee_rate=d("0.010000"),
            settlement_slippage_rate=d("0.020000"),
            reason_codes=("calibrated_model_edge",),
        ),
        candidate(
            market_id="m-watch",
            event_slug="m-weather-watch",
            category="weather",
            model_probability=d("0.600000"),
            market_probability=d("0.550000"),
            taker_fee_rate=d("0.020000"),
            settlement_slippage_rate=d("0.020000"),
            reason_codes=("thin_edge_review",),
        ),
        candidate(
            market_id="a-block",
            event_slug="a-crypto-block",
            category="crypto",
            model_probability=d("0.500000"),
            market_probability=d("0.530000"),
            taker_fee_rate=d("0.005000"),
            settlement_slippage_rate=d("0.005000"),
            reason_codes=("model_market_inversion",),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-market-probability-edge-cost-floor-v2"
    assert result.candidate_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.max_net_edge == d("0.070000")
    assert result.min_required_net_edge == d("0.030000")
    assert result.report_status == "block"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    assert tuple(row.market_id for row in result.rows) == ("z-pass", "m-watch", "a-block")
    passed, watched, blocked = result.rows

    assert passed.status == "pass"
    assert passed.market_id == "z-pass"
    assert passed.event_slug == "z-election-pass"
    assert passed.category == "politics"
    assert passed.model_probability == d("0.720000")
    assert passed.market_probability == d("0.620000")
    assert passed.gross_edge == d("0.100000")
    assert passed.taker_fee_rate == d("0.010000")
    assert passed.settlement_slippage_rate == d("0.020000")
    assert passed.total_cost_floor == d("0.030000")
    assert passed.net_edge == d("0.070000")
    assert passed.reason_codes == (
        "edge_after_cost_floor_meets_minimum",
        "calibrated_model_edge",
    )

    assert watched.status == "watch"
    assert watched.gross_edge == d("0.050000")
    assert watched.total_cost_floor == d("0.040000")
    assert watched.net_edge == d("0.010000")
    assert watched.reason_codes == (
        "edge_after_cost_floor_below_minimum",
        "thin_edge_review",
    )

    assert blocked.status == "block"
    assert blocked.gross_edge == d("-0.030000")
    assert blocked.total_cost_floor == d("0.010000")
    assert blocked.net_edge == d("-0.040000")
    assert blocked.reason_codes == (
        "edge_after_cost_floor_negative",
        "gross_edge_non_positive",
        "model_market_inversion",
    )

    assert tuple(item.reason_code for item in result.reason_code_counts) == tuple(
        sorted(item.reason_code for item in result.reason_code_counts),
    )
    count_by_code = {item.reason_code: item for item in result.reason_code_counts}
    assert count_by_code["edge_after_cost_floor_meets_minimum"].count == d("1.000000")
    assert count_by_code["edge_after_cost_floor_negative"].candidate_ratio == d("0.333333")
    assert count_by_code["gross_edge_non_positive"].count == d("1.000000")


def test_empty_report_is_readonly_empty_status_and_zero_decimals() -> None:
    module = api()
    empty = report()

    assert type(empty) is module.StrategyMarketProbabilityEdgeCostFloorV2Report
    assert empty.candidate_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.max_net_edge == ZERO
    assert empty.min_required_net_edge == ZERO
    assert empty.report_status == "empty"
    assert empty.reason_codes == ()
    assert empty.reason_code_counts == ()
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in empty.derived_validation_digest)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    for public_value in (config(), candidate(), empty):
        assert is_dataclass(public_value)
        assert public_value.__dataclass_params__.frozen is True
        assert_decimal_only_public_dataclass(public_value)


def test_public_payload_uses_decimal_strings_and_rejects_tampering() -> None:
    module = api()
    result = report(
        candidate(
            market_id="payload-market",
            event_slug="payload-event",
            model_probability=d("0.720000"),
            market_probability=d("0.620000"),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_market_probability_edge_cost_floor_v2_public_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["pass_count"] == "1.000000"
    assert payload["max_net_edge"] == "0.070000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["market_id"] == "payload-market"
    assert payload["rows"][0]["net_edge"] == "0.070000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        result.rows[0].derived_validation_digest
    )
    assert payload["rows"][0]["paper_only"] is True
    assert module.validate_strategy_market_probability_edge_cost_floor_v2_public_payload(
        payload,
    )
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    numeric_payload = {**payload, "candidate_count": 1}
    with pytest.raises(ValueError, match="Decimal strings|numeric"):
        module.validate_strategy_market_probability_edge_cost_floor_v2_public_payload(
            numeric_payload,
        )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_market_probability_edge_cost_floor_v2_public_payload(
            missing_digest,
        )

    tampered = {**payload, "max_net_edge": "0.010000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_market_probability_edge_cost_floor_v2_public_payload(tampered)

    tampered_report = replace(result)
    object.__setattr__(tampered_report, "pass_count", d("9.000000"))
    with pytest.raises(ValueError, match="pass_count|derived_validation_digest"):
        module.strategy_market_probability_edge_cost_floor_v2_public_payload(tampered_report)


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
    payload = module.strategy_market_probability_edge_cost_floor_v2_public_payload(
        report(candidate(market_id="unsafe-check", event_slug="unsafe-event")),
    )

    unsafe_payload = {**payload, key: value}
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_strategy_market_probability_edge_cost_floor_v2_public_payload(
            unsafe_payload,
        )


def test_validation_rejects_bad_types_flags_duplicates_and_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_market_probability_edge_cost_floor_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="duplicate probability candidate"):
        report(
            candidate(market_id="dup", event_slug="same-event", category="macro"),
            candidate(market_id="dup", event_slug="same-event", category="macro"),
        )
    with pytest.raises(ValueError, match="model_probability"):
        candidate(model_probability=0.62)
    with pytest.raises(ValueError, match="market_probability"):
        candidate(market_probability=_DecimalSubclass("0.620000"))
    with pytest.raises(ValueError, match="model_probability"):
        candidate(model_probability=d("1.200000"))
    with pytest.raises(ValueError, match="taker_fee_rate"):
        candidate(taker_fee_rate=d("-0.010000"))
    with pytest.raises(ValueError, match="watch_net_edge_floor"):
        config(watch_net_edge_floor=d("0.040000"))
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)

    result = report(candidate(market_id="consistent", event_slug="consistent-event"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result.rows[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count"):
        replace(result, pass_count=d("2.000000"))

    with pytest.raises(FrozenInstanceError):
        result.report_status = "pass"  # type: ignore[misc]


def test_export_contract_and_static_no_external_surfaces() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_STRATEGY_MARKET_PROBABILITY_EDGE_COST_FLOOR_V2_CONFIG_VERSION",
        "StrategyMarketProbabilityEdgeCostFloorV2Candidate",
        "StrategyMarketProbabilityEdgeCostFloorV2Config",
        "StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount",
        "StrategyMarketProbabilityEdgeCostFloorV2Report",
        "StrategyMarketProbabilityEdgeCostFloorV2Row",
        "build_strategy_market_probability_edge_cost_floor_v2_report",
        "strategy_market_probability_edge_cost_floor_v2_public_payload",
        "validate_strategy_market_probability_edge_cost_floor_v2_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for instance in (
        config(),
        candidate(),
        *report(candidate()).rows,
        report(candidate()),
    ):
        for field in fields(instance):
            value = getattr(instance, field.name)
            assert type(value) is not float
            if field.name.endswith(("_count", "_probability", "_edge", "_rate", "_floor")):
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
