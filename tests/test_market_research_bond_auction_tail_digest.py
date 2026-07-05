from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_bond_auction_tail_digest import (
    DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION,
    MarketResearchBondAuctionTailDigestAuction,
    MarketResearchBondAuctionTailDigestConfig,
    MarketResearchBondAuctionTailDigestReasonCodeCount,
    MarketResearchBondAuctionTailDigestReport,
    MarketResearchBondAuctionTailDigestRow,
    build_market_research_bond_auction_tail_digest,
    market_research_bond_auction_tail_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def test_tail_digest_flags_tail_risk_and_sorts_deterministically() -> None:
    report = build_market_research_bond_auction_tail_digest(
        (
            _auction(
                auction_id="auction-pass",
                security_term="10y",
                auctioned_at=datetime(2026, 7, 1, 13, 0, tzinfo=timezone(timedelta(hours=-4))),
                tail_bps=Decimal("0.4"),
                bid_to_cover_ratio=Decimal("2.650"),
                indirect_bidder_pct=Decimal("70.0000"),
            ),
            _auction(
                auction_id="auction-blocked",
                security_term="30y",
                auctioned_at=datetime(2026, 7, 2, 17, 0, tzinfo=UTC),
                tail_bps=Decimal("4.2"),
                bid_to_cover_ratio=Decimal("1.900"),
                indirect_bidder_pct=Decimal("52.0000"),
                high_yield_pct=Decimal("4.6500"),
                when_issued_yield_pct=Decimal("4.6080"),
            ),
            _auction(
                auction_id="auction-watch",
                security_term="5y",
                auctioned_at=datetime(2026, 7, 3, 9, 30, tzinfo=timezone(timedelta(hours=2))),
                tail_bps=Decimal("1.6"),
                bid_to_cover_ratio=Decimal("2.080"),
                indirect_bidder_pct=Decimal("60.0000"),
            ),
        ),
        config=MarketResearchBondAuctionTailDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketResearchBondAuctionTailDigestReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.digest_next_step == "review_bond_auction_tail_risk"
    assert report.auction_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.blocked_count == Decimal("1.000000")
    assert report.tail_event_count == Decimal("2.000000")
    assert report.weak_demand_count == Decimal("2.000000")
    assert report.low_indirect_bidder_count == Decimal("1.000000")
    assert report.max_tail_bps == Decimal("4.200000")
    assert report.average_tail_bps == Decimal("2.066667")
    assert report.average_bid_to_cover_ratio == Decimal("2.210000")
    assert report.tail_event_ratio == Decimal("0.666667")
    assert report.reason_codes == ("bond_auction_tail_digest_blocked",)
    assert report.reason_code_counts == (
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code="auction_tail_blocked",
            count=Decimal("1.000000"),
        ),
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code="auction_tail_passed",
            count=Decimal("1.000000"),
        ),
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code="auction_tail_watch",
            count=Decimal("1.000000"),
        ),
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code="low_indirect_bidder_share",
            count=Decimal("1.000000"),
        ),
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code="positive_auction_tail",
            count=Decimal("2.000000"),
        ),
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code="weak_bid_to_cover",
            count=Decimal("2.000000"),
        ),
    )
    assert report.rows == (
        MarketResearchBondAuctionTailDigestRow(
            auction_id="auction-blocked",
            security_term="30y",
            auctioned_at=datetime(2026, 7, 2, 17, 0, tzinfo=UTC),
            tail_bps=Decimal("4.200000"),
            bid_to_cover_ratio=Decimal("1.900000"),
            indirect_bidder_pct=Decimal("52.000000"),
            high_yield_pct=Decimal("4.650000"),
            when_issued_yield_pct=Decimal("4.608000"),
            tail_status="blocked",
            reason_codes=(
                "auction_tail_blocked",
                "low_indirect_bidder_share",
                "positive_auction_tail",
                "weak_bid_to_cover",
            ),
        ),
        MarketResearchBondAuctionTailDigestRow(
            auction_id="auction-watch",
            security_term="5y",
            auctioned_at=datetime(2026, 7, 3, 7, 30, tzinfo=UTC),
            tail_bps=Decimal("1.600000"),
            bid_to_cover_ratio=Decimal("2.080000"),
            indirect_bidder_pct=Decimal("60.000000"),
            high_yield_pct=Decimal("4.600000"),
            when_issued_yield_pct=Decimal("4.584000"),
            tail_status="watch",
            reason_codes=(
                "auction_tail_watch",
                "positive_auction_tail",
                "weak_bid_to_cover",
            ),
        ),
        MarketResearchBondAuctionTailDigestRow(
            auction_id="auction-pass",
            security_term="10y",
            auctioned_at=datetime(2026, 7, 1, 17, 0, tzinfo=UTC),
            tail_bps=Decimal("0.400000"),
            bid_to_cover_ratio=Decimal("2.650000"),
            indirect_bidder_pct=Decimal("70.000000"),
            high_yield_pct=Decimal("4.600000"),
            when_issued_yield_pct=Decimal("4.596000"),
            tail_status="pass",
            reason_codes=("auction_tail_passed",),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    serialized = repr(asdict(report)).lower()
    assert "buy" not in serialized
    assert "sell" not in serialized
    assert "trade" not in serialized
    assert "wallet" not in serialized
    assert "order" not in serialized
    assert "position" not in serialized


def test_empty_inputs_block_with_decimal_zeroes_and_no_rows() -> None:
    report = build_market_research_bond_auction_tail_digest(
        (),
        config=MarketResearchBondAuctionTailDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.digest_next_step == "review_bond_auction_tail_risk"
    assert report.auction_count == Decimal("0.000000")
    assert report.pass_count == Decimal("0.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.blocked_count == Decimal("0.000000")
    assert report.tail_event_count == Decimal("0.000000")
    assert report.weak_demand_count == Decimal("0.000000")
    assert report.low_indirect_bidder_count == Decimal("0.000000")
    assert report.max_tail_bps == Decimal("0.000000")
    assert report.average_tail_bps == Decimal("0.000000")
    assert report.average_bid_to_cover_ratio == Decimal("0.000000")
    assert report.tail_event_ratio == Decimal("0.000000")
    assert report.reason_codes == ("bond_auction_tail_digest_no_inputs",)
    assert report.reason_code_counts == (
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code="bond_auction_tail_digest_no_inputs",
            count=Decimal("1.000000"),
        ),
    )
    assert report.rows == ()


def test_payload_serializes_decimal_numerics_as_six_decimal_strings() -> None:
    report = build_market_research_bond_auction_tail_digest(
        (
            _auction(
                auction_id="auction-watch",
                auctioned_at=datetime(2026, 7, 3, 14, 30, tzinfo=timezone(timedelta(hours=2))),
                tail_bps=Decimal("1.230000"),
                bid_to_cover_ratio=Decimal("2.0800001"),
                indirect_bidder_pct=Decimal("60.1234567"),
                high_yield_pct=Decimal("4.600000"),
                when_issued_yield_pct=Decimal("4.587700"),
            ),
        ),
        config=MarketResearchBondAuctionTailDigestConfig(),
        generated_at=GENERATED_AT,
    )
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_bond_auction_tail_digest",
    )

    payload = module.market_research_bond_auction_tail_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["auction_count"] == "1.000000"
    assert payload["tail_event_ratio"] == "1.000000"
    assert payload["rows"][0]["auctioned_at"] == "2026-07-03T12:30:00+00:00"
    assert payload["rows"][0]["tail_bps"] == "1.230000"
    assert payload["rows"][0]["bid_to_cover_ratio"] == "2.080000"
    assert payload["rows"][0]["indirect_bidder_pct"] == "60.123457"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    _assert_no_float_or_decimal_payload(payload)


def test_payload_rejects_tampered_false_report_flags() -> None:
    report = build_market_research_bond_auction_tail_digest(
        (_auction(),),
        config=MarketResearchBondAuctionTailDigestConfig(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report, "report_only", False)

    with pytest.raises(ValueError, match="report_only"):
        market_research_bond_auction_tail_digest_payload(report)


def test_payload_rejects_tampered_nested_public_values() -> None:
    report = build_market_research_bond_auction_tail_digest(
        (_auction(),),
        config=MarketResearchBondAuctionTailDigestConfig(),
        generated_at=GENERATED_AT,
    )

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_bond_auction_tail_digest_payload(report)
    object.__setattr__(report.rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_bond_auction_tail_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "paper_only", True)

    object.__setattr__(report.rows[0], "tail_bps", Decimal("0.0000001"))
    with pytest.raises(ValueError, match="six decimals"):
        market_research_bond_auction_tail_digest_payload(report)


def test_all_public_numeric_count_and_ratio_fields_are_decimal_or_none() -> None:
    config = MarketResearchBondAuctionTailDigestConfig()
    auction = _auction()
    report = build_market_research_bond_auction_tail_digest(
        (auction,),
        config=config,
        generated_at=GENERATED_AT,
    )
    public_values = (config, auction, report, *report.rows, *report.reason_code_counts)

    numeric_names = {
        field.name
        for value in public_values
        for field in fields(value)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_pct")
            or field.name.endswith("_bps")
            or field.name.endswith("_yield")
            or field.name.endswith("_yield_pct")
        )
    }
    assert numeric_names
    for value in public_values:
        for field in fields(value):
            if field.name in numeric_names:
                public_value = getattr(value, field.name)
                assert public_value is None or type(public_value) is Decimal


def test_public_constructors_reject_noncanonical_ordering() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        MarketResearchBondAuctionTailDigestRow(
            auction_id="auction-watch",
            security_term="5y",
            auctioned_at=GENERATED_AT,
            tail_bps=Decimal("1.000000"),
            bid_to_cover_ratio=Decimal("2.000000"),
            indirect_bidder_pct=Decimal("60.000000"),
            high_yield_pct=Decimal("4.600000"),
            when_issued_yield_pct=Decimal("4.590000"),
            tail_status="watch",
            reason_codes=("weak_bid_to_cover", "auction_tail_watch"),
        )

    report = build_market_research_bond_auction_tail_digest(
        (
            _auction(
                auction_id="auction-watch",
                tail_bps=Decimal("1.600000"),
                bid_to_cover_ratio=Decimal("2.000000"),
            ),
            _auction(
                auction_id="auction-blocked",
                tail_bps=Decimal("4.200000"),
                bid_to_cover_ratio=Decimal("1.900000"),
            ),
        ),
        config=MarketResearchBondAuctionTailDigestConfig(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))


def test_rejects_bad_types_inconsistent_yields_and_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        MarketResearchBondAuctionTailDigestConfig(
            config_version=_StringSubclass(
                DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="supported config version"):
        MarketResearchBondAuctionTailDigestConfig(config_version="unsupported-version")
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_bond_auction_tail_digest(
            (),
            config=MarketResearchBondAuctionTailDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="auctions"):
        build_market_research_bond_auction_tail_digest(
            (object(),),
            config=MarketResearchBondAuctionTailDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="tail_bps"):
        _auction(tail_bps=_DecimalSubclass("1.0"))
    with pytest.raises(ValueError, match="tail_bps"):
        _auction(tail_bps=Decimal("Infinity"))
    with pytest.raises(ValueError, match="auctioned_at"):
        _auction(auctioned_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        _auction(auctioned_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTZ()))
    with pytest.raises(ValueError, match="tail_bps"):
        _auction(
            tail_bps=Decimal("1.0"),
            high_yield_pct=Decimal("4.6000"),
            when_issued_yield_pct=Decimal("4.5500"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_auction(), paper_only=False)
    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code="auction_tail_passed",
            count=Decimal("0.000000"),
        )

    good_row = MarketResearchBondAuctionTailDigestRow(
        auction_id="auction-pass",
        security_term="10y",
        auctioned_at=GENERATED_AT,
        tail_bps=Decimal("0.000000"),
        bid_to_cover_ratio=Decimal("2.600000"),
        indirect_bidder_pct=Decimal("70.000000"),
        high_yield_pct=Decimal("4.600000"),
        when_issued_yield_pct=Decimal("4.600000"),
        tail_status="pass",
        reason_codes=("auction_tail_passed",),
    )
    kwargs = dict(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION,
        digest_status="pass",
        digest_next_step="review_bond_auction_tail_risk",
        auction_count=Decimal("1.000000"),
        pass_count=Decimal("1.000000"),
        watch_count=Decimal("0.000000"),
        blocked_count=Decimal("0.000000"),
        tail_event_count=Decimal("0.000000"),
        weak_demand_count=Decimal("0.000000"),
        low_indirect_bidder_count=Decimal("0.000000"),
        max_tail_bps=Decimal("0.000000"),
        average_tail_bps=Decimal("0.000000"),
        average_bid_to_cover_ratio=Decimal("2.600000"),
        tail_event_ratio=Decimal("0.000000"),
        rows=(good_row,),
        reason_code_counts=(
            MarketResearchBondAuctionTailDigestReasonCodeCount(
                reason_code="auction_tail_passed",
                count=Decimal("1.000000"),
            ),
        ),
        reason_codes=("bond_auction_tail_digest_passed",),
    )

    assert MarketResearchBondAuctionTailDigestReport(**kwargs).digest_status == "pass"
    with pytest.raises(ValueError, match="pass_count"):
        MarketResearchBondAuctionTailDigestReport(
            **{**kwargs, "pass_count": Decimal("0.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchBondAuctionTailDigestReport(**{**kwargs, "digest_status": "blocked"})
    with pytest.raises(ValueError, match="rows"):
        MarketResearchBondAuctionTailDigestReport(
            **{**kwargs, "rows": (replace(good_row, tail_status="watch"), good_row)},
        )


def test_dataclasses_are_frozen() -> None:
    values = (
        MarketResearchBondAuctionTailDigestConfig(),
        _auction(),
        MarketResearchBondAuctionTailDigestRow(
            auction_id="auction-pass",
            security_term="10y",
            auctioned_at=GENERATED_AT,
            tail_bps=Decimal("0.000000"),
            bid_to_cover_ratio=Decimal("2.600000"),
            indirect_bidder_pct=Decimal("70.000000"),
            high_yield_pct=Decimal("4.600000"),
            when_issued_yield_pct=Decimal("4.600000"),
            tail_status="pass",
            reason_codes=("auction_tail_passed",),
        ),
        MarketResearchBondAuctionTailDigestReasonCodeCount(
            reason_code="auction_tail_passed",
            count=Decimal("1.000000"),
        ),
        build_market_research_bond_auction_tail_digest(
            (_auction(),),
            config=MarketResearchBondAuctionTailDigestConfig(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_public_dataclasses_reject_subclassing_at_definition_and_instantiation() -> None:
    good_row = MarketResearchBondAuctionTailDigestRow(
        auction_id="auction-pass",
        security_term="10y",
        auctioned_at=GENERATED_AT,
        tail_bps=Decimal("0.000000"),
        bid_to_cover_ratio=Decimal("2.600000"),
        indirect_bidder_pct=Decimal("70.000000"),
        high_yield_pct=Decimal("4.600000"),
        when_issued_yield_pct=Decimal("4.600000"),
        tail_status="pass",
        reason_codes=("auction_tail_passed",),
    )
    good_count = MarketResearchBondAuctionTailDigestReasonCodeCount(
        reason_code="auction_tail_passed",
        count=Decimal("1.000000"),
    )
    cases = (
        (MarketResearchBondAuctionTailDigestConfig, {}),
        (MarketResearchBondAuctionTailDigestAuction, _auction_kwargs()),
        (
            MarketResearchBondAuctionTailDigestRow,
            {
                "auction_id": "auction-pass",
                "security_term": "10y",
                "auctioned_at": GENERATED_AT,
                "tail_bps": Decimal("0.000000"),
                "bid_to_cover_ratio": Decimal("2.600000"),
                "indirect_bidder_pct": Decimal("70.000000"),
                "high_yield_pct": Decimal("4.600000"),
                "when_issued_yield_pct": Decimal("4.600000"),
                "tail_status": "pass",
                "reason_codes": ("auction_tail_passed",),
            },
        ),
        (
            MarketResearchBondAuctionTailDigestReasonCodeCount,
            {
                "reason_code": "auction_tail_passed",
                "count": Decimal("1.000000"),
            },
        ),
        (
            MarketResearchBondAuctionTailDigestReport,
            {
                "generated_at": GENERATED_AT,
                "config_version": (
                    DEFAULT_MARKET_RESEARCH_BOND_AUCTION_TAIL_DIGEST_CONFIG_VERSION
                ),
                "digest_status": "pass",
                "digest_next_step": "review_bond_auction_tail_risk",
                "auction_count": Decimal("1.000000"),
                "pass_count": Decimal("1.000000"),
                "watch_count": Decimal("0.000000"),
                "blocked_count": Decimal("0.000000"),
                "tail_event_count": Decimal("0.000000"),
                "weak_demand_count": Decimal("0.000000"),
                "low_indirect_bidder_count": Decimal("0.000000"),
                "max_tail_bps": Decimal("0.000000"),
                "average_tail_bps": Decimal("0.000000"),
                "average_bid_to_cover_ratio": Decimal("2.600000"),
                "tail_event_ratio": Decimal("0.000000"),
                "rows": (good_row,),
                "reason_code_counts": (good_count,),
                "reason_codes": ("bond_auction_tail_digest_passed",),
            },
        ),
    )

    for public_type, kwargs in cases:
        value = public_type(**kwargs)
        assert type(value) is public_type

        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)


def test_module_scope_excludes_io_durable_store_and_execution_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_bond_auction_tail_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_literals = (
        "buy",
        "sell",
        "trade",
        "wallet",
        "order",
        "position",
        "auth",
        "cancel",
        "exchange",
        "mutation",
        "replace",
        "secret",
        "private_key",
        "api_key",
    )
    lowered_source = source.lower()
    assert not any(token in lowered_source for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "sqlite",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "pathlib",
        "os",
        "subprocess",
        "supabase",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _auction(**overrides: object) -> MarketResearchBondAuctionTailDigestAuction:
    return MarketResearchBondAuctionTailDigestAuction(**_auction_kwargs(**overrides))


def _auction_kwargs(**overrides: object) -> dict[str, object]:
    values = {
        "auction_id": "auction-pass",
        "security_term": "10y",
        "auctioned_at": GENERATED_AT,
        "tail_bps": Decimal("0.0"),
        "bid_to_cover_ratio": Decimal("2.600"),
        "indirect_bidder_pct": Decimal("70.0"),
        "high_yield_pct": Decimal("4.6000"),
        "when_issued_yield_pct": Decimal("4.6000"),
    }
    values.update(overrides)
    return values


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]


def _assert_no_float_or_decimal_payload(value: object) -> None:
    if isinstance(value, (float, Decimal)):
        pytest.fail("public payload must not contain float or Decimal numerics")
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_float_or_decimal_payload(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_float_or_decimal_payload(child)
