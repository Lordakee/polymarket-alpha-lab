from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab import research_market_event_liquidity_decay_report as module
from polymarket_alpha_lab.research_market_event_liquidity_decay_report import (
    DEFAULT_RESEARCH_MARKET_EVENT_LIQUIDITY_DECAY_CONFIG_VERSION,
    STATUSES,
    ResearchMarketEventLiquidityDecayConfig,
    ResearchMarketEventLiquidityDecayInput,
    ResearchMarketEventLiquidityDecayReasonCodeCount,
    ResearchMarketEventLiquidityDecayReport,
    ResearchMarketEventLiquidityDecayRow,
    build_research_market_event_liquidity_decay_report,
    research_market_event_liquidity_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 50, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketEventLiquidityDecayConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_MARKET_EVENT_LIQUIDITY_DECAY_CONFIG_VERSION,
        "max_watch_liquidity_decay_score": d("0.350000"),
        "max_block_liquidity_decay_score": d("0.700000"),
        "max_watch_depth_decay_ratio": d("0.250000"),
        "max_block_depth_decay_ratio": d("0.600000"),
        "max_watch_spread_widening_ratio": d("0.500000"),
        "max_block_spread_widening_ratio": d("1.500000"),
        "max_watch_quote_age_seconds": d("300.000000"),
        "max_block_quote_age_seconds": d("1800.000000"),
        "max_watch_volume_fade_ratio": d("0.300000"),
        "max_block_volume_fade_ratio": d("0.700000"),
        "max_watch_fee_rate_bps": d("50.000000"),
        "max_block_fee_rate_bps": d("100.000000"),
        "depth_weight": d("0.250000"),
        "spread_weight": d("0.200000"),
        "quote_staleness_weight": d("0.200000"),
        "volume_weight": d("0.200000"),
        "fee_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchMarketEventLiquidityDecayConfig(**values)


def domain_input(
    event_domain: str,
    *,
    domain_label: str = "public event domain",
    baseline_depth_usd: Decimal = d("100000.000000"),
    current_depth_usd: Decimal = d("90000.000000"),
    baseline_spread_bps: Decimal = d("50.000000"),
    current_spread_bps: Decimal = d("60.000000"),
    quote_age_seconds: Decimal = d("120.000000"),
    baseline_volume_usd: Decimal = d("50000.000000"),
    current_volume_usd: Decimal = d("45000.000000"),
    fee_rate_bps: Decimal = d("20.000000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("domain_liquidity_rollup_reviewed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketEventLiquidityDecayInput:
    return ResearchMarketEventLiquidityDecayInput(
        event_domain=event_domain,
        domain_label=domain_label,
        baseline_depth_usd=baseline_depth_usd,
        current_depth_usd=current_depth_usd,
        baseline_spread_bps=baseline_spread_bps,
        current_spread_bps=current_spread_bps,
        quote_age_seconds=quote_age_seconds,
        baseline_volume_usd=baseline_volume_usd,
        current_volume_usd=current_volume_usd,
        fee_rate_bps=fee_rate_bps,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchMarketEventLiquidityDecayInput,
    cfg: ResearchMarketEventLiquidityDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketEventLiquidityDecayReport:
    return build_research_market_event_liquidity_decay_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected numeric public payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_report_scores_pass_watch_and_block_liquidity_decay_by_event_domain() -> None:
    decay_report = report(
        domain_input("culture"),
        domain_input(
            "economics",
            baseline_depth_usd=d("100000.000000"),
            current_depth_usd=d("65000.000000"),
            baseline_spread_bps=d("40.000000"),
            current_spread_bps=d("70.000000"),
            quote_age_seconds=d("600.000000"),
            baseline_volume_usd=d("50000.000000"),
            current_volume_usd=d("30000.000000"),
            fee_rate_bps=d("60.000000"),
            reason_codes=("manual_liquidity_review",),
        ),
        domain_input(
            "weather",
            baseline_depth_usd=d("100000.000000"),
            current_depth_usd=d("25000.000000"),
            baseline_spread_bps=d("40.000000"),
            current_spread_bps=d("110.000000"),
            quote_age_seconds=d("2400.000000"),
            baseline_volume_usd=d("50000.000000"),
            current_volume_usd=d("10000.000000"),
            fee_rate_bps=d("125.000000"),
            reason_codes=("late_quote_review",),
        ),
    )

    assert is_dataclass(decay_report)
    assert STATUSES == ("pass", "watch", "block")
    assert decay_report.config_version == (
        "research-market-event-liquidity-decay-report-v0"
    )
    assert decay_report.event_domain_count == d("3.000000")
    assert decay_report.pass_count == d("1.000000")
    assert decay_report.watch_count == d("1.000000")
    assert decay_report.block_count == d("1.000000")
    assert decay_report.average_liquidity_decay_score == d("0.500000")
    assert decay_report.max_depth_decay_ratio == d("0.750000")
    assert decay_report.max_spread_widening_ratio == d("1.750000")
    assert decay_report.max_quote_age_seconds == d("2400.000000")
    assert decay_report.max_volume_fade_ratio == d("0.800000")
    assert decay_report.max_fee_rate_bps == d("125.000000")
    assert decay_report.status == "block"
    assert len(decay_report.derived_validation_digest) == 64
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True

    passed, watched, blocked = decay_report.rows
    assert tuple(row.decay_status for row in decay_report.rows) == (
        "pass",
        "watch",
        "block",
    )

    assert passed.event_domain == "culture"
    assert passed.depth_decay_ratio == d("0.100000")
    assert passed.spread_widening_ratio == d("0.200000")
    assert passed.quote_staleness_score == d("0.066667")
    assert passed.volume_fade_ratio == d("0.100000")
    assert passed.fee_friction_score == d("0.200000")
    assert passed.liquidity_decay_score == d("0.128333")
    assert passed.reason_codes == (
        "input_domain_liquidity_rollup_reviewed",
        "liquidity_decay_clear",
    )

    assert watched.event_domain == "economics"
    assert watched.depth_decay_ratio == d("0.350000")
    assert watched.spread_widening_ratio == d("0.750000")
    assert watched.quote_staleness_score == d("0.333333")
    assert watched.volume_fade_ratio == d("0.400000")
    assert watched.fee_friction_score == d("0.600000")
    assert watched.liquidity_decay_score == d("0.474167")
    assert watched.reason_codes == (
        "depth_decay_watch",
        "fee_friction_watch",
        "input_manual_liquidity_review",
        "liquidity_decay_score_watch",
        "quote_staleness_watch",
        "spread_widening_watch",
        "volume_fade_watch",
    )

    assert blocked.event_domain == "weather"
    assert blocked.depth_decay_ratio == d("0.750000")
    assert blocked.spread_widening_ratio == d("1.750000")
    assert blocked.quote_staleness_score == d("1.000000")
    assert blocked.volume_fade_ratio == d("0.800000")
    assert blocked.fee_friction_score == d("1.000000")
    assert blocked.liquidity_decay_score == d("0.897500")
    assert blocked.reason_codes == (
        "depth_decay_block",
        "fee_friction_block",
        "input_late_quote_review",
        "liquidity_decay_score_block",
        "quote_staleness_block",
        "spread_widening_block",
        "volume_fade_block",
    )


def test_empty_report_is_watch_with_decimal_counts_and_hard_flags() -> None:
    decay_report = report()

    assert decay_report.event_domain_count == ZERO
    assert decay_report.pass_count == ZERO
    assert decay_report.watch_count == ZERO
    assert decay_report.block_count == ZERO
    assert decay_report.average_liquidity_decay_score is None
    assert decay_report.max_depth_decay_ratio == ZERO
    assert decay_report.status == "watch"
    assert decay_report.reason_codes == ("liquidity_decay_no_event_domains",)
    assert decay_report.reason_code_counts == (
        ResearchMarketEventLiquidityDecayReasonCodeCount(
            reason_code="liquidity_decay_no_event_domains",
            count=d("1.000000"),
            event_domain_ratio=d("0.000000"),
        ),
    )
    assert decay_report.rows == ()

    populated = report(domain_input("culture"))
    for value in (decay_report, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_ratio",
                    "_score",
                    "_bps",
                    "_usd",
                    "_seconds",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_is_deterministic_digest_signed_and_has_no_numeric_leaks() -> None:
    decay_report = report(
        domain_input("culture", observed_at=datetime(2026, 7, 6, 8, 45, tzinfo=UTC)),
        generated_at=datetime(2026, 7, 6, 9, 0, tzinfo=UTC),
    )

    payload = research_market_event_liquidity_decay_report_payload(decay_report)

    assert payload["generated_at"] == "2026-07-06T09:00:00+00:00"
    assert payload["event_domain_count"] == "1.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T08:45:00+00:00"
    assert payload["rows"][0]["liquidity_decay_score"] == "0.128333"
    assert payload["derived_validation_digest"] == decay_report.derived_validation_digest
    assert "raw_market_id" not in json.dumps(payload, sort_keys=True)
    assert "raw_source_id" not in json.dumps(payload, sort_keys=True)
    assert_no_int_or_float_values(payload)
    json.dumps(payload, sort_keys=True)

    repeated_payload = research_market_event_liquidity_decay_report_payload(
        report(
            domain_input(
                "culture",
                observed_at=datetime(2026, 7, 6, 8, 45, tzinfo=UTC),
            ),
            generated_at=datetime(2026, 7, 6, 9, 0, tzinfo=UTC),
        ),
    )
    assert repeated_payload == payload

    tampered = dict(payload)
    tampered["pass_count"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_market_event_liquidity_decay_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(decay_report, pass_count=d("2.000000"))


def test_public_payload_rejects_raw_identifiers_and_action_language() -> None:
    payload = research_market_event_liquidity_decay_report_payload(
        report(domain_input("culture")),
    )

    for key in (
        "raw_market_id",
        "raw_source_id",
        "condition_id",
        "token_id",
        "source_url",
        "wallet_address",
        "auth_header",
        "order_id",
        "trade_id",
        "network_url",
        "database_table",
        "buy_instruction",
        "sell_instruction",
        "position_size",
        "recommendation_text",
        "sizing_hint",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            research_market_event_liquidity_decay_report_payload(unsafe)

    for value in (
        "raw_market_id:abc",
        "source_url:https://example.invalid",
        "buy this outcome",
        "sell this outcome",
        "trade execution pending",
        "increase position size",
        "recommendation pending",
        "wallet signer",
        "live trading",
        "database write",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            research_market_event_liquidity_decay_report_payload(unsafe)

    numeric = dict(payload)
    numeric["event_domain_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        research_market_event_liquidity_decay_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_market_event_liquidity_decay_report_payload(downgraded)


def test_validation_rejects_non_decimal_duplicate_domains_bad_times_and_flags() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        domain_input("bad-decimal", baseline_depth_usd=100000)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        domain_input(
            "bad-subclass",
            baseline_depth_usd=_DecimalSubclass("100000.000000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(domain_input("aware"), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        domain_input("naive-time", observed_at=datetime(2026, 7, 6, 11, 45))
    with pytest.raises(ValueError, match="observed_at"):
        domain_input(
            "time-subclass",
            observed_at=_DatetimeSubclass(2026, 7, 6, 11, 45, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report(domain_input("future", observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        report(domain_input("duplicate"), domain_input("duplicate"))
    with pytest.raises(ValueError, match="paper_only"):
        domain_input("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_research_market_event_liquidity_decay_report(
            (),
            config=ResearchMarketEventLiquidityDecayConfig.__new__(
                type(
                    "ConfigSubclass",
                    (ResearchMarketEventLiquidityDecayConfig,),
                    {},
                ),
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="weight"):
        config(depth_weight=d("0.350000"))
    with pytest.raises(ValueError, match="quote"):
        config(max_block_quote_age_seconds=d("100.000000"))

    frozen = domain_input("culture")
    with pytest.raises(FrozenInstanceError):
        frozen.event_domain = "changed"  # type: ignore[misc]


def test_manual_materialized_rows_and_reports_validate_consistency() -> None:
    decay_report = report(domain_input("culture"))
    row = decay_report.rows[0]

    with pytest.raises(ValueError, match="liquidity_decay_score"):
        ResearchMarketEventLiquidityDecayRow(
            **{
                **row.__dict__,
                "liquidity_decay_score": d("0.900000"),
            },
        )

    with pytest.raises(ValueError, match="status"):
        ResearchMarketEventLiquidityDecayReport(
            **{
                **decay_report.__dict__,
                "status": "block",
            },
        )


def test_module_surface_stays_pure_report_only_and_readonly() -> None:
    module_path = Path(module.__file__)
    source = module_path.read_text()

    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "subprocess",
        "os.environ",
        "open(",
        ".write(",
        ".execute(",
        "place_order",
        "submit_order",
        "cancel_order",
        "private_key",
        "api_key",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_MARKET_EVENT_LIQUIDITY_DECAY_CONFIG_VERSION",
        "STATUSES",
        "ResearchMarketEventLiquidityDecayConfig",
        "ResearchMarketEventLiquidityDecayInput",
        "ResearchMarketEventLiquidityDecayReasonCodeCount",
        "ResearchMarketEventLiquidityDecayReport",
        "ResearchMarketEventLiquidityDecayRow",
        "build_research_market_event_liquidity_decay_report",
        "research_market_event_liquidity_decay_report_payload",
    }
