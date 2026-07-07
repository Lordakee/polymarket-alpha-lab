from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_evidence_timestamp_integrity_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def assert_payload_decimal_strings(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if isinstance(value, (Decimal, float, int)):
        raise AssertionError(f"payload numeric value must be a string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_decimal_strings(item)
    if isinstance(value, list):
        for item in value:
            assert_payload_decimal_strings(item)


def packet(
    packet_id: str,
    *,
    event_slug: str = "fed-july-cut",
    category: str = "macro-rates",
    evidence_created_at: datetime = GENERATED_AT - timedelta(minutes=10),
    evidence_observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    packet_updated_at: datetime = GENERATED_AT - timedelta(minutes=4),
    source_published_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
    source_count: str = "2",
):
    timestamp_gate = module()
    return timestamp_gate.ResearchPacketEvidenceTimestampIntegrityInput(
        packet_id=packet_id,
        event_slug=event_slug,
        category=category,
        evidence_created_at=evidence_created_at,
        evidence_observed_at=evidence_observed_at,
        packet_updated_at=packet_updated_at,
        source_published_at=source_published_at,
        source_count=d(source_count),
    )


def report(*packets):
    timestamp_gate = module()
    return timestamp_gate.build_research_packet_evidence_timestamp_integrity_gate_v2_report(
        packets,
        config=timestamp_gate.ResearchPacketEvidenceTimestampIntegrityGateV2Config(
            max_observation_lag_seconds=d("600"),
            max_packet_update_lag_seconds=d("300"),
        ),
        generated_at=GENERATED_AT,
    )


def test_report_flags_future_timestamps_stale_updates_and_long_observation_lags() -> None:
    timestamp_report = report(
        packet(
            "packet-clean",
            evidence_created_at=GENERATED_AT - timedelta(minutes=6),
            evidence_observed_at=GENERATED_AT - timedelta(minutes=3),
            packet_updated_at=GENERATED_AT - timedelta(minutes=2),
            source_published_at=GENERATED_AT - timedelta(minutes=30),
            source_count="3",
        ),
        packet(
            "packet-stale",
            event_slug="crypto-etf-flow",
            category="crypto",
            evidence_created_at=GENERATED_AT - timedelta(hours=3),
            evidence_observed_at=GENERATED_AT - timedelta(hours=2, minutes=30),
            packet_updated_at=GENERATED_AT - timedelta(hours=2),
            source_published_at=GENERATED_AT - timedelta(hours=4),
            source_count="1",
        ),
        packet(
            "packet-future",
            event_slug="election-turnout",
            category="politics",
            evidence_created_at=GENERATED_AT + timedelta(seconds=1),
            evidence_observed_at=GENERATED_AT + timedelta(seconds=2),
            packet_updated_at=GENERATED_AT + timedelta(seconds=3),
            source_published_at=GENERATED_AT + timedelta(microseconds=500000),
            source_count="2",
        ),
    )

    assert is_dataclass(timestamp_report)
    assert timestamp_report.generated_at == GENERATED_AT
    assert timestamp_report.config_version == (
        "research-packet-evidence-timestamp-integrity-gate-v2"
    )
    assert timestamp_report.packet_count == d("3")
    assert timestamp_report.pass_packet_count == d("1")
    assert timestamp_report.watch_packet_count == d("1")
    assert timestamp_report.block_packet_count == d("1")
    assert timestamp_report.future_timestamp_packet_count == d("1")
    assert timestamp_report.stale_packet_update_count == d("1")
    assert timestamp_report.long_observation_lag_count == d("1")
    assert timestamp_report.max_observation_lag_seconds == d("1800")
    assert timestamp_report.report_status == "block"
    assert timestamp_report.reason_codes == (
        "future_timestamp_detected",
        "packet_update_stale",
        "observation_lag_long",
    )
    assert type(timestamp_report.derived_validation_digest) is str
    assert len(timestamp_report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in timestamp_report.derived_validation_digest
    )
    assert timestamp_report.paper_only is True
    assert timestamp_report.report_only is True
    assert timestamp_report.readonly is True

    assert tuple(row.packet_id for row in timestamp_report.rows) == (
        "packet-future",
        "packet-stale",
        "packet-clean",
    )
    future = timestamp_report.rows[0]
    assert future.status == "block"
    assert future.future_timestamp_count == d("4")
    assert future.observation_lag_seconds == d("1")
    assert future.packet_update_lag_seconds == d("1")
    assert future.reason_codes == ("future_timestamp_detected",)

    stale = timestamp_report.rows[1]
    assert stale.status == "watch"
    assert stale.observation_lag_seconds == d("1800")
    assert stale.packet_update_lag_seconds == d("1800")
    assert stale.reason_codes == (
        "packet_update_stale",
        "observation_lag_long",
    )

    assert tuple(
        (count.reason_code, count.count) for count in timestamp_report.reason_code_counts
    ) == (
        ("future_timestamp_detected", d("1")),
        ("packet_update_stale", d("1")),
        ("observation_lag_long", d("1")),
    )


def test_empty_report_is_report_only_with_empty_status_and_zero_decimals() -> None:
    timestamp_report = report()

    assert timestamp_report.report_status == "empty"
    assert timestamp_report.reason_codes == ("timestamp_integrity_empty",)
    assert timestamp_report.packet_count == d("0")
    assert timestamp_report.pass_packet_count == d("0")
    assert timestamp_report.watch_packet_count == d("0")
    assert timestamp_report.block_packet_count == d("0")
    assert timestamp_report.future_timestamp_packet_count == d("0")
    assert timestamp_report.stale_packet_update_count == d("0")
    assert timestamp_report.long_observation_lag_count == d("0")
    assert timestamp_report.max_observation_lag_seconds == d("0")
    assert timestamp_report.rows == ()
    assert timestamp_report.reason_code_counts == ()
    assert timestamp_report.paper_only is True
    assert timestamp_report.report_only is True
    assert timestamp_report.readonly is True


def test_inputs_validate_decimal_counts_utc_datetimes_flags_and_mutation() -> None:
    timestamp_gate = module()

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        timestamp_gate.ResearchPacketEvidenceTimestampIntegrityInput(
            packet_id="packet-a",
            event_slug="event-a",
            category="macro-rates",
            evidence_created_at=GENERATED_AT - timedelta(minutes=5),
            evidence_observed_at=GENERATED_AT - timedelta(minutes=4),
            packet_updated_at=GENERATED_AT - timedelta(minutes=3),
            source_published_at=GENERATED_AT - timedelta(minutes=10),
            source_count=1,
        )

    with pytest.raises(ValueError, match="max_observation_lag_seconds must be a Decimal"):
        timestamp_gate.ResearchPacketEvidenceTimestampIntegrityGateV2Config(
            max_observation_lag_seconds=_DecimalSubclass("1"),
        )

    with pytest.raises(ValueError, match="evidence_created_at must be timezone-aware"):
        packet("packet-a", evidence_created_at=datetime(2026, 7, 7, 11, 55))

    normalized = report(
        packet(
            "packet-a",
            evidence_created_at=datetime(
                2026,
                7,
                7,
                7,
                55,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            evidence_observed_at=datetime(
                2026,
                7,
                7,
                7,
                56,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            packet_updated_at=datetime(
                2026,
                7,
                7,
                7,
                57,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
    )
    assert normalized.rows[0].evidence_created_at == datetime(
        2026,
        7,
        7,
        11,
        55,
        tzinfo=UTC,
    )
    assert normalized.rows[0].observation_lag_seconds == d("60")

    row = packet("packet-mutate")
    with pytest.raises(FrozenInstanceError):
        row.source_count = d("9")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        replace(row, report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)


def test_validates_uniqueness_counts_and_timestamp_order() -> None:
    timestamp_gate = module()

    with pytest.raises(ValueError, match="packet_id values must be unique"):
        report(packet("packet-a"), packet("packet-a"))

    with pytest.raises(ValueError, match="source_count must be positive"):
        packet("packet-a", source_count="0")

    with pytest.raises(
        ValueError,
        match="evidence_observed_at must not precede evidence_created_at",
    ):
        packet(
            "packet-a",
            evidence_created_at=GENERATED_AT - timedelta(minutes=5),
            evidence_observed_at=GENERATED_AT - timedelta(minutes=6),
        )

    with pytest.raises(
        ValueError,
        match="packet_updated_at must not precede evidence_observed_at",
    ):
        packet(
            "packet-a",
            evidence_observed_at=GENERATED_AT - timedelta(minutes=5),
            packet_updated_at=GENERATED_AT - timedelta(minutes=6),
        )

    with pytest.raises(
        ValueError,
        match="source_published_at must not be after evidence_created_at",
    ):
        packet(
            "packet-a",
            evidence_created_at=GENERATED_AT - timedelta(minutes=5),
            source_published_at=GENERATED_AT - timedelta(minutes=4),
        )

    with pytest.raises(ValueError, match="rows must contain"):
        timestamp_gate.build_research_packet_evidence_timestamp_integrity_gate_v2_report(
            [object()],
            config=timestamp_gate.ResearchPacketEvidenceTimestampIntegrityGateV2Config(),
            generated_at=GENERATED_AT,
        )


def test_subsecond_lags_are_decimal_normalized_without_float_rounding() -> None:
    timestamp_report = report(
        packet(
            "packet-a",
            evidence_created_at=GENERATED_AT - timedelta(seconds=3, microseconds=250000),
            evidence_observed_at=GENERATED_AT - timedelta(seconds=1, microseconds=500000),
            packet_updated_at=GENERATED_AT - timedelta(seconds=1),
        ),
    )

    assert timestamp_report.rows[0].observation_lag_seconds == d("1.750000")
    assert timestamp_report.rows[0].packet_update_lag_seconds == d("0.500000")
    assert timestamp_report.max_observation_lag_seconds == d("1.750000")
    assert type(timestamp_report.rows[0].observation_lag_seconds) is Decimal
    assert timestamp_report.rows[0].observation_lag_seconds.as_tuple().exponent == -6


def test_json_ready_payload_uses_strings_for_decimals_and_rejects_unsafe_surfaces() -> None:
    timestamp_gate = module()
    timestamp_report = report(
        packet(
            "packet-a",
            evidence_created_at=GENERATED_AT - timedelta(hours=1),
            evidence_observed_at=GENERATED_AT - timedelta(minutes=30),
            packet_updated_at=GENERATED_AT - timedelta(minutes=29),
            source_published_at=GENERATED_AT - timedelta(hours=2),
        ),
    )

    payload = timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
        timestamp_report,
    )

    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["packet_count"] == "1"
    assert payload["max_observation_lag_seconds"] == "1800"
    assert payload["rows"][0]["observation_lag_seconds"] == "1800"
    assert payload["derived_validation_digest"] == (
        timestamp_report.derived_validation_digest
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_payload_decimal_strings(payload)

    with pytest.raises(
        ValueError,
        match="report must be a ResearchPacketEvidenceTimestampIntegrityGateV2Report",
    ):
        timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
            object(),
        )


def test_derived_validation_digest_is_payload_bound_and_tamper_evident() -> None:
    timestamp_gate = module()
    timestamp_report = report(packet("packet-a"))
    payload = timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
        timestamp_report,
    )

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(timestamp_report, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["packet_count"] = "3"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
            tampered_payload,
        )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
            missing_digest,
        )


@pytest.mark.parametrize(
    "unsafe_key",
    (
        "live_connection",
        "auth_token",
        "wallet_handle",
        "order_payload",
        "network_client",
        "database_handle",
        "persist_path",
    ),
)
def test_payload_rejects_unsafe_live_surface_fields(unsafe_key: str) -> None:
    timestamp_gate = module()
    payload = timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
        report(),
    )

    with pytest.raises(ValueError, match="unsafe live surface field"):
        timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
            {**payload, unsafe_key: "redacted"},
        )


def test_payload_dict_preserves_hard_flags_and_decimal_string_contract() -> None:
    timestamp_gate = module()
    payload = timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
        report(packet("packet-a")),
    )

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly must be True"):
        timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
            downgraded,
        )

    numeric_payload = dict(payload)
    numeric_payload["packet_count"] = 1
    with pytest.raises(ValueError, match="must use Decimal-string values"):
        timestamp_gate.research_packet_evidence_timestamp_integrity_gate_v2_payload(
            numeric_payload,
        )


def test_public_api_is_isolated_and_contains_no_live_surface_names() -> None:
    timestamp_gate = module()

    assert timestamp_gate.__all__ == (
        "DEFAULT_RESEARCH_PACKET_EVIDENCE_TIMESTAMP_INTEGRITY_GATE_V2_CONFIG_VERSION",
        "ResearchPacketEvidenceTimestampIntegrityGateV2Config",
        "ResearchPacketEvidenceTimestampIntegrityInput",
        "ResearchPacketEvidenceTimestampIntegrityGateV2Row",
        "ResearchPacketEvidenceTimestampIntegrityGateV2ReasonCodeCount",
        "ResearchPacketEvidenceTimestampIntegrityGateV2Report",
        "build_research_packet_evidence_timestamp_integrity_gate_v2_report",
        "research_packet_evidence_timestamp_integrity_gate_v2_payload",
    )
    for exported_name in timestamp_gate.__all__:
        value = getattr(timestamp_gate, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    public_surface = " ".join(timestamp_gate.__all__).lower()
    for unsafe in (
        "auth",
        "wallet",
        "network",
        "database",
        "persist",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
    ):
        assert unsafe not in public_surface
