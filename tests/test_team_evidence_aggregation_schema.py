from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = (
    REPO_ROOT
    / "supabase"
    / "migrations"
    / "20260714000000_team_evidence_aggregation_tables.sql"
)
TABLE = "team_evaluation_attempts"
FILENAME_PATTERN = re.compile(r"^[0-9]{14}_[a-z0-9_]+\.sql$")

FORBIDDEN_TOKENS = (
    "sqlite",
    "redis",
    "mongo",
    "mongodb",
    "mysql",
    "sqlalchemy",
    "database_url",
    "postgresql://",
    "postgres://",
    "file:",
    "http://",
    "https://",
    "supabase_url",
    "service_role",
    "anon_key",
    "create_client",
)
REMOVED_COLUMN_TOKENS = (
    "lineage_id",
    "revision_no",
    "supersedes_attempt_id",
    "decision",
    "evidence_count",
    "warning_count",
    "scope_kind",
)
MUTATION_PATTERN = re.compile(r"\b(update|delete|drop|truncate)\b")

EXPECTED_COLUMNS = (
    "tea_id text primary key",
    "tfr_id text not null",
    "attempted_at timestamptz not null",
    "status text not null",
    "hard_flag boolean not null",
    "scope_version text not null",
    "scope_key text not null",
    "config_version text not null",
    "config_digest text not null",
    "diagnostic_record_count integer not null",
    "arithmetic_record_count integer not null",
    "payload_sha256 text not null",
    "evaluation_scope_payload jsonb not null",
    "paper_only boolean not null default true",
    "report_only boolean not null default true",
    "readonly boolean not null default true",
    "created_at timestamptz not null default now()",
)

_RESULT = "evaluation_scope_payload -> 'node2_result' -> 'result'"
EXPECTED_CHECKS = (
    "check (tea_id <> '')",
    "check (tfr_id <> '')",
    "check (status in ('ready', 'watch', 'blocked'))",
    "check (diagnostic_record_count >= 0)",
    "check (arithmetic_record_count >= 0)",
    "check (length(payload_sha256) = 64)",
    "check (payload_sha256 ~ '^[a-f0-9]{64}$')",
    "check (length(scope_key) = 64)",
    "check (scope_key ~ '^[a-f0-9]{64}$')",
    "check (length(config_digest) = 64)",
    "check (scope_version <> '')",
    "check (config_version <> '')",
    "check (jsonb_typeof(evaluation_scope_payload) = 'object')",
    "check (jsonb_typeof(evaluation_scope_payload -> 'domain_context') = 'object')",
    "check ((evaluation_scope_payload ->> 'scope_version' = scope_version) is true)",
    f"check (({_RESULT} ->> 'status' = status) is true)",
    f"check ((({_RESULT} ->> 'evaluated_at')::timestamptz = attempted_at) is true)",
    f"check (({_RESULT} ->> 'config_version' = config_version) is true)",
    f"check (({_RESULT} ->> 'config_digest' = config_digest) is true)",
    f"check ((({_RESULT} ->> 'diagnostic_record_count')::integer"
    " = diagnostic_record_count) is true)",
    f"check ((({_RESULT} ->> 'arithmetic_record_count')::integer"
    " = arithmetic_record_count) is true)",
    f"check ((({_RESULT} -> 'contradiction' ->> 'status' = 'blocked')"
    " = hard_flag) is true)",
    "check ((evaluation_scope_payload -> 'run_metadata' ->> 'paper_only'"
    " = 'true') is true)",
    "check ((evaluation_scope_payload -> 'run_metadata' ->> 'report_only'"
    " = 'true') is true)",
    "check ((evaluation_scope_payload -> 'run_metadata' ->> 'readonly'"
    " = 'true') is true)",
    f"check (({_RESULT} ->> 'paper_only' = 'true') is true)",
    f"check (({_RESULT} ->> 'report_only' = 'true') is true)",
    f"check (({_RESULT} ->> 'readonly' = 'true') is true)",
    "check (paper_only is true)",
    "check (report_only is true)",
    "check (readonly is true)",
)

EXPECTED_RUN_INDEX = (
    "create index if not exists team_evaluation_attempts_hard_by_run_idx"
    " on public.team_evaluation_attempts"
    " (tfr_id, attempted_at desc, tea_id desc)"
    " where hard_flag is true and status in ('ready', 'watch', 'blocked')"
)
EXPECTED_SCOPE_INDEX = (
    "create index if not exists team_evaluation_attempts_hard_by_scope_idx"
    " on public.team_evaluation_attempts"
    " (scope_version, scope_key, attempted_at desc, tea_id desc)"
    " where hard_flag is true and status in ('ready', 'watch', 'blocked')"
)


def _normalized() -> str:
    assert MIGRATION_PATH.is_file(), f"missing migration: {MIGRATION_PATH.name}"
    return re.sub(r"\s+", " ", MIGRATION_PATH.read_text(encoding="utf-8").lower())


def _table_fragments(normalized: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    opener = f"create table if not exists public.{TABLE} ("
    start = normalized.index(opener) + len(opener)
    depth = 1
    end = start
    while depth:
        if normalized[end] == "(":
            depth += 1
        elif normalized[end] == ")":
            depth -= 1
        end += 1
    body = normalized[start : end - 1]

    fragments: list[str] = []
    depth = 0
    current = ""
    for char in body:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            fragments.append(current.strip())
            current = ""
            continue
        current += char
    fragments.append(current.strip())
    return (
        tuple(f for f in fragments if not f.startswith("check")),
        tuple(f for f in fragments if f.startswith("check")),
    )


def test_migration_filename_is_exact_and_canonical() -> None:
    assert MIGRATION_PATH.name == "20260714000000_team_evidence_aggregation_tables.sql"
    assert FILENAME_PATTERN.fullmatch(MIGRATION_PATH.name) is not None


def test_single_create_table_statement_for_attempts_table() -> None:
    normalized = _normalized()
    assert len(re.findall(r"create table\b", normalized)) == 1
    assert f"create table if not exists public.{TABLE} (" in normalized


def test_exact_promoted_column_definitions() -> None:
    columns, _ = _table_fragments(_normalized())
    assert columns == EXPECTED_COLUMNS


def test_exact_check_constraint_set() -> None:
    _, checks = _table_fragments(_normalized())
    assert set(checks) == set(EXPECTED_CHECKS)


def test_exact_partial_indexes() -> None:
    statements = tuple(re.findall(r"create index[^;]+", _normalized()))
    assert statements == (EXPECTED_RUN_INDEX, EXPECTED_SCOPE_INDEX)


def test_removed_invented_columns_are_absent() -> None:
    lowered = _normalized()
    assert [token for token in REMOVED_COLUMN_TOKENS if token in lowered] == []


def test_forbidden_backend_and_url_tokens_are_absent() -> None:
    lowered = _normalized()
    assert [token for token in FORBIDDEN_TOKENS if token in lowered] == []


def test_migration_is_append_only_without_mutations() -> None:
    assert MUTATION_PATTERN.findall(_normalized()) == []
