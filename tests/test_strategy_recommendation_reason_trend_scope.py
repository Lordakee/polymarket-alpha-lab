from __future__ import annotations

import ast
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_recommendation_reason_trend.py"
)

WHOLE_MODULE_IMPORT: frozenset[str] | None = None

ALLOWED_IMPORTS = {
    "__future__": frozenset({"annotations"}),
    "dataclasses": frozenset({"dataclass"}),
    "datetime": frozenset({"UTC", "datetime"}),
    "decimal": frozenset({"Decimal", "ROUND_HALF_EVEN"}),
    "typing": frozenset({"Any"}),
    "polymarket_alpha_lab.strategy_recommendation_bundle": frozenset(
        {"PaperStrategyRecommendationBundleReport"},
    ),
    "polymarket_alpha_lab.strategy_recommendation_explain": frozenset(
        {
            "NO_REASON_CODE",
            "PaperStrategyRecommendationExplanationReport",
        },
    ),
    "polymarket_alpha_lab.strategy_recommendation_history": frozenset(
        {"PaperStrategyRecommendationHistoryReport"},
    ),
}

FORBIDDEN_IMPORT_PREFIXES = (
    "aiohttp",
    "clob_client",
    "eth_account",
    "eth_keys",
    "http",
    "httpx",
    "json",
    "os",
    "pathlib",
    "py_clob_client",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "urllib",
    "urllib3",
    "web3",
    "websocket",
    "websockets",
    "polymarket_alpha_lab.api",
    "polymarket_alpha_lab.auth",
    "polymarket_alpha_lab.cli",
    "polymarket_alpha_lab.execution",
    "polymarket_alpha_lab.journal",
    "polymarket_alpha_lab.orders",
    "polymarket_alpha_lab.paper",
    "polymarket_alpha_lab.paper_execution",
    "polymarket_alpha_lab.positions",
    "polymarket_alpha_lab.strategy_recommendation_log",
    "polymarket_alpha_lab.trading",
)

FORBIDDEN_CALL_NAMES = (
    "__import__",
    "compile",
    "eval",
    "exec",
    "open",
)

FORBIDDEN_NAME_FRAGMENTS = (
    "apikey",
    "api",
    "auth",
    "client",
    "credential",
    "secret",
    "privatekey",
    "wallet",
    "allowance",
    "signature",
    "relayer",
    "network",
    "reader",
    "loader",
    "logger",
    "clobclient",
    "liveorder",
    "orderbuilder",
    "createorder",
    "postorder",
    "cancelorder",
    "submitorder",
    "sendorder",
    "signorder",
)

ALLOWED_NAME_FRAGMENTS = {
    "paperstrategyrecommendationbundle report",
    "paperstrategyrecommendationexplanationreport",
    "paperstrategyrecommendationhistoryreport",
}

IDENTIFIER_TOKEN_RE = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+",
)
FORBIDDEN_NAME_TOKEN_ALIASES = {
    "apikey": (("api", "key"),),
    "privatekey": (("private", "key"),),
    "clobclient": (("clob", "client"),),
    "liveorder": (("live", "order"),),
    "orderbuilder": (("order", "builder"),),
    "createorder": (("create", "order"),),
    "postorder": (("post", "order"),),
    "cancelorder": (("cancel", "order"),),
    "submitorder": (("submit", "order"),),
    "sendorder": (("send", "order"),),
    "signorder": (("sign", "order"),),
}


def _module_tree() -> ast.Module:
    return ast.parse(MODULE_PATH.read_text(encoding="utf-8"))


def _module_matches_prefix(module_name: str, forbidden_prefix: str) -> bool:
    return (
        module_name == forbidden_prefix
        or module_name.startswith(f"{forbidden_prefix}.")
    )


def _normalize_identifier(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _identifier_tokens(value: str) -> tuple[str, ...]:
    return tuple(token.lower() for token in IDENTIFIER_TOKEN_RE.findall(value))


def _has_token_sequence(tokens: tuple[str, ...], sequence: tuple[str, ...]) -> bool:
    if not sequence or len(sequence) > len(tokens):
        return False
    return any(
        tokens[index : index + len(sequence)] == sequence
        for index in range(len(tokens) - len(sequence) + 1)
    )


def _forbidden_fragment_matches(name: str) -> bool:
    normalized_name = _normalize_identifier(name)
    tokens = _identifier_tokens(name)
    for allowed in ALLOWED_NAME_FRAGMENTS:
        if normalized_name == _normalize_identifier(allowed):
            return False
    for forbidden in FORBIDDEN_NAME_FRAGMENTS:
        normalized_forbidden = _normalize_identifier(forbidden)
        if normalized_forbidden in normalized_name:
            return True
        for alias in FORBIDDEN_NAME_TOKEN_ALIASES.get(normalized_forbidden, ()):
            if _has_token_sequence(tokens, alias):
                return True
    return False


def test_reason_trend_module_does_not_import_forbidden_surfaces():
    tree = _module_tree()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(
                    _module_matches_prefix(alias.name, forbidden)
                    for forbidden in FORBIDDEN_IMPORT_PREFIXES
                ), alias.name
                assert alias.name in ALLOWED_IMPORTS, alias.name
                assert ALLOWED_IMPORTS[alias.name] is WHOLE_MODULE_IMPORT
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            assert not any(
                _module_matches_prefix(module_name, forbidden)
                for forbidden in FORBIDDEN_IMPORT_PREFIXES
            ), module_name
            assert module_name in ALLOWED_IMPORTS, module_name
            allowed_names = ALLOWED_IMPORTS[module_name]
            if allowed_names is not WHOLE_MODULE_IMPORT:
                imported_names = {alias.name for alias in node.names}
                assert imported_names <= allowed_names, (module_name, imported_names)


def test_reason_trend_module_has_no_forbidden_runtime_calls_or_names():
    tree = _module_tree()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALL_NAMES
            elif isinstance(node.func, ast.Attribute):
                assert not _forbidden_fragment_matches(node.func.attr), node.func.attr
        if isinstance(node, ast.Attribute):
            assert not _forbidden_fragment_matches(node.attr), node.attr
        if isinstance(
            node,
            (
                ast.ClassDef,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            assert not _forbidden_fragment_matches(node.name), node.name
        if isinstance(node, ast.Name):
            assert not _forbidden_fragment_matches(node.id), node.id
        if isinstance(node, ast.arg):
            assert not _forbidden_fragment_matches(node.arg), node.arg


def test_reason_trend_module_declares_only_paper_report_boundary_in_strings():
    tree = _module_tree()

    forbidden_string_fragments = (
        "api key",
        "authenticate",
        "authorization",
        "client",
        "credential",
        "private key",
        "wallet",
        "network",
        "read file",
        "write file",
        "reader",
        "loader",
        "logger",
        "order construction",
        "place order",
        "submit order",
        "cancel order",
        "sign order",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            assert not any(
                fragment in lowered
                for fragment in forbidden_string_fragments
            ), node.value
