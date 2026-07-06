from __future__ import annotations

import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.market_outcome_source_recheck_backlog_report"


class DerivedDatetime(datetime):
    pass


class DerivedDecimal(Decimal):
    pass


class NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "market-outcome-source-recheck-backlog-test-v0",
        "stale_backlog_after_seconds": d("3600.000000"),
        "critical_backlog_after_seconds": d("7200.000000"),
        "high_open_recheck_count_threshold": d("2"),
    }
    values.update(overrides)
    return module.MarketOutcomeSourceRecheckBacklogConfig(**values)


def item(
    market_id: str,
    *,
    market_slug: str | None = None,
    outcome_id: str | None = None,
    source_id: str = "official-resolution-source",
    recheck_requested_at: datetime = GENERATED_AT - timedelta(minutes=30),
    last_rechecked_at: datetime | None = GENERATED_AT - timedelta(minutes=10),
    source_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    expected_outcome: str | None = "yes",
    source_outcome: str | None = "yes",
    open_recheck_count: Decimal = d("1"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketOutcomeSourceRecheckBacklogItem(
        market_id=market_id,
        market_slug=market_slug or f"{market_id}-slug",
        outcome_id=outcome_id or f"{market_id}-outcome",
        source_id=source_id,
        recheck_requested_at=recheck_requested_at,
        last_rechecked_at=last_rechecked_at,
        source_acknowledged_at=source_acknowledged_at,
        expected_outcome=expected_outcome,
        source_outcome=source_outcome,
        open_recheck_count=open_recheck_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, config: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_outcome_source_recheck_backlog_report(
        items,
        config=config or cfg(),
        generated_at=generated_at,
    )


def test_module_contract_names_are_available() -> None:
    module = api()

    assert importlib.util.find_spec(MODULE_NAME) is not None
    assert module.__all__ == (
        "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_BACKLOG_REPORT_CONFIG_VERSION",
        "MarketOutcomeSourceRecheckBacklogConfig",
        "MarketOutcomeSourceRecheckBacklogItem",
        "MarketOutcomeSourceRecheckBacklogReasonCodeCount",
        "MarketOutcomeSourceRecheckBacklogRow",
        "MarketOutcomeSourceRecheckBacklogReport",
        "build_market_outcome_source_recheck_backlog_report",
        "market_outcome_source_recheck_backlog_report_payload",
        "validate_market_outcome_source_recheck_backlog_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)


def test_empty_backlog_is_readonly_decimal_digest_report_and_payload() -> None:
    backlog = report()
    module = api()

    assert backlog == module.MarketOutcomeSourceRecheckBacklogReport(
        generated_at=GENERATED_AT,
        config_version="market-outcome-source-recheck-backlog-test-v0",
        status="clear",
        item_count=d("0"),
        backlog_count=d("0"),
        clear_count=d("0"),
        watch_count=d("0"),
        blocked_count=d("0"),
        missing_recheck_count=d("0"),
        stale_recheck_count=d("0"),
        missing_acknowledgement_count=d("0"),
        source_outcome_conflict_count=d("0"),
        critical_age_count=d("0"),
        high_open_recheck_count=d("0"),
        blocked_ratio=d("0.000000"),
        watch_ratio=d("0.000000"),
        backlog_ratio=d("0.000000"),
        max_backlog_age_seconds=d("0.000000"),
        max_last_recheck_age_seconds=d("0.000000"),
        max_acknowledgement_lag_seconds=d("0.000000"),
        reason_codes=("market_outcome_source_recheck_backlog_empty",),
        reason_code_counts=(),
        rows=(),
    )
    assert backlog.paper_only is True
    assert backlog.report_only is True
    assert backlog.readonly is True
    assert len(backlog.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in backlog.derived_validation_digest)

    payload = module.market_outcome_source_recheck_backlog_report_payload(backlog)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["item_count"] == "0"
    assert payload["blocked_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == backlog.derived_validation_digest
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_values(payload)
    assert_no_unsafe_public_surface(payload)
    assert module.validate_market_outcome_source_recheck_backlog_public_payload(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_backlog_report_prioritizes_blocked_watch_and_clear_rechecks() -> None:
    backlog = report(
        item(
            "market-clear",
            market_slug="gamma-clear",
            recheck_requested_at=GENERATED_AT - timedelta(minutes=20),
            last_rechecked_at=GENERATED_AT - timedelta(minutes=5),
            source_acknowledged_at=GENERATED_AT - timedelta(minutes=2),
            open_recheck_count=d("0"),
        ),
        item(
            "market-blocked",
            market_slug="alpha-blocked",
            recheck_requested_at=GENERATED_AT - timedelta(hours=4),
            last_rechecked_at=None,
            source_acknowledged_at=None,
            expected_outcome="yes",
            source_outcome="no",
            open_recheck_count=d("3"),
        ),
        item(
            "market-watch",
            market_slug="beta-watch",
            recheck_requested_at=GENERATED_AT - timedelta(hours=2),
            last_rechecked_at=GENERATED_AT - timedelta(hours=1),
            source_acknowledged_at=GENERATED_AT - timedelta(minutes=30),
            open_recheck_count=d("1"),
        ),
    )

    assert backlog.status == "blocked"
    assert backlog.item_count == d("3")
    assert backlog.backlog_count == d("2")
    assert backlog.clear_count == d("1")
    assert backlog.watch_count == d("1")
    assert backlog.blocked_count == d("1")
    assert backlog.missing_recheck_count == d("1")
    assert backlog.stale_recheck_count == d("1")
    assert backlog.missing_acknowledgement_count == d("1")
    assert backlog.source_outcome_conflict_count == d("1")
    assert backlog.critical_age_count == d("2")
    assert backlog.high_open_recheck_count == d("1")
    assert backlog.blocked_ratio == d("0.333333")
    assert backlog.watch_ratio == d("0.333333")
    assert backlog.backlog_ratio == d("0.666667")
    assert backlog.max_backlog_age_seconds == d("14400.000000")
    assert backlog.max_last_recheck_age_seconds == d("3600.000000")
    assert backlog.max_acknowledgement_lag_seconds == d("14400.000000")
    assert backlog.reason_codes == (
        "market_outcome_source_recheck_backlog_missing_recheck",
        "market_outcome_source_recheck_backlog_stale_recheck",
        "market_outcome_source_recheck_backlog_missing_acknowledgement",
        "market_outcome_source_recheck_backlog_source_outcome_conflict",
        "market_outcome_source_recheck_backlog_critical_age",
        "market_outcome_source_recheck_backlog_high_open_count",
    )
    assert tuple(row.reason_code for row in backlog.reason_code_counts) == backlog.reason_codes

    assert tuple(row.market_id for row in backlog.rows) == (
        "market-blocked",
        "market-watch",
        "market-clear",
    )
    blocked = backlog.rows[0]
    assert blocked.backlog_status == "blocked"
    assert blocked.backlog_age_seconds == d("14400.000000")
    assert blocked.last_recheck_age_seconds is None
    assert blocked.acknowledgement_lag_seconds == d("14400.000000")
    assert blocked.reason_codes == (
        "market_outcome_source_recheck_backlog_missing_recheck",
        "market_outcome_source_recheck_backlog_missing_acknowledgement",
        "market_outcome_source_recheck_backlog_source_outcome_conflict",
        "market_outcome_source_recheck_backlog_critical_age",
        "market_outcome_source_recheck_backlog_high_open_count",
    )
    watch = backlog.rows[1]
    assert watch.backlog_status == "watch"
    assert watch.last_recheck_age_seconds == d("3600.000000")
    assert watch.reason_codes == (
        "market_outcome_source_recheck_backlog_stale_recheck",
        "market_outcome_source_recheck_backlog_critical_age",
    )
    assert backlog.rows[2].backlog_status == "clear"
    assert backlog.rows[2].reason_codes == ()


def test_timezone_normalization_and_decimal_string_payload() -> None:
    eastern = timezone(timedelta(hours=-4))
    backlog = report(
        item(
            "market-tz",
            recheck_requested_at=datetime(2026, 7, 6, 7, 0, tzinfo=eastern),
            last_rechecked_at=datetime(2026, 7, 6, 7, 30, tzinfo=eastern),
            source_acknowledged_at=datetime(2026, 7, 6, 7, 45, tzinfo=eastern),
            open_recheck_count=d("1"),
        ),
    )

    row = backlog.rows[0]
    assert row.recheck_requested_at == datetime(2026, 7, 6, 11, 0, tzinfo=UTC)
    assert row.last_rechecked_at == datetime(2026, 7, 6, 11, 30, tzinfo=UTC)
    assert row.source_acknowledged_at == datetime(2026, 7, 6, 11, 45, tzinfo=UTC)
    assert row.backlog_age_seconds == d("3600.000000")
    assert row.last_recheck_age_seconds == d("1800.000000")
    assert row.acknowledgement_lag_seconds == d("2700.000000")

    payload = api().market_outcome_source_recheck_backlog_report_payload(backlog)
    assert payload["rows"][0]["recheck_requested_at"] == "2026-07-06T11:00:00+00:00"
    assert payload["rows"][0]["backlog_age_seconds"] == "3600.000000"
    assert payload["rows"][0]["acknowledgement_lag_seconds"] == "2700.000000"
    assert payload["max_last_recheck_age_seconds"] == "1800.000000"
    assert_no_public_numeric_values(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_validates_decimal_inputs_datetimes_duplicates_flags_digest_and_frozen_instances() -> None:
    module = api()

    with pytest.raises(ValueError, match="stale_backlog_after_seconds must be a Decimal"):
        cfg(stale_backlog_after_seconds=3600)
    with pytest.raises(ValueError, match="critical_backlog_after_seconds must be a Decimal"):
        cfg(critical_backlog_after_seconds=DerivedDecimal("7200.000000"))
    with pytest.raises(ValueError, match="high_open_recheck_count_threshold must be an integer Decimal"):
        cfg(high_open_recheck_count_threshold=d("1.500000"))
    with pytest.raises(ValueError, match="open_recheck_count must be a Decimal"):
        item("bad-count", open_recheck_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        item("bad-flag", readonly=False)
    with pytest.raises(ValueError, match="recheck_requested_at must be timezone-aware"):
        item("naive", recheck_requested_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="recheck_requested_at must be timezone-aware"):
        item(
            "none-offset",
            recheck_requested_at=datetime(2026, 7, 6, 12, 0, tzinfo=NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(generated_at=DerivedDatetime(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="recheck_requested_at must not be after generated_at"):
        report(
            item(
                "future",
                recheck_requested_at=GENERATED_AT + timedelta(seconds=1),
                last_rechecked_at=GENERATED_AT + timedelta(seconds=2),
                source_acknowledged_at=GENERATED_AT + timedelta(seconds=3),
            ),
        )
    with pytest.raises(ValueError, match="last_rechecked_at must not be before recheck_requested_at"):
        item(
            "recheck-before-request",
            recheck_requested_at=GENERATED_AT - timedelta(hours=1),
            last_rechecked_at=GENERATED_AT - timedelta(hours=2),
        )
    with pytest.raises(ValueError, match="duplicate market outcome/source recheck backlog item"):
        report(item("dup"), item("dup"))

    input_item = item("frozen")
    with pytest.raises(FrozenInstanceError):
        input_item.market_id = "changed"  # type: ignore[misc]
    good_report = report(input_item)
    with pytest.raises(FrozenInstanceError):
        good_report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        module.market_outcome_source_recheck_backlog_report_payload(
            replace(good_report, report_only=False),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good_report, derived_validation_digest="0" * 64)

    tampered = replace(good_report)
    object.__setattr__(tampered, "backlog_count", d("99"))
    with pytest.raises(ValueError, match="backlog_count|derived_validation_digest"):
        module.market_outcome_source_recheck_backlog_report_payload(tampered)

    for klass in (
        module.MarketOutcomeSourceRecheckBacklogConfig,
        module.MarketOutcomeSourceRecheckBacklogItem,
        module.MarketOutcomeSourceRecheckBacklogReasonCodeCount,
        module.MarketOutcomeSourceRecheckBacklogRow,
        module.MarketOutcomeSourceRecheckBacklogReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Unsafe{klass.__name__}", (klass,), {})


def test_public_payload_rejects_numeric_values_missing_digest_and_unsafe_surfaces() -> None:
    module = api()
    payload = module.market_outcome_source_recheck_backlog_report_payload(
        report(
            item(
                "market-json",
                recheck_requested_at=GENERATED_AT - timedelta(hours=4),
                last_rechecked_at=None,
                source_acknowledged_at=None,
                expected_outcome="yes",
                source_outcome="no",
                open_recheck_count=d("2"),
            ),
        ),
    )

    assert module.validate_market_outcome_source_recheck_backlog_public_payload(payload)

    numeric_payload = {**payload, "item_count": 1}
    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_market_outcome_source_recheck_backlog_public_payload(numeric_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_backlog_public_payload(missing_digest)

    tampered = {**payload, "blocked_count": "0"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_backlog_public_payload(tampered)

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
        with pytest.raises(ValueError, match="unsafe live surface field"):
            module.validate_market_outcome_source_recheck_backlog_public_payload(
                unsafe_payload,
            )

    for forbidden_value in ("wallet", "auth", "order", "network", "database", "persist"):
        with pytest.raises(ValueError, match="unsafe public value"):
            module.validate_market_outcome_source_recheck_backlog_public_payload(
                {**payload, "market_id": forbidden_value},
            )


def test_module_surface_is_readonly_report_only_and_external_io_free() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/market_outcome_source_recheck_backlog_report.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlalchemy",
        "socket",
        "subprocess",
        "open(",
        "write(",
        "live_trading",
        "authentication",
        "private_key",
        "wallet_address",
        "place_order",
        "submit_order",
        "database_dsn",
        "persist_path",
    ):
        assert forbidden not in lowered

    public_names = tuple(name for name in dir(api()) if not name.startswith("_"))
    public_surface = " ".join(public_names).lower()
    for forbidden in ("live", "auth", "wallet", "order", "network", "database", "persist"):
        assert forbidden not in public_surface


def assert_no_public_numeric_values(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | float | Decimal):
        raise AssertionError(f"numeric payload value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_public_numeric_values(item)


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
