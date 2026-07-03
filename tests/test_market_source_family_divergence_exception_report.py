from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_source_family_divergence_exception_report import (
    DIVERGENCE_BEYOND_THRESHOLD_REASON,
    INSUFFICIENT_INDEPENDENT_FAMILIES_REASON,
    MISSING_SOURCE_FAMILY_EVIDENCE_REASON,
    STALE_CONFLICT_ACKNOWLEDGEMENT_REASON,
    UNRESOLVED_CONFLICT_REASON,
    MarketSourceFamilyDivergenceExceptionConfig,
    MarketSourceFamilyDivergenceExceptionInputRow,
    build_market_source_family_divergence_exception_report,
    market_source_family_divergence_exception_report_to_json_dict,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def _row(
    market_id: str,
    family: str,
    probability: str,
    *,
    category_id: str = "macro",
    observed_delta_seconds: int = 300,
    acknowledged_delta_seconds: int | None = 300,
    conflict_resolved: bool = True,
) -> MarketSourceFamilyDivergenceExceptionInputRow:
    acknowledged_at = (
        None
        if acknowledged_delta_seconds is None
        else GENERATED_AT - timedelta(seconds=acknowledged_delta_seconds)
    )
    return MarketSourceFamilyDivergenceExceptionInputRow(
        market_id=market_id,
        category_id=category_id,
        source_family=family,
        source_probability=Decimal(probability),
        evidence_observed_at=GENERATED_AT - timedelta(seconds=observed_delta_seconds),
        conflict_acknowledged_at=acknowledged_at,
        conflict_resolved=conflict_resolved,
    )


def test_builds_deterministic_exception_rows_and_rollups_with_decimal_public_surface() -> None:
    report = build_market_source_family_divergence_exception_report(
        (
            _row(
                "m-beta",
                "official",
                "0.810000",
                category_id="sports",
                observed_delta_seconds=600,
                acknowledged_delta_seconds=7200,
                conflict_resolved=False,
            ),
            _row(
                "m-alpha",
                "official",
                "0.300000",
                acknowledged_delta_seconds=None,
                conflict_resolved=False,
            ),
            _row(
                "m-beta",
                "primary",
                "0.200000",
                category_id="sports",
                observed_delta_seconds=3700,
                acknowledged_delta_seconds=7200,
                conflict_resolved=False,
            ),
            _row(
                "m-alpha",
                "primary",
                "0.610000",
                acknowledged_delta_seconds=None,
                conflict_resolved=False,
            ),
            _row(
                "m-clear",
                "official",
                "0.540000",
                category_id="crypto",
            ),
            _row(
                "m-clear",
                "primary",
                "0.560000",
                category_id="crypto",
            ),
        ),
        config=MarketSourceFamilyDivergenceExceptionConfig(
            min_independent_source_families=Decimal("2"),
            max_family_probability_divergence=Decimal("0.250000"),
            stale_conflict_acknowledgement_seconds=Decimal("3600"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "blocked"
    assert report.reason_codes == (
        STALE_CONFLICT_ACKNOWLEDGEMENT_REASON,
        UNRESOLVED_CONFLICT_REASON,
        DIVERGENCE_BEYOND_THRESHOLD_REASON,
    )
    assert report.market_count == Decimal("3.000000")
    assert report.exception_market_count == Decimal("2.000000")
    assert report.blocked_market_count == Decimal("2.000000")
    assert report.watch_market_count == Decimal("0.000000")
    assert report.clear_market_count == Decimal("1.000000")
    assert report.source_family_count == Decimal("6.000000")
    assert report.exception_market_ratio == Decimal("0.666667")
    assert report.max_family_probability_delta == Decimal("0.610000")
    assert report.max_evidence_age_seconds == Decimal("3700.000000")

    assert [row.market_id for row in report.rows] == ["m-beta", "m-alpha", "m-clear"]
    assert report.rows[0].exception_status == "blocked"
    assert report.rows[0].reason_codes == (
        STALE_CONFLICT_ACKNOWLEDGEMENT_REASON,
        UNRESOLVED_CONFLICT_REASON,
        DIVERGENCE_BEYOND_THRESHOLD_REASON,
    )
    assert report.rows[0].source_family_count == Decimal("2.000000")
    assert report.rows[0].family_probability_delta == Decimal("0.610000")
    assert report.rows[0].max_evidence_age_seconds == Decimal("3700.000000")
    assert report.rows[1].reason_codes == (
        UNRESOLVED_CONFLICT_REASON,
        DIVERGENCE_BEYOND_THRESHOLD_REASON,
    )
    assert report.rows[2].exception_status == "clear"

    assert report.family_rollups[0].source_family == "official"
    assert report.family_rollups[0].market_count == Decimal("3.000000")
    assert report.family_rollups[0].exception_market_count == Decimal("2.000000")
    assert report.category_rollups[0].category_id == "macro"
    assert report.category_rollups[0].exception_market_count == Decimal("1.000000")
    assert report.category_rollups[1].category_id == "sports"
    assert report.category_rollups[1].blocked_market_count == Decimal("1.000000")

    with pytest.raises(FrozenInstanceError):
        report.rows[0].exception_status = "clear"  # type: ignore[misc]


def test_flags_missing_evidence_and_insufficient_independent_families_as_watch() -> None:
    report = build_market_source_family_divergence_exception_report(
        (
            _row("m-missing", "official", "0.420000", category_id="macro"),
            _row("m-solo", "primary", "0.650000", category_id="macro"),
        ),
        config=MarketSourceFamilyDivergenceExceptionConfig(
            min_independent_source_families=Decimal("2"),
            max_family_probability_divergence=Decimal("0.250000"),
            stale_conflict_acknowledgement_seconds=Decimal("3600"),
        ),
        required_source_families=("official", "primary"),
        generated_at=GENERATED_AT,
    )

    assert report.report_status == "watch"
    assert report.reason_codes == (
        INSUFFICIENT_INDEPENDENT_FAMILIES_REASON,
        MISSING_SOURCE_FAMILY_EVIDENCE_REASON,
    )
    assert [row.market_id for row in report.rows] == ["m-missing", "m-solo"]
    assert report.rows[0].exception_status == "watch"
    assert report.rows[0].reason_codes == (
        INSUFFICIENT_INDEPENDENT_FAMILIES_REASON,
        MISSING_SOURCE_FAMILY_EVIDENCE_REASON,
    )
    assert report.rows[0].missing_source_family_count == Decimal("1.000000")
    assert report.rows[0].missing_source_families == ("primary",)
    assert report.rows[1].reason_codes == (
        INSUFFICIENT_INDEPENDENT_FAMILIES_REASON,
        MISSING_SOURCE_FAMILY_EVIDENCE_REASON,
    )


def test_latest_family_tie_breaker_is_order_independent_and_conservative() -> None:
    resolved_official = _row(
        "m-tie",
        "official",
        "0.600000",
        observed_delta_seconds=300,
        conflict_resolved=True,
    )
    unresolved_official = _row(
        "m-tie",
        "official",
        "0.200000",
        observed_delta_seconds=300,
        acknowledged_delta_seconds=None,
        conflict_resolved=False,
    )
    primary = _row("m-tie", "primary", "0.500000", observed_delta_seconds=300)

    config = MarketSourceFamilyDivergenceExceptionConfig(
        min_independent_source_families=Decimal("2"),
        max_family_probability_divergence=Decimal("0.250000"),
        stale_conflict_acknowledgement_seconds=Decimal("3600"),
    )
    first = build_market_source_family_divergence_exception_report(
        (resolved_official, unresolved_official, primary),
        config=config,
        generated_at=GENERATED_AT,
    )
    second = build_market_source_family_divergence_exception_report(
        (unresolved_official, resolved_official, primary),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert first.rows[0] == second.rows[0]
    assert first.rows[0].reason_codes == (
        UNRESOLVED_CONFLICT_REASON,
        DIVERGENCE_BEYOND_THRESHOLD_REASON,
    )


def test_public_numerics_reject_int_float_and_json_helper_emits_decimal_strings() -> None:
    with pytest.raises(ValueError, match="min_independent_source_families must be a Decimal"):
        MarketSourceFamilyDivergenceExceptionConfig(
            min_independent_source_families=2,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="source_probability must be a Decimal"):
        MarketSourceFamilyDivergenceExceptionInputRow(
            market_id="m-float",
            category_id="macro",
            source_family="official",
            source_probability=0.5,  # type: ignore[arg-type]
            evidence_observed_at=GENERATED_AT,
            conflict_acknowledged_at=None,
            conflict_resolved=False,
        )

    report = build_market_source_family_divergence_exception_report(
        (
            _row("m-json", "official", "0.100000"),
            _row("m-json", "primary", "0.700000", conflict_resolved=False),
        ),
        config=MarketSourceFamilyDivergenceExceptionConfig(),
        generated_at=GENERATED_AT,
    )

    payload = market_source_family_divergence_exception_report_to_json_dict(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["rows"][0]["family_probability_delta"] == "0.600000"
    assert payload["family_rollups"][0]["market_count"] == "1.000000"

    def assert_no_float(value: object) -> None:
        if isinstance(value, float):
            raise AssertionError(f"float leaked into JSON payload: {value!r}")
        if isinstance(value, dict):
            for child in value.values():
                assert_no_float(child)
        if isinstance(value, list):
            for child in value:
                assert_no_float(child)

    assert_no_float(payload)


@pytest.mark.parametrize("market_id", ("m-trade", "m-replace", "m-exchange"))
def test_rejects_mutation_terms_in_public_strings(market_id: str) -> None:
    with pytest.raises(ValueError, match="source family divergence exception input row"):
        MarketSourceFamilyDivergenceExceptionInputRow(
            market_id=market_id,
            category_id="macro",
            source_family="official",
            source_probability=Decimal("0.500000"),
            evidence_observed_at=GENERATED_AT,
            conflict_acknowledged_at=None,
            conflict_resolved=False,
        )


def test_rejects_naive_datetimes_and_unsafe_or_non_readonly_public_surface() -> None:
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_market_source_family_divergence_exception_report(
            (_row("m-naive", "official", "0.500000"),),
            config=MarketSourceFamilyDivergenceExceptionConfig(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="source family divergence exception input row"):
        MarketSourceFamilyDivergenceExceptionInputRow(
            market_id="m-token",
            category_id="macro",
            source_family="official",
            source_probability=Decimal("0.500000"),
            evidence_observed_at=GENERATED_AT,
            conflict_acknowledged_at=None,
            conflict_resolved=False,
        )
    with pytest.raises(ValueError, match="paper_only"):
        MarketSourceFamilyDivergenceExceptionConfig(paper_only=False)
