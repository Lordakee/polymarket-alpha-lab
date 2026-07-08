from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_team_forecast_calibration_comparison_report import (
    ResearchTeamForecastCalibrationComparisonConfig,
    ResearchTeamForecastCalibrationComparisonReasonCodeCount,
    ResearchTeamForecastCalibrationComparisonReport,
    ResearchTeamForecastCalibrationComparisonRow,
    ResearchTeamForecastCalibrationObservation,
    build_research_team_forecast_calibration_comparison_report,
    research_team_forecast_calibration_comparison_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchTeamForecastCalibrationComparisonConfig:
    values = {
        "config_version": "research-team-forecast-calibration-comparison-v0",
        "min_sample_count": d("3"),
        "min_domain_count": d("2"),
        "pass_mean_absolute_error": d("0.200000"),
        "watch_mean_absolute_error": d("0.350000"),
        "min_review_quality_score": d("0.700000"),
        "min_confidence_interval_hit_rate": d("0.600000"),
        "max_mean_confidence_interval_width": d("0.500000"),
    }
    values.update(overrides)
    return ResearchTeamForecastCalibrationComparisonConfig(**values)


def observation(
    index: int,
    *,
    research_team_id: str = "team-alpha",
    model_id: str = "model-bayes",
    domain_id: str = "politics",
    forecast_probability: Decimal = d("0.900000"),
    resolved_outcome: Decimal = d("1"),
    review_quality_score: Decimal = d("0.900000"),
    confidence_lower: Decimal = d("0.750000"),
    confidence_upper: Decimal = d("1.000000"),
    observed_at: datetime | None = None,
    resolved_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
) -> ResearchTeamForecastCalibrationObservation:
    return ResearchTeamForecastCalibrationObservation(
        research_team_id=research_team_id,
        model_id=model_id,
        domain_id=domain_id,
        forecast_id=f"{research_team_id}-{model_id}-{domain_id}-{index:03d}",
        forecast_probability=forecast_probability,
        resolved_outcome=resolved_outcome,
        review_quality_score=review_quality_score,
        confidence_lower=confidence_lower,
        confidence_upper=confidence_upper,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(days=4)
        ),
        resolved_at=(
            resolved_at if resolved_at is not None else GENERATED_AT - timedelta(days=1)
        ),
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchTeamForecastCalibrationObservation, ...],
    *,
    cfg: ResearchTeamForecastCalibrationComparisonConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamForecastCalibrationComparisonReport:
    return build_research_team_forecast_calibration_comparison_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_summary() -> None:
    calibration_report = report(())

    assert type(calibration_report) is ResearchTeamForecastCalibrationComparisonReport
    assert calibration_report.generated_at == GENERATED_AT
    assert calibration_report.config_version == (
        "research-team-forecast-calibration-comparison-v0"
    )
    assert calibration_report.comparison_status == "blocked"
    assert calibration_report.observation_count == d("0")
    assert calibration_report.team_model_count == d("0")
    assert calibration_report.domain_count == d("0")
    assert calibration_report.pass_count == d("0")
    assert calibration_report.watch_count == d("0")
    assert calibration_report.blocked_count == d("0")
    assert calibration_report.mean_absolute_error is None
    assert calibration_report.mean_brier_score is None
    assert calibration_report.mean_review_quality_score is None
    assert calibration_report.mean_confidence_interval_width is None
    assert calibration_report.rows == ()
    assert calibration_report.reason_codes == ("no_calibration_observations",)
    assert calibration_report.reason_code_counts == (
        ResearchTeamForecastCalibrationComparisonReasonCodeCount(
            reason_code="no_calibration_observations",
            count=d("1"),
        ),
    )
    assert calibration_report.paper_only is True
    assert calibration_report.report_only is True
    assert calibration_report.readonly is True


