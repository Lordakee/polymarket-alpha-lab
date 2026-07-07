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
    "polymarket_alpha_lab.candidate_decision_time_to_resolution_uncertainty_score"
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
            module.DEFAULT_CANDIDATE_DECISION_TIME_TO_RESOLUTION_UNCERTAINTY_SCORE_CONFIG_VERSION
        ),
        "max_pass_expected_resolution_days": d("14.000000"),
        "max_watch_expected_resolution_days": d("45.000000"),
        "max_pass_resolution_window_width_days": d("2.000000"),
        "max_watch_resolution_window_width_days": d("10.000000"),
        "min_pass_timing_confidence_score": d("0.800000"),
        "min_watch_timing_confidence_score": d("0.500000"),
        "min_pass_catalyst_specificity_score": d("0.750000"),
        "min_watch_catalyst_specificity_score": d("0.450000"),
        "min_pass_evidence_freshness_score": d("0.750000"),
        "min_watch_evidence_freshness_score": d("0.450000"),
        "min_pass_settlement_rule_clarity_score": d("0.800000"),
        "min_watch_settlement_rule_clarity_score": d("0.500000"),
        "expected_resolution_days_weight": d("0.150000"),
        "resolution_window_width_days_weight": d("0.350000"),
        "timing_confidence_score_weight": d("0.200000"),
        "catalyst_specificity_score_weight": d("0.100000"),
        "evidence_freshness_score_weight": d("0.100000"),
        "settlement_rule_clarity_score_weight": d("0.100000"),
        "min_pass_uncertainty_score": d("0.750000"),
        "min_watch_uncertainty_score": d("0.500000"),
    }
    values.update(overrides)
    return module.CandidateDecisionTimeToResolutionUncertaintyScoreConfig(**values)


