from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_forecast_model_comparison_report import (
    ResearchForecastModelComparisonConfig,
    ResearchForecastModelComparisonInputRow,
    ResearchForecastModelComparisonReasonCodeCount,
    ResearchForecastModelComparisonReport,
    ResearchForecastModelComparisonSignalRow,
    build_research_forecast_model_comparison_report,
    research_forecast_model_comparison_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchForecastModelComparisonConfig:
    values = {
        "config_version": "research-forecast-model-comparison-report-v0",
        "min_coverage_ratio": d("0.750000"),
        "watch_disagreement_threshold": d("0.150000"),
        "block_disagreement_threshold": d("0.300000"),
        "min_calibration_observation_count": d("30"),
        "max_expected_calibration_error": d("0.100000"),
        "stale_signal_age_seconds": d("86400.000000"),
        "risk_watch_threshold": d("0.300000"),
        "risk_block_threshold": d("0.600000"),
    }
    values.update(overrides)
    return ResearchForecastModelComparisonConfig(**values)


def signal(
    *,
    market_id: str = "market-alpha",
    model_name: str = "naive",
    probability: Decimal | None = None,
    observed_at: datetime | None = None,
    calibration_observation_count: Decimal | None = None,
    calibration_error: Decimal | None = None,
    risk_score: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchForecastModelComparisonInputRow:
    probability_by_model = {
        "naive": d("0.520000"),
        "book_imbalance": d("0.570000"),
        "llm": d("0.540000"),
        "manual_research": d("0.550000"),
    }
    return ResearchForecastModelComparisonInputRow(
        market_id=market_id,
        model_name=model_name,
        probability=probability
        if probability is not None
        else probability_by_model.get(model_name, d("0.500000")),
        observed_at=observed_at
        if observed_at is not None
        else GENERATED_AT - timedelta(minutes=30),
        calibration_observation_count=calibration_observation_count,
        calibration_error=calibration_error,
        risk_score=risk_score,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchForecastModelComparisonInputRow, ...],
    *,
    cfg: ResearchForecastModelComparisonConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchForecastModelComparisonReport:
    return build_research_forecast_model_comparison_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_full_coverage_low_disagreement_and_calibration_pass() -> None:
    comparison = report(
        (
            signal(model_name="manual_research", calibration_observation_count=d("40"), calibration_error=d("0.040000")),
            signal(model_name="llm", calibration_observation_count=d("35"), calibration_error=d("0.060000")),
            signal(model_name="naive", calibration_observation_count=d("120"), calibration_error=d("0.050000")),
            signal(model_name="book_imbalance", calibration_observation_count=d("80"), calibration_error=d("0.070000")),
        ),
    )

    assert type(comparison) is ResearchForecastModelComparisonReport
    assert comparison.generated_at == GENERATED_AT
    assert comparison.market_count == d("1.000000")
    assert comparison.signal_count == d("4.000000")
    assert comparison.pass_count == d("1.000000")
    assert comparison.watch_count == d("0.000000")
    assert comparison.blocked_count == d("0.000000")
    assert comparison.status == "pass"
    assert comparison.reason_codes == ("research_forecast_model_comparison_pass",)
    assert comparison.next_step == "use_report_only_forecast_model_comparison"
    assert comparison.paper_only is True
    assert comparison.report_only is True
    assert comparison.readonly is True

    row = comparison.rows[0]
    assert type(row) is ResearchForecastModelComparisonSignalRow
    assert row.market_id == "market-alpha"
    assert row.coverage_ratio == d("1.000000")
    assert row.signal_count == d("4.000000")
    assert row.model_names == ("book_imbalance", "llm", "manual_research", "naive")
    assert row.min_probability == d("0.520000")
    assert row.max_probability == d("0.570000")
    assert row.disagreement_score == d("0.050000")
    assert row.calibrated_signal_count == d("4.000000")
    assert row.calibration_available_ratio == d("1.000000")
    assert row.average_calibration_error == d("0.055000")
    assert row.max_risk_score == d("0.100000")
    assert row.status == "pass"
    assert row.reason_codes == ("forecast_model_comparison_pass",)


def test_missing_models_high_disagreement_uncalibrated_and_high_risk_block() -> None:
    comparison = report(
        (
            signal(model_name="naive", probability=d("0.200000"), risk_score=d("0.700000")),
            signal(
                model_name="llm",
                probability=d("0.650000"),
                observed_at=GENERATED_AT - timedelta(days=2),
                risk_score=d("0.200000"),
                reason_codes=("manual_review_required",),
            ),
        ),
    )

    row = comparison.rows[0]
    assert comparison.status == "blocked"
    assert comparison.blocked_count == d("1.000000")
    assert comparison.watch_count == d("0.000000")
    assert comparison.pass_count == d("0.000000")
    assert comparison.thin_coverage_count == d("1.000000")
    assert comparison.high_disagreement_count == d("1.000000")
    assert comparison.uncalibrated_count == d("1.000000")
    assert comparison.high_risk_count == d("1.000000")
    assert row.coverage_ratio == d("0.500000")
    assert row.disagreement_score == d("0.450000")
    assert row.calibration_available_ratio == d("0.000000")
    assert row.average_calibration_error is None
    assert row.max_risk_score == d("0.700000")
    assert row.status == "blocked"
    assert row.reason_codes == (
        "forecast_model_comparison_blocked",
        "high_disagreement_block",
        "input_manual_review_required",
        "missing_model_book_imbalance",
        "missing_model_manual_research",
        "risk_block",
        "signal_stale_watch",
        "uncalibrated_block",
    )


def test_watch_status_for_partial_calibration_and_moderate_disagreement() -> None:
    comparison = report(
        (
            signal(model_name="naive", probability=d("0.410000"), calibration_observation_count=d("50"), calibration_error=d("0.050000")),
            signal(model_name="book_imbalance", probability=d("0.600000"), calibration_observation_count=d("10"), calibration_error=d("0.050000")),
            signal(model_name="llm", probability=d("0.530000"), risk_score=d("0.350000")),
            signal(model_name="manual_research", probability=d("0.560000"), calibration_observation_count=d("40"), calibration_error=d("0.120000")),
        ),
    )

    row = comparison.rows[0]
    assert comparison.status == "watch"
    assert comparison.watch_count == d("1.000000")
    assert row.disagreement_score == d("0.190000")
    assert row.calibrated_signal_count == d("2.000000")
    assert row.calibration_available_ratio == d("0.500000")
    assert row.average_calibration_error == d("0.085000")
    assert row.max_risk_score == d("0.350000")
    assert row.status == "watch"
    assert row.reason_codes == (
        "calibration_partial_watch",
        "disagreement_watch",
        "forecast_model_comparison_watch",
        "risk_watch",
    )


def test_empty_input_returns_blocked_report_without_investment_advice() -> None:
    comparison = report(())

    payload = research_forecast_model_comparison_report_payload(comparison)
    encoded = json.dumps(payload, sort_keys=True)

    assert comparison.status == "blocked"
    assert comparison.next_step == "block_report_only_forecast_model_comparison"
    assert comparison.reason_codes == ("forecast_model_comparison_no_inputs",)
    assert comparison.reason_code_counts == (
        ResearchForecastModelComparisonReasonCodeCount(
            reason_code="forecast_model_comparison_no_inputs",
            count=d("1.000000"),
            market_ratio=d("1.000000"),
        ),
    )
    assert comparison.rows == ()
    assert "advice" not in encoded.lower()
    assert "order" not in encoded.lower()
    assert "wallet" not in encoded.lower()
    assert "trade" not in encoded.lower()


def test_payload_is_deterministic_public_and_decimal_only() -> None:
    comparison = report(
        (
            signal(market_id="z-market", model_name="naive", probability=d("0.300000")),
            signal(market_id="z-market", model_name="llm", probability=d("0.400000")),
            signal(market_id="a-market", model_name="naive", probability=d("0.520000"), calibration_observation_count=d("31"), calibration_error=d("0.040000")),
            signal(market_id="a-market", model_name="book_imbalance", probability=d("0.530000"), calibration_observation_count=d("35"), calibration_error=d("0.050000")),
            signal(market_id="a-market", model_name="llm", probability=d("0.540000"), calibration_observation_count=d("40"), calibration_error=d("0.060000")),
            signal(market_id="a-market", model_name="manual_research", probability=d("0.550000"), calibration_observation_count=d("45"), calibration_error=d("0.070000")),
        ),
    )

    payload = research_forecast_model_comparison_report_payload(comparison)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.market_id for row in comparison.rows) == ("a-market", "z-market")
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["coverage_ratio"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert tuple(
        (count.reason_code, count.count)
        for count in comparison.reason_code_counts
        if count.reason_code.startswith("missing_model_")
    ) == (
        ("missing_model_book_imbalance", d("1.000000")),
        ("missing_model_manual_research", d("1.000000")),
    )


def test_validation_rejects_bad_types_unknown_models_future_times_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="min_coverage_ratio"):
        config(min_coverage_ratio=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="risk_watch_threshold"):
        config(risk_watch_threshold=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="watch_disagreement_threshold"):
        config(watch_disagreement_threshold=d("0.400000"))
    with pytest.raises(ValueError, match="market_id"):
        signal(market_id=" market-alpha")
    with pytest.raises(ValueError, match="model_name"):
        signal(model_name="ensemble")
    with pytest.raises(ValueError, match="probability"):
        signal(probability=d("1.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        signal(observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((signal(),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        report((signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="calibration_observation_count"):
        signal(calibration_observation_count=d("1.5"))
    with pytest.raises(ValueError, match="calibration_error"):
        signal(calibration_error=d("0.100000"), calibration_observation_count=None)
    with pytest.raises(ValueError, match="reason_codes"):
        signal(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    comparison = report(
        (
            signal(model_name="naive", calibration_observation_count=d("120"), calibration_error=d("0.040000")),
            signal(model_name="book_imbalance", calibration_observation_count=d("80"), calibration_error=d("0.050000")),
            signal(model_name="llm", calibration_observation_count=d("60"), calibration_error=d("0.060000")),
            signal(model_name="manual_research", calibration_observation_count=d("40"), calibration_error=d("0.070000")),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        comparison.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        comparison.rows[0].disagreement_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="disagreement_score"):
        replace(comparison.rows[0], disagreement_score=d("0.200000"))
    with pytest.raises(ValueError, match="status"):
        replace(comparison, status="blocked")


def test_owned_module_has_no_network_filesystem_or_mutation_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_forecast_model_comparison_report.py"
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
        "auth",
        "wallet",
        "place_order",
        "cancel_order",
        "create_order",
        "submit_order",
        "live_trading",
        "investment_advice",
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
