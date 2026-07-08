from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_cost_adjusted_probability_gate_report import (
    DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_GATE_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_GATE_STATUSES,
    ResearchStrategyCostAdjustedProbabilityGateConfig,
    ResearchStrategyCostAdjustedProbabilityGateInput,
    ResearchStrategyCostAdjustedProbabilityGateReasonCodeCount,
    ResearchStrategyCostAdjustedProbabilityGateReport,
    ResearchStrategyCostAdjustedProbabilityGateRow,
    build_research_strategy_cost_adjusted_probability_gate_report,
    research_strategy_cost_adjusted_probability_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyCostAdjustedProbabilityGateConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_GATE_REPORT_CONFIG_VERSION
        ),
        "cost_adjusted_probability_gap_pass_floor": d("0.020000"),
        "cost_adjusted_probability_gap_watch_floor": d("0.000000"),
        "probability_quality_pass_floor": d("0.800000"),
        "probability_quality_watch_floor": d("0.500000"),
        "total_cost_drag_pass_ceiling": d("0.025000"),
        "total_cost_drag_watch_ceiling": d("0.060000"),
        "liquidity_sanity_pass_floor": d("0.750000"),
        "liquidity_sanity_watch_floor": d("0.450000"),
        "evidence_confidence_pass_floor": d("0.800000"),
        "evidence_confidence_watch_floor": d("0.500000"),
        "recheck_urgency_pass_ceiling": d("0.300000"),
        "recheck_urgency_watch_ceiling": d("0.700000"),
    }
    values.update(overrides)
    return ResearchStrategyCostAdjustedProbabilityGateConfig(**values)


def gate_input(**overrides: object) -> ResearchStrategyCostAdjustedProbabilityGateInput:
    values = {
        "probability_case_ref": "case_alpha",
        "strategy_ref": "strategy_alpha",
        "market_slug": "market-alpha",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "raw_forecast_probability": d("0.620000"),
        "market_probability": d("0.570000"),
        "probability_quality_score": d("0.920000"),
        "fee_probability_drag": d("0.006000"),
        "spread_probability_drag": d("0.004000"),
        "slippage_probability_drag": d("0.002000"),
        "liquidity_sanity_score": d("0.880000"),
        "evidence_confidence_score": d("0.910000"),
        "recheck_urgency_score": d("0.100000"),
    }
    values.update(overrides)
    return ResearchStrategyCostAdjustedProbabilityGateInput(**values)


