from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_team_market_handoff_quality_score_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_team_market_handoff_quality_score_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def handoff_input(**overrides: object):
    module = api()
    values = {
        "market_id": "market-weather-001",
        "from_team": "team-research",
        "to_team": "team-resolution",
        "handoff_status": "ready",
        "required_section_count": d("8.000000"),
        "completed_section_count": d("8.000000"),
        "evidence_gap_count": d("0.000000"),
        "deadline_minutes": d("240.000000"),
    }
    values.update(overrides)
    return module.StrategyTeamMarketHandoffQualityScoreV10Input(**values)


def evaluate(**overrides: object):
    module = api()
    return module.strategy_team_market_handoff_quality_score_v10(
        handoff_input(**overrides),
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) is float or type(value) is int:
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def test_ready_handoff_scores_complete_with_acceptance_action() -> None:
    module = api()

    result = evaluate()

    assert is_dataclass(result)
    assert result.market_id == "market-weather-001"
    assert result.from_team == "team-research"
    assert result.to_team == "team-resolution"
    assert result.handoff_status == "ready"
    assert result.required_section_count == d("8.000000")
    assert result.completed_section_count == d("8.000000")
    assert result.evidence_gap_count == d("0.000000")
    assert result.deadline_minutes == d("240.000000")
    assert result.handoff_quality_status == "complete"
    assert result.handoff_quality_score == d("1.000000")
    assert result.repair_actions == ("accept_handoff",)
    assert result.reason_codes == (
        "sections_complete",
        "evidence_gap_none",
        "deadline_window_open",
        "handoff_ready",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    encoded = json.dumps(payload, sort_keys=True)
    assert payload == module.strategy_team_market_handoff_quality_score_v10_payload(result)
    assert payload["config_version"] == "strategy-team-market-handoff-quality-score-v10"
    assert payload["market_id"] == "market-weather-001"
    assert payload["from_team"] == "team-research"
    assert payload["to_team"] == "team-resolution"
    assert payload["handoff_status"] == "ready"
    assert payload["required_section_count"] == "8.000000"
    assert payload["completed_section_count"] == "8.000000"
    assert payload["evidence_gap_count"] == "0.000000"
    assert payload["deadline_minutes"] == "240.000000"
    assert payload["handoff_quality_status"] == "complete"
    assert payload["handoff_quality_score"] == "1.000000"
    assert payload["repair_actions"] == ["accept_handoff"]
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert '"1.000000"' in encoded
    assert_no_float_or_int_values(payload)


def test_partial_handoff_scores_repair_with_specific_repair_actions() -> None:
    result = evaluate(
        handoff_status="in_review",
        completed_section_count=d("5.000000"),
        evidence_gap_count=d("2.000000"),
        deadline_minutes=d("45.000000"),
    )

    assert result.handoff_quality_status == "repair"
    assert result.handoff_quality_score == d("0.637500")
    assert result.repair_actions == (
        "complete_required_sections",
        "close_evidence_gaps",
        "expedite_deadline_review",
    )
    assert result.reason_codes == (
        "sections_partial",
        "evidence_gap_present",
        "deadline_window_compressed",
        "handoff_in_review",
    )


def test_blocked_handoff_remains_blocked_until_repaired() -> None:
    result = evaluate(
        handoff_status="blocked",
        completed_section_count=d("4.000000"),
        evidence_gap_count=d("3.000000"),
        deadline_minutes=d("15.000000"),
    )

    assert result.handoff_quality_status == "blocked"
    assert result.handoff_quality_score == d("0.481250")
    assert result.repair_actions == (
        "block_handoff_until_repaired",
        "complete_required_sections",
        "close_evidence_gaps",
        "expedite_deadline_review",
    )
    assert result.reason_codes == (
        "sections_partial",
        "evidence_gap_high",
        "deadline_window_urgent",
        "handoff_blocked",
    )


def test_public_numeric_dataclass_fields_are_decimal_only() -> None:
    module = api()
    numeric_fields = {
        "required_section_count",
        "completed_section_count",
        "evidence_gap_count",
        "deadline_minutes",
        "handoff_quality_score",
    }

    for cls in (
        module.StrategyTeamMarketHandoffQualityScoreV10Input,
        module.StrategyTeamMarketHandoffQualityScoreV10Report,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in numeric_fields:
                assert hints[item.name] is Decimal


def test_validation_rejects_bad_types_ranges_precision_consistency_and_flags() -> None:
    module = api()
    result = evaluate()

    with pytest.raises(FrozenInstanceError):
        result.handoff_quality_status = "repair"  # type: ignore[misc]

    with pytest.raises(ValueError, match="market_id"):
        handoff_input(market_id=_StringSubclass("market-weather-001"))

    with pytest.raises(ValueError, match="from_team and to_team must differ"):
        handoff_input(to_team="team-research")

    with pytest.raises(ValueError, match="required_section_count must be a Decimal"):
        handoff_input(required_section_count=8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="completed_section_count must be a Decimal"):
        handoff_input(completed_section_count=_DecimalSubclass("8.000000"))

    with pytest.raises(ValueError, match="required_section_count must be positive"):
        handoff_input(required_section_count=d("0.000000"))

    with pytest.raises(ValueError, match="evidence_gap_count must be nonnegative"):
        handoff_input(evidence_gap_count=d("-1.000000"))

    with pytest.raises(ValueError, match="deadline_minutes must be whole"):
        handoff_input(deadline_minutes=d("15.500000"))

    with pytest.raises(ValueError, match="deadline_minutes must use the required decimal precision"):
        handoff_input(deadline_minutes=d("15.0000001"))

    with pytest.raises(ValueError, match="completed_section_count must not exceed required_section_count"):
        handoff_input(completed_section_count=d("9.000000"))

    with pytest.raises(ValueError, match="handoff_status must be a known value"):
        handoff_input(handoff_status="submitted")

    with pytest.raises(ValueError, match="paper_only must be True"):
        handoff_input(paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="handoff_quality_score must match input fields"):
        module.StrategyTeamMarketHandoffQualityScoreV10Report(
            market_id="market-weather-001",
            from_team="team-research",
            to_team="team-resolution",
            handoff_status="ready",
            required_section_count=d("8.000000"),
            completed_section_count=d("8.000000"),
            evidence_gap_count=d("0.000000"),
            deadline_minutes=d("240.000000"),
            handoff_quality_status="complete",
            handoff_quality_score=d("0.900000"),
            repair_actions=("accept_handoff",),
            reason_codes=(
                "sections_complete",
                "evidence_gap_none",
                "deadline_window_open",
                "handoff_ready",
            ),
        )


def test_payload_rejects_non_report_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_team_market_handoff_quality_score_v10_payload(object())


def test_public_strings_reject_secret_like_values_before_payload_leakage() -> None:
    with pytest.raises(ValueError, match="must not contain sensitive material"):
        handoff_input(from_team="team-secret-review")


def test_module_scope_is_paper_report_readonly_with_no_external_or_execution_surface() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "durable",
        "store",
        "open(",
        "requests",
        "http",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
