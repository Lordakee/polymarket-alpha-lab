from __future__ import annotations

import re
from pathlib import Path

import pytest


DOC_PATH = Path("docs/action-gated-queue-decision-support.md")

REQUIRED_HEADINGS = (
    "# Action-Gated Queue Decision Support",
    "## Scope",
    "## Source Data",
    "## Operator Flow",
    "## Review Boundaries",
)

REQUIRED_PHRASES = (
    "Phase 1 paper-only/report-only/readonly decision support",
    "Supabase/Postgres is a read-only source of already-persisted "
    "action-gated queue reports",
    "without secrets/DSNs/env contents",
    "no live trading",
    "no authenticated exchange flow",
    "no wallet/private keys",
    "no account reads",
    "no order construction",
    "no order signing",
    "no order submission",
    "no order cancellation",
    "no order replacement",
    "no exchange mutation",
    "Runtime sink appends action-gated queue reports",
    "read-only psycopg loader loads persisted queue reports",
    "priority reducer ranks whole queue reports",
    "risk summary highlights cap utilization",
    "source queue status",
    "reason codes",
    "CLI prints a redacted decision-support summary",
    "operator review aids, not trade approvals",
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
    r"\bwallets?\b",
    r"\bprivate[- ]keys?\b",
    r"\baccount reads?\b",
    r"\borders?\b",
    r"\bsign(?:ing|ed)?\b",
    r"\bsubmit(?:s|ted|ting|mission)?\b",
    r"\bcancel(?:s|led|lation)?\b",
    r"\breplac(?:e|es|ed|ement)\b",
    r"\bexchange mutation\b",
    r"\bsecrets?\b",
    r"\bdsns?\b",
    r"\benv contents\b",
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
    "paper-only/report-only/readonly",
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
            "Operators can use the wallet to submit orders."
        )


def test_action_gated_queue_decision_support_doc_has_required_sections():
    text = _doc_text()

    for heading in REQUIRED_HEADINGS:
        assert heading in text


def test_action_gated_queue_decision_support_doc_states_required_scope():
    text = _doc_text()
    normalized = _normalized(text)

    for phrase in REQUIRED_PHRASES:
        assert phrase in normalized


def test_action_gated_queue_decision_support_doc_omits_secret_values():
    _assert_no_secret_values(_doc_text())


def test_action_gated_queue_decision_support_doc_keeps_live_terms_in_exclusions():
    _assert_guarded_terms_are_boundary_language(_doc_text())
