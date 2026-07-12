from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
import hashlib
import inspect
import json
from typing import Any

import pytest

import polymarket_alpha_lab.probability_event_tail_risk_stress_scenario_report as api
from polymarket_alpha_lab.probability_event_tail_risk_stress_scenario_report import (
    PROBABILITY_EVENT_TAIL_RISK_STRESS_SCENARIO_STATUSES,
    ProbabilityEventTailRiskStressScenarioInput,
    ProbabilityEventTailRiskStressScenarioReport,
    build_probability_event_tail_risk_stress_scenario_report,
    probability_event_tail_risk_stress_scenario_public_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def stress_input(**overrides: object) -> ProbabilityEventTailRiskStressScenarioInput:
    values = {
        "base_case_probability": d("0.620000"),
        "tail_event_probability": d("0.120000"),
        "tail_loss_probability": d("0.250000"),
        "scenario_coverage_count": d("4.000000"),
        "required_scenario_count": d("3.000000"),
    }
    values.update(overrides)
    return ProbabilityEventTailRiskStressScenarioInput(**values)


def report(
    **overrides: object,
) -> ProbabilityEventTailRiskStressScenarioReport:
    return build_probability_event_tail_risk_stress_scenario_report(
        stress_input(**overrides),
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def test_builds_pass_tail_risk_report_with_stress_adjusted_edge() -> None:
    summary = report()

    assert is_dataclass(summary)
    assert type(summary) is ProbabilityEventTailRiskStressScenarioReport
    assert summary.base_case_probability == d("0.620000")
    assert summary.tail_event_probability == d("0.120000")
    assert summary.tail_loss_probability == d("0.250000")
    assert summary.scenario_coverage_count == d("4.000000")
    assert summary.required_scenario_count == d("3.000000")
    assert summary.tail_risk_charge_probability == d("0.030000")
    assert summary.scenario_coverage_ratio == d("1.333333")
    assert summary.stress_adjusted_edge_probability == d("0.590000")
    assert summary.tail_risk_status == "pass"
    assert summary.reason_codes == (
        "tail_risk_stress_scenario_report_pass",
    )
    assert summary.manual_next_step == "document_tail_risk_stress_review"
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.payload_digest) == 64


def test_blocks_when_stress_adjusted_edge_is_not_positive() -> None:
    summary = report(
        base_case_probability=d("0.040000"),
        tail_event_probability=d("0.500000"),
        tail_loss_probability=d("0.100000"),
    )

    assert summary.tail_risk_charge_probability == d("0.050000")
    assert summary.stress_adjusted_edge_probability == d("-0.010000")
    assert summary.tail_risk_status == "blocker"
    assert summary.reason_codes == (
        "stress_adjusted_edge_not_positive_blocker",
    )
    assert summary.manual_next_step == "escalate_manual_tail_risk_review"


def test_attention_when_scenario_coverage_is_below_required_count() -> None:
    summary = report(
        scenario_coverage_count=d("2.000000"),
        required_scenario_count=d("3.000000"),
    )

    assert summary.scenario_coverage_ratio == d("0.666667")
    assert summary.tail_risk_status == "attention"
    assert summary.reason_codes == (
        "scenario_coverage_below_required_attention",
    )
    assert summary.manual_next_step == "add_manual_tail_risk_scenarios"


def test_public_payload_and_digest_are_canonical_and_public_safe() -> None:
    summary = report()
    payload = summary.public_payload

    assert payload == probability_event_tail_risk_stress_scenario_public_payload(summary)
    assert payload["base_case_probability"] == "0.620000"
    assert payload["tail_event_probability"] == "0.120000"
    assert payload["tail_loss_probability"] == "0.250000"
    assert payload["tail_risk_charge_probability"] == "0.030000"
    assert payload["scenario_coverage_count"] == "4.000000"
    assert payload["required_scenario_count"] == "3.000000"
    assert payload["scenario_coverage_ratio"] == "1.333333"
    assert payload["stress_adjusted_edge_probability"] == "0.590000"
    assert payload["tail_risk_status"] == "pass"
    assert payload["reason_codes"] == ["tail_risk_stress_scenario_report_pass"]
    assert payload["manual_next_step"] == "document_tail_risk_stress_review"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == summary.payload_digest
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(payload)
    )

    digest_input = dict(payload)
    digest_input.pop("payload_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_input,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert payload["payload_digest"] == expected_digest

    payload_text = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "auth",
        "wallet",
        "order",
        "key",
        "sign",
        "auto",
        "live",
        "trade",
        "buy",
        "sell",
        "execute",
        "execution",
        "jsonl",
        "persist",
    ):
        assert forbidden not in payload_text


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    summary = report()

    with pytest.raises(FrozenInstanceError):
        summary.tail_risk_status = "attention"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        stress_input(base_case_probability=0.62)

    with pytest.raises(ValueError, match="integer-valued Decimal"):
        stress_input(scenario_coverage_count=d("2.500000"))

    with pytest.raises(ValueError, match="required_scenario_count"):
        stress_input(required_scenario_count=d("0.000000"))

    with pytest.raises(ValueError, match="paper_only"):
        replace(stress_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)

    with pytest.raises(ValueError, match="payload_digest"):
        replace(summary, stress_adjusted_edge_probability=d("0.010000"))


def test_no_io_or_actionable_surface_is_exposed() -> None:
    assert set(PROBABILITY_EVENT_TAIL_RISK_STRESS_SCENARIO_STATUSES) == {
        "pass",
        "attention",
        "blocker",
    }

    unsafe_terms = (
        "auth",
        "wallet",
        "order",
        "key",
        "sign",
        "auto",
        "live",
        "trade",
        "buy",
        "sell",
        "execute",
        "execution",
        "jsonl",
        "persist",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ProbabilityEventTailRiskStressScenarioInput,
        ProbabilityEventTailRiskStressScenarioReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    tree = ast.parse(inspect.getsource(api))
    imported_modules = {
        node.module.split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")])
    }
    assert imported_modules.isdisjoint(
        {
            "builtins",
            "os",
            "pathlib",
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "supabase",
            "web3",
            "ccxt",
            "subprocess",
        },
    )
