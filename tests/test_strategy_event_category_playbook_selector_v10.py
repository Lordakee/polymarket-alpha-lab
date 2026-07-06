from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

import polymarket_alpha_lab.strategy_event_category_playbook_selector_v10 as selector_module
from polymarket_alpha_lab.strategy_event_category_playbook_selector_v10 import (
    DEFAULT_STRATEGY_EVENT_CATEGORY_PLAYBOOK_SELECTOR_V10_CONFIG_VERSION,
    StrategyEventCategoryPlaybookSelectorV10Config,
    StrategyEventCategoryPlaybookSelectorV10Input,
    StrategyEventCategoryPlaybookSelectorV10Report,
    select_strategy_event_category_playbook_v10,
    strategy_event_category_playbook_selector_v10_payload,
)


def test_selects_politics_playbook_with_readonly_decimal_payload() -> None:
    report = select_strategy_event_category_playbook_v10(
        category="politics",
        subcategory="election",
        resolution_risk_tier="high",
        source_quorum_status="met",
        team_specialization_score=Decimal("0.820000"),
        time_to_resolution_minutes=Decimal("180"),
        historical_edge_score=Decimal("0.640000"),
        config=StrategyEventCategoryPlaybookSelectorV10Config(),
    )

    assert isinstance(report, StrategyEventCategoryPlaybookSelectorV10Report)
    assert report.config_version == (
        DEFAULT_STRATEGY_EVENT_CATEGORY_PLAYBOOK_SELECTOR_V10_CONFIG_VERSION
    )
    assert report.playbook_status == "ready"
    assert report.selected_playbook_id == "politics_election_resolution_playbook_v10"
    assert report.required_checks == (
        "official_resolution_source_check",
        "rule_text_alignment_check",
        "source_quorum_replay_check",
        "jurisdiction_timeline_check",
        "high_risk_adjudication_check",
    )
    assert report.reason_codes == (
        "strategy_event_category_playbook_selector_v10_category_politics",
        "strategy_event_category_playbook_selector_v10_subcategory_election",
        "strategy_event_category_playbook_selector_v10_high_resolution_risk",
        "strategy_event_category_playbook_selector_v10_source_quorum_met",
        "strategy_event_category_playbook_selector_v10_team_specialization_ready",
        "strategy_event_category_playbook_selector_v10_historical_edge_supported",
        "strategy_event_category_playbook_selector_v10_ready",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = strategy_event_category_playbook_selector_v10_payload(report)
    assert payload["playbook_status"] == "ready"
    assert payload["selected_playbook_id"] == "politics_election_resolution_playbook_v10"
    assert payload["team_specialization_score"] == "0.820000"
    assert payload["time_to_resolution_minutes"] == "180"
    assert payload["historical_edge_score"] == "0.640000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_blocks_crypto_playbook_when_source_conflict_and_weak_inputs() -> None:
    report = select_strategy_event_category_playbook_v10(
        category="crypto",
        subcategory="stablecoin",
        resolution_risk_tier="critical",
        source_quorum_status="conflict",
        team_specialization_score=Decimal("0.350000"),
        time_to_resolution_minutes=Decimal("20"),
        historical_edge_score=Decimal("0.120000"),
    )

    assert report.playbook_status == "blocked"
    assert report.selected_playbook_id == "crypto_stablecoin_depeg_playbook_v10"
    assert report.required_checks == (
        "primary_source_integrity_check",
        "cross_source_price_reference_check",
        "resolution_rule_specificity_check",
        "source_conflict_reconciliation_check",
        "critical_resolution_risk_check",
        "urgent_resolution_refresh_check",
        "team_specialist_handoff_check",
        "historical_edge_recheck",
    )
    assert report.reason_codes == (
        "strategy_event_category_playbook_selector_v10_category_crypto",
        "strategy_event_category_playbook_selector_v10_subcategory_stablecoin",
        "strategy_event_category_playbook_selector_v10_critical_resolution_risk",
        "strategy_event_category_playbook_selector_v10_source_quorum_conflict",
        "strategy_event_category_playbook_selector_v10_urgent_resolution_window",
        "strategy_event_category_playbook_selector_v10_team_specialization_weak",
        "strategy_event_category_playbook_selector_v10_historical_edge_weak",
        "strategy_event_category_playbook_selector_v10_blocked",
    )


def test_unknown_category_uses_general_review_playbook() -> None:
    report = select_strategy_event_category_playbook_v10(
        category="culture",
        subcategory=None,
        resolution_risk_tier="medium",
        source_quorum_status="partial",
        team_specialization_score=Decimal("0.610000"),
        time_to_resolution_minutes=Decimal("90"),
        historical_edge_score=Decimal("0.420000"),
    )

    assert report.playbook_status == "review_required"
    assert report.selected_playbook_id == "general_event_resolution_playbook_v10"
    assert report.required_checks == (
        "official_resolution_source_check",
        "secondary_source_consistency_check",
        "resolution_rule_specificity_check",
        "source_quorum_gap_check",
        "urgent_resolution_refresh_check",
    )
    assert report.reason_codes == (
        "strategy_event_category_playbook_selector_v10_category_general",
        "strategy_event_category_playbook_selector_v10_medium_resolution_risk",
        "strategy_event_category_playbook_selector_v10_source_quorum_partial",
        "strategy_event_category_playbook_selector_v10_urgent_resolution_window",
        "strategy_event_category_playbook_selector_v10_team_specialization_ready",
        "strategy_event_category_playbook_selector_v10_historical_edge_watch",
        "strategy_event_category_playbook_selector_v10_review_required",
    )


def test_inputs_are_decimal_typed_frozen_and_validated() -> None:
    selection_input = StrategyEventCategoryPlaybookSelectorV10Input(
        category="sports",
        subcategory="soccer",
        resolution_risk_tier="low",
        source_quorum_status="met",
        team_specialization_score=Decimal("0.750000"),
        time_to_resolution_minutes=Decimal("360"),
        historical_edge_score=Decimal("0.550000"),
    )

    with pytest.raises(FrozenInstanceError):
        selection_input.category = "crypto"  # type: ignore[misc]

    with pytest.raises(ValueError, match="team_specialization_score must be a Decimal"):
        StrategyEventCategoryPlaybookSelectorV10Input(
            category="sports",
            subcategory="soccer",
            resolution_risk_tier="low",
            source_quorum_status="met",
            team_specialization_score=0.75,  # type: ignore[arg-type]
            time_to_resolution_minutes=Decimal("360"),
            historical_edge_score=Decimal("0.550000"),
        )

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be a Decimal"):
        StrategyEventCategoryPlaybookSelectorV10Input(
            category="sports",
            subcategory="soccer",
            resolution_risk_tier="low",
            source_quorum_status="met",
            team_specialization_score=Decimal("0.750000"),
            time_to_resolution_minutes=360,  # type: ignore[arg-type]
            historical_edge_score=Decimal("0.550000"),
        )

    with pytest.raises(ValueError, match="source_quorum_status must be a known value"):
        StrategyEventCategoryPlaybookSelectorV10Input(
            category="sports",
            subcategory="soccer",
            resolution_risk_tier="low",
            source_quorum_status="missing",
            team_specialization_score=Decimal("0.750000"),
            time_to_resolution_minutes=Decimal("360"),
            historical_edge_score=Decimal("0.550000"),
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        StrategyEventCategoryPlaybookSelectorV10Config(readonly=False)


def test_public_contract_exposes_no_persistence_network_or_live_trading_surface() -> None:
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
        "trade",
        "live",
        "exchange_mutation",
        "path",
        "file",
        "db",
        "database",
        "dsn",
        "url",
        "http",
        "socket",
    )
    for cls in (
        StrategyEventCategoryPlaybookSelectorV10Config,
        StrategyEventCategoryPlaybookSelectorV10Input,
        StrategyEventCategoryPlaybookSelectorV10Report,
    ):
        for field in fields(cls):
            assert not any(fragment in field.name.lower() for fragment in unsafe_field_fragments)

    tree = ast.parse(selector_module.__loader__.get_source(selector_module.__name__) or "")
    forbidden_imports = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
    }
    forbidden_calls = {
        "open",
        "write_text",
        "write_bytes",
        "mkdir",
        "connect",
        "execute",
        "request",
        "get",
        "post",
    }
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
