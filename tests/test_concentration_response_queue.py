from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.position_concentration_trend_monitor import (
    PositionConcentrationTrendRow,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
REVIEWED_AT = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module("polymarket_alpha_lab.concentration_response_queue")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_CONCENTRATION_RESPONSE_QUEUE_CONFIG_VERSION,
        "stale_review_seconds": d("172800.000000"),
    }
    values.update(overrides)
    return module.ConcentrationResponseQueueConfig(**values)


def trend_row(
    group_type: str,
    *,
    latest_open_notional: Decimal = d("100.000000"),
    latest_share: Decimal = d("0.500000"),
    threshold_share: Decimal = d("0.400000"),
    share_delta: Decimal | None = d("0.050000"),
    trend_rate: Decimal | None = d("0.100000"),
    persistent: bool = False,
    trend_status: str = "declining",
    status: str = "blocked",
    reason_codes: tuple[str, ...] = ("group_concentration_declining",),
) -> PositionConcentrationTrendRow:
    return PositionConcentrationTrendRow(
        group_type=group_type,
        group_value="[REDACTED]",
        latest_position_count=d("2"),
        latest_open_notional=latest_open_notional,
        latest_share_of_total_open_notional=latest_share,
        threshold_share=threshold_share,
        share_delta=share_delta,
        concentration_trend_rate=trend_rate,
        persistent_pressure_flag=persistent,
        trend_status=trend_status,
        status=status,
        reason_codes=reason_codes,
    )


def response_report(*rows: PositionConcentrationTrendRow, cfg=None):
    module = api()
    return module.build_concentration_response_queue_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_response_queue_maps_trend_rows_to_disjoint_statuses() -> None:
    module = api()
    report = response_report(
        trend_row(
            "market",
            latest_share=d("0.850000"),
            persistent=True,
            reason_codes=(
                "group_persistent_pressure",
                "group_concentration_declining",
            ),
        ),
        trend_row(
            "category",
            latest_share=d("0.750000"),
            persistent=False,
            trend_status="declining",
            reason_codes=("group_concentration_declining",),
        ),
        trend_row(
            "team",
            latest_share=d("0.350000"),
            threshold_share=d("0.700000"),
            share_delta=d("-0.200000"),
            trend_rate=d("-0.363636"),
            trend_status="improving",
            status="pass",
            reason_codes=("group_concentration_improving",),
        ),
        trend_row(
            "outcome_side",
            latest_share=d("0.400000"),
            threshold_share=d("0.400000"),
            share_delta=d("0.000000"),
            trend_rate=d("0.000000"),
            trend_status="unchanged",
            status="pass",
            reason_codes=("group_concentration_trend_clear",),
        ),
        trend_row(
            "market",
            latest_share=d("0.300000"),
            threshold_share=d("0.500000"),
            share_delta=d("0.000000"),
            trend_rate=d("0.000000"),
            trend_status="unchanged",
            status="pass",
            reason_codes=("group_concentration_trend_clear",),
        ),
        cfg=config(
            last_reviewed_at=REVIEWED_AT,
            stale_review_seconds=d("86400.000000"),
        ),
    )

    assert type(report) is module.ConcentrationResponseQueueReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "concentration-response-queue-v0"
    assert report.response_queue_status == "blocked"
    assert report.source_row_count == d("5")
    assert report.row_count == d("5")
    assert report.persistent_pressure_count == d("1")
    assert report.worsening_concentration_count == d("1")
    assert report.improving_concentration_count == d("1")
    assert report.stale_review_count == d("1")
    assert report.normal_count == d("1")
    assert report.max_latest_share_of_total_open_notional == d("0.850000")
    assert report.max_review_age_seconds == d("172800.000000")
    assert report.reason_codes == (
        "persistent_concentration_pressure_present",
        "worsening_concentration_present",
        "improving_concentration_observed",
        "stale_concentration_review_present",
        "normal_concentration_observed",
    )
    assert report.boundary_statement == (
        "Report-only concentration response queue; no guidance or execution instructions."
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.response_queue_status for row in report.rows) == (
        "persistent_concentration_pressure",
        "worsening_concentration",
        "improving_concentration",
        "stale_review",
        "normal",
    )
    assert report.rows[0] == module.ConcentrationResponseQueueRow(
        group_type="market",
        group_value="[REDACTED]",
        response_queue_status="persistent_concentration_pressure",
        source_trend_status="declining",
        source_status="blocked",
        latest_position_count=d("2"),
        latest_open_notional=d("100.000000"),
        latest_share_of_total_open_notional=d("0.850000"),
        threshold_share=d("0.400000"),
        share_delta=d("0.050000"),
        concentration_trend_rate=d("0.100000"),
        persistent_pressure_flag=True,
        review_age_seconds=d("172800.000000"),
        reason_codes=("persistent_concentration_pressure_present",),
    )


