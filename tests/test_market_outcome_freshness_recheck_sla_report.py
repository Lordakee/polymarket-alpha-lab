from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_outcome_freshness_recheck_sla_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(
    condition_id: str,
    *,
    outcome_key: str = "yes",
    queued_at: datetime = datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
    recheck_due_at: datetime = datetime(2026, 7, 2, 11, 30, tzinfo=UTC),
    owner_team_id: str | None = "research",
    official_source_checked_at: datetime = datetime(2026, 7, 2, 11, 45, tzinfo=UTC),
    proxy_contradicts_official: bool = False,
    team_acknowledged_at: datetime | None = datetime(2026, 7, 2, 10, 10, tzinfo=UTC),
):
    report_module = module()
    return report_module.MarketOutcomeFreshnessRecheckSlaItem(
        condition_id=condition_id,
        outcome_key=outcome_key,
        queued_at=queued_at,
        recheck_due_at=recheck_due_at,
        owner_team_id=owner_team_id,
        official_source_checked_at=official_source_checked_at,
        proxy_contradicts_official=proxy_contradicts_official,
        team_acknowledged_at=team_acknowledged_at,
    )


def build_report(*items):
    report_module = module()
    return report_module.build_market_outcome_freshness_recheck_sla_report(
        items,
        config=report_module.MarketOutcomeFreshnessRecheckSlaConfig(
            config_version="market-outcome-freshness-recheck-sla-test-v0",
            stale_official_source_after_seconds=d("3600.000000"),
            team_ack_lag_after_seconds=d("900.000000"),
        ),
        generated_at=GENERATED_AT,
    )


def assert_json_ready_without_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if isinstance(value, dict):
        for nested_value in value.values():
            assert_json_ready_without_floats(nested_value)
        return
    if isinstance(value, (list, tuple)):
        for nested_value in value:
            assert_json_ready_without_floats(nested_value)
        return
    assert value is None or isinstance(value, (str, bool))


