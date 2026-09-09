"""Node 7 child-local AST, import/export, forbidden-surface, injection-seam, package-root, and size guard.

Enforces the single Node 7 production module ``crypto_btc_forecast_service.py`` (orchestration only): a curated standard-library allowlist plus exactly
the plan's predecessor modules (Node 6 policy/resolution, Node 2C reducer and types, Node 3 envelope and packet types, the Node 4 config, and Node 5's
adapter bound only through the pinned plural writer), the exact three-name ``__all__`` with anywhere-binding rebinding protection, frozen/slotted/hard-flagged
dataclasses, keyword-only ``evaluator``/``writer`` seams that may bind only the pinned predecessor defaults, no SQL/env/filesystem/network/clock/randomness/
floats/``hash()``/broad-except/``print``, no side-selection or strategy-cycle consumption, DSN pass-through only, the exact package-root export trio, and
every Node 7 ceiling (pending-red fail-closed while the parallel workers are missing).
"""
from __future__ import annotations

import ast
import dataclasses
import importlib
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIR, TEST_DIR = REPO_ROOT / "src" / "polymarket_alpha_lab", REPO_ROOT / "tests"
PRODUCTION_FILE = "crypto_btc_forecast_service.py"
PRODUCTION_PATH = PRODUCTION_DIR / PRODUCTION_FILE
PRODUCTION_IMPORT = "polymarket_alpha_lab.crypto_btc_forecast_service"
PRODUCTION_LINE_LIMIT = 700
TEST_LINE_LIMITS = {"test_crypto_btc_forecast_service.py": 900, "test_crypto_btc_forecast_service_integration.py": 950, "test_crypto_btc_forecast_service_scope.py": 550}
NODE_7_TEST_TOTAL_LINE_LIMIT = 2_400
ADAPTER_MODULE = "polymarket_alpha_lab.team_evidence_aggregation_attempt_psycopg"
POLICY_MODULE = "polymarket_alpha_lab.crypto_btc_evidence_policy"
PINNED_WRITER = "insert_team_evaluation_attempts_with_psycopg"
PINNED_EVALUATOR = "evaluate_crypto_btc_evidence"
PINNED_SEAM_NAMES = frozenset((PINNED_WRITER, PINNED_EVALUATOR))
IMPORT_ALLOWLIST = frozenset((
    "__future__", "dataclasses", "datetime", "typing", "polymarket_alpha_lab.crypto_btc_evidence_policy",
    "polymarket_alpha_lab.crypto_btc_evidence_resolution", "polymarket_alpha_lab.team_evidence_aggregation",
    "polymarket_alpha_lab.team_evidence_aggregation_types", "polymarket_alpha_lab.team_forecast_build_envelope",
    "polymarket_alpha_lab.team_forecast_packet", "polymarket_alpha_lab.supabase_team_evidence_aggregation_config", ADAPTER_MODULE))
SERVICE_EXPORTS = ("CryptoBtcForecastServiceInput", "CryptoBtcForecastServiceResult", "evaluate_and_persist_crypto_btc_forecast")
SERVICE_CLASS_EXPORTS = frozenset(("CryptoBtcForecastServiceInput", "CryptoBtcForecastServiceResult"))
HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
FORBIDDEN_COMPONENTS = frozenset((
    "account", "accounts", "aiohttp", "api", "argparse", "argv", "auth", "authenticate", "authentication", "browser",
    "cache", "caches", "cached", "cancel", "cli", "client", "click", "credential", "credentials", "csv", "cursor",
    "db", "database", "duckdb", "environ", "execute", "execution", "exchange", "external", "file", "files", "filename",
    "filepath", "fork", "getenv", "getopt", "http", "https", "importlib", "jsonl", "log", "logs", "logger", "logging",
    "migration", "migrate", "mkdir", "mkdtemp", "mkstemp", "mongo", "mongodb", "mutate", "mutation", "mysql", "os",
    "order", "orders", "password", "passwords", "pathlib", "popen", "postgres", "postgresql", "process", "processes",
    "putenv", "random", "randomize", "redis", "remove", "request", "requests", "scrape", "scraper", "scrapers",
    "scraping", "secret", "secrets", "seed", "selenium", "sign", "signing", "signature", "signatures", "socket",
    "sockets", "spawn", "sql", "sqlalchemy", "sqlite", "stdin", "stdout", "stderr", "store", "stores", "storage",
    "subprocess", "submit", "submission", "system", "tempfile", "token", "tokens", "typer", "urllib", "wallet",
    "wallets", "websocket", "websockets"))
FORBIDDEN_SINGLES = FORBIDDEN_COMPONENTS | {"side", "sides"}
FORBIDDEN_SEQUENCES = (
    ("live", "trading"), ("trading", "live"), ("private", "key"), ("hosted", "account"), ("read", "text"), ("read", "bytes"),
    ("write", "text"), ("write", "bytes"), ("exchange", "mutate"), ("exchange", "mutation"), ("select", "side"),
    ("side", "select"), ("side", "selection"), ("selection", "side"), ("choose", "side"), ("pick", "side"),
    ("strategy", "cycle"), ("cycle", "strategy"))
FORBIDDEN_EXACT_NAMES = frozenset((
    "insert_team_evaluation_attempt", "load_latest_team_evaluation_attempt", "load_team_evaluation_attempt_rows",
    "_insert_attempt_rows_atomic", "insert_team_evaluation_attempt_with_psycopg", "persist_team_evaluation_attempts_with_psycopg",
    "TeamEvaluationAttemptDbRow", "TeamEvaluationAttemptWriteResult", "TEAM_EVALUATION_ATTEMPT_COLUMNS",
    "team_evaluation_attempt_to_db_row", "team_evaluation_attempt_row_parameters", "validate_local_postgres_dsn"))
FORBIDDEN_BARE_CALLS = frozenset((
    "open", "print", "input", "eval", "exec", "compile", "__import__", "hash", "float", "repr", "random", "randint",
    "randrange", "choice", "choices", "shuffle", "sample", "uniform", "gauss", "seed", "getrandbits", "randbytes", "getenv", "putenv"))
