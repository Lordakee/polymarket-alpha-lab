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


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
FINAL_OUTCOME_AT = datetime(2026, 7, 6, 10, 0, tzinfo=UTC)
RECHECK_REQUESTED_AT = datetime(2026, 7, 6, 10, 5, tzinfo=UTC)


class DatetimeSubclass(datetime):
    pass


class DecimalSubclass(Decimal):
    pass


class NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.market_outcome_source_recheck_latency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "market-outcome-source-recheck-latency-test-v0",
        "watch_recheck_latency_seconds": d("900.000000"),
        "blocked_recheck_latency_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return module.MarketOutcomeSourceRecheckLatencyConfig(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "market_slug": "btc-above-100k",
        "condition_id": "condition-alpha",
        "outcome_id": "yes",
        "source_id": "official-resolution-source",
        "final_outcome_at": FINAL_OUTCOME_AT,
        "recheck_requested_at": RECHECK_REQUESTED_AT,
        "source_rechecked_at": RECHECK_REQUESTED_AT + timedelta(minutes=5),
        "source_acknowledged_at": RECHECK_REQUESTED_AT + timedelta(minutes=7),
        "expected_outcome": "resolved_yes",
        "source_outcome": "resolved_yes",
    }
    values.update(overrides)
    return module.MarketOutcomeSourceRecheckObservation(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_market_outcome_source_recheck_latency_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def test_builds_readonly_latency_report_with_decimal_metrics_and_payload() -> None:
    module = api()
    report = build_report(
        observation(market_slug="market-ready", condition_id="condition-ready"),
        observation(
            market_slug="market-slow",
            condition_id="condition-slow",
            source_rechecked_at=datetime(2026, 7, 6, 11, 0, tzinfo=UTC),
            source_acknowledged_at=datetime(2026, 7, 6, 11, 5, tzinfo=UTC),
        ),
        observation(
            market_slug="market-missing",
            condition_id="condition-missing",
            source_rechecked_at=None,
            source_acknowledged_at=None,
            source_outcome=None,
        ),
        observation(
            market_slug="market-mismatch",
            condition_id="condition-mismatch",
            source_rechecked_at=RECHECK_REQUESTED_AT + timedelta(minutes=15),
            source_acknowledged_at=RECHECK_REQUESTED_AT + timedelta(minutes=20),
            source_outcome="resolved_no",
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-outcome-source-recheck-latency-test-v0"
    assert report.input_count == d("4.000000")
    assert report.row_count == d("4.000000")
    assert report.ready_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("2.000000")
    assert report.issue_count == d("3.000000")
    assert report.missing_recheck_count == d("1.000000")
    assert report.slow_recheck_count == d("1.000000")
    assert report.missing_acknowledgement_count == d("1.000000")
    assert report.outcome_mismatch_count == d("1.000000")
    assert report.issue_ratio == d("0.750000")
    assert report.max_recheck_latency_seconds == d("6900.000000")
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_slug for row in report.rows) == (
        "market-missing",
        "market-mismatch",
        "market-slow",
        "market-ready",
    )

    missing, mismatch, slow, ready = report.rows
    assert missing.latency_status == "blocked"
    assert missing.reason_codes == (
        "missing_outcome_source_recheck",
        "missing_source_acknowledgement",
    )
    assert missing.source_recheck_latency_seconds == d("6900.000000")
    assert missing.source_acknowledgement_latency_seconds is None
    assert missing.source_outcome is None

    assert mismatch.latency_status == "blocked"
    assert mismatch.reason_codes == ("outcome_source_mismatch",)
    assert mismatch.source_recheck_latency_seconds == d("900.000000")
    assert mismatch.source_acknowledgement_latency_seconds == d("1200.000000")

    assert slow.latency_status == "watch"
    assert slow.reason_codes == ("slow_outcome_source_recheck",)
    assert slow.source_recheck_latency_seconds == d("3300.000000")

    assert ready.latency_status == "ready"
    assert ready.reason_codes == ("outcome_source_recheck_latency_clear",)
    assert ready.source_recheck_latency_seconds == d("300.000000")
    assert ready.source_acknowledgement_latency_seconds == d("420.000000")

    payload = module.market_outcome_source_recheck_latency_report_payload(report)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["input_count"] == "4.000000"
    assert payload["issue_ratio"] == "0.750000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["source_recheck_latency_seconds"] == "6900.000000"
    assert payload["rows"][0]["source_acknowledgement_latency_seconds"] is None
    assert module.validate_market_outcome_source_recheck_latency_report_payload(payload)
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_and_all_ready_reports_are_deterministic() -> None:
    empty = build_report()
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.ready_count == d("0.000000")
    assert empty.issue_count == d("0.000000")
    assert empty.issue_ratio == d("0.000000")
    assert empty.max_recheck_latency_seconds == d("0.000000")
    assert empty.rows == ()

    all_ready = build_report(
        observation(market_slug="market-beta", condition_id="condition-beta"),
        observation(market_slug="market-alpha", condition_id="condition-alpha"),
    )
    assert all_ready.input_count == d("2.000000")
    assert all_ready.row_count == d("2.000000")
    assert all_ready.ready_count == d("2.000000")
    assert all_ready.issue_count == d("0.000000")
    assert tuple(row.market_slug for row in all_ready.rows) == (
        "market-alpha",
        "market-beta",
    )


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_LATENCY_REPORT_CONFIG_VERSION",
        "MarketOutcomeSourceRecheckLatencyConfig",
        "MarketOutcomeSourceRecheckObservation",
        "MarketOutcomeSourceRecheckLatencyRow",
        "MarketOutcomeSourceRecheckLatencyReport",
        "build_market_outcome_source_recheck_latency_report",
        "market_outcome_source_recheck_latency_report_payload",
        "validate_market_outcome_source_recheck_latency_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(observation(market_slug="market-slow"))
    for item in (cfg(), observation(), report, *report.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
            ):
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].latency_status = "blocked"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.MarketOutcomeSourceRecheckLatencyConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(module.MarketOutcomeSourceRecheckObservation):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.MarketOutcomeSourceRecheckLatencyRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.MarketOutcomeSourceRecheckLatencyReport):
            pass


