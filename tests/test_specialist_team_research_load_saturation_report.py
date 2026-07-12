from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_research_load_saturation_report.py"
)
GENERATED_AT = datetime(2026, 7, 12, 14, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_research_load_saturation_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object):
    module = api()
    values = {
        "team_id": "team_macro",
        "open_research_items": d("8.000000"),
        "available_specialists": d("4.000000"),
        "urgent_items": d("1.000000"),
        "blocked_items": d("0.000000"),
        "average_age_hours": d("12.000000"),
    }
    values.update(overrides)
    return module.build_specialist_team_research_load_saturation_report(
        generated_at=GENERATED_AT,
        **values,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def test_builds_readonly_saturation_report_from_team_load_inputs() -> None:
    result = report(
        open_research_items=d("10.000000"),
        available_specialists=d("4.000000"),
        urgent_items=d("2.000000"),
        blocked_items=d("1.000000"),
        average_age_hours=d("36.000000"),
    )

    assert result.generated_at == GENERATED_AT
    assert result.config_version == "specialist-team-research-load-saturation-report-v1"
    assert result.team_id == "team_macro"
    assert result.open_research_items == d("10.000000")
    assert result.available_specialists == d("4.000000")
    assert result.urgent_items == d("2.000000")
    assert result.blocked_items == d("1.000000")
    assert result.average_age_hours == d("36.000000")
    assert result.saturation_ratio == d("2.500000")
    assert result.load_status == "watch"
    assert result.reason_codes == (
        "specialist_capacity_watch",
        "urgent_research_items_present",
        "blocked_research_items_present",
        "research_age_watch",
    )
    assert result.manual_next_step == (
        "Manually rebalance specialist coverage before accepting new research intake."
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_blocks_when_no_specialists_are_available_or_ratio_is_critical() -> None:
    no_capacity = report(
        available_specialists=d("0.000000"),
        open_research_items=d("3.000000"),
        urgent_items=d("0.000000"),
        blocked_items=d("0.000000"),
        average_age_hours=d("4.000000"),
    )
    saturated = report(
        available_specialists=d("2.000000"),
        open_research_items=d("8.000000"),
        urgent_items=d("3.000000"),
        blocked_items=d("2.000000"),
        average_age_hours=d("80.000000"),
    )

    assert no_capacity.saturation_ratio == d("3.000000")
    assert no_capacity.load_status == "block"
    assert no_capacity.reason_codes == (
        "no_available_specialists",
        "specialist_capacity_block",
    )
    assert no_capacity.manual_next_step == (
        "Manually pause new research intake and assign specialist coverage."
    )

    assert saturated.saturation_ratio == d("4.000000")
    assert saturated.load_status == "block"
    assert saturated.reason_codes == (
        "specialist_capacity_block",
        "urgent_research_items_present",
        "blocked_research_items_present",
        "research_age_block",
    )


def test_passes_when_capacity_is_available_and_load_is_clear() -> None:
    clear = report(
        open_research_items=d("2.000000"),
        available_specialists=d("4.000000"),
        urgent_items=d("0.000000"),
        blocked_items=d("0.000000"),
        average_age_hours=d("6.000000"),
    )

    assert clear.saturation_ratio == d("0.500000")
    assert clear.load_status == "pass"
    assert clear.reason_codes == ("specialist_research_load_clear",)
    assert clear.manual_next_step == (
        "Manual review only; keep the specialist team load report on file."
    )


def test_payload_is_deterministic_decimal_stringed_and_revalidates_digest() -> None:
    module = api()
    first = report()
    second = report()

    first_payload = module.specialist_team_research_load_saturation_report_payload(first)
    second_payload = module.specialist_team_research_load_saturation_report_payload(second)

    assert first_payload == first.payload
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True, separators=(",", ":")) == json.dumps(
        second_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert first_payload["open_research_items"] == "8.000000"
    assert first_payload["available_specialists"] == "4.000000"
    assert first_payload["saturation_ratio"] == "2.000000"
    assert first_payload["validation_digest"] == first.validation_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert_no_float_or_int_values(first_payload)
    assert (
        module.specialist_team_research_load_saturation_report_payload(first_payload)
        == first_payload
    )

    tampered = dict(first_payload)
    tampered["saturation_ratio"] = "9.000000"
    with pytest.raises(ValueError, match="validation_digest|saturation_ratio"):
        module.specialist_team_research_load_saturation_report_payload(tampered)

    numeric_payload = dict(first_payload)
    numeric_payload["open_research_items"] = 8
    with pytest.raises(ValueError, match="Decimal|numeric"):
        module.specialist_team_research_load_saturation_report_payload(numeric_payload)


def test_validation_requires_frozen_decimal_only_public_team_id_and_hard_flags() -> None:
    module = api()
    result = report()

    with pytest.raises(FrozenInstanceError):
        result.load_status = "block"  # type: ignore[misc]

    with pytest.raises(ValueError, match="open_research_items must be a Decimal"):
        report(open_research_items=8)

    with pytest.raises(ValueError, match="urgent_items must be a Decimal"):
        report(urgent_items=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="blocked_items cannot exceed open_research_items"):
        report(open_research_items=d("1.000000"), blocked_items=d("2.000000"))

    with pytest.raises(ValueError, match="urgent_items cannot exceed open_research_items"):
        report(open_research_items=d("1.000000"), urgent_items=d("2.000000"))

    with pytest.raises(ValueError, match="average_age_hours must be nonnegative"):
        report(average_age_hours=d("-0.000001"))

    with pytest.raises(ValueError, match="team_id must be a public code"):
        report(team_id="team:macro")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(result, paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    decimal_fields = {
        "open_research_items",
        "available_specialists",
        "urgent_items",
        "blocked_items",
        "average_age_hours",
        "saturation_ratio",
    }
    for item in fields(module.SpecialistTeamResearchLoadSaturationReport):
        if item.name in decimal_fields:
            assert get_type_hints(module.SpecialistTeamResearchLoadSaturationReport)[item.name] is Decimal


def test_module_surface_is_pure_readonly_report_without_io_or_trading_terms() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_client",
        "insert",
        "update",
        "delete",
        "execute",
    }
    forbidden_text = (
        "wallet",
        "auth",
        "private_key",
        "live trading",
        "place_order",
        "database",
        "network",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            if isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names

    lowered = source.lower()
    for token in forbidden_text:
        assert token not in lowered
