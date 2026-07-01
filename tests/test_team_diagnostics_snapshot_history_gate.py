from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryReport,
)


MODULE_NAME = "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate"
GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
LATEST_GENERATED_AT = GENERATED_AT - timedelta(seconds=300)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def gate_module():
    return importlib.import_module(MODULE_NAME)


def source_report(**overrides: object) -> TeamDiagnosticsSnapshotHistoryReport:
    values: dict[str, object] = {
        "generated_at": GENERATED_AT,
        "config_version": "team-diagnostics-snapshot-history-v0",
        "snapshot_count": 3,
        "required_snapshot_count": 2,
        "status": "observed",
        "reason_codes": (),
        "latest_snapshot": object(),
        "earliest_generated_at": LATEST_GENERATED_AT - timedelta(days=2),
        "latest_generated_at": LATEST_GENERATED_AT,
        "span_seconds": 172800,
        "status_counts": (("observed", 3),),
        "evidence_quality_average_delta": d("0.010000"),
        "evidence_quality_delta": d("0.010000"),
        "memory_eligible_delta": 1,
        "settled_calibration_delta": 1,
        "duplicate_latest_generated_at": False,
    }
    values.update(overrides)
    if (
        "evidence_quality_average_delta" in overrides
        and "evidence_quality_delta" not in overrides
    ):
        values["evidence_quality_delta"] = values["evidence_quality_average_delta"]
    return TeamDiagnosticsSnapshotHistoryReport(**values)


def build_gate_report(source: TeamDiagnosticsSnapshotHistoryReport, **config: object):
    module = gate_module()
    return module.build_team_diagnostics_snapshot_history_gate_report(
        source,
        config=module.TeamDiagnosticsSnapshotHistoryGateConfig(**config),
        generated_at=GENERATED_AT,
    )


def test_expected_exports_and_pure_reducer_import_surface() -> None:
    module = gate_module()

    assert module.__all__ == (
        "DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_HISTORY_GATE_CONFIG_VERSION",
        "TeamDiagnosticsSnapshotHistoryGateConfig",
        "TeamDiagnosticsSnapshotHistoryGateReasonCodeCount",
        "TeamDiagnosticsSnapshotHistoryGateReport",
        "build_team_diagnostics_snapshot_history_gate_report",
    )
    assert (
        module.DEFAULT_TEAM_DIAGNOSTICS_SNAPSHOT_HISTORY_GATE_CONFIG_VERSION
        == "team-diagnostics-snapshot-history-gate-v0"
    )

    source_path = Path(inspect.getsourcefile(module) or "")
    tree = ast.parse(source_path.read_text())
    imported_modules: list[str] = []
    float_literals: list[ast.Constant] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_literals.append(node)

    assert float_literals == []
    assert not any("psycopg" in name for name in imported_modules)
    assert not any(name.endswith(".cli") for name in imported_modules)
    assert not any("_db" in name for name in imported_modules)
    assert not any("_env" in name or name.endswith(".env") for name in imported_modules)
    assert not any("live" in name or "trading" in name for name in imported_modules)


def test_stable_source_passes() -> None:
    module = gate_module()
    report = build_gate_report(source_report())

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-diagnostics-snapshot-history-gate-v0"
    assert report.source_config_version == "team-diagnostics-snapshot-history-v0"
    assert report.source_generated_at == LATEST_GENERATED_AT
    assert report.latest_snapshot_age_seconds == 300
    assert report.gate_status == "pass"
    assert (
        report.recommended_next_step
        == "allow_team_diagnostics_snapshot_history_memory_use"
    )
    assert report.reason_code_counts == (
        module.TeamDiagnosticsSnapshotHistoryGateReasonCodeCount(
            reason_code="team_diagnostics_snapshot_history_gate_passed",
            count=1,
        ),
    )
    assert report.source_snapshot_count == 3
    assert report.source_required_snapshot_count == 3
    assert report.source_status == "observed"
    assert report.source_span_seconds == 172800
    assert report.source_status_counts == (("observed", 3),)
    assert report.source_reason_codes == ()
    assert report.evidence_quality_average_delta == d("0.010000")
    assert report.memory_eligible_delta == 1
    assert report.settled_calibration_delta == 1
    assert report.duplicate_latest_generated_at is False
    assert report.reason_codes == ("team_diagnostics_snapshot_history_gate_passed",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    "source",
    (
        source_report(snapshot_count=2, status_counts=(("observed", 2),)),
        source_report(
            status="insufficient_history",
            reason_codes=("insufficient_history",),
        ),
    ),
)
def test_insufficient_history_blocks(source: TeamDiagnosticsSnapshotHistoryReport) -> None:
    report = build_gate_report(source)

    assert report.gate_status == "blocked"
    assert (
        report.recommended_next_step
        == "block_team_diagnostics_snapshot_history_memory_use"
    )
    assert report.reason_codes == (
        "insufficient_team_diagnostics_snapshot_history_samples",
    )


