from datetime import UTC, datetime

from polymarket_alpha_lab.central_data_contracts import RawResponse, SourceDefinition
from polymarket_alpha_lab.central_data_persistence_policy import (
    CentralDataPersistencePolicy,
    MAX_RESPONSE_BYTES,
)


def _source() -> SourceDefinition:
    return SourceDefinition(
        source_id="public-source",
        source_family="official",
        url_template="https://example.com/data",
        content_type="application/json",
        freshness_policy_seconds=60,
        is_official=True,
    )


def _raw(
    body: bytes = b'{"id":"market-1"}',
    *,
    content_type: str | None = "application/json",
    **kwargs: object,
) -> RawResponse:
    return RawResponse(
        status_code=200,
        headers={"content-type": "application/json", "etag": "v1"},
        body=body,
        url="https://example.com/data",
        request_url="https://example.com/data",
        retrieval_time=datetime.now(UTC),
        content_type=content_type,
        **kwargs,
    )


def test_safe_json_and_boundary_are_accepted() -> None:
    policy = CentralDataPersistencePolicy()
    assert policy.evaluate_raw_response(_raw(b"{}"), source_definition=_source()) is None
    assert policy.evaluate_raw_response(
        _raw(b"x" * MAX_RESPONSE_BYTES), source_definition=_source()
    ) is None


def test_ordinary_public_id_is_not_treated_as_personal_data() -> None:
    assert CentralDataPersistencePolicy().evaluate_raw_response(
        _raw(b'{"id":"market-1"}'), source_definition=_source()
    ) is None


def test_sensitive_body_values_are_rejected_without_echoing_input() -> None:
    policy = CentralDataPersistencePolicy()
    for sample in (
        b'{"token":"secret-value"}',
        b'{"contact":"alice@example.com"}',
        b'{"wallet":"0x0000000000000000000000000000000000000000"}',
    ):
        rejection = policy.evaluate_raw_response(_raw(sample), source_definition=_source())
        assert rejection is not None
        assert rejection.reason == "sensitive_data_detected"
        assert "alice" not in repr(rejection)
        assert "secret-value" not in str(rejection)


def test_size_encoding_and_url_boundaries_fail_closed() -> None:
    policy = CentralDataPersistencePolicy()
    assert policy.evaluate_raw_response(
        {
            "body": b"x" * (MAX_RESPONSE_BYTES + 1),
            "content_type": "application/json",
            "headers": {"content-type": "application/json"},
            "request_url": "https://example.com/data",
            "final_url": "https://example.com/data",
            "status_code": 200,
        },
        source_definition=_source(),
    ).reason == "oversize_body"
    assert policy.evaluate_raw_response(
        _raw(b"\xff"), source_definition=_source()
    ).reason == "invalid_utf8"
    for url in (
        "https://example.com/data?account=secret",
        "https://user:password@example.com/data",
        "https://example.com/data#fragment",
    ):
        rejection = policy.evaluate_raw_response(
            {
                "body": b"{}",
                "content_type": "application/json",
                "headers": {"content-type": "application/json"},
                "request_url": url,
                "final_url": url,
                "status_code": 200,
            },
            source_definition=_source(),
        )
        assert rejection is not None


def test_header_allowlist_and_header_values_are_checked() -> None:
    policy = CentralDataPersistencePolicy()
    raw = _raw()
    unsafe = RawResponse(
        status_code=200,
        headers={"content-type": "application/json", "x-secret": "no"},
        body=raw.body,
        url=raw.url,
        request_url=raw.request_url,
        retrieval_time=raw.retrieval_time,
        content_type="application/json",
    )
    assert policy.evaluate_raw_response(unsafe, source_definition=_source()).reason == "unsafe_header"


def test_registered_response_media_type_is_enforced_by_the_policy_gate() -> None:
    policy = CentralDataPersistencePolicy()
    mismatch = policy.evaluate_raw_response(
        _raw(content_type="application/xml"),
        source_definition=_source(),
    )
    assert mismatch is not None
    assert mismatch.reason == "source_content_type_mismatch"

    wildcard_source = SourceDefinition(
        source_id="wildcard-source",
        source_family="official",
        url_template="https://example.com/data",
        content_type="*/*",
        freshness_policy_seconds=60,
        is_official=True,
    )
    unsupported = policy.evaluate_raw_response(
        _raw(content_type="text/plain"),
        source_definition=wildcard_source,
    )
    assert unsupported is not None
    assert unsupported.reason == "unsupported_media"

    missing = policy.evaluate_raw_response(
        _raw(b"", content_type=None),
        source_definition=_source(),
    )
    assert missing is not None
    assert missing.reason == "missing_content_type"


def test_public_market_metadata_addresses_are_not_personal_data() -> None:
    policy = CentralDataPersistencePolicy()
    for sample in (
        b'{"assetAddress":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"submitted_by":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"resolvedBy":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"volume":"1234567890123"}',
        b'{"questionID":"0x123456789012345678901234567890123456789012345678901234567890abcd"}',
    ):
        assert policy.evaluate_raw_response(_raw(sample), source_definition=_source()) is None


def test_account_context_wallets_and_formatted_phones_still_refuse() -> None:
    policy = CentralDataPersistencePolicy()
    for sample in (
        b'{"user_wallet":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"ownerAddress":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"fromAddress":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"to_address":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"USER_WALLET":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"usr":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"acct":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        '{"w\u0430llet":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}'.encode(),
        b'{"unknownAddressKey":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"nested":{"owner":"0x91430cad2d6170971b5ba9a8e5f0a00000000000"}}',
        b'{"arr":["0x91430cad2d6170971b5ba9a8e5f0a00000000000"]}',
        b'{"big":"prefix glued to 0x91430cad2d6170971b5ba9a8e5f0a00000000000"}',
        b'{"userWallet":"0X91430CAD2D6170971B5BA9A8E5F0A00000000000"}',
        b'{"contact":"+1 (555) 123-4567"}',
        b'{"note":"call 555-123-4567 now"}',
        b'{"intl":"+44 20 1234 5678"}',
        b'{"local":"1234-5678"}',
        b'{"eu":"+49-30-1234-5678"}',
    ):
        rejection = policy.evaluate_raw_response(_raw(sample), source_definition=_source())
        assert rejection is not None
        assert rejection.reason == "sensitive_data_detected"
