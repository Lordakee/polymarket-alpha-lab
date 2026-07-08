from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_strategy_review_queue_ev_priority_report as api
from polymarket_alpha_lab.research_strategy_review_queue_ev_priority_report import (
    ResearchStrategyReviewQueueEvPriorityConfig,
    ResearchStrategyReviewQueueEvPriorityItem,
    ResearchStrategyReviewQueueEvPriorityReport,
    ResearchStrategyReviewQueueEvPriorityRow,
    build_research_strategy_review_queue_ev_priority_report,
    research_strategy_review_queue_ev_priority_report_digest,
    research_strategy_review_queue_ev_priority_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_review_queue_ev_priority_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def item(**overrides: object) -> ResearchStrategyReviewQueueEvPriorityItem:
    values = {
        "review_key": "review_alpha",
        "cost_adjusted_expected_value_score": d("0.900000"),
        "evidence_quality_score": d("0.880000"),
        "liquidity_reliability_score": d("0.820000"),
        "resolution_clarity_score": d("0.850000"),
        "signal_freshness_score": d("0.800000"),
        "specialist_memory_confidence_score": d("0.900000"),
    }
    values.update(overrides)
    return ResearchStrategyReviewQueueEvPriorityItem(**values)


def report(
    *items: ResearchStrategyReviewQueueEvPriorityItem,
    config: ResearchStrategyReviewQueueEvPriorityConfig | None = None,
) -> ResearchStrategyReviewQueueEvPriorityReport:
    return build_research_strategy_review_queue_ev_priority_report(
        items,
        generated_at=GENERATED_AT,
        config=config,
    )


def test_public_api_declares_report_only_ev_priority_surface() -> None:
    assert api.DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_EV_PRIORITY_CONFIG_VERSION == (
        "research-strategy-review-queue-ev-priority-report"
    )
    assert api.REVIEW_QUEUE_EV_PRIORITY_DIMENSIONS == (
        "cost_adjusted_expected_value",
        "evidence_quality",
        "liquidity_reliability",
        "resolution_clarity",
        "signal_freshness",
        "specialist_memory_confidence",
    )
    assert api.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_REVIEW_QUEUE_EV_PRIORITY_CONFIG_VERSION",
        "REVIEW_QUEUE_EV_PRIORITY_DIMENSIONS",
        "ResearchStrategyReviewQueueEvPriorityConfig",
        "ResearchStrategyReviewQueueEvPriorityItem",
        "ResearchStrategyReviewQueueEvPriorityReport",
        "ResearchStrategyReviewQueueEvPriorityRow",
        "build_research_strategy_review_queue_ev_priority_report",
        "research_strategy_review_queue_ev_priority_report_digest",
        "research_strategy_review_queue_ev_priority_report_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(ResearchStrategyReviewQueueEvPriorityConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True
    assert field_defaults["min_pass_priority_score"] == d("0.750000")
    assert field_defaults["min_watch_priority_score"] == d("0.500000")
    assert field_defaults["min_pass_dimension_score"] == d("0.700000")
    assert field_defaults["min_watch_dimension_score"] == d("0.400000")
    assert field_defaults["cost_adjusted_expected_value_weight"] == d("0.300000")
    assert field_defaults["evidence_quality_weight"] == d("0.175000")
    assert field_defaults["liquidity_reliability_weight"] == d("0.150000")
    assert field_defaults["resolution_clarity_weight"] == d("0.125000")
    assert field_defaults["signal_freshness_weight"] == d("0.125000")
    assert field_defaults["specialist_memory_confidence_weight"] == d("0.125000")


def test_report_prioritizes_review_queue_items_by_cost_adjusted_ev_inputs() -> None:
    result = report(
        item(review_key="review_pass"),
        item(
            review_key="review_watch",
            cost_adjusted_expected_value_score=d("0.700000"),
            evidence_quality_score=d("0.650000"),
            liquidity_reliability_score=d("0.620000"),
            resolution_clarity_score=d("0.700000"),
            signal_freshness_score=d("0.660000"),
            specialist_memory_confidence_score=d("0.680000"),
        ),
        item(
            review_key="review_block",
            cost_adjusted_expected_value_score=d("0.450000"),
            evidence_quality_score=d("0.350000"),
            liquidity_reliability_score=d("0.400000"),
            resolution_clarity_score=d("0.550000"),
            signal_freshness_score=d("0.300000"),
            specialist_memory_confidence_score=d("0.500000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-strategy-review-queue-ev-priority-report"
    assert result.status == "block"
    assert result.review_item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_priority_score == d("0.654167")
    assert result.max_priority_score == d("0.865750")
    assert result.min_priority_score == d("0.425000")
    assert result.min_evidence_quality_score == d("0.350000")
    assert result.min_liquidity_reliability_score == d("0.400000")
    assert result.min_resolution_clarity_score == d("0.550000")
    assert result.min_signal_freshness_score == d("0.300000")
    assert result.min_specialist_memory_confidence_score == d("0.500000")
    assert result.reason_codes == (
        "review_queue_ev_priority_report_block_rows",
        "review_queue_ev_priority_report_watch_rows",
        "review_queue_ev_priority_report_average_below_pass",
        "review_queue_ev_priority_report_low_dimension_floor",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)
    assert_no_non_decimal_public_numbers(result)

    passed, watched, blocked = result.rows
    assert (passed.rank, watched.rank, blocked.rank) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert (passed.review_key, watched.review_key, blocked.review_key) == (
        "review_pass",
        "review_watch",
        "review_block",
    )

    assert passed.priority_score == d("0.865750")
    assert passed.lowest_dimension_score == d("0.800000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("review_queue_ev_priority_passed",)

    assert watched.priority_score == d("0.671750")
    assert watched.lowest_dimension_score == d("0.620000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "review_queue_ev_priority_evidence_quality_watch",
        "review_queue_ev_priority_liquidity_reliability_watch",
        "review_queue_ev_priority_signal_freshness_watch",
        "review_queue_ev_priority_memory_confidence_watch",
        "review_queue_ev_priority_score_below_pass",
    )

    assert blocked.priority_score == d("0.425000")
    assert blocked.lowest_dimension_score == d("0.300000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "review_queue_ev_priority_evidence_quality_block",
        "review_queue_ev_priority_signal_freshness_block",
        "review_queue_ev_priority_score_below_watch",
    )

    same_result = report(
        item(
            review_key="review_block",
            cost_adjusted_expected_value_score=d("0.450000"),
            evidence_quality_score=d("0.350000"),
            liquidity_reliability_score=d("0.400000"),
            resolution_clarity_score=d("0.550000"),
            signal_freshness_score=d("0.300000"),
            specialist_memory_confidence_score=d("0.500000"),
        ),
        item(review_key="review_pass"),
        item(
            review_key="review_watch",
            cost_adjusted_expected_value_score=d("0.700000"),
            evidence_quality_score=d("0.650000"),
            liquidity_reliability_score=d("0.620000"),
            resolution_clarity_score=d("0.700000"),
            signal_freshness_score=d("0.660000"),
            specialist_memory_confidence_score=d("0.680000"),
        ),
    )
    assert same_result.rows == result.rows
    assert same_result.derived_validation_digest == result.derived_validation_digest


def test_empty_queue_blocks_with_stable_zero_aggregates() -> None:
    result = report()

    assert result.status == "block"
    assert result.review_item_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_priority_score == d("0.000000")
    assert result.max_priority_score == d("0.000000")
    assert result.min_priority_score == d("0.000000")
    assert result.min_evidence_quality_score == d("0.000000")
    assert result.min_liquidity_reliability_score == d("0.000000")
    assert result.min_resolution_clarity_score == d("0.000000")
    assert result.min_signal_freshness_score == d("0.000000")
    assert result.min_specialist_memory_confidence_score == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == (
        "review_queue_ev_priority_report_empty",
        "review_queue_ev_priority_report_average_below_watch",
    )


def test_custom_config_drives_row_validation_and_status() -> None:
    custom_config = ResearchStrategyReviewQueueEvPriorityConfig(
        min_pass_priority_score=d("0.800000"),
        cost_adjusted_expected_value_weight=d("0.500000"),
        evidence_quality_weight=d("0.100000"),
        liquidity_reliability_weight=d("0.100000"),
        resolution_clarity_weight=d("0.100000"),
        signal_freshness_weight=d("0.100000"),
        specialist_memory_confidence_weight=d("0.100000"),
    )

    result = report(
        item(
            review_key="review_custom",
            cost_adjusted_expected_value_score=d("0.750000"),
            evidence_quality_score=d("0.800000"),
            liquidity_reliability_score=d("0.800000"),
            resolution_clarity_score=d("0.800000"),
            signal_freshness_score=d("0.800000"),
            specialist_memory_confidence_score=d("0.800000"),
        ),
        config=custom_config,
    )

    assert result.status == "watch"
    assert result.min_pass_priority_score == d("0.800000")
    assert result.average_priority_score == d("0.775000")
    assert result.reason_codes == (
        "review_queue_ev_priority_report_watch_rows",
        "review_queue_ev_priority_report_average_below_pass",
    )
    (row,) = result.rows
    assert row.priority_score == d("0.775000")
    assert row.lowest_dimension_score == d("0.750000")
    assert row.status == "watch"
    assert row.reason_codes == ("review_queue_ev_priority_score_below_pass",)


def test_payload_digest_frozen_flags_and_decimal_only_contract() -> None:
    result = report(item(review_key="review_payload"))
    payload = research_strategy_review_queue_ev_priority_report_payload(result)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["review_item_count"] == "1.000000"
    assert payload["average_priority_score"] == "0.865750"
    assert payload["rows"][0]["priority_score"] == "0.865750"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert research_strategy_review_queue_ev_priority_report_digest(result) == (
        result.derived_validation_digest
    )
    assert_digest(payload["derived_validation_digest"])
    assert_no_float_values(payload)
    assert_no_non_decimal_public_numbers(result)
    assert research_strategy_review_queue_ev_priority_report_payload(payload) == payload

    encoded = json.dumps(payload, sort_keys=True)
    assert ": 0.8" not in encoded
    assert_no_unsafe_payload_surface(payload)

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    tampered = dict(payload)
    tampered["average_priority_score"] = "0.800000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_review_queue_ev_priority_report_payload(tampered)
    with pytest.raises(ValueError, match="Decimal"):
        item(cost_adjusted_expected_value_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        item(evidence_quality_score=_DecimalSubclass("0.880000"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategyReviewQueueEvPriorityConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        item(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_research_strategy_review_queue_ev_priority_report(
            (item(readonly=False),),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "raw_candidate_id",
        "raw_market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "postgres_dsn",
        "table_name",
        "access_token",
        "wallet_ref",
        "order_ref",
        "trade_ref",
        "live_ref",
        "position_ref",
        "sizing_ref",
        "https://example.invalid/item",
    ),
)
def test_rejects_unsafe_public_keys_and_values(unsafe_value: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        item(review_key=unsafe_value)
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_review_queue_ev_priority_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                unsafe_value: "safe",
            },
        )


def test_module_scope_has_no_execution_or_raw_identifier_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "database",
        "db",
        "http",
        "network",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
        "submit",
        "trade",
        "write",
    }
    unsafe_public_terms = (
        "wallet",
        "order",
        "trade",
        "live",
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "position",
        "sizing",
    )

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    for public_name in api.__all__:
        assert not any(term in public_name.lower() for term in unsafe_public_terms)
    for cls in (
        api.ResearchStrategyReviewQueueEvPriorityConfig,
        api.ResearchStrategyReviewQueueEvPriorityItem,
        api.ResearchStrategyReviewQueueEvPriorityRow,
        api.ResearchStrategyReviewQueueEvPriorityReport,
    ):
        for field in fields(cls):
            assert not any(term in field.name.lower() for term in unsafe_public_terms)


def assert_digest(value: object) -> None:
    assert type(value) is str
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_float_values(item_value)
    if isinstance(value, (list, tuple)):
        for item_value in value:
            assert_no_float_values(item_value)


def assert_no_non_decimal_public_numbers(value: object) -> None:
    if type(value) is Decimal:
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal: {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_no_non_decimal_public_numbers(getattr(value, field.name))
        return
    if isinstance(value, (dict, list, tuple)):
        items = value.values() if isinstance(value, dict) else value
        for item_value in items:
            assert_no_non_decimal_public_numbers(item_value)


def assert_no_unsafe_payload_surface(value: object) -> None:
    unsafe_terms = (
        "wallet",
        "order",
        "trade",
        "live",
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "position",
        "sizing",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            assert not any(term in str(key).lower() for term in unsafe_terms)
            assert_no_unsafe_payload_surface(item_value)
    elif isinstance(value, (list, tuple)):
        for item_value in value:
            assert_no_unsafe_payload_surface(item_value)
    elif isinstance(value, str):
        lowered = value.lower()
        assert "://" not in lowered
        assert not any(term in lowered for term in unsafe_terms)
