from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_cross_domain_event_overlap_router.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_cross_domain_event_overlap_router",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def event(**overrides: object):
    module = api()
    values = {
        "event_key": "evt_politics_crypto_macro_overlap",
        "category_ids": (
            "politics",
            "finance.crypto.btc",
            "finance.macro.rates",
        ),
        "overlap_score": d("0.300000"),
        "source_confidence_score": d("0.900000"),
        "urgency_score": d("0.200000"),
        "conflict_score": d("0.100000"),
        "stale_source_score": d("0.000000"),
        "observed_at": GENERATED_AT - timedelta(minutes=30),
    }
    values.update(overrides)
    return module.ResearchCrossDomainEventOverlapCandidate(**values)


def report(events: object | None = None):
    module = api()
    return module.build_research_cross_domain_event_overlap_report(
        events
        if events is not None
        else (
            event(),
            event(
                event_key="evt_crypto_macro_policy_overlap",
                category_ids=("finance.crypto.btc", "finance.macro.rates"),
                overlap_score=d("0.650000"),
                source_confidence_score=d("0.800000"),
                urgency_score=d("0.700000"),
                conflict_score=d("0.200000"),
                stale_source_score=d("0.100000"),
            ),
            event(
                event_key="evt_politics_sports_conflict_overlap",
                category_ids=("politics", "sports.basketball"),
                overlap_score=d("0.900000"),
                source_confidence_score=d("0.400000"),
                urgency_score=d("0.900000"),
                conflict_score=d("0.900000"),
                stale_source_score=d("0.200000"),
            ),
        ),
        generated_at=GENERATED_AT,
    )


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def assert_no_decimal_or_datetime(value: Any) -> None:
    if isinstance(value, (Decimal, datetime)):
        raise AssertionError(f"unexpected raw public value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_datetime(item)
    if isinstance(value, list):
        for item in value:
            assert_no_decimal_or_datetime(item)


def test_routes_cross_domain_events_to_collaborative_research_lanes() -> None:
    result = report()
    rows_by_key = {row.event_key: row for row in result.routes}

    pass_row = rows_by_key["evt_politics_crypto_macro_overlap"]
    watch_row = rows_by_key["evt_crypto_macro_policy_overlap"]
    block_row = rows_by_key["evt_politics_sports_conflict_overlap"]

    assert pass_row.route_status == "pass"
    assert pass_row.queue_lane == "collaborative_research_standard"
    assert pass_row.assigned_team_ids == ("politics", "crypto_btc", "macro_rates")
    assert pass_row.routing_score == d("36.000000")
    assert "routed_to_collaborative_research" in pass_row.reason_codes

    assert watch_row.route_status == "watch"
    assert watch_row.queue_lane == "collaborative_research_watch"
    assert watch_row.assigned_team_ids == ("crypto_btc", "macro_rates")
    assert watch_row.routing_score == d("59.000000")

    assert block_row.route_status == "block"
    assert block_row.queue_lane == "collaborative_research_block"
    assert block_row.assigned_team_ids == ("politics", "sports_basketball")
    assert block_row.routing_score == d("78.000000")
    assert "high_conflict_score" in block_row.reason_codes

    assert tuple(row.route_status for row in result.routes) == ("block", "watch", "pass")
    assert result.event_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.status == "block"
    assert result.mean_routing_score == d("57.666667")
    assert result.max_routing_score == d("78.000000")


def test_public_status_values_are_only_pass_watch_block() -> None:
    module = api()
    result = report()
    payload = module.research_cross_domain_event_overlap_router_payload(result)

    statuses = {payload["status"]}
    statuses.update(row["route_status"] for row in payload["routes"])

    assert statuses <= {"pass", "watch", "block"}
    assert statuses == {"pass", "watch", "block"}
    with pytest.raises(ValueError, match="route_status"):
        replace(result.routes[0], route_status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(result, status="blocked")


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    result = report()

    for klass in (
        module.ResearchCrossDomainEventOverlapRouterConfig,
        module.ResearchCrossDomainEventOverlapCandidate,
        module.ResearchCrossDomainEventOverlapRoute,
        module.ResearchCrossDomainEventOverlapReasonCodeCount,
        module.ResearchCrossDomainEventOverlapReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.routes[0].route_status = "pass"  # type: ignore[misc]

    for public_record in (
        module.ResearchCrossDomainEventOverlapRouterConfig(),
        event(),
        result.routes[0],
        result.reason_code_counts[0],
        result,
    ):
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="overlap_score"):
        event(overlap_score=1)
    with pytest.raises(ValueError, match="source_confidence_score"):
        event(source_confidence_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="urgency_score"):
        event(urgency_score=d("1.000001"))
    with pytest.raises(ValueError, match="watch_routing_score_threshold"):
        module.ResearchCrossDomainEventOverlapRouterConfig(
            watch_routing_score_threshold=45,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(event(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_public_payload_rejects_sensitive_identifiers_and_operational_language() -> None:
    module = api()
    result = report()
    payload = module.research_cross_domain_event_overlap_router_payload(result)
    encoded = json.dumps(payload, sort_keys=True).lower()

    forbidden_fragments = (
        "raw_id",
        "raw-candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "position",
        "buy",
        "sell",
        "recommend",
    )
    for forbidden in forbidden_fragments:
        assert forbidden not in encoded

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)
    assert_no_decimal_or_datetime(payload)

    with pytest.raises(ValueError, match="unsafe"):
        event(event_key=f"evt_{'raw' + '_candidate'}_123")
    with pytest.raises(ValueError, match="unsafe"):
        event(event_key=f"evt_{'market' + '_slug'}_abc")
    with pytest.raises(ValueError, match="unsafe"):
        event(event_key=f"evt_{'https' + '://'}example.test/path")
    with pytest.raises(ValueError, match="unsafe"):
        replace(result.routes[0], event_key=f"evt_{'to' + 'ken'}_abc")


def test_payload_and_digest_are_deterministic_across_input_order() -> None:
    module = api()
    events = (
        event(event_key="evt_low_score_politics_crypto"),
        event(
            event_key="evt_watch_crypto_macro",
            category_ids=("finance.crypto.eth", "finance.macro.rates"),
            overlap_score=d("0.650000"),
            source_confidence_score=d("0.800000"),
            urgency_score=d("0.700000"),
            conflict_score=d("0.200000"),
            stale_source_score=d("0.100000"),
        ),
        event(
            event_key="evt_block_politics_sports",
            category_ids=("politics", "sports.other"),
            overlap_score=d("0.900000"),
            source_confidence_score=d("0.400000"),
            urgency_score=d("0.900000"),
            conflict_score=d("0.900000"),
            stale_source_score=d("0.200000"),
        ),
    )

    forward = report(events)
    reversed_result = report(tuple(reversed(events)))

    assert forward == reversed_result
    assert forward.public_digest == reversed_result.public_digest
    assert module.research_cross_domain_event_overlap_router_payload(
        forward,
    ) == module.research_cross_domain_event_overlap_router_payload(reversed_result)


def test_report_digest_consistency_is_tamper_evident() -> None:
    module = api()
    result = report()
    payload = module.research_cross_domain_event_overlap_router_payload(result)

    assert payload["public_digest"] == result.public_digest
    assert module.research_cross_domain_event_overlap_router_digest(result) == result.public_digest
    assert len(result.public_digest) == 64

    with pytest.raises(ValueError, match="public_digest"):
        replace(result, public_digest="0" * 64)
    with pytest.raises(ValueError, match="public_digest"):
        replace(result, pass_count=d("3"))
    with pytest.raises(ValueError, match="report"):
        module.research_cross_domain_event_overlap_router_payload(object())


def test_module_scope_is_report_only_readonly_and_external_io_free() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    for forbidden in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert forbidden not in source.lower()