def test_hard_block_suppresses_watch_conditions() -> None:
    report = build_gate_report(
        source_report(
            snapshot_count=2,
            status_counts=(("observed", 2),),
            reason_codes=("source_history_warning",),
            evidence_quality_average_delta=d("-0.050001"),
            memory_eligible_delta=-1,
            settled_calibration_delta=-1,
        ),
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == (
        "insufficient_team_diagnostics_snapshot_history_samples",
    )
    assert tuple(row.reason_code for row in report.reason_code_counts) == (
        "insufficient_team_diagnostics_snapshot_history_samples",
    )


def test_source_required_snapshot_count_uses_stricter_effective_requirement() -> None:
    report = build_gate_report(
        source_report(
            snapshot_count=4,
            required_snapshot_count=5,
            status_counts=(("observed", 4),),
        ),
    )

    assert report.gate_status == "blocked"
    assert report.source_snapshot_count == 4
    assert report.source_required_snapshot_count == 5
    assert report.reason_codes == (
        "insufficient_team_diagnostics_snapshot_history_samples",
    )


@pytest.mark.parametrize(
    ("latest_generated_at", "expected_age"),
    (
        (GENERATED_AT - timedelta(seconds=86401), 86401),
        (None, None),
    ),
)
def test_stale_or_missing_latest_snapshot_blocks(
    latest_generated_at: datetime | None,
    expected_age: int | None,
) -> None:
    report = build_gate_report(
        source_report(latest_generated_at=latest_generated_at),
    )

    assert report.gate_status == "blocked"
    assert report.latest_snapshot_age_seconds == expected_age
    assert report.source_generated_at == latest_generated_at
    assert report.reason_codes == ("stale_team_diagnostics_snapshot_history",)


def test_duplicate_latest_generated_at_blocks() -> None:
    report = build_gate_report(
        source_report(
            duplicate_latest_generated_at=True,
            reason_codes=("duplicate_latest_generated_at",),
        ),
    )

    assert report.gate_status == "blocked"
    assert report.duplicate_latest_generated_at is True
    assert report.reason_codes == (
        "duplicate_latest_team_diagnostics_snapshot_history_generated_at",
    )


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    (
        (
            {"evidence_quality_average_delta": d("-0.050001")},
            "team_diagnostics_snapshot_history_evidence_quality_deteriorated",
        ),
        (
            {"memory_eligible_delta": -1},
            "team_diagnostics_snapshot_history_memory_coverage_deteriorated",
        ),
        (
            {"settled_calibration_delta": -1},
            "team_diagnostics_snapshot_history_settled_calibration_deteriorated",
        ),
    ),
)
def test_negative_quality_memory_and_calibration_deltas_watch(
    overrides: dict[str, object],
    expected_reason: str,
) -> None:
    report = build_gate_report(source_report(**overrides))

    assert report.gate_status == "watch"
    assert (
        report.recommended_next_step
        == "throttle_team_diagnostics_snapshot_history_memory_use"
    )
    assert report.reason_codes == (expected_reason,)


def test_source_reason_codes_watch_when_not_blocked() -> None:
    report = build_gate_report(
        source_report(reason_codes=("source_history_warning",)),
    )

    assert report.gate_status == "watch"
    assert report.source_reason_codes == ("source_history_warning",)
    assert report.reason_codes == (
        "team_diagnostics_snapshot_history_source_reason_codes_present",
    )


