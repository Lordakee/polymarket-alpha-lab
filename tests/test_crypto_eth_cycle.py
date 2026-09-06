from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.central_data_contracts import (
    ObservationValueState,
    ParseState,
    RawResponse,
    SourceDefinition,
)
from polymarket_alpha_lab.central_data_db_row import NormalizedObservationRow, RawEventRow
from polymarket_alpha_lab.central_data_normalization import CentralDataNormalizer
from polymarket_alpha_lab.central_data_registry import SourceRegistry
from polymarket_alpha_lab.central_evidence_bundle import (
    EvidenceBundle,
    EvidenceItemAvailability,
    ZeroWeightPlaceholder,
)
from polymarket_alpha_lab.central_evidence_dispatch import (
    ETH_ITEM_REQUIREMENTS,
    build_evidence_bundle,
    route_team,
)
from polymarket_alpha_lab.crypto_eth_team import CryptoEthTeamConfig
from polymarket_alpha_lab.crypto_research_cycle import run_crypto_research_cycle
from polymarket_alpha_lab.crypto_eth_evidence_adapter import adapt_eth_evidence
from polymarket_alpha_lab.crypto_eth_team import build_crypto_eth_team_forecast


AS_OF = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
RETRIEVAL = datetime(2026, 9, 6, 11, 59, 30, tzinfo=UTC)
CONFIG = CryptoEthTeamConfig(config_version="m5-test-v1")


def source(source_id: str, family: str) -> SourceDefinition:
    return SourceDefinition(
        source_id=source_id,
        source_family=family,
        url_template=f"https://example.com/{source_id}",
        content_type="application/json",
        freshness_policy_seconds=600,
    )


def registry() -> SourceRegistry:
    catalog = SourceRegistry()
    for source_id, family in (
        ("kraken_eth_ticker", "kraken_public"),
        ("polymarket_gamma_markets", "polymarket_gamma"),
        ("polymarket_clob_book", "polymarket_clob"),
    ):
        catalog.register(source(source_id, family))
    return catalog


def observation(src: SourceDefinition, value: object) -> NormalizedObservationRow:
    from polymarket_alpha_lab.central_data_contracts import Freshness

    response = RawResponse(
        200,
        {"content-type": "application/json"},
        b'{"synthetic": true}',
        src.url_template,
        retrieval_time=RETRIEVAL,
        request_url=src.url_template,
        content_type="application/json",
    )
    raw = RawEventRow.from_contracts(src, response)
    contract = CentralDataNormalizer.build_observation(
        src,
        raw.identity,
        observation_time=RETRIEVAL,
        value=value,
        freshness=Freshness.FRESH,
        parse_state=ParseState.SUCCESS,
        value_state=ObservationValueState.PRESENT,
    )
    return NormalizedObservationRow.from_contracts(src, contract, raw.identity)


def eth_rows():
    catalog = registry()
    metadata = observation(
        catalog.get("polymarket_gamma_markets"),
        {
            "condition_id": "0xeth",
            "question": "Will ETH close above 5k?",
            "slug": "eth-above-5k",
            "clob_token_ids": ["9", "10"],
            "outcomes": ["Yes", "No"],
        },
    )
    book = observation(
        catalog.get("polymarket_clob_book"),
        {
            "market": "0xeth",
            "asset_id": "9",
            "bids": [{"price": Decimal("0.45"), "size": Decimal("10")}],
            "asks": [{"price": Decimal("0.55"), "size": Decimal("10")}],
        },
    )
    spot = observation(
        catalog.get("kraken_eth_ticker"),
        {"last_price": Decimal("3010.5"), "ask_price": Decimal("3011"), "bid_price": Decimal("3010")},
    )
    return metadata, book, spot


def run_eth(*, metadata, book, spot, bundle=None, generated_at=AS_OF):
    catalog = registry()
    by_source = {
        "polymarket_gamma_markets": [metadata],
        "polymarket_clob_book": [book],
        "kraken_eth_ticker": [spot],
    }
    bundle = bundle or build_evidence_bundle(
        "crypto_eth", ETH_ITEM_REQUIREMENTS, by_source, catalog, as_of=AS_OF,
        market_reference="eth-above-5k",
    )
    return run_crypto_research_cycle(
        team_id="crypto_eth",
        spot_item="eth_spot_price",
        bundle=bundle,
        metadata_observation=metadata,
        book_observation=book,
        spot_observation=spot,
        as_of=AS_OF,
        generated_at=generated_at,
        config=CONFIG,
        adapt_evidence=adapt_eth_evidence,
        build_forecast=build_crypto_eth_team_forecast,
    )


def test_eth_ready_cycle_traverses_the_full_workflow() -> None:
    metadata, book, spot = eth_rows()
    result = run_eth(metadata=metadata, book=book, spot=spot)
    assert result.status == "ready"
    assert result.base_probability == Decimal("0.5")
    assert result.forecast.team_id == "crypto_eth"
    assert result.forecast.market_slug == "eth-above-5k"
    assert "eth_spot_price: ready via kraken_public" in result.operator_packet
    assert "forecast_p_yes: 0.5" in result.operator_packet


