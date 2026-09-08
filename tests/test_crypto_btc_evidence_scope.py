"""Node 6 child-local unified four-module AST, import/export, forbidden-surface, identity, package-root, and size guard.

Enforces the exact Node 6 module set (``crypto_btc_evidence_registry.py``, ``crypto_btc_evidence_catalog.py``,
``crypto_btc_evidence_resolution.py``, ``crypto_btc_evidence_policy.py``): per-module import allowlists (curated standard
library plus Node 6 siblings, with Node 2A ``team_evidence_aggregation_types`` allowed only for the policy module), both
import forms with alias/member handling, forbidden identifiers and calls, floats, ambient clock, randomness, ``hash()``,
broad except, ``!r``, exact ``__all__`` tuples with anywhere-binding rebinding protection, frozen/slotted/final hard-flagged
public dataclasses, no package-root exports, rejection of Node 3 identity surfaces (run/forecast ID minting, tea/tfr/tfe
versions, receipt lists) while the pinned Node 6 evaluator names stay allowed, and all Node 6 line ceilings. Real-module
assertions fail closed while the parallel workers' modules are still pending (expected red until they land).
"""
from __future__ import annotations

import ast
import dataclasses
import importlib
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIR = REPO_ROOT / "src" / "polymarket_alpha_lab"
TEST_DIR = REPO_ROOT / "tests"
PRODUCTION_LINE_LIMITS = {
    "crypto_btc_evidence_registry.py": 260, "crypto_btc_evidence_catalog.py": 360,
    "crypto_btc_evidence_resolution.py": 560, "crypto_btc_evidence_policy.py": 820,
}
PRODUCTION_TOTAL_LINE_LIMIT = 2_000
TEST_LINE_LIMITS = {
    "test_crypto_btc_evidence_registry.py": 450, "test_crypto_btc_evidence_catalog.py": 550,
    "test_crypto_btc_evidence_resolution.py": 850, "test_crypto_btc_evidence_policy.py": 1_150,
    "test_crypto_btc_evidence_scope.py": 650,
}
NODE_6_TEST_TOTAL_LINE_LIMIT = 3_600
STDLIB_IMPORT_ALLOWLIST = frozenset(("__future__", "collections", "dataclasses", "datetime", "decimal", "hashlib", "re", "typing"))
IMPORT_ALLOWLISTS = {
    "crypto_btc_evidence_registry": STDLIB_IMPORT_ALLOWLIST,
    "crypto_btc_evidence_catalog": STDLIB_IMPORT_ALLOWLIST | {"polymarket_alpha_lab.crypto_btc_evidence_registry"},
    "crypto_btc_evidence_resolution": STDLIB_IMPORT_ALLOWLIST | {
        "polymarket_alpha_lab.crypto_btc_evidence_registry", "polymarket_alpha_lab.crypto_btc_evidence_catalog"},
    "crypto_btc_evidence_policy": STDLIB_IMPORT_ALLOWLIST | {
        "polymarket_alpha_lab.crypto_btc_evidence_registry", "polymarket_alpha_lab.crypto_btc_evidence_catalog",
        "polymarket_alpha_lab.crypto_btc_evidence_resolution", "polymarket_alpha_lab.team_evidence_aggregation_types"},
}
PUBLIC_EXPORTS = {
    "crypto_btc_evidence_registry": (
        "CryptoBtcApprovedSource", "approved_crypto_btc_source_registry", "require_approved_crypto_btc_source"),
    "crypto_btc_evidence_catalog": (
        "CryptoBtcTrustedSourceRecord", "trusted_crypto_btc_source_catalog", "resolve_trusted_crypto_btc_source_record"),
    "crypto_btc_evidence_resolution": (
        "CryptoBtcResolutionContract", "CryptoBtcIncidentGates", "CryptoBtcResolutionAssessment",
        "check_crypto_btc_resolution_contract", "crypto_btc_resolution_contract_payload"),
    "crypto_btc_evidence_policy": (
        "CryptoBtcEvidenceInput", "CryptoBtcEvidenceEvaluation",
        "build_crypto_btc_evidence_policy_config", "evaluate_crypto_btc_evidence"),
}
PUBLIC_CLASS_EXPORTS = {
    "crypto_btc_evidence_registry": frozenset(("CryptoBtcApprovedSource",)),
    "crypto_btc_evidence_catalog": frozenset(("CryptoBtcTrustedSourceRecord",)),
    "crypto_btc_evidence_resolution": frozenset(("CryptoBtcResolutionContract", "CryptoBtcIncidentGates", "CryptoBtcResolutionAssessment")),
    "crypto_btc_evidence_policy": frozenset(("CryptoBtcEvidenceInput", "CryptoBtcEvidenceEvaluation")),
}
NODE_6_PUBLIC_NAMES = frozenset().union(*PUBLIC_EXPORTS.values())
NODE_6_MODULE_NAMES = frozenset(f"polymarket_alpha_lab.{name}" for name in IMPORT_ALLOWLISTS)
HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
FORBIDDEN_COMPONENTS = frozenset((
    "account", "accounts", "aiohttp", "api", "argparse", "argv", "auth", "authenticate", "authentication", "browser",
    "cache", "caches", "cached", "cancel", "cli", "client", "click", "credential", "credentials", "csv", "cursor",
    "db", "database", "duckdb", "environ", "execute", "execution", "exchange", "external", "file", "files", "filename",
    "filepath", "fork", "getenv", "getopt", "http", "https", "importlib", "jsonl", "log", "logs", "logger", "logging",
    "migration", "migrate", "mkdir", "mkdtemp", "mkstemp", "mongo", "mongodb", "mutate", "mutation", "mysql", "os",
    "order", "orders", "password", "passwords", "pathlib", "persist", "persistence", "persistent", "popen", "postgres",
    "postgresql", "process", "processes", "psycopg", "putenv", "random", "randomize", "redis", "remove", "request",
    "requests", "scrape", "scraper", "scrapers", "scraping", "secret", "secrets", "seed", "selenium", "sign", "signing",
    "signature", "signatures", "socket", "sockets", "spawn", "sql", "sqlalchemy", "sqlite", "stdin", "stdout", "stderr",
    "store", "stores", "storage", "subprocess", "submit", "submission", "supabase", "system", "tempfile", "token",
    "tokens", "typer", "urllib", "wallet", "wallets", "websocket", "websockets",
))
FORBIDDEN_SEQUENCES = (
    ("live", "trading"), ("trading", "live"), ("private", "key"), ("hosted", "account"), ("read", "text"),
    ("read", "bytes"), ("write", "text"), ("write", "bytes"), ("exchange", "mutate"), ("exchange", "mutation"),
)
FORBIDDEN_BARE_CALLS = frozenset((
    "open", "print", "input", "eval", "exec", "compile", "__import__", "hash", "float", "repr", "random", "randint",
    "randrange", "choice", "choices", "shuffle", "sample", "uniform", "gauss", "seed", "getrandbits", "randbytes",
))
FORBIDDEN_CALL_TERMINALS = frozenset((
    "now", "utcnow", "today", "timestamp", "total_seconds", "time", "time_ns", "monotonic", "monotonic_ns",
    "perf_counter", "perf_counter_ns", "clock", "gmtime", "localtime", "ctime", "asctime",
))
IDENTITY_COMPONENTS = frozenset(("decode", "decoder", "forecast", "legacy", "packet", "provenance", "receipt", "receipts", "replay"))
IDENTITY_SEQUENCES = (
    ("legacy", "projection"), ("forecast", "packet"), ("run", "id"), ("run", "digest"), ("forecast", "id"),
    ("forecast", "digest"), ("evidence", "id"), ("evidence", "digest"),
)
IDENTITY_STRING_TOKENS = ("tea:v1", "tfr:v1", "tfe:v1", "run_id", "forecast_id", "evidence_id", "packet", "legacy", "decoder", "replay")


