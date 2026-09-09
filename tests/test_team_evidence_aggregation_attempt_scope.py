"""Node 5 two-module AST, import/export, forbidden-surface, ownership, package-root, and line-size guard.

The store owns SQL text, latest-attempt ordering, the legacy-insert rejection fence, and the private atomic writer; the psycopg module is the lazy adapter
owning connection, one commit, rollback, and close. Guards imports, exact ``__all__`` with anywhere-binding rebinding protection, filesystem/JSONL/env/
float/clock/randomness/hash()/broad-except/print/DSN/live-trading surfaces, directional SQL/transaction/cursor/connection ownership, and all ceilings.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_DIR, TEST_DIR = REPO_ROOT / "src" / "polymarket_alpha_lab", REPO_ROOT / "tests"
STORE = "team_evidence_aggregation_attempt_store"
PSYCOPG = "team_evidence_aggregation_attempt_psycopg"
MODULES = (STORE, PSYCOPG)
_I, _F = "import polymarket_alpha_lab.", "from polymarket_alpha_lab."
PRODUCTION_LINE_LIMITS = {f"{PSYCOPG}.py": 380, f"{STORE}.py": 420}
PRODUCTION_TOTAL_LINE_LIMIT = 800
TEST_LINE_LIMITS = {"test_team_evidence_aggregation_attempt_disposable.py": 460, "test_team_evidence_aggregation_attempt_psycopg.py": 620,
                    "test_team_evidence_aggregation_attempt_scope.py": 320, "test_team_evidence_aggregation_attempt_store.py": 620}
NODE_5_TEST_TOTAL_LINE_LIMIT = 2_000
IMPORT_ALLOWLISTS = {
    STORE: frozenset(("__future__", "dataclasses", "datetime", "re", "typing", "polymarket_alpha_lab.team_evidence_aggregation_db_row")),
    PSYCOPG: frozenset(("__future__", "typing", "psycopg", "psycopg.types.json", "polymarket_alpha_lab.supabase_local_dsn",
                        "polymarket_alpha_lab.team_evidence_aggregation_attempt_store", "polymarket_alpha_lab.team_forecast_build_envelope",
                        "polymarket_alpha_lab.team_evidence_aggregation_db_row"))}
PUBLIC_EXPORTS = {STORE: ("TEAM_EVALUATION_ATTEMPT_COLUMNS", "TeamEvaluationAttemptWriteResult", "insert_team_evaluation_attempt",
                          "load_latest_team_evaluation_attempt", "load_team_evaluation_attempt_rows"),
                  PSYCOPG: ("insert_team_evaluation_attempt_with_psycopg", "persist_team_evaluation_attempts_with_psycopg")}
CLASS_EXPORTS = {STORE: frozenset(("TeamEvaluationAttemptWriteResult",)), PSYCOPG: frozenset()}
CONSTANT_EXPORTS = {STORE: frozenset(("TEAM_EVALUATION_ATTEMPT_COLUMNS",)), PSYCOPG: frozenset()}
NODE_5_PUBLIC_NAMES = frozenset().union(*PUBLIC_EXPORTS.values())
HARD_FLAG_NAMES = ("paper_only", "report_only", "readonly")
FORBIDDEN_COMPONENTS = frozenset((
    "account", "accounts", "aiohttp", "api", "argv", "auth", "authenticate", "authentication", "browser", "cache", "caches", "cached", "cancel", "cli",
    "client", "click", "credential", "credentials", "csv", "duckdb", "environ", "external", "file", "files", "filename", "filepath", "fork", "getenv",
    "getopt", "http", "https", "importlib", "jsonl", "log", "logs", "logger", "logging", "mkdir", "mkdtemp", "mkstemp", "mongo", "mongodb", "mysql",
    "order", "orders", "password", "passwords", "pathlib", "popen", "putenv", "random", "randomize", "redis", "remove", "requests", "scrape",
    "scraper", "scrapers", "scraping", "secret", "secrets", "seed", "selenium", "sign", "signing", "signature", "signatures", "socket", "sockets",
    "spawn", "sqlite", "sqlalchemy", "stdin", "stdout", "stderr", "subprocess", "system", "tempfile", "token", "tokens", "typer", "urllib", "wallet",
    "wallets", "websocket", "websockets"))
COMPONENTS = {STORE: FORBIDDEN_COMPONENTS | {"connect", "psycopg"}, PSYCOPG: FORBIDDEN_COMPONENTS | {"sql"}}
FORBIDDEN_SEQUENCES = (("live", "trading"), ("trading", "live"), ("private", "key"), ("hosted", "account"), ("read", "text"),
                       ("write", "bytes"), ("write", "text"), ("exchange", "mutate"), ("exchange", "mutation"))
FORBIDDEN_BARE_CALLS = frozenset(("open", "print", "input", "eval", "exec", "compile", "__import__", "hash", "float", "repr", "random",
                                  "randint", "randrange", "choice", "choices", "shuffle", "sample", "uniform", "gauss", "seed",
                                  "getrandbits", "randbytes", "getenv"))
CLOCK_TERMINALS = frozenset(("now", "utcnow", "today", "timestamp", "total_seconds", "time", "time_ns", "monotonic", "monotonic_ns",
                             "perf_counter", "perf_counter_ns", "clock", "gmtime", "localtime", "ctime", "asctime"))
TERMINALS = {STORE: CLOCK_TERMINALS | {"commit", "rollback", "connect"}, PSYCOPG: CLOCK_TERMINALS | {"execute", "executemany", "cursor"}}
SQL_STATEMENT_PATTERNS = tuple(re.compile(p, re.IGNORECASE | re.DOTALL) for p in (
    r"\binsert\s+into\b", r"\bselect\b.+\bfrom\b", r"\bupdate\b.+\bset\b", r"\bdelete\s+from\b", r"\bmerge\s+into\b", r"\bon\s+conflict\b"))
DSN_MARKERS = ("://", "password=")
REDACTED = "<redacted>"
CLEANUP_HELPER = "_close_cursor_after_operation_error"


def _module_violations(source: str, module: str, *, exports: bool = True, expected: tuple[str, ...] | None = None) -> list[str]:
    is_adapter = module == PSYCOPG
    allowlist, singles, terminals = IMPORT_ALLOWLISTS[module], COMPONENTS[module], TERMINALS[module]
    tree = ast.parse(source)
    cleanup_handlers = {id(h) for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) and f.name == CLEANUP_HELPER
                        for h in ast.walk(f) if isinstance(h, ast.ExceptHandler)}
    identifiers, violations = [], []
    for node in ast.walk(tree):
        kind = type(node)
        if kind in (ast.Import, ast.ImportFrom):
            for alias in node.names:
                identifiers.append((node.lineno, (alias.asname or alias.name) if kind is ast.ImportFrom else (alias.asname or alias.name.split(".")[0])))
                if alias.name == "*" and kind is ast.ImportFrom: violations.append(f"line {node.lineno}: wildcard import")
            if kind is ast.ImportFrom and (node.level != 0 or not node.module):
                violations.append(f"line {node.lineno}: relative or empty-module import")
            else:
                for root in ([a.name for a in node.names] if kind is ast.Import else [node.module]):
                    if root not in allowlist: violations.append(f"line {node.lineno}: module '{root}' is not in the Node 5 allowlist")
                    if is_adapter and root.startswith("psycopg") and node.col_offset == 0: violations.append(f"line {node.lineno}: psycopg import must stay lazy inside a function")
        elif kind is ast.Call:
            func = node.func
            terminal = func.id if type(func) is ast.Name else func.attr if type(func) is ast.Attribute else None
            if type(func) is ast.Name and func.id in FORBIDDEN_BARE_CALLS: violations.append(f"line {func.lineno}: forbidden call '{func.id}()'")
            if terminal in terminals: violations.append(f"line {func.lineno}: forbidden terminal call '{terminal}()'")
        elif kind is ast.Name:
            identifiers.append((node.lineno, node.id))
            if node.id == "float": violations.append(f"line {node.lineno}: float annotation, call, or reference")
        elif kind is ast.Attribute: identifiers.append((node.lineno, node.attr))
        elif kind in (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef): identifiers.append((node.lineno, node.name))
        elif kind is ast.arg: identifiers.append((node.lineno, node.arg))
        elif kind is ast.keyword and node.arg is not None: identifiers.append((node.lineno, node.arg))
        elif kind is ast.ExceptHandler:
            if node.name is not None: identifiers.append((node.lineno, node.name))
            caught = {item.id for item in ast.walk(node.type) if type(item) is ast.Name} if node.type is not None else set()
            if "Exception" in caught or ("BaseException" in caught and not (any(type(r) is ast.Raise for r in ast.walk(node)) or id(node) in cleanup_handlers)):
                violations.append(f"line {node.lineno}: broad except handler (BaseException must re-raise or sit in the cursor-cleanup helper)")
        elif kind in (ast.Global, ast.Nonlocal): identifiers.extend((node.lineno, entry) for entry in node.names)
        elif kind is ast.Constant:
            if type(node.value) is float: violations.append(f"line {node.lineno}: float literal")
            elif isinstance(node.value, str):
                if node.value != REDACTED and any(m in node.value for m in DSN_MARKERS): violations.append(f"line {node.lineno}: credential-bearing or DSN-shaped string constant")
                if is_adapter and any(p.search(node.value) for p in SQL_STATEMENT_PATTERNS): violations.append(f"line {node.lineno}: SQL statement text is confined to the store module")
        elif kind is ast.FormattedValue and node.conversion == ord("r"):
            violations.append(f"line {node.lineno}: object repr conversion may leak DSNs or secrets")
    for lineno, identifier in identifiers:
        parts = tuple(word.lower() for chunk in identifier.split("_") for word in re.findall(r"[A-Z]+(?![a-z0-9])|[A-Z][a-z0-9]*|[a-z0-9]+", chunk) if word)
        hits = [part for part in parts if part in singles]
        hits.extend("-".join(s) for s in FORBIDDEN_SEQUENCES for i in range(len(parts) - len(s) + 1) if parts[i:i + len(s)] == s)
        if hits: violations.append(f"line {lineno}: forbidden identifier '{identifier}' ({', '.join(hits)})")
    if exports:
        violations += _export_violations(tree, PUBLIC_EXPORTS[module] if expected is None else expected, CLASS_EXPORTS[module], CONSTANT_EXPORTS[module])
    return violations


def _export_violations(tree: ast.Module, expected: tuple[str, ...], class_exports: frozenset[str], constant_exports: frozenset[str]) -> list[str]:
    violations: list[str] = []
    assignments = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)]
    if len(assignments) != 1: return ["__all__ must be exactly one direct tuple assignment"]
    allowed = {id(t) for t in assignments[0].targets if isinstance(t, ast.Name) and t.id == "__all__"} | {
        id(t) for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign)) for t in (n.targets if isinstance(n, ast.Assign) else [n.target])
        if isinstance(t, ast.Name) and t.id in constant_exports}
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
        if len(set(names)) != len(names): violations.append("__all__ contains duplicate names")
        if names != expected: violations.append(f"__all__ must equal the exact ordered export tuple; got {names!r}")
    for name in expected:
        anywhere = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name]
        bindings = [t for n in tree.body if isinstance(n, (ast.Assign, ast.AnnAssign)) for t in (n.targets if isinstance(n, ast.Assign) else [n.target]) if isinstance(t, ast.Name) and t.id == name]
        if name in constant_exports: ok = not anywhere and len(bindings) == 1
        else: ok = len(anywhere) == 1 and (direct := [n for n in tree.body if n in anywhere]) and type(direct[0]) is (ast.ClassDef if name in class_exports else ast.FunctionDef)
        if not ok: violations.append(f"export '{name}' requires exactly one module-level definition or binding")
    return violations


def _package_root_bound_names(tree: ast.Module) -> set[str]:
    bound = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)}
    bound |= {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            bound |= {alias.asname or alias.name.split(".")[0] for alias in node.names} | {alias.name for alias in node.names}
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            bound |= {item.value for item in ast.walk(node.value) if isinstance(item, ast.Constant) and isinstance(item.value, str)}
    return bound


def _class_def_problems(node: ast.ClassDef) -> list[str]:
    calls = [d for d in node.decorator_list if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass"]
    keywords = {k.arg: k.value for call in calls for k in call.keywords}
    statements = {s.target.id: s for s in node.body if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)}
    problems = ["missing @dataclass(frozen=True)"] * (len(calls) != 1 or bool(set(keywords) - {"frozen", "slots"})
                   or not isinstance((frozen := keywords.get("frozen")), ast.Constant) or frozen.value is not True
                   or not all(isinstance(v, ast.Constant) and v.value is True for v in keywords.values()))
    problems += [f"{flag} must be 'bool' with a literal True default" for flag in HARD_FLAG_NAMES if not (
        isinstance(statements.get(flag), ast.AnnAssign) and isinstance(statements[flag].annotation, ast.Name) and statements[flag].annotation.id == "bool"
        and isinstance(statements[flag].value, ast.Constant) and statements[flag].value.value is True)]
    return problems

_REPO_IMPORTS = (_F + "supabase_local_dsn import validate_local_postgres_dsn\n" + _F + "team_evidence_aggregation_db_row import team_evaluation_attempt_to_db_row\n"
                 + _F + "team_forecast_build_envelope import TeamForecastBuildEnvelope, team_evidence_aggregation_id, team_forecast_evaluation_scope_payload, team_forecast_run_id\n"
                 + _F + "team_evidence_aggregation_attempt_store import TeamEvaluationAttemptWriteResult, _insert_attempt_rows_atomic\n")
STORE_IMPORTS = ("from __future__ import annotations\nimport dataclasses\nfrom dataclasses import dataclass\nimport re\n"
                 "from typing import Any, Final, final\n" + _F + "team_evidence_aggregation_db_row import TeamEvaluationAttemptDbRow\n")
PSYCOPG_IMPORTS = "from __future__ import annotations\nfrom typing import Any, Callable, TypeVar\n" + _REPO_IMPORTS
STORE_VARIANTS = ('from typing import Any as row_value\n_TABLE_NAME = "team_evaluation_attempts"\n'
                  '_SELECT_SQL = "select tea_id, tfr_id, status from team_evaluation_attempts order by attempted_at desc, tea_id desc"\n')
PSYCOPG_VARIANTS = ('from typing import Callable as operation_kind\nfrom typing import Any as row_value\n_REDACTED_DSN = "<redacted>"\n'
                    '_ENV_VAR_NAME = "POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN"\n')
BENIGN = {STORE: (STORE_IMPORTS, STORE_VARIANTS), PSYCOPG: (PSYCOPG_IMPORTS, PSYCOPG_VARIANTS)}
_STORE_BODY = (
    'TEAM_EVALUATION_ATTEMPT_COLUMNS = ("tea_id", "tfr_id", "status")\n'
    "@dataclass(frozen=True, slots=True)\nclass TeamEvaluationAttemptWriteResult:\n    tea_id: str\n    inserted: bool\n"
    "    paper_only: bool = True\n    report_only: bool = True\n    readonly: bool = True\n"
    "def insert_team_evaluation_attempt(connection, row, *, table_name=_TABLE_NAME):\n    raise ValueError(\"legacy insert fence rejects v1 identifiers before cursor activity\")\n"
    "def load_team_evaluation_attempt_rows(connection, *, tfr_id=None, table_name=_TABLE_NAME):\n"
    "    cursor = connection.cursor()\n    cursor.execute(_SELECT_SQL, ())\n    return ()\n"
    "def load_latest_team_evaluation_attempt(connection, *, tfr_id, table_name=_TABLE_NAME):\n    return None\n")
_PSYCOPG_BODY = (
    "def _connect(dsn):\n    import psycopg\n    return psycopg.connect(dsn)\n"
    "def insert_team_evaluation_attempts_with_psycopg(envelopes, *, dsn, env_var_name):\n"
    "    validate_local_postgres_dsn(dsn, env_var_name=env_var_name)\n    connection = _connect(dsn)\n"
    "    try:\n        _insert_attempt_rows_atomic(connection, ())\n        connection.commit()\n    except BaseException:\n        connection.rollback()\n        raise\n"
    "    finally:\n        connection.close()\n    return ()\n"
    "def persist_team_evaluation_attempts_with_psycopg(dsn, envelopes, *, env_var_name):\n    return insert_team_evaluation_attempts_with_psycopg(dsn, envelopes, env_var_name=env_var_name)\n"
    "def insert_team_evaluation_attempt_with_psycopg(dsn, row, *, env_var_name):\n    raise ValueError(\"dsn=<redacted>; legacy adapter insert rejects v1 identifiers before connection activity\")\n")


def _conforming_module(module: str) -> str:
    imports, variants = BENIGN[module]
    return imports + variants + (_STORE_BODY if module == STORE else _PSYCOPG_BODY) + "__all__ = (\n" + "".join(f'    "{n}",\n' for n in PUBLIC_EXPORTS[module]) + ")\n"

IMPORT_FAIL_CASES = (
    ("store_psycopg", STORE, "import psycopg\n"), ("store_dsn", STORE, _F + "supabase_local_dsn import validate_local_postgres_dsn\n"),
    ("store_envelope", STORE, _F + "team_forecast_build_envelope import TeamForecastBuildEnvelope\n"),
    ("store_psycopg_sibling", STORE, _I + "team_forecast_psycopg\n"), ("adapter_store_sibling", PSYCOPG, _F + "team_forecast_store import insert_team_forecast\n"),
    ("adapter_psycopg_sibling", PSYCOPG, _I + "team_forecast_psycopg\n"), ("adapter_dbrow_sibling", PSYCOPG, _I + "team_forecast_db_row\n"),
    ("adapter_config", PSYCOPG, _F + "supabase_team_evidence_aggregation_config import TEAM_EVIDENCE_AGGREGATION_DB_DSN_ENV_VAR\n"),
    ("adapter_prefix_ext", PSYCOPG, _I + "team_evidence_aggregation_db_row_extra\n"), ("adapter_eager", PSYCOPG, "import psycopg\n"),
    ("root_import", STORE, "import polymarket_alpha_lab\n"), ("root_importfrom", PSYCOPG, "from polymarket_alpha_lab import TeamEvaluationAttemptWriteResult\n"),
    ("relative", STORE, "from .team_evidence_aggregation_db_row import TeamEvaluationAttemptDbRow\n"), ("relative_empty", PSYCOPG, "from . import typing\n"),
    ("wildcard", STORE, "from typing import *\n"), ("stdlib_json", STORE, "import json\n"), ("stdlib_os", PSYCOPG, "import os\n"),
    ("stdlib_subprocess", STORE, "import subprocess\n"),
    ("stdlib_tempfile", PSYCOPG, "import tempfile\n"), ("stdlib_pathlib", STORE, "import pathlib\n"), ("bad_alias", STORE, "import re as subprocess\n"),
    ("bad_member", PSYCOPG, "from typing import wallet\n"), ("bad_member_underscore", STORE, "from datetime import _private_wallet_helper\n"))
REJECT_SNIPPETS = (
    ("id_wallet", "value = wallet\n"), ("id_private_key", "value = record.private_key\n"), ("id_order_book", "global order_book\n"),
    ("id_live_trading", "def live_trading_gate():\n    return None\n"), ("id_auth", "def authenticate_caller():\n    return None\n"),
    ("id_credential", "def load(credential_material):\n    return credential_material\n"), ("id_secret_token", "secret_token = 1\n"),
    ("id_jsonl", "audit_jsonl_path = 1\n"), ("id_environ", "value = os.environ\n"), ("call_getenv", 'value = getenv("DSN_ENV")\n'),
    ("call_open", 'descriptor = open("attempts.jsonl")\n'), ("call_print", 'print("message")\n'), ("call_eval", 'value = eval("x")\n'),
    ("call_import", 'module = __import__("os")\n'), ("call_hash", "value = hash(record)\n"), ("call_random", "value = random()\n"),
    ("call_randint", "value = randint(0, 9)\n"), ("call_float", "value = float(record)\n"), ("call_read_text", "value = handle.read_text()\n"),
    ("call_write_bytes", "value = handle.write_bytes(data)\n"), ("call_now", "value = datetime.now()\n"),
    ("call_alias_utcnow", "import datetime as clock\nvalue = clock.utcnow()\n"), ("call_monotonic", "value = timer.monotonic()\n"),
    ("float_literal", "ratio = 0.5\n"), ("float_name", "kind = float\n"), ("broad_except", "try:\n    pass\nexcept Exception:\n    pass\n"),
    ("repr_conv", 'text = f"{record!r}"\n'), ("dsn_constant", 'uri = "postgresql://user:secret@localhost:54322/postgres"\n'),
    ("dsn_password", 'pair = "password=hunter2"\n'))
OWNERSHIP_CASES = (
    ("store_commit", "connection.commit()\n", (STORE,), (PSYCOPG,)), ("store_rollback", "connection.rollback()\n", (STORE,), (PSYCOPG,)),
    ("store_connect", "connection = connect(dsn)\n", (STORE,), (PSYCOPG,)), ("adapter_cursor", "cursor = connection.cursor()\n", (PSYCOPG,), (STORE,)),
    ("adapter_executemany", "cursor.executemany(statement, rows)\n", (PSYCOPG,), (STORE,)),
    ("adapter_execute", 'cursor.execute("insert into team_evaluation_attempts (tea_id) values (%s)", params)\n', (PSYCOPG,), (STORE,)),
    ("adapter_select", '_QUERY = "select tea_id, tfr_id from team_evaluation_attempts"\n', (PSYCOPG,), (STORE,)), ("adapter_conflict", '_CLAUSE = "on conflict (tea_id) do nothing"\n', (PSYCOPG,), (STORE,)),
    ("adapter_update", 'statement_text = "update team_evaluation_attempts set status = %s where tea_id = %s"\n', (PSYCOPG,), (STORE,)),
    ("swallow_baseexc", "try:\n    pass\nexcept BaseException:\n    pass\n", (PSYCOPG, STORE), ()),
    ("cleanup_reraise_baseexc", f"try:\n    pass\nexcept BaseException:\n    {CLEANUP_HELPER}(cursor)\n    raise\n", (), (STORE, PSYCOPG)))
FUTURE_IMPORT = "from __future__ import annotations\n"
OK_DEF = "def insert_team_evaluation_attempt(connection, row):\n    return None\n"
OK_ALL = '__all__ = ("insert_team_evaluation_attempt",)\n'
SINGLE = ("insert_team_evaluation_attempt",)
E = "insert_team_evaluation_attempt"
PAIR_DEFS = "def alpha():\n    return None\n\n\ndef beta():\n    return None\n"


def _export_case(all_expr: str, extra: str = "", definition: str = OK_DEF) -> str: return FUTURE_IMPORT + all_expr + definition + extra

EXPORT_CASES = (
    ("clean", _export_case(OK_ALL), True, SINGLE), ("pair_ok", _export_case('__all__ = ("alpha", "beta")\n', PAIR_DEFS), True, ("alpha", "beta")),
    ("pair_reordered", _export_case('__all__ = ("beta", "alpha")\n', PAIR_DEFS), False, ("alpha", "beta")), ("list_form", _export_case(f'__all__ = ["{E}"]\n'), False, SINGLE),
    ("second_assign", _export_case(OK_ALL, OK_ALL), False, SINGLE), ("chained", _export_case(f'__all__ = {E} = ("{E}",)\n'), False, SINGLE),
    ("unpacked", _export_case(f'__all__ = (__all__,) = ("{E}",)\n'), False, SINGLE), ("walrus", _export_case(OK_ALL, f"if ({E} := 1):\n    pass\n"), False, SINGLE),
    ("def_all", _export_case(OK_ALL, "def __all__():\n    return None\n"), False, SINGLE), ("import_bind", _export_case(f"from typing import {E}\n" + OK_ALL), False, SINGLE),
    ("nested_def", _export_case(OK_ALL, f"def wrapper():\n    def {E}():\n        return None\n"), False, SINGLE),
    ("class_kind", _export_case(OK_ALL, "", f"class {E}:\n    pass\n"), False, SINGLE),
    ("async_kind", _export_case(OK_ALL, "", f"async def {E}():\n    return None\n"), False, SINGLE))
_SAMPLE_CLASS = ("@dataclass(frozen=True, slots=True)\nclass Sample:\n"
                 "    paper_only: bool = True\n    report_only: bool = True\n    readonly: bool = True\n")
CLASS_MUTATIONS = (("@dataclass(frozen=True, slots=True)\n", ""), ("@dataclass(frozen=True, slots=True)", "@dataclass(slots=True)"),
                   ("frozen=True", 'frozen="True"'), ("readonly: bool = True", "readonly: bool = False"),
                   ("paper_only: bool", "paper_only: object"), ("paper_only: bool = True", "paper_only: bool"))
PACKAGE_ROOT_CLEAN_CASE = "import decimal\nif True:\n    value = 1\n__all__ = (\"MarketScore\",)\n"
PACKAGE_ROOT_REJECT_CASES = (
    ("root_store_import", _I + STORE + "\n"), ("root_psycopg_import", _I + PSYCOPG + "\n"),
    ("root_cond_from", f"if True:\n    from polymarket_alpha_lab.{PSYCOPG} import persist_team_evaluation_attempts_with_psycopg\n"),
    ("root_nested", f"def helper():\n    from polymarket_alpha_lab.{STORE} import TeamEvaluationAttemptWriteResult\n"),
    ("root_assign", f"if True:\n    {E} = None\n"), ("root_all", '__all__ = ("load_team_evaluation_attempt_rows",)\n'))


def test_node_5_synthetic_two_direction_import_export_surface_ownership_and_shape_gate() -> None:
    failures: list[str] = []
    for module in MODULES:
        imports, variants = BENIGN[module]
        failures += [f"benign {label} for {module} were rejected" for label, source in (("imports", imports), ("variants", variants)) if _module_violations(source, module, exports=False)]
        if _module_violations(_conforming_module(module), module): failures.append(f"conforming synthetic module {module} was rejected")
    failures += [f"import case '{case}' was not rejected" for case, module, snippet in IMPORT_FAIL_CASES if not _module_violations(snippet, module, exports=False)]
    failures += [f"snippets case '{case}' was not rejected in {module}" for case, snippet in REJECT_SNIPPETS for module in MODULES if not _module_violations(snippet, module, exports=False)]
    for case, snippet, reject_in, allow_in in OWNERSHIP_CASES:
        failures += [f"ownership case '{case}' was not rejected in {module}" for module in reject_in if not _module_violations(snippet, module, exports=False)]
        failures += [f"ownership case '{case}' was wrongly rejected in {module}" for module in allow_in if _module_violations(snippet, module, exports=False)]
    failures += [f"export case '{case}' resolved wrongly in {module}" for case, source, must_pass, expected in EXPORT_CASES for module in MODULES
                 if (found := _module_violations(source, module, exports=True, expected=expected)) and must_pass or (not must_pass and not found)]
    if _class_def_problems(next(n for n in ast.parse(_conforming_module(STORE)).body if isinstance(n, ast.ClassDef))): failures.append("conforming store write-result class was rejected")
    for old, new in CLASS_MUTATIONS:
        if not _class_def_problems(next(n for n in ast.parse(_SAMPLE_CLASS.replace(old, new)).body if isinstance(n, ast.ClassDef))): failures.append(f"class-shape mutation '{old[:24]}' was not rejected")
    assert not failures, "\n".join(failures)


def test_node_5_real_modules_module_set_line_ceilings_and_class_shape_gate() -> None:
    violations: list[str] = []
    counts: dict[str, dict[str, int]] = {"production": {}, "test": {}}
    for directory, limits, kind, total in ((PRODUCTION_DIR, PRODUCTION_LINE_LIMITS, "production", PRODUCTION_TOTAL_LINE_LIMIT),
                                           (TEST_DIR, TEST_LINE_LIMITS, "test", NODE_5_TEST_TOTAL_LINE_LIMIT)):
        found = {path.name for path in directory.glob(("test_" if kind == "test" else "") + "team_evidence_aggregation_attempt*.py")}
        violations += [f"{n}: required Node 5 {kind} module is missing (pending-red until the parallel worker lands)" for n in sorted(set(limits) - found)]
        violations += [f"{e}: {kind} module is outside the exact eight-path Node 5 allowlist" for e in sorted(found - set(limits))]
        for name, limit in limits.items():
            if not (path := directory / name).is_file(): continue
            count = len(path.read_text(encoding="utf-8").splitlines())
            counts[kind][name] = count
            if count > limit: violations.append(f"{name}: {count} physical lines exceed ceiling {limit}")
        if len(counts[kind]) == len(limits) and sum(counts[kind].values()) > total:
            violations.append(f"Node 5 {kind} total {sum(counts[kind].values())} exceeds {total} lines")
    for module in MODULES:
        if (path := PRODUCTION_DIR / f"{module}.py").is_file(): violations.extend(f"{module}: {item}" for item in _module_violations(path.read_text(encoding="utf-8"), module))
        else: violations.append(f"{module}.py: required Node 5 production module is missing (pending-red until the parallel worker lands)")
    if (store_path := PRODUCTION_DIR / f"{STORE}.py").is_file():
        classes = {n.name: n for n in ast.parse(store_path.read_text(encoding="utf-8")).body if isinstance(n, ast.ClassDef)}
        if (node := classes.get("TeamEvaluationAttemptWriteResult")) is None: violations.append(f"{STORE}: TeamEvaluationAttemptWriteResult must be a direct class definition")
        else: violations.extend(f"{STORE}.TeamEvaluationAttemptWriteResult: {item}" for item in _class_def_problems(node))
    forbidden = NODE_5_PUBLIC_NAMES | {f"polymarket_alpha_lab.{module}" for module in MODULES}
    bound = _package_root_bound_names(ast.parse((PRODUCTION_DIR / "__init__.py").read_text(encoding="utf-8")))
    violations.extend(f"package root binds forbidden Node 5 name '{name}'" for name in sorted(bound & forbidden))
    assert not (_package_root_bound_names(ast.parse(PACKAGE_ROOT_CLEAN_CASE)) & forbidden), "clean package-root synthetic was rejected"
    for case, snippet in PACKAGE_ROOT_REJECT_CASES:
        if not (_package_root_bound_names(ast.parse(snippet)) & forbidden): violations.append(f"package-root case '{case}' was not rejected")
    assert not violations, "\n".join(violations)
