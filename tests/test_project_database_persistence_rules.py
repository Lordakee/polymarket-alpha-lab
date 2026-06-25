from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_project_database_persistence_iron_rule_requires_local_supabase_postgres():
    instructions = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
    normalized = " ".join(instructions.split())

    assert "database persistence iron rule" in instructions
    assert "all database-related implementation" in normalized
    assert "local supabase" in normalized
    assert "postgres" in normalized
    assert "only approved database persistence target" in normalized
    assert "alternate database backends" in normalized
    assert "hosted remote database" in normalized
    assert "sqlite" in normalized
    assert "file-backed database substitutes" in normalized
