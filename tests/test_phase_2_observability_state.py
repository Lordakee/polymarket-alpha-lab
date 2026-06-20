from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest

from polymarket_alpha_lab.edge_cost_summary import PaperEdgeCostSummaryReport
from polymarket_alpha_lab.forecast_calibration import (
    PaperForecastCalibrationBucket,
    PaperForecastCalibrationReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    PaperPhase2EvidenceGapRow,
    PaperPhase2EvidenceSnapshotReport,
)
from polymarket_alpha_lab.phase_2_observability_trends import (
    PaperPhase2ObservabilityTrendsConfig,
    PaperPhase2ObservabilityTrendsReport,
    build_paper_phase_2_observability_trends_report,
)
from polymarket_alpha_lab.strategy_segment_summary import (
    PaperStrategySegmentRow,
    PaperStrategySegmentSummaryReport,
)


GENERATED_AT = datetime(2026, 6, 18, 19, 0, tzinfo=UTC)


def _api() -> tuple[type[Any], type[Any], Any]:
    module = import_module("polymarket_alpha_lab.phase_2_observability_state")
    return (
        module.PaperPhase2ObservabilityStateConfig,
        module.PaperPhase2ObservabilityStateReport,
        module.build_paper_phase_2_observability_state_report,
    )


def _config(**overrides: Any) -> Any:
    Config, _Report, _builder = _api()
    values = {"config_version": "phase-2-observability-state-v0"}
    values.update(overrides)
    return Config(**values)


def _build_source_report(
    *,
    calibration_reports: tuple[PaperForecastCalibrationReport, ...] = (),
    segment_summary_reports: tuple[PaperStrategySegmentSummaryReport, ...] = (),
    evidence_snapshots: tuple[PaperPhase2EvidenceSnapshotReport, ...] = (),
    edge_cost_reports: tuple[PaperEdgeCostSummaryReport, ...] = (),
) -> PaperPhase2ObservabilityTrendsReport:
    return build_paper_phase_2_observability_trends_report(
        calibration_reports,
        segment_summary_reports,
        evidence_snapshots,
        edge_cost_reports,
        config=PaperPhase2ObservabilityTrendsConfig(
            config_version="phase-2-observability-trends-v0",
        ),
        generated_at=GENERATED_AT,
    )


