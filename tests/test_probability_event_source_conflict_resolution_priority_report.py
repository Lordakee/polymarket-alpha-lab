from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "probability_event_source_conflict_resolution_priority_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_source_conflict_resolution_priority_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def report_input(**overrides: object) -> Any:
    module = api()
    values = {
        "conflict_count": d("0.000000"),
        "official_conflict_count": d("0.000000"),
        "source_freshness_gap_hours": d("0.000000"),
        "market_move_probability": d("0.000000"),
        "manual_owner_assigned": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ProbabilityEventSourceConflictResolutionPriorityInput(**values)


def build_report(**overrides: object) -> Any:
    module = api()
    return module.build_probability_event_source_conflict_resolution_priority_report(
        report_input(**overrides),
    )


def expected_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned["payload_digest"] = ""
    return sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def test_official_conflict_gets_critical_priority_and_owner_assignment_step() -> None:
    module = api()
    result = build_report(
        conflict_count=d("2.000000"),
        official_conflict_count=d("1.000000"),
        source_freshness_gap_hours=d("30.000000"),
        market_move_probability=d("0.120000"),
        manual_owner_assigned=False,
    )

    assert type(result) is module.ProbabilityEventSourceConflictResolutionPriorityReport
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen is True
    assert result.priority_status == "critical"
    assert result.reason_codes == (
        "official_conflict_present",
        "source_conflict_present",
        "source_freshness_gap_critical",
        "market_move_watch",
        "manual_owner_missing",
    )
    assert (
        result.manual_next_step
        == "assign_owner_for_official_conflict_reconciliation"
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = module.probability_event_source_conflict_resolution_priority_report_payload(
        result,
    )
    assert payload == result.public_payload
    assert payload == {
        "config_version": "probability-event-source-conflict-resolution-priority-v0",
        "priority_status": "critical",
        "conflict_count": "2.000000",
        "official_conflict_count": "1.000000",
        "source_freshness_gap_hours": "30.000000",
        "market_move_probability": "0.120000",
        "manual_owner_assigned": False,
        "reason_codes": result.reason_codes,
        "manual_next_step": "assign_owner_for_official_conflict_reconciliation",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": result.payload_digest,
    }
    assert result.payload_digest == expected_digest(dict(payload))
    assert (
        module.probability_event_source_conflict_resolution_priority_report_digest(
            result,
        )
        == result.payload_digest
    )
    json.dumps(payload, sort_keys=True)
    assert _float_or_int_paths(payload) == ()

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["priority_status"] = "low"


def test_conflict_cluster_with_owner_is_high_priority_report_only() -> None:
    result = build_report(
        conflict_count=d("3.000000"),
        official_conflict_count=d("0.000000"),
        source_freshness_gap_hours=d("12.000000"),
        market_move_probability=d("0.080000"),
        manual_owner_assigned=True,
    )

    assert result.priority_status == "high"
    assert result.reason_codes == (
        "source_conflict_cluster",
        "source_freshness_gap_watch",
        "market_move_watch",
        "manual_owner_assigned",
    )
    assert (
        result.manual_next_step
        == "owner_prioritizes_source_reconciliation_before_report_refresh"
    )
    assert result.public_payload["priority_status"] == "high"
    assert result.public_payload["payload_digest"] == result.payload_digest


def test_clear_inputs_stay_low_priority_without_requiring_manual_owner() -> None:
    result = build_report(manual_owner_assigned=False)

    assert result.priority_status == "low"
    assert result.reason_codes == ("no_source_conflict_detected",)
    assert result.manual_next_step == "continue_readonly_monitoring"
    assert result.public_payload["manual_owner_assigned"] is False
    assert result.public_payload["conflict_count"] == "0.000000"


def test_frozen_decimal_only_exact_types_hard_flags_and_tamper_checks() -> None:
    module = api()
    input_value = report_input()
    result = build_report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.conflict_count = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.priority_status = "high"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(module.ProbabilityEventSourceConflictResolutionPriorityInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(module.ProbabilityEventSourceConflictResolutionPriorityReport):
            pass

    with pytest.raises(ValueError, match="conflict_count"):
        report_input(conflict_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="official_conflict_count"):
        report_input(official_conflict_count=d("1.500000"))
    with pytest.raises(ValueError, match="source_freshness_gap_hours"):
        report_input(source_freshness_gap_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="market_move_probability"):
        report_input(market_move_probability=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_move_probability"):
        report_input(market_move_probability=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="manual_owner_assigned"):
        report_input(manual_owner_assigned=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        report_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="priority_status"):
        replace(result, priority_status="medium")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("manual_owner_missing",))
    with pytest.raises(ValueError, match="payload_digest"):
        module.probability_event_source_conflict_resolution_priority_report_payload(
            replace(result, payload_digest="0" * 64),
        )

    hints = get_type_hints(module.ProbabilityEventSourceConflictResolutionPriorityReport)
    for field in fields(module.ProbabilityEventSourceConflictResolutionPriorityReport):
        value = getattr(result, field.name)
        if field.name in {
            "conflict_count",
            "official_conflict_count",
            "source_freshness_gap_hours",
            "market_move_probability",
        }:
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_scope_is_readonly_report_only_and_has_no_io_surface() -> None:
    module = api()

    assert module.__all__ == (
        "PROBABILITY_EVENT_SOURCE_CONFLICT_RESOLUTION_PRIORITY_REPORT_VERSION",
        "PROBABILITY_EVENT_SOURCE_CONFLICT_RESOLUTION_PRIORITY_STATUSES",
        "ProbabilityEventSourceConflictResolutionPriorityInput",
        "ProbabilityEventSourceConflictResolutionPriorityReport",
        "build_probability_event_source_conflict_resolution_priority_report",
        "probability_event_source_conflict_resolution_priority_report_digest",
        "probability_event_source_conflict_resolution_priority_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden_text in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "web3",
        "private_key",
        "signing",
        "wallet",
        "auth",
        "live",
        "execution",
    ):
        assert forbidden_text not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "aiohttp",
        "asyncpg",
        "boto3",
        "httpx",
        "pathlib",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "write",
                "write_text",
                "write_bytes",
            }
    assert imported_roots.isdisjoint(forbidden_import_roots)


def _float_or_int_paths(value: object, prefix: str = "$") -> tuple[str, ...]:
    paths: list[str] = []
    if type(value) in (float, int):
        paths.append(prefix)
    elif isinstance(value, dict):
        for item_key, item_value in value.items():
            paths.extend(_float_or_int_paths(item_value, f"{prefix}.{item_key}"))
    elif isinstance(value, tuple | list):
        for index, item_value in enumerate(value):
            paths.extend(_float_or_int_paths(item_value, f"{prefix}[{index}]"))
    return tuple(paths)