def _components(identifier: str) -> tuple[str, ...]:
    parts: list[str] = []
    for chunk in identifier.split("_"):
        parts.extend(word.lower() for word in re.findall(r"[A-Z]+(?![a-z0-9])|[A-Z][a-z0-9]*|[a-z0-9]+", chunk))
    return tuple(part for part in parts if part)


def _semantic_identifiers(tree: ast.Module) -> list[tuple[int, str]]:
    """Collect identifiers from every plan-enumerated position, including attribute and import-member names."""
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if isinstance(node, ast.ImportFrom): found.append((node.lineno, alias.name))
                if alias.asname is not None: found.append((node.lineno, alias.asname))
        elif isinstance(node, ast.Attribute): found.append((node.lineno, node.attr))
        elif isinstance(node, ast.Name): found.append((node.lineno, node.id))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): found.append((node.lineno, node.name))
        elif isinstance(node, ast.arg): found.append((node.lineno, node.arg))
        elif isinstance(node, ast.keyword) and node.arg is not None: found.append((node.lineno, node.arg))
        elif isinstance(node, ast.ExceptHandler) and node.name is not None: found.append((node.lineno, node.name))
        elif isinstance(node, (ast.Global, ast.Nonlocal)): found.extend((node.lineno, entry) for entry in node.names)
    return found


def _identifier_violations(tree: ast.Module, singles: frozenset[str], sequences: tuple[tuple[str, ...], ...]) -> list[str]:
    violations: list[str] = []
    for lineno, identifier in _semantic_identifiers(tree):
        parts = _components(identifier)
        hits = [part for part in parts if part in singles]
        hits.extend("-".join(s) for s in sequences for i in range(len(parts) - len(s) + 1) if parts[i:i + len(s)] == s)
        if hits:
            violations.append(f"line {lineno}: forbidden identifier '{identifier}' ({', '.join(hits)})")
    return violations


def _import_violations(tree: ast.Module, allowlist: frozenset[str]) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            violations.extend(f"line {node.lineno}: module '{a.name}' is not in the Node 6 allowlist" for a in node.names if a.name not in allowlist)
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module: violations.append(f"line {node.lineno}: relative or empty-module import")
            elif node.module not in allowlist: violations.append(f"line {node.lineno}: module '{node.module}' is not in the Node 6 allowlist")
            violations.extend(f"line {node.lineno}: wildcard import" for a in node.names if a.name == "*")
    return violations


def _call_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            terminal = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if isinstance(func, ast.Name) and func.id in FORBIDDEN_BARE_CALLS: violations.append(f"line {func.lineno}: forbidden call '{func.id}()'")
            if terminal in FORBIDDEN_CALL_TERMINALS: violations.append(f"line {func.lineno}: forbidden ambient-clock call '{terminal}()'")
    return violations


def _callback_violations(tree: ast.Module) -> list[str]:
    """Reject callback invocation of an input, including closures; ``type[...]`` params are constructors, nested defs'
    decorators/defaults/annotations use enclosing params, and bodies use the shadow-merge rule."""
    violations: list[str] = []

    def visit(node: ast.AST, params: frozenset[str]) -> None:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in params:
            violations.append(f"line {node.lineno}: callback invocation of input '{node.func.id}()'")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            arguments = node.args
            items = arguments.args + arguments.kwonlyargs + arguments.posonlyargs
            every = {item.arg for item in items}
            constructors = {item.arg for item in items if isinstance(item.annotation, ast.Subscript) and isinstance(item.annotation.value, ast.Name) and item.annotation.value.id == "type"}
            if arguments.vararg is not None: every.add(arguments.vararg.arg)
            if arguments.kwarg is not None: every.add(arguments.kwarg.arg)
            for expression in [item.annotation for item in items if item.annotation is not None] + [a for a in (getattr(node, "returns", None), arguments.vararg and arguments.vararg.annotation, arguments.kwarg and arguments.kwarg.annotation) if a is not None] + list(getattr(node, "decorator_list", ())) + list(arguments.defaults) + [d for d in arguments.kw_defaults if d is not None]:
                visit(expression, params)
            for statement in (node.body if isinstance(node.body, list) else [node.body]):
                visit(statement, (params - every) | (every - constructors))
            return
        for child in ast.iter_child_nodes(node):
            visit(child, params)

    visit(tree, frozenset())
    return violations


