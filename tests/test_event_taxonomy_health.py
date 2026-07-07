from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.event_taxonomy_health import (
    EventTaxonomyHealthConfig,
    EventTaxonomyObservation,
    build_event_taxonomy_health_report,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
MODULE_PATH = Path("src/polymarket_alpha_lab/event_taxonomy_health.py")


def test_health_report_covers_team_domains_unknown_categories_and_template_drift() -> None:
    report = build_event_taxonomy_health_report(
        (
            EventTaxonomyObservation(
                event_fingerprint="event-politics",
                category_hint="politics",
                routed_category_id="politics",
                routed_team_id="politics",
                event_template="politics_event",
            ),
            EventTaxonomyObservation(
                event_fingerprint="event-btc",
                category_hint="finance.crypto.btc",
                routed_category_id="finance.crypto.btc",
                routed_team_id="crypto_btc",
                event_template="unexpected_btc_template",
            ),
            EventTaxonomyObservation(
                event_fingerprint="event-macro",
                category_hint="finance.macro.rates",
                routed_category_id="finance.macro.rates",
                routed_team_id="macro_rates",
                event_template="fed_rate_decision",
            ),
            EventTaxonomyObservation(
                event_fingerprint="event-soccer",
                category_hint="sports.soccer",
                routed_category_id="sports.soccer",
                routed_team_id="sports_soccer",
                event_template="sports_match_winner",
            ),
            EventTaxonomyObservation(
                event_fingerprint="event-curling",
                category_hint="sports.unknown.curling",
                routed_category_id="sports.other",
                routed_team_id="sports_other",
                event_template="sports_match_winner",
            ),
            EventTaxonomyObservation(
                event_fingerprint="event-unknown",
                category_hint="finance.unknown",
                routed_category_id=None,
                routed_team_id=None,
                event_template="mystery_template",
            ),
        ),
        config=EventTaxonomyHealthConfig(min_events_per_domain=Decimal("1")),
        generated_at=GENERATED_AT,
    )

    assert report.status == "blocked"
    assert report.event_count == Decimal("6")
    assert report.covered_domain_count == Decimal("4")
    assert report.unknown_category_count == Decimal("2")
    assert report.unroutable_unknown_category_count == Decimal("1")
    assert report.template_drift_count == Decimal("2")
    assert report.coverage_ratio == Decimal("1.000000")
    assert report.reason_codes == (
        "event_taxonomy_unroutable_unknown_category",
        "event_taxonomy_template_drift",
        "event_taxonomy_sports_unknown_category",
    )

    rows_by_domain = {row.domain_id: row for row in report.rows}
    assert set(rows_by_domain) == {"crypto_btc", "macro_rates", "politics", "sports"}
    assert rows_by_domain["crypto_btc"].status == "watch"
    assert rows_by_domain["crypto_btc"].template_drift_count == Decimal("1")
    assert rows_by_domain["sports"].observed_event_count == Decimal("2")
    assert rows_by_domain["sports"].covered_category_count == Decimal("2")
    assert rows_by_domain["sports"].unknown_category_count == Decimal("1")

    payload = asdict(report)
    assert "market_slug" not in repr(payload)
    assert "question" not in repr(payload)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_health_report_blocks_missing_required_domain_coverage() -> None:
    report = build_event_taxonomy_health_report(
        (
            EventTaxonomyObservation(
                event_fingerprint="event-politics",
                category_hint="politics",
                routed_category_id="politics",
                routed_team_id="politics",
                event_template="politics_event",
            ),
        ),
        config=EventTaxonomyHealthConfig(min_events_per_domain=Decimal("1")),
        generated_at=GENERATED_AT,
    )

    assert report.status == "blocked"
    assert report.covered_domain_count == Decimal("1")
    assert report.coverage_ratio == Decimal("0.250000")
    assert report.reason_codes == ("event_taxonomy_missing_domain_coverage",)
    assert tuple(row.domain_id for row in report.rows if row.status == "blocked") == (
        "crypto_btc",
        "macro_rates",
        "sports",
    )


def test_event_taxonomy_health_dataclasses_are_frozen_decimal_only_and_safe() -> None:
    config = EventTaxonomyHealthConfig(min_events_per_domain=Decimal("1"))
    observation = EventTaxonomyObservation(
        event_fingerprint="event-politics",
        category_hint="politics",
        routed_category_id="politics",
        routed_team_id="politics",
        event_template="politics_event",
    )
    report = build_event_taxonomy_health_report(
        (observation,),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert is_dataclass(config)
    assert is_dataclass(observation)
    assert is_dataclass(report)
    with pytest.raises(FrozenInstanceError):
        observation.event_template = "other_template"  # type: ignore[misc]

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

    with pytest.raises(ValueError, match="min_events_per_domain must be a Decimal"):
        EventTaxonomyHealthConfig(min_events_per_domain=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        EventTaxonomyObservation(
            event_fingerprint="event-politics",
            category_hint="politics",
            routed_category_id="politics",
            routed_team_id="politics",
            event_template="politics_event",
            paper_only=False,
        )


def test_event_taxonomy_health_module_stays_readonly_scope() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
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