FORBIDDEN_CALL_TERMINALS = frozenset((
    "now", "utcnow", "today", "timestamp", "total_seconds", "time", "time_ns", "monotonic", "monotonic_ns", "perf_counter",
    "perf_counter_ns", "clock", "gmtime", "localtime", "ctime", "asctime"))
SQL_STATEMENT_PATTERNS = tuple(re.compile(p, re.IGNORECASE | re.DOTALL) for p in (
    r"\binsert\s+into\b", r"\bselect\b.+\bfrom\b", r"\bupdate\b.+\bset\b", r"\bdelete\s+from\b", r"\bmerge\s+into\b",
    r"\bon\s+conflict\b", r"\bcreate\s+table\b", r"\balter\s+table\b", r"\btruncate\s+table\b"))
SIDE_STRING_VALUES, STRATEGY_CYCLE_MARKERS, DSN_STRING_MARKERS = frozenset(("yes", "no")), ("strategy_cycle", "strategy-cycle"), ("://", "password=")
SEAM_WRITER_PARTS, SEAM_EVALUATOR_PARTS, SEAM_RECEIPT_PARTS = frozenset(("writer", "writers")), frozenset(("evaluator", "evaluators")), frozenset(("receipt", "receipts"))


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
        elif isinstance(node, ast.Attribute): found.append((node.lineno, node.attr))
        elif isinstance(node, ast.Name): found.append((node.lineno, node.id))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): found.append((node.lineno, node.name))
        elif isinstance(node, ast.arg): found.append((node.lineno, node.arg))
        elif isinstance(node, ast.keyword) and node.arg is not None: found.append((node.lineno, node.arg))
        elif isinstance(node, ast.ExceptHandler) and node.name is not None: found.append((node.lineno, node.name))
        elif isinstance(node, (ast.Global, ast.Nonlocal)): found.extend((node.lineno, entry) for entry in node.names)
    return found


def _docstring_constant_ids(tree: ast.Module) -> set[int]:
    """Docstrings may state the deferred strategy-cycle boundary in prose; code identifiers and constants may not."""
    statements = [n for n in tree.body if isinstance(n, ast.Expr)] + [s for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) for s in n.body
                      if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)]
    return {id(s.value) for s in statements if isinstance(s.value, ast.Constant) and isinstance(s.value.value, str)}


def _identifier_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for lineno, identifier in _semantic_identifiers(tree):
        if identifier in FORBIDDEN_EXACT_NAMES:
            violations.append(f"line {lineno}: forbidden persistence-surface identifier '{identifier}'")
            continue
        parts = _components(identifier)
        hits = [part for part in parts if part in FORBIDDEN_SINGLES]
        hits.extend("-".join(s) for s in FORBIDDEN_SEQUENCES for i in range(len(parts) - len(s) + 1) if parts[i:i + len(s)] == s)
        if hits: violations.append(f"line {lineno}: forbidden identifier '{identifier}' ({', '.join(hits)})")
    return violations


def _import_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == ADAPTER_MODULE: violations.append(f"line {node.lineno}: the adapter must be imported only via the pinned writer member")
                elif a.name not in IMPORT_ALLOWLIST: violations.append(f"line {node.lineno}: module '{a.name}' is not in the Node 7 allowlist")
        elif isinstance(node, ast.ImportFrom):
            if node.level != 0 or not node.module: violations.append(f"line {node.lineno}: relative or empty-module import")
            elif node.module not in IMPORT_ALLOWLIST: violations.append(f"line {node.lineno}: module '{node.module}' is not in the Node 7 allowlist")
            violations.extend(f"line {node.lineno}: wildcard import" for a in node.names if a.name == "*")
            violations.extend(f"line {node.lineno}: adapter member '{a.asname or a.name}' is not the plain pinned default writer binding" for a in node.names if node.module == ADAPTER_MODULE and a.name != "*" and (a.name != PINNED_WRITER or a.asname is not None))
    return violations


def _call_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call): continue
        func = node.func
        terminal = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if isinstance(func, ast.Name) and func.id in FORBIDDEN_BARE_CALLS: violations.append(f"line {func.lineno}: forbidden call '{func.id}()'")
        if terminal in FORBIDDEN_CALL_TERMINALS: violations.append(f"line {func.lineno}: forbidden ambient-clock call '{terminal}()'")
        if terminal in PINNED_SEAM_NAMES: violations.append(f"line {func.lineno}: pinned default '{terminal}' must be invoked only through its injection seam")
    return violations


