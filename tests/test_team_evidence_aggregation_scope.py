"""Node 2C child-local unified six-module AST, package-root, forbidden-surface, and size guard.
Enforces exact module allowlists, both import forms, alias/member handling, forbidden identifiers and calls, exact
``__all__`` tuples, dataclasses, fail-closed maxima, line ceilings, and no outer identity, packet, legacy, decoder,
or persistence surfaces across the six production modules and the package root.
"""
from __future__ import annotations

import ast
import re
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.team_evidence_aggregation_types as team_evidence_types
from polymarket_alpha_lab.team_evidence_aggregation_types import TeamEvidenceAggregationConfig, TeamEvidenceRequirement

REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIR = REPO_ROOT / "src" / "polymarket_alpha_lab"
TEST_DIR = REPO_ROOT / "tests"
PRODUCTION_LINE_LIMITS = {
    "team_evidence_aggregation_types.py": 900, "team_evidence_aggregation_codec.py": 500,
    "team_evidence_aggregation_temporal.py": 300, "team_evidence_aggregation_allocation.py": 450,
    "team_evidence_aggregation_witness.py": 650, "team_evidence_aggregation.py": 700,
}
TEST_LINE_LIMITS = {
    "test_team_evidence_aggregation_types.py": 900, "test_team_evidence_aggregation_codec.py": 600,
    "test_team_evidence_aggregation_temporal.py": 450, "test_team_evidence_aggregation_allocation.py": 600,
    "test_team_evidence_aggregation_witness.py": 900, "test_team_evidence_aggregation.py": 900,
    "test_team_evidence_aggregation_scope.py": 500,
}
PRODUCTION_TOTAL_LINE_LIMIT = 3_500
TEST_TOTAL_LINE_LIMIT = 4_850
IMPORT_ALLOWLISTS = {
    "team_evidence_aggregation_types": {"__future__", "collections", "dataclasses", "datetime", "decimal", "re", "typing"},
    "team_evidence_aggregation_codec": {"__future__", "dataclasses", "datetime", "decimal", "hashlib", "json", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types"},
    "team_evidence_aggregation_temporal": {"__future__", "datetime", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types"},
    "team_evidence_aggregation_allocation": {"__future__", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types"},
    "team_evidence_aggregation_witness": {"__future__", "collections", "datetime", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types", "polymarket_alpha_lab.team_evidence_aggregation_allocation"},
    "team_evidence_aggregation": {"__future__", "dataclasses", "decimal", "typing", "polymarket_alpha_lab.team_evidence_aggregation_types", "polymarket_alpha_lab.team_evidence_aggregation_codec", "polymarket_alpha_lab.team_evidence_aggregation_temporal", "polymarket_alpha_lab.team_evidence_aggregation_allocation", "polymarket_alpha_lab.team_evidence_aggregation_witness"},
}
PUBLIC_EXPORTS = {
    "team_evidence_aggregation_types": (
        "TeamEvidenceSourceLineage", "TeamEvidenceCapture", "TeamEvidenceRevision", "TeamEvidenceAssessmentRevision",
        "TeamEvidenceAggregationRecord", "TeamEvidenceCurrentRevisionSelection", "TeamEvidenceAggregationInput", "TeamEvidenceRequirement",
        "TeamEvidenceAggregationConfig", "TeamEvidenceTemporalAssessment", "TeamEvidenceWeightAllocation", "TeamEvidenceRequirementWitness",
        "TeamEvidenceRequirementCoverage", "TeamEvidenceDiagnosticRow", "TeamEvidenceContradictionResult", "TeamEvidenceAggregationResult",
        "validate_team_evidence_aggregation_input_contract", "select_team_evidence_canonical_current_records", "select_team_evidence_canonical_capture_records",
    ),
    "team_evidence_aggregation_codec": (
        "team_evidence_aggregation_config_payload", "team_evidence_aggregation_input_payload",
        "team_evidence_aggregation_config_digest", "team_evidence_aggregation_core_payload", "team_evidence_aggregation_payload",
        "team_evidence_aggregation_core_digest", "validate_team_evidence_aggregation_core_digest",
    ),
    "team_evidence_aggregation_temporal": ("assess_team_evidence_temporal",),
    "team_evidence_aggregation_allocation": ("allocate_team_evidence_weights",),
    "team_evidence_aggregation_witness": ("build_team_evidence_requirement_coverage",),
    "team_evidence_aggregation": ("build_team_evidence_aggregation_result", "validate_team_evidence_aggregation_result"),
}
PUBLIC_CLASS_EXPORTS = frozenset(PUBLIC_EXPORTS["team_evidence_aggregation_types"][:16])
NODE_2_PUBLIC_NAMES = frozenset().union(*PUBLIC_EXPORTS.values())
HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
FORBIDDEN_COMPONENTS = frozenset((
    "account", "accounts", "aiohttp", "api", "argparse", "argv", "auth", "authenticate", "authentication", "browser", "cache", "caches",
    "cached", "cli", "client", "click", "credential", "credentials", "csv", "cursor", "db", "database", "duckdb", "environ", "execute",
    "execution", "exchange", "external", "file", "files", "filename", "filepath", "fork", "getenv", "getopt", "http", "https", "importlib",
    "jsonl", "log", "logs", "logger", "logging", "migration", "migrate", "mkdir", "mkdtemp", "mkstemp", "mongo", "mongodb", "mutate",
    "mutation", "mysql", "os", "order", "orders", "password", "passwords", "pathlib", "persist", "persistence", "persistent", "popen",
    "postgres", "postgresql", "process", "processes", "psycopg", "putenv", "random", "randomize", "redis", "remove", "request",
    "requests", "scrape", "scraper", "scrapers", "scraping", "secret", "secrets", "seed", "selenium", "sign", "signing", "signature",
    "signatures", "size", "sizing", "socket", "sockets", "spawn", "sql", "sqlalchemy", "sqlite", "stdin", "stdout", "stderr", "store",
    "stores", "storage", "subprocess", "supabase", "system", "tempfile", "token", "tokens", "typer", "urllib", "wallet", "wallets",
    "websocket", "websockets",
))
FORBIDDEN_SEQUENCES = (
    ("capital", "allocation"), ("allocation", "to", "capital"), ("exchange", "mutation"), ("exchange", "mutate"), ("hosted", "account"),
    ("live", "trading"), ("trading", "live"), ("private", "key"), ("public", "client"), ("read", "text"), ("read", "bytes"),
    ("write", "text"), ("write", "bytes"),
)
FORBIDDEN_BARE_CALLS = frozenset((
    "open", "print", "input", "eval", "exec", "compile", "__import__", "hash", "float", "repr", "random", "randint", "randrange",
    "choice", "choices", "shuffle", "sample", "uniform", "gauss", "seed", "getrandbits", "randbytes",
))
FORBIDDEN_CALL_TERMINALS = frozenset(("now", "utcnow", "timestamp", "total_seconds"))
IDENTITY_COMPONENTS = frozenset(("decode", "decoder", "evaluator", "forecast", "legacy", "packet", "provenance", "receipt", "receipts", "replay"))
IDENTITY_SEQUENCES = (
    ("legacy", "projection"), ("forecast", "packet"), ("run", "id"), ("run", "digest"), ("forecast", "id"), ("forecast", "digest"),
    ("evidence", "id"), ("evidence", "digest"),
)
IDENTITY_STRING_TOKENS = ("tea:v1", "tfr:v1", "tfe:v1", "run_id", "forecast_id", "evidence_id", "packet", "legacy", "decoder", "replay")
CONFIG_BASE: dict[str, object] = {
    "config_version": "generic-test-v1", "max_evidence_age_seconds": Decimal("60.000000"),
    "max_capture_lag_seconds": Decimal("20.000000"), "independence_group_weight_cap": Decimal("1.000000"),
    "correlation_group_weight_cap": Decimal("1.000000"), "max_requirement_assignments_per_evidence": 2,
    "contradiction_no_probability_max": Decimal("0.250000"), "contradiction_yes_probability_min": Decimal("0.750000"),
    "contradiction_watch_score": Decimal("0.250000"), "contradiction_block_score": Decimal("0.750000"),
    "publish_probability_floor": Decimal("0.110000"), "publish_probability_ceiling": Decimal("0.890000"),
    "maximum_records": 128, "maximum_requirements": 32, "maximum_requirement_memberships": 1024, "maximum_witness_edges": 256, "requirements": (),
}
HARD_MAXIMA_CASES = (
    ("max_requirement_assignments_per_evidence", 33, 32), ("maximum_records", 129, 128), ("maximum_requirements", 33, 32),
    ("maximum_requirement_memberships", 1025, 1024), ("maximum_witness_edges", 257, 256),
)


def _components(identifier: str) -> tuple[str, ...]:
    parts: list[str] = []
    for chunk in identifier.split("_"):
        parts.extend(word.lower() for word in re.findall(r"[A-Z]+(?![a-z0-9])|[A-Z][a-z0-9]*|[a-z0-9]+", chunk))
    return tuple(part for part in parts if part)


def _semantic_identifiers(tree: ast.Module, *, surfaces_only: bool = False) -> list[tuple[int, str]]:
    """Collect identifiers from every plan-enumerated position; ``surfaces_only`` drops only function-local ``Name`` ids."""
    found: list[tuple[int, str]] = []
    def visit(node: ast.AST, in_function: bool) -> None:
        for child in ast.iter_child_nodes(node):
            nested = in_function or isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                for alias in child.names:
                    if isinstance(child, ast.ImportFrom):
                        found.append((child.lineno, alias.name))
                    if alias.asname is not None:
                        found.append((child.lineno, alias.asname))
            elif isinstance(child, ast.Attribute):
                found.append((child.lineno, child.attr))
            elif isinstance(child, ast.Name) and not (surfaces_only and in_function):
                found.append((child.lineno, child.id))
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.append((child.lineno, child.name))
            elif isinstance(child, ast.arg):
                found.append((child.lineno, child.arg))
            elif isinstance(child, ast.keyword) and child.arg is not None:
                found.append((child.lineno, child.arg))
            elif isinstance(child, ast.ExceptHandler) and child.name is not None:
                found.append((child.lineno, child.name))
            elif isinstance(child, (ast.Global, ast.Nonlocal)):
                found.extend((child.lineno, entry) for entry in child.names)
            visit(child, nested)

    visit(tree, False)
    return found


def _identifier_violations(tree: ast.Module, singles: frozenset[str], sequences: tuple[tuple[str, ...], ...], *, surfaces_only: bool = False) -> list[str]:
    violations: list[str] = []
    for lineno, identifier in _semantic_identifiers(tree, surfaces_only=surfaces_only):
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
            violations.extend(f"line {node.lineno}: module '{a.name}' is not in the allowlist" for a in node.names if a.name not in allowlist)
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module:
                violations.append(f"line {node.lineno}: relative or empty-module import")
            elif node.module not in allowlist:
                violations.append(f"line {node.lineno}: module '{node.module}' is not in the allowlist")
            violations.extend(f"line {node.lineno}: wildcard import" for a in node.names if a.name == "*")
    return violations


def _call_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            terminal = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if isinstance(func, ast.Name) and func.id in FORBIDDEN_BARE_CALLS:
                violations.append(f"line {func.lineno}: forbidden call '{func.id}()'")
            if terminal in FORBIDDEN_CALL_TERMINALS:
                violations.append(f"line {func.lineno}: forbidden clock call '{terminal}()'")
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
            elif isinstance(node.value, str):
                if "btc" in node.value.lower() or "bitcoin" in node.value.lower():
                    violations.append(f"line {node.lineno}: embedded btc or bitcoin constant")
                if node.value in ("0.020000", "0.980000"): violations.append(f"line {node.lineno}: embedded btc publication bound")
        elif isinstance(node, ast.Name) and node.id == "float": violations.append(f"line {node.lineno}: float annotation, call, or reference")
        elif isinstance(node, ast.ExceptHandler) and node.type is not None:
            if {item.id for item in ast.walk(node.type) if isinstance(item, ast.Name)} & {"Exception", "BaseException"}:
                violations.append(f"line {node.lineno}: broad except handler")
        elif isinstance(node, ast.FormattedValue) and node.conversion == ord("r"): violations.append(f"line {node.lineno}: object repr conversion in payload or error")
    return violations


def _export_violations(tree: ast.Module, module: str) -> list[str]:
    expected = PUBLIC_EXPORTS[module]
    exported = set(expected)
    violations: list[str] = []
    assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)]
    if len(assignments) != 1:
        return ["__all__ must be exactly one direct tuple assignment"]
    allowed = {id(t) for t in assignments[0].targets if isinstance(t, ast.Name) and t.id == "__all__"}
    for node in ast.walk(tree):
        if id(node) in allowed:
            continue
        names: set[str] = set()
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
                if isinstance(node, ast.ImportFrom):
                    names.add(alias.name)
        if "__all__" in names:
            violations.append("__all__ must be exactly one direct tuple assignment with no other binding anywhere")
        violations.extend(f"export '{n}' must not be satisfied or rebound by any binding anywhere" for n in sorted(names & exported))
    if not isinstance(assignments[0].value, ast.Tuple) or not all(isinstance(e, ast.Constant) and isinstance(e.value, str) for e in assignments[0].value.elts):
        violations.append("__all__ must be one tuple of string constants")
    else:
        names = tuple(e.value for e in assignments[0].value.elts)
        if len(set(names)) != len(names):
            violations.append("__all__ contains duplicate names")
        if names != expected:
            violations.append(f"__all__ must equal the exact export tuple; got {names!r}")
    for name in expected:
        want = ast.ClassDef if name in PUBLIC_CLASS_EXPORTS else ast.FunctionDef
        anywhere = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name]
        direct = [n for n in tree.body if n in anywhere]
        if len(anywhere) != 1 or not direct or type(direct[0]) is not want:
            violations.append(f"export '{name}' requires exactly one module-level {'class definition' if want is ast.ClassDef else 'direct function definition'}")
    return violations


def _package_root_bound_names(tree: ast.Module) -> set[str]:
    """Collect every name bound anywhere (including conditional or nested blocks) plus ``__all__`` entries."""
    bound: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            bound.add(node.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add(alias.asname or alias.name.split(".")[0])
                if isinstance(node, ast.ImportFrom):
                    bound.add(alias.name)
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            bound.update(i.value for i in ast.walk(node.value) if isinstance(i, ast.Constant) and isinstance(i.value, str))
    return bound


def _module_violations(source: str, module: str, *, exports: bool = True) -> list[str]:
    tree = ast.parse(source)
    violations = _import_violations(tree, IMPORT_ALLOWLISTS[module])
    violations += _identifier_violations(tree, FORBIDDEN_COMPONENTS, FORBIDDEN_SEQUENCES) + _call_violations(tree) + _callback_violations(tree) + _surface_violations(tree)
    if exports: violations += _export_violations(tree, module)
    return violations


BENIGN_IMPORTS = {
    "team_evidence_aggregation_types": "from __future__ import annotations\nimport re\nfrom collections import defaultdict\nfrom dataclasses import dataclass\nfrom datetime import UTC, datetime\nfrom decimal import Context, Decimal\nfrom typing import Final, final\n",
    "team_evidence_aggregation_codec": "from __future__ import annotations as _annotations\nimport dataclasses as _dataclasses\nfrom datetime import datetime\nfrom decimal import Decimal\nimport hashlib\nimport json\nfrom typing import Any\nfrom polymarket_alpha_lab.team_evidence_aggregation_types import TeamEvidenceAggregationConfig\nimport polymarket_alpha_lab.team_evidence_aggregation_types as _types\n",
    "team_evidence_aggregation_temporal": "from __future__ import annotations\nfrom datetime import UTC, datetime, timedelta\nfrom decimal import Decimal\nfrom typing import Final\nfrom polymarket_alpha_lab.team_evidence_aggregation_types import TeamEvidenceTemporalAssessment\n",
    "team_evidence_aggregation_allocation": "from __future__ import annotations\nfrom decimal import Context, Decimal\nfrom typing import TypeVar, cast\nfrom polymarket_alpha_lab.team_evidence_aggregation_types import TeamEvidenceWeightAllocation\n",
    "team_evidence_aggregation_witness": "from __future__ import annotations\nfrom collections import deque\nfrom datetime import UTC, datetime\nfrom decimal import Decimal\nfrom typing import TypeVar, cast\nfrom polymarket_alpha_lab.team_evidence_aggregation_allocation import allocate_team_evidence_weights\nfrom polymarket_alpha_lab.team_evidence_aggregation_types import TeamEvidenceAggregationRecord\n",
    "team_evidence_aggregation": "from __future__ import annotations\nimport dataclasses\nfrom decimal import Context, Decimal, localcontext\nfrom typing import Final\nfrom polymarket_alpha_lab.team_evidence_aggregation_types import TeamEvidenceAggregationConfig\nfrom polymarket_alpha_lab.team_evidence_aggregation_codec import team_evidence_aggregation_config_digest\nfrom polymarket_alpha_lab.team_evidence_aggregation_temporal import assess_team_evidence_temporal\nfrom polymarket_alpha_lab.team_evidence_aggregation_allocation import allocate_team_evidence_weights\nfrom polymarket_alpha_lab.team_evidence_aggregation_witness import build_team_evidence_requirement_coverage\n",
}
BENIGN_VARIANTS = "from decimal import _private_context_member\nfrom decimal import Decimal as value_type\nimport decimal as fixed_point\ndef outer(factory):\n    def inner(factory: type[object]):\n        return factory()\n    return inner\n"
IMPORT_FAIL_CASES = (
    ("seventh_module", "team_evidence_aggregation", "from polymarket_alpha_lab.team_evidence_aggregation_unknown import helper\n"),
    ("prefix_extension", "team_evidence_aggregation_codec", "import polymarket_alpha_lab.team_evidence_aggregation_types_extra\n"),
    ("package_root_import", "team_evidence_aggregation_temporal", "import polymarket_alpha_lab\n"),
    ("package_root_importfrom", "team_evidence_aggregation_allocation", "from polymarket_alpha_lab import TeamEvidenceWeightAllocation\n"),
    ("relative_import", "team_evidence_aggregation_witness", "from .team_evidence_aggregation_types import TeamEvidenceCapture\n"),
    ("relative_empty_module", "team_evidence_aggregation_types", "from . import team_evidence_aggregation_types\n"),
    ("wildcard_import", "team_evidence_aggregation", "from decimal import *\n"), ("unlisted_module", "team_evidence_aggregation_temporal", "import os\n"),
    ("forbidden_alias", "team_evidence_aggregation", "import decimal as subprocess\n"), ("forbidden_member", "team_evidence_aggregation_types", "from datetime import wallet\n"),
    ("forbidden_member_underscore", "team_evidence_aggregation", "from typing import _private_wallet_helper\n"),
)
REJECT_SNIPPETS = (
    ("identifier_name", "value = wallet\n"), ("identifier_attribute", "value = record.private_wallet\n"),
    ("identifier_function", "def socket_reader():\n    return None\n"), ("identifier_async_function", "async def wallet_loader():\n    return None\n"),
    ("identifier_class", "class Wallet:\n    pass\n"), ("identifier_argument", "def load(wallet_id):\n    return wallet_id\n"),
    ("identifier_global", "global order_book\n"), ("identifier_nonlocal", "def outer():\n    def inner():\n        nonlocal order_book\n"),
    ("identifier_except_name", "try:\n    pass\nexcept ValueError as token_store:\n    pass\n"), ("identifier_import_asname", "import datetime as subprocess\n"),
    ("identifier_importfrom_member", "from datetime import credential_token\n"), ("identifier_keyword", "compute(wallet_id=1)\n"),    ("call_open", 'descriptor = open("state.jsonl")\n'), ("call_print", 'print("message")\n'),
    ("call_input", "value = input()\n"), ("call_eval", 'value = eval("expression")\n'),
    ("call_exec", 'exec("statement")\n'), ("call_compile", 'value = compile("source", "source", "exec")\n'),
    ("call_dynamic_import", 'module = __import__("os")\n'), ("call_hash", "value = hash(record)\n"),
    ("call_random", "value = random()\n"), ("call_randint", "value = randint(0, 9)\n"),
    ("call_float", "value = float(record)\n"), ("call_repr", "text = repr(record)\n"),
    ("call_read_text", "value = handle.read_text()\n"), ("call_write_bytes", "value = handle.write_bytes(data)\n"),
    ("call_module_alias_now", "import datetime as clock\nvalue = clock.now()\n"), ("call_attribute_now", "value = datetime.now()\n"),
    ("call_member_alias_utcnow", "from datetime import datetime as clock\nvalue = clock.utcnow()\n"),
    ("call_terminal_timestamp", "value = record.captured_at.timestamp()\n"), ("call_terminal_total_seconds", "value = record.delta.total_seconds()\n"),
    ("surface_float_literal", "ratio = 0.5\n"), ("surface_float_annotation", "ratio: float = 0\n"), ("surface_float_reference", "kind = float\n"),
    ("surface_broad_exception", "try:\n    pass\nexcept Exception:\n    pass\n"), ("surface_broad_base_exception", "try:\n    pass\nexcept BaseException as error:\n    pass\n"),
    ("surface_formatted_repr", 'text = f"{record!r}"\n'), ("surface_btc_constant", 'theme = "btc"\n'), ("surface_bitcoin_constant", 'theme = "bitcoin-maxi"\n'),
    ("surface_floor_constant", 'value = Decimal("0.020000")\n'), ("surface_ceiling_constant", 'value = Decimal("0.980000")\n'), ("surface_callback_from_input", "def apply(callback):\n    return callback()\n"),
    ("surface_callback_closure", "def outer(callback):\n    def inner():\n        return callback()\n    return inner\n"),
    ("callback_default_scope", "def outer(factory):\n    def inner(factory: type[object] = factory()):\n        return factory()\n    return inner\n"),
    ("callback_annotation_scope", "def outer(callback):\n    def inner(*values: callback(), **options: callback()) -> callback():\n        return None\n    return inner\n"),
)
FUTURE_IMPORT = "from __future__ import annotations\n"
OK_TEMPORAL_DEF = "def assess_team_evidence_temporal(*, config: object) -> None:\n    return None\n"
OK_TEMPORAL_ALL = '__all__ = ("assess_team_evidence_temporal",)\n'


def _export_case(all_expr: str, definition: str, extra: str = "") -> str: return FUTURE_IMPORT + all_expr + definition + extra


EXPORT_CASES = (
    ("clean", _export_case(OK_TEMPORAL_ALL, OK_TEMPORAL_DEF), True), ("list_not_tuple", _export_case('__all__ = ["assess_team_evidence_temporal"]\n', OK_TEMPORAL_DEF), False),
    ("duplicate_entry", _export_case('__all__ = ("assess_team_evidence_temporal", "assess_team_evidence_temporal")\n', OK_TEMPORAL_DEF), False),
    ("extra_entry", _export_case('__all__ = ("assess_team_evidence_temporal", "extra")\n', OK_TEMPORAL_DEF), False), ("non_string_element", _export_case("__all__ = (assess_team_evidence_temporal,)\n", OK_TEMPORAL_DEF), False),
    ("second_assignment", _export_case(OK_TEMPORAL_ALL, OK_TEMPORAL_DEF + OK_TEMPORAL_ALL), False), ("augmented_assignment", _export_case("", OK_TEMPORAL_DEF, '__all__ = ("assess_team_evidence_temporal",)\n__all__ += ("extra",)\n'), False),
    ("assignment_binding", _export_case(OK_TEMPORAL_ALL, OK_TEMPORAL_DEF, "assess_team_evidence_temporal = None\n"), False),
    ("conditional_rebind", _export_case(OK_TEMPORAL_ALL, OK_TEMPORAL_DEF, "if True:\n    assess_team_evidence_temporal = None\n"), False),
    ("conditional_all_rebind", _export_case(OK_TEMPORAL_ALL, OK_TEMPORAL_DEF, 'if True:\n    __all__ = ("other",)\n'), False),
    ("chained_all_rebind", _export_case('__all__ = assess_team_evidence_temporal = ("assess_team_evidence_temporal",)\n', OK_TEMPORAL_DEF), False),
    ("unpacked_all_rebind", _export_case('__all__ = (__all__,) = ("assess_team_evidence_temporal",)\n', OK_TEMPORAL_DEF), False),
    ("nested_import_binding", _export_case(OK_TEMPORAL_ALL, OK_TEMPORAL_DEF, "def wrapper():\n    from datetime import assess_team_evidence_temporal\n"), False),
    ("import_binding", _export_case("from datetime import assess_team_evidence_temporal\n" + OK_TEMPORAL_ALL, OK_TEMPORAL_DEF), False),
    ("nested_definition", _export_case(OK_TEMPORAL_ALL, OK_TEMPORAL_DEF, "def wrapper():\n    def assess_team_evidence_temporal():\n        return None\n    return wrapper\n"), False),
    ("async_kind", _export_case(OK_TEMPORAL_ALL, "async def assess_team_evidence_temporal():\n    return None\n"), False),
    ("class_kind", _export_case(OK_TEMPORAL_ALL, "class assess_team_evidence_temporal:\n    pass\n"), False),
    ("walrus_binding", _export_case(OK_TEMPORAL_ALL, OK_TEMPORAL_DEF, "if (assess_team_evidence_temporal := 1):\n    pass\n"), False),
)
IDENTITY_FAIL_CASES = (
    ("run_identity", "run_id = \"r-1\"\n"), ("version_string", 'schema_version = "tea:v1"\n'), ("legacy_projection", "legacy_projection = 1\n"),
    ("attribute_identity", "def probe(record):\n    return record.run_id\n"), ("packet_builder", "def build_forecast_packet():\n    return None\n"),
    ("decoder_helper", "def _decode_core():\n    return None\n"),
)
PACKAGE_ROOT_CLEAN_CASE = "import decimal\nif True:\n    value = 1\n__all__ = (\"MarketScore\",)\n"
PACKAGE_ROOT_REJECT_CASES = (
    ("conditional_import", "if True:\n    from decimal import TeamEvidenceCapture\n"), ("nested_import", "def helper():\n    from decimal import allocate_team_evidence_weights\n"),
    ("conditional_assign", "if True:\n    assess_team_evidence_temporal = None\n"), ("package_all_listing", '__all__ = ("TeamEvidenceRequirement",)\n'),
)


def _conforming_module(module: str) -> str:
    body = [BENIGN_IMPORTS[module]]
    if module == "team_evidence_aggregation":
        body.append("_ZERO = Decimal(\"0.000000\")\ndef _probe(record, value):\n    with localcontext(Context(prec=64)):\n        total = _ZERO + record.assessment_revision.requested_weight\n    return dataclasses.replace(record, capture_id=record.capture.capture_id), value.is_finite(), sorted((record,))\n")
    for name in PUBLIC_EXPORTS[module]:
        body.append(f"class {name}:\n    pass\n" if name in PUBLIC_CLASS_EXPORTS else f"def {name}(*, config: object) -> None:\n    return None\n")
    body.append("__all__ = (\n" + "".join(f'    "{name}",\n' for name in PUBLIC_EXPORTS[module]) + ")\n")
    return "".join(body)


def test_node_2_unified_ast_import_export_forbidden_surface_and_line_size_gate() -> None:
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
        if not _module_violations(snippet, "team_evidence_aggregation_temporal", exports=False): failures.append(f"snippets case '{case}' was not rejected")
    for case, source, must_pass in EXPORT_CASES:
        found = _module_violations(source, "team_evidence_aggregation_temporal")
        if must_pass and found: failures.append(f"export case '{case}' was wrongly rejected: {found}")
        if not must_pass and not found: failures.append(f"export case '{case}' was not rejected")
    violations: list[str] = []
    production_counts: dict[str, int] = {}
    for module, ceiling in PRODUCTION_LINE_LIMITS.items():
        path = PRODUCTION_DIR / module
        if not path.is_file():
            violations.append(f"{module}: required Node 2 production module is missing")
            continue
        source = path.read_text(encoding="utf-8")
        count = len(source.splitlines())
        production_counts[module] = count
        if count > ceiling:
            violations.append(f"{module}: {count} physical lines exceed ceiling {ceiling}")
        violations.extend(f"{module}: {item}" for item in _module_violations(source, module.removesuffix(".py")))
    if len(production_counts) == len(PRODUCTION_LINE_LIMITS) and sum(production_counts.values()) > PRODUCTION_TOTAL_LINE_LIMIT: violations.append(f"production total {sum(production_counts.values())} exceeds {PRODUCTION_TOTAL_LINE_LIMIT} lines")
    test_counts: dict[str, int] = {}
    for name, ceiling in TEST_LINE_LIMITS.items():
        path = TEST_DIR / name
        if not path.is_file():
            violations.append(f"{name}: required Node 2 test module is missing")
            continue
        count = len(path.read_text(encoding="utf-8").splitlines())
        test_counts[name] = count
        if count > ceiling:
            violations.append(f"{name}: {count} physical lines exceed ceiling {ceiling}")
    if len(test_counts) == len(TEST_LINE_LIMITS) and sum(test_counts.values()) > TEST_TOTAL_LINE_LIMIT: violations.append(f"test total {sum(test_counts.values())} exceeds {TEST_TOTAL_LINE_LIMIT} lines")
    assert not failures, "synthetic guard failures:\n" + "\n".join(failures)
    assert not violations, "\n".join(violations)


def test_node_2_public_dataclasses_are_frozen_slotted_final_and_hard_flagged() -> None:
    source = (PRODUCTION_DIR / "team_evidence_aggregation_types.py").read_text(encoding="utf-8")
    classes = {n.name: n for n in ast.parse(source).body if isinstance(n, ast.ClassDef)}
    problems: list[str] = []
    for name in sorted(PUBLIC_CLASS_EXPORTS):
        node = classes.get(name)
        if node is None:
            problems.append(f"{name} is not a direct class definition")
            continue
        if not any(isinstance(d, ast.Name) and d.id == "final" for d in node.decorator_list): problems.append(f"{name} is missing the @final decorator")
        calls = [d for d in node.decorator_list if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass"]
        keywords = {k.arg: k.value for call in calls for k in call.keywords}
        if len(calls) != 1 or set(keywords) != {"frozen", "slots"} or not all(isinstance(v, ast.Constant) and v.value is True for v in keywords.values()):
            problems.append(f"{name} is missing @dataclass(frozen=True, slots=True)")
        statements = {s.target.id: s for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)}
        for flag in HARD_FLAG_NAMES:
            statement = statements.get(flag)
            if statement is None or not (isinstance(statement.annotation, ast.Name) and statement.annotation.id == "bool") or not (isinstance(statement.value, ast.Constant) and statement.value.value is True):
                problems.append(f"{name}.{flag} must be 'bool' with a literal True default")
    assert not problems, "\n".join(problems)
    for name in sorted(PUBLIC_CLASS_EXPORTS):
        public_class = getattr(team_evidence_types, name)
        assert getattr(public_class, "__final__", False) is True, name
        assert public_class.__dataclass_params__.frozen is True, name
        with pytest.raises(TypeError):
            type("ForbiddenSubclass", (public_class,), {})
    with pytest.raises(ValueError):
        TeamEvidenceRequirement(requirement_id="requirement", minimum_witness_count=1, minimum_effective_weight=Decimal("0"), unmet_status="watch", paper_only=False)


def test_node_2_config_policy_fields_have_no_defaults_and_hard_maxima_fail_closed() -> None:
    source = (PRODUCTION_DIR / "team_evidence_aggregation_types.py").read_text(encoding="utf-8")
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "TeamEvidenceAggregationConfig")
    problems = [f"config policy field '{s.target.id}' must not have a default" for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name) and s.target.id not in HARD_FLAG_NAMES and s.value is not None]
    assert not problems, "\n".join(problems)
    for module, exports in PUBLIC_EXPORTS.items():
        for name in exports:
            assert not name.startswith(("maximum_", "max_")), f"{module} exports implementation maximum '{name}'"
    for field, above_max, exact_max in HARD_MAXIMA_CASES:
        with pytest.raises(ValueError):
            TeamEvidenceAggregationConfig(**(CONFIG_BASE | {field: above_max}))
        TeamEvidenceAggregationConfig(**(CONFIG_BASE | {field: exact_max}))
    TeamEvidenceAggregationConfig(**(CONFIG_BASE | {field: exact_max for field, _, exact_max in HARD_MAXIMA_CASES}))


