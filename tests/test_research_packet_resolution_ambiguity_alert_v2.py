from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_resolution_ambiguity_alert_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {"max_rule_text_age_seconds": d("3600.000000")}
    values.update(overrides)
    return module.ResearchPacketResolutionAmbiguityAlertV2Config(**values)


def event_packet(
    packet_id: str,
    *,
    market_slug: str | None = None,
    event_title: str | None = None,
    resolution_rule_text: str = "Resolve from final official committee bulletin.",
    observed_at: datetime = GENERATED_AT,
    official_anchor_refs: tuple[str, ...] = ("committee_bulletin",),
    source_families: tuple[str, ...] = ("official",),
    contradictory_source_families: tuple[str, ...] = (),
    edge_case_notes: tuple[str, ...] = (),
    settlement_evidence_risk_terms: tuple[str, ...] = (),
):
    module = api()
    return module.ResearchPacketResolutionAmbiguityEventPacket(
        packet_id=packet_id,
        market_slug=market_slug or f"market-{packet_id}",
        event_title=event_title or f"Event {packet_id}",
        resolution_rule_text=resolution_rule_text,
        rule_text_observed_at=observed_at,
        official_anchor_refs=official_anchor_refs,
        source_families=source_families,
        contradictory_source_families=contradictory_source_families,
        edge_case_notes=edge_case_notes,
        settlement_evidence_risk_terms=settlement_evidence_risk_terms,
    )


