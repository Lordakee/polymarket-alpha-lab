"""Node 8 child-local AST, import/export, forbidden-surface, delegation, package-root, and size guard.

Enforces ``team_evaluation_attempt_latest_read.py`` (read-only latest-attempt report): a curated standard-library allowlist
plus exactly the three Node 5 read modules, with the adapter and the store member-pinned to only their plain latest-attempt
loaders (every writer/insert/rows member forbidden), the exact three-name ``__all__`` with anywhere-binding rebinding
protection, the frozen/slotted/hard-flagged field-complete report dataclass, both reader callables delegating to exactly
their own pinned loader, no SQL/env/filesystem/network/floats/ambient-clock/randomness/``hash()``/broad-except/``print``,
no side-selection, ranking, recommendation, packet-construction, writer, DSN-construction, or strategy-cycle semantics
(string literals and identifiers distinguished), no package-root exports, and every Node 8 ceiling (pending-red fail-closed while a parallel worker's file is missing or over its ceiling).
"""
from __future__ import annotations

import ast
import dataclasses
import importlib
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIR, TEST_DIR = REPO_ROOT / "src" / "polymarket_alpha_lab", REPO_ROOT / "tests"
PRODUCTION_FILE = "team_evaluation_attempt_latest_read.py"
PRODUCTION_PATH, PRODUCTION_IMPORT = PRODUCTION_DIR / PRODUCTION_FILE, "polymarket_alpha_lab.team_evaluation_attempt_latest_read"
PRODUCTION_LINE_LIMIT, NODE_8_TEST_TOTAL_LINE_LIMIT = 340, 1_280
TEST_LINE_LIMITS = {"test_team_evaluation_attempt_latest_read.py": 720, "test_team_evaluation_attempt_latest_read_scope.py": 520}
STORE_MODULE = "polymarket_alpha_lab.team_evidence_aggregation_attempt_store"
ADAPTER_MODULE = "polymarket_alpha_lab.team_evidence_aggregation_attempt_psycopg"
DB_ROW_MODULE = "polymarket_alpha_lab.team_evidence_aggregation_db_row"
PINNED_STORE_LOADER = "load_latest_team_evaluation_attempt"
PINNED_ADAPTER_LOADER = "load_latest_team_evaluation_attempt_with_psycopg"
PINNED_LOADERS = frozenset((PINNED_STORE_LOADER, PINNED_ADAPTER_LOADER))
DB_ROW_PINNED_MEMBERS = frozenset(("TeamEvaluationAttemptDbRow", "TEAM_EVALUATION_ATTEMPT_PAYLOAD_KEYS", "TEAM_EVALUATION_ATTEMPT_STATUS_VALUES"))
PROJECT_MODULES = frozenset((STORE_MODULE, ADAPTER_MODULE, DB_ROW_MODULE))
MEMBER_PINS = {STORE_MODULE: (PINNED_STORE_LOADER,), ADAPTER_MODULE: (PINNED_ADAPTER_LOADER,), DB_ROW_MODULE: tuple(sorted(DB_ROW_PINNED_MEMBERS))}
PINNED_IMPORT_PAIRS = ((STORE_MODULE, PINNED_STORE_LOADER), (ADAPTER_MODULE, PINNED_ADAPTER_LOADER))
IMPORT_ALLOWLIST = frozenset(("__future__", "dataclasses", "datetime", "decimal", "typing")) | PROJECT_MODULES
READ_EXPORTS = ("TeamEvaluationAttemptLatestReadReport", "read_latest_team_evaluation_attempt_report", "read_latest_team_evaluation_attempt_report_with_psycopg")
READ_CLASS_EXPORTS = frozenset(("TeamEvaluationAttemptLatestReadReport",))
HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
REPORT_FIELDS = (
    "attempt_present", "absence_reason", "tea_id", "tfr_id", "attempted_at", "scope_version", "scope_key", "status", "hard_flag",
    "publication_gate_present", "publication_gate_status", "reason_codes", "publication_gate_reason_codes", "packet_presence", "audit_packet_selected_side", "audit_packet_forecast_probability_yes",
    "paper_only", "report_only", "readonly",
)
READER_KEYWORDS = ("tfr_id", "scope_version", "scope_key", "table_name")
READER_DELEGATION = (("read_latest_team_evaluation_attempt_report", "connection", PINNED_STORE_LOADER),
                     ("read_latest_team_evaluation_attempt_report_with_psycopg", "dsn", PINNED_ADAPTER_LOADER))
ALLOWED_PINNED_IDENTIFIERS = PINNED_LOADERS | DB_ROW_PINNED_MEMBERS
FORBIDDEN_COMPONENTS = frozenset((
    "account", "accounts", "aiohttp", "api", "argparse", "argv", "auth", "authenticate", "authentication", "browser", "cache", "caches", "cached", "cancel", "cli", "client", "click",
    "cost", "costs", "credential", "credentials", "csv", "cursor", "cycle", "cycles", "db", "database", "duckdb", "environ", "execute", "execution", "exchange", "file", "files",
    "filename", "filepath", "fork", "getenv", "getopt", "http", "https", "importlib", "jsonl", "log", "logs", "logger", "logging", "migration", "migrate", "mkdir", "mkdtemp",
    "mkstemp", "mongo", "mongodb", "mutate", "mutation", "mysql", "os", "order", "orders", "password", "passwords", "pathlib", "persist", "persistence", "persistent", "persists",
    "popen", "postgres", "postgresql", "process", "processes", "putenv", "random", "randomize", "rank", "ranked", "ranking", "ranks", "recommend", "recommended", "recommends",
    "recommendation", "recommendations", "redis", "remove", "request", "requests", "scrape", "scraper", "scrapers", "scraping", "secret", "secrets", "seed", "selenium", "sign",
    "signing", "signature", "signatures", "socket", "sockets", "spawn", "sql", "sqlalchemy", "sqlite", "stdin", "stdout", "stderr", "store", "stores", "storage", "strategies",
    "strategy", "subprocess", "submit", "submission", "system", "tempfile", "token", "tokens", "typer", "urllib", "wallet", "wallets", "websocket", "websockets"))
