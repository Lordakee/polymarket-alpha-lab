from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_signal_quality_gate import (
    DEFAULT_RESEARCH_SIGNAL_QUALITY_GATE_CONFIG_VERSION,
    ResearchSignalQualityGateConfig,
    ResearchSignalQualityGateReport,
    ResearchSignalQualityGateRow,
    ResearchSignalQualityInput,
    ResearchSignalQualityPublicPayloadItem,
    build_research_signal_quality_gate,
    research_signal_quality_gate_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_builds_pass_report_with_decimal_payload_strings() -> None:
    report = build_research_signal_quality_gate(
        (
            _input("item-b"),
            _input("item-a"),
        ),
        generated_at=GENERATED_AT,
        config=ResearchSignalQualityGateConfig(),
    )

    assert isinstance(report, ResearchSignalQualityGateReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_RESEARCH_SIGNAL_QUALITY_GATE_CONFIG_VERSION
    assert report.gate_status == "pass"
    assert report.queue_next_step == "research_queue_standard_review"
    assert report.item_count == Decimal("2.000000")
    assert report.pass_count == Decimal("2.000000")
    assert report.watch_count == Decimal("0.000000")
    assert report.block_count == Decimal("0.000000")
    assert report.pass_ratio == Decimal("1.000000")
    assert report.reason_codes == ("quality_gate_pass",)
    assert tuple(row.queue_item_key for row in report.rows) == ("item-a", "item-b")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = research_signal_quality_gate_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["gate_status"] == "pass"
    assert payload["item_count"] == "2.000000"
    assert payload["pass_ratio"] == "1.000000"
    assert payload["rows"][0]["composite_quality_score"] == "0.891667"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _decimal_values_are_strings(payload)


def test_watch_and_block_reports_route_to_human_research_queue() -> None:
    watch_report = build_research_signal_quality_gate(
        (
            _input(
                "item-watch",
                traceability_score=Decimal("0.700000"),
                freshness_age_hours=Decimal("30.000000"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchSignalQualityGateConfig(),
    )
    block_report = build_research_signal_quality_gate(
        (
            _input("item-pass"),
            _input("item-block", conflict_severity_score=Decimal("0.900000")),
        ),
        generated_at=GENERATED_AT,
        config=ResearchSignalQualityGateConfig(),
    )

    assert watch_report.gate_status == "watch"
    assert watch_report.queue_next_step == "research_queue_elevated_review"
    assert watch_report.watch_count == Decimal("1.000000")
    assert watch_report.rows[0].reason_codes == (
        "traceability_watch",
        "freshness_watch",
    )

    assert block_report.gate_status == "block"
    assert block_report.queue_next_step == "hold_quality_rework"
    assert block_report.block_count == Decimal("1.000000")
    assert tuple(row.gate_status for row in block_report.rows) == ("block", "pass")
    assert block_report.rows[0].reason_codes == ("conflict_block",)
    assert block_report.reason_codes == ("conflict_block", "quality_gate_pass")


def test_empty_inputs_are_report_only_block() -> None:
    report = build_research_signal_quality_gate(
        (),
        generated_at=GENERATED_AT,
        config=ResearchSignalQualityGateConfig(),
    )

    assert report.gate_status == "block"
    assert report.queue_next_step == "hold_quality_rework"
    assert report.reason_codes == ("empty_input",)
    assert report.item_count == Decimal("0.000000")
    assert report.pass_ratio is None
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="config_version"):
        ResearchSignalQualityGateConfig(config_version=_StringSubclass("version-a"))
    with pytest.raises(ValueError, match="min_traceability_score"):
        ResearchSignalQualityGateConfig(min_traceability_score=1)
    with pytest.raises(ValueError, match="min_traceability_score"):
        ResearchSignalQualityGateConfig(min_traceability_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="traceability_score"):
        _input("item-a", traceability_score="0.900000")
    with pytest.raises(ValueError, match="traceability_score"):
        _input("item-a", traceability_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="freshness_age_hours"):
        _input("item-a", freshness_age_hours=24)
    with pytest.raises(ValueError, match="gate_status"):
        ResearchSignalQualityGateRow(
            queue_item_key="item-a",
            traceability_score=Decimal("0.900000"),
            diversity_score=Decimal("0.850000"),
            freshness_age_hours=Decimal("6.000000"),
            freshness_score=Decimal("0.916667"),
            conflict_severity_score=Decimal("0.100000"),
            composite_quality_score=Decimal("0.891667"),
            gate_status="blocked",
            queue_next_step="hold_quality_rework",
            reason_codes=("quality_gate_pass",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_input("item-a"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ResearchSignalQualityGateConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        ResearchSignalQualityGateConfig(readonly=False)

    report = build_research_signal_quality_gate(
        (_input("item-a"),),
        generated_at=GENERATED_AT,
        config=ResearchSignalQualityGateConfig(),
    )
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False
    with pytest.raises(FrozenInstanceError):
        report.rows[0].gate_status = "block"


@pytest.mark.parametrize(
    ("factory_name", "field_name", "field_value"),
    (
        ("input", "queue_item_key", "candidate-abc"),
        ("input", "queue_item_key", "market-abc"),
        ("public_payload", "key", "source_ref"),
        ("public_payload", "key", "wallet"),
        ("public_payload", "value", "https://example.test/ref"),
        ("public_payload", "value", "source text copied from private notes"),
        ("public_payload", "value", "buy or sell recommendation"),
        ("public_payload", "value", "wallet auth token"),
        ("public_payload", "value", "order trade position"),
    ),
)
def test_leak_rejection_for_public_surface_values(
    factory_name: str,
    field_name: str,
    field_value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public"):
        if factory_name == "input":
            _input("item-a", **{field_name: field_value})
        else:
            values = {"key": "safe_key", "value": "safe public note"}
            values[field_name] = field_value
            ResearchSignalQualityPublicPayloadItem(**values)


def test_public_payload_does_not_expose_forbidden_surfaces() -> None:
    report = build_research_signal_quality_gate(
        (_input("item-a"),),
        generated_at=GENERATED_AT,
        config=ResearchSignalQualityGateConfig(),
        public_payload=(
            ResearchSignalQualityPublicPayloadItem(
                key="review_scope",
                value="human review only",
            ),
        ),
    )

    payload = research_signal_quality_gate_payload(report)
    rendered = repr(payload).casefold()
    for token in (
        "candidate",
        "market",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
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
        "blocked",
    ):
        assert token not in rendered

    tampered = dict(payload)
    tampered["gate_status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        research_signal_quality_gate_payload(tampered)


def test_derived_validation_digest_is_tamper_evident() -> None:
    report = build_research_signal_quality_gate(
        (_input("item-a"),),
        generated_at=GENERATED_AT,
        config=ResearchSignalQualityGateConfig(),
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="item_count"):
        replace(report, item_count=Decimal("2.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=())


def test_report_and_digest_are_deterministic() -> None:
    rows = (
        _input("item-c", conflict_severity_score=Decimal("0.900000")),
        _input("item-a"),
        _input("item-b", traceability_score=Decimal("0.700000")),
    )

    report_a = build_research_signal_quality_gate(
        rows,
        generated_at=GENERATED_AT,
        config=ResearchSignalQualityGateConfig(),
    )
    report_b = build_research_signal_quality_gate(
        tuple(reversed(rows)),
        generated_at=GENERATED_AT,
        config=ResearchSignalQualityGateConfig(),
    )

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert research_signal_quality_gate_payload(report_a) == research_signal_quality_gate_payload(
        report_b,
    )
    assert tuple(row.queue_item_key for row in report_a.rows) == (
        "item-c",
        "item-b",
        "item-a",
    )


def test_module_scope_excludes_fetch_storage_and_execution_surfaces() -> None:
    module = importlib.import_module("polymarket_alpha_lab.research_signal_quality_gate")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_SIGNAL_QUALITY_GATE_CONFIG_VERSION",
        "ResearchSignalQualityGateConfig",
        "ResearchSignalQualityGateReport",
        "ResearchSignalQualityGateRow",
        "ResearchSignalQualityInput",
        "ResearchSignalQualityPublicPayloadItem",
        "build_research_signal_quality_gate",
        "research_signal_quality_gate_payload",
    )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "subprocess",
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _input(item_key: str, **overrides: object) -> ResearchSignalQualityInput:
    values = {
        "queue_item_key": item_key,
        "traceability_score": Decimal("0.900000"),
        "diversity_score": Decimal("0.850000"),
        "freshness_age_hours": Decimal("6.000000"),
        "conflict_severity_score": Decimal("0.100000"),
    }
    values.update(overrides)
    return ResearchSignalQualityInput(**values)


def _decimal_values_are_strings(value: object) -> bool:
    if isinstance(value, Decimal):
        return False
    if isinstance(value, dict):
        return all(_decimal_values_are_strings(item) for item in value.values())
    if isinstance(value, list):
        return all(_decimal_values_are_strings(item) for item in value)
    return True
