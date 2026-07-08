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


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=timezone(timedelta(hours=-4)))
GENERATED_AT_UTC = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_gold_signal_memory_quality_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_gold_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values: dict[str, object] = {
        "config_version": "research-domain-gold-signal-memory-quality-report-v0",
        "max_pass_memory_age_seconds": d("43200"),
        "max_watch_memory_age_seconds": d("172800"),
        "min_pass_freshness_ratio": d("0.750000"),
        "min_watch_freshness_ratio": d("0.500000"),
        "max_pass_conflict_ratio": d("0.100000"),
        "max_watch_conflict_ratio": d("0.250000"),
        "min_pass_required_coverage_ratio": d("1.000000"),
        "min_watch_required_coverage_ratio": d("0.750000"),
    }
    values.update(overrides)
    return report.ResearchDomainGoldSignalMemoryQualityConfig(**values)


def memory_input(**overrides: object):
    report = api()
    values: dict[str, object] = {
        "catalyst_family": "central-bank-demand",
        "memory_lane": "gold-macro-team",
        "memory_input_count": d("8"),
        "fresh_memory_input_count": d("7"),
        "stale_memory_input_count": d("1"),
        "conflicting_memory_input_count": d("0"),
        "required_catalyst_count": d("4"),
        "missing_required_catalyst_count": d("0"),
        "latest_memory_observed_at": GENERATED_AT_UTC - timedelta(hours=4),
    }
    values.update(overrides)
    return report.ResearchDomainGoldSignalMemoryInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_domain_gold_signal_memory_quality_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    values: list[Any] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_payload_values(item))
    return tuple(values)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_gold_signal_memory_quality_flags_stale_conflicting_and_missing_inputs() -> None:
    report = api()
    quality_report = build_report(
        memory_input(),
        memory_input(
            catalyst_family="inflation-real-yields",
            memory_lane="gold-rates-team",
            memory_input_count=d("6"),
            fresh_memory_input_count=d("4"),
            stale_memory_input_count=d("2"),
            conflicting_memory_input_count=d("1"),
            required_catalyst_count=d("4"),
            missing_required_catalyst_count=d("1"),
            latest_memory_observed_at=GENERATED_AT_UTC - timedelta(hours=30),
        ),
        memory_input(
            catalyst_family="physical-demand-stress",
            memory_lane="gold-commodities-team",
            memory_input_count=d("5"),
            fresh_memory_input_count=d("1"),
            stale_memory_input_count=d("4"),
            conflicting_memory_input_count=d("2"),
            required_catalyst_count=d("5"),
            missing_required_catalyst_count=d("2"),
            latest_memory_observed_at=GENERATED_AT_UTC - timedelta(days=4),
        ),
    )

    assert report.RESEARCH_DOMAIN_GOLD_SIGNAL_MEMORY_QUALITY_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(quality_report)
    assert type(quality_report) is report.ResearchDomainGoldSignalMemoryQualityReport
    assert quality_report.generated_at == GENERATED_AT_UTC
    assert (
        quality_report.config_version
        == "research-domain-gold-signal-memory-quality-report-v0"
    )
    assert quality_report.memory_lane_count == d("3")
    assert quality_report.memory_input_count == d("19")
    assert quality_report.fresh_memory_input_count == d("12")
    assert quality_report.stale_memory_input_count == d("7")
    assert quality_report.conflicting_memory_input_count == d("3")
    assert quality_report.required_catalyst_count == d("13")
    assert quality_report.missing_required_catalyst_count == d("3")
    assert quality_report.overall_freshness_ratio == d("0.631579")
    assert quality_report.overall_conflict_ratio == d("0.157895")
    assert quality_report.overall_required_coverage_ratio == d("0.769231")
    assert quality_report.max_memory_age_seconds == d("345600")
    assert quality_report.pass_count == d("1")
    assert quality_report.watch_count == d("1")
    assert quality_report.block_count == d("1")
    assert quality_report.status == "block"
    assert quality_report.paper_only is True
    assert quality_report.report_only is True
    assert quality_report.readonly is True

    assert tuple(
        (row.status, row.catalyst_family, row.memory_lane)
        for row in quality_report.rows
    ) == (
        ("block", "physical-demand-stress", "gold-commodities-team"),
        ("watch", "inflation-real-yields", "gold-rates-team"),
        ("pass", "central-bank-demand", "gold-macro-team"),
    )

    blocked, watched, passed = quality_report.rows
    assert type(blocked) is report.ResearchDomainGoldSignalMemoryQualityRow
    assert blocked.freshness_ratio == d("0.200000")
    assert blocked.conflict_ratio == d("0.400000")
    assert blocked.required_coverage_ratio == d("0.600000")
    assert blocked.memory_age_seconds == d("345600")
    assert blocked.reason_codes == (
        "gold_signal_memory_quality_block",
        "gold_memory_freshness_below_watch",
        "gold_memory_age_above_watch",
        "gold_memory_conflict_above_watch",
        "gold_memory_required_coverage_below_watch",
        "gold_memory_required_inputs_missing",
    )
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "gold_signal_memory_quality_watch",
        "gold_memory_freshness_below_pass",
        "gold_memory_age_above_pass",
        "gold_memory_conflict_above_pass",
        "gold_memory_required_coverage_below_pass",
        "gold_memory_required_inputs_missing",
    )
    assert passed.status == "pass"
    assert passed.reason_codes == ("gold_signal_memory_quality_pass",)
    assert tuple(
        (reason_count.reason_code, reason_count.count)
        for reason_count in quality_report.reason_code_counts
    )[:3] == (
        ("gold_signal_memory_quality_block", d("1")),
        ("gold_signal_memory_quality_watch", d("1")),
        ("gold_signal_memory_quality_pass", d("1")),
    )


