from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_autonomous_readiness_gate_psycopg.py"
)


def _module_tree() -> ast.Module:
    return ast.parse(ADAPTER_PATH.read_text(encoding="utf-8"))


def test_readiness_gate_psycopg_adapter_has_no_top_level_psycopg_import() -> None:
    tree = _module_tree()
    for node in tree.body:
        if isinstance(node, ast.Import):
            assert all(alias.name != "psycopg" for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is None or not node.module.startswith("psycopg")


def test_readiness_gate_psycopg_adapter_preserves_phase_one_scope_terms() -> None:
    source = ADAPTER_PATH.read_text(encoding="utf-8").lower()

    forbidden_terms = (
        "private_key",
        "wallet",
        "sign_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
        "account",
        "auth_token",
        "api_key",
    )
    for term in forbidden_terms:
        assert term not in source
