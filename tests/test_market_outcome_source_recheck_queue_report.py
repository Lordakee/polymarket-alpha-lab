from __future__ import annotations

import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.market_outcome_source_recheck_queue_report"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "source_stale_after_seconds": d("3600.000000"),
        "priority_outcome_age_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.MarketOutcomeSourceRecheckQueueConfig(**values)


def record(
    market_id: str,
    *,
    market_slug: str | None = None,
    outcome_id: str | None = None,
    source_id: str = "official-resolution-source",
    final_outcome_at: datetime = GENERATED_AT - timedelta(hours=1),
    source_checked_at: datetime | None = GENERATED_AT - timedelta(minutes=30),
    source_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
    expected_outcome: str | None = "yes",
    source_outcome: str | None = "yes",
):
    module = api()
    return module.MarketOutcomeSourceRecheckRecord(
        market_id=market_id,
        market_slug=market_slug or f"{market_id}-slug",
        outcome_id=outcome_id or f"{market_id}-outcome",
        source_id=source_id,
        final_outcome_at=final_outcome_at,
        source_checked_at=source_checked_at,
        source_acknowledged_at=source_acknowledged_at,
        expected_outcome=expected_outcome,
        source_outcome=source_outcome,
    )


def report(*records: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_outcome_source_recheck_queue_report(
        records,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_module_contract_names_are_available() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_empty_queue_is_readonly_decimal_digest_report_and_payload() -> None:
    module = api()

    queue = report()

    assert is_dataclass(queue)
    assert queue == module.MarketOutcomeSourceRecheckQueueReport(
        generated_at=GENERATED_AT,
        config_version=(
            module.DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_QUEUE_CONFIG_VERSION
        ),
        status="clear",
        record_count=d("0"),
        queued_count=d("0"),
        clear_count=d("0"),
        missing_source_check_count=d("0"),
        stale_source_check_count=d("0"),
        missing_acknowledgement_count=d("0"),
        source_outcome_conflict_count=d("0"),
        outcome_age_priority_count=d("0"),
        pass_count=d("0"),
        watch_count=d("0"),
        blocked_count=d("0"),
        queued_ratio=d("0.000000"),
        missing_source_check_ratio=d("0.000000"),
        stale_source_check_ratio=d("0.000000"),
        missing_acknowledgement_ratio=d("0.000000"),
        source_outcome_conflict_ratio=d("0.000000"),
        max_outcome_age_seconds=d("0.000000"),
        max_source_age_seconds=d("0.000000"),
        max_acknowledgement_lag_seconds=d("0.000000"),
        reason_codes=("market_outcome_source_recheck_queue_empty",),
        reason_code_counts=(),
        rows=(),
    )
    assert queue.paper_only is True
    assert queue.report_only is True
    assert queue.readonly is True
    assert len(queue.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in queue.derived_validation_digest)

    payload = module.market_outcome_source_recheck_queue_report_payload(queue)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["record_count"] == "0"
    assert payload["queued_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == queue.derived_validation_digest
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_payload(payload)
    assert_no_unsafe_public_surface(payload)
    assert module.validate_market_outcome_source_recheck_queue_public_payload(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_recheck_queue_summarizes_source_rechecks_with_counts_and_sorting() -> None:
    queue = report(
        record(
            "market-pass",
            market_slug="alpha-clear",
            final_outcome_at=GENERATED_AT - timedelta(hours=1),
            source_checked_at=GENERATED_AT - timedelta(minutes=20),
            source_acknowledged_at=GENERATED_AT - timedelta(minutes=10),
            expected_outcome="yes",
            source_outcome="yes",
        ),
        record(
            "market-blocked",
            market_slug="beta-blocked",
            final_outcome_at=GENERATED_AT - timedelta(hours=5),
            source_checked_at=None,
            source_acknowledged_at=None,
            expected_outcome="yes",
            source_outcome="no",
        ),
        record(
            "market-watch",
            market_slug="gamma-watch",
            final_outcome_at=GENERATED_AT - timedelta(hours=3),
            source_checked_at=GENERATED_AT - timedelta(hours=2),
            source_acknowledged_at=GENERATED_AT - timedelta(minutes=30),
            expected_outcome="yes",
            source_outcome="yes",
        ),
    )

    assert queue.status == "blocked"
    assert queue.record_count == d("3")
    assert queue.queued_count == d("2")
    assert queue.clear_count == d("1")
    assert queue.missing_source_check_count == d("1")
    assert queue.stale_source_check_count == d("1")
    assert queue.missing_acknowledgement_count == d("1")
    assert queue.source_outcome_conflict_count == d("1")
    assert queue.outcome_age_priority_count == d("2")
    assert queue.pass_count == d("1")
    assert queue.watch_count == d("1")
    assert queue.blocked_count == d("1")
    assert queue.queued_ratio == d("0.666667")
    assert queue.missing_source_check_ratio == d("0.333333")
    assert queue.stale_source_check_ratio == d("0.333333")
    assert queue.missing_acknowledgement_ratio == d("0.333333")
    assert queue.source_outcome_conflict_ratio == d("0.333333")
    assert queue.max_outcome_age_seconds == d("18000.000000")
    assert queue.max_source_age_seconds == d("7200.000000")
    assert queue.max_acknowledgement_lag_seconds == d("18000.000000")
    assert queue.reason_codes == (
        "market_outcome_source_recheck_missing_source_check",
        "market_outcome_source_recheck_stale_source_check",
        "market_outcome_source_recheck_missing_acknowledgement",
        "market_outcome_source_recheck_source_outcome_conflict",
        "market_outcome_source_recheck_outcome_age_priority",
    )
    assert tuple(item.reason_code for item in queue.reason_code_counts) == queue.reason_codes

    assert tuple(row.market_id for row in queue.rows) == (
        "market-blocked",
        "market-watch",
        "market-pass",
    )

    blocked = queue.rows[0]
    assert blocked.queue_status == "blocked"
    assert blocked.outcome_age_seconds == d("18000.000000")
    assert blocked.source_age_seconds is None
    assert blocked.acknowledgement_lag_seconds == d("18000.000000")
    assert blocked.source_checked_after_outcome is False
    assert blocked.source_acknowledged_after_outcome is False
    assert blocked.reason_codes == (
        "market_outcome_source_recheck_missing_source_check",
        "market_outcome_source_recheck_missing_acknowledgement",
        "market_outcome_source_recheck_source_outcome_conflict",
        "market_outcome_source_recheck_outcome_age_priority",
    )

    watch = queue.rows[1]
    assert watch.queue_status == "watch"
    assert watch.source_age_seconds == d("7200.000000")
    assert watch.reason_codes == (
        "market_outcome_source_recheck_stale_source_check",
        "market_outcome_source_recheck_outcome_age_priority",
    )

    clear = queue.rows[2]
    assert clear.queue_status == "pass"
    assert clear.reason_codes == ()


def test_timezone_normalization_and_decimal_string_payload() -> None:
    eastern = timezone(timedelta(hours=-4))
    queue = report(
        record(
            "market-tz",
            final_outcome_at=datetime(2026, 7, 2, 7, 0, tzinfo=eastern),
            source_checked_at=datetime(2026, 7, 2, 7, 30, tzinfo=eastern),
            source_acknowledged_at=datetime(2026, 7, 2, 7, 45, tzinfo=eastern),
        ),
    )

    row = queue.rows[0]
    assert row.final_outcome_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert row.source_checked_at == datetime(2026, 7, 2, 11, 30, tzinfo=UTC)
    assert row.source_acknowledged_at == datetime(2026, 7, 2, 11, 45, tzinfo=UTC)
    assert row.outcome_age_seconds == d("3600.000000")
    assert row.source_age_seconds == d("1800.000000")
    assert row.acknowledgement_lag_seconds == d("2700.000000")

    payload = api().market_outcome_source_recheck_queue_report_payload(queue)

    assert payload["rows"][0]["final_outcome_at"] == "2026-07-02T11:00:00+00:00"
    assert payload["rows"][0]["outcome_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["acknowledgement_lag_seconds"] == "2700.000000"
    assert payload["max_source_age_seconds"] == "1800.000000"
    assert_no_numeric_payload(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_validates_decimal_inputs_datetimes_duplicates_flags_digest_and_frozen_instances() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_stale_after_seconds must be a Decimal"):
        config(source_stale_after_seconds=3600)

    with pytest.raises(ValueError, match="priority_outcome_age_seconds must be a Decimal"):
        config(priority_outcome_age_seconds=_DecimalSubclass("7200.000000"))

    with pytest.raises(ValueError, match="final_outcome_at must be timezone-aware"):
        record("market-naive", final_outcome_at=datetime(2026, 7, 2, 12, 0))

    with pytest.raises(ValueError, match="final_outcome_at must be timezone-aware"):
        record(
            "market-none-offset",
            final_outcome_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTz()),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_outcome_source_recheck_queue_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="final_outcome_at must not be after generated_at"):
        report(
            record(
                "market-future",
                final_outcome_at=GENERATED_AT + timedelta(seconds=1),
                source_checked_at=None,
                source_acknowledged_at=None,
            ),
        )

    with pytest.raises(ValueError, match="source_checked_at must not be before final_outcome_at"):
        record(
            "market-source-before-outcome",
            final_outcome_at=GENERATED_AT - timedelta(hours=1),
            source_checked_at=GENERATED_AT - timedelta(hours=2),
        )

    with pytest.raises(ValueError, match="duplicate market outcome/source recheck"):
        report(record("market-dup"), record("market-dup"))

    input_record = record("market-frozen")
    with pytest.raises(FrozenInstanceError):
        input_record.market_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_record, paper_only=False)

    good_report = report(input_record)
    with pytest.raises(FrozenInstanceError):
        good_report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        module.market_outcome_source_recheck_queue_report_payload(
            replace(good_report, readonly=False),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good_report, derived_validation_digest="0" * 64)

    tampered = replace(good_report)
    object.__setattr__(tampered, "queued_count", d("99"))
    with pytest.raises(ValueError, match="queued_count|derived_validation_digest"):
        module.market_outcome_source_recheck_queue_report_payload(tampered)


def test_public_payload_rejects_numeric_values_missing_digest_and_unsafe_surfaces() -> None:
    module = api()
    payload = module.market_outcome_source_recheck_queue_report_payload(
        report(
            record(
                "market-json",
                final_outcome_at=GENERATED_AT - timedelta(hours=4),
                source_checked_at=None,
                source_acknowledged_at=None,
                expected_outcome="yes",
                source_outcome="no",
            ),
        ),
    )

    assert module.validate_market_outcome_source_recheck_queue_public_payload(payload)

    numeric_payload = {**payload, "record_count": 1}
    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_market_outcome_source_recheck_queue_public_payload(numeric_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_queue_public_payload(missing_digest)

    tampered = {**payload, "queued_count": "0.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_queue_public_payload(tampered)

    for forbidden_key in (
        "auth_token",
        "wallet_address",
        "order_id",
        "network_url",
        "database_dsn",
        "persist_path",
        "live_trading_enabled",
    ):
        unsafe_payload = {**payload, forbidden_key: "not allowed"}
        with pytest.raises(ValueError, match="unsafe"):
            module.validate_market_outcome_source_recheck_queue_public_payload(
                unsafe_payload,
            )


def assert_no_numeric_payload(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | float | Decimal):
        raise AssertionError(f"numeric payload value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_numeric_payload(item)


def assert_no_unsafe_public_surface(payload: dict[str, Any]) -> None:
    payload_text = repr(payload).lower()
    for forbidden in (
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "live trading",
    ):
        assert forbidden not in payload_text
