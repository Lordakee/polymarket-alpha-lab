from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_crypto_l2_blob_fee_spike_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_L2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoL2BlobFeeSpikeDigestConfig,
    MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount,
    MarketResearchCryptoL2BlobFeeSpikeDigestReport,
    MarketResearchCryptoL2BlobFeeSpikeDigestRow,
    MarketResearchCryptoL2BlobFeeSpikeSample,
    build_market_research_crypto_l2_blob_fee_spike_digest,
    market_research_crypto_l2_blob_fee_spike_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchCryptoL2BlobFeeSpikeDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_L2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION
        ),
        "max_source_age_seconds": d("1800.000000"),
        "min_source_count": d("2.000000"),
        "max_blob_base_fee_gwei": d("45.000000"),
        "max_blob_fee_spike_ratio": d("3.000000"),
        "max_l2_priority_fee_gwei": d("0.300000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoL2BlobFeeSpikeDigestConfig(**values)


def sample(
    condition_id: str = "condition_alpha",
    sample_id: str = "base.alpha",
    *,
    rollup_name: str = "Base",
    observed_at: datetime = GENERATED_AT,
    source_count: Decimal = d("3.000000"),
    blob_base_fee_gwei: Decimal = d("20.000000"),
    blob_fee_spike_ratio: Decimal = d("1.200000"),
    l2_priority_fee_gwei: Decimal = d("0.100000"),
    batch_queue_depth: Decimal = d("6.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "crypto-l2-blob-fee-spike-source-v0",
) -> MarketResearchCryptoL2BlobFeeSpikeSample:
    return MarketResearchCryptoL2BlobFeeSpikeSample(
        condition_id=condition_id,
        sample_id=sample_id,
        rollup_name=rollup_name,
        observed_at=observed_at,
        source_count=source_count,
        blob_base_fee_gwei=blob_base_fee_gwei,
        blob_fee_spike_ratio=blob_fee_spike_ratio,
        l2_priority_fee_gwei=l2_priority_fee_gwei,
        batch_queue_depth=batch_queue_depth,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def report(
    *samples: MarketResearchCryptoL2BlobFeeSpikeSample,
    generated_at: datetime = GENERATED_AT,
    cfg: MarketResearchCryptoL2BlobFeeSpikeDigestConfig | None = None,
) -> MarketResearchCryptoL2BlobFeeSpikeDigestReport:
    return build_market_research_crypto_l2_blob_fee_spike_digest(
        samples,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_blob_fee_spike_digest_scores_fee_pressure_and_source_quality() -> None:
    summary = report(
        sample(
            "condition_beta",
            "optimism.beta",
            rollup_name="Optimism",
            observed_at=GENERATED_AT - timedelta(seconds=2000),
            source_count=d("1.000000"),
            blob_base_fee_gwei=d("65.000000"),
            blob_fee_spike_ratio=d("3.500000"),
            l2_priority_fee_gwei=d("0.450000"),
            batch_queue_depth=d("12.000000"),
            confidence=d("0.520000"),
        ),
        sample(
            "condition_alpha",
            "base.alpha",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_CRYPTO_L2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_crypto_l2_blob_fee_spike_digest"
    )
    assert summary.sample_count == d("2.000000")
    assert summary.ready_sample_count == d("1.000000")
    assert summary.watch_sample_count == d("0.000000")
    assert summary.blocked_sample_count == d("1.000000")
    assert summary.fee_spike_sample_count == d("1.000000")
    assert summary.high_blob_fee_sample_count == d("1.000000")
    assert summary.high_l2_fee_sample_count == d("1.000000")
    assert summary.source_gap_sample_count == d("1.000000")
    assert summary.stale_source_sample_count == d("1.000000")
    assert summary.confidence_gap_sample_count == d("1.000000")
    assert summary.average_blob_base_fee_gwei == d("42.500000")
    assert summary.average_blob_fee_spike_ratio == d("2.350000")
    assert summary.average_l2_priority_fee_gwei == d("0.275000")
    assert summary.max_source_age_seconds == d("2000.000000")
    assert summary.ready_sample_ratio == d("0.500000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.condition_id, row.sample_id) for row in summary.rows) == (
        ("condition_beta", "optimism.beta"),
        ("condition_alpha", "base.alpha"),
    )
    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.source_age_seconds == d("2000.000000")
    assert blocked.reason_codes == (
        "market_research_crypto_l2_blob_fee_spike_digest_fee_spike",
        "market_research_crypto_l2_blob_fee_spike_digest_high_blob_fee",
        "market_research_crypto_l2_blob_fee_spike_digest_high_l2_fee",
        "market_research_crypto_l2_blob_fee_spike_digest_source_gap",
        "market_research_crypto_l2_blob_fee_spike_digest_stale_source",
        "market_research_crypto_l2_blob_fee_spike_digest_confidence_gap",
    )
    assert summary.reason_codes == blocked.reason_codes
    assert summary.reason_code_counts[0] == (
        MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_l2_blob_fee_spike_digest_fee_spike"
            ),
            count=d("1.000000"),
            sample_ratio=d("0.500000"),
        )
    )


def test_blob_fee_spike_digest_empty_input_blocks_and_sorting_is_stable() -> None:
    empty = report()
    assert empty.digest_status == "blocked"
    assert empty.sample_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_l2_blob_fee_spike_digest_no_inputs",
    )
    assert empty.reason_code_counts == (
        MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount(
            reason_code="market_research_crypto_l2_blob_fee_spike_digest_no_inputs",
            count=d("1.000000"),
            sample_ratio=d("0.000000"),
        ),
    )

    first = report(
        sample("condition_b", "sample.b"),
        sample("condition_a", "sample.a"),
    )
    second = report(
        sample("condition_a", "sample.a"),
        sample("condition_b", "sample.b"),
    )

    assert first == second
    assert tuple(row.sample_id for row in first.rows) == ("sample.a", "sample.b")


def test_blob_fee_spike_digest_accepts_utc_times_and_watch_sources() -> None:
    generated_at = GENERATED_AT
    observed_at = GENERATED_AT - timedelta(hours=1)

    summary = report(
        sample(
            "condition_gamma",
            "arbitrum.gamma",
            rollup_name="Arbitrum",
            observed_at=observed_at,
            source_count=d("1.000000"),
            blob_base_fee_gwei=d("30.000000"),
            blob_fee_spike_ratio=d("1.500000"),
            l2_priority_fee_gwei=d("0.120000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
        cfg=config(max_source_age_seconds=d("3600.000000")),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.rows[0].observed_at == observed_at
    assert summary.max_source_age_seconds == d("3600.000000")
    assert summary.digest_status == "watch"
    assert summary.reason_code_counts == (
        MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount(
            reason_code="market_research_crypto_l2_blob_fee_spike_digest_source_gap",
            count=d("1.000000"),
            sample_ratio=d("1.000000"),
        ),
    )
    assert summary.source_config_versions == (
        ("arbitrum.gamma", "crypto-l2-blob-fee-spike-source-v0"),
    )


def test_blob_fee_spike_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoL2BlobFeeSpikeDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoL2BlobFeeSpikeSample.__dataclass_params__.frozen
    assert MarketResearchCryptoL2BlobFeeSpikeDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoL2BlobFeeSpikeDigestReport.__dataclass_params__.frozen

    with pytest.raises(TypeError):
        class BadSample(MarketResearchCryptoL2BlobFeeSpikeSample):
            pass

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("blob-fee-v0"))
    with pytest.raises(ValueError, match="max_blob_base_fee_gwei"):
        config(max_blob_base_fee_gwei=_DecimalSubclass("45.000000"))
    with pytest.raises(ValueError, match="max_blob_base_fee_gwei"):
        config(max_blob_base_fee_gwei=d("45"))
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=2)
    with pytest.raises(ValueError, match="confidence"):
        sample(confidence=0.8)
    with pytest.raises(ValueError, match="blob_base_fee_gwei"):
        sample(blob_base_fee_gwei=d("20"))
    with pytest.raises(ValueError, match="confidence"):
        sample(confidence=d("0.82"))
    with pytest.raises(ValueError, match="condition_id"):
        sample(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            sample(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report(sample(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(sample(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(sample(), readonly=False)
    summary = report(sample())
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(FrozenInstanceError):
        sample().paper_only = False  # type: ignore[misc]


def test_blob_fee_spike_digest_rejects_naive_and_unknown_offset_times() -> None:
    unknown_offset = datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTimezone())
    non_utc = datetime(2026, 7, 3, 8, 0, tzinfo=timezone(timedelta(hours=-4)))

    with pytest.raises(ValueError, match="timezone-aware"):
        sample(observed_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        sample(observed_at=unknown_offset)
    with pytest.raises(ValueError, match="UTC-aware"):
        sample(observed_at=non_utc)
    with pytest.raises(ValueError, match="timezone-aware"):
        report(sample(), generated_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(sample(), generated_at=unknown_offset)
    with pytest.raises(ValueError, match="UTC-aware"):
        report(sample(), generated_at=non_utc)


def test_blob_fee_spike_digest_rejects_reason_count_and_sequence_tampering() -> None:
    with pytest.raises(ValueError, match="count"):
        MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount(
            reason_code="market_research_crypto_l2_blob_fee_spike_digest_ready",
            count=d("0.000000"),
            sample_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="whole"):
        MarketResearchCryptoL2BlobFeeSpikeDigestReasonCodeCount(
            reason_code="market_research_crypto_l2_blob_fee_spike_digest_ready",
            count=d("1.500000"),
            sample_ratio=d("0.500000"),
        )

    summary = report(
        sample("condition_b", "sample.b"),
        sample("condition_a", "sample.a"),
    )
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=list(summary.rows))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_config_versions"):
        replace(
            summary,
            source_config_versions=tuple(reversed(summary.source_config_versions)),
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        replace(
            summary,
            source_config_versions=list(summary.source_config_versions),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            summary.rows[0],
            reason_codes=list(summary.rows[0].reason_codes),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=list(summary.reason_codes))  # type: ignore[arg-type]

    blocked = report(
        sample(
            "condition_c",
            "sample.c",
            blob_base_fee_gwei=d("70.000000"),
            blob_fee_spike_ratio=d("3.700000"),
        ),
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(blocked, reason_code_counts=tuple(reversed(blocked.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(blocked, reason_code_counts=list(blocked.reason_code_counts))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(blocked, reason_code_counts=blocked.reason_code_counts[1:])


def test_blob_fee_spike_digest_public_numerics_are_decimal_six_place_values() -> None:
    summary = report(sample())

    for value in (
        config().max_source_age_seconds,
        config().min_source_count,
        config().max_blob_base_fee_gwei,
        config().max_blob_fee_spike_ratio,
        config().max_l2_priority_fee_gwei,
        config().min_confidence,
    ):
        assert type(value) is Decimal
        assert value.as_tuple().exponent == -6

    for row in summary.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_gwei")
                or field.name.endswith("_depth")
                or field.name == "confidence"
            ):
                assert type(value) is Decimal
                assert value.as_tuple().exponent == -6
    for field in fields(summary):
        value = getattr(summary, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
            or field.name.endswith("_gwei")
        ):
            assert type(value) is Decimal
            assert value.as_tuple().exponent == -6
    for reason_count in summary.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.sample_ratio) is Decimal
        assert reason_count.count.as_tuple().exponent == -6
        assert reason_count.sample_ratio.as_tuple().exponent == -6


def test_blob_fee_spike_digest_payload_is_redacted_and_deeply_frozen() -> None:
    payload = market_research_crypto_l2_blob_fee_spike_digest_payload(
        report(sample("condition_redacted", "base.redacted")),
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
    assert payload["sample_count"] == "1.000000"
    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["sample_id"] == "base.redacted"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["rows"][0]["blob_base_fee_gwei"] == "20.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["sample_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["blob_base_fee_gwei"] = "0.000000"  # type: ignore[index]


def test_blob_fee_spike_digest_payload_revalidates_tampered_public_graph() -> None:
    tampered_report = report(sample())
    object.__setattr__(tampered_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_crypto_l2_blob_fee_spike_digest_payload(tampered_report)

    tampered_row = report(sample())
    object.__setattr__(tampered_row.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_crypto_l2_blob_fee_spike_digest_payload(tampered_row)

    tampered_report_only = report(sample())
    object.__setattr__(tampered_report_only, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        market_research_crypto_l2_blob_fee_spike_digest_payload(tampered_report_only)

    tampered_rows = report(sample())
    object.__setattr__(tampered_rows, "rows", ("not-a-row",))
    with pytest.raises(ValueError, match="rows"):
        market_research_crypto_l2_blob_fee_spike_digest_payload(tampered_rows)

    tampered_decimal = report(sample())
    object.__setattr__(tampered_decimal.rows[0], "blob_base_fee_gwei", Decimal("20.0"))
    with pytest.raises(ValueError, match="six decimal"):
        market_research_crypto_l2_blob_fee_spike_digest_payload(tampered_decimal)

    tampered_time = report(sample())
    object.__setattr__(
        tampered_time.rows[0],
        "observed_at",
        datetime(2026, 7, 3, 13, 0, tzinfo=timezone(timedelta(hours=1))),
    )
    with pytest.raises(ValueError, match="UTC-aware"):
        market_research_crypto_l2_blob_fee_spike_digest_payload(tampered_time)


def test_module_scope_has_no_live_or_mutating_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_crypto_l2_blob_fee_spike_digest.py",
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
        "subprocess",
        "network",
        "open(",
        "asdict",
        "market_slug",
        "question",
        "payload_json",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
