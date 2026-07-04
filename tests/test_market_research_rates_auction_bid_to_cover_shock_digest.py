from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
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
        "polymarket_alpha_lab."
        "market_research_rates_auction_bid_to_cover_shock_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "market-research-rates-auction-bid-to-cover-shock-digest-v0"
        ),
        "watch_bid_to_cover_drop_ratio": d("0.080000"),
        "blocked_bid_to_cover_drop_ratio": d("0.180000"),
        "watch_tail_bps": d("2.000000"),
        "blocked_tail_bps": d("5.000000"),
        "watch_shock_score": d("0.350000"),
        "blocked_shock_score": d("0.650000"),
        "max_source_age_seconds": d("900.000000"),
        "stale_confidence_cap": d("0.300000"),
        "watch_confidence_cap": d("0.550000"),
        "blocked_confidence_cap": d("0.250000"),
    }
    values.update(overrides)
    return module.RatesAuctionBidToCoverShockDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "treasury-10y-auction-demand-shock",
    auction_id: str = "treasury-10y-note-2026-07",
    security_tenor: str = "10y",
    reported_bid_to_cover: Decimal = d("2.500000"),
    baseline_bid_to_cover: Decimal = d("2.800000"),
    stop_out_tail_bps: Decimal = d("2.500000"),
    dealer_take_down_ratio: Decimal = d("0.300000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    base_confidence: Decimal = d("0.820000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.RatesAuctionBidToCoverObservation(
        source_id=source_id,
        market_slug=market_slug,
        auction_id=auction_id,
        security_tenor=security_tenor,
        reported_bid_to_cover=reported_bid_to_cover,
        baseline_bid_to_cover=baseline_bid_to_cover,
        stop_out_tail_bps=stop_out_tail_bps,
        dealer_take_down_ratio=dealer_take_down_ratio,
        observed_at=observed_at,
        base_confidence=base_confidence,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    inputs: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    digest_config: Any | None = None,
) -> Any:
    module = api()
    return module.build_market_research_rates_auction_bid_to_cover_shock_digest(
        inputs,
        config=digest_config if digest_config is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_or_decimal_payload(value: object) -> None:
    if isinstance(value, (float, Decimal)):
        pytest.fail("public payload must not contain float or Decimal numerics")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_float_or_decimal_payload(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_float_or_decimal_payload(child)


def test_high_risk_auction_bid_to_cover_shock_digest_screens_probability_events() -> None:
    report = digest(
        (
            observation(
                "beta-watch",
                market_slug="treasury-5y-auction-demand-watch",
                auction_id="treasury-5y-note-2026-07",
                security_tenor="5y",
                reported_bid_to_cover=d("2.500000"),
                baseline_bid_to_cover=d("2.800000"),
                stop_out_tail_bps=d("2.500000"),
                dealer_take_down_ratio=d("0.300000"),
                upstream_reason_codes=("auction_calendar_watch",),
            ),
            observation(
                "alpha-calm",
                market_slug="treasury-2y-auction-demand-calm",
                auction_id="treasury-2y-note-2026-07",
                security_tenor="2y",
                reported_bid_to_cover=d("2.900000"),
                baseline_bid_to_cover=d("2.800000"),
                stop_out_tail_bps=d("0.500000"),
                dealer_take_down_ratio=d("0.180000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
            observation(
                "zeta-blocked",
                market_slug="treasury-10y-auction-demand-blocked",
                auction_id="treasury-10y-note-2026-07",
                security_tenor="10y",
                reported_bid_to_cover=d("2.100000"),
                baseline_bid_to_cover=d("2.800000"),
                stop_out_tail_bps=d("6.000000"),
                dealer_take_down_ratio=d("0.450000"),
                observed_at=GENERATED_AT - timedelta(seconds=1200),
                upstream_reason_codes=("primary_dealer_watch", "bid_to_cover_panel"),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-rates-auction-bid-to-cover-shock-digest-v0"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_shock_count == d("1.000000")
    assert report.watch_shock_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.tail_stress_count == d("2.000000")
    assert report.dealer_take_down_stress_count == d("1.000000")
    assert report.max_bid_to_cover_drop_ratio == d("0.250000")
    assert report.max_shock_score == d("0.890000")
    assert report.average_shock_score == d("0.468548")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_rates_auction_bid_to_cover_shock_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.source_id, row.shock_status, row.shock_score)
        for row in report.rows
    ] == [
        ("zeta-blocked", "blocked", d("0.890000")),
        ("beta-watch", "watch", d("0.458810")),
        ("alpha-calm", "pass", d("0.056833")),
    ]

    blocked, watch, passed = report.rows
    assert blocked.source_age_seconds == d("1200.000000")
    assert blocked.bid_to_cover_gap == d("0.700000")
    assert blocked.bid_to_cover_drop_ratio == d("0.250000")
    assert blocked.confidence_cap == d("0.250000")
    assert blocked.capped_confidence == d("0.250000")
    assert blocked.reason_codes == (
        "bid_to_cover_panel",
        "primary_dealer_watch",
        "rates_auction_bid_to_cover_demand_weaker",
        "rates_auction_bid_to_cover_drop_blocked",
        "rates_auction_bid_to_cover_shock_blocked",
        "rates_auction_bid_to_cover_source_stale",
        "rates_auction_dealer_takedown_high",
        "rates_auction_tail_blocked",
    )
    assert watch.confidence_cap == d("0.550000")
    assert watch.capped_confidence == d("0.550000")
    assert watch.reason_codes == (
        "auction_calendar_watch",
        "rates_auction_bid_to_cover_demand_weaker",
        "rates_auction_bid_to_cover_drop_watch",
        "rates_auction_bid_to_cover_shock_watch",
        "rates_auction_bid_to_cover_source_fresh",
        "rates_auction_tail_watch",
    )
    assert passed.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert passed.bid_to_cover_gap == d("-0.100000")
    assert passed.bid_to_cover_drop_ratio == d("0.000000")
    assert passed.reason_codes == (
        "rates_auction_bid_to_cover_demand_stronger",
        "rates_auction_bid_to_cover_shock_calm",
        "rates_auction_bid_to_cover_source_fresh",
    )
    assert report.reason_codes == (
        "auction_calendar_watch",
        "bid_to_cover_panel",
        "primary_dealer_watch",
        "rates_auction_bid_to_cover_demand_stronger",
        "rates_auction_bid_to_cover_demand_weaker",
        "rates_auction_bid_to_cover_drop_blocked",
        "rates_auction_bid_to_cover_drop_watch",
        "rates_auction_bid_to_cover_shock_blocked",
        "rates_auction_bid_to_cover_shock_calm",
        "rates_auction_bid_to_cover_shock_watch",
        "rates_auction_bid_to_cover_source_fresh",
        "rates_auction_bid_to_cover_source_stale",
        "rates_auction_dealer_takedown_high",
        "rates_auction_tail_blocked",
        "rates_auction_tail_watch",
    )
    weaker = next(
        value
        for value in report.reason_code_counts
        if value.reason_code == "rates_auction_bid_to_cover_demand_weaker"
    )
    assert weaker.count == d("2.000000")
    assert weaker.row_ratio == d("0.666667")


def test_empty_digest_and_payload_are_report_only_readonly_decimal_stringed() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_rates_auction_bid_to_cover_shock_digest_payload(
        report,
    )
    json.dumps(payload, sort_keys=True)

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_shock_count == d("0.000000")
    assert report.watch_shock_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.max_bid_to_cover_drop_ratio == d("0.000000")
    assert report.max_shock_score == d("0.000000")
    assert report.average_shock_score == d("0.000000")
    assert report.digest_status == "blocked"
    assert report.reason_codes == ("rates_auction_bid_to_cover_digest_empty",)
    assert report.reason_code_counts == (
        module.RatesAuctionBidToCoverShockReasonCodeCount(
            reason_code="rates_auction_bid_to_cover_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["reason_code_counts"][0]["row_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_decimal_payload(payload)


def test_deterministic_sorting_reason_codes_and_payload_for_permuted_inputs() -> None:
    module = api()
    inputs = (
        observation("gamma", market_slug="treasury-7y-auction-demand-watch"),
        observation("alpha", market_slug="treasury-3y-auction-demand-watch"),
        observation(
            "beta",
            market_slug="treasury-5y-auction-demand-watch",
            upstream_reason_codes=(
                "rates_auction_tail_watch",
                "auction_calendar_watch",
                "auction_calendar_watch",
            ),
        ),
    )

    first = digest(inputs)
    second = digest(tuple(reversed(inputs)))
    first_payload = module.market_research_rates_auction_bid_to_cover_shock_digest_payload(
        first,
    )
    second_payload = module.market_research_rates_auction_bid_to_cover_shock_digest_payload(
        second,
    )

    assert [row.source_id for row in first.rows] == ["alpha", "beta", "gamma"]
    assert [row.source_id for row in second.rows] == ["alpha", "beta", "gamma"]
    assert first.reason_codes == tuple(sorted(first.reason_codes))
    assert first.rows[1].reason_codes == (
        "auction_calendar_watch",
        "rates_auction_bid_to_cover_demand_weaker",
        "rates_auction_bid_to_cover_drop_watch",
        "rates_auction_bid_to_cover_shock_watch",
        "rates_auction_bid_to_cover_source_fresh",
        "rates_auction_tail_watch",
    )
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_rejects_bad_public_types_datetimes_duplicates_future_rows_and_frozen_changes() -> None:
    module = api()

    with pytest.raises(ValueError, match="reported_bid_to_cover"):
        observation(reported_bid_to_cover=_DecimalSubclass("2.500000"))

    with pytest.raises(ValueError, match="reported_bid_to_cover"):
        observation(reported_bid_to_cover=2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="dealer_take_down_ratio"):
        observation(dealer_take_down_ratio=d("1.100000"))

    with pytest.raises(ValueError, match="watch_bid_to_cover_drop_ratio"):
        config(watch_bid_to_cover_drop_ratio=Decimal("0.200000"))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="duplicate source_id"):
        digest((observation("dupe"), observation("dupe")))

    report = digest((observation(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.RatesAuctionBidToCoverShockDigestConfig,
        module.RatesAuctionBidToCoverObservation,
        module.RatesAuctionBidToCoverShockDigestRow,
        module.RatesAuctionBidToCoverShockReasonCodeCount,
        module.RatesAuctionBidToCoverShockDigestReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type


def test_hard_flags_are_true_on_all_public_objects_and_cannot_be_downgraded() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)

    report = digest((observation(),))
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    for value in (config(), observation(), row, reason_count, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(reason_count, report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)

    with pytest.raises(ValueError, match="report"):
        module.market_research_rates_auction_bid_to_cover_shock_digest_payload(
            {"paper_only": True, "report_only": True, "readonly": True},
        )


def test_non_default_thresholds_reclassify_same_bid_to_cover_observation() -> None:
    calm_input = observation(
        "calm-under-defaults",
        reported_bid_to_cover=d("2.660000"),
        baseline_bid_to_cover=d("2.800000"),
        stop_out_tail_bps=d("1.000000"),
        dealer_take_down_ratio=d("0.200000"),
    )
    default_report = digest((calm_input,))
    stricter_report = digest(
        (calm_input,),
        digest_config=config(
            watch_bid_to_cover_drop_ratio=d("0.040000"),
            blocked_bid_to_cover_drop_ratio=d("0.120000"),
            watch_tail_bps=d("1.500000"),
            blocked_tail_bps=d("4.000000"),
            watch_shock_score=d("0.300000"),
            blocked_shock_score=d("0.600000"),
        ),
    )

    assert default_report.rows[0].bid_to_cover_drop_ratio == d("0.050000")
    assert default_report.rows[0].shock_status == "pass"
    assert default_report.digest_status == "pass"
    assert stricter_report.rows[0].shock_status == "watch"
    assert stricter_report.digest_status == "watch"
    assert "rates_auction_bid_to_cover_drop_watch" in stricter_report.rows[0].reason_codes


def test_module_scope_is_pure_in_memory_without_live_or_durable_surfaces() -> None:
    module = api()
    source = inspect.getsource(module).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "open(",
        "path(",
        "connect(",
        "cursor(",
        "execute(",
        "web3",
        "wallet",
        "private_key",
        "place_order",
        "cancel_order",
        "replace_order",
        "auth",
        "secret",
        "database",
        "network",
        "exchange",
    ):
        assert forbidden not in source

    tree = ast.parse(
        Path(
            "src/polymarket_alpha_lab/"
            "market_research_rates_auction_bid_to_cover_shock_digest.py",
        ).read_text(),
    )
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    report = digest((observation(),))
    assert is_dataclass(report)
