from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/strategy_event_team_assignment_v10.py",
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_event_team_assignment_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-event-team-assignment-v10-test",
        "category_fit_weight": d("0.500000"),
        "team_history_weight": d("0.300000"),
        "source_coverage_weight": d("0.200000"),
        "high_complexity_threshold": d("0.700000"),
        "low_source_coverage_threshold": d("0.600000"),
        "weak_history_threshold": d("0.500000"),
        "max_support_team_count": d("2"),
    }
    values.update(overrides)
    return module.StrategyEventTeamAssignmentV10Config(**values)


def market(
    event_id: str,
    market_category: str,
    *,
    asset: str | None = None,
    league: str | None = None,
    country: str | None = None,
    complexity: str = "0.300000",
    coverage: str = "0.900000",
):
    module = api()
    return module.StrategyEventTeamAssignmentV10Market(
        event_id=event_id,
        market_category=market_category,
        asset=asset,
        league=league,
        country=country,
        parse_rule_complexity_score=d(complexity),
        source_coverage_score=d(coverage),
    )


def history(
    team_id: str,
    *,
    resolved: str = "100",
    accuracy: str = "0.800000",
    calibration: str = "0.800000",
    source: str = "0.800000",
):
    module = api()
    return module.StrategyEventTeamAssignmentV10TeamHistory(
        team_id=team_id,
        resolved_event_count=d(resolved),
        historical_accuracy_score=d(accuracy),
        calibration_score=d(calibration),
        source_reliability_score=d(source),
    )


def full_history():
    return (
        history("politics", accuracy="0.760000", calibration="0.800000"),
        history("crypto_btc", accuracy="0.820000", calibration="0.780000"),
        history("crypto_eth", accuracy="0.700000", calibration="0.720000"),
        history("macro_rates", accuracy="0.740000", calibration="0.760000"),
        history("equity_indices", accuracy="0.830000", calibration="0.810000"),
        history("commodities_gold", accuracy="0.850000", calibration="0.820000"),
        history("sports_soccer", accuracy="0.880000", calibration="0.840000"),
        history("sports_basketball", accuracy="0.860000", calibration="0.830000"),
        history("sports_other", accuracy="0.690000", calibration="0.710000"),
    )


