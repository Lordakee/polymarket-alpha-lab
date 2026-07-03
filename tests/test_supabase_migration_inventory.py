from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass
import re
from pathlib import Path

import pytest

from polymarket_alpha_lab.supabase_migration_inventory import (
    SupabaseMigrationInventoryEntry,
    build_supabase_migration_inventory,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "supabase_migration_inventory.py"
)
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"


def _write_migration(directory: Path, file_name: str, sql: str) -> None:
    (directory / file_name).write_text(sql, encoding="utf-8")


def test_inventory_builds_sorted_sequence_and_sql_fragment_metadata(tmp_path: Path) -> None:
    _write_migration(
        tmp_path,
        "20260602000000_beta_report.sql",
        """
        create table if not exists public.beta_report (
            report_sha256 text primary key,
            paper_only boolean not null default true,
            report_only boolean not null default true,
            readonly boolean not null default true
        );
        create index if not exists idx_beta_report
            on public.beta_report (report_sha256);
        """,
    )
    _write_migration(
        tmp_path,
        "20260601000000_alpha_report.sql",
        """
        create table if not exists public.alpha_report (
            report_sha256 text primary key,
            payload jsonb not null,
            paper_only boolean not null default true,
            report_only boolean not null default true,
            readonly boolean not null default true
        );
        alter table public.alpha_report
            add constraint alpha_payload_is_object
            check (jsonb_typeof(payload) = 'object');
        """,
    )

    report = build_supabase_migration_inventory(tmp_path)

    assert report.migration_count == 2
    assert tuple(entry.file_name for entry in report.entries) == (
        "20260601000000_alpha_report.sql",
        "20260602000000_beta_report.sql",
    )
    first = report.entries[0]
    assert first.sequence_index == 1
    assert first.timestamp == "20260601000000"
    assert first.slug == "alpha_report"
    assert re.fullmatch(r"[a-f0-9]{64}", first.sql_sha256) is not None
    assert first.create_table_count == 1
    assert first.create_index_count == 0
    assert first.alter_table_count == 1
    assert first.function_count == 0
    assert first.table_names == ("public.alpha_report",)
    assert first.has_paper_only_flag is True
    assert first.has_report_only_flag is True
    assert first.has_readonly_flag is True


def test_inventory_summarizes_duplicate_timestamps(tmp_path: Path) -> None:
    _write_migration(
        tmp_path,
        "20260601000000_alpha_report.sql",
        "create table if not exists public.alpha_report (id text);",
    )
    _write_migration(
        tmp_path,
        "20260601000000_beta_report.sql",
        "create table if not exists public.beta_report (id text);",
    )

    report = build_supabase_migration_inventory(tmp_path)

    assert report.duplicate_timestamps == (
        report.duplicate_timestamps[0].__class__(
            timestamp="20260601000000",
            file_names=(
                "20260601000000_alpha_report.sql",
                "20260601000000_beta_report.sql",
            ),
        ),
    )


def test_inventory_summarizes_unsafe_durable_backend_tokens(tmp_path: Path) -> None:
    _write_migration(
        tmp_path,
        "20260601000000_alpha_report.sql",
        """
        create table if not exists public.alpha_report (id text);
        -- sqlite cache notes are not allowed in durable migrations.
        select 'postgresql://example.invalid/hidden';
        """,
    )

    report = build_supabase_migration_inventory(tmp_path)

    assert tuple(
        (finding.file_name, finding.timestamp, finding.token, finding.line_number)
        for finding in report.unsafe_durable_backend_tokens
    ) == (
        (
            "20260601000000_alpha_report.sql",
            "20260601000000",
            "sqlite",
            3,
        ),
        (
            "20260601000000_alpha_report.sql",
            "20260601000000",
            "postgresql://",
            4,
        ),
    )
    assert "example.invalid" not in report.unsafe_durable_backend_tokens[1].fragment
    assert report.unsafe_durable_backend_tokens[1].fragment == (
        "select '<redacted-durable-url>"
    )


def test_inventory_dataclasses_are_frozen_and_module_scope_is_readonly() -> None:
    import polymarket_alpha_lab.supabase_migration_inventory as module

    exported_dataclasses = (
        getattr(module, exported_name)
        for exported_name in module.__all__
        if isinstance(getattr(module, exported_name), type)
    )
    assert all(is_dataclass(value) for value in exported_dataclasses)

    entry = SupabaseMigrationInventoryEntry(
        sequence_index=1,
        file_name="20260601000000_alpha_report.sql",
        timestamp="20260601000000",
        slug="alpha_report",
        sql_sha256="0" * 64,
        line_count=1,
        create_table_count=1,
        create_index_count=0,
        alter_table_count=0,
        function_count=0,
        table_names=("public.alpha_report",),
        has_paper_only_flag=True,
        has_report_only_flag=True,
        has_readonly_flag=True,
    )
    with pytest.raises(FrozenInstanceError):
        entry.slug = "changed"  # type: ignore[misc]

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(MODULE_PATH))
    imported_roots: set[str] = set()
    write_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in {"open", "write_text"}:
                write_calls.append(func.id)
            elif isinstance(func, ast.Attribute) and func.attr in {
                "open",
                "write_bytes",
                "write_text",
            }:
                write_calls.append(func.attr)

    assert imported_roots.isdisjoint(
        {"psycopg", "requests", "httpx", "socket", "sqlite3", "redis", "pymongo"},
    )
    assert write_calls == []
    assert re.search(r"\b(live|auth|wallet|order|account)\b", source.lower()) is None


def test_real_repo_migrations_have_clean_phase_one_inventory() -> None:
    report = build_supabase_migration_inventory(MIGRATIONS_DIR)

    assert report.migration_count == len(tuple(MIGRATIONS_DIR.glob("*.sql")))
    assert report.migration_count > 0
    assert report.duplicate_timestamps == ()
    assert report.unsafe_durable_backend_tokens == ()
    assert tuple(entry.sequence_index for entry in report.entries) == tuple(
        range(1, report.migration_count + 1),
    )
