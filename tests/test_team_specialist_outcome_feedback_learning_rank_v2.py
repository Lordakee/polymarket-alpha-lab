from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_outcome_feedback_learning_rank_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_outcome_feedback_learning_rank_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def feedback(**overrides: object):
    module = api()
    values = {
        "feedback_id": "feedback-rates-a",
        "team_id": "macro_rates",
        "specialist_id": "rates-specialist",
        "topic_id": "rates-outcomes",
        "outcome_feedback_count": d("6"),
        "incorporated_feedback_count": d("6"),
        "baseline_brier_score": d("0.300000"),
        "recent_brier_score": d("0.120000"),
        "baseline_calibration_error": d("0.250000"),
        "recent_calibration_error": d("0.100000"),
        "poor_calibration_event_count": d("0"),
        "latest_feedback_at": GENERATED_AT - timedelta(days=1),
        "latest_learning_at": GENERATED_AT - timedelta(days=1),
    }
    values.update(overrides)
    return module.TeamSpecialistOutcomeFeedbackLearningRankV2Input(**values)


def build_report(*rows: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_outcome_feedback_learning_rank_v2(
        rows,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_outcome_feedback_learning_rank_sorts_and_summarizes_rows() -> None:
    report = build_report(
        feedback(feedback_id="feedback-strong", team_id="macro_rates"),
        feedback(
            feedback_id="feedback-watch",
            team_id="policy_research",
            specialist_id="policy-specialist",
            topic_id="policy-outcomes",
            incorporated_feedback_count=d("4"),
            baseline_brier_score=d("0.400000"),
            recent_brier_score=d("0.200000"),
            baseline_calibration_error=d("0.600000"),
            recent_calibration_error=d("0.250000"),
            poor_calibration_event_count=d("1"),
            latest_learning_at=None,
        ),
        feedback(
            feedback_id="feedback-blocked",
            team_id="event_research",
            specialist_id="event-specialist",
            topic_id="event-outcomes",
            outcome_feedback_count=d("6"),
            incorporated_feedback_count=d("2"),
            baseline_brier_score=d("0.250000"),
            recent_brier_score=d("0.310000"),
            baseline_calibration_error=d("0.220000"),
            recent_calibration_error=d("0.360000"),
            poor_calibration_event_count=d("4"),
            latest_learning_at=None,
        ),
    )

    assert report.report_status == "blocked"
    assert report.source_feedback_count == d("3")
    assert report.row_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.recent_improvement_boost_count == d("1")
    assert report.poor_calibration_penalty_count == d("2")
    assert report.average_outcome_feedback_learning_score == d("0.417778")
    assert tuple(row.feedback_id for row in report.rows) == (
        "feedback-strong",
        "feedback-watch",
        "feedback-blocked",
    )
    assert tuple(row.rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.outcome_feedback_learning_score for row in report.rows) == (
        d("0.820000"),
        d("0.433333"),
        d("0.000000"),
    )
    assert tuple(row.row_status for row in report.rows) == ("pass", "watch", "blocked")
    assert report.reason_codes == (
        "outcome_feedback_learning_rank_blocked_rows",
        "outcome_feedback_learning_rank_watch_rows",
        "recent_improvement_boost_present",
        "poor_calibration_penalty_present",
    )


def test_poor_calibration_penalties_lower_rank_and_status() -> None:
    clean = build_report(feedback(poor_calibration_event_count=d("0"))).rows[0]
    penalized = build_report(feedback(poor_calibration_event_count=d("4"))).rows[0]

    assert clean.poor_calibration_penalty == d("0.000000")
    assert clean.outcome_feedback_learning_score == d("0.820000")
    assert clean.row_status == "pass"
    assert penalized.poor_calibration_penalty == d("0.300000")
    assert penalized.outcome_feedback_learning_score == d("0.520000")
    assert penalized.row_status == "watch"
    assert "poor_calibration_penalty_high" in penalized.reason_codes


def test_recent_improvement_boost_requires_recent_learning_and_improvement() -> None:
    boosted = build_report(feedback()).rows[0]
    old_learning = build_report(
        feedback(latest_learning_at=GENERATED_AT - timedelta(days=10)),
    ).rows[0]
    no_improvement = build_report(
        feedback(
            recent_brier_score=d("0.300000"),
            recent_calibration_error=d("0.250000"),
        ),
    ).rows[0]

    assert boosted.recent_improvement_boost_applied == d("0.150000")
    assert boosted.outcome_feedback_learning_score == d("0.820000")
    assert "recent_improvement_boost" in boosted.reason_codes
    assert old_learning.recent_improvement_boost_applied == d("0.000000")
    assert old_learning.outcome_feedback_learning_score == d("0.670000")
    assert "no_recent_improvement_boost" in old_learning.reason_codes
    assert no_improvement.recent_improvement_boost_applied == d("0.000000")
    assert no_improvement.outcome_feedback_learning_score == d("0.400000")


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    module = api()
    report = build_report(feedback())

    payload = module.team_specialist_outcome_feedback_learning_rank_v2_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_feedback_count"] == "1"
    assert payload["average_outcome_feedback_learning_score"] == "0.820000"
    assert payload["rows"][0]["outcome_feedback_learning_score"] == "0.820000"
    assert payload["rows"][0]["rank"] == "1"
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)

    assert module.team_specialist_outcome_feedback_learning_rank_v2_payload(payload) == payload


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    sample_config = module.TeamSpecialistOutcomeFeedbackLearningRankV2Config()
    sample_feedback = feedback()
    sample_report = build_report(sample_feedback)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_feedback, sample_row, sample_report):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        module.TeamSpecialistOutcomeFeedbackLearningRankV2Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        feedback(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(feedback(readonly=False))


def test_report_rejects_derived_validation_digest_tampering() -> None:
    module = api()
    report = build_report(feedback())
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["derived_validation_digest"] = "f" * 64

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.TeamSpecialistOutcomeFeedbackLearningRankV2Report(**values)


@pytest.mark.parametrize(
    "payload",
    (
        {"paper_only": True, "report_only": True, "readonly": True, "wallet_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "buy signal"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "live signal"},
        {"paper_only": True, "report_only": True, "readonly": True, "network": "mainnet"},
        {"paper_only": True, "report_only": False, "readonly": True},
    ),
)
def test_unsafe_public_payload_keys_values_and_flag_downgrades_rejected(
    payload: dict[str, object],
) -> None:
    module = api()

    with pytest.raises(ValueError):
        module.team_specialist_outcome_feedback_learning_rank_v2_payload(payload)


def test_public_string_values_reject_unsafe_surface_terms() -> None:
    with pytest.raises(ValueError, match="unsafe public value"):
        feedback(feedback_id="live-feedback")
    with pytest.raises(ValueError, match="unsafe public value"):
        feedback(specialist_id="wallet-specialist")


def test_module_scope_has_no_network_auth_wallet_order_db_or_trading_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "database",
        "db",
        "http",
        "network",
        "order",
        "persist",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
        "web3",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "sign",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
