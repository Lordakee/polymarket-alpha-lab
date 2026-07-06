from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.market_outcome_source_recheck_health_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_outcome_source_recheck_health_report.py"
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "market-outcome-source-recheck-health-test-v0",
        "stale_source_seconds": d("3600.000000"),
        "stale_acknowledgement_seconds": d("1800.000000"),
        "min_source_coverage_ratio": d("0.750000"),
        "max_conflict_ratio": d("0.250000"),
    }
    values.update(overrides)
    return module.MarketOutcomeSourceRecheckHealthConfig(**values)


def observation(
    market_slug: str,
    *,
    condition_id: str | None = None,
    source_id: str | None = None,
    source_family: str = "official",
    final_outcome_at: datetime = GENERATED_AT - timedelta(hours=2),
    source_checked_at: datetime | None = GENERATED_AT - timedelta(minutes=30),
    source_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
    expected_outcome: str | None = "yes",
    source_outcome: str | None = "yes",
    expected_source_count: Decimal = d("4.000000"),
    verified_source_count: Decimal = d("4.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    suffix = market_slug.removeprefix("market-")
    return module.MarketOutcomeSourceRecheckObservation(
        market_slug=market_slug,
        condition_id=condition_id or f"condition-{suffix}",
        source_id=source_id or f"source-{suffix}",
        source_family=source_family,
        final_outcome_at=final_outcome_at,
        source_checked_at=source_checked_at,
        source_acknowledged_at=source_acknowledged_at,
        expected_outcome=expected_outcome,
        source_outcome=source_outcome,
        expected_source_count=expected_source_count,
        verified_source_count=verified_source_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*values: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_outcome_source_recheck_health_report(
        values,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_public_numeric(value: object) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | float | Decimal):
        raise AssertionError(f"unexpected numeric public value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)


def test_empty_health_report_is_readonly_decimal_digest_bound_and_json_safe() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.MarketOutcomeSourceRecheckHealthReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.health_status == "clear"
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.clear_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.stale_source_count == d("0.000000")
    assert report.stale_acknowledgement_count == d("0.000000")
    assert report.missing_source_count == d("0.000000")
    assert report.missing_acknowledgement_count == d("0.000000")
    assert report.source_outcome_conflict_count == d("0.000000")
    assert report.low_source_coverage_count == d("0.000000")
    assert report.attention_count == d("0.000000")
    assert report.attention_ratio == d("0.000000")
    assert report.source_coverage_ratio == d("0.000000")
    assert report.conflict_ratio == d("0.000000")
    assert report.max_source_age_seconds == d("0.000000")
    assert report.max_acknowledgement_lag_seconds == d("0.000000")
    assert report.reason_codes == ("market_outcome_source_recheck_health_clear",)
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.market_outcome_source_recheck_health_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["input_count"] == "0.000000"
    assert payload["attention_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.validate_market_outcome_source_recheck_health_public_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_health_report_rolls_up_source_recheck_conditions_deterministically() -> None:
    report = build_report(
        observation("market-clear"),
        observation(
            "market-watch",
            final_outcome_at=GENERATED_AT - timedelta(hours=4),
            source_checked_at=GENERATED_AT - timedelta(hours=2),
            source_acknowledged_at=GENERATED_AT - timedelta(hours=1),
            expected_source_count=d("4.000000"),
            verified_source_count=d("3.000000"),
        ),
        observation(
            "market-blocked",
            final_outcome_at=GENERATED_AT - timedelta(hours=5),
            source_checked_at=None,
            source_acknowledged_at=None,
            expected_outcome="yes",
            source_outcome="no",
            expected_source_count=d("4.000000"),
            verified_source_count=d("1.000000"),
        ),
    )

    assert report.health_status == "blocked"
    assert report.input_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.clear_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.stale_source_count == d("1.000000")
    assert report.stale_acknowledgement_count == d("1.000000")
    assert report.missing_source_count == d("1.000000")
    assert report.missing_acknowledgement_count == d("1.000000")
    assert report.source_outcome_conflict_count == d("1.000000")
    assert report.low_source_coverage_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.attention_ratio == d("0.666667")
    assert report.source_coverage_ratio == d("0.666667")
    assert report.conflict_ratio == d("0.333333")
    assert report.max_source_age_seconds == d("7200.000000")
    assert report.max_acknowledgement_lag_seconds == d("18000.000000")
    assert report.reason_codes == (
        "market_outcome_source_recheck_missing_source",
        "market_outcome_source_recheck_stale_source",
        "market_outcome_source_recheck_missing_acknowledgement",
        "market_outcome_source_recheck_stale_acknowledgement",
        "market_outcome_source_recheck_source_outcome_conflict",
        "market_outcome_source_recheck_low_source_coverage",
    )

    assert tuple(row.market_slug for row in report.rows) == (
        "market-blocked",
        "market-watch",
        "market-clear",
    )

    blocked, watch, clear = report.rows
    assert blocked.health_status == "blocked"
    assert blocked.source_age_seconds is None
    assert blocked.acknowledgement_lag_seconds == d("18000.000000")
    assert blocked.source_coverage_ratio == d("0.250000")
    assert blocked.reason_codes == (
        "market_outcome_source_recheck_missing_source",
        "market_outcome_source_recheck_missing_acknowledgement",
        "market_outcome_source_recheck_source_outcome_conflict",
        "market_outcome_source_recheck_low_source_coverage",
    )

    assert watch.health_status == "watch"
    assert watch.source_age_seconds == d("7200.000000")
    assert watch.acknowledgement_lag_seconds == d("10800.000000")
    assert watch.reason_codes == (
        "market_outcome_source_recheck_stale_source",
        "market_outcome_source_recheck_stale_acknowledgement",
    )

    assert clear.health_status == "clear"
    assert clear.reason_codes == ("market_outcome_source_recheck_health_clear",)
    assert len({row.derived_validation_digest for row in report.rows}) == 3


def test_public_dataclasses_are_frozen_exact_decimal_only_and_reject_subclassing() -> None:
    module = api()
    report = build_report(observation("market-decimal"))

    public_classes = (
        module.MarketOutcomeSourceRecheckHealthConfig,
        module.MarketOutcomeSourceRecheckObservation,
        module.MarketOutcomeSourceRecheckHealthReasonCodeCount,
        module.MarketOutcomeSourceRecheckHealthRow,
        module.MarketOutcomeSourceRecheckHealthReport,
    )
    for klass in public_classes:
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    for instance in (config(), observation("market-fields"), *report.reason_code_counts, *report.rows, report):
        for field in fields(instance):
            value = getattr(instance, field.name)
            assert type(value) is not float
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
            ):
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.health_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        observation("market-flag", paper_only=False)
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedConfig", (module.MarketOutcomeSourceRecheckHealthConfig,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedRow", (module.MarketOutcomeSourceRecheckHealthRow,), {})
    with pytest.raises(ValueError, match="stale_source_seconds"):
        config(stale_source_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="expected_source_count"):
        observation("market-int", expected_source_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="verified_source_count"):
        observation("market-fractional", verified_source_count=d("1.500000"))


def test_timezone_duplicate_digest_and_consistency_validation() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        observation(
            "market-tz",
            final_outcome_at=datetime(2026, 7, 2, 6, 0, tzinfo=eastern),
            source_checked_at=datetime(2026, 7, 2, 7, 0, tzinfo=eastern),
            source_acknowledged_at=datetime(2026, 7, 2, 7, 30, tzinfo=eastern),
        ),
    )
    row = report.rows[0]
    assert row.final_outcome_at == datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
    assert row.source_checked_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert row.source_acknowledged_at == datetime(2026, 7, 2, 11, 30, tzinfo=UTC)
    assert row.source_age_seconds == d("3600.000000")

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_outcome_source_recheck_health_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="final_outcome_at must be timezone-aware"):
        observation("market-naive", final_outcome_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="source_checked_at must be timezone-aware"):
        observation(
            "market-none-offset",
            source_checked_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        build_report(
            observation(
                "market-future",
                final_outcome_at=GENERATED_AT + timedelta(seconds=1),
                source_checked_at=None,
                source_acknowledged_at=None,
            ),
        )
    with pytest.raises(ValueError, match="duplicate market outcome source recheck"):
        build_report(observation("market-dup"), observation("market-dup"))
    with pytest.raises(ValueError, match="source_checked_at must not be before final_outcome_at"):
        observation(
            "market-before",
            final_outcome_at=GENERATED_AT - timedelta(hours=1),
            source_checked_at=GENERATED_AT - timedelta(hours=2),
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    tampered = replace(report)
    object.__setattr__(tampered, "attention_count", d("99.000000"))
    with pytest.raises(ValueError, match="attention_count|derived_validation_digest"):
        module.market_outcome_source_recheck_health_report_payload(tampered)


def test_public_payload_rejects_numeric_values_missing_digest_and_unsafe_surfaces() -> None:
    module = api()
    payload = module.market_outcome_source_recheck_health_report_payload(
        build_report(
            observation(
                "market-json",
                source_checked_at=None,
                source_acknowledged_at=None,
                expected_outcome="yes",
                source_outcome="no",
                expected_source_count=d("4.000000"),
                verified_source_count=d("1.000000"),
            ),
        ),
    )

    assert module.validate_market_outcome_source_recheck_health_public_payload(payload)

    numeric_payload = {**payload, "row_count": 1}
    with pytest.raises(ValueError, match="Decimal strings|numeric"):
        module.validate_market_outcome_source_recheck_health_public_payload(numeric_payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_health_public_payload(missing_digest)

    tampered = {**payload, "blocked_count": "0.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_health_public_payload(tampered)

    for forbidden_key in (
        "live_trading_enabled",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_url",
        "database_dsn",
        "persist_path",
    ):
        unsafe_payload = {**payload, forbidden_key: "not allowed"}
        with pytest.raises(ValueError, match="unsafe"):
            module.validate_market_outcome_source_recheck_health_public_payload(
                unsafe_payload,
            )

    for forbidden_value in (
        "live trading configured",
        "auth configured",
        "wallet configured",
        "order configured",
        "network configured",
        "database configured",
        "persist configured",
    ):
        unsafe_payload = {**payload, "operator_note": forbidden_value}
        with pytest.raises(ValueError, match="unsafe"):
            module.validate_market_outcome_source_recheck_health_public_payload(
                unsafe_payload,
            )


def test_module_scope_rejects_live_auth_wallet_order_network_database_and_persistence_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    forbidden_import_modules = {
        "asyncio",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
        "py_clob_client",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_modules
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_modules

    lowered = source.lower()
    forbidden_fragments = (
        "live_trading",
        "place_order",
        "create_order",
        "cancel_order",
        "wallet",
        "private_key",
        "auth_token",
        "network_client",
        "database_url",
        "persist_path",
        "open(",
        "socket.",
        "requests.",
        "httpx.",
    )
    for fragment in forbidden_fragments:
        assert fragment not in lowered


def test_export_contract_names_are_complete() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_HEALTH_CONFIG_VERSION",
        "MarketOutcomeSourceRecheckHealthConfig",
        "MarketOutcomeSourceRecheckObservation",
        "MarketOutcomeSourceRecheckHealthReasonCodeCount",
        "MarketOutcomeSourceRecheckHealthRow",
        "MarketOutcomeSourceRecheckHealthReport",
        "build_market_outcome_source_recheck_health_report",
        "market_outcome_source_recheck_health_report_payload",
        "validate_market_outcome_source_recheck_health_public_payload",
    )
