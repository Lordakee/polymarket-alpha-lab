from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_cost_adjusted_probability_band_report import (
    DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_STATUSES,
    ResearchStrategyCostAdjustedProbabilityBandConfig,
    ResearchStrategyCostAdjustedProbabilityBandInput,
    ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount,
    ResearchStrategyCostAdjustedProbabilityBandReport,
    ResearchStrategyCostAdjustedProbabilityBandRow,
    build_research_strategy_cost_adjusted_probability_band_report,
    research_strategy_cost_adjusted_probability_band_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyCostAdjustedProbabilityBandConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_REPORT_CONFIG_VERSION
        ),
        "model_confidence_pass_floor": d("0.750000"),
        "model_confidence_watch_floor": d("0.450000"),
        "total_cost_drag_pass_ceiling": d("0.035000"),
        "total_cost_drag_watch_ceiling": d("0.080000"),
        "liquidity_quality_pass_floor": d("0.700000"),
        "liquidity_quality_watch_floor": d("0.400000"),
        "resolution_ambiguity_pass_ceiling": d("0.250000"),
        "resolution_ambiguity_watch_ceiling": d("0.600000"),
        "band_half_width_pass_ceiling": d("0.090000"),
        "band_half_width_watch_ceiling": d("0.180000"),
        "market_distance_pass_ceiling": d("0.020000"),
        "market_distance_watch_ceiling": d("0.080000"),
        "model_confidence_uncertainty_weight": d("0.100000"),
        "liquidity_uncertainty_weight": d("0.060000"),
        "resolution_ambiguity_uncertainty_weight": d("0.080000"),
    }
    values.update(overrides)
    return ResearchStrategyCostAdjustedProbabilityBandConfig(**values)


def band_input(**overrides: object) -> ResearchStrategyCostAdjustedProbabilityBandInput:
    values = {
        "candidate_ref": "candidate_alpha",
        "market_ref": "event_market_alpha",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "model_probability": d("0.640000"),
        "model_confidence_score": d("0.900000"),
        "market_probability": d("0.620000"),
        "fee_probability_drag": d("0.004000"),
        "spread_probability_drag": d("0.003000"),
        "slippage_probability_drag": d("0.002000"),
        "liquidity_quality_score": d("0.900000"),
        "resolution_ambiguity_score": d("0.100000"),
    }
    values.update(overrides)
    return ResearchStrategyCostAdjustedProbabilityBandInput(**values)