def report(
    *rows: ResearchStrategyCostAdjustedProbabilityGateInput,
    cfg: ResearchStrategyCostAdjustedProbabilityGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyCostAdjustedProbabilityGateReport:
    return build_research_strategy_cost_adjusted_probability_gate_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def test_report_scores_aggregate_cost_adjusted_probability_readiness_for_manual_review() -> None:
    summary = report(
        gate_input(
            probability_case_ref="case_alpha",
            strategy_ref="strategy_alpha",
            market_slug="market-alpha",
            raw_forecast_probability=d("0.620000"),
            market_probability=d("0.570000"),
            probability_quality_score=d("0.920000"),
            fee_probability_drag=d("0.006000"),
            spread_probability_drag=d("0.004000"),
            slippage_probability_drag=d("0.002000"),
            liquidity_sanity_score=d("0.880000"),
            evidence_confidence_score=d("0.910000"),
            recheck_urgency_score=d("0.100000"),
        ),
        gate_input(
            probability_case_ref="case_beta",
            strategy_ref="strategy_beta",
            market_slug="market-beta",
            raw_forecast_probability=d("0.580000"),
            market_probability=d("0.510000"),
            probability_quality_score=d("0.700000"),
            fee_probability_drag=d("0.012000"),
            spread_probability_drag=d("0.018000"),
            slippage_probability_drag=d("0.010000"),
            liquidity_sanity_score=d("0.620000"),
            evidence_confidence_score=d("0.680000"),
            recheck_urgency_score=d("0.550000"),
        ),
        gate_input(
            probability_case_ref="case_gamma",
            strategy_ref="strategy_gamma",
            market_slug="market-gamma",
            raw_forecast_probability=d("0.520000"),
            market_probability=d("0.510000"),
            probability_quality_score=d("0.350000"),
            fee_probability_drag=d("0.030000"),
            spread_probability_drag=d("0.035000"),
            slippage_probability_drag=d("0.020000"),
            liquidity_sanity_score=d("0.250000"),
            evidence_confidence_score=d("0.300000"),
            recheck_urgency_score=d("0.900000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyCostAdjustedProbabilityGateReport
    assert summary.generated_at == GENERATED_AT
    assert summary.source_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_raw_probability_quality == d("0.656667")
    assert summary.mean_total_cost_drag_probability == d("0.045667")
    assert summary.mean_cost_adjusted_probability_gap == d("-0.002333")
    assert summary.mean_liquidity_sanity_score == d("0.583333")
    assert summary.mean_evidence_confidence_score == d("0.630000")
    assert summary.max_recheck_urgency_score == d("0.900000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "cost_adjusted_probability_gate_report_block",
        "cost_adjusted_probability_gap_review",
        "cost_drag_review",
        "evidence_confidence_review",
        "liquidity_sanity_review",
        "probability_quality_review",
        "recheck_urgency_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.probability_case_ref for row in summary.rows) == (
        "case_gamma",
        "case_beta",
        "case_alpha",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyCostAdjustedProbabilityGateRow)
    assert blocked.raw_probability_gap == d("0.010000")
    assert blocked.total_cost_drag_probability == d("0.085000")
    assert blocked.cost_adjusted_probability_gap == d("-0.075000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "cost_adjusted_probability_gap_block",
        "cost_drag_block",
        "evidence_confidence_block",
        "liquidity_sanity_block",
        "probability_quality_block",
        "recheck_urgency_block",
    )

    watched = summary.rows[1]
    assert watched.raw_probability_gap == d("0.070000")
    assert watched.total_cost_drag_probability == d("0.040000")
    assert watched.cost_adjusted_probability_gap == d("0.030000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "cost_drag_watch",
        "evidence_confidence_watch",
        "liquidity_sanity_watch",
        "probability_quality_watch",
        "recheck_urgency_watch",
    )

    passed = summary.rows[2]
    assert passed.status == "pass"
    assert passed.reason_codes == ("cost_adjusted_probability_gate_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["cost_drag_watch"] == ResearchStrategyCostAdjustedProbabilityGateReasonCodeCount(
        reason_code="cost_drag_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_cost_adjusted_probability_gate_report_payload(
        report(gate_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_cost_adjusted_probability_gate_report_payload(
        report(gate_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["raw_probability_gap"] == "0.050000"
    assert first_payload["rows"][0]["cost_adjusted_probability_gap"] == "0.038000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )
    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "probability_case_ref",
        "strategy_ref",
        "market_slug",
        "case_alpha",
        "strategy_alpha",
        "market-alpha",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_cost_adjusted_probability_gate_report_payload(
        report(gate_input()),
    )
    tampered_payload["rows"][0]["total_cost_drag_probability"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_cost_adjusted_probability_gate_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_cost_adjusted_probability_gate_report_payload(
            {
                "secret_ref": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_cases() -> None:
    with pytest.raises(ValueError, match="raw_forecast_probability"):
        gate_input(raw_forecast_probability=0.62)
    with pytest.raises(ValueError, match="fee_probability_drag"):
        gate_input(fee_probability_drag=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="market_probability"):
        gate_input(market_probability=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        gate_input(observed_at=datetime(2026, 7, 8, 11, 40))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            gate_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(gate_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            gate_input(probability_case_ref="same_case"),
            gate_input(probability_case_ref="same_case", strategy_ref="strategy_beta"),
        )
    with pytest.raises(ValueError, match="probability_quality_pass_floor"):
        config(probability_quality_pass_floor=d("0.400000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(gate_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_GATE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            total_cost_drag_probability=d("0.010000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            source_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        gate_input(),
        row,
        summary,
        *summary.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "probability_case_ref",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "drag",
                    "floor",
                    "gap",
                    "probability",
                    "ratio",
                    "score",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_cost_adjusted_probability_gate_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_GATE_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_GATE_STATUSES",
        "ResearchStrategyCostAdjustedProbabilityGateConfig",
        "ResearchStrategyCostAdjustedProbabilityGateInput",
        "ResearchStrategyCostAdjustedProbabilityGateReasonCodeCount",
        "ResearchStrategyCostAdjustedProbabilityGateRow",
        "ResearchStrategyCostAdjustedProbabilityGateReport",
        "build_research_strategy_cost_adjusted_probability_gate_report",
        "research_strategy_cost_adjusted_probability_gate_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_source_terms = (
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "trad" + "ing",
        "data" + "base",
        "net" + "work",
        "request",
        "socket",
        "subprocess",
        "open(",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
