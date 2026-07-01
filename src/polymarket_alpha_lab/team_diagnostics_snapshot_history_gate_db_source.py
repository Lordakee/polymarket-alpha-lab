"""Pure DB readback composer for team diagnostics snapshot history gate."""

from __future__ import annotations

from importlib import import_module
from typing import Callable

from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryConfig,
)

__all__ = ("load_team_diagnostics_snapshot_history_gate_report",)


def load_team_diagnostics_snapshot_history_gate_report(
    *,
    history_loader: Callable[..., object],
    gate_builder: Callable[..., object],
    history_config: TeamDiagnosticsSnapshotHistoryConfig,
    gate_config: object,
    generated_at: object,
    team_id: str | None = None,
    market_slug: str | None = None,
    forecast_id: str | None = None,
    config_version: str | None = None,
    limit: int | None = None,
) -> object:
    if not callable(history_loader):
        raise ValueError("history_loader must be callable")
    if not callable(gate_builder):
        raise ValueError("gate_builder must be callable")
    if type(history_config) is not TeamDiagnosticsSnapshotHistoryConfig:
        raise ValueError("history_config must be a TeamDiagnosticsSnapshotHistoryConfig")
    if type(gate_config) is not _gate_config_type():
        raise ValueError("gate_config must be a TeamDiagnosticsSnapshotHistoryGateConfig")

    history_report = history_loader(
        config=history_config,
        generated_at=generated_at,
        team_id=team_id,
        market_slug=market_slug,
        forecast_id=forecast_id,
        config_version=config_version,
        limit=limit,
    )
    gate_report = gate_builder(
        history_report,
        config=gate_config,
        generated_at=generated_at,
    )
    _require_hard_flags(gate_report)
    return gate_report


def _require_hard_flags(report: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(report, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True")


def _gate_config_type() -> type:
    gate_module = import_module(
        "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate",
    )
    return gate_module.TeamDiagnosticsSnapshotHistoryGateConfig