def _surface_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if type(node.value) is float: violations.append(f"line {node.lineno}: float literal")
        elif isinstance(node, ast.Name) and node.id == "float": violations.append(f"line {node.lineno}: float annotation, call, or reference")
        elif isinstance(node, ast.ExceptHandler) and node.type is not None and {item.id for item in ast.walk(node.type) if isinstance(item, ast.Name)} & {"Exception", "BaseException"}:
            violations.append(f"line {node.lineno}: broad except handler")
        elif isinstance(node, ast.FormattedValue) and node.conversion == ord("r"): violations.append(f"line {node.lineno}: object repr conversion in payload or error")
    return violations


def _export_violations(tree: ast.Module, expected: tuple[str, ...], class_exports: frozenset[str]) -> list[str]:
    violations: list[str] = []
    assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)]
    if len(assignments) != 1:
        return ["__all__ must be exactly one direct tuple assignment"]
    allowed = {id(t) for t in assignments[0].targets if isinstance(t, ast.Name) and t.id == "__all__"}
    for node in ast.walk(tree):
        if id(node) in allowed:
            continue
        names: set[str] = set()
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store): names.add(node.id)
        elif isinstance(node, ast.arg): names.add(node.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
                if isinstance(node, ast.ImportFrom): names.add(alias.name)
        if "__all__" in names or (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == "__all__"):
            violations.append("__all__ must be exactly one direct tuple assignment with no other binding anywhere")
        violations.extend(f"export '{name}' must not be satisfied or rebound by any binding anywhere" for name in sorted(names & set(expected)))
    if not isinstance(assignments[0].value, ast.Tuple) or not all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in assignments[0].value.elts):
        violations.append("__all__ must be one tuple of string constants")
    else:
        names = tuple(e.value for e in assignments[0].value.elts)
        if len(set(names)) != len(names):
            violations.append("__all__ contains duplicate names")
        if names != expected:
            violations.append(f"__all__ must equal the exact ordered export tuple; got {names!r}")
    for name in expected:
        want = ast.ClassDef if name in class_exports else ast.FunctionDef
        anywhere = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name]
        direct = [n for n in tree.body if n in anywhere]
        if len(anywhere) != 1 or not direct or type(direct[0]) is not want:
            violations.append(f"export '{name}' requires exactly one module-level {'class definition' if want is ast.ClassDef else 'direct function definition'}")
    return violations


def _package_root_bound_names(tree: ast.Module) -> set[str]:
    """Collect every name bound anywhere (including conditional or nested blocks) plus ``__all__`` entries."""
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store): bound.add(node.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])
                bound.add(alias.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): bound.add(node.name)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            bound.update(item.value for item in ast.walk(node.value) if isinstance(item, ast.Constant) and isinstance(item.value, str))
    return bound


def _module_violations(source: str, module: str, *, exports: bool = True, expected: tuple[str, ...] | None = None) -> list[str]:
    tree = ast.parse(source)
    violations = _import_violations(tree, IMPORT_ALLOWLISTS[module])
    violations += _identifier_violations(tree, FORBIDDEN_COMPONENTS, FORBIDDEN_SEQUENCES) + _call_violations(tree) + _callback_violations(tree) + _surface_violations(tree)
    if exports:
        names = PUBLIC_EXPORTS[module] if expected is None else expected
        violations += _export_violations(tree, names, frozenset(names) & PUBLIC_CLASS_EXPORTS.get(module, frozenset()))
    return violations


def _identity_violations(source: str) -> list[str]:
    tree = ast.parse(source)
    found = _identifier_violations(tree, IDENTITY_COMPONENTS, IDENTITY_SEQUENCES)
    found += [f"line {n.lineno}: forbidden outer-identity constant" for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and any(t in n.value.lower() for t in IDENTITY_STRING_TOKENS)]
    return found


