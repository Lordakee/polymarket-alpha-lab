from __future__ import annotations

import builtins
import importlib
import os
import sys
from dataclasses import dataclass
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeForecast:
    forecast_id: str
    team_id: str
    market_slug: str


@dataclass(frozen=True)
class FakeEvidence:
    evidence_id: str
    forecast_id: str
    team_id: str
    market_slug: str


@dataclass(frozen=True)
class FakeOutcome:
    outcome_id: str
    forecast_id: str
    team_id: str
    market_slug: str


@dataclass(frozen=True)
class FakeBundle:
    bundle_status: str
    rows: tuple[dict[str, Any], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _import_module():
    sys.modules.pop("polymarket_alpha_lab.team_cli_wiring", None)
    return importlib.import_module("polymarket_alpha_lab.team_cli_wiring")


def test_request_rejects_blank_filters_and_nonpositive_limit() -> None:
    wiring = _import_module()

    with pytest.raises(ValueError, match="team_id.*canonical nonblank"):
        wiring.TeamDiagnosticsCliRequest(team_id=" crypto_btc")
    with pytest.raises(ValueError, match="market_slug.*canonical nonblank"):
        wiring.TeamDiagnosticsCliRequest(market_slug="")
    with pytest.raises(ValueError, match="forecast_id.*canonical nonblank"):
        wiring.TeamDiagnosticsCliRequest(forecast_id="forecast-1 ")
    with pytest.raises(ValueError, match="limit.*positive"):
        wiring.TeamDiagnosticsCliRequest(limit=0)
    with pytest.raises(ValueError, match="limit.*int"):
        wiring.TeamDiagnosticsCliRequest(limit=True)


def test_run_invokes_loaders_with_cli_filters_and_builds_compact_rows() -> None:
    wiring = _import_module()
    calls: list[tuple[str, dict[str, Any]]] = []
    forecasts = (
        FakeForecast("forecast-1", "crypto_btc", "bitcoin-above-120k"),
        FakeForecast("forecast-2", "crypto_btc", "bitcoin-above-120k"),
    )
    evidence = (
        FakeEvidence("evidence-1", "forecast-1", "crypto_btc", "bitcoin-above-120k"),
    )
    outcomes = (
        FakeOutcome("outcome-1", "forecast-1", "crypto_btc", "bitcoin-above-120k"),
    )

    def load_forecasts(**filters: Any) -> tuple[FakeForecast, ...]:
        calls.append(("forecasts", filters))
        return forecasts

    def load_evidence(**filters: Any) -> tuple[FakeEvidence, ...]:
        calls.append(("evidence", filters))
        return evidence

    def load_outcomes(**filters: Any) -> tuple[FakeOutcome, ...]:
        calls.append(("outcomes", filters))
        return outcomes

    def build_bundle(*, forecasts: Any, evidence: Any, outcomes: Any) -> FakeBundle:
        calls.append(
            (
                "bundle",
                {
                    "forecasts": forecasts,
                    "evidence": evidence,
                    "outcomes": outcomes,
                },
            ),
        )
        return FakeBundle(
            bundle_status="watch",
            rows=(
                {
                    "section": "forecast",
                    "label": "latest",
                    "value": "2",
                },
            ),
        )

    result = wiring.run_team_diagnostics_cli_request(
        wiring.TeamDiagnosticsCliRequest(
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            forecast_id="forecast-1",
            limit=5,
        ),
        loaders=wiring.TeamDiagnosticsCliLoaders(
            load_forecasts=load_forecasts,
            load_evidence=load_evidence,
            load_outcomes=load_outcomes,
        ),
        bundle_builder=build_bundle,
    )

    assert calls == [
        (
            "forecasts",
            {
                "team_id": "crypto_btc",
                "market_slug": "bitcoin-above-120k",
                "limit": 5,
            },
        ),
        (
            "evidence",
            {
                "forecast_id": "forecast-1",
                "team_id": "crypto_btc",
                "market_slug": "bitcoin-above-120k",
                "limit": 5,
            },
        ),
        (
            "outcomes",
            {
                "team_id": "crypto_btc",
                "market_slug": "bitcoin-above-120k",
                "limit": 5,
            },
        ),
        (
            "bundle",
            {
                "forecasts": forecasts,
                "evidence": evidence,
                "outcomes": outcomes,
            },
        ),
    ]
    assert result.summary_rows == (
        wiring.TeamDiagnosticsCliOutputRow("filter", "team_id", "crypto_btc"),
        wiring.TeamDiagnosticsCliOutputRow(
            "filter",
            "market_slug",
            "bitcoin-above-120k",
        ),
        wiring.TeamDiagnosticsCliOutputRow("filter", "forecast_id", "forecast-1"),
        wiring.TeamDiagnosticsCliOutputRow("filter", "limit", "5"),
        wiring.TeamDiagnosticsCliOutputRow("count", "forecasts", "2"),
        wiring.TeamDiagnosticsCliOutputRow("count", "evidence", "1"),
        wiring.TeamDiagnosticsCliOutputRow("count", "outcomes", "1"),
        wiring.TeamDiagnosticsCliOutputRow("bundle", "bundle_status", "watch"),
        wiring.TeamDiagnosticsCliOutputRow("forecast", "latest", "2"),
    )
    assert result.forecasts == forecasts
    assert result.evidence == evidence
    assert result.outcomes == outcomes
    assert result.bundle == FakeBundle(
        bundle_status="watch",
        rows=(
            {
                "section": "forecast",
                "label": "latest",
                "value": "2",
            },
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_result_shape_is_deterministic_when_filters_are_absent() -> None:
    wiring = _import_module()

    def empty_loader(**filters: Any) -> tuple[Any, ...]:
        assert filters == {}
        return ()

    result = wiring.run_team_diagnostics_cli_request(
        wiring.TeamDiagnosticsCliRequest(),
        loaders=wiring.TeamDiagnosticsCliLoaders(
            load_forecasts=empty_loader,
            load_evidence=empty_loader,
            load_outcomes=empty_loader,
        ),
        bundle_builder=lambda **_: None,
    )

    assert result.summary_rows == (
        wiring.TeamDiagnosticsCliOutputRow("count", "forecasts", "0"),
        wiring.TeamDiagnosticsCliOutputRow("count", "evidence", "0"),
        wiring.TeamDiagnosticsCliOutputRow("count", "outcomes", "0"),
        wiring.TeamDiagnosticsCliOutputRow("bundle", "status", "unavailable"),
    )


def test_import_and_run_do_not_import_psycopg_or_read_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__
    imported: list[str] = []

    def guarded_import(
        name: str,
        globals: dict[str, Any] | None = None,
        locals: dict[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        imported.append(name)
        if name.startswith("psycopg"):
            raise AssertionError("team_cli_wiring must not import psycopg")
        return original_import(name, globals, locals, fromlist, level)

    def getenv_guard(*_: Any, **__: Any) -> str:
        raise AssertionError("team_cli_wiring must not read environment")

    def environ_get_guard(*_: Any, **__: Any) -> str:
        raise AssertionError("team_cli_wiring must not read environment")

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(os, "getenv", getenv_guard)
    monkeypatch.setattr(os.environ, "get", environ_get_guard)
    wiring = _import_module()

    result = wiring.run_team_diagnostics_cli_request(
        wiring.TeamDiagnosticsCliRequest(limit=1),
        loaders=wiring.TeamDiagnosticsCliLoaders(
            load_forecasts=lambda **_: (),
            load_evidence=lambda **_: (),
            load_outcomes=lambda **_: (),
        ),
        bundle_builder=lambda **_: None,
    )

    assert result.summary_rows[0] == wiring.TeamDiagnosticsCliOutputRow(
        "filter",
        "limit",
        "1",
    )
    assert "psycopg" not in imported


def test_loaders_must_be_injected_callables() -> None:
    wiring = _import_module()

    with pytest.raises(ValueError, match="load_forecasts.*callable"):
        wiring.TeamDiagnosticsCliLoaders(
            load_forecasts=None,
            load_evidence=lambda **_: (),
            load_outcomes=lambda **_: (),
        )
