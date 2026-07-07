from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_packet_source_collection_checklist_v2 as api
from polymarket_alpha_lab.research_packet_source_collection_checklist_v2 import (
    RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CHECKS,
    ResearchPacketSourceCollectionChecklistConfig,
    ResearchPacketSourceCollectionChecklistEvidence,
    ResearchPacketSourceCollectionChecklistPublicPayloadItem,
    ResearchPacketSourceCollectionChecklistReport,
    ResearchPacketSourceCollectionChecklistRow,
    build_research_packet_source_collection_checklist_v2_report,
)


NOW = datetime(2026, 2, 1, 12, 0, tzinfo=UTC)


def _evidence(
    source_type: str,
    *,
    packet_id: str = "packet_a",
    claim_id: str = "claim_a",
    source_id: str | None = None,
    source_family: str | None = None,
    observed_at: datetime | None = None,
) -> ResearchPacketSourceCollectionChecklistEvidence:
    return ResearchPacketSourceCollectionChecklistEvidence(
        packet_id=packet_id,
        claim_id=claim_id,
        source_id=source_id or f"{source_type}_a",
        source_type=source_type,
        source_family=source_family or source_type,
        observed_at=observed_at or NOW - timedelta(minutes=15),
    )


def _complete_sources(
    *,
    observed_at: datetime | None = None,
) -> tuple[ResearchPacketSourceCollectionChecklistEvidence, ...]:
    return (
        _evidence("official_source", observed_at=observed_at),
        _evidence("primary_source", observed_at=observed_at),
        _evidence("independent_corroboration", observed_at=observed_at),
        _evidence("contradiction_follow_up", observed_at=observed_at),
        _evidence("market_move_explanation", observed_at=observed_at),
        _evidence("resolution_rule_source", observed_at=observed_at),
    )


def _report(
    evidence: tuple[ResearchPacketSourceCollectionChecklistEvidence, ...],
    *,
    config: ResearchPacketSourceCollectionChecklistConfig | None = None,
    public_payload: tuple[ResearchPacketSourceCollectionChecklistPublicPayloadItem, ...] = (),
) -> ResearchPacketSourceCollectionChecklistReport:
    return build_research_packet_source_collection_checklist_v2_report(
        evidence,
        generated_at=NOW,
        config=config,
        public_payload=public_payload,
    )


