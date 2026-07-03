from __future__ import annotations

import dataclasses
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.team_memory_source_reliability_scorecard_digest import (
    DEFAULT_TEAM_MEMORY_SOURCE_RELIABILITY_SCORECARD_DIGEST_CONFIG_VERSION,
    TeamMemorySourceReliabilityScorecardDigestConfig,
    TeamMemorySourceReliabilityScorecardObservation,
    TeamMemorySourceReliabilityScorecardReasonCodeCount,
    TeamMemorySourceReliabilityScorecardRow,
    build_team_memory_source_reliability_scorecard_digest,
    team_memory_source_reliability_scorecard_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


def test_scores_reliability_by_team_category_with_decimal_metrics_and_redacted_payload() -> None:
    report = build_team_memory_source_reliability_scorecard_digest(
        (
            _observation(
                team_id="team-beta",
                category="macro",
                source_ref="macro-calendar",
                source_family="calendar",
                observed_at=GENERATED_AT - timedelta(seconds=300),
                resolved_at=GENERATED_AT - timedelta(seconds=200),
                acknowledged_at=GENERATED_AT - timedelta(seconds=100),
            ),
            _observation(
                team_id="team-alpha",
                category="politics",
                source_ref="state-results",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=1_800),
                resolved_at=GENERATED_AT - timedelta(seconds=1_000),
                acknowledged_at=GENERATED_AT - timedelta(seconds=400),
            ),
            _observation(
                team_id="team-alpha",
                category="politics",
                source_ref="county-results",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=3_600),
                resolved_at=GENERATED_AT - timedelta(seconds=2_000),
                acknowledged_at=GENERATED_AT - timedelta(seconds=1_000),
            ),
            _observation(
                team_id="team-alpha",
                category="politics",
                source_ref="polling-archive",
                source_family="market",
                observed_at=GENERATED_AT - timedelta(seconds=7_200),
                resolved_at=GENERATED_AT - timedelta(seconds=1_800),
                acknowledged_at=GENERATED_AT - timedelta(seconds=1_000),
                was_hit=False,
                contradiction_count=Decimal("1"),
            ),
        ),
        config=TeamMemorySourceReliabilityScorecardDigestConfig(
            min_hit_rate=Decimal("0.700000"),
            max_source_age_seconds=Decimal("86400.000000"),
            max_contradiction_rate=Decimal("0.500000"),
            max_acknowledgement_lag_seconds=Decimal("3600.000000"),
            min_source_family_diversity_ratio=Decimal("0.500000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_TEAM_MEMORY_SOURCE_RELIABILITY_SCORECARD_DIGEST_CONFIG_VERSION
    )
    assert report.reliability_status == "watch"
    assert report.team_category_count == Decimal("2")
    assert report.event_count == Decimal("4")
    assert report.source_count == Decimal("4")
    assert report.hit_rate == Decimal("0.750000")
    assert report.freshness_age_seconds == Decimal("7200.000000")
    assert report.contradiction_rate == Decimal("0.250000")
    assert report.acknowledgement_lag_seconds == Decimal("1000.000000")
    assert report.source_family_diversity_ratio == Decimal("0.666667")
    assert report.reason_codes == (
        "team_memory_source_reliability_scorecard_digest_low_hit_rate",
    )
    assert report.reason_code_counts == (
        TeamMemorySourceReliabilityScorecardReasonCodeCount(
            reason_code="team_memory_source_reliability_scorecard_digest_low_hit_rate",
            count=Decimal("1"),
        ),
    )
    assert report.rows == (
        TeamMemorySourceReliabilityScorecardRow(
            row_key="team-alpha|politics",
            team_id="team-alpha",
            category="politics",
            event_count=Decimal("3"),
            source_count=Decimal("3"),
            source_family_count=Decimal("2"),
            hit_count=Decimal("2"),
            miss_count=Decimal("1"),
            hit_rate=Decimal("0.666667"),
            freshness_age_seconds=Decimal("7200.000000"),
            contradiction_count=Decimal("1"),
            contradiction_rate=Decimal("0.333333"),
            acknowledgement_lag_seconds=Decimal("1000.000000"),
            source_family_diversity_ratio=Decimal("0.666667"),
            reliability_status="watch",
            reason_codes=(
                "team_memory_source_reliability_scorecard_digest_row_low_hit_rate",
            ),
        ),
        TeamMemorySourceReliabilityScorecardRow(
            row_key="team-beta|macro",
            team_id="team-beta",
            category="macro",
            event_count=Decimal("1"),
            source_count=Decimal("1"),
            source_family_count=Decimal("1"),
            hit_count=Decimal("1"),
            miss_count=Decimal("0"),
            hit_rate=Decimal("1.000000"),
            freshness_age_seconds=Decimal("300.000000"),
            contradiction_count=Decimal("0"),
            contradiction_rate=Decimal("0.000000"),
            acknowledgement_lag_seconds=Decimal("100.000000"),
            source_family_diversity_ratio=Decimal("1.000000"),
            reliability_status="pass",
            reason_codes=(
                "team_memory_source_reliability_scorecard_digest_row_passed",
            ),
        ),
    )

    payload = team_memory_source_reliability_scorecard_digest_payload(report)
    payload_text = repr(payload)
    assert "team-alpha" not in payload_text
    assert "politics" not in payload_text
    assert "state-results" not in payload_text
    assert payload["rows"][0]["redacted_team_ref"] == "<redacted-team-001>"
    assert payload["rows"][0]["redacted_category_ref"] == "<redacted-category-001>"
    assert payload["rows"][0]["hit_rate"] == "0.666667"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_floats(payload)
    _assert_public_numeric_fields_are_decimals(report)
    _assert_public_numeric_fields_are_decimals(report.rows[0])


def test_scorecard_digest_computes_age_and_ack_lag_from_decimal_microseconds() -> None:
    report = build_team_memory_source_reliability_scorecard_digest(
        (
            _observation(
                team_id="team-alpha",
                category="politics",
                source_ref="state-results",
                source_family="official",
                observed_at=datetime(2026, 7, 3, 11, 59, 58, 1, tzinfo=UTC),
                resolved_at=datetime(2026, 7, 3, 11, 59, 58, 500000, tzinfo=UTC),
                acknowledged_at=datetime(2026, 7, 3, 11, 59, 59, 999999, tzinfo=UTC),
            ),
        ),
        config=TeamMemorySourceReliabilityScorecardDigestConfig(),
        generated_at=datetime(2026, 7, 3, 12, 0, 0, 234567, tzinfo=UTC),
    )

    assert report.freshness_age_seconds == Decimal("2.234566")
    assert report.acknowledgement_lag_seconds == Decimal("1.499999")
    assert report.rows[0].freshness_age_seconds == Decimal("2.234566")
    assert report.rows[0].acknowledgement_lag_seconds == Decimal("1.499999")


def test_blocks_high_contradiction_and_sorts_reason_codes_deterministically() -> None:
    report = build_team_memory_source_reliability_scorecard_digest(
        (
            _observation(
                source_ref="source-a",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=90_000),
                resolved_at=GENERATED_AT - timedelta(seconds=8_000),
                acknowledged_at=GENERATED_AT - timedelta(seconds=100),
                was_hit=False,
                contradiction_count=Decimal("1"),
            ),
            _observation(
                source_ref="source-b",
                source_family="official",
                observed_at=GENERATED_AT - timedelta(seconds=120),
                resolved_at=GENERATED_AT - timedelta(seconds=60),
                acknowledged_at=GENERATED_AT - timedelta(seconds=30),
                was_hit=True,
            ),
        ),
        config=TeamMemorySourceReliabilityScorecardDigestConfig(
            min_hit_rate=Decimal("0.750000"),
            max_source_age_seconds=Decimal("86400.000000"),
            max_contradiction_rate=Decimal("0.250000"),
            max_acknowledgement_lag_seconds=Decimal("3600.000000"),
            min_source_family_diversity_ratio=Decimal("0.750000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.reliability_status == "blocked"
    assert report.reason_codes == (
        "team_memory_source_reliability_scorecard_digest_high_contradiction_rate",
        "team_memory_source_reliability_scorecard_digest_low_hit_rate",
        "team_memory_source_reliability_scorecard_digest_stale_source_freshness",
        "team_memory_source_reliability_scorecard_digest_slow_resolution_acknowledgement",
        "team_memory_source_reliability_scorecard_digest_low_source_family_diversity",
    )
    assert report.rows[0].reason_codes == (
        "team_memory_source_reliability_scorecard_digest_row_high_contradiction_rate",
        "team_memory_source_reliability_scorecard_digest_row_low_hit_rate",
        "team_memory_source_reliability_scorecard_digest_row_stale_source_freshness",
        "team_memory_source_reliability_scorecard_digest_row_slow_resolution_acknowledgement",
        "team_memory_source_reliability_scorecard_digest_row_low_source_family_diversity",
    )


def test_empty_input_returns_blocked_report_only_digest() -> None:
    report = build_team_memory_source_reliability_scorecard_digest(
        (),
        config=TeamMemorySourceReliabilityScorecardDigestConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.reliability_status == "blocked"
    assert report.team_category_count == Decimal("0")
    assert report.event_count == Decimal("0")
    assert report.source_count == Decimal("0")
    assert report.rows == ()
    assert report.reason_codes == (
        "team_memory_source_reliability_scorecard_digest_empty",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_public_numeric_fields_are_decimals(report)


def test_validation_guards_decimals_datetimes_flags_sensitive_refs_and_frozen_instances() -> None:
    report = build_team_memory_source_reliability_scorecard_digest(
        (_observation(),),
        config=TeamMemorySourceReliabilityScorecardDigestConfig(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.rows[0].hit_rate = Decimal("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="contradiction_count must be a Decimal"):
        _observation(contradiction_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _observation(observed_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_team_memory_source_reliability_scorecard_digest(
            (_observation(),),
            config=TeamMemorySourceReliabilityScorecardDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        TeamMemorySourceReliabilityScorecardDigestConfig(paper_only=False)
    for source_ref in (
        "0xabc",
        "user@example.com",
        "private-source",
        "token-source",
        "order-source",
    ):
        with pytest.raises(ValueError, match="source_ref must be a redacted identifier"):
            _observation(source_ref=source_ref)


def test_static_forbidden_surface_terms_are_absent() -> None:
    import polymarket_alpha_lab.team_memory_source_reliability_scorecard_digest as module

    source = Path(module.__file__).read_text(encoding="utf-8").lower()
    forbidden_terms = (
        ".total_seconds(",
        "decimal(str(",
        "value: float",
        "account",
        "api_key",
        "auth",
        "broker",
        "cancel",
        "investment_advice",
        "live_trading",
        "place_order",
        "postgres",
        "private_key",
        "requests",
        "secret",
        "sign",
        "signer",
        "signing",
        "socket",
        "sqlite",
        "submit",
        "trading_advice",
        "urlopen",
        "wallet",
        "web3",
    )

    assert [term for term in forbidden_terms if term in source] == []


def _observation(
    *,
    team_id: str = "team-alpha",
    category: str = "politics",
    source_ref: str = "source-alpha",
    source_family: str = "official",
    observed_at: datetime | None = None,
    resolved_at: datetime | None = None,
    acknowledged_at: datetime | None = None,
    was_hit: bool = True,
    contradiction_count: Decimal = Decimal("0"),
) -> TeamMemorySourceReliabilityScorecardObservation:
    return TeamMemorySourceReliabilityScorecardObservation(
        team_id=team_id,
        category=category,
        source_ref=source_ref,
        source_family=source_family,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=300),
        resolved_at=resolved_at or GENERATED_AT - timedelta(seconds=200),
        acknowledged_at=acknowledged_at or GENERATED_AT - timedelta(seconds=100),
        was_hit=was_hit,
        contradiction_count=contradiction_count,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float value leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _assert_public_numeric_fields_are_decimals(value: object) -> None:
    numeric_name_fragments = (
        "age",
        "count",
        "lag",
        "rate",
        "ratio",
        "score",
    )
    for field in dataclasses.fields(value):
        if any(fragment in field.name for fragment in numeric_name_fragments):
            field_value = getattr(value, field.name)
            if isinstance(field_value, datetime):
                continue
            if isinstance(field_value, tuple):
                continue
            assert isinstance(field_value, Decimal), field.name
