from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab as lab
from polymarket_alpha_lab.exposure_concentration_monitor import (
    PaperExposureConcentrationEventRow,
    PaperExposureConcentrationGroupRow,
    PaperExposureConcentrationMonitorConfig,
    PaperExposureConcentrationReport,
    build_paper_exposure_concentration_report,
    paper_exposure_concentration_monitor_payload,
)
from polymarket_alpha_lab.positions import PaperPortfolio, PaperPosition


STAMP = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
SHA256 = "a" * 64


def _position(
    *,
    condition_id: str,
    token_id: str,
    team: str,
    risk_tags: tuple[str, ...],
    open_size: Decimal,
    cost_basis: Decimal,
) -> PaperPosition:
    return PaperPosition(
        source_packet_ids=(f"packet-{token_id}",),
        condition_id=condition_id,
        token_id=token_id,
        market_slug=f"hidden-{condition_id}-{token_id}",
        market_url=f"https://example.invalid/{token_id}",
        question=f"Hidden prompt for {condition_id}",
        outcome_name="Yes",
        strategy_type=team,
        risk_tags=risk_tags,
        rule_text_hash=f"rule-{token_id}",
        resolution_source="paper-resolution-source",
        market_raw_archive_path=f"archive/{token_id}.json",
        last_order_book_raw_archive_path=f"archive/{token_id}-book.json",
        last_order_book_raw_payload_sha256=SHA256,
        last_order_book_snapshot_sha256=SHA256,
        opened_at=STAMP,
        updated_at=STAMP,
        open_size=open_size,
        cost_basis=cost_basis,
        average_entry_price=(cost_basis / open_size).quantize(Decimal("0.000001")),
        realized_pnl=Decimal("0"),
        entry_trade_count=1,
        exit_trade_count=0,
    )


def _portfolio() -> PaperPortfolio:
    positions = (
        _position(
            condition_id="condition-alpha",
            token_id="token-a-yes",
            team="crypto",
            risk_tags=("macro", "btc"),
            open_size=Decimal("40"),
            cost_basis=Decimal("20"),
        ),
        _position(
            condition_id="condition-alpha",
            token_id="token-a-no",
            team="crypto",
            risk_tags=("macro",),
            open_size=Decimal("60"),
            cost_basis=Decimal("30"),
        ),
        _position(
            condition_id="condition-beta",
            token_id="token-b-yes",
            team="sports",
            risk_tags=("sports",),
            open_size=Decimal("20"),
            cost_basis=Decimal("10"),
        ),
    )
    return PaperPortfolio(
        starting_cash=Decimal("100"),
        cash_balance=Decimal("40"),
        realized_pnl=Decimal("0"),
        positions=positions,
    )


def _config(**overrides: object) -> PaperExposureConcentrationMonitorConfig:
    values: dict[str, object] = {
        "config_version": "phase-1",
        "event_warn_share": Decimal("0.800000"),
        "team_warn_share": Decimal("0.800000"),
        "category_warn_share": Decimal("0.800000"),
    }
    values.update(overrides)
    return PaperExposureConcentrationMonitorConfig(**values)


