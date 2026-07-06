from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from json import dumps

import pytest

from polymarket_alpha_lab.strategy_forecast_rationale_quality_v8 import (
    REQUIRED_RATIONALE_SECTIONS,
    StrategyForecastRationaleQualityV8Config,
    StrategyForecastRationaleQualityV8Forecast,
    StrategyForecastRationaleQualityV8Report,
    StrategyForecastRationaleQualityV8Row,
    build_strategy_forecast_rationale_quality_v8_report,
    strategy_forecast_rationale_quality_v8_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def forecast(**overrides: object) -> StrategyForecastRationaleQualityV8Forecast:
    values = {
        "forecast_id": "forecast-complete",
        "market_slug": "fed-cuts-in-september",
        "team_id": "macro_rates",
        "rationale_text": (
            "Uses the historical base rate, current FOMC evidence, opposing inflation "
            "signals, Polymarket resolution rules, and fee-adjusted EV sensitivity."
        ),
        "covers_base_rate": True,
        "covers_current_evidence": True,
        "covers_counter_evidence": True,
        "covers_resolution_mechanics": True,
        "covers_cost_ev_sensitivity": True,
    }
    values.update(overrides)
    return StrategyForecastRationaleQualityV8Forecast(**values)


def report(
    forecasts: tuple[StrategyForecastRationaleQualityV8Forecast, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: StrategyForecastRationaleQualityV8Config | None = None,
) -> StrategyForecastRationaleQualityV8Report:
    return build_strategy_forecast_rationale_quality_v8_report(
        forecasts,
        config=cfg or StrategyForecastRationaleQualityV8Config(),
        generated_at=generated_at,
    )


def test_forecast_rationale_quality_v8_detects_missing_required_sections() -> None:
    complete = forecast()
    incomplete = forecast(
        forecast_id="forecast-gap",
        market_slug="btc-ath-by-year-end",
        team_id="crypto_btc",
        rationale_text=(
            "Mentions the prior BTC rally base rate, ETF flow evidence, and the market "
            "resolution source but omits bears and cost sensitivity."
        ),
        covers_counter_evidence=False,
        covers_cost_ev_sensitivity=False,
    )

    built = report((complete, incomplete))

    assert REQUIRED_RATIONALE_SECTIONS == (
        "base_rate",
        "current_evidence",
        "counter_evidence",
        "resolution_mechanics",
        "cost_ev_sensitivity",
    )
    assert built == StrategyForecastRationaleQualityV8Report(
        generated_at=GENERATED_AT,
        config_version="strategy-forecast-rationale-quality-v8",
        forecast_count=d("2.000000"),
        pass_count=d("1.000000"),
        blocked_count=d("1.000000"),
        rationale_quality_status="blocked",
        missing_sections=("counter_evidence", "cost_ev_sensitivity"),
        reason_codes=(
            "forecast_rationale_complete",
            "missing_counter_evidence",
            "missing_cost_ev_sensitivity",
        ),
        rows=(
            StrategyForecastRationaleQualityV8Row(
                forecast_id="forecast-complete",
                market_slug="fed-cuts-in-september",
                team_id="macro_rates",
                covered_section_count=d("5.000000"),
                missing_section_count=ZERO,
                rationale_quality_status="pass",
                missing_sections=(),
                reason_codes=("forecast_rationale_complete",),
            ),
            StrategyForecastRationaleQualityV8Row(
                forecast_id="forecast-gap",
                market_slug="btc-ath-by-year-end",
                team_id="crypto_btc",
                covered_section_count=d("3.000000"),
                missing_section_count=d("2.000000"),
                rationale_quality_status="blocked",
                missing_sections=("counter_evidence", "cost_ev_sensitivity"),
                reason_codes=(
                    "missing_counter_evidence",
                    "missing_cost_ev_sensitivity",
                ),
            ),
        ),
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True


def test_forecast_rationale_quality_v8_empty_report_is_pass_readonly() -> None:
    built = report(())

    assert built.rationale_quality_status == "pass"
    assert built.forecast_count == ZERO
    assert built.pass_count == ZERO
    assert built.blocked_count == ZERO
    assert built.missing_sections == ()
    assert built.reason_codes == ("forecast_rationale_quality_empty",)
    assert built.rows == ()


def test_forecast_rationale_quality_v8_payload_is_json_ready_and_decimal_only() -> None:
    built = report((forecast(),))
    payload = strategy_forecast_rationale_quality_v8_report_payload(built)

    dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["forecast_count"] == "1.000000"
    assert payload["rows"][0]["covered_section_count"] == "5.000000"
    assert payload["rows"][0]["missing_section_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float(payload)


def test_forecast_rationale_quality_v8_validates_types_utc_and_flags() -> None:
    built = report((forecast(),))

    with pytest.raises(FrozenInstanceError):
        built.rows[0].forecast_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="covers_base_rate must be a bool"):
        forecast(covers_base_rate=1)
    with pytest.raises(ValueError, match="forecast_count must be a Decimal"):
        replace(built, forecast_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="covered_section_count must be a Decimal"):
        replace(built.rows[0], covered_section_count=DecimalSubclass("5.000000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware UTC"):
        report((forecast(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware UTC"):
        report(
            (forecast(),),
            generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        )
    with pytest.raises(ValueError, match="rationale_text must be a canonical nonblank string"):
        forecast(rationale_text=" ")
    with pytest.raises(ValueError, match="paper_only must be True"):
        forecast(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        StrategyForecastRationaleQualityV8Config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(built, readonly=False)


def test_forecast_rationale_quality_v8_rejects_manual_inconsistent_outputs() -> None:
    row = StrategyForecastRationaleQualityV8Row(
        forecast_id="manual-row",
        market_slug="manual-market",
        team_id="macro_rates",
        covered_section_count=d("4.000000"),
        missing_section_count=d("1.000000"),
        rationale_quality_status="blocked",
        missing_sections=("base_rate",),
        reason_codes=("missing_base_rate",),
    )

    assert row.paper_only is True
    with pytest.raises(ValueError, match="reason_codes must match missing_sections"):
        replace(row, reason_codes=("missing_current_evidence",))
    with pytest.raises(ValueError, match="rationale_quality_status must match missing_sections"):
        replace(row, rationale_quality_status="pass")
    with pytest.raises(ValueError, match="forecast_count must match rows"):
        replace(report((forecast(),)), forecast_count=d("2.000000"))


def test_forecast_rationale_quality_v8_accepts_only_typed_forecasts() -> None:
    with pytest.raises(
        ValueError,
        match="forecasts must contain StrategyForecastRationaleQualityV8Forecast values",
    ):
        build_strategy_forecast_rationale_quality_v8_report(
            (object(),),
            config=StrategyForecastRationaleQualityV8Config(),
            generated_at=GENERATED_AT,
        )


def _assert_no_float(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float(item)
