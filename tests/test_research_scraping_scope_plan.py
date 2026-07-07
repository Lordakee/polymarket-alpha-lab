from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_scraping_scope_plan import (
    DEFAULT_RESEARCH_SCRAPING_SCOPE_PLAN_CONFIG_VERSION,
    ResearchScrapingScopePlanConfig,
    ResearchScrapingScopePlanInput,
    ResearchScrapingScopePlanReport,
    ResearchScrapingScopePlanRow,
    build_research_scraping_scope_plan_report,
    research_scraping_scope_plan_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_scraping_scope_plan.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchScrapingScopePlanConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_SCRAPING_SCOPE_PLAN_CONFIG_VERSION,
        "source_gap_watch_count": d("1.000000"),
        "source_gap_block_count": d("3.000000"),
        "conflict_block_count": d("1.000000"),
        "stale_watch_after_seconds": d("86400.000000"),
        "stale_block_after_seconds": d("604800.000000"),
    }
    values.update(overrides)
    return ResearchScrapingScopePlanConfig(**values)


def scope_input(
    scope_key: str,
    *,
    topic_category: str = "macro-rates",
    source_category: str = "official",
    source_age_seconds: Decimal | None = d("3600.000000"),
    source_gap_count: Decimal = d("0.000000"),
    conflict_count: Decimal = d("0.000000"),
    collection_allowed: bool = True,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchScrapingScopePlanInput:
    return ResearchScrapingScopePlanInput(
        scope_key=scope_key,
        topic_category=topic_category,
        source_category=source_category,
        source_age_seconds=source_age_seconds,
        source_gap_count=source_gap_count,
        conflict_count=conflict_count,
        collection_allowed=collection_allowed,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_plan(
    *inputs: ResearchScrapingScopePlanInput,
    cfg: ResearchScrapingScopePlanConfig | None = None,
) -> ResearchScrapingScopePlanReport:
    return build_research_scraping_scope_plan_report(
        inputs,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def assert_no_public_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def assert_no_forbidden_public_text(value: object) -> None:
    forbidden_fragments = (
        "candidate-",
        "market-",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        " buy ",
        " sell ",
        "recommendation",
    )
    if isinstance(value, str):
        lowered = f" {value.lower()} "
        for fragment in forbidden_fragments:
            assert fragment not in lowered
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_no_forbidden_public_text(key)
            assert_no_forbidden_public_text(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_forbidden_public_text(item)


def test_builds_pass_watch_and_block_scope_plan_payload() -> None:
    plan = build_plan(
        scope_input("scope-pass", topic_category="macro-rates", source_category="official"),
        scope_input(
            "scope-watch",
            topic_category="election-admin",
            source_category="regulatory",
            source_age_seconds=d("90000.000000"),
            source_gap_count=d("1.000000"),
        ),
        scope_input(
            "scope-block",
            topic_category="sports-rules",
            source_category="news",
            source_gap_count=d("3.000000"),
            conflict_count=d("1.000000"),
        ),
    )

    assert is_dataclass(plan)
    assert plan.__dataclass_params__.frozen is True
    assert plan.generated_at == GENERATED_AT
    assert plan.config_version == DEFAULT_RESEARCH_SCRAPING_SCOPE_PLAN_CONFIG_VERSION
    assert plan.plan_status == "block"
    assert plan.scope_count == d("3.000000")
    assert plan.pass_count == d("1.000000")
    assert plan.watch_count == d("1.000000")
    assert plan.block_count == d("1.000000")
    assert plan.reason_codes == (
        "research_scraping_scope_plan_block",
        "scraping_scope_conflict_block",
        "scraping_scope_freshness_stale_watch",
        "scraping_scope_source_gap_block",
        "scraping_scope_source_gap_watch",
    )
    assert plan.paper_only is True
    assert plan.report_only is True
    assert plan.readonly is True

    assert tuple(row.scope_status for row in plan.rows) == ("block", "watch", "pass")
    assert tuple(row.freshness_priority for row in plan.rows) == (
        "critical",
        "high",
        "low",
    )
    assert tuple(row.source_category for row in plan.rows) == (
        "news",
        "regulatory",
        "official",
    )
    assert tuple(row.collection_scope for row in plan.rows) == (
        "sports-rules:news:public-web",
        "election-admin:regulatory:public-web",
        "macro-rates:official:public-web",
    )
    assert tuple(row.source_gap_count for row in plan.rows) == (
        d("3.000000"),
        d("1.000000"),
        d("0.000000"),
    )
    assert all(len(row.scope_digest) == 64 for row in plan.rows)
    assert len({row.scope_digest for row in plan.rows}) == 3

    payload = research_scraping_scope_plan_payload(plan)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["scope_count"] == "3.000000"
    assert payload["rows"][0]["source_gap_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)
    assert_no_forbidden_public_text(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_inputs_block_report_only_with_no_inputs_reason() -> None:
    plan = build_plan()

    assert plan.plan_status == "block"
    assert plan.scope_count == d("0.000000")
    assert plan.pass_count == d("0.000000")
    assert plan.watch_count == d("0.000000")
    assert plan.block_count == d("0.000000")
    assert plan.rows == ()
    assert plan.reason_codes == ("research_scraping_scope_plan_no_inputs",)
    payload = research_scraping_scope_plan_payload(plan)
    assert payload["plan_status"] == "block"
    assert payload["rows"] == []
    assert_no_public_float_or_int(payload)


def test_public_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    plan = build_plan(scope_input("scope-types"))

    public_classes = (
        ResearchScrapingScopePlanConfig,
        ResearchScrapingScopePlanInput,
        ResearchScrapingScopePlanRow,
        ResearchScrapingScopePlanReport,
    )
    for klass in public_classes:
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        plan.plan_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(plan, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        scope_input("scope-flag", paper_only=False)
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedConfig", (ResearchScrapingScopePlanConfig,), {})
    with pytest.raises(ValueError, match="source_gap_watch_count"):
        config(source_gap_watch_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="source_age_seconds"):
        scope_input("scope-int-age", source_age_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_gap_count"):
        scope_input("scope-float-gap", source_gap_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        scope_input("scope-list-reasons", reason_codes=["x"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_category"):
        scope_input("scope-unknown-source", source_category="blog")

    for instance in (config(), scope_input("scope-fields"), *plan.rows, plan):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_ratio")
            ):
                assert value is None or type(value) is Decimal


def test_rejects_leaks_in_inputs_and_tampered_payload() -> None:
    unsafe_overrides: tuple[dict[str, object], ...] = (
        {"scope_key": "candidate-raw-123"},
        {"topic_category": "market-slug-presidential-election"},
        {"topic_category": "will rates rise question"},
        {"topic_category": "source_ref:abc"},
        {"topic_category": "https://example.com/market"},
        {"topic_category": "postgres dsn table"},
        {"topic_category": "wallet auth token"},
        {"topic_category": "buy sell recommendation"},
        {"reason_codes": ("operator_buy_recommendation",)},
    )
    for override in unsafe_overrides:
        values: dict[str, object] = {"scope_key": "scope-safe"}
        values.update(override)
        with pytest.raises(ValueError, match="unsafe"):
            scope_input(**values)  # type: ignore[arg-type]

    plan = build_plan(scope_input("scope-safe"))
    object.__setattr__(plan.rows[0], "collection_scope", "https://example.com/raw")
    with pytest.raises(ValueError, match="unsafe"):
        research_scraping_scope_plan_payload(plan)


def test_status_membership_hard_flags_and_row_consistency_are_enforced() -> None:
    plan = build_plan(scope_input("scope-consistency"))

    assert all(row.scope_status in {"pass", "watch", "block"} for row in plan.rows)
    with pytest.raises(ValueError, match="scope_status"):
        replace(plan.rows[0], scope_status="blocked")
    with pytest.raises(ValueError, match="freshness_priority"):
        replace(plan.rows[0], freshness_priority="now")
    with pytest.raises(ValueError, match="scope_status"):
        replace(plan.rows[0], reason_codes=("scraping_scope_source_gap_block",))
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        scope_input("scope-readonly", readonly=False)


def test_output_is_deterministic_for_input_order_and_payload_sorting() -> None:
    inputs = (
        scope_input("scope-zeta", topic_category="macro-rates", source_category="official"),
        scope_input(
            "scope-alpha",
            topic_category="sports-rules",
            source_category="news",
            conflict_count=d("1.000000"),
        ),
        scope_input(
            "scope-beta",
            topic_category="election-admin",
            source_category="regulatory",
            source_gap_count=d("1.000000"),
        ),
    )

    first_payload = research_scraping_scope_plan_payload(build_plan(*inputs))
    second_payload = research_scraping_scope_plan_payload(build_plan(*reversed(inputs)))

    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )
    assert tuple(row["collection_scope"] for row in first_payload["rows"]) == (
        "sports-rules:news:public-web",
        "election-admin:regulatory:public-web",
        "macro-rates:official:public-web",
    )


def test_module_is_report_only_without_network_or_scraping_clients() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "aiohttp",
        "httpx",
        "requests",
        "scrapling",
        "socket",
        "urllib",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
