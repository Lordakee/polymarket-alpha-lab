from __future__ import annotations

import re
from pathlib import Path

import pytest


DOC_PATH = Path("docs/paper-autonomous-screening-decision-support-gate.md")
README_PATH = Path("README.md")

REQUIRED_HEADINGS = (
    "# Paper Autonomous Screening Decision Support Gate",
    "## Scope",
    "## Source Reports",
    "## Operator Flow",
    "## Gate Status and Next Step",
    "## Transaction and Cost Awareness",
    "## Review Boundaries",
)

REQUIRED_PHRASES = (
    "paper-only/report-only/read-only decision support",
    "Polymarket probability-event screening",
    "already-produced and persisted upstream paper reports",
    "combines upstream paper reports into a gate status and recommended next step",
    "operator review aids, not approvals",
    "not financial advice",
    "not investment ranking",
    "not automatic live investing",
    "not order instruction",
    "not execution authorization",
    "no live trading",
    "no auth",
    "no key handling",
    "no wallet handling",
    "no account handling",
    "no exchange mutation",
    "transaction/cost awareness is upstream evidence",
    "no live fee estimation",
)

REQUIRED_README_PHRASES = (
    "Paper Autonomous Screening Decision Support Gate",
    "docs/paper-autonomous-screening-decision-support-gate.md",
    "paper-autonomous-screening-decision-support-gate --limit 25",
    "paper-autonomous-screening-decision-support-gate-persist --limit 25",
    "persisted final screening gate consumed by the allocation",
    "prints aggregate status plus `persisted=True/False`",
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
    r"\blive fee estimation\b",
    r"\bautomatic live investing\b",
    r"\bauth(?:entication|enticated)?\b",
    r"\bkeys?\b",
    r"\bwallets?\b",
    r"\baccounts?\b",
    r"\borders?\b",
    r"\bsign(?:ing|ed)?\b",
    r"\bsubmit(?:s|ted|ting|mission)?\b",
    r"\bcancel(?:s|led|lation)?\b",
    r"\breplac(?:e|es|ed|ement)\b",
    r"\bexchange mutation\b",
    r"\bfinancial advice\b",
    r"\binvestment ranking\b",
    r"\border instruction\b",
    r"\bexecution authorization\b",
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
    "producer",
    "only",
)


def _doc_text() -> str:
    assert DOC_PATH.exists(), f"{DOC_PATH} must exist"
    return DOC_PATH.read_text(encoding="utf-8")


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


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
            "The gate authorizes wallet order submission for live trading.",
        )


def test_doc_has_required_sections() -> None:
    text = _doc_text()

    for heading in REQUIRED_HEADINGS:
        assert heading in text


def test_doc_states_required_scope() -> None:
    normalized = _normalized(_doc_text()).lower()

    for phrase in REQUIRED_PHRASES:
        assert phrase.lower() in normalized


def test_doc_omits_secret_values() -> None:
    _assert_no_secret_values(_doc_text())


def test_doc_keeps_live_terms_in_exclusions() -> None:
    _assert_guarded_terms_are_boundary_language(_doc_text())


def test_readme_links_operator_doc() -> None:
    readme_text = _readme_text()
    normalized = _normalized(readme_text)

    for phrase in REQUIRED_README_PHRASES:
        assert phrase in normalized


def test_doc_describes_separate_persisted_handoff_producer() -> None:
    normalized = _normalized(_doc_text())

    for phrase in (
        "The persisted handoff to the allocation proposal stage is a separate sibling producer command",
        "paper-autonomous-screening-decision-support-gate-persist --limit 25",
        "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED",
        "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN",
        "POLYMARKET_ALPHA_LAB_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE",
        "persists only that final report",
        "persisted=True/False",
    ):
        assert phrase in normalized
