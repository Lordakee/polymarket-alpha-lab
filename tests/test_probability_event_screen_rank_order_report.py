from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.probability_event_screen_rank_order_report import (
    ProbabilityEventScreenRankOrderReport,
    build_probability_event_screen_rank_order_report,
    probability_event_screen_rank_order_report_payload,
)


MODULE_PATH = Path("src/polymarket_alpha_lab/probability_event_screen_rank_order_report.py")
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def report(**overrides: object) -> ProbabilityEventScreenRankOrderReport:
    values = {
        "candidate_count": d("12.000000"),
        "quality_index_score": d("0.880000"),
        "edge_to_threshold_probability": d("0.160000"),
        "time_decay_urgency_score": d("0.420000"),
        "source_reliability_score": d("0.900000"),
        "liquidity_exit_ready": True,
        "manual_decision_gate_ready": True,
        "operator_safety_ready": True,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return build_probability_event_screen_rank_order_report(**values)


def assert_no_runtime_numbers(value: Any) -> None:
    if type(value) is int or type(value) is float or type(value) is Decimal:
        pytest.fail(f"payload contains runtime numeric value: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            for forbidden in ("wallet", "auth", "database", "network"):
                assert forbidden not in lowered_key
            for forbidden in (
                "submit_order",
                "cancel_order",
                "replace_order",
                "create_order",
            ):
                assert forbidden not in lowered_key
            assert_no_runtime_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_runtime_numbers(item)


def test_ready_rank_order_report_emits_decimal_string_payload_and_digest() -> None:
    ranked = report()

    assert isinstance(ranked, ProbabilityEventScreenRankOrderReport)
    assert ranked.rank_order_ready is True
    assert ranked.ranking_band == "top"
    assert ranked.top_candidate_count == d("3.000000")
    assert ranked.ready_ratio == d("1.000000")
    assert ranked.blocked_reason_codes == ()
    assert ranked.attention_reason_codes == ()
    assert len(ranked.digest) == 64

    payload = ranked.public_payload
    assert payload == probability_event_screen_rank_order_report_payload(ranked)
    assert payload["rank_order_ready"] is True
    assert payload["ranking_band"] == "top"
    assert payload["candidate_count"] == "12.000000"
    assert payload["quality_index_score"] == "0.880000"
    assert payload["top_candidate_count"] == "3.000000"
    assert payload["ready_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["digest"] == ranked.digest
    assert_no_runtime_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_blocked_rank_order_report_requires_all_hard_gates() -> None:
    ranked = report(
        candidate_count=d("10.000000"),
        quality_index_score=d("0.780000"),
        edge_to_threshold_probability=d("0.130000"),
        time_decay_urgency_score=d("0.700000"),
        source_reliability_score=d("0.810000"),
        liquidity_exit_ready=False,
        manual_decision_gate_ready=False,
        operator_safety_ready=False,
    )

    assert ranked.rank_order_ready is False
    assert ranked.ranking_band == "blocked"
    assert ranked.top_candidate_count == ZERO
    assert ranked.ready_ratio == ZERO
    assert ranked.blocked_reason_codes == (
        "liquidity_exit_not_ready",
        "manual_decision_gate_not_ready",
        "operator_safety_not_ready",
    )
    assert ranked.attention_reason_codes == ()


def test_watch_rank_order_report_surfaces_attention_reasons() -> None:
    ranked = report(
        candidate_count=d("5.000000"),
        quality_index_score=d("0.590000"),
        edge_to_threshold_probability=d("0.020000"),
        time_decay_urgency_score=d("0.850000"),
        source_reliability_score=d("0.550000"),
    )

    assert ranked.rank_order_ready is False
    assert ranked.ranking_band == "watch"
    assert ranked.top_candidate_count == d("1.000000")
    assert ranked.ready_ratio == d("0.200000")
    assert ranked.blocked_reason_codes == ()
    assert ranked.attention_reason_codes == (
        "edge_to_threshold_probability_low",
        "quality_index_score_low",
        "source_reliability_score_low",
        "time_decay_urgency_high",
    )


def test_empty_candidate_set_is_reportable_but_not_rank_order_ready() -> None:
    ranked = report(
        candidate_count=ZERO,
        quality_index_score=ZERO,
        edge_to_threshold_probability=ZERO,
        time_decay_urgency_score=ZERO,
        source_reliability_score=ZERO,
    )

    assert ranked.rank_order_ready is False
    assert ranked.ranking_band == "watch"
    assert ranked.top_candidate_count == ZERO
    assert ranked.ready_ratio == ZERO
    assert ranked.blocked_reason_codes == ()
    assert ranked.attention_reason_codes == (
        "candidate_batch_empty",
        "edge_to_threshold_probability_low",
        "quality_index_score_low",
        "source_reliability_score_low",
    )


def test_frozen_flags_decimal_validation_and_report_consistency() -> None:
    ranked = report()

    assert is_dataclass(ProbabilityEventScreenRankOrderReport)
    assert ranked.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        ranked.ranking_band = "blocked"  # type: ignore[misc]

    for field in fields(ranked):
        value = getattr(ranked, field.name)
        if field.name.endswith("_count") or field.name.endswith("_score"):
            assert type(value) is Decimal
        if "probability" in field.name or field.name == "ready_ratio":
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        report(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(ranked, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(ranked, readonly=False)
    with pytest.raises(ValueError, match="candidate_count"):
        report(candidate_count=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quality_index_score"):
        report(quality_index_score=0.88)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="edge_to_threshold_probability"):
        report(edge_to_threshold_probability=_DecimalSubclass("0.160000"))
    with pytest.raises(ValueError, match="liquidity_exit_ready"):
        report(liquidity_exit_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ranking_band"):
        replace(ranked, ranking_band="ready")
    with pytest.raises(ValueError, match="top_candidate_count"):
        replace(ranked, top_candidate_count=d("4.000000"))
    with pytest.raises(ValueError, match="ready_ratio"):
        replace(ranked, ready_ratio=d("0.500000"))


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
