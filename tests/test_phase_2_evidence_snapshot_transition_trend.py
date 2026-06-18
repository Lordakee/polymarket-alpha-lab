from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    PaperPhase2EvidenceGapRow,
    PaperPhase2EvidenceSnapshotReport,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_transition import (
    PaperPhase2EvidenceSnapshotTransitionConfig,
    PaperPhase2EvidenceSnapshotTransitionReport,
    build_paper_phase_2_evidence_snapshot_transition_report,
)
from polymarket_alpha_lab.phase_2_evidence_snapshot_transition_trend import (
    PaperPhase2EvidenceSnapshotTransitionTrendConfig,
    PaperPhase2EvidenceSnapshotTransitionTrendGapRow,
    PaperPhase2EvidenceSnapshotTransitionTrendReport,
    build_paper_phase_2_evidence_snapshot_transition_trend_report,
)


GENERATED_AT = datetime(2026, 6, 18, 20, 0, tzinfo=UTC)


def _config(**overrides) -> PaperPhase2EvidenceSnapshotTransitionTrendConfig:
    values = {"config_version": "phase-2-evidence-snapshot-transition-trend-v0"}
    values.update(overrides)
    return PaperPhase2EvidenceSnapshotTransitionTrendConfig(**values)


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


def _observed_snapshot(generated_at: datetime) -> PaperPhase2EvidenceSnapshotReport:
    return _snapshot(generated_at=generated_at)


def _transition(
    *snapshots: PaperPhase2EvidenceSnapshotReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperPhase2EvidenceSnapshotTransitionReport:
    return build_paper_phase_2_evidence_snapshot_transition_report(
        snapshots,
        config=PaperPhase2EvidenceSnapshotTransitionConfig(
            config_version="phase-2-evidence-snapshot-transition-v0",
        ),
        generated_at=generated_at,
    )


def _trend(
    *reports: PaperPhase2EvidenceSnapshotTransitionReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperPhase2EvidenceSnapshotTransitionTrendReport:
    return build_paper_phase_2_evidence_snapshot_transition_trend_report(
        reports,
        config=_config(),
        generated_at=generated_at,
    )


def test_phase_2_evidence_snapshot_transition_trend_reports_empty_history():
    report = _trend()

    assert isinstance(report, PaperPhase2EvidenceSnapshotTransitionTrendReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "phase-2-evidence-snapshot-transition-trend-v0"
    assert report.transition_report_count == 0
    assert report.total_snapshot_report_count == 0
    assert report.total_transition_count == 0
    assert report.first_transition_report_generated_at is None
    assert report.latest_transition_report_generated_at is None
    assert report.latest_from_status is None
    assert report.latest_to_status is None
    assert report.latest_introduced_gap_names == ()
    assert report.latest_cleared_gap_names == ()
    assert report.total_introduced_gap_count == 0
    assert report.total_cleared_gap_count == 0
    assert report.total_persistent_gap_count == 0
    assert report.gap_rows == tuple(
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            evidence_gap_name=gap_name,
            introduced_count=0,
            cleared_count=0,
            persistent_count=0,
            transition_presence_ratio=None,
        )
        for gap_name in EVIDENCE_GAP_NAMES
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_evidence_snapshot_transition_trend_summarizes_append_order_latest():
    first = _transition(
        _not_observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
    )
    second = _transition(
        _gap_snapshot(
            datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
        _observed_snapshot(datetime(2026, 6, 18, 8, 0, tzinfo=UTC)),
    )

    report = _trend(first, second)

    assert report.transition_report_count == 2
    assert report.total_snapshot_report_count == 4
    assert report.total_transition_count == 2
    assert report.first_transition_report_generated_at == first.generated_at
    assert report.latest_transition_report_generated_at == second.generated_at
    assert report.latest_from_status == "phase_2_evidence_gaps"
    assert report.latest_to_status == "phase_2_evidence_observed"
    assert report.latest_introduced_gap_names == ()
    assert report.latest_cleared_gap_names == ("thin_calibration_sample",)


def test_phase_2_evidence_snapshot_transition_trend_counts_gap_changes():
    report = _trend(
        _transition(
            _not_observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
            _gap_snapshot(
                datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
                "thin_calibration_sample",
            ),
            _quality_snapshot(datetime(2026, 6, 18, 12, 0, tzinfo=UTC)),
        ),
        _transition(
            _gap_snapshot(
                datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
                "thin_calibration_sample",
                "thin_segment_probability_samples",
            ),
            _observed_snapshot(datetime(2026, 6, 18, 14, 0, tzinfo=UTC)),
        ),
    )

    assert report.total_transition_count == 3
    assert report.total_introduced_gap_count == 2
    assert report.total_cleared_gap_count == 5
    assert report.total_persistent_gap_count == 0
    assert _gap_row(report, "thin_calibration_sample") == (
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            "thin_calibration_sample",
            introduced_count=1,
            cleared_count=2,
            persistent_count=0,
            transition_presence_ratio=Decimal("1.000000"),
        )
    )
    assert _gap_row(report, "calibration_quality_flags_present") == (
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            "calibration_quality_flags_present",
            introduced_count=1,
            cleared_count=0,
            persistent_count=0,
            transition_presence_ratio=Decimal("0.333333"),
        )
    )


def test_phase_2_evidence_snapshot_transition_trend_aggregates_gap_totals_and_ratios():
    report = _trend(
        _transition(
            _gap_snapshot(
                datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
                "thin_calibration_sample",
            ),
            _gap_snapshot(
                datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
                "thin_calibration_sample",
                "thin_segment_probability_samples",
            ),
            _observed_snapshot(datetime(2026, 6, 18, 12, 0, tzinfo=UTC)),
        ),
        _transition(
            _observed_snapshot(datetime(2026, 6, 18, 13, 0, tzinfo=UTC)),
            _gap_snapshot(
                datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
                "thin_calibration_sample",
                "return_only_segments_present",
            ),
            _gap_snapshot(
                datetime(2026, 6, 18, 15, 0, tzinfo=UTC),
                "thin_calibration_sample",
                "return_only_segments_present",
            ),
        ),
    )

    assert tuple(row.evidence_gap_name for row in report.gap_rows) == EVIDENCE_GAP_NAMES
    assert report.total_snapshot_report_count == 6
    assert report.total_transition_count == 4
    assert report.total_introduced_gap_count == 3
    assert report.total_cleared_gap_count == 2
    assert report.total_persistent_gap_count == 3
    assert _gap_row(report, "thin_calibration_sample") == (
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            "thin_calibration_sample",
            introduced_count=1,
            cleared_count=1,
            persistent_count=2,
            transition_presence_ratio=Decimal("1.000000"),
        )
    )
    assert _gap_row(report, "thin_segment_probability_samples") == (
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            "thin_segment_probability_samples",
            introduced_count=1,
            cleared_count=1,
            persistent_count=0,
            transition_presence_ratio=Decimal("0.500000"),
        )
    )
    assert _gap_row(report, "return_only_segments_present") == (
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            "return_only_segments_present",
            introduced_count=1,
            cleared_count=0,
            persistent_count=1,
            transition_presence_ratio=Decimal("0.500000"),
        )
    )
    assert type(_gap_row(report, "return_only_segments_present").transition_presence_ratio) is Decimal
    assert (
        _gap_row(
            report,
            "return_only_segments_present",
        ).transition_presence_ratio.as_tuple().exponent
        == -6
    )


