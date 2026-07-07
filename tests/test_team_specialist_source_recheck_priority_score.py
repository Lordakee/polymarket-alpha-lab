from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.team_specialist_source_recheck_priority_score"


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "source_age_hours": d("6"),
        "stale_after_hours": d("24"),
        "screening_dependency_count": d("1"),
        "conflicting_observation_count": d("0"),
        "failed_recheck_count": d("0"),
        "available_recheck_capacity_count": d("2"),
        "watch_threshold_bps": d("100.000000"),
        "block_threshold_bps": d("200.000000"),
        "reason_codes": ("scheduler_input_present",),
    }
    values.update(overrides)
    return module.TeamSpecialistSourceRecheckPriorityScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_team_specialist_source_recheck_priority_score(
        score_input() if subject is None else subject,
    )


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def test_source_recheck_priority_score_pass_watch_and_block_states() -> None:
    module = api()

    passed = score()
    watched = score(
        score_input(
            source_age_hours=d("24"),
            screening_dependency_count=d("2"),
            conflicting_observation_count=d("1"),
            available_recheck_capacity_count=d("1"),
        ),
    )
    blocked = score(
        score_input(
            source_age_hours=d("72"),
            screening_dependency_count=d("5"),
            conflicting_observation_count=d("2"),
            failed_recheck_count=d("1"),
            available_recheck_capacity_count=d("0"),
        ),
    )

    assert module.SCORE_STATUSES == ("pass", "watch", "block")
    assert passed.score_status == "pass"
    assert passed.paper_priority_score_bps == d("12.500000")
    assert passed.reason_codes == (
        "scheduler_input_present",
        "team_specialist_source_recheck_priority_score",
        "score_pass",
        "age_pressure_present",
        "dependency_pressure_present",
        "capacity_relief_applied",
        "below_watch_threshold",
    )

    assert watched.score_status == "watch"
    assert watched.paper_priority_score_bps == d("105.000000")
    assert "conflict_pressure_present" in watched.reason_codes
    assert "watch_threshold_met" in watched.reason_codes

    assert blocked.score_status == "block"
    assert blocked.staleness_ratio == d("3.000000")
    assert blocked.age_pressure_bps == d("100.000000")
    assert blocked.paper_priority_score_bps == d("275.000000")
    assert "failed_recheck_pressure_present" in blocked.reason_codes
    assert "block_threshold_met" in blocked.reason_codes


def test_decimal_type_rejection_frozen_dataclasses_and_hard_flags() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.TeamSpecialistSourceRecheckPriorityScoreInput.__dataclass_params__.frozen
    assert module.TeamSpecialistSourceRecheckPriorityScoreResult.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.source_age_hours = d("7")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.score_status = "watch"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="source_age_hours must be a Decimal"):
        score_input(source_age_hours=6)
    with pytest.raises(ValueError, match="source_age_hours must be a Decimal"):
        score_input(source_age_hours=DecimalSubclass("6"))
    with pytest.raises(ValueError, match="stale_after_hours must be positive"):
        score_input(stale_after_hours=d("0"))
    with pytest.raises(ValueError, match="screening_dependency_count must be integral"):
        score_input(screening_dependency_count=d("1.5"))
    with pytest.raises(ValueError, match="block_threshold_bps must be greater than"):
        score_input(watch_threshold_bps=d("200.000000"), block_threshold_bps=d("100.000000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["scheduler_input_present"])
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())


def test_payload_rejects_public_leaks_and_preserves_hard_flags() -> None:
    module = api()
    result = score()
    payload = result.payload

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "derived_validation_digest" in payload
    assert_no_float_or_int_values(payload)

    forbidden_public_terms = (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
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
    for term in forbidden_public_terms:
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_specialist_source_recheck_priority_score_unsafe_payload(
                "unsafe-test",
                {term: "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_specialist_source_recheck_priority_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_payload_is_deterministic_and_digest_consistent() -> None:
    module = api()
    first = score()
    second = score()

    assert first == second
    assert first.payload == second.payload
    assert list(first.payload) == [
        "source_age_hours",
        "stale_after_hours",
        "screening_dependency_count",
        "conflicting_observation_count",
        "failed_recheck_count",
        "available_recheck_capacity_count",
        "staleness_ratio",
        "age_pressure_bps",
        "dependency_pressure_bps",
        "conflict_pressure_bps",
        "failed_recheck_pressure_bps",
        "capacity_relief_bps",
        "paper_priority_score_bps",
        "watch_threshold_bps",
        "block_threshold_bps",
        "score_status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ]
    assert first.payload == module.team_specialist_source_recheck_priority_score_payload(first)
    assert first.payload["source_age_hours"] == "6.000000"
    assert first.payload["paper_priority_score_bps"] == "12.500000"
    assert first.payload["reason_codes"] == list(first.reason_codes)
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest

    rebuilt = module.TeamSpecialistSourceRecheckPriorityScoreResult(
        **public_field_values(first),
    )
    assert rebuilt == first

    object.__setattr__(first, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_source_recheck_priority_score_payload(first)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.TeamSpecialistSourceRecheckPriorityScoreResult(
            **{
                **public_field_values(second),
                "derived_validation_digest": "0" * 64,
            },
        )


def test_module_surface_is_report_only_readonly_and_import_safe() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/team_specialist_source_recheck_priority_score.py",
    ).read_text(encoding="utf-8")

    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "SCORE_STATUSES",
        "TeamSpecialistSourceRecheckPriorityScoreInput",
        "TeamSpecialistSourceRecheckPriorityScoreResult",
        "estimate_team_specialist_source_recheck_priority_score",
        "team_specialist_source_recheck_priority_score_payload",
        "reject_team_specialist_source_recheck_priority_score_unsafe_payload",
    )
