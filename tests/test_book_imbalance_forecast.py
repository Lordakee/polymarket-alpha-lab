import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.domain import (
    MarketSnapshot,
    NormalizedMarket,
    OrderBookLevel,
    OrderBookSnapshot,
    OutcomeToken,
)
from polymarket_alpha_lab.book_imbalance_forecast import (
    PaperBookImbalanceForecast,
    PaperBookImbalanceForecastConfig,
    PaperBookImbalanceForecastLog,
    build_paper_book_imbalance_forecast,
)


GENERATED_AT = datetime(2026, 6, 16, 13, 0, tzinfo=UTC)

COST_QUANTUM = Decimal("0.000001")


def forecast_config(**overrides):
    values = {
        "config_version": "book-imbalance-forecast-v1",
        "imbalance_strength": Decimal("0.0200"),
        "max_nudge": Decimal("0.0500"),
        "min_book_depth": Decimal("1.0000"),
        "low_confidence_value": Decimal("0.5000"),
        "high_confidence_value": Decimal("0.7500"),
        "max_spread_for_high_confidence": Decimal("0.0300"),
    }
    values.update(overrides)
    return PaperBookImbalanceForecastConfig(**values)


def normalized_market(**overrides):
    values = {
        "condition_id": "0xcondition",
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "active": True,
        "closed": False,
        "accepting_orders": True,
        "end_time": None,
        "volume_24h": Decimal("1000.0000"),
        "liquidity": Decimal("500.0000"),
        "captured_at": GENERATED_AT,
        "tokens": (
            OutcomeToken(
                condition_id="0xcondition",
                token_id="yes-token",
                outcome_index=0,
                outcome_name="Yes",
            ),
            OutcomeToken(
                condition_id="0xcondition",
                token_id="no-token",
                outcome_index=1,
                outcome_name="No",
            ),
        ),
        "rules_text": "Market resolves according to the public source.",
        "resolution_source": "public-source",
    }
    values.update(overrides)
    return NormalizedMarket(
        market=MarketSnapshot(
            condition_id=values["condition_id"],
            market_slug=values["market_slug"],
            question=values["question"],
            active=values["active"],
            closed=values["closed"],
            accepting_orders=values["accepting_orders"],
            end_time=values["end_time"],
            volume_24h=values["volume_24h"],
            liquidity=values["liquidity"],
            captured_at=values["captured_at"],
        ),
        tokens=values["tokens"],
        rules_text=values["rules_text"],
        resolution_source=values["resolution_source"],
    )


def book_level(price, size):
    return OrderBookLevel(price=Decimal(price), size=Decimal(size))


def yes_book(**overrides):
    values = {
        "token_id": "yes-token",
        "bids": (book_level("0.5200", "250.0000"),),
        "asks": (book_level("0.5400", "50.0000"),),
        "captured_at": GENERATED_AT,
    }
    values.update(overrides)
    return OrderBookSnapshot(**values)


def no_book(**overrides):
    values = {
        "token_id": "no-token",
        "bids": (book_level("0.4400", "200.0000"),),
        "asks": (book_level("0.4800", "200.0000"),),
        "captured_at": GENERATED_AT,
    }
    values.update(overrides)
    return OrderBookSnapshot(**values)


def forecast(**overrides):
    values = {
        "generated_at": GENERATED_AT,
        "config_version": "book-imbalance-forecast-v1",
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "fair_probability_yes": Decimal("0.553333"),
        "confidence": Decimal("0.750000"),
        "basis": "book_imbalance_v0",
        "yes_best_ask": Decimal("0.5400"),
        "yes_bid_size": Decimal("250.0000"),
        "yes_ask_size": Decimal("50.0000"),
        "imbalance": Decimal("0.666667"),
        "nudge": Decimal("0.013333"),
        "reason_codes": ("book_imbalance_nudge", "high_confidence_book"),
        "paper_only": True,
        "report_only": True,
    }
    values.update(overrides)
    return PaperBookImbalanceForecast(**values)


def build_forecast(market=None, yes=None, no=None, config=None, generated_at=GENERATED_AT):
    return build_paper_book_imbalance_forecast(
        market or normalized_market(),
        yes or yes_book(),
        no or no_book(),
        config=config or forecast_config(),
        generated_at=generated_at,
    )


