from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.operator_candidate_review_budget_allocation_report import (
    OperatorCandidateReviewBudgetAllocationReport,
    build_operator_candidate_review_budget_allocation_report,
    operator_candidate_review_budget_allocation_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/operator_candidate_review_budget_allocation_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def test_capacity_covers_all_candidates_and_prioritizes_manual_review() -> None:
    report = build_operator_candidate_review_budget_allocation_report(
        candidate_count=d("6"),
        high_priority_count=d("2"),
        manual_review_minutes_available=d("90"),
        average_review_minutes_required=d("15"),
        blocked_candidate_count=d("0"),
    )
    payload = operator_candidate_review_budget_allocation_report_payload(report)
    json.dumps(payload, sort_keys=True)

    assert type(report) is OperatorCandidateReviewBudgetAllocationReport
    assert report.budget_status == "sufficient"
    assert report.review_capacity_count == d("6")
    assert report.reason_codes == (
        "operator_candidate_review_budget_allocation_capacity_sufficient",
    )
    assert report.manual_next_step == (
        "review_all_candidates_in_priority_order_without_budget_reallocation"
    )
    assert report.public_payload == {
        "candidate_count": d("6"),
        "high_priority_count": d("2"),
        "manual_review_minutes_available": d("90"),
        "average_review_minutes_required": d("15"),
        "blocked_candidate_count": d("0"),
        "budget_status": "sufficient",
        "review_capacity_count": d("6"),
        "reason_codes": (
            "operator_candidate_review_budget_allocation_capacity_sufficient",
        ),
        "manual_next_step": (
            "review_all_candidates_in_priority_order_without_budget_reallocation"
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert len(report.payload_digest) == 64
    assert payload["candidate_count"] == "6"
    assert payload["review_capacity_count"] == "6"
    assert payload["payload_digest"] == report.payload_digest
    assert payload["public_payload"]["review_capacity_count"] == "6"
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_limited_budget_blocks_excess_candidates_but_covers_high_priority() -> None:
    report = build_operator_candidate_review_budget_allocation_report(
        candidate_count=d("10"),
        high_priority_count=d("3"),
        manual_review_minutes_available=d("75"),
        average_review_minutes_required=d("15"),
        blocked_candidate_count=d("1"),
    )

    assert report.budget_status == "limited"
    assert report.review_capacity_count == d("5")
    assert report.reason_codes == (
        "operator_candidate_review_budget_allocation_capacity_limited",
        "operator_candidate_review_budget_allocation_blocked_candidates_present",
    )
    assert report.manual_next_step == (
        "review_high_priority_candidates_then_defer_remaining_candidates"
    )


def test_budget_is_blocked_when_high_priority_candidates_exceed_capacity() -> None:
    report = build_operator_candidate_review_budget_allocation_report(
        candidate_count=d("8"),
        high_priority_count=d("4"),
        manual_review_minutes_available=d("45"),
        average_review_minutes_required=d("15"),
        blocked_candidate_count=d("0"),
    )

    assert report.budget_status == "blocked"
    assert report.review_capacity_count == d("3")
    assert report.reason_codes == (
        "operator_candidate_review_budget_allocation_high_priority_over_capacity",
    )
    assert report.manual_next_step == (
        "escalate_manual_review_budget_before_candidate_decisions"
    )


def test_zero_candidates_reports_idle_readonly_budget() -> None:
    report = build_operator_candidate_review_budget_allocation_report(
        candidate_count=d("0"),
        high_priority_count=d("0"),
        manual_review_minutes_available=d("30"),
        average_review_minutes_required=d("10"),
        blocked_candidate_count=d("0"),
    )

    assert report.budget_status == "idle"
    assert report.review_capacity_count == d("0")
    assert report.reason_codes == (
        "operator_candidate_review_budget_allocation_no_candidates",
    )
    assert report.manual_next_step == "no_manual_review_allocation_required"


def test_report_contract_is_frozen_decimal_only_and_requires_hard_flags() -> None:
    report = build_operator_candidate_review_budget_allocation_report(
        candidate_count=d("6"),
        high_priority_count=d("2"),
        manual_review_minutes_available=d("90"),
        average_review_minutes_required=d("15"),
        blocked_candidate_count=d("0"),
    )

    with pytest.raises(FrozenInstanceError):
        report.budget_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="candidate_count"):
        build_operator_candidate_review_budget_allocation_report(
            candidate_count=6,  # type: ignore[arg-type]
            high_priority_count=d("2"),
            manual_review_minutes_available=d("90"),
            average_review_minutes_required=d("15"),
            blocked_candidate_count=d("0"),
        )
    with pytest.raises(ValueError, match="candidate_count"):
        build_operator_candidate_review_budget_allocation_report(
            candidate_count=_DecimalSubclass("6"),
            high_priority_count=d("2"),
            manual_review_minutes_available=d("90"),
            average_review_minutes_required=d("15"),
            blocked_candidate_count=d("0"),
        )
    with pytest.raises(ValueError, match="average_review_minutes_required"):
        build_operator_candidate_review_budget_allocation_report(
            candidate_count=d("6"),
            high_priority_count=d("2"),
            manual_review_minutes_available=d("90"),
            average_review_minutes_required=d("0"),
            blocked_candidate_count=d("0"),
        )
    with pytest.raises(ValueError, match="high_priority_count"):
        build_operator_candidate_review_budget_allocation_report(
            candidate_count=d("2"),
            high_priority_count=d("3"),
            manual_review_minutes_available=d("90"),
            average_review_minutes_required=d("15"),
            blocked_candidate_count=d("0"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        build_operator_candidate_review_budget_allocation_report(
            candidate_count=d("6"),
            high_priority_count=d("2"),
            manual_review_minutes_available=d("90"),
            average_review_minutes_required=d("15"),
            blocked_candidate_count=d("0"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_payload_rejects_mutated_digest_and_public_numerics() -> None:
    report = build_operator_candidate_review_budget_allocation_report(
        candidate_count=d("6"),
        high_priority_count=d("2"),
        manual_review_minutes_available=d("90"),
        average_review_minutes_required=d("15"),
        blocked_candidate_count=d("0"),
    )
    payload = operator_candidate_review_budget_allocation_report_payload(report)

    tampered = dict(payload)
    tampered["review_capacity_count"] = "5"
    with pytest.raises(ValueError, match="payload_digest"):
        operator_candidate_review_budget_allocation_report_payload(tampered)

    with pytest.raises(ValueError, match="public payload numerics"):
        operator_candidate_review_budget_allocation_report_payload(
            {
                **payload,
                "candidate_count": 6,
            },
        )


def test_owned_module_has_no_live_auth_wallet_execution_or_file_persistence_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "key",
        "sign",
        "execution",
        "trade",
        "order",
        "jsonl",
        "persist",
        "database",
        "network",
        "socket",
        "subprocess",
        "open(",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
