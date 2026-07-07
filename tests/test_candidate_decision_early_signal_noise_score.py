from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_early_signal_noise_score"


class _DecimalSubclass(Decimal):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing early signal noise score module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_EARLY_SIGNAL_NOISE_SCORE_CONFIG_VERSION
        ),
        "min_pass_signal_count": d("3.000000"),
        "min_watch_signal_count": d("1.000000"),
        "min_pass_independent_signal_ratio": d("0.750000"),
        "min_watch_independent_signal_ratio": d("0.500000"),
        "max_pass_contradiction_ratio": d("0.200000"),
        "max_watch_contradiction_ratio": d("0.500000"),
        "max_pass_volatility_score": d("0.250000"),
        "max_watch_volatility_score": d("0.600000"),
        "max_pass_rumor_risk_score": d("0.200000"),
        "max_watch_rumor_risk_score": d("0.500000"),
        "min_pass_source_quality_score": d("0.700000"),
        "min_watch_source_quality_score": d("0.400000"),
        "min_pass_recency_score": d("0.600000"),
        "min_watch_recency_score": d("0.300000"),
        "max_pass_noise_score": d("0.250000"),
        "max_watch_noise_score": d("0.500000"),
        "independent_signal_weight": d("1.000000"),
        "contradiction_weight": d("1.000000"),
        "volatility_weight": d("1.000000"),
        "rumor_risk_weight": d("1.000000"),
        "source_quality_weight": d("1.000000"),
        "recency_weight": d("1.000000"),
    }
    values.update(overrides)
    return module.CandidateDecisionEarlySignalNoiseScoreConfig(**values)


def signal_input(**overrides: object):
    module = api()
    values = {
        "redacted_candidate_ref": "redacted-alpha",
        "signal_count": d("5.000000"),
        "independent_signal_ratio": d("0.900000"),
        "contradiction_ratio": d("0.050000"),
        "volatility_score": d("0.100000"),
        "rumor_risk_score": d("0.050000"),
        "source_quality_score": d("0.850000"),
        "recency_score": d("0.900000"),
    }
    values.update(overrides)
    return module.CandidateDecisionEarlySignalNoiseScoreInput(**values)


def score(subject: object | None = None, *, cfg=None):
    module = api()
    return module.score_candidate_decision_early_signal_noise(
        signal_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_int_or_decimal_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, int) and not isinstance(value, bool):
        raise AssertionError(f"unexpected int value {value!r}")
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected raw Decimal value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_int_or_decimal_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_int_or_decimal_values(item)