def test_book_imbalance_bid_heavy_book_lifts_fair_probability_above_yes_ask():
    result = build_forecast(
        yes=yes_book(
            bids=(book_level("0.5200", "250.0000"),),
            asks=(book_level("0.5400", "50.0000"),),
        ),
    )

    assert isinstance(result, PaperBookImbalanceForecast)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.yes_best_ask == Decimal("0.5400")
    assert result.yes_bid_size == Decimal("250.0000")
    assert result.yes_ask_size == Decimal("50.0000")
    assert result.imbalance == Decimal("0.666667")
    assert result.nudge > Decimal("0")
    assert result.fair_probability_yes > result.yes_best_ask
    assert result.fair_probability_yes == Decimal("0.553333")
    assert result.nudge == Decimal("0.013333")
    assert result.reason_codes == ("book_imbalance_nudge", "high_confidence_book")


def test_book_imbalance_ask_heavy_book_lowers_fair_probability_below_yes_ask():
    result = build_forecast(
        yes=yes_book(
            bids=(book_level("0.5200", "50.0000"),),
            asks=(book_level("0.5400", "250.0000"),),
        ),
    )

    assert result.imbalance == Decimal("-0.666667")
    assert result.nudge < Decimal("0")
    assert result.fair_probability_yes < result.yes_best_ask
    assert result.fair_probability_yes == Decimal("0.526667")
    assert result.nudge == Decimal("-0.013333")


def test_book_imbalance_balanced_book_produces_zero_nudge():
    result = build_forecast(
        yes=yes_book(
            bids=(book_level("0.5200", "100.0000"),),
            asks=(book_level("0.5400", "100.0000"),),
        ),
    )

    assert result.imbalance == Decimal("0.000000")
    assert result.nudge == Decimal("0.000000")
    assert result.fair_probability_yes == Decimal("0.540000")


@pytest.mark.parametrize(
    ("config_overrides", "yes_overrides"),
    (
        (
            {"imbalance_strength": Decimal("0.1000"), "max_nudge": Decimal("0.0500")},
            {
                "bids": (book_level("0.5200", "1000.0000"),),
                "asks": (book_level("0.5400", "1.0000"),),
            },
        ),
        (
            {},
            {
                "bids": (book_level("0.5200", "250.0000"),),
                "asks": (book_level("0.5400", "50.0000"),),
            },
        ),
    ),
)
def test_book_imbalance_nudge_magnitude_is_bounded_by_max_nudge(config_overrides, yes_overrides):
    config = forecast_config(**config_overrides)
    result = build_forecast(yes=yes_book(**yes_overrides), config=config)

    assert abs(result.nudge) <= config.max_nudge
    if config_overrides:
        assert abs(result.nudge) == config.max_nudge


@pytest.mark.parametrize(
    ("yes_overrides", "expected_yes_best_ask"),
    (
        ({"asks": ()}, None),
        (
            {
                "bids": (book_level("0.5200", "0.0000"),),
                "asks": (book_level("0.5400", "0.0000"),),
            },
            Decimal("0.5400"),
        ),
    ),
)
def test_book_imbalance_missing_ask_or_zero_depth_falls_back_to_low_confidence_placeholder(
    yes_overrides,
    expected_yes_best_ask,
):
    config = forecast_config()
    result = build_forecast(yes=yes_book(**yes_overrides), config=config)

    assert result.fair_probability_yes == config.low_confidence_value
    assert result.nudge == Decimal("0.000000")
    assert result.confidence == config.low_confidence_value
    assert result.yes_best_ask == expected_yes_best_ask
    assert "missing_yes_ask_or_depth" in result.reason_codes
    assert "low_confidence_book" in result.reason_codes


