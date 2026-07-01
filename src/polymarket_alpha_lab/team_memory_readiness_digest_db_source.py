"""Pure DB readback composer for team memory readiness digest."""

from __future__ import annotations

from importlib import import_module
from typing import Callable

from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryConfig,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id

__all__ = ("load_team_memory_readiness_digest_report",)


def load_team_memory_readiness_digest_report(
    *,
    team_ids: tuple[str, ...],
    gate_loader: Callable[..., object],
    digest_builder: Callable[..., object],
    digest_config: object,
    history_config: TeamDiagnosticsSnapshotHistoryConfig,
    gate_config: object,
    generated_at: object,
    config_version: str | None = None,
    limit: int | None = None,
) -> object:
    if not callable(gate_loader):
        raise ValueError("gate_loader must be callable")
    if not callable(digest_builder):
        raise ValueError("digest_builder must be callable")

    normalized_team_ids = _normalize_team_ids(team_ids)
    if type(digest_config) is not _digest_config_type():
        raise ValueError("digest_config must be a TeamMemoryReadinessDigestConfig")
    if type(history_config) is not TeamDiagnosticsSnapshotHistoryConfig:
        raise ValueError("history_config must be a TeamDiagnosticsSnapshotHistoryConfig")
    if type(gate_config) is not _gate_config_type():
        raise ValueError("gate_config must be a TeamDiagnosticsSnapshotHistoryGateConfig")

    _require_hard_flags("digest_config", digest_config)
    _require_hard_flags("history_config", history_config)
    _require_hard_flags("gate_config", gate_config)

    digest_source_type = _digest_source_type()
    digest_sources = tuple(
        digest_source_type(
            team_id=team_id,
            gate_report=gate_loader(
                team_id=team_id,
                history_config=history_config,
                gate_config=gate_config,
                generated_at=generated_at,
                config_version=config_version,
                limit=limit,
            ),
        )
        for team_id in normalized_team_ids
    )
    digest_report = digest_builder(
        digest_sources,
        config=digest_config,
        generated_at=generated_at,
    )
    _require_hard_flags("digest_report", digest_report)
    return digest_report


def _normalize_team_ids(team_ids: tuple[str, ...]) -> tuple[str, ...]:
    if type(team_ids) not in (list, tuple):
        raise ValueError("team_ids must be a list or tuple")
    normalized = tuple(team_ids)
    if not normalized:
        raise ValueError("team_ids must contain at least one value")

    seen: set[str] = set()
    for team_id in normalized:
        require_team_id("team_ids", team_id)
        if team_id in seen:
            raise ValueError("team_ids must be unique")
        seen.add(team_id)
    return normalized


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{name} {flag_name} must be True")


def _digest_config_type() -> type:
    digest_module = import_module("polymarket_alpha_lab.team_memory_readiness_digest")
    return digest_module.TeamMemoryReadinessDigestConfig


def _digest_source_type() -> type:
    digest_module = import_module("polymarket_alpha_lab.team_memory_readiness_digest")
    return digest_module.TeamMemoryReadinessDigestSource


def _gate_config_type() -> type:
    gate_module = import_module(
        "polymarket_alpha_lab.team_diagnostics_snapshot_history_gate",
    )
    return gate_module.TeamDiagnosticsSnapshotHistoryGateConfig