_REGISTRY_IMPORTS = (
    "from __future__ import annotations\nimport dataclasses\nfrom dataclasses import dataclass\n"
    "from datetime import UTC, datetime\nfrom decimal import Context, Decimal\nimport hashlib\nimport re\n"
    "from typing import Final, final\n"
)
BENIGN_IMPORTS = {
    "crypto_btc_evidence_registry": _REGISTRY_IMPORTS,
    "crypto_btc_evidence_catalog": _REGISTRY_IMPORTS
    + "from polymarket_alpha_lab.crypto_btc_evidence_registry import CryptoBtcApprovedSource, require_approved_crypto_btc_source\n"
      "import polymarket_alpha_lab.crypto_btc_evidence_registry as approved_registry\n",
    "crypto_btc_evidence_resolution": _REGISTRY_IMPORTS
    + "from polymarket_alpha_lab.crypto_btc_evidence_catalog import CryptoBtcTrustedSourceRecord, resolve_trusted_crypto_btc_source_record\n"
      "import polymarket_alpha_lab.crypto_btc_evidence_catalog as trusted_catalog\n",
    "crypto_btc_evidence_policy": _REGISTRY_IMPORTS
    + "from polymarket_alpha_lab.crypto_btc_evidence_registry import require_approved_crypto_btc_source\n"
      "from polymarket_alpha_lab.crypto_btc_evidence_catalog import CryptoBtcTrustedSourceRecord, resolve_trusted_crypto_btc_source_record\n"
      "from polymarket_alpha_lab.crypto_btc_evidence_resolution import CryptoBtcIncidentGates, CryptoBtcResolutionAssessment, CryptoBtcResolutionContract, check_crypto_btc_resolution_contract\n"
      "from polymarket_alpha_lab.team_evidence_aggregation_types import TeamEvidenceAggregationConfig, TeamEvidenceAggregationInput, TeamEvidenceAggregationRecord, TeamEvidenceCurrentRevisionSelection, select_team_evidence_canonical_current_records, validate_team_evidence_aggregation_input_contract\n",
}
BENIGN_VARIANTS = (
    "from decimal import _private_context_member\nfrom decimal import Decimal as value_type\nimport decimal as fixed_point\n"
    'version_stamp = "crypto-btc-approved-registry-v0"\nsource_theme = "bitcoin-catalog"\n'
    'publish_floor = Decimal("0.020000")\npublish_ceiling = Decimal("0.980000")\n'
    'evaluation_stamp = "crypto-btc-evidence-policy-v0"\n'
    'resolution_source_family = "btc_resolution_rules"\n'
    "def outer(factory):\n    def inner(factory: type[object]):\n        return factory()\n    return inner\n"
)
IMPORT_FAIL_CASES = (
    ("unknown_project_module", "crypto_btc_evidence_policy", "from polymarket_alpha_lab.team_evidence_aggregation_unknown import helper\n"),
    ("node_2c_reducer_module", "crypto_btc_evidence_policy", "from polymarket_alpha_lab.team_evidence_aggregation import build_team_evidence_aggregation_result\n"),
    ("node_2a_types_outside_policy", "crypto_btc_evidence_catalog", "from polymarket_alpha_lab.team_evidence_aggregation_types import TeamEvidenceAggregationConfig\n"),
    ("node_2_codec_module", "crypto_btc_evidence_policy", "from polymarket_alpha_lab.team_evidence_aggregation_codec import team_evidence_aggregation_config_digest\n"),
    ("node_3_envelope_module", "crypto_btc_evidence_catalog", "import polymarket_alpha_lab.team_forecast_build_envelope\n"),
    ("packet_module", "crypto_btc_evidence_resolution", "from polymarket_alpha_lab.team_forecast_packet import TeamForecastPacket\n"),
    ("store_module", "crypto_btc_evidence_registry", "import polymarket_alpha_lab.team_forecast_store\n"),
    ("psycopg_module", "crypto_btc_evidence_catalog", "import polymarket_alpha_lab.autonomous_market_scorer_psycopg\n"),
    ("supabase_module", "crypto_btc_evidence_resolution", "import polymarket_alpha_lab.supabase_team_evidence_aggregation_config\n"),
    ("prefix_extension", "crypto_btc_evidence_catalog", "import polymarket_alpha_lab.crypto_btc_evidence_registry_extra\n"),
    ("sibling_wrong_direction", "crypto_btc_evidence_registry", "from polymarket_alpha_lab.crypto_btc_evidence_policy import evaluate_crypto_btc_evidence\n"),
    ("package_root_import", "crypto_btc_evidence_policy", "import polymarket_alpha_lab\n"),
    ("package_root_importfrom", "crypto_btc_evidence_resolution", "from polymarket_alpha_lab import CryptoBtcEvidenceInput\n"),
    ("relative_import", "crypto_btc_evidence_catalog", "from .crypto_btc_evidence_registry import CryptoBtcApprovedSource\n"),
    ("relative_empty_module", "crypto_btc_evidence_registry", "from . import dataclasses\n"),
    ("wildcard_import", "crypto_btc_evidence_policy", "from decimal import *\n"),
    ("unlisted_module", "crypto_btc_evidence_registry", "import os\n"),
    ("unlisted_stdlib", "crypto_btc_evidence_catalog", "import importlib\n"),
    ("unlisted_codec_stdlib", "crypto_btc_evidence_resolution", "import json\n"),
    ("process_module", "crypto_btc_evidence_resolution", "import subprocess\n"),
    ("forbidden_alias", "crypto_btc_evidence_policy", "import decimal as subprocess\n"),
    ("forbidden_member", "crypto_btc_evidence_registry", "from datetime import wallet\n"),
    ("forbidden_member_underscore", "crypto_btc_evidence_policy", "from typing import _private_wallet_helper\n"),
)
REJECT_SNIPPETS = (
    ("identifier_name", "value = wallet\n"), ("identifier_attribute", "value = record.private_wallet\n"),
    ("identifier_function", "def socket_reader():\n    return None\n"), ("identifier_async_function", "async def wallet_loader():\n    return None\n"),
    ("identifier_class", "class Wallet:\n    pass\n"), ("identifier_argument", "def load(wallet_id):\n    return wallet_id\n"),
    ("identifier_keyword", "compute(wallet_id=1)\n"), ("identifier_global", "global order_book\n"),
    ("identifier_nonlocal", "def outer():\n    def inner():\n        nonlocal order_book\n"),
    ("identifier_except_name", "try:\n    pass\nexcept ValueError as token_store:\n    pass\n"),
    ("identifier_import_asname", "import datetime as subprocess\n"), ("identifier_importfrom_member", "from datetime import credential_token\n"),
    ("identifier_environ", "value = os.environ\n"), ("identifier_persistence", "def persist_result():\n    return None\n"),
    ("call_open", 'descriptor = open("state.jsonl")\n'), ("call_print", 'print("message")\n'), ("call_input", "value = input()\n"),
    ("call_eval", 'value = eval("expression")\n'), ("call_exec", 'exec("statement")\n'), ("call_compile", 'value = compile("source", "source", "exec")\n'),
    ("call_dynamic_import", 'module = __import__("os")\n'), ("call_hash", "value = hash(record)\n"), ("call_random", "value = random()\n"),
    ("call_randint", "value = randint(0, 9)\n"), ("call_float", "value = float(record)\n"), ("call_repr", "text = repr(record)\n"),
    ("call_read_text", "value = handle.read_text()\n"), ("call_write_bytes", "value = handle.write_bytes(data)\n"),
    ("call_attribute_now", "value = datetime.now()\n"), ("call_module_alias_now", "import datetime as clock\nvalue = clock.now()\n"),
    ("call_member_alias_utcnow", "from datetime import datetime as clock\nvalue = clock.utcnow()\n"), ("call_terminal_today", "stamp = schedule.today()\n"),
    ("call_terminal_monotonic", "value = timer.monotonic()\n"), ("call_terminal_timestamp", "value = record.started_at.timestamp()\n"),
    ("call_terminal_total_seconds", "value = record.delta.total_seconds()\n"), ("call_terminal_time_ns", "value = timer.time_ns()\n"),
    ("surface_float_literal", "ratio = 0.5\n"), ("surface_float_scientific", "value = 1e-6\n"),
    ("surface_float_annotation", "ratio: float = 0\n"), ("surface_float_reference", "kind = float\n"),
    ("surface_broad_exception", "try:\n    pass\nexcept Exception:\n    pass\n"),
    ("surface_broad_base_exception", "try:\n    pass\nexcept BaseException as error:\n    pass\n"),
    ("surface_formatted_repr", 'text = f"{record!r}"\n'),
    ("surface_callback_from_input", "def apply(callback):\n    return callback()\n"),
    ("surface_callback_closure", "def outer(callback):\n    def inner():\n        return callback()\n    return inner\n"),
    ("callback_default_scope", "def outer(factory):\n    def inner(factory: type[object] = factory()):\n        return factory()\n    return inner\n"),
    ("callback_annotation_scope", "def outer(callback):\n    def inner(*values: callback(), **options: callback()) -> callback():\n        return None\n    return inner\n"),
)
FUTURE_IMPORT = "from __future__ import annotations\n"
OK_DEF = "def require_approved_crypto_btc_source(source_id: str) -> CryptoBtcApprovedSource:\n    return None\n"
OK_ALL = '__all__ = ("require_approved_crypto_btc_source",)\n'
SINGLE = ("require_approved_crypto_btc_source",)
PAIR_DEFS = "def alpha():\n    return None\n\n\ndef beta():\n    return None\n"


