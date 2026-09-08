"""Node 3 child-local AST, import/export, forbidden-surface, V1-leak, package-root, and line-size guard.

Enforces the single new production module ``team_forecast_build_envelope.py``: an exact import allowlist (standard library plus
exactly the fixed Node 2 modules and the pure ``team_forecast_packet`` predecessor), both import forms with alias/member handling,
forbidden identifiers and calls, floats, ambient clock, randomness, ``hash()``, no V1 keys in legacy payload construction, the exact
ordered 12-name ``__all__`` tuple with anywhere-binding rebinding protection, frozen/slotted/final hard-flagged public dataclasses,
no package-root exports, and the Node 3 ceilings.
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
PRODUCTION_FILE = "team_forecast_build_envelope.py"
PRODUCTION_MODULE = "polymarket_alpha_lab.team_forecast_build_envelope"
PRODUCTION_LINE_LIMIT = 900
TEST_LINE_LIMITS = {"test_team_forecast_build_envelope.py": 1100, "test_team_forecast_build_envelope_scope.py": 500}
NODE_3_TEST_TOTAL_LINE_LIMIT = 1_600
IMPORT_ALLOWLIST = frozenset((
    "__future__", "collections", "dataclasses", "datetime", "decimal", "hashlib", "json", "re", "typing",
    "polymarket_alpha_lab.team_evidence_aggregation", "polymarket_alpha_lab.team_evidence_aggregation_types",
    "polymarket_alpha_lab.team_evidence_aggregation_codec", "polymarket_alpha_lab.team_forecast_packet",
))
NODE_3_PUBLIC_EXPORTS = (
    "TeamForecastEvaluationScope", "TeamForecastRunMetadata", "TeamForecastEvaluatorReceipt",
    "TeamForecastEvidenceReplayRecord", "TeamForecastBuildEnvelope", "build_team_forecast_build_envelope",
    "validate_team_forecast_build_envelope", "team_forecast_evaluation_scope_payload",
    "team_evidence_aggregation_id", "team_forecast_run_id", "team_forecast_evidence_id",
    "team_forecast_legacy_payload_sha256",
)
NODE_3_CLASS_EXPORTS = frozenset(NODE_3_PUBLIC_EXPORTS[:5])
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
V1_KEY_MARKERS = ("tea_id", "tfr_id", "tfe_id", "tea:v1", "tfr:v1", "tfe:v1", "v1_id")
LEGACY_CONTEXT_COMPONENTS = frozenset(("legacy", "packet"))


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


def _identifier_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for lineno, identifier in _semantic_identifiers(tree):
        parts = _components(identifier)
        hits = [part for part in parts if part in FORBIDDEN_COMPONENTS]
        hits.extend("-".join(s) for s in FORBIDDEN_SEQUENCES for i in range(len(parts) - len(s) + 1) if parts[i:i + len(s)] == s)
        if hits:
            violations.append(f"line {lineno}: forbidden identifier '{identifier}' ({', '.join(hits)})")
    return violations


def _import_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            violations.extend(f"line {node.lineno}: module '{a.name}' is not in the Node 3 allowlist" for a in node.names if a.name not in IMPORT_ALLOWLIST)
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module: violations.append(f"line {node.lineno}: relative or empty-module import")
            elif node.module not in IMPORT_ALLOWLIST: violations.append(f"line {node.lineno}: module '{node.module}' is not in the Node 3 allowlist")
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


def _surface_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if type(node.value) is float: violations.append(f"line {node.lineno}: float literal")
            elif isinstance(node.value, str) and ("btc" in node.value.lower() or "bitcoin" in node.value.lower()): violations.append(f"line {node.lineno}: embedded btc or bitcoin constant")
        elif isinstance(node, ast.Name) and node.id == "float": violations.append(f"line {node.lineno}: float annotation, call, or reference")
        elif isinstance(node, ast.ExceptHandler) and node.type is not None and {item.id for item in ast.walk(node.type) if isinstance(item, ast.Name)} & {"Exception", "BaseException"}:
            violations.append(f"line {node.lineno}: broad except handler")
        elif isinstance(node, ast.FormattedValue) and node.conversion == ord("r"): violations.append(f"line {node.lineno}: object repr conversion in payload or error")
    return violations


def _is_legacy_context(identifier: str) -> bool:
    return bool(LEGACY_CONTEXT_COMPONENTS & set(_components(identifier)))


def _is_v1_key(text: str) -> bool:
    lowered = text.lower()
    return lowered == "v1" or any(marker in lowered for marker in V1_KEY_MARKERS)


def _v1_marker_keys(dictionary: ast.Dict) -> list[str]:
    return [key.value for key in dictionary.keys if isinstance(key, ast.Constant) and isinstance(key.value, str) and _is_v1_key(key.value)]


def _references_legacy_context(node: ast.AST) -> bool:
    return any(isinstance(item, ast.Name) and _is_legacy_context(item.id) for item in ast.walk(node))


def _legacy_leak_violations(tree: ast.Module) -> list[str]:
    """Reject V1 keys entering legacy payload construction plus legacy payload mutation or encoding drift."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.ctx, (ast.Store, ast.Del)):
            base = node.value
            label = base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else ""
            if _is_legacy_context(label):
                violations.append(f"line {node.lineno}: legacy payload '{label}' must never be mutated, extended, or deleted by subscript")
        elif isinstance(node, ast.Dict):
            markers = _v1_marker_keys(node)
            spread = any(key is None and isinstance(value, ast.Name) and _is_legacy_context(value.id) for key, value in zip(node.keys, node.values))
            if markers and spread:
                violations.append(f"line {node.lineno}: V1 key(s) {markers} merged into a legacy payload spread")
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr) and any(_v1_marker_keys(side) for side in (node.left, node.right) if isinstance(side, ast.Dict)) and _references_legacy_context(node):
            violations.append(f"line {node.lineno}: V1 key(s) merged into a legacy payload via '|'")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "dict":
                if any(isinstance(a, ast.Name) and _is_legacy_context(a.id) for a in node.args) and any(k.arg is not None and _is_v1_key(k.arg) for k in node.keywords):
                    violations.append(f"line {node.lineno}: V1 keyword(s) merged into a legacy payload via dict()")
            elif isinstance(func, ast.Attribute):
                base = func.value
                label = base.id if isinstance(base, ast.Name) else base.attr if isinstance(base, ast.Attribute) else ""
                if func.attr in ("update", "setdefault", "pop", "popitem", "clear") and _is_legacy_context(label):
                    violations.append(f"line {node.lineno}: legacy payload '{label}' must never be mutated via '{func.attr}'")
                if func.attr == "dumps" and any(k.arg == "ensure_ascii" for k in node.keywords) and _references_legacy_context(node):
                    violations.append(f"line {node.lineno}: legacy payload encoding must not add ensure_ascii or wrappers")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(node.value, ast.Dict):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and _is_legacy_context(t.id) and _v1_marker_keys(node.value) for t in targets):
                violations.append(f"line {node.lineno}: V1 key(s) {_v1_marker_keys(node.value)} assigned into a legacy-named payload")
    return violations


