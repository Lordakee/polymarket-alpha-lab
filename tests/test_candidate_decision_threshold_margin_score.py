from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_threshold_margin_score"


class _DecimalSubclass(Decimal):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing threshold margin score module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_CANDIDATE_DECISION_THRESHOLD_MARGIN_SCORE_CONFIG_VERSION
        ),
        "min_pass_net_threshold_margin": d("0.100000"),
        "min_watch_net_threshold_margin": d("0.020000"),
        "min_pass_margin_coverage_ratio": d("2.000000"),
        "min_watch_margin_coverage_ratio": d("1.000000"),
        "min_pass_evidence_confidence": d("0.750000"),
        "min_watch_evidence_confidence": d("0.450000"),
        "min_pass_threshold_margin_score": d("0.650000"),
        "min_watch_threshold_margin_score": d("0.300000"),
    }
    values.update(overrides)
    return module.CandidateDecisionThresholdMarginScoreConfig(**values)


def score_input(**overrides: object):
    module = api()
    values = {
        "observed_value": d("0.720000"),
        "critical_threshold": d("0.500000"),
        "resolution_boundary_width": d("0.050000"),
        "measurement_uncertainty": d("0.020000"),
        "evidence_confidence": d("0.900000"),
    }
    values.update(overrides)
    return module.CandidateDecisionThresholdMarginScoreInput(**values)


