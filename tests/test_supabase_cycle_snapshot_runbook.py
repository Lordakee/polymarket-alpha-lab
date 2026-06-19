from __future__ import annotations

import re
from pathlib import Path


RUNBOOK_PATH = Path("docs/supabase-cycle-snapshot-runbook.md")


def _runbook_text() -> str:
    assert RUNBOOK_PATH.exists(), f"{RUNBOOK_PATH} must exist"
    return RUNBOOK_PATH.read_text(encoding="utf-8")


def test_supabase_cycle_snapshot_runbook_documents_local_apply_and_verify_commands():
    text = _runbook_text()

    required_fragments = (
        "sudo -n docker ps",
        "sudo -n docker exec supabase-db psql",
        "/home/ubuntu/supabase/node_modules/.bin/supabase",
        "supabase/migrations/20260619000000_paper_recommendation_cycle_snapshots.sql",
        "psql -v ON_ERROR_STOP=1",
        "postgres.<tenant>",
        "paper_recommendation_cycle_snapshots",
    )

    for fragment in required_fragments:
        assert fragment in text


def test_supabase_cycle_snapshot_runbook_columns_match_committed_migration():
    text = _runbook_text()

    expected_columns = (
        "snapshot_sha256",
        "generated_at",
        "config_version",
        "final_status",
        "stage_counts",
        "artifact_counts",
        "reason_codes",
        "payload",
        "paper_only",
        "report_only",
        "readonly",
        "inserted_at",
    )
    for column in expected_columns:
        assert column in text

    stale_column_names = (
        "stage_count",
        "artifact_count",
        "blocked_artifact_count",
        "watch_artifact_count",
        "stage_counts_json",
        "artifact_counts_json",
        "payload_json",
    )
    for column in stale_column_names:
        assert f"`{column}`" not in text


def test_supabase_cycle_snapshot_runbook_stays_local_and_omits_sensitive_terms():
    text = _runbook_text()
    lower_text = text.lower()

    secret_value_patterns = (
        r"postgres(?:ql)?://",
        r"supabase_(?:anon|service)_key",
        r"service_role",
        r"eyj[a-z0-9_-]{20,}",
        r"sk-[a-z0-9_-]{20,}",
    )
    for pattern in secret_value_patterns:
        assert re.search(pattern, lower_text) is None

    guarded_terms = (
        "password",
        "dsn",
        "token",
        "service-role",
        "service role",
        "secret",
        "live trading",
        "wallet",
        "order",
    )
    allowed_prefixes = (
        "do not ",
        "never ",
        "without ",
        "no ",
        "for local psycopg smoke ",
        "use the tenant-qualified ",
        "- do not ",
        "- never ",
        "- without ",
        "- no ",
        "- for local psycopg smoke ",
        "- use the tenant-qualified ",
    )

    for line in lower_text.splitlines():
        if any(term in line for term in guarded_terms):
            assert line.strip().startswith(allowed_prefixes), line