def report(
    *rows: ResearchStrategyCostAdjustedProbabilityBandInput,
    cfg: ResearchStrategyCostAdjustedProbabilityBandConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyCostAdjustedProbabilityBandReport:
    return build_research_strategy_cost_adjusted_probability_band_report(
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


def test_report_builds_cost_adjusted_probability_bands_without_action_surface() -> None:
    summary = report(
        band_input(
            candidate_ref="candidate_alpha",
            market_ref="event_market_alpha",
            model_probability=d("0.640000"),
            model_confidence_score=d("0.900000"),
            market_probability=d("0.620000"),
            fee_probability_drag=d("0.004000"),
            spread_probability_drag=d("0.003000"),
            slippage_probability_drag=d("0.002000"),
            liquidity_quality_score=d("0.900000"),
            resolution_ambiguity_score=d("0.100000"),
        ),
        band_input(
            candidate_ref="candidate_beta",
            market_ref="event_market_beta",
            model_probability=d("0.580000"),
            model_confidence_score=d("0.700000"),
            market_probability=d("0.520000"),
            fee_probability_drag=d("0.012000"),
            spread_probability_drag=d("0.018000"),
            slippage_probability_drag=d("0.010000"),
            liquidity_quality_score=d("0.620000"),
            resolution_ambiguity_score=d("0.350000"),
        ),
        band_input(
            candidate_ref="candidate_gamma",
            market_ref="event_market_gamma",
            model_probability=d("0.520000"),
            model_confidence_score=d("0.300000"),
            market_probability=d("0.850000"),
            fee_probability_drag=d("0.030000"),
            spread_probability_drag=d("0.035000"),
            slippage_probability_drag=d("0.020000"),
            liquidity_quality_score=d("0.250000"),
            resolution_ambiguity_score=d("0.800000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyCostAdjustedProbabilityBandReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_model_confidence_score == d("0.633333")
    assert summary.mean_total_cost_drag_probability == d("0.044667")
    assert summary.mean_band_half_width_probability == d("0.139267")
    assert summary.mean_market_distance_from_band == d("0.050333")
    assert summary.mean_liquidity_quality_score == d("0.590000")
    assert summary.mean_resolution_ambiguity_score == d("0.416667")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "cost_adjusted_probability_band_report_block",
        "model_confidence_review",
        "cost_drag_review",
        "liquidity_quality_review",
        "resolution_ambiguity_review",
        "band_width_review",
        "market_probability_distance_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.candidate_ref for row in summary.rows) == (
        "candidate_gamma",
        "candidate_beta",
        "candidate_alpha",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyCostAdjustedProbabilityBandRow)
    assert blocked.total_cost_drag_probability == d("0.085000")
    assert blocked.cost_adjusted_midpoint_probability == d("0.435000")
    assert blocked.band_half_width_probability == d("0.264000")
    assert blocked.cost_adjusted_lower_probability == d("0.171000")
    assert blocked.cost_adjusted_upper_probability == d("0.699000")
    assert blocked.market_distance_from_band == d("0.151000")
    assert blocked.market_band_position == "above_band"
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "model_confidence_block",
        "cost_drag_block",
        "liquidity_quality_block",
        "resolution_ambiguity_block",
        "band_width_block",
        "market_probability_distance_block",
    )

    watched = summary.rows[1]
    assert watched.total_cost_drag_probability == d("0.040000")
    assert watched.cost_adjusted_midpoint_probability == d("0.540000")
    assert watched.band_half_width_probability == d("0.120800")
    assert watched.cost_adjusted_lower_probability == d("0.419200")
    assert watched.cost_adjusted_upper_probability == d("0.660800")
    assert watched.market_distance_from_band == d("0.000000")
    assert watched.market_band_position == "inside_band"
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "model_confidence_watch",
        "cost_drag_watch",
        "liquidity_quality_watch",
        "resolution_ambiguity_watch",
        "band_width_watch",
    )

    passed = summary.rows[2]
    assert passed.band_half_width_probability == d("0.033000")
    assert passed.market_distance_from_band == d("0.000000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("cost_adjusted_probability_band_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["band_width_watch"] == ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount(
        reason_code="band_width_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_redacted_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_cost_adjusted_probability_band_report_payload(
        report(band_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_cost_adjusted_probability_band_report_payload(
        report(band_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["market_probability"] == "0.620000"
    assert first_payload["rows"][0]["cost_adjusted_midpoint_probability"] == "0.631000"
    assert first_payload["rows"][0]["cost_adjusted_lower_probability"] == "0.598000"
    assert first_payload["rows"][0]["cost_adjusted_upper_probability"] == "0.664000"
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
        "candidate_ref",
        "market_ref",
        "candidate_alpha",
        "event_market_alpha",
        "market_slug",
        "question",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_cost_adjusted_probability_band_report_payload(
        report(band_input()),
    )
    tampered_payload["rows"][0]["band_half_width_probability"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_cost_adjusted_probability_band_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_cost_adjusted_probability_band_report_payload(
            {
                "market_ref": "event_market_alpha",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_bad_numerics_flags_times_and_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="model_probability"):
        band_input(model_probability=0.62)
    with pytest.raises(ValueError, match="fee_probability_drag"):
        band_input(fee_probability_drag=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="market_probability"):
        band_input(market_probability=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        band_input(observed_at=datetime(2026, 7, 8, 11, 40))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            band_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(band_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            band_input(candidate_ref="same_candidate"),
            band_input(candidate_ref="same_candidate", market_ref="event_market_beta"),
        )
    with pytest.raises(ValueError, match="model_confidence_pass_floor"):
        config(model_confidence_pass_floor=d("0.400000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(band_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_STATUSES == (
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
            band_half_width_probability=d("0.020000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        band_input(),
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
                "candidate_ref",
                "market_ref",
                "market_band_position",
                "status",
                "config_version",
                "derived_validation_digest",
                "observed_at",
                "generated_at",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "drag",
                    "floor",
                    "ceiling",
                    "probability",
                    "ratio",
                    "score",
                    "weight",
                    "width",
                    "distance",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_cost_adjusted_probability_band_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_COST_ADJUSTED_PROBABILITY_BAND_STATUSES",
        "ResearchStrategyCostAdjustedProbabilityBandConfig",
        "ResearchStrategyCostAdjustedProbabilityBandInput",
        "ResearchStrategyCostAdjustedProbabilityBandReasonCodeCount",
        "ResearchStrategyCostAdjustedProbabilityBandRow",
        "ResearchStrategyCostAdjustedProbabilityBandReport",
        "build_research_strategy_cost_adjusted_probability_band_report",
        "research_strategy_cost_adjusted_probability_band_report_payload",
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
