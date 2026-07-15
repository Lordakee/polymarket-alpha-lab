from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_joint_gate_consistency_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab.probability_event_joint_gate_consistency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def gate(**overrides: object) -> Any:
    module = api()
    values = {
        "event_ref": "event-alpha",
        "source_quality_status": "pass",
        "memory_policy_status": "allow",
        "cost_gate_status": "pass",
        "team_route_status": "pass",
        "probability_edge": d("0.040000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ProbabilityEventJointGateConsistencyInput(**values)


def report(*inputs: object, config: object | None = None) -> Any:
    module = api()
    return module.build_probability_event_joint_gate_consistency_report(
        inputs,
        config=config,
    )


def walk_payload(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_payload(item)
        return
    yield value


def assert_decimal_only(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"unexpected numeric value {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_decimal_only(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_decimal_only(item)


def test_any_block_forces_joint_status_blocked_and_lists_inconsistent_gates() -> None:
    module = api()
    result = report(
        gate(event_ref="event-pass"),
        gate(
            event_ref="event-source-block",
            source_quality_status="blocked",
            memory_policy_status="allow",
            cost_gate_status="pass",
            team_route_status="pass",
            probability_edge=d("0.990000"),
        ),
        gate(
            event_ref="event-route-block",
            source_quality_status="pass",
            memory_policy_status="allow",
            cost_gate_status="pass",
            team_route_status="block",
        ),
    )

    assert type(result) is module.ProbabilityEventJointGateConsistencyReport
    assert is_dataclass(result)
    assert result.input_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("0.000000")
    assert result.blocked_count == d("2.000000")
    assert result.inconsistent_input_count == d("2.000000")
    assert result.joint_status == "blocked"
    assert result.inconsistent_gates == (
        "source_quality_status",
        "team_route_status",
    )
    assert result.reason_codes == (
        "joint_gate_has_blocked_inputs",
        "source_quality_status_blocked",
        "team_route_status_blocked",
    )
    assert result.manual_next_step == "manual_review_blocked_gate_before_edge_use"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.event_ref for row in result.rows) == (
        "event-route-block",
        "event-source-block",
        "event-pass",
    )
    route_block, source_block, passed = result.rows
    assert route_block.joint_status == "blocked"
    assert route_block.inconsistent_gates == ("team_route_status",)
    assert route_block.reason_codes == ("team_route_status_blocked",)
    assert source_block.joint_status == "blocked"
    assert source_block.inconsistent_gates == ("source_quality_status",)
    assert source_block.reason_codes == ("source_quality_status_blocked",)
    assert passed.joint_status == "pass"
    assert passed.inconsistent_gates == ()
    assert passed.reason_codes == ("joint_gate_consistency_pass",)


def test_watch_cannot_be_overridden_by_high_edge() -> None:
    result = report(
        gate(
            event_ref="event-high-edge-watch",
            source_quality_status="watch",
            memory_policy_status="allow",
            cost_gate_status="pass",
            team_route_status="pass",
            probability_edge=d("0.990000"),
        ),
        gate(
            event_ref="event-memory-throttle-high-edge",
            source_quality_status="pass",
            memory_policy_status="throttle",
            cost_gate_status="pass",
            team_route_status="pass",
            probability_edge=d("0.980000"),
        ),
    )

    assert result.joint_status == "watch"
    assert result.input_count == d("2.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("2.000000")
    assert result.blocked_count == d("0.000000")
    assert result.inconsistent_input_count == d("2.000000")
    assert result.max_probability_edge == d("0.990000")
    assert result.inconsistent_gates == (
        "source_quality_status",
        "memory_policy_status",
    )
    assert result.reason_codes == (
        "joint_gate_has_watch_inputs",
        "watch_status_requires_manual_review",
        "memory_policy_status_watch",
        "source_quality_status_watch",
    )
    assert result.manual_next_step == "manual_review_watch_gate_before_edge_use"
    assert tuple(row.joint_status for row in result.rows) == ("watch", "watch")
    assert tuple(row.probability_edge for row in result.rows) == (
        d("0.990000"),
        d("0.980000"),
    )
    assert all(
        "watch_status_requires_manual_review" in row.reason_codes
        for row in result.rows
    )


def test_empty_and_all_pass_reports_are_readonly_and_digest_stable() -> None:
    empty = report()
    passed = report(
        gate(event_ref="event-beta", probability_edge=d("0.010000")),
        gate(event_ref="event-alpha", probability_edge=d("0.020000")),
    )
    repeated = report(
        gate(event_ref="event-alpha", probability_edge=d("0.020000")),
        gate(event_ref="event-beta", probability_edge=d("0.010000")),
    )

    assert empty.input_count == d("0.000000")
    assert empty.joint_status == "blocked"
    assert empty.inconsistent_gates == ()
    assert empty.reason_codes == ("missing_probability_event_joint_gate_inputs",)
    assert empty.manual_next_step == "manual_collect_joint_gate_inputs"
    assert empty.rows == ()

    assert passed.joint_status == "pass"
    assert passed.pass_count == d("2.000000")
    assert passed.watch_count == d("0.000000")
    assert passed.blocked_count == d("0.000000")
    assert passed.inconsistent_input_count == d("0.000000")
    assert passed.max_probability_edge == d("0.020000")
    assert passed.inconsistent_gates == ()
    assert passed.reason_codes == ("joint_gate_consistency_pass",)
    assert passed.manual_next_step == "continue_report_only_probability_event_review"
    assert passed.derived_validation_digest == repeated.derived_validation_digest
    assert len(passed.derived_validation_digest) == 64
    assert set(passed.derived_validation_digest) <= set("0123456789abcdef")
    assert all(row.paper_only and row.report_only and row.readonly for row in passed.rows)


def test_payload_is_json_ready_safe_immutable_and_decimal_stringified() -> None:
    module = api()
    result = report(
        gate(
            event_ref="unsafe raw market_id=abc wallet order live auth token",
            source_quality_status="watch",
            probability_edge=d("0.990000"),
        ),
    )

    payload = module.probability_event_joint_gate_consistency_report_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)
    rendered_lower = rendered.casefold()

    assert payload["max_probability_edge"] == "0.990000"
    assert payload["joint_status"] == "watch"
    assert payload["rows"][0]["event_ref_digest"] == result.rows[0].event_ref_digest
    assert "unsafe raw" not in rendered_lower
    assert not any(type(value) in (int, float) for value in walk_payload(payload))
    for forbidden in (
        "wallet",
        "order",
        "live",
        "auth",
        "token",
        "market_id",
        "recommend",
        "buy",
        "sell",
        "trade",
    ):
        assert forbidden not in rendered_lower
    with pytest.raises(TypeError, match="immutable"):
        payload["joint_status"] = "blocked"
    with pytest.raises(TypeError, match="immutable"):
        payload["rows"].append({})


def test_validation_rejects_bad_statuses_decimal_types_flags_and_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_quality_status"):
        gate(source_quality_status="allow")
    with pytest.raises(ValueError, match="memory_policy_status"):
        gate(memory_policy_status="watch")
    with pytest.raises(ValueError, match="cost_gate_status"):
        gate(cost_gate_status="block")
    with pytest.raises(ValueError, match="team_route_status"):
        gate(team_route_status="blocked")
    with pytest.raises(ValueError, match="probability_edge"):
        gate(probability_edge=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="probability_edge"):
        gate(probability_edge=0.1)
    with pytest.raises(ValueError, match="paper_only"):
        gate(paper_only=1)
    with pytest.raises(ValueError, match="paper_only"):
        gate(paper_only=False)

    result = report(gate(source_quality_status="blocked"))
    with pytest.raises(FrozenInstanceError):
        result.joint_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="joint_status"):
        replace(result, joint_status="pass")
    with pytest.raises(ValueError, match="inconsistent_gates"):
        replace(result, inconsistent_gates=())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    assert_decimal_only(result)
    assert module.DEFAULT_PROBABILITY_EVENT_JOINT_GATE_CONSISTENCY_CONFIG_VERSION == (
        "probability-event-joint-gate-consistency-report-v0"
    )


def test_module_scope_excludes_persistence_and_execution_surfaces() -> None:
    source = MODULE_PATH.read_text()
    lowered = source.casefold()
    tree = ast.parse(source)

    for forbidden in (
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "requests",
        "urllib",
        "websocket",
        "private_key",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "auth",
        "live",
    ):
        assert forbidden not in lowered

    imported_roots = {
        alias.name.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", maxsplit=1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
