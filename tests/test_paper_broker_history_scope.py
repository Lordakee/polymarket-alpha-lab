"""Scope tests for paper broker history/load modules."""

from __future__ import annotations

from pathlib import Path


SOURCES = (
    Path("src/polymarket_alpha_lab/paper_broker_history.py"),
    Path("src/polymarket_alpha_lab/paper_broker_load.py"),
)


def test_paper_broker_history_and_load_modules_have_no_forbidden_surfaces() -> None:
    forbidden = [
        "psycopg",
        "supabase",
        "os.environ",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "socket",
        "asyncio",
        "private_key",
        "wallet",
        "account",
        "submit_order",
        "cancel_order",
        "replace_order",
        "approve",
        "open(",
        "print(",
    ]
    for source in SOURCES:
        text = source.read_text()
        for token in forbidden:
            assert token not in text, f"forbidden token found in {source}: {token}"
