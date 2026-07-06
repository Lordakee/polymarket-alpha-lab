from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_market_narrative_shift_v10.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_market_narrative_shift_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-market-narrative-shift-v10",
        "watch_consensus_probability_move": d("0.030000"),
        "urgent_consensus_probability_move": d("0.080000"),
        "watch_source_count_change": d("2.000000"),
        "urgent_source_count_change": d("5.000000"),
        "watch_fresh_primary_source_count": d("1.000000"),
        "urgent_fresh_primary_source_count": d("3.000000"),
        "watch_market_price_move": d("0.020000"),
        "urgent_market_price_move": d("0.060000"),
        "watch_conflict_delta": d("0.150000"),
        "urgent_conflict_delta": d("0.400000"),
        "rapid_time_window_minutes": d("60.000000"),
        "immediate_time_window_minutes": d("15.000000"),
    }
    values.update(overrides)
    return module.StrategyMarketNarrativeShiftV10Config(**values)


def shift_input(**overrides: object):
    module = api()
    values = {
        "previous_consensus_probability": d("0.410000"),
        "current_consensus_probability": d("0.420000"),
        "source_count_change": ZERO,
        "fresh_primary_source_count": ZERO,
        "market_price_move": d("0.010000"),
        "time_window_minutes": d("240.000000"),
        "conflict_delta": d("0.050000"),
    }
    values.update(overrides)
    return module.StrategyMarketNarrativeShiftV10Input(**values)


