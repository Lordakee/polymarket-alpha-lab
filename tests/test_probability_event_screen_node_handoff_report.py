from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_screen_node_handoff_report as api
from polymarket_alpha_lab.probability_event_screen_node_handoff_report import (
    HANDOFF_BANDS,
    ProbabilityEventScreenNodeHandoffInput,
    ProbabilityEventScreenNodeHandoffReport,
    build_probability_event_screen_node_handoff_report,
    probability_event_screen_node_handoff_report_digest,
    probability_event_screen_node_handoff_report_to_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_node_handoff_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def handoff_input(
    *,
    end_to_end_ready: bool = True,
    system_health_ready: bool = True,
    validation_matrix_ready: bool = True,
    release_gate_ready: bool = True,
    operator_runbook_ready: bool = True,
    learning_dashboard_ready: bool = True,
    supabase_persistence_ready: bool = True,
    github_push_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenNodeHandoffInput:
    return ProbabilityEventScreenNodeHandoffInput(
        end_to_end_ready=end_to_end_ready,
        system_health_ready=system_health_ready,
        validation_matrix_ready=validation_matrix_ready,
        release_gate_ready=release_gate_ready,
        operator_runbook_ready=operator_runbook_ready,
        learning_dashboard_ready=learning_dashboard_ready,
        supabase_persistence_ready=supabase_persistence_ready,
        github_push_ready=github_push_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    source: ProbabilityEventScreenNodeHandoffInput,
) -> ProbabilityEventScreenNodeHandoffReport:
    return build_probability_event_screen_node_handoff_report(source)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_handoff_band_vocabulary_is_exact() -> None:
    assert HANDOFF_BANDS == ("ready", "attention", "blocked")


def test_all_handoff_prerequisites_ready_emits_payload_and_digest() -> None:
    report = build_report(handoff_input())

    assert is_dataclass(report)
    assert report.node_handoff_ready is True
    assert report.handoff_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "probability_event_screen_node_handoff_ready",
    )
    assert report.ready_ratio == ONE
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = probability_event_screen_node_handoff_report_to_payload(report)
    assert report.public_payload == payload
    assert payload == {
        "end_to_end_ready": True,
        "system_health_ready": True,
        "validation_matrix_ready": True,
        "release_gate_ready": True,
        "operator_runbook_ready": True,
        "learning_dashboard_ready": True,
        "supabase_persistence_ready": True,
        "github_push_ready": True,
        "node_handoff_ready": True,
        "handoff_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_node_handoff_ready",
        ],
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert report.digest == expected_digest
    assert probability_event_screen_node_handoff_report_digest(report) == expected_digest
    assert_no_runtime_numbers(payload)


def test_missing_blocking_handoff_prerequisites_block_in_deterministic_order() -> None:
    report = build_report(
        handoff_input(
            end_to_end_ready=False,
            system_health_ready=False,
            validation_matrix_ready=False,
            release_gate_ready=False,
            operator_runbook_ready=False,
            learning_dashboard_ready=False,
            supabase_persistence_ready=False,
            github_push_ready=False,
        ),
    )

    assert report.node_handoff_ready is False
    assert report.handoff_band == "blocked"
    assert report.ready_ratio == ZERO
    assert report.blocked_reason_codes == (
        "node_handoff_end_to_end_not_ready",
        "node_handoff_system_health_not_ready",
        "node_handoff_validation_matrix_not_ready",
        "node_handoff_release_gate_not_ready",
        "node_handoff_operator_runbook_not_ready",
        "node_handoff_supabase_persistence_not_ready",
        "node_handoff_github_push_not_ready",
    )
    assert report.attention_reason_codes == ()
    assert report.public_payload["ready_ratio"] == "0.000000"


def test_learning_dashboard_gap_is_attention_not_blocking() -> None:
    report = build_report(handoff_input(learning_dashboard_ready=False))

    assert report.node_handoff_ready is False
    assert report.handoff_band == "attention"
    assert report.ready_ratio == d("0.875000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "node_handoff_learning_dashboard_not_ready",
    )


def test_blocking_gaps_take_precedence_over_attention_gaps() -> None:
    report = build_report(
        handoff_input(
            release_gate_ready=False,
            learning_dashboard_ready=False,
        ),
    )

    assert report.node_handoff_ready is False
    assert report.handoff_band == "blocked"
    assert report.blocked_reason_codes == ("node_handoff_release_gate_not_ready",)
    assert report.attention_reason_codes == ()
    assert report.ready_ratio == d("0.750000")


def test_dataclasses_are_frozen_decimal_only_and_flags_are_enforced() -> None:
    source = handoff_input()
    report = build_report(source)

    assert is_dataclass(ProbabilityEventScreenNodeHandoffInput)
    assert is_dataclass(ProbabilityEventScreenNodeHandoffReport)
    assert source.__dataclass_params__.frozen
    assert report.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        report.handoff_band = "blocked"  # type: ignore[misc]

    for field in fields(report):
        value = getattr(report, field.name)
        if field.name == "ready_ratio":
            assert type(value) is Decimal

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenNodeHandoffInput):
            pass

    with pytest.raises(ValueError, match="end_to_end_ready must be a bool"):
        handoff_input(end_to_end_ready=ONE)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="github_push_ready must be a bool"):
        handoff_input(github_push_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        handoff_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        handoff_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(report, ready_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="blocked_reason_codes"):
        ProbabilityEventScreenNodeHandoffReport(
            end_to_end_ready=False,
            system_health_ready=True,
            validation_matrix_ready=True,
            release_gate_ready=True,
            operator_runbook_ready=True,
            learning_dashboard_ready=True,
            supabase_persistence_ready=True,
            github_push_ready=True,
            node_handoff_ready=False,
            handoff_band="blocked",
            blocked_reason_codes=(),
            attention_reason_codes=(),
            ready_ratio=d("0.875000"),
        )


def test_public_api_stays_readonly_report_only_paper_only_and_side_effect_free() -> None:
    forbidden_fragments = (
        "auth",
        "wallet",
        "database",
        "network",
        "request",
        "http",
        "broker",
        "private_key",
        "api_key",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ProbabilityEventScreenNodeHandoffInput,
        ProbabilityEventScreenNodeHandoffReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.partition(".")[0])

    assert not {
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
    } & imported_roots
    assert ".open(" not in source
    assert "open(" not in source
    assert "live_trading" not in source
    assert "private_key" not in source
