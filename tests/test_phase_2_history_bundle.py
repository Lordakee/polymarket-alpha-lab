from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

import polymarket_alpha_lab
from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    PaperPhase2EvidenceGapRow,
    PaperPhase2EvidenceSnapshotReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_transition import (
    PaperPhase2EvidenceSnapshotTransitionConfig,
    PaperPhase2EvidenceSnapshotTransitionReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_trend import (
    PaperPhase2EvidenceSnapshotTrendConfig,
    PaperPhase2EvidenceSnapshotTrendReport,
)
from polymarket_alpha_lab.phase_2_history_bundle import (
    PaperPhase2HistoryBundleConfig,
    PaperPhase2HistoryBundleReport,
    build_paper_phase_2_history_bundle_report,
)


GENERATED_AT = datetime(2026, 6, 18, 20, 0, tzinfo=UTC)


def _config(**overrides) -> PaperPhase2HistoryBundleConfig:
    values = {"config_version": "phase-2-history-bundle-v0"}
    values.update(overrides)
    return PaperPhase2HistoryBundleConfig(**values)


def _trend_config(**overrides) -> PaperPhase2EvidenceSnapshotTrendConfig:
    values = {"config_version": "phase-2-evidence-snapshot-trend-v0"}
    values.update(overrides)
    return PaperPhase2EvidenceSnapshotTrendConfig(**values)


def _transition_config(**overrides) -> PaperPhase2EvidenceSnapshotTransitionConfig:
    values = {"config_version": "phase-2-evidence-snapshot-transition-v0"}
    values.update(overrides)
    return PaperPhase2EvidenceSnapshotTransitionConfig(**values)


def _gap_rows(*present_gap_names: str) -> tuple[PaperPhase2EvidenceGapRow, ...]:
    present = set(present_gap_names)
    return tuple(
        PaperPhase2EvidenceGapRow(
            evidence_gap_name=gap_name,
            gap_present=gap_name in present,
        )
        for gap_name in EVIDENCE_GAP_NAMES
    )


def _snapshot(
    *,
    generated_at: datetime = GENERATED_AT,
    status: str = "phase_2_evidence_observed",
    gap_names: tuple[str, ...] = (),
    calibration_present: bool = True,
    segment_present: bool = True,
    calibration_count: int | None = 30,
    calibration_status: str | None = "calibration_evidence_observed",
    probability_segment_count: int | None = 2,
    return_only_segment_count: int | None = 0,
    thin_probability_segment_count: int | None = 0,
) -> PaperPhase2EvidenceSnapshotReport:
    if segment_present:
        effective_segment_count = (
            (probability_segment_count or 0) + (return_only_segment_count or 0)
        )
        segment_observation_count = effective_segment_count
    else:
        effective_segment_count = None
        segment_observation_count = None
    return PaperPhase2EvidenceSnapshotReport(
        generated_at=generated_at,
        config_version="phase-2-evidence-snapshot-v0",
        status=status,
        calibration_report_present=calibration_present,
        segment_summary_report_present=segment_present,
        calibration_observation_count=calibration_count,
        calibration_status=calibration_status,
        segment_observation_count=segment_observation_count,
        segment_count=effective_segment_count,
        probability_segment_count=probability_segment_count,
        return_only_segment_count=return_only_segment_count,
        thin_probability_segment_count=thin_probability_segment_count,
        probability_segment_coverage_ratio=(
            None
            if effective_segment_count in (None, 0) or probability_segment_count is None
            else (
                Decimal(probability_segment_count) / Decimal(effective_segment_count)
            ).quantize(Decimal("0.000001"))
        ),
        return_only_segment_ratio=(
            None
            if effective_segment_count in (None, 0) or return_only_segment_count is None
            else (
                Decimal(return_only_segment_count) / Decimal(effective_segment_count)
            ).quantize(Decimal("0.000001"))
        ),
        evidence_gap_count=len(gap_names),
        evidence_gap_names=gap_names,
        evidence_gaps=_gap_rows(*gap_names),
    )


def _not_observed_snapshot(generated_at: datetime) -> PaperPhase2EvidenceSnapshotReport:
    return _snapshot(
        generated_at=generated_at,
        status="phase_2_evidence_not_observed",
        gap_names=("missing_calibration_report", "missing_segment_summary"),
        calibration_present=False,
        segment_present=False,
        calibration_count=None,
        calibration_status=None,
        probability_segment_count=None,
        return_only_segment_count=None,
        thin_probability_segment_count=None,
    )


def _gap_snapshot(
    generated_at: datetime,
    *gap_names: str,
) -> PaperPhase2EvidenceSnapshotReport:
    return _snapshot(
        generated_at=generated_at,
        status="phase_2_evidence_gaps",
        gap_names=gap_names,
        calibration_count=12 if "thin_calibration_sample" in gap_names else 30,
        probability_segment_count=2,
        return_only_segment_count=(
            2 if "return_only_segments_present" in gap_names else 0
        ),
        thin_probability_segment_count=(
            1 if "thin_segment_probability_samples" in gap_names else 0
        ),
    )


def _bundle_report(
    *snapshots: PaperPhase2EvidenceSnapshotReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperPhase2HistoryBundleReport:
    return build_paper_phase_2_history_bundle_report(
        snapshots,
        config=_config(),
        trend_config=_trend_config(),
        transition_config=_transition_config(),
        generated_at=generated_at,
    )


def test_phase_2_history_bundle_reports_empty_sequence():
    report = _bundle_report()

    assert isinstance(report, PaperPhase2HistoryBundleReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "phase-2-history-bundle-v0"
    assert report.snapshot_history == ()
    assert isinstance(report.snapshot_trend, PaperPhase2EvidenceSnapshotTrendReport)
    assert isinstance(
        report.snapshot_transition,
        PaperPhase2EvidenceSnapshotTransitionReport,
    )
    assert report.snapshot_trend.snapshot_report_count == 0
    assert report.snapshot_trend.latest_status is None
    assert report.snapshot_transition.snapshot_report_count == 0
    assert report.snapshot_transition.transition_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_history_bundle_preserves_exact_tuple_and_derives_nested_reports():
    first = _not_observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC))
    second = _gap_snapshot(
        datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        "thin_calibration_sample",
    )
    third = _snapshot(generated_at=datetime(2026, 6, 18, 9, 0, tzinfo=UTC))
    snapshots = (first, second, third)

    report = _bundle_report(*snapshots)

    assert report.snapshot_history == snapshots
    assert report.snapshot_history is not snapshots
    assert tuple(snapshot.status for snapshot in report.snapshot_history) == (
        "phase_2_evidence_not_observed",
        "phase_2_evidence_gaps",
        "phase_2_evidence_observed",
    )
    assert report.snapshot_trend.generated_at == GENERATED_AT
    assert report.snapshot_trend.config_version == (
        "phase-2-evidence-snapshot-trend-v0"
    )
    assert report.snapshot_trend.snapshot_report_count == 3
    assert report.snapshot_trend.latest_report_generated_at == third.generated_at
    assert report.snapshot_trend.latest_status == "phase_2_evidence_observed"
    assert report.snapshot_trend.consecutive_non_observed_count == 0
    assert report.snapshot_transition.generated_at == GENERATED_AT
    assert report.snapshot_transition.config_version == (
        "phase-2-evidence-snapshot-transition-v0"
    )
    assert report.snapshot_transition.snapshot_report_count == 3
    assert report.snapshot_transition.transition_count == 2
    assert report.snapshot_transition.latest_from_status == "phase_2_evidence_gaps"
    assert report.snapshot_transition.latest_to_status == "phase_2_evidence_observed"
    assert report.snapshot_transition.latest_cleared_gap_names == (
        "thin_calibration_sample",
    )


def test_phase_2_history_bundle_accepts_list_and_keeps_snapshot_append_order():
    first = _snapshot(generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC))
    earlier_timestamp = _gap_snapshot(
        datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
        "thin_segment_probability_samples",
    )

    report = build_paper_phase_2_history_bundle_report(
        [first, earlier_timestamp],
        config=_config(),
        trend_config=_trend_config(),
        transition_config=_transition_config(),
        generated_at=GENERATED_AT,
    )

    assert report.snapshot_history == (first, earlier_timestamp)
    assert report.snapshot_trend.first_report_generated_at == first.generated_at
    assert report.snapshot_trend.latest_report_generated_at == (
        earlier_timestamp.generated_at
    )
    assert report.snapshot_transition.latest_from_status == (
        "phase_2_evidence_observed"
    )
    assert report.snapshot_transition.latest_to_status == "phase_2_evidence_gaps"