def test_phase_2_evidence_snapshot_transition_trend_allows_latest_empty_report():
    report = _trend(
        _transition(
            _gap_snapshot(
                datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
                "thin_calibration_sample",
            ),
            _observed_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
        ),
        _transition(_observed_snapshot(datetime(2026, 6, 18, 12, 0, tzinfo=UTC))),
    )

    assert report.transition_report_count == 2
    assert report.total_transition_count == 1
    assert report.latest_from_status is None
    assert report.latest_to_status is None
    assert report.latest_introduced_gap_names == ()
    assert report.latest_cleared_gap_names == ()
    assert _gap_row(report, "thin_calibration_sample").cleared_count == 1


def test_phase_2_evidence_snapshot_transition_trend_normalizes_generated_at_to_utc():
    report = build_paper_phase_2_evidence_snapshot_transition_trend_report(
        (),
        config=_config(),
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT


def test_phase_2_evidence_snapshot_transition_trend_normalizes_report_timestamps_to_utc():
    first_generated_at = datetime(
        2026,
        6,
        18,
        21,
        30,
        tzinfo=timezone(timedelta(hours=1)),
    )
    latest_generated_at = datetime(
        2026,
        6,
        18,
        12,
        45,
        tzinfo=timezone(timedelta(hours=-7)),
    )

    report = _trend(
        _transition(
            _observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
            _gap_snapshot(
                datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
                "thin_calibration_sample",
            ),
            generated_at=first_generated_at,
        ),
        _transition(
            _gap_snapshot(
                datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
                "thin_calibration_sample",
            ),
            _observed_snapshot(datetime(2026, 6, 18, 13, 0, tzinfo=UTC)),
            generated_at=latest_generated_at,
        ),
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.first_transition_report_generated_at == datetime(
        2026,
        6,
        18,
        20,
        30,
        tzinfo=UTC,
    )
    assert report.latest_transition_report_generated_at == datetime(
        2026,
        6,
        18,
        19,
        45,
        tzinfo=UTC,
    )


def test_phase_2_evidence_snapshot_transition_trend_rejects_invalid_inputs_and_flags():
    valid_report = _transition(
        _gap_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC), "thin_calibration_sample"),
        _observed_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    for invalid_reports in (
        object(),
        "reports",
        b"reports",
        {"report": valid_report},
        (report for report in (valid_report,)),
    ):
        with pytest.raises(ValueError, match="transition_reports"):
            build_paper_phase_2_evidence_snapshot_transition_trend_report(
                invalid_reports,
                config=_config(),
                generated_at=GENERATED_AT,
            )
    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotTransitionReport"):
        build_paper_phase_2_evidence_snapshot_transition_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_evidence_snapshot_transition_trend_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_evidence_snapshot_transition_trend_report(
            (),
            config=_config(),
            generated_at="now",
        )

    for flag_name in ("paper_only", "report_only", "readonly"):
        source_report = _transition(
            _gap_snapshot(
                datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
                "thin_calibration_sample",
            ),
            _observed_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
        )
        object.__setattr__(source_report, flag_name, False)
        with pytest.raises(ValueError, match=flag_name):
            build_paper_phase_2_evidence_snapshot_transition_trend_report(
                (source_report,),
                config=_config(),
                generated_at=GENERATED_AT,
            )


def test_phase_2_evidence_snapshot_transition_trend_rejects_subclassed_public_inputs():
    class DerivedConfig(PaperPhase2EvidenceSnapshotTransitionTrendConfig):
        pass

    class DerivedTransitionReport(PaperPhase2EvidenceSnapshotTransitionReport):
        pass

    transition_report = _transition(
        _observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
    )

    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_evidence_snapshot_transition_trend_report(
            (),
            config=DerivedConfig(
                config_version="phase-2-evidence-snapshot-transition-trend-v0",
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotTransitionReport"):
        build_paper_phase_2_evidence_snapshot_transition_trend_report(
            (DerivedTransitionReport(**transition_report.__dict__),),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_phase_2_evidence_snapshot_transition_trend_dataclasses_revalidate_consistency():
    report = _trend(
        _transition(
            _gap_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC), "thin_calibration_sample"),
            _observed_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.total_transition_count = 99
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="total_snapshot_report_count"):
        replace(report, total_snapshot_report_count=3)
    with pytest.raises(ValueError, match="gap_rows"):
        replace(report, gap_rows=tuple(reversed(report.gap_rows)))
    with pytest.raises(ValueError, match="latest_from_status"):
        replace(report, latest_from_status="unknown_status")
    with pytest.raises(ValueError, match="latest_to_status"):
        replace(report, latest_to_status="unknown_status")
    with pytest.raises(ValueError, match="latest_cleared_gap_names"):
        replace(report, latest_cleared_gap_names=())
    drifted_row = replace(
        report.gap_rows[1],
        transition_presence_ratio=Decimal("0.500000"),
    )
    with pytest.raises(ValueError, match="transition_presence_ratio"):
        replace(
            report,
            gap_rows=(
                report.gap_rows[0],
                drifted_row,
                *report.gap_rows[2:],
            ),
        )


def test_phase_2_evidence_snapshot_transition_trend_dataclasses_are_frozen():
    config = _config()
    row = PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
        "thin_calibration_sample",
        introduced_count=1,
        cleared_count=0,
        persistent_count=0,
        transition_presence_ratio=Decimal("1.000000"),
    )
    transition_report = _transition(
        _observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
    )
    report = _trend(
        transition_report,
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"
    with pytest.raises(FrozenInstanceError):
        row.introduced_count = 2
    with pytest.raises(FrozenInstanceError):
        report.readonly = False


def test_phase_2_evidence_snapshot_transition_trend_rejects_scalar_subclasses():
    class DerivedDecimal(Decimal):
        pass

    class DerivedInt(int):
        pass

    class DerivedString(str):
        pass

    transition_report = _transition(
        _observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
    )
    report = _trend(transition_report)

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2EvidenceSnapshotTransitionTrendConfig(
            config_version=DerivedString(
                "phase-2-evidence-snapshot-transition-trend-v0",
            ),
        )
    with pytest.raises(ValueError, match="introduced_count"):
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            "thin_calibration_sample",
            introduced_count=DerivedInt(1),
            cleared_count=0,
            persistent_count=0,
            transition_presence_ratio=Decimal("1.000000"),
        )
    with pytest.raises(ValueError, match="cleared_count"):
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            "thin_calibration_sample",
            introduced_count=0,
            cleared_count=True,
            persistent_count=0,
            transition_presence_ratio=Decimal("1.000000"),
        )
    with pytest.raises(ValueError, match="transition_presence_ratio"):
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            "thin_calibration_sample",
            introduced_count=1,
            cleared_count=0,
            persistent_count=0,
            transition_presence_ratio=DerivedDecimal("1.000000"),
        )
    with pytest.raises(ValueError, match="transition_report_count"):
        replace(report, transition_report_count=DerivedInt(1))


