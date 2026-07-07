from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace

import pytest

from polymarket_alpha_lab.research_team_domain_playbook import (
    DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_CONFIG_VERSION,
    PUBLIC_PLAYBOOK_STATUSES,
    REQUIRED_RESEARCH_TEAM_DOMAIN_IDS,
    ResearchTeamDomainPlaybook,
    ResearchTeamDomainPlaybookConfig,
    ResearchTeamDomainPlaybookReport,
    ResearchTeamDomainPlaybookStep,
    ResearchTeamDomainRiskCheck,
    build_default_research_team_domain_playbook_report,
    build_research_team_domain_playbook,
    research_team_domain_playbook_public_payload,
)


def _step(step_id: str = "scope_public_event", *, status: str = "pass") -> ResearchTeamDomainPlaybookStep:
    return ResearchTeamDomainPlaybookStep(
        step_id=step_id,
        description=f"{step_id}_description",
        public_status=status,
        reason_codes=(f"{step_id}_{status}",),
    )


def _risk(check_id: str = "resolution_rule_clarity", *, status: str = "pass") -> ResearchTeamDomainRiskCheck:
    return ResearchTeamDomainRiskCheck(
        check_id=check_id,
        description=f"{check_id}_description",
        public_status=status,
        reason_codes=(f"{check_id}_{status}",),
    )


def _playbook(domain_id: str = "politics", *, public_status: str = "pass") -> ResearchTeamDomainPlaybook:
    return ResearchTeamDomainPlaybook(
        domain_id=domain_id,
        team_name="Politics Research Team",
        public_status=public_status,
        research_steps=(
            _step("scope_public_event"),
            _step("collect_public_evidence"),
            _step("summarize_scenario_drivers"),
        ),
        risk_checks=(
            _risk("resolution_rule_clarity"),
            _risk("evidence_freshness"),
            _risk("no_execution_language"),
        ),
        reason_codes=("domain_playbook_complete",),
    )


def _report(
    *,
    playbooks: tuple[ResearchTeamDomainPlaybook, ...] | None = None,
    public_status: str = "pass",
) -> ResearchTeamDomainPlaybookReport:
    if playbooks is None:
        playbooks = tuple(build_research_team_domain_playbook(domain_id) for domain_id in REQUIRED_RESEARCH_TEAM_DOMAIN_IDS)
    return ResearchTeamDomainPlaybookReport(
        config_version=DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_CONFIG_VERSION,
        public_status=public_status,
        domain_count=len(playbooks),
        playbooks=playbooks,
        reason_codes=("research_team_domain_playbook_complete",),
    )


def test_default_playbook_covers_required_research_domain_teams() -> None:
    report = build_default_research_team_domain_playbook_report(config=ResearchTeamDomainPlaybookConfig())

    assert report.config_version == DEFAULT_RESEARCH_TEAM_DOMAIN_PLAYBOOK_CONFIG_VERSION
    assert REQUIRED_RESEARCH_TEAM_DOMAIN_IDS == (
        "politics",
        "macro",
        "crypto",
        "equity_index",
        "gold",
        "soccer",
        "basketball",
    )
    assert PUBLIC_PLAYBOOK_STATUSES == ("pass", "watch", "block")
    assert report.public_status == "pass"
    assert report.domain_count == len(REQUIRED_RESEARCH_TEAM_DOMAIN_IDS)
    assert tuple(playbook.domain_id for playbook in report.playbooks) == REQUIRED_RESEARCH_TEAM_DOMAIN_IDS
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    by_domain = {playbook.domain_id: playbook for playbook in report.playbooks}
    assert by_domain["politics"].team_name == "Politics Research Team"
    assert "compare_polling_and_turnout_context" in tuple(
        step.step_id for step in by_domain["politics"].research_steps
    )
    assert "release_calendar_review" in tuple(
        step.step_id for step in by_domain["macro"].research_steps
    )
    assert "review_protocol_and_etf_catalysts" in tuple(
        step.step_id for step in by_domain["crypto"].research_steps
    )
    assert "map_index_calendar_and_close_window" in tuple(
        step.step_id for step in by_domain["equity_index"].research_steps
    )
    assert "map_real_rate_and_usd_context" in tuple(
        step.step_id for step in by_domain["gold"].research_steps
    )
    assert "map_fixture_and_competition_rules" in tuple(
        step.step_id for step in by_domain["soccer"].research_steps
    )
    assert "review_injury_and_rotation_context" in tuple(
        step.step_id for step in by_domain["basketball"].research_steps
    )

    for playbook in report.playbooks:
        assert playbook.public_status == "pass"
        assert playbook.research_steps
        assert playbook.risk_checks
        assert all(step.public_status == "pass" for step in playbook.research_steps)
        assert all(check.public_status == "pass" for check in playbook.risk_checks)
        assert all(step.paper_only and step.report_only and step.readonly for step in playbook.research_steps)
        assert all(check.paper_only and check.report_only and check.readonly for check in playbook.risk_checks)


