from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_learning_feedback_v3.py"
)
GENERATED_AT = datetime(2026, 7, 4, 16, 30, tzinfo=timezone(timedelta(hours=2)))
RESOLVED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_learning_feedback_v3",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    feedback = api()
    values: dict[str, object] = {
        "config_version": "strategy-team-learning-feedback-v3-test-v0",
        "calibration_watch_delta_threshold": d("0.100000"),
        "calibration_blocked_delta_threshold": d("0.250000"),
        "min_source_reliability_score": d("0.600000"),
    }
    values.update(overrides)
    return feedback.StrategyTeamLearningFeedbackV3Config(**values)


def resolved_recommendation(**overrides: object):
    feedback = api()
    values: dict[str, object] = {
        "team_id": "macro_team",
        "category_id": "macro_rates",
        "recommendation_id": "macro-cut-yes",
        "playbook_section": "rates_events",
        "resolved_at": RESOLVED_AT,
        "recommended_probability": d("0.800000"),
        "resolved_outcome": d("1.000000"),
        "source_reliability_score": d("0.900000"),
        "source_failure_tags": (),
        "playbook_update_suggestions": (),
    }
    values.update(overrides)
    return feedback.StrategyTeamLearningFeedbackV3ResolvedRecommendation(**values)


def report(*recommendations: object, cfg=None, generated_at: datetime = GENERATED_AT):
    feedback = api()
    return feedback.build_strategy_team_learning_feedback_v3_report(
        recommendations,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_payload_numbers(value: Any) -> None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        raise AssertionError(f"unexpected JSON numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_payload_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_payload_numbers(item)


def test_feedback_v3_summarizes_team_lessons_calibration_and_source_failures() -> None:
    feedback = api()
    feedback_report = report(
        resolved_recommendation(
            team_id="sports_team",
            category_id="sports_soccer",
            recommendation_id="sports-home-yes",
            playbook_section="injury_news",
            recommended_probability=d("0.900000"),
            resolved_outcome=d("0.000000"),
            source_reliability_score=d("0.300000"),
            source_failure_tags=("late_lineup_news", "thin_source_confirmation"),
            playbook_update_suggestions=(
                "require_lineup_confirmation_before_soccer_yes",
            ),
        ),
        resolved_recommendation(
            team_id="sports_team",
            category_id="sports_soccer",
            recommendation_id="sports-away-no",
            playbook_section="injury_news",
            recommended_probability=d("0.800000"),
            resolved_outcome=d("0.000000"),
            source_reliability_score=d("0.500000"),
            source_failure_tags=("late_lineup_news",),
            playbook_update_suggestions=(
                "cap_soccer_probability_when_lineup_news_is_stale",
            ),
        ),
        resolved_recommendation(
            team_id="macro_team",
            category_id="macro_rates",
            recommendation_id="macro-cut-yes",
            playbook_section="rates_events",
            recommended_probability=d("0.700000"),
            resolved_outcome=d("1.000000"),
            source_reliability_score=d("0.900000"),
        ),
        resolved_recommendation(
            team_id="macro_team",
            category_id="macro_rates",
            recommendation_id="macro-hold-no",
            playbook_section="rates_events",
            recommended_probability=d("0.300000"),
            resolved_outcome=d("0.000000"),
            source_reliability_score=d("0.800000"),
        ),
        resolved_recommendation(
            team_id="crypto_team",
            category_id="crypto_btc",
            recommendation_id="btc-range-yes",
            playbook_section="exchange_flows",
            recommended_probability=d("0.650000"),
            resolved_outcome=d("1.000000"),
            source_reliability_score=d("0.700000"),
            source_failure_tags=("thin_source_confirmation",),
            playbook_update_suggestions=("add_exchange_flow_confirmation_check",),
        ),
    )

    assert is_dataclass(feedback_report)
    assert feedback_report.generated_at == datetime(2026, 7, 4, 14, 30, tzinfo=UTC)
    assert feedback_report.config_version == "strategy-team-learning-feedback-v3-test-v0"
    assert feedback_report.source_recommendation_count == d("5")
    assert feedback_report.team_lesson_count == d("3")
    assert feedback_report.pass_count == d("1")
    assert feedback_report.watch_count == d("1")
    assert feedback_report.blocked_count == d("1")
    assert feedback_report.average_calibration_delta == d("-0.270000")
    assert feedback_report.average_source_reliability_score == d("0.640000")
    assert feedback_report.report_status == "blocked"
    assert feedback_report.reason_codes == (
        "strategy_team_learning_feedback_v3_calibration_blocked",
        "strategy_team_learning_feedback_v3_calibration_watch",
        "strategy_team_learning_feedback_v3_source_reliability_below_min",
        "strategy_team_learning_feedback_v3_source_failure_tags_observed",
        "strategy_team_learning_feedback_v3_playbook_updates_suggested",
    )
    assert feedback_report.paper_only is True
    assert feedback_report.report_only is True
    assert feedback_report.readonly is True

    assert tuple(lesson.team_id for lesson in feedback_report.team_lessons) == (
        "sports_team",
        "crypto_team",
        "macro_team",
    )
    assert tuple(lesson.lesson_status for lesson in feedback_report.team_lessons) == (
        "blocked",
        "watch",
        "pass",
    )

    blocked, watched, passed = feedback_report.team_lessons
    assert blocked.resolved_recommendation_count == d("2")
    assert blocked.average_recommended_probability == d("0.850000")
    assert blocked.average_resolved_outcome == d("0.000000")
    assert blocked.calibration_delta == d("-0.850000")
    assert blocked.average_source_reliability_score == d("0.400000")
    assert blocked.source_failure_tags == (
        "late_lineup_news",
        "thin_source_confirmation",
    )
    assert blocked.playbook_update_suggestions == (
        "cap_soccer_probability_when_lineup_news_is_stale",
        "require_lineup_confirmation_before_soccer_yes",
    )
    assert blocked.team_lesson == "reduce_sports_team_sports_soccer_playbook_confidence"
    assert blocked.reason_codes == (
        "strategy_team_learning_feedback_v3_calibration_blocked",
        "strategy_team_learning_feedback_v3_source_reliability_below_min",
        "strategy_team_learning_feedback_v3_source_failure_tags_observed",
        "strategy_team_learning_feedback_v3_playbook_updates_suggested",
    )

    assert watched.calibration_delta == d("0.350000")
    assert watched.team_lesson == "review_crypto_team_crypto_btc_playbook_calibration"
    assert watched.reason_codes == (
        "strategy_team_learning_feedback_v3_calibration_blocked",
        "strategy_team_learning_feedback_v3_source_failure_tags_observed",
        "strategy_team_learning_feedback_v3_playbook_updates_suggested",
    )

    assert passed.calibration_delta == d("0.000000")
    assert passed.team_lesson == "reuse_macro_team_macro_rates_playbook"
    assert passed.reason_codes == ("strategy_team_learning_feedback_v3_passed",)

    assert feedback_report.source_failure_tag_counts == (
        feedback.StrategyTeamLearningFeedbackV3SourceFailureTagCount(
            source_failure_tag="late_lineup_news",
            count=d("2"),
        ),
        feedback.StrategyTeamLearningFeedbackV3SourceFailureTagCount(
            source_failure_tag="thin_source_confirmation",
            count=d("2"),
        ),
    )
    assert feedback_report.playbook_update_suggestions == (
        feedback.StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion(
            playbook_section="exchange_flows",
            suggestion="add_exchange_flow_confirmation_check",
            supporting_lesson_count=d("1"),
        ),
        feedback.StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion(
            playbook_section="injury_news",
            suggestion="cap_soccer_probability_when_lineup_news_is_stale",
            supporting_lesson_count=d("1"),
        ),
        feedback.StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion(
            playbook_section="injury_news",
            suggestion="require_lineup_confirmation_before_soccer_yes",
            supporting_lesson_count=d("1"),
        ),
    )


def test_empty_feedback_v3_report_is_readonly_watch() -> None:
    empty = report()

    assert empty.source_recommendation_count == d("0")
    assert empty.team_lesson_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.average_calibration_delta == d("0.000000")
    assert empty.average_source_reliability_score == d("0.000000")
    assert empty.report_status == "watch"
    assert empty.team_lessons == ()
    assert empty.source_failure_tag_counts == ()
    assert empty.playbook_update_suggestions == ()
    assert empty.reason_codes == ("strategy_team_learning_feedback_v3_empty",)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_feedback_v3_payload_uses_decimal_strings_flags_and_readonly_report() -> None:
    feedback = api()
    feedback_report = report(
        resolved_recommendation(
            source_failure_tags=("late_lineup_news",),
            playbook_update_suggestions=("tighten_macro_event_window",),
        ),
    )
    payload = feedback.strategy_team_learning_feedback_v3_payload(feedback_report)

    assert payload["generated_at"] == "2026-07-04T14:30:00+00:00"
    assert payload["source_recommendation_count"] == "1"
    assert payload["team_lessons"][0]["calibration_delta"] == "0.200000"
    assert payload["team_lessons"][0]["resolved_recommendation_count"] == "1"
    assert payload["source_failure_tag_counts"][0]["count"] == "1"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_payload_numbers(payload)


def test_feedback_v3_validation_rejects_bad_types_times_flags_and_duplicates() -> None:
    feedback = api()

    with pytest.raises(ValueError, match="config"):
        feedback.build_strategy_team_learning_feedback_v3_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="recommended_probability must be a Decimal"):
        resolved_recommendation(recommended_probability=1)
    with pytest.raises(ValueError, match="resolved_outcome must be a Decimal"):
        resolved_recommendation(resolved_outcome=0.1)
    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        resolved_recommendation(source_reliability_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="resolved_at must be timezone-aware"):
        resolved_recommendation(resolved_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="resolved_at must be timezone-aware"):
        resolved_recommendation(
            resolved_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(
            resolved_recommendation(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(resolved_recommendation(), readonly=False)
    with pytest.raises(ValueError, match="recommendation_id values must be unique"):
        report(resolved_recommendation(), resolved_recommendation())
    with pytest.raises(ValueError, match="resolved_at must not be after generated_at"):
        report(resolved_recommendation(resolved_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="playbook_update_suggestions values must be unique"):
        resolved_recommendation(
            playbook_update_suggestions=("tighten_macro_event_window",) * 2,
        )

    feedback_report = report(resolved_recommendation())
    with pytest.raises(ValueError, match="source_recommendation_count"):
        replace(feedback_report, source_recommendation_count=d("2"))
    with pytest.raises(ValueError, match="team_lessons"):
        replace(feedback_report, team_lessons=(object(),))
    with pytest.raises(FrozenInstanceError):
        feedback_report.team_lessons[0].lesson_status = "watch"  # type: ignore[misc]


def test_feedback_v3_public_types_are_frozen_and_numeric_fields_are_decimal_only() -> None:
    feedback = api()
    feedback_report = report(resolved_recommendation())
    values = (
        config(),
        resolved_recommendation(),
        feedback_report.team_lessons[0],
        feedback_report.source_failure_tag_counts[0]
        if feedback_report.source_failure_tag_counts
        else feedback.StrategyTeamLearningFeedbackV3SourceFailureTagCount(
            source_failure_tag="late_lineup_news",
            count=d("1"),
        ),
        feedback_report,
    )
    numeric_suffixes = (
        "_count",
        "_score",
        "_threshold",
        "_probability",
        "_outcome",
        "_delta",
    )

    assert feedback.__all__ == (
        "DEFAULT_STRATEGY_TEAM_LEARNING_FEEDBACK_V3_CONFIG_VERSION",
        "StrategyTeamLearningFeedbackV3Config",
        "StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion",
        "StrategyTeamLearningFeedbackV3Report",
        "StrategyTeamLearningFeedbackV3ResolvedRecommendation",
        "StrategyTeamLearningFeedbackV3SourceFailureTagCount",
        "StrategyTeamLearningFeedbackV3TeamLesson",
        "build_strategy_team_learning_feedback_v3_report",
        "strategy_team_learning_feedback_v3_payload",
    )
    for exported_name in feedback.__all__:
        exported = getattr(feedback, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            if field.name.endswith(numeric_suffixes):
                assert type(getattr(value, field.name)) is Decimal

    for dataclass_type in (
        feedback.StrategyTeamLearningFeedbackV3Config,
        feedback.StrategyTeamLearningFeedbackV3PlaybookUpdateSuggestion,
        feedback.StrategyTeamLearningFeedbackV3Report,
        feedback.StrategyTeamLearningFeedbackV3ResolvedRecommendation,
        feedback.StrategyTeamLearningFeedbackV3SourceFailureTagCount,
        feedback.StrategyTeamLearningFeedbackV3TeamLesson,
    ):
        hints = get_type_hints(dataclass_type)
        for field in fields(dataclass_type):
            if field.name.endswith(numeric_suffixes):
                assert hints[field.name] is Decimal


def test_feedback_v3_module_scope_stays_pure_report_only() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live_trading",
        "wallet",
        "account",
        "broker",
        "cancel",
        "replace",
        "network",
        "database",
        "durable",
        "store",
        "payload_json",
        "private_key",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "psycopg",
        "sqlite",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "urllib",
    }
    forbidden_call_names = {
        "__import__",
        "connect",
        "eval",
        "exec",
        "executemany",
        "float",
        "open",
        "print",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
