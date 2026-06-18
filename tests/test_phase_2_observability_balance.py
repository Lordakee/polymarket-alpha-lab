from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.phase_2_observability_balance import (
    PaperPhase2ObservabilityBalanceConfig,
    PaperPhase2ObservabilityBalanceReasonRow,
    PaperPhase2ObservabilityBalanceReport,
    build_paper_phase_2_observability_balance_report,
)
from polymarket_alpha_lab.phase_2_observability_state import (
    BLOCKING_REASON_NAMES,
    PaperPhase2ObservabilityStateReport,
)


GENERATED_AT = datetime(2026, 6, 18, 20, 0, tzinfo=UTC)


def _config(**overrides) -> PaperPhase2ObservabilityBalanceConfig:
    values = {"config_version": "phase-2-observability-balance-v0"}
    values.update(overrides)
    return PaperPhase2ObservabilityBalanceConfig(**values)


def _state(
    *,
    generated_at: datetime,
    phase_2_ready: bool,
    blocking_reason_names: tuple[str, ...],
) -> PaperPhase2ObservabilityStateReport:
    return PaperPhase2ObservabilityStateReport(
        generated_at=generated_at,
        config_version="phase-2-observability-state-v0",
        source_config_version="phase-2-observability-trends-v0",
        calibration_report_count=0
        if "missing_calibration_trend" in blocking_reason_names
        else 1,
        segment_summary_report_count=0
        if "missing_segment_summary_trend" in blocking_reason_names
        else 1,
        evidence_snapshot_report_count=0
        if "missing_evidence_snapshot_trend" in blocking_reason_names
        else 1,
        edge_cost_report_count=0
        if "missing_edge_cost_summary_trend" in blocking_reason_names
        else 1,
        latest_calibration_status=(
            None
            if "missing_calibration_trend" in blocking_reason_names
            else (
                "empty_calibration_history"
                if "calibration_not_observed" in blocking_reason_names
                else "calibration_evidence_observed"
            )
        ),
        latest_segment_status=(
            None
            if "missing_segment_summary_trend" in blocking_reason_names
            else (
                "insufficient_segment_probability_sample"
                if "segment_not_observed" in blocking_reason_names
                else "segment_evidence_observed"
            )
        ),
        latest_evidence_status=(
            None
            if "missing_evidence_snapshot_trend" in blocking_reason_names
            else (
                "phase_2_evidence_gaps"
                if "evidence_not_observed" in blocking_reason_names
                else "phase_2_evidence_observed"
            )
        ),
        latest_edge_cost_status=(
            None
            if "missing_edge_cost_summary_trend" in blocking_reason_names
            else (
                "insufficient_edge_cost_sample"
                if "edge_cost_not_observed" in blocking_reason_names
                else "edge_cost_evidence_observed"
            )
        ),
        evidence_gap_count=1 if "evidence_gaps_present" in blocking_reason_names else 0,
        latest_evidence_gap_names=(
            ("thin_segment_probability_samples",)
            if "evidence_gaps_present" in blocking_reason_names
            else ()
        ),
        phase_2_ready=phase_2_ready,
        blocking_reason_names=blocking_reason_names,
    )


def _report(
    *states: PaperPhase2ObservabilityStateReport,
    generated_at: datetime = GENERATED_AT,
) -> PaperPhase2ObservabilityBalanceReport:
    return build_paper_phase_2_observability_balance_report(
        states,
        config=_config(),
        generated_at=generated_at,
    )


def _row(
    report: PaperPhase2ObservabilityBalanceReport,
    reason_name: str,
) -> PaperPhase2ObservabilityBalanceReasonRow:
    return next(row for row in report.reason_rows if row.blocking_reason_name == reason_name)


