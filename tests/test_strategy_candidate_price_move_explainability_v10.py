from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_candidate_price_move_explainability_v10"
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def record(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "previous_probability": d("0.400000"),
        "current_probability": d("0.450000"),
        "evidence_age_minutes": d("30.000000"),
        "source_alignment_score": d("0.950000"),
        "liquidity_support_score": d("0.900000"),
        "reversal_pressure_score": d("0.100000"),
        "reason_codes": ("candidate_input",),
    }
    values.update(overrides)
    return module.StrategyCandidatePriceMoveExplainabilityRecord(**values)


def report(*records: object, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_candidate_price_move_explainability_report(
        records,
        generated_at=generated_at,
    )


def assert_no_public_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_int_or_float_values(item)


def test_scores_explained_watch_and_unexplained_price_moves() -> None:
    result = report(
        record(
            candidate_id="explained-alpha",
            previous_probability=d("0.400000"),
            current_probability=d("0.450000"),
            evidence_age_minutes=d("30.000000"),
            source_alignment_score=d("0.950000"),
            liquidity_support_score=d("0.900000"),
            reversal_pressure_score=d("0.100000"),
        ),
        record(
            candidate_id="watch-alpha",
            previous_probability=d("0.500000"),
            current_probability=d("0.620000"),
            evidence_age_minutes=d("180.000000"),
            source_alignment_score=d("0.700000"),
            liquidity_support_score=d("0.600000"),
            reversal_pressure_score=d("0.400000"),
        ),
        record(
            candidate_id="unexplained-alpha",
            previous_probability=d("0.200000"),
            current_probability=d("0.390000"),
            evidence_age_minutes=d("420.000000"),
            source_alignment_score=d("0.300000"),
            liquidity_support_score=d("0.250000"),
            reversal_pressure_score=d("0.900000"),
        ),
    )

    assert result.config_version == "strategy-candidate-price-move-explainability-v10"
    assert result.candidate_count == d("3")
    assert result.explained_count == d("1")
    assert result.watch_count == d("1")
    assert result.unexplained_count == d("1")
    assert result.min_price_move_explainability_score == d("0.147500")
    assert result.max_absolute_move_bps == d("1900.000000")
    assert result.min_evidence_freshness_score == d("0.000000")
    assert result.min_source_alignment_score == d("0.300000")
    assert result.min_liquidity_support_score == d("0.250000")
    assert result.max_reversal_pressure_score == d("0.900000")
    assert result.status == "unexplained"
    assert result.reason_codes == (
        "strategy_candidate_price_move_explainability_unexplained",
        "price_move_explainability_score_unexplained",
        "move_bps_unexplained",
        "evidence_freshness_unexplained",
        "source_alignment_unexplained",
        "liquidity_support_unexplained",
        "reversal_pressure_unexplained",
        "strategy_candidate_price_move_explainability_watch",
        "price_move_explainability_score_watch",
        "move_bps_watch",
        "evidence_freshness_watch",
        "source_alignment_watch",
        "liquidity_support_watch",
        "reversal_pressure_watch",
        "strategy_candidate_price_move_explainability_explained",
        "evidence_supports_probability_move",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.status for row in result.results) == (
        "unexplained",
        "watch",
        "explained",
    )
    unexplained, watched, explained = result.results

    assert explained.absolute_move_bps == d("500.000000")
    assert explained.move_bps_explainability_score == d("0.750000")
    assert explained.evidence_freshness_score == d("0.916667")
    assert explained.reversal_relief_score == d("0.900000")
    assert explained.price_move_explainability_score == d("0.894167")
    assert explained.reason_codes == (
        "strategy_candidate_price_move_explainability_explained",
        "candidate_input",
        "evidence_supports_probability_move",
    )

    assert watched.absolute_move_bps == d("1200.000000")
    assert watched.move_bps_explainability_score == d("0.400000")
    assert watched.evidence_freshness_score == d("0.500000")
    assert watched.price_move_explainability_score == d("0.570000")
    assert watched.reason_codes == (
        "strategy_candidate_price_move_explainability_watch",
        "candidate_input",
        "move_bps_watch",
        "evidence_freshness_watch",
        "source_alignment_watch",
        "liquidity_support_watch",
        "reversal_pressure_watch",
        "price_move_explainability_score_watch",
    )

    assert unexplained.absolute_move_bps == d("1900.000000")
    assert unexplained.evidence_freshness_score == d("0.000000")
    assert unexplained.price_move_explainability_score == d("0.147500")
    assert unexplained.reason_codes == (
        "strategy_candidate_price_move_explainability_unexplained",
        "candidate_input",
        "move_bps_unexplained",
        "evidence_freshness_unexplained",
        "source_alignment_unexplained",
        "liquidity_support_unexplained",
        "reversal_pressure_unexplained",
        "price_move_explainability_score_unexplained",
    )


def test_payload_uses_decimal_strings_integrity_digests_and_no_public_numbers() -> None:
    module = api()
    result = report(record())

    payload = module.strategy_candidate_price_move_explainability_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["min_price_move_explainability_score"] == "0.894167"
    assert payload["report_integrity_digest"] == result.report_integrity_digest
    assert len(payload["report_integrity_digest"]) == 64
    row = payload["results"][0]
    assert row["absolute_move_bps"] == "500.000000"
    assert row["evidence_freshness_score"] == "0.916667"
    assert row["price_move_explainability_score"] == "0.894167"
    assert row["result_integrity_digest"] == result.results[0].result_integrity_digest
    assert len(row["result_integrity_digest"]) == 64
    assert row["paper_only"] is True
    assert row["report_only"] is True
    assert row["readonly"] is True
    assert_no_public_int_or_float_values(payload)


def test_payload_rejects_unsafe_dict_surfaces_and_flag_downgrades() -> None:
    module = api()
    payload = module.strategy_candidate_price_move_explainability_payload(report(record()))

    with pytest.raises(ValueError, match="unsafe live surface field"):
        module.strategy_candidate_price_move_explainability_payload(
            {**payload, "order_id": "order-123"},
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        module.strategy_candidate_price_move_explainability_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe live surface value"):
        module.strategy_candidate_price_move_explainability_payload(
            {**payload, "results": [{**payload["results"][0], "market_slug": "wallet://x"}]},
        )


def test_tamper_evident_result_and_report_validation_recomputes_derived_fields() -> None:
    result = report(record())
    row = result.results[0]

    with pytest.raises(ValueError, match="absolute_move_bps must match probabilities"):
        replace(row, absolute_move_bps=d("501.000000"))
    with pytest.raises(
        ValueError,
        match="price_move_explainability_score must match components",
    ):
        replace(row, price_move_explainability_score=d("0.800000"))
    with pytest.raises(ValueError, match="reason_codes must match recomputed reasons"):
        replace(row, reason_codes=("tampered_reason",))
    with pytest.raises(ValueError, match="result_integrity_digest must match result"):
        replace(row, result_integrity_digest="0" * 64)
    with pytest.raises(ValueError, match="candidate_count must match results"):
        replace(result, candidate_count=d("2"))
    with pytest.raises(ValueError, match="report_integrity_digest must match report"):
        replace(result, report_integrity_digest="0" * 64)


def test_records_reports_and_results_are_frozen_exact_decimal_and_readonly() -> None:
    module = api()
    result = report(record())

    for name in module.__all__:
        exported = getattr(module, name)
        if is_dataclass(exported):
            assert exported.__dataclass_params__.frozen is True
            with pytest.raises(TypeError, match="must not be subclassed"):

                class Derived(exported):  # type: ignore[misc, valid-type]
                    pass

    with pytest.raises(FrozenInstanceError):
        result.results[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="exact Decimal"):
        record(previous_probability=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="timezone-aware datetime"):
        report(record(), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="timezone-aware datetime"):
        report(
            record(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        record(reason_codes=["candidate_input"])
    with pytest.raises(ValueError, match="evidence_age_minutes must be nonnegative"):
        record(evidence_age_minutes=d("-0.000001"))
    with pytest.raises(ValueError, match="readonly must be True"):
        record(readonly=False)
    with pytest.raises(ValueError, match="report must be"):
        module.strategy_candidate_price_move_explainability_payload(object())


def test_module_is_pure_readonly_decimal_only_and_unwired() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "http",
        "httpx",
        "io",
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
    forbidden_call_names = {
        "cancel",
        "compile",
        "connect",
        "eval",
        "exec",
        "execute",
        "fetch",
        "input",
        "open",
        "order",
        "place_order",
        "print",
        "request",
        "send",
        "submit",
        "trade",
        "write",
    }
    forbidden_attr_fragments = (
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
