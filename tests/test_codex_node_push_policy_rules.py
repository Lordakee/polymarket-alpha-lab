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
    assert "post-node external review gate passes through claude code" in normalized
    assert "claude-opus-4-8" in normalized
    assert "thinking level `max`" in normalized
    assert "opencode" not in normalized.split("## omo / sisyphus session workflow", 1)[0]
    _assert_phrases_appear_in_order(
        normalized,
        (
            "the configured post-node external review gate passes through claude code",
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
    ) < normalized.index("## omo / sisyphus session workflow (historical)")


def test_agent_coordination_defaults_capture_parallel_cap_and_conflict_rule():
    instructions, normalized = _agents_instructions()

    assert "agent coordination defaults" in instructions
    assert "20 active subagent threads" in normalized
    assert "nested subagent depth cap of **3**" in normalized
    assert "independent, non-conflicting work" in normalized
    assert "write-scope overlap" in normalized
    assert "avoid assigning multiple subagents to edit the same files" in normalized
    assert "split ownership by non-overlapping files or modules" in normalized
