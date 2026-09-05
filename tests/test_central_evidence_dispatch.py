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
    EvidenceBundleStatus,
    EvidenceItemAvailability,
    EvidenceItemRequirement,
    SelectedEvidence,
    ZeroWeightPlaceholder,
    typed_value_equality,
)
from polymarket_alpha_lab.central_evidence_dispatch import (
    BTC_ITEM_REQUIREMENTS,
    REQUIRED_ITEM_CATALOG,
    TeamRouting,
    build_evidence_bundle,
    route_team,
)


AS_OF = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
RETRIEVAL = datetime(2026, 9, 5, 11, 59, 30, tzinfo=UTC)


def source(source_id: str, family: str, *, policy_seconds: int = 300) -> SourceDefinition:
    return SourceDefinition(
        source_id=source_id,
        source_family=family,
        url_template=f"https://example.com/{source_id}",
        content_type="application/json",
        freshness_policy_seconds=policy_seconds,
    )


def _observation(
    src: SourceDefinition,
    value: object,
    *,
    observation_time: datetime = RETRIEVAL,
    parse_state: ParseState = ParseState.SUCCESS,
    value_state: ObservationValueState = ObservationValueState.PRESENT,
    body: bytes | None = None,
) -> NormalizedObservationRow:
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
    observation_contract = CentralDataNormalizer.build_observation(
        src,
        raw.identity,
        observation_time=observation_time,
        value=None if parse_state is not ParseState.SUCCESS else value,
        freshness=Freshness.FRESH,
        parse_state=parse_state,
        value_state=value_state,
        reason_codes=() if parse_state is ParseState.SUCCESS else ("synthetic_failure",),
    )
    return NormalizedObservationRow.from_contracts(src, observation_contract, raw.identity)


def test_all_ten_teams_route_supported() -> None:
    for team_id in REQUIRED_ITEM_CATALOG:
        routing = route_team(team_id)
        assert routing.supported is True, team_id
    assert set(REQUIRED_ITEM_CATALOG) == {
        "politics",
        "crypto_btc",
        "crypto_eth",
        "macro_rates",
        "equity_indices",
        "commodities_gold",
        "commodities_oil",
        "sports_soccer",
        "sports_basketball",
        "sports_other",
    }
    with pytest.raises(ValueError):
        route_team("not-a-team")


def test_unregistered_team_requirement_reports_unsupported() -> None:
    empty = SourceRegistry()
    empty.register(source("kraken_btc_ticker", "kraken_public"))
    routing = route_team("crypto_btc", empty)
    assert routing.supported is False
    assert routing.reason_codes == ("team_requirement_not_registered",)
    assert TeamRouting("crypto_btc", True).supported is True


def test_btc_bundle_ready_and_replayable() -> None:
    registry = SourceRegistry()
    kraken = source("kraken_btc_ticker", "kraken_public")
    gamma = source("polymarket_gamma_markets", "polymarket_gamma")
    clob = source("polymarket_clob_book", "polymarket_clob")
    for src in (kraken, gamma, clob):
        registry.register(src)
    by_source = {
        kraken.source_id: (_observation(kraken, {"last_price": Decimal("43000.5")}),),
        gamma.source_id: (_observation(gamma, {"question": "Will X happen?"}),),
        clob.source_id: (_observation(clob, {"bids": [{"price": Decimal("0.4")}]}),),
    }
    bundle = build_evidence_bundle(
        "crypto_btc",
        BTC_ITEM_REQUIREMENTS,
        by_source,
        registry,
        as_of=AS_OF,
        market_reference="will-x-happen",
    )
    assert bundle.status is EvidenceBundleStatus.READY
    assert all(type(item) is SelectedEvidence for item in bundle.items.values())
    assert set(bundle.items) == {"btc_spot_price", "gamma_market_metadata", "clob_book_depth"}
    replay = build_evidence_bundle(
        "crypto_btc",
        BTC_ITEM_REQUIREMENTS,
        by_source,
        registry,
        as_of=AS_OF,
        market_reference="will-x-happen",
    )
    assert replay.bundle_id == bundle.bundle_id
    assert replay == bundle


