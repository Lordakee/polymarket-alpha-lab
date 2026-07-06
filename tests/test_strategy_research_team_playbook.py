from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields

import pytest

import polymarket_alpha_lab.strategy_research_team_playbook as playbook_module
from polymarket_alpha_lab.strategy_research_team_playbook import (
    DEFAULT_STRATEGY_RESEARCH_TEAM_PLAYBOOK_CONFIG_VERSION,
    StrategyResearchTeamPlaybook,
    StrategyResearchTeamPlaybookConfig,
    StrategyResearchTeamPlaybookEntry,
    build_default_strategy_research_team_playbook,
    get_strategy_research_team_playbook_entry,
)
from polymarket_alpha_lab.strategy_team_taxonomy import STRATEGY_TEAM_IDS


def test_default_playbook_defines_readonly_source_contracts_for_strategy_teams() -> None:
    playbook = build_default_strategy_research_team_playbook(
        config=StrategyResearchTeamPlaybookConfig(),
    )

    assert isinstance(playbook, StrategyResearchTeamPlaybook)
    assert playbook.config_version == DEFAULT_STRATEGY_RESEARCH_TEAM_PLAYBOOK_CONFIG_VERSION
    assert playbook.team_count == len(STRATEGY_TEAM_IDS)
    assert tuple(entry.team_id for entry in playbook.entries) == STRATEGY_TEAM_IDS
    assert all(entry.paper_only is True for entry in playbook.entries)
    assert all(entry.report_only is True for entry in playbook.entries)
    assert all(entry.readonly is True for entry in playbook.entries)
    assert playbook.paper_only is True
    assert playbook.report_only is True
    assert playbook.readonly is True

    by_team = {entry.team_id: entry for entry in playbook.entries}
    assert by_team["politics"].required_sources == (
        "official_election_or_government_source",
        "credible_polling_aggregator",
        "campaign_or_court_record",
        "major_news_wire",
    )
    assert by_team["politics"].refresh_cadence_minutes == 60
    assert by_team["politics"].minimum_evidence_count == 4
    assert "polling_error_or_late_swing" in by_team["politics"].key_failure_modes

    assert by_team["crypto_btc"].required_sources == (
        "btc_spot_reference_price",
        "crypto_derivatives_market_data",
        "etf_flow_or_onchain_source",
        "credible_crypto_news_wire",
    )
    assert by_team["crypto_btc"].refresh_cadence_minutes == 15
    assert by_team["crypto_btc"].minimum_evidence_count == 4
    assert "exchange_outage_or_bad_tick" in by_team["crypto_btc"].key_failure_modes

    assert by_team["equity_index"].required_sources == (
        "index_provider_or_exchange_reference",
        "futures_or_options_market_data",
        "macro_calendar_source",
        "market_news_wire",
    )
    assert by_team["equity_index"].refresh_cadence_minutes == 30
    assert by_team["equity_index"].minimum_evidence_count == 4

    assert by_team["commodities_gold"].required_sources == (
        "spot_or_futures_price_reference",
        "real_yield_or_rates_source",
        "central_bank_or_etf_flow_source",
        "macro_calendar_source",
    )
    assert by_team["commodities_gold"].refresh_cadence_minutes == 60
    assert by_team["commodities_gold"].minimum_evidence_count == 4

    assert by_team["soccer"].required_sources == (
        "official_competition_fixture_source",
        "team_lineup_or_injury_source",
        "odds_or_market_price_source",
        "credible_local_sports_news",
    )
    assert by_team["soccer"].refresh_cadence_minutes == 30
    assert by_team["soccer"].minimum_evidence_count == 4

    assert by_team["basketball"].required_sources == (
        "official_league_injury_report",
        "team_depth_chart_or_rotation_source",
        "odds_or_market_price_source",
        "beat_reporter_or_local_news",
    )
    assert by_team["basketball"].refresh_cadence_minutes == 30
    assert by_team["basketball"].minimum_evidence_count == 4


def test_lookup_returns_single_frozen_entry_without_mutating_global_contract() -> None:
    crypto_entry = get_strategy_research_team_playbook_entry("crypto_btc")
    second_crypto_entry = get_strategy_research_team_playbook_entry("crypto_btc")

    assert crypto_entry == second_crypto_entry
    assert crypto_entry is not second_crypto_entry
    assert crypto_entry.team_id == "crypto_btc"

    with pytest.raises(FrozenInstanceError):
        crypto_entry.refresh_cadence_minutes = 5  # type: ignore[misc]

    with pytest.raises(ValueError, match="team_id must be a known strategy team"):
        get_strategy_research_team_playbook_entry("weather")


def test_playbook_entries_are_strictly_typed_and_nonempty() -> None:
    with pytest.raises(ValueError, match="required_sources must be a tuple"):
        StrategyResearchTeamPlaybookEntry(
            team_id="politics",
            required_sources=["official_source"],  # type: ignore[arg-type]
            refresh_cadence_minutes=60,
            key_failure_modes=("ambiguous_resolution",),
            minimum_evidence_count=1,
        )

    with pytest.raises(ValueError, match="refresh_cadence_minutes must be a positive int"):
        StrategyResearchTeamPlaybookEntry(
            team_id="politics",
            required_sources=("official_source",),
            refresh_cadence_minutes=0,
            key_failure_modes=("ambiguous_resolution",),
            minimum_evidence_count=1,
        )

    with pytest.raises(ValueError, match="key_failure_modes must be nonempty"):
        StrategyResearchTeamPlaybookEntry(
            team_id="politics",
            required_sources=("official_source",),
            refresh_cadence_minutes=60,
            key_failure_modes=(),
            minimum_evidence_count=1,
        )

    with pytest.raises(ValueError, match="minimum_evidence_count must be a positive int"):
        StrategyResearchTeamPlaybookEntry(
            team_id="politics",
            required_sources=("official_source",),
            refresh_cadence_minutes=60,
            key_failure_modes=("ambiguous_resolution",),
            minimum_evidence_count=False,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        StrategyResearchTeamPlaybookConfig(readonly=False)


def test_public_contract_exposes_no_persistence_or_live_trading_surface() -> None:
    unsafe_field_fragments = (
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
        "path",
        "file",
        "db",
        "database",
        "dsn",
    )
    for cls in (
        StrategyResearchTeamPlaybookConfig,
        StrategyResearchTeamPlaybookEntry,
        StrategyResearchTeamPlaybook,
    ):
        for field in fields(cls):
            assert not any(fragment in field.name.lower() for fragment in unsafe_field_fragments)

    tree = ast.parse(playbook_module.__loader__.get_source(playbook_module.__name__) or "")
    forbidden_imports = {"sqlite3", "psycopg", "sqlalchemy", "supabase"}
    forbidden_calls = {"open", "write_text", "write_bytes", "mkdir", "connect", "execute"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not forbidden_imports.intersection(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
