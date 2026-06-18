from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.phase_2_evidence_snapshot import (
    EVIDENCE_GAP_NAMES,
    PaperPhase2EvidenceGapRow,
    PaperPhase2EvidenceSnapshotReport,
)


GENERATED_AT = datetime(2026, 6, 18, 20, 0, tzinfo=UTC)
CONFIG_VERSION = "phase-2-snapshot-age-v0"


def _module():
    from polymarket_alpha_lab import phase_2_snapshot_age

    return phase_2_snapshot_age


def _config(**overrides):
    module = _module()
    values = {
        "config_version": CONFIG_VERSION,
        "max_fresh_age_seconds": 600,
    }
    values.update(overrides)
    return module.PaperPhase2SnapshotAgeConfig(**values)


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
) -> PaperPhase2EvidenceSnapshotReport:
    return PaperPhase2EvidenceSnapshotReport(
        generated_at=generated_at,
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


def _age_report(
    *snapshots: PaperPhase2EvidenceSnapshotReport,
    generated_at: datetime = GENERATED_AT,
):
    module = _module()
    return module.build_paper_phase_2_snapshot_age_report(
        snapshots,
        config=_config(),
        generated_at=generated_at,
    )


def test_phase_2_snapshot_age_reports_empty_snapshot_sequence():
    module = _module()

    report = _age_report()

    assert isinstance(report, module.PaperPhase2SnapshotAgeReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.snapshot_report_count == 0
    assert report.first_snapshot_generated_at is None
    assert report.latest_snapshot_generated_at is None
    assert report.history_span_seconds == 0
    assert report.latest_age_seconds is None
    assert report.stale_snapshot_count == 0
    assert report.fresh_snapshot_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_snapshot_age_counts_fresh_and_stale_after_utc_normalization():
    first = _snapshot(
        generated_at=datetime(
            2026,
            6,
            18,
            15,
            35,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )
    threshold_fresh = _snapshot(
        generated_at=datetime(2026, 6, 18, 19, 50, tzinfo=UTC),
    )
    latest = _snapshot(
        generated_at=datetime(
            2026,
            6,
            18,
            21,
            55,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )

    report = _age_report(first, threshold_fresh, latest)

    assert report.snapshot_report_count == 3
    assert report.first_snapshot_generated_at == datetime(
        2026,
        6,
        18,
        19,
        35,
        tzinfo=UTC,
    )
    assert report.latest_snapshot_generated_at == datetime(
        2026,
        6,
        18,
        19,
        55,
        tzinfo=UTC,
    )
    assert report.history_span_seconds == 1200
    assert report.latest_age_seconds == 300
    assert report.stale_snapshot_count == 1
    assert report.fresh_snapshot_count == 2


def test_phase_2_snapshot_age_uses_append_order_for_latest_snapshot_age():
    first_append = _snapshot(
        generated_at=datetime(2026, 6, 18, 19, 40, tzinfo=UTC),
    )
    later_timestamp = _snapshot(
        generated_at=datetime(2026, 6, 18, 19, 58, tzinfo=UTC),
    )
    latest_append = _snapshot(
        generated_at=datetime(2026, 6, 18, 19, 45, tzinfo=UTC),
    )

    report = _age_report(first_append, later_timestamp, latest_append)

    assert report.first_snapshot_generated_at == first_append.generated_at
    assert report.latest_snapshot_generated_at == latest_append.generated_at
    assert report.history_span_seconds == 300
    assert report.latest_age_seconds == 900
    assert report.stale_snapshot_count == 2
    assert report.fresh_snapshot_count == 1


def test_phase_2_snapshot_age_requires_list_or_tuple_input():
    module = _module()
    snapshots = (_snapshot(),)

    with pytest.raises(ValueError, match="snapshots must be a list or tuple"):
        module.build_paper_phase_2_snapshot_age_report(
            iter(snapshots),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_phase_2_snapshot_age_requires_exact_config_type():
    module = _module()
    snapshot = _snapshot()

    class ConfigSubclass(module.PaperPhase2SnapshotAgeConfig):
        pass

    with pytest.raises(
        ValueError,
        match="config must be a PaperPhase2SnapshotAgeConfig",
    ):
        module.build_paper_phase_2_snapshot_age_report(
            [snapshot],
            config={"config_version": CONFIG_VERSION},
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="config must be a PaperPhase2SnapshotAgeConfig",
    ):
        module.build_paper_phase_2_snapshot_age_report(
            [snapshot],
            config=ConfigSubclass(
                config_version=CONFIG_VERSION,
                max_fresh_age_seconds=600,
            ),
            generated_at=GENERATED_AT,
        )


def test_phase_2_snapshot_age_requires_exact_snapshot_type_and_source_flags():
    module = _module()
    snapshot = _snapshot()

    class SnapshotSubclass(PaperPhase2EvidenceSnapshotReport):
        pass

    with pytest.raises(
        ValueError,
        match="snapshots must contain PaperPhase2EvidenceSnapshotReport values",
    ):
        module.build_paper_phase_2_snapshot_age_report(
            [object()],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="snapshots must contain PaperPhase2EvidenceSnapshotReport values",
    ):
        module.build_paper_phase_2_snapshot_age_report(
            [
                SnapshotSubclass(
                    generated_at=snapshot.generated_at,
                    config_version=snapshot.config_version,
                    status=snapshot.status,
                    calibration_report_present=snapshot.calibration_report_present,
                    segment_summary_report_present=snapshot.segment_summary_report_present,
                    calibration_observation_count=snapshot.calibration_observation_count,
                    calibration_status=snapshot.calibration_status,
                    segment_observation_count=snapshot.segment_observation_count,
                    segment_count=snapshot.segment_count,
                    probability_segment_count=snapshot.probability_segment_count,
                    return_only_segment_count=snapshot.return_only_segment_count,
                    thin_probability_segment_count=(
                        snapshot.thin_probability_segment_count
                    ),
                    probability_segment_coverage_ratio=(
                        snapshot.probability_segment_coverage_ratio
                    ),
                    return_only_segment_ratio=snapshot.return_only_segment_ratio,
                    evidence_gap_count=snapshot.evidence_gap_count,
                    evidence_gap_names=snapshot.evidence_gap_names,
                    evidence_gaps=snapshot.evidence_gaps,
                ),
            ],
            config=_config(),
            generated_at=GENERATED_AT,
        )

    object.__setattr__(snapshot, "readonly", False)
    with pytest.raises(ValueError, match="snapshots must contain readonly reports"):
        module.build_paper_phase_2_snapshot_age_report(
            [snapshot],
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_phase_2_snapshot_age_config_is_frozen_and_validates_threshold():
    module = _module()

    config = _config()

    class StrSubclass(str):
        pass

    class IntSubclass(int):
        pass

    assert config.config_version == CONFIG_VERSION
    assert config.max_fresh_age_seconds == 600
    with pytest.raises(FrozenInstanceError):
        config.max_fresh_age_seconds = 300
    with pytest.raises(ValueError, match="config_version"):
        module.PaperPhase2SnapshotAgeConfig(
            config_version=StrSubclass(CONFIG_VERSION),
            max_fresh_age_seconds=600,
        )
    with pytest.raises(ValueError, match="max_fresh_age_seconds"):
        module.PaperPhase2SnapshotAgeConfig(
            config_version=CONFIG_VERSION,
            max_fresh_age_seconds=-1,
        )
    with pytest.raises(ValueError, match="max_fresh_age_seconds"):
        module.PaperPhase2SnapshotAgeConfig(
            config_version=CONFIG_VERSION,
            max_fresh_age_seconds=True,
        )
    with pytest.raises(ValueError, match="max_fresh_age_seconds"):
        module.PaperPhase2SnapshotAgeConfig(
            config_version=CONFIG_VERSION,
            max_fresh_age_seconds=IntSubclass(600),
        )


def test_phase_2_snapshot_age_report_is_frozen_and_validates_counts():
    module = _module()

    report = _age_report(
        _snapshot(generated_at=datetime(2026, 6, 18, 19, 40, tzinfo=UTC)),
    )

    class DateTimeSubclass(datetime):
        pass

    class StrSubclass(str):
        pass

    class IntSubclass(int):
        pass

    with pytest.raises(FrozenInstanceError):
        report.fresh_snapshot_count = 99
    with pytest.raises(ValueError, match="datetime"):
        module.PaperPhase2SnapshotAgeReport(
            generated_at=DateTimeSubclass(2026, 6, 18, 20, 0, tzinfo=UTC),
            config_version=CONFIG_VERSION,
            snapshot_report_count=0,
            first_snapshot_generated_at=None,
            latest_snapshot_generated_at=None,
            history_span_seconds=0,
            latest_age_seconds=None,
            stale_snapshot_count=0,
            fresh_snapshot_count=0,
        )
    with pytest.raises(ValueError, match="config_version"):
        module.PaperPhase2SnapshotAgeReport(
            generated_at=GENERATED_AT,
            config_version=StrSubclass(CONFIG_VERSION),
            snapshot_report_count=0,
            first_snapshot_generated_at=None,
            latest_snapshot_generated_at=None,
            history_span_seconds=0,
            latest_age_seconds=None,
            stale_snapshot_count=0,
            fresh_snapshot_count=0,
        )
    with pytest.raises(ValueError, match="snapshot_report_count"):
        module.PaperPhase2SnapshotAgeReport(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            snapshot_report_count=IntSubclass(0),
            first_snapshot_generated_at=None,
            latest_snapshot_generated_at=None,
            history_span_seconds=0,
            latest_age_seconds=None,
            stale_snapshot_count=0,
            fresh_snapshot_count=0,
        )
    with pytest.raises(ValueError, match="fresh and stale counts"):
        module.PaperPhase2SnapshotAgeReport(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            snapshot_report_count=1,
            first_snapshot_generated_at=report.first_snapshot_generated_at,
            latest_snapshot_generated_at=report.latest_snapshot_generated_at,
            history_span_seconds=0,
            latest_age_seconds=1200,
            stale_snapshot_count=1,
            fresh_snapshot_count=1,
        )


def test_phase_2_snapshot_age_report_rejects_negative_latest_age_seconds():
    module = _module()

    with pytest.raises(ValueError, match="latest_age_seconds"):
        module.PaperPhase2SnapshotAgeReport(
            generated_at=GENERATED_AT,
            config_version=CONFIG_VERSION,
            snapshot_report_count=1,
            first_snapshot_generated_at=GENERATED_AT + timedelta(seconds=1),
            latest_snapshot_generated_at=GENERATED_AT + timedelta(seconds=1),
            history_span_seconds=0,
            latest_age_seconds=-1,
            stale_snapshot_count=0,
            fresh_snapshot_count=1,
        )


def test_phase_2_snapshot_age_builder_rejects_datetime_subclass():
    module = _module()

    class DateTimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at"):
        module.build_paper_phase_2_snapshot_age_report(
            [],
            config=_config(),
            generated_at=DateTimeSubclass(2026, 6, 18, 20, 0, tzinfo=UTC),
        )
