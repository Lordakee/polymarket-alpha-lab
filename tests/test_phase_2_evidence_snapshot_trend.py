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
from polymarket_alpha_lab.phase_2_evidence_snapshot_trend import (
    PaperPhase2EvidenceSnapshotTrendConfig,
    PaperPhase2EvidenceSnapshotTrendGapRow,
    PaperPhase2EvidenceSnapshotTrendReport,
    PaperPhase2EvidenceSnapshotTrendStatusRow,
    build_paper_phase_2_evidence_snapshot_trend_report,
)


GENERATED_AT = datetime(2026, 6, 18, 18, 0, tzinfo=UTC)


def _config(**overrides) -> PaperPhase2EvidenceSnapshotTrendConfig:
    values = {"config_version": "phase-2-evidence-snapshot-trend-v0"}
    values.update(overrides)
    return PaperPhase2EvidenceSnapshotTrendConfig(**values)


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
    segment_count: int | None = 2,
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
        segment_count=None,
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
        calibration_present=True,
        segment_present=True,
        calibration_count=12 if "thin_calibration_sample" in gap_names else 30,
        calibration_status="calibration_evidence_observed",
        segment_count=4,
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


def _trend_report(
    *snapshots: PaperPhase2EvidenceSnapshotReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperPhase2EvidenceSnapshotTrendReport:
    return build_paper_phase_2_evidence_snapshot_trend_report(
        snapshots,
        config=_config(),
        generated_at=generated_at,
    )


def test_phase_2_evidence_snapshot_trend_reports_empty_sequence():
    report = _trend_report()

    assert isinstance(report, PaperPhase2EvidenceSnapshotTrendReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "phase-2-evidence-snapshot-trend-v0"
    assert report.snapshot_report_count == 0
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.latest_status is None
    assert report.latest_evidence_gap_names == ()
    assert report.consecutive_quality_flag_count == 0
    assert report.consecutive_gap_count == 0
    assert report.consecutive_non_observed_count == 0
    assert report.status_rows == tuple(
        PaperPhase2EvidenceSnapshotTrendStatusRow(status, 0, None)
        for status in SNAPSHOT_STATUSES
    )
    assert report.gap_rows == tuple(
        PaperPhase2EvidenceSnapshotTrendGapRow(gap_name, 0, None)
        for gap_name in EVIDENCE_GAP_NAMES
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_evidence_snapshot_trend_preserves_append_order_latest_and_streaks():
    first_append = _snapshot(
        generated_at=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
    )
    earlier_timestamp = _gap_snapshot(
        datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "thin_calibration_sample",
    )
    latest_append = _gap_snapshot(
        datetime(2026, 6, 18, 15, 0, tzinfo=UTC),
        "thin_calibration_sample",
        "thin_segment_probability_samples",
        "return_only_segments_present",
    )

    report = _trend_report(first_append, earlier_timestamp, latest_append)

    assert report.snapshot_report_count == 3
    assert report.first_report_generated_at == first_append.generated_at
    assert report.latest_report_generated_at == latest_append.generated_at
    assert report.latest_status == "phase_2_evidence_gaps"
    assert report.latest_evidence_gap_names == (
        "thin_calibration_sample",
        "thin_segment_probability_samples",
        "return_only_segments_present",
    )
    assert report.consecutive_quality_flag_count == 0
    assert report.consecutive_gap_count == 2
    assert report.consecutive_non_observed_count == 2


def test_phase_2_evidence_snapshot_trend_counts_statuses_and_gaps():
    report = _trend_report(
        _not_observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
        _quality_snapshot(datetime(2026, 6, 18, 12, 0, tzinfo=UTC)),
        _snapshot(generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC)),
    )

    assert report.status_rows == (
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_not_observed",
            1,
            Decimal("0.250000"),
        ),
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_gaps",
            1,
            Decimal("0.250000"),
        ),
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_quality_flags",
            1,
            Decimal("0.250000"),
        ),
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_observed",
            1,
            Decimal("0.250000"),
        ),
    )
    assert report.gap_rows == (
        PaperPhase2EvidenceSnapshotTrendGapRow(
            "missing_calibration_report",
            1,
            Decimal("0.250000"),
        ),
        PaperPhase2EvidenceSnapshotTrendGapRow(
            "thin_calibration_sample",
            1,
            Decimal("0.250000"),
        ),
        PaperPhase2EvidenceSnapshotTrendGapRow(
            "calibration_quality_flags_present",
            1,
            Decimal("0.250000"),
        ),
        PaperPhase2EvidenceSnapshotTrendGapRow(
            "missing_segment_summary",
            1,
            Decimal("0.250000"),
        ),
        PaperPhase2EvidenceSnapshotTrendGapRow(
            "thin_segment_probability_samples",
            0,
            Decimal("0.000000"),
        ),
        PaperPhase2EvidenceSnapshotTrendGapRow(
            "return_only_segments_present",
            0,
            Decimal("0.000000"),
        ),
    )


