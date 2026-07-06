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
OUTCOME_REPORTED_AT = datetime(2026, 7, 2, 8, 0, tzinfo=UTC)
LATEST_RECHECKED_AT = datetime(2026, 7, 2, 10, 30, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.market_outcome_source_recheck_coverage_report"


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
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    report_module = module()
    values = {
        "config_version": "market-outcome-source-recheck-coverage-test-v0",
        "required_recheck_source_count": d("2.000000"),
        "stale_recheck_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return report_module.MarketOutcomeSourceRecheckCoverageConfig(**values)


def observation(**overrides: object) -> Any:
    report_module = module()
    values = {
        "market_slug": "btc-above-100k",
        "condition_id": "condition-alpha",
        "source_id": "official-resolution-source",
        "source_kind": "official_resolution_source",
        "outcome_reported_at": OUTCOME_REPORTED_AT,
        "latest_source_rechecked_at": LATEST_RECHECKED_AT,
        "source_count": d("2.000000"),
        "rechecked_source_count": d("2.000000"),
        "reason_codes": ("market_outcome_requires_source_recheck",),
    }
    values.update(overrides)
    return report_module.MarketOutcomeSourceRecheckCoverageObservation(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    report_module = module()
    return report_module.build_market_outcome_source_recheck_coverage_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def test_builds_readonly_coverage_report_with_decimal_rollups_sorting_and_payload() -> None:
    report_module = module()
    report = build_report(
        observation(market_slug="market-covered", condition_id="condition-covered"),
        observation(
            market_slug="market-missing",
            condition_id="condition-missing",
            latest_source_rechecked_at=None,
            source_count=d("2.000000"),
            rechecked_source_count=d("0.000000"),
        ),
        observation(
            market_slug="market-partial",
            condition_id="condition-partial",
            source_count=d("3.000000"),
            rechecked_source_count=d("1.000000"),
        ),
        observation(
            market_slug="market-stale",
            condition_id="condition-stale",
            latest_source_rechecked_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
            source_count=d("2.000000"),
            rechecked_source_count=d("2.000000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-outcome-source-recheck-coverage-test-v0"
    assert report.input_count == d("4.000000")
    assert report.row_count == d("4.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("2.000000")
    assert report.blocked_count == d("1.000000")
    assert report.covered_count == d("1.000000")
    assert report.partial_count == d("1.000000")
    assert report.missing_count == d("1.000000")
    assert report.stale_count == d("1.000000")
    assert report.coverage_gap_count == d("3.000000")
    assert report.covered_ratio == d("0.250000")
    assert report.gap_ratio == d("0.750000")
    assert report.reason_codes == (
        "missing_outcome_source_recheck",
        "partial_outcome_source_recheck_coverage",
        "stale_outcome_source_recheck",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.coverage_bucket, row.coverage_status, row.market_slug) for row in report.rows) == (
        ("missing", "blocked", "market-missing"),
        ("partial", "watch", "market-partial"),
        ("stale", "watch", "market-stale"),
        ("covered", "pass", "market-covered"),
    )

    missing, partial, stale, covered = report.rows
    assert missing.reason_codes == ("missing_outcome_source_recheck",)
    assert missing.coverage_ratio == d("0.000000")
    assert missing.missing_recheck_count == d("2.000000")
    assert missing.recheck_age_seconds is None

    assert partial.reason_codes == ("partial_outcome_source_recheck_coverage",)
    assert partial.coverage_ratio == d("0.333333")
    assert partial.missing_recheck_count == d("2.000000")

    assert stale.reason_codes == ("stale_outcome_source_recheck",)
    assert stale.source_age_seconds == d("14400.000000")
    assert stale.recheck_age_seconds == d("12600.000000")

    assert covered.reason_codes == ("outcome_source_recheck_covered",)
    assert covered.coverage_ratio == d("1.000000")
    assert covered.recheck_age_seconds == d("5400.000000")

    payload = report_module.market_outcome_source_recheck_coverage_report_payload(report)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["input_count"] == "4.000000"
    assert payload["gap_ratio"] == "0.750000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["coverage_ratio"] == "0.000000"
    assert payload["rows"][0]["recheck_age_seconds"] is None
    assert payload["rows"][2]["recheck_age_seconds"] == "12600.000000"
    assert report_module.validate_market_outcome_source_recheck_coverage_report_payload(payload)
    assert_no_public_numeric(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_and_all_covered_inputs_are_deterministic_readonly_reports() -> None:
    empty = build_report()
    assert empty.input_count == d("0.000000")
    assert empty.row_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.blocked_count == d("0.000000")
    assert empty.covered_ratio == d("0.000000")
    assert empty.gap_ratio == d("0.000000")
    assert empty.reason_codes == ("outcome_source_recheck_coverage_empty",)
    assert empty.rows == ()
    assert len(empty.derived_validation_digest) == 64

    all_covered = build_report(
        observation(condition_id="condition-beta", market_slug="market-beta"),
        observation(condition_id="condition-alpha", market_slug="market-alpha"),
    )

    assert all_covered.input_count == d("2.000000")
    assert all_covered.row_count == d("2.000000")
    assert all_covered.covered_count == d("2.000000")
    assert all_covered.coverage_gap_count == d("0.000000")
    assert all_covered.covered_ratio == d("1.000000")
    assert all_covered.gap_ratio == d("0.000000")
    assert all_covered.reason_codes == ("outcome_source_recheck_coverage_complete",)
    assert tuple(row.market_slug for row in all_covered.rows) == ("market-alpha", "market-beta")


def test_aware_datetimes_normalize_to_utc_and_payload_uses_decimal_strings() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        observation(
            market_slug="market-tz",
            outcome_reported_at=datetime(2026, 7, 2, 7, 0, tzinfo=eastern),
            latest_source_rechecked_at=datetime(2026, 7, 2, 7, 45, tzinfo=eastern),
        ),
    )

    row = report.rows[0]
    assert row.outcome_reported_at == datetime(2026, 7, 2, 11, 0, tzinfo=UTC)
    assert row.latest_source_rechecked_at == datetime(2026, 7, 2, 11, 45, tzinfo=UTC)
    assert row.source_age_seconds == d("3600.000000")
    assert row.recheck_age_seconds == d("900.000000")

    payload = module().market_outcome_source_recheck_coverage_report_payload(report)

    assert payload["rows"][0]["outcome_reported_at"] == "2026-07-02T11:00:00+00:00"
    assert payload["rows"][0]["latest_source_rechecked_at"] == "2026-07-02T11:45:00+00:00"
    assert payload["rows"][0]["source_age_seconds"] == "3600.000000"
    assert_no_public_numeric(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    report_module = module()

    assert report_module.__all__ == (
        "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_COVERAGE_REPORT_CONFIG_VERSION",
        "MarketOutcomeSourceRecheckCoverageConfig",
        "MarketOutcomeSourceRecheckCoverageObservation",
        "MarketOutcomeSourceRecheckCoverageRow",
        "MarketOutcomeSourceRecheckCoverageReport",
        "build_market_outcome_source_recheck_coverage_report",
        "market_outcome_source_recheck_coverage_report_payload",
        "validate_market_outcome_source_recheck_coverage_report_payload",
    )
    for exported_name in report_module.__all__:
        value = getattr(report_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(observation())
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
        report.rows[0].coverage_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        observation(source_count=2)
    with pytest.raises(ValueError, match="required_recheck_source_count must be a Decimal"):
        cfg(required_recheck_source_count=DerivedDecimal("2.000000"))
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(report_module.MarketOutcomeSourceRecheckCoverageConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(report_module.MarketOutcomeSourceRecheckCoverageObservation):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(report_module.MarketOutcomeSourceRecheckCoverageRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(report_module.MarketOutcomeSourceRecheckCoverageReport):
            pass


def test_validation_rejects_datetimes_decimals_sequences_and_false_hard_flags() -> None:
    report_module = module()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report_module.build_market_outcome_source_recheck_coverage_report(
            (),
            config=cfg(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report_module.build_market_outcome_source_recheck_coverage_report(
            (),
            config=cfg(),
            generated_at=DerivedDatetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="outcome_reported_at must be timezone-aware"):
        observation(outcome_reported_at=datetime(2026, 7, 2, 8, 0))
    with pytest.raises(ValueError, match="outcome_reported_at must be timezone-aware"):
        observation(
            outcome_reported_at=datetime(2026, 7, 2, 8, 0, tzinfo=NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="latest_source_rechecked_at"):
        observation(latest_source_rechecked_at=datetime(2026, 7, 2, 7, 59, tzinfo=UTC))
    with pytest.raises(ValueError, match="latest_source_rechecked_at"):
        observation(rechecked_source_count=d("1.000000"), latest_source_rechecked_at=None)
    with pytest.raises(ValueError, match="rechecked_source_count"):
        observation(source_count=d("1.000000"), rechecked_source_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("dup", "dup"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(observation(latest_source_rechecked_at=datetime(2026, 7, 2, 13, 0, tzinfo=UTC)))
    shifted = build_report(
        observation(),
        generated_at=datetime(2026, 7, 2, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.generated_at.tzinfo is UTC
    with pytest.raises(ValueError, match="observations"):
        report_module.build_market_outcome_source_recheck_coverage_report(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        report_module.build_market_outcome_source_recheck_coverage_report(
            (observation(),),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_consistency_and_digest_are_tamper_evident() -> None:
    report_module = module()
    report = build_report(observation())

    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = report_module.market_outcome_source_recheck_coverage_report_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["input_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.validate_market_outcome_source_recheck_coverage_report_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "market_slug", "market-mutated")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.market_outcome_source_recheck_coverage_report_payload(report)


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

    report = build_report(observation())
    payload = report_module.market_outcome_source_recheck_coverage_report_payload(report)

    unsafe_payload = dict(payload)
    unsafe_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        report_module.validate_market_outcome_source_recheck_coverage_report_payload(
            unsafe_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["input_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        report_module.validate_market_outcome_source_recheck_coverage_report_payload(
            numeric_payload,
        )


def test_module_omits_runtime_financial_action_and_storage_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_outcome_source_recheck_coverage_report.py",
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


def assert_no_public_numeric(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if type(value) is int:
        raise AssertionError("payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric(item)