def report(
    event_packets,
    *,
    cfg=None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_packet_resolution_ambiguity_alert_v2_report(
        event_packets,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_report_flags_all_resolution_ambiguity_signals() -> None:
    ambiguity_report = report(
        (
            event_packet(
                "packet_blocked",
                resolution_rule_text=(
                    "Resolve if credible reports show a significant material outcome."
                ),
                observed_at=GENERATED_AT - timedelta(seconds=7201),
                official_anchor_refs=(),
                source_families=("primary", "proxy"),
                contradictory_source_families=("primary_vs_proxy",),
                edge_case_notes=("tie threshold not specified",),
                settlement_evidence_risk_terms=("unverified bulletin",),
            ),
            event_packet(
                "packet_stale",
                observed_at=GENERATED_AT - timedelta(seconds=7200),
            ),
            event_packet(
                "packet_clear",
                observed_at=GENERATED_AT - timedelta(seconds=60),
            ),
        ),
    )

    assert is_dataclass(ambiguity_report)
    assert ambiguity_report.generated_at == GENERATED_AT
    assert ambiguity_report.packet_count == d("3")
    assert ambiguity_report.alert_count == d("2")
    assert ambiguity_report.blocked_count == d("1")
    assert ambiguity_report.watch_count == d("1")
    assert ambiguity_report.clear_count == d("1")
    assert ambiguity_report.vague_trigger_packet_count == d("1")
    assert ambiguity_report.missing_official_anchor_packet_count == d("1")
    assert ambiguity_report.contradictory_source_family_packet_count == d("1")
    assert ambiguity_report.stale_rule_text_packet_count == d("2")
    assert ambiguity_report.edge_case_gap_packet_count == d("1")
    assert ambiguity_report.dispute_prone_settlement_evidence_packet_count == d("1")
    assert ambiguity_report.highest_ambiguity_score == d("1.000000")
    assert ambiguity_report.average_ambiguity_score == d("0.388889")
    assert ambiguity_report.status == "blocked"
    assert ambiguity_report.reason_codes == (
        "vague_trigger_terms_present",
        "missing_official_anchors_present",
        "contradictory_source_families_present",
        "stale_rule_text_present",
        "edge_case_gaps_present",
        "dispute_prone_settlement_evidence_present",
    )
    assert ambiguity_report.paper_only is True
    assert ambiguity_report.report_only is True
    assert ambiguity_report.readonly is True
    assert len(ambiguity_report.derived_validation_digest) == 64

    assert tuple(row.packet_id for row in ambiguity_report.rows) == (
        "packet_blocked",
        "packet_stale",
        "packet_clear",
    )
    blocked, stale, clear = ambiguity_report.rows
    assert blocked.alert_status == "blocked"
    assert blocked.ambiguity_score == d("1.000000")
    assert blocked.vague_trigger_term_count == d("3")
    assert blocked.official_anchor_count == d("0")
    assert blocked.source_family_count == d("2")
    assert blocked.contradictory_source_family_count == d("1")
    assert blocked.edge_case_gap_count == d("1")
    assert blocked.dispute_prone_settlement_evidence_count == d("1")
    assert blocked.reason_codes == (
        "vague_trigger_terms",
        "missing_official_anchor",
        "contradictory_source_families",
        "stale_rule_text",
        "edge_case_gap",
        "dispute_prone_settlement_evidence",
    )

    assert stale.alert_status == "watch"
    assert stale.rule_text_age_seconds == d("7200.000000")
    assert stale.reason_codes == ("stale_rule_text",)

    assert clear.alert_status == "clear"
    assert clear.rule_text_age_seconds == d("60.000000")
    assert clear.ambiguity_score == d("0.000000")
    assert clear.reason_codes == ("resolution_ambiguity_clear",)


def test_clear_report_payload_serializes_decimals_as_strings_and_verifies_digest() -> None:
    eastern = timezone(timedelta(hours=-4))
    clear_report = report(
        (
            event_packet(
                "packet_clear",
                observed_at=datetime(2026, 7, 2, 7, 59, tzinfo=eastern),
            ),
        ),
        generated_at=GENERATED_AT,
    )

    payload = api().research_packet_resolution_ambiguity_alert_v2_payload(clear_report)

    assert clear_report.generated_at.tzinfo is UTC
    assert clear_report.status == "clear"
    assert clear_report.reason_codes == ("resolution_ambiguity_report_clear",)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["packet_count"] == "1"
    assert payload["alert_count"] == "0"
    assert payload["average_ambiguity_score"] == "0.000000"
    assert payload["rows"][0]["rule_text_age_seconds"] == "60.000000"
    assert payload["derived_validation_digest"] == clear_report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)

    round_trip = api().research_packet_resolution_ambiguity_alert_v2_payload(payload)
    assert round_trip == payload

    tampered = dict(payload)
    tampered["alert_count"] = "1"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        api().research_packet_resolution_ambiguity_alert_v2_payload(tampered)


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_packet_resolution_ambiguity_alert_v2_payload(
            {
                "generated_at": "2026-07-02T12:00:00+00:00",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet": "redacted",
                "derived_validation_digest": "0" * 64,
            },
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        event_packet(
            "packet_unsafe",
            market_slug="market-safe",
            event_title="This value mentions wallet",
        )

    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_packet_resolution_ambiguity_alert_v2_payload(
            {
                "generated_at": "2026-07-02T12:00:00+00:00",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "note": "contains signing text",
                "derived_validation_digest": "0" * 64,
            },
        )


def test_validates_decimal_datetime_hard_flags_freezing_and_duplicates() -> None:
    module = api()

    with pytest.raises(ValueError, match="max_rule_text_age_seconds must be a Decimal"):
        config(max_rule_text_age_seconds=1)

    with pytest.raises(ValueError, match="rule_text_observed_at must be timezone-aware"):
        event_packet("packet_naive", observed_at=datetime(2026, 7, 2, 12, 0))

    row = event_packet("packet_frozen")
    with pytest.raises(FrozenInstanceError):
        row.packet_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(config(), readonly=False)

    with pytest.raises(ValueError, match="source_families must be one of"):
        event_packet("packet_bad_family", source_families=("secondary",))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(
            (event_packet("packet_clear"),),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="rule_text_observed_at must not be in the future"):
        report(
            (
                event_packet(
                    "packet_future",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )

    with pytest.raises(ValueError, match="packet_id values must be unique"):
        report((event_packet("packet_duplicate"), event_packet("packet_duplicate")))

    with pytest.raises(ValueError, match="config must be"):
        module.build_research_packet_resolution_ambiguity_alert_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_manual_report_rejects_derived_validation_digest_tampering() -> None:
    clear_report = report((event_packet("packet_clear"),))

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(clear_report, alert_count=d("1"))

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(clear_report, derived_validation_digest="f" * 64)


def test_empty_packet_report_is_blocked_without_numeric_int_payloads() -> None:
    empty_report = report(())

    assert empty_report.packet_count == d("0")
    assert empty_report.alert_count == d("0")
    assert empty_report.status == "blocked"
    assert empty_report.reason_codes == ("no_event_packets",)

    payload = api().research_packet_resolution_ambiguity_alert_v2_payload(empty_report)
    assert payload["packet_count"] == "0"
    assert payload["highest_ambiguity_score"] == "0.000000"
    assert payload["rows"] == []
    assert_no_float(payload)


def test_module_scope_is_pure_in_memory_report_only() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "research_packet_resolution_ambiguity_alert_v2.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for token in (
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "clob",
        "private_key",
        "mnemonic",
        "subprocess",
        "open(",
        ".write(",
        ".read(",
    ):
        assert token not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