def _export_case(all_expr: str, extra: str = "", definition: str = OK_DEF) -> str:
    return FUTURE_IMPORT + all_expr + definition + extra


EXPORT_CASES = (
    ("clean", _export_case(OK_ALL), True, SINGLE),
    ("ordered_pair_pass", _export_case('__all__ = ("alpha", "beta")\n', PAIR_DEFS), True, ("alpha", "beta")),
    ("reordered_pair", _export_case('__all__ = ("beta", "alpha")\n', PAIR_DEFS), False, ("alpha", "beta")),
    ("list_not_tuple", _export_case('__all__ = ["require_approved_crypto_btc_source"]\n'), False, SINGLE),
    ("duplicate_entry", _export_case('__all__ = ("require_approved_crypto_btc_source", "require_approved_crypto_btc_source")\n'), False, SINGLE),
    ("extra_entry", _export_case('__all__ = ("require_approved_crypto_btc_source", "extra")\n'), False, SINGLE),
    ("missing_entry", _export_case("__all__ = ()\n"), False, SINGLE),
    ("non_string_element", _export_case("__all__ = (require_approved_crypto_btc_source,)\n"), False, SINGLE),
    ("second_assignment", _export_case(OK_ALL, OK_ALL), False, SINGLE),
    ("augmented_assignment", _export_case(OK_ALL, '__all__ += ("extra",)\n'), False, SINGLE),
    ("assignment_binding", _export_case(OK_ALL, "require_approved_crypto_btc_source = None\n"), False, SINGLE),
    ("conditional_rebind", _export_case(OK_ALL, "if True:\n    require_approved_crypto_btc_source = None\n"), False, SINGLE),
    ("conditional_all_rebind", _export_case(OK_ALL, 'if True:\n    __all__ = ("other",)\n'), False, SINGLE),
    ("chained_all_rebind", _export_case('__all__ = require_approved_crypto_btc_source = ("require_approved_crypto_btc_source",)\n'), False, SINGLE),
    ("unpacked_all_rebind", _export_case('__all__ = (__all__,) = ("require_approved_crypto_btc_source",)\n'), False, SINGLE),
    ("walrus_binding", _export_case(OK_ALL, "if (require_approved_crypto_btc_source := 1):\n    pass\n"), False, SINGLE),
    ("def_name_binding", _export_case(OK_ALL, "def __all__():\n    return None\n"), False, SINGLE),
    ("import_binding", _export_case("from datetime import require_approved_crypto_btc_source\n" + OK_ALL), False, SINGLE),
    ("nested_import_binding", _export_case(OK_ALL, "def wrapper():\n    from datetime import require_approved_crypto_btc_source\n"), False, SINGLE),
    ("nested_definition", _export_case(OK_ALL, "def wrapper():\n    def require_approved_crypto_btc_source():\n        return None\n    return wrapper\n"), False, SINGLE),
    ("async_kind", _export_case(OK_ALL, "async def require_approved_crypto_btc_source():\n    return None\n"), False, SINGLE),
    ("class_kind", _export_case(OK_ALL, "class require_approved_crypto_btc_source:\n    pass\n"), False, SINGLE),
)
_CLASS_FIELDS = {
    "CryptoBtcApprovedSource": "    source_id: str\n    source_family: str\n    trust_tier: str\n    registry_version: str\n",
    "CryptoBtcTrustedSourceRecord": "    source_id: str\n    record_id: str\n    record_digest: str\n    release_vintage: str\n    catalog_version: str\n    valid_from: datetime\n    valid_until: datetime\n",
    "CryptoBtcResolutionContract": "    condition_id: str\n    market_slug: str\n    event_template: str\n    question_text: str\n    rules_summary: str\n    close_time: datetime\n    resolution_record_id: str\n    resolution_record_digest: str\n    contract_version: str\n",
    "CryptoBtcIncidentGates": "    source_outage: bool\n    index_dislocation: bool\n    chain_reorg: bool\n    resolution_rule_change: bool\n    market_halt: bool\n    derivatives_feed_degraded: bool\n",
    "CryptoBtcResolutionAssessment": "    gate_status: str\n    reason_codes: tuple[str, ...]\n",
    "CryptoBtcEvidenceInput": "    source_id: str\n    record_id: str\n    record_digest: str\n    evidence_record: TeamEvidenceAggregationRecord\n    selected_current: bool\n",
    "CryptoBtcEvidenceEvaluation": "    canonical_records: tuple[TeamEvidenceAggregationRecord, ...]\n    current_selections: tuple[TeamEvidenceCurrentRevisionSelection, ...]\n    aggregation_config: TeamEvidenceAggregationConfig\n    resolution_assessment: CryptoBtcResolutionAssessment\n    policy_gate_status: str\n    reason_codes: tuple[str, ...]\n",
}
_FUNCTION_SIGNATURES = {
    "approved_crypto_btc_source_registry": "() -> tuple[CryptoBtcApprovedSource, ...]",
    "require_approved_crypto_btc_source": "(source_id: str) -> CryptoBtcApprovedSource",
    "trusted_crypto_btc_source_catalog": "() -> tuple[CryptoBtcTrustedSourceRecord, ...]",
    "resolve_trusted_crypto_btc_source_record": "(source_id: str, record_id: str, record_digest: str, *, evaluated_at: datetime) -> CryptoBtcTrustedSourceRecord",
    "check_crypto_btc_resolution_contract": "(contract: CryptoBtcResolutionContract, *, gates: CryptoBtcIncidentGates, evaluated_at: datetime) -> CryptoBtcResolutionAssessment",
    "crypto_btc_resolution_contract_payload": "(contract: CryptoBtcResolutionContract) -> dict[str, object]",
    "build_crypto_btc_evidence_policy_config": "() -> TeamEvidenceAggregationConfig",
    "evaluate_crypto_btc_evidence": "(evidence_input: CryptoBtcEvidenceInput, *, resolution_contract: CryptoBtcResolutionContract, incident_gates: CryptoBtcIncidentGates, evaluated_at: datetime) -> CryptoBtcEvidenceEvaluation",
}


