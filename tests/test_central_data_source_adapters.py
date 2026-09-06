from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

from polymarket_alpha_lab.central_data_contracts import (
    FailureStatus,
    Freshness,
    ParseState,
    RawResponse,
    RequestParamSpec,
    SourceDefinition,
)
from polymarket_alpha_lab.central_data_db_row import RawEventRow, TypedEnvelope


GAMMA = SourceDefinition(
    source_id="polymarket_gamma_markets",
    source_family="polymarket_gamma",
    url_template="https://gamma-api.polymarket.com/markets",
    content_type="application/json",
    freshness_policy_seconds=300,
    is_official=True,
    query_params=(
        RequestParamSpec("limit", "int_range", min_value=1, max_value=100),
        RequestParamSpec("offset", "int_range", min_value=0, max_value=100000),
    ),
)
CLOB = SourceDefinition(
    source_id="polymarket_clob_book",
    source_family="polymarket_clob",
    url_template="https://clob.polymarket.com/book",
    content_type="application/json",
    freshness_policy_seconds=30,
    is_official=True,
    query_params=(RequestParamSpec("token_id", "pattern", pattern=r"[0-9]{1,19}"),),
)
KRAKEN = SourceDefinition(
    source_id="kraken_btc_ticker",
    source_family="kraken_public",
    url_template="https://api.kraken.com/0/public/Ticker",
    content_type="application/json",
    freshness_policy_seconds=300,
    query_params=(RequestParamSpec("pair", "enum", required=True, choices=("XBTUSD",)),),
)


def _raw(source: SourceDefinition, body: bytes, *, retrieval: datetime | None = None) -> RawEventRow:
    moment = retrieval or datetime.now(UTC)
    response = RawResponse(
        200,
        {"content-type": "application/json"},
        body,
        source.url_template,
        retrieval_time=moment,
        request_url=source.url_template,
        content_type="application/json",
    )
    return RawEventRow.from_contracts(source, response)


def _gamma_market_body(**overrides: object) -> bytes:
    market = {
        "id": "0xabc",
        "conditionId": "0x1234",
        "question": "Will X happen?",
        "slug": "will-x-happen",
        "endDate": "2026-12-31T00:00:00Z",
        "active": True,
        "closed": False,
        "volume24hr": 12345.67,
        "liquidity": "98765.43",
        "outcomePrices": '["0.6", "0.4"]',
        "outcomes": '["Yes", "No"]',
        "extraIgnored": {"nested": 1},
    }
    market.update(overrides)
    return json.dumps([market]).encode("utf-8")


def test_gamma_adapter_happy_path_and_determinism() -> None:
    from polymarket_alpha_lab.central_data_source_adapters import parse_gamma_markets

    raw = _raw(GAMMA, _gamma_market_body())
    rows = parse_gamma_markets(GAMMA, raw)
    assert len(rows) == 1
    row = rows[0]
    assert row.parse_state == ParseState.SUCCESS.value
    assert row.freshness_state == Freshness.FRESH.value
    value = TypedEnvelope.decode(dict(row.typed_value))
    assert value["condition_id"] == "0x1234"
    assert value["outcome_prices"] == ["0.6", "0.4"]
    assert rows == parse_gamma_markets(GAMMA, raw)


def test_gamma_adapter_extracts_only_one_canonical_event_lineage() -> None:
    from polymarket_alpha_lab.central_data_source_adapters import parse_gamma_markets

    cases = (
        (
            {"events": [{"id": "event-1", "slug": "event-one"}]},
            "verified",
            "event-1",
        ),
        ({"events": []}, "missing_event", None),
        (
            {"events": [{"id": "event-1", "slug": "one"}, {"id": "event-2", "slug": "two"}]},
            "ambiguous_events",
            None,
        ),
        ({"events": [{"id": 7, "slug": "event-one"}]}, "malformed_event", None),
        (
            {
                "events": [{"id": "event-1", "slug": "event-one"}],
                "endDate": "not-a-timestamp",
            },
            "malformed_event",
            None,
        ),
    )
    for overrides, expected_state, expected_event_id in cases:
        row = parse_gamma_markets(
            GAMMA, _raw(GAMMA, _gamma_market_body(**overrides))
        )[0]
        value = TypedEnvelope.decode(dict(row.typed_value))
        assert value["event_lineage_state"] == expected_state
        assert value["event_id"] == expected_event_id
        if expected_state == "verified":
            assert value["event_slug"] == "event-one"
            assert value["market_end_at"] == datetime(2026, 12, 31, tzinfo=UTC)
        else:
            assert value["event_slug"] is None
            assert value["market_end_at"] is None


