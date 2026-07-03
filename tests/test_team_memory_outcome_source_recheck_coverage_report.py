from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "team_memory_outcome_source_recheck_coverage_report.py",
)


def _api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_outcome_source_recheck_coverage_report",
    )


def _record(
    *,
    outcome_id: str,
    source_id: str,
    team_id: str = "politics",
    category_id: str = "politics",
    outcome_status: str = "unresolved",
    outcome_observed_at: datetime = GENERATED_AT - timedelta(hours=6),
    rechecked_at: datetime | None = GENERATED_AT - timedelta(hours=1),
) -> Any:
    api = _api()
    return api.TeamMemoryOutcomeSourceRecheckRecord(
        outcome_id=outcome_id,
        source_id=source_id,
        team_id=team_id,
        category_id=category_id,
        outcome_status=outcome_status,
        outcome_observed_at=outcome_observed_at,
        rechecked_at=rechecked_at,
    )


def test_build_report_reduces_source_unresolved_and_stale_coverage_by_team_and_category() -> None:
    api = _api()
    config = api.TeamMemoryOutcomeSourceRecheckCoverageConfig(
        config_version="recheck-coverage-test-v0",
        max_recheck_age_seconds=Decimal("86400"),
        expected_team_categories=(
            ("politics", "politics"),
            ("crypto_btc", "finance.crypto.btc"),
            ("sports_soccer", "sports.soccer"),
        ),
    )
    records = (
        _record(outcome_id="outcome-a", source_id="source-current-politics"),
        _record(
            outcome_id="outcome-b",
            source_id="source-stale-politics",
            outcome_observed_at=GENERATED_AT - timedelta(days=4),
            rechecked_at=GENERATED_AT - timedelta(days=3),
        ),
        _record(
            outcome_id="outcome-c",
            source_id="source-missing-btc",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            rechecked_at=None,
        ),
        _record(
            outcome_id="outcome-d",
            source_id="source-current-soccer",
            team_id="sports_soccer",
            category_id="sports.soccer",
            outcome_status="resolved",
            outcome_observed_at=GENERATED_AT - timedelta(days=2),
            rechecked_at=GENERATED_AT - timedelta(hours=2),
        ),
    )

    report = api.build_team_memory_outcome_source_recheck_coverage_report(
        records,
        config=config,
        generated_at=GENERATED_AT,
    )

    assert type(report) is api.TeamMemoryOutcomeSourceRecheckCoverageReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "recheck-coverage-test-v0"
    assert report.coverage_status == "blocked"
    assert report.source_count == Decimal("4")
    assert report.current_source_count == Decimal("2")
    assert report.stale_source_count == Decimal("1")
    assert report.missing_source_count == Decimal("1")
    assert report.unresolved_outcome_count == Decimal("3")
    assert report.unresolved_outcome_with_current_recheck_count == Decimal("1")
    assert report.stale_unresolved_outcome_count == Decimal("1")
    assert report.source_coverage_ratio == Decimal("0.500000")
    assert report.unresolved_outcome_coverage_ratio == Decimal("0.333333")
    assert report.stale_recheck_ratio == Decimal("0.250000")
    assert report.reason_codes == (
        "missing_source_rechecks_present",
        "stale_source_rechecks_present",
        "unresolved_outcomes_missing_current_rechecks",
    )
    assert report.team_count == Decimal("3")
    assert report.category_count == Decimal("3")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.team_rows == (
        api.TeamMemoryOutcomeSourceRecheckTeamRow(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            source_count=Decimal("1"),
            current_source_count=Decimal("0"),
            stale_source_count=Decimal("0"),
            missing_source_count=Decimal("1"),
            unresolved_outcome_count=Decimal("1"),
            unresolved_outcome_with_current_recheck_count=Decimal("0"),
            stale_unresolved_outcome_count=Decimal("0"),
            source_coverage_ratio=Decimal("0.000000"),
            unresolved_outcome_coverage_ratio=Decimal("0.000000"),
            stale_recheck_ratio=Decimal("0.000000"),
            coverage_status="blocked",
            reason_codes=(
                "missing_source_rechecks_present",
                "unresolved_outcomes_missing_current_rechecks",
            ),
        ),
        api.TeamMemoryOutcomeSourceRecheckTeamRow(
            team_id="politics",
            category_id="politics",
            source_count=Decimal("2"),
            current_source_count=Decimal("1"),
            stale_source_count=Decimal("1"),
            missing_source_count=Decimal("0"),
            unresolved_outcome_count=Decimal("2"),
            unresolved_outcome_with_current_recheck_count=Decimal("1"),
            stale_unresolved_outcome_count=Decimal("1"),
            source_coverage_ratio=Decimal("0.500000"),
            unresolved_outcome_coverage_ratio=Decimal("0.500000"),
            stale_recheck_ratio=Decimal("0.500000"),
            coverage_status="blocked",
            reason_codes=(
                "stale_source_rechecks_present",
                "unresolved_outcomes_missing_current_rechecks",
            ),
        ),
        api.TeamMemoryOutcomeSourceRecheckTeamRow(
            team_id="sports_soccer",
            category_id="sports.soccer",
            source_count=Decimal("1"),
            current_source_count=Decimal("1"),
            stale_source_count=Decimal("0"),
            missing_source_count=Decimal("0"),
            unresolved_outcome_count=Decimal("0"),
            unresolved_outcome_with_current_recheck_count=Decimal("0"),
            stale_unresolved_outcome_count=Decimal("0"),
            source_coverage_ratio=Decimal("1.000000"),
            unresolved_outcome_coverage_ratio=None,
            stale_recheck_ratio=Decimal("0.000000"),
            coverage_status="pass",
            reason_codes=("outcome_source_rechecks_covered",),
        ),
    )
    assert tuple(row.category_id for row in report.category_rows) == (
        "finance.crypto.btc",
        "politics",
        "sports.soccer",
    )


