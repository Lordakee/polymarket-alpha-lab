from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_etf_creation_redemption_imbalance_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_IMBALANCE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig,
    MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount,
    MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport,
    MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow,
    MarketResearchCryptoEtfCreationRedemptionImbalanceObservation,
    build_market_research_crypto_etf_creation_redemption_imbalance_digest,
    market_research_crypto_etf_creation_redemption_imbalance_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 15, 0, tzinfo=UTC)


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
) -> MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_IMBALANCE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "watch_abs_imbalance_usd": d("25000000.000000"),
        "blocked_abs_imbalance_usd": d("100000000.000000"),
        "max_imbalance_ratio": d("0.050000"),
        "max_nav_dislocation_abs": d("0.015000"),
        "max_settlement_lag_hours": d("24.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    imbalance_key: str = "btc_spot_etf_create_redeem",
    *,
    asset_symbol: str = "BTC",
    observed_at: datetime = GENERATED_AT,
    creations_usd: Decimal = d("18000000.000000"),
    redemptions_usd: Decimal = d("12000000.000000"),
    previous_imbalance_usd: Decimal = d("4000000.000000"),
    assets_under_management_usd: Decimal = d("1000000000.000000"),
    nav_dislocation: Decimal = d("0.004000"),
    settlement_lag_hours: Decimal = d("6.000000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "crypto-etf-create-redeem-source-v0",
) -> MarketResearchCryptoEtfCreationRedemptionImbalanceObservation:
    return MarketResearchCryptoEtfCreationRedemptionImbalanceObservation(
        condition_id=condition_id,
        imbalance_key=imbalance_key,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        creations_usd=creations_usd,
        redemptions_usd=redemptions_usd,
        previous_imbalance_usd=previous_imbalance_usd,
        assets_under_management_usd=assets_under_management_usd,
        nav_dislocation=nav_dislocation,
        settlement_lag_hours=settlement_lag_hours,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchCryptoEtfCreationRedemptionImbalanceObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig | None = None,
) -> MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport:
    return build_market_research_crypto_etf_creation_redemption_imbalance_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_watch_digest() -> None:
    report = _report()

    assert isinstance(
        report,
        MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport,
    )
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-etf-creation-redemption-imbalance-digest-v0"
    )
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_market_research_crypto_etf_creation_redemption_imbalance_digest"
    )
    assert report.observation_count == d("0.000000")
    assert report.ready_observation_count == d("0.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("0.000000")
    assert report.total_net_creation_redemption_usd == d("0.000000")
    assert report.average_imbalance_ratio == d("0.000000")
    assert report.average_confidence == d("0.000000")
    assert report.max_observation_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_crypto_etf_creation_redemption_imbalance_digest_no_inputs",
    )
    assert report.reason_code_counts == (
        MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_etf_creation_redemption_imbalance_digest_no_inputs"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_imbalance_blocks_probability_event_screening() -> None:
    report = _report(
        _observation(
            "condition_eth",
            "eth_spot_etf_create_redeem",
            asset_symbol="ETH",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            creations_usd=d("5000000.000000"),
            redemptions_usd=d("185000000.000000"),
            previous_imbalance_usd=d("12000000.000000"),
            assets_under_management_usd=d("2000000000.000000"),
            nav_dislocation=d("-0.024000"),
            settlement_lag_hours=d("36.000000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _observation(),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_etf_creation_redemption_imbalance_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.imbalance_usd_observation_count == d("1.000000")
    assert report.imbalance_ratio_observation_count == d("1.000000")
    assert report.redemption_pressure_observation_count == d("1.000000")
    assert report.creation_pressure_observation_count == d("0.000000")
    assert report.imbalance_acceleration_observation_count == d("1.000000")
    assert report.nav_dislocation_observation_count == d("1.000000")
    assert report.settlement_lag_observation_count == d("1.000000")
    assert report.source_gap_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.total_net_creation_redemption_usd == d("-174000000.000000")
    assert report.average_imbalance_ratio == d("0.048000")
    assert report.average_confidence == d("0.685000")
    assert report.max_observation_age_seconds == d("9000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.imbalance_key) for row in report.rows) == (
        ("condition_eth", "eth_spot_etf_create_redeem"),
        ("condition_alpha", "btc_spot_etf_create_redeem"),
    )
    eth = report.rows[0]
    assert eth.digest_status == "blocked"
    assert eth.observation_age_seconds == d("9000.000000")
    assert eth.net_creation_redemption_usd == d("-180000000.000000")
    assert eth.imbalance_abs_usd == d("180000000.000000")
    assert eth.imbalance_ratio == d("0.090000")
    assert eth.imbalance_change_abs_usd == d("192000000.000000")
    assert eth.nav_dislocation_abs == d("0.024000")
    assert eth.reason_codes == (
        "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_usd",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_ratio",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_redemption_pressure",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_acceleration",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_nav_dislocation",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_settlement_lag",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_source_gap",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_confidence_gap",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_stale_observation",
    )
    assert report.reason_codes == eth.reason_codes


def test_timezones_reason_counts_and_source_versions_are_normalized() -> None:
    generated_at = datetime(2026, 7, 2, 11, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 16, 0, tzinfo=timezone(timedelta(hours=2)))

    report = _report(
        _observation(
            "condition_sol",
            "sol_spot_etf_create_redeem",
            asset_symbol="SOL",
            observed_at=observed_at,
            creations_usd=d("10000000.000000"),
            redemptions_usd=d("9000000.000000"),
            previous_imbalance_usd=d("1000000.000000"),
            assets_under_management_usd=d("600000000.000000"),
            source_count=d("1.000000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 2, 14, 0, tzinfo=UTC)
    assert report.rows[0].observation_age_seconds == d("3600.000000")
    assert report.digest_status == "watch"
    assert report.reason_code_counts == (
        MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_etf_creation_redemption_imbalance_digest_source_gap"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_spot_etf_create_redeem", "crypto-etf-create-redeem-source-v0"),
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    beta = _observation(
        "condition_beta",
        "beta_create_redeem",
        creations_usd=d("52000000.000000"),
        redemptions_usd=d("0.000000"),
        previous_imbalance_usd=d("2000000.000000"),
        assets_under_management_usd=d("2000000000.000000"),
    )
    alpha = _observation(
        "condition_alpha_watch",
        "alpha_create_redeem",
        creations_usd=d("52000000.000000"),
        redemptions_usd=d("0.000000"),
        previous_imbalance_usd=d("3000000.000000"),
        assets_under_management_usd=d("2000000000.000000"),
    )

    forward = _report(beta, alpha)
    reverse = _report(alpha, beta)

    assert forward == reverse
    assert tuple(row.imbalance_key for row in forward.rows) == (
        "alpha_create_redeem",
        "beta_create_redeem",
    )
    for row in forward.rows:
        assert row.digest_status == "watch"
        assert row.reason_codes == (
            "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_usd",
            "market_research_crypto_etf_creation_redemption_imbalance_digest_creation_pressure",
            "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_acceleration",
        )
    assert forward.reason_codes == forward.rows[0].reason_codes
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_usd",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_creation_pressure",
        "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_acceleration",
    )


def test_non_default_thresholds_can_downgrade_moderate_imbalance_risk() -> None:
    cfg = _config(
        watch_abs_imbalance_usd=d("120000000.000000"),
        blocked_abs_imbalance_usd=d("220000000.000000"),
        max_imbalance_ratio=d("0.200000"),
        max_nav_dislocation_abs=d("0.050000"),
        max_settlement_lag_hours=d("48.000000"),
        min_confidence=d("0.500000"),
    )

    report = _report(
        _observation(
            "condition_moderate",
            "moderate_create_redeem",
            creations_usd=d("100000000.000000"),
            redemptions_usd=d("8000000.000000"),
            previous_imbalance_usd=d("14000000.000000"),
            assets_under_management_usd=d("1000000000.000000"),
            nav_dislocation=d("0.012000"),
            settlement_lag_hours=d("12.000000"),
            confidence=d("0.750000"),
        ),
        config=cfg,
    )

    assert report.digest_status == "ready"
    assert report.recommended_next_step == (
        "allow_report_only_market_research_crypto_etf_creation_redemption_imbalance_digest"
    )
    assert report.rows[0].digest_status == "ready"
    assert report.rows[0].reason_codes == (
        "market_research_crypto_etf_creation_redemption_imbalance_digest_ready",
    )
    assert report.reason_codes == (
        "market_research_crypto_etf_creation_redemption_imbalance_digest_ready",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    assert MarketResearchCryptoEtfCreationRedemptionImbalanceDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoEtfCreationRedemptionImbalanceObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoEtfCreationRedemptionImbalanceDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReasonCodeCount.__dataclass_params__.frozen
    )
    assert MarketResearchCryptoEtfCreationRedemptionImbalanceDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("crypto-etf-imbalance-v0"))
    with pytest.raises(ValueError, match="watch_abs_imbalance_usd"):
        _config(
            watch_abs_imbalance_usd=d("300000000.000000"),
            blocked_abs_imbalance_usd=d("200000000.000000"),
        )
    with pytest.raises(ValueError, match="max_imbalance_ratio"):
        _config(max_imbalance_ratio=1)
    with pytest.raises(ValueError, match="creations_usd"):
        _observation(creations_usd=_DecimalSubclass("18000000.000000"))
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=0.8)
    with pytest.raises(ValueError, match="condition_id"):
        _observation(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 2, 15, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(
            observed_at=datetime(2026, 7, 2, 15, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="redacted"):
        _observation(imbalance_key="private_key_0xabc")
    with pytest.raises(ValueError, match="redacted"):
        _observation(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(imbalance_key="duplicate"),
            _observation(condition_id="condition_b", imbalance_key="duplicate"),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        build_market_research_crypto_etf_creation_redemption_imbalance_digest(
            ("not-an-observation",),  # type: ignore[arg-type]
            config=_config(),
            generated_at=GENERATED_AT,
        )

    valid_row = _report(_observation()).rows[0]
    with pytest.raises(ValueError, match="imbalance_abs_usd"):
        replace(valid_row, imbalance_abs_usd=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            valid_row,
            reason_codes=(
                "market_research_crypto_etf_creation_redemption_imbalance_digest_ready",
                "market_research_crypto_etf_creation_redemption_imbalance_digest_imbalance_usd",
            ),
        )

    frozen_observation = _observation("condition_frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.condition_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_observations_rows_counts_and_report() -> None:
    report = _report(_observation("condition_flags"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)
    assert all(
        item.paper_only and item.report_only and item.readonly
        for item in report.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(_observation("condition_report_only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count paper_only must be True"):
        replace(report.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(report, paper_only=False)


def test_public_numeric_fields_are_decimal_only_and_payload_is_immutable() -> None:
    report = _report(_observation("condition_payload"))

    for public_record in (
        _config(),
        _observation("condition_numeric"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if _is_public_numeric_field(field.name):
                assert type(value) is Decimal, field.name

    payload = market_research_crypto_etf_creation_redemption_imbalance_digest_payload(
        report,
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
    assert payload["generated_at"] == "2026-07-02T15:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["total_net_creation_redemption_usd"] == "6000000.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-02T15:00:00+00:00"
    assert payload["rows"][0]["creations_usd"] == "18000000.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["creations_usd"] = "0.000000"  # type: ignore[index]

    object.__setattr__(report, "observation_count", 1)
    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        market_research_crypto_etf_creation_redemption_imbalance_digest_payload(report)

    report = _report(_observation("condition_float"))
    object.__setattr__(report, "average_confidence", 0.82)
    with pytest.raises(ValueError, match="JSON value must not be a float"):
        market_research_crypto_etf_creation_redemption_imbalance_digest_payload(report)

    report = _report(_observation("condition_subclass_decimal"))
    object.__setattr__(
        report,
        "total_net_creation_redemption_usd",
        _DecimalSubclass("6000000"),
    )
    with pytest.raises(ValueError, match="JSON Decimal value must be exactly Decimal"):
        market_research_crypto_etf_creation_redemption_imbalance_digest_payload(report)


def test_module_scope_excludes_io_durable_surfaces_and_mutation_language() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_etf_creation_redemption_imbalance_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "market_slug",
        "question",
        "trading",
        "trade",
        "auth",
        "wallet",
        "order",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "store",
        "durable",
        "supabase",
        "persist",
        "sqlite",
        "private_key",
        "exchange",
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
                "connect",
                "execute",
                "getenv",
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
        "urllib",
        "sqlite",
        "subprocess",
        "httpx",
        "pathlib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_seconds")
        or field_name.endswith("_ratio")
        or field_name.endswith("_usd")
        or field_name.endswith("_hours")
        or field_name.endswith("_abs")
        or field_name.endswith("_confidence")
        or field_name
        in {
            "confidence",
            "min_confidence",
            "average_confidence",
            "nav_dislocation",
        }
    )
