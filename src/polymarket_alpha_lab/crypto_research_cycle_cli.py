"""Bounded CLI handlers for the crypto research-cycle commands.

Command registration stays in ``cli.py``; only these handler
implementations and the discarding store live here. The handler composes
the impure pieces (fetch, optional persistence, diagnostics) around the
pure contracts, driven by a per-team wiring table.
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


def _team_wiring(team_id: str) -> dict:
    from polymarket_alpha_lab.central_evidence_dispatch import (
        BTC_ITEM_REQUIREMENTS,
        ETH_ITEM_REQUIREMENTS,
    )
    from polymarket_alpha_lab.crypto_btc_evidence_adapter import adapt_btc_evidence
    from polymarket_alpha_lab.crypto_btc_team import (
        CryptoBtcTeamConfig,
        build_crypto_btc_team_forecast,
    )
    from polymarket_alpha_lab.crypto_eth_evidence_adapter import adapt_eth_evidence
    from polymarket_alpha_lab.crypto_eth_team import (
        CryptoEthTeamConfig,
        build_crypto_eth_team_forecast,
    )

    wiring = {
        "crypto_btc": {
            "spot_source": "kraken_btc_ticker",
            "spot_params": {"pair": "XBTUSD"},
            "requirements": BTC_ITEM_REQUIREMENTS,
            "adapter": adapt_btc_evidence,
            "builder": build_crypto_btc_team_forecast,
            "config_factory": CryptoBtcTeamConfig,
        },
        "crypto_eth": {
            "spot_source": "kraken_eth_ticker",
            "spot_params": {"pair": "ETHUSD"},
            "requirements": ETH_ITEM_REQUIREMENTS,
            "adapter": adapt_eth_evidence,
            "builder": build_crypto_eth_team_forecast,
            "config_factory": CryptoEthTeamConfig,
        },
    }
    if team_id not in wiring:
        raise ValueError(f"unsupported team {team_id!r}")
    return wiring[team_id]


def _yes_token_from_metadata(metadata_value: object) -> str | None:
    if not isinstance(metadata_value, dict):
        return None
    tokens = metadata_value.get("clob_token_ids")
    outcomes = metadata_value.get("outcomes")
    if not isinstance(tokens, list) or not tokens or not isinstance(outcomes, list):
        return None
    for index, outcome in enumerate(outcomes):
        if (
            isinstance(outcome, str)
            and outcome.strip().lower() == "yes"
            and index < len(tokens)
            and isinstance(tokens[index], str)
            and tokens[index].strip()
        ):
            return tokens[index]
    return None


def run_crypto_research_cycle_command(*, team: str, market: str) -> int:
    from datetime import UTC, datetime

    from polymarket_alpha_lab.btc_cycle_diagnostics import format_btc_cycle_diagnostics
    from polymarket_alpha_lab.central_data_acquisition import acquire_once
    from polymarket_alpha_lab.central_data_contracts import FailureStatus
    from polymarket_alpha_lab.central_data_db_row import TypedEnvelope
    from polymarket_alpha_lab.central_data_registry import (
        build_default_source_registry,
        default_allowed_hosts,
    )
    from polymarket_alpha_lab.central_data_transport import SafeGETTransport
    from polymarket_alpha_lab.central_evidence_dispatch import build_evidence_bundle
    from polymarket_alpha_lab.crypto_research_cycle import run_crypto_research_cycle
    from polymarket_alpha_lab.supabase_central_data_config import from_central_data_env

    if type(market) is not str or not market.strip():
        print("crypto-research-cycle failed: --market must be nonblank", file=sys.stderr)
        return 2
    try:
        wiring = _team_wiring(team)
    except ValueError:
        print(f"crypto-research-cycle failed: unsupported team {team!r}", file=sys.stderr)
        return 2

    registry = build_default_source_registry()
    transport = SafeGETTransport(
        allowed_hosts=default_allowed_hosts(),
        source_catalog=registry,
        max_attempts=2,
    )
    central_config = from_central_data_env()
    store = (
        None
        if central_config.enabled and central_config.dsn is not None
        else _DiscardingCentralStore()
    )
    if store is None:
        from polymarket_alpha_lab.central_data_psycopg import CentralDataPsycopg

        store = CentralDataPsycopg(central_config.dsn)

    gamma_params = {"condition_id": market} if market.startswith("0x") else {"slug": market}
    gamma_outcome = acquire_once(
        registry.get("polymarket_gamma_markets"),
        transport=transport,
        store=store,
        params={**gamma_params, "limit": 5},
    )
    if gamma_outcome.failure_status is not FailureStatus.NONE or not gamma_outcome.normalized_rows:
        print(
            "crypto-research-cycle blocked: gamma metadata unavailable "
            f"({gamma_outcome.failure_status.value}; {', '.join(gamma_outcome.reason_codes) or 'no reasons'})",
            file=sys.stderr,
        )
        return 1
    metadata_row = gamma_outcome.normalized_rows[0]
    metadata_value = TypedEnvelope.decode(dict(metadata_row.typed_value))
    yes_token = _yes_token_from_metadata(metadata_value)

    book_outcome = (
        acquire_once(
            registry.get("polymarket_clob_book"),
            transport=transport,
            store=store,
            params={"token_id": yes_token},
        )
        if yes_token is not None
        else None
    )
    spot_outcome = acquire_once(
        registry.get(wiring["spot_source"]),
        transport=transport,
        store=store,
        params=dict(wiring["spot_params"]),
    )

    now = datetime.now(UTC)
    observations_by_source: dict[str, list] = {
        "polymarket_gamma_markets": [metadata_row],
    }
    if book_outcome is not None and book_outcome.normalized_rows:
        observations_by_source["polymarket_clob_book"] = list(book_outcome.normalized_rows)
    if spot_outcome.normalized_rows:
        observations_by_source[wiring["spot_source"]] = list(spot_outcome.normalized_rows)

    bundle = build_evidence_bundle(
        team,
        wiring["requirements"],
        observations_by_source,
        registry,
        as_of=now,
        market_reference=market,
    )
    result = run_crypto_research_cycle(
        team_id=team,
        spot_item=_spot_item_name(team),
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
        config=wiring["config_factory"](config_version=f"m5-{team}-v1"),
        adapt_evidence=wiring["adapter"],
        build_forecast=wiring["builder"],
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


def _spot_item_name(team: str) -> str:
    return {"crypto_btc": "btc_spot_price", "crypto_eth": "eth_spot_price"}[team]


def run_btc_research_cycle_command(*, market: str) -> int:
    """Backward-compatible BTC-only entry (the M3 command)."""

    return run_crypto_research_cycle_command(team="crypto_btc", market=market)


__all__ = ("run_btc_research_cycle_command", "run_crypto_research_cycle_command")
