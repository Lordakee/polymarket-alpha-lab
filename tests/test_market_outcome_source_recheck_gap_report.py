from __future__ import annotations

import ast
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
MODULE_NAME = "polymarket_alpha_lab.market_outcome_source_recheck_gap_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "market_outcome_source_recheck_gap_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
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
        "recheck_due_after_seconds": d("3600.000000"),
        "acknowledgement_due_after_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.MarketOutcomeSourceRecheckGapConfig(**values)


def source(
    market_id: str,
    *,
    market_slug: str | None = None,
    outcome_id: str | None = None,
    source_id: str = "official-resolution-source",
    final_outcome_at: datetime = GENERATED_AT - timedelta(hours=1),
    last_source_rechecked_at: datetime | None = GENERATED_AT - timedelta(minutes=30),
    source_acknowledged_at: datetime | None = GENERATED_AT - timedelta(minutes=20),
    expected_outcome: str | None = "yes",
    source_outcome: str | None = "yes",
):
    module = api()
    return module.MarketOutcomeSourceRecheckGapSource(
        market_id=market_id,
        market_slug=market_slug or f"{market_id}-slug",
        outcome_id=outcome_id or f"{market_id}-outcome",
        source_id=source_id,
        final_outcome_at=final_outcome_at,
        last_source_rechecked_at=last_source_rechecked_at,
        source_acknowledged_at=source_acknowledged_at,
        expected_outcome=expected_outcome,
        source_outcome=source_outcome,
    )


