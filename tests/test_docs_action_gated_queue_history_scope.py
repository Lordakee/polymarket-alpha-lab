from __future__ import annotations

import re
from pathlib import Path

import pytest


DOC_PATH = Path("docs/action-gated-queue-history.md")

REQUIRED_HEADINGS = (
    "# Action-Gated Queue History",
    "## Scope",
    "## Source Data",
    "## Operator Flow",
    "## CLI Output Safety",
    "## Review Boundaries",
)

REQUIRED_PHRASES = (
    "action-gated-queue-history",
    "action-gated-queue-history-db-history",
    "Phase 1 paper-only/report-only/read-only queue history",
    "runtime sink appends paper queue reports",
    "read-only DB loader reads already-persisted reports",
    "persisted history DB history command reads already-persisted history reports only",
    "uses only the action-gated queue history DB environment boundary",
    "supports only --limit and --latest-action-status research_ready|watch|blocked",
    "never persists rows",
    "pure history reducer summarizes trend/history metrics",
    "CLI prints an aggregate-only summary",
    "no live trading",
    "no auth",
    "no wallet/private keys",
    "no account reads",
    "no order construction",
    "no order signing",
    "no order submission",
    "no order cancellation",
    "no order replacement",
    "no exchange mutation",
    "does not approve trades",
    "does not automate investment",
    "supports human/operator research review",
    "CLI output must not include DSNs, table names, payload JSON, "
    "raw DB records, secrets, or env contents",
)

SECRET_VALUE_PATTERNS = (
    r"postgres(?:ql)?://",
    r"\b(?:database_url|dsn|supabase_[a-z_]*key|pgpassword)\s*=",
    r"\bservice_role\b",
    r"\beyj[a-z0-9_-]{20,}",
    r"\bsk-[a-z0-9_-]{20,}",
    r"-----begin [a-z ]*private key-----",
    r"\bpaper_action_gated_strategy_recommendation_queue_reports\b",
)

GUARDED_TERM_PATTERNS = (
    r"\blive trading\b",
    r"\bauth(?:entication|enticated)?\b",
    r"\bwallets?\b",
    r"\bprivate[- ]keys?\b",
    r"\baccount reads?\b",
    r"\borders?\b",
    r"\bsign(?:ing|ed)?\b",
    r"\bsubmit(?:s|ted|ting|mission)?\b",
    r"\bcancel(?:s|led|lation)?\b",
    r"\breplac(?:e|es|ed|ement)\b",
    r"\bexchange mutation\b",
    r"\bapprove(?:s|d|al)?\b",
    r"\bautomate(?:s|d|ion)?\b",
    r"\binvestment\b",
    r"\btrades?\b",
    r"\bsecrets?\b",
    r"\bdsns?\b",
    r"\benv contents\b",
    r"\btable names?\b",
    r"\bpayload\b",
    r"\braw db records?\b",
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
    "redact",
    "redacted",
    "read-only",
    "paper-only/report-only/read-only",
    "aggregate-only",
)


def _doc_text() -> str:
    assert DOC_PATH.exists(), f"{DOC_PATH} must exist"
    return DOC_PATH.read_text(encoding="utf-8")


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


def test_scope_guard_rejects_secret_values_and_positive_live_language():
    with pytest.raises(AssertionError):
        _assert_no_secret_values(
            "Set DATABASE_URL=postgresql://user:pass@example.invalid/db"
        )

    with pytest.raises(AssertionError):
        _assert_guarded_terms_are_boundary_language(
            "Operators can use auth and wallet keys to submit orders."
        )

    with pytest.raises(AssertionError):
        _assert_guarded_terms_are_boundary_language(
            "The CLI can print payload JSON and raw DB records."
        )


def test_action_gated_queue_history_doc_has_required_sections():
    text = _doc_text()

    for heading in REQUIRED_HEADINGS:
        assert heading in text


def test_action_gated_queue_history_doc_states_required_scope():
    text = _doc_text()
    normalized = _normalized(text)

    for phrase in REQUIRED_PHRASES:
        assert phrase in normalized


def test_action_gated_queue_history_doc_omits_secret_values():
    _assert_no_secret_values(_doc_text())


def test_action_gated_queue_history_doc_keeps_live_terms_in_exclusions():
    _assert_guarded_terms_are_boundary_language(_doc_text())
