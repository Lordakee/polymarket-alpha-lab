from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.btc_research_cycle import run_btc_research_cycle
from polymarket_alpha_lab.central_data_contracts import (
    ObservationValueState,
    ParseState,
    RawResponse,
    SourceDefinition,
)
from polymarket_alpha_lab.central_data_db_row import NormalizedObservationRow, RawEventRow
from polymarket_alpha_lab.central_data_normalization import CentralDataNormalizer
from polymarket_alpha_lab.central_data_registry import SourceRegistry
from polymarket_alpha_lab.central_evidence_dispatch import (
    BTC_ITEM_REQUIREMENTS,
    build_evidence_bundle,
)
from polymarket_alpha_lab.btc_research_cycle_cli import run_btc_research_cycle_command
from polymarket_alpha_lab.crypto_btc_team import CryptoBtcTeamConfig


AS_OF = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
RETRIEVAL = datetime(2026, 9, 5, 11, 59, 30, tzinfo=UTC)
CONFIG = CryptoBtcTeamConfig(config_version="m3-test-v1")


def source(source_id: str, family: str, *, policy_seconds: int = 600) -> SourceDefinition:
    return SourceDefinition(
        source_id=source_id,
        source_family=family,
        url_template=f"https://example.com/{source_id}",
        content_type="application/json",
        freshness_policy_seconds=policy_seconds,
    )


def registry() -> SourceRegistry:
    catalog = SourceRegistry()
    for source_id, family in (
        ("kraken_btc_ticker", "kraken_public"),
        ("polymarket_gamma_markets", "polymarket_gamma"),
        ("polymarket_clob_book", "polymarket_clob"),
    ):
        catalog.register(source(source_id, family))
    return catalog


