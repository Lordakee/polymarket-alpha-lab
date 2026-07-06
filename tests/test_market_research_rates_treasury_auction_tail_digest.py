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
        "market_research_rates_treasury_auction_tail_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "market-research-rates-treasury-auction-tail-digest-v0"
        ),
        "watch_tail_bps": d("1.500000"),
        "blocked_tail_bps": d("4.000000"),
        "watch_bid_to_cover_shortfall_ratio": d("0.050000"),
        "blocked_bid_to_cover_shortfall_ratio": d("0.150000"),
        "low_indirect_bidder_pct": d("55.000000"),
        "watch_tail_pressure_score": d("0.350000"),
        "blocked_tail_pressure_score": d("0.650000"),
        "max_source_age_seconds": d("900.000000"),
        "stale_confidence_cap": d("0.300000"),
        "watch_confidence_cap": d("0.600000"),
        "blocked_confidence_cap": d("0.250000"),
    }
    values.update(overrides)
    return module.RatesTreasuryAuctionTailDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    auction_id: str = "treasury-10y-note-2026-07",
    security_tenor: str = "10y",
    auctioned_at: datetime = GENERATED_AT - timedelta(minutes=5),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    stop_out_tail_bps: Decimal = d("2.000000"),
    reported_bid_to_cover: Decimal = d("2.500000"),
    expected_bid_to_cover: Decimal = d("2.800000"),
    indirect_bidder_pct: Decimal = d("52.000000"),
    base_confidence: Decimal = d("0.820000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.RatesTreasuryAuctionTailObservation(
        source_id=source_id,
        auction_id=auction_id,
        security_tenor=security_tenor,
        auctioned_at=auctioned_at,
        observed_at=observed_at,
        stop_out_tail_bps=stop_out_tail_bps,
        reported_bid_to_cover=reported_bid_to_cover,
        expected_bid_to_cover=expected_bid_to_cover,
        indirect_bidder_pct=indirect_bidder_pct,
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
    return module.build_market_research_rates_treasury_auction_tail_digest(
        inputs,
        config=digest_config if digest_config is not None else config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_payload_values(value: object) -> None:
    if type(value) in (float, int) or isinstance(value, Decimal):
        pytest.fail(f"public payload numeric must be a string: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_numeric_payload_values(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_public_numeric_payload_values(child)


def test_treasury_auction_tail_digest_reduces_inputs_deterministically() -> None:
    report = digest(
        (
            observation(
                "beta-watch",
                auction_id="treasury-5y-note-2026-07",
                security_tenor="5y",
                upstream_reason_codes=("public_treasury_result_panel",),
            ),
            observation(
                "alpha-calm",
                auction_id="treasury-2y-note-2026-07",
                security_tenor="2y",
                auctioned_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    55,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                stop_out_tail_bps=d("0.500000"),
                reported_bid_to_cover=d("2.900000"),
                expected_bid_to_cover=d("2.800000"),
                indirect_bidder_pct=d("65.000000"),
            ),
            observation(
                "zeta-blocked",
                auction_id="treasury-10y-note-2026-07",
                security_tenor="10y",
                observed_at=GENERATED_AT - timedelta(seconds=1200),
                stop_out_tail_bps=d("5.000000"),
                reported_bid_to_cover=d("2.100000"),
                expected_bid_to_cover=d("2.800000"),
                indirect_bidder_pct=d("45.000000"),
                base_confidence=d("0.900000"),
                upstream_reason_codes=("auction_calendar_watch",),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-rates-treasury-auction-tail-digest-v0"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_tail_count == d("1.000000")
    assert report.watch_tail_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.weak_bid_to_cover_count == d("2.000000")
    assert report.low_indirect_bidder_count == d("2.000000")
    assert report.positive_tail_count == d("2.000000")
    assert report.max_tail_bps == d("5.000000")
    assert report.max_bid_to_cover_shortfall_ratio == d("0.250000")
    assert report.average_tail_pressure_score == d("0.377662")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_rates_treasury_auction_tail_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert type(report.rows) is tuple
    assert type(report.reason_codes) is tuple
    assert type(report.reason_code_counts) is tuple
    assert all(type(row.reason_codes) is tuple for row in report.rows)

    assert [
        (row.source_id, row.tail_status, row.tail_pressure_score)
        for row in report.rows
    ] == [
        ("zeta-blocked", "blocked", d("0.753030")),
        ("beta-watch", "watch", d("0.338290")),
        ("alpha-calm", "pass", d("0.041667")),
    ]

    blocked, watch, passed = report.rows
    assert blocked.source_age_seconds == d("1200.000000")
    assert blocked.bid_to_cover_gap == d("0.700000")
    assert blocked.bid_to_cover_shortfall_ratio == d("0.250000")
    assert blocked.confidence_cap == d("0.250000")
    assert blocked.capped_confidence == d("0.250000")
    assert blocked.reason_codes == (
        "auction_calendar_watch",
        "rates_treasury_auction_bid_to_cover_shortfall_blocked",
        "rates_treasury_auction_indirect_bidder_share_low",
        "rates_treasury_auction_source_stale",
        "rates_treasury_auction_stop_out_tail_blocked",
        "rates_treasury_auction_tail_blocked",
        "rates_treasury_auction_tail_demand_weaker",
    )
    assert watch.confidence_cap == d("0.600000")
    assert watch.capped_confidence == d("0.600000")
    assert watch.reason_codes == (
        "public_treasury_result_panel",
        "rates_treasury_auction_bid_to_cover_shortfall_watch",
        "rates_treasury_auction_indirect_bidder_share_low",
        "rates_treasury_auction_source_fresh",
        "rates_treasury_auction_stop_out_tail_watch",
        "rates_treasury_auction_tail_demand_weaker",
        "rates_treasury_auction_tail_watch",
    )
    assert passed.auctioned_at == datetime(2026, 7, 4, 11, 55, tzinfo=UTC)
    assert passed.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert passed.bid_to_cover_gap == d("-0.100000")
    assert passed.bid_to_cover_shortfall_ratio == d("0.000000")
    assert passed.reason_codes == (
        "rates_treasury_auction_source_fresh",
        "rates_treasury_auction_tail_calm",
        "rates_treasury_auction_tail_demand_stronger",
    )

    assert report.reason_codes == tuple(sorted(report.reason_codes))
    total_row_reasons = sum(len(row.reason_codes) for row in report.rows)
    total_reason_count = sum(int(count.count) for count in report.reason_code_counts)
    assert total_reason_count == total_row_reasons
    low_share = next(
        value
        for value in report.reason_code_counts
        if value.reason_code == "rates_treasury_auction_indirect_bidder_share_low"
    )
    assert low_share.count == d("2.000000")
    assert low_share.row_ratio == d("0.666667")


def test_empty_digest_and_payload_are_report_only_readonly_decimal_stringed() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_rates_treasury_auction_tail_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_tail_count == d("0.000000")
    assert report.watch_tail_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.digest_status == "blocked"
    assert report.reason_codes == ("rates_treasury_auction_tail_digest_empty",)
    assert report.reason_code_counts == (
        module.RatesTreasuryAuctionTailReasonCodeCount(
            reason_code="rates_treasury_auction_tail_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["row_count"] == "0.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_payload_values(payload)
    public_text = repr(payload)
    for hidden_field in (
        "_".join(("market", "slug")),
        "ques" + "tion",
        "_".join(("payload", "json")),
    ):
        assert hidden_field not in public_text


def test_deterministic_sorting_reason_codes_and_payload_for_permuted_inputs() -> None:
    module = api()
    inputs = (
        observation("gamma", auction_id="treasury-7y-note-2026-07"),
        observation(
            "alpha",
            auction_id="treasury-3y-note-2026-07",
            upstream_reason_codes=("auction_calendar_watch",),
        ),
        observation(
            "beta",
            auction_id="treasury-5y-note-2026-07",
            upstream_reason_codes=(
                "public_treasury_result_panel",
                "auction_calendar_watch",
                "auction_calendar_watch",
            ),
        ),
    )

    assert inputs[2].upstream_reason_codes == (
        "auction_calendar_watch",
        "public_treasury_result_panel",
    )
    first = digest(inputs)
    second = digest(tuple(reversed(inputs)))
    first_payload = module.market_research_rates_treasury_auction_tail_digest_payload(
        first,
    )
    second_payload = module.market_research_rates_treasury_auction_tail_digest_payload(
        second,
    )

    assert [row.source_id for row in first.rows] == ["alpha", "beta", "gamma"]
    assert [row.source_id for row in second.rows] == ["alpha", "beta", "gamma"]
    assert first_payload["rows"][0]["auctioned_at"] == "2026-07-04T11:55:00+00:00"
    assert first_payload["rows"][0]["observed_at"] == "2026-07-04T11:58:00+00:00"
    assert first.reason_codes == tuple(sorted(first.reason_codes))
    assert first.rows[1].reason_codes == (
        "auction_calendar_watch",
        "public_treasury_result_panel",
        "rates_treasury_auction_bid_to_cover_shortfall_watch",
        "rates_treasury_auction_indirect_bidder_share_low",
        "rates_treasury_auction_source_fresh",
        "rates_treasury_auction_stop_out_tail_watch",
        "rates_treasury_auction_tail_demand_weaker",
        "rates_treasury_auction_tail_watch",
    )
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )


def test_rejects_bad_public_types_datetimes_duplicates_subclasses_and_tamper() -> None:
    module = api()

    with pytest.raises(ValueError, match="reported_bid_to_cover"):
        observation(reported_bid_to_cover=_DecimalSubclass("2.500000"))

    with pytest.raises(ValueError, match="reported_bid_to_cover"):
        observation(reported_bid_to_cover=2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_confidence"):
        observation(base_confidence=d("1.100000"))

    with pytest.raises(ValueError, match="watch_tail_bps"):
        config(watch_tail_bps=d("5.000000"))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(auctioned_at=datetime(2026, 7, 4, 11, 55))

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="duplicate source_id"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="config must be exactly"):
        digest((observation(),), digest_config={"paper_only": True})

    with pytest.raises(ValueError, match="inputs must be an iterable"):
        digest("not-a-list")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="inputs must be an iterable"):
        module.build_market_research_rates_treasury_auction_tail_digest(
            b"not-a-list",  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )

    report = digest((observation(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    for bad_count in (d("0.000000"), d("0.500000")):
        with pytest.raises(ValueError, match="count"):
            module.RatesTreasuryAuctionTailReasonCodeCount(
                reason_code="rates_treasury_auction_tail_calm",
                count=bad_count,
                row_ratio=d("0.000000"),
            )

    classes = (
        module.RatesTreasuryAuctionTailDigestConfig,
        module.RatesTreasuryAuctionTailObservation,
        module.RatesTreasuryAuctionTailDigestRow,
        module.RatesTreasuryAuctionTailReasonCodeCount,
        module.RatesTreasuryAuctionTailDigestReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type
        with pytest.raises(TypeError, match="subclass"):
            type("BadSubclass", (type_,), {})

    object.__setattr__(report.rows[0], "tail_pressure_score", d("0.000000"))
    with pytest.raises(ValueError, match="tail_pressure_score"):
        module.market_research_rates_treasury_auction_tail_digest_payload(report)

    report_level_tamper = digest((observation("report-level-tamper"),))
    object.__setattr__(report_level_tamper, "row_count", d("99.000000"))
    with pytest.raises(ValueError, match="row_count"):
        module.market_research_rates_treasury_auction_tail_digest_payload(
            report_level_tamper,
        )

    reason_count_tamper = digest((observation("reason-count-tamper"),))
    object.__setattr__(
        reason_count_tamper.reason_code_counts[0],
        "count",
        d("99.000000"),
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.market_research_rates_treasury_auction_tail_digest_payload(
            reason_count_tamper,
        )


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
        module.market_research_rates_treasury_auction_tail_digest_payload(
            {"paper_only": True, "report_only": True, "readonly": True},
        )


def test_non_default_thresholds_reclassify_same_treasury_auction_observation() -> None:
    calm_input = observation(
        "calm-under-defaults",
        stop_out_tail_bps=d("1.000000"),
        reported_bid_to_cover=d("2.690000"),
        expected_bid_to_cover=d("2.800000"),
        indirect_bidder_pct=d("58.000000"),
        base_confidence=d("0.700000"),
    )
    default_report = digest((calm_input,))
    stricter_report = digest(
        (calm_input,),
        digest_config=config(
            watch_tail_bps=d("0.750000"),
            blocked_tail_bps=d("4.000000"),
            watch_bid_to_cover_shortfall_ratio=d("0.030000"),
            blocked_bid_to_cover_shortfall_ratio=d("0.120000"),
            watch_tail_pressure_score=d("0.150000"),
            blocked_tail_pressure_score=d("0.600000"),
        ),
    )

    assert default_report.rows[0].bid_to_cover_shortfall_ratio == d("0.039286")
    assert default_report.rows[0].tail_status == "pass"
    assert default_report.digest_status == "pass"
    assert stricter_report.rows[0].tail_status == "watch"
    assert stricter_report.digest_status == "watch"
    assert "rates_treasury_auction_bid_to_cover_shortfall_watch" in (
        stricter_report.rows[0].reason_codes
    )


def test_confidence_caps_cover_stale_watch_and_fresh_blocked_paths() -> None:
    stale_watch_report = digest(
        (
            observation(
                "stale-watch",
                observed_at=GENERATED_AT - timedelta(seconds=1200),
                stop_out_tail_bps=d("2.000000"),
                reported_bid_to_cover=d("2.500000"),
                expected_bid_to_cover=d("2.800000"),
                indirect_bidder_pct=d("52.000000"),
                base_confidence=d("0.820000"),
            ),
        ),
    )
    stale_watch = stale_watch_report.rows[0]

    assert stale_watch.tail_status == "watch"
    assert stale_watch.source_age_seconds == d("1200.000000")
    assert stale_watch.confidence_cap == d("0.300000")
    assert stale_watch.capped_confidence == d("0.300000")
    assert "rates_treasury_auction_source_stale" in stale_watch.reason_codes

    fresh_blocked_report = digest(
        (
            observation(
                "fresh-blocked",
                observed_at=GENERATED_AT - timedelta(seconds=120),
                stop_out_tail_bps=d("5.000000"),
                reported_bid_to_cover=d("2.100000"),
                expected_bid_to_cover=d("2.800000"),
                indirect_bidder_pct=d("45.000000"),
                base_confidence=d("0.900000"),
            ),
        ),
    )
    fresh_blocked = fresh_blocked_report.rows[0]

    assert fresh_blocked.tail_status == "blocked"
    assert fresh_blocked.source_age_seconds == d("120.000000")
    assert fresh_blocked.confidence_cap == d("0.250000")
    assert fresh_blocked.capped_confidence == d("0.250000")
    assert "rates_treasury_auction_source_fresh" in fresh_blocked.reason_codes


def test_module_scope_is_pure_report_only_without_forbidden_surfaces() -> None:
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
        "wal" + "let",
        "_".join(("private", "key")),
        "_".join(("api", "key")),
        "place_" + "order",
        "cancel_" + "order",
        "replace_" + "order",
        "au" + "th",
        "sec" + "ret",
        "data" + "base",
        "net" + "work",
        "asdict",
        "_".join(("market", "slug")),
        "ques" + "tion",
        "_".join(("payload", "json")),
    ):
        assert forbidden not in source

    tree = ast.parse(
        Path(
            "src/polymarket_alpha_lab/"
            "market_research_rates_treasury_auction_tail_digest.py",
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
