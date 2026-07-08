from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_event_category_prior_art_memory_report as api
from polymarket_alpha_lab.research_event_category_prior_art_memory_report import (
    ResearchEventCategoryPriorArtMemoryConfig,
    ResearchEventCategoryPriorArtMemoryReport,
    ResearchEventCategoryPriorArtMemoryRow,
    ResearchEventCategoryPriorArtMemorySample,
    build_research_event_category_prior_art_memory_report,
    research_event_category_prior_art_memory_report_digest,
    research_event_category_prior_art_memory_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_category_prior_art_memory_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 9, 30, tzinfo=timezone(timedelta(hours=-4)))
GENERATED_AT_UTC = datetime(2026, 7, 8, 13, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventCategoryPriorArtMemoryConfig:
    values: dict[str, object] = {
        "config_version": "research-event-category-prior-art-memory-report-v0",
        "min_pass_historical_sample_count": d("20"),
        "min_watch_historical_sample_count": d("5"),
        "min_pass_calibration_quality_ratio": d("0.700000"),
        "min_watch_calibration_quality_ratio": d("0.500000"),
        "max_pass_resolution_ambiguity_ratio": d("0.100000"),
        "max_watch_resolution_ambiguity_ratio": d("0.300000"),
        "min_pass_source_reliability_ratio": d("0.700000"),
        "min_watch_source_reliability_ratio": d("0.500000"),
        "max_pass_stale_memory_ratio": d("0.150000"),
        "max_watch_stale_memory_ratio": d("0.400000"),
    }
    values.update(overrides)
    return ResearchEventCategoryPriorArtMemoryConfig(**values)


def sample(**overrides: object) -> ResearchEventCategoryPriorArtMemorySample:
    values: dict[str, object] = {
        "event_category": "politics",
        "event_subcategory": "elections",
        "historical_sample_count": d("100"),
        "calibrated_sample_count": d("82"),
        "miscalibrated_sample_count": d("18"),
        "ambiguous_resolution_count": d("5"),
        "reliable_source_sample_count": d("90"),
        "stale_memory_sample_count": d("8"),
    }
    values.update(overrides)
    return ResearchEventCategoryPriorArtMemorySample(**values)


def report(
    *items: ResearchEventCategoryPriorArtMemorySample,
    cfg: ResearchEventCategoryPriorArtMemoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventCategoryPriorArtMemoryReport:
    return build_research_event_category_prior_art_memory_report(
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


def test_rolls_up_public_prior_art_memory_by_category_and_subcategory() -> None:
    memory_report = report(
        sample(),
        sample(
            event_category="crypto",
            event_subcategory="etf",
            historical_sample_count=d("30"),
            calibrated_sample_count=d("17"),
            miscalibrated_sample_count=d("13"),
            ambiguous_resolution_count=d("8"),
            reliable_source_sample_count=d("19"),
            stale_memory_sample_count=d("6"),
        ),
        sample(
            event_category="sports",
            event_subcategory="injuries",
            historical_sample_count=d("8"),
            calibrated_sample_count=d("2"),
            miscalibrated_sample_count=d("6"),
            ambiguous_resolution_count=d("4"),
            reliable_source_sample_count=d("2"),
            stale_memory_sample_count=d("5"),
        ),
    )

    assert api.STATUSES == ("pass", "watch", "block")
    assert is_dataclass(memory_report)
    assert type(memory_report) is ResearchEventCategoryPriorArtMemoryReport
    assert memory_report.generated_at == GENERATED_AT_UTC
    assert memory_report.category_subcategory_count == d("3")
    assert memory_report.historical_sample_count == d("138")
    assert memory_report.calibrated_sample_count == d("101")
    assert memory_report.miscalibrated_sample_count == d("37")
    assert memory_report.ambiguous_resolution_count == d("17")
    assert memory_report.reliable_source_sample_count == d("111")
    assert memory_report.stale_memory_sample_count == d("19")
    assert memory_report.average_calibration_quality_ratio == d("0.545556")
    assert memory_report.overall_resolution_ambiguity_ratio == d("0.123188")
    assert memory_report.overall_source_reliability_ratio == d("0.804348")
    assert memory_report.overall_stale_memory_ratio == d("0.137681")
    assert memory_report.pass_count == d("1")
    assert memory_report.watch_count == d("1")
    assert memory_report.block_count == d("1")
    assert memory_report.status == "block"
    assert memory_report.paper_only is True
    assert memory_report.report_only is True
    assert memory_report.readonly is True

    assert tuple((row.event_category, row.event_subcategory) for row in memory_report.rows) == (
        ("sports", "injuries"),
        ("crypto", "etf"),
        ("politics", "elections"),
    )

    blocked, watched, passed = memory_report.rows
    assert type(blocked) is ResearchEventCategoryPriorArtMemoryRow
    assert blocked.status == "block"
    assert blocked.calibration_quality_ratio == d("0.250000")
    assert blocked.resolution_ambiguity_ratio == d("0.500000")
    assert blocked.source_reliability_ratio == d("0.250000")
    assert blocked.stale_memory_ratio == d("0.625000")
    assert blocked.reason_codes == (
        "prior_art_memory_block",
        "calibration_quality_below_watch",
        "resolution_ambiguity_above_watch",
        "source_reliability_below_watch",
        "stale_memory_above_watch",
    )
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "prior_art_memory_watch",
        "calibration_quality_below_pass",
        "resolution_ambiguity_above_pass",
        "source_reliability_below_pass",
        "stale_memory_above_pass",
    )
    assert passed.status == "pass"
    assert passed.reason_codes == ("prior_art_memory_pass",)
    assert tuple(
        (reason_count.reason_code, reason_count.count)
        for reason_count in memory_report.reason_code_counts
    )[:3] == (
        ("prior_art_memory_block", d("1")),
        ("prior_art_memory_watch", d("1")),
        ("prior_art_memory_pass", d("1")),
    )


def test_empty_report_is_public_safe_block_with_zero_aggregates() -> None:
    memory_report = report()

    assert memory_report.category_subcategory_count == d("0")
    assert memory_report.historical_sample_count == d("0")
    assert memory_report.average_calibration_quality_ratio == d("0.000000")
    assert memory_report.overall_resolution_ambiguity_ratio == d("0.000000")
    assert memory_report.overall_source_reliability_ratio == d("0.000000")
    assert memory_report.overall_stale_memory_ratio == d("0.000000")
    assert memory_report.status == "block"
    assert memory_report.reason_codes == ("prior_art_memory_no_samples",)
    assert memory_report.rows == ()


def test_payload_digest_is_deterministic_json_ready_and_public_safe() -> None:
    first = report(
        sample(event_category="crypto", event_subcategory="etf"),
        sample(event_category="politics", event_subcategory="elections"),
    )
    second = report(
        sample(event_category="politics", event_subcategory="elections"),
        sample(event_category="crypto", event_subcategory="etf"),
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert research_event_category_prior_art_memory_report_digest(first) == (
        first.derived_validation_digest
    )
    payload = research_event_category_prior_art_memory_report_payload(first)
    json.dumps(payload, sort_keys=True)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T13:30:00+00:00"
    assert payload["rows"][0]["historical_sample_count"] == "100"
    assert payload["rows"][0]["calibration_quality_ratio"] == "0.820000"
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


def test_frozen_dataclasses_decimal_only_numbers_and_hard_flags_are_enforced() -> None:
    memory_report = report(sample())

    with pytest.raises(FrozenInstanceError):
        memory_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        memory_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadConfig", (ResearchEventCategoryPriorArtMemoryConfig,), {})

    with pytest.raises(ValueError, match="min_pass_historical_sample_count"):
        config(min_pass_historical_sample_count=20)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_watch_calibration_quality_ratio"):
        config(min_watch_calibration_quality_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            sample(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 13, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="historical_sample_count"):
        sample(historical_sample_count=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="historical_sample_count"):
        sample(historical_sample_count=d("1.5"))
    with pytest.raises(ValueError, match="calibration counts"):
        sample(calibrated_sample_count=d("81"))
    with pytest.raises(ValueError, match="ambiguous_resolution_count"):
        sample(ambiguous_resolution_count=d("101"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(memory_report, readonly=False)


def test_public_identifiers_and_status_surface_reject_unsafe_values() -> None:
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
            sample(event_category=value)
        with pytest.raises(ValueError, match="public-safe"):
            sample(event_subcategory=value)

    with pytest.raises(ValueError, match="status"):
        replace(memory_report := report(sample()), status="ready")
    assert memory_report.status in api.STATUSES


def test_module_has_no_io_database_network_or_execution_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imported_modules: set[str] = set()
    called_names: set[str] = set()
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
    assert {field.name for field in fields(ResearchEventCategoryPriorArtMemorySample)} == {
        "event_category",
        "event_subcategory",
        "historical_sample_count",
        "calibrated_sample_count",
        "miscalibrated_sample_count",
        "ambiguous_resolution_count",
        "reliable_source_sample_count",
        "stale_memory_sample_count",
        "paper_only",
        "report_only",
        "readonly",
    }
