from __future__ import annotations

from pathlib import Path


DOC_PATH = Path("docs/paper-autonomous-allocation-proposal.md")


def test_allocation_proposal_docs_do_not_claim_unimplemented_shadow_nav() -> None:
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    assert "shadow nav" not in text
