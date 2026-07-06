from __future__ import annotations

import ast
import dataclasses
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_equity_single_stock_gap_risk_digest import (
    DEFAULT_MARKET_RESEARCH_EQUITY_SINGLE_STOCK_GAP_RISK_DIGEST_CONFIG_VERSION,
    MarketResearchEquitySingleStockGapRiskDigestConfig,
    MarketResearchEquitySingleStockGapRiskObservation,
    MarketResearchEquitySingleStockGapRiskReasonCodeCount,
    MarketResearchEquitySingleStockGapRiskReport,
    build_market_research_equity_single_stock_gap_risk_digest,
    market_research_equity_single_stock_gap_risk_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 5, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchEquitySingleStockGapRiskDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_EQUITY_SINGLE_STOCK_GAP_RISK_DIGEST_CONFIG_VERSION
        ),
        "max_source_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "min_confirmation_count": d("1.000000"),
        "material_gap_pct": d("0.050000"),
        "min_event_sensitivity_score": d("0.650000"),
        "max_acknowledgement_lag_seconds": d("900.000000"),
    }
    values.update(overrides)
    return MarketResearchEquitySingleStockGapRiskDigestConfig(**values)


def observation(
    research_key: str = "research.aapl.single_stock_gap",
    *,
    condition_id: str = "condition_aapl_gap_risk",
    equity_symbol: str = "AAPL",
    gap_event_id: str = "equity.aapl.20260705.preopen",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=20),
    acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    source_count: Decimal = d("3.000000"),
    confirmation_count: Decimal = d("1.000000"),
    gap_pct: Decimal = d("0.060000"),
    intraday_volatility_pct: Decimal = d("0.040000"),
    event_sensitivity_score: Decimal = d("0.700000"),
    contradiction_count: Decimal = ZERO,
    source_config_version: str = "single-stock-gap-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchEquitySingleStockGapRiskObservation:
    return MarketResearchEquitySingleStockGapRiskObservation(
        research_key=research_key,
        condition_id=condition_id,
        equity_symbol=equity_symbol,
        gap_event_id=gap_event_id,
        observed_at=observed_at,
        acknowledged_at=acknowledged_at,
        source_count=source_count,
        confirmation_count=confirmation_count,
        gap_pct=gap_pct,
        intraday_volatility_pct=intraday_volatility_pct,
        event_sensitivity_score=event_sensitivity_score,
        contradiction_count=contradiction_count,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[MarketResearchEquitySingleStockGapRiskObservation, ...],
    *,
    cfg: MarketResearchEquitySingleStockGapRiskDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEquitySingleStockGapRiskReport:
    return build_market_research_equity_single_stock_gap_risk_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_gap_risk_digest_summarizes_rows_sorts_and_payloads_strictly() -> None:
    digest_report = report(
        (
            observation(
                "research.msft.single_stock_gap",
                condition_id="condition_msft_gap_risk",
                equity_symbol="MSFT",
                gap_event_id="equity.msft.20260705.preopen",
                observed_at=GENERATED_AT - timedelta(minutes=10),
                acknowledged_at=GENERATED_AT - timedelta(minutes=9),
                confirmation_count=d("2.000000"),
                gap_pct=d("0.010000"),
                intraday_volatility_pct=d("0.020000"),
                event_sensitivity_score=d("0.300000"),
            ),
            observation(
                "research.tsla.single_stock_gap",
                condition_id="condition_tsla_gap_risk",
                equity_symbol="TSLA",
                gap_event_id="equity.tsla.20260705.preopen",
                observed_at=GENERATED_AT - timedelta(hours=3),
                acknowledged_at=None,
                source_count=d("1.000000"),
                confirmation_count=ZERO,
                gap_pct=d("-0.120000"),
                intraday_volatility_pct=d("0.090000"),
                event_sensitivity_score=d("0.880000"),
                contradiction_count=ONE,
            ),
            observation(
                observed_at=datetime(
                    2026,
                    7,
                    5,
                    9,
                    40,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                acknowledged_at=datetime(
                    2026,
                    7,
                    5,
                    9,
                    55,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
        ),
        generated_at=datetime(2026, 7, 5, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        DEFAULT_MARKET_RESEARCH_EQUITY_SINGLE_STOCK_GAP_RISK_DIGEST_CONFIG_VERSION
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_equity_single_stock_gap_risk_digest"
    )
    assert digest_report.event_count == d("3.000000")
    assert digest_report.ready_event_count == d("1.000000")
    assert digest_report.watch_event_count == d("1.000000")
    assert digest_report.blocked_event_count == d("1.000000")
    assert digest_report.material_gap_count == d("2.000000")
    assert digest_report.high_event_sensitivity_count == d("2.000000")
    assert digest_report.thin_source_count == d("1.000000")
    assert digest_report.missing_confirmation_count == d("1.000000")
    assert digest_report.missing_acknowledgement_count == d("1.000000")
    assert digest_report.slow_acknowledgement_count == ZERO
    assert digest_report.stale_source_count == d("1.000000")
    assert digest_report.contradiction_event_count == d("1.000000")
    assert digest_report.average_gap_abs_pct == d("0.063333")
    assert digest_report.max_gap_abs_pct == d("0.120000")
    assert digest_report.average_event_sensitivity_score == d("0.626667")
    assert digest_report.max_source_age_seconds == d("10800.000000")
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple((row.equity_symbol, row.gap_event_id) for row in digest_report.rows) == (
        ("TSLA", "equity.tsla.20260705.preopen"),
        ("AAPL", "equity.aapl.20260705.preopen"),
        ("MSFT", "equity.msft.20260705.preopen"),
    )

    blocked = digest_report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.gap_direction == "gap_down"
    assert blocked.observed_at == GENERATED_AT - timedelta(hours=3)
    assert blocked.acknowledged_at is None
    assert blocked.source_age_seconds == d("10800.000000")
    assert blocked.acknowledgement_lag_seconds is None
    assert blocked.gap_abs_pct == d("0.120000")
    assert blocked.reason_codes == (
        "market_research_equity_single_stock_gap_risk_digest_material_gap",
        "market_research_equity_single_stock_gap_risk_digest_high_event_sensitivity",
        "market_research_equity_single_stock_gap_risk_digest_thin_sources",
        "market_research_equity_single_stock_gap_risk_digest_missing_confirmation",
        "market_research_equity_single_stock_gap_risk_digest_missing_acknowledgement",
        "market_research_equity_single_stock_gap_risk_digest_stale_source",
        "market_research_equity_single_stock_gap_risk_digest_contradiction_present",
    )

    watch = digest_report.rows[1]
    assert watch.digest_status == "watch"
    assert watch.gap_direction == "gap_up"
    assert watch.observed_at == datetime(2026, 7, 5, 13, 40, tzinfo=UTC)
    assert watch.acknowledgement_lag_seconds == d("900.000000")
    assert watch.reason_codes == (
        "market_research_equity_single_stock_gap_risk_digest_material_gap",
        "market_research_equity_single_stock_gap_risk_digest_high_event_sensitivity",
    )

    ready = digest_report.rows[2]
    assert ready.digest_status == "ready"
    assert ready.reason_codes == (
        "market_research_equity_single_stock_gap_risk_digest_ready",
    )

    assert digest_report.reason_codes == (
        "market_research_equity_single_stock_gap_risk_digest_material_gap",
        "market_research_equity_single_stock_gap_risk_digest_high_event_sensitivity",
        "market_research_equity_single_stock_gap_risk_digest_thin_sources",
        "market_research_equity_single_stock_gap_risk_digest_missing_confirmation",
        "market_research_equity_single_stock_gap_risk_digest_missing_acknowledgement",
        "market_research_equity_single_stock_gap_risk_digest_stale_source",
        "market_research_equity_single_stock_gap_risk_digest_contradiction_present",
    )
    assert digest_report.reason_code_counts == (
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code="market_research_equity_single_stock_gap_risk_digest_material_gap",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code=(
                "market_research_equity_single_stock_gap_risk_digest_"
                "high_event_sensitivity"
            ),
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code="market_research_equity_single_stock_gap_risk_digest_thin_sources",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code=(
                "market_research_equity_single_stock_gap_risk_digest_"
                "missing_confirmation"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code=(
                "market_research_equity_single_stock_gap_risk_digest_"
                "missing_acknowledgement"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code="market_research_equity_single_stock_gap_risk_digest_stale_source",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code=(
                "market_research_equity_single_stock_gap_risk_digest_"
                "contradiction_present"
            ),
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )

    payload = market_research_equity_single_stock_gap_risk_digest_payload(digest_report)
    assert payload["generated_at"] == "2026-07-05T14:00:00+00:00"
    assert payload["event_count"] == "3.000000"
    assert payload["rows"][0]["gap_abs_pct"] == "0.120000"
    assert payload["rows"][0]["observed_at"] == "2026-07-05T11:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)
    assert_public_numeric_fields_are_exact_decimals(digest_report)
    for row in digest_report.rows:
        assert_public_numeric_fields_are_exact_decimals(row)


def test_empty_input_returns_blocked_report_only_digest() -> None:
    digest_report = report(())

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_market_research_equity_single_stock_gap_risk_digest"
    )
    assert digest_report.event_count == ZERO
    assert digest_report.ready_event_count == ZERO
    assert digest_report.watch_event_count == ZERO
    assert digest_report.blocked_event_count == ZERO
    assert digest_report.average_gap_abs_pct == ZERO
    assert digest_report.max_gap_abs_pct == ZERO
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "market_research_equity_single_stock_gap_risk_digest_no_inputs",
    )
    assert digest_report.reason_code_counts == (
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code="market_research_equity_single_stock_gap_risk_digest_no_inputs",
            count=ONE,
            event_ratio=ZERO,
        ),
    )


def test_exact_types_six_decimal_inputs_timestamps_tuples_flags_and_freezing() -> None:
    digest_report = report((observation(),))

    assert MarketResearchEquitySingleStockGapRiskDigestConfig.__dataclass_params__.frozen
    assert MarketResearchEquitySingleStockGapRiskObservation.__dataclass_params__.frozen
    assert MarketResearchEquitySingleStockGapRiskReasonCodeCount.__dataclass_params__.frozen
    assert MarketResearchEquitySingleStockGapRiskReport.__dataclass_params__.frozen

    with pytest.raises(TypeError, match="support subclassing"):

        class BadObservation(MarketResearchEquitySingleStockGapRiskObservation):
            pass

    with pytest.raises(FrozenInstanceError):
        digest_report.event_count = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        observation(source_count=_DecimalSubclass("3.000000"))
    with pytest.raises(ValueError, match="source_count must use exactly six decimal places"):
        observation(source_count=Decimal("3"))
    with pytest.raises(ValueError, match="gap_pct must use exactly six decimal places"):
        observation(gap_pct=Decimal("0.06"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 5, 13, 40))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(
            (observation(),),
            generated_at=_DateTimeSubclass(2026, 7, 5, 14, 0, tzinfo=UTC),
        )
    microsecond_report = report(
        (
            observation(
                observed_at=GENERATED_AT - timedelta(seconds=1, microseconds=1),
                acknowledged_at=GENERATED_AT,
            ),
        ),
    )
    assert microsecond_report.max_source_age_seconds == d("1.000001")
    assert microsecond_report.rows[0].source_age_seconds == d("1.000001")
    with pytest.raises(ValueError, match="observed_at cannot be after generated_at"):
        report((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="acknowledged_at cannot be after generated_at"):
        report((observation(acknowledged_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="acknowledged_at cannot be before observed_at"):
        report(
            (
                observation(
                    observed_at=GENERATED_AT - timedelta(minutes=5),
                    acknowledged_at=GENERATED_AT - timedelta(minutes=6),
                ),
            ),
        )
    with pytest.raises(ValueError, match="observations must be a tuple"):
        build_market_research_equity_single_stock_gap_risk_digest(
            [observation()],  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="observation readonly must be True"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="report report_only must be True"):
        replace(digest_report, report_only=False)


def test_reason_counts_reconcile_and_payload_revalidates_nested_dataclasses() -> None:
    digest_report = report((observation(),))

    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchEquitySingleStockGapRiskReasonCodeCount(
            reason_code="market_research_equity_single_stock_gap_risk_digest_ready",
            count=ZERO,
            event_ratio=ZERO,
        )

    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(
            digest_report,
            reason_code_counts=(
                MarketResearchEquitySingleStockGapRiskReasonCodeCount(
                    reason_code="market_research_equity_single_stock_gap_risk_digest_ready",
                    count=d("2.000000"),
                    event_ratio=ONE,
                ),
            ),
        )
    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(digest_report, rows=list(digest_report.rows))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_code_counts must be a tuple"):
        replace(
            digest_report,
            reason_code_counts=list(digest_report.reason_code_counts),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(
            digest_report.rows[0],
            reason_codes=list(digest_report.rows[0].reason_codes),  # type: ignore[arg-type]
        )

    object.__setattr__(
        digest_report.rows[0],
        "observed_at",
        datetime(2026, 7, 5, 9, 40, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="observed_at must be UTC"):
        market_research_equity_single_stock_gap_risk_digest_payload(digest_report)


def test_module_scope_excludes_io_live_execution_and_disallowed_public_fields() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_equity_single_stock_gap_risk_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "market_slug",
        "question",
        "payload_json",
        "trading",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "supabase",
        "sqlite",
        "psycopg",
        "requests",
        "urllib",
        "socket",
        "openai",
        "boto",
        "ccxt",
    )
    assert not any(token in lowered for token in forbidden_literals)
    assert "asdict" not in lowered

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {
                "connect",
                "execute",
                "fetch",
                "open",
                "read",
                "write",
                "request",
                "submit",
                "cancel",
            }

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "pathlib",
        "sqlite",
        "requests",
        "socket",
        "urllib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float value leaked into payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_floats(child)
    if isinstance(value, (list, tuple)):
        for child in value:
            assert_no_floats(child)


def assert_public_numeric_fields_are_exact_decimals(value: object) -> None:
    numeric_fragments = (
        "age",
        "count",
        "pct",
        "ratio",
        "score",
        "seconds",
    )
    for field in fields(value):
        field_value: Any = getattr(value, field.name)
        if field.name == "source_config_version":
            continue
        if not any(fragment in field.name for fragment in numeric_fragments):
            continue
        if isinstance(field_value, tuple):
            continue
        if field_value is None:
            continue
        assert type(field_value) is Decimal, field.name
        assert field_value.as_tuple().exponent == -6, field.name