def test_complete_phase_1_collection_passes_and_reports_all_checklist_items() -> None:
    report = _report(_complete_sources())

    row = report.rows[0]
    assert report.checklist_status == "pass"
    assert report.packet_count == Decimal("1.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.blocked_count == Decimal("0.000000")
    assert report.average_completion_score == Decimal("1.000000")
    assert report.reason_codes == ("source_collection_pass",)
    assert row.packet_id == "packet_a"
    assert row.claim_id == "claim_a"
    assert row.source_count == Decimal("6.000000")
    assert row.required_check_count == Decimal("7.000000")
    assert row.satisfied_check_count == Decimal("7.000000")
    assert row.completion_score == Decimal("1.000000")
    assert row.latest_source_age_minutes == Decimal("15.000000")
    assert row.stale_source_count == Decimal("0.000000")
    assert row.official_source_present is True
    assert row.primary_source_present is True
    assert row.independent_corroboration_present is True
    assert row.contradiction_follow_up_present is True
    assert row.market_move_explanation_present is True
    assert row.resolution_rule_source_present is True
    assert row.timestamp_fresh is True
    assert row.satisfied_checks == RESEARCH_PACKET_SOURCE_COLLECTION_CHECKLIST_V2_CHECKS
    assert row.missing_checks == ()
    assert row.checklist_status == "pass"
    assert row.reason_codes == ("source_collection_pass",)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_missing_required_sources_block_with_deterministic_missing_checks() -> None:
    report = _report((_evidence("primary_source"),))

    row = report.rows[0]
    assert report.checklist_status == "blocked"
    assert report.blocked_count == Decimal("1.000000")
    assert row.satisfied_checks == ("primary_source", "timestamp_freshness")
    assert row.missing_checks == (
        "official_source",
        "independent_corroboration",
        "contradiction_follow_up",
        "market_move_explanation",
        "resolution_rule_source",
    )
    assert row.reason_codes == (
        "missing_official_source",
        "missing_independent_corroboration",
        "missing_contradiction_follow_up",
        "missing_market_move_explanation",
        "missing_resolution_rule_source",
        "source_collection_blocked",
    )
    assert report.reason_codes == row.reason_codes


def test_stale_timestamps_block_even_when_source_types_are_present() -> None:
    config = ResearchPacketSourceCollectionChecklistConfig(
        max_source_age_minutes=Decimal("60.000000"),
    )
    stale_observed_at = NOW - timedelta(minutes=90)

    report = _report(_complete_sources(observed_at=stale_observed_at), config=config)

    row = report.rows[0]
    assert row.latest_source_age_minutes == Decimal("90.000000")
    assert row.stale_source_count == Decimal("6.000000")
    assert row.timestamp_fresh is False
    assert row.missing_checks == ("timestamp_freshness",)
    assert row.checklist_status == "blocked"
    assert row.reason_codes == (
        "stale_source_timestamp",
        "source_collection_blocked",
    )
    assert report.checklist_status == "blocked"


def test_nonblocking_source_gaps_watch_without_blocking_collection() -> None:
    report = _report(
        (
            _evidence("official_source"),
            _evidence("primary_source"),
            _evidence("independent_corroboration"),
            _evidence("resolution_rule_source"),
        ),
    )

    row = report.rows[0]
    assert report.checklist_status == "watch"
    assert report.pass_count == Decimal("0.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.blocked_count == Decimal("0.000000")
    assert report.average_completion_score == Decimal("0.714286")
    assert row.satisfied_checks == (
        "official_source",
        "primary_source",
        "independent_corroboration",
        "resolution_rule_source",
        "timestamp_freshness",
    )
    assert row.missing_checks == (
        "contradiction_follow_up",
        "market_move_explanation",
    )
    assert row.checklist_status == "watch"
    assert row.reason_codes == (
        "missing_contradiction_follow_up",
        "missing_market_move_explanation",
        "source_collection_watch",
    )
    assert report.reason_codes == row.reason_codes


def test_empty_source_collection_blocks_with_empty_rows_reason_code() -> None:
    report = _report(())

    assert report.checklist_status == "blocked"
    assert report.packet_count == Decimal("0.000000")
    assert report.pass_count == Decimal("0.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.blocked_count == Decimal("0.000000")
    assert report.average_completion_score == Decimal("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "empty_source_collection",
        "source_collection_blocked",
    )


def test_mixed_packet_statuses_aggregate_counts_and_blocking_precedence() -> None:
    evidence = (
        *_complete_sources(),
        _evidence(
            "official_source",
            packet_id="packet_b",
            claim_id="claim_b",
            source_id="official_b",
        ),
        _evidence(
            "primary_source",
            packet_id="packet_b",
            claim_id="claim_b",
            source_id="primary_b",
        ),
        _evidence(
            "independent_corroboration",
            packet_id="packet_b",
            claim_id="claim_b",
            source_id="independent_b",
        ),
        _evidence(
            "resolution_rule_source",
            packet_id="packet_b",
            claim_id="claim_b",
            source_id="resolution_b",
        ),
        _evidence(
            "primary_source",
            packet_id="packet_c",
            claim_id="claim_c",
            source_id="primary_c",
        ),
    )

    report = _report(evidence)

    assert report.checklist_status == "blocked"
    assert report.packet_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.blocked_count == Decimal("1.000000")
    assert report.average_completion_score == Decimal("0.666667")
    assert [(row.packet_id, row.claim_id) for row in report.rows] == [
        ("packet_a", "claim_a"),
        ("packet_b", "claim_b"),
        ("packet_c", "claim_c"),
    ]
    assert [row.checklist_status for row in report.rows] == [
        "pass",
        "watch",
        "blocked",
    ]
    assert report.rows[0].completion_score == Decimal("1.000000")
    assert report.rows[1].completion_score == Decimal("0.714286")
    assert report.rows[2].completion_score == Decimal("0.285714")
    assert report.reason_codes == (
        "missing_official_source",
        "missing_independent_corroboration",
        "missing_contradiction_follow_up",
        "missing_market_move_explanation",
        "missing_resolution_rule_source",
        "source_collection_blocked",
        "source_collection_watch",
        "source_collection_pass",
    )


def test_payload_decimal_strings_and_tamper_evident_digest_are_deterministic() -> None:
    evidence = _complete_sources()
    report = _report(
        evidence,
        public_payload=(
            ResearchPacketSourceCollectionChecklistPublicPayloadItem(
                "safe_key",
                "safe value",
            ),
        ),
    )
    reordered_report = _report(tuple(reversed(evidence)))

    assert reordered_report.rows == report.rows
    assert reordered_report.derived_validation_digest != report.derived_validation_digest
    assert _report(evidence).derived_validation_digest == reordered_report.derived_validation_digest

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["packet_count"] == "1.000000"
    assert payload["average_completion_score"] == "1.000000"
    assert payload["rows"][0]["source_count"] == "6.000000"
    assert payload["rows"][0]["latest_source_age_minutes"] == "15.000000"
    assert payload["generated_at"] == "2026-02-01T12:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchPacketSourceCollectionChecklistPublicPayloadItem(
                    "safe_key",
                    "changed value",
                ),
            ),
        )


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    report = _report(_complete_sources())

    with pytest.raises(FrozenInstanceError):
        report.checklist_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchPacketSourceCollectionChecklistConfig):
            pass


def test_hard_flags_and_decimal_inputs_are_enforced() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        ResearchPacketSourceCollectionChecklistConfig(
            max_source_age_minutes=60,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="paper_only"):
        ResearchPacketSourceCollectionChecklistEvidence(
            packet_id="packet_a",
            claim_id="claim_a",
            source_id="official_a",
            source_type="official_source",
            source_family="official_source",
            observed_at=NOW,
            paper_only=False,
        )

    report = _report(_complete_sources())
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_unsafe_public_surfaces_are_rejected_or_absent() -> None:
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
        ResearchPacketSourceCollectionChecklistConfig,
        ResearchPacketSourceCollectionChecklistEvidence,
        ResearchPacketSourceCollectionChecklistPublicPayloadItem,
        ResearchPacketSourceCollectionChecklistRow,
        ResearchPacketSourceCollectionChecklistReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    for key in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchPacketSourceCollectionChecklistPublicPayloadItem(
                f"{key}_key",
                "safe value",
            )

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
    ):
        assert not hasattr(api, forbidden_name)


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
