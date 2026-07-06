from __future__ import annotations

from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from importlib import import_module

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.strategy_probability_forecast_revision_reasoner_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def revision_input(**overrides: object):
    module = api()
    values = {
        "market_id": "market-123",
        "previous_probability": d("0.420000"),
        "new_probability": d("0.540000"),
        "source_update_count": d("3"),
        "market_move_bps": d("180.000000"),
        "model_disagreement_score": d("0.350000"),
        "source_freshness_status": "fresh",
        "resolution_risk_tier": "medium",
    }
    values.update(overrides)
    return module.StrategyProbabilityForecastRevisionReasonerV10Input(**values)


def report(**overrides: object):
    module = api()
    return module.build_strategy_probability_forecast_revision_reasoner_v10(
        revision_input(**overrides),
    )


def test_material_fresh_update_explains_required_upward_revision_and_payload() -> None:
    module = api()
    result = report()

    assert type(result) is module.StrategyProbabilityForecastRevisionReasonerV10Report
    assert is_dataclass(result)
    assert result.revision_status == "revision_required"
    assert result.revision_delta_bps == d("1200.000000")
    assert result.reason_codes == (
        "probability_delta_material",
        "source_updates_available",
        "market_move_material",
        "model_disagreement_high",
        "fresh_sources",
        "resolution_risk_medium",
        "revision_required",
    )
    assert result.revision_reasons == (
        "Probability forecast changed by +1200.000000 bps.",
        "3 source updates support reassessment.",
        "Market price moved 180.000000 bps.",
        "Model disagreement score 0.350000 exceeds review threshold.",
        "Fresh source context supports revision.",
        "Resolution risk is medium; revise with caution.",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    assert payload["market_id"] == "market-123"
    assert payload["previous_probability"] == "0.420000"
    assert payload["new_probability"] == "0.540000"
    assert payload["source_update_count"] == "3"
    assert payload["revision_status"] == "revision_required"
    assert payload["revision_delta_bps"] == "1200.000000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["revision_reasons"] == list(result.revision_reasons)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    payload_text = repr(payload).lower()
    for forbidden in ("wallet", "account", "order", "auth", "private_key", "trade"):
        assert forbidden not in payload_text


def test_stale_high_risk_material_revision_is_watch_not_required() -> None:
    result = report(
        previous_probability=d("0.620000"),
        new_probability=d("0.570000"),
        source_update_count=d("2"),
        market_move_bps=d("-220.000000"),
        model_disagreement_score=d("0.210000"),
        source_freshness_status="stale",
        resolution_risk_tier="high",
    )

    assert result.revision_status == "revision_watch"
    assert result.revision_delta_bps == d("-500.000000")
    assert result.reason_codes == (
        "probability_delta_material",
        "source_updates_available",
        "market_move_material",
        "model_disagreement_high",
        "source_stale",
        "resolution_risk_high",
        "revision_watch",
    )
    assert result.revision_reasons[-2:] == (
        "Source context is stale; refresh evidence before a required revision.",
        "Resolution risk is high; keep the revision on watch.",
    )


def test_low_signal_fresh_low_risk_reports_no_revision_needed() -> None:
    result = report(
        previous_probability=d("0.500000"),
        new_probability=d("0.505000"),
        source_update_count=d("0"),
        market_move_bps=d("20.000000"),
        model_disagreement_score=d("0.050000"),
        source_freshness_status="fresh",
        resolution_risk_tier="low",
    )

    assert result.revision_status == "no_revision_needed"
    assert result.revision_delta_bps == d("50.000000")
    assert result.reason_codes == (
        "probability_delta_immaterial",
        "no_source_updates",
        "market_move_immaterial",
        "model_disagreement_low",
        "fresh_sources",
        "resolution_risk_low",
        "no_revision_needed",
    )
    assert result.revision_reasons == (
        "Probability forecast changed by +50.000000 bps, below material threshold.",
        "No source updates supplied.",
        "Market price move is below material threshold.",
        "Model disagreement score is below review threshold.",
        "Fresh source context supports no revision.",
        "Resolution risk is low.",
    )


def test_blocked_resolution_risk_blocks_even_with_large_revision_signal() -> None:
    result = report(
        previous_probability=d("0.200000"),
        new_probability=d("0.700000"),
        source_update_count=d("4"),
        market_move_bps=d("500.000000"),
        model_disagreement_score=d("0.900000"),
        resolution_risk_tier="blocked",
    )

    assert result.revision_status == "revision_blocked"
    assert result.revision_delta_bps == d("5000.000000")
    assert result.reason_codes[-2:] == (
        "resolution_risk_blocked",
        "revision_blocked",
    )
    assert result.revision_reasons[-1] == (
        "Resolution risk is blocked; do not treat the forecast change as actionable."
    )


def test_dataclasses_are_frozen_strict_decimal_only_and_hard_flagged() -> None:
    module = api()
    result = report()

    assert module.__all__ == (
        "DEFAULT_STRATEGY_PROBABILITY_FORECAST_REVISION_REASONER_V10_CONFIG_VERSION",
        "StrategyProbabilityForecastRevisionReasonerV10Config",
        "StrategyProbabilityForecastRevisionReasonerV10Input",
        "StrategyProbabilityForecastRevisionReasonerV10Report",
        "build_strategy_probability_forecast_revision_reasoner_v10",
        "strategy_probability_forecast_revision_reasoner_v10_payload",
    )

    with pytest.raises(FrozenInstanceError):
        result.revision_status = "revision_watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        revision_input(previous_probability=0.42)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        revision_input(new_probability=_DecimalSubclass("0.540000"))
    with pytest.raises(ValueError, match="source_freshness_status"):
        revision_input(source_freshness_status="old")
    with pytest.raises(ValueError, match="resolution_risk_tier"):
        revision_input(resolution_risk_tier="urgent")
    with pytest.raises(ValueError, match="paper_only"):
        replace(revision_input(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
