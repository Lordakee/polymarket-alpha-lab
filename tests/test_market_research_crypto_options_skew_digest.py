from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_crypto_options_skew_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_SKEW_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoOptionsSkewDigestConfig,
    MarketResearchCryptoOptionsSkewDigestReasonCodeCount,
    MarketResearchCryptoOptionsSkewDigestReport,
    MarketResearchCryptoOptionsSkewDigestRow,
    MarketResearchCryptoOptionsSkewSnapshot,
    build_market_research_crypto_options_skew_digest,
    market_research_crypto_options_skew_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchCryptoOptionsSkewDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_SKEW_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("3600.000000"),
        "min_reference_count": d("2.000000"),
        "min_open_interest_usd": d("1000000.000000"),
        "min_volume_usd": d("250000.000000"),
        "max_call_put_skew_abs": d("0.180000"),
        "max_put_wing_premium": d("0.120000"),
        "max_call_wing_premium": d("0.140000"),
        "min_confidence": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchCryptoOptionsSkewDigestConfig(**values)


def snapshot(
    condition_id: str = "condition_alpha",
    options_skew_key: str = "btc.options.skew.ready",
    *,
    asset_symbol: str = "BTC",
    expiry_bucket: str = "7d",
    observed_at: datetime = GENERATED_AT,
    reference_count: Decimal = d("3.000000"),
    open_interest_usd: Decimal = d("2400000.000000"),
    volume_usd: Decimal = d("450000.000000"),
    call_put_skew: Decimal = d("0.050000"),
    put_wing_premium: Decimal = d("0.060000"),
    call_wing_premium: Decimal = d("0.070000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "crypto-options-skew-source-v0",
) -> MarketResearchCryptoOptionsSkewSnapshot:
    return MarketResearchCryptoOptionsSkewSnapshot(
        condition_id=condition_id,
        options_skew_key=options_skew_key,
        asset_symbol=asset_symbol,
        expiry_bucket=expiry_bucket,
        observed_at=observed_at,
        reference_count=reference_count,
        open_interest_usd=open_interest_usd,
        volume_usd=volume_usd,
        call_put_skew=call_put_skew,
        put_wing_premium=put_wing_premium,
        call_wing_premium=call_wing_premium,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def report(
    *snapshots: MarketResearchCryptoOptionsSkewSnapshot,
    generated_at: datetime = GENERATED_AT,
    cfg: MarketResearchCryptoOptionsSkewDigestConfig | None = None,
) -> MarketResearchCryptoOptionsSkewDigestReport:
    return build_market_research_crypto_options_skew_digest(
        snapshots,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_options_skew_digest_scores_pressure_liquidity_and_confidence() -> None:
    summary = report(
        snapshot(
            "condition_beta",
            "eth.options.skew.blocked",
            asset_symbol="ETH",
            expiry_bucket="30d",
            observed_at=GENERATED_AT - timedelta(seconds=4_200),
            reference_count=d("1.000000"),
            open_interest_usd=d("700000.000000"),
            volume_usd=d("100000.000000"),
            call_put_skew=d("-0.240000"),
            put_wing_premium=d("0.160000"),
            call_wing_premium=d("0.180000"),
            confidence=d("0.520000"),
        ),
        snapshot(
            "condition_alpha",
            "btc.options.skew.ready",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_SKEW_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_crypto_options_skew_digest"
    )
    assert summary.snapshot_count == d("2.000000")
    assert summary.ready_snapshot_count == d("1.000000")
    assert summary.watch_snapshot_count == d("0.000000")
    assert summary.blocked_snapshot_count == d("1.000000")
    assert summary.skew_pressure_snapshot_count == d("1.000000")
    assert summary.put_wing_pressure_snapshot_count == d("1.000000")
    assert summary.call_wing_pressure_snapshot_count == d("1.000000")
    assert summary.reference_gap_snapshot_count == d("1.000000")
    assert summary.open_interest_gap_snapshot_count == d("1.000000")
    assert summary.volume_gap_snapshot_count == d("1.000000")
    assert summary.stale_snapshot_count == d("1.000000")
    assert summary.confidence_gap_snapshot_count == d("1.000000")
    assert summary.average_call_put_skew == d("-0.095000")
    assert summary.average_put_wing_premium == d("0.110000")
    assert summary.average_call_wing_premium == d("0.125000")
    assert summary.max_snapshot_age_seconds == d("4200.000000")
    assert summary.ready_snapshot_ratio == d("0.500000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.condition_id, row.options_skew_key) for row in summary.rows) == (
        ("condition_beta", "eth.options.skew.blocked"),
        ("condition_alpha", "btc.options.skew.ready"),
    )
    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.snapshot_age_seconds == d("4200.000000")
    assert blocked.call_put_skew_abs == d("0.240000")
    assert blocked.reason_codes == (
        "market_research_crypto_options_skew_digest_skew_pressure",
        "market_research_crypto_options_skew_digest_put_wing_pressure",
        "market_research_crypto_options_skew_digest_call_wing_pressure",
        "market_research_crypto_options_skew_digest_reference_gap",
        "market_research_crypto_options_skew_digest_open_interest_gap",
        "market_research_crypto_options_skew_digest_volume_gap",
        "market_research_crypto_options_skew_digest_stale_snapshot",
        "market_research_crypto_options_skew_digest_confidence_gap",
    )
    assert summary.reason_codes == blocked.reason_codes


def test_options_skew_digest_normalizes_timezones_reason_counts_and_sources() -> None:
    generated_at = datetime(2026, 7, 3, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 3, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    summary = report(
        snapshot(
            "condition_gamma",
            "sol.options.skew.watch",
            asset_symbol="SOL",
            expiry_bucket="14d",
            observed_at=observed_at,
            reference_count=d("1.000000"),
            open_interest_usd=d("2000000.000000"),
            volume_usd=d("300000.000000"),
            call_put_skew=d("0.060000"),
            put_wing_premium=d("0.080000"),
            call_wing_premium=d("0.070000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.rows[0].observed_at == datetime(2026, 7, 3, 11, 0, tzinfo=UTC)
    assert summary.max_snapshot_age_seconds == d("3600.000000")
    assert summary.digest_status == "watch"
    assert summary.reason_code_counts == (
        MarketResearchCryptoOptionsSkewDigestReasonCodeCount(
            reason_code="market_research_crypto_options_skew_digest_reference_gap",
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert summary.source_config_versions == (
        ("sol.options.skew.watch", "crypto-options-skew-source-v0"),
    )


def test_options_skew_digest_empty_input_and_sorting_are_deterministic() -> None:
    empty = report()
    assert empty.digest_status == "watch"
    assert empty.snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_options_skew_digest_no_inputs",
    )

    first = report(
        snapshot("condition_b", "source_b"),
        snapshot("condition_a", "source_a"),
    )
    second = report(
        snapshot("condition_a", "source_a"),
        snapshot("condition_b", "source_b"),
    )

    assert first == second
    assert tuple(row.options_skew_key for row in first.rows) == ("source_a", "source_b")


def test_options_skew_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoOptionsSkewDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoOptionsSkewSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoOptionsSkewDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoOptionsSkewDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("options-skew-v0"))
    with pytest.raises(ValueError, match="max_call_put_skew_abs"):
        config(max_call_put_skew_abs=_DecimalSubclass("0.180000"))
    with pytest.raises(ValueError, match="min_reference_count"):
        config(min_reference_count=2)
    with pytest.raises(ValueError, match="confidence"):
        snapshot(confidence=0.8)
    with pytest.raises(ValueError, match="condition_id"):
        snapshot(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            snapshot(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report(snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(snapshot(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        snapshot().paper_only = False  # type: ignore[misc]


def test_options_skew_digest_public_numeric_fields_are_decimal_only() -> None:
    summary = report(snapshot())

    for row in summary.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_usd")
                or field.name.endswith("_skew")
                or field.name.endswith("_premium")
                or field.name.endswith("_abs")
                or field.name == "confidence"
            ):
                assert type(value) is Decimal
    for field in fields(summary):
        value = getattr(summary, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_usd")
            or field.name.endswith("_skew")
            or field.name.endswith("_premium")
        ):
            assert type(value) is Decimal
    for reason_count in summary.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.snapshot_ratio) is Decimal


def test_options_skew_digest_payload_is_redacted_and_has_no_live_surface() -> None:
    payload = market_research_crypto_options_skew_digest_payload(
        report(
            snapshot(
                "condition_redacted",
                "btc.options.skew.redacted",
                asset_symbol="BTC",
                expiry_bucket="7d",
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
    assert payload["snapshot_count"] == "1.000000"
    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["options_skew_key"] == "btc.options.skew.redacted"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["rows"][0]["call_put_skew"] == "0.050000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["call_put_skew"] = "0.000000"  # type: ignore[index]


def test_module_scope_has_no_network_store_live_auth_wallet_order_or_fast_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_crypto_options_skew_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "request",
        "socket",
        "http",
        "url",
        "database",
        "db",
        "store",
        "persist",
        "durable",
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "fast",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
