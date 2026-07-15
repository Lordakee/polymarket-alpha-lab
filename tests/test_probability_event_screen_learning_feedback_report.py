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
    / "probability_event_screen_learning_feedback_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.probability_event_screen_learning_feedback_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: Any) -> Any:
    module = api()
    defaults = dict(
        postmortem_ready=True,
        team_memory_update_queue_ready=True,
        threshold_backtest_ready=True,
        team_scorecard_ready=True,
        source_family_feedback_ready=True,
        calibration_sample_ready=True,
        supabase_persistence_ready=True,
    )
    defaults.update(overrides)
    return module.build_probability_event_screen_learning_feedback_report(**defaults)


def test_exports_configured_read_only_report_api() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_PROBABILITY_EVENT_SCREEN_LEARNING_FEEDBACK_CONFIG_VERSION",
        "PROBABILITY_EVENT_SCREEN_LEARNING_BANDS",
        "ProbabilityEventScreenLearningFeedbackReport",
        "build_probability_event_screen_learning_feedback_report",
    )
    assert module.DEFAULT_PROBABILITY_EVENT_SCREEN_LEARNING_FEEDBACK_CONFIG_VERSION == (
        "probability-event-screen-learning-feedback-v0"
    )
    assert module.PROBABILITY_EVENT_SCREEN_LEARNING_BANDS == (
        "ready",
        "attention",
        "blocked",
    )

    report = build_report()
    assert is_dataclass(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.learning_band = "blocked"  # type: ignore[misc]


def test_ready_report_has_decimal_ratio_digest_and_json_safe_payload() -> None:
    report = build_report()

    assert report.config_version == "probability-event-screen-learning-feedback-v0"
    assert report.learning_feedback_ready is True
    assert report.learning_band == "ready"
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.ready_ratio == d("1.000000")
    assert type(report.ready_ratio) is Decimal
    assert len(report.digest) == 64
    assert report.digest == api().probability_event_screen_learning_feedback_report_digest(report)

    payload = report.public_payload
    assert payload == api().probability_event_screen_learning_feedback_report_payload(report)
    assert payload["learning_feedback_ready"] is True
    assert payload["learning_band"] == "ready"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["digest"] == report.digest
    assert "Decimal" not in repr(payload)
    json.dumps(payload, sort_keys=True)


def test_report_blocks_on_required_learning_feedback_dependencies() -> None:
    report = build_report(
        postmortem_ready=False,
        team_memory_update_queue_ready=False,
        threshold_backtest_ready=False,
        supabase_persistence_ready=False,
    )

    assert report.learning_feedback_ready is False
    assert report.learning_band == "blocked"
    assert report.ready_ratio == d("0.428571")
    assert report.blocked_reason_codes == (
        "postmortem_not_ready",
        "team_memory_update_queue_not_ready",
        "threshold_backtest_not_ready",
        "supabase_persistence_not_ready",
    )
    assert report.attention_reason_codes == ()
    assert report.public_payload["blocked_reason_codes"] == [
        "postmortem_not_ready",
        "team_memory_update_queue_not_ready",
        "threshold_backtest_not_ready",
        "supabase_persistence_not_ready",
    ]


def test_report_uses_attention_band_for_non_blocking_learning_inputs() -> None:
    report = build_report(
        team_scorecard_ready=False,
        source_family_feedback_ready=False,
        calibration_sample_ready=False,
    )

    assert report.learning_feedback_ready is False
    assert report.learning_band == "attention"
    assert report.ready_ratio == d("0.571429")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == (
        "team_scorecard_not_ready",
        "source_family_feedback_not_ready",
        "calibration_sample_not_ready",
    )


def test_validation_requires_decimal_free_public_api_and_hard_safety_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="postmortem_ready must be a bool"):
        build_report(postmortem_ready=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only must be True"):
        build_report(paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        build_report(report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(readonly=False)

    report = build_report()
    with pytest.raises(ValueError, match="ready_ratio must match readiness flags"):
        replace(report, ready_ratio=d("0.123456"))

    with pytest.raises(ValueError, match="digest must match report payload"):
        replace(report, digest="0" * 64)

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
