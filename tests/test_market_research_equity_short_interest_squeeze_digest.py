import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: object) -> None:
        return None

    def dst(self, dt: object) -> None:
        return None


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_equity_short_interest_squeeze_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "short-interest-nvda",
    *,
    equity_symbol: str = "nvda",
    market_slug: str = "nvda-short-interest-squeeze",
    short_interest_ratio: str | Decimal = "0.040000",
    days_to_cover: str | Decimal = "1.200000",
    borrow_fee_rate: str | Decimal = "0.040000",
    five_day_price_return_pct: str | Decimal = "0.020000",
    float_uncertainty_ratio: str | Decimal = "0.010000",
    source_count: str | Decimal = "3.000000",
    data_timestamp: datetime = datetime(2026, 7, 4, 15, 55, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("public_short_interest_release",),
):
    module = digest()
    return module.MarketResearchEquityShortInterestSqueezeDigestObservation(
        source_id=source_id,
        equity_symbol=equity_symbol,
        market_slug=market_slug,
        short_interest_ratio=(
            short_interest_ratio
            if isinstance(short_interest_ratio, Decimal)
            else d(short_interest_ratio)
        ),
        days_to_cover=days_to_cover if isinstance(days_to_cover, Decimal) else d(days_to_cover),
        borrow_fee_rate=(
            borrow_fee_rate if isinstance(borrow_fee_rate, Decimal) else d(borrow_fee_rate)
        ),
        five_day_price_return_pct=(
            five_day_price_return_pct
            if isinstance(five_day_price_return_pct, Decimal)
            else d(five_day_price_return_pct)
        ),
        float_uncertainty_ratio=(
            float_uncertainty_ratio
            if isinstance(float_uncertainty_ratio, Decimal)
            else d(float_uncertainty_ratio)
        ),
        source_count=source_count if isinstance(source_count, Decimal) else d(source_count),
        data_timestamp=data_timestamp,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    config = (
        module.MarketResearchEquityShortInterestSqueezeDigestConfig()
        if cfg is None
        else cfg
    )
    return module.build_market_research_equity_short_interest_squeeze_digest(
        rows,
        config=config,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(
        digest_report,
        module.MarketResearchEquityShortInterestSqueezeDigestReport,
    )
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-equity-short-interest-squeeze-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_equity_short_interest_squeeze_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.high_short_interest_count == d("0.000000")
    assert digest_report.extreme_short_interest_count == d("0.000000")
    assert digest_report.high_days_to_cover_count == d("0.000000")
    assert digest_report.extreme_days_to_cover_count == d("0.000000")
    assert digest_report.high_borrow_fee_count == d("0.000000")
    assert digest_report.extreme_borrow_fee_count == d("0.000000")
    assert digest_report.rally_confirmation_count == d("0.000000")
    assert digest_report.thin_source_count == d("0.000000")
    assert digest_report.stale_observation_count == d("0.000000")
    assert digest_report.float_uncertainty_count == d("0.000000")
    assert digest_report.max_short_interest_ratio == d("0.000000")
    assert digest_report.average_short_interest_ratio == d("0.000000")
    assert digest_report.max_days_to_cover == d("0.000000")
    assert digest_report.average_days_to_cover == d("0.000000")
    assert digest_report.max_borrow_fee_rate == d("0.000000")
    assert digest_report.average_borrow_fee_rate == d("0.000000")
    assert digest_report.squeeze_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "equity_short_interest_squeeze_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.MarketResearchEquityShortInterestSqueezeReasonCodeCount(
            reason_code="equity_short_interest_squeeze_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_short_interest_squeeze_blocks_probability_event_screening() -> None:
    digest_report = report(
        observation(
            "short-interest-gme",
            equity_symbol="gme",
            market_slug="gme-short-interest-squeeze",
            short_interest_ratio="0.310000",
            days_to_cover="8.500000",
            borrow_fee_rate="0.620000",
            five_day_price_return_pct="0.180000",
            float_uncertainty_ratio="0.020000",
            source_count="1.000000",
            data_timestamp=datetime(2026, 7, 4, 15, 30, tzinfo=UTC),
        ),
        observation(
            "short-interest-tsla",
            equity_symbol="tsla",
            market_slug="tsla-short-interest-squeeze",
            short_interest_ratio="0.180000",
            days_to_cover="4.000000",
            borrow_fee_rate="0.230000",
            five_day_price_return_pct="0.030000",
            float_uncertainty_ratio="0.020000",
            source_count="2.000000",
            data_timestamp=datetime(
                2026,
                7,
                4,
                11,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "short-interest-msft",
            equity_symbol="msft",
            market_slug="msft-short-interest-squeeze",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_equity_short_interest_squeeze_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.high_short_interest_count == d("2.000000")
    assert digest_report.extreme_short_interest_count == d("1.000000")
    assert digest_report.high_days_to_cover_count == d("2.000000")
    assert digest_report.extreme_days_to_cover_count == d("1.000000")
    assert digest_report.high_borrow_fee_count == d("2.000000")
    assert digest_report.extreme_borrow_fee_count == d("1.000000")
    assert digest_report.rally_confirmation_count == d("1.000000")
    assert digest_report.thin_source_count == d("1.000000")
    assert digest_report.stale_observation_count == d("0.000000")
    assert digest_report.float_uncertainty_count == d("0.000000")
    assert digest_report.max_short_interest_ratio == d("0.310000")
    assert digest_report.average_short_interest_ratio == d("0.176667")
    assert digest_report.max_days_to_cover == d("8.500000")
    assert digest_report.average_days_to_cover == d("4.566667")
    assert digest_report.max_borrow_fee_rate == d("0.620000")
    assert digest_report.average_borrow_fee_rate == d("0.296667")
    assert digest_report.squeeze_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "equity_short_interest_squeeze_blocked_present",
        "equity_short_interest_squeeze_crowded_short_present",
        "equity_short_interest_squeeze_days_to_cover_present",
        "equity_short_interest_squeeze_borrow_stress_present",
        "equity_short_interest_squeeze_price_rally_present",
        "equity_short_interest_squeeze_data_quality_present",
    )
    assert tuple(row.equity_symbol for row in digest_report.rows) == (
        "gme",
        "tsla",
        "msft",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.squeeze_status == "blocked"
    assert blocked.observation_age_seconds == d("1800.000000")
    assert blocked.short_interest_excess_ratio == d("0.060000")
    assert blocked.days_to_cover_excess == d("1.500000")
    assert blocked.borrow_fee_excess_rate == d("0.120000")
    assert blocked.data_timestamp == datetime(2026, 7, 4, 15, 30, tzinfo=UTC)
    assert blocked.reason_codes == (
        "equity_short_interest_squeeze_extreme_short_interest",
        "equity_short_interest_squeeze_extreme_days_to_cover",
        "equity_short_interest_squeeze_extreme_borrow_fee",
        "equity_short_interest_squeeze_price_rally",
        "equity_short_interest_squeeze_thin_sources",
        "equity_short_interest_squeeze_blocked",
    )
    assert watch.squeeze_status == "watch"
    assert watch.data_timestamp == datetime(2026, 7, 4, 15, 45, tzinfo=UTC)
    assert watch.reason_codes == (
        "equity_short_interest_squeeze_high_short_interest",
        "equity_short_interest_squeeze_high_days_to_cover",
        "equity_short_interest_squeeze_high_borrow_fee",
        "equity_short_interest_squeeze_watch",
    )
    assert passed.squeeze_status == "pass"
    assert passed.reason_codes == ("equity_short_interest_squeeze_inline",)


def test_rows_reason_codes_and_manual_public_constructors_require_canonical_sequences() -> None:
    module = digest()
    first = observation(
        "short-interest-watch-b",
        equity_symbol="zeta",
        market_slug="zeta-short-interest-squeeze",
        short_interest_ratio="0.180000",
        days_to_cover="4.000000",
    )
    second = observation(
        "short-interest-blocked",
        equity_symbol="alpha",
        market_slug="alpha-short-interest-squeeze",
        short_interest_ratio="0.310000",
        days_to_cover="8.500000",
    )
    third = observation(
        "short-interest-watch-a",
        equity_symbol="beta",
        market_slug="beta-short-interest-squeeze",
        short_interest_ratio="0.180000",
        days_to_cover="4.000000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.equity_symbol for row in forward.rows) == ("alpha", "beta", "zeta")
    for row in forward.rows:
        assert row.reason_codes == tuple(
            sorted(row.reason_codes, key=module.ROW_REASON_CODES.index),
        )
    assert tuple(item.reason_code for item in forward.reason_code_counts) == (
        "equity_short_interest_squeeze_blocked_present",
        "equity_short_interest_squeeze_crowded_short_present",
        "equity_short_interest_squeeze_days_to_cover_present",
    )

    kwargs = {
        field.name: getattr(forward, field.name)
        for field in fields(module.MarketResearchEquityShortInterestSqueezeDigestReport)
    }
    with pytest.raises(ValueError, match="rows must be sorted"):
        module.MarketResearchEquityShortInterestSqueezeDigestReport(
            **{**kwargs, "rows": tuple(reversed(forward.rows))},
        )
    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        module.MarketResearchEquityShortInterestSqueezeDigestReport(
            **{**kwargs, "reason_code_counts": tuple(reversed(forward.reason_code_counts))},
        )
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        replace(forward.rows[0], reason_codes=tuple(reversed(forward.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="upstream_reason_codes must be sorted"):
        observation(upstream_reason_codes=("z-source", "a-source"))


def test_non_default_thresholds_can_downgrade_moderate_squeeze_risk() -> None:
    module = digest()
    cfg = module.MarketResearchEquityShortInterestSqueezeDigestConfig(
        watch_short_interest_ratio=d("0.400000"),
        blocked_short_interest_ratio=d("0.500000"),
        watch_days_to_cover=d("10.000000"),
        blocked_days_to_cover=d("20.000000"),
        watch_borrow_fee_rate=d("0.400000"),
        blocked_borrow_fee_rate=d("0.700000"),
        rally_confirmation_pct=d("0.250000"),
    )

    digest_report = report(
        observation(
            "short-interest-moderate",
            short_interest_ratio="0.180000",
            days_to_cover="4.000000",
            borrow_fee_rate="0.230000",
            five_day_price_return_pct="0.030000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_equity_short_interest_squeeze_screening"
    )
    assert digest_report.rows[0].squeeze_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "equity_short_interest_squeeze_inline",
    )
    assert digest_report.squeeze_risk_score == d("0.000000")
    assert digest_report.reason_codes == ("equity_short_interest_squeeze_digest_clear",)


def test_report_helper_rejects_false_config_instead_of_defaulting() -> None:
    with pytest.raises(ValueError, match="config must be exactly"):
        report(cfg=False)


def test_builder_accepts_explicit_none_config_as_default() -> None:
    module = digest()

    digest_report = module.build_market_research_equity_short_interest_squeeze_digest(
        (observation("short-interest-none-config"),),
        config=None,
        generated_at=GENERATED_AT,
    )

    assert digest_report.config_version == (
        "market-research-equity-short-interest-squeeze-digest-v0"
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_validation_rejects_bad_inputs_false_flags_subclasses_and_inconsistent_records() -> None:
    module = digest()

    for public_type in (
        module.MarketResearchEquityShortInterestSqueezeDigestConfig,
        module.MarketResearchEquityShortInterestSqueezeDigestObservation,
        module.MarketResearchEquityShortInterestSqueezeDigestRow,
        module.MarketResearchEquityShortInterestSqueezeReasonCodeCount,
        module.MarketResearchEquityShortInterestSqueezeDigestReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type("RejectedSubclass", (public_type,), {})

    with pytest.raises(ValueError, match="watch_short_interest_ratio must be a Decimal"):
        module.MarketResearchEquityShortInterestSqueezeDigestConfig(
            watch_short_interest_ratio=_DecimalSubclass("0.150000"),
        )
    with pytest.raises(ValueError, match="blocked_short_interest_ratio"):
        module.MarketResearchEquityShortInterestSqueezeDigestConfig(
            watch_short_interest_ratio=d("0.300000"),
            blocked_short_interest_ratio=d("0.250000"),
        )
    with pytest.raises(ValueError, match="source_id must be a string"):
        observation(source_id=_StringSubclass("short-interest-subclass"))
    with pytest.raises(ValueError, match="short_interest_ratio must be between zero and one"):
        observation(short_interest_ratio="1.100000")
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 4, 15, 55))
    with pytest.raises(ValueError, match="data_timestamp must be timezone-aware"):
        observation(data_timestamp=datetime(2026, 7, 4, 15, 55, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_equity_short_interest_squeeze_digest(
            (),
            config=module.MarketResearchEquityShortInterestSqueezeDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("short-interest-dupe"), observation("short-interest-dupe"))

    digest_report = report(observation("short-interest-valid"))
    valid_row = digest_report.rows[0]
    with pytest.raises(ValueError, match="short_interest_excess_ratio must match"):
        replace(valid_row, short_interest_excess_ratio=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "equity_short_interest_squeeze_high_short_interest",
                "equity_short_interest_squeeze_inline",
            ),
        )
    with pytest.raises(ValueError, match="count must be positive"):
        module.MarketResearchEquityShortInterestSqueezeReasonCodeCount(
            reason_code="equity_short_interest_squeeze_digest_clear",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.MarketResearchEquityShortInterestSqueezeDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("short-interest-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(valid_row, readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)

    frozen_observation = observation("short-interest-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_payload_uses_six_decimal_string_numerics_and_module_has_no_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("short-interest-payload"))

    payload = module.market_research_equity_short_interest_squeeze_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["short_interest_ratio"] == "0.040000"
    assert payload["rows"][0]["data_timestamp"] == "2026-07-04T15:55:00+00:00"
    with pytest.raises(ValueError, match="report must be exactly"):
        module.market_research_equity_short_interest_squeeze_digest_payload(
            {"paper_only": True, "report_only": True, "readonly": True},
        )

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "order" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.MarketResearchEquityShortInterestSqueezeDigestConfig(),
        observation("short-interest-dataclass"),
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
        "src/polymarket_alpha_lab/market_research_equity_short_interest_squeeze_digest.py",
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
        if isinstance(node, ast.Call):
            callee = ""
            if isinstance(node.func, ast.Name):
                callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee = node.func.attr
            assert callee not in {
                "open",
                "read",
                "write",
                "connect",
                "execute",
                "submit_order",
                "cancel_order",
                "replace_order",
            }
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlite",
        "pathlib",
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
        "exchange mutation",
    ):
        assert forbidden not in source.lower()


def test_payload_revalidates_nested_public_dataclasses_before_serializing() -> None:
    module = digest()

    row_flag_report = report(observation("short-interest-row-flag"))
    object.__setattr__(row_flag_report.rows[0], "report_only", False)
    with pytest.raises(ValueError, match="row report_only must be True"):
        module.market_research_equity_short_interest_squeeze_digest_payload(
            row_flag_report,
        )

    reason_count_flag_report = report(observation("short-interest-count-flag"))
    object.__setattr__(
        reason_count_flag_report.reason_code_counts[0],
        "readonly",
        False,
    )
    with pytest.raises(ValueError, match="reason code count readonly must be True"):
        module.market_research_equity_short_interest_squeeze_digest_payload(
            reason_count_flag_report,
        )

    row_decimal_report = report(observation("short-interest-row-decimal"))
    object.__setattr__(
        row_decimal_report.rows[0],
        "short_interest_ratio",
        Decimal("0.04"),
    )
    with pytest.raises(
        ValueError,
        match="short_interest_ratio must have exactly six decimal places",
    ):
        module.market_research_equity_short_interest_squeeze_digest_payload(
            row_decimal_report,
        )

    reason_count_decimal_report = report(observation("short-interest-count-decimal"))
    object.__setattr__(
        reason_count_decimal_report.reason_code_counts[0],
        "count",
        Decimal("1"),
    )
    with pytest.raises(ValueError, match="count must have exactly six decimal places"):
        module.market_research_equity_short_interest_squeeze_digest_payload(
            reason_count_decimal_report,
        )


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
