from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 2, 18, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module("polymarket_alpha_lab.fee_drag_response_queue")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_FEE_DRAG_RESPONSE_QUEUE_CONFIG_VERSION,
        "pressure_fee_drag_bps_threshold": d("100.000000"),
        "worsening_fee_drag_bps_delta_threshold": d("25.000000"),
        "improving_fee_drag_bps_delta_threshold": d("25.000000"),
        "stale_review_after_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return module.FeeDragResponseQueueConfig(**values)


def trend_row(scope_id: str, **overrides: object):
    module = api()
    values = {
        "scope_type": "category",
        "scope_id": scope_id,
        "source_trend_status": "stable",
        "latest_fee_drag_bps": d("20.000000"),
        "fee_drag_bps_delta": d("0.000000"),
        "latest_fee_drag_share": d("0.100000"),
        "latest_review_age_seconds": d("3600.000000"),
        "reason_codes": ("fee_drag_trend_stable",),
    }
    values.update(overrides)
    return module.FeeDragTrendRow(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_fee_drag_response_queue_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_response_queue_maps_fee_drag_trends_to_report_only_statuses() -> None:
    module = api()
    queue = report(
        trend_row(
            "crypto",
            source_trend_status="watch",
            latest_fee_drag_bps=d("125.000000"),
            fee_drag_bps_delta=d("10.000000"),
            latest_fee_drag_share=d("0.650000"),
            reason_codes=("fee_drag_trend_issue_flags_present",),
        ),
        trend_row(
            "macro",
            source_trend_status="watch",
            latest_fee_drag_bps=d("80.000000"),
            fee_drag_bps_delta=d("30.000000"),
            latest_fee_drag_share=d("0.300000"),
            reason_codes=("fee_drag_trend_delta_threshold",),
        ),
        trend_row(
            "sports",
            latest_fee_drag_bps=d("45.000000"),
            fee_drag_bps_delta=d("-30.000000"),
            latest_fee_drag_share=d("0.200000"),
            reason_codes=("fee_drag_trend_stable",),
        ),
        trend_row(
            "politics",
            latest_fee_drag_bps=d("35.000000"),
            fee_drag_bps_delta=d("0.000000"),
            latest_review_age_seconds=d("90000.000000"),
        ),
        trend_row("culture"),
    )

    assert type(queue) is module.FeeDragResponseQueueReport
    assert is_dataclass(queue)
    assert queue.generated_at == GENERATED_AT
    assert queue.config_version == "fee-drag-response-queue-v0"
    assert queue.response_queue_status == "blocked"
    assert queue.source_row_count == d("5")
    assert queue.row_count == d("5")
    assert queue.fee_drag_pressure_count == d("1")
    assert queue.worsening_drag_count == d("1")
    assert queue.improving_drag_count == d("1")
    assert queue.stale_review_count == d("1")
    assert queue.normal_count == d("1")
    assert queue.max_latest_fee_drag_bps == d("125.000000")
    assert queue.max_latest_fee_drag_share == d("0.650000")
    assert queue.reason_codes == (
        "fee_drag_pressure_response_required",
        "worsening_fee_drag_response_required",
        "improving_fee_drag_observed",
        "stale_fee_drag_review_response_required",
        "normal_fee_drag_observed",
    )
    assert queue.boundary_statement == (
        "Report-only fee drag response queue; no guidance or execution instructions."
    )
    assert queue.paper_only is True
    assert queue.report_only is True
    assert queue.readonly is True

    assert tuple(row.response_queue_status for row in queue.rows) == (
        "fee_drag_pressure_response_required",
        "worsening_fee_drag_response_required",
        "stale_fee_drag_review_response_required",
        "improving_fee_drag_observed",
        "normal_fee_drag",
    )
    pressure = queue.rows[0]
    assert pressure == module.FeeDragResponseQueueRow(
        scope_type="category",
        scope_id="crypto",
        response_queue_status="fee_drag_pressure_response_required",
        source_trend_status="watch",
        latest_fee_drag_bps=d("125.000000"),
        fee_drag_bps_delta=d("10.000000"),
        latest_fee_drag_share=d("0.650000"),
        latest_review_age_seconds=d("3600.000000"),
        reason_codes=("fee_drag_pressure_response_required",),
    )


def test_response_queue_reports_empty_and_normal_states() -> None:
    empty = report()
    normal = report(trend_row("crypto"))

    assert empty.response_queue_status == "pass"
    assert empty.source_row_count == d("0")
    assert empty.rows == ()
    assert empty.reason_codes == ("no_fee_drag_trend_rows_supplied",)
    assert empty.max_latest_fee_drag_bps is None
    assert empty.max_latest_fee_drag_share is None
    assert normal.response_queue_status == "pass"
    assert normal.reason_codes == ("normal_fee_drag_observed",)
    assert normal.rows[0].response_queue_status == "normal_fee_drag"


def test_response_queue_preserves_overlapping_reason_codes() -> None:
    queue = report(
        trend_row(
            "crypto",
            source_trend_status="watch",
            latest_fee_drag_bps=d("150.000000"),
            fee_drag_bps_delta=d("40.000000"),
            latest_review_age_seconds=d("90000.000000"),
            reason_codes=("fee_drag_trend_issue_flags_present",),
        ),
    )

    assert queue.rows[0].response_queue_status == "fee_drag_pressure_response_required"
    assert queue.rows[0].reason_codes == (
        "fee_drag_pressure_response_required",
        "worsening_fee_drag_response_required",
        "stale_fee_drag_review_response_required",
    )
    assert queue.reason_codes == (
        "fee_drag_pressure_response_required",
        "worsening_fee_drag_response_required",
        "stale_fee_drag_review_response_required",
    )


def test_payload_is_json_ready_redacted_and_has_no_execution_surface_language() -> None:
    payload = api().fee_drag_response_queue_payload(
        report(
            trend_row(
                "crypto",
                source_trend_status="watch",
                latest_fee_drag_bps=d("120.000000"),
                reason_codes=("fee_drag_trend_issue_flags_present",),
            ),
        ),
    )

    payload_text = repr(payload).lower()
    for forbidden in (
        "market_slug",
        "question",
        "payload",
        "recommend",
        "wallet",
        "account",
        "order",
        "trade",
        "auth",
    ):
        assert forbidden not in payload_text
    assert payload["source_row_count"] == "1"
    assert payload["rows"][0]["scope_id"] == "crypto"
    assert payload["rows"][0]["response_queue_status"] == (
        "fee_drag_pressure_response_required"
    )
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64


def test_validation_digest_is_deterministic_and_revalidated() -> None:
    module = api()
    queue = report(
        trend_row("culture"),
        trend_row(
            "crypto",
            source_trend_status="watch",
            latest_fee_drag_bps=d("125.000000"),
            latest_fee_drag_share=d("0.650000"),
            reason_codes=("fee_drag_trend_issue_flags_present",),
        ),
    )
    rebuilt = report(
        trend_row(
            "crypto",
            source_trend_status="watch",
            latest_fee_drag_bps=d("125.000000"),
            latest_fee_drag_share=d("0.650000"),
            reason_codes=("fee_drag_trend_issue_flags_present",),
        ),
        trend_row("culture"),
    )
    changed = report(
        trend_row("culture"),
        trend_row(
            "crypto",
            source_trend_status="watch",
            latest_fee_drag_bps=d("126.000000"),
            latest_fee_drag_share=d("0.650000"),
            reason_codes=("fee_drag_trend_issue_flags_present",),
        ),
    )

    assert queue.derived_validation_digest == rebuilt.derived_validation_digest
    assert queue.derived_validation_digest != changed.derived_validation_digest
    assert queue.derived_validation_digest == module.fee_drag_response_queue_payload(queue)[
        "derived_validation_digest"
    ]
    assert all(char in "0123456789abcdef" for char in queue.derived_validation_digest)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(queue, derived_validation_digest="0" * 64)


def test_response_queue_dataclasses_are_frozen_strict_and_consistent() -> None:
    module = api()
    queue = report(
        trend_row(
            "crypto",
            source_trend_status="watch",
            latest_fee_drag_bps=d("120.000000"),
            reason_codes=("fee_drag_trend_issue_flags_present",),
        ),
    )

    assert module.__all__ == (
        "DEFAULT_FEE_DRAG_RESPONSE_QUEUE_CONFIG_VERSION",
        "FeeDragResponseQueueConfig",
        "FeeDragResponseQueueReport",
        "FeeDragResponseQueueRow",
        "FeeDragTrendRow",
        "build_fee_drag_response_queue_report",
        "fee_drag_response_queue_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        queue.response_queue_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" fee-drag-response-queue-v0")
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 2, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="Decimal"):
        replace(queue.rows[0], latest_fee_drag_bps=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="scope_id"):
        trend_row(_StringSubclass("crypto"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(queue.rows[0], reason_codes=("normal_fee_drag_observed",))
    normal_queue = report(trend_row("culture"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            normal_queue.rows[0],
            reason_codes=("no_fee_drag_trend_rows_supplied",),
        )
    overlap_queue = report(
        trend_row(
            "macro",
            source_trend_status="watch",
            latest_fee_drag_bps=d("125.000000"),
            fee_drag_bps_delta=d("30.000000"),
            reason_codes=("fee_drag_trend_issue_flags_present",),
        ),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            overlap_queue.rows[0],
            reason_codes=(
                "worsening_fee_drag_response_required",
                "fee_drag_pressure_response_required",
            ),
        )
    with pytest.raises(ValueError, match="row_count"):
        replace(queue, row_count=d("2"))


def test_response_queue_rejects_wrong_inputs_duplicates_and_invalid_values() -> None:
    module = api()
    row = trend_row("crypto")

    with pytest.raises(ValueError, match="FeeDragResponseQueueConfig"):
        module.build_fee_drag_response_queue_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows must be a list or tuple"):
        module.build_fee_drag_response_queue_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="FeeDragTrendRow"):
        report(object())
    with pytest.raises(ValueError, match="deterministic"):
        report(row, row)
    with pytest.raises(ValueError, match="latest_fee_drag_share"):
        trend_row("crypto", latest_fee_drag_share=d("1.000001"))
    with pytest.raises(ValueError, match="nonnegative"):
        trend_row("crypto", latest_fee_drag_bps=d("-1.000000"))
    offset_report = report(
        generated_at=datetime(2026, 7, 2, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert offset_report.generated_at == GENERATED_AT


def test_module_scope_is_pure_report_readonly_and_decimal_only() -> None:
    source = Path("src/polymarket_alpha_lab/fee_drag_response_queue.py").read_text(
        encoding="utf-8",
    )
    lowered = source.lower()
    for forbidden in (
        "market_slug",
        "question",
        "payload_json",
        "investment",
        "advice",
        "trade",
        "wallet",
        "account",
        "order",
        "auth",
        "clob",
        "private_key",
        "open(",
        "psycopg",
        "supabase",
        "requests",
        "http",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
