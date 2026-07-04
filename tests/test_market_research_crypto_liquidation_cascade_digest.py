from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_liquidation_cascade_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CASCADE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoLiquidationCascadeDigestConfig,
    MarketResearchCryptoLiquidationCascadeDigestReport,
    MarketResearchCryptoLiquidationCascadeEvent,
    MarketResearchCryptoLiquidationCascadeSeverity,
    build_market_research_crypto_liquidation_cascade_digest,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def test_digest_summarizes_cascade_pressure_with_deterministic_sorting() -> None:
    report = build_market_research_crypto_liquidation_cascade_digest(
        (
            _event(
                venue="binance",
                asset_symbol="ETH",
                observed_at=datetime(2026, 7, 3, 7, 30, tzinfo=timezone(timedelta(hours=-4))),
                long_liquidation_usd=Decimal("900.10"),
                short_liquidation_usd=Decimal("25.00"),
                open_interest_change_usd=Decimal("-1500.25"),
                price_change_ratio=Decimal("-0.0625"),
                liquidation_notional_usd=Decimal("925.10"),
            ),
            _event(
                venue="okx",
                asset_symbol="BTC",
                observed_at=datetime(2026, 7, 3, 11, 45, tzinfo=UTC),
                long_liquidation_usd=Decimal("80.00"),
                short_liquidation_usd=Decimal("20.00"),
                open_interest_change_usd=Decimal("-20.00"),
                price_change_ratio=Decimal("-0.0125"),
                liquidation_notional_usd=Decimal("100.00"),
            ),
            _event(
                venue="bybit",
                asset_symbol="SOL",
                observed_at=datetime(2026, 7, 3, 11, 50, tzinfo=UTC),
                long_liquidation_usd=Decimal("10.00"),
                short_liquidation_usd=Decimal("5.00"),
                open_interest_change_usd=Decimal("2.00"),
                price_change_ratio=Decimal("0.0025"),
                liquidation_notional_usd=Decimal("15.00"),
            ),
        ),
        config=MarketResearchCryptoLiquidationCascadeDigestConfig(
            severe_liquidation_notional_usd=Decimal("750.00"),
            elevated_liquidation_notional_usd=Decimal("75.00"),
            severe_price_move_ratio=Decimal("0.0500"),
            elevated_price_move_ratio=Decimal("0.0100"),
            open_interest_drop_usd=Decimal("1000.00"),
        ),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketResearchCryptoLiquidationCascadeDigestReport)
    assert report.generated_at == GENERATED_AT
    assert (
        report.config_version
        == DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CASCADE_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.digest_next_step == "review_crypto_liquidation_cascade_risk"
    assert report.event_count == Decimal("3")
    assert report.asset_count == Decimal("3")
    assert report.venue_count == Decimal("3")
    assert report.severe_event_count == Decimal("1")
    assert report.elevated_event_count == Decimal("1")
    assert report.normal_event_count == Decimal("1")
    assert report.total_liquidation_notional_usd == Decimal("1040.10")
    assert report.total_long_liquidation_usd == Decimal("990.10")
    assert report.total_short_liquidation_usd == Decimal("50.00")
    assert report.net_long_liquidation_usd == Decimal("940.10")
    assert report.max_liquidation_notional_usd == Decimal("925.10")
    assert report.max_abs_price_change_ratio == Decimal("0.062500")
    assert report.long_liquidation_share_ratio == Decimal("0.951928")
    assert report.severe_event_ratio == Decimal("0.333333")
    assert report.reason_codes == (
        "crypto_liquidation_cascade_severe_notional",
        "crypto_liquidation_cascade_severe_price_move",
        "crypto_liquidation_cascade_open_interest_flush",
    )
    assert report.severity_rows == (
        MarketResearchCryptoLiquidationCascadeSeverity(
            severity="severe",
            event_count=Decimal("1"),
            liquidation_notional_usd=Decimal("925.10"),
        ),
        MarketResearchCryptoLiquidationCascadeSeverity(
            severity="elevated",
            event_count=Decimal("1"),
            liquidation_notional_usd=Decimal("100.00"),
        ),
        MarketResearchCryptoLiquidationCascadeSeverity(
            severity="normal",
            event_count=Decimal("1"),
            liquidation_notional_usd=Decimal("15.00"),
        ),
    )
    assert tuple(row.asset_symbol for row in report.top_events) == ("ETH", "BTC", "SOL")
    assert report.top_events[0].observed_at == datetime(2026, 7, 3, 11, 30, tzinfo=UTC)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    serialized = repr(asdict(report))
    for forbidden in ("buy", "sell", "trade", "wallet", "order", "position"):
        assert forbidden not in serialized.lower()


def test_empty_digest_blocks_with_decimal_zeroes_and_no_ratios() -> None:
    report = build_market_research_crypto_liquidation_cascade_digest(
        (),
        config=MarketResearchCryptoLiquidationCascadeDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "blocked"
    assert report.reason_codes == ("crypto_liquidation_cascade_digest_empty",)
    assert report.event_count == Decimal("0")
    assert report.asset_count == Decimal("0")
    assert report.venue_count == Decimal("0")
    assert report.severe_event_count == Decimal("0")
    assert report.elevated_event_count == Decimal("0")
    assert report.normal_event_count == Decimal("0")
    assert report.total_liquidation_notional_usd == Decimal("0")
    assert report.total_long_liquidation_usd == Decimal("0")
    assert report.total_short_liquidation_usd == Decimal("0")
    assert report.net_long_liquidation_usd == Decimal("0")
    assert report.max_liquidation_notional_usd == Decimal("0")
    assert report.max_abs_price_change_ratio == Decimal("0")
    assert report.long_liquidation_share_ratio is None
    assert report.severe_event_ratio is None
    assert report.severity_rows == ()
    assert report.top_events == ()


def test_all_normal_digest_passes_with_order_independent_output() -> None:
    inputs = (
        _event(
            venue="okx",
            asset_symbol="ETH",
            observed_at=GENERATED_AT,
            long_liquidation_usd=Decimal("10"),
            short_liquidation_usd=Decimal("5"),
            liquidation_notional_usd=Decimal("15"),
            price_change_ratio=Decimal("0.001"),
        ),
        _event(
            venue="binance",
            asset_symbol="BTC",
            observed_at=GENERATED_AT - timedelta(minutes=5),
            long_liquidation_usd=Decimal("8"),
            short_liquidation_usd=Decimal("2"),
            liquidation_notional_usd=Decimal("10"),
            price_change_ratio=Decimal("-0.002"),
        ),
    )

    report = build_market_research_crypto_liquidation_cascade_digest(
        tuple(reversed(inputs)),
        config=MarketResearchCryptoLiquidationCascadeDigestConfig(
            severe_liquidation_notional_usd=Decimal("1000"),
            elevated_liquidation_notional_usd=Decimal("100"),
            severe_price_move_ratio=Decimal("0.10"),
            elevated_price_move_ratio=Decimal("0.05"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.digest_status == "pass"
    assert report.reason_codes == ("crypto_liquidation_cascade_digest_passed",)
    assert report.event_count == Decimal("2")
    assert report.normal_event_count == Decimal("2")
    assert report.total_liquidation_notional_usd == Decimal("25")
    assert report.long_liquidation_share_ratio == Decimal("0.720000")
    assert report.severe_event_ratio == Decimal("0.000000")
    assert tuple(row.asset_symbol for row in report.top_events) == ("ETH", "BTC")


def test_rejects_bad_types_inconsistent_values_and_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        MarketResearchCryptoLiquidationCascadeDigestConfig(
            config_version=_StringSubclass(
                DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CASCADE_DIGEST_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_crypto_liquidation_cascade_digest(
            (),
            config=MarketResearchCryptoLiquidationCascadeDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="events"):
        build_market_research_crypto_liquidation_cascade_digest(
            (object(),),
            config=MarketResearchCryptoLiquidationCascadeDigestConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="long_liquidation_usd"):
        _event(long_liquidation_usd=1)
    with pytest.raises(ValueError, match="long_liquidation_usd"):
        _event(long_liquidation_usd=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="liquidation_notional_usd"):
        _event(
            long_liquidation_usd=Decimal("10"),
            short_liquidation_usd=Decimal("2"),
            liquidation_notional_usd=Decimal("11.99"),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _event(observed_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_event(), paper_only=False)

    good_row = MarketResearchCryptoLiquidationCascadeSeverity(
        severity="normal",
        event_count=Decimal("1"),
        liquidation_notional_usd=Decimal("10"),
    )
    kwargs = dict(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CASCADE_DIGEST_CONFIG_VERSION,
        digest_status="pass",
        digest_next_step="review_crypto_liquidation_cascade_risk",
        event_count=Decimal("1"),
        asset_count=Decimal("1"),
        venue_count=Decimal("1"),
        severe_event_count=Decimal("0"),
        elevated_event_count=Decimal("0"),
        normal_event_count=Decimal("1"),
        total_liquidation_notional_usd=Decimal("10"),
        total_long_liquidation_usd=Decimal("8"),
        total_short_liquidation_usd=Decimal("2"),
        net_long_liquidation_usd=Decimal("6"),
        max_liquidation_notional_usd=Decimal("10"),
        max_abs_price_change_ratio=Decimal("0.002000"),
        long_liquidation_share_ratio=Decimal("0.800000"),
        severe_event_ratio=Decimal("0.000000"),
        severity_rows=(good_row,),
        top_events=(
            _event(
                long_liquidation_usd=Decimal("8"),
                short_liquidation_usd=Decimal("2"),
                liquidation_notional_usd=Decimal("10"),
                price_change_ratio=Decimal("-0.002"),
            ),
        ),
        reason_codes=("crypto_liquidation_cascade_digest_passed",),
    )
    assert MarketResearchCryptoLiquidationCascadeDigestReport(**kwargs).digest_status == "pass"
    with pytest.raises(ValueError, match="event counts"):
        MarketResearchCryptoLiquidationCascadeDigestReport(
            **{**kwargs, "normal_event_count": Decimal("0")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoLiquidationCascadeDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="severity_rows"):
        MarketResearchCryptoLiquidationCascadeDigestReport(
            **{
                **kwargs,
                "severity_rows": (
                    MarketResearchCryptoLiquidationCascadeSeverity(
                        severity="severe",
                        event_count=Decimal("1"),
                        liquidation_notional_usd=Decimal("10"),
                    ),
                    good_row,
                ),
            },
        )


def test_dataclasses_are_frozen() -> None:
    values = (
        MarketResearchCryptoLiquidationCascadeDigestConfig(),
        _event(),
        MarketResearchCryptoLiquidationCascadeSeverity(
            severity="normal",
            event_count=Decimal("1"),
            liquidation_notional_usd=Decimal("10"),
        ),
        build_market_research_crypto_liquidation_cascade_digest(
            (_event(),),
            config=MarketResearchCryptoLiquidationCascadeDigestConfig(),
            generated_at=GENERATED_AT,
        ),
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_module_scope_excludes_io_db_network_auth_and_execution_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_liquidation_cascade_digest",
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
        "private_key",
        "api_key",
        "signature",
        "auth",
        "login",
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
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "web3",
        "eth_account",
        "pathlib",
        "open",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _event(**overrides: object) -> MarketResearchCryptoLiquidationCascadeEvent:
    values = {
        "venue": "binance",
        "asset_symbol": "BTC",
        "observed_at": GENERATED_AT,
        "long_liquidation_usd": Decimal("8"),
        "short_liquidation_usd": Decimal("2"),
        "open_interest_change_usd": Decimal("-1"),
        "price_change_ratio": Decimal("-0.002"),
        "liquidation_notional_usd": Decimal("10"),
    }
    values.update(overrides)
    return MarketResearchCryptoLiquidationCascadeEvent(**values)