def test_response_queue_reports_empty_and_normal_states() -> None:
    empty = response_report()
    normal = response_report(
        trend_row(
            "market",
            latest_share=d("0.300000"),
            threshold_share=d("0.500000"),
            share_delta=d("0.000000"),
            trend_rate=d("0.000000"),
            trend_status="unchanged",
            status="pass",
            reason_codes=("group_concentration_trend_clear",),
        ),
    )

    assert empty.response_queue_status == "pass"
    assert empty.source_row_count == d("0")
    assert empty.row_count == d("0")
    assert empty.rows == ()
    assert empty.reason_codes == ("no_concentration_trend_rows_supplied",)
    assert empty.max_latest_share_of_total_open_notional is None
    assert empty.max_review_age_seconds is None
    assert normal.response_queue_status == "pass"
    assert normal.reason_codes == ("normal_concentration_observed",)
    assert normal.rows[0].response_queue_status == "normal"


def test_response_queue_dataclasses_are_frozen_strict_and_consistent() -> None:
    module = api()
    report = response_report(trend_row("market"))

    assert module.__all__ == (
        "DEFAULT_CONCENTRATION_RESPONSE_QUEUE_CONFIG_VERSION",
        "ConcentrationResponseQueueConfig",
        "ConcentrationResponseQueueReport",
        "ConcentrationResponseQueueRow",
        "build_concentration_response_queue_report",
        "concentration_response_queue_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        report.response_queue_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("concentration-response-queue-v0"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_concentration_response_queue_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="Decimal"):
        replace(report.rows[0], latest_open_notional=_DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=("normal_concentration_observed",))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=2)


def test_response_queue_validation_digest_is_deterministic_and_revalidated() -> None:
    module = api()
    report = response_report(
        trend_row(
            "market",
            latest_share=d("0.300000"),
            threshold_share=d("0.500000"),
            trend_status="unchanged",
            status="pass",
            reason_codes=("group_concentration_trend_clear",),
        ),
        trend_row("category", latest_share=d("0.750000")),
    )
    rebuilt = response_report(
        trend_row("category", latest_share=d("0.750000")),
        trend_row(
            "market",
            latest_share=d("0.300000"),
            threshold_share=d("0.500000"),
            trend_status="unchanged",
            status="pass",
            reason_codes=("group_concentration_trend_clear",),
        ),
    )
    changed = response_report(
        trend_row(
            "market",
            latest_share=d("0.300000"),
            threshold_share=d("0.500000"),
            trend_status="unchanged",
            status="pass",
            reason_codes=("group_concentration_trend_clear",),
        ),
        trend_row("category", latest_share=d("0.760000")),
    )

    assert type(report.derived_validation_digest) is str
    assert len(report.derived_validation_digest) == 64
    assert all(char in "0123456789abcdef" for char in report.derived_validation_digest)
    assert report.derived_validation_digest == rebuilt.derived_validation_digest
    assert report.derived_validation_digest != changed.derived_validation_digest
    assert report.derived_validation_digest == module.concentration_response_queue_payload(report)[
        "derived_validation_digest"
    ]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="boundary_statement"):
        replace(report, boundary_statement="use this queue for execution")


