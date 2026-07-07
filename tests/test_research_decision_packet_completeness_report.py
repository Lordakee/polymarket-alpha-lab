from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_decision_packet_completeness_report import (
    DEFAULT_RESEARCH_DECISION_PACKET_COMPLETENESS_CONFIG_VERSION,
    ResearchDecisionPacketCompletenessConfig,
    ResearchDecisionPacketCompletenessInputRow,
    ResearchDecisionPacketCompletenessReasonCodeCount,
    ResearchDecisionPacketCompletenessReport,
    ResearchDecisionPacketCompletenessRow,
    build_research_decision_packet_completeness_report,
    research_decision_packet_completeness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_decision_packet_completeness_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchDecisionPacketCompletenessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_DECISION_PACKET_COMPLETENESS_CONFIG_VERSION
        ),
        "max_packet_age_seconds": d("86400.000000"),
        "max_team_review_lag_seconds": d("7200.000000"),
        "min_probability_assumption_count": d("1"),
        "min_evidence_source_count": d("2"),
        "min_counter_evidence_count": d("1"),
        "min_cost_review_count": d("1"),
        "min_settlement_rule_count": d("1"),
        "min_team_reviewer_count": d("1"),
        "min_retrospective_plan_count": d("1"),
        "min_section_quality": d("0.700000"),
        "watch_section_quality": d("0.500000"),
    }
    values.update(overrides)
    return ResearchDecisionPacketCompletenessConfig(**values)