def _conforming_class(name: str) -> str:
    return f"@final\n@dataclass(frozen=True, slots=True)\nclass {name}:\n{_CLASS_FIELDS[name]}    paper_only: bool = True\n    report_only: bool = True\n    readonly: bool = True\n"


def _conforming_module(module: str) -> str:
    body = [BENIGN_IMPORTS[module], BENIGN_VARIANTS]
    for name in PUBLIC_EXPORTS[module]:
        body.append(_conforming_class(name) if name in PUBLIC_CLASS_EXPORTS[module] else f"def {name}{_FUNCTION_SIGNATURES[name]}:\n    return None\n")
    body.append("__all__ = (\n" + "".join(f'    "{name}",\n' for name in PUBLIC_EXPORTS[module]) + ")\n")
    return "".join(body)


def _class_def_problems(node: ast.ClassDef) -> list[str]:
    problems: list[str] = []
    if not any(isinstance(decorator, ast.Name) and decorator.id == "final" for decorator in node.decorator_list): problems.append("missing the @final decorator")
    calls = [d for d in node.decorator_list if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass"]
    keywords = {k.arg: k.value for call in calls for k in call.keywords}
    if len(calls) != 1 or set(keywords) != {"frozen", "slots"} or not all(isinstance(v, ast.Constant) and v.value is True for v in keywords.values()): problems.append("missing @dataclass(frozen=True, slots=True)")
    statements = {s.target.id: s for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)}
    for flag in HARD_FLAG_NAMES:
        statement = statements.get(flag)
        if statement is None or not (isinstance(statement.annotation, ast.Name) and statement.annotation.id == "bool") or not (isinstance(statement.value, ast.Constant) and statement.value.value is True): problems.append(f"{flag} must be 'bool' with a literal True default")
    return problems


_SAMPLE_CLASS = (
    "@final\n@dataclass(frozen=True, slots=True)\nclass Sample:\n"
    "    paper_only: bool = True\n    report_only: bool = True\n    readonly: bool = True\n"
)
CLASS_SHAPE_CASES = (
    ("clean", _SAMPLE_CLASS, True), ("missing_final", _SAMPLE_CLASS.replace("@final\n", ""), False),
    ("missing_dataclass", _SAMPLE_CLASS.replace("@dataclass(frozen=True, slots=True)\n", ""), False),
    ("missing_slots", _SAMPLE_CLASS.replace("@dataclass(frozen=True, slots=True)", "@dataclass(frozen=True)"), False),
    ("nonliteral_decorator_flag", _SAMPLE_CLASS.replace("frozen=True", 'frozen="True"'), False),
    ("extra_decorator_keyword", _SAMPLE_CLASS.replace("slots=True)", "slots=True, kw_only=True)"), False),
    ("flag_false", _SAMPLE_CLASS.replace("readonly: bool = True", "readonly: bool = False"), False),
    ("flag_missing", _SAMPLE_CLASS.replace("    readonly: bool = True\n", ""), False),
    ("flag_wrong_annotation", _SAMPLE_CLASS.replace("paper_only: bool", "paper_only: object"), False),
    ("flag_no_default", _SAMPLE_CLASS.replace("paper_only: bool = True", "paper_only: bool"), False),
)
PACKAGE_ROOT_CLEAN_CASE = "import decimal\nif True:\n    value = 1\n__all__ = (\"MarketScore\",)\n"
# ``CryptoBtcEvidenceInput`` is also a legacy ``crypto_btc_team`` class that the package root has exported since
# before Node 6; that pre-existing binding is not a Node 6 export, so only Node 6-owned bindings of it are forbidden.
LEGACY_COLLIDING_ROOT_NAMES = frozenset(("CryptoBtcEvidenceInput",))
PACKAGE_ROOT_REJECT_CASES = (
    ("conditional_import", "if True:\n    from polymarket_alpha_lab.crypto_btc_evidence_policy import evaluate_crypto_btc_evidence\n"),
    ("nested_import", "def helper():\n    from polymarket_alpha_lab.crypto_btc_evidence_registry import require_approved_crypto_btc_source\n"),
    ("module_import", "import polymarket_alpha_lab.crypto_btc_evidence_resolution\n"),
    ("colliding_name_from_node6_module", "from polymarket_alpha_lab.crypto_btc_evidence_policy import CryptoBtcEvidenceInput\n"),
    ("conditional_assign", "if True:\n    evaluate_crypto_btc_evidence = None\n"), ("package_all_listing", '__all__ = ("CryptoBtcEvidenceEvaluation",)\n'),
)


