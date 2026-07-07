from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_forecast_uncertainty_band_report import (
    ResearchForecastUncertaintyBandConfig,
    ResearchForecastUncertaintyBandInputRow,
    ResearchForecastUncertaintyBandReasonCodeCount,
    ResearchForecastUncertaintyBandReport,
    ResearchForecastUncertaintyBandReportRow,
    build_research_forecast_uncertainty_band_report,
    research_forecast_uncertainty_band_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchForecastUncertaintyBandConfig:
    values = {
        "config_version": "research-forecast-uncertainty-band-report-v0",
        "pass_max_uncertainty_score": d("0.150000"),
        "watch_max_uncertainty_score": d("0.450000"),
        "min_interval_half_width": d("0.020000"),
        "max_interval_half_width": d("0.250000"),
        "evidence_quality_weight": d("0.400000"),
        "model_disagreement_weight": d("0.250000"),
        "market_noise_weight": d("0.200000"),
        "settlement_ambiguity_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchForecastUncertaintyBandConfig(**values)


def forecast(
    *,
    event_ref: str = "event-alpha",
    forecast_ref: str = "forecast-naive",
    probability: Decimal = d("0.550000"),
    observed_at: datetime | None = None,
    evidence_quality_score: Decimal = d("0.900000"),
    model_disagreement_score: Decimal = d("0.040000"),
    market_noise_score: Decimal = d("0.050000"),
    settlement_ambiguity_score: Decimal = d("0.030000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchForecastUncertaintyBandInputRow:
    return ResearchForecastUncertaintyBandInputRow(
        event_ref=event_ref,
        forecast_ref=forecast_ref,
        probability=probability,
        observed_at=observed_at
        if observed_at is not None
        else GENERATED_AT - timedelta(minutes=15),
        evidence_quality_score=evidence_quality_score,
        model_disagreement_score=model_disagreement_score,
        market_noise_score=market_noise_score,
        settlement_ambiguity_score=settlement_ambiguity_score,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchForecastUncertaintyBandInputRow, ...],
    *,
    cfg: ResearchForecastUncertaintyBandConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchForecastUncertaintyBandReport:
    return build_research_forecast_uncertainty_band_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_high_quality_aligned_forecasts_produce_pass_band() -> None:
    uncertainty = report(
        (
            forecast(forecast_ref="forecast-naive", probability=d("0.540000")),
            forecast(forecast_ref="forecast-llm", probability=d("0.560000")),
            forecast(forecast_ref="forecast-research", probability=d("0.550000")),
        ),
    )

    assert type(uncertainty) is ResearchForecastUncertaintyBandReport
    assert uncertainty.generated_at == GENERATED_AT
    assert uncertainty.event_count == d("1.000000")
    assert uncertainty.forecast_count == d("3.000000")
    assert uncertainty.pass_count == d("1.000000")
    assert uncertainty.watch_count == d("0.000000")
    assert uncertainty.block_count == d("0.000000")
    assert uncertainty.status == "pass"
    assert uncertainty.reason_codes == ("research_forecast_uncertainty_band_pass",)
    assert uncertainty.paper_only is True
    assert uncertainty.report_only is True
    assert uncertainty.readonly is True

    row = uncertainty.rows[0]
    assert type(row) is ResearchForecastUncertaintyBandReportRow
    assert row.event_ref == "event-alpha"
    assert row.forecast_count == d("3.000000")
    assert row.average_probability == d("0.550000")
    assert row.minimum_probability == d("0.540000")
    assert row.maximum_probability == d("0.560000")
    assert row.average_evidence_quality_score == d("0.900000")
    assert row.evidence_uncertainty_score == d("0.100000")
    assert row.model_disagreement_score == d("0.040000")
    assert row.market_noise_score == d("0.050000")
    assert row.settlement_ambiguity_score == d("0.030000")
    assert row.uncertainty_score == d("0.064500")
    assert row.interval_lower_probability == d("0.515165")
    assert row.interval_upper_probability == d("0.584835")
    assert row.interval_width == d("0.069670")
    assert row.status == "pass"
    assert row.reason_codes == (
        "evidence_quality_strong",
        "forecast_uncertainty_band_pass",
        "market_noise_low",
        "model_disagreement_low",
        "settlement_ambiguity_low",
    )


def test_mixed_quality_and_noise_produce_watch_band() -> None:
    uncertainty = report(
        (
            forecast(
                forecast_ref="forecast-a",
                probability=d("0.570000"),
                evidence_quality_score=d("0.600000"),
                model_disagreement_score=d("0.300000"),
                market_noise_score=d("0.400000"),
                settlement_ambiguity_score=d("0.300000"),
            ),
            forecast(
                forecast_ref="forecast-b",
                probability=d("0.630000"),
                evidence_quality_score=d("0.600000"),
                model_disagreement_score=d("0.300000"),
                market_noise_score=d("0.400000"),
                settlement_ambiguity_score=d("0.300000"),
                reason_codes=("needs_review",),
            ),
        ),
    )

    row = uncertainty.rows[0]
    assert uncertainty.status == "watch"
    assert uncertainty.watch_count == d("1.000000")
    assert uncertainty.max_uncertainty_score == d("0.360000")
    assert row.average_probability == d("0.600000")
    assert row.uncertainty_score == d("0.360000")
    assert row.interval_lower_probability == d("0.497200")
    assert row.interval_upper_probability == d("0.702800")
    assert row.interval_width == d("0.205600")
    assert row.status == "watch"
    assert row.reason_codes == (
        "evidence_quality_watch",
        "forecast_uncertainty_band_watch",
        "input_needs_review",
        "market_noise_watch",
        "model_disagreement_watch",
        "settlement_ambiguity_watch",
    )


def test_low_quality_noisy_ambiguous_forecasts_produce_block_band() -> None:
    uncertainty = report(
        (
            forecast(
                forecast_ref="forecast-low",
                probability=d("0.050000"),
                evidence_quality_score=d("0.200000"),
                model_disagreement_score=d("0.800000"),
                market_noise_score=d("0.700000"),
                settlement_ambiguity_score=d("0.900000"),
            ),
            forecast(
                forecast_ref="forecast-high",
                probability=d("0.950000"),
                evidence_quality_score=d("0.300000"),
                model_disagreement_score=d("0.800000"),
                market_noise_score=d("0.700000"),
                settlement_ambiguity_score=d("0.900000"),
            ),
        ),
    )

    row = uncertainty.rows[0]
    assert uncertainty.status == "block"
    assert uncertainty.block_count == d("1.000000")
    assert uncertainty.pass_count == d("0.000000")
    assert row.average_evidence_quality_score == d("0.250000")
    assert row.evidence_uncertainty_score == d("0.750000")
    assert row.uncertainty_score == d("0.775000")
    assert row.interval_lower_probability == d("0.301750")
    assert row.interval_upper_probability == d("0.698250")
    assert row.status == "block"
    assert row.reason_codes == (
        "evidence_quality_weak",
        "forecast_uncertainty_band_block",
        "market_noise_high",
        "model_disagreement_high",
        "settlement_ambiguity_high",
    )


def test_empty_input_returns_block_report_without_action_language() -> None:
    uncertainty = report(())

    payload = research_forecast_uncertainty_band_report_payload(uncertainty)
    encoded = json.dumps(payload, sort_keys=True).lower()

    assert uncertainty.status == "block"
    assert uncertainty.reason_codes == ("forecast_uncertainty_band_no_inputs",)
    assert uncertainty.rows == ()
    assert uncertainty.reason_code_counts == (
        ResearchForecastUncertaintyBandReasonCodeCount(
            reason_code="forecast_uncertainty_band_no_inputs",
            count=d("1.000000"),
            event_ratio=d("1.000000"),
        ),
    )
    for forbidden in (
        "advice",
        "auth",
        "buy",
        "live_trading",
        "order",
        "position",
        "recommend",
        "sell",
        "trade",
        "wallet",
    ):
        assert forbidden not in encoded


def test_payload_is_deterministic_public_and_decimal_only() -> None:
    uncertainty = report(
        (
            forecast(event_ref="z-event", forecast_ref="z-a", probability=d("0.400000")),
            forecast(event_ref="a-event", forecast_ref="a-a", probability=d("0.520000")),
            forecast(event_ref="a-event", forecast_ref="a-b", probability=d("0.540000")),
        ),
    )

    payload = research_forecast_uncertainty_band_report_payload(uncertainty)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.event_ref for row in uncertainty.rows) == ("a-event", "z-event")
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["average_probability"] == "0.530000"
    assert payload["rows"][0]["interval_lower_probability"] == "0.495165"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_validation_rejects_bad_types_future_times_duplicates_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="pass_max_uncertainty_score"):
        config(pass_max_uncertainty_score=0.15)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_noise_weight"):
        config(market_noise_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="weights"):
        config(market_noise_weight=d("0.300000"))
    with pytest.raises(ValueError, match="event_ref"):
        forecast(event_ref=" event-alpha")
    with pytest.raises(ValueError, match="probability"):
        forecast(probability=d("1.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        forecast(observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((forecast(),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report((forecast(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="reason_codes"):
        forecast(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="duplicate"):
        report((forecast(forecast_ref="same"), forecast(forecast_ref="same")))
    with pytest.raises(ValueError, match="paper_only"):
        replace(forecast(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    uncertainty = report(
        (
            forecast(forecast_ref="forecast-a", probability=d("0.540000")),
            forecast(forecast_ref="forecast-b", probability=d("0.560000")),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        uncertainty.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        uncertainty.rows[0].uncertainty_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="interval_width"):
        replace(uncertainty.rows[0], interval_width=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(uncertainty, status="block")


def test_owned_module_has_no_network_filesystem_or_mutation_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_forecast_uncertainty_band_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "advice",
        "auth",
        "buy",
        "live_trading",
        "order",
        "place_order",
        "position",
        "recommend",
        "sell",
        "submit_order",
        "trade",
        "wallet",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
