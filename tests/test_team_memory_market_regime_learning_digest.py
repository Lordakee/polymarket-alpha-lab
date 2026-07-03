from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_memory_market_regime_learning_digest import (
    DEFAULT_TEAM_MEMORY_MARKET_REGIME_LEARNING_DIGEST_CONFIG_VERSION,
    TeamMemoryMarketRegimeLearningDigestConfig,
    TeamMemoryMarketRegimeLearningDigestReasonCodeCount,
    TeamMemoryMarketRegimeLearningDigestReport,
    TeamMemoryMarketRegimeLearningDigestSource,
    TeamMemoryMarketRegimeLearningDigestSourceStatus,
    build_team_memory_market_regime_learning_digest_report,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def test_report_reduces_sources_with_deterministic_sorting_redaction_and_flags() -> None:
    report = build_team_memory_market_regime_learning_digest_report(
        [
            TeamMemoryMarketRegimeLearningDigestSource(
                team_id="macro_rates",
                market_slug="fed-rate-decision",
                regime_label="range_bound",
                learning_signal="thin_depth",
                observation_count=Decimal("3"),
                confidence_ratio=Decimal("0.40"),
                surprise_ratio=Decimal("0.70"),
                reference="https://example.com/report?token=secret#frag",
                observed_at=GENERATED_AT - timedelta(minutes=10),
            ),
            TeamMemoryMarketRegimeLearningDigestSource(
                team_id="crypto_btc",
                market_slug="bitcoin-price-above-100k",
                regime_label="trend_up",
                learning_signal="stable_spread",
                observation_count=Decimal("5"),
                confidence_ratio=Decimal("0.80"),
                surprise_ratio=Decimal("0.10"),
                reference="BTC desk note private_key=abc123 wallet=0xabc",
                observed_at=GENERATED_AT - timedelta(minutes=20),
            ),
        ],
        config=TeamMemoryMarketRegimeLearningDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_TEAM_MEMORY_MARKET_REGIME_LEARNING_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "watch"
    assert report.recommended_next_step == "review_market_regime_learning_digest"
    assert report.source_count == Decimal("2")
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.blocked_count == Decimal("0")
    assert report.average_confidence_ratio == Decimal("0.60")
    assert report.average_surprise_ratio == Decimal("0.40")
    assert report.reason_codes == (
        "team_memory_market_regime_learning_digest_watch_learning_signals_present",
    )
    assert report.reason_code_counts == (
        TeamMemoryMarketRegimeLearningDigestReasonCodeCount(
            reason_code=(
                "team_memory_market_regime_learning_digest_watch_learning_signals_present"
            ),
            count=Decimal("1"),
        ),
    )
    assert tuple(row.team_id for row in report.source_statuses) == (
        "crypto_btc",
        "macro_rates",
    )
    assert tuple(row.market_slug for row in report.source_statuses) == (
        "bitcoin-price-above-100k",
        "fed-rate-decision",
    )
    assert report.source_statuses[0].source_status == "pass"
    assert report.source_statuses[1].source_status == "watch"
    assert report.source_statuses[0].redacted_reference == (
        "BTC desk note [redacted]=abc123 [redacted]=0xabc"
    )
    assert report.source_statuses[1].redacted_reference == (
        "https://example.com/report?[redacted]#frag"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_blocked_sources_take_precedence_and_empty_sources_are_blocked() -> None:
    blocked_report = build_team_memory_market_regime_learning_digest_report(
        (
            TeamMemoryMarketRegimeLearningDigestSource(
                team_id="politics",
                market_slug="election-outcome",
                regime_label="headline_shock",
                learning_signal="contradictory_signal",
                observation_count=Decimal("1"),
                confidence_ratio=Decimal("0.30"),
                surprise_ratio=Decimal("0.90"),
                reference="local memo",
                observed_at=GENERATED_AT,
            ),
        ),
        config=TeamMemoryMarketRegimeLearningDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert blocked_report.digest_status == "blocked"
    assert blocked_report.recommended_next_step == "block_market_regime_learning_use"
    assert blocked_report.reason_codes == (
        "team_memory_market_regime_learning_digest_blocked_learning_signals_present",
    )

    empty_report = build_team_memory_market_regime_learning_digest_report(
        (),
        config=TeamMemoryMarketRegimeLearningDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert empty_report.digest_status == "blocked"
    assert empty_report.recommended_next_step == "block_market_regime_learning_use"
    assert empty_report.reason_codes == (
        "team_memory_market_regime_learning_digest_empty_sources",
    )
    assert empty_report.source_count == Decimal("0")
    assert empty_report.average_confidence_ratio is None
    assert empty_report.average_surprise_ratio is None


def test_public_dataclasses_are_frozen_and_public_numeric_fields_are_decimals() -> None:
    config = TeamMemoryMarketRegimeLearningDigestConfig()
    source = TeamMemoryMarketRegimeLearningDigestSource(
        team_id="crypto_btc",
        market_slug="bitcoin-price-above-100k",
        regime_label="trend_up",
        learning_signal="stable_spread",
        observation_count=Decimal("5"),
        confidence_ratio=Decimal("0.80"),
        surprise_ratio=Decimal("0.10"),
        reference="local memo",
        observed_at=GENERATED_AT,
    )
    report = build_team_memory_market_regime_learning_digest_report(
        (source,),
        config=config,
        generated_at=GENERATED_AT,
    )

    public_dataclasses = (
        TeamMemoryMarketRegimeLearningDigestConfig,
        TeamMemoryMarketRegimeLearningDigestSource,
        TeamMemoryMarketRegimeLearningDigestSourceStatus,
        TeamMemoryMarketRegimeLearningDigestReasonCodeCount,
        TeamMemoryMarketRegimeLearningDigestReport,
    )
    for cls in public_dataclasses:
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        source.team_id = "macro_rates"  # type: ignore[misc]

    numeric_field_names = {
        "observation_count",
        "confidence_ratio",
        "surprise_ratio",
        "source_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "count",
        "average_confidence_ratio",
        "average_surprise_ratio",
    }
    for item in (source, report, report.source_statuses[0], report.reason_code_counts[0]):
        for field in fields(item):
            if field.name in numeric_field_names:
                value = getattr(item, field.name)
                if value is not None:
                    assert type(value) is Decimal


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_public_dataclasses_reject_truthy_non_true_hard_flags(flag_name: str) -> None:
    config = TeamMemoryMarketRegimeLearningDigestConfig()
    source = TeamMemoryMarketRegimeLearningDigestSource(
        team_id="crypto_btc",
        market_slug="bitcoin-price-above-100k",
        regime_label="trend_up",
        learning_signal="stable_spread",
        observation_count=Decimal("5"),
        confidence_ratio=Decimal("0.80"),
        surprise_ratio=Decimal("0.10"),
        reference="local memo",
        observed_at=GENERATED_AT,
    )
    report = build_team_memory_market_regime_learning_digest_report(
        (source,),
        config=config,
        generated_at=GENERATED_AT,
    )
    values = (
        config,
        source,
        report.source_statuses[0],
        report.reason_code_counts[0],
        report,
    )

    for value in values:
        with pytest.raises(ValueError, match=flag_name):
            replace(value, **{flag_name: 1})


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("observation_count", 5),
        ("observation_count", 5.0),
        ("confidence_ratio", Decimal("NaN")),
        ("confidence_ratio", Decimal("Infinity")),
        ("surprise_ratio", 0.1),
        ("surprise_ratio", Decimal("-0.1")),
        ("surprise_ratio", Decimal("1.1")),
    ],
)
def test_source_rejects_non_decimal_float_and_non_finite_public_numbers(
    field_name: str,
    value: object,
) -> None:
    kwargs = {
        "team_id": "crypto_btc",
        "market_slug": "bitcoin-price-above-100k",
        "regime_label": "trend_up",
        "learning_signal": "stable_spread",
        "observation_count": Decimal("5"),
        "confidence_ratio": Decimal("0.80"),
        "surprise_ratio": Decimal("0.10"),
        "reference": "local memo",
        "observed_at": GENERATED_AT,
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError):
        TeamMemoryMarketRegimeLearningDigestSource(**kwargs)


def test_datetimes_must_be_utc_aware_and_hard_flags_are_required() -> None:
    with pytest.raises(ValueError):
        TeamMemoryMarketRegimeLearningDigestSource(
            team_id="crypto_btc",
            market_slug="bitcoin-price-above-100k",
            regime_label="trend_up",
            learning_signal="stable_spread",
            observation_count=Decimal("5"),
            confidence_ratio=Decimal("0.80"),
            surprise_ratio=Decimal("0.10"),
            reference="local memo",
            observed_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError):
        TeamMemoryMarketRegimeLearningDigestConfig(paper_only=False)

    with pytest.raises(ValueError):
        TeamMemoryMarketRegimeLearningDigestReasonCodeCount(
            reason_code=(
                "team_memory_market_regime_learning_digest_passed"
            ),
            count=Decimal("1.0"),
            readonly=False,
        )


def test_report_constructor_validates_consistency_and_sorted_rows() -> None:
    status = TeamMemoryMarketRegimeLearningDigestSourceStatus(
        team_id="macro_rates",
        market_slug="fed-rate-decision",
        regime_label="range_bound",
        learning_signal="thin_depth",
        observation_count=Decimal("3"),
        confidence_ratio=Decimal("0.40"),
        surprise_ratio=Decimal("0.70"),
        redacted_reference="local memo",
        observed_at=GENERATED_AT,
        source_status="watch",
        reason_codes=(
            "team_memory_market_regime_learning_digest_watch_learning_signal",
        ),
    )

    with pytest.raises(ValueError):
        TeamMemoryMarketRegimeLearningDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_TEAM_MEMORY_MARKET_REGIME_LEARNING_DIGEST_CONFIG_VERSION
            ),
            digest_status="watch",
            recommended_next_step="review_market_regime_learning_digest",
            source_count=Decimal("2"),
            pass_count=Decimal("0"),
            watch_count=Decimal("1"),
            blocked_count=Decimal("0"),
            average_confidence_ratio=Decimal("0.40"),
            average_surprise_ratio=Decimal("0.70"),
            source_statuses=(status,),
            reason_code_counts=(
                TeamMemoryMarketRegimeLearningDigestReasonCodeCount(
                    reason_code=(
                        "team_memory_market_regime_learning_digest_"
                        "watch_learning_signals_present"
                    ),
                    count=Decimal("1"),
                ),
            ),
            reason_codes=(
                "team_memory_market_regime_learning_digest_"
                "watch_learning_signals_present",
            ),
        )
