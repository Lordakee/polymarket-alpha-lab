from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_crypto_oracle_failure_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_FAILURE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoOracleFailureDigestConfig,
    MarketResearchCryptoOracleFailureDigestReasonCodeCount,
    MarketResearchCryptoOracleFailureDigestReport,
    MarketResearchCryptoOracleFailureDigestRow,
    MarketResearchCryptoOracleFailureSnapshot,
    build_market_research_crypto_oracle_failure_digest,
    market_research_crypto_oracle_failure_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_crypto_oracle_failure_digest.py",
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


def _config(**overrides: object) -> MarketResearchCryptoOracleFailureDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_FAILURE_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("1800.000000"),
        "max_feed_lag_seconds": d("600.000000"),
        "max_price_divergence_abs": d("0.030000"),
        "max_conflict_ratio": d("0.200000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoOracleFailureDigestConfig(**values)


def _snapshot(
    condition_id: str = "condition_alpha",
    oracle_key: str = "eth_usd_chainlink",
    *,
    asset_symbol: str = "ETH",
    observed_at: datetime = GENERATED_AT,
    feed_updated_at: datetime = GENERATED_AT - timedelta(seconds=120),
    reference_price: Decimal = d("3000.000000"),
    oracle_price: Decimal = d("2998.000000"),
    source_count: Decimal = d("3.000000"),
    conflicting_source_count: Decimal = d("0.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "oracle-failure-source-v0",
) -> MarketResearchCryptoOracleFailureSnapshot:
    return MarketResearchCryptoOracleFailureSnapshot(
        condition_id=condition_id,
        oracle_key=oracle_key,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        feed_updated_at=feed_updated_at,
        reference_price=reference_price,
        oracle_price=oracle_price,
        source_count=source_count,
        conflicting_source_count=conflicting_source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoOracleFailureSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoOracleFailureDigestConfig | None = None,
) -> MarketResearchCryptoOracleFailureDigestReport:
    return build_market_research_crypto_oracle_failure_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_floats(item)


def test_oracle_failure_digest_models_lag_divergence_conflicts_and_confidence() -> None:
    report = _report(
        _snapshot(
            "condition_beta",
            "btc_usd_pyth",
            asset_symbol="BTC",
            observed_at=GENERATED_AT - timedelta(seconds=2_400),
            feed_updated_at=GENERATED_AT - timedelta(seconds=3_600),
            reference_price=d("65000.000000"),
            oracle_price=d("62000.000000"),
            source_count=d("2.000000"),
            conflicting_source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _snapshot(
            "condition_alpha",
            "eth_usd_chainlink",
            observed_at=GENERATED_AT - timedelta(seconds=120),
            feed_updated_at=GENERATED_AT - timedelta(seconds=180),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_oracle_failure_digest"
    )
    assert report.snapshot_count == d("2.000000")
    assert report.ready_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.feed_lag_snapshot_count == d("1.000000")
    assert report.price_divergence_snapshot_count == d("1.000000")
    assert report.source_diversity_gap_snapshot_count == d("1.000000")
    assert report.source_conflict_snapshot_count == d("1.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.confidence_gap_snapshot_count == d("1.000000")
    assert report.average_price_divergence == d("-0.023410")
    assert report.average_price_divergence_abs == d("0.023410")
    assert report.average_conflict_ratio == d("0.250000")
    assert report.max_snapshot_age_seconds == d("2400.000000")
    assert report.max_feed_lag_seconds == d("1200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.oracle_key) for row in report.rows) == (
        ("condition_beta", "btc_usd_pyth"),
        ("condition_alpha", "eth_usd_chainlink"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.snapshot_age_seconds == d("2400.000000")
    assert beta.feed_lag_seconds == d("1200.000000")
    assert beta.price_divergence == d("-0.046154")
    assert beta.price_divergence_abs == d("0.046154")
    assert beta.source_conflict_ratio == d("0.500000")
    assert beta.reason_codes == (
        "market_research_crypto_oracle_failure_digest_feed_lag",
        "market_research_crypto_oracle_failure_digest_price_divergence",
        "market_research_crypto_oracle_failure_digest_source_diversity_gap",
        "market_research_crypto_oracle_failure_digest_source_conflict",
        "market_research_crypto_oracle_failure_digest_stale_snapshot",
        "market_research_crypto_oracle_failure_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_oracle_failure_digest_normalizes_timezones_and_reason_counts() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=1)))
    feed_updated_at = datetime(2026, 7, 2, 11, 45, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "condition_gamma",
            "sol_usd_pyth",
            asset_symbol="SOL",
            observed_at=observed_at,
            feed_updated_at=feed_updated_at,
            source_count=d("2.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert report.rows[0].feed_updated_at == datetime(2026, 7, 2, 10, 45, tzinfo=UTC)
    assert report.max_snapshot_age_seconds == d("3600.000000")
    assert report.max_feed_lag_seconds == d("900.000000")
    assert report.digest_status == "blocked"
    assert report.reason_code_counts == (
        MarketResearchCryptoOracleFailureDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_oracle_failure_digest_feed_lag"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        MarketResearchCryptoOracleFailureDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_oracle_failure_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        MarketResearchCryptoOracleFailureDigestReasonCodeCount(
            reason_code="market_research_crypto_oracle_failure_digest_stale_snapshot",
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_usd_pyth", "oracle-failure-source-v0"),
    )


def test_oracle_failure_digest_empty_input_is_watch_and_sorted_deterministically() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_oracle_failure_digest_no_inputs",
    )

    first = _report(
        _snapshot("condition_b", "source_b"),
        _snapshot("condition_a", "source_a"),
    )
    second = _report(
        _snapshot("condition_a", "source_a"),
        _snapshot("condition_b", "source_b"),
    )

    assert first == second
    assert tuple(row.oracle_key for row in first.rows) == ("source_a", "source_b")


def test_oracle_failure_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoOracleFailureDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoOracleFailureSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoOracleFailureDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoOracleFailureDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("oracle-failure-v0"))
    with pytest.raises(ValueError, match="max_price_divergence_abs"):
        _config(max_price_divergence_abs=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=0.8)
    with pytest.raises(ValueError, match="condition_id"):
        _snapshot(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        _snapshot(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="feed_updated_at"):
        _snapshot(
            feed_updated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(feed_updated_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]


def test_oracle_failure_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_snapshot())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_price")
                or field.name.endswith("_ratio")
                or field.name.endswith("_abs")
                or field.name == "confidence"
                or field.name == "price_divergence"
            ):
                assert type(value) is Decimal
    for field in fields(report):
        value = getattr(report, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_price")
            or field.name.endswith("_abs")
        ):
            assert type(value) is Decimal
    for reason_count in report.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.snapshot_ratio) is Decimal

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoOracleFailureDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_FAILURE_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_crypto_oracle_failure_digest"
            ),
            snapshot_count=1,  # type: ignore[arg-type]
            ready_snapshot_count=d("1.000000"),
            watch_snapshot_count=d("0.000000"),
            blocked_snapshot_count=d("0.000000"),
            feed_lag_snapshot_count=d("0.000000"),
            price_divergence_snapshot_count=d("0.000000"),
            source_diversity_gap_snapshot_count=d("0.000000"),
            source_conflict_snapshot_count=d("0.000000"),
            stale_snapshot_count=d("0.000000"),
            confidence_gap_snapshot_count=d("0.000000"),
            average_price_divergence=d("-0.000667"),
            average_price_divergence_abs=d("0.000667"),
            average_conflict_ratio=d("0.000000"),
            max_snapshot_age_seconds=d("0.000000"),
            max_feed_lag_seconds=d("120.000000"),
            max_allowed_snapshot_age_seconds=d("1800.000000"),
            max_allowed_feed_lag_seconds=d("600.000000"),
            max_allowed_price_divergence_abs=d("0.030000"),
            max_allowed_conflict_ratio=d("0.200000"),
            min_source_count=d("3.000000"),
            min_confidence=d("0.700000"),
            rows=report.rows,
            source_config_versions=(("eth_usd_chainlink", "oracle-failure-source-v0"),),
            reason_code_counts=report.reason_code_counts,
            reason_codes=("market_research_crypto_oracle_failure_digest_ready",),
        )


def test_oracle_failure_digest_payload_is_immutable_redacted_and_report_only() -> None:
    payload = market_research_crypto_oracle_failure_digest_payload(
        _report(
            _snapshot(
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
        "token",
        "secret",
        "private",
        "0x",
    ):
        assert forbidden not in payload_text
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["payload_kind"] == (
        "market_research_crypto_oracle_failure_digest"
    )
    assert_no_floats(payload)
    assert payload["snapshot_count"] == "1.000000"
    assert payload["rows"][0]["oracle_key"] == "eth_usd_chainlink_redacted"
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "2.000000"  # type: ignore[index]


def test_oracle_failure_digest_static_source_is_pure_and_safe() -> None:
    source = MODULE_PATH.read_text()
    lowered = source.lower()
    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "token",
        "secret",
        "private",
        "0x",
        "auth",
        "account",
        "balance",
        "cancel",
        "replace",
        "exchange_mutation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    }
    forbidden_calls = {
        "open",
        "__import__",
        "connect",
        "request",
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "send",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
            assert not isinstance(node.value, int) or isinstance(node.value, bool)
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "int", "open", "__import__"}
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def test_oracle_failure_digest_module_stays_unwired() -> None:
    root = MODULE_PATH.parent
    needle = "market_research_crypto_oracle_failure_digest"
    references: list[str] = []
    for path in root.glob("*.py"):
        if path == MODULE_PATH:
            continue
        if needle in path.read_text():
            references.append(str(path))

    assert references == []


def test_oracle_failure_digest_import_surface_is_explicit() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_oracle_failure_digest",
    )

    assert set(module.__all__) == {
        "DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_FAILURE_DIGEST_CONFIG_VERSION",
        "MarketResearchCryptoOracleFailureDigestConfig",
        "MarketResearchCryptoOracleFailureDigestReasonCodeCount",
        "MarketResearchCryptoOracleFailureDigestReport",
        "MarketResearchCryptoOracleFailureDigestRow",
        "MarketResearchCryptoOracleFailureSnapshot",
        "build_market_research_crypto_oracle_failure_digest",
        "market_research_crypto_oracle_failure_digest_payload",
    }
