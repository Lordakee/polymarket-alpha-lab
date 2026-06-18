from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    PaperPhase2EvidenceGapRow,
    PaperPhase2EvidenceSnapshotReport,
)
from polymarket_alpha_lab.phase_2_gap_stability import (
    PaperPhase2GapStabilityConfig,
    PaperPhase2GapStabilityReport,
    PaperPhase2GapStabilityRow,
    build_paper_phase_2_gap_stability_report,
)


GENERATED_AT = datetime(2026, 6, 18, 20, 0, tzinfo=UTC)
CONFIG_VERSION = "phase-2-gap-stability-v0"


def _config(**overrides) -> PaperPhase2GapStabilityConfig:
    values = {"config_version": CONFIG_VERSION}
    values.update(overrides)
    return PaperPhase2GapStabilityConfig(**values)


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
    gap_names: tuple[str, ...] = (),
) -> PaperPhase2EvidenceSnapshotReport:
    gap_name_set = set(gap_names)
    calibration_present = "missing_calibration_report" not in gap_name_set
    segment_present = "missing_segment_summary" not in gap_name_set
    probability_segment_count = 2 if segment_present else None
    return_only_segment_count = (
        2 if "return_only_segments_present" in gap_name_set else 0
    )
    thin_probability_segment_count = (
        1 if "thin_segment_probability_samples" in gap_name_set else 0
    )
    if not segment_present:
        segment_count = None
        segment_observation_count = None
        return_only_segment_count = None
        thin_probability_segment_count = None
        probability_segment_count = None
    else:
        segment_count = (probability_segment_count or 0) + (
            return_only_segment_count or 0
        )
        segment_observation_count = segment_count
    calibration_status = (
        None
        if not calibration_present
        else (
            "calibration_quality_flags"
            if "calibration_quality_flags_present" in gap_name_set
            else "calibration_evidence_observed"
        )
    )
    if not calibration_present:
        calibration_count = None
    elif "thin_calibration_sample" in gap_name_set:
        calibration_count = 12
    else:
        calibration_count = 30
    if "calibration_quality_flags_present" in gap_name_set:
        status = "phase_2_evidence_quality_flags"
    elif not calibration_present and not segment_present:
        status = "phase_2_evidence_not_observed"
    elif gap_names:
        status = "phase_2_evidence_gaps"
    else:
        status = "phase_2_evidence_observed"
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


def _gap_stability_report(
    *snapshots: PaperPhase2EvidenceSnapshotReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperPhase2GapStabilityReport:
    return build_paper_phase_2_gap_stability_report(
        snapshots,
        config=_config(),
        generated_at=generated_at,
    )


def _row(
    report: PaperPhase2GapStabilityReport,
    gap_name: str,
) -> PaperPhase2GapStabilityRow:
    return next(row for row in report.rows if row.evidence_gap_name == gap_name)


def test_phase_2_gap_stability_reports_empty_snapshot_sequence():
    report = _gap_stability_report()

    assert isinstance(report, PaperPhase2GapStabilityReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.snapshot_report_count == 0
    assert report.row_count == len(EVIDENCE_GAP_NAMES)
    assert report.stable_gap_names == ()
    assert report.cleared_gap_names == ()
    assert report.rows == tuple(
        PaperPhase2GapStabilityRow(
            gap_name,
            first_seen_index=None,
            latest_seen_index=None,
            occurrence_count=0,
            occurrence_ratio=None,
            consecutive_present_count=0,
            ever_cleared=False,
        )
        for gap_name in EVIDENCE_GAP_NAMES
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_gap_stability_marks_gap_stable_across_all_snapshots():
    first = _snapshot(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        gap_names=("thin_calibration_sample",),
    )
    second = _snapshot(
        generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        gap_names=("thin_calibration_sample",),
    )
    third = _snapshot(
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        gap_names=("thin_calibration_sample",),
    )

    report = _gap_stability_report(first, second, third)

    assert report.stable_gap_names == ("thin_calibration_sample",)
    assert report.cleared_gap_names == ()
    assert _row(report, "thin_calibration_sample") == PaperPhase2GapStabilityRow(
        "thin_calibration_sample",
        first_seen_index=0,
        latest_seen_index=2,
        occurrence_count=3,
        occurrence_ratio=Decimal("1.000000"),
        consecutive_present_count=3,
        ever_cleared=False,
    )


def test_phase_2_gap_stability_marks_cleared_gap_absent_from_latest_snapshot():
    first = _snapshot(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        gap_names=("thin_calibration_sample",),
    )
    second = _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC))

    report = _gap_stability_report(first, second)

    assert report.stable_gap_names == ()
    assert report.cleared_gap_names == ("thin_calibration_sample",)
    assert _row(report, "thin_calibration_sample") == PaperPhase2GapStabilityRow(
        "thin_calibration_sample",
        first_seen_index=0,
        latest_seen_index=0,
        occurrence_count=1,
        occurrence_ratio=Decimal("0.500000"),
        consecutive_present_count=0,
        ever_cleared=True,
    )


def test_phase_2_gap_stability_counts_intermittent_gap_and_latest_streak():
    first = _snapshot(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        gap_names=("return_only_segments_present",),
    )
    second = _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC))
    third = _snapshot(
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        gap_names=("return_only_segments_present",),
    )
    fourth = _snapshot(
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
        gap_names=("return_only_segments_present",),
    )

    report = _gap_stability_report(first, second, third, fourth)

    assert report.stable_gap_names == ()
    assert report.cleared_gap_names == ()
    assert _row(report, "return_only_segments_present") == PaperPhase2GapStabilityRow(
        "return_only_segments_present",
        first_seen_index=0,
        latest_seen_index=3,
        occurrence_count=3,
        occurrence_ratio=Decimal("0.750000"),
        consecutive_present_count=2,
        ever_cleared=True,
    )


