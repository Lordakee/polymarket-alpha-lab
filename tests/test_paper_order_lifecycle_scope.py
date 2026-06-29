from __future__ import annotations

from pathlib import Path

SOURCE = Path("src/polymarket_alpha_lab/paper_order_lifecycle.py")


def test_lifecycle_module_has_no_forbidden_surfaces():
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
        "live",
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


def test_lifecycle_module_imports_only_allowed_modules():
    text = SOURCE.read_text()
    allowed_prefixes = (
        "from __future__",
        "from dataclasses",
        "from datetime",
        "from decimal",
        "from polymarket_alpha_lab.paper_broker",
        "from polymarket_alpha_lab.paper_order_lifecycle",
        "import __future__",
        "import dataclasses",
        "import datetime",
        "import decimal",
    )
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert any(stripped.startswith(prefix) for prefix in allowed_prefixes), f"unexpected import: {stripped}"
