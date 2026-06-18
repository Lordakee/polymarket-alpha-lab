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
from polymarket_alpha_lab.phase_2_status_matrix import (
    PaperPhase2StatusMatrixConfig,
    PaperPhase2StatusMatrixReport,
    PaperPhase2StatusMatrixRow,
    build_paper_phase_2_status_matrix_report,
)


GENERATED_AT = datetime(2026, 6, 18, 19, 0, tzinfo=UTC)
CONFIG_VERSION = "phase-2-status-matrix-v0"


def _config(**overrides) -> PaperPhase2StatusMatrixConfig:
    values = {"config_version": CONFIG_VERSION}
    values.update(overrides)
    return PaperPhase2StatusMatrixConfig(**values)


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


def _gap_snapshot(generated_at: datetime) -> PaperPhase2EvidenceSnapshotReport:
    return _snapshot(
        generated_at=generated_at,
        status="phase_2_evidence_gaps",
        gap_names=("thin_calibration_sample",),
        calibration_count=12,
    )


def _quality_snapshot(generated_at: datetime) -> PaperPhase2EvidenceSnapshotReport:
    return _snapshot(
        generated_at=generated_at,
        status="phase_2_evidence_quality_flags",
        gap_names=("calibration_quality_flags_present",),
        calibration_status="calibration_quality_flags",
    )


def _observed_snapshot(generated_at: datetime) -> PaperPhase2EvidenceSnapshotReport:
    return _snapshot(generated_at=generated_at)


