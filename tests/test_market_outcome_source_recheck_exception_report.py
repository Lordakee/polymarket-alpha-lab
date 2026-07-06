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
RECHECK_REQUESTED_AT = datetime(2026, 7, 2, 8, 0, tzinfo=UTC)
SOURCE_OBSERVED_AT = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)


class DerivedDatetime(datetime):
    pass


class DerivedDecimal(Decimal):
    pass


class NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def module() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.market_outcome_source_recheck_exception_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    report_module = module()
    values = {
        "config_version": "market-outcome-source-recheck-exception-test-v0",
        "stale_source_seconds": d("7200.000000"),
        "repeated_market_threshold": d("2.000000"),
    }
    values.update(overrides)
    return report_module.MarketOutcomeSourceRecheckExceptionConfig(**values)


def observation(**overrides: object) -> Any:
    report_module = module()
    values = {
        "market_slug": "btc-above-100k",
        "condition_id": "condition-alpha",
        "source_id": "official-resolution-source",
        "source_kind": "official_resolution_source",
        "recheck_requested_at": RECHECK_REQUESTED_AT,
        "source_observed_at": SOURCE_OBSERVED_AT,
        "official_source_acknowledged_at": datetime(2026, 7, 2, 10, 30, tzinfo=UTC),
        "source_conflict_resolved_at": datetime(2026, 7, 2, 10, 30, tzinfo=UTC),
        "has_source_conflict": False,
        "reason_codes": ("closed_market_pending_source_recheck",),
    }
    values.update(overrides)
    return report_module.MarketOutcomeSourceRecheckObservation(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    report_module = module()
    return report_module.build_market_outcome_source_recheck_exception_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def test_builds_readonly_exception_report_with_decimal_counts_sorting_and_payload() -> None:
    report_module = module()
    report = build_report(
        observation(market_slug="market-pass", condition_id="condition-pass"),
        observation(
            market_slug="market-stale",
            condition_id="condition-stale",
            source_observed_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
            official_source_acknowledged_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
        ),
        observation(
            market_slug="market-missing-ack",
            condition_id="condition-missing-ack",
            official_source_acknowledged_at=None,
        ),
        observation(
            market_slug="market-conflict",
            condition_id="condition-conflict",
            official_source_acknowledged_at=datetime(2026, 7, 2, 10, 15, tzinfo=UTC),
            source_conflict_resolved_at=None,
            has_source_conflict=True,
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-outcome-source-recheck-exception-test-v0"
    assert report.input_count == d("4.000000")
    assert report.exception_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("2.000000")
    assert report.missing_official_source_acknowledgement_count == d("1.000000")
    assert report.stale_outcome_source_count == d("1.000000")
    assert report.unresolved_source_conflict_count == d("1.000000")
    assert report.repeated_market_gap_count == d("0.000000")
    assert report.exception_ratio == d("0.750000")
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.severity, row.status, row.market_slug) for row in report.rows) == (
        ("critical", "blocked", "market-conflict"),
        ("critical", "blocked", "market-missing-ack"),
        ("warning", "watch", "market-stale"),
    )

    conflict, missing_ack, stale = report.rows
    assert conflict.reason_codes == ("unresolved_source_conflict",)
    assert conflict.source_age_seconds == d("7200.000000")
    assert conflict.acknowledgement_age_seconds == d("6300.000000")
    assert conflict.recheck_to_source_delta_seconds == d("7200.000000")
    assert conflict.recheck_to_acknowledgement_delta_seconds == d("8100.000000")

    assert missing_ack.reason_codes == ("missing_official_source_acknowledgement",)
    assert missing_ack.acknowledgement_age_seconds is None
    assert missing_ack.recheck_to_acknowledgement_delta_seconds is None

    assert stale.reason_codes == ("stale_outcome_source",)
    assert stale.source_age_seconds == d("12600.000000")
    assert stale.acknowledgement_age_seconds == d("10800.000000")

    payload = report_module.market_outcome_source_recheck_exception_report_payload(report)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["input_count"] == "4.000000"
    assert payload["exception_ratio"] == "0.750000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["source_age_seconds"] == "7200.000000"
    assert payload["rows"][1]["acknowledgement_age_seconds"] is None
    assert report_module.validate_market_outcome_source_recheck_exception_report_payload(
        payload,
    )
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_and_all_pass_inputs_are_deterministic_readonly_reports() -> None:
    empty = build_report()
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.exception_count == d("0.000000")
    assert empty.exception_ratio == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.blocked_count == d("0.000000")
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64

    all_pass = build_report(
        observation(condition_id="condition-beta", market_slug="market-beta"),
        observation(condition_id="condition-alpha", market_slug="market-alpha"),
    )

    assert all_pass.input_count == d("2.000000")
    assert all_pass.row_count == d("0.000000")
    assert all_pass.exception_count == d("0.000000")
    assert all_pass.pass_count == d("2.000000")
    assert all_pass.rows == ()
    assert len(all_pass.derived_validation_digest) == 64


def test_repeated_market_gap_marks_blocking_rows_once_threshold_is_met() -> None:
    report = build_report(
        observation(
            market_slug="same-market",
            condition_id="condition-missing-ack",
            official_source_acknowledged_at=None,
        ),
        observation(
            market_slug="same-market",
            condition_id="condition-conflict",
            source_conflict_resolved_at=None,
            has_source_conflict=True,
        ),
    )

    assert report.repeated_market_gap_count == d("1.000000")
    assert tuple(row.repeated_market_gap_count for row in report.rows) == (
        d("2.000000"),
        d("2.000000"),
    )
    assert all("repeated_market_gap" in row.reason_codes for row in report.rows)


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    report_module = module()

    assert report_module.__all__ == (
        "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_EXCEPTION_REPORT_CONFIG_VERSION",
        "MarketOutcomeSourceRecheckExceptionConfig",
        "MarketOutcomeSourceRecheckObservation",
        "MarketOutcomeSourceRecheckExceptionRow",
        "MarketOutcomeSourceRecheckExceptionReport",
        "build_market_outcome_source_recheck_exception_report",
        "market_outcome_source_recheck_exception_report_payload",
        "validate_market_outcome_source_recheck_exception_report_payload",
    )
    for exported_name in report_module.__all__:
        value = getattr(report_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(
        observation(
            market_slug="market-stale",
            condition_id="condition-stale",
            source_observed_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
        ),
    )

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
        report.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(report_module.MarketOutcomeSourceRecheckExceptionConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(report_module.MarketOutcomeSourceRecheckObservation):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(report_module.MarketOutcomeSourceRecheckExceptionRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(report_module.MarketOutcomeSourceRecheckExceptionReport):
            pass


def test_validation_rejects_datetimes_decimals_sequences_and_false_hard_flags() -> None:
    report_module = module()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report_module.build_market_outcome_source_recheck_exception_report(
            (),
            config=cfg(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report_module.build_market_outcome_source_recheck_exception_report(
            (),
            config=cfg(),
            generated_at=DerivedDatetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        observation(source_observed_at=datetime(2026, 7, 2, 9, 0))
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        observation(
            source_observed_at=datetime(
                2026,
                7,
                2,
                9,
                0,
                tzinfo=NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="source_observed_at"):
        observation(source_observed_at=datetime(2026, 7, 2, 7, 59, tzinfo=UTC))
    with pytest.raises(ValueError, match="official_source_acknowledged_at"):
        observation(
            official_source_acknowledged_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_conflict_resolved_at"):
        observation(
            source_conflict_resolved_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="has_source_conflict"):
        observation(has_source_conflict=1)
    with pytest.raises(ValueError, match="stale_source_seconds must be a Decimal"):
        cfg(stale_source_seconds=7200)
    with pytest.raises(ValueError, match="repeated_market_threshold must be a Decimal"):
        cfg(repeated_market_threshold=DerivedDecimal("2.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            observation(
                official_source_acknowledged_at=datetime(2026, 7, 2, 13, 0, tzinfo=UTC),
            ),
        )
    shifted = build_report(
        observation(),
        generated_at=datetime(2026, 7, 2, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.generated_at.tzinfo is UTC
    with pytest.raises(ValueError, match="observations"):
        report_module.build_market_outcome_source_recheck_exception_report(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        report_module.build_market_outcome_source_recheck_exception_report(
            (observation(),),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_consistency_and_digest_are_tamper_evident() -> None:
    report_module = module()
    report = build_report(
        observation(
            market_slug="market-stale",
            condition_id="condition-stale",
            source_observed_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
        ),
    )

    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="watch_count"):
        replace(report, watch_count=d("0.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = report_module.market_outcome_source_recheck_exception_report_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["input_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.validate_market_outcome_source_recheck_exception_report_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "market_slug", "market-mutated")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.market_outcome_source_recheck_exception_report_payload(report)


def test_unsafe_public_surface_values_and_payload_keys_are_rejected() -> None:
    report_module = module()
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

    report = build_report(
        observation(
            market_slug="market-stale",
            condition_id="condition-stale",
            source_observed_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
        ),
    )
    payload = report_module.market_outcome_source_recheck_exception_report_payload(report)

    unsafe_payload = dict(payload)
    unsafe_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        report_module.validate_market_outcome_source_recheck_exception_report_payload(
            unsafe_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["input_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        report_module.validate_market_outcome_source_recheck_exception_report_payload(
            numeric_payload,
        )


def test_module_omits_runtime_financial_action_and_storage_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_outcome_source_recheck_exception_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlalchemy",
        "live_trading",
        "authentication",
        "private_key",
        "account",
        "broker",
        "submit",
        "cancel",
        "signing",
        "advice",
    ):
        assert forbidden not in lowered

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
