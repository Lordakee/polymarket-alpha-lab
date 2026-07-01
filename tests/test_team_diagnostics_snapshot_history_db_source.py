from __future__ import annotations

import ast
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab import (
    team_diagnostics_snapshot_history_db_source as module_under_test,
)
from polymarket_alpha_lab.team_diagnostics_snapshot import (
    TeamDiagnosticsSnapshotReport,
)
from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryConfig,
    build_team_diagnostics_snapshot_history_report,
)
from polymarket_alpha_lab.team_diagnostics_snapshot_history_db_source import (
    load_team_diagnostics_snapshot_history_report,
)


GENERATED_AT = datetime(2026, 6, 28, 15, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 28, 9, 0, tzinfo=UTC)


@dataclass(frozen=True)
class _HistoryResult:
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def _snapshot(
    *,
    generated_at: datetime,
    forecast_row_count: int = 4,
    evidence_row_count: int = 3,
    outcome_row_count: int = 2,
    memory_eligible_reference_count: int = 1,
    calibration_settled_count: int = 1,
    evidence_quality_status: str = "pass",
    evidence_quality_pass_count: int = 3,
    evidence_quality_watch_count: int = 0,
    evidence_quality_blocked_count: int = 0,
    evidence_quality_average_quality_score: Decimal = d("0.800000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamDiagnosticsSnapshotReport:
    return TeamDiagnosticsSnapshotReport(
        generated_at=generated_at,
        config_version="team-diagnostics-snapshot-v0",
        source_config_version="team-diagnostics-bundle-v0",
        filters=(("team_id", "team-alpha"),),
        forecast_row_count=forecast_row_count,
        evidence_row_count=evidence_row_count,
        outcome_row_count=outcome_row_count,
        memory_eligible_reference_count=memory_eligible_reference_count,
        calibration_status="settled",
        calibration_settled_count=calibration_settled_count,
        calibration_group_count=1,
        event_template_row_count=1,
        event_template_status="observed",
        source_reliability_row_count=1,
        source_reliability_missing_source_evidence_count=0,
        evidence_quality_status=evidence_quality_status,
        evidence_quality_pass_count=evidence_quality_pass_count,
        evidence_quality_watch_count=evidence_quality_watch_count,
        evidence_quality_blocked_count=evidence_quality_blocked_count,
        evidence_quality_average_quality_score=evidence_quality_average_quality_score,
        reason_codes=("diagnostics_ready",),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_passes_filter_kwargs_to_loader_and_returns_builder_report() -> None:
    config = TeamDiagnosticsSnapshotHistoryConfig()
    older = _snapshot(generated_at=BASE_AT)
    latest = _snapshot(generated_at=BASE_AT + timedelta(hours=2))
    loader_calls: list[dict[str, object]] = []
    builder_calls: list[
        tuple[tuple[TeamDiagnosticsSnapshotReport, ...], TeamDiagnosticsSnapshotHistoryConfig, datetime]
    ] = []
    expected_result = _HistoryResult()

    def load_snapshots(**kwargs: object) -> tuple[TeamDiagnosticsSnapshotReport, ...]:
        loader_calls.append(kwargs)
        return (latest, older)

    def history_builder(
        snapshots: object,
        *,
        config: TeamDiagnosticsSnapshotHistoryConfig,
        generated_at: datetime,
    ) -> _HistoryResult:
        builder_calls.append((tuple(snapshots), config, generated_at))  # type: ignore[arg-type]
        return expected_result

    result = load_team_diagnostics_snapshot_history_report(
        load_snapshots=load_snapshots,
        history_builder=history_builder,
        config=config,
        generated_at=GENERATED_AT,
        team_id="team-alpha",
        market_slug="market-alpha",
        forecast_id="forecast-alpha",
        config_version="snapshot-v1",
        limit=25,
    )

    assert loader_calls == [
        {
            "team_id": "team-alpha",
            "market_slug": "market-alpha",
            "forecast_id": "forecast-alpha",
            "config_version": "snapshot-v1",
            "limit": 25,
        },
    ]
    assert builder_calls == [((older, latest), config, GENERATED_AT)]
    assert result is expected_result


def test_reverses_newest_first_snapshots_into_chronological_builder_input() -> None:
    config = TeamDiagnosticsSnapshotHistoryConfig()
    older = _snapshot(generated_at=BASE_AT)
    middle = _snapshot(generated_at=BASE_AT + timedelta(hours=1))
    latest = _snapshot(generated_at=BASE_AT + timedelta(hours=2))
    builder_inputs: list[tuple[TeamDiagnosticsSnapshotReport, ...]] = []

    def load_snapshots(**_: object) -> tuple[TeamDiagnosticsSnapshotReport, ...]:
        return (latest, middle, older)

    def history_builder(
        snapshots: object,
        *,
        config: TeamDiagnosticsSnapshotHistoryConfig,
        generated_at: datetime,
    ) -> _HistoryResult:
        builder_inputs.append(tuple(snapshots))  # type: ignore[arg-type]
        return _HistoryResult()

    load_team_diagnostics_snapshot_history_report(
        load_snapshots=load_snapshots,
        history_builder=history_builder,
        config=config,
        generated_at=GENERATED_AT,
    )

    assert builder_inputs == [(older, middle, latest)]


def test_preserves_input_position_for_duplicate_timestamps() -> None:
    config = TeamDiagnosticsSnapshotHistoryConfig()
    older = _snapshot(generated_at=BASE_AT)
    duplicate_first = _snapshot(
        generated_at=BASE_AT + timedelta(hours=1),
        memory_eligible_reference_count=2,
    )
    duplicate_second = _snapshot(
        generated_at=BASE_AT + timedelta(hours=1),
        memory_eligible_reference_count=3,
    )
    builder_inputs: list[tuple[TeamDiagnosticsSnapshotReport, ...]] = []

    def load_snapshots(**_: object) -> tuple[TeamDiagnosticsSnapshotReport, ...]:
        return (duplicate_first, duplicate_second, older)

    def history_builder(
        snapshots: object,
        *,
        config: TeamDiagnosticsSnapshotHistoryConfig,
        generated_at: datetime,
    ) -> _HistoryResult:
        builder_inputs.append(tuple(snapshots))  # type: ignore[arg-type]
        return _HistoryResult()

    load_team_diagnostics_snapshot_history_report(
        load_snapshots=load_snapshots,
        history_builder=history_builder,
        config=config,
        generated_at=GENERATED_AT,
    )

    assert builder_inputs == [(older, duplicate_first, duplicate_second)]


def test_accepts_empty_history_and_still_calls_builder() -> None:
    config = TeamDiagnosticsSnapshotHistoryConfig()
    builder_calls: list[tuple[object, TeamDiagnosticsSnapshotHistoryConfig, datetime]] = []

    def load_snapshots(**_: object) -> tuple[TeamDiagnosticsSnapshotReport, ...]:
        return ()

    def history_builder(
        snapshots: object,
        *,
        config: TeamDiagnosticsSnapshotHistoryConfig,
        generated_at: datetime,
    ):
        builder_calls.append((tuple(snapshots), config, generated_at))  # type: ignore[arg-type]
        return build_team_diagnostics_snapshot_history_report(
            list(snapshots),  # type: ignore[arg-type]
            config=config,
            generated_at=generated_at,
        )

    history = load_team_diagnostics_snapshot_history_report(
        load_snapshots=load_snapshots,
        history_builder=history_builder,
        config=config,
        generated_at=GENERATED_AT,
    )

    assert builder_calls == [((), config, GENERATED_AT)]
    assert history.snapshot_count == 0
    assert history.latest_snapshot is None


def test_rejects_non_callable_loader_builder_and_non_exact_config() -> None:
    config = TeamDiagnosticsSnapshotHistoryConfig()
    calls: list[str] = []

    class ConfigSubclass(TeamDiagnosticsSnapshotHistoryConfig):
        pass

    def load_snapshots(**_: object) -> tuple[TeamDiagnosticsSnapshotReport, ...]:
        calls.append("load_snapshots")
        return ()

    def history_builder(
        snapshots: object,
        *,
        config: TeamDiagnosticsSnapshotHistoryConfig,
        generated_at: datetime,
    ) -> _HistoryResult:
        calls.append("history_builder")
        return _HistoryResult()

    with pytest.raises(ValueError, match="load_snapshots"):
        load_team_diagnostics_snapshot_history_report(
            load_snapshots=object(),
            history_builder=history_builder,
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="history_builder"):
        load_team_diagnostics_snapshot_history_report(
            load_snapshots=load_snapshots,
            history_builder=object(),
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="TeamDiagnosticsSnapshotHistoryConfig"):
        load_team_diagnostics_snapshot_history_report(
            load_snapshots=load_snapshots,
            history_builder=history_builder,
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )

    assert calls == []


def test_module_has_no_connection_lifecycle_write_env_or_psycopg_surface() -> None:
    module_path = Path(module_under_test.__file__)
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    banned_module_fragments = (
        "psycopg",
        "_env",
        "cli",
        "store",
    )
    banned_call_or_attribute_names = {
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "insert",
        "open",
        "persist",
        "rollback",
        "write",
    }

    assert all(
        fragment not in module_name
        for module_name in imported_modules
        for fragment in banned_module_fragments
    )
    assert not (set(call_names) & banned_call_or_attribute_names)
    assert not (set(attribute_names) & banned_call_or_attribute_names)


@pytest.mark.parametrize("flag_name", ["paper_only", "report_only", "readonly"])
def test_requires_returned_report_hard_flags_if_present(flag_name: str) -> None:
    config = TeamDiagnosticsSnapshotHistoryConfig()

    def load_snapshots(**_: object) -> tuple[TeamDiagnosticsSnapshotReport, ...]:
        return ()

    def history_builder(
        snapshots: object,
        *,
        config: TeamDiagnosticsSnapshotHistoryConfig,
        generated_at: datetime,
    ) -> Any:
        return _HistoryResult(**{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        load_team_diagnostics_snapshot_history_report(
            load_snapshots=load_snapshots,
            history_builder=history_builder,
            config=config,
            generated_at=GENERATED_AT,
        )