@pytest.mark.parametrize(
    "yes_overrides",
    (
        {
            "bids": (book_level("0.5200", "250.0000"),),
            "asks": (book_level("0.5400", "50.0000"),),
        },
        {
            "bids": (book_level("0.5200", "50.0000"),),
            "asks": (book_level("0.5400", "250.0000"),),
        },
        {
            "bids": (book_level("0.5200", "100.0000"),),
            "asks": (book_level("0.5400", "100.0000"),),
        },
    ),
)
def test_book_imbalance_field_is_bounded_and_quantized(yes_overrides):
    result = build_forecast(yes=yes_book(**yes_overrides))

    assert result.imbalance is not None
    assert Decimal("-1") <= result.imbalance <= Decimal("1")
    assert result.imbalance == result.imbalance.quantize(COST_QUANTUM)


@pytest.mark.parametrize(
    ("yes_overrides", "expected_confidence", "expected_confidence_reason"),
    (
        (
            {
                "bids": (book_level("0.5200", "250.0000"),),
                "asks": (book_level("0.5400", "250.0000"),),
            },
            Decimal("0.750000"),
            "high_confidence_book",
        ),
        (
            {
                "bids": (book_level("0.5200", "250.0000"),),
                "asks": (book_level("0.5400", "0.5000"),),
            },
            Decimal("0.500000"),
            "low_confidence_book",
        ),
        (
            {
                "bids": (book_level("0.5000", "250.0000"),),
                "asks": (book_level("0.5400", "250.0000"),),
            },
            Decimal("0.500000"),
            "low_confidence_book",
        ),
    ),
)
def test_book_imbalance_confidence_uses_two_bucket_book_quality_scheme(
    yes_overrides,
    expected_confidence,
    expected_confidence_reason,
):
    config = forecast_config()
    result = build_forecast(yes=yes_book(**yes_overrides), config=config)

    assert result.confidence == expected_confidence
    assert expected_confidence_reason in result.reason_codes


def test_book_imbalance_basis_marks_placeholder_book_imbalance_signal():
    result = build_forecast()

    assert result.basis == "book_imbalance_v0"


