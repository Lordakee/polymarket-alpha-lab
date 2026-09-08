from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "polymarket_alpha_lab"
TESTS_ROOT = REPO_ROOT / "tests"
MIGRATIONS_ROOT = REPO_ROOT / "supabase" / "migrations"
DOC_PATH = REPO_ROOT / "docs" / "team-forecast-migration-safety.md"

FORBIDDEN_DURABLE_BACKEND_IMPORTS = frozenset(
    (
        "dbm",
        "duckdb",
        "lmdb",
        "mongoengine",
        "motor",
        "pymongo",
        "redis",
        "shelve",
        "sqlalchemy",
        "sqlite3",
        "tinydb",
    ),
)
FORBIDDEN_DURABLE_BACKEND_CALLS = frozenset(("create_engine",))
FORBIDDEN_DURABLE_FILE_WRITE_CALLS = frozenset(
    (
        "json.dump",
        "open",
        "Path.open",
        "pickle.dump",
        "shelve.open",
        "write_bytes",
        "write_text",
    ),
)
FILE_WRITE_MODE_CHARS = frozenset(("a", "w", "x", "+"))
FORBIDDEN_MIGRATION_TOKENS = (
    "sqlite",
    "redis",
    "mongo",
    "mongodb",
    "sqlalchemy",
    "database_url",
    "postgresql://",
    "postgres://",
    "supabase_url",
    "service_role",
    "anon_key",
    "http://",
    "https://",
    "create_client",
)
PERSISTENCE_SCOPE_NEEDLES = tuple(
    sorted(
        {
            "create_engine",
            *(
                f"import {backend}"
                for backend in FORBIDDEN_DURABLE_BACKEND_IMPORTS
            ),
            *(
                f"from {backend}"
                for backend in FORBIDDEN_DURABLE_BACKEND_IMPORTS
            ),
        }
    )
)
PUBLIC_OUTPUT_PATTERNS = (
    re.compile(r"\bprint\s*\(", flags=re.IGNORECASE),
    re.compile(r"\bsys\.stdout\.write\s*\(", flags=re.IGNORECASE),
    re.compile(r"\bsys\.stderr\.write\s*\(", flags=re.IGNORECASE),
)
PUBLIC_OUTPUT_NEEDLES = (
    "print(",
    "sys.stdout.write",
    "sys.stderr.write",
)
SENSITIVE_OUTPUT_TOKENS = (
    "account",
    "auth",
    "dsn",
    "market_slug",
    "order",
    "table_name",
    "payload_json",
    "payload",
    "private_key",
    "question",
    "secret",
    "token",
    "wallet",
)
PUBLIC_OUTPUT_REDACTION_MARKERS = (
    "<redacted-account>",
    "<redacted-market",
    "<redacted-order>",
    "<redacted-dsn>",
    "<redacted-question>",
    "<redacted-secret>",
    "<redacted-table>",
    "<redacted-payload>",
    "<redacted-sensitive>",
    "<redacted-wallet>",
    "metric_order",
    "recurring_",
    "redacted_",
    "selected_",
)
LEGACY_PHASE_FLAG_MIGRATION_ALLOWLIST = frozenset(
    (
        "supabase/migrations/20260619010000_paper_trade_journal_records.sql missing report_only boolean",
        "supabase/migrations/20260619010000_paper_trade_journal_records.sql missing readonly boolean",
        "supabase/migrations/20260619010100_paper_nav_snapshots.sql missing report_only boolean",
        "supabase/migrations/20260619010100_paper_nav_snapshots.sql missing readonly boolean",
        "supabase/migrations/20260619010200_outcome_tracking_reports.sql missing report_only boolean",
        "supabase/migrations/20260619010200_outcome_tracking_reports.sql missing readonly boolean",
        "supabase/migrations/20260629000000_paper_strategy_cycle_reports.sql missing readonly boolean",
    ),
)
PHASE_ONE_PAYLOAD_TABLE_REQUIRED_FLAGS = {
    "public.paper_trade_journal_records": ("paper_only", "report_only", "readonly"),
    "public.paper_nav_snapshots": ("paper_only", "report_only", "readonly"),
    "public.outcome_tracking_reports": ("paper_only", "report_only", "readonly"),
    "public.paper_strategy_cycle_reports": ("paper_only", "report_only", "readonly"),
}


def _python_files() -> tuple[Path, ...]:
    return tuple(sorted((*SRC_ROOT.rglob("*.py"), *TESTS_ROOT.rglob("*.py"))))