def input_row(
    packet_key: str = "research.packet.frontier.rules",
    *,
    condition_id: str = "condition_frontier_rules",
    packet_label: str = "frontier_rules_packet",
    public_packet_reference: str = "public-packet-memo",
    prepared_at: datetime | None = None,
    reviewed_at: object = _UNSET,
    probability_assumption_count: Decimal = d("2"),
    probability_assumption_quality: Decimal = d("0.800000"),
    evidence_source_count: Decimal = d("3"),
    evidence_quality: Decimal = d("0.820000"),
    counter_evidence_count: Decimal = d("1"),
    counter_evidence_quality: Decimal = d("0.760000"),
    cost_review_count: Decimal = d("1"),
    cost_review_quality: Decimal = d("0.750000"),
    settlement_rule_count: Decimal = d("1"),
    settlement_rule_quality: Decimal = d("0.780000"),
    team_reviewer_count: Decimal = d("2"),
    team_review_quality: Decimal = d("0.800000"),
    retrospective_plan_count: Decimal = d("1"),
    retrospective_plan_quality: Decimal = d("0.720000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchDecisionPacketCompletenessInputRow:
    return ResearchDecisionPacketCompletenessInputRow(
        packet_key=packet_key,
        condition_id=condition_id,
        packet_label=packet_label,
        public_packet_reference=public_packet_reference,
        prepared_at=prepared_at or GENERATED_AT - timedelta(hours=1),
        reviewed_at=(
            GENERATED_AT - timedelta(minutes=30)
            if reviewed_at is _UNSET
            else reviewed_at
        ),
        probability_assumption_count=probability_assumption_count,
        probability_assumption_quality=probability_assumption_quality,
        evidence_source_count=evidence_source_count,
        evidence_quality=evidence_quality,
        counter_evidence_count=counter_evidence_count,
        counter_evidence_quality=counter_evidence_quality,
        cost_review_count=cost_review_count,
        cost_review_quality=cost_review_quality,
        settlement_rule_count=settlement_rule_count,
        settlement_rule_quality=settlement_rule_quality,
        team_reviewer_count=team_reviewer_count,
        team_review_quality=team_review_quality,
        retrospective_plan_count=retrospective_plan_count,
        retrospective_plan_quality=retrospective_plan_quality,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchDecisionPacketCompletenessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchDecisionPacketCompletenessReport:
    return build_research_decision_packet_completeness_report(
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
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if (
            field.name.endswith(
                (
                    "_count",
                    "_quality",
                    "_ratio",
                    "_score",
                    "_seconds",
                ),
            )
            or "probability" in field.name
        ):
            assert type(item) is Decimal


def test_decision_packet_completeness_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.packet.archived.rules",
                condition_id="condition_archived_rules",
                packet_label="archived_rules_packet",
                public_packet_reference="https://vendor.example/packet?credential=hidden",
                prepared_at=GENERATED_AT - timedelta(hours=30),
                reviewed_at=GENERATED_AT - timedelta(hours=28),
                probability_assumption_count=d("1"),
                probability_assumption_quality=d("0.600000"),
                evidence_source_count=d("2"),
                evidence_quality=d("0.550000"),
                counter_evidence_count=d("1"),
                counter_evidence_quality=d("0.600000"),
                cost_review_count=d("1"),
                cost_review_quality=d("0.500000"),
                settlement_rule_count=d("1"),
                settlement_rule_quality=d("0.620000"),
                team_reviewer_count=d("1"),
                team_review_quality=d("0.650000"),
                retrospective_plan_count=d("1"),
                retrospective_plan_quality=d("0.600000"),
            ),
            input_row(
                "research.packet.missing.review",
                condition_id="condition_missing_review",
                packet_label="missing_review_packet",
                public_packet_reference="confidential-packet-brief",
                prepared_at=GENERATED_AT - timedelta(hours=2),
                reviewed_at=None,
                probability_assumption_count=d("0"),
                evidence_source_count=d("1"),
                counter_evidence_count=d("0"),
                cost_review_count=d("0"),
                settlement_rule_count=d("0"),
                team_reviewer_count=d("0"),
                retrospective_plan_count=d("0"),
            ),
            input_row(
                "research.packet.frontier.rules",
                condition_id="condition_frontier_rules",
                packet_label="frontier_rules_packet",
                public_packet_reference="public-packet-memo",
                prepared_at=GENERATED_AT - timedelta(minutes=45),
                reviewed_at=GENERATED_AT - timedelta(minutes=15),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_DECISION_PACKET_COMPLETENESS_CONFIG_VERSION
    )
    assert summary.report_status == "block"
    assert summary.next_step == "block_report_only_decision_packet_completeness"
    assert summary.packet_count == d("3.000000")
    assert summary.pass_packet_count == d("1.000000")
    assert summary.watch_packet_count == d("1.000000")
    assert summary.blocked_packet_count == d("1.000000")
    assert summary.missing_probability_assumption_count == d("1.000000")
    assert summary.missing_evidence_count == d("1.000000")
    assert summary.missing_counter_evidence_count == d("1.000000")
    assert summary.missing_cost_review_count == d("1.000000")
    assert summary.missing_settlement_rule_count == d("1.000000")
    assert summary.missing_team_review_count == d("1.000000")
    assert summary.missing_retrospective_plan_count == d("1.000000")
    assert summary.average_completeness_score == d("0.454762")
    assert summary.minimum_completeness_score == d("0.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.packet_status, row.packet_label) for row in summary.rows) == (
        ("block", "missing_review_packet"),
        ("watch", "archived_rules_packet"),
        ("pass", "frontier_rules_packet"),
    )

    blocked = summary.rows[0]
    assert blocked.packet_age_seconds == d("7200.000000")
    assert blocked.team_review_lag_seconds is None
    assert blocked.completeness_score == d("0.000000")
    assert blocked.redacted_packet_reference == "sha256:e9c216c9c36a"
    assert blocked.reason_codes == (
        "research_decision_packet_completeness_missing_probability_assumptions",
        "research_decision_packet_completeness_missing_evidence",
        "research_decision_packet_completeness_missing_counter_evidence",
        "research_decision_packet_completeness_missing_cost_review",
        "research_decision_packet_completeness_missing_settlement_rules",
        "research_decision_packet_completeness_missing_team_review",
        "research_decision_packet_completeness_missing_retrospective_plan",
    )

    watch = summary.rows[1]
    assert watch.packet_age_seconds == d("108000.000000")
    assert watch.team_review_lag_seconds == d("7200.000000")
    assert watch.completeness_score == d("0.588571")
    assert watch.redacted_packet_reference == "sha256:9ca48f2dc2b0"
    assert watch.reason_codes == (
        "research_decision_packet_completeness_stale_packet",
        "research_decision_packet_completeness_weak_probability_assumptions",
        "research_decision_packet_completeness_weak_evidence",
        "research_decision_packet_completeness_weak_counter_evidence",
        "research_decision_packet_completeness_weak_cost_review",
        "research_decision_packet_completeness_weak_settlement_rules",
        "research_decision_packet_completeness_weak_team_review",
        "research_decision_packet_completeness_weak_retrospective_plan",
    )

    ready = summary.rows[2]
    assert ready.packet_status == "pass"
    assert ready.packet_age_seconds == d("2700.000000")
    assert ready.team_review_lag_seconds == d("1800.000000")
    assert ready.completeness_score == d("0.775714")
    assert ready.redacted_packet_reference == "public-packet-memo"
    assert ready.reason_codes == (
        "research_decision_packet_completeness_pass",
    )

    assert summary.reason_code_counts == (
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code=(
                "research_decision_packet_completeness_missing_probability_assumptions"
            ),
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_missing_evidence",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code=(
                "research_decision_packet_completeness_missing_counter_evidence"
            ),
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_missing_cost_review",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code=(
                "research_decision_packet_completeness_missing_settlement_rules"
            ),
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_missing_team_review",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code=(
                "research_decision_packet_completeness_missing_retrospective_plan"
            ),
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_stale_packet",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code=(
                "research_decision_packet_completeness_weak_probability_assumptions"
            ),
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_weak_evidence",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_weak_counter_evidence",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_weak_cost_review",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_weak_settlement_rules",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_weak_team_review",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_weak_retrospective_plan",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_pass",
            count=d("1.000000"),
            packet_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "hidden",
        "vendor.example",
        "https://",
        "confidential-packet-brief",
        "credential",
    ):
        assert value not in public


