from __future__ import annotations

from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "action_gated_strategy_recommendation_queue_db_row.py"
)


def test_action_gated_queue_db_row_module_stays_pure_db_boundary():
    source = MODULE_PATH.read_text(encoding="utf-8")

    forbidden_fragments = (
        "psycopg",
        "psycopg2",
        "postgres",
        "supabase",
        "os.environ",
        "getenv",
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "wallet",
        "account",
        "auth",
        "order",
        "trade",
        "live",
    )
    lowered = source.lower()

    for fragment in forbidden_fragments:
        assert fragment not in lowered
