from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_screen_push_readiness_report as api
from polymarket_alpha_lab.probability_event_screen_push_readiness_report import (
    PROBABILITY_EVENT_SCREEN_PUSH_READINESS_REPORT_VERSION,
    PUSH_READINESS_BANDS,
    ProbabilityEventScreenPushReadinessInput,
    ProbabilityEventScreenPushReadinessReport,
    build_probability_event_screen_push_readiness_report,
    probability_event_screen_push_readiness_report_digest,
    probability_event_screen_push_readiness_report_to_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_push_readiness_report.py",
)
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def push_input(
    *,
    release_gate_ready: bool = True,
    commit_readiness_ready: bool = True,
    validation_matrix_ready: bool = True,
    codegraph_sync_ready: bool = True,
    claude_review_ready: bool = True,
    github_remote_ready: bool = True,
    worktree_clean_after_commit_ready: bool = True,
    no_live_execution_surface: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenPushReadinessInput:
    return ProbabilityEventScreenPushReadinessInput(
        release_gate_ready=release_gate_ready,
        commit_readiness_ready=commit_readiness_ready,
        validation_matrix_ready=validation_matrix_ready,
        codegraph_sync_ready=codegraph_sync_ready,
        claude_review_ready=claude_review_ready,
        github_remote_ready=github_remote_ready,
        worktree_clean_after_commit_ready=worktree_clean_after_commit_ready,
        no_live_execution_surface=no_live_execution_surface,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    source: ProbabilityEventScreenPushReadinessInput,
) -> ProbabilityEventScreenPushReadinessReport:
    return build_probability_event_screen_push_readiness_report(source)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_push_readiness_band_vocabulary_is_exact() -> None:
    assert PUSH_READINESS_BANDS == ("ready", "attention", "blocked")


def test_all_push_prerequisites_ready_emits_payload_digest_and_schema() -> None:
    report = build_report(push_input())

    assert is_dataclass(report)
    assert report.push_readiness_ready is True
    assert report.push_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "probability_event_screen_push_readiness_ready",
    )
    assert report.ready_ratio == ONE
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = probability_event_screen_push_readiness_report_to_payload(report)
    assert report.public_payload == payload
    assert payload == {
        "config_version": PROBABILITY_EVENT_SCREEN_PUSH_READINESS_REPORT_VERSION,
        "release_gate_ready": True,
        "commit_readiness_ready": True,
        "validation_matrix_ready": True,
        "codegraph_sync_ready": True,
        "claude_review_ready": True,
        "github_remote_ready": True,
        "worktree_clean_after_commit_ready": True,
        "no_live_execution_surface": True,
        "push_readiness_ready": True,
        "push_band": "ready",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_push_readiness_ready",
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
    assert probability_event_screen_push_readiness_report_digest(report) == expected_digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_missing_required_push_prerequisites_block_in_deterministic_order() -> None:
    report = build_report(
        push_input(
            release_gate_ready=False,
            commit_readiness_ready=False,
            validation_matrix_ready=False,
            codegraph_sync_ready=False,
            claude_review_ready=False,
            github_remote_ready=False,
            worktree_clean_after_commit_ready=False,
        ),
    )

    assert report.push_readiness_ready is False
    assert report.push_band == "blocked"
    assert report.ready_ratio == d("0.125000")
    assert report.blocked_reason_codes == (
        "push_release_gate_not_ready",
        "push_commit_readiness_not_ready",
        "push_validation_matrix_not_ready",
        "push_codegraph_sync_not_ready",
        "push_claude_review_not_ready",
        "push_github_remote_not_ready",
        "push_worktree_dirty_after_commit",
    )
    assert report.attention_reason_codes == ()
    assert report.public_payload["ready_ratio"] == "0.125000"


def test_live_execution_surface_attention_blocks_push_ready_flag() -> None:
    report = build_report(push_input(no_live_execution_surface=False))

    assert report.push_readiness_ready is False
    assert report.push_band == "attention"
    assert report.ready_ratio == d("0.875000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "push_live_execution_surface_detected",
    )


def test_dataclasses_are_frozen_decimal_only_and_flags_are_enforced() -> None:
    source = push_input()
    report = build_report(source)

    assert is_dataclass(ProbabilityEventScreenPushReadinessInput)
    assert is_dataclass(ProbabilityEventScreenPushReadinessReport)
    assert source.__dataclass_params__.frozen
    assert report.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        report.push_band = "blocked"  # type: ignore[misc]

    for field in fields(report):
        value = getattr(report, field.name)
        if field.name == "ready_ratio":
            assert type(value) is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenPushReadinessInput):
            pass

    with pytest.raises(ValueError, match="release_gate_ready must be a bool"):
        push_input(release_gate_ready=ONE)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="no_live_execution_surface must be a bool"):
        push_input(no_live_execution_surface=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        push_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        push_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(report, ready_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_ratio must be a Decimal"):
        replace(report, ready_ratio=_DecimalSubclass("1.000000"))


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="blocked_reason_codes"):
        ProbabilityEventScreenPushReadinessReport(
            config_version=PROBABILITY_EVENT_SCREEN_PUSH_READINESS_REPORT_VERSION,
            release_gate_ready=False,
            commit_readiness_ready=True,
            validation_matrix_ready=True,
            codegraph_sync_ready=True,
            claude_review_ready=True,
            github_remote_ready=True,
            worktree_clean_after_commit_ready=True,
            no_live_execution_surface=True,
            push_readiness_ready=False,
            push_band="blocked",
            blocked_reason_codes=(),
            attention_reason_codes=(),
            ready_ratio=d("0.875000"),
        )

    with pytest.raises(ValueError, match="ready_ratio"):
        ProbabilityEventScreenPushReadinessReport(
            config_version=PROBABILITY_EVENT_SCREEN_PUSH_READINESS_REPORT_VERSION,
            release_gate_ready=True,
            commit_readiness_ready=True,
            validation_matrix_ready=True,
            codegraph_sync_ready=True,
            claude_review_ready=True,
            github_remote_ready=True,
            worktree_clean_after_commit_ready=True,
            no_live_execution_surface=True,
            push_readiness_ready=True,
            push_band="ready",
            blocked_reason_codes=(),
            attention_reason_codes=(
                "probability_event_screen_push_readiness_ready",
            ),
            ready_ratio=d("0.500000"),
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
        ProbabilityEventScreenPushReadinessInput,
        ProbabilityEventScreenPushReadinessReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    forbidden_calls = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "place_order",
        "post",
        "put",
        "replace",
        "rollback",
        "send",
        "submit_order",
        "trade",
        "write",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.partition(".")[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    assert not {
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
    } & imported_roots
    assert ".open(" not in source
    assert "open(" not in source
    assert "live_trading" not in source
    assert "private_key" not in source