def _export_violations(tree: ast.Module, expected: tuple[str, ...]) -> list[str]:
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
        want = ast.ClassDef if name in NODE_3_CLASS_EXPORTS else ast.FunctionDef
        anywhere = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name]
        direct = [n for n in tree.body if n in anywhere]
        if len(anywhere) != 1 or not direct or type(direct[0]) is not want:
            violations.append(f"export '{name}' requires exactly one module-level {'class definition' if want is ast.ClassDef else 'direct function definition'}")
    return violations


def _module_violations(source: str, *, exports: bool, expected: tuple[str, ...] = NODE_3_PUBLIC_EXPORTS) -> list[str]:
    tree = ast.parse(source)
    violations = _import_violations(tree) + _identifier_violations(tree) + _call_violations(tree) + _surface_violations(tree) + _legacy_leak_violations(tree)
    return violations + (_export_violations(tree, expected) if exports else [])


BENIGN_IMPORTS = (
    "from __future__ import annotations\nimport dataclasses\nfrom dataclasses import dataclass\n"
    "from datetime import UTC, datetime\nfrom decimal import ROUND_HALF_EVEN, Context, Decimal\nimport hashlib\n"
    "import json\nfrom typing import Any, Final, final\n"
    "from polymarket_alpha_lab.team_evidence_aggregation import validate_team_evidence_aggregation_result\n"
    "from polymarket_alpha_lab.team_evidence_aggregation_types import TeamEvidenceAggregationConfig, TeamEvidenceAggregationInput, TeamEvidenceAggregationResult\n"
    "from polymarket_alpha_lab.team_evidence_aggregation_codec import team_evidence_aggregation_config_digest, team_evidence_aggregation_config_payload, team_evidence_aggregation_input_payload, team_evidence_aggregation_payload\n"
    "from polymarket_alpha_lab.team_forecast_packet import TeamForecastEvidencePacket, TeamForecastPacket, team_forecast_packet_payload\n"
)
BENIGN_VARIANTS = (
    "from decimal import _local_context\nfrom decimal import Decimal as value_type\nimport json as canonical_codec\n"
    'v1_preimage = {"tea_id": tea_id, "receipt": receipt_payload, "legacy_payload_sha256": legacy_sha256}\n'
    'run_preimage = {"tea_id": tea_id, "run_metadata": run_metadata_payload}\n'
)
IMPORT_FAIL_CASES = (
    ("unknown_project_module", "from polymarket_alpha_lab.team_evidence_aggregation_unknown import helper\n"),
    ("prefix_extension", "import polymarket_alpha_lab.team_evidence_aggregation_types_extra\n"),
    ("sibling_node2_module", "import polymarket_alpha_lab.team_evidence_aggregation_temporal\n"),
    ("package_root_import", "import polymarket_alpha_lab\n"), ("package_root_importfrom", "from polymarket_alpha_lab import TeamForecastPacket\n"),
    ("relative_import", "from .team_evidence_aggregation_types import TeamEvidenceCapture\n"),
    ("relative_empty_module", "from . import team_evidence_aggregation_types\n"), ("wildcard_import", "from decimal import *\n"),
    ("wildcard_future_import", "from __future__ import *\n"), ("unlisted_module", "import os\n"), ("unlisted_stdlib", "import importlib\n"),
    ("process_module", "import subprocess\n"), ("forbidden_alias", "import decimal as subprocess\n"),
    ("forbidden_member", "from datetime import wallet\n"), ("forbidden_member_underscore", "from typing import _private_wallet_helper\n"),
)
REJECT_SNIPPETS = (
    ("identifier_name", "value = wallet\n"), ("identifier_attribute", "value = record.private_wallet\n"),
    ("identifier_function", "def socket_reader():\n    return None\n"), ("identifier_async_function", "async def wallet_loader():\n    return None\n"),
    ("identifier_class", "class Wallet:\n    pass\n"), ("identifier_argument", "def load(wallet_id):\n    return wallet_id\n"),
    ("identifier_keyword", "compute(wallet_id=1)\n"), ("identifier_global", "global order_book\n"), ("identifier_nonlocal", "def outer():\n    def inner():\n        nonlocal order_book\n"),
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
    ("call_terminal_total_seconds", "value = record.delta.total_seconds()\n"), ("surface_float_literal", "ratio = 0.5\n"),
    ("surface_float_scientific", "value = 1e-6\n"), ("surface_float_annotation", "ratio: float = 0\n"), ("surface_float_reference", "kind = float\n"),
    ("surface_broad_exception", "try:\n    pass\nexcept Exception:\n    pass\n"),
    ("surface_broad_base_exception", "try:\n    pass\nexcept BaseException as error:\n    pass\n"),
    ("surface_formatted_repr", 'text = f"{record!r}"\n'), ("surface_btc_constant", 'theme = "btc"\n'),
    ("v1_subscript_store", 'legacy_payload["tea_id"] = envelope_id\n'), ("v1_subscript_store_packet", 'evidence_packet_payload["tfe_id"] = replay_id\n'),
    ("v1_update", 'legacy_payload.update({"tea_id": value})\n'), ("v1_setdefault", 'legacy_payload.setdefault("tfr_id", value)\n'),
    ("v1_spread_merge", 'merged = {**legacy_payload, "tea_id": value}\n'), ("v1_binop_merge", 'merged = {"tfr_id": value} | legacy_payload\n'),
    ("v1_dict_call", "extended = dict(legacy_payload, tea_id=value)\n"), ("v1_assign_literal", 'evidence_packet_payload = {"tfe_id": value, "source_id": 1}\n'),
    ("v1_subscript_delete", 'del legacy_payload["source_id"]\n'),
    ("legacy_dumps_drift", 'encoded = json.dumps(legacy_payload, allow_nan=False, separators=(",", ":"), sort_keys=True, ensure_ascii=True)\n'),
)
FUTURE_IMPORT = "from __future__ import annotations\n"
OK_DEF = "def team_forecast_evidence_id(*, scope: object) -> None:\n    return None\n"
OK_ALL = '__all__ = ("team_forecast_evidence_id",)\n'
SINGLE = ("team_forecast_evidence_id",)
PAIR_DEFS = "def alpha():\n    return None\n\n\ndef beta():\n    return None\n"


