from __future__ import annotations

import pytest
from pathlib import Path

SOURCE = Path("src/polymarket_alpha_lab/paper_autonomous_screening_decision_support_gate_transition.py")


def test_source_contains_no_forbidden_surfaces():
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
        "import io",
        "import sys",
        "import logging",
        "import pathlib",
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
        assert token not in text, token
