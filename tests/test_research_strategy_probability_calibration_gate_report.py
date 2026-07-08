from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_probability_calibration_gate_report import (
    CALIBRATION_GATE_STATUSES,
    DEFAULT_RESEARCH_STRATEGY_PROBABILITY_CALIBRATION_GATE_REPORT_CONFIG_VERSION,
    ResearchStrategyProbabilityCalibrationGateConfig,
    ResearchStrategyProbabilityCalibrationGateInput,
    ResearchStrategyProbabilityCalibrationGateReasonCodeCount,
    ResearchStrategyProbabilityCalibrationGateReport,
    ResearchStrategyProbabilityCalibrationGateRow,
    build_research_strategy_probability_calibration_gate_report,
    research_strategy_probability_calibration_gate_report_digest,
    research_strategy_probability_calibration_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyProbabilityCalibrationGateConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_PROBABILITY_CALIBRATION_GATE_REPORT_CONFIG_VERSION
        ),
        "min_pass_prior_calibration_bucket_quality": d("0.750000"),
        "min_watch_prior_calibration_bucket_quality": d("0.500000"),
        "min_pass_evidence_confidence": d("0.700000"),
        "min_watch_evidence_confidence": d("0.450000"),
        "max_pass_disagreement_pressure": d("0.150000"),
        "max_watch_disagreement_pressure": d("0.350000"),
        "max_pass_stale_estimate_age_seconds": d("86400.000000"),
        "max_watch_stale_estimate_age_seconds": d("259200.000000"),
    }
    values.update(overrides)
    return ResearchStrategyProbabilityCalibrationGateConfig(**values)


