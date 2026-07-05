from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_equity_margin_pressure_digest import (
    DEFAULT_MARKET_RESEARCH_EQUITY_MARGIN_PRESSURE_DIGEST_CONFIG_VERSION,
    MarketResearchEquityMarginPressureDigestConfig,
    MarketResearchEquityMarginPressureDigestInput,
    MarketResearchEquityMarginPressureDigestReasonCodeCount,
    MarketResearchEquityMarginPressureDigestReport,
    MarketResearchEquityMarginPressureDigestRow,
    build_market_research_equity_margin_pressure_digest_report,
    market_research_equity_margin_pressure_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_equity_margin_pressure_digest.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchEquityMarginPressureDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_RESEARCH_EQUITY_MARGIN_PRESSURE_DIGEST_CONFIG_VERSION,
        "gross_margin_pressure_watch": d("0.020000"),
        "gross_margin_pressure_blocked": d("0.050000"),
        "operating_margin_pressure_watch": d("0.020000"),
        "operating_margin_pressure_blocked": d("0.040000"),
        "cost_inflation_watch": d("0.030000"),
        "pricing_power_floor": d("0.000000"),
        "stale_source_age_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return MarketResearchEquityMarginPressureDigestConfig(**values)


def observation(
    company_id: str = "company-alpha",
    *,
    sector: str = "software",
    gross_margin_change: Decimal = d("-0.010000"),
    operating_margin_change: Decimal = d("-0.010000"),
    input_cost_inflation: Decimal = d("0.010000"),
    pricing_power_change: Decimal = d("0.010000"),
    source_observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    reason_codes: tuple[str, ...] = ("margin_pressure_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEquityMarginPressureDigestInput:
    return MarketResearchEquityMarginPressureDigestInput(
        company_id=company_id,
        sector=sector,
        gross_margin_change=gross_margin_change,
        operating_margin_change=operating_margin_change,
        input_cost_inflation=input_cost_inflation,
        pricing_power_change=pricing_power_change,
        source_observed_at=source_observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: MarketResearchEquityMarginPressureDigestInput,
    cfg: MarketResearchEquityMarginPressureDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEquityMarginPressureDigestReport:
    return build_market_research_equity_margin_pressure_digest_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_clear_margin_pressure_report_uses_decimal_payload_strings() -> None:
    digest = report(observation("company-clear"))

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.generated_at.tzinfo is UTC
    assert digest.config_version == (
        DEFAULT_MARKET_RESEARCH_EQUITY_MARGIN_PRESSURE_DIGEST_CONFIG_VERSION
    )
    assert digest.company_count == d("1.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.status == "pass"
    assert digest.reason_codes == ("equity_margin_pressure_digest_clear",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    row = digest.company_rows[0]
    assert row.company_id == "company-clear"
    assert row.pressure_status == "pass"
    assert row.margin_pressure_score == d("0.000000")
    assert row.source_age_seconds == d("3600.000000")
    assert row.reason_codes == (
        "margin_pressure_clear",
        "margin_pressure_input_available",
    )

    payload = market_research_equity_margin_pressure_digest_payload(digest)
    assert payload["company_count"] == "1.000000"
    assert payload["company_rows"][0]["margin_pressure_score"] == "0.000000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    digest = report()

    assert digest.status == "blocked"
    assert digest.company_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.mean_margin_pressure_score == ZERO
    assert digest.max_margin_pressure_score == ZERO
    assert digest.reason_codes == (
        "market_research_equity_margin_pressure_digest_no_inputs",
    )
    assert digest.reason_code_counts == (
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="market_research_equity_margin_pressure_digest_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert digest.company_rows == ()


def test_utc_normalization_for_generated_and_source_times() -> None:
    digest = report(
        observation(
            source_observed_at=datetime(
                2026,
                7,
                4,
                7,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            4,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert digest.generated_at == GENERATED_AT
    assert digest.company_rows[0].source_observed_at == datetime(
        2026,
        7,
        4,
        11,
        0,
        tzinfo=UTC,
    )
    assert digest.company_rows[0].source_age_seconds == d("3600.000000")


def test_naive_datetimes_are_rejected_at_phase1_boundary() -> None:
    with pytest.raises(ValueError, match="source_observed_at"):
        observation(source_observed_at=datetime(2026, 7, 4, 11, 0))

    with pytest.raises(ValueError, match="generated_at"):
        report(observation("aware-source"), generated_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="source_observed_at"):
        observation(
            source_observed_at=datetime(
                2026,
                7,
                4,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )


def test_margin_pressure_watch_and_blocked_reason_codes_roll_up() -> None:
    digest = report(
        observation(
            "company-watch",
            gross_margin_change=d("-0.030000"),
            operating_margin_change=d("-0.010000"),
            input_cost_inflation=d("0.040000"),
            pricing_power_change=d("0.010000"),
            source_observed_at=GENERATED_AT - timedelta(days=2),
        ),
        observation(
            "company-blocked",
            gross_margin_change=d("-0.060000"),
            operating_margin_change=d("-0.050000"),
            input_cost_inflation=d("0.020000"),
            pricing_power_change=d("-0.010000"),
        ),
    )

    assert digest.status == "blocked"
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.stale_source_count == d("1.000000")
    assert digest.mean_margin_pressure_score == d("0.070000")
    assert digest.reason_codes == (
        "equity_margin_pressure_digest_blocked",
        "cost_inflation_watch",
        "gross_margin_pressure_blocked",
        "gross_margin_pressure_watch",
        "operating_margin_pressure_blocked",
        "pricing_power_negative_blocked",
        "source_stale_watch",
    )
    assert digest.company_rows[0].company_id == "company-blocked"
    assert digest.company_rows[0].reason_codes == (
        "gross_margin_pressure_blocked",
        "margin_pressure_input_available",
        "operating_margin_pressure_blocked",
        "pricing_power_negative_blocked",
    )
    assert digest.company_rows[1].reason_codes == (
        "cost_inflation_watch",
        "gross_margin_pressure_watch",
        "margin_pressure_input_available",
        "source_stale_watch",
    )


def test_deterministic_sorting_and_reason_code_counts() -> None:
    digest = report(
        observation(
            "zeta-watch",
            gross_margin_change=d("-0.030000"),
            input_cost_inflation=d("0.040000"),
        ),
        observation(
            "beta-blocked",
            gross_margin_change=d("-0.060000"),
            operating_margin_change=d("-0.050000"),
        ),
        observation(
            "alpha-pass",
            gross_margin_change=d("0.010000"),
            reason_codes=("margin_pressure_input_available", "margin_trend_improving"),
        ),
        observation(
            "alpha-blocked",
            pricing_power_change=d("-0.010000"),
        ),
    )

    assert tuple(row.company_id for row in digest.company_rows) == (
        "beta-blocked",
        "alpha-blocked",
        "zeta-watch",
        "alpha-pass",
    )
    assert digest.reason_code_counts == (
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="margin_pressure_input_available",
            count=d("4.000000"),
        ),
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="cost_inflation_watch",
            count=d("1.000000"),
        ),
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="gross_margin_pressure_blocked",
            count=d("1.000000"),
        ),
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="gross_margin_pressure_watch",
            count=d("1.000000"),
        ),
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="margin_pressure_clear",
            count=d("1.000000"),
        ),
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="margin_trend_improving",
            count=d("1.000000"),
        ),
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="operating_margin_pressure_blocked",
            count=d("1.000000"),
        ),
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="pricing_power_negative_blocked",
            count=d("1.000000"),
        ),
    )


def test_hard_flags_frozen_dataclasses_and_decimal_public_numbers() -> None:
    digest = report(observation("frozen"))

    assert is_dataclass(MarketResearchEquityMarginPressureDigestConfig)
    assert is_dataclass(MarketResearchEquityMarginPressureDigestInput)
    assert is_dataclass(MarketResearchEquityMarginPressureDigestRow)
    assert is_dataclass(MarketResearchEquityMarginPressureDigestReasonCodeCount)
    assert is_dataclass(MarketResearchEquityMarginPressureDigestReport)
    with pytest.raises(FrozenInstanceError):
        digest.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.company_rows[0].margin_pressure_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)

    for item in (digest, *digest.company_rows, *digest.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name
    for field_name in (
        "company_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "gross_margin_pressure_count",
        "operating_margin_pressure_count",
        "cost_inflation_watch_count",
        "stale_source_count",
        "mean_margin_pressure_score",
        "max_margin_pressure_score",
    ):
        assert type(getattr(digest, field_name)) is Decimal


def test_public_dataclasses_reject_subclassing_and_subclass_instances() -> None:
    digest = report(observation("exact-type"))
    public_values = (
        config(),
        observation("exact-input"),
        digest.company_rows[0],
        digest.reason_code_counts[0],
        digest,
    )

    for value in public_values:
        public_type = type(value)
        kwargs = {field.name: getattr(value, field.name) for field in fields(value)}

        with pytest.raises(TypeError, match="may not be subclassed"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})

        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)


def test_constructors_reject_noncanonical_sequences_and_zero_reason_counts() -> None:
    with pytest.raises(ValueError, match="canonical sequence"):
        observation(
            reason_codes=(
                "margin_trend_improving",
                "margin_pressure_input_available",
            ),
        )

    with pytest.raises(ValueError, match="canonical sequence"):
        MarketResearchEquityMarginPressureDigestRow(
            company_id="row-sequence",
            sector="software",
            pressure_status="watch",
            gross_margin_change=d("-0.030000"),
            operating_margin_change=d("-0.010000"),
            input_cost_inflation=d("0.010000"),
            pricing_power_change=d("0.010000"),
            margin_pressure_score=d("0.030000"),
            source_observed_at=GENERATED_AT - timedelta(hours=1),
            source_age_seconds=d("3600.000000"),
            reason_codes=(
                "margin_pressure_input_available",
                "gross_margin_pressure_watch",
            ),
        )

    digest = report(
        observation(
            "zeta-watch",
            gross_margin_change=d("-0.030000"),
        ),
        observation("alpha-pass"),
    )
    with pytest.raises(ValueError, match="company_rows"):
        replace(digest, company_rows=tuple(reversed(digest.company_rows)))

    with pytest.raises(ValueError, match="count"):
        MarketResearchEquityMarginPressureDigestReasonCodeCount(
            reason_code="manual_zero",
            count=ZERO,
        )


def test_validation_errors_cover_inputs_config_payload_and_consistency() -> None:
    with pytest.raises(ValueError, match="gross_margin_pressure_watch"):
        config(gross_margin_pressure_watch=d("-0.000001"))
    with pytest.raises(ValueError, match="gross_margin_pressure_watch"):
        config(
            gross_margin_pressure_watch=d("0.060000"),
            gross_margin_pressure_blocked=d("0.050000"),
        )
    with pytest.raises(ValueError, match="cost_inflation_watch"):
        config(cost_inflation_watch=_DecimalSubclass("0.030000"))
    with pytest.raises(ValueError, match="company_id"):
        observation(company_id=" company")
    with pytest.raises(ValueError, match="sector"):
        observation(sector="")
    with pytest.raises(ValueError, match="gross_margin_change"):
        observation(gross_margin_change=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="input_cost_inflation"):
        observation(input_cost_inflation=d("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_observed_at"):
        report(observation(source_observed_at=GENERATED_AT + timedelta(seconds=1)))

    digest = report(observation("consistent"))
    with pytest.raises(ValueError, match="company_count"):
        replace(digest, company_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="blocked")
    with pytest.raises(ValueError, match="gross_margin_pressure_count"):
        replace(digest, gross_margin_pressure_count=d("2.000000"))
    with pytest.raises(ValueError, match="mean_margin_pressure_score"):
        replace(digest, mean_margin_pressure_score=d("2.000000"))
    with pytest.raises(ValueError, match="unsafe"):
        observation(company_id="wallet_company")
    with pytest.raises(
        ValueError,
        match="MarketResearchEquityMarginPressureDigestReport",
    ):
        market_research_equity_margin_pressure_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "company_count": 1.0,
            },
        )
    with pytest.raises(
        ValueError,
        match="MarketResearchEquityMarginPressureDigestReport",
    ):
        market_research_equity_margin_pressure_digest_payload(
            {"paper_only": False, "report_only": True, "readonly": True},
        )

    with pytest.raises(
        ValueError,
        match="MarketResearchEquityMarginPressureDigestReport",
    ):
        market_research_equity_margin_pressure_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "company_count": d("1"),
            },
        )
    with pytest.raises(
        ValueError,
        match="MarketResearchEquityMarginPressureDigestReport",
    ):
        market_research_equity_margin_pressure_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "nested": {"margin_pressure_score": d("0.1000000")},
            },
        )
    with pytest.raises(
        ValueError,
        match="MarketResearchEquityMarginPressureDigestReport",
    ):
        market_research_equity_margin_pressure_digest_payload(
            [("company_count", d("1.000000"))],  # type: ignore[arg-type]
        )
    with pytest.raises(
        ValueError,
        match="MarketResearchEquityMarginPressureDigestReport",
    ):
        market_research_equity_margin_pressure_digest_payload(object())  # type: ignore[arg-type]


