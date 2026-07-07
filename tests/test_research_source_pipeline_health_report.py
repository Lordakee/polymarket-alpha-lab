from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_source_pipeline_health_report import (
    DEFAULT_RESEARCH_SOURCE_PIPELINE_HEALTH_REPORT_CONFIG_VERSION,
    ResearchSourcePipelineHealthConfig,
    ResearchSourcePipelineHealthInput,
    ResearchSourcePipelineHealthReport,
    ResearchSourcePipelineHealthRow,
    build_research_source_pipeline_health_report,
    research_source_pipeline_health_report_payload,
    validate_research_source_pipeline_health_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_pipeline_health_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(
    pipeline_item_ref: str,
    *,
    source_category: str = "official",
    registry_status: str = "pass",
    scraping_scope_status: str = "pass",
    source_freshness_status: str = "pass",
    audit_trail_status: str = "pass",
    collection_status: str = "pass",
    registry_reliability_score: Decimal = d("0.950000"),
    source_freshness_score: Decimal = d("0.900000"),
    audit_trail_score: Decimal = d("0.950000"),
    collection_priority_score: Decimal = d("0.050000"),
    source_age_seconds: Decimal | None = d("1200.000000"),
    collection_priority: str = "defer_collection",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourcePipelineHealthInput:
    return ResearchSourcePipelineHealthInput(
        pipeline_item_ref=pipeline_item_ref,
        source_category=source_category,
        registry_status=registry_status,
        scraping_scope_status=scraping_scope_status,
        source_freshness_status=source_freshness_status,
        audit_trail_status=audit_trail_status,
        collection_status=collection_status,
        registry_reliability_score=registry_reliability_score,
        source_freshness_score=source_freshness_score,
        audit_trail_score=audit_trail_score,
        collection_priority_score=collection_priority_score,
        source_age_seconds=source_age_seconds,
        collection_priority=collection_priority,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _build(
    *inputs: ResearchSourcePipelineHealthInput,
    config: ResearchSourcePipelineHealthConfig | None = None,
) -> ResearchSourcePipelineHealthReport:
    return build_research_source_pipeline_health_report(
        inputs,
        config=config or ResearchSourcePipelineHealthConfig(),
        generated_at=GENERATED_AT,
    )


def _walk_payload_values(value: object) -> list[object]:
    values: list[object] = [value]
    if type(value) is dict:
        for key, item in value.items():
            values.extend(_walk_payload_values(key))
            values.extend(_walk_payload_values(item))
    elif type(value) is list:
        for item in value:
            values.extend(_walk_payload_values(item))
    return values


def _assert_payload_has_no_raw_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        pytest.fail(f"public payload leaked raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            _assert_payload_has_no_raw_numbers(item)
    elif type(value) is list:
        for item in value:
            _assert_payload_has_no_raw_numbers(item)


def _assert_payload_has_no_forbidden_text(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).casefold()
    for forbidden in (
        "safe-pass",
        "safe-watch",
        "safe-block",
        "raw candidate",
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
        "www.",
        "dsn",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in rendered
    assert "table" not in rendered.replace("unstable", "")


def test_builds_pass_watch_block_pipeline_health_report() -> None:
    report = _build(
        _input("safe-pass", source_category="official"),
        _input(
            "safe-watch",
            source_category="regulatory",
            scraping_scope_status="watch",
            source_freshness_status="watch",
            collection_status="watch",
            registry_reliability_score=d("0.800000"),
            source_freshness_score=d("0.650000"),
            audit_trail_score=d("0.800000"),
            collection_priority_score=d("0.450000"),
            source_age_seconds=d("90000.000000"),
            collection_priority="prioritize_collection",
        ),
        _input(
            "safe-block",
            source_category="news",
            registry_status="block",
            scraping_scope_status="block",
            source_freshness_status="block",
            audit_trail_status="block",
            collection_status="block",
            registry_reliability_score=d("0.200000"),
            source_freshness_score=d("0.100000"),
            audit_trail_score=d("0.150000"),
            collection_priority_score=d("0.950000"),
            source_age_seconds=d("700000.000000"),
            collection_priority="collect_before_research_use",
        ),
    )

    assert type(report) is ResearchSourcePipelineHealthReport
    assert report.config_version == DEFAULT_RESEARCH_SOURCE_PIPELINE_HEALTH_REPORT_CONFIG_VERSION
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.attention_ratio == d("0.666667")
    assert report.registry_block_count == d("1.000000")
    assert report.scraping_scope_block_count == d("1.000000")
    assert report.source_freshness_block_count == d("1.000000")
    assert report.audit_trail_block_count == d("1.000000")
    assert report.collection_block_count == d("1.000000")
    assert report.max_source_age_seconds == d("700000.000000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.pipeline_ref for row in report.rows) == (
        "redacted-pipeline-source-000001",
        "redacted-pipeline-source-000002",
        "redacted-pipeline-source-000003",
    )
    assert tuple(row.source_category for row in report.rows) == (
        "news",
        "regulatory",
        "official",
    )
    assert report.rows[0].reason_codes == (
        "registry_status_block",
        "scraping_scope_status_block",
        "source_freshness_status_block",
        "source_age_above_block_threshold",
        "audit_trail_status_block",
        "collection_status_block",
        "collection_priority_collect_before_research_use",
        "pipeline_health_score_below_block_threshold",
        "pipeline_health_block",
    )
    assert report.rows[1].reason_codes == (
        "scraping_scope_status_watch",
        "source_freshness_status_watch",
        "source_age_above_watch_threshold",
        "collection_status_watch",
        "collection_priority_prioritized",
        "pipeline_health_score_below_pass_threshold",
        "pipeline_health_watch",
    )
    assert report.rows[2].reason_codes == ("pipeline_health_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = research_source_pipeline_health_report_payload(report)
    assert payload["status"] == "block"
    assert payload["input_count"] == "3.000000"
    assert payload["attention_ratio"] == "0.666667"
    assert payload["rows"][0]["pipeline_ref"] == "redacted-pipeline-source-000001"
    assert payload["rows"][0]["pipeline_health_score"] == "0.100000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_text(payload)
    assert validate_research_source_pipeline_health_report_payload(payload)


def test_empty_inputs_are_report_only_block() -> None:
    report = _build()

    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.attention_count == d("0.000000")
    assert report.attention_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("source_pipeline_health_no_inputs",)
    payload = research_source_pipeline_health_report_payload(report)
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_payload_has_no_raw_numbers(payload)


def test_decimal_only_frozen_exact_types_and_hard_flags() -> None:
    report = _build(_input("safe-types"))

    assert ResearchSourcePipelineHealthConfig.__dataclass_params__.frozen is True
    assert ResearchSourcePipelineHealthInput.__dataclass_params__.frozen is True
    assert ResearchSourcePipelineHealthRow.__dataclass_params__.frozen is True
    assert ResearchSourcePipelineHealthReport.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedPipelineConfig", (ResearchSourcePipelineHealthConfig,), {})
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_pipeline_health_report(
            (_input("safe-time"),),
            config=ResearchSourcePipelineHealthConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="watch_source_age_seconds"):
        ResearchSourcePipelineHealthConfig(
            watch_source_age_seconds=_DecimalSubclass("86400.000000"),
        )
    with pytest.raises(ValueError, match="block_source_age_seconds"):
        ResearchSourcePipelineHealthConfig(block_source_age_seconds=604800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="registry_reliability_score"):
        _input("safe-int", registry_reliability_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_freshness_score"):
        _input("safe-float", source_freshness_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="audit_trail_score"):
        _input("safe-subclass", audit_trail_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="collection_priority_score"):
        _input("safe-none", collection_priority_score=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_age_seconds"):
        _input("safe-age", source_age_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="registry_status"):
        _input("safe-status", registry_status="blocked")
    with pytest.raises(ValueError, match="paper_only"):
        _input("safe-flags", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_payload_rejects_sensitive_public_surfaces_and_digest_tampering() -> None:
    payload = research_source_pipeline_health_report_payload(_build(_input("safe-payload")))

    for unsafe_key in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "orders_table",
        "token",
        "wallet",
        "auth",
        "trade",
        "position",
    ):
        tampered = dict(payload)
        tampered[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="public"):
            research_source_pipeline_health_report_payload(tampered)

    for unsafe_value in (
        "raw candidate id abc",
        "https://example.test/source",
        "primary source_url",
        "wallet auth token",
        "buy sell recommendation",
    ):
        tampered = dict(payload)
        tampered["operator_note"] = unsafe_value
        with pytest.raises(ValueError, match="public"):
            research_source_pipeline_health_report_payload(tampered)

    tampered_digest = dict(payload)
    tampered_digest["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_pipeline_health_report_payload(tampered_digest)

    with pytest.raises(ValueError, match="unsafe public"):
        _input("market_slug_real")
    with pytest.raises(ValueError, match="unsafe public"):
        _input("safe-ref", collection_priority="buy_recommendation")


def test_payload_and_digest_are_deterministic_for_input_order() -> None:
    inputs = (
        _input("safe-c", source_category="venue", collection_priority_score=d("0.300000")),
        _input("safe-a", source_category="official"),
        _input(
            "safe-b",
            source_category="news",
            registry_status="block",
            registry_reliability_score=d("0.100000"),
            source_freshness_score=d("0.200000"),
            audit_trail_score=d("0.200000"),
            collection_priority_score=d("0.900000"),
            collection_priority="collect_before_research_use",
        ),
    )

    report_a = _build(*inputs)
    report_b = _build(*tuple(reversed(inputs)))
    payload_a = research_source_pipeline_health_report_payload(report_a)
    payload_b = research_source_pipeline_health_report_payload(report_b)

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload_a == payload_b
    assert json.dumps(payload_a, sort_keys=True) == json.dumps(payload_b, sort_keys=True)
    assert all(
        value != "safe-a" and value != "safe-b" and value != "safe-c"
        for value in _walk_payload_values(payload_a)
    )


def test_module_has_no_network_database_or_trading_runtime_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert not imported_roots & {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