def input_row(
    research_key: str = "calibration-case-pass",
    calibration_bucket_label: str = "probability-bucket-60-70",
    *,
    prior_calibration_bucket_quality: Decimal = d("0.880000"),
    evidence_confidence: Decimal = d("0.820000"),
    disagreement_pressure: Decimal = d("0.080000"),
    estimate_age_seconds: Decimal = d("21600.000000"),
    sample_count: Decimal = d("42.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyProbabilityCalibrationGateInput:
    return ResearchStrategyProbabilityCalibrationGateInput(
        research_key=research_key,
        calibration_bucket_label=calibration_bucket_label,
        prior_calibration_bucket_quality=prior_calibration_bucket_quality,
        evidence_confidence=evidence_confidence,
        disagreement_pressure=disagreement_pressure,
        estimate_age_seconds=estimate_age_seconds,
        sample_count=sample_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchStrategyProbabilityCalibrationGateInput,
    cfg: ResearchStrategyProbabilityCalibrationGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyProbabilityCalibrationGateReport:
    return build_research_strategy_probability_calibration_gate_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_manual_probability_calibration_review() -> None:
    gate = report()

    assert type(gate) is ResearchStrategyProbabilityCalibrationGateReport
    assert is_dataclass(gate)
    assert CALIBRATION_GATE_STATUSES == ("pass", "watch", "block")
    assert gate.generated_at == GENERATED_AT
    assert (
        gate.config_version
        == "research-strategy-probability-calibration-gate-report-v0"
    )
    assert gate.input_count == ZERO
    assert gate.pass_count == ZERO
    assert gate.watch_count == ZERO
    assert gate.block_count == ZERO
    assert gate.average_calibration_readiness_score is None
    assert gate.min_prior_calibration_bucket_quality == ZERO
    assert gate.min_evidence_confidence == ZERO
    assert gate.max_disagreement_pressure == ZERO
    assert gate.max_stale_estimate_risk == ZERO
    assert gate.status == "block"
    assert gate.reason_codes == ("no_probability_calibration_inputs",)
    assert gate.reason_code_counts == (
        ResearchStrategyProbabilityCalibrationGateReasonCodeCount(
            reason_code="no_probability_calibration_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert gate.rows == ()
    assert gate.paper_only is True
    assert gate.report_only is True
    assert gate.readonly is True


def test_calibration_gate_scores_pass_watch_and_block_readiness() -> None:
    gate = report(
        input_row(
            "calibration-case-watch",
            prior_calibration_bucket_quality=d("0.650000"),
            evidence_confidence=d("0.760000"),
            disagreement_pressure=d("0.250000"),
            estimate_age_seconds=d("172800.000000"),
        ),
        input_row(
            "calibration-case-block",
            prior_calibration_bucket_quality=d("0.420000"),
            evidence_confidence=d("0.300000"),
            disagreement_pressure=d("0.600000"),
            estimate_age_seconds=d("400000.000000"),
            reason_codes=("analyst_escalated",),
        ),
        input_row("calibration-case-pass", reason_codes=("manual_check_complete",)),
    )

    assert gate.input_count == d("3.000000")
    assert gate.pass_count == d("1.000000")
    assert gate.watch_count == d("1.000000")
    assert gate.block_count == d("1.000000")
    assert gate.average_calibration_readiness_score == d("0.595833")
    assert gate.min_prior_calibration_bucket_quality == d("0.420000")
    assert gate.min_evidence_confidence == d("0.300000")
    assert gate.max_disagreement_pressure == d("0.600000")
    assert gate.max_stale_estimate_risk == d("1.000000")
    assert gate.status == "block"
    assert gate.reason_codes == (
        "probability_calibration_gate_block",
        "prior_calibration_bucket_quality_block",
        "evidence_confidence_block",
        "disagreement_pressure_block",
        "stale_estimate_risk_block",
        "prior_calibration_bucket_quality_watch",
        "disagreement_pressure_watch",
        "stale_estimate_risk_watch",
    )

    block_row, pass_row, watch_row = gate.rows
    assert type(block_row) is ResearchStrategyProbabilityCalibrationGateRow
    assert tuple(row.research_key for row in gate.rows) == (
        "calibration-case-block",
        "calibration-case-pass",
        "calibration-case-watch",
    )
    assert block_row.calibration_readiness_score == d("0.280000")
    assert block_row.stale_estimate_risk == d("1.000000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "disagreement_pressure_block",
        "evidence_confidence_block",
        "input_analyst_escalated",
        "manual_review_probability_calibration_block",
        "prior_calibration_bucket_quality_block",
        "probability_calibration_gate_block",
        "stale_estimate_risk_block",
    )
    assert pass_row.calibration_readiness_score == d("0.884167")
    assert pass_row.stale_estimate_risk == d("0.083333")
    assert pass_row.status == "pass"
    assert "probability_calibration_gate_pass" in pass_row.reason_codes
    assert "input_manual_check_complete" in pass_row.reason_codes
    assert watch_row.calibration_readiness_score == d("0.623333")
    assert watch_row.stale_estimate_risk == d("0.666667")
    assert watch_row.status == "watch"
    assert "prior_calibration_bucket_quality_watch" in watch_row.reason_codes
    assert "disagreement_pressure_watch" in watch_row.reason_codes
    assert "stale_estimate_risk_watch" in watch_row.reason_codes


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    first = report(
        input_row("calibration-case-z", reason_codes=("zeta", "alpha")),
        input_row("calibration-case-a", calibration_bucket_label="probability-bucket-40-50"),
    )
    second = report(
        input_row("calibration-case-a", calibration_bucket_label="probability-bucket-40-50"),
        input_row("calibration-case-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = research_strategy_probability_calibration_gate_report_payload(first)
    second_payload = research_strategy_probability_calibration_gate_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert research_strategy_probability_calibration_gate_report_digest(first) == (
        research_strategy_probability_calibration_gate_report_digest(second)
    )
    assert len(research_strategy_probability_calibration_gate_report_digest(first)) == 64
    assert first_payload["rows"][0]["calibration_readiness_score"] == "0.884167"
    assert first_payload["rows"][0]["sample_count"] == "42.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded
    assert not any(
        _has_forbidden_public_surface_key(key)
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_rows() -> None:
    populated = report(input_row())

    for value in (config(), input_row(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item_value is None:
                continue
            if item.name.endswith(("_count", "_score", "_quality", "_confidence", "_pressure", "_risk", "_seconds", "_ratio")):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].calibration_readiness_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="min_pass_evidence_confidence"):
        config(min_pass_evidence_confidence=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_watch_evidence_confidence"):
        config(min_watch_evidence_confidence=_DecimalSubclass("0.450000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            input_row(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_key"):
        input_row(" calibration-case-pass")
    with pytest.raises(ValueError, match="research_key"):
        input_row("raw-calibration-case")
    with pytest.raises(ValueError, match="prior_calibration_bucket_quality"):
        input_row(prior_calibration_bucket_quality=0.88)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="disagreement_pressure"):
        input_row(disagreement_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="sample_count"):
        input_row(sample_count=d("1.500000"))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row(), paper_only=False)
    with pytest.raises(ValueError, match="calibration_readiness_score"):
        replace(populated.rows[0], calibration_readiness_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(populated, status="watch")


def test_owned_module_has_no_execution_trading_or_raw_public_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_probability_calibration_gate_report.py"
    )
    text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_text",
    )

    assert all(term not in text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _has_forbidden_public_surface_key(key: str) -> bool:
    return key in {
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_text",
        "source_url",
        "source_reference",
        "raw_text",
    }
