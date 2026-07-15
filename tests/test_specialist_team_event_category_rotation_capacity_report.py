from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import inspect
import json
from typing import Any

import pytest

import polymarket_alpha_lab.specialist_team_event_category_rotation_capacity_report as api
from polymarket_alpha_lab.specialist_team_event_category_rotation_capacity_report import (
    SPECIALIST_TEAM_EVENT_CATEGORY_ROTATION_CAPACITY_STATUSES,
    SpecialistTeamEventCategoryRotationCapacityInput,
    SpecialistTeamEventCategoryRotationCapacityReport,
    build_specialist_team_event_category_rotation_capacity_report,
    specialist_team_event_category_rotation_capacity_public_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def rotation_input(
    **overrides: object,
) -> SpecialistTeamEventCategoryRotationCapacityInput:
    values = {
        "team_count": d("6.000000"),
        "category_count": d("4.000000"),
        "overloaded_team_count": d("0.000000"),
        "rotation_slot_count": d("6.000000"),
        "urgent_category_count": d("2.000000"),
    }
    values.update(overrides)
    return SpecialistTeamEventCategoryRotationCapacityInput(**values)


def report(
    **overrides: object,
) -> SpecialistTeamEventCategoryRotationCapacityReport:
    return build_specialist_team_event_category_rotation_capacity_report(
        rotation_input(**overrides),
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def test_builds_ready_report_when_specialist_capacity_covers_categories() -> None:
    summary = report()

    assert is_dataclass(summary)
    assert type(summary) is SpecialistTeamEventCategoryRotationCapacityReport
    assert summary.team_count == d("6.000000")
    assert summary.category_count == d("4.000000")
    assert summary.overloaded_team_count == d("0.000000")
    assert summary.rotation_slot_count == d("6.000000")
    assert summary.urgent_category_count == d("2.000000")
    assert summary.rotation_capacity_status == "ready"
    assert summary.reason_codes == (
        "specialist_team_event_category_rotation_capacity_ready",
    )
    assert summary.manual_next_step == "document_specialist_rotation_capacity_review"
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.payload_digest) == 64


def test_blocks_when_rotation_slots_do_not_cover_urgent_categories() -> None:
    summary = report(
        rotation_slot_count=d("1.000000"),
        urgent_category_count=d("3.000000"),
    )

    assert summary.rotation_capacity_status == "blocked"
    assert summary.reason_codes == (
        "urgent_category_rotation_capacity_shortfall_blocker",
    )
    assert summary.manual_next_step == "escalate_manual_rotation_capacity_review"


def test_attention_when_any_specialist_team_is_overloaded() -> None:
    summary = report(overloaded_team_count=d("2.000000"))

    assert summary.rotation_capacity_status == "attention"
    assert summary.reason_codes == (
        "specialist_team_overload_attention",
    )
    assert summary.manual_next_step == "rebalance_specialist_team_rotation_queue"


def test_attention_when_categories_outnumber_specialist_teams() -> None:
    summary = report(
        team_count=d("3.000000"),
        category_count=d("5.000000"),
        rotation_slot_count=d("5.000000"),
    )

    assert summary.rotation_capacity_status == "attention"
    assert summary.reason_codes == (
        "category_coverage_capacity_attention",
    )
    assert summary.manual_next_step == "assign_additional_specialist_category_coverage"


def test_public_payload_and_digest_are_canonical_decimal_only_and_public_safe() -> None:
    summary = report()
    payload = summary.public_payload

    assert payload == specialist_team_event_category_rotation_capacity_public_payload(
        summary,
    )
    assert payload["team_count"] == "6.000000"
    assert payload["category_count"] == "4.000000"
    assert payload["overloaded_team_count"] == "0.000000"
    assert payload["rotation_slot_count"] == "6.000000"
    assert payload["urgent_category_count"] == "2.000000"
    assert payload["rotation_capacity_status"] == "ready"
    assert payload["reason_codes"] == [
        "specialist_team_event_category_rotation_capacity_ready",
    ]
    assert payload["manual_next_step"] == (
        "document_specialist_rotation_capacity_review"
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == summary.payload_digest
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(payload)
    )

    digest_input = dict(payload)
    digest_input.pop("payload_digest")
    expected_digest = sha256(
        json.dumps(
            digest_input,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert payload["payload_digest"] == expected_digest

    payload_text = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "auth",
        "wallet",
        "key",
        "sign",
        "auto",
        "live",
        "trade",
        "buy",
        "sell",
        "execute",
        "execution",
        "jsonl",
        "persist",
        "crawl",
        "scrape",
    ):
        assert forbidden not in payload_text


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    summary = report()

    with pytest.raises(FrozenInstanceError):
        summary.rotation_capacity_status = "attention"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        rotation_input(team_count=6)

    with pytest.raises(ValueError, match="integer-valued Decimal"):
        rotation_input(category_count=d("4.500000"))

    with pytest.raises(ValueError, match="overloaded_team_count"):
        rotation_input(
            team_count=d("1.000000"),
            overloaded_team_count=d("2.000000"),
        )

    with pytest.raises(ValueError, match="urgent_category_count"):
        rotation_input(
            category_count=d("1.000000"),
            urgent_category_count=d("2.000000"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        replace(rotation_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)

    with pytest.raises(ValueError, match="payload_digest"):
        replace(summary, rotation_capacity_status="attention")


def test_no_io_database_or_execution_surface_is_exposed() -> None:
    assert SPECIALIST_TEAM_EVENT_CATEGORY_ROTATION_CAPACITY_STATUSES == (
        "ready",
        "attention",
        "blocked",
    )

    unsafe_terms = (
        "auth",
        "wallet",
        "key",
        "sign",
        "auto",
        "live",
        "trade",
        "buy",
        "sell",
        "execute",
        "execution",
        "jsonl",
        "persist",
        "crawl",
        "scrape",
        "db",
        "database",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        SpecialistTeamEventCategoryRotationCapacityInput,
        SpecialistTeamEventCategoryRotationCapacityReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    tree = ast.parse(inspect.getsource(api))
    imported_modules = {
        (node.module or "").split(".")[0]
        if isinstance(node, ast.ImportFrom)
        else alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [node])
        if (
            isinstance(node, ast.Import)
            or not (node.module or "").startswith("__future__")
        )
    }
    assert imported_modules <= {
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_calls = {
        "connect",
        "open",
        "request",
        "urlopen",
        "dump",
        "dumps" if False else "load",
    }
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not forbidden_calls & called_names