FORBIDDEN_SEQUENCES = (
    ("live", "trading"), ("trading", "live"), ("private", "key"), ("hosted", "account"), ("read", "text"), ("read", "bytes"), ("write", "text"), ("write", "bytes"),
    ("exchange", "mutate"), ("exchange", "mutation"), ("select", "side"), ("side", "select"), ("side", "selection"), ("selection", "side"), ("choose", "side"), ("side", "choose"),
    ("pick", "side"), ("side", "pick"), ("strategy", "cycle"), ("cycle", "strategy"), ("packet", "build"), ("build", "packet"), ("recommend", "side"), ("side", "recommend"),
)
FORBIDDEN_EXACT_NAMES = frozenset((
    "insert_team_evaluation_attempt", "insert_team_evaluation_attempt_with_psycopg", "insert_team_evaluation_attempts_with_psycopg", "persist_team_evaluation_attempts_with_psycopg",
    "_insert_attempt_rows_atomic", "load_team_evaluation_attempt_rows", "load_team_evaluation_attempts_with_psycopg", "TeamEvaluationAttemptWriteResult",
    "TEAM_EVALUATION_ATTEMPT_COLUMNS", "team_evaluation_attempt_to_db_row", "team_evaluation_attempt_row_parameters", "_with_owned_connection", "_connect",
    "_register_dict_jsonb_dumper", "validate_local_postgres_dsn", "TeamForecastPacket", "TeamForecastEvidencePacket", "team_forecast_packet_payload",
    "legacy_forecast_packet", "TeamForecastBuildEnvelope", "build_team_forecast_build_envelope", "validate_team_forecast_build_envelope",
    "evaluate_crypto_btc_evidence", "evaluate_and_persist_crypto_btc_forecast"))
FORBIDDEN_BARE_CALLS = frozenset((
    "open", "print", "input", "eval", "exec", "compile", "__import__", "hash", "float", "repr", "random", "randint", "randrange", "choice", "choices", "shuffle", "sample", "uniform", "gauss",
    "seed", "getrandbits", "randbytes", "getenv", "putenv"))
FORBIDDEN_CALL_TERMINALS = frozenset((
    "now", "utcnow", "today", "timestamp", "total_seconds", "time", "time_ns", "monotonic", "monotonic_ns", "perf_counter", "perf_counter_ns", "clock", "gmtime", "localtime", "ctime", "asctime"))
SQL_STATEMENT_PATTERNS = tuple(re.compile(p, re.IGNORECASE | re.DOTALL) for p in (
    r"\binsert\s+into\b", r"\bselect\b.+\bfrom\b", r"\bupdate\b.+\bset\b", r"\bdelete\s+from\b", r"\bmerge\s+into\b", r"\bon\s+conflict\b",
    r"\bcreate\s+table\b", r"\balter\s+table\b", r"\btruncate\s+table\b"))
SIDE_STRING_VALUES, STRATEGY_CYCLE_MARKERS, DSN_STRING_MARKERS = frozenset(("yes", "no")), ("strategy_cycle", "strategy-cycle"), ("://", "password=")
DEFAULT_TABLE_NAME = "team_evaluation_attempts"


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
        elif isinstance(node, ast.arg) or (isinstance(node, ast.keyword) and node.arg is not None): found.append((node.lineno, node.arg))
        elif isinstance(node, ast.ExceptHandler) and node.name is not None: found.append((node.lineno, node.name))
        elif isinstance(node, (ast.Global, ast.Nonlocal)): found.extend((node.lineno, entry) for entry in node.names)
    return found


def _docstring_constant_ids(tree: ast.Module) -> set[int]:
    """Docstrings may state the deferred strategy-cycle and side boundaries in prose; code constants may not."""
    statements = [n for n in tree.body if isinstance(n, ast.Expr)] + [s for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                                                                     for s in n.body if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)]
    return {id(s.value) for s in statements if isinstance(s.value, ast.Constant) and isinstance(s.value.value, str)}


def _identifier_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for lineno, identifier in _semantic_identifiers(tree):
        if identifier in FORBIDDEN_EXACT_NAMES:
            violations.append(f"line {lineno}: forbidden persistence or packet-surface identifier '{identifier}'")
            continue
        if identifier in ALLOWED_PINNED_IDENTIFIERS: continue
        parts = _components(identifier)
        hits = [part for part in parts if part in FORBIDDEN_COMPONENTS]
        hits.extend("-".join(s) for s in FORBIDDEN_SEQUENCES for i in range(len(parts) - len(s) + 1) if parts[i:i + len(s)] == s)
        if hits: violations.append(f"line {lineno}: forbidden identifier '{identifier}' ({', '.join(hits)})")
    return violations


def _import_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in PROJECT_MODULES: violations.append(f"line {node.lineno}: module '{a.name}' must be imported only through its pinned members")
                elif a.name not in IMPORT_ALLOWLIST: violations.append(f"line {node.lineno}: module '{a.name}' is not in the Node 8 allowlist")
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module: violations.append(f"line {node.lineno}: relative or empty-module import")
            elif node.module not in IMPORT_ALLOWLIST: violations.append(f"line {node.lineno}: module '{node.module}' is not in the Node 8 allowlist")
            violations.extend(f"line {node.lineno}: wildcard import" for a in node.names if a.name == "*")
            if node.module in PROJECT_MODULES:
                pinned = MEMBER_PINS[node.module]
                violations.extend(f"line {node.lineno}: member '{a.asname or a.name}' of {node.module} is not one of the plainly imported pinned members {sorted(pinned)}" for a in node.names if a.name != "*" and (a.name not in pinned or a.asname is not None))
    return violations


def _pinned_binding_violations(tree: ast.Module) -> list[str]:
    """The two pinned loaders may only be bound by their plain canonical module imports."""
    allowed_alias_ids = {id(a) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level == 0 for a in n.names if a.asname is None and (n.module, a.name) in PINNED_IMPORT_PAIRS}
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            violations.extend(f"line {node.lineno}: pinned loader '{a.asname or a.name}' must be imported plainly from its pinned module" for a in node.names if (a.asname or a.name) in PINNED_LOADERS and id(a) not in allowed_alias_ids)
        elif isinstance(node, ast.Import):
            violations.extend(f"line {node.lineno}: pinned loader must never be bound via a plain module import" for a in node.names if (a.asname or a.name.split(".")[0]) in PINNED_LOADERS)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in PINNED_LOADERS:
            violations.append(f"line {node.lineno}: pinned loader '{node.id}' must never be rebound")
        elif isinstance(node, ast.arg) and node.arg in PINNED_LOADERS:
            violations.append(f"line {node.lineno}: parameter '{node.arg}' shadows a pinned loader")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in PINNED_LOADERS:
            violations.append(f"line {node.lineno}: definition '{node.name}' shadows a pinned loader")
    return violations


def _required_pinned_import_violations(tree: ast.Module) -> list[str]:
    present = {(n.module, a.name) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level == 0 for a in n.names if a.asname is None}
    return [f"the pinned loader '{name}' must be imported plainly from {module}" for module, name in PINNED_IMPORT_PAIRS if (module, name) not in present]


