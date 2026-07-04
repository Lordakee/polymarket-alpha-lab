from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_stablecoin_redemption_queue_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_STABLECOIN_REDEMPTION_QUEUE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoStablecoinRedemptionQueueDigestConfig,
    MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount,
    MarketResearchCryptoStablecoinRedemptionQueueDigestReport,
    MarketResearchCryptoStablecoinRedemptionQueueDigestRow,
    MarketResearchCryptoStablecoinRedemptionQueueSnapshot,
    build_market_research_crypto_stablecoin_redemption_queue_digest,
    market_research_crypto_stablecoin_redemption_queue_digest_payload,
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
) -> MarketResearchCryptoStablecoinRedemptionQueueDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_STABLECOIN_REDEMPTION_QUEUE_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("1800.000000"),
        "max_redemption_queue_usd": d("750000000.000000"),
        "max_queue_ratio": d("0.120000"),
        "max_queue_growth_ratio": d("0.250000"),
        "max_estimated_wait_hours": d("24.000000"),
        "min_source_count": d("3.000000"),
        "min_reserve_coverage_ratio": d("1.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoStablecoinRedemptionQueueDigestConfig(**values)


def _snapshot(
    condition_id: str = "condition_alpha",
    redemption_queue_key: str = "usdc_redemption_queue",
    *,
    stablecoin_symbol: str = "USDC",
    observed_at: datetime = GENERATED_AT,
    redemption_queue_usd: Decimal = d("250000000.000000"),
    previous_redemption_queue_usd: Decimal = d("200000000.000000"),
    circulating_supply_usd: Decimal = d("30000000000.000000"),
    reserve_coverage_ratio: Decimal = d("1.020000"),
    estimated_wait_hours: Decimal = d("8.000000"),
    source_count: Decimal = d("4.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "redemption-queue-source-v0",
) -> MarketResearchCryptoStablecoinRedemptionQueueSnapshot:
    return MarketResearchCryptoStablecoinRedemptionQueueSnapshot(
        condition_id=condition_id,
        redemption_queue_key=redemption_queue_key,
        stablecoin_symbol=stablecoin_symbol,
        observed_at=observed_at,
        redemption_queue_usd=redemption_queue_usd,
        previous_redemption_queue_usd=previous_redemption_queue_usd,
        circulating_supply_usd=circulating_supply_usd,
        reserve_coverage_ratio=reserve_coverage_ratio,
        estimated_wait_hours=estimated_wait_hours,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoStablecoinRedemptionQueueSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoStablecoinRedemptionQueueDigestConfig | None = None,
) -> MarketResearchCryptoStablecoinRedemptionQueueDigestReport:
    return build_market_research_crypto_stablecoin_redemption_queue_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_redemption_queue_digest_models_stress_gaps_and_confidence() -> None:
    report = _report(
        _snapshot(
            "condition_beta",
            "usdt_redemption_queue",
            stablecoin_symbol="USDT",
            observed_at=GENERATED_AT - timedelta(seconds=2_400),
            redemption_queue_usd=d("1200000000.000000"),
            previous_redemption_queue_usd=d("600000000.000000"),
            circulating_supply_usd=d("9000000000.000000"),
            reserve_coverage_ratio=d("0.960000"),
            estimated_wait_hours=d("36.000000"),
            source_count=d("1.000000"),
            confidence=d("0.520000"),
        ),
        _snapshot(
            "condition_alpha",
            "usdc_redemption_queue",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_stablecoin_redemption_queue_digest"
    )
    assert report.snapshot_count == d("2.000000")
    assert report.ready_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.queue_size_snapshot_count == d("1.000000")
    assert report.queue_ratio_snapshot_count == d("1.000000")
    assert report.queue_growth_snapshot_count == d("1.000000")
    assert report.wait_time_snapshot_count == d("1.000000")
    assert report.reserve_gap_snapshot_count == d("1.000000")
    assert report.source_diversity_gap_snapshot_count == d("1.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.confidence_gap_snapshot_count == d("1.000000")
    assert report.average_queue_ratio == d("0.070833")
    assert report.average_queue_growth_ratio == d("0.625000")
    assert report.average_estimated_wait_hours == d("22.000000")
    assert report.max_snapshot_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.redemption_queue_key) for row in report.rows) == (
        ("condition_beta", "usdt_redemption_queue"),
        ("condition_alpha", "usdc_redemption_queue"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.snapshot_age_seconds == d("2400.000000")
    assert beta.queue_ratio == d("0.133333")
    assert beta.queue_growth_ratio == d("1.000000")
    assert beta.reason_codes == (
        "market_research_crypto_stablecoin_redemption_queue_digest_queue_size",
        "market_research_crypto_stablecoin_redemption_queue_digest_queue_ratio",
        "market_research_crypto_stablecoin_redemption_queue_digest_queue_growth",
        "market_research_crypto_stablecoin_redemption_queue_digest_wait_time",
        "market_research_crypto_stablecoin_redemption_queue_digest_reserve_gap",
        "market_research_crypto_stablecoin_redemption_queue_digest_source_diversity_gap",
        "market_research_crypto_stablecoin_redemption_queue_digest_stale_snapshot",
        "market_research_crypto_stablecoin_redemption_queue_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_redemption_queue_digest_allows_growth_above_one() -> None:
    report = _report(
        _snapshot(
            "condition_growth",
            "usdc_redemption_queue_growth",
            redemption_queue_usd=d("300000000.000000"),
            previous_redemption_queue_usd=d("100000000.000000"),
            circulating_supply_usd=d("100000000000.000000"),
        ),
        config=_config(max_queue_growth_ratio=d("1.500000")),
    )

    assert report.digest_status == "blocked"
    assert report.queue_growth_snapshot_count == d("1.000000")
    assert report.average_queue_growth_ratio == d("2.000000")
    assert report.max_allowed_queue_growth_ratio == d("1.500000")
    assert report.rows[0].queue_growth_ratio == d("2.000000")
    assert report.rows[0].reason_codes == (
        "market_research_crypto_stablecoin_redemption_queue_digest_queue_growth",
    )


def test_redemption_queue_digest_normalizes_timezones_reason_counts_and_sources() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "condition_gamma",
            "dai_redemption_queue",
            stablecoin_symbol="DAI",
            observed_at=observed_at,
            source_count=d("2.000000"),
            redemption_queue_usd=d("150000000.000000"),
            previous_redemption_queue_usd=d("150000000.000000"),
            circulating_supply_usd=d("5000000000.000000"),
            reserve_coverage_ratio=d("1.010000"),
            estimated_wait_hours=d("6.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert report.max_snapshot_age_seconds == d("3600.000000")
    assert report.digest_status == "blocked"
    assert report.reason_code_counts == (
        MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_stablecoin_redemption_queue_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_stablecoin_redemption_queue_digest_stale_snapshot"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("dai_redemption_queue", "redemption-queue-source-v0"),
    )


def test_redemption_queue_digest_empty_input_is_watch_and_sorted_deterministically() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_stablecoin_redemption_queue_digest_no_inputs",
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
    assert tuple(row.redemption_queue_key for row in first.rows) == (
        "source_a",
        "source_b",
    )


def test_redemption_queue_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoStablecoinRedemptionQueueDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoStablecoinRedemptionQueueSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoStablecoinRedemptionQueueDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoStablecoinRedemptionQueueDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("redemption-queue-v0"))
    with pytest.raises(ValueError, match="max_queue_ratio"):
        _config(max_queue_ratio=_DecimalSubclass("0.120000"))
    with pytest.raises(ValueError, match="min_source_count"):
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
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]


def test_redemption_queue_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_snapshot())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if _is_public_numeric_field(field.name) or field.name == "confidence":
                assert type(value) is Decimal
    for field in fields(report):
        value = getattr(report, field.name)
        if _is_public_numeric_field(field.name):
            assert type(value) is Decimal
    for reason_count in report.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.snapshot_ratio) is Decimal

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoStablecoinRedemptionQueueDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_CRYPTO_STABLECOIN_REDEMPTION_QUEUE_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_crypto_stablecoin_redemption_queue_digest"
            ),
            snapshot_count=1,  # type: ignore[arg-type]
            ready_snapshot_count=d("1.000000"),
            watch_snapshot_count=d("0.000000"),
            blocked_snapshot_count=d("0.000000"),
            queue_size_snapshot_count=d("0.000000"),
            queue_ratio_snapshot_count=d("0.000000"),
            queue_growth_snapshot_count=d("0.000000"),
            wait_time_snapshot_count=d("0.000000"),
            reserve_gap_snapshot_count=d("0.000000"),
            source_diversity_gap_snapshot_count=d("0.000000"),
            stale_snapshot_count=d("0.000000"),
            confidence_gap_snapshot_count=d("0.000000"),
            average_queue_ratio=d("0.008333"),
            average_queue_growth_ratio=d("0.250000"),
            average_estimated_wait_hours=d("8.000000"),
            max_snapshot_age_seconds=d("0.000000"),
            max_allowed_snapshot_age_seconds=d("1800.000000"),
            max_allowed_redemption_queue_usd=d("750000000.000000"),
            max_allowed_queue_ratio=d("0.120000"),
            max_allowed_queue_growth_ratio=d("0.250000"),
            max_allowed_estimated_wait_hours=d("24.000000"),
            min_source_count=d("3.000000"),
            min_reserve_coverage_ratio=d("1.000000"),
            min_confidence=d("0.700000"),
            rows=report.rows,
            source_config_versions=(
                ("usdc_redemption_queue", "redemption-queue-source-v0"),
            ),
            reason_code_counts=report.reason_code_counts,
            reason_codes=(
                "market_research_crypto_stablecoin_redemption_queue_digest_ready",
            ),
        )


