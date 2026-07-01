from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_settlement_timing import (
    PaperSettlementTimingConfig,
    PaperSettlementTimingInput,
    PaperSettlementTimingReport,
    PaperSettlementTimingRow,
    build_paper_settlement_timing_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 6, 19, 6, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


def d(value: str) -> Decimal:
    return Decimal(value)


def timing_input(
    *,
    market_slug: str = "event-alpha",
    side: str = "yes",
    action: str = "recommend",
    net_probability_edge: Decimal = d("0.080000"),
    expected_resolution_at: datetime | None = datetime(2026, 6, 22, 6, 0, tzinfo=UTC),
    settlement_context_fresh: bool = True,
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("source_edge",),
) -> PaperSettlementTimingInput:
    return PaperSettlementTimingInput(
        market_slug=market_slug,
        side=side,
        action=action,
        net_probability_edge=net_probability_edge,
        expected_resolution_at=expected_resolution_at,
        settlement_context_fresh=settlement_context_fresh,
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def config(
    *,
    max_resolution_horizon_days: Decimal = d("7.000000"),
    stale_context_penalty_per_share: Decimal = d("0.020000"),
    unknown_resolution_penalty_per_share: Decimal = d("0.050000"),
) -> PaperSettlementTimingConfig:
    return PaperSettlementTimingConfig(
        config_version="paper-settlement-timing-v0",
        max_resolution_horizon_days=max_resolution_horizon_days,
        stale_context_penalty_per_share=stale_context_penalty_per_share,
        unknown_resolution_penalty_per_share=unknown_resolution_penalty_per_share,
    )


def build_report(*inputs: PaperSettlementTimingInput) -> PaperSettlementTimingReport:
    return build_paper_settlement_timing_report(
        inputs,
        config=config(),
        generated_at=GENERATED_AT,
    )


def field_values(instance):
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_fresh_known_resolution_within_horizon_is_acceptable_without_timing_cost():
    report = build_report(
        timing_input(
            market_slug="fresh-known",
            net_probability_edge=d("0.080000"),
            expected_resolution_at=datetime(2026, 6, 22, 6, 0, tzinfo=UTC),
        )
    )

    row = report.rows[0]
    assert row.market_slug == "fresh-known"
    assert row.side == "yes"
    assert row.action == "recommend"
    assert row.observed_at == OBSERVED_AT
    assert row.expected_resolution_at == datetime(2026, 6, 22, 6, 0, tzinfo=UTC)
    assert row.days_to_resolution == d("3.000000")
    assert row.timing_status == "acceptable"
    assert row.timing_cost_per_share == ZERO
    assert row.adjusted_net_probability_edge == d("0.080000")
    assert row.reason_codes == ("source_edge",)

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-settlement-timing-v0"
    assert report.input_count == 1
    assert report.row_count == 1
    assert report.acceptable_count == 1
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_stale_context_watches_and_subtracts_stale_penalty_from_edge():
    report = build_report(
        timing_input(
            market_slug="stale-known",
            net_probability_edge=d("0.080000"),
            settlement_context_fresh=False,
        )
    )

    row = report.rows[0]
    assert row.days_to_resolution == d("3.000000")
    assert row.timing_status == "watch"
    assert row.timing_cost_per_share == d("0.020000")
    assert row.adjusted_net_probability_edge == d("0.060000")
    assert "settlement_context_stale" in row.reason_codes


def test_unknown_resolution_blocks_and_applies_unknown_resolution_penalty():
    report = build_report(
        timing_input(
            market_slug="unknown-resolution",
            net_probability_edge=d("0.080000"),
            expected_resolution_at=None,
        )
    )

    row = report.rows[0]
    assert row.days_to_resolution is None
    assert row.timing_status == "blocked"
    assert row.timing_cost_per_share == d("0.050000")
    assert row.adjusted_net_probability_edge == d("0.030000")
    assert "unknown_resolution" in row.reason_codes


def test_resolution_beyond_configured_horizon_blocks_without_extra_cost():
    report = build_report(
        timing_input(
            market_slug="long-horizon",
            expected_resolution_at=datetime(2026, 6, 29, 6, 0, tzinfo=UTC),
        )
    )

    row = report.rows[0]
    assert row.days_to_resolution == d("10.000000")
    assert row.timing_status == "blocked"
    assert row.timing_cost_per_share == ZERO
    assert row.adjusted_net_probability_edge == d("0.080000")
    assert "resolution_horizon_exceeded" in row.reason_codes


def test_timing_penalties_that_remove_edge_block_the_row():
    report = build_report(
        timing_input(
            market_slug="penalty-removes-edge",
            net_probability_edge=d("0.015000"),
            settlement_context_fresh=False,
        )
    )

    row = report.rows[0]
    assert row.timing_status == "blocked"
    assert row.timing_cost_per_share == d("0.020000")
    assert row.adjusted_net_probability_edge == d("-0.005000")
    assert "nonpositive_adjusted_net_probability_edge" in row.reason_codes
    assert "settlement_context_stale" in row.reason_codes


def test_source_watch_and_reject_actions_cannot_be_promoted_by_timing():
    report = build_report(
        timing_input(market_slug="source-watch", action="watch"),
        timing_input(market_slug="source-reject", action="reject"),
    )

    source_watch = next(row for row in report.rows if row.market_slug == "source-watch")
    assert source_watch.timing_status == "watch"
    assert source_watch.adjusted_net_probability_edge == d("0.080000")
    assert "source_action_watch" in source_watch.reason_codes

    source_reject = next(row for row in report.rows if row.market_slug == "source-reject")
    assert source_reject.timing_status == "blocked"
    assert source_reject.adjusted_net_probability_edge == d("0.080000")
    assert "source_action_reject" in source_reject.reason_codes


@pytest.mark.parametrize(
    ("input_kwargs", "expected_status", "expected_reason"),
    (
        (
            {"expected_resolution_at": None},
            "blocked",
            "unknown_resolution",
        ),
        (
            {"expected_resolution_at": OBSERVED_AT},
            "blocked",
            "resolution_already_due",
        ),
        (
            {"action": "reject"},
            "blocked",
            "source_action_reject",
        ),
        (
            {"expected_resolution_at": datetime(2026, 6, 29, 6, 0, tzinfo=UTC)},
            "blocked",
            "resolution_horizon_exceeded",
        ),
        (
            {"settlement_context_fresh": False},
            "watch",
            "settlement_context_stale",
        ),
    ),
)
def test_settlement_timing_characterizes_pending_gate_statuses(
    input_kwargs,
    expected_status,
    expected_reason,
):
    report = build_report(timing_input(market_slug=expected_reason, **input_kwargs))

    row = report.rows[0]
    assert row.timing_status == expected_status
    assert expected_reason in row.reason_codes
    assert report.blocked_count == (1 if expected_status == "blocked" else 0)
    assert report.watch_count == (1 if expected_status == "watch" else 0)
    assert report.acceptable_count == 0


def test_rows_sort_by_adjusted_edge_then_status_then_market_and_side():
    report = build_report(
        timing_input(market_slug="blocked-high", expected_resolution_at=None),
        timing_input(
            market_slug="acceptable-mid",
            net_probability_edge=d("0.070000"),
        ),
        timing_input(
            market_slug="watch-mid",
            net_probability_edge=d("0.090000"),
            settlement_context_fresh=False,
        ),
        timing_input(
            market_slug="acceptable-alpha",
            net_probability_edge=d("0.060000"),
        ),
        timing_input(
            market_slug="acceptable-beta",
            net_probability_edge=d("0.060000"),
        ),
    )

    assert [row.market_slug for row in report.rows] == [
        "acceptable-mid",
        "watch-mid",
        "acceptable-alpha",
        "acceptable-beta",
        "blocked-high",
    ]

    tied_status = build_report(
        timing_input(market_slug="watch-z", action="watch", net_probability_edge=d("0.060000")),
        timing_input(
            market_slug="acceptable-a",
            net_probability_edge=d("0.060000"),
        ),
        timing_input(
            market_slug="blocked-b",
            action="reject",
            net_probability_edge=d("0.060000"),
        ),
    )
    assert [row.market_slug for row in tied_status.rows] == [
        "acceptable-a",
        "watch-z",
        "blocked-b",
    ]


def test_datetimes_normalize_to_utc_and_fractional_days_quantize():
    eastern = timezone(timedelta(hours=-4))
    report = build_paper_settlement_timing_report(
        [
            timing_input(
                observed_at=datetime(2026, 6, 19, 8, 0, tzinfo=eastern),
                expected_resolution_at=datetime(2026, 6, 20, 14, 0, tzinfo=eastern),
            )
        ],
        config=config(),
        generated_at=datetime(2026, 6, 19, 8, 0, tzinfo=eastern),
    )

    row = report.rows[0]
    assert report.generated_at == GENERATED_AT
    assert row.observed_at == GENERATED_AT
    assert row.expected_resolution_at == datetime(2026, 6, 20, 18, 0, tzinfo=UTC)
    assert row.days_to_resolution == d("1.250000")


def test_direct_constructors_validate_consistency_utc_and_safety_flags():
    report = build_report(timing_input())
    rebuilt_row = PaperSettlementTimingRow(**field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]

    with pytest.raises(ValueError, match="adjusted_net_probability_edge"):
        replace(report.rows[0], adjusted_net_probability_edge=d("0.010000"))
    with pytest.raises(ValueError, match="timing_cost_per_share"):
        replace(report.rows[0], timing_cost_per_share=d("0.010000"))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=2)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(timing_input(), readonly=False)


def test_dataclasses_are_frozen():
    input_row = timing_input()
    cfg = config()
    report = build_report(input_row)
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        input_row.side = "no"
    with pytest.raises(FrozenInstanceError):
        cfg.max_resolution_horizon_days = d("10.000000")
    with pytest.raises(FrozenInstanceError):
        row.timing_status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows = ()


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("net_probability_edge", Decimal("NaN"), "net_probability_edge"),
        ("net_probability_edge", 0.08, "net_probability_edge"),
        ("settlement_context_fresh", 1, "settlement_context_fresh"),
        ("observed_at", "2026-06-19T06:00:00Z", "observed_at"),
        ("reason_codes", ("source_edge ",), "reason_codes"),
    ),
)
def test_input_constructor_rejects_invalid_public_values(field_name, bad_value, match):
    with pytest.raises(ValueError, match=match):
        replace(timing_input(), **{field_name: bad_value})


def test_config_rejects_non_decimal_or_negative_cost_and_score_values():
    with pytest.raises(ValueError, match="max_resolution_horizon_days"):
        replace(config(), max_resolution_horizon_days=7)
    with pytest.raises(ValueError, match="stale_context_penalty_per_share"):
        replace(config(), stale_context_penalty_per_share=d("-0.000001"))
    with pytest.raises(ValueError, match="unknown_resolution_penalty_per_share"):
        replace(config(), unknown_resolution_penalty_per_share=0.05)


def test_builder_rejects_non_exact_public_types_and_unsafe_flags():
    with pytest.raises(ValueError, match="config"):
        build_paper_settlement_timing_report(
            [timing_input()],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_settlement_timing_report(
            [timing_input()],
            config=config(),
            generated_at="2026-06-19T12:00:00Z",
        )
    with pytest.raises(ValueError, match="inputs"):
        build_paper_settlement_timing_report(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report_only"):
        build_paper_settlement_timing_report(
            [replace(timing_input(), report_only=False)],
            config=config(),
            generated_at=GENERATED_AT,
        )
