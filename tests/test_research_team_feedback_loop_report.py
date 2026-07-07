from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_team_feedback_loop_report import (
    ResearchTeamFeedbackLoopConfig,
    ResearchTeamFeedbackLoopFact,
    ResearchTeamFeedbackLoopReport,
    ResearchTeamFeedbackLoopRow,
    build_research_team_feedback_loop_report,
    research_team_feedback_loop_report_payload,
)


class DecimalSubclass(Decimal):
    pass


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def fact(**overrides: object) -> ResearchTeamFeedbackLoopFact:
    values = {
        "team_id": "macro-research",
        "feedback_reference": "case-alpha-redacted",
        "resolved_at": datetime(2026, 7, 1, 0, 0, tzinfo=UTC),
        "forecast_probability": d("0.620000"),
        "resolved_outcome_probability": d("0.600000"),
        "postmortem_quality_score": d("0.900000"),
        "evidence_quality_score": d("0.860000"),
        "resolution_quality_score": d("0.900000"),
        "learning_value_score": d("0.880000"),
        "improvement_themes": ("calibration_review",),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ResearchTeamFeedbackLoopFact(**values)


def report(*facts: ResearchTeamFeedbackLoopFact) -> ResearchTeamFeedbackLoopReport:
    return build_research_team_feedback_loop_report(
        facts,
        config=ResearchTeamFeedbackLoopConfig(),
        generated_at=GENERATED_AT,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload contains float")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_complete_pass_feedback_loop_builds_redacted_report_payload() -> None:
    result = report(fact())

    assert is_dataclass(result)
    assert result.report_status == "pass"
    assert result.fact_count == d("1.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.postmortem_ready_count == d("1.000000")
    assert result.learning_queue_count == d("1.000000")

    row = result.rows[0]
    assert is_dataclass(row)
    assert row.status == "pass"
    assert row.calibration_error == d("0.020000")
    assert row.postmortem_readiness_status == "pass"
    assert row.outcome_learning_action == "capture_verified_learning"
    assert row.memory_update_action == "reinforce_team_memory"
    assert row.hard_flags == ()

    payload = research_team_feedback_loop_report_payload(result)
    assert payload == result.payload
    assert payload["report_status"] == "pass"
    assert payload["fact_count"] == "1.000000"
    assert payload["postmortem_readiness"] == {
        "ready_count": "1.000000",
        "watch_count": "0.000000",
        "block_count": "0.000000",
    }
    assert payload["outcome_learning_queue"] == [
        {"outcome_learning_action": "capture_verified_learning", "count": "1.000000"},
    ]
    assert payload["memory_update_strategy"] == [
        {"memory_update_action": "reinforce_team_memory", "count": "1.000000"},
    ]
    assert payload["team_performance_summary"] == [
        {
            "team_id": "macro-research",
            "feedback_count": "1.000000",
            "pass_count": "1.000000",
            "watch_count": "0.000000",
            "block_count": "0.000000",
            "average_calibration_error": "0.020000",
            "average_postmortem_quality_score": "0.900000",
            "average_evidence_quality_score": "0.860000",
            "average_resolution_quality_score": "0.900000",
            "team_status": "pass",
        },
    ]
    assert payload["improvement_suggestions"] == [
        {
            "improvement_theme": "calibration_review",
            "suggestion": "preserve_high_quality_calibration_review_loop",
            "supporting_feedback_count": "1.000000",
        },
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)
    rendered = json.dumps(payload, sort_keys=True)
    for forbidden in (
        "case-alpha-redacted",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
    ):
        assert forbidden not in rendered


def test_watch_feedback_loop_marks_review_queue_without_block_flags() -> None:
    result = report(
        fact(
            feedback_reference="case-watch-redacted",
            forecast_probability=d("0.740000"),
            resolved_outcome_probability=d("0.600000"),
            improvement_themes=("probability_review",),
        ),
    )

    assert result.report_status == "watch"
    row = result.rows[0]
    assert row.status == "watch"
    assert row.calibration_error == d("0.140000")
    assert row.hard_flags == ()
    assert row.reason_codes == ("calibration_review_needed",)
    assert row.outcome_learning_action == "queue_probability_review"
    assert row.memory_update_action == "review_probability_memory"

    payload = research_team_feedback_loop_report_payload(result)
    assert payload["report_status"] == "watch"
    assert payload["status_counts"] == [{"status": "watch", "count": "1.000000"}]
    assert payload["improvement_suggestions"] == [
        {
            "improvement_theme": "probability_review",
            "suggestion": "tighten_probability_review_loop",
            "supporting_feedback_count": "1.000000",
        },
    ]


def test_quality_insufficient_feedback_loop_blocks_memory_update() -> None:
    result = report(
        fact(
            feedback_reference="case-quality-redacted",
            postmortem_quality_score=d("0.450000"),
            evidence_quality_score=d("0.400000"),
            resolution_quality_score=d("0.420000"),
            learning_value_score=d("0.400000"),
            improvement_themes=("evidence_quality", "resolution_quality"),
        ),
    )

    assert result.report_status == "block"
    row = result.rows[0]
    assert row.status == "block"
    assert row.postmortem_readiness_status == "block"
    assert row.hard_flags == (
        "evidence_quality_below_floor",
        "learning_value_below_floor",
        "postmortem_quality_below_floor",
        "resolution_quality_below_floor",
    )
    assert row.outcome_learning_action == "hold_low_quality_learning"
    assert row.memory_update_action == "quarantine_low_quality_memory"

    payload = research_team_feedback_loop_report_payload(result)
    assert payload["report_status"] == "block"
    assert payload["hard_flag_counts"] == [
        {"hard_flag": "evidence_quality_below_floor", "count": "1.000000"},
        {"hard_flag": "learning_value_below_floor", "count": "1.000000"},
        {"hard_flag": "postmortem_quality_below_floor", "count": "1.000000"},
        {"hard_flag": "resolution_quality_below_floor", "count": "1.000000"},
    ]
    assert payload["memory_update_strategy"] == [
        {"memory_update_action": "quarantine_low_quality_memory", "count": "1.000000"},
    ]


def test_types_are_strict_decimal_only_and_dataclasses_are_frozen() -> None:
    result = report(fact())

    for value in (ResearchTeamFeedbackLoopConfig(), fact(), result.rows[0], result):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="forecast_probability"):
        fact(forecast_probability=0.62)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality_score"):
        fact(evidence_quality_score=DecimalSubclass("0.860000"))
    with pytest.raises(ValueError, match="improvement_themes"):
        fact(improvement_themes=["calibration_review"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        build_research_team_feedback_loop_report(
            (fact(),),
            config=ResearchTeamFeedbackLoopConfig(),
            generated_at="2026-07-07",  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="config"):
        build_research_team_feedback_loop_report(
            (fact(),),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_exact_dataclass_types_do_not_support_subclassing() -> None:
    with pytest.raises(TypeError, match="subclassing"):

        class ConfigSubclass(ResearchTeamFeedbackLoopConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class FactSubclass(ResearchTeamFeedbackLoopFact):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class RowSubclass(ResearchTeamFeedbackLoopRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class ReportSubclass(ResearchTeamFeedbackLoopReport):
            pass


def test_unsafe_inputs_and_public_payload_leak_attempts_are_rejected() -> None:
    with pytest.raises(ValueError, match="feedback_reference"):
        fact(feedback_reference="case-alpha")
    with pytest.raises(ValueError, match="unsafe"):
        fact(feedback_reference="candidate-alpha-redacted")
    with pytest.raises(ValueError, match="unsafe"):
        fact(team_id="team-wallet")
    with pytest.raises(ValueError, match="improvement_themes"):
        fact(improvement_themes=("source_url",))
    with pytest.raises(ValueError, match="improvement_themes"):
        fact(improvement_themes=("recommendation_language",))

    payload = dict(research_team_feedback_loop_report_payload(report(fact())))
    for unsafe_payload in (
        {**payload, "market_id": "raw-market-id"},
        {**payload, "market_slug": "raw-market-slug"},
        {**payload, "question": "Will this leak?"},
        {**payload, "source_reference": "raw-source-reference"},
        {**payload, "source_url": "raw-source-url"},
        {**payload, "source_text": "raw-source-text"},
        {**payload, "database_table": "real_table"},
        {**payload, "local_dsn": "secret"},
        {**payload, "token": "secret"},
        {**payload, "wallet": "secret"},
        {**payload, "auth_surface": "secret"},
        {**payload, "trade_surface": "secret"},
        {**payload, "buy_signal": "unsafe"},
        {**payload, "sell_signal": "unsafe"},
        {**payload, "position_sizing": "unsafe"},
        {**payload, "recommendation_language": "unsafe"},
        {**payload, "team_performance_summary": [{"team_id": "market-alpha"}]},
    ):
        with pytest.raises(ValueError, match="unsafe|payload"):
            research_team_feedback_loop_report_payload(unsafe_payload)

    with pytest.raises(ValueError, match="float"):
        research_team_feedback_loop_report_payload(
            {**payload, "average_calibration_error": 0.1},
        )
    with pytest.raises(ValueError, match="Decimal"):
        research_team_feedback_loop_report_payload({**payload, "fact_count": 1})


def test_hard_report_only_flags_are_required_on_all_surfaces() -> None:
    result = report(fact())

    assert ResearchTeamFeedbackLoopConfig().paper_only is True
    assert ResearchTeamFeedbackLoopConfig().report_only is True
    assert ResearchTeamFeedbackLoopConfig().readonly is True
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.rows[0].paper_only is True
    assert result.rows[0].report_only is True
    assert result.rows[0].readonly is True

    with pytest.raises(ValueError, match="paper_only"):
        replace(ResearchTeamFeedbackLoopConfig(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(fact(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        research_team_feedback_loop_report_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )


def test_output_is_deterministic_across_input_order() -> None:
    alpha = fact(
        team_id="alpha-research",
        feedback_reference="case-alpha-redacted",
        resolved_at=datetime(2026, 7, 1, tzinfo=UTC),
        improvement_themes=("evidence_quality",),
    )
    beta = fact(
        team_id="beta-research",
        feedback_reference="case-beta-redacted",
        resolved_at=datetime(2026, 7, 2, tzinfo=UTC),
        forecast_probability=d("0.740000"),
        resolved_outcome_probability=d("0.600000"),
        improvement_themes=("probability_review",),
    )
    gamma = fact(
        team_id="alpha-research",
        feedback_reference="case-gamma-redacted",
        resolved_at=datetime(2026, 7, 3, tzinfo=UTC),
        improvement_themes=("calibration_review",),
    )

    first = report(beta, gamma, alpha)
    second = report(alpha, beta, gamma)

    assert first == second
    assert research_team_feedback_loop_report_payload(first) == (
        research_team_feedback_loop_report_payload(second)
    )
    assert tuple(row.feedback_reference for row in first.rows) == (
        "case-alpha-redacted",
        "case-gamma-redacted",
        "case-beta-redacted",
    )
    assert tuple(summary.team_id for summary in first.team_performance_summary) == (
        "alpha-research",
        "beta-research",
    )
    assert json.dumps(first.payload, sort_keys=True) == json.dumps(
        second.payload,
        sort_keys=True,
    )


def test_static_module_surface_is_pure_readonly_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_team_feedback_loop_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests.",
        "urllib",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "subprocess",
        "socket",
        "open(",
        "getenv",
        "environ",
        "postgres",
        "://",
    ):
        assert forbidden not in lowered