def test_empty_decision_packet_completeness_report_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.report_status == "block"
    assert summary.next_step == "block_report_only_decision_packet_completeness"
    assert summary.packet_count == ZERO
    assert summary.pass_packet_count == ZERO
    assert summary.watch_packet_count == ZERO
    assert summary.blocked_packet_count == ZERO
    assert summary.average_completeness_score == ZERO
    assert summary.minimum_completeness_score == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchDecisionPacketCompletenessReasonCodeCount(
            reason_code="research_decision_packet_completeness_no_inputs",
            count=d("1.000000"),
            packet_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_decision_packet_completeness_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_decision_packet_completeness_honors_custom_threshold_config() -> None:
    summary = report(
        (
            input_row(
                probability_assumption_quality=d("0.640000"),
                evidence_quality=d("0.640000"),
                counter_evidence_quality=d("0.640000"),
                cost_review_quality=d("0.640000"),
                settlement_rule_quality=d("0.640000"),
                team_review_quality=d("0.640000"),
                retrospective_plan_quality=d("0.640000"),
            ),
        ),
        cfg=config(
            max_packet_age_seconds=d("172800.000000"),
            max_team_review_lag_seconds=d("172800.000000"),
            min_evidence_source_count=d("1"),
            min_section_quality=d("0.700000"),
            watch_section_quality=d("0.600000"),
        ),
    )

    assert summary.report_status == "watch"
    assert summary.watch_packet_count == d("1.000000")
    assert summary.rows[0].packet_status == "watch"
    assert summary.rows[0].reason_codes == (
        "research_decision_packet_completeness_weak_probability_assumptions",
        "research_decision_packet_completeness_weak_evidence",
        "research_decision_packet_completeness_weak_counter_evidence",
        "research_decision_packet_completeness_weak_cost_review",
        "research_decision_packet_completeness_weak_settlement_rules",
        "research_decision_packet_completeness_weak_team_review",
        "research_decision_packet_completeness_weak_retrospective_plan",
    )


def test_decision_packet_completeness_payload_uses_decimal_strings_and_redacts() -> None:
    summary = report((input_row(),))
    payload = research_decision_packet_completeness_report_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["packet_count"] == "1.000000"
    assert payload["average_completeness_score"] == "0.775714"
    assert payload["rows"][0]["evidence_source_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_packet_reference':" not in repr(payload)
    assert "confidential" not in repr(payload).lower()


def test_decision_packet_completeness_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(ResearchDecisionPacketCompletenessConfig)
    assert is_dataclass(ResearchDecisionPacketCompletenessInputRow)
    assert is_dataclass(ResearchDecisionPacketCompletenessRow)
    assert is_dataclass(ResearchDecisionPacketCompletenessReasonCodeCount)
    assert is_dataclass(ResearchDecisionPacketCompletenessReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.evidence_source_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].evidence_source_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.packet_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("decision-packet-v0"))
    with pytest.raises(ValueError, match="max_packet_age_seconds"):
        config(max_packet_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_evidence_source_count"):
        config(min_evidence_source_count=d("1.5"))
    with pytest.raises(ValueError, match="min_section_quality"):
        config(min_section_quality=Decimal("NaN"))
    with pytest.raises(ValueError, match="watch_section_quality"):
        config(watch_section_quality=d("-0.000001"))
    with pytest.raises(ValueError, match="watch_section_quality"):
        config(watch_section_quality=d("0.800000"), min_section_quality=d("0.700000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="packet_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="live_surface")
    with pytest.raises(ValueError, match="prepared_at"):
        input_row(prepared_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="reviewed_at"):
        input_row(reviewed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="probability_assumption_count"):
        input_row(probability_assumption_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality"):
        input_row(evidence_quality=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="counter_evidence_quality"):
        input_row(counter_evidence_quality=Decimal("Infinity"))
    with pytest.raises(ValueError, match="cost_review_quality"):
        input_row(cost_review_quality=d("1.000001"))
    with pytest.raises(ValueError, match="settlement_rule_quality"):
        input_row(settlement_rule_quality=d("-0.000001"))
    with pytest.raises(ValueError, match="packet_label"):
        input_row(packet_label="buy_signal_packet")
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_decision_packet_completeness_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_decision_packet_completeness_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "research_decision_packet_completeness_pass",
                "research_decision_packet_completeness_weak_evidence",
            ),
        )
    with pytest.raises(ValueError, match="packet_status"):
        replace(ready, packet_status="block")
    with pytest.raises(ValueError, match="completeness_score"):
        replace(ready, completeness_score=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_packet_reference"):
        replace(ready, redacted_packet_reference="https://host?credential=hidden")

    with pytest.raises(ValueError, match="pass_packet_count"):
        replace(report((input_row(),)), pass_packet_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report((input_row(),)), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report((input_row(),)), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report((input_row(),)), readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.packet.z", packet_label="zeta_packet"),
                input_row(),
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


def test_module_has_no_io_store_execution_or_disallowed_language_surfaces() -> None:
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
        "buy",
        "sell",
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
