from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_decision_audit_summary"


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "watch_audit_severity_score": d("0.250000"),
        "block_audit_severity_score": d("0.750000"),
    }
    values.update(overrides)
    return module.ResearchDecisionAuditSummaryConfig(**values)


def signal(
    component: str,
    *,
    status: str = "pass",
    audited_item_count: Decimal = d("3.000000"),
    issue_count: Decimal = d("0.000000"),
    audit_severity_score: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
    public_summary: str | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchDecisionAuditComponentSignal(
        component=component,
        status=status,
        audited_item_count=audited_item_count,
        issue_count=issue_count,
        audit_severity_score=audit_severity_score,
        reason_codes=reason_codes,
        public_summary=public_summary,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def complete_signals(**overrides: Any) -> tuple[Any, ...]:
    values = {
        "decision_change_log": signal("decision_change_log"),
        "quality_assurance": signal("quality_assurance"),
        "execution_boundary": signal("execution_boundary"),
        "evidence_quality": signal("evidence_quality"),
    }
    values.update(overrides)
    return tuple(values.values())


def report(signals: tuple[Any, ...] | list[Any], *, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_decision_audit_summary(
        signals,
        config=cfg or config(),
    )


def walk_strings(value: object) -> tuple[str, ...]:
    if isinstance(value, dict):
        values: list[str] = []
        for key, child in value.items():
            values.append(key)
            values.extend(walk_strings(child))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for child in value:
            values.extend(walk_strings(child))
        return tuple(values)
    if type(value) is str:
        return (value,)
    return ()


def assert_json_ready(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert type(key) is str
            assert_json_ready(child)
        return
    if isinstance(value, list):
        for child in value:
            assert_json_ready(child)
        return
    assert value is None or type(value) in (str, bool)


def assert_no_public_numeric_scalars(value: object) -> None:
    if type(value) in (Decimal, int, float):
        pytest.fail(f"public payload numeric value was not serialized: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_numeric_scalars(child)
    if isinstance(value, list):
        for child in value:
            assert_no_public_numeric_scalars(child)


def test_audit_summary_passes_when_all_research_controls_pass() -> None:
    audit = report(
        complete_signals(
            decision_change_log=signal(
                "decision_change_log",
                audited_item_count=d("5.000000"),
                audit_severity_score=d("0.040000"),
            ),
            quality_assurance=signal(
                "quality_assurance",
                audit_severity_score=d("0.020000"),
            ),
            execution_boundary=signal(
                "execution_boundary",
                audit_severity_score=d("0.000000"),
            ),
            evidence_quality=signal(
                "evidence_quality",
                audit_severity_score=d("0.080000"),
            ),
        ),
    )

    assert audit.status == "pass"
    assert audit.required_component_count == d("4.000000")
    assert audit.observed_component_count == d("4.000000")
    assert audit.missing_component_count == d("0.000000")
    assert audit.pass_count == d("4.000000")
    assert audit.watch_count == d("0.000000")
    assert audit.block_count == d("0.000000")
    assert audit.total_audited_item_count == d("14.000000")
    assert audit.total_issue_count == d("0.000000")
    assert audit.max_audit_severity_score == d("0.080000")
    assert audit.average_audit_severity_score == d("0.035000")
    assert audit.reason_codes == ("research_decision_audit_pass",)
    assert tuple(row.component for row in audit.rows) == (
        "decision_change_log",
        "quality_assurance",
        "execution_boundary",
        "evidence_quality",
    )
    assert tuple(row.component_key for row in audit.rows) == (
        "redacted-decision-audit-001",
        "redacted-decision-audit-002",
        "redacted-decision-audit-003",
        "redacted-decision-audit-004",
    )
    assert all(row.status == "pass" for row in audit.rows)

    payload = api().research_decision_audit_summary_payload(audit)
    json.dumps(payload, sort_keys=True)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["total_audited_item_count"] == "14.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert_json_ready(payload)
    assert_no_public_numeric_scalars(payload)


def test_audit_summary_watches_nonblocking_execution_boundary_gaps() -> None:
    audit = report(
        complete_signals(
            execution_boundary=signal(
                "execution_boundary",
                status="watch",
                issue_count=d("1.000000"),
                audit_severity_score=d("0.300000"),
                reason_codes=("manual_boundary_check_needed",),
            ),
        ),
    )

    assert audit.status == "watch"
    assert audit.pass_count == d("3.000000")
    assert audit.watch_count == d("1.000000")
    assert audit.block_count == d("0.000000")
    assert audit.reason_codes == (
        "audit_component_issue_watch",
        "input_status_watch",
        "audit_severity_score_watch",
        "input_manual_boundary_check_needed",
        "research_decision_audit_watch",
    )
    row = audit.rows[2]
    assert row.component == "execution_boundary"
    assert row.status == "watch"
    assert row.reason_codes == (
        "audit_component_issue_watch",
        "input_status_watch",
        "audit_severity_score_watch",
        "input_manual_boundary_check_needed",
    )


def test_audit_summary_blocks_missing_or_blocking_research_controls() -> None:
    missing = report(
        (
            signal("decision_change_log"),
            signal("quality_assurance"),
            signal("execution_boundary"),
        ),
    )

    assert missing.status == "block"
    assert missing.observed_component_count == d("3.000000")
    assert missing.missing_component_count == d("1.000000")
    assert missing.block_count == d("0.000000")
    assert missing.reason_codes == (
        "missing_required_audit_component",
        "research_decision_audit_block",
    )

    blocking = report(
        complete_signals(
            evidence_quality=signal(
                "evidence_quality",
                status="block",
                issue_count=d("2.000000"),
                audit_severity_score=d("0.900000"),
            ),
        ),
    )

    assert blocking.status == "block"
    assert blocking.missing_component_count == d("0.000000")
    assert blocking.block_count == d("1.000000")
    assert blocking.rows[3].component == "evidence_quality"
    assert blocking.rows[3].status == "block"
    assert blocking.rows[3].reason_codes == (
        "audit_component_issue_block",
        "input_status_block",
        "audit_severity_score_block",
    )


def test_audit_summary_rejects_types_subclasses_and_mutation() -> None:
    module = api()

    with pytest.raises(ValueError, match="Decimal"):
        config(watch_audit_severity_score=1)
    with pytest.raises(ValueError, match="Decimal"):
        config(block_audit_severity_score=DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="Decimal"):
        signal("decision_change_log", audit_severity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="whole count"):
        signal("decision_change_log", audited_item_count=d("1.500000"))
    with pytest.raises(ValueError, match="signals must be a list or tuple"):
        module.build_research_decision_audit_summary(
            (signal("decision_change_log") for _ in range(1)),
            config=config(),
        )
    with pytest.raises(ValueError, match="signals must contain"):
        module.build_research_decision_audit_summary([object()], config=config())

    audit = report(complete_signals())
    with pytest.raises(FrozenInstanceError):
        audit.status = "block"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class InvalidSignal(module.ResearchDecisionAuditComponentSignal):
            pass


def test_audit_summary_rejects_leaks_in_inputs_and_payload() -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe"):
        signal("decision_change_log", public_summary="raw candidate id rc-42")
    with pytest.raises(ValueError, match="unsafe"):
        signal("decision_change_log", public_summary="market question leaked")
    with pytest.raises(ValueError, match="unsafe"):
        signal("evidence_quality", public_summary="https://example.test/source")
    with pytest.raises(ValueError, match="unsafe"):
        signal("evidence_quality", reason_codes=("source_url_present",))
    with pytest.raises(ValueError, match="unsafe"):
        signal("execution_boundary", public_summary="manual recommendation to buy")
    with pytest.raises(ValueError, match="unsafe"):
        signal("execution_boundary", public_summary="wallet auth token")

    payload = module.research_decision_audit_summary_payload(report(complete_signals()))

    bad_key_payload = dict(payload)
    bad_key_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_decision_audit_summary_payload(bad_key_payload)

    bad_value_payload = dict(payload)
    bad_value_payload["reason_codes"] = ["wallet_auth_required"]
    with pytest.raises(ValueError, match="unsafe"):
        module.research_decision_audit_summary_payload(bad_value_payload)

    bad_nested_payload = dict(payload)
    bad_nested_payload["rows"] = [dict(payload["rows"][0], public_summary="source text leak")]
    with pytest.raises(ValueError, match="unsafe"):
        module.research_decision_audit_summary_payload(bad_nested_payload)

    bad_numeric_payload = dict(payload)
    bad_numeric_payload["pass_count"] = 4
    with pytest.raises(ValueError, match="Decimal-derived string"):
        module.research_decision_audit_summary_payload(bad_numeric_payload)


def test_audit_summary_enforces_hard_report_only_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal("decision_change_log", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        signal("execution_boundary", readonly=False)

    payload = module.research_decision_audit_summary_payload(report(complete_signals()))
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    bad_flag_payload = dict(payload)
    bad_flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_decision_audit_summary_payload(bad_flag_payload)


def test_audit_summary_payload_is_deterministic_and_pure_report_only() -> None:
    module = api()
    signals = complete_signals(
        decision_change_log=signal(
            "decision_change_log",
            audited_item_count=d("7.000000"),
            audit_severity_score=d("0.200000"),
        ),
        quality_assurance=signal(
            "quality_assurance",
            audit_severity_score=d("0.260000"),
        ),
    )

    forward_payload = module.research_decision_audit_summary_payload(report(signals))
    reverse_payload = module.research_decision_audit_summary_payload(report(tuple(reversed(signals))))

    assert forward_payload == reverse_payload
    assert len(forward_payload["derived_validation_digest"]) == 64
    assert list(forward_payload) == [
        "config_version",
        "status",
        "required_component_count",
        "observed_component_count",
        "missing_component_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_audited_item_count",
        "total_issue_count",
        "max_audit_severity_score",
        "average_audit_severity_score",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ]
    assert_json_ready(forward_payload)
    assert_no_public_numeric_scalars(forward_payload)

    forbidden_fragments = (
        "raw-candidate-42",
        "raw candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "https://",
        "url",
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
    )
    public_surface = "\n".join(walk_strings(forward_payload)).lower()
    for fragment in forbidden_fragments:
        assert fragment not in public_surface

    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_decision_audit_summary.py"
    )
    module_text = module_path.read_text(encoding="utf-8")
    forbidden_source_fragments = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in module_text

    tree = ast.parse(module_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}
