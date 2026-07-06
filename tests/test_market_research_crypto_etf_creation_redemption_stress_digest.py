from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import MappingProxyType

import pytest

from polymarket_alpha_lab.market_research_crypto_etf_creation_redemption_stress_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_STRESS_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoEtfCreationRedemptionStressDigestConfig,
    MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount,
    MarketResearchCryptoEtfCreationRedemptionStressDigestReport,
    MarketResearchCryptoEtfCreationRedemptionStressDigestRow,
    MarketResearchCryptoEtfCreationRedemptionStressObservation,
    build_market_research_crypto_etf_creation_redemption_stress_digest,
    market_research_crypto_etf_creation_redemption_stress_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 5, 16, 0, tzinfo=UTC)
BASE_REASON = "market_research_crypto_etf_creation_redemption_stress_digest_"
READY_REASON = BASE_REASON + "ready"
NO_INPUTS_REASON = BASE_REASON + "no_inputs"
REDEMPTION_PRESSURE_USD_REASON = BASE_REASON + "redemption_pressure_usd"
REDEMPTION_PRESSURE_RATIO_REASON = BASE_REASON + "redemption_pressure_ratio"
FLOW_STRESS_RATIO_REASON = BASE_REASON + "flow_stress_ratio"
CASH_BUFFER_GAP_REASON = BASE_REASON + "cash_buffer_gap"
SETTLEMENT_LAG_REASON = BASE_REASON + "settlement_lag"
SOURCE_GAP_REASON = BASE_REASON + "source_gap"
CONFIDENCE_GAP_REASON = BASE_REASON + "confidence_gap"
STALE_SOURCE_REASON = BASE_REASON + "stale_source"


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
) -> MarketResearchCryptoEtfCreationRedemptionStressDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_CREATION_REDEMPTION_STRESS_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "watch_redemption_pressure_usd": d("25000000.000000"),
        "blocked_redemption_pressure_usd": d("100000000.000000"),
        "max_redemption_pressure_ratio": d("0.050000"),
        "watch_flow_stress_ratio": d("0.025000"),
        "min_cash_buffer_ratio": d("0.250000"),
        "max_settlement_lag_hours": d("24.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoEtfCreationRedemptionStressDigestConfig(**values)


def _observation(
    fund_id: str = "fund_alpha",
    stress_id: str = "btc_spot_etf_create_redeem_stress",
    *,
    asset_symbol: str = "BTC",
    observed_at: datetime = GENERATED_AT,
    creations_usd: Decimal = d("20000000.000000"),
    redemptions_usd: Decimal = d("15000000.000000"),
    available_cash_usd: Decimal = d("12000000.000000"),
    underlying_liquidity_usd: Decimal = d("1000000000.000000"),
    settlement_lag_hours: Decimal = d("6.000000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "crypto-etf-create-redeem-stress-source-v0",
) -> MarketResearchCryptoEtfCreationRedemptionStressObservation:
    return MarketResearchCryptoEtfCreationRedemptionStressObservation(
        fund_id=fund_id,
        stress_id=stress_id,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        creations_usd=creations_usd,
        redemptions_usd=redemptions_usd,
        available_cash_usd=available_cash_usd,
        underlying_liquidity_usd=underlying_liquidity_usd,
        settlement_lag_hours=settlement_lag_hours,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchCryptoEtfCreationRedemptionStressObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoEtfCreationRedemptionStressDigestConfig | None = None,
) -> MarketResearchCryptoEtfCreationRedemptionStressDigestReport:
    return build_market_research_crypto_etf_creation_redemption_stress_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_blocked_digest() -> None:
    report = _report()

    assert isinstance(report, MarketResearchCryptoEtfCreationRedemptionStressDigestReport)
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-etf-creation-redemption-stress-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_etf_creation_redemption_stress_digest"
    )
    assert report.observation_count == d("0.000000")
    assert report.ready_observation_count == d("0.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("0.000000")
    assert report.total_redemption_pressure_usd == d("0.000000")
    assert report.average_redemption_pressure_ratio == d("0.000000")
    assert report.average_flow_stress_ratio == d("0.000000")
    assert report.average_confidence == d("0.000000")
    assert report.max_observation_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (NO_INPUTS_REASON,)
    assert report.reason_code_counts == (
        MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount(
            reason_code=NO_INPUTS_REASON,
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_redemption_stress_blocks_probability_event_screening() -> None:
    report = _report(
        _observation(
            "fund_eth",
            "eth_spot_etf_create_redeem_stress",
            asset_symbol="ETH",
            observed_at=GENERATED_AT - timedelta(seconds=9000),
            creations_usd=d("5000000.000000"),
            redemptions_usd=d("185000000.000000"),
            available_cash_usd=d("10000000.000000"),
            underlying_liquidity_usd=d("2000000000.000000"),
            settlement_lag_hours=d("36.000000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _observation(),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_etf_creation_redemption_stress_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.redemption_pressure_usd_observation_count == d("1.000000")
    assert report.redemption_pressure_ratio_observation_count == d("1.000000")
    assert report.flow_stress_ratio_observation_count == d("1.000000")
    assert report.cash_buffer_gap_observation_count == d("1.000000")
    assert report.settlement_lag_observation_count == d("1.000000")
    assert report.source_gap_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.stale_source_observation_count == d("1.000000")
    assert report.total_redemption_pressure_usd == d("170000000.000000")
    assert report.average_redemption_pressure_ratio == d("0.042500")
    assert report.average_flow_stress_ratio == d("0.047500")
    assert report.average_confidence == d("0.685000")
    assert report.max_observation_age_seconds == d("9000.000000")

    assert tuple((row.fund_id, row.stress_id) for row in report.rows) == (
        ("fund_eth", "eth_spot_etf_create_redeem_stress"),
        ("fund_alpha", "btc_spot_etf_create_redeem_stress"),
    )
    eth = report.rows[0]
    assert eth.digest_status == "blocked"
    assert eth.observation_age_seconds == d("9000.000000")
    assert eth.net_creation_redemption_usd == d("-180000000.000000")
    assert eth.redemption_pressure_usd == d("170000000.000000")
    assert eth.redemption_pressure_ratio == d("0.085000")
    assert eth.flow_stress_ratio == d("0.090000")
    assert eth.cash_buffer_ratio == d("0.054054")
    assert eth.reason_codes == (
        REDEMPTION_PRESSURE_USD_REASON,
        REDEMPTION_PRESSURE_RATIO_REASON,
        FLOW_STRESS_RATIO_REASON,
        CASH_BUFFER_GAP_REASON,
        SETTLEMENT_LAG_REASON,
        SOURCE_GAP_REASON,
        CONFIDENCE_GAP_REASON,
        STALE_SOURCE_REASON,
    )
    assert report.reason_codes == eth.reason_codes


def test_timezone_normalization_reason_counts_and_source_versions() -> None:
    generated_at = datetime(2026, 7, 5, 12, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 5, 18, 0, tzinfo=timezone(timedelta(hours=2)))

    report = _report(
        _observation(
            "fund_sol",
            "sol_spot_etf_create_redeem_stress",
            asset_symbol="SOL",
            observed_at=observed_at,
            source_count=d("1.000000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == GENERATED_AT
    assert report.rows[0].observation_age_seconds == d("0.000000")
    assert report.digest_status == "watch"
    assert report.reason_code_counts == (
        MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount(
            reason_code=SOURCE_GAP_REASON,
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_spot_etf_create_redeem_stress", "crypto-etf-create-redeem-stress-source-v0"),
    )


def test_rows_reason_codes_and_public_tuples_require_canonical_sequence() -> None:
    beta = _observation(
        "fund_beta",
        "beta_create_redeem_stress",
        creations_usd=d("0.000000"),
        redemptions_usd=d("52000000.000000"),
        available_cash_usd=d("20000000.000000"),
        underlying_liquidity_usd=d("2000000000.000000"),
    )
    alpha = _observation(
        "fund_alpha_watch",
        "alpha_create_redeem_stress",
        creations_usd=d("0.000000"),
        redemptions_usd=d("52000000.000000"),
        available_cash_usd=d("20000000.000000"),
        underlying_liquidity_usd=d("2000000000.000000"),
    )

    forward = _report(beta, alpha)
    reverse = _report(alpha, beta)

    assert forward == reverse
    assert tuple(row.stress_id for row in forward.rows) == (
        "alpha_create_redeem_stress",
        "beta_create_redeem_stress",
    )
    for row in forward.rows:
        assert row.digest_status == "watch"
        assert row.reason_codes == (
            REDEMPTION_PRESSURE_USD_REASON,
            FLOW_STRESS_RATIO_REASON,
        )
    assert forward.reason_codes == forward.rows[0].reason_codes
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        REDEMPTION_PRESSURE_USD_REASON,
        FLOW_STRESS_RATIO_REASON,
    )

    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(forward, rows=list(forward.rows))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rows must use canonical sequence"):
        replace(forward, rows=tuple(reversed(forward.rows)))
    with pytest.raises(ValueError, match="reason_codes must use canonical sequence"):
        replace(forward.rows[0], reason_codes=tuple(reversed(forward.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="source_config_versions must use canonical sequence"):
        replace(forward, source_config_versions=tuple(reversed(forward.source_config_versions)))


def test_non_default_thresholds_can_downgrade_moderate_stress() -> None:
    cfg = _config(
        watch_redemption_pressure_usd=d("120000000.000000"),
        blocked_redemption_pressure_usd=d("220000000.000000"),
        max_redemption_pressure_ratio=d("0.200000"),
        watch_flow_stress_ratio=d("0.200000"),
        min_cash_buffer_ratio=d("0.050000"),
        max_settlement_lag_hours=d("48.000000"),
        min_confidence=d("0.500000"),
    )

    report = _report(
        _observation(
            "fund_moderate",
            "moderate_create_redeem_stress",
            creations_usd=d("20000000.000000"),
            redemptions_usd=d("80000000.000000"),
            available_cash_usd=d("10000000.000000"),
            underlying_liquidity_usd=d("1000000000.000000"),
            settlement_lag_hours=d("12.000000"),
            confidence=d("0.750000"),
        ),
        config=cfg,
    )

    assert report.digest_status == "ready"
    assert report.recommended_next_step == (
        "allow_report_only_market_research_crypto_etf_creation_redemption_stress_digest"
    )
    assert report.rows[0].digest_status == "ready"
    assert report.rows[0].reason_codes == (READY_REASON,)
    assert report.reason_codes == (READY_REASON,)


def test_non_default_blocked_threshold_can_upgrade_redemption_pressure() -> None:
    cfg = _config(
        blocked_redemption_pressure_usd=d("50000000.000000"),
        max_redemption_pressure_ratio=d("0.200000"),
        watch_flow_stress_ratio=d("0.200000"),
        min_cash_buffer_ratio=d("0.050000"),
        max_settlement_lag_hours=d("48.000000"),
        min_confidence=d("0.500000"),
    )

    report = _report(
        _observation(
            "fund_low_threshold",
            "low_threshold_create_redeem_stress",
            creations_usd=d("20000000.000000"),
            redemptions_usd=d("80000000.000000"),
            available_cash_usd=d("10000000.000000"),
            underlying_liquidity_usd=d("1000000000.000000"),
            settlement_lag_hours=d("12.000000"),
            confidence=d("0.750000"),
        ),
        config=cfg,
    )

    assert report.blocked_redemption_pressure_usd == d("50000000.000000")
    assert report.digest_status == "blocked"
    assert report.rows[0].digest_status == "blocked"
    assert report.rows[0].redemption_pressure_usd == d("50000000.000000")
    assert report.rows[0].reason_codes == (REDEMPTION_PRESSURE_USD_REASON,)


def test_validation_rejects_bad_inputs_subclasses_and_inconsistent_records() -> None:
    assert MarketResearchCryptoEtfCreationRedemptionStressDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoEtfCreationRedemptionStressObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoEtfCreationRedemptionStressDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount.__dataclass_params__.frozen
    )
    assert MarketResearchCryptoEtfCreationRedemptionStressDigestReport.__dataclass_params__.frozen

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "ConfigSubclass",
            (MarketResearchCryptoEtfCreationRedemptionStressDigestConfig,),
            {},
        )
    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "ObservationSubclass",
            (MarketResearchCryptoEtfCreationRedemptionStressObservation,),
            {},
        )

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("crypto-etf-stress-v0"))
    with pytest.raises(ValueError, match="watch_redemption_pressure_usd"):
        _config(
            watch_redemption_pressure_usd=d("300000000.000000"),
            blocked_redemption_pressure_usd=d("200000000.000000"),
        )
    with pytest.raises(ValueError, match="max_redemption_pressure_ratio"):
        _config(max_redemption_pressure_ratio=1)
    with pytest.raises(ValueError, match="creations_usd"):
        _observation(creations_usd=_DecimalSubclass("20000000.000000"))
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=Decimal("0.8200001"))
    with pytest.raises(ValueError, match="fund_id"):
        _observation(fund_id=_StringSubclass("fund_alpha"))
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 5, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 5, 16, 0))
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 5, 16, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(stress_id="duplicate_stress"),
            _observation(fund_id="fund_b", stress_id="duplicate_stress"),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        build_market_research_crypto_etf_creation_redemption_stress_digest(
            ("not-an-observation",),  # type: ignore[arg-type]
            config=_config(),
            generated_at=GENERATED_AT,
        )

    valid_row = _report(_observation()).rows[0]
    with pytest.raises(ValueError, match="redemption_pressure_usd"):
        replace(valid_row, redemption_pressure_usd=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(valid_row, reason_codes=(READY_REASON, REDEMPTION_PRESSURE_USD_REASON))

    frozen_observation = _observation("fund_frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.fund_id = "changed"  # type: ignore[misc]


def test_reason_counts_reject_zero_fractional_and_must_reconcile_with_rows() -> None:
    report = _report(_observation("fund_reason_counts"))

    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount(
            reason_code=READY_REASON,
            count=d("0.000000"),
            observation_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="count must be integral"):
        MarketResearchCryptoEtfCreationRedemptionStressDigestReasonCodeCount(
            reason_code=READY_REASON,
            count=d("1.500000"),
            observation_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            report,
            reason_code_counts=(
                replace(report.reason_code_counts[0], count=d("2.000000")),
            ),
        )


def test_hard_flags_are_enforced_on_all_public_records() -> None:
    report = _report(_observation("fund_flags"))
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
        replace(_observation("fund_report_only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count paper_only must be True"):
        replace(report.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(report, paper_only=False)


def test_public_numerics_payload_serialization_and_tamper_revalidation() -> None:
    report = _report(_observation("fund_payload"))

    for public_record in (
        _config(),
        _observation("fund_numeric"),
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

    payload = market_research_crypto_etf_creation_redemption_stress_digest_payload(
        report,
    )
    payload_text = repr(payload).lower()
    for forbidden in (
        "as" + "dict",
        "market" + "_" + "slug",
        "ques" + "tion",
        "payload" + "_" + "json",
        "wa" + "llet",
        "or" + "der",
        "au" + "th",
        "private",
    ):
        assert forbidden not in payload_text
    assert isinstance(payload, MappingProxyType)
    assert payload["generated_at"] == "2026-07-05T16:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["total_redemption_pressure_usd"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-05T16:00:00+00:00"
    assert payload["rows"][0]["creations_usd"] == "20000000.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["creations_usd"] = "0.000000"  # type: ignore[index]

    tampered_report = _report(_observation("fund_bad_numeric"))
    object.__setattr__(tampered_report, "observation_count", 1)
    with pytest.raises(ValueError, match="observation_count must be a Decimal"):
        market_research_crypto_etf_creation_redemption_stress_digest_payload(tampered_report)

    tampered_report = _report(_observation("fund_bad_time"))
    object.__setattr__(
        tampered_report,
        "generated_at",
        datetime(2026, 7, 5, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        market_research_crypto_etf_creation_redemption_stress_digest_payload(tampered_report)

    tampered_report = _report(
        _observation(
            "fund_nested_tamper",
            "nested_tamper_stress",
            creations_usd=d("0.000000"),
            redemptions_usd=d("52000000.000000"),
            available_cash_usd=d("20000000.000000"),
            underlying_liquidity_usd=d("2000000000.000000"),
        ),
    )
    object.__setattr__(
        tampered_report.rows[0],
        "reason_codes",
        tuple(reversed(tampered_report.rows[0].reason_codes)),
    )
    with pytest.raises(ValueError, match="reason_codes must use canonical sequence"):
        market_research_crypto_etf_creation_redemption_stress_digest_payload(tampered_report)


def test_module_scope_excludes_forbidden_surfaces() -> None:
    module = __import__(
        "polymarket_alpha_lab.market_research_crypto_etf_creation_redemption_stress_digest",
        fromlist=["_"],
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "as" + "dict",
        "market" + "_" + "slug",
        "ques" + "tion",
        "payload" + "_" + "json",
        "wa" + "llet",
        "or" + "der",
        "au" + "th",
        "private",
        "key",
        "trading",
        "trade",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "database",
        "supabase",
        "persist",
        "sqlite",
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
        or field_name.endswith("_confidence")
        or field_name
        in {
            "confidence",
            "min_confidence",
            "average_confidence",
        }
    )