def test_gamma_adapter_drift_cases() -> None:
    from polymarket_alpha_lab.central_data_source_adapters import parse_gamma_markets

    missing = _raw(GAMMA, _gamma_market_body(conditionId=None))
    assert parse_gamma_markets(GAMMA, missing)[0].reason_codes == ("missing_required_field",)

    mismatched = _raw(GAMMA, _gamma_market_body(question=7))
    assert parse_gamma_markets(GAMMA, mismatched)[0].reason_codes == ("type_mismatch",)

    bad_embedded = _raw(GAMMA, _gamma_market_body(outcomePrices="not json"))
    row = parse_gamma_markets(GAMMA, bad_embedded)[0]
    assert row.parse_state == ParseState.SUCCESS.value
    assert row.reason_codes == ("embedded_json_invalid",)
    assert "outcome_prices" not in dict(row.typed_value)

    not_array = _raw(GAMMA, b'{"object": true}')
    assert parse_gamma_markets(GAMMA, not_array)[0].reason_codes == ("type_mismatch",)

    not_json = _raw(GAMMA, b"<html>not json</html>")
    assert parse_gamma_markets(GAMMA, not_json)[0].reason_codes == ("json_parse_failed",)


def test_clob_adapter_uses_content_timestamp_for_freshness() -> None:
    from polymarket_alpha_lab.central_data_source_adapters import parse_clob_book

    retrieval = datetime(2026, 9, 5, 12, 0, 10, tzinfo=UTC)
    epoch = int(retrieval.timestamp()) - 5
    body = {
        "market": "0xmarket",
        "asset_id": "12345",
        "timestamp": str(epoch),
        "bids": [{"price": "0.40", "size": "120"}],
        "asks": [{"price": "0.60", "size": "80"}],
        "hash": "0xhash",
        "extraIgnored": 1,
    }
    raw = _raw(CLOB, json.dumps(body).encode(), retrieval=retrieval)
    rows = parse_clob_book(CLOB, raw)
    assert rows[0].parse_state == ParseState.SUCCESS.value
    assert rows[0].freshness_state == Freshness.FRESH.value
    assert rows[0].observation_time == datetime.fromtimestamp(epoch, tz=UTC)
    value = TypedEnvelope.decode(dict(rows[0].typed_value))
    assert value["bids"] == [{"price": Decimal("0.40"), "size": Decimal("120")}]

    stale_epoch = int(retrieval.timestamp()) - 600
    body["timestamp"] = str(stale_epoch)
    raw_stale = _raw(CLOB, json.dumps(body).encode(), retrieval=retrieval)
    assert parse_clob_book(CLOB, raw_stale)[0].freshness_state == Freshness.STALE.value

    body["timestamp"] = "not-a-number"
    raw_invalid = _raw(CLOB, json.dumps(body).encode(), retrieval=retrieval)
    row = parse_clob_book(CLOB, raw_invalid)[0]
    assert row.reason_codes == ("invalid_content_timestamp",)
    assert row.observation_time == retrieval


def test_clob_adapter_drift_cases() -> None:
    from polymarket_alpha_lab.central_data_source_adapters import parse_clob_book

    def body(**overrides: object) -> bytes:
        payload = {
            "market": "0xmarket",
            "asset_id": "1",
            "bids": [{"price": "0.4", "size": "10"}],
            "asks": [{"price": "0.6", "size": "10"}],
        }
        payload.update(overrides)
        return json.dumps(payload).encode()

    assert parse_clob_book(CLOB, _raw(CLOB, body(asset_id=None)))[0].reason_codes == (
        "missing_required_field",
    )
    assert parse_clob_book(CLOB, _raw(CLOB, body(market=5)))[0].reason_codes == ("type_mismatch",)
    assert parse_clob_book(CLOB, _raw(CLOB, body(bids=[{"price": "cheap", "size": "1"}])))[0].reason_codes == (
        "type_mismatch",
    )
    assert parse_clob_book(CLOB, _raw(CLOB, b"[]"))[0].reason_codes == ("type_mismatch",)