def test_phase_2_gap_stability_uses_append_order_indexes_not_timestamps():
    first = _snapshot(
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        gap_names=("thin_calibration_sample",),
    )
    second = _snapshot(
        generated_at=datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
        gap_names=(
            "thin_calibration_sample",
            "return_only_segments_present",
        ),
    )
    third = _snapshot(
        generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        gap_names=("return_only_segments_present",),
    )

    report = _gap_stability_report(first, second, third)

    assert _row(report, "thin_calibration_sample").latest_seen_index == 1
    assert _row(report, "return_only_segments_present").first_seen_index == 1
    assert _row(report, "return_only_segments_present").latest_seen_index == 2
    assert report.cleared_gap_names == ("thin_calibration_sample",)


def test_phase_2_gap_stability_normalizes_generated_at_to_utc():
    report = _gap_stability_report(
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT


def test_phase_2_gap_stability_rejects_invalid_inputs_and_source_flags():
    invalid_inputs = (
        object(),
        "not snapshots",
        b"not snapshots",
        {"snapshot": _snapshot()},
        (snapshot for snapshot in ()),
    )
    for snapshots in invalid_inputs:
        with pytest.raises(ValueError, match="snapshots must be a list or tuple"):
            build_paper_phase_2_gap_stability_report(
                snapshots,
                config=_config(),
                generated_at=GENERATED_AT,
            )

    with pytest.raises(ValueError, match="PaperPhase2EvidenceSnapshotReport"):
        build_paper_phase_2_gap_stability_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_gap_stability_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_gap_stability_report(
            (),
            config=_config(),
            generated_at="now",
        )

    for flag_name in ("paper_only", "report_only", "readonly"):
        source_report = _snapshot()
        object.__setattr__(source_report, flag_name, False)
        with pytest.raises(ValueError, match=flag_name):
            build_paper_phase_2_gap_stability_report(
                (source_report,),
                config=_config(),
                generated_at=GENERATED_AT,
            )


def test_phase_2_gap_stability_rejects_subclassed_public_inputs():
    class DerivedConfig(PaperPhase2GapStabilityConfig):
        pass

    class DerivedDateTime(datetime):
        pass

    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_gap_stability_report(
            (),
            config=DerivedConfig(config_version=CONFIG_VERSION),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_gap_stability_report(
            (),
            config=_config(),
            generated_at=DerivedDateTime(2026, 6, 18, 20, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2GapStabilityConfig(config_version=type("DerivedString", (str,), {})("v0"))


def test_phase_2_gap_stability_rejects_str_subclass_gap_row_name():
    class DerivedString(str):
        pass

    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2GapStabilityRow(
            DerivedString("thin_calibration_sample"),
            first_seen_index=None,
            latest_seen_index=None,
            occurrence_count=0,
            occurrence_ratio=None,
            consecutive_present_count=0,
            ever_cleared=False,
        )


def test_phase_2_gap_stability_rejects_str_subclass_report_gap_name_sequences():
    class DerivedString(str):
        pass

    stable_report = _gap_stability_report(
        _snapshot(
            generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
        _snapshot(
            generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
    )
    cleared_report = _gap_stability_report(
        _snapshot(
            generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(ValueError, match="stable_gap_names"):
        replace(
            stable_report,
            stable_gap_names=(DerivedString("thin_calibration_sample"),),
        )
    with pytest.raises(ValueError, match="cleared_gap_names"):
        replace(
            cleared_report,
            cleared_gap_names=(DerivedString("thin_calibration_sample"),),
        )


def test_phase_2_gap_stability_dataclass_replace_consistency():
    report = _gap_stability_report(
        _snapshot(
            generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(FrozenInstanceError):
        report.row_count = 0
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=0)
    with pytest.raises(ValueError, match="stable_gap_names"):
        replace(report, stable_gap_names=("thin_calibration_sample",))
    with pytest.raises(ValueError, match="cleared_gap_names"):
        replace(report, cleared_gap_names=())
    with pytest.raises(ValueError, match="first_seen_index"):
        replace(
            report,
            rows=(
                PaperPhase2GapStabilityRow(
                    "missing_calibration_report",
                    first_seen_index=1,
                    latest_seen_index=None,
                    occurrence_count=0,
                    occurrence_ratio=Decimal("0.000000"),
                    consecutive_present_count=0,
                    ever_cleared=False,
                ),
                *report.rows[1:],
            ),
        )
    with pytest.raises(ValueError, match="latest_seen_index"):
        replace(
            report,
            rows=(
                report.rows[0],
                PaperPhase2GapStabilityRow(
                    "thin_calibration_sample",
                    first_seen_index=0,
                    latest_seen_index=2,
                    occurrence_count=1,
                    occurrence_ratio=Decimal("0.500000"),
                    consecutive_present_count=0,
                    ever_cleared=True,
                ),
                *report.rows[2:],
            ),
        )
    with pytest.raises(ValueError, match="ever_cleared"):
        replace(
            report,
            rows=(
                report.rows[0],
                replace(report.rows[1], ever_cleared=False),
                *report.rows[2:],
            ),
        )
    with pytest.raises(ValueError, match="consecutive_present_count"):
        replace(
            report,
            rows=(
                report.rows[0],
                replace(
                    report.rows[1],
                    latest_seen_index=1,
                    consecutive_present_count=0,
                    ever_cleared=True,
                ),
                *report.rows[2:],
            ),
        )
    stable_report = _gap_stability_report(
        _snapshot(
            generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
        _snapshot(
            generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
    )
    with pytest.raises(ValueError, match="ever_cleared"):
        replace(
            stable_report,
            rows=(
                stable_report.rows[0],
                replace(
                    stable_report.rows[1],
                    ever_cleared=True,
                ),
                *stable_report.rows[2:],
            ),
        )
    with pytest.raises(ValueError, match="consecutive_present_count"):
        replace(
            stable_report,
            rows=(
                stable_report.rows[0],
                replace(
                    stable_report.rows[1],
                    consecutive_present_count=1,
                ),
                *stable_report.rows[2:],
            ),
        )


def test_phase_2_gap_stability_validates_exact_ratio_exponent():
    report = _gap_stability_report(
        _snapshot(
            generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
        _snapshot(
            generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
        _snapshot(generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC)),
    )

    assert _row(report, "thin_calibration_sample").occurrence_ratio == Decimal(
        "0.666667",
    )
    assert _row(report, "thin_calibration_sample").occurrence_ratio.as_tuple().exponent == -6
    with pytest.raises(ValueError, match="occurrence_ratio"):
        PaperPhase2GapStabilityRow(
            "thin_calibration_sample",
            first_seen_index=0,
            latest_seen_index=0,
            occurrence_count=1,
            occurrence_ratio=Decimal("0.5"),
            consecutive_present_count=0,
            ever_cleared=True,
        )


def test_phase_2_gap_stability_quantizes_ratios_to_six_decimal_places():
    report = _gap_stability_report(
        _snapshot(
            generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
        _snapshot(generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC)),
        _snapshot(
            generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
    )

    assert _row(report, "thin_calibration_sample").occurrence_ratio == Decimal(
        "0.500000",
    )
    assert _row(report, "missing_calibration_report").occurrence_ratio == Decimal(
        "0.000000",
    )
    assert _row(report, "thin_calibration_sample").occurrence_ratio.as_tuple().exponent == -6
    assert _row(report, "missing_calibration_report").occurrence_ratio.as_tuple().exponent == -6


def test_phase_2_gap_stability_rejects_ratio_bool_and_decimal_subclasses():
    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="occurrence_ratio"):
        PaperPhase2GapStabilityRow(
            "thin_calibration_sample",
            first_seen_index=0,
            latest_seen_index=0,
            occurrence_count=1,
            occurrence_ratio=True,
            consecutive_present_count=0,
            ever_cleared=True,
        )

    with pytest.raises(ValueError, match="occurrence_ratio"):
        PaperPhase2GapStabilityRow(
            "thin_calibration_sample",
            first_seen_index=0,
            latest_seen_index=0,
            occurrence_count=1,
            occurrence_ratio=DerivedDecimal("0.500000"),
            consecutive_present_count=0,
            ever_cleared=True,
        )


def test_phase_2_gap_stability_rejects_bool_and_subclassed_int_indexes_and_counts():
    class DerivedInt(int):
        pass

    with pytest.raises(ValueError, match="first_seen_index"):
        PaperPhase2GapStabilityRow(
            "thin_calibration_sample",
            first_seen_index=DerivedInt(0),
            latest_seen_index=0,
            occurrence_count=1,
            occurrence_ratio=Decimal("0.500000"),
            consecutive_present_count=0,
            ever_cleared=True,
        )

    with pytest.raises(ValueError, match="latest_seen_index"):
        PaperPhase2GapStabilityRow(
            "thin_calibration_sample",
            first_seen_index=0,
            latest_seen_index=True,
            occurrence_count=1,
            occurrence_ratio=Decimal("0.500000"),
            consecutive_present_count=0,
            ever_cleared=True,
        )

    with pytest.raises(ValueError, match="occurrence_count"):
        PaperPhase2GapStabilityRow(
            "thin_calibration_sample",
            first_seen_index=0,
            latest_seen_index=0,
            occurrence_count=DerivedInt(1),
            occurrence_ratio=Decimal("0.500000"),
            consecutive_present_count=0,
            ever_cleared=True,
        )

    with pytest.raises(ValueError, match="consecutive_present_count"):
        PaperPhase2GapStabilityRow(
            "thin_calibration_sample",
            first_seen_index=0,
            latest_seen_index=0,
            occurrence_count=1,
            occurrence_ratio=Decimal("0.500000"),
            consecutive_present_count=True,
            ever_cleared=True,
        )


def test_phase_2_gap_stability_rejects_report_order_and_type_boundaries():
    report = _gap_stability_report(
        _snapshot(
            generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            gap_names=("thin_calibration_sample",),
        ),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(ValueError, match="stable_gap_names"):
        replace(report, stable_gap_names=("thin_calibration_sample", "missing_calibration_report"))
    with pytest.raises(ValueError, match="cleared_gap_names"):
        replace(report, cleared_gap_names=("thin_calibration_sample", "thin_calibration_sample"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=report.rows[1:] + report.rows[:1])
    with pytest.raises(ValueError, match="snapshot_report_count"):
        replace(report, snapshot_report_count=True)


def test_phase_2_gap_stability_rows_and_all_are_exact():
    from polymarket_alpha_lab import phase_2_gap_stability

    assert phase_2_gap_stability.__all__ == (
        "PaperPhase2GapStabilityConfig",
        "PaperPhase2GapStabilityReport",
        "PaperPhase2GapStabilityRow",
        "build_paper_phase_2_gap_stability_report",
    )
    assert tuple(row.evidence_gap_name for row in _gap_stability_report().rows) == (
        EVIDENCE_GAP_NAMES
    )

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2GapStabilityConfig(config_version=" ")
    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2GapStabilityRow("unknown", None, None, 0, None, 0, False)
    with pytest.raises(ValueError, match="occurrence_count"):
        PaperPhase2GapStabilityRow(
            "thin_calibration_sample",
            first_seen_index=0,
            latest_seen_index=0,
            occurrence_count=-1,
            occurrence_ratio=Decimal("0.000000"),
            consecutive_present_count=0,
            ever_cleared=False,
        )


def test_phase_2_gap_stability_is_not_exported_from_package_root():
    import polymarket_alpha_lab as lab

    forbidden_exports = {
        "PaperPhase2GapStabilityConfig",
        "PaperPhase2GapStabilityReport",
        "PaperPhase2GapStabilityRow",
        "build_paper_phase_2_gap_stability_report",
    }

    assert forbidden_exports.isdisjoint(set(lab.__all__))
    for export_name in forbidden_exports:
        assert not hasattr(lab, export_name)