def test_phase_2_observability_balance_reports_empty_sequence():
    report = _report()

    assert isinstance(report, PaperPhase2ObservabilityBalanceReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "phase-2-observability-balance-v0"
    assert report.state_report_count == 0
    assert report.ready_report_count == 0
    assert report.not_ready_report_count == 0
    assert report.ready_ratio is None
    assert report.latest_phase_2_ready is None
    assert report.latest_blocking_reason_names == ()
    assert report.reason_rows == tuple(
        PaperPhase2ObservabilityBalanceReasonRow(
            blocking_reason_name=reason_name,
            occurrence_count=0,
            occurrence_ratio=None,
            latest_present=False,
        )
        for reason_name in BLOCKING_REASON_NAMES
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_phase_2_observability_balance_summarizes_ready_ratio_and_reasons():
    first = _state(
        generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        phase_2_ready=False,
        blocking_reason_names=(
            "missing_calibration_trend",
            "missing_segment_summary_trend",
            "missing_evidence_snapshot_trend",
            "missing_edge_cost_summary_trend",
        ),
    )
    second = _state(
        generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
        phase_2_ready=False,
        blocking_reason_names=("evidence_not_observed", "evidence_gaps_present"),
    )
    third = _state(
        generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        phase_2_ready=True,
        blocking_reason_names=(),
    )

    report = _report(first, second, third)

    assert report.state_report_count == 3
    assert report.ready_report_count == 1
    assert report.not_ready_report_count == 2
    assert report.ready_ratio == Decimal("0.333333")
    assert report.latest_phase_2_ready is True
    assert report.latest_blocking_reason_names == ()
    assert _row(report, "missing_calibration_trend") == (
        PaperPhase2ObservabilityBalanceReasonRow(
            "missing_calibration_trend",
            occurrence_count=1,
            occurrence_ratio=Decimal("0.333333"),
            latest_present=False,
        )
    )
    assert _row(report, "evidence_gaps_present") == (
        PaperPhase2ObservabilityBalanceReasonRow(
            "evidence_gaps_present",
            occurrence_count=1,
            occurrence_ratio=Decimal("0.333333"),
            latest_present=False,
        )
    )


def test_phase_2_observability_balance_tracks_latest_blocking_reasons():
    report = _report(
        _state(
            generated_at=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
            phase_2_ready=True,
            blocking_reason_names=(),
        ),
        _state(
            generated_at=datetime(2026, 6, 18, 11, 0, tzinfo=UTC),
            phase_2_ready=False,
            blocking_reason_names=("edge_cost_not_observed",),
        ),
    )

    assert report.latest_phase_2_ready is False
    assert report.latest_blocking_reason_names == ("edge_cost_not_observed",)
    assert _row(report, "edge_cost_not_observed").latest_present is True
    assert _row(report, "edge_cost_not_observed").occurrence_ratio == Decimal(
        "0.500000",
    )


def test_phase_2_observability_balance_normalizes_generated_at_to_utc():
    report = _report(
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC


def test_phase_2_observability_balance_rejects_invalid_inputs_and_flags():
    valid_state = _state(
        generated_at=GENERATED_AT,
        phase_2_ready=True,
        blocking_reason_names=(),
    )

    class ConfigSubclass(PaperPhase2ObservabilityBalanceConfig):
        pass

    class DateTimeSubclass(datetime):
        pass

    for invalid_states in (
        object(),
        "states",
        b"states",
        {"state": valid_state},
        (state for state in (valid_state,)),
    ):
        with pytest.raises(ValueError, match="state_reports"):
            build_paper_phase_2_observability_balance_report(
                invalid_states,
                config=_config(),
                generated_at=GENERATED_AT,
            )
    with pytest.raises(ValueError, match="PaperPhase2ObservabilityStateReport"):
        build_paper_phase_2_observability_balance_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_observability_balance_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_paper_phase_2_observability_balance_report(
            (),
            config=ConfigSubclass(config_version="phase-2-observability-balance-v0"),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_observability_balance_report(
            (),
            config=_config(),
            generated_at="now",
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_phase_2_observability_balance_report(
            (),
            config=_config(),
            generated_at=DateTimeSubclass(2026, 6, 18, 20, 0, tzinfo=UTC),
        )

    object.__setattr__(valid_state, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _report(valid_state)


def test_phase_2_observability_balance_dataclasses_revalidate_consistency():
    report = _report(
        _state(
            generated_at=GENERATED_AT,
            phase_2_ready=False,
            blocking_reason_names=("edge_cost_not_observed",),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.ready_report_count = 99
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ready_report_count"):
        replace(report, ready_report_count=1)
    with pytest.raises(ValueError, match="reason_rows"):
        replace(report, reason_rows=tuple(reversed(report.reason_rows)))
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(report, ready_ratio=Decimal("1.000000"))
    with pytest.raises(ValueError, match="latest_blocking_reason_names"):
        replace(report, latest_blocking_reason_names=())
    with pytest.raises(ValueError, match="latest_present"):
        replace(
            report,
            reason_rows=(
                *report.reason_rows[:-1],
                replace(report.reason_rows[-1], latest_present=False),
            ),
        )


def test_phase_2_observability_balance_rejects_reason_name_string_subclasses():
    class StrSubclass(str):
        pass

    with pytest.raises(ValueError, match="blocking_reason_name"):
        PaperPhase2ObservabilityBalanceReasonRow(
            StrSubclass("edge_cost_not_observed"),
            1,
            Decimal("1.000000"),
            True,
        )


def test_phase_2_observability_balance_rows_and_all_are_exact():
    from polymarket_alpha_lab import phase_2_observability_balance

    class StrSubclass(str):
        pass

    class IntSubclass(int):
        pass

    class DecimalSubclass(Decimal):
        pass

    assert phase_2_observability_balance.__all__ == (
        "PaperPhase2ObservabilityBalanceConfig",
        "PaperPhase2ObservabilityBalanceReasonRow",
        "PaperPhase2ObservabilityBalanceReport",
        "build_paper_phase_2_observability_balance_report",
    )
    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2ObservabilityBalanceConfig(config_version=" ")
    with pytest.raises(ValueError, match="config_version"):
        PaperPhase2ObservabilityBalanceConfig(
            config_version=StrSubclass("phase-2-observability-balance-v0"),
        )
    with pytest.raises(ValueError, match="blocking_reason_name"):
        PaperPhase2ObservabilityBalanceReasonRow("unknown", 0, None, False)
    with pytest.raises(ValueError, match="occurrence_count"):
        PaperPhase2ObservabilityBalanceReasonRow(
            "edge_cost_not_observed",
            IntSubclass(1),
            None,
            True,
        )
    with pytest.raises(ValueError, match="occurrence_ratio"):
        PaperPhase2ObservabilityBalanceReasonRow(
            "edge_cost_not_observed",
            1,
            Decimal("0.5"),
            True,
        )
    with pytest.raises(ValueError, match="occurrence_ratio"):
        PaperPhase2ObservabilityBalanceReasonRow(
            "edge_cost_not_observed",
            1,
            DecimalSubclass("0.500000"),
            True,
        )
