from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace

import pytest

import polymarket_alpha_lab.research_team_roster as roster_module
from polymarket_alpha_lab.research_team_roster import (
    DEFAULT_RESEARCH_TEAM_ROSTER_CONFIG_VERSION,
    RESEARCH_TEAM_ROSTER_ROLE_IDS,
    ResearchTeamRoster,
    ResearchTeamRosterConfig,
    ResearchTeamRosterEntry,
    ResearchTeamRosterRole,
    build_default_research_team_roster,
    research_team_roster_public_payload,
)
from polymarket_alpha_lab.strategy_team_taxonomy import STRATEGY_TEAM_IDS


def _role(role_id: str, *, status: str = "pass") -> ResearchTeamRosterRole:
    return ResearchTeamRosterRole(
        role_id=role_id,
        title=role_id.replace("_", " ").title(),
        status=status,
        responsibilities=(f"{role_id}_responsibility",),
        audit_outputs=(f"{role_id}_audit_output",),
        reason_codes=(f"{role_id}_{status}",),
    )


def _entry(
    team_id: str = "politics",
    *,
    roles: tuple[ResearchTeamRosterRole, ...] | None = None,
    status: str = "pass",
) -> ResearchTeamRosterEntry:
    return ResearchTeamRosterEntry(
        team_id=team_id,
        display_name="Politics Research Team",
        status=status,
        roles=roles
        or tuple(_role(role_id) for role_id in RESEARCH_TEAM_ROSTER_ROLE_IDS),
        reason_codes=("team_roster_complete",),
    )


def _roster(
    *,
    entries: tuple[ResearchTeamRosterEntry, ...] | None = None,
    status: str = "pass",
) -> ResearchTeamRoster:
    if entries is None:
        entries = tuple(_entry(team_id) for team_id in STRATEGY_TEAM_IDS)
    return ResearchTeamRoster(
        config_version=DEFAULT_RESEARCH_TEAM_ROSTER_CONFIG_VERSION,
        status=status,
        team_count=len(entries),
        role_count=sum(len(entry.roles) for entry in entries),
        entries=entries,
        reason_codes=("research_team_roster_complete",),
    )


def test_default_roster_defines_medium_research_team_roles_for_each_domain_team() -> None:
    roster = build_default_research_team_roster(config=ResearchTeamRosterConfig())

    assert isinstance(roster, ResearchTeamRoster)
    assert roster.config_version == DEFAULT_RESEARCH_TEAM_ROSTER_CONFIG_VERSION
    assert roster.status == "pass"
    assert roster.team_count == len(STRATEGY_TEAM_IDS)
    assert roster.role_count == len(STRATEGY_TEAM_IDS) * len(
        RESEARCH_TEAM_ROSTER_ROLE_IDS,
    )
    assert tuple(entry.team_id for entry in roster.entries) == STRATEGY_TEAM_IDS
    assert roster.paper_only is True
    assert roster.report_only is True
    assert roster.readonly is True

    for entry in roster.entries:
        assert entry.status == "pass"
        assert tuple(role.role_id for role in entry.roles) == RESEARCH_TEAM_ROSTER_ROLE_IDS
        assert all(role.status == "pass" for role in entry.roles)
        assert all(role.paper_only is True for role in entry.roles)
        assert all(role.report_only is True for role in entry.roles)
        assert all(role.readonly is True for role in entry.roles)

    politics = roster.entries[0]
    by_role = {role.role_id: role for role in politics.roles}
    assert by_role["lead"].title == "Research Lead"
    assert "coordinate_domain_research_review" in by_role["lead"].responsibilities
    assert by_role["evidence_scout"].title == "Evidence Scout"
    assert "collect_public_evidence" in by_role[
        "evidence_scout"
    ].responsibilities
    assert by_role["probability_analyst"].title == "Probability Analyst"
    assert "calibrate_probability_range" in by_role[
        "probability_analyst"
    ].responsibilities
    assert by_role["risk_reviewer"].title == "Risk Reviewer"
    assert "surface_resolution_and_data_risks" in by_role[
        "risk_reviewer"
    ].responsibilities
    assert by_role["memory_curator"].title == "Memory Curator"
    assert "maintain_non_persistent_research_memory" in by_role[
        "memory_curator"
    ].responsibilities


