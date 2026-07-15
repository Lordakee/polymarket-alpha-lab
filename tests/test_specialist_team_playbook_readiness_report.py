from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_playbook_readiness_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_playbook_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def team_input(
    *,
    team_code: str = "politics",
    domain: str = "politics",
    playbook_revision_present: bool = True,
    required_source_checklist_present: bool = True,
    domain_risk_checklist_present: bool = True,
    calibration_notes_present: bool = True,
    last_playbook_update_age_seconds: str = "86400",
    supabase_memory_ready: bool = True,
) -> Any:
    module = api()
    return module.SpecialistTeamPlaybookReadinessInput(
        team_code=team_code,
        domain=domain,
        playbook_revision_present=playbook_revision_present,
        required_source_checklist_present=required_source_checklist_present,
        domain_risk_checklist_present=domain_risk_checklist_present,
        calibration_notes_present=calibration_notes_present,
        last_playbook_update_age_seconds=d(last_playbook_update_age_seconds),
        supabase_memory_ready=supabase_memory_ready,
    )


def build_report(*rows: Any) -> Any:
    module = api()
    return module.build_specialist_team_playbook_readiness_report(
        rows,
        config=module.SpecialistTeamPlaybookReadinessConfig(),
    )


def test_exports_config_and_hard_read_only_flags() -> None:
    module = api()
    config = module.SpecialistTeamPlaybookReadinessConfig()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_PLAYBOOK_READINESS_CONFIG_VERSION",
        "SPECIALIST_TEAM_PLAYBOOK_READINESS_STATUSES",
        "SpecialistTeamPlaybookReadinessConfig",
        "SpecialistTeamPlaybookReadinessInput",
        "SpecialistTeamPlaybookReadinessRow",
        "SpecialistTeamPlaybookReadinessReport",
        "build_specialist_team_playbook_readiness_report",
        "specialist_team_playbook_readiness_report_digest",
        "specialist_team_playbook_readiness_report_payload",
    )
    assert module.SPECIALIST_TEAM_PLAYBOOK_READINESS_STATUSES == (
        "ready",
        "attention",
        "blocked",
    )
    assert config.config_version == "specialist-team-playbook-readiness-v0"
    assert config.max_playbook_update_age_seconds == d("2592000")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.SpecialistTeamPlaybookReadinessConfig(paper_only=False)

    with pytest.raises(ValueError, match="max_playbook_update_age_seconds must be a Decimal"):
        module.SpecialistTeamPlaybookReadinessConfig(
            max_playbook_update_age_seconds=2592000,  # type: ignore[arg-type]
        )


def test_report_scores_specialist_playbook_readiness_across_domains() -> None:
    report = build_report(
        team_input(team_code="politics", domain="politics"),
        team_input(
            team_code="finance",
            domain="finance",
            domain_risk_checklist_present=False,
            last_playbook_update_age_seconds="3888000",
        ),
        team_input(
            team_code="sports",
            domain="sports",
            playbook_revision_present=False,
            required_source_checklist_present=False,
            calibration_notes_present=False,
            supabase_memory_ready=False,
        ),
    )

    assert is_dataclass(report)
    assert report.config_version == "specialist-team-playbook-readiness-v0"
    assert report.team_count == d("3")
    assert report.playbook_ready_count == d("1")
    assert report.attention_team_count == d("1")
    assert report.blocked_team_count == d("1")
    assert report.ready_check_ratio == d("0.600000")
    assert report.playbook_ready is False
    assert report.status == "blocked"
    assert report.reason_codes == (
        "playbook_revision_missing",
        "required_source_checklist_missing",
        "domain_risk_checklist_missing",
        "calibration_notes_missing",
        "stale_playbook_update",
        "supabase_memory_not_ready",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.team_code for row in report.readiness_rows) == (
        "sports",
        "finance",
        "politics",
    )
    sports, finance, politics = report.readiness_rows
    assert sports.status == "blocked"
    assert sports.playbook_ready is False
    assert sports.missing_check_count == d("4")
    assert sports.attention_check_count == d("0")
    assert sports.ready_check_ratio == d("0.200000")
    assert sports.reason_codes == (
        "playbook_revision_missing",
        "required_source_checklist_missing",
        "calibration_notes_missing",
        "supabase_memory_not_ready",
    )
    assert finance.status == "attention"
    assert finance.playbook_ready is False
    assert finance.missing_check_count == d("0")
    assert finance.attention_check_count == d("2")
    assert finance.ready_check_ratio == d("0.600000")
    assert finance.reason_codes == (
        "domain_risk_checklist_missing",
        "stale_playbook_update",
    )
    assert politics.status == "ready"
    assert politics.playbook_ready is True
    assert politics.missing_check_count == d("0")
    assert politics.attention_check_count == d("0")
    assert politics.ready_check_ratio == d("1.000000")
    assert politics.reason_codes == ("specialist_team_playbook_ready",)


