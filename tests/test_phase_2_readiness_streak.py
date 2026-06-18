from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest

from polymarket_alpha_lab.phase_2_observability_state import (
    BLOCKING_REASON_NAMES,
    PaperPhase2ObservabilityStateReport,
)


GENERATED_AT = datetime(2026, 6, 18, 18, 0, tzinfo=UTC)


def _api() -> tuple[type[Any], type[Any], Any]:
    module = import_module("polymarket_alpha_lab.phase_2_readiness_streak")
    return (
        module.PaperPhase2ReadinessStreakConfig,
        module.PaperPhase2ReadinessStreakReport,
        module.build_paper_phase_2_readiness_streak_report,
    )


def _config(**overrides: Any) -> Any:
    Config, _Report, _builder = _api()
    values = {"config_version": "phase-2-readiness-streak-v0"}
    values.update(overrides)
    return Config(**values)


def _ready_state_report(**overrides: Any) -> PaperPhase2ObservabilityStateReport:
    values = {
        "generated_at": datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
        "config_version": "phase-2-observability-state-v0",
        "source_config_version": "phase-2-observability-trends-v0",
        "calibration_report_count": 1,
        "segment_summary_report_count": 1,
        "evidence_snapshot_report_count": 1,
        "edge_cost_report_count": 1,
        "latest_calibration_status": "calibration_evidence_observed",
        "latest_segment_status": "segment_evidence_observed",
        "latest_evidence_status": "phase_2_evidence_observed",
        "latest_edge_cost_status": "edge_cost_evidence_observed",
        "evidence_gap_count": 0,
        "latest_evidence_gap_names": (),
        "phase_2_ready": True,
        "blocking_reason_names": (),
    }
    values.update(overrides)
    return PaperPhase2ObservabilityStateReport(**values)


def _not_ready_state_report(**overrides: Any) -> PaperPhase2ObservabilityStateReport:
    values = {
        "generated_at": datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
        "config_version": "phase-2-observability-state-v0",
        "source_config_version": "phase-2-observability-trends-v0",
        "calibration_report_count": 0,
        "segment_summary_report_count": 0,
        "evidence_snapshot_report_count": 0,
        "edge_cost_report_count": 0,
        "latest_calibration_status": None,
        "latest_segment_status": None,
        "latest_evidence_status": None,
        "latest_edge_cost_status": None,
        "evidence_gap_count": 0,
        "latest_evidence_gap_names": (),
        "phase_2_ready": False,
        "blocking_reason_names": BLOCKING_REASON_NAMES[:4],
    }
    values.update(overrides)
    return PaperPhase2ObservabilityStateReport(**values)


