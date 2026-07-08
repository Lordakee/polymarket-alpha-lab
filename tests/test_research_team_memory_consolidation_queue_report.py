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
OBSERVED_AT = GENERATED_AT - timedelta(hours=2)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_memory_consolidation_queue_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_memory_consolidation_queue_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-team-memory-consolidation-queue-report-v0",
        "watch_min_sample_count": d("30"),
        "block_min_sample_count": d("10"),
        "watch_calibration_drift": d("0.050000"),
        "block_calibration_drift": d("0.120000"),
        "watch_stale_memory_hours": d("48.000000"),
        "block_stale_memory_hours": d("168.000000"),
        "watch_evidence_gap_ratio": d("0.100000"),
        "block_evidence_gap_ratio": d("0.250000"),
        "watch_min_domain_coverage_ratio": d("0.650000"),
        "block_min_domain_coverage_ratio": d("0.400000"),
    }
    values.update(overrides)
    return report.ResearchTeamMemoryConsolidationQueueConfig(**values)


def memory_signal(**overrides: object):
    report = api()
    values = {
        "team_key": "macro_rates",
        "aggregate_sample_count": d("36"),
        "calibration_drift": d("0.020000"),
        "stale_memory_hours": d("12.000000"),
        "evidence_gap_ratio": d("0.030000"),
        "domain_coverage_ratio": d("0.800000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return report.ResearchTeamMemoryConsolidationQueueInput(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_team_memory_consolidation_queue_report(
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


def test_memory_consolidation_queue_scores_pass_watch_and_block_statuses() -> None:
    report = build_report(
        memory_signal(
            team_key="sports_soccer",
            aggregate_sample_count=d("8"),
            calibration_drift=d("-0.130000"),
            stale_memory_hours=d("170.000000"),
            evidence_gap_ratio=d("0.270000"),
            domain_coverage_ratio=d("0.350000"),
        ),
        memory_signal(
            team_key="crypto_btc",
            aggregate_sample_count=d("28"),
            calibration_drift=d("0.060000"),
            stale_memory_hours=d("60.000000"),
            evidence_gap_ratio=d("0.120000"),
            domain_coverage_ratio=d("0.600000"),
        ),
        memory_signal(team_key="macro_rates"),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-team-memory-consolidation-queue-report-v0"
    assert report.memory_task_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.status == "block"
    assert report.reason_codes == (
        "memory_consolidation_queue_block",
        "sample_count_block",
        "calibration_drift_block",
        "stale_memory_block",
        "evidence_gap_block",
        "domain_coverage_block",
        "sample_count_watch",
        "calibration_drift_watch",
        "stale_memory_watch",
        "evidence_gap_watch",
        "domain_coverage_watch",
    )
    assert report.paper_queue_action == "paper_memory_consolidation_block"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    blocked, watched, passed = report.rows
    assert tuple(row.memory_status for row in report.rows) == ("block", "watch", "pass")
    assert blocked.team_key == "sports_soccer"
    assert blocked.reason_codes == (
        "sample_count_block",
        "calibration_drift_block",
        "stale_memory_block",
        "evidence_gap_block",
        "domain_coverage_block",
    )
    assert watched.team_key == "crypto_btc"
    assert watched.reason_codes == (
        "sample_count_watch",
        "calibration_drift_watch",
        "stale_memory_watch",
        "evidence_gap_watch",
        "domain_coverage_watch",
    )
    assert passed.reason_codes == ("memory_consolidation_clear",)

    assert report.reason_code_counts[0].reason_code == "memory_consolidation_clear"
    assert report.reason_code_counts[0].count == d("1")
    assert report.reason_code_counts[0].memory_task_ratio == d("0.333333")


def test_empty_queue_is_pass_with_decimal_counts_and_flags() -> None:
    report = build_report()

    assert report.memory_task_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.min_sample_count == d("0")
    assert report.max_calibration_drift == d("0.000000")
    assert report.max_stale_memory_hours == d("0.000000")
    assert report.max_evidence_gap_ratio == d("0.000000")
    assert report.min_domain_coverage_ratio == d("0.000000")
    assert report.status == "pass"
    assert report.paper_queue_action == "paper_memory_consolidation_monitor"
    assert report.reason_codes == ("memory_consolidation_queue_empty",)
    assert report.reason_code_counts == ()
    assert report.rows == ()

    populated = build_report(memory_signal())
    for value in (report, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_drift", "_hours", "_ratio")):
                assert type(item_value) is Decimal


def test_custom_config_drives_status_reason_codes_and_digest() -> None:
    custom = config(
        watch_min_sample_count=d("50"),
        block_min_sample_count=d("5"),
        watch_calibration_drift=d("0.010000"),
        block_calibration_drift=d("0.200000"),
        watch_stale_memory_hours=d("10.000000"),
        block_stale_memory_hours=d("500.000000"),
        watch_evidence_gap_ratio=d("0.020000"),
        block_evidence_gap_ratio=d("0.500000"),
        watch_min_domain_coverage_ratio=d("0.900000"),
        block_min_domain_coverage_ratio=d("0.300000"),
    )

    digest = build_report(memory_signal(), cfg=custom)

    assert digest.status == "watch"
    assert digest.reason_codes == (
        "memory_consolidation_queue_watch",
        "sample_count_watch",
        "calibration_drift_watch",
        "stale_memory_watch",
        "evidence_gap_watch",
        "domain_coverage_watch",
    )
    assert digest.rows[0].reason_codes == digest.reason_codes[1:]


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    report = api()
    first = build_report(
        memory_signal(
            team_key="basketball_stats",
            aggregate_sample_count=d("28"),
            calibration_drift=d("0.060000"),
            stale_memory_hours=d("60.000000"),
            evidence_gap_ratio=d("0.120000"),
            domain_coverage_ratio=d("0.600000"),
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        memory_signal(team_key="macro_rates"),
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
        memory_signal(team_key="macro_rates"),
        memory_signal(
            team_key="basketball_stats",
            aggregate_sample_count=d("28"),
            calibration_drift=d("0.060000"),
            stale_memory_hours=d("60.000000"),
            evidence_gap_ratio=d("0.120000"),
            domain_coverage_ratio=d("0.600000"),
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        ),
    )

    payload = report.research_team_memory_consolidation_queue_report_payload(first)
    repeat_payload = report.research_team_memory_consolidation_queue_report_payload(
        second,
    )

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["memory_task_count"] == "2"
    assert payload["rows"][0]["team_key"] == "basketball_stats"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:30:00+00:00"
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
        report.research_team_memory_consolidation_queue_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2"))


def test_public_payload_rejects_raw_identifiers_unsafe_flags_and_numbers() -> None:
    report = api()
    payload = report.research_team_memory_consolidation_queue_report_payload(
        build_report(memory_signal(team_key="crypto_eth")),
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
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_team_memory_consolidation_queue_report_payload(unsafe)

    for value in (
        "event id",
        "market slug",
        "source reference",
        "wallet signer",
        "auth token",
        "order route",
        "trade route",
        "live execution",
        "recommendation",
        "sizing",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_team_memory_consolidation_queue_report_payload(unsafe)

    numeric = dict(payload)
    numeric["memory_task_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        report.research_team_memory_consolidation_queue_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        report.research_team_memory_consolidation_queue_report_payload(downgraded)


def test_dataclasses_are_frozen_and_enforce_exact_decimal_inputs() -> None:
    row = memory_signal()

    with pytest.raises(FrozenInstanceError):
        row.aggregate_sample_count = d("40")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        memory_signal(aggregate_sample_count=30)
    with pytest.raises(ValueError, match="Decimal"):
        memory_signal(evidence_gap_ratio=0.12)
    with pytest.raises(ValueError, match="Decimal"):
        memory_signal(calibration_drift=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="integral"):
        memory_signal(aggregate_sample_count=d("30.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(memory_signal(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        memory_signal(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="observed_at"):
        memory_signal(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        build_report(memory_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        build_report(memory_signal(), memory_signal())
    with pytest.raises(ValueError, match="paper_only"):
        memory_signal(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(memory_signal(), cfg=object())


def test_digest_statuses_and_materialized_fields_are_tamper_evident() -> None:
    report = api()
    digest = build_report(memory_signal())
    row = digest.rows[0]

    assert report.STATUSES == ("pass", "watch", "block")
    assert "blocked" not in report.STATUSES

    with pytest.raises(ValueError, match="memory_status"):
        report.ResearchTeamMemoryConsolidationQueueRow(
            **{
                **row.__dict__,
                "memory_status": "block",
            },
        )

    with pytest.raises(ValueError, match="status"):
        report.ResearchTeamMemoryConsolidationQueueReport(
            **{
                **digest.__dict__,
                "status": "block",
            },
        )

    object.__setattr__(digest.rows[0], "evidence_gap_ratio", d("0.990000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_team_memory_consolidation_queue_report_payload(digest)


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
