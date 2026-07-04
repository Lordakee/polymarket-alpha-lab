from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_equity_index_market_on_close_imbalance_digest import (
    DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_MARKET_ON_CLOSE_IMBALANCE_DIGEST_CONFIG_VERSION,
    MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig,
    MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow,
    MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount,
    MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport,
    build_market_research_equity_index_market_on_close_imbalance_digest,
    market_research_equity_index_market_on_close_imbalance_digest_to_json,
)


GENERATED_AT = datetime(2026, 7, 2, 19, 55, tzinfo=UTC)


def _config(
    **overrides: object,
) -> MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_MARKET_ON_CLOSE_IMBALANCE_DIGEST_CONFIG_VERSION
        ),
        "watch_close_delta_seconds": Decimal("1800"),
        "blocked_close_delta_seconds": Decimal("300"),
        "watch_imbalance_age_seconds": Decimal("60"),
        "max_imbalance_age_seconds": Decimal("180"),
        "watch_abs_imbalance_notional_usd": Decimal("500000000"),
        "max_abs_imbalance_notional_usd": Decimal("1500000000"),
        "watch_imbalance_ratio": Decimal("0.020000"),
        "max_imbalance_ratio": Decimal("0.050000"),
        "watch_abs_indicative_move_bps": Decimal("10"),
        "max_abs_indicative_move_bps": Decimal("25"),
    }
    values.update(overrides)
    return MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig(**values)


def _row(
    event_slug: str,
    *,
    closes_in: Decimal = Decimal("3600"),
    observed_ago: Decimal | None = Decimal("30"),
    imbalance_side: str = "buy",
    imbalance_notional_usd: Decimal = Decimal("100000000"),
    reference_close_notional_usd: Decimal = Decimal("10000000000"),
    indicative_move_bps: Decimal = Decimal("2"),
    source_reason_codes: tuple[str, ...] = ("official_moc_feed",),
) -> MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow:
    return MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow(
        event_slug=event_slug,
        index_symbol="SPX",
        market_close_at=GENERATED_AT + timedelta(seconds=int(closes_in)),
        imbalance_observed_at=(
            None
            if observed_ago is None
            else GENERATED_AT - timedelta(seconds=int(observed_ago))
        ),
        imbalance_side=imbalance_side,
        imbalance_notional_usd=imbalance_notional_usd,
        reference_close_notional_usd=reference_close_notional_usd,
        indicative_move_bps=indicative_move_bps,
        source_reason_codes=source_reason_codes,
    )


def _digest(
    *rows: MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow,
    config: MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport:
    return build_market_research_equity_index_market_on_close_imbalance_digest(
        rows,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_empty_digest_blocks_with_decimal_counts_and_hard_flags() -> None:
    report = _digest()

    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_MARKET_RESEARCH_EQUITY_INDEX_MARKET_ON_CLOSE_IMBALANCE_DIGEST_CONFIG_VERSION
    )
    assert report.risk_status == "blocked"
    assert report.recommended_next_step == "defer_equity_index_close_event_screening"
    assert report.row_count == Decimal("0")
    assert report.pass_row_count == Decimal("0")
    assert report.watch_row_count == Decimal("0")
    assert report.blocked_row_count == Decimal("0")
    assert report.rows == ()
    assert report.reason_codes == ("equity_index_moc_imbalance_digest_empty",)
    assert report.reason_code_counts == (
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
            reason_code="equity_index_moc_imbalance_digest_empty",
            count=Decimal("1"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_imbalance_blocks_screening_with_focused_reasons() -> None:
    report = _digest(
        _row(
            "spx-close-high-sell-imbalance",
            closes_in=Decimal("300"),
            observed_ago=Decimal("181"),
            imbalance_side="sell",
            imbalance_notional_usd=Decimal("1600000000"),
            reference_close_notional_usd=Decimal("20000000000"),
            indicative_move_bps=Decimal("-30"),
        ),
        _row("spx-close-clear"),
    )

    high_risk_row = report.rows[0]
    assert report.risk_status == "blocked"
    assert report.recommended_next_step == "defer_equity_index_close_event_screening"
    assert report.blocked_row_count == Decimal("1")
    assert report.pass_row_count == Decimal("1")
    assert high_risk_row.event_slug == "spx-close-high-sell-imbalance"
    assert high_risk_row.close_time_delta_seconds == Decimal("300")
    assert high_risk_row.imbalance_age_seconds == Decimal("181")
    assert high_risk_row.abs_imbalance_notional_usd == Decimal("1600000000")
    assert high_risk_row.imbalance_ratio == Decimal("0.080000")
    assert high_risk_row.abs_indicative_move_bps == Decimal("30")
    assert high_risk_row.close_time_status == "imminent"
    assert high_risk_row.imbalance_freshness_status == "stale"
    assert high_risk_row.imbalance_notional_status == "blocked"
    assert high_risk_row.imbalance_ratio_status == "blocked"
    assert high_risk_row.indicative_move_status == "blocked"
    assert high_risk_row.risk_status == "blocked"
    assert high_risk_row.reason_codes == (
        "market_close_imminent",
        "imbalance_stale",
        "imbalance_notional_blocked",
        "imbalance_ratio_blocked",
        "indicative_move_blocked",
    )
    assert report.reason_code_counts == (
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
            reason_code="market_close_imminent",
            count=Decimal("1"),
        ),
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
            reason_code="imbalance_stale",
            count=Decimal("1"),
        ),
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
            reason_code="imbalance_notional_blocked",
            count=Decimal("1"),
        ),
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
            reason_code="imbalance_ratio_blocked",
            count=Decimal("1"),
        ),
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount(
            reason_code="indicative_move_blocked",
            count=Decimal("1"),
        ),
    )


