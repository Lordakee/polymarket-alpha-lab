from __future__ import annotations

import ast
import re
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "paper_probability_selection_summary_history_trend.py"
)

MUTATING_DOMAIN_TOKENS = frozenset(
    (
        "auth",
        "cancel_order",
        "execute_order",
        "exchange",
        "live",
        "mutation",
        "order",
        "private",
        "private_key",
        "replace_order",
        "sign",
        "signing",
        "submit_order",
        "trade",
        "wallet",
    ),
)
PERSISTENCE_TOKENS = frozenset(
    (
        "httpx",
        "jsonl",
        "mongo",
        "open",
        "path",
        "redis",
        "requests",
        "sqlalchemy",
        "sqlite",
        "subprocess",
        "urllib",
        "write",
        "write_bytes",
        "write_text",
    ),
)
NETWORK_OR_PROCESS_IMPORTS = frozenset(
    (
        "httpx",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    ),
)


def _source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _tokens(source: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z0-9_]*", source.lower()))


def _import_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            roots.add(node.module.split(".", 1)[0].lower())
    return roots


def test_history_trend_module_avoids_live_or_mutating_domain_scope() -> None:
    source = _source()
    tokens = _tokens(source)

    assert MUTATING_DOMAIN_TOKENS.isdisjoint(tokens)
    assert "private-key" not in source.lower()
    assert "private key" not in source.lower()
    assert "exchange mutation" not in source.lower()


def test_history_trend_module_avoids_non_supabase_durable_persistence_scope() -> None:
    source = _source()
    tokens = _tokens(source)
    imports = _import_roots(source)

    assert PERSISTENCE_TOKENS.isdisjoint(tokens)
    assert PERSISTENCE_TOKENS.isdisjoint(imports)
    assert NETWORK_OR_PROCESS_IMPORTS.isdisjoint(imports)
