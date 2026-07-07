from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab.research_packet_resolution_outcome_recheck_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def gate_input(**overrides: object) -> Any:
    module = api()
    values = {
        "packet_id": "packet-alpha",
        "market_id": "market-alpha",
        "event_slug": "event-alpha",
        "category": "politics",
        "market_closed_at": GENERATED_AT - timedelta(hours=2),
        "outcome_source_checked_at": GENERATED_AT - timedelta(minutes=5),
        "official_outcome_source_count": d("1.000000"),
        "conflicting_outcome_source_count": d("0.000000"),
        "unresolved_dispute_count": d("0.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchPacketResolutionOutcomeRecheckGateV2Input(**values)


def report(rows: list[object] | tuple[object, ...]) -> Any:
    module = api()
    return module.build_research_packet_resolution_outcome_recheck_gate_v2_report(
        rows,
        generated_at=GENERATED_AT,
    )


def test_report_sorts_rows_and_rolls_up_pass_watch_and_block_statuses() -> None:
    module = api()
    blocked = gate_input(
        packet_id="packet-block",
        market_id="market-block",
        event_slug="event-z",
        category="sports",
        market_closed_at=GENERATED_AT - timedelta(hours=26),
        outcome_source_checked_at=None,
        official_outcome_source_count=d("0.000000"),
    )
    passed = gate_input(
        packet_id="packet-pass",
        market_id="market-pass",
        event_slug="event-a",
        category="politics",
    )
    watched = gate_input(
        packet_id="packet-watch",
        market_id="market-watch",
        event_slug="event-m",
        category="economics",
        market_closed_at=GENERATED_AT - timedelta(hours=5),
        outcome_source_checked_at=GENERATED_AT - timedelta(hours=4),
        official_outcome_source_count=d("1.000000"),
        conflicting_outcome_source_count=d("1.000000"),
    )

    gate_report = report([passed, watched, blocked])
    repeated_report = report([blocked, passed, watched])

    assert type(gate_report) is module.ResearchPacketResolutionOutcomeRecheckGateV2Report
    assert is_dataclass(gate_report)
    assert gate_report.generated_at == GENERATED_AT
    assert gate_report.config_version == (
        module.DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_RECHECK_GATE_V2_CONFIG_VERSION
    )
    assert gate_report.report_status == "block"
    assert gate_report.packet_count == d("3.000000")
    assert gate_report.pass_count == d("1.000000")
    assert gate_report.watch_count == d("1.000000")
    assert gate_report.block_count == d("1.000000")
    assert gate_report.missing_outcome_check_count == d("1.000000")
    assert gate_report.conflict_count == d("1.000000")
    assert gate_report.unresolved_dispute_count == d("0.000000")
    assert gate_report.max_close_age_seconds == d("93600.000000")
    assert [row.packet_id for row in gate_report.rows] == [
        "packet-block",
        "packet-watch",
        "packet-pass",
    ]
    assert gate_report.rows[0].status == "block"
    assert gate_report.rows[0].close_age_seconds == d("93600.000000")
    assert gate_report.rows[0].outcome_check_age_seconds is None
    assert gate_report.rows[0].reason_codes == (
        "outcome_recheck_gate_block",
        "missing_outcome_source_check",
        "missing_official_outcome_source",
    )
    assert gate_report.rows[1].status == "watch"
    assert gate_report.rows[1].close_age_seconds == d("18000.000000")
    assert gate_report.rows[1].outcome_check_age_seconds == d("14400.000000")
    assert gate_report.rows[1].reason_codes == (
        "outcome_recheck_gate_watch",
        "conflicting_outcome_sources_present",
    )
    assert gate_report.rows[2].status == "pass"
    assert gate_report.rows[2].reason_codes == ("outcome_recheck_gate_pass",)
    assert gate_report.reason_code_counts == (
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="conflicting_outcome_sources_present",
            row_count=d("1.000000"),
        ),
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="missing_official_outcome_source",
            row_count=d("1.000000"),
        ),
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="missing_outcome_source_check",
            row_count=d("1.000000"),
        ),
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="outcome_recheck_gate_block",
            row_count=d("1.000000"),
        ),
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="outcome_recheck_gate_pass",
            row_count=d("1.000000"),
        ),
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="outcome_recheck_gate_watch",
            row_count=d("1.000000"),
        ),
    )
    assert gate_report.derived_validation_digest == repeated_report.derived_validation_digest
    assert len(gate_report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in gate_report.derived_validation_digest
    )
    assert gate_report.paper_only is True
    assert gate_report.report_only is True
    assert gate_report.readonly is True


