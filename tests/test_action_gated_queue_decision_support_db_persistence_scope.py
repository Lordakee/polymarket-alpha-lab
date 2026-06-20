from __future__ import annotations

import re
from pathlib import Path

import pytest


DOC_PATH = Path("docs/action-gated-queue-decision-support-db-persistence.md")
CONFIG_PATH = Path(
    "src/polymarket_alpha_lab/"
    "supabase_action_gated_strategy_recommendation_queue_decision_support_config.py",
)
MIGRATION_PATH = Path(
    "supabase/migrations/"
    "20260620000002_action_gated_strategy_recommendation_queue_decision_support_reports.sql",
)

REQUIRED_HEADINGS = (
    "# Action-Gated Queue Decision-Support DB Persistence",
    "## Environment",
    "## Migration",
    "## Scope Boundary",
)

REQUIRED_SCOPE_PHRASES = (
    "persistence-only",
    "paper-only, report-only, and readonly",
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

REQUIRED_SAME_SOURCE_DOC_PHRASES = (
    "priority and risk payloads must be generated from the same source queue set",
    "shared scalar source counts are enforced",
    "detailed risk summary fields remain hydrated from json payloads",
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

FORBIDDEN_LIVE_SURFACE_FRAGMENTS = (
    "account",
    "auth",
    "cancel",
    "client",
    "exchange",
    "live",
    "order",
    "private_key",
    "sign",
    "submit",
    "wallet",
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


def _normalized_identifier_text(text: str) -> str:
    return "".join(character for character in text.lower() if character.isalnum())


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


def test_doc_states_same_source_composite_snapshot_invariant() -> None:
    normalized = _normalized(_doc_text()).lower()

    for phrase in REQUIRED_SAME_SOURCE_DOC_PHRASES:
        assert phrase in normalized


def test_doc_omits_secret_values() -> None:
    _assert_no_secret_values(_doc_text())


def test_doc_keeps_live_terms_in_exclusions() -> None:
    _assert_guarded_terms_are_boundary_language(_doc_text())


def test_persistence_files_do_not_reference_live_trading_surfaces() -> None:
    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    migration_text = _migration_text()
    normalized_text = _normalized_identifier_text(config_text + migration_text)

    for fragment in FORBIDDEN_LIVE_SURFACE_FRAGMENTS:
        assert fragment not in normalized_text


def test_migration_enforces_same_source_scalar_counts() -> None:
    normalized = _normalized(_migration_text()).lower()

    assert "check (priority_source_report_count = risk_source_queue_count)" in normalized
    assert (
        "check (priority_total_ready_notional = risk_total_ready_notional)"
        in normalized
    )