def test_empty_report_is_ready_with_zero_denominator_ratio() -> None:
    report = build_report()

    assert report.team_count == d("0")
    assert report.playbook_ready_count == d("0")
    assert report.attention_team_count == d("0")
    assert report.blocked_team_count == d("0")
    assert report.missing_check_count == d("0")
    assert report.attention_check_count == d("0")
    assert report.ready_check_ratio == d("0.000000")
    assert report.playbook_ready is True
    assert report.status == "ready"
    assert report.reason_codes == ()
    assert report.readiness_rows == ()


def test_payload_digest_and_decimal_only_contract() -> None:
    module = api()
    report = build_report(
        team_input(team_code="politics", domain="politics"),
        team_input(
            team_code="finance",
            domain="finance",
            domain_risk_checklist_present=False,
        ),
    )

    payload = module.specialist_team_playbook_readiness_report_payload(report)
    assert payload["ready_check_ratio"] == "0.900000"
    assert payload["readiness_rows"][1]["ready_check_ratio"] == "1.000000"
    assert payload["readiness_rows"][0]["reason_codes"] == [
        "domain_risk_checklist_missing",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    digest = module.specialist_team_playbook_readiness_report_digest(report)
    assert digest == report.digest
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")
    assert "Decimal" not in repr(payload)


def test_validation_frozen_dataclass_decimal_only_and_side_effect_free() -> None:
    module = api()

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(team_input())
    for value in (
        team_input(team_code="finance", domain="finance"),
        report,
        *report.readiness_rows,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_ratio", "_seconds")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.readiness_rows[0].status = "attention"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.playbook_ready = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="last_playbook_update_age_seconds must be a Decimal"):
        team_input(last_playbook_update_age_seconds="1")
        module.SpecialistTeamPlaybookReadinessInput(
            team_code="politics",
            domain="politics",
            playbook_revision_present=True,
            required_source_checklist_present=True,
            domain_risk_checklist_present=True,
            calibration_notes_present=True,
            last_playbook_update_age_seconds=1,  # type: ignore[arg-type]
            supabase_memory_ready=True,
        )
    with pytest.raises(ValueError, match="team_code must be one of politics, finance, or sports"):
        team_input(team_code="crypto")
    with pytest.raises(ValueError, match="domain must be one of politics, finance, or sports"):
        team_input(domain="crypto")
    with pytest.raises(ValueError, match="team_code and domain must match"):
        team_input(team_code="politics", domain="finance")
    with pytest.raises(ValueError, match="playbook_revision_present must be a bool"):
        team_input(playbook_revision_present=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate specialist team"):
        build_report(team_input(), team_input())
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_check_ratio must match readiness checks"):
        replace(report.readiness_rows[0], ready_check_ratio=d("0.123456"))

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "insert",
        "update ",
        "delete(",
        "post(",
        "put(",
    ):
        assert forbidden not in lowered
    for forbidden in (
        "wallet",
        "live_trading",
        "order",
        "trade",
        "auth",
        "token",
        "dsn",
    ):
        assert forbidden not in lowered


def _float_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) is float:
        return (path or "<root>",)
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_float_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(found)
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(found)
    return ()