def test_eth_stale_missing_contradictory_blocked_traversals() -> None:
    catalog = registry()

    def bundle_with(spot_rows, book_rows):
        return build_evidence_bundle(
            "crypto_eth",
            ETH_ITEM_REQUIREMENTS,
            {
                "polymarket_gamma_markets": [eth_rows()[0]],
                "polymarket_clob_book": book_rows,
                "kraken_eth_ticker": spot_rows,
            },
            catalog,
            as_of=AS_OF,
            market_reference="eth-above-5k",
        )

    metadata, book, spot = eth_rows()

    stale_bundle = bundle_with(
        [_observation_at(catalog.get("kraken_eth_ticker"), AS_OF - timedelta(seconds=400))],
        [book],
    )
    stale_result = run_eth(
        metadata=metadata, book=book,
        spot=_observation_at(catalog.get("kraken_eth_ticker"), AS_OF - timedelta(seconds=400)),
        bundle=stale_bundle,
    )
    assert stale_result.status == "blocked"
    assert "bundle_blocked" in stale_result.reason_codes
    assert stale_bundle.items["eth_spot_price"].availability is EvidenceItemAvailability.STALE

    missing_result = run_eth(metadata=metadata, book=book, spot=None, bundle=bundle_with([], [book]))
    assert missing_result.status == "blocked"
    assert "spot_observation_missing" in missing_result.reason_codes

    contradictory_bundle = EvidenceBundle(
        team_id="crypto_eth",
        market_reference="eth-above-5k",
        as_of=AS_OF,
        reason_codes=("item_contradictory_values",),
        items={
            "eth_spot_price": ZeroWeightPlaceholder(
                item_name="eth_spot_price",
                availability=EvidenceItemAvailability.CONTRADICTORY,
                reason_codes=("contradictory_values",),
            ),
            "gamma_market_metadata": bundle_with([spot], [book]).items["gamma_market_metadata"],
            "clob_book_depth": bundle_with([spot], [book]).items["clob_book_depth"],
        },
    )
    contradictory = run_eth(
        metadata=metadata, book=book, spot=spot, bundle=contradictory_bundle,
    )
    assert contradictory.status == "blocked"
    assert "item_contradictory_values" in contradictory.reason_codes
    assert contradictory_bundle.items["eth_spot_price"].reason_codes == (
        "contradictory_values",
    )


def _observation_at(src, moment: datetime) -> NormalizedObservationRow:
    from polymarket_alpha_lab.central_data_contracts import Freshness

    response = RawResponse(
        200, {"content-type": "application/json"}, b'{"synthetic": true}',
        src.url_template, retrieval_time=moment, request_url=src.url_template,
        content_type="application/json",
    )
    raw = RawEventRow.from_contracts(src, response)
    contract = CentralDataNormalizer.build_observation(
        src, raw.identity, observation_time=moment,
        value={"last_price": Decimal("3010.5")}, freshness=Freshness.FRESH,
    )
    return NormalizedObservationRow.from_contracts(src, contract, raw.identity)


def test_btc_and_eth_team_ids_route_supported_and_others_refuse() -> None:
    assert route_team("crypto_eth").supported is True
    assert route_team("crypto_btc").supported is True
    with pytest.raises(ValueError):
        route_team("not-a-team")


def test_persisted_observed_baseline_is_book_midpoint_not_hint() -> None:
    metadata, book, spot = eth_rows()
    book_value = {"market": "0xeth", "asset_id": "9",
                  "bids": [{"price": Decimal("0.25"), "size": Decimal("5")}],
                  "asks": [{"price": Decimal("0.45"), "size": Decimal("5")}]}
    from polymarket_alpha_lab.central_data_contracts import Freshness, ObservationValueState, ParseState
    from polymarket_alpha_lab.central_data_contracts import RawResponse
    from polymarket_alpha_lab.central_data_db_row import RawEventRow

    catalog = registry()
    src = catalog.get("polymarket_clob_book")
    response = RawResponse(
        200, {"content-type": "application/json"}, b'{"b": 1}', src.url_template,
        retrieval_time=RETRIEVAL, request_url=src.url_template, content_type="application/json",
    )
    raw = RawEventRow.from_contracts(src, response)
    contract = CentralDataNormalizer.build_observation(
        src, raw.identity, observation_time=RETRIEVAL, value=book_value,
        freshness=Freshness.FRESH, parse_state=ParseState.SUCCESS,
        value_state=ObservationValueState.PRESENT,
    )
    from polymarket_alpha_lab.central_data_db_row import NormalizedObservationRow
    book = NormalizedObservationRow.from_contracts(src, contract, raw.identity)
    result = run_eth(metadata=metadata, book=book, spot=spot)
    assert result.status == "ready"
    assert result.base_probability == Decimal("0.35")
    assert result.forecast.market_implied_probability_observed == Decimal("0.35")
    assert result.forecast.selected_side == "yes"
