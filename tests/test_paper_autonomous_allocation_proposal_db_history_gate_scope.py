from __future__ import annotations

from importlib import import_module
import inspect


def test_allocation_proposal_db_history_gate_module_is_pure_paper_report_only_readonly():
    module = import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_gate",
    )
    source = inspect.getsource(module).lower()

    for banned in (
        "psycopg",
        "supabase",
        "os.environ",
        "polymarketpublicclient",
        "requests",
        "httpx",
        "wallet",
        "private_key",
        "relayer",
        "account",
        "signing",
        "exchange",
        "live_trading",
        "order",
    ):
        assert banned not in source