def test_role_coverage_gap_downgrades_entry_to_watch_and_roster_to_watch() -> None:
    missing_memory_curator = tuple(
        _role(role_id)
        for role_id in RESEARCH_TEAM_ROSTER_ROLE_IDS
        if role_id != "memory_curator"
    )
    entry = _entry(roles=missing_memory_curator, status="watch")
    other_entries = tuple(_entry(team_id) for team_id in STRATEGY_TEAM_IDS[1:])

    roster = _roster(entries=(entry,) + other_entries, status="watch")

    assert roster.status == "watch"
    assert roster.entries[0].status == "watch"
    assert roster.entries[0].reason_codes == (
        "missing_required_role_memory_curator",
    )


def test_blocked_role_status_blocks_entry_and_roster() -> None:
    roles = tuple(
        _role(role_id, status="block" if role_id == "risk_reviewer" else "pass")
        for role_id in RESEARCH_TEAM_ROSTER_ROLE_IDS
    )
    entry = _entry(roles=roles, status="block")
    other_entries = tuple(_entry(team_id) for team_id in STRATEGY_TEAM_IDS[1:])

    roster = _roster(entries=(entry,) + other_entries, status="block")

    assert roster.status == "block"
    assert roster.entries[0].status == "block"
    assert "role_blocked_risk_reviewer" in roster.entries[0].reason_codes


def test_config_roles_entries_and_roster_are_frozen_and_strictly_typed() -> None:
    role = _role("lead")
    entry = _entry()
    roster = _roster()

    with pytest.raises(FrozenInstanceError):
        role.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        entry.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        roster.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        ResearchTeamRosterConfig().config_version = "other"  # type: ignore[misc]

    with pytest.raises(ValueError, match="status"):
        replace(role, status="ready")
    with pytest.raises(ValueError, match="role_id"):
        replace(role, role_id="trader")
    with pytest.raises(ValueError, match="responsibilities"):
        replace(role, responsibilities=["coordinate"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="team_id"):
        replace(entry, team_id="weather")
    with pytest.raises(ValueError, match="roles"):
        replace(entry, roles=[role])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="entries"):
        replace(roster, entries=[entry])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(ResearchTeamRosterConfig(), paper_only=False)


def test_public_payload_rejects_sensitive_keys_and_values() -> None:
    roster = _roster()
    payload = research_team_roster_public_payload(roster)

    assert payload == research_team_roster_public_payload(roster)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["status"] == "pass"

    serialized = repr(payload).casefold()
    forbidden_text = (
        "candidate",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "notional",
        "buy",
        "sell",
        "recommend",
    )
    assert not any(term in serialized for term in forbidden_text)

    for unsafe_payload in (
        {"paper_only": True, "report_only": True, "readonly": True, "market_slug": "x"},
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "note": "buy yes",
        },
        {"paper_only": True, "report_only": False, "readonly": True},
    ):
        with pytest.raises(ValueError):
            research_team_roster_public_payload(unsafe_payload)


def test_module_has_hard_flags_and_no_network_database_or_trading_surface() -> None:
    for cls in (
        ResearchTeamRosterConfig,
        ResearchTeamRosterRole,
        ResearchTeamRosterEntry,
        ResearchTeamRoster,
    ):
        field_names = {field.name for field in fields(cls)}
        assert {"paper_only", "report_only", "readonly"}.issubset(field_names)
        assert not {
            "candidate_id",
            "market_id",
            "market_slug",
            "question",
            "source_ref",
            "source_url",
            "source_text",
            "dsn",
            "table",
            "token",
            "wallet",
            "auth",
            "order",
            "trade",
            "position",
        }.intersection(field_names)

    tree = ast.parse(roster_module.__loader__.get_source(roster_module.__name__) or "")
    forbidden_imports = {
        "httpx",
        "requests",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "py_clob_client",
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
        "put",
        "delete",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not forbidden_imports.intersection(
                alias.name.split(".")[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls


def test_roster_output_is_deterministic() -> None:
    first = build_default_research_team_roster(config=ResearchTeamRosterConfig())
    second = build_default_research_team_roster(config=ResearchTeamRosterConfig())

    assert first == second
    assert research_team_roster_public_payload(first) == research_team_roster_public_payload(
        second,
    )