def test_empty_sequence_returns_zero_counts_and_absent_latest_ready():
    _Config, Report, builder = _api()

    report = builder((), config=_config(), generated_at=GENERATED_AT)

    assert isinstance(report, Report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "phase-2-readiness-streak-v0"
    assert report.state_report_count == 0
    assert report.latest_phase_2_ready is None
    assert report.consecutive_ready_count == 0
    assert report.consecutive_not_ready_count == 0
    assert report.ready_report_count == 0
    assert report.not_ready_report_count == 0
    assert report.latest_blocking_reason_names == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_list_input_tracks_latest_ready_streak_and_utc_normalizes_generated_at():
    _Config, Report, builder = _api()

    report = builder(
        [
            _not_ready_state_report(),
            _ready_state_report(),
            _ready_state_report(),
        ],
        config=_config(),
        generated_at=datetime(2026, 6, 18, 13, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    assert isinstance(report, Report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.state_report_count == 3
    assert report.latest_phase_2_ready is True
    assert report.consecutive_ready_count == 2
    assert report.consecutive_not_ready_count == 0
    assert report.ready_report_count == 2
    assert report.not_ready_report_count == 1
    assert report.latest_blocking_reason_names == ()


def test_tuple_input_tracks_latest_not_ready_reason_names():
    _Config, Report, builder = _api()

    report = builder(
        (
            _ready_state_report(),
            _not_ready_state_report(),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, Report)
    assert report.state_report_count == 2
    assert report.latest_phase_2_ready is False
    assert report.consecutive_ready_count == 0
    assert report.consecutive_not_ready_count == 1
    assert report.ready_report_count == 1
    assert report.not_ready_report_count == 1
    assert report.latest_blocking_reason_names == BLOCKING_REASON_NAMES[:4]


@pytest.mark.parametrize(
    "state_reports",
    (
        object(),
        "not reports",
        b"not reports",
        {"report": _ready_state_report()},
        (report for report in ()),
    ),
)
def test_builder_rejects_non_sequence_inputs(state_reports: object):
    _Config, _Report, builder = _api()

    with pytest.raises(ValueError, match="state_reports must be a list or tuple"):
        builder(state_reports, config=_config(), generated_at=GENERATED_AT)


def test_builder_uses_exact_source_report_types_and_flags():
    Config, _Report, builder = _api()
    subclassed_config = type("SubclassedConfig", (Config,), {})
    subclassed_report = type(
        "SubclassedObservabilityStateReport",
        (PaperPhase2ObservabilityStateReport,),
        {},
    )
    subclassed_datetime = type("SubclassedDateTime", (datetime,), {})
    base_report = _ready_state_report()

    with pytest.raises(ValueError, match="state_reports"):
        builder(
            (subclassed_report(**base_report.__dict__),),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="config"):
        builder(
            (base_report,),
            config=subclassed_config(config_version="phase-2-readiness-streak-v0"),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        builder(
            (base_report,),
            config=_config(),
            generated_at=subclassed_datetime(2026, 6, 18, 18, 0, tzinfo=UTC),
        )

    mutated_report = _ready_state_report()
    object.__setattr__(mutated_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        builder((mutated_report,), config=_config(), generated_at=GENERATED_AT)


def test_report_is_frozen_and_revalidates_flags_and_deterministic_reason_order():
    _Config, Report, builder = _api()

    empty_report = builder((), config=_config(), generated_at=GENERATED_AT)
    ready_report = builder(
        (_ready_state_report(),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        empty_report.state_report_count = 1
    with pytest.raises(ValueError, match="paper_only"):
        replace(empty_report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(empty_report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(empty_report, readonly=False)
    with pytest.raises(ValueError, match="latest_phase_2_ready"):
        replace(empty_report, latest_phase_2_ready=True)
    with pytest.raises(ValueError, match="latest_phase_2_ready"):
        replace(ready_report, latest_phase_2_ready=None)
    with pytest.raises(ValueError, match="latest_blocking_reason_names"):
        replace(
            ready_report,
            latest_blocking_reason_names=tuple(reversed(BLOCKING_REASON_NAMES[:4])),
        )
    with pytest.raises(ValueError, match="latest_blocking_reason_names"):
        replace(ready_report, latest_blocking_reason_names=("unknown_reason",))


def test_report_requires_exact_string_reason_names():
    _Config, Report, _builder = _api()
    subclassed_string = type("SubclassedString", (str,), {})

    with pytest.raises(ValueError, match="latest_blocking_reason_names"):
        Report(
            generated_at=GENERATED_AT,
            config_version="phase-2-readiness-streak-v0",
            state_report_count=1,
            latest_phase_2_ready=False,
            consecutive_ready_count=0,
            consecutive_not_ready_count=1,
            ready_report_count=0,
            not_ready_report_count=1,
            latest_blocking_reason_names=(
                subclassed_string(BLOCKING_REASON_NAMES[0]),
            ),
        )


def test_local_all_and_package_root_non_export():
    module = import_module("polymarket_alpha_lab.phase_2_readiness_streak")
    subclassed_string = type("SubclassedString", (str,), {})
    subclassed_integer = type("SubclassedInteger", (int,), {})

    assert module.__all__ == (
        "PaperPhase2ReadinessStreakConfig",
        "PaperPhase2ReadinessStreakReport",
        "build_paper_phase_2_readiness_streak_report",
    )

    with pytest.raises(ValueError, match="config_version"):
        module.PaperPhase2ReadinessStreakConfig(
            config_version=" phase-2-readiness-streak-v0 ",
        )
    with pytest.raises(ValueError, match="config_version"):
        module.PaperPhase2ReadinessStreakConfig(
            config_version=subclassed_string("phase-2-readiness-streak-v0"),
        )
    with pytest.raises(ValueError, match="state_report_count"):
        module.PaperPhase2ReadinessStreakReport(
            generated_at=GENERATED_AT,
            config_version="phase-2-readiness-streak-v0",
            state_report_count=subclassed_integer(0),
            latest_phase_2_ready=None,
            consecutive_ready_count=0,
            consecutive_not_ready_count=0,
            ready_report_count=0,
            not_ready_report_count=0,
            latest_blocking_reason_names=(),
        )

    package_root = import_module("polymarket_alpha_lab")
    assert not hasattr(package_root, "PaperPhase2ReadinessStreakConfig")
    assert not hasattr(package_root, "PaperPhase2ReadinessStreakReport")
    assert not hasattr(
        package_root,
        "build_paper_phase_2_readiness_streak_report",
    )