def test_book_imbalance_requires_expected_input_types_before_building_report():
    with pytest.raises(ValueError, match="market"):
        build_paper_book_imbalance_forecast(
            object(),
            yes_book(),
            no_book(),
            config=forecast_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="yes_book"):
        build_paper_book_imbalance_forecast(
            normalized_market(),
            object(),
            no_book(),
            config=forecast_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="no_book"):
        build_paper_book_imbalance_forecast(
            normalized_market(),
            yes_book(),
            object(),
            config=forecast_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_book_imbalance_forecast(
            normalized_market(),
            yes_book(),
            no_book(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_book_imbalance_forecast(
            normalized_market(),
            yes_book(),
            no_book(),
            config=forecast_config(),
            generated_at=object(),
        )


@pytest.mark.parametrize(
    ("config_overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"config_version": " book-imbalance-forecast-v1"}, "config_version"),
        ({"imbalance_strength": "0.0200"}, "imbalance_strength"),
        ({"imbalance_strength": Decimal("0.0000")}, "imbalance_strength|positive"),
        ({"imbalance_strength": Decimal("NaN")}, "imbalance_strength|finite"),
        ({"max_nudge": Decimal("0.0000")}, "max_nudge|positive"),
        ({"min_book_depth": Decimal("0.0000")}, "min_book_depth|positive"),
        ({"low_confidence_value": Decimal("-0.0001")}, "low_confidence_value"),
        ({"high_confidence_value": Decimal("1.0001")}, "high_confidence_value"),
        (
            {"max_spread_for_high_confidence": Decimal("-0.0001")},
            "max_spread_for_high_confidence",
        ),
        (
            {"max_spread_for_high_confidence": Decimal("NaN")},
            "max_spread_for_high_confidence|finite",
        ),
        ({"low_confidence_value": Decimal("Infinity")}, "low_confidence_value|finite"),
    ),
)
def test_book_imbalance_config_rejects_invalid_decimal_probability_ratio_and_string_inputs(
    config_overrides,
    message,
):
    with pytest.raises(ValueError, match=message):
        forecast_config(**config_overrides)


@pytest.mark.parametrize(
    ("forecast_overrides", "message"),
    (
        ({"generated_at": object()}, "datetime"),
        ({"config_version": ""}, "config_version"),
        ({"market_slug": " fed-cut-june-2026"}, "market_slug"),
        ({"question": ""}, "question"),
        ({"fair_probability_yes": "0.5400"}, "fair_probability_yes"),
        ({"fair_probability_yes": Decimal("NaN")}, "fair_probability_yes|finite"),
        ({"fair_probability_yes": Decimal("1.0001")}, "fair_probability_yes"),
        ({"confidence": Decimal("Infinity")}, "confidence|finite"),
        ({"confidence": Decimal("-0.0001")}, "confidence"),
        ({"basis": "yes_ask_naive_v0"}, "basis"),
        ({"yes_best_ask": Decimal("1.5000")}, "yes_best_ask"),
        ({"yes_best_ask": Decimal("-0.0100")}, "yes_best_ask"),
        ({"yes_bid_size": Decimal("-5.0000")}, "yes_bid_size"),
        ({"yes_ask_size": Decimal("-5.0000")}, "yes_ask_size"),
        ({"imbalance": Decimal("1.5000")}, "imbalance"),
        ({"imbalance": Decimal("-1.5000")}, "imbalance"),
        ({"nudge": "0.013333"}, "nudge"),
        ({"nudge": Decimal("NaN")}, "nudge|finite"),
        ({"reason_codes": ()}, "reason_codes"),
        ({"reason_codes": (" book_imbalance_nudge",)}, "reason_codes"),
    ),
)
def test_book_imbalance_forecast_rejects_invalid_report_inputs(forecast_overrides, message):
    with pytest.raises(ValueError, match=message):
        forecast(**forecast_overrides)


def test_book_imbalance_forecast_dataclasses_are_frozen_and_revalidate_report_flags():
    result = forecast()
    config = forecast_config()

    with pytest.raises(FrozenInstanceError):
        result.confidence = Decimal("0.500000")
    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(result, report_only=False)


def test_book_imbalance_forecast_log_appends_jsonl_decimal_strings_and_preserves_existing_file(
    tmp_path,
):
    result = build_forecast(
        yes=yes_book(
            bids=(book_level("0.5200", "250.0000"),),
            asks=(book_level("0.5400", "50.0000"),),
        ),
    )
    log = PaperBookImbalanceForecastLog(
        path=tmp_path / "nested" / "book-imbalance-forecast.jsonl",
    )

    log.append(result)
    log.append(result)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-06-16T13:00:00+00:00"
    assert stored["market_slug"] == "fed-cut-june-2026"
    assert stored["basis"] == "book_imbalance_v0"
    assert stored["fair_probability_yes"] == "0.553333"
    assert stored["confidence"] == "0.750000"
    assert stored["yes_best_ask"] == "0.5400"
    assert stored["yes_bid_size"] == "250.0000"
    assert stored["yes_ask_size"] == "50.0000"
    assert stored["imbalance"] == "0.666667"
    assert stored["nudge"] == "0.013333"
    assert stored["reason_codes"] == ["book_imbalance_nudge", "high_confidence_book"]

    existing_log_path = tmp_path / "existing.jsonl"
    existing_log_path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PaperBookImbalanceForecast"):
        PaperBookImbalanceForecastLog(path=existing_log_path).append(object())
    assert existing_log_path.read_text(encoding="utf-8") == "existing\n"


@pytest.mark.parametrize(
    ("config_overrides", "yes_overrides"),
    (
        (
            {},
            {
                "bids": (book_level("0.5200", "250.0000"),),
                "asks": (book_level("0.5400", "50.0000"),),
            },
        ),
        (
            {"imbalance_strength": Decimal("0.1000"), "max_nudge": Decimal("0.0500")},
            {
                "bids": (book_level("0.5200", "1000.0000"),),
                "asks": (book_level("0.5400", "1.0000"),),
            },
        ),
    ),
)
def test_book_imbalance_nudge_is_reproducible_from_stored_imbalance_and_strength(
    config_overrides,
    yes_overrides,
):
    config = forecast_config(**config_overrides)
    result = build_forecast(yes=yes_book(**yes_overrides), config=config)

    raw_nudge = result.imbalance * config.imbalance_strength
    clamped = max(-config.max_nudge, min(raw_nudge, config.max_nudge))
    recomputed = clamped.quantize(COST_QUANTUM)

    assert recomputed == result.nudge