def test_empty_input_returns_empty_status_and_zero_decimal_rollups() -> None:
    module = api()

    gate_report = report([])

    assert gate_report.report_status == "empty"
    assert gate_report.rows == ()
    assert gate_report.packet_count == d("0.000000")
    assert gate_report.pass_count == d("0.000000")
    assert gate_report.watch_count == d("0.000000")
    assert gate_report.block_count == d("0.000000")
    assert gate_report.missing_outcome_check_count == d("0.000000")
    assert gate_report.conflict_count == d("0.000000")
    assert gate_report.unresolved_dispute_count == d("0.000000")
    assert gate_report.max_close_age_seconds == d("0.000000")
    assert gate_report.reason_code_counts == (
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="outcome_recheck_gate_empty",
            row_count=d("0.000000"),
        ),
    )


def test_unresolved_disputes_block_and_payload_is_json_safe_decimal_only() -> None:
    module = api()
    gate_report = report(
        [
            gate_input(
                packet_id="packet-dispute",
                market_id="market-dispute",
                unresolved_dispute_count=d("2.000000"),
            ),
        ],
    )

    assert gate_report.report_status == "block"
    assert gate_report.block_count == d("1.000000")
    assert gate_report.unresolved_dispute_count == d("1.000000")
    assert gate_report.rows[0].reason_codes == (
        "outcome_recheck_gate_block",
        "unresolved_disputes_present",
    )

    payload = module.research_packet_resolution_outcome_recheck_gate_v2_payload(gate_report)
    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["packet_count"] == "1.000000"
    assert payload["rows"][0]["close_age_seconds"] == "7200.000000"
    assert payload["rows"][0]["outcome_check_age_seconds"] == "300.000000"
    assert payload["reason_code_counts"][0]["row_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _contains_float(payload)

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["packet_count"] = "9.000000"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]


def test_blocked_rows_keep_conflict_reason_detail_for_public_rollups() -> None:
    module = api()
    gate_report = report(
        [
            gate_input(
                packet_id="packet-block-conflict",
                market_id="market-block-conflict",
                outcome_source_checked_at=None,
                official_outcome_source_count=d("0.000000"),
                conflicting_outcome_source_count=d("2.000000"),
                unresolved_dispute_count=d("1.000000"),
            ),
        ],
    )

    assert gate_report.report_status == "block"
    assert gate_report.conflict_count == d("1.000000")
    assert gate_report.unresolved_dispute_count == d("1.000000")
    assert gate_report.rows[0].reason_codes == (
        "outcome_recheck_gate_block",
        "missing_outcome_source_check",
        "missing_official_outcome_source",
        "conflicting_outcome_sources_present",
        "unresolved_disputes_present",
    )
    assert gate_report.reason_code_counts == (
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="conflicting_outcome_sources_present",
            row_count=d("1.000000"),
        ),
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="missing_official_outcome_source",
            row_count=d("1.000000"),
        ),
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="missing_outcome_source_check",
            row_count=d("1.000000"),
        ),
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="outcome_recheck_gate_block",
            row_count=d("1.000000"),
        ),
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="unresolved_disputes_present",
            row_count=d("1.000000"),
        ),
    )


