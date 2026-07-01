from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest


MODULE_NAME = "polymarket_alpha_lab.team_paper_exposure_guard"
GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def _api():
    return import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    api = _api()
    values = {
        "max_team_notional": d("100.000000"),
        "max_category_notional": d("90.000000"),
        "max_event_template_notional": d("80.000000"),
        "max_market_notional": d("50.000000"),
        "min_confidence_for_full_notional": d("0.600000"),
    }
    values.update(overrides)
    return api.TeamPaperExposureGuardConfig(**values)


def exposure_input(**overrides: object):
    api = _api()
    values = {
        "team_id": "crypto-team",
        "category_id": "crypto",
        "event_template": "btc-direction",
        "market_slug": "btc-above-100k",
        "selected_side": "yes",
        "proposed_notional": d("10.000000"),
        "existing_paper_notional": d("5.000000"),
        "confidence": d("0.800000"),
    }
    values.update(overrides)
    return api.TeamPaperExposureInput(**values)


def build_report(*inputs: object, guard_config=None, generated_at=GENERATED_AT):
    api = _api()
    return api.build_team_paper_exposure_guard_report(
        list(inputs),
        config=guard_config or config(),
        generated_at=generated_at,
    )


def field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_guard_passes_safe_proposals_and_reports_aggregate_metrics():
    api = _api()
    report = build_report(
        exposure_input(
            proposed_notional=d("12.250000"),
            existing_paper_notional=d("7.750000"),
            confidence=d("0.900000"),
        ),
        exposure_input(
            team_id="macro-team",
            category_id="macro",
            event_template="fed-decision",
            market_slug="fed-hold-july",
            selected_side="no",
            proposed_notional=d("20.000000"),
            existing_paper_notional=d("10.000000"),
            confidence=d("0.700000"),
        ),
    )

    assert type(report) is api.TeamPaperExposureGuardReport
    assert report.generated_at == GENERATED_AT
    assert report.input_count == 2
    assert report.row_count == 2
    assert report.pass_count == 2
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.exposure_status == "pass"
    assert report.total_proposed_notional == d("32.250000")
    assert report.total_existing_paper_notional == d("17.750000")
    assert report.total_capped_notional == d("32.250000")
    assert report.reason_codes == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    first = report.rows[0]
    assert first.team_id == "crypto-team"
    assert first.category_id == "crypto"
    assert first.event_template == "btc-direction"
    assert first.market_slug == "btc-above-100k"
    assert first.selected_side == "yes"
    assert first.proposed_notional == d("12.250000")
    assert first.existing_paper_notional == d("7.750000")
    assert first.confidence == d("0.900000")
    assert first.team_total_notional == d("20.000000")
    assert first.category_total_notional == d("20.000000")
    assert first.event_template_total_notional == d("20.000000")
    assert first.market_total_notional == d("20.000000")
    assert first.capped_notional == d("12.250000")
    assert first.exposure_status == "pass"
    assert first.reason_codes == ()
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True


def test_guard_watches_low_confidence_and_suggests_fractional_cap():
    report = build_report(
        exposure_input(
            proposed_notional=d("60.000000"),
            existing_paper_notional=d("0.000000"),
            confidence=d("0.400000"),
        ),
        guard_config=config(
            max_team_notional=d("100.000000"),
            max_category_notional=d("100.000000"),
            max_event_template_notional=d("100.000000"),
            max_market_notional=d("100.000000"),
            min_confidence_for_full_notional=d("0.600000"),
        ),
    )

    row = report.rows[0]
    assert row.exposure_status == "watch"
    assert row.reason_codes == ("confidence_below_full_notional",)
    assert row.capped_notional == d("40.000000")
    assert report.exposure_status == "watch"
    assert report.pass_count == 0
    assert report.watch_count == 1
    assert report.blocked_count == 0
    assert report.total_capped_notional == d("40.000000")
    assert report.reason_codes == ("confidence_below_full_notional",)


def test_guard_blocks_cap_breaches_by_team_category_template_and_market():
    report = build_report(
        exposure_input(
            team_id="alpha-team",
            category_id="crypto",
            event_template="btc-direction",
            market_slug="btc-above-100k",
            proposed_notional=d("30.000000"),
            existing_paper_notional=d("20.000000"),
            confidence=d("0.900000"),
        ),
        exposure_input(
            team_id="alpha-team",
            category_id="crypto",
            event_template="btc-direction",
            market_slug="btc-below-90k",
            proposed_notional=d("40.000000"),
            existing_paper_notional=d("10.000000"),
            confidence=d("0.300000"),
        ),
        guard_config=config(
            max_team_notional=d("90.000000"),
            max_category_notional=d("90.000000"),
            max_event_template_notional=d("80.000000"),
            max_market_notional=d("45.000000"),
            min_confidence_for_full_notional=d("0.600000"),
        ),
    )

    assert report.exposure_status == "blocked"
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 2
    assert report.total_proposed_notional == d("70.000000")
    assert report.total_existing_paper_notional == d("30.000000")
    assert report.total_capped_notional == d("45.000000")
    assert set(report.reason_codes) == {
        "team_notional_above_max",
        "category_notional_above_max",
        "event_template_notional_above_max",
        "market_notional_above_max",
        "confidence_below_full_notional",
    }

    first = next(row for row in report.rows if row.market_slug == "btc-above-100k")
    assert first.team_total_notional == d("100.000000")
    assert first.category_total_notional == d("100.000000")
    assert first.event_template_total_notional == d("100.000000")
    assert first.market_total_notional == d("50.000000")
    assert first.capped_notional == d("25.000000")
    assert first.exposure_status == "blocked"
    assert first.reason_codes == (
        "team_notional_above_max",
        "category_notional_above_max",
        "event_template_notional_above_max",
        "market_notional_above_max",
    )

    second = next(row for row in report.rows if row.market_slug == "btc-below-90k")
    assert second.market_total_notional == d("50.000000")
    assert second.capped_notional == d("20.000000")
    assert second.exposure_status == "blocked"
    assert second.reason_codes == (
        "team_notional_above_max",
        "category_notional_above_max",
        "event_template_notional_above_max",
        "market_notional_above_max",
        "confidence_below_full_notional",
    )


