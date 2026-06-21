from __future__ import annotations

import re
from pathlib import Path

import pytest


DOC_PATH = Path("docs/strategy-candidate-research-queue-history-db-persistence.md")
MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260621000001_strategy_candidate_research_queue_history_reports.sql",
)
DB_ROW_PATH = Path(
    "src/polymarket_alpha_lab/strategy_candidate_research_queue_history_db_row.py",
)

REQUIRED_HEADINGS = (
    "# Strategy Candidate Research Queue History DB Persistence",
    "## Environment",
    "## Migration",
    "## CLI Command",
    "## Scope Boundary",
)

REQUIRED_SCOPE_PHRASES = (
    "persistence-only",
    "paper-only, report-only, and readonly",
    "phase 1 boundary",
    "no live trading",
    "no auth",
    "no wallet access",
    "no private keys",
    "no account reads",
    "no order construction",
    "no signing",
    "no order submission",
    "no cancellation",
    "no replacement",
    "no exchange mutation",
)

REQUIRED_HISTORY_DOC_PHRASES = (
    "paper_strategy_candidate_research_queue_history_reports",
    "polymarket_alpha_lab.strategy_candidate_research_queue_history",
    "paperstrategycandidateresearchqueuehistoryreport",
    "polymarket_alpha_lab.strategy_candidate_research_queue_history_db_row",
    "paperstrategycandidateresearchqueuehistorydbrow",
    "strategy-candidate-research-queue-history",
    "reads already-persisted strategy candidate research queue reports",
    "--persist",
    "without --persist",
    "does not write history rows unless --persist is provided",
    "persists only the generated aggregate history report row",
    "strategy candidate research queue history db config",
    "aggregate-only summary",
    "must not print dsns, table names, payload json, raw db records, secrets, or env contents",
)

HISTORY_ENV_VARS = (
    "POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_DSN",
    "POLYMARKET_ALPHA_LAB_STRATEGY_CANDIDATE_RESEARCH_QUEUE_HISTORY_DB_TABLE",
)

SECRET_VALUE_PATTERNS = (
    r"postgres(?:ql)?://",
    r"\b(?:database_url|dsn|supabase_[a-z_]*key|pgpassword)\s*=",
    r"\bservice_role\b",
    r"\beyj[a-z0-9_-]{20,}",
    r"\bsk-[a-z0-9_-]{20,}",
    r"-----begin [a-z ]*private key-----",
)

GUARDED_TERM_PATTERNS = (
    r"\blive trading\b",
    r"\bauth(?:entication|enticated)?\b",
    r"\bwallet access\b",
    r"\bwallets?\b",
    r"\bprivate[- ]keys?\b",
    r"\baccount reads?\b",
    r"\border construction\b",
    r"\border signing\b",
    r"\border submission\b",
    r"\bsigning\b",
    r"\bsubmission\b",
    r"\bcancellation\b",
    r"\breplacement\b",
    r"\bexchange mutation\b",
)

ALLOWED_BOUNDARY_MARKERS = (
    "no ",
    "not ",
    "never ",
    "without ",
    "exclude",
    "excluded",
    "must not",
    "does not",
    "do not",
    "read-only",
    "readonly",
    "paper-only",
    "report-only",
    "redact",
    "redacted",
)

FORBIDDEN_PERSISTENCE_FILE_FRAGMENTS = (
    "auth",
    "private_key",
    "wallet",
    "clob",
    "order_args",
    "post_order",
    "submit",
    "cancel",
    "replace",
    "exchange",
)

FORBIDDEN_DB_ROW_FILE_FRAGMENTS = tuple(
    fragment
    for fragment in FORBIDDEN_PERSISTENCE_FILE_FRAGMENTS
    if fragment != "replace"
)


def _doc_text() -> str:
    assert DOC_PATH.exists(), f"{DOC_PATH} must exist"
    return DOC_PATH.read_text(encoding="utf-8")


