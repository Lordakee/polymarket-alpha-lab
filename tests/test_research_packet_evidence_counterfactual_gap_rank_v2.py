from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_evidence_counterfactual_gap_rank_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def packet(
    packet_ref: str,
    *,
    question_ref: str = "q-election-certification",
    event_category: str = "politics",
    counterfactual_evidence_count: str = "0",
    catalyst_urgency_score: str = "0.900000",
    source_coverage_score: str = "0.100000",
    contradiction_severity_score: str = "0.800000",
    resolution_rule_sensitivity_score: str = "0.900000",
):
    ranker = api()
    return ranker.ResearchPacketCounterfactualEvidenceGapInput(
        packet_ref=packet_ref,
        question_ref=question_ref,
        event_category=event_category,
        counterfactual_evidence_count=d(counterfactual_evidence_count),
        catalyst_urgency_score=d(catalyst_urgency_score),
        source_coverage_score=d(source_coverage_score),
        contradiction_severity_score=d(contradiction_severity_score),
        resolution_rule_sensitivity_score=d(resolution_rule_sensitivity_score),
    )


def report(*packets):
    ranker = api()
    return ranker.build_research_packet_evidence_counterfactual_gap_rank_v2_report(
        packets,
        config=ranker.ResearchPacketCounterfactualEvidenceGapRankV2Config(),
    )


def test_report_ranks_missing_counterfactual_evidence_by_weighted_drivers() -> None:
    gap_report = report(
        packet(
            "pkt-clear",
            event_category="other",
            counterfactual_evidence_count="2",
            catalyst_urgency_score="0.100000",
            source_coverage_score="1.000000",
            contradiction_severity_score="0.000000",
            resolution_rule_sensitivity_score="0.100000",
        ),
        packet(
            "pkt-watch",
            event_category="macro",
            counterfactual_evidence_count="1",
            catalyst_urgency_score="0.500000",
            source_coverage_score="0.500000",
            contradiction_severity_score="0.200000",
            resolution_rule_sensitivity_score="0.500000",
        ),
        packet("pkt-urgent"),
    )

    assert is_dataclass(gap_report)
    assert gap_report.config_version == "research-packet-evidence-counterfactual-gap-rank-v2-v0"
    assert gap_report.input_count == d("3")
    assert gap_report.blocked_count == d("1")
    assert gap_report.watch_count == d("1")
    assert gap_report.pass_count == d("1")
    assert gap_report.missing_counterfactual_evidence_count == d("2")
    assert gap_report.high_catalyst_urgency_count == d("1")
    assert gap_report.thin_source_coverage_count == d("2")
    assert gap_report.contradiction_severity_count == d("2")
    assert gap_report.resolution_rule_sensitive_count == d("2")
    assert gap_report.highest_priority_score == d("0.935000")
    assert gap_report.status == "blocked"
    assert gap_report.recommended_next_step == (
        "collect_counterfactual_evidence_before_using_packet"
    )
    assert gap_report.reason_codes == (
        "counterfactual_gap_rank_status_blocked",
        "missing_counterfactual_evidence",
        "high_event_category_priority",
        "high_catalyst_urgency",
        "thin_source_coverage",
        "contradiction_severity",
        "resolution_rule_sensitive",
    )
    assert gap_report.paper_only is True
    assert gap_report.report_only is True
    assert gap_report.readonly is True
    assert len(gap_report.derived_validation_digest) == 64

    assert tuple(row.packet_ref for row in gap_report.rows) == (
        "pkt-urgent",
        "pkt-watch",
        "pkt-clear",
    )
    urgent = gap_report.rows[0]
    assert urgent.priority_rank == d("1")
    assert urgent.priority_score == d("0.935000")
    assert urgent.counterfactual_gap_score == d("1.000000")
    assert urgent.event_category_priority_score == d("1.000000")
    assert urgent.source_coverage_gap_score == d("0.900000")
    assert urgent.gap_status == "blocked"
    assert urgent.recommended_research_action == "collect_counterfactual_evidence_first"
    assert urgent.reason_codes == (
        "counterfactual_gap_rank_status_blocked",
        "missing_counterfactual_evidence",
        "high_event_category_priority",
        "high_catalyst_urgency",
        "thin_source_coverage",
        "contradiction_severity",
        "resolution_rule_sensitive",
    )

    watch = gap_report.rows[1]
    assert watch.priority_score == d("0.530000")
    assert watch.gap_status == "watch"

    clear = gap_report.rows[2]
    assert clear.priority_score == d("0.067500")
    assert clear.gap_status == "pass"


def test_payload_is_json_ready_decimal_string_and_digest_checked() -> None:
    ranker = api()
    gap_report = report(packet("pkt-urgent"))

    payload = ranker.research_packet_evidence_counterfactual_gap_rank_v2_payload(
        gap_report,
    )

    assert payload["input_count"] == "1"
    assert payload["blocked_count"] == "1"
    assert payload["highest_priority_score"] == "0.935000"
    assert payload["rows"][0]["priority_score"] == "0.935000"
    assert payload["rows"][0]["counterfactual_evidence_count"] == "0.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == gap_report.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(gap_report, input_count=d("2"))

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(gap_report.rows[0], priority_score=d("0.100000"))


def test_inputs_validate_decimal_categories_flags_duplicates_and_mutation() -> None:
    ranker = api()

    with pytest.raises(ValueError, match="catalyst_urgency_score must be a Decimal"):
        ranker.ResearchPacketCounterfactualEvidenceGapInput(
            packet_ref="pkt-float",
            question_ref="q-float",
            event_category="politics",
            counterfactual_evidence_count=d("0"),
            catalyst_urgency_score=0.5,
            source_coverage_score=d("0.100000"),
            contradiction_severity_score=d("0.800000"),
            resolution_rule_sensitivity_score=d("0.900000"),
        )

    with pytest.raises(ValueError, match="event_category must be one of"):
        packet("pkt-category", event_category="unsupported")

    with pytest.raises(ValueError, match="source_coverage_score must be between"):
        packet("pkt-coverage", source_coverage_score="1.000001")

    with pytest.raises(ValueError, match="inputs must not contain duplicate packet/question pairs"):
        report(packet("pkt-dupe", question_ref="q-dupe"), packet("pkt-dupe", question_ref="q-dupe"))

    item = packet("pkt-frozen")
    with pytest.raises(FrozenInstanceError):
        item.packet_ref = "pkt-edited"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        ranker.ResearchPacketCounterfactualEvidenceGapRankV2Config(readonly=False)


def test_ties_sort_deterministically_by_packet_and_question_ref() -> None:
    gap_report = report(
        packet("pkt-b", question_ref="q-2"),
        packet("pkt-a", question_ref="q-2"),
        packet("pkt-a", question_ref="q-1"),
    )

    assert tuple((row.packet_ref, row.question_ref, row.priority_rank) for row in gap_report.rows) == (
        ("pkt-a", "q-1", d("1")),
        ("pkt-a", "q-2", d("2")),
        ("pkt-b", "q-2", d("3")),
    )


def test_module_has_no_network_persistence_or_float_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_packet_evidence_counterfactual_gap_rank_v2.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "eth_account",
    }
    forbidden_calls = {
        "commit",
        "connect",
        "delete",
        "execute",
        "executemany",
        "open",
        "post",
        "put",
        "request",
        "send",
        "sign",
        "submit",
        "update",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
            assert node.func.id != "float"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_calls
