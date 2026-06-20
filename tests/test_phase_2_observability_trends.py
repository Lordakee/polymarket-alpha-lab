from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest

from polymarket_alpha_lab.edge_cost_summary import PaperEdgeCostSummaryReport
from polymarket_alpha_lab.edge_cost_summary_trend import PaperEdgeCostSummaryTrendReport
from polymarket_alpha_lab.forecast_calibration import PaperForecastCalibrationReport
from polymarket_alpha_lab.forecast_calibration_trend import (
    PaperForecastCalibrationTrendReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    PaperPhase2EvidenceGapRow,
    PaperPhase2EvidenceSnapshotReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_trend import (
    PaperPhase2EvidenceSnapshotTrendReport,
)
from polymarket_alpha_lab.strategy_segment_summary import (
    PaperStrategySegmentSummaryReport,
    PaperStrategySegmentRow,
)
from polymarket_alpha_lab.strategy_segment_summary_trend import (
    PaperStrategySegmentSummaryTrendReport,
)


GENERATED_AT = datetime(2026, 6, 18, 19, 0, tzinfo=UTC)


def _api() -> tuple[type[Any], type[Any], Any]:
    module = import_module("polymarket_alpha_lab.phase_2_observability_trends")
    return (
        module.PaperPhase2ObservabilityTrendsConfig,
        module.PaperPhase2ObservabilityTrendsReport,
        module.build_paper_phase_2_observability_trends_report,
    )


def _config(**overrides: Any) -> Any:
    Config, _Report, _builder = _api()
    values = {"config_version": "phase-2-observability-trends-v0"}
    values.update(overrides)
    return Config(**values)


def _build_report(
    *,
    calibration_reports: list[PaperForecastCalibrationReport]
    | tuple[PaperForecastCalibrationReport, ...] = (),
    segment_summary_reports: list[PaperStrategySegmentSummaryReport]
    | tuple[PaperStrategySegmentSummaryReport, ...] = (),
    evidence_snapshots: list[PaperPhase2EvidenceSnapshotReport]
    | tuple[PaperPhase2EvidenceSnapshotReport, ...] = (),
    edge_cost_reports: list[PaperEdgeCostSummaryReport]
    | tuple[PaperEdgeCostSummaryReport, ...] = (),
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    _Config, _Report, builder = _api()
    return builder(
        calibration_reports,
        segment_summary_reports,
        evidence_snapshots,
        edge_cost_reports,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def _calibration_report(**overrides: Any) -> PaperForecastCalibrationReport:
    values = {
        "generated_at": datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "config_version": "forecast-calibration-v0",
        "observation_count": 0,
        "first_observed_at": None,
        "last_observed_at": None,
        "brier_score": None,
        "mean_absolute_error": None,
        "expected_calibration_error": None,
        "max_bucket_error": None,
        "bucket_count": 0,
        "status": "empty_calibration_history",
        "buckets": (),
    }
    values.update(overrides)
    return PaperForecastCalibrationReport(**values)


def _segment_summary_report(**overrides: Any) -> PaperStrategySegmentSummaryReport:
    rows = (
        PaperStrategySegmentRow(
            segment_type="strategy_type",
            segment_name="mean_reversion",
            observation_count=3,
            probability_observation_count=3,
            return_observation_count=3,
            mean_predicted_probability=Decimal("0.600000"),
            observed_frequency=Decimal("0.666667"),
            brier_score=Decimal("0.240000"),
            mean_paper_return_ratio=Decimal("0.040000"),
            positive_return_rate=Decimal("1.000000"),
            status="segment_evidence_observed",
        ),
    )
    values = {
        "generated_at": datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        "config_version": "strategy-segment-summary-v0",
        "observation_count": 3,
        "strategy_segment_count": 1,
        "risk_tag_segment_count": 0,
        "first_observed_at": datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
        "last_observed_at": datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return PaperStrategySegmentSummaryReport(**values)


def _gap_rows(*present_gap_names: str) -> tuple[PaperPhase2EvidenceGapRow, ...]:
    present = set(present_gap_names)
    return tuple(
        PaperPhase2EvidenceGapRow(
            evidence_gap_name=gap_name,
            gap_present=gap_name in present,
        )
        for gap_name in EVIDENCE_GAP_NAMES
    )


def _evidence_snapshot(**overrides: Any) -> PaperPhase2EvidenceSnapshotReport:
    values = {
        "generated_at": datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "config_version": "phase-2-evidence-snapshot-v0",
        "status": "phase_2_evidence_observed",
        "calibration_report_present": True,
        "segment_summary_report_present": True,
        "calibration_observation_count": 30,
        "calibration_status": "calibration_evidence_observed",
        "segment_observation_count": 2,
        "segment_count": 2,
        "probability_segment_count": 2,
        "return_only_segment_count": 0,
        "thin_probability_segment_count": 0,
        "probability_segment_coverage_ratio": Decimal("1.000000"),
        "return_only_segment_ratio": Decimal("0.000000"),
        "evidence_gap_count": 0,
        "evidence_gap_names": (),
        "evidence_gaps": _gap_rows(),
    }
    values.update(overrides)
    return PaperPhase2EvidenceSnapshotReport(**values)


def _edge_cost_report(**overrides: Any) -> PaperEdgeCostSummaryReport:
    values = {
        "generated_at": datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
        "config_version": "edge-cost-summary-v0",
        "edge_observation_count": 4,
        "first_observed_at": datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
        "latest_observed_at": datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "unique_market_count": 2,
        "unique_strategy_count": 2,
        "unique_risk_tag_count": 2,
        "mean_theoretical_edge_ratio": Decimal("0.080000"),
        "mean_executable_edge_ratio": Decimal("0.050000"),
        "mean_edge_cost_gap": Decimal("0.030000"),
        "worst_edge_cost_gap": Decimal("0.050000"),
        "mean_fill_probability": Decimal("0.750000"),
        "mean_residual_exposure_ratio": Decimal("0.100000"),
        "worst_residual_exposure_ratio": Decimal("0.100000"),
        "mean_paper_return_ratio": Decimal("0.010000"),
        "negative_executable_edge_count": 0,
        "negative_executable_edge_ratio": Decimal("0.000000"),
        "low_fill_probability_count": 0,
        "low_fill_probability_ratio": Decimal("0.000000"),
        "high_residual_exposure_count": 0,
        "high_residual_exposure_ratio": Decimal("0.000000"),
        "positive_paper_return_count": 3,
        "positive_paper_return_ratio": Decimal("0.750000"),
        "status": "edge_cost_summary_observed",
    }
    values.update(overrides)
    return PaperEdgeCostSummaryReport(**values)


def test_phase_2_observability_trends_empty_histories_delegate_to_child_trends():
    _Config, Report, _builder = _api()

    report = _build_report()

    assert isinstance(report, Report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "phase-2-observability-trends-v0"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert isinstance(
        report.forecast_calibration_trend,
        PaperForecastCalibrationTrendReport,
    )
    assert (
        report.forecast_calibration_trend.config_version
        == "phase-2-forecast-calibration-trend-v0"
    )
    assert report.forecast_calibration_trend.calibration_report_count == 0
    assert report.forecast_calibration_trend.paper_only is True
    assert report.forecast_calibration_trend.report_only is True
    assert report.forecast_calibration_trend.readonly is True

    assert isinstance(
        report.strategy_segment_summary_trend,
        PaperStrategySegmentSummaryTrendReport,
    )
    assert (
        report.strategy_segment_summary_trend.config_version
        == "phase-2-strategy-segment-summary-trend-v0"
    )
    assert report.strategy_segment_summary_trend.segment_summary_report_count == 0
    assert report.strategy_segment_summary_trend.paper_only is True
    assert report.strategy_segment_summary_trend.report_only is True
    assert report.strategy_segment_summary_trend.readonly is True

    assert isinstance(
        report.phase_2_evidence_snapshot_trend,
        PaperPhase2EvidenceSnapshotTrendReport,
    )
    assert (
        report.phase_2_evidence_snapshot_trend.config_version
        == "phase-2-evidence-snapshot-trend-v0"
    )
    assert report.phase_2_evidence_snapshot_trend.snapshot_report_count == 0
    assert report.phase_2_evidence_snapshot_trend.paper_only is True
    assert report.phase_2_evidence_snapshot_trend.report_only is True
    assert report.phase_2_evidence_snapshot_trend.readonly is True

    assert isinstance(report.edge_cost_summary_trend, PaperEdgeCostSummaryTrendReport)
    assert (
        report.edge_cost_summary_trend.config_version
        == "phase-2-edge-cost-summary-trend-v0"
    )
    assert report.edge_cost_summary_trend.edge_cost_report_count == 0
    assert report.edge_cost_summary_trend.paper_only is True
    assert report.edge_cost_summary_trend.report_only is True
    assert report.edge_cost_summary_trend.readonly is True


def test_phase_2_observability_trends_child_reports_are_exact_trend_types():
    report = _build_report()

    assert type(report.forecast_calibration_trend) is PaperForecastCalibrationTrendReport
    assert (
        type(report.strategy_segment_summary_trend)
        is PaperStrategySegmentSummaryTrendReport
    )
    assert (
        type(report.phase_2_evidence_snapshot_trend)
        is PaperPhase2EvidenceSnapshotTrendReport
    )
    assert type(report.edge_cost_summary_trend) is PaperEdgeCostSummaryTrendReport


def test_phase_2_observability_trends_normalizes_generated_at_to_utc():
    generated_at = datetime(2026, 6, 18, 15, 0, tzinfo=timezone(-timedelta(hours=4)))

    report = _build_report(generated_at=generated_at)

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.forecast_calibration_trend.generated_at == GENERATED_AT
    assert report.forecast_calibration_trend.generated_at.tzinfo is UTC
    assert report.strategy_segment_summary_trend.generated_at == GENERATED_AT
    assert report.strategy_segment_summary_trend.generated_at.tzinfo is UTC
    assert report.phase_2_evidence_snapshot_trend.generated_at == GENERATED_AT
    assert report.phase_2_evidence_snapshot_trend.generated_at.tzinfo is UTC
    assert report.edge_cost_summary_trend.generated_at == GENERATED_AT
    assert report.edge_cost_summary_trend.generated_at.tzinfo is UTC


def test_phase_2_observability_trends_delegates_nonempty_histories():
    report = _build_report(
        calibration_reports=(_calibration_report(),),
        segment_summary_reports=(_segment_summary_report(),),
        evidence_snapshots=(_evidence_snapshot(),),
        edge_cost_reports=(_edge_cost_report(),),
    )

    assert report.forecast_calibration_trend.calibration_report_count == 1
    assert report.forecast_calibration_trend.latest_status == "empty_calibration_history"
    assert report.strategy_segment_summary_trend.segment_summary_report_count == 1
    assert (
        report.strategy_segment_summary_trend.latest_status
        == "segment_evidence_observed"
    )
    assert report.phase_2_evidence_snapshot_trend.snapshot_report_count == 1
    assert (
        report.phase_2_evidence_snapshot_trend.latest_status
        == "phase_2_evidence_observed"
    )
    assert report.edge_cost_summary_trend.edge_cost_report_count == 1
    assert report.edge_cost_summary_trend.latest_status == "edge_cost_evidence_observed"
    assert report.edge_cost_summary_trend.latest_mean_edge_cost_drag == Decimal("0.030000")
    assert report.edge_cost_summary_trend.latest_positive_paper_return_rate == Decimal(
        "0.750000",
    )


def test_phase_2_observability_trends_edge_cost_history_is_optional():
    _Config, Report, builder = _api()

    report = builder(
        (),
        (),
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, Report)
    assert report.edge_cost_summary_trend.edge_cost_report_count == 0


def test_phase_2_observability_trends_rejects_invalid_builder_inputs():
    with pytest.raises(ValueError, match="config"):
        _build_report(config=object())

    with pytest.raises(ValueError, match="generated_at"):
        _build_report(generated_at="now")

    with pytest.raises(ValueError, match="PaperForecastCalibrationReport"):
        _build_report(calibration_reports=(object(),))

    with pytest.raises(ValueError, match="PaperStrategySegmentSummaryReport"):
        _build_report(segment_summary_reports=(object(),))

    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        _build_report(evidence_snapshots=(object(),))

    with pytest.raises(ValueError, match="PaperEdgeCostSummaryReport"):
        _build_report(edge_cost_reports=(object(),))


def test_phase_2_observability_trends_rejects_scalar_subclasses_at_public_boundaries():
    class ConfigVersion(str):
        pass

    class GeneratedAt(datetime):
        pass

    Config, Report, _builder = _api()
    report = _build_report()

    with pytest.raises(ValueError, match="config_version"):
        Config(config_version=ConfigVersion("phase-2-observability-trends-v0"))

    with pytest.raises(ValueError, match="generated_at"):
        _build_report(generated_at=GeneratedAt(2026, 6, 18, 19, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="generated_at"):
        Report(
            generated_at=GeneratedAt(2026, 6, 18, 19, 0, tzinfo=UTC),
            config_version="phase-2-observability-trends-v0",
            forecast_calibration_trend=report.forecast_calibration_trend,
            strategy_segment_summary_trend=report.strategy_segment_summary_trend,
            phase_2_evidence_snapshot_trend=report.phase_2_evidence_snapshot_trend,
            edge_cost_summary_trend=report.edge_cost_summary_trend,
        )

    with pytest.raises(ValueError, match="config_version"):
        Report(
            generated_at=GENERATED_AT,
            config_version=ConfigVersion("phase-2-observability-trends-v0"),
            forecast_calibration_trend=report.forecast_calibration_trend,
            strategy_segment_summary_trend=report.strategy_segment_summary_trend,
            phase_2_evidence_snapshot_trend=report.phase_2_evidence_snapshot_trend,
            edge_cost_summary_trend=report.edge_cost_summary_trend,
        )


def test_phase_2_observability_trends_rejects_source_reports_with_nonfinal_flags():
    calibration_report = _calibration_report()
    object.__setattr__(calibration_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _build_report(calibration_reports=(calibration_report,))

    segment_summary_report = _segment_summary_report()
    object.__setattr__(segment_summary_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _build_report(segment_summary_reports=(segment_summary_report,))

    evidence_snapshot = _evidence_snapshot()
    object.__setattr__(evidence_snapshot, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        _build_report(evidence_snapshots=(evidence_snapshot,))

    edge_cost_report = _edge_cost_report()
    object.__setattr__(edge_cost_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _build_report(edge_cost_reports=(edge_cost_report,))


def test_phase_2_observability_trends_report_validates_nested_types_and_flags():
    _Config, Report, _builder = _api()
    report = _build_report()

    with pytest.raises(ValueError, match="forecast_calibration_trend"):
        replace(
            report,
            forecast_calibration_trend=report.strategy_segment_summary_trend,
        )
    with pytest.raises(ValueError, match="strategy_segment_summary_trend"):
        replace(
            report,
            strategy_segment_summary_trend=report.forecast_calibration_trend,
        )
    with pytest.raises(ValueError, match="phase_2_evidence_snapshot_trend"):
        replace(
            report,
            phase_2_evidence_snapshot_trend=report.forecast_calibration_trend,
        )
    with pytest.raises(ValueError, match="edge_cost_summary_trend"):
        replace(
            report,
            edge_cost_summary_trend=report.forecast_calibration_trend,
        )

    tampered_child = replace(report.forecast_calibration_trend)
    object.__setattr__(tampered_child, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, forecast_calibration_trend=tampered_child)

    with pytest.raises(FrozenInstanceError):
        report.config_version = "changed"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="config_version"):
        Report(
            generated_at=GENERATED_AT,
            config_version=" phase-2-observability-trends-v0 ",
            forecast_calibration_trend=report.forecast_calibration_trend,
            strategy_segment_summary_trend=report.strategy_segment_summary_trend,
            phase_2_evidence_snapshot_trend=report.phase_2_evidence_snapshot_trend,
            edge_cost_summary_trend=report.edge_cost_summary_trend,
        )


def test_phase_2_observability_trends_all_is_module_local_only():
    module = import_module("polymarket_alpha_lab.phase_2_observability_trends")

    assert module.__all__ == (
        "PaperPhase2ObservabilityTrendsConfig",
        "PaperPhase2ObservabilityTrendsReport",
        "build_paper_phase_2_observability_trends_report",
    )

    with pytest.raises(ValueError, match="config_version"):
        module.PaperPhase2ObservabilityTrendsConfig(
            config_version=" phase-2-observability-trends-v0 ",
        )