def test_phase_2_evidence_snapshot_transition_trend_rejects_gap_name_string_subclass():
    class DerivedString(str):
        pass

    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            DerivedString("thin_calibration_sample"),
            introduced_count=1,
            cleared_count=0,
            persistent_count=0,
            transition_presence_ratio=Decimal("1.000000"),
        )


@pytest.mark.parametrize(
    ("field_name", "gap_name"),
    (
        ("latest_introduced_gap_names", "thin_calibration_sample"),
        ("latest_cleared_gap_names", "thin_calibration_sample"),
    ),
)
def test_phase_2_evidence_snapshot_transition_trend_rejects_latest_gap_string_subclasses(
    field_name,
    gap_name,
):
    class DerivedString(str):
        pass

    if field_name == "latest_introduced_gap_names":
        report = _trend(
            _transition(
                _observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
                _gap_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC), gap_name),
            ),
        )
    else:
        report = _trend(
            _transition(
                _gap_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC), gap_name),
                _observed_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
            ),
        )

    with pytest.raises(ValueError, match=field_name):
        replace(report, **{field_name: (DerivedString(gap_name),)})


@pytest.mark.parametrize(
    ("field_name", "status"),
    (
        ("latest_from_status", "phase_2_evidence_observed"),
        ("latest_to_status", "phase_2_evidence_gaps"),
    ),
)
def test_phase_2_evidence_snapshot_transition_trend_rejects_latest_status_string_subclasses(
    field_name,
    status,
):
    class DerivedString(str):
        pass

    report = _trend(
        _transition(
            _observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
            _gap_snapshot(datetime(2026, 6, 18, 11, 0, tzinfo=UTC), "thin_calibration_sample"),
        ),
    )

    with pytest.raises(ValueError, match=field_name):
        replace(report, **{field_name: DerivedString(status)})


