from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_market_archetype_playbook_score_v2.py"
)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_market_archetype_playbook_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object):
    module = api()
    values: dict[str, object] = {}
    values.update(overrides)
    return module.TeamSpecialistMarketArchetypePlaybookScoreV2Config(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "archetype_id": "event_momentum",
        "archetype_fit_score": d("0.900000"),
        "playbook_step_coverage_score": d("0.850000"),
        "evidence_alignment_score": d("0.800000"),
        "risk_control_score": d("0.900000"),
        "review_learning_score": d("0.700000"),
        "critical_gap_count": d("0"),
    }
    values.update(overrides)
    return module.TeamSpecialistMarketArchetypePlaybookScoreV2Observation(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop(
        "generated_at",
        datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    )
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            observation(team_id="alpha_specialists"),
            observation(
                team_id="beta_specialists",
                archetype_fit_score=d("0.700000"),
                playbook_step_coverage_score=d("0.600000"),
                evidence_alignment_score=d("0.650000"),
                risk_control_score=d("0.550000"),
                review_learning_score=d("0.600000"),
                critical_gap_count=d("1"),
            ),
            observation(
                team_id="gamma_specialists",
                archetype_fit_score=d("0.400000"),
                playbook_step_coverage_score=d("0.350000"),
                evidence_alignment_score=d("0.300000"),
                risk_control_score=d("0.400000"),
                review_learning_score=d("0.200000"),
                critical_gap_count=d("4"),
            ),
        )
    return module.build_team_specialist_market_archetype_playbook_score_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int(item)


def unsafe_terms() -> tuple[str, ...]:
    return (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )


def test_team_archetype_scoring_and_report_rollups_are_decimal_only() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.score_status == "weak"
    assert report.team_count == d("3")
    assert report.strong_team_count == d("1")
    assert report.watch_team_count == d("1")
    assert report.weak_team_count == d("1")
    assert report.weak_playbook_gap_count == d("1")
    assert report.average_market_archetype_playbook_score == d("0.607083")
    assert report.top_market_archetype_playbook_score == d("0.866250")
    assert report.bottom_market_archetype_playbook_score == d("0.303750")
    assert report.reason_codes == (
        "team_specialist_market_archetype_playbook_score_weak_rows",
        "team_specialist_market_archetype_playbook_score_watch_rows",
        "weak_playbook_gap_flags",
    )

    rows = report.rows
    assert tuple(row.team_id for row in rows) == (
        "alpha_specialists",
        "beta_specialists",
        "gamma_specialists",
    )
    assert tuple(row.score_rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.market_archetype_playbook_score for row in rows) == (
        d("0.866250"),
        d("0.651250"),
        d("0.303750"),
    )
    assert tuple(row.playbook_readiness_score for row in rows) == (
        d("0.925000"),
        d("0.675000"),
        d("0.175000"),
    )
    assert tuple(row.score_status for row in rows) == ("strong", "watch", "weak")

    for item in (cfg(), *rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name.endswith(("_count", "_score", "_weight", "_floor", "_rank")):
                assert type(value) is Decimal


def test_weak_playbook_gap_flags_are_exposed_on_rows_and_report() -> None:
    report = build_report(
        observation(
            team_id="gap_specialists",
            playbook_step_coverage_score=d("0.400000"),
            critical_gap_count=d("4"),
        ),
    )
    row = report.rows[0]

    assert row.score_status == "watch"
    assert row.playbook_gap_health_score == d("0.000000")
    assert row.playbook_readiness_score == d("0.200000")
    assert "weak_playbook_gap_flag" in row.reason_codes
    assert report.weak_playbook_gap_count == d("1")
    assert "weak_playbook_gap_flags" in report.reason_codes


def test_payload_serialization_and_validation_are_canonical() -> None:
    module = api()
    report = build_report()
    payload = module.team_specialist_market_archetype_playbook_score_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["team_count"] == "3"
    assert payload["average_market_archetype_playbook_score"] == "0.607083"
    assert payload["rows"][0]["score_rank"] == "1"
    assert payload["rows"][0]["market_archetype_playbook_score"] == "0.866250"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.validate_team_specialist_market_archetype_playbook_score_v2_payload(
        payload,
    )
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_TEAM_SPECIALIST_MARKET_ARCHETYPE_PLAYBOOK_SCORE_V2_CONFIG_VERSION",
        "TeamSpecialistMarketArchetypePlaybookScoreV2Config",
        "TeamSpecialistMarketArchetypePlaybookScoreV2Observation",
        "TeamSpecialistMarketArchetypePlaybookScoreV2Row",
        "TeamSpecialistMarketArchetypePlaybookScoreV2Report",
        "build_team_specialist_market_archetype_playbook_score_v2",
        "team_specialist_market_archetype_playbook_score_v2_payload",
        "validate_team_specialist_market_archetype_playbook_score_v2_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].score_status = "weak"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.TeamSpecialistMarketArchetypePlaybookScoreV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(
            module.TeamSpecialistMarketArchetypePlaybookScoreV2Observation,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.TeamSpecialistMarketArchetypePlaybookScoreV2Row):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.TeamSpecialistMarketArchetypePlaybookScoreV2Report):
            pass

    with pytest.raises(ValueError, match="archetype_fit_score must be exactly Decimal"):
        observation(archetype_fit_score=DecimalSubclass("0.900000"))


def test_hard_flags_are_enforced() -> None:
    module = api()
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(report, report_only=False)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert module.team_specialist_market_archetype_playbook_score_v2_payload(report)[
        "readonly"
    ] is True


def test_digest_tampering_is_rejected_for_report_and_payload() -> None:
    module = api()
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, average_market_archetype_playbook_score=d("0.100000"))

    payload = module.team_specialist_market_archetype_playbook_score_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["team_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_team_specialist_market_archetype_playbook_score_v2_payload(
            tampered_payload,
        )

    object.__setattr__(
        report.rows[0],
        "market_archetype_playbook_score",
        d("0.100000"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_market_archetype_playbook_score_v2_payload(report)


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    module = api()

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public surface"):
            observation(team_id=f"team-{term}")

    payload = module.team_specialist_market_archetype_playbook_score_v2_payload(
        build_report(),
    )
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_team_specialist_market_archetype_playbook_score_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_value_payload["rows"][0]["team_id"] = "team-" + "".join(("tr", "ade"))
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_team_specialist_market_archetype_playbook_score_v2_payload(
            unsafe_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["team_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_team_specialist_market_archetype_playbook_score_v2_payload(
            numeric_payload,
        )


def test_module_omits_unsafe_public_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_or_int([imports, call_names, attribute_names])
