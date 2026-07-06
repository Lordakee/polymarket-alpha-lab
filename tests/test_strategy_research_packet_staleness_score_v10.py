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
        "polymarket_alpha_lab.strategy_research_packet_staleness_score_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def staleness_input(**overrides: object):
    module = api()
    values = {
        "market_id": "market-weather-001",
        "last_packet_update_minutes": d("30.000000"),
        "last_primary_source_update_minutes": d("20.000000"),
        "market_move_bps": d("10.000000"),
        "source_freshness_status": "fresh",
        "time_to_resolution_minutes": d("1440.000000"),
        "team_capacity_score": d("0.900000"),
    }
    values.update(overrides)
    return module.ResearchPacketStalenessScoreV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.strategy_research_packet_staleness_score_v10(
        staleness_input(**overrides),
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


def test_fresh_packet_with_quiet_market_stays_current() -> None:
    module = api()

    result = evaluate()

    assert is_dataclass(result)
    assert result.staleness_status == "current"
    assert result.staleness_score == d("0.036389")
    assert result.refresh_action == "monitor"
    assert result.reason_codes == (
        "packet_current",
        "primary_source_current",
        "source_status_fresh",
        "market_move_quiet",
        "resolution_window_open",
        "capacity_healthy",
        "refresh_monitor",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload == module.strategy_research_packet_staleness_score_v10_payload(result)
    assert payload["config_version"] == "strategy-research-packet-staleness-score-v10"
    assert payload["market_id"] == "market-weather-001"
    assert payload["last_packet_update_minutes"] == "30.000000"
    assert payload["last_primary_source_update_minutes"] == "20.000000"
    assert payload["market_move_bps"] == "10.000000"
    assert payload["source_freshness_status"] == "fresh"
    assert payload["time_to_resolution_minutes"] == "1440.000000"
    assert payload["team_capacity_score"] == "0.900000"
    assert payload["staleness_status"] == "current"
    assert payload["staleness_score"] == "0.036389"
    assert payload["refresh_action"] == "monitor"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))


def test_stale_packet_refreshes_now_when_sources_move_and_resolution_is_critical() -> None:
    result = evaluate(
        last_packet_update_minutes=d("420.000000"),
        last_primary_source_update_minutes=d("240.000000"),
        market_move_bps=d("-125.000000"),
        source_freshness_status="stale",
        time_to_resolution_minutes=d("45.000000"),
        team_capacity_score=d("0.400000"),
    )

    assert result.staleness_status == "stale"
    assert result.staleness_score == d("0.866667")
    assert result.refresh_action == "refresh_now"
    assert result.reason_codes == (
        "packet_stale",
        "primary_source_stale",
        "source_status_stale",
        "market_move_large",
        "resolution_window_critical",
        "capacity_constrained",
        "refresh_now",
    )


def test_blocked_packet_requires_refresh_before_use() -> None:
    result = evaluate(
        last_packet_update_minutes=d("720.000000"),
        last_primary_source_update_minutes=d("10.000000"),
        market_move_bps=d("0.000000"),
        source_freshness_status="blocked",
        time_to_resolution_minutes=d("600.000000"),
        team_capacity_score=d("0.800000"),
    )

    assert result.staleness_status == "blocked"
    assert result.staleness_score == d("0.606944")
    assert result.refresh_action == "block_refresh_required"
    assert result.reason_codes == (
        "packet_expired",
        "primary_source_current",
        "source_status_blocked",
        "market_move_quiet",
        "resolution_window_open",
        "capacity_healthy",
        "refresh_blocked",
    )


def test_validation_requires_exact_decimals_bounds_flags_and_frozen_outputs() -> None:
    module = api()
    result = evaluate()

    with pytest.raises(FrozenInstanceError):
        result.refresh_action = "refresh_now"  # type: ignore[misc]

    with pytest.raises(ValueError, match="last_packet_update_minutes must be a Decimal"):
        staleness_input(last_packet_update_minutes=30)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="team_capacity_score must be a Decimal"):
        staleness_input(team_capacity_score=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="market_move_bps must be finite"):
        staleness_input(market_move_bps=Decimal("NaN"))

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be a whole Decimal"):
        staleness_input(time_to_resolution_minutes=d("1.500000"))

    with pytest.raises(ValueError, match="last_primary_source_update_minutes must be nonnegative"):
        staleness_input(last_primary_source_update_minutes=d("-1.000000"))

    with pytest.raises(ValueError, match="team_capacity_score must be between zero and one"):
        staleness_input(team_capacity_score=d("1.100000"))

    with pytest.raises(ValueError, match="source_freshness_status must be one of"):
        staleness_input(source_freshness_status="late")

    with pytest.raises(ValueError, match="market_id must be a canonical nonblank string"):
        staleness_input(market_id=" market-weather-001 ")

    with pytest.raises(ValueError, match="input must be paper_only"):
        staleness_input(paper_only=False)

    with pytest.raises(ValueError, match="report must be readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="reason_codes must match"):
        module.ResearchPacketStalenessScoreV10Report(
            market_id="market-weather-001",
            last_packet_update_minutes=d("30.000000"),
            last_primary_source_update_minutes=d("20.000000"),
            market_move_bps=d("10.000000"),
            source_freshness_status="fresh",
            time_to_resolution_minutes=d("1440.000000"),
            team_capacity_score=d("0.900000"),
            staleness_status="current",
            staleness_score=d("0.036389"),
            refresh_action="monitor",
            reason_codes=("refresh_now",),
        )


def test_payload_rejects_bad_dicts_and_non_report_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.strategy_research_packet_staleness_score_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_research_packet_staleness_score_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "staleness_score": 0.1,
            },
        )

    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.strategy_research_packet_staleness_score_v10_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "last_packet_update_minutes": 30,
            },
        )

    with pytest.raises(ValueError, match="payload field is not supported"):
        module.strategy_research_packet_staleness_score_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "extra": "field"},
        )

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_research_packet_staleness_score_v10_payload(object())


def test_module_scope_is_paper_report_readonly_without_side_effect_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_research_packet_staleness_score_v10.py",
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
