from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.exposure_gate import (
    PaperExposureGateConfig,
    PaperExposureGateReport,
    PaperExposureGateRow,
    build_paper_exposure_gate_report,
)
from polymarket_alpha_lab.positions import PaperPortfolio, PaperPosition


GENERATED_AT = datetime(2026, 6, 18, 9, 30, tzinfo=UTC)
HEX = "a" * 64


def _config(**overrides) -> PaperExposureGateConfig:
    values = {
        "config_version": "paper-exposure-gate-v0",
        "max_market_exposure": Decimal("100.0000"),
        "max_total_exposure": Decimal("250.0000"),
        "max_position_count": 3,
        "min_cash_buffer": Decimal("25.0000"),
    }
    values.update(overrides)
    return PaperExposureGateConfig(**values)


def _position(
    *,
    condition_id: str,
    token_id: str,
    market_slug: str,
    cost_basis: Decimal,
    opened_at: datetime = datetime(2026, 6, 18, 8, 0, tzinfo=UTC),
    updated_at: datetime = datetime(2026, 6, 18, 9, 0, tzinfo=UTC),
) -> PaperPosition:
    open_size = max(Decimal("100.0000"), cost_basis)
    return PaperPosition(
        source_packet_ids=(f"packet-{token_id}",),
        condition_id=condition_id,
        token_id=token_id,
        market_slug=market_slug,
        market_url=f"https://example.test/{market_slug}",
        question=f"{market_slug} question",
        outcome_name="YES",
        strategy_type="event",
        risk_tags=("paper",),
        rule_text_hash=HEX,
        resolution_source="resolution-source",
        market_raw_archive_path=f"raw/{market_slug}.json",
        last_order_book_raw_archive_path=f"book/{token_id}.json",
        last_order_book_raw_payload_sha256=HEX,
        last_order_book_snapshot_sha256=HEX,
        opened_at=opened_at,
        updated_at=updated_at,
        open_size=open_size,
        cost_basis=cost_basis,
        average_entry_price=(cost_basis / open_size).quantize(
            Decimal("0.0001"),
        ),
        realized_pnl=Decimal("0.0000"),
        entry_trade_count=1,
        exit_trade_count=0,
    )


def _portfolio(
    positions: tuple[PaperPosition, ...],
    *,
    cash_balance: Decimal = Decimal("100.0000"),
    realized_pnl: Decimal = Decimal("0.0000"),
) -> PaperPortfolio:
    total_cost_basis = sum((position.cost_basis for position in positions), Decimal("0"))
    return PaperPortfolio(
        starting_cash=cash_balance + total_cost_basis - realized_pnl,
        cash_balance=cash_balance,
        realized_pnl=realized_pnl,
        positions=positions,
    )