def _package_root_node6_module_imports(tree: ast.Module) -> list[str]:
    """List every import statement in the package root that draws from a Node 6 production module."""
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(f"line {node.lineno}: import '{a.name}' draws from a Node 6 module" for a in node.names if a.name in NODE_6_MODULE_NAMES)
        elif isinstance(node, ast.ImportFrom) and node.module in NODE_6_MODULE_NAMES:
            found.append(f"line {node.lineno}: import from '{node.module}' draws from a Node 6 module")
    return found
IDENTITY_ALLOW_CASES = (
    ("evaluation_class_allowed", "class CryptoBtcEvidenceEvaluation:\n    pass\n"),
    ("evaluate_function_allowed", "def evaluate_crypto_btc_evidence(*, config: object) -> None:\n    return None\n"),
    ("evaluator_component_allowed", "value = evaluator\n"),
    ("evaluation_attribute_allowed", "value = record.evidence_evaluation\n"),
    ("btc_version_string_allowed", 'version = "crypto-btc-evidence-policy-v0"\n'),
)
IDENTITY_FAIL_CASES = (
    ("run_identity", 'run_id = "r-1"\n'), ("forecast_id_attribute", "def probe(record):\n    return record.forecast_id\n"),
    ("evidence_id_field", "def probe(record):\n    return record.evidence_id\n"), ("run_digest_field", "run_digest = 1\n"),
    ("tea_mint", 'schema_version = "tea:v1"\n'), ("tfe_mint", 'preflight = "tfe:v1"\n'), ("tfr_mint", 'receipt_preimage = "tfr:v1"\n'),
    ("packet_builder", "def build_forecast_packet():\n    return None\n"),
    ("receipt_list", "evaluator_receipts = ()\n"),
    ("legacy_replay", "legacy_replay = 1\n"), ("decoder_helper", "def _decode_core():\n    return None\n"),
    ("provenance_note", "provenance_note = 1\n"),
)


def test_node_6_exact_nine_path_module_set_is_present() -> None:
    violations: list[str] = []
    found_production = {path.name for path in PRODUCTION_DIR.glob("crypto_btc_evidence_*.py")}
    for name in sorted(PRODUCTION_LINE_LIMITS):
        if name not in found_production: violations.append(f"{name}: required Node 6 production module is missing (pending-red until the parallel worker lands)")
    for extra in sorted(found_production - set(PRODUCTION_LINE_LIMITS)):
        violations.append(f"{extra}: fifth crypto_btc_evidence_* production module is not in the exact nine-path allowlist")
    found_tests = {path.name for path in TEST_DIR.glob("test_crypto_btc_evidence_*.py")}
    for name in sorted(TEST_LINE_LIMITS):
        if name not in found_tests: violations.append(f"{name}: required Node 6 test module is missing (pending-red until the parallel worker lands)")
    for extra in sorted(found_tests - set(TEST_LINE_LIMITS)):
        violations.append(f"{extra}: sixth test_crypto_btc_evidence_* test module is not in the exact nine-path allowlist")
    assert not violations, "\n".join(violations)


def test_node_6_unified_ast_import_export_forbidden_surface_and_line_size_gate() -> None:
    failures: list[str] = []
    for module in IMPORT_ALLOWLISTS:
        for label, source in (("imports", BENIGN_IMPORTS[module]), ("variants", BENIGN_VARIANTS)):
            found = _module_violations(source, module, exports=False)
            if found: failures.append(f"benign {label} for {module} were rejected: {found}")
        found = _module_violations(_conforming_module(module), module)
        if found: failures.append(f"conforming synthetic module {module} was rejected: {found}")
    for case, module, snippet in IMPORT_FAIL_CASES:
        if not _module_violations(snippet, module, exports=False): failures.append(f"import case '{case}' was not rejected")
    for case, snippet in REJECT_SNIPPETS:
        if not _module_violations(snippet, "crypto_btc_evidence_resolution", exports=False): failures.append(f"snippets case '{case}' was not rejected")
    for case, source, must_pass, expected in EXPORT_CASES:
        found = _module_violations(source, "crypto_btc_evidence_registry", exports=True, expected=expected)
        if must_pass and found: failures.append(f"export case '{case}' was wrongly rejected: {found}")
        if not must_pass and not found: failures.append(f"export case '{case}' was not rejected")
    violations: list[str] = []
    production_counts: dict[str, int] = {}
    for module, ceiling in PRODUCTION_LINE_LIMITS.items():
        path = PRODUCTION_DIR / module
        if not path.is_file():
            violations.append(f"{module}: required Node 6 production module is missing (pending-red until the parallel worker lands)")
            continue
        source = path.read_text(encoding="utf-8")
        count = len(source.splitlines())
        production_counts[module] = count
        if count > ceiling: violations.append(f"{module}: {count} physical lines exceed ceiling {ceiling}")
        violations.extend(f"{module}: {item}" for item in _module_violations(source, module.removesuffix(".py")))
    if len(production_counts) == len(PRODUCTION_LINE_LIMITS) and sum(production_counts.values()) > PRODUCTION_TOTAL_LINE_LIMIT:
        violations.append(f"Node 6 production total {sum(production_counts.values())} exceeds {PRODUCTION_TOTAL_LINE_LIMIT} lines")
    test_counts: dict[str, int] = {}
    for name, ceiling in TEST_LINE_LIMITS.items():
        path = TEST_DIR / name
        if not path.is_file():
            violations.append(f"{name}: required Node 6 test module is missing (pending-red until the parallel worker lands)")
            continue
        count = len(path.read_text(encoding="utf-8").splitlines())
        test_counts[name] = count
        if count > ceiling: violations.append(f"{name}: {count} physical lines exceed ceiling {ceiling}")
    if len(test_counts) == len(TEST_LINE_LIMITS) and sum(test_counts.values()) > NODE_6_TEST_TOTAL_LINE_LIMIT:
        violations.append(f"Node 6 test total {sum(test_counts.values())} exceeds {NODE_6_TEST_TOTAL_LINE_LIMIT} lines")
    assert not failures, "synthetic guard failures:\n" + "\n".join(failures)
    assert not violations, "\n".join(violations)