def _call_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call): continue
        func = node.func
        terminal = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if isinstance(func, ast.Name) and func.id in FORBIDDEN_BARE_CALLS: violations.append(f"line {func.lineno}: forbidden call '{func.id}()'")
        if terminal in FORBIDDEN_CALL_TERMINALS: violations.append(f"line {func.lineno}: forbidden ambient-clock call '{terminal}()'")
        if terminal in FORBIDDEN_EXACT_NAMES: violations.append(f"line {func.lineno}: forbidden persistence, packet, or writer call '{terminal}()'")
    return violations


def _surface_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    docstrings = _docstring_constant_ids(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if type(node.value) is float: violations.append(f"line {node.lineno}: float literal")
            elif isinstance(node.value, str):
                if any(p.search(node.value) for p in SQL_STATEMENT_PATTERNS): violations.append(f"line {node.lineno}: SQL statement text in a read-only report module")
                elif any(m in node.value for m in DSN_STRING_MARKERS): violations.append(f"line {node.lineno}: credential-bearing or DSN-shaped string constant")
                elif node.value.lower() in SIDE_STRING_VALUES: violations.append(f"line {node.lineno}: YES/NO side recommendation token constant")
                elif id(node) not in docstrings and any(m in node.value for m in STRATEGY_CYCLE_MARKERS): violations.append(f"line {node.lineno}: strategy-cycle token constant")
        elif isinstance(node, ast.Name) and node.id == "float": violations.append(f"line {node.lineno}: float annotation, call, or reference")
        elif isinstance(node, ast.ExceptHandler) and node.type is not None and {item.id for item in ast.walk(node.type) if isinstance(item, ast.Name)} & {"Exception", "BaseException"}:
            violations.append(f"line {node.lineno}: broad except handler; DB errors must propagate unchanged")
    return violations


def _dsn_construction_violations(tree: ast.Module) -> list[str]:
    """The caller DSN is only ever passed through to the pinned adapter, never built or interpolated."""
    def references_dsn(node: ast.AST | None) -> bool:
        return node is not None and any((isinstance(n, ast.Name) and "dsn" in _components(n.id)) or (isinstance(n, ast.Attribute) and "dsn" in _components(n.attr)) for n in ast.walk(node))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr) and references_dsn(node): violations.append(f"line {node.lineno}: DSN must only be passed through, never interpolated")
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)) and references_dsn(node): violations.append(f"line {node.lineno}: DSN must only be passed through, never concatenated or %-formatted")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("format", "join") and references_dsn(node): violations.append(f"line {node.lineno}: DSN must only be passed through, never built via '{node.func.attr}'")
    return violations


