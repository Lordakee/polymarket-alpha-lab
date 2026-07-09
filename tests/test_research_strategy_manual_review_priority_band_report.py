from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_strategy_manual_review_priority_band_report as api
from polymarket_alpha_lab.research_strategy_manual_review_priority_band_report import (
    ResearchStrategyManualReviewPriorityBandConfig,
    ResearchStrategyManualReviewPriorityBandReport,
    ResearchStrategyManualReviewPriorityBandSignal,
    build_research_strategy_manual_review_priority_band_report,
    research_strategy_manual_review_priority_band_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_manual_review_priority_band_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(**overrides: object) -> ResearchStrategyManualReviewPriorityBandSignal:
    values = {
        "review_key": "review_alpha",
        "evidence_completeness_score": d("0.950000"),
        "cost_sanity_score": d("0.900000"),
        "liquidity_reliability_score": d("0.900000"),
        "resolution_ambiguity_score": d("0.100000"),
        "team_memory_readiness_score": d("0.900000"),
    }
    values.update(overrides)
    return ResearchStrategyManualReviewPriorityBandSignal(**values)


def report(
    *signals: ResearchStrategyManualReviewPriorityBandSignal,
    config: ResearchStrategyManualReviewPriorityBandConfig | None = None,
) -> ResearchStrategyManualReviewPriorityBandReport:
    return build_research_strategy_manual_review_priority_band_report(
        signals,
        generated_at=GENERATED_AT,
        config=config,
    )


def test_public_api_declares_report_only_priority_band_surface() -> None:
    assert api.DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_PRIORITY_BAND_CONFIG_VERSION == (
        "research-strategy-manual-review-priority-band-report"
    )
    assert api.MANUAL_REVIEW_PRIORITY_BAND_DIMENSIONS == (
        "evidence_completeness",
        "cost_sanity",
        "liquidity_reliability",
        "resolution_ambiguity",
        "team_memory_readiness",
    )
    assert api.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MANUAL_REVIEW_PRIORITY_BAND_CONFIG_VERSION",
        "MANUAL_REVIEW_PRIORITY_BAND_DIMENSIONS",
        "ResearchStrategyManualReviewPriorityBandConfig",
        "ResearchStrategyManualReviewPriorityBandReport",
        "ResearchStrategyManualReviewPriorityBandRow",
        "ResearchStrategyManualReviewPriorityBandSignal",
        "build_research_strategy_manual_review_priority_band_report",
        "research_strategy_manual_review_priority_band_report_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(ResearchStrategyManualReviewPriorityBandConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True
    assert field_defaults["min_pass_readiness_score"] == d("0.850000")
    assert field_defaults["min_watch_readiness_score"] == d("0.650000")
    assert field_defaults["min_pass_dimension_score"] == d("0.800000")
    assert field_defaults["min_watch_dimension_score"] == d("0.600000")
    assert field_defaults["max_pass_ambiguity_score"] == d("0.250000")
    assert field_defaults["max_watch_ambiguity_score"] == d("0.500000")


def test_priority_band_report_assigns_bands_and_aggregates_deterministically() -> None:
    result = report(
        signal(review_key="review_pass"),
        signal(
            review_key="review_watch",
            evidence_completeness_score=d("0.700000"),
            cost_sanity_score=d("0.720000"),
            liquidity_reliability_score=d("0.750000"),
            resolution_ambiguity_score=d("0.400000"),
            team_memory_readiness_score=d("0.650000"),
        ),
        signal(
            review_key="review_block",
            evidence_completeness_score=d("0.400000"),
            cost_sanity_score=d("0.450000"),
            liquidity_reliability_score=d("0.500000"),
            resolution_ambiguity_score=d("0.800000"),
            team_memory_readiness_score=d("0.500000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-strategy-manual-review-priority-band-report"
    assert result.report_status == "block"
    assert result.review_item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_review_readiness_score == d("0.668000")
    assert result.min_review_readiness_score == d("0.410000")
    assert result.max_resolution_ambiguity_score == d("0.800000")
    assert result.min_liquidity_reliability_score == d("0.500000")
    assert result.reason_codes == (
        "manual_review_priority_report_block_rows",
        "manual_review_priority_report_watch_rows",
        "manual_review_priority_report_average_below_pass",
        "manual_review_priority_report_ambiguity_elevated",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)
    assert_no_non_decimal_public_numbers(result)

    blocked, watched, passed = result.rows
    assert (blocked.rank, watched.rank, passed.rank) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert (blocked.review_key, watched.review_key, passed.review_key) == (
        "review_block",
        "review_watch",
        "review_pass",
    )

    assert blocked.resolution_clarity_score == d("0.200000")
    assert blocked.review_readiness_score == d("0.410000")
    assert blocked.priority_band == "block"
    assert blocked.reason_codes == (
        "manual_review_priority_evidence_block",
        "manual_review_priority_cost_block",
        "manual_review_priority_liquidity_block",
        "manual_review_priority_resolution_block",
        "manual_review_priority_memory_block",
        "manual_review_priority_readiness_below_watch",
    )

    assert watched.resolution_clarity_score == d("0.600000")
    assert watched.review_readiness_score == d("0.684000")
    assert watched.priority_band == "watch"
    assert watched.reason_codes == (
        "manual_review_priority_evidence_watch",
        "manual_review_priority_cost_watch",
        "manual_review_priority_liquidity_watch",
        "manual_review_priority_resolution_watch",
        "manual_review_priority_memory_watch",
        "manual_review_priority_readiness_below_pass",
    )

    assert passed.resolution_clarity_score == d("0.900000")
    assert passed.review_readiness_score == d("0.910000")
    assert passed.priority_band == "pass"
    assert passed.reason_codes == ("manual_review_priority_band_passed",)

    same_result = report(
        signal(
            review_key="review_block",
            evidence_completeness_score=d("0.400000"),
            cost_sanity_score=d("0.450000"),
            liquidity_reliability_score=d("0.500000"),
            resolution_ambiguity_score=d("0.800000"),
            team_memory_readiness_score=d("0.500000"),
        ),
        signal(review_key="review_pass"),
        signal(
            review_key="review_watch",
            evidence_completeness_score=d("0.700000"),
            cost_sanity_score=d("0.720000"),
            liquidity_reliability_score=d("0.750000"),
            resolution_ambiguity_score=d("0.400000"),
            team_memory_readiness_score=d("0.650000"),
        ),
    )
    assert same_result.rows == result.rows
    assert same_result.derived_validation_digest == result.derived_validation_digest


def test_empty_signal_set_blocks_with_stable_zero_aggregates() -> None:
    result = report()

    assert result.report_status == "block"
    assert result.review_item_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_review_readiness_score == d("0.000000")
    assert result.min_review_readiness_score == d("0.000000")
    assert result.max_resolution_ambiguity_score == d("0.000000")
    assert result.min_liquidity_reliability_score == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == (
        "manual_review_priority_report_empty",
        "manual_review_priority_report_average_below_watch",
    )


def test_payload_digest_frozen_flags_and_decimal_only_contract() -> None:
    result = report(signal(review_key="review_payload"))
    payload = research_strategy_manual_review_priority_band_report_payload(result)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["review_item_count"] == "1.000000"
    assert payload["average_review_readiness_score"] == "0.910000"
    assert payload["rows"][0]["review_readiness_score"] == "0.910000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert_digest(payload["derived_validation_digest"])
    assert_no_float_values(payload)
    assert_no_non_decimal_public_numbers(result)
    assert research_strategy_manual_review_priority_band_report_payload(payload) == payload

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    tampered = dict(payload)
    tampered["average_review_readiness_score"] = "0.900001"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_manual_review_priority_band_report_payload(tampered)
    with pytest.raises(ValueError, match="Decimal"):
        signal(evidence_completeness_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        signal(cost_sanity_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategyManualReviewPriorityBandConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_research_strategy_manual_review_priority_band_report(
            (signal(readonly=False),),
            generated_at=GENERATED_AT,
        )


def test_payload_validation_rejects_forged_status_and_decimal_strings() -> None:
    payload = research_strategy_manual_review_priority_band_report_payload(
        report(signal(review_key="review_payload_schema")),
    )

    forged_status = dict(payload)
    forged_status["report_status"] = "investigate"
    forged_status["derived_validation_digest"] = api._digest_from_values(forged_status)
    with pytest.raises(ValueError, match="report_status"):
        research_strategy_manual_review_priority_band_report_payload(forged_status)

    forged_row_status = dict(payload)
    forged_row_status["rows"] = [dict(payload["rows"][0], priority_band="investigate")]
    forged_row_status["derived_validation_digest"] = api._digest_from_values(
        forged_row_status,
    )
    with pytest.raises(ValueError, match="priority_band"):
        research_strategy_manual_review_priority_band_report_payload(forged_row_status)

    forged_decimal = dict(payload)
    forged_decimal["average_review_readiness_score"] = "not-a-decimal"
    forged_decimal["derived_validation_digest"] = api._digest_from_values(forged_decimal)
    with pytest.raises(ValueError, match="average_review_readiness_score"):
        research_strategy_manual_review_priority_band_report_payload(forged_decimal)


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
        "network_ref",
        "auth_ref",
        "recommendation_ref",
        "sizing_ref",
        "https://example.invalid/item",
    ),
)
def test_rejects_unsafe_public_keys_and_values(unsafe_value: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        signal(review_key=unsafe_value)
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_manual_review_priority_band_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                unsafe_value: "safe",
            },
        )


def test_module_scope_has_no_live_execution_or_raw_identifier_surfaces() -> None:
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
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
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
        "auth",
        "wallet",
        "order",
        "buy",
        "sell",
        "trade",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "recommendation",
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
        api.ResearchStrategyManualReviewPriorityBandConfig,
        api.ResearchStrategyManualReviewPriorityBandSignal,
        api.ResearchStrategyManualReviewPriorityBandRow,
        api.ResearchStrategyManualReviewPriorityBandReport,
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
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


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
        for item in items:
            assert_no_non_decimal_public_numbers(item)
