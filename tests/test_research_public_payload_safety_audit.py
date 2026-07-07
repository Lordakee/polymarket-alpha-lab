from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_public_payload_safety_audit import (
    PublicPayloadSafetyFinding,
    PublicPayloadSafetyReport,
    audit_research_public_payload,
    research_public_payload_safety_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
MODULE_PATH = Path("src/polymarket_alpha_lab/research_public_payload_safety_audit.py")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


@dataclass(frozen=True)
class PublicResearchReportShape:
    report_id: str
    summary: str
    confidence_score: Decimal | None
    public_payload: dict[str, object]
    rows: tuple[dict[str, object], ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def safe_report(**overrides: object) -> PublicResearchReportShape:
    values: dict[str, object] = {
        "report_id": "public_research_report",
        "summary": "Public research summary for review queue.",
        "confidence_score": d("0.800000"),
        "public_payload": {
            "claim_key": "public_claim_key",
            "status": "watch",
            "confidence_score": d("0.800000"),
        },
        "rows": (
            {
                "claim_key": "public_claim_key",
                "public_note": "Requires human review before publication.",
            },
        ),
    }
    values.update(overrides)
    return PublicResearchReportShape(**values)


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def test_safe_research_payload_passes_with_deterministic_decimal_report() -> None:
    report = audit_research_public_payload(
        safe_report(),
        generated_at=GENERATED_AT,
        report_name="source_quality_public_report",
    )
    payload = research_public_payload_safety_report_payload(report)
    json.dumps(payload, sort_keys=True)

    assert type(report) is PublicPayloadSafetyReport
    assert report.generated_at == GENERATED_AT
    assert report.report_name == "source_quality_public_report"
    assert report.audit_status == "pass"
    assert report.next_step == "publish_report_only_research_payload"
    assert report.finding_count == d("0")
    assert report.watch_finding_count == d("0")
    assert report.block_finding_count == d("0")
    assert report.score == d("1.000000")
    assert report.findings == ()
    assert report.reason_codes == (
        "research_public_payload_safety_audit_pass",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert payload["score"] == "1.000000"
    assert not any(isinstance(value, float) for value in walk_values(payload))


def test_blocking_identifiers_sources_secrets_and_trading_language_are_flagged() -> None:
    report = audit_research_public_payload(
        {
            "candidate_id": "cand_abc_123_raw",
            "market": {"market_id": "0xabc123", "slug": "will-team-win"},
            "question": "Will Team win?",
            "source_url": "https://example.invalid/private?token=hidden",
            "source_text": "raw document says wallet auth token and dsn table are exposed",
            "trade_note": "Buy 100 shares and size the position at 5%.",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        generated_at=GENERATED_AT,
        report_name="unsafe_public_payload",
    )

    assert report.audit_status == "block"
    assert report.next_step == "block_report_only_research_payload"
    assert report.finding_count == d("11")
    assert report.watch_finding_count == d("4")
    assert report.block_finding_count == d("7")
    assert report.score == d("0.000000")
    assert tuple((item.severity, item.path, item.reason_code) for item in report.findings) == (
        (
            "block",
            "candidate_id",
            "research_public_payload_safety_audit_raw_candidate_id_field",
        ),
        (
            "block",
            "market.market_id",
            "research_public_payload_safety_audit_market_id_field",
        ),
        (
            "watch",
            "market.slug",
            "research_public_payload_safety_audit_slug_field",
        ),
        (
            "watch",
            "question",
            "research_public_payload_safety_audit_question_field",
        ),
        (
            "watch",
            "source_url",
            "research_public_payload_safety_audit_source_reference_field",
        ),
        (
            "block",
            "source_url",
            "research_public_payload_safety_audit_source_reference_value",
        ),
        (
            "watch",
            "source_text",
            "research_public_payload_safety_audit_source_reference_field",
        ),
        (
            "block",
            "source_text",
            "research_public_payload_safety_audit_secret_reference_value",
        ),
        (
            "block",
            "trade_note",
            "research_public_payload_safety_audit_trade_field",
        ),
        (
            "block",
            "trade_note",
            "research_public_payload_safety_audit_order_or_trade_language",
        ),
        (
            "block",
            "trade_note",
            "research_public_payload_safety_audit_position_sizing_language",
        ),
    )
    assert report.reason_codes == tuple(item.reason_code for item in report.findings)


def test_watch_status_for_public_market_text_without_blocking_values() -> None:
    report = audit_research_public_payload(
        safe_report(
            public_payload={
                "public_market_label": "Market label redacted by family.",
                "public_slug_note": "slug withheld",
                "confidence_score": d("0.750000"),
            },
        ),
        generated_at=GENERATED_AT,
        report_name="market_label_payload",
    )

    assert report.audit_status == "watch"
    assert report.next_step == "review_report_only_research_payload"
    assert report.finding_count == d("2")
    assert report.watch_finding_count == d("2")
    assert report.block_finding_count == d("0")
    assert report.score == d("0.800000")
    assert tuple(item.reason_code for item in report.findings) == (
        "research_public_payload_safety_audit_market_id_field",
        "research_public_payload_safety_audit_slug_field",
    )


def test_decimal_score_can_be_disabled_and_payload_stays_json_ready() -> None:
    report = audit_research_public_payload(
        {"summary": "public report", "question": "Redacted question label"},
        generated_at=GENERATED_AT,
        report_name="scoreless_payload",
        include_score=False,
    )
    payload = research_public_payload_safety_report_payload(report)

    assert report.audit_status == "watch"
    assert report.score is None
    assert payload["score"] is None
    assert payload["finding_count"] == "1"
    assert not any(isinstance(value, float) for value in walk_values(payload))


def test_public_contracts_are_frozen_and_validate_strict_types() -> None:
    finding = PublicPayloadSafetyFinding(
        path="summary",
        severity="watch",
        reason_code="research_public_payload_safety_audit_question_field",
        redacted_detail="question field present",
    )
    report = PublicPayloadSafetyReport(
        generated_at=GENERATED_AT,
        report_name="manual_report",
        audit_status="watch",
        next_step="review_report_only_research_payload",
        finding_count=d("1"),
        watch_finding_count=d("1"),
        block_finding_count=d("0"),
        score=d("0.800000"),
        findings=(finding,),
        reason_codes=("research_public_payload_safety_audit_question_field",),
    )

    with pytest.raises(FrozenInstanceError):
        finding.severity = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.audit_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="path"):
        replace(finding, path=_StringSubclass("summary"))
    with pytest.raises(ValueError, match="severity"):
        replace(finding, severity="critical")
    with pytest.raises(ValueError, match="reason_code"):
        replace(finding, reason_code="unsafe code")
    with pytest.raises(ValueError, match="generated_at"):
        replace(report, generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="finding_count"):
        replace(report, finding_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="score"):
        replace(report, score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="findings"):
        replace(report, findings=(object(),))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("different_reason",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_audit_rejects_unsafe_container_types_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="payload"):
        audit_research_public_payload([("not", "public")], generated_at=GENERATED_AT)
    with pytest.raises(ValueError, match="generated_at"):
        audit_research_public_payload({}, generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="report_name"):
        audit_research_public_payload({}, generated_at=GENERATED_AT, report_name=" bad")
    with pytest.raises(ValueError, match="include_score"):
        audit_research_public_payload({}, generated_at=GENERATED_AT, include_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        audit_research_public_payload(
            {"summary": "public", "paper_only": False},
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="confidence_score"):
        audit_research_public_payload(
            safe_report(confidence_score=Decimal("NaN")),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="payload"):
        audit_research_public_payload(
            {"summary": object()},
            generated_at=GENERATED_AT,
        )


def test_owned_module_has_no_live_network_database_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "live_trading",
        "broker",
        "cancel_order",
        "private_key",
        "api_key",
        "secret_key",
        "requests",
        "socket",
        "subprocess",
        "open(",
        "network",
        "database",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
