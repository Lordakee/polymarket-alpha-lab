"""Bounded CLI handler for the M3/M4 BTC research-cycle command.

Extracted from ``cli.py`` in M4 (operational quality): the command
registration stays in ``cli.py``; only this handler implementation and
its discarding store live here. The handler composes the impure pieces
(fetch, optional persistence, diagnostics) around the pure contracts.
"""

from __future__ import annotations

import sys


class _DiscardingCentralStore:
    """No-op store used when central-data persistence is disabled."""

    def insert_raw_event(self, row):
        from polymarket_alpha_lab.central_data_store import CentralDataInsertResult

        return CentralDataInsertResult(row.raw_event_id, "not_persisted")

    def insert_normalized_observation(self, row):
        from polymarket_alpha_lab.central_data_store import CentralDataInsertResult

        return CentralDataInsertResult(row.normalized_observation_id, "not_persisted")


def run_btc_research_cycle_command(*, market: str) -> int:
    from datetime import UTC, datetime

    from polymarket_alpha_lab.btc_research_cycle import run_btc_research_cycle
    from polymarket_alpha_lab.central_data_acquisition import acquire_once
    from polymarket_alpha_lab.central_data_contracts import FailureStatus
    from polymarket_alpha_lab.central_data_db_row import TypedEnvelope
    from polymarket_alpha_lab.central_data_registry import (
        build_default_source_registry,
        default_allowed_hosts,
    )
    from polymarket_alpha_lab.central_data_transport import SafeGETTransport
    from polymarket_alpha_lab.central_evidence_dispatch import (
        BTC_ITEM_REQUIREMENTS,
        build_evidence_bundle,
    )
    from polymarket_alpha_lab.crypto_btc_team import CryptoBtcTeamConfig
    from polymarket_alpha_lab.supabase_central_data_config import from_central_data_env

    if type(market) is not str or not market.strip():
        print("btc-research-cycle failed: --market must be nonblank", file=sys.stderr)
        return 2

    registry = build_default_source_registry()
    transport = SafeGETTransport(
        allowed_hosts=default_allowed_hosts(),
        source_catalog=registry,
        max_attempts=2,
    )
    central_config = from_central_data_env()
    if central_config.enabled and central_config.dsn is not None:
        from polymarket_alpha_lab.central_data_psycopg import CentralDataPsycopg

        central_adapter = CentralDataPsycopg(central_config.dsn)
        gamma_params = {"condition_id": market} if market.startswith("0x") else {"slug": market}
        gamma_outcome = acquire_once(
            registry.get("polymarket_gamma_markets"),
            transport=transport,
            store=central_adapter,
            params={**gamma_params, "limit": 5},
        )
    else:
        store = _DiscardingCentralStore()
        gamma_params = {"condition_id": market} if market.startswith("0x") else {"slug": market}
        gamma_outcome = acquire_once(
            registry.get("polymarket_gamma_markets"),
            transport=transport,
            store=store,
            params={**gamma_params, "limit": 5},
        )

    if gamma_outcome.failure_status is not FailureStatus.NONE or not gamma_outcome.normalized_rows:
        print(
            "btc-research-cycle blocked: gamma metadata unavailable "
            f"({gamma_outcome.failure_status.value}; {', '.join(gamma_outcome.reason_codes) or 'no reasons'})",
            file=sys.stderr,
        )
        return 1
    metadata_row = gamma_outcome.normalized_rows[0]
    metadata_value = TypedEnvelope.decode(dict(metadata_row.typed_value))
    tokens = metadata_value.get("clob_token_ids") if isinstance(metadata_value, dict) else None
    yes_token = tokens[0] if isinstance(tokens, list) and tokens and isinstance(tokens[0], str) else None

    def _acquire(source_id, params):
        target_store = (
            central_adapter
            if central_config.enabled and central_config.dsn is not None
            else store
        )
        return acquire_once(
            registry.get(source_id),
            transport=transport,
            store=target_store,
            params=params,
        )

    book_outcome = (
        _acquire("polymarket_clob_book", {"token_id": yes_token})
        if yes_token is not None
        else None
    )
    spot_outcome = _acquire("kraken_btc_ticker", {"pair": "XBTUSD"})

    now = datetime.now(UTC)
    observations_by_source: dict[str, list] = {
        "polymarket_gamma_markets": [metadata_row],
    }
    if book_outcome is not None and book_outcome.normalized_rows:
        observations_by_source["polymarket_clob_book"] = list(book_outcome.normalized_rows)
    if spot_outcome.normalized_rows:
        observations_by_source["kraken_btc_ticker"] = list(spot_outcome.normalized_rows)

    bundle = build_evidence_bundle(
        "crypto_btc",
        BTC_ITEM_REQUIREMENTS,
        observations_by_source,
        registry,
        as_of=now,
        market_reference=market,
    )
    result = run_btc_research_cycle(
        bundle=bundle,
        metadata_observation=metadata_row,
        book_observation=book_outcome.normalized_rows[0]
        if book_outcome is not None and book_outcome.normalized_rows
        else None,
        spot_observation=spot_outcome.normalized_rows[0]
        if spot_outcome.normalized_rows
        else None,
        as_of=now,
        generated_at=now,
        config=CryptoBtcTeamConfig(config_version="m3-btc-slice-v1"),
        market_slug_hint=market,
        condition_id_hint=market,
    )

    from polymarket_alpha_lab.supabase_team_forecast_config import from_team_forecast_db_env

    forecast_config = from_team_forecast_db_env()
    if result.status == "ready" and forecast_config.enabled and forecast_config.dsn is not None:
        from polymarket_alpha_lab.team_forecast_psycopg import (
            insert_team_forecast_evidence_with_psycopg,
            insert_team_forecast_with_psycopg,
        )

        insert_team_forecast_with_psycopg(
            forecast_config.dsn,
            result.forecast,
            table_name=forecast_config.team_forecast_table_name,
        )
        for evidence_packet in result.evidence_packets:
            insert_team_forecast_evidence_with_psycopg(
                forecast_config.dsn,
                evidence_packet,
                forecast_id=result.forecast.forecast_id,
                config_version=result.forecast.config_version,
                generated_at=result.forecast.generated_at,
                table_name=forecast_config.team_forecast_evidence_table_name,
            )

    from polymarket_alpha_lab.btc_cycle_diagnostics import (
        format_btc_cycle_diagnostics,
    )

    print(result.operator_packet)
    print()
    print(
        format_btc_cycle_diagnostics(
            [outcome for outcome in (gamma_outcome, book_outcome, spot_outcome) if outcome is not None],
            bundle,
            result,
        )
    )
    return 0 if result.status == "ready" else 1


