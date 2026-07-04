import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 14, 15, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_rates_inflation_swap_breakout_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "rates-swap-alpha",
    *,
    market_slug: str = "us-cpi-above-forecast",
    swap_tenor: str = "2y",
    inflation_swap_rate_pct: str | Decimal = "3.420000",
    prior_inflation_swap_rate_pct: str | Decimal = "3.020000",
    breakeven_rate_pct: str | Decimal = "2.640000",
    consensus_inflation_rate_pct: str | Decimal = "2.500000",
    five_day_swap_change_bp: str | Decimal = "40.000000",
    volume_notional_usd_m: str | Decimal = "950.000000",
    data_timestamp: datetime = datetime(2026, 7, 4, 13, 45, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("public_inflation_swap_curve",),
):
    module = digest()
    return module.RatesInflationSwapBreakoutObservation(
        source_id=source_id,
        market_slug=market_slug,
        swap_tenor=swap_tenor,
        inflation_swap_rate_pct=(
            inflation_swap_rate_pct
            if isinstance(inflation_swap_rate_pct, Decimal)
            else d(inflation_swap_rate_pct)
        ),
        prior_inflation_swap_rate_pct=(
            prior_inflation_swap_rate_pct
            if isinstance(prior_inflation_swap_rate_pct, Decimal)
            else d(prior_inflation_swap_rate_pct)
        ),
        breakeven_rate_pct=(
            breakeven_rate_pct
            if isinstance(breakeven_rate_pct, Decimal)
            else d(breakeven_rate_pct)
        ),
        consensus_inflation_rate_pct=(
            consensus_inflation_rate_pct
            if isinstance(consensus_inflation_rate_pct, Decimal)
            else d(consensus_inflation_rate_pct)
        ),
        five_day_swap_change_bp=(
            five_day_swap_change_bp
            if isinstance(five_day_swap_change_bp, Decimal)
            else d(five_day_swap_change_bp)
        ),
        volume_notional_usd_m=(
            volume_notional_usd_m
            if isinstance(volume_notional_usd_m, Decimal)
            else d(volume_notional_usd_m)
        ),
        data_timestamp=data_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_rates_inflation_swap_breakout_digest(
        rows,
        config=cfg or module.RatesInflationSwapBreakoutDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.RatesInflationSwapBreakoutDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-rates-inflation-swap-breakout-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_rates_inflation_swap_breakout_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.breakout_count == d("0.000000")
    assert digest_report.breakeven_premium_count == d("0.000000")
    assert digest_report.consensus_gap_count == d("0.000000")
    assert digest_report.volume_confirmation_count == d("0.000000")
    assert digest_report.max_swap_change_bp == d("0.000000")
    assert digest_report.average_swap_rate_pct == d("0.000000")
    assert digest_report.breakout_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "rates_inflation_swap_breakout_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.RatesInflationSwapBreakoutReasonCodeCount(
            reason_code="rates_inflation_swap_breakout_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_swap_breakout_blocks_probability_event_screening() -> None:
    digest_report = report(
        observation(
            "rates-swap-blocked",
            market_slug="us-cpi-above-forecast",
            swap_tenor="2y",
            inflation_swap_rate_pct="3.420000",
            prior_inflation_swap_rate_pct="3.020000",
            breakeven_rate_pct="2.640000",
            consensus_inflation_rate_pct="2.500000",
            five_day_swap_change_bp="40.000000",
            volume_notional_usd_m="950.000000",
        ),
        observation(
            "rates-swap-watch",
            market_slug="us-pce-above-forecast",
            swap_tenor="5y",
            inflation_swap_rate_pct="3.050000",
            prior_inflation_swap_rate_pct="2.770000",
            breakeven_rate_pct="2.680000",
            consensus_inflation_rate_pct="2.760000",
            five_day_swap_change_bp="28.000000",
            volume_notional_usd_m="420.000000",
            data_timestamp=datetime(2026, 7, 4, 9, 45, tzinfo=timezone(timedelta(hours=-4))),
        ),
        observation(
            "rates-swap-inline",
            market_slug="us-cpi-below-forecast",
            swap_tenor="10y",
            inflation_swap_rate_pct="2.430000",
            prior_inflation_swap_rate_pct="2.390000",
            breakeven_rate_pct="2.410000",
            consensus_inflation_rate_pct="2.470000",
            five_day_swap_change_bp="4.000000",
            volume_notional_usd_m="280.000000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_rates_inflation_swap_breakout_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.breakout_count == d("2.000000")
    assert digest_report.breakeven_premium_count == d("2.000000")
    assert digest_report.consensus_gap_count == d("1.000000")
    assert digest_report.volume_confirmation_count == d("1.000000")
    assert digest_report.max_swap_change_bp == d("40.000000")
    assert digest_report.average_swap_rate_pct == d("2.966667")
    assert digest_report.breakout_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "rates_inflation_swap_breakout_blocked_present",
        "rates_inflation_swap_breakout_momentum_present",
        "rates_inflation_swap_breakout_breakeven_premium_present",
        "rates_inflation_swap_breakout_consensus_gap_present",
        "rates_inflation_swap_breakout_volume_confirmed_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "us-cpi-above-forecast",
        "us-pce-above-forecast",
        "us-cpi-below-forecast",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.breakout_status == "blocked"
    assert blocked.swap_rate_delta_pct == d("0.400000")
    assert blocked.swap_breakeven_spread_pct == d("0.780000")
    assert blocked.swap_consensus_gap_pct == d("0.920000")
    assert blocked.data_timestamp == datetime(2026, 7, 4, 13, 45, tzinfo=UTC)
    assert blocked.reason_codes == (
        "rates_inflation_swap_breakout_blocked",
        "rates_inflation_swap_breakout_breakeven_premium",
        "rates_inflation_swap_breakout_consensus_gap",
        "rates_inflation_swap_breakout_momentum",
        "rates_inflation_swap_breakout_volume_confirmed",
    )
    assert watch.breakout_status == "watch"
    assert watch.data_timestamp == datetime(2026, 7, 4, 13, 45, tzinfo=UTC)
    assert watch.reason_codes == (
        "rates_inflation_swap_breakout_breakeven_premium",
        "rates_inflation_swap_breakout_momentum",
        "rates_inflation_swap_breakout_watch",
    )
    assert passed.breakout_status == "pass"
    assert passed.reason_codes == ("rates_inflation_swap_breakout_inline",)


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "rates-watch-b",
        market_slug="zeta-watch",
        swap_tenor="5y",
        inflation_swap_rate_pct="3.000000",
        prior_inflation_swap_rate_pct="2.740000",
        breakeven_rate_pct="2.680000",
        consensus_inflation_rate_pct="2.760000",
        five_day_swap_change_bp="26.000000",
        volume_notional_usd_m="320.000000",
    )
    second = observation(
        "rates-blocked",
        market_slug="alpha-blocked",
        swap_tenor="2y",
        inflation_swap_rate_pct="3.440000",
        prior_inflation_swap_rate_pct="3.010000",
        breakeven_rate_pct="2.600000",
        consensus_inflation_rate_pct="2.480000",
        five_day_swap_change_bp="43.000000",
        volume_notional_usd_m="925.000000",
    )
    third = observation(
        "rates-watch-a",
        market_slug="alpha-watch",
        swap_tenor="5y",
        inflation_swap_rate_pct="3.010000",
        prior_inflation_swap_rate_pct="2.750000",
        breakeven_rate_pct="2.680000",
        consensus_inflation_rate_pct="2.760000",
        five_day_swap_change_bp="26.000000",
        volume_notional_usd_m="320.000000",
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
    assert forward.reason_codes == (
        "rates_inflation_swap_breakout_blocked_present",
        "rates_inflation_swap_breakout_momentum_present",
        "rates_inflation_swap_breakout_breakeven_premium_present",
        "rates_inflation_swap_breakout_consensus_gap_present",
        "rates_inflation_swap_breakout_volume_confirmed_present",
    )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "rates_inflation_swap_breakout_blocked_present",
        "rates_inflation_swap_breakout_momentum_present",
        "rates_inflation_swap_breakout_breakeven_premium_present",
        "rates_inflation_swap_breakout_consensus_gap_present",
        "rates_inflation_swap_breakout_volume_confirmed_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_breakout_risk() -> None:
    module = digest()
    cfg = module.RatesInflationSwapBreakoutDigestConfig(
        watch_swap_change_bp=d("35.000000"),
        blocked_swap_change_bp=d("55.000000"),
        breakeven_premium_pct=d("0.500000"),
        consensus_gap_pct=d("0.700000"),
        volume_confirmation_usd_m=d("900.000000"),
    )

    digest_report = report(
        observation(
            "rates-moderate",
            inflation_swap_rate_pct="3.060000",
            prior_inflation_swap_rate_pct="2.780000",
            breakeven_rate_pct="2.720000",
            consensus_inflation_rate_pct="2.760000",
            five_day_swap_change_bp="28.000000",
            volume_notional_usd_m="640.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_rates_inflation_swap_breakout_screening"
    )
    assert digest_report.rows[0].breakout_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "rates_inflation_swap_breakout_inline",
    )
    assert digest_report.breakout_risk_score == d("0.000000")
    assert digest_report.reason_codes == (
        "rates_inflation_swap_breakout_digest_clear",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="inflation_swap_rate_pct must be a Decimal"):
        observation(inflation_swap_rate_pct=_DecimalSubclass("3.420000"))
    with pytest.raises(ValueError, match="volume_notional_usd_m must be positive"):
        observation(volume_notional_usd_m="0.000000")
    with pytest.raises(ValueError, match="five_day_swap_change_bp must be nonnegative"):
        observation(five_day_swap_change_bp="-1.000000")
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 4, 13, 45))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_rates_inflation_swap_breakout_digest(
            (),
            config=module.RatesInflationSwapBreakoutDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 14, 15, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("rates-dupe"), observation("rates-dupe"))
    with pytest.raises(ValueError, match="watch_swap_change_bp"):
        module.RatesInflationSwapBreakoutDigestConfig(
            watch_swap_change_bp=d("60.000000"),
            blocked_swap_change_bp=d("50.000000"),
        )

    valid_row = report(observation("rates-valid")).rows[0]
    with pytest.raises(ValueError, match="swap_rate_delta_pct must match"):
        replace(valid_row, swap_rate_delta_pct=d("9.990000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "rates_inflation_swap_breakout_inline",
                "rates_inflation_swap_breakout_momentum",
            ),
        )

    frozen_observation = observation("rates-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_and_report() -> None:
    module = digest()

    digest_report = report(observation("rates-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.RatesInflationSwapBreakoutDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("rates-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("rates-payload"))

    payload = module.market_research_rates_inflation_swap_breakout_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["inflation_swap_rate_pct"] == "3.420000"
    assert payload["rows"][0]["data_timestamp"] == "2026-07-04T13:45:00+00:00"

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
        module.RatesInflationSwapBreakoutDigestConfig(),
        observation("rates-dataclass"),
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

    source = Path(
        "src/polymarket_alpha_lab/market_research_rates_inflation_swap_breakout_digest.py",
    ).read_text()
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
