from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_bridge_withdrawal_delay_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_WITHDRAWAL_DELAY_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoBridgeWithdrawalDelayDigestConfig,
    MarketResearchCryptoBridgeWithdrawalDelayDigestReasonCodeCount,
    MarketResearchCryptoBridgeWithdrawalDelayDigestReport,
    MarketResearchCryptoBridgeWithdrawalDelayDigestRow,
    MarketResearchCryptoBridgeWithdrawalDelayObservation,
    build_market_research_crypto_bridge_withdrawal_delay_digest,
    market_research_crypto_bridge_withdrawal_delay_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


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
) -> MarketResearchCryptoBridgeWithdrawalDelayDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_WITHDRAWAL_DELAY_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("1800.000000"),
        "watch_delay_seconds": d("3600.000000"),
        "blocked_delay_seconds": d("14400.000000"),
        "max_pending_withdrawal_ratio": d("0.350000"),
        "max_fee_spike_ratio": d("0.500000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoBridgeWithdrawalDelayDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    bridge_delay_key: str = "arb_eth_withdrawal_delay",
    *,
    bridge_name: str = "Arbitrum",
    asset_symbol: str = "ETH",
    observed_at: datetime = GENERATED_AT,
    withdrawal_delay_seconds: Decimal = d("1800.000000"),
    baseline_delay_seconds: Decimal = d("900.000000"),
    pending_withdrawal_usd: Decimal = d("1000000.000000"),
    bridge_tvl_usd: Decimal = d("10000000.000000"),
    median_fee_usd: Decimal = d("3.000000"),
    baseline_fee_usd: Decimal = d("2.000000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "bridge-delay-source-v0",
) -> MarketResearchCryptoBridgeWithdrawalDelayObservation:
    return MarketResearchCryptoBridgeWithdrawalDelayObservation(
        condition_id=condition_id,
        bridge_delay_key=bridge_delay_key,
        bridge_name=bridge_name,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        withdrawal_delay_seconds=withdrawal_delay_seconds,
        baseline_delay_seconds=baseline_delay_seconds,
        pending_withdrawal_usd=pending_withdrawal_usd,
        bridge_tvl_usd=bridge_tvl_usd,
        median_fee_usd=median_fee_usd,
        baseline_fee_usd=baseline_fee_usd,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchCryptoBridgeWithdrawalDelayObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoBridgeWithdrawalDelayDigestConfig | None = None,
) -> MarketResearchCryptoBridgeWithdrawalDelayDigestReport:
    return build_market_research_crypto_bridge_withdrawal_delay_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_bridge_withdrawal_delay_digest_models_delay_pressure_and_confidence() -> None:
    report = _report(
        _observation(
            "condition_beta",
            "op_usdc_withdrawal_delay",
            bridge_name="Optimism",
            asset_symbol="USDC",
            observed_at=GENERATED_AT - timedelta(seconds=2_400),
            withdrawal_delay_seconds=d("18000.000000"),
            baseline_delay_seconds=d("3600.000000"),
            pending_withdrawal_usd=d("8000000.000000"),
            bridge_tvl_usd=d("10000000.000000"),
            median_fee_usd=d("7.000000"),
            baseline_fee_usd=d("3.000000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _observation(
            "condition_alpha",
            "arb_eth_withdrawal_delay",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_bridge_withdrawal_delay_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.withdrawal_delay_observation_count == d("1.000000")
    assert report.delay_expansion_observation_count == d("1.000000")
    assert report.pending_withdrawal_pressure_observation_count == d("1.000000")
    assert report.fee_spike_observation_count == d("1.000000")
    assert report.source_diversity_gap_observation_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.average_withdrawal_delay_seconds == d("9900.000000")
    assert report.average_delay_expansion_ratio == d("2.500000")
    assert report.average_pending_withdrawal_ratio == d("0.450000")
    assert report.average_fee_spike_ratio == d("0.916666")
    assert report.max_observation_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.bridge_delay_key) for row in report.rows) == (
        ("condition_beta", "op_usdc_withdrawal_delay"),
        ("condition_alpha", "arb_eth_withdrawal_delay"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.observation_age_seconds == d("2400.000000")
    assert beta.delay_expansion_ratio == d("4.000000")
    assert beta.pending_withdrawal_ratio == d("0.800000")
    assert beta.fee_spike_ratio == d("1.333333")
    assert beta.reason_codes == (
        "market_research_crypto_bridge_withdrawal_delay_digest_withdrawal_delay",
        "market_research_crypto_bridge_withdrawal_delay_digest_delay_expansion",
        "market_research_crypto_bridge_withdrawal_delay_digest_pending_withdrawal_pressure",
        "market_research_crypto_bridge_withdrawal_delay_digest_fee_spike",
        "market_research_crypto_bridge_withdrawal_delay_digest_source_diversity_gap",
        "market_research_crypto_bridge_withdrawal_delay_digest_stale_observation",
        "market_research_crypto_bridge_withdrawal_delay_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_bridge_withdrawal_delay_digest_normalizes_timezones_reason_counts_and_sources() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _observation(
            "condition_gamma",
            "base_eth_withdrawal_delay",
            bridge_name="Base",
            observed_at=observed_at,
            source_count=d("2.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert report.max_observation_age_seconds == d("3600.000000")
    assert report.digest_status == "blocked"
    assert report.reason_code_counts == (
        MarketResearchCryptoBridgeWithdrawalDelayDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_bridge_withdrawal_delay_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        MarketResearchCryptoBridgeWithdrawalDelayDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_bridge_withdrawal_delay_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("base_eth_withdrawal_delay", "bridge-delay-source-v0"),
    )


def test_bridge_withdrawal_delay_digest_empty_input_is_watch_and_sorted_deterministically() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.observation_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_bridge_withdrawal_delay_digest_no_inputs",
    )

    first = _report(
        _observation("condition_b", "source_b"),
        _observation("condition_a", "source_a"),
    )
    second = _report(
        _observation("condition_a", "source_a"),
        _observation("condition_b", "source_b"),
    )

    assert first == second
    assert tuple(row.bridge_delay_key for row in first.rows) == ("source_a", "source_b")


def test_bridge_withdrawal_delay_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoBridgeWithdrawalDelayDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoBridgeWithdrawalDelayObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoBridgeWithdrawalDelayDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoBridgeWithdrawalDelayDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("bridge-delay-v0"))
    with pytest.raises(ValueError, match="watch_delay_seconds"):
        _config(watch_delay_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=0.8)
    with pytest.raises(ValueError, match="condition_id"):
        _observation(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        _observation(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _observation().paper_only = False  # type: ignore[misc]


def test_bridge_withdrawal_delay_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_observation())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_ratio")
                or field.name.endswith("_usd")
                or field.name == "confidence"
            ):
                assert type(value) is Decimal
    for field in fields(report):
        value = getattr(report, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_usd")
        ):
            assert type(value) is Decimal
    for reason_count in report.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.observation_ratio) is Decimal

    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoBridgeWithdrawalDelayDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_WITHDRAWAL_DELAY_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_crypto_bridge_withdrawal_delay_digest"
            ),
            observation_count=1,  # type: ignore[arg-type]
            ready_observation_count=d("1.000000"),
            watch_observation_count=d("0.000000"),
            blocked_observation_count=d("0.000000"),
            withdrawal_delay_observation_count=d("0.000000"),
            delay_expansion_observation_count=d("0.000000"),
            pending_withdrawal_pressure_observation_count=d("0.000000"),
            fee_spike_observation_count=d("0.000000"),
            source_diversity_gap_observation_count=d("0.000000"),
            stale_observation_count=d("0.000000"),
            confidence_gap_observation_count=d("0.000000"),
            average_withdrawal_delay_seconds=d("1800.000000"),
            average_delay_expansion_ratio=d("1.000000"),
            average_pending_withdrawal_ratio=d("0.100000"),
            average_fee_spike_ratio=d("0.500000"),
            max_observation_age_seconds=d("0.000000"),
            max_allowed_observation_age_seconds=d("1800.000000"),
            watch_delay_seconds=d("3600.000000"),
            blocked_delay_seconds=d("14400.000000"),
            max_pending_withdrawal_ratio=d("0.350000"),
            max_fee_spike_ratio=d("0.500000"),
            min_source_count=d("3.000000"),
            min_confidence=d("0.700000"),
            rows=report.rows,
            source_config_versions=(
                ("arb_eth_withdrawal_delay", "bridge-delay-source-v0"),
            ),
            reason_code_counts=report.reason_code_counts,
            reason_codes=(
                "market_research_crypto_bridge_withdrawal_delay_digest_ready",
            ),
        )


def test_bridge_withdrawal_delay_digest_payload_is_immutable_redacted_and_report_only() -> None:
    payload = market_research_crypto_bridge_withdrawal_delay_digest_payload(
        _report(
            _observation(
                "condition_redacted",
                "arb_eth_withdrawal_delay_redacted",
                bridge_name="Arbitrum",
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
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["rows"][0]["withdrawal_delay_seconds"] == "1800.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["withdrawal_delay_seconds"] = "1.000000"  # type: ignore[index]


def test_bridge_withdrawal_delay_digest_rejects_duplicates_and_bad_report_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(bridge_delay_key="duplicate"),
            _observation(bridge_delay_key="duplicate"),
        )

    valid = _report(_observation())
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(MarketResearchCryptoBridgeWithdrawalDelayDigestReport)
    }
    assert (
        MarketResearchCryptoBridgeWithdrawalDelayDigestReport(**kwargs).digest_status
        == "ready"
    )

    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoBridgeWithdrawalDelayDigestReport(
            **{**kwargs, "observation_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoBridgeWithdrawalDelayDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoBridgeWithdrawalDelayDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoBridgeWithdrawalDelayDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_bridge_withdrawal_delay_digest_ready"
                        ),
                        count=d("2.000000"),
                        observation_ratio=d("1.000000"),
                    ),
                ),
            },
        )


def test_bridge_withdrawal_delay_digest_module_scope_excludes_execution_io_network_and_persistence() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_bridge_withdrawal_delay_digest",
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
    )
    assert not any(token in lowered for token in forbidden_literals)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"open", "eval", "exec", "__import__"}

    assert imported_modules <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "types",
        "typing",
    }
