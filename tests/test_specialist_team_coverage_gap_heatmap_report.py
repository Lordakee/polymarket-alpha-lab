from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
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
    / "specialist_team_coverage_gap_heatmap_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_coverage_gap_heatmap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def generated_at() -> datetime:
    return datetime(2026, 7, 12, 15, 30, tzinfo=UTC)


def coverage(**overrides: object):
    module = api()
    values = {
        "team_id": "team_politics",
        "category_id": "category_elections",
        "market_count": d("12.000000"),
        "assigned_specialist_count": d("3.000000"),
        "source_family_count": d("4.000000"),
        "memory_ready_count": d("10.000000"),
        "unresolved_gap_count": d("0.000000"),
    }
    values.update(overrides)
    return module.SpecialistTeamCoverageGapHeatmapInput(**values)


def report(*items: object):
    module = api()
    return module.build_specialist_team_coverage_gap_heatmap_report(
        items,
        config=module.SpecialistTeamCoverageGapHeatmapConfig(),
        generated_at=generated_at(),
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


def test_build_report_outputs_ranked_team_category_gap_heatmap_rows() -> None:
    module = api()
    ready = coverage(team_id="team_politics", category_id="category_elections")
    watch = coverage(
        team_id="team_crypto",
        category_id="category_btc",
        market_count=d("8.000000"),
        assigned_specialist_count=d("1.000000"),
        source_family_count=d("2.000000"),
        memory_ready_count=d("6.000000"),
        unresolved_gap_count=d("1.000000"),
    )
    blocked = coverage(
        team_id="team_equities",
        category_id="category_indices",
        market_count=d("9.000000"),
        assigned_specialist_count=d("0.000000"),
        source_family_count=d("1.000000"),
        memory_ready_count=d("3.000000"),
        unresolved_gap_count=d("4.000000"),
    )

    result = report(blocked, watch, ready)

    assert is_dataclass(result)
    assert module.SPECIALIST_TEAM_COVERAGE_GAP_HEATMAP_STATUSES == (
        "ready",
        "watch",
        "blocked",
    )
    assert result.report_status == "blocked"
    assert result.row_count == d("3.000000")
    assert result.team_count == d("3.000000")
    assert result.category_count == d("3.000000")
    assert result.ready_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.blocked_count == d("1.000000")
    assert result.manual_next_step_count == d("2.000000")
    assert result.total_market_count == d("29.000000")
    assert result.total_unresolved_gap_count == d("5.000000")
    assert result.max_gap_heat == d("0.854167")
    assert result.average_gap_heat == d("0.395833")
    assert result.reason_codes == (
        "coverage_gap_heatmap_blocked_rows",
        "coverage_gap_heatmap_watch_rows",
    )
    assert [row.team_id for row in result.rows] == [
        "team_equities",
        "team_crypto",
        "team_politics",
    ]
    assert [row.category_id for row in result.rows] == [
        "category_indices",
        "category_btc",
        "category_elections",
    ]
    assert [row.coverage_status for row in result.rows] == [
        "blocked",
        "watch",
        "ready",
    ]
    assert [row.gap_heat for row in result.rows] == [
        d("0.854167"),
        d("0.333333"),
        d("0.000000"),
    ]
    assert result.rows[0].reason_codes == (
        "coverage_blocked",
        "specialist_assignment_gap",
        "source_family_gap",
        "memory_readiness_gap",
        "unresolved_gap_backlog",
    )
    assert result.rows[0].manual_next_step == "assign_specialist_and_refresh_memory"
    assert result.rows[1].reason_codes == (
        "coverage_watch",
        "source_family_gap",
        "unresolved_gap_backlog",
    )
    assert result.rows[1].manual_next_step == "review_coverage_gap"
    assert result.rows[2].reason_codes == ("coverage_ready",)
    assert result.rows[2].manual_next_step == "none"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = module.specialist_team_coverage_gap_heatmap_report_payload(result)
    assert payload == result.payload
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)
    assert module.validate_specialist_team_coverage_gap_heatmap_report_payload(payload)


