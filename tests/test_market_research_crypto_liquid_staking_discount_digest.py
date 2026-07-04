from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import importlib
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-crypto-liquid-staking-discount-digest-test-v0"


class NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class DerivedDatetime(datetime):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_liquid_staking_discount_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "watch_discount_ratio": d("0.010000"),
        "blocked_discount_ratio": d("0.030000"),
        "watch_source_age_hours": d("12.000000"),
        "blocked_source_age_hours": d("48.000000"),
    }
    values.update(overrides)
    return digest.MarketResearchCryptoLiquidStakingDiscountDigestConfig(**values)


def observation(
    asset_slug: str,
    observation_id: str,
    *,
    derivative_asset_slug: str,
    protocol_slug: str,
    chain_slug: str = "ethereum",
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    derivative_price: Decimal = d("0.990000"),
    backing_asset_price: Decimal = d("1.000000"),
    source_ref: str = "https://prices.example.invalid/liquid-staking",
    source_config_version: str = "liquid-staking-source-config-v0",
    reason_codes: tuple[str, ...] = ("liquid_staking_discount_observed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchCryptoLiquidStakingDiscountObservation(
        asset_slug=asset_slug,
        observation_id=observation_id,
        derivative_asset_slug=derivative_asset_slug,
        protocol_slug=protocol_slug,
        chain_slug=chain_slug,
        observed_at=observed_at,
        derivative_price=derivative_price,
        backing_asset_price=backing_asset_price,
        source_ref=source_ref,
        source_config_version=source_config_version,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations, **overrides: object):
    digest = module()
    values = {
        "observations": observations,
        "config": cfg(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_crypto_liquid_staking_discount_digest(**values)


def test_liquid_staking_discount_digest_summarizes_watch_and_blocked_observations() -> None:
    report = build_report(
        observation(
            "eth",
            "blocked",
            derivative_asset_slug="steth",
            protocol_slug="lido",
            observed_at=GENERATED_AT - timedelta(hours=50),
            derivative_price=d("0.960000"),
            backing_asset_price=d("1.000000"),
        ),
        observation(
            "eth",
            "watch",
            derivative_asset_slug="reth",
            protocol_slug="rocket-pool",
            observed_at=GENERATED_AT - timedelta(hours=10),
            derivative_price=d("0.985000"),
            backing_asset_price=d("1.000000"),
        ),
        observation(
            "sol",
            "clear",
            derivative_asset_slug="msol",
            protocol_slug="marinade",
            chain_slug="solana",
            observed_at=GENERATED_AT - timedelta(hours=1),
            derivative_price=d("1.000000"),
            backing_asset_price=d("1.000000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_crypto_liquid_staking_discount_research"
    )
    assert report.observation_count == d("3.000000")
    assert report.clear_observation_count == d("1.000000")
    assert report.watch_observation_count == d("1.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.max_discount_ratio == d("0.040000")
    assert report.max_source_age_hours == d("50.000000")
    assert report.reason_codes == (
        "crypto_liquid_staking_discount_ratio_blocked",
        "crypto_liquid_staking_discount_source_age_blocked",
        "crypto_liquid_staking_discount_ratio_watch",
    )
    assert report.source_config_versions == (
        ("eth", "blocked", "liquid-staking-source-config-v0"),
        ("eth", "watch", "liquid-staking-source-config-v0"),
        ("sol", "clear", "liquid-staking-source-config-v0"),
    )
    assert tuple((row.asset_slug, row.observation_id) for row in report.rows) == (
        ("eth", "blocked"),
        ("eth", "watch"),
        ("sol", "clear"),
    )

    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.discount_ratio == d("0.040000")
    assert blocked.source_age_hours == d("50.000000")
    assert blocked.reason_codes == (
        "crypto_liquid_staking_discount_ratio_blocked",
        "crypto_liquid_staking_discount_source_age_blocked",
        "liquid_staking_discount_observed",
    )
    assert blocked.paper_only is True
    assert blocked.report_only is True
    assert blocked.readonly is True
    assert "https://prices" not in repr(report).lower()


def test_no_observations_returns_report_only_blocked_rollup() -> None:
    report = build_report()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_crypto_liquid_staking_discount_research"
    )
    assert report.observation_count == d("0.000000")
    assert report.clear_observation_count == d("0.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("0.000000")
    assert report.max_discount_ratio == d("0.000000")
    assert report.max_source_age_hours == d("0.000000")
    assert report.reason_codes == ("crypto_liquid_staking_discount_inventory_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_and_public_metrics_are_decimal_only() -> None:
    digest = module()

    assert digest.__all__ == (
        "DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUID_STAKING_DISCOUNT_DIGEST_CONFIG_VERSION",
        "MarketResearchCryptoLiquidStakingDiscountDigestConfig",
        "MarketResearchCryptoLiquidStakingDiscountDigestReport",
        "MarketResearchCryptoLiquidStakingDiscountDigestRow",
        "MarketResearchCryptoLiquidStakingDiscountObservation",
        "build_market_research_crypto_liquid_staking_discount_digest",
        "market_research_crypto_liquid_staking_discount_digest_payload",
    )
    for exported_name in digest.__all__:
        value = getattr(digest, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(
        observation(
            "eth",
            "clear",
            derivative_asset_slug="steth",
            protocol_slug="lido",
        ),
    )

    for value in (report, *report.rows):
        for field in fields(value):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_hours")
                or field.name.endswith("_price")
            ):
                assert type(getattr(value, field.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].digest_status = "blocked"  # type: ignore[misc]


def test_utc_aware_datetimes_are_required_and_normalized() -> None:
    digest = module()
    report = build_report(
        observation(
            "eth",
            "tz",
            derivative_asset_slug="steth",
            protocol_slug="lido",
            observed_at=datetime(2026, 7, 4, 10, 0, tzinfo=timezone.utc),
        ),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 4, 10, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_research_crypto_liquid_staking_discount_digest(
            (),
            config=digest.MarketResearchCryptoLiquidStakingDiscountDigestConfig(),
            generated_at=datetime(2026, 7, 4, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(
            "eth",
            "naive",
            derivative_asset_slug="steth",
            protocol_slug="lido",
            observed_at=datetime(2026, 7, 4, 12, 0),
        )


def test_rejects_none_offset_timezones_datetime_subclasses_and_false_flags() -> None:
    digest = module()
    none_offset_datetime = datetime(2026, 7, 4, 12, 0, tzinfo=NoneOffsetTimezone())

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_research_crypto_liquid_staking_discount_digest(
            (),
            config=digest.MarketResearchCryptoLiquidStakingDiscountDigestConfig(),
            generated_at=none_offset_datetime,
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(
            "eth",
            "none-offset",
            derivative_asset_slug="steth",
            protocol_slug="lido",
            observed_at=none_offset_datetime,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest.build_market_research_crypto_liquid_staking_discount_digest(
            (),
            config=digest.MarketResearchCryptoLiquidStakingDiscountDigestConfig(),
            generated_at=DerivedDatetime(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        observation(
            "eth",
            "derived",
            derivative_asset_slug="steth",
            protocol_slug="lido",
            observed_at=DerivedDatetime(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        digest.MarketResearchCryptoLiquidStakingDiscountDigestConfig(paper_only=False)


def test_rejects_public_float_numerics_nonfinite_decimals_and_duplicate_observations() -> None:
    digest = module()

    with pytest.raises(ValueError, match="watch_discount_ratio must be a Decimal"):
        digest.MarketResearchCryptoLiquidStakingDiscountDigestConfig(
            watch_discount_ratio=0.01,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="watch_discount_ratio must be finite"):
        digest.MarketResearchCryptoLiquidStakingDiscountDigestConfig(
            watch_discount_ratio=Decimal("NaN"),
        )
    with pytest.raises(ValueError, match="reason_codes must not contain duplicates"):
        observation(
            "eth",
            "dupe-reason",
            derivative_asset_slug="steth",
            protocol_slug="lido",
            reason_codes=("duplicate", "duplicate"),
        )
    with pytest.raises(
        ValueError,
        match="observations must not contain duplicate asset/observation pairs",
    ):
        build_report(
            observation("eth", "same", derivative_asset_slug="steth", protocol_slug="lido"),
            observation("eth", "same", derivative_asset_slug="reth", protocol_slug="rocket-pool"),
        )


def test_payload_redacts_source_refs_and_uses_decimal_strings() -> None:
    digest = module()
    report = build_report(
        observation(
            "eth",
            "payload",
            derivative_asset_slug="steth",
            protocol_slug="lido",
        ),
    )

    payload = digest.market_research_crypto_liquid_staking_discount_digest_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload["observation_count"] == "1.000000"
    assert payload["max_discount_ratio"] == "0.010000"
    assert payload["rows"][0]["derivative_price"] == "0.990000"
    assert payload["rows"][0]["source_ref"] == "<redacted-source-ref>"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)


def test_module_omits_runtime_io_and_financial_action_surfaces() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "persistence",
        "network",
        "live",
        "authentication",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "replace",
        "exchange",
        "signing",
        "advice",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)
