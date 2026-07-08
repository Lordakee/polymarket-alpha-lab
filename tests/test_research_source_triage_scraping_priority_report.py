from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_triage_scraping_priority_report import (
    ResearchSourceTriageScrapingPriorityConfig,
    ResearchSourceTriageScrapingPriorityInput,
    ResearchSourceTriageScrapingPriorityReasonCodeCount,
    ResearchSourceTriageScrapingPriorityReport,
    ResearchSourceTriageScrapingPriorityRow,
    build_research_source_triage_scraping_priority_report,
    research_source_triage_scraping_priority_report_digest,
    research_source_triage_scraping_priority_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceTriageScrapingPriorityConfig:
    values = {
        "config_version": "research-source-triage-scraping-priority-report-v0",
        "fresh_source_age_seconds": d("3600"),
        "stale_source_age_seconds": d("86400"),
        "pass_priority_threshold": d("0.600000"),
        "watch_priority_threshold": d("0.300000"),
        "reliability_block_floor": d("0.250000"),
        "reliability_watch_floor": d("0.500000"),
        "manual_check_contradiction_threshold": d("0.600000"),
        "freshness_weight": d("0.250000"),
        "reliability_weight": d("0.200000"),
        "catalyst_weight": d("0.200000"),
        "contradiction_weight": d("0.200000"),
        "coverage_gap_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchSourceTriageScrapingPriorityConfig(**values)


def source_input(
    source_class_id: str,
    *,
    latest_source_age_seconds: Decimal = Decimal("7200"),
    reliability_memory_score: Decimal = Decimal("0.800000"),
    catalyst_pressure_score: Decimal = Decimal("0.700000"),
    contradiction_score: Decimal = Decimal("0.100000"),
    coverage_gap_score: Decimal = Decimal("0.500000"),
    public_item_count: Decimal = Decimal("3"),
    required_item_count: Decimal = Decimal("5"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceTriageScrapingPriorityInput:
    return ResearchSourceTriageScrapingPriorityInput(
        source_class_id=source_class_id,
        latest_source_age_seconds=latest_source_age_seconds,
        reliability_memory_score=reliability_memory_score,
        catalyst_pressure_score=catalyst_pressure_score,
        contradiction_score=contradiction_score,
        coverage_gap_score=coverage_gap_score,
        public_item_count=public_item_count,
        required_item_count=required_item_count,
        reason_codes=reason_codes,
    )


def build_report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceTriageScrapingPriorityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceTriageScrapingPriorityReport:
    return build_research_source_triage_scraping_priority_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_with_hard_flags() -> None:
    report = build_report(())

    assert type(report) is ResearchSourceTriageScrapingPriorityReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-source-triage-scraping-priority-report-v0"
    assert report.source_class_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.scrape_count == d("0")
    assert report.manual_check_count == d("0")
    assert report.average_priority_score is None
    assert report.status == "block"
    assert report.rows == ()
    assert report.reason_codes == ("no_public_source_classes",)
    assert report.reason_code_counts == (
        ResearchSourceTriageScrapingPriorityReasonCodeCount(
            reason_code="no_public_source_classes",
            count=d("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_prioritizes_stale_reliable_catalyst_and_gap_sources_deterministically() -> None:
    report = build_report(
        (
            source_input(
                "secondary_context_feeds",
                latest_source_age_seconds=d("1800"),
                reliability_memory_score=d("0.650000"),
                catalyst_pressure_score=d("0.100000"),
                contradiction_score=d("0.000000"),
                coverage_gap_score=d("0.100000"),
                public_item_count=d("4"),
                required_item_count=d("4"),
            ),
            source_input(
                "official_event_pages",
                latest_source_age_seconds=d("172800"),
                reliability_memory_score=d("0.950000"),
                catalyst_pressure_score=d("0.900000"),
                contradiction_score=d("0.400000"),
                coverage_gap_score=d("0.800000"),
                public_item_count=d("1"),
                required_item_count=d("5"),
                reason_codes=("manually_seen_gap",),
            ),
            source_input(
                "public_archive_backfill",
                latest_source_age_seconds=d("90000"),
                reliability_memory_score=d("0.200000"),
                catalyst_pressure_score=d("0.200000"),
                contradiction_score=d("0.100000"),
                coverage_gap_score=d("0.900000"),
                public_item_count=d("0"),
                required_item_count=d("3"),
            ),
        ),
    )

    assert report.status == "watch"
    assert report.source_class_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.scrape_count == d("1")
    assert report.manual_check_count == d("1")
    assert report.average_priority_score == d("0.490000")

    rows = report.rows
    assert tuple(row.source_class_id for row in rows) == (
        "official_event_pages",
        "public_archive_backfill",
        "secondary_context_feeds",
    )
    assert tuple(row.priority_rank for row in rows) == (d("1"), d("2"), d("3"))

    top = rows[0]
    assert type(top) is ResearchSourceTriageScrapingPriorityRow
    assert top.source_class_id == "official_event_pages"
    assert top.freshness_pressure_score == d("1.000000")
    assert top.reliability_memory_score == d("0.950000")
    assert top.catalyst_pressure_score == d("0.900000")
    assert top.contradiction_score == d("0.400000")
    assert top.coverage_gap_score == d("0.800000")
    assert top.observed_coverage_ratio == d("0.200000")
    assert top.priority_score == d("0.820000")
    assert top.status == "pass"
    assert top.collection_mode == "scrape"
    assert top.reason_codes == (
        "coverage_gap_pressure",
        "freshness_gap_pressure",
        "input_manually_seen_gap",
        "public_collection_scrape",
        "research_source_triage_priority_pass",
    )

    assert rows[1].status == "block"
    assert rows[1].collection_mode == "defer"
    assert "reliability_memory_below_block_floor" in rows[1].reason_codes
    assert rows[2].status == "watch"
    assert rows[2].collection_mode == "manual_check"
    assert "low_priority_watch" in rows[2].reason_codes


def test_contradiction_pressure_routes_to_manual_check_without_blocking() -> None:
    report = build_report(
        (
            source_input(
                "public_filings",
                latest_source_age_seconds=d("4000"),
                reliability_memory_score=d("0.700000"),
                catalyst_pressure_score=d("0.400000"),
                contradiction_score=d("0.750000"),
                coverage_gap_score=d("0.400000"),
                public_item_count=d("2"),
                required_item_count=d("4"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "watch"
    assert report.pass_count == d("0")
    assert report.watch_count == d("1")
    assert row.status == "watch"
    assert row.collection_mode == "manual_check"
    assert row.priority_score == d("0.441574")
    assert row.reason_codes == (
        "contradiction_pressure",
        "manual_check_contradiction",
        "public_collection_manual_check",
        "research_source_triage_priority_watch",
    )


def test_payload_and_digest_are_deterministic_decimal_only_and_payload_safe() -> None:
    rows = (
        source_input("z_public_calendar", reason_codes=("zeta", "alpha")),
        source_input(
            "a_official_feed",
            latest_source_age_seconds=d("172800"),
            reliability_memory_score=d("0.900000"),
            catalyst_pressure_score=d("0.800000"),
            contradiction_score=d("0.100000"),
            coverage_gap_score=d("0.900000"),
            public_item_count=d("1"),
            required_item_count=d("6"),
        ),
    )
    forward = build_report(rows)
    reverse = build_report(tuple(reversed(rows)))

    forward_payload = research_source_triage_scraping_priority_report_payload(forward)
    reverse_payload = research_source_triage_scraping_priority_report_payload(reverse)
    encoded = json.dumps(forward_payload, sort_keys=True)

    assert forward_payload == reverse_payload
    assert research_source_triage_scraping_priority_report_digest(
        forward,
    ) == research_source_triage_scraping_priority_report_digest(reverse)
    assert tuple(row["source_class_id"] for row in forward_payload["rows"]) == (
        "a_official_feed",
        "z_public_calendar",
    )
    assert forward_payload["rows"][0]["priority_score"] == "0.745000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(forward_payload))
    assert "://" not in encoded
    assert "source_ref" not in encoded
    assert "raw_text" not in encoded
    assert "recommend" not in encoded.lower()
    assert "sizing" not in encoded.lower()


def test_validation_rejects_bad_numeric_types_enums_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="freshness_weight"):
        config(freshness_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_priority_threshold"):
        config(pass_priority_threshold=0.6)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reliability_weight"):
        config(reliability_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report((source_input("official_pages"),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            (source_input("official_pages"),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_class_id"):
        source_input(" https_example ")
    with pytest.raises(ValueError, match="source_class_id"):
        source_input("raw_text_dump")
    with pytest.raises(ValueError, match="latest_source_age_seconds"):
        source_input("official_pages", latest_source_age_seconds=d("-1"))
    with pytest.raises(ValueError, match="reliability_memory_score"):
        source_input("official_pages", reliability_memory_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_item_count"):
        source_input("official_pages", public_item_count=d("1.5"))
    with pytest.raises(ValueError, match="required_item_count"):
        source_input("official_pages", public_item_count=d("5"), required_item_count=d("4"))
    with pytest.raises(ValueError, match="reason_codes"):
        source_input("official_pages", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(source_input("official_pages"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    report = build_report((source_input("official_pages"),))

    with pytest.raises(FrozenInstanceError):
        report.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="priority_score"):
        replace(report.rows[0], priority_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="pass")


def test_owned_module_has_no_io_execution_or_market_action_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_triage_scraping_priority_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "private",
        "live",
        "execution",
        "recommend",
        "sizing",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
