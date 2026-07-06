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
        "polymarket_alpha_lab.strategy_research_source_refresh_schedule_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def schedule_input(**overrides: object):
    module = api()
    values = {
        "market_id": "market-weather-001",
        "source_family": "official_weather",
        "freshness_status": "fresh",
        "source_reliability_score": d("0.900000"),
        "market_time_sensitivity": d("0.300000"),
        "time_to_resolution_minutes": d("1440.000000"),
        "team_capacity_score": d("0.850000"),
    }
    values.update(overrides)
    return module.ResearchSourceRefreshScheduleV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.strategy_research_source_refresh_schedule_v10(
        schedule_input(**overrides),
    )


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


def test_fresh_reliable_low_sensitivity_source_defers_refresh() -> None:
    module = api()

    result = evaluate()

    assert is_dataclass(result)
    assert result.refresh_schedule_status == "deferred"
    assert result.next_refresh_minutes == d("240.000000")
    assert result.refresh_cadence_minutes == d("240.000000")
    assert result.reason_codes == (
        "freshness_fresh",
        "reliability_high",
        "time_sensitivity_low",
        "resolution_window_open",
        "capacity_healthy",
        "refresh_deferred",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload == module.strategy_research_source_refresh_schedule_v10_payload(result)
    assert payload["config_version"] == "strategy-research-source-refresh-schedule-v10"
    assert payload["market_id"] == "market-weather-001"
    assert payload["source_family"] == "official_weather"
    assert payload["freshness_status"] == "fresh"
    assert payload["source_reliability_score"] == "0.900000"
    assert payload["market_time_sensitivity"] == "0.300000"
    assert payload["time_to_resolution_minutes"] == "1440.000000"
    assert payload["team_capacity_score"] == "0.850000"
    assert payload["refresh_schedule_status"] == "deferred"
    assert payload["next_refresh_minutes"] == "240.000000"
    assert payload["refresh_cadence_minutes"] == "240.000000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))


def test_stale_low_reliability_critical_source_refreshes_now() -> None:
    result = evaluate(
        freshness_status="stale",
        source_reliability_score=d("0.450000"),
        market_time_sensitivity=d("0.950000"),
        time_to_resolution_minutes=d("45.000000"),
        team_capacity_score=d("0.700000"),
    )

    assert result.refresh_schedule_status == "refresh_now"
    assert result.next_refresh_minutes == d("0.000000")
    assert result.refresh_cadence_minutes == d("15.000000")
    assert result.reason_codes == (
        "freshness_stale",
        "reliability_low",
        "time_sensitivity_high",
        "resolution_window_critical",
        "capacity_usable",
        "refresh_now",
    )


def test_constrained_capacity_limits_aging_compressed_refresh() -> None:
    result = evaluate(
        freshness_status="aging",
        source_reliability_score=d("0.650000"),
        market_time_sensitivity=d("0.750000"),
        time_to_resolution_minutes=d("180.000000"),
        team_capacity_score=d("0.350000"),
    )

    assert result.refresh_schedule_status == "capacity_limited"
    assert result.next_refresh_minutes == d("60.000000")
    assert result.refresh_cadence_minutes == d("30.000000")
    assert result.reason_codes == (
        "freshness_aging",
        "reliability_medium",
        "time_sensitivity_medium",
        "resolution_window_compressed",
        "capacity_constrained",
        "refresh_capacity_limited",
    )


def test_validation_requires_exact_decimals_bounds_flags_and_frozen_outputs() -> None:
    module = api()
    result = evaluate()

    with pytest.raises(FrozenInstanceError):
        result.refresh_schedule_status = "refresh_now"  # type: ignore[misc]

    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        schedule_input(source_reliability_score=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        schedule_input(source_reliability_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="market_time_sensitivity must be finite"):
        schedule_input(market_time_sensitivity=Decimal("NaN"))

    with pytest.raises(ValueError, match="team_capacity_score must be between zero and one"):
        schedule_input(team_capacity_score=d("1.100000"))

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be a whole Decimal"):
        schedule_input(time_to_resolution_minutes=d("1.500000"))

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        schedule_input(time_to_resolution_minutes=d("-1.000000"))

    with pytest.raises(ValueError, match="freshness_status must be one of"):
        schedule_input(freshness_status="late")

    with pytest.raises(ValueError, match="market_id must be a canonical nonblank string"):
        schedule_input(market_id=" market-weather-001 ")

    with pytest.raises(ValueError, match="input must be paper_only"):
        schedule_input(paper_only=False)

    with pytest.raises(ValueError, match="report must be readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="reason_codes must match"):
        module.ResearchSourceRefreshScheduleV10Report(
            market_id="market-weather-001",
            source_family="official_weather",
            freshness_status="fresh",
            source_reliability_score=d("0.900000"),
            market_time_sensitivity=d("0.300000"),
            time_to_resolution_minutes=d("1440.000000"),
            team_capacity_score=d("0.850000"),
            refresh_schedule_status="deferred",
            next_refresh_minutes=d("240.000000"),
            refresh_cadence_minutes=d("240.000000"),
            reason_codes=("refresh_now",),
            payload=result.payload,
        )


def test_payload_rejects_bad_dicts_and_non_report_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.strategy_research_source_refresh_schedule_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_research_source_refresh_schedule_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "next_refresh_minutes": 1.5,
            },
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.strategy_research_source_refresh_schedule_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "refresh_cadence_minutes": 15,
            },
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.strategy_research_source_refresh_schedule_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "extra": "field"},
        )

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_research_source_refresh_schedule_v10_payload(object())


def test_module_scope_is_paper_report_readonly_without_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_research_source_refresh_schedule_v10.py",
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
