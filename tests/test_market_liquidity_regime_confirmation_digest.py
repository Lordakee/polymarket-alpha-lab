from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_liquidity_regime_confirmation_digest import (
    MarketLiquidityRegimeConfirmationDigestConfig,
    MarketLiquidityRegimeConfirmationDigestInput,
    MarketLiquidityRegimeConfirmationDigestReport,
    MarketLiquidityRegimeConfirmationDigestRow,
    build_market_liquidity_regime_confirmation_digest,
    market_liquidity_regime_confirmation_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def config(
    **overrides: object,
) -> MarketLiquidityRegimeConfirmationDigestConfig:
    values: dict[str, object] = {
        "config_version": "market-liquidity-regime-confirmation-digest-v1",
        "min_probability_move": Decimal("0.030000"),
        "min_depth_change_ratio": Decimal("0.150000"),
        "min_spread_change_ratio": Decimal("0.120000"),
        "max_source_age_seconds": Decimal("300.000000"),
        "min_volume_proxy": Decimal("50.000000"),
        "stale_confidence_cap": Decimal("0.300000"),
        "thin_volume_confidence_cap": Decimal("0.500000"),
        "unconfirmed_confidence_cap": Decimal("0.600000"),
    }
    values.update(overrides)
    return MarketLiquidityRegimeConfirmationDigestConfig(**values)


def market_input(
    market_slug: str = "alpha-market",
    *,
    outcome_name: str = "Yes",
    probability_before: Decimal = Decimal("0.420000"),
    probability_after: Decimal = Decimal("0.490000"),
    depth_before: Decimal = Decimal("100.000000"),
    depth_after: Decimal = Decimal("140.000000"),
    spread_before: Decimal = Decimal("0.060000"),
    spread_after: Decimal = Decimal("0.040000"),
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    volume_proxy: Decimal = Decimal("90.000000"),
    base_confidence: Decimal = Decimal("0.800000"),
    source_reference: str = "public/clob/book",
    upstream_reason_codes: tuple[str, ...] = ("probability_move_detected",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketLiquidityRegimeConfirmationDigestInput:
    return MarketLiquidityRegimeConfirmationDigestInput(
        market_slug=market_slug,
        outcome_name=outcome_name,
        probability_before=probability_before,
        probability_after=probability_after,
        depth_before=depth_before,
        depth_after=depth_after,
        spread_before=spread_before,
        spread_after=spread_after,
        source_observed_at=source_observed_at,
        volume_proxy=volume_proxy,
        base_confidence=base_confidence,
        source_reference=source_reference,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    inputs: tuple[MarketLiquidityRegimeConfirmationDigestInput, ...],
    *,
    cfg: MarketLiquidityRegimeConfirmationDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketLiquidityRegimeConfirmationDigestReport:
    return build_market_liquidity_regime_confirmation_digest(
        inputs,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_floats(item)


def decimal_public_field_names(type_: type[object]) -> set[str]:
    return {
        field.name
        for field in fields(type_)
        if "Decimal" in str(field.type) or field.type is Decimal
    }


def test_empty_input_returns_report_only_diagnostic_rollup() -> None:
    report = digest(())

    assert report.generated_at == GENERATED_AT
    assert report.input_count == Decimal("0.000000")
    assert report.row_count == Decimal("0.000000")
    assert report.confirmed_count == Decimal("0.000000")
    assert report.partial_count == Decimal("0.000000")
    assert report.unconfirmed_count == Decimal("0.000000")
    assert report.stale_source_count == Decimal("0.000000")
    assert report.thin_volume_count == Decimal("0.000000")
    assert report.max_probability_move == Decimal("0.000000")
    assert report.max_confirmation_score == Decimal("0.000000")
    assert report.reason_codes == ("liquidity_regime_confirmation_digest_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_confirmed_move_uses_depth_spread_freshness_volume_and_redaction() -> None:
    report = digest(
        (
            market_input(
                source_reference="https://example.test/books?api_key=secret",
            ),
        ),
    )

    assert report.input_count == Decimal("1.000000")
    assert report.confirmed_count == Decimal("1.000000")
    assert report.partial_count == Decimal("0.000000")
    assert report.unconfirmed_count == Decimal("0.000000")
    assert report.stale_source_count == Decimal("0.000000")
    assert report.thin_volume_count == Decimal("0.000000")
    assert report.max_probability_move == Decimal("0.070000")
    assert report.max_confirmation_score == Decimal("0.800000")
    assert report.reason_codes == (
        "depth_regime_changed",
        "liquidity_regime_confirmed",
        "probability_move_detected",
        "source_fresh",
        "spread_regime_changed",
        "volume_proxy_sufficient",
    )

    row = report.rows[0]
    assert row.market_slug == "alpha-market"
    assert row.confirmation_status == "confirmed"
    assert row.probability_move == Decimal("0.070000")
    assert row.depth_change_ratio == Decimal("0.400000")
    assert row.spread_change_ratio == Decimal("0.333333")
    assert row.source_age_seconds == Decimal("120.000000")
    assert row.confirmation_score == Decimal("0.800000")
    assert row.confidence_cap == Decimal("1.000000")
    assert row.capped_confidence == Decimal("0.800000")
    assert row.source_reference == "https://example.test/books?<redacted>"
    assert row.reason_codes == report.reason_codes


def test_unconfirmed_move_caps_confidence_for_stale_and_thin_sources() -> None:
    observed_at = datetime(2026, 7, 2, 4, 50, tzinfo=timezone(timedelta(hours=-7)))
    report = digest(
        (
            market_input(
                source_observed_at=observed_at,
                depth_before=Decimal("100.000000"),
                depth_after=Decimal("104.000000"),
                spread_before=Decimal("0.050000"),
                spread_after=Decimal("0.052000"),
                volume_proxy=Decimal("10.000000"),
                base_confidence=Decimal("0.900000"),
                upstream_reason_codes=("upstream_watch",),
            ),
        ),
    )

    assert report.confirmed_count == Decimal("0.000000")
    assert report.partial_count == Decimal("0.000000")
    assert report.unconfirmed_count == Decimal("1.000000")
    assert report.stale_source_count == Decimal("1.000000")
    assert report.thin_volume_count == Decimal("1.000000")

    row = report.rows[0]
    assert row.confirmation_status == "unconfirmed"
    assert row.source_observed_at == datetime(2026, 7, 2, 11, 50, tzinfo=UTC)
    assert row.source_age_seconds == Decimal("600.000000")
    assert row.confirmation_score == Decimal("0.000000")
    assert row.confidence_cap == Decimal("0.300000")
    assert row.capped_confidence == Decimal("0.300000")
    assert row.reason_codes == (
        "depth_regime_unchanged",
        "liquidity_regime_unconfirmed",
        "source_stale",
        "spread_regime_unchanged",
        "upstream_watch",
        "volume_proxy_thin",
    )


def test_partial_confirmation_requires_probability_move_and_one_liquidity_signal() -> None:
    report = digest(
        (
            market_input(
                "partial-market",
                depth_before=Decimal("100.000000"),
                depth_after=Decimal("130.000000"),
                spread_before=Decimal("0.050000"),
                spread_after=Decimal("0.048000"),
                base_confidence=Decimal("0.900000"),
                upstream_reason_codes=(),
            ),
            market_input(
                "tiny-move-market",
                probability_before=Decimal("0.420000"),
                probability_after=Decimal("0.430000"),
                depth_before=Decimal("100.000000"),
                depth_after=Decimal("150.000000"),
                spread_before=Decimal("0.060000"),
                spread_after=Decimal("0.040000"),
                upstream_reason_codes=(),
            ),
        ),
    )

    assert [(row.market_slug, row.confirmation_status) for row in report.rows] == [
        ("partial-market", "partial"),
        ("tiny-move-market", "unconfirmed"),
    ]
    partial = report.rows[0]
    assert partial.confirmation_score == Decimal("0.400000")
    assert partial.confidence_cap == Decimal("0.600000")
    assert partial.capped_confidence == Decimal("0.600000")
    assert partial.reason_codes == (
        "depth_regime_changed",
        "liquidity_regime_partially_confirmed",
        "source_fresh",
        "spread_regime_unchanged",
        "volume_proxy_sufficient",
    )

    tiny_move = report.rows[1]
    assert tiny_move.probability_move == Decimal("0.010000")
    assert tiny_move.confirmation_score == Decimal("0.000000")
    assert "probability_move_below_threshold" in tiny_move.reason_codes


def test_rows_sort_deterministically_by_status_score_and_identity() -> None:
    report = digest(
        (
            market_input("zeta-market"),
            market_input(
                "alpha-market",
                depth_after=Decimal("104.000000"),
                spread_after=Decimal("0.055000"),
            ),
            market_input(
                "beta-market",
                depth_after=Decimal("130.000000"),
                spread_after=Decimal("0.058000"),
            ),
        ),
    )

    assert [(row.market_slug, row.confirmation_status) for row in report.rows] == [
        ("zeta-market", "confirmed"),
        ("beta-market", "partial"),
        ("alpha-market", "unconfirmed"),
    ]


def test_equal_identity_rows_sort_by_observed_time_and_redacted_reference() -> None:
    report = digest(
        (
            market_input(
                source_observed_at=GENERATED_AT - timedelta(seconds=30),
                source_reference="public/clob/b",
            ),
            market_input(
                source_observed_at=GENERATED_AT - timedelta(seconds=60),
                source_reference="public/clob/a",
            ),
        ),
    )

    assert [row.source_reference for row in report.rows] == [
        "public/clob/a",
        "public/clob/b",
    ]
    assert [row.source_age_seconds for row in report.rows] == [
        Decimal("60.000000"),
        Decimal("30.000000"),
    ]


def test_rejects_sensitive_reason_codes_before_payload_serialization() -> None:
    with pytest.raises(ValueError, match="reason_code must not contain sensitive text"):
        market_input(upstream_reason_codes=("source_token=secret",))


def test_rejects_non_decimal_numeric_fields_floats_and_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="probability_before"):
        market_input(probability_before=Decimal("NaN"))

    with pytest.raises(ValueError, match="depth_before"):
        market_input(depth_before=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="spread_after"):
        market_input(spread_after=0.04)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="min_probability_move"):
        config(min_probability_move=_DecimalSubclass("0.030000"))

    with pytest.raises(ValueError, match="base_confidence"):
        market_input(base_confidence=Decimal("Infinity"))


def test_rejects_naive_datetime_datetime_subclass_and_future_sources() -> None:
    with pytest.raises(ValueError, match="UTC-aware"):
        market_input(source_observed_at=datetime(2026, 7, 2, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        market_input(source_observed_at=_DatetimeSubclass(2026, 7, 2, tzinfo=UTC))

    with pytest.raises(ValueError, match="source_observed_at must not be after generated_at"):
        digest(
            (
                market_input(
                    source_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )


def test_hard_flags_are_required_and_public_dataclasses_are_frozen() -> None:
    report = digest((market_input(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        market_input(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        MarketLiquidityRegimeConfirmationDigestRow(
            market_slug="alpha-market",
            outcome_name="Yes",
            probability_before=Decimal("0.420000"),
            probability_after=Decimal("0.490000"),
            probability_move=Decimal("0.070000"),
            depth_before=Decimal("100.000000"),
            depth_after=Decimal("140.000000"),
            depth_change_ratio=Decimal("0.400000"),
            spread_before=Decimal("0.060000"),
            spread_after=Decimal("0.040000"),
            spread_change_ratio=Decimal("0.333333"),
            source_observed_at=GENERATED_AT - timedelta(seconds=120),
            source_age_seconds=Decimal("120.000000"),
            volume_proxy=Decimal("90.000000"),
            confirmation_score=Decimal("0.800000"),
            confidence_cap=Decimal("1.000000"),
            capped_confidence=Decimal("0.800000"),
            confirmation_status="confirmed",
            source_reference="public/clob/book",
            reason_codes=("liquidity_regime_confirmed",),
            readonly=False,
        )


def test_public_count_and_ratio_fields_are_decimal_only() -> None:
    assert "depth_change_ratio" in decimal_public_field_names(
        MarketLiquidityRegimeConfirmationDigestRow,
    )
    assert "spread_change_ratio" in decimal_public_field_names(
        MarketLiquidityRegimeConfirmationDigestRow,
    )
    assert "input_count" in decimal_public_field_names(
        MarketLiquidityRegimeConfirmationDigestReport,
    )
    assert all(
        "int" not in str(field.type) and field.type is not int
        for type_ in (
            MarketLiquidityRegimeConfirmationDigestConfig,
            MarketLiquidityRegimeConfirmationDigestInput,
            MarketLiquidityRegimeConfirmationDigestRow,
            MarketLiquidityRegimeConfirmationDigestReport,
        )
        for field in fields(type_)
    )


def test_payload_uses_decimal_strings_iso_datetimes_and_no_floats() -> None:
    report = digest(
        (market_input(),),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    payload = market_liquidity_regime_confirmation_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["max_probability_move"] == "0.070000"
    assert payload["rows"][0]["source_observed_at"] == "2026-07-02T11:58:00+00:00"
    assert payload["rows"][0]["depth_change_ratio"] == "0.400000"
    assert_no_floats(payload)


def test_source_age_preserves_subsecond_decimal_precision() -> None:
    report = digest(
        (
            market_input(
                source_observed_at=datetime(2026, 7, 2, 11, 59, 59, 500000, tzinfo=UTC),
            ),
        ),
    )

    assert report.rows[0].source_age_seconds == Decimal("0.500000")


def test_direct_report_consistency_validation() -> None:
    with pytest.raises(ValueError, match="status counts"):
        MarketLiquidityRegimeConfirmationDigestReport(
            generated_at=GENERATED_AT,
            config_version="market-liquidity-regime-confirmation-digest-v1",
            input_count=Decimal("1.000000"),
            row_count=Decimal("0.000000"),
            confirmed_count=Decimal("2.000000"),
            partial_count=Decimal("0.000000"),
            unconfirmed_count=Decimal("0.000000"),
            stale_source_count=Decimal("0.000000"),
            thin_volume_count=Decimal("0.000000"),
            max_probability_move=Decimal("0.000000"),
            max_confirmation_score=Decimal("0.000000"),
            reason_codes=("liquidity_regime_confirmed",),
            rows=(),
        )