def test_phase_2_history_bundle_normalizes_generated_at_to_utc():
    report = _bundle_report(
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.snapshot_trend.generated_at == GENERATED_AT
    assert report.snapshot_transition.generated_at == GENERATED_AT


def test_phase_2_history_bundle_rejects_invalid_builder_inputs():
    invalid_inputs = (
        object(),
        "not snapshots",
        b"not snapshots",
        {"snapshot": _snapshot()},
        (snapshot for snapshot in ()),
    )
    for snapshots in invalid_inputs:
        with pytest.raises(ValueError, match="snapshots must be a list or tuple"):
            build_paper_phase_2_history_bundle_report(
                snapshots,
                config=_config(),
                trend_config=_trend_config(),
                transition_config=_transition_config(),
                generated_at=GENERATED_AT,
            )

    subclassed_bundle_config = type(
        "SubclassedBundleConfig",
        (PaperPhase2HistoryBundleConfig,),
        {},
    )
    subclassed_trend_config = type(
        "SubclassedTrendConfig",
        (PaperPhase2EvidenceSnapshotTrendConfig,),
        {},
    )
    subclassed_transition_config = type(
        "SubclassedTransitionConfig",
        (PaperPhase2EvidenceSnapshotTransitionConfig,),
        {},
    )
    subclassed_snapshot_type = type(
        "SubclassedSnapshotReport",
        (PaperPhase2EvidenceSnapshotReport,),
        {},
    )
    snapshot = _snapshot()

    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        _bundle_report(object())
    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        _bundle_report(subclassed_snapshot_type(**snapshot.__dict__))
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_history_bundle_report(
            (),
            config=object(),
            trend_config=_trend_config(),
            transition_config=_transition_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_history_bundle_report(
            (),
            config=subclassed_bundle_config(config_version="phase-2-history-bundle-v0"),
            trend_config=_trend_config(),
            transition_config=_transition_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="trend_config"):
        build_paper_phase_2_history_bundle_report(
            (),
            config=_config(),
            trend_config=object(),
            transition_config=_transition_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="trend_config"):
        build_paper_phase_2_history_bundle_report(
            (),
            config=_config(),
            trend_config=subclassed_trend_config(
                config_version="phase-2-evidence-snapshot-trend-v0",
            ),
            transition_config=_transition_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="transition_config"):
        build_paper_phase_2_history_bundle_report(
            (),
            config=_config(),
            trend_config=_trend_config(),
            transition_config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="transition_config"):
        build_paper_phase_2_history_bundle_report(
            (),
            config=_config(),
            trend_config=_trend_config(),
            transition_config=subclassed_transition_config(
                config_version="phase-2-evidence-snapshot-transition-v0",
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_history_bundle_report(
            (),
            config=_config(),
            trend_config=_trend_config(),
            transition_config=_transition_config(),
            generated_at="now",
        )


def test_phase_2_history_bundle_rejects_scalar_subclasses():
    subclassed_string = type("SubclassedString", (str,), {})
    subclassed_datetime = type("SubclassedDateTime", (datetime,), {})
    report = _bundle_report(_snapshot())

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2HistoryBundleConfig(
            config_version=subclassed_string("phase-2-history-bundle-v0"),
        )
    with pytest.raises(ValueError, match="config_version"):
        replace(
            report,
            config_version=subclassed_string("phase-2-history-bundle-v0"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_history_bundle_report(
            (),
            config=_config(),
            trend_config=_trend_config(),
            transition_config=_transition_config(),
            generated_at=subclassed_datetime(2026, 6, 18, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        replace(
            report,
            generated_at=subclassed_datetime(2026, 6, 18, 20, 0, tzinfo=UTC),
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_phase_2_history_bundle_rejects_source_reports_with_nonfinal_flags(flag_name):
    source_report = _snapshot()
    object.__setattr__(source_report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        _bundle_report(source_report)


def test_phase_2_history_bundle_dataclasses_are_frozen_and_validate_flags():
    report = _bundle_report(_snapshot())

    with pytest.raises(FrozenInstanceError):
        report.snapshot_history = ()
    with pytest.raises(FrozenInstanceError):
        _config().config_version = "other"
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=" phase-2-history-bundle-v0 ")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_phase_2_history_bundle_revalidates_nested_report_types_and_flags():
    report = _bundle_report(_snapshot())
    two_snapshot_report = _bundle_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(ValueError, match="snapshot_history"):
        replace(report, snapshot_history=[_snapshot()])
    with pytest.raises(ValueError, match="snapshot_history"):
        replace(report, snapshot_history=(object(),))
    with pytest.raises(ValueError, match="snapshot_trend"):
        replace(report, snapshot_trend=object())
    with pytest.raises(ValueError, match="snapshot_transition"):
        replace(report, snapshot_transition=object())

    mutated_trend = replace(report.snapshot_trend)
    object.__setattr__(mutated_trend, "paper_only", False)
    with pytest.raises(ValueError, match="snapshot_trend paper_only"):
        replace(report, snapshot_trend=mutated_trend)

    mutated_transition = replace(report.snapshot_transition)
    object.__setattr__(mutated_transition, "readonly", False)
    with pytest.raises(ValueError, match="snapshot_transition readonly"):
        replace(report, snapshot_transition=mutated_transition)
    with pytest.raises(ValueError, match="snapshot_trend"):
        replace(report, snapshot_trend=two_snapshot_report.snapshot_trend)
    with pytest.raises(ValueError, match="snapshot_transition"):
        replace(report, snapshot_transition=two_snapshot_report.snapshot_transition)


def test_phase_2_history_bundle_revalidates_nested_reports_against_same_history():
    original = _bundle_report(
        _gap_snapshot(
            datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )
    same_length_different_history = _bundle_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "return_only_segments_present",
        ),
    )

    with pytest.raises(ValueError, match="snapshot_trend"):
        replace(
            original,
            snapshot_trend=same_length_different_history.snapshot_trend,
        )
    with pytest.raises(ValueError, match="snapshot_transition"):
        replace(
            original,
            snapshot_transition=same_length_different_history.snapshot_transition,
        )


def test_phase_2_history_bundle_local_all_and_package_root_non_export():
    from polymarket_alpha_lab import phase_2_history_bundle

    assert phase_2_history_bundle.__all__ == (
        "PaperPhase2HistoryBundleConfig",
        "PaperPhase2HistoryBundleReport",
        "build_paper_phase_2_history_bundle_report",
    )
    for exported_name in phase_2_history_bundle.__all__:
        assert exported_name not in polymarket_alpha_lab.__all__
        assert not hasattr(polymarket_alpha_lab, exported_name)