def test_node_6_public_dataclasses_are_frozen_slotted_final_and_hard_flagged() -> None:
    failures: list[str] = []
    for label, source, must_pass in CLASS_SHAPE_CASES:
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef))
        problems = _class_def_problems(node)
        if must_pass and problems: failures.append(f"class-shape case '{label}' was wrongly rejected: {problems}")
        if not must_pass and not problems: failures.append(f"class-shape case '{label}' was not rejected")
    for module in sorted(IMPORT_ALLOWLISTS):
        found = _module_violations(_conforming_module(module), module)
        failures.extend(f"conforming synthetic module {module} was rejected: {item}" for item in found)
    assert not failures, "synthetic class-shape guard failures:\n" + "\n".join(failures)
    problems: list[str] = []
    for module in sorted(IMPORT_ALLOWLISTS):
        path = PRODUCTION_DIR / f"{module}.py"
        if not path.is_file():
            problems.append(f"{module}.py: required Node 6 production module is missing (pending-red until the parallel worker lands)")
            continue
        classes = {n.name: n for n in ast.parse(path.read_text(encoding="utf-8")).body if isinstance(n, ast.ClassDef)}
        for name in sorted(PUBLIC_CLASS_EXPORTS[module]):
            node = classes.get(name)
            if node is None:
                problems.append(f"{module}.{name} is not a direct class definition")
                continue
            problems.extend(f"{module}.{name}: {item}" for item in _class_def_problems(node))
    assert not problems, "\n".join(problems)
    for module in sorted(IMPORT_ALLOWLISTS):
        loaded = importlib.import_module(f"polymarket_alpha_lab.{module}")
        for name in sorted(PUBLIC_CLASS_EXPORTS[module]):
            public_class = getattr(loaded, name)
            assert getattr(public_class, "__final__", False) is True, f"{module}.{name}"
            assert public_class.__dataclass_params__.frozen is True, f"{module}.{name}"
            assert public_class.__dataclass_params__.slots is True, f"{module}.{name}"
            defaults = {field.name: field.default for field in dataclasses.fields(public_class) if field.name in HARD_FLAG_NAMES}
            assert defaults == dict.fromkeys(HARD_FLAG_NAMES, True), f"{module}.{name}"
            with pytest.raises(TypeError):
                type("ForbiddenSubclass", (public_class,), {})


def test_node_6_package_root_has_no_node_6_exports() -> None:
    forbidden = (NODE_6_PUBLIC_NAMES - LEGACY_COLLIDING_ROOT_NAMES) | NODE_6_MODULE_NAMES
    tree = ast.parse((PRODUCTION_DIR / "__init__.py").read_text(encoding="utf-8"))
    bound = _package_root_bound_names(tree)
    problems = sorted(bound & forbidden) + _package_root_node6_module_imports(tree)
    assert not problems, problems
    assert not (_package_root_bound_names(ast.parse(PACKAGE_ROOT_CLEAN_CASE)) & forbidden), "clean package-root synthetic was rejected"
    for case, snippet in PACKAGE_ROOT_REJECT_CASES:
        parsed = ast.parse(snippet)
        overlap = (_package_root_bound_names(parsed) & forbidden) or _package_root_node6_module_imports(parsed)
        assert overlap, f"package-root case '{case}' was not rejected"


def test_node_6_has_no_outer_identity_surface_with_evaluator_allowance() -> None:
    failures: list[str] = []
    for module in sorted(IMPORT_ALLOWLISTS):
        found = _identity_violations(_conforming_module(module))
        if found: failures.append(f"conforming synthetic module {module} was wrongly rejected by the identity rules: {found}")
    for case, snippet in IDENTITY_ALLOW_CASES:
        if _identity_violations(snippet): failures.append(f"identity allowance case '{case}' was wrongly rejected")
    for case, snippet in IDENTITY_FAIL_CASES:
        if not _identity_violations(snippet): failures.append(f"identity case '{case}' was not rejected")
    violations: list[str] = []
    for module in sorted(IMPORT_ALLOWLISTS):
        path = PRODUCTION_DIR / f"{module}.py"
        if not path.is_file():
            violations.append(f"{module}: required Node 6 production module is missing (pending-red until the parallel worker lands)")
            continue
        violations.extend(f"{module}: {item}" for item in _identity_violations(path.read_text(encoding="utf-8")))
    assert not failures, "synthetic identity guard failures:\n" + "\n".join(failures)
    assert not violations, "\n".join(violations)