def test_blocked_paths_missing_stale_parse_unknown() -> None:
    registry = SourceRegistry()
    kraken = source("kraken_btc_ticker", "kraken_public")
    registry.register(kraken)

    missing = build_evidence_bundle(
        "crypto_btc",
        (BTC_ITEM_REQUIREMENTS[0],),
        {},
        registry,
        as_of=AS_OF,
    )
    assert missing.status is EvidenceBundleStatus.BLOCKED
    placeholder = missing.items["btc_spot_price"]
    assert type(placeholder) is ZeroWeightPlaceholder
    assert placeholder.availability is EvidenceItemAvailability.MISSING

    stale = build_evidence_bundle(
        "crypto_btc",
        (BTC_ITEM_REQUIREMENTS[0],),
        {
            kraken.source_id: (
                _observation(
                    kraken,
                    {"last_price": Decimal("1")},
                    observation_time=AS_OF - timedelta(seconds=301),
                ),
            )
        },
        registry,
        as_of=AS_OF,
    )
    assert stale.items["btc_spot_price"].availability is EvidenceItemAvailability.STALE

    item_tighter = EvidenceItemRequirement(
        item_name="btc_spot_price",
        source_ids=(kraken.source_id,),
        max_age_seconds=10,
    )
    tightened = build_evidence_bundle(
        "crypto_btc",
        (item_tighter,),
        {
            kraken.source_id: (
                _observation(
                    kraken,
                    {"last_price": Decimal("1")},
                    observation_time=AS_OF - timedelta(seconds=60),
                ),
            )
        },
        registry,
        as_of=AS_OF,
    )
    assert tightened.items["btc_spot_price"].availability is EvidenceItemAvailability.STALE

    parse_failed = build_evidence_bundle(
        "crypto_btc",
        (BTC_ITEM_REQUIREMENTS[0],),
        {
            kraken.source_id: (
                _observation(
                    kraken,
                    None,
                    parse_state=ParseState.FAILED,
                    value_state=ObservationValueState.NULL,
                ),
            )
        },
        registry,
        as_of=AS_OF,
    )
    assert parse_failed.items["btc_spot_price"].availability is EvidenceItemAvailability.PARSE_FAILED

    unknown = build_evidence_bundle(
        "crypto_btc",
        (BTC_ITEM_REQUIREMENTS[0],),
        {
            kraken.source_id: (
                _observation(
                    kraken,
                    None,
                    value_state=ObservationValueState.UNKNOWN,
                ),
            )
        },
        registry,
        as_of=AS_OF,
    )
    assert unknown.items["btc_spot_price"].availability is EvidenceItemAvailability.UNKNOWN_VALUE