def test_concentration_report_groups_open_positions_without_slug_or_question() -> None:
    report = build_paper_exposure_concentration_report(
        _portfolio(),
        config=_config(),
        generated_at=STAMP,
    )

    assert isinstance(report, PaperExposureConcentrationReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.status == "concentration_watch"
    assert report.starting_cash == Decimal("100")
    assert report.cash_balance == Decimal("40")
    assert report.total_cost_basis == Decimal("60")
    assert report.open_position_count == Decimal("3")
    assert report.event_count == Decimal("2")
    assert report.team_count == Decimal("2")
    assert report.category_count == Decimal("3")
    assert report.largest_event_condition_id == "condition-alpha"
    assert report.largest_event_share == Decimal("0.833333")
    assert report.largest_team_share == Decimal("0.833333")
    assert report.largest_category_share == Decimal("0.833333")

    assert report.event_rows == (
        PaperExposureConcentrationEventRow(
            condition_id="condition-alpha",
            position_count=Decimal("2"),
            open_size=Decimal("100"),
            cost_basis=Decimal("50"),
            share_of_total_cost_basis=Decimal("0.833333"),
            warning_triggered=True,
        ),
        PaperExposureConcentrationEventRow(
            condition_id="condition-beta",
            position_count=Decimal("1"),
            open_size=Decimal("20"),
            cost_basis=Decimal("10"),
            share_of_total_cost_basis=Decimal("0.166667"),
            warning_triggered=False,
        ),
    )
    assert report.team_rows[0] == PaperExposureConcentrationGroupRow(
        group_type="team",
        group_value="crypto",
        position_count=Decimal("2"),
        event_count=Decimal("1"),
        open_size=Decimal("100"),
        cost_basis=Decimal("50"),
        share_of_total_cost_basis=Decimal("0.833333"),
        warning_triggered=True,
    )
    assert report.category_rows[1] == PaperExposureConcentrationGroupRow(
        group_type="category",
        group_value="macro",
        position_count=Decimal("2"),
        event_count=Decimal("1"),
        open_size=Decimal("100"),
        cost_basis=Decimal("50"),
        share_of_total_cost_basis=Decimal("0.833333"),
        warning_triggered=True,
    )

    report_rows = (*report.event_rows, *report.team_rows, *report.category_rows)
    assert all(not hasattr(row, "market_slug") for row in report_rows)
    assert all(not hasattr(row, "question") for row in report_rows)
    assert lab.PaperExposureConcentrationMonitorConfig is PaperExposureConcentrationMonitorConfig
    assert lab.PaperExposureConcentrationEventRow is PaperExposureConcentrationEventRow
    assert lab.PaperExposureConcentrationGroupRow is PaperExposureConcentrationGroupRow
    assert lab.PaperExposureConcentrationReport is PaperExposureConcentrationReport
    assert (
        lab.build_paper_exposure_concentration_report
        is build_paper_exposure_concentration_report
    )


def test_empty_portfolio_report_is_readonly_with_no_risk_rows() -> None:
    portfolio = PaperPortfolio(
        starting_cash=Decimal("100"),
        cash_balance=Decimal("100"),
        realized_pnl=Decimal("0"),
        positions=(),
    )

    report = build_paper_exposure_concentration_report(
        portfolio,
        config=_config(),
        generated_at=STAMP,
    )

    assert report.status == "no_open_positions"
    assert report.open_position_count == Decimal("0")
    assert report.event_count == Decimal("0")
    assert report.team_count == Decimal("0")
    assert report.category_count == Decimal("0")
    assert report.total_cost_basis == Decimal("0")
    assert report.largest_event_condition_id is None
    assert report.largest_event_share is None
    assert report.event_rows == ()
    assert report.team_rows == ()
    assert report.category_rows == ()


def test_concentration_dataclasses_are_frozen_and_decimal_only() -> None:
    report = build_paper_exposure_concentration_report(
        _portfolio(),
        config=_config(),
        generated_at=STAMP,
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="event_warn_share must be a Decimal"):
        _config(event_warn_share=0.8)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="cost_basis must be a Decimal"):
        PaperExposureConcentrationEventRow(
            condition_id="condition",
            position_count=Decimal("1"),
            open_size=Decimal("1"),
            cost_basis=1,  # type: ignore[arg-type]
            share_of_total_cost_basis=Decimal("1"),
            warning_triggered=False,
        )
    for public_record in (
        _config(),
        *report.event_rows,
        *report.team_rows,
        *report.category_rows,
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not isinstance(value, int) or isinstance(value, bool)
            assert not isinstance(value, float)


def test_concentration_report_has_tamper_evident_public_payload() -> None:
    report = build_paper_exposure_concentration_report(
        _portfolio(),
        config=_config(),
        generated_at=STAMP,
    )

    payload = paper_exposure_concentration_monitor_payload(report)
    payload_text = repr(payload).lower()

    assert payload["generated_at"] == "2026-01-02T03:04:05+00:00"
    assert payload["open_position_count"] == "3"
    assert payload["event_rows"][0]["position_count"] == "2"
    assert payload["event_rows"][0]["share_of_total_cost_basis"] == "0.833333"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert paper_exposure_concentration_monitor_payload(report) == payload
    assert _json_contains_no_float(payload)
    for unsafe_text in (
        "market_slug",
        "question",
        "wallet",
        "order",
        "auth",
        "private_key",
        "cash_balance",
    ):
        assert unsafe_text not in payload_text

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["total_cost_basis"] = "999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        paper_exposure_concentration_monitor_payload(tampered)

    with pytest.raises(ValueError, match="readonly"):
        paper_exposure_concentration_monitor_payload({**payload, "readonly": False})


def test_zero_cost_open_positions_keep_largest_group_shares_absent() -> None:
    zero_cost_portfolio = PaperPortfolio(
        starting_cash=Decimal("100"),
        cash_balance=Decimal("100"),
        realized_pnl=Decimal("0"),
        positions=(
            _position(
                condition_id="condition-zero",
                token_id="token-zero-yes",
                team="crypto",
                risk_tags=("macro",),
                open_size=Decimal("10"),
                cost_basis=Decimal("0"),
            ),
        ),
    )

    report = build_paper_exposure_concentration_report(
        zero_cost_portfolio,
        config=_config(),
        generated_at=STAMP,
    )

    assert report.status == "concentration_clear"
    assert report.total_cost_basis == Decimal("0")
    assert report.largest_event_share is None
    assert report.largest_team_share is None
    assert report.largest_category_share is None
    assert report.event_rows[0].share_of_total_cost_basis is None
    assert paper_exposure_concentration_monitor_payload(report)["total_cost_basis"] == "0"


def test_monitor_module_stays_report_only_leaf_computation() -> None:
    source = Path("src/polymarket_alpha_lab/exposure_concentration_monitor.py").read_text()

    forbidden_terms = (
        "api",
        "auth",
        "client",
        "wallet",
        "order",
        "account",
        "trade",
        "fast",
        "slug",
        "question",
        "Path",
        "open(",
    )
    lowered_source = source.lower()
    for term in forbidden_terms:
        assert term.lower() not in lowered_source


def _json_contains_no_float(value: Any) -> bool:
    if isinstance(value, float):
        return False
    if isinstance(value, dict):
        return all(_json_contains_no_float(item) for item in value.values())
    if isinstance(value, list):
        return all(_json_contains_no_float(item) for item in value)
    return True