def report(*sources: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_market_outcome_source_recheck_gap_report(
        sources,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_module_contract_names_are_available() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_gap_report_summarizes_outcome_source_recheck_gaps_and_payload() -> None:
    module = api()

    gap_report = report(
        source(
            "market-pass",
            market_slug="alpha-clear",
            final_outcome_at=GENERATED_AT - timedelta(hours=1),
            last_source_rechecked_at=GENERATED_AT - timedelta(minutes=30),
            source_acknowledged_at=GENERATED_AT - timedelta(minutes=20),
            expected_outcome="yes",
            source_outcome="yes",
        ),
        source(
            "market-blocked",
            market_slug="beta-blocked",
            final_outcome_at=GENERATED_AT - timedelta(hours=5),
            last_source_rechecked_at=None,
            source_acknowledged_at=None,
            expected_outcome="yes",
            source_outcome="no",
        ),
        source(
            "market-watch",
            market_slug="gamma-watch",
            final_outcome_at=GENERATED_AT - timedelta(hours=3),
            last_source_rechecked_at=GENERATED_AT - timedelta(minutes=90),
            source_acknowledged_at=GENERATED_AT - timedelta(minutes=80),
            expected_outcome="yes",
            source_outcome="yes",
        ),
    )

    assert type(gap_report) is module.MarketOutcomeSourceRecheckGapReport
    assert gap_report.status == "blocked"
    assert gap_report.source_row_count == d("3")
    assert gap_report.gap_count == d("2")
    assert gap_report.clear_count == d("1")
    assert gap_report.watch_count == d("1")
    assert gap_report.blocked_count == d("1")
    assert gap_report.missing_recheck_count == d("1")
    assert gap_report.overdue_recheck_count == d("2")
    assert gap_report.missing_acknowledgement_count == d("1")
    assert gap_report.source_outcome_conflict_count == d("1")
    assert gap_report.gap_ratio == d("0.666667")
    assert gap_report.missing_recheck_ratio == d("0.333333")
    assert gap_report.overdue_recheck_ratio == d("0.666667")
    assert gap_report.max_recheck_gap_seconds == d("18000.000000")
    assert gap_report.max_acknowledgement_gap_seconds == d("18000.000000")
    assert gap_report.reason_codes == (
        "market_outcome_source_recheck_missing_recheck",
        "market_outcome_source_recheck_overdue_recheck",
        "market_outcome_source_recheck_missing_acknowledgement",
        "market_outcome_source_recheck_conflicting_outcome_source",
    )
    assert tuple(item.reason_code for item in gap_report.reason_code_counts) == (
        gap_report.reason_codes
    )

    assert tuple(row.market_id for row in gap_report.rows) == (
        "market-blocked",
        "market-watch",
        "market-pass",
    )
    blocked, watch, clear = gap_report.rows
    assert blocked.gap_status == "blocked"
    assert blocked.outcome_age_seconds == d("18000.000000")
    assert blocked.recheck_gap_seconds == d("18000.000000")
    assert blocked.acknowledgement_gap_seconds == d("18000.000000")
    assert blocked.last_source_rechecked_at is None
    assert blocked.source_acknowledged_at is None
    assert blocked.reason_codes == (
        "market_outcome_source_recheck_missing_recheck",
        "market_outcome_source_recheck_overdue_recheck",
        "market_outcome_source_recheck_missing_acknowledgement",
        "market_outcome_source_recheck_conflicting_outcome_source",
    )
    assert watch.gap_status == "watch"
    assert watch.recheck_gap_seconds == d("5400.000000")
    assert watch.acknowledgement_gap_seconds == d("6000.000000")
    assert watch.reason_codes == (
        "market_outcome_source_recheck_overdue_recheck",
    )
    assert clear.gap_status == "pass"
    assert clear.reason_codes == ()

    payload = module.market_outcome_source_recheck_gap_report_payload(gap_report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["source_row_count"] == "3"
    assert payload["gap_ratio"] == "0.666667"
    assert payload["rows"][0]["recheck_gap_seconds"] == "18000.000000"
    assert payload["rows"][0]["last_source_rechecked_at"] is None
    assert payload["derived_validation_digest"] == gap_report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert module.validate_market_outcome_source_recheck_gap_public_payload(payload)
    assert_no_numeric_payload(payload)
    assert_no_unsafe_public_surface(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_timezone_normalization_and_decimal_only_public_payload() -> None:
    eastern = timezone(timedelta(hours=-4))

    gap_report = report(
        source(
            "market-tz",
            final_outcome_at=datetime(2026, 7, 6, 7, 0, tzinfo=eastern),
            last_source_rechecked_at=datetime(2026, 7, 6, 8, 0, tzinfo=eastern),
            source_acknowledged_at=datetime(2026, 7, 6, 8, 30, tzinfo=eastern),
        ),
        generated_at=GENERATED_AT + timedelta(hours=1),
    )

    row = gap_report.rows[0]
    assert row.final_outcome_at == datetime(2026, 7, 6, 11, 0, tzinfo=UTC)
    assert row.last_source_rechecked_at == datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
    assert row.source_acknowledged_at == datetime(2026, 7, 6, 12, 30, tzinfo=UTC)
    assert row.outcome_age_seconds == d("7200.000000")
    assert row.recheck_gap_seconds == d("3600.000000")
    assert row.acknowledgement_gap_seconds == d("5400.000000")

    payload = api().market_outcome_source_recheck_gap_report_payload(gap_report)
    assert payload["rows"][0]["final_outcome_at"] == "2026-07-06T11:00:00+00:00"
    assert payload["rows"][0]["last_source_rechecked_at"] == (
        "2026-07-06T12:00:00+00:00"
    )
    assert payload["rows"][0]["source_acknowledged_at"] == (
        "2026-07-06T12:30:00+00:00"
    )
    assert payload["max_recheck_gap_seconds"] == "3600.000000"
    assert_no_numeric_payload(payload)


def test_dataclasses_are_frozen_exact_decimal_hard_flagged_and_digest_bound() -> None:
    module = api()

    for klass in (
        module.MarketOutcomeSourceRecheckGapConfig,
        module.MarketOutcomeSourceRecheckGapSource,
        module.MarketOutcomeSourceRecheckGapReasonCodeCount,
        module.MarketOutcomeSourceRecheckGapRow,
        module.MarketOutcomeSourceRecheckGapReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="recheck_due_after_seconds"):
        config(recheck_due_after_seconds=3600)
    with pytest.raises(ValueError, match="acknowledgement_due_after_seconds"):
        config(acknowledgement_due_after_seconds=_DecimalSubclass("7200.000000"))

    input_source = source("market-frozen")
    with pytest.raises(FrozenInstanceError):
        input_source.market_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_source, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    good_report = report(input_source)
    with pytest.raises(FrozenInstanceError):
        good_report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(good_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="source_row_count"):
        replace(good_report, source_row_count=1)

    decimal_fields = {
        "source_row_count",
        "gap_count",
        "clear_count",
        "watch_count",
        "blocked_count",
        "missing_recheck_count",
        "overdue_recheck_count",
        "missing_acknowledgement_count",
        "source_outcome_conflict_count",
        "gap_ratio",
        "missing_recheck_ratio",
        "overdue_recheck_ratio",
        "max_recheck_gap_seconds",
        "max_acknowledgement_gap_seconds",
    }
    for field in fields(good_report):
        if field.name in decimal_fields:
            assert type(getattr(good_report, field.name)) is Decimal
    for row in good_report.rows:
        for field in fields(row):
            if field.name.endswith("_seconds"):
                assert type(getattr(row, field.name)) is Decimal

    tampered = replace(good_report)
    object.__setattr__(tampered, "gap_count", d("99"))
    with pytest.raises(ValueError, match="gap_count|derived_validation_digest"):
        module.market_outcome_source_recheck_gap_report_payload(tampered)


def test_validates_inputs_public_payload_and_unsafe_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="recheck_due_after_seconds"):
        config(recheck_due_after_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="final_outcome_at must be timezone-aware"):
        source("market-naive", final_outcome_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="final_outcome_at must be timezone-aware"):
        source(
            "market-none-offset",
            final_outcome_at=datetime(2026, 7, 6, 12, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_outcome_source_recheck_gap_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="final_outcome_at must not be after generated_at"):
        report(
            source(
                "market-future",
                final_outcome_at=GENERATED_AT + timedelta(seconds=1),
                last_source_rechecked_at=None,
                source_acknowledged_at=None,
            ),
        )
    with pytest.raises(ValueError, match="last_source_rechecked_at"):
        source(
            "market-rechecked-before-outcome",
            final_outcome_at=GENERATED_AT - timedelta(hours=1),
            last_source_rechecked_at=GENERATED_AT - timedelta(hours=2),
        )
    with pytest.raises(ValueError, match="duplicate market outcome source recheck gap"):
        report(source("market-dup"), source("market-dup"))

    payload = module.market_outcome_source_recheck_gap_report_payload(
        report(
            source(
                "market-json",
                final_outcome_at=GENERATED_AT - timedelta(hours=4),
                last_source_rechecked_at=None,
                source_acknowledged_at=None,
                expected_outcome="yes",
                source_outcome="no",
            ),
        ),
    )
    assert module.validate_market_outcome_source_recheck_gap_public_payload(payload)

    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_market_outcome_source_recheck_gap_public_payload(
            {**payload, "source_row_count": 1},
        )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_gap_public_payload(missing_digest)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_gap_public_payload(
            {**payload, "gap_count": "0"},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.validate_market_outcome_source_recheck_gap_public_payload(
            {**payload, "market_id": "wallet"},
        )

    for forbidden_key in (
        "auth_token",
        "wallet_address",
        "order_id",
        "network_url",
        "database_dsn",
        "persist_path",
        "live_trading_enabled",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            module.validate_market_outcome_source_recheck_gap_public_payload(
                {**payload, forbidden_key: "not allowed"},
            )


def test_module_scope_is_readonly_report_only_and_external_io_free() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source_text.lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "account",
        "broker",
        "database",
        "payload_json",
        "open(",
        "requests",
        "http",
        "network",
        "submit_order",
        "place_order",
        "persist",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    forbidden_import_fragments = (
        "db",
        "env",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
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
