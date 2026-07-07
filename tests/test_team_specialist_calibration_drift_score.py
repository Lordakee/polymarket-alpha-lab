from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.team_specialist_calibration_drift_score"


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "team_key": "macro_calibration",
        "specialist_key": "rates_probability",
        "long_term_sample_count": d("40"),
        "recent_sample_count": d("10"),
        "long_term_calibration_error_bps": d("20.000000"),
        "recent_calibration_error_bps": d("30.000000"),
        "drift_watch_threshold_bps": d("25.000000"),
        "drift_block_threshold_bps": d("75.000000"),
        "minimum_recent_sample_count": d("5"),
        "reason_codes": ("calibration_history_present",),
    }
    values.update(overrides)
    return module.TeamSpecialistCalibrationDriftScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_team_specialist_calibration_drift_score(
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


def test_pass_status_when_recent_calibration_matches_long_term_baseline() -> None:
    module = api()

    result = score()

    assert result == module.TeamSpecialistCalibrationDriftScoreResult(
        team_key="macro_calibration",
        specialist_key="rates_probability",
        long_term_sample_count=d("40"),
        recent_sample_count=d("10"),
        long_term_calibration_error_bps=d("20.000000"),
        recent_calibration_error_bps=d("30.000000"),
        calibration_drift_bps=d("10.000000"),
        absolute_calibration_drift_bps=d("10.000000"),
        recent_sample_coverage_ratio=d("0.250000"),
        drift_watch_threshold_bps=d("25.000000"),
        drift_block_threshold_bps=d("75.000000"),
        minimum_recent_sample_count=d("5"),
        report_status="pass",
        reason_codes=(
            "calibration_history_present",
            "team_specialist_calibration_drift_score",
            "drift_pass",
            "recent_sample_sufficient",
            "recent_error_worse",
            "drift_below_watch_threshold",
        ),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert result.report_status in module.REPORT_STATUSES
    assert module.REPORT_STATUSES == ("pass", "watch", "block")
    assert type(result.absolute_calibration_drift_bps) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_watch_status_when_recent_drift_crosses_watch_threshold() -> None:
    result = score(score_input(recent_calibration_error_bps=d("55.000000")))

    assert result.report_status == "watch"
    assert result.calibration_drift_bps == d("35.000000")
    assert result.absolute_calibration_drift_bps == d("35.000000")
    assert "drift_watch" in result.reason_codes
    assert "drift_watch_threshold_met" in result.reason_codes


def test_block_status_when_recent_drift_crosses_block_threshold() -> None:
    result = score(score_input(recent_calibration_error_bps=d("110.000000")))

    assert result.report_status == "block"
    assert result.calibration_drift_bps == d("90.000000")
    assert result.absolute_calibration_drift_bps == d("90.000000")
    assert "drift_block" in result.reason_codes
    assert "drift_block_threshold_met" in result.reason_codes


def test_decimal_types_are_exact_and_reject_subclasses() -> None:
    with pytest.raises(ValueError, match="long_term_sample_count must be a Decimal"):
        score_input(long_term_sample_count=40)
    with pytest.raises(ValueError, match="recent_calibration_error_bps must be a Decimal"):
        score_input(recent_calibration_error_bps=_DecimalSubclass("30.000000"))
    with pytest.raises(ValueError, match="drift_block_threshold_bps must be at least"):
        score_input(drift_watch_threshold_bps=d("80.000000"))
    with pytest.raises(ValueError, match="score_input"):
        score(object())


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert api().TeamSpecialistCalibrationDriftScoreInput.__dataclass_params__.frozen
    assert api().TeamSpecialistCalibrationDriftScoreResult.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.team_key = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]

    for instance in (subject, result):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    rebuilt = api().TeamSpecialistCalibrationDriftScoreResult(**public_field_values(result))
    assert rebuilt == result


def test_public_payload_rejects_sensitive_keys_and_values() -> None:
    module = api()
    unsafe_terms = (
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
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_seen",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_specialist_calibration_drift_score_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_specialist_calibration_drift_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_payload_is_deterministic_decimal_string_only_and_digest_consistent() -> None:
    module = api()
    first = score()
    second = score(score_input())

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64

    first_payload = first.payload
    second_payload = module.team_specialist_calibration_drift_score_payload(second)
    assert first_payload == second_payload
    assert first_payload["long_term_sample_count"] == "40"
    assert first_payload["recent_sample_coverage_ratio"] == "0.250000"
    assert first_payload["absolute_calibration_drift_bps"] == "10.000000"
    assert first_payload["report_status"] == "pass"
    assert first_payload["reason_codes"] == list(first.reason_codes)
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert_no_float_or_int_values(first_payload)
    json.dumps(first_payload, sort_keys=True)

    object.__setattr__(first, "absolute_calibration_drift_bps", d("0.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_calibration_drift_score_payload(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.TeamSpecialistCalibrationDriftScoreResult(
            **{
                **public_field_values(second),
                "derived_validation_digest": "0" * 64,
            },
        )


def test_module_has_no_runtime_side_effect_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/team_specialist_calibration_drift_score.py",
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
        "REPORT_STATUSES",
        "TeamSpecialistCalibrationDriftScoreInput",
        "TeamSpecialistCalibrationDriftScoreResult",
        "estimate_team_specialist_calibration_drift_score",
        "team_specialist_calibration_drift_score_payload",
        "reject_team_specialist_calibration_drift_score_unsafe_payload",
    )