def test_node_2_package_root_has_no_node_2_public_exports() -> None:
    tree = ast.parse((PRODUCTION_DIR / "__init__.py").read_text(encoding="utf-8"))
    bound = _package_root_bound_names(tree)
    assert not (bound & NODE_2_PUBLIC_NAMES), sorted(bound & NODE_2_PUBLIC_NAMES)
    assert not (_package_root_bound_names(ast.parse(PACKAGE_ROOT_CLEAN_CASE)) & NODE_2_PUBLIC_NAMES), "clean package-root synthetic was rejected"
    for case, snippet in PACKAGE_ROOT_REJECT_CASES:
        overlap = _package_root_bound_names(ast.parse(snippet)) & NODE_2_PUBLIC_NAMES
        assert overlap, f"package-root case '{case}' was not rejected"


def test_node_2_has_no_outer_identity_packet_legacy_or_persistence_surface() -> None:
    def identity_violations(snippet: str) -> list[str]:
        tree = ast.parse(snippet)
        found = _identifier_violations(tree, IDENTITY_COMPONENTS, IDENTITY_SEQUENCES, surfaces_only=True)
        found += [f"line {n.lineno}: forbidden outer-identity constant" for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and any(t in n.value.lower() for t in IDENTITY_STRING_TOKENS)]
        return found

    failures = [f"identity case '{case}' was not rejected" for case, snippet in IDENTITY_FAIL_CASES if not identity_violations(snippet)]
    violations: list[str] = []
    for module in PRODUCTION_LINE_LIMITS:
        path = PRODUCTION_DIR / module
        if not path.is_file():
            violations.append(f"{module}: required Node 2 production module is missing")
            continue
        violations.extend(f"{module}: {item}" for item in identity_violations(path.read_text(encoding="utf-8")))
    assert not failures, "synthetic identity guard failures:\n" + "\n".join(failures)
    assert not violations, "\n".join(violations)
