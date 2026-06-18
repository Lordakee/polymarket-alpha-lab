from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    PaperPhase2EvidenceGapRow,
    PaperPhase2EvidenceSnapshotReport,
)
from polymarket_alpha_lab.phase_2_gap_delta import (
    PaperPhase2GapDeltaConfig,
    PaperPhase2GapDeltaReport,
    PaperPhase2GapDeltaRow,
    build_paper_phase_2_gap_delta_report,
)


GENERATED_AT = datetime(2026, 6, 18, 21, 0, tzinfo=UTC)


def _config(**overrides) -> PaperPhase2GapDeltaConfig:
    values = {"config_version": "phase-2-gap-delta-v0"}
    values.update(overrides)
    return PaperPhase2GapDeltaConfig(**values)


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
    generated_at: datetime,
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
        segment_count = (probability_segment_count or 0) + (
            return_only_segment_count or 0
        )
        segment_observation_count = segment_count
    else:
        segment_count = None
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
        segment_count=segment_count,
        probability_segment_count=probability_segment_count,
        return_only_segment_count=return_only_segment_count,
        thin_probability_segment_count=thin_probability_segment_count,
        probability_segment_coverage_ratio=(
            None
            if segment_count in (None, 0) or probability_segment_count is None
            else (Decimal(probability_segment_count) / Decimal(segment_count)).quantize(
                Decimal("0.000001"),
            )
        ),
        return_only_segment_ratio=(
            None
            if segment_count in (None, 0) or return_only_segment_count is None
            else (Decimal(return_only_segment_count) / Decimal(segment_count)).quantize(
                Decimal("0.000001"),
            )
        ),
        evidence_gap_count=len(gap_names),
        evidence_gap_names=gap_names,
        evidence_gaps=_gap_rows(*gap_names),
    )


