from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_strategy_review_signal_priority_decay_report as api
from polymarket_alpha_lab.research_strategy_review_signal_priority_decay_report import (
    DEFAULT_RESEARCH_STRATEGY_REVIEW_SIGNAL_PRIORITY_DECAY_REPORT_CONFIG_VERSION,
    REVIEW_SIGNAL_PRIORITY_DECAY_DIMENSIONS,
    ResearchStrategyReviewSignalPriorityDecayConfig,
    ResearchStrategyReviewSignalPriorityDecayReport,
    ResearchStrategyReviewSignalPriorityDecaySignal,
    build_research_strategy_review_signal_priority_decay_report,
    research_strategy_review_signal_priority_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_review_signal_priority_decay_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(**overrides: object) -> ResearchStrategyReviewSignalPriorityDecaySignal:
    values = {
        "review_key": "review_pass",
        "signal_freshness_score": d("0.950000"),
        "evidence_strength_score": d("0.900000"),
        "authority_score": d("0.900000"),
        "movement_score": d("0.100000"),
        "cost_drag_score": d("0.100000"),
        "liquidity_quality_score": d("0.900000"),
        "resolution_clarity_score": d("0.900000"),
        "specialist_memory_confidence_score": d("0.900000"),
    }
    values.update(overrides)
    return ResearchStrategyReviewSignalPriorityDecaySignal(**values)


def report(
    *signals: ResearchStrategyReviewSignalPriorityDecaySignal,
    config: ResearchStrategyReviewSignalPriorityDecayConfig | None = None,
) -> ResearchStrategyReviewSignalPriorityDecayReport:
    return build_research_strategy_review_signal_priority_decay_report(
        signals,
        generated_at=GENERATED_AT,
        config=config,
    )


def test_public_api_declares_report_only_decay_surface() -> None:
    assert DEFAULT_RESEARCH_STRATEGY_REVIEW_SIGNAL_PRIORITY_DECAY_REPORT_CONFIG_VERSION == (
        "research-strategy-review-signal-priority-decay-report"
    )
    assert REVIEW_SIGNAL_PRIORITY_DECAY_DIMENSIONS == (
        "signal_freshness",
        "evidence_strength",
        "authority",
        "movement",
        "cost_drag",
        "liquidity_quality",
        "resolution_clarity",
        "specialist_memory_confidence",
    )
    assert api.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_REVIEW_SIGNAL_PRIORITY_DECAY_REPORT_CONFIG_VERSION",
        "REVIEW_SIGNAL_PRIORITY_DECAY_DIMENSIONS",
        "ResearchStrategyReviewSignalPriorityDecayConfig",
        "ResearchStrategyReviewSignalPriorityDecayReport",
        "ResearchStrategyReviewSignalPriorityDecayRow",
        "ResearchStrategyReviewSignalPriorityDecaySignal",
        "build_research_strategy_review_signal_priority_decay_report",
        "research_strategy_review_signal_priority_decay_report_payload",
    )

    field_defaults = {
        field.name: field.default
        for field in fields(ResearchStrategyReviewSignalPriorityDecayConfig)
    }
    assert field_defaults["paper_only"] is True
    assert field_defaults["report_only"] is True
    assert field_defaults["readonly"] is True
    assert field_defaults["min_pass_priority_score"] == d("0.800000")
    assert field_defaults["min_watch_priority_score"] == d("0.550000")
    assert field_defaults["min_pass_dimension_score"] == d("0.700000")
    assert field_defaults["min_watch_dimension_score"] == d("0.500000")
    assert field_defaults["max_pass_movement_score"] == d("0.300000")
    assert field_defaults["max_watch_movement_score"] == d("0.600000")
    assert field_defaults["max_pass_cost_drag_score"] == d("0.250000")
    assert field_defaults["max_watch_cost_drag_score"] == d("0.500000")