def test_sorting_and_reason_codes_are_deterministic() -> None:
    rows = (
        _row("z-pass"),
        _row("near-close", closes_in=Decimal("1800")),
        _row("aging-imbalance", observed_ago=Decimal("60")),
        _row(
            "notional-watch",
            imbalance_notional_usd=Decimal("500000000"),
            reference_close_notional_usd=Decimal("100000000000"),
        ),
        _row(
            "ratio-watch",
            imbalance_notional_usd=Decimal("400000000"),
            reference_close_notional_usd=Decimal("20000000000"),
        ),
        _row("move-watch", indicative_move_bps=Decimal("10")),
        _row(
            "ratio-blocked",
            imbalance_notional_usd=Decimal("1000000000"),
            reference_close_notional_usd=Decimal("20000000000"),
        ),
        _row("a-pass"),
    )

    forward = _digest(*rows)
    reversed_report = _digest(*reversed(rows))

    assert forward == reversed_report
    assert tuple(row.event_slug for row in forward.rows) == (
        "ratio-blocked",
        "near-close",
        "aging-imbalance",
        "notional-watch",
        "ratio-watch",
        "move-watch",
        "a-pass",
        "z-pass",
    )
    assert forward.reason_codes == (
        "imbalance_ratio_blocked",
        "market_close_near",
        "imbalance_aging",
        "imbalance_notional_watch",
        "imbalance_ratio_watch",
        "indicative_move_watch",
    )


