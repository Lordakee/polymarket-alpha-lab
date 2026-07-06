from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_team_signal_triage_matrix_v2 import (
    MarketResearchTeamSignalTriageMatrixV2Config,
    MarketResearchTeamSignalTriageMatrixV2Row,
    build_market_research_team_signal_triage_matrix_v2,
    lookup_market_research_team_signal_triage_matrix_v2,
    market_research_team_signal_triage_matrix_v2_payload,
)
from polymarket_alpha_lab.team_taxonomy import TEAM_CATEGORIES


def _row(
    *,
    market_category: str = "politics",
    event_archetype: str = "court_or_policy_stay",
    specialist_team_ids: tuple[str, ...] = ("macro_rates", "politics"),
    required_source_families: tuple[str, ...] = (
        "primary_news_reporting",
        "court_docket",
        "agency_statement",
    ),
    minimum_evidence_count: Decimal = Decimal("3.000000"),
    escalation_tags: tuple[str, ...] = (
        "time_sensitive",
        "resolution_rule_risk",
        "cross_team_review",
    ),
) -> MarketResearchTeamSignalTriageMatrixV2Row:
    return MarketResearchTeamSignalTriageMatrixV2Row(
        market_category=market_category,
        event_archetype=event_archetype,
        specialist_team_ids=specialist_team_ids,
        required_source_families=required_source_families,
        minimum_evidence_count=minimum_evidence_count,
        escalation_tags=escalation_tags,
    )


def test_default_matrix_covers_categories_and_maps_crypto_shock() -> None:
    matrix = build_market_research_team_signal_triage_matrix_v2()
    payload = market_research_team_signal_triage_matrix_v2_payload(matrix)
    crypto_row = lookup_market_research_team_signal_triage_matrix_v2(
        "finance.crypto.btc",
        "etf_flow_or_onchain_shock",
    )

    assert matrix.row_count == Decimal("20.000000")
    assert matrix.category_count == Decimal("10.000000")
    assert {row.market_category for row in matrix.rows} == set(TEAM_CATEGORIES)
    assert [(row.market_category, row.event_archetype) for row in matrix.rows] == sorted(
        (row.market_category, row.event_archetype) for row in matrix.rows
    )
    assert crypto_row.specialist_team_ids == ("crypto_btc",)
    assert crypto_row.required_source_families == (
        "exchange_market_data",
        "fund_flow",
        "onchain_analytics",
    )
    assert crypto_row.minimum_evidence_count == Decimal("3.000000")
    assert crypto_row.escalation_tags == (
        "liquidity_dislocation",
        "market_microstructure_review",
    )
    assert payload["row_count"] == "20.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_custom_config_normalizes_rows_and_tuple_sequences_deterministically() -> None:
    basketball_row = _row(
        market_category="sports.basketball",
        event_archetype="schedule_fatigue_spot",
        specialist_team_ids=("sports_basketball",),
        required_source_families=(
            "team_statement",
            "odds_consensus",
            "league_statement",
        ),
        escalation_tags=("time_sensitive", "market_microstructure_review"),
    )
    politics_row = _row()
    config = MarketResearchTeamSignalTriageMatrixV2Config(
        rule_rows=(basketball_row, politics_row),
    )

    matrix = build_market_research_team_signal_triage_matrix_v2(config=config)

    assert [(row.market_category, row.event_archetype) for row in matrix.rows] == [
        ("politics", "court_or_policy_stay"),
        ("sports.basketball", "schedule_fatigue_spot"),
    ]
    assert matrix.rows[0].specialist_team_ids == ("politics", "macro_rates")
    assert matrix.rows[0].required_source_families == (
        "agency_statement",
        "court_docket",
        "primary_news_reporting",
    )
    assert matrix.rows[0].escalation_tags == (
        "cross_team_review",
        "resolution_rule_risk",
        "time_sensitive",
    )
    assert matrix.rows[1].required_source_families == (
        "league_statement",
        "odds_consensus",
        "team_statement",
    )


def test_rows_are_frozen_and_reject_bad_flags_primary_team_and_counts() -> None:
    row = _row()

    with pytest.raises(FrozenInstanceError):
        row.minimum_evidence_count = Decimal("4.000000")
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="primary team"):
        replace(
            row,
            market_category="finance.crypto.btc",
            specialist_team_ids=("crypto_eth",),
        )
    with pytest.raises(ValueError, match="cover all required source families"):
        replace(row, minimum_evidence_count=Decimal("2.000000"))
    with pytest.raises(ValueError, match="Decimal"):
        replace(row, minimum_evidence_count=3)
    with pytest.raises(ValueError, match="whole count"):
        replace(row, minimum_evidence_count=Decimal("3.500000"))


def test_payload_rejects_float_values_and_bad_report_flags() -> None:
    matrix = build_market_research_team_signal_triage_matrix_v2()
    payload = market_research_team_signal_triage_matrix_v2_payload(matrix)

    float_payload = dict(payload)
    float_payload["row_count"] = 20.0
    with pytest.raises(ValueError, match="float"):
        market_research_team_signal_triage_matrix_v2_payload(float_payload)

    bad_flag_payload = dict(payload)
    bad_flag_payload["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        market_research_team_signal_triage_matrix_v2_payload(bad_flag_payload)


def test_lookup_and_config_reject_unknown_or_inconsistent_inputs() -> None:
    with pytest.raises(ValueError, match="triage rule not found"):
        lookup_market_research_team_signal_triage_matrix_v2(
            "sports.other",
            "court_or_policy_stay",
        )
    with pytest.raises(ValueError, match="event_archetype"):
        lookup_market_research_team_signal_triage_matrix_v2(
            "politics",
            "unknown_event",
        )
    with pytest.raises(ValueError, match="config"):
        build_market_research_team_signal_triage_matrix_v2(config=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unique"):
        MarketResearchTeamSignalTriageMatrixV2Config(rule_rows=(_row(), _row()))
