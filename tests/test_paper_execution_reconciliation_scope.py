"""Scope tests for paper_execution_reconciliation module."""

from __future__ import annotations

from pathlib import Path

SOURCE = Path("src/polymarket_alpha_lab/paper_execution_reconciliation.py")


def test_reconciliation_module_has_no_forbidden_surfaces():
    text = SOURCE.read_text()
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
        "execute",
        "approve",
        "trade",
        "open(",
        "print(",
    ]
    for token in forbidden:
        assert token not in text, f"forbidden token found: {token}"
