from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.probability_event_scenario_tree_consistency_report import (
    ProbabilityEventScenarioTreeConsistencyReport,
    build_probability_event_scenario_tree_consistency_report,
    probability_event_scenario_tree_consistency_public_payload,
    validate_probability_event_scenario_tree_consistency_payload_digest,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def report(
    *,
    scenario_count: Decimal = d("4"),
    covered_scenario_count: Decimal = d("4"),
    contradictory_scenario_count: Decimal = d("0"),
    base_case_probability: Decimal = d("0.650000"),
    tail_case_probability: Decimal = d("0.120000"),
) -> ProbabilityEventScenarioTreeConsistencyReport:
    return build_probability_event_scenario_tree_consistency_report(
        scenario_count=scenario_count,
        covered_scenario_count=covered_scenario_count,
        contradictory_scenario_count=contradictory_scenario_count,
        base_case_probability=base_case_probability,
        tail_case_probability=tail_case_probability,
    )


def test_complete_noncontradictory_tree_passes_with_public_digest() -> None:
    tree = report()

    assert type(tree) is ProbabilityEventScenarioTreeConsistencyReport
    assert tree.scenario_count == d("4")
    assert tree.covered_scenario_count == d("4")
    assert tree.contradictory_scenario_count == d("0")
    assert tree.base_case_probability == d("0.650000")
    assert tree.tail_case_probability == d("0.120000")
    assert tree.scenario_tree_status == "pass"
    assert tree.reason_codes == ("scenario_tree_consistent",)
    assert tree.manual_next_step == "No manual action required; keep monitoring scenario coverage."
    assert tree.paper_only is True
    assert tree.report_only is True
    assert tree.readonly is True

    payload = probability_event_scenario_tree_consistency_public_payload(tree)
    assert payload == tree.public_payload
    assert payload["scenario_count"] == "4"
    assert payload["covered_scenario_count"] == "4"
    assert payload["contradictory_scenario_count"] == "0"
    assert payload["base_case_probability"] == "0.650000"
    assert payload["tail_case_probability"] == "0.120000"
    assert payload["scenario_tree_status"] == "pass"
    assert payload["reason_codes"] == ["scenario_tree_consistent"]
    assert payload["manual_next_step"] == (
        "No manual action required; keep monitoring scenario coverage."
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_digest"] == tree.payload_digest
    assert len(tree.payload_digest) == 64
    int(tree.payload_digest, 16)
    assert json.loads(json.dumps(payload)) == payload
    assert validate_probability_event_scenario_tree_consistency_payload_digest(payload)


def test_incomplete_tree_watches_and_contradictions_block() -> None:
    incomplete = report(
        scenario_count=d("5"),
        covered_scenario_count=d("3"),
        contradictory_scenario_count=d("0"),
        base_case_probability=d("0.550000"),
        tail_case_probability=d("0.300000"),
    )

    assert incomplete.scenario_tree_status == "watch"
    assert incomplete.reason_codes == ("scenario_tree_incomplete",)
    assert incomplete.manual_next_step == (
        "Manually review missing scenario branches before using this probability event tree."
    )

    contradictory = report(
        scenario_count=d("5"),
        covered_scenario_count=d("5"),
        contradictory_scenario_count=d("1"),
        base_case_probability=d("0.550000"),
        tail_case_probability=d("0.300000"),
    )

    assert contradictory.scenario_tree_status == "block"
    assert contradictory.reason_codes == ("scenario_tree_contradictory",)
    assert contradictory.manual_next_step == (
        "Resolve contradictory scenario branches before relying on this probability event tree."
    )


def test_probability_order_and_empty_tree_are_blocked() -> None:
    ordered = report(
        scenario_count=d("2"),
        covered_scenario_count=d("2"),
        contradictory_scenario_count=d("0"),
        base_case_probability=d("0.200000"),
        tail_case_probability=d("0.300000"),
    )
    assert ordered.scenario_tree_status == "block"
    assert ordered.reason_codes == ("base_case_probability_below_tail_case_probability",)
    assert ordered.manual_next_step == (
        "Reconcile base and tail probabilities before relying on this probability event tree."
    )

    empty = report(
        scenario_count=d("0"),
        covered_scenario_count=d("0"),
        contradictory_scenario_count=d("0"),
        base_case_probability=d("0.000000"),
        tail_case_probability=d("0.000000"),
    )
    assert empty.scenario_tree_status == "block"
    assert empty.reason_codes == ("scenario_tree_empty",)
    assert empty.manual_next_step == (
        "Add scenario branches before using this probability event tree."
    )


def test_validation_rejects_non_decimal_values_bad_counts_flags_and_tamper() -> None:
    with pytest.raises(ValueError, match="scenario_count must be a Decimal"):
        report(scenario_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="base_case_probability must be a Decimal"):
        report(base_case_probability="0.650000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="covered_scenario_count"):
        report(scenario_count=d("2"), covered_scenario_count=d("3"))
    with pytest.raises(ValueError, match="contradictory_scenario_count"):
        report(
            scenario_count=d("2"),
            covered_scenario_count=d("2"),
            contradictory_scenario_count=d("3"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(report(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(), readonly=False)
    with pytest.raises(FrozenInstanceError):
        report().readonly = False  # type: ignore[misc]

    payload = dict(report().public_payload)
    payload["scenario_tree_status"] = "block"
    assert not validate_probability_event_scenario_tree_consistency_payload_digest(payload)


def test_module_is_readonly_report_only_without_durable_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "probability_event_scenario_tree_consistency_report.py"
    )
    source = module_path.read_text()
    forbidden_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "private_key",
        "sign",
        "execute",
        "jsonl",
        "open(",
        "Path(",
        "write_text",
        "append",
    )
    lowered = source.lower()
    for term in forbidden_terms:
        assert term not in lowered
