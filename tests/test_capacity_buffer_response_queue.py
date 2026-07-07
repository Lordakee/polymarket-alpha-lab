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
    return import_module("polymarket_alpha_lab.capacity_buffer_response_queue")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": module.DEFAULT_CAPACITY_BUFFER_RESPONSE_QUEUE_CONFIG_VERSION,
        "pressure_utilization_threshold": d("0.900000"),
        "worsening_utilization_delta_threshold": d("0.050000"),
        "improving_buffer_delta_threshold": d("100.000000"),
        "stale_review_after_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return module.CapacityBufferResponseQueueConfig(**values)


def trend_row(category_id: str, team_id: str, **overrides: object):
    module = api()
    values = {
        "category_id": category_id,
        "team_id": team_id,
        "source_capacity_status": "ready",
        "latest_utilization_ratio": d("0.500000"),
        "utilization_ratio_delta": d("0.000000"),
        "latest_remaining_capacity_buffer": d("500.000000"),
        "remaining_capacity_buffer_delta": d("0.000000"),
        "latest_over_capacity_amount": d("0.000000"),
        "latest_review_age_seconds": d("3600.000000"),
        "reason_codes": ("paper_capacity_trend_normal",),
    }
    values.update(overrides)
    return module.CapacityBufferTrendRow(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_capacity_buffer_response_queue_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_response_queue_maps_capacity_trends_to_report_only_statuses() -> None:
    module = api()
    queue = report(
        trend_row(
            "crypto",
            "alpha",
            source_capacity_status="blocked",
            latest_utilization_ratio=d("1.020000"),
            utilization_ratio_delta=d("0.010000"),
            latest_remaining_capacity_buffer=d("0.000000"),
            remaining_capacity_buffer_delta=d("-75.000000"),
            latest_over_capacity_amount=d("20.000000"),
            reason_codes=("paper_capacity_report_blocked",),
        ),
        trend_row(
            "macro",
            "beta",
            source_capacity_status="watch",
            latest_utilization_ratio=d("0.850000"),
            utilization_ratio_delta=d("0.060000"),
            latest_remaining_capacity_buffer=d("120.000000"),
            remaining_capacity_buffer_delta=d("-80.000000"),
            reason_codes=("paper_capacity_row_watch_band",),
        ),
        trend_row(
            "sports",
            "gamma",
            latest_utilization_ratio=d("0.700000"),
            utilization_ratio_delta=d("-0.080000"),
            latest_remaining_capacity_buffer=d("350.000000"),
            remaining_capacity_buffer_delta=d("125.000000"),
            reason_codes=("paper_capacity_buffer_available",),
        ),
        trend_row(
            "politics",
            "delta",
            latest_utilization_ratio=d("0.400000"),
            latest_remaining_capacity_buffer=d("900.000000"),
            latest_review_age_seconds=d("90000.000000"),
            reason_codes=("paper_capacity_buffer_available",),
        ),
        trend_row("culture", "epsilon"),
    )

    assert type(queue) is module.CapacityBufferResponseQueueReport
    assert is_dataclass(queue)
    assert queue.generated_at == GENERATED_AT
    assert queue.config_version == "capacity-buffer-response-queue-v0"
    assert queue.response_queue_status == "blocked"
    assert queue.source_row_count == d("5")
    assert queue.row_count == d("5")
    assert queue.capacity_pressure_count == d("1")
    assert queue.worsening_utilization_count == d("1")
    assert queue.improving_buffer_count == d("1")
    assert queue.stale_review_count == d("1")
    assert queue.normal_capacity_count == d("1")
    assert queue.max_latest_utilization_ratio == d("1.020000")
    assert queue.min_latest_remaining_capacity_buffer == d("0.000000")
    assert queue.reason_codes == (
        "capacity_pressure_response_required",
        "worsening_utilization_response_required",
        "improving_buffer_observed",
        "stale_capacity_review_response_required",
        "normal_capacity_observed",
    )
    assert queue.boundary_statement == (
        "Report-only capacity buffer response queue; no live execution surface."
    )
    assert queue.paper_only is True
    assert queue.report_only is True
    assert queue.readonly is True

    assert tuple(row.response_queue_status for row in queue.rows) == (
        "capacity_pressure_response_required",
        "worsening_utilization_response_required",
        "stale_capacity_review_response_required",
        "improving_buffer_observed",
        "normal_capacity",
    )
    pressure = queue.rows[0]
    assert pressure == module.CapacityBufferResponseQueueRow(
        category_id="crypto",
        team_id="alpha",
        response_queue_status="capacity_pressure_response_required",
        source_capacity_status="blocked",
        latest_utilization_ratio=d("1.020000"),
        utilization_ratio_delta=d("0.010000"),
        latest_remaining_capacity_buffer=d("0.000000"),
        remaining_capacity_buffer_delta=d("-75.000000"),
        latest_over_capacity_amount=d("20.000000"),
        latest_review_age_seconds=d("3600.000000"),
        reason_codes=("capacity_pressure_response_required",),
    )


def test_response_queue_reports_empty_and_normal_states() -> None:
    empty = report()
    normal = report(trend_row("crypto", "alpha"))

    assert empty.response_queue_status == "pass"
    assert empty.source_row_count == d("0")
    assert empty.rows == ()
    assert empty.reason_codes == ("no_capacity_buffer_trend_rows_supplied",)
    assert empty.max_latest_utilization_ratio is None
    assert empty.min_latest_remaining_capacity_buffer is None
    assert normal.response_queue_status == "pass"
    assert normal.reason_codes == ("normal_capacity_observed",)
    assert normal.rows[0].response_queue_status == "normal_capacity"


def test_response_queue_preserves_overlapping_reason_codes() -> None:
    queue = report(
        trend_row(
            "crypto",
            "alpha",
            source_capacity_status="watch",
            latest_utilization_ratio=d("0.920000"),
            utilization_ratio_delta=d("0.060000"),
            latest_remaining_capacity_buffer=d("150.000000"),
            remaining_capacity_buffer_delta=d("125.000000"),
            latest_review_age_seconds=d("90000.000000"),
            reason_codes=("paper_capacity_multi_signal",),
        ),
    )

    assert queue.rows[0].response_queue_status == "capacity_pressure_response_required"
    assert queue.rows[0].reason_codes == (
        "capacity_pressure_response_required",
        "worsening_utilization_response_required",
        "improving_buffer_observed",
        "stale_capacity_review_response_required",
    )
    assert queue.reason_codes == (
        "capacity_pressure_response_required",
        "worsening_utilization_response_required",
        "improving_buffer_observed",
        "stale_capacity_review_response_required",
    )


def test_payload_is_json_ready_redacted_and_has_no_live_surface_language() -> None:
    payload = api().capacity_buffer_response_queue_payload(
        report(
            trend_row(
                "crypto",
                "alpha",
                source_capacity_status="watch",
                latest_utilization_ratio=d("0.920000"),
                latest_remaining_capacity_buffer=d("50.000000"),
                reason_codes=("paper_capacity_row_watch_band",),
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
        "advice",
        "auth",
    ):
        assert forbidden not in payload_text
    assert payload["source_row_count"] == "1"
    assert payload["rows"][0]["category_id"] == "crypto"
    assert payload["rows"][0]["response_queue_status"] == (
        "capacity_pressure_response_required"
    )
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64


def test_payload_rejects_live_surface_values() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        api().capacity_buffer_response_queue_payload(
            report(trend_row("wallet", "alpha")),
        )
    with pytest.raises(ValueError, match="unsafe"):
        api().capacity_buffer_response_queue_payload(
            report(trend_row("crypto", "order")),
        )


def test_validation_digest_is_deterministic_and_revalidated() -> None:
    module = api()
    queue = report(
        trend_row("culture", "epsilon"),
        trend_row(
            "crypto",
            "alpha",
            source_capacity_status="watch",
            latest_utilization_ratio=d("0.920000"),
            latest_remaining_capacity_buffer=d("50.000000"),
            reason_codes=("paper_capacity_row_watch_band",),
        ),
    )
    rebuilt = report(
        trend_row(
            "crypto",
            "alpha",
            source_capacity_status="watch",
            latest_utilization_ratio=d("0.920000"),
            latest_remaining_capacity_buffer=d("50.000000"),
            reason_codes=("paper_capacity_row_watch_band",),
        ),
        trend_row("culture", "epsilon"),
    )
    changed = report(
        trend_row("culture", "epsilon"),
        trend_row(
            "crypto",
            "alpha",
            source_capacity_status="watch",
            latest_utilization_ratio=d("0.930000"),
            latest_remaining_capacity_buffer=d("50.000000"),
            reason_codes=("paper_capacity_row_watch_band",),
        ),
    )

    assert queue.derived_validation_digest == rebuilt.derived_validation_digest
    assert queue.derived_validation_digest != changed.derived_validation_digest
    assert queue.derived_validation_digest == (
        module.capacity_buffer_response_queue_payload(queue)["derived_validation_digest"]
    )
    assert all(char in "0123456789abcdef" for char in queue.derived_validation_digest)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(queue, derived_validation_digest="0" * 64)


def test_response_queue_dataclasses_are_frozen_strict_and_consistent() -> None:
    module = api()
    queue = report(
        trend_row(
            "crypto",
            "alpha",
            source_capacity_status="watch",
            latest_utilization_ratio=d("0.920000"),
            latest_remaining_capacity_buffer=d("50.000000"),
            reason_codes=("paper_capacity_row_watch_band",),
        ),
    )

    assert module.__all__ == (
        "DEFAULT_CAPACITY_BUFFER_RESPONSE_QUEUE_CONFIG_VERSION",
        "CapacityBufferResponseQueueConfig",
        "CapacityBufferResponseQueueReport",
        "CapacityBufferResponseQueueRow",
        "CapacityBufferTrendRow",
        "build_capacity_buffer_response_queue_report",
        "capacity_buffer_response_queue_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        queue.response_queue_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=" capacity-buffer-response-queue-v0")
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 2, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="Decimal"):
        replace(queue.rows[0], latest_utilization_ratio=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="category_id"):
        trend_row(_StringSubclass("crypto"), "alpha")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(queue.rows[0], reason_codes=("normal_capacity_observed",))
    overlap_queue = report(
        trend_row(
            "macro",
            "beta",
            source_capacity_status="watch",
            latest_utilization_ratio=d("0.920000"),
            utilization_ratio_delta=d("0.060000"),
            latest_remaining_capacity_buffer=d("150.000000"),
            reason_codes=("paper_capacity_multi_signal",),
        ),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            overlap_queue.rows[0],
            reason_codes=(
                "worsening_utilization_response_required",
                "capacity_pressure_response_required",
            ),
        )
    with pytest.raises(ValueError, match="row_count"):
        replace(queue, row_count=d("2"))


def test_response_queue_rejects_wrong_inputs_duplicates_and_invalid_counts() -> None:
    module = api()
    row = trend_row("crypto", "alpha")

    with pytest.raises(ValueError, match="CapacityBufferResponseQueueConfig"):
        module.build_capacity_buffer_response_queue_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="rows must be a list or tuple"):
        module.build_capacity_buffer_response_queue_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="CapacityBufferTrendRow"):
        report(object())
    with pytest.raises(ValueError, match="deterministic"):
        report(row, row)
    with pytest.raises(ValueError, match="latest_over_capacity_amount"):
        trend_row(
            "crypto",
            "alpha",
            latest_over_capacity_amount=d("1.000000"),
            latest_remaining_capacity_buffer=d("1.000000"),
        )
    with pytest.raises(ValueError, match="nonnegative"):
        trend_row(
            "crypto",
            "alpha",
            latest_remaining_capacity_buffer=d("-1.000000"),
        )
    offset_report = report(
        generated_at=datetime(2026, 7, 2, 11, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert offset_report.generated_at == GENERATED_AT


def test_module_scope_is_pure_report_readonly_and_decimal_only() -> None:
    source = Path("src/polymarket_alpha_lab/capacity_buffer_response_queue.py").read_text(
        encoding="utf-8",
    )
    lowered = source.lower()
    for forbidden in (
        "market_slug",
        "question",
        "payload_json",
        "investment",
        "recommend",
        "trade instruction",
        "wallet",
        "account",
        "auth",
        "order",
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
