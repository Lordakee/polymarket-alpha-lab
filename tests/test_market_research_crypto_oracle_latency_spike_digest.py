from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_crypto_oracle_latency_spike_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_LATENCY_SPIKE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoOracleLatencySpikeDigestConfig,
    MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount,
    MarketResearchCryptoOracleLatencySpikeDigestReport,
    MarketResearchCryptoOracleLatencySpikeDigestRow,
    MarketResearchCryptoOracleLatencySpikeObservation,
    build_market_research_crypto_oracle_latency_spike_digest,
    market_research_crypto_oracle_latency_spike_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_crypto_oracle_latency_spike_digest.py",
)


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


def _config(**overrides: object) -> MarketResearchCryptoOracleLatencySpikeDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_LATENCY_SPIKE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("1800.000000"),
        "watch_latency_spike_ratio": d("0.500000"),
        "blocked_latency_spike_ratio": d("1.500000"),
        "max_publish_lag_seconds": d("300.000000"),
        "max_confirm_lag_seconds": d("600.000000"),
        "max_round_gap_ratio": d("0.250000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoOracleLatencySpikeDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    oracle_key: str = "eth_usd_chainlink",
    *,
    asset_symbol: str = "ETH",
    observed_at: datetime = GENERATED_AT,
    published_at: datetime = GENERATED_AT - timedelta(seconds=45),
    confirmed_at: datetime = GENERATED_AT - timedelta(seconds=30),
    observed_latency_seconds: Decimal = d("45.000000"),
    baseline_latency_seconds: Decimal = d("40.000000"),
    p95_latency_seconds: Decimal = d("90.000000"),
    baseline_p95_latency_seconds: Decimal = d("80.000000"),
    round_gap_ratio: Decimal = d("0.050000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "oracle-latency-source-v0",
) -> MarketResearchCryptoOracleLatencySpikeObservation:
    return MarketResearchCryptoOracleLatencySpikeObservation(
        condition_id=condition_id,
        oracle_key=oracle_key,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        published_at=published_at,
        confirmed_at=confirmed_at,
        observed_latency_seconds=observed_latency_seconds,
        baseline_latency_seconds=baseline_latency_seconds,
        p95_latency_seconds=p95_latency_seconds,
        baseline_p95_latency_seconds=baseline_p95_latency_seconds,
        round_gap_ratio=round_gap_ratio,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchCryptoOracleLatencySpikeObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoOracleLatencySpikeDigestConfig | None = None,
) -> MarketResearchCryptoOracleLatencySpikeDigestReport:
    return build_market_research_crypto_oracle_latency_spike_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_oracle_latency_spike_digest_models_latency_and_confidence() -> None:
    report = _report(
        _observation(
            "condition_beta",
            "btc_usd_pyth",
            asset_symbol="BTC",
            observed_at=GENERATED_AT - timedelta(seconds=2_400),
            published_at=GENERATED_AT - timedelta(seconds=900),
            confirmed_at=GENERATED_AT - timedelta(seconds=1_200),
            observed_latency_seconds=d("120.000000"),
            baseline_latency_seconds=d("30.000000"),
            p95_latency_seconds=d("300.000000"),
            baseline_p95_latency_seconds=d("75.000000"),
            round_gap_ratio=d("0.400000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _observation(
            "condition_alpha",
            "eth_usd_chainlink",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-oracle-latency-spike-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_oracle_latency_spike_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.latency_spike_observation_count == d("1.000000")
    assert report.p95_latency_spike_observation_count == d("1.000000")
    assert report.publish_lag_observation_count == d("1.000000")
    assert report.confirm_lag_observation_count == d("1.000000")
    assert report.round_gap_observation_count == d("1.000000")
    assert report.source_diversity_gap_observation_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.average_latency_spike_ratio == d("1.562500")
    assert report.average_p95_latency_spike_ratio == d("1.562500")
    assert report.average_round_gap_ratio == d("0.225000")
    assert report.average_publish_lag_seconds == d("472.500000")
    assert report.average_confirm_lag_seconds == d("615.000000")
    assert report.max_observation_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.oracle_key) for row in report.rows) == (
        ("condition_beta", "btc_usd_pyth"),
        ("condition_alpha", "eth_usd_chainlink"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.observation_age_seconds == d("2400.000000")
    assert beta.publish_lag_seconds == d("900.000000")
    assert beta.confirm_lag_seconds == d("1200.000000")
    assert beta.latency_spike_ratio == d("3.000000")
    assert beta.p95_latency_spike_ratio == d("3.000000")
    assert beta.reason_codes == (
        "market_research_crypto_oracle_latency_spike_digest_latency_spike",
        "market_research_crypto_oracle_latency_spike_digest_p95_latency_spike",
        "market_research_crypto_oracle_latency_spike_digest_publish_lag",
        "market_research_crypto_oracle_latency_spike_digest_confirm_lag",
        "market_research_crypto_oracle_latency_spike_digest_round_gap",
        "market_research_crypto_oracle_latency_spike_digest_source_diversity_gap",
        "market_research_crypto_oracle_latency_spike_digest_stale_observation",
        "market_research_crypto_oracle_latency_spike_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_oracle_latency_spike_digest_normalizes_timezones_reason_counts_and_sources() -> None:
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=1)))
    published_at = datetime(2026, 7, 4, 11, 30, tzinfo=timezone(timedelta(hours=1)))
    confirmed_at = datetime(2026, 7, 4, 11, 20, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _observation(
            "condition_gamma",
            "sol_usd_pyth",
            asset_symbol="SOL",
            observed_at=observed_at,
            published_at=published_at,
            confirmed_at=confirmed_at,
            source_count=d("2.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert report.rows[0].published_at == datetime(2026, 7, 4, 10, 30, tzinfo=UTC)
    assert report.rows[0].confirmed_at == datetime(2026, 7, 4, 10, 20, tzinfo=UTC)
    assert report.max_observation_age_seconds == d("3600.000000")
    assert report.digest_status == "blocked"
    assert report.reason_code_counts == (
        MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_oracle_latency_spike_digest_publish_lag"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_oracle_latency_spike_digest_confirm_lag"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_oracle_latency_spike_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_oracle_latency_spike_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_usd_pyth", "oracle-latency-source-v0"),
    )


def test_oracle_latency_spike_digest_empty_input_is_watch_and_sorted_deterministically() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.observation_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_oracle_latency_spike_digest_no_inputs",
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
    assert tuple(row.oracle_key for row in first.rows) == ("source_a", "source_b")


def test_oracle_latency_spike_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoOracleLatencySpikeDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoOracleLatencySpikeObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoOracleLatencySpikeDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoOracleLatencySpikeDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("oracle-latency-v0"))
    with pytest.raises(ValueError, match="watch_latency_spike_ratio"):
        _config(watch_latency_spike_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_id"):
        _observation(condition_id=_StringSubclass("condition_alpha"))
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
    with pytest.raises(ValueError, match="published_at"):
        _observation(
            published_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="confirmed_at"):
        _observation(
            confirmed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(published_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(confirmed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _observation().paper_only = False  # type: ignore[misc]


def test_oracle_latency_spike_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_observation())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if _is_public_numeric_field(field.name) or field.name == "confidence":
                assert type(value) is Decimal, field.name
    for field in fields(report):
        value = getattr(report, field.name)
        if _is_public_numeric_field(field.name):
            assert type(value) is Decimal, field.name
    for reason_count in report.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.observation_ratio) is Decimal

    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoOracleLatencySpikeDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_LATENCY_SPIKE_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_crypto_oracle_latency_spike_digest"
            ),
            observation_count=1,  # type: ignore[arg-type]
            ready_observation_count=d("1.000000"),
            watch_observation_count=d("0.000000"),
            blocked_observation_count=d("0.000000"),
            latency_spike_observation_count=d("0.000000"),
            p95_latency_spike_observation_count=d("0.000000"),
            publish_lag_observation_count=d("0.000000"),
            confirm_lag_observation_count=d("0.000000"),
            round_gap_observation_count=d("0.000000"),
            source_diversity_gap_observation_count=d("0.000000"),
            stale_observation_count=d("0.000000"),
            confidence_gap_observation_count=d("0.000000"),
            average_latency_spike_ratio=d("0.125000"),
            average_p95_latency_spike_ratio=d("0.125000"),
            average_round_gap_ratio=d("0.050000"),
            average_publish_lag_seconds=d("45.000000"),
            average_confirm_lag_seconds=d("30.000000"),
            max_observation_age_seconds=d("0.000000"),
            max_allowed_observation_age_seconds=d("1800.000000"),
            watch_latency_spike_ratio=d("0.500000"),
            blocked_latency_spike_ratio=d("1.500000"),
            max_publish_lag_seconds=d("300.000000"),
            max_confirm_lag_seconds=d("600.000000"),
            max_round_gap_ratio=d("0.250000"),
            min_source_count=d("3.000000"),
            min_confidence=d("0.700000"),
            rows=report.rows,
            source_config_versions=(("eth_usd_chainlink", "oracle-latency-source-v0"),),
            reason_code_counts=report.reason_code_counts,
            reason_codes=(
                "market_research_crypto_oracle_latency_spike_digest_ready",
            ),
        )


def test_oracle_latency_spike_digest_payload_is_immutable_redacted_and_report_only() -> None:
    payload = market_research_crypto_oracle_latency_spike_digest_payload(
        _report(
            _observation(
                "condition_redacted",
                "eth_usd_chainlink_redacted",
                asset_symbol="ETH",
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
    assert payload["payload_kind"] == (
        "market_research_crypto_oracle_latency_spike_digest"
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["observed_latency_seconds"] == "45.000000"
    assert payload["rows"][0]["paper_only"] is True
    _assert_no_float_int_or_decimal_payload_numbers(payload)
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["observed_latency_seconds"] = "1.000000"  # type: ignore[index]


def test_oracle_latency_spike_digest_rejects_duplicates_and_bad_report_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(oracle_key="duplicate"),
            _observation(oracle_key="duplicate"),
        )

    valid = _report(_observation())
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(MarketResearchCryptoOracleLatencySpikeDigestReport)
    }
    assert MarketResearchCryptoOracleLatencySpikeDigestReport(**kwargs).digest_status == "ready"

    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoOracleLatencySpikeDigestReport(
            **{**kwargs, "observation_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoOracleLatencySpikeDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoOracleLatencySpikeDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_oracle_latency_spike_digest_ready"
                        ),
                        count=d("2.000000"),
                        observation_ratio=d("1.000000"),
                    ),
                ),
            },
        )


def test_oracle_latency_spike_digest_module_scope_excludes_execution_io_network_and_persistence() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_oracle_latency_spike_digest",
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
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
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
    assert MODULE_PATH.read_text() == source_text


def test_oracle_latency_spike_digest_module_stays_unwired() -> None:
    root = MODULE_PATH.parent
    needle = "market_research_crypto_oracle_latency_spike_digest"
    references: list[str] = []
    for path in root.glob("*.py"):
        if path == MODULE_PATH:
            continue
        if needle in path.read_text():
            references.append(str(path))

    assert references == []


def test_oracle_latency_spike_digest_import_surface_is_explicit() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_oracle_latency_spike_digest",
    )

    assert set(module.__all__) == {
        "DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_LATENCY_SPIKE_DIGEST_CONFIG_VERSION",
        "MarketResearchCryptoOracleLatencySpikeDigestConfig",
        "MarketResearchCryptoOracleLatencySpikeDigestReasonCodeCount",
        "MarketResearchCryptoOracleLatencySpikeDigestReport",
        "MarketResearchCryptoOracleLatencySpikeDigestRow",
        "MarketResearchCryptoOracleLatencySpikeObservation",
        "build_market_research_crypto_oracle_latency_spike_digest",
        "market_research_crypto_oracle_latency_spike_digest_payload",
    }


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_seconds")
        or field_name.endswith("_ratio")
    )


def _assert_no_float_int_or_decimal_payload_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_int_or_decimal_payload_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_float_int_or_decimal_payload_numbers(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, (Decimal, float, int))