def test_empty_report_blocks_with_zero_aggregates() -> None:
    quality_report = build_report()

    assert quality_report.memory_lane_count == d("0")
    assert quality_report.memory_input_count == d("0")
    assert quality_report.conflicting_memory_input_count == d("0")
    assert quality_report.required_catalyst_count == d("0")
    assert quality_report.missing_required_catalyst_count == d("0")
    assert quality_report.overall_freshness_ratio == d("0.000000")
    assert quality_report.overall_conflict_ratio == d("0.000000")
    assert quality_report.overall_required_coverage_ratio == d("0.000000")
    assert quality_report.max_memory_age_seconds == d("0")
    assert quality_report.status == "block"
    assert quality_report.reason_codes == ("gold_signal_memory_quality_no_inputs",)
    assert quality_report.rows == ()


def test_payload_digest_is_deterministic_json_ready_and_public_safe() -> None:
    report = api()
    first = build_report(
        memory_input(catalyst_family="central-bank-demand"),
        memory_input(
            catalyst_family="inflation-real-yields",
            memory_lane="gold-rates-team",
        ),
    )
    second = build_report(
        memory_input(
            catalyst_family="inflation-real-yields",
            memory_lane="gold-rates-team",
        ),
        memory_input(catalyst_family="central-bank-demand"),
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert report.research_domain_gold_signal_memory_quality_report_digest(first) == (
        first.derived_validation_digest
    )
    payload = report.research_domain_gold_signal_memory_quality_report_payload(first)
    json.dumps(payload, sort_keys=True)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert payload["rows"][0]["freshness_ratio"] == "0.875000"
    assert payload["rows"][0]["conflict_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    assert not any(type(value) in (float, int) for value in walk_payload_values(payload))
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate",
        "event_id",
        "market_id",
        "market_slug",
        "question",
        "slug",
        "url",
        "http://",
        "https://",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
        "recommend",
        "sizing",
        "allocation",
    ):
        assert forbidden not in encoded

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_frozen_decimal_only_flags_validation_and_side_effect_surface() -> None:
    report = api()
    quality_report = build_report(memory_input())

    for item in (
        config(),
        memory_input(),
        quality_report.rows[0],
        quality_report.reason_code_counts[0],
        quality_report,
    ):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(FrozenInstanceError):
        quality_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        quality_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadInput", (report.ResearchDomainGoldSignalMemoryInput,), {})

    with pytest.raises(ValueError, match="max_pass_memory_age_seconds"):
        config(max_pass_memory_age_seconds=d("200000"))
    with pytest.raises(ValueError, match="min_watch_freshness_ratio"):
        config(min_watch_freshness_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            memory_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="memory_input_count"):
        memory_input(memory_input_count=8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fresh and stale memory input counts"):
        memory_input(fresh_memory_input_count=d("6"), stale_memory_input_count=d("1"))
    with pytest.raises(ValueError, match="conflicting_memory_input_count"):
        memory_input(conflicting_memory_input_count=d("9"))
    with pytest.raises(ValueError, match="missing_required_catalyst_count"):
        memory_input(missing_required_catalyst_count=d("5"))
    with pytest.raises(ValueError, match="latest_memory_observed_at"):
        build_report(
            memory_input(latest_memory_observed_at=GENERATED_AT_UTC + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(memory_input(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(quality_report, readonly=False)

    for value in (
        "candidate-alpha",
        "event_id_123",
        "market_slug",
        "question",
        "https://example.test",
        "source_text",
        "warehouse_table",
        "dsn-main",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "recommendation",
        "sizing",
    ):
        with pytest.raises(ValueError, match="public-safe"):
            memory_input(catalyst_family=value)
        with pytest.raises(ValueError, match="public-safe"):
            memory_input(memory_lane=value)

    with pytest.raises(ValueError, match="status"):
        replace(quality_report, status="ready")
    assert quality_report.status in report.RESEARCH_DOMAIN_GOLD_SIGNAL_MEMORY_QUALITY_REPORT_STATUSES

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules: set[str] = set()
    called_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert imported_modules.isdisjoint(
        {
            "asyncio",
            "httpx",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "subprocess",
            "supabase",
            "urllib",
            "web3",
        },
    )
    assert called_names.isdisjoint(
        {
            "open",
            "connect",
            "execute",
            "post",
            "put",
            "patch",
            "delete",
            "send",
            "submit",
            "sign",
            "transfer",
        },
    )
    assert {field.name for field in fields(report.ResearchDomainGoldSignalMemoryInput)} == {
        "catalyst_family",
        "memory_lane",
        "memory_input_count",
        "fresh_memory_input_count",
        "stale_memory_input_count",
        "conflicting_memory_input_count",
        "required_catalyst_count",
        "missing_required_catalyst_count",
        "latest_memory_observed_at",
        "paper_only",
        "report_only",
        "readonly",
    }