def test_decay_report_scores_pass_watch_and_block_rows_deterministically() -> None:
    result = report(
        signal(review_key="review_pass"),
        signal(
            review_key="review_watch",
            signal_freshness_score=d("0.650000"),
            evidence_strength_score=d("0.680000"),
            authority_score=d("0.720000"),
            movement_score=d("0.400000"),
            cost_drag_score=d("0.350000"),
            liquidity_quality_score=d("0.700000"),
            resolution_clarity_score=d("0.650000"),
            specialist_memory_confidence_score=d("0.670000"),
        ),
        signal(
            review_key="review_block",
            signal_freshness_score=d("0.300000"),
            evidence_strength_score=d("0.450000"),
            authority_score=d("0.450000"),
            movement_score=d("0.750000"),
            cost_drag_score=d("0.650000"),
            liquidity_quality_score=d("0.400000"),
            resolution_clarity_score=d("0.450000"),
            specialist_memory_confidence_score=d("0.450000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-strategy-review-signal-priority-decay-report"
    )
    assert result.report_status == "block"
    assert result.review_item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_priority_retention_score == d("0.652917")
    assert result.max_priority_decay_score == d("0.612500")
    assert result.max_movement_score == d("0.750000")
    assert result.max_cost_drag_score == d("0.650000")
    assert result.min_signal_freshness_score == d("0.300000")
    assert result.reason_codes == (
        "review_signal_priority_decay_report_block_rows",
        "review_signal_priority_decay_report_watch_rows",
        "review_signal_priority_decay_report_average_below_pass",
        "review_signal_priority_decay_report_movement_elevated",
        "review_signal_priority_decay_report_cost_drag_elevated",
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

    assert blocked.movement_stability_score == d("0.250000")
    assert blocked.cost_efficiency_score == d("0.350000")
    assert blocked.priority_retention_score == d("0.387500")
    assert blocked.priority_decay_score == d("0.612500")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "review_signal_priority_decay_signal_freshness_block",
        "review_signal_priority_decay_evidence_strength_block",
        "review_signal_priority_decay_authority_block",
        "review_signal_priority_decay_movement_block",
        "review_signal_priority_decay_cost_drag_block",
        "review_signal_priority_decay_liquidity_quality_block",
        "review_signal_priority_decay_resolution_clarity_block",
        "review_signal_priority_decay_specialist_memory_confidence_block",
        "review_signal_priority_decay_priority_retention_below_watch",
    )

    assert watched.movement_stability_score == d("0.600000")
    assert watched.cost_efficiency_score == d("0.650000")
    assert watched.priority_retention_score == d("0.665000")
    assert watched.priority_decay_score == d("0.335000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "review_signal_priority_decay_signal_freshness_watch",
        "review_signal_priority_decay_evidence_strength_watch",
        "review_signal_priority_decay_movement_watch",
        "review_signal_priority_decay_cost_drag_watch",
        "review_signal_priority_decay_resolution_clarity_watch",
        "review_signal_priority_decay_specialist_memory_confidence_watch",
        "review_signal_priority_decay_priority_retention_below_pass",
    )

    assert passed.priority_retention_score == d("0.906250")
    assert passed.priority_decay_score == d("0.093750")
    assert passed.status == "pass"
    assert passed.reason_codes == ("review_signal_priority_decay_passed",)

    same_result = report(
        signal(review_key="review_pass"),
        signal(
            review_key="review_block",
            signal_freshness_score=d("0.300000"),
            evidence_strength_score=d("0.450000"),
            authority_score=d("0.450000"),
            movement_score=d("0.750000"),
            cost_drag_score=d("0.650000"),
            liquidity_quality_score=d("0.400000"),
            resolution_clarity_score=d("0.450000"),
            specialist_memory_confidence_score=d("0.450000"),
        ),
        signal(
            review_key="review_watch",
            signal_freshness_score=d("0.650000"),
            evidence_strength_score=d("0.680000"),
            authority_score=d("0.720000"),
            movement_score=d("0.400000"),
            cost_drag_score=d("0.350000"),
            liquidity_quality_score=d("0.700000"),
            resolution_clarity_score=d("0.650000"),
            specialist_memory_confidence_score=d("0.670000"),
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
    assert result.average_priority_retention_score == d("0.000000")
    assert result.max_priority_decay_score == d("0.000000")
    assert result.max_movement_score == d("0.000000")
    assert result.max_cost_drag_score == d("0.000000")
    assert result.min_signal_freshness_score == d("0.000000")
    assert result.rows == ()
    assert result.reason_codes == (
        "review_signal_priority_decay_report_empty",
        "review_signal_priority_decay_report_average_below_watch",
    )


def test_payload_digest_frozen_flags_and_decimal_only_contract() -> None:
    result = report(signal(review_key="review_payload"))
    payload = research_strategy_review_signal_priority_decay_report_payload(result)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["review_item_count"] == "1.000000"
    assert payload["average_priority_retention_score"] == "0.906250"
    assert payload["rows"][0]["priority_decay_score"] == "0.093750"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert_digest(payload["derived_validation_digest"])
    assert_no_float_values(payload)
    assert_no_non_decimal_public_numbers(result)
    assert research_strategy_review_signal_priority_decay_report_payload(payload) == payload

    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    tampered = dict(payload)
    tampered["average_priority_retention_score"] = "0.900001"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_review_signal_priority_decay_report_payload(tampered)
    with pytest.raises(ValueError, match="Decimal"):
        signal(evidence_strength_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        signal(authority_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="paper_only"):
        ResearchStrategyReviewSignalPriorityDecayConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_research_strategy_review_signal_priority_decay_report(
            (signal(readonly=False),),
            generated_at=GENERATED_AT,
        )


def test_payload_validation_rejects_digest_matching_forged_schema_and_status() -> None:
    payload = research_strategy_review_signal_priority_decay_report_payload(
        report(signal(review_key="review_payload")),
    )

    forged_extra_key = dict(payload)
    forged_extra_key["safe_extra"] = "safe"
    forged_extra_key["derived_validation_digest"] = api._digest_from_values(
        forged_extra_key,
    )
    with pytest.raises(ValueError, match="schema"):
        research_strategy_review_signal_priority_decay_report_payload(forged_extra_key)

    forged_report_status = dict(payload)
    forged_report_status["report_status"] = "clear"
    forged_report_status["derived_validation_digest"] = api._digest_from_values(
        forged_report_status,
    )
    with pytest.raises(ValueError, match="pass, watch, or block"):
        research_strategy_review_signal_priority_decay_report_payload(forged_report_status)

    forged_row_status = dict(payload)
    forged_rows = [dict(item) for item in payload["rows"]]  # type: ignore[index]
    forged_rows[0]["status"] = "clear"
    forged_row_status["rows"] = forged_rows
    forged_row_status["derived_validation_digest"] = api._digest_from_values(
        forged_row_status,
    )
    with pytest.raises(ValueError, match="pass, watch, or block"):
        research_strategy_review_signal_priority_decay_report_payload(forged_row_status)


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
        "live_surface",
        "position_ref",
        "https://example.invalid/item",
    ),
)
def test_rejects_unsafe_public_keys_and_values(unsafe_value: str) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        signal(review_key=unsafe_value)
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_review_signal_priority_decay_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                unsafe_value: "safe",
            },
        )


def test_module_scope_has_no_execution_or_exposure_surfaces() -> None:
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

    forbidden_import_roots = {
        "httpx",
        "os",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
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
        "rollback",
        "sell",
        "send",
        "sign",
        "submit",
        "trade",
        "write",
    }
    unsafe_public_terms = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
        "position",
    )

    assert not float_constants
    assert not any(imported.split(".", 1)[0] in forbidden_import_roots for imported in imports)
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    for public_name in api.__all__:
        assert not any(term in public_name.lower() for term in unsafe_public_terms)
    for cls in (
        api.ResearchStrategyReviewSignalPriorityDecayConfig,
        api.ResearchStrategyReviewSignalPriorityDecaySignal,
        api.ResearchStrategyReviewSignalPriorityDecayRow,
        api.ResearchStrategyReviewSignalPriorityDecayReport,
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
