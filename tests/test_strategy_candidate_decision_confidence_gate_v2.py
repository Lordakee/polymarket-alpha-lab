from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_decision_confidence_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 14, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_decision_confidence_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def evidence(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-pass",
        "market_slug": "event-outcome-pass",
        "event_id": "event-pass",
        "source_verified_edge_score": d("0.950000"),
        "recommendation_uncertainty_band": d("0.040000"),
        "specialist_signal_confidence": d("0.920000"),
        "liquidity_exit_risk_score": d("0.070000"),
        "resolution_ambiguity_score": d("0.060000"),
        "portfolio_impact_score": d("0.100000"),
        "research_readiness_score": d("0.930000"),
    }
    values.update(overrides)
    return module.StrategyCandidateDecisionConfidenceEvidenceV2(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            evidence(candidate_id="candidate-pass", market_slug="event-outcome-pass"),
            evidence(
                candidate_id="candidate-watch",
                market_slug="event-outcome-watch",
                event_id="event-watch",
                source_verified_edge_score=d("0.800000"),
                recommendation_uncertainty_band=d("0.100000"),
                specialist_signal_confidence=d("0.760000"),
                liquidity_exit_risk_score=d("0.200000"),
                resolution_ambiguity_score=d("0.200000"),
                portfolio_impact_score=d("0.300000"),
                research_readiness_score=d("0.750000"),
            ),
            evidence(
                candidate_id="candidate-blocked",
                market_slug="event-outcome-blocked",
                event_id="event-blocked",
                source_verified_edge_score=d("0.600000"),
                recommendation_uncertainty_band=d("0.050000"),
                specialist_signal_confidence=d("0.880000"),
                liquidity_exit_risk_score=d("0.100000"),
                resolution_ambiguity_score=d("0.100000"),
                portfolio_impact_score=d("0.100000"),
                research_readiness_score=d("0.880000"),
            ),
        )
    return module.build_strategy_candidate_decision_confidence_gate_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_final_candidate_decision_confidence_report_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.gate_status == "blocked"
    assert report.final_decision_blocked is True
    assert report.candidate_count == d("3")
    assert report.pass_candidate_count == d("1")
    assert report.watch_candidate_count == d("1")
    assert report.blocked_candidate_count == d("1")
    assert report.average_confidence_score == d("0.852200")
    assert report.reason_codes == (
        "decision_confidence_gate_watch_rows",
        "decision_confidence_gate_blocked_rows",
    )

    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-blocked",
        "candidate-watch",
        "candidate-pass",
    )
    assert tuple(row.validation_status for row in report.rows) == (
        "blocked",
        "watch",
        "pass",
    )
    assert tuple(row.confidence_score for row in report.rows) == (
        d("0.826500"),
        d("0.794000"),
        d("0.936100"),
    )
    assert "source_verified_edge_weak" in report.rows[0].reason_codes

    payload = report.payload
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)
    assert payload["candidate_count"] == "3"
    assert payload["average_confidence_score"] == "0.852200"
    assert payload["generated_at"] == "2026-07-06T14:30:00+00:00"
    assert payload["final_decision_blocked"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["confidence_score"] == "0.826500"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert "Decimal" not in rendered
    assert_no_float_values(payload)


def test_empty_report_is_digest_backed_report_only_and_blocking() -> None:
    report = build_report(
        *(),
        generated_at=GENERATED_AT,
        use_default_items=False,
    )

    assert report.gate_status == "blocked"
    assert report.final_decision_blocked is True
    assert report.candidate_count == d("0")
    assert report.average_confidence_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("decision_confidence_gate_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.StrategyCandidateDecisionConfidenceGateV2Config()
    item = evidence()
    report = build_report(item)
    row = report.rows[0]

    for obj in (config, item, row, report):
        assert obj.paper_only is True
        assert obj.report_only is True
        assert obj.readonly is True
        with pytest.raises(FrozenInstanceError):
            obj.paper_only = False  # type: ignore[misc]
        for field in fields(obj):
            value = getattr(obj, field.name)
            if field.name.endswith(("_score", "_floor", "_weight", "_band", "_count")):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="source_verified_edge_score must be exactly Decimal"):
        evidence(source_verified_edge_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="specialist_signal_confidence must be exactly Decimal"):
        evidence(specialist_signal_confidence=0)
    with pytest.raises(ValueError, match="research_readiness_score must be <= 1.000000"):
        evidence(research_readiness_score=d("1.000001"))
    with pytest.raises(
        ValueError,
        match="recommendation_uncertainty_band must use six decimal places or fewer",
    ):
        evidence(recommendation_uncertainty_band=d("0.0700004"))
    with pytest.raises(ValueError, match="portfolio_impact_score must be finite"):
        evidence(portfolio_impact_score=Decimal("NaN"))


def test_config_and_build_validation_reject_bad_inputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="pass_confidence_floor must be exactly Decimal"):
        module.StrategyCandidateDecisionConfidenceGateV2Config(
            pass_confidence_floor=0,
        )
    with pytest.raises(ValueError, match="watch_confidence_floor must not exceed pass_confidence_floor"):
        module.StrategyCandidateDecisionConfidenceGateV2Config(
            watch_confidence_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.StrategyCandidateDecisionConfidenceGateV2Config(
            source_verified_edge_weight=d("0.200000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.StrategyCandidateDecisionConfidenceGateV2Config(paper_only=False)
    with pytest.raises(ValueError, match="candidate confidence evidence must be an iterable"):
        module.build_strategy_candidate_decision_confidence_gate_v2(
            object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(
        ValueError,
        match="candidate confidence evidence items must be StrategyCandidateDecisionConfidenceEvidenceV2",
    ):
        module.build_strategy_candidate_decision_confidence_gate_v2(
            [object()],
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate candidate_id, market_slug, and event_id"):
        build_report(evidence(), evidence())
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_strategy_candidate_decision_confidence_gate_v2(
            [evidence()],
            generated_at=datetime(2026, 7, 6),
        )


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, average_confidence_score=d("0.800000"))


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_candidate",
        "auth_candidate",
        "wallet_candidate",
        "order_candidate",
        "network_candidate",
        "database_candidate",
        "persist_candidate",
        "signing_candidate",
        "mutation_candidate",
        "buy_candidate",
        "sell_candidate",
        "trade_candidate",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            evidence(candidate_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade_signal",))


def test_report_revalidates_row_sequence_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by status and candidate_id"):
        replace(report, rows=(report.rows[1], report.rows[0], report.rows[2]))
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(report, pass_candidate_count=d("2"))
    with pytest.raises(ValueError, match="reason_codes must match gate_status"):
        replace(report, reason_codes=("decision_confidence_gate_passed",))


def test_module_scope_has_no_file_database_network_or_action_surface() -> None:
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
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "fetch",
        "float",
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
    assert not any(imported.split(".")[0] in forbidden_import_roots for imported in imports)
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
