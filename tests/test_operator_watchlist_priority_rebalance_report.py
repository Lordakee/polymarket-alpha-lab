from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.operator_watchlist_priority_rebalance_report import (
    DEFAULT_OPERATOR_WATCHLIST_PRIORITY_REBALANCE_REPORT_CONFIG_VERSION,
    OperatorWatchlistPriorityRebalanceInput,
    OperatorWatchlistPriorityRebalanceReport,
    build_operator_watchlist_priority_rebalance_report,
    operator_watchlist_priority_rebalance_report_digest,
    operator_watchlist_priority_rebalance_report_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 10, 15, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/operator_watchlist_priority_rebalance_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(
    *,
    candidate_count: Decimal = d("8.000000"),
    high_edge_count: Decimal = d("4.000000"),
    stale_count: Decimal = d("2.000000"),
    blocked_count: Decimal = d("1.000000"),
    manual_capacity_slots: Decimal = d("3.000000"),
    time_budget_minutes: Decimal = d("90.000000"),
    generated_at: datetime = GENERATED_AT,
) -> OperatorWatchlistPriorityRebalanceReport:
    inputs = OperatorWatchlistPriorityRebalanceInput(
        candidate_count=candidate_count,
        high_edge_count=high_edge_count,
        stale_count=stale_count,
        blocked_count=blocked_count,
        manual_capacity_slots=manual_capacity_slots,
        time_budget_minutes=time_budget_minutes,
    )
    return build_operator_watchlist_priority_rebalance_report(
        inputs,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_blocked_rebalance_report_prioritizes_blocker_clearance_before_edges() -> None:
    report = build_report(
        candidate_count=d("12.000000"),
        high_edge_count=d("5.000000"),
        stale_count=d("3.000000"),
        blocked_count=d("2.000000"),
        manual_capacity_slots=d("3.000000"),
        time_budget_minutes=d("90.000000"),
    )

    assert report.config_version == (
        DEFAULT_OPERATOR_WATCHLIST_PRIORITY_REBALANCE_REPORT_CONFIG_VERSION
    )
    assert report.rebalance_status == "blocked"
    assert report.priority_queue_action == "clear_blockers_before_rebalance"
    assert report.manual_next_step == "resolve_blocked_watchlist_items_before_review"
    assert report.reason_codes == (
        "operator_watchlist_blocked_items_present",
        "operator_watchlist_high_edge_backlog",
        "operator_watchlist_stale_items_present",
        "operator_watchlist_manual_capacity_constrained",
    )
    assert report.candidate_count == d("12.000000")
    assert report.high_edge_count == d("5.000000")
    assert report.stale_count == d("3.000000")
    assert report.blocked_count == d("2.000000")
    assert report.manual_capacity_slots == d("3.000000")
    assert report.time_budget_minutes == d("90.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == operator_watchlist_priority_rebalance_report_payload(report)
    assert payload["candidate_count"] == "12.000000"
    assert payload["high_edge_count"] == "5.000000"
    assert payload["stale_count"] == "3.000000"
    assert payload["blocked_count"] == "2.000000"
    assert payload["manual_capacity_slots"] == "3.000000"
    assert payload["time_budget_minutes"] == "90.000000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["payload_digest"] == (
        operator_watchlist_priority_rebalance_report_digest(report)
    )
    assert report.payload_digest == payload["payload_digest"]
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_report_escalates_capacity_constrained_high_edge_queue() -> None:
    report = build_report(
        candidate_count=d("9.000000"),
        high_edge_count=d("4.000000"),
        stale_count=ZERO,
        blocked_count=ZERO,
        manual_capacity_slots=d("2.000000"),
        time_budget_minutes=d("80.000000"),
    )

    assert report.rebalance_status == "watch"
    assert report.priority_queue_action == "rebalance_high_edge_candidates_first"
    assert report.manual_next_step == "review_high_edge_candidates_within_capacity"
    assert report.reason_codes == (
        "operator_watchlist_high_edge_backlog",
        "operator_watchlist_manual_capacity_constrained",
    )


def test_pass_report_continues_current_watchlist_when_capacity_covers_queue() -> None:
    report = build_report(
        candidate_count=d("2.000000"),
        high_edge_count=d("1.000000"),
        stale_count=ZERO,
        blocked_count=ZERO,
        manual_capacity_slots=d("4.000000"),
        time_budget_minutes=d("60.000000"),
    )

    assert report.rebalance_status == "pass"
    assert report.priority_queue_action == "maintain_current_priority_queue"
    assert report.manual_next_step == "continue_operator_watchlist_monitoring"
    assert report.reason_codes == ("operator_watchlist_priority_queue_current",)


def test_stale_or_time_budget_constraints_schedule_rebalance() -> None:
    stale_report = build_report(
        candidate_count=d("5.000000"),
        high_edge_count=d("1.000000"),
        stale_count=d("2.000000"),
        blocked_count=ZERO,
        manual_capacity_slots=d("5.000000"),
        time_budget_minutes=d("45.000000"),
    )
    time_report = build_report(
        candidate_count=d("5.000000"),
        high_edge_count=d("1.000000"),
        stale_count=ZERO,
        blocked_count=ZERO,
        manual_capacity_slots=d("5.000000"),
        time_budget_minutes=d("20.000000"),
    )

    assert stale_report.rebalance_status == "watch"
    assert stale_report.priority_queue_action == "refresh_stale_candidates_before_rebalance"
    assert stale_report.manual_next_step == "refresh_stale_candidates_then_rebalance"
    assert stale_report.reason_codes == ("operator_watchlist_stale_items_present",)
    assert time_report.rebalance_status == "watch"
    assert time_report.priority_queue_action == "defer_rebalance_until_manual_window"
    assert time_report.manual_next_step == "schedule_additional_manual_review_time"
    assert time_report.reason_codes == (
        "operator_watchlist_time_budget_constrained",
    )


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    for dataclass_type in (
        OperatorWatchlistPriorityRebalanceInput,
        OperatorWatchlistPriorityRebalanceReport,
    ):
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True
        for field in fields(dataclass_type):
            assert "float" not in str(field.type)
            assert "int" not in str(field.type)

    inputs = OperatorWatchlistPriorityRebalanceInput(
        candidate_count=d("1.000000"),
        high_edge_count=ZERO,
        stale_count=ZERO,
        blocked_count=ZERO,
        manual_capacity_slots=d("1.000000"),
        time_budget_minutes=d("30.000000"),
    )
    with pytest.raises(FrozenInstanceError):
        inputs.candidate_count = d("2.000000")  # type: ignore[misc]


def test_validates_decimal_counts_flags_digest_and_public_payload_surface() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        build_report(candidate_count=1.0)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="plain Decimal"):
        build_report(high_edge_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="nonnegative"):
        build_report(stale_count=d("-1.000000"))

    with pytest.raises(ValueError, match="cannot exceed candidate_count"):
        build_report(candidate_count=d("1.000000"), high_edge_count=d("2.000000"))

    with pytest.raises(ValueError, match="cannot exceed candidate_count"):
        build_report(candidate_count=d("1.000000"), blocked_count=d("2.000000"))

    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(generated_at=datetime(2026, 7, 12, 10, 15))

    with pytest.raises(ValueError, match="paper_only"):
        replace(
            OperatorWatchlistPriorityRebalanceInput(
                candidate_count=d("1.000000"),
                high_edge_count=ZERO,
                stale_count=ZERO,
                blocked_count=ZERO,
                manual_capacity_slots=d("1.000000"),
                time_budget_minutes=d("30.000000"),
            ),
            paper_only=False,
        )

    report = build_report()
    tampered = dict(report.public_payload)
    tampered["payload_digest"] = "0" * 64
    with pytest.raises(ValueError, match="payload_digest must match"):
        operator_watchlist_priority_rebalance_report_payload(tampered)

    with pytest.raises(ValueError, match="unsafe public"):
        operator_watchlist_priority_rebalance_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet_path": "redacted",
            },
        )


def test_module_scope_has_no_live_auth_wallet_order_keys_signing_execution_or_persistence() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    forbidden_import_roots = {
        "builtins",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
    }
    forbidden_text = (
        "auth",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "secret_key",
        "sign",
        "execute",
        "execution",
        "live",
        "jsonl",
        "persist",
        "open(",
        "write_text",
        "write_bytes",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots

    lowered_source = source.lower()
    for term in forbidden_text:
        assert term not in lowered_source
