from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_resolution_monitoring_backlog_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "evidence_age_watch_seconds": d("3600.000000"),
        "evidence_age_block_seconds": d("7200.000000"),
        "oracle_lag_watch_seconds": d("1800.000000"),
        "oracle_lag_block_seconds": d("3600.000000"),
        "deadline_watch_ratio": d("0.500000"),
        "deadline_block_ratio": d("0.850000"),
        "reliability_watch_floor": d("0.800000"),
        "reliability_block_floor": d("0.600000"),
        "contradiction_watch_ratio": d("0.500000"),
        "contradiction_block_ratio": d("0.750000"),
        "capacity_watch_ratio": d("0.750000"),
        "capacity_block_ratio": d("0.400000"),
        "evidence_age_weight": d("0.200000"),
        "deadline_weight": d("0.200000"),
        "oracle_lag_weight": d("0.200000"),
        "reliability_gap_weight": d("0.150000"),
        "contradiction_weight": d("0.150000"),
        "capacity_gap_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchResolutionMonitoringBacklogPriorityConfig(**values)


def input_row(
    public_backlog_key: str,
    *,
    monitoring_item_count: Decimal = d("1.000000"),
    aggregate_evidence_age_seconds: Decimal = d("900.000000"),
    deadline_proximity: Decimal = d("0.100000"),
    oracle_lag_seconds: Decimal = d("300.000000"),
    source_reliability_score: Decimal = d("0.950000"),
    contradiction_pressure: Decimal = d("0.050000"),
    available_team_capacity_units: Decimal = d("4.000000"),
    required_team_capacity_units: Decimal = d("4.000000"),
    reason_codes: tuple[str, ...] = (),
) -> Any:
    module = api()
    return module.ResearchResolutionMonitoringBacklogPriorityInput(
        public_backlog_key=public_backlog_key,
        monitoring_item_count=monitoring_item_count,
        aggregate_evidence_age_seconds=aggregate_evidence_age_seconds,
        deadline_proximity=deadline_proximity,
        oracle_lag_seconds=oracle_lag_seconds,
        source_reliability_score=source_reliability_score,
        contradiction_pressure=contradiction_pressure,
        available_team_capacity_units=available_team_capacity_units,
        required_team_capacity_units=required_team_capacity_units,
        reason_codes=reason_codes,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_resolution_monitoring_backlog_priority_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk_payload_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk_payload_values(child))
    return (value,)


