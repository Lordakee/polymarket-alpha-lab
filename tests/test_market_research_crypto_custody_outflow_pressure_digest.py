from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_custody_outflow_pressure_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_CUSTODY_OUTFLOW_PRESSURE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoCustodyOutflowPressureDigestConfig,
    MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount,
    MarketResearchCryptoCustodyOutflowPressureDigestReport,
    MarketResearchCryptoCustodyOutflowPressureDigestRow,
    MarketResearchCryptoCustodyOutflowPressureObservation,
    build_market_research_crypto_custody_outflow_pressure_digest,
    market_research_crypto_custody_outflow_pressure_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


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
) -> MarketResearchCryptoCustodyOutflowPressureDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_CUSTODY_OUTFLOW_PRESSURE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("1800.000000"),
        "watch_outflow_ratio": d("0.050000"),
        "blocked_outflow_ratio": d("0.100000"),
        "max_outflow_growth_ratio": d("0.500000"),
        "max_withdrawal_queue_ratio": d("0.200000"),
        "max_withdrawal_wait_hours": d("24.000000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoCustodyOutflowPressureDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    custody_pressure_key: str = "coinbase_btc_custody_pressure",
    *,
    venue_name: str = "coinbase",
    venue_type: str = "exchange",
    asset_symbol: str = "BTC",
    observed_at: datetime = GENERATED_AT,
    net_outflow_usd: Decimal = d("250000000.000000"),
    previous_net_outflow_usd: Decimal = d("240000000.000000"),
    assets_under_custody_usd: Decimal = d("20000000000.000000"),
    withdrawal_queue_usd: Decimal = d("50000000.000000"),
    daily_withdrawal_capacity_usd: Decimal = d("500000000.000000"),
    estimated_withdrawal_wait_hours: Decimal = d("4.000000"),
    source_count: Decimal = d("4.000000"),
    confidence: Decimal = d("0.840000"),
    source_config_version: str = "custody-pressure-source-v0",
) -> MarketResearchCryptoCustodyOutflowPressureObservation:
    return MarketResearchCryptoCustodyOutflowPressureObservation(
        condition_id=condition_id,
        custody_pressure_key=custody_pressure_key,
        venue_name=venue_name,
        venue_type=venue_type,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        net_outflow_usd=net_outflow_usd,
        previous_net_outflow_usd=previous_net_outflow_usd,
        assets_under_custody_usd=assets_under_custody_usd,
        withdrawal_queue_usd=withdrawal_queue_usd,
        daily_withdrawal_capacity_usd=daily_withdrawal_capacity_usd,
        estimated_withdrawal_wait_hours=estimated_withdrawal_wait_hours,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchCryptoCustodyOutflowPressureObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoCustodyOutflowPressureDigestConfig | None = None,
) -> MarketResearchCryptoCustodyOutflowPressureDigestReport:
    return build_market_research_crypto_custody_outflow_pressure_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_custody_outflow_pressure_digest_blocks_probability_screening() -> None:
    report = _report(
        _observation(
            "condition_beta",
            "binance_eth_custody_pressure",
            venue_name="binance",
            asset_symbol="ETH",
            observed_at=GENERATED_AT - timedelta(seconds=2400),
            net_outflow_usd=d("2500000000.000000"),
            previous_net_outflow_usd=d("1000000000.000000"),
            assets_under_custody_usd=d("10000000000.000000"),
            withdrawal_queue_usd=d("4000000000.000000"),
            daily_withdrawal_capacity_usd=d("1000000000.000000"),
            estimated_withdrawal_wait_hours=d("48.000000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _observation(
            "condition_alpha",
            "coinbase_btc_custody_pressure",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_custody_outflow_pressure_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.pass_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.outflow_pressure_observation_count == d("1.000000")
    assert report.outflow_watch_observation_count == d("0.000000")
    assert report.outflow_growth_observation_count == d("1.000000")
    assert report.withdrawal_queue_pressure_observation_count == d("1.000000")
    assert report.withdrawal_wait_observation_count == d("1.000000")
    assert report.source_diversity_gap_observation_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.average_outflow_ratio == d("0.131250")
    assert report.average_outflow_growth_ratio == d("0.770834")
    assert report.average_withdrawal_queue_ratio == d("2.050000")
    assert report.average_estimated_withdrawal_wait_hours == d("26.000000")
    assert report.max_observation_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.custody_pressure_key) for row in report.rows) == (
        ("condition_beta", "binance_eth_custody_pressure"),
        ("condition_alpha", "coinbase_btc_custody_pressure"),
    )
    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.observation_age_seconds == d("2400.000000")
    assert blocked.outflow_ratio == d("0.250000")
    assert blocked.outflow_growth_ratio == d("1.500000")
    assert blocked.withdrawal_queue_ratio == d("4.000000")
    assert blocked.reason_codes == (
        "market_research_crypto_custody_outflow_pressure_digest_outflow_pressure",
        "market_research_crypto_custody_outflow_pressure_digest_outflow_growth",
        "market_research_crypto_custody_outflow_pressure_digest_withdrawal_queue_pressure",
        "market_research_crypto_custody_outflow_pressure_digest_withdrawal_wait",
        "market_research_crypto_custody_outflow_pressure_digest_source_diversity_gap",
        "market_research_crypto_custody_outflow_pressure_digest_stale_observation",
        "market_research_crypto_custody_outflow_pressure_digest_confidence_gap",
    )
    assert report.reason_codes == blocked.reason_codes


def test_custody_outflow_pressure_digest_normalizes_timezones_reason_counts_and_sources() -> None:
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _observation(
            "condition_gamma",
            "bitgo_eth_custody_pressure",
            venue_name="bitgo",
            venue_type="custodian",
            asset_symbol="ETH",
            observed_at=observed_at,
            net_outflow_usd=d("300000000.000000"),
            previous_net_outflow_usd=d("300000000.000000"),
            assets_under_custody_usd=d("5000000000.000000"),
            source_count=d("2.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert report.max_observation_age_seconds == d("3600.000000")
    assert report.digest_status == "blocked"
    assert report.reason_code_counts == (
        MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_custody_outflow_pressure_digest_outflow_watch"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_custody_outflow_pressure_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_custody_outflow_pressure_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert all(item.paper_only and item.report_only and item.readonly for item in report.reason_code_counts)
    assert report.source_config_versions == (
        ("bitgo_eth_custody_pressure", "custody-pressure-source-v0"),
    )


def test_custody_outflow_pressure_digest_empty_input_blocks_and_sorts_deterministically() -> None:
    empty = _report()
    assert empty.digest_status == "blocked"
    assert empty.observation_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_custody_outflow_pressure_digest_no_inputs",
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
    assert tuple(row.custody_pressure_key for row in first.rows) == ("source_a", "source_b")
    for row in first.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))


def test_custody_outflow_pressure_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoCustodyOutflowPressureDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoCustodyOutflowPressureObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoCustodyOutflowPressureDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoCustodyOutflowPressureDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("custody-pressure-v0"))
    with pytest.raises(ValueError, match="watch_outflow_ratio"):
        _config(watch_outflow_ratio=_DecimalSubclass("0.050000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_id"):
        _observation(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="venue_type"):
        _observation(venue_type="desk")
    with pytest.raises(ValueError, match="redacted"):
        _observation(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(custody_pressure_key="duplicate"),
            _observation(custody_pressure_key="duplicate"),
        )
    with pytest.raises(FrozenInstanceError):
        _observation().paper_only = False  # type: ignore[misc]


def test_custody_outflow_pressure_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_observation())

    for public_record in (
        _config(),
        _observation("condition_decimal", "decimal_pressure"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if _is_public_numeric_field(field.name) or field.name == "confidence":
                assert type(value) is Decimal, field.name

    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoCustodyOutflowPressureDigestReport)
    }
    assert (
        MarketResearchCryptoCustodyOutflowPressureDigestReport(**kwargs).digest_status
        == "pass"
    )

    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoCustodyOutflowPressureDigestReport(
            **{**kwargs, "observation_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoCustodyOutflowPressureDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoCustodyOutflowPressureDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoCustodyOutflowPressureDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_custody_outflow_pressure_digest_pass"
                        ),
                        count=d("2.000000"),
                        observation_ratio=d("1.000000"),
                    ),
                ),
            },
        )


def test_custody_outflow_pressure_digest_payload_uses_string_numerics_and_is_immutable() -> None:
    payload = market_research_crypto_custody_outflow_pressure_digest_payload(
        _report(
            _observation(
                "condition_redacted",
                "kraken_btc_custody_pressure",
                venue_name="kraken",
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
    assert payload["observation_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["net_outflow_usd"] == "250000000.000000"
    assert payload["rows"][0]["outflow_ratio"] == "0.012500"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["net_outflow_usd"] = "0.000000"  # type: ignore[index]


def test_custody_outflow_pressure_digest_module_scope_excludes_io_network_and_live_mutation_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_custody_outflow_pressure_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "market_slug",
        "question",
        "live trading",
        "auth",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange mutation",
        "payload_json",
        "psycopg",
        "supabase",
        "sqlite",
    )
    assert not any(token in lowered for token in forbidden_literals)

    imported_modules: set[str] = set()
    forbidden_call_names = {
        "__import__",
        "connect",
        "exec",
        "eval",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    assert imported_modules <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "types",
        "typing",
    }


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_seconds")
        or field_name.endswith("_usd")
        or field_name.endswith("_hours")
    )