def _export_case(all_expr: str, extra: str = "", definition: str = OK_DEF) -> str:
    return FUTURE_IMPORT + all_expr + definition + extra


EXPORT_CASES = (
    ("clean", _export_case(OK_ALL), True, SINGLE),
    ("ordered_pair_pass", _export_case('__all__ = ("alpha", "beta")\n', PAIR_DEFS), True, ("alpha", "beta")),
    ("reordered_pair", _export_case('__all__ = ("beta", "alpha")\n', PAIR_DEFS), False, ("alpha", "beta")),
    ("list_not_tuple", _export_case('__all__ = ["team_forecast_evidence_id"]\n'), False, SINGLE),
    ("duplicate_entry", _export_case('__all__ = ("team_forecast_evidence_id", "team_forecast_evidence_id")\n'), False, SINGLE),
    ("extra_entry", _export_case('__all__ = ("team_forecast_evidence_id", "extra")\n'), False, SINGLE), ("missing_entry", _export_case("__all__ = ()\n"), False, SINGLE),
    ("non_string_element", _export_case("__all__ = (team_forecast_evidence_id,)\n"), False, SINGLE), ("second_assignment", _export_case(OK_ALL, OK_ALL), False, SINGLE),
    ("augmented_assignment", _export_case(OK_ALL, '__all__ += ("extra",)\n'), False, SINGLE), ("assignment_binding", _export_case(OK_ALL, "team_forecast_evidence_id = None\n"), False, SINGLE),
    ("conditional_rebind", _export_case(OK_ALL, "if True:\n    team_forecast_evidence_id = None\n"), False, SINGLE),
    ("conditional_all_rebind", _export_case(OK_ALL, 'if True:\n    __all__ = ("other",)\n'), False, SINGLE),
    ("chained_all_rebind", _export_case('__all__ = team_forecast_evidence_id = ("team_forecast_evidence_id",)\n'), False, SINGLE),
    ("unpacked_all_rebind", _export_case('__all__ = (__all__,) = ("team_forecast_evidence_id",)\n'), False, SINGLE),
    ("walrus_binding", _export_case(OK_ALL, "if (team_forecast_evidence_id := 1):\n    pass\n"), False, SINGLE),
    ("def_name_binding", _export_case(OK_ALL, "def __all__():\n    return None\n"), False, SINGLE),
    ("import_binding", _export_case("from datetime import team_forecast_evidence_id\n" + OK_ALL), False, SINGLE),
    ("nested_import_binding", _export_case(OK_ALL, "def wrapper():\n    from datetime import team_forecast_evidence_id\n"), False, SINGLE),
    ("nested_definition", _export_case(OK_ALL, "def wrapper():\n    def team_forecast_evidence_id():\n        return None\n    return wrapper\n"), False, SINGLE),
    ("async_kind", _export_case(OK_ALL, "async def team_forecast_evidence_id():\n    return None\n"), False, SINGLE),
    ("class_kind", _export_case(OK_ALL, "class team_forecast_evidence_id:\n    pass\n"), False, SINGLE),
)
_CONFORMING_CLASS = (
    "@final\n@dataclass(frozen=True, slots=True)\nclass {name}:\n"
    "    paper_only: bool = True\n    report_only: bool = True\n    readonly: bool = True\n"
)
_BUILDER_SIGNATURE = (
    "def build_team_forecast_build_envelope(result: TeamEvidenceAggregationResult, *, "
    "aggregation_input: TeamEvidenceAggregationInput, config: TeamEvidenceAggregationConfig, "
    "scope: TeamForecastEvaluationScope, run_metadata: TeamForecastRunMetadata, "
    "evaluator_receipts: tuple[TeamForecastEvaluatorReceipt, ...], "
    "legacy_forecast_packet: TeamForecastPacket | None, "
    "legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...]) -> TeamForecastBuildEnvelope:\n"
    "    return None\n"
)
_VALIDATOR_SIGNATURE = (
    "def validate_team_forecast_build_envelope(envelope: TeamForecastBuildEnvelope, *, "
    "result: TeamEvidenceAggregationResult, aggregation_input: TeamEvidenceAggregationInput, "
    "config: TeamEvidenceAggregationConfig, scope: TeamForecastEvaluationScope, "
    "run_metadata: TeamForecastRunMetadata, "
    "evaluator_receipts: tuple[TeamForecastEvaluatorReceipt, ...], "
    "legacy_forecast_packet: TeamForecastPacket | None, "
    "legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...]) -> None:\n"
    "    return None\n"
)
_FUNCTION_SIGNATURES = {
    "team_forecast_evaluation_scope_payload": "(scope: TeamForecastEvaluationScope) -> dict[str, object]",
    "team_evidence_aggregation_id": "(scope: TeamForecastEvaluationScope) -> str",
    "team_forecast_run_id": "(tea_id: str, run_metadata: TeamForecastRunMetadata) -> str",
    "team_forecast_evidence_id": "(tea_id: str, receipt: TeamForecastEvaluatorReceipt, legacy_payload_sha256: str) -> str",
    "team_forecast_legacy_payload_sha256": "(legacy_payload: dict[str, object]) -> str",
}


