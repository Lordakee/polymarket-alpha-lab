from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.candidate_decision_exogenous_shock_sensitivity_score"
)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_EXOGENOUS_SHOCK_SENSITIVITY_SCORE_CONFIG_VERSION
        ),
        "normalization_probability_move_bps": d("500.000000"),
        "max_pass_probability_move_bps": d("150.000000"),
        "max_watch_probability_move_bps": d("350.000000"),
        "max_pass_historical_shock_frequency_score": d("0.350000"),
        "max_watch_historical_shock_frequency_score": d("0.650000"),
        "max_pass_shock_driver_correlation_score": d("0.350000"),
        "max_watch_shock_driver_correlation_score": d("0.650000"),
        "max_pass_external_dependency_score": d("0.400000"),
        "max_watch_external_dependency_score": d("0.700000"),
        "min_pass_mitigation_coverage_score": d("0.700000"),
        "min_watch_mitigation_coverage_score": d("0.450000"),
        "max_pass_monitoring_latency_score": d("0.350000"),
        "max_watch_monitoring_latency_score": d("0.650000"),
        "max_pass_exogenous_shock_sensitivity_score": d("0.350000"),
        "max_watch_exogenous_shock_sensitivity_score": d("0.650000"),
        "probability_move_weight": d("0.300000"),
        "historical_shock_frequency_weight": d("0.200000"),
        "shock_driver_correlation_weight": d("0.200000"),
        "external_dependency_weight": d("0.150000"),
        "mitigation_gap_weight": d("0.100000"),
        "monitoring_latency_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.CandidateDecisionExogenousShockSensitivityScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values = {
        "baseline_probability_move_bps": d("100.000000"),
        "historical_shock_frequency_score": d("0.200000"),
        "shock_driver_correlation_score": d("0.250000"),
        "external_dependency_score": d("0.200000"),
        "mitigation_coverage_score": d("0.850000"),
        "monitoring_latency_score": d("0.200000"),
    }
    values.update(overrides)
    return module.CandidateDecisionExogenousShockSensitivityScoreInput(**values)


