from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime

import pytest

from polymarket_alpha_lab.research_manual_execution_boundary_guard import (
    ResearchManualExecutionBoundaryGuardPacket,
    ResearchManualExecutionBoundaryGuardReport,
    ResearchManualExecutionBoundaryGuardRow,
    build_research_manual_execution_boundary_guard_report,
    research_manual_execution_boundary_guard_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def packet(
    packet_key: str = "candidate-alpha-market-123",
    body: object | None = None,
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchManualExecutionBoundaryGuardPacket:
    return ResearchManualExecutionBoundaryGuardPacket(
        packet_key=packet_key,
        body=body
        if body is not None
        else {
            "summary": "Probability evidence is internally consistent.",
            "signal_quality": "high",
            "confidence_band": "0.60 to 0.66",
        },
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *packets: ResearchManualExecutionBoundaryGuardPacket,
) -> ResearchManualExecutionBoundaryGuardReport:
    return build_research_manual_execution_boundary_guard_report(
        packets,
        generated_at=GENERATED_AT,
    )


def test_safe_packet_passes_with_report_only_payload() -> None:
    guard = report(packet())

    assert is_dataclass(guard)
    assert guard.status == "pass"
    assert guard.pass_count == 1
    assert guard.watch_count == 0
    assert guard.block_count == 0
    assert guard.reason_codes == ("boundary_clear",)
    assert guard.paper_only is True
    assert guard.report_only is True
    assert guard.readonly is True

    row = guard.rows[0]
    assert row.status == "pass"
    assert row.item_key.startswith("item_")
    assert row.finding_count == 0
    assert row.reason_codes == ("boundary_clear",)

    payload = research_manual_execution_boundary_guard_payload(guard)
    assert payload["status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json_payload = json.dumps(payload, sort_keys=True)
    assert "candidate-alpha-market-123" not in json_payload
    assert "candidate" not in json_payload.lower()
    assert "market" not in json_payload.lower()
    assert "question" not in json_payload.lower()
    assert "source" not in json_payload.lower()


def test_suspicious_human_handoff_terms_watch_without_leaking_text() -> None:
    guard = report(
        packet(
            body={
                "summary": "Evidence is strong.",
                "handoff_note": "Manual review requested before publication.",
            },
        ),
    )

    assert guard.status == "watch"
    assert guard.watch_count == 1
    assert guard.block_count == 0
    assert guard.rows[0].status == "watch"
    assert guard.rows[0].reason_codes == ("human_boundary_watch",)

    payload_text = json.dumps(
        research_manual_execution_boundary_guard_payload(guard),
        sort_keys=True,
    ).lower()
    assert "manual review requested" not in payload_text
    assert "handoff_note" not in payload_text


def test_execution_and_identifier_leakage_blocks_but_redacts_payload() -> None:
    guard = report(
        packet(
            body={
                "market_slug": "will-candidate-alpha-win",
                "question": "Will Candidate Alpha win?",
                "wallet": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "instruction": "Recommend buy YES, then sell after the trade fills.",
                "position_size": "100 shares",
                "order_payload": {"side": "buy"},
                "source_url": "https://example.invalid/report",
                "table_name": "paper_trade_orders",
            },
        ),
    )

    assert guard.status == "block"
    assert guard.block_count == 1
    assert guard.rows[0].status == "block"
    assert guard.rows[0].reason_codes == (
        "credential_leak_block",
        "intent_language_block",
        "raw_context_block",
    )

    payload_text = json.dumps(
        research_manual_execution_boundary_guard_payload(guard),
        sort_keys=True,
    ).lower()
    for unsafe in (
        "candidate",
        "market",
        "slug",
        "question",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "source",
        "url",
        "table",
    ):
        assert unsafe not in payload_text


def test_type_rejections_and_public_status_boundaries() -> None:
    with pytest.raises(ValueError, match="packet_key must be a string"):
        ResearchManualExecutionBoundaryGuardPacket(packet_key=123, body={})  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        packet(body={"confidence": 0.72})

    with pytest.raises(ValueError, match="packets must be a tuple"):
        build_research_manual_execution_boundary_guard_report(  # type: ignore[arg-type]
            [packet()],
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        ResearchManualExecutionBoundaryGuardRow(
            item_key="item_abcdef1234567890",
            status="hold",
            finding_count=0,
            reason_codes=("boundary_clear",),
        )

    with pytest.raises(FrozenInstanceError):
        guard = report(packet())
        guard.status = "watch"  # type: ignore[misc]


def test_hard_flags_are_required_on_inputs_reports_and_payloads() -> None:
    with pytest.raises(ValueError, match="readonly must be True"):
        packet(readonly=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        ResearchManualExecutionBoundaryGuardReport(
            generated_at=GENERATED_AT,
            item_count=0,
            pass_count=0,
            watch_count=0,
            block_count=0,
            status="pass",
            reason_codes=("boundary_clear",),
            rows=(),
            paper_only=False,
        )

    with pytest.raises(ValueError, match="report_only must be True"):
        research_manual_execution_boundary_guard_payload(
            {
                "generated_at": GENERATED_AT.isoformat(),
                "status": "pass",
                "paper_only": True,
                "report_only": False,
                "readonly": True,
            },
        )


def test_payload_output_is_deterministic_and_redacted() -> None:
    first = research_manual_execution_boundary_guard_payload(
        report(
            packet("candidate-z", {"summary": "Consistent evidence."}),
            packet("candidate-a", {"handoff_note": "Manual review requested."}),
        ),
    )
    second = research_manual_execution_boundary_guard_payload(
        report(
            packet("candidate-a", {"handoff_note": "Manual review requested."}),
            packet("candidate-z", {"summary": "Consistent evidence."}),
        ),
    )

    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
