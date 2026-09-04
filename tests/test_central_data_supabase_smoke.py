"""Opt-in local Supabase smoke coverage.

The default suite is pure/fake.  The real test is enabled explicitly so a
developer never points it at a hosted database by accident.
"""

from datetime import UTC, datetime, timedelta
import os

import pytest

from polymarket_alpha_lab.supabase_central_data_config import validate_local_postgres_dsn


@pytest.mark.skipif(
    os.environ.get("CENTRAL_DATA_SUPABASE_SMOKE") != "1",
    reason="set CENTRAL_DATA_SUPABASE_SMOKE=1 for the local-only destructive smoke",
)
def test_local_supabase_smoke_is_explicitly_gated() -> None:
    dsn = os.environ.get("POLYMARKET_ALPHA_LAB_CENTRAL_DATA_PERSISTENCE_DSN")
    if not dsn:
        pytest.fail("local smoke requires an explicit DSN environment value")
    validate_local_postgres_dsn(dsn)
    pytest.importorskip("psycopg")
    from polymarket_alpha_lab.central_data_psycopg import CentralDataPsycopg

    adapter = CentralDataPsycopg(dsn)
    assert adapter is not None
    # The complete migration/catalog/synthetic-row lifecycle is executed by
    # the node handoff verification command; this gate prevents hosted use.