def test_builds_report_for_overdue_missing_owner_stale_proxy_and_ack_lag() -> None:
    report = build_report(
        item(
            "condition-pass",
            recheck_due_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
        ),
        item(
            "condition-overdue",
            recheck_due_at=datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
        ),
        item(
            "condition-missing-owner",
            owner_team_id=None,
            recheck_due_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
        ),
        item(
            "condition-stale-source",
            recheck_due_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
            official_source_checked_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
        ),
        item(
            "condition-proxy",
            recheck_due_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
            proxy_contradicts_official=True,
        ),
        item(
            "condition-ack-lag",
            recheck_due_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 20, tzinfo=UTC),
        ),
    )

    assert report.sla_status == "blocked"
    assert report.total_recheck_count == d("6.000000")
    assert report.pass_recheck_count == d("1.000000")
    assert report.watch_recheck_count == d("3.000000")
    assert report.blocked_recheck_count == d("2.000000")
    assert report.overdue_recheck_count == d("1.000000")
    assert report.missing_owner_count == d("1.000000")
    assert report.stale_official_source_count == d("1.000000")
    assert report.proxy_contradiction_count == d("1.000000")
    assert report.team_ack_lag_count == d("1.000000")
    assert report.clear_recheck_ratio == d("0.166667")
    assert report.reason_codes == (
        "missing_recheck_owner",
        "proxy_contradicts_official_source",
        "recheck_sla_overdue",
        "official_source_stale",
        "team_acknowledgement_lag",
    )
    assert tuple(row.condition_id for row in report.rows) == (
        "condition-missing-owner",
        "condition-proxy",
        "condition-ack-lag",
        "condition-overdue",
        "condition-stale-source",
        "condition-pass",
    )
    assert report.rows[0].sla_status == "blocked"
    assert report.rows[0].reason_codes == ("missing_recheck_owner",)
    assert report.rows[1].reason_codes == ("proxy_contradicts_official_source",)
    assert report.rows[2].sla_status == "watch"
    assert report.rows[2].team_ack_lag_seconds == d("1200.000000")
    assert report.rows[3].overdue_by_seconds == d("3600.000000")
    assert report.rows[4].official_source_age_seconds == d("10800.000000")
    assert report.rows[5].sla_status == "pass"
    assert report.rows[5].reason_codes == ("outcome_freshness_recheck_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_queue_blocks_without_dividing_by_zero() -> None:
    report = build_report()

    assert report.sla_status == "blocked"
    assert report.total_recheck_count == d("0.000000")
    assert report.clear_recheck_ratio == d("0.000000")
    assert report.reason_codes == ("no_outcome_freshness_rechecks",)
    assert report.rows == ()


def test_json_payload_helper_is_json_ready_and_contains_no_floats() -> None:
    report_module = module()
    report = build_report(
        item(
            "condition-json",
            recheck_due_at=datetime(2026, 7, 2, 12, 30, tzinfo=UTC),
        ),
    )

    payload = report_module.market_outcome_freshness_recheck_sla_report_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["total_recheck_count"] == "1.000000"
    assert payload["clear_recheck_ratio"] == "1.000000"
    assert payload["rows"][0]["queue_age_seconds"] == "7200.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert_json_ready_without_floats(payload)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_and_public_decimal_fields_use_decimal() -> None:
    report_module = module()

    assert report_module.__all__ == (
        "DEFAULT_MARKET_OUTCOME_FRESHNESS_RECHECK_SLA_CONFIG_VERSION",
        "MarketOutcomeFreshnessRecheckSlaConfig",
        "MarketOutcomeFreshnessRecheckSlaItem",
        "MarketOutcomeFreshnessRecheckSlaReport",
        "MarketOutcomeFreshnessRecheckSlaRow",
        "build_market_outcome_freshness_recheck_sla_report",
        "market_outcome_freshness_recheck_sla_report_payload",
    )
    for exported_name in report_module.__all__:
        value = getattr(report_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(item("condition-frozen"))
    with pytest.raises(FrozenInstanceError):
        report.rows[0].sla_status = "blocked"  # type: ignore[misc]

    public_decimal_suffixes = ("count", "ratio", "seconds")
    for value in (report, *report.rows):
        for field in fields(value):
            if field.name.endswith(public_decimal_suffixes):
                assert type(getattr(value, field.name)) is Decimal


def test_aware_datetimes_are_required_and_normalized_to_utc() -> None:
    report_module = module()

    report = report_module.build_market_outcome_freshness_recheck_sla_report(
        (
            item(
                "condition-timezone",
                queued_at=datetime(
                    2026,
                    7,
                    2,
                    5,
                    0,
                    tzinfo=timezone.utc,
                ),
                recheck_due_at=datetime(
                    2026,
                    7,
                    2,
                    8,
                    0,
                    tzinfo=timezone.utc,
                ),
                official_source_checked_at=datetime(
                    2026,
                    7,
                    2,
                    8,
                    30,
                    tzinfo=timezone.utc,
                ),
            ),
        ),
        config=report_module.MarketOutcomeFreshnessRecheckSlaConfig(),
        generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].queued_at == datetime(2026, 7, 2, 5, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report_module.build_market_outcome_freshness_recheck_sla_report(
            (),
            config=report_module.MarketOutcomeFreshnessRecheckSlaConfig(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="queued_at must be timezone-aware"):
        item("condition-naive", queued_at=datetime(2026, 7, 2, 10, 0))


def test_rejects_float_and_decimal_subclass_thresholds() -> None:
    report_module = module()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="stale_official_source_after_seconds"):
        report_module.MarketOutcomeFreshnessRecheckSlaConfig(
            stale_official_source_after_seconds=1.0,
        )
    with pytest.raises(ValueError, match="team_ack_lag_after_seconds"):
        report_module.MarketOutcomeFreshnessRecheckSlaConfig(
            team_ack_lag_after_seconds=DerivedDecimal("1.000000"),
        )


def test_module_omits_forbidden_runtime_surfaces() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "persistence",
        "network",
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
    ):
        assert forbidden not in lowered
