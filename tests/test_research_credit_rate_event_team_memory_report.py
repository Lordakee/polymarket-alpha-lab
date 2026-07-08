from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_credit_rate_event_team_memory_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def _api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_credit_rate_event_team_memory_report",
    )


def _team(
    api: Any,
    team_label: str,
    event_family_label: str,
    *,
    memory_fresh_count: Decimal,
    memory_total_count: Decimal,
    policy_fresh_count: Decimal,
    policy_reference_count: Decimal,
    evidence_reuse_count: Decimal,
    evidence_case_count: Decimal,
    calibration_ready_count: Decimal,
    calibration_target_count: Decimal,
) -> Any:
    return api.ResearchCreditRateEventTeamMemoryInput(
        team_label=team_label,
        event_family_label=event_family_label,
        memory_fresh_count=memory_fresh_count,
        memory_total_count=memory_total_count,
        policy_fresh_count=policy_fresh_count,
        policy_reference_count=policy_reference_count,
        evidence_reuse_count=evidence_reuse_count,
        evidence_case_count=evidence_case_count,
        calibration_ready_count=calibration_ready_count,
        calibration_target_count=calibration_target_count,
    )


def test_builds_credit_rates_event_memory_readiness_report() -> None:
    api = _api()

    report = api.build_research_credit_rate_event_team_memory_report(
        (
            _team(
                api,
                "credit_rates_policy",
                "fomc_target_rate",
                memory_fresh_count=Decimal("5"),
                memory_total_count=Decimal("5"),
                policy_fresh_count=Decimal("6"),
                policy_reference_count=Decimal("6"),
                evidence_reuse_count=Decimal("4"),
                evidence_case_count=Decimal("4"),
                calibration_ready_count=Decimal("5"),
                calibration_target_count=Decimal("5"),
            ),
            _team(
                api,
                "sofr_curve",
                "term_rate",
                memory_fresh_count=Decimal("3"),
                memory_total_count=Decimal("4"),
                policy_fresh_count=Decimal("4"),
                policy_reference_count=Decimal("5"),
                evidence_reuse_count=Decimal("2"),
                evidence_case_count=Decimal("3"),
                calibration_ready_count=Decimal("3"),
                calibration_target_count=Decimal("4"),
            ),
            _team(
                api,
                "central_bank_credit",
                "lending_conditions",
                memory_fresh_count=Decimal("2"),
                memory_total_count=Decimal("5"),
                policy_fresh_count=Decimal("2"),
                policy_reference_count=Decimal("5"),
                evidence_reuse_count=Decimal("1"),
                evidence_case_count=Decimal("5"),
                calibration_ready_count=Decimal("2"),
                calibration_target_count=Decimal("5"),
            ),
        ),
        config=api.ResearchCreditRateEventTeamMemoryReportConfig(),
        generated_at=GENERATED_AT,
    )

    assert type(report) is api.ResearchCreditRateEventTeamMemoryReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_RESEARCH_CREDIT_RATE_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.team_count == Decimal("3.000000")
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert report.average_readiness_score == Decimal("0.697222")
    assert report.lowest_memory_readiness_ratio == Decimal("0.400000")
    assert report.lowest_policy_freshness_ratio == Decimal("0.400000")
    assert report.lowest_evidence_reuse_ratio == Decimal("0.200000")
    assert report.lowest_calibration_readiness_ratio == Decimal("0.400000")
    assert report.reason_codes == (
        "credit_rate_event_team_memory_block_teams_present",
        "credit_rate_event_team_memory_watch_teams_present",
    )
    assert report.reason_code_counts == (
        api.ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code="credit_rate_event_team_memory_memory_readiness_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code="credit_rate_event_team_memory_policy_freshness_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code="credit_rate_event_team_memory_evidence_reuse_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code="credit_rate_event_team_memory_calibration_readiness_block",
            count=Decimal("1.000000"),
        ),
        api.ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code="credit_rate_event_team_memory_memory_readiness_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code="credit_rate_event_team_memory_policy_freshness_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code="credit_rate_event_team_memory_evidence_reuse_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code="credit_rate_event_team_memory_calibration_readiness_watch",
            count=Decimal("1.000000"),
        ),
        api.ResearchCreditRateEventTeamMemoryReasonCodeCount(
            reason_code="credit_rate_event_team_memory_ready",
            count=Decimal("1.000000"),
        ),
    )
    assert tuple((row.team_label, row.event_family_label, row.status) for row in report.rows) == (
        ("central_bank_credit", "lending_conditions", "block"),
        ("credit_rates_policy", "fomc_target_rate", "pass"),
        ("sofr_curve", "term_rate", "watch"),
    )

    blocked = report.rows[0]
    assert blocked.memory_readiness_ratio == Decimal("0.400000")
    assert blocked.policy_freshness_ratio == Decimal("0.400000")
    assert blocked.evidence_reuse_ratio == Decimal("0.200000")
    assert blocked.calibration_readiness_ratio == Decimal("0.400000")
    assert blocked.readiness_score == Decimal("0.350000")
    assert blocked.reason_codes == (
        "credit_rate_event_team_memory_memory_readiness_block",
        "credit_rate_event_team_memory_policy_freshness_block",
        "credit_rate_event_team_memory_evidence_reuse_block",
        "credit_rate_event_team_memory_calibration_readiness_block",
    )
    watched = report.rows[2]
    assert watched.readiness_score == Decimal("0.741667")
    assert watched.reason_codes == (
        "credit_rate_event_team_memory_memory_readiness_watch",
        "credit_rate_event_team_memory_policy_freshness_watch",
        "credit_rate_event_team_memory_evidence_reuse_watch",
        "credit_rate_event_team_memory_calibration_readiness_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_payload_digest_is_deterministic_decimal_only_and_aggregate_safe() -> None:
    api = _api()
    first_rows = (
        _team(
            api,
            "sofr_curve",
            "term_rate",
            memory_fresh_count=Decimal("3"),
            memory_total_count=Decimal("4"),
            policy_fresh_count=Decimal("4"),
            policy_reference_count=Decimal("5"),
            evidence_reuse_count=Decimal("2"),
            evidence_case_count=Decimal("3"),
            calibration_ready_count=Decimal("3"),
            calibration_target_count=Decimal("4"),
        ),
        _team(
            api,
            "credit_rates_policy",
            "fomc_target_rate",
            memory_fresh_count=Decimal("5"),
            memory_total_count=Decimal("5"),
            policy_fresh_count=Decimal("6"),
            policy_reference_count=Decimal("6"),
            evidence_reuse_count=Decimal("4"),
            evidence_case_count=Decimal("4"),
            calibration_ready_count=Decimal("5"),
            calibration_target_count=Decimal("5"),
        ),
    )

    report = api.build_research_credit_rate_event_team_memory_report(
        first_rows,
        config=api.ResearchCreditRateEventTeamMemoryReportConfig(),
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    rebuilt = api.build_research_credit_rate_event_team_memory_report(
        tuple(reversed(first_rows)),
        config=api.ResearchCreditRateEventTeamMemoryReportConfig(),
        generated_at=GENERATED_AT,
    )

    assert rebuilt.derived_validation_digest == report.derived_validation_digest
    assert api.research_credit_rate_event_team_memory_report_digest(report) == (
        report.derived_validation_digest
    )
    assert all(
        character in "0123456789abcdef"
        for character in report.derived_validation_digest
    )

    payload = api.research_credit_rate_event_team_memory_report_payload(report)
    assert api.research_credit_rate_event_team_memory_report_payload(payload) == payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["team_count"] == "2.000000"
    assert payload["average_readiness_score"] == "0.870834"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["team_label"] == "credit_rates_policy"
    assert payload["rows"][0]["policy_reference_count"] == "6.000000"
    assert payload["rows"][0]["paper_only"] is True
    encoded = json.dumps(payload, sort_keys=True)
    assert "team_id" not in encoded
    assert "user_id" not in encoded
    assert "account" not in encoded
    assert "source_key" not in encoded
    assert "market_slug" not in encoded
    _assert_no_int_or_float_values(payload)


def test_validates_decimal_inputs_flags_safe_labels_and_digest_consistency() -> None:
    api = _api()
    report = api.build_research_credit_rate_event_team_memory_report(
        (
            _team(
                api,
                "credit_rates_policy",
                "fomc_target_rate",
                memory_fresh_count=Decimal("1"),
                memory_total_count=Decimal("1"),
                policy_fresh_count=Decimal("1"),
                policy_reference_count=Decimal("1"),
                evidence_reuse_count=Decimal("1"),
                evidence_case_count=Decimal("1"),
                calibration_ready_count=Decimal("1"),
                calibration_target_count=Decimal("1"),
            ),
        ),
        config=api.ResearchCreditRateEventTeamMemoryReportConfig(),
        generated_at=GENERATED_AT,
    )

    assert is_dataclass(report)
    assert {row.status for row in report.rows} <= {"pass", "watch", "block"}
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="memory_fresh_count must be a Decimal"):
        replace(report.rows[0], memory_fresh_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_fresh_count must not exceed"):
        replace(report.rows[0], memory_fresh_count=Decimal("2.000000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_research_credit_rate_event_team_memory_report(
            (),
            config=api.ResearchCreditRateEventTeamMemoryReportConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="policy_freshness_watch_threshold must be a Decimal"):
        api.ResearchCreditRateEventTeamMemoryReportConfig(
            policy_freshness_watch_threshold=_DecimalSubclass("0.850000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(api.ResearchCreditRateEventTeamMemoryReportConfig(), paper_only=False)
    with pytest.raises(ValueError, match="team_label must be public"):
        _team(
            api,
            "wal" "let-team",
            "fomc_target_rate",
            memory_fresh_count=Decimal("1"),
            memory_total_count=Decimal("1"),
            policy_fresh_count=Decimal("1"),
            policy_reference_count=Decimal("1"),
            evidence_reuse_count=Decimal("1"),
            evidence_case_count=Decimal("1"),
            calibration_ready_count=Decimal("1"),
            calibration_target_count=Decimal("1"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, average_readiness_score=Decimal("0.500000"))
    with pytest.raises(ValueError, match="readonly"):
        api.research_credit_rate_event_team_memory_report_payload(
            {**report.payload, "readonly": False},
        )


def test_public_contract_is_frozen_decimal_only_and_report_only() -> None:
    api = _api()
    public_types = {
        "ResearchCreditRateEventTeamMemoryReportConfig",
        "ResearchCreditRateEventTeamMemoryInput",
        "ResearchCreditRateEventTeamMemoryRow",
        "ResearchCreditRateEventTeamMemoryReasonCodeCount",
        "ResearchCreditRateEventTeamMemoryReport",
    }
    for name in public_types:
        cls = getattr(api, name)
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    report = api.build_research_credit_rate_event_team_memory_report(
        (
            _team(
                api,
                "credit_rates_policy",
                "fomc_target_rate",
                memory_fresh_count=Decimal("1"),
                memory_total_count=Decimal("1"),
                policy_fresh_count=Decimal("1"),
                policy_reference_count=Decimal("1"),
                evidence_reuse_count=Decimal("1"),
                evidence_case_count=Decimal("1"),
                calibration_ready_count=Decimal("1"),
                calibration_target_count=Decimal("1"),
            ),
        ),
        config=api.ResearchCreditRateEventTeamMemoryReportConfig(),
        generated_at=GENERATED_AT,
    )
    for field_name in (
        "team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_readiness_score",
        "lowest_memory_readiness_ratio",
        "lowest_policy_freshness_ratio",
        "lowest_evidence_reuse_ratio",
        "lowest_calibration_readiness_ratio",
    ):
        assert type(getattr(report, field_name)) is Decimal
    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_score")
            ):
                assert type(value) is Decimal
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {"__import__", "eval", "exec", "open", "print"}
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name is not None:
                calls.add(name)
    assert not (imports & forbidden_import_roots)
    assert not (calls & forbidden_call_names)

    text = MODULE_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "credential",
        "private_key",
        "secret",
        "order",
        "live",
        "trade",
        "broker",
        "buy",
        "sell",
        "request",
        "submit",
        "supabase",
        "sqlite",
        "postgres",
        "insert",
        "update",
        "delete",
        "commit",
        "cursor",
    ):
        assert forbidden not in text
    assert api.__all__ == (
        "DEFAULT_RESEARCH_CREDIT_RATE_EVENT_TEAM_MEMORY_REPORT_CONFIG_VERSION",
        "STATUSES",
        "ResearchCreditRateEventTeamMemoryReportConfig",
        "ResearchCreditRateEventTeamMemoryInput",
        "ResearchCreditRateEventTeamMemoryRow",
        "ResearchCreditRateEventTeamMemoryReasonCodeCount",
        "ResearchCreditRateEventTeamMemoryReport",
        "build_research_credit_rate_event_team_memory_report",
        "research_credit_rate_event_team_memory_report_digest",
        "research_credit_rate_event_team_memory_report_payload",
    )


def _assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected numeric value {value!r}")
    if isinstance(value, dict):
        for nested_value in value.values():
            _assert_no_int_or_float_values(nested_value)
    elif isinstance(value, (list, tuple)):
        for nested_value in value:
            _assert_no_int_or_float_values(nested_value)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None