def _migration_text() -> str:
    assert MIGRATION_PATH.exists(), f"{MIGRATION_PATH} must exist"
    return MIGRATION_PATH.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _assert_no_secret_values(text: str) -> None:
    lower_text = text.lower()
    for pattern in SECRET_VALUE_PATTERNS:
        assert re.search(pattern, lower_text) is None, pattern


def _assert_guarded_terms_are_boundary_language(text: str) -> None:
    for line in text.lower().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(re.search(pattern, stripped) for pattern in GUARDED_TERM_PATTERNS):
            assert any(marker in stripped for marker in ALLOWED_BOUNDARY_MARKERS), line


def test_scope_guard_rejects_secret_values_and_positive_live_language() -> None:
    with pytest.raises(AssertionError):
        _assert_no_secret_values(
            "Set DATABASE_URL=postgresql://user:pass@example.invalid/db",
        )

    with pytest.raises(AssertionError):
        _assert_guarded_terms_are_boundary_language(
            "Operators can use wallet access for order submission.",
        )


def test_doc_has_required_sections() -> None:
    text = _doc_text()

    for heading in REQUIRED_HEADINGS:
        assert heading in text


def test_doc_states_required_persistence_scope() -> None:
    normalized = _normalized(_doc_text()).lower()

    for phrase in REQUIRED_SCOPE_PHRASES:
        assert phrase in normalized


def test_doc_names_history_env_vars_and_artifacts() -> None:
    normalized = _normalized(_doc_text()).lower()

    for env_var in HISTORY_ENV_VARS:
        assert env_var in _doc_text()
    for phrase in REQUIRED_HISTORY_DOC_PHRASES:
        assert phrase in normalized


def test_doc_does_not_describe_history_cli_as_unconditionally_non_persisting() -> None:
    normalized = _normalized(_doc_text()).lower()

    assert "it does not persist rows. its output" not in normalized


def test_doc_omits_secret_values() -> None:
    _assert_no_secret_values(_doc_text())


def test_doc_keeps_live_terms_in_exclusions() -> None:
    _assert_guarded_terms_are_boundary_language(_doc_text())


def test_migration_defines_history_report_table() -> None:
    sql = _migration_text()

    assert (
        "create table if not exists "
        "public.paper_strategy_candidate_research_queue_history_reports"
    ) in sql
    for column in (
        "report_sha256 text primary key",
        "generated_at timestamptz not null",
        "source_report_count integer not null",
        "first_source_generated_at timestamptz",
        "last_source_generated_at timestamptz",
        "action_status_research_ready_count integer not null",
        "action_status_watch_count integer not null",
        "action_status_blocked_count integer not null",
        "research_status_ready_count integer not null",
        "research_status_watch_count integer not null",
        "research_status_blocked_count integer not null",
        "total_ready_notional numeric not null",
        "total_selected_notional numeric not null",
        "total_suggested_notional numeric not null",
        "latest_action_status text",
        "latest_recommended_next_step text",
        "latest_research_status text",
        "latest_top_research_priority_score numeric",
        "latest_average_research_ready_score numeric",
        "status_transition_count integer not null",
        "ready_notional_delta numeric not null",
        "selected_notional_delta numeric not null",
        "latest_selected_count integer not null",
        "latest_skipped_count integer not null",
        "latest_not_selected_count integer not null",
        "latest_primary_reason_code_counts jsonb not null",
        "latest_reason_codes jsonb not null",
        "payload jsonb not null",
        "paper_only boolean not null default true",
        "report_only boolean not null default true",
        "readonly boolean not null default true",
        "inserted_at timestamptz not null default now()",
    ):
        assert column in sql