def test_phase_2_evidence_snapshot_trend_ratios_are_quantized_to_six_places():
    report = _trend_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
        _gap_snapshot(
            datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
    )

    assert report.status_rows == (
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_not_observed",
            0,
            Decimal("0.000000"),
        ),
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_gaps",
            2,
            Decimal("0.666667"),
        ),
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_quality_flags",
            0,
            Decimal("0.000000"),
        ),
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_observed",
            1,
            Decimal("0.333333"),
        ),
    )
    assert all(
        row.snapshot_ratio.as_tuple().exponent == Decimal("0.000001").as_tuple().exponent
        for row in report.status_rows
        if row.snapshot_ratio is not None
    )
    assert report.gap_rows[1] == PaperPhase2EvidenceSnapshotTrendGapRow(
        "thin_calibration_sample",
        2,
        Decimal("0.666667"),
    )
    assert report.gap_rows[1].gap_ratio.as_tuple().exponent == (
        Decimal("0.000001").as_tuple().exponent
    )


def test_phase_2_evidence_snapshot_trend_counts_quality_and_non_observed_streaks():
    report = _trend_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _quality_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
        _quality_snapshot(datetime(2026, 6, 18, 12, 0, tzinfo=UTC)),
    )

    assert report.latest_status == "phase_2_evidence_quality_flags"
    assert report.consecutive_quality_flag_count == 2
    assert report.consecutive_gap_count == 0
    assert report.consecutive_non_observed_count == 2


