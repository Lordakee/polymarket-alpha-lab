from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_packet_official_resolution_evidence_gap_queue_v2 as api
from polymarket_alpha_lab.research_packet_official_resolution_evidence_gap_queue_v2 import (
    ResearchPacketOfficialResolutionEvidence,
    ResearchPacketOfficialResolutionEvidenceGapQueueConfig,
    ResearchPacketOfficialResolutionEvidenceGapQueueReport,
    ResearchPacketOfficialResolutionEvidenceGapQueueRow,
    ResearchPacketOfficialResolutionEvidencePublicPayloadItem,
    build_research_packet_official_resolution_evidence_gap_queue_v2_report,
    research_packet_official_resolution_evidence_gap_queue_v2_payload,
)


NOW = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def _evidence(
    *,
    packet_id: str = "packet_a",
    criterion_id: str = "criterion_a",
    source_id: str = "source_a",
    source_family: str = "official_source",
    source_role: str = "official",
    confidence_score: Decimal = Decimal("0.700000"),
    supports_resolution: bool = True,
    public_note: str | None = None,
) -> ResearchPacketOfficialResolutionEvidence:
    return ResearchPacketOfficialResolutionEvidence(
        packet_id=packet_id,
        criterion_id=criterion_id,
        source_id=source_id,
        source_family=source_family,
        source_role=source_role,
        observed_at=NOW,
        confidence_score=confidence_score,
        supports_resolution=supports_resolution,
        public_note=public_note,
    )


