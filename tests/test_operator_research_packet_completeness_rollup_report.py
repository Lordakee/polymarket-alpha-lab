from __future__ import annotations

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from polymarket_alpha_lab.operator_research_packet_completeness_rollup_report import (
    OperatorResearchPacketCompletenessRollupInput,
    build_operator_research_packet_completeness_rollup_report,
    operator_research_packet_completeness_rollup_payload,
    operator_research_packet_completeness_rollup_payload_digest,
)


def test_builds_complete_research_packet_rollup_payload_and_digest() -> None:
    report = build_operator_research_packet_completeness_rollup_report(
        OperatorResearchPacketCompletenessRollupInput(
            packet_count=Decimal("4"),
            complete_packet_count=Decimal("4"),
            missing_source_packet_count=Decimal("0"),
            missing_cost_packet_count=Decimal("0"),
            missing_memory_packet_count=Decimal("0"),
        ),
    )

    assert report.completeness_status == "complete"
    assert report.reason_codes == ("research_packet_completeness_rollup_complete",)
    assert report.manual_next_step == "continue_manual_research_review"
    assert report.packet_count == Decimal("4.000000")
    assert report.complete_packet_count == Decimal("4.000000")
    assert report.incomplete_packet_count == Decimal("0.000000")
    assert report.completeness_ratio == Decimal("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.completeness_status = "blocked"  # type: ignore[misc]

    payload = operator_research_packet_completeness_rollup_payload(report)

    assert payload["completeness_status"] == "complete"
    assert payload["reason_codes"] == [
        "research_packet_completeness_rollup_complete",
    ]
    assert payload["manual_next_step"] == "continue_manual_research_review"
    assert payload["packet_count"] == "4.000000"
    assert payload["complete_packet_count"] == "4.000000"
    assert payload["incomplete_packet_count"] == "0.000000"
    assert payload["completeness_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "wallet" not in str(payload).lower()
    assert "auth" not in str(payload).lower()
    assert "sign" not in str(payload).lower()
    assert "execution" not in str(payload).lower()
    assert operator_research_packet_completeness_rollup_payload_digest(report) == (
        report.payload_digest
    )
    assert payload["payload_digest"] == report.payload_digest


def test_reports_missing_source_cost_and_memory_reason_codes() -> None:
    report = build_operator_research_packet_completeness_rollup_report(
        OperatorResearchPacketCompletenessRollupInput(
            packet_count=Decimal("5"),
            complete_packet_count=Decimal("2"),
            missing_source_packet_count=Decimal("1"),
            missing_cost_packet_count=Decimal("2"),
            missing_memory_packet_count=Decimal("3"),
        ),
    )

    assert report.completeness_status == "incomplete"
    assert report.reason_codes == (
        "research_packet_source_missing",
        "research_packet_cost_missing",
        "research_packet_memory_missing",
        "research_packet_rollup_incomplete",
    )
    assert report.manual_next_step == "manually_complete_missing_research_packet_fields"
    assert report.incomplete_packet_count == Decimal("3.000000")
    assert report.completeness_ratio == Decimal("0.400000")


def test_reports_empty_rollup_without_treating_it_as_complete() -> None:
    report = build_operator_research_packet_completeness_rollup_report(
        OperatorResearchPacketCompletenessRollupInput(
            packet_count=Decimal("0"),
            complete_packet_count=Decimal("0"),
            missing_source_packet_count=Decimal("0"),
            missing_cost_packet_count=Decimal("0"),
            missing_memory_packet_count=Decimal("0"),
        ),
    )

    assert report.completeness_status == "empty"
    assert report.reason_codes == ("research_packet_rollup_empty",)
    assert report.manual_next_step == "manually_collect_research_packets"
    assert report.completeness_ratio == Decimal("0.000000")


def test_rejects_non_decimal_counts_inconsistent_counts_and_non_readonly_flags() -> None:
    with pytest.raises(ValueError, match="packet_count must be a Decimal"):
        OperatorResearchPacketCompletenessRollupInput(
            packet_count=4,  # type: ignore[arg-type]
            complete_packet_count=Decimal("4"),
            missing_source_packet_count=Decimal("0"),
            missing_cost_packet_count=Decimal("0"),
            missing_memory_packet_count=Decimal("0"),
        )

    with pytest.raises(ValueError, match="complete_packet_count cannot exceed packet_count"):
        OperatorResearchPacketCompletenessRollupInput(
            packet_count=Decimal("1"),
            complete_packet_count=Decimal("2"),
            missing_source_packet_count=Decimal("0"),
            missing_cost_packet_count=Decimal("0"),
            missing_memory_packet_count=Decimal("0"),
        )

    with pytest.raises(ValueError, match="readonly must be True"):
        OperatorResearchPacketCompletenessRollupInput(
            packet_count=Decimal("1"),
            complete_packet_count=Decimal("1"),
            missing_source_packet_count=Decimal("0"),
            missing_cost_packet_count=Decimal("0"),
            missing_memory_packet_count=Decimal("0"),
            readonly=False,
        )


def test_public_payload_tamper_detection_and_no_unsafe_public_surface() -> None:
    report = build_operator_research_packet_completeness_rollup_report(
        OperatorResearchPacketCompletenessRollupInput(
            packet_count=Decimal("3"),
            complete_packet_count=Decimal("2"),
            missing_source_packet_count=Decimal("1"),
            missing_cost_packet_count=Decimal("0"),
            missing_memory_packet_count=Decimal("0"),
        ),
    )
    bad_report = type(report)(
        config_version=report.config_version,
        completeness_status=report.completeness_status,
        reason_codes=report.reason_codes,
        manual_next_step=report.manual_next_step,
        packet_count=report.packet_count,
        complete_packet_count=report.complete_packet_count,
        missing_source_packet_count=report.missing_source_packet_count,
        missing_cost_packet_count=report.missing_cost_packet_count,
        missing_memory_packet_count=report.missing_memory_packet_count,
        incomplete_packet_count=report.incomplete_packet_count,
        completeness_ratio=report.completeness_ratio,
        payload_digest="tampered",
    )

    with pytest.raises(ValueError, match="payload_digest does not match report payload"):
        operator_research_packet_completeness_rollup_payload(bad_report)

    public_payload_text = str(operator_research_packet_completeness_rollup_payload(report)).lower()
    for unsafe_fragment in (
        "live",
        "wallet",
        "auth",
        "key",
        "signing",
        "execution",
        "jsonl",
    ):
        assert unsafe_fragment not in public_payload_text
