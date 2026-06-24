from __future__ import annotations

import ast
import re
from pathlib import Path


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_history.py",
)

ALLOWED_IMPORTS = {
    "__future__",
    "dataclasses",
    "datetime",
    "decimal",
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal",
}

FORBIDDEN_RAW_FRAGMENTS = (
    "private_key",
    "wallet",
    "submit_order",
    "cancel_order",
    "replace_order",
    "requests.",
    "httpx.",
    "urllib.",
    "subprocess",
    "open(",
    "print(",
)

FORBIDDEN_NAME_PATTERNS = (
    r"\bauth\b",
    r"\baccount\b",
    r"\bapi_key\b",
    r"\border\b",
    r"\btrade\b",
    r"\bsign\b",
    r"\bsubmit\b",
    r"\bcancel\b",
    r"\bapprove\b",
    r"\bexecute\b",
)


def _module_source() -> str:
    assert MODULE_PATH.exists(), f"{MODULE_PATH} must exist"
    return MODULE_PATH.read_text(encoding="utf-8")


def _tree() -> ast.Module:
    return ast.parse(_module_source())


def test_allocation_proposal_db_history_imports_only_standard_library_and_source_report_module() -> None:
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] in ALLOWED_IMPORTS
        elif isinstance(node, ast.ImportFrom):
            assert node.module in ALLOWED_IMPORTS


def test_allocation_proposal_db_history_omits_io_network_process_and_execution_fragments() -> None:
    source = _module_source().lower()

    for fragment in FORBIDDEN_RAW_FRAGMENTS:
        assert fragment not in source


def test_allocation_proposal_db_history_omits_live_auth_account_order_names() -> None:
    identifiers: list[str] = []
    for node in ast.walk(_tree()):
        if isinstance(node, ast.Name):
            identifiers.append(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.append(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            identifiers.append(node.name)
        elif isinstance(node, ast.arg):
            identifiers.append(node.arg)

    identifier_text = "\n".join(identifiers).lower()
    for pattern in FORBIDDEN_NAME_PATTERNS:
        assert re.search(pattern, identifier_text) is None, pattern
