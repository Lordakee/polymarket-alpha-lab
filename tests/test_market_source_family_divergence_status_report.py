from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_source_family_divergence_status_report"
GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> Any:
    return import_module(MODULE_NAME)


def at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def row(
    market_id: str,
    category_id: str,
    workflow_state: str,
    *,
    detected_at: datetime,
    updated_at: datetime | None = None,
    official_observed_at: datetime | None = None,
    proxy_observed_at: datetime | None = None,
    acknowledged_at: datetime | None = None,
    cleared_at: datetime | None = None,
) -> object:
    module = api()
    return module.MarketSourceFamilyDivergenceStatusInputRow(
        market_id=market_id,
        category_id=category_id,
        workflow_state=workflow_state,
        detected_at=detected_at,
        updated_at=updated_at or detected_at,
        official_observed_at=official_observed_at,
        proxy_observed_at=proxy_observed_at,
        acknowledged_at=acknowledged_at,
        cleared_at=cleared_at,
    )


def config(**overrides: object) -> object:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_STATUS_REPORT_CONFIG_VERSION
        ),
        "overdue_after_seconds": d("3600.000000"),
        "official_stale_after_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return module.MarketSourceFamilyDivergenceStatusConfig(**values)


def report(*rows: object, generated_at: datetime = GENERATED_AT) -> object:
    module = api()
    return module.build_market_source_family_divergence_status_report(
        rows,
        config=config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError("payload contains float")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_status_report_summarizes_all_workflow_states_with_decimal_metrics() -> None:
    module = api()

    status_report = report(
        row(
            "market-cleared",
            "sports",
            "cleared",
            detected_at=at(hours=2),
            updated_at=at(minutes=5),
            official_observed_at=at(minutes=5),
            proxy_observed_at=at(minutes=5),
            cleared_at=at(minutes=5),
        ),
        row(
            "market-open",
            "weather",
            "open",
            detected_at=at(minutes=20),
            updated_at=at(minutes=20),
            official_observed_at=at(minutes=15),
            proxy_observed_at=at(minutes=10),
        ),
        row(
            "market-blocked",
            "politics",
            "blocked",
            detected_at=at(hours=2),
            updated_at=at(hours=1),
            official_observed_at=at(minutes=20),
            proxy_observed_at=at(minutes=15),
        ),
        row(
            "market-acknowledged",
            "macro",
            "acknowledged",
            detected_at=at(minutes=45),
            updated_at=at(minutes=10),
            official_observed_at=at(minutes=20),
            proxy_observed_at=at(minutes=15),
            acknowledged_at=at(minutes=10),
        ),
        row(
            "market-stale-official",
            "commodities",
            "open",
            detected_at=at(minutes=25),
            updated_at=at(minutes=25),
            official_observed_at=at(hours=2),
            proxy_observed_at=at(minutes=10),
        ),
        row(
            "market-overdue",
            "crypto",
            "open",
            detected_at=at(hours=3),
            updated_at=at(hours=3),
            official_observed_at=at(minutes=30),
            proxy_observed_at=at(minutes=20),
        ),
        row(
            "market-proxy-only",
            "finance",
            "open",
            detected_at=at(minutes=10),
            updated_at=at(minutes=10),
            proxy_observed_at=at(minutes=5),
        ),
    )

    assert type(status_report) is module.MarketSourceFamilyDivergenceStatusReport
    assert is_dataclass(status_report)
    assert status_report.generated_at == GENERATED_AT
    assert status_report.config_version == (
        module.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_STATUS_REPORT_CONFIG_VERSION
    )
    assert status_report.report_status == "blocked"
    assert status_report.reason_codes == (
        "market_source_family_divergence_status_blocked",
        "market_source_family_divergence_status_overdue",
        "market_source_family_divergence_status_stale_official",
        "market_source_family_divergence_status_proxy_only",
        "market_source_family_divergence_status_open",
        "market_source_family_divergence_status_acknowledged",
        "market_source_family_divergence_status_cleared",
    )
    assert status_report.market_count == d("7.000000")
    assert status_report.open_count == d("4.000000")
    assert status_report.overdue_count == d("1.000000")
    assert status_report.blocked_count == d("1.000000")
    assert status_report.acknowledged_count == d("1.000000")
    assert status_report.cleared_count == d("1.000000")
    assert status_report.stale_official_count == d("1.000000")
    assert status_report.proxy_only_count == d("1.000000")
    assert status_report.actionable_count == d("5.000000")
    assert status_report.open_ratio == d("0.571429")
    assert status_report.overdue_ratio == d("0.142857")
    assert status_report.blocked_ratio == d("0.142857")
    assert status_report.acknowledged_ratio == d("0.142857")
    assert status_report.cleared_ratio == d("0.142857")
    assert status_report.stale_official_ratio == d("0.142857")
    assert status_report.proxy_only_ratio == d("0.142857")
    assert status_report.actionable_ratio == d("0.714286")
    assert status_report.max_divergence_age_seconds == d("10800.000000")
    assert status_report.max_source_age_seconds == d("7200.000000")
    assert status_report.paper_only is True
    assert status_report.report_only is True
    assert status_report.readonly is True

    assert tuple(item.market_id for item in status_report.rows) == (
        "market-blocked",
        "market-overdue",
        "market-stale-official",
        "market-proxy-only",
        "market-open",
        "market-acknowledged",
        "market-cleared",
    )

    blocked = status_report.rows[0]
    assert blocked.row_status == "blocked"
    assert blocked.workflow_state == "blocked"
    assert blocked.divergence_age_seconds == d("7200.000000")
    assert blocked.source_age_seconds == d("1200.000000")
    assert blocked.reason_codes == (
        "market_source_family_divergence_status_blocked",
    )

    overdue = status_report.rows[1]
    assert overdue.row_status == "overdue"
    assert overdue.divergence_age_seconds == d("10800.000000")
    assert overdue.reason_codes == (
        "market_source_family_divergence_status_overdue",
    )

    stale = status_report.rows[2]
    assert stale.row_status == "stale_official"
    assert stale.official_source_age_seconds == d("7200.000000")
    assert stale.reason_codes == (
        "market_source_family_divergence_status_stale_official",
    )

    proxy = status_report.rows[3]
    assert proxy.row_status == "proxy_only"
    assert proxy.official_source_age_seconds == d("0.000000")
    assert proxy.proxy_source_age_seconds == d("300.000000")
    assert proxy.reason_codes == (
        "market_source_family_divergence_status_proxy_only",
    )

    assert status_report.rows[-1].row_status == "cleared"


def test_empty_report_is_clear_and_payload_is_json_ready_without_floats() -> None:
    module = api()
    empty_report = report()

    assert empty_report.report_status == "clear"
    assert empty_report.reason_codes == (
        "market_source_family_divergence_status_clear",
    )
    assert empty_report.market_count == d("0.000000")
    assert empty_report.actionable_ratio == d("0.000000")
    assert empty_report.rows == ()

    payload = module.market_source_family_divergence_status_report_payload(
        report(
            row(
                "market-proxy-only",
                "finance",
                "open",
                detected_at=at(minutes=10),
                updated_at=at(minutes=10),
                proxy_observed_at=at(minutes=5),
            ),
        ),
    )

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["proxy_only_ratio"] == "1.000000"
    assert payload["rows"][0]["row_status"] == "proxy_only"
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_validation_rejects_non_decimal_config_naive_time_future_rows_and_mutation() -> None:
    module = api()

    with pytest.raises(ValueError, match="overdue_after_seconds must be a Decimal"):
        config(overdue_after_seconds=3600)

    with pytest.raises(ValueError, match="config_version contains unsafe text"):
        config(config_version="token-config-v0")

    with pytest.raises(ValueError, match="detected_at must be timezone-aware"):
        row(
            "market-naive",
            "politics",
            "open",
            detected_at=datetime(2026, 7, 2, 11, 0),
            updated_at=at(hours=1),
        )

    with pytest.raises(ValueError, match="input rows must not contain duplicate"):
        report(
            row(
                "market-dupe",
                "politics",
                "open",
                detected_at=at(minutes=10),
                updated_at=at(minutes=10),
            ),
            row(
                "market-dupe",
                "politics",
                "open",
                detected_at=at(minutes=5),
                updated_at=at(minutes=5),
            ),
        )

    with pytest.raises(ValueError, match="detected_at must not be after generated_at"):
        report(
            row(
                "market-future",
                "politics",
                "open",
                detected_at=GENERATED_AT + timedelta(seconds=1),
                updated_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    with pytest.raises(ValueError, match="acknowledged rows require acknowledged_at"):
        row(
            "market-bad-ack",
            "politics",
            "acknowledged",
            detected_at=at(minutes=20),
            updated_at=at(minutes=10),
        )

    sample = row(
        "market-frozen",
        "politics",
        "open",
        detected_at=at(minutes=10),
        updated_at=at(minutes=10),
    )
    with pytest.raises(FrozenInstanceError):
        sample.market_id = "changed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(sample, paper_only=False)

    converted = report(
        row(
            "market-offset",
            "politics",
            "open",
            detected_at=datetime(2026, 7, 2, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
            updated_at=datetime(2026, 7, 2, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
    )
    assert converted.rows[0].detected_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert type(module.MarketSourceFamilyDivergenceStatusConfig()) is (
        module.MarketSourceFamilyDivergenceStatusConfig
    )


def test_module_scope_has_no_disallowed_runtime_or_numeric_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_source_family_divergence_status_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "network",
        "persistence",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
        "fast",
        "open(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
