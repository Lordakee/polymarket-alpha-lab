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
SOURCE_OBSERVED_AT = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)
LAST_RECHECKED_AT = datetime(2026, 7, 2, 11, 0, tzinfo=UTC)


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
        "polymarket_alpha_lab.market_outcome_source_recheck_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    report_module = module()
    values = {
        "config_version": "market-outcome-source-recheck-priority-test-v0",
        "stale_recheck_seconds": d("7200.000000"),
        "urgent_recheck_seconds": d("21600.000000"),
        "stale_source_seconds": d("7200.000000"),
        "urgent_source_seconds": d("21600.000000"),
    }
    values.update(overrides)
    return report_module.MarketOutcomeSourceRecheckPriorityConfig(**values)


def candidate(**overrides: object) -> Any:
    report_module = module()
    values = {
        "market_slug": "btc-above-100k",
        "condition_id": "condition-alpha",
        "source_id": "official-resolution-source",
        "source_kind": "official_resolution_source",
        "source_observed_at": SOURCE_OBSERVED_AT,
        "last_rechecked_at": LAST_RECHECKED_AT,
        "official_source_acknowledged_at": datetime(2026, 7, 2, 10, 30, tzinfo=UTC),
        "has_source_conflict": False,
        "historical_gap_count": d("0.000000"),
    }
    values.update(overrides)
    return report_module.MarketOutcomeSourceRecheckPriorityCandidate(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    report_module = module()
    return report_module.build_market_outcome_source_recheck_priority_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)


def test_builds_readonly_priority_report_with_decimal_ranking_and_payload() -> None:
    report_module = module()
    report = build_report(
        candidate(
            market_slug="market-low",
            condition_id="condition-low",
            source_observed_at=datetime(2026, 7, 2, 11, 30, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 2, 11, 45, tzinfo=UTC),
            official_source_acknowledged_at=datetime(2026, 7, 2, 11, 35, tzinfo=UTC),
        ),
        candidate(
            market_slug="market-stale",
            condition_id="condition-stale",
            source_observed_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
            official_source_acknowledged_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
        ),
        candidate(
            market_slug="market-missing-ack",
            condition_id="condition-missing-ack",
            source_observed_at=datetime(2026, 7, 2, 7, 0, tzinfo=UTC),
            last_rechecked_at=None,
            official_source_acknowledged_at=None,
            historical_gap_count=d("1.000000"),
        ),
        candidate(
            market_slug="market-conflict",
            condition_id="condition-conflict",
            source_observed_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 2, 5, 30, tzinfo=UTC),
            official_source_acknowledged_at=datetime(2026, 7, 2, 10, 30, tzinfo=UTC),
            has_source_conflict=True,
            historical_gap_count=d("2.000000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-outcome-source-recheck-priority-test-v0"
    assert report.candidate_count == d("4.000000")
    assert report.row_count == d("4.000000")
    assert report.urgent_count == d("2.000000")
    assert report.watch_count == d("1.000000")
    assert report.low_count == d("1.000000")
    assert report.recheck_count == d("3.000000")
    assert report.max_priority_score == d("100.000000")
    assert report.max_source_age_seconds == d("18000.000000")
    assert report.status == "urgent"
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.priority_status, row.market_slug) for row in report.rows) == (
        ("urgent", "market-conflict"),
        ("urgent", "market-missing-ack"),
        ("watch", "market-stale"),
        ("low", "market-low"),
    )

    conflict, missing_ack, stale, low = report.rows
    assert conflict.priority_rank == d("1.000000")
    assert conflict.priority_score == d("100.000000")
    assert conflict.source_age_seconds == d("7200.000000")
    assert conflict.recheck_age_seconds == d("23400.000000")
    assert conflict.acknowledgement_age_seconds == d("5400.000000")
    assert conflict.reason_codes == (
        "source_recheck_urgent",
        "outcome_source_age_stale",
        "unresolved_source_conflict",
        "historical_source_gap_present",
        "priority_score_clamped",
    )
    assert missing_ack.priority_score == d("90.000000")
    assert missing_ack.recheck_age_seconds is None
    assert missing_ack.acknowledgement_age_seconds is None
    assert missing_ack.reason_codes == (
        "source_never_rechecked",
        "outcome_source_age_stale",
        "missing_official_source_acknowledgement",
        "historical_source_gap_present",
    )
    assert stale.priority_score == d("30.000000")
    assert stale.reason_codes == (
        "source_recheck_stale",
        "outcome_source_age_stale",
    )
    assert low.priority_score == d("0.000000")
    assert low.reason_codes == ("source_recheck_recent",)

    payload = report_module.market_outcome_source_recheck_priority_report_payload(report)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["candidate_count"] == "4.000000"
    assert payload["max_priority_score"] == "100.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["priority_rank"] == "1.000000"
    assert payload["rows"][0]["priority_score"] == "100.000000"
    assert payload["rows"][1]["recheck_age_seconds"] is None
    assert report_module.validate_market_outcome_source_recheck_priority_report_payload(
        payload,
    )
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_input_returns_deterministic_readonly_report() -> None:
    report = build_report()

    assert report.candidate_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.urgent_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.low_count == d("0.000000")
    assert report.recheck_count == d("0.000000")
    assert report.max_priority_score == d("0.000000")
    assert report.max_source_age_seconds is None
    assert report.status == "empty"
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64


