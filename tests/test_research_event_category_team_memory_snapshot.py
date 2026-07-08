from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_category_team_memory_snapshot.py"
)
GENERATED_AT = datetime(2026, 7, 8, 9, 30, tzinfo=timezone(timedelta(hours=-4)))
GENERATED_AT_UTC = datetime(2026, 7, 8, 13, 30, tzinfo=UTC)
ZERO_RATIO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_category_team_memory_snapshot",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    snapshot = api()
    values: dict[str, object] = {
        "config_version": "research-event-category-team-memory-snapshot-test-v0",
        "min_pass_coverage_ratio": d("0.700000"),
        "min_watch_coverage_ratio": d("0.400000"),
        "max_pass_stale_ratio": d("0.200000"),
        "max_watch_stale_ratio": d("0.500000"),
        "max_pass_blocked_ratio": d("0.000000"),
        "max_watch_blocked_ratio": d("0.250000"),
    }
    values.update(overrides)
    return snapshot.ResearchEventCategoryTeamMemorySnapshotConfig(**values)


def memory(**overrides: object):
    snapshot = api()
    values: dict[str, object] = {
        "team_id": "politics_research_team",
        "event_category_hint": "us election policy",
        "memory_entry_count": d("10"),
        "passing_memory_entry_count": d("8"),
        "watch_memory_entry_count": d("2"),
        "blocked_memory_entry_count": d("0"),
        "stale_memory_entry_count": d("1"),
    }
    values.update(overrides)
    return snapshot.ResearchEventCategoryTeamMemoryInput(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    snapshot = api()
    return snapshot.build_research_event_category_team_memory_snapshot(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_public_numbers(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload contains public numeric {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)


def test_routes_memory_into_required_categories_and_rolls_up_statuses() -> None:
    snapshot_report = report(
        memory(),
        memory(
            team_id="crypto_research_team",
            event_category_hint="btc ethereum crypto",
            memory_entry_count=d("10"),
            passing_memory_entry_count=d("5"),
            watch_memory_entry_count=d("5"),
            blocked_memory_entry_count=d("0"),
            stale_memory_entry_count=d("2"),
        ),
        memory(
            team_id="macro_research_team",
            event_category_hint="fomc rates inflation",
            memory_entry_count=d("10"),
            passing_memory_entry_count=d("2"),
            watch_memory_entry_count=d("3"),
            blocked_memory_entry_count=d("5"),
            stale_memory_entry_count=d("1"),
        ),
        memory(
            team_id="metals_research_team",
            event_category_hint="xau gold bullion",
            memory_entry_count=d("5"),
            passing_memory_entry_count=d("4"),
            watch_memory_entry_count=d("1"),
            blocked_memory_entry_count=d("0"),
            stale_memory_entry_count=d("0"),
        ),
        memory(
            team_id="soccer_research_team",
            event_category_hint="football premier league",
            memory_entry_count=d("6"),
            passing_memory_entry_count=d("3"),
            watch_memory_entry_count=d("3"),
            blocked_memory_entry_count=d("0"),
            stale_memory_entry_count=d("1"),
        ),
        memory(
            team_id="basketball_research_team",
            event_category_hint="nba basketball",
            memory_entry_count=d("8"),
            passing_memory_entry_count=d("1"),
            watch_memory_entry_count=d("2"),
            blocked_memory_entry_count=d("5"),
            stale_memory_entry_count=d("3"),
        ),
    )

    assert is_dataclass(snapshot_report)
    assert snapshot_report.generated_at == GENERATED_AT_UTC
    assert snapshot_report.config_version == (
        "research-event-category-team-memory-snapshot-test-v0"
    )
    assert tuple(row.category_id for row in snapshot_report.category_rows) == (
        "politics",
        "crypto",
        "macro",
        "gold",
        "soccer",
        "basketball",
    )
    assert tuple(row.public_status for row in snapshot_report.category_rows) == (
        "pass",
        "watch",
        "block",
        "pass",
        "watch",
        "block",
    )
    assert snapshot_report.category_count == d("6")
    assert snapshot_report.observed_category_count == d("6")
    assert snapshot_report.team_count == d("6")
    assert snapshot_report.pass_category_count == d("2")
    assert snapshot_report.watch_category_count == d("2")
    assert snapshot_report.block_category_count == d("2")
    assert snapshot_report.memory_entry_count == d("49")
    assert snapshot_report.passing_memory_entry_count == d("23")
    assert snapshot_report.coverage_ratio == d("0.469388")
    assert snapshot_report.public_status == "block"
    assert snapshot_report.paper_only is True
    assert snapshot_report.report_only is True
    assert snapshot_report.readonly is True

    politics, crypto, macro, gold, soccer, basketball = snapshot_report.category_rows
    assert politics.team_count == d("1")
    assert politics.coverage_ratio == d("0.800000")
    assert politics.blocked_ratio == ZERO_RATIO
    assert politics.reason_codes == ("team_memory_snapshot_pass",)
    assert crypto.coverage_ratio == d("0.500000")
    assert crypto.reason_codes == (
        "team_memory_snapshot_watch",
        "team_memory_snapshot_coverage_below_pass",
    )
    assert macro.blocked_ratio == d("0.500000")
    assert macro.reason_codes == (
        "team_memory_snapshot_block",
        "team_memory_snapshot_coverage_below_watch",
        "team_memory_snapshot_blocked_ratio_above_watch",
    )
    assert gold.coverage_ratio == d("0.800000")
    assert soccer.public_status == "watch"
    assert basketball.public_status == "block"

    assert snapshot_report.reason_codes == (
        "team_memory_snapshot_block",
        "team_memory_snapshot_watch",
        "team_memory_snapshot_pass",
        "team_memory_snapshot_coverage_below_watch",
        "team_memory_snapshot_coverage_below_pass",
        "team_memory_snapshot_blocked_ratio_above_watch",
    )
    assert tuple(
        (reason_count.reason_code, reason_count.count)
        for reason_count in snapshot_report.reason_code_counts
    )[:3] == (
        ("team_memory_snapshot_block", d("2")),
        ("team_memory_snapshot_watch", d("2")),
        ("team_memory_snapshot_pass", d("2")),
    )


def test_missing_categories_are_public_blocks_without_private_context() -> None:
    empty = report()

    assert tuple(row.category_id for row in empty.category_rows) == (
        "politics",
        "crypto",
        "macro",
        "gold",
        "soccer",
        "basketball",
    )
    assert tuple(row.public_status for row in empty.category_rows) == (
        "block",
        "block",
        "block",
        "block",
        "block",
        "block",
    )
    assert empty.observed_category_count == d("0")
    assert empty.team_count == d("0")
    assert empty.memory_entry_count == d("0")
    assert empty.coverage_ratio == ZERO_RATIO
    assert empty.public_status == "block"
    assert empty.reason_codes == (
        "team_memory_snapshot_block",
        "team_memory_snapshot_no_memory_coverage",
    )


def test_payload_is_deterministic_decimal_string_safe_and_digest_consistent() -> None:
    snapshot = api()
    first = report(
        memory(
            team_id="macro_research_team",
            event_category_hint="rates cpi",
            memory_entry_count=d("4"),
            passing_memory_entry_count=d("2"),
            watch_memory_entry_count=d("2"),
            blocked_memory_entry_count=d("0"),
            stale_memory_entry_count=d("1"),
        ),
        memory(
            team_id="crypto_research_team",
            event_category_hint="bitcoin",
            memory_entry_count=d("5"),
            passing_memory_entry_count=d("4"),
            watch_memory_entry_count=d("1"),
            blocked_memory_entry_count=d("0"),
            stale_memory_entry_count=d("0"),
        ),
    )
    second = report(
        memory(
            team_id="crypto_research_team",
            event_category_hint="bitcoin",
            memory_entry_count=d("5"),
            passing_memory_entry_count=d("4"),
            watch_memory_entry_count=d("1"),
            blocked_memory_entry_count=d("0"),
            stale_memory_entry_count=d("0"),
        ),
        memory(
            team_id="macro_research_team",
            event_category_hint="rates cpi",
            memory_entry_count=d("4"),
            passing_memory_entry_count=d("2"),
            watch_memory_entry_count=d("2"),
            blocked_memory_entry_count=d("0"),
            stale_memory_entry_count=d("1"),
        ),
        generated_at=GENERATED_AT_UTC,
    )

    first_payload = snapshot.research_event_category_team_memory_snapshot_payload(first)
    second_payload = snapshot.research_event_category_team_memory_snapshot_payload(second)
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )
    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T13:30:00+00:00"
    assert first_payload["memory_entry_count"] == "9"
    assert first_payload["coverage_ratio"] == "0.666667"
    assert first_payload["public_digest"] == first.public_digest
    assert snapshot.research_event_category_team_memory_snapshot_digest(first) == (
        first.public_digest
    )
    assert first_payload == first.public_payload
    assert_no_public_numbers(first_payload)

    rendered = repr(first_payload).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "politics_research_team",
        "crypto_research_team",
        "macro_research_team",
    ):
        assert forbidden not in rendered


def test_validation_rejects_float_int_subclasses_bad_times_statuses_and_duplicates() -> None:
    snapshot = api()

    with pytest.raises(ValueError, match="config"):
        snapshot.build_research_event_category_team_memory_snapshot(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="memory_entry_count must be a Decimal"):
        memory(memory_entry_count=1)
    with pytest.raises(ValueError, match="passing_memory_entry_count must be a Decimal"):
        memory(passing_memory_entry_count=0.8)
    with pytest.raises(ValueError, match="stale_memory_entry_count must be a Decimal"):
        memory(stale_memory_entry_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="min_pass_coverage_ratio must be a Decimal"):
        config(min_pass_coverage_ratio=0.7)
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(memory(), generated_at=_DatetimeSubclass(2026, 7, 8, 13, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(memory(), generated_at=datetime(2026, 7, 8, 13, 30))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            memory(),
            generated_at=datetime(2026, 7, 8, 13, 30, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(memory(), readonly=False)
    with pytest.raises(ValueError, match="memory rows must be unique"):
        report(memory(), memory())
    with pytest.raises(ValueError, match="public_status"):
        replace(report(memory()).category_rows[0], public_status="ready")
    with pytest.raises(FrozenInstanceError):
        report(memory()).category_rows[0].public_status = "pass"  # type: ignore[misc]


def test_public_text_and_payload_reject_private_or_actionable_surface_leaks() -> None:
    snapshot = api()

    for overrides in (
        {"team_id": "candidate_123"},
        {"team_id": "wallet_ops"},
        {"event_category_hint": "https://example.invalid/source?token=abc"},
        {"event_category_hint": "market_slug election question text"},
        {"event_category_hint": "buy soccer recommendation"},
    ):
        with pytest.raises(ValueError):
            memory(**overrides)

    safe_report = report(memory())
    with pytest.raises(ValueError, match="public"):
        replace(
            safe_report.category_rows[0],
            category_id="source_url",
            public_digest=safe_report.category_rows[0].public_digest,
        )
    with pytest.raises(ValueError, match="public_digest"):
        replace(safe_report, public_digest="0" * 64)

    payload = snapshot.research_event_category_team_memory_snapshot_payload(safe_report)
    rendered = repr(payload).lower()
    for forbidden in (
        "candidate",
        "market_slug",
        "question",
        "source",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in rendered


def test_public_dataclasses_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    snapshot = api()
    snapshot_report = report(memory())
    values = (
        config(),
        memory(),
        snapshot_report.category_rows[0],
        snapshot_report.reason_code_counts[0],
        snapshot_report,
    )
    numeric_suffixes = (
        "_count",
        "_ratio",
    )

    assert snapshot.__all__ == (
        "DEFAULT_RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CONFIG_VERSION",
        "RESEARCH_EVENT_CATEGORY_TEAM_MEMORY_SNAPSHOT_CATEGORIES",
        "ResearchEventCategoryTeamMemoryInput",
        "ResearchEventCategoryTeamMemorySnapshotCategoryRow",
        "ResearchEventCategoryTeamMemorySnapshotConfig",
        "ResearchEventCategoryTeamMemorySnapshotReasonCodeCount",
        "ResearchEventCategoryTeamMemorySnapshotReport",
        "build_research_event_category_team_memory_snapshot",
        "research_event_category_team_memory_snapshot_digest",
        "research_event_category_team_memory_snapshot_payload",
    )
    for exported_name in snapshot.__all__:
        exported = getattr(snapshot, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            if field.name.endswith(numeric_suffixes):
                assert type(getattr(value, field.name)) is Decimal

    for dataclass_type in (
        snapshot.ResearchEventCategoryTeamMemoryInput,
        snapshot.ResearchEventCategoryTeamMemorySnapshotCategoryRow,
        snapshot.ResearchEventCategoryTeamMemorySnapshotConfig,
        snapshot.ResearchEventCategoryTeamMemorySnapshotReasonCodeCount,
        snapshot.ResearchEventCategoryTeamMemorySnapshotReport,
    ):
        hints = get_type_hints(dataclass_type)
        for field in fields(dataclass_type):
            if field.name.endswith(numeric_suffixes):
                assert hints[field.name] is Decimal


def test_module_scope_stays_report_only_and_without_forbidden_runtime_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "candidate_id",
        "market_id",
        "market_slug",
        "source_ref",
        "source_url",
        "source_text",
        "private_key",
        "api_key",
        "payload_json",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    forbidden_call_names = {
        "__import__",
        "connect",
        "eval",
        "exec",
        "executemany",
        "float",
        "open",
        "print",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