def _report(
    evidence: tuple[ResearchPacketOfficialResolutionEvidence, ...],
    *,
    config: ResearchPacketOfficialResolutionEvidenceGapQueueConfig | None = None,
    public_payload: tuple[ResearchPacketOfficialResolutionEvidencePublicPayloadItem, ...] = (),
) -> ResearchPacketOfficialResolutionEvidenceGapQueueReport:
    return build_research_packet_official_resolution_evidence_gap_queue_v2_report(
        evidence,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_official_resolution_evidence_gap_queue_scores_complete_rows() -> None:
    report = _report(
        (
            _evidence(source_id="source_a", source_family="official_source"),
            _evidence(
                source_id="source_b",
                source_family="public_record",
                source_role="corroborating",
            ),
        ),
    )

    row = report.rows[0]
    assert report.queue_status == "pass"
    assert report.packet_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.blocked_count == Decimal("0.000000")
    assert report.average_official_resolution_evidence_score == Decimal("0.800000")
    assert row.evidence_count == Decimal("2.000000")
    assert row.official_evidence_count == Decimal("1.000000")
    assert row.supporting_evidence_count == Decimal("2.000000")
    assert row.corroborating_family_count == Decimal("1.000000")
    assert row.missing_official_evidence_penalty == Decimal("0.000000")
    assert row.corroborated_evidence_boost == Decimal("0.100000")
    assert row.average_support_confidence_score == Decimal("0.700000")
    assert row.official_resolution_evidence_score == Decimal("0.800000")
    assert row.queue_status == "pass"
    assert row.reason_codes == (
        "official_resolution_evidence_observed",
        "corroborated_evidence_boost",
        "official_resolution_evidence_complete",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_missing_official_resolution_evidence_applies_penalty_and_blocks() -> None:
    report = _report(
        (
            _evidence(
                source_id="source_b",
                source_family="public_record",
                source_role="corroborating",
                confidence_score=Decimal("0.800000"),
            ),
            _evidence(
                source_id="source_c",
                source_family="agency_notice",
                source_role="corroborating",
                confidence_score=Decimal("0.800000"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.queue_status == "blocked"
    assert report.blocked_count == Decimal("1.000000")
    assert report.max_missing_official_evidence_penalty == Decimal("0.400000")
    assert row.official_evidence_count == Decimal("0.000000")
    assert row.corroborating_family_count == Decimal("2.000000")
    assert row.missing_official_evidence_penalty == Decimal("0.400000")
    assert row.corroborated_evidence_boost == Decimal("0.200000")
    assert row.average_support_confidence_score == Decimal("0.800000")
    assert row.official_resolution_evidence_score == Decimal("0.600000")
    assert row.queue_status == "blocked"
    assert row.reason_codes == (
        "missing_official_resolution_evidence",
        "corroborated_evidence_boost",
    )
    assert "missing_official_resolution_evidence" in report.reason_codes


def test_corroborated_evidence_boost_can_clear_watch_queue() -> None:
    official_only = _report(
        (
            _evidence(
                source_id="source_a",
                source_family="official_source",
                confidence_score=Decimal("0.600000"),
            ),
        ),
    )
    corroborated = _report(
        (
            _evidence(
                source_id="source_a",
                source_family="official_source",
                confidence_score=Decimal("0.600000"),
            ),
            _evidence(
                source_id="source_b",
                source_family="public_record",
                source_role="corroborating",
                confidence_score=Decimal("0.600000"),
            ),
        ),
    )

    official_row = official_only.rows[0]
    corroborated_row = corroborated.rows[0]
    assert official_row.queue_status == "watch"
    assert official_row.corroborated_evidence_boost == Decimal("0.000000")
    assert official_row.official_resolution_evidence_score == Decimal("0.600000")
    assert official_row.reason_codes == (
        "official_resolution_evidence_observed",
        "missing_corroborated_evidence",
        "evidence_score_watch",
    )
    assert corroborated_row.queue_status == "pass"
    assert corroborated_row.corroborated_evidence_boost == Decimal("0.100000")
    assert corroborated_row.official_resolution_evidence_score == Decimal("0.700000")
    assert corroborated_row.official_resolution_evidence_score > (
        official_row.official_resolution_evidence_score
    )
    assert "corroborated_evidence_boost" in corroborated_row.reason_codes


def test_payload_serializes_decimals_as_strings_and_is_json_ready() -> None:
    report = _report(
        (
            _evidence(source_id="source_a", source_family="official_source"),
            _evidence(
                source_id="source_b",
                source_family="public_record",
                source_role="corroborating",
            ),
        ),
        public_payload=(
            ResearchPacketOfficialResolutionEvidencePublicPayloadItem(
                "safe_key",
                "safe value",
            ),
        ),
    )

    payload = report.payload
    function_payload = research_packet_official_resolution_evidence_gap_queue_v2_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)
    assert function_payload == payload
    assert payload["packet_count"] == "1.000000"
    assert payload["average_official_resolution_evidence_score"] == "0.800000"
    assert payload["rows"][0]["evidence_count"] == "2.000000"
    assert payload["rows"][0]["corroborated_evidence_boost"] == "0.100000"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report(
        (
            _evidence(source_id="source_a", source_family="official_source"),
            _evidence(
                source_id="source_b",
                source_family="public_record",
                source_role="corroborating",
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.queue_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchPacketOfficialResolutionEvidenceGapQueueConfig):
            pass

    assert api.__all__ == (
        "DEFAULT_RESEARCH_PACKET_OFFICIAL_RESOLUTION_EVIDENCE_GAP_QUEUE_V2_CONFIG_VERSION",
        "ResearchPacketOfficialResolutionEvidence",
        "ResearchPacketOfficialResolutionEvidenceGapQueueConfig",
        "ResearchPacketOfficialResolutionEvidenceGapQueueReport",
        "ResearchPacketOfficialResolutionEvidenceGapQueueRow",
        "ResearchPacketOfficialResolutionEvidencePublicPayloadItem",
        "build_research_packet_official_resolution_evidence_gap_queue_v2_report",
        "research_packet_official_resolution_evidence_gap_queue_v2_payload",
    )


def test_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchPacketOfficialResolutionEvidenceGapQueueConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        ResearchPacketOfficialResolutionEvidence(
            packet_id="packet_a",
            criterion_id="criterion_a",
            source_id="source_a",
            source_family="official_source",
            source_role="official",
            observed_at=NOW,
            confidence_score=Decimal("0.700000"),
            report_only=False,
        )

    report = _report(
        (
            _evidence(source_id="source_a", source_family="official_source"),
            _evidence(
                source_id="source_b",
                source_family="public_record",
                source_role="corroborating",
            ),
        ),
    )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_derived_validation_digest_rejects_tampering() -> None:
    report = _report(
        (
            _evidence(source_id="source_a", source_family="official_source"),
            _evidence(
                source_id="source_b",
                source_family="public_record",
                source_role="corroborating",
            ),
        ),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchPacketOfficialResolutionEvidencePublicPayloadItem(
                    "safe_key",
                    "changed value",
                ),
            ),
        )

    with pytest.raises(ValueError, match="packet_count"):
        replace(report, packet_count=Decimal("2.000000"))


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    for key in (
        "live_key",
        "auth_key",
        "wallet_key",
        "order_key",
        "network_key",
        "database_key",
        "persist_key",
        "signing_key",
        "mutation_key",
        "buy_key",
        "sell_key",
        "trade_key",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchPacketOfficialResolutionEvidencePublicPayloadItem(key, "safe value")

    for value in (
        "live item",
        "auth item",
        "wallet item",
        "order item",
        "network item",
        "database item",
        "persist item",
        "signing item",
        "mutation item",
        "buy item",
        "sell item",
        "trade item",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchPacketOfficialResolutionEvidencePublicPayloadItem("safe_key", value)

    with pytest.raises(ValueError, match="unsafe public"):
        _evidence(source_id="buy_signal")

    with pytest.raises(ValueError, match="unsafe public"):
        _evidence(public_note="safe note about live item")


def test_rejects_invalid_inputs_and_no_evidence_report_state() -> None:
    empty = _report(())
    assert empty.queue_status == "blocked"
    assert empty.packet_count == Decimal("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("empty_evidence",)
    assert empty.average_official_resolution_evidence_score == Decimal("0.000000")

    row = _evidence(source_id="source_a")
    with pytest.raises(ValueError, match="ResearchPacketOfficialResolutionEvidenceGapQueueConfig"):
        build_research_packet_official_resolution_evidence_gap_queue_v2_report(
            (),
            generated_at=NOW,
            config=object(),
        )
    with pytest.raises(ValueError, match="evidence must be a sequence"):
        build_research_packet_official_resolution_evidence_gap_queue_v2_report(
            object(),
            generated_at=NOW,
        )
    with pytest.raises(ValueError, match="ResearchPacketOfficialResolutionEvidence"):
        build_research_packet_official_resolution_evidence_gap_queue_v2_report(
            (object(),),
            generated_at=NOW,
        )
    with pytest.raises(ValueError, match="unique"):
        _report((row, row))
    with pytest.raises(ValueError, match="after generated_at"):
        build_research_packet_official_resolution_evidence_gap_queue_v2_report(
            (
                ResearchPacketOfficialResolutionEvidence(
                    packet_id="packet_a",
                    criterion_id="criterion_a",
                    source_id="source_a",
                    source_family="official_source",
                    source_role="official",
                    observed_at=datetime(2026, 7, 6, 12, 1, tzinfo=UTC),
                    confidence_score=Decimal("0.700000"),
                ),
            ),
            generated_at=NOW,
        )
    with pytest.raises(ValueError, match="Decimal"):
        _evidence(confidence_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="known evidence role"):
        _evidence(source_role="unreviewed")
    with pytest.raises(ValueError, match="report"):
        research_packet_official_resolution_evidence_gap_queue_v2_payload(object())


def test_no_unsafe_surfaces_are_exposed() -> None:
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchPacketOfficialResolutionEvidence,
        ResearchPacketOfficialResolutionEvidenceGapQueueConfig,
        ResearchPacketOfficialResolutionEvidenceGapQueueReport,
        ResearchPacketOfficialResolutionEvidenceGapQueueRow,
        ResearchPacketOfficialResolutionEvidencePublicPayloadItem,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    source = Path(api.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "submit",
        "execute",
        "commit",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_call_names
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_call_names


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
