"""Opt-in real-network smoke for registered central sources.

Disabled by default; enable with PAL_CENTRAL_DATA_NETWORK_SMOKE=1. Uses
the real SafeGETTransport against registered public sources and asserts
only status outcomes. It never touches the database and never prints
credentials. Fixture tests remain the authoritative acceptance surface.
"""

import os

import pytest

from polymarket_alpha_lab.central_data_contracts import CentralDataRequest, FailureStatus
from polymarket_alpha_lab.central_data_registry import (
    build_default_source_registry,
    default_allowed_hosts,
)
from polymarket_alpha_lab.central_data_transport import SafeGETTransport


pytestmark = pytest.mark.skipif(
    os.environ.get("PAL_CENTRAL_DATA_NETWORK_SMOKE") != "1",
    reason="set PAL_CENTRAL_DATA_NETWORK_SMOKE=1 for the bounded real-network smoke",
)


def test_registered_sources_answer_through_safe_transport() -> None:
    registry = build_default_source_registry()
    transport = SafeGETTransport(
        allowed_hosts=default_allowed_hosts(),
        source_catalog=registry,
        max_attempts=1,
    )
    kraken = registry.get("kraken_btc_ticker")
    response = transport.fetch(
        kraken,
        CentralDataRequest(
            source_id=kraken.source_id,
            url=kraken.url_template,
            headers={"accept": "application/json", "user-agent": transport.user_agent},
            query={"pair": "XBTUSD"},
        ),
    )
    assert response.failure_status is FailureStatus.NONE, response.failure_status
    assert response.body

    gamma = registry.get("polymarket_gamma_markets")
    response = transport.fetch(
        gamma,
        CentralDataRequest(
            source_id=gamma.source_id,
            url=gamma.url_template,
            headers={"accept": "application/json", "user-agent": transport.user_agent},
            query={"limit": "1"},
        ),
    )
    assert response.failure_status is FailureStatus.NONE, response.failure_status
    assert response.body


def test_full_btc_cycle_smoke_through_dispatch_and_reducer() -> None:
    from datetime import UTC, datetime

    from polymarket_alpha_lab.btc_research_cycle import run_btc_research_cycle
    from polymarket_alpha_lab.central_data_acquisition import acquire_once
    from polymarket_alpha_lab.central_data_db_row import TypedEnvelope
    from polymarket_alpha_lab.central_evidence_dispatch import (
        BTC_ITEM_REQUIREMENTS,
        build_evidence_bundle,
    )
    from polymarket_alpha_lab.central_data_psycopg import _JsonConnection
    from polymarket_alpha_lab.crypto_btc_team import CryptoBtcTeamConfig
    from psycopg.types.json import Jsonb

    class _DiscardingStore:
        def insert_raw_event(self, row):
            from polymarket_alpha_lab.central_data_store import CentralDataInsertResult

            return CentralDataInsertResult(row.raw_event_id, "not_persisted")

        def insert_normalized_observation(self, row):
            from polymarket_alpha_lab.central_data_store import CentralDataInsertResult

            return CentralDataInsertResult(row.normalized_observation_id, "not_persisted")

    registry = build_default_source_registry()
    transport = SafeGETTransport(
        allowed_hosts=default_allowed_hosts(),
        source_catalog=registry,
        max_attempts=2,
    )
    store = _DiscardingStore()
    gamma_outcome = acquire_once(
        registry.get("polymarket_gamma_markets"),
        transport=transport,
        store=store,
        params={"limit": "5"},
    )
    assert gamma_outcome.failure_status is FailureStatus.NONE
    assert gamma_outcome.normalized_rows
    metadata_row = gamma_outcome.normalized_rows[0]
    metadata_value = TypedEnvelope.decode(dict(metadata_row.typed_value))
    tokens = metadata_value.get("clob_token_ids") if isinstance(metadata_value, dict) else None
    yes_token = (
        tokens[0] if isinstance(tokens, list) and tokens and isinstance(tokens[0], str) else None
    )
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
        registry.get("kraken_btc_ticker"),
        transport=transport,
        store=store,
        params={"pair": "XBTUSD"},
    )
    assert spot_outcome.failure_status is FailureStatus.NONE

    now = datetime.now(UTC)
    observations = {"polymarket_gamma_markets": [metadata_row]}
    if book_outcome is not None and book_outcome.normalized_rows:
        observations["polymarket_clob_book"] = list(book_outcome.normalized_rows)
    if spot_outcome.normalized_rows:
        observations["kraken_btc_ticker"] = list(spot_outcome.normalized_rows)
    bundle = build_evidence_bundle(
        "crypto_btc",
        BTC_ITEM_REQUIREMENTS,
        observations,
        registry,
        as_of=now,
        market_reference="network-smoke",
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
        config=CryptoBtcTeamConfig(config_version="network-smoke-v1"),
    )
    assert result.status in {"ready", "blocked"}
    assert result.operator_packet
    assert result.cycle_id
