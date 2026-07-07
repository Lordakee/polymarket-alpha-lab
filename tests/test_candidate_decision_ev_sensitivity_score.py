from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.candidate_decision_ev_sensitivity_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def score_input(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "forecast_yes_probability": d("0.620000"),
        "executable_yes_price": d("0.570000"),
        "executable_no_price": d("0.460000"),
        "evaluated_side": "yes",
        "fee_drag_bps": d("8.000000"),
        "spread_drag_bps": d("14.000000"),
        "cash_lock_settlement_drag_bps": d("6.000000"),
        "forecast_uncertainty_band_bps": d("15.000000"),
        "minimum_pass_edge_bps": d("25.000000"),
        "reason_codes": ("evidence_aligned",),
    }
    values.update(overrides)
    return module.CandidateDecisionEvSensitivityScoreInput(**values)


def score(subject: object | None = None):
    module = api()
    return module.estimate_candidate_decision_ev_sensitivity_score(
        score_input() if subject is None else subject,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_yes_side_passes_when_adjusted_edge_survives_all_drags() -> None:
    module = api()

    result = score()

    assert type(result) is module.CandidateDecisionEvSensitivityScoreResult
    assert result.forecast_yes_probability == d("0.620000")
    assert result.executable_yes_price == d("0.570000")
    assert result.executable_no_price == d("0.460000")
    assert result.evaluated_side == "yes"
    assert result.side_forecast_probability == d("0.620000")
    assert result.executable_side_price == d("0.570000")
    assert result.apparent_edge_bps == d("500.000000")
    assert result.total_drag_bps == d("43.000000")
    assert result.risk_adjusted_edge_bps == d("457.000000")
    assert result.margin_to_pass_bps == d("432.000000")
    assert result.decision_support_status == "pass"
    assert result.reason_codes == (
        "evidence_aligned",
        "candidate_decision_ev_sensitivity_score",
        "status_pass",
        "side_yes",
        "apparent_edge_positive",
        "fee_drag_applied",
        "spread_drag_applied",
        "cash_lock_settlement_drag_applied",
        "forecast_uncertainty_band_applied",
        "minimum_pass_edge_met",
    )
    assert len(result.derived_validation_digest) == 64
    assert result.derived_validation_digest.islower()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_no_side_uses_inverse_forecast_and_watches_below_pass_threshold() -> None:
    result = score(
        score_input(
            executable_no_price=d("0.365000"),
            evaluated_side="no",
            fee_drag_bps=d("20.000000"),
            spread_drag_bps=d("20.000000"),
            cash_lock_settlement_drag_bps=d("10.000000"),
            forecast_uncertainty_band_bps=d("30.000000"),
            minimum_pass_edge_bps=d("100.000000"),
            reason_codes=(),
        ),
    )

    assert result.side_forecast_probability == d("0.380000")
    assert result.executable_side_price == d("0.365000")
    assert result.apparent_edge_bps == d("150.000000")
    assert result.total_drag_bps == d("80.000000")
    assert result.risk_adjusted_edge_bps == d("70.000000")
    assert result.margin_to_pass_bps == d("-30.000000")
    assert result.decision_support_status == "watch"
    assert result.reason_codes == (
        "candidate_decision_ev_sensitivity_score",
        "status_watch",
        "side_no",
        "apparent_edge_positive",
        "fee_drag_applied",
        "spread_drag_applied",
        "cash_lock_settlement_drag_applied",
        "forecast_uncertainty_band_applied",
        "positive_below_pass_threshold",
    )


def test_blocks_when_drag_and_uncertainty_consume_the_apparent_edge() -> None:
    result = score(
        score_input(
            forecast_yes_probability=d("0.540000"),
            executable_yes_price=d("0.535000"),
            fee_drag_bps=d("10.000000"),
            spread_drag_bps=d("15.000000"),
            cash_lock_settlement_drag_bps=d("5.000000"),
            forecast_uncertainty_band_bps=d("30.000000"),
            minimum_pass_edge_bps=d("25.000000"),
            reason_codes=(),
        ),
    )

    assert result.apparent_edge_bps == d("50.000000")
    assert result.total_drag_bps == d("60.000000")
    assert result.risk_adjusted_edge_bps == d("-10.000000")
    assert result.margin_to_pass_bps == d("-35.000000")
    assert result.decision_support_status == "block"
    assert "adjusted_edge_nonpositive" in result.reason_codes


def test_payload_serializes_decimal_strings_and_excludes_identifiers_and_execution_terms() -> None:
    module = api()
    result = score()

    payload = result.payload

    assert payload == module.candidate_decision_ev_sensitivity_score_payload(result)
    assert payload["forecast_yes_probability"] == "0.620000"
    assert payload["apparent_edge_bps"] == "500.000000"
    assert payload["risk_adjusted_edge_bps"] == "457.000000"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    public_text = repr(payload).lower()
    forbidden_public_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "dsn",
        "table_name",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "position_size",
    )
    for fragment in forbidden_public_fragments:
        assert fragment not in public_text

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.candidate_decision_ev_sensitivity_score_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    subject = score_input()
    result = score(subject)

    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.CandidateDecisionEvSensitivityScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionEvSensitivityScoreResult.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.evaluated_side = "no"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.decision_support_status = "watch"  # type: ignore[misc]

    for instance in (subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="forecast_yes_probability must be a Decimal"):
        score_input(forecast_yes_probability=0.62)
    with pytest.raises(ValueError, match="executable_yes_price must be no greater than 1"):
        score_input(executable_yes_price=d("1.000001"))
    with pytest.raises(ValueError, match="evaluated_side must be one of"):
        score_input(evaluated_side="maybe")
    with pytest.raises(ValueError, match="fee_drag_bps must be nonnegative"):
        score_input(fee_drag_bps=d("-0.000001"))
    with pytest.raises(ValueError, match="minimum_pass_edge_bps must be nonnegative"):
        score_input(minimum_pass_edge_bps=d("-0.000001"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        score_input(reason_codes=["evidence_aligned"])
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        score_input(reason_codes=("evidence_aligned", "evidence_aligned"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="score_input"):
        score(object())

    rebuilt = module.CandidateDecisionEvSensitivityScoreResult(
        **public_field_values(result),
    )
    assert rebuilt == result


def test_rejects_digest_tampering_result_inconsistency_and_unsafe_payload_text() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionEvSensitivityScoreResult(
            **{
                **public_field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )

    with pytest.raises(ValueError, match="risk_adjusted_edge_bps"):
        replace(result, risk_adjusted_edge_bps=d("999.000000"))
    with pytest.raises(ValueError, match="decision_support_status"):
        replace(result, decision_support_status="pass", minimum_pass_edge_bps=d("999.000000"))

    unsafe_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "dsn",
        "table_name",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "private_token",
        "position_size",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            score_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_candidate_decision_ev_sensitivity_score_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_candidate_decision_ev_sensitivity_score_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_ev_sensitivity_score.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()

    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "subprocess",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
        ".write(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    unsafe_surface_terms = (
        " wallet",
        " auth",
        " order",
        " trade",
        " buy",
        " sell",
        " recommend",
        "private_key",
        "private_token",
        "position_size",
        "source_url",
        "market_slug",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

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
        "DECISION_SUPPORT_STATUSES",
        "EVALUATED_SIDES",
        "CandidateDecisionEvSensitivityScoreInput",
        "CandidateDecisionEvSensitivityScoreResult",
        "estimate_candidate_decision_ev_sensitivity_score",
        "candidate_decision_ev_sensitivity_score_payload",
        "reject_candidate_decision_ev_sensitivity_score_unsafe_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "candidate_decision_ev_sensitivity_score" not in getattr(
        root,
        "__all__",
        (),
    )
