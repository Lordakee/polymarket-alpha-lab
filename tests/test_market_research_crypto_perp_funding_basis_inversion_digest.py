from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import MappingProxyType

import pytest

from polymarket_alpha_lab.market_research_crypto_perp_funding_basis_inversion_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_FUNDING_BASIS_INVERSION_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoPerpFundingBasisInversionDigestConfig,
    MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount,
    MarketResearchCryptoPerpFundingBasisInversionDigestReport,
    MarketResearchCryptoPerpFundingBasisInversionDigestRow,
    MarketResearchCryptoPerpFundingBasisInversionSnapshot,
    build_market_research_crypto_perp_funding_basis_inversion_digest,
    market_research_crypto_perp_funding_basis_inversion_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchCryptoPerpFundingBasisInversionDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_PERP_FUNDING_BASIS_INVERSION_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("1800.000000"),
        "watch_perp_funding_rate_abs": d("0.000500"),
        "blocked_perp_funding_rate_abs": d("0.002000"),
        "watch_spot_perp_basis_abs": d("0.002500"),
        "blocked_spot_perp_basis_abs": d("0.010000"),
        "watch_open_interest_change_abs": d("0.080000"),
        "blocked_open_interest_change_abs": d("0.200000"),
        "watch_liquidation_pressure": d("0.300000"),
        "blocked_liquidation_pressure": d("0.600000"),
        "watch_borrow_stablecoin_funding_stress": d("0.250000"),
        "blocked_borrow_stablecoin_funding_stress": d("0.500000"),
        "watch_risk_score": d("0.350000"),
        "blocked_risk_score": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoPerpFundingBasisInversionDigestConfig(**values)


