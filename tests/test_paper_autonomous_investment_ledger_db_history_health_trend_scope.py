from __future__ import annotations

from importlib import import_module
import inspect


def test_investment_ledger_db_history_health_trend_module_is_pure_phase1_reducer() -> None:
    module = import_module(
        "polymarket_alpha_lab."
        "paper_autonomous_investment_ledger_db_history_health_trend",
    )
    source = inspect.getsource(module).lower()

    for banned in (
        "psycopg",
        "supabase",
        "os.environ",
        "requests",
        "httpx",
        "urllib",
        "private_key",
        "wallet",
        "account",
        "submit_order",
        "cancel_order",
        "replace_order",
        "execute",
        "approve",
        "trade",
        "open(",
        "print(",
    ):
        assert banned not in source
