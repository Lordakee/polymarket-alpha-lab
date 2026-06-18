from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

import polymarket_alpha_lab
from polymarket_alpha_lab.forecast_calibration import (
    PaperForecastCalibrationConfig,
    PaperForecastCalibrationReport,
    build_paper_forecast_calibration_report,
)
from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceObservation
from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    PaperPhase2EvidenceSnapshotConfig,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_history import (
    PaperPhase2EvidenceSnapshotHistoryConfig,
    build_paper_phase_2_evidence_snapshot_history,
)
from polymarket_alpha_lab.strategy_segment_summary import (
    PaperStrategySegmentSummaryConfig,
    build_paper_strategy_segment_summary_report,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


def _history_config(**overrides) -> PaperPhase2EvidenceSnapshotHistoryConfig:
    values = {"config_version": "phase-2-evidence-snapshot-history-v0"}
    values.update(overrides)
    return PaperPhase2EvidenceSnapshotHistoryConfig(**values)


def _snapshot_config(**overrides) -> PaperPhase2EvidenceSnapshotConfig:
    values = {
        "config_version": "phase-2-evidence-snapshot-v0",
        "min_calibration_observations": 30,
        "min_probability_segment_observations": 10,
    }
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


def _calibration_report(probability_count: int):
    return build_paper_forecast_calibration_report(
        (
            _observation(
                index,
                predicted_probability=Decimal("0.7000"),
                actual_outcome_value=Decimal("1"),
                paper_return_ratio=None,
            )
            for index in range(probability_count)
        ),
        config=PaperForecastCalibrationConfig(
            config_version="forecast-calibration-test",
            min_observation_count=1,
            max_brier_score=Decimal("0.250000"),
            max_expected_calibration_error=Decimal("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )


def _segment_summary_report(
    probability_count: int,
    *,
    return_only_count: int = 0,
    minute_offset: int = 0,
):
    probability_items = tuple(
        _observation(
            minute_offset + index,
            predicted_probability=Decimal("0.7000"),
            actual_outcome_value=Decimal("1"),
            paper_return_ratio=Decimal("0.0100"),
        )
        for index in range(probability_count)
    )
    return_only_items = tuple(
        _observation(
            minute_offset + 100 + index,
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
            min_segment_observations=1,
        ),
        generated_at=GENERATED_AT,
    )


def _history(calibration_reports, segment_summary_reports):
    return build_paper_phase_2_evidence_snapshot_history(
        calibration_reports,
        segment_summary_reports,
        config=_history_config(),
        snapshot_config=_snapshot_config(),
        generated_at=GENERATED_AT,
    )


def _unsafe_clone_report_with_flag(report, flag_name: str, flag_value: bool):
    clone = object.__new__(type(report))
    for field_name, field_value in report.__dict__.items():
        object.__setattr__(clone, field_name, field_value)
    object.__setattr__(clone, flag_name, flag_value)
    return clone


def test_phase_2_evidence_snapshot_history_returns_empty_for_empty_histories():
    assert _history([], ()) == ()


def test_phase_2_evidence_snapshot_history_aligns_calibration_prefix_then_paired():
    first_calibration = _calibration_report(12)
    second_calibration = _calibration_report(30)
    segment_summary = _segment_summary_report(30)

    snapshots = _history((first_calibration, second_calibration), (segment_summary,))

    assert len(snapshots) == 2
    assert tuple(snapshot.generated_at for snapshot in snapshots) == (
        GENERATED_AT,
        GENERATED_AT,
    )
    assert tuple(snapshot.calibration_report_present for snapshot in snapshots) == (
        True,
        True,
    )
    assert tuple(snapshot.segment_summary_report_present for snapshot in snapshots) == (
        True,
        True,
    )
    assert tuple(snapshot.calibration_observation_count for snapshot in snapshots) == (
        12,
        30,
    )
    assert tuple(snapshot.segment_observation_count for snapshot in snapshots) == (
        30,
        30,
    )
    assert snapshots[0].status == "phase_2_evidence_gaps"
    assert snapshots[0].evidence_gap_names == ("thin_calibration_sample",)
    assert snapshots[1].status == "phase_2_evidence_observed"
    assert snapshots[1].evidence_gap_names == ()


def test_phase_2_evidence_snapshot_history_aligns_segment_only_prefixes():
    first_segment_summary = _segment_summary_report(8)
    second_segment_summary = _segment_summary_report(
        8,
        return_only_count=2,
        minute_offset=1000,
    )

    snapshots = _history([], [first_segment_summary, second_segment_summary])

    assert len(snapshots) == 2
    assert tuple(snapshot.calibration_report_present for snapshot in snapshots) == (
        False,
        False,
    )
    assert tuple(snapshot.segment_summary_report_present for snapshot in snapshots) == (
        True,
        True,
    )
    assert tuple(snapshot.segment_observation_count for snapshot in snapshots) == (
        8,
        10,
    )
    assert tuple(snapshot.return_only_segment_count for snapshot in snapshots) == (
        0,
        2,
    )
    assert snapshots[0].evidence_gap_names == (
        "missing_calibration_report",
        "thin_segment_probability_samples",
    )
    assert snapshots[1].evidence_gap_names == (
        "missing_calibration_report",
        "thin_segment_probability_samples",
        "return_only_segments_present",
    )


def test_phase_2_evidence_snapshot_history_uses_max_prefix_append_order():
    first_calibration = _calibration_report(12)
    second_calibration = _calibration_report(30)
    first_segment_summary = _segment_summary_report(8)
    second_segment_summary = _segment_summary_report(
        30,
        minute_offset=1000,
    )
    third_segment_summary = _segment_summary_report(
        30,
        return_only_count=2,
        minute_offset=2000,
    )

    snapshots = _history(
        [first_calibration, second_calibration],
        [first_segment_summary, second_segment_summary, third_segment_summary],
    )

    assert len(snapshots) == 3
    assert tuple(snapshot.calibration_observation_count for snapshot in snapshots) == (
        12,
        30,
        30,
    )
    assert tuple(snapshot.segment_observation_count for snapshot in snapshots) == (
        8,
        30,
        32,
    )
    assert tuple(snapshot.status for snapshot in snapshots) == (
        "phase_2_evidence_gaps",
        "phase_2_evidence_observed",
        "phase_2_evidence_gaps",
    )
    assert snapshots[2].evidence_gap_names == ("return_only_segments_present",)


def test_phase_2_evidence_snapshot_history_rejects_invalid_inputs_and_flags():
    calibration_report = _calibration_report(30)
    segment_summary_report = _segment_summary_report(30)
    subclassed_config_type = type(
        "SubclassedHistoryConfig",
        (PaperPhase2EvidenceSnapshotHistoryConfig,),
        {},
    )
    subclassed_snapshot_config_type = type(
        "SubclassedSnapshotConfig",
        (PaperPhase2EvidenceSnapshotConfig,),
        {},
    )
    subclassed_calibration_type = type(
        "SubclassedCalibrationReport",
        (PaperForecastCalibrationReport,),
        {},
    )
    subclassed_segment_type = type(
        "SubclassedSegmentSummaryReport",
        (type(segment_summary_report),),
        {},
    )

    with pytest.raises(ValueError, match="calibration_reports"):
        _history((report for report in (calibration_report,)), [segment_summary_report])
    with pytest.raises(ValueError, match="calibration_reports"):
        _history(
            tuple.__new__(type("CalibrationTuple", (tuple,), {}), (calibration_report,)),
            [segment_summary_report],
        )
    with pytest.raises(ValueError, match="segment_summary_reports"):
        _history([calibration_report], {"segment": segment_summary_report})
    with pytest.raises(ValueError, match="segment_summary_reports"):
        _history(
            [calibration_report],
            list.__new__(type("SegmentList", (list,), {})),
        )
    with pytest.raises(ValueError, match="PaperForecastCalibrationReport"):
        _history([object()], [segment_summary_report])
    with pytest.raises(ValueError, match="PaperForecastCalibrationReport"):
        _history(
            [subclassed_calibration_type(**calibration_report.__dict__)],
            [segment_summary_report],
        )
    with pytest.raises(ValueError, match="PaperStrategySegmentSummaryReport"):
        _history([calibration_report], [object()])
    with pytest.raises(ValueError, match="PaperStrategySegmentSummaryReport"):
        _history(
            [calibration_report],
            [subclassed_segment_type(**segment_summary_report.__dict__)],
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_evidence_snapshot_history(
            [calibration_report],
            [segment_summary_report],
            config=object(),
            snapshot_config=_snapshot_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_evidence_snapshot_history(
            [calibration_report],
            [segment_summary_report],
            config=subclassed_config_type(
                config_version="phase-2-evidence-snapshot-history-v0",
            ),
            snapshot_config=_snapshot_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="snapshot_config"):
        build_paper_phase_2_evidence_snapshot_history(
            [calibration_report],
            [segment_summary_report],
            config=_history_config(),
            snapshot_config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="snapshot_config"):
        build_paper_phase_2_evidence_snapshot_history(
            [calibration_report],
            [segment_summary_report],
            config=_history_config(),
            snapshot_config=subclassed_snapshot_config_type(
                config_version="phase-2-evidence-snapshot-v0",
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_evidence_snapshot_history(
            [calibration_report],
            [segment_summary_report],
            config=_history_config(),
            snapshot_config=_snapshot_config(),
            generated_at="2026-06-18",
        )
    with pytest.raises(ValueError, match="calibration_reports paper_only"):
        _history(
            [_unsafe_clone_report_with_flag(calibration_report, "paper_only", False)],
            [segment_summary_report],
        )
    with pytest.raises(ValueError, match="segment_summary_reports readonly"):
        _history(
            [calibration_report],
            [_unsafe_clone_report_with_flag(segment_summary_report, "readonly", False)],
        )


def test_phase_2_evidence_snapshot_history_config_and_all_are_local():
    from polymarket_alpha_lab import phase_2_evidence_snapshot_history

    assert phase_2_evidence_snapshot_history.__all__ == (
        "PaperPhase2EvidenceSnapshotHistoryConfig",
        "build_paper_phase_2_evidence_snapshot_history",
    )
    for exported_name in phase_2_evidence_snapshot_history.__all__:
        assert exported_name not in polymarket_alpha_lab.__all__
        assert not hasattr(polymarket_alpha_lab, exported_name)

    config = _history_config()
    assert config.config_version == "phase-2-evidence-snapshot-history-v0"
    assert config.alignment_strategy == "max_prefix"
    with pytest.raises(FrozenInstanceError):
        config.alignment_strategy = "other"
    with pytest.raises(ValueError, match="config_version"):
        _history_config(config_version=" phase-2-evidence-snapshot-history-v0 ")
    with pytest.raises(ValueError, match="alignment_strategy"):
        _history_config(alignment_strategy="by_timestamp")
