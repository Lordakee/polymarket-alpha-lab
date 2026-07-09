from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_resolution_clause_edge_explainability_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_resolution_clause_edge_explainability_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 16, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def config(**overrides: object) -> object:
    values: dict[str, object] = {
        "cost_adjusted_edge_pass_floor": d("0.030000"),
        "cost_adjusted_edge_watch_floor": d("0.000000"),
        "clause_ambiguity_pass_ceiling": d("0.200000"),
        "clause_ambiguity_watch_ceiling": d("0.500000"),
        "edge_explainability_pass_floor": d("0.750000"),
        "edge_explainability_watch_floor": d("0.550000"),
        "source_confidence_pass_floor": d("0.700000"),
        "source_confidence_watch_floor": d("0.500000"),
        "clause_clarity_weight": d("0.300000"),
        "edge_quality_weight": d("0.400000"),
        "source_confidence_weight": d("0.200000"),
        "cost_stability_weight": d("0.100000"),
        "total_cost_drag_watch_ceiling": d("0.080000"),
    }
    values.update(overrides)
    return api().ResearchStrategyResolutionClauseEdgeExplainabilityConfig(**values)


def clause_input(**overrides: object) -> object:
    values: dict[str, object] = {
        "candidate_id": "candidate_alpha_raw_id",
        "market_id": "market_alpha_raw_id",
        "market_slug": "market-alpha-slug",
        "market_question": "Will alpha resolve yes?",
        "source_url": "https://example.invalid/private-alpha",
        "source_text": (
            "private source text dsn=postgres table=markets token=secret "
            "wallet order trade"
        ),
        "observed_at": datetime(2026, 7, 9, 15, 45, tzinfo=UTC),
        "forecast_probability": d("0.640000"),
        "market_probability": d("0.580000"),
        "fee_probability_drag": d("0.006000"),
        "spread_probability_drag": d("0.004000"),
        "liquidity_probability_drag": d("0.003000"),
        "resolution_cost_probability_drag": d("0.002000"),
        "clause_ambiguity_score": d("0.100000"),
        "edge_explanation_quality_score": d("0.900000"),
        "source_confidence_score": d("0.850000"),
    }
    values.update(overrides)
    return api().ResearchStrategyResolutionClauseEdgeExplainabilityInput(**values)