def _observed_snapshot(generated_at: datetime) -> PaperPhase2EvidenceSnapshotReport:
    return _snapshot(generated_at=generated_at)


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
    calibration_present = "missing_calibration_report" not in gap_names
    segment_present = "missing_segment_summary" not in gap_names
    return _snapshot(
        generated_at=generated_at,
        status="phase_2_evidence_gaps",
        gap_names=gap_names,
        calibration_present=calibration_present,
        segment_present=segment_present,
        calibration_count=(
            None
            if not calibration_present
            else 12 if "thin_calibration_sample" in gap_names else 30
        ),
        calibration_status=(
            None if not calibration_present else "calibration_evidence_observed"
        ),
        probability_segment_count=None if not segment_present else 2,
        return_only_segment_count=(
            None
            if not segment_present
            else
            2 if "return_only_segments_present" in gap_names else 0
        ),
        thin_probability_segment_count=(
            None
            if not segment_present
            else
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


def _delta(
    *snapshots: PaperPhase2EvidenceSnapshotReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperPhase2GapDeltaReport:
    return build_paper_phase_2_gap_delta_report(
        snapshots,
        config=_config(),
        generated_at=generated_at,
    )


def test_phase_2_gap_delta_reports_empty_sequence():
    report = _delta()

    assert isinstance(report, PaperPhase2GapDeltaReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "phase-2-gap-delta-v0"
    assert report.snapshot_pair_count == 0
    assert report.latest_from_generated_at is None
    assert report.latest_to_generated_at is None
    assert report.latest_introduced_gap_names == ()
    assert report.latest_cleared_gap_names == ()
    assert report.total_introduced_gap_count == 0
    assert report.total_cleared_gap_count == 0
    assert report.rows == tuple(PaperPhase2GapDeltaRow(gap_name, 0, 0, 0) for gap_name in EVIDENCE_GAP_NAMES)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_gap_delta_handles_single_snapshot_without_pairs():
    snapshot = _gap_snapshot(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "thin_calibration_sample",
    )

    report = _delta(snapshot)

    assert report.snapshot_pair_count == 0
    assert report.latest_from_generated_at is None
    assert report.latest_to_generated_at is None
    assert report.latest_introduced_gap_names == ()
    assert report.latest_cleared_gap_names == ()
    assert all(row.introduced_count == 0 for row in report.rows)
    assert all(row.cleared_count == 0 for row in report.rows)
    assert all(row.persistent_count == 0 for row in report.rows)


def test_phase_2_gap_delta_counts_adjacent_gap_deltas_from_snapshots():
    first = _not_observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC))
    second = _gap_snapshot(
        datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        "thin_calibration_sample",
        "missing_segment_summary",
    )
    third = _quality_snapshot(datetime(2026, 6, 18, 12, 0, tzinfo=UTC))
    fourth = _observed_snapshot(datetime(2026, 6, 18, 13, 0, tzinfo=UTC))

    report = _delta(first, second, third, fourth)

    assert report.snapshot_pair_count == 3
    assert report.latest_from_generated_at == third.generated_at
    assert report.latest_to_generated_at == fourth.generated_at
    assert report.latest_introduced_gap_names == ()
    assert report.latest_cleared_gap_names == ("calibration_quality_flags_present",)
    assert report.total_introduced_gap_count == 2
    assert report.total_cleared_gap_count == 4
    assert _row(report, "missing_calibration_report") == PaperPhase2GapDeltaRow(
        "missing_calibration_report",
        introduced_count=0,
        cleared_count=1,
        persistent_count=0,
    )
    assert _row(report, "missing_segment_summary") == PaperPhase2GapDeltaRow(
        "missing_segment_summary",
        introduced_count=0,
        cleared_count=1,
        persistent_count=1,
    )
    assert _row(report, "thin_calibration_sample") == PaperPhase2GapDeltaRow(
        "thin_calibration_sample",
        introduced_count=1,
        cleared_count=1,
        persistent_count=0,
    )
    assert _row(report, "calibration_quality_flags_present") == PaperPhase2GapDeltaRow(
        "calibration_quality_flags_present",
        introduced_count=1,
        cleared_count=1,
        persistent_count=0,
    )


def test_phase_2_gap_delta_preserves_append_order_not_timestamp_sorting():
    first_append = _observed_snapshot(datetime(2026, 6, 18, 16, 0, tzinfo=UTC))
    second_append_earlier_time = _gap_snapshot(
        datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
        "thin_calibration_sample",
    )

    report = _delta(first_append, second_append_earlier_time)

    assert report.snapshot_pair_count == 1
    assert report.latest_from_generated_at == first_append.generated_at
    assert report.latest_to_generated_at == second_append_earlier_time.generated_at
    assert report.latest_introduced_gap_names == ("thin_calibration_sample",)
    assert report.latest_cleared_gap_names == ()


def test_phase_2_gap_delta_normalizes_generated_at_and_latest_pair_times_to_utc():
    report = _delta(
        _observed_snapshot(
            datetime(2026, 6, 18, 10, 0, tzinfo=timezone(timedelta(hours=-7))),
        ),
        _gap_snapshot(
            datetime(2026, 6, 18, 12, 0),
            "thin_calibration_sample",
        ),
        generated_at=datetime(2026, 6, 18, 14, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.latest_from_generated_at == datetime(2026, 6, 18, 17, 0, tzinfo=UTC)
    assert report.latest_to_generated_at == datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


def test_phase_2_gap_delta_rejects_invalid_builder_inputs():
    invalid_inputs = (
        object(),
        "not snapshots",
        b"not snapshots",
        {"snapshot": _observed_snapshot(GENERATED_AT)},
        (snapshot for snapshot in ()),
    )
    for snapshots in invalid_inputs:
        with pytest.raises(ValueError, match="snapshots must be a list or tuple"):
            build_paper_phase_2_gap_delta_report(
                snapshots,
                config=_config(),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        build_paper_phase_2_gap_delta_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_gap_delta_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_gap_delta_report(
            (),
            config=_config(),
            generated_at="now",
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_phase_2_gap_delta_rejects_source_snapshots_with_nonfinal_flags(flag_name):
    source_snapshot = _observed_snapshot(GENERATED_AT)
    object.__setattr__(source_snapshot, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_phase_2_gap_delta_report(
            (source_snapshot,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_phase_2_gap_delta_dataclasses_are_frozen_and_validate_consistency():
    report = _delta(
        _gap_snapshot(
            datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
        _observed_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(FrozenInstanceError):
        report.snapshot_pair_count = 0
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="latest_from_generated_at"):
        replace(report, snapshot_pair_count=0)
    with pytest.raises(ValueError, match="latest_cleared_gap_names"):
        replace(report, latest_cleared_gap_names=())
    with pytest.raises(ValueError, match="latest gap names"):
        replace(
            report,
            latest_introduced_gap_names=("thin_calibration_sample",),
            latest_cleared_gap_names=("thin_calibration_sample",),
        )
    with pytest.raises(ValueError, match="total_introduced_gap_count"):
        replace(report, total_introduced_gap_count=2)
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=report.rows[1:] + report.rows[:1])


def test_phase_2_gap_delta_rows_and_all_are_exact():
    from polymarket_alpha_lab import phase_2_gap_delta

    assert phase_2_gap_delta.__all__ == (
        "PaperPhase2GapDeltaConfig",
        "PaperPhase2GapDeltaReport",
        "PaperPhase2GapDeltaRow",
        "build_paper_phase_2_gap_delta_report",
    )

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2GapDeltaConfig(config_version=" ")
    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2GapDeltaRow("unknown", 0, 0, 0)
    with pytest.raises(ValueError, match="introduced_count"):
        PaperPhase2GapDeltaRow("thin_calibration_sample", -1, 0, 0)
    with pytest.raises(ValueError, match="cleared_count"):
        PaperPhase2GapDeltaRow("thin_calibration_sample", 0, True, 0)
    with pytest.raises(ValueError, match="persistent_count"):
        PaperPhase2GapDeltaRow("thin_calibration_sample", 0, 0, -1)


def _row(report: PaperPhase2GapDeltaReport, gap_name: str) -> PaperPhase2GapDeltaRow:
    return next(row for row in report.rows if row.evidence_gap_name == gap_name)
