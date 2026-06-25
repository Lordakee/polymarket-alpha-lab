from __future__ import annotations

from pathlib import Path


def test_history_store_is_generic_db_api_boundary_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_probability_selection_summary_history_store.py",
    ).read_text(encoding="utf-8")
    lower = source.lower()

    assert "import psycopg" not in lower
    assert "import os" not in lower
    assert "environ" not in lower
    assert "commit(" not in lower
    assert "rollback(" not in lower

    for banned in (
        "private_key",
        "wallet",
        "signature",
        "signing",
        "order placement",
        "live_trading",
        "clob",
        "gamma",
    ):
        assert banned not in lower
