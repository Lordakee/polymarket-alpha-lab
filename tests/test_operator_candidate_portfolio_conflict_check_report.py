from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.operator_candidate_portfolio_conflict_check_report as api
from polymarket_alpha_lab.operator_candidate_portfolio_conflict_check_report import (
    OPERATOR_CANDIDATE_PORTFOLIO_CONFLICT_STATUSES,
    OperatorCandidatePortfolioConflictCheckReport,
    build_operator_candidate_portfolio_conflict_check_report,
    operator_candidate_portfolio_conflict_check_report_payload,
    operator_candidate_portfolio_conflict_check_report_payload_digest,
    validate_operator_candidate_portfolio_conflict_check_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "operator_candidate_portfolio_conflict_check_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> OperatorCandidatePortfolioConflictCheckReport:
    values = {
        "candidate_market_count": d("3"),
        "same_event_family_count": d("0"),
        "opposing_outcome_count": d("0"),
        "correlated_risk_count": d("0"),
        "manual_conflict_limit_count": d("3"),
    }
    values.update(overrides)
    return build_operator_candidate_portfolio_conflict_check_report(**values)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_conflict_status_vocabulary_is_exact() -> None:
    assert OPERATOR_CANDIDATE_PORTFOLIO_CONFLICT_STATUSES == (
        "clear",
        "manual_review",
        "blocked",
    )


def test_clear_report_is_readonly_deterministic_and_public_safe() -> None:
    first = report()
    second = report()

    assert type(first) is OperatorCandidatePortfolioConflictCheckReport
    assert is_dataclass(first)
    assert first.candidate_market_count == d("3")
    assert first.same_event_family_count == d("0")
    assert first.opposing_outcome_count == d("0")
    assert first.correlated_risk_count == d("0")
    assert first.manual_conflict_limit_count == d("3")
    assert first.conflict_status == "clear"
    assert first.reason_codes == ("candidate_portfolio_conflict_clear",)
    assert first.manual_next_step == "manual_monitor_candidate_portfolio"
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = operator_candidate_portfolio_conflict_check_report_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "candidate_market_count": "3",
        "same_event_family_count": "0",
        "opposing_outcome_count": "0",
        "correlated_risk_count": "0",
        "manual_conflict_limit_count": "3",
        "conflict_status": "clear",
        "reason_codes": ["candidate_portfolio_conflict_clear"],
        "manual_next_step": "manual_monitor_candidate_portfolio",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert second.payload_digest == expected_digest
    assert operator_candidate_portfolio_conflict_check_report_payload_digest(first) == (
        expected_digest
    )
    assert (
        validate_operator_candidate_portfolio_conflict_check_public_payload(payload)
        == payload
    )
    assert_no_runtime_numbers(payload)


def test_manual_review_status_reports_candidate_conflicts_without_execution() -> None:
    result = report(same_event_family_count=d("1"), correlated_risk_count=d("2"))

    assert result.conflict_status == "manual_review"
    assert result.reason_codes == (
        "candidate_portfolio_same_event_family_conflict",
        "candidate_portfolio_correlated_risk_conflict",
    )
    assert result.manual_next_step == "manual_review_candidate_portfolio_conflicts"
    assert result.public_payload["conflict_status"] == "manual_review"


def test_blocked_status_when_opposing_outcomes_or_manual_limit_breach() -> None:
    opposing = report(opposing_outcome_count=d("1"))
    limit = report(
        candidate_market_count=d("4"),
        manual_conflict_limit_count=d("3"),
        same_event_family_count=d("1"),
    )

    assert opposing.conflict_status == "blocked"
    assert opposing.reason_codes == (
        "candidate_portfolio_opposing_outcome_conflict",
    )
    assert opposing.manual_next_step == "manual_block_candidate_portfolio_until_resolved"

    assert limit.conflict_status == "blocked"
    assert limit.reason_codes == (
        "candidate_portfolio_same_event_family_conflict",
        "candidate_portfolio_manual_conflict_limit_exceeded",
    )
    assert limit.manual_next_step == "manual_block_candidate_portfolio_until_resolved"


def test_dataclass_is_frozen_exact_type_and_decimal_only() -> None:
    result = report()

    assert is_dataclass(OperatorCandidatePortfolioConflictCheckReport)
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.conflict_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(OperatorCandidatePortfolioConflictCheckReport):
            pass

    with pytest.raises(ValueError, match="candidate_market_count"):
        report(candidate_market_count=3)
    with pytest.raises(ValueError, match="same_event_family_count"):
        report(same_event_family_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="manual_conflict_limit_count"):
        report(manual_conflict_limit_count=d("-1"))
    with pytest.raises(ValueError, match="integer"):
        report(candidate_market_count=d("1.500000"))
    with pytest.raises(ValueError, match="report must be exactly"):
        operator_candidate_portfolio_conflict_check_report_payload(
            replace(result, conflict_status="manual_review"),
        )

    hints = get_type_hints(OperatorCandidatePortfolioConflictCheckReport)
    for field_name in (
        "candidate_market_count",
        "same_event_family_count",
        "opposing_outcome_count",
        "correlated_risk_count",
        "manual_conflict_limit_count",
    ):
        assert hints[field_name] is Decimal

    for field in fields(result):
        value = getattr(result, field.name)
        if field.name.endswith("_count"):
            assert type(value) is Decimal


def test_manual_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        OperatorCandidatePortfolioConflictCheckReport(
            candidate_market_count=d("3"),
            same_event_family_count=d("1"),
            opposing_outcome_count=d("0"),
            correlated_risk_count=d("0"),
            manual_conflict_limit_count=d("3"),
            conflict_status="manual_review",
            reason_codes=("candidate_portfolio_conflict_clear",),
            manual_next_step="manual_review_candidate_portfolio_conflicts",
        )


def test_payload_tamper_checks_digest_changes_and_no_live_io_surface() -> None:
    ready = report()
    manual = report(same_event_family_count=d("1"))
    blocked = report(opposing_outcome_count=d("1"))
    payload = dict(ready.public_payload)

    assert ready.payload_digest != manual.payload_digest
    assert ready.payload_digest != blocked.payload_digest

    with pytest.raises(ValueError, match="candidate_market_count"):
        validate_operator_candidate_portfolio_conflict_check_public_payload(
            {**payload, "candidate_market_count": "4"},
        )
    with pytest.raises(ValueError, match="conflict_status"):
        validate_operator_candidate_portfolio_conflict_check_public_payload(
            {**payload, "conflict_status": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_operator_candidate_portfolio_conflict_check_public_payload(
            {**payload, "paper_only": False},
        )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "sqlite3",
        "supabase",
        "jsonl",
        "open(",
        "private_key",
        "secret",
        "wallet",
        "auth",
        "signature",
        "sign_order",
        "live_trading",
        "submit_order",
        "cancel_order",
        "execute_order",
        "auto_execute",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

    assert not float_constants
    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "psycopg",
            "supabase",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "cursor",
            "delete",
            "execute",
            "executemany",
            "fetch",
            "insert",
            "open",
            "post",
            "put",
            "rollback",
            "send",
            "sign",
            "submit",
            "upsert",
            "write",
            "write_text",
            "write_bytes",
        },
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "wallet" not in lowered
        assert "auth" not in lowered
        assert "order" not in lowered
        assert "trade" not in lowered