def _module_string_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level plain string-constant assignments, used to resolve keyword-default names."""
    constants: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            constants.update({target.id: node.value.value for target in node.targets if isinstance(target, ast.Name)})
    return constants


def _delegation_problems(tree: ast.Module) -> list[str]:
    """Each reader callable delegates to exactly its own pinned loader, called directly by name."""
    problems: list[str] = []
    for name, _first, own in READER_DELEGATION:
        node = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name), None)
        if node is None: problems.append(f"{name} must be one module-level function definition"); continue
        called = {n.func.id for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        if own not in called: problems.append(f"{name} must call the pinned loader '{own}' directly by name")
        problems.extend(f"{name} must not call the other pinned loader '{other}'" for other in sorted((PINNED_LOADERS - {own}) & called))
    return problems


def _export_violations(tree: ast.Module, expected: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)]
    if len(assignments) != 1: return ["__all__ must be exactly one direct tuple assignment"]
    allowed = {id(t) for t in assignments[0].targets if isinstance(t, ast.Name) and t.id == "__all__"}
    for node in ast.walk(tree):
        if id(node) in allowed: continue
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
        if len(set(names)) != len(names): violations.append("__all__ contains duplicate names")
        if names != expected: violations.append(f"__all__ must equal the exact ordered export tuple; got {names!r}")
    for name in expected:
        want = ast.ClassDef if name in READ_CLASS_EXPORTS else ast.FunctionDef
        anywhere = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name]
        direct = [n for n in tree.body if n in anywhere]
        if len(anywhere) != 1 or not direct or type(direct[0]) is not want: violations.append(f"export '{name}' requires exactly one module-level definition of the pinned kind")
    return violations


def _module_violations(source: str, *, exports: bool = False, expected: tuple[str, ...] | None = None, require_pinned: bool = False) -> list[str]:
    tree = ast.parse(source)
    violations = (_import_violations(tree) + _identifier_violations(tree) + _call_violations(tree) + _surface_violations(tree)
                  + _dsn_construction_violations(tree) + _pinned_binding_violations(tree))
    if require_pinned: violations += _required_pinned_import_violations(tree)
    if exports: violations += _export_violations(tree, READ_EXPORTS if expected is None else expected)
    return violations


def _class_def_problems(node: ast.ClassDef) -> list[str]:
    calls = [d for d in node.decorator_list if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass"]
    keywords = {k.arg: k.value for call in calls for k in call.keywords}
    problems: list[str] = []
    if len(calls) != 1 or set(keywords) != {"frozen", "slots"} or not all(isinstance(v, ast.Constant) and v.value is True for v in keywords.values()):
        problems.append("missing @dataclass(frozen=True, slots=True)")
    statements = {s.target.id: s for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)}
    for flag in HARD_FLAG_NAMES:
        statement = statements.get(flag)
        if statement is None or not (isinstance(statement.annotation, ast.Name) and statement.annotation.id == "bool") or not (isinstance(statement.value, ast.Constant) and statement.value.value is True): problems.append(f"{flag} must be 'bool' with a literal True default")
    return problems


def _report_field_problems(node: ast.ClassDef) -> list[str]:
    fields = tuple(s.target.id for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name))
    return [] if fields == REPORT_FIELDS else [f"{node.name} fields must be exactly the pinned ordered report fields; got {fields}"]


def _reader_signature_problems(node: ast.FunctionDef, first: str, constants: dict[str, str] | None = None) -> list[str]:
    arguments = node.args
    problems: list[str] = []
    if arguments.posonlyargs or arguments.vararg or arguments.kwarg: problems.append(f"{node.name} takes only plain and keyword-only parameters")
    if tuple(i.arg for i in arguments.args) != (first,): problems.append(f"{node.name} must take exactly one positional parameter '{first}'")
    if tuple(i.arg for i in arguments.kwonlyargs) != READER_KEYWORDS: problems.append(f"{node.name} keyword-only parameters must be exactly {READER_KEYWORDS}")
    defaults = list("none" if d is None else ast.unparse(d) for d in arguments.kw_defaults)
    if len(defaults) == 4 and isinstance(arguments.kw_defaults[3], ast.Name): defaults[3] = repr((constants or {}).get(arguments.kw_defaults[3].id, ""))
    if tuple(defaults) != ("None", "None", "None", repr(DEFAULT_TABLE_NAME)): problems.append(f"{node.name} keyword defaults must be None/None/None/{DEFAULT_TABLE_NAME!r}")
    if node.returns is None or ast.unparse(node.returns) != READ_EXPORTS[0]: problems.append(f"{node.name} must return {READ_EXPORTS[0]}")
    return problems


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


_I, _F = "import polymarket_alpha_lab.", "from polymarket_alpha_lab."
_S, _A, _R = _F + "team_evidence_aggregation_attempt_store import ", _F + "team_evidence_aggregation_attempt_psycopg import ", _F + "team_evidence_aggregation_db_row import "
BENIGN_IMPORTS = (
    "from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime\nfrom decimal import Decimal\nfrom typing import Any\n"
    + _A + "load_latest_team_evaluation_attempt_with_psycopg\n" + _S + "load_latest_team_evaluation_attempt\n" + _R + "TeamEvaluationAttemptDbRow, TEAM_EVALUATION_ATTEMPT_PAYLOAD_KEYS, TEAM_EVALUATION_ATTEMPT_STATUS_VALUES\n")
BENIGN_VARIANTS = (
    "def _gate_section(run_metadata: dict[str, Any]) -> dict[str, Any] | None:\n    gate = run_metadata.get(\"external_publication_gate\")\n    return gate if isinstance(gate, dict) else None\n"
    "def _reason_codes(section: dict[str, Any]) -> tuple[str, ...]:\n    return tuple(section.get(\"reason_codes\", ()))\n"
    "def _audit_packet_fields(packet_presence: str | None) -> tuple[str | None, Decimal | None]:\n    if packet_presence != \"projected\":\n        return None, None\n    return None, Decimal(\"0.500000\")\n")
_REPORT_CLASS = (
    "@dataclass(frozen=True, slots=True)\nclass TeamEvaluationAttemptLatestReadReport:\n"
    "    attempt_present: bool\n    absence_reason: str | None\n    tea_id: str | None\n    tfr_id: str | None\n    attempted_at: datetime | None\n"
    "    scope_version: str | None\n    scope_key: str | None\n    status: str | None\n    hard_flag: bool | None\n    publication_gate_present: bool | None\n"
    "    publication_gate_status: str | None\n    reason_codes: tuple[str, ...]\n    publication_gate_reason_codes: tuple[str, ...]\n    packet_presence: str | None\n"
    "    audit_packet_selected_side: str | None\n    audit_packet_forecast_probability_yes: Decimal | None\n    paper_only: bool = True\n    report_only: bool = True\n    readonly: bool = True\n")
_READER_BODY = (
    "def read_latest_team_evaluation_attempt_report(connection, *, tfr_id=None, scope_version=None, scope_key=None, table_name=\"team_evaluation_attempts\") -> TeamEvaluationAttemptLatestReadReport:\n"
    "    row = load_latest_team_evaluation_attempt(connection, tfr_id=tfr_id, scope_version=scope_version, scope_key=scope_key, table_name=table_name)\n"
    "    if row is None:\n        return TeamEvaluationAttemptLatestReadReport(attempt_present=False, absence_reason=\"no_matching_attempt\", reason_codes=(), publication_gate_reason_codes=(), audit_packet_selected_side=None, audit_packet_forecast_probability_yes=None)\n"
    "    return _project_row_to_report(row)\n")
_READER_PSVCOPG_BODY = (
    "def read_latest_team_evaluation_attempt_report_with_psycopg(dsn, *, tfr_id=None, scope_version=None, scope_key=None, table_name=\"team_evaluation_attempts\") -> TeamEvaluationAttemptLatestReadReport:\n"
    "    row = load_latest_team_evaluation_attempt_with_psycopg(dsn, tfr_id=tfr_id, scope_version=scope_version, scope_key=scope_key, table_name=table_name)\n"
    "    return _project_row_to_report(row)\n")
IMPORT_FAIL_CASES = (
    ('store_writer_member', _S + 'insert_team_evaluation_attempt\n'), ('store_rows_member', _S + 'load_team_evaluation_attempt_rows\n'), ('store_plain_module', _I + 'team_evidence_aggregation_attempt_store\n'), ('store_alias_member', _S + 'load_latest_team_evaluation_attempt as fetch_latest\n'),
    ('store_extra_member', _S + 'load_latest_team_evaluation_attempt, insert_team_evaluation_attempt\n'), ('adapter_writer_member', _A + 'insert_team_evaluation_attempts_with_psycopg\n'), ('adapter_persist_member', _A + 'persist_team_evaluation_attempts_with_psycopg\n'), ('adapter_single_writer', _A + 'insert_team_evaluation_attempt_with_psycopg\n'),
    ('adapter_rows_member', _A + 'load_team_evaluation_attempts_with_psycopg\n'), ('adapter_plain_module', _I + 'team_evidence_aggregation_attempt_psycopg\n'), ('adapter_alias_member', _A + 'load_latest_team_evaluation_attempt_with_psycopg as latest_adapter\n'), ('adapter_private_member', _A + '_insert_attempt_rows_atomic\n'),
    ('db_row_to_row_helper', _R + 'team_evaluation_attempt_to_db_row\n'), ('db_row_parameters_helper', _R + 'team_evaluation_attempt_row_parameters\n'), ('db_row_plain_module', _I + 'team_evidence_aggregation_db_row\n'), ('db_row_alias_member', _R + 'TeamEvaluationAttemptDbRow as Row\n'),
    ('db_row_private_member', _R + '_normalize_payload\n'), ('packet_module', _F + 'team_forecast_packet import TeamForecastPacket\n'), ('envelope_module', _I + 'team_forecast_build_envelope\n'), ('policy_module', _F + 'crypto_btc_evidence_policy import evaluate_crypto_btc_evidence\n'),
    ('service_module', _I + 'crypto_btc_forecast_service\n'), ('temporal_module', _I + 'team_evidence_aggregation_temporal\n'), ('witness_module', _I + 'team_evidence_aggregation_witness\n'), ('codec_module', _I + 'team_evidence_aggregation_codec\n'),
    ('config_module', _F + 'supabase_team_evidence_aggregation_config import SupabaseTeamEvidenceAggregationConfig\n'), ('dsn_module', _F + 'supabase_local_dsn import validate_local_postgres_dsn\n'), ('strategy_cycle_module', _I + 'strategy_cycle\n'), ('cli_module', _I + 'cli\n'),
    ('cost_module', _F + 'cost_aware_event_strategy import build_paper_cost_aware_event_strategy_report\n'), ('prefix_extension', _I + 'team_evidence_aggregation_attempt_store_extra\n'), ('package_root_import', 'import polymarket_alpha_lab\n'), ('package_root_importfrom', 'from polymarket_alpha_lab import TeamEvaluationAttemptDbRow\n'),
    ('relative_import', 'from .team_evidence_aggregation_attempt_store import load_latest_team_evaluation_attempt\n'), ('relative_empty_module', 'from . import typing\n'), ('wildcard_import', 'from typing import *\n'), ('wildcard_future', 'from __future__ import *\n'), ('stdlib_os', 'import os\n'),
    ('stdlib_json', 'import json\n'), ('stdlib_re', 'import re\n'), ('stdlib_hashlib', 'import hashlib\n'), ('stdlib_subprocess', 'import subprocess\n'), ('stdlib_pathlib', 'import pathlib\n'), ('stdlib_importlib', 'import importlib\n'), ('forbidden_alias', 'import datetime as subprocess\n'),
    ('forbidden_member', 'from datetime import wallet\n'), ('forbidden_member_underscore', 'from typing import _private_wallet_helper\n'),)
REJECT_SNIPPETS = (
    ('identifier_name', 'value = wallet\n'), ('identifier_attribute', 'value = record.private_key\n'), ('identifier_function', 'def socket_reader():\n    return None\n'), ('identifier_async_function', 'async def wallet_loader():\n    return None\n'), ('identifier_class', 'class Wallet:\n    pass\n'),
    ('identifier_argument', 'def load(credential_material):\n    return credential_material\n'), ('identifier_keyword', 'compute(wallet_id=1)\n'), ('identifier_global', 'global order_book\n'), ('identifier_nonlocal', 'def outer():\n    def inner():\n        nonlocal order_book\n'),
    ('identifier_except_name', 'try:\n    pass\nexcept ValueError as token_store:\n    pass\n'), ('identifier_import_asname', 'import datetime as subprocess\n'), ('identifier_importfrom_member', 'from datetime import credential_token\n'), ('identifier_environ', 'value = os.environ\n'),
    ('identifier_persistence', 'def persist_result():\n    return None\n'), ('identifier_store_surface', 'value = team_forecast_store_rows\n'), ('identifier_db_surface', 'def probe(db_row):\n    return db_row\n'), ('identifier_execute', 'def execute_write():\n    return None\n'),
    ('identifier_strategy_cycle', 'strategy_cycle_input = 1\n'), ('identifier_cycle_strategy', 'def _cycle_strategy_inputs():\n    return None\n'), ('identifier_cost', 'cost_hint = 1\n'), ('identifier_rank', 'rank_rows = 1\n'), ('identifier_recommendation', 'recommended_side = None\n'),
    ('identifier_side_selection', 'side_selection = 1\n'), ('identifier_select_side', 'def _select_side(evaluation):\n    return None\n'), ('identifier_choose_side', 'def _choose_side(evaluation):\n    return None\n'), ('identifier_build_packet', 'def _build_packet_wrapper():\n    return None\n'),
    ('call_open', 'descriptor = open("attempts.jsonl")\n'), ('call_print', 'print("message")\n'), ('call_input', 'value = input()\n'), ('call_eval', 'value = eval("expression")\n'), ('call_exec', 'exec("statement")\n'), ('call_compile', 'value = compile("source", "source", "exec")\n'),
    ('call_dynamic_import', 'module = __import__("os")\n'), ('call_hash', 'value = hash(record)\n'), ('call_random', 'value = random()\n'), ('call_randint', 'value = randint(0, 9)\n'), ('call_float', 'value = float(record)\n'), ('call_repr', 'text = repr(record)\n'),
    ('call_getenv_bare', 'value = getenv("DSN_ENV")\n'), ('call_getenv_attr', 'value = os.getenv("DSN_ENV")\n'), ('call_read_text', 'value = handle.read_text()\n'), ('call_write_bytes', 'value = handle.write_bytes(data)\n'), ('call_now', 'value = datetime.now()\n'), ('call_alias_utcnow', 'import datetime as clock\nvalue = clock.utcnow()\n'),
    ('call_terminal_today', 'stamp = schedule.today()\n'), ('call_terminal_monotonic', 'value = timer.monotonic()\n'), ('call_terminal_timestamp', 'value = record.attempted_at.timestamp()\n'), ('call_terminal_total_seconds', 'value = record.delta.total_seconds()\n'), ('call_terminal_time_ns', 'value = timer.time_ns()\n'),
    ('surface_float_literal', 'ratio = 0.5\n'), ('surface_float_scientific', 'value = 1e-6\n'), ('surface_float_annotation', 'ratio: float = 0\n'), ('surface_float_reference', 'kind = float\n'),
    ('surface_broad_exception', 'try:\n    pass\nexcept Exception:\n    pass\n'), ('surface_broad_base_exception', 'try:\n    pass\nexcept BaseException as error:\n    pass\n'),
    ('sql_insert', 'statement = "insert into team_evaluation_attempts (tea_id) values (%s)"\n'), ('sql_select', 'query = "select tea_id, tfr_id from team_evaluation_attempts"\n'), ('sql_update', 'statement = "update team_evaluation_attempts set status = %s"\n'), ('sql_delete', 'statement = "delete from team_evaluation_attempts where tea_id = %s"\n'),
    ('sql_on_conflict', 'clause = "on conflict (tea_id) do nothing"\n'), ('sql_create_table', 'statement = "create table team_evaluation_attempts (tea_id text)"\n'), ('dsn_constant', 'uri = "postgresql://user:secret@localhost:54322/postgres"\n'), ('dsn_password', 'pair = "password=hunter2"\n'),
    ('dsn_fstring', 'target = f"{caller_dsn}?sslmode=require"\n'), ('dsn_concat', 'target = caller_dsn + "?sslmode=require"\n'), ('dsn_format', 'target = "{}?sslmode=require".format(caller_dsn)\n'), ('dsn_join', 'target = "".join((caller_dsn, "?sslmode=require"))\n'),
    ('side_yes_token', 'picked = "YES"\n'), ('side_no_token', 'picked = "no"\n'), ('side_yes_mixed', 'value = "Yes"\n'), ('strategy_cycle_string', 'label = "strategy_cycle_report"\n'), ('strategy_cycle_fstring', 'label = f"{strategy_cycle}_report"\n'),
    ('packet_construction', 'packet = TeamForecastPacket(condition_id=condition_id)\n'), ('packet_legacy_construction', 'legacy = legacy_forecast_packet(scope=scope)\n'), ('envelope_construction', 'envelope = build_team_forecast_build_envelope(result=aggregation_result)\n'), ('packet_payload_call', 'encoded = team_forecast_packet_payload(packet)\n'),
    ('store_writer_call', 'rows = insert_team_evaluation_attempt(connection, row)\n'), ('adapter_writer_call', 'rows = insert_team_evaluation_attempts_with_psycopg(dsn, envelopes)\n'), ('rows_loader_call', 'rows = load_team_evaluation_attempt_rows(connection, tfr_id=tfr_id)\n'), ('rows_loader_attribute_call', 'rows = store.load_team_evaluation_attempt_rows(connection)\n'),
    ('dsn_validator_call', 'validate_local_postgres_dsn(dsn, env_var_name="X")\n'), ('to_db_row_call', 'row = team_evaluation_attempt_to_db_row(tea_id=tea_id)\n'), ('row_parameters_call', 'params = team_evaluation_attempt_row_parameters(row)\n'),)
ALLOW_SNIPPETS = (
    ('store_loader_call', 'row = load_latest_team_evaluation_attempt(connection, tfr_id=tfr_id, scope_version=scope_version, scope_key=scope_key, table_name=table_name)\n'),
    ('adapter_loader_call', 'row = load_latest_team_evaluation_attempt_with_psycopg(dsn, tfr_id=tfr_id, scope_version=scope_version, scope_key=scope_key, table_name=table_name)\n'),
    ('row_type_reference', 'row_type = TeamEvaluationAttemptDbRow\n'), ('payload_keys_reference', 'keys = TEAM_EVALUATION_ATTEMPT_PAYLOAD_KEYS\n'), ('status_values_reference', 'values = TEAM_EVALUATION_ATTEMPT_STATUS_VALUES\n'), ('gate_key_string', 'gate = run_metadata.get("external_publication_gate")\n'),
    ('packet_key_check', 'injected = "legacy_forecast_packet" in payload\n'), ('selected_side_key_check', 'if "selected_side" in payload:\n    raise ValueError("packet-shaped key")\n'), ('status_literals', 'state = "ready"\nwatch_state = "watch"\nblocked_state = "blocked"\n'), ('presence_literals', 'presence = "projected"\nsuppressed = "suppressed"\n'),
    ('absence_reason_literal', 'absence_reason = "no_matching_attempt"\n'), ('decimal_parse', 'probability = Decimal("0.123456")\n'), ('audit_field_annotations', 'audit_packet_selected_side: str | None = None\naudit_packet_forecast_probability_yes: Decimal | None = None\n'), ('dsn_local_passthrough', 'target_dsn = caller_dsn\n'), ('table_name_default', 'table_name = "team_evaluation_attempts"\n'),
    ('boundary_docstring', '"""This report module never selects a strategy side, ranks attempts, or wires strategy_cycle."""\n'),
    ('report_construction', 'report = TeamEvaluationAttemptLatestReadReport(attempt_present=True, absence_reason=None, reason_codes=(), publication_gate_reason_codes=())\n'),)
FUTURE_IMPORT = "from __future__ import annotations\n"
E = READ_EXPORTS[1]
OK_DEF = f"def {E}() -> None:\n    return None\n"
OK_ALL = f'__all__ = ("{E}",)\n'
SINGLE, PAIR_DEFS = (E,), "def alpha():\n    return None\n\n\ndef beta():\n    return None\n"
_KW = "*, tfr_id=None, scope_version=None, scope_key=None"


def _export_case(all_expr: str, extra: str = "", definition: str = OK_DEF) -> str:
    return FUTURE_IMPORT + all_expr + definition + extra


EXPORT_CASES = (
    ('clean', _export_case(OK_ALL), True, SINGLE), ('ordered_pair_pass', _export_case('__all__ = ("alpha", "beta")\n', PAIR_DEFS), True, ('alpha', 'beta')), ('reordered_pair', _export_case('__all__ = ("beta", "alpha")\n', PAIR_DEFS), False, ('alpha', 'beta')),
    ('list_not_tuple', _export_case(f'__all__ = ["{E}"]\n'), False, SINGLE), ('duplicate_entry', _export_case(f'__all__ = ("{E}", "{E}")\n'), False, SINGLE), ('extra_entry', _export_case(f'__all__ = ("{E}", "extra")\n'), False, SINGLE),
    ('missing_entry', _export_case('__all__ = ()\n'), False, SINGLE), ('non_string_element', _export_case(f'__all__ = ({E},)\n'), False, SINGLE), ('second_assignment', _export_case(OK_ALL, OK_ALL), False, SINGLE),
    ('augmented_assignment', _export_case(OK_ALL, '__all__ += ("extra",)\n'), False, SINGLE), ('assignment_binding', _export_case(OK_ALL, f'{E} = None\n'), False, SINGLE), ('conditional_rebind', _export_case(OK_ALL, f'if True:\n    {E} = None\n'), False, SINGLE),
    ('conditional_all_rebind', _export_case(OK_ALL, 'if True:\n    __all__ = ("other",)\n'), False, SINGLE), ('chained_all_rebind', _export_case(f'__all__ = {E} = ("{E}",)\n'), False, SINGLE), ('unpacked_all_rebind', _export_case(f'__all__ = (__all__,) = ("{E}",)\n'), False, SINGLE),
    ('walrus_binding', _export_case(OK_ALL, f'if ({E} := 1):\n    pass\n'), False, SINGLE), ('def_name_binding', _export_case(OK_ALL, 'def __all__():\n    return None\n'), False, SINGLE), ('import_binding', _export_case(f'from typing import {E}\n' + OK_ALL), False, SINGLE),
    ('nested_import_binding', _export_case(OK_ALL, f'def wrapper():\n    from typing import {E}\n'), False, SINGLE), ('nested_definition', _export_case(OK_ALL, f'def wrapper():\n    def {E}():\n        return None\n    return wrapper\n'), False, SINGLE), ('async_kind', _export_case(OK_ALL, f'async def {E}():\n    return None\n'), False, SINGLE),
    ('class_kind', _export_case(OK_ALL, '', f'class {E}:\n    pass\n'), False, SINGLE),)
_SAMPLE_CLASS = ("@dataclass(frozen=True, slots=True)\nclass Sample:\n    paper_only: bool = True\n    report_only: bool = True\n    readonly: bool = True\n")
CLASS_MUTATIONS = (
    ('missing_dataclass', '@dataclass(frozen=True, slots=True)\n', ''), ('missing_slots', '@dataclass(frozen=True, slots=True)', '@dataclass(frozen=True)'), ('nonliteral_decorator_flag', 'frozen=True', 'frozen="True"'),
    ('extra_decorator_keyword', 'slots=True)', 'slots=True, kw_only=True)'), ('flag_false', 'readonly: bool = True', 'readonly: bool = False'), ('flag_missing', '    readonly: bool = True\n', ''), ('flag_wrong_annotation', 'paper_only: bool', 'paper_only: object'),
    ('flag_no_default', 'paper_only: bool = True', 'paper_only: bool'),)
CLASS_TOLERANCE_CASES = (
    ('with_final_decorator', "@final\n" + _SAMPLE_CLASS),
    ('with_seal_method', _SAMPLE_CLASS.replace('    readonly: bool = True\n', '    readonly: bool = True\n\n    def __init_subclass__(cls) -> None:\n        raise TypeError("sealed")\n')),
    ('with_sealed_base', "class _Sealed:\n    def __init_subclass__(cls) -> None:\n        raise TypeError(\"x\")\n\n" + _SAMPLE_CLASS.replace("class Sample:", "class Sample(_Sealed):")),)
DELEGATION_CASES = (
    ('clean_both', _READER_BODY + _READER_PSVCOPG_BODY, True), ('missing_psycopg_delegation', _READER_BODY, False),
    ('wrong_loader', _READER_BODY + "def read_latest_team_evaluation_attempt_report_with_psycopg(dsn):\n    return load_latest_team_evaluation_attempt(dsn)\n", False),
    ('plain_reader_calls_adapter', "def read_latest_team_evaluation_attempt_report(connection):\n    return load_latest_team_evaluation_attempt_with_psycopg(connection)\n" + _READER_PSVCOPG_BODY, False),
    ('both_loaders', "def read_latest_team_evaluation_attempt_report(connection):\n    load_latest_team_evaluation_attempt(connection)\n    return load_latest_team_evaluation_attempt_with_psycopg(connection)\n" + _READER_PSVCOPG_BODY, False),
    ('attribute_call_only', "def read_latest_team_evaluation_attempt_report(connection):\n    return store.load_latest_team_evaluation_attempt(connection)\n" + _READER_PSVCOPG_BODY, False),)
SIGNATURE_CASES = (
    ('clean', _READER_BODY, True), ('missing_keyword', "def f(connection):\n    return None\n", False), ('extra_keyword', f'def f(connection, {_KW}, table_name="team_evaluation_attempts", limit=None):\n    return None\n', False),
    ('vararg', "def f(connection, *args):\n    return None\n", False), ('wrong_first_param', f'def f(cursor, {_KW}, table_name="team_evaluation_attempts"):\n    return None\n', False), ('wrong_default', f'def f(connection, {_KW}, table_name=None):\n    return None\n', False),
    ('wrong_return', f'def f(connection, {_KW}, table_name="team_evaluation_attempts") -> object:\n    return None\n', False),
    ('constant_default_ok', f'_DEFAULT_TABLE_NAME = "{DEFAULT_TABLE_NAME}"\ndef f(connection, {_KW}, table_name=_DEFAULT_TABLE_NAME) -> TeamEvaluationAttemptLatestReadReport:\n    return None\n', True),
    ('constant_default_wrong', f'_DEFAULT_TABLE_NAME = "other_attempts"\ndef f(connection, {_KW}, table_name=_DEFAULT_TABLE_NAME) -> TeamEvaluationAttemptLatestReadReport:\n    return None\n', False),)
PACKAGE_ROOT_CLEAN_CASE = "import decimal\nif True:\n    value = 1\n__all__ = (\"MarketScore\",)\n"
PACKAGE_ROOT_REJECT_CASES = (
    ('conditional_import', "if True:\n    from polymarket_alpha_lab.team_evaluation_attempt_latest_read import TeamEvaluationAttemptLatestReadReport\n"),
    ('nested_import', "def helper():\n    from polymarket_alpha_lab.team_evaluation_attempt_latest_read import read_latest_team_evaluation_attempt_report\n"), ('module_import', 'import polymarket_alpha_lab.team_evaluation_attempt_latest_read\n'),
    ('conditional_assign', "if True:\n    read_latest_team_evaluation_attempt_report = None\n"), ('package_all_listing', '__all__ = ("TeamEvaluationAttemptLatestReadReport",)\n'),
    ('package_all_extra_listing', '__all__ = ("read_latest_team_evaluation_attempt_report_with_psycopg",)\n'),)


def _conforming_module() -> str:
    return "".join((BENIGN_IMPORTS, BENIGN_VARIANTS, _REPORT_CLASS, _READER_BODY, _READER_PSVCOPG_BODY, "__all__ = (\n" + "".join(f'    "{name}",\n' for name in READ_EXPORTS) + ")\n"))


def test_node_8_synthetic_import_export_surface_delegation_and_signature_gate() -> None:
    failures: list[str] = []
    for label, source in (("imports", BENIGN_IMPORTS), ("variants", BENIGN_VARIANTS), ("report_class", _REPORT_CLASS), ("reader_body", _READER_BODY), ("reader_psycopg_body", _READER_PSVCOPG_BODY)):
        if (found := _module_violations(source)): failures.append(f"benign {label} were rejected: {found}")
    if (found := _module_violations(_conforming_module(), exports=True, require_pinned=True)): failures.append(f"conforming synthetic reader module was rejected: {found}")
    if (found := _delegation_problems(ast.parse(_conforming_module()))): failures.append(f"conforming synthetic delegation was rejected: {found}")
    for label, source in (("reader", _READER_BODY), ("reader_psycopg", _READER_PSVCOPG_BODY)):
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef))
        if (found := _reader_signature_problems(node, "dsn" if label.endswith("psycopg") else "connection")): failures.append(f"synthetic {label} signature was rejected: {found}")
    report_node = next(n for n in ast.parse(_REPORT_CLASS).body if isinstance(n, ast.ClassDef))
    for label, problems in (("shape", _class_def_problems(report_node)), ("fields", _report_field_problems(report_node))):
        if problems: failures.append(f"synthetic report class {label} was rejected: {problems}")
    failures.extend(f"import case '{case}' was not rejected" for case, snippet in IMPORT_FAIL_CASES if not _module_violations(snippet))
    failures.extend(f"snippet case '{case}' was not rejected" for case, snippet in REJECT_SNIPPETS if not _module_violations(snippet))
    failures.extend(f"allowance case '{case}' was wrongly rejected: {found}" for case, snippet in ALLOW_SNIPPETS if (found := _module_violations(snippet)))
    for case, source, must_pass in DELEGATION_CASES:
        found = _delegation_problems(ast.parse(source))
        if must_pass and found: failures.append(f"delegation case '{case}' was wrongly rejected: {found}")
        if not must_pass and not found: failures.append(f"delegation case '{case}' was not rejected")
    for case, source, must_pass in SIGNATURE_CASES:
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
        found = _reader_signature_problems(node, "connection", _module_string_constants(tree))
        if must_pass and found: failures.append(f"signature case '{case}' was wrongly rejected: {found}")
        if not must_pass and not found: failures.append(f"signature case '{case}' was not rejected")
    for case, source, must_pass, expected in EXPORT_CASES:
        found = _module_violations(source, exports=True, expected=expected)
        if must_pass and found: failures.append(f"export case '{case}' was wrongly rejected: {found}")
        if not must_pass and not found: failures.append(f"export case '{case}' was not rejected")
    for label, old, new in CLASS_MUTATIONS:
        if not _class_def_problems(next(n for n in ast.parse(_SAMPLE_CLASS.replace(old, new)).body if isinstance(n, ast.ClassDef))): failures.append(f"class-shape mutation '{label}' was not rejected")
    for label, source in CLASS_TOLERANCE_CASES:
        if (found := _class_def_problems(next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "Sample"))): failures.append(f"class-shape tolerance case '{label}' was wrongly rejected: {found}")
    if not _report_field_problems(next(n for n in ast.parse(_REPORT_CLASS.replace("    packet_presence: str | None\n", "")).body if isinstance(n, ast.ClassDef))): failures.append("report field mutation 'missing_field' was not rejected")
    assert not failures, "synthetic guard failures:\n" + "\n".join(failures)


def test_node_8_real_module_lines_imports_exports_delegation_and_package_root() -> None:
    violations: list[str] = []
    found_production = {p.name for p in PRODUCTION_DIR.glob("team_evaluation_attempt_latest_read*.py")}
    if PRODUCTION_FILE not in found_production: violations.append(f"{PRODUCTION_FILE}: required Node 8 production module is missing (pending-red until the module worker lands)")
    violations.extend(f"{extra}: extra team_evaluation_attempt_latest_read* production module outside the Node 8 allowlist" for extra in sorted(found_production - {PRODUCTION_FILE}))
    found_tests = {p.name for p in TEST_DIR.glob("test_team_evaluation_attempt_latest_read*.py")}
    violations.extend(f"{name}: required Node 8 test module is missing (behavior tests pending-red until the behavior worker lands)" for name in sorted(set(TEST_LINE_LIMITS) - found_tests))
    violations.extend(f"{extra}: extra test_team_evaluation_attempt_latest_read* test module outside the Node 8 allowlist" for extra in sorted(found_tests - set(TEST_LINE_LIMITS)))
    counts: dict[str, int] = {}
    for name, ceiling in TEST_LINE_LIMITS.items():
        if not (path := TEST_DIR / name).is_file(): continue
        counts[name] = (count := len(path.read_text(encoding="utf-8").splitlines()))
        if count > ceiling: violations.append(f"{name}: {count} physical lines exceed ceiling {ceiling}")
    if len(counts) == len(TEST_LINE_LIMITS) and sum(counts.values()) > NODE_8_TEST_TOTAL_LINE_LIMIT:
        violations.append(f"Node 8 test total {sum(counts.values())} exceeds {NODE_8_TEST_TOTAL_LINE_LIMIT} lines")
    if PRODUCTION_PATH.is_file():
        tree = ast.parse(source := PRODUCTION_PATH.read_text(encoding="utf-8"))
        if (count := len(source.splitlines())) > PRODUCTION_LINE_LIMIT: violations.append(f"{PRODUCTION_FILE}: {count} physical lines exceed ceiling {PRODUCTION_LINE_LIMIT}")
        violations.extend(f"{PRODUCTION_FILE}: {item}" for item in _module_violations(source, exports=True, require_pinned=True))
        violations.extend(f"{PRODUCTION_FILE}: {item}" for item in _delegation_problems(tree))
        constants, functions, classes = _module_string_constants(tree), {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}, {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}
        for name, first, _own in READER_DELEGATION:
            node = functions.get(name)
            if node is None: violations.append(f"{PRODUCTION_FILE}: {name} must be a direct function definition")
            else: violations.extend(f"{PRODUCTION_FILE}: {item}" for item in _reader_signature_problems(node, first, constants))
        report_node = classes.get(READ_EXPORTS[0])
        if report_node is None: violations.append(f"{PRODUCTION_FILE}: {READ_EXPORTS[0]} must be a direct class definition")
        else: violations.extend(f"{PRODUCTION_FILE}: {item}" for item in _class_def_problems(report_node) + _report_field_problems(report_node))
    forbidden_root_names = set(READ_EXPORTS) | {PRODUCTION_IMPORT}
    root_bound = _package_root_bound_names(ast.parse((PRODUCTION_DIR / "__init__.py").read_text(encoding="utf-8")))
    violations.extend(f"package root must not bind Node 8 export or module name '{name}'" for name in sorted(root_bound & forbidden_root_names))
    assert not (_package_root_bound_names(ast.parse(PACKAGE_ROOT_CLEAN_CASE)) & forbidden_root_names), "clean package-root synthetic was rejected"
    violations.extend(f"package-root case '{case}' was not rejected" for case, snippet in PACKAGE_ROOT_REJECT_CASES if not (_package_root_bound_names(ast.parse(snippet)) & forbidden_root_names))
    if PRODUCTION_PATH.is_file() and not (root_bound & forbidden_root_names):
        root = importlib.import_module("polymarket_alpha_lab")
        assert all(getattr(root, name, None) is None for name in READ_EXPORTS), "package root leaked a Node 8 export at runtime"
    assert not violations, "\n".join(violations)


def test_node_8_real_report_class_runtime_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN", raising=False)
    assert PRODUCTION_PATH.is_file(), f"{PRODUCTION_FILE}: required Node 8 production module is missing (pending-red until the module worker lands)"
    module = importlib.import_module(PRODUCTION_IMPORT)
    assert tuple(module.__all__) == READ_EXPORTS
    public_class = getattr(module, READ_EXPORTS[0])
    assert public_class.__dataclass_params__.frozen is True and public_class.__dataclass_params__.slots is True
    assert tuple(field.name for field in dataclasses.fields(public_class)) == REPORT_FIELDS
    assert {field.name: field.default for field in dataclasses.fields(public_class) if field.name in HARD_FLAG_NAMES} == dict.fromkeys(HARD_FLAG_NAMES, True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        object.__new__(public_class).paper_only = False