def _surface_violations(tree: ast.Module) -> list[str]:
    violations: list[str] = []
    docstrings = _docstring_constant_ids(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            if type(node.value) is float: violations.append(f"line {node.lineno}: float literal")
            elif isinstance(node.value, str):
                if any(p.search(node.value) for p in SQL_STATEMENT_PATTERNS): violations.append(f"line {node.lineno}: SQL statement text in an orchestration module")
                elif any(m in node.value for m in DSN_STRING_MARKERS): violations.append(f"line {node.lineno}: credential-bearing or DSN-shaped string constant")
                elif node.value.lower() in SIDE_STRING_VALUES: violations.append(f"line {node.lineno}: YES/NO side token constant")
                elif id(node) not in docstrings and any(m in node.value for m in STRATEGY_CYCLE_MARKERS): violations.append(f"line {node.lineno}: strategy-cycle token constant")
        elif isinstance(node, ast.Name) and node.id == "float": violations.append(f"line {node.lineno}: float annotation, call, or reference")
        elif isinstance(node, ast.ExceptHandler) and node.type is not None and {item.id for item in ast.walk(node.type) if isinstance(item, ast.Name)} & {"Exception", "BaseException"}: violations.append(f"line {node.lineno}: broad except handler")
        elif isinstance(node, ast.FormattedValue) and node.conversion == ord("r"): violations.append(f"line {node.lineno}: object repr conversion")
    return violations


def _references(node: ast.AST | None, identifier: str, *, by_component: bool = False) -> bool:
    if node is None: return False
    def has(text: str) -> bool:
        return identifier in _components(text) if by_component else text == identifier
    return any((isinstance(n, ast.Name) and has(n.id)) or (isinstance(n, ast.Attribute) and has(n.attr)) for n in ast.walk(node))


def _dsn_construction_violations(tree: ast.Module) -> list[str]:
    """The DSN is only ever passed through from the persistence config, never built or interpolated."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr) and _references(node, "dsn", by_component=True):
            violations.append(f"line {node.lineno}: DSN must only be passed through, never interpolated")
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)) and _references(node, "dsn", by_component=True): violations.append(f"line {node.lineno}: DSN must only be passed through, never concatenated or %-formatted")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("format", "join") and _references(node, "dsn", by_component=True): violations.append(f"line {node.lineno}: DSN must only be passed through, never built via '{node.func.attr}'")
    return violations


def _seam_value_violations(tree: ast.Module) -> list[str]:
    """Writer/evaluator-named bindings may hold only expressions referencing the pinned predecessor default, or None."""
    violations: list[str] = []
    for node in ast.walk(tree):
        targets: list[ast.expr] = list(node.targets) if isinstance(node, ast.Assign) else [node.target] if isinstance(node, (ast.AnnAssign, ast.NamedExpr)) else []
        for target in targets:
            for name_node in ast.walk(target):
                if not (isinstance(name_node, ast.Name) and isinstance(name_node.ctx, ast.Store)): continue
                parts = set(_components(name_node.id))
                is_writer = bool(parts & SEAM_WRITER_PARTS)
                is_evaluator = bool(parts & SEAM_EVALUATOR_PARTS) and not (parts & SEAM_RECEIPT_PARTS)  # evaluator_receipts fields are data, not seams
                if not (is_writer or is_evaluator): continue
                pinned, role = (PINNED_WRITER, "writer") if is_writer else (PINNED_EVALUATOR, "evaluator")
                if _references(node.value, pinned): continue
                violations.append(f"line {node.lineno}: {role} seam '{name_node.id}' may only bind the pinned {role} default or None")
    return violations


def _pinned_seam_binding_violations(tree: ast.Module) -> list[str]:
    """The two pinned defaults may only be bound by their plain canonical module imports."""
    canonical = {(ADAPTER_MODULE, PINNED_WRITER), (POLICY_MODULE, PINNED_EVALUATOR)}
    allowed_alias_ids = {id(a) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level == 0
                         for a in n.names if a.asname is None and (n.module, a.name) in canonical}
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            violations.extend(f"line {node.lineno}: pinned default '{a.asname or a.name}' must be imported plainly from its pinned module" for a in node.names if (a.asname or a.name) in PINNED_SEAM_NAMES and id(a) not in allowed_alias_ids)
        elif isinstance(node, ast.Import):
            violations.extend(f"line {node.lineno}: pinned default must never be bound via a plain module import" for a in node.names if (a.asname or a.name.split(".")[0]) in PINNED_SEAM_NAMES)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in PINNED_SEAM_NAMES:
            violations.append(f"line {node.lineno}: pinned default '{node.id}' must never be rebound")
        elif isinstance(node, ast.arg) and node.arg in PINNED_SEAM_NAMES:
            violations.append(f"line {node.lineno}: parameter '{node.arg}' shadows a pinned predecessor default")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in PINNED_SEAM_NAMES:
            violations.append(f"line {node.lineno}: definition '{node.name}' shadows a pinned predecessor default")
    return violations


def _required_seam_import_violations(tree: ast.Module) -> list[str]:
    present = {(n.module, a.name) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level == 0
               for a in n.names if a.asname is None and (n.module, a.name) in ((ADAPTER_MODULE, PINNED_WRITER), (POLICY_MODULE, PINNED_EVALUATOR))}
    return [f"the pinned {role} default '{name}' must be imported plainly from {module}"
            for module, name, role in ((ADAPTER_MODULE, PINNED_WRITER, "writer"), (POLICY_MODULE, PINNED_EVALUATOR, "evaluator")) if (module, name) not in present]


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
        want = ast.ClassDef if name in SERVICE_CLASS_EXPORTS else ast.FunctionDef
        anywhere = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name]
        direct = [n for n in tree.body if n in anywhere]
        if len(anywhere) != 1 or not direct or type(direct[0]) is not want: violations.append(f"export '{name}' requires exactly one module-level {'class definition' if want is ast.ClassDef else 'direct function definition'}")
    return violations


def _module_violations(source: str, *, exports: bool = False, expected: tuple[str, ...] | None = None, require_seams: bool = False) -> list[str]:
    tree = ast.parse(source)
    violations = (_import_violations(tree) + _identifier_violations(tree) + _call_violations(tree) + _surface_violations(tree)
                  + _dsn_construction_violations(tree) + _seam_value_violations(tree) + _pinned_seam_binding_violations(tree))
    if require_seams: violations += _required_seam_import_violations(tree)
    if exports: violations += _export_violations(tree, SERVICE_EXPORTS if expected is None else expected)
    return violations


def _class_def_problems(node: ast.ClassDef) -> list[str]:
    calls = [d for d in node.decorator_list if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass"]
    keywords = {k.arg: k.value for call in calls for k in call.keywords}
    problems: list[str] = []
    if len(calls) != 1 or set(keywords) != {"frozen", "slots"} or not all(isinstance(v, ast.Constant) and v.value is True for v in keywords.values()): problems.append("missing @dataclass(frozen=True, slots=True)")
    statements = {s.target.id: s for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)}
    for flag in HARD_FLAG_NAMES:
        statement = statements.get(flag)
        if statement is None or not (isinstance(statement.annotation, ast.Name) and statement.annotation.id == "bool") or not (isinstance(statement.value, ast.Constant) and statement.value.value is True): problems.append(f"{flag} must be 'bool' with a literal True default")
    return problems


def _service_callable_problems(node: ast.FunctionDef) -> list[str]:
    arguments = node.args
    problems: list[str] = []
    if arguments.posonlyargs or arguments.vararg or arguments.kwarg: problems.append("the service callable takes only plain and keyword-only parameters")
    if tuple(i.arg for i in arguments.args) != ("service_input",): problems.append("the only positional parameter is service_input")
    if tuple(i.arg for i in arguments.kwonlyargs) != ("evaluator", "writer"): problems.append("keyword-only parameters are exactly evaluator then writer")
    if arguments.args and (arguments.args[0].annotation is None or ast.unparse(arguments.args[0].annotation) != "CryptoBtcForecastServiceInput"): problems.append("service_input must be annotated CryptoBtcForecastServiceInput")
    for param, pinned in zip(arguments.kwonlyargs, (PINNED_EVALUATOR, PINNED_WRITER)):
        text = ast.unparse(param.annotation) if param.annotation is not None else ""
        if not (text.startswith("Callable[") and text.endswith("| None")): problems.append(f"{param.arg} must be annotated Callable[...] | None")
        default = arguments.kw_defaults[arguments.kwonlyargs.index(param)]
        if not (isinstance(default, ast.Constant) and default.value is None): problems.append(f"{param.arg} must default to None (the body binds the pinned {pinned})")
    if node.returns is None or ast.unparse(node.returns) != "CryptoBtcForecastServiceResult": problems.append("the return annotation must be CryptoBtcForecastServiceResult")
    return problems


def _package_root_bound_names(tree: ast.Module) -> set[str]:
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


def _package_root_problems(tree: ast.Module, service_names: set[str]) -> list[str]:
    problems: list[str] = []
    canonical = [n for n in tree.body if isinstance(n, ast.ImportFrom) and n.module == PRODUCTION_IMPORT]
    members = sorted(a.name for n in canonical for a in n.names)
    if len(canonical) != 1 or members != sorted(SERVICE_EXPORTS):
        problems.append(f"the package root must import exactly the three Node 7 service names from {PRODUCTION_IMPORT}")
    problems.extend(f"line {n.lineno}: package-root service import must not use aliases" for n in canonical for a in n.names if a.asname is not None)
    problems.extend(f"line {n.lineno}: the service module must be imported at module top level" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == PRODUCTION_IMPORT and n not in tree.body)
    problems.extend(f"line {n.lineno}: direct module import of the service module is not the export form" for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names if a.name == PRODUCTION_IMPORT)
    bound = _package_root_bound_names(tree)
    problems.extend(f"package root must bind service export '{name}'" for name in SERVICE_EXPORTS if name not in bound)
    problems.extend(f"package root leaks non-export Node 7 name '{name}'" for name in sorted(bound & (service_names - set(SERVICE_EXPORTS))))
    return problems


_I, _F = "import polymarket_alpha_lab.", "from polymarket_alpha_lab."
BENIGN_IMPORTS = (
    "from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime\nfrom typing import Callable, final\n"
    + _F + "crypto_btc_evidence_policy import CryptoBtcEvidenceEvaluation, CryptoBtcEvidenceInput, evaluate_crypto_btc_evidence\n"
    + _F + "crypto_btc_evidence_resolution import CryptoBtcIncidentGates, CryptoBtcResolutionContract\n"
    + _F + "team_evidence_aggregation import build_team_evidence_aggregation_result, validate_team_evidence_aggregation_result\n"
    + _F + "team_evidence_aggregation_types import TeamEvidenceAggregationInput, TeamEvidenceAggregationResult\n"
    + _F + "team_forecast_build_envelope import TeamForecastBuildEnvelope, TeamForecastEvaluatorReceipt, TeamForecastEvaluationScope, "
    "TeamForecastRunMetadata, build_team_forecast_build_envelope, validate_team_forecast_build_envelope\n"
    + _F + "team_forecast_packet import TeamForecastEvidencePacket, TeamForecastPacket\n"
    + _F + "supabase_team_evidence_aggregation_config import SupabaseTeamEvidenceAggregationConfig\n"
    + _F + "team_evidence_aggregation_attempt_psycopg import insert_team_evaluation_attempts_with_psycopg\n")
BENIGN_VARIANTS = (
    "def _combine_publication_status(policy_status: str, aggregation_status: str) -> str:\n"
    "    if policy_status == \"blocked\" or aggregation_status == \"blocked\":\n        return \"blocked\"\n"
    "    if policy_status == \"watch\" or aggregation_status == \"watch\":\n        return \"watch\"\n    return \"ready\"\n"
    "def _merge_reason_codes(policy_codes: tuple[str, ...], aggregation_codes: tuple[str, ...]) -> tuple[str, ...]:\n"
    "    return tuple(sorted(set(policy_codes) | set(aggregation_codes)))\n")
_INPUT_CLASS = (
    "@final\n@dataclass(frozen=True, slots=True)\nclass CryptoBtcForecastServiceInput:\n"
    "    condition_id: str\n    market_slug: str\n    event_template: str\n"
    "    resolution_contract: CryptoBtcResolutionContract\n    incident_gates: CryptoBtcIncidentGates\n"
    "    evidence_inputs: tuple[CryptoBtcEvidenceInput, ...]\n    evaluated_at: datetime\n"
    "    scope: TeamForecastEvaluationScope\n    run_metadata: TeamForecastRunMetadata\n"
    "    evaluator_receipts: tuple[TeamForecastEvaluatorReceipt, ...]\n    legacy_forecast_packet: TeamForecastPacket | None\n"
    "    legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...]\n"
    "    persistence_config: SupabaseTeamEvidenceAggregationConfig\n"
    "    paper_only: bool = True\n    report_only: bool = True\n    readonly: bool = True\n")
_RESULT_CLASS = (
    "@final\n@dataclass(frozen=True, slots=True)\nclass CryptoBtcForecastServiceResult:\n"
    "    policy_evaluation: CryptoBtcEvidenceEvaluation\n    aggregation_result: TeamEvidenceAggregationResult\n"
    "    publication_status: str\n    reason_codes: tuple[str, ...]\n    envelope: TeamForecastBuildEnvelope\n"
    "    write_results: tuple[object, ...]\n    paper_only: bool = True\n    report_only: bool = True\n    readonly: bool = True\n")
_SERVICE_BODY = (
    "def evaluate_and_persist_crypto_btc_forecast(service_input: CryptoBtcForecastServiceInput, *, "
    "evaluator: Callable[..., CryptoBtcEvidenceEvaluation] | None = None, "
    "writer: Callable[..., tuple[object, ...]] | None = None) -> CryptoBtcForecastServiceResult:\n"
    "    bound_evaluator = evaluate_crypto_btc_evidence if evaluator is None else evaluator\n"
    "    bound_writer = insert_team_evaluation_attempts_with_psycopg if writer is None else writer\n"
    "    evaluation = bound_evaluator(condition_id=service_input.condition_id, market_slug=service_input.market_slug, "
    "event_template=service_input.event_template, resolution_contract=service_input.resolution_contract, "
    "incident_gates=service_input.incident_gates, evidence_inputs=service_input.evidence_inputs, evaluated_at=service_input.evaluated_at)\n"
    "    aggregation_input = TeamEvidenceAggregationInput(evaluated_at=evaluation.evaluated_at, records=evaluation.records, "
    "current_revisions=evaluation.current_selections)\n"
    "    aggregation_result = build_team_evidence_aggregation_result(aggregation_input, config=evaluation.config)\n"
    "    validate_team_evidence_aggregation_result(aggregation_result, aggregation_input=aggregation_input, config=evaluation.config)\n"
    "    envelope = build_team_forecast_build_envelope(aggregation_result, aggregation_input=aggregation_input, config=evaluation.config, "
    "scope=service_input.scope, run_metadata=service_input.run_metadata, evaluator_receipts=service_input.evaluator_receipts, "
    "legacy_forecast_packet=service_input.legacy_forecast_packet, legacy_evidence_packets=service_input.legacy_evidence_packets)\n"
    "    validate_team_forecast_build_envelope(envelope, result=aggregation_result, aggregation_input=aggregation_input, "
    "config=evaluation.config, scope=service_input.scope, run_metadata=service_input.run_metadata, "
    "evaluator_receipts=service_input.evaluator_receipts, legacy_forecast_packet=service_input.legacy_forecast_packet, "
    "legacy_evidence_packets=service_input.legacy_evidence_packets)\n"
    "    write_results = bound_writer(service_input.persistence_config.dsn, (envelope,), table_name=service_input.persistence_config.table_name)\n"
    "    return CryptoBtcForecastServiceResult(policy_evaluation=evaluation, aggregation_result=aggregation_result, "
    "publication_status=_combine_publication_status(evaluation.status, aggregation_result.status), "
    "reason_codes=_merge_reason_codes(evaluation.reason_codes, aggregation_result.reason_codes), envelope=envelope, write_results=write_results)\n")
IMPORT_FAIL_CASES = (
    ('store_module_direct', _F + 'team_evidence_aggregation_attempt_store import insert_team_evaluation_attempt\n'), ('store_module_import', _I + 'team_evidence_aggregation_attempt_store\n'), ('db_row_module', _F + 'team_evidence_aggregation_db_row import team_evaluation_attempt_to_db_row\n'),
    ('codec_module', _F + 'team_evidence_aggregation_codec import team_evidence_aggregation_payload\n'), ('temporal_module', _I + 'team_evidence_aggregation_temporal\n'), ('witness_module', _I + 'team_evidence_aggregation_witness\n'),
    ('allocation_module', _I + 'team_evidence_aggregation_allocation\n'), ('registry_module', _F + 'crypto_btc_evidence_registry import require_approved_crypto_btc_source\n'), ('catalog_module', _F + 'crypto_btc_evidence_catalog import resolve_trusted_crypto_btc_source_record\n'),
    ('dsn_module', _F + 'supabase_local_dsn import validate_local_postgres_dsn\n'), ('psycopg_direct', 'import psycopg\n'), ('psycopg_lazy', 'def _connect():\n    import psycopg\n    return None\n'),
    ('psycopg_json_types', 'from psycopg.types.json import JsonbDumper\n'), ('forecast_psycopg_sibling', _I + 'team_forecast_psycopg\n'), ('forecast_store_sibling', _I + 'team_forecast_store\n'),
    ('forecast_db_row_sibling', _I + 'team_forecast_db_row\n'), ('cli_wiring_module', _I + 'team_cli_wiring\n'), ('strategy_cycle_config', _I + 'supabase_paper_strategy_cycle_report_config\n'),
    ('prefix_extension', _I + 'crypto_btc_evidence_policy_extra\n'), ('package_root_import', 'import polymarket_alpha_lab\n'), ('package_root_importfrom', 'from polymarket_alpha_lab import TeamForecastBuildEnvelope\n'),
    ('relative_import', 'from .team_forecast_packet import TeamForecastPacket\n'), ('relative_empty_module', 'from . import typing\n'), ('wildcard_import', 'from typing import *\n'),
    ('wildcard_future', 'from __future__ import *\n'), ('stdlib_os', 'import os\n'), ('stdlib_json', 'import json\n'),
    ('stdlib_collections', 'import collections\n'), ('stdlib_subprocess', 'import subprocess\n'), ('stdlib_pathlib', 'import pathlib\n'),
    ('stdlib_importlib', 'import importlib\n'), ('forbidden_alias', 'import typing as subprocess\n'), ('forbidden_member', 'from datetime import wallet\n'),
    ('forbidden_member_underscore', 'from typing import _private_wallet_helper\n'), ('adapter_module_plain_import', _I + 'team_evidence_aggregation_attempt_psycopg\n'), ('adapter_alias_member', _F + 'team_evidence_aggregation_attempt_psycopg import persist_team_evaluation_attempts_with_psycopg\n'),
    ('adapter_legacy_member', _F + 'team_evidence_aggregation_attempt_psycopg import insert_team_evaluation_attempt_with_psycopg\n'), ('adapter_private_member', _F + 'team_evidence_aggregation_attempt_psycopg import _insert_attempt_rows_atomic\n'), ('adapter_asname', _F + 'team_evidence_aggregation_attempt_psycopg import insert_team_evaluation_attempts_with_psycopg as batch_writer\n'),)
REJECT_SNIPPETS = (
    ('identifier_name', 'value = wallet\n'), ('identifier_attribute', 'value = record.private_key\n'), ('identifier_function', 'def socket_reader():\n    return None\n'), ('identifier_async_function', 'async def wallet_loader():\n    return None\n'),
    ('identifier_class', 'class Wallet:\n    pass\n'), ('identifier_argument', 'def load(credential_material):\n    return credential_material\n'), ('identifier_keyword', 'compute(wallet_id=1)\n'), ('identifier_global', 'global order_book\n'),
    ('identifier_nonlocal', 'def outer():\n    def inner():\n        nonlocal order_book\n'), ('identifier_except_name', 'try:\n    pass\nexcept ValueError as token_store:\n    pass\n'), ('identifier_import_asname', 'import datetime as subprocess\n'), ('identifier_importfrom_member', 'from datetime import credential_token\n'),
    ('identifier_environ', 'value = os.environ\n'), ('identifier_store', 'value = team_forecast_store_rows\n'), ('identifier_db', 'def probe(db_row):\n    return db_row\n'), ('identifier_execute', 'def execute_write():\n    return None\n'),
    ('call_open', 'descriptor = open("attempts.jsonl")\n'), ('call_print', 'print("message")\n'), ('call_input', 'value = input()\n'), ('call_eval', 'value = eval("expression")\n'),
    ('call_exec', 'exec("statement")\n'), ('call_compile', 'value = compile("source", "source", "exec")\n'), ('call_dynamic_import', 'module = __import__("os")\n'), ('call_hash', 'value = hash(record)\n'),
    ('call_random', 'value = random()\n'), ('call_randint', 'value = randint(0, 9)\n'), ('call_float', 'value = float(record)\n'), ('call_repr', 'text = repr(record)\n'),
    ('call_getenv_bare', 'value = getenv("DSN_ENV")\n'), ('call_getenv_attr', 'value = os.getenv("DSN_ENV")\n'), ('call_read_text', 'value = handle.read_text()\n'), ('call_write_bytes', 'value = handle.write_bytes(data)\n'),
    ('call_now', 'value = datetime.now()\n'), ('call_alias_utcnow', 'import datetime as clock\nvalue = clock.utcnow()\n'), ('call_terminal_today', 'stamp = schedule.today()\n'), ('call_terminal_monotonic', 'value = timer.monotonic()\n'),
    ('call_terminal_timestamp', 'value = record.evaluated_at.timestamp()\n'), ('call_terminal_total_seconds', 'value = record.delta.total_seconds()\n'), ('call_terminal_time_ns', 'value = timer.time_ns()\n'), ('surface_float_literal', 'ratio = 0.5\n'),
    ('surface_float_scientific', 'value = 1e-6\n'), ('surface_float_annotation', 'ratio: float = 0\n'), ('surface_float_reference', 'kind = float\n'), ('surface_broad_exception', 'try:\n    pass\nexcept Exception:\n    pass\n'),
    ('surface_broad_base_exception', 'try:\n    pass\nexcept BaseException as error:\n    pass\n'), ('surface_formatted_repr', 'text = f"{record!r}"\n'), ('sql_insert', 'statement = "insert into team_evaluation_attempts (tea_id) values (%s)"\n'), ('sql_select', 'query = "select tea_id, tfr_id from team_evaluation_attempts"\n'),
    ('sql_update', 'statement = "update team_evaluation_attempts set status = %s"\n'), ('sql_delete', 'statement = "delete from team_evaluation_attempts where tea_id = %s"\n'), ('sql_on_conflict', 'clause = "on conflict (tea_id) do nothing"\n'), ('sql_create_table', 'statement = "create table team_evaluation_attempts (tea_id text)"\n'),
    ('dsn_constant', 'uri = "postgresql://user:secret@localhost:54322/postgres"\n'), ('dsn_password', 'pair = "password=hunter2"\n'), ('dsn_fstring', 'target = f"{config.dsn}?sslmode=require"\n'), ('dsn_concat', 'target = config.dsn + "?sslmode=require"\n'),
    ('dsn_component_fstring', 'target = f"{aggregation_dsn}?sslmode=require"\n'), ('dsn_format', 'target = "{}?sslmode=require".format(config.dsn)\n'), ('dsn_join', 'target = "".join((config.dsn, "?sslmode=require"))\n'), ('side_component', 'value = record.outcome_side\n'),
    ('side_selection_helper', 'def _select_side(evaluation):\n    return None\n'), ('side_selection_field', 'side_selection = 1\n'), ('side_yes_token', 'picked = "YES"\n'), ('side_no_token', 'picked = "no"\n'),
    ('strategy_cycle_identifier', 'strategy_cycle_input = 1\n'), ('strategy_cycle_string', 'label = "strategy_cycle_report"\n'), ('cycle_strategy_helper', 'def _cycle_strategy_inputs():\n    return None\n'), ('seam_writer_lambda', 'writer = lambda dsn, envelopes: ()\n'),
    ('seam_writer_alias_default', 'writer = persist_team_evaluation_attempts_with_psycopg\n'), ('seam_default_writer_module', '_default_writer = insert_team_evaluation_attempt_with_psycopg\n'), ('seam_evaluator_fake', 'evaluator = _fake_evaluator\n'), ('seam_unpacked_writer', 'writer, evaluator = _alternate_pair\n'),
    ('pinned_writer_rebind', 'insert_team_evaluation_attempts_with_psycopg = _alternate_writer\n'), ('pinned_evaluator_shadow', 'def evaluate_crypto_btc_evidence():\n    return None\n'), ('pinned_writer_direct_call', 'results = insert_team_evaluation_attempts_with_psycopg(dsn, envelopes)\n'), ('store_writer_call', 'rows = insert_team_evaluation_attempt_with_psycopg(dsn, row)\n'),
    ('store_read_call', 'latest = load_latest_team_evaluation_attempt(connection, tfr_id=tfr_id)\n'), ('dsn_validator_call', 'validate_local_postgres_dsn(dsn, env_var_name="X")\n'),)
ALLOW_SNIPPETS = (
    ('seam_writer_call', 'write_results = writer(config.dsn, (envelope,), table_name=config.table_name)\n'), ('bound_writer_call', 'write_results = bound_writer(config.dsn, (envelope,), table_name=config.table_name)\n'), ('seam_evaluator_call', 'evaluation = bound_evaluator(condition_id=condition_id, evaluated_at=stamp)\n'),
    ('seam_conditional_binding', 'bound_writer = insert_team_evaluation_attempts_with_psycopg if writer is None else writer\n'), ('dsn_passthrough', 'dsn_value = service_input.persistence_config.dsn\n'), ('selections_passthrough', 'current = evaluation.current_selections\n'),
    ('seam_none_default_local', 'if writer is None:\n    writer = insert_team_evaluation_attempts_with_psycopg\n'), ('status_literals', 'status = "watch"\nreason = "blocked"\n'), ('boundary_docstring', '"""No strategy-cycle wiring and no side selection in this module."""\n'),
    ('evaluator_receipts_field', 'evaluator_receipts: tuple[TeamForecastEvaluatorReceipt, ...]\n'),)
FUTURE_IMPORT = "from __future__ import annotations\n"
E = "evaluate_and_persist_crypto_btc_forecast"
OK_DEF = f"def {E}() -> None:\n    return None\n"
OK_ALL = f'__all__ = ("{E}",)\n'
SINGLE, PAIR_DEFS = (E,), "def alpha():\n    return None\n\n\ndef beta():\n    return None\n"


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
    ('missing_dataclass', '@dataclass(frozen=True, slots=True)\n', ''), ('missing_slots', '@dataclass(frozen=True, slots=True)', '@dataclass(frozen=True)'),
    ('nonliteral_decorator_flag', 'frozen=True', 'frozen="True"'), ('extra_decorator_keyword', 'slots=True)', 'slots=True, kw_only=True)'),
    ('flag_false', 'readonly: bool = True', 'readonly: bool = False'), ('flag_missing', '    readonly: bool = True\n', ''),
    ('flag_wrong_annotation', 'paper_only: bool', 'paper_only: object'), ('flag_no_default', 'paper_only: bool = True', 'paper_only: bool'),)
ROOT_SYNTHETIC_SERVICE_NAMES = set(SERVICE_EXPORTS) | {"_combine_publication_status", "_merge_reason_codes"}
_ROOT_TRIO = ("from polymarket_alpha_lab.crypto_btc_forecast_service import CryptoBtcForecastServiceInput, "
              "CryptoBtcForecastServiceResult, evaluate_and_persist_crypto_btc_forecast\n")
PACKAGE_ROOT_CLEAN_CASE = _ROOT_TRIO + '__all__ = ["CryptoBtcForecastServiceInput", "CryptoBtcForecastServiceResult", "evaluate_and_persist_crypto_btc_forecast"]\n'
PACKAGE_ROOT_REJECT_CASES = (
    ('missing_result_class', 'from polymarket_alpha_lab.crypto_btc_forecast_service import CryptoBtcForecastServiceInput, evaluate_and_persist_crypto_btc_forecast\n'), ('extra_service_member', _ROOT_TRIO + 'from polymarket_alpha_lab.crypto_btc_forecast_service import _combine_publication_status\n'),
    ('asname_binding', 'from polymarket_alpha_lab.crypto_btc_forecast_service import evaluate_and_persist_crypto_btc_forecast as run_crypto_btc_forecast\n' + _ROOT_TRIO), ('conditional_import', 'if True:\n    ' + _ROOT_TRIO),
    ('nested_import', 'def helper():\n    ' + _ROOT_TRIO), ('direct_module_import', 'import polymarket_alpha_lab.crypto_btc_forecast_service\n'),
    ('extra_name_assign', _ROOT_TRIO + '_merge_reason_codes = None\n'),)


def _conforming_module() -> str:
    return "".join((BENIGN_IMPORTS, BENIGN_VARIANTS, _INPUT_CLASS, _RESULT_CLASS, _SERVICE_BODY, "__all__ = (\n" + "".join(f'    "{name}",\n' for name in SERVICE_EXPORTS) + ")\n"))


def test_node_7_synthetic_import_export_surface_seam_and_signature_gate() -> None:
    failures: list[str] = []
    for label, source in (("imports", BENIGN_IMPORTS), ("variants", BENIGN_VARIANTS), ("input_class", _INPUT_CLASS),
                          ("result_class", _RESULT_CLASS), ("service_body", _SERVICE_BODY)):
        found = _module_violations(source)
        if found: failures.append(f"benign {label} were rejected: {found}")
    if (found := _module_violations(_conforming_module(), exports=True, require_seams=True)): failures.append(f"conforming synthetic service module was rejected: {found}")
    if (found := _service_callable_problems(next(n for n in ast.parse(_SERVICE_BODY).body if isinstance(n, ast.FunctionDef)))): failures.append(f"synthetic service signature was rejected: {found}")
    failures.extend(f"import case '{case}' was not rejected" for case, snippet in IMPORT_FAIL_CASES if not _module_violations(snippet))
    failures.extend(f"snippet case '{case}' was not rejected" for case, snippet in REJECT_SNIPPETS if not _module_violations(snippet))
    failures.extend(f"allowance case '{case}' was wrongly rejected: {found}" for case, snippet in ALLOW_SNIPPETS if (found := _module_violations(snippet)))
    for case, source, must_pass, expected in EXPORT_CASES:
        found = _module_violations(source, exports=True, expected=expected)
        if must_pass and found: failures.append(f"export case '{case}' was wrongly rejected: {found}")
        if not must_pass and not found: failures.append(f"export case '{case}' was not rejected")
    assert not failures, "synthetic guard failures:\n" + "\n".join(failures)


def test_node_7_real_module_set_line_ceilings_seams_and_package_root_exports() -> None:
    violations: list[str] = []
    found_production = {p.name for p in PRODUCTION_DIR.glob("crypto_btc_forecast_service*.py")}
    if PRODUCTION_FILE not in found_production:
        violations.append(f"{PRODUCTION_FILE}: required Node 7 production module is missing (pending-red until the parallel module worker lands)")
    violations.extend(f"{extra}: extra crypto_btc_forecast_service* production module outside the Node 7 allowlist"
                      for extra in sorted(found_production - {PRODUCTION_FILE}))
    found_tests = {p.name for p in TEST_DIR.glob("test_crypto_btc_forecast_service*.py")}
    violations.extend(f"{name}: required Node 7 test module is missing (pending-red until the parallel workers land)"
                      for name in sorted(set(TEST_LINE_LIMITS) - found_tests))
    violations.extend(f"{extra}: extra test_crypto_btc_forecast_service* test module outside the Node 7 allowlist"
                      for extra in sorted(found_tests - set(TEST_LINE_LIMITS)))
    counts: dict[str, int] = {}
    for name, ceiling in TEST_LINE_LIMITS.items():
        path = TEST_DIR / name
        if not path.is_file(): continue
        count = len(path.read_text(encoding="utf-8").splitlines())
        counts[name] = count
        if count > ceiling: violations.append(f"{name}: {count} physical lines exceed ceiling {ceiling}")
    if len(counts) == len(TEST_LINE_LIMITS) and sum(counts.values()) > NODE_7_TEST_TOTAL_LINE_LIMIT: violations.append(f"Node 7 test total {sum(counts.values())} exceeds {NODE_7_TEST_TOTAL_LINE_LIMIT} lines")
    service_names = set(SERVICE_EXPORTS)
    if PRODUCTION_PATH.is_file():
        source = PRODUCTION_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        count = len(source.splitlines())
        if count > PRODUCTION_LINE_LIMIT: violations.append(f"{PRODUCTION_FILE}: {count} physical lines exceed ceiling {PRODUCTION_LINE_LIMIT}")
        violations.extend(f"{PRODUCTION_FILE}: {item}" for item in _module_violations(source, exports=True, require_seams=True))
        service_names = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        callable_node = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}.get(SERVICE_EXPORTS[2])
        if callable_node is None:
            violations.append(f"{PRODUCTION_FILE}: {SERVICE_EXPORTS[2]} must be a direct function definition")
        else:
            violations.extend(f"{PRODUCTION_FILE}: {item}" for item in _service_callable_problems(callable_node))
            if not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and "writer" in _components(n.func.id) and n.func.id not in FORBIDDEN_EXACT_NAMES and any(k.arg == "table_name" for k in n.keywords) for n in ast.walk(callable_node)):
                violations.append(f"{PRODUCTION_FILE}: the injected writer call must forward table_name from the persistence config")
    root_tree = ast.parse((PRODUCTION_DIR / "__init__.py").read_text(encoding="utf-8"))
    violations.extend(f"package root: {item}" for item in _package_root_problems(root_tree, service_names))
    assert not _package_root_problems(ast.parse(PACKAGE_ROOT_CLEAN_CASE), ROOT_SYNTHETIC_SERVICE_NAMES), "clean package-root synthetic was rejected"
    violations.extend(f"package-root case '{case}' was not rejected" for case, snippet in PACKAGE_ROOT_REJECT_CASES
                      if not _package_root_problems(ast.parse(snippet), ROOT_SYNTHETIC_SERVICE_NAMES))
    if PRODUCTION_PATH.is_file() and not _package_root_problems(root_tree, service_names):
        root, service = importlib.import_module("polymarket_alpha_lab"), importlib.import_module(PRODUCTION_IMPORT)
        for name in SERVICE_EXPORTS:
            assert getattr(root, name, None) is getattr(service, name), f"package root {name} is not the service module object"
    assert not violations, "\n".join(violations)


def test_node_7_public_dataclasses_are_frozen_slotted_and_hard_flagged() -> None:
    failures: list[str] = []
    for label, source in (("input", _INPUT_CLASS), ("result", _RESULT_CLASS), ("sample", _SAMPLE_CLASS)):
        if _class_def_problems(next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef))): failures.append(f"conforming class '{label}' was wrongly rejected")
    failures.extend(f"class-shape mutation '{label}' was not rejected" for label, old, new in CLASS_MUTATIONS
                    if not _class_def_problems(next(n for n in ast.parse(_SAMPLE_CLASS.replace(old, new)).body if isinstance(n, ast.ClassDef))))
    assert not failures, "synthetic class-shape guard failures:\n" + "\n".join(failures)
    assert PRODUCTION_PATH.is_file(), f"{PRODUCTION_FILE}: required Node 7 production module is missing (pending-red until the parallel module worker lands)"
    classes = {n.name: n for n in ast.parse(PRODUCTION_PATH.read_text(encoding="utf-8")).body if isinstance(n, ast.ClassDef)}
    problems: list[str] = []
    for name in sorted(SERVICE_CLASS_EXPORTS):
        node = classes.get(name)
        if node is None: problems.append(f"{name} is not a direct class definition"); continue
        problems.extend(f"{name}: {item}" for item in _class_def_problems(node))
    assert not problems, "\n".join(problems)
    module = importlib.import_module(PRODUCTION_IMPORT)
    for name in sorted(SERVICE_CLASS_EXPORTS):
        public_class = getattr(module, name)
        assert public_class.__dataclass_params__.frozen is True, name
        assert public_class.__dataclass_params__.slots is True, name
        defaults = {field.name: field.default for field in dataclasses.fields(public_class) if field.name in HARD_FLAG_NAMES}
        assert defaults == dict.fromkeys(HARD_FLAG_NAMES, True), name
