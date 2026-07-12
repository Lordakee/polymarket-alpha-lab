from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/specialist_team_research_backlog_wip_limit_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_research_backlog_wip_limit_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object):
    report = api()
    values = {
        "open_research_item_count": d("6"),
        "active_agent_count": d("3"),
        "team_capacity_count": d("8"),
        "blocked_item_count": d("0"),
        "oldest_item_age_hours": d("12.000000"),
    }
    values.update(overrides)
    return report.build_specialist_team_research_backlog_wip_limit_report(**values)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        nested: list[object] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def test_wip_limit_report_flags_blocked_research_backlog_risk() -> None:
    summary = build_report(
        open_research_item_count=d("16"),
        active_agent_count=d("3"),
        team_capacity_count=d("8"),
        blocked_item_count=d("2"),
        oldest_item_age_hours=d("30.000000"),
    )

    assert is_dataclass(summary)
    assert summary.wip_status == "block"
    assert summary.manual_next_step == "pause_new_research_intake_and_rebalance_team_queue"
    assert summary.reason_codes == (
        "specialist_team_research_backlog_above_capacity_block",
        "specialist_team_research_agent_wip_limit_block",
        "specialist_team_research_blocked_items_present",
        "specialist_team_research_oldest_item_stale_block",
    )
    assert summary.open_research_item_count == d("16")
    assert summary.active_agent_count == d("3")
    assert summary.team_capacity_count == d("8")
    assert summary.blocked_item_count == d("2")
    assert summary.oldest_item_age_hours == d("30.000000")
    assert summary.backlog_to_capacity_ratio == d("2.000000")
    assert summary.backlog_per_active_agent == d("5.333333")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.payload_digest) == 64


@pytest.mark.parametrize(
    (
        "open_research_item_count",
        "active_agent_count",
        "team_capacity_count",
        "blocked_item_count",
        "oldest_item_age_hours",
        "expected_status",
        "expected_step",
        "expected_reasons",
    ),
    (
        (
            d("5"),
            d("3"),
            d("8"),
            d("0"),
            d("6.000000"),
            "pass",
            "continue_manual_research_triage",
            ("specialist_team_research_wip_clear",),
        ),
        (
            d("9"),
            d("3"),
            d("8"),
            d("0"),
            d("18.000000"),
            "watch",
            "review_team_research_backlog_before_new_intake",
            (
                "specialist_team_research_backlog_above_capacity_watch",
                "specialist_team_research_oldest_item_stale_watch",
            ),
        ),
        (
            d("0"),
            d("0"),
            d("0"),
            d("0"),
            d("0.000000"),
            "pass",
            "continue_manual_research_triage",
            ("specialist_team_research_wip_clear",),
        ),
    ),
)
def test_wip_statuses_are_deterministic_from_phase_one_inputs(
    open_research_item_count: Decimal,
    active_agent_count: Decimal,
    team_capacity_count: Decimal,
    blocked_item_count: Decimal,
    oldest_item_age_hours: Decimal,
    expected_status: str,
    expected_step: str,
    expected_reasons: tuple[str, ...],
) -> None:
    summary = build_report(
        open_research_item_count=open_research_item_count,
        active_agent_count=active_agent_count,
        team_capacity_count=team_capacity_count,
        blocked_item_count=blocked_item_count,
        oldest_item_age_hours=oldest_item_age_hours,
    )

    assert summary.wip_status == expected_status
    assert summary.manual_next_step == expected_step
    assert summary.reason_codes == expected_reasons


def test_public_payload_is_decimal_string_only_and_tamper_evident() -> None:
    report = api()
    summary = build_report()

    payload = summary.public_payload

    assert payload == {
        "report_name": "specialist_team_research_backlog_wip_limit_report",
        "phase": "phase_1",
        "wip_status": "pass",
        "reason_codes": ["specialist_team_research_wip_clear"],
        "manual_next_step": "continue_manual_research_triage",
        "open_research_item_count": "6",
        "active_agent_count": "3",
        "team_capacity_count": "8",
        "blocked_item_count": "0",
        "oldest_item_age_hours": "12.000000",
        "backlog_to_capacity_ratio": "0.750000",
        "backlog_per_active_agent": "2.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": summary.payload_digest,
    }
    assert all(type(value) is not Decimal for value in walk_values(payload))
    assert payload["payload_digest"] == report.payload_digest_for_public_payload(payload)

    tampered = dict(payload)
    tampered["blocked_item_count"] = "2"
    with pytest.raises(ValueError, match="payload_digest"):
        report.validate_specialist_team_research_backlog_wip_limit_public_payload(
            tampered,
        )

    payload_text = json.dumps(payload, sort_keys=True)
    assert not any(
        forbidden in payload_text.lower()
        for forbidden in (
            "wallet",
            "private",
            "signature",
            "automatic",
            "database",
            "jsonl",
        )
    )


def test_dataclass_is_frozen_decimal_only_and_flags_are_hard_required() -> None:
    report = api()
    summary = build_report()

    with pytest.raises(FrozenInstanceError):
        summary.wip_status = "block"  # type: ignore[misc]

    for field in fields(summary):
        item = getattr(summary, field.name)
        if field.name in {
            "paper_only",
            "report_only",
            "readonly",
            "reason_codes",
            "manual_next_step",
            "wip_status",
            "public_payload",
            "payload_digest",
        }:
            continue
        assert type(item) is Decimal

    with pytest.raises(ValueError, match="Decimal"):
        build_report(open_research_item_count=6)
    with pytest.raises(ValueError, match="Decimal"):
        build_report(oldest_item_age_hours=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="whole"):
        build_report(active_agent_count=d("1.5"))
    with pytest.raises(ValueError, match="nonnegative"):
        build_report(blocked_item_count=d("-1"))
    with pytest.raises(ValueError, match="paper_only"):
        report.SpecialistTeamResearchBacklogWipLimitReport(
            open_research_item_count=d("1"),
            active_agent_count=d("1"),
            team_capacity_count=d("1"),
            blocked_item_count=d("0"),
            oldest_item_age_hours=d("1.000000"),
            backlog_to_capacity_ratio=d("1.000000"),
            backlog_per_active_agent=d("1.000000"),
            wip_status="pass",
            reason_codes=("specialist_team_research_wip_clear",),
            manual_next_step="continue_manual_research_triage",
            public_payload={},
            payload_digest="0" * 64,
            paper_only=False,
        )


def test_module_scope_stays_report_only_without_persistence_or_connectors() -> None:
    source = MODULE_PATH.read_text()
    lowered = source.lower()

    assert "psycopg" not in lowered
    assert "sqlite" not in lowered
    assert "sqlalchemy" not in lowered
    assert "requests" not in lowered
    assert "httpx" not in lowered
    assert "jsonl" not in lowered
    assert "open(" not in lowered
    assert ".write(" not in lowered
    assert "paper_only: bool = true" in lowered
    assert "report_only: bool = true" in lowered
    assert "readonly: bool = true" in lowered
