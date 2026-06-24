from __future__ import annotations

import ast
from pathlib import Path


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history_metrics.py",
)

ALLOWED_IMPORTS = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal",
}

GUARDED_TOKENS = (
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
)


def _module_source() -> str:
    assert MODULE_PATH.exists(), f"{MODULE_PATH} must exist"
    return MODULE_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_module_source())


def test_metrics_reducer_imports_only_standard_library_and_proposal_report_module() -> None:
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name in ALLOWED_IMPORTS, alias.name
        elif isinstance(node, ast.ImportFrom):
            assert node.module in ALLOWED_IMPORTS, node.module


def test_metrics_reducer_has_no_db_env_network_execution_or_guarded_tokens() -> None:
    source = _module_source().lower()

    for token in GUARDED_TOKENS:
        assert token not in source, token
