from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_scraping_need_classifier import (
    ResearchSourceScrapingNeedConfig,
    ResearchSourceScrapingNeedGap,
    ResearchSourceScrapingNeedReport,
    ResearchSourceScrapingNeedRow,
    build_research_source_scraping_need_report,
    research_source_scraping_need_report_digest,
    research_source_scraping_need_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceScrapingNeedConfig:
    values = {
        "config_version": "research-source-scraping-need-classifier-v0",
        "min_source_family_count": d("2"),
        "watch_need_score": d("0.250000"),
        "block_need_score": d("0.800000"),
        "missing_official_weight": d("0.250000"),
        "missing_independent_weight": d("0.200000"),
        "staleness_weight": d("0.200000"),
        "scrapling_weight": d("0.150000"),
        "browser_weight": d("0.200000"),
        "manual_verification_weight": d("0.400000"),
        "conflict_weight": d("0.300000"),
        "low_diversity_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchSourceScrapingNeedConfig(**values)


def gap(
    public_gap_key: str,
    *,
    gap_kind: str = "official_resolution",
    freshness_score: Decimal = d("0.950000"),
    source_family_count: Decimal = d("2"),
    has_official_anchor: bool = True,
    has_independent_source: bool = True,
    needs_dynamic_rendering: bool = False,
    needs_unstructured_extraction: bool = False,
    requires_human_verification: bool = False,
    conflict_flag: bool = False,
    public_note: str | None = None,
) -> ResearchSourceScrapingNeedGap:
    return ResearchSourceScrapingNeedGap(
        public_gap_key=public_gap_key,
        gap_kind=gap_kind,
        freshness_score=freshness_score,
        source_family_count=source_family_count,
        has_official_anchor=has_official_anchor,
        has_independent_source=has_independent_source,
        needs_dynamic_rendering=needs_dynamic_rendering,
        needs_unstructured_extraction=needs_unstructured_extraction,
        requires_human_verification=requires_human_verification,
        conflict_flag=conflict_flag,
        public_note=public_note,
    )


def report(
    gaps: tuple[ResearchSourceScrapingNeedGap, ...],
    *,
    cfg: ResearchSourceScrapingNeedConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceScrapingNeedReport:
    return build_research_source_scraping_need_report(
        gaps,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_pass_watch_and_block_classifications_are_safe_task_types() -> None:
    scraping_report = report(
        (
            gap("gap-browser", needs_dynamic_rendering=True),
            gap(
                "gap-manual",
                requires_human_verification=True,
                conflict_flag=True,
            ),
            gap(
                "gap-agent",
                has_independent_source=False,
                source_family_count=d("1"),
                freshness_score=d("0.700000"),
            ),
            gap("gap-pass"),
        ),
    )

    assert scraping_report.status == "block"
    assert scraping_report.gap_count == d("4")
    assert scraping_report.pass_count == d("1")
    assert scraping_report.watch_count == d("2")
    assert scraping_report.block_count == d("1")
    assert scraping_report.agent_reach_count == d("1")
    assert scraping_report.scrapling_count == d("0")
    assert scraping_report.browser_count == d("1")
    assert scraping_report.manual_verification_count == d("1")
    assert scraping_report.paper_only is True
    assert scraping_report.report_only is True
    assert scraping_report.readonly is True

    rows = {row.public_gap_key: row for row in scraping_report.rows}
    assert rows["gap-pass"].status == "pass"
    assert rows["gap-pass"].task_types == ("none",)
    assert rows["gap-pass"].need_score == d("0.010000")
    assert rows["gap-agent"].status == "watch"
    assert rows["gap-agent"].task_types == ("agent_reach",)
    assert rows["gap-browser"].status == "watch"
    assert rows["gap-browser"].task_types == ("browser",)
    assert rows["gap-manual"].status == "block"
    assert rows["gap-manual"].task_types == ("manual_verification",)
    assert rows["gap-manual"].reason_codes == (
        "conflict_flag_present",
        "manual_verification_required",
        "scraping_need_block",
    )


def test_type_decimal_and_datetime_rejections_are_strict() -> None:
    with pytest.raises(ValueError, match="watch_need_score"):
        config(watch_need_score=0.25)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_need_score"):
        config(block_need_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="freshness_score"):
        gap("gap-type", freshness_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_family_count"):
        gap("gap-type", source_family_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="has_official_anchor"):
        replace(gap("gap-type"), has_official_anchor=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="gap_kind"):
        gap("gap-type", gap_kind="raw_web_page")
    with pytest.raises(ValueError, match="generated_at"):
        report((gap("gap-type"),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((gap("gap-type"),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))


def test_public_leak_rejection_blocks_raw_identifiers_urls_and_trading_language() -> None:
    unsafe_examples = (
        ("candidate-123", {}),
        ("market-slug-raw", {}),
        ("question-raw", {}),
        ("source-url-raw", {}),
        ("gap-safe", {"public_note": "contains https://example.test/source"}),
        ("gap-safe", {"public_note": "dsn table token should not surface"}),
        ("gap-safe", {"public_note": "buy sell trade position language"}),
        ("gap-safe", {"public_note": "wallet order auth field"}),
    )

    for public_gap_key, kwargs in unsafe_examples:
        with pytest.raises(ValueError, match="unsafe"):
            gap(public_gap_key, **kwargs)

    safe_report = report((gap("gap-safe"),))
    payload_text = json.dumps(
        research_source_scraping_need_report_payload(safe_report),
        sort_keys=True,
    ).lower()
    forbidden_public_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    assert all(fragment not in payload_text for fragment in forbidden_public_fragments)


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    safe_gap = gap("gap-hard-flags")
    safe_report = report((safe_gap,))

    with pytest.raises(ValueError, match="paper_only"):
        replace(safe_gap, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(safe_report, readonly=False)
    with pytest.raises(FrozenInstanceError):
        safe_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        safe_report.rows[0].need_score = d("0.500000")  # type: ignore[misc]


def test_payload_digest_and_rows_are_deterministic_and_json_ready() -> None:
    input_gaps = (
        gap("gap-z", needs_unstructured_extraction=True),
        gap("gap-a"),
        gap("gap-m", has_official_anchor=False, freshness_score=d("0.600000")),
    )
    first = report(input_gaps)
    second = report(tuple(reversed(input_gaps)))

    first_payload = research_source_scraping_need_report_payload(first)
    second_payload = research_source_scraping_need_report_payload(second)

    assert tuple(row.public_gap_key for row in first.rows) == ("gap-a", "gap-m", "gap-z")
    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert research_source_scraping_need_report_digest(first) == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert first_payload["rows"][0]["need_score"] == str(first.rows[0].need_score)

    encoded = json.dumps(first_payload, sort_keys=True)
    assert ": 0." not in encoded
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_owned_module_has_no_network_filesystem_or_live_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_scraping_need_classifier.py"
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
        "browser.",
        "scrapling.",
        "agent_reach.",
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
