from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=20)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_parallel_review_capacity_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_parallel_review_capacity_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-team-parallel-review-capacity-report-v0",
        "watch_active_load_ratio": d("0.700000"),
        "block_active_load_ratio": d("1.100000"),
        "watch_sla_age_seconds": d("1800"),
        "block_sla_age_seconds": d("3600"),
        "watch_unresolved_escalation_ratio": d("0.200000"),
        "block_unresolved_escalation_ratio": d("0.400000"),
        "watch_memory_writeback_delay_seconds": d("900"),
        "block_memory_writeback_delay_seconds": d("1800"),
        "watch_manual_escalation_urgency": d("0.500000"),
        "block_manual_escalation_urgency": d("0.800000"),
    }
    values.update(overrides)
    return report.ResearchTeamParallelReviewCapacityConfig(**values)


def capacity_signal(**overrides: object):
    report = api()
    values = {
        "review_team_key": "macro_review",
        "reviewer_pool_key": "rates",
        "available_reviewer_count": d("5"),
        "active_packet_count": d("3"),
        "oldest_sla_age_seconds": d("600"),
        "unresolved_escalation_count": d("0"),
        "memory_writeback_delay_seconds": d("300"),
        "manual_escalation_urgency": d("0.100000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return report.ResearchTeamParallelReviewCapacityInput(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_team_parallel_review_capacity_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_parallel_review_capacity_rolls_up_public_capacity_pressure() -> None:
    report = build_report(
        capacity_signal(
            review_team_key="macro_review",
            reviewer_pool_key="rates",
            available_reviewer_count=d("5"),
            active_packet_count=d("2"),
            oldest_sla_age_seconds=d("600"),
            unresolved_escalation_count=d("0"),
            memory_writeback_delay_seconds=d("300"),
            manual_escalation_urgency=d("0.100000"),
        ),
        capacity_signal(
            review_team_key="sports_review",
            reviewer_pool_key="soccer",
            available_reviewer_count=d("4"),
            active_packet_count=d("3"),
            oldest_sla_age_seconds=d("2400"),
            unresolved_escalation_count=d("1"),
            memory_writeback_delay_seconds=d("1200"),
            manual_escalation_urgency=d("0.600000"),
        ),
        capacity_signal(
            review_team_key="crypto_review",
            reviewer_pool_key="policy",
            available_reviewer_count=d("3"),
            active_packet_count=d("5"),
            oldest_sla_age_seconds=d("4200"),
            unresolved_escalation_count=d("3"),
            memory_writeback_delay_seconds=d("2100"),
            manual_escalation_urgency=d("0.900000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-team-parallel-review-capacity-report-v0"
    assert report.review_scope_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.total_available_reviewer_count == d("12")
    assert report.total_active_packet_count == d("10")
    assert report.total_unresolved_escalation_count == d("4")
    assert report.max_oldest_sla_age_seconds == d("4200")
    assert report.max_memory_writeback_delay_seconds == d("2100")
    assert report.max_manual_escalation_urgency == d("0.900000")
    assert report.max_capacity_pressure_ratio == d("1.000000")
    assert report.average_capacity_pressure_ratio == d("0.614815")
    assert report.status == "block"
    assert report.paper_queue_action == "paper_parallel_review_capacity_block"
    assert report.reason_codes == (
        "parallel_review_capacity_report_block",
        "active_packet_load_block",
        "sla_age_block",
        "unresolved_escalation_block",
        "memory_writeback_delay_block",
        "manual_escalation_urgency_block",
        "parallel_review_capacity_report_watch",
        "active_packet_load_watch",
        "sla_age_watch",
        "unresolved_escalation_watch",
        "memory_writeback_delay_watch",
        "manual_escalation_urgency_watch",
    )
    assert len(report.derived_validation_digest) == 64

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.review_team_key == "crypto_review"
    assert blocked.reviewer_pool_key == "policy"
    assert blocked.active_load_ratio == d("1.666667")
    assert blocked.reviewer_availability_ratio == d("0.375000")
    assert blocked.escalation_load_ratio == d("0.600000")
    assert blocked.capacity_pressure_ratio == d("1.000000")
    assert blocked.reason_codes == (
        "active_packet_load_block",
        "sla_age_block",
        "unresolved_escalation_block",
        "memory_writeback_delay_block",
        "manual_escalation_urgency_block",
    )
    assert watched.review_team_key == "sports_review"
    assert watched.capacity_pressure_ratio == d("0.444444")
    assert watched.reason_codes == (
        "active_packet_load_watch",
        "sla_age_watch",
        "unresolved_escalation_watch",
        "memory_writeback_delay_watch",
        "manual_escalation_urgency_watch",
    )
    assert passed.review_team_key == "macro_review"
    assert passed.reason_codes == ("parallel_review_capacity_clear",)

    assert report.reason_code_counts[0].reason_code == "parallel_review_capacity_clear"
    assert report.reason_code_counts[0].count == d("1")
    assert report.reason_code_counts[0].review_scope_ratio == d("0.333333")

    for value in (report, *report.rows, *report.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_ratio", "_seconds", "_urgency")):
                assert type(item_value) is Decimal


def test_empty_report_is_pass_with_decimal_zeroes() -> None:
    report = build_report()

    assert report.review_scope_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.total_available_reviewer_count == d("0")
    assert report.total_active_packet_count == d("0")
    assert report.total_unresolved_escalation_count == d("0")
    assert report.max_oldest_sla_age_seconds == d("0")
    assert report.max_memory_writeback_delay_seconds == d("0")
    assert report.max_manual_escalation_urgency == d("0.000000")
    assert report.max_capacity_pressure_ratio == d("0.000000")
    assert report.average_capacity_pressure_ratio == d("0.000000")
    assert report.status == "pass"
    assert report.paper_queue_action == "paper_parallel_review_capacity_monitor"
    assert report.reason_codes == ("parallel_review_capacity_no_inputs",)
    assert report.reason_code_counts == ()
    assert report.rows == ()


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    report_api = api()
    first = build_report(
        capacity_signal(
            review_team_key="sports_review",
            reviewer_pool_key="soccer",
            active_packet_count=d("3"),
            oldest_sla_age_seconds=d("2400"),
            unresolved_escalation_count=d("1"),
            memory_writeback_delay_seconds=d("1200"),
            manual_escalation_urgency=d("0.600000"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                40,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        capacity_signal(review_team_key="macro_review", reviewer_pool_key="rates"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        capacity_signal(review_team_key="macro_review", reviewer_pool_key="rates"),
        capacity_signal(
            review_team_key="sports_review",
            reviewer_pool_key="soccer",
            active_packet_count=d("3"),
            oldest_sla_age_seconds=d("2400"),
            unresolved_escalation_count=d("1"),
            memory_writeback_delay_seconds=d("1200"),
            manual_escalation_urgency=d("0.600000"),
            observed_at=datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        ),
    )

    payload = report_api.research_team_parallel_review_capacity_report_payload(first)
    repeat_payload = report_api.research_team_parallel_review_capacity_report_payload(
        second,
    )

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["review_scope_count"] == "2"
    assert payload["rows"][0]["review_team_key"] == "sports_review"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:40:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    unsafe_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "network",
        "database",
        "recommendation",
        "sizing",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in unsafe_fragments
    )
    payload_text = repr(payload).lower()
    assert not any(fragment in payload_text for fragment in unsafe_fragments)

    tampered = dict(payload)
    tampered["pass_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_api.research_team_parallel_review_capacity_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2"))


def test_public_payload_rejects_raw_identifiers_unsafe_flags_and_numbers() -> None:
    report_api = api()
    payload = report_api.research_team_parallel_review_capacity_report_payload(
        build_report(capacity_signal(review_team_key="crypto_review", reviewer_pool_key="risk")),
    )

    for key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "database_dsn",
        "table_name",
        "private_token",
        "wallet_address",
        "auth_header",
        "order_id",
        "trade_id",
        "live_url",
        "network_url",
        "position_sizing",
        "recommendation_id",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            report_api.research_team_parallel_review_capacity_report_payload(unsafe)

    for value in (
        "candidate id",
        "market slug",
        "question text",
        "source url",
        "database dsn",
        "table name",
        "private token",
        "wallet signer",
        "auth token",
        "order route",
        "trade route",
        "live execution",
        "network call",
        "recommendation",
        "sizing",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            report_api.research_team_parallel_review_capacity_report_payload(unsafe)

    numeric = dict(payload)
    numeric["review_scope_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        report_api.research_team_parallel_review_capacity_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        report_api.research_team_parallel_review_capacity_report_payload(downgraded)


def test_dataclasses_are_frozen_and_enforce_exact_decimal_inputs() -> None:
    row = capacity_signal()

    with pytest.raises(FrozenInstanceError):
        row.active_packet_count = d("4")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        capacity_signal(active_packet_count=3)
    with pytest.raises(ValueError, match="Decimal"):
        capacity_signal(memory_writeback_delay_seconds=1.0)
    with pytest.raises(ValueError, match="Decimal"):
        capacity_signal(unresolved_escalation_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="integral"):
        capacity_signal(active_packet_count=d("3.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(capacity_signal(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        capacity_signal(observed_at=datetime(2026, 7, 8, 11, 40))
    with pytest.raises(ValueError, match="observed_at"):
        capacity_signal(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 40, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(capacity_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(capacity_signal(), capacity_signal())
    with pytest.raises(ValueError, match="paper_only"):
        capacity_signal(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(capacity_signal(), cfg=object())


def test_statuses_and_materialized_fields_are_tamper_evident() -> None:
    report_api = api()
    report = build_report(capacity_signal())
    row = report.rows[0]

    assert report_api.STATUSES == ("pass", "watch", "block")
    assert "blocked" not in report_api.STATUSES

    with pytest.raises(ValueError, match="status"):
        report_api.ResearchTeamParallelReviewCapacityRow(
            **{
                **row.__dict__,
                "status": "block",
            },
        )

    with pytest.raises(ValueError, match="status"):
        report_api.ResearchTeamParallelReviewCapacityReport(
            **{
                **report.__dict__,
                "status": "block",
            },
        )

    object.__setattr__(report.rows[0], "active_load_ratio", d("0.990000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_api.research_team_parallel_review_capacity_report_payload(report)


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
        "ccxt",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