def _snapshot(
    exchange: str = "binance_perp",
    asset_symbol: str = "BTC",
    market_slug: str = "btc-election-range",
    *,
    source_timestamp: datetime = GENERATED_AT,
    perp_funding_rate: Decimal = d("0.000000"),
    spot_perp_basis: Decimal = d("0.000000"),
    open_interest_change_ratio: Decimal = d("0.000000"),
    liquidation_pressure_ratio: Decimal = d("0.000000"),
    borrow_stablecoin_funding_stress: Decimal = d("0.000000"),
    upstream_reason_codes: tuple[str, ...] = (),
    source_config_version: str = "perp-funding-basis-source-v0",
) -> MarketResearchCryptoPerpFundingBasisInversionSnapshot:
    return MarketResearchCryptoPerpFundingBasisInversionSnapshot(
        exchange=exchange,
        asset_symbol=asset_symbol,
        market_slug=market_slug,
        source_timestamp=source_timestamp,
        perp_funding_rate=perp_funding_rate,
        spot_perp_basis=spot_perp_basis,
        open_interest_change_ratio=open_interest_change_ratio,
        liquidation_pressure_ratio=liquidation_pressure_ratio,
        borrow_stablecoin_funding_stress=borrow_stablecoin_funding_stress,
        upstream_reason_codes=upstream_reason_codes,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoPerpFundingBasisInversionSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoPerpFundingBasisInversionDigestConfig | None = None,
) -> MarketResearchCryptoPerpFundingBasisInversionDigestReport:
    return build_market_research_crypto_perp_funding_basis_inversion_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_perp_funding_basis_inversion_digest_models_pressure_states() -> None:
    report = _report(
        _snapshot(
            "binance_perp",
            "BTC",
            "btc-election-range",
        ),
        _snapshot(
            "okx_perp",
            "ETH",
            "eth-reversal-range",
            perp_funding_rate=d("-0.002400"),
            spot_perp_basis=d("0.012000"),
            open_interest_change_ratio=d("0.240000"),
            liquidation_pressure_ratio=d("0.650000"),
            borrow_stablecoin_funding_stress=d("0.550000"),
            upstream_reason_codes=("external_funding_dislocation",),
        ),
        _snapshot(
            "bybit_perp",
            "SOL",
            "sol-basis-watch",
            perp_funding_rate=d("-0.000700"),
            spot_perp_basis=d("0.003000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_perp_funding_basis_inversion_digest"
    )
    assert report.snapshot_count == d("3.000000")
    assert report.pass_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("1.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.inversion_snapshot_count == d("2.000000")
    assert report.perp_funding_rate_pressure_snapshot_count == d("2.000000")
    assert report.spot_perp_basis_pressure_snapshot_count == d("2.000000")
    assert report.open_interest_acceleration_snapshot_count == d("1.000000")
    assert report.liquidation_pressure_snapshot_count == d("1.000000")
    assert report.borrow_stablecoin_funding_stress_snapshot_count == d("1.000000")
    assert report.upstream_reason_signal_snapshot_count == d("1.000000")
    assert report.stale_source_timestamp_snapshot_count == d("0.000000")
    assert report.average_perp_funding_rate == d("-0.001033")
    assert report.average_spot_perp_basis == d("0.005000")
    assert report.average_open_interest_change_ratio == d("0.080000")
    assert report.average_liquidation_pressure_ratio == d("0.216667")
    assert report.average_borrow_stablecoin_funding_stress == d("0.183333")
    assert report.average_risk_score == d("0.471667")
    assert report.max_risk_score == d("1.000000")
    assert report.max_snapshot_age_seconds == d("0.000000")
    assert report.watch_risk_score == d("0.350000")
    assert report.blocked_risk_score == d("0.700000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.exchange, row.asset_symbol, row.market_slug) for row in report.rows) == (
        ("okx_perp", "ETH", "eth-reversal-range"),
        ("bybit_perp", "SOL", "sol-basis-watch"),
        ("binance_perp", "BTC", "btc-election-range"),
    )
    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.snapshot_age_seconds == d("0.000000")
    assert blocked.perp_funding_rate_abs == d("0.002400")
    assert blocked.spot_perp_basis_abs == d("0.012000")
    assert blocked.open_interest_change_abs == d("0.240000")
    assert blocked.funding_basis_inverted is True
    assert blocked.risk_score == d("1.000000")
    assert blocked.reason_codes == (
        "market_research_crypto_perp_funding_basis_inversion_digest_inversion_pressure",
        "market_research_crypto_perp_funding_basis_inversion_digest_perp_funding_rate_pressure",
        "market_research_crypto_perp_funding_basis_inversion_digest_spot_perp_basis_pressure",
        "market_research_crypto_perp_funding_basis_inversion_digest_open_interest_acceleration",
        "market_research_crypto_perp_funding_basis_inversion_digest_liquidation_pressure",
        "market_research_crypto_perp_funding_basis_inversion_digest_borrow_stablecoin_funding_stress",
        "market_research_crypto_perp_funding_basis_inversion_digest_upstream_reason_signal",
    )
    watch = report.rows[1]
    assert watch.digest_status == "watch"
    assert watch.risk_score == d("0.415000")
    assert watch.funding_basis_inverted is True
    assert report.reason_codes == blocked.reason_codes
    assert report.reason_code_counts == (
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_perp_funding_basis_inversion_digest_inversion_pressure"
            ),
            count=d("2.000000"),
            snapshot_ratio=d("0.666667"),
        ),
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_perp_funding_basis_inversion_digest_perp_funding_rate_pressure"
            ),
            count=d("2.000000"),
            snapshot_ratio=d("0.666667"),
        ),
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_perp_funding_basis_inversion_digest_spot_perp_basis_pressure"
            ),
            count=d("2.000000"),
            snapshot_ratio=d("0.666667"),
        ),
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_perp_funding_basis_inversion_digest_open_interest_acceleration"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("0.333333"),
        ),
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_perp_funding_basis_inversion_digest_liquidation_pressure"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("0.333333"),
        ),
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_perp_funding_basis_inversion_digest_borrow_stablecoin_funding_stress"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("0.333333"),
        ),
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_perp_funding_basis_inversion_digest_upstream_reason_signal"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("0.333333"),
        ),
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code="market_research_crypto_perp_funding_basis_inversion_digest_pass",
            count=d("1.000000"),
            snapshot_ratio=d("0.333333"),
        ),
    )


def test_perp_funding_basis_inversion_digest_normalizes_timezones_and_staleness() -> None:
    generated_at = datetime(2026, 7, 3, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    source_timestamp = datetime(2026, 7, 3, 10, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "deribit_perp",
            "BTC",
            "btc-stale-basis",
            source_timestamp=source_timestamp,
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].source_timestamp == datetime(2026, 7, 3, 9, 0, tzinfo=UTC)
    assert report.rows[0].snapshot_age_seconds == d("10800.000000")
    assert report.rows[0].digest_status == "blocked"
    assert report.rows[0].reason_codes == (
        "market_research_crypto_perp_funding_basis_inversion_digest_stale_source_timestamp",
    )
    assert report.reason_code_counts == (
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_perp_funding_basis_inversion_digest_stale_source_timestamp"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        (("deribit_perp", "BTC", "btc-stale-basis"), "perp-funding-basis-source-v0"),
    )


def test_perp_funding_basis_inversion_digest_empty_input_and_deterministic_sorting() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_perp_funding_basis_inversion_digest_no_inputs",
    )
    assert empty.average_risk_score == d("0.000000")

    first = _report(
        _snapshot("okx_perp", "ETH", "eth-range"),
        _snapshot("binance_perp", "BTC", "btc-range"),
    )
    second = _report(
        _snapshot("binance_perp", "BTC", "btc-range"),
        _snapshot("okx_perp", "ETH", "eth-range"),
    )

    assert first == second
    assert tuple(row.exchange for row in first.rows) == ("binance_perp", "okx_perp")