def score_input(
    redacted_candidate_ref: str = (
        "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    ),
    **overrides: object,
):
    module = api()
    values = {
        "redacted_candidate_ref": redacted_candidate_ref,
        "expected_resolution_days": d("7.000000"),
        "resolution_window_width_days": d("1.000000"),
        "timing_confidence_score": d("0.900000"),
        "catalyst_specificity_score": d("0.850000"),
        "evidence_freshness_score": d("0.850000"),
        "settlement_rule_clarity_score": d("0.900000"),
    }
    values.update(overrides)
    return module.CandidateDecisionTimeToResolutionUncertaintyScoreInput(**values)


def score(subject: object | None = None, *, cfg: object | None = None):
    module = api()
    return module.score_candidate_decision_time_to_resolution_uncertainty_score(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_public_payload_is_json_safe(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected raw Decimal payload value {value!r}")
    if isinstance(value, float):
        raise AssertionError(f"unexpected float payload value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int payload value {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_public_payload_is_json_safe(child)
    elif isinstance(value, list):
        for child in value:
            assert_public_payload_is_json_safe(child)


def test_clear_timing_resolution_window_passes() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionTimeToResolutionUncertaintyScoreResult(
        config_version=(
            "candidate-decision-time-to-resolution-uncertainty-score-v0"
        ),
        redacted_candidate_ref=(
            "candidate_ref_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        ),
        expected_resolution_days=d("7.000000"),
        resolution_window_width_days=d("1.000000"),
        timing_confidence_score=d("0.900000"),
        catalyst_specificity_score=d("0.850000"),
        evidence_freshness_score=d("0.850000"),
        settlement_rule_clarity_score=d("0.900000"),
        expected_resolution_days_component_score=d("1.000000"),
        resolution_window_width_days_component_score=d("1.000000"),
        timing_confidence_component_score=d("1.000000"),
        catalyst_specificity_component_score=d("1.000000"),
        evidence_freshness_component_score=d("1.000000"),
        settlement_rule_clarity_component_score=d("1.000000"),
        uncertainty_score=d("1.000000"),
        status="pass",
        hard_flag_codes=(),
        reason_codes=(
            "time_to_resolution_uncertainty_score",
            "status_pass",
            "expected_resolution_days_pass",
            "resolution_window_width_days_pass",
            "timing_confidence_score_pass",
            "catalyst_specificity_score_pass",
            "evidence_freshness_score_pass",
            "settlement_rule_clarity_score_pass",
            "uncertainty_score_pass",
        ),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64
    assert result.payload == (
        module.candidate_decision_time_to_resolution_uncertainty_score_payload(result)
    )


def test_wide_resolution_window_blocks_even_when_other_evidence_is_clear() -> None:
    result = score(
        score_input(
            resolution_window_width_days=d("12.000000"),
        ),
    )

    assert result.resolution_window_width_days_component_score == d("0.000000")
    assert result.uncertainty_score == d("0.650000")
    assert result.status == "block"
    assert result.hard_flag_codes == ("resolution_window_width_days_block",)
    assert result.reason_codes == (
        "time_to_resolution_uncertainty_score",
        "status_block",
        "expected_resolution_days_pass",
        "resolution_window_width_days_block",
        "timing_confidence_score_pass",
        "catalyst_specificity_score_pass",
        "evidence_freshness_score_pass",
        "settlement_rule_clarity_score_pass",
        "uncertainty_score_watch",
    )


def test_moderate_time_window_uncertainty_is_watch() -> None:
    result = score(
        score_input(
            resolution_window_width_days=d("6.000000"),
        ),
    )

    assert result.resolution_window_width_days_component_score == d("0.500000")
    assert result.uncertainty_score == d("0.825000")
    assert result.status == "watch"
    assert result.hard_flag_codes == ()
    assert result.reason_codes == (
        "time_to_resolution_uncertainty_score",
        "status_watch",
        "expected_resolution_days_pass",
        "resolution_window_width_days_watch",
        "timing_confidence_score_pass",
        "catalyst_specificity_score_pass",
        "evidence_freshness_score_pass",
        "settlement_rule_clarity_score_pass",
        "uncertainty_score_pass",
    )


def test_decimal_exact_type_rejection_and_ranges() -> None:
    module = api()

    with pytest.raises(ValueError, match="expected_resolution_days must be a Decimal"):
        score_input(expected_resolution_days=7)
    with pytest.raises(
        ValueError,
        match="timing_confidence_score must be an exact Decimal",
    ):
        score_input(timing_confidence_score=DecimalSubclass("0.900000"))
    with pytest.raises(
        ValueError,
        match="settlement_rule_clarity_score must be between 0 and 1",
    ):
        score_input(settlement_rule_clarity_score=d("1.000001"))
    with pytest.raises(ValueError, match="resolution_window_width_days"):
        score_input(resolution_window_width_days=d("-0.000001"))
    with pytest.raises(ValueError, match="input_value"):
        score(object())
    with pytest.raises(ValueError, match="config"):
        score(score_input(), cfg=object())
    with pytest.raises(ValueError, match="weights must sum to 1.000000"):
        config(expected_resolution_days_weight=d("0.200000"))
    class ConfigSubclass(
        module.CandidateDecisionTimeToResolutionUncertaintyScoreConfig,
    ):
        pass

    with pytest.raises(ValueError, match="config must be"):
        ConfigSubclass()


def test_public_payload_leak_rejection() -> None:
    module = api()
    payload = score().payload

    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert "candidate_ref_" in rendered
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "position_size",
        "ready",
        "blocked",
        "matched",
        "supported",
    ):
        assert forbidden not in rendered

    unsafe_payloads = (
        ({"candidate_id": "raw"}, "raw candidate"),
        ({"market_slug": "will-event-resolve"}, "raw market"),
        ({"question": "Will this happen?"}, "raw market"),
        ({"source_url": "https://example.test/source"}, "source"),
        ({"source_text": "verbatim source"}, "source"),
        ({"dsn": "postgresql://example.test/db"}, "storage"),
        ({"table_name": "candidate_scores"}, "storage"),
        ({"status": "ready"}, "status"),
        ({"status": "blocked"}, "status"),
        ({"safe_key": "wallet key"}, "unsafe"),
        ({"safe_key": "submit order"}, "unsafe"),
        ({"safe_key": "buy or sell"}, "unsafe"),
        ({"safe_key": "position sizing"}, "unsafe"),
        ({"safe_key": "recommendation"}, "unsafe"),
        ({"diagnostic_count": 1}, "numeric"),
        ({"diagnostic_ratio": 1.0}, "numeric"),
    )
    for extra_payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_time_to_resolution_uncertainty_score_public_payload(
                {**payload, **extra_payload},
            )

    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        score_input("candidate:unredacted-slug")
    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        score_input("candidate_ref_not-a-digest")


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    result = score(subject, cfg=cfg)

    for klass in (
        module.CandidateDecisionTimeToResolutionUncertaintyScoreConfig,
        module.CandidateDecisionTimeToResolutionUncertaintyScoreInput,
        module.CandidateDecisionTimeToResolutionUncertaintyScoreResult,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        subject.expected_resolution_days = d("8.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    for instance in (cfg, subject, result):
        for item in fields(instance):
            value = getattr(instance, item.name)
            if item.name in {
                "config_version",
                "redacted_candidate_ref",
                "status",
                "hard_flag_codes",
                "reason_codes",
                "derived_validation_digest",
                "paper_only",
                "report_only",
                "readonly",
            }:
                continue
            assert type(value) is Decimal, item.name

    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(subject, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)


def test_deterministic_payload_and_digest_are_stable() -> None:
    first = score()
    second = score()

    assert first == second
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert_public_payload_is_json_safe(first.payload)
    json.dumps(first.payload, allow_nan=False, sort_keys=True)


def test_result_consistency_is_validated() -> None:
    module = api()
    result = score()
    rebuilt = module.CandidateDecisionTimeToResolutionUncertaintyScoreResult(
        **public_values(result),
    )

    assert rebuilt == result
    with pytest.raises(ValueError, match="uncertainty_score"):
        replace(result, uncertainty_score=d("0.900000"))
    with pytest.raises(ValueError, match="expected_resolution_days_component_score"):
        replace(result, expected_resolution_days_component_score=d("0.500000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("time_to_resolution_uncertainty_score",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="result must be"):
        module.candidate_decision_time_to_resolution_uncertainty_score_payload(object())


def test_module_static_pure_report_only_boundary() -> None:
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

    forbidden_import_roots = {
        "asyncio",
        "http",
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
    assert not (set(imported_modules) & forbidden_import_roots)
    for forbidden in (
        "private_key",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommendation",
        "position_size",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "open(",
        "connect(",
        "execute(",
    ):
        assert forbidden not in lowered

    assert module.TIME_TO_RESOLUTION_UNCERTAINTY_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_TIME_TO_RESOLUTION_UNCERTAINTY_SCORE_CONFIG_VERSION",
        "TIME_TO_RESOLUTION_UNCERTAINTY_STATUSES",
        "CandidateDecisionTimeToResolutionUncertaintyScoreConfig",
        "CandidateDecisionTimeToResolutionUncertaintyScoreInput",
        "CandidateDecisionTimeToResolutionUncertaintyScoreResult",
        "score_candidate_decision_time_to_resolution_uncertainty_score",
        "candidate_decision_time_to_resolution_uncertainty_score_payload",
        "validate_candidate_decision_time_to_resolution_uncertainty_score_public_payload",
    )
