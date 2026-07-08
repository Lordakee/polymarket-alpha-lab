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


GENERATED_AT = datetime(2026, 7, 8, 9, 30, tzinfo=timezone(timedelta(hours=-4)))
GENERATED_AT_UTC = datetime(2026, 7, 8, 13, 30, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_energy_event_team_memory_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_energy_event_team_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values: dict[str, object] = {
        "config_version": "research-energy-event-team-memory-report-v0",
        "min_pass_memory_score": d("0.750000"),
        "min_watch_memory_score": d("0.500000"),
        "min_pass_source_freshness_ratio": d("0.750000"),
        "min_watch_source_freshness_ratio": d("0.500000"),
        "max_pass_source_age_seconds": d("43200"),
        "max_watch_source_age_seconds": d("172800"),
        "min_pass_evidence_reuse_ratio": d("0.700000"),
        "min_watch_evidence_reuse_ratio": d("0.400000"),
        "min_pass_calibration_sample_count": d("30"),
        "min_watch_calibration_sample_count": d("10"),
        "min_pass_calibration_ready_ratio": d("0.700000"),
        "min_watch_calibration_ready_ratio": d("0.450000"),
    }
    values.update(overrides)
    return report.ResearchEnergyEventTeamMemoryConfig(**values)


def observation(**overrides: object):
    report = api()
    values: dict[str, object] = {
        "event_family": "oil-inventory-cycle",
        "specialist_key": "energy-oil-storage",
        "memory_score": d("0.880000"),
        "source_count": d("8"),
        "fresh_source_count": d("7"),
        "stale_source_count": d("1"),
        "latest_source_observed_at": GENERATED_AT_UTC - timedelta(hours=4),
        "evidence_reuse_count": d("6"),
        "calibration_sample_count": d("44"),
        "calibration_ready_ratio": d("0.820000"),
    }
    values.update(overrides)
    return report.ResearchEnergyEventTeamMemoryObservation(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_energy_event_team_memory_report(
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


def test_energy_event_team_memory_rolls_up_source_evidence_and_calibration() -> None:
    report = api()
    memory_report = build_report(
        observation(),
        observation(
            event_family="gas-storage-cycle",
            specialist_key="energy-gas-storage",
            memory_score=d("0.660000"),
            source_count=d("6"),
            fresh_source_count=d("4"),
            stale_source_count=d("2"),
            latest_source_observed_at=GENERATED_AT_UTC - timedelta(hours=20),
            evidence_reuse_count=d("3"),
            calibration_sample_count=d("24"),
            calibration_ready_ratio=d("0.620000"),
        ),
        observation(
            event_family="oil-supply-shock",
            specialist_key="energy-oil-geopolicy",
            memory_score=d("0.320000"),
            source_count=d("4"),
            fresh_source_count=d("1"),
            stale_source_count=d("3"),
            latest_source_observed_at=GENERATED_AT_UTC - timedelta(days=3),
            evidence_reuse_count=d("1"),
            calibration_sample_count=d("8"),
            calibration_ready_ratio=d("0.300000"),
        ),
    )

    assert report.STATUSES == ("pass", "watch", "block")
    assert is_dataclass(memory_report)
    assert type(memory_report) is report.ResearchEnergyEventTeamMemoryReport
    assert memory_report.generated_at == GENERATED_AT_UTC
    assert memory_report.config_version == "research-energy-event-team-memory-report-v0"
    assert memory_report.event_specialist_count == d("3")
    assert memory_report.source_count == d("18")
    assert memory_report.fresh_source_count == d("12")
    assert memory_report.stale_source_count == d("6")
    assert memory_report.evidence_reuse_count == d("10")
    assert memory_report.calibration_sample_count == d("76")
    assert memory_report.average_memory_score == d("0.620000")
    assert memory_report.overall_source_freshness_ratio == d("0.666667")
    assert memory_report.overall_evidence_reuse_ratio == d("0.555556")
    assert memory_report.average_calibration_ready_ratio == d("0.580000")
    assert memory_report.min_calibration_sample_count == d("8")
    assert memory_report.max_source_age_seconds == d("259200")
    assert memory_report.pass_count == d("1")
    assert memory_report.watch_count == d("1")
    assert memory_report.block_count == d("1")
    assert memory_report.status == "block"
    assert memory_report.paper_only is True
    assert memory_report.report_only is True
    assert memory_report.readonly is True

    assert tuple((row.status, row.event_family, row.specialist_key) for row in memory_report.rows) == (
        ("block", "oil-supply-shock", "energy-oil-geopolicy"),
        ("watch", "gas-storage-cycle", "energy-gas-storage"),
        ("pass", "oil-inventory-cycle", "energy-oil-storage"),
    )

    blocked, watched, passed = memory_report.rows
    assert type(blocked) is report.ResearchEnergyEventTeamMemoryRow
    assert blocked.source_freshness_ratio == d("0.250000")
    assert blocked.evidence_reuse_ratio == d("0.250000")
    assert blocked.source_age_seconds == d("259200")
    assert blocked.reason_codes == (
        "energy_event_team_memory_block",
        "memory_score_below_watch",
        "source_freshness_below_watch",
        "source_age_above_watch",
        "evidence_reuse_below_watch",
        "calibration_sample_below_watch",
        "calibration_ready_below_watch",
    )
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "energy_event_team_memory_watch",
        "memory_score_below_pass",
        "source_freshness_below_pass",
        "source_age_above_pass",
        "evidence_reuse_below_pass",
        "calibration_sample_below_pass",
        "calibration_ready_below_pass",
    )
    assert passed.status == "pass"
    assert passed.reason_codes == ("energy_event_team_memory_pass",)
    assert tuple(
        (reason_count.reason_code, reason_count.count)
        for reason_count in memory_report.reason_code_counts
    )[:3] == (
        ("energy_event_team_memory_block", d("1")),
        ("energy_event_team_memory_watch", d("1")),
        ("energy_event_team_memory_pass", d("1")),
    )


def test_empty_report_blocks_with_zero_aggregates() -> None:
    memory_report = build_report()

    assert memory_report.event_specialist_count == d("0")
    assert memory_report.source_count == d("0")
    assert memory_report.evidence_reuse_count == d("0")
    assert memory_report.calibration_sample_count == d("0")
    assert memory_report.average_memory_score == d("0.000000")
    assert memory_report.overall_source_freshness_ratio == d("0.000000")
    assert memory_report.overall_evidence_reuse_ratio == d("0.000000")
    assert memory_report.average_calibration_ready_ratio == d("0.000000")
    assert memory_report.min_calibration_sample_count == d("0")
    assert memory_report.max_source_age_seconds == d("0")
    assert memory_report.status == "block"
    assert memory_report.reason_codes == ("energy_event_team_memory_no_observations",)
    assert memory_report.rows == ()


def test_payload_digest_is_deterministic_json_ready_and_public_safe() -> None:
    report = api()
    first = build_report(
        observation(event_family="oil-inventory-cycle"),
        observation(event_family="gas-storage-cycle", specialist_key="energy-gas-storage"),
    )
    second = build_report(
        observation(event_family="gas-storage-cycle", specialist_key="energy-gas-storage"),
        observation(event_family="oil-inventory-cycle"),
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert report.research_energy_event_team_memory_report_digest(first) == (
        first.derived_validation_digest
    )
    payload = report.research_energy_event_team_memory_report_payload(first)
    json.dumps(payload, sort_keys=True)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T13:30:00+00:00"
    assert payload["rows"][0]["memory_score"] == "0.880000"
    assert payload["rows"][0]["source_freshness_ratio"] == "0.875000"
    assert payload["rows"][0]["evidence_reuse_ratio"] == "0.750000"
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


def test_frozen_decimal_only_flags_validation_and_side_effect_surface() -> None:
    report = api()
    memory_report = build_report(observation())

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
        type("BadObservation", (report.ResearchEnergyEventTeamMemoryObservation,), {})

    with pytest.raises(ValueError, match="min_pass_memory_score"):
        config(min_pass_memory_score=d("0.400000"))
    with pytest.raises(ValueError, match="min_watch_source_freshness_ratio"):
        config(min_watch_source_freshness_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            observation(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 13, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="memory_score"):
        observation(memory_score=0.88)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_reuse_count"):
        observation(evidence_reuse_count=d("9"))
    with pytest.raises(ValueError, match="fresh and stale source counts"):
        observation(fresh_source_count=d("6"), stale_source_count=d("1"))
    with pytest.raises(ValueError, match="latest_source_observed_at"):
        build_report(
            observation(latest_source_observed_at=GENERATED_AT_UTC + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(memory_report, readonly=False)

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
        replace(memory_report, status="ready")
    assert memory_report.status in report.STATUSES

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
    assert {field.name for field in fields(report.ResearchEnergyEventTeamMemoryObservation)} == {
        "event_family",
        "specialist_key",
        "memory_score",
        "source_count",
        "fresh_source_count",
        "stale_source_count",
        "latest_source_observed_at",
        "evidence_reuse_count",
        "calibration_sample_count",
        "calibration_ready_ratio",
        "paper_only",
        "report_only",
        "readonly",
    }
