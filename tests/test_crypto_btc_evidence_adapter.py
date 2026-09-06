from datetime import UTC, datetime
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
    EvidenceBundleStatus,
    EvidenceItemAvailability,
    ZeroWeightPlaceholder,
)
from polymarket_alpha_lab.central_evidence_dispatch import (
    BTC_ITEM_REQUIREMENTS,
    build_evidence_bundle,
)
from polymarket_alpha_lab.crypto_btc_evidence_adapter import adapt_btc_evidence


AS_OF = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
RETRIEVAL = datetime(2026, 9, 5, 11, 59, 30, tzinfo=UTC)


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


def ready_inputs() -> tuple[dict, dict]:
    catalog = registry()
    metadata = observation(
        catalog.get("polymarket_gamma_markets"),
        {
            "condition_id": "0xabc",
            "question": "Will BTC close above 100k?",
            "slug": "btc-above-100k",
            "clob_token_ids": ["123", "456"],
            "outcomes": ["Yes", "No"],
        },
    )
    book = observation(
        catalog.get("polymarket_clob_book"),
        {
            "market": "0xabc",
            "asset_id": "123",
            "bids": [{"price": Decimal("0.40"), "size": Decimal("10")}],
            "asks": [{"price": Decimal("0.60"), "size": Decimal("10")}],
        },
    )
    spot = observation(
        catalog.get("kraken_btc_ticker"),
        {"last_price": Decimal("43000.5"), "ask_price": Decimal("43001"), "bid_price": Decimal("43000")},
    )
    by_source = {
        "polymarket_gamma_markets": [metadata],
        "polymarket_clob_book": [book],
        "kraken_btc_ticker": [spot],
    }
    rows = {"gamma_market_metadata": metadata, "clob_book_depth": book, "btc_spot_price": spot}
    return by_source, rows


def ready_bundle():
    by_source, rows = ready_inputs()
    bundle = build_evidence_bundle(
        "crypto_btc",
        BTC_ITEM_REQUIREMENTS,
        by_source,
        registry(),
        as_of=AS_OF,
        market_reference="btc-above-100k",
    )
    return bundle, rows


def test_adapter_maps_ready_items_with_zero_impact() -> None:
    bundle, rows = ready_bundle()
    adaptation = adapt_btc_evidence(bundle, observations_by_item=rows, as_of=AS_OF)
    assert len(adaptation.inputs) == 3
    assert all(item.probability_impact == Decimal("0") for item in adaptation.inputs)
    assert all(item.weight == Decimal("0.5") for item in adaptation.inputs)
    spot = next(item for item in adaptation.inputs if "btc_spot_price" in item.evidence_type)
    assert "43000.5" in spot.evidence_text
    assert "kraken_public" in spot.evidence_text


def test_adapter_maps_blocked_items_to_zero_weight_reason_rows() -> None:
    placeholder = ZeroWeightPlaceholder(
        item_name="btc_spot_price",
        availability=EvidenceItemAvailability.STALE,
        reason_codes=("item_stale",),
    )
    bundle = EvidenceBundle(
        team_id="crypto_btc",
        market_reference="btc-above-100k",
        as_of=AS_OF,
        items={"btc_spot_price": placeholder},
    )
    adaptation = adapt_btc_evidence(bundle, observations_by_item={}, as_of=AS_OF)
    assert len(adaptation.inputs) == 1
    blocked = adaptation.inputs[0]
    assert blocked.weight == Decimal("0")
    assert blocked.probability_impact == Decimal("0")
    assert blocked.reason_codes == ("item_stale",)
    assert "stale" in blocked.evidence_text


def test_adapter_maps_missing_selected_rows_to_zero_weight() -> None:
    bundle, _rows = ready_bundle()
    empty = EvidenceBundle(
        team_id="crypto_btc",
        market_reference=None,
        as_of=AS_OF,
        items={"btc_spot_price": bundle.items["btc_spot_price"]},
    )
    adaptation = adapt_btc_evidence(empty, observations_by_item={}, as_of=AS_OF)
    assert adaptation.inputs[0].reason_codes == ("selected_observation_unavailable",)
    assert adaptation.inputs[0].weight == Decimal("0")


def test_adapter_rejects_foreign_teams() -> None:
    bundle, _rows = ready_bundle()
    foreign = EvidenceBundle(
        team_id="crypto_eth",
        market_reference=None,
        as_of=AS_OF,
        items={"btc_spot_price": bundle.items["btc_spot_price"]},
    )
    with pytest.raises(ValueError, match="crypto_btc"):
        adapt_btc_evidence(foreign, observations_by_item={}, as_of=AS_OF)
