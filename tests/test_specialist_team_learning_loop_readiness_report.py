from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "specialist_team_learning_loop_readiness_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.specialist_team_learning_loop_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def team_input(
    *,
    team_label: str = "politics",
    resolved_market_count: str = "12",
    pending_market_count: str = "3",
    calibration_error_count: str = "1",
    memory_event_count: str = "16",
    last_review_age_seconds: str = "3600",
    supabase_persistence_ready: bool = True,
) -> Any:
    module = api()
    return module.SpecialistTeamLearningLoopReadinessInput(
        team_label=team_label,
        resolved_market_count=d(resolved_market_count),
        pending_market_count=d(pending_market_count),
        calibration_error_count=d(calibration_error_count),
        memory_event_count=d(memory_event_count),
        last_review_age_seconds=d(last_review_age_seconds),
        supabase_persistence_ready=supabase_persistence_ready,
    )


def build_report(*rows: Any) -> Any:
    module = api()
    return module.build_specialist_team_learning_loop_readiness_report(
        rows,
        config=module.SpecialistTeamLearningLoopReadinessConfig(),
    )


def test_exports_config_bands_and_hard_report_only_flags() -> None:
    module = api()
    config = module.SpecialistTeamLearningLoopReadinessConfig()

    assert module.__all__ == (
        "DEFAULT_SPECIALIST_TEAM_LEARNING_LOOP_READINESS_CONFIG_VERSION",
        "SPECIALIST_TEAM_LEARNING_LOOP_PRIORITY_BANDS",
        "SpecialistTeamLearningLoopReadinessConfig",
        "SpecialistTeamLearningLoopReadinessInput",
        "SpecialistTeamLearningLoopReadinessRow",
        "SpecialistTeamLearningLoopReadinessReport",
        "build_specialist_team_learning_loop_readiness_report",
        "specialist_team_learning_loop_readiness_report_payload",
    )
    assert module.SPECIALIST_TEAM_LEARNING_LOOP_PRIORITY_BANDS == (
        "ready",
        "attention",
        "blocked",
    )
    assert config.config_version == "specialist-team-learning-loop-readiness-v0"
    assert config.min_resolved_market_count == d("10")
    assert config.max_pending_market_count == d("5")
    assert config.max_calibration_error_count == d("2")
    assert config.min_memory_event_count == d("12")
    assert config.max_last_review_age_seconds == d("604800")
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.SpecialistTeamLearningLoopReadinessConfig(paper_only=False)

    with pytest.raises(ValueError, match="min_resolved_market_count must be a Decimal"):
        module.SpecialistTeamLearningLoopReadinessConfig(
            min_resolved_market_count=10,  # type: ignore[arg-type]
        )


def test_report_scores_specialist_team_learning_loop_readiness() -> None:
    report = build_report(
        team_input(team_label="politics"),
        team_input(
            team_label="finance",
            resolved_market_count="8",
            pending_market_count="6",
            calibration_error_count="2",
            memory_event_count="9",
            last_review_age_seconds="700000",
        ),
        team_input(
            team_label="sports",
            resolved_market_count="15",
            pending_market_count="1",
            calibration_error_count="0",
            memory_event_count="21",
            last_review_age_seconds="7200",
            supabase_persistence_ready=False,
        ),
    )

    assert is_dataclass(report)
    assert report.config_version == "specialist-team-learning-loop-readiness-v0"
    assert report.team_count == d("3")
    assert report.ready_team_count == d("1")
    assert report.attention_team_count == d("1")
    assert report.blocked_team_count == d("1")
    assert report.aggregate_ready_ratio == d("0.333333")
    assert report.learning_loop_ready is False
    assert report.priority_band == "blocked"
    assert report.blocker_reasons == ("supabase_persistence_not_ready",)
    assert report.attention_reasons == (
        "resolved_market_sample_gap",
        "pending_market_backlog",
        "memory_event_gap",
        "stale_learning_review",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.team_label for row in report.readiness_rows) == (
        "sports",
        "finance",
        "politics",
    )
    sports, finance, politics = report.readiness_rows
    assert sports.priority_band == "blocked"
    assert sports.learning_loop_ready is False
    assert sports.ready_ratio == d("0.800000")
    assert sports.blocker_reasons == ("supabase_persistence_not_ready",)
    assert sports.attention_reasons == ()
    assert finance.priority_band == "attention"
    assert finance.learning_loop_ready is False
    assert finance.ready_ratio == d("0.500000")
    assert finance.blocker_reasons == ()
    assert finance.attention_reasons == (
        "resolved_market_sample_gap",
        "pending_market_backlog",
        "memory_event_gap",
        "stale_learning_review",
    )
    assert politics.priority_band == "ready"
    assert politics.learning_loop_ready is True
    assert politics.ready_ratio == d("1.000000")
    assert politics.blocker_reasons == ()
    assert politics.attention_reasons == ()

    payload = api().specialist_team_learning_loop_readiness_report_payload(report)
    assert payload["aggregate_ready_ratio"] == "0.333333"
    assert payload["readiness_rows"][0]["ready_ratio"] == "0.800000"
    assert payload["readiness_rows"][0]["priority_band"] == "blocked"
    assert "Decimal" not in repr(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_report_is_ready_with_zero_denominator_ratio() -> None:
    report = build_report()

    assert report.team_count == d("0")
    assert report.ready_team_count == d("0")
    assert report.attention_team_count == d("0")
    assert report.blocked_team_count == d("0")
    assert report.aggregate_ready_ratio == d("0.000000")
    assert report.learning_loop_ready is True
    assert report.priority_band == "ready"
    assert report.blocker_reasons == ()
    assert report.attention_reasons == ()
    assert report.readiness_rows == ()


def test_validation_frozen_decimal_only_and_public_safe_boundaries() -> None:
    module = api()

    with pytest.raises(ValueError, match="resolved_market_count must be a Decimal"):
        module.SpecialistTeamLearningLoopReadinessInput(
            team_label="politics",
            resolved_market_count=12,  # type: ignore[arg-type]
            pending_market_count=d("3"),
            calibration_error_count=d("1"),
            memory_event_count=d("16"),
            last_review_age_seconds=d("3600"),
            supabase_persistence_ready=True,
        )

    with pytest.raises(ValueError, match="resolved_market_count must be a whole Decimal"):
        team_input(resolved_market_count="1.500000")

    with pytest.raises(ValueError, match="team_label must be one of"):
        team_input(team_label="crypto")

    with pytest.raises(ValueError, match="duplicate specialist team"):
        build_report(team_input(team_label="politics"), team_input(team_label="politics"))

    with pytest.raises(ValueError, match="supabase_persistence_ready must be a bool"):
        team_input(supabase_persistence_ready=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(team_input(), paper_only=False)

    row = build_report(team_input()).readiness_rows[0]
    with pytest.raises(FrozenInstanceError):
        row.ready_ratio = d("0.1")  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        build_report(team_input()).priority_band = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="ready_ratio must match readiness components"):
        replace(row, ready_ratio=d("0.123456"))


def test_module_source_is_read_only_paper_only_and_side_effect_free() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "subprocess",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "insert",
        "update ",
        "delete(",
        "post(",
        "put(",
    ):
        assert forbidden not in lowered
    for forbidden in (
        "wallet",
        "order",
        "trade",
        "sizing",
        "auth",
        "token",
        "dsn",
    ):
        assert forbidden not in lowered
