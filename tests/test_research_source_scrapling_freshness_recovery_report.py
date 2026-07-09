from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_scrapling_freshness_recovery_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scrapling_freshness_recovery_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
PUBLIC_STATUSES = ("pass", "watch", "block")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def ago(seconds: int) -> datetime:
    return GENERATED_AT - timedelta(seconds=seconds)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "research-source-scrapling-freshness-recovery-report-v0",
        "watch_recovered_ratio": d("0.800000"),
        "block_recovered_ratio": d("0.500000"),
        "watch_recovery_latency_seconds": d("1800.000000"),
        "block_recovery_latency_seconds": d("7200.000000"),
        "min_recovery_success_pass_ratio": d("0.800000"),
        "min_recovery_success_block_ratio": d("0.400000"),
        "max_fallback_retry_pass_ratio": d("0.250000"),
        "max_fallback_retry_block_ratio": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchSourceScraplingFreshnessRecoveryConfig(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "recovery_bucket": "alpha-feed",
        "first_stale_at": ago(1200),
        "recovered_at": ago(300),
        "attempted_refresh_count": d("4.000000"),
        "successful_refresh_count": d("4.000000"),
        "fallback_retry_count": d("0.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceScraplingFreshnessRecoveryObservation(**values)


def build_report(
    *rows: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_source_scrapling_freshness_recovery_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_builds_recovery_report_from_public_bucket_inputs() -> None:
    module = api()
    report = build_report(
        observation(
            recovery_bucket="alpha-feed",
            first_stale_at=ago(1200),
            recovered_at=ago(300),
            attempted_refresh_count=d("4.000000"),
            successful_refresh_count=d("4.000000"),
            fallback_retry_count=d("0.000000"),
        ),
        observation(
            recovery_bucket="beta-feed",
            first_stale_at=ago(3900),
            recovered_at=ago(1200),
            attempted_refresh_count=d("3.000000"),
            successful_refresh_count=d("2.000000"),
            fallback_retry_count=d("1.000000"),
        ),
        observation(
            recovery_bucket="gamma-feed",
            first_stale_at=ago(14400),
            recovered_at=None,
            attempted_refresh_count=d("2.000000"),
            successful_refresh_count=d("0.000000"),
            fallback_retry_count=d("2.000000"),
        ),
    )

    assert type(report) is module.ResearchSourceScraplingFreshnessRecoveryReport
    assert is_dataclass(report)
    assert report.status == "block"
    assert report.generated_at == GENERATED_AT
    assert report.recovery_bucket_count == d("3.000000")
    assert report.recovered_count == d("2.000000")
    assert report.unrecovered_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.recovered_ratio == d("0.666667")
    assert report.recovery_success_ratio == d("0.666667")
    assert report.fallback_retry_pressure_ratio == d("0.333333")
    assert report.max_stale_age_seconds == d("14400.000000")
    assert report.max_recovery_latency_seconds == d("14400.000000")
    assert report.average_recovery_latency_seconds == d("6000.000000")
    assert report.reason_codes == (
        "recovery_missing_block",
        "recovery_latency_watch",
        "recovery_success_ratio_block",
        "recovery_success_ratio_watch",
        "fallback_retry_pressure_block",
        "fallback_retry_pressure_watch",
        "recovered_ratio_watch",
        "freshness_recovery_report_block",
    )

    alpha, beta, gamma = report.rows
    assert tuple(row.recovery_bucket for row in report.rows) == (
        "alpha-feed",
        "beta-feed",
        "gamma-feed",
    )
    assert alpha.status == "pass"
    assert alpha.recovered is True
    assert alpha.recovery_latency_seconds == d("900.000000")
    assert alpha.reason_codes == ("freshness_recovery_pass",)
    assert beta.status == "watch"
    assert beta.recovery_latency_seconds == d("2700.000000")
    assert beta.recovery_success_ratio == d("0.666667")
    assert beta.fallback_retry_pressure_ratio == d("0.333333")
    assert beta.reason_codes == (
        "recovery_latency_watch",
        "recovery_success_ratio_watch",
        "fallback_retry_pressure_watch",
    )
    assert gamma.status == "block"
    assert gamma.recovered is False
    assert gamma.stale_age_seconds == d("14400.000000")
    assert gamma.reason_codes == (
        "recovery_missing_block",
        "recovery_success_ratio_block",
        "fallback_retry_pressure_block",
    )


def test_payload_is_deterministic_decimal_string_safe_and_digest_validated() -> None:
    module = api()
    rows = (
        observation(recovery_bucket="beta-feed"),
        observation(recovery_bucket="alpha-feed"),
    )

    first = build_report(
        *rows,
        generated_at=datetime(2026, 7, 9, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = build_report(*tuple(reversed(rows)))
    first_payload = (
        module.research_source_scrapling_freshness_recovery_report_payload(first)
    )
    second_payload = (
        module.research_source_scrapling_freshness_recovery_report_payload(second)
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["recovery_bucket_count"] == "2.000000"
    assert first_payload["rows"][0]["recovery_bucket"] == "alpha-feed"
    assert first_payload["rows"][0]["stale_age_seconds"] == "1200.000000"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert first.derived_validation_digest == second.derived_validation_digest
    json.dumps(first_payload, allow_nan=False, sort_keys=True)
    assert_no_public_numeric_values(first_payload)
    assert_payload_has_no_leaked_surface(first_payload)
    assert_statuses_are_public(first_payload)
    module.validate_research_source_scrapling_freshness_recovery_report_digest(first)
    module.validate_research_source_scrapling_freshness_recovery_public_payload(
        first_payload,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    tampered = dict(first_payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_scrapling_freshness_recovery_public_payload(
            tampered,
        )
    with pytest.raises(ValueError, match="unsafe"):
        observation(recovery_bucket="market-alpha")
    with pytest.raises(ValueError, match="unsafe"):
        module.validate_research_source_scrapling_freshness_recovery_public_payload(
            {**first_payload, "wallet": "paper"},
        )


def test_dataclasses_are_frozen_decimal_flags_statuses_and_surface_constraints() -> None:
    module = api()
    report = build_report(observation())

    assert module.RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_STATUSES",
        "ResearchSourceScraplingFreshnessRecoveryConfig",
        "ResearchSourceScraplingFreshnessRecoveryObservation",
        "ResearchSourceScraplingFreshnessRecoveryRow",
        "ResearchSourceScraplingFreshnessRecoveryReport",
        "build_research_source_scrapling_freshness_recovery_report",
        "research_source_scrapling_freshness_recovery_report_payload",
        "validate_research_source_scrapling_freshness_recovery_public_payload",
        "validate_research_source_scrapling_freshness_recovery_report_digest",
    }

    for public_record in (config(), observation(), report, report.rows[0]):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert public_record.paper_only is True
        assert public_record.report_only is True
        assert public_record.readonly is True
        assert_decimal_public_numbers(public_record)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadObservation(module.ResearchSourceScraplingFreshnessRecoveryObservation):
            pass

    with pytest.raises(ValueError, match="attempted_refresh_count must be a Decimal"):
        observation(attempted_refresh_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="successful_refresh_count must be a Decimal"):
        observation(successful_refresh_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="first_stale_at must be a datetime"):
        observation(first_stale_at=_DatetimeSubclass(2026, 7, 9, 11, tzinfo=UTC))
    with pytest.raises(ValueError, match="recovered_at must be timezone-aware"):
        observation(recovered_at=datetime(2026, 7, 9, 11, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(observation(), generated_at=datetime(2026, 7, 9, 12))
    with pytest.raises(ValueError, match="first_stale_at must not be after generated_at"):
        build_report(
            observation(
                first_stale_at=GENERATED_AT + timedelta(seconds=1),
                recovered_at=GENERATED_AT + timedelta(seconds=2),
            ),
        )
    with pytest.raises(ValueError, match="recovered_at must not be before first_stale_at"):
        observation(first_stale_at=ago(100), recovered_at=ago(200))
    with pytest.raises(ValueError, match="successful_refresh_count"):
        observation(
            attempted_refresh_count=d("1.000000"),
            successful_refresh_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="fallback_retry_count"):
        observation(
            attempted_refresh_count=d("1.000000"),
            successful_refresh_count=d("1.000000"),
            fallback_retry_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="watch_recovered_ratio"):
        config(watch_recovered_ratio=d("0.400000"), block_recovered_ratio=d("0.500000"))

    public_fields = {
        field.name
        for cls in (
            type(config()),
            type(observation()),
            type(report),
            type(report.rows[0]),
        )
        for field in fields(cls)
    }
    assert UNSAFE_PUBLIC_FIELD_NAMES.isdisjoint(public_fields)
    for public_name in module.__all__:
        assert_payload_has_no_leaked_surface({"name": public_name})


def test_module_scope_is_report_only_without_external_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Name):
            assert node.id.lower() not in FORBIDDEN_RUNTIME_NAMES
        if isinstance(node, ast.Attribute):
            assert node.attr.lower() not in FORBIDDEN_RUNTIME_NAMES
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in FORBIDDEN_CALLS
            assert call_name.lower() not in FORBIDDEN_RUNTIME_NAMES

    forbidden_import_fragments = (
        "auth",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert ".timestamp(" not in source
    assert ".total_seconds(" not in source


UNSAFE_PUBLIC_FIELD_NAMES = {
    "raw_id",
    "raw_ids",
    "candidate_id",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order_id",
    "trade_id",
    "recommendation",
    "sizing",
}
FORBIDDEN_CALLS = {
    "connect",
    "execute",
    "executemany",
    "open",
    "request",
    "post",
    "put",
    "patch",
    "submit_order",
    "place_order",
    "recommend",
    "size_position",
}
FORBIDDEN_RUNTIME_NAMES = {
    "auth",
    "wallet",
    "token",
    "dsn",
    "order",
    "trade",
    "sizing",
    "recommendation",
    "submit",
    "cancel",
    "replace_order",
    "create_order",
    "connect",
    "commit",
    "rollback",
    "cursor",
    "open",
}


def assert_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (float, int):
        raise AssertionError(f"public numeric was not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            assert_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_decimal_public_numbers(getattr(value, field.name))


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)
    else:
        assert type(value) is not float
        assert type(value) is not int


def assert_payload_has_no_leaked_surface(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "www.",
        "postgres://",
        "mysql://",
        "jdbc:",
        "raw",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
        "recommendation",
        "sizing",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_lower = key.lower()
            assert not any(fragment in key_lower for fragment in forbidden_fragments)
            assert_payload_has_no_leaked_surface(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_surface(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)


def assert_statuses_are_public(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("status"):
                assert item in PUBLIC_STATUSES
            assert_statuses_are_public(item)
    elif isinstance(value, list):
        for item in value:
            assert_statuses_are_public(item)
