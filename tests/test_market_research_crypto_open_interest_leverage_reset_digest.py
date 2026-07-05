from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_crypto_open_interest_leverage_reset_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "market-research-crypto-open-interest-leverage-reset-digest-v0"
        ),
        "watch_open_interest_drop_ratio": d("0.050000"),
        "blocked_open_interest_drop_ratio": d("0.120000"),
        "watch_leverage_drop_ratio": d("0.100000"),
        "blocked_leverage_drop_ratio": d("0.200000"),
        "min_liquidation_to_volume_ratio": d("0.040000"),
        "high_abs_funding_rate_8h": d("0.000800"),
        "stale_source_after_seconds": d("900.000000"),
    }
    values.update(overrides)
    return module.MarketResearchCryptoOpenInterestLeverageResetDigestConfig(**values)


def observation(
    source_id: str = "binance-btcusdt-perp",
    *,
    event_key: str = "btc-open-interest-leverage-reset",
    base_asset: str = "btc",
    venue_id: str = "binance-perp",
    current_open_interest_usd: Decimal = d("760000000.000000"),
    previous_open_interest_usd: Decimal = d("1000000000.000000"),
    current_estimated_leverage_ratio: Decimal = d("3.000000"),
    previous_estimated_leverage_ratio: Decimal = d("5.000000"),
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
    return module.CryptoOpenInterestLeverageResetObservation(
        source_id=source_id,
        event_key=event_key,
        base_asset=base_asset,
        venue_id=venue_id,
        current_open_interest_usd=current_open_interest_usd,
        previous_open_interest_usd=previous_open_interest_usd,
        current_estimated_leverage_ratio=current_estimated_leverage_ratio,
        previous_estimated_leverage_ratio=previous_estimated_leverage_ratio,
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
    return module.build_market_research_crypto_open_interest_leverage_reset_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_public_values(value: object) -> None:
    if isinstance(value, (Decimal, datetime, float)):
        pytest.fail("public payload must contain serialized scalar values")
    if isinstance(value, dict):
        for key, child in value.items():
            assert "market_slug" not in key.lower()
            walk_public_values(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            walk_public_values(child)


def test_empty_digest_is_blocked_report_only_and_decimal_zeroed() -> None:
    module = api()

    report = digest(generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))))
    payload = module.market_research_crypto_open_interest_leverage_reset_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_crypto_open_interest_leverage_reset_digest"
    )
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.max_open_interest_drop_ratio == d("0.000000")
    assert report.max_leverage_drop_ratio == d("0.000000")
    assert report.max_liquidation_to_volume_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "crypto_open_interest_leverage_reset_digest_empty",
    )
    assert report.reason_code_counts == (
        module.CryptoOpenInterestLeverageResetReasonCodeCount(
            reason_code="crypto_open_interest_leverage_reset_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert payload["row_count"] == "0.000000"
    assert payload["generated_at"] == "2026-07-05T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    walk_public_values(payload)


def test_blocked_digest_ranks_leverage_reset_candidates_and_reason_codes() -> None:
    report = digest(
        observation(
            "okx-solusdt-perp",
            event_key="sol-leverage-stable",
            base_asset="sol",
            venue_id="okx-perp",
            current_open_interest_usd=d("995000000.000000"),
            previous_open_interest_usd=d("1000000000.000000"),
            current_estimated_leverage_ratio=d("4.950000"),
            previous_estimated_leverage_ratio=d("5.000000"),
            funding_rate_8h=d("0.000100"),
            long_liquidations_usd=d("1000000.000000"),
            short_liquidations_usd=d("1000000.000000"),
            volume_24h_usd=d("800000000.000000"),
        ),
        observation(
            "coinbase-ethusdt-perp",
            event_key="eth-leverage-reset-watch",
            base_asset="eth",
            venue_id="coinbase-perp",
            current_open_interest_usd=d("930000000.000000"),
            previous_open_interest_usd=d("1000000000.000000"),
            current_estimated_leverage_ratio=d("4.400000"),
            previous_estimated_leverage_ratio=d("5.000000"),
            funding_rate_8h=d("0.000200"),
            long_liquidations_usd=d("9000000.000000"),
            short_liquidations_usd=d("1000000.000000"),
            volume_24h_usd=d("500000000.000000"),
        ),
        observation(),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_crypto_open_interest_leverage_reset_digest"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.max_open_interest_drop_ratio == d("0.240000")
    assert report.max_leverage_drop_ratio == d("0.400000")
    assert report.max_liquidation_to_volume_ratio == d("0.100000")
    assert report.reason_codes == (
        "crypto_open_interest_leverage_reset_blocked_present",
        "crypto_open_interest_leverage_reset_watch_present",
    )

    assert [
        (row.event_key, row.reset_status, row.open_interest_drop_ratio)
        for row in report.rows
    ] == [
        ("btc-open-interest-leverage-reset", "blocked", d("0.240000")),
        ("eth-leverage-reset-watch", "watch", d("0.070000")),
        ("sol-leverage-stable", "pass", d("0.005000")),
    ]

    blocked, watched, passed = report.rows
    assert blocked.open_interest_change_ratio == d("-0.240000")
    assert blocked.leverage_change_ratio == d("-0.400000")
    assert blocked.leverage_drop_ratio == d("0.400000")
    assert blocked.liquidation_to_volume_ratio == d("0.100000")
    assert blocked.dominant_liquidation_side == "long"
    assert blocked.observed_at == GENERATED_AT - timedelta(seconds=60)
    assert blocked.reason_codes == (
        "open_interest_drop_blocked",
        "leverage_drop_blocked",
        "liquidation_confirms_reset",
        "funding_extreme",
    )
    assert watched.reason_codes == (
        "open_interest_drop_watch",
        "leverage_drop_watch",
    )
    assert passed.reason_codes == ("open_interest_leverage_reset_inline",)


def test_digest_output_is_deterministic_for_unsorted_inputs_and_payloads() -> None:
    module = api()
    gamma = observation("source-gamma", event_key="gamma-reset", base_asset="gamma")
    alpha = observation(
        "source-alpha",
        event_key="alpha-reset",
        base_asset="alpha",
        current_open_interest_usd=d("880000000.000000"),
        previous_open_interest_usd=d("1000000000.000000"),
        current_estimated_leverage_ratio=d("3.500000"),
        previous_estimated_leverage_ratio=d("5.000000"),
        funding_rate_8h=d("0.000100"),
        long_liquidations_usd=d("80000000.000000"),
        short_liquidations_usd=d("1000000.000000"),
        volume_24h_usd=d("1000000000.000000"),
    )
    first = digest(gamma, alpha)
    second = digest(alpha, gamma)

    first_payload = (
        module.market_research_crypto_open_interest_leverage_reset_digest_payload(
            first,
        )
    )
    second_payload = (
        module.market_research_crypto_open_interest_leverage_reset_digest_payload(
            second,
        )
    )

    assert tuple(row.source_id for row in first.rows) == (
        "source-gamma",
        "source-alpha",
    )
    assert first.reason_codes == (
        "crypto_open_interest_leverage_reset_blocked_present",
    )
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_validates_decimals_datetimes_duplicates_and_public_canonical_records() -> None:
    module = api()

    with pytest.raises(ValueError, match="current_open_interest_usd must be a Decimal"):
        observation(current_open_interest_usd=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="current_open_interest_usd must be six-decimal"):
        observation(current_open_interest_usd=d("760000000"))
    with pytest.raises(ValueError, match="watch_open_interest_drop_ratio must be six-decimal"):
        config(watch_open_interest_drop_ratio=d("0.0500001"))
    with pytest.raises(ValueError, match="previous_open_interest_usd must be positive"):
        observation(previous_open_interest_usd=d("0.000000"))
    with pytest.raises(ValueError, match="current_estimated_leverage_ratio"):
        observation(current_estimated_leverage_ratio=3.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at must be UTC-aware"):
        observation(observed_at=datetime(2026, 7, 5, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 5, 12, 0, tzinfo=UTC))
    normalized = observation(
        observed_at=(GENERATED_AT - timedelta(minutes=5)).astimezone(
            timezone(timedelta(hours=-4)),
        ),
    )
    assert normalized.observed_at == GENERATED_AT - timedelta(minutes=5)
    assert normalized.observed_at.tzinfo is UTC
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observations must not contain duplicate"):
        digest(observation("duplicate-source"), observation("duplicate-source"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_crypto_open_interest_leverage_reset_digest(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 5, 12, 0, tzinfo=UTC),
        )

    valid_report = digest(
        observation("blocked-source"),
        observation(
            "watch-source",
            event_key="watch-reset",
            current_open_interest_usd=d("930000000.000000"),
            previous_open_interest_usd=d("1000000000.000000"),
            current_estimated_leverage_ratio=d("4.400000"),
            previous_estimated_leverage_ratio=d("5.000000"),
            funding_rate_8h=d("0.000100"),
            long_liquidations_usd=d("1000000.000000"),
            short_liquidations_usd=d("1000000.000000"),
            volume_24h_usd=d("1000000000.000000"),
        ),
    )
    with pytest.raises(ValueError, match="reason_codes must be canonical"):
        replace(
            valid_report.rows[0],
            reason_codes=(
                "liquidation_confirms_reset",
                "open_interest_drop_blocked",
            ),
        )
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(valid_report, rows=tuple(reversed(valid_report.rows)))
    with pytest.raises(ValueError, match="rows must be a canonical tuple"):
        replace(valid_report, rows=list(valid_report.rows))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        replace(
            valid_report,
            reason_code_counts=tuple(reversed(valid_report.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_code_counts must be a canonical tuple"):
        replace(
            valid_report,
            reason_code_counts=list(valid_report.reason_code_counts),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="reason_codes must be a canonical tuple"):
        replace(valid_report, reason_codes=list(valid_report.reason_codes))  # type: ignore[arg-type]
    mismatched_count = replace(
        valid_report.reason_code_counts[0],
        count=d("2.000000"),
    )
    with pytest.raises(ValueError, match="reason_code_counts must match reason_codes"):
        replace(
            valid_report,
            reason_code_counts=(mismatched_count, *valid_report.reason_code_counts[1:]),
        )
    with pytest.raises(ValueError, match="reset_status must match row metrics"):
        replace(valid_report.rows[0], reset_status="pass")


def test_payload_revalidates_public_dataclasses_and_rejects_non_utc_payload_time() -> None:
    module = api()
    report = digest(observation("payload-source"))

    object.__setattr__(
        report,
        "generated_at",
        GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        module.market_research_crypto_open_interest_leverage_reset_digest_payload(
            report,
        )

    fresh_report = digest(observation("nested-payload-source"))
    object.__setattr__(fresh_report.rows[0], "reset_status", "pass")
    with pytest.raises(ValueError, match="reset_status must match row metrics"):
        module.market_research_crypto_open_interest_leverage_reset_digest_payload(
            fresh_report,
        )


def test_hard_flags_frozen_dataclasses_and_decimal_public_numerics_are_enforced() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.CryptoOpenInterestLeverageResetReasonCodeCount(
            reason_code="crypto_open_interest_leverage_reset_watch_present",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
            readonly=False,
        )
    with pytest.raises(ValueError, match="count must be positive"):
        module.CryptoOpenInterestLeverageResetReasonCodeCount(
            reason_code="crypto_open_interest_leverage_reset_watch_present",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
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
                or field.name.endswith("_seconds")
                or field.name.endswith("_8h")
            ):
                assert type(field_value) is Decimal, field.name


def test_non_default_thresholds_change_screening_status_without_mutating_inputs() -> None:
    source = observation(
        "threshold-source",
        current_open_interest_usd=d("930000000.000000"),
        previous_open_interest_usd=d("1000000000.000000"),
        current_estimated_leverage_ratio=d("4.400000"),
        previous_estimated_leverage_ratio=d("5.000000"),
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
            blocked_open_interest_drop_ratio=d("0.150000"),
            watch_leverage_drop_ratio=d("0.150000"),
            blocked_leverage_drop_ratio=d("0.300000"),
        ),
    )
    tight_report = digest(
        source,
        cfg=config(
            watch_open_interest_drop_ratio=d("0.030000"),
            blocked_open_interest_drop_ratio=d("0.060000"),
            watch_leverage_drop_ratio=d("0.050000"),
            blocked_leverage_drop_ratio=d("0.100000"),
        ),
    )

    assert default_report.rows[0].reset_status == "watch"
    assert loose_report.rows[0].reset_status == "pass"
    assert tight_report.rows[0].reset_status == "blocked"
    assert source.current_open_interest_usd == d("930000000.000000")

    with pytest.raises(ValueError, match="blocked_open_interest_drop_ratio"):
        config(blocked_open_interest_drop_ratio=d("0.040000"))
    with pytest.raises(ValueError, match="watch_open_interest_drop_ratio"):
        config(watch_open_interest_drop_ratio=0.050000)  # type: ignore[arg-type]


def test_module_scope_is_pure_report_only_without_durable_or_mutating_surfaces() -> None:
    source = inspect.getsource(api()).lower()

    for forbidden in (
        "asdict(",
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
        "market_slug",
    ):
        assert forbidden not in source
