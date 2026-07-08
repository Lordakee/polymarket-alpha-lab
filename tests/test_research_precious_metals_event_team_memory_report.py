from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_precious_metals_event_team_memory_report as api
from polymarket_alpha_lab.research_precious_metals_event_team_memory_report import (
    ResearchPreciousMetalsEventTeamMemoryConfig,
    ResearchPreciousMetalsEventTeamMemoryObservation,
    ResearchPreciousMetalsEventTeamMemoryReport,
    ResearchPreciousMetalsEventTeamMemoryRow,
    build_research_precious_metals_event_team_memory_report,
    research_precious_metals_event_team_memory_report_digest,
    research_precious_metals_event_team_memory_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_precious_metals_event_team_memory_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 9, 30, tzinfo=timezone(timedelta(hours=-4)))
GENERATED_AT_UTC = datetime(2026, 7, 8, 13, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchPreciousMetalsEventTeamMemoryConfig:
    values: dict[str, object] = {
        "config_version": "research-precious-metals-event-team-memory-report-v0",
        "min_pass_memory_score": d("0.750000"),
        "min_watch_memory_score": d("0.500000"),
        "min_pass_source_freshness_ratio": d("0.750000"),
        "min_watch_source_freshness_ratio": d("0.500000"),
        "max_pass_source_age_seconds": d("43200"),
        "max_watch_source_age_seconds": d("172800"),
        "min_pass_gold_specificity_ratio": d("0.700000"),
        "min_watch_gold_specificity_ratio": d("0.450000"),
    }
    values.update(overrides)
    return ResearchPreciousMetalsEventTeamMemoryConfig(**values)


def observation(
    **overrides: object,
) -> ResearchPreciousMetalsEventTeamMemoryObservation:
    values: dict[str, object] = {
        "event_family": "gold-rate-decision",
        "specialist_key": "precious-metals-macro",
        "memory_score": d("0.880000"),
        "source_count": d("8"),
        "fresh_source_count": d("7"),
        "stale_source_count": d("1"),
        "latest_source_observed_at": GENERATED_AT_UTC - timedelta(hours=4),
        "gold_specificity_ratio": d("0.820000"),
    }
    values.update(overrides)
    return ResearchPreciousMetalsEventTeamMemoryObservation(**values)


def report(
    *items: ResearchPreciousMetalsEventTeamMemoryObservation,
    cfg: ResearchPreciousMetalsEventTeamMemoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchPreciousMetalsEventTeamMemoryReport:
    return build_research_precious_metals_event_team_memory_report(
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


def test_rolls_up_precious_metals_specialist_memory_and_source_freshness() -> None:
    memory_report = report(
        observation(),
        observation(
            event_family="gold-inflation-print",
            specialist_key="precious-metals-cpi",
            memory_score=d("0.620000"),
            source_count=d("5"),
            fresh_source_count=d("3"),
            stale_source_count=d("2"),
            latest_source_observed_at=GENERATED_AT_UTC - timedelta(hours=20),
            gold_specificity_ratio=d("0.620000"),
        ),
        observation(
            event_family="silver-industrial-demand",
            specialist_key="precious-metals-demand",
            memory_score=d("0.360000"),
            source_count=d("4"),
            fresh_source_count=d("1"),
            stale_source_count=d("3"),
            latest_source_observed_at=GENERATED_AT_UTC - timedelta(days=3),
            gold_specificity_ratio=d("0.300000"),
        ),
    )

    assert api.STATUSES == ("pass", "watch", "block")
    assert is_dataclass(memory_report)
    assert type(memory_report) is ResearchPreciousMetalsEventTeamMemoryReport
    assert memory_report.generated_at == GENERATED_AT_UTC
    assert memory_report.event_specialist_count == d("3")
    assert memory_report.source_count == d("17")
    assert memory_report.fresh_source_count == d("11")
    assert memory_report.stale_source_count == d("6")
    assert memory_report.average_memory_score == d("0.620000")
    assert memory_report.overall_source_freshness_ratio == d("0.647059")
    assert memory_report.average_gold_specificity_ratio == d("0.580000")
    assert memory_report.max_source_age_seconds == d("259200")
    assert memory_report.pass_count == d("1")
    assert memory_report.watch_count == d("1")
    assert memory_report.block_count == d("1")
    assert memory_report.status == "block"
    assert memory_report.paper_only is True
    assert memory_report.report_only is True
    assert memory_report.readonly is True

    assert tuple((row.status, row.event_family, row.specialist_key) for row in memory_report.rows) == (
        ("block", "silver-industrial-demand", "precious-metals-demand"),
        ("watch", "gold-inflation-print", "precious-metals-cpi"),
        ("pass", "gold-rate-decision", "precious-metals-macro"),
    )

    blocked, watched, passed = memory_report.rows
    assert type(blocked) is ResearchPreciousMetalsEventTeamMemoryRow
    assert blocked.source_freshness_ratio == d("0.250000")
    assert blocked.source_age_seconds == d("259200")
    assert blocked.reason_codes == (
        "precious_metals_memory_block",
        "memory_score_below_watch",
        "source_freshness_below_watch",
        "source_age_above_watch",
        "gold_specificity_below_watch",
    )
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "precious_metals_memory_watch",
        "memory_score_below_pass",
        "source_freshness_below_pass",
        "source_age_above_pass",
        "gold_specificity_below_pass",
    )
    assert passed.status == "pass"
    assert passed.reason_codes == ("precious_metals_memory_pass",)
    assert tuple(
        (reason_count.reason_code, reason_count.count)
        for reason_count in memory_report.reason_code_counts
    )[:3] == (
        ("precious_metals_memory_block", d("1")),
        ("precious_metals_memory_watch", d("1")),
        ("precious_metals_memory_pass", d("1")),
    )


def test_empty_report_is_block_with_zero_aggregates() -> None:
    memory_report = report()

    assert memory_report.event_specialist_count == d("0")
    assert memory_report.source_count == d("0")
    assert memory_report.average_memory_score == d("0.000000")
    assert memory_report.overall_source_freshness_ratio == d("0.000000")
    assert memory_report.average_gold_specificity_ratio == d("0.000000")
    assert memory_report.max_source_age_seconds == d("0")
    assert memory_report.status == "block"
    assert memory_report.reason_codes == ("precious_metals_memory_no_observations",)
    assert memory_report.rows == ()


def test_payload_digest_is_deterministic_json_ready_and_public_safe() -> None:
    first = report(
        observation(event_family="gold-rate-decision"),
        observation(event_family="gold-inflation-print", specialist_key="precious-metals-cpi"),
    )
    second = report(
        observation(event_family="gold-inflation-print", specialist_key="precious-metals-cpi"),
        observation(event_family="gold-rate-decision"),
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert research_precious_metals_event_team_memory_report_digest(first) == (
        first.derived_validation_digest
    )
    payload = research_precious_metals_event_team_memory_report_payload(first)
    json.dumps(payload, sort_keys=True)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T13:30:00+00:00"
    assert payload["rows"][0]["memory_score"] == "0.880000"
    assert payload["rows"][0]["source_freshness_ratio"] == "0.875000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    assert not any(type(value) in (float, int) for value in walk_payload_values(payload))
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "event_id",
        "market_id",
        "source_id",
        "source_url",
        "http://",
        "https://",
        "slug",
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


def test_frozen_decimal_only_hard_flags_and_validation_are_enforced() -> None:
    memory_report = report(observation())

    for item in (
        config(),
        observation(),
        memory_report.rows[0],
        memory_report.reason_code_counts[0],
        memory_report,
    ):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(FrozenInstanceError):
        memory_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        memory_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadObservation", (ResearchPreciousMetalsEventTeamMemoryObservation,), {})

    with pytest.raises(ValueError, match="min_pass_memory_score"):
        config(min_pass_memory_score=Decimal("0.400000"))
    with pytest.raises(ValueError, match="min_watch_source_freshness_ratio"):
        config(min_watch_source_freshness_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 13, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="memory_score"):
        observation(memory_score=0.88)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_count"):
        observation(source_count=d("4.5"))
    with pytest.raises(ValueError, match="fresh and stale source counts"):
        observation(fresh_source_count=d("6"), stale_source_count=d("1"))
    with pytest.raises(ValueError, match="latest_source_observed_at"):
        report(observation(latest_source_observed_at=GENERATED_AT_UTC + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(memory_report, readonly=False)


def test_public_identifiers_statuses_and_side_effect_surface_are_constrained() -> None:
    for value in (
        "event_id_123",
        "market_slug",
        "source_url",
        "https://example.test",
        "wallet",
        "auth",
        "order",
        "trade",
        "live_execution",
        "recommendation",
        "sizing",
    ):
        with pytest.raises(ValueError, match="public-safe"):
            observation(event_family=value)
        with pytest.raises(ValueError, match="public-safe"):
            observation(specialist_key=value)

    with pytest.raises(ValueError, match="status"):
        replace(memory_report := report(observation()), status="ready")
    assert memory_report.status in api.STATUSES

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
    assert {field.name for field in fields(ResearchPreciousMetalsEventTeamMemoryObservation)} == {
        "event_family",
        "specialist_key",
        "memory_score",
        "source_count",
        "fresh_source_count",
        "stale_source_count",
        "latest_source_observed_at",
        "gold_specificity_ratio",
        "paper_only",
        "report_only",
        "readonly",
    }
