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


MODULE_NAME = "polymarket_alpha_lab.local_supabase_evidence_persistence_readiness_report"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/local_supabase_evidence_persistence_readiness_report.py",
)
GENERATED_AT = datetime(2026, 7, 12, 9, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 12, 8, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def plan(
    surface: str,
    *,
    local_supabase_postgres_planned: bool = True,
    dsn_validator_name: str = "validate_local_postgres_dsn",
    durable_jsonl_file_fallback_absent: bool = True,
    hosted_database_absent: bool = True,
    sqlite_absent: bool = True,
    redis_absent: bool = True,
    mongo_absent: bool = True,
    sqlalchemy_absent: bool = True,
    observed_at: datetime = OBSERVED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return api().LocalSupabaseEvidencePersistencePlanSignal(
        evidence_surface=surface,
        local_supabase_postgres_planned=local_supabase_postgres_planned,
        dsn_validator_name=dsn_validator_name,
        durable_jsonl_file_fallback_absent=durable_jsonl_file_fallback_absent,
        hosted_database_absent=hosted_database_absent,
        sqlite_absent=sqlite_absent,
        redis_absent=redis_absent,
        mongo_absent=mongo_absent,
        sqlalchemy_absent=sqlalchemy_absent,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*plans: Any, generated_at: datetime = GENERATED_AT) -> Any:
    return api().build_local_supabase_evidence_persistence_readiness_report(
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


def test_evidence_persistence_readiness_requires_all_six_history_surfaces() -> None:
    module = api()

    report = build_report(
        plan("candidate_history"),
        plan("gate_history"),
        plan("source_history"),
        plan("memory_history"),
        plan("cost_history"),
        plan("operator_packet_history"),
    )

    assert module.LOCAL_SUPABASE_EVIDENCE_PERSISTENCE_REQUIRED_SURFACES == (
        "candidate_history",
        "gate_history",
        "source_history",
        "memory_history",
        "cost_history",
        "operator_packet_history",
    )
    assert module.LOCAL_SUPABASE_EVIDENCE_PERSISTENCE_READINESS_STATUSES == (
        "ready",
        "attention",
        "blocker",
    )
    assert report.status == "ready"
    assert report.evidence_surface_count == d("6.000000")
    assert report.ready_count == d("6.000000")
    assert report.attention_count == ZERO
    assert report.blocker_count == ZERO
    assert report.ready_ratio == ONE
    assert report.required_surface_count == d("6.000000")
    assert report.missing_required_surface_count == ZERO
    assert report.reason_codes == ("local_supabase_evidence_persistence_ready",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.evidence_surface for row in report.rows) == (
        "candidate_history",
        "gate_history",
        "source_history",
        "memory_history",
        "cost_history",
        "operator_packet_history",
    )
    assert all(row.status == "ready" for row in report.rows)
    assert all(row.ready_check_count == d("8.000000") for row in report.rows)
    assert all(row.required_check_count == d("8.000000") for row in report.rows)
    assert all(row.readiness_ratio == ONE for row in report.rows)
    assert all(
        row.dsn_validator_name == "validate_local_postgres_dsn"
        for row in report.rows
    )

    payload = module.local_supabase_evidence_persistence_readiness_report_payload(
        report,
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["ready_ratio"] == "1.000000"
    assert payload["required_surface_count"] == "6.000000"
    assert payload["rows"][0]["ready_check_count"] == "8.000000"
    assert payload["rows"][0]["dsn_validator_name"] == "validate_local_postgres_dsn"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)


def test_evidence_persistence_readiness_blocks_missing_surfaces_and_bad_backends() -> None:
    report = build_report(
        plan("candidate_history"),
        plan("gate_history", dsn_validator_name="validate_postgres_dsn"),
        plan("source_history", durable_jsonl_file_fallback_absent=False),
        plan("memory_history", local_supabase_postgres_planned=False),
        plan("cost_history", hosted_database_absent=False),
        plan("operator_packet_history", sqlite_absent=False),
    )

    assert report.status == "blocker"
    assert report.ready_count == d("1.000000")
    assert report.blocker_count == d("5.000000")
    assert report.attention_count == ZERO
    assert report.ready_ratio == d("0.166667")
    assert report.missing_required_surface_count == ZERO
    assert report.reason_codes == (
        "local_supabase_postgres_plan_missing_blocker",
        "dsn_validator_not_validate_local_postgres_dsn_blocker",
        "durable_jsonl_file_fallback_present_blocker",
        "hosted_database_plan_present_blocker",
        "sqlite_plan_present_blocker",
        "local_supabase_evidence_persistence_ready",
    )
    assert tuple(row.status for row in report.rows) == (
        "blocker",
        "blocker",
        "blocker",
        "blocker",
        "blocker",
        "ready",
    )
    assert report.rows[0].evidence_surface == "gate_history"
    assert report.rows[0].reason_codes == (
        "dsn_validator_not_validate_local_postgres_dsn_blocker",
    )
    assert report.rows[1].evidence_surface == "source_history"
    assert report.rows[1].reason_codes == (
        "durable_jsonl_file_fallback_present_blocker",
    )


def test_evidence_persistence_readiness_blocks_unreported_required_surfaces() -> None:
    module = api()

    report = build_report(plan("candidate_history"), plan("source_history"))

    assert report.status == "blocker"
    assert report.evidence_surface_count == d("2.000000")
    assert report.ready_count == d("2.000000")
    assert report.blocker_count == ZERO
    assert report.missing_required_surface_count == d("4.000000")
    assert report.ready_ratio == d("0.333333")
    assert report.reason_codes == (
        "gate_history_persistence_plan_missing_blocker",
        "memory_history_persistence_plan_missing_blocker",
        "cost_history_persistence_plan_missing_blocker",
        "operator_packet_history_persistence_plan_missing_blocker",
        "local_supabase_evidence_persistence_ready",
    )
    assert report.missing_required_surfaces == (
        "gate_history",
        "memory_history",
        "cost_history",
        "operator_packet_history",
    )
    assert report.reason_code_counts == (
        module.LocalSupabaseEvidencePersistenceReadinessReasonCodeCount(
            reason_code="gate_history_persistence_plan_missing_blocker",
            count=ONE,
            ratio=d("0.166667"),
        ),
        module.LocalSupabaseEvidencePersistenceReadinessReasonCodeCount(
            reason_code="memory_history_persistence_plan_missing_blocker",
            count=ONE,
            ratio=d("0.166667"),
        ),
        module.LocalSupabaseEvidencePersistenceReadinessReasonCodeCount(
            reason_code="cost_history_persistence_plan_missing_blocker",
            count=ONE,
            ratio=d("0.166667"),
        ),
        module.LocalSupabaseEvidencePersistenceReadinessReasonCodeCount(
            reason_code="operator_packet_history_persistence_plan_missing_blocker",
            count=ONE,
            ratio=d("0.166667"),
        ),
        module.LocalSupabaseEvidencePersistenceReadinessReasonCodeCount(
            reason_code="local_supabase_evidence_persistence_ready",
            count=d("2.000000"),
            ratio=d("0.333333"),
        ),
    )


def test_public_dataclasses_are_frozen_exact_decimal_and_hard_flagged() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_LOCAL_SUPABASE_EVIDENCE_PERSISTENCE_READINESS_CONFIG_VERSION",
        "LOCAL_SUPABASE_EVIDENCE_PERSISTENCE_READINESS_STATUSES",
        "LOCAL_SUPABASE_EVIDENCE_PERSISTENCE_REQUIRED_SURFACES",
        "LocalSupabaseEvidencePersistencePlanSignal",
        "LocalSupabaseEvidencePersistenceReadinessReasonCodeCount",
        "LocalSupabaseEvidencePersistenceReadinessReport",
        "LocalSupabaseEvidencePersistenceReadinessRow",
        "build_local_supabase_evidence_persistence_readiness_report",
        "local_supabase_evidence_persistence_readiness_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(*(plan(surface) for surface in module.LOCAL_SUPABASE_EVIDENCE_PERSISTENCE_REQUIRED_SURFACES))
    for value in (
        plan("candidate_history"),
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
        plan("candidate_history", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        plan("candidate_history", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_count must be a Decimal"):
        replace(report, ready_count=1)  # type: ignore[arg-type]


def test_validation_rejects_bad_inputs_duplicate_surfaces_and_timestamps() -> None:
    module = api()

    with pytest.raises(ValueError, match="evidence_surface"):
        plan("candidate history")
    with pytest.raises(ValueError, match="evidence_surface"):
        plan("unknown_history")
    with pytest.raises(ValueError, match="local_supabase_postgres_planned"):
        plan("candidate_history", local_supabase_postgres_planned=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dsn_validator_name"):
        plan("candidate_history", dsn_validator_name="")
    with pytest.raises(ValueError, match="observed_at"):
        plan("candidate_history", observed_at=datetime(2026, 7, 12, 8, 45))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(plan("candidate_history"), generated_at=datetime(2026, 7, 12, 9, 0))
    with pytest.raises(ValueError, match="duplicate evidence_surface"):
        build_report(plan("candidate_history"), plan("candidate_history"))
    with pytest.raises(ValueError, match="observed_at"):
        build_report(
            plan("candidate_history", observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="plans must be an iterable"):
        module.build_local_supabase_evidence_persistence_readiness_report(
            None,
            generated_at=GENERATED_AT,
        )

    est_generated = datetime(
        2026,
        7,
        12,
        5,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    assert build_report(plan("candidate_history"), generated_at=est_generated).generated_at == GENERATED_AT


def test_static_forbidden_durable_fallbacks_and_database_clients_are_absent() -> None:
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
        "order",
        "trade",
        "auth",
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
