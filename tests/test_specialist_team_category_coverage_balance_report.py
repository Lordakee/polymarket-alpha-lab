from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_category_coverage_balance_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_category_coverage_balance_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object):
    module = api()
    values = {
        "category_count": d("5"),
        "covered_category_count": d("5"),
        "overloaded_team_count": d("0"),
        "undercovered_category_count": d("0"),
        "memory_ready_category_count": d("5"),
    }
    values.update(overrides)
    return module.build_specialist_team_category_coverage_balance_report(**values)


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_int_values(child)
    if isinstance(value, list):
        for child in value:
            assert_no_float_or_int_values(child)


def test_builds_balanced_readonly_report_payload_and_digest() -> None:
    result = report()

    assert result.config_version == (
        "specialist-team-category-coverage-balance-report-v1"
    )
    assert result.category_count == d("5")
    assert result.covered_category_count == d("5")
    assert result.overloaded_team_count == d("0")
    assert result.undercovered_category_count == d("0")
    assert result.memory_ready_category_count == d("5")
    assert result.coverage_balance_status == "balanced"
    assert result.reason_codes == (
        "all_categories_covered",
        "no_overloaded_specialist_teams",
        "no_undercovered_categories",
        "all_category_memory_ready",
        "coverage_balance_balanced",
    )
    assert result.manual_next_step == (
        "Manual review only; keep specialist team category coverage on file."
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    with pytest.raises(FrozenInstanceError):
        result.coverage_balance_status = "blocked"  # type: ignore[misc]

    payload = api().specialist_team_category_coverage_balance_report_payload(result)

    assert payload == result.public_payload
    assert payload["category_count"] == "5"
    assert payload["covered_category_count"] == "5"
    assert payload["overloaded_team_count"] == "0"
    assert payload["undercovered_category_count"] == "0"
    assert payload["memory_ready_category_count"] == "5"
    assert payload["coverage_balance_status"] == "balanced"
    assert payload["payload_digest"] == result.payload_digest
    assert len(result.payload_digest) == 64
    assert result.payload_digest != "pending"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)


def test_blocks_when_categories_are_missing_or_undercovered() -> None:
    blocked = report(
        category_count=d("6"),
        covered_category_count=d("4"),
        overloaded_team_count=d("2"),
        undercovered_category_count=d("2"),
        memory_ready_category_count=d("3"),
    )

    assert blocked.coverage_balance_status == "blocked"
    assert blocked.reason_codes == (
        "category_coverage_incomplete",
        "overloaded_specialist_teams_present",
        "undercovered_categories_present",
        "category_memory_incomplete",
        "coverage_balance_blocked",
    )
    assert blocked.manual_next_step == (
        "Manually assign specialist team coverage before paper research."
    )

    empty = report(
        category_count=d("0"),
        covered_category_count=d("0"),
        overloaded_team_count=d("0"),
        undercovered_category_count=d("0"),
        memory_ready_category_count=d("0"),
    )

    assert empty.coverage_balance_status == "blocked"
    assert empty.reason_codes == (
        "category_universe_missing",
        "no_overloaded_specialist_teams",
        "no_undercovered_categories",
        "all_category_memory_ready",
        "coverage_balance_blocked",
    )


def test_marks_watch_when_coverage_exists_but_balance_or_memory_is_not_ready() -> None:
    watched = report(
        category_count=d("4"),
        covered_category_count=d("4"),
        overloaded_team_count=d("1"),
        undercovered_category_count=d("0"),
        memory_ready_category_count=d("3"),
    )

    assert watched.coverage_balance_status == "watch"
    assert watched.reason_codes == (
        "all_categories_covered",
        "overloaded_specialist_teams_present",
        "no_undercovered_categories",
        "category_memory_incomplete",
        "coverage_balance_watch",
    )
    assert watched.manual_next_step == (
        "Manually rebalance specialist coverage and memory readiness before reuse."
    )


def test_payload_is_deterministic_and_revalidates_digest() -> None:
    module = api()
    first = report(
        category_count=d("7"),
        covered_category_count=d("7"),
        overloaded_team_count=d("0"),
        undercovered_category_count=d("0"),
        memory_ready_category_count=d("7"),
    )
    second = report(
        category_count=d("7"),
        covered_category_count=d("7"),
        overloaded_team_count=d("0"),
        undercovered_category_count=d("0"),
        memory_ready_category_count=d("7"),
    )

    first_payload = module.specialist_team_category_coverage_balance_report_payload(first)
    second_payload = module.specialist_team_category_coverage_balance_report_payload(second)

    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True, separators=(",", ":")) == json.dumps(
        second_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert module.specialist_team_category_coverage_balance_report_payload(first_payload) == (
        first_payload
    )

    tampered = dict(first_payload)
    tampered["covered_category_count"] = "6"
    with pytest.raises(ValueError, match="payload_digest|coverage"):
        module.specialist_team_category_coverage_balance_report_payload(tampered)

    numeric_payload = dict(first_payload)
    numeric_payload["category_count"] = 7
    with pytest.raises(ValueError, match="Decimal|numeric"):
        module.specialist_team_category_coverage_balance_report_payload(numeric_payload)


def test_validation_requires_decimal_only_counts_relationships_and_hard_flags() -> None:
    module = api()
    result = report()

    with pytest.raises(ValueError, match="category_count must be a Decimal"):
        report(category_count=5)

    with pytest.raises(ValueError, match="covered_category_count must be a Decimal"):
        report(covered_category_count=_DecimalSubclass("5"))

    with pytest.raises(ValueError, match="covered_category_count cannot exceed category_count"):
        report(
            category_count=d("3"),
            covered_category_count=d("4"),
            memory_ready_category_count=d("3"),
        )

    with pytest.raises(ValueError, match="undercovered_category_count cannot exceed category_count"):
        report(
            category_count=d("3"),
            covered_category_count=d("3"),
            undercovered_category_count=d("4"),
            memory_ready_category_count=d("3"),
        )

    with pytest.raises(ValueError, match="memory_ready_category_count cannot exceed category_count"):
        report(
            category_count=d("3"),
            covered_category_count=d("3"),
            memory_ready_category_count=d("4"),
        )

    with pytest.raises(ValueError, match="overloaded_team_count must be nonnegative"):
        report(overloaded_team_count=d("-1"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(result, paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(TypeError):

        class ReportSubclass(module.SpecialistTeamCategoryCoverageBalanceReport):
            pass

    decimal_fields = {
        "category_count",
        "covered_category_count",
        "overloaded_team_count",
        "undercovered_category_count",
        "memory_ready_category_count",
    }
    hints = get_type_hints(module.SpecialistTeamCategoryCoverageBalanceReport)
    for item in fields(module.SpecialistTeamCategoryCoverageBalanceReport):
        if item.name in decimal_fields:
            assert hints[item.name] is Decimal


def test_module_surface_is_pure_readonly_report_without_io_or_execution_paths() -> None:
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
        "pathlib",
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
        "run",
        "send",
    }
    forbidden_fragments = (
        "li" "ve",
        "au" "th",
        "wal" "let",
        "private_" "key",
        "api_" "key",
        "si" "gnature",
        "si" "gning",
        "自动执行",
        "签名",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names

    lowered_source = source.lower()
    for fragment in forbidden_fragments:
        assert fragment not in lowered_source