def _conforming_module() -> str:
    body = [BENIGN_IMPORTS, BENIGN_VARIANTS]
    for name in NODE_3_PUBLIC_EXPORTS:
        if name in NODE_3_CLASS_EXPORTS:
            body.append(_CONFORMING_CLASS.format(name=name))
        elif name == "build_team_forecast_build_envelope":
            body.append(_BUILDER_SIGNATURE)
        elif name == "validate_team_forecast_build_envelope":
            body.append(_VALIDATOR_SIGNATURE)
        else:
            body.append(f"def {name}{_FUNCTION_SIGNATURES[name]}:\n    return None\n")
    body.append("__all__ = (\n" + "".join(f'    "{name}",\n' for name in NODE_3_PUBLIC_EXPORTS) + ")\n")
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
PACKAGE_ROOT_REJECT_CASES = (
    ("conditional_import", "if True:\n    from polymarket_alpha_lab.team_forecast_build_envelope import TeamForecastBuildEnvelope\n"),
    ("nested_import", "def helper():\n    from polymarket_alpha_lab.team_forecast_build_envelope import team_forecast_run_id\n"),
    ("module_import", "import polymarket_alpha_lab.team_forecast_build_envelope\n"),
    ("conditional_assign", "if True:\n    team_forecast_legacy_payload_sha256 = None\n"), ("package_all_listing", '__all__ = ("TeamForecastEvaluationScope",)\n'),
)


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


