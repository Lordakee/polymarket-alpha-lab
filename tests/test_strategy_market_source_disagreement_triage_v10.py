from __future__ import annotations
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from decimal import Decimal

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_market_source_disagreement_triage_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def triage_input(
    *,
    official: str = "0.520000",
    primary: str = "0.530000",
    secondary: str = "0.510000",
    market: str = "0.515000",
    reliability: str = "0.800000",
    minutes: str = "1440.000000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.StrategyMarketSourceDisagreementTriageV10Input(
        official_source_probability=d(official),
        primary_source_probability=d(primary),
        secondary_source_probability=d(secondary),
        market_price_probability=d(market),
        source_reliability_weight=d(reliability),
        time_to_resolution_minutes=d(minutes),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def evaluate(**overrides):
    module = api()
    return module.evaluate_strategy_market_source_disagreement_triage_v10(
        triage_input(**overrides),
    )


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_aligned_sources_keep_report_signal_and_zero_penalty():
    result = evaluate()

    assert is_dataclass(result)
    assert result.disagreement_status == "aligned"
    assert result.triage_action == "keep_report_signal"
    assert result.confidence_penalty == d("0.000000")
    assert result.reason_codes == ("market_sources_aligned",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_watch_disagreement_queues_source_recheck_with_decimal_penalty():
    result = evaluate(
        official="0.620000",
        primary="0.500000",
        secondary="0.550000",
        market="0.560000",
        reliability="0.900000",
        minutes="720.000000",
    )

    assert result.disagreement_status == "watch"
    assert result.triage_action == "queue_source_recheck"
    assert result.confidence_penalty == d("0.076800")
    assert result.reason_codes == (
        "market_source_disagreement_watch",
        "source_spread_watch",
    )


def test_divergent_official_market_gap_escalates_manual_review_near_resolution():
    result = evaluate(
        official="0.700000",
        primary="0.550000",
        secondary="0.520000",
        market="0.500000",
        reliability="0.750000",
        minutes="180.000000",
    )

    assert result.disagreement_status == "divergent"
    assert result.triage_action == "escalate_source_review"
    assert result.confidence_penalty == d("0.154000")
    assert result.reason_codes == (
        "market_source_disagreement_divergent",
        "official_market_gap_divergent",
        "resolution_near",
    )


def test_critical_source_split_quarantines_signal_without_trade_advice():
    result = evaluate(
        official="0.900000",
        primary="0.200000",
        secondary="0.250000",
        market="0.300000",
        reliability="0.500000",
        minutes="45.000000",
    )

    assert result.disagreement_status == "critical"
    assert result.triage_action == "quarantine_probability_signal"
    assert result.confidence_penalty == d("0.700000")
    assert result.reason_codes == (
        "market_source_disagreement_critical",
        "source_spread_critical",
        "official_market_gap_critical",
        "market_source_mean_gap_watch",
        "source_reliability_low",
        "resolution_imminent",
    )


def test_payload_serializes_decimal_strings_and_contains_no_floats():
    module = api()
    result = evaluate(
        official="0.620000",
        primary="0.500000",
        secondary="0.550000",
        market="0.560000",
        reliability="0.900000",
        minutes="720.000000",
    )

    payload = module.strategy_market_source_disagreement_triage_v10_payload(result)
    encoded = json.dumps(payload, sort_keys=True)

    assert result.payload == payload
    assert payload["official_source_probability"] == "0.620000"
    assert payload["source_spread"] == "0.120000"
    assert payload["confidence_penalty"] == "0.076800"
    assert payload["reason_codes"] == [
        "market_source_disagreement_watch",
        "source_spread_watch",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"0.076800"' in encoded
    assert all(type(value) is not float for value in _walk(payload))


def test_validation_rejects_non_decimal_precision_nonfinite_and_unsafe_flags():
    module = api()

    with pytest.raises(ValueError, match="official_source_probability must be a Decimal"):
        module.StrategyMarketSourceDisagreementTriageV10Input(
            official_source_probability=0.5,
            primary_source_probability=d("0.500000"),
            secondary_source_probability=d("0.500000"),
            market_price_probability=d("0.500000"),
            source_reliability_weight=d("0.800000"),
            time_to_resolution_minutes=d("60.000000"),
        )

    with pytest.raises(ValueError, match="primary_source_probability must use"):
        triage_input(primary="0.5000001")

    with pytest.raises(ValueError, match="market_price_probability must be finite"):
        triage_input(market="NaN")

    with pytest.raises(ValueError, match="source_reliability_weight must be between 0 and 1"):
        triage_input(reliability="1.000001")

    with pytest.raises(ValueError, match="time_to_resolution_minutes must be nonnegative"):
        triage_input(minutes="-1.000000")

    with pytest.raises(ValueError, match="paper_only must be True"):
        triage_input(paper_only=False)

    result = evaluate()
    with pytest.raises(FrozenInstanceError):
        result.disagreement_status = "critical"  # type: ignore[misc]


def test_public_surface_stays_readonly_and_avoids_live_trading_terms():
    module = api()
    source = module.__loader__.get_source(module.__name__)

    assert source is not None
    lowered = source.lower()
    assert "requests." not in lowered
    assert "sqlite" not in lowered
    assert "open(" not in lowered
    for forbidden in (
        "place_order",
        "wallet",
        "private_key",
        "signing",
        "auth_token",
    ):
        assert forbidden not in lowered
