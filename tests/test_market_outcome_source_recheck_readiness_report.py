from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.market_outcome_source_recheck_readiness_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_outcome_source_recheck_readiness_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "recheck_due_after_seconds": d("3600.000000"),
        "blocked_recheck_age_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.MarketOutcomeSourceRecheckReadinessConfig(**values)


def source(
    market_id: str,
    *,
    market_slug: str | None = None,
    category_id: str = "politics",
    outcome_source_id: str | None = None,
    checked_seconds_ago: int | None = 600,
    outcome_source_last_rechecked_at: datetime | None = None,
    official_source_acknowledged_at: datetime | None = GENERATED_AT
    - timedelta(minutes=5),
    recheck_cadence_seconds: Decimal | None = d("3600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    if outcome_source_last_rechecked_at is None and checked_seconds_ago is not None:
        outcome_source_last_rechecked_at = GENERATED_AT - timedelta(
            seconds=checked_seconds_ago,
        )
    return module.MarketOutcomeSourceRecheckReadinessSource(
        market_id=market_id,
        market_slug=market_slug if market_slug is not None else f"{market_id}_slug",
        category_id=category_id,
        outcome_source_id=(
            outcome_source_id
            if outcome_source_id is not None
            else f"{market_id}_official_result"
        ),
        outcome_source_last_rechecked_at=outcome_source_last_rechecked_at,
        official_source_acknowledged_at=official_source_acknowledged_at,
        recheck_cadence_seconds=recheck_cadence_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_market_outcome_source_recheck_readiness_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_readonly_decimal_digest_and_json_safe() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.MarketOutcomeSourceRecheckReadinessReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.status == "empty"
    assert report.market_count == d("0.000000")
    assert report.ready_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.missing_source_recheck_count == d("0.000000")
    assert report.missing_official_source_acknowledgement_count == d("0.000000")
    assert report.stale_recheck_count == d("0.000000")
    assert report.blocked_stale_recheck_count == d("0.000000")
    assert report.ready_ratio == d("0.000000")
    assert report.max_source_age_seconds == d("0.000000")
    assert report.max_stale_recheck_age_seconds == d("0.000000")
    assert report.reason_codes == ("market_outcome_source_recheck_readiness_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    with pytest.raises(FrozenInstanceError):
        report.status = "ready"  # type: ignore[misc]

    payload = module.market_outcome_source_recheck_readiness_report_payload(report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["market_count"] == "0.000000"
    assert payload["ready_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    module.validate_market_outcome_source_recheck_readiness_public_payload(payload)
    json.dumps(payload, sort_keys=True)
    _assert_no_public_float_or_int(payload)


def test_status_rollups_reason_codes_and_rows_are_deterministic() -> None:
    report = build_report(
        source("market_ready", checked_seconds_ago=600),
        source("market_watch", checked_seconds_ago=5400),
        source(
            "market_missing_ack",
            checked_seconds_ago=600,
            official_source_acknowledged_at=None,
        ),
        source("market_blocked_stale", checked_seconds_ago=9600),
    )

    assert report.status == "blocked"
    assert report.reason_codes == (
        "market_outcome_source_missing_official_source_acknowledgement",
        "market_outcome_source_recheck_stale",
        "market_outcome_source_recheck_blocked_stale",
    )
    assert report.market_count == d("4.000000")
    assert report.ready_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("2.000000")
    assert report.missing_source_recheck_count == d("0.000000")
    assert report.missing_official_source_acknowledgement_count == d("1.000000")
    assert report.stale_recheck_count == d("2.000000")
    assert report.blocked_stale_recheck_count == d("1.000000")
    assert report.ready_ratio == d("0.250000")
    assert report.max_source_age_seconds == d("9600.000000")
    assert report.max_stale_recheck_age_seconds == d("6000.000000")

    assert tuple(row.market_id for row in report.rows) == (
        "market_blocked_stale",
        "market_missing_ack",
        "market_watch",
        "market_ready",
    )
    assert tuple(row.status for row in report.rows) == (
        "blocked",
        "blocked",
        "watch",
        "ready",
    )
    assert tuple(row.source_age_seconds for row in report.rows) == (
        d("9600.000000"),
        d("600.000000"),
        d("5400.000000"),
        d("600.000000"),
    )
    assert tuple(row.stale_recheck_age_seconds for row in report.rows) == (
        d("6000.000000"),
        d("0.000000"),
        d("1800.000000"),
        d("0.000000"),
    )


def test_dataclasses_are_frozen_exact_decimal_only_and_flags_are_hard() -> None:
    module = api()
    report = build_report(source("market_ready"), source("market_watch", checked_seconds_ago=5400))

    for cls in (
        module.MarketOutcomeSourceRecheckReadinessConfig,
        module.MarketOutcomeSourceRecheckReadinessSource,
        module.MarketOutcomeSourceRecheckReadinessRow,
        module.MarketOutcomeSourceRecheckReadinessReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    _assert_decimal_public_fields(report)
    for row in report.rows:
        _assert_decimal_public_fields(row)

    with pytest.raises(ValueError, match="recheck_due_after_seconds"):
        config(recheck_due_after_seconds=3600)
    with pytest.raises(ValueError, match="blocked_recheck_age_seconds"):
        config(blocked_recheck_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="recheck_cadence_seconds"):
        source("market_bad_cadence", recheck_cadence_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="recheck_cadence_seconds"):
        source("market_int_cadence", recheck_cadence_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        source("market_flag_case", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_datetime_normalization_future_rejection_and_public_string_validation() -> None:
    module = api()
    offset = timezone(timedelta(hours=-4))
    normalized = source(
        "market_offset",
        outcome_source_last_rechecked_at=datetime(2026, 7, 6, 7, 0, tzinfo=offset),
        official_source_acknowledged_at=datetime(2026, 7, 6, 7, 30, tzinfo=offset),
    )

    assert normalized.outcome_source_last_rechecked_at == datetime(
        2026,
        7,
        6,
        11,
        0,
        tzinfo=UTC,
    )
    assert build_report(normalized).rows[0].source_age_seconds == d("3600.000000")

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_outcome_source_recheck_readiness_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(
        ValueError,
        match="outcome_source_last_rechecked_at must be timezone-aware",
    ):
        source(
            "market_naive",
            outcome_source_last_rechecked_at=datetime(2026, 7, 6, 11, 0),
        )
    with pytest.raises(
        ValueError,
        match="outcome_source_last_rechecked_at must not be in the future",
    ):
        build_report(source("market_future", checked_seconds_ago=-1))
    with pytest.raises(ValueError, match="market_id"):
        source(" wallet")
    with pytest.raises(ValueError, match="outcome_source_id"):
        source("market_unsafe_source", outcome_source_id="network_client")


def test_public_payload_validator_rejects_unsafe_surface_values_and_numerics() -> None:
    module = api()
    payload = module.market_outcome_source_recheck_readiness_report_payload(
        build_report(source("market_ready")),
    )

    module.validate_market_outcome_source_recheck_readiness_public_payload(payload)
    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.validate_market_outcome_source_recheck_readiness_public_payload(
            {**payload, "wallet": "paper"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_market_outcome_source_recheck_readiness_public_payload(
            {**payload, "market_id": "network"},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_market_outcome_source_recheck_readiness_public_payload(
            {**payload, "market_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_market_outcome_source_recheck_readiness_public_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_readiness_public_payload(
            {**payload, "market_count": "9.000000"},
        )


def test_module_scope_is_readonly_report_only_and_external_io_free() -> None:
    module = api()

    assert set(module.__all__) == {
        "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_READINESS_CONFIG_VERSION",
        "MarketOutcomeSourceRecheckReadinessConfig",
        "MarketOutcomeSourceRecheckReadinessSource",
        "MarketOutcomeSourceRecheckReadinessRow",
        "MarketOutcomeSourceRecheckReadinessReport",
        "build_market_outcome_source_recheck_readiness_report",
        "market_outcome_source_recheck_readiness_report_payload",
        "validate_market_outcome_source_recheck_readiness_public_payload",
    }

    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    assigned_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Name):
            assigned_names.add(node.id)

    assert not imported_roots.intersection(
        {
            "requests",
            "urllib",
            "httpx",
            "socket",
            "websocket",
            "psycopg",
            "sqlite3",
            "sqlalchemy",
            "supabase",
            "subprocess",
        },
    )
    assert not called_names.intersection(
        {
            "open",
            "connect",
            "request",
            "post",
            "put",
            "patch",
            "delete",
            "execute",
            "commit",
            "rollback",
            "place_order",
            "submit_order",
            "cancel_order",
        },
    )
    assert not assigned_names.intersection(
        {
            "live_trading",
            "wallet",
            "auth",
            "order_client",
            "network_client",
            "database",
            "persistence",
        },
    )


def _assert_decimal_public_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal


def _assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_public_float_or_int(item)
