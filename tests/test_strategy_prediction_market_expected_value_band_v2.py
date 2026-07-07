from __future__ import annotations

import json
import re
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_prediction_market_expected_value_band_v2 import (
    StrategyPredictionMarketExpectedValueBandV2Candidate,
    StrategyPredictionMarketExpectedValueBandV2Config,
    StrategyPredictionMarketExpectedValueBandV2Report,
    build_strategy_prediction_market_expected_value_band_v2_report,
    strategy_prediction_market_expected_value_band_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    candidate_id: str,
    *,
    market_id: str | None = None,
    event_slug: str | None = None,
    category: str = "macro",
    model_probability: Decimal = d("0.580000"),
    market_probability: Decimal = d("0.500000"),
    limit_price: Decimal = d("0.500000"),
    notional_usdc: Decimal = d("100.000000"),
    total_cost_rate: Decimal = d("0.010000"),
) -> StrategyPredictionMarketExpectedValueBandV2Candidate:
    return StrategyPredictionMarketExpectedValueBandV2Candidate(
        candidate_id=candidate_id,
        market_id=market_id or f"market_{candidate_id}",
        event_slug=event_slug or f"event-{candidate_id}",
        category=category,
        model_probability=model_probability,
        market_probability=market_probability,
        limit_price=limit_price,
        notional_usdc=notional_usdc,
        total_cost_rate=total_cost_rate,
    )


def report(
    *candidates: StrategyPredictionMarketExpectedValueBandV2Candidate,
    config: StrategyPredictionMarketExpectedValueBandV2Config | None = None,
) -> StrategyPredictionMarketExpectedValueBandV2Report:
    return build_strategy_prediction_market_expected_value_band_v2_report(
        candidates,
        config=config or StrategyPredictionMarketExpectedValueBandV2Config(),
        generated_at=GENERATED_AT,
    )