def assert_public_safe_payload(value: object) -> None:
    forbidden_key_fragments = (
        "event_id",
        "market_id",
        "market_slug",
        "condition_id",
        "source_id",
        "source_ref",
        "source_reference",
        "source_url",
        "raw_",
    )
    forbidden_value_fragments = (
        "http://",
        "https://",
        "event-",
        "market-",
        "source-",
        "condition-",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            assert not any(fragment in key.lower() for fragment in forbidden_key_fragments)
            assert_public_safe_payload(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_safe_payload(item)
    else:
        assert type(value) is not float
        assert type(value) is not int
        if isinstance(value, str):
            lowered = value.lower()
            assert not any(fragment in lowered for fragment in forbidden_value_fragments)


def test_empty_backlog_builds_pass_report_only_digest() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchResolutionMonitoringBacklogPriorityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.backlog_item_count == d("0.000000")
    assert report.monitoring_item_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.priority_rows == ()
    assert report.reason_codes == (
        "research_resolution_monitoring_backlog_priority_no_items",
    )
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_backlog_priority_uses_age_deadline_oracle_reliability_contradiction_capacity() -> None:
    report = build_report(
        input_row("bucket-a"),
        input_row(
            "bucket-c",
            monitoring_item_count=d("5.000000"),
            aggregate_evidence_age_seconds=d("9000.000000"),
            deadline_proximity=d("0.900000"),
            oracle_lag_seconds=d("4000.000000"),
            source_reliability_score=d("0.500000"),
            contradiction_pressure=d("0.800000"),
            available_team_capacity_units=d("3.000000"),
            required_team_capacity_units=d("10.000000"),
            reason_codes=("manual_review_needed",),
        ),
        input_row(
            "bucket-b",
            monitoring_item_count=d("2.000000"),
            aggregate_evidence_age_seconds=d("4500.000000"),
            deadline_proximity=d("0.400000"),
            oracle_lag_seconds=d("1200.000000"),
            source_reliability_score=d("0.750000"),
            contradiction_pressure=d("0.300000"),
            available_team_capacity_units=d("6.000000"),
            required_team_capacity_units=d("10.000000"),
        ),
    )

    assert tuple(row.public_backlog_key for row in report.priority_rows) == (
        "bucket-c",
        "bucket-b",
        "bucket-a",
    )
    assert tuple(row.status for row in report.priority_rows) == (
        "block",
        "watch",
        "pass",
    )
    block_row, watch_row, pass_row = report.priority_rows
    assert block_row.aggregate_evidence_age_pressure == d("1.000000")
    assert block_row.oracle_lag_pressure == d("1.000000")
    assert block_row.source_reliability_gap == d("0.500000")
    assert block_row.team_capacity_ratio == d("0.300000")
    assert block_row.team_capacity_gap == d("0.700000")
    assert block_row.priority_score == d("0.845000")
    assert "input_manual_review_needed" in block_row.reason_codes
    assert watch_row.aggregate_evidence_age_pressure == d("0.625000")
    assert watch_row.oracle_lag_pressure == d("0.333333")
    assert watch_row.team_capacity_ratio == d("0.600000")
    assert watch_row.priority_score == d("0.394167")
    assert pass_row.priority_score == d("0.076667")
    assert report.status == "block"
    assert report.backlog_item_count == d("3.000000")
    assert report.monitoring_item_count == d("8.000000")
    assert report.block_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.average_priority_score == d("0.438611")
    assert report.max_aggregate_evidence_age_seconds == d("9000.000000")
    assert report.max_oracle_lag_seconds == d("4000.000000")


def test_payload_is_deterministic_public_safe_and_decimal_stringed() -> None:
    module = api()
    rows = (
        input_row(
            "bucket-b",
            monitoring_item_count=d("2.000000"),
            aggregate_evidence_age_seconds=d("4500.000000"),
            deadline_proximity=d("0.400000"),
            oracle_lag_seconds=d("1200.000000"),
            source_reliability_score=d("0.750000"),
            contradiction_pressure=d("0.300000"),
            available_team_capacity_units=d("6.000000"),
            required_team_capacity_units=d("10.000000"),
        ),
        input_row("bucket-a"),
    )

    payload = module.research_resolution_monitoring_backlog_priority_report_payload(
        build_report(*rows),
    )
    reversed_payload = module.research_resolution_monitoring_backlog_priority_report_payload(
        build_report(*reversed(rows)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["priority_rows"][0]["priority_score"] == "0.394167"
    assert payload["priority_rows"][0]["monitoring_item_count"] == "2.000000"
    assert not any(type(value) in (float, int) for value in walk_payload_values(payload))
    assert json.dumps(payload, sort_keys=True)
    assert_public_safe_payload(payload)


def test_validation_enforces_decimal_only_flags_statuses_and_public_keys() -> None:
    module = api()
    assert module.STATUSES == ("pass", "watch", "block")

    with pytest.raises(ValueError, match="evidence_age_watch_seconds must be a Decimal"):
        config(evidence_age_watch_seconds=3600)
    with pytest.raises(ValueError, match="deadline_weight must be a Decimal"):
        config(deadline_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="evidence_age_block_seconds"):
        config(evidence_age_block_seconds=d("3000.000000"))
    with pytest.raises(ValueError, match="weights must sum to 1"):
        config(capacity_gap_weight=d("0.200000"))
    with pytest.raises(ValueError, match="monitoring_item_count must be a Decimal"):
        input_row("bucket-a", monitoring_item_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        input_row("bucket-a", source_reliability_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_backlog_key"):
        input_row("event-alpha")
    with pytest.raises(ValueError, match="public_backlog_key"):
        input_row("market-alpha")
    with pytest.raises(ValueError, match="public_backlog_key"):
        input_row("source-alpha")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_resolution_monitoring_backlog_priority_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_resolution_monitoring_backlog_priority_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchResolutionMonitoringBacklogPriorityInput(
            public_backlog_key="bucket-a",
            monitoring_item_count=d("1.000000"),
            aggregate_evidence_age_seconds=d("900.000000"),
            deadline_proximity=d("0.100000"),
            oracle_lag_seconds=d("300.000000"),
            source_reliability_score=d("0.950000"),
            contradiction_pressure=d("0.050000"),
            available_team_capacity_units=d("4.000000"),
            required_team_capacity_units=d("4.000000"),
            paper_only=False,
        )


def test_public_dataclasses_are_frozen() -> None:
    report = build_report(input_row("bucket-a"))

    assert is_dataclass(config())
    assert is_dataclass(input_row("bucket-a"))
    assert is_dataclass(report.priority_rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.priority_rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().deadline_weight = d("0.300000")


def test_module_scope_is_pure_report_only_without_execution_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
        "source_id",
        "market_id",
        "event_id",
        "condition_id",
        "market_slug",
        "source_url",
        "source_ref",
        "source_reference",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "db",
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
