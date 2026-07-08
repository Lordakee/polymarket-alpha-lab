from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_cost_adjusted_edge_gate_report import (
    DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_STATUSES,
    ResearchStrategyCostAdjustedEdgeGateConfig,
    ResearchStrategyCostAdjustedEdgeGateInput,
    ResearchStrategyCostAdjustedEdgeGateReasonCodeCount,
    ResearchStrategyCostAdjustedEdgeGateReport,
    ResearchStrategyCostAdjustedEdgeGateRow,
    build_research_strategy_cost_adjusted_edge_gate_report,
    research_strategy_cost_adjusted_edge_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyCostAdjustedEdgeGateConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_REPORT_CONFIG_VERSION
        ),
        "usable_edge_pass_floor": d("0.020000"),
        "usable_edge_watch_floor": d("0.000000"),
        "total_friction_pass_ceiling": d("0.030000"),
        "total_friction_watch_ceiling": d("0.060000"),
        "forecast_confidence_pass_floor": d("0.800000"),
        "forecast_confidence_watch_floor": d("0.500000"),
        "depth_quality_pass_floor": d("0.750000"),
        "depth_quality_watch_floor": d("0.450000"),
        "latency_quality_pass_floor": d("0.800000"),
        "latency_quality_watch_floor": d("0.500000"),
    }
    values.update(overrides)
    return ResearchStrategyCostAdjustedEdgeGateConfig(**values)


def gate_input(**overrides: object) -> ResearchStrategyCostAdjustedEdgeGateInput:
    values = {
        "candidate_id": "candidate_alpha_raw_id",
        "market_id": "market_alpha_raw_id",
        "market_slug": "market-alpha-slug",
        "market_question": "Will alpha resolve yes?",
        "source_url": "https://example.invalid/private-alpha",
        "source_text": "private alpha source text",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "candidate_forecast_probability": d("0.620000"),
        "market_probability": d("0.570000"),
        "fee_probability_drag": d("0.006000"),
        "spread_probability_drag": d("0.004000"),
        "depth_probability_drag": d("0.003000"),
        "latency_probability_haircut": d("0.002000"),
        "forecast_confidence_score": d("0.920000"),
        "depth_quality_score": d("0.900000"),
        "latency_quality_score": d("0.880000"),
    }
    values.update(overrides)
    return ResearchStrategyCostAdjustedEdgeGateInput(**values)


