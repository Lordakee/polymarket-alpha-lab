from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedExitWindowShape:
    review_reference: str
    observed_at: datetime
    exit_depth_ratio: Decimal
    spread_ratio: Decimal
    expected_fill_window_minutes: Decimal
    book_age_seconds: Decimal
    resolution_window_hours: Decimal
    depth_decay_ratio: Decimal
    fee_drag_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_liquidity_exit_window_scorecard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_WINDOW_SCORECARD_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_exit_depth_ratio": d("0.700000"),
        "minimum_watch_exit_depth_ratio": d("0.400000"),
        "maximum_pass_spread_ratio": d("0.020000"),
        "maximum_watch_spread_ratio": d("0.050000"),
        "maximum_pass_fill_window_minutes": d("15.000000"),
        "maximum_watch_fill_window_minutes": d("60.000000"),
        "maximum_pass_book_age_seconds": d("120.000000"),
        "maximum_watch_book_age_seconds": d("900.000000"),
        "minimum_pass_resolution_window_hours": d("72.000000"),
        "minimum_watch_resolution_window_hours": d("24.000000"),
        "maximum_pass_depth_decay_ratio": d("0.200000"),
        "maximum_watch_depth_decay_ratio": d("0.600000"),
        "maximum_pass_fee_drag_ratio": d("0.010000"),
        "maximum_watch_fee_drag_ratio": d("0.030000"),
        "exit_depth_weight": d("0.300000"),
        "spread_weight": d("0.200000"),
        "fill_window_weight": d("0.150000"),
        "book_age_weight": d("0.100000"),
        "resolution_window_weight": d("0.100000"),
        "depth_decay_weight": d("0.100000"),
        "fee_drag_weight": d("0.050000"),
        "pass_exit_window_score": d("0.750000"),
        "watch_exit_window_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketLiquidityExitWindowScorecardConfig(**values)


