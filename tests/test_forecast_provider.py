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
from polymarket_alpha_lab.forecast_provider import (
    PaperForecast,
    PaperForecastConfig,
    PaperForecastLog,
    build_paper_naive_forecast,
)


GENERATED_AT = datetime(2026, 6, 16, 13, 0, tzinfo=UTC)


def forecast_config(**overrides):
    values = {
        "config_version": "naive-forecast-v1",
        "min_book_depth": Decimal("10.0000"),
        "low_confidence_value": Decimal("0.5000"),
        "high_confidence_value": Decimal("0.7500"),
        "max_spread_for_high_confidence": Decimal("0.0300"),
    }
    values.update(overrides)
    return PaperForecastConfig(**values)


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
        "asks": (book_level("0.5400", "250.0000"),),
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
        "config_version": "naive-forecast-v1",
        "market_slug": "fed-cut-june-2026",
        "question": "Will the Fed cut rates by June 2026?",
        "fair_probability_yes": Decimal("0.540000"),
        "confidence": Decimal("0.750000"),
        "basis": "yes_ask_naive_v0",
        "reason_codes": ("yes_ask_basis", "high_confidence_book"),
        "paper_only": True,
        "report_only": True,
    }
    values.update(overrides)
    return PaperForecast(**values)


def build_forecast(market=None, yes=None, no=None, config=None, generated_at=GENERATED_AT):
    return build_paper_naive_forecast(
        market or normalized_market(),
        yes or yes_book(),
        no or no_book(),
        config=config or forecast_config(),
        generated_at=generated_at,
    )


def test_naive_forecast_uses_yes_best_ask_and_high_confidence_for_deep_tight_book():
    result = build_forecast(
        yes=yes_book(
            bids=(book_level("0.5200", "250.0000"),),
            asks=(book_level("0.5400", "250.0000"),),
        ),
    )

    assert isinstance(result, PaperForecast)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "naive-forecast-v1"
    assert result.market_slug == "fed-cut-june-2026"
    assert result.question == "Will the Fed cut rates by June 2026?"
    assert result.fair_probability_yes == Decimal("0.540000")
    assert result.confidence == Decimal("0.750000")
    assert result.basis == "yes_ask_naive_v0"
    assert result.reason_codes == ("yes_ask_basis", "high_confidence_book")


@pytest.mark.parametrize(
    ("ask_price", "expected_probability"),
    (
        ("-0.0200", Decimal("0.000000")),
        ("1.0200", Decimal("1.000000")),
    ),
)
def test_naive_forecast_clamps_yes_best_ask_to_probability_bounds(
    ask_price,
    expected_probability,
):
    result = build_forecast(
        yes=yes_book(
            bids=(book_level("1.0000", "250.0000"),),
            asks=(book_level(ask_price, "250.0000"),),
        ),
    )

    assert result.fair_probability_yes == expected_probability
    assert result.reason_codes == ("yes_ask_basis", "high_confidence_book")


@pytest.mark.parametrize(
    ("yes_overrides", "expected_reason"),
    (
        ({"asks": (book_level("0.5400", "5.0000"),)}, "low_confidence_book"),
        ({"bids": (book_level("0.4900", "250.0000"),)}, "low_confidence_book"),
        ({"bids": ()}, "low_confidence_book"),
    ),
)
def test_naive_forecast_uses_low_confidence_for_thin_wide_or_missing_bid_books(
    yes_overrides,
    expected_reason,
):
    result = build_forecast(yes=yes_book(**yes_overrides))

    assert result.fair_probability_yes == Decimal("0.540000")
    assert result.confidence == Decimal("0.500000")
    assert result.reason_codes == ("yes_ask_basis", expected_reason)


def test_naive_forecast_handles_missing_yes_ask_with_low_confidence_placeholder():
    result = build_forecast(yes=yes_book(asks=()))

    assert result.fair_probability_yes == Decimal("0.500000")
    assert result.confidence == Decimal("0.500000")
    assert result.basis == "yes_ask_naive_v0"
    assert result.reason_codes == ("missing_yes_ask", "low_confidence_book")


def test_naive_forecast_requires_expected_input_types_before_building_report():
    with pytest.raises(ValueError, match="market"):
        build_paper_naive_forecast(
            object(),
            yes_book(),
            no_book(),
            config=forecast_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="yes_book"):
        build_paper_naive_forecast(
            normalized_market(),
            object(),
            no_book(),
            config=forecast_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="no_book"):
        build_paper_naive_forecast(
            normalized_market(),
            yes_book(),
            object(),
            config=forecast_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_naive_forecast(
            normalized_market(),
            yes_book(),
            no_book(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_naive_forecast(
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
        ({"config_version": " naive-forecast-v1"}, "config_version"),
        ({"min_book_depth": "1.0000"}, "min_book_depth"),
        ({"min_book_depth": Decimal("0.0000")}, "min_book_depth|positive"),
        ({"low_confidence_value": Decimal("-0.0001")}, "low_confidence_value"),
        ({"high_confidence_value": Decimal("1.0001")}, "high_confidence_value"),
        ({"max_spread_for_high_confidence": Decimal("-0.0001")}, "max_spread_for_high_confidence"),
        ({"max_spread_for_high_confidence": Decimal("NaN")}, "max_spread_for_high_confidence|finite"),
        ({"low_confidence_value": Decimal("Infinity")}, "low_confidence_value|finite"),
    ),
)
def test_forecast_config_rejects_invalid_decimal_probability_ratio_and_string_inputs(
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
        ({"basis": "midpoint_naive_v0"}, "basis"),
        ({"reason_codes": ()}, "reason_codes"),
        ({"reason_codes": (" yes_ask_basis",)}, "reason_codes"),
    ),
)
def test_forecast_rejects_invalid_report_inputs(forecast_overrides, message):
    with pytest.raises(ValueError, match=message):
        forecast(**forecast_overrides)


def test_forecast_dataclasses_are_frozen_and_revalidate_report_flags():
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


def test_forecast_log_appends_jsonl_decimal_strings_and_preserves_existing_file(tmp_path):
    result = build_forecast()
    log = PaperForecastLog(path=tmp_path / "nested" / "forecast-provider.jsonl")

    log.append(result)
    log.append(result)

    lines = log.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    stored = json.loads(lines[0])
    assert stored["paper_only"] is True
    assert stored["report_only"] is True
    assert stored["generated_at"] == "2026-06-16T13:00:00+00:00"
    assert stored["market_slug"] == "fed-cut-june-2026"
    assert stored["fair_probability_yes"] == "0.540000"
    assert stored["confidence"] == "0.750000"
    assert stored["basis"] == "yes_ask_naive_v0"
    assert stored["reason_codes"] == ["yes_ask_basis", "high_confidence_book"]

    existing_log_path = tmp_path / "existing.jsonl"
    existing_log_path.write_text("existing\n", encoding="utf-8")
    with pytest.raises(ValueError, match="PaperForecast"):
        PaperForecastLog(path=existing_log_path).append(object())
    assert existing_log_path.read_text(encoding="utf-8") == "existing\n"