def test_phase_2_evidence_snapshot_transition_trend_requires_deterministic_gap_sequences():
    transition_report = _transition(
        _observed_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "thin_calibration_sample",
            "thin_segment_probability_samples",
        ),
    )
    report = _trend(transition_report)

    assert report.latest_introduced_gap_names == (
        "thin_calibration_sample",
        "thin_segment_probability_samples",
    )
    with pytest.raises(ValueError, match="latest_introduced_gap_names"):
        replace(
            report,
            latest_introduced_gap_names=(
                "thin_segment_probability_samples",
                "thin_calibration_sample",
            ),
        )
    with pytest.raises(ValueError, match="latest_introduced_gap_names"):
        replace(
            report,
            latest_introduced_gap_names=(
                "thin_calibration_sample",
                "thin_calibration_sample",
            ),
        )


def test_phase_2_evidence_snapshot_transition_trend_rows_and_all_are_exact():
    from polymarket_alpha_lab import phase_2_evidence_snapshot_transition_trend

    assert phase_2_evidence_snapshot_transition_trend.__all__ == (
        "PaperPhase2EvidenceSnapshotTransitionTrendConfig",
        "PaperPhase2EvidenceSnapshotTransitionTrendGapRow",
        "PaperPhase2EvidenceSnapshotTransitionTrendReport",
        "build_paper_phase_2_evidence_snapshot_transition_trend_report",
    )

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2EvidenceSnapshotTransitionTrendConfig(config_version=" ")
    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow("unknown", 0, 0, 0, None)
    with pytest.raises(ValueError, match="transition_presence_ratio"):
        PaperPhase2EvidenceSnapshotTransitionTrendGapRow(
            "thin_calibration_sample",
            1,
            0,
            0,
            Decimal("0.1"),
        )


def _gap_row(
    report: PaperPhase2EvidenceSnapshotTransitionTrendReport,
    gap_name: str,
) -> PaperPhase2EvidenceSnapshotTransitionTrendGapRow:
    return next(row for row in report.gap_rows if row.evidence_gap_name == gap_name)