def test_phase_2_evidence_snapshot_trend_normalizes_generated_at_to_utc():
    report = _trend_report(
        generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT


def test_phase_2_evidence_snapshot_trend_normalizes_direct_report_datetimes_to_utc():
    report = PaperPhase2EvidenceSnapshotTrendReport(
        generated_at=datetime(2026, 6, 18, 18, 0),
        config_version="phase-2-evidence-snapshot-trend-v0",
        snapshot_report_count=1,
        first_report_generated_at=datetime(
            2026,
            6,
            18,
            11,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
        latest_report_generated_at=datetime(2026, 6, 18, 18, 0),
        latest_status="phase_2_evidence_observed",
        latest_evidence_gap_names=(),
        consecutive_quality_flag_count=0,
        consecutive_gap_count=0,
        consecutive_non_observed_count=0,
        status_rows=(
            PaperPhase2EvidenceSnapshotTrendStatusRow(
                "phase_2_evidence_not_observed",
                0,
                Decimal("0.000000"),
            ),
            PaperPhase2EvidenceSnapshotTrendStatusRow(
                "phase_2_evidence_gaps",
                0,
                Decimal("0.000000"),
            ),
            PaperPhase2EvidenceSnapshotTrendStatusRow(
                "phase_2_evidence_quality_flags",
                0,
                Decimal("0.000000"),
            ),
            PaperPhase2EvidenceSnapshotTrendStatusRow(
                "phase_2_evidence_observed",
                1,
                Decimal("1.000000"),
            ),
        ),
        gap_rows=tuple(
            PaperPhase2EvidenceSnapshotTrendGapRow(gap_name, 0, Decimal("0.000000"))
            for gap_name in EVIDENCE_GAP_NAMES
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.first_report_generated_at == GENERATED_AT
    assert report.first_report_generated_at.tzinfo is UTC
    assert report.latest_report_generated_at == GENERATED_AT
    assert report.latest_report_generated_at.tzinfo is UTC


def test_phase_2_evidence_snapshot_trend_rejects_invalid_builder_inputs():
    invalid_inputs = (
        object(),
        "not snapshots",
        b"not snapshots",
        {"snapshot": _snapshot()},
        (snapshot for snapshot in ()),
    )
    for snapshots in invalid_inputs:
        with pytest.raises(ValueError, match="snapshots must be a list or tuple"):
            build_paper_phase_2_evidence_snapshot_trend_report(
                snapshots,
                config=_config(),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        build_paper_phase_2_evidence_snapshot_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_evidence_snapshot_trend_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_evidence_snapshot_trend_report(
            (),
            config=_config(),
            generated_at="now",
        )


def test_phase_2_evidence_snapshot_trend_rejects_scalar_subclasses_at_boundary():
    class StrSubclass(str):
        pass

    class IntSubclass(int):
        pass

    class DatetimeSubclass(datetime):
        pass

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2EvidenceSnapshotTrendConfig(
            config_version=StrSubclass("phase-2-evidence-snapshot-trend-v0"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_evidence_snapshot_trend_report(
            (),
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 18, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="snapshot_count"):
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_observed",
            IntSubclass(1),
            Decimal("1.000000"),
        )
    with pytest.raises(ValueError, match="snapshot_ratio"):
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_observed",
            1,
            DecimalSubclass("1.000000"),
        )


def test_phase_2_evidence_snapshot_trend_rejects_scalar_subclasses_in_row_string_fields():
    class StrSubclass(str):
        pass

    with pytest.raises(ValueError, match="snapshot_status"):
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            StrSubclass("phase_2_evidence_observed"),
            1,
            Decimal("1.000000"),
        )
    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2EvidenceSnapshotTrendGapRow(
            StrSubclass("thin_calibration_sample"),
            1,
            Decimal("1.000000"),
        )


def test_phase_2_evidence_snapshot_trend_rejects_scalar_subclasses_in_report_string_fields():
    class StrSubclass(str):
        pass

    report = _trend_report(
        _gap_snapshot(
            datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            "thin_calibration_sample",
        )
    )

    with pytest.raises(ValueError, match="latest_status"):
        replace(report, latest_status=StrSubclass("phase_2_evidence_gaps"))
    with pytest.raises(ValueError, match="latest_evidence_gap_names"):
        replace(
            report,
            latest_evidence_gap_names=(StrSubclass("thin_calibration_sample"),),
        )


def test_phase_2_evidence_snapshot_trend_rejects_scalar_subclasses_in_source_snapshot_fields():
    class StrSubclass(str):
        pass

    source_report = _gap_snapshot(
        datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "thin_calibration_sample",
    )
    object.__setattr__(source_report, "status", StrSubclass("phase_2_evidence_gaps"))
    object.__setattr__(
        source_report,
        "evidence_gap_names",
        (StrSubclass("thin_calibration_sample"),),
    )

    with pytest.raises(ValueError, match="status"):
        build_paper_phase_2_evidence_snapshot_trend_report(
            (source_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_phase_2_evidence_snapshot_trend_rejects_source_report_subclasses():
    class SnapshotReportSubclass(PaperPhase2EvidenceSnapshotReport):
        pass

    source_report = SnapshotReportSubclass(
        generated_at=GENERATED_AT,
        config_version="phase-2-evidence-snapshot-v0",
        status="phase_2_evidence_observed",
        calibration_report_present=True,
        segment_summary_report_present=True,
        calibration_observation_count=30,
        calibration_status="calibration_evidence_observed",
        segment_observation_count=2,
        segment_count=2,
        probability_segment_count=2,
        return_only_segment_count=0,
        thin_probability_segment_count=0,
        probability_segment_coverage_ratio=Decimal("1.000000"),
        return_only_segment_ratio=Decimal("0.000000"),
        evidence_gap_count=0,
        evidence_gap_names=(),
        evidence_gaps=_gap_rows(),
    )

    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        build_paper_phase_2_evidence_snapshot_trend_report(
            (source_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_phase_2_evidence_snapshot_trend_rejects_source_reports_with_nonfinal_flags(
    flag_name,
):
    source_report = _snapshot()
    object.__setattr__(source_report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_paper_phase_2_evidence_snapshot_trend_report(
            (source_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_phase_2_evidence_snapshot_trend_dataclasses_are_frozen_and_revalidate_flags():
    report = _trend_report(_snapshot())
    config = _config()
    status_row = report.status_rows[-1]
    gap_row = report.gap_rows[0]

    with pytest.raises(FrozenInstanceError):
        config.config_version = "other"
    with pytest.raises(FrozenInstanceError):
        status_row.snapshot_count = 2
    with pytest.raises(FrozenInstanceError):
        gap_row.gap_count = 1
    with pytest.raises(FrozenInstanceError):
        report.latest_status = "phase_2_evidence_gaps"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_phase_2_evidence_snapshot_trend_revalidates_empty_consistency():
    report = _trend_report()

    with pytest.raises(ValueError, match="latest_status"):
        replace(report, latest_status="phase_2_evidence_observed")
    with pytest.raises(ValueError, match="latest_evidence_gap_names"):
        replace(report, latest_evidence_gap_names=("thin_calibration_sample",))
    with pytest.raises(ValueError, match="first_report_generated_at"):
        replace(report, first_report_generated_at=GENERATED_AT)


def test_phase_2_evidence_snapshot_trend_revalidates_rows_and_streaks():
    report = _trend_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _quality_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(ValueError, match="status_rows"):
        replace(report, status_rows=tuple(reversed(report.status_rows)))
    drifted_status_row = replace(report.status_rows[-2])
    object.__setattr__(drifted_status_row, "snapshot_ratio", Decimal("0.250000"))
    with pytest.raises(ValueError, match="status_rows ratios"):
        replace(
            report,
            status_rows=(
                report.status_rows[0],
                report.status_rows[1],
                drifted_status_row,
                report.status_rows[3],
            ),
        )
    with pytest.raises(ValueError, match="gap_rows"):
        replace(report, gap_rows=tuple(reversed(report.gap_rows)))
    drifted_gap_row = replace(report.gap_rows[2])
    object.__setattr__(drifted_gap_row, "gap_ratio", Decimal("0.000000"))
    with pytest.raises(ValueError, match="gap_rows ratios"):
        replace(
            report,
            gap_rows=(
                report.gap_rows[0],
                report.gap_rows[1],
                drifted_gap_row,
                *report.gap_rows[3:],
            ),
        )
    with pytest.raises(ValueError, match="latest_status"):
        replace(
            report,
            status_rows=(
                report.status_rows[0],
                report.status_rows[1],
                PaperPhase2EvidenceSnapshotTrendStatusRow(
                    "phase_2_evidence_quality_flags",
                    0,
                    Decimal("0.000000"),
                ),
                PaperPhase2EvidenceSnapshotTrendStatusRow(
                    "phase_2_evidence_observed",
                    2,
                    Decimal("1.000000"),
                ),
            ),
        )
    with pytest.raises(ValueError, match="requires a streak"):
        replace(report, consecutive_quality_flag_count=0)
    with pytest.raises(ValueError, match="quality flag streak"):
        replace(report, consecutive_quality_flag_count=2)
    with pytest.raises(ValueError, match="non-observed"):
        replace(report, consecutive_non_observed_count=0)


def test_phase_2_evidence_snapshot_trend_revalidates_latest_gap_name_order():
    report = _trend_report(
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "thin_calibration_sample",
            "thin_segment_probability_samples",
            "return_only_segments_present",
        ),
    )

    with pytest.raises(ValueError, match="deterministic order"):
        replace(
            report,
            latest_evidence_gap_names=tuple(reversed(report.latest_evidence_gap_names)),
        )


def test_phase_2_evidence_snapshot_trend_rows_and_all_are_exact():
    from polymarket_alpha_lab import phase_2_evidence_snapshot_trend

    assert phase_2_evidence_snapshot_trend.__all__ == (
        "PaperPhase2EvidenceSnapshotTrendConfig",
        "PaperPhase2EvidenceSnapshotTrendGapRow",
        "PaperPhase2EvidenceSnapshotTrendReport",
        "PaperPhase2EvidenceSnapshotTrendStatusRow",
        "build_paper_phase_2_evidence_snapshot_trend_report",
    )

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2EvidenceSnapshotTrendConfig(
            config_version=" phase-2-evidence-snapshot-trend-v0 ",
        )
    with pytest.raises(ValueError, match="snapshot_status"):
        PaperPhase2EvidenceSnapshotTrendStatusRow("unknown", 0, None)
    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2EvidenceSnapshotTrendGapRow("unknown", 0, None)
    with pytest.raises(ValueError, match="snapshot_ratio"):
        PaperPhase2EvidenceSnapshotTrendStatusRow(
            "phase_2_evidence_observed",
            1,
            Decimal("0.1"),
        )
