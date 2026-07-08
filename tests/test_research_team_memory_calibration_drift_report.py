from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_memory_calibration_drift_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_memory_calibration_drift_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-memory-calibration-drift-report-test",
        "min_recent_outcome_sample_count": d("12"),
        "calibration_error_watch_threshold": d("0.075000"),
        "calibration_error_block_threshold": d("0.150000"),
        "stale_memory_pressure_watch_threshold": d("0.450000"),
        "stale_memory_pressure_block_threshold": d("0.800000"),
        "unresolved_feedback_backlog_watch_threshold": d("3"),
        "unresolved_feedback_backlog_block_threshold": d("8"),
        "manual_recheck_urgency_watch_threshold": d("0.500000"),
        "manual_recheck_urgency_block_threshold": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchTeamMemoryCalibrationDriftConfig(**values)


def fact(**overrides: object):
    module = api()
    values = {
        "domain_team": "macro-rates",
        "recent_outcome_sample_count": d("30"),
        "calibration_error": d("0.040000"),
        "stale_memory_pressure": d("0.150000"),
        "unresolved_feedback_backlog": d("1"),
        "manual_recheck_urgency": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchTeamMemoryCalibrationFact(**values)


def build_report(*facts: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_memory_calibration_drift_report(
        facts,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected primitive numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_builds_deterministic_report_with_pass_watch_and_block_statuses() -> None:
    report = build_report(
        fact(
            domain_team="sports",
            recent_outcome_sample_count=d("40"),
            calibration_error=d("0.030000"),
            stale_memory_pressure=d("0.100000"),
            unresolved_feedback_backlog=d("0"),
            manual_recheck_urgency=d("0.100000"),
        ),
        fact(
            domain_team="macro-rates",
            recent_outcome_sample_count=d("24"),
            calibration_error=d("0.080000"),
            stale_memory_pressure=d("0.500000"),
            unresolved_feedback_backlog=d("4"),
            manual_recheck_urgency=d("0.600000"),
        ),
        fact(
            domain_team="crypto",
            recent_outcome_sample_count=d("6"),
            calibration_error=d("0.180000"),
            stale_memory_pressure=d("0.900000"),
            unresolved_feedback_backlog=d("9"),
            manual_recheck_urgency=d("0.850000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.domain_team_count == d("3")
    assert report.recent_outcome_sample_count == d("70")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_calibration_error == d("0.060000")
    assert report.average_stale_memory_pressure == d("0.305714")
    assert report.total_unresolved_feedback_backlog == d("13")
    assert report.max_manual_recheck_urgency == d("0.850000")
    assert tuple(row.domain_team for row in report.rows) == (
        "sports",
        "macro-rates",
        "crypto",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert report.rows[0].reason_codes == ("memory_calibration_drift_pass",)
    assert report.rows[1].reason_codes == (
        "calibration_error_watch",
        "stale_memory_pressure_watch",
        "unresolved_feedback_backlog_watch",
        "manual_recheck_urgency_watch",
        "memory_calibration_drift_watch",
    )
    assert report.rows[2].reason_codes == (
        "insufficient_recent_outcome_sample_count",
        "calibration_error_block",
        "stale_memory_pressure_block",
        "unresolved_feedback_backlog_block",
        "manual_recheck_urgency_block",
        "memory_calibration_drift_block",
    )
    assert report.reason_codes == (
        "insufficient_recent_outcome_sample_count",
        "calibration_error_block",
        "stale_memory_pressure_block",
        "unresolved_feedback_backlog_block",
        "manual_recheck_urgency_block",
        "calibration_error_watch",
        "stale_memory_pressure_watch",
        "unresolved_feedback_backlog_watch",
        "manual_recheck_urgency_watch",
        "memory_calibration_drift_block",
        "memory_calibration_drift_watch",
    )


def test_empty_fact_set_blocks_report_only_summary() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.domain_team_count == d("0")
    assert report.recent_outcome_sample_count == d("0")
    assert report.average_calibration_error is None
    assert report.average_stale_memory_pressure is None
    assert report.total_unresolved_feedback_backlog == d("0")
    assert report.max_manual_recheck_urgency is None
    assert report.rows == ()
    assert report.reason_codes == ("no_team_memory_calibration_facts",)
    assert report.reason_code_counts[0].reason_code == "no_team_memory_calibration_facts"
    assert report.reason_code_counts[0].count == d("1")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_canonical_digest_bound_and_redacts_private_surfaces() -> None:
    module = api()
    report = build_report(fact())

    payload = module.research_team_memory_calibration_drift_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "pass"
    assert payload["recent_outcome_sample_count"] == "30"
    assert payload["average_calibration_error"] == "0.040000"
    assert payload["rows"][0]["domain_team"] == "macro-rates"
    assert payload["rows"][0]["calibration_error"] == "0.040000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "private",
        "wallet",
        "order",
        "recommendation",
        "sizing",
        "http://",
        "https://",
    )
    assert all(fragment not in encoded.lower() for fragment in forbidden_fragments)

    tampered = dict(payload)
    tampered["average_calibration_error"] = "0.050000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_memory_calibration_drift_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["source_url"] = "https://private.example/source"
    unsafe["derived_validation_digest"] = canonical_digest(unsafe)
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_memory_calibration_drift_report_payload(unsafe)


def test_validation_rejects_non_decimal_bad_statuses_unsafe_values_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at"):
        build_report(fact(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(fact(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="config"):
        module.build_research_team_memory_calibration_drift_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="domain_team"):
        fact(domain_team="https://private.example/team")
    with pytest.raises(ValueError, match="recent_outcome_sample_count"):
        fact(recent_outcome_sample_count=12)
    with pytest.raises(ValueError, match="calibration_error"):
        fact(calibration_error=0.1)
    with pytest.raises(ValueError, match="stale_memory_pressure"):
        fact(stale_memory_pressure=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="unresolved_feedback_backlog"):
        fact(unresolved_feedback_backlog=d("1.5"))
    with pytest.raises(ValueError, match="manual_recheck_urgency"):
        fact(manual_recheck_urgency=Decimal("NaN"))
    with pytest.raises(ValueError, match="block threshold"):
        config(calibration_error_watch_threshold=d("0.200000"))
    with pytest.raises(ValueError, match="facts"):
        build_report(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_team values must be unique"):
        build_report(fact(domain_team="macro-rates"), fact(domain_team="macro-rates"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(fact(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(build_report(fact()), status="blocked")
    with pytest.raises(TypeError):
        type("FactSubclass", (module.ResearchTeamMemoryCalibrationFact,), {})


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    report = build_report(fact())
    items = (
        config(),
        fact(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for item in items:
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    assert module.research_team_memory_calibration_drift_report_digest(report) == (
        report.derived_validation_digest
    )


def test_owned_module_has_no_db_network_wallet_order_sizing_or_recommendation_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    field_names: list[str] = []
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
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            field_names.append(node.target.id)
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
        "os",
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
        "persist",
        "rollback",
        "send",
        "write",
    }
    forbidden_field_names = {
        "account_id",
        "auth_token",
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "order_id",
        "private_token",
        "raw_candidate_id",
        "raw_market_id",
        "source_text",
        "source_url",
        "wallet_address",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert not any(name in forbidden_field_names for name in field_names)
    assert_no_float_or_int_values([imports, call_names, attribute_names, field_names])