def _matrix(*snapshots: PaperPhase2EvidenceSnapshotReport) -> PaperPhase2StatusMatrixReport:
    return build_paper_phase_2_status_matrix_report(
        snapshots,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def test_phase_2_status_matrix_reports_empty_sequence():
    report = _matrix()

    assert isinstance(report, PaperPhase2StatusMatrixReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.snapshot_report_count == 0
    assert report.transition_count == 0
    assert report.latest_from_status is None
    assert report.latest_to_status is None
    assert len(report.rows) == len(SNAPSHOT_STATUSES) ** 2
    assert report.rows == tuple(
        PaperPhase2StatusMatrixRow(
            from_status=from_status,
            to_status=to_status,
            transition_count=0,
            transition_ratio=Decimal("0.000000"),
        )
        for from_status in SNAPSHOT_STATUSES
        for to_status in SNAPSHOT_STATUSES
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_status_matrix_counts_adjacent_pairs_and_ratios():
    report = _matrix(
        _not_observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
        _quality_snapshot(datetime(2026, 6, 18, 12, 0, tzinfo=UTC)),
        _observed_snapshot(datetime(2026, 6, 18, 13, 0, tzinfo=UTC)),
    )

    assert report.snapshot_report_count == 4
    assert report.transition_count == 3
    assert report.latest_from_status == "phase_2_evidence_quality_flags"
    assert report.latest_to_status == "phase_2_evidence_observed"
    assert _row(
        report,
        "phase_2_evidence_not_observed",
        "phase_2_evidence_gaps",
    ) == PaperPhase2StatusMatrixRow(
        "phase_2_evidence_not_observed",
        "phase_2_evidence_gaps",
        1,
        Decimal("0.333333"),
    )
    assert _row(
        report,
        "phase_2_evidence_gaps",
        "phase_2_evidence_quality_flags",
    ).transition_ratio == Decimal("0.333333")
    assert _row(
        report,
        "phase_2_evidence_quality_flags",
        "phase_2_evidence_observed",
    ).transition_ratio == Decimal("0.333333")
    assert _row(
        report,
        "phase_2_evidence_observed",
        "phase_2_evidence_observed",
    ).transition_ratio == Decimal("0.000000")
    assert sum(row.transition_count for row in report.rows) == 3
    assert sum(row.transition_ratio for row in report.rows) == Decimal("0.999999")


def test_phase_2_status_matrix_uses_append_sequence_for_latest_pair():
    older_generated_later = _observed_snapshot(
        datetime(2026, 6, 18, 15, 0, tzinfo=UTC),
    )
    newer_generated_earlier = _gap_snapshot(
        datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
    )

    report = _matrix(older_generated_later, newer_generated_earlier)

    assert report.latest_from_status == "phase_2_evidence_observed"
    assert report.latest_to_status == "phase_2_evidence_gaps"
    assert _row(
        report,
        "phase_2_evidence_observed",
        "phase_2_evidence_gaps",
    ).transition_count == 1


def test_phase_2_status_matrix_normalizes_generated_at_to_utc():
    report = build_paper_phase_2_status_matrix_report(
        (),
        config=_config(),
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT


def test_phase_2_status_matrix_rejects_invalid_builder_inputs():
    class DerivedConfig(PaperPhase2StatusMatrixConfig):
        pass

    class DerivedSnapshot(PaperPhase2EvidenceSnapshotReport):
        pass

    class DerivedDateTime(datetime):
        pass

    for invalid_snapshots in (
        object(),
        "snapshots",
        b"snapshots",
        {"snapshot": _observed_snapshot(GENERATED_AT)},
        (snapshot for snapshot in ()),
    ):
        with pytest.raises(ValueError, match="snapshots"):
            build_paper_phase_2_status_matrix_report(
                invalid_snapshots,
                config=_config(),
                generated_at=GENERATED_AT,
            )
    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        build_paper_phase_2_status_matrix_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        build_paper_phase_2_status_matrix_report(
            (DerivedSnapshot.__new__(DerivedSnapshot),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_status_matrix_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_status_matrix_report(
            (),
            config=DerivedConfig(config_version=CONFIG_VERSION),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_status_matrix_report(
            (),
            config=_config(),
            generated_at="now",
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_status_matrix_report(
            (),
            config=_config(),
            generated_at=DerivedDateTime(2026, 6, 18, 19, 0, tzinfo=UTC),
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_phase_2_status_matrix_rejects_source_reports_with_nonfinal_flags(flag_name):
    source_report = _observed_snapshot(GENERATED_AT)
    object.__setattr__(source_report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_phase_2_status_matrix_report(
            (source_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_phase_2_status_matrix_rejects_source_reports_with_drifted_status_type():
    class DerivedStr(str):
        pass

    source_report = _observed_snapshot(GENERATED_AT)
    object.__setattr__(
        source_report,
        "status",
        DerivedStr("phase_2_evidence_observed"),
    )

    with pytest.raises(ValueError, match="status"):
        build_paper_phase_2_status_matrix_report(
            (source_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_phase_2_status_matrix_dataclasses_are_frozen_and_revalidate():
    report = _matrix(
        _gap_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _observed_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(FrozenInstanceError):
        report.transition_count = 99
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
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=tuple(reversed(report.rows)))
    drifted_row = replace(report.rows[0], transition_ratio=Decimal("0.100000"))
    with pytest.raises(ValueError, match="ratios"):
        replace(report, rows=(drifted_row, *report.rows[1:]))


def test_phase_2_status_matrix_rows_and_all_are_exact():
    from polymarket_alpha_lab import phase_2_status_matrix

    class DerivedStr(str):
        pass

    class DerivedInt(int):
        pass

    class DerivedDecimal(Decimal):
        pass

    assert phase_2_status_matrix.__all__ == (
        "PaperPhase2StatusMatrixConfig",
        "PaperPhase2StatusMatrixReport",
        "PaperPhase2StatusMatrixRow",
        "build_paper_phase_2_status_matrix_report",
    )
    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2StatusMatrixConfig(config_version=" ")
    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2StatusMatrixConfig(config_version=DerivedStr(CONFIG_VERSION))
    with pytest.raises(ValueError, match="from_status"):
        PaperPhase2StatusMatrixRow(
            "unknown",
            "phase_2_evidence_observed",
            0,
            Decimal("0.000000"),
        )
    with pytest.raises(ValueError, match="from_status"):
        PaperPhase2StatusMatrixRow(
            DerivedStr("phase_2_evidence_observed"),
            "phase_2_evidence_observed",
            0,
            Decimal("0.000000"),
        )
    with pytest.raises(ValueError, match="transition_count"):
        PaperPhase2StatusMatrixRow(
            "phase_2_evidence_observed",
            "phase_2_evidence_observed",
            True,
            Decimal("0.000000"),
        )
    with pytest.raises(ValueError, match="transition_count"):
        PaperPhase2StatusMatrixRow(
            "phase_2_evidence_observed",
            "phase_2_evidence_observed",
            DerivedInt(0),
            Decimal("0.000000"),
        )
    with pytest.raises(ValueError, match="transition_ratio"):
        PaperPhase2StatusMatrixRow(
            "phase_2_evidence_observed",
            "phase_2_evidence_observed",
            0,
            Decimal("0.1"),
        )
    with pytest.raises(ValueError, match="transition_ratio"):
        PaperPhase2StatusMatrixRow(
            "phase_2_evidence_observed",
            "phase_2_evidence_observed",
            0,
            DerivedDecimal("0.000000"),
        )


def _row(
    report: PaperPhase2StatusMatrixReport,
    from_status: str,
    to_status: str,
) -> PaperPhase2StatusMatrixRow:
    return next(
        row
        for row in report.rows
        if row.from_status == from_status and row.to_status == to_status
    )