def _build_report(
    observability_trends: PaperPhase2ObservabilityTrendsReport | Any | None = None,
    *,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    _Config, _Report, builder = _api()
    return builder(
        _build_source_report() if observability_trends is None else observability_trends,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def _calibration_report(**overrides: Any) -> PaperForecastCalibrationReport:
    buckets = (
        PaperForecastCalibrationBucket(
            bucket_label="0.5000-0.7000",
            lower_probability=Decimal("0.5000"),
            upper_probability=Decimal("0.7000"),
            observation_count=30,
            mean_predicted_probability=Decimal("0.600000"),
            observed_frequency=Decimal("0.680000"),
            bucket_error=Decimal("0.080000"),
            bucket_weight=Decimal("1.000000"),
        ),
    )
    values = {
        "generated_at": datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "config_version": "forecast-calibration-v0",
        "observation_count": 30,
        "first_observed_at": datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
        "last_observed_at": datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "brier_score": Decimal("0.120000"),
        "mean_absolute_error": Decimal("0.220000"),
        "expected_calibration_error": Decimal("0.080000"),
        "max_bucket_error": Decimal("0.080000"),
        "bucket_count": 1,
        "status": "calibration_evidence_observed",
        "buckets": buckets,
    }
    values.update(overrides)
    return PaperForecastCalibrationReport(**values)


def _segment_summary_report(
    *,
    row_status: str = "segment_evidence_observed",
    probability_observation_count: int = 10,
    **overrides: Any,
) -> PaperStrategySegmentSummaryReport:
    has_probability = probability_observation_count > 0
    probability_fields = (
        {
            "mean_predicted_probability": Decimal("0.600000"),
            "observed_frequency": Decimal("0.700000"),
            "brier_score": Decimal("0.180000"),
        }
        if has_probability
        else {
            "mean_predicted_probability": None,
            "observed_frequency": None,
            "brier_score": None,
        }
    )
    rows = (
        PaperStrategySegmentRow(
            segment_type="strategy_type",
            segment_name="mean_reversion",
            observation_count=10,
            probability_observation_count=probability_observation_count,
            return_observation_count=10,
            **probability_fields,
            mean_paper_return_ratio=Decimal("0.040000"),
            positive_return_rate=Decimal("1.000000"),
            status=row_status,
        ),
    )
    values = {
        "generated_at": datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        "config_version": "strategy-segment-summary-v0",
        "observation_count": 10,
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


def _evidence_snapshot(
    *,
    gap_names: tuple[str, ...] = (),
    status: str = "phase_2_evidence_observed",
    calibration_status: str = "calibration_evidence_observed",
    **overrides: Any,
) -> PaperPhase2EvidenceSnapshotReport:
    values = {
        "generated_at": datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "config_version": "phase-2-evidence-snapshot-v0",
        "status": status,
        "calibration_report_present": True,
        "segment_summary_report_present": True,
        "calibration_observation_count": 30,
        "calibration_status": calibration_status,
        "segment_observation_count": 10,
        "segment_count": 1,
        "probability_segment_count": 1,
        "return_only_segment_count": 0,
        "thin_probability_segment_count": 0,
        "probability_segment_coverage_ratio": Decimal("1.000000"),
        "return_only_segment_ratio": Decimal("0.000000"),
        "evidence_gap_count": len(gap_names),
        "evidence_gap_names": gap_names,
        "evidence_gaps": _gap_rows(*gap_names),
    }
    values.update(overrides)
    return PaperPhase2EvidenceSnapshotReport(**values)


def _edge_cost_report(**overrides: Any) -> PaperEdgeCostSummaryReport:
    overrides = _edge_cost_overrides_for_current_schema(overrides)
    values = {
        "generated_at": datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
        "config_version": "edge-cost-summary-v0",
        "edge_observation_count": 4,
        "first_observed_at": datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
        "latest_observed_at": datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "unique_market_count": 1,
        "unique_strategy_count": 1,
        "unique_risk_tag_count": 1,
        "mean_theoretical_edge_ratio": Decimal("0.080000"),
        "mean_executable_edge_ratio": Decimal("0.050000"),
        "mean_edge_cost_gap": Decimal("0.030000"),
        "worst_edge_cost_gap": Decimal("0.030000"),
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
    if "mean_edge_cost_gap" in overrides and "worst_edge_cost_gap" not in overrides:
        values["worst_edge_cost_gap"] = values["mean_edge_cost_gap"]
    if (
        "mean_residual_exposure_ratio" in overrides
        and "worst_residual_exposure_ratio" not in overrides
    ):
        values["worst_residual_exposure_ratio"] = values[
            "mean_residual_exposure_ratio"
        ]
    return PaperEdgeCostSummaryReport(**values)


def _edge_cost_overrides_for_current_schema(overrides: dict[str, Any]) -> dict[str, Any]:
    values = dict(overrides)
    field_aliases = {
        "last_observed_at": "latest_observed_at",
        "mean_edge_cost_drag": "mean_edge_cost_gap",
        "negative_executable_edge_rate": "negative_executable_edge_ratio",
        "low_fill_probability_rate": "low_fill_probability_ratio",
        "high_residual_exposure_rate": "high_residual_exposure_ratio",
        "positive_paper_return_rate": "positive_paper_return_ratio",
    }
    for old_name, new_name in field_aliases.items():
        if old_name in values:
            values[new_name] = values.pop(old_name)
    status_aliases = {
        "empty_edge_cost_history": "empty_edge_cost_summary",
        "insufficient_edge_cost_sample": "edge_cost_summary_observed",
        "edge_cost_evidence_observed": "edge_cost_summary_observed",
        "edge_cost_quality_flags": "edge_cost_summary_observed",
    }
    if values.get("status") in status_aliases:
        values["status"] = status_aliases[values["status"]]
    return values


def _ready_source_report() -> PaperPhase2ObservabilityTrendsReport:
    return _build_source_report(
        calibration_reports=(_calibration_report(),),
        segment_summary_reports=(_segment_summary_report(),),
        evidence_snapshots=(_evidence_snapshot(),),
        edge_cost_reports=(_edge_cost_report(),),
    )


def test_empty_trends_are_not_ready_with_missing_reasons():
    _Config, Report, _builder = _api()

    report = _build_report(_build_source_report())

    assert isinstance(report, Report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "phase-2-observability-state-v0"
    assert report.source_config_version == "phase-2-observability-trends-v0"
    assert report.calibration_report_count == 0
    assert report.segment_summary_report_count == 0
    assert report.evidence_snapshot_report_count == 0
    assert report.edge_cost_report_count == 0
    assert report.latest_calibration_status is None
    assert report.latest_segment_status is None
    assert report.latest_evidence_status is None
    assert report.latest_edge_cost_status is None
    assert report.evidence_gap_count == 0
    assert report.latest_evidence_gap_names == ()
    assert report.phase_2_ready is False
    assert report.blocking_reason_names == (
        "missing_calibration_trend",
        "missing_segment_summary_trend",
        "missing_evidence_snapshot_trend",
        "missing_edge_cost_summary_trend",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_fully_observed_trends_are_ready():
    report = _build_report(_ready_source_report())

    assert report.calibration_report_count == 1
    assert report.segment_summary_report_count == 1
    assert report.evidence_snapshot_report_count == 1
    assert report.edge_cost_report_count == 1
    assert report.latest_calibration_status == "calibration_evidence_observed"
    assert report.latest_segment_status == "segment_evidence_observed"
    assert report.latest_evidence_status == "phase_2_evidence_observed"
    assert report.latest_edge_cost_status == "edge_cost_evidence_observed"
    assert report.evidence_gap_count == 0
    assert report.latest_evidence_gap_names == ()
    assert report.phase_2_ready is True
    assert report.blocking_reason_names == ()


def test_generated_at_is_normalized_to_utc():
    report = _build_report(
        _ready_source_report(),
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC


@pytest.mark.parametrize(
    ("scenario", "expected_reasons"),
    (
        ("calibration_empty", ("calibration_not_observed",)),
        ("segment_incomplete", ("segment_not_observed",)),
        (
            "evidence_quality_flags",
            ("evidence_not_observed", "evidence_gaps_present"),
        ),
        ("evidence_gaps", ("evidence_not_observed", "evidence_gaps_present")),
        ("edge_cost_quality_flags", ("edge_cost_not_observed",)),
    ),
)
def test_non_observed_latest_conditions_add_deterministic_reasons(
    scenario: str,
    expected_reasons: tuple[str, ...],
):
    source_report_by_scenario = {
        "calibration_empty": _build_source_report(
            calibration_reports=(
                _calibration_report(
                    observation_count=0,
                    first_observed_at=None,
                    last_observed_at=None,
                    brier_score=None,
                    mean_absolute_error=None,
                    expected_calibration_error=None,
                    max_bucket_error=None,
                    bucket_count=0,
                    buckets=(),
                    status="empty_calibration_history",
                ),
            ),
            segment_summary_reports=(_segment_summary_report(),),
            evidence_snapshots=(_evidence_snapshot(),),
            edge_cost_reports=(_edge_cost_report(),),
        ),
        "segment_incomplete": _build_source_report(
            calibration_reports=(_calibration_report(),),
            segment_summary_reports=(
                _segment_summary_report(
                    row_status="insufficient_segment_probability_sample",
                    probability_observation_count=1,
                ),
            ),
            evidence_snapshots=(_evidence_snapshot(),),
            edge_cost_reports=(_edge_cost_report(),),
        ),
        "evidence_quality_flags": _build_source_report(
            calibration_reports=(_calibration_report(),),
            segment_summary_reports=(_segment_summary_report(),),
            evidence_snapshots=(
                _evidence_snapshot(
                    status="phase_2_evidence_quality_flags",
                    calibration_status="calibration_quality_flags",
                    gap_names=("calibration_quality_flags_present",),
                ),
            ),
            edge_cost_reports=(_edge_cost_report(),),
        ),
        "evidence_gaps": _build_source_report(
            calibration_reports=(_calibration_report(),),
            segment_summary_reports=(_segment_summary_report(),),
            evidence_snapshots=(
                _evidence_snapshot(
                    status="phase_2_evidence_gaps",
                    gap_names=("thin_segment_probability_samples",),
                    thin_probability_segment_count=1,
                ),
            ),
            edge_cost_reports=(_edge_cost_report(),),
        ),
            "edge_cost_quality_flags": _build_source_report(
                calibration_reports=(_calibration_report(),),
                segment_summary_reports=(_segment_summary_report(),),
                evidence_snapshots=(_evidence_snapshot(),),
                edge_cost_reports=(
                    _edge_cost_report(
                        edge_observation_count=4,
                        negative_executable_edge_count=1,
                        negative_executable_edge_rate=Decimal("0.250000"),
                        low_fill_probability_count=1,
                        low_fill_probability_rate=Decimal("0.250000"),
                        high_residual_exposure_count=0,
                        high_residual_exposure_rate=Decimal("0.000000"),
                        positive_paper_return_count=3,
                        positive_paper_return_rate=Decimal("0.750000"),
                        status="edge_cost_quality_flags",
                    ),
                ),
            ),
    }
    source_report = source_report_by_scenario[scenario]

    report = _build_report(source_report)

    assert report.phase_2_ready is False
    assert report.blocking_reason_names == expected_reasons


def test_latest_evidence_gap_names_are_carried_in_deterministic_order():
    source_report = _build_source_report(
        calibration_reports=(_calibration_report(),),
        segment_summary_reports=(_segment_summary_report(),),
        evidence_snapshots=(
            _evidence_snapshot(
                status="phase_2_evidence_gaps",
                gap_names=(
                    "thin_calibration_sample",
                    "thin_segment_probability_samples",
                ),
                calibration_observation_count=10,
                thin_probability_segment_count=1,
            ),
        ),
        edge_cost_reports=(_edge_cost_report(),),
    )

    report = _build_report(source_report)

    assert report.evidence_gap_count == 2
    assert report.latest_evidence_gap_names == (
        "thin_calibration_sample",
        "thin_segment_probability_samples",
    )
    assert report.blocking_reason_names == (
        "evidence_not_observed",
        "evidence_gaps_present",
    )


def test_builder_uses_exact_types_and_revalidates_source_flags():
    with pytest.raises(ValueError, match="observability_trends"):
        _build_report(object())

    with pytest.raises(ValueError, match="config"):
        _build_report(_ready_source_report(), config=object())

    with pytest.raises(ValueError, match="generated_at"):
        _build_report(_ready_source_report(), generated_at="now")

    source_report = _ready_source_report()
    object.__setattr__(source_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        _build_report(source_report)


def test_report_is_frozen_and_revalidates_exact_types_and_flags():
    _Config, Report, _builder = _api()
    report = _build_report(_ready_source_report())

    with pytest.raises(FrozenInstanceError):
        report.config_version = "changed"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="phase_2_ready"):
        replace(report, phase_2_ready=1)
    with pytest.raises(ValueError, match="blocking_reason_names"):
        replace(report, blocking_reason_names=("unknown_reason",))
    with pytest.raises(ValueError, match="latest_evidence_gap_names"):
        replace(report, latest_evidence_gap_names=("not_a_gap",))
    with pytest.raises(ValueError, match="latest_calibration_status"):
        replace(report, calibration_report_count=0)
    with pytest.raises(ValueError, match="blocking_reason_names"):
        replace(
            report,
            latest_evidence_status="phase_2_evidence_gaps",
            evidence_gap_count=1,
            latest_evidence_gap_names=("thin_segment_probability_samples",),
            phase_2_ready=False,
            blocking_reason_names=("evidence_not_observed",),
        )
    with pytest.raises(ValueError, match="latest_calibration_status"):
        replace(
            report,
            calibration_report_count=0,
            phase_2_ready=False,
            blocking_reason_names=("missing_calibration_trend",),
        )
    with pytest.raises(ValueError, match="latest_segment_status"):
        replace(
            report,
            latest_segment_status=None,
            phase_2_ready=False,
            blocking_reason_names=("segment_not_observed",),
        )
    empty_report = _build_report(_build_source_report())
    with pytest.raises(ValueError, match="latest_evidence_gap_names"):
        replace(
            empty_report,
            evidence_gap_count=1,
            latest_evidence_gap_names=("thin_segment_probability_samples",),
            blocking_reason_names=(
                "missing_calibration_trend",
                "missing_segment_summary_trend",
                "missing_evidence_snapshot_trend",
                "missing_edge_cost_summary_trend",
                "evidence_gaps_present",
            ),
        )

    class StringSubclass(str):
        pass

    with pytest.raises(ValueError, match="config_version"):
        Report(
            generated_at=GENERATED_AT,
            config_version=StringSubclass("phase-2-observability-state-v0"),
            source_config_version="phase-2-observability-trends-v0",
            calibration_report_count=1,
            segment_summary_report_count=1,
            evidence_snapshot_report_count=1,
            edge_cost_report_count=1,
            latest_calibration_status="calibration_evidence_observed",
            latest_segment_status="segment_evidence_observed",
            latest_evidence_status="phase_2_evidence_observed",
            latest_edge_cost_status="edge_cost_evidence_observed",
            evidence_gap_count=0,
            latest_evidence_gap_names=(),
            phase_2_ready=True,
            blocking_reason_names=(),
        )

    with pytest.raises(ValueError, match="config_version"):
        Report(
            generated_at=GENERATED_AT,
            config_version=" phase-2-observability-state-v0 ",
            source_config_version="phase-2-observability-trends-v0",
            calibration_report_count=1,
            segment_summary_report_count=1,
            evidence_snapshot_report_count=1,
            edge_cost_report_count=1,
            latest_calibration_status="calibration_evidence_observed",
            latest_segment_status="segment_evidence_observed",
            latest_evidence_status="phase_2_evidence_observed",
            latest_edge_cost_status="edge_cost_evidence_observed",
            evidence_gap_count=0,
            latest_evidence_gap_names=(),
            phase_2_ready=True,
            blocking_reason_names=(),
        )


def test_local_all_and_package_root_non_export():
    module = import_module("polymarket_alpha_lab.phase_2_observability_state")

    assert module.__all__ == (
        "PaperPhase2ObservabilityStateConfig",
        "PaperPhase2ObservabilityStateReport",
        "build_paper_phase_2_observability_state_report",
    )
    with pytest.raises(ValueError, match="config_version"):
        module.PaperPhase2ObservabilityStateConfig(
            config_version=" phase-2-observability-state-v0 ",
        )

    package_root = import_module("polymarket_alpha_lab")
    assert not hasattr(package_root, "PaperPhase2ObservabilityStateConfig")
    assert not hasattr(package_root, "PaperPhase2ObservabilityStateReport")
    assert not hasattr(
        package_root,
        "build_paper_phase_2_observability_state_report",
    )
