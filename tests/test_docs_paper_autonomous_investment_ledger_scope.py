from __future__ import annotations

import re
from pathlib import Path

import pytest


README_PATH = Path("README.md")

REQUIRED_README_PHRASES = (
    "Paper Autonomous Investment Ledger",
    ".venv/bin/polymarket-alpha-lab paper-autonomous-investment-ledger --limit 25",
    ".venv/bin/polymarket-alpha-lab paper-autonomous-investment-ledger --limit 25 --persist",
    ".venv/bin/polymarket-alpha-lab paper-autonomous-investment-ledger-db-history --limit 25",
    "POLYMARKET_ALPHA_LAB_PAPER_BROKER_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_PAPER_BROKER_DB_DSN",
    "POLYMARKET_ALPHA_LAB_PAPER_BROKER_DB_TABLE",
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_DSN",
    "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_INVESTMENT_LEDGER_DB_TABLE",
    "paper broker DB",
    "paper autonomous investment ledger DB",
    "paper-only/report-only/readonly",
    "env-only",
    "reads already-persisted paper broker execution records",
    "stores only the already-built investment ledger report",
    "prints `persisted=True/False`",
    "DB history readback is env-only, read-only, paper-only/report-only/readonly",
    "accepts only `--limit`",
    "does not accept DSN/table CLI flags",
    "does not accept `--persist`",
    "does not persist in db-history",
    "does not write reports",
    "does not read upstream paper broker tables",
    "no live trading",
    "no auth",
    "no key handling",
    "no wallet handling",
    "no account reads",
    "no order construction",
    "no order signing",
    "no order submission",
    "no order cancellation",
    "no exchange mutation",
    "not financial advice",
    "not investment ranking",
    "not order instruction",
    "not execution authorization",
)

REQUIRED_PHASE_1_PHRASES = (
    "paper autonomous investment ledger artifacts",
    "paper autonomous investment ledger DB-history artifacts",
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
    r"\blive[- ]execution\b",
    r"\bauth(?:entication|enticated|orization)?\b",
    r"\bkeys?\b",
    r"\bwallets?\b",
    r"\baccounts?\b",
    r"\borders?\b",
    r"\bsign(?:ing|ed)?\b",
    r"\bsubmit(?:s|ted|ting|mission)?\b",
    r"\bcancel(?:s|led|lation)?\b",
    r"\bmutat(?:e|es|ed|ing|ion)\b",
    r"\bexchange mutation\b",
    r"\bfinancial advice\b",
    r"\binvestment ranking\b",
    r"\border instruction\b",
    r"\bexecution authorization\b",
    r"\bsecrets?\b",
)

ALLOWED_BOUNDARY_MARKERS = (
    "no ",
    "not ",
    "never ",
    "without ",
    "does not",
    "do not",
    "read-only",
    "paper-only/report-only/readonly",
    "boundary",
)


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _readme_phase_1_scope_section() -> str:
    readme_text = _readme_text()
    section_marker = "## Phase 1 Scope"
    next_section_marker = "## Phase 1 Operational Freeze"
    assert section_marker in readme_text
    assert next_section_marker in readme_text
    start = readme_text.index(section_marker)
    end = readme_text.index(next_section_marker)
    assert start < end
    return readme_text[start:end]


def _readme_ledger_section() -> str:
    readme_text = _readme_text()
    section_marker = "Paper Autonomous Investment Ledger"
    next_section_marker = "## Level 1B Node 1 Status"
    assert section_marker in readme_text
    assert next_section_marker in readme_text
    start = readme_text.index(section_marker)
    end = readme_text.index(next_section_marker)
    assert start < end
    return readme_text[start:end]


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
            "The investment ledger authorizes wallet order submission.",
        )


def test_readme_documents_investment_ledger_cli_scope() -> None:
    normalized = _normalized(_readme_ledger_section())

    for phrase in REQUIRED_README_PHRASES:
        assert phrase in normalized


def test_readme_places_investment_ledger_after_allocation_proposal_block() -> None:
    readme_text = _readme_text()
    allocation_marker = "paper-autonomous-allocation-proposal-db-history-health-trend-gate --limit 25"
    section_marker = "Paper Autonomous Investment Ledger"
    default_command_marker = "paper-autonomous-investment-ledger --limit 25"
    persist_command_marker = "paper-autonomous-investment-ledger --limit 25 --persist"
    db_history_command_marker = "paper-autonomous-investment-ledger-db-history --limit 25"
    next_section_marker = "## Level 1B Node 1 Status"

    assert allocation_marker in readme_text
    assert section_marker in readme_text
    assert default_command_marker in readme_text
    assert persist_command_marker in readme_text
    assert db_history_command_marker in readme_text
    assert next_section_marker in readme_text

    allocation_start = readme_text.index(allocation_marker)
    section_start = readme_text.index(section_marker, allocation_start)
    default_command_start = readme_text.index(default_command_marker, section_start)
    persist_command_start = readme_text.index(persist_command_marker, default_command_start)
    db_history_command_start = readme_text.index(
        db_history_command_marker,
        persist_command_start,
    )
    next_section_start = readme_text.index(next_section_marker)

    assert (
        allocation_start
        < section_start
        < default_command_start
        < persist_command_start
        < db_history_command_start
        < next_section_start
    )


def test_readme_investment_ledger_section_omits_secret_values() -> None:
    _assert_no_secret_values(_readme_ledger_section())


def test_readme_investment_ledger_section_keeps_live_auth_order_terms_in_boundary_language() -> None:
    _assert_guarded_terms_are_boundary_language(_readme_ledger_section())


def test_readme_phase_1_scope_mentions_investment_ledger_artifacts() -> None:
    normalized = _normalized(_readme_phase_1_scope_section())

    for phrase in REQUIRED_PHASE_1_PHRASES:
        assert phrase in normalized
