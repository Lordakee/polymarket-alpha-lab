from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.central_data_contracts import (
    RESERVED_REQUEST_PARAM_NAMES,
    CentralDataRequest,
    RequestParamSpec,
    SourceDefinition,
)
from polymarket_alpha_lab.central_data_request_params import (
    PaginationPolicy,
    build_request_query,
    canonical_query_string,
    request_query_identity,
)


def spec_source() -> SourceDefinition:
    return SourceDefinition(
        source_id="spec_source",
        source_family="spec_family",
        url_template="https://example.com/data",
        content_type="application/json",
        freshness_policy_seconds=60,
        query_params=(
            RequestParamSpec("condition_id", "pattern", pattern=r"[0-9a-fA-Fx]{1,66}"),
            RequestParamSpec("limit", "int_range", min_value=1, max_value=100, default="50"),
            RequestParamSpec("pair", "enum", required=True, choices=("XBTUSD", "ETHUSD")),
        ),
    )


def test_param_specs_reject_reserved_and_malformed_names() -> None:
    for reserved in RESERVED_REQUEST_PARAM_NAMES:
        with pytest.raises(ValueError, match="reserved"):
            RequestParamSpec(reserved, "pattern", pattern=r"[a-z]+")
    with pytest.raises(ValueError):
        RequestParamSpec("BadName", "pattern", pattern=r"[a-z]+")
    with pytest.raises(ValueError):
        RequestParamSpec("x", "unknown_kind")
    with pytest.raises(ValueError):
        RequestParamSpec("x", "pattern")
    with pytest.raises(ValueError):
        RequestParamSpec("x", "int_range", min_value=10, max_value=1)
    with pytest.raises(ValueError):
        RequestParamSpec("x", "enum", choices=())
    with pytest.raises(ValueError):
        RequestParamSpec("x", "enum", required=True, choices=("a",), default="a")


def test_build_request_query_validates_types_defaults_and_unknowns() -> None:
    source = spec_source()
    assert build_request_query(source, {"pair": "XBTUSD", "limit": 25}) == {
        "limit": "25",
        "pair": "XBTUSD",
    }
    assert build_request_query(source, {"pair": "ETHUSD"}) == {
        "limit": "50",
        "pair": "ETHUSD",
    }
    with pytest.raises(ValueError, match="unknown request parameters"):
        build_request_query(source, {"pair": "XBTUSD", "mystery": "1"})
    with pytest.raises(ValueError, match="missing required"):
        build_request_query(source, {"limit": "5"})
    with pytest.raises(ValueError):
        build_request_query(source, {"pair": "XBTUSD", "limit": "101"})
    with pytest.raises(ValueError):
        build_request_query(source, {"pair": "XBTUSD", "limit": "abc"})
    with pytest.raises(ValueError):
        build_request_query(source, {"pair": "SOLUSD"})
    with pytest.raises(ValueError):
        build_request_query(source, {"pair": "XBTUSD", "condition_id": "not hex!"})


def test_canonical_query_string_is_name_sorted_and_stable() -> None:
    assert canonical_query_string({"offset": "10", "limit": "5"}) == "limit=5&offset=10"
    assert canonical_query_string({}) == ""
    first = request_query_identity("s", {"a": "1", "b": "2"})
    second = request_query_identity("s", {"b": "2", "a": "1"})
    assert first == second
    assert first != request_query_identity("s", {"a": "1", "b": "3"})


def test_central_data_request_query_is_canonical_and_reserved_free() -> None:
    request = CentralDataRequest(
        source_id="spec_source",
        url="https://example.com/data",
        query={"limit": "5", "pair": "XBTUSD"},
    )
    assert dict(request.query) == {"limit": "5", "pair": "XBTUSD"}
    with pytest.raises(ValueError, match="reserved"):
        CentralDataRequest(
            source_id="spec_source",
            url="https://example.com/data",
            query={"id": "123"},
        )
    with pytest.raises(ValueError):
        CentralDataRequest(
            source_id="spec_source",
            url="https://example.com/data",
            query={"bad name": "1"},
        )
    with pytest.raises(ValueError):
        CentralDataRequest(
            source_id="spec_source",
            url="https://example.com/data",
            query={"limit": "has space"},
        )
    with pytest.raises(ValueError):
        CentralDataRequest(
            source_id="spec_source",
            url="https://example.com/data",
            query={"limit": "%2020"},
        )


def test_pagination_policy_bounds() -> None:
    assert PaginationPolicy(max_pages=10, min_items_per_page=1, max_items_per_page=100)
    with pytest.raises(ValueError):
        PaginationPolicy(max_pages=0, min_items_per_page=1, max_items_per_page=100)
    with pytest.raises(ValueError):
        PaginationPolicy(max_pages=10, min_items_per_page=100, max_items_per_page=1)


def test_source_definition_query_params_are_unique_and_typed() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        SourceDefinition(
            source_id="s",
            source_family="f",
            url_template="https://example.com/data",
            content_type="application/json",
            freshness_policy_seconds=60,
            query_params=(
                RequestParamSpec("limit", "int_range", min_value=1, max_value=10),
                RequestParamSpec("limit", "int_range", min_value=1, max_value=10),
            ),
        )
    assert spec_source().query_params[1].name == "limit"


def test_reserved_names_would_trip_the_persistence_policy() -> None:
    from polymarket_alpha_lab.central_data_persistence_policy import (
        CentralDataPersistencePolicy,
    )

    policy = CentralDataPersistencePolicy()
    for name in ("id", "uid", "user_id", "account_id", "wallet"):
        url = f"https://example.com/data?{name}=1"
        rejection = policy.evaluate_raw_response(
            {
                "body": b"{}",
                "content_type": "application/json",
                "headers": {"content-type": "application/json"},
                "request_url": url,
                "final_url": url,
                "status_code": 200,
            }
        )
        assert rejection is not None, name
