from __future__ import annotations

import re
from pathlib import Path

import pytest


DOC_PATH = Path("docs/strategy-first-roadmap.md")

REQUIRED_HEADINGS = (
    "# Strategy-First Roadmap",
    "## Current Phase Priority",
    "## Decision Inputs",
    "## Durable Data Boundary",
    "## Operating Model Connection",
    "## Execution Boundary",
)

REQUIRED_PHRASES = (
    "selecting and analyzing Polymarket probability-event markets",
    "not ordinary asset-price investing",
    "event probability",
    "outcome criteria",
    "resolution risk",
    "market microstructure",
    "spread/liquidity",
    "fees/cost drag",
    "cash lockup",
    "finalization/settlement timing",
    "team memory",
    "All durable data is local Supabase/Postgres only",
    "live trading/order placement is out of scope for the current phase",
    "operator/manual execution can be used after report review",
    "medium-scale team model",
    "candidate decision score engine",
)

FORBIDDEN_DURABLE_BACKENDS = (
    "sqlite",
    "duckdb",
    "redis",
    "mongodb",
    "hosted postgres",
    "jsonl durable",
    "file-backed durable",
)

GUARDED_TERM_PATTERNS = (
    r"\blive trading\b",
    r"\border placement\b",
    r"\border submission\b",
    r"\border signing\b",
    r"\bwallet\b",
    r"\bauth\b",
    r"\bexchange mutation\b",
)

ALLOWED_BOUNDARY_MARKERS = (
    "out of scope",
    "no ",
    "not ",
    "must not",
    "does not",
    "manual",
    "operator",
    "boundary",
    "after report review",
)


def _doc_text() -> str:
    assert DOC_PATH.exists(), f"{DOC_PATH} must exist"
    return DOC_PATH.read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _assert_guarded_terms_are_boundary_language(text: str) -> None:
    for line in text.lower().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(re.search(pattern, stripped) for pattern in GUARDED_TERM_PATTERNS):
            assert any(marker in stripped for marker in ALLOWED_BOUNDARY_MARKERS), line


def test_boundary_guard_rejects_positive_live_automation_language() -> None:
    with pytest.raises(AssertionError):
        _assert_guarded_terms_are_boundary_language(
            "The roadmap enables live trading order placement through wallet auth.",
        )


def test_strategy_first_roadmap_has_required_sections() -> None:
    text = _doc_text()

    for heading in REQUIRED_HEADINGS:
        assert heading in text


def test_strategy_first_roadmap_states_required_scope_and_decision_factors() -> None:
    normalized = _normalized(_doc_text())

    for phrase in REQUIRED_PHRASES:
        assert phrase in normalized


def test_strategy_first_roadmap_keeps_durable_data_local_only() -> None:
    lower_text = _normalized(_doc_text()).lower()

    for backend in FORBIDDEN_DURABLE_BACKENDS:
        assert backend not in lower_text


def test_strategy_first_roadmap_keeps_live_automation_terms_in_boundaries() -> None:
    _assert_guarded_terms_are_boundary_language(_doc_text())
