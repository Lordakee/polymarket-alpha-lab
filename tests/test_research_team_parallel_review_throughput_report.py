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
OBSERVED_AT = GENERATED_AT - timedelta(minutes=15)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_parallel_review_throughput_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_parallel_review_throughput_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-team-parallel-review-throughput-report-v0",
        "watch_queue_load_ratio": d("0.700000"),
        "block_queue_load_ratio": d("1.100000"),
        "watch_stale_memory_ratio": d("0.250000"),
        "block_stale_memory_ratio": d("0.500000"),
        "watch_reviewer_utilization_ratio": d("0.800000"),
        "block_reviewer_utilization_ratio": d("1.050000"),
        "watch_escalation_ratio": d("0.200000"),
        "block_escalation_ratio": d("0.400000"),
    }
    values.update(overrides)
    return report.ResearchTeamParallelReviewThroughputConfig(**values)


def throughput_signal(**overrides: object):
    report = api()
    values = {
        "team_key": "macro_review",
        "review_lane": "rates",
        "queued_review_count": d("3"),
        "completed_review_count": d("10"),
        "reviewer_capacity_count": d("12"),
        "stale_memory_count": d("1"),
        "reviewer_bottleneck_count": d("2"),
        "escalation_count": d("1"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return report.ResearchTeamParallelReviewThroughputInput(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_team_parallel_review_throughput_report(
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


def test_parallel_review_throughput_rolls_up_public_aggregate_pressure() -> None:
    digest = build_report(
        throughput_signal(
            team_key="macro_rates",
            review_lane="policy",
            queued_review_count=d("2"),
            completed_review_count=d("12"),
            reviewer_capacity_count=d("12"),
            stale_memory_count=d("0"),
            reviewer_bottleneck_count=d("1"),
            escalation_count=d("1"),
        ),
        throughput_signal(
            team_key="sports_soccer",
            review_lane="fixtures",
            queued_review_count=d("8"),
            completed_review_count=d("10"),
            reviewer_capacity_count=d("12"),
            stale_memory_count=d("3"),
            reviewer_bottleneck_count=d("7"),
            escalation_count=d("2"),
        ),
        throughput_signal(
            team_key="crypto_policy",
            review_lane="stablecoin",
            queued_review_count=d("15"),
            completed_review_count=d("8"),
            reviewer_capacity_count=d("12"),
            stale_memory_count=d("8"),
            reviewer_bottleneck_count=d("13"),
            escalation_count=d("7"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.generated_at.tzinfo is UTC
    assert digest.config_version == "research-team-parallel-review-throughput-report-v0"
    assert digest.review_team_count == d("3")
    assert digest.pass_count == d("1")
    assert digest.watch_count == d("1")
    assert digest.block_count == d("1")
    assert digest.total_queued_review_count == d("25")
    assert digest.total_completed_review_count == d("30")
    assert digest.total_reviewer_capacity_count == d("36")
    assert digest.total_stale_memory_count == d("11")
    assert digest.total_reviewer_bottleneck_count == d("21")
    assert digest.total_escalation_count == d("10")
    assert digest.max_throughput_pressure_ratio == d("1.000000")
    assert digest.average_throughput_pressure_ratio == d("0.620715")
    assert digest.status == "block"
    assert digest.paper_queue_action == "paper_parallel_review_throughput_block"
    assert digest.reason_codes == (
        "parallel_review_throughput_queue_block",
        "queue_load_block",
        "stale_memory_block",
        "reviewer_bottleneck_block",
        "escalation_load_block",
        "queue_load_watch",
        "stale_memory_watch",
        "reviewer_bottleneck_watch",
        "escalation_load_watch",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert len(digest.derived_validation_digest) == 64

    blocked, watched, passed = digest.rows
    assert tuple(row.status for row in digest.rows) == ("block", "watch", "pass")
    assert blocked.team_key == "crypto_policy"
    assert blocked.review_lane == "stablecoin"
    assert blocked.queue_load_ratio == d("1.250000")
    assert blocked.stale_memory_ratio == d("0.533333")
    assert blocked.reviewer_utilization_ratio == d("1.083333")
    assert blocked.escalation_ratio == d("0.466667")
    assert blocked.throughput_pressure_ratio == d("1.000000")
    assert blocked.reason_codes == (
        "queue_load_block",
        "stale_memory_block",
        "reviewer_bottleneck_block",
        "escalation_load_block",
    )
    assert watched.team_key == "sports_soccer"
    assert watched.throughput_pressure_ratio == d("0.751146")
    assert watched.reason_codes == (
        "queue_load_watch",
        "stale_memory_watch",
        "reviewer_bottleneck_watch",
        "escalation_load_watch",
    )
    assert passed.team_key == "macro_rates"
    assert passed.reason_codes == ("parallel_review_throughput_clear",)

    assert digest.reason_code_counts[0].reason_code == "parallel_review_throughput_clear"
    assert digest.reason_code_counts[0].count == d("1")
    assert digest.reason_code_counts[0].review_team_ratio == d("0.333333")

    for value in (digest, *digest.rows, *digest.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_ratio")):
                assert type(item_value) is Decimal


def test_empty_report_is_pass_with_decimal_aggregate_zeroes() -> None:
    digest = build_report()

    assert digest.review_team_count == d("0")
    assert digest.pass_count == d("0")
    assert digest.watch_count == d("0")
    assert digest.block_count == d("0")
    assert digest.total_queued_review_count == d("0")
    assert digest.total_completed_review_count == d("0")
    assert digest.total_reviewer_capacity_count == d("0")
    assert digest.total_stale_memory_count == d("0")
    assert digest.total_reviewer_bottleneck_count == d("0")
    assert digest.total_escalation_count == d("0")
    assert digest.max_throughput_pressure_ratio == d("0.000000")
    assert digest.average_throughput_pressure_ratio == d("0.000000")
    assert digest.status == "pass"
    assert digest.paper_queue_action == "paper_parallel_review_throughput_monitor"
    assert digest.reason_codes == ("parallel_review_throughput_queue_empty",)
    assert digest.reason_code_counts == ()
    assert digest.rows == ()


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    report = api()
    first = build_report(
        throughput_signal(
            team_key="sports_soccer",
            review_lane="fixtures",
            queued_review_count=d("8"),
            completed_review_count=d("10"),
            reviewer_capacity_count=d("12"),
            stale_memory_count=d("3"),
            reviewer_bottleneck_count=d("7"),
            escalation_count=d("2"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                45,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        throughput_signal(team_key="macro_rates", review_lane="policy"),
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
        throughput_signal(team_key="macro_rates", review_lane="policy"),
        throughput_signal(
            team_key="sports_soccer",
            review_lane="fixtures",
            queued_review_count=d("8"),
            completed_review_count=d("10"),
            reviewer_capacity_count=d("12"),
            stale_memory_count=d("3"),
            reviewer_bottleneck_count=d("7"),
            escalation_count=d("2"),
            observed_at=datetime(2026, 7, 8, 11, 45, tzinfo=UTC),
        ),
    )

    payload = report.research_team_parallel_review_throughput_report_payload(first)
    repeat_payload = report.research_team_parallel_review_throughput_report_payload(
        second,
    )

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["review_team_count"] == "2"
    assert payload["rows"][0]["team_key"] == "sports_soccer"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:45:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    unsafe_fragments = (
        "event",
        "market",
        "source",
        "recommendation",
        "sizing",
        "order",
        "wallet",
        "auth",
        "trade",
        "live",
        "network",
        "database",
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
        report.research_team_parallel_review_throughput_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2"))


def test_public_payload_rejects_raw_identifiers_unsafe_flags_and_numbers() -> None:
    report = api()
    payload = report.research_team_parallel_review_throughput_report_payload(
        build_report(throughput_signal(team_key="crypto_policy", review_lane="risk")),
    )

    for key in (
        "event_id",
        "market_slug",
        "source_reference",
        "recommendation_id",
        "position_sizing",
        "order_id",
        "wallet_address",
        "auth_header",
        "trade_id",
        "live_url",
        "network_url",
        "database_dsn",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_team_parallel_review_throughput_report_payload(unsafe)

    for value in (
        "event id",
        "market slug",
        "source reference",
        "wallet signer",
        "auth token",
        "order route",
        "trade route",
        "live execution",
        "network call",
        "database row",
        "recommendation",
        "sizing",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_team_parallel_review_throughput_report_payload(unsafe)

    numeric = dict(payload)
    numeric["review_team_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        report.research_team_parallel_review_throughput_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        report.research_team_parallel_review_throughput_report_payload(downgraded)


def test_dataclasses_are_frozen_and_enforce_exact_decimal_inputs() -> None:
    row = throughput_signal()

    with pytest.raises(FrozenInstanceError):
        row.queued_review_count = d("4")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        throughput_signal(queued_review_count=3)
    with pytest.raises(ValueError, match="Decimal"):
        throughput_signal(stale_memory_count=1.0)
    with pytest.raises(ValueError, match="Decimal"):
        throughput_signal(escalation_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="integral"):
        throughput_signal(queued_review_count=d("3.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(throughput_signal(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        throughput_signal(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="observed_at"):
        throughput_signal(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(throughput_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(throughput_signal(), throughput_signal())
    with pytest.raises(ValueError, match="paper_only"):
        throughput_signal(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(throughput_signal(), cfg=object())


def test_digest_statuses_and_materialized_fields_are_tamper_evident() -> None:
    report = api()
    digest = build_report(throughput_signal())
    row = digest.rows[0]

    assert report.STATUSES == ("pass", "watch", "block")
    assert "blocked" not in report.STATUSES

    with pytest.raises(ValueError, match="status"):
        report.ResearchTeamParallelReviewThroughputRow(
            **{
                **row.__dict__,
                "status": "block",
            },
        )

    with pytest.raises(ValueError, match="status"):
        report.ResearchTeamParallelReviewThroughputReport(
            **{
                **digest.__dict__,
                "status": "block",
            },
        )

    object.__setattr__(digest.rows[0], "queue_load_ratio", d("0.990000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_team_parallel_review_throughput_report_payload(digest)


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
