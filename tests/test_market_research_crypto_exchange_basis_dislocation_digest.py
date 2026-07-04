from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_crypto_exchange_basis_dislocation_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_BASIS_DISLOCATION_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoExchangeBasisDislocationDigestConfig,
    MarketResearchCryptoExchangeBasisDislocationDigestReasonCodeCount,
    MarketResearchCryptoExchangeBasisDislocationDigestReport,
    MarketResearchCryptoExchangeBasisDislocationDigestRow,
    MarketResearchCryptoExchangeBasisDislocationSnapshot,
    build_market_research_crypto_exchange_basis_dislocation_digest,
    market_research_crypto_exchange_basis_dislocation_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchCryptoExchangeBasisDislocationDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_BASIS_DISLOCATION_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("3600.000000"),
        "watch_basis_dislocation_abs": d("0.015000"),
        "blocked_basis_dislocation_abs": d("0.035000"),
        "watch_basis_change_abs": d("0.010000"),
        "blocked_basis_change_abs": d("0.025000"),
        "min_source_count": d("3.000000"),
        "min_open_interest_usd": d("1000000.000000"),
        "min_confidence": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchCryptoExchangeBasisDislocationDigestConfig(**values)


def _snapshot(
    condition_id: str = "condition_alpha",
    basis_id: str = "btc_perp_basis",
    *,
    asset_symbol: str = "BTC",
    venue_pair: str = "coinbase_binance",
    derivative_kind: str = "perp",
    observed_at: datetime = GENERATED_AT,
    spot_price_usd: Decimal = d("62000.000000"),
    derivative_price_usd: Decimal = d("62310.000000"),
    fair_basis_pct: Decimal = d("0.001000"),
    observed_basis_pct: Decimal = d("0.006000"),
    previous_basis_pct: Decimal = d("0.004000"),
    source_count: Decimal = d("3.000000"),
    open_interest_usd: Decimal = d("2500000.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "basis-dislocation-source-v0",
) -> MarketResearchCryptoExchangeBasisDislocationSnapshot:
    return MarketResearchCryptoExchangeBasisDislocationSnapshot(
        condition_id=condition_id,
        basis_id=basis_id,
        asset_symbol=asset_symbol,
        venue_pair=venue_pair,
        derivative_kind=derivative_kind,
        observed_at=observed_at,
        spot_price_usd=spot_price_usd,
        derivative_price_usd=derivative_price_usd,
        fair_basis_pct=fair_basis_pct,
        observed_basis_pct=observed_basis_pct,
        previous_basis_pct=previous_basis_pct,
        source_count=source_count,
        open_interest_usd=open_interest_usd,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoExchangeBasisDislocationSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoExchangeBasisDislocationDigestConfig | None = None,
) -> MarketResearchCryptoExchangeBasisDislocationDigestReport:
    return build_market_research_crypto_exchange_basis_dislocation_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_exchange_basis_dislocation_digest_summarizes_blocked_watch_and_pass_rows() -> None:
    report = _report(
        _snapshot(
            "condition_watch",
            "sol_quarterly_basis",
            asset_symbol="SOL",
            venue_pair="okx_deribit",
            derivative_kind="future",
            observed_at=GENERATED_AT - timedelta(seconds=900),
            spot_price_usd=d("130.000000"),
            derivative_price_usd=d("132.600000"),
            fair_basis_pct=d("0.005000"),
            observed_basis_pct=d("0.021000"),
            previous_basis_pct=d("0.015000"),
            source_count=d("2.000000"),
            open_interest_usd=d("800000.000000"),
            confidence=d("0.760000"),
        ),
        _snapshot(
            "condition_pass",
            "btc_perp_basis",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
        _snapshot(
            "condition_blocked",
            "eth_perp_basis",
            asset_symbol="ETH",
            venue_pair="coinbase_bybit",
            derivative_kind="perp",
            observed_at=GENERATED_AT - timedelta(seconds=4_200),
            spot_price_usd=d("3400.000000"),
            derivative_price_usd=d("3580.000000"),
            fair_basis_pct=d("0.004000"),
            observed_basis_pct=d("0.049000"),
            previous_basis_pct=d("0.018000"),
            source_count=d("1.000000"),
            open_interest_usd=d("700000.000000"),
            confidence=d("0.520000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_exchange_basis_dislocation_digest"
    )
    assert report.snapshot_count == d("3.000000")
    assert report.pass_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("1.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.basis_dislocation_snapshot_count == d("2.000000")
    assert report.basis_change_snapshot_count == d("1.000000")
    assert report.source_gap_snapshot_count == d("2.000000")
    assert report.open_interest_gap_snapshot_count == d("2.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.confidence_gap_snapshot_count == d("1.000000")
    assert report.average_observed_basis_pct == d("0.025333")
    assert report.average_basis_dislocation_abs == d("0.022000")
    assert report.max_basis_dislocation_abs == d("0.045000")
    assert report.max_snapshot_age_seconds == d("4200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.basis_id for row in report.rows) == (
        "eth_perp_basis",
        "sol_quarterly_basis",
        "btc_perp_basis",
    )
    blocked, watch, passed = report.rows
    assert blocked.digest_status == "blocked"
    assert blocked.snapshot_age_seconds == d("4200.000000")
    assert blocked.basis_dislocation_abs == d("0.045000")
    assert blocked.basis_change_abs == d("0.031000")
    assert blocked.reason_codes == (
        "market_research_crypto_exchange_basis_dislocation_digest_blocked_basis_dislocation",
        "market_research_crypto_exchange_basis_dislocation_digest_blocked_basis_change",
        "market_research_crypto_exchange_basis_dislocation_digest_source_gap",
        "market_research_crypto_exchange_basis_dislocation_digest_open_interest_gap",
        "market_research_crypto_exchange_basis_dislocation_digest_stale_snapshot",
        "market_research_crypto_exchange_basis_dislocation_digest_confidence_gap",
    )
    assert watch.digest_status == "watch"
    assert watch.reason_codes == (
        "market_research_crypto_exchange_basis_dislocation_digest_watch_basis_dislocation",
        "market_research_crypto_exchange_basis_dislocation_digest_source_gap",
        "market_research_crypto_exchange_basis_dislocation_digest_open_interest_gap",
    )
    assert passed.digest_status == "pass"
    assert passed.reason_codes == (
        "market_research_crypto_exchange_basis_dislocation_digest_basis_aligned",
    )
    assert report.reason_codes == (
        "market_research_crypto_exchange_basis_dislocation_digest_blocked_basis_dislocation",
        "market_research_crypto_exchange_basis_dislocation_digest_watch_basis_dislocation",
        "market_research_crypto_exchange_basis_dislocation_digest_blocked_basis_change",
        "market_research_crypto_exchange_basis_dislocation_digest_source_gap",
        "market_research_crypto_exchange_basis_dislocation_digest_open_interest_gap",
        "market_research_crypto_exchange_basis_dislocation_digest_stale_snapshot",
        "market_research_crypto_exchange_basis_dislocation_digest_confidence_gap",
    )


def test_exchange_basis_dislocation_digest_normalizes_timezones_and_reason_counts() -> None:
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "condition_gamma",
            "xrp_perp_basis",
            asset_symbol="XRP",
            observed_at=observed_at,
            observed_basis_pct=d("0.012000"),
            fair_basis_pct=d("0.001000"),
            previous_basis_pct=d("0.004000"),
            source_count=d("2.000000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert report.max_snapshot_age_seconds == d("3600.000000")
    assert report.digest_status == "watch"
    assert report.reason_code_counts == (
        MarketResearchCryptoExchangeBasisDislocationDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_exchange_basis_dislocation_digest_source_gap"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("xrp_perp_basis", "basis-dislocation-source-v0"),
    )


def test_exchange_basis_dislocation_digest_empty_input_and_sorting_are_deterministic() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_exchange_basis_dislocation_digest_no_inputs",
    )

    first = _report(
        _snapshot("condition_b", "basis_b"),
        _snapshot("condition_a", "basis_a"),
    )
    second = _report(
        _snapshot("condition_a", "basis_a"),
        _snapshot("condition_b", "basis_b"),
    )

    assert first == second
    assert tuple(row.basis_id for row in first.rows) == ("basis_a", "basis_b")


def test_exchange_basis_dislocation_digest_validates_types_flags_freezing_and_duplicates() -> None:
    assert MarketResearchCryptoExchangeBasisDislocationDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoExchangeBasisDislocationSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoExchangeBasisDislocationDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchCryptoExchangeBasisDislocationDigestReasonCodeCount.__dataclass_params__.frozen
    )
    assert MarketResearchCryptoExchangeBasisDislocationDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("basis-dislocation-v0"))
    with pytest.raises(ValueError, match="watch_basis_dislocation_abs"):
        _config(watch_basis_dislocation_abs=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="blocked_basis_dislocation_abs"):
        _config(
            watch_basis_dislocation_abs=d("0.040000"),
            blocked_basis_dislocation_abs=d("0.035000"),
        )
    with pytest.raises(ValueError, match="source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_id"):
        _snapshot(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        _snapshot(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        _report(_snapshot(basis_id="duplicate"), _snapshot(basis_id="duplicate"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]


def test_exchange_basis_dislocation_digest_public_numerics_are_decimal_only() -> None:
    report = _report(_snapshot())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if _is_public_numeric_field(field.name):
                assert type(value) is Decimal, field.name
    for field in fields(report):
        value = getattr(report, field.name)
        if _is_public_numeric_field(field.name):
            assert type(value) is Decimal, field.name
    for reason_count in report.reason_code_counts:
        assert reason_count.paper_only is True
        assert reason_count.report_only is True
        assert reason_count.readonly is True
        assert type(reason_count.count) is Decimal
        assert type(reason_count.snapshot_ratio) is Decimal

    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoExchangeBasisDislocationDigestReport)
    }
    assert (
        MarketResearchCryptoExchangeBasisDislocationDigestReport(**kwargs).digest_status
        == "pass"
    )
    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoExchangeBasisDislocationDigestReport(
            **{**kwargs, "snapshot_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoExchangeBasisDislocationDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoExchangeBasisDislocationDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_exchange_basis_dislocation_digest_basis_aligned"
                        ),
                        count=d("2.000000"),
                        snapshot_ratio=d("1.000000"),
                    ),
                ),
            },
        )


def test_exchange_basis_dislocation_digest_payload_is_immutable_redacted_and_six_decimal() -> None:
    payload = market_research_crypto_exchange_basis_dislocation_digest_payload(
        _report(
            _snapshot(
                "condition_redacted",
                "btc_perp_basis_redacted",
                asset_symbol="BTC",
            ),
        ),
    )
    payload_text = repr(payload).lower()

    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "order",
        "auth",
        "token",
        "private",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["average_basis_dislocation_abs"] == "0.005000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["spot_price_usd"] == "62000.000000"
    assert payload["rows"][0]["basis_dislocation_abs"] == "0.005000"
    assert payload["rows"][0]["paper_only"] is True
    assert_no_float_int_or_decimal_payload_numbers(payload)
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["basis_dislocation_abs"] = "0.000000"  # type: ignore[index]


def test_exchange_basis_dislocation_digest_payload_rejects_tampered_values() -> None:
    report = _report(_snapshot())
    object.__setattr__(report, "snapshot_count", 1)
    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        market_research_crypto_exchange_basis_dislocation_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report, "average_basis_dislocation_abs", 0.005)
    with pytest.raises(ValueError, match="JSON value must not be a float"):
        market_research_crypto_exchange_basis_dislocation_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report, "rows", (object(),))
    with pytest.raises(ValueError, match="JSON serializable"):
        market_research_crypto_exchange_basis_dislocation_digest_payload(report)

    with pytest.raises(ValueError, match="report must be exactly"):
        market_research_crypto_exchange_basis_dislocation_digest_payload(object())


def test_exchange_basis_dislocation_digest_module_scope_is_pure_report_only() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_exchange_basis_dislocation_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "market_slug",
        "question",
        "live trading",
        "trade",
        "auth",
        "wallet",
        "private",
        "token",
        "secret",
        "order",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "account",
        "advice",
        "network",
        "database",
        "store",
        "durable",
        "supabase",
        "persist",
        "sqlite",
        "subprocess",
        "socket",
        "http",
        "psycopg",
        "payload_json",
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
                "submit",
                "cancel",
                "replace",
            }
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_float_int_or_decimal_payload_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_int_or_decimal_payload_numbers(item)
        return
    if isinstance(value, tuple):
        for item in value:
            assert_no_float_int_or_decimal_payload_numbers(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, (Decimal, float, int))


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_seconds")
        or field_name.endswith("_pct")
        or field_name.endswith("_abs")
        or field_name.endswith("_usd")
        or field_name.endswith("_ratio")
        or field_name == "confidence"
    )