def test_mirror_dedup_and_family_quorum_semantics() -> None:
    registry = SourceRegistry()
    mirror_a = source("mirror_a", "provider_family")
    mirror_b = source("mirror_b", "provider_family")
    independent = source("independent_b", "other_family")
    for src in (mirror_a, mirror_b, independent):
        registry.register(src)
    shared_body = b'{"identical": "payload"}'

    mirrors = build_evidence_bundle(
        "crypto_btc",
        (
            EvidenceItemRequirement(
                item_name="price",
                source_ids=(mirror_a.source_id, mirror_b.source_id),
                minimum_current_families=1,
            ),
        ),
        {
            mirror_a.source_id: (_observation(mirror_a, {"p": Decimal("1")}, body=shared_body),),
            mirror_b.source_id: (_observation(mirror_b, {"p": Decimal("1")}, body=shared_body),),
        },
        registry,
        as_of=AS_OF,
    )
    assert mirrors.status is EvidenceBundleStatus.READY
    assert "multi_family_corroboration" not in mirrors.reason_codes

    cross_family = build_evidence_bundle(
        "crypto_btc",
        (
            EvidenceItemRequirement(
                item_name="price",
                source_ids=(mirror_a.source_id, independent.source_id),
                minimum_current_families=2,
            ),
        ),
        {
            mirror_a.source_id: (_observation(mirror_a, {"p": Decimal("1")}, body=shared_body),),
            independent.source_id: (
                _observation(independent, {"p": Decimal("1")}, body=shared_body),
            ),
        },
        registry,
        as_of=AS_OF,
    )
    assert cross_family.status is EvidenceBundleStatus.READY
    assert "multi_family_corroboration" in cross_family.reason_codes

    single_family_quorum_two = build_evidence_bundle(
        "crypto_btc",
        (
            EvidenceItemRequirement(
                item_name="price",
                source_ids=(mirror_a.source_id, mirror_b.source_id),
                minimum_current_families=2,
            ),
        ),
        {
            mirror_a.source_id: (_observation(mirror_a, {"p": Decimal("1")}, body=shared_body),),
            mirror_b.source_id: (_observation(mirror_b, {"p": Decimal("1")}, body=shared_body),),
        },
        registry,
        as_of=AS_OF,
    )
    placeholder = single_family_quorum_two.items["price"]
    assert type(placeholder) is ZeroWeightPlaceholder
    assert placeholder.availability is EvidenceItemAvailability.QUORUM_NOT_MET
    assert placeholder.reason_codes == ("source_quorum_not_met",)


def test_contradiction_and_tie_break() -> None:
    registry = SourceRegistry()
    left = source("left_src", "left_family")
    right = source("right_src", "right_family")
    for src in (left, right):
        registry.register(src)

    contradiction = build_evidence_bundle(
        "crypto_btc",
        (
            EvidenceItemRequirement(
                item_name="price",
                source_ids=(left.source_id, right.source_id),
                minimum_current_families=1,
            ),
        ),
        {
            left.source_id: (_observation(left, {"p": Decimal("1")}),),
            right.source_id: (_observation(right, {"p": Decimal("2")}),),
        },
        registry,
        as_of=AS_OF,
    )
    placeholder = contradiction.items["price"]
    assert type(placeholder) is ZeroWeightPlaceholder
    assert placeholder.availability is EvidenceItemAvailability.CONTRADICTORY
    assert placeholder.reason_codes == ("contradictory_values",)
    assert len(placeholder.references) == 2

    first = _observation(left, {"p": Decimal("1")})
    second = _observation(left, {"p": Decimal("1")})
    tie = build_evidence_bundle(
        "crypto_btc",
        (
            EvidenceItemRequirement(
                item_name="price",
                source_ids=(left.source_id,),
                minimum_current_families=1,
            ),
        ),
        {left.source_id: (first, second)},
        registry,
        as_of=AS_OF,
    )
    selected = tie.items["price"]
    assert type(selected) is SelectedEvidence
    assert selected.observation_id == min(
        first.normalized_observation_id, second.normalized_observation_id
    )


def test_blocked_bundle_has_one_placeholder_per_item() -> None:
    registry = SourceRegistry()
    kraken = source("kraken_btc_ticker", "kraken_public")
    gamma = source("polymarket_gamma_markets", "polymarket_gamma")
    for src in (kraken, gamma):
        registry.register(src)
    bundle = build_evidence_bundle(
        "crypto_btc",
        BTC_ITEM_REQUIREMENTS[:2],
        {kraken.source_id: (_observation(kraken, {"last_price": Decimal("1")}),)},
        registry,
        as_of=AS_OF,
    )
    assert len(bundle.items) == 2
    assert sum(type(item) is ZeroWeightPlaceholder for item in bundle.items.values()) == 1
    assert bundle.status is EvidenceBundleStatus.BLOCKED
