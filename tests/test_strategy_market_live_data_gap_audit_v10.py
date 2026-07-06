from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_market_live_data_gap_audit_v10"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def audit_input(**overrides: object) -> Any:
    module = api()
    values = {
        "market_id": "fed-july-policy-path",
        "source_family_count": d("3.000000"),
        "required_source_family_count": d("3.000000"),
        "last_market_snapshot_minutes": d("2.000000"),
        "last_primary_source_minutes": d("10.000000"),
        "last_orderbook_depth_minutes": d("1.000000"),
        "time_to_resolution_minutes": d("1440.000000"),
    }
    values.update(overrides)
    return module.StrategyMarketLiveDataGapAuditV10Input(**values)


def audit(**overrides: object) -> Any:
    module = api()
    return module.audit_strategy_market_live_data_gap_v10(
        audit_input(**overrides),
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float, field.name
        assert type(value) is not int, field.name


def assert_payload_has_no_runtime_numbers(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for child in value.values():
            assert_payload_has_no_runtime_numbers(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_has_no_runtime_numbers(child)


def test_complete_live_data_returns_readonly_monitor_payload() -> None:
    module = api()

    result = audit()

    assert isinstance(result, module.StrategyMarketLiveDataGapAuditV10Result)
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.data_gap_status == "complete"
    assert result.missing_data_types == ()
    assert result.refresh_priority == "monitor"
    assert result.reason_codes == ("live_data_gap_audit_clear",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)


def test_watch_status_tracks_aging_live_data_before_material_gap() -> None:
    result = audit(
        last_market_snapshot_minutes=d("6.000000"),
        last_primary_source_minutes=d("45.000000"),
        last_orderbook_depth_minutes=d("6.000000"),
        time_to_resolution_minutes=d("480.000000"),
    )

    assert result.data_gap_status == "watch"
    assert result.missing_data_types == (
        "market_snapshot",
        "primary_source",
        "orderbook_depth",
    )
    assert result.refresh_priority == "normal"
    assert result.reason_codes == (
        "live_data_gap_watch",
        "market_snapshot_aging",
        "orderbook_depth_aging",
        "primary_source_aging",
    )


def test_incomplete_status_prioritizes_missing_quorum_and_stale_sources() -> None:
    result = audit(
        source_family_count=d("1.000000"),
        required_source_family_count=d("3.000000"),
        last_market_snapshot_minutes=d("20.000000"),
        last_primary_source_minutes=d("150.000000"),
        last_orderbook_depth_minutes=d("20.000000"),
        time_to_resolution_minutes=d("180.000000"),
    )

    assert result.data_gap_status == "incomplete"
    assert result.missing_data_types == (
        "source_family_quorum",
        "market_snapshot",
        "primary_source",
        "orderbook_depth",
    )
    assert result.refresh_priority == "high"
    assert result.reason_codes == (
        "live_data_gap_incomplete",
        "market_snapshot_stale",
        "orderbook_depth_stale",
        "primary_source_stale",
        "resolution_near",
        "source_family_count_below_required",
    )


def test_critical_status_uses_urgent_priority_for_empty_sources_and_imminent_resolution() -> None:
    result = audit(
        source_family_count=d("0.000000"),
        required_source_family_count=d("3.000000"),
        last_market_snapshot_minutes=d("90.000000"),
        last_primary_source_minutes=d("420.000000"),
        last_orderbook_depth_minutes=d("90.000000"),
        time_to_resolution_minutes=d("45.000000"),
    )

    assert result.data_gap_status == "critical"
    assert result.refresh_priority == "urgent"
    assert result.missing_data_types == (
        "source_family_quorum",
        "market_snapshot",
        "primary_source",
        "orderbook_depth",
    )
    assert result.reason_codes == (
        "live_data_gap_critical",
        "market_snapshot_critical",
        "orderbook_depth_critical",
        "primary_source_critical",
        "resolution_imminent",
        "source_family_count_zero",
    )


def test_payload_serializes_decimals_as_strings_and_exposes_result_payload() -> None:
    module = api()
    result = audit(
        source_family_count=d("1.000000"),
        required_source_family_count=d("3.000000"),
        last_market_snapshot_minutes=d("20.000000"),
        last_primary_source_minutes=d("150.000000"),
        last_orderbook_depth_minutes=d("20.000000"),
        time_to_resolution_minutes=d("180.000000"),
    )

    payload = module.strategy_market_live_data_gap_audit_v10_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert result.payload == payload
    assert payload["market_id"] == "fed-july-policy-path"
    assert payload["source_family_count"] == "1.000000"
    assert payload["required_source_family_count"] == "3.000000"
    assert payload["last_market_snapshot_minutes"] == "20.000000"
    assert payload["last_primary_source_minutes"] == "150.000000"
    assert payload["last_orderbook_depth_minutes"] == "20.000000"
    assert payload["time_to_resolution_minutes"] == "180.000000"
    assert payload["data_gap_status"] == "incomplete"
    assert payload["missing_data_types"] == [
        "source_family_quorum",
        "market_snapshot",
        "primary_source",
        "orderbook_depth",
    ]
    assert payload["refresh_priority"] == "high"
    assert payload["reason_codes"] == [
        "live_data_gap_incomplete",
        "market_snapshot_stale",
        "orderbook_depth_stale",
        "primary_source_stale",
        "resolution_near",
        "source_family_count_below_required",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"150.000000"' in encoded
    assert_payload_has_no_runtime_numbers(payload)


def test_validation_rejects_non_decimal_granular_nonfinite_and_unsafe_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="market_id must be a nonblank trimmed string"):
        audit_input(market_id=" fed ")
    with pytest.raises(ValueError, match="source_family_count must be exactly Decimal"):
        audit_input(source_family_count=_DecimalSubclass("3.000000"))
    with pytest.raises(ValueError, match="last_primary_source_minutes must be a Decimal"):
        audit_input(last_primary_source_minutes=10)
    with pytest.raises(ValueError, match="last_market_snapshot_minutes precision is too granular"):
        audit_input(last_market_snapshot_minutes=d("2.0000001"))
    with pytest.raises(ValueError, match="last_orderbook_depth_minutes must be finite"):
        audit_input(last_orderbook_depth_minutes=d("NaN"))
    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        audit_input(time_to_resolution_minutes=d("-1.000000"))
    with pytest.raises(ValueError, match="source_family_count must be a whole Decimal"):
        audit_input(source_family_count=d("1.500000"))
    with pytest.raises(ValueError, match="required_source_family_count must be positive"):
        audit_input(required_source_family_count=d("0.000000"))
    with pytest.raises(ValueError, match="input paper_only must be True"):
        audit_input(paper_only=False)

    with pytest.raises(ValueError, match="input_row must be a StrategyMarketLiveDataGapAuditV10Input"):
        module.audit_strategy_market_live_data_gap_v10(object())

    result = audit()
    with pytest.raises(FrozenInstanceError):
        result.data_gap_status = "critical"  # type: ignore[misc]
    with pytest.raises(ValueError, match="result readonly must be True"):
        module.StrategyMarketLiveDataGapAuditV10Result(
            **{**result.__dict__, "readonly": False},
        )


def test_result_revalidates_derived_status_priority_missing_data_and_reasons() -> None:
    result = audit()
    module = api()

    with pytest.raises(ValueError, match="refresh_priority must match data_gap_status"):
        module.StrategyMarketLiveDataGapAuditV10Result(
            **{**result.__dict__, "refresh_priority": "urgent"},
        )
    with pytest.raises(ValueError, match="missing_data_types must match inputs"):
        module.StrategyMarketLiveDataGapAuditV10Result(
            **{**result.__dict__, "missing_data_types": ("market_snapshot",)},
        )
    with pytest.raises(ValueError, match="reason_codes must match inputs"):
        module.StrategyMarketLiveDataGapAuditV10Result(
            **{**result.__dict__, "reason_codes": ("live_data_gap_watch",)},
        )


def test_module_is_paper_report_readonly_without_io_or_execution_surface() -> None:
    path = Path("src/polymarket_alpha_lab/strategy_market_live_data_gap_audit_v10.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_imports = {
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_call_names = {
        "auth",
        "cancel",
        "connect",
        "create_order",
        "login",
        "open",
        "place_order",
        "submit_order",
        "trade",
        "wallet",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_call_names
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_call_names

    forbidden_terms = (
        "api_key",
        "private_key",
        "secret",
        "signing",
        "sqlite",
        "postgres",
        "psycopg",
        "requests",
        "httpx",
        "urllib",
    )
    lowered = source.lower()
    for term in forbidden_terms:
        assert term not in lowered