def test_validation_is_strict_frozen_digest_backed_and_paper_only() -> None:
    module = api()
    row = gate_input()
    other_row = gate_input(
        packet_id="packet-beta",
        market_id="market-beta",
        event_slug="event-beta",
    )
    gate_report = report([row, other_row])

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_RECHECK_GATE_V2_CONFIG_VERSION",
        "ResearchPacketResolutionOutcomeRecheckGateV2Input",
        "ResearchPacketResolutionOutcomeRecheckGateV2Row",
        "ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount",
        "ResearchPacketResolutionOutcomeRecheckGateV2Report",
        "build_research_packet_resolution_outcome_recheck_gate_v2_report",
        "research_packet_resolution_outcome_recheck_gate_v2_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    with pytest.raises(FrozenInstanceError):
        row.packet_id = "packet-mutated"  # type: ignore[misc]
    with pytest.raises(ValueError, match="packet_id"):
        gate_input(packet_id=_StringSubclass("packet-alpha"))
    with pytest.raises(ValueError, match="official_outcome_source_count"):
        gate_input(official_outcome_source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="conflicting_outcome_source_count"):
        gate_input(conflicting_outcome_source_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="unresolved_dispute_count"):
        gate_input(unresolved_dispute_count=d("0.500000"))
    with pytest.raises(ValueError, match="row_count"):
        module.ResearchPacketResolutionOutcomeRecheckGateV2ReasonCodeCount(
            reason_code="outcome_recheck_gate_pass",
            row_count=d("0.500000"),
        )
    with pytest.raises(ValueError, match="market_closed_at"):
        gate_input(market_closed_at=datetime(2026, 7, 7, 10, 0))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_packet_resolution_outcome_recheck_gate_v2_report(
            [row],
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="market_closed_at"):
        report([gate_input(market_closed_at=GENERATED_AT + timedelta(seconds=1))])
    with pytest.raises(ValueError, match="outcome_source_checked_at"):
        report([gate_input(outcome_source_checked_at=GENERATED_AT + timedelta(seconds=1))])
    with pytest.raises(ValueError, match="outcome_source_checked_at"):
        report(
            [
                gate_input(
                    market_closed_at=GENERATED_AT - timedelta(hours=1),
                    outcome_source_checked_at=GENERATED_AT - timedelta(hours=2),
                ),
            ],
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(gate_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(gate_report, derived_validation_digest="0" * 64)
    blocked_row = report(
        [
            gate_input(
                packet_id="packet-row-validation",
                market_id="market-row-validation",
                outcome_source_checked_at=None,
                official_outcome_source_count=d("0.000000"),
                conflicting_outcome_source_count=d("1.000000"),
                unresolved_dispute_count=d("1.000000"),
            ),
        ],
    ).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            blocked_row,
            reason_codes=(
                "outcome_recheck_gate_block",
                "unresolved_disputes_present",
                "conflicting_outcome_sources_present",
                "missing_official_outcome_source",
                "missing_outcome_source_check",
            ),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            blocked_row,
            reason_codes=(
                "outcome_recheck_gate_block",
                "missing_outcome_source_check",
                "missing_official_outcome_source",
                "unresolved_disputes_present",
            ),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="rows"):
        module.ResearchPacketResolutionOutcomeRecheckGateV2Report(
            generated_at=gate_report.generated_at,
            config_version=gate_report.config_version,
            report_status=gate_report.report_status,
            packet_count=gate_report.packet_count,
            pass_count=gate_report.pass_count,
            watch_count=gate_report.watch_count,
            block_count=gate_report.block_count,
            missing_outcome_check_count=gate_report.missing_outcome_check_count,
            conflict_count=gate_report.conflict_count,
            unresolved_dispute_count=gate_report.unresolved_dispute_count,
            max_close_age_seconds=gate_report.max_close_age_seconds,
            rows=list(reversed(gate_report.rows)),
            reason_code_counts=gate_report.reason_code_counts,
            derived_validation_digest=gate_report.derived_validation_digest,
        )


def test_source_file_exposes_no_live_capability_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_packet_resolution_outcome_recheck_gate_v2.py"
    )
    tree = ast.parse(source_path.read_text())
    banned_fragments = (
        "network",
        "socket",
        "requests",
        "http",
        "auth",
        "wallet",
        "account",
        "broker",
        "trade",
        "trading",
        "order",
        "database",
        "db",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in banned_fragments)
        if isinstance(node, ast.arg):
            lowered = node.arg.lower()
            assert not any(fragment in lowered for fragment in banned_fragments)


def _contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False
