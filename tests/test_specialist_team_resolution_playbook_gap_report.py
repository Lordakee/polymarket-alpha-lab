from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.specialist_team_resolution_playbook_gap_report as api
from polymarket_alpha_lab.specialist_team_resolution_playbook_gap_report import (
    SpecialistTeamResolutionPlaybookGapReport,
    build_specialist_team_resolution_playbook_gap_report,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def report(
    *,
    team_id: str = "team-alpha",
    category_id: str = "category-politics",
    resolution_rule_examples_count: Decimal = d("3.000000"),
    ambiguous_rule_examples_count: Decimal = d("0.000000"),
    post_settlement_notes_count: Decimal = d("2.000000"),
    last_playbook_review_age_hours: Decimal = d("12.000000"),
) -> SpecialistTeamResolutionPlaybookGapReport:
    return build_specialist_team_resolution_playbook_gap_report(
        team_id=team_id,
        category_id=category_id,
        resolution_rule_examples_count=resolution_rule_examples_count,
        ambiguous_rule_examples_count=ambiguous_rule_examples_count,
        post_settlement_notes_count=post_settlement_notes_count,
        last_playbook_review_age_hours=last_playbook_review_age_hours,
    )


def test_builds_pass_report_for_current_complete_resolution_playbook() -> None:
    result = report()

    assert result.team_id == "team-alpha"
    assert result.category_id == "category-politics"
    assert result.playbook_gap_status == "pass"
    assert result.reason_codes == ("specialist_team_resolution_playbook_gap_passed",)
    assert result.manual_next_step == "continue scheduled review cadence"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_blocks_when_resolution_rules_are_missing_or_ambiguous() -> None:
    result = report(
        resolution_rule_examples_count=d("1.000000"),
        ambiguous_rule_examples_count=d("2.000000"),
    )

    assert result.playbook_gap_status == "blocked"
    assert result.reason_codes == (
        "resolution_rule_examples_gap",
        "ambiguous_resolution_rule_examples_present",
    )
    assert result.manual_next_step == (
        "manually add deterministic resolution rule examples and adjudicate ambiguous rules"
    )


def test_watch_for_missing_settlement_notes_or_stale_review() -> None:
    result = report(
        post_settlement_notes_count=d("0.000000"),
        last_playbook_review_age_hours=d("73.000000"),
    )

    assert result.playbook_gap_status == "watch"
    assert result.reason_codes == (
        "post_settlement_notes_gap",
        "playbook_review_stale",
    )
    assert result.manual_next_step == (
        "manually refresh settlement notes and schedule specialist playbook review"
    )


def test_public_payload_uses_decimal_strings_and_stable_digest() -> None:
    result = report()

    payload = result.public_payload
    json.dumps(payload, sort_keys=True)

    assert payload == {
        "team_id": "team-alpha",
        "category_id": "category-politics",
        "resolution_rule_examples_count": "3.000000",
        "ambiguous_rule_examples_count": "0.000000",
        "post_settlement_notes_count": "2.000000",
        "last_playbook_review_age_hours": "12.000000",
        "playbook_gap_status": "pass",
        "reason_codes": ["specialist_team_resolution_playbook_gap_passed"],
        "manual_next_step": "continue scheduled review cadence",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert len(result.payload_digest) == 64
    assert result.payload_digest == report().payload_digest
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(result)


def test_frozen_decimal_only_validation_and_public_safety() -> None:
    result = report()

    assert hasattr(result, "__dataclass_fields__")
    with pytest.raises(FrozenInstanceError):
        result.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="resolution_rule_examples_count"):
        report(resolution_rule_examples_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_rule_examples_count"):
        report(resolution_rule_examples_count=d("3.0000004"))
    with pytest.raises(ValueError, match="ambiguous_rule_examples_count"):
        report(ambiguous_rule_examples_count=d("-1.000000"))
    with pytest.raises(ValueError, match="team_id"):
        report(team_id="wallet-team")
    with pytest.raises(ValueError, match="category_id"):
        report(category_id="live-category")
    with pytest.raises(ValueError, match="paper_only"):
        SpecialistTeamResolutionPlaybookGapReport(
            team_id="team-alpha",
            category_id="category-politics",
            resolution_rule_examples_count=d("3.000000"),
            ambiguous_rule_examples_count=d("0.000000"),
            post_settlement_notes_count=d("2.000000"),
            last_playbook_review_age_hours=d("12.000000"),
            playbook_gap_status="pass",
            reason_codes=("specialist_team_resolution_playbook_gap_passed",),
            manual_next_step="continue scheduled review cadence",
            paper_only=False,
        )


def test_no_live_auth_wallet_database_or_persistence_surface() -> None:
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "key",
        "sign",
        "execute",
        "database",
        "db",
        "jsonl",
        "persist",
        "write",
        "order",
        "trade",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for field in fields(SpecialistTeamResolutionPlaybookGapReport):
        lowered = field.name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "open",
        "Path",
    ):
        assert not hasattr(api, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, str):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            if field.name == "public_payload":
                continue
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
