from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_team_memory_quality_audit_report import (
    DEFAULT_RESEARCH_TEAM_MEMORY_QUALITY_AUDIT_CONFIG_VERSION,
    ResearchTeamMemoryQualityAuditConfig,
    ResearchTeamMemoryQualityAuditInputRow,
    ResearchTeamMemoryQualityAuditReasonCodeCount,
    ResearchTeamMemoryQualityAuditReport,
    ResearchTeamMemoryQualityAuditRow,
    build_research_team_memory_quality_audit_report,
    research_team_memory_quality_audit_report_digest,
    research_team_memory_quality_audit_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def input_row(
    team_key: str = "research.macro",
    *,
    specialist_key: str = "specialist.policy",
    memory_scope: str = "macro_policy",
    quality_score: Decimal = d("0.920000"),
    coverage_ratio: Decimal = d("0.940000"),
    conflict_ratio: Decimal = d("0.020000"),
    update_lag_seconds: Decimal = d("3600.000000"),
    reviewed_item_count: Decimal = d("12.000000"),
    stale_item_count: Decimal = d("0.000000"),
    conflict_item_count: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamMemoryQualityAuditInputRow:
    return ResearchTeamMemoryQualityAuditInputRow(
        team_key=team_key,
        specialist_key=specialist_key,
        memory_scope=memory_scope,
        quality_score=quality_score,
        coverage_ratio=coverage_ratio,
        conflict_ratio=conflict_ratio,
        update_lag_seconds=update_lag_seconds,
        reviewed_item_count=reviewed_item_count,
        stale_item_count=stale_item_count,
        conflict_item_count=conflict_item_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchTeamMemoryQualityAuditInputRow, ...],
    *,
    cfg: ResearchTeamMemoryQualityAuditConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamMemoryQualityAuditReport:
    return build_research_team_memory_quality_audit_report(
        rows,
        config=cfg or ResearchTeamMemoryQualityAuditConfig(),
        generated_at=generated_at,
    )


def test_quality_audit_reduces_pass_watch_and_block_team_memory_rows() -> None:
    summary = report(
        (
            input_row(
                "research.pass",
                specialist_key="specialist.fast",
                memory_scope="macro_policy",
            ),
            input_row(
                "research.watch",
                specialist_key="specialist.gaps",
                memory_scope="event_context",
                quality_score=d("0.720000"),
                coverage_ratio=d("0.760000"),
                conflict_ratio=d("0.140000"),
                update_lag_seconds=d("1814400.000000"),
                stale_item_count=d("2.000000"),
                conflict_item_count=d("1.000000"),
            ),
            input_row(
                "research.block",
                specialist_key="specialist.stale",
                memory_scope="policy_context",
                quality_score=d("0.420000"),
                coverage_ratio=d("0.440000"),
                conflict_ratio=d("0.360000"),
                update_lag_seconds=d("3456000.000000"),
                reviewed_item_count=d("10.000000"),
                stale_item_count=d("8.000000"),
                conflict_item_count=d("4.000000"),
            ),
        ),
    )

    assert isinstance(summary, ResearchTeamMemoryQualityAuditReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_RESEARCH_TEAM_MEMORY_QUALITY_AUDIT_CONFIG_VERSION
    assert summary.report_status == "block"
    assert summary.audited_team_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_quality_score == d("0.686667")
    assert summary.average_coverage_ratio == d("0.713333")
    assert summary.average_conflict_ratio == d("0.173333")
    assert summary.average_update_lag_seconds == d("1758000.000000")
    assert summary.stale_team_count == d("2.000000")
    assert summary.conflict_team_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.team_key for row in summary.rows) == (
        "research.block",
        "research.watch",
        "research.pass",
    )

    blocked = summary.rows[0]
    assert blocked.public_status == "block"
    assert blocked.quality_gap == d("0.380000")
    assert blocked.coverage_gap == d("0.360000")
    assert blocked.conflict_excess_ratio == d("0.260000")
    assert blocked.update_lag_excess_seconds == d("2246400.000000")
    assert blocked.human_improvement_summary == (
        "Pause automated reuse until quality, coverage, conflict, and freshness gaps "
        "are reviewed by a human."
    )
    assert blocked.reason_codes == (
        "research_team_memory_quality_audit_block_conflict",
        "research_team_memory_quality_audit_block_coverage",
        "research_team_memory_quality_audit_block_quality",
        "research_team_memory_quality_audit_block_stale",
    )

    watched = summary.rows[1]
    assert watched.public_status == "watch"
    assert watched.reason_codes == (
        "research_team_memory_quality_audit_watch_conflict",
        "research_team_memory_quality_audit_watch_coverage",
        "research_team_memory_quality_audit_watch_quality",
        "research_team_memory_quality_audit_watch_stale",
    )

    passed = summary.rows[2]
    assert passed.public_status == "pass"
    assert passed.reason_codes == ("research_team_memory_quality_audit_pass",)

    assert summary.reason_code_counts == (
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_block_conflict",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_block_coverage",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_block_quality",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_block_stale",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_pass",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_watch_conflict",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_watch_coverage",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_watch_quality",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_watch_stale",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(item.reason_code for item in summary.reason_code_counts)


def test_empty_inputs_return_block_report_only_digest() -> None:
    summary = report(())

    assert summary.report_status == "block"
    assert summary.audited_team_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("research_team_memory_quality_audit_no_inputs",)
    assert summary.reason_code_counts == (
        ResearchTeamMemoryQualityAuditReasonCodeCount(
            reason_code="research_team_memory_quality_audit_no_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert research_team_memory_quality_audit_report_digest(summary) == {
        "generated_at": "2026-07-08T12:00:00Z",
        "config_version": DEFAULT_RESEARCH_TEAM_MEMORY_QUALITY_AUDIT_CONFIG_VERSION,
        "report_status": "block",
        "audited_team_count": "0.000000",
        "pass_count": "0.000000",
        "watch_count": "0.000000",
        "block_count": "0.000000",
        "reason_codes": ("research_team_memory_quality_audit_no_inputs",),
    }


def test_quality_audit_validates_types_decimals_flags_and_freezing() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        input_row(quality_score=0.9)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="datetime"):
        report((input_row(),), generated_at="2026-07-08T12:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        report((input_row(),), generated_at=datetime(2026, 7, 8, 12, 0))

    with pytest.raises(ValueError, match="whole second"):
        report((input_row(),), generated_at=datetime(2026, 7, 8, 12, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(TypeError, match="exactly"):
        ResearchTeamMemoryQualityAuditInputRow(
            team_key=_StringSubclass("research.alpha"),
            specialist_key="specialist.policy",
            memory_scope="macro_policy",
            quality_score=d("0.900000"),
            coverage_ratio=d("0.900000"),
            conflict_ratio=d("0.050000"),
            update_lag_seconds=d("3600.000000"),
            reviewed_item_count=d("4.000000"),
            stale_item_count=d("0.000000"),
            conflict_item_count=d("0.000000"),
        )

    with pytest.raises(TypeError, match="exactly"):
        input_row(coverage_ratio=_DecimalSubclass("0.900000"))

    with pytest.raises(ValueError, match="unit interval"):
        input_row(conflict_ratio=d("1.000001"))

    with pytest.raises(ValueError, match="nonnegative"):
        input_row(update_lag_seconds=d("-1.000000"))

    with pytest.raises(ValueError, match="whole"):
        input_row(reviewed_item_count=d("1.500000"))

    with pytest.raises(ValueError, match="stale_item_count"):
        input_row(reviewed_item_count=d("1.000000"), stale_item_count=d("2.000000"))

    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)

    with pytest.raises(TypeError, match="Decimal"):
        ResearchTeamMemoryQualityAuditConfig(pass_quality_score=1)  # type: ignore[arg-type]

    frozen = input_row()
    with pytest.raises(FrozenInstanceError):
        frozen.quality_score = d("0.100000")  # type: ignore[misc]

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.report_status = "pass"  # type: ignore[misc]

    assert replace(frozen, quality_score=d("0.880000")).quality_score == d("0.880000")


def test_public_inputs_and_outputs_reject_private_or_actionable_leaks() -> None:
    leak_values = (
        _join_parts("raw_", "candidate", "_17"),
        _join_parts("market", "_slug"),
        _join_parts("https", "://example.test/path"),
        _join_parts("dsn", "_analytics"),
        _join_parts("source", "_ref"),
        _join_parts("wal", "let", "_field"),
        _join_parts("sub", "mit", "_order"),
        _join_parts("buy", "_signal"),
        _join_parts("rec", "ommend", "_yes"),
        _join_parts("to", "ken", "_abc"),
    )

    for value in leak_values:
        with pytest.raises(ValueError, match="public"):
            input_row(memory_scope=value)

    summary = report((input_row(),))
    payload = research_team_memory_quality_audit_report_payload(summary)
    digest = research_team_memory_quality_audit_report_digest(summary)
    public = repr((payload, digest, asdict(summary))).lower()

    assert {summary.report_status, *(row.public_status for row in summary.rows)} <= {
        "pass",
        "watch",
        "block",
    }
    for token in (
        _join_parts("candidate"),
        _join_parts("market", "_slug"),
        _join_parts("https", "://"),
        _join_parts("source", "_ref"),
        _join_parts("dsn"),
        _join_parts("table"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("order"),
        _join_parts("position"),
        _join_parts("buy"),
        _join_parts("sell"),
        _join_parts("rec", "ommend"),
    ):
        assert token not in public


def test_payload_is_deterministic_decimal_string_only_and_consistent_with_digest() -> None:
    first = report(
        (
            input_row(
                "research.watch",
                specialist_key="specialist.gaps",
                quality_score=d("0.720000"),
                coverage_ratio=d("0.760000"),
                conflict_ratio=d("0.140000"),
                update_lag_seconds=d("1814400.000000"),
            ),
            input_row("research.pass", specialist_key="specialist.fast"),
        ),
    )
    second = report(
        (
            input_row("research.pass", specialist_key="specialist.fast"),
            input_row(
                "research.watch",
                specialist_key="specialist.gaps",
                quality_score=d("0.720000"),
                coverage_ratio=d("0.760000"),
                conflict_ratio=d("0.140000"),
                update_lag_seconds=d("1814400.000000"),
            ),
        ),
    )

    first_payload = research_team_memory_quality_audit_report_payload(first)
    second_payload = research_team_memory_quality_audit_report_payload(second)
    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00Z"
    assert first_payload["audited_team_count"] == "2.000000"
    assert first_payload["rows"][0]["public_status"] == "watch"
    assert first_payload["rows"][1]["public_status"] == "pass"
    assert first_payload["rows"][0]["quality_score"] == "0.720000"

    def walk(value: object) -> tuple[object, ...]:
        if isinstance(value, dict):
            return tuple(child for item in value.values() for child in walk(item))
        if isinstance(value, tuple):
            return tuple(child for item in value for child in walk(item))
        return (value,)

    assert not any(isinstance(value, float) for value in walk(first_payload))

    digest = research_team_memory_quality_audit_report_digest(first)
    assert digest["report_status"] == first_payload["report_status"] == first.report_status
    assert digest["audited_team_count"] == first_payload["audited_team_count"]
    assert digest["pass_count"] == first_payload["pass_count"]
    assert digest["watch_count"] == first_payload["watch_count"]
    assert digest["block_count"] == first_payload["block_count"]
    assert digest["reason_codes"] == first_payload["reason_codes"] == first.reason_codes


def test_quality_audit_module_is_report_only_and_has_no_io_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_memory_quality_audit_report.py"
    )
    module_source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(module_source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "json",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "delete",
        "cursor",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    forbidden_terms = (
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("order"),
        _join_parts("trade"),
        _join_parts("trading"),
        _join_parts("position"),
        _join_parts("buy"),
        _join_parts("sell"),
        _join_parts("rec", "ommend"),
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert not any(term in module_source.lower() for term in forbidden_terms)

    for cls in (
        ResearchTeamMemoryQualityAuditConfig,
        ResearchTeamMemoryQualityAuditInputRow,
        ResearchTeamMemoryQualityAuditReasonCodeCount,
        ResearchTeamMemoryQualityAuditReport,
        ResearchTeamMemoryQualityAuditRow,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
