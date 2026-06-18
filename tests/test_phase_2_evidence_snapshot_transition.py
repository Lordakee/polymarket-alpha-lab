from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    SNAPSHOT_STATUSES,
    PaperPhase2EvidenceGapRow,
    PaperPhase2EvidenceSnapshotReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_transition import (
    PaperPhase2EvidenceSnapshotGapTransitionRow,
    PaperPhase2EvidenceSnapshotStatusTransitionRow,
    PaperPhase2EvidenceSnapshotTransitionConfig,
    PaperPhase2EvidenceSnapshotTransitionReport,
    build_paper_phase_2_evidence_snapshot_transition_report,
)


GENERATED_AT = datetime(2026, 6, 18, 19, 0, tzinfo=UTC)


def _config(**overrides) -> PaperPhase2EvidenceSnapshotTransitionConfig:
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


def _quality_snapshot(generated_at: datetime) -> PaperPhase2EvidenceSnapshotReport:
    return _snapshot(
        generated_at=generated_at,
        status="phase_2_evidence_quality_flags",
        gap_names=("calibration_quality_flags_present",),
        calibration_status="calibration_quality_flags",
    )


def _transition_report(
    *snapshots: PaperPhase2EvidenceSnapshotReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperPhase2EvidenceSnapshotTransitionReport:
    return build_paper_phase_2_evidence_snapshot_transition_report(
        snapshots,
        config=_config(),
        generated_at=generated_at,
    )


def test_phase_2_evidence_snapshot_transition_reports_empty_sequence():
    report = _transition_report()

    assert isinstance(report, PaperPhase2EvidenceSnapshotTransitionReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "phase-2-evidence-snapshot-transition-v0"
    assert report.snapshot_report_count == 0
    assert report.transition_count == 0
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.latest_from_status is None
    assert report.latest_to_status is None
    assert report.latest_introduced_gap_names == ()
    assert report.latest_cleared_gap_names == ()
    assert len(report.status_transition_rows) == len(SNAPSHOT_STATUSES) ** 2
    assert all(row.transition_count == 0 for row in report.status_transition_rows)
    assert all(row.transition_ratio is None for row in report.status_transition_rows)
    assert report.gap_transition_rows == tuple(
        PaperPhase2EvidenceSnapshotGapTransitionRow(gap_name, 0, 0, 0)
        for gap_name in EVIDENCE_GAP_NAMES
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_evidence_snapshot_transition_counts_adjacent_status_pairs():
    first = _not_observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC))
    second = _gap_snapshot(
        datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        "thin_calibration_sample",
    )
    third = _snapshot(generated_at=datetime(2026, 6, 18, 9, 0, tzinfo=UTC))

    report = _transition_report(first, second, third)

    assert report.snapshot_report_count == 3
    assert report.transition_count == 2
    assert report.first_report_generated_at == first.generated_at
    assert report.latest_report_generated_at == third.generated_at
    assert report.latest_from_status == "phase_2_evidence_gaps"
    assert report.latest_to_status == "phase_2_evidence_observed"
    assert _status_row(
        report,
        "phase_2_evidence_not_observed",
        "phase_2_evidence_gaps",
    ) == PaperPhase2EvidenceSnapshotStatusTransitionRow(
        "phase_2_evidence_not_observed",
        "phase_2_evidence_gaps",
        1,
        Decimal("0.500000"),
    )
    assert _status_row(
        report,
        "phase_2_evidence_gaps",
        "phase_2_evidence_observed",
    ) == PaperPhase2EvidenceSnapshotStatusTransitionRow(
        "phase_2_evidence_gaps",
        "phase_2_evidence_observed",
        1,
        Decimal("0.500000"),
    )


def test_phase_2_evidence_snapshot_transition_counts_gap_changes():
    first = _gap_snapshot(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "thin_calibration_sample",
        "return_only_segments_present",
    )
    second = _gap_snapshot(
        datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        "thin_calibration_sample",
        "thin_segment_probability_samples",
    )
    third = _quality_snapshot(datetime(2026, 6, 18, 12, 0, tzinfo=UTC))

    report = _transition_report(first, second, third)

    assert report.latest_from_status == "phase_2_evidence_gaps"
    assert report.latest_to_status == "phase_2_evidence_quality_flags"
    assert report.latest_introduced_gap_names == ("calibration_quality_flags_present",)
    assert report.latest_cleared_gap_names == (
        "thin_calibration_sample",
        "thin_segment_probability_samples",
    )
    assert _gap_row(report, "thin_calibration_sample") == (
        PaperPhase2EvidenceSnapshotGapTransitionRow(
            "thin_calibration_sample",
            introduced_count=0,
            cleared_count=1,
            persistent_count=1,
        )
    )
    assert _gap_row(report, "thin_segment_probability_samples") == (
        PaperPhase2EvidenceSnapshotGapTransitionRow(
            "thin_segment_probability_samples",
            introduced_count=1,
            cleared_count=1,
            persistent_count=0,
        )
    )
    assert _gap_row(report, "calibration_quality_flags_present") == (
        PaperPhase2EvidenceSnapshotGapTransitionRow(
            "calibration_quality_flags_present",
            introduced_count=1,
            cleared_count=0,
            persistent_count=0,
        )
    )


def test_phase_2_evidence_snapshot_transition_handles_single_snapshot_without_pairs():
    snapshot = _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC))

    report = _transition_report(snapshot)

    assert report.snapshot_report_count == 1
    assert report.transition_count == 0
    assert report.first_report_generated_at == snapshot.generated_at
    assert report.latest_report_generated_at == snapshot.generated_at
    assert report.latest_from_status is None
    assert report.latest_to_status is None


