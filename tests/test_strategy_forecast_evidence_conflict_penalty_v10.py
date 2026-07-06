from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_forecast_evidence_conflict_penalty_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(
    forecast_id: str,
    source_id: str,
    source_family: str,
    probability: str,
    reliability: str,
    *,
    observed_at: datetime | None = None,
):
    module = api()
    return module.StrategyForecastEvidenceConflictEvidence(
        forecast_id=forecast_id,
        source_id=source_id,
        source_family=source_family,
        probability=d(probability),
        reliability=d(reliability),
        observed_at=observed_at or (GENERATED_AT - timedelta(hours=1)),
    )


def forecast(
    forecast_id: str,
    *,
    base_probability: str = "0.500000",
    resolution_at: datetime | None = None,
    evidence_rows=(),
):
    module = api()
    return module.StrategyForecastEvidenceConflictForecast(
        forecast_id=forecast_id,
        base_probability=d(base_probability),
        resolution_at=resolution_at or (GENERATED_AT + timedelta(days=3)),
        evidence=evidence_rows,
    )


def report(*forecasts, generated_at: datetime = GENERATED_AT, config=None):
    module = api()
    return module.build_strategy_forecast_evidence_conflict_penalty_v10(
        forecasts,
        config=config or module.StrategyForecastEvidenceConflictPenaltyConfig(),
        generated_at=generated_at,
    )


def risky_forecast():
    return forecast(
        "forecast-risky",
        base_probability="0.800000",
        resolution_at=GENERATED_AT + timedelta(hours=6),
        evidence_rows=(
            evidence(
                "forecast-risky",
                "model-a",
                "model",
                "0.200000",
                "0.900000",
                observed_at=GENERATED_AT - timedelta(hours=1),
            ),
            evidence(
                "forecast-risky",
                "model-b",
                "model",
                "0.250000",
                "0.300000",
                observed_at=GENERATED_AT - timedelta(hours=49),
            ),
            evidence(
                "forecast-risky",
                "research-a",
                "research",
                "0.790000",
                "0.700000",
                observed_at=GENERATED_AT - timedelta(hours=25),
            ),
        ),
    )


def test_penalty_scores_all_conflict_dimensions_and_adjusts_probability() -> None:
    penalty_report = report(risky_forecast())

    assert is_dataclass(penalty_report)
    assert penalty_report.generated_at == GENERATED_AT
    assert penalty_report.config_version == (
        "strategy-forecast-evidence-conflict-penalty-v10"
    )
    assert penalty_report.result_count == d("1")
    assert penalty_report.clear_result_count == d("0")
    assert penalty_report.watch_result_count == d("0")
    assert penalty_report.blocked_result_count == d("1")
    assert penalty_report.max_penalty_score == d("0.715834")
    assert penalty_report.mean_penalty_score == d("0.715834")
    assert penalty_report.status == "blocked"
    assert penalty_report.reason_codes == (
        "strategy_forecast_evidence_conflict_penalty_blocked",
        "contradiction_rate_present",
        "reliability_spread_high",
        "source_family_concentration_high",
        "recency_mismatch_high",
        "resolution_urgency_high",
        "penalty_applied",
    )
    assert penalty_report.paper_only is True
    assert penalty_report.report_only is True
    assert penalty_report.readonly is True
    assert len(penalty_report.validation_digest) == 64

    result = penalty_report.results[0]
    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "strategy-forecast-evidence-conflict-penalty-v10"
    )
    assert result.forecast.forecast_id == "forecast-risky"
    assert result.evidence_count == d("3")
    assert result.conflicting_evidence_count == d("2")
    assert result.contradiction_rate == d("0.666667")
    assert result.reliability_spread == d("0.600000")
    assert result.source_family_concentration == d("0.666667")
    assert result.recency_mismatch == d("1.000000")
    assert result.resolution_urgency == d("0.750000")
    assert result.penalty_score == d("0.715834")
    assert result.penalty_amount == d("0.214750")
    assert result.adjusted_probability == d("0.585250")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "contradiction_rate_present",
        "reliability_spread_high",
        "source_family_concentration_high",
        "recency_mismatch_high",
        "resolution_urgency_high",
    )
    assert len(result.validation_digest) == 64


def test_low_conflict_forecast_stays_clear_with_decimal_metrics() -> None:
    penalty_report = report(
        forecast(
            "forecast-clear",
            base_probability="0.520000",
            resolution_at=GENERATED_AT + timedelta(days=3),
            evidence_rows=(
                evidence(
                    "forecast-clear",
                    "model",
                    "model",
                    "0.510000",
                    "0.850000",
                    observed_at=GENERATED_AT - timedelta(hours=1),
                ),
                evidence(
                    "forecast-clear",
                    "research",
                    "research",
                    "0.530000",
                    "0.800000",
                    observed_at=GENERATED_AT - timedelta(hours=2),
                ),
                evidence(
                    "forecast-clear",
                    "team",
                    "team",
                    "0.520000",
                    "0.820000",
                    observed_at=GENERATED_AT - timedelta(minutes=90),
                ),
            ),
        ),
    )

    result = penalty_report.results[0]
    assert penalty_report.status == "clear"
    assert penalty_report.clear_result_count == d("1")
    assert penalty_report.reason_codes == (
        "strategy_forecast_evidence_conflict_penalty_clear",
        "penalty_applied",
    )
    assert result.status == "clear"
    assert result.contradiction_rate == d("0.000000")
    assert result.reliability_spread == d("0.050000")
    assert result.source_family_concentration == d("0.333333")
    assert result.recency_mismatch == d("0.020833")
    assert result.resolution_urgency == d("0.000000")
    assert result.penalty_score == d("0.063125")
    assert result.penalty_amount == d("0.001262")
    assert result.adjusted_probability == d("0.518738")
    assert result.reason_codes == ("evidence_conflict_penalty_clear",)


