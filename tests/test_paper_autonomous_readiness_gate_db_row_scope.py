from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_autonomous_readiness_gate_db_row.py"
)


def normalize_identifier(value: str) -> str:
    return "".join(character for character in value.lower() if character.isalnum())


def test_readiness_gate_db_row_is_pure_codec_without_live_or_db_connection_surface():
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    module_docstring = ast.get_docstring(tree)
    forbidden_fragments = {
        "account",
        "auth",
        "cancel",
        "client",
        "connect",
        "dsn",
        "exchange",
        "live",
        "order",
        "privatekey",
        "psycopg",
        "sign",
        "sqlite",
        "submit",
        "supabase",
        "wallet",
    }

    values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            values.append(node.module or "")
            values.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.Name):
            values.append(node.id)
        elif isinstance(node, ast.Attribute):
            values.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value != module_docstring:
                values.append(node.value)

    normalized_values = tuple(normalize_identifier(value) for value in values)
    for fragment in forbidden_fragments:
        normalized_fragment = normalize_identifier(fragment)
        matches = tuple(
            value
            for value in normalized_values
            if normalized_fragment in value
        )
        assert matches == (), (fragment, matches)
