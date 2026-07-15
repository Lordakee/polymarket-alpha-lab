from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, get_type_hints

import pytest

import polymarket_alpha_lab.probability_event_bayesian_prior_update_readiness_report as api
from polymarket_alpha_lab.probability_event_bayesian_prior_update_readiness_report import (
    BAYESIAN_PRIOR_UPDATE_STATUSES,
    ProbabilityEventBayesianPriorUpdateReadinessInput,
    ProbabilityEventBayesianPriorUpdateReadinessReport,
    build_probability_event_bayesian_prior_update_readiness_report,
    probability_event_bayesian_prior_update_readiness_report_digest,
    probability_event_bayesian_prior_update_readiness_report_to_payload,
    validate_probability_event_bayesian_prior_update_readiness_public_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_bayesian_prior_update_readiness_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(
    **overrides: object,
) -> ProbabilityEventBayesianPriorUpdateReadinessInput:
    values = {
        "prior_probability": d("0.400000"),
        "new_evidence_probability": d("0.700000"),
        "evidence_reliability_probability": d("0.800000"),
        "base_rate_sample_count": d("250.000000"),
        "calibration_error_probability": d("0.050000"),
    }
    values.update(overrides)
    return ProbabilityEventBayesianPriorUpdateReadinessInput(**values)


def report(
    **overrides: object,
) -> ProbabilityEventBayesianPriorUpdateReadinessReport:
    return build_probability_event_bayesian_prior_update_readiness_report(
        readiness_input(**overrides),
    )


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_update_status_vocabulary_is_exact() -> None:
    assert BAYESIAN_PRIOR_UPDATE_STATUSES == (
        "ready",
        "manual_review",
        "blocked",
    )


def test_ready_inputs_emit_decimal_only_readonly_payload_and_digest() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventBayesianPriorUpdateReadinessReport
    assert is_dataclass(first)
    assert first.update_status == "ready"
    assert first.posterior_probability == d("0.592000")
    assert first.reason_codes == (
        "probability_event_bayesian_prior_update_ready",
    )
    assert first.manual_next_step == (
        "Record the research-only posterior update for manual review; no "
        "parameter, order, or execution change is authorized."
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second

    payload = probability_event_bayesian_prior_update_readiness_report_to_payload(first)
    assert first.public_payload == payload
    assert payload == {
        "prior_probability": "0.400000",
        "new_evidence_probability": "0.700000",
        "evidence_reliability_probability": "0.800000",
        "base_rate_sample_count": "250.000000",
        "calibration_error_probability": "0.050000",
        "update_status": "ready",
        "posterior_probability": "0.592000",
        "reason_codes": [
            "probability_event_bayesian_prior_update_ready",
        ],
        "manual_next_step": (
            "Record the research-only posterior update for manual review; no "
            "parameter, order, or execution change is authorized."
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    expected_digest = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert first.payload_digest == second.payload_digest
    assert (
        probability_event_bayesian_prior_update_readiness_report_digest(first)
        == expected_digest
    )
    assert (
        validate_probability_event_bayesian_prior_update_readiness_public_payload(
            payload,
        )
        == payload
    )
    assert_no_runtime_numbers(payload)


def test_manual_review_reasons_are_deterministic_without_overriding_posterior() -> None:
    result = report(
        evidence_reliability_probability=d("0.450000"),
        base_rate_sample_count=d("25.000000"),
        calibration_error_probability=d("0.180000"),
    )

    assert result.update_status == "manual_review"
    assert result.posterior_probability == d("0.484000")
    assert result.reason_codes == (
        "bayesian_prior_update_low_evidence_reliability",
        "bayesian_prior_update_sparse_base_rate_sample",
        "bayesian_prior_update_high_calibration_error",
    )
    assert result.manual_next_step == (
        "Review reliability, base-rate depth, and calibration error before "
        "using the posterior as a research note."
    )


def test_probability_domain_or_mode_flag_gaps_block_the_report() -> None:
    result = report(
        prior_probability=d("1.000000"),
        new_evidence_probability=d("0.000000"),
        paper_only=False,
        readonly=False,
    )

    assert result.update_status == "blocked"
    assert result.posterior_probability == d("1.000000")
    assert result.reason_codes == (
        "bayesian_prior_update_prior_at_closed_boundary",
        "bayesian_prior_update_evidence_at_closed_boundary",
        "bayesian_prior_update_paper_only_flag_not_set",
        "bayesian_prior_update_readonly_flag_not_set",
    )
    assert result.manual_next_step == (
        "Do not use this posterior in research notes until blocked inputs and "
        "mode flags are corrected."
    )
    assert result.public_payload["paper_only"] is True
    assert result.public_payload["readonly"] is True


def test_dataclasses_are_frozen_exact_type_and_decimal_only() -> None:
    source = readiness_input()
    result = report()

    assert is_dataclass(ProbabilityEventBayesianPriorUpdateReadinessInput)
    assert is_dataclass(ProbabilityEventBayesianPriorUpdateReadinessReport)
    assert source.__dataclass_params__.frozen
    assert result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        result.update_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventBayesianPriorUpdateReadinessInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventBayesianPriorUpdateReadinessReport):
            pass

    with pytest.raises(ValueError, match="prior_probability"):
        readiness_input(prior_probability=1)
    with pytest.raises(ValueError, match="new_evidence_probability"):
        readiness_input(new_evidence_probability="0.5")
    with pytest.raises(ValueError, match="base_rate_sample_count"):
        readiness_input(base_rate_sample_count=d("-1.000000"))
    with pytest.raises(ValueError, match="posterior_probability"):
        replace(result, posterior_probability=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="posterior_probability"):
        replace(result, posterior_probability=_DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="paper_only"):
        readiness_input(paper_only=1)

    hints = get_type_hints(ProbabilityEventBayesianPriorUpdateReadinessReport)
    assert hints["posterior_probability"] is Decimal
    for field in fields(result):
        value = getattr(result, field.name)
        if field.name.endswith("_probability") or field.name == "base_rate_sample_count":
            assert type(value) is Decimal


def test_manual_report_construction_must_match_derived_findings() -> None:
    with pytest.raises(ValueError, match="reason_codes"):
        ProbabilityEventBayesianPriorUpdateReadinessReport(
            prior_probability=d("0.400000"),
            new_evidence_probability=d("0.700000"),
            evidence_reliability_probability=d("0.800000"),
            base_rate_sample_count=d("250.000000"),
            calibration_error_probability=d("0.050000"),
            update_status="ready",
            posterior_probability=d("0.592000"),
            reason_codes=("bayesian_prior_update_high_calibration_error",),
            manual_next_step=(
                "Record the research-only posterior update for manual review; no "
                "parameter, order, or execution change is authorized."
            ),
        )


def test_public_payload_tamper_checks_and_no_live_io_surface() -> None:
    payload = dict(report().public_payload)

    with pytest.raises(ValueError, match="posterior_probability"):
        validate_probability_event_bayesian_prior_update_readiness_public_payload(
            {**payload, "posterior_probability": "0.500000"},
        )
    with pytest.raises(ValueError, match="update_status"):
        validate_probability_event_bayesian_prior_update_readiness_public_payload(
            {**payload, "update_status": "blocked"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        validate_probability_event_bayesian_prior_update_readiness_public_payload(
            {**payload, "paper_only": False},
        )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "auth",
        "wallet",
        "private_key",
        "secret",
        "live",
        "submit_order",
        "cancel_order",
        "execute_order",
        "auto_trade",
        "write_text",
        "write_bytes",
        "jsonl",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source)
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)
        elif isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id.lower())
            elif isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr.lower())

    assert not float_constants
    assert imported_roots.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "psycopg",
            "supabase",
            "web3",
        },
    )
    assert call_names.isdisjoint(
        {
            "connect",
            "cursor",
            "delete",
            "execute",
            "executemany",
            "fetch",
            "insert",
            "open",
            "post",
            "put",
            "rollback",
            "send",
            "sign",
            "submit",
            "upsert",
            "write",
            "write_text",
            "write_bytes",
        },
    )

    for public_name in api.__all__:
        lowered = public_name.lower()
        assert "auth" not in lowered
        assert "wallet" not in lowered
        assert "order" not in lowered
        assert "trade" not in lowered
        assert "key" not in lowered


def test_payload_digest_changes_when_update_inputs_change() -> None:
    ready = report()
    reliability_review = report(evidence_reliability_probability=d("0.450000"))
    blocked = report(prior_probability=d("1.000000"))

    assert ready.payload_digest != reliability_review.payload_digest
    assert ready.payload_digest != blocked.payload_digest
    assert ready.public_payload != reliability_review.public_payload