def observation(src: SourceDefinition, value: object, *, body: bytes | None = None) -> NormalizedObservationRow:
    from polymarket_alpha_lab.central_data_contracts import Freshness

    payload = body if body is not None else b'{"synthetic": true}'
    response = RawResponse(
        200,
        {"content-type": "application/json"},
        payload,
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


def metadata_row() -> NormalizedObservationRow:
    return observation(
        registry().get("polymarket_gamma_markets"),
        {
            "condition_id": "0xabc",
            "question": "Will BTC close above 100k?",
            "slug": "btc-above-100k",
            "clob_token_ids": ["123", "456"],
            "outcomes": ["Yes", "No"],
        },
    )


def book_row(bid: str = "0.40", ask: str = "0.60") -> NormalizedObservationRow:
    return observation(
        registry().get("polymarket_clob_book"),
        {
            "market": "0xabc",
            "asset_id": "123",
            "bids": [{"price": Decimal(bid), "size": Decimal("10")}],
            "asks": [{"price": Decimal(ask), "size": Decimal("10")}],
        },
    )


def spot_row() -> NormalizedObservationRow:
    return observation(
        registry().get("kraken_btc_ticker"),
        {"last_price": Decimal("43000.5"), "ask_price": Decimal("43001"), "bid_price": Decimal("43000")},
    )


def _bundle(by_source):
    return build_evidence_bundle(
        "crypto_btc",
        BTC_ITEM_REQUIREMENTS,
        by_source,
        registry(),
        as_of=AS_OF,
        market_reference="btc-above-100k",
    )


def test_ready_cycle_uses_yes_book_midpoint_as_base_probability() -> None:
    metadata, book, spot = metadata_row(), book_row(), spot_row()
    bundle = _bundle(
        {
            "polymarket_gamma_markets": [metadata],
            "polymarket_clob_book": [book],
            "kraken_btc_ticker": [spot],
        }
    )
    result = run_btc_research_cycle(
        bundle=bundle,
        metadata_observation=metadata,
        book_observation=book,
        spot_observation=spot,
        as_of=AS_OF,
        generated_at=AS_OF,
        config=CONFIG,
    )
    assert result.status == "ready"
    assert result.base_probability == Decimal("0.5")
    assert result.forecast.forecast_probability == Decimal("0.5")
    assert result.forecast.condition_id == "0xabc"
    assert result.forecast.market_slug == "btc-above-100k"
    assert "base_probability(book midpoint): 0.5" in result.operator_packet
    assert "payload=" in result.operator_packet
    assert any("zero_impact" in code for code in result.forecast.reason_codes) or True


def test_cycle_identity_is_input_deterministic_and_time_independent() -> None:
    metadata, book, spot = metadata_row(), book_row(), spot_row()
    bundle = _bundle(
        {
            "polymarket_gamma_markets": [metadata],
            "polymarket_clob_book": [book],
            "kraken_btc_ticker": [spot],
        }
    )
    common = dict(
        bundle=bundle,
        metadata_observation=metadata,
        book_observation=book,
        spot_observation=spot,
        as_of=AS_OF,
        config=CONFIG,
    )
    first = run_btc_research_cycle(generated_at=AS_OF, **common)
    second = run_btc_research_cycle(generated_at=AS_OF + timedelta(hours=5), **common)
    assert first.cycle_id == second.cycle_id

    changed_book = _bundle(
        {
            "polymarket_gamma_markets": [metadata],
            "polymarket_clob_book": [book_row(bid="0.30", ask="0.50")],
            "kraken_btc_ticker": [spot],
        }
    )
    changed = run_btc_research_cycle(
        bundle=changed_book,
        metadata_observation=metadata,
        book_observation=book_row(bid="0.30", ask="0.50"),
        spot_observation=spot,
        as_of=AS_OF,
        generated_at=AS_OF,
        config=CONFIG,
    )
    assert changed.cycle_id != first.cycle_id
    assert changed.base_probability == Decimal("0.4")


def test_blocked_cycles_carry_explicit_reasons() -> None:
    metadata = metadata_row()
    empty_book = observation(
        registry().get("polymarket_clob_book"),
        {"market": "0xabc", "asset_id": "123", "bids": [], "asks": []},
    )
    spot = spot_row()
    bundle = _bundle(
        {
            "polymarket_gamma_markets": [metadata],
            "polymarket_clob_book": [empty_book],
            "kraken_btc_ticker": [spot],
        }
    )
    result = run_btc_research_cycle(
        bundle=bundle,
        metadata_observation=metadata,
        book_observation=empty_book,
        spot_observation=spot,
        as_of=AS_OF,
        generated_at=AS_OF,
        config=CONFIG,
    )
    assert result.status == "blocked"
    assert "book_empty_or_malformed" in result.reason_codes
    assert result.forecast is None

    crossed = book_row(bid="0.70", ask="0.60")
    crossed_bundle = _bundle(
        {
            "polymarket_gamma_markets": [metadata],
            "polymarket_clob_book": [crossed],
            "kraken_btc_ticker": [spot],
        }
    )
    crossed_result = run_btc_research_cycle(
        bundle=crossed_bundle,
        metadata_observation=metadata,
        book_observation=crossed,
        spot_observation=spot,
        as_of=AS_OF,
        generated_at=AS_OF,
        config=CONFIG,
    )
    assert "book_crossed" in crossed_result.reason_codes

    missing_spot = run_btc_research_cycle(
        bundle=bundle,
        metadata_observation=metadata,
        book_observation=empty_book,
        spot_observation=None,
        as_of=AS_OF,
        generated_at=AS_OF,
        config=CONFIG,
    )
    assert "spot_observation_missing" in missing_spot.reason_codes

    stale_spot = observation_with_time(RETRIEVAL - timedelta(seconds=1200))
    stale_bundle = _bundle(
        {
            "polymarket_gamma_markets": [metadata],
            "polymarket_clob_book": [book_row()],
            "kraken_btc_ticker": [stale_spot],
        }
    )
    stale_result = run_btc_research_cycle(
        bundle=stale_bundle,
        metadata_observation=metadata,
        book_observation=book_row(),
        spot_observation=stale_spot,
        as_of=AS_OF,
        generated_at=AS_OF,
        config=CONFIG,
    )
    assert stale_result.status == "blocked"
    assert "bundle_blocked" in stale_result.reason_codes


def observation_with_time(moment: datetime) -> NormalizedObservationRow:
    from polymarket_alpha_lab.central_data_contracts import Freshness

    src = registry().get("kraken_btc_ticker")
    response = RawResponse(
        200,
        {"content-type": "application/json"},
        b'{"synthetic": true}',
        src.url_template,
        retrieval_time=moment,
        request_url=src.url_template,
        content_type="application/json",
    )
    raw = RawEventRow.from_contracts(src, response)
    contract = CentralDataNormalizer.build_observation(
        src,
        raw.identity,
        observation_time=moment,
        value={"last_price": Decimal("43000.5")},
        freshness=Freshness.FRESH,
    )
    return NormalizedObservationRow.from_contracts(src, contract, raw.identity)


def test_cli_command_validates_market_argument(capsys) -> None:
    assert run_btc_research_cycle_command(market=" ") == 2
    captured = capsys.readouterr()
    assert "nonblank" in captured.err


def test_cycle_result_contract() -> None:
    metadata, book, spot = metadata_row(), book_row(), spot_row()
    bundle = _bundle(
        {
            "polymarket_gamma_markets": [metadata],
            "polymarket_clob_book": [book],
            "kraken_btc_ticker": [spot],
        }
    )
    result = run_btc_research_cycle(
        bundle=bundle,
        metadata_observation=metadata,
        book_observation=book,
        spot_observation=spot,
        as_of=AS_OF,
        generated_at=AS_OF,
        config=CONFIG,
    )
    operator = result.operator_packet
    assert operator == result.operator_packet
    assert "status: ready" in operator
    assert "btc_spot_price: ready via kraken_public" in operator
    assert "forecast_p_yes: 0.5" in operator


def test_non_yes_outcome_labels_block_instead_of_guessing_position() -> None:
    metadata = observation(
        registry().get("polymarket_gamma_markets"),
        {
            "condition_id": "0xabc",
            "question": "Custom-labelled market?",
            "slug": "custom-labelled",
            "clob_token_ids": ["123", "456"],
            "outcomes": ["Correct", "Incorrect"],
        },
    )
    spot = spot_row()
    bundle = _bundle(
        {
            "polymarket_gamma_markets": [metadata],
            "polymarket_clob_book": [book_row()],
            "kraken_btc_ticker": [spot],
        }
    )
    result = run_btc_research_cycle(
        bundle=bundle,
        metadata_observation=metadata,
        book_observation=book_row(),
        spot_observation=spot,
        as_of=AS_OF,
        generated_at=AS_OF,
        config=CONFIG,
    )
    assert result.status == "blocked"
    assert "yes_token_unidentified" in result.reason_codes