def test_bands_candidates_by_expected_value_after_costs_with_deterministic_rollups() -> None:
    digest = report(
        candidate(
            "candidate-low",
            model_probability=d("0.510000"),
            market_probability=d("0.500000"),
            limit_price=d("0.500000"),
            notional_usdc=d("50.000000"),
            total_cost_rate=d("0.000000"),
        ),
        candidate(
            "candidate-negative",
            model_probability=d("0.475000"),
            market_probability=d("0.500000"),
            limit_price=d("0.500000"),
            notional_usdc=d("100.000000"),
            total_cost_rate=d("0.005000"),
        ),
        candidate(
            "candidate-medium",
            model_probability=d("0.545000"),
            market_probability=d("0.500000"),
            limit_price=d("0.500000"),
            notional_usdc=d("200.000000"),
            total_cost_rate=d("0.010000"),
        ),
        candidate(
            "candidate-high",
            model_probability=d("0.620000"),
            market_probability=d("0.500000"),
            limit_price=d("0.500000"),
            notional_usdc=d("100.000000"),
            total_cost_rate=d("0.010000"),
        ),
    )

    assert digest.report_status == "block"
    assert digest.candidate_count == d("4.000000")
    assert digest.high_count == d("1.000000")
    assert digest.medium_count == d("1.000000")
    assert digest.low_count == d("1.000000")
    assert digest.negative_count == d("1.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("2.000000")
    assert digest.block_count == d("1.000000")
    assert digest.total_net_expected_value_usdc == d("15.500000")
    assert digest.max_net_expected_value_usdc == d("11.000000")
    assert re.fullmatch(r"[0-9a-f]{64}", digest.derived_validation_digest)

    assert tuple(row.candidate_id for row in digest.rows) == (
        "candidate-high",
        "candidate-medium",
        "candidate-low",
        "candidate-negative",
    )

    high, medium, low, negative = digest.rows
    assert high.gross_edge == d("0.120000")
    assert high.expected_value_usdc == d("12.000000")
    assert high.cost_usdc == d("1.000000")
    assert high.net_expected_value_usdc == d("11.000000")
    assert high.ev_band == "high"
    assert high.status == "pass"
    assert high.reason_codes == ("ev_band_high",)

    assert medium.net_expected_value_usdc == d("7.000000")
    assert medium.ev_band == "medium"
    assert medium.status == "watch"
    assert medium.reason_codes == ("ev_band_medium",)

    assert low.net_expected_value_usdc == d("0.500000")
    assert low.ev_band == "low"
    assert low.status == "watch"
    assert low.reason_codes == ("ev_band_low",)

    assert negative.net_expected_value_usdc == d("-3.000000")
    assert negative.ev_band == "negative"
    assert negative.status == "block"
    assert negative.reason_codes == ("ev_band_negative",)

    assert tuple((item.reason_code, item.count) for item in digest.reason_code_counts) == (
        ("ev_band_high", d("1.000000")),
        ("ev_band_low", d("1.000000")),
        ("ev_band_medium", d("1.000000")),
        ("ev_band_negative", d("1.000000")),
    )


def test_empty_input_returns_empty_status_and_zero_decimals() -> None:
    digest = report()

    assert digest.report_status == "empty"
    assert digest.rows == ()
    assert digest.reason_code_counts == ()
    assert digest.candidate_count == ZERO
    assert digest.high_count == ZERO
    assert digest.medium_count == ZERO
    assert digest.low_count == ZERO
    assert digest.negative_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.block_count == ZERO
    assert digest.total_net_expected_value_usdc == ZERO
    assert digest.max_net_expected_value_usdc == ZERO
    assert re.fullmatch(r"[0-9a-f]{64}", digest.derived_validation_digest)


def test_expected_value_uses_limit_price_as_execution_price() -> None:
    digest = report(
        candidate(
            "candidate-limit",
            model_probability=d("0.580000"),
            market_probability=d("0.520000"),
            limit_price=d("0.550000"),
            notional_usdc=d("100.000000"),
            total_cost_rate=d("0.010000"),
        ),
    )

    row = digest.rows[0]
    assert row.gross_edge == d("0.030000")
    assert row.expected_value_usdc == d("3.000000")
    assert row.cost_usdc == d("1.000000")
    assert row.net_expected_value_usdc == d("2.000000")
    assert row.ev_band == "low"
    assert row.status == "watch"


def test_payload_is_safe_json_without_float_or_live_surface_fields() -> None:
    digest = report(candidate("candidate-alpha"))

    payload = strategy_prediction_market_expected_value_band_v2_payload(digest)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["model_probability"] == "0.580000"
    assert payload["rows"][0]["net_expected_value_usdc"] == "7.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["rows"][0]["derived_validation_digest"] == digest.rows[0].derived_validation_digest
    json.dumps(payload, sort_keys=True)
    assert not any(type(value) is Decimal for value in walk_payload_values(payload))
    assert not any(type(value) is float for value in walk_payload_values(payload))


def test_frozen_decimal_only_inputs_and_digest_validation_reject_tampering() -> None:
    digest = report(candidate("candidate-alpha"))

    with pytest.raises(FrozenInstanceError):
        digest.rows[0].candidate_id = "candidate-other"  # type: ignore[misc]

    with pytest.raises(ValueError, match="total_cost_rate must be a Decimal"):
        candidate("candidate-bad-decimal", total_cost_rate=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(digest, paper_only=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest.rows[0], derived_validation_digest="0" * 64)

    object.__setattr__(digest.rows[0], "candidate_id", "candidate-tampered")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_prediction_market_expected_value_band_v2_payload(digest)


def walk_payload_values(value: Any) -> tuple[object, ...]:
    if type(value) is dict:
        return tuple(item for child in value.values() for item in walk_payload_values(child))
    if type(value) is list:
        return tuple(item for child in value for item in walk_payload_values(child))
    return (value,)