def test_dataclasses_are_frozen_exact_decimal_only_and_reject_subclassing() -> None:
    report_module = module()

    assert report_module.__all__ == (
        "DEFAULT_MARKET_OUTCOME_SOURCE_RECHECK_PRIORITY_REPORT_CONFIG_VERSION",
        "MarketOutcomeSourceRecheckPriorityConfig",
        "MarketOutcomeSourceRecheckPriorityCandidate",
        "MarketOutcomeSourceRecheckPriorityRow",
        "MarketOutcomeSourceRecheckPriorityReport",
        "build_market_outcome_source_recheck_priority_report",
        "market_outcome_source_recheck_priority_report_payload",
        "validate_market_outcome_source_recheck_priority_report_payload",
    )
    for exported_name in report_module.__all__:
        value = getattr(report_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(
        candidate(
            source_observed_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
        ),
    )

    for item in (cfg(), candidate(), report, *report.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) not in (float, int)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_seconds")
            ):
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(cfg(), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(report_module.MarketOutcomeSourceRecheckPriorityConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeCandidate(report_module.MarketOutcomeSourceRecheckPriorityCandidate):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(report_module.MarketOutcomeSourceRecheckPriorityRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(report_module.MarketOutcomeSourceRecheckPriorityReport):
            pass


def test_validation_rejects_numerics_datetimes_sequences_and_unsafe_values() -> None:
    report_module = module()

    with pytest.raises(ValueError, match="stale_recheck_seconds must be a Decimal"):
        cfg(stale_recheck_seconds=7200)
    with pytest.raises(ValueError, match="urgent_source_seconds must be a Decimal"):
        cfg(urgent_source_seconds=DerivedDecimal("21600.000000"))
    with pytest.raises(ValueError, match="urgent_recheck_seconds"):
        cfg(urgent_recheck_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="historical_gap_count must be a Decimal"):
        candidate(historical_gap_count=1)
    with pytest.raises(ValueError, match="has_source_conflict must be a bool"):
        candidate(has_source_conflict=1)
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        candidate(source_observed_at=datetime(2026, 7, 2, 10, 0))
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        candidate(
            source_observed_at=datetime(
                2026,
                7,
                2,
                10,
                0,
                tzinfo=NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report_module.build_market_outcome_source_recheck_priority_report(
            (),
            config=cfg(),
            generated_at=DerivedDatetime(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="last_rechecked_at"):
        candidate(
            last_rechecked_at=datetime(2026, 7, 2, 9, 0),
        )
    with pytest.raises(ValueError, match="official_source_acknowledged_at"):
        candidate(
            source_observed_at=datetime(2026, 7, 2, 10, 0, tzinfo=UTC),
            official_source_acknowledged_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            candidate(
                source_observed_at=datetime(2026, 7, 2, 13, 0, tzinfo=UTC),
                official_source_acknowledged_at=None,
            ),
        )
    with pytest.raises(ValueError, match="unsafe"):
        candidate(market_slug="wallet-market")
    with pytest.raises(ValueError, match="candidates"):
        report_module.build_market_outcome_source_recheck_priority_report(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        report_module.build_market_outcome_source_recheck_priority_report(
            (candidate(),),
            config=object(),
            generated_at=GENERATED_AT,
        )

    shifted = build_report(
        candidate(),
        generated_at=datetime(2026, 7, 2, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.generated_at.tzinfo is UTC


def test_report_consistency_and_digest_are_tamper_evident() -> None:
    report_module = module()
    report = build_report(
        candidate(
            source_observed_at=datetime(2026, 7, 2, 8, 30, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 2, 9, 0, tzinfo=UTC),
        ),
    )

    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="watch_count"):
        replace(report, watch_count=d("0.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="priority_rank"):
        replace(report.rows[0], priority_rank=d("2.000000"))
    with pytest.raises(ValueError, match="priority_score"):
        replace(report.rows[0], priority_score=d("99.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = report_module.market_outcome_source_recheck_priority_report_payload(report)
    tampered = {
        **payload,
        "rows": [{**payload["rows"][0], "priority_score": "99.000000"}],
    }
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_module.validate_market_outcome_source_recheck_priority_report_payload(
            tampered,
        )


def test_public_payload_validator_rejects_unsafe_surfaces_and_public_numerics() -> None:
    report_module = module()
    payload = report_module.market_outcome_source_recheck_priority_report_payload(
        build_report(candidate()),
    )

    assert report_module.validate_market_outcome_source_recheck_priority_report_payload(
        payload,
    )
    with pytest.raises(ValueError, match="unsafe live surface field"):
        report_module.validate_market_outcome_source_recheck_priority_report_payload(
            {**payload, "wallet": "paper"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        report_module.validate_market_outcome_source_recheck_priority_report_payload(
            {
                **payload,
                "rows": [{**payload["rows"][0], "market_slug": "network-surface"}],
            },
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        report_module.validate_market_outcome_source_recheck_priority_report_payload(
            {**payload, "candidate_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        report_module.validate_market_outcome_source_recheck_priority_report_payload(
            {**payload, "readonly": False},
        )


def test_module_scope_is_readonly_report_only_and_external_io_free() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_outcome_source_recheck_priority_report.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "post",
        "put",
        "patch",
        "delete",
        "send",
        "write",
        "dump",
        "dumps",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
