from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_candidate_monitoring_summary import (
    DEFAULT_RESEARCH_CANDIDATE_MONITORING_SUMMARY_CONFIG_VERSION,
    ResearchCandidateMonitoringSummaryConfig,
    ResearchCandidateMonitoringSummaryInput,
    ResearchCandidateMonitoringSummaryReport,
    ResearchCandidateMonitoringSummaryRow,
    build_research_candidate_monitoring_summary,
    build_research_candidate_monitoring_summary_from_public_payloads,
    research_candidate_monitoring_summary_payload,
    validate_research_candidate_monitoring_summary_public_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_candidate_monitoring_summary.py"
)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market question",
    "question",
    "source_ref",
    "source_reference",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "://",
    "url",
    "URL",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "recommend",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(
    monitoring_surface: str,
    public_status: str = "pass",
    *,
    input_count: Decimal = d("2.000000"),
    watch_count: Decimal = d("0.000000"),
    block_count: Decimal = d("0.000000"),
    attention_score: Decimal = d("0.250000"),
    trigger_count: Decimal = d("1.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchCandidateMonitoringSummaryInput:
    return ResearchCandidateMonitoringSummaryInput(
        monitoring_surface=monitoring_surface,
        public_status=public_status,
        input_count=input_count,
        watch_count=watch_count,
        block_count=block_count,
        attention_score=attention_score,
        trigger_count=trigger_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _build(
    *inputs: ResearchCandidateMonitoringSummaryInput,
    config: ResearchCandidateMonitoringSummaryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchCandidateMonitoringSummaryReport:
    return build_research_candidate_monitoring_summary(
        inputs,
        generated_at=generated_at,
        config=config or ResearchCandidateMonitoringSummaryConfig(),
    )


def _assert_payload_has_no_raw_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        pytest.fail(f"public payload leaked raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            _assert_payload_has_no_raw_numbers(item)
    elif type(value) is list:
        for item in value:
            _assert_payload_has_no_raw_numbers(item)


def _assert_payload_has_no_forbidden_text(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True)
    rendered_casefold = rendered.casefold()
    for forbidden in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert forbidden.casefold() not in rendered_casefold


def test_builds_pass_watch_block_monitoring_summary_from_desensitized_inputs() -> None:
    report = _build(
        _input("snapshot_summary", "pass", attention_score=d("0.250000")),
        _input(
            "resolution_watch",
            "watch",
            input_count=d("3.000000"),
            watch_count=d("1.000000"),
            attention_score=d("0.550000"),
            trigger_count=d("4.000000"),
        ),
        _input(
            "alert_queue",
            "block",
            block_count=d("1.000000"),
            attention_score=d("0.900000"),
            trigger_count=d("2.000000"),
        ),
        _input(
            "pipeline_health",
            "pass",
            input_count=d("3.000000"),
            attention_score=d("0.200000"),
        ),
    )

    assert type(report) is ResearchCandidateMonitoringSummaryReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_RESEARCH_CANDIDATE_MONITORING_SUMMARY_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.surface_count == d("4.000000")
    assert report.pass_surface_count == d("2.000000")
    assert report.watch_surface_count == d("1.000000")
    assert report.block_surface_count == d("1.000000")
    assert report.total_input_count == d("10.000000")
    assert report.total_watch_count == d("1.000000")
    assert report.total_block_count == d("1.000000")
    assert report.total_trigger_count == d("8.000000")
    assert report.max_attention_score == d("0.900000")
    assert report.average_attention_score == d("0.475000")
    assert report.reason_codes == (
        "monitoring_block_present",
        "monitoring_watch_present",
        "alert_queue_block",
        "resolution_watch_watch",
    )
    assert tuple(row.monitoring_surface for row in report.rows) == (
        "alert_queue",
        "resolution_watch",
        "snapshot_summary",
        "pipeline_health",
    )
    assert tuple(row.surface_ref for row in report.rows) == (
        "redacted-monitoring-surface-000001",
        "redacted-monitoring-surface-000002",
        "redacted-monitoring-surface-000003",
        "redacted-monitoring-surface-000004",
    )
    assert tuple(row.public_status for row in report.rows) == (
        "block",
        "watch",
        "pass",
        "pass",
    )
    assert report.rows[0].monitoring_priority_score == d("1.000000")
    assert report.rows[0].next_human_action == "manual_rework_required"
    assert report.rows[1].monitoring_priority_score == d("0.725000")
    assert report.rows[1].next_human_action == "monitor_before_use"
    assert report.rows[2].reason_codes == ("snapshot_summary_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = research_candidate_monitoring_summary_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["status"] == "block"
    assert payload["total_input_count"] == "10.000000"
    assert payload["average_attention_score"] == "0.475000"
    assert payload["rows"][0]["surface_ref"] == "redacted-monitoring-surface-000001"
    assert payload["rows"][0]["monitoring_priority_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_text(payload)
    assert validate_research_candidate_monitoring_summary_public_payload(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_builds_from_existing_desensitized_public_payload_shapes() -> None:
    report = build_research_candidate_monitoring_summary_from_public_payloads(
        candidate_snapshot_payload={
            "public_status": "pass",
            "snapshot_count": "2.000000",
            "watch_count": "0.000000",
            "block_count": "0.000000",
            "max_screening_priority_score": "0.250000",
            "reason_codes": ["snapshot_pass"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        resolution_watch_payload={
            "status": "watch",
            "item_count": "3.000000",
            "watch_count": "1.000000",
            "block_count": "0.000000",
            "max_combined_watch_score": "0.550000",
            "reason_codes": ["resolution_watch_queue_watch_present"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        alert_queue_payload={
            "queue_status": "block",
            "input_count": "2.000000",
            "watch_count": "0.000000",
            "block_count": "1.000000",
            "highest_priority_score": "0.900000",
            "reason_codes": ["alert_block_present", "rule_risk_blocking"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        source_pipeline_health_payload={
            "status": "pass",
            "input_count": "3.000000",
            "watch_count": "0.000000",
            "block_count": "0.000000",
            "attention_ratio": "0.200000",
            "reason_codes": ["pipeline_health_pass"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        generated_at=GENERATED_AT,
    )

    assert report.status == "block"
    assert report.total_input_count == d("10.000000")
    assert tuple(row.monitoring_surface for row in report.rows) == (
        "alert_queue",
        "resolution_watch",
        "snapshot_summary",
        "pipeline_health",
    )
    payload = research_candidate_monitoring_summary_payload(report)
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_text(payload)


def test_empty_or_missing_surfaces_block_manual_monitoring() -> None:
    report = _build()

    assert report.status == "block"
    assert report.reason_codes == (
        "monitoring_block_present",
        "monitoring_surface_missing",
    )
    assert report.rows == ()
    assert report.surface_count == d("0.000000")
    assert report.total_input_count == d("0.000000")

    with pytest.raises(ValueError, match="required monitoring surfaces"):
        _build(_input("snapshot_summary"))
    with pytest.raises(ValueError, match="duplicate monitoring_surface"):
        _build(
            _input("snapshot_summary"),
            _input("snapshot_summary", "watch", watch_count=d("1.000000")),
            _input("resolution_watch"),
            _input("alert_queue"),
            _input("pipeline_health"),
        )


def test_frozen_dataclasses_strict_decimal_types_datetime_and_flags() -> None:
    report = _build(
        _input("snapshot_summary"),
        _input("resolution_watch"),
        _input("alert_queue"),
        _input("pipeline_health"),
    )

    for cls in (
        ResearchCandidateMonitoringSummaryConfig,
        ResearchCandidateMonitoringSummaryInput,
        ResearchCandidateMonitoringSummaryRow,
        ResearchCandidateMonitoringSummaryReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].public_status = "block"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type("DerivedMonitoringInput", (ResearchCandidateMonitoringSummaryInput,), {})
    with pytest.raises(ValueError, match="attention_score"):
        _input("snapshot_summary", attention_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_count"):
        _input("snapshot_summary", watch_count=0.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_count"):
        _input("snapshot_summary", block_count=_DecimalSubclass("0.000000"))
    with pytest.raises(ValueError, match="trigger_count"):
        _input("snapshot_summary", trigger_count=d("1.100000"))
    with pytest.raises(ValueError, match="monitoring_surface"):
        _input("market_slug")
    with pytest.raises(ValueError, match="public_status"):
        _input("snapshot_summary", "ready")
    with pytest.raises(ValueError, match="paper_only"):
        _input("snapshot_summary", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchCandidateMonitoringSummaryConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        _build(
            _input("snapshot_summary"),
            _input("resolution_watch"),
            _input("alert_queue"),
            _input("pipeline_health"),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _build(
            _input("snapshot_summary"),
            _input("resolution_watch"),
            _input("alert_queue"),
            _input("pipeline_health"),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )


def test_public_payload_rejects_sensitive_surfaces_raw_numbers_and_digest_tampering() -> None:
    report = _build(
        _input("snapshot_summary"),
        _input("resolution_watch"),
        _input("alert_queue"),
        _input("pipeline_health"),
    )
    payload = research_candidate_monitoring_summary_payload(report)

    for unsafe_key, unsafe_value in (
        ("raw_candidate_id", "abc"),
        ("market_id", "hidden"),
        ("market_slug", "hidden"),
        ("market_question", "Will this resolve?"),
        ("source_ref", "hidden"),
        ("source_url", "https://example.test/ref"),
        ("source_text", "copied private evidence"),
        ("URL", "https://example.test/ref"),
        ("dsn", "postgres://user:pass@host/db"),
        ("table", "private_table"),
        ("token", "secret-token"),
        ("wallet", "0xabc"),
        ("auth", "bearer"),
        ("order", "place order"),
        ("trade", "trade language"),
        ("position", "position language"),
        ("value", "buy sell recommendation"),
    ):
        tampered = dict(payload)
        tampered[unsafe_key] = unsafe_value
        with pytest.raises(ValueError, match="unsafe public"):
            research_candidate_monitoring_summary_payload(tampered)

    tampered_number = dict(payload)
    tampered_number["total_input_count"] = 4
    with pytest.raises(ValueError, match="Decimal-derived string"):
        research_candidate_monitoring_summary_payload(tampered_number)

    tampered_digest = dict(payload)
    tampered_digest["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_candidate_monitoring_summary_payload(tampered_digest)

    source_payload = {
        "public_status": "pass",
        "snapshot_count": "1.000000",
        "watch_count": "0.000000",
        "block_count": "0.000000",
        "max_screening_priority_score": "0.100000",
        "reason_codes": ["snapshot_pass"],
        "market_id": "private-market",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    with pytest.raises(ValueError, match="unsafe public"):
        build_research_candidate_monitoring_summary_from_public_payloads(
            candidate_snapshot_payload=source_payload,
            resolution_watch_payload={},
            alert_queue_payload={},
            source_pipeline_health_payload={},
            generated_at=GENERATED_AT,
        )


def test_module_is_pure_research_without_io_or_trading_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    banned_import_roots = {
        "httpx",
        "requests",
        "socket",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
    }
    banned_call_names = {
        "connect",
        "execute",
        "open",
        "post",
        "put",
        "request",
        "send",
        "trade",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in banned_call_names
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in banned_call_names