def _build_report(
    positions: PaperPortfolio | tuple[PaperPosition, ...],
    **config_overrides,
) -> PaperExposureGateReport:
    return build_paper_exposure_gate_report(
        positions,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_exposure_gate_passes_portfolio_within_limits():
    positions = (
        _position(
            condition_id="condition-a",
            token_id="token-a",
            market_slug="market-alpha",
            cost_basis=Decimal("40.0000"),
        ),
        _position(
            condition_id="condition-b",
            token_id="token-b",
            market_slug="market-beta",
            cost_basis=Decimal("70.0000"),
        ),
    )
    report = _build_report(_portfolio(positions, cash_balance=Decimal("80.0000")))

    assert isinstance(report, PaperExposureGateReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-exposure-gate-v0"
    assert report.status == "pass"
    assert report.total_exposure == Decimal("110.0000")
    assert report.position_count == 2
    assert report.cash_buffer == Decimal("80.0000")
    assert report.reason_codes == ()
    assert tuple(row.market_slug for row in report.rows) == (
        "market-alpha",
        "market-beta",
    )
    assert report.rows[0] == PaperExposureGateRow(
        market_slug="market-alpha",
        exposure_amount=Decimal("40.0000"),
        status="pass",
        reason_codes=(),
    )


def test_exposure_gate_blocks_market_exposure_breach_and_sorts_by_severity():
    positions = (
        _position(
            condition_id="condition-a",
            token_id="token-a",
            market_slug="market-pass",
            cost_basis=Decimal("20.0000"),
        ),
        _position(
            condition_id="condition-b",
            token_id="token-b",
            market_slug="market-blocked",
            cost_basis=Decimal("125.0000"),
        ),
        _position(
            condition_id="condition-c",
            token_id="token-c",
            market_slug="market-watch",
            cost_basis=Decimal("100.0000"),
        ),
    )

    report = _build_report(
        _portfolio(positions, cash_balance=Decimal("50.0000")),
        max_total_exposure=Decimal("300.0000"),
    )

    assert report.status == "blocked"
    assert tuple((row.market_slug, row.status) for row in report.rows) == (
        ("market-blocked", "blocked"),
        ("market-watch", "watch"),
        ("market-pass", "pass"),
    )
    assert report.rows[0].exposure_amount == Decimal("125.0000")
    assert report.rows[0].reason_codes == ("market_exposure_exceeds_max",)
    assert "market_exposure_exceeds_max" in report.reason_codes


def test_exposure_gate_blocks_total_exposure_breach_without_marking_rows_blocked():
    positions = (
        _position(
            condition_id="condition-a",
            token_id="token-a",
            market_slug="market-alpha",
            cost_basis=Decimal("80.0000"),
        ),
        _position(
            condition_id="condition-b",
            token_id="token-b",
            market_slug="market-beta",
            cost_basis=Decimal("90.0000"),
        ),
    )

    report = _build_report(
        _portfolio(positions, cash_balance=Decimal("100.0000")),
        max_total_exposure=Decimal("150.0000"),
    )

    assert report.status == "blocked"
    assert report.total_exposure == Decimal("170.0000")
    assert report.reason_codes == ("total_exposure_exceeds_max",)
    assert tuple(row.status for row in report.rows) == ("pass", "pass")


def test_exposure_gate_empty_positions_watch_with_explicit_reason():
    report = _build_report(_portfolio((), cash_balance=Decimal("100.0000")))

    assert report.status == "watch"
    assert report.position_count == 0
    assert report.total_exposure == Decimal("0")
    assert report.rows == ()
    assert report.reason_codes == ("no_positions",)


def test_exposure_gate_rejects_wrong_scalar_types_exactly():
    with pytest.raises(ValueError, match="max_market_exposure"):
        _config(max_market_exposure=1)
    with pytest.raises(ValueError, match="max_total_exposure"):
        _config(max_total_exposure="250.0000")
    with pytest.raises(ValueError, match="max_position_count"):
        _config(max_position_count=True)
    with pytest.raises(ValueError, match="min_cash_buffer"):
        _config(min_cash_buffer=25.0)
    with pytest.raises(ValueError, match="config"):
        build_paper_exposure_gate_report((), config=object(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="generated_at"):
        build_paper_exposure_gate_report((), config=_config(), generated_at="now")
    with pytest.raises(ValueError, match="positions"):
        build_paper_exposure_gate_report(object(), config=_config(), generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="PaperPosition"):
        build_paper_exposure_gate_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_exposure_gate_normalizes_report_datetime_to_utc():
    generated_at = datetime(2026, 6, 18, 5, 30, tzinfo=timezone(timedelta(hours=-4)))

    report = build_paper_exposure_gate_report(
        _portfolio((), cash_balance=Decimal("100.0000")),
        config=_config(),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC


def test_exposure_gate_dataclasses_are_frozen_and_revalidate_hard_flags():
    report = _build_report(_portfolio((), cash_balance=Decimal("100.0000")))

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_exposure_gate_report_rejects_blocked_row_with_pass_summary():
    blocked_row = PaperExposureGateRow(
        market_slug="market-blocked",
        exposure_amount=Decimal("125.0000"),
        status="blocked",
        reason_codes=("market_exposure_exceeds_max",),
    )

    with pytest.raises(ValueError, match="reason_codes"):
        PaperExposureGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-exposure-gate-v0",
            status="pass",
            position_count=1,
            total_exposure=Decimal("125.0000"),
            cash_buffer=Decimal("100.0000"),
            rows=(blocked_row,),
            reason_codes=(),
        )


def test_exposure_gate_report_rejects_total_exposure_that_does_not_match_rows():
    rows = (
        PaperExposureGateRow(
            market_slug="market-alpha",
            exposure_amount=Decimal("40.0000"),
            status="pass",
            reason_codes=(),
        ),
        PaperExposureGateRow(
            market_slug="market-beta",
            exposure_amount=Decimal("70.0000"),
            status="pass",
            reason_codes=(),
        ),
    )

    with pytest.raises(ValueError, match="total_exposure"):
        PaperExposureGateReport(
            generated_at=GENERATED_AT,
            config_version="paper-exposure-gate-v0",
            status="pass",
            position_count=2,
            total_exposure=Decimal("109.9999"),
            cash_buffer=Decimal("100.0000"),
            rows=rows,
            reason_codes=(),
        )


def test_exposure_gate_rejects_subclassed_scalar_types_exactly():
    class IntSubclass(int):
        pass

    class StrSubclass(str):
        pass

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=StrSubclass("paper-exposure-gate-v0"))
    with pytest.raises(ValueError, match="max_position_count"):
        _config(max_position_count=IntSubclass(3))
    with pytest.raises(ValueError, match="market_slug"):
        PaperExposureGateRow(
            market_slug=StrSubclass("market-alpha"),
            exposure_amount=Decimal("1.0000"),
            status="pass",
            reason_codes=(),
        )
    with pytest.raises(ValueError, match="status"):
        PaperExposureGateRow(
            market_slug="market-alpha",
            exposure_amount=Decimal("1.0000"),
            status=StrSubclass("pass"),
            reason_codes=(),
        )
