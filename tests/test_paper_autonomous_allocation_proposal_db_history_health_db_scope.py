from __future__ import annotations

from pathlib import Path


def test_health_db_row_module_is_pure_phase1_codec() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row as codec

    assert codec.__name__.endswith("_db_row")
    source = Path(
        "src/polymarket_alpha_lab/"
        "paper_autonomous_allocation_proposal_db_history_health_db_row.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    for banned in (
        "psycopg",
        "supabase",
        "environ",
        "requests",
        "httpx",
        "urllib",
        "client",
        "exchange",
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "execute",
        "submit",
        "approve",
        "commit",
        "rollback",
        "cursor",
        "print",
        "open",
    ):
        assert banned not in lowered
