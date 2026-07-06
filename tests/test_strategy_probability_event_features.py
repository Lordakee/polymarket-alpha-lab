from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.strategy_probability_event_features import (
    PROBABILITY_EVENT_MARKET_MODEL_KIND,
    StrategyProbabilityEventFeatures,
    extract_strategy_probability_event_features,
    strategy_probability_event_features_payload,
)


def test_extracts_binary_threshold_probability_event_features() -> None:
    features = extract_strategy_probability_event_features(
        question="Will the Fed cut interest rates by at least 25 bps at the March FOMC meeting?",
        category="Economics",
        tags=("Fed", "Macro", "Interest Rates"),
        end_date=datetime(2026, 3, 18, 18, tzinfo=UTC),
        probabilities=(Decimal("0.610000"), Decimal("0.390000")),
        as_of=datetime(2026, 3, 15, 18, tzinfo=UTC),
    )

    assert features.model_kind == PROBABILITY_EVENT_MARKET_MODEL_KIND
    assert features.price_asset_model is False
    assert features.event_type == "macro_policy"
    assert features.time_to_resolution_hours == Decimal("72.000000")
    assert features.probability_count == Decimal("2")
    assert features.normalized_probabilities == (Decimal("0.610000"), Decimal("0.390000"))
    assert features.implied_probability_sum == Decimal("1.000000")
    assert features.binary_outcome_hint is True
    assert features.threshold_hint is True
    assert features.threshold_terms == ("25 bps",)
    assert features.multi_outcome_hint is False
    assert features.ambiguous_resolution_flags == ()
    assert features.paper_only is True
    assert features.report_only is True
    assert features.readonly is True


def test_extracts_multi_outcome_sports_probability_event_features() -> None:
    features = extract_strategy_probability_event_features(
        question="Who will win the NBA Finals: Celtics, Nuggets, Knicks, or Lakers?",
        category="Sports",
        tags=("NBA", "Basketball", "championship"),
        end_date=datetime(2026, 6, 20, 4, tzinfo=UTC),
        probabilities=(
            Decimal("0.320000"),
            Decimal("0.280000"),
            Decimal("0.210000"),
            Decimal("0.190000"),
        ),
        as_of=datetime(2026, 6, 16, 4, tzinfo=UTC),
    )

    assert features.event_type == "sports"
    assert features.time_to_resolution_hours == Decimal("96.000000")
    assert features.binary_outcome_hint is False
    assert features.multi_outcome_hint is True
    assert features.threshold_hint is False
    assert features.threshold_terms == ()
    assert features.ambiguous_resolution_flags == ()
    assert features.implied_probability_sum == Decimal("1.000000")


def test_flags_ambiguous_resolution_language_for_contested_event_markets() -> None:
    features = extract_strategy_probability_event_features(
        question=(
            "Will Candidate A be called the winner if recount lawsuits are still pending?"
        ),
        category="Politics",
        tags=("Election", "recount", "lawsuit", "called race"),
        end_date=datetime(2026, 11, 7, 12, tzinfo=UTC),
        probabilities=(Decimal("0.520000"), Decimal("0.480000")),
        as_of=datetime(2026, 11, 5, 12, tzinfo=UTC),
    )

    assert features.event_type == "politics"
    assert features.binary_outcome_hint is True
    assert features.ambiguous_resolution_flags == (
        "conditional_resolution_terms",
        "disputed_or_recount_risk",
        "unofficial_source_dependency",
    )


def test_probability_event_features_payload_is_report_only_decimal_text() -> None:
    features = extract_strategy_probability_event_features(
        question="Will BTC be above $100,000 on December 31, 2026?",
        category="Crypto",
        tags=("Bitcoin", "threshold"),
        end_date=datetime(2026, 12, 31, 23, tzinfo=UTC),
        probabilities=(Decimal("0.450000"), Decimal("0.550000")),
        as_of=datetime(2026, 12, 30, 23, tzinfo=UTC),
    )

    assert strategy_probability_event_features_payload(features) == {
        "model_kind": "probability_event_market",
        "price_asset_model": False,
        "event_type": "crypto",
        "time_to_resolution_hours": "24.000000",
        "probability_count": "2",
        "normalized_probabilities": ["0.450000", "0.550000"],
        "implied_probability_sum": "1.000000",
        "binary_outcome_hint": True,
        "threshold_hint": True,
        "threshold_terms": ["$100,000"],
        "multi_outcome_hint": False,
        "ambiguous_resolution_flags": [],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


@pytest.mark.parametrize(
    ("kwargs", "match"),
    (
        ({"question": ""}, "question"),
        ({"category": ""}, "category"),
        ({"tags": ["Fed"]}, "tags"),
        ({"tags": ("Fed", "")}, "tags"),
        ({"end_date": datetime(2026, 3, 18, 18)}, "end_date"),
        ({"as_of": datetime(2026, 3, 15, 18)}, "as_of"),
        ({"probabilities": [Decimal("0.500000"), Decimal("0.500000")]}, "probabilities"),
        ({"probabilities": (Decimal("1.250000"),)}, "probabilities"),
        ({"probabilities": (Decimal("0.600000"), Decimal("0.600000"))}, "probabilities"),
    ),
)
def test_validates_probability_event_inputs(kwargs: dict[str, object], match: str) -> None:
    valid_kwargs = {
        "question": "Will the Fed cut rates in March?",
        "category": "Economics",
        "tags": ("Fed",),
        "end_date": datetime(2026, 3, 18, 18, tzinfo=UTC),
        "probabilities": (Decimal("0.500000"), Decimal("0.500000")),
        "as_of": datetime(2026, 3, 15, 18, tzinfo=UTC),
    }
    valid_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=match):
        extract_strategy_probability_event_features(**valid_kwargs)


def test_probability_event_features_outputs_are_frozen() -> None:
    features = extract_strategy_probability_event_features(
        question="Will the Fed cut rates in March?",
        category="Economics",
        tags=("Fed",),
        end_date=datetime(2026, 3, 18, 18, tzinfo=UTC),
        probabilities=(Decimal("0.500000"), Decimal("0.500000")),
        as_of=datetime(2026, 3, 15, 18, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        features.event_type = "price_asset"  # type: ignore[misc]
    with pytest.raises(ValueError, match="model_kind"):
        replace(features, model_kind="price_asset")
    with pytest.raises(ValueError, match="price_asset_model"):
        replace(features, price_asset_model=True)
    with pytest.raises(ValueError, match="ambiguous_resolution_flags"):
        replace(features, ambiguous_resolution_flags=["conditional_resolution_terms"])  # type: ignore[arg-type]


def test_probability_event_features_rejects_subclasses() -> None:
    class StrategyProbabilityEventFeaturesSubclass(StrategyProbabilityEventFeatures):
        pass

    with pytest.raises(ValueError, match="features"):
        StrategyProbabilityEventFeaturesSubclass(
            event_type="macro_policy",
            time_to_resolution_hours=Decimal("24.000000"),
            probability_count=Decimal("2"),
            normalized_probabilities=(Decimal("0.500000"), Decimal("0.500000")),
            implied_probability_sum=Decimal("1.000000"),
            binary_outcome_hint=True,
            threshold_hint=False,
            threshold_terms=(),
            multi_outcome_hint=False,
            ambiguous_resolution_flags=(),
        )