def test_guard_quantizes_decimals_and_normalizes_generated_at_to_utc():
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        exposure_input(
            proposed_notional=d("1.0000004"),
            existing_paper_notional=d("2.0000004"),
            confidence=d("0.9000004"),
        ),
        guard_config=config(
            max_team_notional=d("10.0000004"),
            max_category_notional=d("10.0000004"),
            max_event_template_notional=d("10.0000004"),
            max_market_notional=d("10.0000004"),
            min_confidence_for_full_notional=d("0.6000004"),
        ),
        generated_at=datetime(2026, 7, 1, 8, 0, tzinfo=eastern),
    )

    row = report.rows[0]
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert row.proposed_notional == d("1.000000")
    assert row.existing_paper_notional == d("2.000000")
    assert row.confidence == d("0.900000")
    assert row.team_total_notional == d("3.000000")
    assert row.capped_notional == d("1.000000")

    edge_report = build_report(
        exposure_input(confidence=d("1.0000004")),
        guard_config=config(min_confidence_for_full_notional=d("1.0000004")),
    )
    assert edge_report.rows[0].confidence == d("1.000000")


def test_guard_dataclasses_are_frozen_and_validate_public_values():
    api = _api()
    input_row = exposure_input()
    guard_config = config()
    report = build_report(input_row)

    with pytest.raises(FrozenInstanceError):
        input_row.team_id = "other-team"
    with pytest.raises(FrozenInstanceError):
        guard_config.max_team_notional = d("1.000000")
    with pytest.raises(FrozenInstanceError):
        report.rows[0].exposure_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        report.rows = ()

    rebuilt_row = api.TeamPaperExposureGuardRow(**field_values(report.rows[0]))
    assert rebuilt_row == report.rows[0]

    with pytest.raises(ValueError, match="proposed_notional"):
        exposure_input(proposed_notional=1.0)
    with pytest.raises(ValueError, match="existing_paper_notional"):
        exposure_input(existing_paper_notional=d("-0.000001"))
    assert exposure_input(confidence=d("1.000001")).confidence == d("1.000001")
    with pytest.raises(ValueError, match="max_team_notional"):
        config(max_team_notional=1.0)
    with pytest.raises(ValueError, match="min_confidence_for_full_notional"):
        config(min_confidence_for_full_notional=d("1.000001"))
    with pytest.raises(ValueError, match="input paper_only"):
        exposure_input(paper_only=False)
    with pytest.raises(ValueError, match="config report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="row readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="capped_notional"):
        replace(report.rows[0], capped_notional=d("99.000000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=0)


def test_guard_builder_rejects_bad_public_types_and_non_list_inputs():
    api = _api()
    input_row = exposure_input()
    guard_config = config()

    with pytest.raises(ValueError, match="list or tuple"):
        api.build_team_paper_exposure_guard_report(
            (value for value in [input_row]),
            config=guard_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="list or tuple"):
        api.build_team_paper_exposure_guard_report(
            {"row": input_row},
            config=guard_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="list or tuple"):
        api.build_team_paper_exposure_guard_report(
            "not-inputs",
            config=guard_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="TeamPaperExposureInput"):
        api.build_team_paper_exposure_guard_report(
            [object()],
            config=guard_config,
            generated_at=GENERATED_AT,
        )

    class InputSubclass(api.TeamPaperExposureInput):
        pass

    with pytest.raises(ValueError, match="TeamPaperExposureInput"):
        api.build_team_paper_exposure_guard_report(
            [InputSubclass(**field_values(input_row))],
            config=guard_config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        api.build_team_paper_exposure_guard_report(
            [input_row],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_team_paper_exposure_guard_report(
            [input_row],
            config=guard_config,
            generated_at="2026-07-01T12:00:00Z",
        )


def test_guard_returns_empty_report_for_empty_input_list():
    report = _api().build_team_paper_exposure_guard_report(
        [],
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.input_count == 0
    assert report.row_count == 0
    assert report.pass_count == 0
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.exposure_status == "pass"
    assert report.total_proposed_notional == d("0.000000")
    assert report.total_existing_paper_notional == d("0.000000")
    assert report.total_capped_notional == d("0.000000")
    assert report.reason_codes == ()
    assert report.rows == ()
