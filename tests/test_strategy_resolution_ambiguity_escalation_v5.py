from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_resolution_ambiguity_escalation_v5",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    case_id: str = "case_clear",
    *,
    question_specificity_score: Decimal = d("0.900000"),
    rules_clarity_score: Decimal = d("0.900000"),
    source_hierarchy_level: str = "primary_resolution_source",
    seconds_until_close: Decimal = d("172800.000000"),
    dispute_indicator_count: Decimal = d("0"),
    team_confidence_score: Decimal = d("0.900000"),
) -> Any:
    module = api()
    return module.StrategyResolutionAmbiguityEscalationV5Signal(
        case_id=case_id,
        question_specificity_score=question_specificity_score,
        rules_clarity_score=rules_clarity_score,
        source_hierarchy_level=source_hierarchy_level,
        seconds_until_close=seconds_until_close,
        dispute_indicator_count=dispute_indicator_count,
        team_confidence_score=team_confidence_score,
    )


def build_report(*signals: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_strategy_resolution_ambiguity_escalation_v5_report(
        signals,
        config=cfg if cfg is not None else module.StrategyResolutionAmbiguityEscalationV5Config(),
        generated_at=GENERATED_AT,
    )


def test_escalates_critically_ambiguous_resolution_inputs_to_operations() -> None:
    report = build_report(
        signal(
            "case_escalate",
            question_specificity_score=d("0.400000"),
            rules_clarity_score=d("0.500000"),
            source_hierarchy_level="missing_resolution_source",
            seconds_until_close=d("1800.000000"),
            dispute_indicator_count=d("2"),
            team_confidence_score=d("0.450000"),
        ),
    )

    assert report.escalation_status == "escalate"
    assert report.owner_team == "resolution_operations_team"
    assert report.next_action == "escalate_for_manual_resolution_review"
    assert report.signal_count == d("1")
    assert report.escalate_count == d("1")
    assert report.watch_count == d("0")
    assert report.clear_count == d("0")
    assert report.reason_codes == (
        "question_specificity_critically_low",
        "resolution_rules_critically_unclear",
        "source_hierarchy_missing",
        "close_time_imminent",
        "dispute_indicators_elevated",
        "team_confidence_critically_low",
    )

    row = report.rows[0]
    assert row.case_id == "case_escalate"
    assert row.escalation_status == "escalate"
    assert row.owner_team == "resolution_operations_team"
    assert row.next_action == "escalate_for_manual_resolution_review"
    assert row.reason_codes == report.reason_codes
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_watch_and_clear_rows_are_ranked_and_rolled_up_deterministically() -> None:
    report = build_report(
        signal("case_clear"),
        signal(
            "case_watch",
            question_specificity_score=d("0.700000"),
            rules_clarity_score=d("0.750000"),
            source_hierarchy_level="secondary_resolution_source",
            seconds_until_close=d("7200.000000"),
            dispute_indicator_count=d("1"),
            team_confidence_score=d("0.650000"),
        ),
    )

    assert tuple(row.case_id for row in report.rows) == ("case_watch", "case_clear")
    assert report.escalation_status == "watch"
    assert report.owner_team == "resolution_policy_team"
    assert report.next_action == "schedule_resolution_review"
    assert report.signal_count == d("2")
    assert report.watch_count == d("1")
    assert report.clear_count == d("1")
    assert report.escalate_count == d("0")
    assert report.reason_codes == (
        "question_specificity_low",
        "resolution_rules_unclear",
        "source_hierarchy_secondary_only",
        "close_time_inside_review_window",
        "dispute_indicators_present",
        "team_confidence_low",
    )

    watch_row = report.rows[0]
    assert watch_row.escalation_status == "watch"
    assert watch_row.owner_team == "resolution_policy_team"
    assert watch_row.next_action == "schedule_resolution_review"

    clear_row = report.rows[1]
    assert clear_row.escalation_status == "clear"
    assert clear_row.owner_team == "strategy_research_team"
    assert clear_row.next_action == "continue_paper_monitoring"
    assert clear_row.reason_codes == ("resolution_ambiguity_clear",)


def test_empty_report_is_clear_readonly_and_decimal_counted() -> None:
    report = build_report()

    assert report.generated_at == GENERATED_AT
    assert report.escalation_status == "clear"
    assert report.owner_team == "strategy_research_team"
    assert report.next_action == "continue_paper_monitoring"
    assert report.signal_count == d("0")
    assert report.clear_count == d("0")
    assert report.watch_count == d("0")
    assert report.escalate_count == d("0")
    assert report.reason_codes == ("no_resolution_ambiguity_signals_supplied",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rejects_non_decimal_numerics_unknown_levels_and_non_utc_times() -> None:
    module = api()

    with pytest.raises(ValueError, match="question_specificity_score must be a Decimal"):
        signal(question_specificity_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="rules_clarity_score must be a Decimal"):
        signal(rules_clarity_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dispute_indicator_count must be integral"):
        signal(dispute_indicator_count=d("1.500000"))
    with pytest.raises(ValueError, match="seconds_until_close must be nonnegative"):
        signal(seconds_until_close=d("-1.000000"))
    with pytest.raises(ValueError, match="source_hierarchy_level must be a known source hierarchy level"):
        signal(source_hierarchy_level="forum_post")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_resolution_ambiguity_escalation_v5_report(
            (),
            config=module.StrategyResolutionAmbiguityEscalationV5Config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )


def test_public_dataclasses_are_frozen_and_exports_are_stable() -> None:
    module = api()
    report = build_report(signal("case_frozen"))

    assert module.__all__ == (
        "DEFAULT_STRATEGY_RESOLUTION_AMBIGUITY_ESCALATION_V5_CONFIG_VERSION",
        "StrategyResolutionAmbiguityEscalationV5Config",
        "StrategyResolutionAmbiguityEscalationV5Report",
        "StrategyResolutionAmbiguityEscalationV5Row",
        "StrategyResolutionAmbiguityEscalationV5Signal",
        "build_strategy_resolution_ambiguity_escalation_v5_report",
        "strategy_resolution_ambiguity_escalation_v5_payload",
    )
    assert is_dataclass(module.StrategyResolutionAmbiguityEscalationV5Config())
    assert is_dataclass(signal("case_dataclass"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.escalation_status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].owner_team = "changed"
    with pytest.raises(FrozenInstanceError):
        module.StrategyResolutionAmbiguityEscalationV5Config().team_confidence_watch_threshold = d(
            "0.600000",
        )


def test_payload_is_json_ready_decimal_stringed_and_float_free() -> None:
    module = api()
    report = build_report(
        signal(
            "case_payload",
            source_hierarchy_level="secondary_resolution_source",
            seconds_until_close=d("7200.000000"),
        ),
    )

    payload = module.strategy_resolution_ambiguity_escalation_v5_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["signal_count"] == "1"
    assert payload["watch_count"] == "1"
    assert payload["rows"][0]["question_specificity_score"] == "0.900000"
    assert payload["rows"][0]["seconds_until_close"] == "7200.000000"
    json.dumps(payload)

    def assert_no_float_or_decimal_values(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float_or_decimal_values(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float_or_decimal_values(item)
        else:
            assert type(value) is not float
            assert type(value) is not Decimal

    assert_no_float_or_decimal_values(payload)


def test_module_scope_is_pure_readonly_report_without_io_db_or_execution_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "subprocess",
        "broker",
        "wallet",
        "private_key",
        "credential",
        "submit",
        "cancel",
        "execute",
        "connect",
        "trade",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "post",
                "put",
                "delete",
                "send",
                "submit",
                "cancel",
            }
