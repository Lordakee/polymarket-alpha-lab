from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.research_team_expertise_gap_router import (
    ResearchTeamExpertiseGapInput,
    ResearchTeamExpertiseGapReport,
    ResearchTeamExpertiseGapRouterConfig,
    ResearchTeamExpertiseGapRouteRow,
    build_research_team_expertise_gap_report,
    research_team_expertise_gap_public_digest,
    research_team_expertise_gap_report_payload,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _input(
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    coverage_score: Decimal = Decimal("0.900000"),
    evidence_score: Decimal = Decimal("0.900000"),
    freshness_score: Decimal = Decimal("0.900000"),
    queue_priority_score: Decimal = Decimal("0.300000"),
    reason_codes: tuple[str, ...] = ("coverage_ok",),
) -> ResearchTeamExpertiseGapInput:
    return ResearchTeamExpertiseGapInput(
        raw_candidate_id="candidate-secret-123",
        market_id="market-secret-456",
        market_slug="bitcoin-secret-market",
        question="Will Bitcoin leak through public payload?",
        source_ref="https://example.invalid/private-source",
        source_text="private source text",
        team_id=team_id,
        category_id=category_id,
        coverage_score=coverage_score,
        evidence_score=evidence_score,
        freshness_score=freshness_score,
        queue_priority_score=queue_priority_score,
        reason_codes=reason_codes,
    )


def test_routes_domain_teams_to_collaborative_research_queue_without_raw_market_fields():
    report = build_research_team_expertise_gap_report(
        (
            _input(team_id="politics", category_id="politics"),
            _input(team_id="crypto_btc", category_id="finance.crypto.btc"),
            _input(team_id="crypto_eth", category_id="finance.crypto.eth"),
            _input(team_id="macro_rates", category_id="finance.macro.rates"),
            _input(team_id="commodities_gold", category_id="finance.commodities.gold"),
            _input(team_id="sports_soccer", category_id="sports.soccer"),
            _input(team_id="sports_basketball", category_id="sports.basketball"),
        ),
        config=ResearchTeamExpertiseGapRouterConfig(),
        generated_at=GENERATED_AT,
    )

    assert [row.collaborative_queue for row in report.rows] == [
        "collab-politics-research",
        "collab-crypto-research",
        "collab-crypto-research",
        "collab-macro-research",
        "collab-gold-research",
        "collab-football-research",
        "collab-basketball-research",
    ]
    assert {row.public_status for row in report.rows} == {"pass"}
    assert report.pass_count == Decimal("7")
    assert report.watch_count == Decimal("0")
    assert report.block_count == Decimal("0")
    assert report.public_status == "pass"

    payload_text = json.dumps(
        research_team_expertise_gap_report_payload(report),
        sort_keys=True,
    )
    for forbidden in (
        "candidate-secret-123",
        "market-secret-456",
        "bitcoin-secret-market",
        "Will Bitcoin",
        "example.invalid",
        "private source text",
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_text",
    ):
        assert forbidden not in payload_text

    with pytest.raises(FrozenInstanceError):
        report.rows[0].public_status = "watch"  # type: ignore[misc]


def test_public_status_thresholds_are_pass_watch_block_only():
    report = build_research_team_expertise_gap_report(
        (
            _input(
                team_id="politics",
                category_id="politics",
                coverage_score=Decimal("0.870000"),
                evidence_score=Decimal("0.860000"),
                freshness_score=Decimal("0.850000"),
                reason_codes=("coverage_complete",),
            ),
            _input(
                team_id="sports_soccer",
                category_id="sports.soccer",
                coverage_score=Decimal("0.600000"),
                evidence_score=Decimal("0.720000"),
                freshness_score=Decimal("0.760000"),
                queue_priority_score=Decimal("0.720000"),
                reason_codes=("lineup_depth_missing",),
            ),
            _input(
                team_id="commodities_gold",
                category_id="finance.commodities.gold",
                coverage_score=Decimal("0.300000"),
                evidence_score=Decimal("0.500000"),
                freshness_score=Decimal("0.550000"),
                queue_priority_score=Decimal("0.970000"),
                reason_codes=("real_rates_gap",),
            ),
        ),
        config=ResearchTeamExpertiseGapRouterConfig(),
        generated_at=GENERATED_AT,
    )

    assert [row.public_status for row in report.rows] == ["pass", "watch", "block"]
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")
    assert report.public_status == "block"
    assert report.rows[1].collaboration_required is True
    assert report.rows[2].collaboration_required is True
    assert set(report.reason_codes) >= {
        "coverage_complete",
        "lineup_depth_missing",
        "real_rates_gap",
        "expertise_gap_watch",
        "expertise_gap_block",
    }


def test_type_and_decimal_only_rejections():
    with pytest.raises(ValueError, match="coverage_score must be a Decimal"):
        _input(coverage_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="inputs must contain ResearchTeamExpertiseGapInput"):
        build_research_team_expertise_gap_report(
            (object(),),  # type: ignore[arg-type]
            config=ResearchTeamExpertiseGapRouterConfig(),
            generated_at=GENERATED_AT,
        )

    valid_row = ResearchTeamExpertiseGapRouteRow(
        category_id="politics",
        team_id="politics",
        collaborative_queue="collab-politics-research",
        public_status="pass",
        collaboration_required=False,
        coverage_score=Decimal("0.900000"),
        evidence_score=Decimal("0.900000"),
        freshness_score=Decimal("0.900000"),
        queue_priority_score=Decimal("0.200000"),
        expertise_gap_score=Decimal("0.100000"),
        reason_codes=("coverage_ok",),
    )

    with pytest.raises(ValueError, match="route_count must be a Decimal"):
        ResearchTeamExpertiseGapReport(
            generated_at=GENERATED_AT,
            config_version="research-team-expertise-gap-router-v0",
            route_count=1,  # type: ignore[arg-type]
            pass_count=Decimal("1"),
            watch_count=Decimal("0"),
            block_count=Decimal("0"),
            public_status="pass",
            rows=(valid_row,),
            reason_codes=("coverage_ok",),
        )


def test_public_payload_rejects_statuses_and_unsafe_public_surfaces():
    with pytest.raises(ValueError, match="public_status must be one of"):
        ResearchTeamExpertiseGapRouteRow(
            category_id="politics",
            team_id="politics",
            collaborative_queue="collab-politics-research",
            public_status="ready",  # type: ignore[arg-type]
            collaboration_required=False,
            coverage_score=Decimal("0.900000"),
            evidence_score=Decimal("0.900000"),
            freshness_score=Decimal("0.900000"),
            queue_priority_score=Decimal("0.200000"),
            expertise_gap_score=Decimal("0.100000"),
            reason_codes=("coverage_ok",),
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        ResearchTeamExpertiseGapRouteRow(
            category_id="politics",
            team_id="politics",
            collaborative_queue="collab-politics-research",
            public_status="watch",
            collaboration_required=True,
            coverage_score=Decimal("0.700000"),
            evidence_score=Decimal("0.800000"),
            freshness_score=Decimal("0.800000"),
            queue_priority_score=Decimal("0.600000"),
            expertise_gap_score=Decimal("0.300000"),
            reason_codes=("market_slug_leak",),
        )

    report = build_research_team_expertise_gap_report(
        (_input(),),
        config=ResearchTeamExpertiseGapRouterConfig(),
        generated_at=GENERATED_AT,
    )
    payload = research_team_expertise_gap_report_payload(report)
    payload["wallet_address"] = "0xunsafe"
    with pytest.raises(ValueError, match="unsafe public field"):
        research_team_expertise_gap_public_digest(payload)  # type: ignore[arg-type]


def test_payload_is_deterministic_decimal_string_only_and_digest_matches_report():
    inputs = (
        _input(
            team_id="sports_basketball",
            category_id="sports.basketball",
            coverage_score=Decimal("0.5555554"),
            evidence_score=Decimal("0.800000"),
            freshness_score=Decimal("0.700000"),
            queue_priority_score=Decimal("0.900000"),
            reason_codes=("injury_rotation_gap",),
        ),
        _input(
            team_id="macro_rates",
            category_id="finance.macro.rates",
            coverage_score=Decimal("0.620000"),
            evidence_score=Decimal("0.730000"),
            freshness_score=Decimal("0.740000"),
            queue_priority_score=Decimal("0.650000"),
            reason_codes=("data_surprise_gap",),
        ),
    )
    report_a = build_research_team_expertise_gap_report(
        tuple(reversed(inputs)),
        config=ResearchTeamExpertiseGapRouterConfig(),
        generated_at=GENERATED_AT,
    )
    report_b = build_research_team_expertise_gap_report(
        inputs,
        config=ResearchTeamExpertiseGapRouterConfig(),
        generated_at=GENERATED_AT,
    )

    payload_a = research_team_expertise_gap_report_payload(report_a)
    payload_b = research_team_expertise_gap_report_payload(report_b)
    assert payload_a == payload_b
    assert payload_a["derived_public_digest"] == report_a.derived_public_digest
    assert research_team_expertise_gap_public_digest(report_a) == report_a.derived_public_digest
    assert research_team_expertise_gap_public_digest(payload_a) == report_a.derived_public_digest
    assert report_a.rows[1].coverage_score == Decimal("0.555555")

    payload_text = json.dumps(payload_a, sort_keys=True)
    assert ".555555" in payload_text
    assert "0.5555554" not in payload_text
    assert not any(isinstance(value, float) for value in _walk_payload(payload_a))


def _walk_payload(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        nested: list[object] = [value]
        for item in value.values():
            nested.extend(_walk_payload(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = [value]
        for item in value:
            nested.extend(_walk_payload(item))
        return tuple(nested)
    return (value,)