def test_exact_config_and_source_type_validation() -> None:
    module = gate_module()

    class ConfigSubclass(module.TeamDiagnosticsSnapshotHistoryGateConfig):
        pass

    class SourceSubclass(TeamDiagnosticsSnapshotHistoryReport):
        pass

    with pytest.raises(ValueError, match="config"):
        module.build_team_diagnostics_snapshot_history_gate_report(
            source_report(),
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source_report"):
        module.build_team_diagnostics_snapshot_history_gate_report(
            SourceSubclass(
                generated_at=GENERATED_AT,
                config_version="team-diagnostics-snapshot-history-v0",
                snapshot_count=3,
                required_snapshot_count=2,
                status="observed",
                reason_codes=(),
                latest_snapshot=object(),
                earliest_generated_at=LATEST_GENERATED_AT - timedelta(days=2),
                latest_generated_at=LATEST_GENERATED_AT,
                span_seconds=172800,
                status_counts=(("observed", 3),),
                evidence_quality_average_delta=d("0.010000"),
                evidence_quality_delta=d("0.010000"),
                memory_eligible_delta=1,
                settled_calibration_delta=1,
                duplicate_latest_generated_at=False,
            ),
            config=module.TeamDiagnosticsSnapshotHistoryGateConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_team_diagnostics_snapshot_history_gate_report(
            source_report(),
            config=module.TeamDiagnosticsSnapshotHistoryGateConfig(),
            generated_at=_DatetimeSubclass(2026, 7, 1, 12, 0, tzinfo=UTC),
        )


def test_hard_flags_on_config_source_report_and_reason_counts() -> None:
    module = gate_module()
    valid = build_gate_report(source_report())

    with pytest.raises(ValueError, match="paper_only"):
        module.TeamDiagnosticsSnapshotHistoryGateConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        module.TeamDiagnosticsSnapshotHistoryGateReasonCodeCount(
            reason_code="team_diagnostics_snapshot_history_gate_passed",
            count=1,
            report_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(valid, readonly=False)

    unsafe_source = source_report()
    object.__setattr__(unsafe_source, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        build_gate_report(unsafe_source)


def test_gate_dataclasses_are_frozen() -> None:
    module = gate_module()
    config = module.TeamDiagnosticsSnapshotHistoryGateConfig()
    reason_count = module.TeamDiagnosticsSnapshotHistoryGateReasonCodeCount(
        reason_code="team_diagnostics_snapshot_history_gate_passed",
        count=1,
    )
    report = build_gate_report(source_report())

    with pytest.raises(FrozenInstanceError):
        config.min_source_snapshot_count = 4  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.gate_status = "blocked"  # type: ignore[misc]


def test_decimal_only_thresholds_and_quantized_decimal_fields() -> None:
    module = gate_module()

    with pytest.raises(ValueError, match="min_evidence_quality_average_delta"):
        module.TeamDiagnosticsSnapshotHistoryGateConfig(
            min_evidence_quality_average_delta=-0.05,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="min_evidence_quality_average_delta"):
        module.TeamDiagnosticsSnapshotHistoryGateConfig(
            min_evidence_quality_average_delta=_DecimalSubclass("-0.050000"),
        )
    with pytest.raises(ValueError, match="min_source_snapshot_count"):
        module.TeamDiagnosticsSnapshotHistoryGateConfig(
            min_source_snapshot_count=_IntSubclass(3),
        )

    config = module.TeamDiagnosticsSnapshotHistoryGateConfig(
        min_evidence_quality_average_delta=d("-0.0500004"),
    )
    report = module.build_team_diagnostics_snapshot_history_gate_report(
        source_report(evidence_quality_average_delta=d("-0.0600004")),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert config.min_evidence_quality_average_delta == d("-0.050000")
    assert report.evidence_quality_average_delta == d("-0.060000")


def test_direct_report_constructor_consistency_validation() -> None:
    module = gate_module()
    report = build_gate_report(source_report())

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=())
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(
            report,
            recommended_next_step="block_team_diagnostics_snapshot_history_memory_use",
        )
    with pytest.raises(ValueError, match="gate_status"):
        replace(report, gate_status="blocked")
    with pytest.raises(ValueError, match="latest_snapshot_age_seconds"):
        replace(report, latest_snapshot_age_seconds=301)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=())

    blocked = build_gate_report(
        source_report(latest_generated_at=GENERATED_AT - timedelta(seconds=86401)),
    )
    with pytest.raises(ValueError, match="gate_status"):
        replace(
            blocked,
            gate_status="watch",
            recommended_next_step="throttle_team_diagnostics_snapshot_history_memory_use",
        )
    with pytest.raises(ValueError, match="stale"):
        replace(
            report,
            source_generated_at=None,
            latest_snapshot_age_seconds=None,
        )
    with pytest.raises(ValueError, match="source reason"):
        replace(
            report,
            gate_status="watch",
            recommended_next_step=(
                "throttle_team_diagnostics_snapshot_history_memory_use"
            ),
            reason_codes=(
                "team_diagnostics_snapshot_history_evidence_quality_deteriorated",
            ),
            reason_code_counts=(
                module.TeamDiagnosticsSnapshotHistoryGateReasonCodeCount(
                    reason_code=(
                        "team_diagnostics_snapshot_history_evidence_quality_deteriorated"
                    ),
                    count=1,
                ),
            ),
            source_reason_codes=("source_history_warning",),
        )


def test_generated_at_and_source_datetimes_normalize_to_utc() -> None:
    module = gate_module()
    generated_at = datetime(2026, 7, 1, 5, 0, tzinfo=timezone(timedelta(hours=-7)))
    latest_at = datetime(2026, 7, 1, 4, 55, tzinfo=timezone(timedelta(hours=-7)))

    report = module.build_team_diagnostics_snapshot_history_gate_report(
        source_report(latest_generated_at=latest_at),
        config=module.TeamDiagnosticsSnapshotHistoryGateConfig(),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.source_generated_at == LATEST_GENERATED_AT
    assert report.source_generated_at.tzinfo is UTC