def test_redemption_queue_digest_payload_is_immutable_redacted_and_report_only() -> None:
    payload = market_research_crypto_stablecoin_redemption_queue_digest_payload(
        _report(
            _snapshot(
                "condition_redacted",
                "usdc_redemption_queue_redacted",
                stablecoin_symbol="USDC",
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
    assert payload["snapshot_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["rows"][0]["redemption_queue_usd"] == "250000000.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["redemption_queue_usd"] = "0.000000"  # type: ignore[index]


def test_redemption_queue_digest_rejects_duplicates_and_bad_report_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(
            _snapshot(redemption_queue_key="duplicate"),
            _snapshot(redemption_queue_key="duplicate"),
        )

    valid = _report(_snapshot())
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(MarketResearchCryptoStablecoinRedemptionQueueDigestReport)
    }
    assert (
        MarketResearchCryptoStablecoinRedemptionQueueDigestReport(**kwargs).digest_status
        == "ready"
    )

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoStablecoinRedemptionQueueDigestReport(
            **{**kwargs, "snapshot_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoStablecoinRedemptionQueueDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoStablecoinRedemptionQueueDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoStablecoinRedemptionQueueDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_stablecoin_redemption_queue_digest_ready"
                        ),
                        count=d("2.000000"),
                        snapshot_ratio=d("1.000000"),
                    ),
                ),
            },
        )


def test_redemption_queue_digest_module_scope_excludes_execution_io_network_and_persistence() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_stablecoin_redemption_queue_digest",
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
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {"open", "read", "write", "submit", "cancel"}
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
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_seconds")
        or field_name.endswith("_usd")
        or field_name.endswith("_hours")
    )
