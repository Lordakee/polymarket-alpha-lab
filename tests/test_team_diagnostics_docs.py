from __future__ import annotations

from pathlib import Path
import re


DOC_PATH = Path("docs/team-diagnostics-readonly.md")
README_PATH = Path("README.md")
ENV_EXAMPLE_PATH = Path(".env.example")
TEAM_AGENT_FRAMEWORK_PATH = Path("docs/team-agent-framework.md")
TEAM_FORECAST_RUNBOOK_PATH = Path("docs/team-forecast-supabase-runbook.md")

EXPECTED_ENV_VARS = (
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_DSN",
    "POLYMARKET_ALPHA_LAB_TEAM_PROFILE_DB_TABLE",
    "POLYMARKET_ALPHA_LAB_TEAM_ROUTE_DB_TABLE",
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_DB_TABLE",
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_EVIDENCE_DB_TABLE",
    "POLYMARKET_ALPHA_LAB_TEAM_FORECAST_OUTCOME_DB_TABLE",
)

EXPECTED_TABLES = (
    "team_profiles",
    "team_market_routes",
    "team_forecasts",
    "team_forecast_evidence",
    "team_forecast_outcomes",
)

SNAPSHOT_ENV_VARS = (
    "POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_DSN",
    "POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE",
)

EXPECTED_TEAM_MEMORY_READINESS_DIGEST_SAMPLE_LINE = (
    "team-memory-readiness-digest: digest_status=pass "
    "recommended_next_step=allow_team_memory_readiness_use "
    "team_count=1 pass_count=1 watch_count=0 blocked_count=0 "
    "source_statuses=crypto_btc:pass:1200:12/3 "
    "source_config_versions=crypto_btc:team-diagnostics-snapshot-history-v0 "
    "reason_code_counts=team_memory_readiness_digest_passed:1 "
    "reason_codes=team_memory_readiness_digest_passed "
    "paper_only=True report_only=True readonly=True"
)


def _doc_text() -> str:
    assert DOC_PATH.exists(), f"{DOC_PATH} must exist"
    return DOC_PATH.read_text(encoding="utf-8")


def _section_between(text: str, start: str, end: str | None) -> str:
    assert start in text
    section = text.split(start, 1)[1]
    if end is not None:
        assert end in section
        section = section.split(end, 1)[0]
    return section


def _single_fenced_text_line_after(section: str, marker: str) -> str:
    assert marker in section
    tail = section.split(marker, 1)[1]
    match = re.search(r"```text\n(?P<body>.*?)\n```", tail, flags=re.DOTALL)
    assert match is not None
    lines = tuple(line for line in match.group("body").splitlines() if line)
    assert len(lines) == 1
    return lines[0]


def test_team_diagnostics_readonly_doc_covers_purpose_and_phase_1_boundary() -> None:
    text = _doc_text()
    lower_text = text.lower()

    required_fragments = (
        "team memory",
        "calibration",
        "event template performance",
        "source reliability",
        "evidence quality",
        "read-only/report-only/paper-only",
        "no live trading",
        "auth",
        "wallet",
        "order",
        "account",
        "mutation",
    )
    for fragment in required_fragments:
        assert fragment in lower_text


def test_team_diagnostics_readonly_doc_uses_local_supabase_and_env_surface() -> None:
    text = _doc_text()
    lower_text = text.lower()

    assert "local Supabase/Postgres" in text
    assert "supabase_team_forecast_config" in text
    assert "validate_local_postgres_dsn" in text
    assert "SQLite" in text
    assert "file-journal" in text

    for env_var in EXPECTED_ENV_VARS:
        assert env_var in text
    for table_name in EXPECTED_TABLES:
        assert table_name in text

    forbidden_durable_substitutes = (
        "sqlite fallback",
        "sqlite substitute",
        "file-journal fallback",
        "file-journal substitute",
        "redis fallback",
        "mongo fallback",
    )
    for phrase in forbidden_durable_substitutes:
        assert phrase not in lower_text


def test_team_diagnostics_readonly_doc_includes_command_and_troubleshooting() -> None:
    text = _doc_text()
    lower_text = text.lower()

    assert (
        "polymarket-alpha-lab team-diagnostics --team-id crypto_btc --limit 100"
        in text
    )
    assert "once the command is available" in lower_text

    troubleshooting_fragments = (
        "missing db env",
        "non-local dsn",
        "no rows",
        "pending outcomes",
    )
    for fragment in troubleshooting_fragments:
        assert fragment in lower_text


