from __future__ import annotations

import ast
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
    / "team_specialist_error_pattern_score.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
PUBLIC_STATUSES = frozenset(("pass", "watch", "block"))
FORBIDDEN_PUBLIC_TERMS = (
    "market",
    "candidate",
    "slug",
    "question",
    "url",
    "source",
    "ref",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "recommendation",
    "position",
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_error_pattern_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def record(**overrides: object):
    module = api()
    values = {
        "team_id": "team_alpha",
        "specialist_id": "rates_specialist",
        "resolved_case_count": d("20.000000"),
        "recurring_error_count": d("0.000000"),
        "overconfidence_error_ratio": d("0.020000"),
        "underreaction_error_ratio": d("0.030000"),
        "stale_model_error_ratio": d("0.010000"),
        "recent_improvement_score": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamSpecialistErrorPatternScoreInput(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_team_specialist_error_pattern_score_report(
        rows,
        config=cfg,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_public_statuses_are_limited(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("_status"):
                assert item in PUBLIC_STATUSES
                assert item not in {"ready", "blocked", "matched", "supported"}
            assert_public_statuses_are_limited(item)
    if isinstance(value, list):
        for item in value:
            assert_public_statuses_are_limited(item)


def assert_payload_has_no_forbidden_public_terms(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(term in lowered for term in FORBIDDEN_PUBLIC_TERMS)
            assert_payload_has_no_forbidden_public_terms(item)
    if isinstance(value, list):
        for item in value:
            assert_payload_has_no_forbidden_public_terms(item)
    if isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in FORBIDDEN_PUBLIC_TERMS)


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


def test_clean_history_pass_report_only_payload() -> None:
    report = build_report(record())

    assert is_dataclass(report)
    assert report.error_pattern_status == "pass"
    assert report.row_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_error_pattern_score == d("0.981500")
    assert report.reason_codes == ("error_pattern_score_pass",)

    row = report.rows[0]
    assert row.team_id == "team_alpha"
    assert row.specialist_id == "rates_specialist"
    assert row.rank == d("1.000000")
    assert row.resolved_case_depth_score == d("1.000000")
    assert row.recurring_error_control_score == d("1.000000")
    assert row.overconfidence_control_score == d("0.980000")
    assert row.underreaction_control_score == d("0.970000")
    assert row.stale_model_control_score == d("0.990000")
    assert row.error_pattern_score == d("0.981500")
    assert row.error_pattern_status == "pass"
    assert row.reason_codes == (
        "error_pattern_pass",
        "resolved_case_depth_full",
        "recurring_errors_clear",
        "overconfidence_errors_clear",
        "underreaction_errors_clear",
        "stale_model_errors_clear",
        "recent_improvement_strong",
    )

    payload = report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["average_error_pattern_score"] == "0.981500"
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)
    assert_public_statuses_are_limited(payload)
    assert_payload_has_no_forbidden_public_terms(payload)
    json.dumps(payload, sort_keys=True)


def test_recurring_error_pattern_blocks_specialist() -> None:
    report = build_report(
        record(
            resolved_case_count=d("8.000000"),
            recurring_error_count=d("5.000000"),
            overconfidence_error_ratio=d("0.700000"),
            underreaction_error_ratio=d("0.650000"),
            stale_model_error_ratio=d("0.750000"),
            recent_improvement_score=d("0.050000"),
        ),
    )

    assert report.error_pattern_status == "block"
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("1.000000")
    assert report.average_error_pattern_score == d("0.207500")
    assert report.reason_codes == ("error_pattern_score_block",)

    row = report.rows[0]
    assert row.error_pattern_status == "block"
    assert row.error_pattern_score == d("0.207500")
    assert row.reason_codes == (
        "error_pattern_block",
        "resolved_case_depth_thin",
        "recurring_errors_severe",
        "overconfidence_errors_severe",
        "underreaction_errors_severe",
        "stale_model_errors_severe",
        "recent_improvement_weak",
    )


def test_recent_improvement_keeps_recurring_pattern_on_watch() -> None:
    report = build_report(
        record(
            resolved_case_count=d("12.000000"),
            recurring_error_count=d("2.000000"),
            overconfidence_error_ratio=d("0.200000"),
            underreaction_error_ratio=d("0.160000"),
            stale_model_error_ratio=d("0.120000"),
            recent_improvement_score=d("0.950000"),
        ),
    )

    assert report.error_pattern_status == "watch"
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("0.000000")
    row = report.rows[0]
    assert row.error_pattern_status == "watch"
    assert row.error_pattern_score == d("0.729000")
    assert row.reason_codes == (
        "error_pattern_watch",
        "resolved_case_depth_watch",
        "recurring_errors_watch",
        "overconfidence_errors_clear",
        "underreaction_errors_clear",
        "stale_model_errors_clear",
        "recent_improvement_strong",
    )


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "resolved_case_count",
            _DecimalSubclass("1.000000"),
            "resolved_case_count must be exactly Decimal",
        ),
        (
            "recurring_error_count",
            d("-1.000000"),
            "recurring_error_count must be nonnegative",
        ),
        (
            "overconfidence_error_ratio",
            d("0.5000004"),
            "overconfidence_error_ratio must use six decimal places or fewer",
        ),
        (
            "stale_model_error_ratio",
            d("1.000001"),
            "stale_model_error_ratio must be between zero and one",
        ),
        (
            "recent_improvement_score",
            Decimal("NaN"),
            "recent_improvement_score must be finite",
        ),
    ),
)
def test_decimal_exact_type_rejection(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        record(**{field_name: bad_value})


@pytest.mark.parametrize(
    "bad_payload",
    (
        {"paper_only": True, "report_only": True, "readonly": True, "market_id": "x"},
        {"paper_only": True, "report_only": True, "readonly": True, "note": "buy"},
        {"paper_only": True, "report_only": True, "readonly": True, "token": "x"},
        {
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "position_sizing": "none",
        },
    ),
)
def test_leak_rejection_for_inputs_and_payloads(bad_payload: dict[str, object]) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public value"):
        record(team_id="market_alpha")
    with pytest.raises(ValueError, match="unsafe public value"):
        record(specialist_id="https://example.invalid")
    with pytest.raises(ValueError, match="unsafe public"):
        module.team_specialist_error_pattern_score_payload(bad_payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistErrorPatternScoreConfig()
    sample = record()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistErrorPatternScoreConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        record(report_only=False)


def test_input_order_does_not_change_deterministic_payload_or_digest() -> None:
    first = record(team_id="team_alpha", specialist_id="rates_specialist")
    second = record(
        team_id="team_beta",
        specialist_id="policy_specialist",
        resolved_case_count=d("12.000000"),
        recurring_error_count=d("2.000000"),
        overconfidence_error_ratio=d("0.200000"),
        underreaction_error_ratio=d("0.160000"),
        stale_model_error_ratio=d("0.120000"),
        recent_improvement_score=d("0.950000"),
    )

    left = build_report(first, second)
    right = build_report(second, first)

    assert tuple((row.team_id, row.rank) for row in left.rows) == (
        ("team_alpha", d("1.000000")),
        ("team_beta", d("2.000000")),
    )
    assert left.payload == right.payload
    assert left.derived_validation_digest == right.derived_validation_digest


def test_report_consistency_is_enforced() -> None:
    report = build_report(record())

    with pytest.raises(ValueError, match="row_count must match rows"):
        replace(report, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest does not match"):
        replace(report, derived_validation_digest="0" * 64)


def test_module_remains_pure_report_only_without_runtime_side_effect_imports() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert not imported_roots & {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "supabase",
        "psycopg2",
        "sqlalchemy",
    }

    forbidden_calls = {"insert", "upsert", "delete", "execute", "connect", "commit"}
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
    assert not called_names & forbidden_calls
