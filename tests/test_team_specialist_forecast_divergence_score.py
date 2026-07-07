from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.team_specialist_forecast_divergence_score"


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def forecast_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "specialist_group_id": "macro_forecast_reviewers",
        "forecast_scope_id": "macro_event_family",
        "specialist_forecast_count": d("4"),
        "minimum_forecast_count": d("3"),
        "minimum_forecast_probability": d("0.470000"),
        "maximum_forecast_probability": d("0.530000"),
        "mean_forecast_probability": d("0.500000"),
        "interquartile_range": d("0.030000"),
        "stdev_probability": d("0.010000"),
        "watch_divergence_threshold": d("0.150000"),
        "block_divergence_threshold": d("0.300000"),
        "reason_codes": ("forecast_set_ready",),
    }
    values.update(overrides)
    return module.TeamSpecialistForecastDivergenceScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_team_specialist_forecast_divergence_score(
        forecast_input() if subject is None else subject,
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


def test_scores_pass_watch_and_block_public_states() -> None:
    module = api()

    passing = score()
    watching = score(
        forecast_input(
            minimum_forecast_probability=d("0.410000"),
            maximum_forecast_probability=d("0.590000"),
            interquartile_range=d("0.090000"),
            stdev_probability=d("0.040000"),
        ),
    )
    blocking = score(
        forecast_input(
            minimum_forecast_probability=d("0.250000"),
            maximum_forecast_probability=d("0.650000"),
            interquartile_range=d("0.220000"),
            stdev_probability=d("0.120000"),
        ),
    )

    assert module.SCORE_STATUSES == ("pass", "watch", "block")
    assert passing.report_status == "pass"
    assert passing.forecast_range_ratio == d("0.060000")
    assert passing.dispersion_pressure_ratio == d("0.060000")
    assert passing.forecast_divergence_score == d("6.000000")
    assert passing.reason_codes == (
        "forecast_set_ready",
        "team_specialist_forecast_divergence_score",
        "score_pass",
        "divergence_below_watch_threshold",
    )

    assert watching.report_status == "watch"
    assert watching.dispersion_pressure_ratio == d("0.180000")
    assert "divergence_watch_threshold_met" in watching.reason_codes

    assert blocking.report_status == "block"
    assert blocking.dispersion_pressure_ratio == d("0.400000")
    assert "divergence_block_threshold_met" in blocking.reason_codes


def test_insufficient_forecast_count_blocks_review() -> None:
    result = score(forecast_input(specialist_forecast_count=d("2")))

    assert result.report_status == "block"
    assert result.forecast_count_gap == d("1")
    assert "forecast_count_below_minimum" in result.reason_codes


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = forecast_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.TeamSpecialistForecastDivergenceScoreInput.__dataclass_params__.frozen
    assert module.TeamSpecialistForecastDivergenceScoreResult.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.forecast_scope_id = "other_scope"  # type: ignore[misc]
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

    with pytest.raises(ValueError, match="specialist_forecast_count must be a Decimal"):
        forecast_input(specialist_forecast_count=4)
    with pytest.raises(ValueError, match="mean_forecast_probability must be a Decimal"):
        forecast_input(mean_forecast_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="minimum_forecast_probability must not exceed"):
        forecast_input(
            minimum_forecast_probability=d("0.600000"),
            maximum_forecast_probability=d("0.400000"),
        )
    with pytest.raises(ValueError, match="watch_divergence_threshold must not exceed"):
        forecast_input(
            watch_divergence_threshold=d("0.400000"),
            block_divergence_threshold=d("0.300000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        forecast_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())


def test_payload_is_deterministic_decimal_string_only_and_digest_checked() -> None:
    module = api()
    result = score()

    payload = result.payload
    second_payload = module.team_specialist_forecast_divergence_score_payload(result)

    assert payload == second_payload
    assert payload == result.payload
    assert json.dumps(payload, sort_keys=True) == json.dumps(second_payload, sort_keys=True)
    assert payload["specialist_forecast_count"] == "4"
    assert payload["forecast_divergence_score"] == "6.000000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    rebuilt = module.TeamSpecialistForecastDivergenceScoreResult(
        **public_field_values(result),
    )
    assert rebuilt == result
    assert rebuilt.payload == payload

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.TeamSpecialistForecastDivergenceScoreResult(
            **{
                **public_field_values(result),
                "reason_codes": (*result.reason_codes, "digest_tamper_probe"),
                "derived_validation_digest": result.derived_validation_digest,
            },
        )
    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.team_specialist_forecast_divergence_score_payload(result)


def test_rejects_unsafe_public_payload_keys_and_values() -> None:
    module = api()
    unsafe_terms = (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "market_question",
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
            forecast_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_specialist_forecast_divergence_score_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_team_specialist_forecast_divergence_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )

    payload_text = json.dumps(score().payload, sort_keys=True).lower()
    for forbidden in unsafe_terms:
        assert forbidden not in payload_text


def test_module_has_no_runtime_side_effect_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/team_specialist_forecast_divergence_score.py",
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
        "TeamSpecialistForecastDivergenceScoreInput",
        "TeamSpecialistForecastDivergenceScoreResult",
        "estimate_team_specialist_forecast_divergence_score",
        "team_specialist_forecast_divergence_score_payload",
        "reject_team_specialist_forecast_divergence_score_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "team_specialist_forecast_divergence_score" not in getattr(root, "__all__", ())
