from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_evidence_update_cadence_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_evidence_update_cadence_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def sample(
    group: str,
    *,
    latest_update_age_minutes: int = 15,
    previous_update_age_minutes: int = 45,
    source_count: str = "4.000000",
    stale_source_count: str = "0.000000",
    checked_claim_count: str = "4.000000",
    contradiction_count: str = "0.000000",
    resolution_rule_count: str = "4.000000",
    resolution_rule_covered_count: str = "4.000000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventEvidenceUpdateCadenceSample(
        cadence_group=group,
        previous_update_at=GENERATED_AT
        - timedelta(minutes=previous_update_age_minutes),
        latest_update_at=GENERATED_AT - timedelta(minutes=latest_update_age_minutes),
        source_count=d(source_count),
        stale_source_count=d(stale_source_count),
        checked_claim_count=d(checked_claim_count),
        contradiction_count=d(contradiction_count),
        resolution_rule_count=d(resolution_rule_count),
        resolution_rule_covered_count=d(resolution_rule_covered_count),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*samples: object, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_event_evidence_update_cadence_report(
        samples,
        generated_at=generated_at,
    )


def assert_no_json_numbers(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_json_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_json_numbers(item)


def assert_no_raw_public_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "candidate",
        "condition_id",
        "dsn",
        "market_id",
        "market_slug",
        "question",
        "raw",
        "recommendation",
        "sizing",
        "slug",
        "source_id",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
        "order",
    )
    forbidden_value_fragments = (
        "://",
        "candidate",
        "condition",
        "dsn",
        "market",
        "question",
        "raw",
        "recommend",
        "sizing",
        "slug",
        "table",
        "token",
        "trade",
        "wallet",
        "order",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_raw_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_raw_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def test_event_evidence_update_cadence_aggregates_pass_watch_and_block() -> None:
    report = build_report(
        sample("safe-c", latest_update_age_minutes=15, previous_update_age_minutes=45),
        sample(
            "safe-a",
            latest_update_age_minutes=30,
            previous_update_age_minutes=120,
            stale_source_count="1.000000",
            contradiction_count="1.000000",
            resolution_rule_covered_count="3.000000",
        ),
        sample(
            "safe-b",
            latest_update_age_minutes=240,
            previous_update_age_minutes=600,
            stale_source_count="3.000000",
            contradiction_count="3.000000",
            resolution_rule_covered_count="1.000000",
        ),
    )

    assert report.status == "block"
    assert report.update_group_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.mean_update_interval_seconds == d("9600.000000")
    assert report.max_update_interval_seconds == d("21600.000000")
    assert report.max_latest_update_age_seconds == d("14400.000000")
    assert report.source_count == d("12.000000")
    assert report.stale_source_count == d("4.000000")
    assert report.stale_source_pressure_ratio == d("0.333333")
    assert report.checked_claim_count == d("12.000000")
    assert report.contradiction_count == d("4.000000")
    assert report.contradiction_pressure_ratio == d("0.333333")
    assert report.resolution_rule_count == d("12.000000")
    assert report.resolution_rule_covered_count == d("8.000000")
    assert report.resolution_rule_coverage_ratio == d("0.666667")

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.aggregate_public_label == "cadence-group-002"
    assert block_row.update_interval_seconds == d("21600.000000")
    assert block_row.latest_update_age_seconds == d("14400.000000")
    assert block_row.stale_source_pressure_ratio == d("0.750000")
    assert block_row.contradiction_pressure_ratio == d("0.750000")
    assert block_row.resolution_rule_coverage_ratio == d("0.250000")
    assert block_row.reason_codes == (
        "update_interval_block",
        "latest_update_age_block",
        "stale_source_pressure_block",
        "contradiction_pressure_block",
        "resolution_rule_coverage_block",
    )
    assert watch_row.aggregate_public_label == "cadence-group-001"
    assert watch_row.reason_codes == (
        "update_interval_watch",
        "latest_update_age_pass",
        "stale_source_pressure_watch",
        "contradiction_pressure_watch",
        "resolution_rule_coverage_watch",
    )
    assert pass_row.aggregate_public_label == "cadence-group-003"
    assert pass_row.reason_codes == (
        "update_interval_pass",
        "latest_update_age_pass",
        "stale_source_pressure_pass",
        "contradiction_pressure_pass",
        "resolution_rule_coverage_pass",
    )


def test_public_payload_is_deterministic_digest_backed_and_redacted() -> None:
    module = api()
    first = build_report(
        sample("safe-c"),
        sample(
            "safe-a",
            latest_update_age_minutes=30,
            previous_update_age_minutes=120,
            stale_source_count="1.000000",
            contradiction_count="1.000000",
            resolution_rule_covered_count="3.000000",
        ),
        sample(
            "safe-b",
            latest_update_age_minutes=240,
            previous_update_age_minutes=600,
            stale_source_count="3.000000",
            contradiction_count="3.000000",
            resolution_rule_covered_count="1.000000",
        ),
    )
    second = build_report(
        sample(
            "safe-b",
            latest_update_age_minutes=240,
            previous_update_age_minutes=600,
            stale_source_count="3.000000",
            contradiction_count="3.000000",
            resolution_rule_covered_count="1.000000",
        ),
        sample("safe-c"),
        sample(
            "safe-a",
            latest_update_age_minutes=30,
            previous_update_age_minutes=120,
            stale_source_count="1.000000",
            contradiction_count="1.000000",
            resolution_rule_covered_count="3.000000",
        ),
    )

    payload = module.research_event_evidence_update_cadence_report_payload(first)
    repeat_payload = module.research_event_evidence_update_cadence_report_payload(second)
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload == repeat_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.research_event_evidence_update_cadence_report_digest(first) == (
        first.derived_validation_digest
    )
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)
    assert module.validate_research_event_evidence_update_cadence_report_payload(payload)
    assert_no_json_numbers(payload)
    assert_no_raw_public_surface(payload)
    assert "safe-a" not in encoded
    assert "safe-b" not in encoded
    assert "safe-c" not in encoded

    tampered = dict(payload)
    tampered["status"] = "pass"
    assert not module.validate_research_event_evidence_update_cadence_report_payload(
        tampered,
    )

    numeric = dict(payload)
    numeric["update_group_count"] = 3
    assert not module.validate_research_event_evidence_update_cadence_report_payload(
        numeric,
    )

    unsafe = dict(payload)
    unsafe["source_" + "url"] = "https://example.invalid/raw"
    unsafe["derived_validation_digest"] = first.derived_validation_digest
    assert not module.validate_research_event_evidence_update_cadence_report_payload(
        unsafe,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, update_group_count=d("4.000000"))


def test_frozen_decimal_only_validation_and_empty_report_safety() -> None:
    module = api()
    report = build_report(sample("validation-safe"))
    empty = build_report()

    assert empty.status == "block"
    assert empty.update_group_count == d("0.000000")
    assert empty.reason_codes == ("event_evidence_update_cadence_no_inputs",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    records = (
        module.ResearchEventEvidenceUpdateCadenceConfig(),
        sample("record-safe"),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    for record in records:
        assert is_dataclass(record)
        assert record.__dataclass_params__.frozen is True
        assert record.paper_only is True
        assert record.report_only is True
        assert record.readonly is True
        for field in fields(record):
            value = getattr(record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name
        with pytest.raises(FrozenInstanceError):
            record.paper_only = False  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(module.ResearchEventEvidenceUpdateCadenceReport):
            pass

    with pytest.raises(ValueError, match="source_count must be exactly Decimal"):
        module.ResearchEventEvidenceUpdateCadenceSample(
            cadence_group="bad-decimal",
            previous_update_at=GENERATED_AT - timedelta(minutes=10),
            latest_update_at=GENERATED_AT - timedelta(minutes=5),
            source_count=1,  # type: ignore[arg-type]
            stale_source_count=d("0.000000"),
            checked_claim_count=d("1.000000"),
            contradiction_count=d("0.000000"),
            resolution_rule_count=d("1.000000"),
            resolution_rule_covered_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="stale_source_count must be exactly Decimal"):
        replace(sample("bad-subclass"), stale_source_count=_DecimalSubclass("0.000000"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            sample("bad-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="latest_update_at"):
        sample(
            "bad-chronology",
            latest_update_age_minutes=60,
            previous_update_age_minutes=30,
        )
    with pytest.raises(ValueError, match="cadence_group"):
        sample("market_" + "slug")
    with pytest.raises(ValueError, match="report_only"):
        sample("bad-flag", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="halt")


def test_module_exposes_no_side_effect_or_live_trading_surfaces() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)

    forbidden_imports = {
        "aiohttp",
        "httpx",
        "psycopg",
        "py_clob_client",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "post",
        "put",
        "request",
        "send",
    }
    forbidden_public_names = {
        "auth",
        "client",
        "database",
        "dsn",
        "live",
        "order",
        "recommendation",
        "sizing",
        "table",
        "token",
        "trade",
        "wallet",
    }

    assert imported_roots.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert set(dir(module)).isdisjoint(forbidden_public_names)
