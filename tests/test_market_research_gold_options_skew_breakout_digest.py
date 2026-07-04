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


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_gold_options_skew_breakout_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "market-research-gold-options-skew-breakout-digest-v0"
        ),
        "watch_abs_skew_z_score": d("1.500000"),
        "blocked_abs_skew_z_score": d("2.500000"),
        "watch_implied_vol_change_pct": d("0.030000"),
        "watch_real_yield_beta_pressure": d("0.300000"),
        "watch_etf_flow_proxy": d("0.200000"),
        "watch_futures_oi_change_pct": d("0.040000"),
        "watch_pressure_score": d("0.500000"),
        "blocked_pressure_score": d("0.800000"),
        "max_source_age_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.GoldOptionsSkewBreakoutDigestConfig(**values)


def observation(
    venue: str = "cme",
    contract: str = "gc-aug26-risk-reversal",
    market_slug: str = "gold-options-skew-breakout",
    *,
    risk_reversal_skew_z_score: Decimal = d("3.000000"),
    implied_vol_change_pct: Decimal = d("0.060000"),
    real_yield_beta_pressure: Decimal = d("0.500000"),
    etf_flow_proxy: Decimal = d("0.300000"),
    futures_oi_change_pct: Decimal = d("0.070000"),
    source_timestamp: datetime = GENERATED_AT - timedelta(minutes=45),
    upstream_reason_codes: tuple[str, ...] = ("cme_surface",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.GoldOptionsSkewBreakoutObservation(
        venue=venue,
        contract=contract,
        market_slug=market_slug,
        risk_reversal_skew_z_score=risk_reversal_skew_z_score,
        implied_vol_change_pct=implied_vol_change_pct,
        real_yield_beta_pressure=real_yield_beta_pressure,
        etf_flow_proxy=etf_flow_proxy,
        futures_oi_change_pct=futures_oi_change_pct,
        source_timestamp=source_timestamp,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(*rows: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_gold_options_skew_breakout_digest(
        rows,
        config=config(),
        generated_at=generated_at,
    )


def assert_no_public_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_floats(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_floats(item)


def test_builds_deterministic_gold_options_skew_breakout_report() -> None:
    module = api()

    report = digest(
        observation(
            "lbma",
            "xau-spot-weekly-risk-reversal",
            "gold-spot-weekly-skew-watch",
            risk_reversal_skew_z_score=d("-1.500000"),
            implied_vol_change_pct=d("0.000000"),
            real_yield_beta_pressure=d("0.000000"),
            etf_flow_proxy=d("0.000000"),
            futures_oi_change_pct=d("0.000000"),
            source_timestamp=datetime(
                2026,
                7,
                3,
                11,
                10,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            upstream_reason_codes=(),
        ),
        observation(
            "comex",
            "gc-dec26-atm-straddle",
            "gold-options-skew-pass",
            risk_reversal_skew_z_score=d("0.500000"),
            implied_vol_change_pct=d("0.000000"),
            real_yield_beta_pressure=d("0.000000"),
            etf_flow_proxy=d("0.000000"),
            futures_oi_change_pct=d("0.000000"),
            source_timestamp=GENERATED_AT - timedelta(minutes=10),
            upstream_reason_codes=("desk_note",),
        ),
        observation(
            "cme",
            "gc-aug26-risk-reversal",
            "gold-options-skew-breakout",
            source_timestamp=datetime(
                2026,
                7,
                3,
                11,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            upstream_reason_codes=("cme_surface",),
        ),
    )

    assert isinstance(report, module.GoldOptionsSkewBreakoutDigestReport)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-gold-options-skew-breakout-digest-v0"
    )
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.max_abs_skew_z_score == d("3.000000")
    assert report.max_breakout_pressure_score == d("1.000000")
    assert report.average_breakout_pressure_score == d("0.440000")
    assert report.blocked_row_ratio == d("0.333333")
    assert report.report_risk_score == d("0.800000")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_gold_options_skew_breakout_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (
            row.venue,
            row.contract,
            row.breakout_status,
            row.breakout_pressure_score,
            row.abs_skew_z_score,
        )
        for row in report.rows
    ] == [
        (
            "cme",
            "gc-aug26-risk-reversal",
            "blocked",
            d("1.000000"),
            d("3.000000"),
        ),
        (
            "lbma",
            "xau-spot-weekly-risk-reversal",
            "watch",
            d("0.240000"),
            d("1.500000"),
        ),
        (
            "comex",
            "gc-dec26-atm-straddle",
            "pass",
            d("0.080000"),
            d("0.500000"),
        ),
    ]

    blocked = report.rows[0]
    assert blocked.source_timestamp == datetime(2026, 7, 3, 15, 30, tzinfo=UTC)
    assert blocked.source_age_seconds == d("1800.000000")
    assert blocked.skew_direction == "call"
    assert blocked.reason_codes == (
        "cme_surface",
        "gold_options_etf_flow_pressure_watch",
        "gold_options_futures_oi_pressure_watch",
        "gold_options_iv_pressure_watch",
        "gold_options_pressure_score_blocked",
        "gold_options_real_yield_pressure_watch",
        "gold_options_skew_blocked",
        "gold_options_skew_direction_call",
        "gold_options_source_fresh",
    )
    assert report.rows[1].skew_direction == "put"
    assert report.rows[1].reason_codes == (
        "gold_options_skew_direction_put",
        "gold_options_skew_watch",
        "gold_options_source_fresh",
    )
    assert report.rows[2].skew_direction == "neutral"
    assert report.rows[2].reason_codes == (
        "desk_note",
        "gold_options_pressure_pass",
        "gold_options_skew_direction_neutral",
        "gold_options_source_fresh",
    )

    assert report.reason_codes == (
        "cme_surface",
        "desk_note",
        "gold_options_etf_flow_pressure_watch",
        "gold_options_futures_oi_pressure_watch",
        "gold_options_iv_pressure_watch",
        "gold_options_pressure_pass",
        "gold_options_pressure_score_blocked",
        "gold_options_real_yield_pressure_watch",
        "gold_options_skew_blocked",
        "gold_options_skew_direction_call",
        "gold_options_skew_direction_neutral",
        "gold_options_skew_direction_put",
        "gold_options_skew_watch",
        "gold_options_source_fresh",
    )
    assert report.reason_code_counts == (
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="cme_surface",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="desk_note",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_etf_flow_pressure_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_futures_oi_pressure_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_iv_pressure_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_pressure_pass",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_pressure_score_blocked",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_real_yield_pressure_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_skew_blocked",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_skew_direction_call",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_skew_direction_neutral",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_skew_direction_put",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_skew_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_source_fresh",
            count=d("3.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_empty_digest_and_payload_are_report_only_decimal_stringed() -> None:
    module = api()

    report = digest()
    payload = module.market_research_gold_options_skew_breakout_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_gold_options_skew_breakout_digest"
    )
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.report_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("gold_options_skew_breakout_digest_empty",)
    assert report.reason_code_counts == (
        module.GoldOptionsSkewBreakoutReasonCodeCount(
            reason_code="gold_options_skew_breakout_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert payload["input_count"] == "0.000000"
    assert payload["report_risk_score"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_floats(payload)


def test_validates_public_types_thresholds_flags_duplicates_and_frozen_state() -> None:
    module = api()

    with pytest.raises(ValueError, match="risk_reversal_skew_z_score"):
        observation(risk_reversal_skew_z_score=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="implied_vol_change_pct"):
        observation(implied_vol_change_pct=0.01)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="source_timestamp must be UTC-aware"):
        observation(source_timestamp=datetime(2026, 7, 3, 15, 0))

    with pytest.raises(ValueError, match="source_timestamp must be a datetime"):
        observation(
            source_timestamp=_DatetimeSubclass(2026, 7, 3, 15, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="source_timestamp must not be after generated_at"):
        digest(observation(source_timestamp=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        digest(observation(), observation())

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    with pytest.raises(ValueError, match="blocked_abs_skew_z_score"):
        config(blocked_abs_skew_z_score=d("1.000000"))

    report = digest(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.GoldOptionsSkewBreakoutDigestConfig,
        module.GoldOptionsSkewBreakoutObservation,
        module.GoldOptionsSkewBreakoutDigestRow,
        module.GoldOptionsSkewBreakoutReasonCodeCount,
        module.GoldOptionsSkewBreakoutDigestReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            value = getattr(
                config() if type_.__name__.endswith("Config") else report,
                field.name,
                None,
            )
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type
    assert is_dataclass(report)


def test_module_is_pure_in_memory_without_forbidden_surfaces() -> None:
    source = inspect.getsource(api()).lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "os.environ",
        "open(",
        "path(",
        "connect(",
        "execute(",
        "private_key",
        "wallet",
        "place_order",
        "cancel_order",
        "replace_order",
        "auth",
    ):
        assert forbidden not in source
