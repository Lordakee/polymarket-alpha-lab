from __future__ import annotations

import pytest

from polymarket_alpha_lab.supabase_team_forecast_config import (
    TEAM_FORECAST_DB_DSN_ENV_VAR,
    TEAM_FORECAST_DB_ENABLED_ENV_VAR,
    TEAM_FORECAST_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR,
    TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR,
)


LOCAL_DSN = "postgresql://postgres:local-secret@localhost:54322/postgres"


def test_disabled_db_fails_closed_without_calling_loaders() -> None:
    from polymarket_alpha_lab.team_diagnostics_db_source import (
        TeamDiagnosticsDbSourceRequest,
        load_team_diagnostics_rows_from_env,
    )

    calls: list[str] = []

    def forbidden_loader(*args: object, **kwargs: object) -> tuple[object, ...]:
        calls.append("called")
        return ()

    with pytest.raises(ValueError) as exc_info:
        load_team_diagnostics_rows_from_env(
            env={TEAM_FORECAST_DB_ENABLED_ENV_VAR: "false"},
            request=TeamDiagnosticsDbSourceRequest(),
            forecast_loader=forbidden_loader,
            evidence_loader=forbidden_loader,
            outcome_loader=forbidden_loader,
        )

    message = str(exc_info.value)
    assert "team forecast DB is disabled" in message
    assert "postgresql://" not in message
    assert calls == []


def test_missing_dsn_fails_closed_without_echoing_secret_shape() -> None:
    from polymarket_alpha_lab.team_diagnostics_db_source import (
        TeamDiagnosticsDbSourceRequest,
        load_team_diagnostics_rows_from_env,
    )

    with pytest.raises(ValueError) as exc_info:
        load_team_diagnostics_rows_from_env(
            env={TEAM_FORECAST_DB_ENABLED_ENV_VAR: "true"},
            request=TeamDiagnosticsDbSourceRequest(),
            forecast_loader=lambda *args, **kwargs: (),
            evidence_loader=lambda *args, **kwargs: (),
            outcome_loader=lambda *args, **kwargs: (),
        )

    message = str(exc_info.value)
    assert TEAM_FORECAST_DB_DSN_ENV_VAR in message
    assert "must be set" in message
    assert "postgresql://" not in message


def test_table_names_and_filters_are_passed_to_read_only_loaders() -> None:
    from polymarket_alpha_lab.team_diagnostics_db_source import (
        TeamDiagnosticsDbSourceRequest,
        load_team_diagnostics_rows_from_env,
    )

    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def forecast_loader(*args: object, **kwargs: object) -> tuple[str, ...]:
        calls.append(("forecast", args, kwargs))
        return ("forecast-row",)

    def evidence_loader(*args: object, **kwargs: object) -> tuple[str, ...]:
        calls.append(("evidence", args, kwargs))
        return ("evidence-row",)

    def outcome_loader(*args: object, **kwargs: object) -> tuple[str, ...]:
        calls.append(("outcome", args, kwargs))
        return ("outcome-row",)

    result = load_team_diagnostics_rows_from_env(
        env={
            TEAM_FORECAST_DB_ENABLED_ENV_VAR: "true",
            TEAM_FORECAST_DB_DSN_ENV_VAR: LOCAL_DSN,
            TEAM_FORECAST_DB_TABLE_ENV_VAR: "diagnostic_team_forecasts",
            TEAM_FORECAST_EVIDENCE_DB_TABLE_ENV_VAR: "diagnostic_team_evidence",
            TEAM_FORECAST_OUTCOME_DB_TABLE_ENV_VAR: "diagnostic_team_outcomes",
        },
        request=TeamDiagnosticsDbSourceRequest(
            team_id="crypto_btc",
            market_slug="bitcoin-above-120k",
            forecast_id="forecast-btc-1",
            limit=25,
        ),
        forecast_loader=forecast_loader,
        evidence_loader=evidence_loader,
        outcome_loader=outcome_loader,
    )

    assert result.forecasts == ("forecast-row",)
    assert result.evidence == ("evidence-row",)
    assert result.outcomes == ("outcome-row",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert calls == [
        (
            "forecast",
            (LOCAL_DSN,),
            {
                "team_id": "crypto_btc",
                "market_slug": "bitcoin-above-120k",
                "limit": 25,
                "table_name": "diagnostic_team_forecasts",
            },
        ),
        (
            "evidence",
            (LOCAL_DSN,),
            {
                "forecast_id": "forecast-btc-1",
                "team_id": "crypto_btc",
                "market_slug": "bitcoin-above-120k",
                "limit": 25,
                "table_name": "diagnostic_team_evidence",
            },
        ),
        (
            "outcome",
            (LOCAL_DSN,),
            {
                "team_id": "crypto_btc",
                "market_slug": "bitcoin-above-120k",
                "limit": 25,
                "table_name": "diagnostic_team_outcomes",
            },
        ),
    ]


def test_request_and_result_are_frozen_and_reject_mutation_concepts() -> None:
    from dataclasses import FrozenInstanceError

    from polymarket_alpha_lab.team_diagnostics_db_source import (
        TeamDiagnosticsDbRows,
        TeamDiagnosticsDbSourceRequest,
    )

    request = TeamDiagnosticsDbSourceRequest()
    result = TeamDiagnosticsDbRows(forecasts=(), evidence=(), outcomes=())

    with pytest.raises(FrozenInstanceError):
        request.team_id = "crypto_btc"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.forecasts = ("changed",)  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        TeamDiagnosticsDbRows(
            forecasts=(),
            evidence=(),
            outcomes=(),
            paper_only=False,
        )


def test_module_surface_does_not_expose_mutation_or_live_trading_concepts() -> None:
    import polymarket_alpha_lab.team_diagnostics_db_source as source

    forbidden_fragments = (
        "insert",
        "update",
        "delete",
        "write",
        "order",
        "wallet",
        "auth",
        "account",
        "sign",
        "cancel",
        "replace",
    )

    exported = tuple(getattr(source, "__all__", ()))
    rendered = " ".join(exported).lower()

    assert exported
    for fragment in forbidden_fragments:
        assert fragment not in rendered
