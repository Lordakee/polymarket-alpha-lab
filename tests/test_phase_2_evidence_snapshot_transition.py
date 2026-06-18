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


class IntSubclass(int):
    pass


class StrSubclass(str):
    pass


class DecimalSubclass(Decimal):
    pass


class DateTimeSubclass(datetime):
    pass


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


def test_phase_2_evidence_snapshot_transition_status_rows_are_deterministic_and_quantized():
    report = _transition_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _gap_snapshot(
            datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            "thin_calibration_sample",
        ),
        _snapshot(generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC)),
        _quality_snapshot(datetime(2026, 6, 18, 13, 0, tzinfo=UTC)),
    )

    assert tuple(
        (row.from_snapshot_status, row.to_snapshot_status)
        for row in report.status_transition_rows
    ) == tuple(
        (from_status, to_status)
        for from_status in SNAPSHOT_STATUSES
        for to_status in SNAPSHOT_STATUSES
    )
    assert sum(row.transition_count for row in report.status_transition_rows) == 3
    assert _status_row(
        report,
        "phase_2_evidence_observed",
        "phase_2_evidence_gaps",
    ).transition_ratio == Decimal("0.333333")
    assert _status_row(
        report,
        "phase_2_evidence_gaps",
        "phase_2_evidence_observed",
    ).transition_ratio == Decimal("0.333333")
    assert _status_row(
        report,
        "phase_2_evidence_observed",
        "phase_2_evidence_quality_flags",
    ).transition_ratio == Decimal("0.333333")
    assert all(
        row.transition_ratio is None
        or (
            type(row.transition_ratio) is Decimal
            and row.transition_ratio.as_tuple().exponent == Decimal(
                "0.000001",
            ).as_tuple().exponent
        )
        for row in report.status_transition_rows
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


def test_phase_2_evidence_snapshot_transition_gap_rows_are_deterministic_and_complete():
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
    third = _gap_snapshot(
        datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        "thin_calibration_sample",
        "thin_segment_probability_samples",
        "return_only_segments_present",
    )

    report = _transition_report(first, second, third)

    assert tuple(row.evidence_gap_name for row in report.gap_transition_rows) == (
        EVIDENCE_GAP_NAMES
    )
    assert _gap_row(report, "thin_calibration_sample") == (
        PaperPhase2EvidenceSnapshotGapTransitionRow(
            "thin_calibration_sample",
            introduced_count=0,
            cleared_count=0,
            persistent_count=2,
        )
    )
    assert _gap_row(report, "return_only_segments_present") == (
        PaperPhase2EvidenceSnapshotGapTransitionRow(
            "return_only_segments_present",
            introduced_count=1,
            cleared_count=1,
            persistent_count=0,
        )
    )
    assert _gap_row(report, "thin_segment_probability_samples") == (
        PaperPhase2EvidenceSnapshotGapTransitionRow(
            "thin_segment_probability_samples",
            introduced_count=1,
            cleared_count=0,
            persistent_count=1,
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


def test_phase_2_evidence_snapshot_transition_normalizes_report_datetimes_to_utc():
    source_snapshot = _snapshot(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone(timedelta(hours=2))),
    )

    report = _transition_report(
        source_snapshot,
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.first_report_generated_at == datetime(2026, 6, 18, 8, 0, tzinfo=UTC)
    assert report.latest_report_generated_at == datetime(2026, 6, 18, 8, 0, tzinfo=UTC)


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


def test_phase_2_evidence_snapshot_transition_rejects_status_row_mismatches():
    report = _transition_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(ValueError, match="status_transition_rows"):
        replace(
            report,
            status_transition_rows=report.status_transition_rows[1:]
            + report.status_transition_rows[:1],
        )

    list_normalized_report = replace(
        report,
        status_transition_rows=list(report.status_transition_rows),
    )
    assert type(list_normalized_report.status_transition_rows) is tuple
    assert list_normalized_report.status_transition_rows == report.status_transition_rows

    observed_row = _status_row(
        report,
        "phase_2_evidence_observed",
        "phase_2_evidence_observed",
    )
    replacement_rows = tuple(
        replace(row, transition_count=0) if row == observed_row else row
        for row in report.status_transition_rows
    )
    with pytest.raises(ValueError, match="counts must sum"):
        replace(report, status_transition_rows=replacement_rows)

    replacement_rows = tuple(
        replace(row, transition_ratio=Decimal("0.000000"))
        if row == observed_row
        else row
        for row in report.status_transition_rows
    )
    with pytest.raises(ValueError, match="ratios must match"):
        replace(report, status_transition_rows=replacement_rows)

    replacement_rows = tuple(
        replace(row, transition_ratio=Decimal("0.999999"))
        if row == observed_row
        else row
        for row in report.status_transition_rows
    )
    with pytest.raises(ValueError, match="ratios must match"):
        replace(report, status_transition_rows=replacement_rows)


def test_phase_2_evidence_snapshot_transition_rejects_gap_row_mismatches():
    report = _transition_report(
        _gap_snapshot(datetime(2026, 6, 18, 10, 0, tzinfo=UTC), "thin_calibration_sample"),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(ValueError, match="gap_transition_rows"):
        replace(
            report,
            gap_transition_rows=report.gap_transition_rows[1:]
            + report.gap_transition_rows[:1],
        )

    with pytest.raises(ValueError, match="gap_transition_rows"):
        replace(report, gap_transition_rows=report.gap_transition_rows[:-1])

    list_normalized_report = replace(
        report,
        gap_transition_rows=list(report.gap_transition_rows),
    )
    assert type(list_normalized_report.gap_transition_rows) is tuple
    assert list_normalized_report.gap_transition_rows == report.gap_transition_rows

    excessive_row = replace(
        _gap_row(report, "thin_calibration_sample"),
        introduced_count=1,
    )
    replacement_rows = tuple(
        excessive_row
        if row.evidence_gap_name == excessive_row.evidence_gap_name
        else row
        for row in report.gap_transition_rows
    )
    with pytest.raises(ValueError, match="counts cannot exceed transition_count"):
        replace(report, gap_transition_rows=replacement_rows)

    replacement_rows = tuple(
        replace(_gap_row(report, "thin_calibration_sample"), cleared_count=0)
        if row.evidence_gap_name == "thin_calibration_sample"
        else row
        for row in report.gap_transition_rows
    )
    with pytest.raises(ValueError, match="latest_cleared_gap_names"):
        replace(report, gap_transition_rows=replacement_rows)


def test_phase_2_evidence_snapshot_transition_rejects_scalar_subclasses():
    report = _transition_report()

    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2EvidenceSnapshotTransitionConfig(
            config_version=StrSubclass("phase-2-evidence-snapshot-transition-v0"),
        )
    with pytest.raises(ValueError, match="transition_count"):
        PaperPhase2EvidenceSnapshotStatusTransitionRow(
            "phase_2_evidence_observed",
            "phase_2_evidence_observed",
            IntSubclass(0),
            None,
        )
    with pytest.raises(ValueError, match="transition_ratio"):
        PaperPhase2EvidenceSnapshotStatusTransitionRow(
            "phase_2_evidence_observed",
            "phase_2_evidence_observed",
            0,
            DecimalSubclass("0.000000"),
        )
    with pytest.raises(ValueError, match="introduced_count"):
        PaperPhase2EvidenceSnapshotGapTransitionRow(
            "thin_calibration_sample",
            IntSubclass(0),
            0,
            0,
        )
    with pytest.raises(ValueError, match="snapshot_report_count"):
        replace(report, snapshot_report_count=IntSubclass(0))
    with pytest.raises(ValueError, match="datetime value"):
        replace(report, generated_at=DateTimeSubclass(2026, 6, 18, 19, 0))


@pytest.mark.parametrize(
    "field_name",
    (
        "from_snapshot_status",
        "to_snapshot_status",
    ),
)
def test_phase_2_evidence_snapshot_transition_status_rows_reject_str_subclasses(
    field_name,
):
    values = {
        "from_snapshot_status": "phase_2_evidence_observed",
        "to_snapshot_status": "phase_2_evidence_observed",
        "transition_count": 0,
        "transition_ratio": None,
    }
    values[field_name] = StrSubclass(values[field_name])

    with pytest.raises(ValueError, match=field_name):
        PaperPhase2EvidenceSnapshotStatusTransitionRow(**values)


def test_phase_2_evidence_snapshot_transition_gap_rows_reject_str_subclasses():
    with pytest.raises(ValueError, match="evidence_gap_name"):
        PaperPhase2EvidenceSnapshotGapTransitionRow(
            StrSubclass("thin_calibration_sample"),
            0,
            0,
            0,
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "latest_from_status",
        "latest_to_status",
    ),
)
def test_phase_2_evidence_snapshot_transition_report_statuses_reject_str_subclasses(
    field_name,
):
    report = _transition_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
        _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
    )

    with pytest.raises(ValueError, match=field_name):
        replace(report, **{field_name: StrSubclass(getattr(report, field_name))})


@pytest.mark.parametrize(
    ("field_name", "report"),
    (
        (
            "latest_introduced_gap_names",
            _transition_report(
                _snapshot(generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC)),
                _gap_snapshot(
                    datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
                    "thin_calibration_sample",
                ),
            ),
        ),
        (
            "latest_cleared_gap_names",
            _transition_report(
                _gap_snapshot(
                    datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
                    "thin_calibration_sample",
                ),
                _snapshot(generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC)),
            ),
        ),
    ),
)
def test_phase_2_evidence_snapshot_transition_latest_gap_names_reject_str_subclasses(
    field_name,
    report,
):
    with pytest.raises(ValueError, match=field_name):
        replace(
            report,
            **{
                field_name: tuple(
                    StrSubclass(gap_name) for gap_name in getattr(report, field_name)
                ),
            },
        )


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