def test_team_diagnostics_readonly_doc_omits_secrets_and_live_authorization() -> None:
    lower_text = _doc_text().lower()

    forbidden_patterns = (
        r"postgres(?:ql)?://",
        r"\bdb\.[a-z0-9-]+\.supabase\.co\b",
        r"\b[a-z0-9-]+\.pooler\.supabase\.com\b",
        r"supabase_(?:anon|service)_key",
        r"service_role",
        r"\bsbp_[a-z0-9_=-]{8,}",
        r"\beyj[a-z0-9_-]{20,}",
        r"\bsk-[a-z0-9_-]{20,}",
        r"\benable(?:s|d)? live\b",
        r"\bauthori[sz]e(?:s|d)? live\b",
        r"\bpermit(?:s|ted)? live\b",
        r"\benable(?:s|d)? auth\b",
        r"\bauthori[sz]e(?:s|d)? auth\b",
        r"\bpermit(?:s|ted)? auth\b",
        r"\benable(?:s|d)? wallet\b",
        r"\bauthori[sz]e(?:s|d)? wallet\b",
        r"\bpermit(?:s|ted)? wallet\b",
        r"\benable(?:s|d)? account\b",
        r"\bauthori[sz]e(?:s|d)? account\b",
        r"\bpermit(?:s|ted)? account\b",
        r"\benable(?:s|d)? order\b",
        r"\bauthori[sz]e(?:s|d)? order\b",
        r"\bpermit(?:s|ted)? order\b",
    )
    for pattern in forbidden_patterns:
        assert re.search(pattern, lower_text) is None


def test_existing_team_docs_index_readonly_team_diagnostics_runbook() -> None:
    for path in (README_PATH, TEAM_AGENT_FRAMEWORK_PATH, TEAM_FORECAST_RUNBOOK_PATH):
        assert path.exists(), f"{path} must exist"
        text = path.read_text(encoding="utf-8")
        lower_text = text.lower()

        assert "team-diagnostics-readonly.md" in text
        assert "local Supabase/Postgres" in text
        assert "Phase 1" in text
        assert "diagnostics" in lower_text
        assert "read-only" in lower_text or "readonly" in lower_text
        assert "paper" in lower_text
        assert "report" in lower_text


def test_team_diagnostics_docs_cover_snapshot_persistence_surface() -> None:
    for path in (DOC_PATH, README_PATH):
        assert path.exists(), f"{path} must exist"
        text = path.read_text(encoding="utf-8")
        lower_text = text.lower()

        assert "team_diagnostics_snapshots" in text
        assert "internal report persistence" in lower_text
        assert "local Supabase/Postgres" in text
        assert "Phase 1" in text
        assert "paper-only/report-only/readonly" in text
        for env_var in SNAPSHOT_ENV_VARS:
            assert env_var in text


def test_team_diagnostics_docs_cover_snapshot_history_readback_surface() -> None:
    expected_history_output_fields = (
        "status=",
        "snapshot_count=",
        "required_snapshot_count=",
        "earliest_generated_at=",
        "latest_generated_at=",
        "span_seconds=",
        "status_counts=",
        "evidence_quality_average_delta=",
        "memory_eligible_delta=",
        "settled_calibration_delta=",
        "duplicate_latest_generated_at=",
        "reason_codes=",
        "paper_only=True",
        "report_only=True",
        "readonly=True",
    )
    expected_gate_output_fields = (
        "gate_status=",
        "recommended_next_step=",
        "source_config_version=",
        "source_generated_at=",
        "source_snapshot_count=",
        "source_required_snapshot_count=",
        "source_status=",
        "source_span_seconds=",
        "source_status_counts=",
        "source_reason_codes=",
        "latest_snapshot_age_seconds=",
        "reason_code_counts=",
        "evidence_quality_average_delta=",
        "memory_eligible_delta=",
        "settled_calibration_delta=",
        "duplicate_latest_generated_at=",
        "reason_codes=",
        "paper_only=True",
        "report_only=True",
        "readonly=True",
    )
    stale_gate_history_fields = (
        " status=",
        " snapshot_count=",
        " required_snapshot_count=",
        " earliest_generated_at=",
        " latest_generated_at=",
        " span_seconds=",
        " status_counts=",
    )
    required_gate_fragments = (
        "team-diagnostics-snapshot-history-gate",
        "local Supabase/Postgres readback",
        "persisted diagnostics snapshot history",
        "pass/watch/blocked",
        "gate status `pass`",
        "gate status `watch`",
        "gate status `blocked`",
        "insufficient, stale, or duplicate-latest history",
    )
    forbidden_cli_flags = (
        "--dsn",
        "--db-dsn",
        "--table",
        "--db-table",
        "--snapshot-dsn",
        "--snapshot-table",
        "--persist",
        "--live",
        "--auth",
        "--wallet",
        "--order",
        "--private-key",
        "--account",
    )

    for path in (DOC_PATH, README_PATH):
        assert path.exists(), f"{path} must exist"
        text = path.read_text(encoding="utf-8")
        lower_text = text.lower()
        if path == DOC_PATH:
            history_section = _section_between(
                text,
                "## Snapshot History Readback",
                "## Snapshot History Gate",
            )
            gate_section = _section_between(
                text,
                "## Snapshot History Gate",
                "## What Diagnostics Evaluate",
            )
        else:
            history_section = _section_between(
                text,
                "Read persisted local Supabase/Postgres snapshot history",
                "Gate persisted diagnostics snapshot history",
            )
            gate_section = _section_between(
                text,
                "Gate persisted diagnostics snapshot history",
                "## Project Iron Rules",
            )

        assert "team-diagnostics-snapshot-history" in text
        for fragment in required_gate_fragments:
            assert fragment in text
        assert "persisted local Supabase/Postgres" in text
        assert "team_diagnostics_snapshots" in text
        assert "long-term team-memory" in lower_text
        assert "readback" in lower_text
        assert "paper-only/report-only/readonly" in text
        assert "no live trading" in lower_text
        assert "order" in lower_text
        for env_var in SNAPSHOT_ENV_VARS:
            assert env_var in text
        for field in expected_history_output_fields:
            assert field in history_section
        for field in expected_gate_output_fields:
            assert field in gate_section
        for field in stale_gate_history_fields:
            assert field not in gate_section
        for flag in forbidden_cli_flags:
            assert flag not in history_section
            assert flag not in gate_section