def build(*events: object, histories: object | None = None, cfg: object | None = None):
    module = api()
    return module.build_strategy_event_team_assignment_v10_report(
        events,
        team_histories=histories if histories is not None else full_history(),
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_assigns_domain_leads_supports_escalations_and_reason_codes() -> None:
    module = api()

    report = build(
        market("event-politics", "politics.election", country="US"),
        market("event-index", "finance", asset="NASDAQ"),
        market("event-gold", "finance.commodities", asset="XAU"),
        market(
            "event-soccer",
            "sports",
            league="UEFA Champions League",
            country="GB",
            complexity="0.850000",
            coverage="0.550000",
        ),
        market("event-basketball", "sports", league="NBA"),
    )

    assert is_dataclass(report)
    assert type(report) is module.StrategyEventTeamAssignmentV10Report
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-event-team-assignment-v10-test"
    assert report.input_count == d("5")
    assert report.assigned_event_count == d("5")
    assert report.escalated_event_count == d("1")
    assert report.assignment_status == "watch"
    assert report.reason_codes == (
        "strategy_event_team_assignment_v10_assigned",
        "strategy_event_team_assignment_v10_high_complexity",
        "strategy_event_team_assignment_v10_low_source_coverage",
        "strategy_event_team_assignment_v10_escalated",
    )

    by_event_id = {row.event_id: row for row in report.rows}
    assert by_event_id["event-politics"].lead_team == "politics"
    assert by_event_id["event-politics"].support_teams == ("macro_rates",)
    assert by_event_id["event-politics"].escalation_team == "politics"
    assert by_event_id["event-politics"].assignment_status == "assigned"

    assert by_event_id["event-index"].lead_team == "equity_indices"
    assert by_event_id["event-index"].support_teams == ("macro_rates", "crypto_btc")
    assert by_event_id["event-gold"].lead_team == "commodities_gold"
    assert by_event_id["event-gold"].support_teams == ("macro_rates", "equity_indices")
    assert by_event_id["event-basketball"].lead_team == "sports_basketball"
    assert by_event_id["event-basketball"].support_teams == ("sports_other", "sports_soccer")

    soccer = by_event_id["event-soccer"]
    assert soccer.lead_team == "sports_soccer"
    assert soccer.support_teams == ("sports_other", "sports_basketball")
    assert soccer.escalation_team == "research_quality"
    assert soccer.assignment_status == "escalated"
    assert soccer.lead_assignment_score == d("0.862000")
    assert soccer.reason_codes == (
        "strategy_event_team_assignment_v10_category_sports_soccer",
        "strategy_event_team_assignment_v10_high_complexity",
        "strategy_event_team_assignment_v10_low_source_coverage",
        "strategy_event_team_assignment_v10_escalated",
    )
    assert soccer.paper_only is True
    assert soccer.report_only is True
    assert soccer.readonly is True


def test_crypto_lead_can_be_selected_by_history_when_category_is_generic() -> None:
    report = build(
        market(
            "event-generic-crypto",
            "finance.crypto",
            complexity="0.400000",
            coverage="0.900000",
        ),
        histories=(
            history("crypto_btc", accuracy="0.400000", calibration="0.450000"),
            history("crypto_eth", accuracy="0.900000", calibration="0.880000"),
            history("macro_rates", accuracy="0.700000", calibration="0.700000"),
        ),
    )

    row = report.rows[0]
    assert row.lead_team == "crypto_eth"
    assert row.support_teams == ("crypto_btc", "macro_rates")
    assert row.escalation_team == "crypto_eth"
    assert row.lead_assignment_score == d("0.888000")
    assert row.reason_codes == (
        "strategy_event_team_assignment_v10_category_crypto",
        "strategy_event_team_assignment_v10_assigned",
    )


def test_missing_history_still_routes_but_weak_history_escalates() -> None:
    report = build(
        market("event-btc", "finance.crypto", asset="BTC"),
        histories=(
            history(
                "crypto_btc",
                resolved="5",
                accuracy="0.200000",
                calibration="0.300000",
                source="0.400000",
            ),
        ),
    )

    row = report.rows[0]
    assert row.lead_team == "crypto_btc"
    assert row.support_teams == ("crypto_eth", "macro_rates")
    assert row.escalation_team == "research_quality"
    assert row.assignment_status == "escalated"
    assert row.team_history_score == d("0.168000")
    assert row.reason_codes == (
        "strategy_event_team_assignment_v10_asset_crypto_btc",
        "strategy_event_team_assignment_v10_weak_team_history",
        "strategy_event_team_assignment_v10_escalated",
    )


def test_empty_inputs_return_readonly_clear_report() -> None:
    report = build()

    assert report.input_count == d("0")
    assert report.assigned_event_count == d("0")
    assert report.escalated_event_count == d("0")
    assert report.assignment_status == "clear"
    assert report.reason_codes == ("strategy_event_team_assignment_v10_clear",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_and_scores_are_decimal_only() -> None:
    module = api()
    cfg = config()
    input_market = market("event-btc", "finance.crypto", asset="BTC")
    input_history = history("crypto_btc")
    report = build(input_market, histories=(input_history,), cfg=cfg)
    row = report.rows[0]

    for exported_name in module.__all__:
        exported_value = getattr(module, exported_name)
        if isinstance(exported_value, type):
            assert is_dataclass(exported_value)
            assert exported_value.__dataclass_params__.frozen is True

    for item in (cfg, input_market, input_history, row, report):
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert getattr(item, field.name) is True
            if field.name.endswith(("_score", "_count", "_weight", "_threshold")):
                assert field.type == "Decimal"
                assert type(getattr(item, field.name)) is Decimal

    with pytest.raises(ValueError, match="source_coverage_score"):
        replace(input_market, source_coverage_score=0.8)
    with pytest.raises(ValueError, match="parse_rule_complexity_score"):
        replace(input_market, parse_rule_complexity_score=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="market_category"):
        replace(input_market, market_category=_StringSubclass("finance.crypto"))
    with pytest.raises(ValueError, match="max_support_team_count"):
        config(max_support_team_count=d("2.500000"))
    with pytest.raises(ValueError, match="weight sum"):
        config(source_coverage_weight=d("0.300000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(cfg, paper_only=False)


def test_payload_helper_uses_decimal_strings_and_rejects_unsafe_surfaces() -> None:
    module = api()
    payload = module.strategy_event_team_assignment_v10_payload(
        build(market("event-nba", "sports", league="NBA")),
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["rows"][0]["lead_assignment_score"] == "0.929000"
    assert '"0.929000"' in encoded
    assert all(type(value) is not float for value in _walk(payload))

    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_event_team_assignment_v10_payload(
            replace(build(market("event-nba", "sports", league="NBA")), paper_only=False),
        )
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_event_team_assignment_v10_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "wallet": "x"},
        )


def test_module_has_no_float_literals_or_live_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "live trading",
        "order",
        "cancel",
        "replace",
        "signing",
        "api_key",
        "private_key",
        "payload_json",
        "sqlite",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "open(",
        "read(",
        "write(",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in {"__import__", "open", "read", "write", "float"}
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in {
                    "connect",
                    "execute",
                    "open",
                    "request",
                    "read",
                    "read_text",
                    "write",
                    "write_text",
                }
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in {
                    "httpx",
                    "os",
                    "pathlib",
                    "psycopg",
                    "requests",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "supabase",
                }
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in {
                "httpx",
                "os",
                "pathlib",
                "psycopg",
                "requests",
                "socket",
                "sqlite3",
                "subprocess",
                "supabase",
            }


def _walk(value: object):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value