def test_validation_rejects_bad_types_timelines_duplicates_and_false_flags() -> None:
    module = api()
    with pytest.raises(ValueError, match="watch_recheck_latency_seconds must be a Decimal"):
        cfg(watch_recheck_latency_seconds=900)
    with pytest.raises(ValueError, match="blocked_recheck_latency_seconds must be a Decimal"):
        cfg(blocked_recheck_latency_seconds=DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)
    with pytest.raises(ValueError, match="final_outcome_at must be a datetime"):
        observation(final_outcome_at=DatetimeSubclass(2026, 7, 6, 10, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="final_outcome_at must be timezone-aware"):
        observation(final_outcome_at=datetime(2026, 7, 6, 10, 0))
    with pytest.raises(ValueError, match="final_outcome_at must be timezone-aware"):
        observation(
            final_outcome_at=datetime(
                2026,
                7,
                6,
                10,
                0,
                tzinfo=NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="recheck_requested_at"):
        observation(recheck_requested_at=FINAL_OUTCOME_AT - timedelta(seconds=1))
    with pytest.raises(ValueError, match="source_rechecked_at"):
        observation(source_rechecked_at=RECHECK_REQUESTED_AT - timedelta(seconds=1))
    with pytest.raises(ValueError, match="source_acknowledged_at"):
        observation(source_acknowledged_at=RECHECK_REQUESTED_AT - timedelta(seconds=1))
    with pytest.raises(ValueError, match="source_outcome"):
        observation(source_rechecked_at=None, source_outcome="resolved_yes")
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            observation(
                source_rechecked_at=GENERATED_AT + timedelta(seconds=1),
                source_acknowledged_at=GENERATED_AT + timedelta(seconds=2),
            ),
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_report(observation(), observation())
    with pytest.raises(ValueError, match="observations"):
        module.build_market_outcome_source_recheck_latency_report(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_market_outcome_source_recheck_latency_report(
            (observation(),),
            config=object(),
            generated_at=GENERATED_AT,
        )

    shifted = build_report(
        observation(
            final_outcome_at=datetime(
                2026,
                7,
                6,
                6,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            recheck_requested_at=datetime(
                2026,
                7,
                6,
                6,
                5,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            source_rechecked_at=datetime(
                2026,
                7,
                6,
                6,
                10,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            source_acknowledged_at=datetime(
                2026,
                7,
                6,
                6,
                12,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
    )
    assert shifted.rows[0].source_recheck_latency_seconds == d("300.000000")
    assert shifted.rows[0].source_acknowledgement_latency_seconds == d("420.000000")


def test_report_consistency_and_digest_are_tamper_evident() -> None:
    module = api()
    report = build_report(observation(market_slug="market-slow"))

    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="ready_count"):
        replace(report, ready_count=d("0.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.market_outcome_source_recheck_latency_report_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["input_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_market_outcome_source_recheck_latency_report_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "market_slug", "market-mutated")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.market_outcome_source_recheck_latency_report_payload(report)


def test_unsafe_public_surface_values_and_payload_keys_are_rejected() -> None:
    module = api()
    unsafe_terms = (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
    )

    for unsafe_term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public surface"):
            observation(market_slug=f"market-{unsafe_term}")

    payload = module.market_outcome_source_recheck_latency_report_payload(
        build_report(observation(market_slug="market-ready")),
    )
    unsafe_payload = dict(payload)
    unsafe_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_market_outcome_source_recheck_latency_report_payload(
            unsafe_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["input_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_market_outcome_source_recheck_latency_report_payload(
            numeric_payload,
        )


def test_module_omits_runtime_financial_action_and_storage_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_outcome_source_recheck_latency_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    for blocked_text in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "private_key",
        "credential",
        "secret",
        "token",
        "signing",
        "submit",
        "cancel",
        "broker",
    ):
        assert blocked_text not in lowered
    for blocked_text in (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
    ):
        assert blocked_text not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def assert_no_float_or_int(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if type(value) is int:
        raise AssertionError("payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)
