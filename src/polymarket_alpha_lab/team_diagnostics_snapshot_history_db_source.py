"""Pure DB readback composer for team diagnostics snapshot history."""

from __future__ import annotations

from typing import Callable

from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryConfig,
)

__all__ = ("load_team_diagnostics_snapshot_history_report",)


def load_team_diagnostics_snapshot_history_report(
    *,
    load_snapshots: Callable[..., object],
    history_builder: Callable[..., object],
    config: TeamDiagnosticsSnapshotHistoryConfig,
    generated_at: object,
    team_id: str | None = None,
    market_slug: str | None = None,
    forecast_id: str | None = None,
    config_version: str | None = None,
    limit: int | None = None,
) -> object:
    if not callable(load_snapshots):
        raise ValueError("load_snapshots must be callable")
    if not callable(history_builder):
        raise ValueError("history_builder must be callable")
    if type(config) is not TeamDiagnosticsSnapshotHistoryConfig:
        raise ValueError("config must be a TeamDiagnosticsSnapshotHistoryConfig")

    loaded_snapshots = tuple(
        load_snapshots(
            team_id=team_id,
            market_slug=market_slug,
            forecast_id=forecast_id,
            config_version=config_version,
            limit=limit,
        ),
    )
    report = history_builder(
        _chronological_snapshots(loaded_snapshots),
        config=config,
        generated_at=generated_at,
    )
    _require_hard_flags_if_present(report)
    return report


def _chronological_snapshots(snapshots: tuple[object, ...]) -> tuple[object, ...]:
    indexed = list(enumerate(snapshots))
    indexed.sort(key=lambda item: (getattr(item[1], "generated_at"), item[0]))
    return tuple(snapshot for _, snapshot in indexed)


def _require_hard_flags_if_present(report: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if hasattr(report, flag_name) and getattr(report, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