def test_perp_funding_basis_inversion_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoPerpFundingBasisInversionDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoPerpFundingBasisInversionSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoPerpFundingBasisInversionDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoPerpFundingBasisInversionDigestReport.__dataclass_params__.frozen
    assert (
        MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount.__dataclass_params__.frozen
    )

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("perp-funding-basis-v0"))
    with pytest.raises(ValueError, match="watch_risk_score"):
        _config(watch_risk_score=_DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="max_snapshot_age_seconds"):
        _config(max_snapshot_age_seconds=1800)
    with pytest.raises(ValueError, match="exchange"):
        _snapshot(exchange=_StringSubclass("binance_perp"))
    with pytest.raises(ValueError, match="market_slug"):
        _snapshot(market_slug=_StringSubclass("btc-election-range"))
    with pytest.raises(ValueError, match="perp_funding_rate"):
        _snapshot(perp_funding_rate="-0.001000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="upstream_reason_codes"):
        _snapshot(upstream_reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="source_config_version"):
        _snapshot(source_config_version="source-auth-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="source_timestamp"):
        _snapshot(
            source_timestamp=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(source_timestamp=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]


def test_perp_funding_basis_inversion_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_snapshot())
    config = _config()

    numeric_name_parts = (
        "count",
        "ratio",
        "seconds",
        "rate",
        "basis",
        "stress",
        "score",
        "pressure",
        "change",
        "abs",
    )
    excluded_names = {
        "exchange",
        "funding_basis_inverted",
        "generated_at",
        "market_slug",
        "reason_code_counts",
        "reason_codes",
        "rows",
        "source_timestamp",
        "source_config_versions",
    }
    for item in (config, *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name not in excluded_names and any(
                part in field.name for part in numeric_name_parts
            ):
                assert type(value) is Decimal
    for reason_count in report.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.snapshot_ratio) is Decimal

    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoPerpFundingBasisInversionDigestReport)
    }
    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoPerpFundingBasisInversionDigestReport(
            **{**kwargs, "snapshot_count": 1},  # type: ignore[arg-type]
        )


def test_perp_funding_basis_inversion_digest_payload_is_immutable_and_canonical() -> None:
    payload = market_research_crypto_perp_funding_basis_inversion_digest_payload(
        _report(
            _snapshot(
                "okx_perp",
                "ETH",
                "eth-reversal-range",
                perp_funding_rate=d("-0.002400"),
                spot_perp_basis=d("0.012000"),
                open_interest_change_ratio=d("0.240000"),
                liquidation_pressure_ratio=d("0.650000"),
                borrow_stablecoin_funding_stress=d("0.550000"),
                upstream_reason_codes=("external_funding_dislocation",),
            ),
        ),
    )
    assert isinstance(payload, MappingProxyType)
    payload_text = repr(payload).lower()

    for forbidden in (
        "wallet",
        "auth",
        "private",
        "secret",
        "payload_json",
        "cancel",
        "replace",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["average_risk_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["source_timestamp"] == "2026-07-03T12:00:00+00:00"
    assert payload["rows"][0]["perp_funding_rate"] == "-0.002400"
    assert payload["rows"][0]["spot_perp_basis"] == "0.012000"
    assert payload["rows"][0]["risk_score"] == "1.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["risk_score"] = "0.000000"  # type: ignore[index]


def test_perp_funding_basis_inversion_digest_rejects_duplicates_and_bad_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(
            _snapshot("okx_perp", "ETH", "eth-range"),
            _snapshot("okx_perp", "ETH", "eth-range"),
        )

    valid = _report(_snapshot())
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(MarketResearchCryptoPerpFundingBasisInversionDigestReport)
    }
    assert MarketResearchCryptoPerpFundingBasisInversionDigestReport(**kwargs).digest_status == (
        "pass"
    )

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoPerpFundingBasisInversionDigestReport(
            **{**kwargs, "snapshot_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoPerpFundingBasisInversionDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoPerpFundingBasisInversionDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoPerpFundingBasisInversionDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_perp_funding_basis_inversion_digest_pass"
                        ),
                        count=d("2.000000"),
                        snapshot_ratio=d("1.000000"),
                    ),
                ),
            },
        )


def test_perp_funding_basis_inversion_digest_module_scope_excludes_io_and_mutation() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_perp_funding_basis_inversion_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "wallet",
        "auth",
        "private",
        "secret",
        "live_",
        "trading",
        "trade_",
        "broker",
        "signing",
        "submit_",
        "cancel_",
        "replace_",
        "network",
        "database",
        "supabase",
        "persist",
        "sqlite",
        "requests",
        "httpx",
        "socket",
        "urlopen",
        "psycopg",
        "subprocess",
        "getenv",
        "environ",
    )
    assert not any(token in lowered for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {
                "open",
                "read",
                "write",
                "connect",
                "execute",
                "request",
                "urlopen",
                "getenv",
                "run",
            }
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "os",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "pathlib",
        "sqlite",
        "supabase",
        "subprocess",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
