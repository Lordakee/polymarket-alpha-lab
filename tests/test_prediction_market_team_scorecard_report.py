from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "prediction_market_team_scorecard_report.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.prediction_market_team_scorecard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_scorecard(**overrides: object):
    module = api()
    values = {
        "team_code": "macro_rates",
        "domain": "central_bank_policy",
        "screened_market_count": d("20"),
        "ready_recommendation_count": d("12"),
        "blocked_recommendation_count": d("3"),
        "average_edge_to_threshold_probability": d("0.700000"),
        "average_source_reliability_score": d("0.900000"),
        "average_memory_quality_score": d("0.800000"),
        "settled_feedback_sample_count": d("6"),
    }
    values.update(overrides)
    return module.build_prediction_market_team_scorecard_report(**values)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_decimal_scorecard_payload_and_digest() -> None:
    report = build_scorecard()

    assert is_dataclass(report)
    assert report.team_code == "macro_rates"
    assert report.domain == "central_bank_policy"
    assert report.ready_ratio == d("0.600000")
    assert report.team_score == d("0.735000")
    assert report.score_band == "watch"
    assert report.improvement_reason_codes == (
        "ready_ratio_watch",
        "recommendation_block_rate_watch",
        "edge_to_threshold_watch",
        "source_reliability_strong",
        "memory_quality_strong",
        "settled_feedback_adequate",
        "prediction_market_team_scorecard_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.digest) == 64

    payload = report.public_payload
    assert payload == {
        "team_code": "macro_rates",
        "domain": "central_bank_policy",
        "screened_market_count": "20",
        "ready_recommendation_count": "12",
        "blocked_recommendation_count": "3",
        "average_edge_to_threshold_probability": "0.700000",
        "average_source_reliability_score": "0.900000",
        "average_memory_quality_score": "0.800000",
        "settled_feedback_sample_count": "6",
        "ready_ratio": "0.600000",
        "team_score": "0.735000",
        "score_band": "watch",
        "improvement_reason_codes": [
            "ready_ratio_watch",
            "recommendation_block_rate_watch",
            "edge_to_threshold_watch",
            "source_reliability_strong",
            "memory_quality_strong",
            "settled_feedback_adequate",
            "prediction_market_team_scorecard_watch",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "digest": report.digest,
    }
    assert_no_float_values(payload)


@pytest.mark.parametrize(
    (
        "screened",
        "ready",
        "blocked",
        "edge",
        "source",
        "memory",
        "feedback",
        "expected_ratio",
        "expected_score",
        "expected_band",
        "expected_final_reason",
    ),
    (
        (
            d("10"),
            d("9"),
            d("0"),
            d("0.900000"),
            d("0.900000"),
            d("0.900000"),
            d("12"),
            d("0.900000"),
            d("0.930000"),
            "strong",
            "prediction_market_team_scorecard_strong",
        ),
        (
            d("10"),
            d("1"),
            d("8"),
            d("0.100000"),
            d("0.300000"),
            d("0.200000"),
            d("0"),
            d("0.100000"),
            d("0.165000"),
            "blocked",
            "prediction_market_team_scorecard_blocked",
        ),
        (
            d("0"),
            d("0"),
            d("0"),
            d("0.900000"),
            d("0.900000"),
            d("0.900000"),
            d("0"),
            d("0.000000"),
            d("0.540000"),
            "blocked",
            "prediction_market_team_scorecard_blocked",
        ),
    ),
)
def test_score_bands_cover_strong_blocked_and_empty_screening(
    screened: Decimal,
    ready: Decimal,
    blocked: Decimal,
    edge: Decimal,
    source: Decimal,
    memory: Decimal,
    feedback: Decimal,
    expected_ratio: Decimal,
    expected_score: Decimal,
    expected_band: str,
    expected_final_reason: str,
) -> None:
    report = build_scorecard(
        screened_market_count=screened,
        ready_recommendation_count=ready,
        blocked_recommendation_count=blocked,
        average_edge_to_threshold_probability=edge,
        average_source_reliability_score=source,
        average_memory_quality_score=memory,
        settled_feedback_sample_count=feedback,
    )

    assert report.ready_ratio == expected_ratio
    assert report.team_score == expected_score
    assert report.score_band == expected_band
    assert report.improvement_reason_codes[-1] == expected_final_reason


def test_dataclass_is_frozen_decimal_only_and_revalidates_digest() -> None:
    report = build_scorecard()

    with pytest.raises(FrozenInstanceError):
        report.paper_only = False  # type: ignore[misc]

    decimal_fields = {
        "screened_market_count",
        "ready_recommendation_count",
        "blocked_recommendation_count",
        "average_edge_to_threshold_probability",
        "average_source_reliability_score",
        "average_memory_quality_score",
        "settled_feedback_sample_count",
        "team_score",
        "ready_ratio",
    }
    for field in fields(report):
        value = getattr(report, field.name)
        if field.name in decimal_fields:
            assert type(value) is Decimal

    with pytest.raises(ValueError, match="digest must match public payload"):
        replace(report, digest="0" * 64)
    with pytest.raises(ValueError, match="team_score must match score inputs"):
        replace(report, team_score=d("0.700000"))


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "screened_market_count",
            _DecimalSubclass("20"),
            "screened_market_count must be exactly Decimal",
        ),
        (
            "ready_recommendation_count",
            d("1.5"),
            "ready_recommendation_count must be an integral Decimal",
        ),
        (
            "blocked_recommendation_count",
            d("-1"),
            "blocked_recommendation_count must be >= 0.000000",
        ),
        (
            "average_edge_to_threshold_probability",
            d("1.000001"),
            "average_edge_to_threshold_probability must be <= 1.000000",
        ),
        (
            "average_source_reliability_score",
            d("0.9000004"),
            "average_source_reliability_score must use six decimal places or fewer",
        ),
        (
            "average_memory_quality_score",
            Decimal("NaN"),
            "average_memory_quality_score must be finite",
        ),
    ),
)
def test_validation_rejects_non_decimal_out_of_range_and_fractional_counts(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_scorecard(**{field_name: bad_value})


def test_rejects_inconsistent_counts_disabled_flags_and_unsafe_public_text() -> None:
    with pytest.raises(
        ValueError,
        match="ready and blocked recommendation counts must not exceed screened_market_count",
    ):
        build_scorecard(
            screened_market_count=d("4"),
            ready_recommendation_count=d("3"),
            blocked_recommendation_count=d("2"),
        )

    with pytest.raises(ValueError, match="paper_only must be True"):
        build_scorecard(paper_only=False)
    with pytest.raises(ValueError, match="unsafe public payload"):
        build_scorecard(team_code="live_team")
    with pytest.raises(ValueError, match="unsafe public payload"):
        build_scorecard(domain="wallet_auth")


def test_module_scope_is_report_only_without_network_database_or_execution_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
