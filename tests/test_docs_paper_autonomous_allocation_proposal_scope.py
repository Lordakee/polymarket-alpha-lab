from __future__ import annotations

import re
from pathlib import Path

import pytest


DOC_PATH = Path("docs/paper-autonomous-allocation-proposal.md")
README_PATH = Path("README.md")

REQUIRED_HEADINGS = (
    "# Paper Autonomous Allocation Proposal",
    "## Scope",
    "## Source Reports",
    "## Operator Flow",
    "## Allocation Proposal Status and Next Step",
    "## Paper Allocation Evidence",
    "## Transaction and Cost Awareness",
    "## CLI Contract",
    "## Review Boundaries",
)

REQUIRED_PHRASES = (
    "paper-only/report-only/read-only autonomous allocation proposal",
    "Polymarket probability-event allocation review",
    "already-produced and persisted upstream paper reports",
    "combines upstream paper reports into an allocation proposal status and recommended next step",
    "moves toward autonomous investing only by preparing paper allocation proposals",
    "operator review aids, not approvals",
    "paper notional is paper sizing, not capital commitment",
    "paper allocation proposal rows are not order tickets",
    "a pass status is not permission to trade",
    "not financial advice",
    "not investment ranking",
    "not automatic live investing",
    "not order instruction",
    "not execution authorization",
    "not an approval workflow",
    "not a live-execution signal",
    "no live trading",
    "no auth",
    "no key handling",
    "no wallet handling",
    "no account handling",
    "no account reads",
    "no order construction",
    "no order signing",
    "no order submission",
    "no order cancellation",
    "no order replacement",
    "no exchange mutation",
    "transaction/cost awareness is upstream evidence",
    "no live fee estimation",
    "paper-autonomous-allocation-proposal-db-history --limit 25",
    "reads only persisted final allocation proposal reports",
    "reads the final allocation proposal DB configured by env",
    "does not write reports",
    "does not read upstream tables",
    "does not place orders, approve execution, read accounts, or mutate exchange state",
    "prints aggregate history status, proposal-status counts, latest aggregate allocation counts, duplicate timestamp count, and reason-code summaries",
)

REQUIRED_README_PHRASES = (
    "Paper Autonomous Allocation Proposal",
    "docs/paper-autonomous-allocation-proposal.md",
    ".venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal --limit 25",
    "paper-autonomous-allocation-proposal-persist --limit 25",
    "paper-only/report-only/read-only",
    "env-only",
    "already-persisted upstream reports",
    "accepts only `--limit`",
    "does not accept DSN/table/persist flags",
    "does not write reports",
    "no-write",
    "sibling env-only producer command",
    "writes only that final proposal report",
    "persisted=True/False",
    "does not create live instructions or mutate exchange state",
    "no live trading",
    "no auth",
    "no key handling",
    "no wallet handling",
    "no account handling",
    "no account reads",
    "no order construction",
    "no order signing",
    "no order submission",
    "no order cancellation",
    "no order replacement",
    "no exchange mutation",
    "no investment ranking",
    "not automatic live investing",
    "not an approval workflow",
    ".venv/bin/polymarket-alpha-lab paper-autonomous-allocation-proposal-db-history --limit 25",
    "reads only persisted final allocation proposal reports",
    "reads the final allocation proposal DB configured by env",
    "does not read upstream tables",
    "does not place orders, approve execution, read accounts, or mutate exchange state",
    "prints aggregate history status, proposal-status counts, latest aggregate allocation counts, duplicate timestamp count, and reason-code summaries",
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
    r"\blive fee estimation\b",
    r"\bautomatic live investing\b",
    r"\bauth(?:entication|enticated|orization)?\b",
    r"\bkeys?\b",
    r"\bwallets?\b",
    r"\baccounts?\b",
    r"\borders?\b",
    r"\btrade\b",
    r"\bsign(?:ing|ed)?\b",
    r"\bsubmit(?:s|ted|ting|mission)?\b",
    r"\bcancel(?:s|led|lation)?\b",
    r"\breplac(?:e|es|ed|ement)\b",
    r"\bapprov(?:e|es|ed|ing|al|als)?\b",
    r"\bexecut(?:e|es|ed|ing|ion)\b",
    r"\bmutat(?:e|es|ed|ing|ion)\b",
    r"\bexchange mutation\b",
    r"\bfinancial advice\b",
    r"\binvestment ranking\b",
    r"\border instruction\b",
    r"\bexecution authorization\b",
    r"\bapproval workflow\b",
    r"\bsecrets?\b",
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
    "paper-only/report-only/read-only",
    "boundary",
    "no-write",
)


