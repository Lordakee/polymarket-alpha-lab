from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_memory_update_backlog_priority_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_memory_update_backlog_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def request(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "pending_memory_update_count": d("2.000000"),
        "settled_market_count": d("15.000000"),
        "calibration_error_probability": d("0.040000"),
        "oldest_update_age_hours": d("12.000000"),
        "team_capacity_slots": d("5.000000"),
    }
    values.update(overrides)
    return module.SpecialistTeamMemoryUpdateBacklogPriorityInput(**values)


def build(**overrides: object) -> Any:
    module = api()
    return module.build_specialist_team_memory_update_backlog_priority_report(
        request(**overrides),
    )


def assert_no_float_or_int_values(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def test_build_report_prioritizes_backlog_status_reason_codes_and_manual_step() -> None:
    module = api()

    clear = build(
        pending_memory_update_count=d("0.000000"),
        settled_market_count=d("8.000000"),
        calibration_error_probability=d("0.020000"),
        oldest_update_age_hours=d("0.000000"),
        team_capacity_slots=d("4.000000"),
    )
    monitor = build(
        pending_memory_update_count=d("2.000000"),
        settled_market_count=d("12.000000"),
        calibration_error_probability=d("0.040000"),
        oldest_update_age_hours=d("12.000000"),
        team_capacity_slots=d("5.000000"),
    )
    priority = build(
        pending_memory_update_count=d("6.000000"),
        settled_market_count=d("18.000000"),
        calibration_error_probability=d("0.110000"),
        oldest_update_age_hours=d("48.000000"),
        team_capacity_slots=d("5.000000"),
    )
    critical = build(
        pending_memory_update_count=d("9.000000"),
        settled_market_count=d("30.000000"),
        calibration_error_probability=d("0.210000"),
        oldest_update_age_hours=d("96.000000"),
        team_capacity_slots=d("3.000000"),
    )

    assert is_dataclass(critical)
    assert module.SPECIALIST_TEAM_MEMORY_UPDATE_BACKLOG_STATUSES == (
        "clear",
        "monitor",
        "priority",
        "critical",
    )
    assert clear.backlog_status == "clear"
    assert clear.reason_codes == ("specialist_team_memory_update_backlog_clear",)
    assert clear.manual_next_step == "manual_archive_memory_update_backlog_report"
    assert monitor.backlog_status == "monitor"
    assert monitor.reason_codes == (
        "specialist_team_memory_update_backlog_monitor",
        "pending_memory_updates_within_capacity",
    )
    assert monitor.manual_next_step == "manual_review_memory_update_backlog_next_cycle"
    assert priority.backlog_status == "priority"
    assert priority.reason_codes == (
        "specialist_team_memory_update_backlog_priority",
        "pending_memory_updates_exceed_capacity",
        "calibration_error_probability_review",
        "oldest_memory_update_aging",
    )
    assert priority.manual_next_step == "manual_prioritize_memory_updates_before_new_research"
    assert critical.backlog_status == "critical"
    assert critical.reason_codes == (
        "specialist_team_memory_update_backlog_critical",
        "pending_memory_updates_exceed_capacity",
        "calibration_error_probability_critical",
        "oldest_memory_update_stale",
        "settled_markets_need_memory_backlog_review",
    )
    assert critical.manual_next_step == "manual_clear_memory_update_backlog_before_new_research"
    assert critical.paper_only is True
    assert critical.report_only is True
    assert critical.readonly is True


def test_public_payload_is_json_ready_decimal_only_and_digest_validated() -> None:
    module = api()
    result = build(
        pending_memory_update_count=d("7.000000"),
        settled_market_count=d("25.000000"),
        calibration_error_probability=d("0.180000"),
        oldest_update_age_hours=d("72.000000"),
        team_capacity_slots=d("4.000000"),
    )

    payload = result.public_payload

    assert payload == module.specialist_team_memory_update_backlog_priority_public_payload(
        result,
    )
    assert payload["payload_digest"] == result.payload_digest
    assert payload["pending_memory_update_count"] == "7.000000"
    assert payload["calibration_error_probability"] == "0.180000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    assert module.validate_specialist_team_memory_update_backlog_priority_public_payload(
        payload,
    )

    tampered = dict(payload)
    tampered["backlog_status"] = "monitor"
    with pytest.raises(ValueError, match="payload_digest must match public payload"):
        module.validate_specialist_team_memory_update_backlog_priority_public_payload(
            tampered,
        )

    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "order",
        "key",
        "signature",
        "execute",
        "execution",
        "database",
        "persist",
    ):
        assert forbidden not in encoded


def test_validation_requires_exact_decimal_inputs_flags_and_frozen_report() -> None:
    module = api()
    result = build()

    public_types = {
        "SpecialistTeamMemoryUpdateBacklogPriorityInput",
        "SpecialistTeamMemoryUpdateBacklogPriorityReport",
    }
    for name in public_types:
        cls = getattr(module, name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.backlog_status = "critical"  # type: ignore[misc]

    with pytest.raises(ValueError, match="pending_memory_update_count must be a Decimal"):
        request(pending_memory_update_count=2)

    with pytest.raises(ValueError, match="settled_market_count must be a Decimal"):
        request(settled_market_count=_DecimalSubclass("15.000000"))

    with pytest.raises(ValueError, match="pending_memory_update_count must be an integer Decimal"):
        request(pending_memory_update_count=d("1.500000"))

    with pytest.raises(ValueError, match="calibration_error_probability must not exceed one"):
        request(calibration_error_probability=d("1.000001"))

    with pytest.raises(ValueError, match="team_capacity_slots must be positive"):
        request(team_capacity_slots=d("0.000000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(request(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_module_has_no_external_io_or_write_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert not (imports & forbidden_import_roots)

    text = MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret_key",
        "signature",
        "signing",
        "execute",
        "execution",
        "database",
        "persist",
        "insert",
        "update ",
        "delete",
        "commit",
        "cursor",
    ):
        assert forbidden not in text