def test_report_is_deterministic_for_unsorted_inputs_and_normalizes_utc() -> None:
    api = _api()
    plus_two = timezone(timedelta(hours=2))
    generated_at = datetime(2026, 7, 2, 14, 0, tzinfo=plus_two)
    config = api.TeamMemoryOutcomeSourceRecheckCoverageConfig(
        expected_team_categories=(
            ("sports_soccer", "sports.soccer"),
            ("politics", "politics"),
        ),
    )
    records = (
        _record(
            outcome_id="outcome-b",
            source_id="source-b",
            team_id="sports_soccer",
            category_id="sports.soccer",
            outcome_observed_at=datetime(2026, 7, 2, 10, 30, tzinfo=plus_two),
            rechecked_at=datetime(2026, 7, 2, 13, 0, tzinfo=plus_two),
        ),
        _record(
            outcome_id="outcome-a",
            source_id="source-a",
            outcome_observed_at=datetime(2026, 7, 2, 9, 0, tzinfo=plus_two),
            rechecked_at=datetime(2026, 7, 2, 11, 0, tzinfo=plus_two),
        ),
    )

    first = api.build_team_memory_outcome_source_recheck_coverage_report(
        records,
        config=config,
        generated_at=generated_at,
    )
    second = api.build_team_memory_outcome_source_recheck_coverage_report(
        tuple(reversed(records)),
        config=config,
        generated_at=generated_at,
    )

    assert first == second
    assert first.generated_at == GENERATED_AT
    assert first.latest_rechecked_at == GENERATED_AT - timedelta(hours=1)
    assert tuple(row.team_id for row in first.team_rows) == (
        "politics",
        "sports_soccer",
    )
    assert first.coverage_status == "pass"
    assert first.reason_codes == ("outcome_source_rechecks_covered",)


