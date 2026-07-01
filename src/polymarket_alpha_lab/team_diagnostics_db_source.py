"""Read-only local Supabase source for team diagnostics."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from polymarket_alpha_lab import supabase_team_forecast_config
from polymarket_alpha_lab.supabase_team_forecast_config import SupabaseTeamForecastConfig


_RowLoader = Callable[..., tuple[Any, ...]]


@dataclass(frozen=True)
class TeamDiagnosticsDbSourceRequest:
    team_id: str | None = None
    market_slug: str | None = None
    forecast_id: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class TeamDiagnosticsDbRows:
    forecasts: tuple[Any, ...]
    evidence: tuple[Any, ...]
    outcomes: tuple[Any, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "forecasts", tuple(self.forecasts))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "outcomes", tuple(self.outcomes))
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")


def load_team_diagnostics_rows_from_env(
    *,
    env: Mapping[str, str] | None = None,
    request: TeamDiagnosticsDbSourceRequest | None = None,
    forecast_loader: _RowLoader | None = None,
    evidence_loader: _RowLoader | None = None,
    outcome_loader: _RowLoader | None = None,
) -> TeamDiagnosticsDbRows:
    config = supabase_team_forecast_config.from_team_forecast_db_env(env)
    return load_team_diagnostics_rows(
        config=config,
        request=TeamDiagnosticsDbSourceRequest() if request is None else request,
        forecast_loader=forecast_loader,
        evidence_loader=evidence_loader,
        outcome_loader=outcome_loader,
    )


def load_team_diagnostics_rows(
    *,
    config: SupabaseTeamForecastConfig,
    request: TeamDiagnosticsDbSourceRequest,
    forecast_loader: _RowLoader | None = None,
    evidence_loader: _RowLoader | None = None,
    outcome_loader: _RowLoader | None = None,
) -> TeamDiagnosticsDbRows:
    if type(config) is not SupabaseTeamForecastConfig:
        raise ValueError("config must be a SupabaseTeamForecastConfig")
    if type(request) is not TeamDiagnosticsDbSourceRequest:
        raise ValueError("request must be a TeamDiagnosticsDbSourceRequest")
    if not config.enabled:
        raise ValueError("team forecast DB is disabled")
    if config.dsn is None:
        raise ValueError("team forecast DB DSN must be set")

    forecast_loader = _default_forecast_loader() if forecast_loader is None else forecast_loader
    evidence_loader = _default_evidence_loader() if evidence_loader is None else evidence_loader
    outcome_loader = _default_outcome_loader() if outcome_loader is None else outcome_loader

    forecasts = forecast_loader(
        config.dsn,
        team_id=request.team_id,
        market_slug=request.market_slug,
        limit=request.limit,
        table_name=config.team_forecast_table_name,
    )
    evidence = evidence_loader(
        config.dsn,
        forecast_id=request.forecast_id,
        team_id=request.team_id,
        market_slug=request.market_slug,
        limit=request.limit,
        table_name=config.team_forecast_evidence_table_name,
    )
    outcomes = outcome_loader(
        config.dsn,
        team_id=request.team_id,
        market_slug=request.market_slug,
        limit=request.limit,
        table_name=config.team_forecast_outcome_table_name,
    )
    return TeamDiagnosticsDbRows(
        forecasts=forecasts,
        evidence=evidence,
        outcomes=outcomes,
    )


def _default_forecast_loader() -> _RowLoader:
    return _psycopg_loader(
        "load_team_forecast_rows_with_psycopg",
        "load_team_forecasts_with_psycopg",
    )


def _default_evidence_loader() -> _RowLoader:
    return _psycopg_loader(
        "load_team_forecast_evidence_rows_with_psycopg",
        "load_team_forecast_evidence_with_psycopg",
    )


def _default_outcome_loader() -> _RowLoader:
    return _psycopg_loader(
        "load_team_forecast_outcome_rows_with_psycopg",
        "load_team_forecast_outcomes_with_psycopg",
    )


def _psycopg_loader(primary_name: str, fallback_name: str) -> _RowLoader:
    from polymarket_alpha_lab import team_forecast_psycopg

    loader = getattr(team_forecast_psycopg, primary_name, None)
    if loader is None:
        loader = getattr(team_forecast_psycopg, fallback_name, None)
    if loader is None:
        raise RuntimeError("team forecast psycopg row loaders are unavailable")
    return loader


__all__ = (
    "TeamDiagnosticsDbRows",
    "TeamDiagnosticsDbSourceRequest",
    "load_team_diagnostics_rows",
    "load_team_diagnostics_rows_from_env",
)