def exit_window_input(
    review_reference: str = "alpha-pass",
    *,
    observed_at: datetime = OBSERVED_AT,
    exit_depth_ratio: Decimal = d("0.900000"),
    spread_ratio: Decimal = d("0.005000"),
    expected_fill_window_minutes: Decimal = d("10.000000"),
    book_age_seconds: Decimal = d("60.000000"),
    resolution_window_hours: Decimal = d("96.000000"),
    depth_decay_ratio: Decimal = d("0.100000"),
    fee_drag_ratio: Decimal = d("0.005000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchMarketLiquidityExitWindowScorecardInput(
        review_reference=review_reference,
        observed_at=observed_at,
        exit_depth_ratio=exit_depth_ratio,
        spread_ratio=spread_ratio,
        expected_fill_window_minutes=expected_fill_window_minutes,
        book_age_seconds=book_age_seconds,
        resolution_window_hours=resolution_window_hours,
        depth_decay_ratio=depth_decay_ratio,
        fee_drag_ratio=fee_drag_ratio,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_liquidity_exit_window_scorecard_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_exit_window_review_with_digest() -> None:
    module = api()
    empty = report()

    assert module.LIQUIDITY_EXIT_WINDOW_SCORECARD_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "LIQUIDITY_EXIT_WINDOW_SCORECARD_STATUSES",
        "DEFAULT_RESEARCH_MARKET_LIQUIDITY_EXIT_WINDOW_SCORECARD_REPORT_CONFIG_VERSION",
        "ResearchMarketLiquidityExitWindowScorecardConfig",
        "ResearchMarketLiquidityExitWindowScorecardInput",
        "ResearchMarketLiquidityExitWindowScorecardReasonCodeCount",
        "ResearchMarketLiquidityExitWindowScorecardReport",
        "ResearchMarketLiquidityExitWindowScorecardRow",
        "build_research_market_liquidity_exit_window_scorecard_report",
        "research_market_liquidity_exit_window_scorecard_report_digest",
        "research_market_liquidity_exit_window_scorecard_report_payload",
    )
    assert type(empty) is module.ResearchMarketLiquidityExitWindowScorecardReport
    assert empty.observation_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.exit_depth_pressure_count == ZERO
    assert empty.spread_pressure_count == ZERO
    assert empty.fill_window_pressure_count == ZERO
    assert empty.stale_book_count == ZERO
    assert empty.resolution_window_pressure_count == ZERO
    assert empty.depth_decay_pressure_count == ZERO
    assert empty.fee_drag_pressure_count == ZERO
    assert empty.average_exit_window_score is None
    assert empty.min_exit_depth_ratio == ZERO
    assert empty.max_spread_ratio == ZERO
    assert empty.max_expected_fill_window_minutes == ZERO
    assert empty.max_book_age_seconds == ZERO
    assert empty.min_resolution_window_hours == ZERO
    assert empty.max_depth_decay_ratio == ZERO
    assert empty.max_fee_drag_ratio == ZERO
    assert empty.status == "block"
    assert empty.rows == ()
    assert empty.reason_codes == ("no_exit_window_observations",)
    assert empty.reason_code_counts == (
        module.ResearchMarketLiquidityExitWindowScorecardReasonCodeCount(
            reason_code="no_exit_window_observations",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert len(empty.derived_validation_digest) == 64
    int(empty.derived_validation_digest, 16)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_scores_exit_depth_costs_freshness_timing_decay_and_fees() -> None:
    combined = report(
        exit_window_input("alpha-pass"),
        exit_window_input(
            (
                "case-block market_id market_slug question text "
                "https://example.invalid dsn=postgres table_name=markets token=secret"
            ),
            exit_depth_ratio=d("0.200000"),
            spread_ratio=d("0.080000"),
            expected_fill_window_minutes=d("120.000000"),
            book_age_seconds=d("1200.000000"),
            resolution_window_hours=d("8.000000"),
            depth_decay_ratio=d("0.800000"),
            fee_drag_ratio=d("0.040000"),
            reason_codes=("manual_liquidity_check",),
        ),
        exit_window_input(
            "gamma-watch",
            exit_depth_ratio=d("0.550000"),
            spread_ratio=d("0.030000"),
            expected_fill_window_minutes=d("30.000000"),
            book_age_seconds=d("300.000000"),
            resolution_window_hours=d("36.000000"),
            depth_decay_ratio=d("0.300000"),
            fee_drag_ratio=d("0.020000"),
        ),
    )

    assert combined.observation_count == d("3.000000")
    assert combined.pass_count == d("1.000000")
    assert combined.watch_count == d("1.000000")
    assert combined.block_count == d("1.000000")
    assert combined.exit_depth_pressure_count == d("2.000000")
    assert combined.spread_pressure_count == d("2.000000")
    assert combined.fill_window_pressure_count == d("2.000000")
    assert combined.stale_book_count == d("2.000000")
    assert combined.resolution_window_pressure_count == d("2.000000")
    assert combined.depth_decay_pressure_count == d("2.000000")
    assert combined.fee_drag_pressure_count == d("2.000000")
    assert combined.average_exit_window_score == d("0.489259")
    assert combined.min_exit_depth_ratio == d("0.200000")
    assert combined.max_spread_ratio == d("0.080000")
    assert combined.max_expected_fill_window_minutes == d("120.000000")
    assert combined.max_book_age_seconds == d("1200.000000")
    assert combined.min_resolution_window_hours == d("8.000000")
    assert combined.max_depth_decay_ratio == d("0.800000")
    assert combined.max_fee_drag_ratio == d("0.040000")
    assert combined.status == "block"
    assert combined.reason_codes == (
        "exit_window_block",
        "exit_depth_block",
        "spread_block",
        "fill_window_block",
        "book_age_block",
        "resolution_window_block",
        "depth_decay_block",
        "fee_drag_block",
        "exit_depth_watch",
        "spread_watch",
        "fill_window_watch",
        "book_age_watch",
        "resolution_window_watch",
        "depth_decay_watch",
        "fee_drag_watch",
    )

    pass_row, block_row, watch_row = combined.rows
    assert tuple(row.public_row_ref for row in combined.rows) == (
        "exit_window_group_001",
        "exit_window_group_002",
        "exit_window_group_003",
    )
    assert tuple(row.status for row in combined.rows) == ("pass", "block", "watch")
    assert pass_row.exit_window_score == d("0.893333")
    assert pass_row.status == "pass"
    assert block_row.exit_depth_score == d("0.200000")
    assert block_row.resolution_window_score == d("0.111111")
    assert block_row.exit_window_score == d("0.071111")
    assert block_row.status == "block"
    assert "input_manual_liquidity_check" in block_row.reason_codes
    assert watch_row.book_age_score == d("0.666667")
    assert watch_row.exit_window_score == d("0.503333")
    assert "exit_depth_watch" in watch_row.reason_codes
    assert "fee_drag_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    sensitive_reference = (
        "case-block market_id market_slug question text "
        "https://example.invalid dsn=postgres table_name=markets "
        "token=secret wallet order trade live recommend sizing"
    )
    first = report(
        SuppliedExitWindowShape(
            review_reference=sensitive_reference,
            observed_at=OBSERVED_AT,
            exit_depth_ratio=d("0.550000"),
            spread_ratio=d("0.030000"),
            expected_fill_window_minutes=d("30.000000"),
            book_age_seconds=d("300.000000"),
            resolution_window_hours=d("36.000000"),
            depth_decay_ratio=d("0.300000"),
            fee_drag_ratio=d("0.020000"),
            reason_codes=("zeta", "alpha"),
        ),
        exit_window_input("alpha-pass"),
    )
    second = report(
        exit_window_input("alpha-pass"),
        SuppliedExitWindowShape(
            review_reference=sensitive_reference,
            observed_at=OBSERVED_AT,
            exit_depth_ratio=d("0.550000"),
            spread_ratio=d("0.030000"),
            expected_fill_window_minutes=d("30.000000"),
            book_age_seconds=d("300.000000"),
            resolution_window_hours=d("36.000000"),
            depth_decay_ratio=d("0.300000"),
            fee_drag_ratio=d("0.020000"),
            reason_codes=("alpha", "zeta"),
        ),
    )

    first_payload = module.research_market_liquidity_exit_window_scorecard_report_payload(
        first,
    )
    second_payload = module.research_market_liquidity_exit_window_scorecard_report_payload(
        second,
    )
    digest_payload = dict(first_payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert (
        module.research_market_liquidity_exit_window_scorecard_report_digest(first)
        == first.derived_validation_digest
    )
    assert hashlib.sha256(encoded.encode("utf-8")).hexdigest() == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["exit_window_score"] == "0.893333"
    assert first_payload["rows"][1]["book_age_score"] == "0.666667"
    assert not any(
        type(value) in (float, int) for value in _walk_payload_values(first_payload)
    )
    encoded_public = json.dumps(first_payload, sort_keys=True).lower()
    assert all(
        fragment not in encoded_public
        for fragment in (
            "market_id",
            "market_slug",
            "question text",
            "https://",
            "dsn=",
            "table_name",
            "token=",
            "wallet",
            "order",
            "trade",
            "live",
            "recommend",
            "sizing",
        )
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_validation_rejects_bad_types_thresholds_flags_and_duplicates() -> None:
    with pytest.raises(ValueError, match="scorecard weights"):
        config(exit_depth_weight=d("0.100000"))
    with pytest.raises(ValueError, match="minimum_pass_exit_depth_ratio"):
        config(minimum_pass_exit_depth_ratio=d("0.300000"))
    with pytest.raises(ValueError, match="maximum_pass_spread_ratio"):
        config(maximum_pass_spread_ratio=d("0.060000"))
    with pytest.raises(ValueError, match="minimum_pass_resolution_window_hours"):
        config(minimum_pass_resolution_window_hours=d("12.000000"))
    with pytest.raises(ValueError, match="exit_depth_weight"):
        config(exit_depth_weight=DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="maximum_pass_book_age_seconds"):
        config(maximum_pass_book_age_seconds=120)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        report(exit_window_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            exit_window_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="exit_depth_ratio"):
        exit_window_input(exit_depth_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="fee_drag_ratio"):
        exit_window_input(fee_drag_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        exit_window_input(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        exit_window_input(paper_only=False)
    with pytest.raises(ValueError, match="review_reference values"):
        report(exit_window_input("duplicate"), exit_window_input("duplicate"))


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    module = api()
    exit_report = report(exit_window_input())

    with pytest.raises(FrozenInstanceError):
        exit_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        exit_report.rows[0].exit_window_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(exit_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="exit_window_score"):
        replace(exit_report.rows[0], exit_window_score=d("0.100000"))
    with pytest.raises(ValueError, match="observation_count"):
        replace(exit_report, observation_count=d("2.000000"))

    public_dataclasses = (
        module.ResearchMarketLiquidityExitWindowScorecardConfig,
        module.ResearchMarketLiquidityExitWindowScorecardInput,
        module.ResearchMarketLiquidityExitWindowScorecardReasonCodeCount,
        module.ResearchMarketLiquidityExitWindowScorecardReport,
        module.ResearchMarketLiquidityExitWindowScorecardRow,
    )
    for contract in public_dataclasses:
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (float, int) for field in fields(contract))


def test_owned_module_has_no_filesystem_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_exit_window_scorecard_report.py"
    )
    module_text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    )

    assert all(term not in module_text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
