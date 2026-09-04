from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.central_data_contracts import (
    EvidenceReference,
    Freshness,
    NormalizedObservation,
    ObservationValueState,
    ParseState,
    RawResponse,
    SourceDefinition,
)
from polymarket_alpha_lab.central_data_db_row import (
    NormalizedObservationRow,
    RawEventRow,
    TypedEnvelope,
)


def _source() -> SourceDefinition:
    return SourceDefinition("source-a", "official", "https://example.com/data", "application/json", 60, True)


def _raw(at: datetime | None = None, body: bytes = b'{"value":1}') -> RawResponse:
    at = at or datetime.now(UTC)
    return RawResponse(
        200,
        {"content-type": "application/json", "etag": "v1"},
        body,
        "https://example.com/data",
        retrieval_time=at,
        request_url="https://example.com/data",
        content_type="application/json",
    )


def test_raw_identity_is_deterministic_but_retrieval_events_are_distinct() -> None:
    source = _source()
    first = RawEventRow.from_contracts(source, _raw())
    replay = RawEventRow.from_contracts(source, _raw(first.retrieval_time))
    later = RawEventRow.from_contracts(source, _raw(first.retrieval_time + timedelta(seconds=1)))
    assert first.raw_event_id == replay.raw_event_id
    assert first.raw_event_id != later.raw_event_id
    assert first.raw_payload_sha256 == later.raw_payload_sha256
    assert "value" not in repr(first)
    assert "example.com" not in repr(first.identity)


def test_typed_envelope_preserves_decimal_string_null_and_user_type_key() -> None:
    value = {"type": "user-field", "decimal": Decimal("-0.00"), "none": None, "text": "0.00"}
    encoded = TypedEnvelope.encode(value)
    assert encoded["type"] == "object"
    decoded = TypedEnvelope.decode(encoded)
    assert decoded["decimal"] == Decimal("-0.00")
    assert decoded["text"] == "0.00"
    assert decoded["type"] == "user-field"
    with pytest.raises(ValueError):
        TypedEnvelope.decode({"type": "decimal", "value": "1", "items": []})
    with pytest.raises(ValueError):
        TypedEnvelope.encode({"valid": None, 1: None})


def test_raw_row_rejects_a_sha_shaped_but_spoofed_event_identity() -> None:
    row = RawEventRow.from_contracts(_source(), _raw())
    with pytest.raises(ValueError, match="immutable event identity"):
        replace(row, raw_event_id="0" * 64)


def test_normalized_id_contains_complete_observation_identity() -> None:
    source = _source()
    raw = RawEventRow.from_contracts(source, _raw())
    observed_at = raw.retrieval_time
    evidence = EvidenceReference("source-a", raw.retrieval_time, observed_at, raw.raw_payload_sha256)
    observation = NormalizedObservation(
        "source-a",
        observed_at,
        Decimal("1.20"),
        Freshness.FRESH,
        ParseState.SUCCESS,
        evidence,
        value_state=ObservationValueState.PRESENT,
    )
    row = NormalizedObservationRow.from_contracts(source, observation, raw.identity)
    assert row.normalized_observation_id
    restored = row.to_contracts(source, raw.identity)
    assert restored.value == Decimal("1.20")
    with pytest.raises(ValueError):
        NormalizedObservationRow(
            normalized_observation_id="a" * 64,
            raw_event_id=row.raw_event_id,
            source_id=row.source_id,
            source_family=row.source_family,
            endpoint_url=row.endpoint_url,
            official_source=True,
            observation_time=row.observation_time,
            retrieval_time=row.retrieval_time,
            raw_payload_sha256=row.raw_payload_sha256,
            parser_version=row.parser_version,
            parse_state=row.parse_state,
            freshness_state=row.freshness_state,
            failure_status=row.failure_status,
            value_state=row.value_state,
            reason_codes=row.reason_codes,
            typed_value=dict(row.typed_value),
        )
