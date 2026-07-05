from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


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


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_rates_auction_tail_pressure_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "market-research-rates-auction-tail-pressure-digest-v0"
        ),
        "watch_tail_bps": d("1.000000"),
        "blocked_tail_bps": d("3.000000"),
        "watch_pressure_score": d("0.350000"),
        "blocked_pressure_score": d("0.650000"),
        "min_bid_to_cover_ratio": d("2.400000"),
        "high_primary_dealer_award_share": d("0.250000"),
        "min_indirect_bidder_award_share": d("0.550000"),
        "max_source_age_seconds": d("600.000000"),
        "blocked_confidence_cap": d("0.350000"),
        "watch_confidence_cap": d("0.650000"),
        "stale_confidence_cap": d("0.250000"),
    }
    values.update(overrides)
    return module.RatesAuctionTailPressureDigestConfig(**values)


def observation(
    source_id: str = "auction-source-alpha",
    *,
    market_slug: str = "treasury-auction-tail-pressure",
    auction_id: str = "2026-07-05-10y",
    tenor_bucket: str = "10y",
    observed_at: datetime = GENERATED_AT - timedelta(seconds=60),
    when_issued_yield_pct: Decimal = d("4.260000"),
    stop_yield_pct: Decimal = d("4.300000"),
    bid_to_cover_ratio: Decimal = d("2.000000"),
    primary_dealer_award_share: Decimal = d("0.320000"),
    indirect_bidder_award_share: Decimal = d("0.480000"),
    base_confidence: Decimal = d("0.900000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.RatesAuctionTailPressureObservation(
        source_id=source_id,
        market_slug=market_slug,
        auction_id=auction_id,
        tenor_bucket=tenor_bucket,
        observed_at=observed_at,
        when_issued_yield_pct=when_issued_yield_pct,
        stop_yield_pct=stop_yield_pct,
        bid_to_cover_ratio=bid_to_cover_ratio,
        primary_dealer_award_share=primary_dealer_award_share,
        indirect_bidder_award_share=indirect_bidder_award_share,
        base_confidence=base_confidence,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    inputs: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    if cfg is None:
        cfg = config()
    return module.build_market_research_rates_auction_tail_pressure_digest(
        inputs,
        config=cfg,
        generated_at=generated_at,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        items: list[object] = []
        for key, item in value.items():
            items.append(key)
            items.extend(walk_payload_values(item))
        return tuple(items)
    if isinstance(value, list):
        items = []
        for item in value:
            items.extend(walk_payload_values(item))
        return tuple(items)
    return (value,)


def test_reduces_treasury_auction_tail_pressure_deterministically() -> None:
    report = digest(
        (
            observation(
                "pass-source",
                auction_id="auction-pass",
                tenor_bucket="2y",
                when_issued_yield_pct=d("4.260000"),
                stop_yield_pct=d("4.245000"),
                bid_to_cover_ratio=d("2.800000"),
                primary_dealer_award_share=d("0.180000"),
                indirect_bidder_award_share=d("0.650000"),
                observed_at=GENERATED_AT - timedelta(seconds=120),
            ),
            observation(
                "watch-source",
                auction_id="auction-watch",
                tenor_bucket="5y",
                when_issued_yield_pct=d("4.260000"),
                stop_yield_pct=d("4.275000"),
                bid_to_cover_ratio=d("2.350000"),
                primary_dealer_award_share=d("0.270000"),
                indirect_bidder_award_share=d("0.540000"),
                observed_at=GENERATED_AT - timedelta(seconds=900),
            ),
            observation(
                "blocked-source",
                auction_id="auction-blocked",
                tenor_bucket="10y",
                observed_at=datetime(
                    2026,
                    7,
                    5,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                upstream_reason_codes=("treasury_auction_release",),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "market-research-rates-auction-tail-pressure-digest-v0"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_pressure_count == d("1.000000")
    assert report.watch_pressure_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.tail_count == d("2.000000")
    assert report.stop_through_count == d("1.000000")
    assert report.weak_bid_to_cover_count == d("2.000000")
    assert report.dealer_take_down_count == d("2.000000")
    assert report.indirect_bid_gap_count == d("2.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.max_tail_pressure_score == d("0.566424")
    assert report.average_tail_pressure_score == d("0.275773")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_rates_auction_tail_pressure_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (
            row.source_id,
            row.pressure_status,
            row.auction_tail_bps,
            row.tail_pressure_score,
        )
        for row in report.rows
    ] == [
        ("blocked-source", "blocked", d("4.000000"), d("0.566424")),
        ("watch-source", "watch", d("1.500000"), d("0.260894")),
        ("pass-source", "pass", d("-1.500000"), d("0.000000")),
    ]

    blocked = report.rows[0]
    assert blocked.observed_at == datetime(2026, 7, 5, 11, 59, tzinfo=UTC)
    assert blocked.source_age_seconds == d("60.000000")
    assert blocked.stop_through_bps == ZERO
    assert blocked.bid_to_cover_shortfall == d("0.400000")
    assert blocked.indirect_bidder_award_gap == d("0.070000")
    assert blocked.primary_dealer_award_excess == d("0.070000")
    assert blocked.confidence_cap == d("0.350000")
    assert blocked.capped_confidence == d("0.350000")
    assert blocked.reason_codes == (
        "auction_tail_pressure_blocked",
        "auction_tail_pressure_dealer_take_down",
        "auction_tail_pressure_indirect_bid_gap",
        "auction_tail_pressure_source_fresh",
        "auction_tail_pressure_tail_present",
        "auction_tail_pressure_weak_bid_to_cover",
        "treasury_auction_release",
    )

    watch = report.rows[1]
    assert watch.source_age_seconds == d("900.000000")
    assert watch.confidence_cap == d("0.250000")
    assert watch.capped_confidence == d("0.250000")
    assert watch.reason_codes == (
        "auction_tail_pressure_dealer_take_down",
        "auction_tail_pressure_indirect_bid_gap",
        "auction_tail_pressure_source_stale",
        "auction_tail_pressure_tail_present",
        "auction_tail_pressure_watch",
        "auction_tail_pressure_weak_bid_to_cover",
    )

    passed = report.rows[2]
    assert passed.stop_through_bps == d("1.500000")
    assert passed.reason_codes == (
        "auction_tail_pressure_clear",
        "auction_tail_pressure_source_fresh",
        "auction_tail_pressure_stop_through_present",
    )

    assert report.reason_codes == (
        "auction_tail_pressure_blocked",
        "auction_tail_pressure_clear",
        "auction_tail_pressure_dealer_take_down",
        "auction_tail_pressure_indirect_bid_gap",
        "auction_tail_pressure_source_fresh",
        "auction_tail_pressure_source_stale",
        "auction_tail_pressure_stop_through_present",
        "auction_tail_pressure_tail_present",
        "auction_tail_pressure_watch",
        "auction_tail_pressure_weak_bid_to_cover",
        "treasury_auction_release",
    )
    assert tuple(item.reason_code for item in report.reason_code_counts[:5]) == (
        "auction_tail_pressure_dealer_take_down",
        "auction_tail_pressure_indirect_bid_gap",
        "auction_tail_pressure_source_fresh",
        "auction_tail_pressure_tail_present",
        "auction_tail_pressure_weak_bid_to_cover",
    )
    assert tuple(item.count for item in report.reason_code_counts[:5]) == (
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
    )


def test_reversed_inputs_build_identical_report_and_manual_public_sorting_is_rejected() -> None:
    first = observation("tail-b", auction_id="tail-b")
    second = observation(
        "tail-a",
        auction_id="tail-a",
        stop_yield_pct=d("4.280000"),
    )
    third = observation(
        "clear-a",
        auction_id="clear-a",
        stop_yield_pct=d("4.250000"),
        bid_to_cover_ratio=d("2.700000"),
        primary_dealer_award_share=d("0.200000"),
        indirect_bidder_award_share=d("0.650000"),
    )

    forward = digest((first, second, third))
    reverse = digest((third, second, first))

    assert forward == reverse
    assert tuple(row.auction_id for row in forward.rows) == (
        "tail-b",
        "tail-a",
        "clear-a",
    )

    with pytest.raises(ValueError, match="rows.*sorted"):
        replace(forward, rows=tuple(reversed(forward.rows)))

    with pytest.raises(ValueError, match="reason_code_counts.*sorted"):
        replace(
            forward,
            reason_code_counts=tuple(reversed(forward.reason_code_counts)),
        )

    with pytest.raises(ValueError, match="upstream_reason_codes.*canonical"):
        observation(upstream_reason_codes=("z_reason", "a_reason"))


def test_empty_input_blocks_with_decimal_zeroes_and_synthetic_reason_count() -> None:
    module = api()
    report = digest(())

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_rates_auction_tail_pressure_digest"
    )
    assert report.input_count == ZERO
    assert report.row_count == ZERO
    assert report.blocked_pressure_count == ZERO
    assert report.watch_pressure_count == ZERO
    assert report.pass_count == ZERO
    assert report.max_tail_pressure_score == ZERO
    assert report.average_tail_pressure_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("auction_tail_pressure_digest_empty",)
    assert report.reason_code_counts == (
        module.RatesAuctionTailPressureReasonCodeCount(
            reason_code="auction_tail_pressure_digest_empty",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )


def test_builder_uses_default_config_only_when_config_is_none() -> None:
    module = api()

    report = module.build_market_research_rates_auction_tail_pressure_digest(
        (observation("default-config-source"),),
        config=None,
        generated_at=GENERATED_AT,
    )

    assert report.config_version == (
        "market-research-rates-auction-tail-pressure-digest-v0"
    )


def test_validation_rejects_bad_types_false_flags_dates_duplicates_and_zero_counts() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                "market-research-rates-auction-tail-pressure-digest-v0",
            ),
        )
    with pytest.raises(ValueError, match="watch_tail_bps"):
        config(watch_tail_bps=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_tail_bps"):
        config(watch_tail_bps=d("4.000000"))
    with pytest.raises(ValueError, match="when_issued_yield_pct"):
        observation(when_issued_yield_pct=_DecimalSubclass("4.260000"))
    with pytest.raises(ValueError, match="bid_to_cover_ratio"):
        observation(bid_to_cover_ratio=2.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="primary_dealer_award_share"):
        observation(primary_dealer_award_share=d("1.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DateTimeSubclass(2026, 7, 5, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 5, 12, 0))
    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 5, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="duplicate source_id"):
        digest(
            (
                observation("duplicate-source", auction_id="auction-one"),
                observation("duplicate-source", auction_id="auction-two"),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest((observation("readonly-source"),)).rows[0], readonly=False)
    with pytest.raises(ValueError, match="count.*positive"):
        module.RatesAuctionTailPressureReasonCodeCount(
            reason_code="manual_zero_count",
            count=ZERO,
            row_ratio=ZERO,
        )

    row = digest((observation("frozen-source"),)).rows[0]
    with pytest.raises(FrozenInstanceError):
        row.source_id = "changed"  # type: ignore[misc]


def test_public_dataclasses_reject_subclassing_and_expose_decimal_only_numerics() -> None:
    module = api()
    report = digest((observation("numeric-source"),))

    public_classes = (
        module.RatesAuctionTailPressureDigestConfig,
        module.RatesAuctionTailPressureObservation,
        module.RatesAuctionTailPressureDigestRow,
        module.RatesAuctionTailPressureReasonCodeCount,
        module.RatesAuctionTailPressureDigestReport,
    )
    for public_class in public_classes:
        assert public_class.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_class.__name__}Child", (public_class,), {})

    public_records = (
        config(),
        observation("field-source"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    for record in public_records:
        for field in fields(record):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            value = getattr(record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert "float" not in str(field.type).lower()
            assert "int" not in str(field.type).lower()


def test_payload_uses_six_decimal_strings_utc_datetimes_and_no_raw_numerics() -> None:
    module = api()
    report = digest((observation("payload-source"),))
    payload = module.market_research_rates_auction_tail_pressure_digest_payload(report)

    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-05T12:00:00+00:00"
    assert payload["input_count"] == "1.000000"
    assert payload["max_tail_pressure_score"] == "0.566424"
    assert payload["rows"][0]["observed_at"] == "2026-07-05T11:59:00+00:00"
    assert payload["rows"][0]["auction_tail_bps"] == "4.000000"
    assert payload["rows"][0]["tail_pressure_score"] == "0.566424"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(payload))
    assert not any(isinstance(value, float) for value in walk_payload_values(payload))
    assert not any(
        type(value) is int and not isinstance(value, bool)
        for value in walk_payload_values(payload)
    )


def test_payload_revalidates_nested_public_dataclasses_before_serialization() -> None:
    module = api()

    false_flag_report = digest((observation("payload-false-flag"),))
    object.__setattr__(false_flag_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.market_research_rates_auction_tail_pressure_digest_payload(
            false_flag_report,
        )

    row_decimal_report = digest((observation("payload-row-decimal"),))
    object.__setattr__(row_decimal_report.rows[0], "auction_tail_bps", d("4.0"))
    with pytest.raises(ValueError, match="auction_tail_bps.*six-decimal"):
        module.market_research_rates_auction_tail_pressure_digest_payload(
            row_decimal_report,
        )

    count_decimal_report = digest((observation("payload-count-decimal"),))
    object.__setattr__(
        count_decimal_report.reason_code_counts[0],
        "row_ratio",
        d("1"),
    )
    with pytest.raises(ValueError, match="row_ratio.*six-decimal"):
        module.market_research_rates_auction_tail_pressure_digest_payload(
            count_decimal_report,
        )


def test_module_scope_is_pure_and_unwired_to_io_storage_auth_or_trading_surfaces() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_RATES_AUCTION_TAIL_PRESSURE_DIGEST_CONFIG_VERSION",
        "RatesAuctionTailPressureDigestConfig",
        "RatesAuctionTailPressureObservation",
        "RatesAuctionTailPressureDigestRow",
        "RatesAuctionTailPressureReasonCodeCount",
        "RatesAuctionTailPressureDigestReport",
        "build_market_research_rates_auction_tail_pressure_digest",
        "market_research_rates_auction_tail_pressure_digest_payload",
    )

    source = inspect.getsource(module)
    lowered_source = source.lower()
    tree = ast.parse(source)

    forbidden_import_roots = {
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "connect",
        "cursor",
        "execute",
        "open",
        "send",
    }
    forbidden_fragments = (
        "api_key",
        "auth",
        "cancel_order",
        "exchange",
        "live_trading",
        "place_order",
        "private_key",
        "replace_order",
        "submit_order",
        "wallet",
    )

    assert not any(fragment in lowered_source for fragment in forbidden_fragments)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_call_names
