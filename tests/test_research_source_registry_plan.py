from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_registry_plan import (
    ResearchSourceRegistryCandidate,
    ResearchSourceRegistryCategoryPlan,
    ResearchSourceRegistryPlanConfig,
    ResearchSourceRegistryPlanReport,
    ResearchSourceRegistryPlanRow,
    build_research_source_registry_plan,
    research_source_registry_plan_payload,
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceRegistryPlanConfig:
    values = {
        "config_version": "research-source-registry-plan-v0",
        "min_pass_reliability_score": d("0.750000"),
        "min_watch_reliability_score": d("0.500000"),
        "max_pass_refresh_frequency_minutes": d("1440"),
        "max_watch_refresh_frequency_minutes": d("10080"),
        "min_pass_audit_event_count": d("2"),
    }
    values.update(overrides)
    return ResearchSourceRegistryPlanConfig(**values)


def candidate(
    *,
    source_category: str = "official",
    reliability_score: Decimal = d("0.920000"),
    refresh_frequency_minutes: Decimal = d("720"),
    audit_trail_state: str = "complete",
    audit_event_count: Decimal = d("3"),
) -> ResearchSourceRegistryCandidate:
    return ResearchSourceRegistryCandidate(
        source_category=source_category,
        reliability_score=reliability_score,
        refresh_frequency_minutes=refresh_frequency_minutes,
        audit_trail_state=audit_trail_state,
        audit_event_count=audit_event_count,
    )


def report(
    candidates: tuple[ResearchSourceRegistryCandidate, ...],
    *,
    cfg: ResearchSourceRegistryPlanConfig | None = None,
) -> ResearchSourceRegistryPlanReport:
    return build_research_source_registry_plan(candidates, config=cfg or config())


def test_registration_complete_sources_pass_with_redacted_registry_plan() -> None:
    registry_report = report(
        (
            candidate(source_category="venue", reliability_score=d("0.870000")),
            candidate(source_category="official", reliability_score=d("0.920000")),
        ),
    )

    assert type(registry_report) is ResearchSourceRegistryPlanReport
    assert registry_report.status == "pass"
    assert registry_report.candidate_count == d("2")
    assert registry_report.pass_count == d("2")
    assert registry_report.watch_count == d("0")
    assert registry_report.block_count == d("0")
    assert registry_report.paper_only is True
    assert registry_report.report_only is True
    assert registry_report.readonly is True

    assert tuple(row.registry_key for row in registry_report.rows) == (
        "redacted-source-registry-001",
        "redacted-source-registry-002",
    )
    assert tuple(row.source_category for row in registry_report.rows) == (
        "official",
        "venue",
    )
    assert tuple(row.status for row in registry_report.rows) == ("pass", "pass")
    assert tuple(row.reliability_tier for row in registry_report.rows) == (
        "high",
        "high",
    )
    assert tuple(row.refresh_frequency_tier for row in registry_report.rows) == (
        "daily",
        "daily",
    )
    assert registry_report.category_plans == (
        ResearchSourceRegistryCategoryPlan(
            source_category="official",
            candidate_count=d("1"),
            pass_count=d("1"),
            watch_count=d("0"),
            block_count=d("0"),
            status="pass",
            reason_codes=("category_registry_pass",),
        ),
        ResearchSourceRegistryCategoryPlan(
            source_category="venue",
            candidate_count=d("1"),
            pass_count=d("1"),
            watch_count=d("0"),
            block_count=d("0"),
            status="pass",
            reason_codes=("category_registry_pass",),
        ),
    )

    payload = research_source_registry_plan_payload(registry_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["status"] == "pass"
    assert payload["upstream_write_plan"] == "report_only_registry_upsert_plan"
    assert payload["rows"][0]["registry_key"] == "redacted-source-registry-001"
    assert not any(_is_forbidden_number(value) for value in _walk_payload_values(payload))
    assert "raw-candidate" not in encoded
    assert "market-" not in encoded


def test_partial_audit_or_borderline_quality_routes_to_watch() -> None:
    registry_report = report(
        (
            candidate(
                source_category="regulator",
                reliability_score=d("0.640000"),
                refresh_frequency_minutes=d("2880"),
                audit_trail_state="partial",
                audit_event_count=d("1"),
            ),
        ),
    )

    assert registry_report.status == "watch"
    assert registry_report.pass_count == d("0")
    assert registry_report.watch_count == d("1")
    assert registry_report.block_count == d("0")

    row = registry_report.rows[0]
    assert row.status == "watch"
    assert row.reliability_tier == "medium"
    assert row.refresh_frequency_tier == "weekly"
    assert row.reason_codes == (
        "audit_event_count_below_pass_threshold",
        "audit_trail_partial",
        "refresh_frequency_above_pass_threshold",
        "reliability_below_pass_threshold",
        "registry_plan_watch",
    )


def test_quality_insufficient_sources_block_registry_plan() -> None:
    registry_report = report(
        (
            candidate(
                source_category="community",
                reliability_score=d("0.250000"),
                refresh_frequency_minutes=d("20160"),
                audit_trail_state="missing",
                audit_event_count=d("0"),
            ),
        ),
    )

    assert registry_report.status == "block"
    assert registry_report.pass_count == d("0")
    assert registry_report.watch_count == d("0")
    assert registry_report.block_count == d("1")

    row = registry_report.rows[0]
    assert row.status == "block"
    assert row.reliability_tier == "low"
    assert row.refresh_frequency_tier == "stale"
    assert row.reason_codes == (
        "audit_event_count_missing",
        "audit_trail_missing",
        "refresh_frequency_above_watch_threshold",
        "reliability_below_watch_threshold",
        "registry_plan_block",
    )


def test_type_validation_rejects_non_decimal_subclasses_and_bad_statuses() -> None:
    with pytest.raises(ValueError, match="min_pass_reliability_score"):
        config(min_pass_reliability_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_watch_reliability_score"):
        config(min_watch_reliability_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="reliability_score"):
        candidate(reliability_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="refresh_frequency_minutes"):
        candidate(refresh_frequency_minutes=720)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_category"):
        candidate(source_category="prediction")
    with pytest.raises(ValueError, match="audit_trail_state"):
        candidate(audit_trail_state="unknown")
    with pytest.raises(ValueError, match="candidates"):
        build_research_source_registry_plan("not-candidates", config=config())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="candidate"):
        build_research_source_registry_plan((object(),), config=config())  # type: ignore[arg-type]

    registry_report = report((candidate(),))
    with pytest.raises(FrozenInstanceError):
        registry_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        registry_report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(registry_report.rows[0], status="blocked")


def test_leak_rejection_blocks_raw_ids_market_source_refs_and_trading_language() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        ResearchSourceRegistryPlanRow(
            plan_rank=d("1"),
            registry_key="wallet-auth-leak",
            source_category="official",
            reliability_score=d("0.920000"),
            reliability_tier="high",
            refresh_frequency_minutes=d("720"),
            refresh_frequency_tier="daily",
            audit_trail_state="complete",
            audit_event_count=d("3"),
            status="pass",
            reason_codes=("registry_plan_pass",),
        )
    with pytest.raises(ValueError, match="unsafe"):
        ResearchSourceRegistryPlanRow(
            plan_rank=d("1"),
            registry_key="redacted-source-registry-001",
            source_category="official",
            reliability_score=d("0.920000"),
            reliability_tier="high",
            refresh_frequency_minutes=d("720"),
            refresh_frequency_tier="daily",
            audit_trail_state="complete",
            audit_event_count=d("3"),
            status="pass",
            reason_codes=("buy_recommendation",),
        )

    payload = research_source_registry_plan_payload(report((candidate(),)))
    with pytest.raises(ValueError, match="unsafe"):
        research_source_registry_plan_payload(
            {**payload, "upstream_write_plan": "buy this market_slug now"},
        )
    with pytest.raises(ValueError, match="unsupported"):
        research_source_registry_plan_payload({**payload, "source_url": "https://example.test"})


def test_hard_flags_are_required_on_configs_candidates_reports_and_payloads() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(candidate(), readonly=False)

    registry_report = report((candidate(),))
    with pytest.raises(ValueError, match="report_only"):
        replace(registry_report, report_only=False)

    payload = research_source_registry_plan_payload(registry_report)
    with pytest.raises(ValueError, match="readonly"):
        research_source_registry_plan_payload({**payload, "readonly": False})


def test_registry_plan_payload_is_deterministic_for_equivalent_inputs() -> None:
    official = candidate(source_category="official", reliability_score=d("0.920000"))
    venue = candidate(source_category="venue", reliability_score=d("0.870000"))
    first_payload = research_source_registry_plan_payload(report((venue, official)))
    second_payload = research_source_registry_plan_payload(report((official, venue)))

    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_module_has_no_network_filesystem_or_database_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_registry_plan.py"
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
        "psycopg",
        "sqlalchemy",
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


def _is_forbidden_number(value: object) -> bool:
    return type(value) is int or type(value) is float