def build_report(*inputs: object, cfg: object | None = None) -> object:
    return api().build_research_strategy_resolution_clause_edge_explainability_report(
        inputs,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def walk_json(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_json(item)
        return
    if isinstance(value, list):
        for item in value:
            yield from walk_json(item)
        return
    yield value


def test_report_scores_clause_edge_explainability_across_pass_watch_and_block() -> None:
    module = api()

    report = build_report(
        clause_input(),
        clause_input(
            candidate_id="candidate_beta_raw_id",
            market_id="market_beta_raw_id",
            market_slug="market-beta-slug",
            market_question="Will beta resolve no?",
            source_url="https://example.invalid/private-beta",
            source_text="private beta source",
            forecast_probability=d("0.610000"),
            market_probability=d("0.560000"),
            fee_probability_drag=d("0.010000"),
            spread_probability_drag=d("0.008000"),
            liquidity_probability_drag=d("0.004000"),
            resolution_cost_probability_drag=d("0.003000"),
            clause_ambiguity_score=d("0.350000"),
            edge_explanation_quality_score=d("0.620000"),
            source_confidence_score=d("0.650000"),
        ),
        clause_input(
            candidate_id="candidate_gamma_raw_id",
            market_id="market_gamma_raw_id",
            market_slug="market-gamma-slug",
            market_question="Will gamma resolve yes?",
            source_url="https://example.invalid/private-gamma",
            source_text="private gamma source",
            forecast_probability=d("0.530000"),
            market_probability=d("0.510000"),
            fee_probability_drag=d("0.020000"),
            spread_probability_drag=d("0.020000"),
            liquidity_probability_drag=d("0.020000"),
            resolution_cost_probability_drag=d("0.010000"),
            clause_ambiguity_score=d("0.700000"),
            edge_explanation_quality_score=d("0.300000"),
            source_confidence_score=d("0.400000"),
        ),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyResolutionClauseEdgeExplainabilityReport
    assert report.generated_at == GENERATED_AT
    assert report.source_row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.mean_cost_adjusted_edge_probability == d("0.006667")
    assert report.mean_clause_ambiguity_score == d("0.383333")
    assert report.mean_edge_explainability_score == d("0.608500")
    assert report.min_edge_explainability_score == d("0.302500")
    assert report.status == "block"
    assert report.reason_codes == (
        "resolution_clause_edge_explainability_report_block",
        "cost_adjusted_edge_review",
        "resolution_clause_ambiguity_review",
        "edge_explainability_review",
        "source_confidence_review",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_digest(report.derived_validation_digest)

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    blocked, watched, passed = report.rows
    assert blocked.raw_forecast_edge_probability == d("0.020000")
    assert blocked.total_cost_drag_probability == d("0.070000")
    assert blocked.cost_adjusted_edge_probability == d("-0.050000")
    assert blocked.edge_explainability_score == d("0.302500")
    assert blocked.reason_codes == (
        "cost_adjusted_edge_block",
        "resolution_clause_ambiguity_block",
        "edge_explainability_block",
        "source_confidence_block",
    )
    assert watched.cost_adjusted_edge_probability == d("0.025000")
    assert watched.edge_explainability_score == d("0.641750")
    assert watched.reason_codes == (
        "cost_adjusted_edge_watch",
        "resolution_clause_ambiguity_watch",
        "edge_explainability_watch",
        "source_confidence_watch",
    )
    assert passed.cost_adjusted_edge_probability == d("0.045000")
    assert passed.edge_explainability_score == d("0.881250")
    assert passed.reason_codes == ("resolution_clause_edge_explainability_pass",)

    counts = {item.reason_code: item for item in report.reason_code_counts}
    assert counts[
        "resolution_clause_ambiguity_watch"
    ] == module.ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount(
        reason_code="resolution_clause_ambiguity_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_deterministic_sha256_bound_decimal_stringed_and_redacted() -> None:
    module = api()
    generated_at = GENERATED_AT.astimezone(timezone(timedelta(hours=-4)))
    raw_values = (
        "candidate_alpha_raw_id",
        "market_alpha_raw_id",
        "market-alpha-slug",
        "Will alpha resolve yes?",
        "https://example.invalid/private-alpha",
        "private source text",
        "dsn=postgres",
        "table=markets",
        "token=secret",
        "wallet",
        "order",
        "trade",
    )
    first = module.build_research_strategy_resolution_clause_edge_explainability_report(
        (clause_input(),),
        config=config(),
        generated_at=generated_at,
    )
    second = module.build_research_strategy_resolution_clause_edge_explainability_report(
        tuple(reversed((clause_input(),))),
        config=config(),
        generated_at=generated_at,
    )

    payload = module.research_strategy_resolution_clause_edge_explainability_report_payload(
        first,
    )
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_digest(payload["derived_validation_digest"])
    assert payload["generated_at"] == "2026-07-09T16:30:00+00:00"
    assert payload["source_row_count"] == "1.000000"
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["edge_explainability_score"] == "0.881250"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float, Decimal) for value in walk_json(payload))

    for forbidden in raw_values + (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
    ):
        assert forbidden.lower() not in encoded.lower()

    changed = build_report(clause_input(edge_explanation_quality_score=d("0.899999")))
    assert changed.derived_validation_digest != first.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, mean_clause_ambiguity_score=d("0.999999"))

    tampered_payload = dict(payload)
    tampered_payload["source_row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_resolution_clause_edge_explainability_report_payload(
            tampered_payload,
        )

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_resolution_clause_edge_explainability_report_payload(
            unsafe_key_payload,
        )


def test_empty_input_blocks_with_report_only_flags() -> None:
    report = build_report()

    assert report.source_row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.mean_cost_adjusted_edge_probability == d("0.000000")
    assert report.mean_clause_ambiguity_score == d("0.000000")
    assert report.mean_edge_explainability_score == d("0.000000")
    assert report.min_edge_explainability_score == d("0.000000")
    assert report.status == "block"
    assert report.reason_codes == (
        "resolution_clause_edge_explainability_report_empty",
    )
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_frozen_decimal_only_status_flags_and_validation_contracts() -> None:
    module = api()
    report = build_report(clause_input())

    assert module.RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    for contract in (
        module.ResearchStrategyResolutionClauseEdgeExplainabilityConfig,
        module.ResearchStrategyResolutionClauseEdgeExplainabilityInput,
        module.ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount,
        module.ResearchStrategyResolutionClauseEdgeExplainabilityRow,
        module.ResearchStrategyResolutionClauseEdgeExplainabilityReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(module.ResearchStrategyResolutionClauseEdgeExplainabilityConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        clause_input(forecast_probability=_DecimalSubclass("0.620000"))
    with pytest.raises(ValueError, match="cost_adjusted_edge"):
        config(
            cost_adjusted_edge_pass_floor=d("-0.010000"),
            cost_adjusted_edge_watch_floor=d("0.000000"),
        )
    with pytest.raises(ValueError, match="clause_ambiguity"):
        config(
            clause_ambiguity_pass_ceiling=d("0.600000"),
            clause_ambiguity_watch_ceiling=d("0.500000"),
        )
    with pytest.raises(ValueError, match="weights"):
        config(cost_stability_weight=d("0.200000"))
    with pytest.raises(ValueError, match="unsafe"):
        clause_input(candidate_id="")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="review")


def test_module_api_and_import_surface_are_report_only_readonly() -> None:
    module = api()

    assert (
        module.DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION
        == "research-strategy-resolution-clause-edge-explainability-report-v0"
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_RESOLUTION_CLAUSE_EDGE_EXPLAINABILITY_STATUSES",
        "ResearchStrategyResolutionClauseEdgeExplainabilityConfig",
        "ResearchStrategyResolutionClauseEdgeExplainabilityInput",
        "ResearchStrategyResolutionClauseEdgeExplainabilityReasonCodeCount",
        "ResearchStrategyResolutionClauseEdgeExplainabilityReport",
        "ResearchStrategyResolutionClauseEdgeExplainabilityRow",
        "build_research_strategy_resolution_clause_edge_explainability_report",
        "research_strategy_resolution_clause_edge_explainability_report_digest",
        "research_strategy_resolution_clause_edge_explainability_report_payload",
        "validate_research_strategy_resolution_clause_edge_explainability_report_digest",
    )
    source = module.__loader__.get_source(module.__name__).lower()
    assert "recommendation" not in source.replace('"recommendation"', "")

    tree = ast.parse(MODULE_PATH.read_text())
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    banned_fragments = (
        "asyncpg",
        "psycopg",
        "requests",
        "urllib",
        "websocket",
        "sqlalchemy",
        "supabase",
        "order",
        "trade",
        "wallet",
        "live",
        "auth",
    )
    assert not any(
        fragment in module_name.lower()
        for fragment in banned_fragments
        for module_name in imported_modules
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")