def test_missing_required_domain_downgrades_report_to_watch() -> None:
    playbooks = tuple(
        build_research_team_domain_playbook(domain_id)
        for domain_id in REQUIRED_RESEARCH_TEAM_DOMAIN_IDS
        if domain_id != "basketball"
    )

    report = _report(playbooks=playbooks, public_status="watch")

    assert report.public_status == "watch"
    assert "missing_required_domain_basketball" in report.reason_codes


def test_invalid_report_block_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="public_status must match playbook coverage"):
        _report(public_status="block")


def test_blocked_risk_check_blocks_playbook_and_report() -> None:
    blocked_playbook = replace(
        build_research_team_domain_playbook("politics"),
        public_status="block",
        risk_checks=(
            _risk("resolution_rule_clarity"),
            _risk("evidence_freshness", status="block"),
            _risk("no_execution_language"),
        ),
    )
    other_playbooks = tuple(
        build_research_team_domain_playbook(domain_id)
        for domain_id in REQUIRED_RESEARCH_TEAM_DOMAIN_IDS
        if domain_id != "politics"
    )

    report = _report(playbooks=(blocked_playbook,) + other_playbooks, public_status="block")

    assert blocked_playbook.public_status == "block"
    assert "risk_blocked_evidence_freshness" in blocked_playbook.reason_codes
    assert report.public_status == "block"
    assert "domain_blocked_politics" in report.reason_codes


def test_config_steps_checks_playbooks_and_report_are_frozen_and_strictly_typed() -> None:
    config = ResearchTeamDomainPlaybookConfig()
    step = _step()
    risk = _risk()
    playbook = _playbook()
    report = _report()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        step.public_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        risk.public_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        playbook.public_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.public_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="required_domain_ids"):
        replace(config, required_domain_ids=["politics"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_status"):
        replace(step, public_status="ready")
    with pytest.raises(ValueError, match="step_id"):
        replace(step, step_id="unknown_step")
    with pytest.raises(ValueError, match="check_id"):
        replace(risk, check_id="unknown_check")
    with pytest.raises(ValueError, match="research_steps"):
        replace(playbook, research_steps=[step])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="risk_checks"):
        replace(playbook, risk_checks=[risk])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_id"):
        build_research_team_domain_playbook("weather")
    with pytest.raises(ValueError, match="domain_count"):
        replace(report, domain_count="7")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)


def test_public_payload_rejects_sensitive_fields_values_and_execution_language() -> None:
    report = build_default_research_team_domain_playbook_report(config=ResearchTeamDomainPlaybookConfig())
    payload = research_team_domain_playbook_public_payload(report)

    assert payload == research_team_domain_playbook_public_payload(report)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["public_status"] == "pass"

    serialized = repr(payload).casefold()
    forbidden_text = (
        "raw_candidate_id",
        "candidate id",
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
        "buy",
        "sell",
        "recommend",
        "recommendation",
    )
    assert not any(term in serialized for term in forbidden_text)

    for unsafe_payload in (
        {"paper_only": True, "report_only": True, "readonly": True, "raw_candidate_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "market slug leaked"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "source url leaked"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "buy yes"},
        {"paper_only": True, "report_only": False, "readonly": True},
    ):
        with pytest.raises(ValueError):
            research_team_domain_playbook_public_payload(unsafe_payload)


def test_public_models_include_hard_flags_and_exclude_sensitive_field_names() -> None:
    forbidden_fields = {
        "raw_candidate_id",
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
        "buy",
        "sell",
        "recommendation",
    }
    for cls in (
        ResearchTeamDomainPlaybookConfig,
        ResearchTeamDomainPlaybookStep,
        ResearchTeamDomainRiskCheck,
        ResearchTeamDomainPlaybook,
        ResearchTeamDomainPlaybookReport,
    ):
        field_names = {field.name for field in fields(cls)}
        assert {"paper_only", "report_only", "readonly"}.issubset(field_names)
        assert not forbidden_fields.intersection(field_names)


def test_playbook_output_is_deterministic() -> None:
    first = build_default_research_team_domain_playbook_report(config=ResearchTeamDomainPlaybookConfig())
    second = build_default_research_team_domain_playbook_report(config=ResearchTeamDomainPlaybookConfig())

    assert first == second
    assert research_team_domain_playbook_public_payload(first) == research_team_domain_playbook_public_payload(
        second,
    )