def test_migration_enforces_history_invariants() -> None:
    normalized = _normalized(_migration_text()).lower()

    for fragment in (
        "check (report_sha256 ~ '^[a-f0-9]{64}$')",
        "check (source_report_count >= 0)",
        "check (action_status_research_ready_count >= 0)",
        "check (action_status_watch_count >= 0)",
        "check (action_status_blocked_count >= 0)",
        "check (research_status_ready_count >= 0)",
        "check (research_status_watch_count >= 0)",
        "check (research_status_blocked_count >= 0)",
        "check (total_ready_notional >= 0)",
        "check (total_selected_notional >= 0)",
        "check (total_suggested_notional >= 0)",
        "check (latest_top_research_priority_score is null or (latest_top_research_priority_score >= 0 and latest_top_research_priority_score <= 1))",
        "check (latest_average_research_ready_score is null or (latest_average_research_ready_score >= 0 and latest_average_research_ready_score <= 1))",
        "check (status_transition_count >= 0)",
        "check (latest_selected_count >= 0)",
        "check (latest_skipped_count >= 0)",
        "check (latest_not_selected_count >= 0)",
        "check (jsonb_typeof(latest_primary_reason_code_counts) = 'object')",
        "check (jsonb_typeof(latest_reason_codes) = 'array')",
        "check (jsonb_typeof(payload) = 'object')",
        "check (paper_only is true)",
        "check (report_only is true)",
        "check (readonly is true)",
        "check (source_report_count = action_status_research_ready_count + action_status_watch_count + action_status_blocked_count)",
        "check (source_report_count = research_status_ready_count + research_status_watch_count + research_status_blocked_count)",
        "latest_research_status is null and latest_top_research_priority_score is null and latest_average_research_ready_score is null and status_transition_count = 0",
        "check (source_report_count = 0 or last_source_generated_at >= first_source_generated_at)",
        "check (source_report_count = 0 or status_transition_count < source_report_count)",
        "check (source_report_count > 0 or latest_primary_reason_code_counts = '{}'::jsonb)",
        "check (source_report_count > 0 or latest_reason_codes = '[]'::jsonb)",
    ):
        assert fragment in normalized


def test_migration_keeps_status_and_next_step_pairs_nullable_for_empty_history() -> None:
    normalized = _normalized(_migration_text()).lower()

    assert (
        "check (latest_action_status is null or latest_action_status in "
        "('research_ready', 'watch', 'blocked'))"
    ) in normalized
    assert (
        "check (latest_recommended_next_step is null or latest_recommended_next_step in "
        "('review_candidate_research_queue', 'await_fresh_cycle_evidence', "
        "'repair_cycle_evidence'))"
    ) in normalized
    assert (
        "check ((latest_action_status is null and latest_recommended_next_step is null) "
        "or (latest_action_status = 'research_ready' and latest_recommended_next_step = "
        "'review_candidate_research_queue') or (latest_action_status = 'watch' and "
        "latest_recommended_next_step = 'await_fresh_cycle_evidence') or "
        "(latest_action_status = 'blocked' and latest_recommended_next_step = "
        "'repair_cycle_evidence'))"
    ) in normalized
    assert (
        "check (latest_research_status is null or latest_research_status in "
        "('ready', 'watch', 'blocked'))"
    ) in normalized
    assert (
        "check (source_report_count = 0 or (first_source_generated_at is not null "
        "and last_source_generated_at is not null and latest_action_status is not null "
        "and latest_recommended_next_step is not null and latest_research_status is not null))"
    ) in normalized


def test_migration_indexes_history_load_paths() -> None:
    normalized = _normalized(_migration_text()).lower()

    for index_fragment in (
        "(generated_at desc)",
        "(latest_action_status, generated_at desc)",
        "(latest_recommended_next_step, generated_at desc)",
        "(latest_research_status, generated_at desc)",
        "(source_report_count, generated_at desc)",
        "(latest_action_status, latest_research_status, generated_at desc, inserted_at desc, report_sha256 desc)",
    ):
        assert index_fragment in normalized


def test_persistence_files_do_not_reference_live_trading_surfaces() -> None:
    migration_text = _migration_text().lower()
    db_row_text = DB_ROW_PATH.read_text(encoding="utf-8").lower()

    for fragment in FORBIDDEN_PERSISTENCE_FILE_FRAGMENTS:
        assert fragment not in migration_text
    for fragment in FORBIDDEN_DB_ROW_FILE_FRAGMENTS:
        assert fragment not in db_row_text
