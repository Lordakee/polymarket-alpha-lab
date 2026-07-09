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
    "src/polymarket_alpha_lab/research_team_specialist_workload_pressure_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_workload_pressure_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-team-specialist-workload-pressure-report-v0",
        "max_pass_pending_packet_count": d("5"),
        "max_watch_pending_packet_count": d("12"),
        "min_pass_reviewer_available_count": d("2"),
        "min_watch_reviewer_available_count": d("1"),
        "max_pass_sla_age_hours": d("8.000000"),
        "max_watch_sla_age_hours": d("24.000000"),
        "max_pass_unresolved_escalation_count": d("0"),
        "max_watch_unresolved_escalation_count": d("2"),
        "max_pass_memory_writeback_delay_hours": d("12.000000"),
        "max_watch_memory_writeback_delay_hours": d("48.000000"),
    }
    values.update(overrides)
    return report.ResearchTeamSpecialistWorkloadPressureConfig(**values)


def workload_signal(**overrides: object):
    report = api()
    values = {
        "team_key": "macro_rates",
        "team_domain": "macro",
        "observed_at": GENERATED_AT - timedelta(minutes=30),
        "pending_packet_count": d("2"),
        "reviewer_available_count": d("3"),
        "oldest_sla_age_hours": d("2.000000"),
        "unresolved_escalation_count": d("0"),
        "memory_writeback_delay_hours": d("5.000000"),
    }
    values.update(overrides)
    return report.ResearchTeamSpecialistWorkloadPressureInput(**values)


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_team_specialist_workload_pressure_report(
        items,
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


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def redigested_payload(payload: dict[str, Any]) -> dict[str, Any]:
    report = api()
    payload["derived_validation_digest"] = report._payload_validation_digest(payload)
    return payload


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal
        if field.name.endswith(("_count", "_hours", "_seconds", "_ratio")):
            assert type(item) is Decimal


def test_workload_pressure_report_rolls_up_pass_watch_and_block_teams() -> None:
    summary = build_report(
        workload_signal(
            team_key="sports_soccer",
            team_domain="sports",
        ),
        workload_signal(
            team_key="macro_rates",
            team_domain="macro",
            observed_at=GENERATED_AT - timedelta(hours=2),
            pending_packet_count=d("14"),
            reviewer_available_count=d("0"),
            oldest_sla_age_hours=d("26.000000"),
            unresolved_escalation_count=d("3"),
            memory_writeback_delay_hours=d("50.000000"),
        ),
        workload_signal(
            team_key="crypto_policy",
            team_domain="crypto",
            observed_at=GENERATED_AT - timedelta(hours=1),
            pending_packet_count=d("7"),
            reviewer_available_count=d("1"),
            oldest_sla_age_hours=d("12.000000"),
            unresolved_escalation_count=d("1"),
            memory_writeback_delay_hours=d("24.000000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == "research-team-specialist-workload-pressure-report-v0"
    assert summary.status == "block"
    assert summary.paper_queue_action == "paper_specialist_workload_block"
    assert summary.specialist_team_count == d("3")
    assert summary.pass_count == d("1")
    assert summary.watch_count == d("1")
    assert summary.block_count == d("1")
    assert summary.overloaded_team_count == d("2")
    assert summary.total_pending_packet_count == d("23")
    assert summary.total_reviewer_available_count == d("4")
    assert summary.pending_packet_pressure_team_count == d("2")
    assert summary.reviewer_gap_team_count == d("2")
    assert summary.sla_breach_team_count == d("2")
    assert summary.unresolved_escalation_team_count == d("2")
    assert summary.memory_writeback_delay_team_count == d("2")
    assert summary.max_pending_packet_count == d("14")
    assert summary.min_reviewer_available_count == d("0")
    assert summary.max_sla_age_hours == d("26.000000")
    assert summary.max_unresolved_escalation_count == d("3")
    assert summary.max_memory_writeback_delay_hours == d("50.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    blocked, watched, passed = summary.rows
    assert tuple((row.workload_status, row.team_domain) for row in summary.rows) == (
        ("block", "macro"),
        ("watch", "crypto"),
        ("pass", "sports"),
    )
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.reason_codes == (
        "specialist_workload_pending_packet_block",
        "specialist_workload_reviewer_availability_block",
        "specialist_workload_sla_age_block",
        "specialist_workload_unresolved_escalation_block",
        "specialist_workload_memory_writeback_block",
    )
    assert watched.reason_codes == (
        "specialist_workload_pending_packet_watch",
        "specialist_workload_reviewer_availability_watch",
        "specialist_workload_sla_age_watch",
        "specialist_workload_unresolved_escalation_watch",
        "specialist_workload_memory_writeback_watch",
    )
    assert passed.reason_codes == ("specialist_workload_clear",)
    assert summary.reason_codes == (
        "specialist_workload_report_block",
        "specialist_workload_pending_packet_block",
        "specialist_workload_reviewer_availability_block",
        "specialist_workload_sla_age_block",
        "specialist_workload_unresolved_escalation_block",
        "specialist_workload_memory_writeback_block",
        "specialist_workload_pending_packet_watch",
        "specialist_workload_reviewer_availability_watch",
        "specialist_workload_sla_age_watch",
        "specialist_workload_unresolved_escalation_watch",
        "specialist_workload_memory_writeback_watch",
    )
    assert summary.reason_code_counts[-1].reason_code == "specialist_workload_clear"
    assert summary.reason_code_counts[-1].count == d("1")
    assert summary.reason_code_counts[-1].team_ratio == d("0.333333")
    assert len(summary.derived_validation_digest) == 64


def test_empty_workload_pressure_report_blocks_without_team_rows() -> None:
    summary = build_report()

    assert summary.status == "block"
    assert summary.paper_queue_action == "paper_specialist_workload_block"
    assert summary.specialist_team_count == d("0")
    assert summary.pass_count == d("0")
    assert summary.watch_count == d("0")
    assert summary.block_count == d("0")
    assert summary.overloaded_team_count == d("0")
    assert summary.total_pending_packet_count == d("0")
    assert summary.total_reviewer_available_count == d("0")
    assert summary.min_reviewer_available_count == d("0")
    assert summary.rows == ()
    assert summary.reason_codes == ("specialist_workload_no_teams",)
    assert summary.reason_code_counts == (
        api().ResearchTeamSpecialistWorkloadPressureReasonCodeCount(
            reason_code="specialist_workload_no_teams",
            count=d("1"),
            team_ratio=d("1.000000"),
        ),
    )


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    report = api()
    first = build_report(
        workload_signal(team_key="sports_soccer", team_domain="sports"),
        workload_signal(
            team_key="crypto_policy",
            team_domain="crypto",
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
            pending_packet_count=d("7"),
            reviewer_available_count=d("1"),
            oldest_sla_age_hours=d("12.000000"),
            unresolved_escalation_count=d("1"),
            memory_writeback_delay_hours=d("24.000000"),
        ),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        workload_signal(
            team_key="crypto_policy",
            team_domain="crypto",
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
            pending_packet_count=d("7"),
            reviewer_available_count=d("1"),
            oldest_sla_age_hours=d("12.000000"),
            unresolved_escalation_count=d("1"),
            memory_writeback_delay_hours=d("24.000000"),
        ),
        workload_signal(team_key="sports_soccer", team_domain="sports"),
    )

    payload = report.research_team_specialist_workload_pressure_report_payload(first)
    repeat_payload = report.research_team_specialist_workload_pressure_report_payload(
        second,
    )

    assert first.generated_at == GENERATED_AT
    assert payload == repeat_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["specialist_team_count"] == "2"
    assert payload["rows"][0]["team_key"] == "crypto_policy"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_numeric = not any(type(value) in (int, float) for value in walk_values(payload))
    assert assert_no_numeric
    json.dumps(payload, sort_keys=True)

    unsafe_fragments = (
        "market",
        "source",
        "recommendation",
        "sizing",
        "order",
        "wallet",
        "auth",
        "trade",
        "live",
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in unsafe_fragments
    )
    payload_text = repr(payload).lower()
    assert not any(fragment in payload_text for fragment in unsafe_fragments)

    tampered = dict(payload)
    tampered["total_pending_packet_count"] = "99"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_team_specialist_workload_pressure_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2"))


def test_custom_config_and_public_contract_validation() -> None:
    report = api()
    relaxed = config(
        max_pass_pending_packet_count=d("8"),
        max_watch_pending_packet_count=d("12"),
        min_pass_reviewer_available_count=d("1"),
        min_watch_reviewer_available_count=d("0"),
        max_pass_sla_age_hours=d("12.000000"),
        max_watch_sla_age_hours=d("24.000000"),
        max_pass_unresolved_escalation_count=d("1"),
        max_watch_unresolved_escalation_count=d("2"),
        max_pass_memory_writeback_delay_hours=d("24.000000"),
        max_watch_memory_writeback_delay_hours=d("48.000000"),
    )
    summary = build_report(
        workload_signal(
            pending_packet_count=d("7"),
            reviewer_available_count=d("1"),
            oldest_sla_age_hours=d("12.000000"),
            unresolved_escalation_count=d("1"),
            memory_writeback_delay_hours=d("24.000000"),
        ),
        cfg=relaxed,
    )

    assert report.STATUSES == ("pass", "watch", "block")
    assert "blocked" not in report.STATUSES
    assert summary.status == "pass"
    assert summary.rows[0].workload_status == "pass"
    assert summary.rows[0].reason_codes == ("specialist_workload_clear",)

    with pytest.raises(ValueError, match="max_watch_pending_packet_count"):
        config(
            max_pass_pending_packet_count=d("12"),
            max_watch_pending_packet_count=d("5"),
        )
    with pytest.raises(ValueError, match="min_watch_reviewer_available_count"):
        config(
            min_pass_reviewer_available_count=d("1"),
            min_watch_reviewer_available_count=d("2"),
        )
    with pytest.raises(ValueError, match="Decimal"):
        workload_signal(pending_packet_count=2)
    with pytest.raises(ValueError, match="Decimal"):
        workload_signal(oldest_sla_age_hours=2.0)
    with pytest.raises(ValueError, match="Decimal"):
        workload_signal(memory_writeback_delay_hours=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="integral"):
        workload_signal(reviewer_available_count=d("1.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        workload_signal(observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="observed_at"):
        workload_signal(
            observed_at=_DateTimeSubclass(2026, 7, 8, 11, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        build_report(workload_signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="team_key"):
        workload_signal(team_key="market_slug")
    with pytest.raises(ValueError, match="team_domain"):
        workload_signal(team_domain="source_family")
    with pytest.raises(ValueError, match="unique"):
        build_report(workload_signal(), workload_signal())
    with pytest.raises(ValueError, match="paper_only"):
        workload_signal(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_report(workload_signal(), cfg=object())


def test_dataclasses_are_frozen_and_materialized_fields_are_tamper_evident() -> None:
    report = api()
    cfg = config()
    signal = workload_signal()
    summary = build_report(signal, cfg=cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(signal)
    assert is_dataclass(summary)
    assert is_dataclass(summary.rows[0])
    assert is_dataclass(summary.reason_code_counts[0])

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        signal.pending_packet_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].pending_packet_count = d("4")  # type: ignore[misc]

    for value in (cfg, signal, summary, *summary.rows, *summary.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_decimal_public_fields(value)

    with pytest.raises(ValueError, match="workload_status"):
        report.ResearchTeamSpecialistWorkloadPressureRow(
            **{
                **summary.rows[0].__dict__,
                "workload_status": "block",
            },
        )
    with pytest.raises(ValueError, match="status"):
        report.ResearchTeamSpecialistWorkloadPressureReport(
            **{
                **summary.__dict__,
                "status": "block",
            },
        )

    object.__setattr__(summary.rows[0], "pending_packet_count", d("99"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_team_specialist_workload_pressure_report_payload(summary)


def test_public_payload_rejects_raw_identifiers_unsafe_flags_and_numbers() -> None:
    report = api()
    payload = report.research_team_specialist_workload_pressure_report_payload(
        build_report(workload_signal()),
    )

    for key in (
        "candidate_id",
        "raw_slug",
        "resolution_question",
        "raw_url",
        "dsn",
        "market_slug",
        "source_reference",
        "source_url",
        "raw_text",
        "table_name",
        "token",
        "recommendation_id",
        "position_sizing",
        "order_id",
        "wallet_address",
        "auth_header",
        "trade_id",
        "live_url",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_team_specialist_workload_pressure_report_payload(unsafe)

    for value in (
        "candidate id",
        "event slug",
        "resolution question",
        "raw url",
        "raw dsn",
        "market slug",
        "source reference",
        "source text",
        "table name",
        "bearer token",
        "wallet signer",
        "auth token",
        "order route",
        "trade route",
        "live execution",
        "recommendation",
        "sizing",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            report.research_team_specialist_workload_pressure_report_payload(unsafe)

    numeric = dict(payload)
    numeric["specialist_team_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        report.research_team_specialist_workload_pressure_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        report.research_team_specialist_workload_pressure_report_payload(downgraded)

    nested_downgraded = json.loads(json.dumps(payload))
    nested_downgraded["rows"][0]["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(nested_downgraded),
        )

    invalid_report_status = json.loads(json.dumps(payload))
    invalid_report_status["status"] = "blocked"
    with pytest.raises(ValueError, match="status"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(invalid_report_status),
        )

    invalid_row_status = json.loads(json.dumps(payload))
    invalid_row_status["rows"][0]["workload_status"] = "blocked"
    with pytest.raises(ValueError, match="workload_status"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(invalid_row_status),
        )


def test_public_payload_rejects_redigested_schema_drift() -> None:
    report = api()
    payload = report.research_team_specialist_workload_pressure_report_payload(
        build_report(workload_signal()),
    )

    extra_key = json.loads(json.dumps(payload))
    extra_key["safe_extra_field"] = "safe_extra_value"
    with pytest.raises(ValueError, match="unexpected"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(extra_key),
        )

    missing_key = json.loads(json.dumps(payload))
    del missing_key["total_pending_packet_count"]
    with pytest.raises(ValueError, match="required"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(missing_key),
        )

    invalid_decimal = json.loads(json.dumps(payload))
    invalid_decimal["specialist_team_count"] = "not_decimal"
    with pytest.raises(ValueError, match="Decimal"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(invalid_decimal),
        )

    invalid_reason_code = json.loads(json.dumps(payload))
    invalid_reason_code["rows"][0]["reason_codes"] = [
        "specialist_workload_safe_unknown",
    ]
    with pytest.raises(ValueError, match="reason_code"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(invalid_reason_code),
        )

    mismatched_rollup = json.loads(json.dumps(payload))
    mismatched_rollup["pass_count"] = "0"
    with pytest.raises(ValueError, match="pass_count"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(mismatched_rollup),
        )

    invalid_config_version = json.loads(json.dumps(payload))
    invalid_config_version["config_version"] = (
        "research-team-specialist-workload-pressure-report-v1"
    )
    with pytest.raises(ValueError, match="config_version"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(invalid_config_version),
        )

    mismatched_row_generated_at = json.loads(json.dumps(payload))
    mismatched_row_generated_at["rows"][0]["generated_at"] = (
        "2026-07-08T12:00:01+00:00"
    )
    mismatched_row_generated_at["rows"][0]["observation_age_seconds"] = "1801.000000"
    with pytest.raises(ValueError, match="generated_at"):
        report.research_team_specialist_workload_pressure_report_payload(
            redigested_payload(mismatched_row_generated_at),
        )


def test_module_is_report_only_without_external_write_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
        "write_text",
        "write_bytes",
        "float",
        "__import__",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
