from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_settlement_delay_risk_report import (
    ProbabilityEventSettlementDelayRiskInput,
    ProbabilityEventSettlementDelayRiskReport,
    build_probability_event_settlement_delay_risk_report,
    probability_event_settlement_delay_risk_report_digest,
    probability_event_settlement_delay_risk_report_payload,
    validate_probability_event_settlement_delay_risk_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_settlement_delay_risk_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def risk_input(
    *,
    expected_resolution_hours: Decimal = d("12.000000"),
    historical_delay_hours: Decimal = d("2.000000"),
    oracle_dependency_count: Decimal = d("0.000000"),
    ambiguous_rule_count: Decimal = d("0.000000"),
    capital_lockup_probability: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ProbabilityEventSettlementDelayRiskInput:
    return ProbabilityEventSettlementDelayRiskInput(
        expected_resolution_hours=expected_resolution_hours,
        historical_delay_hours=historical_delay_hours,
        oracle_dependency_count=oracle_dependency_count,
        ambiguous_rule_count=ambiguous_rule_count,
        capital_lockup_probability=capital_lockup_probability,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    **overrides: Decimal | bool,
) -> ProbabilityEventSettlementDelayRiskReport:
    return build_probability_event_settlement_delay_risk_report(
        risk_input(**overrides),
    )


def test_builds_pass_report_with_payload_digest_and_public_decimal_strings() -> None:
    result = report()

    assert result.delay_risk_status == "pass"
    assert result.expected_settlement_delay_hours == d("16.400000")
    assert result.reason_codes == ("settlement_delay_risk_pass",)
    assert result.manual_next_step == "monitor_public_resolution_timeline"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload_digest == probability_event_settlement_delay_risk_report_digest(
        result,
    )

    payload = probability_event_settlement_delay_risk_report_payload(result)
    assert payload is result.public_payload
    assert payload["expected_resolution_hours"] == "12.000000"
    assert payload["historical_delay_hours"] == "2.000000"
    assert payload["oracle_dependency_count"] == "0.000000"
    assert payload["ambiguous_rule_count"] == "0.000000"
    assert payload["capital_lockup_probability"] == "0.050000"
    assert payload["expected_settlement_delay_hours"] == "16.400000"
    assert payload["payload_digest"] == result.payload_digest
    assert len(result.payload_digest) == 64
    validate_probability_event_settlement_delay_risk_public_payload(payload)


def test_watch_report_surfaces_oracle_dependency_delay_risk_only() -> None:
    result = report(
        expected_resolution_hours=d("30.000000"),
        historical_delay_hours=d("10.000000"),
        oracle_dependency_count=d("2.000000"),
        capital_lockup_probability=d("0.100000"),
    )

    assert result.delay_risk_status == "watch"
    assert result.expected_settlement_delay_hours == d("68.800000")
    assert result.reason_codes == ("oracle_dependency_delay_risk",)
    assert result.manual_next_step == "prepare_manual_settlement_delay_review"
    assert result.public_payload["delay_risk_status"] == "watch"


def test_block_report_combines_delay_rule_ambiguity_and_capital_lockup_reasons() -> None:
    result = report(
        expected_resolution_hours=d("100.000000"),
        historical_delay_hours=d("48.000000"),
        oracle_dependency_count=d("4.000000"),
        ambiguous_rule_count=d("3.000000"),
        capital_lockup_probability=d("0.800000"),
    )

    assert result.delay_risk_status == "block"
    assert result.expected_settlement_delay_hours == d("296.400000")
    assert result.reason_codes == (
        "expected_resolution_window_extended",
        "historical_settlement_delay_observed",
        "oracle_dependency_delay_risk",
        "ambiguous_resolution_rule_delay_risk",
        "capital_lockup_probability_high",
    )
    assert result.manual_next_step == "pause_new_capital_until_resolution_risk_review"


def test_dataclasses_are_frozen_flag_guarded_and_decimal_only() -> None:
    input_value = risk_input()
    result = report()

    with pytest.raises(FrozenInstanceError):
        input_value.expected_resolution_hours = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.delay_risk_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventSettlementDelayRiskInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventSettlementDelayRiskReport):
            pass

    with pytest.raises(ValueError, match="expected_resolution_hours"):
        risk_input(expected_resolution_hours=12)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="oracle_dependency_count"):
        risk_input(oracle_dependency_count=d("1.500000"))
    with pytest.raises(ValueError, match="capital_lockup_probability"):
        risk_input(capital_lockup_probability=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        risk_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="expected_settlement_delay_hours"):
        replace(result, expected_settlement_delay_hours=0)  # type: ignore[arg-type]

    numeric_fields = {
        "expected_resolution_hours",
        "historical_delay_hours",
        "oracle_dependency_count",
        "ambiguous_rule_count",
        "capital_lockup_probability",
        "expected_settlement_delay_hours",
    }
    hints = get_type_hints(ProbabilityEventSettlementDelayRiskInput)
    report_hints = get_type_hints(ProbabilityEventSettlementDelayRiskReport)
    for field in fields(ProbabilityEventSettlementDelayRiskInput):
        if field.name in numeric_fields:
            assert hints[field.name] is Decimal
    for field in fields(ProbabilityEventSettlementDelayRiskReport):
        if field.name in numeric_fields:
            assert report_hints[field.name] is Decimal
    _assert_public_numeric_values_are_decimal(result)


def test_public_payload_tamper_checks_and_no_disallowed_surfaces() -> None:
    payload = dict(report().public_payload)
    assert payload["payload_digest"]

    with pytest.raises(ValueError, match="payload_digest"):
        probability_event_settlement_delay_risk_report_payload(
            replace(report(), payload_digest="0" * 64),
        )
    with pytest.raises(ValueError, match="payload_digest"):
        validate_probability_event_settlement_delay_risk_public_payload(
            {**payload, "delay_risk_status": "block"},
        )
    with pytest.raises(ValueError, match="payload_digest"):
        validate_probability_event_settlement_delay_risk_public_payload(
            {**payload, "payload_digest": "0" * 64},
        )
    with pytest.raises(TypeError):
        report().public_payload["delay_risk_status"] = "block"

    encoded = json.dumps(payload, sort_keys=True).lower()
    for fragment in _blocked_fragments():
        assert fragment not in encoded

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for fragment in _blocked_fragments():
        assert fragment not in lowered_source

    tree = ast.parse(source)
    blocked_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "fetch",
        "insert",
        "open",
        "post",
        "put",
        "rollback",
        "sell",
        "send",
        "upsert",
    }
    call_names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not float_constants
    assert not any(name in blocked_call_names for name in call_names)


def _blocked_fragments() -> tuple[str, ...]:
    return (
        "li" + "ve",
        "au" + "th",
        "wal" + "let",
        "or" + "der",
        "private" + "_key",
        "api" + "_key",
        "secret" + "_key",
        "si" + "gn",
        "自动" + "下单",
        "执行" + "路径",
    )


def _assert_public_numeric_values_are_decimal(value: Any) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for child in value.values():
            _assert_public_numeric_values_are_decimal(child)
        return
    if isinstance(value, (list, tuple)):
        for child in value:
            _assert_public_numeric_values_are_decimal(child)
