from __future__ import annotations

import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> ModuleType:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_fx_carry_unwind_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "market-research-fx-carry-unwind-digest-v0",
        "watch_unwind_score": d("0.400000"),
        "blocked_unwind_score": d("0.750000"),
        "max_source_age_seconds": d("900.000000"),
        "stale_confidence_cap": d("0.350000"),
        "calm_confidence_cap": d("0.600000"),
    }
    values.update(overrides)
    return module.FXCarryUnwindDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    market_slug: str = "jpy-carry-unwind-watch",
    carry_pair: str = "aud-jpy",
    funding_currency: str = "jpy",
    target_currency: str = "aud",
    spot_return_pct: Decimal = d("-0.020000"),
    rate_differential_pct: Decimal = d("0.050000"),
    volatility_z_score: Decimal = d("2.000000"),
    funding_currency_strength_pct: Decimal = d("0.010000"),
    liquidity_stress_ratio: Decimal = d("0.500000"),
    observed_at: datetime = GENERATED_AT - timedelta(seconds=1200),
    base_confidence: Decimal = d("0.850000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.FXCarryUnwindObservation(
        source_id=source_id,
        market_slug=market_slug,
        carry_pair=carry_pair,
        funding_currency=funding_currency,
        target_currency=target_currency,
        spot_return_pct=spot_return_pct,
        rate_differential_pct=rate_differential_pct,
        volatility_z_score=volatility_z_score,
        funding_currency_strength_pct=funding_currency_strength_pct,
        liquidity_stress_ratio=liquidity_stress_ratio,
        observed_at=observed_at,
        base_confidence=base_confidence,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(inputs: tuple[Any, ...], *, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_research_fx_carry_unwind_digest(
        inputs,
        config=config(),
        generated_at=generated_at,
    )


def clone_report(report: Any, **overrides: object) -> Any:
    values = {field.name: getattr(report, field.name) for field in fields(type(report))}
    values.update(overrides)
    return type(report)(**values)


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail(f"public payload must not contain floats: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_no_floats(item)


def test_builds_report_only_fx_carry_unwind_digest_with_decimal_sorting_and_reasons() -> None:
    report = digest(
        (
            observation(
                "beta-calm",
                market_slug="aud-jpy-carry-resilient",
                spot_return_pct=d("0.005000"),
                volatility_z_score=d("0.400000"),
                funding_currency_strength_pct=d("-0.001000"),
                liquidity_stress_ratio=d("0.100000"),
                observed_at=GENERATED_AT - timedelta(seconds=60),
                upstream_reason_codes=("desk_note",),
            ),
            observation(
                "alpha-watch",
                observed_at=GENERATED_AT - timedelta(seconds=1200),
            ),
            observation(
                "zeta-blocked",
                market_slug="mxn-jpy-carry-unwind",
                carry_pair="mxn-jpy",
                target_currency="mxn",
                spot_return_pct=d("-0.040000"),
                volatility_z_score=d("3.200000"),
                funding_currency_strength_pct=d("0.030000"),
                liquidity_stress_ratio=d("0.900000"),
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    7,
                    59,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                upstream_reason_codes=("macro_shock",),
            ),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-research-fx-carry-unwind-digest-v0"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_unwind_count == d("1.000000")
    assert report.watch_unwind_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.carry_unwind_count == d("2.000000")
    assert report.max_unwind_score == d("0.775000")
    assert report.average_unwind_score == d("0.408333")
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_fx_carry_unwind_digest"
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert [
        (row.source_id, row.unwind_status, row.unwind_score)
        for row in report.rows
    ] == [
        ("zeta-blocked", "blocked", d("0.775000")),
        ("alpha-watch", "watch", d("0.400000")),
        ("beta-calm", "pass", d("0.050000")),
    ]

    blocked, watch, passed = report.rows
    assert blocked.observed_at == datetime(2026, 7, 4, 11, 59, tzinfo=UTC)
    assert blocked.source_age_seconds == d("60.000000")
    assert blocked.unwind_direction == "carry_unwind"
    assert blocked.capped_confidence == d("0.850000")
    assert blocked.reason_codes == (
        "carry_unwind_blocked",
        "funding_currency_strength",
        "liquidity_stress_high",
        "macro_shock",
        "source_fresh",
        "spot_carry_drawdown",
        "volatility_pressure_high",
    )
    assert watch.unwind_direction == "carry_unwind"
    assert watch.source_age_seconds == d("1200.000000")
    assert watch.confidence_cap == d("0.350000")
    assert watch.capped_confidence == d("0.350000")
    assert watch.reason_codes == (
        "carry_unwind_watch",
        "source_stale",
        "spot_carry_drawdown",
    )
    assert passed.unwind_direction == "carry_resilient"
    assert passed.confidence_cap == d("0.600000")
    assert passed.capped_confidence == d("0.600000")
    assert passed.reason_codes == (
        "carry_unwind_calm",
        "desk_note",
        "source_fresh",
    )
    assert report.reason_codes == (
        "carry_unwind_blocked",
        "carry_unwind_calm",
        "carry_unwind_watch",
        "desk_note",
        "funding_currency_strength",
        "liquidity_stress_high",
        "macro_shock",
        "source_fresh",
        "source_stale",
        "spot_carry_drawdown",
        "volatility_pressure_high",
    )
    assert report.reason_code_counts[0].reason_code == "carry_unwind_blocked"
    assert report.reason_code_counts[0].count == d("1.000000")
    assert report.reason_code_counts[0].row_ratio == d("0.333333")


def test_empty_digest_and_payload_are_decimal_stringed_report_only_readonly() -> None:
    module = api()
    report = digest(())
    payload = module.market_research_fx_carry_unwind_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_unwind_count == d("0.000000")
    assert report.max_unwind_score == d("0.000000")
    assert report.average_unwind_score == d("0.000000")
    assert report.digest_status == "blocked"
    assert report.reason_codes == ("fx_carry_unwind_digest_empty",)
    assert report.reason_code_counts == (
        module.FXCarryUnwindReasonCodeCount(
            reason_code="fx_carry_unwind_digest_empty",
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
    assert_no_floats(payload)


def test_extreme_unwind_factors_cap_score_at_one_without_rejecting_report() -> None:
    report = digest(
        (
            observation(
                "extreme-unwind",
                market_slug="jpy-carry-unwind-extreme",
                spot_return_pct=d("-0.500000"),
                volatility_z_score=d("8.000000"),
                funding_currency_strength_pct=d("0.120000"),
                liquidity_stress_ratio=d("1.000000"),
                observed_at=GENERATED_AT - timedelta(seconds=30),
            ),
        ),
    )

    assert report.row_count == d("1.000000")
    assert report.max_unwind_score == d("1.000000")
    assert report.average_unwind_score == d("1.000000")
    assert report.digest_status == "blocked"
    assert report.rows[0].unwind_score == d("1.000000")
    assert report.rows[0].unwind_status == "blocked"


def test_rejects_bad_public_types_datetimes_duplicates_future_rows_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="spot_return_pct"):
        observation(spot_return_pct=_DecimalSubclass("-0.010000"))

    with pytest.raises(ValueError, match="liquidity_stress_ratio"):
        observation(liquidity_stress_ratio=d("1.100000"))

    with pytest.raises(ValueError, match="watch_unwind_score"):
        config(watch_unwind_score=0.4)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="UTC-aware"):
        observation(
            observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))

    with pytest.raises(ValueError, match="config"):
        module.build_market_research_fx_carry_unwind_digest(
            (),
            config=False,  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        digest((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        digest((observation("dupe"), observation("dupe")))

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    report = digest((observation(),))
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]

    classes = (
        module.FXCarryUnwindDigestConfig,
        module.FXCarryUnwindObservation,
        module.FXCarryUnwindDigestRow,
        module.FXCarryUnwindReasonCodeCount,
        module.FXCarryUnwindDigestReport,
    )
    for type_ in classes:
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type


def test_public_dataclasses_reject_subclassing() -> None:
    module = api()

    for type_ in (
        module.FXCarryUnwindDigestConfig,
        module.FXCarryUnwindObservation,
        module.FXCarryUnwindDigestRow,
        module.FXCarryUnwindReasonCodeCount,
        module.FXCarryUnwindDigestReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{type_.__name__}", (type_,), {})


def test_constructors_reject_noncanonical_ordering_and_zero_reason_counts() -> None:
    module = api()
    report = digest(
        (
            observation("alpha-watch"),
            observation(
                "beta-calm",
                market_slug="aud-jpy-carry-resilient",
                spot_return_pct=d("0.005000"),
                volatility_z_score=d("0.400000"),
                funding_currency_strength_pct=d("-0.001000"),
                liquidity_stress_ratio=d("0.100000"),
                observed_at=GENERATED_AT - timedelta(seconds=60),
                upstream_reason_codes=("desk_note",),
            ),
        ),
    )

    with pytest.raises(ValueError, match="upstream_reason_codes.*canonical"):
        observation(upstream_reason_codes=("z_reason", "a_reason"))

    with pytest.raises(ValueError, match="count.*positive"):
        module.FXCarryUnwindReasonCodeCount(
            reason_code="manual_zero",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )

    with pytest.raises(ValueError, match="rows.*canonical"):
        clone_report(report, rows=tuple(reversed(report.rows)))

    with pytest.raises(ValueError, match="reason_codes.*canonical"):
        clone_report(report, reason_codes=tuple(reversed(report.reason_codes)))

    with pytest.raises(ValueError, match="reason_code_counts.*canonical"):
        clone_report(
            report,
            reason_code_counts=tuple(reversed(report.reason_code_counts)),
        )

    bad_count = module.FXCarryUnwindReasonCodeCount(
        reason_code=report.reason_code_counts[0].reason_code,
        count=d("2.000000"),
        row_ratio=d("1.000000"),
    )
    with pytest.raises(ValueError, match="reason_code_counts.*match rows"):
        clone_report(
            report,
            reason_code_counts=(bad_count, *report.reason_code_counts[1:]),
        )


def test_payload_rejects_tampered_nested_public_values() -> None:
    module = api()
    report = digest((observation(),))

    object.__setattr__(report.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.market_research_fx_carry_unwind_digest_payload(report)
    object.__setattr__(report.rows[0], "readonly", True)

    object.__setattr__(report.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        module.market_research_fx_carry_unwind_digest_payload(report)
    object.__setattr__(report.reason_code_counts[0], "report_only", True)

    object.__setattr__(report.rows[0], "source_age_seconds", d("1200.0000001"))
    with pytest.raises(ValueError, match="six decimals"):
        module.market_research_fx_carry_unwind_digest_payload(report)


def test_module_scope_is_pure_in_memory_without_live_or_durable_surfaces() -> None:
    source = inspect.getsource(api()).lower()

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
        "exchange",
        "auth",
        "api_key",
        "secret",
        "bearer",
        "token",
        "private_key",
        "post(",
        "put(",
        "delete(",
        "place_order",
        "cancel_order",
        "replace_order",
    ):
        assert forbidden not in source