def test_team_diagnostics_docs_cover_team_memory_readiness_digest_surface() -> None:
    expected_digest_output_fields = (
        "digest_status=",
        "recommended_next_step=",
        "team_count=",
        "pass_count=",
        "watch_count=",
        "blocked_count=",
        "source_statuses=crypto_btc:pass:1200:12/3",
        "source_config_versions=crypto_btc:team-diagnostics-snapshot-history-v0",
        "reason_code_counts=team_memory_readiness_digest_passed:1",
        "reason_codes=",
        "paper_only=True",
        "report_only=True",
        "readonly=True",
    )
    required_digest_fragments = (
        "team-memory-readiness-digest",
        "Phase 1 read-only/report-only/paper-only local Supabase/Postgres readback",
        "per-team digest sources backed by diagnostics snapshot history gate results",
        "TeamMemoryReadinessDigestSource",
        "pass/watch/blocked digest",
        "digest status `pass`",
        "digest status `watch`",
        "digest status `blocked`",
        "allow_team_memory_readiness_use",
        "throttle_team_memory_readiness_use",
        "block_team_memory_readiness_use",
        "team_memory_readiness_digest_empty_sources",
    )
    forbidden_cli_flags = (
        "--dsn",
        "--db-dsn",
        "--table",
        "--db-table",
        "--snapshot-dsn",
        "--snapshot-table",
        "--persist",
        "--live",
        "--auth",
        "--wallet",
        "--order",
        "--private-key",
        "--account",
    )

    for path in (DOC_PATH, README_PATH):
        assert path.exists(), f"{path} must exist"
        text = path.read_text(encoding="utf-8")
        lower_text = text.lower()
        if path == DOC_PATH:
            digest_section = _section_between(
                text,
                "## Team Memory Readiness Digest",
                "## What Diagnostics Evaluate",
            )
            digest_sample_line = _single_fenced_text_line_after(
                digest_section,
                "Sample digest output fields:",
            )
            assert (
                digest_sample_line
                == EXPECTED_TEAM_MEMORY_READINESS_DIGEST_SAMPLE_LINE
            )
        else:
            digest_section = _section_between(
                text,
                "Summarize team readiness for long-term team-memory",
                "## Project Iron Rules",
            )

        assert "polymarket-alpha-lab team-memory-readiness-digest" in digest_section
        assert "local Supabase/Postgres readback" in digest_section
        assert (
            "per-team digest sources backed by diagnostics snapshot history gate results"
            in digest_section
        )
        assert "team_diagnostics_snapshots" in digest_section
        assert "no live trading" in lower_text
        assert "no order path" in lower_text
        for fragment in required_digest_fragments:
            assert fragment in digest_section
        for env_var in SNAPSHOT_ENV_VARS:
            assert env_var in digest_section
        for field in expected_digest_output_fields:
            assert field in digest_section
        for flag in forbidden_cli_flags:
            assert flag not in digest_section


def test_env_example_lists_team_diagnostics_snapshot_env_surface() -> None:
    assert ENV_EXAMPLE_PATH.exists(), f"{ENV_EXAMPLE_PATH} must exist"
    text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    lines = tuple(text.splitlines())

    for env_var in SNAPSHOT_ENV_VARS:
        assert any(line.startswith(f"{env_var}=") for line in lines)

    assert "POLYMARKET_ALPHA_LAB_TEAM_DIAGNOSTICS_SNAPSHOT_DB_TABLE=" in lines
    assert "postgresql://" not in text