def test_builder_compares_team_model_calibration_statuses_and_coverage() -> None:
    calibration_report = report(
        (
            observation(1, domain_id="politics", forecast_probability=d("0.900000")),
            observation(2, domain_id="politics", forecast_probability=d("0.850000")),
            observation(
                3,
                domain_id="economics",
                forecast_probability=d("0.100000"),
                resolved_outcome=d("0"),
                confidence_lower=d("0.000000"),
                confidence_upper=d("0.250000"),
            ),
            observation(
                4,
                domain_id="economics",
                forecast_probability=d("0.200000"),
                resolved_outcome=d("0"),
                confidence_lower=d("0.000000"),
                confidence_upper=d("0.300000"),
            ),
            observation(
                5,
                research_team_id="team-beta",
                model_id="model-linear",
                domain_id="sports",
                forecast_probability=d("0.900000"),
                resolved_outcome=d("0"),
                review_quality_score=d("0.450000"),
                confidence_lower=d("0.400000"),
                confidence_upper=d("1.000000"),
            ),
            observation(
                6,
                research_team_id="team-beta",
                model_id="model-linear",
                domain_id="sports",
                forecast_probability=d("0.800000"),
                resolved_outcome=d("0"),
                review_quality_score=d("0.450000"),
                confidence_lower=d("0.350000"),
                confidence_upper=d("0.950000"),
            ),
            observation(
                7,
                research_team_id="team-beta",
                model_id="model-linear",
                domain_id="sports",
                forecast_probability=d("0.200000"),
                review_quality_score=d("0.450000"),
                confidence_lower=d("0.000000"),
                confidence_upper=d("0.600000"),
            ),
            observation(
                8,
                research_team_id="team-beta",
                model_id="model-linear",
                domain_id="sports",
                forecast_probability=d("0.100000"),
                review_quality_score=d("0.450000"),
                confidence_lower=d("0.000000"),
                confidence_upper=d("0.550000"),
            ),
            observation(
                9,
                research_team_id="team-gamma",
                model_id="model-ensemble",
                domain_id="crypto",
                forecast_probability=d("0.800000"),
                review_quality_score=d("0.650000"),
                confidence_lower=d("0.650000"),
                confidence_upper=d("1.000000"),
            ),
            observation(
                10,
                research_team_id="team-gamma",
                model_id="model-ensemble",
                domain_id="crypto",
                forecast_probability=d("0.200000"),
                resolved_outcome=d("0"),
                review_quality_score=d("0.650000"),
                confidence_lower=d("0.000000"),
                confidence_upper=d("0.350000"),
            ),
            observation(
                11,
                research_team_id="team-gamma",
                model_id="model-ensemble",
                domain_id="crypto",
                forecast_probability=d("0.800000"),
                review_quality_score=d("0.650000"),
                confidence_lower=d("0.650000"),
                confidence_upper=d("1.000000"),
            ),
        ),
    )

    assert calibration_report.comparison_status == "blocked"
    assert calibration_report.observation_count == d("11")
    assert calibration_report.team_model_count == d("3")
    assert calibration_report.domain_count == d("4")
    assert calibration_report.pass_count == d("1")
    assert calibration_report.watch_count == d("1")
    assert calibration_report.blocked_count == d("1")
    assert calibration_report.mean_absolute_error == d("0.413636")
    assert tuple((row.research_team_id, row.model_id) for row in calibration_report.rows) == (
        ("team-alpha", "model-bayes"),
        ("team-beta", "model-linear"),
        ("team-gamma", "model-ensemble"),
    )

    pass_row, blocked_row, watch_row = calibration_report.rows
    assert type(pass_row) is ResearchTeamForecastCalibrationComparisonRow
    assert pass_row.sample_count == d("4")
    assert pass_row.domain_count == d("2")
    assert pass_row.mean_absolute_error == d("0.137500")
    assert pass_row.mean_brier_score == d("0.020625")
    assert pass_row.mean_signed_error == d("0.012500")
    assert pass_row.mean_review_quality_score == d("0.900000")
    assert pass_row.confidence_interval_hit_rate == d("1.000000")
    assert pass_row.mean_confidence_interval_width == d("0.262500")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("calibration_pass",)

    assert blocked_row.status == "blocked"
    assert blocked_row.mean_absolute_error == d("0.850000")
    assert blocked_row.reason_codes == (
        "calibration_error_blocked",
        "confidence_interval_miss",
        "low_review_quality",
        "narrow_domain_coverage",
        "wide_confidence_interval",
    )
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "low_review_quality",
        "narrow_domain_coverage",
    )


def test_payload_is_deterministic_decimal_string_only_and_public_safe() -> None:
    calibration_report = report(
        (
            observation(2, domain_id="economics", forecast_probability=d("0.100000"), resolved_outcome=d("0"), confidence_lower=d("0.000000"), confidence_upper=d("0.250000")),
            observation(1, domain_id="politics", forecast_probability=d("0.900000")),
            observation(3, domain_id="politics", forecast_probability=d("0.850000")),
        ),
    )

    payload = research_team_forecast_calibration_comparison_report_payload(
        calibration_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["mean_absolute_error"] == "0.116667"
    assert payload["rows"][0]["sample_count"] == "3"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert ": 0." not in encoded
    assert "wallet" not in encoded.lower()
    assert "auth" not in encoded.lower()
    assert "order" not in encoded.lower()

    with pytest.raises(ValueError, match="unsafe public field|unsafe public value"):
        research_team_forecast_calibration_comparison_report_payload(
            {"paper_only": True, "report_only": True, "readonly": True, "wallet": "x"},
        )


def test_validation_rejects_bad_types_dates_ranges_duplicates_and_flags() -> None:
    with pytest.raises(ValueError, match="pass_mean_absolute_error"):
        config(pass_mean_absolute_error=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_mean_absolute_error"):
        config(watch_mean_absolute_error=_DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="forecast_probability"):
        observation(1, forecast_probability=d("1.1"))
    with pytest.raises(ValueError, match="resolved_outcome"):
        observation(1, resolved_outcome=d("0.5"))
    with pytest.raises(ValueError, match="confidence"):
        observation(
            1,
            forecast_probability=d("0.500000"),
            confidence_lower=d("0.600000"),
            confidence_upper=d("0.700000"),
        )
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 1))
    with pytest.raises(ValueError, match="resolved_at"):
        observation(
            1,
            observed_at=GENERATED_AT - timedelta(days=1),
            resolved_at=GENERATED_AT - timedelta(days=2),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)
    with pytest.raises(ValueError, match="forecast_id"):
        report((observation(1), observation(1)))
    with pytest.raises(ValueError, match="iterable"):
        build_research_team_forecast_calibration_comparison_report(
            "not rows",  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="ResearchTeamForecastCalibrationObservation"):
        build_research_team_forecast_calibration_comparison_report(
            (object(),),  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_research_team_forecast_calibration_comparison_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    calibration_report = report(
        (
            observation(1, domain_id="politics", forecast_probability=d("0.900000")),
            observation(2, domain_id="economics", forecast_probability=d("0.100000"), resolved_outcome=d("0"), confidence_lower=d("0.000000"), confidence_upper=d("0.250000")),
            observation(3, domain_id="politics", forecast_probability=d("0.850000")),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        calibration_report.comparison_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        calibration_report.rows[0].mean_absolute_error = d("1")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(calibration_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="sample_count"):
        replace(calibration_report.rows[0], sample_count=d("4"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(calibration_report, pass_count=d("0"))


def test_owned_module_has_no_network_write_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_forecast_calibration_comparison_report.py"
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
        "wallet",
        "auth",
        "order",
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
