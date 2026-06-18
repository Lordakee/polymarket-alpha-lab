from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_calibration import (
    PaperForecastCalibrationConfig,
    build_paper_forecast_calibration_report,
)
from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation
from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    PaperPhase2EvidenceGapRow,
    PaperPhase2EvidenceSnapshotConfig,
    PaperPhase2EvidenceSnapshotReport,
    build_paper_phase_2_evidence_snapshot_report,
)
from polymarket_alpha_lab.strategy_segment_summary import (
    PaperStrategySegmentSummaryConfig,
    build_paper_strategy_segment_summary_report,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
GAP_NAMES = (
    "missing_calibration_report",
    "thin_calibration_sample",
    "calibration_quality_flags_present",
    "missing_segment_summary",
    "thin_segment_probability_samples",
    "return_only_segments_present",
)


def _config(**overrides):
    values = {"config_version": "phase-2-evidence-snapshot-v0"}
    values.update(overrides)
    return PaperPhase2EvidenceSnapshotConfig(**values)


def _observation(
    index: int,
    *,
    strategy_type: str = "book_imbalance_paper",
    risk_tags: tuple[str, ...] = ("thin_liquidity",),
    predicted_probability: Decimal | None = Decimal("0.7000"),
    actual_outcome_value: Decimal | None = Decimal("1"),
    paper_return_ratio: Decimal | None = Decimal("0.0100"),
) -> PaperForecastEvidenceObservation:
    probability_values = {}
    if predicted_probability is not None or actual_outcome_value is not None:
        probability_values = {
            "predicted_probability": predicted_probability,
            "actual_outcome_value": actual_outcome_value,
        }
    return_values = {}
    if paper_return_ratio is not None:
        return_values = {
            "theoretical_edge_ratio": Decimal("0.0500"),
            "executable_edge_ratio": Decimal("0.0300"),
            "fill_probability": Decimal("0.7500"),
            "residual_exposure_ratio": Decimal("0.0200"),
            "paper_return_ratio": paper_return_ratio,
        }
    return PaperForecastEvidenceObservation(
        observed_at=GENERATED_AT + timedelta(minutes=index),
        source_packet_id=f"packet-{index}",
        condition_id=f"condition-{index}",
        token_id=f"token-{index}",
        market_slug=f"market-{index}",
        strategy_type=strategy_type,
        risk_tags=risk_tags,
        **probability_values,
        **return_values,
    )


def _calibration_report(
    probability_count: int,
    *,
    actual: Decimal = Decimal("1"),
    min_observation_count: int = 1,
):
    return build_paper_forecast_calibration_report(
        (
            _observation(
                index,
                predicted_probability=Decimal("0.7000"),
                actual_outcome_value=actual,
                paper_return_ratio=None,
            )
            for index in range(probability_count)
        ),
        config=PaperForecastCalibrationConfig(
            config_version="forecast-calibration-test",
            min_observation_count=min_observation_count,
            max_brier_score=Decimal("0.250000"),
            max_expected_calibration_error=Decimal("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )


def _segment_summary_report(
    probability_count: int,
    *,
    return_only_count: int = 0,
    min_segment_observations: int = 1,
):
    probability_items = tuple(
        _observation(
            index,
            predicted_probability=Decimal("0.7000"),
            actual_outcome_value=Decimal("1"),
            paper_return_ratio=Decimal("0.0100"),
        )
        for index in range(probability_count)
    )
    return_only_items = tuple(
        _observation(
            100 + index,
            strategy_type="return_only_paper",
            risk_tags=("return_only",),
            predicted_probability=None,
            actual_outcome_value=None,
            paper_return_ratio=Decimal("0.0200"),
        )
        for index in range(return_only_count)
    )
    return build_paper_strategy_segment_summary_report(
        (*probability_items, *return_only_items),
        config=PaperStrategySegmentSummaryConfig(
            config_version="strategy-segment-summary-test",
            min_segment_observations=min_segment_observations,
        ),
        generated_at=GENERATED_AT,
    )


def _snapshot(
    calibration_report=None,
    segment_summary_report=None,
    *,
    config=None,
):
    return build_paper_phase_2_evidence_snapshot_report(
        calibration_report,
        segment_summary_report,
        config=config or _config(),
        generated_at=GENERATED_AT,
    )


def _unsafe_clone_report_with_flag(report, flag_name: str, flag_value: bool):
    clone = object.__new__(type(report))
    for field_name, field_value in report.__dict__.items():
        object.__setattr__(clone, field_name, field_value)
    object.__setattr__(clone, flag_name, flag_value)
    return clone


def test_phase_2_evidence_snapshot_describes_missing_local_reports():
    report = _snapshot()

    assert isinstance(report, PaperPhase2EvidenceSnapshotReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "phase-2-evidence-snapshot-v0"
    assert report.status == "phase_2_evidence_not_observed"
    assert report.calibration_report_present is False
    assert report.segment_summary_report_present is False
    assert report.calibration_observation_count is None
    assert report.segment_observation_count is None
    assert report.segment_count is None
    assert report.probability_segment_count is None
    assert report.return_only_segment_count is None
    assert report.thin_probability_segment_count is None
    assert report.probability_segment_coverage_ratio is None
    assert report.return_only_segment_ratio is None
    assert report.evidence_gap_count == 2
    assert tuple(row.evidence_gap_name for row in report.evidence_gaps) == GAP_NAMES
    assert tuple(row.gap_present for row in report.evidence_gaps) == (
        True,
        False,
        False,
        True,
        False,
        False,
    )
    assert report.evidence_gap_names == (
        "missing_calibration_report",
        "missing_segment_summary",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_evidence_snapshot_reports_observed_coverage_with_decimal_ratios():
    report = _snapshot(
        _calibration_report(30),
        _segment_summary_report(30, min_segment_observations=10),
        config=_config(
            min_calibration_observations=30,
            min_probability_segment_observations=10,
        ),
    )

    assert report.status == "phase_2_evidence_observed"
    assert report.calibration_report_present is True
    assert report.segment_summary_report_present is True
    assert report.calibration_status == "calibration_evidence_observed"
    assert report.segment_observation_count == 30
    assert report.segment_count == 2
    assert report.probability_segment_count == 2
    assert report.return_only_segment_count == 0
    assert report.thin_probability_segment_count == 0
    assert report.probability_segment_coverage_ratio == Decimal("1.000000")
    assert report.return_only_segment_ratio == Decimal("0.000000")
    assert report.evidence_gap_count == 0
    assert report.evidence_gap_names == ()
    assert tuple(row.gap_present for row in report.evidence_gaps) == (
        False,
        False,
        False,
        False,
        False,
        False,
    )


def test_phase_2_evidence_snapshot_reports_thin_and_return_only_segment_gaps():
    report = _snapshot(
        _calibration_report(12),
        _segment_summary_report(
            8,
            return_only_count=2,
            min_segment_observations=10,
        ),
        config=_config(
            min_calibration_observations=30,
            min_probability_segment_observations=10,
        ),
    )

    assert report.status == "phase_2_evidence_gaps"
    assert report.calibration_observation_count == 12
    assert report.segment_observation_count == 10
    assert report.segment_count == 4
    assert report.probability_segment_count == 2
    assert report.return_only_segment_count == 2
    assert report.thin_probability_segment_count == 2
    assert report.probability_segment_coverage_ratio == Decimal("0.500000")
    assert report.return_only_segment_ratio == Decimal("0.500000")
    assert report.evidence_gap_names == (
        "thin_calibration_sample",
        "thin_segment_probability_samples",
        "return_only_segments_present",
    )


def test_phase_2_evidence_snapshot_quality_flags_have_status_precedence_over_gaps():
    report = _snapshot(
        _calibration_report(
            30,
            actual=Decimal("0"),
            min_observation_count=30,
        ),
        _segment_summary_report(8, min_segment_observations=10),
        config=_config(
            min_calibration_observations=30,
            min_probability_segment_observations=10,
        ),
    )

    assert report.calibration_status == "calibration_quality_flags"
    assert report.status == "phase_2_evidence_quality_flags"
    assert report.evidence_gap_names == (
        "calibration_quality_flags_present",
        "thin_segment_probability_samples",
    )


def test_phase_2_evidence_snapshot_dataclasses_reject_invalid_inputs_and_flags():
    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2EvidenceSnapshotConfig(config_version=" ")
    with pytest.raises(ValueError, match="min_calibration_observations"):
        PaperPhase2EvidenceSnapshotConfig(
            config_version="phase-2-evidence-snapshot-v0",
            min_calibration_observations=-1,
        )
    with pytest.raises(ValueError, match="min_probability_segment_observations"):
        PaperPhase2EvidenceSnapshotConfig(
            config_version="phase-2-evidence-snapshot-v0",
            min_probability_segment_observations=True,
        )

    row = PaperPhase2EvidenceGapRow(
        evidence_gap_name="missing_calibration_report",
        gap_present=True,
    )
    with pytest.raises(FrozenInstanceError):
        row.gap_present = False
    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2EvidenceGapRow("unknown_gap", True)
    with pytest.raises(ValueError, match="gap_present"):
        PaperPhase2EvidenceGapRow("missing_calibration_report", 1)

    report = _snapshot(_calibration_report(30), _segment_summary_report(30))
    with pytest.raises(FrozenInstanceError):
        report.status = "phase_2_evidence_gaps"
    with pytest.raises(ValueError, match="status"):
        replace(report, status="phase_2_evidence_gaps")
    with pytest.raises(ValueError, match="evidence_gap_count"):
        replace(report, evidence_gap_count=1)
    with pytest.raises(ValueError, match="deterministic"):
        replace(report, evidence_gaps=(report.evidence_gaps[1], report.evidence_gaps[0]))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_phase_2_evidence_snapshot_revalidates_gap_reasons_and_ratios():
    report = _snapshot(
        _calibration_report(30),
        _segment_summary_report(30, min_segment_observations=10),
        config=_config(
            min_calibration_observations=30,
            min_probability_segment_observations=10,
        ),
    )

    impossible_gap_rows = tuple(
        replace(row, gap_present=True)
        if row.evidence_gap_name == "missing_calibration_report"
        else row
        for row in report.evidence_gaps
    )
    with pytest.raises(ValueError, match="evidence_gaps"):
        replace(
            report,
            status="phase_2_evidence_gaps",
            evidence_gap_count=1,
            evidence_gap_names=("missing_calibration_report",),
            evidence_gaps=impossible_gap_rows,
        )
    with pytest.raises(ValueError, match="probability_segment_coverage_ratio"):
        replace(report, probability_segment_coverage_ratio=Decimal("0.500000"))
    with pytest.raises(ValueError, match="return_only_segment_ratio"):
        replace(report, return_only_segment_ratio=Decimal("0.500000"))


def test_phase_2_evidence_snapshot_builder_requires_typed_reports_and_hard_flags():
    calibration_report = _calibration_report(30)
    segment_summary_report = _segment_summary_report(30)

    with pytest.raises(ValueError, match="calibration_report"):
        _snapshot(object(), segment_summary_report)
    with pytest.raises(ValueError, match="segment_summary_report"):
        _snapshot(calibration_report, object())
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_evidence_snapshot_report(
            calibration_report,
            segment_summary_report,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_evidence_snapshot_report(
            calibration_report,
            segment_summary_report,
            config=_config(),
            generated_at="2026-06-18",
        )
    with pytest.raises(ValueError, match="calibration_report paper_only"):
        _snapshot(
            _unsafe_clone_report_with_flag(calibration_report, "paper_only", False),
            segment_summary_report,
        )
    with pytest.raises(ValueError, match="segment_summary_report readonly"):
        _snapshot(
            calibration_report,
            _unsafe_clone_report_with_flag(segment_summary_report, "readonly", False),
        )
