from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_liquidation_cluster_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CLUSTER_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoLiquidationClusterDigestConfig,
    MarketResearchCryptoLiquidationClusterDigestReasonCodeCount,
    MarketResearchCryptoLiquidationClusterDigestReport,
    MarketResearchCryptoLiquidationClusterDigestRow,
    MarketResearchCryptoLiquidationClusterSnapshot,
    build_market_research_crypto_liquidation_cluster_digest,
    market_research_crypto_liquidation_cluster_digest_payload,
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
) -> MarketResearchCryptoLiquidationClusterDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CLUSTER_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("900.000000"),
        "max_long_liquidation_ratio": d("0.650000"),
        "max_short_liquidation_ratio": d("0.650000"),
        "max_notional_change_ratio": d("0.750000"),
        "min_liquidation_notional_usd": d("10000000.000000"),
        "min_venue_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoLiquidationClusterDigestConfig(**values)


def _snapshot(
    condition_id: str = "condition_alpha",
    cluster_key: str = "btc_liquidation_cluster",
    *,
    asset_symbol: str = "BTC",
    observed_at: datetime = GENERATED_AT,
    long_liquidation_usd: Decimal = d("6000000.000000"),
    short_liquidation_usd: Decimal = d("5000000.000000"),
    previous_total_liquidation_usd: Decimal = d("9000000.000000"),
    venue_source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "liquidation-cluster-source-v0",
) -> MarketResearchCryptoLiquidationClusterSnapshot:
    return MarketResearchCryptoLiquidationClusterSnapshot(
        condition_id=condition_id,
        cluster_key=cluster_key,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        long_liquidation_usd=long_liquidation_usd,
        short_liquidation_usd=short_liquidation_usd,
        previous_total_liquidation_usd=previous_total_liquidation_usd,
        venue_source_count=venue_source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoLiquidationClusterSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoLiquidationClusterDigestConfig | None = None,
) -> MarketResearchCryptoLiquidationClusterDigestReport:
    return build_market_research_crypto_liquidation_cluster_digest(
        snapshots,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_liquidation_cluster_digest_models_cluster_pressure_gaps_and_confidence() -> None:
    report = _report(
        _snapshot(
            "condition_beta",
            "eth_liquidation_cluster",
            asset_symbol="ETH",
            observed_at=GENERATED_AT - timedelta(seconds=1_200),
            long_liquidation_usd=d("26000000.000000"),
            short_liquidation_usd=d("4000000.000000"),
            previous_total_liquidation_usd=d("12000000.000000"),
            venue_source_count=d("1.000000"),
            confidence=d("0.520000"),
        ),
        _snapshot(
            "condition_alpha",
            "btc_liquidation_cluster",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_liquidation_cluster_digest"
    )
    assert report.snapshot_count == d("2.000000")
    assert report.ready_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.long_cluster_snapshot_count == d("1.000000")
    assert report.short_cluster_snapshot_count == d("0.000000")
    assert report.notional_surge_snapshot_count == d("1.000000")
    assert report.source_diversity_gap_snapshot_count == d("1.000000")
    assert report.notional_gap_snapshot_count == d("0.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.confidence_gap_snapshot_count == d("1.000000")
    assert report.average_total_liquidation_usd == d("20500000.000000")
    assert report.average_dominant_liquidation_ratio == d("0.706061")
    assert report.average_notional_change_ratio == d("0.861111")
    assert report.max_snapshot_age_seconds == d("1200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.cluster_key) for row in report.rows) == (
        ("condition_beta", "eth_liquidation_cluster"),
        ("condition_alpha", "btc_liquidation_cluster"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.snapshot_age_seconds == d("1200.000000")
    assert beta.total_liquidation_usd == d("30000000.000000")
    assert beta.dominant_liquidation_ratio == d("0.866667")
    assert beta.notional_change_ratio == d("1.500000")
    assert beta.reason_codes == (
        "market_research_crypto_liquidation_cluster_digest_long_cluster",
        "market_research_crypto_liquidation_cluster_digest_notional_surge",
        "market_research_crypto_liquidation_cluster_digest_source_diversity_gap",
        "market_research_crypto_liquidation_cluster_digest_stale_snapshot",
        "market_research_crypto_liquidation_cluster_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_liquidation_cluster_digest_normalizes_timezones_and_reason_counts() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "condition_gamma",
            "sol_liquidation_cluster",
            asset_symbol="SOL",
            observed_at=observed_at,
            long_liquidation_usd=d("2000000.000000"),
            short_liquidation_usd=d("8000000.000000"),
            previous_total_liquidation_usd=d("10000000.000000"),
            venue_source_count=d("2.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert report.max_snapshot_age_seconds == d("3600.000000")
    assert report.digest_status == "blocked"
    assert report.reason_code_counts == (
        MarketResearchCryptoLiquidationClusterDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_liquidation_cluster_digest_short_cluster"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        MarketResearchCryptoLiquidationClusterDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_liquidation_cluster_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        MarketResearchCryptoLiquidationClusterDigestReasonCodeCount(
            reason_code="market_research_crypto_liquidation_cluster_digest_stale_snapshot",
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_liquidation_cluster", "liquidation-cluster-source-v0"),
    )


def test_liquidation_cluster_digest_empty_input_is_watch_and_sorted_deterministically() -> None:
    empty = _report()
    assert empty.digest_status == "blocked"
    assert empty.snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_liquidation_cluster_digest_no_inputs",
    )
    assert empty.reason_code_counts == (
        MarketResearchCryptoLiquidationClusterDigestReasonCodeCount(
            reason_code="market_research_crypto_liquidation_cluster_digest_no_inputs",
            count=d("1.000000"),
            snapshot_ratio=d("0.000000"),
        ),
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
    assert tuple(row.cluster_key for row in first.rows) == ("source_a", "source_b")


def test_liquidation_cluster_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoLiquidationClusterDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoLiquidationClusterSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoLiquidationClusterDigestRow.__dataclass_params__.frozen
    reason_count_cls = MarketResearchCryptoLiquidationClusterDigestReasonCodeCount
    assert reason_count_cls.__dataclass_params__.frozen
    assert MarketResearchCryptoLiquidationClusterDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("liquidation-cluster-v0"))
    with pytest.raises(ValueError, match="max_long_liquidation_ratio"):
        _config(max_long_liquidation_ratio=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="min_venue_source_count"):
        _config(min_venue_source_count=3)
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
    with pytest.raises(ValueError, match="config"):
        build_market_research_crypto_liquidation_cluster_digest(
            (),
            config=False,  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
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


def test_liquidation_cluster_digest_rejects_all_false_report_only_flags() -> None:
    report = _report(_snapshot())
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    cases = (
        ("config paper_only", "paper_only", lambda: _config(paper_only=False)),
        ("config report_only", "report_only", lambda: _config(report_only=False)),
        ("config readonly", "readonly", lambda: _config(readonly=False)),
        ("snapshot paper_only", "paper_only", lambda: replace(_snapshot(), paper_only=False)),
        (
            "snapshot report_only",
            "report_only",
            lambda: replace(_snapshot(), report_only=False),
        ),
        ("snapshot readonly", "readonly", lambda: replace(_snapshot(), readonly=False)),
        ("row paper_only", "paper_only", lambda: replace(row, paper_only=False)),
        ("row report_only", "report_only", lambda: replace(row, report_only=False)),
        ("row readonly", "readonly", lambda: replace(row, readonly=False)),
        (
            "reason count paper_only",
            "paper_only",
            lambda: replace(reason_count, paper_only=False),
        ),
        (
            "reason count report_only",
            "report_only",
            lambda: replace(reason_count, report_only=False),
        ),
        (
            "reason count readonly",
            "readonly",
            lambda: replace(reason_count, readonly=False),
        ),
        ("report paper_only", "paper_only", lambda: replace(report, paper_only=False)),
        ("report report_only", "report_only", lambda: replace(report, report_only=False)),
        ("report readonly", "readonly", lambda: replace(report, readonly=False)),
    )

    for _label, flag, build_invalid in cases:
        with pytest.raises(ValueError, match=flag):
            build_invalid()


def test_liquidation_cluster_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_snapshot())

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
        assert type(reason_count.snapshot_ratio) is Decimal
        assert reason_count.paper_only is True
        assert reason_count.report_only is True
        assert reason_count.readonly is True

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoLiquidationClusterDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_CRYPTO_LIQUIDATION_CLUSTER_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_crypto_liquidation_cluster_digest"
            ),
            snapshot_count=1,  # type: ignore[arg-type]
            ready_snapshot_count=d("1.000000"),
            watch_snapshot_count=d("0.000000"),
            blocked_snapshot_count=d("0.000000"),
            long_cluster_snapshot_count=d("0.000000"),
            short_cluster_snapshot_count=d("0.000000"),
            notional_surge_snapshot_count=d("0.000000"),
            source_diversity_gap_snapshot_count=d("0.000000"),
            notional_gap_snapshot_count=d("0.000000"),
            stale_snapshot_count=d("0.000000"),
            confidence_gap_snapshot_count=d("0.000000"),
            average_total_liquidation_usd=d("11000000.000000"),
            average_dominant_liquidation_ratio=d("0.545455"),
            average_notional_change_ratio=d("0.222222"),
            max_snapshot_age_seconds=d("0.000000"),
            max_allowed_snapshot_age_seconds=d("900.000000"),
            max_allowed_long_liquidation_ratio=d("0.650000"),
            max_allowed_short_liquidation_ratio=d("0.650000"),
            max_allowed_notional_change_ratio=d("0.750000"),
            min_liquidation_notional_usd=d("10000000.000000"),
            min_venue_source_count=d("3.000000"),
            min_confidence=d("0.700000"),
            rows=report.rows,
            source_config_versions=(
                ("btc_liquidation_cluster", "liquidation-cluster-source-v0"),
            ),
            reason_code_counts=report.reason_code_counts,
            reason_codes=(
                "market_research_crypto_liquidation_cluster_digest_ready",
            ),
        )
    with pytest.raises(ValueError, match="count"):
        MarketResearchCryptoLiquidationClusterDigestReasonCodeCount(
            reason_code="market_research_crypto_liquidation_cluster_digest_ready",
            count=d("0.000000"),
            snapshot_ratio=d("0.000000"),
        )


def test_liquidation_cluster_digest_payload_is_immutable_redacted_and_report_only() -> None:
    payload = market_research_crypto_liquidation_cluster_digest_payload(
        _report(
            _snapshot(
                "condition_redacted",
                "btc_liquidation_cluster_redacted",
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
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["rows"][0]["total_liquidation_usd"] == "11000000.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["total_liquidation_usd"] = "0.000000"  # type: ignore[index]


def test_liquidation_cluster_digest_payload_rejects_tampered_nested_public_values() -> None:
    report = _report(_snapshot())

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_crypto_liquidation_cluster_digest_payload(report)
    object.__setattr__(report.rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        market_research_crypto_liquidation_cluster_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "report_only", True)

    object.__setattr__(report.rows[0], "total_liquidation_usd", d("11000000.0000001"))
    with pytest.raises(ValueError, match="six decimals"):
        market_research_crypto_liquidation_cluster_digest_payload(report)


def test_liquidation_cluster_digest_rejects_duplicates_and_bad_report_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(
            _snapshot(cluster_key="duplicate"),
            _snapshot(cluster_key="duplicate"),
        )

    valid = _report(_snapshot())
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(MarketResearchCryptoLiquidationClusterDigestReport)
    }
    assert MarketResearchCryptoLiquidationClusterDigestReport(**kwargs).digest_status == (
        "ready"
    )

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoLiquidationClusterDigestReport(
            **{**kwargs, "snapshot_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoLiquidationClusterDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoLiquidationClusterDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoLiquidationClusterDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_liquidation_cluster_digest_ready"
                        ),
                        count=d("2.000000"),
                        snapshot_ratio=d("1.000000"),
                    ),
                ),
            },
        )

    two_row_report = _report(
        _snapshot("condition_b", "source_b"),
        _snapshot("condition_a", "source_a"),
    )
    two_row_kwargs = {
        field.name: getattr(two_row_report, field.name)
        for field in fields(MarketResearchCryptoLiquidationClusterDigestReport)
    }
    with pytest.raises(ValueError, match="rows"):
        MarketResearchCryptoLiquidationClusterDigestReport(
            **{
                **two_row_kwargs,
                "rows": tuple(reversed(two_row_report.rows)),
            },
        )


def test_liquidation_cluster_digest_module_scope_excludes_execution_io_network_and_persistence() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_liquidation_cluster_digest",
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
        "secret",
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
