from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_decision_readiness_exception_report import (
    DEFAULT_RESEARCH_DECISION_READINESS_EXCEPTION_CONFIG_VERSION,
    ResearchDecisionReadinessExceptionConfig,
    ResearchDecisionReadinessExceptionInputRow,
    ResearchDecisionReadinessExceptionReasonCodeCount,
    ResearchDecisionReadinessExceptionReport,
    ResearchDecisionReadinessExceptionRow,
    build_research_decision_readiness_exception_report,
    research_decision_readiness_exception_report_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_decision_readiness_exception_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchDecisionReadinessExceptionConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_DECISION_READINESS_EXCEPTION_CONFIG_VERSION,
        "missing_evidence_block_threshold": d("1"),
        "cost_anomaly_watch_threshold": d("0.150000"),
        "cost_anomaly_block_threshold": d("0.350000"),
        "settlement_ambiguity_watch_threshold": d("0.200000"),
        "settlement_ambiguity_block_threshold": d("0.500000"),
        "team_disagreement_watch_threshold": d("0.250000"),
        "team_disagreement_block_threshold": d("0.600000"),
    }
    values.update(overrides)
    return ResearchDecisionReadinessExceptionConfig(**values)


def input_row(
    packet_id: str = "packet.public.readiness",
    *,
    exception_id: str = "exception.public.pass",
    exception_type: str = "missing_evidence",
    observed_at: datetime | None = None,
    public_reference: str = "public-readiness-memo",
    severity_score: Decimal = d("0.050000"),
    missing_evidence_count: Decimal = ZERO,
    cost_anomaly_score: Decimal = ZERO,
    settlement_ambiguity_score: Decimal = ZERO,
    team_disagreement_score: Decimal = ZERO,
    safety_blocked: bool = False,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchDecisionReadinessExceptionInputRow:
    return ResearchDecisionReadinessExceptionInputRow(
        packet_id=packet_id,
        exception_id=exception_id,
        exception_type=exception_type,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        public_reference=public_reference,
        severity_score=severity_score,
        missing_evidence_count=missing_evidence_count,
        cost_anomaly_score=cost_anomaly_score,
        settlement_ambiguity_score=settlement_ambiguity_score,
        team_disagreement_score=team_disagreement_score,
        safety_blocked=safety_blocked,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchDecisionReadinessExceptionConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchDecisionReadinessExceptionReport:
    return build_research_decision_readiness_exception_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly", "safety_blocked"}:
            continue
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
            assert type(item) is Decimal


def test_decision_readiness_exception_report_covers_all_exception_types() -> None:
    summary = report(
        (
            input_row(
                "packet.public.safety",
                exception_id="exception.public.safety",
                exception_type="safety_block",
                observed_at=GENERATED_AT - timedelta(minutes=15),
                public_reference="confidential-safety-note?credential=hidden",
                severity_score=d("0.900000"),
                safety_blocked=True,
            ),
            input_row(
                "packet.public.evidence",
                exception_id="exception.public.evidence",
                exception_type="missing_evidence",
                observed_at=GENERATED_AT - timedelta(hours=2),
                severity_score=d("0.700000"),
                missing_evidence_count=d("1"),
            ),
            input_row(
                "packet.public.cost",
                exception_id="exception.public.cost",
                exception_type="cost_anomaly",
                observed_at=GENERATED_AT - timedelta(hours=3),
                public_reference="private-cost-review?credential=hidden",
                severity_score=d("0.650000"),
                cost_anomaly_score=d("0.420000"),
            ),
            input_row(
                "packet.public.settlement",
                exception_id="exception.public.settlement",
                exception_type="settlement_ambiguity",
                observed_at=GENERATED_AT - timedelta(hours=4),
                severity_score=d("0.300000"),
                settlement_ambiguity_score=d("0.300000"),
            ),
            input_row(
                "packet.public.team",
                exception_id="exception.public.team",
                exception_type="team_disagreement",
                observed_at=GENERATED_AT - timedelta(hours=5),
                severity_score=d("0.400000"),
                team_disagreement_score=d("0.400000"),
            ),
            input_row(),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_DECISION_READINESS_EXCEPTION_CONFIG_VERSION
    )
    assert summary.report_status == "block"
    assert summary.next_step == (
        "block_report_only_research_decision_readiness_exception_report"
    )
    assert summary.exception_count == d("6.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("2.000000")
    assert summary.block_count == d("3.000000")
    assert summary.missing_evidence_count == d("1.000000")
    assert summary.cost_anomaly_count == d("1.000000")
    assert summary.settlement_ambiguity_count == d("1.000000")
    assert summary.team_disagreement_count == d("1.000000")
    assert summary.safety_block_count == d("1.000000")
    assert summary.average_severity_score == d("0.500000")
    assert summary.max_exception_age_seconds == d("18000.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.status, row.exception_type) for row in summary.rows) == (
        ("block", "safety_block"),
        ("block", "missing_evidence"),
        ("block", "cost_anomaly"),
        ("watch", "team_disagreement"),
        ("watch", "settlement_ambiguity"),
        ("pass", "missing_evidence"),
    )

    assert summary.rows[0].reason_codes == (
        "research_decision_readiness_exception_safety_block",
    )
    assert summary.rows[0].redacted_public_reference == "sha256:55d9c2306e76"
    assert summary.rows[1].reason_codes == (
        "research_decision_readiness_exception_missing_evidence",
    )
    assert summary.rows[2].reason_codes == (
        "research_decision_readiness_exception_cost_anomaly_block",
    )
    assert summary.rows[3].reason_codes == (
        "research_decision_readiness_exception_team_disagreement_watch",
    )
    assert summary.rows[4].reason_codes == (
        "research_decision_readiness_exception_settlement_ambiguity_watch",
    )
    assert summary.rows[5].reason_codes == (
        "research_decision_readiness_exception_pass",
    )
    assert summary.rows[5].redacted_public_reference == "public-readiness-memo"

    assert summary.reason_code_counts == (
        ResearchDecisionReadinessExceptionReasonCodeCount(
            reason_code="research_decision_readiness_exception_safety_block",
            count=d("1.000000"),
            exception_ratio=d("0.166667"),
        ),
        ResearchDecisionReadinessExceptionReasonCodeCount(
            reason_code="research_decision_readiness_exception_missing_evidence",
            count=d("1.000000"),
            exception_ratio=d("0.166667"),
        ),
        ResearchDecisionReadinessExceptionReasonCodeCount(
            reason_code="research_decision_readiness_exception_cost_anomaly_block",
            count=d("1.000000"),
            exception_ratio=d("0.166667"),
        ),
        ResearchDecisionReadinessExceptionReasonCodeCount(
            reason_code="research_decision_readiness_exception_settlement_ambiguity_watch",
            count=d("1.000000"),
            exception_ratio=d("0.166667"),
        ),
        ResearchDecisionReadinessExceptionReasonCodeCount(
            reason_code="research_decision_readiness_exception_team_disagreement_watch",
            count=d("1.000000"),
            exception_ratio=d("0.166667"),
        ),
        ResearchDecisionReadinessExceptionReasonCodeCount(
            reason_code="research_decision_readiness_exception_pass",
            count=d("1.000000"),
            exception_ratio=d("0.166667"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "hidden",
        "credential",
        "confidential-safety-note",
        "private-cost-review",
    ):
        assert value not in public


def test_empty_decision_readiness_exception_report_is_blocked() -> None:
    summary = report(())

    assert summary.report_status == "block"
    assert summary.next_step == (
        "block_report_only_research_decision_readiness_exception_report"
    )
    assert summary.exception_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_severity_score == ZERO
    assert summary.max_exception_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchDecisionReadinessExceptionReasonCodeCount(
            reason_code="research_decision_readiness_exception_no_inputs",
            count=d("1.000000"),
            exception_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_decision_readiness_exception_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_decision_readiness_exception_report_honors_custom_thresholds() -> None:
    summary = report(
        (
            input_row(
                exception_type="cost_anomaly",
                cost_anomaly_score=d("0.120000"),
            ),
        ),
        cfg=config(
            cost_anomaly_watch_threshold=d("0.100000"),
            cost_anomaly_block_threshold=d("0.900000"),
        ),
    )

    assert summary.report_status == "watch"
    assert summary.watch_count == d("1.000000")
    assert summary.rows[0].status == "watch"
    assert summary.rows[0].reason_codes == (
        "research_decision_readiness_exception_cost_anomaly_watch",
    )


def test_decision_readiness_exception_payload_is_public_and_decimal_stringed() -> None:
    summary = report(
        (
            input_row(
                public_reference="private-cost-review?credential=hidden",
                cost_anomaly_score=d("0.420000"),
            ),
        ),
    )
    payload = research_decision_readiness_exception_report_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["exception_count"] == "1.000000"
    assert payload["average_severity_score"] == "0.050000"
    assert payload["rows"][0]["cost_anomaly_score"] == "0.420000"
    assert payload["rows"][0]["redacted_public_reference"].startswith("sha256:")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk_values(payload))
    assert not any(type(value) is int for value in walk_values(payload))
    assert "'public_reference':" not in repr(payload)
    assert "credential" not in repr(payload).lower()
    assert "private-cost-review" not in repr(payload).lower()


def test_decision_readiness_exception_validates_contracts_and_flags() -> None:
    assert is_dataclass(ResearchDecisionReadinessExceptionConfig)
    assert is_dataclass(ResearchDecisionReadinessExceptionInputRow)
    assert is_dataclass(ResearchDecisionReadinessExceptionRow)
    assert is_dataclass(ResearchDecisionReadinessExceptionReasonCodeCount)
    assert is_dataclass(ResearchDecisionReadinessExceptionReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.severity_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].severity_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.exception_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("readiness-v0"))
    with pytest.raises(ValueError, match="missing_evidence_block_threshold"):
        config(missing_evidence_block_threshold=d("1.5"))
    with pytest.raises(ValueError, match="cost_anomaly_watch_threshold"):
        config(cost_anomaly_watch_threshold=d("-0.000001"))
    with pytest.raises(ValueError, match="cost_anomaly_block_threshold"):
        config(
            cost_anomaly_watch_threshold=d("0.500000"),
            cost_anomaly_block_threshold=d("0.350000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="packet_id"):
        input_row(" bad")
    with pytest.raises(ValueError, match="exception_id"):
        input_row(exception_id="live_surface")
    with pytest.raises(ValueError, match="exception_type"):
        input_row(exception_type="unsupported")
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="public_reference"):
        input_row(public_reference=" bad")
    with pytest.raises(ValueError, match="severity_score"):
        input_row(severity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="missing_evidence_count"):
        input_row(missing_evidence_count=d("1.5"))
    with pytest.raises(ValueError, match="cost_anomaly_score"):
        input_row(cost_anomaly_score=_DecimalSubclass("0.420000"))
    with pytest.raises(ValueError, match="settlement_ambiguity_score"):
        input_row(settlement_ambiguity_score=d("1.000001"))
    with pytest.raises(ValueError, match="team_disagreement_score"):
        input_row(team_disagreement_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="safety_blocked"):
        input_row(safety_blocked=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_decision_readiness_exception_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_decision_readiness_exception_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))
    with pytest.raises(ValueError, match="observed_at"):
        report((input_row(observed_at=GENERATED_AT + timedelta(seconds=1)),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    passed = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passed,
            reason_codes=(
                "research_decision_readiness_exception_pass",
                "research_decision_readiness_exception_cost_anomaly_watch",
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(passed, status="block")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(passed, cost_anomaly_score=d("0.420000"))
    with pytest.raises(ValueError, match="redacted_public_reference"):
        replace(passed, redacted_public_reference="credential=hidden")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report((input_row(),)), pass_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report((input_row(),)), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report((input_row(),)), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report((input_row(),)), readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row(
                    "packet.public.a",
                    exception_id="exception.public.a",
                    severity_score=d("0.100000"),
                ),
                input_row(
                    "packet.public.z",
                    exception_id="exception.public.z",
                    severity_score=d("0.200000"),
                ),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_or_action_surfaces() -> None:
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
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "advice",
        "market_slug",
        "question",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "buy",
        "sell",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
        "database",
        "durable",
        "recommend",
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
