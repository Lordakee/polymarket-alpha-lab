from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import inspect

import pytest

import polymarket_alpha_lab.market_research_energy_pipeline_pressure_drop_digest as module
from polymarket_alpha_lab.market_research_energy_pipeline_pressure_drop_digest import (
    EnergyPipelinePressureDropDigestReport,
    EnergyPipelinePressureDropDigestThresholds,
    EnergyPipelinePressureDropObservation,
    build_market_research_energy_pipeline_pressure_drop_digest_report,
    market_research_energy_pipeline_pressure_drop_digest_payload,
)


def _observation(
    *,
    pipeline_id: str = "gulf-coast-mainline",
    market_slug: str = "will-gulf-coast-gas-pipeline-face-disruption",
    region: str = "us-gulf-coast",
    observed_at: datetime = datetime(2026, 1, 1, 12, tzinfo=UTC),
    pressure_drop_ratio: Decimal = Decimal("0.120000"),
    flow_reduction_ratio: Decimal = Decimal("0.040000"),
    affected_capacity_mmcfd: Decimal = Decimal("80.000000"),
    repair_eta_hours: Decimal = Decimal("4.000000"),
    source_count: Decimal = Decimal("1"),
    source_confidence: Decimal = Decimal("0.700000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> EnergyPipelinePressureDropObservation:
    return EnergyPipelinePressureDropObservation(
        pipeline_id=pipeline_id,
        market_slug=market_slug,
        region=region,
        observed_at=observed_at,
        pressure_drop_ratio=pressure_drop_ratio,
        flow_reduction_ratio=flow_reduction_ratio,
        affected_capacity_mmcfd=affected_capacity_mmcfd,
        repair_eta_hours=repair_eta_hours,
        source_count=source_count,
        source_confidence=source_confidence,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_empty_digest_is_report_only_with_decimal_zeroes() -> None:
    generated_at = datetime(2026, 1, 1, 13, tzinfo=UTC)

    report = build_market_research_energy_pipeline_pressure_drop_digest_report(
        [],
        generated_at=generated_at,
    )

    assert report.generated_at == generated_at
    assert report.status == "no_observations"
    assert report.observation_count == Decimal("0")
    assert report.high_risk_count == Decimal("0")
    assert report.elevated_risk_count == Decimal("0")
    assert report.watch_count == Decimal("0")
    assert report.total_capacity_at_risk_mmcfd == Decimal("0")
    assert report.max_pressure_drop_ratio == Decimal("0")
    assert report.max_risk_score == Decimal("0")
    assert report.average_risk_score == Decimal("0")
    assert report.top_market_slug is None
    assert report.reason_codes == ("no_pressure_drop_observations",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = market_research_energy_pipeline_pressure_drop_digest_payload(report)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["observation_count"] == "0"
    assert payload["rows"] == []


def test_high_risk_pressure_drop_produces_screening_row() -> None:
    generated_at = datetime(2026, 1, 1, 13, tzinfo=UTC)
    observation = _observation(
        pressure_drop_ratio=Decimal("0.330000"),
        flow_reduction_ratio=Decimal("0.200000"),
        affected_capacity_mmcfd=Decimal("500.000000"),
        repair_eta_hours=Decimal("36.000000"),
        source_count=Decimal("3"),
        source_confidence=Decimal("0.920000"),
    )

    report = build_market_research_energy_pipeline_pressure_drop_digest_report(
        [observation],
        generated_at=generated_at,
    )

    assert report.status == "high_risk"
    assert report.observation_count == Decimal("1")
    assert report.high_risk_count == Decimal("1")
    assert report.elevated_risk_count == Decimal("0")
    assert report.watch_count == Decimal("0")
    assert report.top_market_slug == observation.market_slug
    assert report.max_pressure_drop_ratio == Decimal("0.330000")
    assert report.max_risk_score == Decimal("0.992000")
    assert report.total_capacity_at_risk_mmcfd == Decimal("500.000000")

    row = report.rows[0]
    assert row.screening_status == "high_risk"
    assert row.risk_score == Decimal("0.992000")
    assert row.reason_codes == (
        "pressure_drop_severe",
        "throughput_drop_elevated",
        "capacity_at_risk",
        "prolonged_repair_window",
        "multi_source_confirmation",
    )
    assert report.reason_codes == row.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_sorting_and_reason_codes_are_deterministic() -> None:
    generated_at = datetime(2026, 1, 2, 13, tzinfo=UTC)
    lower = _observation(
        pipeline_id="beta-pipeline",
        market_slug="beta-pipeline-disruption-risk",
        observed_at=datetime(2026, 1, 2, 8, tzinfo=UTC),
        pressure_drop_ratio=Decimal("0.120000"),
        flow_reduction_ratio=Decimal("0.060000"),
        affected_capacity_mmcfd=Decimal("50.000000"),
    )
    higher = _observation(
        pipeline_id="alpha-pipeline",
        market_slug="alpha-pipeline-disruption-risk",
        observed_at=datetime(2026, 1, 2, 7, tzinfo=UTC),
        pressure_drop_ratio=Decimal("0.260000"),
        flow_reduction_ratio=Decimal("0.110000"),
        affected_capacity_mmcfd=Decimal("300.000000"),
        repair_eta_hours=Decimal("30.000000"),
        source_count=Decimal("2"),
    )

    first = build_market_research_energy_pipeline_pressure_drop_digest_report(
        [lower, higher],
        generated_at=generated_at,
    )
    second = build_market_research_energy_pipeline_pressure_drop_digest_report(
        [higher, lower],
        generated_at=generated_at,
    )

    assert first == second
    assert [row.market_slug for row in first.rows] == [
        "alpha-pipeline-disruption-risk",
        "beta-pipeline-disruption-risk",
    ]
    assert first.reason_codes == (
        "pressure_drop_severe",
        "pressure_drop_elevated",
        "throughput_drop_elevated",
        "capacity_at_risk",
        "prolonged_repair_window",
        "multi_source_confirmation",
    )


def test_validation_rejects_non_decimal_naive_datetimes_and_sensitive_text() -> None:
    with pytest.raises(ValueError, match="pressure_drop_ratio.*Decimal"):
        _observation(pressure_drop_ratio=0.12)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at.*timezone-aware"):
        _observation(observed_at=datetime(2026, 1, 1, 12))

    with pytest.raises(ValueError, match="sensitive"):
        _observation(pipeline_id="api_key=secret")

    with pytest.raises(ValueError, match="EnergyPipelinePressureDropObservation"):
        build_market_research_energy_pipeline_pressure_drop_digest_report(
            [object()],  # type: ignore[list-item]
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
        build_market_research_energy_pipeline_pressure_drop_digest_report(
            [],
            generated_at=datetime(2026, 1, 1),
        )


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    report = build_market_research_energy_pipeline_pressure_drop_digest_report(
        [_observation()],
        generated_at=datetime(2026, 1, 1, 13, tzinfo=UTC),
    )

    with pytest.raises(FrozenInstanceError):
        report.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        _observation(paper_only=False)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    payload = market_research_energy_pipeline_pressure_drop_digest_payload(report)
    payload["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        market_research_energy_pipeline_pressure_drop_digest_payload(payload)


def test_non_default_thresholds_change_screening_status() -> None:
    generated_at = datetime(2026, 1, 1, 13, tzinfo=UTC)
    observation = _observation(
        pressure_drop_ratio=Decimal("0.120000"),
        flow_reduction_ratio=Decimal("0.040000"),
        affected_capacity_mmcfd=Decimal("80.000000"),
        repair_eta_hours=Decimal("4.000000"),
    )

    default_report = build_market_research_energy_pipeline_pressure_drop_digest_report(
        [observation],
        generated_at=generated_at,
    )
    custom_report = build_market_research_energy_pipeline_pressure_drop_digest_report(
        [observation],
        generated_at=generated_at,
        thresholds=EnergyPipelinePressureDropDigestThresholds(
            elevated_pressure_drop_ratio=Decimal("0.050000"),
            severe_pressure_drop_ratio=Decimal("0.100000"),
            elevated_flow_reduction_ratio=Decimal("0.030000"),
            capacity_at_risk_mmcfd=Decimal("75.000000"),
            prolonged_repair_eta_hours=Decimal("4.000000"),
            multi_source_confirmation_count=Decimal("2"),
            minimum_source_confidence=Decimal("0.600000"),
            elevated_risk_score=Decimal("0.250000"),
            high_risk_score=Decimal("0.400000"),
        ),
    )

    assert default_report.status == "elevated"
    assert default_report.high_risk_count == Decimal("0")
    assert custom_report.status == "high_risk"
    assert custom_report.high_risk_count == Decimal("1")
    assert custom_report.thresholds.high_risk_score == Decimal("0.400000")


def test_payload_rejects_float_int_and_unsafe_live_surface_fields() -> None:
    with pytest.raises(ValueError, match="float"):
        market_research_energy_pipeline_pressure_drop_digest_payload(
            {
                "generated_at": datetime(2026, 1, 1, tzinfo=UTC),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "risk_score": 0.5,
            },
        )

    with pytest.raises(ValueError, match="Decimal"):
        market_research_energy_pipeline_pressure_drop_digest_payload(
            {
                "generated_at": datetime(2026, 1, 1, tzinfo=UTC),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "observation_count": 1,
            },
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        market_research_energy_pipeline_pressure_drop_digest_payload(
            {
                "generated_at": datetime(2026, 1, 1, tzinfo=UTC),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet": "not allowed",
            },
        )


def test_payload_requires_report_or_mapping() -> None:
    with pytest.raises(ValueError, match="EnergyPipelinePressureDropDigestReport"):
        market_research_energy_pipeline_pressure_drop_digest_payload("not a report")

    assert EnergyPipelinePressureDropDigestReport.__dataclass_params__.frozen is True


def test_module_source_avoids_live_surface_tokens() -> None:
    source = inspect.getsource(module).lower()

    assert "wallet" not in source
    assert "private_key" not in source
