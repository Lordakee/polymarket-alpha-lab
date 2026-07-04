from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_perp_open_interest_flush_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "market-research-crypto-perp-open-interest-flush-digest-v0"
        ),
        "watch_open_interest_drop_ratio": d("0.060000"),
        "high_open_interest_drop_ratio": d("0.120000"),
        "min_abs_price_move_ratio": d("0.020000"),
        "high_liquidation_to_volume_ratio": d("0.080000"),
        "high_abs_funding_rate_8h": d("0.000800"),
        "stale_source_after_seconds": d("900.000000"),
    }
    values.update(overrides)
    return module.MarketResearchCryptoPerpOpenInterestFlushDigestConfig(**values)


def observation(
    source_id: str = "binance-btcusdt-perp",
    *,
    market_slug: str = "btc-open-interest-flush-risk",
    base_asset: str = "btc",
    venue_id: str = "binance-perp",
    current_open_interest_usd: Decimal = d("820000000.000000"),
    previous_open_interest_usd: Decimal = d("1000000000.000000"),
    current_mark_price: Decimal = d("93000.000000"),
    previous_mark_price: Decimal = d("100000.000000"),
    funding_rate_8h: Decimal = d("0.001200"),
    long_liquidations_usd: Decimal = d("95000000.000000"),
    short_liquidations_usd: Decimal = d("5000000.000000"),
    volume_24h_usd: Decimal = d("1000000000.000000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=60),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.CryptoPerpOpenInterestFlushObservation(
        source_id=source_id,
        market_slug=market_slug,
        base_asset=base_asset,
        venue_id=venue_id,
        current_open_interest_usd=current_open_interest_usd,
        previous_open_interest_usd=previous_open_interest_usd,
        current_mark_price=current_mark_price,
        previous_mark_price=previous_mark_price,
        funding_rate_8h=funding_rate_8h,
        long_liquidations_usd=long_liquidations_usd,
        short_liquidations_usd=short_liquidations_usd,
        volume_24h_usd=volume_24h_usd,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    *rows: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_crypto_perp_open_interest_flush_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_public_values(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("public payload must not contain float values")
    if isinstance(value, dict):
        for child in value.values():
            walk_public_values(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            walk_public_values(child)


def test_empty_digest_is_blocked_report_only_and_decimal_zeroed() -> None:
    module = api()

    report = digest(generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))))
    payload = module.market_research_crypto_perp_open_interest_flush_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_crypto_perp_open_interest_flush_digest"
    )
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.high_risk_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.clear_count == d("0.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.max_open_interest_drop_ratio == d("0.000000")
    assert report.max_abs_price_move_ratio == d("0.000000")
    assert report.max_liquidation_to_volume_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "crypto_perp_open_interest_flush_digest_empty",
    )
    assert report.reason_code_counts == (
        module.CryptoPerpOpenInterestFlushReasonCodeCount(
            reason_code="crypto_perp_open_interest_flush_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert payload["row_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    walk_public_values(payload)


def test_high_risk_digest_ranks_flush_candidates_and_reason_codes() -> None:
    report = digest(
        observation(
            "okx-solusdt-perp",
            market_slug="sol-open-interest-stable",
            base_asset="sol",
            venue_id="okx-perp",
            current_open_interest_usd=d("392000000.000000"),
            previous_open_interest_usd=d("400000000.000000"),
            current_mark_price=d("151.500000"),
            previous_mark_price=d("150.000000"),
            funding_rate_8h=d("0.000100"),
            long_liquidations_usd=d("1000000.000000"),
            short_liquidations_usd=d("1000000.000000"),
            volume_24h_usd=d("800000000.000000"),
        ),
        observation(
            "coinbase-ethusdt-perp",
            market_slug="eth-open-interest-watch",
            base_asset="eth",
            venue_id="coinbase-perp",
            current_open_interest_usd=d("460000000.000000"),
            previous_open_interest_usd=d("500000000.000000"),
            current_mark_price=d("3430.000000"),
            previous_mark_price=d("3500.000000"),
            funding_rate_8h=d("0.000200"),
            long_liquidations_usd=d("9000000.000000"),
            short_liquidations_usd=d("1000000.000000"),
            volume_24h_usd=d("500000000.000000"),
        ),
        observation(),
    )

    assert report.digest_status == "high_risk"
    assert report.recommended_next_step == (
        "block_report_only_crypto_perp_open_interest_flush_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.high_risk_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.clear_count == d("1.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.max_open_interest_drop_ratio == d("0.180000")
    assert report.max_abs_price_move_ratio == d("0.070000")
    assert report.max_liquidation_to_volume_ratio == d("0.100000")
    assert report.reason_codes == (
        "crypto_perp_open_interest_flush_high_risk_present",
        "crypto_perp_open_interest_flush_watch_present",
    )

    assert [
        (row.market_slug, row.flush_status, row.open_interest_drop_ratio)
        for row in report.rows
    ] == [
        ("btc-open-interest-flush-risk", "high_risk", d("0.180000")),
        ("eth-open-interest-watch", "watch", d("0.080000")),
        ("sol-open-interest-stable", "clear", d("0.020000")),
    ]

    high, watched, clear = report.rows
    assert high.open_interest_change_ratio == d("-0.180000")
    assert high.mark_price_change_ratio == d("-0.070000")
    assert high.abs_price_move_ratio == d("0.070000")
    assert high.liquidation_to_volume_ratio == d("0.100000")
    assert high.dominant_liquidation_side == "long"
    assert high.observed_at == GENERATED_AT - timedelta(seconds=60)
    assert high.reason_codes == (
        "open_interest_drop_high",
        "price_move_confirms_flush",
        "liquidation_pressure_high",
        "funding_extreme",
    )
    assert watched.reason_codes == (
        "open_interest_drop_watch",
        "price_move_confirms_flush",
    )
    assert clear.reason_codes == ("open_interest_flush_clear",)


def test_digest_output_is_deterministic_for_unsorted_inputs_and_payloads() -> None:
    module = api()
    gamma = observation("source-gamma", market_slug="gamma-flush", base_asset="gamma")
    alpha = observation(
        "source-alpha",
        market_slug="alpha-flush",
        base_asset="alpha",
        current_open_interest_usd=d("880000000.000000"),
        previous_open_interest_usd=d("1000000000.000000"),
        current_mark_price=d("97000.000000"),
        previous_mark_price=d("100000.000000"),
        funding_rate_8h=d("0.000100"),
        long_liquidations_usd=d("80000000.000000"),
        short_liquidations_usd=d("1000000.000000"),
        volume_24h_usd=d("1000000000.000000"),
    )
    first = digest(gamma, alpha)
    second = digest(alpha, gamma)

    first_payload = module.market_research_crypto_perp_open_interest_flush_digest_payload(
        first,
    )
    second_payload = module.market_research_crypto_perp_open_interest_flush_digest_payload(
        second,
    )

    assert tuple(row.source_id for row in first.rows) == (
        "source-gamma",
        "source-alpha",
    )
    assert first.reason_codes == tuple(sorted(first.reason_codes))
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_validates_decimals_datetimes_duplicates_and_row_consistency() -> None:
    module = api()

    with pytest.raises(ValueError, match="current_open_interest_usd must be a Decimal"):
        observation(current_open_interest_usd=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="previous_open_interest_usd must be positive"):
        observation(previous_open_interest_usd=d("0.000000"))
    with pytest.raises(ValueError, match="current_mark_price must be a Decimal"):
        observation(current_mark_price=93000.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observations must not contain duplicate"):
        digest(observation("duplicate-source"), observation("duplicate-source"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_crypto_perp_open_interest_flush_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reason_codes must match row metrics"):
        module.CryptoPerpOpenInterestFlushDigestRow(
            source_id="manual-row",
            market_slug="manual-row",
            base_asset="btc",
            venue_id="manual-venue",
            current_open_interest_usd=d("820000000.000000"),
            previous_open_interest_usd=d("1000000000.000000"),
            open_interest_change_ratio=d("-0.180000"),
            open_interest_drop_ratio=d("0.180000"),
            current_mark_price=d("93000.000000"),
            previous_mark_price=d("100000.000000"),
            mark_price_change_ratio=d("-0.070000"),
            abs_price_move_ratio=d("0.070000"),
            funding_rate_8h=d("0.001200"),
            long_liquidations_usd=d("95000000.000000"),
            short_liquidations_usd=d("5000000.000000"),
            volume_24h_usd=d("1000000000.000000"),
            liquidation_to_volume_ratio=d("0.100000"),
            dominant_liquidation_side="long",
            source_age_seconds=d("60.000000"),
            observed_at=GENERATED_AT - timedelta(seconds=60),
            flush_status="high_risk",
            reason_codes=("open_interest_flush_clear",),
        )


def test_hard_flags_frozen_dataclasses_and_decimal_public_numerics_are_enforced() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.CryptoPerpOpenInterestFlushReasonCodeCount(
            reason_code="crypto_perp_open_interest_flush_watch_present",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
            readonly=False,
        )

    report = digest(observation("frozen-source"))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    values = (
        config(),
        observation("dataclass-source"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    for value in values:
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            public_type = str(field.type).lower()
            assert "float" not in public_type
            field_value = getattr(value, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_usd")
                or field.name.endswith("_price")
                or field.name.endswith("_seconds")
                or field.name.endswith("_8h")
            ):
                assert type(field_value) is Decimal, field.name


def test_non_default_thresholds_change_screening_status_without_mutating_inputs() -> None:
    source = observation(
        "threshold-source",
        current_open_interest_usd=d("920000000.000000"),
        previous_open_interest_usd=d("1000000000.000000"),
        current_mark_price=d("97000.000000"),
        previous_mark_price=d("100000.000000"),
        funding_rate_8h=d("0.000100"),
        long_liquidations_usd=d("1000000.000000"),
        short_liquidations_usd=d("1000000.000000"),
        volume_24h_usd=d("1000000000.000000"),
    )

    default_report = digest(source)
    loose_report = digest(
        source,
        cfg=config(
            watch_open_interest_drop_ratio=d("0.090000"),
            high_open_interest_drop_ratio=d("0.150000"),
            min_abs_price_move_ratio=d("0.040000"),
        ),
    )
    tight_report = digest(
        source,
        cfg=config(
            watch_open_interest_drop_ratio=d("0.030000"),
            high_open_interest_drop_ratio=d("0.070000"),
        ),
    )

    assert default_report.rows[0].flush_status == "watch"
    assert loose_report.rows[0].flush_status == "clear"
    assert tight_report.rows[0].flush_status == "high_risk"
    assert source.current_open_interest_usd == d("920000000.000000")

    with pytest.raises(ValueError, match="high_open_interest_drop_ratio"):
        config(high_open_interest_drop_ratio=d("0.050000"))
    with pytest.raises(ValueError, match="watch_open_interest_drop_ratio"):
        config(watch_open_interest_drop_ratio=0.060000)  # type: ignore[arg-type]


def test_module_scope_is_pure_report_only_without_durable_or_mutating_surfaces() -> None:
    source = inspect.getsource(api()).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "subprocess",
        "path(",
        "read_text",
        "write_text",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "secret",
        "auth",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source
