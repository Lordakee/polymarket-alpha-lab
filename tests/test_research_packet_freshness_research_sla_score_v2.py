from __future__ import annotations

import ast
import importlib
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_packet_freshness_research_sla_score_v2.py"
)
GENERATED_AT = datetime(2026, 1, 15, 16, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_freshness_research_sla_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {}
    values.update(overrides)
    return module.ResearchPacketFreshnessResearchSlaScoreV2Config(**values)


def source(
    source_id: str = "source-alpha",
    *,
    packet_id: str = "packet-alpha",
    research_topic_id: str = "election-resolution",
    source_priority: str = "standard",
    source_label: str = "public-evidence-alpha",
    age_seconds: int = 3600,
    last_researched_at: datetime | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchPacketFreshnessResearchSlaScoreV2Source(
        packet_id=packet_id,
        source_id=source_id,
        research_topic_id=research_topic_id,
        source_priority=source_priority,
        source_label=source_label,
        last_researched_at=(
            GENERATED_AT - timedelta(seconds=age_seconds)
            if last_researched_at is None
            else last_researched_at
        ),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*sources: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_packet_freshness_research_sla_score_v2_report(
        sources,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"public numeric scalar must be serialized as a string: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_numeric_scalars(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            assert_no_public_numeric_scalars(child)


def test_scores_research_sla_freshness_and_overdue_source_penalties() -> None:
    module = api()
    report = build_report(
        source("source-fresh", age_seconds=3600),
        source("source-overdue", age_seconds=90000),
        source(
            "source-critical",
            source_priority="critical",
            source_label="public-evidence-critical",
            age_seconds=25200,
        ),
    )

    assert is_dataclass(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.source_count == d("3")
    assert report.overdue_source_count == d("2")
    assert report.priority_escalated_count == d("1")
    assert report.blocked_count == d("1")
    assert report.watch_count == d("1")
    assert report.pass_count == d("1")
    assert report.average_freshness_sla_score == d("0.328473")
    assert report.highest_freshness_sla_score == d("0.608334")
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        module.REPORT_BLOCKED_REASON,
        module.OVERDUE_SOURCE_REASON,
        module.FRESHNESS_PENALTY_REASON,
        module.PRIORITY_ESCALATED_REASON,
    )

    critical, overdue, fresh = report.source_rows
    assert critical.source_id == "source-critical"
    assert critical.research_sla_seconds == d("21600.000000")
    assert critical.seconds_over_sla == d("3600.000000")
    assert critical.overdue_ratio == d("0.166667")
    assert critical.freshness_penalty_score == d("0.458334")
    assert critical.priority_escalation_score == d("0.150000")
    assert critical.freshness_sla_score == d("0.608334")
    assert critical.row_status == "blocked"
    assert critical.reason_codes == (
        module.OVERDUE_SOURCE_REASON,
        module.FRESHNESS_PENALTY_REASON,
        module.PRIORITY_ESCALATED_REASON,
    )

    assert overdue.source_id == "source-overdue"
    assert overdue.research_sla_seconds == d("86400.000000")
    assert overdue.seconds_over_sla == d("3600.000000")
    assert overdue.overdue_ratio == d("0.041667")
    assert overdue.freshness_sla_score == d("0.377084")
    assert overdue.row_status == "watch"

    assert fresh.source_id == "source-fresh"
    assert fresh.freshness_sla_score == d("0.000000")
    assert fresh.row_status == "pass"
    assert fresh.reason_codes == (module.FRESH_SOURCE_REASON,)


def test_priority_escalation_blocks_critical_overdue_source() -> None:
    module = api()
    report = build_report(
        source(
            "source-critical",
            source_priority="critical",
            age_seconds=25200,
        ),
    )

    row = report.source_rows[0]
    assert row.priority_escalation_score == d("0.150000")
    assert row.row_status == "blocked"
    assert report.priority_escalated_count == d("1")
    assert module.PRIORITY_ESCALATED_REASON in row.reason_codes
    assert module.PRIORITY_ESCALATED_REASON in report.reason_codes


def test_serialization_decimal_strings_flags_and_digest_tamper_rejection() -> None:
    module = api()
    report = build_report(
        source("source-overdue", age_seconds=90000),
        source(
            "source-critical",
            source_priority="critical",
            source_label="public-evidence-critical",
            age_seconds=25200,
        ),
    )

    payload = module.research_packet_freshness_research_sla_score_v2_payload(report)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["source_count"] == "2"
    assert payload["average_freshness_sla_score"] == "0.492709"
    assert payload["source_rows"][0]["freshness_sla_score"] == "0.608334"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert module.validate_research_packet_freshness_research_sla_score_v2_public_payload(
        payload,
    )
    assert_no_public_numeric_scalars(payload)

    row_tampered = deepcopy(payload)
    row_tampered["source_rows"][0]["freshness_sla_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_packet_freshness_research_sla_score_v2_public_payload(
            row_tampered,
        )

    report_tampered = deepcopy(payload)
    report_tampered["average_freshness_sla_score"] = "0.000001"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_packet_freshness_research_sla_score_v2_public_payload(
            report_tampered,
        )

    missing_digest = deepcopy(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_packet_freshness_research_sla_score_v2_public_payload(
            missing_digest,
        )


def test_frozen_dataclasses_exact_decimal_public_values_and_hard_flags() -> None:
    module = api()
    cfg = config()
    item = source()
    report = build_report(item)
    row = report.source_rows[0]

    for value in (cfg, item, row, report):
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name.endswith("_seconds") or field.name.endswith("_score") or field.name in {
                "source_count",
                "overdue_source_count",
                "priority_escalated_count",
                "blocked_count",
                "watch_count",
                "pass_count",
                "overdue_ratio",
                "average_freshness_sla_score",
                "highest_freshness_sla_score",
            }:
                assert type(field_value) is Decimal

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="standard_research_sla_seconds must be a Decimal"):
        config(standard_research_sla_seconds=86400)
    with pytest.raises(ValueError, match="watch_score_threshold must be a Decimal"):
        config(watch_score_threshold=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="last_researched_at must be a datetime"):
        source(last_researched_at=_DatetimeSubclass(2026, 1, 15, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only must be True"):
        source(paper_only=False)

    tampered_config = config()
    object.__setattr__(tampered_config, "readonly", False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(source(), cfg=tampered_config)


def test_public_payload_rejects_unsafe_keys_values_and_module_has_no_unsafe_surface() -> None:
    module = api()
    payload = module.research_packet_freshness_research_sla_score_v2_payload(
        build_report(source("source-overdue", age_seconds=90000)),
    )

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        unsafe_key_payload = deepcopy(payload)
        unsafe_key_payload[f"{term}_surface"] = "blocked"
        with pytest.raises(ValueError, match="unsafe public"):
            module.validate_research_packet_freshness_research_sla_score_v2_public_payload(
                unsafe_key_payload,
            )

        unsafe_value_payload = deepcopy(payload)
        unsafe_value_payload["source_rows"][0]["source_label"] = (
            f"contains {term} surface"
        )
        with pytest.raises(ValueError, match="unsafe public"):
            module.validate_research_packet_freshness_research_sla_score_v2_public_payload(
                unsafe_value_payload,
            )

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "order",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