def _doc_text() -> str:
    assert DOC_PATH.exists(), f"{DOC_PATH} must exist"
    return DOC_PATH.read_text(encoding="utf-8")


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _readme_allocation_section() -> str:
    readme_text = _readme_text()
    section_marker = "Paper Autonomous Allocation Proposal"
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
            "The proposal authorizes wallet order submission for live trading.",
        )


def test_doc_has_required_sections_in_order() -> None:
    headings = [line for line in _doc_text().splitlines() if line.startswith("#")]
    matched_headings = [heading for heading in headings if heading in REQUIRED_HEADINGS]

    assert matched_headings == list(REQUIRED_HEADINGS)


def test_doc_states_required_scope() -> None:
    normalized = _normalized(_doc_text()).lower()

    for phrase in REQUIRED_PHRASES:
        assert phrase.lower() in normalized


def test_doc_and_readme_section_omit_secret_values() -> None:
    _assert_no_secret_values(_doc_text())
    _assert_no_secret_values(_readme_allocation_section())


def test_doc_and_readme_section_keep_live_auth_order_terms_in_boundary_language() -> None:
    _assert_guarded_terms_are_boundary_language(_doc_text())
    _assert_guarded_terms_are_boundary_language(_readme_allocation_section())


def test_readme_places_allocation_section_after_screening_gate_block() -> None:
    readme_text = _readme_text()
    gate_closing_line = "DSN/table/persist flags and does not write reports."
    producer_marker = "paper-autonomous-screening-decision-support-gate-persist"
    default_command_marker = "paper-autonomous-allocation-proposal --limit 25"
    persist_command_marker = "paper-autonomous-allocation-proposal-persist --limit 25"
    db_history_command_marker = (
        "paper-autonomous-allocation-proposal-db-history --limit 25"
    )
    section_marker = "Paper Autonomous Allocation Proposal"
    next_section_marker = "## Level 1B Node 1 Status"

    assert gate_closing_line in readme_text
    assert producer_marker in readme_text
    assert section_marker in readme_text
    assert default_command_marker in readme_text
    assert persist_command_marker in readme_text
    assert db_history_command_marker in readme_text
    assert next_section_marker in readme_text

    gate_end = readme_text.index(gate_closing_line) + len(gate_closing_line)
    producer_start = readme_text.index(producer_marker, gate_end)
    section_start = readme_text.index(section_marker, producer_start)
    default_command_start = readme_text.index(default_command_marker, section_start)
    persist_command_start = readme_text.index(persist_command_marker, default_command_start)
    db_history_command_start = readme_text.index(
        db_history_command_marker,
        persist_command_start,
    )
    next_section_start = readme_text.index(next_section_marker)

    assert (
        gate_end
        < producer_start
        < section_start
        < default_command_start
        < persist_command_start
        < db_history_command_start
        < next_section_start
    )


def test_readme_links_operator_doc_and_states_cli_contract() -> None:
    section_text = _readme_allocation_section()
    normalized = _normalized(section_text)

    for phrase in REQUIRED_README_PHRASES:
        assert phrase in normalized


def test_doc_describes_separate_persisted_handoff_producer() -> None:
    normalized = _normalized(_doc_text())

    for phrase in (
        "The persisted handoff is a separate sibling producer command",
        "paper-autonomous-allocation-proposal-persist --limit 25",
        "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_ENABLED",
        "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_DSN",
        "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_TABLE",
        "persists only the final proposal report",
        "persisted=True/False",
        "does not write upstream reports",
    ):
        assert phrase in normalized
