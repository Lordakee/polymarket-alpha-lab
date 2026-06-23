from __future__ import annotations

import ast
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_research_packet_source.py"
)

FORBIDDEN_IMPORT_PREFIXES = (
    "aiohttp",
    "http",
    "httpx",
    "os",
    "pathlib",
    "psycopg",
    "requests",
    "requests_html",
    "socket",
    "subprocess",
    "supabase",
    "urllib",
)
FORBIDDEN_PROJECT_MODULE_FRAGMENTS = (
    "archive",
    "auth",
    "client",
    "exchange",
    "execution",
    "journal",
    "network",
    "order",
    "persistence",
    "psycopg",
    "signing",
    "store",
    "wallet",
)
FORBIDDEN_CALL_NAMES = (
    "__import__",
    "compile",
    "eval",
    "exec",
    "open",
    "Popen",
    "run",
)
FORBIDDEN_CALL_ATTRIBUTES = (
    "Popen",
    "append",
    "connect",
    "delete",
    "get",
    "mkdir",
    "patch",
    "post",
    "put",
    "read_bytes",
    "read_text",
    "remove",
    "rename",
    "replace",
    "request",
    "rmdir",
    "run",
    "send",
    "unlink",
    "write",
    "write_bytes",
    "write_text",
)


def _module_source() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def _module_matches_prefix(module_name: str, forbidden_prefix: str) -> bool:
    return module_name == forbidden_prefix or module_name.startswith(
        f"{forbidden_prefix}.",
    )


def _has_forbidden_project_module_fragment(module_name: str) -> bool:
    segments = tuple(module_name.split("."))
    if not module_name.startswith("polymarket_alpha_lab."):
        return False
    return any(
        forbidden in segment
        for segment in segments[1:]
        for forbidden in FORBIDDEN_PROJECT_MODULE_FRAGMENTS
    )


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _call_attr(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _scope_violations(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _record_import_violation(alias.name, violations)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                _record_import_violation(node.module, violations)
        elif isinstance(node, ast.Call):
            name = _call_name(node)
            if name in FORBIDDEN_CALL_NAMES:
                violations.append(f"call:{name}")
            attr = _call_attr(node)
            if attr in FORBIDDEN_CALL_ATTRIBUTES:
                violations.append(f"call_attr:{attr}")
    return tuple(violations)


def _record_import_violation(module_name: str, violations: list[str]) -> None:
    if any(
        _module_matches_prefix(module_name, forbidden)
        for forbidden in FORBIDDEN_IMPORT_PREFIXES
    ):
        violations.append(f"import:{module_name}")
    if _has_forbidden_project_module_fragment(module_name):
        violations.append(f"project_import:{module_name}")


def test_strategy_candidate_research_packet_source_uses_only_pure_adapter_surfaces():
    assert _scope_violations(_module_source()) == ()


@pytest.mark.parametrize(
    "source",
    (
        "import socket\n",
        "import subprocess\n",
        "import os\n",
        "import pathlib\n",
        "from urllib import request\n",
        "from polymarket_alpha_lab.paper_research_packet_store import Store\n",
        "from polymarket_alpha_lab.paper_trade_journal import PaperTradeJournal\n",
        "from polymarket_alpha_lab.paper_execution import Executor\n",
        "from polymarket_alpha_lab.exchange_client import Client\n",
        "from polymarket_alpha_lab.wallet_signing import sign_payload\n",
        "from polymarket_alpha_lab.auth_token import token\n",
        "from polymarket_alpha_lab.network_archive import archive\n",
    ),
)
def test_scope_guard_rejects_io_network_process_persistence_and_live_trade_imports(
    source,
):
    assert _scope_violations(source)


@pytest.mark.parametrize(
    "source",
    (
        "open('artifact.json')\n",
        "__import__('os')\n",
        "eval('1 + 1')\n",
        "exec('value = 1')\n",
        "compile('value = 1', '<scope>', 'exec')\n",
        "subprocess.run(['echo', 'x'])\n",
        "subprocess.Popen(['echo', 'x'])\n",
        "socket.socket().connect(('127.0.0.1', 80))\n",
        "Path('artifact.json').read_text()\n",
        "Path('artifact.json').read_bytes()\n",
        "Path('artifact.json').write_text('x')\n",
        "Path('artifact.json').unlink()\n",
        "client.request('GET', '/')\n",
        "client.get('/')\n",
        "client.post('/', json={})\n",
        "client.put('/', json={})\n",
        "client.patch('/', json={})\n",
        "client.delete('/')\n",
        "PaperTradeJournal.append(row)\n",
    ),
)
def test_scope_guard_rejects_file_network_process_and_mutating_calls(source):
    assert _scope_violations(source)


def test_scope_guard_allows_harmless_pure_identifier_names():
    source = """
significant_edge = Decimal("0.100000")
assigned_rows = ()
source_order = ()
ordered_rows = tuple(source_order)
open_interest = Decimal("100.000000")
capitalized_label = "Open Interest"
"""

    assert _scope_violations(source) == ()
