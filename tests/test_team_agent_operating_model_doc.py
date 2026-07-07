from __future__ import annotations

from pathlib import Path


DOC_PATH = Path("docs/team-agent-operating-model.md")


def _doc_text() -> str:
    assert DOC_PATH.exists(), f"{DOC_PATH} must exist"
    return DOC_PATH.read_text(encoding="utf-8")


def test_team_agent_operating_model_doc_exists_and_states_phase_1_boundary() -> None:
    text = _doc_text()

    required_fragments = (
        "local Supabase/Postgres",
        "paper-only/report-only/readonly",
        "no live order placement",
        "long-term memory",
    )
    for fragment in required_fragments:
        assert fragment in text


def test_team_agent_operating_model_doc_makes_medium_scale_team_memory_concrete() -> None:
    lower_text = _doc_text().lower()

    required_fragments = (
        "medium-scale team design",
        "3-5 roles/agents",
        "source scout",
        "evidence analyst",
        "probability forecaster",
        "market microstructure/cost analyst",
        "memory steward/reviewer",
        "candidate decision scores",
        "politics",
        "crypto/btc",
        "equities/indexes",
        "gold/rates",
        "football",
        "basketball",
    )
    for fragment in required_fragments:
        assert fragment in lower_text
