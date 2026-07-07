from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_uncertainty_band_score"


class _DecimalSubclass(Decimal):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing uncertainty band score module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_UNCERTAINTY_BAND_SCORE_CONFIG_VERSION
        ),
        "min_pass_midpoint_net_edge": d("0.030000"),
        "min_watch_midpoint_net_edge": d("0.010000"),
        "min_pass_lower_bound_net_edge": d("0.005000"),
        "max_pass_band_width": d("0.080000"),
        "max_watch_band_width": d("0.180000"),
        "max_pass_uncertainty_to_edge_ratio": d("1.000000"),
        "max_watch_uncertainty_to_edge_ratio": d("3.000000"),
        "min_pass_evidence_quality": d("0.750000"),
        "min_watch_evidence_quality": d("0.400000"),
        "min_pass_band_score": d("0.750000"),
        "min_watch_band_score": d("0.250000"),
    }
    values.update(overrides)
    return module.CandidateDecisionUncertaintyBandScoreConfig(**values)


def band_input(**overrides: object):
    module = api()
    values = {
        "forecast_midpoint": d("0.620000"),
        "forecast_lower_bound": d("0.600000"),
        "forecast_upper_bound": d("0.640000"),
        "market_probability": d("0.560000"),
        "estimated_cost_drag": d("0.010000"),
        "evidence_quality": d("0.850000"),
    }
    values.update(overrides)
    return module.CandidateDecisionUncertaintyBandScoreInput(**values)