def test_low_noise_signals_pass_with_decimal_weighted_score() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionEarlySignalNoiseScoreReport(
        config_version="candidate-decision-early-signal-noise-score-v0",
        redacted_candidate_ref="redacted-alpha",
        signal_count=d("5.000000"),
        independent_signal_ratio=d("0.900000"),
        contradiction_ratio=d("0.050000"),
        volatility_score=d("0.100000"),
        rumor_risk_score=d("0.050000"),
        source_quality_score=d("0.850000"),
        recency_score=d("0.900000"),
        independence_noise_score=d("0.100000"),
        source_quality_noise_score=d("0.150000"),
        recency_noise_score=d("0.100000"),
        weighted_noise_score=d("0.091667"),
        status="pass",
        hard_flag_codes=(),
        reason_codes=(
            "candidate_decision_early_signal_noise_score",
            "status_pass",
            "signal_count_pass",
            "independent_signal_ratio_pass",
            "contradiction_ratio_pass",
            "volatility_score_pass",
            "rumor_risk_score_pass",
            "source_quality_score_pass",
            "recency_score_pass",
            "weighted_noise_score_pass",
        ),
        derived_validation_digest=result.derived_validation_digest,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload == module.candidate_decision_early_signal_noise_score_payload(result)


def test_noisy_contradiction_blocks_even_when_weighted_score_is_low() -> None:
    result = score(signal_input(contradiction_ratio=d("0.750000")))

    assert result.weighted_noise_score == d("0.208333")
    assert result.status == "block"
    assert result.hard_flag_codes == ("contradiction_ratio_block",)
    assert result.reason_codes == (
        "candidate_decision_early_signal_noise_score",
        "status_block",
        "signal_count_pass",
        "independent_signal_ratio_pass",
        "contradiction_ratio_block",
        "volatility_score_pass",
        "rumor_risk_score_pass",
        "source_quality_score_pass",
        "recency_score_pass",
        "weighted_noise_score_pass",
    )


def test_sparse_signals_watch_without_hard_flags() -> None:
    result = score(signal_input(signal_count=d("1.000000")))

    assert result.status == "watch"
    assert result.hard_flag_codes == ()
    assert "signal_count_watch" in result.reason_codes
    assert "weighted_noise_score_pass" in result.reason_codes


def test_decimal_exact_type_rejection_and_frozen_report_only_flags() -> None:
    module = api()
    cfg = config()
    subject = signal_input()
    result = score(subject, cfg=cfg)

    for klass in (
        module.CandidateDecisionEarlySignalNoiseScoreConfig,
        module.CandidateDecisionEarlySignalNoiseScoreInput,
        module.CandidateDecisionEarlySignalNoiseScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        subject.signal_count = d("2.000000")  # type: ignore[misc]
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
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="signal_count must be a Decimal"):
        signal_input(signal_count=5)
    with pytest.raises(ValueError, match="independent_signal_ratio must be a Decimal"):
        signal_input(independent_signal_ratio=0.9)
    with pytest.raises(ValueError, match="signal_count must be an exact Decimal"):
        signal_input(signal_count=_DecimalSubclass("5.000000"))
    with pytest.raises(ValueError, match="signal_count must be a nonnegative count Decimal"):
        signal_input(signal_count=d("1.500000"))
    with pytest.raises(ValueError, match="contradiction_ratio must be between 0 and 1"):
        signal_input(contradiction_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.CandidateDecisionEarlySignalNoiseScoreConfig(
            **{**public_values(cfg), "readonly": False},
        )
    with pytest.raises(ValueError, match="input_value"):
        score(object())
    with pytest.raises(ValueError, match="config"):
        score(subject, cfg=object())


def test_public_payload_rejects_identifier_source_storage_and_execution_leaks() -> None:
    module = api()
    payload = score().payload
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["redacted_candidate_ref"] == "redacted-alpha"
    assert payload["weighted_noise_score"] == "0.091667"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_int_or_decimal_values(payload)

    forbidden_payload_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
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
        "recommendation",
        "position_size",
        "position-sizing",
    )
    for fragment in forbidden_payload_fragments:
        assert fragment not in payload
        assert fragment not in rendered

    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        signal_input(redacted_candidate_ref="candidate_id=abc123")
    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        signal_input(redacted_candidate_ref="https://example.test/raw")
    with pytest.raises(ValueError, match="redacted_candidate_ref"):
        signal_input(redacted_candidate_ref="candidate-abc123")

    unsafe_payloads = (
        ({"candidate_id": "candidate-123"}, "unsafe public payload field"),
        ({"market_id": "market-123"}, "unsafe public payload field"),
        ({"market_slug": "will-event-resolve"}, "unsafe public payload field"),
        ({"market_question": "Will this event resolve yes?"}, "unsafe public payload field"),
        ({"source_ref": "source-123"}, "unsafe public payload field"),
        ({"source_url": "https://example.test/source"}, "unsafe public payload field"),
        ({"source_text": "raw source text"}, "unsafe public payload field"),
        ({"dsn": "postgresql://example.test/db"}, "unsafe public payload field"),
        ({"table_name": "candidate_scores"}, "unsafe public payload field"),
        ({"token": "redacted"}, "unsafe live surface field"),
        ({"diagnostic_count": 1}, "numeric public payload values"),
        ({"diagnostic_values": (1,)}, "numeric public payload values"),
        ({"status_note": "buy"}, "unsafe public payload value"),
        ({"status_note": "sell"}, "unsafe public payload value"),
        ({"status_note": "recommendation"}, "unsafe public payload value"),
        ({"status_note": "trade"}, "unsafe public payload value"),
        ({"status_note": "position-sizing"}, "unsafe public payload value"),
    )
    for extra_payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_early_signal_noise_score_public_payload(
                {**payload, **extra_payload},
            )

    assert module.validate_candidate_decision_early_signal_noise_score_public_payload(payload)


def test_hard_flags_capture_blocking_signal_noise_dimensions() -> None:
    result = score(
        signal_input(
            signal_count=d("0.000000"),
            independent_signal_ratio=d("0.200000"),
            contradiction_ratio=d("0.700000"),
            volatility_score=d("0.800000"),
            rumor_risk_score=d("0.900000"),
            source_quality_score=d("0.200000"),
            recency_score=d("0.100000"),
        ),
    )

    assert result.status == "block"
    assert result.hard_flag_codes == (
        "signal_count_block",
        "independent_signal_ratio_block",
        "contradiction_ratio_block",
        "volatility_score_block",
        "rumor_risk_score_block",
        "source_quality_score_block",
        "recency_score_block",
        "weighted_noise_score_block",
    )
    assert all(code in result.reason_codes for code in result.hard_flag_codes)


def test_payload_is_deterministic_and_uses_only_public_status_vocabulary() -> None:
    first = score()
    second = score()

    assert first == second
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert first.status in ("pass", "watch", "block")

    rendered = json.dumps(first.payload, allow_nan=False, sort_keys=True).lower()
    for forbidden_status in ("ready", "blocked", "matched", "supported"):
        assert forbidden_status not in rendered


def test_report_consistency_validates_metrics_reasons_and_digest() -> None:
    module = api()
    result = score()

    rebuilt = module.CandidateDecisionEarlySignalNoiseScoreReport(**public_values(result))
    assert rebuilt == result

    with pytest.raises(ValueError, match="weighted_noise_score"):
        replace(result, weighted_noise_score=d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, status="watch")
    with pytest.raises(ValueError, match="hard_flag_codes"):
        replace(result, hard_flag_codes=("volatility_score_block",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="min_watch_signal_count"):
        config(min_watch_signal_count=d("4.000000"))
    with pytest.raises(ValueError, match="max_pass_contradiction_ratio"):
        config(max_pass_contradiction_ratio=d("0.600000"))
    with pytest.raises(ValueError, match="min_watch_source_quality_score"):
        config(min_watch_source_quality_score=d("0.800000"))
    with pytest.raises(ValueError, match="weights must include at least one positive value"):
        config(
            independent_signal_weight=d("0.000000"),
            contradiction_weight=d("0.000000"),
            volatility_weight=d("0.000000"),
            rumor_risk_weight=d("0.000000"),
            source_quality_weight=d("0.000000"),
            recency_weight=d("0.000000"),
        )


def test_module_is_pure_report_only_with_no_io_or_float_literals() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")
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

    banned_import_roots = {
        "asyncio",
        "csv",
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
    assert not (set(imported_modules) & banned_import_roots)
    assert module.EARLY_SIGNAL_NOISE_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_EARLY_SIGNAL_NOISE_SCORE_CONFIG_VERSION",
        "EARLY_SIGNAL_NOISE_STATUSES",
        "CandidateDecisionEarlySignalNoiseScoreConfig",
        "CandidateDecisionEarlySignalNoiseScoreInput",
        "CandidateDecisionEarlySignalNoiseScoreReport",
        "score_candidate_decision_early_signal_noise",
        "candidate_decision_early_signal_noise_score_payload",
        "validate_candidate_decision_early_signal_noise_score_public_payload",
    )
