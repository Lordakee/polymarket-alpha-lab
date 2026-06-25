from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _agents_instructions() -> tuple[str, str]:
    instructions = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
    normalized = " ".join(instructions.split())
    return instructions, normalized


def _assert_phrases_appear_in_order(text: str, phrases: tuple[str, ...]) -> None:
    position = -1
    for phrase in phrases:
        next_position = text.index(phrase)
        assert next_position > position
        position = next_position


def test_codex_node_push_policy_preserves_verified_push_gate():
    instructions, normalized = _agents_instructions()

    assert "codex node push policy" in instructions
    assert "focused local commit with a clean worktree" in normalized
    assert "focused tests for the changed surface pass" in normalized
    assert "the full test suite passes" in normalized
    assert "git diff --check" in normalized
    assert "python compile verification passes" in normalized
    assert "codegraph is synced" in normalized
    assert "secret scan finds no leaked credentials or tokens" in normalized
    assert "post-node external review gate passes through local opencode" in normalized
    _assert_phrases_appear_in_order(
        normalized,
        (
            "the configured post-node external review gate passes through local opencode",
            "do not push half-finished work",
        ),
    )


def test_codex_node_push_policy_continues_after_verified_push_by_default():
    instructions, normalized = _agents_instructions()

    assert "codex node push policy" in instructions
    assert "verified, committed, reviewed, and pushed to github" in normalized
    assert "continue to the next suitable task by default" in normalized
    assert "do not pause solely because a github push completed" in normalized
    assert "user confirmation is needed" in normalized
    assert "blocker prevents meaningful progress" in normalized
    assert "phase or risk boundary would change" in normalized
    assert "user explicitly asks to stop or pause" in normalized
    assert normalized.index(
        "after a completed codex node is verified, committed, reviewed, and pushed to github",
    ) < instructions.index("## omo / sisyphus session workflow (opencode only — codex ignores this section)")