def test_dataclasses_validate_flags_counts_pairs_and_frozen_instances() -> None:
    api = _api()
    row = api.TeamMemoryOutcomeSourceRecheckTeamRow(
        team_id="politics",
        category_id="politics",
        source_count=Decimal("1"),
        current_source_count=Decimal("1"),
        stale_source_count=Decimal("0"),
        missing_source_count=Decimal("0"),
        unresolved_outcome_count=Decimal("1"),
        unresolved_outcome_with_current_recheck_count=Decimal("1"),
        stale_unresolved_outcome_count=Decimal("0"),
        source_coverage_ratio=Decimal("1.000000"),
        unresolved_outcome_coverage_ratio=Decimal("1.000000"),
        stale_recheck_ratio=Decimal("0.000000"),
        coverage_status="pass",
        reason_codes=("outcome_source_rechecks_covered",),
    )
    report = api.TeamMemoryOutcomeSourceRecheckCoverageReport(
        generated_at=GENERATED_AT,
        config_version="recheck-coverage-test-v0",
        coverage_status="pass",
        source_count=Decimal("1"),
        current_source_count=Decimal("1"),
        stale_source_count=Decimal("0"),
        missing_source_count=Decimal("0"),
        unresolved_outcome_count=Decimal("1"),
        unresolved_outcome_with_current_recheck_count=Decimal("1"),
        stale_unresolved_outcome_count=Decimal("0"),
        source_coverage_ratio=Decimal("1.000000"),
        unresolved_outcome_coverage_ratio=Decimal("1.000000"),
        stale_recheck_ratio=Decimal("0.000000"),
        team_count=Decimal("1"),
        category_count=Decimal("1"),
        latest_rechecked_at=GENERATED_AT,
        team_rows=(row,),
        category_rows=(
            api.TeamMemoryOutcomeSourceRecheckCategoryRow(
                category_id="politics",
                source_count=Decimal("1"),
                current_source_count=Decimal("1"),
                stale_source_count=Decimal("0"),
                missing_source_count=Decimal("0"),
                unresolved_outcome_count=Decimal("1"),
                unresolved_outcome_with_current_recheck_count=Decimal("1"),
                stale_unresolved_outcome_count=Decimal("0"),
                source_coverage_ratio=Decimal("1.000000"),
                unresolved_outcome_coverage_ratio=Decimal("1.000000"),
                stale_recheck_ratio=Decimal("0.000000"),
                coverage_status="pass",
                reason_codes=("outcome_source_rechecks_covered",),
            ),
        ),
        reason_codes=("outcome_source_rechecks_covered",),
    )

    with pytest.raises(FrozenInstanceError):
        row.coverage_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="category_id must match team_id"):
        _record(
            outcome_id="outcome-mismatch",
            source_id="source-mismatch",
            team_id="crypto_btc",
            category_id="politics",
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="current_source_count"):
        replace(report, current_source_count=Decimal("0"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_team_memory_outcome_source_recheck_coverage_report(
            (_record(outcome_id="outcome-naive", source_id="source-naive"),),
            config=api.TeamMemoryOutcomeSourceRecheckCoverageConfig(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )


def test_public_surface_is_decimal_json_ready_and_pure_in_memory() -> None:
    api = _api()
    report = api.build_team_memory_outcome_source_recheck_coverage_report(
        (_record(outcome_id="outcome-a", source_id="source-a"),),
        config=api.TeamMemoryOutcomeSourceRecheckCoverageConfig(),
        generated_at=GENERATED_AT,
    )

    assert api.__all__ == (
        "DEFAULT_TEAM_MEMORY_OUTCOME_SOURCE_RECHECK_COVERAGE_CONFIG_VERSION",
        "DEFAULT_TEAM_CATEGORY_IDS",
        "TeamMemoryOutcomeSourceRecheckCoverageConfig",
        "TeamMemoryOutcomeSourceRecheckRecord",
        "TeamMemoryOutcomeSourceRecheckTeamRow",
        "TeamMemoryOutcomeSourceRecheckCategoryRow",
        "TeamMemoryOutcomeSourceRecheckCoverageReport",
        "build_team_memory_outcome_source_recheck_coverage_report",
        "team_memory_outcome_source_recheck_coverage_report_to_jsonable",
    )
    record_fields = {field.name for field in fields(api.TeamMemoryOutcomeSourceRecheckRecord)}
    report_fields = {
        field.name for field in fields(api.TeamMemoryOutcomeSourceRecheckCoverageReport)
    }
    assert "question" not in record_fields
    assert "market_slug" not in record_fields
    assert "question" not in report_fields
    assert "market_slug" not in report_fields
    public_decimal_fields = {
        "max_recheck_age_seconds",
        "source_count",
        "current_source_count",
        "stale_source_count",
        "missing_source_count",
        "unresolved_outcome_count",
        "unresolved_outcome_with_current_recheck_count",
        "stale_unresolved_outcome_count",
        "team_count",
        "category_count",
    }
    for public_type in (
        api.TeamMemoryOutcomeSourceRecheckCoverageConfig,
        api.TeamMemoryOutcomeSourceRecheckTeamRow,
        api.TeamMemoryOutcomeSourceRecheckCategoryRow,
        api.TeamMemoryOutcomeSourceRecheckCoverageReport,
    ):
        for field in fields(public_type):
            if field.name in public_decimal_fields:
                assert field.type == "Decimal"
    assert _contains_float(asdict(report)) is False
    json.dumps(asdict(report), default=str, allow_nan=False, sort_keys=True)

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {"__import__", "eval", "exec", "open", "print"}
    forbidden_source_fragments = (
        "auth",
        "broker",
        "buy",
        "cancel",
        "credential",
        "dotenv",
        "environ",
        "live",
        "market_slug",
        "order",
        "position",
        "private_key",
        "psycopg",
        "question",
        "recommend",
        "request",
        "sell",
        "signing",
        "socket",
        "submit",
        "supabase",
        "trade",
        "urllib",
        "wallet",
    )

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module] if node.module is not None else []
        else:
            names = []
        for name in names:
            root = name.split(".", maxsplit=1)[0]
            if root in forbidden_import_roots:
                violations.append(f"forbidden import {name}")

        if isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name in forbidden_call_names:
                violations.append(f"forbidden call {call_name}")

    lowered_source = source.lower()
    for fragment in forbidden_source_fragments:
        if fragment in lowered_source:
            violations.append(f"forbidden source fragment {fragment}")

    assert sorted(set(violations)) == []


def test_jsonable_uses_shared_paper_report_surface_guards() -> None:
    api = _api()
    report = api.build_team_memory_outcome_source_recheck_coverage_report(
        (_record(outcome_id="outcome-a", source_id="source-a"),),
        config=api.TeamMemoryOutcomeSourceRecheckCoverageConfig(),
        generated_at=GENERATED_AT,
    )

    payload = api.team_memory_outcome_source_recheck_coverage_report_to_jsonable(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["source_count"] == "1"
    assert payload["team_count"] == "1"
    assert payload["category_count"] == "1"
    assert payload["source_coverage_ratio"] == "1.000000"
    assert payload["team_rows"][0]["source_count"] == "1"
    assert payload["team_rows"][0]["source_coverage_ratio"] == "1.000000"
    assert _contains_float(payload) is False

    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "json_ready_no_floats" in source
    assert "reject_unsafe_surface_fields" in source
    assert "require_paper_only_flags" in source


def test_jsonable_rejects_nested_flag_and_payload_tampering() -> None:
    api = _api()
    report = api.build_team_memory_outcome_source_recheck_coverage_report(
        (_record(outcome_id="outcome-a", source_id="source-a"),),
        config=api.TeamMemoryOutcomeSourceRecheckCoverageConfig(),
        generated_at=GENERATED_AT,
    )

    object.__setattr__(report.team_rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        api.team_memory_outcome_source_recheck_coverage_report_to_jsonable(report)
    object.__setattr__(report.team_rows[0], "readonly", True)

    original_asdict = api.asdict
    try:
        api.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "execution_order_id": "live-order-1",
        }
        with pytest.raises(ValueError, match="unsafe live surface field"):
            api.team_memory_outcome_source_recheck_coverage_report_to_jsonable(report)

        api.asdict = lambda value: {  # type: ignore[method-assign]
            **original_asdict(value),
            "source_coverage_ratio": 1.0,
        }
        with pytest.raises(ValueError, match="must not be a float"):
            api.team_memory_outcome_source_recheck_coverage_report_to_jsonable(report)
    finally:
        api.asdict = original_asdict  # type: ignore[method-assign]


def test_public_decimal_count_and_age_fields_reject_int_constructors() -> None:
    api = _api()
    with pytest.raises(ValueError, match="max_recheck_age_seconds must be a Decimal"):
        api.TeamMemoryOutcomeSourceRecheckCoverageConfig(
            max_recheck_age_seconds=86_400,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        api.TeamMemoryOutcomeSourceRecheckTeamRow(
            team_id="politics",
            category_id="politics",
            source_count=1,  # type: ignore[arg-type]
            current_source_count=Decimal("1"),
            stale_source_count=Decimal("0"),
            missing_source_count=Decimal("0"),
            unresolved_outcome_count=Decimal("1"),
            unresolved_outcome_with_current_recheck_count=Decimal("1"),
            stale_unresolved_outcome_count=Decimal("0"),
            source_coverage_ratio=Decimal("1.000000"),
            unresolved_outcome_coverage_ratio=Decimal("1.000000"),
            stale_recheck_ratio=Decimal("0.000000"),
            coverage_status="pass",
            reason_codes=("outcome_source_rechecks_covered",),
        )

    row = api.TeamMemoryOutcomeSourceRecheckTeamRow(
        team_id="politics",
        category_id="politics",
        source_count=Decimal("1"),
        current_source_count=Decimal("1"),
        stale_source_count=Decimal("0"),
        missing_source_count=Decimal("0"),
        unresolved_outcome_count=Decimal("1"),
        unresolved_outcome_with_current_recheck_count=Decimal("1"),
        stale_unresolved_outcome_count=Decimal("0"),
        source_coverage_ratio=Decimal("1.000000"),
        unresolved_outcome_coverage_ratio=Decimal("1.000000"),
        stale_recheck_ratio=Decimal("0.000000"),
        coverage_status="pass",
        reason_codes=("outcome_source_rechecks_covered",),
    )
    category_row = api.TeamMemoryOutcomeSourceRecheckCategoryRow(
        category_id="politics",
        source_count=Decimal("1"),
        current_source_count=Decimal("1"),
        stale_source_count=Decimal("0"),
        missing_source_count=Decimal("0"),
        unresolved_outcome_count=Decimal("1"),
        unresolved_outcome_with_current_recheck_count=Decimal("1"),
        stale_unresolved_outcome_count=Decimal("0"),
        source_coverage_ratio=Decimal("1.000000"),
        unresolved_outcome_coverage_ratio=Decimal("1.000000"),
        stale_recheck_ratio=Decimal("0.000000"),
        coverage_status="pass",
        reason_codes=("outcome_source_rechecks_covered",),
    )
    with pytest.raises(ValueError, match="team_count must be a Decimal"):
        api.TeamMemoryOutcomeSourceRecheckCoverageReport(
            generated_at=GENERATED_AT,
            config_version="recheck-coverage-test-v0",
            coverage_status="pass",
            source_count=Decimal("1"),
            current_source_count=Decimal("1"),
            stale_source_count=Decimal("0"),
            missing_source_count=Decimal("0"),
            unresolved_outcome_count=Decimal("1"),
            unresolved_outcome_with_current_recheck_count=Decimal("1"),
            stale_unresolved_outcome_count=Decimal("0"),
            source_coverage_ratio=Decimal("1.000000"),
            unresolved_outcome_coverage_ratio=Decimal("1.000000"),
            stale_recheck_ratio=Decimal("0.000000"),
            team_count=1,  # type: ignore[arg-type]
            category_count=Decimal("1"),
            latest_rechecked_at=GENERATED_AT,
            team_rows=(row,),
            category_rows=(category_row,),
            reason_codes=("outcome_source_rechecks_covered",),
        )


def test_fractional_recheck_age_over_threshold_is_stale() -> None:
    api = _api()
    config = api.TeamMemoryOutcomeSourceRecheckCoverageConfig(
        max_recheck_age_seconds=Decimal("86400"),
    )

    report = api.build_team_memory_outcome_source_recheck_coverage_report(
        (
            _record(
                outcome_id="outcome-stale-subsecond",
                source_id="source-stale-subsecond",
                outcome_observed_at=GENERATED_AT - timedelta(days=2),
                rechecked_at=GENERATED_AT
                - timedelta(days=1)
                - timedelta(microseconds=500_000),
            ),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert report.current_source_count == Decimal("0")
    assert report.stale_source_count == Decimal("1")
    assert report.team_rows[0].reason_codes == (
        "stale_source_rechecks_present",
        "unresolved_outcomes_missing_current_rechecks",
    )


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
