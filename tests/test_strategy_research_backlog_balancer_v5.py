from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_research_backlog_balancer_v5 import (
    StrategyResearchBacklogBalancerV5Config,
    StrategyResearchBacklogCandidateV5,
    StrategyResearchBacklogTeamSpecializationV5,
    StrategyResearchBacklogTeamStateV5,
    build_strategy_research_backlog_balancer_v5_report,
    strategy_research_backlog_balancer_v5_payload,
)


GENERATED_AT = datetime(2026, 7, 1, 15, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def team_state(
    team_id: str,
    *,
    backlog_item_count: str,
    backlog_capacity_count: str = "10",
    active_research_now_count: str = "0",
    max_research_now_count: str = "2",
) -> StrategyResearchBacklogTeamStateV5:
    return StrategyResearchBacklogTeamStateV5(
        team_id=team_id,
        backlog_item_count=d(backlog_item_count),
        backlog_capacity_count=d(backlog_capacity_count),
        active_research_now_count=d(active_research_now_count),
        max_research_now_count=d(max_research_now_count),
    )


def specialization(
    team_id: str,
    score: str,
) -> StrategyResearchBacklogTeamSpecializationV5:
    return StrategyResearchBacklogTeamSpecializationV5(
        team_id=team_id,
        specialization_score=d(score),
    )


def candidate(
    market_slug: str,
    *,
    market_ev: str,
    source_freshness_score: str,
    deadline_pressure_score: str,
    specializations: tuple[StrategyResearchBacklogTeamSpecializationV5, ...],
) -> StrategyResearchBacklogCandidateV5:
    return StrategyResearchBacklogCandidateV5(
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        category_id="finance.crypto.btc",
        market_ev=d(market_ev),
        source_freshness_score=d(source_freshness_score),
        deadline_pressure_score=d(deadline_pressure_score),
        team_specializations=specializations,
    )


def base_config() -> StrategyResearchBacklogBalancerV5Config:
    return StrategyResearchBacklogBalancerV5Config(
        min_market_ev=d("0.05"),
        min_source_freshness_score=d("0.40"),
        research_now_score_threshold=d("1.00"),
        research_later_score_threshold=d("0.50"),
    )


def test_balances_markets_into_research_now_later_defer_and_drop() -> None:
    report = build_strategy_research_backlog_balancer_v5_report(
        (
            candidate(
                "btc-fed-cut-hedge",
                market_ev="0.42",
                source_freshness_score="0.95",
                deadline_pressure_score="0.80",
                specializations=(
                    specialization("crypto_btc", "0.90"),
                    specialization("macro_rates", "0.60"),
                ),
            ),
            candidate(
                "rates-dot-plot-review",
                market_ev="0.24",
                source_freshness_score="0.75",
                deadline_pressure_score="0.30",
                specializations=(
                    specialization("macro_rates", "0.85"),
                    specialization("crypto_btc", "0.20"),
                ),
            ),
            candidate(
                "stale-source-refresh-needed",
                market_ev="0.35",
                source_freshness_score="0.20",
                deadline_pressure_score="0.90",
                specializations=(specialization("crypto_btc", "0.80"),),
            ),
            candidate(
                "tiny-edge-market",
                market_ev="0.02",
                source_freshness_score="0.95",
                deadline_pressure_score="0.95",
                specializations=(specialization("crypto_btc", "0.90"),),
            ),
        ),
        team_backlogs=(
            team_state("crypto_btc", backlog_item_count="1"),
            team_state(
                "macro_rates",
                backlog_item_count="9",
                active_research_now_count="1",
                max_research_now_count="1",
            ),
        ),
        config=base_config(),
        generated_at=GENERATED_AT,
    )

    assert report.candidate_count == d("4")
    assert report.research_now_count == d("1")
    assert report.research_later_count == d("1")
    assert report.defer_count == d("1")
    assert report.drop_count == d("1")
    assert report.top_priority_score == d("1.6225")

    now_row = report.research_now[0]
    assert now_row.market_slug == "btc-fed-cut-hedge"
    assert now_row.owner_team == "crypto_btc"
    assert now_row.priority_score == d("1.6225")
    assert now_row.reason_codes == (
        "high_market_ev",
        "fresh_sources",
        "deadline_pressure",
        "team_specialization_fit",
        "team_backlog_capacity_available",
    )

    later_row = report.research_later[0]
    assert later_row.market_slug == "rates-dot-plot-review"
    assert later_row.owner_team == "macro_rates"
    assert later_row.priority_score == d("0.8925")
    assert "team_research_now_capacity_full" in later_row.reason_codes

    defer_row = report.defer[0]
    assert defer_row.market_slug == "stale-source-refresh-needed"
    assert defer_row.owner_team == "crypto_btc"
    assert defer_row.reason_codes == (
        "source_freshness_below_threshold",
        "defer_until_sources_refresh",
    )

    drop_row = report.drop[0]
    assert drop_row.market_slug == "tiny-edge-market"
    assert drop_row.owner_team == "crypto_btc"
    assert drop_row.reason_codes == (
        "market_ev_below_threshold",
        "drop_low_ev",
    )


def test_dataclasses_are_frozen_decimal_only_and_report_only() -> None:
    row = candidate(
        "btc-flow",
        market_ev="0.25",
        source_freshness_score="0.80",
        deadline_pressure_score="0.70",
        specializations=(specialization("crypto_btc", "0.90"),),
    )
    report = build_strategy_research_backlog_balancer_v5_report(
        (row,),
        team_backlogs=(team_state("crypto_btc", backlog_item_count="0"),),
        config=base_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.research_now[0].owner_team = "macro_rates"  # type: ignore[misc]

    with pytest.raises(ValueError, match="market_ev must be a Decimal"):
        StrategyResearchBacklogCandidateV5(
            market_slug="bad-float",
            question="Will bad-float resolve yes?",
            category_id="finance.crypto.btc",
            market_ev=0.25,  # type: ignore[arg-type]
            source_freshness_score=d("0.80"),
            deadline_pressure_score=d("0.70"),
            team_specializations=(specialization("crypto_btc", "0.90"),),
        )

    with pytest.raises(ValueError, match="paper_only"):
        build_strategy_research_backlog_balancer_v5_report(
            (row,),
            team_backlogs=(team_state("crypto_btc", backlog_item_count="0"),),
            config=replace(base_config(), paper_only=False),
            generated_at=GENERATED_AT,
        )


def test_payload_is_json_ready_and_rejects_live_surface_fields() -> None:
    report = build_strategy_research_backlog_balancer_v5_report(
        (
            candidate(
                "btc-flow",
                market_ev="0.25",
                source_freshness_score="0.80",
                deadline_pressure_score="0.70",
                specializations=(specialization("crypto_btc", "0.90"),),
            ),
        ),
        team_backlogs=(team_state("crypto_btc", backlog_item_count="0"),),
        config=base_config(),
        generated_at=GENERATED_AT,
    )

    payload = strategy_research_backlog_balancer_v5_payload(report)

    assert payload["paper_only"] is True
    assert payload["readonly"] is True
    assert payload["research_now"][0]["priority_score"] == "1.3800"
    assert_no_float_values(payload)

    with pytest.raises(ValueError, match="unsafe live surface field"):
        strategy_research_backlog_balancer_v5_payload(
            {
                "wallet_address": "0xabc",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_module_has_no_float_literals_or_live_integrations() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_research_backlog_balancer_v5.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    banned_modules = {"requests", "psycopg", "sqlalchemy", "web3", "py_clob_client"}
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module.split(".")[0])

    assert imported_modules.isdisjoint(banned_modules)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload contains float")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
