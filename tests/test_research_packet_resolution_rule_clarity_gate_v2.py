from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.research_packet_resolution_rule_clarity_gate_v2",
    )


def gate_input(**overrides: Any):
    values: dict[str, Any] = {
        "packet_id": "packet-alpha",
        "market_slug": "market-alpha",
        "rule_text_excerpt": "Resolves using final agency notice by stated deadline.",
        "resolution_criteria_count": d("4.000000"),
        "official_source_mapping_count": d("4.000000"),
        "ambiguous_phrase_count": d("0.000000"),
        "edge_case_coverage_count": d("4.000000"),
        "dispute_prone_trigger_count": d("0.000000"),
    }
    values.update(overrides)
    return api().ResearchPacketResolutionRuleClarityGateV2Input(**values)


def build(subject: object | None = None):
    return api().build_research_packet_resolution_rule_clarity_gate_v2(
        gate_input() if subject is None else subject,
    )


def assert_no_decimal_or_float_payload_values(value: Any) -> None:
    if isinstance(value, (Decimal, float)):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_or_float_payload_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_decimal_or_float_payload_values(item)


def test_clear_rule_text_scores_as_pass_with_hard_readonly_report_flags() -> None:
    module = api()

    result = build()

    assert result == module.ResearchPacketResolutionRuleClarityGateV2Result(
        packet_id="packet-alpha",
        market_slug="market-alpha",
        rule_text_excerpt="Resolves using final agency notice by stated deadline.",
        resolution_criteria_count=d("4.000000"),
        official_source_mapping_count=d("4.000000"),
        ambiguous_phrase_count=d("0.000000"),
        edge_case_coverage_count=d("4.000000"),
        dispute_prone_trigger_count=d("0.000000"),
        resolution_criteria_score=d("1.000000"),
        official_source_mapping_score=d("1.000000"),
        ambiguity_penalty_score=d("0.000000"),
        edge_case_coverage_score=d("1.000000"),
        dispute_trigger_penalty_score=d("0.000000"),
        clarity_score=d("1.000000"),
        clarity_gate_status="pass",
        recommended_action="include_in_research_packet",
        required_followups=(),
        reason_codes=(
            "clarity_status_pass",
            "resolution_criteria_complete",
            "official_sources_complete",
            "edge_cases_complete",
            "ambiguous_phrasing_clear",
            "dispute_triggers_clear",
        ),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    for value in (
        result.resolution_criteria_score,
        result.official_source_mapping_score,
        result.ambiguity_penalty_score,
        result.edge_case_coverage_score,
        result.dispute_trigger_penalty_score,
        result.clarity_score,
    ):
        assert type(value) is Decimal


def test_review_score_reflects_missing_source_mapping_ambiguity_edges_and_triggers() -> None:
    result = build(
        gate_input(
            packet_id="packet-review",
            resolution_criteria_count=d("3.000000"),
            official_source_mapping_count=d("1.000000"),
            ambiguous_phrase_count=d("2.000000"),
            edge_case_coverage_count=d("1.000000"),
            dispute_prone_trigger_count=d("1.000000"),
        ),
    )

    assert result.resolution_criteria_score == d("0.750000")
    assert result.official_source_mapping_score == d("0.333333")
    assert result.ambiguity_penalty_score == d("0.400000")
    assert result.edge_case_coverage_score == d("0.250000")
    assert result.dispute_trigger_penalty_score == d("0.250000")
    assert result.clarity_score == d("0.523333")
    assert result.clarity_gate_status == "review"
    assert result.recommended_action == "clarify_before_packet_use"
    assert result.required_followups == (
        "map_each_resolution_criterion_to_official_source",
        "remove_or_define_ambiguous_rule_phrasing",
        "add_missing_edge_case_resolution_paths",
        "neutralize_dispute_prone_trigger_language",
    )
    assert result.reason_codes == (
        "clarity_status_review",
        "resolution_criteria_partial",
        "official_sources_partial",
        "edge_cases_partial",
        "ambiguous_phrasing_present",
        "dispute_triggers_present",
    )


def test_blocked_score_clamps_extreme_rule_clarity_risks() -> None:
    result = build(
        gate_input(
            packet_id="packet-blocked",
            resolution_criteria_count=d("0.000000"),
            official_source_mapping_count=d("8.000000"),
            ambiguous_phrase_count=d("7.000000"),
            edge_case_coverage_count=d("0.000000"),
            dispute_prone_trigger_count=d("8.000000"),
        ),
    )

    assert result.resolution_criteria_score == d("0.000000")
    assert result.official_source_mapping_score == d("0.000000")
    assert result.ambiguity_penalty_score == d("1.000000")
    assert result.edge_case_coverage_score == d("0.000000")
    assert result.dispute_trigger_penalty_score == d("1.000000")
    assert result.clarity_score == d("0.000000")
    assert result.clarity_gate_status == "blocked"
    assert result.recommended_action == "exclude_until_rules_are_clarified"
    assert result.reason_codes == (
        "clarity_status_blocked",
        "resolution_criteria_missing",
        "official_sources_missing",
        "edge_cases_missing",
        "ambiguous_phrasing_heavy",
        "dispute_triggers_heavy",
    )


def test_public_payload_serializes_decimal_as_strings_and_rejects_tampering() -> None:
    module = api()
    result = build(
        gate_input(
            packet_id="packet-payload",
            resolution_criteria_count=d("2.000000"),
            official_source_mapping_count=d("1.000000"),
            ambiguous_phrase_count=d("1.000000"),
            edge_case_coverage_count=d("2.000000"),
            dispute_prone_trigger_count=d("0.000000"),
        ),
    )

    payload = module.research_packet_resolution_rule_clarity_gate_v2_payload(result)

    assert payload == result.payload
    assert payload["resolution_criteria_count"] == "2.000000"
    assert payload["official_source_mapping_score"] == "0.500000"
    assert payload["clarity_score"] == "0.595000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert_no_decimal_or_float_payload_values(payload)

    restored = module.ResearchPacketResolutionRuleClarityGateV2Result.from_payload(payload)
    assert restored == result

    tampered = dict(payload)
    tampered["clarity_score"] = "0.990000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.ResearchPacketResolutionRuleClarityGateV2Result.from_payload(tampered)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(result, packet_id="packet-tampered")


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    module = api()

    for forbidden_value in (
        "live surface",
        "auth callback",
        "wallet field",
        "order detail",
        "network call",
        "database row",
        "persist record",
        "signing request",
        "mutation path",
        "buy button",
        "sell action",
        "trade route",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            gate_input(rule_text_excerpt=forbidden_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("payload", {"safe": {"wallet": "blocked"}})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("payload", {"safe": "database field"})


def test_validation_rejects_wrong_types_subclasses_bad_flags_and_mismatched_results() -> None:
    module = api()
    subject = gate_input()
    result = build(subject)

    class InputSubclass(module.ResearchPacketResolutionRuleClarityGateV2Input):
        pass

    class ResultSubclass(module.ResearchPacketResolutionRuleClarityGateV2Result):
        pass

    with pytest.raises(FrozenInstanceError):
        subject.packet_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.clarity_gate_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="packet_id must"):
        gate_input(packet_id=" packet-alpha ")
    with pytest.raises(ValueError, match="rule_text_excerpt must"):
        gate_input(rule_text_excerpt="")
    with pytest.raises(ValueError, match="resolution_criteria_count must be a Decimal"):
        gate_input(resolution_criteria_count=4)
    with pytest.raises(ValueError, match="resolution_criteria_count must be nonnegative"):
        gate_input(resolution_criteria_count=d("-1.000000"))
    with pytest.raises(ValueError, match="resolution_criteria_count must be a whole Decimal"):
        gate_input(resolution_criteria_count=d("1.500000"))
    with pytest.raises(ValueError, match="official_source_mapping_count cannot exceed"):
        gate_input(
            resolution_criteria_count=d("3.000000"),
            official_source_mapping_count=d("4.000000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        gate_input(paper_only=False)
    with pytest.raises(ValueError, match="subject must be"):
        build(object())
    with pytest.raises(ValueError, match="subject must be"):
        build(InputSubclass(**subject.__dict__))
    with pytest.raises(ValueError, match="result must be"):
        module.research_packet_resolution_rule_clarity_gate_v2_payload(object())
    with pytest.raises(ValueError, match="result must be"):
        ResultSubclass(**result.__dict__)
    with pytest.raises(ValueError, match="clarity_score must match"):
        replace(result, clarity_score=d("0.010000"))
    with pytest.raises(ValueError, match="recommended_action must match"):
        replace(result, recommended_action="clarify_before_packet_use")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(result, reason_codes=("clarity_status_pass",))
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_module_is_decimal_only_report_only_and_unwired_from_live_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)

    assert module.ResearchPacketResolutionRuleClarityGateV2Input.__dataclass_params__.frozen
    assert module.ResearchPacketResolutionRuleClarityGateV2Result.__dataclass_params__.frozen
    assert module.__all__ == (
        "CLARITY_GATE_STATUSES",
        "RECOMMENDED_ACTIONS",
        "REQUIRED_FOLLOWUPS",
        "REASON_CODES",
        "ResearchPacketResolutionRuleClarityGateV2Input",
        "ResearchPacketResolutionRuleClarityGateV2Result",
        "build_research_packet_resolution_rule_clarity_gate_v2",
        "research_packet_resolution_rule_clarity_gate_v2_payload",
    )

    forbidden_import_roots = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    )
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "create_order",
        "open",
        "place_order",
        "read_text",
        "submit_order",
        "write_text",
    }

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert {name.split(".", 1)[0] for name in imported_modules}.isdisjoint(
        forbidden_import_roots,
    )
    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
