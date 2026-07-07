from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_decision_explainability",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def score(**overrides: object):
    module = api()
    values = {
        "score_name": "evidence_traceability",
        "status": "pass",
        "score": d("0.910000"),
        "weight": d("1.000000"),
        "summary": "Evidence lineage is complete.",
        "reason_codes": ("evidence_complete",),
    }
    values.update(overrides)
    return module.StrategyDecisionExplainerScore(**values)


def explanation(*scores: object):
    module = api()
    return module.build_strategy_decision_explanation(scores)


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_pass_explanation_is_auditable_redacted_and_digest_stable() -> None:
    module = api()
    result = explanation(
        score(
            score_name="source_lag",
            status="pass",
            score=d("0.880000"),
            summary="Source timing is within the review window.",
            reason_codes=("source_lag_clear",),
        ),
        score(
            score_name="evidence_traceability",
            status="pass",
            score=d("0.940000"),
            summary="Evidence lineage is complete.",
            reason_codes=("evidence_complete",),
        ),
    )

    assert is_dataclass(result)
    assert result.public_status == "pass"
    assert result.score_count == d("2")
    assert result.pass_score_count == d("2")
    assert result.watch_score_count == d("0")
    assert result.block_score_count == d("0")
    assert result.weighted_score == d("0.910000")
    assert result.explanation_digest == module.strategy_decision_explanation_digest(
        result.payload,
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = result.payload
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert payload["public_status"] == "pass"
    assert payload["weighted_score"] == "0.910000"
    assert payload["rows"][0]["score_name"] == "evidence_traceability"
    assert payload["rows"][1]["score_name"] == "source_lag"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "buy" not in rendered
    assert "sell" not in rendered
    assert "recommend" not in rendered
    assert_no_int_or_float_values(payload)


def test_watch_and_block_explanations_surface_review_reasons() -> None:
    watched = explanation(
        score(status="pass", score=d("0.900000"), reason_codes=("evidence_complete",)),
        score(
            score_name="resolution_timing",
            status="watch",
            score=d("0.550000"),
            summary="Resolution timing needs human review.",
            reason_codes=("timing_watch",),
        ),
    )
    blocked = explanation(
        score(status="pass", score=d("0.900000"), reason_codes=("evidence_complete",)),
        score(
            score_name="rule_completeness",
            status="block",
            score=d("0.200000"),
            summary="Resolution rule is incomplete.",
            reason_codes=("rule_incomplete",),
        ),
    )

    assert watched.public_status == "watch"
    assert watched.reason_codes == (
        "decision_explanation_watch",
        "timing_watch",
    )
    assert watched.review_notes == (
        "resolution_timing: Resolution timing needs human review.",
    )

    assert blocked.public_status == "block"
    assert blocked.reason_codes == (
        "decision_explanation_block",
        "rule_incomplete",
    )
    assert blocked.review_notes == (
        "rule_completeness: Resolution rule is incomplete.",
    )


def test_conflict_explanation_for_mixed_statuses_is_watch_without_block() -> None:
    result = explanation(
        score(
            score_name="crowd_overreaction",
            status="pass",
            score=d("0.910000"),
            reason_codes=("crowd_reaction_clear",),
        ),
        score(
            score_name="historical_resolution_pattern",
            status="watch",
            score=d("0.520000"),
            summary="Comparable history is mixed.",
            reason_codes=("history_pattern_mixed",),
        ),
        score(
            score_name="source_revision_frequency",
            status="pass",
            score=d("0.840000"),
            reason_codes=("revision_frequency_clear",),
        ),
    )

    assert result.public_status == "watch"
    assert result.reason_codes == (
        "decision_explanation_watch",
        "status_conflict_present",
        "crowd_reaction_clear",
        "history_pattern_mixed",
        "revision_frequency_clear",
    )
    assert "conflicting score statuses require review" in result.review_notes


def test_type_validation_flags_freezing_and_decimal_only_payload() -> None:
    module = api()
    item = score()
    result = explanation(item)

    assert module.StrategyDecisionExplainerScore.__dataclass_params__.frozen
    assert module.StrategyDecisionExplanationRow.__dataclass_params__.frozen
    assert module.StrategyDecisionExplanation.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        item.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.public_status = "block"  # type: ignore[misc]

    for value in (result, *result.rows):
        for item_field in fields(value):
            if item_field.name.endswith(("_count", "_score", "_weight")):
                assert type(getattr(value, item_field.name)) is Decimal

    with pytest.raises(ValueError, match="score must be a Decimal"):
        score(score=0.9)
    with pytest.raises(ValueError, match="weight must be a Decimal"):
        score(weight=1)
    with pytest.raises(ValueError, match="status must be one of"):
        score(status="clear")
    with pytest.raises(ValueError, match="paper_only must be True"):
        score(paper_only=False)
    with pytest.raises(ValueError, match="scores must contain"):
        explanation(object())
    with pytest.raises(ValueError, match="payload must be a StrategyDecisionExplanation"):
        module.strategy_decision_explanation_payload(object())

    assert_no_int_or_float_values(result.payload)


def test_public_payload_rejects_leaky_identifiers_sources_and_action_language() -> None:
    module = api()
    leaky_values = (
        ("score_name", "market_id_alpha"),
        ("summary", "Question slug mentions election market"),
        ("summary", "Source URL https://example.invalid/ref"),
        ("summary", "DSN table public.orders"),
        ("summary", "token secret leaked"),
        ("summary", "wallet auth required"),
        ("summary", "buy this outcome"),
        ("summary", "sell this outcome"),
        ("summary", "recommendation is strong"),
        ("reason_codes", ("source_ref_visible",)),
    )
    for field_name, value in leaky_values:
        with pytest.raises(ValueError, match=field_name) as exc:
            score(**{field_name: value})
        assert str(value) not in str(exc.value)

    with pytest.raises(ValueError, match="payload field"):
        module.strategy_decision_explanation_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "public_status": "pass",
                "market_id": "alpha",
            },
        )
    with pytest.raises(ValueError, match="public_status"):
        module.strategy_decision_explanation_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "public_status": "clear",
            },
        )


def test_deterministic_payload_digest_and_ordering() -> None:
    module = api()
    unordered = (
        score(
            score_name="zeta_review",
            status="pass",
            score=d("0.800000"),
            weight=d("0.500000"),
            reason_codes=("zeta_clear",),
        ),
        score(
            score_name="alpha_review",
            status="watch",
            score=d("0.600000"),
            weight=d("1.500000"),
            summary="Alpha check needs review.",
            reason_codes=("alpha_watch",),
        ),
    )

    first = explanation(*unordered)
    second = explanation(*reversed(unordered))
    assert first == second
    assert first.payload == second.payload
    assert first.payload["rows"][0]["score_name"] == "alpha_review"
    assert first.explanation_digest == second.explanation_digest

    canonical = json.dumps(first.payload, allow_nan=False, sort_keys=True, separators=(",", ":"))
    assert first.explanation_digest == sha256(canonical.encode("utf-8")).hexdigest()


def test_module_scope_has_no_io_persistence_trade_or_float_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "httpx",
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
    forbidden_call_names = {
        "connect",
        "execute",
        "float",
        "open",
        "print",
        "request",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            for name in names:
                assert name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                assert target.id not in forbidden_call_names
            if isinstance(target, ast.Attribute):
                assert target.attr not in forbidden_call_names
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)

    lowered = source.lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert forbidden not in lowered

    root = Path(__file__).resolve().parents[1]
    assert (root / "src/polymarket_alpha_lab/strategy_decision_explainability.py").exists()