def test_phase_2_evidence_snapshot_transition_normalizes_generated_at_to_utc():
    report = _transition_report(
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT


def test_phase_2_evidence_snapshot_transition_rejects_invalid_builder_inputs():
    invalid_inputs = (
        object(),
        "not snapshots",
        b"not snapshots",
        {"snapshot": _snapshot()},
        (snapshot for snapshot in ()),
    )
    for snapshots in invalid_inputs:
        with pytest.raises(ValueError, match="snapshots must be a list or tuple"):
            build_paper_phase_2_evidence_snapshot_transition_report(
                snapshots,
                config=_config(),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        build_paper_phase_2_evidence_snapshot_transition_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_evidence_snapshot_transition_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_evidence_snapshot_transition_report(
            (),
            config=_config(),
            generated_at="now",
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_phase_2_evidence_snapshot_transition_rejects_source_reports_with_nonfinal_flags(
    flag_name,
):
    source_report = _snapshot()
    object.__setattr__(source_report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_phase_2_evidence_snapshot_transition_report(
            (source_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_phase_2_evidence_snapshot_transition_dataclasses_are_frozen_and_validate():
    report = _transition_report(
        _gap_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC), "thin_calibration_sample"),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(FrozenInstanceError):
        report.transition_count = 0
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="transition_count"):
        replace(report, transition_count=2)
    with pytest.raises(ValueError, match="latest_to_status"):
        replace(report, latest_to_status="phase_2_evidence_gaps")
    with pytest.raises(ValueError, match="latest_cleared_gap_names"):
        replace(report, latest_cleared_gap_names=())
    with pytest.raises(ValueError, match="latest gap changes"):
        replace(
            report,
            latest_introduced_gap_names=("thin_calibration_sample",),
            latest_cleared_gap_names=("thin_calibration_sample",),
        )
    counted_report = _transition_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )
    with pytest.raises(ValueError, match="latest_introduced_gap_names"):
        replace(counted_report, latest_introduced_gap_names=("thin_calibration_sample",))


def test_phase_2_evidence_snapshot_transition_rows_and_all_are_exact():
    from polymarket_alpha_lab import phase_2_evidence_snapshot_transition

    assert phase_2_evidence_snapshot_transition.__all__ == (
        "PaperPhase2EvidenceSnapshotGapTransitionRow",
        "PaperPhase2EvidenceSnapshotStatusTransitionRow",
        "PaperPhase2EvidenceSnapshotTransitionConfig",
        "PaperPhase2EvidenceSnapshotTransitionReport",
        "build_paper_phase_2_evidence_snapshot_transition_report",
    )

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2EvidenceSnapshotTransitionConfig(config_version=" ")
    with pytest.raises(ValueError, match="from_snapshot_status"):
        PaperPhase2EvidenceSnapshotStatusTransitionRow(
            "unknown",
            "phase_2_evidence_observed",
            0,
            None,
        )
    with pytest.raises(ValueError, match="to_snapshot_status"):
        PaperPhase2EvidenceSnapshotStatusTransitionRow(
            "phase_2_evidence_observed",
            "unknown",
            0,
            None,
        )
    with pytest.raises(ValueError, match="transition_ratio"):
        PaperPhase2EvidenceSnapshotStatusTransitionRow(
            "phase_2_evidence_observed",
            "phase_2_evidence_observed",
            1,
            Decimal("0.1"),
        )
    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2EvidenceSnapshotGapTransitionRow("unknown", 0, 0, 0)


def _status_row(
    report: PaperPhase2EvidenceSnapshotTransitionReport,
    from_status: str,
    to_status: str,
) -> PaperPhase2EvidenceSnapshotStatusTransitionRow:
    return next(
        row
        for row in report.status_transition_rows
        if row.from_snapshot_status == from_status and row.to_snapshot_status == to_status
    )


def _gap_row(
    report: PaperPhase2EvidenceSnapshotTransitionReport,
    gap_name: str,
) -> PaperPhase2EvidenceSnapshotGapTransitionRow:
    return next(
        row
        for row in report.gap_transition_rows
        if row.evidence_gap_name == gap_name
    )