def score(subject: object | None = None, *, cfg: object | None = None):
    module = api()
    return module.score_candidate_decision_exogenous_shock_sensitivity(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_public_json_scalars(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected raw Decimal value {value!r}")
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_public_json_scalars(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_json_scalars(item)


def test_low_exogenous_shock_sensitivity_passes() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionExogenousShockSensitivityScoreReport(
        config_version=(
            "candidate-decision-exogenous-shock-sensitivity-score-v0"
        ),
        baseline_probability_move_bps=d("100.000000"),
        historical_shock_frequency_score=d("0.200000"),
        shock_driver_correlation_score=d("0.250000"),
        external_dependency_score=d("0.200000"),
        mitigation_coverage_score=d("0.850000"),
        monitoring_latency_score=d("0.200000"),
        normalized_probability_move_score=d("0.200000"),
        mitigation_gap_score=d("0.150000"),
        exogenous_shock_sensitivity_score=d("0.205000"),
        exogenous_shock_resilience_score=d("0.795000"),
        status="pass",
        hard_flag_codes=(),
        reason_codes=(
            "candidate_decision_exogenous_shock_sensitivity_score",
            "status_pass",
            "baseline_probability_move_bps_pass",
            "historical_shock_frequency_score_pass",
            "shock_driver_correlation_score_pass",
            "external_dependency_score_pass",
            "mitigation_coverage_score_pass",
            "monitoring_latency_score_pass",
            "exogenous_shock_sensitivity_score_pass",
            "hard_flags_absent",
        ),
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64
    assert result.payload == (
        module.candidate_decision_exogenous_shock_sensitivity_score_payload(result)
    )


def test_moderate_exogenous_shock_sensitivity_watches() -> None:
    result = score(
        score_input(
            baseline_probability_move_bps=d("220.000000"),
            historical_shock_frequency_score=d("0.500000"),
            shock_driver_correlation_score=d("0.400000"),
            external_dependency_score=d("0.300000"),
            mitigation_coverage_score=d("0.650000"),
            monitoring_latency_score=d("0.400000"),
        ),
    )

    assert result.normalized_probability_move_score == d("0.440000")
    assert result.mitigation_gap_score == d("0.350000")
    assert result.exogenous_shock_sensitivity_score == d("0.412000")
    assert result.exogenous_shock_resilience_score == d("0.588000")
    assert result.status == "watch"
    assert result.hard_flag_codes == ()
    assert "baseline_probability_move_bps_watch" in result.reason_codes
    assert "exogenous_shock_sensitivity_score_watch" in result.reason_codes


def test_severe_exogenous_shock_sensitivity_blocks_with_hard_flags() -> None:
    result = score(
        score_input(
            baseline_probability_move_bps=d("500.000000"),
            historical_shock_frequency_score=d("0.800000"),
            shock_driver_correlation_score=d("0.900000"),
            external_dependency_score=d("0.800000"),
            mitigation_coverage_score=d("0.200000"),
            monitoring_latency_score=d("0.750000"),
        ),
    )

    assert result.normalized_probability_move_score == d("1.000000")
    assert result.mitigation_gap_score == d("0.800000")
    assert result.exogenous_shock_sensitivity_score == d("0.877500")
    assert result.exogenous_shock_resilience_score == d("0.122500")
    assert result.status == "block"
    assert result.hard_flag_codes == (
        "baseline_probability_move_bps_hard_flag",
        "historical_shock_frequency_score_hard_flag",
        "shock_driver_correlation_score_hard_flag",
        "external_dependency_score_hard_flag",
        "mitigation_coverage_score_hard_flag",
        "monitoring_latency_score_hard_flag",
    )
    assert "exogenous_shock_sensitivity_score_block" in result.reason_codes
    assert "hard_flags_present" in result.reason_codes


def test_decimal_exact_type_rejection() -> None:
    with pytest.raises(ValueError, match="baseline_probability_move_bps must be a Decimal"):
        score_input(baseline_probability_move_bps=100)
    with pytest.raises(ValueError, match="historical_shock_frequency_score must be a Decimal"):
        score_input(historical_shock_frequency_score=0.2)
    with pytest.raises(ValueError, match="shock_driver_correlation_score must be an exact Decimal"):
        score_input(shock_driver_correlation_score=DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="external_dependency_score must be between 0 and 1"):
        score_input(external_dependency_score=d("1.000001"))
    with pytest.raises(ValueError, match="mitigation_coverage_score must be between 0 and 1"):
        score_input(mitigation_coverage_score=d("-0.000001"))
    with pytest.raises(ValueError, match="monitoring_latency_weight must be an exact Decimal"):
        config(monitoring_latency_weight=DecimalSubclass("0.050000"))
    with pytest.raises(ValueError, match="config weights must sum to 1"):
        config(mitigation_gap_weight=d("0.110000"))


def test_leak_rejection_for_identifiers_sources_and_execution_terms() -> None:
    module = api()
    payload = score().payload

    unsafe_payloads = (
        {"candidate_id": "raw-candidate-123"},
        {"raw_candidate_id": "candidate-123"},
        {"market_id": "market-123"},
        {"market_slug": "will-event-resolve"},
        {"market_question": "Will this event resolve?"},
        {"source_ref": "source-123"},
        {"source_url": "https://example.invalid/source"},
        {"source_text": "raw source text"},
        {"dsn": "postgresql://example.invalid/db"},
        {"table_name": "candidate_scores"},
        {"secret_token": "redacted"},
        {"status_note": "wallet"},
        {"status_note": "auth"},
        {"status_note": "order"},
        {"status_note": "trade"},
        {"status_note": "buy"},
        {"status_note": "sell"},
        {"status_note": "recommendation"},
        {"status_note": "position-sizing"},
        {"diagnostic_count": 1},
    )
    for extra_payload in unsafe_payloads:
        with pytest.raises(ValueError):
            module.validate_candidate_decision_exogenous_shock_sensitivity_public_payload(
                {**payload, **extra_payload},
            )


def test_hard_flags_and_safety_flags_are_enforced() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    result = score(subject, cfg=cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.CandidateDecisionExogenousShockSensitivityScoreConfig.__dataclass_params__.frozen
    assert module.CandidateDecisionExogenousShockSensitivityScoreInput.__dataclass_params__.frozen
    assert module.CandidateDecisionExogenousShockSensitivityScoreReport.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.baseline_probability_move_bps = d("120.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(result, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.CandidateDecisionExogenousShockSensitivityScoreConfig(
            **{**public_values(cfg), "readonly": False},
        )
    with pytest.raises(ValueError, match="input_value"):
        score(object())
    with pytest.raises(ValueError, match="config"):
        score(subject, cfg=object())


def test_deterministic_payload_has_json_scalars_and_public_status_words() -> None:
    first = score()
    second = score()

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.payload == second.payload
    assert json.dumps(first.payload, allow_nan=False, sort_keys=True) == json.dumps(
        second.payload,
        allow_nan=False,
        sort_keys=True,
    )

    payload = first.payload
    assert payload["baseline_probability_move_bps"] == "100.000000"
    assert payload["normalized_probability_move_score"] == "0.200000"
    assert payload["exogenous_shock_sensitivity_score"] == "0.205000"
    assert payload["exogenous_shock_resilience_score"] == "0.795000"
    assert payload["status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_public_json_scalars(payload)

    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position-sizing",
        "position_size",
    ):
        assert forbidden not in rendered


def test_report_consistency_and_digest_are_validated() -> None:
    module = api()
    result = score()

    rebuilt = module.CandidateDecisionExogenousShockSensitivityScoreReport(
        **public_values(result),
    )
    assert rebuilt == result

    with pytest.raises(ValueError, match="exogenous_shock_sensitivity_score"):
        replace(result, exogenous_shock_sensitivity_score=d("0.250000"))
    with pytest.raises(ValueError, match="exogenous_shock_resilience_score"):
        replace(result, exogenous_shock_resilience_score=d("0.700000"))
    with pytest.raises(ValueError, match="status"):
        replace(result, status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("candidate_decision_exogenous_shock_sensitivity_score",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.CandidateDecisionExogenousShockSensitivityScoreReport(
            **{**public_values(result), "derived_validation_digest": "0" * 64},
        )
    with pytest.raises(ValueError, match="max_pass_probability_move_bps"):
        config(max_pass_probability_move_bps=d("400.000000"))
    with pytest.raises(ValueError, match="min_watch_mitigation_coverage_score"):
        config(min_watch_mitigation_coverage_score=d("0.800000"))
    with pytest.raises(ValueError, match="normalization_probability_move_bps"):
        config(normalization_probability_move_bps=d("0.000000"))


def test_module_has_report_only_boundary_no_io_or_live_surface_and_no_float_literals() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
    lowered = source.lower()
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
    for forbidden in (
        "candidate_id",
        "raw_candidate",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "private_key",
        "secret_token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "dsn",
        "table_name",
        "position_size",
        "position-sizing",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "open(",
        "path(",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "exchange",
    ):
        assert forbidden not in lowered

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_EXOGENOUS_SHOCK_SENSITIVITY_SCORE_CONFIG_VERSION",
        "EXOGENOUS_SHOCK_SENSITIVITY_STATUSES",
        "CandidateDecisionExogenousShockSensitivityScoreConfig",
        "CandidateDecisionExogenousShockSensitivityScoreInput",
        "CandidateDecisionExogenousShockSensitivityScoreReport",
        "score_candidate_decision_exogenous_shock_sensitivity",
        "candidate_decision_exogenous_shock_sensitivity_score_payload",
        "validate_candidate_decision_exogenous_shock_sensitivity_public_payload",
    )
    root = importlib.import_module("polymarket_alpha_lab")
    assert "candidate_decision_exogenous_shock_sensitivity_score" not in getattr(
        root,
        "__all__",
        (),
    )
