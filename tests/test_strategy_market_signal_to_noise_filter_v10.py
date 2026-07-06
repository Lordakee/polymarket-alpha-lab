from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_market_signal_to_noise_filter_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def input_row(**overrides: object):
    signal_filter = api()
    values = {
        "market_id": "market-2026-fed-cuts",
        "market_move_bps": d("120.000000"),
        "source_confirmation_count": d("3"),
        "rumor_count": d("0"),
        "source_reliability_score": d("0.900000"),
        "model_disagreement_score": d("0.050000"),
        "time_window_minutes": d("20.000000"),
    }
    values.update(overrides)
    return signal_filter.StrategyMarketSignalToNoiseFilterV10Input(**values)


def evaluate(**overrides: object):
    signal_filter = api()
    return signal_filter.strategy_market_signal_to_noise_filter_v10(
        input_row(**overrides),
    )


def test_filter_keeps_confirmed_market_signal_with_decimal_payload() -> None:
    result = evaluate()

    assert is_dataclass(result)
    assert result.market_id == "market-2026-fed-cuts"
    assert result.signal_quality_status == "confirmed_signal"
    assert result.signal_to_noise_score == d("3.716667")
    assert result.filter_action == "keep_candidate"
    assert result.reason_codes == (
        "material_market_move",
        "confirmed_by_sources",
        "reliable_sources",
        "model_consensus",
        "fresh_window",
        "signal_score_passed",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert is_dataclass(result.payload)
    assert result.payload.market_id == "market-2026-fed-cuts"
    assert result.payload.market_move_bps == d("120.000000")
    assert result.payload.source_confirmation_count == d("3")
    assert result.payload.rumor_count == d("0")
    assert result.payload.source_reliability_score == d("0.900000")
    assert result.payload.model_disagreement_score == d("0.050000")
    assert result.payload.time_window_minutes == d("20.000000")
    assert result.payload.signal_to_noise_score == d("3.716667")
    assert result.payload.paper_only is True
    assert result.payload.report_only is True
    assert result.payload.readonly is True


def test_filter_drops_noisy_unconfirmed_market_signal() -> None:
    result = evaluate(
        market_move_bps=d("15.000000"),
        source_confirmation_count=d("0"),
        rumor_count=d("4"),
        source_reliability_score=d("0.300000"),
        model_disagreement_score=d("0.800000"),
        time_window_minutes=d("120.000000"),
    )

    assert result.signal_quality_status == "noise_rejected"
    assert result.signal_to_noise_score == d("-5.950000")
    assert result.filter_action == "drop_candidate"
    assert result.reason_codes == (
        "market_move_below_threshold",
        "source_confirmation_absent",
        "source_reliability_low",
        "rumor_pressure_high",
        "model_disagreement_high",
        "stale_window",
        "signal_score_failed",
    )


def test_filter_routes_borderline_signal_to_manual_review() -> None:
    result = evaluate(
        market_move_bps=d("80.000000"),
        source_confirmation_count=d("2"),
        rumor_count=d("1"),
        source_reliability_score=d("0.800000"),
        model_disagreement_score=d("0.100000"),
        time_window_minutes=d("30.000000"),
    )

    assert result.signal_quality_status == "watch_signal"
    assert result.signal_to_noise_score == d("1.075000")
    assert result.filter_action == "review_manually"
    assert result.reason_codes == (
        "material_market_move",
        "confirmed_by_sources",
        "reliable_sources",
        "rumor_pressure_present",
        "model_consensus",
        "fresh_window",
        "signal_score_review",
    )


def test_filter_payload_serializes_json_without_floats_or_live_surface() -> None:
    signal_filter = api()
    result = evaluate()
    payload = signal_filter.strategy_market_signal_to_noise_filter_v10_payload(result)
    payload_text = repr(payload)

    assert payload["market_id"] == "market-2026-fed-cuts"
    assert payload["signal_to_noise_score"] == "3.716667"
    assert payload["payload"]["market_move_bps"] == "120.000000"
    assert payload["payload"]["source_confirmation_count"] == "3"
    assert "Decimal(" not in payload_text

    def assert_no_float_or_int(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float_or_int(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float_or_int(item)
        else:
            assert type(value) is not float
            assert type(value) is not int

    assert_no_float_or_int(payload)

    with pytest.raises(ValueError, match="payload must be readonly"):
        signal_filter.strategy_market_signal_to_noise_filter_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        signal_filter.strategy_market_signal_to_noise_filter_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "signal_to_noise_score": 0.1,
            },
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        signal_filter.strategy_market_signal_to_noise_filter_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet": "redacted",
            },
        )


def test_filter_validates_decimal_inputs_flags_and_frozen_outputs() -> None:
    result = evaluate()

    with pytest.raises(FrozenInstanceError):
        result.filter_action = "drop_candidate"  # type: ignore[misc]

    with pytest.raises(ValueError, match="market_move_bps must be a Decimal"):
        input_row(market_move_bps=120)

    with pytest.raises(ValueError, match="market_move_bps must be a Decimal"):
        input_row(market_move_bps=_DecimalSubclass("120.000000"))

    with pytest.raises(ValueError, match="market_move_bps must be finite"):
        input_row(market_move_bps=Decimal("NaN"))

    with pytest.raises(ValueError, match="source_confirmation_count must be integral"):
        input_row(source_confirmation_count=d("1.500000"))

    with pytest.raises(ValueError, match="source_reliability_score must be between"):
        input_row(source_reliability_score=d("1.100000"))

    with pytest.raises(ValueError, match="time_window_minutes must be positive"):
        input_row(time_window_minutes=d("0.000000"))

    with pytest.raises(ValueError, match="input must be readonly"):
        input_row(readonly=False)

    with pytest.raises(ValueError, match="payload must match result"):
        replace(
            result,
            payload=replace(result.payload, signal_to_noise_score=d("0.000000")),
        )


def test_module_scope_has_no_live_forbidden_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_market_signal_to_noise_filter_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "db",
        "file io",
        "open(",
        "advice",
        "order",
        "trade",
        "trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
