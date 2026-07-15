from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest


MODULE_NAME = "polymarket_alpha_lab.paper_position_concentration_guard"
GENERATED_AT = datetime(2026, 7, 2, 8, 0, tzinfo=UTC)


def _api():
    return import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values = {
        "config_version": "paper-position-concentration-guard-v0",
        "market_warn_share": d("0.500000"),
        "category_warn_share": d("0.600000"),
        "team_warn_share": d("0.700000"),
        "outcome_side_warn_share": d("0.400000"),
    }
    values.update(overrides)
    return _api().PaperPositionConcentrationGuardConfig(**values)


def position(**overrides: object):
    values = {
        "market_slug": "btc-above-100k",
        "category_id": "crypto",
        "team_id": "crypto-team",
        "outcome_side": "yes",
        "open_notional": d("10.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return _api().PaperPositionConcentrationRecord(**values)


def build_report(*records: object, guard_config=None, generated_at=GENERATED_AT):
    return _api().build_paper_position_concentration_guard_report(
        list(records),
        config=guard_config or config(),
        generated_at=generated_at,
    )


def field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_guard_flags_market_category_team_and_outcome_side_concentration() -> None:
    api = _api()
    report = build_report(
        position(
            market_slug="btc-above-100k",
            category_id="crypto",
            team_id="crypto-team",
            outcome_side="yes",
            open_notional=d("30.000000"),
        ),
        position(
            market_slug="btc-below-90k",
            category_id="crypto",
            team_id="crypto-team",
            outcome_side="no",
            open_notional=d("20.000000"),
        ),
        position(
            market_slug="fed-cut-july",
            category_id="macro",
            team_id="macro-team",
            outcome_side="yes",
            open_notional=d("10.000000"),
        ),
    )

    assert type(report) is api.PaperPositionConcentrationGuardReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-position-concentration-guard-v0"
    assert report.record_count == 3
    assert report.group_count == 9
    assert report.clear_count == 5
    assert report.watch_count == 4
    assert report.total_open_notional == d("60.000000")
    assert report.concentration_status == "watch"
    assert report.reason_codes == (
        "market_share_at_or_above_limit",
        "category_share_at_or_above_limit",
        "team_share_at_or_above_limit",
        "outcome_side_share_at_or_above_limit",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.rows[0] == api.PaperPositionConcentrationGuardRow(
        group_type="market",
        group_value="btc-above-100k",
        position_count=1,
        open_notional=d("30.000000"),
        share_of_total_open_notional=d("0.500000"),
        threshold_share=d("0.500000"),
        concentration_status="watch",
        reason_codes=("market_share_at_or_above_limit",),
    )
    assert report.rows[1].group_type == "category"
    assert report.rows[1].group_value == "crypto"
    assert report.rows[1].open_notional == d("50.000000")
    assert report.rows[1].share_of_total_open_notional == d("0.833333")
    assert report.rows[1].reason_codes == ("category_share_at_or_above_limit",)
    assert report.rows[2].group_type == "team"
    assert report.rows[2].group_value == "crypto-team"
    assert report.rows[2].share_of_total_open_notional == d("0.833333")
    assert report.rows[3].group_type == "outcome_side"
    assert report.rows[3].group_value == "yes"
    assert report.rows[3].share_of_total_open_notional == d("0.666667")


def test_guard_returns_empty_readonly_report_for_no_positions() -> None:
    report = build_report()

    assert report.record_count == 0
    assert report.group_count == 0
    assert report.clear_count == 0
    assert report.watch_count == 0
    assert report.total_open_notional == d("0.000000")
    assert report.concentration_status == "clear"
    assert report.reason_codes == ()
    assert report.rows == ()


def test_guard_quantizes_decimal_arithmetic_and_normalizes_generated_at() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        position(open_notional=d("1.0000004")),
        position(
            market_slug="eth-above-5k",
            category_id="crypto",
            team_id="crypto-team",
            outcome_side="no",
            open_notional=d("2.0000004"),
        ),
        guard_config=config(
            market_warn_share=d("0.7000004"),
            category_warn_share=d("0.7000004"),
            team_warn_share=d("0.7000004"),
            outcome_side_warn_share=d("0.7000004"),
        ),
        generated_at=datetime(2026, 7, 2, 4, 0, tzinfo=eastern),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.total_open_notional == d("3.000000")
    assert report.rows[0].open_notional == d("3.000000")
    assert report.rows[0].share_of_total_open_notional == d("1.000000")
    assert report.rows[0].threshold_share == d("0.700000")


def test_guard_dataclasses_are_frozen_decimal_only_and_consistent() -> None:
    api = _api()
    record = position()
    guard_config = config()
    report = build_report(record)

    with pytest.raises(FrozenInstanceError):
        record.market_slug = "other"
    with pytest.raises(FrozenInstanceError):
        guard_config.market_warn_share = d("0.1")
    with pytest.raises(FrozenInstanceError):
        report.rows[0].concentration_status = "clear"

    rebuilt_row = api.PaperPositionConcentrationGuardRow(**field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]

    with pytest.raises(ValueError, match="open_notional"):
        position(open_notional=1.0)
    with pytest.raises(ValueError, match="open_notional"):
        position(open_notional=d("-0.000001"))
    canonical_zero = position(open_notional=d("-0"))
    assert canonical_zero.open_notional == d("0.000000")
    assert canonical_zero.open_notional.is_signed() is False
    with pytest.raises(ValueError, match="market_warn_share"):
        config(market_warn_share=0.5)
    with pytest.raises(ValueError, match="market_warn_share"):
        config(market_warn_share=d("1.000001"))
    with pytest.raises(ValueError, match="record paper_only"):
        position(paper_only=False)
    with pytest.raises(ValueError, match="config readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="row report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="watch_count"):
        replace(report, watch_count=99)
    with pytest.raises(ValueError, match="concentration_status"):
        replace(report.rows[0], concentration_status="bad")


def test_guard_rejects_non_list_inputs_subclasses_and_bad_generated_at() -> None:
    api = _api()
    record = position()
    guard_config = config()

    with pytest.raises(ValueError, match="list or tuple"):
        api.build_paper_position_concentration_guard_report(
            (value for value in [record]),
            config=guard_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PaperPositionConcentrationRecord"):
        api.build_paper_position_concentration_guard_report(
            [object()],
            config=guard_config,
            generated_at=GENERATED_AT,
        )

    class RecordSubclass(api.PaperPositionConcentrationRecord):
        pass

    with pytest.raises(ValueError, match="PaperPositionConcentrationRecord"):
        api.build_paper_position_concentration_guard_report(
            [RecordSubclass(**field_values(record))],
            config=guard_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        api.build_paper_position_concentration_guard_report(
            [record],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_paper_position_concentration_guard_report(
            [record],
            config=guard_config,
            generated_at="2026-07-02T08:00:00Z",
        )
    naive_report = api.build_paper_position_concentration_guard_report(
        [record],
        config=guard_config,
        generated_at=datetime(2026, 7, 2, 8, 0),
    )
    assert naive_report.generated_at == GENERATED_AT
    assert naive_report.generated_at.tzinfo is UTC


def test_guard_module_stays_leaf_report_only_without_private_market_text() -> None:
    source_path = Path(inspect.getsourcefile(_api()) or "")
    source = source_path.read_text()

    forbidden_terms = (
        "api",
        "auth",
        "client",
        "wallet",
        "order",
        "account",
        "trade",
        "advice",
        "question",
        "url",
        "description",
        "Path",
        "open(",
    )
    lowered_source = source.lower()
    for term in forbidden_terms:
        assert term.lower() not in lowered_source
