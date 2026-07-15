from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_outcome_dependency_collision_report import (
    PROBABILITY_EVENT_OUTCOME_DEPENDENCY_COLLISION_REPORT_VERSION,
    ProbabilityEventOutcomeDependencyCollisionInput,
    ProbabilityEventOutcomeDependencyCollisionReport,
    build_probability_event_outcome_dependency_collision_report,
    probability_event_outcome_dependency_collision_report_digest,
    probability_event_outcome_dependency_collision_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_outcome_dependency_collision_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def collision_input(
    **overrides: object,
) -> ProbabilityEventOutcomeDependencyCollisionInput:
    values = {
        "outcome_count": d("4"),
        "shared_dependency_count": d("1"),
        "conflicting_dependency_count": d("0"),
        "official_dependency_count": d("1"),
        "collision_threshold_count": d("2"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventOutcomeDependencyCollisionInput(**values)


def report(**overrides: object) -> ProbabilityEventOutcomeDependencyCollisionReport:
    return build_probability_event_outcome_dependency_collision_report(
        collision_input(**overrides),
    )


def test_clear_report_payload_digest_and_public_schema() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventOutcomeDependencyCollisionReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert first.config_version == (
        PROBABILITY_EVENT_OUTCOME_DEPENDENCY_COLLISION_REPORT_VERSION
    )
    assert first.collision_status == "clear"
    assert first.reason_codes == ("no_dependency_collision_detected",)
    assert first.manual_next_step == (
        "Continue read-only monitoring; no manual collision review is required."
    )
    assert first.payload_digest == second.payload_digest
    assert probability_event_outcome_dependency_collision_report_digest(first) == (
        first.payload_digest
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    payload = probability_event_outcome_dependency_collision_report_payload(first)
    assert payload == first.public_payload
    assert payload == {
        "config_version": "probability-event-outcome-dependency-collision-v0",
        "outcome_count": "4.000000",
        "shared_dependency_count": "1.000000",
        "conflicting_dependency_count": "0.000000",
        "official_dependency_count": "1.000000",
        "collision_threshold_count": "2.000000",
        "collision_status": "clear",
        "reason_codes": ("no_dependency_collision_detected",),
        "manual_next_step": (
            "Continue read-only monitoring; no manual collision review is required."
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": first.payload_digest,
    }
    json.dumps(payload, sort_keys=True)
    expected_digest = sha256(
        json.dumps(
            {**payload, "payload_digest": ""},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert _float_or_int_paths(payload) == ()

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["collision_status"] = "blocked"


def test_collision_blocks_when_conflicts_meet_threshold() -> None:
    result = report(
        shared_dependency_count=d("3"),
        conflicting_dependency_count=d("2"),
        official_dependency_count=d("0"),
        collision_threshold_count=d("2"),
    )

    assert result.collision_status == "blocked"
    assert result.reason_codes == (
        "conflicting_dependency_count_at_or_above_threshold",
        "shared_dependencies_without_official_dependency",
    )
    assert result.manual_next_step == (
        "Pause any automated action path and complete manual outcome dependency review."
    )
    assert result.public_payload["reason_codes"] == result.reason_codes


def test_watch_when_shared_or_conflicting_dependencies_need_manual_review() -> None:
    shared = report(
        shared_dependency_count=d("2"),
        conflicting_dependency_count=d("0"),
        official_dependency_count=d("0"),
        collision_threshold_count=d("3"),
    )
    conflict_below_threshold = report(
        shared_dependency_count=d("2"),
        conflicting_dependency_count=d("1"),
        official_dependency_count=d("1"),
        collision_threshold_count=d("3"),
    )

    assert shared.collision_status == "watch"
    assert shared.reason_codes == (
        "shared_dependencies_without_official_dependency",
    )
    assert shared.manual_next_step == (
        "Manually review outcome dependency mapping before escalating this event."
    )
    assert conflict_below_threshold.collision_status == "watch"
    assert conflict_below_threshold.reason_codes == (
        "conflicting_dependency_count_below_threshold",
    )


def test_frozen_decimal_only_exact_types_and_hard_flags() -> None:
    input_value = collision_input()
    result = report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.outcome_count = d("5")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.collision_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventOutcomeDependencyCollisionInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventOutcomeDependencyCollisionReport):
            pass

    with pytest.raises(ValueError, match="outcome_count must be exactly Decimal"):
        collision_input(outcome_count=4)
    with pytest.raises(ValueError, match="outcome_count must be a whole count"):
        collision_input(outcome_count=d("4.5"))
    with pytest.raises(ValueError, match="shared_dependency_count cannot exceed"):
        collision_input(shared_dependency_count=d("5"))
    with pytest.raises(ValueError, match="conflicting_dependency_count cannot exceed"):
        collision_input(conflicting_dependency_count=d("2"), shared_dependency_count=d("1"))
    with pytest.raises(ValueError, match="collision_threshold_count must be positive"):
        collision_input(collision_threshold_count=d("0"))
    with pytest.raises(ValueError, match="paper_only"):
        collision_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="collision_status must match"):
        replace(result, collision_status="blocked")
    with pytest.raises(ValueError, match="payload_digest"):
        probability_event_outcome_dependency_collision_report_payload(
            replace(result, payload_digest="0" * 64),
        )

    hints = get_type_hints(ProbabilityEventOutcomeDependencyCollisionReport)
    for field in fields(ProbabilityEventOutcomeDependencyCollisionReport):
        value = getattr(result, field.name)
        if field.name.endswith("_count"):
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_is_readonly_report_only_and_has_no_live_execution_or_io_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "web3",
        "private_key",
        "wallet",
        "authentication",
        "auth",
        "signature",
        "live_trading",
        "order execution",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "jsonl",
        "database",
        "network",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "post",
        "put",
        "rollback",
        "sell",
        "send",
        "sign",
        "upsert",
        "write",
        "write_text",
        "write_bytes",
    }
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not imported_roots.intersection(forbidden_imports)
    assert not call_names.intersection(forbidden_call_names)
    assert float_constants == []


def _float_or_int_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if type(value) in (int, float, Decimal):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_or_int_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, (list, tuple)):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_or_int_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