def test_payload_revalidates_nested_report_dataclasses_after_tampering() -> None:
    digest = report(observation("tampered-row-shape"))
    row_payload = market_research_equity_margin_pressure_digest_payload(digest)[
        "company_rows"
    ][0]
    object.__setattr__(digest, "company_rows", (row_payload,))
    with pytest.raises(ValueError, match="company_rows"):
        market_research_equity_margin_pressure_digest_payload(digest)

    digest = report(observation("tampered-row-decimal"))
    object.__setattr__(
        digest.company_rows[0],
        "margin_pressure_score",
        d("0.0000000"),
    )
    with pytest.raises(ValueError, match="six decimal"):
        market_research_equity_margin_pressure_digest_payload(digest)

    digest = report(observation("tampered-row-time"))
    object.__setattr__(
        digest.company_rows[0],
        "source_observed_at",
        datetime(
            2026,
            7,
            4,
            7,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )
    with pytest.raises(ValueError, match="UTC"):
        market_research_equity_margin_pressure_digest_payload(digest)

    digest = report(observation("tampered-row-flag"))
    object.__setattr__(digest.company_rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_equity_margin_pressure_digest_payload(digest)

    digest = report(observation("tampered-reason-count"))
    object.__setattr__(digest.reason_code_counts[0], "count", ZERO)
    with pytest.raises(ValueError, match="count"):
        market_research_equity_margin_pressure_digest_payload(digest)


def test_public_exports_are_exact() -> None:
    import polymarket_alpha_lab.market_research_equity_margin_pressure_digest as digest

    assert digest.__all__ == (
        "DEFAULT_MARKET_RESEARCH_EQUITY_MARGIN_PRESSURE_DIGEST_CONFIG_VERSION",
        "MarketResearchEquityMarginPressureDigestConfig",
        "MarketResearchEquityMarginPressureDigestInput",
        "MarketResearchEquityMarginPressureDigestReasonCodeCount",
        "MarketResearchEquityMarginPressureDigestReport",
        "MarketResearchEquityMarginPressureDigestRow",
        "build_market_research_equity_margin_pressure_digest_report",
        "market_research_equity_margin_pressure_digest_payload",
    )


def test_static_forbidden_surface_terms_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_dataclass_helpers = {"asdict"}
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", *forbidden_dataclass_helpers}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(
                alias.name not in forbidden_dataclass_helpers
                for alias in node.names
            )


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]
