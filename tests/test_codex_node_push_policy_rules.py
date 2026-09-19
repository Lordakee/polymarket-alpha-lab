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
    assert "claude-opus-5" in normalized
    assert "thinking level `max`" in normalized
    assert "if local claude code is unavailable" in normalized
    assert "treat the review gate as blocked" in normalized
    assert "no fallback reviewer" in normalized
    # Research-client choices in the current owner override are not reviewers.
    # Preserve the historical review restriction below Scope, not a word ban
    # on unrelated, explicitly authorized client-selection instructions.
    legacy_policy = normalized.split("## scope", 1)[1].split(
        "## omo / sisyphus session workflow", 1
    )[0]
    assert "opencode" not in legacy_policy
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


def test_claude_review_monitoring_has_no_fixed_timeout_or_live_interruption():
    instructions, normalized = _agents_instructions()

    assert "must not be wrapped in a fixed elapsed-time timeout" in normalized
    assert "inspectable session" in normalized
    assert "check them about every 30 seconds" in normalized
    assert "process/session liveness" in normalized
    assert "when available, stream growth or event count" in normalized
    assert "stderr or terminal events, cpu, and network activity" in normalized
    assert (
        "elapsed time alone or a quiet interval is not evidence of a stall"
        in normalized
    )
    assert "do not interrupt, terminate, restart, duplicate, or replace it" in normalized
    assert "do not route around" in normalized
    assert "keep waiting and monitoring" in normalized
    assert "act only on an explicit result or error" in normalized
    assert "confirmed process/session exit" in normalized
    assert "concrete auth/permission/provider failure" in normalized
    assert "proven stall" in normalized
    assert "newer user instruction" in normalized


def test_agent_coordination_defaults_capture_parallel_cap_and_conflict_rule():
    instructions, normalized = _agents_instructions()

    assert "agent coordination defaults" in instructions
    assert "project sets no fixed subagent concurrency count" in normalized
    assert "discover usable capacity dynamically" in normalized
    assert "nested subagent depth remains capped at **3**" in normalized
    assert "independent, non-conflicting work" in normalized
    assert "write-scope overlap" in normalized
    assert "avoid assigning multiple subagents to edit the same files" in normalized
    assert "split ownership by non-overlapping files or modules" in normalized


def test_research_client_choices_are_separate_from_review_policy():
    instructions, normalized = _agents_instructions()
    owner = normalized.split("## current owner instruction: complete github-first handoffs", 1)[0]
    for client in ("codex", "claude code", "opencode", "grok cli", "zcode cli"):
        assert client in owner
    assert "self-review" in owner
    review = instructions.split("## review / audit defaults", 1)[1].split("\n## ", 1)[0]
    assert "opencode" not in review
    assert "unless the user explicitly changes this rule again" in review
