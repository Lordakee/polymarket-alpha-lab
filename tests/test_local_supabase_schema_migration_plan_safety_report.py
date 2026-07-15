from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.local_supabase_schema_migration_plan_safety_report"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/local_supabase_schema_migration_plan_safety_report.py",
)
GENERATED_AT = datetime(2026, 7, 12, 10, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 12, 9, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def plan(
    surface: str,
    *,
    local_supabase_postgres_only: bool = True,
    dsn_validator_name: str = "validate_local_postgres_dsn",
    sqlite_absent: bool = True,
    redis_absent: bool = True,
    mongo_absent: bool = True,
    sqlalchemy_absent: bool = True,
    hosted_database_absent: bool = True,
    durable_jsonl_fallback_absent: bool = True,
    paper_evidence_only: bool = True,
    migration_execution_absent: bool = True,
    observed_at: datetime = OBSERVED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return api().LocalSupabaseSchemaMigrationPlanSafetySignal(
        migration_surface=surface,
        local_supabase_postgres_only=local_supabase_postgres_only,
        dsn_validator_name=dsn_validator_name,
        sqlite_absent=sqlite_absent,
        redis_absent=redis_absent,
        mongo_absent=mongo_absent,
        sqlalchemy_absent=sqlalchemy_absent,
        hosted_database_absent=hosted_database_absent,
        durable_jsonl_fallback_absent=durable_jsonl_fallback_absent,
        paper_evidence_only=paper_evidence_only,
        migration_execution_absent=migration_execution_absent,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*plans: Any, generated_at: datetime = GENERATED_AT) -> Any:
    return api().build_local_supabase_schema_migration_plan_safety_report(
        plans,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_schema_migration_plan_safety_requires_all_paper_evidence_surfaces() -> None:
    module = api()

    report = build_report(
        plan("paper_research_packets"),
        plan("paper_recommendation_reports"),
        plan("paper_cycle_snapshots"),
        plan("paper_trade_journal"),
        plan("paper_nav_snapshots"),
        plan("paper_operator_evidence"),
    )

    assert module.LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES == (
        "paper_research_packets",
        "paper_recommendation_reports",
        "paper_cycle_snapshots",
        "paper_trade_journal",
        "paper_nav_snapshots",
        "paper_operator_evidence",
    )
    assert module.LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_STATUSES == (
        "ready",
        "attention",
        "blocker",
    )
    assert report.status == "ready"
    assert report.migration_surface_count == d("6.000000")
    assert report.required_surface_count == d("6.000000")
    assert report.missing_required_surface_count == ZERO
    assert report.ready_count == d("6.000000")
    assert report.attention_count == ZERO
    assert report.blocker_count == ZERO
    assert report.ready_ratio == ONE
    assert report.reason_codes == ("local_supabase_schema_migration_plan_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.migration_surface for row in report.rows) == (
        "paper_research_packets",
        "paper_recommendation_reports",
        "paper_cycle_snapshots",
        "paper_trade_journal",
        "paper_nav_snapshots",
        "paper_operator_evidence",
    )
    assert all(row.status == "ready" for row in report.rows)
    assert all(row.ready_check_count == d("10.000000") for row in report.rows)
    assert all(row.required_check_count == d("10.000000") for row in report.rows)
    assert all(row.readiness_ratio == ONE for row in report.rows)
    assert all(
        row.dsn_validator_name == "validate_local_postgres_dsn"
        for row in report.rows
    )

    payload = module.local_supabase_schema_migration_plan_safety_report_payload(report)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["ready_ratio"] == "1.000000"
    assert payload["required_surface_count"] == "6.000000"
    assert payload["rows"][0]["ready_check_count"] == "10.000000"
    assert payload["rows"][0]["dsn_validator_name"] == "validate_local_postgres_dsn"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)


def test_schema_migration_plan_safety_blocks_nonlocal_backends_and_execution() -> None:
    report = build_report(
        plan("paper_research_packets"),
        plan("paper_recommendation_reports", dsn_validator_name="validate_postgres_dsn"),
        plan("paper_cycle_snapshots", durable_jsonl_fallback_absent=False),
        plan("paper_trade_journal", local_supabase_postgres_only=False),
        plan("paper_nav_snapshots", hosted_database_absent=False),
        plan("paper_operator_evidence", sqlite_absent=False),
    )

    assert report.status == "blocker"
    assert report.ready_count == d("1.000000")
    assert report.blocker_count == d("5.000000")
    assert report.attention_count == ZERO
    assert report.ready_ratio == d("0.166667")
    assert report.missing_required_surface_count == ZERO
    assert report.reason_codes == (
        "local_supabase_postgres_only_missing_blocker",
        "dsn_validator_not_validate_local_postgres_dsn_blocker",
        "durable_jsonl_fallback_present_blocker",
        "hosted_database_plan_present_blocker",
        "sqlite_plan_present_blocker",
        "local_supabase_schema_migration_plan_ready",
    )
    assert tuple(row.status for row in report.rows) == (
        "blocker",
        "blocker",
        "blocker",
        "blocker",
        "blocker",
        "ready",
    )
    assert report.rows[0].migration_surface == "paper_recommendation_reports"
    assert report.rows[0].reason_codes == (
        "dsn_validator_not_validate_local_postgres_dsn_blocker",
    )
    assert report.rows[1].migration_surface == "paper_cycle_snapshots"
    assert report.rows[1].reason_codes == (
        "durable_jsonl_fallback_present_blocker",
    )


def test_schema_migration_plan_safety_blocks_unreported_or_nonpaper_surfaces() -> None:
    module = api()

    report = build_report(
        plan("paper_research_packets"),
        plan("paper_trade_journal", paper_evidence_only=False),
        plan("paper_cycle_snapshots", migration_execution_absent=False),
    )

    assert report.status == "blocker"
    assert report.migration_surface_count == d("3.000000")
    assert report.ready_count == d("1.000000")
    assert report.blocker_count == d("2.000000")
    assert report.missing_required_surface_count == d("3.000000")
    assert report.ready_ratio == d("0.166667")
    assert report.reason_codes == (
        "paper_recommendation_reports_migration_plan_missing_blocker",
        "paper_nav_snapshots_migration_plan_missing_blocker",
        "paper_operator_evidence_migration_plan_missing_blocker",
        "paper_evidence_only_missing_blocker",
        "migration_execution_present_blocker",
        "local_supabase_schema_migration_plan_ready",
    )
    assert report.missing_required_surfaces == (
        "paper_recommendation_reports",
        "paper_nav_snapshots",
        "paper_operator_evidence",
    )
    assert report.reason_code_counts == (
        module.LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount(
            reason_code="paper_recommendation_reports_migration_plan_missing_blocker",
            count=ONE,
            ratio=d("0.166667"),
        ),
        module.LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount(
            reason_code="paper_nav_snapshots_migration_plan_missing_blocker",
            count=ONE,
            ratio=d("0.166667"),
        ),
        module.LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount(
            reason_code="paper_operator_evidence_migration_plan_missing_blocker",
            count=ONE,
            ratio=d("0.166667"),
        ),
        module.LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount(
            reason_code="paper_evidence_only_missing_blocker",
            count=ONE,
            ratio=d("0.166667"),
        ),
        module.LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount(
            reason_code="migration_execution_present_blocker",
            count=ONE,
            ratio=d("0.166667"),
        ),
        module.LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount(
            reason_code="local_supabase_schema_migration_plan_ready",
            count=ONE,
            ratio=d("0.166667"),
        ),
    )


def test_public_dataclasses_are_frozen_exact_decimal_and_hard_flagged() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_CONFIG_VERSION",
        "LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_SAFETY_STATUSES",
        "LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES",
        "LocalSupabaseSchemaMigrationPlanSafetySignal",
        "LocalSupabaseSchemaMigrationPlanSafetyReasonCodeCount",
        "LocalSupabaseSchemaMigrationPlanSafetyReport",
        "LocalSupabaseSchemaMigrationPlanSafetyRow",
        "build_local_supabase_schema_migration_plan_safety_report",
        "local_supabase_schema_migration_plan_safety_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(
        *(plan(surface) for surface in module.LOCAL_SUPABASE_SCHEMA_MIGRATION_PLAN_REQUIRED_SURFACES),
    )
    for value in (
        plan("paper_research_packets"),
        report,
        *report.rows,
        *report.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_ratio")):
                assert type(item) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "blocker"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        plan("paper_research_packets", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        plan("paper_research_packets", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_count must be a Decimal"):
        replace(report, ready_count=1)  # type: ignore[arg-type]


def test_validation_rejects_bad_inputs_duplicate_surfaces_and_timestamps() -> None:
    module = api()

    with pytest.raises(ValueError, match="migration_surface"):
        plan("paper research packets")
    with pytest.raises(ValueError, match="migration_surface"):
        plan("unknown_history")
    with pytest.raises(ValueError, match="local_supabase_postgres_only"):
        plan("paper_research_packets", local_supabase_postgres_only=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dsn_validator_name"):
        plan("paper_research_packets", dsn_validator_name="")
    with pytest.raises(ValueError, match="observed_at"):
        plan("paper_research_packets", observed_at=datetime(2026, 7, 12, 9, 45))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(plan("paper_research_packets"), generated_at=datetime(2026, 7, 12, 10, 0))
    with pytest.raises(ValueError, match="duplicate migration_surface"):
        build_report(plan("paper_research_packets"), plan("paper_research_packets"))
    with pytest.raises(ValueError, match="observed_at"):
        build_report(
            plan("paper_research_packets", observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="plans must be an iterable"):
        module.build_local_supabase_schema_migration_plan_safety_report(
            None,
            generated_at=GENERATED_AT,
        )

    est_generated = datetime(
        2026,
        7,
        12,
        6,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    assert build_report(plan("paper_research_packets"), generated_at=est_generated).generated_at == GENERATED_AT


def test_static_forbidden_writes_clients_live_auth_wallet_order_and_backends_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    assert "validate_local_postgres_dsn" in source
    assert "validate_postgres_dsn" not in source.replace("validate_local_postgres_dsn", "")
    for forbidden in (
        ".json",
        "create_client",
        "supabase_url",
        "remote database",
        "durable file",
        "wallet",
        "private_key",
        "live_trading",
        "auth",
        "order",
        "requests",
        "httpx",
        "socket",
        "open(",
        ".write(",
        "write_text",
        "write_bytes",
        "connect(",
        "execute(",
        "insert(",
        "upsert(",
        "delete(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "redis",
        "pymongo",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
