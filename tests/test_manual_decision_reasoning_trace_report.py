from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.manual_decision_reasoning_trace_report as api
from polymarket_alpha_lab.manual_decision_reasoning_trace_report import (
    ManualDecisionReasoningTraceInput,
    ManualDecisionReasoningTraceReport,
    build_manual_decision_reasoning_trace_report,
    manual_decision_reasoning_trace_report_digest,
    manual_decision_reasoning_trace_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/manual_decision_reasoning_trace_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def trace_input(
    *,
    screen_digest_present: Decimal = ONE,
    research_digest_present: Decimal = ONE,
    source_reliability_digest_present: Decimal = ONE,
    cost_digest_present: Decimal = ONE,
    team_memory_digest_present: Decimal = ONE,
    position_sizing_digest_present: Decimal = ONE,
    operator_safety_digest_present: Decimal = ONE,
    decision_summary_redacted: Decimal = ONE,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ManualDecisionReasoningTraceInput:
    return ManualDecisionReasoningTraceInput(
        screen_digest_present=screen_digest_present,
        research_digest_present=research_digest_present,
        source_reliability_digest_present=source_reliability_digest_present,
        cost_digest_present=cost_digest_present,
        team_memory_digest_present=team_memory_digest_present,
        position_sizing_digest_present=position_sizing_digest_present,
        operator_safety_digest_present=operator_safety_digest_present,
        decision_summary_redacted=decision_summary_redacted,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    trace: ManualDecisionReasoningTraceInput,
) -> ManualDecisionReasoningTraceReport:
    return build_manual_decision_reasoning_trace_report(trace)


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_all_reasoning_trace_inputs_ready_for_manual_decision() -> None:
    readiness = report(trace_input())

    assert is_dataclass(readiness)
    assert readiness.trace_ready is True
    assert readiness.missing_digest_count == ZERO
    assert readiness.redaction_ready is True
    assert readiness.blocked_reason_codes == ()
    assert readiness.attention_reason_codes == ("manual_decision_reasoning_trace_ready",)
    assert readiness.ready_ratio == ONE
    assert readiness.paper_only is True
    assert readiness.report_only is True
    assert readiness.readonly is True

    payload = manual_decision_reasoning_trace_report_payload(readiness)
    assert payload == readiness.public_payload
    assert payload == {
        "trace_ready": True,
        "missing_digest_count": "0.000000",
        "redaction_ready": True,
        "blocked_reason_codes": [],
        "attention_reason_codes": ["manual_decision_reasoning_trace_ready"],
        "ready_ratio": "1.000000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert_digest(manual_decision_reasoning_trace_report_digest(readiness))
    assert readiness.digest == manual_decision_reasoning_trace_report_digest(readiness)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_float_or_int_values(payload)


def test_missing_required_digest_blocks_trace_and_counts_missing_digest_inputs() -> None:
    readiness = report(
        trace_input(
            screen_digest_present=ZERO,
            research_digest_present=d("0.500000"),
            cost_digest_present=ZERO,
            team_memory_digest_present=d("0.750000"),
        ),
    )

    assert readiness.trace_ready is False
    assert readiness.missing_digest_count == d("2.000000")
    assert readiness.redaction_ready is True
    assert readiness.blocked_reason_codes == (
        "manual_decision_reasoning_trace_screen_digest_missing",
        "manual_decision_reasoning_trace_cost_digest_missing",
    )
    assert readiness.attention_reason_codes == (
        "manual_decision_reasoning_trace_research_digest_attention",
        "manual_decision_reasoning_trace_team_memory_digest_attention",
    )
    assert readiness.ready_ratio == d("0.625000")

    payload = readiness.public_payload
    assert payload["trace_ready"] is False
    assert payload["missing_digest_count"] == "2.000000"
    assert payload["ready_ratio"] == "0.625000"
    assert_no_float_or_int_values(payload)


def test_unredacted_decision_summary_blocks_public_trace_release() -> None:
    readiness = report(
        trace_input(
            decision_summary_redacted=ZERO,
            operator_safety_digest_present=d("0.500000"),
        ),
    )

    assert readiness.trace_ready is False
    assert readiness.missing_digest_count == ZERO
    assert readiness.redaction_ready is False
    assert readiness.blocked_reason_codes == (
        "manual_decision_reasoning_trace_redaction_missing",
    )
    assert readiness.attention_reason_codes == (
        "manual_decision_reasoning_trace_operator_safety_digest_attention",
    )
    assert readiness.ready_ratio == d("0.812500")
    assert "decision_summary" not in json.dumps(readiness.public_payload, sort_keys=True)


def test_dataclasses_are_frozen_decimal_only_and_flags_are_enforced() -> None:
    readiness = report(trace_input())

    with pytest.raises(FrozenInstanceError):
        readiness.trace_ready = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ManualDecisionReasoningTraceInput):
            pass

    with pytest.raises(ValueError, match="screen_digest_present must be a Decimal"):
        trace_input(screen_digest_present=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="screen_digest_present must be between"):
        trace_input(screen_digest_present=d("1.100000"))

    with pytest.raises(ValueError, match="paper_only"):
        trace_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        trace_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(readiness, readonly=False)

    with pytest.raises(ValueError, match="blocked reports require blocked_reason_codes"):
        replace(readiness, trace_ready=False, blocked_reason_codes=())

    with pytest.raises(ValueError, match="ready reports must not include blocked_reason_codes"):
        replace(
            readiness,
            blocked_reason_codes=(
                "manual_decision_reasoning_trace_screen_digest_missing",
            ),
        )


def test_public_api_excludes_live_trading_auth_wallet_and_side_effect_surfaces() -> None:
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "database",
        "network",
        "request",
        "http",
        "broker",
        "private_key",
        "api_key",
        "order",
        "execution",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (ManualDecisionReasoningTraceInput, ManualDecisionReasoningTraceReport):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "web3",
            "ccxt",
            "subprocess",
        },
    )
