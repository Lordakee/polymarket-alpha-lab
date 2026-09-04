from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.central_data_contracts import (
    FailureStatus,
    Freshness,
    ParseState,
    SourceDefinition,
    ObservationValueState,
)
from polymarket_alpha_lab.central_data_db_row import RawEventRow
from polymarket_alpha_lab.central_data_normalization import (
    CentralDataNormalizer,
    NormalizationError,
)


def test_json_numbers_use_decimal_and_duplicate_keys_fail() -> None:
    value = CentralDataNormalizer.parse_json('{"whole":1,"fraction":1.25,"nested":{"zero":0}}')
    assert value == {"whole": Decimal("1"), "fraction": Decimal("1.25"), "nested": {"zero": Decimal("0")}}
    with pytest.raises(NormalizationError, match="duplicate_json_key"):
        CentralDataNormalizer.parse_json('{"a":1,"a":2}')
    with pytest.raises(NormalizationError, match="non_finite_number"):
        CentralDataNormalizer.parse_json('{"a":NaN}')


def test_xml_declarations_are_case_insensitive_and_tree_is_bounded() -> None:
    for document in ("<!DOCTYPE rss><rss/>", "<!doctype rss><rss/>", "<!ENTITY x 'y'><rss/>"):
        with pytest.raises(NormalizationError):
            CentralDataNormalizer.parse_rss(document)
    parsed = CentralDataNormalizer.parse_rss("<rss><channel><title>public</title></channel></rss>")
    assert parsed["tag"] == "rss"
    assert parsed["children"][0]["children"][0]["text"] == "public"


def test_nested_datetime_is_utc_normalized_and_failed_parse_has_no_value() -> None:
    normalized = CentralDataNormalizer.normalize_value(
        {"when": [datetime(2026, 1, 1, 1, 0), datetime(2026, 1, 1, tzinfo=UTC)]}
    )
    assert normalized["when"][0].tzinfo is UTC
    source = SourceDefinition("source-a", "official", "https://example.com/data", "application/json", 60)
    from polymarket_alpha_lab.central_data_contracts import RawResponse
    raw = RawEventRow.from_contracts(
        source,
        RawResponse(
            200,
            {"content-type": "application/json"},
            b"{}",
            source.url_template,
            request_url=source.url_template,
            retrieval_time=datetime.now(UTC),
            content_type="application/json",
        ),
    )
    with pytest.raises(ValueError):
        CentralDataNormalizer.build_observation(
            source,
            raw.identity,
            observation_time=raw.retrieval_time,
            value={"fake": "value"},
            freshness=Freshness.UNKNOWN,
            parse_state=ParseState.FAILED,
            failure_status=FailureStatus.UNKNOWN,
            value_state=ObservationValueState.UNKNOWN,
        )
