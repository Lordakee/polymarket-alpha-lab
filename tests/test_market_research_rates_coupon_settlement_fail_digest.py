from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 14, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_rates_coupon_settlement_fail_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_rates_coupon_settlement_fail_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    cusip: str = "91282CKQ3",
    tenor_bucket: str = "10y",
    market_slug: str = "treasury-coupon-settlement-fail-stress",
    fail_rate_bps: str | Decimal = "180.000000",
    settlement_age_days: str | Decimal = "1.000000",
    repo_specialness_bps: str | Decimal = "45.000000",
    auction_cycle_proximity_days: str | Decimal = "12.000000",
    deliverable_supply_score: str | Decimal = "0.750000",
    source_freshness_minutes: str | Decimal = "30.000000",
    source_quorum: str | Decimal = "3.000000",
    data_timestamp: datetime = datetime(2026, 7, 4, 13, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("dtcc_public_fail_snapshot",),
):
    module = digest()

    def decimal_value(value: str | Decimal) -> Decimal:
        return value if isinstance(value, Decimal) else d(value)

    return module.RatesCouponSettlementFailObservation(
        source_id=source_id,
        cusip=cusip,
        tenor_bucket=tenor_bucket,
        market_slug=market_slug,
        fail_rate_bps=decimal_value(fail_rate_bps),
        settlement_age_days=decimal_value(settlement_age_days),
        repo_specialness_bps=decimal_value(repo_specialness_bps),
        auction_cycle_proximity_days=decimal_value(auction_cycle_proximity_days),
        deliverable_supply_score=decimal_value(deliverable_supply_score),
        source_freshness_minutes=decimal_value(source_freshness_minutes),
        source_quorum=decimal_value(source_quorum),
        data_timestamp=data_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_rates_coupon_settlement_fail_digest(
        rows,
        config=cfg or module.RatesCouponSettlementFailDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.RatesCouponSettlementFailDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-rates-coupon-settlement-fail-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_rates_coupon_settlement_fail_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.high_fail_rate_count == d("0.000000")
    assert digest_report.aged_fail_count == d("0.000000")
    assert digest_report.repo_specialness_count == d("0.000000")
    assert digest_report.auction_cycle_pressure_count == d("0.000000")
    assert digest_report.thin_deliverable_supply_count == d("0.000000")
    assert digest_report.stale_source_count == d("0.000000")
    assert digest_report.low_source_quorum_count == d("0.000000")
    assert digest_report.max_fail_rate_bps == d("0.000000")
    assert digest_report.max_settlement_age_days == d("0.000000")
    assert digest_report.max_repo_specialness_bps == d("0.000000")
    assert digest_report.average_fail_rate_bps == d("0.000000")
    assert digest_report.settlement_fail_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "rates_coupon_settlement_fail_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.RatesCouponSettlementFailReasonCodeCount(
            reason_code="rates_coupon_settlement_fail_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_settlement_fail_stress_blocks_rates_event_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            cusip="91282CKQ3",
            tenor_bucket="10y",
            market_slug="ten-year-coupon-delivery-stress",
            fail_rate_bps="640.000000",
            settlement_age_days="6.000000",
            repo_specialness_bps="185.000000",
            auction_cycle_proximity_days="2.000000",
            deliverable_supply_score="0.210000",
            source_freshness_minutes="180.000000",
            source_quorum="1.000000",
        ),
        observation(
            "source-watch",
            cusip="91282CLH2",
            tenor_bucket="5y",
            market_slug="five-year-coupon-delivery-watch",
            fail_rate_bps="275.000000",
            settlement_age_days="2.000000",
            repo_specialness_bps="82.000000",
            auction_cycle_proximity_days="4.000000",
            deliverable_supply_score="0.320000",
            data_timestamp=datetime(
                2026,
                7,
                4,
                9,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-pass",
            cusip="91282CMN8",
            tenor_bucket="2y",
            market_slug="two-year-coupon-delivery-inline",
            fail_rate_bps="24.000000",
            settlement_age_days="0.000000",
            repo_specialness_bps="12.000000",
            auction_cycle_proximity_days="18.000000",
            deliverable_supply_score="0.910000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_rates_coupon_settlement_fail_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.high_fail_rate_count == d("1.000000")
    assert digest_report.aged_fail_count == d("1.000000")
    assert digest_report.repo_specialness_count == d("2.000000")
    assert digest_report.auction_cycle_pressure_count == d("2.000000")
    assert digest_report.thin_deliverable_supply_count == d("2.000000")
    assert digest_report.stale_source_count == d("1.000000")
    assert digest_report.low_source_quorum_count == d("1.000000")
    assert digest_report.max_fail_rate_bps == d("640.000000")
    assert digest_report.max_settlement_age_days == d("6.000000")
    assert digest_report.max_repo_specialness_bps == d("185.000000")
    assert digest_report.average_fail_rate_bps == d("313.000000")
    assert digest_report.settlement_fail_risk_score == d("0.500000")
    assert digest_report.reason_codes == (
        "rates_coupon_settlement_fail_aged_fail_present",
        "rates_coupon_settlement_fail_auction_cycle_pressure_present",
        "rates_coupon_settlement_fail_high_fail_rate_present",
        "rates_coupon_settlement_fail_low_source_quorum_present",
        "rates_coupon_settlement_fail_repo_specialness_present",
        "rates_coupon_settlement_fail_stale_source_present",
        "rates_coupon_settlement_fail_thin_deliverable_supply_present",
    )

    blocked, watched, passed = digest_report.rows
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "ten-year-coupon-delivery-stress",
        "five-year-coupon-delivery-watch",
        "two-year-coupon-delivery-inline",
    )
    assert blocked.settlement_fail_status == "blocked"
    assert blocked.risk_score == d("1.000000")
    assert blocked.data_timestamp == datetime(2026, 7, 4, 13, 0, tzinfo=UTC)
    assert blocked.reason_codes == (
        "rates_coupon_settlement_fail_aged_fail",
        "rates_coupon_settlement_fail_auction_cycle_pressure",
        "rates_coupon_settlement_fail_high_fail_rate",
        "rates_coupon_settlement_fail_low_source_quorum",
        "rates_coupon_settlement_fail_repo_specialness",
        "rates_coupon_settlement_fail_stale_source",
        "rates_coupon_settlement_fail_thin_deliverable_supply",
    )
    assert watched.settlement_fail_status == "watch"
    assert watched.data_timestamp == datetime(2026, 7, 4, 13, 30, tzinfo=UTC)
    assert watched.reason_codes == (
        "rates_coupon_settlement_fail_auction_cycle_pressure",
        "rates_coupon_settlement_fail_repo_specialness",
        "rates_coupon_settlement_fail_thin_deliverable_supply",
        "rates_coupon_settlement_fail_watch_age",
        "rates_coupon_settlement_fail_watch_fail_rate",
    )
    assert passed.settlement_fail_status == "pass"
    assert passed.reason_codes == ("rates_coupon_settlement_fail_inline",)


def test_rows_and_reason_counts_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        cusip="91282CZZ9",
        market_slug="zeta-watch",
        fail_rate_bps="280.000000",
        repo_specialness_bps="80.000000",
    )
    second = observation(
        "source-blocked",
        cusip="91282CAA1",
        market_slug="alpha-blocked",
        fail_rate_bps="510.000000",
    )
    third = observation(
        "source-watch-a",
        cusip="91282CBB2",
        market_slug="alpha-watch",
        fail_rate_bps="280.000000",
        repo_specialness_bps="80.000000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "zeta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == tuple(sorted(forward.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == tuple(
        sorted(item.reason_code for item in forward.reason_code_counts),
    )


def test_extreme_repo_specialness_blocks_even_when_fail_rate_and_age_are_inline() -> None:
    digest_report = report(
        observation(
            "source-special",
            fail_rate_bps="40.000000",
            settlement_age_days="0.000000",
            repo_specialness_bps="175.000000",
            auction_cycle_proximity_days="12.000000",
            deliverable_supply_score="0.800000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.settlement_fail_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "rates_coupon_settlement_fail_repo_specialness_present",
    )
    assert digest_report.rows[0].settlement_fail_status == "blocked"
    assert digest_report.rows[0].reason_codes == (
        "rates_coupon_settlement_fail_repo_specialness",
    )


def test_non_default_thresholds_can_downgrade_moderate_fail_stress() -> None:
    module = digest()
    cfg = module.RatesCouponSettlementFailDigestConfig(
        watch_fail_rate_bps=d("320.000000"),
        blocked_fail_rate_bps=d("700.000000"),
        watch_settlement_age_days=d("3.000000"),
        blocked_settlement_age_days=d("8.000000"),
        watch_repo_specialness_bps=d("120.000000"),
        blocked_repo_specialness_bps=d("260.000000"),
        auction_cycle_window_days=d("1.000000"),
        thin_deliverable_supply_score=d("0.150000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            fail_rate_bps="275.000000",
            settlement_age_days="2.000000",
            repo_specialness_bps="82.000000",
            auction_cycle_proximity_days="4.000000",
            deliverable_supply_score="0.320000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_rates_coupon_settlement_fail_screening"
    )
    assert digest_report.rows[0].settlement_fail_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "rates_coupon_settlement_fail_inline",
    )
    assert digest_report.settlement_fail_risk_score == d("0.000000")
    assert digest_report.reason_codes == (
        "rates_coupon_settlement_fail_digest_clear",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="fail_rate_bps must be a Decimal"):
        observation(fail_rate_bps=_DecimalSubclass("42.000000"))
    with pytest.raises(ValueError, match="settlement_age_days must be nonnegative"):
        observation(settlement_age_days="-1.000000")
    with pytest.raises(
        ValueError,
        match="deliverable_supply_score must be between zero and one",
    ):
        observation(deliverable_supply_score="1.100000")
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 4, 13, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_rates_coupon_settlement_fail_digest(
            (),
            config=module.RatesCouponSettlementFailDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_fail_rate_bps"):
        module.RatesCouponSettlementFailDigestConfig(
            watch_fail_rate_bps=d("800.000000"),
            blocked_fail_rate_bps=d("700.000000"),
        )
    with pytest.raises(ValueError, match="cusip must be a 9-character CUSIP"):
        observation(cusip="bad-cusip")

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="risk_score must match"):
        replace(valid_row, risk_score=d("0.999999"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "rates_coupon_settlement_fail_inline",
                "rates_coupon_settlement_fail_watch_fail_rate",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_counts_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)
    assert all(
        item.paper_only and item.report_only and item.readonly
        for item in digest_report.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.RatesCouponSettlementFailDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count report_only must be True"):
        replace(digest_report.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_canonical_string_numerics_and_no_unsafe_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_rates_coupon_settlement_fail_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["fail_rate_bps"] == "180.000000"
    assert payload["rows"][0]["source_quorum"] == "3.000000"
    assert payload["rows"][0]["data_timestamp"] == "2026-07-04T13:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "order" not in lowered
                assert "auth" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.RatesCouponSettlementFailDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
