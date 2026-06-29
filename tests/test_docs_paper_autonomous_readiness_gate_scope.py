from __future__ import annotations

import re
from pathlib import Path


DOC_PATH = Path("docs/paper-autonomous-readiness-gate.md")
README_PATH = Path("README.md")

REQUIRED_HEADINGS = (
    "# Paper Autonomous Readiness Gate",
    "## Scope",
    "## Source Reports",
    "## Readiness Status",
    "## Review Boundaries",
)

REQUIRED_PHRASES = (
    "Phase 1 paper-only/report-only/read-only pure reducer",
    "already-built typed reports",
    "screening decision-support gate DB-history health",
    "strategy-cycle report history gate",
    "optional fourth source",
    "strategy_cycle_report_history_gate",
    "allocation proposal DB-history health trend gate",
    "investment-ledger DB-history health trend gate",
    "three-source legacy reports remain valid",
    "does not query or load DB history",
    "no CLI",
    "no runner",
    "no sink",
    "no loader",
    "no persistence path",
    "no env read",
    "no DSN/table flags",
    "no live trading",
    "no auth",
    "no private keys",
    "no wallet handling",
    "no account reads",
    "no order construction",
    "no order signing",
    "no order submission",
    "no order cancellation",
    "no order replacement",
    "pass status is not permission to trade",
    "not financial advice",
    "not investment ranking",
    "not order instruction",
    "not execution authorization",
    "not an approval workflow",
    "operator-facing paper review",
    "does not alter strategy behavior",
    "does not trigger allocation",
    "does not stop execution paths",
)

README_PHRASES = (
    "Paper Autonomous Readiness Gate",
    "paper-only/report-only/readonly readiness report",
    "operator-facing paper review",
    "does not alter strategy behavior",
    "does not trigger allocation",
    "does not stop execution paths",
    "not order instruction",
    "not execution authorization",
)

SECRET_VALUE_PATTERNS = (
    r"postgres(?:ql)?://",
    r"\b(?:database_url|dsn|supabase_[a-z_]*key|pgpassword)\s*=",
    r"\bservice_role\b",
    r"\beyj[a-z0-9_-]{20,}",
    r"\bsk-[a-z0-9_-]{20,}",
    r"-----begin [a-z ]*private key-----",
)


def test_readiness_gate_doc_exists_and_has_required_boundary_language() -> None:
    doc = DOC_PATH.read_text(encoding="utf-8")
    lower_doc = doc.lower()

    previous_index = -1
    for heading in REQUIRED_HEADINGS:
        index = doc.find(heading)
        assert index > previous_index, heading
        previous_index = index
    for phrase in REQUIRED_PHRASES:
        assert phrase in doc
    for pattern in SECRET_VALUE_PATTERNS:
        assert re.search(pattern, lower_doc) is None


def test_readiness_gate_readme_links_operator_doc_and_boundary() -> None:
    readme = README_PATH.read_text(encoding="utf-8")

    assert "docs/paper-autonomous-readiness-gate.md" in readme
    for phrase in README_PHRASES:
        assert phrase in readme