def test_node_3_ast_import_export_forbidden_surface_and_line_size_gate() -> None:
    failures: list[str] = []
    for label, source in (("imports", BENIGN_IMPORTS), ("variants", BENIGN_VARIANTS)):
        found = _module_violations(source, exports=False)
        if found: failures.append(f"benign {label} were rejected: {found}")
    found = _module_violations(_conforming_module(), exports=True)
    if found: failures.append(f"conforming synthetic module was rejected: {found}")
    for case, snippet in IMPORT_FAIL_CASES:
        if not _module_violations(snippet, exports=False): failures.append(f"import case '{case}' was not rejected")
    for case, snippet in REJECT_SNIPPETS:
        if not _module_violations(snippet, exports=False): failures.append(f"snippets case '{case}' was not rejected")
    for case, source, must_pass, expected in EXPORT_CASES:
        found = _module_violations(source, exports=True, expected=expected)
        if must_pass and found: failures.append(f"export case '{case}' was wrongly rejected: {found}")
        if not must_pass and not found: failures.append(f"export case '{case}' was not rejected")
    violations: list[str] = []
    production_path = PRODUCTION_DIR / PRODUCTION_FILE
    if not production_path.is_file():
        violations.append(f"{PRODUCTION_FILE}: required Node 3 production module is missing (red until Worker A lands)")
    else:
        source = production_path.read_text(encoding="utf-8")
        count = len(source.splitlines())
        if count > PRODUCTION_LINE_LIMIT: violations.append(f"{PRODUCTION_FILE}: {count} physical lines exceed ceiling {PRODUCTION_LINE_LIMIT}")
        violations.extend(f"{PRODUCTION_FILE}: {item}" for item in _module_violations(source, exports=True))
    test_counts: dict[str, int] = {}
    for name, ceiling in TEST_LINE_LIMITS.items():
        path = TEST_DIR / name
        if not path.is_file():
            violations.append(f"{name}: required Node 3 test module is missing (behavior tests red until Worker B lands; scope file must exist)")
            continue
        count = len(path.read_text(encoding="utf-8").splitlines())
        test_counts[name] = count
        if count > ceiling: violations.append(f"{name}: {count} physical lines exceed ceiling {ceiling}")
    if len(test_counts) == len(TEST_LINE_LIMITS) and sum(test_counts.values()) > NODE_3_TEST_TOTAL_LINE_LIMIT:
        violations.append(f"Node 3 test total {sum(test_counts.values())} exceeds {NODE_3_TEST_TOTAL_LINE_LIMIT} lines")
    assert not failures, "synthetic guard failures:\n" + "\n".join(failures)
    assert not violations, "\n".join(violations)