def _durable_persistence_python_files() -> tuple[Path, ...]:
    durable_suffixes = (
        "_db_row.py",
        "_psycopg.py",
        "_store.py",
    )
    return tuple(
        sorted(
            path
            for path in SRC_ROOT.rglob("*.py")
            if path.name.startswith("supabase_")
            or path.name.endswith(durable_suffixes)
            or "readiness_digest" in path.stem
        )
    )


def _migration_files() -> tuple[Path, ...]:
    return tuple(sorted(MIGRATIONS_ROOT.glob("*.sql")))


def _migration_corpus() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in _migration_files()
    )


def _table_phase_flag_fragments(sql: str) -> dict[str, str]:
    compact_sql = re.sub(r"\s+", " ", sql.lower())
    fragments: dict[str, str] = {}
    statements = tuple(
        statement.strip()
        for statement in compact_sql.split(";")
        if statement.strip()
    )
    for statement in statements:
        match = re.search(
            r"\b(?:create|alter)\s+table\s+(?:if\s+(?:not\s+)?exists\s+)?"
            r"(?P<table>public\.[a-z][a-z0-9_]*)\b",
            statement,
        )
        if match is None:
            continue
        table_name = match.group("table")
        fragments[table_name] = f"{fragments.get(table_name, '')} {statement}"
    return fragments


def _phase_flag_schema_by_table() -> dict[str, str]:
    schema_by_table: dict[str, str] = {}
    for path in _migration_files():
        for table_name, fragment in _table_phase_flag_fragments(
            path.read_text(encoding="utf-8"),
        ).items():
            schema_by_table[table_name] = f"{schema_by_table.get(table_name, '')} {fragment}"
    return schema_by_table


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _dotted_call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_call_name(node.value)
        if parent is None:
            return node.attr
        return f"{parent}.{node.attr}"
    return None


def _literal_string_argument(
    node: ast.Call,
    *,
    position: int,
    keyword_name: str,
) -> str | None:
    if len(node.args) > position:
        value = node.args[position]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            return value.value
    for keyword in node.keywords:
        if keyword.arg == keyword_name and isinstance(keyword.value, ast.Constant):
            if isinstance(keyword.value.value, str):
                return keyword.value.value
    return None


def _is_file_write_call(node: ast.Call) -> bool:
    dotted_name = _dotted_call_name(node.func)
    call_name = _call_name(node.func)
    if dotted_name in {"json.dump", "pickle.dump", "shelve.open"}:
        return True
    if call_name in {"write_bytes", "write_text"}:
        return True
    if call_name != "open":
        return False
    mode_position = 1 if isinstance(node.func, ast.Name) else 0
    mode = _literal_string_argument(
        node,
        position=mode_position,
        keyword_name="mode",
    )
    return mode is not None and any(char in mode for char in FILE_WRITE_MODE_CHARS)


def _source_segment(source_text: str, node: ast.AST) -> str:
    return ast.get_source_segment(source_text, node) or ""


