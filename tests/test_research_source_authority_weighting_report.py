from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.research_source_authority_weighting_report as api
from polymarket_alpha_lab.research_source_authority_weighting_report import (
    ResearchSourceAuthorityClassMixRow,
    ResearchSourceAuthorityObservation,
    ResearchSourceAuthorityWeightingConfig,
    ResearchSourceAuthorityWeightingReport,
    ResearchSourceAuthorityWeightingRow,
    build_research_source_authority_weighting_report,
    research_source_authority_weighting_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    packet_id: str = "packet-alpha",
    authority_class: str = "official",
    source_count: Decimal = Decimal("1"),
    latest_observed_at: datetime | None = None,
    contradiction_count: Decimal = Decimal("0"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceAuthorityObservation:
    return ResearchSourceAuthorityObservation(
        packet_id=packet_id,
        authority_class=authority_class,
        source_count=source_count,
        latest_observed_at=(
            latest_observed_at
            if latest_observed_at is not None
            else GENERATED_AT - timedelta(minutes=30)
        ),
        contradiction_count=contradiction_count,
        reason_codes=reason_codes,
    )


def report(
    observations: tuple[ResearchSourceAuthorityObservation, ...],
    *,
    config: ResearchSourceAuthorityWeightingConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceAuthorityWeightingReport:
    return build_research_source_authority_weighting_report(
        observations,
        generated_at=generated_at,
        config=config,
    )


def test_authority_mix_freshness_and_coverage_pass_with_deterministic_digest() -> None:
    weighting_report = report(
        (
            observation(
                authority_class="data",
                latest_observed_at=GENERATED_AT - timedelta(hours=4),
            ),
            observation(
                authority_class="official",
                source_count=d("2"),
                latest_observed_at=GENERATED_AT - timedelta(minutes=30),
            ),
            observation(
                authority_class="expert",
                latest_observed_at=GENERATED_AT - timedelta(hours=2),
                reason_codes=("manual_reviewed",),
            ),
        ),
    )

    assert type(weighting_report) is ResearchSourceAuthorityWeightingReport
    assert weighting_report.status == "pass"
    assert weighting_report.packet_count == d("1.000000")
    assert weighting_report.pass_count == d("1.000000")
    assert weighting_report.watch_count == d("0.000000")
    assert weighting_report.block_count == d("0.000000")
    assert weighting_report.average_authority_weighting_score == d("0.939375")
    assert weighting_report.max_recheck_urgency_score == d("0.062500")
    assert len(weighting_report.derived_validation_digest) == 64
    assert weighting_report.paper_only is True
    assert weighting_report.report_only is True
    assert weighting_report.readonly is True

    row = weighting_report.rows[0]
    assert type(row) is ResearchSourceAuthorityWeightingRow
    assert row.packet_id == "packet-alpha"
    assert row.source_count == d("4.000000")
    assert row.authority_class_count == d("3.000000")
    assert row.required_authority_class_count == d("2.000000")
    assert row.covered_required_authority_class_count == d("2.000000")
    assert row.coverage_gap_count == d("0.000000")
    assert row.authority_weight_score == d("0.900000")
    assert row.freshness_score == d("0.937500")
    assert row.contradiction_pressure == d("0.000000")
    assert row.coverage_gap_score == d("0.000000")
    assert row.coverage_score == d("1.000000")
    assert row.authority_weighting_score == d("0.939375")
    assert row.recheck_urgency_score == d("0.062500")
    assert row.status == "pass"
    assert row.missing_required_authority_classes == ()
    assert row.reason_codes == (
        "contradiction_pressure_low",
        "coverage_complete",
        "fresh_authority_sources",
        "input_manual_reviewed",
        "recheck_urgency_low",
        "research_source_authority_weighting_pass",
        "strong_authority_class_mix",
    )

    assert tuple(item.authority_class for item in row.authority_class_mix) == (
        "official",
        "expert",
        "data",
    )
    official_mix = row.authority_class_mix[0]
    assert type(official_mix) is ResearchSourceAuthorityClassMixRow
    assert official_mix.source_count == d("2.000000")
    assert official_mix.source_share == d("0.500000")
    assert official_mix.authority_weight == d("1.000000")
    assert official_mix.weighted_authority_contribution == d("0.500000")
    assert official_mix.source_age_seconds == d("1800.000000")
    assert official_mix.freshness_score == d("1.000000")

    payload = research_source_authority_weighting_report_payload(weighting_report)
    assert payload == weighting_report.payload
    assert payload["average_authority_weighting_score"] == "0.939375"
    assert payload["rows"][0]["authority_class_mix"][0]["source_count"] == "2.000000"
    assert payload["derived_validation_digest"] == weighting_report.derived_validation_digest
    json.dumps(payload, sort_keys=True)
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(weighting_report)


def test_contradiction_pressure_coverage_gaps_and_staleness_block_recheck() -> None:
    weighting_report = report(
        (
            observation(
                packet_id="packet-risk",
                authority_class="social",
                source_count=d("2"),
                latest_observed_at=GENERATED_AT - timedelta(days=2),
                contradiction_count=d("2"),
            ),
        ),
    )

    row = weighting_report.rows[0]
    assert weighting_report.status == "block"
    assert weighting_report.block_count == d("1.000000")
    assert weighting_report.average_authority_weighting_score == d("0.112500")
    assert weighting_report.max_recheck_urgency_score == d("1.000000")
    assert row.packet_id == "packet-risk"
    assert row.source_count == d("2.000000")
    assert row.authority_class_count == d("1.000000")
    assert row.covered_required_authority_class_count == d("0.000000")
    assert row.coverage_gap_count == d("2.000000")
    assert row.authority_weight_score == d("0.250000")
    assert row.freshness_score == d("0.000000")
    assert row.contradiction_pressure == d("1.000000")
    assert row.coverage_gap_score == d("1.000000")
    assert row.coverage_score == d("0.000000")
    assert row.authority_weighting_score == d("0.112500")
    assert row.recheck_urgency_score == d("1.000000")
    assert row.status == "block"
    assert row.missing_required_authority_classes == ("official", "expert")
    assert row.reason_codes == (
        "contradiction_pressure_high",
        "coverage_gaps_present",
        "recheck_urgency_high",
        "research_source_authority_weighting_block",
        "stale_authority_sources",
        "weak_authority_class_mix",
    )


def test_rows_reason_counts_payload_and_digest_are_deterministic() -> None:
    first = report(
        (
            observation(packet_id="packet-z", authority_class="media"),
            observation(packet_id="packet-a", authority_class="official"),
            observation(packet_id="packet-a", authority_class="expert"),
        ),
    )
    second = report(
        (
            observation(packet_id="packet-a", authority_class="expert"),
            observation(packet_id="packet-z", authority_class="media"),
            observation(packet_id="packet-a", authority_class="official"),
        ),
    )

    assert tuple(row.packet_id for row in first.rows) == ("packet-a", "packet-z")
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.payload == second.payload
    assert tuple(
        (item.reason_code, item.count)
        for item in first.reason_code_counts
        if item.reason_code.startswith("research_source_authority_weighting_")
    ) == (
        ("research_source_authority_weighting_pass", d("1.000000")),
        ("research_source_authority_weighting_watch", d("1.000000")),
    )
    encoded = json.dumps(first.payload, sort_keys=True)
    assert "blocked" not in encoded
    assert ": 0.5" not in encoded
    assert "https://" not in encoded
    assert "market_id" not in encoded
    assert "source_text" not in encoded
    assert "question" not in encoded


def test_validation_rejects_bad_types_unsafe_identifiers_future_times_and_flags() -> None:
    with pytest.raises(ValueError, match="authority_mix_score_weight"):
        ResearchSourceAuthorityWeightingConfig(authority_mix_score_weight=0.45)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="official_authority_weight"):
        ResearchSourceAuthorityWeightingConfig(
            official_authority_weight=_DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="required_authority_classes"):
        ResearchSourceAuthorityWeightingConfig(required_authority_classes=("official", "official"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="authority_class"):
        observation(authority_class="blog")
    with pytest.raises(ValueError, match="source_count"):
        observation(source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_count"):
        observation(source_count=d("1.5"))
    with pytest.raises(ValueError, match="latest_observed_at"):
        observation(latest_observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="latest_observed_at"):
        report((observation(latest_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="contradiction_count"):
        observation(source_count=d("1"), contradiction_count=d("2"))
    with pytest.raises(ValueError, match="unsafe public"):
        observation(packet_id="https://example.test/raw")
    with pytest.raises(ValueError, match="unsafe public"):
        observation(packet_id="market_id_123")
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)


def test_public_dataclasses_are_frozen_and_digest_rejects_tampering() -> None:
    weighting_report = report(
        (
            observation(authority_class="official"),
            observation(authority_class="expert"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        weighting_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        weighting_report.rows[0].authority_weighting_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(weighting_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(weighting_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="readonly"):
        replace(weighting_report, readonly=False)
    with pytest.raises(TypeError):

        class BadReport(ResearchSourceAuthorityWeightingReport):
            pass


def test_owned_module_exposes_no_raw_source_market_or_live_trading_surfaces() -> None:
    forbidden_public_fragments = (
        "url",
        "source_text",
        "market_id",
        "question",
        "wallet",
        "order",
        "live",
        "trade",
        "network",
        "database",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    for cls in (
        ResearchSourceAuthorityWeightingConfig,
        ResearchSourceAuthorityObservation,
        ResearchSourceAuthorityClassMixRow,
        ResearchSourceAuthorityWeightingRow,
        ResearchSourceAuthorityWeightingReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
