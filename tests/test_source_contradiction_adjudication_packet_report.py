from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from pathlib import Path

import pytest

import polymarket_alpha_lab.source_contradiction_adjudication_packet_report as api
from polymarket_alpha_lab.source_contradiction_adjudication_packet_report import (
    SourceContradictionAdjudicationPacketInput,
    SourceContradictionAdjudicationPacketReport,
    build_source_contradiction_adjudication_packet_report,
    source_contradiction_adjudication_packet_report_to_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/source_contradiction_adjudication_packet_report.py",
)


def packet_input(
    *,
    contradiction_count: int = 0,
    unresolved_contradiction_count: int = 0,
    official_source_position: str = "supports_yes",
    independent_source_positions: tuple[str, ...] = ("supports_yes",),
    adjudication_note_present: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SourceContradictionAdjudicationPacketInput:
    return SourceContradictionAdjudicationPacketInput(
        contradiction_count=contradiction_count,
        unresolved_contradiction_count=unresolved_contradiction_count,
        official_source_position=official_source_position,
        independent_source_positions=independent_source_positions,
        adjudication_note_present=adjudication_note_present,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    packet: SourceContradictionAdjudicationPacketInput,
) -> SourceContradictionAdjudicationPacketReport:
    return build_source_contradiction_adjudication_packet_report(packet)


def test_no_contradictions_passes_as_readonly_adjudication_packet() -> None:
    result = report(packet_input())

    assert is_dataclass(result)
    assert result.adjudication_status == "pass"
    assert result.reason_codes == ("source_contradiction_adjudication_pass",)
    assert result.manual_next_step == "proceed_with_documented_source_packet"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = source_contradiction_adjudication_packet_report_to_payload(result)
    assert payload == {
        "adjudication_status": "pass",
        "reason_codes": ["source_contradiction_adjudication_pass"],
        "manual_next_step": "proceed_with_documented_source_packet",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def test_resolved_contradictions_watch_and_require_manual_documentation() -> None:
    result = report(
        packet_input(
            contradiction_count=2,
            unresolved_contradiction_count=0,
            official_source_position="supports_yes",
            independent_source_positions=("supports_no", "supports_yes"),
            adjudication_note_present=True,
        ),
    )

    assert result.adjudication_status == "watch"
    assert result.reason_codes == (
        "source_contradiction_detected",
        "source_positions_diverge",
        "source_contradiction_adjudication_note_present",
    )
    assert result.manual_next_step == "review_documented_adjudication_before_packet_use"


def test_unresolved_contradictions_block_even_when_note_is_present() -> None:
    result = report(
        packet_input(
            contradiction_count=3,
            unresolved_contradiction_count=1,
            official_source_position="supports_yes",
            independent_source_positions=("supports_no", "supports_no"),
            adjudication_note_present=True,
        ),
    )

    assert result.adjudication_status == "block"
    assert "source_contradiction_unresolved" in result.reason_codes
    assert result.manual_next_step == "resolve_source_contradictions_before_packet_use"


def test_missing_adjudication_note_blocks_contradicted_packets() -> None:
    result = report(
        packet_input(
            contradiction_count=1,
            unresolved_contradiction_count=0,
            official_source_position="supports_yes",
            independent_source_positions=("supports_no",),
            adjudication_note_present=False,
        ),
    )

    assert result.adjudication_status == "block"
    assert result.reason_codes == (
        "source_contradiction_detected",
        "source_positions_diverge",
        "source_contradiction_adjudication_note_missing",
    )
    assert result.manual_next_step == "add_manual_adjudication_note_before_packet_use"


def test_unknown_positions_block_for_manual_source_review() -> None:
    result = report(
        packet_input(
            contradiction_count=0,
            unresolved_contradiction_count=0,
            official_source_position="unknown",
            independent_source_positions=("supports_yes", "unknown"),
            adjudication_note_present=True,
        ),
    )

    assert result.adjudication_status == "block"
    assert result.reason_codes == (
        "source_position_unknown",
        "source_positions_diverge",
    )
    assert result.manual_next_step == "clarify_source_positions_before_packet_use"


def test_public_dataclasses_are_frozen_and_flags_are_enforced() -> None:
    result = report(packet_input())

    with pytest.raises(FrozenInstanceError):
        result.adjudication_status = "block"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(SourceContradictionAdjudicationPacketInput):
            pass

    with pytest.raises(ValueError, match="contradiction_count"):
        packet_input(contradiction_count=-1)

    with pytest.raises(ValueError, match="unresolved_contradiction_count"):
        packet_input(contradiction_count=1, unresolved_contradiction_count=2)

    with pytest.raises(ValueError, match="official_source_position"):
        packet_input(official_source_position="supports maybe")

    with pytest.raises(ValueError, match="independent_source_positions"):
        packet_input(independent_source_positions=())

    with pytest.raises(ValueError, match="paper_only"):
        packet_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        packet_input(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_report_rejects_inconsistent_pass_and_reason_code_state() -> None:
    with pytest.raises(ValueError, match="unresolved"):
        SourceContradictionAdjudicationPacketReport(
            adjudication_status="pass",
            reason_codes=("source_contradiction_unresolved",),
            manual_next_step="proceed_with_documented_source_packet",
        )

    with pytest.raises(ValueError, match="reason_codes"):
        SourceContradictionAdjudicationPacketReport(
            adjudication_status="pass",
            reason_codes=("source_contradiction_detected",),
            manual_next_step="proceed_with_documented_source_packet",
        )

    with pytest.raises(ValueError, match="manual_next_step"):
        SourceContradictionAdjudicationPacketReport(
            adjudication_status="block",
            reason_codes=("source_contradiction_unresolved",),
            manual_next_step="proceed_with_documented_source_packet",
        )


def test_public_api_excludes_persistence_live_auth_wallet_and_order_surfaces() -> None:
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "database",
        "persist",
        "store",
        "order",
        "trade",
        "request",
        "http",
        "broker",
        "private_key",
        "api_key",
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)

    for cls in (
        SourceContradictionAdjudicationPacketInput,
        SourceContradictionAdjudicationPacketReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
        "subprocess",
    ):
        assert not hasattr(api, forbidden_name)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "web3",
            "ccxt",
            "subprocess",
            "pathlib",
        },
    )