def score(subject: object | None = None, *, cfg=None):
    module = api()
    return module.score_candidate_decision_uncertainty_band(
        band_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_int_or_decimal_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected raw Decimal value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_int_or_decimal_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_int_or_decimal_values(item)


def test_confident_band_passes_when_lower_bound_preserves_cost_adjusted_edge() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionUncertaintyBandScoreResult(
        config_version="candidate-decision-uncertainty-band-score-v0",
        forecast_midpoint=d("0.620000"),
        forecast_lower_bound=d("0.600000"),
        forecast_upper_bound=d("0.640000"),
        market_probability=d("0.560000"),
        estimated_cost_drag=d("0.010000"),
        evidence_quality=d("0.850000"),
        gross_midpoint_edge=d("0.060000"),
        net_midpoint_edge=d("0.050000"),
        lower_bound_net_edge=d("0.030000"),
        upper_bound_net_edge=d("0.070000"),
        uncertainty_band_width=d("0.040000"),
        uncertainty_to_edge_ratio=d("0.800000"),
        uncertainty_band_score=d("0.850000"),
        status="pass",
        reason_codes=(
            "candidate_decision_uncertainty_band_score",
            "status_pass",
            "midpoint_net_edge_pass",
            "lower_bound_net_edge_pass",
            "uncertainty_band_width_pass",
            "uncertainty_to_edge_ratio_pass",
            "evidence_quality_pass",
            "uncertainty_band_score_pass",
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload == module.candidate_decision_uncertainty_band_score_payload(result)


def test_band_watch_when_midpoint_edge_survives_but_lower_bound_does_not() -> None:
    result = score(
        band_input(
            forecast_lower_bound=d("0.530000"),
            forecast_upper_bound=d("0.630000"),
            evidence_quality=d("0.700000"),
        ),
    )

    assert result.net_midpoint_edge == d("0.050000")
    assert result.lower_bound_net_edge == d("-0.040000")
    assert result.upper_bound_net_edge == d("0.060000")
    assert result.uncertainty_band_width == d("0.100000")
    assert result.uncertainty_to_edge_ratio == d("2.000000")
    assert result.uncertainty_band_score == d("0.350000")
    assert result.status == "watch"
    assert result.reason_codes == (
        "candidate_decision_uncertainty_band_score",
        "status_watch",
        "midpoint_net_edge_pass",
        "lower_bound_net_edge_nonpositive",
        "uncertainty_band_width_watch",
        "uncertainty_to_edge_ratio_watch",
        "evidence_quality_watch",
        "uncertainty_band_score_watch",
    )


def test_band_blocks_when_uncertainty_overwhelms_apparent_edge() -> None:
    result = score(
        band_input(
            forecast_midpoint=d("0.600000"),
            forecast_lower_bound=d("0.350000"),
            forecast_upper_bound=d("0.850000"),
            market_probability=d("0.560000"),
            estimated_cost_drag=d("0.015000"),
            evidence_quality=d("0.800000"),
        ),
    )

    assert result.gross_midpoint_edge == d("0.040000")
    assert result.net_midpoint_edge == d("0.025000")
    assert result.lower_bound_net_edge == d("-0.225000")
    assert result.uncertainty_band_width == d("0.500000")
    assert result.uncertainty_to_edge_ratio == d("20.000000")
    assert result.uncertainty_band_score == d("0.040000")
    assert result.status == "block"
    assert result.reason_codes == (
        "candidate_decision_uncertainty_band_score",
        "status_block",
        "midpoint_net_edge_watch",
        "lower_bound_net_edge_nonpositive",
        "uncertainty_band_width_block",
        "uncertainty_to_edge_ratio_block",
        "evidence_quality_pass",
        "uncertainty_band_score_block",
    )


def test_negative_or_low_quality_midpoint_edge_blocks_without_execution_language() -> None:
    no_edge = score(
        band_input(
            forecast_midpoint=d("0.550000"),
            forecast_lower_bound=d("0.500000"),
            forecast_upper_bound=d("0.600000"),
            evidence_quality=d("0.900000"),
        ),
    )
    weak_evidence = score(band_input(evidence_quality=d("0.300000")))

    assert no_edge.net_midpoint_edge == d("-0.020000")
    assert no_edge.status == "block"
    assert "midpoint_net_edge_block" in no_edge.reason_codes
    assert weak_evidence.status == "block"
    assert "evidence_quality_block" in weak_evidence.reason_codes

    rendered = json.dumps(no_edge.payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in ("buy", "sell", "recommendation", "position_size"):
        assert forbidden not in rendered


def test_payload_uses_decimal_strings_and_exposes_no_raw_identifiers_or_sources() -> None:
    module = api()
    payload = score().payload
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["config_version"] == "candidate-decision-uncertainty-band-score-v0"
    assert payload["forecast_midpoint"] == "0.620000"
    assert payload["forecast_lower_bound"] == "0.600000"
    assert payload["forecast_upper_bound"] == "0.640000"
    assert payload["market_probability"] == "0.560000"
    assert payload["estimated_cost_drag"] == "0.010000"
    assert payload["uncertainty_band_score"] == "0.850000"
    assert payload["reason_codes"] == [
        "candidate_decision_uncertainty_band_score",
        "status_pass",
        "midpoint_net_edge_pass",
        "lower_bound_net_edge_pass",
        "uncertainty_band_width_pass",
        "uncertainty_to_edge_ratio_pass",
        "evidence_quality_pass",
        "uncertainty_band_score_pass",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_int_or_decimal_values(payload)

    forbidden_payload_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "dsn",
        "table_name",
        "position_size",
        "private_key",
    )
    for fragment in forbidden_payload_fragments:
        assert fragment not in payload
        assert fragment not in rendered

    assert module.validate_candidate_decision_uncertainty_band_score_public_payload(payload)


def test_public_payload_validator_rejects_identifier_source_storage_and_execution_surfaces() -> None:
    module = api()
    payload = score().payload
    unsafe_payloads = (
        ({"candidate_id": "candidate-123"}, "unsafe public payload field"),
        ({"market_id": "market-123"}, "unsafe public payload field"),
        ({"market_slug": "will-event-resolve"}, "unsafe public payload field"),
        ({"market_question": "Will this event resolve yes?"}, "unsafe public payload field"),
        ({"source_ref": "source-123"}, "unsafe public payload field"),
        ({"source_url": "https://example.test/source"}, "unsafe public payload field"),
        ({"source_text": "raw source text"}, "unsafe public payload field"),
        ({"dsn": "postgresql://example.test/db"}, "unsafe public payload field"),
        ({"table_name": "candidate_scores"}, "unsafe public payload field"),
        ({"position_size": "10.000000"}, "unsafe public payload field"),
        ({"private_key": "redacted"}, "unsafe live surface field"),
        ({"diagnostic_count": 1}, "numeric public payload values"),
        ({"diagnostic_values": (1,)}, "numeric public payload values"),
        ({"status_note": "buy"}, "unsafe public payload value"),
        ({"status_note": "sell"}, "unsafe public payload value"),
        ({"status_note": "recommendation"}, "unsafe public payload value"),
        ({"status_note": "trade"}, "unsafe public payload value"),
    )

    for extra_payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_uncertainty_band_score_public_payload(
                {**payload, **extra_payload},
            )


def test_dataclasses_are_frozen_exact_decimal_only_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    subject = band_input()
    result = score(subject, cfg=cfg)

    for klass in (
        module.CandidateDecisionUncertaintyBandScoreConfig,
        module.CandidateDecisionUncertaintyBandScoreInput,
        module.CandidateDecisionUncertaintyBandScoreResult,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        subject.forecast_midpoint = d("0.500000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    for instance in (cfg, subject, result):
        for item in fields(instance):
            value = getattr(instance, item.name)
            if item.name in {
                "config_version",
                "status",
                "reason_codes",
                "paper_only",
                "report_only",
                "readonly",
            }:
                continue
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="forecast_midpoint must be a Decimal"):
        band_input(forecast_midpoint=0.62)
    with pytest.raises(ValueError, match="forecast_midpoint must be an exact Decimal"):
        band_input(forecast_midpoint=_DecimalSubclass("0.620000"))
    with pytest.raises(ValueError, match="forecast_lower_bound must be between 0 and 1"):
        band_input(forecast_lower_bound=d("-0.000001"))
    with pytest.raises(ValueError, match="forecast_lower_bound must not exceed midpoint"):
        band_input(forecast_lower_bound=d("0.630000"))
    with pytest.raises(ValueError, match="forecast_upper_bound must be at least midpoint"):
        band_input(forecast_upper_bound=d("0.610000"))
    with pytest.raises(ValueError, match="estimated_cost_drag must be between 0 and 1"):
        band_input(estimated_cost_drag=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        band_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.CandidateDecisionUncertaintyBandScoreConfig(
            **{**public_values(cfg), "readonly": False},
        )
    with pytest.raises(ValueError, match="input_value"):
        score(object())
    with pytest.raises(ValueError, match="config"):
        score(subject, cfg=object())


def test_config_thresholds_and_result_consistency_are_validated() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="min_watch_midpoint_net_edge"):
        config(min_watch_midpoint_net_edge=d("0.040000"))
    with pytest.raises(ValueError, match="max_pass_band_width"):
        config(max_pass_band_width=d("0.190000"))
    with pytest.raises(ValueError, match="max_pass_uncertainty_to_edge_ratio"):
        config(max_pass_uncertainty_to_edge_ratio=d("3.500000"))
    with pytest.raises(ValueError, match="min_watch_evidence_quality"):
        config(min_watch_evidence_quality=d("0.800000"))
    with pytest.raises(ValueError, match="min_watch_band_score"):
        config(min_watch_band_score=d("0.800000"))

    rebuilt = module.CandidateDecisionUncertaintyBandScoreResult(
        **public_values(result),
    )
    assert rebuilt == result
    with pytest.raises(ValueError, match="net_midpoint_edge"):
        replace(result, net_midpoint_edge=d("0.040000"))
    with pytest.raises(ValueError, match="uncertainty_band_score"):
        replace(result, uncertainty_band_score=d("0.750000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("candidate_decision_uncertainty_band_score",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)


def test_result_rejects_inconsistent_or_unknown_reason_classifications() -> None:
    result = score()

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            result,
            status="watch",
            reason_codes=(
                "candidate_decision_uncertainty_band_score",
                "status_watch",
                "midpoint_net_edge_pass",
                "lower_bound_net_edge_pass",
                "uncertainty_band_width_pass",
                "uncertainty_to_edge_ratio_pass",
                "evidence_quality_pass",
                "uncertainty_band_score_pass",
            ),
        )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            result,
            reason_codes=(
                "candidate_decision_uncertainty_band_score",
                "status_pass",
                "midpoint_net_edge_pass",
                "lower_bound_net_edge_pass",
                "uncertainty_band_width_pass",
                "uncertainty_to_edge_ratio_pass",
                "evidence_quality_pass",
                "source_text_pass",
            ),
        )


def test_module_has_phase_one_boundary_no_io_or_live_surface_and_no_float_literals() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    banned_import_roots = {
        "asyncio",
        "csv",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    assert not (set(imported_modules) & banned_import_roots)
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "private_key",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "dsn",
        "table_name",
        "position_size",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "open(",
        "path(",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "replace",
        "exchange",
    ):
        assert forbidden not in lowered

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_UNCERTAINTY_BAND_SCORE_CONFIG_VERSION",
        "UNCERTAINTY_BAND_STATUSES",
        "CandidateDecisionUncertaintyBandScoreConfig",
        "CandidateDecisionUncertaintyBandScoreInput",
        "CandidateDecisionUncertaintyBandScoreResult",
        "score_candidate_decision_uncertainty_band",
        "candidate_decision_uncertainty_band_score_payload",
        "validate_candidate_decision_uncertainty_band_score_public_payload",
    )