def report(
    input_value: object | None = None,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_strategy_market_narrative_shift_v10_report(
        input_value if input_value is not None else shift_input(),
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_v10_confirms_urgent_narrative_shift_from_primary_fast_signals() -> None:
    result = report(
        shift_input(
            previous_consensus_probability=d("0.410000"),
            current_consensus_probability=d("0.510000"),
            source_count_change=d("5.000000"),
            fresh_primary_source_count=d("3.000000"),
            market_price_move=d("0.070000"),
            time_window_minutes=d("10.000000"),
            conflict_delta=d("0.450000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-market-narrative-shift-v10"
    assert result.consensus_probability_move == d("0.100000")
    assert result.source_count_change_magnitude == d("5.000000")
    assert result.market_price_move_magnitude == d("0.070000")
    assert result.shift_status == "confirmed_shift"
    assert result.update_urgency == "immediate"
    assert result.research_action == "escalate_primary_source_review"
    assert result.reason_codes == (
        "consensus_probability_move_urgent",
        "source_count_change_urgent",
        "fresh_primary_sources_urgent",
        "market_price_move_urgent",
        "conflict_delta_urgent",
        "immediate_time_window_urgent",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_v10_marks_emerging_shift_for_sub_urgent_fast_signal_cluster() -> None:
    result = report(
        shift_input(
            previous_consensus_probability=d("0.410000"),
            current_consensus_probability=d("0.450000"),
            source_count_change=d("-2.000000"),
            fresh_primary_source_count=d("1.000000"),
            market_price_move=d("-0.030000"),
            time_window_minutes=d("45.000000"),
            conflict_delta=d("0.200000"),
        ),
    )

    assert result.consensus_probability_move == d("0.040000")
    assert result.source_count_change_magnitude == d("2.000000")
    assert result.market_price_move_magnitude == d("0.030000")
    assert result.shift_status == "emerging_shift"
    assert result.update_urgency == "elevated"
    assert result.research_action == "refresh_narrative_research"
    assert result.reason_codes == (
        "consensus_probability_move_watch",
        "source_count_change_watch",
        "fresh_primary_sources_watch",
        "market_price_move_watch",
        "conflict_delta_watch",
        "rapid_time_window_watch",
    )


def test_v10_stays_stable_when_probability_sources_price_and_conflict_are_quiet() -> None:
    result = report(
        shift_input(
            previous_consensus_probability=d("0.410000"),
            current_consensus_probability=d("0.420000"),
            source_count_change=d("0.000000"),
            fresh_primary_source_count=d("0.000000"),
            market_price_move=d("0.010000"),
            time_window_minutes=d("240.000000"),
            conflict_delta=d("0.050000"),
        ),
    )

    assert result.shift_status == "stable"
    assert result.update_urgency == "none"
    assert result.research_action == "no_action"
    assert result.reason_codes == ("market_narrative_shift_v10_stable",)


def test_v10_payload_is_json_ready_utc_and_decimal_only() -> None:
    module = api()
    result = module.build_strategy_market_narrative_shift_v10_report(
        shift_input(current_consensus_probability=d("0.450000")),
        config=config(),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_market_narrative_shift_v10_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["previous_consensus_probability"] == "0.410000"
    assert payload["current_consensus_probability"] == "0.450000"
    assert payload["consensus_probability_move"] == "0.040000"
    assert payload["source_count_change_magnitude"] == "0.000000"
    assert payload["market_price_move_magnitude"] == "0.010000"
    assert payload["shift_status"] == "emerging_shift"
    assert payload["update_urgency"] == "elevated"
    assert payload["research_action"] == "refresh_narrative_research"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_int_or_float_values(payload)


def test_v10_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    result = report()

    for klass in (
        module.StrategyMarketNarrativeShiftV10Config,
        module.StrategyMarketNarrativeShiftV10Input,
        module.StrategyMarketNarrativeShiftV10Report,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.shift_status = "confirmed_shift"  # type: ignore[misc]

    decimal_result_fields = {
        "previous_consensus_probability",
        "current_consensus_probability",
        "consensus_probability_move",
        "source_count_change",
        "source_count_change_magnitude",
        "fresh_primary_source_count",
        "market_price_move",
        "market_price_move_magnitude",
        "time_window_minutes",
        "conflict_delta",
    }
    for field in fields(result):
        if field.name in decimal_result_fields:
            assert type(getattr(result, field.name)) is Decimal

    with pytest.raises(ValueError, match="previous_consensus_probability"):
        shift_input(previous_consensus_probability=0.41)
    with pytest.raises(ValueError, match="current_consensus_probability"):
        shift_input(current_consensus_probability=1)
    with pytest.raises(ValueError, match="market_price_move"):
        shift_input(market_price_move=DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))  # type: ignore[call-arg]


def test_v10_validates_bounds_thresholds_flags_and_builder_types() -> None:
    module = api()
    valid_input = shift_input()

    with pytest.raises(ValueError, match="input_value"):
        module.build_strategy_market_narrative_shift_v10_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_market_narrative_shift_v10_report(
            valid_input,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="between 0 and 1"):
        shift_input(current_consensus_probability=d("1.000001"))
    with pytest.raises(ValueError, match="source_count_change"):
        shift_input(source_count_change=d("1.500000"))
    with pytest.raises(ValueError, match="fresh_primary_source_count"):
        shift_input(fresh_primary_source_count=d("-1.000000"))
    with pytest.raises(ValueError, match="time_window_minutes"):
        shift_input(time_window_minutes=ZERO)
    with pytest.raises(ValueError, match="conflict_delta"):
        shift_input(conflict_delta=d("1.000001"))
    with pytest.raises(ValueError, match="urgent_consensus_probability_move"):
        config(urgent_consensus_probability_move=d("0.020000"))
    with pytest.raises(ValueError, match="immediate_time_window_minutes"):
        config(immediate_time_window_minutes=d("90.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid_input, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_market_narrative_shift_v10_payload(replace(report(), readonly=False))
    with pytest.raises(ValueError, match="report"):
        module.strategy_market_narrative_shift_v10_payload(object())


def test_v10_report_revalidates_derived_fields_status_action_and_reasons() -> None:
    result = report()

    with pytest.raises(ValueError, match="consensus_probability_move"):
        replace(result, consensus_probability_move=d("0.020000"))
    with pytest.raises(ValueError, match="source_count_change_magnitude"):
        replace(result, source_count_change_magnitude=d("1.000000"))
    with pytest.raises(ValueError, match="market_price_move_magnitude"):
        replace(result, market_price_move_magnitude=d("0.020000"))
    with pytest.raises(ValueError, match="shift_status"):
        replace(result, shift_status="confirmed_shift")
    with pytest.raises(ValueError, match="update_urgency"):
        replace(result, update_urgency="immediate")
    with pytest.raises(ValueError, match="research_action"):
        replace(result, research_action="escalate_primary_source_review")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("market_price_move_watch", "market_price_move_watch"))


def test_v10_module_scope_has_no_network_db_or_live_trading_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_roots = {
        "asyncio",
        "csv",
        "http",
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
    forbidden_call_names = {
        "open",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert module_name.split(".")[0] not in forbidden_import_roots
