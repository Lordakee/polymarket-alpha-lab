from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.event_archetype_registry_health import (
    EventArchetypeRegistryEntry,
    EventArchetypeRegistryHealthConfig,
    EventArchetypeRegistryObservation,
    build_event_archetype_registry_health_report,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
MODULE_PATH = Path("src/polymarket_alpha_lab/event_archetype_registry_health.py")


def test_registry_health_summarizes_coverage_unknowns_and_template_freshness() -> None:
    report = build_event_archetype_registry_health_report(
        (
            EventArchetypeRegistryEntry(
                domain_id="politics",
                category_id="politics",
                archetype_id="politics_event",
                template_version="politics-template-v1",
                updated_at=GENERATED_AT - timedelta(days=2),
            ),
            EventArchetypeRegistryEntry(
                domain_id="crypto",
                category_id="finance.crypto.btc",
                archetype_id="btc_hit_price",
                template_version="btc-template-v1",
                updated_at=GENERATED_AT - timedelta(days=3),
            ),
            EventArchetypeRegistryEntry(
                domain_id="macro",
                category_id="finance.macro.rates",
                archetype_id="fed_rate_decision",
                template_version="macro-template-v1",
                updated_at=GENERATED_AT - timedelta(days=30),
            ),
            EventArchetypeRegistryEntry(
                domain_id="commodities",
                category_id="finance.commodities.gold",
                archetype_id="gold_hit_price",
                template_version="gold-template-v1",
                updated_at=GENERATED_AT - timedelta(days=10),
            ),
            EventArchetypeRegistryEntry(
                domain_id="sports",
                category_id="sports.soccer",
                archetype_id="sports_match_winner",
                template_version="sports-template-v1",
                updated_at=GENERATED_AT - timedelta(days=4),
            ),
            EventArchetypeRegistryEntry(
                domain_id="sports",
                category_id="sports.other",
                archetype_id="sports_other_event",
                template_version="sports-other-template-v1",
                updated_at=GENERATED_AT - timedelta(days=95),
            ),
        ),
        (
            EventArchetypeRegistryObservation(
                event_fingerprint="event-politics",
                domain_id="politics",
                category_id="politics",
                archetype_id="politics_event",
                template_version="politics-template-v1",
                observed_at=GENERATED_AT - timedelta(days=1),
            ),
            EventArchetypeRegistryObservation(
                event_fingerprint="event-btc",
                domain_id="crypto",
                category_id="finance.crypto.btc",
                archetype_id="btc_hit_price",
                template_version="btc-template-v1",
                observed_at=GENERATED_AT - timedelta(hours=2),
            ),
            EventArchetypeRegistryObservation(
                event_fingerprint="event-rates",
                domain_id="macro",
                category_id="finance.macro.rates",
                archetype_id="fed_rate_decision",
                template_version="macro-template-v0",
                observed_at=GENERATED_AT - timedelta(days=1),
            ),
            EventArchetypeRegistryObservation(
                event_fingerprint="event-gold",
                domain_id="commodities",
                category_id="finance.commodities.gold",
                archetype_id="gold_hit_price",
                template_version="gold-template-v1",
                observed_at=GENERATED_AT - timedelta(days=1),
            ),
            EventArchetypeRegistryObservation(
                event_fingerprint="event-sports",
                domain_id="sports",
                category_id="sports.soccer",
                archetype_id="sports_match_winner",
                template_version="sports-template-v1",
                observed_at=GENERATED_AT - timedelta(hours=4),
            ),
            EventArchetypeRegistryObservation(
                event_fingerprint="event-sports-unknown",
                domain_id="sports",
                category_id="sports.other",
                archetype_id="curling_prop",
                template_version="curling-template-v1",
                observed_at=GENERATED_AT - timedelta(hours=4),
            ),
        ),
        config=EventArchetypeRegistryHealthConfig(
            max_template_age_seconds=Decimal("7776000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.health_status == "blocked"
    assert report.domain_count == Decimal("5")
    assert report.covered_domain_count == Decimal("5")
    assert report.archetype_coverage_ratio == Decimal("1.000000")
    assert report.unknown_archetype_count == Decimal("1")
    assert report.stale_template_count == Decimal("1")
    assert report.template_version_mismatch_count == Decimal("1")
    assert report.reason_codes == (
        "unknown_event_archetypes_observed",
        "stale_event_archetype_templates",
        "event_archetype_template_version_mismatch",
    )

    rows_by_domain = {row.domain_id: row for row in report.rows}
    assert set(rows_by_domain) == {"commodities", "crypto", "macro", "politics", "sports"}
    assert rows_by_domain["sports"].health_status == "blocked"
    assert rows_by_domain["sports"].registered_archetype_count == Decimal("2")
    assert rows_by_domain["sports"].observed_archetype_count == Decimal("2")
    assert rows_by_domain["sports"].unknown_archetype_count == Decimal("1")
    assert rows_by_domain["sports"].stale_template_count == Decimal("1")
    assert rows_by_domain["macro"].health_status == "watch"
    assert rows_by_domain["macro"].template_version_mismatch_count == Decimal("1")

    serialized = repr(asdict(report)).lower()
    assert "market_slug" not in serialized
    assert "question" not in serialized
    assert "payload" not in serialized
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_registry_health_blocks_missing_domain_coverage() -> None:
    report = build_event_archetype_registry_health_report(
        (
            EventArchetypeRegistryEntry(
                domain_id="politics",
                category_id="politics",
                archetype_id="politics_event",
                template_version="politics-template-v1",
                updated_at=GENERATED_AT,
            ),
        ),
        (),
        config=EventArchetypeRegistryHealthConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.health_status == "blocked"
    assert report.covered_domain_count == Decimal("1")
    assert report.missing_domain_count == Decimal("4")
    assert report.archetype_coverage_ratio == Decimal("0.200000")
    assert report.reason_codes == ("missing_event_archetype_domain_coverage",)
    assert tuple(row.domain_id for row in report.rows if row.health_status == "blocked") == (
        "crypto",
        "macro",
        "commodities",
        "sports",
    )


def test_registry_health_dataclasses_are_frozen_decimal_only_and_safe() -> None:
    config = EventArchetypeRegistryHealthConfig(max_template_age_seconds=Decimal("86400"))
    entry = EventArchetypeRegistryEntry(
        domain_id="politics",
        category_id="politics",
        archetype_id="politics_event",
        template_version="politics-template-v1",
        updated_at=GENERATED_AT,
    )
    observation = EventArchetypeRegistryObservation(
        event_fingerprint="event-politics",
        domain_id="politics",
        category_id="politics",
        archetype_id="politics_event",
        template_version="politics-template-v1",
        observed_at=GENERATED_AT,
    )
    report = build_event_archetype_registry_health_report(
        (entry,),
        (observation,),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert is_dataclass(config)
    assert is_dataclass(entry)
    assert is_dataclass(observation)
    assert is_dataclass(report)
    with pytest.raises(FrozenInstanceError):
        entry.template_version = "other"  # type: ignore[misc]

    numeric_values = [
        value
        for row in report.rows
        for value in asdict(row).values()
        if isinstance(value, Decimal)
    ]
    numeric_values.extend(
        value for value in asdict(report).values() if isinstance(value, Decimal)
    )
    assert numeric_values
    assert all(type(value) is Decimal for value in numeric_values)

    with pytest.raises(ValueError, match="max_template_age_seconds must be a Decimal"):
        EventArchetypeRegistryHealthConfig(max_template_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(observation, paper_only=False)


def test_registry_health_rejects_future_times_duplicates_wrong_domains_and_false_flags() -> None:
    entry = EventArchetypeRegistryEntry(
        domain_id="politics",
        category_id="politics",
        archetype_id="politics_event",
        template_version="politics-template-v1",
        updated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="future"):
        build_event_archetype_registry_health_report(
            (replace(entry, updated_at=GENERATED_AT + timedelta(seconds=1)),),
            (),
            config=EventArchetypeRegistryHealthConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        build_event_archetype_registry_health_report(
            (entry, entry),
            (),
            config=EventArchetypeRegistryHealthConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="category_id must match domain_id"):
        EventArchetypeRegistryEntry(
            domain_id="crypto",
            category_id="politics",
            archetype_id="politics_event",
            template_version="politics-template-v1",
            updated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        build_event_archetype_registry_health_report(
            (replace(entry, paper_only=False),),
            (),
            config=EventArchetypeRegistryHealthConfig(),
            generated_at=GENERATED_AT,
        )


def test_registry_health_module_stays_readonly_scope() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {"__import__", "eval", "exec", "open", "print"}
    forbidden_fragments = (
        "advice",
        "auth",
        "buy",
        "cancel",
        "live",
        "market_slug",
        "order",
        "payload",
        "question",
        "recommend",
        "sell",
        "wallet",
    )

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module] if node.module is not None else []
        else:
            names = []
        for name in names:
            if name and name.split(".", maxsplit=1)[0] in forbidden_import_roots:
                violations.append(name)
        if isinstance(node, ast.Call):
            call = node.func
            call_name = call.id if isinstance(call, ast.Name) else None
            if call_name in forbidden_call_names:
                violations.append(call_name)
    lowered_source = source.lower()
    violations.extend(
        fragment for fragment in forbidden_fragments if fragment in lowered_source
    )

    assert sorted(set(violations)) == []