def test_node_3_public_dataclasses_are_frozen_slotted_and_hard_flagged() -> None:
    failures: list[str] = []
    for label, source, must_pass in CLASS_SHAPE_CASES:
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef))
        problems = _class_def_problems(node)
        if must_pass and problems: failures.append(f"class-shape case '{label}' was wrongly rejected: {problems}")
        if not must_pass and not problems: failures.append(f"class-shape case '{label}' was not rejected")
    assert not failures, "synthetic class-shape guard failures:\n" + "\n".join(failures)
    path = PRODUCTION_DIR / PRODUCTION_FILE
    assert path.is_file(), f"{PRODUCTION_FILE}: required Node 3 production module is missing (red until Worker A lands)"
    classes = {n.name: n for n in ast.parse(path.read_text(encoding="utf-8")).body if isinstance(n, ast.ClassDef)}
    problems: list[str] = []
    for name in sorted(NODE_3_CLASS_EXPORTS):
        node = classes.get(name)
        if node is None:
            problems.append(f"{name} is not a direct class definition")
            continue
        problems.extend(f"{name}: {item}" for item in _class_def_problems(node))
    assert not problems, "\n".join(problems)
    module = importlib.import_module(PRODUCTION_MODULE)
    for name in sorted(NODE_3_CLASS_EXPORTS):
        public_class = getattr(module, name)
        assert getattr(public_class, "__final__", False) is True, name
        assert public_class.__dataclass_params__.frozen is True, name
        assert public_class.__dataclass_params__.slots is True, name
        defaults = {field.name: field.default for field in dataclasses.fields(public_class) if field.name in HARD_FLAG_NAMES}
        assert defaults == dict.fromkeys(HARD_FLAG_NAMES, True), name
        with pytest.raises(TypeError):
            type("ForbiddenSubclass", (public_class,), {})


def test_node_3_package_root_has_no_node_3_exports() -> None:
    forbidden = set(NODE_3_PUBLIC_EXPORTS) | {PRODUCTION_MODULE}
    tree = ast.parse((PRODUCTION_DIR / "__init__.py").read_text(encoding="utf-8"))
    bound = _package_root_bound_names(tree)
    assert not (bound & forbidden), sorted(bound & forbidden)
    assert not (_package_root_bound_names(ast.parse(PACKAGE_ROOT_CLEAN_CASE)) & forbidden), "clean package-root synthetic was rejected"
    for case, snippet in PACKAGE_ROOT_REJECT_CASES:
        overlap = _package_root_bound_names(ast.parse(snippet)) & forbidden
        assert overlap, f"package-root case '{case}' was not rejected"