def test_python_persistence_scope_does_not_add_non_postgres_durable_backends() -> None:
    violations: list[str] = []
    for path in _python_files():
        text = path.read_text(encoding="utf-8")
        lowered_text = text.lower()
        if not any(needle in lowered_text for needle in PERSISTENCE_SCOPE_NEEDLES):
            continue
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_name = alias.name.split(".", 1)[0]
                    if root_name in FORBIDDEN_DURABLE_BACKEND_IMPORTS:
                        violations.append(
                            f"{path.relative_to(REPO_ROOT)}:{node.lineno}: import {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                root_name = module_name.split(".", 1)[0]
                if root_name in FORBIDDEN_DURABLE_BACKEND_IMPORTS:
                    violations.append(
                        f"{path.relative_to(REPO_ROOT)}:{node.lineno}: import {module_name}"
                    )
            elif isinstance(node, ast.Call):
                call_name = _call_name(node.func)
                if call_name in FORBIDDEN_DURABLE_BACKEND_CALLS:
                    violations.append(
                        f"{path.relative_to(REPO_ROOT)}:{node.lineno}: call {call_name}"
                    )

    assert violations == []


def test_supabase_and_digest_persistence_modules_do_not_add_file_backed_durable_writes() -> None:
    violations: list[str] = []
    durable_files = _durable_persistence_python_files()
    assert durable_files, "expected Supabase/Postgres durable persistence modules"

    for path in durable_files:
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_file_write_call(node):
                continue
            call_name = _dotted_call_name(node.func) or _call_name(node.func) or "call"
            violations.append(
                f"{path.relative_to(REPO_ROOT)}:{node.lineno}: "
                f"{call_name} is not a durable persistence target",
            )

    assert violations == []


def test_supabase_migrations_do_not_document_or_create_alternate_durable_stores() -> None:
    migration_files = _migration_files()
    assert migration_files, "expected Supabase/Postgres migration files"

    violations: list[str] = []
    for path in migration_files:
        sql = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN_MIGRATION_TOKENS:
            if token in sql:
                violations.append(f"{path.relative_to(REPO_ROOT)} contains {token!r}")

    assert violations == []


def test_supabase_migrations_with_payloads_keep_phase_one_hard_flags() -> None:
    violations: list[str] = []
    for path in _migration_files():
        sql = re.sub(r"\s+", " ", path.read_text(encoding="utf-8").lower())
        has_payload = "payload jsonb" in sql or "payload_json jsonb" in sql
        if not has_payload:
            continue
        for required in (
            "paper_only boolean",
            "report_only boolean",
            "readonly boolean",
        ):
            if required not in sql:
                violations.append(f"{path.relative_to(REPO_ROOT).as_posix()} missing {required}")

    unexpected = tuple(
        violation
        for violation in violations
        if violation not in LEGACY_PHASE_FLAG_MIGRATION_ALLOWLIST
    )
    assert unexpected == ()


def test_phase_flag_migration_allowlist_rejects_unknown_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    migrations_root = tmp_path / "supabase" / "migrations"
    migrations_root.mkdir(parents=True)
    monkeypatch.setitem(globals(), "REPO_ROOT", tmp_path)
    monkeypatch.setitem(globals(), "MIGRATIONS_ROOT", migrations_root)
    sql = "create table reports (payload jsonb, paper_only boolean);"
    legacy_path = migrations_root / "20260619010100_paper_nav_snapshots.sql"
    legacy_path.write_text(sql, encoding="utf-8")

    test_supabase_migrations_with_payloads_keep_phase_one_hard_flags()

    (migrations_root / "new_reports.sql").write_text(sql, encoding="utf-8")
    with pytest.raises(AssertionError):
        test_supabase_migrations_with_payloads_keep_phase_one_hard_flags()


def test_supabase_migration_sequence_backfills_legacy_phase_one_hard_flags() -> None:
    schema_by_table = _phase_flag_schema_by_table()

    missing: list[str] = []
    for table_name, required_flags in PHASE_ONE_PAYLOAD_TABLE_REQUIRED_FLAGS.items():
        table_schema = schema_by_table.get(table_name, "")
        for flag in required_flags:
            flag_column = f"{flag} boolean"
            flag_check = f"check ({flag} is true)"
            if flag_column not in table_schema or flag_check not in table_schema:
                missing.append(f"{table_name} missing final {flag} hard flag")

    assert missing == []


def test_phase_flag_schema_guard_is_table_scoped() -> None:
    sql = """
    alter table if exists public.paper_trade_journal_records
      add column if not exists report_only boolean not null default true;

    alter table if exists public.unrelated_reports
      add constraint unrelated_readonly_true check (readonly is true);
    """

    schema_by_table = _table_phase_flag_fragments(sql)

    assert "readonly boolean" not in schema_by_table["public.paper_trade_journal_records"]
    assert "check (readonly is true)" not in schema_by_table[
        "public.paper_trade_journal_records"
    ]


def test_public_cli_output_paths_do_not_print_dsn_table_or_payload_context() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        lowered_text = text.lower()
        if not any(needle in lowered_text for needle in PUBLIC_OUTPUT_NEEDLES):
            continue
        if not any(token in lowered_text for token in SENSITIVE_OUTPUT_TOKENS):
            continue
        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            call_name = _call_name(node.func)
            dotted_call_name = _dotted_call_name(node.func)
            if call_name != "print" and dotted_call_name not in {
                "sys.stdout.write",
                "sys.stderr.write",
            }:
                continue
            segment = _source_segment(text, node).lower()
            if not any(pattern.search(segment) for pattern in PUBLIC_OUTPUT_PATTERNS):
                continue
            if not any(token in segment for token in SENSITIVE_OUTPUT_TOKENS):
                continue
            if "payload" in segment and "len(payload)" in segment:
                continue
            if not any(marker in segment for marker in PUBLIC_OUTPUT_REDACTION_MARKERS):
                violations.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}: {segment}")

    assert violations == []


def test_durable_only_policy_is_documented_for_supabase_migration_work() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    required_phrases = (
        "durable-only audit",
        "local supabase/postgres is the only durable persistence target",
        "public cli output must not expose dsn values, table names, or payload json",
        "market slugs, market questions, secrets, tokens, private keys",
        "wallet/account identifiers, and order-like fields. failure paths",
        "sqlite, redis, mongo, sqlalchemy-managed engines, file journals, and hosted database targets remain disallowed",
    )
    for phrase in required_phrases:
        assert phrase in text