def test_payload_and_digest_are_deterministic_for_same_public_inputs() -> None:
    left = report(
        coverage(team_id="team_crypto", category_id="category_btc"),
        coverage(team_id="team_politics", category_id="category_elections"),
    )
    right = report(
        coverage(team_id="team_politics", category_id="category_elections"),
        coverage(team_id="team_crypto", category_id="category_btc"),
    )

    assert left.derived_validation_digest == right.derived_validation_digest
    assert left.payload == right.payload
    encoded = json.dumps(left.payload, sort_keys=True)
    assert left.derived_validation_digest in encoded


def test_empty_report_is_blocked_report_only_and_digest_backed() -> None:
    result = report()

    assert result.report_status == "blocked"
    assert result.row_count == d("0.000000")
    assert result.team_count == d("0.000000")
    assert result.category_count == d("0.000000")
    assert result.max_gap_heat == d("0.000000")
    assert result.average_gap_heat == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == ("coverage_gap_heatmap_empty",)
    assert result.payload["derived_validation_digest"] == result.derived_validation_digest


def test_validation_requires_decimal_counts_public_codes_flags_and_frozen_outputs() -> None:
    module = api()
    result = report(coverage())

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="market_count must be a Decimal"):
        coverage(market_count=12)

    with pytest.raises(ValueError, match="assigned_specialist_count must be a Decimal"):
        coverage(assigned_specialist_count=_DecimalSubclass("2.000000"))

    with pytest.raises(ValueError, match="source_family_count must be an integer Decimal"):
        coverage(source_family_count=d("1.500000"))

    with pytest.raises(ValueError, match="memory_ready_count must not exceed market_count"):
        coverage(memory_ready_count=d("13.000000"))

    with pytest.raises(ValueError, match="team_id must be a public code"):
        coverage(team_id="Team Politics")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(coverage(), paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="coverage_status must be supported"):
        module.SpecialistTeamCoverageGapHeatmapRow(
            team_id="team_macro",
            category_id="category_rates",
            market_count=d("2.000000"),
            assigned_specialist_count=d("1.000000"),
            source_family_count=d("2.000000"),
            memory_ready_count=d("2.000000"),
            unresolved_gap_count=d("0.000000"),
            coverage_status="clear",
            gap_heat=d("0.000000"),
            reason_codes=("coverage_ready",),
            manual_next_step="none",
        )


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "required_assigned_specialist_count",
        "required_source_family_count",
        "market_count",
        "assigned_specialist_count",
        "source_family_count",
        "memory_ready_count",
        "unresolved_gap_count",
        "gap_heat",
        "row_count",
        "team_count",
        "category_count",
        "ready_count",
        "watch_count",
        "blocked_count",
        "manual_next_step_count",
        "total_market_count",
        "total_unresolved_gap_count",
        "max_gap_heat",
        "average_gap_heat",
        "count",
    }

    for cls in (
        module.SpecialistTeamCoverageGapHeatmapConfig,
        module.SpecialistTeamCoverageGapHeatmapInput,
        module.SpecialistTeamCoverageGapHeatmapRow,
        module.SpecialistTeamCoverageGapHeatmapReasonCodeCount,
        module.SpecialistTeamCoverageGapHeatmapReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in decimal_fields:
                assert hints[item.name] is Decimal


def test_payload_validation_rejects_tampering_and_unsafe_numeric_values() -> None:
    module = api()
    payload = report(coverage()).payload

    tampered = dict(payload)
    tampered["report_status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.validate_specialist_team_coverage_gap_heatmap_report_payload(tampered)

    tampered_numeric = dict(payload)
    tampered_numeric["row_count"] = 1
    with pytest.raises(ValueError, match="payload numeric values must be strings"):
        module.validate_specialist_team_coverage_gap_heatmap_report_payload(
            tampered_numeric,
        )

    tampered_float = dict(payload)
    tampered_float["average_gap_heat"] = 0.1
    with pytest.raises(ValueError, match="payload numeric values must be strings"):
        module.validate_specialist_team_coverage_gap_heatmap_report_payload(
            tampered_float,
        )


def test_module_scope_has_no_persistence_network_wallet_or_order_surface() -> None:
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
    assert_no_float_or_int_values([imports, call_names, attribute_names])
