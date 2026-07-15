from __future__ import annotations

from pathlib import Path

SOURCE = Path("src/polymarket_alpha_lab/paper_autonomous_candidate_selection.py")


def test_candidate_selection_module_has_no_forbidden_surfaces() -> None:
    text = SOURCE.read_text()
    forbidden = [
        "psycopg",
        "supabase",
        "os.environ",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "network",
        "open(",
        "print(",
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "execute",
        "submit",
        "cancel",
        "replace",
        "paper_autonomous_allocation",
        "allocation_proposal",
    ]
    for token in forbidden:
        assert token not in text, f"forbidden token found: {token}"


def test_candidate_selection_module_imports_only_allowed_modules() -> None:
    text = SOURCE.read_text()
    allowed_prefixes = (
        "from __future__",
            "from dataclasses",
            "from datetime",
            "from decimal",
            "from polymarket_alpha_lab.strategy_candidate_decision_matrix",
            "from polymarket_alpha_lab.strategy_candidate_research_queue",
            "import __future__",
        "import dataclasses",
        "import datetime",
        "import decimal",
    )
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert any(
                stripped.startswith(prefix) for prefix in allowed_prefixes
            ), f"unexpected import: {stripped}"
