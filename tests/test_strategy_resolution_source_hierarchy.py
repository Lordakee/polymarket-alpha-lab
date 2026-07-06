from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_resolution_source_hierarchy import (
    StrategyResolutionSourceEvidence,
    StrategyResolutionSourceHierarchyReport,
    build_strategy_resolution_source_hierarchy_report,
    strategy_resolution_source_hierarchy_payload,
)


class StrategyResolutionSourceEvidenceSubclass(StrategyResolutionSourceEvidence):
    pass


class StrategyResolutionSourceHierarchyReportSubclass(
    StrategyResolutionSourceHierarchyReport,
):
    pass


def _source(
    source_tier: str = "official_rules",
    *,
    source_id: str | None = None,
) -> StrategyResolutionSourceEvidence:
    return StrategyResolutionSourceEvidence(
        source_id=source_id or f"{source_tier}-source",
        source_tier=source_tier,
    )


def _report(
    *sources: StrategyResolutionSourceEvidence,
) -> StrategyResolutionSourceHierarchyReport:
    return build_strategy_resolution_source_hierarchy_report(sources)


def test_strategy_resolution_source_hierarchy_passes_with_official_rules() -> None:
    report = _report(
        _source("social_rumor"),
        _source("primary_data_source"),
        _source("official_rules"),
    )

    assert report.hierarchy_status == "pass"
    assert report.best_available_source_tier == "official_rules"
    assert report.source_count == 3
    assert report.best_available_source_count == 1
    assert report.reason_codes == ("official_resolution_rules_available",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("source_tier", "best_reason_code"),
    (
        (
            "exchange_polymarket_page",
            "best_available_source_is_exchange_polymarket_page",
        ),
        ("primary_data_source", "best_available_source_is_primary_data_source"),
    ),
)
def test_strategy_resolution_source_hierarchy_watches_nonofficial_primary_sources(
    source_tier: str,
    best_reason_code: str,
) -> None:
    report = _report(_source(source_tier))

    assert report.hierarchy_status == "watch"
    assert report.best_available_source_tier == source_tier
    assert report.reason_codes == (
        "missing_official_resolution_rules",
        best_reason_code,
    )


@pytest.mark.parametrize(
    ("source_tier", "best_reason_code"),
    (
        ("secondary_news", "best_available_source_is_secondary_news"),
        ("social_rumor", "best_available_source_is_social_rumor"),
    ),
)
def test_strategy_resolution_source_hierarchy_blocks_weak_source_tiers(
    source_tier: str,
    best_reason_code: str,
) -> None:
    report = _report(_source(source_tier))

    assert report.hierarchy_status == "blocked"
    assert report.best_available_source_tier == source_tier
    assert report.reason_codes == (
        "missing_official_resolution_rules",
        "weak_resolution_source_hierarchy",
        best_reason_code,
    )


def test_strategy_resolution_source_hierarchy_blocks_missing_sources() -> None:
    report = build_strategy_resolution_source_hierarchy_report(())

    assert report.hierarchy_status == "blocked"
    assert report.best_available_source_tier is None
    assert report.source_count == 0
    assert report.best_available_source_count == 0
    assert report.reason_codes == ("missing_resolution_source",)


def test_strategy_resolution_source_hierarchy_counts_best_tier_sources() -> None:
    report = _report(
        _source("exchange_polymarket_page", source_id="poly-page-1"),
        _source("exchange_polymarket_page", source_id="poly-page-2"),
        _source("primary_data_source", source_id="primary-data-1"),
        _source("secondary_news", source_id="news-1"),
    )

    assert report.hierarchy_status == "watch"
    assert report.best_available_source_tier == "exchange_polymarket_page"
    assert report.source_count == 4
    assert report.best_available_source_count == 2
    assert report.reason_codes == (
        "missing_official_resolution_rules",
        "best_available_source_is_exchange_polymarket_page",
    )


def test_strategy_resolution_source_hierarchy_payload_is_report_only() -> None:
    payload = strategy_resolution_source_hierarchy_payload(
        _report(_source("official_rules")),
    )

    assert payload == {
        "hierarchy_status": "pass",
        "best_available_source_tier": "official_rules",
        "source_count": 1,
        "best_available_source_count": 1,
        "reason_codes": ["official_resolution_rules_available"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("source_id", ""),
        ("source_id", " source "),
        ("source_tier", "blog_post"),
        ("paper_only", False),
        ("report_only", False),
        ("readonly", False),
    ),
)
def test_strategy_resolution_source_hierarchy_sources_validate_inputs(
    field_name: str,
    bad_value: object,
) -> None:
    kwargs: dict[str, object] = {
        "source_id": "official-rules-source",
        "source_tier": "official_rules",
        field_name: bad_value,
    }

    with pytest.raises(ValueError, match=field_name):
        StrategyResolutionSourceEvidence(**kwargs)


def test_strategy_resolution_source_hierarchy_rejects_duplicate_source_ids() -> None:
    duplicate_source = StrategyResolutionSourceEvidence(
        source_id="duplicate-source",
        source_tier="official_rules",
    )

    with pytest.raises(ValueError, match="source_id"):
        build_strategy_resolution_source_hierarchy_report(
            (duplicate_source, duplicate_source),
        )


def test_strategy_resolution_source_hierarchy_outputs_are_frozen_and_consistent() -> None:
    report = _report(_source("official_rules"))

    with pytest.raises(FrozenInstanceError):
        report.hierarchy_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=["official_resolution_rules_available"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="hierarchy_status"):
        replace(report, hierarchy_status="blocked")
    with pytest.raises(ValueError, match="best_available_source_tier"):
        replace(report, best_available_source_tier="social_rumor")
    with pytest.raises(ValueError, match="source_count"):
        replace(report, source_count=-1)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_strategy_resolution_source_hierarchy_rejects_subclasses() -> None:
    source = _source("official_rules")
    report = _report(source)

    with pytest.raises(ValueError, match="source"):
        StrategyResolutionSourceEvidenceSubclass(**source.__dict__)
    with pytest.raises(ValueError, match="report"):
        StrategyResolutionSourceHierarchyReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="source"):
        build_strategy_resolution_source_hierarchy_report(
            (StrategyResolutionSourceEvidenceSubclass(**source.__dict__),),
        )


def test_strategy_resolution_source_hierarchy_rejects_unsafe_source_flags() -> None:
    source = _source("official_rules")
    object.__setattr__(source, "paper_only", False)

    with pytest.raises(ValueError, match="paper_only"):
        _report(source)


def test_strategy_resolution_source_hierarchy_module_scope_stays_pure_readonly() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_resolution_source_hierarchy.py",
    ).read_text(encoding="utf-8")

    for banned_term in (
        "psycopg",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "websocket",
        "websockets",
        "eth_account",
        "private_key",
        "wallet",
        "auth",
        "clob",
        "gamma",
        "supabase",
    ):
        assert banned_term not in source.lower()
