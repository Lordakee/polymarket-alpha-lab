from __future__ import annotations

from collections import Counter
from pathlib import Path
import re


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"
MIGRATION_FILENAME_PATTERN = re.compile(r"^[0-9]{14}_[a-z0-9_]+\.sql$")


def test_supabase_migration_versions_are_unique() -> None:
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))

    versions = [path.name.split("_", 1)[0] for path in migration_paths]
    duplicate_versions = {
        version: count for version, count in Counter(versions).items() if count > 1
    }

    assert duplicate_versions == {}


def test_supabase_migration_filenames_are_canonical() -> None:
    migration_paths = sorted(MIGRATIONS_DIR.glob("*.sql"))

    assert migration_paths
    for path in migration_paths:
        assert MIGRATION_FILENAME_PATTERN.fullmatch(path.name) is not None
