from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.team_category_queue_balance_score"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def score_config(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "target_open_per_capacity": d("3.000000"),
        "watch_open_per_capacity": d("4.000000"),
        "block_open_per_capacity": d("6.000000"),
        "urgent_watch_ratio": d("0.250000"),
        "urgent_block_ratio": d("0.500000"),
        "stale_watch_ratio": d("0.200000"),
        "stale_block_ratio": d("0.400000"),
        "average_age_watch_hours": d("48.000000"),
        "average_age_block_hours": d("96.000000"),
        "minimum_pass_score": d("70.000000"),
        "minimum_watch_score": d("35.000000"),
        "balance_weight": d("50.000000"),
        "freshness_weight": d("20.000000"),
        "completion_weight": d("15.000000"),
        "calibration_weight": d("15.000000"),
    }
    values.update(overrides)
    return module.TeamCategoryQueueBalanceScoreConfig(**values)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "team_id": "team-alpha",
        "category_id": "category-politics",
        "open_candidate_count": d("9"),
        "urgent_candidate_count": d("1"),
        "stale_candidate_count": d("1"),
        "average_age_hours": d("18.000000"),
        "recent_completion_count": d("4"),
        "capacity_per_day": d("4.000000"),
        "calibration_score": d("0.900000"),
        "config": score_config(),
        "reason_codes": ("category_queue_observed",),
    }
    values.update(overrides)
    return module.TeamCategoryQueueBalanceScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_team_category_queue_balance_score(
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


def test_balanced_queue_scores_pass() -> None:
    module = api()

    result = score()

    assert result == module.TeamCategoryQueueBalanceScoreResult(
        team_id="team-alpha",
        category_id="category-politics",
        open_candidate_count=d("9"),
        urgent_candidate_count=d("1"),
        stale_candidate_count=d("1"),
        average_age_hours=d("18.000000"),
        recent_completion_count=d("4"),
        capacity_per_day=d("4.000000"),
        calibration_score=d("0.900000"),
        config=score_config(),
        open_per_capacity_ratio=d("2.250000"),
        urgent_candidate_ratio=d("0.111111"),
        stale_candidate_ratio=d("0.111111"),
        completion_capacity_ratio=d("1.000000"),
        balance_component_score=d("100.000000"),
        freshness_component_score=d("72.222200"),
        completion_component_score=d("100.000000"),
        calibration_component_score=d("90.000000"),
        paper_score=d("92.944440"),
        score_status="pass",
        score_decision="continue_research",
        reason_codes=(
            "category_queue_observed",
            "team_category_queue_balance_score",
            "score_pass",
            "capacity_available",
            "freshness_within_watch_threshold",
            "recent_completion_support_present",
            "minimum_pass_score_met",
        ),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert type(result.paper_score) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_overloaded_queue_scores_block() -> None:
    result = score(
        score_input(
            open_candidate_count=d("30"),
            urgent_candidate_count=d("18"),
            stale_candidate_count=d("13"),
            average_age_hours=d("120.000000"),
            recent_completion_count=d("1"),
            capacity_per_day=d("4.000000"),
            calibration_score=d("0.400000"),
        ),
    )

    assert result.open_per_capacity_ratio == d("7.500000")
    assert result.urgent_candidate_ratio == d("0.600000")
    assert result.stale_candidate_ratio == d("0.433333")
    assert result.paper_score == d("9.750000")
    assert result.score_status == "block"
    assert result.score_decision == "pause_candidate_research"
    assert "open_queue_block_threshold_met" in result.reason_codes
    assert "urgent_queue_block_threshold_met" in result.reason_codes
    assert "stale_queue_block_threshold_met" in result.reason_codes
    assert "average_age_block_threshold_met" in result.reason_codes


def test_stale_backlog_scores_watch_without_blocking() -> None:
    result = score(
        score_input(
            open_candidate_count=d("12"),
            urgent_candidate_count=d("2"),
            stale_candidate_count=d("3"),
            average_age_hours=d("60.000000"),
            recent_completion_count=d("2"),
            capacity_per_day=d("4.000000"),
            calibration_score=d("0.750000"),
        ),
    )

    assert result.open_per_capacity_ratio == d("3.000000")
    assert result.stale_candidate_ratio == d("0.250000")
    assert result.paper_score == d("76.250000")
    assert result.score_status == "watch"
    assert result.score_decision == "rebalance_before_more_research"
    assert "stale_queue_watch_threshold_met" in result.reason_codes
    assert "average_age_watch_threshold_met" in result.reason_codes


def test_zero_or_negative_capacity_is_rejected() -> None:
    with pytest.raises(ValueError, match="capacity_per_day must be positive"):
        score_input(capacity_per_day=d("0.000000"))
    with pytest.raises(ValueError, match="capacity_per_day must be positive"):
        score_input(capacity_per_day=d("-1.000000"))


def test_decimal_exact_type_rejection() -> None:
    module = api()

    with pytest.raises(ValueError, match="open_candidate_count must be a Decimal"):
        score_input(open_candidate_count=9)
    with pytest.raises(ValueError, match="capacity_per_day must be a Decimal"):
        score_input(capacity_per_day="4.0")

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="calibration_score must be a Decimal"):
        score_input(calibration_score=DecimalSubclass("0.9"))
    with pytest.raises(ValueError, match="score_input"):
        module.estimate_team_category_queue_balance_score(object())


def test_leak_rejection_blocks_unsafe_public_payload_terms() -> None:
    module = api()
    unsafe_terms = (
        "market",
        "candidate_id",
        "slug",
        "question",
        "url",
        "source_ref",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position_sizing",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_category_queue_balance_score_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_category_queue_balance_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_dataclasses_are_frozen_and_hard_flagged() -> None:
    module = api()
    config = score_config()
    subject = score_input(config=config)
    result = score(subject)

    assert is_dataclass(config)
    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.TeamCategoryQueueBalanceScoreConfig.__dataclass_params__.frozen
    assert module.TeamCategoryQueueBalanceScoreInput.__dataclass_params__.frozen
    assert module.TeamCategoryQueueBalanceScoreResult.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.team_id = "team-beta"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.score_status = "watch"  # type: ignore[misc]

    for instance in (config, subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name in {
                "config",
                "derived_validation_digest",
            }:
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_payload_is_deterministic_and_rejects_digest_tampering() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload == module.team_category_queue_balance_score_payload(result)
    assert payload["team_id"] == "team-alpha"
    assert payload["category_id"] == "category-politics"
    assert payload["open_candidate_count"] == "9"
    assert payload["paper_score"] == "92.944440"
    assert payload["config"]["target_open_per_capacity"] == "3.000000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    rebuilt = module.TeamCategoryQueueBalanceScoreResult(**public_field_values(result))
    assert rebuilt == result

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_category_queue_balance_score_payload(result)


def test_report_consistency_and_public_status_vocabulary() -> None:
    module = api()
    result = score()

    assert module.SCORE_STATUSES == ("pass", "watch", "block")
    assert result.score_status in module.SCORE_STATUSES
    assert result.score_status not in {"ready", "blocked", "matched", "supported"}

    with pytest.raises(ValueError, match="score_status"):
        module.TeamCategoryQueueBalanceScoreResult(
            **{
                **public_field_values(result),
                "score_status": "ready",
            },
        )
    with pytest.raises(ValueError, match="paper_score"):
        module.TeamCategoryQueueBalanceScoreResult(
            **{
                **public_field_values(result),
                "paper_score": d("1.000000"),
            },
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.TeamCategoryQueueBalanceScoreResult(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/team_category_queue_balance_score.py",
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
        "buy",
        "sell",
        "trade",
        "recommendation",
        "position-sizing",
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
        "TeamCategoryQueueBalanceScoreConfig",
        "TeamCategoryQueueBalanceScoreInput",
        "TeamCategoryQueueBalanceScoreResult",
        "estimate_team_category_queue_balance_score",
        "team_category_queue_balance_score_payload",
        "reject_team_category_queue_balance_score_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "team_category_queue_balance_score" not in getattr(root, "__all__", ())
