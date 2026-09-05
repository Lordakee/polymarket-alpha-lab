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