def test_validation_requires_decimal_public_numerics_utc_and_public_text() -> None:
    with pytest.raises(ValueError, match="generated_at.*UTC"):
        _digest(_row("ok"), generated_at=datetime(2026, 7, 2, 19, 55))

    with pytest.raises(ValueError, match="market_close_at.*UTC"):
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow(
            event_slug="bad-close-time",
            index_symbol="SPX",
            market_close_at=datetime(
                2026,
                7,
                2,
                15,
                55,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            imbalance_observed_at=GENERATED_AT,
            imbalance_side="buy",
            imbalance_notional_usd=Decimal("100000000"),
            reference_close_notional_usd=Decimal("10000000000"),
            indicative_move_bps=Decimal("2"),
            source_reason_codes=("official_moc_feed",),
        )

    with pytest.raises(ValueError, match="imbalance_observed_at.*future"):
        _digest(
            MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow(
                event_slug="future-imbalance",
                index_symbol="SPX",
                market_close_at=GENERATED_AT + timedelta(minutes=30),
                imbalance_observed_at=GENERATED_AT + timedelta(seconds=1),
                imbalance_side="buy",
                imbalance_notional_usd=Decimal("100000000"),
                reference_close_notional_usd=Decimal("10000000000"),
                indicative_move_bps=Decimal("2"),
                source_reason_codes=("official_moc_feed",),
            ),
        )

    with pytest.raises(ValueError, match="reference_close_notional_usd.*positive"):
        _row("bad-reference-notional", reference_close_notional_usd=Decimal("0"))
    with pytest.raises(ValueError, match="imbalance_notional_usd.*Decimal"):
        _row("float-notional", imbalance_notional_usd=100.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reason_codes.*public"):
        _row("secret-source", source_reason_codes=("api_key_leak",))


def test_public_dataclasses_are_frozen_and_enforce_hard_flags() -> None:
    with pytest.raises(ValueError, match="input_row must be paper_only"):
        replace(_row("bad-input-flag"), paper_only=False)
    with pytest.raises(ValueError, match="config must be report_only"):
        replace(_config(), report_only=False)
    with pytest.raises(ValueError, match="config must be readonly"):
        replace(_config(), readonly=False)

    report = _digest(_row("clear"))
    with pytest.raises(FrozenInstanceError):
        report.risk_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=Decimal("2"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=())
    with pytest.raises(ValueError, match="report must be readonly"):
        replace(report, readonly=False)

    public_dataclasses = (
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestConfig,
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestInputRow,
        type(report.rows[0]),
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReasonCodeCount,
        MarketResearchEquityIndexMarketOnCloseImbalanceDigestReport,
    )
    assert all(getattr(cls, "__dataclass_params__").frozen for cls in public_dataclasses)


def test_non_default_thresholds_can_keep_screening_passed() -> None:
    screened_row = _row(
        "threshold-sensitive",
        closes_in=Decimal("1200"),
        observed_ago=Decimal("90"),
        imbalance_notional_usd=Decimal("600000000"),
        reference_close_notional_usd=Decimal("20000000000"),
        indicative_move_bps=Decimal("12"),
    )

    default_report = _digest(screened_row)
    custom_report = _digest(
        screened_row,
        config=_config(
            watch_close_delta_seconds=Decimal("600"),
            blocked_close_delta_seconds=Decimal("120"),
            watch_imbalance_age_seconds=Decimal("120"),
            max_imbalance_age_seconds=Decimal("300"),
            watch_abs_imbalance_notional_usd=Decimal("700000000"),
            max_abs_imbalance_notional_usd=Decimal("2000000000"),
            watch_imbalance_ratio=Decimal("0.040000"),
            max_imbalance_ratio=Decimal("0.080000"),
            watch_abs_indicative_move_bps=Decimal("15"),
            max_abs_indicative_move_bps=Decimal("30"),
        ),
    )

    assert default_report.risk_status == "watch"
    assert default_report.rows[0].reason_codes == (
        "market_close_near",
        "imbalance_aging",
        "imbalance_notional_watch",
        "imbalance_ratio_watch",
        "indicative_move_watch",
    )
    assert custom_report.risk_status == "pass"
    assert custom_report.reason_codes == ("equity_index_moc_imbalance_digest_passed",)
    assert custom_report.rows[0].reason_codes == (
        "equity_index_moc_imbalance_digest_passed",
    )


def test_json_payload_uses_decimal_strings_and_iso_datetimes_without_floats() -> None:
    report = _digest(
        _row(
            "payload",
            closes_in=Decimal("900"),
            observed_ago=Decimal("30"),
            imbalance_notional_usd=Decimal("123456789.12"),
            reference_close_notional_usd=Decimal("10000000000"),
            indicative_move_bps=Decimal("3.25"),
        ),
    )

    payload = market_research_equity_index_market_on_close_imbalance_digest_to_json(
        report,
    )

    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["row_count"] == "1"
    assert payload["max_abs_imbalance_notional_usd_observed"] == "123456789.12"
    assert payload["max_imbalance_ratio_observed"] == "0.012346"
    row_payload = payload["rows"][0]
    assert row_payload["market_close_at"] == (
        GENERATED_AT + timedelta(seconds=900)
    ).isoformat()
    assert row_payload["close_time_delta_seconds"] == "900"
    assert row_payload["imbalance_age_seconds"] == "30"
    assert row_payload["abs_imbalance_notional_usd"] == "123456789.12"
    assert row_payload["imbalance_ratio"] == "0.012346"
    assert row_payload["abs_indicative_move_bps"] == "3.25"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_decimal_datetime_or_float(payload)


def test_module_has_no_forbidden_live_or_mutating_surfaces() -> None:
    import polymarket_alpha_lab.market_research_equity_index_market_on_close_imbalance_digest as module

    forbidden_terms = (
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange",
        "trade",
        "db",
        "network",
        "live",
    )
    public_names = [name for name in dir(module) if not name.startswith("_")]
    assert not [
        name
        for name in public_names
        if any(term in name.lower() for term in forbidden_terms)
    ]

    source = inspect.getsource(module)
    assert "private_key" not in source.lower()
    parsed = ast.parse(source)
    forbidden_imports = {
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "web3",
    }
    assert not [
        node
        for node in ast.walk(parsed)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        and any(alias.name.partition(".")[0] in forbidden_imports for alias in node.names)
    ]
    assert not [
        node
        for node in ast.walk(parsed)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"eval", "exec", "open", "__import__"}
    ]


def _assert_no_decimal_datetime_or_float(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_datetime_or_float(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_decimal_datetime_or_float(item)
        return
    assert not isinstance(value, (Decimal, datetime, float))


def test_public_dataclass_numeric_fields_are_decimal_only() -> None:
    report = _digest(_row("numeric-types"))

    def assert_public_numerics_are_decimal(value: object) -> None:
        if is_dataclass(value):
            for field in fields(value):
                item = getattr(value, field.name)
                if isinstance(item, tuple):
                    for child in item:
                        assert_public_numerics_are_decimal(child)
                    continue
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    raise AssertionError(f"{field.name} used non-Decimal public numeric")
                if is_dataclass(item):
                    assert_public_numerics_are_decimal(item)

    assert_public_numerics_are_decimal(report)