def report(
    *rows: ResearchStrategyCostAdjustedEdgeGateInput,
    cfg: ResearchStrategyCostAdjustedEdgeGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyCostAdjustedEdgeGateReport:
    return build_research_strategy_cost_adjusted_edge_gate_report(
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


def test_report_scores_edge_usability_after_costs_depth_and_latency() -> None:
    summary = report(
        gate_input(
            candidate_id="candidate_alpha_raw_id",
            market_id="market_alpha_raw_id",
            market_slug="market-alpha-slug",
            candidate_forecast_probability=d("0.620000"),
            market_probability=d("0.570000"),
            fee_probability_drag=d("0.006000"),
            spread_probability_drag=d("0.004000"),
            depth_probability_drag=d("0.003000"),
            latency_probability_haircut=d("0.002000"),
            forecast_confidence_score=d("0.920000"),
            depth_quality_score=d("0.900000"),
            latency_quality_score=d("0.880000"),
        ),
        gate_input(
            candidate_id="candidate_beta_raw_id",
            market_id="market_beta_raw_id",
            market_slug="market-beta-slug",
            candidate_forecast_probability=d("0.580000"),
            market_probability=d("0.510000"),
            fee_probability_drag=d("0.010000"),
            spread_probability_drag=d("0.020000"),
            depth_probability_drag=d("0.008000"),
            latency_probability_haircut=d("0.007000"),
            forecast_confidence_score=d("0.700000"),
            depth_quality_score=d("0.650000"),
            latency_quality_score=d("0.650000"),
        ),
        gate_input(
            candidate_id="candidate_gamma_raw_id",
            market_id="market_gamma_raw_id",
            market_slug="market-gamma-slug",
            candidate_forecast_probability=d("0.520000"),
            market_probability=d("0.510000"),
            fee_probability_drag=d("0.030000"),
            spread_probability_drag=d("0.035000"),
            depth_probability_drag=d("0.020000"),
            latency_probability_haircut=d("0.015000"),
            forecast_confidence_score=d("0.300000"),
            depth_quality_score=d("0.250000"),
            latency_quality_score=d("0.300000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyCostAdjustedEdgeGateReport
    assert summary.generated_at == GENERATED_AT
    assert summary.source_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_absolute_forecast_edge_probability == d("0.043333")
    assert summary.mean_total_friction_probability == d("0.053333")
    assert summary.mean_usable_edge_probability == d("-0.010000")
    assert summary.mean_forecast_confidence_score == d("0.640000")
    assert summary.mean_depth_quality_score == d("0.600000")
    assert summary.mean_latency_quality_score == d("0.610000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "cost_adjusted_edge_gate_report_block",
        "usable_edge_review",
        "total_friction_review",
        "forecast_confidence_review",
        "depth_quality_review",
        "latency_quality_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.candidate_id for row in summary.rows) == (
        "candidate_gamma_raw_id",
        "candidate_beta_raw_id",
        "candidate_alpha_raw_id",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyCostAdjustedEdgeGateRow)
    assert blocked.absolute_forecast_edge_probability == d("0.010000")
    assert blocked.total_friction_probability == d("0.100000")
    assert blocked.usable_edge_probability == d("-0.090000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "usable_edge_block",
        "total_friction_block",
        "forecast_confidence_block",
        "depth_quality_block",
        "latency_quality_block",
    )

    watched = summary.rows[1]
    assert watched.absolute_forecast_edge_probability == d("0.070000")
    assert watched.total_friction_probability == d("0.045000")
    assert watched.usable_edge_probability == d("0.025000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "total_friction_watch",
        "forecast_confidence_watch",
        "depth_quality_watch",
        "latency_quality_watch",
    )

    passed = summary.rows[2]
    assert passed.status == "pass"
    assert passed.reason_codes == ("cost_adjusted_edge_gate_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["total_friction_watch"] == ResearchStrategyCostAdjustedEdgeGateReasonCodeCount(
        reason_code="total_friction_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_deterministic_redacted_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_cost_adjusted_edge_gate_report_payload(
        report(gate_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_cost_adjusted_edge_gate_report_payload(
        report(gate_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["absolute_forecast_edge_probability"] == "0.050000"
    assert first_payload["rows"][0]["usable_edge_probability"] == "0.035000"
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
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "candidate_alpha_raw_id",
        "market_alpha_raw_id",
        "market-alpha-slug",
        "will alpha resolve yes",
        "https://example.invalid/private-alpha",
        "private alpha source text",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_cost_adjusted_edge_gate_report_payload(
        report(gate_input()),
    )
    tampered_payload["rows"][0]["total_friction_probability"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_cost_adjusted_edge_gate_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_cost_adjusted_edge_gate_report_payload(
            {
                "access_" + "token": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="candidate_forecast_probability"):
        gate_input(candidate_forecast_probability=0.62)
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
            gate_input(candidate_id="same_candidate", market_id="market_a"),
            gate_input(candidate_id="same_candidate", market_id="market_b"),
        )
    with pytest.raises(ValueError, match="usable_edge_pass_floor"):
        config(usable_edge_pass_floor=d("0.000000"), usable_edge_watch_floor=d("0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(gate_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_STATUSES == (
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
            total_friction_probability=d("0.010000"),
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
                "candidate_id",
                "market_id",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "drag",
                    "edge",
                    "floor",
                    "friction",
                    "haircut",
                    "probability",
                    "ratio",
                    "score",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_cost_adjusted_edge_gate_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_STATUSES",
        "ResearchStrategyCostAdjustedEdgeGateConfig",
        "ResearchStrategyCostAdjustedEdgeGateInput",
        "ResearchStrategyCostAdjustedEdgeGateReasonCodeCount",
        "ResearchStrategyCostAdjustedEdgeGateRow",
        "ResearchStrategyCostAdjustedEdgeGateReport",
        "build_research_strategy_cost_adjusted_edge_gate_report",
        "research_strategy_cost_adjusted_edge_gate_report_payload",
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
