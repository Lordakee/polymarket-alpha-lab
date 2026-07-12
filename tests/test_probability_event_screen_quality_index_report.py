from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_screen_quality_index_report import (
    QUALITY_BANDS,
    ProbabilityEventScreenQualityIndexReport,
    build_probability_event_screen_quality_index_report,
    probability_event_screen_quality_index_report_digest,
    probability_event_screen_quality_index_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/probability_event_screen_quality_index_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventScreenQualityIndexReport:
    values = {
        "source_reliability_score": d("0.900000"),
        "due_diligence_depth_score": d("0.800000"),
        "information_gap_score": d("0.100000"),
        "resolution_rule_clarity_score": d("0.850000"),
        "liquidity_exit_risk_score": d("0.200000"),
        "team_memory_quality_score": d("0.750000"),
        "operator_safety_ready": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return build_probability_event_screen_quality_index_report(**values)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in ("wallet", "auth", "order", "database", "network"):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_quality_band_vocabulary_is_exact() -> None:
    assert QUALITY_BANDS == ("ready", "watch", "blocked")


def test_ready_quality_index_report_emits_decimal_payload_and_digest() -> None:
    quality = report()

    assert isinstance(quality, ProbabilityEventScreenQualityIndexReport)
    assert quality.quality_index_score == d("0.833333")
    assert quality.quality_band == "ready"
    assert quality.ready_ratio == ONE
    assert quality.blocked_reason_codes == ()
    assert quality.attention_reason_codes == ()
    assert len(quality.digest) == 64
    assert quality.digest == probability_event_screen_quality_index_report_digest(quality)
    assert quality.public_payload == probability_event_screen_quality_index_report_payload(
        quality,
    )

    payload = quality.public_payload
    assert payload["quality_index_score"] == "0.833333"
    assert payload["quality_band"] == "ready"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["source_reliability_score"] == "0.900000"
    assert payload["information_gap_score"] == "0.100000"
    assert payload["liquidity_exit_risk_score"] == "0.200000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["digest"] == quality.digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_blocked_operator_safety_and_hard_quality_failures_are_deterministic() -> None:
    quality = report(
        source_reliability_score=d("0.500000"),
        due_diligence_depth_score=d("0.400000"),
        information_gap_score=d("0.700000"),
        resolution_rule_clarity_score=d("0.450000"),
        liquidity_exit_risk_score=d("0.650000"),
        team_memory_quality_score=d("0.300000"),
        operator_safety_ready=False,
    )

    assert quality.quality_index_score == d("0.383333")
    assert quality.quality_band == "blocked"
    assert quality.ready_ratio == ZERO
    assert quality.blocked_reason_codes == (
        "information_gap_score_high",
        "liquidity_exit_risk_score_high",
        "operator_safety_not_ready",
        "resolution_rule_clarity_score_low",
        "source_reliability_score_low",
        "team_memory_quality_score_low",
    )
    assert quality.attention_reason_codes == (
        "due_diligence_depth_score_low",
        "quality_index_score_low",
    )


def test_watch_band_preserves_partial_ready_ratio_with_attention_reasons() -> None:
    quality = report(
        source_reliability_score=d("0.680000"),
        due_diligence_depth_score=d("0.550000"),
        information_gap_score=d("0.300000"),
        resolution_rule_clarity_score=d("0.650000"),
        liquidity_exit_risk_score=d("0.400000"),
        team_memory_quality_score=d("0.620000"),
    )

    assert quality.quality_index_score == d("0.633333")
    assert quality.quality_band == "watch"
    assert quality.ready_ratio == d("0.633333")
    assert quality.blocked_reason_codes == ()
    assert quality.attention_reason_codes == (
        "due_diligence_depth_score_low",
        "information_gap_score_elevated",
        "liquidity_exit_risk_score_elevated",
        "source_reliability_score_watch",
    )


def test_dataclass_is_frozen_decimal_only_and_flags_are_enforced() -> None:
    quality = report()

    assert is_dataclass(ProbabilityEventScreenQualityIndexReport)
    assert quality.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        quality.quality_band = "blocked"  # type: ignore[misc]

    for field in fields(quality):
        value = getattr(quality, field.name)
        if field.name.endswith("_score") or field.name == "ready_ratio":
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(quality, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(quality, readonly=False)
    with pytest.raises(ValueError, match="source_reliability_score"):
        report(source_reliability_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="due_diligence_depth_score"):
        report(due_diligence_depth_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="information_gap_score"):
        report(information_gap_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="liquidity_exit_risk_score"):
        report(liquidity_exit_risk_score=d("1.100000"))
    with pytest.raises(ValueError, match="operator_safety_ready"):
        report(operator_safety_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quality_index_score"):
        ProbabilityEventScreenQualityIndexReport(
            source_reliability_score=d("0.900000"),
            due_diligence_depth_score=d("0.800000"),
            information_gap_score=d("0.100000"),
            resolution_rule_clarity_score=d("0.850000"),
            liquidity_exit_risk_score=d("0.200000"),
            team_memory_quality_score=d("0.750000"),
            operator_safety_ready=True,
            quality_index_score=d("0.790000"),
            quality_band="ready",
            blocked_reason_codes=(),
            attention_reason_codes=(),
            ready_ratio=ONE,
        )


def test_pure_readonly_report_only_module_has_no_io_or_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "live trading",
        "wallet",
        "private_key",
        "authentication",
        "database",
        "network",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "urlopen",
        "connect(",
        "execute(",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "open",
        "connect",
        "execute",
        "request",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
