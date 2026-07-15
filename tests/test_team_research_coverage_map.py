from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
import inspect

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def _api():
    return import_module("polymarket_alpha_lab.team_research_coverage_map")


def _config(**overrides):
    values = {"config_version": "team-research-coverage-map-v0"}
    values.update(overrides)
    return _api().TeamResearchCoverageMapConfig(**values)


def _coverage_map(*observations, **config_overrides):
    return _api().build_team_research_coverage_map(
        observations,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _observation(
    research_domain: str,
    source_family: str,
    team_id: str,
    evidence_status: str,
    public_identifier: str,
):
    return _api().TeamResearchCoverageMapObservation(
        research_domain=research_domain,
        source_family=source_family,
        team_id=team_id,
        evidence_status=evidence_status,
        public_identifier=public_identifier,
    )


def test_coverage_map_summarizes_domains_sources_teams_and_evidence_with_redactions() -> None:
    api = _api()
    report = _coverage_map(
        _observation(
            "politics",
            "resolution_rules",
            "politics",
            "covered",
            "politics-private-source-id",
        ),
        _observation(
            "finance",
            "official_api",
            "crypto_btc",
            "gap",
            "btc-private-source-id",
        ),
        _observation(
            "finance",
            "official_api",
            "crypto_btc",
            "covered",
            "btc-private-source-id-2",
        ),
        _observation(
            "sports",
            "injury_reporting",
            "sports_soccer",
            "watch",
            "soccer-private-source-id",
        ),
        _observation(
            "general",
            "research_ops",
            "general_research",
            "blocked",
            "ops-private-source-id",
        ),
    )
    payload = api.team_research_coverage_map_payload(report)
    rendered_report = repr(report)
    rendered_payload = repr(payload)

    assert report.coverage_status == "blocked"
    assert report.reason_codes == (
        "blocked_evidence_present",
        "evidence_gaps_present",
        "watch_evidence_present",
    )
    assert report.observation_count == 5
    assert report.covered_observation_count == 2
    assert report.watch_observation_count == 1
    assert report.gap_observation_count == 1
    assert report.blocked_observation_count == 1
    assert report.covered_observation_pct == Decimal("40.000000")
    assert report.domain_summaries == (
        api.TeamResearchCoverageMapSummary(
            dimension="research_domain",
            value="finance",
            observation_count=2,
            observation_pct=Decimal("40.000000"),
        ),
        api.TeamResearchCoverageMapSummary(
            dimension="research_domain",
            value="general",
            observation_count=1,
            observation_pct=Decimal("20.000000"),
        ),
        api.TeamResearchCoverageMapSummary(
            dimension="research_domain",
            value="politics",
            observation_count=1,
            observation_pct=Decimal("20.000000"),
        ),
        api.TeamResearchCoverageMapSummary(
            dimension="research_domain",
            value="sports",
            observation_count=1,
            observation_pct=Decimal("20.000000"),
        ),
    )
    assert tuple((row.value, row.observation_count) for row in report.source_family_summaries) == (
        ("injury_reporting", 1),
        ("official_api", 2),
        ("research_ops", 1),
        ("resolution_rules", 1),
    )
    assert tuple((row.value, row.observation_count) for row in report.team_summaries) == (
        ("crypto_btc", 2),
        ("general_research", 1),
        ("politics", 1),
        ("sports_soccer", 1),
    )
    assert tuple((row.value, row.observation_count) for row in report.evidence_status_summaries) == (
        ("blocked", 1),
        ("covered", 2),
        ("gap", 1),
        ("watch", 1),
    )
    assert tuple(
        (row.research_domain, row.source_family, row.team_id, row.evidence_status)
        for row in report.coverage_rows
    ) == (
        ("finance", "official_api", "crypto_btc", "covered"),
        ("finance", "official_api", "crypto_btc", "gap"),
        ("general", "research_ops", "general_research", "blocked"),
        ("politics", "resolution_rules", "politics", "covered"),
        ("sports", "injury_reporting", "sports_soccer", "watch"),
    )
    assert report.team_evidence_summaries == (
        api.TeamResearchCoverageMapTeamEvidenceSummary(
            team_id="crypto_btc",
            observation_count=2,
            covered_observation_count=1,
            watch_observation_count=0,
            gap_observation_count=1,
            blocked_observation_count=0,
            covered_observation_pct=Decimal("50.000000"),
        ),
        api.TeamResearchCoverageMapTeamEvidenceSummary(
            team_id="general_research",
            observation_count=1,
            covered_observation_count=0,
            watch_observation_count=0,
            gap_observation_count=0,
            blocked_observation_count=1,
            covered_observation_pct=Decimal("0.000000"),
        ),
        api.TeamResearchCoverageMapTeamEvidenceSummary(
            team_id="politics",
            observation_count=1,
            covered_observation_count=1,
            watch_observation_count=0,
            gap_observation_count=0,
            blocked_observation_count=0,
            covered_observation_pct=Decimal("100.000000"),
        ),
        api.TeamResearchCoverageMapTeamEvidenceSummary(
            team_id="sports_soccer",
            observation_count=1,
            covered_observation_count=0,
            watch_observation_count=1,
            gap_observation_count=0,
            blocked_observation_count=0,
            covered_observation_pct=Decimal("0.000000"),
        ),
    )
    assert all(
        redacted.startswith("public_id_sha256:")
        for row in report.coverage_rows
        for redacted in row.redacted_public_identifiers
    )
    assert payload["domain_summaries"][0]["observation_pct"] == "40.000000"
    assert payload["coverage_rows"][0]["observation_pct"] == "20.000000"
    assert payload["team_evidence_summaries"][0]["covered_observation_pct"] == "50.000000"
    assert "politics-private-source-id" not in rendered_report
    assert "btc-private-source-id" not in rendered_report
    assert "soccer-private-source-id" not in rendered_payload
    assert "ops-private-source-id" not in rendered_payload
    assert "public_identifier" not in rendered_payload
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_coverage_map_handles_empty_and_safe_coverage_deterministically() -> None:
    api = _api()
    empty = _coverage_map()
    safe = _coverage_map(
        _observation("sports", "official_api", "sports_other", "covered", "sports-2"),
        _observation("sports", "official_api", "sports_other", "covered", "sports-1"),
        _observation("finance", "official_api", "macro_rates", "covered", "macro-1"),
    )

    assert empty.coverage_status == "blocked"
    assert empty.reason_codes == ("empty_coverage_map",)
    assert empty.observation_count == 0
    assert empty.covered_observation_pct is None
    assert empty.team_evidence_summaries == ()
    assert empty.coverage_rows == ()
    assert empty.domain_summaries == ()

    assert safe.coverage_status == "safe"
    assert safe.reason_codes == ("coverage_map_safe",)
    assert safe.covered_observation_count == 3
    assert safe.covered_observation_pct == Decimal("100.000000")
    assert tuple(row.value for row in safe.domain_summaries) == ("finance", "sports")
    assert tuple(
        (
            row.research_domain,
            row.source_family,
            row.team_id,
            row.evidence_status,
            row.observation_count,
            row.redacted_public_identifiers,
        )
        for row in safe.coverage_rows
    ) == (
        (
            "finance",
            "official_api",
            "macro_rates",
            "covered",
            1,
            (api.redact_team_research_coverage_map_identifier("macro-1"),),
        ),
        (
            "sports",
            "official_api",
            "sports_other",
            "covered",
            2,
            (
                api.redact_team_research_coverage_map_identifier("sports-1"),
                api.redact_team_research_coverage_map_identifier("sports-2"),
            ),
        ),
    )


def test_coverage_map_rejects_wrong_inputs_false_flags_and_non_utc_times() -> None:
    api = _api()

    with pytest.raises(ValueError, match="TeamResearchCoverageMapConfig"):
        api.build_team_research_coverage_map((), config=object(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="TeamResearchCoverageMapObservation"):
        api.build_team_research_coverage_map((object(),), config=_config(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="paper_only"):
        api.TeamResearchCoverageMapConfig(paper_only=False)
    naive_report = api.build_team_research_coverage_map(
        (),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 12, 0),
    )
    assert naive_report.generated_at == GENERATED_AT
    assert naive_report.generated_at.tzinfo is UTC
    with pytest.raises(ValueError, match="research_domain"):
        _observation("crypto", "official_api", "crypto_btc", "covered", "btc-1")
    with pytest.raises(ValueError, match="evidence_status"):
        _observation("finance", "official_api", "crypto_btc", "ready_to_act", "btc-1")
    with pytest.raises(ValueError, match="canonical"):
        _observation("finance", " official_api", "crypto_btc", "covered", "btc-1")


def test_coverage_map_dataclasses_are_frozen_and_consistent() -> None:
    api = _api()
    row = api.TeamResearchCoverageMapRow(
        research_domain="finance",
        source_family="official_api",
        team_id="crypto_btc",
        evidence_status="covered",
        observation_count=2,
        total_observation_count=4,
        redacted_public_identifiers=(
            api.redact_team_research_coverage_map_identifier("btc-1"),
            api.redact_team_research_coverage_map_identifier("btc-2"),
        ),
    )

    assert row.observation_pct == Decimal("50.000000")
    with pytest.raises(FrozenInstanceError):
        row.team_id = "crypto_eth"
    with pytest.raises(ValueError, match="redacted_public_identifiers"):
        replace(row, redacted_public_identifiers=("btc-1",))
    with pytest.raises(ValueError, match="redacted_public_identifiers"):
        replace(
            row,
            redacted_public_identifiers=(
                api.redact_team_research_coverage_map_identifier("btc-1"),
                api.redact_team_research_coverage_map_identifier("btc-1"),
            ),
        )
    with pytest.raises(ValueError, match="observation_count"):
        replace(row, observation_count=5)
    with pytest.raises(ValueError, match="deterministic"):
        api.TeamResearchCoverageMapReport(
            generated_at=GENERATED_AT,
            config_version="team-research-coverage-map-v0",
            coverage_status="safe",
            observation_count=2,
            domain_summaries=(),
            source_family_summaries=(),
            team_summaries=(),
            evidence_status_summaries=(),
            coverage_rows=(
                row,
                replace(row, research_domain="finance", source_family="alternative_source"),
            ),
            reason_codes=("coverage_map_safe",),
        )


def test_coverage_map_imports_no_db_cli_network_or_filesystem_modules(monkeypatch) -> None:
    import builtins
    import sys
    from types import ModuleType
    from typing import Any

    disallowed_import_roots = {
        "asyncpg",
        "dotenv",
        "os",
        "pathlib",
        "polymarket_alpha_lab.cli",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
    }
    imported_names: list[str] = []
    original_import = builtins.__import__

    def tracking_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> ModuleType:
        if level == 0:
            imported_names.append(name)
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", tracking_import)
    sys.modules.pop("polymarket_alpha_lab.team_research_coverage_map", None)

    import_module("polymarket_alpha_lab.team_research_coverage_map")

    imported_roots = {name.partition(".")[0] for name in imported_names}
    assert imported_roots.isdisjoint(disallowed_import_roots)
    assert "polymarket_alpha_lab.cli" not in imported_names


def test_coverage_map_public_api_has_no_execution_ranking_or_advice_terms() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api)

    assert all("market_slug" not in name for name in public_names)
    assert all("question" not in name for name in public_names)
    assert all("rank" not in name for name in public_names)
    assert "recommended_next_step" not in source
    assert "investment" not in source
    assert "place_order" not in source
    assert "submit_order" not in source
    assert "position" not in source