def test_every_acquired_default_source_has_a_parser() -> None:
    from polymarket_alpha_lab.central_data_registry import DEFAULT_SOURCE_DEFINITIONS
    from polymarket_alpha_lab.central_data_source_adapters import SOURCE_PARSERS

    acquired_source_ids = {
        "polymarket_gamma_markets",
        "polymarket_clob_book",
        "kraken_btc_ticker",
        "kraken_eth_ticker",
    }
    registered = {source.source_id for source in DEFAULT_SOURCE_DEFINITIONS}
    assert acquired_source_ids <= registered
    assert acquired_source_ids <= SOURCE_PARSERS.keys()


def test_both_kraken_sources_share_the_public_ticker_parser() -> None:
    from polymarket_alpha_lab.central_data_source_adapters import (
        SOURCE_PARSERS,
        parse_kraken_ticker,
    )

    assert SOURCE_PARSERS["kraken_btc_ticker"] is parse_kraken_ticker
    assert SOURCE_PARSERS["kraken_eth_ticker"] is parse_kraken_ticker


def test_kraken_adapter_happy_path_and_failures() -> None:
    from polymarket_alpha_lab.central_data_source_adapters import parse_kraken_ticker

    body = {
        "error": [],
        "result": {
            "XXBTZUSD": {
                "a": ["43300.1", "3", "1690900000.123456"],
                "b": ["43299.9", "1", "1690900000.1"],
                "c": ["43300.0", "0.01"],
                "v": ["1200", "3100"],
            }
        },
    }
    raw = _raw(KRAKEN, json.dumps(body).encode())
    rows = parse_kraken_ticker(KRAKEN, raw)
    assert rows[0].parse_state == ParseState.SUCCESS.value
    value = TypedEnvelope.decode(dict(rows[0].typed_value))
    assert value["last_price"] == Decimal("43300.0")
    assert value["ask_price"] == Decimal("43300.1")
    assert value["bid_price"] == Decimal("43299.9")

    provider_error = {"error": ["EQuery:Unknown asset pair"], "result": {}}
    assert parse_kraken_ticker(KRAKEN, _raw(KRAKEN, json.dumps(provider_error).encode()))[0].reason_codes == (
        "provider_error",
    )
    empty = {"error": [], "result": {}}
    assert parse_kraken_ticker(KRAKEN, _raw(KRAKEN, json.dumps(empty).encode()))[0].reason_codes == (
        "missing_required_field",
    )
    bad_price = {"error": [], "result": {"XXBTZUSD": {"a": ["x"], "b": ["1"], "c": ["1"]}}}
    assert parse_kraken_ticker(KRAKEN, _raw(KRAKEN, json.dumps(bad_price).encode()))[0].reason_codes == (
        "type_mismatch",
    )


def test_null_and_unknown_states_survive_the_envelope() -> None:
    from polymarket_alpha_lab.central_data_source_adapters import parse_gamma_markets
    from polymarket_alpha_lab.central_data_db_row import TypedEnvelope

    raw = _raw(GAMMA, _gamma_market_body(active=None, endDate=None))
    row = parse_gamma_markets(GAMMA, raw)[0]
    value = TypedEnvelope.decode(dict(row.typed_value))
    assert value["active"] is None
    assert value["end_date_iso"] is None
    assert value["condition_id"] == "0x1234"


def test_gamma_adapter_extracts_volume_and_liquidity_as_decimals() -> None:
    from polymarket_alpha_lab.central_data_db_row import TypedEnvelope
    from polymarket_alpha_lab.central_data_source_adapters import parse_gamma_markets

    raw = _raw(GAMMA, _gamma_market_body())
    row = parse_gamma_markets(GAMMA, raw)[0]
    value = TypedEnvelope.decode(dict(row.typed_value))
    assert value["volume24hr"] == Decimal("12345.67")
    assert value["liquidity"] == Decimal("98765.43")

    missing = _raw(GAMMA, _gamma_market_body(volume24hr=None, liquidity=None))
    value = TypedEnvelope.decode(dict(parse_gamma_markets(GAMMA, missing)[0].typed_value))
    assert value["volume24hr"] is None and value["liquidity"] is None