def score(subject: object | None = None, *, cfg: object | None = None):
    module = api()
    return module.score_candidate_decision_threshold_margin_score(
        score_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def public_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_float_int_or_decimal_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected raw Decimal payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_int_or_decimal_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_int_or_decimal_values(item)


def test_pass_status_when_event_has_clear_margin_from_threshold_boundary() -> None:
    module = api()

    result = score()

    assert result == module.CandidateDecisionThresholdMarginScoreReport(
        config_version="candidate-decision-threshold-margin-score-v0",
        observed_value=d("0.720000"),
        critical_threshold=d("0.500000"),
        resolution_boundary_width=d("0.050000"),
        measurement_uncertainty=d("0.020000"),
        evidence_confidence=d("0.900000"),
        absolute_threshold_margin=d("0.220000"),
        total_boundary_buffer=d("0.070000"),
        net_threshold_margin=d("0.150000"),
        margin_coverage_ratio=d("3.142857"),
        threshold_margin_score=d("0.682759"),
        status="pass",
        reason_codes=(
            "candidate_decision_threshold_margin_score",
            "status_pass",
            "net_threshold_margin_pass",
            "margin_coverage_ratio_pass",
            "evidence_confidence_pass",
            "threshold_margin_score_pass",
        ),
        report_sha256=result.report_sha256,
        derived_validation_digest=result.derived_validation_digest,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_sha256(result.report_sha256)
    assert_sha256(result.derived_validation_digest)
    assert result.payload == module.candidate_decision_threshold_margin_score_payload(result)
    assert module.validate_candidate_decision_threshold_margin_score_report(result) is True


def test_watch_status_when_margin_survives_but_is_thin() -> None:
    result = score(
        score_input(
            observed_value=d("0.600000"),
            evidence_confidence=d("0.700000"),
        ),
    )

    assert result.absolute_threshold_margin == d("0.100000")
    assert result.total_boundary_buffer == d("0.070000")
    assert result.net_threshold_margin == d("0.030000")
    assert result.margin_coverage_ratio == d("1.428571")
    assert result.threshold_margin_score == d("0.411765")
    assert result.status == "watch"
    assert result.reason_codes == (
        "candidate_decision_threshold_margin_score",
        "status_watch",
        "net_threshold_margin_watch",
        "margin_coverage_ratio_watch",
        "evidence_confidence_watch",
        "threshold_margin_score_watch",
    )


def test_block_status_when_boundary_buffer_overwhelms_margin() -> None:
    result = score(
        score_input(
            observed_value=d("0.540000"),
            evidence_confidence=d("0.800000"),
        ),
    )

    assert result.absolute_threshold_margin == d("0.040000")
    assert result.total_boundary_buffer == d("0.070000")
    assert result.net_threshold_margin == d("-0.030000")
    assert result.margin_coverage_ratio == d("0.571429")
    assert result.threshold_margin_score == d("0.290909")
    assert result.status == "block"
    assert result.reason_codes == (
        "candidate_decision_threshold_margin_score",
        "status_block",
        "net_threshold_margin_block",
        "margin_coverage_ratio_block",
        "evidence_confidence_pass",
        "threshold_margin_score_block",
    )


def test_decimal_type_rejection_frozen_dataclasses_and_hard_flags() -> None:
    module = api()
    cfg = config()
    subject = score_input()
    result = score(subject, cfg=cfg)

    for klass in (
        module.CandidateDecisionThresholdMarginScoreConfig,
        module.CandidateDecisionThresholdMarginScoreInput,
        module.CandidateDecisionThresholdMarginScoreReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        subject.observed_value = d("0.700000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    for instance in (cfg, subject, result):
        for item in fields(instance):
            item_value = getattr(instance, item.name)
            if item.name in {
                "config_version",
                "status",
                "reason_codes",
                "report_sha256",
                "derived_validation_digest",
                "paper_only",
                "report_only",
                "readonly",
            }:
                continue
            assert type(item_value) is Decimal

    with pytest.raises(ValueError, match="observed_value must be a Decimal"):
        score_input(observed_value=0.72)
    with pytest.raises(ValueError, match="critical_threshold must be an exact Decimal"):
        score_input(critical_threshold=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="resolution_boundary_width must be between"):
        score_input(resolution_boundary_width=d("-0.000001"))
    with pytest.raises(ValueError, match="evidence_confidence must be between"):
        score_input(evidence_confidence=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="input_value"):
        score(object())
    with pytest.raises(ValueError, match="config"):
        score(subject, cfg=object())


def test_public_payload_rejects_identifier_source_storage_and_execution_leaks() -> None:
    module = api()
    payload = score().payload
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["observed_value"] == "0.720000"
    assert payload["threshold_margin_score"] == "0.682759"
    assert payload["status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_int_or_decimal_values(payload)

    for forbidden in (
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
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert forbidden not in rendered

    unsafe_payloads = (
        ({"candidate_id": "candidate-123"}, "unsafe public payload field"),
        ({"market_id": "market-123"}, "unsafe public payload field"),
        ({"market_slug": "event-threshold"}, "unsafe public payload field"),
        ({"market_question": "Will this cross a threshold?"}, "unsafe public payload field"),
        ({"source_ref": "source-123"}, "unsafe public payload field"),
        ({"source_url": "https://example.test/ref"}, "unsafe public payload field"),
        ({"source_text": "raw source"}, "unsafe public payload field"),
        ({"dsn": "postgresql://example.test/db"}, "unsafe public payload field"),
        ({"table_name": "threshold_scores"}, "unsafe public payload field"),
        ({"token": "secret"}, "unsafe public payload field"),
        ({"wallet": "0xabc"}, "unsafe public payload field"),
        ({"position_size": "1.000000"}, "unsafe public payload field"),
        ({"diagnostic_count": 1}, "numeric public payload values"),
        ({"diagnostic_ratio": Decimal("1.000000")}, "numeric public payload values"),
        ({"status_note": "buy"}, "unsafe public payload value"),
        ({"status_note": "sell"}, "unsafe public payload value"),
        ({"status_note": "recommendation"}, "unsafe public payload value"),
        ({"status_note": "wallet"}, "unsafe public payload value"),
        ({**payload, "paper_only": False}, "paper_only"),
    )

    for extra_payload, match in unsafe_payloads:
        with pytest.raises(ValueError, match=match):
            module.validate_candidate_decision_threshold_margin_score_public_payload(
                {**payload, **extra_payload},
            )


def test_payload_digest_and_report_consistency_are_deterministic() -> None:
    module = api()
    first = score()
    second = score()

    assert first == second
    assert first.payload == second.payload
    assert first.report_sha256 == second.report_sha256
    assert first.derived_validation_digest == second.derived_validation_digest
    json.dumps(first.payload, allow_nan=False, sort_keys=True)

    rebuilt = module.CandidateDecisionThresholdMarginScoreReport(**public_values(first))
    assert rebuilt == first
    assert rebuilt.payload == first.payload

    with pytest.raises(ValueError, match="threshold_margin_score must match"):
        replace(first, threshold_margin_score=d("0.500000"))
    with pytest.raises(ValueError, match="status must match"):
        replace(first, status="block")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(first, reason_codes=("candidate_decision_threshold_margin_score",))
    with pytest.raises(ValueError, match="report_sha256 must match"):
        replace(first, report_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(first, derived_validation_digest="0" * 64)


def test_config_thresholds_and_source_have_no_io_or_live_action_surface() -> None:
    module = api()

    with pytest.raises(ValueError, match="min_watch_net_threshold_margin"):
        config(min_watch_net_threshold_margin=d("0.200000"))
    with pytest.raises(ValueError, match="min_watch_margin_coverage_ratio"):
        config(min_watch_margin_coverage_ratio=d("3.000000"))
    with pytest.raises(ValueError, match="min_watch_evidence_confidence"):
        config(min_watch_evidence_confidence=d("0.800000"))
    with pytest.raises(ValueError, match="min_watch_threshold_margin_score"):
        config(min_watch_threshold_margin_score=d("0.700000"))

    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "exec", "eval"}

    banned_import_roots = {
        "asyncio",
        "csv",
        "http",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    assert not (set(imports) & banned_import_roots)

    lowered = source.lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_ref",
        "source_url",
        "source_text",
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "place_order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "dsn",
        "table",
    ):
        assert forbidden not in lowered

    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_THRESHOLD_MARGIN_SCORE_CONFIG_VERSION",
        "THRESHOLD_MARGIN_STATUSES",
        "CandidateDecisionThresholdMarginScoreConfig",
        "CandidateDecisionThresholdMarginScoreInput",
        "CandidateDecisionThresholdMarginScoreReport",
        "score_candidate_decision_threshold_margin_score",
        "candidate_decision_threshold_margin_score_payload",
        "validate_candidate_decision_threshold_margin_score_public_payload",
        "validate_candidate_decision_threshold_margin_score_report",
    )
