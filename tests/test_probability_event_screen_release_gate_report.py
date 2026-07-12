from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_screen_release_gate_report as api
from polymarket_alpha_lab.probability_event_screen_release_gate_report import (
    ProbabilityEventScreenReleaseGateInput,
    ProbabilityEventScreenReleaseGateReport,
    RELEASE_GATE_BANDS,
    build_probability_event_screen_release_gate_report,
    probability_event_screen_release_gate_report_digest,
    probability_event_screen_release_gate_report_to_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_release_gate_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def release_input(
    *,
    commit_readiness_ready: bool = True,
    final_review_ready: bool = True,
    operator_runbook_ready: bool = True,
    dashboard_snapshot_ready: bool = True,
    audit_summary_ready: bool = True,
    codegraph_sync_ready: bool = True,
    claude_review_ready: bool = True,
    no_live_execution_surface: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenReleaseGateInput:
    return ProbabilityEventScreenReleaseGateInput(
        commit_readiness_ready=commit_readiness_ready,
        final_review_ready=final_review_ready,
        operator_runbook_ready=operator_runbook_ready,
        dashboard_snapshot_ready=dashboard_snapshot_ready,
        audit_summary_ready=audit_summary_ready,
        codegraph_sync_ready=codegraph_sync_ready,
        claude_review_ready=claude_review_ready,
        no_live_execution_surface=no_live_execution_surface,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    source: ProbabilityEventScreenReleaseGateInput,
) -> ProbabilityEventScreenReleaseGateReport:
    return build_probability_event_screen_release_gate_report(source)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_release_gate_band_vocabulary_is_exact() -> None:
    assert RELEASE_GATE_BANDS == ("ready", "attention", "blocked")


def test_all_release_prerequisites_ready_emits_payload_and_digest() -> None:
    report = build_report(release_input())

    assert is_dataclass(report)
    assert report.release_gate_ready is True
    assert report.release_gate_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "probability_event_screen_release_gate_ready",
    )
    assert report.ready_ratio == ONE
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = probability_event_screen_release_gate_report_to_payload(report)
    assert report.public_payload == payload
    assert payload == {
        "commit_readiness_ready": True,
        "final_review_ready": True,
        "operator_runbook_ready": True,
        "dashboard_snapshot_ready": True,
        "audit_summary_ready": True,
        "codegraph_sync_ready": True,
        "claude_review_ready": True,
        "no_live_execution_surface": True,
        "release_gate_ready": True,
        "release_gate_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_release_gate_ready",
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
    assert probability_event_screen_release_gate_report_digest(report) == expected_digest
    assert_no_runtime_numbers(payload)


def test_missing_required_release_artifacts_block_in_deterministic_order() -> None:
    report = build_report(
        release_input(
            commit_readiness_ready=False,
            final_review_ready=False,
            operator_runbook_ready=False,
            dashboard_snapshot_ready=False,
            audit_summary_ready=False,
            codegraph_sync_ready=False,
            claude_review_ready=False,
        ),
    )

    assert report.release_gate_ready is False
    assert report.release_gate_band == "blocked"
    assert report.ready_ratio == d("0.125000")
    assert report.blocked_reason_codes == (
        "release_gate_commit_readiness_not_ready",
        "release_gate_final_review_not_ready",
        "release_gate_operator_runbook_not_ready",
        "release_gate_dashboard_snapshot_not_ready",
        "release_gate_audit_summary_not_ready",
        "release_gate_codegraph_sync_not_ready",
        "release_gate_claude_review_not_ready",
    )
    assert report.attention_reason_codes == ()
    assert report.public_payload["ready_ratio"] == "0.125000"


def test_live_execution_surface_attention_blocks_release_ready_flag() -> None:
    report = build_report(release_input(no_live_execution_surface=False))

    assert report.release_gate_ready is False
    assert report.release_gate_band == "attention"
    assert report.ready_ratio == d("0.875000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "release_gate_live_execution_surface_detected",
    )


def test_dataclasses_are_frozen_decimal_only_and_flags_are_enforced() -> None:
    source = release_input()
    report = build_report(source)

    assert is_dataclass(ProbabilityEventScreenReleaseGateInput)
    assert is_dataclass(ProbabilityEventScreenReleaseGateReport)
    assert source.__dataclass_params__.frozen
    assert report.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        report.release_gate_band = "blocked"  # type: ignore[misc]

    for field in fields(report):
        value = getattr(report, field.name)
        if field.name == "ready_ratio":
            assert type(value) is Decimal

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenReleaseGateInput):
            pass

    with pytest.raises(ValueError, match="commit_readiness_ready must be a bool"):
        release_input(commit_readiness_ready=ONE)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="no_live_execution_surface must be a bool"):
        release_input(no_live_execution_surface=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        release_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        release_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(report, ready_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="blocked_reason_codes"):
        ProbabilityEventScreenReleaseGateReport(
            commit_readiness_ready=False,
            final_review_ready=True,
            operator_runbook_ready=True,
            dashboard_snapshot_ready=True,
            audit_summary_ready=True,
            codegraph_sync_ready=True,
            claude_review_ready=True,
            no_live_execution_surface=True,
            release_gate_ready=False,
            release_gate_band="blocked",
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
        ProbabilityEventScreenReleaseGateInput,
        ProbabilityEventScreenReleaseGateReport,
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
