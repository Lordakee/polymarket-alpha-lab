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
        "polymarket_alpha_lab.strategy_signal_freshness_decay_curve_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(**overrides: object):
    module = api()
    values = {
        "signal_age_minutes": d("60.000000"),
        "half_life_minutes": d("60.000000"),
        "source_reliability": d("1.000000"),
        "market_time_sensitivity": d("0.000000"),
        "resolution_urgency": d("0.000000"),
        "last_confirmed_update_minutes": d("0.000000"),
    }
    values.update(overrides)
    return module.SignalFreshnessDecayCurveV10Input(**values)


def evaluate(**overrides: object):
    return api().strategy_signal_freshness_decay_curve_v10(signal(**overrides))


def walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for child in value.values():
            items.extend(walk(child))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(walk(child))
        return tuple(items)
    return (value,)


def test_half_life_signal_decays_to_half_weight_with_readonly_payload() -> None:
    result = evaluate()

    assert is_dataclass(result)
    assert result.freshness_weight == d("0.500000")
    assert result.decay_status == "decaying"
    assert result.refresh_required is False
    assert result.reason_codes == (
        "source_reliability_high",
        "time_sensitivity_normal",
        "resolution_urgency_normal",
        "confirmed_update_recent",
        "signal_decaying",
        "decay_status_decaying",
        "refresh_not_required",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload == api().strategy_signal_freshness_decay_curve_v10_payload(result)
    assert payload["config_version"] == "strategy-signal-freshness-decay-curve-v10"
    assert payload["signal_age_minutes"] == "60.000000"
    assert payload["half_life_minutes"] == "60.000000"
    assert payload["freshness_weight"] == "0.500000"
    assert payload["decay_status"] == "decaying"
    assert payload["refresh_required"] is False
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))


def test_time_pressure_and_old_confirmation_force_refresh() -> None:
    result = evaluate(
        source_reliability=d("0.800000"),
        market_time_sensitivity=d("1.000000"),
        resolution_urgency=d("1.000000"),
        last_confirmed_update_minutes=d("60.000000"),
    )

    assert result.freshness_weight == d("0.200000")
    assert result.decay_status == "stale"
    assert result.refresh_required is True
    assert result.reason_codes == (
        "source_reliability_high",
        "time_sensitivity_high",
        "resolution_urgency_high",
        "confirmed_update_stale",
        "signal_decaying",
        "decay_status_stale",
        "refresh_required",
    )


def test_low_reliability_signal_is_weighted_down_without_forced_refresh() -> None:
    result = evaluate(
        signal_age_minutes=d("0.000000"),
        source_reliability=d("0.400000"),
    )

    assert result.freshness_weight == d("0.400000")
    assert result.decay_status == "decaying"
    assert result.refresh_required is False
    assert "source_reliability_low" in result.reason_codes
    assert "signal_fresh" in result.reason_codes


def test_validation_requires_decimal_inputs_bounds_flags_and_frozen_outputs() -> None:
    module = api()
    result = evaluate()

    with pytest.raises(FrozenInstanceError):
        result.decay_status = "fresh"  # type: ignore[misc]

    with pytest.raises(ValueError, match="signal_age_minutes must be a Decimal"):
        signal(signal_age_minutes=60)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_reliability must be a Decimal"):
        signal(source_reliability=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_reliability must be a Decimal"):
        signal(source_reliability=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="signal_age_minutes must be finite"):
        signal(signal_age_minutes=Decimal("NaN"))

    with pytest.raises(ValueError, match="half_life_minutes must be greater than zero"):
        signal(half_life_minutes=d("0.000000"))

    with pytest.raises(ValueError, match="market_time_sensitivity must be between 0 and 1"):
        signal(market_time_sensitivity=d("1.000001"))

    with pytest.raises(ValueError, match="input must be paper_only"):
        signal(paper_only=False)

    with pytest.raises(ValueError, match="result must be readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="reason_codes must match"):
        module.SignalFreshnessDecayCurveV10Result(
            signal_age_minutes=d("60.000000"),
            half_life_minutes=d("60.000000"),
            source_reliability=d("1.000000"),
            market_time_sensitivity=d("0.000000"),
            resolution_urgency=d("0.000000"),
            last_confirmed_update_minutes=d("0.000000"),
            freshness_weight=d("0.500000"),
            decay_status="decaying",
            refresh_required=False,
            reason_codes=("refresh_required",),
        )


def test_payload_rejects_bad_dicts_and_non_report_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="payload must be readonly"):
        module.strategy_signal_freshness_decay_curve_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_signal_freshness_decay_curve_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "freshness_weight": 0.5,
            },
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.strategy_signal_freshness_decay_curve_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "signal_age_minutes": 60,
            },
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.strategy_signal_freshness_decay_curve_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "extra": "field"},
        )

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_signal_freshness_decay_curve_v10_payload(object())


def test_module_scope_is_paper_report_readonly_without_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_signal_freshness_decay_curve_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "signing",
        "order placement",
        "submit",
        "cancel",
        "database",
        "network",
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