def test_response_queue_rejects_wrong_inputs_and_duplicate_rows() -> None:
    module = api()
    row = trend_row("market")

    with pytest.raises(ValueError, match="ConcentrationResponseQueueConfig"):
        module.build_concentration_response_queue_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows must be a list or tuple"):
        module.build_concentration_response_queue_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="PositionConcentrationTrendRow"):
        module.build_concentration_response_queue_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        response_report(row, row)
    with pytest.raises(ValueError, match="last_reviewed_at must not be after generated_at"):
        response_report(
            row,
            cfg=config(last_reviewed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    offset_report = module.build_concentration_response_queue_report(
        (),
        config=config(),
        generated_at=datetime(2026, 7, 2, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert offset_report.generated_at == GENERATED_AT


def test_response_queue_sorts_collapsed_redacted_rows_deterministically() -> None:
    row = trend_row("market")
    same_public_sort_group = trend_row(
        "market",
        latest_open_notional=d("101.000000"),
    )

    report = response_report(row, same_public_sort_group)
    rebuilt = response_report(same_public_sort_group, row)

    assert tuple(queue_row.latest_open_notional for queue_row in report.rows) == (
        d("101.000000"),
        d("100.000000"),
    )
    assert report.rows == rebuilt.rows
    assert report.derived_validation_digest == rebuilt.derived_validation_digest


def test_response_queue_payload_is_redacted_json_ready_and_local_scope() -> None:
    module = api()
    report = response_report(trend_row("market"))

    payload = module.concentration_response_queue_payload(report)
    payload_text = repr(payload).lower()
    assert payload["source_row_count"] == "1.000000"
    assert payload["rows"][0]["group_value"] == "[REDACTED]"
    assert payload["max_latest_share_of_total_open_notional"] == "0.500000"
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert "market_slug" not in payload_text
    assert "question" not in payload_text
    assert "wallet" not in payload_text
    assert "order" not in payload_text
    assert "advice" not in payload_text
    assert "recommend" not in payload_text
    assert asdict(report)["readonly"] is True

    source = Path("src/polymarket_alpha_lab/concentration_response_queue.py").read_text(
        encoding="utf-8",
    )
    lowered = source.lower()
    for banned in (
        "market_slug",
        "question",
        "investment",
        "advice",
        "recommend",
        "trade",
        "buy",
        "sell",
        "order",
        "wallet",
        "auth",
        "private_key",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "open(",
        ".write(",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def test_response_queue_rejects_unredacted_public_group_values() -> None:
    module = api()
    with pytest.raises(ValueError, match="group_value"):
        module.ConcentrationResponseQueueRow(
            group_type="market",
            group_value="unredacted-public-value",
            response_queue_status="worsening_concentration",
            source_trend_status="declining",
            source_status="blocked",
            latest_position_count=d("2"),
            latest_open_notional=d("100.000000"),
            latest_share_of_total_open_notional=d("0.500000"),
            threshold_share=d("0.400000"),
            share_delta=d("0.050000"),
            concentration_trend_rate=d("0.100000"),
            persistent_pressure_flag=False,
            review_age_seconds=None,
            reason_codes=("worsening_concentration_present",),
        )
    with pytest.raises(ValueError, match="group_value"):
        response_report(
            PositionConcentrationTrendRow(
                group_type="market",
                group_value="real market slug should not surface",
                latest_position_count=d("2"),
                latest_open_notional=d("100.000000"),
                latest_share_of_total_open_notional=d("0.500000"),
                threshold_share=d("0.400000"),
                share_delta=d("0.050000"),
                concentration_trend_rate=d("0.100000"),
                persistent_pressure_flag=False,
                trend_status="declining",
                status="blocked",
                reason_codes=("group_concentration_declining",),
            ),
        )
