from __future__ import annotations

import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.market_outcome_source_recheck_replay_report"


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
        "max_replay_lag_seconds": d("3600.000000"),
        "priority_outcome_age_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.MarketOutcomeSourceRecheckReplayConfig(**values)


def record(
    market_id: str,
    *,
    market_slug: str | None = None,
    outcome_id: str | None = None,
    source_id: str = "official-resolution-source",
    final_outcome_at: datetime = GENERATED_AT - timedelta(hours=1),
    replayed_at: datetime | None = GENERATED_AT - timedelta(minutes=30),
    expected_outcome: str | None = "yes",
    replayed_outcome: str | None = "yes",
):
    module = api()
    return module.MarketOutcomeSourceRecheckReplayRecord(
        market_id=market_id,
        market_slug=market_slug or f"{market_id}-slug",
        outcome_id=outcome_id or f"{market_id}-outcome",
        source_id=source_id,
        final_outcome_at=final_outcome_at,
        replayed_at=replayed_at,
        expected_outcome=expected_outcome,
        replayed_outcome=replayed_outcome,
    )


def report(*records: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_outcome_source_recheck_replay_report(
        records,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_module_contract_names_are_available() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_empty_replay_is_readonly_decimal_digest_report_and_payload() -> None:
    module = api()

    replay = report()

    assert is_dataclass(replay)
    assert replay == module.MarketOutcomeSourceRecheckReplayReport(
        generated_at=GENERATED_AT,
        config_version=(
            module.DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_REPLAY_CONFIG_VERSION
        ),
        status="clear",
        record_count=d("0"),
        replayed_count=d("0"),
        missing_replay_count=d("0"),
        replay_lag_breach_count=d("0"),
        outcome_mismatch_count=d("0"),
        outcome_age_priority_count=d("0"),
        pass_count=d("0"),
        watch_count=d("0"),
        blocked_count=d("0"),
        replayed_ratio=d("0.000000"),
        missing_replay_ratio=d("0.000000"),
        outcome_mismatch_ratio=d("0.000000"),
        max_outcome_age_seconds=d("0.000000"),
        max_replay_lag_seconds=d("0.000000"),
        reason_codes=("market_outcome_source_recheck_replay_empty",),
        reason_code_counts=(),
        rows=(),
    )
    assert replay.paper_only is True
    assert replay.report_only is True
    assert replay.readonly is True
    assert len(replay.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in replay.derived_validation_digest
    )

    payload = module.market_outcome_source_recheck_replay_report_payload(replay)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["record_count"] == "0"
    assert payload["replayed_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == replay.derived_validation_digest
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_payload(payload)
    assert_no_unsafe_public_surface(payload)
    assert module.validate_market_outcome_source_recheck_replay_public_payload(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_replay_report_summarizes_rechecks_with_counts_and_sorting() -> None:
    replay = report(
        record(
            "market-pass",
            market_slug="alpha-clear",
            final_outcome_at=GENERATED_AT - timedelta(hours=1),
            replayed_at=GENERATED_AT - timedelta(minutes=30),
            expected_outcome="yes",
            replayed_outcome="yes",
        ),
        record(
            "market-blocked",
            market_slug="beta-blocked",
            final_outcome_at=GENERATED_AT - timedelta(hours=6),
            replayed_at=GENERATED_AT - timedelta(hours=4),
            expected_outcome="yes",
            replayed_outcome="no",
        ),
        record(
            "market-watch",
            market_slug="gamma-watch",
            final_outcome_at=GENERATED_AT - timedelta(hours=5),
            replayed_at=GENERATED_AT - timedelta(hours=3),
            expected_outcome="yes",
            replayed_outcome="yes",
        ),
    )

    assert replay.status == "blocked"
    assert replay.record_count == d("3")
    assert replay.replayed_count == d("3")
    assert replay.missing_replay_count == d("0")
    assert replay.replay_lag_breach_count == d("2")
    assert replay.outcome_mismatch_count == d("1")
    assert replay.outcome_age_priority_count == d("2")
    assert replay.pass_count == d("1")
    assert replay.watch_count == d("1")
    assert replay.blocked_count == d("1")
    assert replay.replayed_ratio == d("1.000000")
    assert replay.missing_replay_ratio == d("0.000000")
    assert replay.outcome_mismatch_ratio == d("0.333333")
    assert replay.max_outcome_age_seconds == d("21600.000000")
    assert replay.max_replay_lag_seconds == d("7200.000000")
    assert replay.reason_codes == (
        "market_outcome_source_recheck_replay_lag_breach",
        "market_outcome_source_recheck_replay_outcome_mismatch",
        "market_outcome_source_recheck_replay_outcome_age_priority",
    )
    assert tuple(item.reason_code for item in replay.reason_code_counts) == (
        "market_outcome_source_recheck_replay_lag_breach",
        "market_outcome_source_recheck_replay_outcome_mismatch",
        "market_outcome_source_recheck_replay_outcome_age_priority",
    )

    assert tuple(row.market_id for row in replay.rows) == (
        "market-blocked",
        "market-watch",
        "market-pass",
    )

    blocked = replay.rows[0]
    assert blocked.replay_status == "blocked"
    assert blocked.outcome_age_seconds == d("21600.000000")
    assert blocked.replay_lag_seconds == d("7200.000000")
    assert blocked.replayed_after_outcome is True
    assert blocked.outcome_match is False
    assert blocked.reason_codes == (
        "market_outcome_source_recheck_replay_lag_breach",
        "market_outcome_source_recheck_replay_outcome_mismatch",
        "market_outcome_source_recheck_replay_outcome_age_priority",
    )

    watch = replay.rows[1]
    assert watch.replay_status == "watch"
    assert watch.outcome_match is True
    assert watch.reason_codes == (
        "market_outcome_source_recheck_replay_lag_breach",
        "market_outcome_source_recheck_replay_outcome_age_priority",
    )

    clear = replay.rows[2]
    assert clear.replay_status == "pass"
    assert clear.reason_codes == ()


def test_missing_replay_timezone_normalization_and_decimal_string_payload() -> None:
    eastern = timezone(timedelta(hours=-4))
    replay = report(
        record(
            "market-tz",
            final_outcome_at=datetime(2026, 7, 6, 7, 0, tzinfo=eastern),
            replayed_at=None,
            expected_outcome="yes",
            replayed_outcome=None,
        ),
    )

    row = replay.rows[0]
    assert row.final_outcome_at == datetime(2026, 7, 6, 11, 0, tzinfo=UTC)
    assert row.replayed_at is None
    assert row.outcome_age_seconds == d("3600.000000")
    assert row.replay_lag_seconds == d("3600.000000")
    assert row.replayed_after_outcome is False
    assert row.outcome_match is False

    payload = api().market_outcome_source_recheck_replay_report_payload(replay)

    assert payload["rows"][0]["final_outcome_at"] == "2026-07-06T11:00:00+00:00"
    assert payload["rows"][0]["replayed_at"] is None
    assert payload["rows"][0]["outcome_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["replay_lag_seconds"] == "3600.000000"
    assert payload["missing_replay_count"] == "1"
    assert_no_numeric_payload(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_validates_decimal_inputs_datetimes_duplicates_flags_digest_and_frozen_instances() -> None:
    module = api()

    with pytest.raises(ValueError, match="max_replay_lag_seconds must be a Decimal"):
        config(max_replay_lag_seconds=3600)

    with pytest.raises(ValueError, match="priority_outcome_age_seconds must be a Decimal"):
        config(priority_outcome_age_seconds=_DecimalSubclass("7200.000000"))

    with pytest.raises(ValueError, match="final_outcome_at must be timezone-aware"):
        record("market-naive", final_outcome_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="final_outcome_at must be timezone-aware"):
        record(
            "market-none-offset",
            final_outcome_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTz()),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_outcome_source_recheck_replay_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="final_outcome_at must not be after generated_at"):
        report(
            record(
                "market-future",
                final_outcome_at=GENERATED_AT + timedelta(seconds=1),
                replayed_at=None,
                replayed_outcome=None,
            ),
        )

    with pytest.raises(ValueError, match="replayed_at must not be before final_outcome_at"):
        record(
            "market-replay-before-outcome",
            final_outcome_at=GENERATED_AT - timedelta(hours=1),
            replayed_at=GENERATED_AT - timedelta(hours=2),
        )

    with pytest.raises(ValueError, match="duplicate market outcome/source recheck replay"):
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
        replace(good_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good_report, derived_validation_digest="0" * 64)

    tampered = replace(good_report)
    object.__setattr__(tampered, "record_count", d("99"))
    with pytest.raises(ValueError, match="record_count|derived_validation_digest"):
        module.market_outcome_source_recheck_replay_report_payload(tampered)


def test_public_payload_rejects_numeric_values_missing_digest_and_unsafe_surfaces() -> None:
    module = api()
    payload = module.market_outcome_source_recheck_replay_report_payload(
        report(
            record(
                "market-json",
                final_outcome_at=GENERATED_AT - timedelta(hours=4),
                replayed_at=GENERATED_AT - timedelta(hours=2),
                expected_outcome="yes",
                replayed_outcome="no",
            ),
        ),
    )

    assert module.validate_market_outcome_source_recheck_replay_public_payload(payload)

    numeric_payload = {**payload, "record_count": 1}
    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_market_outcome_source_recheck_replay_public_payload(numeric_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_replay_public_payload(missing_digest)

    tampered = {**payload, "replayed_count": "0"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_replay_public_payload(tampered)

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
            module.validate_market_outcome_source_recheck_replay_public_payload(
                unsafe_payload,
            )

    unsafe_value_payload = {**payload, "review_note": "wallet reference"}
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_market_outcome_source_recheck_replay_public_payload(
            unsafe_value_payload,
        )


def test_public_api_surface_excludes_unsafe_live_capabilities() -> None:
    module = api()

    for name in module.__all__:
        lowered = name.lower()
        for forbidden in (
            "auth",
            "wallet",
            "order",
            "network",
            "database",
            "persist",
            "live",
        ):
            assert forbidden not in lowered


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
