from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_screen_daily_brief_report as api
from polymarket_alpha_lab.probability_event_screen_daily_brief_report import (
    ProbabilityEventScreenDailyBriefInput,
    ProbabilityEventScreenDailyBriefReport,
    build_probability_event_screen_daily_brief_report,
    probability_event_screen_daily_brief_report_digest,
    probability_event_screen_daily_brief_report_to_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_daily_brief_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def brief_input(
    *,
    total_candidate_count: Decimal = d("10.000000"),
    ready_for_manual_review_count: Decimal = d("7.000000"),
    watch_count: Decimal = d("3.000000"),
    blocked_count: Decimal = ZERO,
    average_edge_to_threshold_probability: Decimal = d("0.030000"),
    average_source_reliability_score: Decimal = d("0.900000"),
    average_cost_burden_ratio: Decimal = d("0.200000"),
    highest_priority_team_count: Decimal = d("2.000000"),
    operator_safety_ready: Decimal = ONE,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventScreenDailyBriefInput:
    return ProbabilityEventScreenDailyBriefInput(
        total_candidate_count=total_candidate_count,
        ready_for_manual_review_count=ready_for_manual_review_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_edge_to_threshold_probability=average_edge_to_threshold_probability,
        average_source_reliability_score=average_source_reliability_score,
        average_cost_burden_ratio=average_cost_burden_ratio,
        highest_priority_team_count=highest_priority_team_count,
        operator_safety_ready=operator_safety_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    daily_input: ProbabilityEventScreenDailyBriefInput,
) -> ProbabilityEventScreenDailyBriefReport:
    return build_probability_event_screen_daily_brief_report(daily_input)


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_ready_daily_brief_payload_and_digest_are_stable() -> None:
    daily_brief = report(brief_input())

    assert is_dataclass(daily_brief)
    assert daily_brief.daily_brief_ready is True
    assert daily_brief.headline_status == "ready_for_manual_review"
    assert daily_brief.blocked_reason_codes == ()
    assert daily_brief.attention_reason_codes == (
        "probability_event_screen_daily_watch_candidates_present",
    )
    assert daily_brief.ready_ratio == d("0.700000")
    assert daily_brief.paper_only is True
    assert daily_brief.report_only is True
    assert daily_brief.readonly is True

    payload = probability_event_screen_daily_brief_report_to_payload(daily_brief)
    assert daily_brief.public_payload == payload
    assert payload == {
        "total_candidate_count": "10.000000",
        "ready_for_manual_review_count": "7.000000",
        "watch_count": "3.000000",
        "blocked_count": "0.000000",
        "average_edge_to_threshold_probability": "0.030000",
        "average_source_reliability_score": "0.900000",
        "average_cost_burden_ratio": "0.200000",
        "highest_priority_team_count": "2.000000",
        "operator_safety_ready": "1.000000",
        "daily_brief_ready": True,
        "headline_status": "ready_for_manual_review",
        "blocked_reason_codes": [],
        "attention_reason_codes": [
            "probability_event_screen_daily_watch_candidates_present",
        ],
        "ready_ratio": "0.700000",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert daily_brief.digest == expected_digest
    assert probability_event_screen_daily_brief_report_digest(daily_brief) == (
        expected_digest
    )
    assert_no_int_or_float_values(payload)


def test_blocked_daily_brief_reports_all_blocking_reasons() -> None:
    daily_brief = report(
        brief_input(
            total_candidate_count=d("8.000000"),
            ready_for_manual_review_count=d("2.000000"),
            watch_count=d("4.000000"),
            blocked_count=d("2.000000"),
            average_edge_to_threshold_probability=d("-0.010000"),
            average_source_reliability_score=d("0.400000"),
            average_cost_burden_ratio=d("0.900000"),
            highest_priority_team_count=ZERO,
            operator_safety_ready=ZERO,
        ),
    )

    assert daily_brief.daily_brief_ready is False
    assert daily_brief.headline_status == "blocked"
    assert daily_brief.ready_ratio == d("0.250000")
    assert daily_brief.blocked_reason_codes == (
        "probability_event_screen_daily_blocked_candidates_present",
        "probability_event_screen_daily_edge_below_threshold",
        "probability_event_screen_daily_source_reliability_block",
        "probability_event_screen_daily_cost_burden_block",
        "probability_event_screen_daily_no_high_priority_team",
        "probability_event_screen_daily_operator_safety_block",
    )
    assert daily_brief.attention_reason_codes == (
        "probability_event_screen_daily_ready_ratio_watch",
        "probability_event_screen_daily_watch_candidates_present",
    )

    payload = daily_brief.public_payload
    assert payload["headline_status"] == "blocked"
    assert payload["blocked_reason_codes"] == list(daily_brief.blocked_reason_codes)
    assert payload["attention_reason_codes"] == list(daily_brief.attention_reason_codes)
    assert_no_int_or_float_values(payload)


def test_watch_daily_brief_has_attention_reasons_without_blockers() -> None:
    daily_brief = report(
        brief_input(
            total_candidate_count=d("5.000000"),
            ready_for_manual_review_count=d("2.000000"),
            watch_count=d("3.000000"),
            average_edge_to_threshold_probability=ZERO,
            average_source_reliability_score=d("0.650000"),
            average_cost_burden_ratio=d("0.700000"),
        ),
    )

    assert daily_brief.daily_brief_ready is False
    assert daily_brief.headline_status == "attention_required"
    assert daily_brief.ready_ratio == d("0.400000")
    assert daily_brief.blocked_reason_codes == ()
    assert daily_brief.attention_reason_codes == (
        "probability_event_screen_daily_ready_ratio_watch",
        "probability_event_screen_daily_watch_candidates_present",
        "probability_event_screen_daily_edge_at_threshold",
        "probability_event_screen_daily_source_reliability_watch",
        "probability_event_screen_daily_cost_burden_watch",
    )


def test_empty_candidate_brief_blocks_meeting() -> None:
    daily_brief = report(
        brief_input(
            total_candidate_count=ZERO,
            ready_for_manual_review_count=ZERO,
            watch_count=ZERO,
            average_edge_to_threshold_probability=ZERO,
            highest_priority_team_count=ZERO,
        ),
    )

    assert daily_brief.daily_brief_ready is False
    assert daily_brief.headline_status == "blocked"
    assert daily_brief.ready_ratio == ZERO
    assert daily_brief.blocked_reason_codes == (
        "probability_event_screen_daily_no_candidates",
        "probability_event_screen_daily_no_high_priority_team",
    )
    assert daily_brief.attention_reason_codes == (
        "probability_event_screen_daily_ready_ratio_watch",
        "probability_event_screen_daily_edge_at_threshold",
    )


def test_dataclasses_are_frozen_decimal_only_and_flags_are_enforced() -> None:
    daily_brief = report(brief_input())

    with pytest.raises(FrozenInstanceError):
        daily_brief.headline_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventScreenDailyBriefInput):
            pass

    with pytest.raises(ValueError, match="total_candidate_count must be a Decimal"):
        brief_input(total_candidate_count=10)  # type: ignore[arg-type]

    with pytest.raises(
        ValueError,
        match="average_edge_to_threshold_probability must be a Decimal",
    ):
        brief_input(average_edge_to_threshold_probability=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="candidate counts must sum"):
        brief_input(
            total_candidate_count=d("3.000000"),
            ready_for_manual_review_count=ONE,
            watch_count=ONE,
            blocked_count=ZERO,
        )

    with pytest.raises(ValueError, match="operator_safety_ready"):
        brief_input(operator_safety_ready=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only"):
        brief_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        brief_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(daily_brief, readonly=False)


def test_public_api_stays_readonly_report_only_and_side_effect_free() -> None:
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
        ProbabilityEventScreenDailyBriefInput,
        ProbabilityEventScreenDailyBriefReport,
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
            "sqlalchemy",
            "psycopg",
            "supabase",
            "web3",
            "ccxt",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "execute_order",
            "place_order",
            "sign_order",
            "submit_order",
            "insert",
            "update",
            "delete",
        },
    )
