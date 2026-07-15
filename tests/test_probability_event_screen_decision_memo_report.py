from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_screen_decision_memo_report as api
from polymarket_alpha_lab.probability_event_screen_decision_memo_report import (
    ProbabilityEventScreenDecisionMemoInput,
    ProbabilityEventScreenDecisionMemoReport,
    build_probability_event_screen_decision_memo_report,
    probability_event_screen_decision_memo_report_digest,
    probability_event_screen_decision_memo_report_to_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_decision_memo_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def memo_input(
    *,
    screen_digest_present: bool = True,
    recommendation_digest_present: bool = True,
    daily_brief_digest_present: bool = True,
    due_diligence_depth_ready: bool = True,
    information_gap_band: str = "ready",
    liquidity_exit_ready: bool = True,
    team_scorecard_ready: bool = True,
    operator_safety_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenDecisionMemoInput:
    return ProbabilityEventScreenDecisionMemoInput(
        screen_digest_present=screen_digest_present,
        recommendation_digest_present=recommendation_digest_present,
        daily_brief_digest_present=daily_brief_digest_present,
        due_diligence_depth_ready=due_diligence_depth_ready,
        information_gap_band=information_gap_band,
        liquidity_exit_ready=liquidity_exit_ready,
        team_scorecard_ready=team_scorecard_ready,
        operator_safety_ready=operator_safety_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    source: ProbabilityEventScreenDecisionMemoInput,
) -> ProbabilityEventScreenDecisionMemoReport:
    return build_probability_event_screen_decision_memo_report(source)


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_ready_inputs_build_decision_memo_payload_and_digest() -> None:
    report = build_report(memo_input())

    assert is_dataclass(report)
    assert report.decision_memo_ready is True
    assert report.memo_status_band == "ready"
    assert report.missing_artifact_count == ZERO
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "probability_event_screen_decision_memo_ready",
    )
    assert report.ready_ratio == ONE
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = probability_event_screen_decision_memo_report_to_payload(report)
    assert report.public_payload == payload
    assert payload == {
        "screen_digest_present": True,
        "recommendation_digest_present": True,
        "daily_brief_digest_present": True,
        "due_diligence_depth_ready": True,
        "information_gap_band": "ready",
        "liquidity_exit_ready": True,
        "team_scorecard_ready": True,
        "operator_safety_ready": True,
        "decision_memo_ready": True,
        "memo_status_band": "ready",
        "missing_artifact_count": "0.000000",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_decision_memo_ready",
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
    assert probability_event_screen_decision_memo_report_digest(report) == expected_digest
    assert_no_int_or_float_values(payload)


def test_missing_artifacts_block_decision_memo_and_count_each_gap() -> None:
    report = build_report(
        memo_input(
            screen_digest_present=False,
            recommendation_digest_present=False,
            daily_brief_digest_present=False,
            due_diligence_depth_ready=False,
            information_gap_band="blocker",
            liquidity_exit_ready=False,
            team_scorecard_ready=False,
            operator_safety_ready=False,
        ),
    )

    assert report.decision_memo_ready is False
    assert report.memo_status_band == "blocked"
    assert report.missing_artifact_count == d("8.000000")
    assert report.ready_ratio == ZERO
    assert report.blocked_reason_codes == (
        "decision_memo_screen_digest_missing",
        "decision_memo_recommendation_digest_missing",
        "decision_memo_daily_brief_digest_missing",
        "decision_memo_due_diligence_depth_not_ready",
        "decision_memo_information_gap_blocker",
        "decision_memo_liquidity_exit_not_ready",
        "decision_memo_team_scorecard_not_ready",
        "decision_memo_operator_safety_not_ready",
    )
    assert report.attention_reason_codes == ()
    assert report.public_payload["missing_artifact_count"] == "8.000000"
    assert report.public_payload["ready_ratio"] == "0.000000"


def test_attention_gap_keeps_memo_in_attention_until_resolved() -> None:
    report = build_report(memo_input(information_gap_band="attention"))

    assert report.decision_memo_ready is False
    assert report.memo_status_band == "attention"
    assert report.missing_artifact_count == ZERO
    assert report.ready_ratio == d("0.875000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "decision_memo_information_gap_attention",
    )


def test_dataclasses_are_frozen_and_input_types_flags_are_enforced() -> None:
    report = build_report(memo_input())

    with pytest.raises(FrozenInstanceError):
        report.memo_status_band = "attention"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenDecisionMemoInput):
            pass

    with pytest.raises(ValueError, match="screen_digest_present must be a bool"):
        memo_input(screen_digest_present=ONE)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="information_gap_band"):
        memo_input(information_gap_band="BLOCKER")

    with pytest.raises(ValueError, match="paper_only"):
        memo_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        memo_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="missing_artifact_count must be a Decimal"):
        replace(report, missing_artifact_count=0)  # type: ignore[arg-type]


def test_public_api_stays_readonly_report_only_paper_only_and_side_effect_free() -> None:
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
        "order_execution",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        ProbabilityEventScreenDecisionMemoInput,
        ProbabilityEventScreenDecisionMemoReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "psycopg",
            "supabase",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "request",
            "urlopen",
            "send",
            "submit",
            "place_order",
            "cancel_order",
            "sign",
        },
    )


def test_digest_changes_when_readiness_inputs_change() -> None:
    ready = build_report(memo_input())
    attention = build_report(memo_input(information_gap_band="attention"))

    assert ready.digest != attention.digest
    assert ready.public_payload != attention.public_payload