def test_empty_report_is_deterministic_readonly_and_report_only() -> None:
    penalty_report = report()

    assert penalty_report.result_count == d("0")
    assert penalty_report.clear_result_count == d("0")
    assert penalty_report.watch_result_count == d("0")
    assert penalty_report.blocked_result_count == d("0")
    assert penalty_report.max_penalty_score is None
    assert penalty_report.mean_penalty_score is None
    assert penalty_report.status == "clear"
    assert penalty_report.reason_codes == (
        "strategy_forecast_evidence_conflict_penalty_empty",
    )
    assert penalty_report.results == ()
    assert penalty_report.paper_only is True
    assert penalty_report.report_only is True
    assert penalty_report.readonly is True
    assert len(penalty_report.validation_digest) == 64


def test_validation_rejects_float_inputs_duplicates_timestamps_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="base_probability must be a Decimal"):
        module.StrategyForecastEvidenceConflictForecast(
            forecast_id="forecast-float",
            base_probability=0.5,
            resolution_at=GENERATED_AT + timedelta(days=1),
            evidence=(),
        )
    with pytest.raises(ValueError, match="reliability must be finite"):
        evidence(
            "forecast-nan",
            "source",
            "model",
            "0.500000",
            "0.700000",
        ).__class__(
            forecast_id="forecast-nan",
            source_id="source",
            source_family="model",
            probability=d("0.500000"),
            reliability=Decimal("NaN"),
            observed_at=GENERATED_AT - timedelta(hours=1),
        )
    with pytest.raises(ValueError, match="duplicate source_id"):
        forecast(
            "forecast-dupe",
            evidence_rows=(
                evidence("forecast-dupe", "source", "model", "0.500000", "0.700000"),
                evidence("forecast-dupe", "source", "team", "0.510000", "0.800000"),
            ),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            forecast(
                "forecast-future-source",
                evidence_rows=(
                    evidence(
                        "forecast-future-source",
                        "source",
                        "model",
                        "0.500000",
                        "0.700000",
                        observed_at=GENERATED_AT + timedelta(seconds=1),
                    ),
                ),
            ),
        )
    with pytest.raises(ValueError, match="resolution_at must not be before generated_at"):
        report(
            forecast(
                "forecast-past-resolution",
                resolution_at=GENERATED_AT - timedelta(seconds=1),
                evidence_rows=(
                    evidence(
                        "forecast-past-resolution",
                        "source",
                        "model",
                        "0.500000",
                        "0.700000",
                    ),
                ),
            ),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(
            evidence("forecast-flags", "source", "model", "0.500000", "0.700000"),
            readonly=False,
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyForecastEvidenceConflictPenaltyConfig(paper_only=False)


def test_frozen_dataclasses_and_tamper_evident_validation_recompute_fields() -> None:
    penalty_report = report(risky_forecast())
    result = penalty_report.results[0]

    with pytest.raises(FrozenInstanceError):
        result.status = "clear"  # type: ignore[misc]
    with pytest.raises(ValueError, match="penalty_score must match"):
        replace(result, penalty_score=d("0.000000"))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="result_count must match results"):
        replace(penalty_report, result_count=d("2"))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(penalty_report, validation_digest="0" * 64)


def test_report_data_serializes_decimal_strings_and_module_has_no_live_surfaces() -> None:
    module = api()
    penalty_report = report(risky_forecast())

    data = module.strategy_forecast_evidence_conflict_penalty_report_data(
        penalty_report,
    )
    encoded = json.dumps(data, sort_keys=True)

    assert data["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert data["result_count"] == "1"
    assert data["results"][0]["penalty_score"] == "0.715834"
    assert data["results"][0]["adjusted_probability"] == "0.585250"
    assert '"0.715834"' in encoded
    assert all(type(value) is not float for value in walk(data))

    with pytest.raises(ValueError, match="readonly must be True"):
        module.strategy_forecast_evidence_conflict_penalty_report_data(
            {"paper_only": True, "report_only": True},
        )
    with pytest.raises(ValueError, match="unsafe surface field"):
        module.strategy_forecast_evidence_conflict_penalty_report_data(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet": "blocked",
            },
        )

    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "network",
        "database",
        "open(",
        "requests",
        "socket",
        "psycopg",
        "sql",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)
    else:
        yield value
