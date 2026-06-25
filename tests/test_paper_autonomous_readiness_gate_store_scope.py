from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STORE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_autonomous_readiness_gate_store.py"
)


def _module_tree() -> ast.Module:
    return ast.parse(STORE_PATH.read_text(encoding="utf-8"))


def test_readiness_gate_store_does_not_import_forbidden_boundaries() -> None:
    tree = _module_tree()
    imported_roots: set[str] = set()
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".", maxsplit=1)[0])
                imported_names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_roots.add(node.module.split(".", maxsplit=1)[0])
                imported_names.add(node.module)

    forbidden_roots = {
        "os",
        "psycopg",
        "requests",
        "supabase",
        "web3",
    }
    assert imported_roots.isdisjoint(forbidden_roots)
    assert all("polymarket_client" not in name for name in imported_names)


def test_readiness_gate_store_preserves_phase_one_scope_terms() -> None:
    source = STORE_PATH.read_text(encoding="utf-8").lower()

    forbidden_terms = (
        "private_key",
        "wallet",
        "sign_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
        "auth_token",
        "api_key",
        "commit(",
        "rollback(",
    )
    for term in forbidden_terms:
        assert term not in source
