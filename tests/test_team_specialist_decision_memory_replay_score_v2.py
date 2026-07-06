from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.team_specialist_decision_memory_replay_score_v2"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "specialist_id": "specialist-memory-replay-v2",
        "memory_id": "decision-memory-replay-v2",
        "decision_memory_count": d("8"),
        "replayed_decision_count": d("6"),
        "matching_replay_count": d("4"),
        "stale_replay_count": d("2"),
        "recent_learning_count": d("3"),
        "minimum_actionable_score": d("100.000000"),
        "reason_codes": ("decision_memory_present",),
    }
    values.update(overrides)
    return module.TeamSpecialistDecisionMemoryReplayScoreV2Input(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_team_specialist_decision_memory_replay_score_v2(
        score_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_decision_memory_replay_score_applies_penalties_and_boosts() -> None:
    module = api()

    result = score()

    assert result == module.TeamSpecialistDecisionMemoryReplayScoreV2Result(
        specialist_id="specialist-memory-replay-v2",
        memory_id="decision-memory-replay-v2",
        decision_memory_count=d("8"),
        replayed_decision_count=d("6"),
        matching_replay_count=d("4"),
        stale_replay_count=d("2"),
        recent_learning_count=d("3"),
        replay_coverage_ratio=d("0.750000"),
        replay_match_ratio=d("0.666667"),
        stale_replay_ratio=d("0.333333"),
        recent_learning_ratio=d("0.375000"),
        raw_memory_replay_score_bps=d("141.666700"),
        stale_replay_penalty_bps=d("33.333300"),
        recent_learning_boost_bps=d("18.750000"),
        paper_score_bps=d("127.083400"),
        minimum_actionable_score=d("100.000000"),
        score_status="candidate",
        score_decision="paper_candidate",
        reason_codes=(
            "decision_memory_present",
            "team_specialist_decision_memory_replay_score_v2",
            "score_candidate",
            "replay_coverage_present",
            "stale_replay_penalty_applied",
            "recent_learning_boost_applied",
            "minimum_actionable_score_met",
        ),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert type(result.paper_score_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_stale_replay_penalties_can_move_score_to_watch() -> None:
    fresh = score(score_input(stale_replay_count=d("0"), recent_learning_count=d("0")))
    stale = score(score_input(stale_replay_count=d("6"), recent_learning_count=d("0")))

    assert fresh.stale_replay_penalty_bps == d("0.000000")
    assert fresh.paper_score_bps == d("141.666700")
    assert fresh.score_status == "candidate"
    assert stale.stale_replay_penalty_bps == d("100.000000")
    assert stale.paper_score_bps == d("41.666700")
    assert stale.score_status == "watch"
    assert stale.score_decision == "manual_review"
    assert "stale_replay_penalty_applied" in stale.reason_codes
    assert "score_positive_below_minimum" in stale.reason_codes


def test_recent_learning_boosts_raise_replay_score() -> None:
    without_learning = score(score_input(recent_learning_count=d("0")))
    with_learning = score(score_input(recent_learning_count=d("8")))

    assert without_learning.recent_learning_boost_bps == d("0.000000")
    assert with_learning.recent_learning_ratio == d("1.000000")
    assert with_learning.recent_learning_boost_bps == d("50.000000")
    assert with_learning.paper_score_bps == without_learning.paper_score_bps + d(
        "50.000000",
    )
    assert "recent_learning_boost_applied" in with_learning.reason_codes


def test_payload_serializes_decimals_as_strings_and_revalidates_digest() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.team_specialist_decision_memory_replay_score_v2_payload(
        result,
    )
    assert payload["decision_memory_count"] == "8"
    assert payload["paper_score_bps"] == "127.083400"
    assert payload["stale_replay_ratio"] == "0.333333"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_decision_memory_replay_score_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.TeamSpecialistDecisionMemoryReplayScoreV2Input.__dataclass_params__.frozen
    assert module.TeamSpecialistDecisionMemoryReplayScoreV2Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.memory_id = "other-memory"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.score_status = "watch"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="decision_memory_count must be a Decimal"):
        score_input(decision_memory_count=8)
    with pytest.raises(ValueError, match="memory_id must be a canonical"):
        score_input(memory_id=" decision-memory-replay-v2")
    with pytest.raises(ValueError, match="matching_replay_count must not exceed"):
        score_input(matching_replay_count=d("7"))
    with pytest.raises(ValueError, match="recent_learning_count must not exceed"):
        score_input(recent_learning_count=d("9"))
    with pytest.raises(ValueError, match="minimum_actionable_score must be nonnegative"):
        score_input(minimum_actionable_score=d("-1.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["decision_memory_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.TeamSpecialistDecisionMemoryReplayScoreV2Result(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_and_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.TeamSpecialistDecisionMemoryReplayScoreV2Result(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_specialist_decision_memory_replay_score_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_specialist_decision_memory_replay_score_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/team_specialist_decision_memory_replay_score_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "SCORE_STATUSES",
        "SCORE_DECISIONS",
        "TeamSpecialistDecisionMemoryReplayScoreV2Input",
        "TeamSpecialistDecisionMemoryReplayScoreV2Result",
        "estimate_team_specialist_decision_memory_replay_score_v2",
        "team_specialist_decision_memory_replay_score_v2_payload",
        "reject_team_specialist_decision_memory_replay_score_v2_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "team_specialist_decision_memory_replay_score_v2" not in getattr(
        root,
        "__all__",
        (),
    )
