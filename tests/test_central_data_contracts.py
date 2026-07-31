from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.central_data_contracts import (
    MAX_RESPONSE_BYTES,
    CentralDataRequest,
    EvidenceReference,
    FailureStatus,
    Freshness,
    NormalizedObservation,
    ObservationValueState,
    ParseState,
    RawResponse,
    SourceDefinition,
    canonical_json_bytes,
    sha256_hash,
)


NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def reference() -> EvidenceReference:
    return EvidenceReference(
        source_id="gamma",
        retrieval_time=NOW,
        observation_time=NOW,
        payload_hash=sha256_hash(b"payload"),
    )


def source(url: str = "https://example.com/data") -> SourceDefinition:
    return SourceDefinition(
        source_id="gamma",
        source_family="polymarket_gamma",
        url_template=url,
        content_type="application/json",
        freshness_policy_seconds=300,
        is_official=True,
    )


def test_source_definition_and_host_are_canonical():
    item = source()
    assert item.host == "example.com"
    assert item.is_official is True


def test_central_data_request_is_get_only_and_immutable():
    request = CentralDataRequest(
        source_id="gamma",
        url="https://example.com/data",
        headers={"Accept": "application/json"},
    )
    assert request.method == "GET"
    assert request.headers["accept"] == "application/json"
    with pytest.raises(TypeError):
        request.headers["x-test"] = "mutated"
    with pytest.raises(ValueError):
        CentralDataRequest(source_id="gamma", url="https://example.com/data", method="POST")
    with pytest.raises(ValueError):
        CentralDataRequest(
            source_id="gamma",
            url="https://example.com/data",
            headers={"Authorization": "Bearer token"},
        )


@pytest.mark.parametrize(
    "url",
    (
        "http://example.com/data",
        "https://user:pass@example.com/data",
        "https://example.com/data?token=x",
        "https://example.com/data#fragment",
        "https://example.com:443/data",
        "https://127.0.0.1/data",
        "https://localhost/data",
        "https://service.local/data",
    ),
)
def test_source_definition_rejects_unsafe_url_templates(url: str):
    with pytest.raises(ValueError):
        source(url)


@pytest.mark.parametrize(
    "url",
    (
        "https://{tenant}.example.com/data",
        "https://example.com/{bad-name}",
        "https://example.com/{UPPER}",
        "https://example.com/{}",
        "https://example.com/{{token}}",
    ),
)
def test_source_definition_rejects_unrendered_endpoint_templates(url: str):
    with pytest.raises(ValueError):
        source(url)


def test_raw_response_hashes_bytes_and_rejects_oversize():
    response = RawResponse(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body=b"{\"value\":0}",
        url="https://example.com/data",
        retrieval_time=NOW,
    )
    assert response.payload_hash == sha256_hash(response.body)
    assert response.raw_payload_sha256 == response.payload_hash
    with pytest.raises(TypeError):
        response.headers["x-test"] = "mutated"
    with pytest.raises(ValueError):
        RawResponse(
            status_code=200,
            headers={},
            body=b"x" * (MAX_RESPONSE_BYTES + 1),
            url="https://example.com/data",
            retrieval_time=NOW,
        )


def test_normalized_observation_distinguishes_null_zero_unknown():
    null_observation = NormalizedObservation(
        source_id="gamma",
        observation_time=NOW,
        value=None,
        freshness=Freshness.UNKNOWN,
        parse_state=ParseState.UNKNOWN,
        evidence_reference=reference(),
        value_state=ObservationValueState.NULL,
    )
    zero_observation = NormalizedObservation(
        source_id="gamma",
        observation_time=NOW,
        value=Decimal("0"),
        freshness=Freshness.FRESH,
        parse_state=ParseState.SUCCESS,
        evidence_reference=reference(),
    )
    unknown_observation = NormalizedObservation(
        source_id="gamma",
        observation_time=NOW,
        value=None,
        freshness=Freshness.UNKNOWN,
        parse_state=ParseState.UNKNOWN,
        evidence_reference=reference(),
        value_state=ObservationValueState.UNKNOWN,
        reason_codes=("central_evidence_unknown",),
    )
    assert null_observation.value_state is ObservationValueState.NULL
    assert zero_observation.value_state is ObservationValueState.ZERO
    assert unknown_observation.value_state is ObservationValueState.UNKNOWN
    with pytest.raises(ValueError):
        NormalizedObservation(
            source_id="gamma",
            observation_time=NOW,
            value=1,
            freshness=Freshness.FRESH,
            parse_state=ParseState.SUCCESS,
            evidence_reference=reference(),
        )
    with pytest.raises(ValueError):
        NormalizedObservation(
            source_id="gamma",
            observation_time=NOW,
            value=Decimal("1"),
            freshness=Freshness.FRESH,
            parse_state=ParseState.SUCCESS,
            evidence_reference=reference(),
            value_state=ObservationValueState.ZERO,
        )


def test_contracts_enforce_hard_flags_and_reference_integrity():
    with pytest.raises(ValueError):
        NormalizedObservation(
            source_id="gamma",
            observation_time=NOW,
            value=Decimal("1"),
            freshness=Freshness.FRESH,
            parse_state=ParseState.SUCCESS,
            evidence_reference=reference(),
            paper_only=False,
        )
    with pytest.raises(ValueError):
        EvidenceReference(
            source_id="gamma",
            retrieval_time=NOW,
            observation_time=NOW,
            payload_hash="z" * 64,
        )
    with pytest.raises(ValueError):
        source_definition = source()
        SourceDefinition(
            source_id=source_definition.source_id,
            source_family=source_definition.source_family,
            url_template=source_definition.url_template,
            content_type=source_definition.content_type,
            freshness_policy_seconds=source_definition.freshness_policy_seconds,
            paper_only=False,
        )


def test_normalized_observation_deep_freezes_values_and_matches_reference_time():
    observation = NormalizedObservation(
        source_id="gamma",
        observation_time=NOW,
        value={"nested": [Decimal("0")]},
        freshness=Freshness.FRESH,
        parse_state=ParseState.SUCCESS,
        evidence_reference=reference(),
    )
    assert observation.value["nested"] == (Decimal("0"),)
    with pytest.raises(TypeError):
        observation.value["nested"] = ()
    with pytest.raises(ValueError):
        NormalizedObservation(
            source_id="gamma",
            observation_time=NOW,
            value=Decimal("1"),
            freshness=Freshness.FRESH,
            parse_state=ParseState.SUCCESS,
            evidence_reference=EvidenceReference(
                source_id="gamma",
                retrieval_time=NOW,
                observation_time=NOW.replace(hour=13),
                payload_hash=sha256_hash(b"payload"),
            ),
        )


def test_canonical_json_is_sorted_and_rejects_floats():
    assert canonical_json_bytes({"b": Decimal("2.00"), "a": 0}) == b'{"a":0,"b":"2.00"}'
    with pytest.raises(ValueError):
        canonical_json_bytes({"value": 1.5})
    with pytest.raises(ValueError):
        NormalizedObservation(
            source_id="gamma",
            observation_time=NOW,
            value={"value": 1.5},
            freshness=Freshness.FRESH,
            parse_state=ParseState.SUCCESS,
            evidence_reference=reference(),
        )


def test_failure_status_is_typed():
    response = RawResponse(
        status_code=302,
        headers={"location": "https://other.example"},
        body=b"",
        url="https://example.com/data",
        retrieval_time=NOW,
        failure_status=FailureStatus.REDIRECT,
    )
    assert response.failure_status is FailureStatus.REDIRECT
